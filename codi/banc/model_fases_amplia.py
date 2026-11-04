"""A fases amb la graella ampliada (T3al del pla per tocs, `docs/pla-tocs.md`, «T3al»; D-74).

    cd codi && uv run python -I -m banc.model_fases_amplia [--processos 12]

A fases de la T3ak (`banc/model_fases.py`) tal qual: les mateixes fases simulades, amb els mateixos nivells i les
mateixes llavors, A pilota morta a sota, la mateixa resta i el mateix decodificador. Només canvia la graella
(`GRAELLA`): `gamma` i `delta` fins a 8 per imatge, i `marge_s` de 0 a 1 s. No s'entrena res.

1. **En començar:** A xarxes i A equips sencers, amb la memòria cau, han de donar el banc de la T3v, A pilota creïble,
   el de la T3w, i A neteja d'aire, el de la T3ac; i els bancs de la T3ah i de la T3ak han de ser d'aquest codi. Si
   no, s'atura.
2. **La graella** als quatre ×¼ de cada partit, amb els nivells bo, mitjà i dolent i les llavors de triar. Cap punt no
   hi ha de donar la D a una imatge netejada, i els punts que ja hi eren a la T3ak hi han de donar exactament el mateix
   (`comprova_la_graella`).
3. **La tria** de cada partit, amb els altres nou, com a la T3ak (`model_fases.tria`).
4. **Es prova** als onze escenaris amb els quatre nivells i les llavors de provar (`model_fases.informe`). A pilota
   morta d'aquí ha de donar l'spellF1 del banc de la T3ah; sense etiquetes, exactament A neteja d'aire; i sense fases,
   A fases àmplia ha de ser exactament A pilota morta. On un partit tria el mateix punt que a la T3ak, ha de donar
   exactament A fases (`comprova_les_mateixes`). Si no, s'atura.
5. **El criteri** del pla, el de la T3ak; el millor fins ara, contra A fases. Només per saber-ho: per font; amb el
   nivell bo; contra A pilota morta i contra A fases a cada nivell; les causes de `banc/on_falla.py` per als tres, i
   el punt triat a cada partit.

Escriu `resultats/model-fases-amplia.json` i `.md`. Tot són dades obertes. Els mòduls d'abans no es toquen.
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
from banc import model_a_q as mq
from banc import model_a_quart as t3b
from banc import model_a_toc as mt
from banc import model_camp_girat as mcg
from banc import model_etiquetes_decodificador as med
from banc import model_fases as mfs
from banc import model_pilota_creible as mpc
from banc import model_pilotes_aturades as mpa
from banc import model_represes as mre
from banc import model_vores as mv
from banc import on_falla as of
from banc import smart_tagging_simulat as sts
from banc import veritat_toc as vt
from cadena import pilota_morta as pmo

ESCENARIS, QUARTS_T3, PARTIT, CURTS = mfs.ESCENARIS, mfs.QUARTS_T3, mfs.PARTIT, mfs.CURTS
XARXES, XARXES_TOC, A_EQUIPS, A_CREIBLE, A_NETEJA = mfs.XARXES, mfs.XARXES_TOC, mfs.A_EQUIPS, mfs.A_CREIBLE, mfs.A_NETEJA
A_PM, A_FS = mfs.A_PM, mfs.A_FS
A_FA = "A fases àmplia"
TOC, NIVELLS, NIVELLS_TRIA, MITJA, TRIA = mfs.TOC, mfs.NIVELLS, mfs.NIVELLS_TRIA, mfs.MITJA, mfs.TRIA
DIR_RESULTATS = mfs.DIR_RESULTATS
Suma, PARAMETRES = mfs.Suma, mfs.PARAMETRES

GAMMES = (0.0, 0.5, 1.0, 2.0, 4.0, 8.0)          # per imatge, a l'altre equip
DELTES = (0.0, 1.0, 2.0, 4.0, 8.0)               # per imatge, a la D
MARGES = (0.0, 0.5, 1.0)                         # a cada vora de la fase, en segons
GRAELLA = tuple(Suma(*v) for v in itertools.product(GAMMES, DELTES, MARGES))
COMUNS = frozenset(GRAELLA) & frozenset(mfs.GRAELLA)


def graella(tasca: tuple[str, str, pmo.Abans, tuple]) -> list[dict]:
    """Com `model_fases.graella`, amb la graella d'aquí: un partit i un ×¼, cada punt amb els nivells de
    `NIVELLS_TRIA` i les llavors de triar, a la veritat de toc."""
    nom, escenari, a_pm, triat = tasca
    base = med.base(nom, escenari)
    de_sempre, r, _, netejades = base
    p = replace(de_sempre, veritat=vt.veritat(nom))
    files = []
    for nivell in NIVELLS_TRIA:
        relativa = mfs.relativa_pm(nom, escenari, nivell, TRIA, a_pm, de_sempre, r, netejades)
        fases = fsm.fases_de(nom, escenari, nivell, TRIA)
        fetes: dict[Suma, dict] = {}
        for s in GRAELLA:
            if mfs.efectiva(s) not in fetes:
                pred = mfs._decodifica(nom, escenari, nivell, A_FA, relativa, fases, s, base, triat)
                fetes[mfs.efectiva(s)] = {k: v for k, v in avalua.puntua(p, pred).items()
                                          if k in ("spell_f1", "macro_f1")}
            files.append({"partit": nom, "font": de_sempre.font, "escenari": escenari, "nivell": nivell,
                          **s._asdict(), **fetes[mfs.efectiva(s)]})
    return files


def _als_comuns(files: pd.DataFrame) -> pd.DataFrame:
    es = [Suma(*map(float, v)) in COMUNS for v in files[PARAMETRES].itertuples(index=False)]
    return files[es].set_index(["partit", "escenari", "nivell", *PARAMETRES])[["spell_f1", "macro_f1"]].sort_index()


def comprova_la_graella(aqui: pd.DataFrame, t3ak: pd.DataFrame) -> None:
    """Els punts de la graella que ja hi eren a la T3ak hi han de donar exactament el mateix."""
    a, b = _als_comuns(aqui), _als_comuns(t3ak)
    if not a.index.equals(b.index) or not np.array_equal(a.to_numpy(float), b.to_numpy(float), equal_nan=True):
        raise RuntimeError(f"{A_FA}: els punts de la graella de la T3ak no hi donen el mateix")


def comprova_les_mateixes(nous: pd.DataFrame, t3ak: pd.DataFrame, triats: dict[str, Suma],
                          triats_t3ak: dict[str, Suma]) -> None:
    """On un partit tria el mateix punt que a la T3ak, A fases àmplia ha de donar exactament A fases."""
    iguals = [nom for nom in fonts.NOMS if triats[nom] == triats_t3ak[nom]]
    claus = ["partit", "escenari", "nivell", "veritat"]

    def de(t: pd.DataFrame, metode: str) -> pd.Series:
        return t[(t["metode"] == metode) & t["partit"].isin(iguals)].set_index(claus)["spell_f1"].sort_index()

    a, b = de(nous, A_FA), de(t3ak, A_FS)
    if not a.index.equals(b.index) or not np.array_equal(a.to_numpy(float), b.to_numpy(float), equal_nan=True):
        raise RuntimeError(f"{A_FA}: on es tria el punt de la T3ak, no dona {A_FS}")


def reanomena(r: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """Les files de `model_fases.informe` diuen A fases al mètode nou: aquí és A fases àmplia."""
    return {k: [{**f, "metode": A_FA} if f.get("metode") == A_FS else f for f in v] for k, v in r.items()}


def de_la_t3ak() -> dict:
    desat = json.loads((DIR_RESULTATS / "model-fases.json").read_text())
    if desat["clau"] != mfs.clau_dels_resultats():
        raise RuntimeError("El banc de la T3ak no és d'aquest codi")
    return desat


def taula_causes(causes: pd.DataFrame, sobren: pd.DataFrame, escenaris: tuple[str, ...]) -> pd.DataFrame:
    """Com `model_fases.taula_causes`, per als tres mètodes."""
    c = causes[causes["escenari"].isin(escenaris)].groupby(["metode", "causa"])["n"].sum().unstack("metode")
    totes = c.sum()
    t = (c / totes).reindex(of.CAUSES).fillna(0.0)
    s = sobren[sobren["escenari"].isin(escenaris)].groupby(["metode", "on"])["n"].sum().unstack("metode")
    t.loc["sobren a l'altre equip, per cada 100"] = 100 * s.reindex(["a l'altre equip"]).fillna(0.0).iloc[0] / totes
    return t[[A_PM, A_FS, A_FA]].rename_axis("causa")


def _regla(millor: dict[str, bool], robust: dict[str, bool]) -> list[str]:
    es = all(millor.values()) and all(robust.values())
    m = mpa._marca
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | {m(millor['quarts'])} |",
            f"| «{PARTIT}» | la diferència no és negativa | {m(millor['partit'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {m(millor['altres'])} |",
            f"| Dolent i cap | la segona part del criteri | {m(all(robust.values()))} |", "",
            f"**{A_FA} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_FA if es else A_FS}.", ""]


def _vores(triats: dict[str, Suma]) -> list[str]:
    vores = [f"{camp} = {v:g}" for camp in PARAMETRES
             for v in sorted({getattr(s, camp) for s in triats.values()})
             if v in (min(getattr(g, camp) for g in GRAELLA), max(getattr(g, camp) for g in GRAELLA))
             and not (camp == "marge_s" and all(not (s.gamma or s.delta) for s in triats.values()))]
    return [f"**A la vora de la graella:** {', '.join(vores)}." if vores else "Cap partit no tria a la vora de la graella."]


def markdown(r: dict) -> str:
    passa_tot = all(r["passa"].values()) and all(r["robust"].values())
    linies = ["# Banc obert · A fases amb la graella ampliada (T3al)", "",
              "Generat amb `uv run python -I -m banc.model_fases_amplia`. Dades obertes: 7 partits de DFL (IDSSE, CC BY",
              "4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el criteri:",
              "`docs/pla-tocs.md`, «T3al», i la capçalera de `banc/model_fases_amplia.py`. Es puntua a la veritat de toc.",
              "", f"**{XARXES_TOC}** i **{A_EQUIPS}** són els de la T3v, **{A_CREIBLE}**, el de la T3w, **{A_NETEJA}**,",
              f"el de la T3ac, **{A_PM}**, el de la T3ah, i **{A_FS}**, el de la T3ak (✓ comprovat). **{A_FA}** és {A_FS}",
              "amb la graella més ampla. ✓ Comprovat: no dona mai la D a una imatge netejada; els punts de la graella de la",
              f"T3ak hi donen exactament el mateix; {A_PM} d'aquí dona l'spellF1 de la T3ah; sense etiquetes, exactament",
              f"{A_NETEJA}; sense fases, {A_FA} és exactament {A_PM}; i on es tria el punt de la T3ak, exactament {A_FS}.",
              "", f"## Amb el nivell {MITJA}: {A_FA} contra {XARXES_TOC} (spellF1), el criteri", "",
              *t3b._taula(r["c"], A_FA, XARXES_TOC), "", *mt._criteris(r["passa"]),
              f"## Amb els nivells dolent i cap: {A_FA} contra {A_NETEJA}, la segona part del criteri", "",
              *mpa._robustesa(r["c_neteja"], r["robust"]), "",
              f"**{A_FA} {'passa' if passa_tot else 'no passa'} el criteri sencer.**", ""]
    for contra, clau in ((A_FS, "c_fs"), (A_PM, "c_pm")):
        for nivell in NIVELLS:
            linies += [f"## Amb el nivell {nivell}: {A_FA} contra {contra} (spellF1)", "",
                       *t3i._comparacio(r[clau][nivell], A_FA, contra), ""]
    if not passa_tot:
        linies += ["## No passa: és el millor fins ara?", "",
                   f"La regla de la D-50, escrita abans, contra {A_FS} amb el nivell {MITJA}, i la mateixa segona part",
                   "del criteri:", "", *_regla(r["millor"], r["robust"])]
    for (titol, contra), taula in r["altres"].items():
        linies += [f"## {titol}", "", *t3i._comparacio(taula, A_FA, contra), ""]
    linies += ["## On falla, abans i després", "",
               f"Amb el nivell {MITJA}, les causes de `banc/on_falla.py`: la part de les possessions de la veritat de",
               "cada causa, i les predites que sobren a l'altre equip per cada 100 possessions de la veritat.", ""]
    for titol, escenaris in ((CURTS, (CURTS,)), ("els quatre ×¼ junts", QUARTS_T3), ("net", ("net",))):
        linies += [f"**{titol}**", "", mv._md(taula_causes(r["causes"], r["sobrants"], escenaris), 3), ""]
    linies += ["## Les fases simulades", "",
               f"A {CURTS}, amb les llavors de provar, la mitjana dels deu partits: quantes fases, i la part de les",
               "imatges on se'n resta (dins d'una fase d'un sol equip, sense el marge triat).", "",
               mv._md(mfs.taula_fases(r["fases"]), 3), "",
               "## El punt triat", "",
               "A cada partit, amb els altres nou, als quatre ×¼ i a la mitjana dels nivells bo, mitjà i dolent; i el",
               "que hi va triar la T3ak.", "",
               "| partit | gamma | delta | marge_s | a la T3ak |", "|---|---|---|---|---|",
               *(f"| {nom} | {s.gamma:g} | {s.delta:g} | {s.marge_s:g} | "
                 f"{r['triats_t3ak'][nom].gamma:g}, {r['triats_t3ak'][nom].delta:g}, {r['triats_t3ak'][nom].marge_s:g} |"
                 for nom, s in r["triats"].items()), "",
               *_vores(r["triats"]), "",
               f"## L'spellF1 de cada mètode (mitjana dels deu partits, nivell {MITJA})", "",
               *mt._mitjanes(r["mitja"], [XARXES_TOC, A_EQUIPS, A_NETEJA, A_PM, A_FS, A_FA]), "## Els decodificadors", "",
               f"{A_NETEJA}, {A_PM}, {A_FS} i {A_FA} fan servir, a cada partit, el d'{A_EQUIPS}.", "",
               *mq._triades(r["triades"]), ""]
    return "\n".join(linies)


def clau_dels_resultats() -> str:
    h = hashlib.sha256(mfs.clau_dels_resultats().encode())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_fases_amplia as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        return list(feina.map(getattr(aquest, fes), tasques))


def de_fs(t: pd.DataFrame) -> pd.DataFrame:
    return t[t["metode"] == A_FS]


def comparacions(metodes: pd.DataFrame, tots: pd.DataFrame) -> dict:
    """Les comparacions del pla: el criteri, la segona part, el millor fins ara i les de saber-ho."""
    nomes_fa = tots[tots["metode"] == A_FA]
    c = mt.comparacio(mpa.de_nivell(metodes, nomes_fa, MITJA), A_FA, XARXES_TOC, TOC, amb_criteri=True)
    c_neteja = {n: mt.comparacio(mpa.de_nivell(metodes, nomes_fa, n), A_FA, A_NETEJA, TOC, amb_criteri=False)
                for n in NIVELLS}
    c_fs, c_pm = ({n: mt.comparacio(tots[tots["nivell"] == n].drop(columns="nivell"), A_FA, contra, TOC,
                                    amb_criteri=False) for n in NIVELLS} for contra in (A_FS, A_PM))
    mitja = mpa.de_nivell(metodes, tots, MITJA)
    altres = {(f"{A_FA} contra {contra}, nivell {MITJA}, només els partits de {font}", contra):
              mt.comparacio(mitja[mitja["font"] == font], A_FA, contra, TOC, amb_criteri=False)
              for font in mpc.FONTS for contra in (XARXES_TOC, A_FS)}
    altres[(f"{A_FA} contra {XARXES_TOC}, nivell bo", XARXES_TOC)] = mt.comparacio(
        mpa.de_nivell(metodes, nomes_fa, "bo"), A_FA, XARXES_TOC, TOC, amb_criteri=False)
    return {"c": c, "passa": mt.compleix(c), "robust": mpa.aguanta(c_neteja), "c_neteja": c_neteja, "c_fs": c_fs,
            "c_pm": c_pm, "millor": mq.millor_fins_ara(c_fs[MITJA]), "altres": altres, "mitja": mitja}


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
    a_pm, t3ak = mfs.de_la_t3ah(), de_la_t3ak()
    triats_t3ak = {nom: Suma(**s) for nom, s in t3ak["triats"].items()}
    print(f"· {XARXES} i {A_EQUIPS} donen el del banc de la T3v, {A_CREIBLE}, el de la T3w, i {A_NETEJA}, el de "
          f"la T3ac; els bancs de la T3ah i de la T3ak són d'aquest codi", flush=True)
    de_la_neteja = triades[A_EQUIPS]
    files_graella = pd.DataFrame([f for tros in en_paral_lel(
        "graella", [(nom, e, a_pm[nom], de_la_neteja[nom]) for nom, e in itertools.product(fonts.NOMS, QUARTS_T3)],
        args.processos) for f in tros])
    comprova_la_graella(files_graella, pd.DataFrame(t3ak["graella"]))
    print(f"· {A_FA}: la graella, mai la D a les imatges netejades, i als punts de la T3ak, el mateix", flush=True)
    triats = {nom: mfs.tria(files_graella, nom) for nom in fonts.NOMS}
    tasques = [(nom, e, a_pm[nom], triats[nom], de_la_neteja[nom]) for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    trossos = [reanomena(t) for t in mfs.en_paral_lel("informe", tasques, args.processos)]
    nous, causes, sobren, quantes = (pd.DataFrame([f for tros in trossos for f in tros[k]])
                                     for k in ("files", "causes", "sobrants", "fases"))
    mre.comprova_la_t3ah(nous)
    med.comprova_la_neteja(nous[nous["metode"] == A_FA], metodes)
    files_t3ak = pd.DataFrame(t3ak["files"])
    comprova_les_mateixes(nous, files_t3ak, triats, triats_t3ak)
    print(f"· {A_FA}: {A_PM} dona l'spellF1 de la T3ah; sense etiquetes, {A_NETEJA}; sense fases, {A_FA} és "
          f"exactament {A_PM}; on es tria el punt de la T3ak, {A_FS}", flush=True)
    tots = pd.concat([nous, de_fs(files_t3ak)], ignore_index=True).drop(columns=[*PARAMETRES, "neteja"])
    r = {**comparacions(metodes, tots), "causes": pd.concat([causes, de_fs(pd.DataFrame(t3ak["causes"]))]),
         "sobrants": pd.concat([sobren, de_fs(pd.DataFrame(t3ak["sobrants"]))]), "fases": quantes, "triats": triats,
         "triats_t3ak": triats_t3ak, "triades": {A_EQUIPS: de_la_neteja}}
    contingut = {"clau": clau_dels_resultats(), "passa": r["passa"], "aguanta": r["robust"],
                 "millor_fins_ara": r["millor"], "comparacio": t3.registres(r["c"]),
                 "contra_a_neteja_d_aire": {n: t3.registres(t) for n, t in r["c_neteja"].items()},
                 "contra_a_fases": {n: t3.registres(t) for n, t in r["c_fs"].items()},
                 "contra_a_pilota_morta": {n: t3.registres(t) for n, t in r["c_pm"].items()},
                 "triats": {nom: s._asdict() for nom, s in triats.items()},
                 "triades": {A_EQUIPS: de_la_neteja}, "files": t3.registres(nous),
                 "graella": t3.registres(files_graella),
                 "altres": {titol: t3.registres(t) for (titol, _), t in r["altres"].items()},
                 "causes": t3.registres(causes), "sobrants": t3.registres(sobren), "fases": t3.registres(quantes)}
    mpa.escriu("model-fases-amplia", contingut, markdown(r))


if __name__ == "__main__":
    main()
