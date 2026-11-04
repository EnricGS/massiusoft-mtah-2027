"""El cost de canviar d'equip, après (T3i del pla per tocs, `docs/pla-tocs.md`, «T3i»).

    cd codi && uv run python -I -m banc.model_a_canvis [--processos 12]

1. **Les probabilitats d'equip,** les d'A contacte (T3h) tal com són, de la memòria cau.
2. **Un classificador de canvis:** a cada imatge, la probabilitat q que hi hagi un canvi d'equip de la veritat a `K`
   imatges o menys (`canvis`, `objectiu`). Els senyals, els del segon classificador d'A contacte: per entrenar, amb
   les probabilitats dels primers dels grups; per provar, amb les del primer del partit que es prova (totes, de la
   memòria cau de la T3h). El mateix LightGBM, amb dues classes, una imatge de cada 16 amb veritat H, A o D i
   cadascuna també girada; q és la mitjana de les dues vistes. Deixant cada partit fora: 10 models, i les q de cada
   un als deu escenaris de la T3, a la memòria cau (`dades/banc/a-canvis/`).
3. **El decodificador** amb el cost a cada imatge (`cadena/decodifica_tocs.viterbi`): d'H a A, o al revés, w · (−ln q);
   cap a la D o des de la D, λ; i la durada mínima. w, λ i la durada mínima es trien junts amb els altres nou partits
   als escenaris ×¼. Amb les probabilitats d'A contacte, és **A canvis**; amb les d'A context, només per saber-ho.
4. **El criteri** del pla: A canvis contra A context, el de la cadena, amb el seu decodificador triat igual. Només per
   saber-ho, A canvis contra A contacte amb el decodificador d'ara, i A context amb el cost après contra A context.

Escriu `resultats/model-a-canvis.json` (la clau del codi i les files) i `resultats/model-a-canvis.md`. Tot són dades
obertes. Els mòduls de la T3e a la T3h no es toquen.
"""

from __future__ import annotations

import argparse
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

from banc import avalua, degrada, fonts
from banc import decodificador_tocs as t3
from banc import model_a_contacte as t3h
from banc import model_a_context as t3e
from banc import model_a_quart as t3b
from banc.partit import PartitBanc
from cadena import decodifica, model, senyals
from cadena import decodifica_tocs as dt
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ENTRENAMENT = t3h.ENTRENAMENT
K = 6                                       # imatges a banda i banda d'un canvi, com a l'oracle
WS = (1.0, 2.0, 4.0, 8.0)
LAMS = (2.0, 4.0, 8.0, 16.0)
DMINS = decodifica.GRAELLA_DMIN
Q_MINIM = 1e-4                              # perquè −ln q no sigui infinit
CANVIS = "A canvis"
CONTEXT_CANVIS = "A context amb el cost après"
AMB_COST = {CONTEXT_CANVIS: t3e.CONTEXT, CANVIS: t3h.CONTACTE}     # de qui són les probabilitats d'equip
METODES = (t3e.CONTEXT, t3h.CONTACTE, CONTEXT_CANVIS, CANVIS)
PARAMS = {k: v for k, v in model.PARAMS.items() if k != "num_class"} | {"objective": "binary"}
DIR_CAU = fonts.DIR_CAU / "a-canvis"
DIR_RESULTATS = t3.DIR_RESULTATS


def canvis(etiqueta: np.ndarray, trams: list[tuple[int, int]]) -> np.ndarray:
    """On comença cada possessió (de la mètrica) d'un equip diferent del de l'anterior, dins de cada part, encara que
    entremig hi hagi pilota morta."""
    out = []
    for tram in trams:
        darrer = None
        for inici, _, k in pm.possession_spells(etiqueta.astype(np.int8), [tram]):
            if darrer is not None and k != darrer:
                out.append(inici)
            darrer = k
    return np.array(out, dtype=int)


def objectiu(etiqueta: np.ndarray, trams: list[tuple[int, int]], k: int = K) -> np.ndarray:
    """Les imatges a `k` o menys d'un canvi d'equip."""
    a_prop = np.zeros(len(etiqueta), dtype=bool)
    for c in canvis(etiqueta, trams):
        a_prop[max(c - k, 0):c + k + 1] = True
    return a_prop


def mostres(p: PartitBanc, taula: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    """Una imatge de cada `model.PAS` amb veritat H, A o D (com `model.mostres`), i cadascuna també girada, amb
    l'objectiu: un canvi ho és igual amb els equips girats."""
    tria = np.flatnonzero(np.isin(p.veritat, model.CLASSES))[::model.PAS]
    x = taula.iloc[tria].reset_index(drop=True)
    y = objectiu(p.veritat, avalua.trams_valids(p))[tria].astype(np.int8)
    return pd.concat([x, senyals.intercanvia(x)], ignore_index=True), np.concatenate([y, y])


def mostres_de(prova: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Les mostres per provar `prova`: els altres nou partits, als sis escenaris, amb la taula del segon d'A contacte
    feta amb les probabilitats del primer que no ha vist cap d'ells."""
    primers = {}
    for i in range(t3e.GRUPS):
        primers |= t3h.primer_del_grup((prova, i))
    xs, ys = [], []
    for (nom, e), primer in primers.items():
        p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[e])
        x, y = mostres(p, t3h.taula_segon(p, primer.astype(float)))
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def q_de(entrenat: lgb.Booster, taula: pd.DataFrame) -> np.ndarray:
    """La mitjana de la vista original i de la girada."""
    return (entrenat.predict(taula) + entrenat.predict(senyals.intercanvia(taula))) / 2


def probabilitats(prova: str, entrena: bool = True) -> dict[str, np.ndarray]:
    """Les q al partit `prova`, a cada escenari de la T3. Amb `entrena=False`, només les llegeix de la memòria cau, i
    si no hi són o són d'un altre codi, s'atura."""
    cami = DIR_CAU / f"{prova}.npz"
    desat = None
    if cami.exists():
        with np.load(cami, allow_pickle=False) as d:
            if str(d["clau"]) == CLAU:
                desat = {k: d[k] for k in d.files if k != "clau"}
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les probabilitats de canvis de {prova}, o són d'un altre codi")
        x, y = mostres_de(prova)
        entrenat = lgb.train(PARAMS, lgb.Dataset(x, label=y, free_raw_data=True), num_boost_round=model.RONDES)
        del x
        primers = t3h.primer_de_la_prova(prova)
        desat = {}
        for i, (nom_e, escenari) in enumerate(t3.ESCENARIS.items()):
            p = degrada.aplica(fonts.partit(prova), escenari)
            desat[f"e{i}"] = q_de(entrenat, t3h.taula_segon(p, primers[nom_e].astype(float))).astype(np.float32)
        cami.parent.mkdir(parents=True, exist_ok=True)
        temporal = cami.with_name(f"{cami.name}.{os.getpid()}.part.npz")
        np.savez(temporal, clau=CLAU, **desat)
        temporal.replace(cami)
    return {e: desat[f"e{i}"] for i, e in enumerate(t3.ESCENARIS)}


def costos(q: np.ndarray, lam: float, w: float) -> np.ndarray:
    """(n, 3, 3): d'H a A, o al revés, w · (−ln q); cap a la D o des de la D, λ."""
    cost = np.full((len(q), 3, 3), lam)
    entre = w * -np.log(np.clip(q, Q_MINIM, 1.0))
    cost[:, dt.H, dt.A] = entre
    cost[:, dt.A, dt.H] = entre
    return cost


def per_trams(relativa: np.ndarray, q: np.ndarray, trams: tuple[tuple[int, int, int], ...], w: float, lam: float,
              d_min: int) -> np.ndarray:
    """Els codis de la mètrica: H, A o D dins de cada part, i X fora (com `decodifica.per_trams`)."""
    cost = costos(q, lam, w)
    out = np.full(len(relativa), pm.X, dtype=np.int8)
    for _, inici, fi in trams:
        out[inici:fi + 1] = np.asarray(dt.CLASSES)[dt.viterbi(relativa[inici:fi + 1], cost[inici:fi + 1], d_min)]
    return out


def de_qui(metode: str):
    return {t3e.CONTEXT: t3e.probabilitats, t3h.CONTACTE: t3h.probabilitats}[metode]


def graella(tasca: tuple[str, str]) -> list[dict]:
    """Un partit i un escenari: A context i A contacte amb el decodificador d'ara, i tots dos amb el cost après."""
    nom, escenari = tasca
    p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[escenari])
    q = probabilitats(nom, entrena=False)[escenari].astype(float)
    comu = {"partit": nom, "font": p.font, "escenari": escenari}
    files = []
    for metode in (t3e.CONTEXT, t3h.CONTACTE):
        probes, prior = de_qui(metode)(nom, entrena=False)
        proba = probes[escenari].astype(float)
        for lam, d_min in itertools.product(decodifica.GRAELLA_LAMBDA, decodifica.GRAELLA_DMIN):
            pred = decodifica.per_trams(proba, prior, p.trams, lam, d_min)
            files.append({**comu, "metode": metode, "w": math.nan, "lam": lam, "d_min": d_min,
                          **avalua.puntua(p, pred)})
    for metode, base in AMB_COST.items():
        probes, prior = de_qui(base)(nom, entrena=False)
        relativa = log_relativa(probes[escenari].astype(float), prior)
        for w, lam, d_min in itertools.product(WS, LAMS, DMINS):
            pred = per_trams(relativa, q, p.trams, w, lam, d_min)
            files.append({**comu, "metode": metode, "w": w, "lam": lam, "d_min": d_min, **avalua.puntua(p, pred)})
    return files


def parametres(metode: str) -> list[str]:
    return ["w", "lam", "d_min"] if metode in AMB_COST else ["lam", "d_min"]


def tria_sense_mirar(files: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Les files de cada mètode a cada partit, amb els paràmetres triats amb els altres nou als escenaris ×¼. També
    les triades."""
    triats, triades = [], {}
    for prova in fonts.NOMS:
        triades[prova] = {}
        for metode in METODES:
            seu = files[files["metode"] == metode]
            columnes = parametres(metode)
            millor = t3.millor(seu[seu["partit"] != prova], columnes)
            del_partit = seu[seu["partit"] == prova]
            tria = np.logical_and.reduce([del_partit[c] == v for c, v in zip(columnes, millor)])
            triats.append(del_partit[tria])
            triades[prova][metode] = tuple(int(v) if c == "d_min" else float(v) for c, v in zip(columnes, millor))
    return pd.concat(triats, ignore_index=True), triades


def _comparacio(c: pd.DataFrame, nou: str, contra: str) -> list[str]:
    linies = [f"| escenari | {contra} | {nou} | diferència | interval del 95 % | {nou} guanya |",
              "|---|---|---|---|---|---|"]
    return linies + [f"| {f.escenari} | {f.contra:.3f} | {f.nou:.3f} | {f.diferencia:+.3f} | {f.baix:+.3f} a "
                     f"{f.alt:+.3f} | {f.guanya} de {f.partits} |" for f in c.itertuples()]


def markdown(c: pd.DataFrame, c_contacte: pd.DataFrame, c_context: pd.DataFrame, metodes: pd.DataFrame,
             triades: dict, passa: dict[str, bool]) -> str:
    ordre = list(METODES)
    linies = ["# Banc obert · El cost de canviar d'equip, après (T3i)", "",
              "Generat amb `uv run python -I -m banc.model_a_canvis`. Dades obertes: 7 partits de DFL (IDSSE, CC BY",
              "4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3i», i la capçalera de `banc/model_a_canvis.py`.", "",
              f"**{t3e.CONTEXT}** és el model de la cadena (T3e), i **{t3h.CONTACTE}**, el de la T3h, tots dos amb el",
              f"decodificador d'ara. **{CANVIS}** són les probabilitats d'{t3h.CONTACTE} amb el decodificador que cobra",
              "w · (−ln q) per canviar d'equip, amb q la probabilitat d'un canvi a 6 imatges o menys, d'un classificador",
              f"de canvis. **{CONTEXT_CANVIS}** és el mateix amb les probabilitats d'{t3e.CONTEXT}. Tots tenen els",
              "paràmetres del decodificador triats amb els altres nou partits als escenaris ×¼.", "",
              "## L'spellF1 i el macroF1 de cada mètode (mitjana dels deu partits)", ""]
    for columna, nom in (("spell_f1", "spellF1"), ("macro_f1", "macroF1")):
        t = metodes.pivot_table(index="escenari", columns="metode", values=columna, sort=False)[ordre]
        linies += [f"**{nom}**", "", "| escenari | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 1) + "|"]
        linies += [f"| {e} | " + " | ".join(f"{v:.3f}" for v in f) + " |" for e, f in t.iterrows()]
        linies.append("")
    linies += [f"## {CANVIS} contra {t3e.CONTEXT} (spellF1): el criteri", "",
               *t3b._taula(c, CANVIS, t3e.CONTEXT), "", *t3b._criteris(passa, False),
               f"## {CANVIS} contra {t3h.CONTACTE} (spellF1), només per saber-ho", "",
               "Les mateixes probabilitats d'equip: la diferència és el que afegeix el decodificador.", "",
               *_comparacio(c_contacte, CANVIS, t3h.CONTACTE), "",
               f"## {CONTEXT_CANVIS} contra {t3e.CONTEXT} (spellF1), només per saber-ho", "",
               "El decodificador sol, sobre el model de la cadena.", "",
               *_comparacio(c_context, CONTEXT_CANVIS, t3e.CONTEXT), "",
               "## Possessions predites per cada real (mitjana dels deu partits), només per saber-ho", "",
               "| escenari | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 1) + "|"]
    rati = (metodes["possessions"] / metodes["possessions_reals"]).groupby(
        [metodes["escenari"], metodes["metode"]], sort=False).mean().unstack()[ordre]
    linies += [f"| {e} | " + " | ".join(f"{v:.2f}" for v in f) + " |" for e, f in rati.iterrows()]
    linies += ["", "## Els paràmetres triats (cada partit, amb els altres nou)", ""]
    compta: dict[str, int] = {}
    for t in triades.values():
        trossos = []
        for m, valors in t.items():
            noms = dict(zip(parametres(m), valors))
            w = f"w = {noms['w']:g}, " if "w" in noms else ""
            trossos.append(f"{m}: {w}λ = {noms['lam']:g}, durada mínima {noms['d_min']}")
        clau_ = " · ".join(trossos)
        compta[clau_] = compta.get(clau_, 0) + 1
    linies += [f"- {k} ({n} partits)" for k, n in compta.items()]
    return "\n".join(linies + [""])


def clau() -> str:
    """El que fa les q: la clau d'A contacte (els seus senyals i primers), l'objectiu, l'entrenament i això."""
    h = hashlib.sha256((t3h.CLAU + repr((ENTRENAMENT, K, PARAMS, model.PAS, model.RONDES))).encode())
    for funcio in (canvis, objectiu, mostres, mostres_de, q_de, probabilitats):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + t3h.clau_dels_resultats()).encode())
    for modul in (t3h, t3e, t3b, t3, decodifica, dt, avalua, degrada):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def main() -> None:
    from banc import model_a_canvis as aquest           # pel nom del mòdul, perquè els processos fills el trobin

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=2, help="models alhora (cadascun fa servir 8 fils)")
    args = ap.parse_args()
    for nom in fonts.NOMS:                              # les d'A context i d'A contacte: abans cal fer-les
        t3e.probabilitats(nom, entrena=False)
        t3h.probabilitats(nom, entrena=False)
    with ProcessPoolExecutor(max_workers=args.processos_models) as feina:
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.probabilitats, fonts.NOMS)):
            print(f"· {nom}: el classificador de canvis, fet", flush=True)
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        tasques = list(itertools.product(fonts.NOMS, t3.ESCENARIS))
        files = pd.DataFrame([f for tros in feina.map(aquest.graella, tasques) for f in tros])
    metodes, triades = tria_sense_mirar(files)
    c = t3b.comparacio(metodes, CANVIS, t3e.CONTEXT)
    c_contacte = t3b.comparacio(metodes, CANVIS, t3h.CONTACTE)
    c_context = t3b.comparacio(metodes, CONTEXT_CANVIS, t3e.CONTEXT)
    passa = t3b.compleix(c)
    desa = {"clau": clau_dels_resultats(), "passa": passa, "comparacio": t3.registres(c),
            "comparacio_contacte": t3.registres(c_contacte), "comparacio_context": t3.registres(c_context),
            "triades": triades, "files": t3.registres(files)}
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-a-canvis.json").write_text(json.dumps(desa, indent=1, default=float, allow_nan=False))
    (DIR_RESULTATS / "model-a-canvis.md").write_text(markdown(c, c_contacte, c_context, metodes, triades, passa))
    print((DIR_RESULTATS / "model-a-canvis.md").read_text())


if __name__ == "__main__":
    main()
