"""Les etiquetes de pilota aturada del Smart Tagging al decodificador (T3ag del pla per tocs, `docs/pla-tocs.md`,
«T3ag»; D-69).

Abans de decodificar, cada etiqueta (`cadena/smart_tagging.py`) suma a la probabilitat relativa a l'entorn del seu
inici (`suma`):
- **la D, abans:** `beta_d` per imatge, durant `abans_s` segons, fins a `marge_s` abans de l'inici;
- **l'equip, després:** `beta_e` per imatge a l'equip de l'etiqueta, durant `despres_s` segons, des de `marge_s`
  després de l'inici; si l'etiqueta no porta equip, es resta `beta_e` a la D;
- **el marge:** a menys de `marge_s` de l'inici no s'hi suma res.

Tot va dins de la part on comença l'etiqueta, i les que no comencen dins de cap part no hi són. Si dues etiquetes toquen
la mateixa imatge, no se sumen: a cada classe hi va la més gran, i a la D, la més gran del que suma menys la més gran
del que resta. Sense etiquetes no canvia res. La D impossible on la neteja ha tret la pilota es posa després.
"""

from __future__ import annotations

import itertools
from typing import NamedTuple

import numpy as np

from cadena import decodifica_tocs as dt
from cadena.smart_tagging import Etiqueta
from possessio.oficial import possession_metrics as pm

FPS = pm.FPS


class Suma(NamedTuple):
    beta_d: float           # per imatge, a la D abans de l'inici
    abans_s: float
    beta_e: float           # per imatge, a l'equip després de l'inici (o es resta a la D, si no en porta)
    despres_s: float
    marge_s: float


GRAELLA = tuple(Suma(*v) for v in itertools.product((0.0, 0.25, 0.5, 1.0), (4, 10), (0.0, 0.25, 0.5, 1.0), (2, 4),
                                                    (0, 1, 2)))


def efectiva(s: Suma) -> tuple:
    """Una clau igual per als punts de la graella que sumen sempre el mateix: sense `beta_d`, `abans_s` no hi fa res;
    sense `beta_e`, `despres_s` tampoc; i sense cap dels dos, tampoc el marge."""
    abans = (s.beta_d, s.abans_s) if s.beta_d else (0.0, None)
    despres = (s.beta_e, s.despres_s) if s.beta_e else (0.0, None)
    return (*abans, *despres, s.marge_s if s.beta_d or s.beta_e else None)


def suma(etiquetes: tuple[Etiqueta, ...], n: int, trams: tuple[tuple[int, int, int], ...], s: Suma) -> np.ndarray:
    """(n, 3), en l'ordre de les classes del decodificador: el que les etiquetes sumen a la probabilitat relativa."""
    marge, abans, despres = (int(round(x * FPS)) for x in (s.marge_s, s.abans_s, s.despres_s))
    mes = np.zeros((n, 3))
    resta_d = np.zeros(n)
    for e in etiquetes:
        part = next(((a, b) for _, a, b in trams if a <= e.inici <= b), None)
        if part is None:
            continue
        a, b = part
        de, fins = max(a, e.inici - marge - abans), max(a, e.inici - marge)
        mes[de:fins, dt.D] = np.maximum(mes[de:fins, dt.D], s.beta_d)
        de, fins = min(b + 1, e.inici + marge), min(b + 1, e.inici + marge + despres)
        if e.equip is None:
            resta_d[de:fins] = np.maximum(resta_d[de:fins], s.beta_e)
        else:
            k = dt.H if e.equip == pm.H else dt.A
            mes[de:fins, k] = np.maximum(mes[de:fins, k], s.beta_e)
    mes[:, dt.D] -= resta_d
    return mes


def amb_les_etiquetes(relativa: np.ndarray, etiquetes: tuple[Etiqueta, ...], trams: tuple[tuple[int, int, int], ...],
                      s: Suma) -> np.ndarray:
    """La probabilitat relativa amb el que hi sumen les etiquetes (una còpia)."""
    return relativa + suma(etiquetes, len(relativa), trams, s)
