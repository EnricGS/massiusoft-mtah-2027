"""T3e al banc: els grups sense el partit que es prova, el segon classificador, la tria i el criteri del pla."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from banc import decodificador_tocs as t3
from banc import fonts
from banc import model_a_context as t3e
from banc import model_a_control as t3d
from banc import model_a_dos_errors as t3c
from banc import model_a_quart as t3b
from banc.tests import sintetic
from cadena import context


@pytest.mark.parametrize("prova", fonts.NOMS)
def test_els_grups_son_els_altres_nou_sense_repetir_i_sempre_els_mateixos(prova: str):
    g = t3e.grups(prova)
    assert len(g) == t3e.GRUPS and all(len(grup) == 3 for grup in g)
    assert sorted(sum(g, ())) == sorted(n for n in fonts.NOMS if n != prova)
    assert g == t3e.grups(prova)


def test_la_taula_son_els_senyals_d_a_control_i_els_del_context():
    p = sintetic.partit(n=3000)
    primer = np.random.default_rng(1).dirichlet([1, 1, 1], p.n)
    x = t3e.taula(p, primer)
    assert list(x.columns) == [*t3d.taula(p).columns, *context.calcula(primer, p.trams).columns]


def test_sense_entrenar_s_atura_si_no_hi_ha_les_probabilitats(tmp_path, monkeypatch):
    monkeypatch.setattr(t3e, "DIR_CAU", tmp_path)
    with pytest.raises(RuntimeError, match="A context"):
        t3e.probabilitats(fonts.NOMS[0], entrena=False)


def graella(guany: dict[str, float]) -> pd.DataFrame:
    """Cada classificador, a 0,40 amb λ 2; A ×1+×¼, a 0,50 amb λ 8; A control, a 0,53 amb λ 4; A context, a
    0,50 + guany amb λ 2 i durada mínima 12."""
    millors = {t3c.DOS: (8.0, 25, 0.0), t3d.CONTROL: (4.0, 25, 0.03), t3e.CONTEXT: (2.0, 12, None)}
    files = []
    for i, nom in enumerate(fonts.NOMS):
        font = "dfl" if i < 7 else "metrica"
        soroll = 0.01 * ((i % 3) - 1)
        for escenari in t3.ESCENARIS:
            comu = {"partit": nom, "font": font, "escenari": escenari, "macro_f1": 0.8}
            for metode, (lam, d_min, mes) in millors.items():
                spell = 0.50 + (guany[escenari] + soroll if mes is None else mes)
                files += [{**comu, "metode": metode, "lam": lam, "d_min": d_min, "spell_f1": spell},
                          {**comu, "metode": metode, "lam": 2.0, "d_min": 1, "spell_f1": 0.40}]
    return pd.DataFrame(files)


def als_quarts(dins: float, fora: float) -> dict[str, float]:
    return {e: (dins if e in t3.QUARTS else fora) for e in t3.ESCENARIS}


def test_la_tria_de_cada_classificador():
    metodes, triades = t3e.tria_sense_mirar(graella(als_quarts(0.06, 0.0)))
    assert all(t == {t3c.DOS: (8.0, 25), t3d.CONTROL: (4.0, 25), t3e.CONTEXT: (2.0, 12)} for t in triades.values())
    assert set(metodes["metode"]) == set(t3e.CLASSIFICADORS)
    assert len(metodes) == 3 * len(fonts.NOMS) * len(t3.ESCENARIS)


@pytest.mark.parametrize(("dins", "perd", "passa"), [(0.06, -0.03, {"quarts": True, "altres": True}),
                                                     (0.06, -0.05, {"quarts": True, "altres": False}),
                                                     (0.03, 0.0, {"quarts": False, "altres": True})])
def test_el_criteri_es_contra_a_dos_errors(dins: float, perd: float, passa: dict[str, bool]):
    metodes, _ = t3e.tria_sense_mirar(graella(als_quarts(dins, perd)))
    assert t3b.compleix(t3b.comparacio(metodes, t3e.CONTEXT, t3c.DOS)) == passa


def test_l_informe():
    metodes, triades = t3e.tria_sense_mirar(graella(als_quarts(0.06, 0.0)))
    c, c_control = (t3b.comparacio(metodes, t3e.CONTEXT, t3c.DOS),
                    t3b.comparacio(metodes, t3e.CONTEXT, t3d.CONTROL))
    md = t3e.markdown(c, c_control, metodes, triades, t3b.compleix(c))
    assert "## A context contra A ×1+×¼ (spellF1): el criteri" in md and "**Passa.**" in md
    assert "## A context contra A control (spellF1), només per saber-ho" in md
    assert "nan" not in md and "A context: λ = 2, durada mínima 12 (10 partits)" in md
