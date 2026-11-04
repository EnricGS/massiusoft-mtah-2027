"""Un segon classificador d'A, que mira el primer al voltant (T3e del pla per tocs, `docs/pla-tocs.md`, «T3e»).

    cd codi && uv run python -I -m banc.model_a_context [--processos 12]

1. **El primer classificador** és A control (T3d). Per entrenar el segon calen les seves probabilitats a partits que
   no hagi vist: per a cada partit que es prova, els altres nou es parteixen en tres grups (`grups`), i cada grup
   rep les d'un A control entrenat amb els altres sis, als sis escenaris d'entrenament (`dades/banc/a-context-primer/`).
2. **El segon, A context,** és el mateix model, entrenat amb els nou partits i els sis escenaris, amb els senyals
   d'A control i els del context (`cadena/context.py`), fets amb aquelles probabilitats. Al partit que es prova, el
   primer és l'A control de la T3d (entrenat amb els nou). Les probabilitats d'A context, als deu escenaris de la
   T3, a la memòria cau (`dades/banc/a-context/`).
3. **Totes les combinacions** del decodificador d'A amb A ×1+×¼, A control i A context, a cada partit i escenari, i
   la que va millor de mitjana als altres nou, als escenaris ×¼, com a la T3c i la T3d.
4. **El criteri** del pla: A context contra A ×1+×¼, el classificador de la cadena d'ara. Contra A control, només per
   saber quant hi afegeix el segon classificador.

Escriu `resultats/model-a-context.json` (la clau del codi i les files) i `resultats/model-a-context.md`. Tot són
dades obertes.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import itertools
import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from banc import avalua, canvis, degrada, fonts
from banc import decodificador_tocs as t3
from banc import model_a_control as t3d
from banc import model_a_dos_errors as t3c
from banc import model_a_quart as t3b
from banc.partit import PartitBanc
from cadena import context, decodifica, model

ENTRENAMENT = t3d.ENTRENAMENT
CONTEXT = "A context"
CLASSIFICADORS = (t3c.DOS, t3d.CONTROL, CONTEXT)
GRUPS = 3
DIR_CAU = fonts.DIR_CAU / "a-context"
DIR_CAU_PRIMER = fonts.DIR_CAU / "a-context-primer"
DIR_RESULTATS = t3.DIR_RESULTATS


def grups(prova: str) -> tuple[tuple[str, ...], ...]:
    """Els altres nou partits, en tres grups de tres, sempre els mateixos (per l'ordre dels noms)."""
    altres = [nom for nom in fonts.NOMS if nom != prova]
    return tuple(tuple(altres[i::GRUPS]) for i in range(GRUPS))


def taula(p: PartitBanc, primer: np.ndarray) -> pd.DataFrame:
    """Els senyals d'A control i els del context, fets amb les probabilitats `primer` del primer classificador."""
    return pd.concat([t3d.taula(p), context.calcula(primer, p.trams)], axis=1)


def primer_del_grup(tasca: tuple[str, int]) -> dict[tuple[str, str], np.ndarray]:
    """Les probabilitats d'A control als partits del grup `i` de `prova`, als sis escenaris d'entrenament, amb un A
    control entrenat amb els altres sis partits. A la memòria cau."""
    prova, i = tasca
    grup = grups(prova)[i]
    cami = DIR_CAU_PRIMER / f"{prova}-{i}.npz"
    claus = {(nom, e): f"p{j}_{k}" for j, nom in enumerate(grup) for k, e in enumerate(ENTRENAMENT)}
    if cami.exists():
        with np.load(cami, allow_pickle=False) as desat:
            if str(desat["clau"]) == CLAU:
                return {qui: desat[nom] for qui, nom in claus.items()}
    mostres = [t3d.mostres_de(nom) for nom in fonts.NOMS if nom != prova and nom not in grup]
    x, y = pd.concat([m[0] for m in mostres], ignore_index=True), np.concatenate([m[1] for m in mostres])
    entrenat = model.entrena(x, y)
    probes = {}
    for (nom, e), clau_ in claus.items():
        p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[e])
        probes[clau_] = model.probabilitats(entrenat, t3d.taula(p)).astype(np.float32)
    DIR_CAU_PRIMER.mkdir(parents=True, exist_ok=True)
    temporal = cami.with_name(f"{cami.name}.{os.getpid()}.part.npz")
    np.savez(temporal, clau=CLAU, **probes)
    temporal.replace(cami)
    return {qui: probes[nom] for qui, nom in claus.items()}


def mostres_de(prova: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Les mostres del segon classificador per provar `prova`: els altres nou partits, als sis escenaris, amb les
    probabilitats del primer que no ha vist cap d'ells."""
    primers = {}
    for i in range(GRUPS):
        primers |= primer_del_grup((prova, i))
    xs, ys = [], []
    for (nom, e), primer in primers.items():
        p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[e])
        x, y = model.mostres([taula(p, primer.astype(float))], [p.veritat], model.PAS)
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def probabilitats(prova: str, entrena: bool = True) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Les d'A context al partit `prova`, a cada escenari de la T3, i el prior. Amb `entrena=False`, només les
    llegeix de la memòria cau, i si no hi són o són d'un altre codi, s'atura."""
    cami = DIR_CAU / f"{prova}.npz"
    if cami.exists():
        with np.load(cami, allow_pickle=False) as desat:
            if str(desat["clau"]) == CLAU:
                return {e: desat[f"e{i}"] for i, e in enumerate(t3.ESCENARIS)}, desat["prior"]
    if not entrena:
        raise RuntimeError(f"Falten les probabilitats d'{CONTEXT} de {prova}, o són d'un altre codi")
    x, y = mostres_de(prova)
    entrenat = model.entrena(x, y)
    prior = model.prior(y)
    del x
    primers, _ = t3d.probabilitats(prova, entrena=False)
    probes = {}
    for i, (nom_e, escenari) in enumerate(t3.ESCENARIS.items()):
        p = degrada.aplica(fonts.partit(prova), escenari)
        probes[f"e{i}"] = model.probabilitats(entrenat, taula(p, primers[nom_e].astype(float))).astype(np.float32)
    DIR_CAU.mkdir(parents=True, exist_ok=True)
    temporal = cami.with_name(f"{cami.name}.{os.getpid()}.part.npz")
    np.savez(temporal, clau=CLAU, prior=prior, **probes)
    temporal.replace(cami)
    return {e: probes[f"e{i}"] for i, e in enumerate(t3.ESCENARIS)}, prior


def graella(tasca: tuple[str, str]) -> list[dict]:
    """Un partit i un escenari: totes les combinacions del decodificador d'A, amb cada classificador."""
    nom, escenari = tasca
    p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[escenari])
    comu = {"partit": nom, "font": p.font, "escenari": escenari}
    files = []
    for metode, de in zip(CLASSIFICADORS, (t3c.probabilitats, t3d.probabilitats, probabilitats)):
        probes, prior = de(nom, entrena=False)
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


def markdown(c: pd.DataFrame, c_control: pd.DataFrame, metodes: pd.DataFrame, triades: dict,
             passa: dict[str, bool]) -> str:
    ordre = list(CLASSIFICADORS)
    linies = ["# Banc obert · Un segon classificador d'A, que mira el primer al voltant (T3e)", "",
              "Generat amb `uv run python -I -m banc.model_a_context`. Dades obertes: 7 partits de DFL (IDSSE, CC BY",
              "4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3e», i la capçalera de `banc/model_a_context.py`.", "",
              f"**{t3c.DOS}** és el classificador de la cadena d'ara (T3c); **{t3d.CONTROL}**, el mateix amb els",
              f"senyals del control (T3d); i **{CONTEXT}**, un segon classificador que mira les probabilitats",
              f"d'{t3d.CONTROL} al voltant de cada imatge. Tots tenen el decodificador triat amb els altres nou",
              "partits als escenaris ×¼.", "",
              "## L'spellF1 i el macroF1 de cada classificador (mitjana dels deu partits)", ""]
    for columna, nom in (("spell_f1", "spellF1"), ("macro_f1", "macroF1")):
        t = metodes.pivot_table(index="escenari", columns="metode", values=columna, sort=False)[ordre]
        linies += [f"**{nom}**", "", "| escenari | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 1) + "|"]
        linies += [f"| {e} | " + " | ".join(f"{v:.3f}" for v in f) + " |" for e, f in t.iterrows()]
        linies.append("")
    linies += [f"## {CONTEXT} contra {t3c.DOS} (spellF1): el criteri", "", *t3b._taula(c, CONTEXT, t3c.DOS), "",
               *t3b._criteris(passa, False),
               f"## {CONTEXT} contra {t3d.CONTROL} (spellF1), només per saber-ho", "",
               f"| escenari | {t3d.CONTROL} | {CONTEXT} | diferència | interval del 95 % | {CONTEXT} guanya |",
               "|---|---|---|---|---|---|"]
    linies += [f"| {f.escenari} | {f.contra:.3f} | {f.nou:.3f} | {f.diferencia:+.3f} | {f.baix:+.3f} a {f.alt:+.3f} | "
               f"{f.guanya} de {f.partits} |" for f in c_control.itertuples()]
    linies += ["", "## Els decodificadors triats (cada partit, amb els altres nou)", ""]
    compta: dict[str, int] = {}
    for t in triades.values():
        clau_ = " · ".join(f"{m}: λ = {lam:g}, durada mínima {d}" for m, (lam, d) in t.items())
        compta[clau_] = compta.get(clau_, 0) + 1
    linies += [f"- {k} ({n} partits)" for k, n in compta.items()]
    return "\n".join(linies + [""])


def clau() -> str:
    """El que fa les probabilitats d'A context: la clau d'A control, els senyals del context, els grups i això."""
    h = hashlib.sha256((t3d.CLAU + repr((ENTRENAMENT, GRUPS, fonts.NOMS))).encode())
    h.update(Path(context.__file__).read_bytes())
    for funcio in (grups, taula, primer_del_grup, mostres_de, probabilitats):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + t3d.clau_dels_resultats()).encode())
    for modul in (t3d, t3c, t3b, t3, decodifica, canvis, avalua, degrada):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def main() -> None:
    from banc import model_a_context as aquest          # pel nom del mòdul, perquè els processos fills el trobin

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=2, help="models alhora (cadascun fa servir 8 fils)")
    args = ap.parse_args()
    for nom in fonts.NOMS:                              # les d'A ×1+×¼ (T3c) i d'A control (T3d): abans cal fer-les
        t3c.probabilitats(nom, entrena=False)
        t3d.probabilitats(nom, entrena=False)
    with ProcessPoolExecutor(max_workers=args.processos_models) as feina:
        tasques = list(itertools.product(fonts.NOMS, range(GRUPS)))
        for (nom, i), _ in zip(tasques, feina.map(aquest.primer_del_grup, tasques)):
            print(f"· {nom}: el primer, grup {i + 1} de {GRUPS}, fet", flush=True)
    with ProcessPoolExecutor(max_workers=args.processos_models) as feina:
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.probabilitats, fonts.NOMS)):
            print(f"· {nom}: {CONTEXT} fet", flush=True)
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        tasques = list(itertools.product(fonts.NOMS, t3.ESCENARIS))
        files = pd.DataFrame([f for tros in feina.map(aquest.graella, tasques) for f in tros])
    metodes, triades = tria_sense_mirar(files)
    c, c_control = t3b.comparacio(metodes, CONTEXT, t3c.DOS), t3b.comparacio(metodes, CONTEXT, t3d.CONTROL)
    passa = t3b.compleix(c)
    desa = {"clau": clau_dels_resultats(), "passa": passa, "comparacio": t3.registres(c),
            "contra_control": t3.registres(c_control), "triades": triades, "files": t3.registres(files)}
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-a-context.json").write_text(json.dumps(desa, indent=1, default=float, allow_nan=False))
    (DIR_RESULTATS / "model-a-context.md").write_text(markdown(c, c_control, metodes, triades, passa))
    print((DIR_RESULTATS / "model-a-context.md").read_text())


if __name__ == "__main__":
    main()
