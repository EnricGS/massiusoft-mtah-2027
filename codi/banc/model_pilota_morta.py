"""La pilota morta d'abans de la represa, més llarga i més forta (T3ah del pla per tocs, `docs/pla-tocs.md`, «T3ah»;
D-70).

    cd codi && uv run python -I -m banc.model_pilota_morta [--processos 12]

A neteja d'aire (T3ac) tal qual, amb les seves peces de la memòria cau i el decodificador d'A equips sencers a cada
partit. L'única diferència: abans de decodificar, les etiquetes simulades (`banc/smart_tagging_simulat.py`, les
mateixes de la T3ag) sumen a la D (`cadena/pilota_morta.py`), i després s'hi posa la D impossible on la neteja ha tret
la pilota. No s'entrena res.

1. **En començar:** A xarxes i A equips sencers, amb la memòria cau, han de donar el banc de la T3v, A pilota creïble,
   el de la T3w, i A neteja d'aire, amb el decodificador d'A equips sencers, el de la T3ac. Si no, s'atura.
2. **Les medianes per tipus** de la pilota morta abans de les represes, a la veritat de toc, mai d'un partit que es
   prova (`medianes_sense`).
3. **La graella** (`pmo.GRAELLA`, 96 punts) als quatre ×¼ de cada partit, amb els nivells bo, mitjà i dolent i les
   llavors d'aprendre. Els punts per tipus es fan, per a cada altre partit, amb les medianes sense tots dos (`sense`),
   perquè la tria d'un partit no en miri mai la veritat. Cap punt no hi ha de donar la D a una imatge netejada, i els
   punts de la T3ag (`beta_d` = 1, fixa, 10 s) han de donar el mateix que a la graella de la T3ag. Si no, s'atura.
4. **La tria** de cada partit, amb els altres nou: el punt amb més spellF1 de mitjana als quatre ×¼ i als tres
   nivells, a la veritat de toc (`tria`).
5. **Es prova** als onze escenaris amb els quatre nivells i les llavors de provar, amb les medianes sense el partit.
   Sense etiquetes ha de donar exactament A neteja d'aire, i A neteja d'aire, l'spellF1 de la T3ac. Si no, s'atura.
6. **El criteri** del pla, el de la T3ag. Només per saber-ho: per font; amb el nivell bo; contra la T3ag a cada nivell;
   a 5 s o menys de les represes, on encerta cadascú; la part del sostre de la T3af que se n'aprofita; les medianes i
   els paràmetres triats.

Escriu `resultats/model-pilota-morta.json` i `.md`. Tot són dades obertes. Els mòduls d'abans no es toquen.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import itertools
import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

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
from banc import model_pilotes_aturades as mpa
from banc import model_vores as mv
from banc import smart_tagging_simulat as sts
from banc import sostre_sense_pilota as ssp
from banc import veritat_toc as vt
from cadena import pilota_morta as pmo
from cadena.smart_tagging import TIPUS
from possessio.oficial import possession_metrics as pm

ESCENARIS, QUARTS_T3, PARTIT = med.ESCENARIS, med.QUARTS_T3, med.PARTIT
XARXES, XARXES_TOC, A_EQUIPS, A_CREIBLE, A_NETEJA = med.XARXES, med.XARXES_TOC, med.A_EQUIPS, med.A_CREIBLE, med.A_NETEJA
A_ED = med.A_ED
A_PM = "A pilota morta"
SEMPRE, TOC = med.SEMPRE, med.TOC
NIVELLS, NIVELLS_TRIA, MITJA = med.NIVELLS, med.NIVELLS_TRIA, med.MITJA
TRIA, PROVA = med.TRIA, med.PROVA                   # les etiquetes de la T3ag
PARAMS = list(pmo.Abans._fields)
DE_LA_T3AG = 1.0, 10.0                              # beta_d i la durada fixa del punt que hi van triar
DIR_RESULTATS = t3.DIR_RESULTATS


@functools.cache
def mortes(nom: str) -> tuple[tuple[str, float], ...]:
    """Les durades de la pilota morta abans de cada represa d'un partit, a la veritat de toc."""
    return pmo.durades(vt.veritat(nom), fonts.partit(nom).trams,
                       ((r.imatge, r.tipus) for r in sts.represes(nom).represes))


def medianes_sense(*fora: str) -> dict[str, float]:
    """Les medianes per tipus dels partits del banc que no són a `fora`."""
    return pmo.medianes(d for nom in fonts.NOMS if nom not in fora for d in mortes(nom))


def relativa_amb(r: np.ndarray, etiquetes: tuple, trams: tuple[tuple[int, int, int], ...], a: pmo.Abans,
                 medianes: dict[str, float], netejades: np.ndarray) -> np.ndarray:
    """La relativa d'A pilota creïble amb el que hi sumen les etiquetes, i després la D impossible a `netejades`."""
    return mna.amb_la_d_impossible(pmo.amb_les_etiquetes(r, etiquetes, trams, a, medianes), netejades)


def _puntua(fetes: dict, tasca: tuple, a: pmo.Abans, medianes: dict[str, float]) -> dict:
    """La puntuació d'un punt a la veritat de toc, un sol cop per clau efectiva."""
    nom, escenari, nivell, de_sempre, r, q_, netejades, p, etiquetes, triat = tasca
    clau_ = pmo.efectiva(a, medianes)
    if clau_ not in fetes:
        pred = mna.prediccio(relativa_amb(r, etiquetes, de_sempre.trams, a, medianes, netejades), q_, de_sempre.trams,
                             triat)
        if (pred[netejades] == pm.D).any():
            raise RuntimeError(f"{nom}, {escenari}, {nivell}, {a}: {A_PM} dona la D a una imatge netejada")
        fetes[clau_] = {k: v for k, v in avalua.puntua(p, pred).items() if k in ("spell_f1", "macro_f1")}
    return fetes[clau_]


def graella(tasca: tuple[str, str, tuple]) -> list[dict]:
    """Un partit i un ×¼, amb el decodificador d'A neteja d'aire (`triat`): cada punt de la graella amb els nivells de
    `NIVELLS_TRIA` i les llavors d'aprendre, a la veritat de toc. Els fixos, un cop (`sense` buit); els per tipus, amb
    les medianes sense el partit i sense cadascun dels altres (`sense`)."""
    nom, escenari, triat = tasca
    de_sempre, r, q_, netejades = med.base(nom, escenari)
    p = replace(de_sempre, veritat=vt.veritat(nom))
    sense = {altre: medianes_sense(nom, altre) for altre in fonts.NOMS if altre != nom}
    files = []
    for nivell in NIVELLS_TRIA:
        dades = (nom, escenari, nivell, de_sempre, r, q_, netejades, p,
                 mpa.etiquetes_de(nom, escenari, nivell, TRIA), triat)
        fetes: dict[tuple, dict] = {}
        for a in pmo.GRAELLA:
            amb = [("", medianes_sense(nom))] if a.forma == pmo.FIXA else list(sense.items())
            files += [{"partit": nom, "font": de_sempre.font, "escenari": escenari, "nivell": nivell, "sense": altre,
                       **a._asdict(), **_puntua(fetes, dades, a, m)} for altre, m in amb]
    return files


def comprova_la_t3ag(files: pd.DataFrame) -> None:
    """Els punts fixos de 10 s amb `beta_d` = 1, a cada marge, han de donar el mateix que els seus a la graella de la
    T3ag (sense res a l'equip), a cada partit, ×¼ i nivell."""
    t3ag = pd.DataFrame(json.loads((DIR_RESULTATS / "model-etiquetes-decodificador.json").read_text())["graella"])
    t3ag = t3ag[(t3ag["beta_d"] == DE_LA_T3AG[0]) & (t3ag["abans_s"] == DE_LA_T3AG[1]) & (t3ag["beta_e"] == 0)
                & (t3ag["despres_s"] == 2)]
    aqui = files[(files["forma"] == pmo.FIXA) & (files["beta_d"] == DE_LA_T3AG[0])
                 & (files["durada"] == DE_LA_T3AG[1])]
    claus = ["partit", "escenari", "nivell", "marge_s"]
    junts = aqui.merge(t3ag[[*claus, "spell_f1"]], on=claus, suffixes=("", " de la T3ag"), validate="one_to_one")
    if len(junts) != len(fonts.NOMS) * len(QUARTS_T3) * len(NIVELLS_TRIA) * 3 or not np.allclose(
            junts["spell_f1"], junts["spell_f1 de la T3ag"], atol=1e-12, rtol=0):
        raise RuntimeError("Els punts de la T3ag no donen el mateix que a la graella de la T3ag")


def tria(files: pd.DataFrame, prova: str) -> pmo.Abans:
    """El punt de la graella per a `prova`, amb els altres nou i les medianes sense `prova`: el de més spellF1 de
    mitjana als quatre ×¼ i als nivells de les files (desempata el macroF1)."""
    mira = files[(files["partit"] != prova) & files["sense"].isin(["", prova])]
    millor = mp.millor(mira, PARAMS, QUARTS_T3)
    return next(a for a in pmo.GRAELLA if tuple(a) == tuple(millor))


def informe(tasca: tuple[str, str, pmo.Abans, tuple]) -> dict[str, list[dict]]:
    """Un partit i un escenari: les files d'A pilota morta a cada nivell (amb les llavors de provar i les medianes
    sense el partit), a les dues veritats, amb l'spellF1 d'A neteja d'aire a la de toc; i a prop de les represes, on
    encerta cadascú. S'atura si dona la D a una imatge netejada, o si sense etiquetes no dona exactament A neteja
    d'aire."""
    nom, escenari, a, triat = tasca
    de_sempre, r, q_, netejades = med.base(nom, escenari)
    medianes = medianes_sense(nom)
    toc = vt.veritat(nom)
    partits = {SEMPRE: de_sempre, TOC: replace(de_sempre, veritat=toc)}
    trams = avalua.trams_valids(partits[TOC])
    prop = mpa.a_prop(sts.represes(nom).represes, len(toc), de_sempre.trams) & ssp.dins(len(toc), trams)
    preds = {(A_NETEJA, ""): mna.prediccio(mna.amb_la_d_impossible(r, netejades), q_, de_sempre.trams, triat)}
    for nivell in NIVELLS:
        etiquetes = mpa.etiquetes_de(nom, escenari, nivell, PROVA)
        preds[(A_PM, nivell)] = mna.prediccio(relativa_amb(r, etiquetes, de_sempre.trams, a, medianes, netejades), q_,
                                              de_sempre.trams, triat)
        if (preds[(A_PM, nivell)][netejades] == pm.D).any():
            raise RuntimeError(f"{nom}, {escenari}, {nivell}: {A_PM} dona la D a una imatge netejada")
    if not np.array_equal(preds[(A_PM, "cap")], preds[(A_NETEJA, "")]):
        raise RuntimeError(f"{nom}, {escenari}: sense etiquetes, {A_PM} no dona {A_NETEJA}")
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}
    neteja = avalua.puntua(partits[TOC], preds[(A_NETEJA, "")])["spell_f1"]
    files = [{**comu, "metode": A_PM, "nivell": nivell, "veritat": veritat, **a._asdict(), "neteja": neteja,
              **avalua.puntua(p, preds[(A_PM, nivell)])} for nivell in NIVELLS for veritat, p in partits.items()]
    encerts = [{**comu, "metode": metode, "nivell": nivell, "n": int(prop.sum()),
                "encerts": int((pm.fill_abstentions(pred.astype(np.int8), trams)[prop] == toc[prop]).sum())}
               for (metode, nivell), pred in preds.items()]
    return {"files": files, "encerts": encerts}


def contra_la_t3ag(nous: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """A cada nivell, A pilota morta contra A etiquetes al decodificador, amb les files de la T3ag."""
    t3ag = pd.DataFrame(json.loads((DIR_RESULTATS / "model-etiquetes-decodificador.json").read_text())["files"])
    columnes = ["partit", "font", "escenari", "metode", "nivell", "veritat", "spell_f1", "macro_f1"]
    junts = pd.concat([t3ag[columnes], nous[columnes]], ignore_index=True)
    return {n: mt.comparacio(junts[junts["nivell"] == n].drop(columns="nivell"), A_PM, A_ED, TOC, amb_criteri=False)
            for n in NIVELLS}


def taula_medianes(per_partit: dict[str, dict[str, float]]) -> pd.DataFrame:
    return pd.DataFrame(per_partit).T[list(TIPUS)].rename_axis("partit")


def taula_triats(triats: dict[str, pmo.Abans]) -> pd.DataFrame:
    return pd.DataFrame({nom: a._asdict() for nom, a in triats.items()}).T.rename_axis("partit")


def a_la_vora(triats: dict[str, pmo.Abans]) -> list[str]:
    """Els paràmetres que algun partit tria al valor més baix o al més alt de la graella (la durada, dins de la seva
    forma)."""
    vora = []
    for f in ("beta_d", "marge_s"):
        valors = {getattr(a, f) for a in pmo.GRAELLA}
        vora += [f"`{f}` = {v:g}" for v in (min(valors), max(valors)) if any(getattr(a, f) == v for a in triats.values())]
    for forma, durades in pmo.DURADES.items():
        vora += [f"`durada` = {v:g} ({forma})" for v in (min(durades), max(durades))
                 if any(a.forma == forma and a.durada == v for a in triats.values())]
    return vora


def taula_encerts(t: pd.DataFrame) -> pd.DataFrame:
    g = t.groupby(["escenari", "metode", "nivell"], sort=False)[["n", "encerts"]].sum()
    part = (g["encerts"] / g["n"]).unstack(["metode", "nivell"])
    part.columns = [A_NETEJA if m == A_NETEJA else f"{A_PM}, {n}" for m, n in part.columns]
    return part[[A_NETEJA, *(f"{A_PM}, {n}" for n in NIVELLS)]].reindex(ESCENARIS).rename_axis("escenari")


def _regla(millor: dict[str, bool], robust: dict[str, bool]) -> list[str]:
    es = all(millor.values()) and all(robust.values())
    m = mpa._marca
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | {m(millor['quarts'])} |",
            f"| «{PARTIT}» | la diferència no és negativa | {m(millor['partit'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {m(millor['altres'])} |",
            f"| Dolent i cap | la segona part del criteri | {m(all(robust.values()))} |", "",
            f"**{A_PM} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_PM if es else A_NETEJA}.", ""]


def markdown(mitja: pd.DataFrame, triades: dict, triats: dict[str, pmo.Abans], medianes: dict[str, dict[str, float]],
             c: pd.DataFrame, passa: dict[str, bool], robust: dict[str, bool], c_neteja: dict[str, pd.DataFrame],
             millor: dict[str, bool], c_t3ag: dict[str, pd.DataFrame], altres: dict[tuple[str, str], pd.DataFrame],
             encerts: pd.DataFrame, sostre: pd.DataFrame) -> str:
    passa_tot = all(passa.values()) and all(robust.values())
    vora = a_la_vora(triats)
    linies = ["# Banc obert · La pilota morta d'abans de la represa, més llarga i més forta (T3ah)", "",
              "Generat amb `uv run python -I -m banc.model_pilota_morta`. Dades obertes: 7 partits de DFL (IDSSE,",
              "CC BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3ah», i la capçalera de `banc/model_pilota_morta.py`. Es puntua a la",
              "veritat de toc.", "",
              f"**{XARXES_TOC}** i **{A_EQUIPS}** són els de la T3v, **{A_CREIBLE}**, el de la T3w, i **{A_NETEJA}**,",
              "el de la T3ac, amb les peces de la memòria cau (✓ comprovat). **A pilota morta** és A neteja d'aire amb",
              "el seu decodificador, i abans de decodificar, el que les etiquetes simulades sumen a la D. ✓ Comprovat:",
              "no dona mai la D a una imatge netejada, sense etiquetes dona exactament A neteja d'aire, i els punts de",
              "la T3ag donen el mateix que a la graella de la T3ag.", "",
              f"## Amb el nivell {MITJA}: {A_PM} contra {XARXES_TOC} (spellF1), el criteri", "",
              *t3b._taula(c, A_PM, XARXES_TOC), "", *mt._criteris(passa),
              f"## Amb els nivells dolent i cap: {A_PM} contra {A_NETEJA}, la segona part del criteri", "",
              *mpa._robustesa(c_neteja, robust), "",
              f"**{A_PM} {'passa' if passa_tot else 'no passa'} el criteri sencer.**", ""]
    for nivell in NIVELLS:
        linies += [f"## Amb el nivell {nivell}: {A_PM} contra {A_NETEJA} (spellF1)", "",
                   *t3i._comparacio(c_neteja[nivell], A_PM, A_NETEJA), ""]
    if not passa_tot:
        linies += ["## No passa: és el millor fins ara?", "",
                   f"La regla de la D-50, escrita abans, contra {A_NETEJA} amb el nivell {MITJA}, i la mateixa",
                   "segona part del criteri:", "", *_regla(millor, robust)]
    for nivell in NIVELLS[:-1]:
        linies += [f"## Amb el nivell {nivell}: {A_PM} contra {A_ED}, la T3ag (spellF1)", "",
                   *t3i._comparacio(c_t3ag[nivell], A_PM, A_ED), ""]
    for (titol, contra), taula in altres.items():
        linies += [f"## {titol}", "", *t3i._comparacio(taula, A_PM, contra), ""]
    linies += ["## La part del sostre de la T3af que se n'aprofita", "",
               "A la veritat de toc, la mitjana dels deu partits: el sostre de la T3af menys A neteja d'aire, el que en",
               "treu A pilota morta, i la part.", "", t3p.md(sostre), "",
               "## A 5 s o menys de cada represa", "",
               "La part de les imatges vàlides a 5 s o menys d'una represa on la predicció (amb les abstencions",
               "omplertes) és la veritat de toc.", "", t3p.md(taula_encerts(encerts)), "",
               "## Les medianes per tipus", "",
               "A cada partit, la mediana dels segons de pilota morta seguida abans de les represes de cada tipus, a la",
               "veritat de toc dels altres nou.", "", mv._md(taula_medianes(medianes), 1), "",
               "## Els paràmetres triats", "",
               "A cada partit, amb els altres nou, als quatre ×¼ i a la mitjana dels nivells bo, mitjà i dolent.", "",
               mv._md(taula_triats(triats), 2), "",
               ("**A la vora de la graella** (algun partit tria el valor més baix o el més alt): " + ", ".join(vora)
                + "." if vora else "Cap paràmetre no es tria a la vora de la graella."), "",
               f"## L'spellF1 de cada mètode (mitjana dels deu partits, nivell {MITJA})", "",
               *mt._mitjanes(mitja, [XARXES_TOC, A_EQUIPS, A_NETEJA, A_PM]), "## Els decodificadors", "",
               f"{A_NETEJA} i {A_PM} fan servir, a cada partit, el d'{A_EQUIPS}.", "", *mq._triades(triades), ""]
    return "\n".join(linies)


def clau_dels_resultats() -> str:
    h = hashlib.sha256(med.clau_dels_resultats().encode())
    for modul in (pmo, med):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_pilota_morta as aquest

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
    print(f"· {XARXES} i {A_EQUIPS} donen el del banc de la T3v, {A_CREIBLE}, el de la T3w, i {A_NETEJA}, el de "
          "la T3ac", flush=True)
    de_la_neteja = triades[A_EQUIPS]
    files_graella = pd.DataFrame([f for tros in en_paral_lel("graella", [(nom, e, de_la_neteja[nom]) for nom, e in
                                                                         itertools.product(fonts.NOMS, QUARTS_T3)],
                                                             args.processos) for f in tros])
    comprova_la_t3ag(files_graella)
    print(f"· {A_PM}: la graella, mai la D a les imatges netejades, i els punts de la T3ag, com a la T3ag", flush=True)
    triats = {nom: tria(files_graella, nom) for nom in fonts.NOMS}
    medianes = {nom: medianes_sense(nom) for nom in fonts.NOMS}
    tasques = [(nom, e, triats[nom], de_la_neteja[nom]) for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    trossos = en_paral_lel("informe", tasques, args.processos)
    nous, encerts = (pd.DataFrame([f for tros in trossos for f in tros[k]]) for k in ("files", "encerts"))
    med.comprova_la_neteja(nous, metodes)
    print(f"· {A_PM}: sense etiquetes, exactament {A_NETEJA}, amb l'spellF1 de la T3ac", flush=True)
    sense = nous.drop(columns=[*PARAMS, "neteja"])
    c = mt.comparacio(mpa.de_nivell(metodes, sense, MITJA), A_PM, XARXES_TOC, TOC, amb_criteri=True)
    c_neteja = {n: mt.comparacio(mpa.de_nivell(metodes, sense, n), A_PM, A_NETEJA, TOC, amb_criteri=False)
                for n in NIVELLS}
    passa, robust, millor = mt.compleix(c), mpa.aguanta(c_neteja), mq.millor_fins_ara(c_neteja[MITJA])
    c_t3ag = contra_la_t3ag(nous)
    mitja = mpa.de_nivell(metodes, sense, MITJA)
    altres = {(f"{A_PM} contra {contra}, nivell {MITJA}, només els partits de {font}", contra):
              mt.comparacio(mitja[mitja["font"] == font], A_PM, contra, TOC, amb_criteri=False)
              for font in mpc.FONTS for contra in (XARXES_TOC, A_NETEJA)}
    altres[(f"{A_PM} contra {XARXES_TOC}, nivell bo", XARXES_TOC)] = mt.comparacio(
        mpa.de_nivell(metodes, sense, "bo"), A_PM, XARXES_TOC, TOC, amb_criteri=False)
    sostre = med.part_del_sostre(nous)
    contingut = {"clau": clau_dels_resultats(), "passa": passa, "aguanta": robust, "millor_fins_ara": millor,
                 "comparacio": t3.registres(c),
                 "contra_a_neteja_d_aire": {n: t3.registres(t) for n, t in c_neteja.items()},
                 "contra_la_t3ag": {n: t3.registres(t) for n, t in c_t3ag.items()},
                 "triats": {nom: a._asdict() for nom, a in triats.items()}, "a_la_vora": a_la_vora(triats),
                 "medianes": medianes, "triades": {A_EQUIPS: de_la_neteja}, "files": t3.registres(nous),
                 "graella": t3.registres(files_graella),
                 "altres": {titol: t3.registres(t) for (titol, _), t in altres.items()},
                 "encerts": t3.registres(encerts)}
    mpa.escriu("model-pilota-morta", contingut,
               markdown(mitja, {A_EQUIPS: de_la_neteja}, triats, medianes, c, passa, robust, c_neteja, millor, c_t3ag,
                        altres, encerts, sostre))


if __name__ == "__main__":
    main()
