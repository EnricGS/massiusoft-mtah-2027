"""T3j al banc: la taula del segon classificador de canvis, el primer de cada partit d'entrenament fet sense el seu
grup, com és la q, la tria dels paràmetres, el criteri del pla i l'informe."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from banc import fonts
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_canvis2 as t3j
from banc import model_a_context as t3e
from banc import model_a_quart as t3b
from banc.tests import sintetic
from possessio.oficial import possession_metrics as pm


def test_la_taula_del_segon_es_la_del_primer_i_el_context_de_la_q():
    p = sintetic.partit(n=3000)
    taula = pd.DataFrame({"x_h": np.arange(p.n, dtype=np.float32), "x_a": np.zeros(p.n, np.float32)})
    t = t3j.amb_canvis(p, taula, np.random.default_rng(1).random(p.n))
    assert len(t) == p.n and list(t.columns[:2]) == ["x_h", "x_a"]
    assert all(c.startswith("canvi_") for c in t.columns[2:]) and "canvi_q@max13" in t.columns
    pd.testing.assert_frame_equal(t[["x_h", "x_a"]], taula)


def test_el_primer_de_cada_partit_d_entrenament_no_ha_vist_el_seu_grup(monkeypatch):
    prova = fonts.NOMS[0]

    def taules(p):
        assert p == prova
        for nom in fonts.NOMS[1:]:
            for _ in range(2):
                yield nom, None, None

    monkeypatch.setattr(t3j, "taules", taules)
    monkeypatch.setattr(t3i, "mostres", lambda p, taula: ("x", "y"))
    vistos = []

    def entrena_canvis(mostres):
        vistos.append(len(mostres))
        return len(vistos) - 1

    monkeypatch.setattr(t3j, "entrena_canvis", entrena_canvis)
    del_partit = t3j.models_dels_grups(prova)
    assert sorted(del_partit) == sorted(fonts.NOMS[1:]) and vistos == [12, 12, 12]
    for i, grup in enumerate(t3e.grups(prova)):
        assert {del_partit[nom] for nom in grup} == {i}


def test_la_q_perfecta_i_la_q_constant():
    e = np.concatenate([np.full(n, codi, dtype=np.int8) for codi, n in ((pm.H, 100), (pm.A, 80), (pm.D, 20),
                                                                         (pm.H, 100))])
    trams = [(0, len(e))]
    perfecta = t3i.objectiu(e, trams).astype(float)
    assert t3j.qualitat(perfecta, e, trams) == {"auc": 1.0, "canvis_q_alta": 1.0}
    assert t3j.qualitat(np.full(len(e), 0.1), e, trams) == {"auc": 0.5, "canvis_q_alta": 0.0}


def test_sense_entrenar_s_atura_si_no_hi_ha_les_probabilitats(tmp_path, monkeypatch):
    monkeypatch.setattr(t3j, "DIR_CAU", tmp_path)
    with pytest.raises(RuntimeError, match="segon classificador de canvis"):
        t3j.probabilitats(fonts.NOMS[0], entrena=False)


def graella(guany: dict[str, float]) -> pd.DataFrame:
    """A context, a 0,60 amb λ 4 i durada mínima 12; A canvis, a 0,62 amb w 4, λ 16 i durada mínima 12; A canvis 2,
    a 0,60 + guany amb w 2, λ 32 i durada mínima 1; tots, a 0,40 amb una altra combinació."""
    millors = {t3e.CONTEXT: ((math.nan, 4.0, 12), 0.0), t3i.CANVIS: ((4.0, 16.0, 12), 0.02),
               t3j.CANVIS2: ((2.0, 32.0, 1), None)}
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
    metodes, triades = t3j.tria_sense_mirar(graella(als_quarts(0.06, 0.0)))
    esperat = {t3e.CONTEXT: (4.0, 12), t3i.CANVIS: (4.0, 16.0, 12), t3j.CANVIS2: (2.0, 32.0, 1)}
    assert all(t == esperat for t in triades.values())
    assert len(metodes) == len(t3j.METODES) * len(fonts.NOMS) * len(t3.ESCENARIS)


@pytest.mark.parametrize(("dins", "perd", "passa"), [(0.06, -0.03, {"quarts": True, "altres": True}),
                                                     (0.06, -0.05, {"quarts": True, "altres": False}),
                                                     (0.03, 0.0, {"quarts": False, "altres": True})])
def test_el_criteri_es_contra_a_context(dins: float, perd: float, passa: dict[str, bool]):
    metodes, _ = t3j.tria_sense_mirar(graella(als_quarts(dins, perd)))
    assert t3b.compleix(t3b.comparacio(metodes, t3j.CANVIS2, t3e.CONTEXT)) == passa


def test_l_informe():
    metodes, triades = t3j.tria_sense_mirar(graella(als_quarts(0.06, 0.0)))
    c = t3b.comparacio(metodes, t3j.CANVIS2, t3e.CONTEXT)
    c_canvis = t3b.comparacio(metodes, t3j.CANVIS2, t3i.CANVIS)
    q = pd.DataFrame([{"partit": nom, "escenari": e, "metode": m, "auc": auc, "canvis_q_alta": alta}
                      for nom in fonts.NOMS for e in t3.QUARTS
                      for m, auc, alta in ((t3i.CANVIS, 0.9, 0.4), (t3j.CANVIS2, 0.95, 0.55))])
    md = t3j.markdown(c, c_canvis, metodes, q, triades, t3b.compleix(c))
    assert "## A canvis 2 contra A context (spellF1): el criteri" in md and "**Passa.**" in md
    assert "## A canvis 2 contra A canvis (spellF1), només per saber-ho" in md
    assert f"| {t3.QUARTS[0]} | 0.900 | 0.950 | 0.400 | 0.550 |" in md
    assert "## Possessions predites per cada real" in md and "0.75" in md
    assert "A canvis 2: w = 2, λ = 32, durada mínima 1 (10 partits)" in md and "nan" not in md
