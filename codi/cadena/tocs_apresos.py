"""Els senyals d'un detector de tocs après per al segon (T3u del pla per tocs, `docs/pla-tocs.md`, «T3u»; D-53).

El detector són cinc xarxes com les d'A sense pilota (`xarxa_sense_pilota.py` i `xarxes.py`, tal com són): veuen el
mateix i s'entrenen igual, però aprenen, a cada imatge, si hi ha un toc de l'H a prop, un de l'A o cap (la D; vegeu
`banc/tocs_esdeveniments.py`). Les seves probabilitats són les de `xarxa_sense_pilota.probabilitats`.

Per al segon (`senyals_segon`): les tres probabilitats i el seu context (`context.calcula`), amb noms propis (`pt`) i
la convenció de `senyals.py`, perquè `senyals.intercanvia` també els giri.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cadena import context
from cadena.model import CLASSES
from possessio.oficial import possession_metrics as pm

H, A, D = (CLASSES.index(c) for c in (pm.H, pm.A, pm.D))


def senyals_segon(proba: np.ndarray, trams: tuple[tuple[int, int, int], ...]) -> pd.DataFrame:
    """Per al segon classificador: P(toc de l'H), P(toc de l'A) i P(cap), i el seu context (`context.calcula`)."""
    ctx = context.calcula(proba, trams)
    ctx.columns = [_nom(c) for c in ctx.columns]
    seves = pd.DataFrame({"pt_h": proba[:, H], "pt_a": proba[:, A], "pt_d": proba[:, D]}).astype(np.float32)
    return pd.concat([seves, ctx], axis=1)


def _nom(col: str) -> str:
    """Els noms de `context.calcula` amb `pt` (dif_p → dif_pt, morta → cap_toc, p_h → pt_h)."""
    if col.startswith("dif_p"):
        return "dif_pt" + col[len("dif_p"):]
    if col.startswith("morta"):
        return "cap_toc" + col[len("morta"):]
    if col.startswith("p_"):
        return "pt_" + col[len("p_"):]
    raise ValueError(f"Un senyal del context que no conec: {col}")
