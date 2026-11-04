"""Per què no passa la T3p: on guanya i on perd A partit contra A xarxes (`docs/pla-tocs.md`, «Per què no passa la
T3p»). Només per saber-ho.

    cd codi && uv run python -I -m banc.analisi_t3p

Amb les probabilitats i les q que ha desat `banc.model_a_partit`, i el decodificador triat a cada partit
(`resultats/model-a-partit.json`): la D (pilota morta), l'equip, les possessions per durada i, abans de decodificar,
segons si la pilota es veu. Escriu `resultats/analisi-t3p.md`. Tot són dades obertes.
"""

from __future__ import annotations

import functools
import itertools
import json
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_partit as mp
from banc import model_a_xarxes as t3o
from cadena import model
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

METODES = (t3o.XARXES, mp.A_PARTIT)
ESCENARIS = (mp.PARTIT, *t3.QUARTS)
DURADES = (0, 1, 2, 5, 10, np.inf)
NOMS_DURADA = ("<1 s", "1-2 s", "2-5 s", "5-10 s", "≥10 s")


@functools.cache
def triades() -> dict[str, dict[str, list]]:
    """El decodificador triat a cada partit pel banc de la T3p."""
    return json.loads((mp.DIR_RESULTATS / "model-a-partit.json").read_text())["triades"]


def tram(durada_s: float) -> str:
    return NOMS_DURADA[int(np.searchsorted(DURADES, durada_s, side="right")) - 1]


def aparellats(de: list, contra: list) -> np.ndarray:
    """De cada tros de `de`, la part dels llindars d'IoU on s'aparella amb un de `contra` (com la mètrica)."""
    solapes = pm.spell_overlaps(de, contra)
    return np.mean([pm.matched_gt_flags(solapes, len(de), t) for t in pm.SPELL_IOUS], axis=0) if de else np.zeros(0)


def morts(codis: np.ndarray, trams) -> list[tuple[int, int]]:
    return [(a, b) for a, b, k in pm.segments(codis, trams) if k == pm.D]


def tasca(nom_escenari: tuple[str, str]) -> dict[str, list[dict]]:
    nom, escenari = nom_escenari
    p = mp.degradat(nom, escenari)
    gt = p.veritat.astype(np.int8)
    trams = avalua.trams_valids(p)
    vista = ~np.isnan(p.tracking.pilota[:, 0])
    puntuat = gt != pm.X
    comu = {"partit": nom, "font": p.font, "escenari": escenari}
    out = {"cm": [], "abans": [], "possessions": [], "d": []}
    for metode in METODES:
        entrenament = mp.ENTRENAMENT[metode]
        probes, prior = mp.segon((nom, entrenament), entrena=False)
        w, lam, d_min = triades()[nom][metode]
        q = mp.q((nom, entrenament), entrena=False)[escenari].astype(float)
        pred = t3i.per_trams(log_relativa(probes[escenari].astype(float), prior), q, p.trams, w, lam, int(d_min))
        c = {**comu, "metode": metode}
        out["cm"].append({**c, "cm": pm.scored_confusion(pm.confusion(gt, pred)).ravel().tolist()})
        # abans de decodificar: l'encert de la classe més probable, segons la veritat i si la pilota es veu
        bo = np.asarray(model.CLASSES)[np.nan_to_num(probes[escenari], nan=-1.0).argmax(1)] == gt
        for joc, v in itertools.product((True, False), (True, False)):
            sel = puntuat & ((gt != pm.D) == joc) & (vista == v)
            out["abans"].append({**c, "joc": joc, "pilota": v, "bons": int(bo[sel].sum()), "imatges": int(sel.sum())})
        # les possessions: les reals, per durada, i si s'aparellen; les predites, per durada, i si s'aparellen
        omplert = pm.fill_abstentions(pred, trams)
        reals, predites = pm.possession_spells(gt, trams), pm.possession_spells(omplert, trams)
        for qui, trossos, contra in (("reals", reals, predites), ("predites", predites, reals)):
            for (a, b, _), m in zip(trossos, aparellats(trossos, contra)):
                out["possessions"].append({**c, "qui": qui, "durada": tram((b - a) / pm.FPS), "aparellada": m})
        # la D: cada estona real, si es troba (la meitat o més de D predita) i el desfasament de les vores
        d_pred = morts(omplert, trams)
        es_d = omplert == pm.D
        for a, b in morts(gt, trams):
            trobada = es_d[a:b].mean() >= 0.5
            millor = max(d_pred, key=lambda r: min(b, r[1]) - max(a, r[0]), default=None)
            solapa = millor is not None and min(b, millor[1]) > max(a, millor[0])
            out["d"].append({**c, "qui": "real", "durada": tram((b - a) / pm.FPS), "trobada": bool(trobada),
                             "inici_s": (millor[0] - a) / pm.FPS if solapa else np.nan,
                             "fi_s": (millor[1] - b) / pm.FPS if solapa else np.nan})
        es_d_real = gt == pm.D
        for a, b in d_pred:
            out["d"].append({**c, "qui": "predita", "durada": tram((b - a) / pm.FPS),
                             "trobada": bool(es_d_real[a:b].mean() >= 0.5), "inici_s": np.nan, "fi_s": np.nan})
    return out


def f1s(cm: np.ndarray) -> dict[str, float]:
    cm3 = cm.reshape(pm.N_SCORED, -1)
    p_d, r_d, f_d = pm.per_class_prf(cm3, pm.D)
    return {"F1 H": pm.per_class_prf(cm3, pm.H)[2], "F1 A": pm.per_class_prf(cm3, pm.A)[2], "F1 D": f_d,
            "D precisió": p_d, "D record": r_d, "equip (joc a tots dos)": pm.team_accuracy(cm3)[1],
            "viva/morta F1": pm.alive_dead_f1(cm3)}


def md(t: pd.DataFrame) -> str:
    """La taula en Markdown: els comptes (columnes «n»), sencers; la resta, amb tres decimals."""
    columnes = [" · ".join(c) if isinstance(c, tuple) else str(c) for c in t.columns]
    linies = ["| " + " | ".join([*map(str, t.index.names), *columnes]) + " |",
              "|---" * (len(t.index.names) + len(columnes)) + "|"]
    for idx, fila in t.iterrows():
        idx = idx if isinstance(idx, tuple) else (idx,)
        valors = [f"{x:.0f}" if c.startswith("n") else f"{x:.3f}" for c, x in zip(columnes, fila)]
        linies.append("| " + " | ".join([*map(str, idx), *valors]) + " |")
    return "\n".join(linies)


def perdudes(po: pd.DataFrame) -> pd.DataFrame:
    """De les possessions reals que no s'aparellen (comptades amb la part no aparellada), quantes i quina part
    de totes les perdudes és de cada durada."""
    reals = po[po["qui"] == "reals"].assign(perduda=lambda t: 1 - t["aparellada"])
    n = reals.groupby(["escenari", "metode", "durada"], sort=False)["perduda"].sum()
    return pd.DataFrame({"n perdudes": n, "part": n / n.groupby(level=[0, 1]).transform("sum")}).unstack("metode")


def main() -> None:
    with ProcessPoolExecutor(max_workers=10) as feina:
        trossos = list(feina.map(tasca, itertools.product(fonts.NOMS, ESCENARIS)))
    t = {k: pd.DataFrame([f for tros in trossos for f in tros[k]]) for k in trossos[0]}
    sortida = []
    # 1. per classe: mitjana dels partits
    cm = t["cm"]
    per = pd.DataFrame([{**f[["escenari", "metode"]].to_dict(), **f1s(np.array(f["cm"]))} for _, f in cm.iterrows()])
    sortida += ["## Per classe (mitjana dels deu partits)", "",
                md(per.groupby(["escenari", "metode"], sort=False).mean()), ""]
    # 2. abans de decodificar
    ab = t["abans"].groupby(["escenari", "joc", "pilota", "metode"], sort=False)[["bons", "imatges"]].sum()
    ab = (ab["bons"] / ab["imatges"]).unstack("metode")
    sortida += ["## Abans de decodificar: l'encert de la classe més probable", "", md(ab), ""]
    # 3. possessions per durada
    po = t["possessions"]
    rec = po.groupby(["escenari", "qui", "durada", "metode"], sort=False)["aparellada"].agg(["mean", "size"])
    taula = rec["mean"].unstack("metode").join(rec["size"].unstack("metode").add_prefix("n "))
    sortida += ["## Possessions per durada: la part aparellada (mitjana dels llindars d'IoU)", "",
                "*reals*: el record; *predites*: la precisió. *n*: quantes n'hi ha (els deu partits).", "", md(taula),
                ""]
    # 4. la D
    d = t["d"]
    reals = d[d["qui"] == "real"]
    dr = reals.groupby(["escenari", "durada", "metode"], sort=False).agg(
        trobada=("trobada", "mean"), n=("trobada", "size"), inici_s=("inici_s", lambda s: s.abs().median()),
        fi_s=("fi_s", lambda s: s.abs().median())).unstack("metode")
    pr = d[d["qui"] == "predita"].groupby(["escenari", "durada", "metode"], sort=False).agg(
        bona=("trobada", "mean"), n=("trobada", "size")).unstack("metode")
    sortida += ["## Les possessions reals que no s'aparellen, per durada", "", md(perdudes(po)), "",
                "## La D real: si es troba, i el desfasament de les vores (mediana, en s)", "", md(dr), "",
                "## La D predita: la part que és D de veritat", "", md(pr), ""]
    cap = ["# Banc obert · Per què no passa la T3p", "",
           "Generat amb `uv run python -I -m banc.analisi_t3p`, amb el que ha desat `banc.model_a_partit`. Dades",
           "obertes. Només per saber-ho.", ""]
    (mp.DIR_RESULTATS / "analisi-t3p.md").write_text("\n".join(cap + sortida))
    print("\n".join(sortida))


if __name__ == "__main__":
    main()
