"""El decodificador d'A xarxes a la cadena: el de la T3i al banc, tal qual, i els seus costos."""

from __future__ import annotations

import numpy as np
import pytest

from banc import model_a_canvis as t3i
from cadena import decodifica_canvis
from cadena import decodifica_tocs as dt
from possessio.oficial import possession_metrics as pm


@pytest.mark.parametrize(("w", "lam", "d_min"), [(4.0, 32.0, 12), (1.0, 4.0, 1), (8.0, 64.0, 25)])
def test_fa_el_mateix_que_el_del_banc(w, lam, d_min):
    rng = np.random.default_rng(int(w * lam + d_min))
    n = 3000
    relativa = np.log(rng.dirichlet((0.5, 0.5, 0.5), n) + 1e-6) - np.log(1 / 3)
    q = rng.beta(0.3, 3.0, n)
    trams = ((1, 100, 1399), (2, 1600, 2899))
    np.testing.assert_array_equal(decodifica_canvis.per_trams(relativa, q, trams, w, lam, d_min),
                                  t3i.per_trams(relativa, q, trams, w, lam, d_min))
    np.testing.assert_array_equal(decodifica_canvis.costos(q, lam, w), t3i.costos(q, lam, w))
    assert decodifica_canvis.Q_MINIM == t3i.Q_MINIM


def test_els_costos():
    cost = decodifica_canvis.costos(np.array([1.0, np.exp(-1), 0.0]), lam=16.0, w=4.0)
    np.testing.assert_allclose(cost[:, dt.H, dt.A], [0.0, 4.0, -4 * np.log(decodifica_canvis.Q_MINIM)])
    np.testing.assert_array_equal(cost[:, dt.A, dt.H], cost[:, dt.H, dt.A])
    for i, j in ((dt.H, dt.D), (dt.D, dt.H), (dt.A, dt.D), (dt.D, dt.A)):
        assert (cost[:, i, j] == 16.0).all()


def test_on_el_canvi_es_probable_hi_canvia_i_fora_de_les_parts_x():
    """Les probabilitats diuen H i després A, amb un tros d'indecís entremig: el canvi va on la q és alta."""
    n = 400
    relativa = np.zeros((n, 3))
    relativa[:150, dt.H] = relativa[250:, dt.A] = 1.0
    q = np.full(n, 0.01)
    q[220] = 0.9
    out = decodifica_canvis.per_trams(relativa, q, ((1, 10, 389),), w=4.0, lam=32.0, d_min=12)
    assert (out[:10] == pm.X).all() and (out[390:] == pm.X).all()
    assert (out[10:220] == pm.H).all() and (out[220:390] == pm.A).all()
