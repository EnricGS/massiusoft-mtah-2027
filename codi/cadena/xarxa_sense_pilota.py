"""Les xarxes veuen els jugadors també sense pilota (T3t del pla per tocs, `docs/pla-tocs.md`, «T3t»; D-52).

Les xarxes de la T3m i la T3o (`xarxa.py`, `xarxes.py`) mesuren els jugadors des de la pilota, i sense pilota tot el
que veuen d'aquella imatge és 0. Aquí, on no es veu la pilota, veuen una pilota estimada:

- **La pilota estimada** (`estimada`): a cada tros sense pilota d'una part, en línia recta i a velocitat constant d'on
  s'ha vist per darrer cop a on es torna a veure. Si el tros toca l'inici o el final de la part, quieta a la vista més
  propera. En una part sense cap pilota, no n'hi ha cap. No passa mai d'una part a l'altra.
- **El que veu la xarxa a cada imatge** (`canals`, 31 valors):
  - els 29 de `xarxa.canals`. On es veu la pilota, exactament els mateixos; on no, calculats igual amb la pilota
    estimada, i el primer, 0 (la pilota no es veu);
  - quant fa que no es veu la pilota i quant falta perquè es torni a veure (`temps`), en segons, fins a `FINS_A`. On
    es veu, 0.
- **La finestra, l'entrenament i el càlcul amb numpy,** els de `xarxa.py` i `xarxes.py`, amb aquests canals
  (`mostres`, `probabilitats`). A la finestra hi ha 31 × 25 = 775 valors.

`xarxa.py` i `xarxes.py` no es toquen: la cadena d'ara els fa servir.
"""

from __future__ import annotations

import numpy as np

from cadena import xarxa
from cadena.llegeix import Tracking
from cadena.model import CLASSES, GIRA

CANALS = xarxa.CANALS + 2
FINS_A = 10.0                   # segons
Trams = tuple[tuple[int, int, int], ...]


def estimada(pilota: np.ndarray) -> np.ndarray:
    """(n, 2): la pilota d'una part, amb els trossos on no es veu en línia recta entre les vistes del costat, i quieta
    a la vista més propera a les vores. Si no es veu mai, tota NaN."""
    vistes = np.flatnonzero(np.isfinite(pilota).all(axis=1))
    if len(vistes) == 0:
        return np.full(pilota.shape, np.nan)
    i = np.arange(len(pilota))
    return np.column_stack([np.interp(i, vistes, pilota[vistes, k]) for k in range(pilota.shape[1])])


def temps(vista: np.ndarray, fins_a: float = FINS_A) -> tuple[np.ndarray, np.ndarray]:
    """En segons, fins a `fins_a`: quant fa que no es veu la pilota i quant falta perquè es torni a veure. On es veu,
    0; si no s'ha vist abans o no es torna a veure dins de la part, `fins_a`."""
    n = len(vista)
    i = np.arange(n)
    darrera = np.maximum.accumulate(np.where(vista, i, -1))
    seguent = np.minimum.accumulate(np.where(vista, i, n)[::-1])[::-1]
    des_de = np.where(darrera >= 0, (i - darrera) / xarxa.FPS, np.inf)
    fins = np.where(seguent < n, (seguent - i) / xarxa.FPS, np.inf)
    return np.minimum(des_de, fins_a), np.minimum(fins, fins_a)


def canals(t: Tracking, trams: Trams) -> np.ndarray:
    """(n, 31) float32: el que veu la xarxa a cada imatge. Fora de les parts, 0."""
    n = len(t.fotograma)
    if not np.array_equal(t.fotograma, np.arange(n)):
        raise ValueError("La xarxa vol una fila per imatge: primer, a_reixa")
    if not trams:
        raise ValueError("No hi ha cap part")
    escala = np.asarray(t.camp_m, float)
    out = np.zeros((n, CANALS), np.float32)
    for _, inici, fi in trams:
        part = slice(inici, fi + 1)
        pilota, casa, fora = t.pilota[part] * escala, t.casa[part] * escala, t.fora[part] * escala
        vista = ~np.isnan(pilota[:, 0])
        de_debo = xarxa._una_part(pilota, casa, fora, escala)
        amb_l_estimada = xarxa._una_part(estimada(pilota), casa, fora, escala)
        amb_l_estimada[:, 0] = 0.0
        out[part, :xarxa.CANALS] = np.where(vista[:, None], de_debo, amb_l_estimada)
        out[part, xarxa.CANALS:] = np.column_stack(temps(vista))
    return out


def mostres(t: Tracking, trams: Trams, files: np.ndarray, etiquetes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Com `xarxa.mostres`, amb aquests canals: les finestres de `files` i també amb els equips girats."""
    x = np.concatenate([xarxa.finestra(canals(t, trams), trams, files),
                        xarxa.finestra(canals(xarxa.girat(t), trams), trams, files)])
    return x, np.concatenate([etiquetes, GIRA[etiquetes]]).astype(np.int8)


def probabilitats(xarxes: tuple[xarxa.Xarxa, ...], t: Tracking, trams: Trams) -> np.ndarray:
    """Com `xarxes.probabilitats`, amb aquests canals: (n, 3), la mitjana de les xarxes (cadascuna, de la vista directa
    i de la girada), arrodonida; NaN fora de les parts."""
    if not xarxes:
        raise ValueError("Cal almenys una xarxa")
    c, c_girat = canals(t, trams), canals(xarxa.girat(t), trams)
    out = np.full((len(c), len(CLASSES)), np.nan)
    dins = np.concatenate([np.arange(a, b + 1) for _, a, b in trams])
    for s in range(0, len(dins), xarxa.TROS):
        f = dins[s:s + xarxa.TROS]
        directa, girada = xarxa.finestra(c, trams, f), xarxa.finestra(c_girat, trams, f)
        suma = np.zeros((len(f), len(CLASSES)))
        for xr in xarxes:
            suma += (xarxa.endavant(xr, directa) + xarxa.endavant(xr, girada)[:, GIRA]) / 2
        out[f] = np.round(suma / len(xarxes) * xarxa.ARRODONIMENT) / xarxa.ARRODONIMENT
    return out
