"""El decodificador amb tocs (T3): els candidats, els costos i el Viterbi amb el cost de cada imatge."""

from __future__ import annotations

import math

import numpy as np
import pytest

from cadena import decodifica_tocs as dt
from cadena.tocs import Tocs
from possessio.decodificacio import _viterbi_durada_minima
from possessio.oficial import possession_metrics as pm


def tocs(imatges: list[int], equips: list[int]) -> Tocs:
    m = len(imatges)
    return Tocs(imatge=np.array(imatges, int), equip=np.array(equips, np.int8), propi_m=np.zeros(m),
                altre_m=np.full(m, np.inf), canvi_ms=np.full(m, 10.0))


@pytest.mark.parametrize("d", [1, 5, 25])
@pytest.mark.parametrize("lam", [2.0, 8.0])
def test_amb_costos_iguals_fa_el_mateix_cami_que_el_d_a(d, lam):
    rng = np.random.default_rng(d)
    em = rng.normal(0, 1, (600, 3)).cumsum(axis=0) / 20 + rng.normal(0, 1, (600, 3))
    cost = np.full((600, 3, 3), lam)
    np.testing.assert_array_equal(dt.viterbi(em, cost, d), _viterbi_durada_minima(em, lam, d))


def test_l_ultim_tram_pot_ser_curt():
    em = np.zeros((40, 3))
    em[:, dt.H] = 1.0
    em[-3:, dt.A] = 5.0                      # les tres últimes, clarament A
    cami = dt.viterbi(em, np.full((40, 3, 3), 1.0), 25)
    assert (cami[:-3] == dt.H).all() and (cami[-3:] == dt.A).all()


def test_canvia_al_toc_si_amb_la_pilota_visible_no_pot():
    n = 200
    em = np.zeros((n, 3))
    em[:100, dt.H], em[100:, dt.A] = 0.3, 0.3          # la proximitat diu que canvia a la 100
    par = dt.Parametres(control=1, lam_vis=math.inf, lam=8.0, d_min=1)
    cost = dt.costos(np.ones(n, bool), np.array([120]), np.array([pm.A], np.int8), par)
    cami = dt.viterbi(em, cost, par.d_min)
    assert (cami[:120] == dt.H).all() and (cami[120:] == dt.A).all()


def test_dins_d_un_forat_mana_la_proximitat():
    n = 200
    em = np.zeros((n, 3))
    em[:100, dt.H], em[100:, dt.A] = 0.5, 0.5
    visible = np.ones(n, bool)
    visible[80:130] = False                             # el canvi cau dins del forat
    par = dt.Parametres(control=1, lam_vis=math.inf, lam=2.0, d_min=1)
    cami = dt.viterbi(em, dt.costos(visible, np.array([], int), np.array([], np.int8), par), 1)
    assert cami[99] == dt.H and cami[100] == dt.A


def test_els_candidats_son_el_primer_toc_de_cada_serie():
    t = tocs([10, 20, 30, 40, 50, 60, 70], [pm.H, pm.H, pm.A, pm.H, pm.A, pm.A, pm.A])
    trams = ((1, 0, 99),)
    i, e = dt.candidats(t, trams, 1)
    assert i.tolist() == [10, 30, 40, 50] and e.tolist() == [pm.H, pm.A, pm.H, pm.A]
    i, e = dt.candidats(t, trams, 2)
    assert i.tolist() == [10, 50] and e.tolist() == [pm.H, pm.A]           # el 30 i el 40, un toc i prou


def test_cap_serie_passa_d_una_part_a_l_altra():
    t = tocs([10, 20, 110, 120], [pm.H, pm.H, pm.H, pm.H])
    i, _ = dt.candidats(t, ((1, 0, 99), (2, 100, 199)), 2)
    assert i.tolist() == [10, 110]


def test_els_costos():
    par = dt.Parametres(lam_vis=64.0, lam=8.0)
    visible = np.array([True, False, True, True])
    c = dt.costos(visible, np.array([3]), np.array([pm.A], np.int8), par)
    assert c[0, dt.H, dt.A] == 64.0 and c[1, dt.H, dt.A] == 8.0 and c[0, dt.H, dt.D] == 8.0
    assert c[3, dt.H, dt.A] == 0.0 and c[3, dt.D, dt.A] == 0.0 and c[3, dt.A, dt.H] == 64.0
    assert c[2, dt.D, dt.H] == 8.0


def test_fora_de_les_parts_es_x():
    n = 60
    proba = np.full((n, 3), 1 / 3)
    proba[:, 0] = 0.6
    proba /= proba.sum(axis=1, keepdims=True)
    out = dt.per_trams(proba, np.full(3, 1 / 3), ((1, 10, 29), (2, 30, 49)), np.ones(n, bool), tocs([], []),
                       dt.Parametres(d_min=1))
    assert (out[:10] == pm.X).all() and (out[50:] == pm.X).all() and (out[10:50] == pm.H).all()
