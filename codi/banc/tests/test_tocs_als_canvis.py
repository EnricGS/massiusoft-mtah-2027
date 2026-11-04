"""Què troba el detector de tocs als canvis d'equip: els canvis, el que troba, com és el toc i la taula."""

from __future__ import annotations

import numpy as np
import pandas as pd

from banc import tocs_als_canvis as tac
from possessio.oficial import possession_metrics as pm


def etiqueta(*trossos: tuple[int, int]) -> np.ndarray:
    return np.concatenate([np.full(n, codi, dtype=np.int8) for codi, n in trossos])


def test_els_canvis_venen_de_l_altre_equip_amb_la_pilota_a_la_vista():
    toc = etiqueta((pm.H, 10), (pm.A, 10), (pm.D, 5), (pm.A, 10), (pm.H, 10))
    forat = np.zeros(45, dtype=bool)
    forat[35] = True
    assert tac.canvis(toc, [(0, 45)], forat) == [(10, 20, pm.A)]


def test_que_troba_el_detector():
    imatges, equips = np.array([5, 30]), np.array([pm.A, pm.H])
    assert [tac.trobat(imatges, equips, a, pm.A) for a in (10, 40, 100)] == [tac.BO, tac.D_ABANS, tac.CAP]


def posicions(d_casa: float, d_fora: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    pilota = np.zeros((20, 2))
    return (np.tile([[[d_casa, 0.0]]], (20, 1, 1)), np.tile([[[0.0, d_fora]]], (20, 1, 1)), pilota)


def test_com_es_el_toc():
    fort, suau = np.where(np.arange(20) == 10, 6.0, 1.0), np.ones(20)
    assert [tac.mena(*posicions(1, 5), fort, 10, pm.H), tac.mena(*posicions(1, 5), suau, 10, pm.H),
            tac.mena(*posicions(1, 0.5), fort, 10, pm.H), tac.mena(*posicions(3, 5), fort, 10, pm.H),
            tac.mena(*posicions(5, 1), fort, 10, pm.A)] == [tac.FORT, tac.SUAU, tac.DISPUTAT, tac.LLUNY, tac.FORT]


def test_la_taula_dels_canvis():
    files = pd.DataFrame([{"escenari": "net", "trobat": tac.BO, tac.TARD: False}] * 6
                         + [{"escenari": "net", "trobat": tac.BO, tac.TARD: True}] * 2
                         + [{"escenari": "net", "trobat": tac.CAP, tac.TARD: True}] * 2)
    t = tac.taula_canvis(files).loc["net"]
    assert (t["n canvis"], t[tac.BO], t[tac.D_ABANS], t[tac.CAP], t["tard, a tots"]) == (10, 0.8, 0, 0.2, 0.4)
    assert (t[f"tard, si troba {tac.BO}"], t[f"tard, si troba {tac.CAP}"]) == (0.25, 1.0)
