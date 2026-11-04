"""Les fases de defensar a sobre d'A girat amb fases (T3an del pla per tocs, `docs/pla-tocs.md`, «T3an»; D-82).

    cd codi && uv run python -I -m banc.model_girat_defenses [--processos 12]

**A girat amb defenses** és A girat amb fases tal qual, el de la cadena, amb els punts que hi va triar cada partit a la
T3am (la pilota morta i les fases) i el decodificador d'A camp girat. Les fases de defensar simulades
(`banc/fases_defensar.py`) porten l'equip que defensa: es giren a l'equip que té la pilota i s'afegeixen a les d'atac
abans de restar (`amb_les_de_defensar`), amb la mateixa `gamma`, `delta` i `marge_s`. Una de defensar i una d'atac
del mateix equip a la mateixa imatge hi compten com una; d'equips diferents, no s'hi resta res. No s'entrena ni es
tria res.

1. **En començar:** el banc de la T3am ha de ser d'aquest codi (`de_la_t3am`), i A girat amb fases, refet aquí amb les
   seves peces, n'ha de donar les files (`comprova_la_t3am`). Si no, s'atura.
2. **Es prova** als onze escenaris amb les llavors de provar (`informe`), als casos de `CASOS`: les fases d'atac, al
   nivell de cada fila; les de defensar, al mateix nivell i amb cada `lligades`; i les de defensar al nivell dolent
   amb `lligades` = 0, a sobre de les d'atac al mitjà (`SEGONA`). Amb `lligades` = 1, i sense fases (el nivell cap),
   ha de donar exactament A girat amb fases (`comprova_les_lligades`), i mai la D a una imatge netejada. Si no,
   s'atura.
3. **El criteri** del pla, contra A girat amb fases, amb el nivell mitjà i `lligades` = 0,5 (`CRITERI`); la segona
   part, a `SEGONA` (`aguanta`); el millor fins ara, amb la regla de la D-50. Només per saber-ho: els altres casos, per
   font, les causes de `banc/on_falla.py` i quanta part de les imatges de dins de les parts té alguna fase.

Escriu `resultats/model-girat-defenses.json` i `.md`. Tot són dades obertes. Els mòduls d'abans no es toquen.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd

from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import fases_defensar as fd
from banc import fases_simulades as fsm
from banc import model_a_canvis as t3i
from banc import model_a_partit as mp
from banc import model_a_q as mq
from banc import model_a_quart as t3b
from banc import model_a_toc as mt
from banc import model_camp_girat as mcg
from banc import model_fases as mfs
from banc import model_girat_fases as mgf
from banc import model_pilota_creible as mpc
from banc import model_pilotes_aturades as mpa
from banc import model_vores as mv
from banc import on_falla as of
from banc import smart_tagging_simulat as sts
from banc import veritat_toc as vt
from cadena import fases as fs
from cadena import pilota_morta as pmo
from cadena.fases import Fase
from possessio.oficial import possession_metrics as pm

ESCENARIS, QUARTS_T3, PARTIT, CURTS = mgf.ESCENARIS, mgf.QUARTS_T3, mgf.PARTIT, mgf.CURTS
QUARTS = mp.QUARTS                                  # els quatre ×¼ i «partit ×¼»: la segona part
A_GIRAT, A_GFS = mgf.A_GIRAT, mgf.A_GFS
A_GDF = "A girat amb defenses"
SEMPRE, TOC, NIVELLS, MITJA, PROVA = mgf.SEMPRE, mgf.TOC, mgf.NIVELLS, mgf.MITJA, mgf.PROVA
DIR_RESULTATS = mgf.DIR_RESULTATS
MARGE_SEGONA = mpa.MARGE_ROBUST


class Cas(NamedTuple):
    nivell: str             # el de les fases d'atac (i de les etiquetes)
    defensar: str           # el de les fases de defensar
    lligades: float


CRITERI = Cas(MITJA, MITJA, 0.5)
SEGONA = Cas(MITJA, "dolent", 0.0)
CASOS = (*(Cas(n, n, x) for n in NIVELLS for x in fd.LLIGADES), SEGONA)


def amb_les_de_defensar(atac: tuple[Fase, ...], defensar: tuple[Fase, ...]) -> tuple[Fase, ...]:
    """Les fases d'atac i les de defensar girades a l'equip que té la pilota, juntes (`cadena.fases.resta` hi compta
    una per equip a cada imatge)."""
    return tuple(sorted((*atac, *(Fase(f.inici, f.final, 1 - f.equip) for f in defensar))))


def cobertura(atac: tuple[Fase, ...], totes: tuple[Fase, ...], n: int, trams: tuple[tuple[int, int, int], ...],
              marge_s: float) -> dict[str, float]:
    """De les imatges de dins de les parts, la part amb alguna fase (d'atac, o d'atac o de defensar) i la part on es
    resta (dins de fases d'un sol equip, sense el marge `marge_s`)."""
    dins_part = np.zeros(n, dtype=bool)
    for _, a, b in trams:
        dins_part[a:b + 1] = True

    def alguna(fases: tuple[Fase, ...]) -> float:
        return float(fs.estones(fases, n, trams, 0.0).any(axis=1)[dins_part].mean())

    def resta(fases: tuple[Fase, ...]) -> float:
        d = fs.estones(fases, n, trams, marge_s)
        return float((d[:, pm.H] != d[:, pm.A])[dins_part].mean())

    return {"part_atac": alguna(atac), "part_alguna": alguna(totes), "resta_atac": resta(atac), "resta_amb": resta(totes)}


def comprova_les_lligades(sense: dict[str, np.ndarray], amb: dict[Cas, np.ndarray], nom: str, escenari: str) -> None:
    """Amb `lligades` = 1 a cada nivell, i sense fases (el nivell cap), A girat amb defenses ha de ser exactament A
    girat amb fases."""
    for nivell in NIVELLS:
        if not np.array_equal(amb[Cas(nivell, nivell, 1.0)], sense[nivell]):
            raise RuntimeError(f"{nom}, {escenari}, {nivell}: amb lligades = 1, {A_GDF} no dona {A_GFS}")
    for lligades in fd.LLIGADES:
        if not np.array_equal(amb[Cas("cap", "cap", lligades)], sense["cap"]):
            raise RuntimeError(f"{nom}, {escenari}: sense fases, {A_GDF} no dona {A_GFS}")


def _causes(comu: dict, metode: str, toc: np.ndarray, pred: np.ndarray, trams: list, vista: np.ndarray) -> tuple:
    c, so = mfs.causes_de(toc.astype(np.int8), pred, trams, vista)
    return ([{**comu, "metode": metode, "causa": k, "n": n} for k, n in c.items()],
            [{**comu, "metode": metode, "on": k, "n": n} for k, n in so.items()])


def informe(tasca: tuple[str, str, pmo.Abans, mfs.Suma, tuple]) -> dict[str, list[dict]]:
    """Un partit i un escenari, amb els punts de la T3am (`a`, `s`) i el decodificador d'A camp girat (`triat`): A girat
    amb fases a cada nivell i A girat amb defenses a cada cas, a les dues veritats; les causes, al cas del criteri."""
    nom, escenari, a, s, triat = tasca
    b = mgf.base(A_GIRAT, nom, escenari)
    de_sempre, r, _, netejades = b
    toc = vt.veritat(nom)
    partits = {SEMPRE: de_sempre, TOC: replace(de_sempre, veritat=toc)}
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}
    relatives = {n: mfs.relativa_pm(nom, escenari, n, PROVA, a, de_sempre, r, netejades) for n in NIVELLS}
    atac = {n: fsm.fases_de(nom, escenari, n, PROVA) for n in NIVELLS}
    sense = {n: mfs._decodifica(nom, escenari, n, A_GFS, relatives[n], atac[n], s, b, triat) for n in NIVELLS}
    amb, quantes = {}, []
    for cas in CASOS:
        defensar = fd.fases_de(nom, escenari, cas.defensar, PROVA, cas.lligades)
        totes = amb_les_de_defensar(atac[cas.nivell], defensar)
        amb[cas] = mfs._decodifica(nom, escenari, cas.nivell, A_GDF, relatives[cas.nivell], totes, s, b, triat)
        quantes.append({**comu, **cas._asdict(), "fases": len(atac[cas.nivell]), "de_defensar": len(defensar),
                        **cobertura(atac[cas.nivell], totes, len(toc), de_sempre.trams, s.marge_s)})
    comprova_les_lligades(sense, amb, nom, escenari)
    gfs = [{**comu, "metode": A_GFS, "nivell": n, "veritat": v, **avalua.puntua(p, sense[n])}
           for n in NIVELLS for v, p in partits.items()]
    gdf = [{**comu, "metode": A_GDF, **cas._asdict(), "veritat": v, **avalua.puntua(p, amb[cas])}
           for cas in CASOS for v, p in partits.items()]
    vista, valids = ~np.isnan(de_sempre.tracking.pilota[:, 0]), avalua.trams_valids(partits[TOC])
    (c1, s1), (c2, s2) = (_causes(comu, m, toc, pred, valids, vista)
                          for m, pred in ((A_GFS, sense[MITJA]), (A_GDF, amb[CRITERI])))
    return {"gfs": gfs, "gdf": gdf, "causes": c1 + c2, "sobrants": s1 + s2, "fases": quantes}


def de_la_t3am() -> dict:
    desat = json.loads((DIR_RESULTATS / "model-girat-fases.json").read_text())
    if desat["clau"] != mgf.clau_dels_resultats():
        raise RuntimeError("El banc de la T3am no és d'aquest codi")
    return desat


def comprova_la_t3am(refet: pd.DataFrame, t3am: pd.DataFrame) -> None:
    """A girat amb fases d'aquí ha de donar les files d'A girat amb fases del banc de la T3am."""
    claus = ["partit", "escenari", "nivell", "veritat"]
    b = t3am[t3am["metode"] == A_GFS].set_index(claus).sort_index()
    a = refet.set_index(claus).sort_index()
    valors = [c for c in a.columns if c not in ("metode", "font")]
    if (not a.index.equals(b.index) or any(c not in b.columns for c in valors)
            or not all(np.allclose(a[c].to_numpy(float), b[c].to_numpy(float), atol=1e-12, rtol=0) for c in valors)):
        raise RuntimeError(f"{A_GFS} d'aquí no dona les files del banc de la T3am")


def de_cas(gfs: pd.DataFrame, gdf: pd.DataFrame, cas: Cas) -> pd.DataFrame:
    """Les files d'A girat amb fases al nivell de `cas` i les d'A girat amb defenses de `cas`, sense el cas."""
    sense = gfs[gfs["nivell"] == cas.nivell].drop(columns="nivell")
    triat = (gdf["nivell"] == cas.nivell) & (gdf["defensar"] == cas.defensar) & (gdf["lligades"] == cas.lligades)
    return pd.concat([sense, gdf[triat].drop(columns=list(Cas._fields))], ignore_index=True)


def comparacions(gfs: pd.DataFrame, gdf: pd.DataFrame) -> dict:
    """Les comparacions del pla, contra A girat amb fases: el criteri, la segona part, el millor fins ara i les de
    saber-ho (els altres casos amb fases, i per font)."""
    def compara(cas: Cas, amb_criteri: bool = False, files: pd.DataFrame | None = None) -> pd.DataFrame:
        return mt.comparacio(de_cas(gfs, gdf, cas) if files is None else files, A_GDF, A_GFS, TOC,
                             amb_criteri=amb_criteri)

    c, segona = compara(CRITERI, amb_criteri=True), compara(SEGONA)
    aguanta = bool((segona["diferencia"][segona["escenari"].isin(QUARTS)] >= -MARGE_SEGONA - 1e-12).all())
    casos = {cas: compara(cas) for cas in CASOS if cas not in (CRITERI, SEGONA) and cas.nivell != "cap"}
    mitja = de_cas(gfs, gdf, CRITERI)
    per_font = {font: compara(CRITERI, files=mitja[mitja["font"] == font]) for font in mpc.FONTS}
    return {"c": c, "passa": mt.compleix(c), "segona": segona, "aguanta": aguanta, "millor": mq.millor_fins_ara(c),
            "casos": casos, "per_font": per_font, "mitja": mitja}


def taula_causes(causes: pd.DataFrame, sobren: pd.DataFrame, escenaris: tuple[str, ...]) -> pd.DataFrame:
    """Com `model_girat_fases.taula_causes`, per a A girat amb fases i A girat amb defenses."""
    c = causes[causes["escenari"].isin(escenaris)].groupby(["metode", "causa"])["n"].sum().unstack("metode")
    totes = c.sum()
    t = (c / totes).reindex(of.CAUSES).fillna(0.0)
    s = sobren[sobren["escenari"].isin(escenaris)].groupby(["metode", "on"])["n"].sum().unstack("metode")
    t.loc["sobren a l'altre equip, per cada 100"] = 100 * s.reindex(["a l'altre equip"]).fillna(0.0).iloc[0] / totes
    return t[[A_GFS, A_GDF]].rename_axis("causa")


def nom_del_cas(cas: Cas) -> str:
    return f"atac {cas.nivell}, defensar {cas.defensar}, lligades {cas.lligades:g}"


def taula_fases(quantes: pd.DataFrame) -> pd.DataFrame:
    t = quantes[quantes["escenari"] == CURTS].groupby(list(Cas._fields), sort=False)[
        ["fases", "de_defensar", "part_atac", "part_alguna", "resta_atac", "resta_amb"]].mean()
    t.index = [nom_del_cas(Cas(*i)) for i in t.index]
    return t.reindex([nom_del_cas(c) for c in CASOS]).rename_axis("cas")


def _segona(c: pd.DataFrame, aguanta: bool) -> list[str]:
    d = c.set_index("escenari")["diferencia"]
    return [f"| {' | '.join(QUARTS)} | No baixa de −{MARGE_SEGONA} |", "|---" * (len(QUARTS) + 1) + "|",
            "| " + " | ".join(f"{d[e]:+.4f}" for e in QUARTS) + f" | {mpa._marca(aguanta)} |"]


def _regla(millor: dict[str, bool], aguanta: bool) -> list[str]:
    es = all(millor.values()) and aguanta
    m = mpa._marca
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | {m(millor['quarts'])} |",
            f"| «{PARTIT}» | la diferència no és negativa | {m(millor['partit'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {m(millor['altres'])} |",
            f"| {nom_del_cas(SEGONA)} | la segona part del criteri | {m(aguanta)} |", "",
            f"**{A_GDF} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_GDF if es else A_GFS}.", ""]


def markdown(r: dict) -> str:
    passa_tot = all(r["passa"].values()) and r["aguanta"]
    linies = ["# Banc obert · Les fases de defensar a sobre d'A girat amb fases (T3an)", "",
              "Generat amb `uv run python -I -m banc.model_girat_defenses`. Dades obertes: 7 partits de DFL (IDSSE, CC",
              "BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3an», i la capçalera de `banc/model_girat_defenses.py`. Es puntua a la",
              "veritat de toc.", "",
              f"**{A_GFS}** és el de la T3am, el de la cadena, refet aquí amb els punts que hi va triar cada partit (✓",
              f"comprovat: en dona les files). **{A_GDF}** és {A_GFS} amb les fases de defensar simulades, girades, a",
              "sobre, amb els mateixos paràmetres; no s'entrena ni es tria res. ✓ Comprovat: no dona mai la D a una",
              f"imatge netejada; amb `lligades` = 1, i sense fases, és exactament {A_GFS}.", "",
              f"## {nom_del_cas(CRITERI)}: {A_GDF} contra {A_GFS} (spellF1), el criteri", "",
              *t3b._taula(r["c"], A_GDF, A_GFS), "", *mt._criteris(r["passa"]),
              f"## {nom_del_cas(SEGONA)}: la segona part del criteri", "", *_segona(r["segona"], r["aguanta"]), "",
              f"**{A_GDF} {'passa' if passa_tot else 'no passa'} el criteri sencer.**", ""]
    if not passa_tot:
        linies += ["## No passa: és el millor fins ara?", "",
                   f"La regla de la D-50, escrita abans, contra {A_GFS} a {nom_del_cas(CRITERI)}, i la mateixa segona",
                   "part del criteri:", "", *_regla(r["millor"], r["aguanta"])]
    for cas, c in r["casos"].items():
        linies += [f"## {nom_del_cas(cas)}: {A_GDF} contra {A_GFS} (spellF1)", "", *t3i._comparacio(c, A_GDF, A_GFS),
                   ""]
    for font, c in r["per_font"].items():
        linies += [f"## {nom_del_cas(CRITERI)}, només els partits de {font}", "", *t3i._comparacio(c, A_GDF, A_GFS),
                   ""]
    linies += ["## On falla, abans i després", "",
               f"A {nom_del_cas(CRITERI)}, les causes de `banc/on_falla.py`: la part de les possessions de la veritat",
               "de cada causa, i les predites que sobren a l'altre equip per cada 100 possessions de la veritat.", ""]
    for titol, escenaris in ((CURTS, (CURTS,)), ("els quatre ×¼ junts", QUARTS_T3), ("net", ("net",))):
        linies += [f"**{titol}**", "", mv._md(taula_causes(r["causes"], r["sobrants"], escenaris), 3), ""]
    linies += ["## Les fases simulades", "",
               f"A {CURTS}, amb les llavors de provar, la mitjana dels deu partits: quantes fases d'atac i de defensar;",
               "de les imatges de dins de les parts, la part amb alguna fase (d'atac, o de qualsevol) i la part on es",
               "resta (dins de fases d'un sol equip, sense el marge triat).", "", mv._md(taula_fases(r["fases"]), 3), "",
               f"## L'spellF1 de cada mètode (mitjana dels deu partits, {nom_del_cas(CRITERI)})", "",
               *mt._mitjanes(r["mitja"], [A_GFS, A_GDF]), "## Els punts i els decodificadors", "",
               f"Els de la T3am, a cada partit: la pilota morta i les fases d'{A_GFS}, i el decodificador d'{A_GIRAT}.",
               ""]
    return "\n".join(linies)


def clau_dels_resultats() -> str:
    h = hashlib.sha256(mgf.clau_dels_resultats().encode())
    for f in (Path(fd.__file__), Path(__file__)):
        h.update(f.read_bytes())
    return h.hexdigest()


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_girat_defenses as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        return list(feina.map(getattr(aquest, fes), tasques))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    args = ap.parse_args()
    for nom in fonts.NOMS:
        for metode in (mgf.XARXES, mgf.A_EQUIPS, mgf.A_CREIBLE, A_GIRAT):
            mcg.de_qui(metode, nom)
        mpc.q(nom, entrena=False)
        vt.veritat(nom)
        sts.represes(nom)
    t3am = de_la_t3am()
    triats_pm = {nom: pmo.Abans(**a) for nom, a in t3am["triats_pilota_morta"].items()}
    triats_fs = {nom: mfs.Suma(**s) for nom, s in t3am["triats_fases"].items()}
    del_girat = {nom: tuple(t) for nom, t in t3am["triades"][A_GIRAT].items()}
    trossos = en_paral_lel("informe", [(nom, e, triats_pm[nom], triats_fs[nom], del_girat[nom])
                                       for nom, e in itertools.product(fonts.NOMS, ESCENARIS)], args.processos)
    gfs, gdf, causes, sobren, quantes = (pd.DataFrame([f for tros in trossos for f in tros[k]])
                                         for k in ("gfs", "gdf", "causes", "sobrants", "fases"))
    comprova_la_t3am(gfs, pd.DataFrame(t3am["files"]))
    print(f"· {A_GFS}, refet, dona el banc de la T3am; amb lligades = 1, i sense fases, {A_GDF} és exactament "
          f"{A_GFS}; mai la D a les imatges netejades", flush=True)
    r = {**comparacions(gfs, gdf), "causes": causes, "sobrants": sobren, "fases": quantes}
    contingut = {"clau": clau_dels_resultats(), "passa": r["passa"], "aguanta": r["aguanta"],
                 "millor_fins_ara": r["millor"], "comparacio": t3.registres(r["c"]),
                 "segona_part": t3.registres(r["segona"]),
                 "casos": {nom_del_cas(cas): t3.registres(c) for cas, c in r["casos"].items()},
                 "per_font": {font: t3.registres(c) for font, c in r["per_font"].items()},
                 "files_a_girat_amb_fases": t3.registres(gfs), "files": t3.registres(gdf),
                 "causes": t3.registres(causes), "sobrants": t3.registres(sobren), "fases": t3.registres(quantes)}
    mpa.escriu("model-girat-defenses", contingut, markdown(r))


if __name__ == "__main__":
    main()
