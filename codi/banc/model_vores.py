"""Les vores dels canvis, afinades (T3ae del pla per tocs, `docs/pla-tocs.md`, «T3ae»; D-66).

    cd codi && uv run python -I -m banc.model_vores [--processos 12] [--processos-models 3]

A neteja d'aire (T3ac) tal qual, i després del decodificador, un LightGBM que mou cada canvi de la predicció fins a
0,5 s, on és més probable el canvi de la veritat (`cadena/vores.py`).

1. **En començar:** A xarxes i A equips sencers, amb la memòria cau, han de donar el banc de la T3v, A pilota creïble,
   el de la T3w, i A neteja d'aire, amb el decodificador d'A equips sencers, el de la T3ac (com a la T3ad). Si no,
   s'atura.
2. **Les prediccions dels altres nou, sense el partit que es prova:** per a cada partit que es prova i cada grup dels
   altres nou (els de la T3e), un segon i una q nous, entrenats amb les mostres de sempre dels altres sis (les de
   `mae.mostres_segon` i `mp.mostres_q`, sense les del grup), i aplicats al grup amb el seu primer i les seves cinc
   xarxes (de la memòria cau de la T3p i de la T3v). 30 segons i 30 q (`dades/banc/vores/`). Amb el decodificador d'A
   neteja d'aire del partit que es prova, la predicció de cada partit del grup als sis escenaris d'entrenament. Allà
   la neteja no treu res (si en tragués, s'atura).
3. **Les vores de cada partit:** el LightGBM aprèn amb els canvis d'aquestes prediccions dels altres nou, a la veritat
   de toc, i mou els de la predicció d'A neteja d'aire del partit que es prova, a tots els escenaris, amb les seves
   peces (de la memòria cau) i el seu decodificador. Mai la D a una imatge netejada: si n'hi posés, s'atura.
4. **El criteri** del pla: A vores contra A xarxes, a la veritat de toc. Si no passa, la regla de la D-50 contra A
   neteja d'aire. Només per saber-ho: per font, com es mouen els canvis, i el sostre de les vores perfectes (calculat
   com a la comprovació 2 de «Tres maneres per al pas següent, a sobre d'A neteja d'aire», que ha de donar el mateix)
   i la part que se'n treu.

Escriu `resultats/model-vores.json` i `resultats/model-vores.md`. Tot són dades obertes. Els mòduls d'abans no es
toquen.
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
from banc import model_a_contacte as t3h
from banc import model_a_context as t3e
from banc import model_a_equips as mae
from banc import model_a_partit as mp
from banc import model_a_possessio as t3f
from banc import model_a_q as mq
from banc import model_a_quart as t3b
from banc import model_a_toc as mt
from banc import model_a_xarxa as t3m
from banc import model_camp_girat as mcg
from banc import model_neteja_aire as mna
from banc import model_pilota_creible as mpc
from banc import veritat_toc as vt
from cadena import model
from cadena import pilota_creible as pc
from cadena import vores as vo
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ESCENARIS = mp.ESCENARIS                            # els deu de la T3 i «partit ×¼»
SIS = mp.SIS
XARXES, XARXES_TOC, A_EQUIPS, A_CREIBLE = mpc.XARXES, mpc.XARXES_TOC, mpc.A_EQUIPS, mpc.A_CREIBLE
A_NETEJA = mna.A_NETEJA
A_VORES = "A vores"
SEMPRE, TOC = mpc.SEMPRE, mpc.TOC
FONTS = mpc.FONTS
A_PROP = 2                                          # imatges: un canvi a 2 o menys del de la veritat, gairebé bo
# el sostre de les vores perfectes, de la comprovació 2 (mitjana dels deu partits, a 4 decimals)
COMPROVACIO_2 = {"net": 0.0109, "curts ×¼": 0.0153, "llargs ×¼": 0.0135, "barreja ×¼": 0.0137, "aire ×¼": 0.0161,
                 mp.PARTIT: 0.0108}
DIR_CAU = fonts.DIR_CAU / "vores"
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


def dels_altres_grups(prova: str, i: int) -> list[tuple[dict, dict]]:
    """El primer i les cinc xarxes de cada partit dels altres dos grups de `prova`, als sis escenaris d'entrenament
    (de la memòria cau): els altres sis partits, sense els del grup `i`."""
    return [(mp.primer_del_grup((prova, j, SIS)), mae.xarxes_del_grup((prova, j), entrena=False))
            for j in range(t3e.GRUPS) if j != i]


def mostres_segon(prova: str, i: int) -> tuple[pd.DataFrame, np.ndarray]:
    """Les de `mae.mostres_segon(prova)`, sense les dels partits del grup `i`."""
    xs, ys = [], []
    for primers, de_les_xarxes in dels_altres_grups(prova, i):
        for (nom, e), primer in primers.items():
            p = mp.degradat(nom, e)
            x, y = t3f.mostres(p, t3m.taula_segon(p, primer.astype(float), de_les_xarxes[(nom, e)].astype(float)))
            xs.append(x)
            ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def mostres_q(prova: str, i: int) -> tuple[pd.DataFrame, np.ndarray]:
    """Les de `mp.mostres_q(prova, SIS)`, sense les dels partits del grup `i`."""
    xs, ys = [], []
    for primers, _ in dels_altres_grups(prova, i):
        for (nom, e), primer in primers.items():
            p = mp.degradat(nom, e)
            x, y = t3i.mostres(p, t3h.taula_segon(p, primer.astype(float)))
            xs.append(x)
            ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def segon_del_grup(tasca: tuple[str, int], entrena: bool = True) -> tuple[dict[tuple[str, str], np.ndarray], np.ndarray]:
    """Les probabilitats del segon nou als partits del grup `i` de `prova`, als sis escenaris d'entrenament, i el
    prior: entrenat amb els altres sis, i aplicat amb el primer i les cinc xarxes del grup."""
    prova, i = tasca
    claus = mp.claus_del_grup(prova, i, SIS)
    cami = cau("segon-grup", prova, i)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falta el segon del grup {i} de {prova}, o és d'un altre codi")
        x, y = mostres_segon(prova, i)
        entrenat, prior = model.entrena(x, y), model.prior(y)
        del x
        primers, de_les_xarxes = mp.primer_del_grup((prova, i, SIS)), mae.xarxes_del_grup((prova, i), entrena=False)
        desat = {"prior": prior}
        for (nom, e), clau_ in claus.items():
            p = mp.degradat(nom, e)
            taula = t3m.taula_segon(p, primers[(nom, e)].astype(float), de_les_xarxes[(nom, e)].astype(float))
            desat[clau_] = model.probabilitats(entrenat, taula).astype(np.float32)
        desa(cami, **desat)
    return {qui: desat[nom] for qui, nom in claus.items()}, desat["prior"]


def q_del_grup(tasca: tuple[str, int], entrena: bool = True) -> dict[tuple[str, str], np.ndarray]:
    """Les q noves als partits del grup `i` de `prova`, als sis escenaris d'entrenament: entrenades amb els altres
    sis, i aplicades amb el primer del grup."""
    prova, i = tasca
    claus = mp.claus_del_grup(prova, i, SIS)
    cami = cau("q-grup", prova, i)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falta la q del grup {i} de {prova}, o és d'un altre codi")
        x, y = mostres_q(prova, i)
        entrenat = lgb.train(t3i.PARAMS, lgb.Dataset(x, label=y, free_raw_data=True), num_boost_round=model.RONDES)
        del x
        primers = mp.primer_del_grup((prova, i, SIS))
        desat = {}
        for (nom, e), clau_ in claus.items():
            p = mp.degradat(nom, e)
            desat[clau_] = t3i.q_de(entrenat, t3h.taula_segon(p, primers[(nom, e)].astype(float))).astype(np.float32)
        desa(cami, **desat)
    return {qui: desat[nom] for qui, nom in claus.items()}


def mostres_vores(prova: str, triat: tuple) -> tuple[np.ndarray, np.ndarray]:
    """Les del LightGBM de les vores de `prova`: els canvis de la predicció dels altres nou partits, als sis escenaris
    d'entrenament, feta amb les peces del seu grup i el decodificador `triat`, a la veritat de toc."""
    xs, ys = [], []
    for i in range(t3e.GRUPS):
        segons, prior = segon_del_grup((prova, i), entrena=False)
        qs = q_del_grup((prova, i), entrena=False)
        de_les_xarxes = mae.xarxes_del_grup((prova, i), entrena=False)
        for (nom, e), probes in segons.items():
            p = mp.degradat(nom, e)
            if pc.lluny(p.tracking).any():
                raise RuntimeError(f"{nom}, {e}: la neteja hi treu la pilota, i és un escenari d'entrenament")
            pred = mna.prediccio(log_relativa(probes.astype(float), prior), qs[(nom, e)], p.trams, triat)
            s = vo.senyals(p.tracking, p.trams, probes, de_les_xarxes[(nom, e)], qs[(nom, e)])
            toc = vt.veritat(nom)
            x, y = vo.mostres(pred, p.trams, s, vo.de_la_veritat(toc, avalua.trams_valids(replace(p, veritat=toc))))
            xs.append(x)
            ys.append(y)
    return np.concatenate(xs), np.concatenate(ys)


def de_la_neteja(nom: str, escenari: str, triat: tuple) -> tuple[np.ndarray, np.ndarray, vo.Senyals]:
    """La predicció d'A neteja d'aire (amb el decodificador `triat`), les imatges netejades i els senyals de les seves
    peces, al partit netejat."""
    de_sempre = mp.degradat(nom, escenari)
    netejades = pc.lluny(de_sempre.tracking)
    r, q_ = mcg.relativa(A_NETEJA, nom, escenari, netejades)
    pred = mna.prediccio(r, q_, de_sempre.trams, triat)
    probes, _ = mpc.segon(nom, entrena=False)
    s = vo.senyals(mpc.creible(nom, escenari).tracking, de_sempre.trams, probes[escenari],
                   mpc.xarxes_de_la_prova(nom, entrena=False)[escenari], q_)
    return pred, netejades, s


def vores(tasca: tuple[str, tuple], entrena: bool = True) -> dict[str, np.ndarray]:
    """La predicció d'A vores al partit `prova`, a tots els escenaris: el LightGBM, entrenat amb els altres nou, mou els
    canvis de la d'A neteja d'aire (amb el decodificador `triat`)."""
    prova, triat = tasca
    cami = cau("vores", prova, *triat)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les vores de {prova}, o són d'un altre codi")
        x, y = mostres_vores(prova, triat)
        entrenat = vo.entrena(x, y)
        del x
        desat = {"importancia": entrenat.feature_importance("gain")}
        for i, e in enumerate(ESCENARIS):
            pred, netejades, s = de_la_neteja(prova, e, triat)
            nova, _, _ = vo.amb_les_vores(entrenat, pred, mp.degradat(prova, e).trams, int(triat[2]), netejades, s)
            if (nova[netejades] == pm.D).any():
                raise RuntimeError(f"{prova}, {e}: {A_VORES} dona la D a una imatge netejada")
            desat[f"e{i}"] = nova
        desa(cami, **desat)
    return mpc.per_escenari(desat)


def importancia(tasca: tuple[str, tuple]) -> dict[str, float]:
    """Del LightGBM de les vores de `prova`, el guany de cada cosa que mira (de la memòria cau)."""
    prova, triat = tasca
    desat = llegeix(cau("vores", prova, *triat))
    if desat is None:
        raise RuntimeError(f"Falten les vores de {prova}, o són d'un altre codi")
    return dict(zip(vo.TRETS, map(float, desat["importancia"])))


def perfectes(ple: np.ndarray, gt: np.ndarray, trams: list[tuple[int, int]]) -> np.ndarray:
    """Les vores perfectes, com a la comprovació 2: cada canvi de la predicció (amb les abstencions omplertes), mogut al
    canvi de la veritat del mateix tipus més proper, si n'hi ha un a `vo.RADI` imatges o menys. Les possessions de la
    predicció conserven la classe, i un canvi no passa mai el d'abans."""
    de_la_veritat_ = vo.de_la_veritat(gt, trams)
    x = ple.copy()
    for a, b in trams:
        w = ple[a:b]
        dins = list(np.flatnonzero(w[1:] != w[:-1]) + 1)
        noves = [0]
        for k in dins:
            bona = vo.la_bona(vo.Canvi(a + int(k), int(w[k - 1]), int(w[k]), a, b - 1), de_la_veritat_)
            noves.append((a + int(k) if bona is None else bona) - a)
        noves = np.maximum.accumulate(np.array([*noves, len(w)]))
        for s, (de, fins) in enumerate(zip(noves[:-1], noves[1:])):
            x[a + de:a + fins] = w[[0, *dins][s]]
    return x


def comptes(pred: np.ndarray, nova: np.ndarray, trams: tuple, de_la_veritat_: dict) -> dict[str, int]:
    """Com s'han mogut els canvis de `pred` a `nova`: quants n'hi ha i quants es mouen; dels que tenen el de la
    veritat a `vo.RADI` imatges o menys, la distància abans i després, quants hi són a `A_PROP` o menys, i dels que es
    mouen, quants s'hi acosten i quants se n'allunyen."""
    abans, despres = vo.canvis(pred, trams), vo.canvis(nova, trams)
    if [(c.de, c.a, c.inici) for c in abans] != [(c.de, c.a, c.inici) for c in despres]:
        raise RuntimeError("Les vores han canviat els canvis, no només on són")
    r = dict.fromkeys(("canvis", "moguts", "amb_la_bona", "distancia_abans", "distancia_despres", "a_prop_abans",
                       "a_prop_despres", "s_acosten", "s_allunyen"), 0)
    for c, d in zip(abans, despres):
        r["canvis"] += 1
        r["moguts"] += d.t != c.t
        bona = vo.la_bona(c, de_la_veritat_)
        if bona is None:
            continue
        de, a = abs(c.t - bona), abs(d.t - bona)
        r["amb_la_bona"] += 1
        r["distancia_abans"] += de
        r["distancia_despres"] += a
        r["a_prop_abans"] += de <= A_PROP
        r["a_prop_despres"] += a <= A_PROP
        r["s_acosten"] += a < de
        r["s_allunyen"] += a > de
    return r


def informe(tasca: tuple[str, str, tuple]) -> dict[str, list[dict]]:
    """Un partit i un escenari: les files d'A vores a les dues veritats, com s'han mogut els canvis i, a la veritat de
    toc, l'spellF1 d'A neteja d'aire, amb les vores perfectes i amb les d'A vores."""
    nom, escenari, triat = tasca
    pred, netejades, _ = de_la_neteja(nom, escenari, triat)
    nova = vores((nom, triat), entrena=False)[escenari]
    if (nova[netejades] == pm.D).any():
        raise RuntimeError(f"{nom}, {escenari}: {A_VORES} dona la D a una imatge netejada")
    de_sempre = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    partits = {SEMPRE: de_sempre, TOC: replace(de_sempre, veritat=toc)}
    w, lam, d_min = triat
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}
    files = [{**comu, "metode": A_VORES, "veritat": veritat, "w": w, "lam": lam, "d_min": d_min,
              **avalua.puntua(p, nova)} for veritat, p in partits.items()]
    trams = avalua.trams_valids(partits[TOC])
    gt = toc.astype(np.int8)
    spell = lambda x: pm.spell_scores(gt, pm.fill_abstentions(x.astype(np.int8), trams), trams)["mean_f1"]  # noqa: E731
    ple = pm.fill_abstentions(pred.astype(np.int8), trams)
    sostre = [{**comu, "neteja": spell(pred), "perfectes": spell(perfectes(ple, gt, trams)), "vores": spell(nova)}]
    moguts = [{**comu, **comptes(pred, nova, de_sempre.trams, vo.de_la_veritat(toc, trams))}]
    return {"files": files, "sostre": sostre, "moguts": moguts}


def taula_sostre(t: pd.DataFrame) -> pd.DataFrame:
    """Per escenari: el sostre de la comprovació 2, el d'ara, el que treu A vores i la part del sostre."""
    g = t.groupby("escenari", sort=False)[["neteja", "perfectes", "vores"]].mean()
    sostre = g["perfectes"] - g["neteja"]
    out = pd.DataFrame({"sostre de la comprovació 2": pd.Series(COMPROVACIO_2), "sostre ara": sostre,
                        f"{A_VORES} − {A_NETEJA}": g["vores"] - g["neteja"],
                        "part del sostre": (g["vores"] - g["neteja"]) / sostre})
    out["el mateix"] = [mq._marca(abs(a - b) < 5e-5) if not np.isnan(a) else "" for a, b in
                        zip(out["sostre de la comprovació 2"], out["sostre ara"])]
    return out.reindex(ESCENARIS).rename_axis("escenari")


def taula_moguts(t: pd.DataFrame) -> pd.DataFrame:
    """Per escenari: els canvis per partit i la part que es mou; dels que tenen el de la veritat a prop, la distància
    mitjana i la part a `A_PROP` o menys, abans i després; dels que es mouen, la part que s'hi acosta i la que se
    n'allunya."""
    g = t.groupby("escenari", sort=False).sum(numeric_only=True)
    bona = g["amb_la_bona"]
    moguts_amb_la_bona = g["s_acosten"] + g["s_allunyen"]
    return pd.DataFrame({
        "canvis per partit": g["canvis"] / t["partit"].nunique(),
        "es mouen": g["moguts"] / g["canvis"],
        "amb el de la veritat a prop": bona / g["canvis"],
        "distància abans (imatges)": g["distancia_abans"] / bona,
        "distància després": g["distancia_despres"] / bona,
        f"a {A_PROP} o menys, abans": g["a_prop_abans"] / bona,
        f"a {A_PROP} o menys, després": g["a_prop_despres"] / bona,
        "dels que es mouen i el tenen a prop: s'hi acosten": g["s_acosten"] / moguts_amb_la_bona,
        "se n'allunyen": g["s_allunyen"] / moguts_amb_la_bona,
    }).reindex(ESCENARIS).rename_axis("escenari")


def _md(t: pd.DataFrame, decimals: int = 3) -> str:
    """La taula en Markdown: els números amb `decimals` decimals (els que falten, buits), i el text tal qual."""
    valor = lambda x: x if isinstance(x, str) else "" if pd.isna(x) else f"{x:.{decimals}f}"  # noqa: E731
    return "\n".join(["| " + " | ".join([t.index.name, *t.columns]) + " |", "|---" * (len(t.columns) + 1) + "|",
                      *("| " + " | ".join([str(i), *map(valor, fila)]) + " |" for i, fila in t.iterrows())])


def _regla(millor: dict[str, bool]) -> list[str]:
    es = all(millor.values())
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | "
            f"{mq._marca(millor['quarts'])} |",
            f"| «{mp.PARTIT}» | la diferència no és negativa | {mq._marca(millor['partit'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {mq._marca(millor['altres'])} |",
            "", f"**{A_VORES} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_VORES if es else A_NETEJA}.", ""]


def markdown(metodes: pd.DataFrame, triades: dict, c: pd.DataFrame, passa: dict[str, bool], c_neteja: pd.DataFrame,
             millor: dict[str, bool], per_font: dict[tuple[str, str], pd.DataFrame], sostre: pd.DataFrame,
             moguts: pd.DataFrame) -> str:
    linies = ["# Banc obert · Les vores dels canvis, afinades (T3ae)", "",
              "Generat amb `uv run python -I -m banc.model_vores`. Dades obertes: 7 partits de DFL (IDSSE, CC BY 4.0) i",
              "els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el criteri:",
              "`docs/pla-tocs.md`, «T3ae», i la capçalera de `banc/model_vores.py`. Es puntua a la veritat de toc.", "",
              f"**{XARXES_TOC}** i **{A_EQUIPS}** són els de la T3v, **{A_CREIBLE}**, el de la T3w, i **{A_NETEJA}**,",
              "el de la T3ac, amb les peces de la memòria cau (✓ comprovat: donen l'spellF1 d'aquells bancs, i els",
              f"decodificadors triats són els seus). **{A_VORES}** és {A_NETEJA}, amb el mateix decodificador, i després",
              "un LightGBM que mou cada canvi fins a 0,5 s. Aprèn amb les prediccions dels altres nou partits fetes",
              "sense el partit que es prova (un segon i una q nous per a cada grup). ✓ Comprovat a cada partit i",
              "escenari: no dona mai la D a una imatge netejada.", "",
              f"## {A_VORES} contra {XARXES_TOC} (spellF1): el criteri", "",
              *t3b._taula(c, A_VORES, XARXES_TOC), "", *mt._criteris(passa),
              f"## {A_VORES} contra {A_NETEJA} (spellF1)", "", *t3i._comparacio(c_neteja, A_VORES, A_NETEJA), ""]
    if not all(passa.values()):
        linies += ["## No passa: és el millor fins ara?", "",
                   f"La regla de la D-50, escrita abans, contra {A_NETEJA}:", "", *_regla(millor)]
    for (font, contra), taula in per_font.items():
        linies += [f"## {A_VORES} contra {contra}, només els partits de {font}", "",
                   *t3i._comparacio(taula, A_VORES, contra), ""]
    linies += ["## El sostre de les vores perfectes", "",
               "A la veritat de toc, la mitjana dels deu partits: el sostre (cada canvi d'A neteja d'aire, al de la",
               f"veritat del mateix tipus més proper, a {vo.RADI} imatges o menys), el que en treu {A_VORES} i la part.",
               "", _md(taula_sostre(sostre), 4), "",
               "## Com es mouen els canvis", "",
               f"Els canvis d'{A_NETEJA} i on els deixa {A_VORES}. «A prop»: amb un canvi de la veritat del mateix",
               f"tipus a {vo.RADI} imatges o menys (a la veritat de toc).", "",
               _md(taula_moguts(moguts)), "",
               "## L'spellF1 de cada mètode (mitjana dels deu partits)", "",
               *mt._mitjanes(metodes, [XARXES_TOC, A_EQUIPS, A_NETEJA, A_VORES]), "## Els decodificadors triats", "",
               f"{A_NETEJA} i {A_VORES} fan servir, a cada partit, el d'{A_EQUIPS}.", "", *mq._triades(triades), ""]
    return "\n".join(linies)


def clau() -> str:
    """El que fa les peces d'aquí: les d'A pilota creïble i d'A equips sencers, les vores i això."""
    h = hashlib.sha256((mpc.CLAU + mae.CLAU + mp.CLAU + vt.CLAU + repr((SIS, ESCENARIS, model.RONDES, model.PAS,
                                                                        t3i.PARAMS))).encode())
    h.update(Path(vo.__file__).read_bytes())
    for funcio in (dels_altres_grups, mostres_segon, mostres_q, segon_del_grup, q_del_grup, mostres_vores,
                   de_la_neteja, vores, mna.prediccio, mna.amb_la_d_impossible, mcg.relativa):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + mna.clau_dels_resultats()).encode())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_vores as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        return list(feina.map(getattr(aquest, fes), tasques))


def fes(tasca: tuple[str, tuple]) -> str:
    """Una peça (`segon_del_grup`, `q_del_grup` o `vores`) a la memòria cau; sense tornar-ne res."""
    peca, qui = tasca
    globals()[peca](qui)
    return peca


def entrena_les_peces(processos: int, triades_equips: dict[str, tuple]) -> None:
    """El segon i la q de cada grup, i després les vores de cada partit."""
    from banc import model_vores as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        grups = [(peca, (nom, i)) for nom in fonts.NOMS for i in range(t3e.GRUPS)
                 for peca in ("segon_del_grup", "q_del_grup")]
        for k, ((peca, (nom, i)), _) in enumerate(zip(grups, feina.map(aquest.fes, grups)), start=1):
            print(f"· {k}/{len(grups)}: {'el segon' if peca == 'segon_del_grup' else 'la q'} del grup {i} de {nom}",
                  flush=True)
        partits = [("vores", (nom, triades_equips[nom])) for nom in fonts.NOMS]
        for k, ((_, (nom, _)), _) in enumerate(zip(partits, feina.map(aquest.fes, partits)), start=1):
            print(f"· {k}/{len(partits)}: les vores de {nom}", flush=True)


def escriu(contingut: dict, md: str) -> None:
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-vores.json").write_text(json.dumps(contingut, indent=1, default=float, allow_nan=False))
    (DIR_RESULTATS / "model-vores.md").write_text(md)
    print(md)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=3, help="models alhora")
    args = ap.parse_args()
    for nom in fonts.NOMS:
        for metode in (XARXES, A_EQUIPS, A_CREIBLE):
            mpc.de_qui(metode, nom)
        mpc.primer(nom, entrena=False)
        mpc.xarxes_de_la_prova(nom, entrena=False)
        vt.veritat(nom)
    metodes, triades = mcg.comprova_les_d_abans(args.processos)
    print(f"· {XARXES} i {A_EQUIPS} donen el del banc de la T3v, {A_CREIBLE}, el de la T3w, i {A_NETEJA}, el de "
          "la T3ac", flush=True)
    entrena_les_peces(args.processos_models, triades[A_EQUIPS])
    tasques = [(nom, e, triades[A_EQUIPS][nom]) for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    trossos = en_paral_lel("informe", tasques, args.processos)
    files, sostre, moguts = (pd.DataFrame([f for tros in trossos for f in tros[clau_]])
                             for clau_ in ("files", "sostre", "moguts"))
    print(f"· {A_VORES}: mai la D a les imatges netejades", flush=True)
    metodes = pd.concat([metodes, files], ignore_index=True)
    c = mt.comparacio(metodes, A_VORES, XARXES_TOC, TOC, amb_criteri=True)
    c_neteja = mt.comparacio(metodes, A_VORES, A_NETEJA, TOC, amb_criteri=False)
    passa, millor = mt.compleix(c), mq.millor_fins_ara(c_neteja)
    per_font = {(font, contra): mt.comparacio(metodes[metodes["font"] == font], A_VORES, contra, TOC,
                                              amb_criteri=False)
                for font in FONTS for contra in (XARXES_TOC, A_NETEJA)}
    contingut = {"clau": clau_dels_resultats(), "passa": passa, "millor_fins_ara": millor,
                 "comparacio": t3.registres(c), "contra_a_neteja_d_aire": t3.registres(c_neteja), "triades": triades,
                 "files": t3.registres(files),
                 "per_font": {f"{font} · {contra}": t3.registres(t) for (font, contra), t in per_font.items()},
                 "sostre": t3.registres(sostre), "moguts": t3.registres(moguts),
                 "importancia": {nom: importancia((nom, triades[A_EQUIPS][nom])) for nom in fonts.NOMS}}
    escriu(contingut, markdown(metodes, triades, c, passa, c_neteja, millor, per_font, sostre, moguts))


if __name__ == "__main__":
    main()
