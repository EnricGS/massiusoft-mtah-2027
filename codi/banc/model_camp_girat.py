"""Les xarxes aprenen també amb el camp girat de dalt a baix (T3ad del pla per tocs, `docs/pla-tocs.md`, «T3ad»; D-65).

    cd codi && uv run python -I -m banc.model_camp_girat [--processos 12] [--processos-models 3]

A neteja d'aire (T3ac) tal qual, amb una sola diferència: les cinc xarxes aprenen i s'apliquen també amb el camp girat
de dalt a baix (`cadena/xarxa_girada.py`).

1. **En començar:** A xarxes i A equips sencers, amb la memòria cau, han de donar a cada punt de la graella i a les dues
   veritats l'spellF1 del banc de la T3v, i A pilota creïble, el de la T3w; els decodificadors triats, els d'aquells
   bancs. A neteja d'aire, amb el decodificador d'A equips sencers, ha de donar el del banc de la T3ac. Si no, s'atura.
2. **Les xarxes noves:** les cinc de cada grup (entrenades amb els altres sis partits, per entrenar el segon) i les
   cinc del partit que es prova (amb els altres nou), amb les mostres de la T3v, la meitat girades a l'atzar, amb una
   llavor per partit i escenari. 200 xarxes (`dades/banc/camp-girat/`). Les del partit que es prova s'apliquen al
   partit netejat (`cadena/pilota_creible.py`), com a A pilota creïble.
3. **El segon,** entrenat com el d'A equips sencers (les mateixes mostres), amb les xarxes noves dels grups, i aplicat
   al partit netejat amb el primer d'A pilota creïble.
4. **El decodificador,** amb la graella de la T3j, la q d'A pilota creïble i la D impossible on la neteja ha tret la
   pilota (com a A neteja d'aire), triat amb els altres nou als quatre ×¼ a la veritat de toc. Cap punt de la graella
   no hi ha de donar la D a una imatge netejada.
5. **El criteri** del pla: A camp girat contra A xarxes, a la veritat de toc. Si no passa, la regla de la D-50 contra
   A neteja d'aire. Només per saber-ho: per font, les possessions de la veritat aparellades a 0,5 per durada, on
   encerten l'equip les xarxes i el segon, i els decodificadors triats.

Escriu `resultats/model-camp-girat.json` i `resultats/model-camp-girat.md`. Tot són dades obertes. Els mòduls d'abans no
es toquen.
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
from banc import errors_als_forats as eaf
from banc import model_a_canvis as t3i
from banc import model_a_canvis2 as t3j
from banc import model_a_context as t3e
from banc import model_a_equips as mae
from banc import model_a_partit as mp
from banc import model_a_possessio as t3f
from banc import model_a_q as mq
from banc import model_a_quart as t3b
from banc import model_a_toc as mt
from banc import model_a_xarxa as t3m
from banc import model_neteja_aire as mna
from banc import model_pilota_creible as mpc
from banc import sostre_sense_pilota as ssp
from banc import veritat_toc as vt
from cadena import model, xarxa, xarxes
from cadena import pilota_creible as pc
from cadena import xarxa_equips as xeq
from cadena import xarxa_girada as xg
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ESCENARIS = mp.ESCENARIS                            # els deu de la T3 i «partit ×¼»
SIS = mp.SIS
XARXES, XARXES_TOC, A_EQUIPS, A_CREIBLE = mpc.XARXES, mpc.XARXES_TOC, mpc.A_EQUIPS, mpc.A_CREIBLE
A_NETEJA = mna.A_NETEJA
A_GIRAT = "A camp girat"
SEMPRE, TOC = mpc.SEMPRE, mpc.TOC
FONTS = mpc.FONTS
XARXES_NETEJA, XARXES_NOVES = "xarxes d'A neteja d'aire", "xarxes noves"
SEGON_NETEJA, SEGON_NOU = "segon d'A neteja d'aire", "segon nou"
QUI = (XARXES_NETEJA, XARXES_NOVES, SEGON_NETEJA, SEGON_NOU)
ON = ("amb pilota", "sense pilota")
PER_DURADA = ("net", "curts ×¼", mp.PARTIT)         # on es comptaven les possessions aparellades per durada
DURADES = ((0.0, 1.0, "de menys d'1 s"), (1.0, 2.0, "d'1 a 2 s"), (2.0, 5.0, "de 2 a 5 s"),
           (5.0, 10.0, "de 5 a 10 s"), (10.0, np.inf, "de 10 s o més"))
LLINDAR = 0.5                                       # la IoU per aparellar-les
DIR_CAU = fonts.DIR_CAU / "camp-girat"
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


def entrena_xarxes(noms: list[str]) -> tuple[tuple[xarxa.Xarxa, ...], list[list[float]]]:
    """Com `mae.entrena_xarxes`, amb les mostres de `xarxa_girada.mostres`: les mateixes files, la meitat girades."""
    triades = {(nom, e): t3f.tria(p.veritat, avalua.trams_valids(p))
               for nom in noms for e in SIS for p in (mp.degradat(nom, e),)}
    x = np.empty((2 * sum(map(len, triades.values())), xeq.ENTRADES), np.float32)
    y = np.empty(len(x), np.int8)
    fet = 0
    for (nom, e), files in triades.items():
        p = mp.degradat(nom, e)
        x_, y_ = xg.mostres(p.tracking, p.trams, files, p.veritat[files], xg.llavor(nom, e))
        x[fet:fet + len(x_)], y[fet:fet + len(y_)] = x_, y_
        fet += len(x_)
    return xarxes.entrena(x, y)


def xarxes_del_grup(tasca: tuple[str, int], entrena: bool = True) -> dict[tuple[str, str], np.ndarray]:
    """La mitjana de les cinc xarxes noves als partits del grup `i` de `prova`, als sis escenaris d'entrenament,
    entrenades amb els altres sis partits. Allà la neteja no canvia res (T3w)."""
    prova, i = tasca
    claus = mp.claus_del_grup(prova, i, SIS)
    cami = cau("xarxes-grup", prova, i)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les xarxes noves del grup {i} de {prova}, o són d'un altre codi")
        entrenades, perdues = entrena_xarxes(t3m.per_entrenar_el_grup(prova, i))
        desat = {}
        for (nom, e), clau_ in claus.items():
            p = mp.degradat(nom, e)
            desat[clau_] = xg.probabilitats(entrenades, p.tracking, p.trams).astype(np.float32)
        desa(cami, perdues=np.array(perdues), **desat)
    return {qui: desat[nom] for qui, nom in claus.items()}


def xarxes_de_la_prova(prova: str, entrena: bool = True) -> dict[str, np.ndarray]:
    """La mitjana de les cinc xarxes noves al partit `prova` netejat, a tots els escenaris, entrenades amb els altres
    nou."""
    cami = cau("xarxes", prova)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les xarxes noves de {prova}, o són d'un altre codi")
        entrenades, perdues = entrena_xarxes([nom for nom in fonts.NOMS if nom != prova])
        desat = {}
        for i, e in enumerate(ESCENARIS):
            p = mpc.creible(prova, e)
            desat[f"e{i}"] = xg.probabilitats(entrenades, p.tracking, p.trams).astype(np.float32)
        desa(cami, perdues=np.array(perdues), **desat)
    return mpc.per_escenari(desat)


def mostres_segon(prova: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Com `mae.mostres_segon`, amb les xarxes noves dels grups."""
    primers, de_les_xarxes = {}, {}
    for i in range(t3e.GRUPS):
        primers |= mp.primer_del_grup((prova, i, SIS))
        de_les_xarxes |= xarxes_del_grup((prova, i), entrena=False)
    xs, ys = [], []
    for (nom, e), primer in primers.items():
        p = mp.degradat(nom, e)
        x, y = t3f.mostres(p, t3m.taula_segon(p, primer.astype(float), de_les_xarxes[(nom, e)].astype(float)))
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def segon(prova: str, entrena: bool = True) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Les probabilitats d'A camp girat al partit `prova` netejat, a tots els escenaris, i el prior: el segon entrenat
    com a `mae.segon`, amb les xarxes noves, i aplicat amb el primer d'A pilota creïble (`mpc.primer`)."""
    cami = cau("segon", prova)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les probabilitats del segon d'{A_GIRAT} de {prova}, o són d'un altre codi")
        x, y = mostres_segon(prova)
        entrenat, prior = model.entrena(x, y), model.prior(y)
        del x
        primers, de_les_xarxes = mpc.primer(prova, entrena=False), xarxes_de_la_prova(prova, entrena=False)
        desat = {"prior": prior}
        for i, e in enumerate(ESCENARIS):
            p = mpc.creible(prova, e)
            taula = t3m.taula_segon(p, primers[e].astype(float), de_les_xarxes[e].astype(float))
            desat[f"e{i}"] = model.probabilitats(entrenat, taula).astype(np.float32)
        desa(cami, **desat)
    return mpc.per_escenari(desat), desat["prior"]


def de_qui(metode: str, nom: str) -> tuple[dict[str, np.ndarray], np.ndarray, dict[str, np.ndarray]]:
    """Les probabilitats, el prior i la q d'A camp girat (amb la q d'A pilota creïble), o les d'A xarxes, A equips
    sencers o A pilota creïble (`mpc.de_qui`)."""
    if metode != A_GIRAT:
        return mpc.de_qui(metode, nom)
    probes, prior = segon(nom, entrena=False)
    return probes, prior, mpc.q(nom, entrena=False)


def relativa(metode: str, nom: str, escenari: str, netejades: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """La probabilitat relativa amb la D impossible a les imatges `netejades`, i la q: d'A camp girat, o d'A neteja
    d'aire amb les peces d'A pilota creïble."""
    probes, prior, q_ = de_qui(A_CREIBLE if metode == A_NETEJA else metode, nom)
    r = log_relativa(probes[escenari].astype(float), prior)
    return mna.amb_la_d_impossible(r, netejades), q_[escenari]


def graella(tasca: tuple[str, str]) -> list[dict]:
    """Un partit i un escenari: cada punt de la graella de la T3j d'A camp girat, puntuat a les dues veritats. S'atura
    si a cap punt hi dona la D a una imatge netejada."""
    nom, escenari = tasca
    de_sempre = mp.degradat(nom, escenari)
    partits = {SEMPRE: de_sempre, TOC: replace(de_sempre, veritat=vt.veritat(nom))}
    netejades = pc.lluny(de_sempre.tracking)
    r, q_ = relativa(A_GIRAT, nom, escenari, netejades)
    files = []
    for w, lam, d_min in itertools.product(t3j.WS, t3j.LAMS, t3j.DMINS):
        pred = t3i.per_trams(r, q_.astype(float), de_sempre.trams, w, lam, d_min)
        if (pred[netejades] == pm.D).any():
            raise RuntimeError(f"{nom}, {escenari}, {(w, lam, d_min)}: {A_GIRAT} dona la D a una imatge netejada")
        for veritat, p in partits.items():
            files.append({"partit": nom, "font": p.font, "escenari": escenari, "metode": A_GIRAT, "veritat": veritat,
                          "w": w, "lam": lam, "d_min": d_min, **avalua.puntua(p, pred)})
    return files


def per_durada(toc: np.ndarray, pred: np.ndarray, trams: list[tuple[int, int]]) -> list[dict]:
    """Les possessions de la veritat, per durada: quantes n'hi ha, i quantes s'aparellen amb una de la predicció a la
    IoU `LLINDAR`, com a l'spellF1 (la predicció amb les abstencions omplertes, i cadascuna amb una de sola)."""
    ple = pm.fill_abstentions(pred.astype(np.int8), trams)
    de_la_veritat = pm.possession_spells(toc.astype(np.int8), trams)
    parelles = pm.spell_overlaps(de_la_veritat, pm.possession_spells(ple, trams))
    fetes = pm.matched_gt_flags(parelles, len(de_la_veritat), LLINDAR)
    durada = np.array([(b - a) / pm.FPS for a, b, _ in de_la_veritat])
    return [{"durada": nom, "n": int(m.sum()), "aparellades": int((fetes & m).sum())}
            for de, fins, nom in DURADES for m in ((durada >= de) & (durada < fins),)]


def informe(tasca: tuple[str, str, dict[str, tuple]]) -> dict[str, list[dict]]:
    """Un partit i un escenari, a la veritat de toc: on encerten l'equip les xarxes i el segon d'A neteja d'aire i els
    nous, amb pilota i sense, i, als escenaris de `PER_DURADA`, les possessions aparellades per durada de cadascun,
    amb el seu decodificador (`triats`)."""
    nom, escenari, triats = tasca
    de_sempre = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    trams = avalua.trams_valids(replace(de_sempre, veritat=toc))
    valides = ssp.dins(len(toc), trams)
    vista = ~np.isnan(mpc.creible(nom, escenari).tracking.pilota[:, 0])
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}
    probes = {XARXES_NETEJA: mpc.xarxes_de_la_prova(nom, entrena=False)[escenari].astype(float),
              XARXES_NOVES: xarxes_de_la_prova(nom, entrena=False)[escenari].astype(float)}
    for qui, metode in ((SEGON_NETEJA, A_CREIBLE), (SEGON_NOU, A_GIRAT)):
        de_l_un, prior, _ = de_qui(metode, nom)
        probes[qui] = log_relativa(de_l_un[escenari].astype(float), prior)
    encerts_ = []
    for on, mascara in zip(ON, (vista, ~vista)):
        for qui in QUI:
            n, e = ssp.encerts(probes[qui], toc, mascara & valides)
            encerts_.append({**comu, "on": on, "qui": qui, "n": n, "encerts": e})
    durades = []
    if escenari in PER_DURADA:
        netejades = pc.lluny(de_sempre.tracking)
        for metode, triat in triats.items():
            r, q_ = relativa(metode, nom, escenari, netejades)
            pred = mna.prediccio(r, q_, de_sempre.trams, triat)
            durades += [{**comu, "metode": metode, **f} for f in per_durada(toc, pred, trams)]
    return {"encerts": encerts_, "durades": durades}


def comprova_la_t3ac(fixes_: pd.DataFrame) -> None:
    """A neteja d'aire (i la neteja sola), amb el decodificador d'A equips sencers, dona a cada partit, escenari i
    veritat l'spellF1 del banc de la T3ac."""
    banc = pd.DataFrame(json.loads((DIR_RESULTATS / "model-neteja-aire.json").read_text())["files"])
    aqui = fixes_[[*mna.CLAUS, "spell_f1"]]
    junts = aqui.merge(banc[[*mna.CLAUS, "spell_f1"]], on=mna.CLAUS, suffixes=("", " del banc"), how="outer")
    if (len(junts) != len(aqui) or len(aqui) != len(banc) or junts.isna().any().any()
            or not np.allclose(junts["spell_f1"], junts["spell_f1 del banc"], rtol=0, atol=1e-12)):
        raise RuntimeError(f"{A_NETEJA} no dona el del banc de la T3ac")


def taula_durades(t: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i durada: quantes possessions de la veritat hi ha per partit, i la part aparellada de cadascú."""
    g = t.groupby(["escenari", "durada", "metode"], sort=False)[["n", "aparellades"]].sum()
    part = (g["aparellades"] / g["n"]).unstack("metode")[[A_NETEJA, A_GIRAT]].add_prefix("aparellades · ")
    n = (g["n"].xs(A_GIRAT, level="metode") / t["partit"].nunique()).rename("n per partit")
    return eaf.en_ordre(pd.concat([n, part], axis=1), PER_DURADA, [nom for _, _, nom in DURADES])


def taula_encerts(t: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i on: quantes imatges hi ha d'un equip, i la part on cadascú hi encerta l'equip."""
    g = t.groupby(["escenari", "on", "qui"], sort=False)[["n", "encerts"]].sum()
    part = (g["encerts"] / g["n"]).unstack("qui")[list(QUI)]
    n = g["n"].xs(SEGON_NOU, level="qui").rename("n imatges")
    return eaf.en_ordre(pd.concat([n, part], axis=1), ESCENARIS, ON)


def _regla(millor: dict[str, bool]) -> list[str]:
    es = all(millor.values())
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | "
            f"{mq._marca(millor['quarts'])} |",
            f"| «{mp.PARTIT}» | la diferència no és negativa | {mq._marca(millor['partit'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {mq._marca(millor['altres'])} |",
            "", f"**{A_GIRAT} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_GIRAT if es else A_NETEJA}.", ""]


def markdown(metodes: pd.DataFrame, triades: dict, c: pd.DataFrame, passa: dict[str, bool], c_neteja: pd.DataFrame,
             millor: dict[str, bool], per_font: dict[tuple[str, str], pd.DataFrame], durades: pd.DataFrame,
             encerts_: pd.DataFrame) -> str:
    linies = ["# Banc obert · Les xarxes aprenen també amb el camp girat de dalt a baix (T3ad)", "",
              "Generat amb `uv run python -I -m banc.model_camp_girat`. Dades obertes: 7 partits de DFL (IDSSE, CC BY",
              "4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3ad», i la capçalera de `banc/model_camp_girat.py`. Es puntua a la",
              "veritat de toc.", "",
              f"**{XARXES_TOC}** i **{A_EQUIPS}** són els de la T3v, **{A_CREIBLE}**, el de la T3w, i **{A_NETEJA}**,",
              "el de la T3ac, amb les peces de la memòria cau (✓ comprovat: donen l'spellF1 d'aquells bancs, i els",
              f"decodificadors triats són els seus). **{A_GIRAT}** és {A_NETEJA}, amb les cinc xarxes que aprenen i",
              "s'apliquen també amb el camp girat de dalt a baix, i el decodificador triat de nou. ✓ Comprovat a cada",
              "punt de la graella: no dona mai la D a una imatge netejada.", "",
              f"## {A_GIRAT} contra {XARXES_TOC} (spellF1): el criteri", "",
              *t3b._taula(c, A_GIRAT, XARXES_TOC), "", *mt._criteris(passa),
              f"## {A_GIRAT} contra {A_NETEJA} (spellF1)", "", *t3i._comparacio(c_neteja, A_GIRAT, A_NETEJA), ""]
    if not all(passa.values()):
        linies += ["## No passa: és el millor fins ara?", "",
                   f"La regla de la D-50, escrita abans, contra {A_NETEJA}:", "", *_regla(millor)]
    for (font, contra), taula in per_font.items():
        linies += [f"## {A_GIRAT} contra {contra}, només els partits de {font}", "",
                   *t3i._comparacio(taula, A_GIRAT, contra), ""]
    linies += ["## Les possessions de la veritat aparellades, per durada", "",
               f"Les possessions de la veritat de toc, i la part que s'aparella amb una de la predicció a la IoU {LLINDAR}",
               "(com a l'spellF1), de cada mètode amb el seu decodificador.", "",
               t3p.md(taula_durades(durades)), "",
               "## On encerten l'equip les xarxes i el segon", "",
               "On la veritat de toc és d'un equip, la part de les imatges on l'equip més probable és el bo (les",
               "xarxes, amb les seves probabilitats; el segon, amb la relativa). Amb pilota i sense, al partit netejat.",
               "", t3p.md(taula_encerts(encerts_[encerts_["escenari"].isin(mp.QUARTS)])), "",
               "## L'spellF1 de cada mètode (mitjana dels deu partits)", "",
               *mt._mitjanes(metodes, [XARXES_TOC, A_EQUIPS, A_NETEJA, A_GIRAT]), "## Els decodificadors triats", "",
               f"{A_NETEJA} fa servir, a cada partit, el d'{A_EQUIPS}.", "", *mq._triades(triades), ""]
    return "\n".join(linies)


def clau() -> str:
    """El que fa les probabilitats d'aquí: les peces d'A pilota creïble i d'A equips sencers, el camp girat i això."""
    h = hashlib.sha256((mpc.CLAU + mae.CLAU + mp.CLAU + repr((SIS, ESCENARIS, xarxes.LLAVORS, model.RONDES,
                                                               model.PAS))).encode())
    h.update(Path(xg.__file__).read_bytes())
    for funcio in (entrena_xarxes, xarxes_del_grup, xarxes_de_la_prova, mostres_segon, segon):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + vt.CLAU + mna.clau_dels_resultats()).encode())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_camp_girat as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        return list(feina.map(getattr(aquest, fes), tasques))


def entrena_les_peces(processos: int) -> None:
    """Les xarxes dels grups, les dels partits i el segon de cada partit."""
    from banc import model_camp_girat as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        grups = [(nom, i) for nom in fonts.NOMS for i in range(t3e.GRUPS)]
        for k, ((nom, i), _) in enumerate(zip(grups, feina.map(aquest.xarxes_del_grup, grups)), start=1):
            print(f"· {k}/{len(grups)}: les xarxes noves del grup {i} de {nom}", flush=True)
        for k, (nom, _) in enumerate(zip(fonts.NOMS, feina.map(aquest.xarxes_de_la_prova, fonts.NOMS)), start=1):
            print(f"· {k}/{len(fonts.NOMS)}: les xarxes noves de {nom}", flush=True)
        for k, (nom, _) in enumerate(zip(fonts.NOMS, feina.map(aquest.segon, fonts.NOMS)), start=1):
            print(f"· {k}/{len(fonts.NOMS)}: el segon d'{A_GIRAT} de {nom}", flush=True)


def escriu(contingut: dict, md: str) -> None:
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-camp-girat.json").write_text(json.dumps(contingut, indent=1, default=float,
                                                                    allow_nan=False))
    (DIR_RESULTATS / "model-camp-girat.md").write_text(md)
    print(md)


def comprova_les_d_abans(processos: int) -> tuple[pd.DataFrame, dict]:
    """El pas 1: les files d'A xarxes i d'A equips sencers amb el seu decodificador triat, els decodificadors triats i
    les files d'A neteja d'aire, comprovat tot contra els bancs de la T3v, la T3w i la T3ac."""
    files = mpc.files_de((XARXES, A_EQUIPS, A_CREIBLE), processos)
    mpc.comprova_les_d_abans(files)
    mna.comprova_la_t3w(files)
    de_xarxes, triades_xarxes = mt.tria_sense_mirar(files, XARXES, TOC, XARXES_TOC)
    de_equips, triades_equips = mt.tria_sense_mirar(files, A_EQUIPS, TOC, A_EQUIPS)
    _, triades_creible = mt.tria_sense_mirar(files, A_CREIBLE, TOC, A_CREIBLE)
    mna.comprova_les_triades({XARXES_TOC: triades_xarxes, A_EQUIPS: triades_equips, A_CREIBLE: triades_creible})
    tasques = [(nom, e, triades_equips[nom]) for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    fixes_ = pd.DataFrame([f for tros in mna.en_paral_lel("fixes", tasques, processos) for f in tros["files"]])
    comprova_la_t3ac(fixes_)
    metodes = pd.concat([de_xarxes, de_equips, fixes_[fixes_["metode"] == A_NETEJA]], ignore_index=True)
    return metodes, {XARXES_TOC: triades_xarxes, A_EQUIPS: triades_equips}


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
    metodes, triades = comprova_les_d_abans(args.processos)
    print(f"· {XARXES} i {A_EQUIPS} donen el del banc de la T3v, {A_CREIBLE}, el de la T3w, i {A_NETEJA}, el de "
          "la T3ac", flush=True)
    entrena_les_peces(args.processos_models)
    files = pd.DataFrame([f for tros in en_paral_lel("graella", list(itertools.product(fonts.NOMS, ESCENARIS)),
                                                     args.processos) for f in tros])
    print(f"· {A_GIRAT}: mai la D a les imatges netejades, a cap punt de la graella", flush=True)
    de_girat, triades[A_GIRAT] = mt.tria_sense_mirar(files, A_GIRAT, TOC, A_GIRAT)
    metodes = pd.concat([metodes, de_girat], ignore_index=True)
    c = mt.comparacio(metodes, A_GIRAT, XARXES_TOC, TOC, amb_criteri=True)
    c_neteja = mt.comparacio(metodes, A_GIRAT, A_NETEJA, TOC, amb_criteri=False)
    passa, millor = mt.compleix(c), mq.millor_fins_ara(c_neteja)
    per_font = {(font, contra): mt.comparacio(metodes[metodes["font"] == font], A_GIRAT, contra, TOC,
                                              amb_criteri=False)
                for font in FONTS for contra in (XARXES_TOC, A_NETEJA)}
    tasques = [(nom, e, {A_NETEJA: triades[A_EQUIPS][nom], A_GIRAT: triades[A_GIRAT][nom]})
               for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    trossos = en_paral_lel("informe", tasques, args.processos)
    encerts_, durades = (pd.DataFrame([f for tros in trossos for f in tros[clau_]]) for clau_ in ("encerts", "durades"))
    contingut = {"clau": clau_dels_resultats(), "passa": passa, "millor_fins_ara": millor,
                 "comparacio": t3.registres(c), "contra_a_neteja_d_aire": t3.registres(c_neteja), "triades": triades,
                 "files": t3.registres(files),
                 "per_font": {f"{font} · {contra}": t3.registres(t) for (font, contra), t in per_font.items()},
                 "durades": t3.registres(durades), "encerts": t3.registres(encerts_)}
    escriu(contingut, markdown(metodes, triades, c, passa, c_neteja, millor, per_font, durades, encerts_))


if __name__ == "__main__":
    main()
