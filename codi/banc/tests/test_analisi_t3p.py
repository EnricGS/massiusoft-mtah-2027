"""L'anàlisi de la T3p: les durades, l'aparellament de la mètrica, les estones de D, les possessions perdudes i les
taules."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from banc import analisi_t3p as an
from possessio.oficial import possession_metrics as pm


@pytest.mark.parametrize(("s", "tram"), [(0.2, "<1 s"), (1.0, "1-2 s"), (4.9, "2-5 s"), (5.0, "5-10 s"), (30, "≥10 s")])
def test_el_tram_de_durada(s, tram):
    assert an.tram(s) == tram


def test_l_aparellament_es_el_de_la_metrica():
    """Una possessió igual, una a mitges (IoU 0,5: s'aparella a 0,3, 0,4 i 0,5) i una que no hi és."""
    reals = [(0, 100, pm.H), (200, 300, pm.A), (400, 450, pm.H)]
    predites = [(0, 100, pm.H), (200, 250, pm.A)]
    np.testing.assert_allclose(an.aparellats(reals, predites), [1.0, 0.6, 0.0])
    assert an.aparellats([], predites).size == 0


def test_les_estones_de_d():
    codis = np.array([pm.H] * 5 + [pm.D] * 3 + [pm.A] * 2 + [pm.D] * 2, dtype=np.int8)
    assert an.morts(codis, [(0, len(codis))]) == [(5, 8), (10, 12)]


def test_les_possessions_perdudes_per_durada():
    po = pd.DataFrame({"escenari": "e", "metode": "m", "qui": ["reals"] * 3 + ["predites"],
                       "durada": ["<1 s", "<1 s", "≥10 s", "<1 s"], "aparellada": [0.0, 0.5, 0.5, 0.0]})
    t = an.perdudes(po)
    assert t.loc[("e", "<1 s"), ("n perdudes", "m")] == pytest.approx(1.5)
    assert t.loc[("e", "<1 s"), ("part", "m")] == pytest.approx(0.75)


def test_la_taula_en_markdown():
    t = pd.DataFrame({"n x": [3.0], "encert": [0.12345]}, index=pd.Index(["a"], name="escenari"))
    assert an.md(t).splitlines() == ["| escenari | n x | encert |", "|---|---|---|", "| a | 3 | 0.123 |"]
