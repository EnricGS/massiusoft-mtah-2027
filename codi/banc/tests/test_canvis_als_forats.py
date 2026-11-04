"""Els canvis d'equip dins dels forats: els forats, de quin és cada imatge, el tipus pel que amaga la veritat, què hi
fa la predicció, i els senyals del moment del canvi."""

from __future__ import annotations

import numpy as np
import pandas as pd

from banc import canvis_als_forats as caf
from possessio.oficial import possession_metrics as pm

H, A, D, X = pm.H, pm.A, pm.D, pm.X
K = caf.K


def test_els_forats_no_passen_d_una_part_a_l_altra():
    vista = np.ones(40, dtype=bool)
    vista[[0, 1, 5, 6, 7, 19, 20, 21, 39]] = False
    parts = ((1, 0, 19), (2, 20, 39))
    assert caf.forats(vista, parts) == [(0, 1, 0, 19), (5, 7, 0, 19), (19, 19, 0, 19), (20, 21, 20, 39),
                                        (39, 39, 20, 39)]


def test_cada_imatge_al_forat_mes_proper():
    n = 60
    forats_ = [(10, 12, 0, n - 1), (22, 25, 0, n - 1)]
    al_forat = np.zeros(n, dtype=bool)
    al_forat[10 - K:26 + K] = True
    qui = caf.de_quin_forat(n, forats_, al_forat)
    assert qui[10 - K] == 0 and qui[12 + 4] == 0 and qui[12 + 6] == 1 and qui[25 + K] == 1
    assert qui[12 + 5] == 0                                             # a la mateixa distància, el d'abans
    assert qui[10 - K - 1] == -1 and (qui[~al_forat] == -1).all()
    assert caf.de_quin_forat(n, [], al_forat).tolist() == [-1] * n


def test_el_tipus_pel_que_amaga_la_veritat():
    assert caf.tipus(np.array([H, H, H, X])) == caf.SENSE
    assert caf.tipus(np.array([H, H, A, A])) == caf.UN
    assert caf.tipus(np.array([H, A, A, H])) == caf.AMAGADA
    assert caf.tipus(np.array([H, A, H, A])) == caf.ALTRES
    assert caf.tipus(np.array([H, D, A])) == caf.ALTRES
    assert caf.tipus(np.array([X, X])) == ""


def test_que_hi_fa_la_prediccio():
    assert caf.que_fa(np.array([H, H, A, A]), H, A) == (caf.FA_EL_CANVI, 2)
    assert caf.que_fa(np.array([H, H, H, H]), H, A) == (caf.EL_D_ABANS, -1)
    assert caf.que_fa(np.array([A, A, A, A]), H, A) == (caf.EL_NOU, -1)
    assert caf.que_fa(np.array([H, D, A, A]), H, A) == (caf.ALTRA_COSA, -1)
    assert caf.que_fa(np.array([H, A, H, A]), H, A) == (caf.ALTRA_COSA, -1)


def test_on_canvia_el_segon():
    relativa = np.array([[1.0, 0, -5], [0.5, 0, -5], [0, 0.2, -5], [-1, 1, -5]])
    assert caf.on_canvia_el_segon(relativa, H, A) == 2
    assert caf.on_canvia_el_segon(relativa[:2], H, A) == 2              # no hi canvia: al final
    assert caf.on_canvia_el_segon(relativa[[3, 0]], H, A) == 0


def test_la_distancia_del_mes_proper():
    pilota = np.array([[0.0, 0.0], [10.0, 0.0], [np.nan, np.nan]])
    jugadors = np.array([[[3.0, 4.0], [np.nan, np.nan]], [[10.0, 1.0], [12.0, 0.0]], [[1.0, 1.0], [2.0, 2.0]]])
    d = caf.mes_proper(jugadors, pilota)
    np.testing.assert_allclose(d[:2], [5.0, 1.0])
    assert np.isinf(d[2])
    assert np.isinf(caf.mes_proper(np.full((1, 2, 2), np.nan), np.zeros((1, 2))))[0]


def test_on_cau_el_canvi_i_els_errors_de_temps():
    assert caf.quart(10, 10, 13) == caf.QUARTS_DEL_FORAT[0]
    assert caf.quart(13, 10, 13) == caf.QUARTS_DEL_FORAT[3]
    assert caf.quart(14, 10, 13) == caf.QUARTS_DEL_FORAT[3]               # a la primera imatge amb pilota
    assert caf.quart(12, 10, 13) == caf.QUARTS_DEL_FORAT[2]
    errors = np.array([0.0, 0.4, -0.9, 1.5, 3.0, np.nan])
    t = caf.temps(errors)
    assert t == {"a 0,5 s o menys": 2 / 5, "a 1 s o menys": 3 / 5, "mediana (s)": 0.9, "abans": 1 / 5,
                 "n forats": 5}


def test_les_parts_per_durada_i_a_tots():
    canvis = pd.DataFrame({"escenari": ["curts ×¼"] * 3, "durada": ["<2 s", "<2 s", "≥5 s"],
                           "quart": [caf.QUARTS_DEL_FORAT[0], caf.QUARTS_DEL_FORAT[3], caf.QUARTS_DEL_FORAT[3]]})
    t = caf.parts_de(canvis, "quart", caf.QUARTS_DEL_FORAT)
    assert list(t.index) == [("curts ×¼", "<2 s"), ("curts ×¼", "≥5 s"), ("curts ×¼", caf.TOTS)]
    assert t.loc[("curts ×¼", "<2 s")].tolist() == [2, 0.5, 0.0, 0.0, 0.5]
    np.testing.assert_allclose(t.loc[("curts ×¼", caf.TOTS)].tolist(), [3, 1 / 3, 0, 0, 2 / 3])


def test_que_hi_fa_la_prediccio_sense_canvi():
    assert caf.que_fa_sense(np.array([H, H, H]), H) == caf.NO_CANVIA
    assert caf.que_fa_sense(np.array([H, A, A, H]), H) == caf.INVENTA
    assert caf.que_fa_sense(np.array([H, H, A]), H) == caf.CANVIA
    assert caf.que_fa_sense(np.array([A, A, H]), H) == caf.CANVIA
    assert caf.que_fa_sense(np.array([H, D, H]), H) == caf.POSA_LA_D
    assert caf.que_fa_sense(np.array([A, H, A, H]), H) == caf.ALTRA_COSA
    assert caf.errors_del_tros(np.array([H, H, X, A]), np.array([H, A, A, D])) == 2
