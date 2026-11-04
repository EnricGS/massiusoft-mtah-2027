"""La pilota morta i les fases a sobre del camp girat (T3am del pla per tocs, `docs/pla-tocs.md`, «T3am»; D-75).

    cd codi && uv run python -I -m banc.model_girat_fases [--processos 12]

Les capes d'A fases, en el mateix ordre, amb A camp girat de la T3ad a sota en lloc d'A neteja d'aire (`base`):
- **A camp girat** tal qual, de la memòria cau, amb la q d'A pilota creïble, la D impossible on la neteja ha tret la
  pilota i el decodificador que va triar cada partit a la T3ad;
- **A girat amb pilota morta:** les etiquetes simulades de la T3ag sumen a la D, com a la T3ah, amb la seva graella
  (`graella_pm`), triada com a la T3ah (`model_pilota_morta.tria`);
- **A girat amb fases:** a sobre del punt triat a la capa d'abans, les fases simulades de la T3ak, com a la T3ak, amb
  la seva graella (`graella_fs`), triada com a la T3ak (`model_fases.tria`).
No s'entrena res.

1. **En començar:** A xarxes i A equips sencers, amb la memòria cau, han de donar el banc de la T3v, A pilota creïble,
   el de la T3w, i A neteja d'aire, el de la T3ac; els bancs de la T3ad, la T3ah i la T3ak han de ser d'aquest codi; i
   A camp girat, de la memòria cau i amb el decodificador de cada partit, ha de donar l'spellF1 del banc de la T3ad
   (`comprova_la_t3ad`). Si no, s'atura.
2. **Les graelles,** una rere l'altra, als quatre ×¼ de cada partit, amb els nivells bo, mitjà i dolent i les llavors
   de triar. Cap punt no hi ha de donar la D a una imatge netejada.
3. **Es prova** als onze escenaris amb els quatre nivells i les llavors de provar (`informe`). Sense etiquetes ni fases,
   A girat amb fases ha de ser exactament A camp girat, i sense fases, exactament A girat amb pilota morta
   (`comprova_sense_res`). Si no, s'atura.
4. **El criteri** del pla, el de la T3ak; el millor fins ara, contra A fases. Només per saber-ho: per font; amb el
   nivell bo; contra A fases i contra A camp girat a cada nivell; les causes de `banc/on_falla.py` per a A fases i A
   girat amb fases, i els punts triats a cada partit.

Escriu `resultats/model-girat-fases.json` i `.md`. Tot són dades obertes. Els mòduls d'abans no es toquen.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

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
from banc import model_fases as mfs
from banc import model_fases_amplia as mfa
from banc import model_neteja_aire as mna
from banc import model_pilota_creible as mpc
from banc import model_pilota_morta as mpm
from banc import model_pilotes_aturades as mpa
from banc import model_vores as mv
from banc import on_falla as of
from banc import smart_tagging_simulat as sts
from banc import veritat_toc as vt
from cadena import fases as fs
from cadena import pilota_creible as pc
from cadena import pilota_morta as pmo
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ESCENARIS, QUARTS_T3, PARTIT, CURTS = mfs.ESCENARIS, mfs.QUARTS_T3, mfs.PARTIT, mfs.CURTS
XARXES, XARXES_TOC, A_EQUIPS, A_CREIBLE, A_NETEJA = mfs.XARXES, mfs.XARXES_TOC, mfs.A_EQUIPS, mfs.A_CREIBLE, mfs.A_NETEJA
A_PM, A_FS, A_GIRAT = mfs.A_PM, mfs.A_FS, mcg.A_GIRAT
A_GPM = "A girat amb pilota morta"
A_GFS = "A girat amb fases"
SEMPRE, TOC, NIVELLS, NIVELLS_TRIA, MITJA = mfs.SEMPRE, mfs.TOC, mfs.NIVELLS, mfs.NIVELLS_TRIA, mfs.MITJA
TRIA, PROVA = mfs.TRIA, mfs.PROVA
DIR_RESULTATS = mfs.DIR_RESULTATS
GRAELLA_PM, GRAELLA_FS, ZERO = pmo.GRAELLA, mfs.GRAELLA, mfs.ZERO


def base(sota: str, nom: str, escenari: str) -> tuple:
    """El partit degradat, la relativa de la capa de sota (sense la D impossible), la seva q i les imatges netejades:
    d'A camp girat, o d'A neteja d'aire (`model_etiquetes_decodificador.base`)."""
    if sota == A_NETEJA:
        return med.base(nom, escenari)
    if sota != A_GIRAT:
        raise ValueError(f"No hi ha cap base per a {sota}")
    de_sempre = mp.degradat(nom, escenari)
    probes, prior, q_ = mcg.de_qui(A_GIRAT, nom)
    return de_sempre, log_relativa(probes[escenari].astype(float), prior), q_[escenari], pc.lluny(de_sempre.tracking)


def girat(tasca: tuple[str, str, tuple]) -> list[dict]:
    """A camp girat d'un partit i un escenari, amb el seu decodificador (`triat`), a les dues veritats."""
    nom, escenari, triat = tasca
    de_sempre, r, q_, netejades = base(A_GIRAT, nom, escenari)
    pred = mna.prediccio(mna.amb_la_d_impossible(r, netejades), q_, de_sempre.trams, triat)
    return [{"partit": nom, "escenari": escenari, "veritat": veritat, "spell_f1": avalua.puntua(p, pred)["spell_f1"]}
            for veritat, p in ((SEMPRE, de_sempre), (TOC, replace(de_sempre, veritat=vt.veritat(nom))))]


def comprova_la_t3ad(aqui: pd.DataFrame, t3ad: pd.DataFrame, triades: dict[str, tuple]) -> None:
    """A camp girat d'aquí, amb el decodificador de cada partit, ha de donar l'spellF1 del banc de la T3ad."""
    claus = ["partit", "escenari", "veritat"]
    triat = [(w, lam, d) == tuple(triades[nom])
             for nom, w, lam, d in t3ad[["partit", "w", "lam", "d_min"]].itertuples(index=False)]
    b = t3ad[triat].set_index(claus)["spell_f1"].sort_index()
    a = aqui.set_index(claus)["spell_f1"].sort_index()
    if not a.index.equals(b.index) or not np.allclose(a.to_numpy(float), b.to_numpy(float), atol=1e-12, rtol=0):
        raise RuntimeError(f"{A_GIRAT} d'aquí no dona l'spellF1 del banc de la T3ad")


def graella_pm(tasca: tuple[str, str, str, tuple]) -> list[dict]:
    """Com `model_pilota_morta.graella`, a sobre de la capa `sota`: un partit i un ×¼, cada punt de la graella de la
    T3ah amb els nivells de `NIVELLS_TRIA` i les llavors de triar, a la veritat de toc. Els fixos, un cop (`sense`
    buit); els per tipus, amb les medianes sense el partit i sense cadascun dels altres (`sense`)."""
    sota, nom, escenari, triat = tasca
    de_sempre, r, q_, netejades = base(sota, nom, escenari)
    p = replace(de_sempre, veritat=vt.veritat(nom))
    sense = {altre: mpm.medianes_sense(nom, altre) for altre in fonts.NOMS if altre != nom}
    files = []
    for nivell in NIVELLS_TRIA:
        dades = (nom, escenari, nivell, de_sempre, r, q_, netejades, p,
                 mpa.etiquetes_de(nom, escenari, nivell, TRIA), triat)
        fetes: dict[tuple, dict] = {}
        for a in GRAELLA_PM:
            amb = [("", mpm.medianes_sense(nom))] if a.forma == pmo.FIXA else list(sense.items())
            files += [{"partit": nom, "font": de_sempre.font, "escenari": escenari, "nivell": nivell, "sense": altre,
                       **a._asdict(), **mpm._puntua(fetes, dades, a, m)} for altre, m in amb]
    return files


def graella_fs(tasca: tuple[str, str, str, pmo.Abans, tuple]) -> list[dict]:
    """Com `model_fases.graella`, a sobre de la capa `sota` amb la pilota morta `a_pm`: un partit i un ×¼, cada punt de
    la graella de la T3ak amb els nivells de `NIVELLS_TRIA` i les llavors de triar, a la veritat de toc."""
    sota, nom, escenari, a_pm, triat = tasca
    b = base(sota, nom, escenari)
    de_sempre, r, _, netejades = b
    p = replace(de_sempre, veritat=vt.veritat(nom))
    files = []
    for nivell in NIVELLS_TRIA:
        relativa = mfs.relativa_pm(nom, escenari, nivell, TRIA, a_pm, de_sempre, r, netejades)
        fases = fsm.fases_de(nom, escenari, nivell, TRIA)
        fetes: dict[mfs.Suma, dict] = {}
        for s in GRAELLA_FS:
            if mfs.efectiva(s) not in fetes:
                pred = mfs._decodifica(nom, escenari, nivell, A_GFS, relativa, fases, s, b, triat)
                fetes[mfs.efectiva(s)] = {k: v for k, v in avalua.puntua(p, pred).items()
                                          if k in ("spell_f1", "macro_f1")}
            files.append({"partit": nom, "font": de_sempre.font, "escenari": escenari, "nivell": nivell,
                          **s._asdict(), **fetes[mfs.efectiva(s)]})
    return files


def comprova_sense_res(preds: dict[tuple[str, str], np.ndarray], nom: str, escenari: str) -> None:
    """Sense etiquetes ni fases (el nivell cap), A girat amb pilota morta i A girat amb fases han de ser exactament A
    camp girat."""
    if not np.array_equal(preds[(A_GPM, "cap")], preds[(A_GIRAT, "cap")]):
        raise RuntimeError(f"{nom}, {escenari}: sense etiquetes, {A_GPM} no dona {A_GIRAT}")
    if not np.array_equal(preds[(A_GFS, "cap")], preds[(A_GPM, "cap")]):
        raise RuntimeError(f"{nom}, {escenari}: sense fases, {A_GFS} no dona {A_GPM}")


def informe(tasca: tuple[str, str, pmo.Abans, mfs.Suma, tuple]) -> dict[str, list[dict]]:
    """Un partit i un escenari: les files d'A camp girat, A girat amb pilota morta i A girat amb fases a cada nivell
    (amb les llavors de provar), a les dues veritats; i amb el nivell mitjà, les causes d'A girat amb fases."""
    nom, escenari, a, s, triat = tasca
    b = base(A_GIRAT, nom, escenari)
    de_sempre, r, q_, netejades = b
    toc = vt.veritat(nom)
    partits = {SEMPRE: de_sempre, TOC: replace(de_sempre, veritat=toc)}
    sola = mna.prediccio(mna.amb_la_d_impossible(r, netejades), q_, de_sempre.trams, triat)
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}
    preds, quantes = {}, []
    for nivell in NIVELLS:
        relativa = mfs.relativa_pm(nom, escenari, nivell, PROVA, a, de_sempre, r, netejades)
        fases = fsm.fases_de(nom, escenari, nivell, PROVA)
        preds[(A_GIRAT, nivell)] = sola
        for metode, suma in ((A_GPM, ZERO), (A_GFS, s)):
            preds[(metode, nivell)] = mfs._decodifica(nom, escenari, nivell, metode, relativa, fases, suma, b, triat)
        dins = fs.estones(fases, len(toc), de_sempre.trams, s.marge_s)
        quantes.append({**comu, "nivell": nivell, "fases": len(fases),
                        "part_dins": float((dins[:, pm.H] != dins[:, pm.A]).mean())})
    comprova_sense_res(preds, nom, escenari)
    files = [{**comu, "metode": metode, "nivell": nivell, "veritat": veritat, **avalua.puntua(p, preds[(metode, nivell)])}
             for metode in (A_GIRAT, A_GPM, A_GFS) for nivell in NIVELLS for veritat, p in partits.items()]
    vista = ~np.isnan(de_sempre.tracking.pilota[:, 0])
    c, so = mfs.causes_de(toc.astype(np.int8), preds[(A_GFS, MITJA)], avalua.trams_valids(partits[TOC]), vista)
    return {"files": files, "causes": [{**comu, "metode": A_GFS, "causa": k, "n": n} for k, n in c.items()],
            "sobrants": [{**comu, "metode": A_GFS, "on": k, "n": n} for k, n in so.items()], "fases": quantes}


def de_la_t3ad() -> dict:
    desat = json.loads((DIR_RESULTATS / "model-camp-girat.json").read_text())
    if desat["clau"] != mcg.clau_dels_resultats():
        raise RuntimeError("El banc de la T3ad no és d'aquest codi")
    return desat


def de_fs(t: pd.DataFrame) -> pd.DataFrame:
    return t[t["metode"] == A_FS]


def taula_causes(causes: pd.DataFrame, sobren: pd.DataFrame, escenaris: tuple[str, ...]) -> pd.DataFrame:
    """Com `model_fases.taula_causes`, per a A pilota morta, A fases i A girat amb fases."""
    c = causes[causes["escenari"].isin(escenaris)].groupby(["metode", "causa"])["n"].sum().unstack("metode")
    totes = c.sum()
    t = (c / totes).reindex(of.CAUSES).fillna(0.0)
    s = sobren[sobren["escenari"].isin(escenaris)].groupby(["metode", "on"])["n"].sum().unstack("metode")
    t.loc["sobren a l'altre equip, per cada 100"] = 100 * s.reindex(["a l'altre equip"]).fillna(0.0).iloc[0] / totes
    return t[[A_PM, A_FS, A_GFS]].rename_axis("causa")


def comparacions(metodes: pd.DataFrame, tots: pd.DataFrame) -> dict:
    """Les comparacions del pla: el criteri, la segona part, el millor fins ara i les de saber-ho."""
    nomes = tots[tots["metode"] == A_GFS]
    c = mt.comparacio(mpa.de_nivell(metodes, nomes, MITJA), A_GFS, XARXES_TOC, TOC, amb_criteri=True)
    c_neteja = {n: mt.comparacio(mpa.de_nivell(metodes, nomes, n), A_GFS, A_NETEJA, TOC, amb_criteri=False)
                for n in NIVELLS}
    c_fs, c_girat = ({n: mt.comparacio(tots[tots["nivell"] == n].drop(columns="nivell"), A_GFS, contra, TOC,
                                       amb_criteri=False) for n in NIVELLS} for contra in (A_FS, A_GIRAT))
    mitja = mpa.de_nivell(metodes, tots, MITJA)
    altres = {(f"{A_GFS} contra {contra}, nivell {MITJA}, només els partits de {font}", contra):
              mt.comparacio(mitja[mitja["font"] == font], A_GFS, contra, TOC, amb_criteri=False)
              for font in mpc.FONTS for contra in (XARXES_TOC, A_FS)}
    altres[(f"{A_GFS} contra {XARXES_TOC}, nivell bo", XARXES_TOC)] = mt.comparacio(
        mpa.de_nivell(metodes, nomes, "bo"), A_GFS, XARXES_TOC, TOC, amb_criteri=False)
    return {"c": c, "passa": mt.compleix(c), "robust": mpa.aguanta(c_neteja), "c_neteja": c_neteja, "c_fs": c_fs,
            "c_girat": c_girat, "millor": mq.millor_fins_ara(c_fs[MITJA]), "altres": altres, "mitja": mitja}


def _regla(millor: dict[str, bool], robust: dict[str, bool]) -> list[str]:
    es = all(millor.values()) and all(robust.values())
    m = mpa._marca
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | {m(millor['quarts'])} |",
            f"| «{PARTIT}» | la diferència no és negativa | {m(millor['partit'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {m(millor['altres'])} |",
            f"| Dolent i cap | la segona part del criteri | {m(all(robust.values()))} |", "",
            f"**{A_GFS} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_GFS if es else A_FS}.", ""]


def _punts(r: dict) -> list[str]:
    def pm_(a: pmo.Abans) -> str:
        return f"{a.beta_d:g}, {a.forma}, {a.durada:g}, {a.marge_s:g}"

    def fs_(s: mfs.Suma) -> str:
        return f"{s.gamma:g}, {s.delta:g}, {s.marge_s:g}"

    vores = mpm.a_la_vora(r["triats_pm"])
    return ["A cada partit, amb els altres nou, als quatre ×¼ i a la mitjana dels nivells bo, mitjà i dolent; i el que",
            "hi van triar la T3ah i la T3ak. La pilota morta: `beta_d`, la forma, la durada i `marge_s`; les fases:",
            "`gamma`, `delta` i `marge_s`.", "",
            "| partit | pilota morta | a la T3ah | fases | a la T3ak |", "|---|---|---|---|---|",
            *(f"| {nom} | {pm_(a)} | {pm_(r['triats_t3ah'][nom])} | {fs_(r['triats_fs'][nom])} | "
              f"{fs_(r['triats_t3ak'][nom])} |" for nom, a in r["triats_pm"].items()), "",
            f"**La pilota morta, a la vora de la graella:** {', '.join(vores)}." if vores else
            "La pilota morta: cap partit no tria a la vora de la graella.",
            f"Les fases: {mfs._vores(r['triats_fs'])[0]}", ""]


def markdown(r: dict) -> str:
    passa_tot = all(r["passa"].values()) and all(r["robust"].values())
    linies = ["# Banc obert · La pilota morta i les fases a sobre del camp girat (T3am)", "",
              "Generat amb `uv run python -I -m banc.model_girat_fases`. Dades obertes: 7 partits de DFL (IDSSE, CC BY",
              "4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el criteri:",
              "`docs/pla-tocs.md`, «T3am», i la capçalera de `banc/model_girat_fases.py`. Es puntua a la veritat de toc.",
              "", f"**{XARXES_TOC}** i **{A_EQUIPS}** són els de la T3v, **{A_CREIBLE}**, el de la T3w, **{A_NETEJA}**,",
              f"el de la T3ac, **{A_GIRAT}**, el de la T3ad, i **{A_FS}**, el de la T3ak (✓ comprovat). **{A_GFS}** és",
              f"{A_GIRAT} amb la pilota morta i les fases a sobre, amb els punts triats de nou. ✓ Comprovat: no dona mai",
              f"la D a una imatge netejada; {A_GIRAT} d'aquí dona l'spellF1 de la T3ad; sense etiquetes ni fases, {A_GFS}",
              f"és exactament {A_GIRAT}; i sense fases, exactament {A_GPM}.", "",
              f"## Amb el nivell {MITJA}: {A_GFS} contra {XARXES_TOC} (spellF1), el criteri", "",
              *t3b._taula(r["c"], A_GFS, XARXES_TOC), "", *mt._criteris(r["passa"]),
              f"## Amb els nivells dolent i cap: {A_GFS} contra {A_NETEJA}, la segona part del criteri", "",
              *mpa._robustesa(r["c_neteja"], r["robust"]), "",
              f"**{A_GFS} {'passa' if passa_tot else 'no passa'} el criteri sencer.**", ""]
    for contra, clau in ((A_FS, "c_fs"), (A_GIRAT, "c_girat")):
        for nivell in NIVELLS:
            linies += [f"## Amb el nivell {nivell}: {A_GFS} contra {contra} (spellF1)", "",
                       *t3i._comparacio(r[clau][nivell], A_GFS, contra), ""]
    if not passa_tot:
        linies += ["## No passa: és el millor fins ara?", "",
                   f"La regla de la D-50, escrita abans, contra {A_FS} amb el nivell {MITJA}, i la mateixa segona part",
                   "del criteri:", "", *_regla(r["millor"], r["robust"])]
    for (titol, contra), taula in r["altres"].items():
        linies += [f"## {titol}", "", *t3i._comparacio(taula, A_GFS, contra), ""]
    linies += ["## On falla, abans i després", "",
               f"Amb el nivell {MITJA}, les causes de `banc/on_falla.py`: la part de les possessions de la veritat de",
               "cada causa, i les predites que sobren a l'altre equip per cada 100 possessions de la veritat.", ""]
    for titol, escenaris in ((CURTS, (CURTS,)), ("els quatre ×¼ junts", QUARTS_T3), ("net", ("net",))):
        linies += [f"**{titol}**", "", mv._md(taula_causes(r["causes"], r["sobrants"], escenaris), 3), ""]
    linies += ["## Les fases simulades", "",
               f"A {CURTS}, amb les llavors de provar, la mitjana dels deu partits: quantes fases, i la part de les",
               "imatges on se'n resta (dins d'una fase d'un sol equip, sense el marge triat).", "",
               mv._md(mfs.taula_fases(r["fases"]), 3), "", "## Els punts triats", "", *_punts(r),
               f"## L'spellF1 de cada mètode (mitjana dels deu partits, nivell {MITJA})", "",
               *mt._mitjanes(r["mitja"], [XARXES_TOC, A_NETEJA, A_GIRAT, A_FS, A_GPM, A_GFS]), "## Els decodificadors", "",
               f"{A_GPM} i {A_GFS} fan servir, a cada partit, el d'{A_GIRAT}; {A_FS}, el d'{A_EQUIPS}.", "",
               *mq._triades(r["triades"]), ""]
    return "\n".join(linies)


def clau_dels_resultats() -> str:
    h = hashlib.sha256((mcg.clau_dels_resultats() + mfs.clau_dels_resultats()).encode())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_girat_fases as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        return list(feina.map(getattr(aquest, fes), tasques))


def files_de(fes: str, tasques: list, processos: int) -> pd.DataFrame:
    return pd.DataFrame([f for tros in en_paral_lel(fes, tasques, processos) for f in tros])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    args = ap.parse_args()
    for nom in fonts.NOMS:
        for metode in (XARXES, A_EQUIPS, A_CREIBLE, A_GIRAT):
            mcg.de_qui(metode, nom)
        mpc.q(nom, entrena=False)
        vt.veritat(nom)
        sts.represes(nom)
    metodes, triades = mcg.comprova_les_d_abans(args.processos)
    t3ad, a_t3ah, t3ak = de_la_t3ad(), mfs.de_la_t3ah(), mfa.de_la_t3ak()
    del_girat = {nom: tuple(t) for nom, t in t3ad["triades"][A_GIRAT].items()}
    comprova_la_t3ad(files_de("girat", [(nom, e, del_girat[nom]) for nom, e in itertools.product(fonts.NOMS, ESCENARIS)],
                              args.processos), pd.DataFrame(t3ad["files"]), del_girat)
    print(f"· {XARXES} i {A_EQUIPS} donen el del banc de la T3v, {A_CREIBLE}, el de la T3w, i {A_NETEJA}, el de "
          f"la T3ac; els bancs de la T3ad, la T3ah i la T3ak són d'aquest codi; {A_GIRAT} dona el de la T3ad", flush=True)
    quarts = list(itertools.product(fonts.NOMS, QUARTS_T3))
    files_pm = files_de("graella_pm", [(A_GIRAT, nom, e, del_girat[nom]) for nom, e in quarts], args.processos)
    triats_pm = {nom: mpm.tria(files_pm, nom) for nom in fonts.NOMS}
    print(f"· {A_GPM}: la graella, mai la D a les imatges netejades", flush=True)
    files_fs = files_de("graella_fs", [(A_GIRAT, nom, e, triats_pm[nom], del_girat[nom]) for nom, e in quarts],
                        args.processos)
    triats_fs = {nom: mfs.tria(files_fs, nom) for nom in fonts.NOMS}
    print(f"· {A_GFS}: la graella, mai la D a les imatges netejades", flush=True)
    trossos = en_paral_lel("informe", [(nom, e, triats_pm[nom], triats_fs[nom], del_girat[nom])
                                       for nom, e in itertools.product(fonts.NOMS, ESCENARIS)], args.processos)
    nous, causes, sobren, quantes = (pd.DataFrame([f for tros in trossos for f in tros[k]])
                                     for k in ("files", "causes", "sobrants", "fases"))
    print(f"· {A_GFS}: sense etiquetes ni fases, exactament {A_GIRAT}; sense fases, {A_GPM}", flush=True)
    files_t3ak = pd.DataFrame(t3ak["files"])
    tots = pd.concat([nous, de_fs(files_t3ak).drop(columns=[*mfs.PARAMETRES, "neteja"])], ignore_index=True)
    d_abans = pd.DataFrame(t3ak["causes"]), pd.DataFrame(t3ak["sobrants"])
    r = {**comparacions(metodes, tots), "causes": pd.concat([causes, d_abans[0]]),
         "sobrants": pd.concat([sobren, d_abans[1]]), "fases": quantes, "triats_pm": triats_pm, "triats_fs": triats_fs,
         "triats_t3ah": a_t3ah,
         "triats_t3ak": {nom: mfs.Suma(**s) for nom, s in t3ak["triats"].items()},
         "triades": {A_GIRAT: del_girat, A_EQUIPS: triades[A_EQUIPS]}}
    contingut = {"clau": clau_dels_resultats(), "passa": r["passa"], "aguanta": r["robust"],
                 "millor_fins_ara": r["millor"], "comparacio": t3.registres(r["c"]),
                 "contra_a_neteja_d_aire": {n: t3.registres(t) for n, t in r["c_neteja"].items()},
                 "contra_a_fases": {n: t3.registres(t) for n, t in r["c_fs"].items()},
                 "contra_a_camp_girat": {n: t3.registres(t) for n, t in r["c_girat"].items()},
                 "triats_pilota_morta": {nom: a._asdict() for nom, a in triats_pm.items()},
                 "triats_fases": {nom: s._asdict() for nom, s in triats_fs.items()}, "triades": r["triades"],
                 "files": t3.registres(nous), "graella_pilota_morta": t3.registres(files_pm),
                 "graella_fases": t3.registres(files_fs),
                 "altres": {titol: t3.registres(t) for (titol, _), t in r["altres"].items()},
                 "causes": t3.registres(causes), "sobrants": t3.registres(sobren), "fases": t3.registres(quantes)}
    mpa.escriu("model-girat-fases", contingut, markdown(r))


if __name__ == "__main__":
    main()
