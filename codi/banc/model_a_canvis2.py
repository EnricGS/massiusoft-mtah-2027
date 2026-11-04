"""Un segon classificador de canvis, que mira la q al voltant (T3j del pla per tocs, `docs/pla-tocs.md`, «T3j»).

    cd codi && uv run python -I -m banc.model_a_canvis2 [--processos 12]

1. **El primer classificador de canvis,** el de la T3i, als nou partits d'entrenament, fet per models que no els han
   vist: als tres grups de tres de la T3e, un per grup, entrenat amb els altres sis com el de la T3i (`models_dels_
   grups`). Els senyals, els del segon d'A contacte amb les probabilitats dels primers dels grups de la T3h.
2. **El segon classificador de canvis:** els senyals del primer i el context de la seva q (`cadena/canvis.py`).
   L'objectiu, les mostres, el LightGBM i les dues vistes són els de la T3i. Deixant cada partit fora: 10 models, i
   les q de cada un als deu escenaris de la T3, a la memòria cau (`dades/banc/a-canvis2/`). Al partit que es prova,
   la q del primer és la de la T3i.
3. **El decodificador** de la T3i, amb les probabilitats d'A contacte i la q del segon: és **A canvis 2**. Amb la q
   del primer, **A canvis**, amb la mateixa graella. w, λ i la durada mínima es trien junts amb els altres nou
   partits als escenaris ×¼.
4. **El criteri** del pla: A canvis 2 contra A context, el de la cadena, amb el seu decodificador triat igual. Només
   per saber-ho, A canvis 2 contra A canvis, i com és la q de cadascun.

Escriu `resultats/model-a-canvis2.json` (la clau del codi i les files) i `resultats/model-a-canvis2.md`. Tot són dades
obertes. Els mòduls de la T3e a la T3i no es toquen.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import itertools
import json
import math
import os
from collections.abc import Iterator
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from banc import avalua, degrada, fonts
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_contacte as t3h
from banc import model_a_context as t3e
from banc import model_a_quart as t3b
from banc.partit import PartitBanc
from cadena import canvis, decodifica, model
from cadena import decodifica_tocs as dt
from possessio.decodificacio import log_relativa

WS = (1.0, 2.0, 4.0, 8.0)
LAMS = (4.0, 8.0, 16.0, 32.0, 64.0)                 # més amunt que a la T3i, on es va triar el màxim (16)
DMINS = (1, 12, 25)
Q_ALTA = 0.3                                        # per saber-ho: quants canvis tenen la q alta a ±K imatges
CANVIS2 = "A canvis 2"
AMB_COST = {t3i.CANVIS: "q1", CANVIS2: "q2"}         # quina q fa servir cadascun
METODES = (t3e.CONTEXT, t3i.CANVIS, CANVIS2)
DIR_CAU = fonts.DIR_CAU / "a-canvis2"
DIR_RESULTATS = t3.DIR_RESULTATS


def taules(prova: str) -> Iterator[tuple[str, PartitBanc, pd.DataFrame]]:
    """Les taules del primer classificador de canvis als altres nou partits, als sis escenaris, amb les probabilitats
    dels primers dels grups de la T3h (com `t3i.mostres_de`), d'una en una."""
    for i in range(t3e.GRUPS):
        for (nom, e), primer in t3h.primer_del_grup((prova, i)).items():
            p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[e])
            yield nom, p, t3h.taula_segon(p, primer.astype(float))


def amb_canvis(p: PartitBanc, taula: pd.DataFrame, q1: np.ndarray) -> pd.DataFrame:
    """La taula del segon classificador de canvis: la del primer i el context de la seva q."""
    return pd.concat([taula, canvis.calcula(q1, p.trams)], axis=1)


def entrena_canvis(mostres: list[tuple[pd.DataFrame, np.ndarray]]) -> lgb.Booster:
    x = pd.concat([x for x, _ in mostres], ignore_index=True)
    y = np.concatenate([y for _, y in mostres])
    return lgb.train(t3i.PARAMS, lgb.Dataset(x, label=y, free_raw_data=True), num_boost_round=model.RONDES)


def models_dels_grups(prova: str) -> dict[str, lgb.Booster]:
    """El primer classificador de canvis per a cada partit d'entrenament: el del seu grup, entrenat amb els altres
    sis partits."""
    per_partit: dict[str, list] = {}
    for nom, p, taula in taules(prova):
        per_partit.setdefault(nom, []).append(t3i.mostres(p, taula))
    del_partit = {}
    for grup in t3e.grups(prova):
        entrenat = entrena_canvis([m for nom, llista in per_partit.items() if nom not in grup for m in llista])
        del_partit |= dict.fromkeys(grup, entrenat)
    return del_partit


def mostres_de(prova: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Les mostres del segon classificador per provar `prova`: els altres nou partits, als sis escenaris, amb la q del
    primer del seu grup."""
    del_partit = models_dels_grups(prova)
    xs, ys = [], []
    for nom, p, taula in taules(prova):
        x, y = t3i.mostres(p, amb_canvis(p, taula, t3i.q_de(del_partit[nom], taula)))
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def probabilitats(prova: str, entrena: bool = True) -> dict[str, np.ndarray]:
    """Les q del segon al partit `prova`, a cada escenari de la T3. Amb `entrena=False`, només les llegeix de la
    memòria cau, i si no hi són o són d'un altre codi, s'atura."""
    cami = DIR_CAU / f"{prova}.npz"
    desat = None
    if cami.exists():
        with np.load(cami, allow_pickle=False) as d:
            if str(d["clau"]) == CLAU:
                desat = {k: d[k] for k in d.files if k != "clau"}
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les probabilitats del segon classificador de canvis de {prova}, o són d'un "
                               "altre codi")
        x, y = mostres_de(prova)
        entrenat = lgb.train(t3i.PARAMS, lgb.Dataset(x, label=y, free_raw_data=True), num_boost_round=model.RONDES)
        del x
        primers = t3h.primer_de_la_prova(prova)
        q1s = t3i.probabilitats(prova, entrena=False)
        desat = {}
        for i, (nom_e, escenari) in enumerate(t3.ESCENARIS.items()):
            p = degrada.aplica(fonts.partit(prova), escenari)
            taula = amb_canvis(p, t3h.taula_segon(p, primers[nom_e].astype(float)), q1s[nom_e].astype(float))
            desat[f"e{i}"] = t3i.q_de(entrenat, taula).astype(np.float32)
        cami.parent.mkdir(parents=True, exist_ok=True)
        temporal = cami.with_name(f"{cami.name}.{os.getpid()}.part.npz")
        np.savez(temporal, clau=CLAU, **desat)
        temporal.replace(cami)
    return {e: desat[f"e{i}"] for i, e in enumerate(t3.ESCENARIS)}


def les_q(nom: str) -> dict[str, dict[str, np.ndarray]]:
    """La q del primer (T3i) i la del segon, a cada escenari."""
    return {"q1": t3i.probabilitats(nom, entrena=False), "q2": probabilitats(nom, entrena=False)}


def qualitat(q: np.ndarray, veritat: np.ndarray, trams: list[tuple[int, int]]) -> dict[str, float]:
    """L'AUC de la q contra l'objectiu (a les imatges de dins de les parts amb veritat H, A o D) i la part dels canvis
    de la veritat amb la q a `Q_ALTA` o més a `t3i.K` imatges o menys."""
    dins = np.zeros(len(veritat), dtype=bool)
    for inici, fi in trams:
        dins[inici:fi] = True
    dins &= np.isin(veritat, model.CLASSES)
    y = t3i.objectiu(veritat, trams)[dins]
    rang = pd.Series(q[dins]).rank().to_numpy()
    positius, negatius = int(y.sum()), int((~y).sum())
    auc = (rang[y].sum() - positius * (positius + 1) / 2) / (positius * negatius) if positius and negatius else math.nan
    altes = [q[max(c - t3i.K, 0):c + t3i.K + 1].max() >= Q_ALTA for c in t3i.canvis(veritat, trams)]
    return {"auc": float(auc), "canvis_q_alta": float(np.mean(altes)) if altes else math.nan}


def graella(tasca: tuple[str, str]) -> list[dict]:
    """Un partit i un escenari: A context amb el decodificador d'ara, i les probabilitats d'A contacte amb el cost
    après de la q del primer i de la del segon."""
    nom, escenari = tasca
    p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[escenari])
    comu = {"partit": nom, "font": p.font, "escenari": escenari}
    probes, prior = t3e.probabilitats(nom, entrena=False)
    files = []
    for lam, d_min in itertools.product(decodifica.GRAELLA_LAMBDA, decodifica.GRAELLA_DMIN):
        pred = decodifica.per_trams(probes[escenari].astype(float), prior, p.trams, lam, d_min)
        files.append({**comu, "metode": t3e.CONTEXT, "w": math.nan, "lam": lam, "d_min": d_min,
                      **avalua.puntua(p, pred)})
    probes, prior = t3h.probabilitats(nom, entrena=False)
    relativa = log_relativa(probes[escenari].astype(float), prior)
    qs = les_q(nom)
    for metode, quina in AMB_COST.items():
        q = qs[quina][escenari].astype(float)
        for w, lam, d_min in itertools.product(WS, LAMS, DMINS):
            pred = t3i.per_trams(relativa, q, p.trams, w, lam, d_min)
            files.append({**comu, "metode": metode, "w": w, "lam": lam, "d_min": d_min, **avalua.puntua(p, pred)})
    return files


def qualitats(tasca: tuple[str, str]) -> list[dict]:
    nom, escenari = tasca
    p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[escenari])
    trams = avalua.trams_valids(p)
    qs = les_q(nom)
    return [{"partit": nom, "escenari": escenari, "metode": metode,
             **qualitat(qs[quina][escenari].astype(float), p.veritat.astype(np.int8), trams)}
            for metode, quina in AMB_COST.items()]


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


def markdown(c: pd.DataFrame, c_canvis: pd.DataFrame, metodes: pd.DataFrame, q: pd.DataFrame, triades: dict,
             passa: dict[str, bool]) -> str:
    ordre = list(METODES)
    linies = ["# Banc obert · Un segon classificador de canvis (T3j)", "",
              "Generat amb `uv run python -I -m banc.model_a_canvis2`. Dades obertes: 7 partits de DFL (IDSSE, CC BY",
              "4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3j», i la capçalera de `banc/model_a_canvis2.py`.", "",
              f"**{t3e.CONTEXT}** és el model de la cadena (T3e), amb el decodificador d'ara. **{t3i.CANVIS}** són les",
              f"probabilitats d'{t3h.CONTACTE} amb el decodificador que cobra w · (−ln q) per canviar d'equip, amb la q",
              f"del classificador de canvis de la T3i. **{CANVIS2}** és el mateix amb la q d'un segon classificador",
              "de canvis, que també mira la q del primer al voltant de cada imatge. Tots tenen els paràmetres del",
              "decodificador triats amb els altres nou partits als escenaris ×¼, i els dos amb cost, amb la mateixa",
              "graella.", "",
              "## L'spellF1 i el macroF1 de cada mètode (mitjana dels deu partits)", ""]
    for columna, nom in (("spell_f1", "spellF1"), ("macro_f1", "macroF1")):
        t = metodes.pivot_table(index="escenari", columns="metode", values=columna, sort=False)[ordre]
        linies += [f"**{nom}**", "", "| escenari | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 1) + "|"]
        linies += [f"| {e} | " + " | ".join(f"{v:.3f}" for v in f) + " |" for e, f in t.iterrows()]
        linies.append("")
    linies += [f"## {CANVIS2} contra {t3e.CONTEXT} (spellF1): el criteri", "",
               *t3b._taula(c, CANVIS2, t3e.CONTEXT), "", *t3b._criteris(passa, False),
               f"## {CANVIS2} contra {t3i.CANVIS} (spellF1), només per saber-ho", "",
               "Les mateixes probabilitats d'equip i la mateixa graella: la diferència és el que afegeix el segon",
               "classificador de canvis.", "",
               *t3i._comparacio(c_canvis, CANVIS2, t3i.CANVIS), "",
               "## Com és la q (escenaris ×¼, mitjana dels deu partits), només per saber-ho", "",
               f"L'AUC és contra l'objectiu (un canvi a {t3i.K} imatges o menys). «Canvis amb q alta» és la part dels "
               f"canvis de la veritat amb la q a {Q_ALTA:g} o més a {t3i.K} imatges o menys.", "",
               "| escenari | AUC, " + " | AUC, ".join(AMB_COST) + " | canvis amb q alta, "
               + " | canvis amb q alta, ".join(AMB_COST) + " |", "|---" * (2 * len(AMB_COST) + 1) + "|"]
    mitjana = q.groupby(["escenari", "metode"], sort=False)[["auc", "canvis_q_alta"]].mean().unstack()
    for e, f in mitjana.iterrows():
        valors = [f[("auc", m)] for m in AMB_COST] + [f[("canvis_q_alta", m)] for m in AMB_COST]
        linies.append(f"| {e} | " + " | ".join(f"{v:.3f}" for v in valors) + " |")
    linies += ["", "## Possessions predites per cada real (mitjana dels deu partits), només per saber-ho", "",
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
    """El que fa les q del segon: la clau de la T3i (el primer, l'objectiu, l'entrenament), els grups, el context de
    la q i això."""
    h = hashlib.sha256((t3i.CLAU + repr((t3e.GRUPS, fonts.NOMS))).encode())
    h.update(Path(canvis.__file__).read_bytes())
    for funcio in (taules, amb_canvis, entrena_canvis, models_dels_grups, mostres_de, probabilitats):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + t3i.clau_dels_resultats()).encode())
    for modul in (t3i, t3h, t3e, t3b, t3, decodifica, dt, avalua, degrada):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def main() -> None:
    from banc import model_a_canvis2 as aquest          # pel nom del mòdul, perquè els processos fills el trobin

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=2, help="models alhora (cadascun fa servir 8 fils)")
    args = ap.parse_args()
    for nom in fonts.NOMS:                              # les d'A context, d'A contacte i de la T3i: abans cal fer-les
        t3e.probabilitats(nom, entrena=False)
        t3h.probabilitats(nom, entrena=False)
        t3i.probabilitats(nom, entrena=False)
    with ProcessPoolExecutor(max_workers=args.processos_models) as feina:
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.probabilitats, fonts.NOMS)):
            print(f"· {nom}: el segon classificador de canvis, fet", flush=True)
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        files = pd.DataFrame([f for tros in feina.map(aquest.graella, itertools.product(fonts.NOMS, t3.ESCENARIS))
                              for f in tros])
        q = pd.DataFrame([f for tros in feina.map(aquest.qualitats, itertools.product(fonts.NOMS, t3.QUARTS))
                          for f in tros])
    metodes, triades = tria_sense_mirar(files)
    c = t3b.comparacio(metodes, CANVIS2, t3e.CONTEXT)
    c_canvis = t3b.comparacio(metodes, CANVIS2, t3i.CANVIS)
    passa = t3b.compleix(c)
    desa = {"clau": clau_dels_resultats(), "passa": passa, "comparacio": t3.registres(c),
            "comparacio_canvis": t3.registres(c_canvis), "qualitat": t3.registres(q), "triades": triades,
            "files": t3.registres(files)}
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-a-canvis2.json").write_text(json.dumps(desa, indent=1, default=float, allow_nan=False))
    (DIR_RESULTATS / "model-a-canvis2.md").write_text(markdown(c, c_canvis, metodes, q, triades, passa))
    print((DIR_RESULTATS / "model-a-canvis2.md").read_text())


if __name__ == "__main__":
    main()
