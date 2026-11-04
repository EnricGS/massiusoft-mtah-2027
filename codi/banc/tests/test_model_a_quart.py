"""T3b al banc: A entrenat amb l'error ×¼, la tria sense mirar el partit que es puntua i els criteris del pla."""

from __future__ import annotations

import math
from dataclasses import asdict

import numpy as np
import pandas as pd
import pytest

from banc import decodificador_tocs as t3
from banc import degrada, fonts
from banc import model_a_quart as t3b
from cadena import decodifica_tocs as dt
from cadena import tocs

DET = tocs.Parametres(5, 5.0, 1.5)
BO, DOLENT = dt.Parametres(1, 16.0, 16.0, 25), dt.Parametres(1, math.inf, 4.0, 1)


def test_s_entrena_amb_els_tres_escenaris_d_a_amb_l_error_quart():
    assert t3b.ENTRENAMENT == ("curts ×¼", "llargs ×¼", "barreja ×¼")
    for q in t3b.ENTRENAMENT:
        e, base = t3.ESCENARIS[q], degrada.ESCENARIS[q.removesuffix(" ×¼")]
        assert e.nom == base.nom and e.sigma_jugadors_m == base.sigma_jugadors_m / 4


def test_sense_entrenar_s_atura_si_no_hi_ha_les_probabilitats(tmp_path, monkeypatch):
    monkeypatch.setattr(t3b, "DIR_CAU", tmp_path)
    with pytest.raises(RuntimeError, match="A ×¼"):
        t3b.probabilitats(fonts.NOMS[0], entrena=False)


def graella(guany_a: dict[str, float], guany_tocs: dict[str, float]) -> pd.DataFrame:
    """A a 0,50 amb λ 8 i a 0,40 amb λ 2; A ×¼, a 0,50 + guany_a amb λ 16 i a 0,40 amb λ 2; tocs ×¼, el BO a A ×¼ +
    guany_tocs i el DOLENT a 0,30."""
    files = []
    for i, nom in enumerate(fonts.NOMS):
        font = "dfl" if i < 7 else "metrica"
        soroll = 0.01 * ((i % 3) - 1)
        for escenari in t3.ESCENARIS:
            comu = {"partit": nom, "font": font, "escenari": escenari, "macro_f1": 0.8}
            quart = 0.50 + guany_a[escenari] + soroll
            files += [{**comu, "classificador": t3b.ARA, "metode": "A", "lam": 8.0, "d_min": 25, "spell_f1": 0.50},
                      {**comu, "classificador": t3b.ARA, "metode": "A", "lam": 2.0, "d_min": 1, "spell_f1": 0.40},
                      {**comu, "classificador": t3b.QUART, "metode": "A", "lam": 16.0, "d_min": 25,
                       "spell_f1": quart},
                      {**comu, "classificador": t3b.QUART, "metode": "A", "lam": 2.0, "d_min": 1, "spell_f1": 0.40},
                      {**comu, "classificador": t3b.QUART, "metode": "tocs", **asdict(DET), **asdict(BO),
                       "spell_f1": quart + guany_tocs[escenari] + soroll},
                      {**comu, "classificador": t3b.QUART, "metode": "tocs", **asdict(DET), **asdict(DOLENT),
                       "spell_f1": 0.30}]
    return pd.DataFrame(files)


def tria(guany_a: dict[str, float], guany_tocs: dict[str, float]) -> tuple[pd.DataFrame, dict]:
    return t3b.tria_sense_mirar(graella(guany_a, guany_tocs), dict.fromkeys(fonts.NOMS, DET),
                                dict.fromkeys(fonts.NOMS, (2.0, 1)))


def als_quarts(dins: float, fora: float) -> dict[str, float]:
    return {e: (dins if e in t3.QUARTS else fora) for e in t3.ESCENARIS}


def test_la_tria_de_cada_metode():
    metodes, triades = tria(als_quarts(0.10, 0.0), als_quarts(0.10, 0.0))
    assert all(t["A"] == (8.0, 25) and t[t3b.A_QUART] == (16.0, 25) and t[t3b.TOCS_QUART] == BO
               and t["detector"] == DET for t in triades.values())
    assert set(metodes["metode"]) == {"A cadena", "A", t3b.A_QUART, t3b.TOCS_QUART}
    assert len(metodes) == 4 * len(fonts.NOMS) * len(t3.ESCENARIS)
    net = metodes[metodes["escenari"] == "net"].groupby("metode")["spell_f1"].mean()
    assert np.isclose(net["A cadena"], 0.40) and np.isclose(net["A"], 0.50)


def test_els_criteris_de_les_dues_comparacions():
    metodes, _ = tria(als_quarts(0.10, 0.0), als_quarts(0.03, 0.0))
    c1 = t3b.comparacio(metodes, t3b.A_QUART, "A")
    c2 = t3b.comparacio(metodes, t3b.TOCS_QUART, t3b.A_QUART)
    assert t3b.compleix(c1) == {"quarts": True, "altres": True}
    assert t3b.compleix(c2) == {"quarts": False, "altres": True}       # els tocs només hi afegeixen 0,03
    assert np.allclose(c2.set_index("escenari").loc[list(t3.QUARTS), "diferencia"], 0.03, atol=0.002)


def test_si_a_quart_guanya_amb_poc_error_pero_perd_amb_el_x1_no_passa():
    guany = als_quarts(0.10, 0.0)
    guany["barreja"] = -0.06
    c1 = t3b.comparacio(tria(guany, als_quarts(0.0, 0.0))[0], t3b.A_QUART, "A")
    assert t3b.compleix(c1) == {"quarts": True, "altres": False}
    assert not c1.set_index("escenari").loc["barreja", "passa"]


def passades(a_temps_tocs: float, abans_tocs: float) -> pd.DataFrame:
    return pd.DataFrame([{"escenari": "els quatre ×¼", "metode": t3b.A_QUART, "canvis": 100, "a_temps": 0.40,
                          "abans": 0.10},
                         {"escenari": "els quatre ×¼", "metode": t3b.TOCS_QUART, "canvis": 100,
                          "a_temps": a_temps_tocs, "abans": abans_tocs}])


def test_el_criteri_de_les_passades_es_el_de_la_t3_amb_a_quart():
    assert t3b.criteri_passades(passades(0.50, 0.10))
    assert not t3b.criteri_passades(passades(0.50, 0.11))
    assert not t3b.criteri_passades(passades(0.40, 0.05))


def test_l_informe():
    metodes, triades = tria(als_quarts(0.10, 0.0), als_quarts(0.03, 0.0))
    c1 = t3b.comparacio(metodes, t3b.A_QUART, "A")
    c2 = t3b.comparacio(metodes, t3b.TOCS_QUART, t3b.A_QUART)
    passa = {"1": t3b.compleix(c1), "2": {**t3b.compleix(c2), "passades": False}}
    md = t3b.markdown(c1, c2, metodes, triades, passades(0.40, 0.10), passa)
    assert "## 1. A ×¼ contra A" in md and "**Passa.**" in md and "**No passa.**" in md
    assert "nan" not in md and "λ_vis 16" in md and "(10 partits)" in md
