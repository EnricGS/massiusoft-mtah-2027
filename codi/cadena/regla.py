"""La regla de la línia base: l'equip del jugador més proper a la pilota, i una majoria dins de cada part.

És la idea de la línia base publicada (EVALUATION.md: «nearest tracked player to the ball,
then a majority vote over a window»), escrita de nou a partir d'aquesta descripció.
"""

from __future__ import annotations

import numpy as np


def jugador_mes_proper(pilota: np.ndarray, casa: np.ndarray, fora: np.ndarray,
                       camp_m: tuple[float, float]) -> np.ndarray:
    """H o A segons l'equip del jugador més proper, en metres; X si no hi ha pilota o cap jugador."""
    escala = np.asarray(camp_m, float)

    def distancia(jugadors: np.ndarray) -> np.ndarray:
        d = np.hypot(*((jugadors - pilota[:, None, :]) * escala).transpose(2, 0, 1))
        return np.where(np.isnan(d), np.inf, d).min(axis=1, initial=np.inf)

    dh, da = distancia(casa), distancia(fora)
    return np.where(dh < da, "H", np.where(da < dh, "A", "X"))


VOTEN = ("H", "A", "D")


def majoria(etiquetes: np.ndarray, finestra: int) -> np.ndarray:
    """L'etiqueta que més surt (H, A o D) a la finestra centrada en cada fotograma; X si n'hi ha dues
    empatades al capdamunt, o si a la finestra només hi ha X. Sense cap D, és la majoria entre H i A de la línia base."""
    n = len(etiquetes)
    primer = np.arange(n) - finestra // 2
    inici, fi = np.clip(primer, 0, n), np.clip(primer + finestra, 0, n)
    compta = np.stack([np.concatenate([[0], np.cumsum(etiquetes == e)]) for e in VOTEN])
    vots = compta[:, fi] - compta[:, inici]
    millor = vots.max(axis=0)
    sol = (vots == millor).sum(axis=0) == 1
    return np.where(sol & (millor > 0), np.array(VOTEN)[vots.argmax(axis=0)], "X")


def per_fotograma(fotograma: np.ndarray, etiquetes: np.ndarray, n: int,
                  trams: tuple[tuple[int, int, int], ...], finestra: int) -> np.ndarray:
    """Una etiqueta per a cada fotograma del vídeo: la majoria dins de cada part, i X fora de les parts."""
    if len(np.unique(fotograma)) != len(fotograma):
        raise ValueError("L'ATD repeteix algun fotograma")
    fila = np.full(n, "X")
    dins = (fotograma >= 0) & (fotograma < n)
    fila[fotograma[dins]] = etiquetes[dins]
    sortida = np.full(n, "X")
    for _, inici, fi in trams:
        sortida[inici:fi + 1] = majoria(fila[inici:fi + 1], finestra)
    return sortida
