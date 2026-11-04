"""Capa fina sobre la mètrica oficial (`oficial/possession_metrics.py`, sense modificar).

El codi oficial divideix el partit en trams vàlids buscant els frames que no
són X a la veritat. Als nostres partits les dues parts són contigües (no hi ha
forat de mitja part), de manera que li passem explícitament un tram per part:
així cap possessió ni cap transició pot creuar la mitja part, igual que a
l'avaluació oficial.

Codis: els nostres HOME=0, AWAY=1, ATURAT=2 coincideixen amb H=0, A=1, D=2.
"""

from __future__ import annotations

import numpy as np

from possessio import config
from possessio.oficial import possession_metrics as pm

assert (config.HOME, config.AWAY, config.ATURAT) == (pm.H, pm.A, pm.D)


def trams_per_part(periode: np.ndarray) -> list[tuple[int, int]]:
    canvis = np.flatnonzero(np.diff(periode) != 0) + 1
    vores = np.concatenate([[0], canvis, [len(periode)]])
    return [(int(a), int(b)) for a, b in zip(vores[:-1], vores[1:])]


def avalua_oficial(y: np.ndarray, pred: np.ndarray, periode: np.ndarray) -> dict:
    """spellF1 (rànquing), macroF1 (desempat) i les mètriques temporals oficials."""
    gt = y.astype(np.int8)
    pr = pred.astype(np.int8)
    trams = trams_per_part(periode)
    cm3 = pm.scored_confusion(pm.confusion(gt, pr))
    omplert = pm.fill_abstentions(pr, trams)
    spells = pm.spell_scores(gt, omplert, trams)
    t_gt, t_pr = pm.transitions(gt, trams), pm.transitions(omplert, trams)
    n_gt_seg, n_pr_seg, frag = pm.fragmentation(gt, omplert, trams)
    est_gt, est_pr = pm.possession_stats(gt, trams), pm.possession_stats(omplert, trams)
    return {
        "spell_f1": spells["mean_f1"],
        "spell_f1_iou": {str(k): v["f1"] for k, v in spells["per_iou"].items()},
        "macro_f1": pm.macro_f1(cm3),
        "accuracy": pm.accuracy(cm3),
        "alive_dead_f1": pm.alive_dead_f1(cm3),
        "f1_per_classe": {nom: pm.per_class_prf(cm3, k)[2] for k, nom in enumerate(pm.SCORED)},
        "possessions_reals": spells["n_gt"],
        "possessions_predites": spells["n_pred"],
        "durada_mitjana_real_s": est_gt["mean_duration_s"],
        "durada_mitjana_predita_s": est_pr["mean_duration_s"],
        "fragmentacio": frag,
        "transicions_f1": {str(t): pm.transition_scores(t_gt, t_pr, t)["f1"] for t in pm.TAUS},
    }


def spell_f1(y: np.ndarray, pred: np.ndarray, periode: np.ndarray) -> float:
    trams = trams_per_part(periode)
    return pm.spell_scores(y.astype(np.int8), pm.fill_abstentions(pred.astype(np.int8), trams), trams)["mean_f1"]


def macro_f1(y: np.ndarray, pred: np.ndarray) -> float:
    return pm.macro_f1(pm.scored_confusion(pm.confusion(y.astype(np.int8), pred.astype(np.int8))))


def desplaca(pred: np.ndarray, periode: np.ndarray, n: int) -> np.ndarray:
    """Prediccions endarrerides n frames (n < 0: avançades), dins de cada part."""
    out = pred.copy()
    for a, b in trams_per_part(periode):
        tros = pred[a:b]
        if n > 0:
            out[a:b] = np.concatenate([np.full(n, tros[0]), tros[:-n]])
        elif n < 0:
            out[a:b] = np.concatenate([tros[-n:], np.full(-n, tros[-1])])
    return out
