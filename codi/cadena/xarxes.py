"""La mitjana de cinc xarxes (T3o del pla per tocs, `docs/pla-tocs.md`, «T3o»).

La xarxa de la T3m (`xarxa.py`) s'aprèn els partits d'entrenament, i cada vegada que s'entrena ho fa d'una manera
diferent, segons l'atzar. Aquí se n'entrenen `N`, exactament com `xarxa.entrena`, i només canvia la llavor
(`LLAVORS`: la del model i les següents). La primera és, doncs, la xarxa de la T3m.

- **Entrenar** (`entrena`): les mateixes mostres i el mateix estandarditzat per a totes (les mostres són les mateixes),
  i una `xarxa.Xarxa` per llavor.
- **Les probabilitats** (`probabilitats`): la mitjana de les `N`, cadascuna amb la mitjana de la vista directa i de
  la girada, com `xarxa.probabilitats`. Arrodonides a 1/`xarxa.ARRODONIMENT` un sol cop, al final. Fora de les parts,
  NaN.
"""

from __future__ import annotations

import warnings

import numpy as np

from cadena import xarxa
from cadena.llegeix import Tracking
from cadena.model import CLASSES, GIRA, LLAVOR

N = 5
LLAVORS = tuple(LLAVOR + k for k in range(N))


def entrena(x: np.ndarray, y: np.ndarray, llavors: tuple[int, ...] = LLAVORS,
            passades: int = xarxa.PASSADES) -> tuple[tuple[xarxa.Xarxa, ...], list[list[float]]]:
    """Una xarxa per llavor, cadascuna exactament com `xarxa.entrena` amb aquella llavor, i la pèrdua de cada passada
    de cadascuna. `x` (float32) s'estandarditza al seu lloc, un sol cop."""
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.neural_network import MLPClassifier

    mitjana, escala = xarxa._mitjana_i_escala(x)
    x -= mitjana.astype(np.float32)
    x /= escala.astype(np.float32)
    xarxes, perdues = [], []
    for llavor in llavors:
        model = MLPClassifier(hidden_layer_sizes=xarxa.OCULTES, activation="relu", solver="adam", alpha=xarxa.L2,
                              batch_size=xarxa.LOT, max_iter=passades, shuffle=True, random_state=llavor,
                              early_stopping=False, tol=0.0, n_iter_no_change=passades + 1)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)      # fa les passades que toca, ni més ni menys
            model.fit(x, y)
        if list(model.classes_) != list(range(len(CLASSES))):
            raise ValueError("Per entrenar les xarxes calen imatges de H, d'A i de D")
        xarxes.append(xarxa.Xarxa(mitjana, escala, tuple(w.astype(np.float64) for w in model.coefs_),
                                  tuple(b.astype(np.float64) for b in model.intercepts_)))
        perdues.append([float(p) for p in model.loss_curve_])
    return tuple(xarxes), perdues


def probabilitats(xarxes: tuple[xarxa.Xarxa, ...], t: Tracking,
                  trams: tuple[tuple[int, int, int], ...]) -> np.ndarray:
    """(n, 3): P(H), P(A) i P(D), la mitjana de les xarxes (cadascuna, de la vista directa i de la girada),
    arrodonides; NaN fora de les parts."""
    if not xarxes:
        raise ValueError("Cal almenys una xarxa")
    c, c_girat = xarxa.canals(t, trams), xarxa.canals(xarxa.girat(t), trams)
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
