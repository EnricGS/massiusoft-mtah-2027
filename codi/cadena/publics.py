"""La comprovació amb la finestra pública: que la cadena sigui correcta, mai per triar res (RULES §2).

Mira dues coses i en diu només ✓, ⚠ o ✗, sense cap xifra:
- **H i A ben orientats:** amb les etiquetes tal com són, l'spellF1 i el macroF1 han de ser més alts que amb H i A
  girats (un empat en un dels dos no compta en contra). Si cap dels dos no és més alt i algun és més baix, la
  cadena s'atura amb ✗. Si un diu que sí i l'altre que no, avisa (⚠).
- **Sense desfasament de segons:** el macroF1, que és imatge a imatge, ha de ser més alt tal com és que mogut 5 s
  endavant o enrere. No veu un desfasament de poques imatges: això ho prova el test de la cadena contra el banc. Si
  no, avisa (⚠): amb tan poques possessions, un model fluix també ho podria fer.

La veritat és la del clon oficial (`evaluation/gt/*_possession_gt_public.csv`, com la troba `run_evaluation.py`), i
la mètrica, l'oficial. El fitxer no en depèn: això es mira quan ja és escrit.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np

from possessio.oficial import possession_metrics as pm

PATRO = "*_possession_gt_public.csv"
DESPLACAMENT = 125                                  # 5 s
GIRA = np.array([pm.A, pm.H, pm.D, pm.X], dtype=np.int8)


def puntua(gt: np.ndarray, pred: np.ndarray) -> tuple[float, float]:
    """(spellF1, macroF1), com `possession_metrics.evaluate`, sense el bootstrap."""
    trams = pm.valid_runs(gt)
    spells = pm.spell_scores(gt, pm.fill_abstentions(pred, trams), trams)
    return spells["mean_f1"], pm.macro_f1(pm.scored_confusion(pm.confusion(gt, pred)))


def mou(pred: np.ndarray, k: int) -> np.ndarray:
    """pred[t − k]: el fitxer mogut k imatges endavant, amb X a la vora."""
    out = np.full_like(pred, pm.X)
    if k > 0:
        out[k:] = pred[:-k]
    else:
        out[:k] = pred[-k:]
    return out


def ben_orientats(tal: tuple[float, float], girat: tuple[float, float]) -> bool | None:
    """Sí si cap puntuació no és més baixa que amb H i A girats i alguna és més alta; no, al revés; si no, None."""
    millor = any(a > b for a, b in zip(tal, girat))
    pitjor = any(a < b for a, b in zip(tal, girat))
    return None if millor == pitjor else millor


def comprova(cami: Path, clon: Path, parla: Callable[[str], None]) -> bool:
    """Fals només si H i A semblen girats. Si no es pot mirar, o les imatges no quadren, només avisa."""
    veritats = sorted((clon / "evaluation" / "gt").glob(PATRO))
    if len(veritats) != 1:
        parla("⚠ No trobo la finestra pública al clon oficial: no he mirat si H i A van bé")
        return True
    try:
        gt = pm.label_codes(pm.read_label_csv(veritats[0]))
        pred = pm.label_codes(pm.read_label_csv(cami))
        if len(gt) != len(pred):
            raise ValueError("mides diferents")
        tal, girat = puntua(gt, pred), puntua(gt, GIRA[pred])
        moguts = [puntua(gt, mou(pred, k))[1] for k in (-DESPLACAMENT, DESPLACAMENT)]
    except Exception as error:  # noqa: BLE001 - el missatge pot portar dades: només el tipus
        parla(f"⚠ No he pogut puntuar la finestra pública ({type(error).__name__}): no he mirat si H i A van bé")
        return True
    bo = True
    orientats = ben_orientats(tal, girat)
    if orientats is True:
        parla("✓ H i A, ben orientats (la finestra pública)")
    elif orientats is False:
        parla("✗ H i A semblen girats (la finestra pública)")
        bo = False
    else:
        parla("⚠ Amb la finestra pública no queda clar si H i A van bé")
    if tal[1] > max(moguts):
        parla("✓ Sense desfasament de segons (la finestra pública)")
    else:
        parla("⚠ Amb la finestra pública, el fitxer potser va desfasat uns segons")
    return bo
