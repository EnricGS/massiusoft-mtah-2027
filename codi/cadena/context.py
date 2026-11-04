"""Els senyals del context per al segon classificador d'A (T3e del pla per tocs, `docs/pla-tocs.md`).

Es fan amb les probabilitats del primer classificador (P(H), P(A) i P(D) per imatge) al voltant de cada imatge:
- la diferència P(H) − P(A) (`dif_p`) i P(D) (`morta`), a la mateixa imatge i desplaçades (`DESPLACAMENTS`);
- les seves mitjanes en finestres centrades (`FINESTRES`), i abans i després (`COSTATS`);
- el màxim de P(H) i de P(A) en finestres centrades (`MAXIMS`).

Així el segon classificador veu com és el canvi: quant dura, i si el que ve després torna a l'equip d'abans. Segueix
la convenció de `senyals.py` (`dif_` canvia de signe, `_h` i `_a` es canvien), i com que les probabilitats del primer
giren exactament amb els equips (`model.probabilitats`), `senyals.intercanvia` també gira aquests. Cap finestra passa
d'una part a l'altra, i fora de les parts són NaN.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cadena import senyals
from cadena.model import CLASSES
from possessio.oficial import possession_metrics as pm

DESPLACAMENTS = (-125, -50, -25, -12, -5, 5, 12, 25, 50, 125)
FINESTRES = (5, 13, 25, 51, 125, 251)
COSTATS = (12, 25, 50, 125)
MAXIMS = (25, 125)
H, A, D = (CLASSES.index(c) for c in (pm.H, pm.A, pm.D))


def calcula(proba: np.ndarray, trams: tuple[tuple[int, int, int], ...]) -> pd.DataFrame:
    """Una fila per imatge (float32), amb les probabilitats (n, 3) del primer classificador."""
    if proba.ndim != 2 or proba.shape[1] != len(CLASSES):
        raise ValueError("Les probabilitats han de ser (n, 3)")
    if not trams:
        raise ValueError("No hi ha cap part")
    trossos = []
    for _, inici, fi in trams:
        trossos.append(pd.DataFrame(_una_part(proba[inici:fi + 1].astype(float))).set_axis(pd.RangeIndex(inici, fi + 1)))
    return pd.concat(trossos).reindex(pd.RangeIndex(len(proba))).astype(np.float32)


def _una_part(p: np.ndarray) -> dict[str, np.ndarray]:
    valors = {"dif_p": p[:, H] - p[:, A], "morta": p[:, D]}
    f = dict(valors)
    for nom, v in valors.items():
        for k in DESPLACAMENTS:
            f[f"{nom}@{k:+d}"] = senyals._desplaca(v, k)
        for w in FINESTRES:
            f[f"{nom}@{w}"] = senyals._finestra(v, w, "mean")
        for w in COSTATS:
            f[f"{nom}@p{w}"] = senyals._finestra(v, w, "mean", "passat")
            f[f"{nom}@f{w}"] = senyals._finestra(v, w, "mean", "futur")
    for e, columna in (("h", H), ("a", A)):
        for w in MAXIMS:
            f[f"p_{e}@max{w}"] = senyals._finestra(p[:, columna], w, "max")
    return f
