"""El banc d'A tocs apresos: les mostres del detector, que s'entrena dues vegades exactament igual, com encerta els
tocs, quan troba el de l'equip nou i les taules."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from banc import avalua, degrada
from banc import model_a_tocs_apresos as mta
from banc import tocs_esdeveniments as te
from banc.tests import sintetic
from cadena import xarxes
from cadena import xarxa_sense_pilota as xsp
from cadena.model import GIRA
from possessio.oficial import possession_metrics as pm

H, A, D = pm.H, pm.A, pm.D


@pytest.fixture(scope="module")
def partit():
    return degrada.aplica(sintetic.partit(n=3000), "barreja")


@pytest.fixture(scope="module")
def tocs_():
    files = np.arange(40, 3000, 60)
    return np.column_stack([files, np.where(files % 120 == 40, H, A)])


def test_les_mostres_son_tots_els_tocs_i_una_de_cada_32_i_girades(partit, tocs_):
    x, y = mta.mostres_detector(partit, tocs_)
    etiqueta = te.etiquetes_de_toc(tocs_, len(partit.veritat), partit.trams)
    files = te.files(etiqueta, avalua.trams_valids(partit))
    a_prop = np.flatnonzero(etiqueta != D)
    valides = np.zeros(len(etiqueta), dtype=bool)
    for a, b in avalua.trams_valids(partit):
        valides[a:b] = True
    assert set(a_prop[valides[a_prop]]) <= set(files)
    assert len(files) - valides[a_prop].sum() == len(np.flatnonzero(valides & (etiqueta == D))[::te.PAS])
    assert len(x) == 2 * len(files) and x.shape[1] == xsp.CANALS * 25
    np.testing.assert_array_equal(y[:len(files)], etiqueta[files])
    np.testing.assert_array_equal(y[len(files):], GIRA[etiqueta[files]])
    assert {H, A, D} <= set(y[:len(files)].tolist())


def test_el_detector_s_entrena_dues_vegades_exactament_igual(partit, tocs_):
    def una_vegada():
        x, y = mta.mostres_detector(partit, tocs_)
        entrenades, _ = xarxes.entrena(x, y, llavors=xarxes.LLAVORS[:2], passades=2)
        return xsp.probabilitats(entrenades, partit.tracking, partit.trams)

    np.testing.assert_array_equal(una_vegada(), una_vegada())


def test_com_encerta_els_tocs_el_detector():
    det = np.tile([0.1, 0.1, 0.8], (20, 1))
    det[5] = [0.6, 0.3, 0.1]                     # toc de l'H: l'encerta
    det[12] = [0.5, 0.2, 0.3]                    # toc de l'A: no l'encerta
    det[3] = [0.4, 0.3, 0.3]                     # sense toc, amb la mateixa P(toc) que el 12
    etiqueta = np.full(20, D)
    etiqueta[[5, 12]] = [H, A]
    on = np.ones(20, dtype=bool)
    on[18:] = False
    r = mta.del_detector(det, np.array([[5, H], [12, A], [19, H]]), etiqueta, on)
    assert r["n tocs"] == 2 and r["l'equip del toc"] == 0.5
    assert r["AUC"] == pytest.approx((16 + 15.5) / (2 * 16))    # el 12 empata amb el 3


def test_troba_el_toc_de_l_equip_nou_si_la_probabilitat_hi_arriba():
    det = np.zeros((60, 3))
    det[30 + mta.FINESTRA, A] = mta.LLINDAR
    det[30, H] = 0.9
    assert mta.troba(det, 30, A) and mta.troba(det, 30, H)
    assert not mta.troba(det, 30 - 1, A) and not mta.troba(det, 50, H)


def test_les_taules():
    canvis = pd.DataFrame([{"escenari": "net", mta.APRES: True, mta.FET_A_MA: False, mta.A_SENSE: True,
                            mta.A_TOCS: False}] * 3
                          + [{"escenari": "net", mta.APRES: False, mta.FET_A_MA: True, mta.A_SENSE: True,
                              mta.A_TOCS: True}])
    t = mta.taula_canvis(canvis).loc["net"]
    assert (t["n canvis"], t[f"troba el toc: {mta.APRES}"], t[f"tard: {mta.A_SENSE}"], t[f"tard: {mta.A_TOCS}"]) == (
        4, 0.75, 1.0, 0.25)
    assert (t[f"tard si el troba: {mta.A_TOCS}"], t[f"tard si no el troba: {mta.A_TOCS}"]) == (0.0, 1.0)
    errors = pd.DataFrame([{"escenari": e, "metode": m, "n imatges": 100, "errors": 10, "a l'altre equip": 8,
                            "on el segon dubta": d} for e in ("curts ×¼", "net") for m, d in ((mta.A_SENSE, 6),
                                                                                              (mta.A_TOCS, 4))])
    t = mta.taula_errors(errors)
    assert list(t.index) == ["net", "curts ×¼"]
    assert t.loc["net", "n imatges"] == 100 and t[("on el segon dubta", mta.A_TOCS)]["net"] == 0.04
    detector = pd.DataFrame([{"escenari": "net", "n tocs": n, "l'equip del toc": e, "AUC": 0.9}
                             for n, e in ((10, 0.8), (30, 0.6))])
    assert mta.taula_detector(detector).loc["net"].tolist() == [40, 0.7, 0.9]
