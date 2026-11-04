"""Un detector de les possessions engolides, a sobre d'A pilota morta (T3aj del pla per tocs, `docs/pla-tocs.md`,
«T3aj»; D-72).

    cd codi && uv run python -I -m banc.model_engolides [--processos 12] [--processos-models 3]

A pilota morta (T3ah) tal qual, amb els paràmetres i el decodificador que hi va triar cada partit. A sobre, **el
detector**: un LightGBM binari com el segon (els mateixos paràmetres i rondes), que només mira les imatges de dins de
les possessions predites d'A pilota morta i en dona la probabilitat que la veritat hi sigui l'altre equip. Les seves
columnes es diuen respecte de l'equip predit (`cadena/engolides.py`). Dins de les possessions predites, a la
probabilitat relativa de l'altre equip s'hi suma `beta` vegades el logit de la del detector, i es torna a decodificar
amb el mateix decodificador. La D no es toca: on la neteja ha tret la pilota, continua impossible.

1. **En començar:** A xarxes i A equips sencers, amb la memòria cau, han de donar el banc de la T3v, A pilota creïble,
   el de la T3w, i A neteja d'aire, el de la T3ac; i el banc de la T3ah ha de ser d'aquest codi. Si no, s'atura.
2. **Les mostres** de cada partit i escenari d'entrenament (`SIS`): la predicció d'A pilota morta amb els models que
   deixen fora aquest partit, les etiquetes al nivell de cada partit i escenari amb les llavors d'aprendre, i una de
   cada `PAS` imatges de dins de les possessions predites amb veritat de toc (`mostres_del_partit`). Es desen.
3. **El detector de cada partit** (`detector`), après amb les mostres dels altres nou (`altres`). Es desa.
4. **La graella** (`BETES`) als quatre ×¼ de cada partit, amb els nivells bo, mitjà i dolent, les llavors d'aprendre i
   el detector del mateix partit. Cap punt no hi ha de donar la D a una imatge netejada.
5. **La tria** de cada partit, amb els altres nou: la `beta` amb més spellF1 de mitjana als quatre ×¼ i als tres
   nivells, a la veritat de toc (`tria`).
6. **Es prova** als onze escenaris amb els quatre nivells i les llavors de provar. Amb `beta` = 0 ha de donar l'spellF1
   d'A pilota morta del banc de la T3ah, i sense etiquetes i amb `beta` = 0, exactament A neteja d'aire. Si no,
   s'atura.
7. **El criteri** del pla, el de la T3ai; el millor fins ara, contra A pilota morta. Només per saber-ho: per font; amb
   el nivell bo; contra A pilota morta a cada nivell; les causes de `banc/on_falla.py` per a tots dos; la `beta` de
   cada partit; l'AUC del detector, i les columnes que més fa servir.

Escriu `resultats/model-engolides.json` i `.md`. Tot són dades obertes. Els mòduls d'abans no es toquen.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import inspect
import itertools
import json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from banc import analisi_t3p as t3p
from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_partit as mp
from banc import model_a_q as mq
from banc import model_a_quart as t3b
from banc import model_a_toc as mt
from banc import model_camp_girat as mcg
from banc import model_etiquetes_decodificador as med
from banc import model_neteja_aire as mna
from banc import model_pilota_creible as mpc
from banc import model_pilota_morta as mpm
from banc import model_pilotes_aturades as mpa
from banc import model_represes as mre
from banc import model_vores as mv
from banc import on_falla as of
from banc import smart_tagging_simulat as sts
from banc import sostre_sense_pilota as ssp
from banc import veritat_toc as vt
from cadena import engolides as eg
from cadena import model
from cadena import pilota_creible as pc
from cadena import pilota_morta as pmo
from possessio.oficial import possession_metrics as pm

ESCENARIS, QUARTS_T3, PARTIT, SIS = med.ESCENARIS, med.QUARTS_T3, med.PARTIT, mpa.SIS
XARXES, XARXES_TOC, A_EQUIPS, A_CREIBLE, A_NETEJA = med.XARXES, med.XARXES_TOC, med.A_EQUIPS, med.A_CREIBLE, med.A_NETEJA
A_PM = mpm.A_PM
A_EG = "A engolides"
SEMPRE, TOC = med.SEMPRE, med.TOC
NIVELLS, NIVELLS_TRIA, MITJA = med.NIVELLS, med.NIVELLS_TRIA, med.MITJA
TRIA, PROVA = med.TRIA, med.PROVA                   # les etiquetes de la T3ag
BETES = (0.0, 0.25, 0.5, 1.0, 2.0)
PAS = 4                                             # una de cada quatre imatges de dins de les possessions predites
PARAMS = {**{k: v for k, v in model.PARAMS.items() if k not in ("objective", "num_class")}, "objective": "binary"}
RONDES = model.RONDES
CURTS = "curts ×¼"
DIR_CAU = mpa.DIR_CAU
DIR_RESULTATS = t3.DIR_RESULTATS


def altres(prova: str) -> list[str]:
    """Els partits d'on aprèn el detector de `prova`."""
    return [nom for nom in fonts.NOMS if nom != prova]


def parts(trams: tuple[tuple[int, int, int], ...]) -> list[tuple[int, int]]:
    """Les parts del partit com a trams [inici, final)."""
    return [(a, b + 1) for _, a, b in trams]


def relativa_pm(nom: str, escenari: str, nivell: str, per: str, a_pm: pmo.Abans, de_sempre, r: np.ndarray,
                netejades: np.ndarray) -> np.ndarray:
    """La probabilitat relativa d'A pilota morta, com al banc de la T3ah: amb les etiquetes i la D impossible."""
    etiquetes = mpa.etiquetes_de(nom, escenari, nivell, per)
    return mna.amb_la_d_impossible(pmo.amb_les_etiquetes(r, etiquetes, de_sempre.trams, a_pm, mpm.medianes_sense(nom)),
                                   netejades)


def columnes_de(de_sempre, relativa: np.ndarray, q_: np.ndarray, pred: np.ndarray) -> tuple[pd.DataFrame, np.ndarray]:
    """Les columnes del detector, amb el tracking netejat (el que veu A pilota morta), i l'equip predit a cada imatge."""
    trams = parts(de_sempre.trams)
    return (eg.columnes(pc.neteja(de_sempre.tracking), relativa, q_, pred, trams),
            eg.possessions(pred, trams)[0])


def mostres_del_partit(toc: np.ndarray, trams_valids: list[tuple[int, int]], x: pd.DataFrame,
                       equip: np.ndarray) -> tuple[pd.DataFrame, np.ndarray]:
    """Una de cada `PAS` imatges de dins de les possessions predites amb veritat de toc, i si la veritat hi és l'altre
    equip (H = 0, A = 1)."""
    i = np.flatnonzero((equip >= 0) & ssp.dins(len(toc), trams_valids))[::PAS]
    return x.iloc[i].reset_index(drop=True), (toc[i] == 1 - equip[i]).astype(np.int8)


def _cami_mostres(nom: str, escenari: str) -> Path:
    return DIR_CAU / f"engolides-mostres-{nom}-{SIS.index(escenari)}.npz"


def mostres(tasca: tuple[str, str, pmo.Abans, tuple]) -> int:
    """Les mostres d'un partit i un escenari d'entrenament, amb A pilota morta (`a_pm`) i el decodificador d'A equips
    sencers (`triat`) d'aquest partit, i les etiquetes al seu nivell amb la llavor d'aprendre. Les desa i en torna
    quantes."""
    nom, escenari, a_pm, triat = tasca
    cami = _cami_mostres(nom, escenari)
    desat = llegeix(cami)
    if desat is None:
        de_sempre, r, q_, netejades = med.base(nom, escenari)
        relativa = relativa_pm(nom, escenari, sts.nivell_per_aprendre(nom, escenari), TRIA, a_pm, de_sempre, r,
                               netejades)
        pred = mna.prediccio(relativa, q_, de_sempre.trams, triat)
        x, equip = columnes_de(de_sempre, relativa, q_.astype(float), pred)
        toc = replace(de_sempre, veritat=vt.veritat(nom))
        x, y = mostres_del_partit(toc.veritat, avalua.trams_valids(toc), x, equip)
        desat = {"x": x.to_numpy(float), "y": y}
        desa(cami, **desat)
    return len(desat["y"])


def mostres_desades(nom: str, escenari: str) -> dict[str, np.ndarray]:
    desat = llegeix(_cami_mostres(nom, escenari))
    if desat is None:
        raise RuntimeError(f"Falten les mostres del detector de {nom}, {escenari}, o són d'un altre codi")
    return desat


def entrena_detector(x: pd.DataFrame, y: np.ndarray, rondes: int = RONDES) -> lgb.Booster:
    return lgb.train(PARAMS, lgb.Dataset(x, label=y, free_raw_data=True), num_boost_round=rondes)


def prediu(detector_: lgb.Booster, x: pd.DataFrame) -> np.ndarray:
    """La probabilitat que la veritat sigui l'altre equip, amb un sol fil (els processos ja van en paral·lel)."""
    return detector_.predict(x, num_threads=1)


def detector(prova: str, entrena: bool = True) -> dict[str, np.ndarray]:
    """El detector de `prova`, après amb les mostres dels altres nou als sis escenaris d'entrenament: el model, el
    guany de cada columna, quantes mostres i la part de positives."""
    cami = DIR_CAU / f"engolides-detector-{prova}.npz"
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falta el detector d'engolides de {prova}, o és d'un altre codi")
        de_qui = altres(prova)
        if prova in de_qui:
            raise RuntimeError(f"{prova}: el detector aprendria del partit que es prova")
        trossos = [mostres_desades(nom, e) for nom in de_qui for e in SIS]
        x = pd.DataFrame(np.concatenate([t["x"] for t in trossos]), columns=list(eg.COLUMNES))
        y = np.concatenate([t["y"] for t in trossos])
        del trossos
        entrenat = entrena_detector(x, y)
        desat = {"model": np.array(entrenat.model_to_string()), "importancia": entrenat.feature_importance("gain"),
                 "mostres": np.array(len(y)), "positives": np.array(float(y.mean()))}
        desa(cami, **desat)
    return desat


@functools.lru_cache(maxsize=None)
def _detector(nom: str) -> lgb.Booster:
    return lgb.Booster(model_str=str(detector(nom, entrena=False)["model"]))


def p_altre(nom: str, x: pd.DataFrame, equip: np.ndarray) -> np.ndarray:
    """La del detector de `nom` a les imatges de dins de les possessions predites; fora, NaN."""
    p = np.full(len(x), np.nan)
    i = np.flatnonzero(equip >= 0)
    if len(i):
        p[i] = prediu(_detector(nom), x.iloc[i])
    return p


def relativa_amb(relativa: np.ndarray, p: np.ndarray, equip: np.ndarray, beta: float,
                 netejades: np.ndarray) -> np.ndarray:
    """La relativa d'A pilota morta amb la del detector sumada a l'altre equip (`eg.suma`), i la D impossible a
    `netejades` (que ja hi era)."""
    return mna.amb_la_d_impossible(eg.suma(relativa, p, equip, beta), netejades)


def clau() -> str:
    """El que fa les mostres i els detectors d'aquí: A pilota morta de la T3ah, les columnes i això."""
    h = hashlib.sha256((mpm.clau_dels_resultats() + repr((SIS, PAS, PARAMS, RONDES))).encode())
    h.update(Path(eg.__file__).read_bytes())
    for funcio in (parts, relativa_pm, columnes_de, mostres_del_partit, mostres, entrena_detector, detector):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


def desa(cami: Path, **arrays: np.ndarray) -> None:
    cami.parent.mkdir(parents=True, exist_ok=True)
    temporal = cami.with_name(f"{cami.name}.part.npz")
    np.savez(temporal, clau=CLAU, **arrays)
    temporal.replace(cami)


def llegeix(cami: Path) -> dict[str, np.ndarray] | None:
    if cami.exists():
        with np.load(cami, allow_pickle=False) as desat:
            if str(desat["clau"]) == CLAU:
                return {k: desat[k] for k in desat.files if k != "clau"}
    return None


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def _amb_el_detector(nom: str, escenari: str, nivell: str, per: str, a_pm: pmo.Abans, triat: tuple, base: tuple
                     ) -> tuple:
    """A pilota morta a un nivell: la relativa, la predicció, l'equip predit i la del detector."""
    de_sempre, r, q_, netejades = base
    relativa = relativa_pm(nom, escenari, nivell, per, a_pm, de_sempre, r, netejades)
    pred = mna.prediccio(relativa, q_, de_sempre.trams, triat)
    x, equip = columnes_de(de_sempre, relativa, q_.astype(float), pred)
    return relativa, pred, equip, p_altre(nom, x, equip)


def _decodifica(nom: str, escenari: str, nivell: str, metode: str, relativa: np.ndarray, p: np.ndarray,
                equip: np.ndarray, beta: float, base: tuple, triat: tuple) -> np.ndarray:
    de_sempre, _, q_, netejades = base
    pred = mna.prediccio(relativa_amb(relativa, p, equip, beta, netejades), q_, de_sempre.trams, triat)
    if (pred[netejades] == pm.D).any():
        raise RuntimeError(f"{nom}, {escenari}, {nivell}, beta {beta}: {metode} dona la D a una imatge netejada")
    return pred


def graella(tasca: tuple[str, str, pmo.Abans, tuple]) -> list[dict]:
    """Un partit i un ×¼, amb A pilota morta (`a_pm`), el decodificador d'A equips sencers (`triat`) i el detector del
    mateix partit: cada `beta` amb els nivells de `NIVELLS_TRIA` i les llavors d'aprendre, a la veritat de toc."""
    nom, escenari, a_pm, triat = tasca
    base = med.base(nom, escenari)
    p = replace(base[0], veritat=vt.veritat(nom))
    files = []
    for nivell in NIVELLS_TRIA:
        relativa, _, equip, pa = _amb_el_detector(nom, escenari, nivell, TRIA, a_pm, triat, base)
        for beta in BETES:
            pred = _decodifica(nom, escenari, nivell, A_EG, relativa, pa, equip, beta, base, triat)
            files.append({"partit": nom, "font": base[0].font, "escenari": escenari, "nivell": nivell, "beta": beta,
                          **{k: v for k, v in avalua.puntua(p, pred).items() if k in ("spell_f1", "macro_f1")}})
    return files


def tria(files: pd.DataFrame, prova: str) -> float:
    """La `beta` per a `prova`, amb els altres nou: la de més spellF1 de mitjana als quatre ×¼ i als nivells de les
    files (desempata el macroF1)."""
    millor = mp.millor(files[files["partit"] != prova], ["beta"], QUARTS_T3)
    return float(millor[0] if isinstance(millor, tuple) else millor)


def auc(toc: np.ndarray, trams_valids: list[tuple[int, int]], equip: np.ndarray, p: np.ndarray) -> dict:
    """L'AUC del detector a les imatges de dins de les possessions predites amb veritat de toc."""
    i = np.flatnonzero((equip >= 0) & ssp.dins(len(toc), trams_valids))
    y = toc[i] == 1 - equip[i]
    n = {"n": len(i), "positives": int(y.sum())}
    return {**n, "auc": float(roc_auc_score(y, p[i])) if 0 < y.sum() < len(y) else None}


def causes_de(toc: np.ndarray, pred: np.ndarray, trams: list[tuple[int, int]], vista: np.ndarray) -> tuple:
    """Quantes possessions de la veritat hi ha de cada causa de `on_falla` i quantes predites sobren on."""
    omplerta = pm.fill_abstentions(pred.astype(np.int8), trams)
    return (Counter(f["causa"] for f in of.causes(toc, omplerta, trams, vista)),
            Counter(f["on"] for f in of.sobrants(toc, omplerta, trams)))


def informe(tasca: tuple[str, str, pmo.Abans, float, tuple]) -> dict[str, list[dict]]:
    """Un partit i un escenari: les files d'A pilota morta i d'A engolides a cada nivell (amb les llavors de provar), a
    les dues veritats, amb l'spellF1 d'A neteja d'aire a la de toc; i amb el nivell mitjà, les causes de cadascú i
    l'AUC del detector. S'atura si dona la D a una imatge netejada, o si sense etiquetes A pilota morta no dona
    exactament A neteja d'aire."""
    nom, escenari, a_pm, beta, triat = tasca
    base = med.base(nom, escenari)
    de_sempre, r, q_, netejades = base
    toc = vt.veritat(nom)
    partits = {SEMPRE: de_sempre, TOC: replace(de_sempre, veritat=toc)}
    trams = avalua.trams_valids(partits[TOC])
    neteja_pred = mna.prediccio(mna.amb_la_d_impossible(r, netejades), q_, de_sempre.trams, triat)
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}
    preds, aucs = {}, []
    for nivell in NIVELLS:
        relativa, _, equip, pa = _amb_el_detector(nom, escenari, nivell, PROVA, a_pm, triat, base)
        for metode, b in ((A_PM, 0.0), (A_EG, beta)):
            preds[(metode, nivell)] = _decodifica(nom, escenari, nivell, metode, relativa, pa, equip, b, base, triat)
        aucs.append({**comu, "nivell": nivell, **auc(toc, trams, equip, pa)})
    if not np.array_equal(preds[(A_PM, "cap")], neteja_pred):
        raise RuntimeError(f"{nom}, {escenari}: sense etiquetes, {A_PM} no dona {A_NETEJA}")
    neteja = avalua.puntua(partits[TOC], neteja_pred)["spell_f1"]
    files = [{**comu, "metode": metode, "nivell": nivell, "veritat": veritat, "beta": beta if metode == A_EG else 0.0,
              "neteja": neteja, **avalua.puntua(p, preds[(metode, nivell)])}
             for metode in (A_PM, A_EG) for nivell in NIVELLS for veritat, p in partits.items()]
    vista = ~np.isnan(de_sempre.tracking.pilota[:, 0])
    causes, sobren = [], []
    for metode in (A_PM, A_EG):
        c, s = causes_de(toc.astype(np.int8), preds[(metode, MITJA)], trams, vista)
        causes += [{**comu, "metode": metode, "causa": k, "n": n} for k, n in c.items()]
        sobren += [{**comu, "metode": metode, "on": k, "n": n} for k, n in s.items()]
    return {"files": files, "causes": causes, "sobrants": sobren, "auc": aucs}


def de_la_t3ah() -> dict[str, pmo.Abans]:
    desat = json.loads((DIR_RESULTATS / "model-pilota-morta.json").read_text())
    if desat["clau"] != mpm.clau_dels_resultats():
        raise RuntimeError("El banc de la T3ah no és d'aquest codi")
    return {nom: pmo.Abans(**a) for nom, a in desat["triats"].items()}


def taula_causes(causes: pd.DataFrame, sobren: pd.DataFrame, escenaris: tuple[str, ...]) -> pd.DataFrame:
    """Per a cada mètode, la part de les possessions de la veritat de cada causa, i les predites que sobren a l'altre
    equip per cada 100 de la veritat."""
    c = causes[causes["escenari"].isin(escenaris)].groupby(["metode", "causa"])["n"].sum().unstack("metode")
    totes = c.sum()
    t = (c / totes).reindex(of.CAUSES).fillna(0.0)
    s = sobren[sobren["escenari"].isin(escenaris)].groupby(["metode", "on"])["n"].sum().unstack("metode")
    t.loc["sobren a l'altre equip, per cada 100"] = 100 * s.reindex(["a l'altre equip"]).fillna(0.0).iloc[0] / totes
    return t[[A_PM, A_EG]].rename_axis("causa")


def taula_auc(aucs: pd.DataFrame) -> pd.DataFrame:
    t = aucs[aucs["nivell"] == MITJA]
    return t.groupby("escenari")[["auc"]].agg(["mean", "min"]).droplevel(0, axis=1).reindex(ESCENARIS).rename_axis(
        "escenari")


def importancia() -> pd.Series:
    """La part del guany de cada columna, a la mitjana dels deu detectors."""
    parts_ = []
    for nom in fonts.NOMS:
        guany = pd.Series(detector(nom, entrena=False)["importancia"], index=list(eg.COLUMNES))
        parts_.append(guany / guany.sum())
    return pd.concat(parts_, axis=1).mean(axis=1).sort_values(ascending=False)


def _regla(millor: dict[str, bool], robust: dict[str, bool]) -> list[str]:
    es = all(millor.values()) and all(robust.values())
    m = mpa._marca
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | {m(millor['quarts'])} |",
            f"| «{PARTIT}» | la diferència no és negativa | {m(millor['partit'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {m(millor['altres'])} |",
            f"| Dolent i cap | la segona part del criteri | {m(all(robust.values()))} |", "",
            f"**{A_EG} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_EG if es else A_PM}.", ""]


def markdown(r: dict) -> str:
    passa_tot = all(r["passa"].values()) and all(r["robust"].values())
    vores = sorted({b for b in r["betes"].values() if b in (min(BETES), max(BETES))})
    imp = r["importancia"]
    linies = ["# Banc obert · Un detector de les possessions engolides (T3aj)", "",
              "Generat amb `uv run python -I -m banc.model_engolides`. Dades obertes: 7 partits de DFL (IDSSE,",
              "CC BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3aj», i la capçalera de `banc/model_engolides.py`. Es puntua a la",
              "veritat de toc.", "",
              f"**{XARXES_TOC}** i **{A_EQUIPS}** són els de la T3v, **{A_CREIBLE}**, el de la T3w, **{A_NETEJA}**, el",
              f"de la T3ac, i **{A_PM}**, el de la T3ah (✓ comprovat). **{A_EG}** és {A_PM} amb, dins de les",
              "possessions predites, la del detector sumada a l'altre equip. ✓ Comprovat: no dona mai la D a una",
              f"imatge netejada; amb beta = 0 dona l'spellF1 d'{A_PM} de la T3ah, i sense etiquetes, exactament",
              f"{A_NETEJA}.", "",
              f"## Amb el nivell {MITJA}: {A_EG} contra {XARXES_TOC} (spellF1), el criteri", "",
              *t3b._taula(r["c"], A_EG, XARXES_TOC), "", *mt._criteris(r["passa"]),
              f"## Amb els nivells dolent i cap: {A_EG} contra {A_NETEJA}, la segona part del criteri", "",
              *mpa._robustesa(r["c_neteja"], r["robust"]), "",
              f"**{A_EG} {'passa' if passa_tot else 'no passa'} el criteri sencer.**", ""]
    for nivell in NIVELLS:
        linies += [f"## Amb el nivell {nivell}: {A_EG} contra {A_PM} (spellF1)", "",
                   *t3i._comparacio(r["c_pm"][nivell], A_EG, A_PM), ""]
    if not passa_tot:
        linies += ["## No passa: és el millor fins ara?", "",
                   f"La regla de la D-50, escrita abans, contra {A_PM} amb el nivell {MITJA}, i la mateixa segona part",
                   "del criteri:", "", *_regla(r["millor"], r["robust"])]
    for (titol, contra), taula in r["altres"].items():
        linies += [f"## {titol}", "", *t3i._comparacio(taula, A_EG, contra), ""]
    linies += ["## On falla, abans i després", "",
               f"Amb el nivell {MITJA}, les causes de `banc/on_falla.py`: la part de les possessions de la veritat de",
               "cada causa, i les predites que sobren a l'altre equip per cada 100 possessions de la veritat.", ""]
    for titol, escenaris in ((CURTS, (CURTS,)), ("els quatre ×¼ junts", QUARTS_T3), ("net", ("net",))):
        linies += [f"**{titol}**", "", mv._md(taula_causes(r["causes"], r["sobrants"], escenaris), 3), ""]
    linies += ["## El detector", "",
               f"L'AUC a les imatges de dins de les possessions predites, amb el nivell {MITJA} i les llavors de",
               "provar (la mitjana i la més baixa dels deu partits):", "", t3p.md(taula_auc(r["auc"])), "",
               f"Les mostres de cada un: de {min(r['mostres'].values())} a {max(r['mostres'].values())}; la part on",
               f"la veritat és l'altre equip, de {min(r['positives'].values()):.3f} a",
               f"{max(r['positives'].values()):.3f}. Les columnes que més hi fan (la part del guany, a la mitjana dels",
               "deu):", "", "| columna | part |", "|---|---|",
               *(f"| `{c}` | {v:.3f} |" for c, v in imp.head(15).items()), "",
               "## La beta triada", "",
               "A cada partit, amb els altres nou, als quatre ×¼ i a la mitjana dels nivells bo, mitjà i dolent.", "",
               "| partit | beta |", "|---|---|", *(f"| {nom} | {b:g} |" for nom, b in r["betes"].items()), "",
               (f"**A la vora de la graella:** beta = {', '.join(f'{b:g}' for b in vores)}." if vores
                else "Cap partit no tria a la vora de la graella."), "",
               f"## L'spellF1 de cada mètode (mitjana dels deu partits, nivell {MITJA})", "",
               *mt._mitjanes(r["mitja"], [XARXES_TOC, A_EQUIPS, A_NETEJA, A_PM, A_EG]), "## Els decodificadors", "",
               f"{A_NETEJA}, {A_PM} i {A_EG} fan servir, a cada partit, el d'{A_EQUIPS}.", "",
               *mq._triades(r["triades"]), ""]
    return "\n".join(linies)


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + mpm.clau_dels_resultats()).encode())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_engolides as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        return list(feina.map(getattr(aquest, fes), tasques))


def entrena_els_detectors(processos: int) -> None:
    from banc import model_engolides as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        for k, (nom, _) in enumerate(zip(fonts.NOMS, feina.map(aquest.detector, fonts.NOMS)), start=1):
            print(f"· {k}/{len(fonts.NOMS)}: el detector d'engolides de {nom}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=3, help="detectors alhora")
    args = ap.parse_args()
    for nom in fonts.NOMS:
        for metode in (XARXES, A_EQUIPS, A_CREIBLE):
            mpc.de_qui(metode, nom)
        mpc.q(nom, entrena=False)
        vt.veritat(nom)
        sts.represes(nom)
    metodes, triades = mcg.comprova_les_d_abans(args.processos)
    a_pm = de_la_t3ah()
    print(f"· {XARXES} i {A_EQUIPS} donen el del banc de la T3v, {A_CREIBLE}, el de la T3w, i {A_NETEJA}, el de "
          f"la T3ac; el banc de la T3ah és d'aquest codi", flush=True)
    de_la_neteja = triades[A_EQUIPS]
    n = en_paral_lel("mostres", [(nom, e, a_pm[nom], de_la_neteja[nom]) for nom, e in itertools.product(fonts.NOMS, SIS)],
                     args.processos)
    print(f"· Les mostres del detector: {sum(n)} en {len(n)} partits i escenaris", flush=True)
    entrena_els_detectors(args.processos_models)
    files_graella = pd.DataFrame([f for tros in en_paral_lel(
        "graella", [(nom, e, a_pm[nom], de_la_neteja[nom]) for nom, e in itertools.product(fonts.NOMS, QUARTS_T3)],
        args.processos) for f in tros])
    print(f"· {A_EG}: la graella, mai la D a les imatges netejades", flush=True)
    betes = {nom: tria(files_graella, nom) for nom in fonts.NOMS}
    tasques = [(nom, e, a_pm[nom], betes[nom], de_la_neteja[nom]) for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    trossos = en_paral_lel("informe", tasques, args.processos)
    nous, causes, sobren, aucs = (pd.DataFrame([f for tros in trossos for f in tros[k]])
                                  for k in ("files", "causes", "sobrants", "auc"))
    mre.comprova_la_t3ah(nous)
    nous_eg = nous[nous["metode"] == A_EG]
    med.comprova_la_neteja(nous_eg, metodes)
    print(f"· {A_EG}: amb beta = 0, l'spellF1 d'{A_PM} de la T3ah; sense etiquetes, {A_PM} és exactament {A_NETEJA}",
          flush=True)
    sense = nous.drop(columns=["beta", "neteja"])
    nomes_eg = sense[sense["metode"] == A_EG]
    c = mt.comparacio(mpa.de_nivell(metodes, nomes_eg, MITJA), A_EG, XARXES_TOC, TOC, amb_criteri=True)
    c_neteja = {n: mt.comparacio(mpa.de_nivell(metodes, nomes_eg, n), A_EG, A_NETEJA, TOC, amb_criteri=False)
                for n in NIVELLS}
    c_pm = {n: mt.comparacio(sense[sense["nivell"] == n].drop(columns="nivell"), A_EG, A_PM, TOC, amb_criteri=False)
            for n in NIVELLS}
    passa, robust, millor = mt.compleix(c), mpa.aguanta(c_neteja), mq.millor_fins_ara(c_pm[MITJA])
    mitja = mpa.de_nivell(metodes, sense, MITJA)
    altres_ = {(f"{A_EG} contra {contra}, nivell {MITJA}, només els partits de {font}", contra):
               mt.comparacio(mitja[mitja["font"] == font], A_EG, contra, TOC, amb_criteri=False)
               for font in mpc.FONTS for contra in (XARXES_TOC, A_PM)}
    altres_[(f"{A_EG} contra {XARXES_TOC}, nivell bo", XARXES_TOC)] = mt.comparacio(
        mpa.de_nivell(metodes, nomes_eg, "bo"), A_EG, XARXES_TOC, TOC, amb_criteri=False)
    imp = importancia()
    desats = {nom: detector(nom, entrena=False) for nom in fonts.NOMS}
    mostres_ = {nom: int(d["mostres"]) for nom, d in desats.items()}
    positives = {nom: float(d["positives"]) for nom, d in desats.items()}
    r = {"c": c, "passa": passa, "robust": robust, "c_neteja": c_neteja, "c_pm": c_pm, "millor": millor,
         "altres": altres_, "causes": causes, "sobrants": sobren, "auc": aucs, "betes": betes, "importancia": imp,
         "mostres": mostres_, "positives": positives, "mitja": mitja, "triades": {A_EQUIPS: de_la_neteja}}
    contingut = {"clau": clau_dels_resultats(), "passa": passa, "aguanta": robust, "millor_fins_ara": millor,
                 "comparacio": t3.registres(c),
                 "contra_a_neteja_d_aire": {n: t3.registres(t) for n, t in c_neteja.items()},
                 "contra_a_pilota_morta": {n: t3.registres(t) for n, t in c_pm.items()},
                 "betes": betes, "mostres": mostres_, "positives": positives,
                 "importancia": {k: float(v) for k, v in imp.items()},
                 "triades": {A_EQUIPS: de_la_neteja}, "files": t3.registres(nous),
                 "graella": t3.registres(files_graella),
                 "altres": {titol: t3.registres(t) for (titol, _), t in altres_.items()},
                 "causes": t3.registres(causes), "sobrants": t3.registres(sobren),
                 "auc": t3.registres(aucs)}
    mpa.escriu("model-engolides", contingut, markdown(r))


if __name__ == "__main__":
    main()
