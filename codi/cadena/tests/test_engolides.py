"""El detector d'engolides (T3aj): les seves columnes, que es diuen respecte de l'equip predit, i com se suma a la
probabilitat relativa."""

from __future__ import annotations

import inspect

import numpy as np
import pandas as pd

from cadena import engolides as eg
from cadena.llegeix import Tracking
from possessio.oficial import possession_metrics as pm

H, A, D = pm.H, pm.A, pm.D
CAMP = (105.0, 68.0)


def tracking(pilota_m: np.ndarray, casa_m: np.ndarray, fora_m: np.ndarray) -> Tracking:
    escala = np.asarray(CAMP)
    return Tracking(np.arange(len(pilota_m)), pilota_m / escala, casa_m / escala, fora_m / escala, "H", "A", True, CAMP)


def a_l_atzar(n: int = 600, llavor: int = 0) -> tuple:
    rng = np.random.default_rng(llavor)
    pilota = np.cumsum(rng.normal(0, 0.4, (n, 2)), axis=0) + [50.0, 34.0]
    pilota[rng.random(n) < 0.3] = np.nan
    casa, fora = pilota[:, None, :] + rng.normal(0, 3, (n, 4, 2)), pilota[:, None, :] + rng.normal(0, 3, (n, 4, 2))
    pred = np.repeat(rng.choice([H, A, D], size=n // 20), 20).astype(np.int8)
    return tracking(pilota, casa, fora), rng.normal(size=(n, 3)), rng.random(n), pred


def test_girant_els_equips_les_columnes_son_les_mateixes():
    t, relativa, q, pred = a_l_atzar()
    trams = [(0, len(pred))]
    girat = tracking(t.pilota * CAMP, t.fora * CAMP, t.casa * CAMP)
    gira = np.array([A, H, D, pm.X], dtype=np.int8)
    a, b = eg.columnes(t, relativa, q, pred, trams), eg.columnes(girat, relativa[:, [A, H, D]], q, gira[pred], trams)
    pd.testing.assert_frame_equal(a, b)
    assert list(a.columns) == list(eg.COLUMNES)
    assert "veritat" not in inspect.signature(eg.columnes).parameters


def test_les_possessions_predites():
    pred = np.array([D, D, H, H, H, D, A, A, D, H], dtype=np.int8)
    equip, des, fins, durada = eg.possessions(pred, [(0, 5), (5, 10)])
    np.testing.assert_array_equal(equip, [-1, -1, H, H, H, -1, A, A, -1, H])
    np.testing.assert_array_equal(des[2:5], [0, 1, 2])
    np.testing.assert_array_equal(fins[2:5], [2, 1, 0])
    np.testing.assert_array_equal(durada[[2, 6, 9]], [3, 2, 1])
    assert np.isnan(des[[0, 1, 5, 8]]).all()


def test_sense_pilota():
    des, fins = eg.sense_pilota(np.array([True, False, False, True, False]))
    np.testing.assert_array_equal(des, [0, 1, 2, 0, 1])
    np.testing.assert_array_equal(fins, [0, 2, 1, 0, eg.TOPALL])


def test_les_peces_del_toc():
    n = 100
    x = 50.0 - 0.4 * np.abs(np.arange(n) - 50)                 # a 10 m/s, i tomba a la imatge 50
    pilota = np.stack([x, np.full(n, 34.0)], axis=1)
    pilota[80:] = np.nan
    t = tracking(pilota, np.tile([[[50.0, 50.0]]], (n, 1, 1)), np.tile([[[50.0, 34.0]]], (n, 1, 1)))
    canvi, dist = eg.peces(t)
    np.testing.assert_allclose(canvi[50], 20.0)
    np.testing.assert_allclose(canvi[40], 0.0, atol=1e-9)
    np.testing.assert_allclose(dist[50], [16.0, 0.0], atol=1e-9)
    assert np.isnan(canvi[85]) and np.isnan(dist[85]).all()


def test_nomes_suma_dins_i_a_l_altre_equip():
    rng = np.random.default_rng(1)
    relativa = rng.normal(size=(50, 3))
    relativa[10:20, D] = -1e6                                  # la D impossible d'on s'ha netejat la pilota
    p = rng.random(50)
    equip = np.repeat(np.array([-1, H, A, -1, H], dtype=np.int8), 10)
    x = eg.suma(relativa, p, equip, 0.5)
    fora = equip < 0
    np.testing.assert_array_equal(x[fora], relativa[fora])
    np.testing.assert_array_equal(x[:, D], relativa[:, D])
    logit = np.log(p / (1 - p))
    for k in (H, A):
        dins = equip == k
        np.testing.assert_array_equal(x[dins, k], relativa[dins, k])
        np.testing.assert_allclose(x[dins, 1 - k], relativa[dins, 1 - k] + 0.5 * logit[dins])


def test_amb_beta_zero_no_canvia_res():
    rng = np.random.default_rng(2)
    relativa, p = rng.normal(size=(50, 3)), rng.random(50)
    equip = np.repeat(np.array([H, A, -1, H, A], dtype=np.int8), 10)
    x = eg.suma(relativa, p, equip, 0.0)
    np.testing.assert_array_equal(x, relativa)
    assert x is not relativa
