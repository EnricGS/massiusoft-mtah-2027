"""T3 al banc: els escenaris ×¼, la tria sense mirar el partit que es puntua i els criteris del pla."""

from __future__ import annotations

import math
from dataclasses import asdict

import numpy as np
import pandas as pd

from banc import decodificador_tocs as t3
from banc import degrada, fonts
from banc import tocs as banc_tocs
from cadena import decodifica_tocs as dt
from cadena import tocs

DET = tocs.Parametres(5, 5.0, 1.5)
BO, DOLENT = dt.Parametres(2, 64.0, 8.0, 25), dt.Parametres(1, math.inf, 4.0, 1)


def test_els_escenaris_quart_tenen_els_mateixos_forats_i_menys_error():
    for q, b in zip(t3.QUARTS, t3.BASES):
        e, base = t3.ESCENARIS[q], degrada.ESCENARIS[b]
        assert e.nom == base.nom and e.forats_s == base.forats_s and e.camera_m == base.camera_m
        assert e.sigma_pilota_m == base.sigma_pilota_m / 4 and e.tremolor_jugadors_m == base.tremolor_jugadors_m / 4
    assert set(t3.ESCENARIS) == {"net", *t3.QUARTS, *t3.BASES, "soroll2"}


def test_el_detector_de_cada_partit_es_tria_amb_els_altres():
    files = []
    for nom in fonts.NOMS:
        for det, trobats in ((DET, 60), (tocs.Parametres(8, 8.0, 1.0), 40)):
            if nom == fonts.NOMS[0]:
                trobats = 100 - trobats                                 # aquest partit preferiria l'altre
            files.append({"partit": nom, "escenari": "barreja, soroll ×0.25", **asdict(det),
                          **dict.fromkeys(banc_tocs.COMPTES, 1), "canvis_amb_pilota": 100,
                          "trobats_amb_pilota": trobats, "de_l_altre_sense_accio": 0})
    triats = t3.detectors(pd.DataFrame(files))
    assert set(triats.values()) == {DET}


def graella(guany: dict[str, float]) -> pd.DataFrame:
    """A a 0,50 amb λ 8 i a 0,40 amb λ 2; tocs, el BO a 0,50 + guany i el DOLENT a 0,30."""
    files = []
    for i, nom in enumerate(fonts.NOMS):
        font = "dfl" if i < 7 else "metrica"
        for escenari in t3.ESCENARIS:
            comu = {"partit": nom, "font": font, "escenari": escenari, "macro_f1": 0.8}
            files += [{**comu, "metode": "A", "lam": 8.0, "d_min": 25, "spell_f1": 0.50},
                      {**comu, "metode": "A", "lam": 2.0, "d_min": 1, "spell_f1": 0.40}]
            soroll = 0.01 * ((i % 3) - 1)
            files += [{**comu, "metode": "tocs", **asdict(DET), **asdict(BO),
                       "spell_f1": 0.50 + guany[escenari] + soroll},
                      {**comu, "metode": "tocs", **asdict(DET), **asdict(DOLENT), "spell_f1": 0.30}]
    return pd.DataFrame(files)


def test_la_tria_i_els_criteris():
    guany = {e: (0.10 if e in t3.QUARTS else -0.02) for e in t3.ESCENARIS}
    dets = dict.fromkeys(fonts.NOMS, DET)
    cadena = dict.fromkeys(fonts.NOMS, (2.0, 1))
    metodes, triades = t3.tria_sense_mirar(graella(guany), dets, cadena)
    assert all(t["A"] == (8.0, 25) and t["tocs"] == BO for t in triades.values())
    assert set(metodes["metode"]) == {"A", "A cadena", "tocs"}
    assert len(metodes) == 3 * len(fonts.NOMS) * len(t3.ESCENARIS)
    c = t3.comparacio(metodes).set_index("escenari")
    assert c.loc[list(t3.QUARTS), "passa"].all() and c.loc["net", "passa"]
    assert np.isclose(c.loc["net", "A cadena"], 0.40)


def test_si_perd_massa_en_un_escenari_no_passa():
    guany = {e: (0.10 if e in t3.QUARTS else 0.0) for e in t3.ESCENARIS}
    guany["soroll2"] = -0.06
    metodes, _ = t3.tria_sense_mirar(graella(guany), dict.fromkeys(fonts.NOMS, DET),
                                     dict.fromkeys(fonts.NOMS, (8.0, 25)))
    c = t3.comparacio(metodes).set_index("escenari")
    assert not c.loc["soroll2", "passa"] and c.loc["barreja", "passa"]


def test_guanyar_per_poc_als_quart_no_es_clarament():
    guany = {e: (0.03 if e in t3.QUARTS else 0.0) for e in t3.ESCENARIS}
    metodes, _ = t3.tria_sense_mirar(graella(guany), dict.fromkeys(fonts.NOMS, DET),
                                     dict.fromkeys(fonts.NOMS, (8.0, 25)))
    assert not t3.comparacio(metodes).set_index("escenari").loc[list(t3.QUARTS), "passa"].any()


def test_el_criteri_de_les_passades_llargues():
    def taula(a_temps_tocs: float, abans_tocs: float) -> pd.DataFrame:
        return pd.DataFrame([{"escenari": "els quatre ×¼", "metode": "A", "a_temps": 0.40, "abans": 0.10},
                             {"escenari": "els quatre ×¼", "metode": "tocs", "a_temps": a_temps_tocs,
                              "abans": abans_tocs}])
    assert t3.criteri_passades(taula(0.50, 0.10))
    assert not t3.criteri_passades(taula(0.50, 0.11))
    assert not t3.criteri_passades(taula(0.40, 0.05))


def test_el_json_no_porta_infinits():
    t = pd.DataFrame({"lam_vis": [math.inf, 64.0], "x": [np.nan, 1.0]})
    assert t3.registres(t) == [{"lam_vis": "inf", "x": None}, {"lam_vis": 64.0, "x": 1.0}]
