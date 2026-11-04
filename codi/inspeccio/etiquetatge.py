"""El Smart Tagging (SportsCode XML): si és el que diu DATA.md, i què cobreix.

Es llegeix amb l'ElementTree de la biblioteca estàndard, que no resol entitats externes.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

from inspeccio import grafic
from inspeccio.esperat import Esperat
from inspeccio.seccio import Comprovacio, Seccio, comprova_igual, pct, xifra
from inspeccio.temps import puntuats

BASE = ("id", "inici_s", "fi_s", "codi")
COLORS_EQUIP = {"barcelona": grafic.LOCAL, "atletic club": grafic.VISITANT, "athletic club": grafic.VISITANT}


def instancies(cami: Path) -> pd.DataFrame:
    """Una fila per instància: inici i fi en segons, codi i una columna per grup d'etiquetes."""
    files = []
    for inst in ET.parse(cami).getroot().iter("instance"):
        fila = {"id": (inst.findtext("ID") or "").strip(),
                "inici_s": (inst.findtext("start") or "").strip(),
                "fi_s": (inst.findtext("end") or "").strip(),
                "codi": (inst.findtext("code") or "").strip()}
        for etiqueta in inst.iter("label"):
            grup = (etiqueta.findtext("group") or "(sense grup)").strip()
            text = (etiqueta.findtext("text") or "").strip()
            fila[grup] = f"{fila[grup]}; {text}" if grup in fila else text
        files.append(fila)
    df = pd.DataFrame(files)
    df = df.reindex(columns=[*BASE, *(c for c in df.columns if c not in BASE)])
    for temps in ("inici_s", "fi_s"):
        df[temps] = pd.to_numeric(df[temps].astype("string").str.replace(",", "."), errors="coerce")
    return df


def amb_temps(df: pd.DataFrame) -> pd.DataFrame:
    """Les instàncies que tenen inici i fi (les altres no es poden posar a la línia de temps)."""
    return df[np.isfinite(df["inici_s"].to_numpy(float)) & np.isfinite(df["fi_s"].to_numpy(float))]


def columna(df: pd.DataFrame, nom: str) -> pd.Series:
    """La columna d'un grup sense mirar majúscules (DATA.md: `Team`, no `team`)."""
    for c in df.columns:
        if c.lower() == nom.lower():
            return df[c].fillna("(buit)")
    return pd.Series(["(no hi és)"] * len(df), index=df.index)


def compta(serie: pd.Series, esperat: dict[str, int]) -> list[Comprovacio]:
    trobat = serie.value_counts().to_dict()
    claus = list(esperat) + sorted(set(trobat) - set(esperat))
    return [comprova_igual(f"`{k}`", esperat.get(k, 0), int(trobat.get(k, 0))) for k in claus]


def frame(segons: float, esperat: Esperat) -> int:
    return int(round(segons * esperat.fps))


def coberta(df: pd.DataFrame, frames: np.ndarray, esperat: Esperat) -> np.ndarray:
    """Quins dels `frames` cauen dins d'alguna instància de `df`."""
    dins = np.zeros(len(frames), bool)
    df = amb_temps(df)
    for inici, fi in zip(df["inici_s"], df["fi_s"]):
        dins |= (frames >= frame(inici, esperat)) & (frames <= frame(fi, esperat))
    return dins


def taula_codis(df: pd.DataFrame, esperat: Esperat) -> list[tuple]:
    frames = np.arange(esperat.fotogrames["tactical"])
    tots = puntuats(frames, esperat.rangs_puntuats)
    files = []
    for codi, g in df.groupby("codi"):
        durada = g["fi_s"] - g["inici_s"]
        cob = coberta(g, frames[tots], esperat)
        files.append((f"`{codi}`", xifra(len(g)), xifra(float(durada.median())),
                      xifra(float(durada.quantile(0.9))), f"{xifra(pct(cob.sum(), tots.sum()))} %"))
    cob = coberta(df, frames[tots], esperat)
    files.append(("**qualsevol**", xifra(len(df)), "", "", f"{xifra(pct(cob.sum(), tots.sum()))} %"))
    return files


def taula_sortides(df: pd.DataFrame, esperat: Esperat) -> list[tuple]:
    tipus = columna(df, "Type")
    sortides = amb_temps(df[tipus.str.lower().str.startswith("kick off (start)")])
    files = []
    for (_, inici, _), (_, fila) in zip(esperat.rangs_puntuats, sortides.sort_values("inici_s").iterrows()):
        f = frame(fila["inici_s"], esperat)
        files.append((xifra(inici), xifra(f), xifra(f - inici)))
    return files


def figura_cronologia(df: pd.DataFrame, esperat: Esperat):
    df = amb_temps(df)
    codis = sorted(df["codi"].unique())
    fig, ax = grafic.figura(0.9 + 0.22 * len(codis))
    grafic.ombreja_rangs(ax, esperat.rangs_puntuats, esperat.fps)
    equip = columna(df, "Team").str.lower()
    for fila, codi in enumerate(codis):
        tria = df["codi"] == codi
        trams = [(i / 60, (f - i) / 60) for i, f in zip(df.loc[tria, "inici_s"], df.loc[tria, "fi_s"])]
        colors = [COLORS_EQUIP.get(e, grafic.NEUTRE) for e in equip[tria]]
        ax.broken_barh(trams, (fila - 0.38, 0.76), facecolors=colors, lw=0)
    ax.set_yticks(range(len(codis)), codis, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("minut del vídeo")
    ax.grid(axis="y", visible=False)
    return fig


def omple(seccio: Seccio, cami: Path, esperat: Esperat) -> pd.DataFrame:
    df = instancies(cami)
    seccio.comprovacions([comprova_igual("instàncies", esperat.etiquetatge_instancies, len(df)),
                          comprova_igual("totes amb inici i fi", True, len(amb_temps(df)) == len(df)),
                          comprova_igual("totes amb inici < fi", True, bool((df["inici_s"] < df["fi_s"]).all()))])
    seccio.text("**Codis.**")
    seccio.comprovacions(compta(df["codi"], esperat.etiquetatge_codis))
    seccio.text("**Equip (`Team`) i tipus de jugada a pilota aturada (`Type`).**")
    tipus = columna(df, "Type")
    seccio.comprovacions(compta(columna(df, "Team"), esperat.etiquetatge_equip)
                         + compta(tipus[~tipus.isin(["(buit)", "(no hi és)"])], esperat.etiquetatge_tipus))
    seccio.taula("Les dues sortides de mig camp contra l'inici de cada part", (
        "Inici de la part (DATA.md)", "`Kick Off (Start)` × 25", "Diferència (fotogrames)"),
        taula_sortides(df, esperat), "DATA.md diu que la base de temps està comprovada amb les dues sortides.")
    seccio.taula("Durada i cobertura de cada codi", ("Codi", "Instàncies", "Durada mediana (s)",
                                                     "p90 (s)", "Fotogrames puntuats coberts"),
                 taula_codis(df, esperat))
    seccio.figura("Les instàncies al llarg del vídeo (blau, Barcelona; taronja, Athletic; gris, N/A)",
                  figura_cronologia(df, esperat))
    grups = [c for c in df.columns if c not in BASE]
    seccio.taula("Grups d'etiquetes", ("Grup", "Instàncies que el porten", "Valors"),
                 [(f"`{g}`", xifra(int(df[g].notna().sum())), ", ".join(sorted(df[g].dropna().unique())[:12]))
                  for g in grups])
    return df
