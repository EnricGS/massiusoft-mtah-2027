"""Decodificació conscient de la mètrica (spellF1).

L'spellF1 compta possessions senceres: un canvi fals o un D enmig d'una
possessió la trosseja i en fa perdre l'aparellament. Per això, en lloc de
triar l'etiqueta més probable frame a frame, es busca la seqüència que
maximitza

    sum_t log( p(y_t | x_t) / p(y_t) )  -  lambda * (nombre de canvis)

amb la restricció opcional que cap tram duri menys de `d_min` frames
(semi-Markov de durada mínima). Les dues coses s'ajusten només amb els
partits d'entrenament (prediccions fora de plec), maximitzant l'spellF1.
"""

from __future__ import annotations

import numpy as np

from possessio.metriques_oficials import trams_per_part

EPS = 1e-9
GRAELLA_LAMBDA = (0.0, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0)
GRAELLA_DMIN = (1, 12, 25, 50)


def log_relativa(proba: np.ndarray, prior: np.ndarray) -> np.ndarray:
    return np.log(proba + EPS) - np.log(prior + EPS)


def _viterbi_penalitzat(em: np.ndarray, lam: float) -> np.ndarray:
    n, k = em.shape
    punter = np.empty((n, k), dtype=np.int8)
    score = em[0].copy()
    fora_diag = ~np.eye(k, dtype=bool)
    for t in range(1, n):
        cand = score[:, None] - lam * fora_diag
        punter[t] = np.argmax(cand, axis=0)
        score = cand[punter[t], np.arange(k)] + em[t]
    cami = np.empty(n, dtype=np.int64)
    cami[-1] = int(np.argmax(score))
    for t in range(n - 1, 0, -1):
        cami[t - 1] = punter[t, cami[t]]
    return cami


def _viterbi_durada_minima(em: np.ndarray, lam: float, d: int) -> np.ndarray:
    """Viterbi amb estats expandits: cada classe té d subestats en cadena (el primer i l'últim tram de cada part estan exempts).

    Només es pot sortir d'una classe des del seu últim subestat (tram ja de
    >= d frames), pagant lambda. El primer tram de cada part pot ser més curt.
    """
    n, k = em.shape
    if d <= 1:
        return _viterbi_penalitzat(em, lam)
    menys_inf = -np.inf
    score = np.full((k, d), menys_inf)
    score[:, d - 1] = em[0]
    entra_de = np.zeros((n, k), dtype=np.int8)
    es_queda = np.zeros((n, k), dtype=bool)
    idx = np.arange(k)
    for t in range(1, n):
        madur = score[:, d - 1]
        ordre = np.argsort(madur)[::-1]
        millor, segon = ordre[0], ordre[1]
        origen = np.where(idx == millor, segon, millor)
        nou = np.empty_like(score)
        nou[:, 0] = madur[origen] - lam + em[t]
        if d > 2:
            nou[:, 1:d - 1] = score[:, 0:d - 2] + em[t][:, None]
        queda = score[:, d - 1] >= score[:, d - 2]
        nou[:, d - 1] = np.where(queda, score[:, d - 1], score[:, d - 2]) + em[t]
        entra_de[t], es_queda[t] = origen, queda
        score = nou
    cami = np.empty(n, dtype=np.int64)
    k_act, j_act = np.unravel_index(int(np.argmax(score)), score.shape)
    for t in range(n - 1, -1, -1):
        cami[t] = k_act
        if t == 0:
            break
        if j_act == d - 1:
            j_act = d - 1 if es_queda[t, k_act] else d - 2
        elif j_act >= 1:
            j_act -= 1
        else:
            k_act, j_act = int(entra_de[t, k_act]), d - 1
    return cami


def decodifica(proba: np.ndarray, prior: np.ndarray, periode: np.ndarray,
               lam: float, d_min: int = 1) -> np.ndarray:
    """Seqüència òptima per part (les parts es decodifiquen per separat)."""
    em = log_relativa(proba, prior)
    out = np.empty(len(proba), dtype=np.int64)
    for a, b in trams_per_part(periode):
        out[a:b] = _viterbi_durada_minima(em[a:b], lam, d_min)
    return out

