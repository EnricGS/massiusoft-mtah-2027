"""T3n al banc: amb qui aprèn cada xarxa i quin és el partit apartat, la memòria cau, la tria dels paràmetres, el
criteri del pla i l'informe."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from banc import fonts
from banc import decodificador_tocs as t3
from banc import model_a_context as t3e
from banc import model_a_quart as t3b
from banc import model_a_xarxa as t3m
from banc import model_a_xarxa_validada as t3n


def test_cada_xarxa_apren_amb_els_seus_i_l_apartat_es_el_primer_de_dfl():
    for prova in fonts.NOMS:
        noms = t3n.per_entrenar(prova)
        assert len(noms) == 9 and prova not in noms and noms == [n for n in fonts.NOMS if n != prova]
        assert noms[0].startswith("dfl-")
        for i, grup in enumerate(t3e.grups(prova)):
            noms = t3n.per_entrenar(prova, i)
            assert noms == t3m.per_entrenar_el_grup(prova, i)          # els mateixos sis que a la T3m
            assert len(noms) == 6 and prova not in noms and not set(noms) & set(grup)
            assert noms[0].startswith("dfl-") and noms == [n for n in fonts.NOMS if n in noms]


@pytest.mark.parametrize("de_qui", ["probabilitats", "xarxa_de_la_prova"])
def test_sense_entrenar_s_atura_si_no_hi_ha_les_probabilitats(tmp_path, monkeypatch, de_qui):
    monkeypatch.setattr(t3n, "DIR_CAU", tmp_path)
    monkeypatch.setattr(t3n, "DIR_CAU_PROVA", tmp_path)
    with pytest.raises(RuntimeError, match="validada"):
        getattr(t3n, de_qui)(fonts.NOMS[0], entrena=False)


def test_la_corba_desada(tmp_path, monkeypatch):
    monkeypatch.setattr(t3n, "DIR_CAU_PROVA", tmp_path)
    monkeypatch.setattr(t3n, "DIR_CAU_GRUPS", tmp_path)
    c = {"apartat": [0.5, 0.4, 0.45, 0.46, 0.47], "primera": [0.6, 0.5, 0.4, 0.35, 0.3], "passades": 2,
         "segona": [0.6, 0.5]}
    t3n.desa(tmp_path / f"{fonts.NOMS[0]}.npz", **t3n._corba(c), e0=np.zeros(3))
    assert t3n.corba(fonts.NOMS[0]) == c
    with pytest.raises(RuntimeError, match="validada"):
        t3n.corba(fonts.NOMS[0], 1)
    monkeypatch.setattr(t3n, "CLAU", "una altra")
    with pytest.raises(RuntimeError):
        t3n.corba(fonts.NOMS[0])


def graella(guany: dict[str, float]) -> pd.DataFrame:
    """A context, a 0,60 amb λ 4 i durada mínima 12; A xarxa, a 0,62 amb w 4, λ 16 i durada mínima 12; A xarxa
    validada, a 0,60 + guany amb w 2, λ 32 i durada mínima 1; tots, a 0,40 amb una altra combinació."""
    millors = {t3e.CONTEXT: ((math.nan, 4.0, 12), 0.0), t3m.XARXA: ((4.0, 16.0, 12), 0.02),
               t3n.VALIDADA: ((2.0, 32.0, 1), None)}
    files = []
    for i, nom in enumerate(fonts.NOMS):
        soroll = 0.01 * ((i % 3) - 1)
        for escenari in t3.ESCENARIS:
            comu = {"partit": nom, "font": "dfl" if i < 7 else "metrica", "escenari": escenari, "macro_f1": 0.8,
                    "possessions": 300, "possessions_reals": 400}
            for metode, ((w, lam, d_min), mes) in millors.items():
                spell = 0.60 + (guany[escenari] + soroll if mes is None else mes)
                altre_w = math.nan if math.isnan(w) else 1.0
                files += [{**comu, "metode": metode, "w": w, "lam": lam, "d_min": d_min, "spell_f1": spell},
                          {**comu, "metode": metode, "w": altre_w, "lam": 8.0, "d_min": 25, "spell_f1": 0.40}]
    return pd.DataFrame(files)


def als_quarts(dins: float, fora: float) -> dict[str, float]:
    return {e: (dins if e in t3.QUARTS else fora) for e in t3.ESCENARIS}


def test_la_tria_de_cada_metode():
    metodes, triades = t3n.tria_sense_mirar(graella(als_quarts(0.06, 0.0)))
    esperat = {t3e.CONTEXT: (4.0, 12), t3m.XARXA: (4.0, 16.0, 12), t3n.VALIDADA: (2.0, 32.0, 1)}
    assert all(t == esperat for t in triades.values())
    assert len(metodes) == len(t3n.METODES) * len(fonts.NOMS) * len(t3.ESCENARIS)


@pytest.mark.parametrize(("dins", "perd", "passa"), [(0.06, -0.03, {"quarts": True, "altres": True}),
                                                     (0.06, -0.05, {"quarts": True, "altres": False}),
                                                     (0.03, 0.0, {"quarts": False, "altres": True})])
def test_el_criteri_es_contra_a_context(dins: float, perd: float, passa: dict[str, bool]):
    metodes, _ = t3n.tria_sense_mirar(graella(als_quarts(dins, perd)))
    assert t3b.compleix(t3b.comparacio(metodes, t3n.VALIDADA, t3e.CONTEXT)) == passa


def test_l_informe():
    metodes, triades = t3n.tria_sense_mirar(graella(als_quarts(0.06, 0.0)))
    c = t3b.comparacio(metodes, t3n.VALIDADA, t3e.CONTEXT)
    c_xarxa = t3b.comparacio(metodes, t3n.VALIDADA, t3m.XARXA)
    enc = pd.DataFrame([{"partit": nom, "escenari": e, "metode": m, "durada": d, "pilota": v, "encert": encert,
                         "imatges": 100}
                        for nom in fonts.NOMS for e in t3.QUARTS for d in t3m.NOMS_DURADA for v in (True, False)
                        for m, encert in zip(t3n.ENCERT, (0.7, 0.6, 0.65, 0.8, 0.85))])
    cor = pd.DataFrame([{"prova": nom, "xarxa": x, "apartat": "dfl-J03WMX", "passades": p, "fetes": p + 3,
                         "minim": 0.35, "a_la_15": math.nan if p + 3 < 15 else 0.36}
                        for nom in fonts.NOMS for x, p in (("grup 0", 10), ("la seva", 21))])
    md = t3n.markdown(c, c_xarxa, metodes, enc, cor, triades, t3b.compleix(c))
    assert "## A xarxa validada contra A context (spellF1): el criteri" in md and "**Passa.**" in md
    assert "## A xarxa validada contra A xarxa (spellF1), només per saber-ho" in md
    assert "| <1 s | sí | 0.700 | 0.600 | 0.650 | 0.800 | 0.850 |" in md
    assert "| dfl-J03WMX | grup 0 | dfl-J03WMX | 10 | 13 | 0.3500 | — |" in md
    assert "| dfl-J03WMX | la seva | dfl-J03WMX | 21 | 24 | 0.3500 | 0.3600 |" in md
    assert "Les triades: de 10 a 21, la mediana 15.5." in md
    assert "A xarxa validada: w = 2, λ = 32, durada mínima 1 (10 partits)" in md and "nan" not in md


def test_els_resultats_es_poden_desar_en_json():
    cor = pd.DataFrame([{"prova": "a", "passades": 3, "a_la_15": math.nan, "perdua_apartat": [0.5, 0.4]}])
    assert t3.registres(cor) == [{"prova": "a", "passades": 3, "a_la_15": None, "perdua_apartat": [0.5, 0.4]}]
