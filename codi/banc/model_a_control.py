"""Els senyals del control al classificador d'A (T3d del pla per tocs, `docs/pla-tocs.md`, «T3d»).

    cd codi && uv run python -I -m banc.model_a_control [--processos 12]

1. **El classificador A control:** el d'A ×1+×¼ (T3c), entrenat igual deixant cada partit fora i amb els sis
   escenaris, però amb els senyals de `cadena/control.py` a més dels d'ara. Les probabilitats del partit que queda
   fora, als deu escenaris de la T3, a la memòria cau (`dades/banc/a-control/`).
2. **Totes les combinacions** del decodificador d'A (λ i la durada mínima) amb A ×1+×¼ i amb A control, a cada partit
   i escenari.
3. **Per a cada partit,** la combinació de cada classificador que va millor de mitjana als altres nou, als escenaris
   ×¼, com a la T3c.
4. **El criteri** del pla: A control contra A ×1+×¼, el classificador de la cadena d'ara.

Escriu `resultats/model-a-control.json` (la clau del codi i les files) i `resultats/model-a-control.md`. Tot són
dades obertes.
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

from banc import avalua, canvis, degrada, fonts
from banc import decodificador_tocs as t3
from banc import model_a_dos_errors as t3c
from banc import model_a_quart as t3b
from banc.partit import PartitBanc
from cadena import control, decodifica, model, senyals, tocs

ENTRENAMENT = t3c.ENTRENAMENT
CONTROL = "A control"
CLASSIFICADORS = (t3c.DOS, CONTROL)
DIR_CAU = fonts.DIR_CAU / "a-control"
DIR_RESULTATS = t3.DIR_RESULTATS


def taula(p: PartitBanc) -> pd.DataFrame:
    """Els senyals d'A i els del control, en una fila per imatge."""
    return pd.concat([senyals.calcula(p.tracking, p.trams), control.calcula(p.tracking, p.trams)], axis=1)


@functools.cache
def mostres_de(nom: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Les mostres d'entrenament d'un partit, dels sis escenaris de la T3c (un cop per procés)."""
    xs, ys = [], []
    for escenari in ENTRENAMENT:
        p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[escenari])
        x, y = model.mostres([taula(p)], [p.veritat], model.PAS)
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def probabilitats(prova: str, entrena: bool = True) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Les d'A control al partit `prova`, a cada escenari de la T3, amb el model entrenat amb els altres, i el prior.
    Amb `entrena=False`, només les llegeix de la memòria cau, i si no hi són o són d'un altre codi, s'atura."""
    cami = DIR_CAU / f"{prova}.npz"
    if cami.exists():
        with np.load(cami, allow_pickle=False) as desat:
            if str(desat["clau"]) == CLAU:
                return {e: desat[f"e{i}"] for i, e in enumerate(t3.ESCENARIS)}, desat["prior"]
    if not entrena:
        raise RuntimeError(f"Falten les probabilitats d'{CONTROL} de {prova}, o són d'un altre codi")
    mostres = [mostres_de(nom) for nom in fonts.NOMS if nom != prova]
    x, y = pd.concat([m[0] for m in mostres], ignore_index=True), np.concatenate([m[1] for m in mostres])
    entrenat = model.entrena(x, y)
    prior = model.prior(y)
    probes = {}
    for i, escenari in enumerate(t3.ESCENARIS.values()):
        p = degrada.aplica(fonts.partit(prova), escenari)
        probes[f"e{i}"] = model.probabilitats(entrenat, taula(p)).astype(np.float32)
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
    for metode, de in zip(CLASSIFICADORS, (t3c.probabilitats, probabilitats)):
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


def markdown(c: pd.DataFrame, metodes: pd.DataFrame, triades: dict, passa: dict[str, bool]) -> str:
    linies = ["# Banc obert · Els senyals del control al classificador d'A (T3d)", "",
              "Generat amb `uv run python -I -m banc.model_a_control`. Dades obertes: 7 partits de DFL (IDSSE, CC BY",
              "4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3d», i la capçalera de `banc/model_a_control.py`.", "",
              f"**{t3c.DOS}** és el classificador de la cadena d'ara (T3c), i **{CONTROL}**, el mateix amb els",
              "senyals del control (`cadena/control.py`). Tots dos tenen el decodificador triat amb els altres nou",
              "partits als escenaris ×¼.", "",
              "## L'spellF1 i el macroF1 de cada classificador (mitjana dels deu partits)", ""]
    for columna, nom in (("spell_f1", "spellF1"), ("macro_f1", "macroF1")):
        t = metodes.pivot_table(index="escenari", columns="metode", values=columna, sort=False)[list(CLASSIFICADORS)]
        linies += [f"**{nom}**", "", "| escenari | " + " | ".join(CLASSIFICADORS) + " |",
                   "|---" * (len(CLASSIFICADORS) + 1) + "|"]
        linies += [f"| {e} | " + " | ".join(f"{v:.3f}" for v in f) + " |" for e, f in t.iterrows()]
        linies.append("")
    linies += [f"## {CONTROL} contra {t3c.DOS} (spellF1): el criteri", "", *t3b._taula(c, CONTROL, t3c.DOS), "",
               *t3b._criteris(passa, False), "## Els decodificadors triats (cada partit, amb els altres nou)", ""]
    compta: dict[str, int] = {}
    for t in triades.values():
        clau_ = " · ".join(f"{m}: λ = {lam:g}, durada mínima {d}" for m, (lam, d) in t.items())
        compta[clau_] = compta.get(clau_, 0) + 1
    linies += [f"- {k} ({n} partits)" for k, n in compta.items()]
    return "\n".join(linies + [""])


def clau() -> str:
    """El que fa les probabilitats d'A control: la clau d'A ×1+×¼, els senyals del control i els tocs, i això."""
    h = hashlib.sha256((t3c.CLAU + repr(ENTRENAMENT)).encode())
    for modul in (control, tocs):
        h.update(Path(modul.__file__).read_bytes())
    for funcio in (taula, mostres_de, probabilitats):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + t3c.clau_dels_resultats()).encode())
    for modul in (t3c, t3b, t3, decodifica, canvis, avalua, degrada):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def main() -> None:
    from banc import model_a_control as aquest          # pel nom del mòdul, perquè els processos fills el trobin

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=2, help="models alhora (cadascun fa servir 8 fils)")
    args = ap.parse_args()
    for nom in fonts.NOMS:                              # les d'A ×1+×¼ (T3c): si falten, abans cal fer-les
        t3c.probabilitats(nom, entrena=False)
    with ProcessPoolExecutor(max_workers=args.processos_models) as feina:
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.probabilitats, fonts.NOMS)):
            print(f"· {nom}: {CONTROL} fet", flush=True)
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        tasques = list(itertools.product(fonts.NOMS, t3.ESCENARIS))
        files = pd.DataFrame([f for tros in feina.map(aquest.graella, tasques) for f in tros])
    metodes, triades = tria_sense_mirar(files)
    c = t3b.comparacio(metodes, CONTROL, t3c.DOS)
    passa = t3b.compleix(c)
    desa = {"clau": clau_dels_resultats(), "passa": passa, "comparacio": t3.registres(c), "triades": triades,
            "files": t3.registres(files)}
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-a-control.json").write_text(json.dumps(desa, indent=1, default=float, allow_nan=False))
    (DIR_RESULTATS / "model-a-control.md").write_text(markdown(c, metodes, triades, passa))
    print((DIR_RESULTATS / "model-a-control.md").read_text())


if __name__ == "__main__":
    main()
