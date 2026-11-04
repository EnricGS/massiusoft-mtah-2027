"""Un verificador de les possessions (T3s del pla per tocs, `docs/pla-tocs.md`, «T3s»; D-51).

    cd codi && uv run python -I -m banc.model_a_verificador [--processos 10] [--processos-models 4]

A xarxes tal qual i, després de decodificar, un verificador: un LightGBM binari que diu si cada possessió és
inventada (la veritat de toc no hi té el seu equip a 1 s o menys). Si ho diu, la possessió passa sencera a l'altre
equip (`cf.arregla`), totes alhora sobre la decodificació d'A xarxes. El decodificador d'A xarxes és el triat a la
veritat de toc pel banc de la T3r.

1. **En començar,** A xarxes, amb la memòria cau de la T3p, ha de donar a cada partit l'spellF1 del banc de la T3r.
2. **Amb què aprèn:** per a cada partit que es prova i cada grup dels altres nou (`t3e.grups`), un segon i una q
   entrenats com els d'A xarxes, amb els altres dos grups (`dades/banc/a-verificador/`). Amb el primer i les xarxes
   del grup (de la memòria cau), decodifiquen els partits del grup als sis escenaris d'entrenament, amb el
   decodificador triat per al partit que es prova.
3. **El llindar:** el verificador entrenat amb dos grups puntua les possessions d'A xarxes (les del banc) dels
   partits del tercer, i es queda el llindar que dona més spellF1 de mitjana als nou partits als quatre ×¼.
4. **El verificador del partit,** entrenat amb els tres grups, arregla les possessions d'A xarxes al partit que es
   prova, als deu escenaris de la T3 i a «partit ×¼».
5. **El criteri** del pla: A verificador contra A xarxes, a la veritat de toc. Als quatre ×¼ guanya clarament; al
   net, als ×1, al soroll2 i a «partit ×¼», no perd. Si no passa, la regla del millor fins ara (D-50).

Escriu `resultats/model-a-verificador.json` i `resultats/model-a-verificador.md`. Tot són dades obertes. Els mòduls
d'abans no es toquen.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import inspect
import itertools
import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from banc import analisi_t3p as t3p
from banc import analisi_t3q as t3q
from banc import analisi_t3r as an
from banc import avalua, fonts
from banc import canvis_falsos as cf
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_contacte as t3h
from banc import model_a_context as t3e
from banc import model_a_partit as mp
from banc import model_a_possessio as t3f
from banc import model_a_q as mq
from banc import model_a_quart as t3b
from banc import model_a_toc as mt
from banc import model_a_xarxa as t3m
from banc import veritat_toc as vt
from cadena import model
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ESCENARIS = mp.ESCENARIS                            # els deu de la T3 i «partit ×¼»
QUARTS = t3.QUARTS
SIS = mq.SIS
XARXES_TOC = mq.XARXES_TOC                          # A xarxes, amb el decodificador triat a la veritat de toc
A_VERIFICADOR = "A verificador"
TOC = mq.TOC
FONTS = mq.FONTS
ALTRE, ATURADA, VORA = 0, 1, 2                      # què hi ha abans i després d'una possessió
PROP = 5 * pm.FPS                                   # els canvis d'equip «a prop»: a 5 s o menys
MAI = "mai"
LLINDARS = (0.5, 0.6, 0.7, 0.8, 0.9, MAI)           # de menys a més prudent
TRETS = ("durada", "equip", "l'altre", "aturada", "relativa", "q a l'inici", "q al final", "vista",
         "vista a l'inici", "vista al final", "abans", "després", "durada d'abans", "durada de després",
         "canvis a prop")
PARAMS = {"objective": "binary", "learning_rate": 0.05, "num_leaves": 15, "min_data_in_leaf": 50,
          "feature_fraction": 0.8, "bagging_fraction": 0.8, "bagging_freq": 1, "num_threads": 2,
          "deterministic": True, "force_row_wise": True, "verbose": -1, "seed": 0}
RONDES = 300
DIR_CAU = fonts.DIR_CAU / "a-verificador"
DIR_RESULTATS = t3.DIR_RESULTATS
Tram = tuple[int, int]


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


# Les possessions i els seus trets

def trams_de(trams: tuple[tuple[int, int, int], ...]) -> list[Tram]:
    """Els trams del decodificador, [inici, final), a partir dels del partit (amb l'última imatge inclosa)."""
    return [(inici, ultim + 1) for _, inici, ultim in trams]


def vei(tros: tuple[int, int, int] | None) -> tuple[int, int]:
    """Què és el tros del costat d'una possessió (l'altre equip, una aturada o la vora del tram) i quant dura."""
    if tros is None:
        return VORA, 0
    a, b, codi = tros
    return (ATURADA if codi == pm.D else ALTRE), b - a


def canvis_d_equip(trossos: list[tuple[int, int, int]]) -> np.ndarray:
    """On comença cada possessió d'un equip diferent del de l'anterior, encara que entremig hi hagi una aturada."""
    equips = [(a, k) for a, _, k in trossos if k in pm.POSSESSION_LABELS]
    return np.array([a for (a, k), (_, abans) in zip(equips[1:], equips) if k != abans], dtype=int)


def trets(probes: np.ndarray, relativa: np.ndarray, q: np.ndarray, vista: np.ndarray, a: int, b: int, k: int,
          abans: tuple[int, int, int] | None, despres: tuple[int, int, int] | None,
          canvis: np.ndarray) -> dict[str, float]:
    """Els trets de la possessió [a, b) de l'equip `k`, tots respecte del seu equip."""
    altre = pm.A if k == pm.H else pm.H
    que_abans, durada_abans = vei(abans)
    que_despres, durada_despres = vei(despres)
    return {"durada": b - a, "equip": float(probes[a:b, k].mean()), "l'altre": float(probes[a:b, altre].mean()),
            "aturada": float(probes[a:b, pm.D].mean()),
            "relativa": float((relativa[a:b, k] - relativa[a:b, altre]).mean()),
            "q a l'inici": float(q[max(a - t3i.K, 0):a + t3i.K + 1].max()),
            "q al final": float(q[max(b - t3i.K, 0):b + t3i.K + 1].max()),
            "vista": float(vista[a:b].mean()), "vista a l'inici": float(vista[a]),
            "vista al final": float(vista[b - 1]),
            "abans": que_abans, "després": que_despres, "durada d'abans": durada_abans,
            "durada de després": durada_despres,
            "canvis a prop": int(((canvis >= a - PROP) & (canvis <= b + PROP)).sum())}


def possessions_de(pred: np.ndarray, probes: np.ndarray, relativa: np.ndarray, q: np.ndarray, vista: np.ndarray,
                   trams: list[Tram]) -> pd.DataFrame:
    """Les possessions de `pred`, tram a tram: on són, el seu equip, entre què són i els trets."""
    files = []
    for tram in trams:
        trossos = pm.segments(pred, [tram])
        canvis = canvis_d_equip(trossos)
        for s, (a, b, k) in enumerate(trossos):
            if k not in pm.POSSESSION_LABELS:
                continue
            abans = trossos[s - 1] if s > 0 else None
            despres = trossos[s + 1] if s + 1 < len(trossos) else None
            files.append({"a": a, "b": b, "k": k, "vores": cf.vores(pred, a, b, tram),
                          **trets(probes, relativa, q, vista, a, b, k, abans, despres, canvis)})
    return pd.DataFrame(files, columns=["a", "b", "k", "vores", *TRETS])


def amb_l_objectiu(possessions: pd.DataFrame, toc: np.ndarray) -> pd.DataFrame:
    """Si cada possessió és inventada a la veritat de toc, i si és tota dins de la veritat (cap imatge X)."""
    llocs = list(possessions[["a", "b", "k"]].itertuples(index=False, name=None))
    return possessions.assign(inventada=[cf.inventada(toc, a, b, k) for a, b, k in llocs],
                              dins=[bool(np.all(toc[a:b] != pm.X)) for a, b, _ in llocs])


# El verificador

def entrena(possessions: pd.DataFrame) -> lgb.Booster:
    """Un LightGBM binari, amb els paràmetres del pla, amb les possessions que són tot dins de la veritat."""
    dins = possessions[possessions["dins"]]
    dades = lgb.Dataset(dins[list(TRETS)].to_numpy(dtype=float), label=dins["inventada"].to_numpy(dtype=int))
    return lgb.train(PARAMS, dades, num_boost_round=RONDES)


def probabilitat(verificador: lgb.Booster, possessions: pd.DataFrame) -> np.ndarray:
    """La probabilitat que cada possessió sigui inventada."""
    if possessions.empty:
        return np.zeros(0)
    return verificador.predict(possessions[list(TRETS)].to_numpy(dtype=float))


def arregla_amb(pred: np.ndarray, possessions: pd.DataFrame, prob: np.ndarray, llindar: float | str) -> np.ndarray:
    """`pred`, amb les possessions que el verificador diu inventades (`prob` ≥ `llindar`) a l'altre equip, totes
    alhora; amb «mai», tal qual."""
    if llindar == MAI:
        return pred.copy()
    return cf.arregla(pred, possessions[prob >= llindar].to_dict("records"))


def tria_llindar(files: pd.DataFrame) -> float | str:
    """El llindar amb més spellF1 de mitjana; si n'hi ha més d'un, el més prudent."""
    mitjana = files.groupby("llindar", sort=False)["spell_f1"].mean()
    return [llindar for llindar in LLINDARS if llindar in mitjana.index and mitjana[llindar] == mitjana.max()][-1]


def puntua(toc: np.ndarray, trams: tuple[tuple[int, int, int], ...], pred: np.ndarray) -> float:
    """L'spellF1 a la veritat de toc, amb `avalua.puntua` (només en fa servir la veritat i els trams)."""
    return avalua.puntua(SimpleNamespace(veritat=toc, trams=trams), pred)["spell_f1"]


def compta_canvis(pred: np.ndarray, toc: np.ndarray, trams: list[Tram]) -> dict[str, int]:
    """Els canvis d'equip de `pred` i quants són falsos: sense cap canvi de la veritat a 1 s o menys."""
    predits = t3i.canvis(pred, trams)
    return {"canvis": len(predits), "falsos": int((~an.a_prop(predits, t3i.canvis(toc, trams), an.TOL)).sum())}


# El segon i la q de cada grup

def mostres_segon(prova: str, g: int) -> tuple[pd.DataFrame, np.ndarray]:
    """Com `mp.mostres_segon` amb els sis escenaris d'ara, sense el grup `g`: només els altres dos."""
    xs, ys = [], []
    for i in range(t3e.GRUPS):
        if i == g:
            continue
        primers, de_les_xarxes = mp.primer_del_grup((prova, i, SIS)), mp.xarxes_del_grup((prova, i, SIS))
        for (nom, e), primer in primers.items():
            p = mp.degradat(nom, e)
            x, y = t3f.mostres(p, t3m.taula_segon(p, primer.astype(float), de_les_xarxes[(nom, e)].astype(float)))
            xs.append(x)
            ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def mostres_q(prova: str, g: int) -> tuple[pd.DataFrame, np.ndarray]:
    """Com `mp.mostres_q` amb els sis escenaris d'ara, sense el grup `g`: només els altres dos."""
    xs, ys = [], []
    for i in range(t3e.GRUPS):
        if i == g:
            continue
        for (nom, e), primer in mp.primer_del_grup((prova, i, SIS)).items():
            p = mp.degradat(nom, e)
            x, y = t3i.mostres(p, t3h.taula_segon(p, primer.astype(float)))
            xs.append(x)
            ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def peces_del_grup(tasca: tuple[str, int], entrena: bool = True) -> tuple[dict, np.ndarray, dict]:
    """El segon i la q del grup `g` de `prova`, entrenats com els d'A xarxes amb els altres dos grups: les seves
    probabilitats i les q als partits del grup, als sis escenaris d'entrenament, i el prior. Amb `entrena=False`, només
    les llegeix de la memòria cau, i si no hi són o són d'un altre codi, s'atura."""
    prova, g = tasca
    primers, de_les_xarxes = mp.primer_del_grup((prova, g, SIS)), mp.xarxes_del_grup((prova, g, SIS))
    claus = {qui: f"p{n}" for n, qui in enumerate(primers)}
    cami = cau("peces", prova, g)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten el segon i la q del grup {g} de {prova}, o són d'un altre codi")
        x, y = mostres_segon(prova, g)
        segon, prior = model.entrena(x, y), model.prior(y)
        del x
        x, y = mostres_q(prova, g)
        de_canvis = lgb.train(t3i.PARAMS, lgb.Dataset(x, label=y, free_raw_data=True), num_boost_round=model.RONDES)
        del x
        desat = {"prior": prior}
        for (nom, e), clau_ in claus.items():
            p = mp.degradat(nom, e)
            primer = primers[(nom, e)].astype(float)
            taula = t3m.taula_segon(p, primer, de_les_xarxes[(nom, e)].astype(float))
            desat[f"s_{clau_}"] = model.probabilitats(segon, taula).astype(np.float32)
            desat[f"q_{clau_}"] = t3i.q_de(de_canvis, t3h.taula_segon(p, primer)).astype(np.float32)
        desa(cami, **desat)
    return ({qui: desat[f"s_{c}"] for qui, c in claus.items()}, desat["prior"],
            {qui: desat[f"q_{c}"] for qui, c in claus.items()})


# A xarxes, decodificat

@functools.cache
def triades() -> dict[str, list]:
    """El decodificador d'A xarxes triat a cada partit a la veritat de toc pel banc de la T3r."""
    return an.triades()[XARXES_TOC]


def decodifica(probes: np.ndarray, prior: np.ndarray, q: np.ndarray, trams: tuple[tuple[int, int, int], ...],
               triat: list) -> tuple[np.ndarray, np.ndarray]:
    """Com el banc de la T3r (`mq.graella`): la predicció d'A xarxes i la probabilitat relativa."""
    w, lam, d_min = triat
    relativa = log_relativa(probes, prior)
    return t3i.per_trams(relativa, q, trams, w, lam, int(d_min)), relativa


def del_banc(tasca: tuple[str, str]) -> dict:
    """A xarxes al partit i l'escenari, com al banc de la T3r: la predicció, les possessions amb els trets i
    l'objectiu, els trams, la font i l'spellF1 a la veritat de toc."""
    nom, escenari = tasca
    p = mp.degradat(nom, escenari)
    probes, prior = mp.segon((nom, SIS), entrena=False)
    q = mp.q((nom, SIS), entrena=False)[escenari].astype(float)
    de_l_escenari = probes[escenari].astype(float)
    pred, relativa = decodifica(de_l_escenari, prior, q, p.trams, triades()[nom])
    toc = vt.veritat(nom)
    possessions = possessions_de(pred, de_l_escenari, relativa, q, ~np.isnan(p.tracking.pilota[:, 0]),
                                 trams_de(p.trams))
    return {"pred": pred, "possessions": amb_l_objectiu(possessions, toc), "trams": p.trams, "font": p.font,
            "spell_f1": puntua(toc, p.trams, pred)}


def del_grup(prova: str, g: int) -> pd.DataFrame:
    """Les possessions dels partits del grup `g` de `prova`, als sis escenaris d'entrenament, decodificades amb el
    segon i la q del grup i el decodificador triat per a `prova`, amb els trets i l'objectiu."""
    probes, prior, qs = peces_del_grup((prova, g), entrena=False)
    parts = []
    for (nom, e), de_l_escenari in probes.items():
        p = mp.degradat(nom, e)
        de_l_escenari, q = de_l_escenari.astype(float), qs[(nom, e)].astype(float)
        pred, relativa = decodifica(de_l_escenari, prior, q, p.trams, triades()[prova])
        possessions = possessions_de(pred, de_l_escenari, relativa, q, ~np.isnan(p.tracking.pilota[:, 0]),
                                     trams_de(p.trams))
        parts.append(amb_l_objectiu(possessions, vt.veritat(nom)).assign(partit=nom, escenari=e))
    return pd.concat(parts, ignore_index=True)


# Cada partit que es prova

def llindar_amb_els_nou(prova: str, grups: list[pd.DataFrame], banc: dict[tuple[str, str], dict]) -> list[dict]:
    """Cada llindar als altres nou partits, als quatre ×¼: el verificador entrenat amb dos grups, a les possessions
    d'A xarxes (les del banc) dels partits del tercer."""
    files = []
    for g, partits in enumerate(t3e.grups(prova)):
        verificador = entrena(pd.concat([grups[h] for h in range(t3e.GRUPS) if h != g], ignore_index=True))
        for nom in partits:
            toc = vt.veritat(nom)
            for e in QUARTS:
                b = banc[(nom, e)]
                prob = probabilitat(verificador, b["possessions"])
                files += [{"partit": nom, "escenari": e, "llindar": llindar,
                           "spell_f1": puntua(toc, b["trams"], arregla_amb(b["pred"], b["possessions"], prob, llindar))}
                          for llindar in LLINDARS]
    return files


def prova(tasca: tuple[str, dict[tuple[str, str], dict]]) -> dict:
    """Un partit: el llindar triat amb els altres nou, i A xarxes i A verificador a cada escenari, amb el que ha fet
    el verificador a cada possessió i els canvis d'equip que fa cadascun."""
    nom, banc = tasca
    grups = [del_grup(nom, g) for g in range(t3e.GRUPS)]
    llindar = tria_llindar(pd.DataFrame(llindar_amb_els_nou(nom, grups, banc)))
    verificador = entrena(pd.concat(grups, ignore_index=True))
    toc = vt.veritat(nom)
    files, possessions, canvis = [], [], []
    for e in ESCENARIS:
        b = banc[(nom, e)]
        prob = probabilitat(verificador, b["possessions"])
        arreglada = arregla_amb(b["pred"], b["possessions"], prob, llindar)
        comu = {"partit": nom, "font": b["font"], "escenari": e, "veritat": TOC}
        files += [{**comu, "metode": XARXES_TOC, "spell_f1": b["spell_f1"]},
                  {**comu, "metode": A_VERIFICADOR, "spell_f1": puntua(toc, b["trams"], arreglada)}]
        possessions.append(b["possessions"][["vores", "dins", "inventada"]].assign(
            escenari=e, prob=prob, arreglada=(prob >= llindar) if llindar != MAI else False))
        valids = avalua.trams_valids(SimpleNamespace(veritat=toc, trams=b["trams"]))
        canvis += [{"escenari": e, "metode": metode, **compta_canvis(pred, toc, valids)}
                   for metode, pred in ((XARXES_TOC, b["pred"]), (A_VERIFICADOR, arreglada))]
    return {"partit": nom, "llindar": llindar, "files": files, "possessions": pd.concat(possessions, ignore_index=True),
            "canvis": canvis}


# L'informe

def taula_verificador(possessions: pd.DataFrame) -> pd.DataFrame:
    """Per escenari, amb les possessions dins de la veritat dels deu partits: quantes n'hi ha i quantes són
    inventades, l'AUC del verificador, quantes n'arregla, la part de les arreglades que són inventades (encerta) i la
    part de les inventades que arregla (troba); i el mateix entre dues de l'altre equip i tocant una aturada."""
    files = {}
    for escenari, t in possessions[possessions["dins"]].groupby("escenari", sort=False):
        inv, arr = t["inventada"].to_numpy(dtype=bool), t["arreglada"].to_numpy(dtype=bool)
        fila = {"n possessions": len(t), "n inventades": int(inv.sum()),
                "AUC": float(roc_auc_score(inv, t["prob"])) if 0 < inv.sum() < len(inv) else np.nan,
                "n arreglades": int(arr.sum()), "encerta": inv[arr].mean() if arr.any() else np.nan,
                "troba": arr[inv].mean() if inv.any() else np.nan}
        for vora in (cf.INSERIDA, cf.AL_COSTAT):
            de_la_vora = arr & (t["vores"] == vora).to_numpy()
            fila[f"n arreglades · {vora}"] = int(de_la_vora.sum())
            fila[f"encerta · {vora}"] = inv[de_la_vora].mean() if de_la_vora.any() else np.nan
        files[escenari] = fila
    t = pd.DataFrame.from_dict(files, orient="index")
    t.index.name = "escenari"
    return t


def taula_canvis(canvis: pd.DataFrame) -> pd.DataFrame:
    """Per escenari, als deu partits: els canvis d'equip de cada mètode i la part que són falsos."""
    g = canvis.groupby(["escenari", "metode"], sort=False)[["canvis", "falsos"]].sum()
    files = {}
    for escenari, f in g.groupby(level="escenari", sort=False):
        f = f.droplevel("escenari")
        files[escenari] = {k: v for metode in (XARXES_TOC, A_VERIFICADOR) for k, v in (
            (f"n canvis · {metode}", f.loc[metode, "canvis"]),
            (f"falsos · {metode}", f.loc[metode, "falsos"] / f.loc[metode, "canvis"]))}
    t = pd.DataFrame.from_dict(files, orient="index")
    t.index.name = "escenari"
    return t


def _regla(millor: dict[str, bool]) -> list[str]:
    def marca(v: bool) -> str:
        return "✓" if v else "✗"

    es = all(millor.values())
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | "
            f"{marca(millor['quarts'])} |",
            f"| «{mp.PARTIT}» | la diferència no és negativa | {marca(millor['partit'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {marca(millor['altres'])} |", "",
            f"**{A_VERIFICADOR} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_VERIFICADOR if es else 'A xarxes'}.", ""]


def _mitjanes(metodes: pd.DataFrame) -> list[str]:
    t = metodes.pivot_table(index="escenari", columns="metode", values="spell_f1", sort=False)
    t = t[[XARXES_TOC, A_VERIFICADOR]]
    return ["| escenari | " + " | ".join(t.columns) + " |", "|---" * (len(t.columns) + 1) + "|",
            *(f"| {e} | " + " | ".join(f"{x:.3f}" for x in f) + " |" for e, f in t.iterrows())]


def _llindars(llindars: dict[str, float | str]) -> list[str]:
    compta = pd.Series(list(llindars.values()), dtype=object).value_counts(sort=False)
    return ["; ".join(f"{llindar if llindar == MAI else format(llindar, 'g')} ({n} partits)"
                      for llindar, n in compta.items()) + "."]


def markdown(c: pd.DataFrame, passa: dict[str, bool], millor: dict[str, bool], per_font: dict[str, pd.DataFrame],
             metodes: pd.DataFrame, verificador: pd.DataFrame, canvis: pd.DataFrame,
             llindars: dict[str, float | str]) -> str:
    linies = ["# Banc obert · Un verificador de les possessions (T3s)", "",
              "Generat amb `uv run python -I -m banc.model_a_verificador`. Dades obertes: 7 partits de DFL (IDSSE, CC",
              "BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3s», i la capçalera de `banc/model_a_verificador.py`. Es puntua a la",
              "veritat de toc.", "",
              f"**{XARXES_TOC}** és A xarxes amb el decodificador triat a la veritat de toc, de la memòria cau (✓",
              "comprovat: a cada partit dona l'spellF1 del banc de la T3r). **A verificador** és el mateix, amb les",
              "possessions que el verificador diu inventades passades a l'altre equip.", "",
              f"## {A_VERIFICADOR} contra {XARXES_TOC} (spellF1): el criteri", "",
              *t3b._taula(c, A_VERIFICADOR, XARXES_TOC), "", *mt._criteris(passa)]
    if not all(passa.values()):
        linies += ["## No passa: és el millor fins ara?", "", *_regla(millor)]
    for font, taula in per_font.items():
        linies += [f"## {A_VERIFICADOR} contra {XARXES_TOC}, només els partits de {font}", "",
                   *t3i._comparacio(taula, A_VERIFICADOR, XARXES_TOC), ""]
    linies += ["## El verificador", "",
               "Les possessions d'A xarxes dins de la veritat, als deu partits. *Inventada:* la veritat de toc no hi",
               "té el seu equip a 1 s o menys. *encerta:* de les que arregla, la part que són inventades; *troba:* de les",
               f"inventades, la part que arregla. *{cf.INSERIDA}:* entre dues de l'altre equip; *{cf.AL_COSTAT}:*",
               "tocant una aturada o la vora del tram.", "", t3p.md(t3q.ordena(verificador)), "",
               "## Els canvis d'equip falsos", "",
               f"Els canvis d'equip de cada mètode, i la part sense cap canvi de la veritat a {an.TOL} imatges (1 s) o",
               "menys.", "", t3p.md(t3q.ordena(canvis)), "",
               "## L'spellF1 de cada mètode (mitjana dels deu partits)", "", *_mitjanes(metodes), "",
               "## Els llindars triats", "", *_llindars(llindars), ""]
    return "\n".join(linies)


def clau() -> str:
    """El que fa el segon i la q dels grups: les peces d'A xarxes i això."""
    h = hashlib.sha256((mp.CLAU + repr((SIS, t3e.GRUPS, model.PARAMS, t3i.PARAMS, model.RONDES, model.PAS))).encode())
    for funcio in (mostres_segon, mostres_q, peces_del_grup):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + vt.CLAU + mq.clau_dels_resultats()).encode())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


# Córrer-ho

def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_a_verificador as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        return list(feina.map(getattr(aquest, fes), tasques))


def entrena_les_peces(processos: int) -> None:
    from banc import model_a_verificador as aquest

    tasques = list(itertools.product(fonts.NOMS, range(t3e.GRUPS)))
    with ProcessPoolExecutor(max_workers=processos) as feina:
        for n, ((nom, g), _) in enumerate(zip(tasques, feina.map(aquest.peces_del_grup, tasques)), 1):
            print(f"· {n}/{len(tasques)}: el segon i la q del grup {g} de {nom}", flush=True)


def comprova_a_xarxes(banc: dict[tuple[str, str], dict]) -> None:
    """A xarxes, amb la memòria cau, dona a cada partit i escenari l'spellF1 del banc de la T3r."""
    an.comprova(pd.DataFrame([{"partit": nom, "escenari": e, "sostre": an.XARXES, "spell_f1": b["spell_f1"]}
                              for (nom, e), b in banc.items()]), (an.XARXES,))


def per_a(nom: str, banc: dict[tuple[str, str], dict]) -> dict[tuple[str, str], dict]:
    """El que fa servir la prova de `nom`: els seus escenaris, i els quatre ×¼ dels altres nou."""
    return {(j, e): b for (j, e), b in banc.items() if j == nom or e in QUARTS}


def les_proves(banc: dict[tuple[str, str], dict], processos: int) -> list[dict]:
    from banc import model_a_verificador as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        proves = []
        for r in feina.map(aquest.prova, [(nom, per_a(nom, banc)) for nom in fonts.NOMS]):
            print(f"· {r['partit']}: el llindar, {r['llindar']}", flush=True)
            proves.append(r)
    return proves


def escriu(contingut: dict, md: str) -> None:
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-a-verificador.json").write_text(
        json.dumps(contingut, indent=1, default=float, allow_nan=False))
    (DIR_RESULTATS / "model-a-verificador.md").write_text(md)
    print(md)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=10)
    ap.add_argument("--processos-models", type=int, default=4, help="models alhora")
    args = ap.parse_args()
    for nom in fonts.NOMS:
        mp.segon((nom, SIS), entrena=False)
        mp.q((nom, SIS), entrena=False)
        vt.veritat(nom)
    tasques = list(itertools.product(fonts.NOMS, ESCENARIS))
    banc = dict(zip(tasques, en_paral_lel("del_banc", tasques, args.processos)))
    comprova_a_xarxes(banc)
    print(f"· {XARXES_TOC} dona el del banc de la T3r", flush=True)
    entrena_les_peces(args.processos_models)
    proves = les_proves(banc, args.processos)
    metodes = pd.DataFrame([f for r in proves for f in r["files"]])
    c = mt.comparacio(metodes, A_VERIFICADOR, XARXES_TOC, TOC, amb_criteri=True)
    passa, millor = mt.compleix(c), mq.millor_fins_ara(c)
    per_font = {font: mt.comparacio(metodes[metodes["font"] == font], A_VERIFICADOR, XARXES_TOC, TOC,
                                    amb_criteri=False) for font in FONTS}
    verificador = taula_verificador(pd.concat([r["possessions"] for r in proves], ignore_index=True))
    canvis = taula_canvis(pd.DataFrame([f for r in proves for f in r["canvis"]]))
    llindars = {r["partit"]: r["llindar"] for r in proves}
    contingut = {"clau": clau_dels_resultats(), "passa": passa, "millor_fins_ara": millor,
                 "comparacio": t3.registres(c), "llindars": llindars, "files": t3.registres(metodes),
                 "per_font": {font: t3.registres(t) for font, t in per_font.items()},
                 "verificador": t3.registres(verificador.reset_index()), "canvis": t3.registres(canvis.reset_index())}
    escriu(contingut, markdown(c, passa, millor, per_font, metodes, verificador, canvis, llindars))


if __name__ == "__main__":
    main()
