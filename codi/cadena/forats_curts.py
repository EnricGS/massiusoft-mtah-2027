"""Un model de cada forat curt, al decodificador (T3x del pla per tocs, `docs/pla-tocs.md`, «T3x»; D-56).

A curts ×¼, als forats, el que falla és el costat del forat on va el canvi d'equip, no el moment. Aquí:

- **Els forats** (`forats`): els trossos sense pilota de menys de `CURT` imatges amb la pilota vista a les dues vores,
  dins de la mateixa part.
- **Els trets de cada forat** (`trets`), del tracking, en metres i segons. Cap no depèn de quin equip és l'H.
  - Els nous (`NOUS`): el desplaçament de la pilota de la vora d'abans a la de després, la velocitat mitjana, la
    velocitat en sortir i en tornar (amb `VORA` imatges seguides com a molt i 2 com a mínim), el gir entre totes dues
    direccions i el de cadascuna amb la del desplaçament, i si el jugador més proper és el mateix a les dues vores.
  - Els que la cadena ja sap (`SABUTS`): la durada; a la vora d'abans, el més proper de cada equip (l'equip del més
    proper és el «seu»); a la de després, el més proper del seu equip i el de l'altre, i si el més proper és del seu;
    a cada vora, la distància de la pilota a la línia més propera (negativa si és fora).
- **El cost** (`cost`): als canvis d'H a A i d'A a H de dins de cada forat (de la primera imatge sense pilota a la
  primera amb pilota després), c passa a max(0, c − β · r), on r és el que diu el model del forat més enllà del que és
  habitual (`r_de`).
- **El decodificador** (`per_trams`): com `banc.model_a_canvis.per_trams`, amb el cost ja fet.
- **Les columnes del segon** (`columnes_del_segon`; T3y, D-57): a cada imatge a `K` o menys d'un forat curt, dins de la
  part, els trets del forat més proper (a la mateixa distància, el d'abans) i on és la imatge respecte del forat (les
  que falten per arribar-hi, negatiu; 0 a dins; les que fa que se n'ha sortit, positiu). NaN a la resta.

No toca res del que rep.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cadena import decodifica_tocs as dt
from cadena.llegeix import Tracking
from possessio.oficial import possession_metrics as pm

CURT = 5 * pm.FPS                       # un forat curt: de menys de 5 s
VORA = 5                                # imatges seguides amb pilota, com a molt, per a la velocitat a cada vora
P_MINIM = 1e-3                          # la p del model, entre P_MINIM i 1 − P_MINIM
NOUS = ("desplacament", "velocitat", "v_sortida", "v_tornada", "gir", "gir_sortida", "gir_tornada",
        "mateix_jugador")
SABUTS = ("durada", "seu_sortida", "altre_sortida", "seu_tornada", "altre_tornada", "es_del_seu", "linia_sortida",
          "linia_tornada")
TRETS = (*NOUS, *SABUTS)
K = 6                                   # imatges a cada banda d'un forat, com `banc.model_a_canvis.K`
COLUMNES = (*(f"forat_{x}" for x in TRETS), "forat_on")


def forats(vista: np.ndarray, parts: tuple[tuple[int, int, int], ...]) -> np.ndarray:
    """(m, 4) Els forats curts: la primera i l'última imatge sense pilota, i l'inici i l'última de la part."""
    out = []
    for _, inici, ultim in parts:
        vores = np.diff(np.r_[0, (~vista[inici:ultim + 1]).astype(np.int8), 0])
        for a, b in zip(np.flatnonzero(vores == 1), np.flatnonzero(vores == -1) - 1):
            if a > 0 and inici + b < ultim and b - a + 1 < CURT:
                out.append((inici + a, inici + b, inici, ultim))
    return np.array(out, dtype=int).reshape(-1, 4)


def seguides(vista: np.ndarray, parts: tuple[tuple[int, int, int], ...]) -> tuple[np.ndarray, np.ndarray]:
    """(n,), (n,) Quantes imatges seguides amb pilota acaben a cada imatge, i quantes en comencen, dins de la seva
    part; 0 on no es veu."""
    enrere, endavant = np.zeros(len(vista), int), np.zeros(len(vista), int)

    def compta(v: np.ndarray) -> np.ndarray:
        c = np.cumsum(v)
        return c - np.maximum.accumulate(np.where(v == 0, c, 0))

    for _, inici, ultim in parts:
        v = vista[inici:ultim + 1].astype(int)
        enrere[inici:ultim + 1] = compta(v)
        endavant[inici:ultim + 1] = compta(v[::-1])[::-1]
    return enrere, endavant


def angle(u: np.ndarray, w: np.ndarray) -> np.ndarray:
    """(m,) L'angle en graus entre cada parell de vectors; NaN si algun és zero o no se sap."""
    nu, nw = np.hypot(*u.T), np.hypot(*w.T)
    with np.errstate(invalid="ignore", divide="ignore"):
        cos = (u * w).sum(axis=1) / (nu * nw)
        return np.where((nu > 0) & (nw > 0), np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))), np.nan)


def velocitat(pilota: np.ndarray, des_de: np.ndarray, seguides_: np.ndarray, cap: int) -> np.ndarray:
    """(m, 2) En m/s, la de la pilota de `des_de` a `cap` (−1 enrere, +1 endavant) amb les imatges seguides que hi ha,
    `VORA` com a molt; NaN si no n'hi ha 2."""
    j = np.minimum(seguides_[des_de], VORA) - 1
    altra = des_de + cap * np.maximum(j, 0)
    v = (pilota[altra] - pilota[des_de]) * cap * pm.FPS / np.maximum(j, 1)[:, None]
    return np.where((j >= 1)[:, None], v, np.nan)


def mes_proper(jugadors: np.ndarray, pilota: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(m,), (m,) La distància del més proper a la pilota (NaN si no se'n veu cap) i quin és (−1 si cap)."""
    d = np.hypot(*(jugadors - pilota[:, None, :]).transpose(2, 0, 1))
    d = np.where(np.isnan(d), np.inf, d)
    qui = np.argmin(d, axis=1)
    minim = d[np.arange(len(d)), qui]
    return np.where(np.isfinite(minim), minim, np.nan), np.where(np.isfinite(minim), qui, -1)


def a_la_linia(pilota: np.ndarray, camp: np.ndarray) -> np.ndarray:
    """(m,) La distància a la línia més propera, en metres: positiva a dins, negativa fora."""
    return np.minimum(np.minimum(pilota[:, 0], camp[0] - pilota[:, 0]), np.minimum(pilota[:, 1], camp[1] - pilota[:, 1]))


def trets(t: Tracking, forats_: np.ndarray, parts: tuple[tuple[int, int, int], ...]) -> pd.DataFrame:
    """Els `TRETS` de cada forat, en l'ordre de `forats_`."""
    camp = np.asarray(t.camp_m, float)
    pilota = t.pilota * camp
    enrere, endavant = seguides(~np.isnan(t.pilota[:, 0]), parts)
    s, e = forats_[:, 0] - 1, forats_[:, 1] + 1
    desp = pilota[e] - pilota[s]
    v_sortida = velocitat(pilota, s, enrere, -1)
    v_tornada = velocitat(pilota, e, endavant, +1)
    casa, fora = t.casa * camp, t.fora * camp
    d_h_s, qui_h_s = mes_proper(casa[s], pilota[s])
    d_a_s, qui_a_s = mes_proper(fora[s], pilota[s])
    d_h_e, qui_h_e = mes_proper(casa[e], pilota[e])
    d_a_e, qui_a_e = mes_proper(fora[e], pilota[e])
    with np.errstate(invalid="ignore"):
        seu_h = np.nan_to_num(d_h_s, nan=np.inf) <= np.nan_to_num(d_a_s, nan=np.inf)
        seu_tornada = np.where(seu_h, d_h_e, d_a_e)
        altre_tornada = np.where(seu_h, d_a_e, d_h_e)
        hi_es = np.isfinite(np.fmin(d_h_s, d_a_s)) & np.isfinite(np.fmin(d_h_e, d_a_e))
        del_seu = np.nan_to_num(seu_tornada, nan=np.inf) < np.nan_to_num(altre_tornada, nan=np.inf)
        mateix = np.where(seu_h, qui_h_s == qui_h_e, qui_a_s == qui_a_e) & del_seu
        temps = (e - s) / pm.FPS
        return pd.DataFrame({
            "desplacament": np.hypot(*desp.T),
            "velocitat": np.hypot(*desp.T) / temps,
            "v_sortida": np.hypot(*v_sortida.T),
            "v_tornada": np.hypot(*v_tornada.T),
            "gir": angle(v_sortida, v_tornada),
            "gir_sortida": angle(v_sortida, desp),
            "gir_tornada": angle(desp, v_tornada),
            "mateix_jugador": np.where(hi_es, mateix, np.nan),
            "durada": (forats_[:, 1] - forats_[:, 0] + 1) / pm.FPS,
            "seu_sortida": np.where(seu_h, d_h_s, d_a_s),
            "altre_sortida": np.where(seu_h, d_a_s, d_h_s),
            "seu_tornada": seu_tornada,
            "altre_tornada": altre_tornada,
            "es_del_seu": np.where(hi_es, del_seu, np.nan),
            "linia_sortida": a_la_linia(pilota[s], camp),
            "linia_tornada": a_la_linia(pilota[e], camp),
        }, columns=list(TRETS))


def r_de(p: np.ndarray, pi: float) -> np.ndarray:
    """El que diu el model més enllà del que és habitual: el log-odds de `p` menys el de `pi`."""
    p = np.clip(p, P_MINIM, 1 - P_MINIM)
    return np.log(p / (1 - p)) - np.log(pi / (1 - pi))


def cost(cost_: np.ndarray, forats_: np.ndarray, r: np.ndarray, beta: float) -> np.ndarray:
    """(n, 3, 3) Un cost nou: als canvis d'H a A i d'A a H de cada forat [a, b + 1], max(0, c − β · r)."""
    rebaixa = np.zeros(len(cost_))
    for (a, b, _, _), r_ in zip(forats_, r):
        rebaixa[a:b + 2] = beta * r_
    out = cost_.copy()
    on = rebaixa != 0
    for i, j in ((dt.H, dt.A), (dt.A, dt.H)):
        out[on, i, j] = np.maximum(0.0, cost_[on, i, j] - rebaixa[on])
    return out


def per_trams(relativa: np.ndarray, cost_: np.ndarray, trams: tuple[tuple[int, int, int], ...],
              d_min: int) -> np.ndarray:
    """Els codis de la mètrica: H, A o D dins de cada part, i X fora."""
    out = np.full(len(relativa), pm.X, dtype=np.int8)
    for _, inici, fi in trams:
        out[inici:fi + 1] = np.asarray(dt.CLASSES)[dt.viterbi(relativa[inici:fi + 1], cost_[inici:fi + 1], d_min)]
    return out


def de_quin(n: int, forats_: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(n,), (n,) A cada imatge, el forat curt més proper a `K` o menys dins de la part (−1 si cap; a la mateixa
    distància, el d'abans), i on és respecte d'aquest forat."""
    qui, lluny, on = np.full(n, -1), np.full(n, np.inf), np.zeros(n)
    for i, (a, b, inici, ultim) in enumerate(forats_):
        j = np.arange(max(a - K, inici), min(b + K, ultim) + 1)
        d = np.maximum(a - j, j - b).clip(min=0)
        millor = d < lluny[j]
        qui[j[millor]], lluny[j[millor]] = i, d[millor]
        on[j[millor]] = np.where(j < a, j - a, np.where(j > b, j - b, 0))[millor]
    return qui, on


def columnes_del_segon(t: Tracking, parts: tuple[tuple[int, int, int], ...]) -> pd.DataFrame:
    """(n, `COLUMNES`) Els trets del forat curt més proper i on és la imatge respecte del forat; NaN a la resta."""
    n = len(t.pilota)
    forats_ = forats(~np.isnan(t.pilota[:, 0]), parts)
    x = trets(t, forats_, parts).to_numpy(np.float32)
    qui, on = de_quin(n, forats_)
    out = np.full((n, len(COLUMNES)), np.nan, np.float32)
    hi_es = qui >= 0
    out[hi_es, :-1] = x[qui[hi_es]]
    out[hi_es, -1] = on[hi_es]
    return pd.DataFrame(out, columns=list(COLUMNES))
