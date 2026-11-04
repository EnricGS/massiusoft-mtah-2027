"""Per què no passa la T3r (`docs/pla-tocs.md`, «Per què no passa la T3r»).

    cd codi && uv run python -I -m banc.analisi_t3r

Amb el que han desat els bancs de la T3p i de la T3r (les probabilitats d'A xarxes, la seva q i la d'A q) i el
decodificador triat a cada partit a la veritat de toc. Es comprova que l'spellF1 de cada partit és el del banc de la
T3r. Al net, als quatre ×¼ i a «partit ×¼», a la veritat de toc:

1. **Els canvis que fa el decodificador:** quants canvis d'equip fa cada model, quants dels reals troba i quants dels
   seus encerten (un de l'altra llista a 1 s o menys), amb la pilota i als forats.
2. **D'on ve el sostre de la q:** la q perfecta (com a `banc/sostre_curtes.py`), i perfecta només en una banda: als
   canvis (on n'hi ha, 0,99; a la resta, l'apresa) o fora dels canvis (on no n'hi ha, 0,0001; als canvis,
   l'apresa). I fora, però només a més d'1 s dels canvis: treu els canvis falsos, però no els que es fan una mica
   abans o després. Amb la q d'A xarxes i amb la d'A q.
3. **La q com a classificador** de les imatges a 6 o menys d'un canvi: l'AUC i les falses alarmes (la part de les
   altres imatges amb la q a 0,3 o més), amb la pilota i als forats.

Escriu `resultats/analisi-t3r.md`. Dades obertes, només per saber-ho.
"""

from __future__ import annotations

import itertools
import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from banc import analisi_t3p as t3p
from banc import analisi_t3q as t3q
from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_canvis2 as t3j
from banc import model_a_partit as mp
from banc import model_a_q as mq
from banc import sostre_curtes as sc
from banc import veritat_toc as vt
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ESCENARIS = t3q.ESCENARIS                           # el net, els quatre ×¼ i «partit ×¼»
SIS = mq.SIS
XARXES, XARXES_TOC, A_Q = mq.XARXES, mq.XARXES_TOC, mq.A_Q
SEMPRE, TOC = mq.SEMPRE, mq.TOC
AMB_PILOTA, ALS_FORATS = mq.AMB_PILOTA, mq.ALS_FORATS
TOL = pm.FPS                                        # un canvi «troba» l'altre si n'és a 1 s o menys
ALS_CANVIS, FORA = "perfecta als canvis", "perfecta fora dels canvis"
LLUNY = "perfecta a més d'1 s dels canvis"
DECODIFICADOR = {XARXES: XARXES_TOC, A_Q: A_Q}      # el decodificador de cada model, triat a la veritat de toc
SOSTRES = (A_Q, sc.Q_PERFECTA, *(f"{m}, {s}" for m in (XARXES, A_Q) for s in (ALS_CANVIS, FORA, LLUNY)))
DIR_RESULTATS = mq.DIR_RESULTATS


def triades() -> dict[str, dict[str, list]]:
    """El decodificador triat a cada partit pel banc de la T3r."""
    return json.loads((DIR_RESULTATS / "model-a-q.json").read_text())["triades"]


def files_del_banc() -> pd.DataFrame:
    return pd.DataFrame(json.loads((DIR_RESULTATS / "model-a-q.json").read_text())["files"])


def comprova(files: pd.DataFrame, metodes: tuple[str, ...] = tuple(DECODIFICADOR)) -> None:
    """Les prediccions de `metodes` (A xarxes i A q) són les del banc de la T3r: el mateix spellF1, partit a
    partit."""
    banc, trs = files_del_banc(), triades()
    esperat = []
    for metode in metodes:
        for nom, (w, lam, d_min) in trs[DECODIFICADOR[metode]].items():
            tria = ((banc["metode"] == metode) & (banc["veritat"] == TOC) & (banc["partit"] == nom)
                    & (banc["w"] == w) & (banc["lam"] == lam) & (banc["d_min"] == d_min))
            esperat.append(banc[tria][["partit", "escenari", "spell_f1"]].assign(sostre=metode))
    esperat = pd.concat(esperat, ignore_index=True)
    aqui = files[files["sostre"].isin(metodes)]
    junts = aqui.merge(esperat, on=["sostre", "partit", "escenari"], suffixes=("", " del banc"), how="left")
    if (aqui.empty or set(aqui["sostre"]) != set(metodes) or junts["spell_f1 del banc"].isna().any()
            or not np.allclose(junts["spell_f1"], junts["spell_f1 del banc"], rtol=0, atol=1e-12)):
        raise RuntimeError("Les prediccions no són les del banc de la T3r")


def a_prop(de: np.ndarray, a: np.ndarray, tol: int) -> np.ndarray:
    """Per a cada imatge de `de`, si n'hi ha alguna d'`a` a `tol` imatges o menys."""
    if len(a) == 0:
        return np.zeros(len(de), dtype=bool)
    a = np.sort(a)
    i = np.searchsorted(a, de)
    abans, despres = a[np.clip(i - 1, 0, len(a) - 1)], a[np.clip(i, 0, len(a) - 1)]
    return np.minimum(np.abs(de - abans), np.abs(despres - de)) <= tol


def compta_canvis(reals: np.ndarray, predits: np.ndarray, al_forat: np.ndarray, tol: int = TOL) -> list[dict]:
    """Amb la pilota i als forats: quants canvis reals hi ha i quants en troba el model (un dels seus a `tol` o
    menys), i quants en fa i quants n'encerta (un de real a `tol` o menys). Cada canvi va on és la seva imatge."""
    trobats, encertats = a_prop(reals, predits, tol), a_prop(predits, reals, tol)
    files = []
    for on, forat in ((AMB_PILOTA, False), (ALS_FORATS, True)):
        r, p = al_forat[reals] == forat, al_forat[predits] == forat
        files.append({"on": on, "n reals": int(r.sum()), "n trobats": int(trobats[r].sum()),
                      "n predits": int(p.sum()), "n encertats": int(encertats[p].sum())})
    return files


def q_als_canvis(q: np.ndarray, a_prop_d_un_canvi: np.ndarray) -> np.ndarray:
    return np.where(a_prop_d_un_canvi, sc.Q_CANVI, q)


def q_fora_dels_canvis(q: np.ndarray, a_prop_d_un_canvi: np.ndarray) -> np.ndarray:
    return np.where(a_prop_d_un_canvi, q, t3i.Q_MINIM)


def classificador(q: np.ndarray, a_prop_d_un_canvi: np.ndarray, tria: np.ndarray) -> dict[str, float]:
    """La q, a les imatges de `tria`, com a classificador de les que són a prop d'un canvi: l'AUC, i la part de les
    altres amb la q a `t3j.Q_ALTA` o més (falses alarmes)."""
    y, s = a_prop_d_un_canvi[tria], q[tria]
    auc = float(roc_auc_score(y, s)) if len(np.unique(y)) == 2 else np.nan
    altres = s[~y]
    return {"auc": auc, "alarmes": float((altres >= t3j.Q_ALTA).mean()) if len(altres) else np.nan}


def tasca(nom_escenari: tuple[str, str]) -> dict[str, list[dict]]:
    nom, escenari = nom_escenari
    de_sempre = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    p_toc = replace(de_sempre, veritat=toc)
    trams = avalua.trams_valids(p_toc)
    a_prop_d_un_canvi, reals = t3i.objectiu(toc, trams), t3i.canvis(toc, trams)
    a_1_s_d_un_canvi = t3i.objectiu(toc, trams, k=TOL)
    dins = np.zeros(len(toc), dtype=bool)
    for a, b in trams:
        dins[a:b] = True
    al_forat = sc.forats(~np.isnan(de_sempre.tracking.pilota[:, 0]))
    probes, prior = mp.segon((nom, SIS), entrena=False)
    relativa = log_relativa(probes[escenari].astype(float), prior)
    les_q = {XARXES: mp.q((nom, SIS), entrena=False)[escenari].astype(float),
             A_Q: mq.q(nom, entrena=False)[escenari].astype(float)}
    trs = triades()
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}

    def decodifica(q: np.ndarray, metode: str) -> np.ndarray:
        w, lam, d_min = trs[DECODIFICADOR[metode]][nom]
        return t3i.per_trams(relativa, q, de_sempre.trams, w, lam, int(d_min))

    def fila(sostre: str, pred: np.ndarray) -> dict:
        return {**comu, "sostre": sostre, "spell_f1": avalua.puntua(p_toc, pred)["spell_f1"]}

    files, canvis, de_la_q = [], [], []
    for metode, q in les_q.items():
        pred = decodifica(q, metode)
        files += [fila(metode, pred), fila(f"{metode}, {ALS_CANVIS}", decodifica(q_als_canvis(q, a_prop_d_un_canvi),
                                                                                  metode)),
                  fila(f"{metode}, {FORA}", decodifica(q_fora_dels_canvis(q, a_prop_d_un_canvi), metode)),
                  fila(f"{metode}, {LLUNY}", decodifica(q_fora_dels_canvis(q, a_1_s_d_un_canvi), metode))]
        canvis += [{**comu, "metode": metode, **f}
                   for f in compta_canvis(reals, t3i.canvis(pred, trams), al_forat)]
        de_la_q += [{**comu, "metode": metode, "on": on, **classificador(q, a_prop_d_un_canvi, tria)}
                    for on, tria in ((AMB_PILOTA, dins & ~al_forat), (ALS_FORATS, dins & al_forat))]
    files.append(fila(sc.Q_PERFECTA, decodifica(sc.q_perfecta(toc, trams), XARXES)))
    return {"files": files, "canvis": canvis, "q": de_la_q}


def taula_canvis(canvis: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i lloc: els canvis reals, i de cada model, quants en fa, la part dels reals que troba i la part
    dels seus que encerten."""
    g = canvis.groupby(["escenari", "on", "metode"], sort=False)[["n reals", "n trobats", "n predits",
                                                                 "n encertats"]].sum()
    metodes = list(dict.fromkeys(canvis["metode"]))
    t = pd.DataFrame({"n reals": g["n reals"].xs(metodes[0], level="metode")})
    for m in metodes:
        de_m = g.xs(m, level="metode")
        t[f"n predits · {m}"] = de_m["n predits"]
        t[f"troba · {m}"] = de_m["n trobats"] / de_m["n reals"]
        t[f"encerta · {m}"] = de_m["n encertats"] / de_m["n predits"]
    return t


def taula_q(de_la_q: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i lloc: l'AUC i les falses alarmes de cada q (mitjana dels partits)."""
    t = de_la_q.groupby(["escenari", "on", "metode"], sort=False)[["auc", "alarmes"]].mean().unstack("metode")
    t = t.reindex(index=pd.MultiIndex.from_tuples(list(dict.fromkeys(zip(de_la_q["escenari"], de_la_q["on"]))),
                                                  names=["escenari", "on"]))
    t.columns = [f"{que} · {m}" for que, m in t.columns]
    return t


def main() -> None:
    with ProcessPoolExecutor(max_workers=10) as feina:
        tasques = list(feina.map(tasca, itertools.product(fonts.NOMS, ESCENARIS)))
    files, canvis, de_la_q = (pd.DataFrame([f for t in tasques for f in t[k]]) for k in ("files", "canvis", "q"))
    comprova(files)
    sortida = [
        "# Banc obert · Per què no passa la T3r", "",
        "Generat amb `uv run python -I -m banc.analisi_t3r`, amb el que han desat `banc.model_a_partit` i",
        "`banc.model_a_q`. Dades obertes. Només per saber-ho. Tot a la veritat de toc, amb el decodificador triat a",
        f"cada partit a la veritat de toc. Les prediccions d'{XARXES} i d'{A_Q} són les del banc de la T3r (✓",
        "comprovat: el mateix spellF1 a cada partit).", "",
        "## Els canvis que fa el decodificador", "",
        f"Els canvis d'equip (deu partits). *Troba:* la part dels reals amb un del model a {TOL} imatges (1 s) o",
        "menys. *Encerta:* la part dels del model amb un de real a 1 s o menys. Cada canvi va on és la seva imatge:",
        f"als forats (sense pilota, i a {t3i.K} imatges o menys) o amb la pilota.", "",
        t3p.md(taula_canvis(canvis)), "",
        "## D'on ve el sostre de la q", "",
        f"spellF1 d'{XARXES} (mitjana dels deu partits) i quant hi guanya cada model. *q perfecta:* el decodificador",
        f"sap on canvia l'equip ({sc.Q_CANVI} a {t3i.K} imatges o menys d'un canvi de la veritat, {t3i.Q_MINIM:g} a la",
        f"resta). *{ALS_CANVIS}:* {sc.Q_CANVI} a prop dels canvis, i la q apresa a la resta. *{FORA}:*",
        f"{t3i.Q_MINIM:g} lluny dels canvis, i la q apresa a prop. *{LLUNY}:* com l'anterior, però {t3i.Q_MINIM:g}",
        f"només a més de {TOL} imatges (1 s) d'un canvi: treu els canvis falsos, però no els que es fan una mica abans",
        f"o després. Les probabilitats sempre són les d'{XARXES}.", "",
        t3p.md(sc.taula_guany(files, SOSTRES)), "",
        "## La q com a classificador", "",
        f"De les imatges a {t3i.K} o menys d'un canvi (mitjana dels partits). *Alarmes:* la part de les altres imatges",
        f"amb la q a {t3j.Q_ALTA:g} o més.", "",
        t3p.md(taula_q(de_la_q)), "",
        "## Passaria el criteri als ×¼?", "",
        f"El guany de mitjana · en quants partits guanya · ✓ si passaria (> {t3.SOROLL}, l'interval del 95 % per",
        f"sobre de zero i {t3.GUANYA_MINIM} partits de 10 o més).", "",
        *sc.taula_criteri(files, SOSTRES), "",
    ]
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "analisi-t3r.md").write_text("\n".join(sortida))
    print("\n".join(sortida))


if __name__ == "__main__":
    main()
