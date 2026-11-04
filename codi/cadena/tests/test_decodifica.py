"""El decodificador per trams: X fora de les parts, cada part pel seu compte i menys canvis com més penalització."""

from __future__ import annotations

import numpy as np

from cadena import decodifica
from possessio.oficial import possession_metrics as pm

TRAMS = ((1, 10, 109), (2, 110, 189))
PRIOR = np.array([0.4, 0.4, 0.2])


def probabilitats(llavor: int = 3) -> np.ndarray:
    rng = np.random.default_rng(llavor)
    p = rng.dirichlet([1, 1, 1], 200)
    p[30:70] = [0.7, 0.2, 0.1]
    return p


def canvis(codis: np.ndarray) -> int:
    return int((np.diff(codis[10:190]) != 0).sum())


def test_fora_de_les_parts_es_x_i_dins_mai():
    out = decodifica.per_trams(probabilitats(), PRIOR, TRAMS, lam=4)
    assert (out[:10] == pm.X).all() and (out[190:] == pm.X).all()
    assert set(np.unique(out[10:190]).tolist()) <= {pm.H, pm.A, pm.D}


def test_sense_penalitzacio_es_la_mes_probable_relativa_al_prior():
    p = probabilitats()
    out = decodifica.per_trams(p, PRIOR, TRAMS, lam=0)
    np.testing.assert_array_equal(out[10:190], (p / PRIOR).argmax(axis=1)[10:190])


def test_com_mes_penalitzacio_menys_canvis():
    p = probabilitats()
    n = [canvis(decodifica.per_trams(p, PRIOR, TRAMS, lam=lam)) for lam in (0, 2, 8, 1000)]
    assert n == sorted(n, reverse=True) and n[-1] <= 1


def test_cada_part_pel_seu_compte():
    p, q = probabilitats(), probabilitats()
    q[110:] = [0.1, 0.1, 0.8]
    a, b = (decodifica.per_trams(x, PRIOR, TRAMS, lam=8) for x in (p, q))
    np.testing.assert_array_equal(a[:110], b[:110])
    assert (b[110:190] == pm.D).all()


def test_la_durada_minima():
    p = probabilitats()
    out = decodifica.per_trams(p, PRIOR, TRAMS, lam=1, d_min=12)
    for _, inici, fi in TRAMS:
        tros = out[inici:fi + 1]
        vores = np.flatnonzero(np.diff(tros)) + 1
        llargades = np.diff(np.r_[0, vores, len(tros)])
        assert (llargades[1:-1] >= 12).all()
