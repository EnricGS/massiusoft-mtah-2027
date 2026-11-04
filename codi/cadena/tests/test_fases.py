"""Les fases amb equip al decodificador (T3ak): les estones, i què es resta i on."""

from __future__ import annotations

import numpy as np

from cadena import decodifica_tocs as dt
from cadena import fases as fs
from cadena import smart_tagging as st
from possessio.oficial import possession_metrics as pm

H, A, D = pm.H, pm.A, pm.D
TRAMS = ((1, 0, 499), (2, 500, 999))
FPS = pm.FPS


def test_les_estones_amb_el_marge_i_dins_de_la_part():
    fases = (fs.Fase(100, 199, H), fs.Fase(450, 560, A), fs.Fase(1200, 1300, H))
    dins = fs.estones(fases, 1000, TRAMS, 1.0)
    np.testing.assert_array_equal(np.flatnonzero(dins[:, H]), np.arange(100 + FPS, 200 - FPS))
    np.testing.assert_array_equal(np.flatnonzero(dins[:, A]), np.arange(450 + FPS, 500 - FPS))
    sense_marge = fs.estones(fases, 1000, TRAMS, 0.0)
    np.testing.assert_array_equal(np.flatnonzero(sense_marge[:, A]), np.arange(450, 500))
    assert not fs.estones((fs.Fase(100, 130, H),), 1000, TRAMS, 1.0).any()      # més curta que els dos marges


def test_nomes_es_resta_a_l_altre_equip_i_a_la_d():
    rng = np.random.default_rng(0)
    relativa = rng.normal(size=(1000, 3))
    fases = (fs.Fase(100, 299, H), fs.Fase(600, 799, A))
    x = fs.resta(relativa, fases, TRAMS, 0.5, 0.25, 0.0)
    for k, (a, b) in ((H, (100, 300)), (A, (600, 800))):
        np.testing.assert_array_equal(x[a:b, k], relativa[a:b, k])
        np.testing.assert_allclose(x[a:b, 1 - k], relativa[a:b, 1 - k] - 0.5)
        np.testing.assert_allclose(x[a:b, D], relativa[a:b, D] - 0.25)
    fora = np.ones(1000, dtype=bool)
    fora[100:300] = fora[600:800] = False
    np.testing.assert_array_equal(x[fora], relativa[fora])
    assert dt.D == D


def test_dues_fases_a_la_mateixa_imatge():
    relativa = np.zeros((1000, 3))
    x = fs.resta(relativa, (fs.Fase(100, 299, H), fs.Fase(200, 399, H), fs.Fase(250, 349, A)), TRAMS, 1.0, 1.0, 0.0)
    np.testing.assert_array_equal(x[100:250, A], -1.0)                 # només una per equip
    np.testing.assert_array_equal(x[300:350, :], 0.0)                  # d'equips diferents: res
    np.testing.assert_array_equal(x[250:300, :], 0.0)
    np.testing.assert_array_equal(x[350:400, A], -1.0)


def test_amb_zeros_o_sense_fases_no_canvia_res():
    rng = np.random.default_rng(1)
    relativa = rng.normal(size=(1000, 3))
    fases = (fs.Fase(100, 299, H),)
    for x in (fs.resta(relativa, fases, TRAMS, 0.0, 0.0, 1.0), fs.resta(relativa, (), TRAMS, 0.5, 0.5, 1.0)):
        np.testing.assert_array_equal(x, relativa)
        assert x is not relativa


def test_girant_els_equips_dona_el_mateix_girat():
    rng = np.random.default_rng(2)
    relativa = rng.normal(size=(1000, 3))
    fases = (fs.Fase(100, 299, H), fs.Fase(320, 480, A), fs.Fase(700, 900, H))
    girades = tuple(f._replace(equip=1 - f.equip) for f in fases)
    a = fs.resta(relativa, fases, TRAMS, 0.25, 1.0, 1.0)
    b = fs.resta(relativa[:, [A, H, D]], girades, TRAMS, 0.25, 1.0, 1.0)
    np.testing.assert_array_equal(a, b[:, [A, H, D]])


def test_les_fases_que_diuen_l_equip_que_te_la_pilota():
    assert set(fs.CODIS) == {"build up", "progression", "creating chances", "ball in final third", "ball in the box",
                             "attacking transition"}
    assert not any(c.startswith("defending") or c == "defensive transition" for c in fs.CODIS)
    assert set(fs.CODIS) <= st.CODIS
