"""Les fases amb equip del Smart Tagging, al decodificador, a sobre d'A pilota morta (T3ak del pla per tocs,
`docs/pla-tocs.md`, «T3ak»; D-73).

    cd codi && uv run python -I -m banc.model_fases [--processos 12]

A pilota morta (T3ah) tal qual, amb els paràmetres i el decodificador que hi va triar cada partit. A sobre, abans de
decodificar, les fases simulades de l'equip que té la pilota (`banc/fases_simulades.py`): dins de cada una, deixant
`marge_s` a cada vora, a l'altre equip s'hi resta `gamma` i a la D, `delta` (`cadena/fases.py`). Després, la D
impossible on la neteja ha tret la pilota, i el decodificador d'A equips sencers. No s'entrena res.

1. **En començar:** A xarxes i A equips sencers, amb la memòria cau, han de donar el banc de la T3v, A pilota creïble,
   el de la T3w, i A neteja d'aire, el de la T3ac; i el banc de la T3ah ha de ser d'aquest codi. Si no, s'atura.
2. **La graella** (`GRAELLA`) als quatre ×¼ de cada partit, amb els nivells bo, mitjà i dolent i les llavors de triar,
   les de les pilotes aturades i les de les fases. Cap punt no hi ha de donar la D a una imatge netejada.
3. **La tria** de cada partit, amb els altres nou: el punt amb més spellF1 de mitjana als quatre ×¼ i als tres nivells,
   a la veritat de toc (`tria`).
4. **Es prova** als onze escenaris amb els quatre nivells i les llavors de provar. A pilota morta d'aquí ha de donar
   l'spellF1 del banc de la T3ah; sense etiquetes, exactament A neteja d'aire; i sense fases, A fases ha de ser
   exactament A pilota morta. Si no, s'atura.
5. **El criteri** del pla, el de la T3aj; el millor fins ara, contra A pilota morta. Només per saber-ho: per font; amb
   el nivell bo; contra A pilota morta a cada nivell; les causes de `banc/on_falla.py` per a tots dos, i el punt triat
   a cada partit.

Escriu `resultats/model-fases.json` i `.md`. Tot són dades obertes. Els mòduls d'abans no es toquen.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd

from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import fases_simulades as fsm
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
from banc import veritat_toc as vt
from cadena import fases as fs
from cadena import pilota_morta as pmo
from possessio.oficial import possession_metrics as pm

ESCENARIS, QUARTS_T3, PARTIT = med.ESCENARIS, med.QUARTS_T3, med.PARTIT
XARXES, XARXES_TOC, A_EQUIPS, A_CREIBLE, A_NETEJA = med.XARXES, med.XARXES_TOC, med.A_EQUIPS, med.A_CREIBLE, med.A_NETEJA
A_PM = mpm.A_PM
A_FS = "A fases"
SEMPRE, TOC = med.SEMPRE, med.TOC
NIVELLS, NIVELLS_TRIA, MITJA = med.NIVELLS, med.NIVELLS_TRIA, med.MITJA
TRIA, PROVA = med.TRIA, med.PROVA                   # les llavors de la T3ag
CURTS = "curts ×¼"
DIR_RESULTATS = t3.DIR_RESULTATS


class Suma(NamedTuple):
    gamma: float            # per imatge, a l'altre equip
    delta: float            # per imatge, a la D
    marge_s: float          # a cada vora de la fase


GRAELLA = tuple(Suma(*v) for v in itertools.product((0.0, 0.05, 0.1, 0.25, 0.5, 1.0), (0.0, 0.25, 1.0),
                                                     (0.0, 1.0, 2.0)))
ZERO = Suma(0.0, 0.0, 0.0)
PARAMETRES = list(Suma._fields)


def efectiva(s: Suma) -> Suma:
    """Els punts sense res a restar són tots el mateix."""
    return ZERO if not (s.gamma or s.delta) else s


def relativa_amb(relativa: np.ndarray, fases: tuple[fs.Fase, ...], trams: tuple[tuple[int, int, int], ...], s: Suma,
                 netejades: np.ndarray) -> np.ndarray:
    """La relativa d'A pilota morta amb les fases restades (`fs.resta`), i la D impossible a `netejades`."""
    return mna.amb_la_d_impossible(fs.resta(relativa, fases, trams, s.gamma, s.delta, s.marge_s), netejades)


def relativa_pm(nom: str, escenari: str, nivell: str, per: str, a_pm: pmo.Abans, de_sempre, r: np.ndarray,
                netejades: np.ndarray) -> np.ndarray:
    """La probabilitat relativa d'A pilota morta, com al banc de la T3ah: amb les etiquetes i la D impossible."""
    etiquetes = mpa.etiquetes_de(nom, escenari, nivell, per)
    return mna.amb_la_d_impossible(pmo.amb_les_etiquetes(r, etiquetes, de_sempre.trams, a_pm, mpm.medianes_sense(nom)),
                                   netejades)


def _decodifica(nom: str, escenari: str, nivell: str, metode: str, relativa: np.ndarray, fases: tuple, s: Suma,
                base: tuple, triat: tuple) -> np.ndarray:
    de_sempre, _, q_, netejades = base
    pred = mna.prediccio(relativa_amb(relativa, fases, de_sempre.trams, s, netejades), q_, de_sempre.trams, triat)
    if (pred[netejades] == pm.D).any():
        raise RuntimeError(f"{nom}, {escenari}, {nivell}, {s}: {metode} dona la D a una imatge netejada")
    return pred


def graella(tasca: tuple[str, str, pmo.Abans, tuple]) -> list[dict]:
    """Un partit i un ×¼, amb A pilota morta (`a_pm`) i el decodificador d'A equips sencers (`triat`): cada punt de la
    graella amb els nivells de `NIVELLS_TRIA` i les llavors de triar, a la veritat de toc."""
    nom, escenari, a_pm, triat = tasca
    base = med.base(nom, escenari)
    de_sempre, r, _, netejades = base
    p = replace(de_sempre, veritat=vt.veritat(nom))
    files = []
    for nivell in NIVELLS_TRIA:
        relativa = relativa_pm(nom, escenari, nivell, TRIA, a_pm, de_sempre, r, netejades)
        fases = fsm.fases_de(nom, escenari, nivell, TRIA)
        fetes: dict[Suma, dict] = {}
        for s in GRAELLA:
            if efectiva(s) not in fetes:
                pred = _decodifica(nom, escenari, nivell, A_FS, relativa, fases, s, base, triat)
                fetes[efectiva(s)] = {k: v for k, v in avalua.puntua(p, pred).items() if k in ("spell_f1", "macro_f1")}
            files.append({"partit": nom, "font": de_sempre.font, "escenari": escenari, "nivell": nivell,
                          **s._asdict(), **fetes[efectiva(s)]})
    return files


def tria(files: pd.DataFrame, prova: str) -> Suma:
    """El punt per a `prova`, amb els altres nou: el de més spellF1 de mitjana als quatre ×¼ i als nivells de les files
    (desempata el macroF1)."""
    return Suma(*(float(v) for v in mp.millor(files[files["partit"] != prova], PARAMETRES, QUARTS_T3)))


def causes_de(toc: np.ndarray, pred: np.ndarray, trams: list[tuple[int, int]], vista: np.ndarray) -> tuple:
    """Quantes possessions de la veritat hi ha de cada causa de `on_falla` i quantes predites sobren on."""
    omplerta = pm.fill_abstentions(pred.astype(np.int8), trams)
    return (Counter(f["causa"] for f in of.causes(toc, omplerta, trams, vista)),
            Counter(f["on"] for f in of.sobrants(toc, omplerta, trams)))


def informe(tasca: tuple[str, str, pmo.Abans, Suma, tuple]) -> dict[str, list[dict]]:
    """Un partit i un escenari: les files d'A pilota morta i d'A fases a cada nivell (amb les llavors de provar), a les
    dues veritats, amb l'spellF1 d'A neteja d'aire a la de toc; i amb el nivell mitjà, les causes de cadascú. S'atura si
    dona la D a una imatge netejada, si sense etiquetes A pilota morta no dona exactament A neteja d'aire, o si sense
    fases A fases no dona exactament A pilota morta."""
    nom, escenari, a_pm, s, triat = tasca
    base = med.base(nom, escenari)
    de_sempre, r, q_, netejades = base
    toc = vt.veritat(nom)
    partits = {SEMPRE: de_sempre, TOC: replace(de_sempre, veritat=toc)}
    trams = avalua.trams_valids(partits[TOC])
    neteja_pred = mna.prediccio(mna.amb_la_d_impossible(r, netejades), q_, de_sempre.trams, triat)
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}
    preds, quantes = {}, []
    for nivell in NIVELLS:
        relativa = relativa_pm(nom, escenari, nivell, PROVA, a_pm, de_sempre, r, netejades)
        fases = fsm.fases_de(nom, escenari, nivell, PROVA)
        for metode, suma in ((A_PM, ZERO), (A_FS, s)):
            preds[(metode, nivell)] = _decodifica(nom, escenari, nivell, metode, relativa, fases, suma, base, triat)
        dins = fs.estones(fases, len(toc), de_sempre.trams, s.marge_s)
        quantes.append({**comu, "nivell": nivell, "fases": len(fases),
                        "part_dins": float((dins[:, pm.H] != dins[:, pm.A]).mean())})
    if not np.array_equal(preds[(A_PM, "cap")], neteja_pred):
        raise RuntimeError(f"{nom}, {escenari}: sense etiquetes, {A_PM} no dona {A_NETEJA}")
    if not np.array_equal(preds[(A_FS, "cap")], preds[(A_PM, "cap")]):
        raise RuntimeError(f"{nom}, {escenari}: sense fases, {A_FS} no dona {A_PM}")
    neteja = avalua.puntua(partits[TOC], neteja_pred)["spell_f1"]
    files = [{**comu, "metode": metode, "nivell": nivell, "veritat": veritat, **(s if metode == A_FS else ZERO)._asdict(),
              "neteja": neteja, **avalua.puntua(p, preds[(metode, nivell)])}
             for metode in (A_PM, A_FS) for nivell in NIVELLS for veritat, p in partits.items()]
    vista = ~np.isnan(de_sempre.tracking.pilota[:, 0])
    causes, sobren = [], []
    for metode in (A_PM, A_FS):
        c, so = causes_de(toc.astype(np.int8), preds[(metode, MITJA)], trams, vista)
        causes += [{**comu, "metode": metode, "causa": k, "n": n} for k, n in c.items()]
        sobren += [{**comu, "metode": metode, "on": k, "n": n} for k, n in so.items()]
    return {"files": files, "causes": causes, "sobrants": sobren, "fases": quantes}


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
    return t[[A_PM, A_FS]].rename_axis("causa")


def taula_fases(quantes: pd.DataFrame) -> pd.DataFrame:
    t = quantes[quantes["escenari"] == CURTS].groupby("nivell")[["fases", "part_dins"]].mean()
    return t.reindex(list(NIVELLS)).rename_axis("nivell")


def _regla(millor: dict[str, bool], robust: dict[str, bool]) -> list[str]:
    es = all(millor.values()) and all(robust.values())
    m = mpa._marca
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | {m(millor['quarts'])} |",
            f"| «{PARTIT}» | la diferència no és negativa | {m(millor['partit'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {m(millor['altres'])} |",
            f"| Dolent i cap | la segona part del criteri | {m(all(robust.values()))} |", "",
            f"**{A_FS} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_FS if es else A_PM}.", ""]


def _vores(triats: dict[str, Suma]) -> list[str]:
    vores = [f"{camp} = {v:g}" for camp in PARAMETRES
             for v in sorted({getattr(s, camp) for s in triats.values()})
             if v in (min(getattr(g, camp) for g in GRAELLA), max(getattr(g, camp) for g in GRAELLA))
             and not (camp == "marge_s" and all(not (s.gamma or s.delta) for s in triats.values()))]
    return [f"**A la vora de la graella:** {', '.join(vores)}." if vores else "Cap partit no tria a la vora de la graella."]


def markdown(r: dict) -> str:
    passa_tot = all(r["passa"].values()) and all(r["robust"].values())
    linies = ["# Banc obert · Les fases amb equip del Smart Tagging, al decodificador (T3ak)", "",
              "Generat amb `uv run python -I -m banc.model_fases`. Dades obertes: 7 partits de DFL (IDSSE, CC BY 4.0)",
              "i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el criteri:",
              "`docs/pla-tocs.md`, «T3ak», i la capçalera de `banc/model_fases.py`. Es puntua a la veritat de toc.", "",
              f"**{XARXES_TOC}** i **{A_EQUIPS}** són els de la T3v, **{A_CREIBLE}**, el de la T3w, **{A_NETEJA}**, el",
              f"de la T3ac, i **{A_PM}**, el de la T3ah (✓ comprovat). **{A_FS}** és {A_PM} amb, dins de les fases",
              "simulades de l'equip que té la pilota, l'altre equip i la D restats. ✓ Comprovat: no dona mai la D a una",
              f"imatge netejada; {A_PM} d'aquí dona l'spellF1 de la T3ah; sense etiquetes, exactament {A_NETEJA}; i",
              f"sense fases, {A_FS} és exactament {A_PM}.", "",
              f"## Amb el nivell {MITJA}: {A_FS} contra {XARXES_TOC} (spellF1), el criteri", "",
              *t3b._taula(r["c"], A_FS, XARXES_TOC), "", *mt._criteris(r["passa"]),
              f"## Amb els nivells dolent i cap: {A_FS} contra {A_NETEJA}, la segona part del criteri", "",
              *mpa._robustesa(r["c_neteja"], r["robust"]), "",
              f"**{A_FS} {'passa' if passa_tot else 'no passa'} el criteri sencer.**", ""]
    for nivell in NIVELLS:
        linies += [f"## Amb el nivell {nivell}: {A_FS} contra {A_PM} (spellF1)", "",
                   *t3i._comparacio(r["c_pm"][nivell], A_FS, A_PM), ""]
    if not passa_tot:
        linies += ["## No passa: és el millor fins ara?", "",
                   f"La regla de la D-50, escrita abans, contra {A_PM} amb el nivell {MITJA}, i la mateixa segona part",
                   "del criteri:", "", *_regla(r["millor"], r["robust"])]
    for (titol, contra), taula in r["altres"].items():
        linies += [f"## {titol}", "", *t3i._comparacio(taula, A_FS, contra), ""]
    linies += ["## On falla, abans i després", "",
               f"Amb el nivell {MITJA}, les causes de `banc/on_falla.py`: la part de les possessions de la veritat de",
               "cada causa, i les predites que sobren a l'altre equip per cada 100 possessions de la veritat.", ""]
    for titol, escenaris in ((CURTS, (CURTS,)), ("els quatre ×¼ junts", QUARTS_T3), ("net", ("net",))):
        linies += [f"**{titol}**", "", mv._md(taula_causes(r["causes"], r["sobrants"], escenaris), 3), ""]
    linies += ["## Les fases simulades", "",
               f"A {CURTS}, amb les llavors de provar, la mitjana dels deu partits: quantes fases, i la part de les",
               "imatges on se'n resta (dins d'una fase d'un sol equip, sense el marge triat).", "",
               mv._md(taula_fases(r["fases"]), 3), "",
               "## El punt triat", "",
               "A cada partit, amb els altres nou, als quatre ×¼ i a la mitjana dels nivells bo, mitjà i dolent.", "",
               "| partit | gamma | delta | marge_s |", "|---|---|---|---|",
               *(f"| {nom} | {s.gamma:g} | {s.delta:g} | {s.marge_s:g} |" for nom, s in r["triats"].items()), "",
               *_vores(r["triats"]), "",
               f"## L'spellF1 de cada mètode (mitjana dels deu partits, nivell {MITJA})", "",
               *mt._mitjanes(r["mitja"], [XARXES_TOC, A_EQUIPS, A_NETEJA, A_PM, A_FS]), "## Els decodificadors", "",
               f"{A_NETEJA}, {A_PM} i {A_FS} fan servir, a cada partit, el d'{A_EQUIPS}.", "",
               *mq._triades(r["triades"]), ""]
    return "\n".join(linies)


def clau_dels_resultats() -> str:
    h = hashlib.sha256(mpm.clau_dels_resultats().encode())
    for modul in (fs, fsm, sts):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_fases as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        return list(feina.map(getattr(aquest, fes), tasques))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
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
    files_graella = pd.DataFrame([f for tros in en_paral_lel(
        "graella", [(nom, e, a_pm[nom], de_la_neteja[nom]) for nom, e in itertools.product(fonts.NOMS, QUARTS_T3)],
        args.processos) for f in tros])
    print(f"· {A_FS}: la graella, mai la D a les imatges netejades", flush=True)
    triats = {nom: tria(files_graella, nom) for nom in fonts.NOMS}
    tasques = [(nom, e, a_pm[nom], triats[nom], de_la_neteja[nom]) for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    trossos = en_paral_lel("informe", tasques, args.processos)
    nous, causes, sobren, quantes = (pd.DataFrame([f for tros in trossos for f in tros[k]])
                                     for k in ("files", "causes", "sobrants", "fases"))
    mre.comprova_la_t3ah(nous)
    nous_fs = nous[nous["metode"] == A_FS]
    med.comprova_la_neteja(nous_fs, metodes)
    print(f"· {A_FS}: {A_PM} dona l'spellF1 de la T3ah; sense etiquetes, {A_NETEJA}; sense fases, {A_FS} és "
          f"exactament {A_PM}", flush=True)
    sense = nous.drop(columns=[*PARAMETRES, "neteja"])
    nomes_fs = sense[sense["metode"] == A_FS]
    c = mt.comparacio(mpa.de_nivell(metodes, nomes_fs, MITJA), A_FS, XARXES_TOC, TOC, amb_criteri=True)
    c_neteja = {n: mt.comparacio(mpa.de_nivell(metodes, nomes_fs, n), A_FS, A_NETEJA, TOC, amb_criteri=False)
                for n in NIVELLS}
    c_pm = {n: mt.comparacio(sense[sense["nivell"] == n].drop(columns="nivell"), A_FS, A_PM, TOC, amb_criteri=False)
            for n in NIVELLS}
    passa, robust, millor = mt.compleix(c), mpa.aguanta(c_neteja), mq.millor_fins_ara(c_pm[MITJA])
    mitja = mpa.de_nivell(metodes, sense, MITJA)
    altres = {(f"{A_FS} contra {contra}, nivell {MITJA}, només els partits de {font}", contra):
              mt.comparacio(mitja[mitja["font"] == font], A_FS, contra, TOC, amb_criteri=False)
              for font in mpc.FONTS for contra in (XARXES_TOC, A_PM)}
    altres[(f"{A_FS} contra {XARXES_TOC}, nivell bo", XARXES_TOC)] = mt.comparacio(
        mpa.de_nivell(metodes, nomes_fs, "bo"), A_FS, XARXES_TOC, TOC, amb_criteri=False)
    r = {"c": c, "passa": passa, "robust": robust, "c_neteja": c_neteja, "c_pm": c_pm, "millor": millor,
         "altres": altres, "causes": causes, "sobrants": sobren, "fases": quantes, "triats": triats, "mitja": mitja,
         "triades": {A_EQUIPS: de_la_neteja}}
    contingut = {"clau": clau_dels_resultats(), "passa": passa, "aguanta": robust, "millor_fins_ara": millor,
                 "comparacio": t3.registres(c),
                 "contra_a_neteja_d_aire": {n: t3.registres(t) for n, t in c_neteja.items()},
                 "contra_a_pilota_morta": {n: t3.registres(t) for n, t in c_pm.items()},
                 "triats": {nom: s._asdict() for nom, s in triats.items()},
                 "triades": {A_EQUIPS: de_la_neteja}, "files": t3.registres(nous),
                 "graella": t3.registres(files_graella),
                 "altres": {titol: t3.registres(t) for (titol, _), t in altres.items()},
                 "causes": t3.registres(causes), "sobrants": t3.registres(sobren), "fases": t3.registres(quantes)}
    mpa.escriu("model-fases", contingut, markdown(r))


if __name__ == "__main__":
    main()
