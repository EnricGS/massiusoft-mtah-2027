"""La tria del candidat, per passos (`docs/pla-mesura-atd.md`, «Com es tria»). La fan igual el banc, per validar-la
amb dades obertes (`banc.mesura_atd`), i l'eina, al partit.

Cada pas tria uns paràmetres amb unes mesures, entre els candidats que encaixen amb el que s'ha triat abans: primer la
pilota morta, amb la mesura que no depèn de res més; després la llargada dels forats; al final, on comencen. Així una
mesura que va diferent d'una font a l'altra (on comencen els forats de la pilota morta) no tria la resta.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from mesura import estadistiques as est

SIGMA_MINIMA = 1e-3

Pas = tuple[tuple[str, ...], tuple[str, ...]]          # els paràmetres que tria i les mesures amb què els tria


def referencies(taula: pd.DataFrame, claus: Sequence[str],
                columnes: Sequence[str]) -> tuple[pd.DataFrame, pd.Series]:
    """La mitjana de cada grup de candidats, i com varia cada mesura dins dels grups (l'arrel de la mitjana de les
    variàncies), entre partits i entre els paràmetres que encara no s'han triat."""
    grups = taula.groupby(list(claus))[list(columnes)]
    return grups.mean(), np.sqrt(grups.var(ddof=1).mean()).fillna(SIGMA_MINIMA).clip(lower=SIGMA_MINIMA)


def parts(mesures: Mapping[str, float], mitjanes: pd.DataFrame, sigma: pd.Series) -> pd.DataFrame:
    """De cada grup, la part de cada mesura a la distància: la diferència al quadrat, dividida per com varia."""
    return ((mitjanes - pd.Series({k: mesures[k] for k in mitjanes.columns}, dtype=float)) / sigma) ** 2


@dataclass(frozen=True)
class Triat:
    parametres: dict[str, object]
    parts: dict[str, float]                 # de cada mesura, la part de la distància al grup triat
    passos: tuple[pd.DataFrame, ...]        # de cada pas, els grups amb la distància, del més proper al més llunyà

    @property
    def distancia(self) -> float:
        return float(sum(self.parts.values()))


def com_a_valor(x: object) -> object:
    return x.item() if isinstance(x, np.generic) else x


def tria(mesures: Mapping[str, float], taula: pd.DataFrame, passos: Sequence[Pas]) -> Triat:
    triat: dict[str, object] = {}
    totes: dict[str, float] = {}
    detall = []
    for claus, columnes in passos:
        candidats = taula
        for k, v in triat.items():
            candidats = candidats[candidats[k] == v]
        mitjanes, sigma = referencies(candidats, claus, columnes)
        p = parts(mesures, mitjanes, sigma)
        distancia = p.sum(axis=1).sort_values(kind="stable")
        primer = distancia.index[0]
        triat.update(zip(claus, map(com_a_valor, primer if isinstance(primer, tuple) else (primer,))))
        totes.update(p.loc[primer].to_dict())
        detall.append(mitjanes.assign(distancia=distancia).loc[distancia.index].reset_index())
    return Triat(triat, totes, tuple(detall))


def clau() -> str:
    """Les mesures i la tria: les referències del banc només valen si s'han fet amb el mateix codi."""
    return hashlib.sha256((est.clau() + hashlib.sha256(Path(__file__).read_bytes()).hexdigest()).encode()).hexdigest()


def passos_de(bloc: Mapping) -> tuple[Pas, ...]:
    """Els passos com es desen al JSON de les referències."""
    return tuple((tuple(claus), tuple(columnes)) for claus, columnes in bloc["passos"])
