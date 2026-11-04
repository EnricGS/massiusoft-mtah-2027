"""T3h al banc: les taules dels dos classificadors, les mostres, la tria del decodificador, el criteri del pla i
l'informe."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import model_a_contacte as t3h
from banc import model_a_context as t3e
from banc import model_a_control as t3d
from banc import model_a_possessio as t3f
from banc import model_a_quart as t3b
from banc.tests import sintetic
from cadena import contacte, context


@pytest.fixture(scope="module")
def partit():
    return sintetic.partit(n=3000)


def test_el_primer_te_els_senyals_d_a_control_i_els_del_contacte(partit):
    t = t3h.taula_primer(partit)
    nous = contacte.calcula(partit.tracking, partit.trams)
    assert list(t.columns) == [*t3d.taula(partit).columns, *nous.columns]
    pd.testing.assert_frame_equal(t[nous.columns], nous)


def test_el_segon_te_els_del_primer_i_els_del_context(partit):
    primer = np.random.default_rng(1).dirichlet(np.ones(3), partit.n)
    t = t3h.taula_segon(partit, primer)
    assert list(t.columns) == [*t3h.taula_primer(partit).columns, *context.calcula(primer, partit.trams).columns]


def test_les_mostres_son_les_de_la_t3f(partit):
    x, y = t3f.mostres(partit, t3h.taula_primer(partit))
    t = t3f.tria(partit.veritat, avalua.trams_valids(partit))
    assert len(x) == len(y) == 2 * len(t)


def test_sense_entrenar_s_atura_si_no_hi_ha_les_probabilitats(tmp_path, monkeypatch):
    monkeypatch.setattr(t3h, "DIR_CAU", tmp_path)
    with pytest.raises(RuntimeError, match="A contacte"):
        t3h.probabilitats(fonts.NOMS[0], entrena=False)


def graella(guany: dict[str, float]) -> pd.DataFrame:
    """A context, a 0,60 amb λ 4 i durada mínima 12; A per possessió, a 0,61 amb λ 8 i durada mínima 12; A contacte,
    a 0,60 + guany amb λ 8 i durada mínima 1; tots tres, a 0,40 amb λ 2 i durada mínima 1."""
    millors = {t3e.CONTEXT: (4.0, 12, 0.0), t3f.POSSESSIO: (8.0, 12, 0.01), t3h.CONTACTE: (8.0, 1, None)}
    files = []
    for i, nom in enumerate(fonts.NOMS):
        soroll = 0.01 * ((i % 3) - 1)
        for escenari in t3.ESCENARIS:
            comu = {"partit": nom, "font": "dfl" if i < 7 else "metrica", "escenari": escenari, "macro_f1": 0.8,
                    "possessions": 300, "possessions_reals": 400}
            for metode, (lam, d_min, mes) in millors.items():
                spell = 0.60 + (guany[escenari] + soroll if mes is None else mes)
                files += [{**comu, "metode": metode, "lam": lam, "d_min": d_min, "spell_f1": spell},
                          {**comu, "metode": metode, "lam": 2.0, "d_min": 1, "spell_f1": 0.40}]
    return pd.DataFrame(files)


def als_quarts(dins: float, fora: float) -> dict[str, float]:
    return {e: (dins if e in t3.QUARTS else fora) for e in t3.ESCENARIS}


def test_la_tria_de_cada_classificador():
    metodes, triades = t3h.tria_sense_mirar(graella(als_quarts(0.06, 0.0)))
    assert all(t == {t3e.CONTEXT: (4.0, 12), t3f.POSSESSIO: (8.0, 12), t3h.CONTACTE: (8.0, 1)}
               for t in triades.values())
    assert len(metodes) == 3 * len(fonts.NOMS) * len(t3.ESCENARIS)


@pytest.mark.parametrize(("dins", "perd", "passa"), [(0.06, -0.03, {"quarts": True, "altres": True}),
                                                     (0.06, -0.05, {"quarts": True, "altres": False}),
                                                     (0.03, 0.0, {"quarts": False, "altres": True})])
def test_el_criteri_es_contra_a_context(dins: float, perd: float, passa: dict[str, bool]):
    metodes, _ = t3h.tria_sense_mirar(graella(als_quarts(dins, perd)))
    assert t3b.compleix(t3b.comparacio(metodes, t3h.CONTACTE, t3e.CONTEXT)) == passa


def test_l_informe():
    metodes, triades = t3h.tria_sense_mirar(graella(als_quarts(0.06, 0.0)))
    c = t3b.comparacio(metodes, t3h.CONTACTE, t3e.CONTEXT)
    c_possessio = t3b.comparacio(metodes, t3h.CONTACTE, t3f.POSSESSIO)
    encert = pd.DataFrame([{"metode": m, "durada": d, "encert_imatge": 0.5, "encert_decodificat": 0.4}
                           for m in t3h.CLASSIFICADORS for d in (0.5, 1.5, 3.0, 7.0, 20.0)])
    md = t3h.markdown(c, c_possessio, metodes, triades, t3b.compleix(c), t3f.encert_per_durada(encert))
    assert "## A contacte contra A context (spellF1): el criteri" in md and "**Passa.**" in md
    assert "## A contacte contra A per possessió (spellF1), només per saber-ho" in md
    assert "## Possessions predites per cada real" in md and "0.75" in md
    assert "## L'encert de l'equip per durada de la possessió" in md
    assert "nan" not in md and "A contacte: λ = 8, durada mínima 1 (10 partits)" in md
