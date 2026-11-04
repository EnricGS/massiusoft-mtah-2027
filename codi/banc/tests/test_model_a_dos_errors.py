"""T3c al banc: A entrenat amb els dos errors, la tria sense mirar el partit que es puntua i el criteri del pla."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from banc import decodificador_tocs as t3
from banc import fonts, model_a
from banc import model_a_dos_errors as t3c
from banc import model_a_quart as t3b


def test_les_mostres_son_les_d_a_i_les_d_a_quart_juntes(monkeypatch):
    def mostres(valor: int):
        return lambda nom: (pd.DataFrame({"x": [valor, valor]}), np.array([valor, valor], np.int8))

    monkeypatch.setattr(model_a, "mostres_de", mostres(1))
    monkeypatch.setattr(t3b, "mostres_de", mostres(2))
    x, y = t3c.mostres_de(fonts.NOMS[0])
    assert x["x"].tolist() == [1, 1, 2, 2] and y.tolist() == [1, 1, 2, 2]
    assert t3c.ENTRENAMENT == ("curts", "llargs", "barreja", "curts ×¼", "llargs ×¼", "barreja ×¼")


def test_sense_entrenar_s_atura_si_no_hi_ha_les_probabilitats(tmp_path, monkeypatch):
    monkeypatch.setattr(t3c, "DIR_CAU", tmp_path)
    with pytest.raises(RuntimeError, match="A ×1\\+×¼"):
        t3c.probabilitats(fonts.NOMS[0], entrena=False)


def graella(guany: dict[str, float]) -> pd.DataFrame:
    """Cada classificador, a 0,40 amb λ 2; A, a 0,50 amb λ 8; A ×¼, a 0,55 amb λ 16; A ×1+×¼, a 0,50 + guany amb
    λ 4."""
    millors = {"A": (8.0, 0.0), t3b.A_QUART: (16.0, 0.05), t3c.DOS: (4.0, None)}
    files = []
    for i, nom in enumerate(fonts.NOMS):
        font = "dfl" if i < 7 else "metrica"
        soroll = 0.01 * ((i % 3) - 1)
        for escenari in t3.ESCENARIS:
            comu = {"partit": nom, "font": font, "escenari": escenari, "macro_f1": 0.8}
            for metode, (lam, mes) in millors.items():
                spell = 0.50 + (guany[escenari] + soroll if mes is None else mes)
                files += [{**comu, "metode": metode, "lam": lam, "d_min": 25, "spell_f1": spell},
                          {**comu, "metode": metode, "lam": 2.0, "d_min": 1, "spell_f1": 0.40}]
    return pd.DataFrame(files)


def als_quarts(dins: float, fora: float) -> dict[str, float]:
    return {e: (dins if e in t3.QUARTS else fora) for e in t3.ESCENARIS}


def test_la_tria_de_cada_classificador():
    metodes, triades = t3c.tria_sense_mirar(graella(als_quarts(0.06, 0.0)), dict.fromkeys(fonts.NOMS, (2.0, 1)))
    assert all(t == {"A": (8.0, 25), t3b.A_QUART: (16.0, 25), t3c.DOS: (4.0, 25)} for t in triades.values())
    assert set(metodes["metode"]) == {"A cadena", *t3c.CLASSIFICADORS}
    assert len(metodes) == 4 * len(fonts.NOMS) * len(t3.ESCENARIS)
    net = metodes[metodes["escenari"] == "net"].groupby("metode")["spell_f1"].mean()
    assert np.isclose(net["A cadena"], 0.40) and np.isclose(net[t3b.A_QUART], 0.55)


@pytest.mark.parametrize(("perd", "passa"), [(-0.03, True), (-0.05, False)])
def test_el_criteri_contra_a(perd: float, passa: bool):
    metodes, _ = t3c.tria_sense_mirar(graella(als_quarts(0.06, perd)), dict.fromkeys(fonts.NOMS, (8.0, 25)))
    c = t3b.comparacio(metodes, t3c.DOS, "A")
    assert t3b.compleix(c) == {"quarts": True, "altres": passa}


def test_l_informe():
    metodes, triades = t3c.tria_sense_mirar(graella(als_quarts(0.06, 0.0)), dict.fromkeys(fonts.NOMS, (2.0, 1)))
    c, c_quart = t3b.comparacio(metodes, t3c.DOS, "A"), t3b.comparacio(metodes, t3c.DOS, t3b.A_QUART)
    md = t3c.markdown(c, c_quart, metodes, triades, t3b.compleix(c))
    assert "## A ×1+×¼ contra A (spellF1): el criteri" in md and "**Passa.**" in md
    assert "nan" not in md and "A ×1+×¼: λ = 4, durada mínima 25 (10 partits)" in md
