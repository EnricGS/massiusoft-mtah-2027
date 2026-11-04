"""El pas 1 de la T3x: el tipus de cada forat, l'AUC, els grups i la porta, escrita abans."""

from __future__ import annotations

import numpy as np
import pandas as pd

from banc import canvis_als_forats as caf
from banc import separen_els_forats as sef
from cadena import forats_curts as fc

H, A = caf.H, caf.A


def test_el_tipus_i_el_que_hi_fa_la_prediccio():
    toc = np.array([H, H, H, H, A, A, A, A])
    assert sef.del_forat(toc, np.array([H, H, H, H, H, A, A, A]), 3, 5) == (caf.UN, caf.FA_EL_CANVI)
    assert sef.del_forat(toc, np.full(8, H), 3, 5) == (caf.UN, caf.EL_D_ABANS)
    sempre_h = np.full(8, H)
    assert sef.del_forat(sempre_h, np.array([H, H, H, A, A, A, A, A]), 3, 5) == (caf.SENSE, caf.CANVIA)
    assert sef.del_forat(sempre_h, sempre_h, 3, 5) == (caf.SENSE, caf.NO_CANVIA)
    assert sef.del_forat(np.array([H, H, H, A, A, H, H, H]), sempre_h, 3, 5) == (caf.AMAGADA, "")


def test_l_auc_sense_els_que_no_tenen_el_tret():
    un = pd.Series([False, False, True, True, True])
    assert sef.auc(pd.Series([1.0, 2.0, 3.0, 4.0, np.nan]), un) == 1.0
    assert sef.auc(pd.Series([4.0, 3.0, 2.0, 1.0, 0.0]), un) == 0.0
    assert np.isnan(sef.auc(pd.Series([np.nan, np.nan, 1.0, 2.0, 3.0]), un))      # només n'hi ha d'un canvi


def forats_fets(separa: bool) -> pd.DataFrame:
    """200 forats de curts ×¼: la meitat d'un canvi; a cada grup, el desplaçament els separa o no."""
    rng = np.random.default_rng(0)
    tipus = np.repeat([caf.UN, caf.SENSE], 100)
    fa = np.tile(np.repeat(np.array([caf.FA_EL_CANVI, caf.EL_D_ABANS], dtype=object), 50), 2)
    fa[100:] = np.where(fa[100:] == caf.FA_EL_CANVI, caf.CANVIA, caf.NO_CANVIA)
    f = pd.DataFrame({"escenari": sef.CURTS, "tipus": tipus, "fa": fa,
                      **{x: rng.random(200) for x in fc.TRETS}})
    if separa:
        f["desplacament"] = np.where(f["tipus"] == caf.UN, 10.0, 1.0)
    return f


def test_els_grups_son_els_dos_errors():
    g = sef.dels_grups(forats_fets(False))
    assert len(g[sef.HI_CANVIA]) == len(g[sef.NO_HI_CANVIA]) == 100 and len(g[sef.TOTS]) == 200
    assert set(g[sef.HI_CANVIA]["fa"]) == {caf.FA_EL_CANVI, caf.CANVIA}
    assert g[sef.NO_HI_CANVIA]["un"].sum() == 50


def test_la_porta():
    passa, lluny = sef.porta(forats_fets(True))
    assert passa and set(lluny["tret"]) == {"desplacament"} and set(lluny["grup"]) == set(sef.GRUPS)
    f = forats_fets(False)
    for x in fc.NOUS:
        f[x] = 1.0                                     # cap tret nou no separa res
    f["durada"] = np.where(f["tipus"] == caf.UN, 10.0, 1.0)         # un que ja se sap, sí: no compta
    assert not sef.porta(f)[0]
