"""A entrenat amb els dos errors de posició (T3c del pla per tocs, `docs/pla-tocs.md`, «T3c»).

    cd codi && uv run python -I -m banc.model_a_dos_errors [--processos 12]

1. **El classificador A ×1+×¼:** el d'A, entrenat deixant cada partit fora, amb les mostres d'A (curts, llargs i
   barreja amb l'error ×1, `model_a.mostres_de`) i les d'A ×¼ (els mateixos amb l'error ×¼,
   `model_a_quart.mostres_de`) juntes. Les probabilitats del partit que queda fora, als deu escenaris de la T3, a la
   memòria cau (`dades/banc/a-entrenat-dos-errors/`).
2. **Totes les combinacions** del decodificador d'A (λ i la durada mínima) amb els tres classificadors, a cada partit
   i escenari: A, A ×¼ (T3b) i A ×1+×¼.
3. **Per a cada partit,** la combinació de cada classificador que va millor de mitjana als altres nou, als escenaris
   ×¼, com a la T3 i a la T3b. A més, A amb el decodificador de la cadena d'ara.
4. **El criteri** del pla: A ×1+×¼ contra A. Contra A ×¼, només per saber quant del guany de la T3b es queda.

Escriu `resultats/model-a-dos-errors.json` (la clau del codi i les files) i `resultats/model-a-dos-errors.md`. Tot
són dades obertes.
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

from banc import avalua, canvis, degrada, fonts, model_a
from banc import decodificador_tocs as t3
from banc import model_a_quart as t3b
from cadena import decodifica, model, senyals

ENTRENAMENT = (*model_a.ESCENARIS_ENTRENAMENT, *t3b.ENTRENAMENT)
DOS = "A ×1+×¼"
CLASSIFICADORS = ("A", t3b.A_QUART, DOS)
DIR_CAU = fonts.DIR_CAU / "a-entrenat-dos-errors"
DIR_RESULTATS = t3.DIR_RESULTATS


def mostres_de(nom: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Les mostres d'entrenament d'un partit: les d'A i les d'A ×¼, juntes (cadascuna es fa un cop per procés)."""
    (x1, y1), (xq, yq) = model_a.mostres_de(nom), t3b.mostres_de(nom)
    return pd.concat([x1, xq], ignore_index=True), np.concatenate([y1, yq])


def probabilitats(prova: str, entrena: bool = True) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Les d'A ×1+×¼ al partit `prova`, a cada escenari de la T3, amb el model entrenat amb els altres, i el prior.
    Amb `entrena=False`, només les llegeix de la memòria cau, i si no hi són o són d'un altre codi, s'atura."""
    cami = DIR_CAU / f"{prova}.npz"
    if cami.exists():
        with np.load(cami, allow_pickle=False) as desat:
            if str(desat["clau"]) == CLAU:
                return {e: desat[f"e{i}"] for i, e in enumerate(t3.ESCENARIS)}, desat["prior"]
    if not entrena:
        raise RuntimeError(f"Falten les probabilitats d'A ×1+×¼ de {prova}, o són d'un altre codi")
    mostres = [mostres_de(nom) for nom in fonts.NOMS if nom != prova]
    x, y = pd.concat([m[0] for m in mostres], ignore_index=True), np.concatenate([m[1] for m in mostres])
    entrenat = model.entrena(x, y)
    prior = model.prior(y)
    probes = {}
    for i, escenari in enumerate(t3.ESCENARIS.values()):
        p = degrada.aplica(fonts.partit(prova), escenari)
        probes[f"e{i}"] = model.probabilitats(entrenat, senyals.calcula(p.tracking, p.trams)).astype(np.float32)
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
    for metode, de in zip(CLASSIFICADORS, (t3.probabilitats, t3b.probabilitats, probabilitats)):
        probes, prior = de(nom, entrena=False)
        proba = probes[escenari].astype(float)
        for lam, d_min in itertools.product(decodifica.GRAELLA_LAMBDA, decodifica.GRAELLA_DMIN):
            pred = decodifica.per_trams(proba, prior, p.trams, lam, d_min)
            files.append({**comu, "metode": metode, "lam": lam, "d_min": d_min, **avalua.puntua(p, pred)})
    return files


def tria_sense_mirar(files: pd.DataFrame, cadena: dict[str, tuple[float, int]]) -> tuple[pd.DataFrame, dict]:
    """Les files de cada classificador a cada partit, amb el decodificador triat amb els altres nou als escenaris ×¼
    (`model_a_quart`), i A cadena, amb el de la cadena. També les triades."""
    triats, triades = [], {}
    for prova in fonts.NOMS:
        triades[prova] = {}
        for metode in CLASSIFICADORS:
            seu = files[files["metode"] == metode]
            lam, d_min = t3.millor(seu[seu["partit"] != prova], ["lam", "d_min"])
            del_partit = seu[seu["partit"] == prova]
            triats.append(del_partit[(del_partit["lam"] == lam) & (del_partit["d_min"] == d_min)])
            triades[prova][metode] = (float(lam), int(d_min))
        lam_c, d_c = cadena[prova]
        a = files[(files["metode"] == "A") & (files["partit"] == prova)]
        triats.append(a[(a["lam"] == lam_c) & (a["d_min"] == d_c)].assign(metode="A cadena"))
    return pd.concat(triats, ignore_index=True), triades


def markdown(c: pd.DataFrame, c_quart: pd.DataFrame, metodes: pd.DataFrame, triades: dict,
             passa: dict[str, bool]) -> str:
    ordre = ["A cadena", *CLASSIFICADORS]
    linies = ["# Banc obert · A entrenat amb els dos errors (T3c)", "",
              "Generat amb `uv run python -I -m banc.model_a_dos_errors`. Dades obertes: 7 partits de DFL (IDSSE, CC",
              "BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3c», i la capçalera de `banc/model_a_dos_errors.py`.", "",
              "**A** és el classificador d'ara, entrenat amb l'error de posició ×1; **A ×¼**, el de la T3b, entrenat",
              f"amb l'error ×¼; i **{DOS}**, entrenat amb tots dos. Els tres tenen el decodificador triat amb els",
              "altres nou partits als escenaris ×¼. **A cadena** és A amb el decodificador de la cadena d'ara.", "",
              "## L'spellF1 i el macroF1 de cada classificador (mitjana dels deu partits)", ""]
    for columna, nom in (("spell_f1", "spellF1"), ("macro_f1", "macroF1")):
        t = metodes.pivot_table(index="escenari", columns="metode", values=columna, sort=False)[ordre]
        linies += [f"**{nom}**", "", "| escenari | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 1) + "|"]
        linies += [f"| {e} | " + " | ".join(f"{v:.3f}" for v in f) + " |" for e, f in t.iterrows()]
        linies.append("")
    linies += [f"## {DOS} contra A (spellF1): el criteri", "", *t3b._taula(c, DOS, "A"), "",
               *t3b._criteris(passa, False),
               f"## {DOS} contra A ×¼ (spellF1), només per saber-ho", "",
               f"| escenari | A ×¼ | {DOS} | diferència | interval del 95 % | {DOS} guanya |", "|---|---|---|---|---|---|"]
    linies += [f"| {f.escenari} | {f.contra:.3f} | {f.nou:.3f} | {f.diferencia:+.3f} | {f.baix:+.3f} a {f.alt:+.3f} | "
               f"{f.guanya} de {f.partits} |" for f in c_quart.itertuples()]
    linies += ["", "## Els decodificadors triats (cada partit, amb els altres nou)", ""]
    compta: dict[str, int] = {}
    for t in triades.values():
        clau_ = " · ".join(f"{m}: λ = {lam:g}, durada mínima {d}" for m, (lam, d) in t.items())
        compta[clau_] = compta.get(clau_, 0) + 1
    linies += [f"- {k} ({n} partits)" for k, n in compta.items()]
    return "\n".join(linies + [""])


def clau() -> str:
    """El que fa les probabilitats d'A ×1+×¼: les mostres d'A i d'A ×¼ (les seves claus), els escenaris i això."""
    h = hashlib.sha256((model_a.CLAU + t3b.CLAU + repr(list(t3.ESCENARIS.values())) + repr(ENTRENAMENT)).encode())
    for funcio in (mostres_de, probabilitats):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + t3.CLAU_CAU + model_a.CLAU_RESULTATS).encode())
    for modul in (t3b, t3, decodifica, canvis, avalua, degrada):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def main() -> None:
    from banc import model_a_dos_errors as aquest      # pel nom del mòdul, perquè els processos fills el trobin

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=2, help="models alhora (cadascun fa servir 8 fils)")
    args = ap.parse_args()
    for nom in fonts.NOMS:                              # les d'A (T3) i les d'A ×¼ (T3b): si falten, abans cal fer-les
        t3.probabilitats(nom, entrena=False)
        t3b.probabilitats(nom, entrena=False)
    with ProcessPoolExecutor(max_workers=args.processos_models) as feina:
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.probabilitats, fonts.NOMS)):
            print(f"· {nom}: {DOS} fet", flush=True)
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        tasques = list(itertools.product(fonts.NOMS, t3.ESCENARIS))
        files = pd.DataFrame([f for tros in feina.map(aquest.graella, tasques) for f in tros])
    metodes, triades = tria_sense_mirar(files, canvis.decodificadors(model_a.resultats()))
    c, c_quart = t3b.comparacio(metodes, DOS, "A"), t3b.comparacio(metodes, DOS, t3b.A_QUART)
    passa = t3b.compleix(c)
    desa = {"clau": clau_dels_resultats(), "passa": passa, "comparacio": t3.registres(c),
            "contra_a_quart": t3.registres(c_quart), "triades": triades, "files": t3.registres(files)}
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-a-dos-errors.json").write_text(json.dumps(desa, indent=1, default=float,
                                                                      allow_nan=False))
    (DIR_RESULTATS / "model-a-dos-errors.md").write_text(markdown(c, c_quart, metodes, triades, passa))
    print((DIR_RESULTATS / "model-a-dos-errors.md").read_text())


if __name__ == "__main__":
    main()
