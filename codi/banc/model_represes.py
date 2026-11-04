"""Un segon només per a les represes, a sobre d'A pilota morta (T3ai del pla per tocs, `docs/pla-tocs.md`, «T3ai»;
D-71).

    cd codi && uv run python -I -m banc.model_represes [--processos 12] [--processos-models 3]

A pilota morta (T3ah) tal qual, amb els paràmetres que hi va triar cada partit. A sobre, **el segon de les represes**:
un classificador com el segon, que veu el mateix que el segon del pas 2 de la T3af (les columnes del segon d'A neteja
d'aire i les 17 del Smart Tagging simulat), però que només aprèn i només s'aplica a l'entorn de cada etiqueta
(`cadena/represes.py`). A l'entorn, la probabilitat relativa es barreja amb la d'A pilota morta amb `alfa`. Després,
la D impossible on la neteja ha tret la pilota, i el decodificador d'A equips sencers.

1. **En començar:** A xarxes i A equips sencers, amb la memòria cau, han de donar el banc de la T3v, A pilota creïble,
   el de la T3w, i A neteja d'aire, el de la T3ac; i el banc de la T3ah ha de ser d'aquest codi. Si no, s'atura.
2. **El segon de les represes de cada partit** (`segon`), après dels altres nou, als sis escenaris d'entrenament, amb
   les mateixes mostres que el segon del pas 2 de la T3af (`mpa.per_aprendre`), les etiquetes al nivell de cada partit
   i escenari amb les llavors d'aprendre, només les imatges de l'entorn (`mostres_entorn`), cadascuna també girada, i
   la veritat de toc. S'aplica al partit netejat, a l'entorn de les etiquetes d'aprendre (els quatre ×¼ i els nivells
   bo, mitjà i dolent) i de les de provar (els onze escenaris i els quatre nivells). Es desa a la memòria cau.
3. **La graella** (`rp.ALFES`) als quatre ×¼ de cada partit, amb els nivells bo, mitjà i dolent i les llavors
   d'aprendre. Cap punt no hi ha de donar la D a una imatge netejada.
4. **La tria** de cada partit, amb els altres nou: l'`alfa` amb més spellF1 de mitjana als quatre ×¼ i als tres
   nivells, a la veritat de toc (`tria`).
5. **Es prova** als onze escenaris amb els quatre nivells i les llavors de provar. Amb `alfa` = 0 ha de donar l'spellF1
   d'A pilota morta del banc de la T3ah, i sense etiquetes, exactament A neteja d'aire. Si no, s'atura.
6. **El criteri** del pla, el de la T3ah; el millor fins ara, contra A pilota morta. Només per saber-ho: per font;
   amb el nivell bo; contra A pilota morta a cada nivell; els errors a l'entorn de les represes; la part del sostre de
   la T3af que se n'aprofita; l'`alfa` triat i les columnes que més fa servir el segon de les represes.

Escriu `resultats/model-represes.json` i `.md`. Tot són dades obertes. Els mòduls d'abans no es toquen.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import itertools
import json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from banc import analisi_t3p as t3p
from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_context as t3e
from banc import model_a_equips as mae
from banc import model_a_partit as mp
from banc import model_a_possessio as t3f
from banc import model_a_q as mq
from banc import model_a_quart as t3b
from banc import model_a_toc as mt
from banc import model_a_xarxa as t3m
from banc import model_camp_girat as mcg
from banc import model_etiquetes_decodificador as med
from banc import model_neteja_aire as mna
from banc import model_pilota_creible as mpc
from banc import model_pilota_morta as mpm
from banc import model_pilotes_aturades as mpa
from banc import model_vores as mv
from banc import smart_tagging_simulat as sts
from banc import sostre_sense_pilota as ssp
from banc import veritat_toc as vt
from cadena import model, senyals
from cadena import pilota_morta as pmo
from cadena import represes as rp
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ESCENARIS, QUARTS_T3, PARTIT, SIS = med.ESCENARIS, med.QUARTS_T3, med.PARTIT, mpa.SIS
XARXES, XARXES_TOC, A_EQUIPS, A_CREIBLE, A_NETEJA = med.XARXES, med.XARXES_TOC, med.A_EQUIPS, med.A_CREIBLE, med.A_NETEJA
A_PM = mpm.A_PM
A_RE = "A represes"
SEMPRE, TOC = med.SEMPRE, med.TOC
NIVELLS, NIVELLS_TRIA, MITJA = med.NIVELLS, med.NIVELLS_TRIA, med.MITJA
TRIA, PROVA = med.TRIA, med.PROVA                   # les etiquetes de la T3ag
CLAUS = (*((TRIA, e, n) for e in QUARTS_T3 for n in NIVELLS_TRIA), *((PROVA, e, n) for e in ESCENARIS for n in NIVELLS))
TRAMS_ERRORS = ((-10, -5), (-5, -2), (-2, 0), (0, 1), (1, 3), (3, 5), (5, 10))     # segons des de la represa
ERRORS = ("bé", "diu un equip i és D", "diu D i és un equip", "l'altre equip")
DIR_CAU = mpa.DIR_CAU
DIR_RESULTATS = t3.DIR_RESULTATS


def mostres_entorn(veritat: np.ndarray, trams_valids: list[tuple[int, int]], taula: pd.DataFrame,
                   entorn: np.ndarray) -> tuple[pd.DataFrame, np.ndarray]:
    """Les imatges que s'aprenen (`t3f.tria`) que són a l'entorn, cadascuna també amb els equips girats."""
    t = t3f.tria(veritat, trams_valids)
    t = t[entorn[t]]
    x = taula.iloc[t].reset_index(drop=True)
    y = veritat[t]
    return (pd.concat([x, senyals.intercanvia(x)], ignore_index=True),
            np.concatenate([y, model.GIRA[y]]).astype(np.int8))


def mostres(prova: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Les mostres del segon de les represes de `prova`: les dels altres nou del segon del pas 2 de la T3af, amb les
    etiquetes al nivell de cada partit i escenari i la llavor d'aprendre, a l'entorn i amb la veritat de toc."""
    primers, de_les_xarxes = {}, {}
    for i in range(t3e.GRUPS):
        primers |= mp.primer_del_grup((prova, i, SIS))
        de_les_xarxes |= mae.xarxes_del_grup((prova, i), entrena=False)
    if sorted(primers) != sorted(mpa.per_aprendre(prova)) or any(nom == prova for nom, _ in primers):
        raise RuntimeError(f"{prova}: les mostres del segon de les represes no són les dels altres nou")
    xs, ys = [], []
    for (nom, e), primer in primers.items():
        p = mp.degradat(nom, e)
        etiquetes = mpa.etiquetes_de(nom, e, sts.nivell_per_aprendre(nom, e), TRIA)
        taula = mpa.amb_les_etiquetes(t3m.taula_segon(p, primer.astype(float), de_les_xarxes[(nom, e)].astype(float)),
                                      etiquetes, p.trams)
        toc = replace(p, veritat=vt.veritat(nom))
        x, y = mostres_entorn(toc.veritat, avalua.trams_valids(toc), taula, rp.entorn(etiquetes, len(taula), p.trams))
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def clau() -> str:
    """El que fa les probabilitats d'aquí: les peces de la T3af, l'entorn i això."""
    h = hashlib.sha256((mpa.CLAU + repr((CLAUS, rp.ABANS_S, rp.DESPRES_S))).encode())
    h.update(Path(rp.__file__).read_bytes())
    for funcio in (mostres_entorn, mostres, segon):
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


def segon(prova: str, entrena: bool = True) -> dict[str, np.ndarray]:
    """El segon de les represes de `prova`, après amb `mostres`, aplicat al partit netejat a l'entorn de les etiquetes
    de cada una de les `CLAUS`: a cada una, les imatges (`c{k}_i`) i les probabilitats (`c{k}_p`). També el prior, les
    columnes, el guany de cada una i quantes mostres."""
    cami = DIR_CAU / f"segon-represes-{prova}.npz"
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falta el segon de les represes de {prova}, o és d'un altre codi")
        x, y = mostres(prova)
        entrenat = model.entrena(x, y)
        desat = {"prior": model.prior(y), "columnes": np.array(list(x.columns)), "mostres": np.array(len(y)),
                 "importancia": entrenat.feature_importance("gain")}
        del x
        primers, de_les_xarxes = mpc.primer(prova, entrena=False), mpc.xarxes_de_la_prova(prova, entrena=False)
        for e in ESCENARIS:
            p = mpc.creible(prova, e)
            base = t3m.taula_segon(p, primers[e].astype(float), de_les_xarxes[e].astype(float))
            for k, (per, e_, nivell) in enumerate(CLAUS):
                if e_ != e:
                    continue
                etiquetes = mpa.etiquetes_de(prova, e, nivell, per)
                idx = np.flatnonzero(rp.entorn(etiquetes, len(base), p.trams)).astype(np.int32)
                probes = (model.probabilitats(entrenat, mpa.amb_les_etiquetes(base, etiquetes, p.trams).iloc[idx])
                          if len(idx) else np.zeros((0, 3)))
                desat[f"c{k}_i"], desat[f"c{k}_p"] = idx, probes.astype(np.float32)
        desa(cami, **desat)
    return desat


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def a_tot(n: int, idx: np.ndarray, probes: np.ndarray, prior: np.ndarray) -> np.ndarray:
    """(n, 3): la probabilitat relativa del segon de les represes a les imatges `idx`, i fora, res (NaN)."""
    x = np.full((n, 3), np.nan)
    if len(idx):
        x[idx] = log_relativa(probes.astype(float), prior)
    return x


def de_les_represes(nom: str, per: str, escenari: str, nivell: str, etiquetes: tuple, n: int,
                    trams: tuple[tuple[int, int, int], ...]) -> tuple[np.ndarray, np.ndarray]:
    """L'entorn de `etiquetes` i la probabilitat relativa del segon de les represes de `nom` (de la memòria cau). S'atura
    si l'entorn no és el que es va desar."""
    desat = segon(nom, entrena=False)
    k = CLAUS.index((per, escenari, nivell))
    entorn = rp.entorn(etiquetes, n, trams)
    if not np.array_equal(np.flatnonzero(entorn), desat[f"c{k}_i"]):
        raise RuntimeError(f"{nom}, {escenari}, {nivell}: l'entorn no és el del segon de les represes desat")
    return entorn, a_tot(n, desat[f"c{k}_i"], desat[f"c{k}_p"], desat["prior"])


def relativa_amb(r_pm: np.ndarray, de_les_represes_: np.ndarray, entorn: np.ndarray, alfa: float,
                 netejades: np.ndarray) -> np.ndarray:
    """La relativa d'A pilota morta amb la del segon de les represes barrejada a l'entorn, i després la D impossible a
    `netejades`."""
    return mna.amb_la_d_impossible(rp.barreja(r_pm, de_les_represes_, entorn, alfa), netejades)


def _peces(nom: str, escenari: str, nivell: str, per: str, a_pm: pmo.Abans, de_sempre, r: np.ndarray) -> tuple:
    etiquetes = mpa.etiquetes_de(nom, escenari, nivell, per)
    r_pm = pmo.amb_les_etiquetes(r, etiquetes, de_sempre.trams, a_pm, mpm.medianes_sense(nom))
    return (r_pm, *de_les_represes(nom, per, escenari, nivell, etiquetes, len(r), de_sempre.trams))


def graella(tasca: tuple[str, str, pmo.Abans, tuple]) -> list[dict]:
    """Un partit i un ×¼, amb A pilota morta (`a_pm`) i el decodificador d'A neteja d'aire (`triat`): cada `alfa` amb
    els nivells de `NIVELLS_TRIA` i les llavors d'aprendre, a la veritat de toc."""
    nom, escenari, a_pm, triat = tasca
    de_sempre, r, q_, netejades = med.base(nom, escenari)
    p = replace(de_sempre, veritat=vt.veritat(nom))
    files = []
    for nivell in NIVELLS_TRIA:
        r_pm, entorn, x = _peces(nom, escenari, nivell, TRIA, a_pm, de_sempre, r)
        for alfa in rp.ALFES:
            pred = mna.prediccio(relativa_amb(r_pm, x, entorn, alfa, netejades), q_, de_sempre.trams, triat)
            if (pred[netejades] == pm.D).any():
                raise RuntimeError(f"{nom}, {escenari}, {nivell}, alfa {alfa}: {A_RE} dona la D a una imatge netejada")
            files.append({"partit": nom, "font": de_sempre.font, "escenari": escenari, "nivell": nivell, "alfa": alfa,
                          **{k: v for k, v in avalua.puntua(p, pred).items() if k in ("spell_f1", "macro_f1")}})
    return files


def tria(files: pd.DataFrame, prova: str) -> float:
    """L'`alfa` per a `prova`, amb els altres nou: el de més spellF1 de mitjana als quatre ×¼ i als nivells de les files
    (desempata el macroF1)."""
    millor = mp.millor(files[files["partit"] != prova], ["alfa"], QUARTS_T3)
    return float(millor[0] if isinstance(millor, tuple) else millor)


def errors_a_l_entorn(toc: np.ndarray, pred: np.ndarray, valides: np.ndarray, represes: tuple) -> Counter:
    """A cada tram de `TRAMS_ERRORS` de cada represa, quantes imatges vàlides hi ha de cada mena d'`ERRORS`."""
    c: Counter = Counter()
    for rep in represes:
        for de, fins in TRAMS_ERRORS:
            i = np.arange(max(0, rep.imatge + de * pm.FPS), min(len(toc), rep.imatge + fins * pm.FPS))
            i = i[valides[i]]
            v, q = toc[i], pred[i]
            mena = np.where(v == q, 0, np.where(v == pm.D, 1, np.where(q == pm.D, 2, 3)))
            c.update({(f"{de} a {fins} s", ERRORS[m]): int(k) for m, k in zip(*np.unique(mena, return_counts=True))})
    return c


def informe(tasca: tuple[str, str, pmo.Abans, float, tuple]) -> dict[str, list[dict]]:
    """Un partit i un escenari: les files d'A pilota morta i d'A represes a cada nivell (amb les llavors de provar), a
    les dues veritats, amb l'spellF1 d'A neteja d'aire a la de toc; a prop de les represes, on encerta cadascú; i amb el
    nivell mitjà, els errors a l'entorn de les represes. S'atura si dona la D a una imatge netejada, o si sense
    etiquetes no dona exactament A neteja d'aire."""
    nom, escenari, a_pm, alfa, triat = tasca
    de_sempre, r, q_, netejades = med.base(nom, escenari)
    toc = vt.veritat(nom)
    partits = {SEMPRE: de_sempre, TOC: replace(de_sempre, veritat=toc)}
    trams = avalua.trams_valids(partits[TOC])
    valides = ssp.dins(len(toc), trams)
    represes = sts.represes(nom).represes
    prop = mpa.a_prop(represes, len(toc), de_sempre.trams) & valides
    preds = {(A_NETEJA, ""): mna.prediccio(mna.amb_la_d_impossible(r, netejades), q_, de_sempre.trams, triat)}
    for nivell in NIVELLS:
        r_pm, entorn, x = _peces(nom, escenari, nivell, PROVA, a_pm, de_sempre, r)
        for metode, a in ((A_PM, 0.0), (A_RE, alfa)):
            preds[(metode, nivell)] = mna.prediccio(relativa_amb(r_pm, x, entorn, a, netejades), q_, de_sempre.trams,
                                                    triat)
            if (preds[(metode, nivell)][netejades] == pm.D).any():
                raise RuntimeError(f"{nom}, {escenari}, {nivell}: {metode} dona la D a una imatge netejada")
    if not (np.array_equal(preds[(A_RE, "cap")], preds[(A_NETEJA, "")])
            and np.array_equal(preds[(A_PM, "cap")], preds[(A_NETEJA, "")])):
        raise RuntimeError(f"{nom}, {escenari}: sense etiquetes, {A_RE} no dona {A_NETEJA}")
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}
    neteja = avalua.puntua(partits[TOC], preds[(A_NETEJA, "")])["spell_f1"]
    files = [{**comu, "metode": metode, "nivell": nivell, "veritat": veritat, "alfa": alfa if metode == A_RE else 0.0,
              "neteja": neteja, **avalua.puntua(p, preds[(metode, nivell)])}
             for metode in (A_PM, A_RE) for nivell in NIVELLS for veritat, p in partits.items()]
    encerts = [{**comu, "metode": metode, "nivell": nivell, "n": int(prop.sum()),
                "encerts": int((pm.fill_abstentions(pred.astype(np.int8), trams)[prop] == toc[prop]).sum())}
               for (metode, nivell), pred in preds.items()]
    errors = [{**comu, "metode": metode, "tram": tram, "mena": mena, "n": n}
              for metode in (A_PM, A_RE)
              for (tram, mena), n in errors_a_l_entorn(toc, pm.fill_abstentions(
                  preds[(metode, MITJA)].astype(np.int8), trams), valides, represes).items()]
    return {"files": files, "encerts": encerts, "errors": errors}


def comprova_la_t3ah(nous: pd.DataFrame) -> None:
    """A pilota morta d'aquí (amb `alfa` = 0) ha de donar l'spellF1 del banc de la T3ah, a cada partit, escenari, nivell
    i veritat."""
    claus = ["partit", "escenari", "nivell", "veritat"]
    de_la_t3ah = pd.DataFrame(json.loads((DIR_RESULTATS / "model-pilota-morta.json").read_text())["files"]).set_index(
        claus)["spell_f1"]
    aqui = nous[nous["metode"] == A_PM].set_index(claus)["spell_f1"]
    if len(aqui) != len(de_la_t3ah) or not np.allclose(aqui, de_la_t3ah.reindex(aqui.index), atol=1e-12, rtol=0):
        raise RuntimeError(f"{A_PM} d'aquí no dona l'spellF1 del banc de la T3ah")


def de_la_t3ah() -> dict[str, pmo.Abans]:
    desat = json.loads((DIR_RESULTATS / "model-pilota-morta.json").read_text())
    return {nom: pmo.Abans(**a) for nom, a in desat["triats"].items()}


def taula_errors(t: pd.DataFrame, escenaris: tuple[str, ...]) -> pd.DataFrame:
    g = t[t["escenari"].isin(escenaris)].groupby(["metode", "tram", "mena"])["n"].sum()
    part = (g / g.groupby(["metode", "tram"]).transform("sum")).unstack(["metode", "mena"]).fillna(0.0)
    trams = [f"{de} a {fins} s" for de, fins in TRAMS_ERRORS]
    part = part.reindex(index=trams, columns=pd.MultiIndex.from_product([(A_PM, A_RE), ERRORS]), fill_value=0.0)
    part.columns = [f"{m} · {mena}" for m, mena in part.columns]
    return part.rename_axis("tram")


def taula_encerts(t: pd.DataFrame) -> pd.DataFrame:
    g = t.groupby(["escenari", "metode", "nivell"], sort=False)[["n", "encerts"]].sum()
    part = (g["encerts"] / g["n"]).unstack(["metode", "nivell"])
    part.columns = [m if m == A_NETEJA else f"{m}, {n}" for m, n in part.columns]
    ordre = [A_NETEJA, *(f"{A_PM}, {n}" for n in NIVELLS[:-1]), *(f"{A_RE}, {n}" for n in NIVELLS[:-1])]
    return part[ordre].reindex(ESCENARIS).rename_axis("escenari")


def importancia() -> pd.Series:
    """La part del guany de cada columna, a la mitjana dels deu segons de les represes."""
    parts = []
    for nom in fonts.NOMS:
        desat = segon(nom, entrena=False)
        guany = pd.Series(desat["importancia"], index=desat["columnes"].tolist())
        parts.append(guany / guany.sum())
    return pd.concat(parts, axis=1).fillna(0.0).mean(axis=1).sort_values(ascending=False)


def _regla(millor: dict[str, bool], robust: dict[str, bool]) -> list[str]:
    es = all(millor.values()) and all(robust.values())
    m = mpa._marca
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | {m(millor['quarts'])} |",
            f"| «{PARTIT}» | la diferència no és negativa | {m(millor['partit'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {m(millor['altres'])} |",
            f"| Dolent i cap | la segona part del criteri | {m(all(robust.values()))} |", "",
            f"**{A_RE} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_RE if es else A_PM}.", ""]


def markdown(r: dict) -> str:
    passa_tot = all(r["passa"].values()) and all(r["robust"].values())
    vores = sorted({a for a in r["alfes"].values() if a in (min(rp.ALFES), max(rp.ALFES))})
    imp = r["importancia"]
    st_part = float(imp[[c for c in imp.index if c.startswith("st_")]].sum())
    linies = ["# Banc obert · Un segon només per a les represes (T3ai)", "",
              "Generat amb `uv run python -I -m banc.model_represes`. Dades obertes: 7 partits de DFL (IDSSE,",
              "CC BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3ai», i la capçalera de `banc/model_represes.py`. Es puntua a la",
              "veritat de toc.", "",
              f"**{XARXES_TOC}** i **{A_EQUIPS}** són els de la T3v, **{A_CREIBLE}**, el de la T3w, **{A_NETEJA}**, el",
              f"de la T3ac, i **{A_PM}**, el de la T3ah (✓ comprovat). **{A_RE}** és {A_PM} amb, a l'entorn de cada",
              "etiqueta, la probabilitat relativa del segon de les represes barrejada. ✓ Comprovat: no dona mai la D a",
              "una imatge netejada, i sense etiquetes dona exactament A neteja d'aire.", "",
              f"## Amb el nivell {MITJA}: {A_RE} contra {XARXES_TOC} (spellF1), el criteri", "",
              *t3b._taula(r["c"], A_RE, XARXES_TOC), "", *mt._criteris(r["passa"]),
              f"## Amb els nivells dolent i cap: {A_RE} contra {A_NETEJA}, la segona part del criteri", "",
              *mpa._robustesa(r["c_neteja"], r["robust"]), "",
              f"**{A_RE} {'passa' if passa_tot else 'no passa'} el criteri sencer.**", ""]
    for nivell in NIVELLS:
        linies += [f"## Amb el nivell {nivell}: {A_RE} contra {A_PM} (spellF1)", "",
                   *t3i._comparacio(r["c_pm"][nivell], A_RE, A_PM), ""]
    if not passa_tot:
        linies += ["## No passa: és el millor fins ara?", "",
                   f"La regla de la D-50, escrita abans, contra {A_PM} amb el nivell {MITJA}, i la mateixa segona part",
                   "del criteri:", "", *_regla(r["millor"], r["robust"])]
    for (titol, contra), taula in r["altres"].items():
        linies += [f"## {titol}", "", *t3i._comparacio(taula, A_RE, contra), ""]
    linies += ["## Els errors a l'entorn de les represes", "",
               f"Amb el nivell {MITJA}, la part de les imatges vàlides de cada tram, segons on són respecte de la",
               "represa de veritat. «Diu un equip i és D» vol dir que la predicció (amb les abstencions omplertes) és",
               "un equip i la veritat de toc és la D.", ""]
    for titol, escenaris in (("curts ×¼", ("curts ×¼",)), ("els quatre ×¼ junts", QUARTS_T3)):
        linies += [f"**{titol}**", "", mv._md(taula_errors(r["errors"], escenaris), 3), ""]
    linies += ["## La part del sostre de la T3af que se n'aprofita", "",
               "A la veritat de toc, la mitjana dels deu partits: el sostre de la T3af menys A neteja d'aire, el que en",
               f"treu {A_RE}, i la part.", "", t3p.md(r["sostre"]), "",
               "## A 5 s o menys de cada represa", "",
               "La part de les imatges vàlides a 5 s o menys d'una represa on la predicció (amb les abstencions",
               "omplertes) és la veritat de toc.", "", t3p.md(taula_encerts(r["encerts"])), "",
               "## L'alfa triat", "",
               "A cada partit, amb els altres nou, als quatre ×¼ i a la mitjana dels nivells bo, mitjà i dolent.", "",
               "| partit | alfa |", "|---|---|", *(f"| {nom} | {a:g} |" for nom, a in r["alfes"].items()), "",
               (f"**A la vora de la graella:** alfa = {', '.join(f'{a:g}' for a in vores)}." if vores
                else "Cap partit no tria a la vora de la graella."), "",
               "## El segon de les represes", "",
               f"Les mostres de cada un (amb les girades): de {min(r['mostres'].values())} a "
               f"{max(r['mostres'].values())}. Les 17 columnes del Smart Tagging hi fan el {100 * st_part:.1f} % del",
               "guany. Les 15 columnes que més hi fan (la part del guany, a la mitjana dels deu):", "",
               "| columna | part |", "|---|---|", *(f"| `{c}` | {v:.3f} |" for c, v in imp.head(15).items()), "",
               f"## L'spellF1 de cada mètode (mitjana dels deu partits, nivell {MITJA})", "",
               *mt._mitjanes(r["mitja"], [XARXES_TOC, A_EQUIPS, A_NETEJA, A_PM, A_RE]), "## Els decodificadors", "",
               f"{A_NETEJA}, {A_PM} i {A_RE} fan servir, a cada partit, el d'{A_EQUIPS}.", "",
               *mq._triades(r["triades"]), ""]
    return "\n".join(linies)


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + mpm.clau_dels_resultats()).encode())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_represes as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        return list(feina.map(getattr(aquest, fes), tasques))


def entrena_els_segons(processos: int) -> None:
    from banc import model_represes as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        for k, (nom, _) in enumerate(zip(fonts.NOMS, feina.map(aquest.segon, fonts.NOMS)), start=1):
            print(f"· {k}/{len(fonts.NOMS)}: el segon de les represes de {nom}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=3, help="segons de les represes alhora")
    args = ap.parse_args()
    for nom in fonts.NOMS:
        for metode in (XARXES, A_EQUIPS, A_CREIBLE):
            mpc.de_qui(metode, nom)
        mpc.q(nom, entrena=False)
        vt.veritat(nom)
        sts.represes(nom)
    metodes, triades = mcg.comprova_les_d_abans(args.processos)
    a_pm = de_la_t3ah()
    if json.loads((DIR_RESULTATS / "model-pilota-morta.json").read_text())["clau"] != mpm.clau_dels_resultats():
        raise RuntimeError("El banc de la T3ah no és d'aquest codi")
    print(f"· {XARXES} i {A_EQUIPS} donen el del banc de la T3v, {A_CREIBLE}, el de la T3w, i {A_NETEJA}, el de "
          f"la T3ac; el banc de la T3ah és d'aquest codi", flush=True)
    entrena_els_segons(args.processos_models)
    de_la_neteja = triades[A_EQUIPS]
    files_graella = pd.DataFrame([f for tros in en_paral_lel(
        "graella", [(nom, e, a_pm[nom], de_la_neteja[nom]) for nom, e in itertools.product(fonts.NOMS, QUARTS_T3)],
        args.processos) for f in tros])
    print(f"· {A_RE}: la graella, mai la D a les imatges netejades", flush=True)
    alfes = {nom: tria(files_graella, nom) for nom in fonts.NOMS}
    tasques = [(nom, e, a_pm[nom], alfes[nom], de_la_neteja[nom]) for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    trossos = en_paral_lel("informe", tasques, args.processos)
    nous, encerts, errors = (pd.DataFrame([f for tros in trossos for f in tros[k]]) for k in ("files", "encerts",
                                                                                              "errors"))
    comprova_la_t3ah(nous)
    nous_re = nous[nous["metode"] == A_RE]
    med.comprova_la_neteja(nous_re, metodes)
    print(f"· {A_RE}: amb alfa = 0, l'spellF1 d'{A_PM} de la T3ah; sense etiquetes, exactament {A_NETEJA}", flush=True)
    sense = nous.drop(columns=["alfa", "neteja"])
    nomes_re = sense[sense["metode"] == A_RE]
    c = mt.comparacio(mpa.de_nivell(metodes, nomes_re, MITJA), A_RE, XARXES_TOC, TOC, amb_criteri=True)
    c_neteja = {n: mt.comparacio(mpa.de_nivell(metodes, nomes_re, n), A_RE, A_NETEJA, TOC, amb_criteri=False)
                for n in NIVELLS}
    c_pm = {n: mt.comparacio(sense[sense["nivell"] == n].drop(columns="nivell"), A_RE, A_PM, TOC, amb_criteri=False)
            for n in NIVELLS}
    passa, robust, millor = mt.compleix(c), mpa.aguanta(c_neteja), mq.millor_fins_ara(c_pm[MITJA])
    mitja = mpa.de_nivell(metodes, sense, MITJA)
    altres = {(f"{A_RE} contra {contra}, nivell {MITJA}, només els partits de {font}", contra):
              mt.comparacio(mitja[mitja["font"] == font], A_RE, contra, TOC, amb_criteri=False)
              for font in mpc.FONTS for contra in (XARXES_TOC, A_PM)}
    altres[(f"{A_RE} contra {XARXES_TOC}, nivell bo", XARXES_TOC)] = mt.comparacio(
        mpa.de_nivell(metodes, nomes_re, "bo"), A_RE, XARXES_TOC, TOC, amb_criteri=False)
    imp = importancia()
    mostres_ = {nom: int(segon(nom, entrena=False)["mostres"]) for nom in fonts.NOMS}
    r = {"c": c, "passa": passa, "robust": robust, "c_neteja": c_neteja, "c_pm": c_pm, "millor": millor,
         "altres": altres, "errors": errors, "sostre": med.part_del_sostre(nous_re), "encerts": encerts, "alfes": alfes,
         "importancia": imp, "mostres": mostres_, "mitja": mitja, "triades": {A_EQUIPS: de_la_neteja}}
    contingut = {"clau": clau_dels_resultats(), "passa": passa, "aguanta": robust, "millor_fins_ara": millor,
                 "comparacio": t3.registres(c),
                 "contra_a_neteja_d_aire": {n: t3.registres(t) for n, t in c_neteja.items()},
                 "contra_a_pilota_morta": {n: t3.registres(t) for n, t in c_pm.items()},
                 "alfes": alfes, "mostres": mostres_, "importancia": {k: float(v) for k, v in imp.head(40).items()},
                 "triades": {A_EQUIPS: de_la_neteja}, "files": t3.registres(nous),
                 "graella": t3.registres(files_graella),
                 "altres": {titol: t3.registres(t) for (titol, _), t in altres.items()},
                 "encerts": t3.registres(encerts), "errors": t3.registres(errors)}
    mpa.escriu("model-represes", contingut, markdown(r))


if __name__ == "__main__":
    main()
