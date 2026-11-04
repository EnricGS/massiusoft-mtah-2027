"""El banc de la T3aa: la mitjana dels dos segons, que s'atura si el prior o la q no són els mateixos, i que amb dos
segons iguals és exactament A equips sencers."""

from __future__ import annotations

import numpy as np
import pytest

from banc import model_dos_segons as mds
from banc.tests import sintetic

PRIOR = np.array([0.3, 0.3, 0.4])


def probabilitats(n: int, llavor: int) -> np.ndarray:
    return np.random.default_rng(llavor).dirichlet(np.ones(3), n).astype(np.float32)


def model(n: int, llavor: int, prior: np.ndarray = PRIOR) -> tuple[dict, np.ndarray, dict]:
    rng = np.random.default_rng(100 + llavor)
    probes = {e: probabilitats(n, llavor + k) for k, e in enumerate(mds.ESCENARIS)}
    q = {e: rng.uniform(0, 1, n).astype(np.float32) for e in mds.ESCENARIS}
    return probes, prior, q


def test_la_mitjana_de_les_probabilitats():
    un, altre = probabilitats(500, 1), probabilitats(500, 2)
    m = mds.mitjana(un, altre)
    np.testing.assert_allclose(m, (un.astype(float) + altre.astype(float)) / 2, rtol=0, atol=0)
    np.testing.assert_allclose(m.sum(axis=1), 1.0, atol=1e-6)
    np.testing.assert_array_equal(mds.mitjana(un, un), un.astype(float))
    with pytest.raises(ValueError):
        mds.mitjana(un, altre[:-1])


def test_s_atura_si_el_prior_o_la_q_no_son_els_mateixos(monkeypatch):
    equips = model(300, 1)
    altre_prior = model(300, 2, prior=np.array([0.31, 0.31, 0.38]))
    altra_q = (model(300, 2)[0], PRIOR, {**equips[2], mds.ESCENARIS[-1]: equips[2][mds.ESCENARIS[-1]] * 0.5})
    for canvis in (altre_prior, altra_q):
        monkeypatch.setattr(mds.mmc, "de_qui", lambda metode, nom, c=canvis: equips if metode == mds.A_EQUIPS else c)
        with pytest.raises(RuntimeError):
            mds.de_qui(mds.A_DOS, "u")
    canvis = (model(300, 2)[0], PRIOR.copy(), {e: v.copy() for e, v in equips[2].items()})
    monkeypatch.setattr(mds.mmc, "de_qui", lambda metode, nom: equips if metode == mds.A_EQUIPS else canvis)
    probes, prior, q = mds.de_qui(mds.A_DOS, "u")
    np.testing.assert_array_equal(prior, PRIOR)
    assert q is equips[2]
    for e in mds.ESCENARIS:
        np.testing.assert_array_equal(probes[e], mds.mitjana(equips[0][e], canvis[0][e]))


def test_amb_dos_segons_iguals_es_exactament_a_equips_sencers(monkeypatch):
    p = sintetic.partit(n=1500, llavor=3)
    equips = model(len(p.veritat), 1)
    monkeypatch.setattr(mds.mmc, "de_qui", lambda metode, nom: equips)
    monkeypatch.setattr(mds.mp, "degradat", lambda nom, e: p)
    monkeypatch.setattr(mds.vt, "veritat", lambda nom: p.veritat)
    escenari = mds.ESCENARIS[3]
    files = mds.graella(("u", escenari, (mds.A_EQUIPS, mds.A_DOS)))
    de = {m: [(f["veritat"], f["w"], f["lam"], f["d_min"], f["spell_f1"], f["macro_f1"])
              for f in files if f["metode"] == m] for m in (mds.A_EQUIPS, mds.A_DOS)}
    assert len(de[mds.A_DOS]) == 2 * len(mds.t3j.WS) * len(mds.t3j.LAMS) * len(mds.t3j.DMINS)
    assert de[mds.A_DOS] == de[mds.A_EQUIPS]
