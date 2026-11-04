"""El decodificador amb el cost après dels canvis (T3i del pla per tocs, `docs/pla-tocs.md`, «T3i»), el d'A xarxes.

És el Viterbi del decodificador amb tocs (`decodifica_tocs.viterbi`), amb la durada mínima, sobre log(p / prior)
(`possessio.decodificacio.log_relativa`), amb un cost a cada imatge:
- **d'H a A, o al revés,** w · (−ln q). La q és la probabilitat que hi hagi un canvi d'equip a 6 imatges o menys, del
  classificador de canvis. On el canvi és probable, canviar costa poc; on no, molt;
- **cap a la D o des de la D,** λ, com al decodificador d'A (`decodifica.py`).

Cada part es decodifica per separat, i fora de les parts s'escriu X. És el de la T3i al banc
(`banc/model_a_canvis.py`, `costos` i `per_trams`), tal qual: el banc no es toca, i un test mira que donin el mateix.
"""

from __future__ import annotations

import numpy as np

from cadena import decodifica_tocs as dt
from possessio.oficial import possession_metrics as pm

Q_MINIM = 1e-4                              # perquè −ln q no sigui infinit


def costos(q: np.ndarray, lam: float, w: float) -> np.ndarray:
    """(n, 3, 3): d'H a A, o al revés, w · (−ln q); cap a la D o des de la D, λ."""
    cost = np.full((len(q), 3, 3), lam)
    entre = w * -np.log(np.clip(q, Q_MINIM, 1.0))
    cost[:, dt.H, dt.A] = entre
    cost[:, dt.A, dt.H] = entre
    return cost


def per_trams(relativa: np.ndarray, q: np.ndarray, trams: tuple[tuple[int, int, int], ...], w: float, lam: float,
              d_min: int) -> np.ndarray:
    """Els codis de la mètrica: H, A o D dins de cada part, i X fora. `relativa` és log(p / prior), (n, 3)."""
    cost = costos(q, lam, w)
    out = np.full(len(relativa), pm.X, dtype=np.int8)
    for _, inici, fi in trams:
        out[inici:fi + 1] = np.asarray(dt.CLASSES)[dt.viterbi(relativa[inici:fi + 1], cost[inici:fi + 1], d_min)]
    return out
