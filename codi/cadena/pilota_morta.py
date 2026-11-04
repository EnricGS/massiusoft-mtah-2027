"""La pilota morta d'abans de la represa, a la D del decodificador (T3ah del pla per tocs, `docs/pla-tocs.md`,
«T3ah»; D-70).

Abans de decodificar, cada etiqueta de pilota aturada (`cadena/smart_tagging.py`) suma `beta_d` per imatge a la D,
durant una estona que acaba `marge_s` abans del seu inici (`suma`). A l'equip no s'hi suma res. L'estona és:
- **fixa:** `durada` segons, a totes les etiquetes;
- **per tipus:** `durada` vegades la mediana del tipus de l'etiqueta (`medianes`), la de la pilota morta seguida abans
  de les represes d'aquest tipus (`durades`) als partits d'on s'aprèn, mai al que es prova.

Tot va dins de la part on comença l'etiqueta, i les que no comencen dins de cap part no hi són. Si dues etiquetes toquen
la mateixa imatge, no se sumen: hi va la més gran. Sense etiquetes no canvia res. La D impossible on la neteja ha tret
la pilota es posa després.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import NamedTuple

import numpy as np

from cadena import decodifica_tocs as dt
from cadena.smart_tagging import TIPUS, Etiqueta
from possessio.oficial import possession_metrics as pm

FPS = pm.FPS
FIXA, PER_TIPUS = "fixa", "per tipus"
DURADES = {FIXA: (10.0, 20.0, 30.0, 45.0), PER_TIPUS: (0.5, 0.75, 1.0, 1.5)}


class Abans(NamedTuple):
    beta_d: float           # per imatge, a la D
    forma: str              # FIXA o PER_TIPUS
    durada: float           # segons (FIXA) o vegades la mediana del tipus (PER_TIPUS)
    marge_s: float          # l'estona acaba tant abans de l'inici


GRAELLA = tuple(Abans(beta_d, forma, durada, marge_s) for beta_d in (1.0, 2.0, 4.0, 8.0) for forma in (FIXA, PER_TIPUS)
                for durada in DURADES[forma] for marge_s in (0.0, 1.0, 2.0))


def _part(trams: tuple[tuple[int, int, int], ...], i: int) -> tuple[int, int] | None:
    return next(((a, b) for _, a, b in trams if a <= i <= b), None)


def durades(veritat: np.ndarray, trams: tuple[tuple[int, int, int], ...],
            represes: Iterable[tuple[int, str]]) -> tuple[tuple[str, float], ...]:
    """Per cada represa (imatge, tipus) que és dins d'una part, el tipus i els segons de D seguida just abans, a
    `veritat`, sense sortir de la part."""
    out = []
    for imatge, tipus in represes:
        part = _part(trams, imatge)
        if part is None:
            continue
        j = imatge
        while j > part[0] and veritat[j - 1] == pm.D:
            j -= 1
        out.append((tipus, (imatge - j) / FPS))
    return tuple(out)


def medianes(durades_: Iterable[tuple[str, float]]) -> dict[str, float]:
    """La mediana dels segons de cada tipus de `TIPUS`. Un tipus sense cap represa pren la de totes."""
    per_tipus: dict[str, list[float]] = {t: [] for t in TIPUS}
    for tipus, s in durades_:
        per_tipus[tipus].append(s)
    totes = [s for v in per_tipus.values() for s in v]
    return {t: float(np.median(v if v else totes)) for t, v in per_tipus.items()}


def finestres(a: Abans, medianes_: dict[str, float]) -> dict[str, int]:
    """Les imatges de l'estona de cada tipus."""
    return {t: int(round((a.durada if a.forma == FIXA else a.durada * medianes_[t]) * FPS)) for t in TIPUS}


def efectiva(a: Abans, medianes_: dict[str, float]) -> tuple:
    """Una clau igual per als punts que, amb aquestes medianes, sumen sempre el mateix."""
    f = finestres(a, medianes_)
    return a.beta_d, int(round(a.marge_s * FPS)), tuple(f[t] for t in TIPUS)


def suma(etiquetes: tuple[Etiqueta, ...], n: int, trams: tuple[tuple[int, int, int], ...], a: Abans,
         medianes_: dict[str, float]) -> np.ndarray:
    """(n, 3), en l'ordre de les classes del decodificador: el que les etiquetes sumen a la probabilitat relativa."""
    marge, f = int(round(a.marge_s * FPS)), finestres(a, medianes_)
    mes = np.zeros((n, 3))
    for e in etiquetes:
        part = _part(trams, e.inici)
        if part is None:
            continue
        de, fins = max(part[0], e.inici - marge - f[e.tipus]), max(part[0], e.inici - marge)
        mes[de:fins, dt.D] = np.maximum(mes[de:fins, dt.D], a.beta_d)
    return mes


def amb_les_etiquetes(relativa: np.ndarray, etiquetes: tuple[Etiqueta, ...], trams: tuple[tuple[int, int, int], ...],
                      a: Abans, medianes_: dict[str, float]) -> np.ndarray:
    """La probabilitat relativa amb el que hi sumen les etiquetes (una còpia)."""
    return relativa + suma(etiquetes, len(relativa), trams, a, medianes_)
