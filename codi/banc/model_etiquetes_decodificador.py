"""Les etiquetes de pilota aturada al decodificador (T3ag del pla per tocs, `docs/pla-tocs.md`, «T3ag»; D-69).

    cd codi && uv run python -I -m banc.model_etiquetes_decodificador [--processos 12]

A neteja d'aire (T3ac) tal qual, amb les seves peces de la memòria cau i el decodificador d'A equips sencers a cada
partit. L'única diferència: abans de decodificar, les etiquetes simulades (`banc/smart_tagging_simulat.py`) sumen a la
probabilitat relativa (`cadena/etiquetes_decodificador.py`), i després s'hi posa la D impossible on la neteja ha tret
la pilota. No s'entrena res.

1. **En començar:** A xarxes i A equips sencers, amb la memòria cau, han de donar el banc de la T3v, A pilota creïble,
   el de la T3w, i A neteja d'aire, amb el decodificador d'A equips sencers, el de la T3ac. Si no, s'atura.
2. **La graella** (`ed.GRAELLA`, 192 punts) als quatre ×¼ de cada partit, amb els nivells bo, mitjà i dolent i les
   llavors d'aprendre. Els punts que sumen sempre el mateix (`ed.efectiva`) es decodifiquen un sol cop. Cap punt no hi
   ha de donar la D a una imatge netejada.
3. **La tria** de cada partit, amb els altres nou: el punt amb més spellF1 de mitjana als quatre ×¼ i als tres
   nivells, a la veritat de toc (`tria`).
4. **Es prova** als onze escenaris amb els quatre nivells (bo, mitjà, dolent i cap) i les llavors de provar, les de la
   T3af. Sense etiquetes ha de donar exactament A neteja d'aire, i A neteja d'aire, l'spellF1 de la T3ac. Si no,
   s'atura.
5. **El criteri** del pla, el de la T3af (`banc/model_pilotes_aturades.py`): amb el nivell mitjà, el de sempre contra A
   xarxes; amb el dolent i sense etiquetes, contra A neteja d'aire, als quatre ×¼ i a «partit ×¼», no baixar de
   −0,005. Si no passa, la regla de la D-50 contra A neteja d'aire amb el nivell mitjà, i la mateixa segona part.
   Només per saber-ho: per font; amb el nivell bo; a 5 s o menys de les represes, on encerta cadascú; la part del
   sostre de la T3af que se n'aprofita; i els paràmetres triats.

Escriu `resultats/model-etiquetes-decodificador.json` i `.md`. Tot són dades obertes. Els mòduls d'abans no es toquen.
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

from banc import analisi_t3p as t3p
from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_partit as mp
from banc import model_a_q as mq
from banc import model_a_quart as t3b
from banc import model_a_toc as mt
from banc import model_camp_girat as mcg
from banc import model_neteja_aire as mna
from banc import model_pilota_creible as mpc
from banc import model_pilotes_aturades as mpa
from banc import model_vores as mv
from banc import smart_tagging_simulat as sts
from banc import sostre_sense_pilota as ssp
from banc import veritat_toc as vt
from cadena import etiquetes_decodificador as ed
from cadena import pilota_creible as pc
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ESCENARIS, QUARTS_T3, QUARTS, PARTIT = mpa.ESCENARIS, mpa.QUARTS_T3, mpa.QUARTS, mpa.PARTIT
XARXES, XARXES_TOC, A_EQUIPS, A_CREIBLE, A_NETEJA = mpa.XARXES, mpa.XARXES_TOC, mpa.A_EQUIPS, mpa.A_CREIBLE, mpa.A_NETEJA
A_ED = "A etiquetes al decodificador"
SEMPRE, TOC = mpa.SEMPRE, mpa.TOC
NIVELLS = mpa.NIVELLS                               # bo, mitjà, dolent i cap
NIVELLS_TRIA = ("bo", "mitjà", "dolent")            # amb què es tria: no sabem quin és el del partit
MITJA = mpa.PER_TRIAR                               # el nivell del criteri
TRIA, PROVA = "aprendre", "provar"                  # les llavors de les etiquetes
PARAMS = list(ed.Suma._fields)
DIR_RESULTATS = t3.DIR_RESULTATS


def relativa_amb(r: np.ndarray, etiquetes: tuple, trams: tuple[tuple[int, int, int], ...], s: ed.Suma,
                 netejades: np.ndarray) -> np.ndarray:
    """La relativa d'A pilota creïble amb el que hi sumen les etiquetes, i després la D impossible a `netejades`."""
    return mna.amb_la_d_impossible(ed.amb_les_etiquetes(r, etiquetes, trams, s), netejades)


def base(nom: str, escenari: str) -> tuple:
    """El partit degradat, la relativa d'A pilota creïble (sense la D impossible), la seva q i les imatges netejades:
    les peces d'A neteja d'aire (`mcg.relativa`)."""
    de_sempre = mp.degradat(nom, escenari)
    probes, prior, q_ = mpc.de_qui(A_CREIBLE, nom)
    return de_sempre, log_relativa(probes[escenari].astype(float), prior), q_[escenari], pc.lluny(de_sempre.tracking)


def graella(tasca: tuple[str, str, tuple]) -> list[dict]:
    """Un partit i un ×¼, amb el decodificador d'A neteja d'aire (`triat`): cada punt de la graella amb els nivells de
    `NIVELLS_TRIA` i les llavors d'aprendre, a la veritat de toc."""
    nom, escenari, triat = tasca
    de_sempre, r, q_, netejades = base(nom, escenari)
    p = replace(de_sempre, veritat=vt.veritat(nom))
    files = []
    for nivell in NIVELLS_TRIA:
        etiquetes = mpa.etiquetes_de(nom, escenari, nivell, TRIA)
        fetes: dict[tuple, dict] = {}
        for s in ed.GRAELLA:
            clau_ = ed.efectiva(s)
            if clau_ not in fetes:
                pred = mna.prediccio(relativa_amb(r, etiquetes, de_sempre.trams, s, netejades), q_, de_sempre.trams,
                                     triat)
                if (pred[netejades] == pm.D).any():
                    raise RuntimeError(f"{nom}, {escenari}, {nivell}, {s}: {A_ED} dona la D a una imatge netejada")
                fetes[clau_] = avalua.puntua(p, pred)
            files.append({"partit": nom, "font": de_sempre.font, "escenari": escenari, "nivell": nivell,
                          **s._asdict(), **fetes[clau_]})
    return files


def tria(files: pd.DataFrame, prova: str) -> ed.Suma:
    """El punt de la graella per a `prova`, amb els altres nou: el de més spellF1 de mitjana als quatre ×¼ i als
    nivells de les files (desempata el macroF1)."""
    millor = mp.millor(files[files["partit"] != prova], PARAMS, QUARTS_T3)
    return next(s for s in ed.GRAELLA if tuple(map(float, s)) == tuple(map(float, millor)))


def informe(tasca: tuple[str, str, ed.Suma, tuple]) -> dict[str, list[dict]]:
    """Un partit i un escenari: les files d'A etiquetes al decodificador a cada nivell (amb les llavors de provar), a
    les dues veritats, amb l'spellF1 d'A neteja d'aire a la de toc; i a prop de les represes, on encerta cadascú.
    S'atura si dona la D a una imatge netejada, o si sense etiquetes no dona exactament A neteja d'aire."""
    nom, escenari, s, triat = tasca
    de_sempre, r, q_, netejades = base(nom, escenari)
    toc = vt.veritat(nom)
    partits = {SEMPRE: de_sempre, TOC: replace(de_sempre, veritat=toc)}
    trams = avalua.trams_valids(partits[TOC])
    prop = mpa.a_prop(sts.represes(nom).represes, len(toc), de_sempre.trams) & ssp.dins(len(toc), trams)
    preds = {(A_NETEJA, ""): mna.prediccio(mna.amb_la_d_impossible(r, netejades), q_, de_sempre.trams, triat)}
    for nivell in NIVELLS:
        etiquetes = mpa.etiquetes_de(nom, escenari, nivell, PROVA)
        preds[(A_ED, nivell)] = mna.prediccio(relativa_amb(r, etiquetes, de_sempre.trams, s, netejades), q_,
                                              de_sempre.trams, triat)
        if (preds[(A_ED, nivell)][netejades] == pm.D).any():
            raise RuntimeError(f"{nom}, {escenari}, {nivell}: {A_ED} dona la D a una imatge netejada")
    if not np.array_equal(preds[(A_ED, "cap")], preds[(A_NETEJA, "")]):
        raise RuntimeError(f"{nom}, {escenari}: sense etiquetes, {A_ED} no dona {A_NETEJA}")
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}
    neteja = avalua.puntua(partits[TOC], preds[(A_NETEJA, "")])["spell_f1"]
    files = [{**comu, "metode": A_ED, "nivell": nivell, "veritat": veritat, **s._asdict(), "neteja": neteja,
              **avalua.puntua(p, preds[(A_ED, nivell)])} for nivell in NIVELLS for veritat, p in partits.items()]
    encerts = [{**comu, "metode": metode, "nivell": nivell, "n": int(prop.sum()),
                "encerts": int((pm.fill_abstentions(pred.astype(np.int8), trams)[prop] == toc[prop]).sum())}
               for (metode, nivell), pred in preds.items()]
    return {"files": files, "encerts": encerts}


def comprova_la_neteja(nous: pd.DataFrame, metodes: pd.DataFrame) -> None:
    """A neteja d'aire d'aquí ha de donar l'spellF1 del banc de la T3ac, a cada partit i escenari."""
    de_la_t3ac = metodes[(metodes["metode"] == A_NETEJA) & (metodes["veritat"] == TOC)].set_index(
        ["partit", "escenari"])["spell_f1"]
    aqui = nous.drop_duplicates(["partit", "escenari"]).set_index(["partit", "escenari"])["neteja"]
    if len(aqui) != len(fonts.NOMS) * len(ESCENARIS) or not np.allclose(aqui, de_la_t3ac.reindex(aqui.index),
                                                                        atol=1e-9, rtol=0):
        raise RuntimeError(f"{A_NETEJA} no dona l'spellF1 del banc de la T3ac")


def part_del_sostre(nous: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i nivell, a la veritat de toc: el sostre de la T3af menys A neteja d'aire, el que en treu A
    etiquetes al decodificador i la part. Les files de la T3af han de tenir la mateixa A neteja d'aire."""
    t3af = pd.DataFrame(json.loads((DIR_RESULTATS / "sostre-pilotes-aturades.json").read_text())["files"])
    aqui = nous[(nous["veritat"] == TOC) & nous["nivell"].isin(mpa.NIVELLS_SOSTRE)]
    junts = aqui.merge(t3af[["partit", "escenari", "nivell", "neteja", "sostre"]], on=["partit", "escenari", "nivell"],
                       suffixes=("", " de la T3af"), validate="one_to_one")
    if len(junts) != len(aqui) or not np.allclose(junts["neteja"], junts["neteja de la T3af"], atol=1e-9, rtol=0):
        raise RuntimeError("El sostre de la T3af no és d'aquesta A neteja d'aire")
    g = junts.assign(sostre=junts["sostre"] - junts["neteja"], treu=junts["spell_f1"] - junts["neteja"]).groupby(
        ["escenari", "nivell"], sort=False)[["sostre", "treu"]].mean()
    g["part"] = g["treu"] / g["sostre"]
    return g.unstack("nivell").reindex(ESCENARIS).rename_axis("escenari")


def taula_triats(triats: dict[str, ed.Suma]) -> pd.DataFrame:
    return pd.DataFrame({nom: s._asdict() for nom, s in triats.items()}).T.rename_axis("partit")


def a_la_vora(triats: dict[str, ed.Suma]) -> list[str]:
    """Els paràmetres que algun partit tria al valor més alt de la graella."""
    return [f for f in PARAMS if any(getattr(s, f) == max(getattr(g, f) for g in ed.GRAELLA) for s in triats.values())]


def taula_encerts(t: pd.DataFrame) -> pd.DataFrame:
    g = t.groupby(["escenari", "metode", "nivell"], sort=False)[["n", "encerts"]].sum()
    part = (g["encerts"] / g["n"]).unstack(["metode", "nivell"])
    part.columns = [A_NETEJA if m == A_NETEJA else f"{A_ED}, {n}" for m, n in part.columns]
    return part[[A_NETEJA, *(f"{A_ED}, {n}" for n in NIVELLS)]].reindex(ESCENARIS).rename_axis("escenari")


def _regla(millor: dict[str, bool], robust: dict[str, bool]) -> list[str]:
    es = all(millor.values()) and all(robust.values())
    m = mpa._marca
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | {m(millor['quarts'])} |",
            f"| «{PARTIT}» | la diferència no és negativa | {m(millor['partit'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {m(millor['altres'])} |",
            f"| Dolent i cap | la segona part del criteri | {m(all(robust.values()))} |", "",
            f"**{A_ED} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_ED if es else A_NETEJA}.", ""]


def markdown(mitja: pd.DataFrame, triades: dict, triats: dict[str, ed.Suma], c: pd.DataFrame, passa: dict[str, bool],
             robust: dict[str, bool], c_neteja: dict[str, pd.DataFrame], millor: dict[str, bool],
             altres: dict[tuple[str, str], pd.DataFrame], encerts: pd.DataFrame, sostre: pd.DataFrame) -> str:
    passa_tot = all(passa.values()) and all(robust.values())
    vora = a_la_vora(triats)
    linies = ["# Banc obert · Les etiquetes de pilota aturada al decodificador (T3ag)", "",
              "Generat amb `uv run python -I -m banc.model_etiquetes_decodificador`. Dades obertes: 7 partits de DFL",
              "(IDSSE, CC BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es",
              "fa i el criteri: `docs/pla-tocs.md`, «T3ag», i la capçalera de `banc/model_etiquetes_decodificador.py`.",
              "Es puntua a la veritat de toc.", "",
              f"**{XARXES_TOC}** i **{A_EQUIPS}** són els de la T3v, **{A_CREIBLE}**, el de la T3w, i **{A_NETEJA}**,",
              "el de la T3ac, amb les peces de la memòria cau (✓ comprovat). **A etiquetes al decodificador** és A",
              "neteja d'aire amb el seu decodificador, i abans de decodificar, el que hi sumen les etiquetes simulades.",
              "✓ Comprovat: no dona mai la D a una imatge netejada, i sense etiquetes dona exactament A neteja d'aire.", "",
              f"## Amb el nivell {MITJA}: {A_ED} contra {XARXES_TOC} (spellF1), el criteri", "",
              *t3b._taula(c, A_ED, XARXES_TOC), "", *mt._criteris(passa),
              f"## Amb els nivells dolent i cap: {A_ED} contra {A_NETEJA}, la segona part del criteri", "",
              *mpa._robustesa(c_neteja, robust), "",
              f"**{A_ED} {'passa' if passa_tot else 'no passa'} el criteri sencer.**", ""]
    for nivell in NIVELLS:
        linies += [f"## Amb el nivell {nivell}: {A_ED} contra {A_NETEJA} (spellF1)", "",
                   *t3i._comparacio(c_neteja[nivell], A_ED, A_NETEJA), ""]
    if not passa_tot:
        linies += ["## No passa: és el millor fins ara?", "",
                   f"La regla de la D-50, escrita abans, contra {A_NETEJA} amb el nivell {MITJA}, i la mateixa",
                   "segona part del criteri:", "", *_regla(millor, robust)]
    for (titol, contra), taula in altres.items():
        linies += [f"## {titol}", "", *t3i._comparacio(taula, A_ED, contra), ""]
    linies += ["## La part del sostre de la T3af que se n'aprofita", "",
               "A la veritat de toc, la mitjana dels deu partits: el sostre de la T3af menys A neteja d'aire, el que en",
               "treu A etiquetes al decodificador, i la part.", "", t3p.md(sostre), "",
               "## A 5 s o menys de cada represa", "",
               "La part de les imatges vàlides a 5 s o menys d'una represa on la predicció (amb les abstencions",
               "omplertes) és la veritat de toc.", "", t3p.md(taula_encerts(encerts)), "",
               "## Els paràmetres triats", "",
               "A cada partit, amb els altres nou, als quatre ×¼ i a la mitjana dels nivells bo, mitjà i dolent.", "",
               mv._md(taula_triats(triats), 2), "",
               ("**A la vora de la graella** (algun partit tria el valor més alt): " + ", ".join(f"`{f}`" for f in vora)
                + "." if vora else "Cap paràmetre no es tria a la vora de la graella."), "",
               f"## L'spellF1 de cada mètode (mitjana dels deu partits, nivell {MITJA})", "",
               *mt._mitjanes(mitja, [XARXES_TOC, A_EQUIPS, A_NETEJA, A_ED]), "## Els decodificadors", "",
               f"{A_NETEJA} i {A_ED} fan servir, a cada partit, el d'{A_EQUIPS}.", "", *mq._triades(triades), ""]
    return "\n".join(linies)


def clau_dels_resultats() -> str:
    h = hashlib.sha256((mpa.clau_dels_resultats() + sts.CLAU).encode())
    for modul in (ed, mpa):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_etiquetes_decodificador as aquest

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
    print(f"· {A_ED}: la graella, mai la D a les imatges netejades", flush=True)
    triats = {nom: tria(files_graella, nom) for nom in fonts.NOMS}
    tasques = [(nom, e, triats[nom], de_la_neteja[nom]) for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    trossos = en_paral_lel("informe", tasques, args.processos)
    nous, encerts = (pd.DataFrame([f for tros in trossos for f in tros[k]]) for k in ("files", "encerts"))
    comprova_la_neteja(nous, metodes)
    print(f"· {A_ED}: sense etiquetes, exactament {A_NETEJA}, amb l'spellF1 de la T3ac", flush=True)
    sense = nous.drop(columns=[*PARAMS, "neteja"])
    c = mt.comparacio(mpa.de_nivell(metodes, sense, MITJA), A_ED, XARXES_TOC, TOC, amb_criteri=True)
    c_neteja = {n: mt.comparacio(mpa.de_nivell(metodes, sense, n), A_ED, A_NETEJA, TOC, amb_criteri=False)
                for n in NIVELLS}
    passa, robust, millor = mt.compleix(c), mpa.aguanta(c_neteja), mq.millor_fins_ara(c_neteja[MITJA])
    mitja = mpa.de_nivell(metodes, sense, MITJA)
    altres = {(f"{A_ED} contra {contra}, nivell {MITJA}, només els partits de {font}", contra):
              mt.comparacio(mitja[mitja["font"] == font], A_ED, contra, TOC, amb_criteri=False)
              for font in mpc.FONTS for contra in (XARXES_TOC, A_NETEJA)}
    altres[(f"{A_ED} contra {XARXES_TOC}, nivell bo", XARXES_TOC)] = mt.comparacio(
        mpa.de_nivell(metodes, sense, "bo"), A_ED, XARXES_TOC, TOC, amb_criteri=False)
    sostre = part_del_sostre(nous)
    contingut = {"clau": clau_dels_resultats(), "passa": passa, "aguanta": robust, "millor_fins_ara": millor,
                 "comparacio": t3.registres(c),
                 "contra_a_neteja_d_aire": {n: t3.registres(t) for n, t in c_neteja.items()},
                 "triats": {nom: s._asdict() for nom, s in triats.items()}, "a_la_vora": a_la_vora(triats),
                 "triades": {A_EQUIPS: de_la_neteja}, "files": t3.registres(nous), "graella": t3.registres(files_graella),
                 "altres": {titol: t3.registres(t) for (titol, _), t in altres.items()},
                 "encerts": t3.registres(encerts)}
    mpa.escriu("model-etiquetes-decodificador", contingut,
               markdown(mitja, {A_EQUIPS: de_la_neteja}, triats, c, passa, robust, c_neteja, millor, altres, encerts,
                        sostre))


if __name__ == "__main__":
    main()
