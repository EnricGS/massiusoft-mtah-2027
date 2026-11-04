"""El banc de la T3ac: la D impossible exactament a les imatges netejades, el decodificador que no hi dona mai la D,
i que on la neteja no treu res tot surt igual."""

from __future__ import annotations

import numpy as np

from banc import model_a_canvis as t3i
from banc import model_neteja_aire as mna
from banc import sostre_curtes as sc
from cadena import decodifica_tocs as dt
from possessio.oficial import possession_metrics as pm

N = 300


def relativa(n: int, llavor: int) -> np.ndarray:
    return np.random.default_rng(llavor).normal(0.0, 3.0, (n, 3))


def test_la_d_impossible_exactament_on_s_ha_tret_la_pilota():
    r = relativa(N, 1)
    abans = r.copy()
    on = np.zeros(N, dtype=bool)
    on[[0, 7, 8, 9, 150, N - 1]] = True
    out = mna.amb_la_d_impossible(r, on)
    np.testing.assert_array_equal(r, abans)                              # la que rep, igual
    assert (out[on, dt.D] == -mna.IMPOSSIBLE).all()
    np.testing.assert_array_equal(out[on][:, [dt.H, dt.A]], r[on][:, [dt.H, dt.A]])    # l'H i l'A, com estaven
    np.testing.assert_array_equal(out[~on], r[~on])                      # la resta, igual


def decodifica(r: np.ndarray, d_min: int = 25) -> np.ndarray:
    """El decodificador amb la λ més alta de la graella: és quan costa més sortir de la D."""
    q = np.full(len(r), 0.5)
    return t3i.per_trams(r, q, ((1, 0, len(r) - 1),), w=8.0, lam=64.0, d_min=d_min)


def test_el_decodificador_no_hi_dona_mai_la_d():
    r = np.full((N, 3), -10.0)
    r[:, dt.D] = 10.0                                                    # la D, molt segura a tot arreu
    on = np.zeros(N, dtype=bool)
    on[[0, 5, 6, 7, 150, 290, N - 1]] = True                             # a les vores, a prop i al mig
    assert (decodifica(r) == pm.D).all()
    for d_min in (1, 12, 25):
        pred = decodifica(mna.amb_la_d_impossible(r, on), d_min)
        assert not (pred[on] == pm.D).any()
        assert (pred[~on] == pm.D).mean() > 0.6                          # la resta, encara D
    # amb −30, com als sostres, el decodificador encara hi posaria la D: per això aquí és molt més
    com_als_sostres = r.copy()
    com_als_sostres[on, dt.D] = -sc.SEGUR
    assert (decodifica(com_als_sostres)[150] == pm.D)


def test_on_la_neteja_no_treu_res_surt_igual():
    r = relativa(N, 2)
    cap = np.zeros(N, dtype=bool)
    np.testing.assert_array_equal(mna.amb_la_d_impossible(r, cap), r)
    np.testing.assert_array_equal(decodifica(mna.amb_la_d_impossible(r, cap), 12), decodifica(r, 12))


def test_la_d_de_la_veritat_que_es_perd():
    toc = np.array([pm.H, pm.D, pm.D, pm.A, pm.D, pm.X, pm.D, pm.H], dtype=np.int8)
    on = np.array([0, 1, 0, 1, 1, 1, 0, 0], dtype=bool)
    valides = np.array([1, 1, 1, 1, 1, 1, 1, 0], dtype=bool)
    assert mna.d_de_la_veritat(toc, on, valides) == {"netejades": 4, "d": 4, "d_netejades": 2}
    valides[4] = False
    assert mna.d_de_la_veritat(toc, on, valides) == {"netejades": 3, "d": 3, "d_netejades": 1}
