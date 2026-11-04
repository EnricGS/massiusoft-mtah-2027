"""T3f al banc: quines imatges s'aprenen, les mostres, la tria del decodificador, el criteri del pla i l'informe."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import model_a_context as t3e
from banc import model_a_control as t3d
from banc import model_a_possessio as t3f
from banc import model_a_quart as t3b
from banc.tests import sintetic
from cadena import model
from possessio.oficial import possession_metrics as pm


def etiqueta(*trossos: tuple[int, int]) -> np.ndarray:
    return np.concatenate([np.full(n, codi, dtype=np.int8) for codi, n in trossos])


def una_de_cada_pas(e: np.ndarray) -> np.ndarray:
    return np.flatnonzero(np.isin(e, model.CLASSES))[::model.PAS]


def test_amb_possessions_llargues_tria_el_mateix_que_model_mostres():
    e = etiqueta((pm.H, 400), (pm.D, 100), (pm.A, 400))
    assert np.array_equal(t3f.tria(e, [(0, len(e))]), una_de_cada_pas(e))


def test_una_possessio_curta_passa_a_tenir_8_imatges_repartides_i_la_resta_no_canvia():
    e = etiqueta((pm.H, 400), (pm.A, 40), (pm.H, 400))
    t = t3f.tria(e, [(0, len(e))])
    dins = (t >= 400) & (t < 440)
    assert list(t[dins]) == list(np.round(np.linspace(400, 439, 8)).astype(int))
    abans = una_de_cada_pas(e)
    assert np.array_equal(t[~dins], abans[(abans < 400) | (abans >= 440)])


def test_una_possessio_de_menys_de_8_imatges_les_dona_totes():
    e = etiqueta((pm.H, 400), (pm.A, 5), (pm.H, 400))
    t = t3f.tria(e, [(0, len(e))])
    assert list(t[(t >= 400) & (t < 405)]) == [400, 401, 402, 403, 404]


def test_la_d_no_es_completa():
    e = etiqueta((pm.H, 400), (pm.D, 20), (pm.H, 400))
    t = t3f.tria(e, [(0, len(e))])
    assert np.array_equal(t, una_de_cada_pas(e))


def test_les_possessions_son_les_de_la_metrica_cada_part_a_part():
    e = etiqueta((pm.H, 30), (pm.H, 30))
    assert len(t3f.tria(e, [(0, 30), (30, 60)])) == 16                 # dues possessions, una per part
    assert len(t3f.tria(e, [(0, 60)])) == 8


def test_la_x_no_s_apren():
    e = etiqueta((pm.X, 10), (pm.H, 30), (pm.X, 20), (pm.A, 30))
    t = t3f.tria(e, [(10, 40), (60, 90)])
    assert np.isin(e[t], model.CLASSES).all() and len(t) == 16


def test_les_mostres_son_les_triades_i_les_girades():
    p = sintetic.partit(n=3000)
    taula = t3d.taula(p)
    x, y = t3f.mostres(p, taula)
    t = t3f.tria(p.veritat, avalua.trams_valids(p))
    assert len(x) == len(y) == 2 * len(t)
    pd.testing.assert_frame_equal(x.iloc[:len(t)].reset_index(drop=True), taula.iloc[t].reset_index(drop=True))
    assert np.array_equal(y[:len(t)], p.veritat[t]) and np.array_equal(y[len(t):], model.GIRA[p.veritat[t]])


def test_sense_entrenar_s_atura_si_no_hi_ha_les_probabilitats(tmp_path, monkeypatch):
    monkeypatch.setattr(t3f, "DIR_CAU", tmp_path)
    with pytest.raises(RuntimeError, match="A per possessió"):
        t3f.probabilitats(fonts.NOMS[0], entrena=False)


def graella(guany: dict[str, float]) -> pd.DataFrame:
    """A context, a 0,60 amb λ 4 i durada mínima 12; A per possessió, a 0,60 + guany amb λ 2 i durada mínima 12;
    tots dos, a 0,40 amb λ 2 i durada mínima 1."""
    millors = {t3e.CONTEXT: (4.0, 12, 0.0), t3f.POSSESSIO: (2.0, 12, None)}
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
    metodes, triades = t3f.tria_sense_mirar(graella(als_quarts(0.06, 0.0)))
    assert all(t == {t3e.CONTEXT: (4.0, 12), t3f.POSSESSIO: (2.0, 12)} for t in triades.values())
    assert len(metodes) == 2 * len(fonts.NOMS) * len(t3.ESCENARIS)


@pytest.mark.parametrize(("dins", "perd", "passa"), [(0.06, -0.03, {"quarts": True, "altres": True}),
                                                     (0.06, -0.05, {"quarts": True, "altres": False}),
                                                     (0.03, 0.0, {"quarts": False, "altres": True})])
def test_el_criteri_es_contra_a_context(dins: float, perd: float, passa: dict[str, bool]):
    metodes, _ = t3f.tria_sense_mirar(graella(als_quarts(dins, perd)))
    assert t3b.compleix(t3b.comparacio(metodes, t3f.POSSESSIO, t3e.CONTEXT)) == passa


def test_l_encert_per_durada():
    files = pd.DataFrame([
        {"metode": t3e.CONTEXT, "durada": 0.5, "encert_imatge": 0.4, "encert_decodificat": 0.2},
        {"metode": t3e.CONTEXT, "durada": 0.8, "encert_imatge": 0.6, "encert_decodificat": 0.4},
        {"metode": t3f.POSSESSIO, "durada": 0.5, "encert_imatge": 0.7, "encert_decodificat": 0.6},
        {"metode": t3f.POSSESSIO, "durada": 30.0, "encert_imatge": 1.0, "encert_decodificat": 1.0}])
    e = t3f.encert_per_durada(files)
    assert e.loc["<1 s", (t3e.CONTEXT, "encert_imatge")] == pytest.approx(0.5)
    assert e.loc["<1 s", (t3f.POSSESSIO, "encert_decodificat")] == pytest.approx(0.6)
    assert e.loc[">10 s", (t3f.POSSESSIO, "encert_imatge")] == pytest.approx(1.0)


def test_l_informe():
    metodes, triades = t3f.tria_sense_mirar(graella(als_quarts(0.06, 0.0)))
    c = t3b.comparacio(metodes, t3f.POSSESSIO, t3e.CONTEXT)
    encert = pd.DataFrame([{"metode": m, "durada": d, "encert_imatge": 0.5, "encert_decodificat": 0.4}
                           for m in t3f.CLASSIFICADORS for d in (0.5, 1.5, 3.0, 7.0, 20.0)])
    md = t3f.markdown(c, metodes, triades, t3b.compleix(c), t3f.encert_per_durada(encert))
    assert "## A per possessió contra A context (spellF1): el criteri" in md and "**Passa.**" in md
    assert "## Possessions predites per cada real" in md and "0.75" in md
    assert "## L'encert de l'equip per durada de la possessió" in md
    assert "nan" not in md and "A per possessió: λ = 2, durada mínima 12 (10 partits)" in md
