"""El detector de les possessions engolides (T3aj del pla per tocs, `docs/pla-tocs.md`, «T3aj»; D-72).

Una possessió engolida és una possessió curta de l'altre equip que queda dins d'una possessió predita. El detector
només mira les imatges de dins de les possessions predites d'A pilota morta (`possessions`), i en dona la probabilitat
que la veritat hi sigui l'altre equip. Les seves columnes (`columnes`) es diuen respecte de l'equip predit («mateix» i
«altre»), i per això no cal girar els equips: girant-los, són les mateixes. Cap d'elles mira la veritat.

Com s'aplica (`suma`): dins de les possessions predites, a la probabilitat relativa de l'altre equip s'hi suma
`beta` vegades el logit de la del detector, i després es torna a decodificar amb el mateix decodificador. La D no es
toca, i on la D era impossible ho continua sent. Amb `beta` = 0 no canvia res.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cadena.llegeix import Tracking
from possessio.oficial import possession_metrics as pm

FPS = pm.FPS
MIG = 3                          # imatges abans i després per al canvi de velocitat de la pilota
FINESTRES = (12, 25)             # ±0,5 s i ±1 s
TOPALL = 10 * FPS                # els comptadors d'imatges es tallen a 10 s
EPS = 1e-6

PECES = ("canvi", "d_mateix", "d_altre", "altre_mes_a_prop")
AGREGA = {"canvi": "max", "d_mateix": "min", "d_altre": "min", "altre_mes_a_prop": "max"}
COLUMNES = (*PECES, *(f"{c}_{w}" for w in FINESTRES for c in PECES),
            "vista", "sense_des_de", "sense_fins_a",
            "rel_mateix", "rel_altre", "q", "des_de_l_inici", "fins_al_final", "durada")


def _mes_a_prop(jugadors: np.ndarray, pilota: np.ndarray) -> np.ndarray:
    """La distància del jugador més a prop de la pilota; NaN si no es veu la pilota o no hi ha cap jugador."""
    d = np.linalg.norm(jugadors - pilota[:, None, :], axis=2)
    minim = np.where(np.isnan(d), np.inf, d).min(axis=1, initial=np.inf)
    return np.where(np.isfinite(minim), minim, np.nan)


def peces(t: Tracking) -> tuple[np.ndarray, np.ndarray]:
    """Les peces d'un toc: (n,) quant canvia la velocitat de la pilota (m/s) entre `MIG` imatges abans i `MIG` després,
    i (n, 2) la distància (m) del jugador de l'H i de l'A més a prop de la pilota. NaN on no es pot saber."""
    camp = np.asarray(t.camp_m, float)
    pilota = t.pilota * camp
    v = np.full_like(pilota, np.nan)
    v[1:-1] = (pilota[2:] - pilota[:-2]) / 2 * FPS
    canvi = np.full(len(pilota), np.nan)
    canvi[MIG:-MIG] = np.linalg.norm(v[2 * MIG:] - v[:-2 * MIG], axis=1)
    return canvi, np.stack([_mes_a_prop(t.casa * camp, pilota), _mes_a_prop(t.fora * camp, pilota)], axis=1)


def sense_pilota(vista: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per a cada imatge, quantes en fa que es va veure la pilota per últim cop i quantes en falten perquè es torni a
    veure (0 si es veu), tallades a `TOPALL`."""
    n = len(vista)
    i = np.arange(n)
    ultima = np.maximum.accumulate(np.where(vista, i, -TOPALL - n))
    seguent = np.minimum.accumulate(np.where(vista, i, 2 * n + TOPALL)[::-1])[::-1]
    return np.minimum(i - ultima, TOPALL), np.minimum(seguent - i, TOPALL)


def possessions(pred: np.ndarray, trams: list[tuple[int, int]]) -> tuple[np.ndarray, ...]:
    """Les possessions predites dins de cada tram [inici, final): (n,) l'equip (−1 fora), i quantes imatges fa que va
    començar, quantes en falten perquè acabi i quantes en dura (NaN fora)."""
    n = len(pred)
    equip = np.full(n, -1, dtype=np.int8)
    des, fins, durada = (np.full(n, np.nan) for _ in range(3))
    for a, b, k in pm.possession_spells(pred, trams):
        equip[a:b] = k
        des[a:b] = np.arange(b - a)
        fins[a:b] = np.arange(b - a)[::-1]
        durada[a:b] = b - a
    return equip, des, fins, durada


def _per_trams(x: np.ndarray, trams: list[tuple[int, int]], w: int, com: str) -> np.ndarray:
    """El màxim o el mínim de ±`w` imatges, sense sortir del tram; NaN fora dels trams."""
    out = np.full(x.shape, np.nan)
    for a, b in trams:
        out[a:b] = getattr(pd.DataFrame(x[a:b]).rolling(2 * w + 1, center=True, min_periods=1), com)().to_numpy()
    return out


def _de_l_equip(x: np.ndarray, equip: np.ndarray, altre: bool) -> np.ndarray:
    """De (n, 2), la columna de l'equip predit (o de l'altre); NaN fora de les possessions predites."""
    dins = equip >= 0
    k = np.where(dins, equip, 0) if not altre else np.where(dins, 1 - equip, 0)
    return np.where(dins, x[np.arange(len(x)), k], np.nan)


def columnes(t: Tracking, relativa: np.ndarray, q: np.ndarray, pred: np.ndarray,
             trams: list[tuple[int, int]]) -> pd.DataFrame:
    """Les columnes del detector (`COLUMNES`), una fila per imatge, respecte de l'equip predit per `pred` a cada imatge.
    Fora de les possessions predites, les que depenen de l'equip són NaN."""
    equip, des, fins, durada = possessions(pred, trams)
    canvi, dist = peces(t)
    altre_a_prop = np.where(np.isnan(dist).any(axis=1), np.nan, 0.0)[:, None] + np.stack(
        [dist[:, pm.A] < dist[:, pm.H], dist[:, pm.H] < dist[:, pm.A]], axis=1)
    per_equip = {"d_mateix": (dist, False), "d_altre": (dist, True), "altre_mes_a_prop": (altre_a_prop, False)}

    out = {"canvi": canvi, **{c: _de_l_equip(x, equip, altre) for c, (x, altre) in per_equip.items()}}
    for w in FINESTRES:
        out[f"canvi_{w}"] = _per_trams(canvi[:, None], trams, w, AGREGA["canvi"])[:, 0]
        for c, (x, altre) in per_equip.items():
            out[f"{c}_{w}"] = _de_l_equip(_per_trams(x, trams, w, AGREGA[c]), equip, altre)
    vista = ~np.isnan(t.pilota[:, 0])
    out["vista"] = vista.astype(float)
    out["sense_des_de"], out["sense_fins_a"] = (x.astype(float) for x in sense_pilota(vista))
    out["rel_mateix"] = _de_l_equip(relativa[:, [pm.H, pm.A]], equip, False)
    out["rel_altre"] = _de_l_equip(relativa[:, [pm.H, pm.A]], equip, True)
    out["q"] = np.asarray(q, float)
    out["des_de_l_inici"], out["fins_al_final"], out["durada"] = des, fins, durada
    return pd.DataFrame({c: out[c] for c in COLUMNES})


def suma(relativa: np.ndarray, p_altre: np.ndarray, equip: np.ndarray, beta: float) -> np.ndarray:
    """La probabilitat relativa amb `beta` vegades el logit de `p_altre` sumat a l'altre equip, només dins de les
    possessions predites (`equip` ≥ 0). Una còpia; la D no es toca."""
    nova = relativa.copy()
    if beta:
        i = np.flatnonzero(equip >= 0)
        p = np.clip(p_altre[i], EPS, 1 - EPS)
        nova[i, 1 - equip[i]] += beta * (np.log(p) - np.log(1 - p))
    return nova
