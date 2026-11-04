"""Els trets dels forats curts, al segon (T3y del pla per tocs, `docs/pla-tocs.md`, «T3y»; D-57).

    cd codi && uv run python -I -m banc.model_forats_al_segon [--processos 12] [--processos-models 3]

A equips sencers tal qual, amb una sola diferència: el segon també veu els trets del forat curt més proper
(`cadena/forats_curts.py`, `columnes_del_segon`).

1. **En començar,** A xarxes i A equips sencers, amb la memòria cau, han de donar a cada punt de la graella i a les dues
   veritats l'spellF1 del banc de la T3v. I, a cada partit i escenari, la taula del segon sense les columnes noves ha
   de ser exactament la de la T3v.
2. **El segon,** entrenat com el d'A equips sencers (`mae.segon`: els altres nou partits, als sis escenaris
   d'entrenament, a la veritat de sempre), amb les columnes noves. El primer, les cinc xarxes i la q, de la memòria cau
   de la T3v. Les seves probabilitats, a `dades/banc/forats-al-segon/`.
3. **El decodificador,** amb la graella de la T3j, triat amb els altres nou als quatre ×¼ a la veritat de toc.
4. **El criteri** del pla: A forats al segon contra A xarxes, a la veritat de toc. Si no passa, la regla de la D-55 a
   curts ×¼, contra A equips sencers. Només per saber-ho: per font, què hi fa la predicció als forats curts de curts ×¼,
   on encerta l'equip el segon a cada ×¼, i els decodificadors triats.

Escriu `resultats/model-forats-al-segon.json` i `resultats/model-forats-al-segon.md`. Tot són dades obertes. Els mòduls
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

import numpy as np
import pandas as pd

from banc import analisi_t3p as t3p
from banc import avalua, fonts
from banc import canvis_als_forats as caf
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_canvis2 as t3j
from banc import model_a_context as t3e
from banc import model_a_equips as mae
from banc import model_a_partit as mp
from banc import model_a_possessio as t3f
from banc import model_a_q as mq
from banc import model_a_quart as t3b
from banc import model_a_sense_pilota as msp
from banc import model_a_toc as mt
from banc import model_a_xarxa as t3m
from banc import model_forats_curts as mfc
from banc import model_pilota_creible as mpc
from banc import separen_els_forats as sef
from banc import sostre_sense_pilota as ssp
from banc import veritat_toc as vt
from banc.partit import PartitBanc
from cadena import forats_curts as fc
from cadena import model
from possessio.decodificacio import log_relativa

ESCENARIS = mp.ESCENARIS                            # els deu de la T3 i «partit ×¼»
SIS = mp.SIS
CURTS = sef.CURTS                                   # l'escenari on va
XARXES, XARXES_TOC, A_EQUIPS = mae.XARXES, mae.XARXES_TOC, mae.A_EQUIPS
SEMPRE, TOC = mae.SEMPRE, mae.TOC
A_FORATS = "A forats al segon"
FONTS = mae.FONTS
AMB_PILOTA, ALS_FORATS, ALS_CURTS = msp.AMB_PILOTA, msp.ALS_FORATS, "als forats curts"
ON = (AMB_PILOTA, ALS_FORATS, ALS_CURTS)
SEGON_EQUIPS, SEGON_NOU = f"el segon d'{A_EQUIPS}", "el segon nou"
QUI = {SEGON_EQUIPS: A_EQUIPS, SEGON_NOU: A_FORATS}
DIR_CAU = fonts.DIR_CAU / "forats-al-segon"
DIR_RESULTATS = t3.DIR_RESULTATS


def desa(cami: Path, **arrays: np.ndarray) -> None:
    cami.parent.mkdir(parents=True, exist_ok=True)
    temporal = cami.with_name(f"{cami.name}.{os.getpid()}.part.npz")
    np.savez(temporal, clau=CLAU, **arrays)
    temporal.replace(cami)


def llegeix(cami: Path) -> dict[str, np.ndarray] | None:
    if cami.exists():
        with np.load(cami, allow_pickle=False) as desat:
            if str(desat["clau"]) == CLAU:
                return {k: desat[k] for k in desat.files if k != "clau"}
    return None


def taula_segon(p: PartitBanc, primer: np.ndarray, de_les_xarxes: np.ndarray) -> pd.DataFrame:
    """La del segon d'A equips sencers (`t3m.taula_segon`) i les columnes dels forats curts."""
    return pd.concat([t3m.taula_segon(p, primer, de_les_xarxes), fc.columnes_del_segon(p.tracking, p.trams)], axis=1)


def mostres_segon(prova: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Com `mae.mostres_segon`, amb la taula d'aquí."""
    primers, de_les_xarxes = {}, {}
    for i in range(t3e.GRUPS):
        primers |= mp.primer_del_grup((prova, i, SIS))
        de_les_xarxes |= mae.xarxes_del_grup((prova, i), entrena=False)
    xs, ys = [], []
    for (nom, e), primer in primers.items():
        p = mp.degradat(nom, e)
        x, y = t3f.mostres(p, taula_segon(p, primer.astype(float), de_les_xarxes[(nom, e)].astype(float)))
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def segon(prova: str, entrena: bool = True) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Les probabilitats d'A forats al segon al partit `prova`, a tots els escenaris, i el prior: com `mae.segon`, amb
    la taula d'aquí. Amb `entrena=False`, només les llegeix de la memòria cau."""
    cami = DIR_CAU / f"segon-{prova}.npz"
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les probabilitats del segon d'{A_FORATS} de {prova}, o són d'un altre codi")
        x, y = mostres_segon(prova)
        entrenat, prior = model.entrena(x, y), model.prior(y)
        del x
        primers = mp.primer_de_la_prova((prova, SIS))
        de_les_xarxes = mae.xarxes_de_la_prova(prova, entrena=False)
        desat = {"prior": prior}
        for i, e in enumerate(ESCENARIS):
            p = mp.degradat(prova, e)
            taula = taula_segon(p, primers[e].astype(float), de_les_xarxes[e].astype(float))
            desat[f"e{i}"] = model.probabilitats(entrenat, taula).astype(np.float32)
        desa(cami, **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(ESCENARIS)}, desat["prior"]


def de_qui(metode: str, nom: str) -> tuple[dict[str, np.ndarray], np.ndarray, dict[str, np.ndarray]]:
    """Les probabilitats, el prior i la q d'A forats al segon (amb la q d'A xarxes, com A equips sencers), o les d'A
    xarxes o A equips sencers (`mae.de_qui`)."""
    if metode != A_FORATS:
        return mae.de_qui(metode, nom)
    probes, prior = segon(nom, entrena=False)
    return probes, prior, mp.q((nom, SIS), entrena=False)


def primer_desat(nom: str) -> dict[str, np.ndarray]:
    """El primer del partit `nom`, de la memòria cau de la T3p; si no hi és, s'atura (no l'entrena)."""
    desat = mp.llegeix(mp.cau("primer", SIS, nom))
    if desat is None:
        raise RuntimeError(f"Falta el primer de {nom} a la memòria cau de la T3p, o és d'un altre codi")
    return {e: desat[f"e{i}"] for i, e in enumerate(ESCENARIS)}


def comprova_la_taula(tasca: tuple[str, str]) -> None:
    """Al partit que es prova i a un escenari: sense les columnes noves, la taula del segon és exactament la de la T3v,
    i les noves no hi eren."""
    nom, escenari = tasca
    p = mp.degradat(nom, escenari)
    primer = primer_desat(nom)[escenari].astype(float)
    de_les_xarxes = mae.xarxes_de_la_prova(nom, entrena=False)[escenari].astype(float)
    vella, nova = t3m.taula_segon(p, primer, de_les_xarxes), taula_segon(p, primer, de_les_xarxes)
    if (list(nova.columns) != [*vella.columns, *fc.COLUMNES] or not nova.index.equals(vella.index)
            or not nova[list(vella.columns)].equals(vella)):
        raise RuntimeError(f"{nom}, {escenari}: sense les columnes noves, la taula del segon no és la de la T3v")


def graella(tasca: tuple[str, str, tuple[str, ...]]) -> list[dict]:
    """Com `mae.graella`, amb A forats al segon també."""
    nom, escenari, metodes = tasca
    de_sempre = mp.degradat(nom, escenari)
    partits = {SEMPRE: de_sempre, TOC: replace(de_sempre, veritat=vt.veritat(nom))}
    files = []
    for metode in metodes:
        probes, prior, q_ = de_qui(metode, nom)
        relativa = log_relativa(probes[escenari].astype(float), prior)
        for w, lam, d_min in itertools.product(t3j.WS, t3j.LAMS, t3j.DMINS):
            pred = t3i.per_trams(relativa, q_[escenari].astype(float), de_sempre.trams, w, lam, d_min)
            for veritat, p in partits.items():
                files.append({"partit": nom, "font": p.font, "escenari": escenari, "metode": metode,
                              "veritat": veritat, "w": w, "lam": lam, "d_min": d_min, **avalua.puntua(p, pred)})
    return files


def que_hi_fa(tasca: tuple[str, dict[str, tuple]]) -> list[dict]:
    """A curts ×¼, als forats curts d'un canvi i sense canvi amb les dues vores als trams vàlids (els de la T3x): què
    hi fa A equips sencers i què hi fa A forats al segon, cadascun amb el seu decodificador triat."""
    nom, triats = tasca
    d = mfc.forats_de((nom, CURTS))
    toc = vt.veritat(nom)
    trams = mp.degradat(nom, CURTS).trams
    files = []
    for metode, (w, lam, d_min) in triats.items():
        probes, prior, q_ = de_qui(metode, nom)
        pred = t3i.per_trams(log_relativa(probes[CURTS].astype(float), prior), q_[CURTS].astype(float), trams, w,
                             lam, int(d_min))
        for (a, b, _, _), y in zip(d["forats"], d["y"]):
            if not np.isnan(y):
                tipus, fa = sef.del_forat(toc, pred, a, b)
                if tipus in (caf.UN, caf.SENSE):
                    files.append({"partit": nom, "metode": metode, "tipus": tipus, "fa": fa})
    return files


def taula_que_hi_fa(fets: pd.DataFrame) -> pd.DataFrame:
    t = fets.groupby(["tipus", "fa", "metode"]).size().unstack("metode").reindex(columns=[A_EQUIPS, A_FORATS])
    t = t.fillna(0).astype(int)
    t.columns = [f"n {c}" for c in t.columns]
    return t


def mascares(de_sempre: PartitBanc, valides: np.ndarray) -> dict[str, np.ndarray]:
    """On es veu la pilota i als forats (`msp.mascares`), i a les imatges amb les columnes noves (els forats curts amb
    `fc.K` imatges a cada banda); només a les `valides`."""
    out = msp.mascares(~np.isnan(de_sempre.tracking.pilota[:, 0]), valides)
    curts = fc.columnes_del_segon(de_sempre.tracking, de_sempre.trams)["forat_on"].notna().to_numpy()
    return {AMB_PILOTA: out[AMB_PILOTA], ALS_FORATS: out[ALS_FORATS], ALS_CURTS: curts & valides}


def encerts(tasca: tuple[str, str]) -> list[dict]:
    """Un partit i un escenari: on la veritat de toc és d'un equip, a quantes imatges el segon d'A equips sencers i el
    nou hi encerten l'equip (amb la relativa)."""
    nom, escenari = tasca
    de_sempre = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    valides = ssp.dins(len(toc), avalua.trams_valids(replace(de_sempre, veritat=toc)))
    probes = {}
    for qui, metode in QUI.items():
        de_l_un, prior, _ = de_qui(metode, nom)
        probes[qui] = log_relativa(de_l_un[escenari].astype(float), prior)
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}
    files = []
    for on, mascara in mascares(de_sempre, valides).items():
        for qui in QUI:
            n, e = ssp.encerts(probes[qui], toc, mascara)
            files.append({**comu, "on": on, "qui": qui, "n": n, "encerts": e})
    return files


def taula_encerts(t: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i on: quantes imatges hi ha d'un equip, i la part on cada segon hi encerta l'equip."""
    g = t.groupby(["escenari", "on", "qui"], sort=False)[["n", "encerts"]].sum()
    part = (g["encerts"] / g["n"]).unstack("qui")[list(QUI)]
    n = g["n"].xs(SEGON_NOU, level="qui").rename("n imatges")
    ordre = {**{e: i for i, e in enumerate(ESCENARIS)}, **{o: i for i, o in enumerate(ON)}}
    return pd.concat([n, part], axis=1).sort_index(key=lambda idx: idx.map(lambda x: ordre.get(x, len(ordre))))


def _regla(millor: dict[str, bool]) -> list[str]:
    es = all(millor.values())
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| {CURTS} | la diferència és positiva i l'interval del 95 % no toca el zero | "
            f"{mq._marca(millor['escenari'])} |",
            f"| Els altres tres ×¼ i «{mp.PARTIT}» | la diferència no és negativa | {mq._marca(millor['quarts'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {mq._marca(millor['altres'])} |",
            "", f"**{A_FORATS} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_FORATS if es else A_EQUIPS}.", ""]


def markdown(metodes: pd.DataFrame, triades: dict, c: pd.DataFrame, passa: dict[str, bool], c_equips: pd.DataFrame,
             millor: dict[str, bool], per_font: dict[tuple[str, str], pd.DataFrame], fets: pd.DataFrame,
             encerts_: pd.DataFrame) -> str:
    linies = ["# Banc obert · Els trets dels forats curts, al segon (T3y)", "",
              "Generat amb `uv run python -I -m banc.model_forats_al_segon`. Dades obertes: 7 partits de DFL (IDSSE, CC",
              "BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3y», i la capçalera de `banc/model_forats_al_segon.py`. Es puntua a la",
              "veritat de toc.", "",
              f"**{XARXES_TOC}** i **{A_EQUIPS}** són els de la T3v, amb les peces de la memòria cau (✓ comprovat: a",
              "cada punt de la graella donen l'spellF1 del banc de la T3v; i, sense les columnes noves, la taula del",
              f"segon és la de la T3v). **{A_FORATS}** és {A_EQUIPS}, amb el segon que també veu els trets del forat",
              "curt més proper.", "",
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
    linies += [f"## Què hi fa la predicció als forats curts de {CURTS}", "",
               "Als d'un canvi i als sense canvi amb les dues vores als trams vàlids, com a `canvis_als_forats.py`, amb",
               "el decodificador triat de cada mètode a cada partit.", "", t3p.md(taula_que_hi_fa(fets)), "",
               "## On encerta l'equip el segon", "",
               "On la veritat de toc és d'un equip, la part de les imatges on l'equip més probable (amb la relativa) és",
               f"el bo. Als forats: els trossos sense pilota, amb {t3i.K} imatges més a cada banda. Als forats curts:",
               "les imatges amb les columnes noves.", "", t3p.md(taula_encerts(encerts_)), "",
               "## L'spellF1 de cada mètode (mitjana dels deu partits)", "",
               *mt._mitjanes(metodes, [XARXES_TOC, A_EQUIPS, A_FORATS]), "## Els decodificadors triats", "",
               *mq._triades(triades), ""]
    return "\n".join(linies)


def clau() -> str:
    """El que fa les probabilitats d'aquí: les peces d'A equips sencers, les columnes dels forats curts i això."""
    h = hashlib.sha256((mae.CLAU + mp.CLAU + repr((SIS, ESCENARIS, model.RONDES, model.PAS))).encode())
    h.update(Path(fc.__file__).read_bytes())
    for funcio in (taula_segon, mostres_segon, segon):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + vt.CLAU + mae.clau_dels_resultats() + mfc.CLAU).encode())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_forats_al_segon as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        return list(feina.map(getattr(aquest, fes), tasques))


def entrena_els_segons(processos: int) -> None:
    from banc import model_forats_al_segon as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        for k, (nom, _) in enumerate(zip(fonts.NOMS, feina.map(aquest.segon, fonts.NOMS)), start=1):
            print(f"· {k}/{len(fonts.NOMS)}: el segon d'{A_FORATS} de {nom}", flush=True)


def files_de(metodes: tuple[str, ...], processos: int) -> pd.DataFrame:
    tasques = [(nom, e, metodes) for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    return pd.DataFrame([f for tros in en_paral_lel("graella", tasques, processos) for f in tros])


def escriu(contingut: dict, md: str) -> None:
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-forats-al-segon.json").write_text(json.dumps(contingut, indent=1, default=float,
                                                                         allow_nan=False))
    (DIR_RESULTATS / "model-forats-al-segon.md").write_text(md)
    print(md)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=3, help="models alhora")
    args = ap.parse_args()
    for nom in fonts.NOMS:
        for metode in (XARXES, A_EQUIPS):
            mae.de_qui(metode, nom)
        primer_desat(nom)
        mae.xarxes_de_la_prova(nom, entrena=False)
        vt.veritat(nom)
    files = files_de((XARXES, A_EQUIPS), args.processos)
    mpc.comprova_les_d_abans(files)
    print(f"· {XARXES} i {A_EQUIPS} donen el del banc de la T3v", flush=True)
    en_paral_lel("comprova_la_taula", list(itertools.product(fonts.NOMS, ESCENARIS)), args.processos)
    print("· sense les columnes noves, la taula del segon és la de la T3v", flush=True)
    entrena_els_segons(args.processos_models)
    files = pd.concat([files, files_de((A_FORATS,), args.processos)], ignore_index=True)
    de_xarxes, triades_xarxes = mt.tria_sense_mirar(files, XARXES, TOC, XARXES_TOC)
    de_equips, triades_equips = mt.tria_sense_mirar(files, A_EQUIPS, TOC, A_EQUIPS)
    de_forats, triades_forats = mt.tria_sense_mirar(files, A_FORATS, TOC, A_FORATS)
    triades = {XARXES_TOC: triades_xarxes, A_EQUIPS: triades_equips, A_FORATS: triades_forats}
    mpc.comprova_les_triades(triades)
    metodes = pd.concat([de_xarxes, de_equips, de_forats], ignore_index=True)
    c = mt.comparacio(metodes, A_FORATS, XARXES_TOC, TOC, amb_criteri=True)
    c_equips = mt.comparacio(metodes, A_FORATS, A_EQUIPS, TOC, amb_criteri=False)
    passa, millor = mt.compleix(c), mpc.millor_d_un_escenari(c_equips, CURTS)
    per_font = {(font, contra): mt.comparacio(metodes[metodes["font"] == font], A_FORATS, contra, TOC,
                                              amb_criteri=False)
                for font in FONTS for contra in (XARXES_TOC, A_EQUIPS)}
    fets = pd.DataFrame([f for tros in en_paral_lel(
        "que_hi_fa", [(nom, {A_EQUIPS: triades_equips[nom], A_FORATS: triades_forats[nom]}) for nom in fonts.NOMS],
        args.processos) for f in tros])
    encerts_ = pd.DataFrame([f for tros in en_paral_lel("encerts", list(itertools.product(fonts.NOMS, mp.QUARTS)),
                                                         args.processos) for f in tros])
    contingut = {"clau": clau_dels_resultats(), "passa": passa, "millor_fins_ara": millor,
                 "comparacio": t3.registres(c), "contra_a_equips_sencers": t3.registres(c_equips),
                 "triades": triades, "files": t3.registres(files[files["metode"] == A_FORATS]),
                 "per_font": {f"{font} · {contra}": t3.registres(t) for (font, contra), t in per_font.items()},
                 "que_hi_fa": t3.registres(fets), "encerts": t3.registres(encerts_)}
    escriu(contingut, markdown(metodes, triades, c, passa, c_equips, millor, per_font, fets, encerts_))


if __name__ == "__main__":
    main()
