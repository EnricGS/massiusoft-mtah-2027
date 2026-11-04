"""La mètrica oficial al banc: cada partit per separat, i deixant-lo fora de l'entrenament.

Les funcions són les de `possession_metrics.py` sense modificar (la còpia del prototip, igual que la del commit
f8f2629). Com al concurs, la veritat X no es puntua i cap possessió passa d'una part a l'altra: aquí les parts
són seguides a l'array, i per això els trams es fan per part i no només amb `valid_runs`.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from banc import degrada, fonts
from banc.partit import PartitBanc
from possessio.oficial import possession_metrics as pm

Metode = Callable[[tuple[str, ...], str, PartitBanc], np.ndarray]


def trams_valids(p: PartitBanc) -> list[tuple[int, int]]:
    """[inici, final) on la veritat no és X, dins de cada part."""
    return [(inici + a, inici + b) for _, inici, ultim in p.trams
            for a, b in pm.valid_runs(p.veritat[inici:ultim + 1])]


def puntua(p: PartitBanc, prediccio: np.ndarray) -> dict[str, float]:
    gt, pred = p.veritat.astype(np.int8), prediccio.astype(np.int8)
    trams = trams_valids(p)
    spells = pm.spell_scores(gt, pm.fill_abstentions(pred, trams), trams)
    return {"spell_f1": spells["mean_f1"], "macro_f1": pm.macro_f1(pm.scored_confusion(pm.confusion(gt, pred))),
            "possessions": spells["n_pred"], "possessions_reals": spells["n_gt"]}


def avalua(metodes: dict[str, Metode], noms: tuple[str, ...], escenari: str,
           proves: tuple[str, ...] | None = None,
           carrega: Callable[[str], PartitBanc] = fonts.partit) -> list[dict]:
    """Una fila per partit i mètode. Cada mètode s'entrena amb els altres partits (en rep els noms) i es prova
    amb aquest, degradat un sol cop per a tots. `proves` en tria uns quants (per repartir la feina)."""
    files = []
    for nom in proves or noms:
        prova = degrada.aplica(carrega(nom), escenari)
        entrenament = tuple(n for n in noms if n != nom)
        com_es = degrada.resum(prova)
        for nom_metode, metode in metodes.items():
            files.append({"partit": nom, "font": prova.font, "escenari": escenari, "metode": nom_metode,
                          **puntua(prova, metode(entrenament, escenari, prova)), **com_es})
    return files
