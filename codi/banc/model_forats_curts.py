"""Un model de cada forat curt, al decodificador (pas 2 de la T3x del pla per tocs, `docs/pla-tocs.md`, «T3x»; D-56).

    cd codi && uv run python -I -m banc.model_forats_curts [--processos 12]

A equips sencers tal qual, amb el cost del decodificador canviat als canvis d'equip de dins dels forats curts
(`cadena/forats_curts.py`):

1. **Els forats i els trets** de cada partit, als deu escenaris de la T3 i a «partit ×¼»: els de la cadena (de menys de
   5 s, amb la pilota vista a les dues vores, a la mateixa part). Per aprendre i per a l'AUC, només els que tenen les
   dues vores als trams vàlids, amb l'objectiu: si la veritat de toc hi canvia d'equip, sense comptar la D
   (`objectiu`).
2. **El model del partit que es prova:** un LightGBM binari amb els forats dels altres nou partits, als sis escenaris
   d'entrenament, amb els paràmetres del verificador de la T3s. Les seves p, a cada escenari, a la memòria cau
   (`dades/banc/forats-curts/`).
3. **El decodificador,** amb les probabilitats i la q d'A equips sencers de la memòria cau de la T3v: el cost de
   `t3i.costos` amb cada decodificador triat d'A equips sencers, i el de `forats_curts.cost` amb cada β. Amb β = 0 ha
   de donar exactament l'spellF1 d'A equips sencers del banc de la T3v, a les dues veritats; si no, s'atura. A xarxes,
   decodificat de nou amb el seu decodificador triat, també.
4. **La β** de cada partit, triada amb els altres nou als quatre ×¼ a la veritat de toc, amb el w, la λ i la durada
   mínima d'A equips sencers del partit que es prova (els de la T3v, que no es tornen a triar).
5. **El criteri** del pla: A forats curts contra A xarxes, a la veritat de toc. Si no passa, la regla de la D-55 a curts
   ×¼, contra A equips sencers. Només per saber-ho: per font, l'AUC del model a cada escenari, què hi fa la predicció
   als forats curts de curts ×¼, i les β triades.

Escriu `resultats/model-forats-curts.json` i `resultats/model-forats-curts.md`. Tot són dades obertes. Els mòduls
d'abans no es toquen.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import itertools
import json
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from banc import analisi_t3p as t3p
from banc import avalua, fonts
from banc import canvis_als_forats as caf
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_equips as mae
from banc import model_a_partit as mp
from banc import model_a_q as mq
from banc import model_a_quart as t3b
from banc import model_a_toc as mt
from banc import model_a_verificador as mav
from banc import model_pilota_creible as mpc
from banc import separen_els_forats as sef
from banc import sostre_sense_pilota as ssp
from banc import veritat_toc as vt
from cadena import forats_curts as fc
from possessio.decodificacio import log_relativa

ESCENARIS = mp.ESCENARIS                            # els deu de la T3 i «partit ×¼»
SIS = mp.SIS                                        # on aprèn el model dels forats
CURTS = sef.CURTS                                   # l'escenari on va
XARXES, XARXES_TOC, A_EQUIPS = mae.XARXES, mae.XARXES_TOC, mae.A_EQUIPS
SEMPRE, TOC = mae.SEMPRE, mae.TOC
A_FORATS = "A forats curts"
BETES = (0.0, 0.5, 1.0, 2.0, 4.0, 8.0)
PARAMS, RONDES = mav.PARAMS, mav.RONDES
FONTS = mae.FONTS
DIR_CAU = fonts.DIR_CAU / "forats-curts"
DIR_RESULTATS = t3.DIR_RESULTATS


def objectiu(toc: np.ndarray, a: int, b: int) -> float:
    """1 si la veritat canvia d'equip de la vora d'abans del forat [a, b] a la de després, sense comptar la D; 0 si no;
    NaN si no hi és de cap equip."""
    v = toc[a - 1:b + 2]
    v = v[np.isin(v, ssp.EQUIPS)]
    return float(len(caf.seguits(v)) >= 2) if len(v) else np.nan


def forats_de(nom_escenari: tuple[str, str]) -> dict:
    """Els forats curts d'un partit i un escenari, els seus trets i l'objectiu (NaN on les dues vores no són als trams
    vàlids)."""
    nom, escenari = nom_escenari
    de_sempre = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    valides = ssp.dins(len(toc), avalua.trams_valids(replace(de_sempre, veritat=toc)))
    forats_ = fc.forats(~np.isnan(de_sempre.tracking.pilota[:, 0]), de_sempre.trams)
    y = np.array([objectiu(toc, a, b) if valides[a - 1:b + 2].all() else np.nan for a, b, _, _ in forats_])
    return {"partit": nom, "escenari": escenari, "forats": forats_,
            "trets": fc.trets(de_sempre.tracking, forats_, de_sempre.trams), "y": y}


def entrena(prova: str, tots: dict[tuple[str, str], dict]) -> tuple[lgb.Booster, float]:
    """El model del partit `prova`: els forats amb objectiu dels altres nou, als sis escenaris d'entrenament; i π, la
    part d'aquests forats amb canvi."""
    xs, ys = [], []
    for (nom, e), d in tots.items():
        if nom != prova and e in SIS:
            amb = ~np.isnan(d["y"])
            xs.append(d["trets"][amb])
            ys.append(d["y"][amb])
    x, y = pd.concat(xs, ignore_index=True), np.concatenate(ys)
    return lgb.train(PARAMS, lgb.Dataset(x, label=y), num_boost_round=RONDES), float(y.mean())


def probabilitats(prova: str, tots: dict[tuple[str, str], dict]) -> tuple[dict[str, np.ndarray], float]:
    """Les p del model de `prova` als seus forats curts de cada escenari, i la π; de la memòria cau si hi són."""
    cami = DIR_CAU / f"{prova}.npz"
    if cami.exists():
        with np.load(cami, allow_pickle=False) as d:
            if str(d["clau"]) == CLAU:
                return {e: d[f"e{i}"] for i, e in enumerate(ESCENARIS)}, float(d["pi"])
    model, pi = entrena(prova, tots)
    p = {e: model.predict(tots[(prova, e)]["trets"]) if len(tots[(prova, e)]["trets"]) else np.zeros(0)
         for e in ESCENARIS}
    cami.parent.mkdir(parents=True, exist_ok=True)
    temporal = cami.with_name(f"{cami.name}.{os.getpid()}.part.npz")
    np.savez(temporal, clau=CLAU, pi=pi, **{f"e{i}": p[e] for i, e in enumerate(ESCENARIS)})
    temporal.replace(cami)
    return p, pi


def d_equips(nom: str, escenari: str) -> tuple[np.ndarray, np.ndarray]:
    """La probabilitat relativa i la q d'A equips sencers, de la memòria cau de la T3v."""
    probes, prior, q_ = mae.de_qui(A_EQUIPS, nom)
    return log_relativa(probes[escenari].astype(float), prior), q_[escenari].astype(float)


def decodifica(relativa: np.ndarray, q: np.ndarray, trams: tuple[tuple[int, int, int], ...], forats_: np.ndarray,
               p: np.ndarray, pi: float, w: float, lam: float, d_min: int, beta: float) -> np.ndarray:
    """A forats curts, amb un decodificador i una β."""
    return fc.per_trams(relativa, fc.cost(t3i.costos(q, lam, w), forats_, fc.r_de(p, pi), beta), trams, d_min)


def graella(tasca: tuple[str, str, np.ndarray, np.ndarray, float, tuple, tuple]) -> list[dict]:
    """Un partit i un escenari: A forats curts amb cada decodificador triat d'A equips sencers i cada β, i A xarxes
    amb el seu, a les dues veritats."""
    nom, escenari, forats_, p, pi, triades_equips, triada_xarxes = tasca
    de_sempre = mp.degradat(nom, escenari)
    if not np.array_equal(forats_, fc.forats(~np.isnan(de_sempre.tracking.pilota[:, 0]), de_sempre.trams)):
        raise RuntimeError(f"{nom}, {escenari}: els forats no són els de les p")
    partits = {SEMPRE: de_sempre, TOC: replace(de_sempre, veritat=vt.veritat(nom))}
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}
    relativa, q = d_equips(nom, escenari)
    files = []
    for (w, lam, d_min), beta in itertools.product(triades_equips, BETES):
        pred = decodifica(relativa, q, de_sempre.trams, forats_, p, pi, w, lam, int(d_min), beta)
        files += [{**comu, "metode": A_FORATS, "veritat": v, "w": w, "lam": lam, "d_min": int(d_min), "beta": beta,
                   **avalua.puntua(pv, pred)} for v, pv in partits.items()]
    probes, prior, q_ = mae.de_qui(XARXES, nom)
    w, lam, d_min = triada_xarxes
    pred = t3i.per_trams(log_relativa(probes[escenari].astype(float), prior), q_[escenari].astype(float),
                         de_sempre.trams, w, lam, int(d_min))
    files += [{**comu, "metode": XARXES, "veritat": v, "w": w, "lam": lam, "d_min": int(d_min),
               **avalua.puntua(pv, pred)} for v, pv in partits.items()]
    return files


def comprova_les_d_abans(files: pd.DataFrame, banc: pd.DataFrame) -> None:
    """Amb β = 0, A forats curts dona a cada partit, escenari, decodificador i veritat l'spellF1 d'A equips sencers
    del banc de la T3v; i A xarxes, el seu."""
    claus = ["partit", "escenari", "veritat", "w", "lam", "d_min"]
    for metode, aqui in ((A_EQUIPS, files[(files["metode"] == A_FORATS) & (files["beta"] == 0)]),
                         (XARXES, files[files["metode"] == XARXES])):
        del_banc = banc[banc["metode"] == metode][[*claus, "spell_f1"]]
        junts = aqui[[*claus, "spell_f1"]].merge(del_banc, on=claus, suffixes=("", " del banc"), how="left")
        if (len(junts) != len(aqui) or junts.isna().any().any()
                or not np.allclose(junts["spell_f1"], junts["spell_f1 del banc"], rtol=0, atol=1e-12)):
            raise RuntimeError(f"{metode} no dona el del banc de la T3v")


def tria_beta(files: pd.DataFrame, triades_equips: dict[str, tuple]) -> tuple[pd.DataFrame, dict]:
    """A cada partit, les files d'A forats curts amb el seu decodificador d'A equips sencers i la β triada amb els
    altres nou als quatre ×¼ a la veritat de toc; i les triades (w, λ, durada mínima, β)."""
    seu = files[files["metode"] == A_FORATS]
    triats, triades = [], {}
    for prova in fonts.NOMS:
        w, lam, d_min = triades_equips[prova]
        amb = seu[(seu["w"] == w) & (seu["lam"] == lam) & (seu["d_min"] == d_min)]
        beta = float(mp.millor(amb[(amb["partit"] != prova) & (amb["veritat"] == TOC)], ["beta"], t3.QUARTS))
        triats.append(amb[(amb["partit"] == prova) & (amb["beta"] == beta)])
        triades[prova] = (float(w), float(lam), int(d_min), beta)
    return pd.concat(triats, ignore_index=True), triades


def taula_auc(tots: dict[tuple[str, str], dict], ps: dict[str, dict[str, np.ndarray]]) -> pd.DataFrame:
    """A cada escenari, als forats amb objectiu dels deu partits (cadascun amb el model que no l'ha vist): quants n'hi
    ha, quina part amb canvi, i l'AUC del model."""
    files = []
    for e in ESCENARIS:
        y = np.concatenate([tots[(nom, e)]["y"] for nom in fonts.NOMS])
        p = np.concatenate([ps[nom][e] for nom in fonts.NOMS])
        amb = ~np.isnan(y)
        files.append({"escenari": e, "n forats": int(amb.sum()), "amb canvi": float(y[amb].mean()),
                      "AUC": float(roc_auc_score(y[amb], p[amb])) if len(set(y[amb])) == 2 else np.nan})
    return pd.DataFrame(files).set_index("escenari")


def que_hi_fa(tasca: tuple[str, np.ndarray, np.ndarray, np.ndarray, float, tuple]) -> list[dict]:
    """A curts ×¼, als forats curts d'un canvi i sense canvi amb les dues vores als trams vàlids: què hi fa A equips
    sencers i què hi fa A forats curts, amb la β triada."""
    nom, forats_, y, p, pi, (w, lam, d_min, beta) = tasca
    toc = vt.veritat(nom)
    relativa, q = d_equips(nom, CURTS)
    trams = mp.degradat(nom, CURTS).trams
    files = []
    for metode, b in ((A_EQUIPS, 0.0), (A_FORATS, beta)):
        pred = decodifica(relativa, q, trams, forats_, p, pi, w, lam, int(d_min), b)
        for (a, b_, _, _), y_ in zip(forats_, y):
            if not np.isnan(y_):
                tipus, fa = sef.del_forat(toc, pred, a, b_)
                if tipus in (caf.UN, caf.SENSE):
                    files.append({"partit": nom, "metode": metode, "tipus": tipus, "fa": fa})
    return files


def taula_que_hi_fa(fets: pd.DataFrame) -> pd.DataFrame:
    t = fets.groupby(["tipus", "fa", "metode"]).size().unstack("metode").reindex(columns=[A_EQUIPS, A_FORATS])
    t = t.fillna(0)
    t.columns = [f"n {c}" for c in t.columns]
    return t


def _regla(millor: dict[str, bool]) -> list[str]:
    es = all(millor.values())
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| {CURTS} | la diferència és positiva i l'interval del 95 % no toca el zero | "
            f"{mq._marca(millor['escenari'])} |",
            f"| Els altres tres ×¼ i «{mp.PARTIT}» | la diferència no és negativa | {mq._marca(millor['quarts'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {mq._marca(millor['altres'])} |",
            "", f"**{A_FORATS} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_FORATS if es else A_EQUIPS}.", ""]


def _betes(triades: dict[str, tuple]) -> list[str]:
    compta: dict[str, int] = {}
    for w, lam, d_min, beta in triades.values():
        clau_ = f"β = {beta:g} (w = {w:g}, λ = {lam:g}, durada mínima {d_min})"
        compta[clau_] = compta.get(clau_, 0) + 1
    return [f"- {k}: {n} partits" for k, n in sorted(compta.items())]


def markdown(metodes: pd.DataFrame, triades: dict, c: pd.DataFrame, passa: dict[str, bool], c_equips: pd.DataFrame,
             millor: dict[str, bool], per_font: dict[tuple[str, str], pd.DataFrame], auc: pd.DataFrame,
             fets: pd.DataFrame) -> str:
    linies = ["# Banc obert · Un model de cada forat curt, al decodificador (T3x)", "",
              "Generat amb `uv run python -I -m banc.model_forats_curts`. Dades obertes: 7 partits de DFL (IDSSE, CC BY",
              "4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3x», i la capçalera de `banc/model_forats_curts.py`. Es puntua a la",
              "veritat de toc.", "",
              f"**{XARXES_TOC}** i **{A_EQUIPS}** són els de la T3v, amb les probabilitats de la memòria cau (✓",
              f"comprovat: decodificats de nou, donen l'spellF1 del banc de la T3v; {A_EQUIPS}, amb β = 0).",
              f"**{A_FORATS}** és {A_EQUIPS} amb el cost dels canvis d'equip de dins dels forats curts canviat pel",
              "model del forat.", "",
              f"## {A_FORATS} contra {XARXES_TOC} (spellF1): el criteri", "",
              *t3b._taula(c, A_FORATS, XARXES_TOC), "", *mt._criteris(passa),
              f"## {A_FORATS} contra {A_EQUIPS} (spellF1)", "", *t3i._comparacio(c_equips, A_FORATS, A_EQUIPS), ""]
    if not all(passa.values()):
        linies += ["## No passa: és el millor fins ara?", "",
                   f"La regla dels passos que només van a un escenari (D-55), escrita abans, a {CURTS}, contra "
                   f"{A_EQUIPS}:", "", *_regla(millor)]
    for (font, contra), taula in per_font.items():
        linies += [f"## {A_FORATS} contra {contra}, només els partits de {font}", "",
                   *t3i._comparacio(taula, A_FORATS, contra), ""]
    linies += ["## El model dels forats", "",
               "Als forats curts amb les dues vores als trams vàlids, dels deu partits, cadascun amb el model que no l'ha",
               "vist: quants n'hi ha, quina part tenen canvi d'equip, i l'AUC del model.", "", t3p.md(auc), "",
               f"## Què hi fa la predicció als forats curts de {CURTS}", "",
               "Als d'un canvi i als sense canvi, com a `canvis_als_forats.py`, amb la β triada a cada partit.", "",
               t3p.md(taula_que_hi_fa(fets)), "",
               "## Les β triades", "", *_betes(triades), "",
               "## L'spellF1 de cada mètode (mitjana dels deu partits)", "",
               *mt._mitjanes(metodes, [XARXES_TOC, A_EQUIPS, A_FORATS])]
    return "\n".join(linies)


def clau() -> str:
    """El que fa les p d'aquí: els forats i els trets de la cadena, l'objectiu i el model."""
    h = hashlib.sha256((mp.CLAU + vt.CLAU + repr(PARAMS) + str(RONDES)).encode())
    h.update(Path(fc.__file__).read_bytes())
    for funcio in (objectiu, forats_de, entrena, probabilitats):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + mae.clau_dels_resultats()).encode())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_forats_curts as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        return list(feina.map(getattr(aquest, fes), tasques))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    args = ap.parse_args()
    banc_t3v = mpc.banc_t3v()
    banc = pd.DataFrame(banc_t3v["files"])
    de_xarxes, triades_xarxes = mt.tria_sense_mirar(banc, XARXES, TOC, XARXES_TOC)
    de_equips, triades_equips = mt.tria_sense_mirar(banc, A_EQUIPS, TOC, A_EQUIPS)
    mpc.comprova_les_triades({XARXES_TOC: triades_xarxes, A_EQUIPS: triades_equips})
    for nom in fonts.NOMS:
        for metode in (XARXES, A_EQUIPS):
            mae.de_qui(metode, nom)
        vt.veritat(nom)
    tots = {(d["partit"], d["escenari"]): d
            for d in en_paral_lel("forats_de", list(itertools.product(fonts.NOMS, ESCENARIS)), args.processos)}
    print(f"· els forats curts i els seus trets, a {len(tots)} partits i escenaris", flush=True)
    ps, pis = {}, {}
    for nom in fonts.NOMS:
        ps[nom], pis[nom] = probabilitats(nom, tots)
    print("· els 10 models dels forats", flush=True)
    distintes = tuple(sorted(set(triades_equips.values())))
    tasques = [(nom, e, tots[(nom, e)]["forats"], ps[nom][e], pis[nom], distintes, triades_xarxes[nom])
               for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    files = pd.DataFrame([f for tros in en_paral_lel("graella", tasques, args.processos) for f in tros])
    comprova_les_d_abans(files, banc)
    print(f"· amb β = 0, {A_FORATS} dona el d'{A_EQUIPS}, i {XARXES} el seu, com el banc de la T3v", flush=True)
    de_forats, triades = tria_beta(files, triades_equips)
    metodes = pd.concat([de_xarxes, de_equips, de_forats], ignore_index=True)
    c = mt.comparacio(metodes, A_FORATS, XARXES_TOC, TOC, amb_criteri=True)
    c_equips = mt.comparacio(metodes, A_FORATS, A_EQUIPS, TOC, amb_criteri=False)
    passa, millor = mt.compleix(c), mpc.millor_d_un_escenari(c_equips, CURTS)
    per_font = {(font, contra): mt.comparacio(metodes[metodes["font"] == font], A_FORATS, contra, TOC,
                                              amb_criteri=False)
                for font in FONTS for contra in (XARXES_TOC, A_EQUIPS)}
    fets = pd.DataFrame([f for tros in en_paral_lel(
        "que_hi_fa", [(nom, tots[(nom, CURTS)]["forats"], tots[(nom, CURTS)]["y"], ps[nom][CURTS], pis[nom],
                       triades[nom]) for nom in fonts.NOMS], args.processos) for f in tros])
    auc = taula_auc(tots, ps)
    md = markdown(metodes, triades, c, passa, c_equips, millor, per_font, auc, fets)
    contingut = {"clau": clau_dels_resultats(), "files": files[files["metode"] == A_FORATS].to_dict("records"),
                 "triades": {A_FORATS: triades}, "passa": passa, "millor": millor}
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-forats-curts.json").write_text(json.dumps(contingut, indent=1, default=float,
                                                                      allow_nan=False))
    (DIR_RESULTATS / "model-forats-curts.md").write_text(md)
    print(md)


if __name__ == "__main__":
    main()
