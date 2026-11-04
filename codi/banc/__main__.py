"""El banc obert: les línies base a cada partit i a cada escenari, amb la mètrica oficial.

    cd codi && uv run python -I -m banc [--processos 4]

Tot són dades obertes (DFL i Metrica): les xifres poden sortir a la consola. Escriu a `banc/resultats/`
`linies-base.json` (una fila per partit, escenari i mètode) i `linies-base.md` (el resum).
"""

from __future__ import annotations

import argparse
import itertools
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

from banc import degrada, fonts, linies_base
from banc.linies_base import FINESTRES, ORDRE_PUBLICAT, SENSE_PILOTA

DIR_RESULTATS = Path(__file__).resolve().parent / "resultats"
ORDRE_PUBLICAT_MACRO = ("smooth25", "smooth50", "raw", "smooth125")   # per macroF1 (EVALUATION.md)


def acords(ordre: tuple[str, ...], publicat: tuple[str, ...]) -> int:
    """Quantes de les sis parelles queden en el mateix ordre que el publicat."""
    lloc = {b: i for i, b in enumerate(ordre)}
    return sum(lloc[a] < lloc[b] for a, b in itertools.combinations(publicat, 2))


def taula(files: pd.DataFrame, columna: str, sense: str) -> pd.DataFrame:
    tria = files[files["sense"] == sense]
    per_font = tria.pivot_table(index="base", columns=["escenari", "font"], values=columna, aggfunc="mean")
    tots = tria.pivot_table(index="base", columns="escenari", values=columna, aggfunc="mean")
    tots.columns = pd.MultiIndex.from_tuples([(e, "tots") for e in tots.columns])
    out = pd.concat([per_font, tots], axis=1)
    columnes = [(e, f) for e in degrada.NOMS for f in ("dfl", "metrica", "tots") if (e, f) in out.columns]
    return out.loc[list(FINESTRES), columnes]


def markdown(files: pd.DataFrame) -> str:
    linies = ["# Banc obert · les línies base", "",
              "Generat amb `uv run python -I -m banc`. Dades obertes: 7 partits de DFL (IDSSE, CC BY 4.0) i els 3 de",
              "mostra de Metrica. Mitjana dels partits de cada font. Cap dada del concurs.", ""]
    for sense in SENSE_PILOTA:
        linies += [f"## Sense pilota, {sense}", ""]
        for columna, nom in (("spell_f1", "spellF1"), ("macro_f1", "macroF1")):
            t = taula(files, columna, sense)
            capcalera = ["línia base"] + [f"{e} {f}" for e, f in t.columns]
            linies += [f"**{nom}**", "", "| " + " | ".join(capcalera) + " |", "|" + "---|" * len(capcalera)]
            linies += ["| " + " | ".join([base] + [f"{v:.3f}" for v in fila]) + " |" for base, fila in t.iterrows()]
            linies.append("")
        linies += ["**L'ordre per spellF1** (publicat: " + " > ".join(ORDRE_PUBLICAT) + ")", "",
                   "| escenari | font | ordre | parelles com al publicat | smooth50 > raw (partits) |",
                   "|---|---|---|---|---|"]
        t = taula(files, "spell_f1", sense)
        for escenari, font in t.columns:
            ordre = tuple(t[(escenari, font)].sort_values(ascending=False).index)
            tria = files[(files["sense"] == sense) & (files["escenari"] == escenari)
                         & ((files["font"] == font) | (font == "tots"))]
            per_partit = tria.pivot_table(index="partit", columns="base", values="spell_f1")
            guanya = int((per_partit["smooth50"] > per_partit["raw"]).sum())
            linies.append(f"| {escenari} | {font} | {' > '.join(ordre)} | {acords(ordre, ORDRE_PUBLICAT)} de 6 "
                          f"| {guanya} de {len(per_partit)} |")
        linies.append("")
    resum = files.drop_duplicates(["partit", "escenari"]).groupby(["escenari", "font"])[
        ["pilota_absent", "pilota_absent_viva", "pilota_absent_morta", "objectes", "slots"]].mean()
    linies += ["## Com queden els partits a cada escenari", "",
               "Mitjana dels partits de cada font. La pilota absent és dels fotogrames puntuats.", "",
               "| escenari | font | pilota absent | amb la pilota viva | amb la pilota morta | objectes vistos | slots |",
               "|---|---|---|---|---|---|---|"]
    linies += [f"| {e} | {f} | {r.pilota_absent:.1%} | {r.pilota_absent_viva:.1%} | {r.pilota_absent_morta:.1%} "
               f"| {r.objectes:.1f} | {r.slots:.0f} |" for e in degrada.NOMS for f in ("dfl", "metrica")
               for r in [resum.loc[(e, f)]]]
    return "\n".join(linies) + "\n"


def main() -> None:
    p = argparse.ArgumentParser(prog="python -I -m banc", description=__doc__.splitlines()[0])
    p.add_argument("--processos", type=int, default=4)
    args = p.parse_args()
    fonts.prepara(processos=args.processos)
    tasques = list(itertools.product(degrada.NOMS, fonts.NOMS))
    with ProcessPoolExecutor(max_workers=args.processos) as feines:
        files = [f for tros in feines.map(linies_base.feina, tasques) for f in tros]
    df = pd.DataFrame(files)
    df[["base", "sense"]] = df["metode"].str.split("·", expand=True)
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "linies-base.json").write_text(json.dumps(files, indent=1, ensure_ascii=False) + "\n")
    text = markdown(df)
    (DIR_RESULTATS / "linies-base.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
