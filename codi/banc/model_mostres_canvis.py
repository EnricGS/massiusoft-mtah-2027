"""Les xarxes aprenen més a prop dels canvis (T3z del pla per tocs, `docs/pla-tocs.md`, «T3z»; D-58).

    cd codi && uv run python -I -m banc.model_mostres_canvis [--processos 12] [--processos-models 3]
                                                             [--processos-models-prova 2]

A equips sencers tal qual, amb una sola diferència: les mostres de les cinc xarxes també tenen una de cada dues imatges
a ±0,5 s de cada canvi d'equip de la veritat d'entrenament (`tria`).

1. **En començar,** A xarxes i A equips sencers, amb la memòria cau, han de donar a cada punt de la graella i a les dues
   veritats l'spellF1 del banc de la T3v.
2. **Les xarxes noves:** les cinc de cada grup (entrenades amb els altres sis partits, per entrenar el segon) i les
   cinc del partit que es prova (amb els altres nou), com a `mae`, amb les mostres d'aquí. 200 xarxes
   (`dades/banc/mostres-canvis/`). Les del partit que es prova aprenen amb nou partits, i per la memòria se'n fan menys
   alhora (`--processos-models-prova`); no canvia cap resultat.
3. **El segon,** entrenat com el d'A equips sencers (les mateixes mostres), amb les probabilitats de les xarxes noves.
4. **El decodificador,** amb la graella de la T3j, triat amb els altres nou als quatre ×¼ a la veritat de toc.
5. **El criteri** del pla: A mostres als canvis contra A xarxes, a la veritat de toc. Si no passa, la regla de la D-50
   contra A equips sencers. Només per saber-ho: per font, la part dels errors d'equip a prop dels canvis, on encerten
   l'equip les xarxes i el segon, els canvis falsos i els decodificadors triats.

Escriu `resultats/model-mostres-canvis.json` i `resultats/model-mostres-canvis.md`. Tot són dades obertes. Els mòduls
d'abans no es toquen.
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
from banc import model_a_canvis as t3i
from banc import model_a_canvis2 as t3j
from banc import model_a_context as t3e
from banc import model_a_equips as mae
from banc import model_a_partit as mp
from banc import model_a_possessio as t3f
from banc import model_a_q as mq
from banc import model_a_quart as t3b
from banc import model_a_sense_pilota as msp
from banc import model_a_toc as mt
from banc import model_a_xarxa as t3m
from banc import model_pilota_creible as mpc
from banc import sostre_curtes as sc
from banc import sostre_sense_pilota as ssp
from banc import veritat_toc as vt
from banc.partit import PartitBanc
from cadena import model, xarxa, xarxes
from cadena import xarxa_equips as xeq
from possessio.decodificacio import log_relativa

ESCENARIS = mp.ESCENARIS                            # els deu de la T3 i «partit ×¼»
SIS = mp.SIS
XARXES, XARXES_TOC, A_EQUIPS = mae.XARXES, mae.XARXES_TOC, mae.A_EQUIPS
SEMPRE, TOC = mae.SEMPRE, mae.TOC
A_CANVIS = "A mostres als canvis"
FONTS = mae.FONTS
K = 12                                              # ±0,5 s
CADA = 2                                            # una de cada dues imatges
K_LLUNY = 25                                        # ±1 s, només per a l'informe
A_PROP, LLUNY = "a ±0,5 s d'un canvi", "a la resta"
ON = tuple(f"{on}, {pilota}" for on in (A_PROP, LLUNY) for pilota in ("amb pilota", "sense pilota"))
XARXES_EQUIPS, XARXES_NOVES = f"les xarxes d'{A_EQUIPS}", "les xarxes noves"
SEGON_EQUIPS, SEGON_NOU = f"el segon d'{A_EQUIPS}", "el segon nou"
QUI = (XARXES_EQUIPS, XARXES_NOVES, SEGON_EQUIPS, SEGON_NOU)
DIR_CAU = fonts.DIR_CAU / "mostres-canvis"
DIR_RESULTATS = t3.DIR_RESULTATS


def canvis(veritat: np.ndarray, parts: tuple[tuple[int, int, int], ...]) -> np.ndarray:
    """La primera imatge de l'equip nou a cada canvi d'equip (de l'H a l'A o de l'A a l'H) de dins de cada part, sense
    comptar la D ni la X entremig."""
    out = [np.zeros(0, int)]
    for _, inici, ultim in parts:
        v = veritat[inici:ultim + 1]
        j = np.flatnonzero(np.isin(v, ssp.EQUIPS))
        out.append(inici + j[1:][v[j[1:]] != v[j[:-1]]])
    return np.concatenate(out)


def imatges_noves(veritat: np.ndarray, parts: tuple[tuple[int, int, int], ...],
                  trams: list[tuple[int, int]]) -> np.ndarray:
    """Una de cada `CADA` imatges a ±`K` de cada canvi, dins dels trams vàlids i amb la veritat H, A o D, en ordre i
    sense repetir-ne cap."""
    j = np.unique((canvis(veritat, parts)[:, None] + np.arange(-K, K + 1, CADA)).ravel())
    j = j[(j >= 0) & (j < len(veritat))]
    return j[ssp.dins(len(veritat), trams)[j] & np.isin(veritat[j], model.CLASSES)]


def tria(p: PartitBanc) -> np.ndarray:
    """Les imatges que aprenen les xarxes: la tria de la T3f i les noves, en ordre i sense repetir-ne cap."""
    trams = avalua.trams_valids(p)
    return np.union1d(t3f.tria(p.veritat, trams), imatges_noves(p.veritat, p.trams, trams))


def a_prop(veritat: np.ndarray, parts: tuple[tuple[int, int, int], ...], k: int) -> np.ndarray:
    """Les imatges a `k` o menys d'un canvi d'equip (`canvis`)."""
    out = np.zeros(len(veritat), bool)
    for c in canvis(veritat, parts):
        out[max(c - k, 0):c + k + 1] = True
    return out


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
    """Com `mae.entrena_xarxes`, amb les imatges de `tria`."""
    triades = {(nom, e): tria(mp.degradat(nom, e)) for nom in noms for e in SIS}
    x = np.empty((2 * sum(map(len, triades.values())), xeq.ENTRADES), np.float32)
    y = np.empty(len(x), np.int8)
    fet = 0
    for (nom, e), files in triades.items():
        p = mp.degradat(nom, e)
        x_, y_ = xeq.mostres(p.tracking, p.trams, files, p.veritat[files])
        x[fet:fet + len(x_)], y[fet:fet + len(y_)] = x_, y_
        fet += len(x_)
    return xarxes.entrena(x, y)


def xarxes_del_grup(tasca: tuple[str, int], entrena: bool = True) -> dict[tuple[str, str], np.ndarray]:
    """Com `mae.xarxes_del_grup`, amb les xarxes d'aquí."""
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
            desat[clau_] = xeq.probabilitats(entrenades, p.tracking, p.trams).astype(np.float32)
        desa(cami, perdues=np.array(perdues), **desat)
    return {qui: desat[nom] for qui, nom in claus.items()}


def xarxes_de_la_prova(prova: str, entrena: bool = True) -> dict[str, np.ndarray]:
    """Com `mae.xarxes_de_la_prova`, amb les xarxes d'aquí."""
    cami = cau("xarxes", prova)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les xarxes noves de {prova}, o són d'un altre codi")
        entrenades, perdues = entrena_xarxes([nom for nom in fonts.NOMS if nom != prova])
        desat = {}
        for i, e in enumerate(ESCENARIS):
            p = mp.degradat(prova, e)
            desat[f"e{i}"] = xeq.probabilitats(entrenades, p.tracking, p.trams).astype(np.float32)
        desa(cami, perdues=np.array(perdues), **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(ESCENARIS)}


def mostres_segon(prova: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Com `mae.mostres_segon`, amb les xarxes d'aquí."""
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
    """Les probabilitats d'A mostres als canvis al partit `prova`, a tots els escenaris, i el prior: com `mae.segon`,
    amb les xarxes d'aquí. Amb `entrena=False`, només les llegeix de la memòria cau."""
    cami = cau("segon", prova)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les probabilitats del segon d'{A_CANVIS} de {prova}, o són d'un altre codi")
        x, y = mostres_segon(prova)
        entrenat, prior = model.entrena(x, y), model.prior(y)
        del x
        primers = mp.primer_de_la_prova((prova, SIS))
        de_les_xarxes = xarxes_de_la_prova(prova, entrena=False)
        desat = {"prior": prior}
        for i, e in enumerate(ESCENARIS):
            p = mp.degradat(prova, e)
            taula = t3m.taula_segon(p, primers[e].astype(float), de_les_xarxes[e].astype(float))
            desat[f"e{i}"] = model.probabilitats(entrenat, taula).astype(np.float32)
        desa(cami, **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(ESCENARIS)}, desat["prior"]


def de_qui(metode: str, nom: str) -> tuple[dict[str, np.ndarray], np.ndarray, dict[str, np.ndarray]]:
    """Les probabilitats, el prior i la q d'A mostres als canvis (amb la q d'A xarxes, com A equips sencers), o les
    d'A xarxes o A equips sencers (`mae.de_qui`)."""
    if metode != A_CANVIS:
        return mae.de_qui(metode, nom)
    probes, prior = segon(nom, entrena=False)
    return probes, prior, mp.q((nom, SIS), entrena=False)


def graella(tasca: tuple[str, str, tuple[str, ...]]) -> list[dict]:
    """Com `mae.graella`, amb A mostres als canvis també."""
    nom, escenari, metodes = tasca
    de_sempre = mp.degradat(nom, escenari)
    partits = {SEMPRE: de_sempre, TOC: replace(de_sempre, veritat=vt.veritat(nom))}
    files = []
    for metode in metodes:
        probes, prior, q_ = de_qui(metode, nom)
        relativa = log_relativa(probes[escenari].astype(float), prior)
        for w, lam, d_min in itertools.product(t3j.WS, t3j.LAMS, t3j.DMINS):
            pred = t3i.per_trams(relativa, q_[escenari].astype(float), de_sempre.trams, w, lam, d_min)
            for veritat, p in partits.items():
                files.append({"partit": nom, "font": p.font, "escenari": escenari, "metode": metode,
                              "veritat": veritat, "w": w, "lam": lam, "d_min": d_min, **avalua.puntua(p, pred)})
    return files


def encerts(tasca: tuple[str, str, dict[str, tuple]]) -> dict[str, list[dict]]:
    """Un partit i un escenari, amb el decodificador triat de cada mètode, a la veritat de toc: quants errors d'equip
    són a prop dels canvis, on encerten l'equip les xarxes i el segon, i els canvis falsos de cada predicció."""
    nom, escenari, triats = tasca
    de_sempre = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    trams = avalua.trams_valids(replace(de_sempre, veritat=toc))
    valides = ssp.dins(len(toc), trams)
    vista = ~np.isnan(de_sempre.tracking.pilota[:, 0])
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}
    probes = {XARXES_EQUIPS: mae.xarxes_de_la_prova(nom, entrena=False)[escenari].astype(float),
              XARXES_NOVES: xarxes_de_la_prova(nom, entrena=False)[escenari].astype(float)}
    preds = {}
    for metode, qui in ((A_EQUIPS, SEGON_EQUIPS), (A_CANVIS, SEGON_NOU)):
        de_l_un, prior, q_ = de_qui(metode, nom)
        probes[qui] = log_relativa(de_l_un[escenari].astype(float), prior)
        w, lam, d_min = triats[metode]
        preds[metode] = t3i.per_trams(probes[qui], q_[escenari].astype(float), de_sempre.trams, w, lam, int(d_min))
    equip = valides & np.isin(toc, ssp.EQUIPS)
    errors = []
    for k, a in ((K, "±0,5 s"), (K_LLUNY, "±1 s")):
        prop = a_prop(toc, de_sempre.trams, k)
        for metode, pred in preds.items():
            error = equip & (pred != toc)
            errors.append({**comu, "a": a, "metode": metode, "errors": int(error.sum()),
                           "a prop": int((error & prop).sum())})
    prop = a_prop(toc, de_sempre.trams, K)
    mascares = dict(zip(ON, (prop & vista, prop & ~vista, ~prop & vista, ~prop & ~vista)))
    files = []
    for on, mascara in mascares.items():
        for qui in QUI:
            n, e = ssp.encerts(probes[qui], toc, mascara & valides)
            files.append({**comu, "on": on, "qui": qui, "n": n, "encerts": e})
    al_forat = sc.forats(vista)
    canvis_ = [{**comu, "metode": metode, **msp.falsos(pred, toc, trams, al_forat)} for metode, pred in preds.items()]
    return {"errors": errors, "encerts": files, "canvis": canvis_}


def taula_errors(t: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i distància: els errors d'equip de cada mètode, i la part que és a prop d'un canvi."""
    g = t.groupby(["escenari", "a", "metode"], sort=False)[["errors", "a prop"]].sum()
    part = (g["a prop"] / g["errors"]).unstack("metode")[[A_EQUIPS, A_CANVIS]]
    n = g["errors"].unstack("metode")[[A_EQUIPS, A_CANVIS]]
    taula = pd.concat([n.add_prefix("n errors, "), part.add_prefix("a prop, ")], axis=1)
    ordre = {**{e: i for i, e in enumerate(ESCENARIS)}, "±0,5 s": 0, "±1 s": 1}
    return taula.sort_index(key=lambda idx: idx.map(lambda x: ordre.get(x, len(ordre))))


def taula_encerts(t: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i on: quantes imatges hi ha d'un equip, i la part on cadascú hi encerta l'equip."""
    g = t.groupby(["escenari", "on", "qui"], sort=False)[["n", "encerts"]].sum()
    part = (g["encerts"] / g["n"]).unstack("qui")[list(QUI)]
    n = g["n"].xs(SEGON_NOU, level="qui").rename("n imatges")
    ordre = {**{e: i for i, e in enumerate(ESCENARIS)}, **{o: i for i, o in enumerate(ON)}}
    return pd.concat([n, part], axis=1).sort_index(key=lambda idx: idx.map(lambda x: ordre.get(x, len(ordre))))


def _regla(millor: dict[str, bool]) -> list[str]:
    es = all(millor.values())
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | "
            f"{mq._marca(millor['quarts'])} |",
            f"| «{mp.PARTIT}» | la diferència no és negativa | {mq._marca(millor['partit'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {mq._marca(millor['altres'])} |",
            "", f"**{A_CANVIS} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_CANVIS if es else A_EQUIPS}.", ""]


def markdown(metodes: pd.DataFrame, triades: dict, c: pd.DataFrame, passa: dict[str, bool], c_equips: pd.DataFrame,
             millor: dict[str, bool], per_font: dict[tuple[str, str], pd.DataFrame], errors_: pd.DataFrame,
             encerts_: pd.DataFrame, canvis_: pd.DataFrame) -> str:
    quarts = encerts_["escenari"].isin(mp.QUARTS)
    linies = ["# Banc obert · Les xarxes aprenen més a prop dels canvis (T3z)", "",
              "Generat amb `uv run python -I -m banc.model_mostres_canvis`. Dades obertes: 7 partits de DFL (IDSSE, CC",
              "BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3z», i la capçalera de `banc/model_mostres_canvis.py`. Es puntua a la",
              "veritat de toc.", "",
              f"**{XARXES_TOC}** i **{A_EQUIPS}** són els de la T3v, amb les peces de la memòria cau (✓ comprovat: a",
              f"cada punt de la graella donen l'spellF1 del banc de la T3v). **{A_CANVIS}** és {A_EQUIPS}, amb les",
              f"xarxes que també aprenen una de cada {CADA} imatges a ±0,5 s de cada canvi d'equip.", "",
              f"## {A_CANVIS} contra {XARXES_TOC} (spellF1): el criteri", "",
              *t3b._taula(c, A_CANVIS, XARXES_TOC), "", *mt._criteris(passa),
              f"## {A_CANVIS} contra {A_EQUIPS} (spellF1)", "", *t3i._comparacio(c_equips, A_CANVIS, A_EQUIPS), ""]
    if not all(passa.values()):
        linies += ["## No passa: és el millor fins ara?", "",
                   f"La regla de la D-50, escrita abans, contra {A_EQUIPS}:", "", *_regla(millor)]
    for (font, contra), taula in per_font.items():
        linies += [f"## {A_CANVIS} contra {contra}, només els partits de {font}", "",
                   *t3i._comparacio(taula, A_CANVIS, contra), ""]
    linies += ["## Els errors d'equip a prop dels canvis", "",
               "On la veritat de toc és d'un equip i la predicció no hi encerta l'equip: quants n'hi ha, i la part a",
               "±0,5 s i a ±1 s d'un canvi d'equip de la veritat de toc.", "",
               t3p.md(taula_errors(errors_[errors_["escenari"].isin(mp.QUARTS)])), "",
               "## On encerten l'equip les xarxes i el segon", "",
               "On la veritat de toc és d'un equip, la part de les imatges on l'equip més probable és el bo (les",
               "xarxes, amb les seves probabilitats; el segon, amb la relativa).", "",
               t3p.md(taula_encerts(encerts_[quarts])), "",
               "## Els canvis d'equip de la predicció, i quants són falsos", "",
               f"Un canvi és fals si no n'hi ha cap de real a {msp.an.TOL} imatges o menys.", "",
               t3p.md(msp.taula_canvis(canvis_)), "",
               "## L'spellF1 de cada mètode (mitjana dels deu partits)", "",
               *mt._mitjanes(metodes, [XARXES_TOC, A_EQUIPS, A_CANVIS]), "## Els decodificadors triats", "",
               *mq._triades(triades), ""]
    return "\n".join(linies)


def clau() -> str:
    """El que fa les probabilitats d'aquí: les peces d'A equips sencers, les mostres noves i això."""
    h = hashlib.sha256((mae.CLAU + mp.CLAU + repr((SIS, ESCENARIS, K, CADA, model.RONDES, model.PAS))).encode())
    for funcio in (canvis, imatges_noves, tria, entrena_xarxes, xarxes_del_grup, xarxes_de_la_prova, mostres_segon,
                   segon):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + vt.CLAU + mae.clau_dels_resultats()).encode())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_mostres_canvis as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        return list(feina.map(getattr(aquest, fes), tasques))


def entrena_les_peces(processos: int, processos_prova: int) -> None:
    """Les xarxes dels grups, les dels partits (amb nou partits cadascuna, menys alhora) i el segon de cada partit."""
    from banc import model_mostres_canvis as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        grups = [(nom, i) for nom in fonts.NOMS for i in range(t3e.GRUPS)]
        for k, ((nom, i), _) in enumerate(zip(grups, feina.map(aquest.xarxes_del_grup, grups)), start=1):
            print(f"· {k}/{len(grups)}: les xarxes noves del grup {i} de {nom}", flush=True)
    with ProcessPoolExecutor(max_workers=processos_prova) as feina:
        for k, (nom, _) in enumerate(zip(fonts.NOMS, feina.map(aquest.xarxes_de_la_prova, fonts.NOMS)), start=1):
            print(f"· {k}/{len(fonts.NOMS)}: les xarxes noves de {nom}", flush=True)
    with ProcessPoolExecutor(max_workers=processos) as feina:
        for k, (nom, _) in enumerate(zip(fonts.NOMS, feina.map(aquest.segon, fonts.NOMS)), start=1):
            print(f"· {k}/{len(fonts.NOMS)}: el segon d'{A_CANVIS} de {nom}", flush=True)


def files_de(metodes: tuple[str, ...], processos: int) -> pd.DataFrame:
    tasques = [(nom, e, metodes) for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    return pd.DataFrame([f for tros in en_paral_lel("graella", tasques, processos) for f in tros])


def escriu(contingut: dict, md: str) -> None:
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-mostres-canvis.json").write_text(json.dumps(contingut, indent=1, default=float,
                                                                        allow_nan=False))
    (DIR_RESULTATS / "model-mostres-canvis.md").write_text(md)
    print(md)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=3, help="models alhora")
    ap.add_argument("--processos-models-prova", type=int, default=2, help="xarxes dels partits alhora")
    args = ap.parse_args()
    for nom in fonts.NOMS:
        for metode in (XARXES, A_EQUIPS):
            mae.de_qui(metode, nom)
        mae.xarxes_de_la_prova(nom, entrena=False)
        vt.veritat(nom)
    files = files_de((XARXES, A_EQUIPS), args.processos)
    mpc.comprova_les_d_abans(files)
    print(f"· {XARXES} i {A_EQUIPS} donen el del banc de la T3v", flush=True)
    entrena_les_peces(args.processos_models, args.processos_models_prova)
    files = pd.concat([files, files_de((A_CANVIS,), args.processos)], ignore_index=True)
    de_xarxes, triades_xarxes = mt.tria_sense_mirar(files, XARXES, TOC, XARXES_TOC)
    de_equips, triades_equips = mt.tria_sense_mirar(files, A_EQUIPS, TOC, A_EQUIPS)
    de_canvis, triades_canvis = mt.tria_sense_mirar(files, A_CANVIS, TOC, A_CANVIS)
    triades = {XARXES_TOC: triades_xarxes, A_EQUIPS: triades_equips, A_CANVIS: triades_canvis}
    mpc.comprova_les_triades(triades)
    metodes = pd.concat([de_xarxes, de_equips, de_canvis], ignore_index=True)
    c = mt.comparacio(metodes, A_CANVIS, XARXES_TOC, TOC, amb_criteri=True)
    c_equips = mt.comparacio(metodes, A_CANVIS, A_EQUIPS, TOC, amb_criteri=False)
    passa, millor = mt.compleix(c), mq.millor_fins_ara(c_equips)
    per_font = {(font, contra): mt.comparacio(metodes[metodes["font"] == font], A_CANVIS, contra, TOC,
                                              amb_criteri=False)
                for font in FONTS for contra in (XARXES_TOC, A_EQUIPS)}
    tasques = [(nom, e, {A_EQUIPS: triades_equips[nom], A_CANVIS: triades_canvis[nom]})
               for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    trossos = en_paral_lel("encerts", tasques, args.processos)
    errors_, encerts_, canvis_ = (pd.DataFrame([f for tros in trossos for f in tros[clau_]])
                                  for clau_ in ("errors", "encerts", "canvis"))
    contingut = {"clau": clau_dels_resultats(), "passa": passa, "millor_fins_ara": millor,
                 "comparacio": t3.registres(c), "contra_a_equips_sencers": t3.registres(c_equips),
                 "triades": triades, "files": t3.registres(files[files["metode"] == A_CANVIS]),
                 "per_font": {f"{font} · {contra}": t3.registres(t) for (font, contra), t in per_font.items()},
                 "errors": t3.registres(errors_), "encerts": t3.registres(encerts_), "canvis": t3.registres(canvis_)}
    escriu(contingut, markdown(metodes, triades, c, passa, c_equips, millor, per_font, errors_, encerts_, canvis_))


if __name__ == "__main__":
    main()
