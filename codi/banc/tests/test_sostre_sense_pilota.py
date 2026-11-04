"""El sostre de les xarxes sense pilota: els encerts d'equip, el segon perfecte, l'equip encertat i segur, els
trossos, l'equip com on es veu la pilota i la taula dels forats."""

from __future__ import annotations

import numpy as np
import pandas as pd

from banc import sostre_sense_pilota as ssp
from possessio.oficial import possession_metrics as pm

SEGUR = ssp.SEGUR


def relativa(*files: tuple[float, float, float]) -> np.ndarray:
    return np.array(files, dtype=float)


def test_dins_marca_les_imatges_dels_trams():
    assert ssp.dins(8, [(1, 3), (5, 7)]).tolist() == [False, True, True, False, False, True, True, False]


def test_els_encerts_compten_nomes_on_la_veritat_es_d_un_equip_i_hi_ha_probabilitats():
    r = relativa((1, 0, 0), (0, 1, 0), (1, 0, 0), (np.nan, np.nan, np.nan), (0, 1, 5))
    toc = np.array([pm.H, pm.H, pm.D, pm.A, pm.A])
    tot = np.ones(5, dtype=bool)
    assert ssp.encerts(r, toc, tot) == (3, 2)           # la D i el NaN no compten; la D alta no hi fa res
    assert ssp.encerts(r, toc, np.array([False, True, True, True, False])) == (1, 0)
    assert ssp.encerts_pred(np.array([pm.H, pm.A, pm.D, pm.A, pm.D]), toc, tot) == (4, 2)


def test_el_segon_perfecte_nomes_toca_on_es_diu_i_on_la_veritat_no_es_x():
    r = relativa((1, 2, 3), (1, 2, 3), (1, 2, 3), (1, 2, 3))
    toc = np.array([pm.H, pm.D, pm.X, pm.A])
    out = ssp.perfecte(r, toc, np.array([True, True, True, False]))
    assert out.tolist() == [[SEGUR, -SEGUR, -SEGUR], [-SEGUR, -SEGUR, SEGUR], [1, 2, 3], [1, 2, 3]]
    assert r.tolist() == [[1, 2, 3]] * 4                # l'original, intacte


def test_l_equip_encertat_gira_l_h_i_l_a_on_s_equivoca_i_deixa_la_d():
    r = relativa((2, -1, 0.5), (-3, 1, 4), (-2, 1, 0), (0, 1, 0))
    toc = np.array([pm.A, pm.H, pm.A, pm.H])
    out = ssp.equip_encertat(r, toc, np.array([True, True, True, False]))
    assert out.tolist() == [[-1, 2, 0.5], [1, -3, 4], [-2, 1, 0], [0, 1, 0]]
    assert r[0].tolist() == [2, -1, 0.5]


def test_l_equip_segur_fa_impossible_l_altre_equip_i_deixa_la_d():
    r = relativa((2, -1, 0.5), (-2, 1, 0), (0, 1, 0))
    toc = np.array([pm.A, pm.A, pm.D])
    out = ssp.equip_segur(r, toc, np.ones(3, dtype=bool))
    assert out.tolist() == [[-SEGUR, 2, 0.5], [-SEGUR, 1, 0], [0, 1, 0]]


def test_els_trossos_seguits():
    assert ssp.trossos(np.array([1, 1, 0, 1, 0, 0, 1], dtype=bool)) == [(0, 2), (3, 4), (6, 7)]
    assert ssp.trossos(np.zeros(3, dtype=bool)) == []


def com_amb_pilota(r: np.ndarray, toc: np.ndarray, al_forat: np.ndarray, llavor: int = 0) -> np.ndarray:
    return ssp.com_amb_pilota(r, toc, al_forat, np.ones(len(toc), dtype=bool), np.random.default_rng(llavor))


def test_com_on_es_veu_la_pilota_gira_trossos_d_errors_fins_que_hi_arriba():
    # On es veu la pilota (les 10 primeres), encerta 8 de 10. Als forats (les 20 últimes), 10 de 20: cinc trossos
    # d'errors de 2.
    toc = np.full(30, pm.H)
    bona, dolenta = (1.0, -1.0, 0.0), (-1.0, 1.0, 0.0)
    r = relativa(*[bona] * 8, *[dolenta] * 2, *([bona] * 2 + [dolenta] * 2) * 5)
    al_forat = np.arange(30) >= 10
    out = com_amb_pilota(r, toc, al_forat)
    assert ssp.encerts(out, toc, al_forat) == (20, 16)        # 0,8 × 20: tres trossos girats, i prou
    assert np.array_equal(out[:10], r[:10])                   # on es veu la pilota, com estava
    assert np.array_equal(com_amb_pilota(r, toc, al_forat), out)
    meitat = ssp.com_amb_pilota(r, toc, al_forat, np.ones(30, dtype=bool), np.random.default_rng(0), part=0.5)
    assert ssp.encerts(meitat, toc, al_forat) == (20, 14)     # la meitat dels 6 que falten: dos trossos girats


def test_com_on_es_veu_la_pilota_no_toca_res_si_als_forats_ja_hi_encerta_tant():
    toc = np.full(20, pm.A)
    r = relativa(*[(1.0, -1.0, 0.0)] * 5, *[(-1.0, 1.0, 0.0)] * 15)
    al_forat = np.arange(20) >= 10
    assert np.array_equal(com_amb_pilota(r, toc, al_forat), r)


def test_la_taula_dels_forats():
    files = []
    for on, puntuades, n, e in ((ssp.AMB_PILOTA, 30, 20, 18), (ssp.ALS_FORATS, 10, 10, 6)):
        for qui in ssp.QUI:
            files.append({"partit": "p", "escenari": "net", "on": on, "qui": qui, "puntuades": puntuades, "n": n,
                          "encerts": e})
    t = ssp.taula_forats(pd.DataFrame(files))
    fila = t.loc["net"]
    assert fila["part als forats"] == 0.25
    assert fila[f"{ssp.SEGON_}, {ssp.AMB_PILOTA}"] == 0.9
    assert fila[f"{ssp.BASE}, {ssp.ALS_FORATS}"] == 0.6
    assert fila[f"errors d'{ssp.BASE} als forats"] == 4 / 6
