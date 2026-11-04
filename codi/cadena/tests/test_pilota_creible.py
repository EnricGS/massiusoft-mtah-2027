"""La pilota que no pot ser (T3w): a quants metres de la línia és, i la neteja, que no toca res més."""

from __future__ import annotations

import numpy as np

from banc.tests import sintetic
from cadena import pilota_creible as pc
from cadena.llegeix import Tracking

CAMP = (105.0, 68.0)
NAN = np.nan


def tracking(pilota_m: list[tuple[float, float]]) -> Tracking:
    """Un tracking amb la pilota on es diu (en metres) i dos jugadors per equip."""
    n = len(pilota_m)
    rng = np.random.default_rng(0)
    return Tracking(fotograma=np.arange(n), pilota=np.array(pilota_m, float) / np.array(CAMP),
                    casa=rng.random((n, 2, 2)), fora=rng.random((n, 2, 2)), nom_casa="H", nom_fora="A",
                    casa_es_home=True, camp_m=CAMP)


def test_a_quants_metres_de_la_linia():
    t = tracking([(50, 30), (0, 0), (105, 68), (-3, 30), (110, 30), (50, -4), (50, 80), (-6, -8), (109, 71),
                  (NAN, NAN)])
    fora = pc.fora_del_camp(t.pilota, t.camp_m)
    np.testing.assert_allclose(fora[:9], [0, 0, 0, 3, 5, 4, 12, 10, 5], atol=1e-9)
    assert np.isnan(fora[9])


def test_la_neteja_nomes_treu_la_pilota_a_10_m_o_mes():
    t = tracking([(50, 30), (-9.9, 30), (-10, 30), (50, 90), (NAN, NAN), (115.5, 30)])
    abans = {k: getattr(t, k).copy() for k in ("pilota", "casa", "fora")}
    net = pc.neteja(t)
    assert pc.lluny(t).tolist() == [False, False, True, True, False, True]
    assert np.isnan(net.pilota[[2, 3, 4, 5]]).all()
    np.testing.assert_array_equal(net.pilota[[0, 1]], t.pilota[[0, 1]])
    for k, v in abans.items():
        np.testing.assert_array_equal(getattr(t, k), v)                    # el que rep, igual
    np.testing.assert_array_equal(net.casa, t.casa)
    np.testing.assert_array_equal(net.fora, t.fora)
    assert (net.fotograma is t.fotograma and net.camp_m == t.camp_m and net.nom_casa == t.nom_casa
            and net.casa_es_home == t.casa_es_home)


def test_un_partit_sense_cap_pilota_tan_lluny_surt_identic():
    p = sintetic.partit(n=600)
    assert not pc.lluny(p.tracking).any()
    net = pc.neteja(p.tracking)
    for k in ("fotograma", "pilota", "casa", "fora"):
        np.testing.assert_array_equal(getattr(net, k), getattr(p.tracking, k))
