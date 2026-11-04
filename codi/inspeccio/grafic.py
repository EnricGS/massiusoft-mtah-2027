"""Aspecte de les figures de l'informe."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

PAPER = "#F7F6F2"
SUPERFICIE = "#ECEBE6"
TINTA = "#15171A"
TINTA_2 = "#5A606A"
LOCAL = "#1D4ED8"        # H
VISITANT = "#C2410C"     # A
NEUTRE = "#7A808A"       # D, o sense equip
PILOTA = "#FFE45C"
AMPLE_IN = 9.0
DPI = 110

plt.rcParams.update({
    "figure.facecolor": PAPER, "axes.facecolor": PAPER, "savefig.facecolor": PAPER,
    "axes.edgecolor": TINTA_2, "axes.labelcolor": TINTA, "text.color": TINTA,
    "xtick.color": TINTA_2, "ytick.color": TINTA_2, "axes.spines.top": False,
    "axes.spines.right": False, "font.size": 9, "axes.titlesize": 10,
    "axes.grid": True, "grid.color": TINTA_2, "grid.alpha": 0.15, "figure.dpi": DPI,
})


def figura(alcada_in: float = 3.2, files: int = 1, columnes: int = 1, **opcions):
    return plt.subplots(files, columnes, figsize=(AMPLE_IN, alcada_in), **opcions)


def color_equip(index: int) -> str:
    return (LOCAL, VISITANT)[index] if index in (0, 1) else NEUTRE


def ombreja_rangs(ax, rangs, fps: int, en_minuts: bool = True) -> None:
    """Pinta de fons els trams que es puntuen."""
    escala = 60 * fps if en_minuts else 1
    for _, inici, fi in rangs:
        ax.axvspan(inici / escala, fi / escala, color=SUPERFICIE, zorder=0, lw=0)
