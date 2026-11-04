"""La q veu el que veu el segon (T3r del pla per tocs, `docs/pla-tocs.md`, «T3r»; D-50).

    cd codi && uv run python -I -m banc.model_a_q [--processos 12] [--processos-models 4]

A xarxes tal qual, amb una sola diferència: la q (el classificador de canvis de la T3i) aprèn amb la taula del segon
(`t3m.taula_segon`: la d'A contacte, els senyals de l'aturada i els de les cinc xarxes) en lloc de la d'A contacte
sola. Les mostres són les mateixes imatges que les de la q d'A xarxes, amb el mateix objectiu (a la veritat de
sempre). El primer, les cinc xarxes i el segon són els d'A xarxes, de la memòria cau de la T3p.

1. **En començar,** A xarxes, amb la memòria cau, ha de donar a cada punt de la graella i a les dues veritats
   l'spellF1 del banc de la T3q.
2. **A q:** la q de cada partit, entrenada amb els altres nou (`dades/banc/a-q/`). El decodificador, amb la graella
   de la T3j, triat amb els altres nou als quatre ×¼ a la veritat de toc; el d'A xarxes, igual.
3. **El criteri** del pla: A q contra A xarxes, a la veritat de toc. Als quatre ×¼ guanya clarament; al net, als ×1,
   al soroll2 i a «partit ×¼», no perd. Si no passa, la regla del millor fins ara. Només per saber-ho: contra A
   xarxes amb el decodificador de la cadena, tots dos a la veritat de sempre, per font, i quants canvis troba cada q.

Escriu `resultats/model-a-q.json` i `resultats/model-a-q.md`. Tot són dades obertes. Els mòduls d'abans no es toquen.
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

from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_canvis2 as t3j
from banc import model_a_context as t3e
from banc import model_a_partit as mp
from banc import model_a_quart as t3b
from banc import model_a_toc as mt
from banc import model_a_xarxa as t3m
from banc import model_a_xarxes as t3o
from banc import sostre_curtes as sc
from banc import veritat_toc as vt
from cadena import model
from possessio.decodificacio import log_relativa

ESCENARIS = mp.ESCENARIS                            # els deu de la T3 i «partit ×¼»
QUARTS = t3.QUARTS
SIS = t3o.ENTRENAMENT
XARXES, XARXES_TOC = mt.XARXES, mt.XARXES_TOC       # A xarxes, amb el decodificador de la cadena i triat a la de toc
A_Q = "A q"
SEMPRE, TOC = mt.SEMPRE, mt.TOC
ALTRES = ((A_Q, XARXES, TOC), (A_Q, XARXES_TOC, SEMPRE))      # només per saber-ho
FONTS = ("dfl", "metrica")
AMB_PILOTA, ALS_FORATS = "amb pilota", "als forats"
DIR_CAU = fonts.DIR_CAU / "a-q"
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


def cau(peca: str, *qui: object) -> Path:
    return DIR_CAU / f"{peca}-{'-'.join(map(str, qui))}.npz"


def mostres_q(prova: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Les imatges i l'objectiu de la q d'A xarxes (`mp.mostres_q`), amb la taula del segon (`mp.mostres_segon`)."""
    primers, de_les_xarxes = {}, {}
    for i in range(t3e.GRUPS):
        primers |= mp.primer_del_grup((prova, i, SIS))
        de_les_xarxes |= mp.xarxes_del_grup((prova, i, SIS))
    xs, ys = [], []
    for (nom, e), primer in primers.items():
        p = mp.degradat(nom, e)
        x, y = t3i.mostres(p, t3m.taula_segon(p, primer.astype(float), de_les_xarxes[(nom, e)].astype(float)))
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def entrena_q(x: pd.DataFrame, y: np.ndarray) -> lgb.Booster:
    """Com la q d'A xarxes (`mp.q`): LightGBM amb els paràmetres de la T3i."""
    return lgb.train(t3i.PARAMS, lgb.Dataset(x, label=y, free_raw_data=True), num_boost_round=model.RONDES)


def q(prova: str, entrena: bool = True) -> dict[str, np.ndarray]:
    """Les q d'A q al partit `prova`, a tots els escenaris, entrenada amb els altres nou. Amb `entrena=False`, només
    les llegeix de la memòria cau, i si no hi són o són d'un altre codi, s'atura."""
    cami = cau("q", prova)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les q d'{A_Q} de {prova}, o són d'un altre codi")
        x, y = mostres_q(prova)
        entrenat = entrena_q(x, y)
        del x
        primers, de_les_xarxes = mp.primer_de_la_prova((prova, SIS)), mp.xarxes_de_la_prova((prova, SIS))
        desat = {}
        for i, e in enumerate(ESCENARIS):
            p = mp.degradat(prova, e)
            taula = t3m.taula_segon(p, primers[e].astype(float), de_les_xarxes[e].astype(float))
            desat[f"e{i}"] = t3i.q_de(entrenat, taula).astype(np.float32)
        desa(cami, **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(ESCENARIS)}


def de_qui(metode: str, nom: str) -> tuple[dict[str, np.ndarray], np.ndarray, dict[str, np.ndarray]]:
    """Les probabilitats i el prior d'A xarxes (de la memòria cau de la T3p), amb la seva q o amb la d'A q."""
    probes, prior = mp.segon((nom, SIS), entrena=False)
    return probes, prior, (mp.q((nom, SIS), entrena=False) if metode == XARXES else q(nom, entrena=False))


def graella(tasca: tuple[str, str, tuple[str, ...]]) -> list[dict]:
    """Un partit, un escenari i els mètodes: cada punt de la graella de la T3j, puntuat a les dues veritats."""
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


def files_t3q() -> pd.DataFrame:
    return pd.DataFrame(json.loads((mt.DIR_RESULTATS / "model-a-toc.json").read_text())["files"])


def comprova_a_xarxes(files: pd.DataFrame) -> None:
    """A xarxes, amb la memòria cau, dona a cada punt de la graella i a les dues veritats l'spellF1 del banc de la
    T3q."""
    claus = ["partit", "escenari", "veritat", "w", "lam", "d_min"]
    aqui = files[files["metode"] == XARXES][[*claus, "spell_f1"]]
    del_banc = files_t3q()
    del_banc = del_banc[del_banc["metode"] == XARXES][[*claus, "spell_f1"]]
    junts = aqui.merge(del_banc, on=claus, suffixes=("", " del banc"), how="outer")
    if (len(junts) != len(aqui) or junts.isna().any().any()
            or not np.allclose(junts["spell_f1"], junts["spell_f1 del banc"], rtol=0, atol=1e-12)):
        raise RuntimeError(f"{XARXES} no dona el del banc de la T3q")


def troba(tasca: tuple[str, str]) -> list[dict]:
    """Un partit i un escenari: quants canvis de la veritat de toc troba cada q (hi arriba a `t3j.Q_ALTA` a `t3i.K`
    imatges o menys), amb la pilota i als forats (`sc.forats`: sense pilota, i a `t3i.K` imatges o menys)."""
    nom, escenari = tasca
    p = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    canvis = t3i.canvis(toc, avalua.trams_valids(replace(p, veritat=toc)))
    al_forat = sc.forats(~np.isnan(p.tracking.pilota[:, 0]))[canvis]
    files = []
    for metode, q_ in ((XARXES, mp.q((nom, SIS), entrena=False)), (A_Q, q(nom, entrena=False))):
        de_l_escenari = q_[escenari].astype(float)
        trobat = np.array([de_l_escenari[max(c - t3i.K, 0):c + t3i.K + 1].max() >= t3j.Q_ALTA for c in canvis],
                          dtype=bool)
        for on, tria in ((AMB_PILOTA, ~al_forat), (ALS_FORATS, al_forat)):
            files.append({"partit": nom, "font": p.font, "escenari": escenari, "metode": metode, "on": on,
                          "canvis": int(tria.sum()), "trobats": int(trobat[tria].sum())})
    return files


def millor_fins_ara(c: pd.DataFrame) -> dict[str, bool]:
    """La regla del pla, escrita abans: als quatre ×¼, la diferència és positiva i l'interval del 95 % no toca el zero;
    a «partit ×¼», la diferència no és negativa; a la resta, no baixa de −`t3.SOROLL`."""
    quarts, partit = c["escenari"].isin(QUARTS), c["escenari"] == mp.PARTIT
    return {"quarts": bool(((c["diferencia"] > 0) & (c["baix"] > 0))[quarts].all()),
            "partit": bool((c["diferencia"] >= 0)[partit].all()),
            "altres": bool((c["diferencia"] >= -t3.SOROLL)[~quarts & ~partit].all())}


def _marca(v: bool) -> str:
    return "✓" if v else "✗"


def _regla(millor: dict[str, bool]) -> list[str]:
    es = all(millor.values())
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | "
            f"{_marca(millor['quarts'])} |",
            f"| «{mp.PARTIT}» | la diferència no és negativa | {_marca(millor['partit'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {_marca(millor['altres'])} |", "",
            f"**{A_Q} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_Q if es else XARXES}.", ""]


def _troba(t: pd.DataFrame) -> list[str]:
    g = t.groupby(["escenari", "on", "metode"], sort=False)[["canvis", "trobats"]].sum()
    linies = [f"| escenari | on | canvis | {XARXES} | {A_Q} |", "|---|---|---|---|---|"]
    for (escenari, on), f in g.groupby(level=["escenari", "on"], sort=False):
        f = f.droplevel(["escenari", "on"])
        canvis = int(f.loc[XARXES, "canvis"])
        parts = " | ".join(f"{100 * f.loc[m, 'trobats'] / canvis:.0f} %" if canvis else "—" for m in (XARXES, A_Q))
        linies.append(f"| {escenari} | {on} | {canvis} | {parts} |")
    return linies


def _triades(triades: dict) -> list[str]:
    linies = []
    for metode, t in triades.items():
        compta: dict[str, int] = {}
        for w, lam, d_min in t.values():
            clau_ = f"w = {w:g}, λ = {lam:g}, durada mínima {d_min}"
            compta[clau_] = compta.get(clau_, 0) + 1
        linies.append(f"- **{metode}:** " + "; ".join(f"{k} ({n} partits)" for k, n in compta.items()))
    return linies


def markdown(metodes: pd.DataFrame, triades: dict, c: pd.DataFrame, passa: dict[str, bool],
             millor: dict[str, bool], altres: dict[tuple[str, str, str], pd.DataFrame],
             per_font: dict[str, pd.DataFrame], trobats: pd.DataFrame) -> str:
    linies = ["# Banc obert · La q veu el que veu el segon (T3r)", "",
              "Generat amb `uv run python -I -m banc.model_a_q`. Dades obertes: 7 partits de DFL (IDSSE, CC BY 4.0) i",
              "els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el criteri:",
              "`docs/pla-tocs.md`, «T3r», i la capçalera de `banc/model_a_q.py`. Es puntua a la veritat de toc, llevat",
              "d'on es diu.", "",
              f"**{XARXES}** és el de la cadena, amb les peces de la memòria cau de la T3p (✓ comprovat: a cada punt de",
              f"la graella dona l'spellF1 del banc de la T3q). **{A_Q}** és el mateix, amb la q apresa amb la taula del",
              "segon.", "",
              f"## {A_Q} contra {XARXES_TOC} (spellF1): el criteri", "",
              *t3b._taula(c, A_Q, XARXES_TOC), "", *mt._criteris(passa)]
    if not all(passa.values()):
        linies += ["## No passa: és el millor fins ara?", "", *_regla(millor)]
    for (nou, contra, veritat), taula in altres.items():
        linies += [f"## {mt.nom_de(nou, contra, veritat)}, només per saber-ho", "",
                   *t3i._comparacio(taula, nou, contra), ""]
    for font, taula in per_font.items():
        linies += [f"## {A_Q} contra {XARXES_TOC}, només els partits de {font}", "",
                   *t3i._comparacio(taula, A_Q, XARXES_TOC), ""]
    linies += ["## Quants canvis troba cada q", "",
               f"Els canvis d'equip de la veritat de toc on la q arriba a {t3j.Q_ALTA:g} a {t3i.K} imatges o menys. Els",
               f"forats són les imatges sense pilota i les que en són a {t3i.K} o menys.", "", *_troba(trobats), "",
               "## L'spellF1 de cada mètode (mitjana dels deu partits)", "",
               *mt._mitjanes(metodes, [XARXES, XARXES_TOC, A_Q]), "## Els decodificadors triats", "",
               *_triades(triades), ""]
    return "\n".join(linies)


def clau() -> str:
    """El que fa les q d'aquí: les peces d'A xarxes i això."""
    h = hashlib.sha256((mp.CLAU + repr((SIS, ESCENARIS, t3i.PARAMS, model.RONDES, model.PAS))).encode())
    for funcio in (mostres_q, entrena_q, q):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + vt.CLAU + mt.clau_dels_resultats()).encode())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_a_q as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        return list(feina.map(getattr(aquest, fes), tasques))


def entrena_les_q(processos: int) -> None:
    from banc import model_a_q as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.q, fonts.NOMS)):
            print(f"· {nom}: la q d'{A_Q} feta", flush=True)


def files_de(metodes: tuple[str, ...], processos: int) -> pd.DataFrame:
    tasques = [(nom, e, metodes) for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    return pd.DataFrame([f for tros in en_paral_lel("graella", tasques, processos) for f in tros])


def escriu(contingut: dict, md: str) -> None:
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-a-q.json").write_text(json.dumps(contingut, indent=1, default=float, allow_nan=False))
    (DIR_RESULTATS / "model-a-q.md").write_text(md)
    print(md)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=4, help="models alhora")
    args = ap.parse_args()
    for nom in fonts.NOMS:
        de_qui(XARXES, nom)
        vt.veritat(nom)
    files = files_de((XARXES,), args.processos)
    comprova_a_xarxes(files)
    print(f"· {XARXES} dona el del banc de la T3q", flush=True)
    entrena_les_q(args.processos_models)
    files =pd.concat([files, files_de((A_Q,), args.processos)], ignore_index=True)
    de_xarxes, triades_xarxes = mt.tria_sense_mirar(files, XARXES, SEMPRE, XARXES)
    mt.comprova_el_decodificador(triades_xarxes)
    xarxes_toc, triades_xarxes_toc = mt.tria_sense_mirar(files, XARXES, TOC, XARXES_TOC)
    de_q, triades_q = mt.tria_sense_mirar(files, A_Q, TOC, A_Q)
    metodes = pd.concat([de_xarxes, xarxes_toc, de_q], ignore_index=True)
    c = mt.comparacio(metodes, A_Q, XARXES_TOC, TOC, amb_criteri=True)
    passa, millor = mt.compleix(c), millor_fins_ara(c)
    altres = {qui: mt.comparacio(metodes, *qui, amb_criteri=False) for qui in ALTRES}
    per_font = {font: mt.comparacio(metodes[metodes["font"] == font], A_Q, XARXES_TOC, TOC, amb_criteri=False)
                for font in FONTS}
    tasques = list(itertools.product(fonts.NOMS, ESCENARIS))
    trobats = pd.DataFrame([f for tros in en_paral_lel("troba", tasques, args.processos) for f in tros])
    triades = {XARXES: triades_xarxes, XARXES_TOC: triades_xarxes_toc, A_Q: triades_q}
    contingut = {"clau": clau_dels_resultats(), "passa": passa, "millor_fins_ara": millor,
                 "comparacio": t3.registres(c), "triades": triades, "files": t3.registres(files),
                 "altres": {mt.nom_de(*qui): t3.registres(t) for qui, t in altres.items()},
                 "per_font": {font: t3.registres(t) for font, t in per_font.items()},
                 "trobats": t3.registres(trobats)}
    escriu(contingut, markdown(metodes, triades, c, passa, millor, altres, per_font, trobats))


if __name__ == "__main__":
    main()
