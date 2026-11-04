"""T3o al banc: les mostres i els partits de cada grup, els de la T3m; la memòria cau, la tria dels paràmetres, el
criteri del pla i l'informe."""

from __future__ import annotations

import ast
import inspect
import math
import textwrap

import numpy as np
import pandas as pd
import pytest

from banc import fonts
from banc import decodificador_tocs as t3
from banc import model_a_context as t3e
from banc import model_a_quart as t3b
from banc import model_a_xarxa as t3m
from banc import model_a_xarxes as t3o


def test_les_mostres_son_les_de_la_t3m():
    """El mateix cos que `t3m.entrena_xarxa`, llevat de la darrera línia (qui entrena): les mateixes mostres, en el
    mateix ordre."""
    def cos(f) -> list[str]:
        funcio = ast.parse(textwrap.dedent(inspect.getsource(f))).body[0]
        return [ast.dump(s) for s in funcio.body[1:-1]]                     # sense el docstring ni el return

    assert t3o.ENTRENAMENT == t3m.ENTRENAMENT
    assert cos(t3o.entrena_xarxes) == cos(t3m.entrena_xarxa) and len(cos(t3m.entrena_xarxa)) == 4


@pytest.mark.parametrize("de_qui", ["probabilitats", "xarxes_de_la_prova"])
def test_sense_entrenar_s_atura_si_no_hi_ha_les_probabilitats(tmp_path, monkeypatch, de_qui):
    monkeypatch.setattr(t3o, "DIR_CAU", tmp_path)
    monkeypatch.setattr(t3o, "DIR_CAU_PROVA", tmp_path)
    with pytest.raises(RuntimeError, match="xarxes"):
        getattr(t3o, de_qui)(fonts.NOMS[0], entrena=False)


def test_la_memoria_cau_porta_la_clau(tmp_path, monkeypatch):
    cami = tmp_path / "x.npz"
    t3o.desa(cami, a=np.arange(3))
    np.testing.assert_array_equal(t3o.llegeix(cami)["a"], np.arange(3))
    monkeypatch.setattr(t3o, "CLAU", "una altra")
    assert t3o.llegeix(cami) is None


def graella(guany: dict[str, float]) -> pd.DataFrame:
    """A context, a 0,60 amb λ 4 i durada mínima 12; A xarxa, a 0,62 amb w 4, λ 16 i durada mínima 12; A xarxes,
    a 0,60 + guany amb w 2, λ 32 i durada mínima 1; tots, a 0,40 amb una altra combinació."""
    millors = {t3e.CONTEXT: ((math.nan, 4.0, 12), 0.0), t3m.XARXA: ((4.0, 16.0, 12), 0.02),
               t3o.XARXES: ((2.0, 32.0, 1), None)}
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
    metodes, triades = t3o.tria_sense_mirar(graella(als_quarts(0.06, 0.0)))
    esperat = {t3e.CONTEXT: (4.0, 12), t3m.XARXA: (4.0, 16.0, 12), t3o.XARXES: (2.0, 32.0, 1)}
    assert all(t == esperat for t in triades.values())
    assert len(metodes) == len(t3o.METODES) * len(fonts.NOMS) * len(t3.ESCENARIS)


@pytest.mark.parametrize(("dins", "perd", "passa"), [(0.06, -0.03, {"quarts": True, "altres": True}),
                                                     (0.06, -0.05, {"quarts": True, "altres": False}),
                                                     (0.03, 0.0, {"quarts": False, "altres": True})])
def test_el_criteri_es_contra_a_context(dins: float, perd: float, passa: dict[str, bool]):
    metodes, _ = t3o.tria_sense_mirar(graella(als_quarts(dins, perd)))
    assert t3b.compleix(t3b.comparacio(metodes, t3o.XARXES, t3e.CONTEXT)) == passa


def test_l_informe():
    metodes, triades = t3o.tria_sense_mirar(graella(als_quarts(0.06, 0.0)))
    c = t3b.comparacio(metodes, t3o.XARXES, t3e.CONTEXT)
    c_xarxa = t3b.comparacio(metodes, t3o.XARXES, t3m.XARXA)
    enc = pd.DataFrame([{"partit": nom, "escenari": e, "metode": m, "durada": d, "pilota": v, "encert": encert,
                         "imatges": 100}
                        for nom in fonts.NOMS for e in t3.QUARTS for d in t3m.NOMS_DURADA for v in (True, False)
                        for m, encert in zip(t3o.ENCERT, (0.7, 0.6, 0.65, 0.8, 0.85))])
    md = t3o.markdown(c, c_xarxa, metodes, enc, triades, t3b.compleix(c))
    assert "## A xarxes contra A context (spellF1): el criteri" in md and "**Passa.**" in md
    assert "## A xarxes contra A xarxa (spellF1), només per saber-ho" in md
    assert "| <1 s | sí | 0.700 | 0.600 | 0.650 | 0.800 | 0.850 |" in md
    assert "A xarxes: w = 2, λ = 32, durada mínima 1 (10 partits)" in md and "nan" not in md
