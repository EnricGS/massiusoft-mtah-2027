"""Cada possessió, amb prou mostres (T3f del pla per tocs, `docs/pla-tocs.md`, «T3f»).

    cd codi && uv run python -I -m banc.model_a_possessio [--processos 12]

És A context (T3e) tal qual, amb una sola diferència: quines imatges s'aprenen (`tria`). Com ara, una de cada 16
amb veritat H, A o D; però cada possessió H o A de la veritat (les que puntua l'spellF1) que en tingui menys de 8
en passa a tenir 8, repartides per igual (totes, si en té menys). Als dos classificadors.

1. **El primer classificador** (A control, amb aquestes mostres): al partit que es prova, entrenat amb els altres
   nou (`dades/banc/a-possessio-primer/`); i, per entrenar el segon, el de cada grup de la T3e, entrenat amb els
   altres sis (`dades/banc/a-possessio-grups/`).
2. **El segon, A per possessió,** entrenat amb els nou partits i els sis escenaris, amb les probabilitats dels
   grups. Les seves, als deu escenaris de la T3, a la memòria cau (`dades/banc/a-possessio/`).
3. **Totes les combinacions** del decodificador d'A amb A context i A per possessió, a cada partit i escenari, i la
   de cada partit triada amb els altres nou als escenaris ×¼, com a la T3c, la T3d i la T3e.
4. **El criteri** del pla: A per possessió contra A context, el de la cadena. Només per saber-ho, les possessions
   predites per cada real i l'encert de l'equip per durada de la possessió, als escenaris ×¼.

Escriu `resultats/model-a-possessio.json` (la clau del codi i les files) i `resultats/model-a-possessio.md`. Tot
són dades obertes. Els mòduls de la T3d i la T3e no es toquen: les seves claus i els resultats d'A context, que són
els de la cadena, queden com són.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import inspect
import itertools
import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from banc import avalua, degrada, fonts
from banc import decodificador_tocs as t3
from banc import model_a_context as t3e
from banc import model_a_control as t3d
from banc import model_a_quart as t3b
from banc.partit import PartitBanc
from cadena import decodifica, model, senyals
from possessio.oficial import possession_metrics as pm

ENTRENAMENT = t3e.ENTRENAMENT
MINIM = 8                                   # mostres per possessió, com a mínim
POSSESSIO = "A per possessió"
CLASSIFICADORS = (t3e.CONTEXT, POSSESSIO)
DIR_CAU = fonts.DIR_CAU / "a-possessio"
DIR_CAU_PRIMER = fonts.DIR_CAU / "a-possessio-primer"
DIR_CAU_GRUPS = fonts.DIR_CAU / "a-possessio-grups"
DIR_RESULTATS = t3.DIR_RESULTATS
DURADES = (0, 1, 2, 5, 10, np.inf)          # s
NOMS_DURADA = ("<1 s", "1-2 s", "2-5 s", "5-10 s", ">10 s")


def tria(etiqueta: np.ndarray, trams: list[tuple[int, int]], pas: int = model.PAS, minim: int = MINIM) -> np.ndarray:
    """Les imatges que s'aprenen, en ordre: una de cada `pas` amb veritat H, A o D (com `model.mostres`), però cada
    possessió H o A de la mètrica (`trams`: on es puntua) que en tingui menys de `minim` en passa a tenir `minim`,
    repartides per igual (totes, si en té menys)."""
    triades = np.zeros(len(etiqueta), dtype=bool)
    triades[np.flatnonzero(np.isin(etiqueta, model.CLASSES))[::pas]] = True
    for inici, final, _ in pm.possession_spells(etiqueta.astype(np.int8), trams):
        if triades[inici:final].sum() < minim:
            triades[inici:final] = False
            triades[np.round(np.linspace(inici, final - 1, min(minim, final - inici))).astype(int)] = True
    return np.flatnonzero(triades)


def mostres(p: PartitBanc, taula: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    """Com `model.mostres`, amb les imatges de `tria`: cadascuna també girada."""
    t = tria(p.veritat, avalua.trams_valids(p))
    x = taula.iloc[t].reset_index(drop=True)
    y = p.veritat[t]
    return (pd.concat([x, senyals.intercanvia(x)], ignore_index=True),
            np.concatenate([y, model.GIRA[y]]).astype(np.int8))


@functools.cache
def mostres_primer(nom: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Les mostres d'A control d'un partit, als sis escenaris d'entrenament, amb `tria` (un cop per procés)."""
    xs, ys = [], []
    for escenari in ENTRENAMENT:
        p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[escenari])
        x, y = mostres(p, t3d.taula(p))
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def entrena_primer(noms: list[str]):
    m = [mostres_primer(nom) for nom in noms]
    return model.entrena(pd.concat([x for x, _ in m], ignore_index=True), np.concatenate([y for _, y in m]))


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


def primer_de_la_prova(prova: str) -> dict[str, np.ndarray]:
    """Les probabilitats del primer classificador al partit `prova`, als deu escenaris, entrenat amb els altres nou.
    A la memòria cau."""
    cami = DIR_CAU_PRIMER / f"{prova}.npz"
    desat = llegeix(cami)
    if desat is None:
        entrenat = entrena_primer([nom for nom in fonts.NOMS if nom != prova])
        desat = {f"e{i}": model.probabilitats(entrenat, t3d.taula(degrada.aplica(fonts.partit(prova), e))
                                              ).astype(np.float32) for i, e in enumerate(t3.ESCENARIS.values())}
        desa(cami, **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(t3.ESCENARIS)}


def primer_del_grup(tasca: tuple[str, int]) -> dict[tuple[str, str], np.ndarray]:
    """Les probabilitats del primer classificador als partits del grup `i` de `prova` (els grups de la T3e), als sis
    escenaris d'entrenament, entrenat amb els altres sis. A la memòria cau."""
    prova, i = tasca
    grup = t3e.grups(prova)[i]
    claus = {(nom, e): f"p{j}_{k}" for j, nom in enumerate(grup) for k, e in enumerate(ENTRENAMENT)}
    cami = DIR_CAU_GRUPS / f"{prova}-{i}.npz"
    desat = llegeix(cami)
    if desat is None:
        entrenat = entrena_primer([nom for nom in fonts.NOMS if nom != prova and nom not in grup])
        desat = {clau_: model.probabilitats(entrenat, t3d.taula(degrada.aplica(fonts.partit(nom), t3.ESCENARIS[e]))
                                            ).astype(np.float32) for (nom, e), clau_ in claus.items()}
        desa(cami, **desat)
    return {qui: desat[nom] for qui, nom in claus.items()}


def mostres_segon(prova: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Les mostres del segon classificador per provar `prova`: els altres nou partits, als sis escenaris, amb les
    probabilitats del primer que no ha vist cap d'ells, i amb `tria`."""
    primers = {}
    for i in range(t3e.GRUPS):
        primers |= primer_del_grup((prova, i))
    xs, ys = [], []
    for (nom, e), primer in primers.items():
        p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[e])
        x, y = mostres(p, t3e.taula(p, primer.astype(float)))
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def probabilitats(prova: str, entrena: bool = True) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Les d'A per possessió al partit `prova`, a cada escenari de la T3, i el prior. Amb `entrena=False`, només les
    llegeix de la memòria cau, i si no hi són o són d'un altre codi, s'atura."""
    cami = DIR_CAU / f"{prova}.npz"
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les probabilitats d'{POSSESSIO} de {prova}, o són d'un altre codi")
        x, y = mostres_segon(prova)
        entrenat = model.entrena(x, y)
        prior = model.prior(y)
        del x
        primers = primer_de_la_prova(prova)
        desat = {"prior": prior}
        for i, (nom_e, escenari) in enumerate(t3.ESCENARIS.items()):
            p = degrada.aplica(fonts.partit(prova), escenari)
            desat[f"e{i}"] = model.probabilitats(entrenat, t3e.taula(p, primers[nom_e].astype(float))
                                                 ).astype(np.float32)
        desa(cami, **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(t3.ESCENARIS)}, desat["prior"]


def de_qui(metode: str):
    return {t3e.CONTEXT: t3e.probabilitats, POSSESSIO: probabilitats}[metode]


def graella(tasca: tuple[str, str]) -> list[dict]:
    """Un partit i un escenari: totes les combinacions del decodificador d'A, amb cada classificador."""
    nom, escenari = tasca
    p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[escenari])
    comu = {"partit": nom, "font": p.font, "escenari": escenari}
    files = []
    for metode in CLASSIFICADORS:
        probes, prior = de_qui(metode)(nom, entrena=False)
        proba = probes[escenari].astype(float)
        for lam, d_min in itertools.product(decodifica.GRAELLA_LAMBDA, decodifica.GRAELLA_DMIN):
            pred = decodifica.per_trams(proba, prior, p.trams, lam, d_min)
            files.append({**comu, "metode": metode, "lam": lam, "d_min": d_min, **avalua.puntua(p, pred)})
    return files


def tria_sense_mirar(files: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Les files de cada classificador a cada partit, amb el decodificador triat amb els altres nou als escenaris ×¼.
    També les triades."""
    triats, triades = [], {}
    for prova in fonts.NOMS:
        triades[prova] = {}
        for metode in CLASSIFICADORS:
            seu = files[files["metode"] == metode]
            lam, d_min = t3.millor(seu[seu["partit"] != prova], ["lam", "d_min"])
            del_partit = seu[seu["partit"] == prova]
            triats.append(del_partit[(del_partit["lam"] == lam) & (del_partit["d_min"] == d_min)])
            triades[prova][metode] = (float(lam), int(d_min))
    return pd.concat(triats, ignore_index=True), triades


def encert(tasca: tuple[str, str, dict]) -> list[dict]:
    """A cada possessió de la veritat d'un partit i un escenari, i amb cada classificador: quina part de les imatges
    tenen l'equip bo abans de decodificar (P(H) contra P(A)) i després, amb el decodificador triat."""
    nom, escenari, triades = tasca
    p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[escenari])
    files = []
    for metode in CLASSIFICADORS:
        probes, prior = de_qui(metode)(nom, entrena=False)
        proba = probes[escenari].astype(float)
        pred = decodifica.per_trams(proba, prior, p.trams, *triades[metode])
        for inici, final, k in pm.possession_spells(p.veritat.astype(np.int8), avalua.trams_valids(p)):
            tros = slice(inici, final)
            files.append({"partit": nom, "escenari": escenari, "metode": metode, "durada": (final - inici) / 25,
                          "encert_imatge": float(((proba[tros, 0] > proba[tros, 1]) == (k == pm.H)).mean()),
                          "encert_decodificat": float((pred[tros] == k).mean())})
    return files


def encert_per_durada(files: pd.DataFrame) -> pd.DataFrame:
    """La mitjana per possessió, per durada (files) i classificador (columnes)."""
    tram = pd.cut(files["durada"], DURADES, labels=NOMS_DURADA, right=False)
    t = files.groupby([tram, "metode"], observed=True)[["encert_imatge", "encert_decodificat"]].mean().unstack()
    return t.swaplevel(axis=1).sort_index(axis=1)


def markdown(c: pd.DataFrame, metodes: pd.DataFrame, triades: dict, passa: dict[str, bool],
             encerts: pd.DataFrame) -> str:
    ordre = list(CLASSIFICADORS)
    linies = ["# Banc obert · Cada possessió, amb prou mostres (T3f)", "",
              "Generat amb `uv run python -I -m banc.model_a_possessio`. Dades obertes: 7 partits de DFL (IDSSE, CC",
              "BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3f», i la capçalera de `banc/model_a_possessio.py`.", "",
              f"**{t3e.CONTEXT}** és el model de la cadena (T3e), i **{POSSESSIO}**, el mateix amb una altra tria de",
              f"les imatges que s'aprenen: cada possessió de la veritat, com a mínim amb {MINIM}. Tots dos tenen el",
              "decodificador triat amb els altres nou partits als escenaris ×¼.", "",
              "## L'spellF1 i el macroF1 de cada classificador (mitjana dels deu partits)", ""]
    for columna, nom in (("spell_f1", "spellF1"), ("macro_f1", "macroF1")):
        t = metodes.pivot_table(index="escenari", columns="metode", values=columna, sort=False)[ordre]
        linies += [f"**{nom}**", "", "| escenari | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 1) + "|"]
        linies += [f"| {e} | " + " | ".join(f"{v:.3f}" for v in f) + " |" for e, f in t.iterrows()]
        linies.append("")
    linies += [f"## {POSSESSIO} contra {t3e.CONTEXT} (spellF1): el criteri", "",
               *t3b._taula(c, POSSESSIO, t3e.CONTEXT), "", *t3b._criteris(passa, False),
               "## Possessions predites per cada real (mitjana dels deu partits), només per saber-ho", "",
               "| escenari | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 1) + "|"]
    rati = (metodes["possessions"] / metodes["possessions_reals"]).groupby(
        [metodes["escenari"], metodes["metode"]], sort=False).mean().unstack()[ordre]
    linies += [f"| {e} | " + " | ".join(f"{v:.2f}" for v in f) + " |" for e, f in rati.iterrows()]
    linies += ["", "## L'encert de l'equip per durada de la possessió, només per saber-ho", "",
               "Als quatre escenaris ×¼: la part de les imatges de cada possessió de la veritat amb l'equip bo, de",
               "mitjana per possessió. *Abans*, la P(H) contra la P(A) de cada imatge; *després*, amb el decodificador.",
               "", "| durada | " + " | ".join(f"{m}, abans | {m}, després" for m in ordre) + " |",
               "|---" * (2 * len(ordre) + 1) + "|"]
    linies += [f"| {d} | " + " | ".join(f"{f[(m, 'encert_imatge')]:.3f} | {f[(m, 'encert_decodificat')]:.3f}"
                                         for m in ordre) + " |" for d, f in encerts.iterrows()]
    linies += ["", "## Els decodificadors triats (cada partit, amb els altres nou)", ""]
    compta: dict[str, int] = {}
    for t in triades.values():
        clau_ = " · ".join(f"{m}: λ = {lam:g}, durada mínima {d}" for m, (lam, d) in t.items())
        compta[clau_] = compta.get(clau_, 0) + 1
    linies += [f"- {k} ({n} partits)" for k, n in compta.items()]
    return "\n".join(linies + [""])


def clau() -> str:
    """El que fa les probabilitats d'A per possessió: la clau d'A context (els senyals, els grups), la tria i això."""
    h = hashlib.sha256((t3e.CLAU + repr((ENTRENAMENT, MINIM, model.PAS, fonts.NOMS))).encode())
    for modul in (avalua, pm):
        h.update(Path(modul.__file__).read_bytes())
    for funcio in (tria, mostres, mostres_primer, entrena_primer, primer_de_la_prova, primer_del_grup,
                   mostres_segon, probabilitats):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + t3e.clau_dels_resultats()).encode())
    for modul in (t3e, t3d, t3b, t3, decodifica, avalua, degrada):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def main() -> None:
    from banc import model_a_possessio as aquest        # pel nom del mòdul, perquè els processos fills el trobin

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=2, help="models alhora (cadascun fa servir 8 fils)")
    args = ap.parse_args()
    for nom in fonts.NOMS:                              # les d'A context (T3e): abans cal fer-les
        t3e.probabilitats(nom, entrena=False)
    with ProcessPoolExecutor(max_workers=args.processos_models) as feina:
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.primer_de_la_prova, fonts.NOMS)):
            print(f"· {nom}: el primer, fet", flush=True)
        tasques = list(itertools.product(fonts.NOMS, range(t3e.GRUPS)))
        for (nom, i), _ in zip(tasques, feina.map(aquest.primer_del_grup, tasques)):
            print(f"· {nom}: el primer, grup {i + 1} de {t3e.GRUPS}, fet", flush=True)
    with ProcessPoolExecutor(max_workers=args.processos_models) as feina:
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.probabilitats, fonts.NOMS)):
            print(f"· {nom}: {POSSESSIO} fet", flush=True)
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        tasques = list(itertools.product(fonts.NOMS, t3.ESCENARIS))
        files = pd.DataFrame([f for tros in feina.map(aquest.graella, tasques) for f in tros])
        metodes, triades = tria_sense_mirar(files)
        tasques = [(nom, e, triades[nom]) for nom in fonts.NOMS for e in t3.QUARTS]
        encerts = encert_per_durada(pd.DataFrame([f for tros in feina.map(aquest.encert, tasques) for f in tros]))
    c = t3b.comparacio(metodes, POSSESSIO, t3e.CONTEXT)
    passa = t3b.compleix(c)
    desa_ = {"clau": clau_dels_resultats(), "passa": passa, "comparacio": t3.registres(c), "triades": triades,
             "encert": t3.registres(encerts.stack(level=0, future_stack=True).reset_index()),
             "files": t3.registres(files)}
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-a-possessio.json").write_text(json.dumps(desa_, indent=1, default=float, allow_nan=False))
    (DIR_RESULTATS / "model-a-possessio.md").write_text(markdown(c, metodes, triades, passa, encerts))
    print((DIR_RESULTATS / "model-a-possessio.md").read_text())


if __name__ == "__main__":
    main()
