"""Els tocs dels esdeveniments de la T3u: els de Metrica, el que aprèn el detector a cada imatge i les imatges que
s'aprenen."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from banc import tocs_esdeveniments as te
from possessio.oficial import possession_metrics as pm

H, A, D = pm.H, pm.A, pm.D


def esdeveniment(tipus: str, inici: int, equip: str = "Home", subtipus: str = "", part: int = 1) -> dict:
    return {"team": equip, "type": tipus, "subtype": subtipus, "period": part, "start_frame": inici,
            "end_frame": inici + 10}


def test_els_tocs_de_metrica_son_a_l_inici_dels_que_diu_el_pla():
    events = pd.DataFrame([
        esdeveniment("PASS", 105), esdeveniment("RECOVERY", 130, "Away"), esdeveniment("CARRY", 120),
        esdeveniment("CHALLENGE", 140, "Away", "GROUND-WON"), esdeveniment("CHALLENGE", 141, "Home", "GROUND-LOST"),
        esdeveniment("CHALLENGE", 150, "Away", "FAULT-WON"), esdeveniment("CHALLENGE", 151, "Home", "ADVANTAGE-WON"),
        esdeveniment("FAULT RECEIVED", 152), esdeveniment("CARD", 153), esdeveniment("SET PIECE", 160, "Away"),
        esdeveniment("SHOT", 170), esdeveniment("BALL LOST", 180, "Away"), esdeveniment("BALL OUT", 190),
        esdeveniment("PASS", 310, "Away", part=2),
    ])
    frame = np.arange(100, 400)
    periode = np.where(frame < 300, 1, 2)
    assert te.de_metrica(events, frame, periode) == [(5, H), (20, H), (30, A), (40, A), (60, A), (70, H), (80, A),
                                                     (90, H), (210, A)]


def test_un_toc_de_metrica_sense_imatge_a_la_seva_part_atura():
    frame = np.arange(100, 400)
    periode = np.where(frame < 300, 1, 2)
    with pytest.raises(ValueError):
        te.de_metrica(pd.DataFrame([esdeveniment("PASS", 310, part=1)]), frame, periode)
    with pytest.raises(ValueError):
        te.de_metrica(pd.DataFrame([esdeveniment("PASS", 50)]), frame, periode)


def test_cada_toc_marca_tres_imatges_a_cada_banda_amb_el_seu_equip():
    y = te.etiquetes_de_toc(np.array([[10, H], [30, A]]), 40, ((1, 0, 39),))
    assert y[7:14].tolist() == [H] * 7 and y[27:34].tolist() == [A] * 7
    assert (np.delete(y, np.r_[7:14, 27:34]) == D).all()


def test_si_n_hi_ha_dos_a_prop_el_mes_proper_i_a_la_mateixa_distancia_el_primer():
    y = te.etiquetes_de_toc(np.array([[10, H], [14, A]]), 30, ((1, 0, 29),))
    assert y[7:18].tolist() == [H] * 6 + [A] * 5                  # 12: a 2 de tots dos, el primer (H)
    y = te.etiquetes_de_toc(np.array([[10, H], [13, A]]), 30, ((1, 0, 29),))
    assert y[11:13].tolist() == [H, A]


def test_mai_d_una_part_a_l_altra_i_fora_de_les_parts_res():
    trams = ((1, 0, 19), (2, 25, 44))
    y = te.etiquetes_de_toc(np.array([[18, A], [21, H], [26, H]]), 50, trams)
    assert y[15:20].tolist() == [A] * 5
    assert (y[20:25] == D).all()                                  # el de la fila 21 no és de cap part
    assert y[25:30].tolist() == [H] * 5 and (y[30:] == D).all()


def test_s_aprenen_tots_els_tocs_i_una_de_cada_32_de_la_resta():
    y = np.full(200, D, dtype=np.int8)
    y[50:57] = H
    y[150:157] = A
    f = te.files(y, [(0, 100), (120, 200)])
    toc = [*range(50, 57), *range(150, 157)]
    resta = [i for i in [*range(0, 100), *range(120, 200)] if i not in toc]
    assert f.tolist() == sorted(toc + resta[::32])


def test_dues_vegades_exactament_el_mateix():
    tocs = np.array([[5, H], [9, A], [40, A]])
    trams = ((1, 0, 30), (2, 31, 60))
    y = te.etiquetes_de_toc(tocs, 61, trams)
    np.testing.assert_array_equal(y, te.etiquetes_de_toc(tocs, 61, trams))
    np.testing.assert_array_equal(te.files(y, [(0, 31), (31, 61)]), te.files(y, [(0, 31), (31, 61)]))
