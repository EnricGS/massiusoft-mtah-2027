"""Les xarxes de la T3t: la pilota estimada, els temps, el que veu la xarxa (on es veu la pilota, el mateix que a la
T3m), que no passa d'una part a l'altra, que gira exactament amb els equips, numpy com scikit-learn i dues vegades,
exactament el mateix."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from banc import degrada
from banc.tests import sintetic
from cadena import xarxa, xarxes
from cadena import xarxa_sense_pilota as xsp
from cadena.model import GIRA
from possessio.oficial import possession_metrics as pm

PASSADES_PROVA = 2
NAN = np.nan


@pytest.fixture(scope="module")
def partit():
    return sintetic.partit(n=3000)


@pytest.fixture(scope="module")
def barreja(partit):
    return degrada.aplica(partit, "barreja")


@pytest.fixture(scope="module")
def mostres(barreja):
    files = np.flatnonzero(np.isin(barreja.veritat, (pm.H, pm.A, pm.D)))[::5]
    return xsp.mostres(barreja.tracking, barreja.trams, files, barreja.veritat[files])


@pytest.fixture(scope="module")
def entrenades(mostres):
    x, y = mostres
    return xarxes.entrena(x.copy(), y, llavors=xarxes.LLAVORS[:2], passades=PASSADES_PROVA)


def test_la_pilota_estimada_va_en_linia_recta_i_queda_quieta_a_les_vores():
    pilota = np.array([[NAN, NAN], [1.0, 2.0], [NAN, NAN], [NAN, NAN], [4.0, 8.0], [NAN, NAN]])
    np.testing.assert_allclose(xsp.estimada(pilota),
                               [[1, 2], [1, 2], [2, 4], [3, 6], [4, 8], [4, 8]])
    assert np.isnan(xsp.estimada(np.full((4, 2), NAN))).all()


def test_els_temps_sense_pilota():
    fps = xarxa.FPS
    vista = np.array([False, True, False, False, True, False])
    des_de, fins_a = xsp.temps(vista, fins_a=10.0)
    np.testing.assert_allclose(des_de, [10.0, 0, 1 / fps, 2 / fps, 0, 1 / fps])
    np.testing.assert_allclose(fins_a, [1 / fps, 0, 2 / fps, 1 / fps, 0, 10.0])
    llarg = np.zeros(20 * fps, dtype=bool)
    llarg[0] = True
    des_de, _ = xsp.temps(llarg)
    assert des_de[-1] == xsp.FINS_A and des_de[5 * fps] == 5.0


def test_on_es_veu_la_pilota_veu_el_mateix_que_la_xarxa_de_la_t3m(barreja):
    c, t3m = xsp.canals(barreja.tracking, barreja.trams), xarxa.canals(barreja.tracking, barreja.trams)
    assert c.shape == (barreja.n, xsp.CANALS) == (barreja.n, 31) and c.dtype == np.float32
    vista = ~np.isnan(barreja.tracking.pilota[:, 0])
    assert vista.any() and (~vista).any()
    np.testing.assert_array_equal(c[vista, :xarxa.CANALS], t3m[vista])
    assert (c[vista, xarxa.CANALS:] == 0).all()


def test_on_no_es_veu_hi_ha_la_pilota_estimada_i_els_jugadors(barreja):
    c = xsp.canals(barreja.tracking, barreja.trams)
    dins = np.zeros(barreja.n, dtype=bool)
    for _, a, b in barreja.trams:
        dins[a:b + 1] = True
    sense = np.isnan(barreja.tracking.pilota[:, 0]) & dins
    assert (c[sense, 0] == 0).all()
    assert (np.abs(c[sense, 5:29]).sum(axis=1) > 0).all()            # els jugadors, mesurats des de l'estimada
    assert (c[sense, 29] > 0).all() and (c[sense, 30] > 0).all()
    assert (c[sense, 29:] <= xsp.FINS_A).all()
    assert (c[~dins] == 0).all()


def test_la_pilota_estimada_no_passa_d_una_part_a_l_altra(partit):
    t = partit.tracking
    pilota = t.pilota.copy()
    pilota[1000:1010] = NAN                                        # la segona part comença sense pilota
    trams = ((1, 0, 999), (2, 1000, 2999))
    c = xsp.canals(replace(t, pilota=pilota), trams)
    assert (c[1000:1010, 29] == xsp.FINS_A).all()                  # no s'ha vist abans dins de la part
    np.testing.assert_allclose(c[1000:1010, 30], (10 - np.arange(10)) / xarxa.FPS, rtol=1e-6)
    np.testing.assert_array_equal(c[1000:1010, 1:3], np.repeat(c[1010:1011, 1:3], 10, axis=0))     # quieta


def test_una_part_sense_pilota_es_com_ara(partit):
    t = partit.tracking
    pilota = t.pilota.copy()
    pilota[1000:] = NAN
    trams = ((1, 0, 999), (2, 1000, 2999))
    t_ = replace(t, pilota=pilota)
    c = xsp.canals(t_, trams)
    np.testing.assert_array_equal(c[1000:, :xarxa.CANALS], xarxa.canals(t_, trams)[1000:])
    assert (c[1000:, xarxa.CANALS:] == xsp.FINS_A).all()


def test_les_mostres_porten_les_dues_vistes_i_775_valors(mostres):
    x, y = mostres
    assert x.shape[1] == xsp.CANALS * len(xarxa.DESPLACAMENTS) == 775
    n = len(y) // 2
    np.testing.assert_array_equal(y[n:], GIRA[y[:n]])


def test_girar_els_equips_gira_exactament_les_probabilitats(barreja, entrenades):
    xs, _ = entrenades
    directa = xsp.probabilitats(xs, barreja.tracking, barreja.trams)
    girada = xsp.probabilitats(xs, xarxa.girat(barreja.tracking), barreja.trams)
    np.testing.assert_array_equal(girada, directa[:, GIRA])
    dins = ~np.isnan(directa[:, 0])
    assert dins.any() and not np.isnan(directa[dins]).any()
    np.testing.assert_allclose(directa[dins].sum(axis=1), 1.0, atol=3 / xarxa.ARRODONIMENT)


@pytest.mark.filterwarnings("ignore::sklearn.exceptions.ConvergenceWarning")
def test_amb_numpy_dona_el_mateix_que_scikit_learn():
    from sklearn.neural_network import MLPClassifier

    rng = np.random.default_rng(3)
    x = rng.normal(size=(2000, 775)).astype(np.float32)
    y = (x[:, 0] > 0).astype(int) + (x[:, 1] > 1)
    m = MLPClassifier(hidden_layer_sizes=xarxa.OCULTES, max_iter=3, random_state=1).fit(x, y)
    xr = xarxa.Xarxa(np.zeros(775), np.ones(775), tuple(w.astype(float) for w in m.coefs_),
                     tuple(b.astype(float) for b in m.intercepts_))
    np.testing.assert_allclose(xarxa.endavant(xr, x[:200]), m.predict_proba(x[:200]), atol=1e-5)


def test_dues_vegades_exactament_el_mateix(barreja, mostres, entrenades):
    x, y = mostres
    xs, perdues = entrenades
    altres, altres_perdues = xarxes.entrena(x.copy(), y, llavors=xarxes.LLAVORS[:2], passades=PASSADES_PROVA)
    assert perdues == altres_perdues
    for a, b in zip(xs, altres):
        for u, v in zip(a.pesos + a.biaixos, b.pesos + b.biaixos):
            np.testing.assert_array_equal(u, v)
    np.testing.assert_array_equal(xsp.probabilitats(xs, barreja.tracking, barreja.trams),
                                  xsp.probabilitats(altres, barreja.tracking, barreja.trams))
