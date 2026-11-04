"""Les cinc xarxes de la T3o: la primera és la de la T3m, són diferents entre si, la mitjana gira exactament amb els
equips, i dues vegades, exactament el mateix."""

from __future__ import annotations

import numpy as np
import pytest

from banc import degrada
from banc.tests import sintetic
from cadena import xarxa, xarxes
from cadena.model import GIRA, LLAVOR
from possessio.oficial import possession_metrics as pm

PASSADES_PROVA = 3


@pytest.fixture(scope="module")
def partit():
    return sintetic.partit(n=3000)


@pytest.fixture(scope="module")
def mostres(partit):
    p = degrada.aplica(partit, "barreja")
    files = np.flatnonzero(np.isin(p.veritat, (pm.H, pm.A, pm.D)))[::5]
    return xarxa.mostres(p.tracking, p.trams, files, p.veritat[files])


@pytest.fixture(scope="module")
def entrenades(mostres):
    x, y = mostres
    return xarxes.entrena(x.copy(), y, passades=PASSADES_PROVA)


def test_les_llavors():
    assert xarxes.LLAVORS == tuple(LLAVOR + k for k in range(5)) and xarxes.N == 5


def test_la_primera_es_la_de_la_t3m(mostres, entrenades):
    x, y = mostres
    t3m, perdua = xarxa.entrena(x.copy(), y, passades=PASSADES_PROVA)
    primera = entrenades[0][0]
    for a, b in zip((t3m.mitjana, t3m.escala, *t3m.pesos, *t3m.biaixos),
                    (primera.mitjana, primera.escala, *primera.pesos, *primera.biaixos)):
        np.testing.assert_array_equal(a, b)
    assert entrenades[1][0] == perdua


def test_son_diferents_entre_si(entrenades):
    xs, perdues = entrenades
    assert len(xs) == len(perdues) == 5 and all(len(p) == PASSADES_PROVA for p in perdues)
    for i in range(5):
        for j in range(i + 1, 5):
            assert not np.array_equal(xs[i].pesos[0], xs[j].pesos[0])


def test_la_mitjana_gira_exactament_amb_els_equips(partit, entrenades):
    xs, _ = entrenades
    p = degrada.aplica(partit, "barreja")
    directa = xarxes.probabilitats(xs, p.tracking, p.trams)
    girada = xarxes.probabilitats(xs, xarxa.girat(p.tracking), p.trams)
    np.testing.assert_array_equal(girada, directa[:, GIRA])
    assert not np.isnan(directa).any()
    np.testing.assert_allclose(directa.sum(axis=1), 1.0, atol=3 / xarxa.ARRODONIMENT)
    np.testing.assert_array_equal(directa * xarxa.ARRODONIMENT, np.round(directa * xarxa.ARRODONIMENT))


def test_amb_una_sola_xarxa_es_la_de_la_t3m(partit, entrenades):
    xs, _ = entrenades
    p = degrada.aplica(partit, "curts")
    np.testing.assert_array_equal(xarxes.probabilitats(xs[:1], p.tracking, p.trams),
                                  xarxa.probabilitats(xs[0], p.tracking, p.trams))


def test_fora_de_les_parts_no_hi_ha_probabilitats(partit, entrenades):
    xs, _ = entrenades
    trams = ((1, 100, 1199), (2, 1500, 2899))
    p = xarxes.probabilitats(xs, partit.tracking, trams)
    fora = np.ones(partit.n, bool)
    fora[100:1200] = fora[1500:2900] = False
    assert np.isnan(p[fora]).all() and not np.isnan(p[~fora]).any()


def test_sempre_igual(mostres, entrenades):
    x, y = mostres
    altres, perdues = xarxes.entrena(x.copy(), y, passades=PASSADES_PROVA)
    assert perdues == entrenades[1]
    for a, b in zip(altres, entrenades[0]):
        for u, v in zip(a.pesos + a.biaixos, b.pesos + b.biaixos):
            np.testing.assert_array_equal(u, v)


def test_cal_almenys_una_xarxa(partit):
    with pytest.raises(ValueError):
        xarxes.probabilitats((), partit.tracking, partit.trams)
