"""El darrer contacte, com a senyal (T3h del pla per tocs, `docs/pla-tocs.md`, «T3h»).

    cd codi && uv run python -I -m banc.model_a_contacte [--processos 12]

És A per possessió (T3f) tal qual, amb una sola diferència: el primer classificador també té els senyals del darrer
contacte (`cadena/contacte.py`). El segon porta els del primer, i per tant també els nous. Les mateixes mostres
(`model_a_possessio.tria`), els mateixos grups i el mateix LightGBM.

1. **El primer classificador** (A control amb el contacte): al partit que es prova, entrenat amb els altres nou
   (`dades/banc/a-contacte-primer/`); i, per entrenar el segon, el de cada grup de la T3e, entrenat amb els altres
   sis (`dades/banc/a-contacte-grups/`).
2. **El segon, A contacte,** entrenat amb els nou partits i els sis escenaris, amb les probabilitats dels grups. Les
   seves, als deu escenaris de la T3, a la memòria cau (`dades/banc/a-contacte/`).
3. **Totes les combinacions** del decodificador d'A amb A context, A per possessió i A contacte, a cada partit i
   escenari, i la de cada partit triada amb els altres nou als escenaris ×¼, com fins ara.
4. **El criteri** del pla: A contacte contra A context, el de la cadena. Només per saber-ho, A contacte contra A per
   possessió (les mateixes mostres, sense els senyals nous), les possessions predites per cada real i l'encert de
   l'equip per durada de la possessió, als escenaris ×¼.

Escriu `resultats/model-a-contacte.json` (la clau del codi i les files) i `resultats/model-a-contacte.md`. Tot són
dades obertes. Els mòduls de la T3d a la T3f no es toquen: les seves claus i els seus resultats queden com són.
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
from banc import model_a_possessio as t3f
from banc import model_a_quart as t3b
from banc.partit import PartitBanc
from cadena import contacte, context, decodifica, model
from possessio.oficial import possession_metrics as pm

ENTRENAMENT = t3f.ENTRENAMENT
CONTACTE = "A contacte"
CLASSIFICADORS = (t3e.CONTEXT, t3f.POSSESSIO, CONTACTE)
DIR_CAU = fonts.DIR_CAU / "a-contacte"
DIR_CAU_PRIMER = fonts.DIR_CAU / "a-contacte-primer"
DIR_CAU_GRUPS = fonts.DIR_CAU / "a-contacte-grups"
DIR_RESULTATS = t3.DIR_RESULTATS


def taula_primer(p: PartitBanc) -> pd.DataFrame:
    """Els senyals d'A control i els del contacte, en una fila per imatge."""
    return pd.concat([t3d.taula(p), contacte.calcula(p.tracking, p.trams)], axis=1)


def taula_segon(p: PartitBanc, primer: np.ndarray) -> pd.DataFrame:
    """Els del primer i els del context, fets amb les probabilitats `primer` del primer classificador."""
    return pd.concat([taula_primer(p), context.calcula(primer, p.trams)], axis=1)


@functools.cache
def mostres_primer(nom: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Les mostres del primer d'un partit, als sis escenaris d'entrenament, amb la tria de la T3f (un cop per
    procés)."""
    xs, ys = [], []
    for escenari in ENTRENAMENT:
        p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[escenari])
        x, y = t3f.mostres(p, taula_primer(p))
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
        desat = {f"e{i}": model.probabilitats(entrenat, taula_primer(degrada.aplica(fonts.partit(prova), e))
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
        desat = {clau_: model.probabilitats(entrenat, taula_primer(degrada.aplica(fonts.partit(nom),
                                                                                 t3.ESCENARIS[e]))
                                            ).astype(np.float32) for (nom, e), clau_ in claus.items()}
        desa(cami, **desat)
    return {qui: desat[nom] for qui, nom in claus.items()}


def mostres_segon(prova: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Les mostres del segon classificador per provar `prova`: els altres nou partits, als sis escenaris, amb les
    probabilitats del primer que no ha vist cap d'ells, i amb la tria de la T3f."""
    primers = {}
    for i in range(t3e.GRUPS):
        primers |= primer_del_grup((prova, i))
    xs, ys = [], []
    for (nom, e), primer in primers.items():
        p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[e])
        x, y = t3f.mostres(p, taula_segon(p, primer.astype(float)))
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def probabilitats(prova: str, entrena: bool = True) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Les d'A contacte al partit `prova`, a cada escenari de la T3, i el prior. Amb `entrena=False`, només les llegeix
    de la memòria cau, i si no hi són o són d'un altre codi, s'atura."""
    cami = DIR_CAU / f"{prova}.npz"
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les probabilitats d'{CONTACTE} de {prova}, o són d'un altre codi")
        x, y = mostres_segon(prova)
        entrenat = model.entrena(x, y)
        prior = model.prior(y)
        del x
        primers = primer_de_la_prova(prova)
        desat = {"prior": prior}
        for i, (nom_e, escenari) in enumerate(t3.ESCENARIS.items()):
            p = degrada.aplica(fonts.partit(prova), escenari)
            desat[f"e{i}"] = model.probabilitats(entrenat, taula_segon(p, primers[nom_e].astype(float))
                                                 ).astype(np.float32)
        desa(cami, **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(t3.ESCENARIS)}, desat["prior"]


def de_qui(metode: str):
    return {t3e.CONTEXT: t3e.probabilitats, t3f.POSSESSIO: t3f.probabilitats, CONTACTE: probabilitats}[metode]


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


def markdown(c: pd.DataFrame, c_possessio: pd.DataFrame, metodes: pd.DataFrame, triades: dict,
             passa: dict[str, bool], encerts: pd.DataFrame) -> str:
    ordre = list(CLASSIFICADORS)
    linies = ["# Banc obert · El darrer contacte, com a senyal (T3h)", "",
              "Generat amb `uv run python -I -m banc.model_a_contacte`. Dades obertes: 7 partits de DFL (IDSSE, CC",
              "BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3h», i la capçalera de `banc/model_a_contacte.py`.", "",
              f"**{t3e.CONTEXT}** és el model de la cadena (T3e); **{t3f.POSSESSIO}**, el mateix amb una altra tria",
              f"de les imatges que s'aprenen (T3f); i **{CONTACTE}**, {t3f.POSSESSIO} amb els senyals del darrer",
              "contacte al primer classificador. Tots tenen el decodificador triat amb els altres nou partits als",
              "escenaris ×¼.", "",
              "## L'spellF1 i el macroF1 de cada classificador (mitjana dels deu partits)", ""]
    for columna, nom in (("spell_f1", "spellF1"), ("macro_f1", "macroF1")):
        t = metodes.pivot_table(index="escenari", columns="metode", values=columna, sort=False)[ordre]
        linies += [f"**{nom}**", "", "| escenari | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 1) + "|"]
        linies += [f"| {e} | " + " | ".join(f"{v:.3f}" for v in f) + " |" for e, f in t.iterrows()]
        linies.append("")
    linies += [f"## {CONTACTE} contra {t3e.CONTEXT} (spellF1): el criteri", "",
               *t3b._taula(c, CONTACTE, t3e.CONTEXT), "", *t3b._criteris(passa, False),
               f"## {CONTACTE} contra {t3f.POSSESSIO} (spellF1), només per saber-ho", "",
               "Les mateixes mostres: la diferència és el que afegeixen els senyals del contacte.", "",
               f"| escenari | {t3f.POSSESSIO} | {CONTACTE} | diferència | interval del 95 % | {CONTACTE} guanya |",
               "|---|---|---|---|---|---|"]
    linies += [f"| {f.escenari} | {f.contra:.3f} | {f.nou:.3f} | {f.diferencia:+.3f} | {f.baix:+.3f} a {f.alt:+.3f} | "
               f"{f.guanya} de {f.partits} |" for f in c_possessio.itertuples()]
    linies += ["", "## Possessions predites per cada real (mitjana dels deu partits), només per saber-ho", "",
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
    """El que fa les probabilitats d'A contacte: la clau d'A per possessió (la tria, A context), els senyals del
    contacte i el context, i això."""
    h = hashlib.sha256((t3f.CLAU + repr((ENTRENAMENT, contacte.RADIS_M))).encode())
    for modul in (contacte, context):
        h.update(Path(modul.__file__).read_bytes())
    for funcio in (taula_primer, taula_segon, mostres_primer, entrena_primer, primer_de_la_prova, primer_del_grup,
                   mostres_segon, probabilitats):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + t3f.clau_dels_resultats()).encode())
    for modul in (t3f, t3e, t3d, t3b, t3, decodifica, avalua, degrada):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def main() -> None:
    from banc import model_a_contacte as aquest         # pel nom del mòdul, perquè els processos fills el trobin

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=2, help="models alhora (cadascun fa servir 8 fils)")
    args = ap.parse_args()
    for nom in fonts.NOMS:                              # les d'A context i d'A per possessió: abans cal fer-les
        t3e.probabilitats(nom, entrena=False)
        t3f.probabilitats(nom, entrena=False)
    with ProcessPoolExecutor(max_workers=args.processos_models) as feina:
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.primer_de_la_prova, fonts.NOMS)):
            print(f"· {nom}: el primer, fet", flush=True)
        tasques = list(itertools.product(fonts.NOMS, range(t3e.GRUPS)))
        for (nom, i), _ in zip(tasques, feina.map(aquest.primer_del_grup, tasques)):
            print(f"· {nom}: el primer, grup {i + 1} de {t3e.GRUPS}, fet", flush=True)
    with ProcessPoolExecutor(max_workers=args.processos_models) as feina:
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.probabilitats, fonts.NOMS)):
            print(f"· {nom}: {CONTACTE} fet", flush=True)
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        tasques = list(itertools.product(fonts.NOMS, t3.ESCENARIS))
        files = pd.DataFrame([f for tros in feina.map(aquest.graella, tasques) for f in tros])
        metodes, triades = tria_sense_mirar(files)
        tasques = [(nom, e, triades[nom]) for nom in fonts.NOMS for e in t3.QUARTS]
        encerts = t3f.encert_per_durada(pd.DataFrame([f for tros in feina.map(aquest.encert, tasques)
                                                      for f in tros]))
    c = t3b.comparacio(metodes, CONTACTE, t3e.CONTEXT)
    c_possessio = t3b.comparacio(metodes, CONTACTE, t3f.POSSESSIO)
    passa = t3b.compleix(c)
    desa_ = {"clau": clau_dels_resultats(), "passa": passa, "comparacio": t3.registres(c),
             "comparacio_possessio": t3.registres(c_possessio), "triades": triades,
             "encert": t3.registres(encerts.stack(level=0, future_stack=True).reset_index()),
             "files": t3.registres(files)}
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-a-contacte.json").write_text(json.dumps(desa_, indent=1, default=float, allow_nan=False))
    (DIR_RESULTATS / "model-a-contacte.md").write_text(markdown(c, c_possessio, metodes, triades, passa, encerts))
    print((DIR_RESULTATS / "model-a-contacte.md").read_text())


if __name__ == "__main__":
    main()
