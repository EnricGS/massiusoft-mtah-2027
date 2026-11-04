"""El context de la q per al segon classificador de canvis (T3j del pla per tocs, `docs/pla-tocs.md`, «T3j»).

La q és la probabilitat que hi hagi un canvi d'equip a 6 imatges o menys, del primer classificador de canvis (T3i).
Com `context.py` fa amb les probabilitats d'equip, aquests senyals miren la q al voltant de cada imatge:
- la q a la mateixa imatge i desplaçada (`context.DESPLACAMENTS`);
- les seves mitjanes en finestres centrades (`context.FINESTRES`), i abans i després (`context.COSTATS`);
- el màxim en finestres centrades (`MAXIMS`), i si la imatge és el màxim a ±`PIC` (un pic).

La q no depèn de quin equip és quin, i aquests tampoc: cap no acaba en `_h` o `_a` ni comença per `dif_`, i
`senyals.intercanvia` els deixa igual. Cap finestra passa d'una part a l'altra, i fora de les parts són NaN.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cadena import senyals
from cadena.context import COSTATS, DESPLACAMENTS, FINESTRES

MAXIMS = (13, 25, 125)
PIC = 6


def calcula(q: np.ndarray, trams: tuple[tuple[int, int, int], ...]) -> pd.DataFrame:
    """Una fila per imatge (float32), amb la q (n,) del primer classificador de canvis."""
    if q.ndim != 1:
        raise ValueError("La q ha de ser una sèrie (n,)")
    if not trams:
        raise ValueError("No hi ha cap part")
    trossos = []
    for _, inici, fi in trams:
        trossos.append(pd.DataFrame(_una_part(q[inici:fi + 1].astype(float))).set_axis(pd.RangeIndex(inici, fi + 1)))
    return pd.concat(trossos).reindex(pd.RangeIndex(len(q))).astype(np.float32)


def _una_part(v: np.ndarray) -> dict[str, np.ndarray]:
    f = {"canvi_q": v}
    for k in DESPLACAMENTS:
        f[f"canvi_q@{k:+d}"] = senyals._desplaca(v, k)
    for w in FINESTRES:
        f[f"canvi_q@{w}"] = senyals._finestra(v, w, "mean")
    for w in COSTATS:
        f[f"canvi_q@p{w}"] = senyals._finestra(v, w, "mean", "passat")
        f[f"canvi_q@f{w}"] = senyals._finestra(v, w, "mean", "futur")
    for w in MAXIMS:
        f[f"canvi_q@max{w}"] = senyals._finestra(v, w, "max")
    f["canvi_pic"] = (v >= senyals._finestra(v, 2 * PIC + 1, "max")).astype(float)
    return f
