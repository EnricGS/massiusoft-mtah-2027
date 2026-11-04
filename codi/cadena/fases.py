"""Les fases amb equip del Smart Tagging, al decodificador (T3ak del pla per tocs, `docs/pla-tocs.md`, «T3ak»; D-73).

Només hi van les fases que diuen, per definició, l'equip que té la pilota (`CODIS`, DATA.md). Les de defensar no:
no sabem si l'equip hi és el que defensa o el que té la pilota.

Abans de decodificar, a cada imatge de dins d'una fase de l'equip X, deixant `marge_s` a cada vora (`estones`), a la
probabilitat relativa de l'altre equip s'hi resta `gamma`, i a la de la D, `delta` (`resta`). A X no s'hi toca res.
Cada fase va dins de la part on comença, i les que no comencen dins de cap part no hi són. Si dues fases toquen la
mateixa imatge, només hi compta una per equip; si són d'equips diferents, no s'hi resta res. Amb zeros, o sense fases,
no canvia res. La D impossible on la neteja ha tret la pilota es posa després.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np

from possessio.oficial import possession_metrics as pm

FPS = pm.FPS
CODIS = ("build up", "progression", "creating chances", "ball in final third", "ball in the box",
         "attacking transition")


class Fase(NamedTuple):
    inici: int              # imatge del vídeo tàctic
    final: int              # inclosa
    equip: int              # pm.H o pm.A


def estones(fases: tuple[Fase, ...], n: int, trams: tuple[tuple[int, int, int], ...], marge_s: float) -> np.ndarray:
    """(n, 2) booleà, de l'H i de l'A: les imatges de dins d'alguna fase de l'equip, sense les `marge_s` de cada vora."""
    marge = int(round(marge_s * FPS))
    dins = np.zeros((n, 2), dtype=bool)
    for f in fases:
        part = next(((a, b) for _, a, b in trams if a <= f.inici <= b), None)
        if part is not None:
            dins[f.inici + marge:min(f.final, part[1]) + 1 - marge, f.equip] = True
    return dins


def resta(relativa: np.ndarray, fases: tuple[Fase, ...], trams: tuple[tuple[int, int, int], ...], gamma: float,
          delta: float, marge_s: float) -> np.ndarray:
    """La probabilitat relativa amb `gamma` restat a l'altre equip i `delta` a la D, dins de les fases (una còpia)."""
    nova = relativa.copy()
    if gamma or delta:
        dins = estones(fases, len(relativa), trams, marge_s)
        nomes_un = dins[:, pm.H] != dins[:, pm.A]
        for k in (pm.H, pm.A):
            i = dins[:, k] & nomes_un
            nova[i, 1 - k] -= gamma
            nova[i, pm.D] -= delta
    return nova
