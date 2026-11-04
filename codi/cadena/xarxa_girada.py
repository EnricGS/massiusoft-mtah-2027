"""Les xarxes aprenen també amb el camp girat de dalt a baix (T3ad del pla per tocs, `docs/pla-tocs.md`, «T3ad»; D-65).

Les xarxes d'A equips sencers (`xarxa_equips.py`) aprenen cada imatge també amb els equips canviats, i en aplicar-les
fan la mitjana de les dues vistes. Aquí, també amb el camp girat de dalt a baix:

- **El camp girat** (`de_dalt_a_baix`): la y de la pilota i de tots els jugadors passa a 1 − y (les coordenades van de
  0 a 1). La x, igual, i on no es veu res, igual. És el mateix futbol: una jugada per la banda esquerra, feta per la
  dreta. De qui és la pilota no canvia. El que veuen les xarxes es calcula del partit girat com sempre, i hi surten la
  y i la vy canviades de signe.
- **Les mostres** (`mostres`): les de `xarxa_equips.mostres` (cada imatge, també amb els equips canviats), i cada fila,
  del partit tal qual o del girat, a l'atzar (`GIRADES`, la meitat de mitjana), amb la llavor que rep. Ni una fila més.
  `llavor` en dona una de fixa per a cada partit i escenari, la mateixa a qualsevol ordinador.
- **Les probabilitats** (`probabilitats`): com `xarxa_equips.probabilitats`, amb la mitjana de quatre vistes: la
  directa, amb els equips canviats, amb el camp girat i amb les dues coses. De cada camp, primer la mitjana de les dues
  vistes dels equips, com a `xarxa_equips.py`: així, girar els equips gira exactament les probabilitats. Arrodonides un
  sol cop, al final.

`xarxa_equips.py` i la resta no es toquen.
"""

from __future__ import annotations

import zlib
from dataclasses import replace

import numpy as np

from cadena import xarxa
from cadena import xarxa_equips as xeq
from cadena import xarxa_sense_pilota as xsp
from cadena.llegeix import Tracking
from cadena.model import CLASSES, GIRA, LLAVOR

GIRADES = 0.5                   # la part de les mostres girades, de mitjana
Trams = tuple[tuple[int, int, int], ...]


def de_dalt_a_baix(t: Tracking) -> Tracking:
    """El mateix tracking amb el camp girat de dalt a baix: la y de la pilota i dels jugadors, 1 − y."""
    return replace(t, pilota=_gira_y(t.pilota), casa=_gira_y(t.casa), fora=_gira_y(t.fora))


def _gira_y(xy: np.ndarray) -> np.ndarray:
    out = xy.copy()
    out[..., 1] = 1.0 - xy[..., 1]
    return out


def llavor(nom: str, escenari: str) -> int:
    """La de l'atzar de les mostres d'un partit i un escenari."""
    return zlib.crc32(f"{nom} · {escenari}".encode()) ^ LLAVOR


def mostres(t: Tracking, trams: Trams, files: np.ndarray, etiquetes: np.ndarray,
            llavor: int) -> tuple[np.ndarray, np.ndarray]:
    """Les de `xarxa_equips.mostres`, i cada fila, del partit tal qual o del girat de dalt a baix, a l'atzar."""
    x, y = xeq.mostres(t, trams, files, etiquetes)
    x_girat, _ = xeq.mostres(de_dalt_a_baix(t), trams, files, etiquetes)
    girades = np.random.default_rng(llavor).random(len(x)) < GIRADES
    x[girades] = x_girat[girades]
    return x, y


def probabilitats(xarxes: tuple[xarxa.Xarxa, ...], t: Tracking, trams: Trams) -> np.ndarray:
    """(n, 3): la mitjana de les xarxes, cadascuna amb la mitjana de les quatre vistes, arrodonida; NaN fora de les
    parts."""
    if not xarxes:
        raise ValueError("Cal almenys una xarxa")
    camps = []
    for u in (t, de_dalt_a_baix(t)):
        girat = xarxa.girat(u)
        camps.append(((xsp.canals(u, trams), xeq.equips(u, trams)),
                      (xsp.canals(girat, trams), xeq.equips(girat, trams))))
    out = np.full((len(t.fotograma), len(CLASSES)), np.nan)
    dins = np.concatenate([np.arange(a, b + 1) for _, a, b in trams])
    for s in range(0, len(dins), xarxa.TROS):
        f = dins[s:s + xarxa.TROS]
        finestres = [(xeq.finestra(*directa, trams, f), xeq.finestra(*girada, trams, f)) for directa, girada in camps]
        suma = np.zeros((len(f), len(CLASSES)))
        for xr in xarxes:
            tal_qual, de_dalt = (xarxa.endavant(xr, d) + xarxa.endavant(xr, g)[:, GIRA] for d, g in finestres)
            suma += (tal_qual + de_dalt) / 4
        out[f] = np.round(suma / len(xarxes) * xarxa.ARRODONIMENT) / xarxa.ARRODONIMENT
    return out
