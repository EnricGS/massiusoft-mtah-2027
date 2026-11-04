"""El decodificador per trams: converteix les probabilitats en possessions senceres.

És el del prototip (`possessio.decodificacio`), tal qual: el Viterbi que maximitza la suma de
log(p / prior) menys `lam` per cada canvi, amb una durada mínima opcional (`d_min`, el primer i l'últim tram de cada
part n'estan exempts). Cada part es decodifica per separat, i fora de les parts s'escriu X, que no costa res.
La penalització i la durada es trien al banc, mai amb el partit que es prova.
"""

from __future__ import annotations

import numpy as np

from cadena.model import CLASSES
from possessio.decodificacio import _viterbi_durada_minima, log_relativa
from possessio.oficial import possession_metrics as pm

GRAELLA_LAMBDA = (0.0, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0)
GRAELLA_DMIN = (1, 12, 25)


def per_trams(proba: np.ndarray, prior: np.ndarray, trams: tuple[tuple[int, int, int], ...],
              lam: float, d_min: int = 1) -> np.ndarray:
    """Els codis de la mètrica: H, A o D dins de cada part, i X fora."""
    relativa = log_relativa(proba, prior)
    out = np.full(len(proba), pm.X, dtype=np.int8)
    for _, inici, fi in trams:
        out[inici:fi + 1] = np.asarray(CLASSES)[_viterbi_durada_minima(relativa[inici:fi + 1], lam, d_min)]
    return out
