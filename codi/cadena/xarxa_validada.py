"""La xarxa de la T3m, que aprèn fins que deixa de millorar en un partit apartat (T3n del pla per tocs,
`docs/pla-tocs.md`, «T3n»).

`xarxa.py` fa sempre `xarxa.PASSADES` passades. Aquí, quantes en fa ho decideix una regla fixada abans de provar res:

- **El partit apartat** és el primer dels partits d'entrenament, en l'ordre que es donen (al banc, el del banc).
- **La primera volta** (`corba`): la xarxa aprèn amb els altres, passada a passada, amb tot el de `xarxa.py` (el que
  veu, la finestra, la mida, Adam, els lots, la L2 i la llavor). Després de cada passada, la pèrdua (l'entropia
  creuada) a les mostres del partit apartat.
- **La regla** (`s_atura`, `triades`): la volta s'atura quan la pèrdua del partit apartat fa `PACIENCIA` passades
  seguides sense baixar del seu mínim, o a les `MAXIM` passades. Les passades triades són les del mínim.
- **La segona volta** és `xarxa.entrena` amb tots els partits, també l'apartat, i amb les passades triades.

La xarxa que en surt és una `xarxa.Xarxa` com la de la T3m: es desa i es calcula igual.
"""

from __future__ import annotations

import numpy as np

from cadena import xarxa
from cadena.model import CLASSES, LLAVOR

PACIENCIA = 3
MAXIM = 60
ZERO = 1e-15                    # la probabilitat més petita per a la pèrdua, com `sklearn.metrics.log_loss`


def s_atura(perdues: list[float]) -> bool:
    """Si la primera volta s'atura després d'aquestes pèrdues del partit apartat: `PACIENCIA` passades seguides sense
    baixar del mínim (igualar-lo no és baixar), o `MAXIM` passades."""
    if not perdues:
        return False
    return len(perdues) >= MAXIM or len(perdues) - 1 - int(np.argmin(perdues)) >= PACIENCIA


def triades(perdues: list[float]) -> int:
    """Les passades del mínim de la pèrdua del partit apartat (el primer, si n'hi ha més d'un)."""
    return int(np.argmin(perdues)) + 1


def corba(x: np.ndarray, y: np.ndarray, x_apartat: np.ndarray, y_apartat: np.ndarray,
          maxim: int = MAXIM) -> tuple[list[float], list[float]]:
    """La primera volta, fins que la regla l'atura (o a `maxim` passades): la pèrdua del partit apartat i la de
    l'entrenament a cada passada. `x` i `x_apartat` (float32) s'estandarditzen al seu lloc, amb els valors de `x`."""
    from sklearn.neural_network import MLPClassifier

    mitjana, escala = xarxa._mitjana_i_escala(x)
    for m in (x, x_apartat):
        m -= mitjana.astype(np.float32)
        m /= escala.astype(np.float32)
    # Amb un RandomState (i no la llavor), cada passada continua l'atzar de l'anterior, com quan s'entrena d'un cop
    model = MLPClassifier(hidden_layer_sizes=xarxa.OCULTES, activation="relu", solver="adam", alpha=xarxa.L2,
                          batch_size=xarxa.LOT, shuffle=True, random_state=np.random.RandomState(LLAVOR),
                          early_stopping=False, tol=0.0, n_iter_no_change=maxim + 1)
    classes = np.arange(len(CLASSES))
    if not np.isin(classes, y).all():
        raise ValueError("Per entrenar la xarxa calen imatges de H, d'A i de D")
    apartat: list[float] = []
    while not (s_atura(apartat) or len(apartat) >= maxim):
        model.partial_fit(x, y, classes=classes)
        apartat.append(_perdua(model, x_apartat, y_apartat))
    return apartat, [float(p) for p in model.loss_curve_]


def entrena(per_partit: list[tuple[np.ndarray, np.ndarray]],
            maxim: int = MAXIM) -> tuple[xarxa.Xarxa, dict[str, list[float] | int]]:
    """Les dues voltes amb les mostres de cada partit d'entrenament (`xarxa.mostres`), per ordre: el primer és
    l'apartat. La xarxa, i la corba: la pèrdua del partit apartat i la de l'entrenament a cada passada de la primera
    volta, les passades triades i la pèrdua de cada passada de la segona."""
    if len(per_partit) < 2:
        raise ValueError("Calen almenys dos partits: l'apartat i un per aprendre")
    x_apartat, y_apartat = per_partit[0]
    apartat, primera = corba(np.concatenate([x for x, _ in per_partit[1:]]),
                             np.concatenate([y for _, y in per_partit[1:]]), x_apartat.copy(), y_apartat, maxim)
    passades = triades(apartat)
    entrenada, segona = xarxa.entrena(np.concatenate([x for x, _ in per_partit]),
                                      np.concatenate([y for _, y in per_partit]), passades=passades)
    return entrenada, {"apartat": apartat, "primera": primera, "passades": passades, "segona": segona}


def _perdua(model, x: np.ndarray, y: np.ndarray) -> float:
    """L'entropia creuada mitjana de `model` a les mostres `x` (ja estandarditzades), a trossos."""
    suma = 0.0
    for s in range(0, len(x), xarxa.TROS):
        p = model.predict_proba(x[s:s + xarxa.TROS]).astype(np.float64)
        suma -= np.log(np.clip(p[np.arange(len(p)), y[s:s + xarxa.TROS]], ZERO, 1.0)).sum()
    return suma / len(x)
