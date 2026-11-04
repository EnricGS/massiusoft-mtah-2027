"""El classificador d'A: P(H), P(A) i P(D) per imatge, amb LightGBM.

Com funciona:
- **Simetria.** Cada imatge d'entrenament hi és dues vegades, la segona amb els equips girats (i H i A canviats a
  l'etiqueta). En predir, es fa la mitjana de les dues vistes. Així no aprèn res de quin equip és el de casa.
- **Una de cada `pas` imatges**, perquè les seguides són gairebé iguals. Les X no s'hi fan servir.
- **Determinista**: els paràmetres són fixos, amb llavor, `deterministic` i un nombre de fils fix. Mai s'ajusten
  amb el partit que es prova.
"""

from __future__ import annotations

import lightgbm as lgb
import numpy as np
import pandas as pd

from cadena import senyals
from possessio.oficial import possession_metrics as pm

CLASSES = (pm.H, pm.A, pm.D)        # les columnes de les probabilitats, i les etiquetes del LightGBM
if CLASSES != tuple(range(len(CLASSES))):
    raise ImportError("Els codis H, A i D han de ser 0, 1 i 2: fan d'etiqueta i de columna")
GIRA = np.array([CLASSES.index({pm.H: pm.A, pm.A: pm.H}.get(c, c)) for c in CLASSES])     # H i A canviats
LLAVOR = 20271024
PAS = 16                            # el del banc: la cadena entrena exactament com s'ha provat
RONDES = 300
PARAMS = {
    "objective": "multiclass",
    "num_class": len(CLASSES),
    "learning_rate": 0.05,
    "num_leaves": 63,
    "min_data_in_leaf": 400,
    "feature_fraction": 0.7,
    "bagging_fraction": 0.7,
    "bagging_freq": 1,
    "lambda_l2": 1.0,
    "num_threads": 8,
    "deterministic": True,
    "force_row_wise": True,
    "verbose": -1,
    "seed": LLAVOR,
}


def mostres(taules: list[pd.DataFrame], etiquetes: list[np.ndarray], pas: int = PAS
            ) -> tuple[pd.DataFrame, np.ndarray]:
    """Les imatges d'entrenament: una de cada `pas` de les que tenen veritat H, A o D, i cadascuna també girada."""
    xs, ys = [], []
    for taula, etiqueta in zip(taules, etiquetes):
        tria = np.flatnonzero(np.isin(etiqueta, CLASSES))[::pas]
        x = taula.iloc[tria].reset_index(drop=True)
        xs += [x, senyals.intercanvia(x)]
        ys += [etiqueta[tria], GIRA[etiqueta[tria]]]
    return pd.concat(xs, ignore_index=True), np.concatenate(ys).astype(np.int8)


def prior(y: np.ndarray) -> np.ndarray:
    """La freqüència de cada classe a les mostres: el decodificador la treu de les probabilitats."""
    return np.bincount(y, minlength=len(CLASSES)) / len(y)


def entrena(x: pd.DataFrame, y: np.ndarray, rondes: int = RONDES) -> lgb.Booster:
    """Amb les mostres de `mostres` (es fan a part perquè cada partit en pugui deixar només les seves)."""
    return lgb.train(PARAMS, lgb.Dataset(x, label=y, free_raw_data=True), num_boost_round=rondes)


def probabilitats(model: lgb.Booster, taula: pd.DataFrame) -> np.ndarray:
    """(n, 3): la mitjana de la vista original i de la girada (amb H i A tornats al seu lloc)."""
    directa = model.predict(taula)
    girada = model.predict(senyals.intercanvia(taula))[:, GIRA]
    return (directa + girada) / 2
