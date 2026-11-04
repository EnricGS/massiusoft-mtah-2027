"""Les mesures de l'ATD que el banc suposa (`docs/pla-mesura-atd.md`, «Què es mesura»).

Es calculen igual a l'ATD del partit, a l'ordinador de l'equip, i als partits oberts degradats, al banc
(`banc.mesura_atd`). Només fan servir el tracking (la pilota i els slots dels jugadors, en coordenades 0-1) i quines
imatges es puntuen: cap etiqueta.
"""

from __future__ import annotations

import hashlib
import warnings
from pathlib import Path

import numpy as np

from cadena.llegeix import Tracking

FPS = 25
VORES_FORAT_S = (1.0, 3.0, 8.0, 20.0)
VORES_PECA_S = (2.0, 10.0, 60.0)
MIG_JUGADORS = 12               # la velocitat d'un jugador, en ±12 imatges, com `cadena.senyals`
QUIETS_MS = 0.8                 # la velocitat mediana dels jugadors: per sota, als 10 partits oberts la pilota
                                # és morta en un 91-98 % de les imatges
CORREN_MS = 2.5                 # i per sobre, en un 2-5 %
EN_JOC_MS = 2.0                 # on es miren els inicis dels forats: per sobre, és morta en un 3-6 %
SALT_JUGADOR_MS = 12.0          # més de pressa és un slot que passa a una altra persona: no compta
PAS_PILOTA = 5                  # la velocitat de la pilota, en 5 imatges
RAPIDA_MS = 12.0                # com `banc.degrada.Escenari.velocitat_aire_ms`
RADI_M = 3.0                    # com `banc.degrada.Escenari.radi_aglomeracio_m`
JUGADORS_AGLOMERACIO = 3        # i `jugadors_aglomeracio`
PSEUDO = 1.0                    # el pes, en casos, de la freqüència conjunta als quocients

FORATS = ("forats_fins_1s", "forats_1_3s", "forats_3_8s", "forats_8_20s", "forats_mes_20s")   # els forats en joc
PILOTA = ("falta_quiets", "falta_corren", *FORATS, "inici_rapida", "inici_aglomeracio")
JUGADORS = ("peces_fins_2s", "peces_2_10s", "peces_10_60s", "peces_mes_60s")


def clau() -> str:
    """El codi d'aquestes mesures: les referències del banc només valen si s'han fet amb el mateix."""
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def puntuades(n: int, trams: tuple[tuple[int, int, int], ...]) -> np.ndarray:
    hi_es = np.zeros(n, bool)
    for _, inici, ultim in trams:
        hi_es[inici:ultim + 1] = True
    return hi_es


def tirades(hi_es: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(primera, última + 1) de cada tros seguit de True."""
    vores = np.diff(np.r_[0, hi_es.astype(np.int8), 0])
    return np.flatnonzero(vores == 1), np.flatnonzero(vores == -1)


def parts_per_llargada(llargades: np.ndarray, vores_s: tuple[float, ...]) -> np.ndarray:
    """De totes les imatges dels trossos, la part que és en trossos de cada llargada (entre les vores, en segons)."""
    sumes = np.bincount(np.digitize(llargades / FPS, vores_s), weights=llargades, minlength=len(vores_s) + 1)
    return sumes / sumes.sum() if sumes.sum() > 0 else sumes


def quocient(en_a: int, de_a: int, en_b: int, de_b: int) -> float:
    """log de la freqüència a A entre la freqüència a B, cadascuna acostada a la de totes dues juntes amb el pes de
    `PSEUDO` casos: amb pocs casos, el quocient s'acosta a 1. Si no n'hi ha cap enlloc, 0."""
    conjunta = (en_a + en_b) / max(de_a + de_b, 1)
    if conjunta <= 0:
        return 0.0
    a = (en_a + PSEUDO * conjunta) / (de_a + PSEUDO)
    b = (en_b + PSEUDO * conjunta) / (de_b + PSEUDO)
    return float(np.log(a / b))


def en_metres(t: Tracking) -> tuple[np.ndarray, np.ndarray]:
    escala = np.asarray(t.camp_m, float)
    return t.pilota * escala, np.concatenate([t.casa, t.fora], axis=1) * escala


def activitat(jugadors_m: np.ndarray) -> np.ndarray:
    """La velocitat mediana dels jugadors vistos a cada imatge (m/s); NaN si no n'hi ha cap."""
    k = MIG_JUGADORS
    velocitat = np.full(jugadors_m.shape[:2], np.nan)
    if len(jugadors_m) > 2 * k:
        velocitat[k:-k] = np.linalg.norm(jugadors_m[2 * k:] - jugadors_m[:-2 * k], axis=2) * FPS / (2 * k)
    velocitat[velocitat > SALT_JUGADOR_MS] = np.nan
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)          # les imatges sense cap jugador: NaN
        return np.nanmedian(velocitat, axis=1)


def falta_si(falta: np.ndarray, on: np.ndarray) -> float:
    return float(falta[on].mean()) if on.any() else float("nan")


def quiets(activitat_: np.ndarray, puntuat: np.ndarray) -> np.ndarray:
    """Els jugadors van quiets: gairebé sempre és pilota morta. Amb un llindar fix i no per terços, que depenen de
    quanta pilota morta té el partit."""
    return puntuat & np.isfinite(activitat_) & (activitat_ < QUIETS_MS)


def forats_en_joc(inicis: np.ndarray, finals: np.ndarray, quiet: np.ndarray) -> np.ndarray:
    """La llargada dels forats que no tenen cap imatge amb els jugadors quiets. Els altres són, sobretot, les estones
    de pilota morta, que són de cada partit i no de l'ATD."""
    quiets_fins = np.r_[0, np.cumsum(quiet)]
    sense_quiets = quiets_fins[finals] - quiets_fins[inicis] == 0
    return (finals - inicis)[sense_quiets]


def inicis_de_forat(pilota_m: np.ndarray, jugadors_m: np.ndarray, falta: np.ndarray,
                    en_joc: np.ndarray) -> tuple[float, float]:
    """Quant més sovint va ràpida la pilota, i quant més sovint hi ha una aglomeració, a la darrera imatge abans
    d'un forat que a totes les imatges amb pilota (log dels quocients). Només on els jugadors es mouen (`en_joc`),
    perquè els forats de la pilota morta no ho tapin."""
    vista = en_joc & ~falta
    inici = np.zeros(len(falta), bool)
    inici[:-1] = vista[:-1] & falta[1:]
    velocitat = np.full(len(falta), np.nan)
    velocitat[PAS_PILOTA:] = np.linalg.norm(pilota_m[PAS_PILOTA:] - pilota_m[:-PAS_PILOTA], axis=1) * FPS / PAS_PILOTA
    amb_velocitat = vista & np.isfinite(velocitat)
    rapida = amb_velocitat & (velocitat > RAPIDA_MS)
    distancia = np.linalg.norm(jugadors_m - pilota_m[:, None, :], axis=2)
    aglomeracio = vista & ((np.nan_to_num(distancia, nan=np.inf) <= RADI_M).sum(axis=1) >= JUGADORS_AGLOMERACIO)
    rapides = quocient(int((rapida & inici).sum()), int((amb_velocitat & inici).sum()),
                       int(rapida.sum()), int(amb_velocitat.sum()))
    apilats = quocient(int((aglomeracio & inici).sum()), int(inici.sum()), int(aglomeracio.sum()), int(vista.sum()))
    return rapides, apilats


def de_la_pilota(t: Tracking, puntuat: np.ndarray) -> dict[str, float]:
    """Les mesures de la pilota a les imatges puntuades: quant falta quan els jugadors van quiets i quan corren, la
    llargada dels forats en joc i on comencen els forats quan es mouen."""
    pilota_m, jugadors_m = en_metres(t)
    falta = np.isnan(t.pilota[:, 0])
    inicis, finals = tirades(falta & puntuat)
    activitat_ = activitat(jugadors_m)
    en_joc = puntuat & np.isfinite(activitat_) & (activitat_ > EN_JOC_MS)
    rapides, apilats = inicis_de_forat(pilota_m, jugadors_m, falta, en_joc)
    quiet = quiets(activitat_, puntuat)
    corren = puntuat & np.isfinite(activitat_) & (activitat_ > CORREN_MS)
    return {"falta_quiets": falta_si(falta, quiet), "falta_corren": falta_si(falta, corren),
            **dict(zip(FORATS, parts_per_llargada(forats_en_joc(inicis, finals, quiet), VORES_FORAT_S).tolist())),
            "inici_rapida": rapides, "inici_aglomeracio": apilats}


def dels_jugadors(t: Tracking, puntuat: np.ndarray) -> dict[str, float]:
    """De les imatges en què es veu cada slot, la part que és en trossos seguits de cada llargada."""
    llargades = []
    for equip in (t.casa, t.fora):
        for columna in range(equip.shape[1]):
            inicis, finals = tirades(~np.isnan(equip[:, columna, 0]) & puntuat)
            llargades.append(finals - inicis)
    tots = np.concatenate(llargades) if llargades else np.empty(0, np.int64)
    return dict(zip(JUGADORS, parts_per_llargada(tots, VORES_PECA_S).tolist()))
