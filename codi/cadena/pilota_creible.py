"""La pilota a 10 m o més fora del camp, com un forat (T3w del pla per tocs, `docs/pla-tocs.md`, «T3w»; D-55).

Una pilota fora de joc no s'allunya tant de la línia: als deu partits oberts, al net, no passa mai de 10 m. Vista més
lluny és un error del tracking (al banc, la projecció de la càmera suposada d'aire, `banc/degrada.py`). Aquí es tracta
com si no es veiés, a l'entrada de la cadena i abans de cap peça:

- **La distància a la línia** (`fora_del_camp`), en metres, amb la mida del camp del partit: el que la x passa de 0 o
  de la llargada, el que la y passa de 0 o de l'amplada, i la hipotenusa dels dos. Dins del camp i a la línia, 0.
- **La neteja** (`neteja`): on és a `LLUNY_M` o més, la pilota passa a NaN, com en un forat. Els jugadors no es
  toquen, i el tracking que rep tampoc.

Tot el que ve després ja sap què fer amb un forat.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from cadena.llegeix import Tracking

LLUNY_M = 10.0


def fora_del_camp(pilota: np.ndarray, camp_m: tuple[float, float]) -> np.ndarray:
    """(n,) A quants metres de la línia és la pilota (`pilota` en coordenades 0-1), fora del camp: 0 a dins i a la
    línia, NaN on no es veu."""
    camp = np.asarray(camp_m, float)
    x, y = (pilota * camp).T
    return np.hypot(np.maximum(0.0, np.maximum(-x, x - camp[0])), np.maximum(0.0, np.maximum(-y, y - camp[1])))


def lluny(t: Tracking) -> np.ndarray:
    """(n,) On la pilota es veu a `LLUNY_M` o més fora del camp."""
    with np.errstate(invalid="ignore"):
        return fora_del_camp(t.pilota, t.camp_m) >= LLUNY_M


def neteja(t: Tracking) -> Tracking:
    """El mateix tracking, amb la pilota de `lluny` a NaN."""
    treu = lluny(t)
    if not treu.any():
        return t
    pilota = t.pilota.copy()
    pilota[treu] = np.nan
    return replace(t, pilota=pilota)
