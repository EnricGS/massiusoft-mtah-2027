"""La pilota morta, amb senyals de l'aturada (T3k del pla per tocs, `docs/pla-tocs.md`, «T3k»).

    cd codi && uv run python -I -m banc.model_a_aturades [--processos 12]

1. **El segon classificador d'A contacte** (T3h), amb els senyals de l'aturada (`cadena/aturades.py`) a més dels
   seus: els mateixos primers dels grups i del partit, de la memòria cau de la T3h, i les mateixes mostres de la T3f.
   Deixant cada partit fora: 10 models, i les probabilitats de cada un als deu escenaris de la T3, a la memòria cau
   (`dades/banc/a-aturades/`).
2. **El decodificador** d'A canvis (T3i), amb la q de la T3i: amb aquestes probabilitats és **A aturades**, i amb les
   d'A contacte, **A canvis**, amb la mateixa graella (la de la T3j). w, λ i la durada mínima es trien junts amb els
   altres nou partits als escenaris ×¼.
3. **El criteri** del pla: A aturades contra A context, el de la cadena, amb el seu decodificador triat igual. Només per
   saber-ho, A aturades contra A canvis, i com s'encerten les vores de les aturades.

Escriu `resultats/model-a-aturades.json` (la clau del codi i les files) i `resultats/model-a-aturades.md`. Tot són
dades obertes. Els mòduls de la T3e a la T3j no es toquen.
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

import numpy as np
import pandas as pd

from banc import avalua, degrada, fonts
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_canvis2 as t3j
from banc import model_a_contacte as t3h
from banc import model_a_context as t3e
from banc import model_a_possessio as t3f
from banc import model_a_quart as t3b
from banc.partit import PartitBanc
from cadena import aturades, decodifica, model
from cadena import decodifica_tocs as dt
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ATURADES = "A aturades"
AMB_COST = {t3i.CANVIS: t3h.probabilitats}           # de qui són les probabilitats d'equip (A aturades, les d'aquí)
METODES = (t3e.CONTEXT, t3i.CANVIS, ATURADES)
ERRA_S = 0.5                                        # per saber-ho: una vora errada per més d'això
DIR_CAU = fonts.DIR_CAU / "a-aturades"
DIR_RESULTATS = t3.DIR_RESULTATS


def taula_segon(p: PartitBanc, primer: np.ndarray) -> pd.DataFrame:
    """La del segon d'A contacte i els senyals de l'aturada."""
    return pd.concat([t3h.taula_segon(p, primer), aturades.calcula(p.tracking, p.trams)], axis=1)


def mostres_segon(prova: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Les mostres del segon per provar `prova`: els altres nou partits, als sis escenaris, amb les probabilitats del
    primer dels grups de la T3h, i amb la tria de la T3f."""
    primers = {}
    for i in range(t3e.GRUPS):
        primers |= t3h.primer_del_grup((prova, i))
    xs, ys = [], []
    for (nom, e), primer in primers.items():
        p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[e])
        x, y = t3f.mostres(p, taula_segon(p, primer.astype(float)))
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def probabilitats(prova: str, entrena: bool = True) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Les d'A aturades al partit `prova`, a cada escenari de la T3, i el prior. Amb `entrena=False`, només les llegeix
    de la memòria cau, i si no hi són o són d'un altre codi, s'atura."""
    cami = DIR_CAU / f"{prova}.npz"
    desat = None
    if cami.exists():
        with np.load(cami, allow_pickle=False) as d:
            if str(d["clau"]) == CLAU:
                desat = {k: d[k] for k in d.files if k != "clau"}
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les probabilitats d'{ATURADES} de {prova}, o són d'un altre codi")
        x, y = mostres_segon(prova)
        entrenat = model.entrena(x, y)
        prior = model.prior(y)
        del x
        primers = t3h.primer_de_la_prova(prova)
        desat = {"prior": prior}
        for i, (nom_e, escenari) in enumerate(t3.ESCENARIS.items()):
            p = degrada.aplica(fonts.partit(prova), escenari)
            desat[f"e{i}"] = model.probabilitats(entrenat, taula_segon(p, primers[nom_e].astype(float))
                                                 ).astype(np.float32)
        cami.parent.mkdir(parents=True, exist_ok=True)
        temporal = cami.with_name(f"{cami.name}.{os.getpid()}.part.npz")
        np.savez(temporal, clau=CLAU, **desat)
        temporal.replace(cami)
    return {e: desat[f"e{i}"] for i, e in enumerate(t3.ESCENARIS)}, desat["prior"]


def de_qui(metode: str):
    return AMB_COST.get(metode, probabilitats)


def graella(tasca: tuple[str, str]) -> list[dict]:
    """Un partit i un escenari: A context amb el decodificador d'ara, i les probabilitats d'A contacte i les d'A
    aturades amb el cost après de la T3i."""
    nom, escenari = tasca
    p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[escenari])
    comu = {"partit": nom, "font": p.font, "escenari": escenari}
    probes, prior = t3e.probabilitats(nom, entrena=False)
    files = []
    for lam, d_min in itertools.product(decodifica.GRAELLA_LAMBDA, decodifica.GRAELLA_DMIN):
        pred = decodifica.per_trams(probes[escenari].astype(float), prior, p.trams, lam, d_min)
        files.append({**comu, "metode": t3e.CONTEXT, "w": math.nan, "lam": lam, "d_min": d_min,
                      **avalua.puntua(p, pred)})
    q = t3i.probabilitats(nom, entrena=False)[escenari].astype(float)
    for metode in (t3i.CANVIS, ATURADES):
        probes, prior = de_qui(metode)(nom, entrena=False)
        relativa = log_relativa(probes[escenari].astype(float), prior)
        for w, lam, d_min in itertools.product(t3j.WS, t3j.LAMS, t3j.DMINS):
            pred = t3i.per_trams(relativa, q, p.trams, w, lam, d_min)
            files.append({**comu, "metode": metode, "w": w, "lam": lam, "d_min": d_min, **avalua.puntua(p, pred)})
    return files


def vores(veritat: np.ndarray, pred: np.ndarray, trams: list[tuple[int, int]]) -> list[dict]:
    """Per a cada aturada de la veritat: si en troba alguna imatge de D, i l'error de l'inici i de la represa (de la
    primera imatge de D predita que la toca a la darrera, en segons; positiu, tard)."""
    ple = pm.fill_abstentions(pred, trams)
    predites = [(s, e) for s, e, k in pm.segments(ple, trams) if k == pm.D]
    files = []
    for s, e, k in pm.segments(veritat, trams):
        if k != pm.D:
            continue
        tocs = [(a, b) for a, b in predites if a < e and s < b]
        if not tocs:
            files.append({"trobada": False, "inici_s": math.nan, "represa_s": math.nan})
            continue
        files.append({"trobada": True, "inici_s": (min(a for a, _ in tocs) - s) / pm.FPS,
                      "represa_s": (max(b for _, b in tocs) - e) / pm.FPS})
    return files


def les_vores(tasca: tuple[str, str, dict]) -> list[dict]:
    """Un partit i un escenari ×¼, amb els paràmetres triats: les vores de les aturades d'A canvis i d'A aturades."""
    nom, escenari, triades = tasca
    p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[escenari])
    q = t3i.probabilitats(nom, entrena=False)[escenari].astype(float)
    files = []
    for metode in (t3i.CANVIS, ATURADES):
        probes, prior = de_qui(metode)(nom, entrena=False)
        w, lam, d_min = triades[metode]
        pred = t3i.per_trams(log_relativa(probes[escenari].astype(float), prior), q, p.trams, w, lam, d_min)
        files += [{"partit": nom, "escenari": escenari, "metode": metode, **f}
                  for f in vores(p.veritat.astype(np.int8), pred, avalua.trams_valids(p))]
    return files


def resum_de_les_vores(v: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i mètode: la part de les aturades que troba, i de les trobades, la part amb l'inici i amb la
    represa errats per més d'`ERRA_S`."""
    g = v.groupby(["escenari", "metode"], sort=False)
    trobades = v[v["trobada"]].groupby(["escenari", "metode"], sort=False)
    return pd.DataFrame({"trobades": g["trobada"].mean(),
                         "inici": trobades["inici_s"].apply(lambda s: (s.abs() > ERRA_S).mean()),
                         "represa": trobades["represa_s"].apply(lambda s: (s.abs() > ERRA_S).mean())}).reset_index()


def parametres(metode: str) -> list[str]:
    return ["lam", "d_min"] if metode == t3e.CONTEXT else ["w", "lam", "d_min"]


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


def markdown(c: pd.DataFrame, c_canvis: pd.DataFrame, metodes: pd.DataFrame, v: pd.DataFrame, triades: dict,
             passa: dict[str, bool]) -> str:
    ordre = list(METODES)
    linies = ["# Banc obert · La pilota morta, amb senyals de l'aturada (T3k)", "",
              "Generat amb `uv run python -I -m banc.model_a_aturades`. Dades obertes: 7 partits de DFL (IDSSE, CC BY",
              "4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3k», i la capçalera de `banc/model_a_aturades.py`.", "",
              f"**{t3e.CONTEXT}** és el model de la cadena (T3e), amb el decodificador d'ara. **{t3i.CANVIS}** són les",
              f"probabilitats d'{t3h.CONTACTE} amb el decodificador que cobra w · (−ln q) per canviar d'equip, amb la q",
              f"de la T3i. **{ATURADES}** és el mateix amb el segon classificador d'{t3h.CONTACTE} amb els senyals de",
              "l'aturada a més dels seus. Tots tenen els paràmetres del decodificador triats amb els altres nou partits",
              "als escenaris ×¼, i els dos amb cost, amb la mateixa graella.", "",
              "## L'spellF1 i el macroF1 de cada mètode (mitjana dels deu partits)", ""]
    for columna, nom in (("spell_f1", "spellF1"), ("macro_f1", "macroF1")):
        t = metodes.pivot_table(index="escenari", columns="metode", values=columna, sort=False)[ordre]
        linies += [f"**{nom}**", "", "| escenari | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 1) + "|"]
        linies += [f"| {e} | " + " | ".join(f"{x:.3f}" for x in f) + " |" for e, f in t.iterrows()]
        linies.append("")
    linies += [f"## {ATURADES} contra {t3e.CONTEXT} (spellF1): el criteri", "",
               *t3b._taula(c, ATURADES, t3e.CONTEXT), "", *t3b._criteris(passa, False),
               f"## {ATURADES} contra {t3i.CANVIS} (spellF1), només per saber-ho", "",
               "La mateixa q i la mateixa graella: la diferència és el que afegeixen els senyals de l'aturada.", "",
               *t3i._comparacio(c_canvis, ATURADES, t3i.CANVIS), "",
               "## Les vores de les aturades (escenaris ×¼, totes les dels deu partits), només per saber-ho", "",
               f"*Trobades*: la part de les aturades de la veritat amb alguna imatge de D predita. *Inici* i *represa*: "
               f"de les trobades, la part amb la vora errada per més de {ERRA_S:g} s.", "",
               "| escenari | mètode | trobades | inici | represa |", "|---|---|---|---|---|"]
    linies += [f"| {f.escenari} | {f.metode} | {f.trobades:.3f} | {f.inici:.3f} | {f.represa:.3f} |"
               for f in v.itertuples()]
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
            noms = dict(zip(parametres(m), valors))
            w = f"w = {noms['w']:g}, " if "w" in noms else ""
            trossos.append(f"{m}: {w}λ = {noms['lam']:g}, durada mínima {noms['d_min']}")
        clau_ = " · ".join(trossos)
        compta[clau_] = compta.get(clau_, 0) + 1
    linies += [f"- {k} ({n} partits)" for k, n in compta.items()]
    return "\n".join(linies + [""])


def clau() -> str:
    """El que fa les probabilitats d'A aturades: la clau d'A contacte (els primers, les mostres de la T3f), els senyals
    de l'aturada i això."""
    h = hashlib.sha256((t3h.CLAU + repr((t3e.GRUPS, fonts.NOMS))).encode())
    h.update(Path(aturades.__file__).read_bytes())
    for funcio in (taula_segon, mostres_segon, probabilitats):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + t3i.clau_dels_resultats()).encode())
    for modul in (t3j, t3i, t3h, t3f, t3e, t3b, t3, decodifica, dt, avalua, degrada):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def main() -> None:
    from banc import model_a_aturades as aquest         # pel nom del mòdul, perquè els processos fills el trobin

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=2, help="models alhora (cadascun fa servir 8 fils)")
    args = ap.parse_args()
    for nom in fonts.NOMS:                              # les d'A context, d'A contacte i la q: abans cal fer-les
        t3e.probabilitats(nom, entrena=False)
        t3h.probabilitats(nom, entrena=False)
        t3i.probabilitats(nom, entrena=False)
    with ProcessPoolExecutor(max_workers=args.processos_models) as feina:
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.probabilitats, fonts.NOMS)):
            print(f"· {nom}: {ATURADES} fet", flush=True)
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        files = pd.DataFrame([f for tros in feina.map(aquest.graella, itertools.product(fonts.NOMS, t3.ESCENARIS))
                              for f in tros])
        metodes, triades = tria_sense_mirar(files)
        tasques = [(nom, e, triades[nom]) for nom in fonts.NOMS for e in t3.QUARTS]
        v = resum_de_les_vores(pd.DataFrame([f for tros in feina.map(aquest.les_vores, tasques) for f in tros]))
    c = t3b.comparacio(metodes, ATURADES, t3e.CONTEXT)
    c_canvis = t3b.comparacio(metodes, ATURADES, t3i.CANVIS)
    passa = t3b.compleix(c)
    desa = {"clau": clau_dels_resultats(), "passa": passa, "comparacio": t3.registres(c),
            "comparacio_canvis": t3.registres(c_canvis), "vores": t3.registres(v), "triades": triades,
            "files": t3.registres(files)}
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-a-aturades.json").write_text(json.dumps(desa, indent=1, default=float, allow_nan=False))
    (DIR_RESULTATS / "model-a-aturades.md").write_text(markdown(c, c_canvis, metodes, v, triades, passa))
    print((DIR_RESULTATS / "model-a-aturades.md").read_text())


if __name__ == "__main__":
    main()
