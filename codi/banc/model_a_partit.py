"""Entrenar també com el partit (T3p del pla per tocs, `docs/pla-tocs.md`, «T3p»).

    cd codi && uv run python -I -m banc.model_a_partit [--processos 12] [--processos-models 4]

A xarxes (T3o) tal qual, amb una sola diferència: un escenari més, «partit ×¼» (`banc/escenari_partit.py`), on
s'entrena i es tria com als altres ×¼. Les peces són les d'A xarxes, cridades amb la llista dels escenaris
d'entrenament (`SIS`, els d'ara, o `SET`, amb «partit ×¼»), i es proven als deu escenaris de la T3 i a «partit ×¼».

1. **Pas 1: A context i A xarxes, tal com són, a «partit ×¼».** A la memòria cau de la T3e i de la T3o només hi ha
   les seves probabilitats als deu escenaris de la T3. Els models del partit que es prova (A control i el segon
   d'A context; el primer, les cinc xarxes, el segon i el de canvis d'A xarxes) es tornen a fer igual, amb les
   mateixes mostres i llavors, i els dels grups es llegeixen de la memòria cau. Es comprova que tornen el mateix
   als deu escenaris (`reproduccio`).
2. **Pas 2: A partit.** Els primers i les cinc xarxes dels grups i del partit que es prova, el segon i el de canvis,
   entrenats amb els set escenaris (`dades/banc/a-partit/`).
3. **El decodificador,** amb la q de cadascun i la graella de la T3j: A context i A xarxes, triats als quatre ×¼,
   com a la cadena; A partit, als cinc.
4. **El criteri** del pla: A partit contra A xarxes. A «partit ×¼» guanya clarament, i als altres deu no perd.

Escriu `resultats/model-a-partit.json` (la clau del codi i les files) i `resultats/model-a-partit.md`. Tot són dades
obertes. Els mòduls de la T3e a la T3o no es toquen.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import inspect
import itertools
import json
import math
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from banc import avalua, degrada, fonts, model_a
from banc import decodificador_tocs as t3
from banc import escenari_partit as ep
from banc import model_a_aturades as t3k
from banc import model_a_canvis as t3i
from banc import model_a_canvis2 as t3j
from banc import model_a_contacte as t3h
from banc import model_a_context as t3e
from banc import model_a_control as t3d
from banc import model_a_possessio as t3f
from banc import model_a_quart as t3b
from banc import model_a_xarxa as t3m
from banc import model_a_xarxes as t3o
from banc.partit import PartitBanc
from cadena import decodifica, model, xarxa, xarxes
from possessio.decodificacio import log_relativa

PARTIT = ep.NOM
ESCENARIS = (*t3.ESCENARIS, PARTIT)                 # on es prova
QUARTS = (*t3.QUARTS, PARTIT)
SIS = t3o.ENTRENAMENT
SET = (*SIS, PARTIT)
A_PARTIT = "A partit"
METODES = (t3e.CONTEXT, t3o.XARXES, A_PARTIT)
ENTRENAMENT = {t3o.XARXES: SIS, A_PARTIT: SET}
QUARTS_DE = {t3e.CONTEXT: t3.QUARTS, t3o.XARXES: t3.QUARTS, A_PARTIT: QUARTS}      # on es tria el decodificador
NOM_LLISTA = {SIS: "sis", SET: "set"}
PECES = ("A context", "el primer", "les cinc xarxes", "A xarxes", "el de canvis")    # les del Pas 1
DIR_CAU = fonts.DIR_CAU / "a-partit"
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


def cau(peca: str, entrenament: tuple[str, ...], *qui: object) -> Path:
    return DIR_CAU / f"{peca}-{NOM_LLISTA[entrenament]}-{'-'.join(map(str, qui))}.npz"


def degradat(nom: str, escenari: str) -> PartitBanc:
    """El partit `nom` a «partit ×¼» o a un escenari de la T3."""
    p = fonts.partit(nom)
    return ep.aplica(p) if escenari == PARTIT else degrada.aplica(p, t3.ESCENARIS[escenari])


def claus_del_grup(prova: str, i: int, entrenament: tuple[str, ...]) -> dict[tuple[str, str], str]:
    return {(nom, e): f"p{j}_{k}" for j, nom in enumerate(t3e.grups(prova)[i]) for k, e in enumerate(entrenament)}


@functools.cache
def mostres_primer(nom: str, escenari: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Les mostres del primer d'A contacte (T3h) d'un partit a un escenari, amb la tria de la T3f (un cop per
    procés)."""
    p = degradat(nom, escenari)
    return t3f.mostres(p, t3h.taula_primer(p))


def entrena_primer(noms: list[str], entrenament: tuple[str, ...]) -> lgb.Booster:
    """Com `t3h.entrena_primer`: les mostres de cada partit, escenari per escenari, en el mateix ordre."""
    m = [mostres_primer(nom, e) for nom in noms for e in entrenament]
    return model.entrena(pd.concat([x for x, _ in m], ignore_index=True), np.concatenate([y for _, y in m]))


def primer_del_grup(tasca: tuple[str, int, tuple[str, ...]]) -> dict[tuple[str, str], np.ndarray]:
    """Les del primer als partits del grup `i` de `prova` (els grups de la T3e), als escenaris d'entrenament, entrenat
    amb els altres sis. Amb els sis d'ara, les de la T3h, de la memòria cau."""
    prova, i, entrenament = tasca
    if entrenament == SIS:
        return t3h.primer_del_grup((prova, i))
    claus = claus_del_grup(prova, i, entrenament)
    cami = cau("primer-grup", entrenament, prova, i)
    desat = llegeix(cami)
    if desat is None:
        entrenat = entrena_primer(t3m.per_entrenar_el_grup(prova, i), entrenament)
        desat = {clau_: model.probabilitats(entrenat, t3h.taula_primer(degradat(nom, e))).astype(np.float32)
                 for (nom, e), clau_ in claus.items()}
        desa(cami, **desat)
    return {qui: desat[nom] for qui, nom in claus.items()}


def primer_de_la_prova(tasca: tuple[str, tuple[str, ...]]) -> dict[str, np.ndarray]:
    """Les del primer al partit `prova`, a tots els escenaris, entrenat amb els altres nou."""
    prova, entrenament = tasca
    cami = cau("primer", entrenament, prova)
    desat = llegeix(cami)
    if desat is None:
        entrenat = entrena_primer([nom for nom in fonts.NOMS if nom != prova], entrenament)
        desat = {f"e{i}": model.probabilitats(entrenat, t3h.taula_primer(degradat(prova, e))).astype(np.float32)
                 for i, e in enumerate(ESCENARIS)}
        desa(cami, **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(ESCENARIS)}


def entrena_xarxes(noms: list[str], entrenament: tuple[str, ...]) -> tuple[tuple[xarxa.Xarxa, ...], list[list[float]]]:
    """Com `t3o.entrena_xarxes`, amb els escenaris d'entrenament que es diuen."""
    xs, ys = [], []
    for nom in noms:
        for e in entrenament:
            p = degradat(nom, e)
            files = t3f.tria(p.veritat, avalua.trams_valids(p))
            x, y = xarxa.mostres(p.tracking, p.trams, files, p.veritat[files])
            xs.append(x)
            ys.append(y)
    x = np.concatenate(xs)
    del xs
    return xarxes.entrena(x, np.concatenate(ys))


def xarxes_del_grup(tasca: tuple[str, int, tuple[str, ...]]) -> dict[tuple[str, str], np.ndarray]:
    """La mitjana de les cinc xarxes als partits del grup `i` de `prova`, als escenaris d'entrenament, entrenades amb
    els altres sis. Amb els sis d'ara, les de la T3o, de la memòria cau."""
    prova, i, entrenament = tasca
    if entrenament == SIS:
        return t3o.xarxes_del_grup((prova, i))
    claus = claus_del_grup(prova, i, entrenament)
    cami = cau("xarxes-grup", entrenament, prova, i)
    desat = llegeix(cami)
    if desat is None:
        entrenades, perdues = entrena_xarxes(t3m.per_entrenar_el_grup(prova, i), entrenament)
        desat = {}
        for (nom, e), clau_ in claus.items():
            p = degradat(nom, e)
            desat[clau_] = xarxes.probabilitats(entrenades, p.tracking, p.trams).astype(np.float32)
        desa(cami, perdues=np.array(perdues), **desat)
    return {qui: desat[nom] for qui, nom in claus.items()}


def xarxes_de_la_prova(tasca: tuple[str, tuple[str, ...]]) -> dict[str, np.ndarray]:
    """La mitjana de les cinc xarxes al partit `prova`, a tots els escenaris, entrenades amb els altres nou."""
    prova, entrenament = tasca
    cami = cau("xarxes", entrenament, prova)
    desat = llegeix(cami)
    if desat is None:
        entrenades, perdues = entrena_xarxes([nom for nom in fonts.NOMS if nom != prova], entrenament)
        desat = {}
        for i, e in enumerate(ESCENARIS):
            p = degradat(prova, e)
            desat[f"e{i}"] = xarxes.probabilitats(entrenades, p.tracking, p.trams).astype(np.float32)
        desa(cami, perdues=np.array(perdues), **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(ESCENARIS)}


def mostres_segon(prova: str, entrenament: tuple[str, ...]) -> tuple[pd.DataFrame, np.ndarray]:
    """Com `t3o.mostres_segon`, amb els escenaris d'entrenament que es diuen."""
    primers, de_les_xarxes = {}, {}
    for i in range(t3e.GRUPS):
        primers |= primer_del_grup((prova, i, entrenament))
        de_les_xarxes |= xarxes_del_grup((prova, i, entrenament))
    xs, ys = [], []
    for (nom, e), primer in primers.items():
        p = degradat(nom, e)
        x, y = t3f.mostres(p, t3m.taula_segon(p, primer.astype(float), de_les_xarxes[(nom, e)].astype(float)))
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def segon(tasca: tuple[str, tuple[str, ...]], entrena: bool = True) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Les d'A xarxes (amb `SIS`) o d'A partit (amb `SET`) al partit `prova`, a tots els escenaris, i el prior. Amb
    `entrena=False`, només les llegeix de la memòria cau, i si no hi són o són d'un altre codi, s'atura."""
    prova, entrenament = tasca
    cami = cau("segon", entrenament, prova)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les probabilitats del segon ({NOM_LLISTA[entrenament]}) de {prova}, o són "
                               "d'un altre codi")
        x, y = mostres_segon(prova, entrenament)
        entrenat, prior = model.entrena(x, y), model.prior(y)
        del x
        primers = primer_de_la_prova((prova, entrenament))
        de_les_xarxes = xarxes_de_la_prova((prova, entrenament))
        desat = {"prior": prior}
        for i, e in enumerate(ESCENARIS):
            p = degradat(prova, e)
            taula = t3m.taula_segon(p, primers[e].astype(float), de_les_xarxes[e].astype(float))
            desat[f"e{i}"] = model.probabilitats(entrenat, taula).astype(np.float32)
        desa(cami, **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(ESCENARIS)}, desat["prior"]


def mostres_q(prova: str, entrenament: tuple[str, ...]) -> tuple[pd.DataFrame, np.ndarray]:
    """Com `t3i.mostres_de`, amb els escenaris d'entrenament que es diuen."""
    primers = {}
    for i in range(t3e.GRUPS):
        primers |= primer_del_grup((prova, i, entrenament))
    xs, ys = [], []
    for (nom, e), primer in primers.items():
        p = degradat(nom, e)
        x, y = t3i.mostres(p, t3h.taula_segon(p, primer.astype(float)))
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def q(tasca: tuple[str, tuple[str, ...]], entrena: bool = True) -> dict[str, np.ndarray]:
    """Les q del de canvis (T3i) al partit `prova`, a tots els escenaris. Amb `entrena=False`, només les llegeix de la
    memòria cau, i si no hi són o són d'un altre codi, s'atura."""
    prova, entrenament = tasca
    cami = cau("q", entrenament, prova)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les q ({NOM_LLISTA[entrenament]}) de {prova}, o són d'un altre codi")
        x, y = mostres_q(prova, entrenament)
        entrenat = lgb.train(t3i.PARAMS, lgb.Dataset(x, label=y, free_raw_data=True), num_boost_round=model.RONDES)
        del x
        primers = primer_de_la_prova((prova, entrenament))
        desat = {}
        for i, e in enumerate(ESCENARIS):
            p = degradat(prova, e)
            desat[f"e{i}"] = t3i.q_de(entrenat, t3h.taula_segon(p, primers[e].astype(float))).astype(np.float32)
        desa(cami, **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(ESCENARIS)}


def a_context(prova: str, entrena: bool = True) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Les d'A context (T3e) tal com és al partit `prova`, a tots els escenaris, i el prior: A control (T3d) i el
    segon, refets amb les mostres de la T3d i de la T3e (i els primers dels grups, de la memòria cau). Amb
    `entrena=False`, només les llegeix de la memòria cau, i si no hi són o són d'un altre codi, s'atura."""
    cami = DIR_CAU / f"context-{prova}.npz"
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les probabilitats d'{t3e.CONTEXT} de {prova}, o són d'un altre codi")
        mostres = [t3d.mostres_de(nom) for nom in fonts.NOMS if nom != prova]
        control = model.entrena(pd.concat([m[0] for m in mostres], ignore_index=True),
                                np.concatenate([m[1] for m in mostres]))
        x, y = t3e.mostres_de(prova)
        entrenat, prior = model.entrena(x, y), model.prior(y)
        del x
        desat = {"prior": prior}
        for i, e in enumerate(ESCENARIS):
            p = degradat(prova, e)
            primer = model.probabilitats(control, t3d.taula(p)).astype(np.float32)
            desat[f"e{i}"] = model.probabilitats(entrenat, t3e.taula(p, primer.astype(float))).astype(np.float32)
        desa(cami, **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(ESCENARIS)}, desat["prior"]


def diferencia(a: np.ndarray, b: np.ndarray) -> float:
    """La diferència més gran entre dues probabilitats; infinita si no tenen la mateixa forma o no falten als mateixos
    llocs."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.shape != b.shape or not np.array_equal(np.isnan(a), np.isnan(b)):
        return math.inf
    return float(np.abs(np.nan_to_num(a - b)).max(initial=0.0))


def reproduccio(prova: str) -> dict[str, float]:
    """Pas 1: de cada peça refeta, la diferència més gran amb la de la memòria cau de la T3e, la T3h, la T3i i la T3o
    als deu escenaris de la T3, i amb el seu prior (0: els mateixos models)."""
    def amb_prior(probes_i_prior: tuple[dict[str, np.ndarray], np.ndarray]) -> dict[str, np.ndarray]:
        probes, prior = probes_i_prior
        return {**probes, "prior": prior}

    refet = {"A context": amb_prior(a_context(prova, entrena=False)), "el primer": primer_de_la_prova((prova, SIS)),
             "les cinc xarxes": xarxes_de_la_prova((prova, SIS)), "A xarxes": amb_prior(segon((prova, SIS), False)),
             "el de canvis": q((prova, SIS), entrena=False)}
    desat = {"A context": amb_prior(t3e.probabilitats(prova, entrena=False)),
             "el primer": t3h.primer_de_la_prova(prova), "les cinc xarxes": t3o.xarxes_de_la_prova(prova, False),
             "A xarxes": amb_prior(t3o.probabilitats(prova, entrena=False)),
             "el de canvis": t3i.probabilitats(prova, entrena=False)}
    return {peca: max(diferencia(refet[peca][k], v) for k, v in desat[peca].items()) for peca in PECES}


def graella(tasca: tuple[str, str]) -> list[dict]:
    """Un partit i un escenari: A context amb el decodificador d'ara; A xarxes i A partit amb la seva q i la graella de
    la T3j."""
    nom, escenari = tasca
    p = degradat(nom, escenari)
    comu = {"partit": nom, "font": p.font, "escenari": escenari}
    probes, prior = a_context(nom, entrena=False)
    files = []
    for lam, d_min in itertools.product(decodifica.GRAELLA_LAMBDA, decodifica.GRAELLA_DMIN):
        pred = decodifica.per_trams(probes[escenari].astype(float), prior, p.trams, lam, d_min)
        files.append({**comu, "metode": t3e.CONTEXT, "w": math.nan, "lam": lam, "d_min": d_min,
                      **avalua.puntua(p, pred)})
    for metode, entrenament in ENTRENAMENT.items():
        probes, prior = segon((nom, entrenament), entrena=False)
        relativa = log_relativa(probes[escenari].astype(float), prior)
        q_ = q((nom, entrenament), entrena=False)[escenari].astype(float)
        for w, lam, d_min in itertools.product(t3j.WS, t3j.LAMS, t3j.DMINS):
            pred = t3i.per_trams(relativa, q_, p.trams, w, lam, d_min)
            files.append({**comu, "metode": metode, "w": w, "lam": lam, "d_min": d_min, **avalua.puntua(p, pred)})
    return files


def millor(files: pd.DataFrame, columnes: list[str], quarts: tuple[str, ...]) -> tuple:
    """Com `t3.millor`, als escenaris `quarts`: la combinació amb més spellF1 de mitjana (desempata el macroF1)."""
    tria = files[files["escenari"].isin(quarts)]
    mitjanes = tria.groupby(columnes, dropna=False)[["spell_f1", "macro_f1"]].mean()
    return mitjanes.sort_values(["spell_f1", "macro_f1"], ascending=False).index[0]


def tria_sense_mirar(files: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Les files de cada mètode a cada partit, amb els paràmetres triats amb els altres nou als ×¼ de cada mètode
    (`QUARTS_DE`). També les triades."""
    triats, triades = [], {}
    for prova in fonts.NOMS:
        triades[prova] = {}
        for metode in METODES:
            seu = files[files["metode"] == metode]
            columnes = t3k.parametres(metode)
            millor_ = millor(seu[seu["partit"] != prova], columnes, QUARTS_DE[metode])
            del_partit = seu[seu["partit"] == prova]
            tria = np.logical_and.reduce([del_partit[c] == v for c, v in zip(columnes, millor_)])
            triats.append(del_partit[tria])
            triades[prova][metode] = tuple(int(v) if c == "d_min" else float(v) for c, v in zip(columnes, millor_))
    return pd.concat(triats, ignore_index=True), triades


def comparacio(metodes: pd.DataFrame, nou: str, contra: str) -> pd.DataFrame:
    """Per escenari: `nou` contra `contra`, i si compleix el criteri del pla: a «partit ×¼», guanya clarament; als
    altres, no perd."""
    files = []
    for escenari in ESCENARIS:
        tria = metodes[metodes["escenari"] == escenari].pivot_table(index="partit", columns="metode",
                                                                   values="spell_f1")
        dif = (tria[nou] - tria[contra]).to_numpy()
        font = metodes.groupby("partit")["font"].first().loc[tria.index].to_numpy()
        baix, alt = model_a.interval(dif, font)
        guanya = int((dif > 0).sum())
        if escenari == PARTIT:
            criteri = "guanya clarament"
            passa = bool(dif.mean() > t3.SOROLL and baix > 0 and guanya >= t3.GUANYA_MINIM)
        else:
            criteri, passa = "no perd", bool(dif.mean() >= -t3.SOROLL)
        files.append({"escenari": escenari, "contra": tria[contra].mean(), "nou": tria[nou].mean(),
                      "diferencia": dif.mean(), "baix": baix, "alt": alt, "guanya": guanya, "partits": len(dif),
                      "criteri": criteri, "passa": passa})
    return pd.DataFrame(files)


def compleix(c: pd.DataFrame) -> dict[str, bool]:
    del_partit = c["escenari"] == PARTIT
    return {"partit": bool(c[del_partit]["passa"].all()), "altres": bool(c[~del_partit]["passa"].all())}


def _criteris(passa: dict[str, bool]) -> list[str]:
    def marca(v: bool) -> str:
        return "✓" if v else "✗"

    return ["| | Passa si | |", "|---|---|---|",
            f"| «{PARTIT}» | guanya clarament (diferència > {t3.SOROLL}, interval > 0, {t3.GUANYA_MINIM} partits de 10 "
            f"o més) | {marca(passa['partit'])} |",
            f"| Els quatre ×¼ d'ara, el net, els ×1 i el soroll2 | no perd a cap (diferència ≥ −{t3.SOROLL}) | "
            f"{marca(passa['altres'])} |", "", f"**{'Passa' if all(passa.values()) else 'No passa'}.**", ""]


def _reproduccio(r: dict[str, dict[str, float]]) -> list[str]:
    pitjor = {peca: max(d[peca] for d in r.values()) for peca in PECES}
    linies = ["| peça | la diferència més gran (els deu partits) | |", "|---|---|---|"]
    linies += [f"| {peca} | {v:.2g} | {'✓ la mateixa' if v == 0 else '⚠ no és la mateixa'} |"
               for peca, v in pitjor.items()]
    return linies + [""]


def markdown(c: pd.DataFrame, c_pas1: pd.DataFrame, metodes: pd.DataFrame, triades: dict, passa: dict[str, bool],
             r: dict[str, dict[str, float]]) -> str:
    ordre = list(METODES)
    linies = ["# Banc obert · Entrenar també com el partit (T3p)", "",
              "Generat amb `uv run python -I -m banc.model_a_partit`. Dades obertes: 7 partits de DFL (IDSSE, CC BY",
              "4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3p», i la capçalera de `banc/model_a_partit.py`.", "",
              f"**{t3e.CONTEXT}** i **{t3o.XARXES}** són els de la T3e i la T3o, tal com són, amb el decodificador triat",
              f"als quatre ×¼. **{A_PARTIT}** és {t3o.XARXES} entrenat també a «{PARTIT}» (`banc/escenari_partit.py`),",
              "amb el decodificador triat als cinc ×¼. Cada partit, amb els paràmetres triats amb els altres nou.", "",
              "## Pas 1: els models refets", "",
              "A la memòria cau només hi ha les probabilitats als deu escenaris de la T3: per tenir-les a",
              f"«{PARTIT}», els models del partit que es prova es tornen a fer igual. Contra les de la memòria cau, als",
              "deu escenaris i al prior:", "", *_reproduccio(r),
              "## L'spellF1 i el macroF1 de cada mètode (mitjana dels deu partits)", ""]
    for columna, nom in (("spell_f1", "spellF1"), ("macro_f1", "macroF1")):
        t = metodes.pivot_table(index="escenari", columns="metode", values=columna, sort=False)[ordre]
        linies += [f"**{nom}**", "", "| escenari | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 1) + "|"]
        linies += [f"| {e} | " + " | ".join(f"{x:.3f}" for x in f) + " |" for e, f in t.iterrows()]
        linies.append("")
    linies += [f"## {A_PARTIT} contra {t3o.XARXES} (spellF1): el criteri", "",
               *t3b._taula(c, A_PARTIT, t3o.XARXES), "", *_criteris(passa),
               f"## Pas 1: {t3o.XARXES} contra {t3e.CONTEXT} (spellF1), només per saber-ho", "",
               f"Si a «{PARTIT}» l'ordre és el mateix que als ×¼ d'ara.", "",
               *t3i._comparacio(c_pas1, t3o.XARXES, t3e.CONTEXT), "",
               "## Per font (spellF1, mitjana dels partits de cada font), només per saber-ho", "",
               "| escenari | font | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 2) + "|"]
    per_font = metodes.pivot_table(index=["escenari", "font"], columns="metode", values="spell_f1", sort=False)[ordre]
    linies += [f"| {e} | {f} | " + " | ".join(f"{x:.3f}" for x in fila) + " |" for (e, f), fila in per_font.iterrows()]
    linies += ["", "## Possessions predites per cada real (mitjana dels deu partits), només per saber-ho", "",
               "| escenari | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 1) + "|"]
    rati = (metodes["possessions"] / metodes["possessions_reals"]).groupby(
        [metodes["escenari"], metodes["metode"]], sort=False).mean().unstack()[ordre]
    linies += [f"| {e} | " + " | ".join(f"{x:.2f}" for x in f) + " |" for e, f in rati.iterrows()]
    linies += ["", "## Els paràmetres triats (cada partit, amb els altres nou)", ""]
    compta: dict[str, int] = {}
    for t in triades.values():
        trossos = []
        for m, valors in t.items():
            noms = dict(zip(t3k.parametres(m), valors))
            w = f"w = {noms['w']:g}, " if "w" in noms else ""
            trossos.append(f"{m}: {w}λ = {noms['lam']:g}, durada mínima {noms['d_min']}")
        clau_ = " · ".join(trossos)
        compta[clau_] = compta.get(clau_, 0) + 1
    linies += [f"- {k} ({n} partits)" for k, n in compta.items()]
    return "\n".join(linies + [""])


def clau() -> str:
    """El que fa les probabilitats d'aquí: les claus de les peces d'A xarxes i d'A context, l'escenari i això."""
    h = hashlib.sha256((t3o.CLAU + t3i.CLAU + t3e.CLAU + t3d.CLAU + ep.clau() + repr((SIS, SET, ESCENARIS))).encode())
    for funcio in (degradat, claus_del_grup, mostres_primer, entrena_primer, primer_del_grup, primer_de_la_prova,
                   entrena_xarxes, xarxes_del_grup, xarxes_de_la_prova, mostres_segon, segon, mostres_q, q, a_context):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + t3o.clau_dels_resultats()).encode())
    for modul in (ep, model_a):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def comprova_les_d_abans() -> None:
    """Les de la T3o i de la T3e, i les dels seus grups: el Pas 1 les llegeix i s'hi compara. No les refà."""
    t3o.comprova_les_d_abans()
    for nom in fonts.NOMS:
        t3o.probabilitats(nom, entrena=False)
        t3o.xarxes_de_la_prova(nom, entrena=False)
        if any(t3o.llegeix(t3o.DIR_CAU_GRUPS / f"{nom}-{i}.npz") is None for i in range(t3e.GRUPS)):
            raise RuntimeError(f"Falten les xarxes dels grups de la T3o de {nom}, o són d'un altre codi")
        if any(not a_la_cau(t3e.DIR_CAU_PRIMER / f"{nom}-{i}.npz", t3e.CLAU) for i in range(t3e.GRUPS)):
            raise RuntimeError(f"Falten els primers dels grups de la T3e de {nom}, o són d'un altre codi")


def a_la_cau(cami: Path, clau_: str) -> bool:
    if not cami.exists():
        return False
    with np.load(cami, allow_pickle=False) as desat:
        return str(desat["clau"]) == clau_


def pas_1(feina: ProcessPoolExecutor) -> dict[str, dict[str, float]]:
    """A context i A xarxes refets, i com s'assemblen als de la memòria cau."""
    from banc import model_a_partit as aquest           # pel nom del mòdul, perquè els processos fills el trobin

    proves = [(nom, SIS) for nom in fonts.NOMS]
    for peca, de_qui in (("el primer", aquest.primer_de_la_prova), ("les xarxes", aquest.xarxes_de_la_prova),
                         ("el segon", aquest.segon), ("el de canvis", aquest.q)):
        for (nom, _), _ in zip(proves, feina.map(de_qui, proves)):
            print(f"· Pas 1, {nom}: {peca} fet", flush=True)
    for nom, _ in zip(fonts.NOMS, feina.map(aquest.a_context, fonts.NOMS)):
        print(f"· Pas 1, {nom}: {t3e.CONTEXT} fet", flush=True)
    r = {nom: reproduccio(nom) for nom in fonts.NOMS}
    print("\n".join(_reproduccio(r)), flush=True)
    return r


def pas_2(feina: ProcessPoolExecutor) -> None:
    """A partit: els grups, i després el partit que es prova."""
    from banc import model_a_partit as aquest

    grups = [(nom, i, SET) for nom in fonts.NOMS for i in range(t3e.GRUPS)]
    for peca, de_qui in (("el primer", aquest.primer_del_grup), ("les xarxes", aquest.xarxes_del_grup)):
        for (nom, i, _), _ in zip(grups, feina.map(de_qui, grups)):
            print(f"· Pas 2, {nom}: {peca} del grup {i} fet", flush=True)
    proves = [(nom, SET) for nom in fonts.NOMS]
    for peca, de_qui in (("el primer", aquest.primer_de_la_prova), ("les xarxes", aquest.xarxes_de_la_prova),
                         ("el segon", aquest.segon), ("el de canvis", aquest.q)):
        for (nom, _), _ in zip(proves, feina.map(de_qui, proves)):
            print(f"· Pas 2, {nom}: {peca} fet", flush=True)


def per_json(r: dict[str, dict[str, float]]) -> dict[str, dict[str, float | str]]:
    return {nom: {peca: v if math.isfinite(v) else "inf" for peca, v in d.items()} for nom, d in r.items()}


def main() -> None:
    from banc import model_a_partit as aquest

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=4, help="models alhora")
    args = ap.parse_args()
    comprova_les_d_abans()
    with ProcessPoolExecutor(max_workers=args.processos_models) as feina:
        r = pas_1(feina)
        pas_2(feina)
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        files = pd.DataFrame([f for tros in feina.map(aquest.graella, itertools.product(fonts.NOMS, ESCENARIS))
                              for f in tros])
    metodes, triades = tria_sense_mirar(files)
    c = comparacio(metodes, A_PARTIT, t3o.XARXES)
    c_pas1 = comparacio(metodes, t3o.XARXES, t3e.CONTEXT)
    passa = compleix(c)
    desa_ = {"clau": clau_dels_resultats(), "passa": passa, "reproduccio": per_json(r), "comparacio": t3.registres(c),
             "comparacio_pas1": t3.registres(c_pas1), "triades": triades, "files": t3.registres(files)}
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-a-partit.json").write_text(json.dumps(desa_, indent=1, default=float, allow_nan=False))
    (DIR_RESULTATS / "model-a-partit.md").write_text(markdown(c, c_pas1, metodes, triades, passa, r))
    print((DIR_RESULTATS / "model-a-partit.md").read_text())


if __name__ == "__main__":
    main()
