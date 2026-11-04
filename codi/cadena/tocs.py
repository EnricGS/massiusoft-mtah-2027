"""Els tocs de la pilota, a partir del tracking (T2 del pla per tocs, `docs/pla-tocs.md`; D-24).

Un toc és una imatge on la pilota canvia de cop de velocitat o de direcció amb un jugador a l'abast:
- **la velocitat** d'abans i la de després surten d'una recta ajustada a les `k` imatges de cada costat. Les rectes
  esmorteeixen el tremolor de la posició, i on falta la pilota en alguna d'aquestes imatges no es busca cap toc;
- **el canvi** és la diferència entre les dues velocitats (en m/s): un xut, una recepció, una desviació o una
  aturada. Es queda el màxim de cada tros de ±`k` imatges, perquè cada toc surti un sol cop;
- **l'abast:** el jugador més proper ha de ser a `abast_m` o menys. Si no hi ha ningú, és un bot o soroll;
- **l'equip** és el del jugador més proper. També es guarda a quina distància és el més proper de l'altre equip,
  perquè qui decideixi la possessió sàpiga si el toc és disputat.

Cap finestra passa d'una part a l'altra, i fora de les parts no hi ha tocs. Tot és col·lectiu: els slots de l'ATD
no tenen identitat.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from cadena.llegeix import Tracking
from possessio.oficial import possession_metrics as pm

FPS = 25


@dataclass(frozen=True)
class Parametres:
    k: int = 5                  # imatges de cada costat on s'ajusta la velocitat de la pilota
    canvi_ms: float = 5.0       # el canvi de velocitat mínim
    abast_m: float = 2.0        # on ha de ser el jugador més proper


@dataclass(frozen=True)
class Tocs:
    imatge: np.ndarray          # (m,) la imatge del vídeo de cada toc, en ordre
    equip: np.ndarray           # (m,) pm.H o pm.A: l'equip del jugador més proper
    propi_m: np.ndarray         # (m,) la distància del jugador més proper a la pilota
    altre_m: np.ndarray         # (m,) la del més proper de l'altre equip (inf si no se'n veu cap)
    canvi_ms: np.ndarray        # (m,) el canvi de velocitat


def detecta(t: Tracking, trams: tuple[tuple[int, int, int], ...], par: Parametres = Parametres()) -> Tocs:
    """Els tocs de cada part puntuada, amb el tracking en una fila per imatge (`senyals.a_reixa`)."""
    escala = np.asarray(t.camp_m, float)
    pilota, casa, fora = t.pilota * escala, t.casa * escala, t.fora * escala
    canvi = np.full(len(pilota), np.nan)
    trobades = []
    for _, inici, ultim in trams:
        canvi[inici:ultim + 1] = _canvi_de_velocitat(pilota[inici:ultim + 1], par.k)
        trobades.append(inici + _maxims(canvi[inici:ultim + 1], par.k, par.canvi_ms))
    i = np.concatenate(trobades) if trobades else np.array([], dtype=int)
    d_casa, d_fora = _mes_proper(casa[i], pilota[i]), _mes_proper(fora[i], pilota[i])
    a_l_abast = np.fmin(d_casa, d_fora) <= par.abast_m
    i, d_casa, d_fora = i[a_l_abast], d_casa[a_l_abast], d_fora[a_l_abast]
    de_casa = d_casa <= d_fora
    return Tocs(imatge=i.astype(int), equip=np.where(de_casa, pm.H, pm.A).astype(np.int8),
                propi_m=np.where(de_casa, d_casa, d_fora), altre_m=np.where(de_casa, d_fora, d_casa),
                canvi_ms=canvi[i])


def soroll_lliure(t: Tracking, trams: tuple[tuple[int, int, int], ...], k: int = 5, lluny_m: float = 5.0) -> float:
    """El tremolor de la pilota: la mediana del canvi de velocitat on és a `lluny_m` o més de tothom. Lluny de tothom
    ningú no la toca, i el que hi canvia és sobretot el soroll de la posició. NaN si no n'hi ha cap."""
    escala = np.asarray(t.camp_m, float)
    pilota = t.pilota * escala
    jugadors = np.concatenate([t.casa, t.fora], axis=1) * escala
    distancia = np.linalg.norm(jugadors - pilota[:, None, :], axis=2)
    lluny = np.where(np.isnan(distancia), np.inf, distancia).min(axis=1) >= lluny_m
    canvi = np.full(len(pilota), np.nan)
    for _, inici, ultim in trams:
        canvi[inici:ultim + 1] = _canvi_de_velocitat(pilota[inici:ultim + 1], k)
    valors = canvi[lluny & ~np.isnan(canvi)]
    return float(np.median(valors)) if len(valors) else float("nan")


def _pendents(pilota: np.ndarray, k: int) -> np.ndarray:
    """(n − k, 2): la velocitat (m/s) de la recta ajustada a cada finestra de k + 1 imatges; NaN si en falta alguna."""
    if len(pilota) <= k:
        return np.empty((0, 2))
    j = np.arange(k + 1) - k / 2
    pesos = j / (j ** 2).sum()
    return sliding_window_view(pilota, k + 1, axis=0) @ pesos * FPS


def _canvi_de_velocitat(pilota: np.ndarray, k: int) -> np.ndarray:
    """|v(després) − v(abans)| a cada imatge, amb les rectes de [t − k, t] i de [t, t + k]; NaN a les vores."""
    canvi = np.full(len(pilota), np.nan)
    pendents = _pendents(pilota, k)
    if len(pendents) > k:
        abans, despres = pendents[:-k], pendents[k:]          # la que acaba a t, i la que comença a t
        canvi[k:len(pilota) - k] = np.linalg.norm(despres - abans, axis=1)
    return canvi


def _maxims(canvi: np.ndarray, k: int, minim: float) -> np.ndarray:
    """Les imatges on el canvi passa del mínim i és el més gran de ±k (el primer, si n'hi ha d'iguals)."""
    valors = np.where(np.isnan(canvi), -np.inf, canvi)
    if len(valors) == 0:
        return np.array([], dtype=int)
    farcit = np.pad(valors, k, constant_values=-np.inf)
    finestres = sliding_window_view(farcit, 2 * k + 1)
    primer = np.argmax(finestres, axis=1) == k
    return np.flatnonzero((valors >= minim) & primer)


def _mes_proper(jugadors: np.ndarray, pilota: np.ndarray) -> np.ndarray:
    """La distància del jugador més proper a la pilota, a cada imatge; inf si no se'n veu cap."""
    d = np.linalg.norm(jugadors - pilota[:, None, :], axis=2)
    return np.where(np.isnan(d), np.inf, d).min(axis=1) if d.shape[1] else np.full(len(pilota), np.inf)
