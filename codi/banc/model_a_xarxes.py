"""La mitjana de cinc xarxes (T3o del pla per tocs, `docs/pla-tocs.md`, «T3o»).

    cd codi && uv run python -I -m banc.model_a_xarxes [--processos 12] [--processos-models 4]

A xarxa (T3m) tal qual, amb una sola diferència: en lloc d'una xarxa, les cinc de `cadena/xarxes.py` (entrenades
exactament com la de la T3m, cadascuna amb la seva llavor; la primera és la de la T3m), i el segon classificador en
rep la mitjana. Els mateixos primers (de la T3h), les mateixes mostres (la tria de la T3f), el mateix segon d'A
aturades, la q de la T3i i el decodificador amb la graella de la T3j.

1. **Les xarxes dels grups:** per entrenar el segon, les cinc de cada grup de la T3e, amb els altres sis partits
   (`dades/banc/a-xarxes-grups/`).
2. **Les xarxes del partit que es prova,** amb els altres nou (`dades/banc/a-xarxes-prova/`).
3. **El segon,** entrenat amb els nou partits i els sis escenaris, amb les probabilitats dels primers i de la mitjana
   de les xarxes dels grups. Les seves, als deu escenaris de la T3, a la memòria cau (`dades/banc/a-xarxes/`).
4. **El criteri** del pla: A xarxes contra A context, el de la cadena. Només per saber-ho, contra A xarxa (el mateix
   amb una sola xarxa), per font, i l'encert de l'equip per durada, amb pilota i sense.

Escriu `resultats/model-a-xarxes.json` (la clau del codi i les files) i `resultats/model-a-xarxes.md`. Tot són dades
obertes. Els mòduls de la T3e a la T3n no es toquen.
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

from banc import avalua, degrada, fonts, partit
from banc import decodificador_tocs as t3
from banc import model_a_aturades as t3k
from banc import model_a_canvis as t3i
from banc import model_a_canvis2 as t3j
from banc import model_a_contacte as t3h
from banc import model_a_context as t3e
from banc import model_a_possessio as t3f
from banc import model_a_quart as t3b
from banc import model_a_xarxa as t3m
from banc.partit import PartitBanc
from cadena import decodifica, model, xarxa, xarxes
from cadena import decodifica_tocs as dt
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ENTRENAMENT = t3m.ENTRENAMENT
XARXES = "A xarxes"
METODES = (t3e.CONTEXT, t3m.XARXA, XARXES)
SOLA_T3M = "la xarxa de la T3m sola"
SOLES = "la mitjana de les cinc sola"
ENCERT = (t3m.PRIMER, SOLA_T3M, SOLES, t3m.XARXA, XARXES)          # per saber-ho, abans de decodificar
DIR_CAU = fonts.DIR_CAU / "a-xarxes"
DIR_CAU_PROVA = fonts.DIR_CAU / "a-xarxes-prova"
DIR_CAU_GRUPS = fonts.DIR_CAU / "a-xarxes-grups"
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


def entrena_xarxes(noms: list[str]) -> tuple[tuple[xarxa.Xarxa, ...], list[list[float]]]:
    """Les cinc xarxes entrenades amb `noms`, als sis escenaris d'entrenament i amb la tria de la T3f: les mateixes
    mostres que `t3m.entrena_xarxa`."""
    xs, ys = [], []
    for nom in noms:
        for e in ENTRENAMENT:
            p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[e])
            files = t3f.tria(p.veritat, avalua.trams_valids(p))
            x, y = xarxa.mostres(p.tracking, p.trams, files, p.veritat[files])
            xs.append(x)
            ys.append(y)
    x = np.concatenate(xs)
    del xs
    return xarxes.entrena(x, np.concatenate(ys))


def xarxes_de_la_prova(prova: str, entrena: bool = True) -> dict[str, np.ndarray]:
    """La mitjana de les cinc xarxes al partit `prova`, als deu escenaris, entrenades amb els altres nou. A la memòria
    cau, amb la pèrdua de cada passada de cadascuna."""
    cami = DIR_CAU_PROVA / f"{prova}.npz"
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les probabilitats de les xarxes de {prova}, o són d'un altre codi")
        entrenades, perdues = entrena_xarxes([nom for nom in fonts.NOMS if nom != prova])
        desat = {f"e{i}": xarxes.probabilitats(entrenades, *_tracking_i_trams(degrada.aplica(fonts.partit(prova), e))
                                               ).astype(np.float32) for i, e in enumerate(t3.ESCENARIS.values())}
        desa(cami, perdues=np.array(perdues), **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(t3.ESCENARIS)}


def xarxes_del_grup(tasca: tuple[str, int]) -> dict[tuple[str, str], np.ndarray]:
    """La mitjana de les cinc xarxes als partits del grup `i` de `prova`, als sis escenaris d'entrenament, entrenades
    amb els altres sis (els mateixos que a la T3m). A la memòria cau."""
    prova, i = tasca
    grup = t3e.grups(prova)[i]
    claus = {(nom, e): f"p{j}_{k}" for j, nom in enumerate(grup) for k, e in enumerate(ENTRENAMENT)}
    cami = DIR_CAU_GRUPS / f"{prova}-{i}.npz"
    desat = llegeix(cami)
    if desat is None:
        entrenades, perdues = entrena_xarxes(t3m.per_entrenar_el_grup(prova, i))
        desat = {clau_: xarxes.probabilitats(entrenades, *_tracking_i_trams(degrada.aplica(fonts.partit(nom),
                                                                                          t3.ESCENARIS[e]))
                                             ).astype(np.float32) for (nom, e), clau_ in claus.items()}
        desa(cami, perdues=np.array(perdues), **desat)
    return {qui: desat[nom] for qui, nom in claus.items()}


def _tracking_i_trams(p: PartitBanc) -> tuple:
    return p.tracking, p.trams


def mostres_segon(prova: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Les mostres del segon per provar `prova`: els altres nou partits, als sis escenaris, amb les probabilitats del
    primer i de la mitjana de les xarxes dels grups (que no han vist el partit), i amb la tria de la T3f."""
    primers, de_les_xarxes = {}, {}
    for i in range(t3e.GRUPS):
        primers |= t3h.primer_del_grup((prova, i))
        de_les_xarxes |= xarxes_del_grup((prova, i))
    xs, ys = [], []
    for (nom, e), primer in primers.items():
        p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[e])
        x, y = t3f.mostres(p, t3m.taula_segon(p, primer.astype(float), de_les_xarxes[(nom, e)].astype(float)))
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def probabilitats(prova: str, entrena: bool = True) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Les d'A xarxes al partit `prova`, a cada escenari de la T3, i el prior. Amb `entrena=False`, només les llegeix
    de la memòria cau, i si no hi són o són d'un altre codi, s'atura."""
    cami = DIR_CAU / f"{prova}.npz"
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les probabilitats d'{XARXES} de {prova}, o són d'un altre codi")
        x, y = mostres_segon(prova)
        entrenat, prior = model.entrena(x, y), model.prior(y)
        del x
        primers = t3h.primer_de_la_prova(prova)
        de_les_xarxes = xarxes_de_la_prova(prova)
        desat = {"prior": prior}
        for i, (nom_e, escenari) in enumerate(t3.ESCENARIS.items()):
            p = degrada.aplica(fonts.partit(prova), escenari)
            taula = t3m.taula_segon(p, primers[nom_e].astype(float), de_les_xarxes[nom_e].astype(float))
            desat[f"e{i}"] = model.probabilitats(entrenat, taula).astype(np.float32)
        desa(cami, **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(t3.ESCENARIS)}, desat["prior"]


def de_qui(metode: str):
    return t3m.probabilitats if metode == t3m.XARXA else probabilitats


def graella(tasca: tuple[str, str]) -> list[dict]:
    """Un partit i un escenari: A context amb el decodificador d'ara, i A xarxa i A xarxes amb la q de la T3i i la
    graella de la T3j."""
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
    for metode in (t3m.XARXA, XARXES):
        probes, prior = de_qui(metode)(nom, entrena=False)
        relativa = log_relativa(probes[escenari].astype(float), prior)
        for w, lam, d_min in itertools.product(t3j.WS, t3j.LAMS, t3j.DMINS):
            pred = t3i.per_trams(relativa, q, p.trams, w, lam, d_min)
            files.append({**comu, "metode": metode, "w": w, "lam": lam, "d_min": d_min, **avalua.puntua(p, pred)})
    return files


def tria_sense_mirar(files: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Les files de cada mètode a cada partit, amb els paràmetres triats amb els altres nou als escenaris ×¼. També
    les triades."""
    triats, triades = [], {}
    for prova in fonts.NOMS:
        triades[prova] = {}
        for metode in METODES:
            seu = files[files["metode"] == metode]
            columnes = t3k.parametres(metode)
            millor = t3.millor(seu[seu["partit"] != prova], columnes)
            del_partit = seu[seu["partit"] == prova]
            tria = np.logical_and.reduce([del_partit[c] == v for c, v in zip(columnes, millor)])
            triats.append(del_partit[tria])
            triades[prova][metode] = tuple(int(v) if c == "d_min" else float(v) for c, v in zip(columnes, millor))
    return pd.concat(triats, ignore_index=True), triades


def encert(tasca: tuple[str, str]) -> list[dict]:
    """Un partit i un escenari ×¼: a les possessions H o A de la veritat, la part de les imatges on l'equip més probable
    és el de la veritat, per durada de la possessió i si la pilota es veu (abans de decodificar). Del primer sol, de
    la xarxa de la T3m sola, de la mitjana de les cinc sola, d'A xarxa i d'A xarxes."""
    nom, escenari = tasca
    p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[escenari])
    gt = p.veritat.astype(np.int8)
    vista = ~np.isnan(p.tracking.pilota[:, 0])
    durada = np.full(p.n, np.nan)
    for s, e, _ in pm.possession_spells(gt, avalua.trams_valids(p)):
        durada[s:e] = (e - s) / pm.FPS
    tram = pd.cut(durada, t3m.DURADES, labels=t3m.NOMS_DURADA, right=False)
    dins = ~np.isnan(durada)
    de_cadascun = {t3m.PRIMER: t3h.primer_de_la_prova(nom)[escenari],
                   SOLA_T3M: t3m.xarxa_de_la_prova(nom, entrena=False)[escenari],
                   SOLES: xarxes_de_la_prova(nom, entrena=False)[escenari],
                   t3m.XARXA: t3m.probabilitats(nom, entrena=False)[0][escenari],
                   XARXES: probabilitats(nom, entrena=False)[0][escenari]}
    files = []
    for metode, probes in de_cadascun.items():
        bo = np.asarray(model.CLASSES)[np.nan_to_num(probes, nan=-1.0).argmax(1)] == gt
        t = pd.DataFrame({"tram": tram[dins], "pilota": vista[dins], "bo": bo[dins]})
        files += [{"partit": nom, "escenari": escenari, "metode": metode, "durada": d, "pilota": bool(v),
                   "encert": float(g["bo"].mean()), "imatges": len(g)}
                  for (d, v), g in t.groupby(["tram", "pilota"], observed=True)]
    return files


def markdown(c: pd.DataFrame, c_xarxa: pd.DataFrame, metodes: pd.DataFrame, enc: pd.DataFrame, triades: dict,
             passa: dict[str, bool]) -> str:
    ordre = list(METODES)
    linies = ["# Banc obert · La mitjana de cinc xarxes (T3o)", "",
              "Generat amb `uv run python -I -m banc.model_a_xarxes`. Dades obertes: 7 partits de DFL (IDSSE, CC BY",
              "4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3o», i la capçalera de `banc/model_a_xarxes.py`.", "",
              f"**{t3e.CONTEXT}** és el model de la cadena (T3e), amb el decodificador d'ara. **{t3m.XARXA}** és el de",
              f"la T3m, amb una xarxa. **{XARXES}** és {t3m.XARXA} amb la mitjana de cinc xarxes entrenades igual, cadascuna",
              "amb la seva llavor (`cadena/xarxes.py`; la primera és la de la T3m). Tots tenen els paràmetres del",
              "decodificador triats amb els altres nou partits als escenaris ×¼.", "",
              "## L'spellF1 i el macroF1 de cada mètode (mitjana dels deu partits)", ""]
    for columna, nom in (("spell_f1", "spellF1"), ("macro_f1", "macroF1")):
        t = metodes.pivot_table(index="escenari", columns="metode", values=columna, sort=False)[ordre]
        linies += [f"**{nom}**", "", "| escenari | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 1) + "|"]
        linies += [f"| {e} | " + " | ".join(f"{x:.3f}" for x in f) + " |" for e, f in t.iterrows()]
        linies.append("")
    linies += [f"## {XARXES} contra {t3e.CONTEXT} (spellF1): el criteri", "",
               *t3b._taula(c, XARXES, t3e.CONTEXT), "", *t3b._criteris(passa, False),
               f"## {XARXES} contra {t3m.XARXA} (spellF1), només per saber-ho", "",
               "El mateix amb una sola xarxa: la diferència és el que hi afegeix la mitjana.", "",
               *t3i._comparacio(c_xarxa, XARXES, t3m.XARXA), "",
               "## Per font (spellF1, mitjana dels partits de cada font), només per saber-ho", "",
               "| escenari | font | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 2) + "|"]
    per_font = metodes.pivot_table(index=["escenari", "font"], columns="metode", values="spell_f1", sort=False)[ordre]
    linies += [f"| {e} | {f} | " + " | ".join(f"{x:.3f}" for x in fila) + " |" for (e, f), fila in per_font.iterrows()]
    linies += ["", "## L'encert de l'equip abans de decodificar (escenaris ×¼), només per saber-ho", "",
               "A les imatges de les possessions de la veritat, la part on l'equip més probable és el de la veritat,",
               f"per durada de la possessió i segons si la pilota es veu. *{t3m.PRIMER.capitalize()}* és el primer",
               f"classificador d'{t3h.CONTACTE} sol.", "",
               "| durada | pilota | " + " | ".join(ENCERT) + " |", "|---" * (len(ENCERT) + 2) + "|"]
    pes = enc.assign(bons=enc["encert"] * enc["imatges"]).groupby(["durada", "pilota", "metode"], sort=False)
    taxa = (pes["bons"].sum() / pes["imatges"].sum()).unstack()[list(ENCERT)]
    linies += [f"| {d} | {'sí' if v else 'no'} | " + " | ".join(f"{x:.3f}" for x in fila) + " |"
               for (d, v), fila in taxa.iterrows()]
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
    """El que fa les probabilitats d'A xarxes: la clau d'A xarxa (els primers, les mostres, l'aturada, la xarxa), les
    cinc xarxes i això."""
    h = hashlib.sha256((t3m.CLAU + repr((t3e.GRUPS, fonts.NOMS, partit.VERSIO))).encode())
    h.update(Path(xarxes.__file__).read_bytes())
    for funcio in (entrena_xarxes, xarxes_de_la_prova, xarxes_del_grup, mostres_segon, probabilitats):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + t3m.clau_dels_resultats()).encode())
    for modul in (t3m, t3k, t3j, t3i, t3h, t3f, t3e, t3b, t3, decodifica, dt, avalua, degrada):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def comprova_les_d_abans() -> None:
    """Les d'A context, d'A xarxa (i la seva xarxa sola), la q de la T3i i els primers de la T3h: abans cal fer-les.
    No les refà."""
    t3m.comprova_les_d_abans()
    for nom in fonts.NOMS:
        t3m.probabilitats(nom, entrena=False)
        t3m.xarxa_de_la_prova(nom, entrena=False)


def main() -> None:
    from banc import model_a_xarxes as aquest           # pel nom del mòdul, perquè els processos fills el trobin

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=4, help="models alhora")
    args = ap.parse_args()
    comprova_les_d_abans()
    with ProcessPoolExecutor(max_workers=args.processos_models) as feina:
        tasques = [(nom, i) for nom in fonts.NOMS for i in range(t3e.GRUPS)]
        for (nom, i), _ in zip(tasques, feina.map(aquest.xarxes_del_grup, tasques)):
            print(f"· {nom}: les xarxes del grup {i} fetes", flush=True)
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.xarxes_de_la_prova, fonts.NOMS)):
            print(f"· {nom}: les xarxes fetes", flush=True)
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.probabilitats, fonts.NOMS)):
            print(f"· {nom}: {XARXES} fet", flush=True)
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        files = pd.DataFrame([f for tros in feina.map(aquest.graella, itertools.product(fonts.NOMS, t3.ESCENARIS))
                              for f in tros])
        enc = pd.DataFrame([f for tros in feina.map(aquest.encert, itertools.product(fonts.NOMS, t3.QUARTS))
                            for f in tros])
    metodes, triades = tria_sense_mirar(files)
    c = t3b.comparacio(metodes, XARXES, t3e.CONTEXT)
    c_xarxa = t3b.comparacio(metodes, XARXES, t3m.XARXA)
    passa = t3b.compleix(c)
    desa_ = {"clau": clau_dels_resultats(), "passa": passa, "comparacio": t3.registres(c),
             "comparacio_xarxa": t3.registres(c_xarxa), "encert": t3.registres(enc), "triades": triades,
             "files": t3.registres(files)}
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-a-xarxes.json").write_text(json.dumps(desa_, indent=1, default=float, allow_nan=False))
    (DIR_RESULTATS / "model-a-xarxes.md").write_text(markdown(c, c_xarxa, metodes, enc, triades, passa))
    print((DIR_RESULTATS / "model-a-xarxes.md").read_text())


if __name__ == "__main__":
    main()
