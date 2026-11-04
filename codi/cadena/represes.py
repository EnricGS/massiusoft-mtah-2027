"""L'entorn de les represes i la barreja amb el segon de les represes (T3ai del pla per tocs, `docs/pla-tocs.md`,
«T3ai»; D-71).

El segon de les represes només aprèn i només actua a **l'entorn** de cada etiqueta de pilota aturada
(`cadena/smart_tagging.py`): de `ABANS_S` segons abans del seu inici a `DESPRES_S` després, dins de la part on
comença (`entorn`). Les etiquetes que no comencen dins de cap part no hi són. A l'entorn, la probabilitat relativa és
`(1 − alfa)` vegades la d'abans més `alfa` vegades la del segon de les represes; fora, la d'abans (`barreja`). Amb
`alfa` = 0, o sense etiquetes, no canvia res. La D impossible on la neteja ha tret la pilota es posa després.
"""

from __future__ import annotations

import numpy as np

from cadena.smart_tagging import Etiqueta
from possessio.oficial import possession_metrics as pm

FPS = pm.FPS
ABANS_S, DESPRES_S = 6, 10
ALFES = (0.0, 0.25, 0.5, 0.75, 1.0)


def entorn(etiquetes: tuple[Etiqueta, ...], n: int, trams: tuple[tuple[int, int, int], ...]) -> np.ndarray:
    """(n,) booleà: les imatges de l'entorn d'alguna etiqueta."""
    dins = np.zeros(n, dtype=bool)
    for e in etiquetes:
        part = next(((a, b) for _, a, b in trams if a <= e.inici <= b), None)
        if part is not None:
            dins[max(part[0], e.inici - ABANS_S * FPS):min(part[1] + 1, e.inici + DESPRES_S * FPS)] = True
    return dins


def barreja(relativa: np.ndarray, de_les_represes: np.ndarray, entorn_: np.ndarray, alfa: float) -> np.ndarray:
    """La probabilitat relativa amb la del segon de les represes barrejada a l'entorn (una còpia). Fora de l'entorn,
    `de_les_represes` no es mira."""
    nova = relativa.copy()
    if alfa:
        nova[entorn_] = (1 - alfa) * relativa[entorn_] + alfa * de_les_represes[entorn_]
    return nova
