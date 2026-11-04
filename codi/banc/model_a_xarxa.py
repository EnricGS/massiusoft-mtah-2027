"""Una xarxa que mira les posicions al voltant de la pilota (T3m del pla per tocs, `docs/pla-tocs.md`, «T3m»).

    cd codi && uv run python -I -m banc.model_a_xarxa [--processos 12] [--processos-models 3]

A aturades (T3k) tal qual, amb una sola diferència: el segon classificador també rep les probabilitats de la xarxa
(`cadena/xarxa.py`) i el seu context. Els mateixos primers (de la memòria cau de la T3h), les mateixes mostres (la tria
de la T3f), la q de la T3i i el decodificador amb la graella de la T3j.

1. **Les xarxes dels grups:** per entrenar el segon, la de cada grup de la T3e, entrenada amb els altres sis partits,
   com els primers (`dades/banc/a-xarxa-grups/`).
2. **La xarxa del partit que es prova,** entrenada amb els altres nou (`dades/banc/a-xarxa-prova/`).
3. **El segon,** entrenat amb els nou partits i els sis escenaris, amb les probabilitats dels primers i de les xarxes
   dels grups. Les seves, als deu escenaris de la T3, a la memòria cau (`dades/banc/a-xarxa/`).
4. **El criteri** del pla: A xarxa contra A context, el de la cadena. Només per saber-ho, contra A aturades (el mateix
   sense la xarxa), per font, i l'encert de l'equip per durada, amb pilota i sense: el primer sol, la xarxa sola, A
   aturades i A xarxa.

Escriu `resultats/model-a-xarxa.json` (la clau del codi i les files) i `resultats/model-a-xarxa.md`. Tot són dades
obertes. Els mòduls de la T3e a la T3l no es toquen.
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
from banc.partit import PartitBanc
from cadena import decodifica, model, xarxa
from cadena import decodifica_tocs as dt
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ENTRENAMENT = t3h.ENTRENAMENT
XARXA = "A xarxa"
METODES = (t3e.CONTEXT, t3k.ATURADES, XARXA)
PRIMER = "el primer"
SOLA = "la xarxa sola"
ENCERT = (PRIMER, SOLA, t3k.ATURADES, XARXA)        # per saber-ho, abans de decodificar
DURADES = (0, 1, 2, 5, math.inf)                    # s
NOMS_DURADA = ("<1 s", "1-2 s", "2-5 s", "≥5 s")
DIR_CAU = fonts.DIR_CAU / "a-xarxa"
DIR_CAU_PROVA = fonts.DIR_CAU / "a-xarxa-prova"
DIR_CAU_GRUPS = fonts.DIR_CAU / "a-xarxa-grups"
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


def per_entrenar_el_grup(prova: str, i: int) -> list[str]:
    """Amb qui aprèn la xarxa del grup `i` de `prova`: els altres sis, com el primer del grup."""
    grup = t3e.grups(prova)[i]
    return [nom for nom in fonts.NOMS if nom != prova and nom not in grup]


def entrena_xarxa(noms: list[str]) -> tuple[xarxa.Xarxa, list[float]]:
    """La xarxa entrenada amb `noms`, als sis escenaris d'entrenament i amb la tria de la T3f."""
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
    return xarxa.entrena(x, np.concatenate(ys))


def xarxa_de_la_prova(prova: str, entrena: bool = True) -> dict[str, np.ndarray]:
    """Les probabilitats de la xarxa al partit `prova`, als deu escenaris, entrenada amb els altres nou. A la memòria
    cau, amb la pèrdua de cada passada."""
    cami = DIR_CAU_PROVA / f"{prova}.npz"
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les probabilitats de la xarxa de {prova}, o són d'un altre codi")
        entrenada, perdua = entrena_xarxa([nom for nom in fonts.NOMS if nom != prova])
        desat = {f"e{i}": xarxa.probabilitats(entrenada, *_tracking_i_trams(degrada.aplica(fonts.partit(prova), e))
                                              ).astype(np.float32) for i, e in enumerate(t3.ESCENARIS.values())}
        desa(cami, perdua=np.array(perdua), **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(t3.ESCENARIS)}


def xarxa_del_grup(tasca: tuple[str, int]) -> dict[tuple[str, str], np.ndarray]:
    """Les probabilitats de la xarxa als partits del grup `i` de `prova`, als sis escenaris d'entrenament, entrenada
    amb els altres sis. A la memòria cau."""
    prova, i = tasca
    grup = t3e.grups(prova)[i]
    claus = {(nom, e): f"p{j}_{k}" for j, nom in enumerate(grup) for k, e in enumerate(ENTRENAMENT)}
    cami = DIR_CAU_GRUPS / f"{prova}-{i}.npz"
    desat = llegeix(cami)
    if desat is None:
        entrenada, perdua = entrena_xarxa(per_entrenar_el_grup(prova, i))
        desat = {clau_: xarxa.probabilitats(entrenada, *_tracking_i_trams(degrada.aplica(fonts.partit(nom),
                                                                                        t3.ESCENARIS[e]))
                                            ).astype(np.float32) for (nom, e), clau_ in claus.items()}
        desa(cami, perdua=np.array(perdua), **desat)
    return {qui: desat[nom] for qui, nom in claus.items()}


def _tracking_i_trams(p: PartitBanc) -> tuple:
    return p.tracking, p.trams


def taula_segon(p: PartitBanc, primer: np.ndarray, de_la_xarxa: np.ndarray) -> pd.DataFrame:
    """La del segon d'A aturades i els senyals de la xarxa."""
    return pd.concat([t3k.taula_segon(p, primer), xarxa.senyals_segon(de_la_xarxa, p.trams)], axis=1)


def mostres_segon(prova: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Les mostres del segon per provar `prova`: els altres nou partits, als sis escenaris, amb les probabilitats del
    primer i de la xarxa dels grups (que no han vist el partit), i amb la tria de la T3f."""
    primers, xarxes = {}, {}
    for i in range(t3e.GRUPS):
        primers |= t3h.primer_del_grup((prova, i))
        xarxes |= xarxa_del_grup((prova, i))
    xs, ys = [], []
    for (nom, e), primer in primers.items():
        p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[e])
        x, y = t3f.mostres(p, taula_segon(p, primer.astype(float), xarxes[(nom, e)].astype(float)))
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def probabilitats(prova: str, entrena: bool = True) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Les d'A xarxa al partit `prova`, a cada escenari de la T3, i el prior. Amb `entrena=False`, només les llegeix de
    la memòria cau, i si no hi són o són d'un altre codi, s'atura."""
    cami = DIR_CAU / f"{prova}.npz"
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les probabilitats d'{XARXA} de {prova}, o són d'un altre codi")
        x, y = mostres_segon(prova)
        entrenat, prior = model.entrena(x, y), model.prior(y)
        del x
        primers = t3h.primer_de_la_prova(prova)
        xarxes = xarxa_de_la_prova(prova)
        desat = {"prior": prior}
        for i, (nom_e, escenari) in enumerate(t3.ESCENARIS.items()):
            p = degrada.aplica(fonts.partit(prova), escenari)
            taula = taula_segon(p, primers[nom_e].astype(float), xarxes[nom_e].astype(float))
            desat[f"e{i}"] = model.probabilitats(entrenat, taula).astype(np.float32)
        desa(cami, **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(t3.ESCENARIS)}, desat["prior"]


def de_qui(metode: str):
    return t3k.probabilitats if metode == t3k.ATURADES else probabilitats


def graella(tasca: tuple[str, str]) -> list[dict]:
    """Un partit i un escenari: A context amb el decodificador d'ara, i A aturades i A xarxa amb la q de la T3i i la
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
    for metode in (t3k.ATURADES, XARXA):
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
    la xarxa sola, d'A aturades i d'A xarxa."""
    nom, escenari = tasca
    p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[escenari])
    gt = p.veritat.astype(np.int8)
    vista = ~np.isnan(p.tracking.pilota[:, 0])
    durada = np.full(p.n, np.nan)
    for s, e, _ in pm.possession_spells(gt, avalua.trams_valids(p)):
        durada[s:e] = (e - s) / pm.FPS
    tram = pd.cut(durada, DURADES, labels=NOMS_DURADA, right=False)
    dins = ~np.isnan(durada)
    de_cadascun = {PRIMER: t3h.primer_de_la_prova(nom)[escenari], SOLA: xarxa_de_la_prova(nom, entrena=False)[escenari],
                   t3k.ATURADES: t3k.probabilitats(nom, entrena=False)[0][escenari],
                   XARXA: probabilitats(nom, entrena=False)[0][escenari]}
    files = []
    for metode, probes in de_cadascun.items():
        bo = np.asarray(model.CLASSES)[np.nan_to_num(probes, nan=-1.0).argmax(1)] == gt
        t = pd.DataFrame({"tram": tram[dins], "pilota": vista[dins], "bo": bo[dins]})
        files += [{"partit": nom, "escenari": escenari, "metode": metode, "durada": d, "pilota": bool(v),
                   "encert": float(g["bo"].mean()), "imatges": len(g)}
                  for (d, v), g in t.groupby(["tram", "pilota"], observed=True)]
    return files


def markdown(c: pd.DataFrame, c_aturades: pd.DataFrame, metodes: pd.DataFrame, enc: pd.DataFrame, triades: dict,
             passa: dict[str, bool]) -> str:
    ordre = list(METODES)
    linies = ["# Banc obert · Una xarxa que mira les posicions al voltant de la pilota (T3m)", "",
              "Generat amb `uv run python -I -m banc.model_a_xarxa`. Dades obertes: 7 partits de DFL (IDSSE, CC BY 4.0)",
              "i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el criteri:",
              "`docs/pla-tocs.md`, «T3m», i la capçalera de `banc/model_a_xarxa.py`.", "",
              f"**{t3e.CONTEXT}** és el model de la cadena (T3e), amb el decodificador d'ara. **{t3k.ATURADES}** és el de la",
              f"T3k. **{XARXA}** és {t3k.ATURADES} amb les probabilitats de la xarxa (`cadena/xarxa.py`) al segon",
              "classificador. Tots tenen els paràmetres del decodificador triats amb els altres nou partits als",
              "escenaris ×¼.", "",
              "## L'spellF1 i el macroF1 de cada mètode (mitjana dels deu partits)", ""]
    for columna, nom in (("spell_f1", "spellF1"), ("macro_f1", "macroF1")):
        t = metodes.pivot_table(index="escenari", columns="metode", values=columna, sort=False)[ordre]
        linies += [f"**{nom}**", "", "| escenari | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 1) + "|"]
        linies += [f"| {e} | " + " | ".join(f"{x:.3f}" for x in f) + " |" for e, f in t.iterrows()]
        linies.append("")
    linies += [f"## {XARXA} contra {t3e.CONTEXT} (spellF1): el criteri", "",
               *t3b._taula(c, XARXA, t3e.CONTEXT), "", *t3b._criteris(passa, False),
               f"## {XARXA} contra {t3k.ATURADES} (spellF1), només per saber-ho", "",
               "El mateix sense la xarxa: la diferència és el que hi afegeix.", "",
               *t3i._comparacio(c_aturades, XARXA, t3k.ATURADES), "",
               "## Per font (spellF1, mitjana dels partits de cada font), només per saber-ho", "",
               "| escenari | font | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 2) + "|"]
    per_font = metodes.pivot_table(index=["escenari", "font"], columns="metode", values="spell_f1", sort=False)[ordre]
    linies += [f"| {e} | {f} | " + " | ".join(f"{x:.3f}" for x in fila) + " |" for (e, f), fila in per_font.iterrows()]
    linies += ["", "## L'encert de l'equip abans de decodificar (escenaris ×¼), només per saber-ho", "",
               "A les imatges de les possessions de la veritat, la part on l'equip més probable és el de la veritat,",
               f"per durada de la possessió i segons si la pilota es veu. *{PRIMER.capitalize()}* és el primer classificador",
               f"d'{t3h.CONTACTE} sol, i *{SOLA}*, la xarxa sola.", "",
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
    """El que fa les probabilitats d'A xarxa: la clau d'A aturades (els primers, les mostres, els senyals de
    l'aturada), la xarxa i això."""
    h = hashlib.sha256((t3k.CLAU + repr((t3e.GRUPS, fonts.NOMS, partit.VERSIO))).encode())
    h.update(Path(xarxa.__file__).read_bytes())
    for funcio in (per_entrenar_el_grup, entrena_xarxa, xarxa_de_la_prova, xarxa_del_grup, taula_segon, mostres_segon,
                   probabilitats):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + t3k.clau_dels_resultats()).encode())
    for modul in (t3k, t3j, t3i, t3h, t3f, t3e, t3b, t3, decodifica, dt, avalua, degrada):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def comprova_les_d_abans() -> None:
    """Les d'A context, d'A aturades, la q de la T3i i els primers de la T3h: abans cal fer-les. No les refà."""
    for nom in fonts.NOMS:
        t3e.probabilitats(nom, entrena=False)
        t3k.probabilitats(nom, entrena=False)
        t3i.probabilitats(nom, entrena=False)
        camins = [t3h.DIR_CAU_PRIMER / f"{nom}.npz"] + [t3h.DIR_CAU_GRUPS / f"{nom}-{i}.npz" for i in range(t3e.GRUPS)]
        if any(t3h.llegeix(c) is None for c in camins):
            raise RuntimeError(f"Falten els primers de la T3h de {nom}, o són d'un altre codi")


def main() -> None:
    from banc import model_a_xarxa as aquest            # pel nom del mòdul, perquè els processos fills el trobin

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=3, help="models alhora")
    args = ap.parse_args()
    comprova_les_d_abans()
    with ProcessPoolExecutor(max_workers=args.processos_models) as feina:
        tasques = [(nom, i) for nom in fonts.NOMS for i in range(t3e.GRUPS)]
        for (nom, i), _ in zip(tasques, feina.map(aquest.xarxa_del_grup, tasques)):
            print(f"· {nom}: la xarxa del grup {i} feta", flush=True)
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.xarxa_de_la_prova, fonts.NOMS)):
            print(f"· {nom}: la xarxa feta", flush=True)
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.probabilitats, fonts.NOMS)):
            print(f"· {nom}: {XARXA} fet", flush=True)
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        files = pd.DataFrame([f for tros in feina.map(aquest.graella, itertools.product(fonts.NOMS, t3.ESCENARIS))
                              for f in tros])
        enc = pd.DataFrame([f for tros in feina.map(aquest.encert, itertools.product(fonts.NOMS, t3.QUARTS))
                            for f in tros])
    metodes, triades = tria_sense_mirar(files)
    c = t3b.comparacio(metodes, XARXA, t3e.CONTEXT)
    c_aturades = t3b.comparacio(metodes, XARXA, t3k.ATURADES)
    passa = t3b.compleix(c)
    desa_ = {"clau": clau_dels_resultats(), "passa": passa, "comparacio": t3.registres(c),
             "comparacio_aturades": t3.registres(c_aturades), "encert": t3.registres(enc), "triades": triades,
             "files": t3.registres(files)}
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-a-xarxa.json").write_text(json.dumps(desa_, indent=1, default=float, allow_nan=False))
    (DIR_RESULTATS / "model-a-xarxa.md").write_text(markdown(c, c_aturades, metodes, enc, triades, passa))
    print((DIR_RESULTATS / "model-a-xarxa.md").read_text())


if __name__ == "__main__":
    main()
