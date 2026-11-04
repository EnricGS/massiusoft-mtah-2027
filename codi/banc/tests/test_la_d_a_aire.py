"""D'on surt la D d'aire ×¼: la distància fora del camp, als forats, els comptes i la taula."""

from __future__ import annotations

import numpy as np
import pandas as pd

from banc import la_d_a_aire as lda
from possessio.oficial import possession_metrics as pm

H, A, D = pm.H, pm.A, pm.D
CAMP = np.array([105.0, 68.0])


def test_a_quants_metres_de_la_linia():
    pilota = np.array([[50.0, 30.0], [-3.0, 30.0], [110.0, 72.0], [50.0, 168.0], [np.nan, np.nan]])
    out = lda.fora_del_camp(pilota, CAMP)
    np.testing.assert_allclose(out[:4], [0.0, 3.0, np.hypot(5, 4), 100.0])
    assert np.isnan(out[4])


def test_als_forats_la_mes_lluny_de_la_d_abans_i_la_de_despres():
    fora = np.array([np.nan, 0.0, 30.0, np.nan, np.nan, 2.0, np.nan])
    out = lda.amb_els_forats(fora)
    np.testing.assert_array_equal(out[1:], [0.0, 30.0, 30.0, 30.0, 2.0, 2.0])
    assert out[0] == 0.0                                 # només n'hi ha una de després


def test_els_comptes_per_on_veritat_i_distancia():
    toc = np.array([H, H, A, D, H])
    pred = np.array([H, D, D, D, H])
    vista = np.array([True, False, False, True, True])
    distancia = np.array([0.0, 60.0, 60.0, 3.0, np.nan])
    relativa = np.array([[1.0, 0, 0], [0, 0, 1], [0, 1, 0], [0, 0, 1], [1, 0, 0]])
    c = lda.comptes(pred, toc, relativa, vista, distancia, np.ones(5, dtype=bool))
    files = {(r.on, r.veritat, r.distancia): (r.n, r.d, r.segon_d) for r in c.itertuples()}
    assert files == {(lda.ES_VEU, lda.D_UN_EQUIP, lda.NOMS[0]): (1, 0, 0),
                     (lda.AL_FORAT, lda.D_UN_EQUIP, lda.NOMS[3]): (2, 2, 1),
                     (lda.ES_VEU, lda.LA_D, lda.NOMS[1]): (1, 1, 1),
                     (lda.ES_VEU, lda.D_UN_EQUIP, lda.CAP): (1, 0, 0)}


def test_la_taula():
    c = pd.DataFrame([
        {"escenari": "aire ×¼", "on": lda.AL_FORAT, "veritat": lda.D_UN_EQUIP, "distancia": lda.NOMS[3], "n": 20, "d": 10,
         "segon_d": 12},
        {"escenari": "aire ×¼", "on": lda.AL_FORAT, "veritat": lda.D_UN_EQUIP, "distancia": lda.NOMS[0], "n": 30, "d": 0,
         "segon_d": 0},
        {"escenari": "aire ×¼", "on": lda.ES_VEU, "veritat": lda.D_UN_EQUIP, "distancia": lda.NOMS[0], "n": 50, "d": 10,
         "segon_d": 5},
        {"escenari": "aire ×¼", "on": lda.ES_VEU, "veritat": lda.LA_D, "distancia": lda.NOMS[1], "n": 40, "d": 40,
         "segon_d": 40}])
    t = lda.taula(c, lda.AL_FORAT)
    assert list(t.index) == [("aire ×¼", lda.NOMS[0]), ("aire ×¼", lda.NOMS[3])]
    assert t.loc[("aire ×¼", lda.NOMS[3])].tolist() == [0.2, 0.0, 0.5, 0.6, 0.5]
