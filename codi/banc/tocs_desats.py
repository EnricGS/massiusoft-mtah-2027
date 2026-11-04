"""Els resultats desats del banc de tocs (`banc.tocs`): on són, la clau del codi que els fa i els noms dels escenaris
de soroll, sense carregar el banc.

El banc carrega LightGBM (el model A), i LightGBM i PyTorch no poden conviure al mateix procés (cadascun porta el seu
OpenMP, i Python cau). `pilota.valida`, que fa servir PyTorch, llegeix els resultats d'aquí.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

CODI = Path(__file__).resolve().parents[1]
DIR_RESULTATS = CODI / "banc" / "resultats"
FACTORS_SOROLL = (0.0, 0.25, 0.5, 1.0, 2.0)
FITXERS_DE_LA_CLAU = ("cadena/tocs.py", "banc/degrada.py", "banc/canvis.py", "banc/tocs_reals.py", "banc/tocs.py",
                      "banc/tocs_desats.py")


def nom_soroll(factor: float) -> str:
    return f"barreja, soroll ×{factor:g}"


def clau() -> str:
    """L'empremta del codi que fa els resultats: si canvia, s'han de tornar a fer."""
    h = hashlib.sha256()
    for fitxer in FITXERS_DE_LA_CLAU:
        h.update((CODI / fitxer).read_bytes())
    return h.hexdigest()
