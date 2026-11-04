"""Un detector de tocs après (T3u del pla per tocs, `docs/pla-tocs.md`, «T3u»; D-53).

    cd codi && uv run python -I -m banc.model_a_tocs_apresos [--processos 12] [--processos-models 4]

A sense pilota tal qual, amb una sola diferència: el segon també rep les probabilitats d'un detector de tocs après
(`cadena/tocs_apresos.py`). El primer i la q són els d'A xarxes, de la memòria cau de la T3p, i les cinc xarxes, les
d'A sense pilota, de la memòria cau de la T3t.

1. **En començar,** A xarxes i A sense pilota, amb la memòria cau, han de donar a cada punt de la graella i a les dues
   veritats l'spellF1 del banc de la T3t.
2. **El detector:** cinc xarxes com les d'A sense pilota, que aprenen a cada imatge si hi ha un toc de l'H a prop, un
   de l'A o cap (`banc/tocs_esdeveniments.py`): totes les imatges a prop d'un toc i una de cada 32 de la resta, als sis
   escenaris d'entrenament, i cadascuna també amb els equips girats. Les de cada grup (entrenades amb els altres sis
   partits, per entrenar el segon) i les del partit que es prova (amb els altres nou). 200 xarxes
   (`dades/banc/a-tocs-apresos/`).
3. **El segon,** entrenat com el d'A sense pilota, amb els senyals del detector a més.
4. **El decodificador,** amb la graella de la T3j, triat amb els altres nou als quatre ×¼ a la veritat de toc.
5. **El criteri** del pla: A tocs apresos contra A xarxes, a la veritat de toc. Si no passa, la regla del millor fins
   ara, contra A sense pilota. Només per saber-ho: per font; com encerta els tocs el detector; què troba als canvis
   d'equip on es veu la pilota i on la predicció hi arriba tard; i els errors d'equip on es veu la pilota.

Escriu `resultats/model-a-tocs-apresos.json` i `resultats/model-a-tocs-apresos.md`. Tot són dades obertes. Els mòduls
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
from banc import decodificador_tocs as t3
from banc import errors_amb_pilota as eap
from banc import model_a_canvis as t3i
from banc import model_a_canvis2 as t3j
from banc import model_a_context as t3e
from banc import model_a_partit as mp
from banc import model_a_possessio as t3f
from banc import model_a_q as mq
from banc import model_a_quart as t3b
from banc import model_a_sense_pilota as msp
from banc import model_a_toc as mt
from banc import model_a_xarxa as t3m
from banc import sostre_curtes as sc
from banc import sostre_sense_pilota as ssp
from banc import tocs_als_canvis as tac
from banc import tocs_esdeveniments as te
from banc import veritat_toc as vt
from banc.partit import PartitBanc
from cadena import model, tocs, xarxes
from cadena import tocs_apresos as ta
from cadena import xarxa_sense_pilota as xsp
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ESCENARIS = mp.ESCENARIS                            # els deu de la T3 i «partit ×¼»
SIS = mp.SIS
XARXES, XARXES_TOC = mt.XARXES, mt.XARXES_TOC       # A xarxes, amb el decodificador de la cadena i triat a la de toc
A_SENSE = msp.A_SENSE
A_TOCS = "A tocs apresos"
SEMPRE, TOC = mt.SEMPRE, mt.TOC
FONTS = msp.FONTS
FINESTRA = tac.FINESTRA                             # 0,5 s
LLINDAR = 0.5                                       # la probabilitat de toc de l'equip nou, per dir que el troba
APRES, FET_A_MA = "el detector après", "el fet a mà"
DIR_CAU = fonts.DIR_CAU / "a-tocs-apresos"
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


def mostres_detector(p: PartitBanc, tocs_: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Les mostres del detector d'un partit a un escenari: les imatges de `te.files`, també amb els equips girats."""
    if len(p.tracking.fotograma) != len(p.veritat):
        raise ValueError(f"{p.nom}: el tracking no té una fila per imatge")
    y = te.etiquetes_de_toc(tocs_, len(p.veritat), p.trams)
    f = te.files(y, avalua.trams_valids(p))
    return xsp.mostres(p.tracking, p.trams, f, y[f])


def entrena_detector(noms: list[str]) -> tuple[tuple, list[list[float]]]:
    """Les cinc xarxes del detector, amb els tocs dels partits `noms` als sis escenaris d'entrenament."""
    xs, ys = [], []
    for nom in noms:
        tocs_ = te.tocs(nom)
        for e in SIS:
            x, y = mostres_detector(mp.degradat(nom, e), tocs_)
            xs.append(x)
            ys.append(y)
    x = np.concatenate(xs)
    del xs
    return xarxes.entrena(x, np.concatenate(ys))


def detector_del_grup(tasca: tuple[str, int], entrena: bool = True) -> dict[tuple[str, str], np.ndarray]:
    """Les probabilitats del detector als partits del grup `i` de `prova`, als sis escenaris d'entrenament,
    entrenat amb els altres sis partits."""
    prova, i = tasca
    claus = mp.claus_del_grup(prova, i, SIS)
    cami = cau("detector-grup", prova, i)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falta el detector del grup {i} de {prova}, o és d'un altre codi")
        entrenades, perdues = entrena_detector(t3m.per_entrenar_el_grup(prova, i))
        desat = {}
        for (nom, e), clau_ in claus.items():
            p = mp.degradat(nom, e)
            desat[clau_] = xsp.probabilitats(entrenades, p.tracking, p.trams).astype(np.float32)
        desa(cami, perdues=np.array(perdues), **desat)
    return {qui: desat[nom] for qui, nom in claus.items()}


def detector_de_la_prova(prova: str, entrena: bool = True) -> dict[str, np.ndarray]:
    """Les probabilitats del detector al partit `prova`, a tots els escenaris, entrenat amb els altres nou."""
    cami = cau("detector", prova)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falta el detector de {prova}, o és d'un altre codi")
        entrenades, perdues = entrena_detector([nom for nom in fonts.NOMS if nom != prova])
        desat = {}
        for i, e in enumerate(ESCENARIS):
            p = mp.degradat(prova, e)
            desat[f"e{i}"] = xsp.probabilitats(entrenades, p.tracking, p.trams).astype(np.float32)
        desa(cami, perdues=np.array(perdues), **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(ESCENARIS)}


def taula_segon(p: PartitBanc, primer: np.ndarray, de_les_xarxes: np.ndarray, del_detector: np.ndarray) -> pd.DataFrame:
    """La del segon d'A sense pilota i els senyals del detector."""
    return pd.concat([t3m.taula_segon(p, primer, de_les_xarxes), ta.senyals_segon(del_detector, p.trams)], axis=1)


def mostres_segon(prova: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Com `msp.mostres_segon`, amb el detector de cada grup a més."""
    primers, de_les_xarxes, dels_detectors = {}, {}, {}
    for i in range(t3e.GRUPS):
        primers |= mp.primer_del_grup((prova, i, SIS))
        de_les_xarxes |= msp.xarxes_del_grup((prova, i), entrena=False)
        dels_detectors |= detector_del_grup((prova, i), entrena=False)
    xs, ys = [], []
    for (nom, e), primer in primers.items():
        p = mp.degradat(nom, e)
        x, y = t3f.mostres(p, taula_segon(p, primer.astype(float), de_les_xarxes[(nom, e)].astype(float),
                                          dels_detectors[(nom, e)].astype(float)))
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def segon(prova: str, entrena: bool = True) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Les probabilitats d'A tocs apresos al partit `prova`, a tots els escenaris, i el prior: com el segon d'A sense
    pilota (`msp.segon`), amb el detector a més. Amb `entrena=False`, només les llegeix de la memòria cau."""
    cami = cau("segon", prova)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les probabilitats del segon d'{A_TOCS} de {prova}, o són d'un altre codi")
        x, y = mostres_segon(prova)
        entrenat, prior = model.entrena(x, y), model.prior(y)
        del x
        primers = mp.primer_de_la_prova((prova, SIS))
        de_les_xarxes = msp.xarxes_de_la_prova(prova, entrena=False)
        del_detector = detector_de_la_prova(prova, entrena=False)
        desat = {"prior": prior}
        for i, e in enumerate(ESCENARIS):
            p = mp.degradat(prova, e)
            taula = taula_segon(p, primers[e].astype(float), de_les_xarxes[e].astype(float),
                                del_detector[e].astype(float))
            desat[f"e{i}"] = model.probabilitats(entrenat, taula).astype(np.float32)
        desa(cami, **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(ESCENARIS)}, desat["prior"]


def de_qui(metode: str, nom: str) -> tuple[dict[str, np.ndarray], np.ndarray, dict[str, np.ndarray]]:
    """Les probabilitats i el prior d'A xarxes (de la memòria cau de la T3p), d'A sense pilota (de la de la T3t) o
    d'A tocs apresos, amb la q d'A xarxes."""
    if metode == XARXES:
        probes, prior = mp.segon((nom, SIS), entrena=False)
    elif metode == A_SENSE:
        probes, prior = msp.segon(nom, entrena=False)
    else:
        probes, prior = segon(nom, entrena=False)
    return probes, prior, mp.q((nom, SIS), entrena=False)


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


def comprova_les_d_abans(files: pd.DataFrame) -> None:
    """A xarxes i A sense pilota, amb la memòria cau, donen a cada punt de la graella i a les dues veritats l'spellF1
    del banc de la T3t."""
    claus = ["partit", "escenari", "metode", "veritat", "w", "lam", "d_min"]
    aqui = files[files["metode"].isin((XARXES, A_SENSE))][[*claus, "spell_f1"]]
    banc = pd.DataFrame(json.loads((DIR_RESULTATS / "model-a-sense-pilota.json").read_text())["files"])
    junts = aqui.merge(banc[[*claus, "spell_f1"]], on=claus, suffixes=("", " del banc"), how="outer")
    if (len(junts) != len(aqui) or junts.isna().any().any()
            or not np.allclose(junts["spell_f1"], junts["spell_f1 del banc"], rtol=0, atol=1e-12)):
        raise RuntimeError(f"{XARXES} o {A_SENSE} no donen el del banc de la T3t")


def del_detector(det: np.ndarray, tocs_: np.ndarray, etiqueta: np.ndarray, on: np.ndarray) -> dict[str, float]:
    """Com encerta els tocs el detector a les imatges d'`on`: als tocs dels esdeveniments, la part on l'equip del toc
    és el més probable; i si hi ha un toc a prop o no (l'AUC de P(toc) = 1 − P(cap))."""
    from sklearn.metrics import roc_auc_score

    on = on & np.isfinite(det).all(axis=1)
    seus = tocs_[on[tocs_[:, 0]]]
    altre = np.where(seus[:, 1] == pm.H, pm.A, pm.H)
    encert = det[seus[:, 0], seus[:, 1]] > det[seus[:, 0], altre]
    return {"n tocs": len(seus), "l'equip del toc": float(encert.mean()),
            "AUC": float(roc_auc_score(etiqueta[on] != pm.D, 1 - det[on, pm.D]))}


def troba(det: np.ndarray, a: int, k: int, finestra: int = FINESTRA, llindar: float = LLINDAR) -> bool:
    """Si el detector après troba el toc de l'equip `k` al canvi de la imatge `a`: la seva probabilitat hi arriba a
    `llindar` a ±`finestra` imatges."""
    return bool((det[max(a - finestra, 0):a + finestra + 1, k] >= llindar).any())


def analisi(tasca: tuple[str, str, dict[str, tuple]]) -> dict[str, list[dict]]:
    """Un partit i un escenari, amb els decodificadors triats d'A sense pilota i d'A tocs apresos: com encerta els
    tocs el detector, què troben els detectors als canvis d'equip on es veu la pilota i si la predicció hi arriba
    tard, i els errors d'equip on es veu la pilota."""
    nom, escenari, triats = tasca
    p = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    trams = avalua.trams_valids(replace(p, veritat=toc))
    forat = sc.forats(~np.isnan(p.tracking.pilota[:, 0]))
    pilota = ssp.dins(len(toc), trams) & ~forat
    det = detector_de_la_prova(nom, entrena=False)[escenari].astype(float)
    tocs_ = te.tocs(nom)
    comu = {"partit": nom, "font": p.font, "escenari": escenari}
    detector = {**comu, **del_detector(det, tocs_, te.etiquetes_de_toc(tocs_, len(toc), p.trams),
                                       ssp.dins(len(toc), trams))}
    relatives, preds = {}, {}
    for metode in (A_SENSE, A_TOCS):
        probes, prior, q_ = de_qui(metode, nom)
        relatives[metode] = log_relativa(probes[escenari].astype(float), prior)
        w, lam, d_min = triats[metode]
        preds[metode] = t3i.per_trams(relatives[metode], q_[escenari].astype(float), p.trams, w, lam, int(d_min))
    fet_a_ma = tocs.detecta(p.tracking, p.trams, tac.PAR)
    canvis = []
    for a, b, k in tac.canvis(toc, trams, forat):
        primera = slice(a, a + min(FINESTRA, b - a))
        canvis.append({**comu, APRES: troba(det, a, k),
                       FET_A_MA: tac.trobat(fet_a_ma.imatge, fet_a_ma.equip, a, k) == tac.BO,
                       **{metode: bool(np.mean(pred[primera] == k) < 0.5) for metode, pred in preds.items()}})
    inici, _, _ = eap.possessions(toc, trams)
    errors = []
    for metode, pred in preds.items():
        e = eap.errors(pred, toc, relatives[metode], pilota, trams)
        a_l_altre = e["dona"] == eap.L_ALTRE
        errors.append({**comu, "metode": metode, "n imatges": int((pilota & (inici >= 0)).sum()), "errors": len(e),
                       "a l'altre equip": int(a_l_altre.sum()),
                       "on el segon dubta": int((a_l_altre & (e["segon"] == eap.DUBTA)).sum())})
    return {"detector": [detector], "canvis": canvis, "errors": errors}


def ordena(t: pd.DataFrame) -> pd.DataFrame:
    return t.reindex([e for e in ESCENARIS if e in t.index])


def taula_detector(t: pd.DataFrame) -> pd.DataFrame:
    """Per escenari: els tocs dels esdeveniments, la part on l'equip del toc és el més probable i l'AUC (mitjana dels
    partits)."""
    g = t.groupby("escenari")
    return ordena(pd.DataFrame({"n tocs": g["n tocs"].sum(), "l'equip del toc": g["l'equip del toc"].mean(),
                                "AUC": g["AUC"].mean()}))


def taula_canvis(t: pd.DataFrame) -> pd.DataFrame:
    """Per escenari: els canvis d'equip on es veu la pilota, on hi troba el toc de l'equip nou cada detector, i on la
    predicció hi arriba tard amb cada mètode (a tots i segons si el detector après el troba)."""
    g = t.groupby("escenari")
    taula = pd.DataFrame({"n canvis": g.size(), f"troba el toc: {APRES}": g[APRES].mean(),
                          f"troba el toc: {FET_A_MA}": g[FET_A_MA].mean()})
    for metode in (A_SENSE, A_TOCS):
        taula[f"tard: {metode}"] = g[metode].mean()
    for troba_, nom in ((True, "si el troba"), (False, "si no el troba")):
        seus = t[t[APRES] == troba_].groupby("escenari")
        for metode in (A_SENSE, A_TOCS):
            taula[f"tard {nom}: {metode}"] = seus[metode].mean()
    return ordena(taula)


def taula_errors(t: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i mètode: la part de les imatges d'un equip on es veu la pilota on la predicció no hi dona aquest
    equip, on hi dona l'altre, i on hi dona l'altre i el segon dubta."""
    parts = ("errors", "a l'altre equip", "on el segon dubta")
    g = t.groupby(["escenari", "metode"])[["n imatges", *parts]].sum()
    taula = pd.DataFrame({c: g[c] / g["n imatges"] for c in parts}).unstack("metode")
    taula = taula[[(c, m) for c in parts for m in (A_SENSE, A_TOCS)]]
    return ordena(pd.concat([g["n imatges"].xs(A_SENSE, level="metode"), taula], axis=1))


def _regla(millor: dict[str, bool]) -> list[str]:
    es = all(millor.values())
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | "
            f"{mq._marca(millor['quarts'])} |",
            f"| «{mp.PARTIT}» | la diferència no és negativa | {mq._marca(millor['partit'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {mq._marca(millor['altres'])} |",
            "", f"**{A_TOCS} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_TOCS if es else A_SENSE}.", ""]


def markdown(metodes: pd.DataFrame, triades: dict, c: pd.DataFrame, passa: dict[str, bool], c_sense: pd.DataFrame,
             millor: dict[str, bool], per_font: dict[tuple[str, str], pd.DataFrame], detector: pd.DataFrame,
             canvis: pd.DataFrame, errors: pd.DataFrame) -> str:
    linies = ["# Banc obert · Un detector de tocs après (T3u)", "",
              "Generat amb `uv run python -I -m banc.model_a_tocs_apresos`. Dades obertes: 7 partits de DFL (IDSSE,",
              "CC BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3u», i la capçalera de `banc/model_a_tocs_apresos.py`. Es puntua a la",
              "veritat de toc.", "",
              f"**{XARXES}** i **{A_SENSE}** són els de la T3t, amb les peces de la memòria cau (✓ comprovat: a cada",
              f"punt de la graella donen l'spellF1 del banc de la T3t). **{A_TOCS}** és {A_SENSE}, amb el segon que",
              "també rep les probabilitats d'un detector de tocs après.", "",
              f"## {A_TOCS} contra {XARXES_TOC} (spellF1): el criteri", "",
              *t3b._taula(c, A_TOCS, XARXES_TOC), "", *mt._criteris(passa),
              f"## {A_TOCS} contra {A_SENSE} (spellF1)", "", *t3i._comparacio(c_sense, A_TOCS, A_SENSE), ""]
    if not all(passa.values()):
        linies += ["## No passa: és el millor fins ara?", "", *_regla(millor)]
    for (font, contra), taula in per_font.items():
        linies += [f"## {A_TOCS} contra {contra}, només els partits de {font}", "",
                   *t3i._comparacio(taula, A_TOCS, contra), ""]
    linies += ["## Com encerta els tocs el detector", "",
               "El detector entrenat amb els altres nou partits, a les parts puntuades. Als tocs dels esdeveniments,",
               "la part on l'equip del toc és més probable que l'altre; i l'AUC de la probabilitat de toc (1 − P(cap))",
               f"per distingir les imatges a {te.A_PROP} o menys d'un toc de les altres (mitjana dels deu partits).", "",
               t3p.md(taula_detector(detector)), "",
               "## Als canvis d'equip on es veu la pilota", "",
               "Un canvi: el començament d'una possessió de la veritat de toc que ve de l'altre equip, amb la pilota a",
               f"la vista (com a `tocs_als_canvis.py`). *Troba el toc:* {APRES}, si la probabilitat de toc de l'equip",
               f"nou hi arriba a {LLINDAR} a ±0,5 s; {FET_A_MA} (`cadena/tocs.py`), si hi té un toc de l'equip nou a",
               "±0,5 s. *Tard:* a la primera mitja segona de la possessió, la predicció hi dona l'equip nou a menys de",
               "la meitat de les imatges; a tots els canvis, i segons si el detector après hi troba el toc.", "",
               t3p.md(taula_canvis(canvis)), "",
               "## Els errors d'equip on es veu la pilota", "",
               "On es veu la pilota i la veritat de toc és d'un equip: la part de les imatges on la predicció no hi",
               "dona aquest equip, on hi dona l'altre, i on hi dona l'altre i el segon dubta (com a",
               f"`errors_amb_pilota.py`: la probabilitat de l'equip bo davant de l'altre, {eap.DUBTE} o més).", "",
               t3p.md(taula_errors(errors)), "",
               "## L'spellF1 de cada mètode (mitjana dels deu partits)", "",
               *mt._mitjanes(metodes, [XARXES, XARXES_TOC, A_SENSE, A_TOCS]), "## Els decodificadors triats", "",
               *mq._triades(triades), ""]
    return "\n".join(linies)


def clau() -> str:
    """El que fa les probabilitats d'aquí: les peces d'A sense pilota, els tocs, el detector, el segon i això."""
    h = hashlib.sha256((msp.CLAU + te.CLAU + repr((SIS, ESCENARIS, xarxes.LLAVORS, model.RONDES, model.PAS))).encode())
    h.update(Path(ta.__file__).read_bytes())
    for funcio in (mostres_detector, entrena_detector, detector_del_grup, detector_de_la_prova, taula_segon,
                   mostres_segon, segon):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + vt.CLAU + msp.clau_dels_resultats()).encode())
    for modul in (tac, eap, tocs):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_a_tocs_apresos as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        return list(feina.map(getattr(aquest, fes), tasques))


def entrena_les_peces(processos: int) -> None:
    """Els detectors dels grups i dels partits, i després el segon de cada partit."""
    from banc import model_a_tocs_apresos as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        grups = [(nom, i) for nom in fonts.NOMS for i in range(t3e.GRUPS)]
        for k, ((nom, i), _) in enumerate(zip(grups, feina.map(aquest.detector_del_grup, grups)), start=1):
            print(f"· {k}/{len(grups)}: el detector del grup {i} de {nom}", flush=True)
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.detector_de_la_prova, fonts.NOMS)):
            print(f"· el detector de {nom}", flush=True)
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.segon, fonts.NOMS)):
            print(f"· el segon d'{A_TOCS} de {nom}", flush=True)


def files_de(metodes: tuple[str, ...], processos: int) -> pd.DataFrame:
    tasques = [(nom, e, metodes) for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    return pd.DataFrame([f for tros in en_paral_lel("graella", tasques, processos) for f in tros])


def escriu(contingut: dict, md: str) -> None:
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-a-tocs-apresos.json").write_text(json.dumps(contingut, indent=1, default=float,
                                                                         allow_nan=False))
    (DIR_RESULTATS / "model-a-tocs-apresos.md").write_text(md)
    print(md)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=4, help="models alhora")
    args = ap.parse_args()
    for nom in fonts.NOMS:
        de_qui(XARXES, nom)
        de_qui(A_SENSE, nom)
        vt.veritat(nom)
        te.tocs(nom)
    files = files_de((XARXES, A_SENSE), args.processos)
    comprova_les_d_abans(files)
    print(f"· {XARXES} i {A_SENSE} donen el del banc de la T3t", flush=True)
    entrena_les_peces(args.processos_models)
    files = pd.concat([files, files_de((A_TOCS,), args.processos)], ignore_index=True)
    de_xarxes, triades_xarxes = mt.tria_sense_mirar(files, XARXES, SEMPRE, XARXES)
    mt.comprova_el_decodificador(triades_xarxes)
    xarxes_toc, triades_xarxes_toc = mt.tria_sense_mirar(files, XARXES, TOC, XARXES_TOC)
    de_sense, triades_sense = mt.tria_sense_mirar(files, A_SENSE, TOC, A_SENSE)
    de_tocs, triades_tocs = mt.tria_sense_mirar(files, A_TOCS, TOC, A_TOCS)
    metodes = pd.concat([de_xarxes, xarxes_toc, de_sense, de_tocs], ignore_index=True)
    c = mt.comparacio(metodes, A_TOCS, XARXES_TOC, TOC, amb_criteri=True)
    c_sense = mt.comparacio(metodes, A_TOCS, A_SENSE, TOC, amb_criteri=False)
    passa, millor = mt.compleix(c), mq.millor_fins_ara(c_sense)
    per_font = {(font, contra): mt.comparacio(metodes[metodes["font"] == font], A_TOCS, contra, TOC, amb_criteri=False)
                for font in FONTS for contra in (XARXES_TOC, A_SENSE)}
    tasques = [(nom, e, {A_SENSE: triades_sense[nom], A_TOCS: triades_tocs[nom]})
               for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    trossos = en_paral_lel("analisi", tasques, args.processos)
    detector, canvis, errors = (pd.DataFrame([f for t in trossos for f in t[k]])
                                for k in ("detector", "canvis", "errors"))
    triades = {XARXES: triades_xarxes, XARXES_TOC: triades_xarxes_toc, A_SENSE: triades_sense, A_TOCS: triades_tocs}
    contingut = {"clau": clau_dels_resultats(), "passa": passa, "millor_fins_ara": millor,
                 "comparacio": t3.registres(c), "contra_a_sense_pilota": t3.registres(c_sense), "triades": triades,
                 "files": t3.registres(files),
                 "per_font": {f"{font} · {contra}": t3.registres(t) for (font, contra), t in per_font.items()},
                 "detector": t3.registres(detector), "canvis": t3.registres(canvis), "errors": t3.registres(errors)}
    escriu(contingut, markdown(metodes, triades, c, passa, c_sense, millor, per_font, detector, canvis, errors))


if __name__ == "__main__":
    main()
