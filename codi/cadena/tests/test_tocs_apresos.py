"""Els senyals del detector de tocs après per al segon (T3u): noms propis, que giren exactament amb els equips, i dues
vegades, exactament el mateix."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cadena import context, senyals, xarxa
from cadena import tocs_apresos as ta
from cadena.model import GIRA

TRAMS = ((1, 0, 299), (2, 300, 599))


def proba() -> np.ndarray:
    return np.random.default_rng(4).dirichlet([1, 1, 1], 600)


def test_els_senyals_del_detector_tenen_noms_propis():
    taula = ta.senyals_segon(proba(), TRAMS)
    assert taula.dtypes.eq(np.float32).all() and len(taula) == 600
    assert not set(taula.columns) & set(context.calcula(proba(), TRAMS).columns)
    assert not set(taula.columns) & set(xarxa.senyals_segon(proba(), TRAMS).columns)
    assert {"pt_h", "pt_a", "pt_d", "dif_pt", "cap_toc", "pt_h@max25"} <= set(taula.columns)


def test_girar_els_equips_gira_exactament_els_senyals_nous():
    p = proba()
    taula = ta.senyals_segon(p, TRAMS)
    pd.testing.assert_frame_equal(ta.senyals_segon(p[:, GIRA], TRAMS), senyals.intercanvia(taula))
    assert not taula.equals(senyals.intercanvia(taula))


def test_dues_vegades_exactament_el_mateix():
    pd.testing.assert_frame_equal(ta.senyals_segon(proba(), TRAMS), ta.senyals_segon(proba(), TRAMS))
