"""L'entorn de les represes i la barreja (T3ai): on actua el segon de les represes, i què hi fa."""

from __future__ import annotations

import numpy as np

from cadena import represes as rp
from cadena.smart_tagging import Etiqueta
from possessio.oficial import possession_metrics as pm

H, A = pm.H, pm.A
TOT = ((1, 0, 2999),)


def test_l_entorn_de_6_s_abans_a_10_s_despres():
    x = rp.entorn((Etiqueta(1000, 1100, "corner", H),), 3000, TOT)
    np.testing.assert_array_equal(np.flatnonzero(x), np.arange(850, 1250))
    y = rp.entorn((Etiqueta(1000, 1100, "corner", H), Etiqueta(1300, 1350, "banda", None)), 3000, TOT)
    np.testing.assert_array_equal(np.flatnonzero(y), np.arange(850, 1550))


def test_l_entorn_dins_de_la_part_i_sense_les_de_fora():
    trams = ((1, 0, 999), (2, 1000, 1999))
    x = rp.entorn((Etiqueta(1050, 1100, "falta", A), Etiqueta(1950, 1990, "porta", A), Etiqueta(2500, 2600, "corner", H)),
                  3000, trams)
    np.testing.assert_array_equal(np.flatnonzero(x), [*range(1000, 1300), *range(1800, 2000)])
    assert not rp.entorn((), 3000, TOT).any()


def test_fora_de_l_entorn_no_canvia_res():
    rng = np.random.default_rng(0)
    relativa, de_les_represes = rng.normal(size=(3000, 3)), rng.normal(size=(3000, 3))
    entorn = rp.entorn((Etiqueta(1000, 1100, "corner", H),), 3000, TOT)
    for alfa in rp.ALFES:
        x = rp.barreja(relativa, de_les_represes, entorn, alfa)
        np.testing.assert_array_equal(x[~entorn], relativa[~entorn])
        np.testing.assert_allclose(x[entorn], (1 - alfa) * relativa[entorn] + alfa * de_les_represes[entorn])
        assert x is not relativa


def test_amb_alfa_zero_o_sense_etiquetes_es_la_d_abans():
    rng = np.random.default_rng(1)
    relativa = rng.normal(size=(3000, 3))
    de_les_represes = np.full((3000, 3), np.nan)                 # fora de l'entorn no se'n sap res
    entorn = rp.entorn((Etiqueta(1000, 1100, "corner", H),), 3000, TOT)
    de_les_represes[entorn] = rng.normal(size=(entorn.sum(), 3))
    np.testing.assert_array_equal(rp.barreja(relativa, de_les_represes, entorn, 0.0), relativa)
    for alfa in rp.ALFES:
        np.testing.assert_array_equal(rp.barreja(relativa, de_les_represes, np.zeros(3000, dtype=bool), alfa), relativa)
    assert np.isfinite(rp.barreja(relativa, de_les_represes, entorn, 1.0)).all()


def test_la_graella_del_pla():
    assert rp.ALFES == (0.0, 0.25, 0.5, 0.75, 1.0)
    assert (rp.ABANS_S, rp.DESPRES_S) == (6, 10)
