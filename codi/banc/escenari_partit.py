"""L'escenari «partit ×¼» (T3p del pla per tocs, `docs/pla-tocs.md`, «T3p»): el candidat que l'eina que mesura l'ATD
(D-44) ha triat al partit, aplicat com l'aplica l'eina (`banc.mesura_atd.aplica`) a cada partit obert.

El que l'eina ha dit amb paraules, i el candidat que hi correspon (`NOMS` de `banc.mesura_atd`):

- quan la pilota és morta, hi falta «gairebé sempre (com Metrica)»;
- en joc, «un 10 %», en forats «llargs»;
- els forats comencen amb la pilota ràpida «igual que a la resta»; les aglomeracions no s'han pogut mesurar, i es
  queden com al banc;
- els jugadors es perden estones «llargues (de 2 a 30 s)»;
- l'error de posició, ×¼ (V1), com tots els candidats.

No toca `banc.degrada`, que entra a la clau dels models.
"""

from __future__ import annotations

import hashlib
import inspect
from pathlib import Path

from banc import decodificador_tocs as t3
from banc import degrada
from banc import mesura_atd as m
from banc.partit import PartitBanc
from mesura import estadistiques as est

NOM = "partit ×¼"
CANDIDAT = m.CandidatPilota(forats="llargs", morta=0.97, viva=0.1, aire=0.0, aglomeracio=3.0)
PERDUA = (2.0, 30.0)                    # s


def aplica(p: PartitBanc) -> PartitBanc:
    return m.aplica(p, CANDIDAT, PERDUA)


def clau() -> str:
    """El que fa l'escenari: el candidat, i el codi de l'eina i de `degrada` que l'aplica."""
    h = hashlib.sha256(repr((NOM, CANDIDAT, PERDUA, t3.QUART)).encode())
    h.update(Path(degrada.__file__).read_bytes())
    for funcio in (m.aplica, m.forats, m.fi_de_la_morta, est.tirades, t3.amb_error, aplica):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()
