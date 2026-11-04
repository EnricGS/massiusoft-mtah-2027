"""El banc del pas 2 de la T3x: l'objectiu, el decodificador amb β = 0, amb què aprèn el model i com es tria la β."""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from banc import canvis_als_forats as caf
from banc import fonts
from banc import model_a_canvis as t3i
from banc import model_forats_curts as mfc
from banc import model_a_partit as mp
from cadena import forats_curts as fc
from possessio.oficial import possession_metrics as pm

H, A, D, X = caf.H, caf.A, caf.D, pm.X


def test_l_objectiu():
    assert mfc.objectiu(np.array([H, H, H, A, A, A]), 2, 3) == 1.0           # un canvi
    assert mfc.objectiu(np.full(6, H), 2, 3) == 0.0                          # cap
    assert mfc.objectiu(np.array([H, H, A, A, H, H]), 2, 3) == 1.0           # una possessió amagada
    assert mfc.objectiu(np.array([H, H, D, D, H, H]), 2, 3) == 0.0           # la D, amb el mateix equip
    assert mfc.objectiu(np.array([H, H, D, D, A, A]), 2, 3) == 1.0           # la D, amb canvi d'equip
    assert np.isnan(mfc.objectiu(np.array([H, D, D, D, X, A]), 2, 3))        # cap equip a les vores ni al mig


def test_amb_beta_0_el_decodificador_de_sempre():
    rng = np.random.default_rng(1)
    n = 400
    relativa = np.log(rng.dirichlet(np.ones(3), n))
    q = rng.uniform(0.01, 0.9, n)
    trams = ((1, 0, 199), (2, 210, 399))
    forats_ = np.array([[20, 30, 0, 199], [250, 260, 210, 399]])
    p = np.array([0.1, 0.9])
    abans = t3i.per_trams(relativa, q, trams, 4.0, 16.0, 12)
    np.testing.assert_array_equal(mfc.decodifica(relativa, q, trams, forats_, p, 0.2, 4.0, 16.0, 12, 0.0), abans)


def tots_fets() -> dict[tuple[str, str], dict]:
    """Uns forats fets per a cada partit i escenari: el desplaçament diu si hi ha canvi."""
    rng = np.random.default_rng(0)
    out = {}
    for i, (nom, e) in enumerate(itertools.product(fonts.NOMS, mp.ESCENARIS)):
        y = rng.integers(0, 2, 60).astype(float)
        y[:5] = np.nan
        x = pd.DataFrame({t: rng.random(60) for t in fc.TRETS})
        x["desplacament"] = y + rng.normal(0, 0.3, 60) + i * 1e-6
        out[(nom, e)] = {"partit": nom, "escenari": e, "forats": np.zeros((60, 4), int), "trets": x, "y": y}
    return out


def test_el_model_de_cada_partit_no_ha_apres_amb_ell(monkeypatch):
    tots, vist = tots_fets(), {}

    def train(params, data, num_boost_round):
        vist["x"], vist["y"] = data.data, data.label
        return "model"

    monkeypatch.setattr(mfc.lgb, "train", train)
    prova = fonts.NOMS[0]
    model, pi = mfc.entrena(prova, tots)
    esperat = [d for (nom, e), d in tots.items() if nom != prova and e in mp.SIS]
    assert model == "model" and len(vist["x"]) == sum(55 for _ in esperat) == len(vist["y"])
    np.testing.assert_allclose(pi, np.nanmean(np.concatenate([d["y"] for d in esperat])))
    propis = np.concatenate([tots[(prova, e)]["trets"]["desplacament"].to_numpy() for e in mp.ESCENARIS])
    assert not np.isin(vist["x"]["desplacament"].to_numpy(), propis).any()


def test_dues_vegades_el_mateix():
    tots, prova = tots_fets(), fonts.NOMS[1]
    x = tots[(prova, "curts ×¼")]["trets"]
    (m1, pi1), (m2, pi2) = mfc.entrena(prova, tots), mfc.entrena(prova, tots)
    np.testing.assert_array_equal(m1.predict(x), m2.predict(x))
    assert pi1 == pi2


def test_la_beta_es_tria_amb_els_altres_nou():
    files = []
    for nom, e, beta in itertools.product(fonts.NOMS, mp.ESCENARIS, mfc.BETES):
        bo = 2.0 if nom != fonts.NOMS[0] else 8.0              # el partit que es prova preferiria 8
        for veritat in (mfc.SEMPRE, mfc.TOC):
            files.append({"partit": nom, "escenari": e, "metode": mfc.A_FORATS, "veritat": veritat, "w": 4.0,
                          "lam": 16.0, "d_min": 12, "beta": beta, "spell_f1": 0.5 - 0.01 * abs(beta - bo),
                          "macro_f1": 0.5})
    triades_equips = {nom: (4.0, 16.0, 12) for nom in fonts.NOMS}
    triats, triades = mfc.tria_beta(pd.DataFrame(files), triades_equips)
    assert all(t == (4.0, 16.0, 12, 2.0) for t in triades.values())
    assert len(triats) == len(fonts.NOMS) * len(mp.ESCENARIS) * 2 and set(triats["beta"]) == {2.0}
