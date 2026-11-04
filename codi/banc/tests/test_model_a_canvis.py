"""T3i al banc: els canvis d'equip de la veritat, l'objectiu i les mostres del classificador de canvis, el cost a cada
imatge, el decodificador, la tria dels paràmetres, el criteri del pla i l'informe."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_contacte as t3h
from banc import model_a_context as t3e
from banc import model_a_quart as t3b
from banc.tests import sintetic
from cadena import decodifica, model, senyals
from cadena import decodifica_tocs as dt
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm


def etiqueta(*trossos: tuple[int, int]) -> np.ndarray:
    return np.concatenate([np.full(n, codi, dtype=np.int8) for codi, n in trossos])


def test_un_canvi_es_una_possessio_de_l_altre_equip_encara_que_hi_hagi_pilota_morta_entremig():
    e = etiqueta((pm.H, 50), (pm.A, 30), (pm.D, 10), (pm.A, 40), (pm.D, 5), (pm.H, 20))
    assert list(t3i.canvis(e, [(0, len(e))])) == [50, 135]


def test_els_canvis_son_dins_de_cada_part():
    e = etiqueta((pm.H, 30), (pm.A, 30))
    assert len(t3i.canvis(e, [(0, 30), (30, 60)])) == 0
    assert list(t3i.canvis(e, [(0, 60)])) == [30]


def test_l_objectiu_son_les_imatges_a_6_o_menys_d_un_canvi():
    e = etiqueta((pm.H, 50), (pm.A, 50))
    o = t3i.objectiu(e, [(0, len(e))])
    assert list(np.flatnonzero(o)) == list(range(44, 57))


def test_les_mostres_son_una_de_cada_16_i_les_girades_amb_el_mateix_objectiu():
    p = sintetic.partit(n=3000)
    taula = pd.DataFrame({"x_h": np.arange(p.n, dtype=np.float32), "x_a": np.zeros(p.n, np.float32)})
    x, y = t3i.mostres(p, taula)
    tria = np.flatnonzero(np.isin(p.veritat, model.CLASSES))[::model.PAS]
    o = t3i.objectiu(p.veritat, avalua.trams_valids(p))[tria]
    assert len(x) == len(y) == 2 * len(tria) and o.any()
    assert np.array_equal(y, np.concatenate([o, o]).astype(np.int8))
    pd.testing.assert_frame_equal(x.iloc[len(tria):].reset_index(drop=True),
                                  senyals.intercanvia(taula.iloc[tria]).reset_index(drop=True))


def test_el_cost_d_h_a_a_ve_de_q_i_el_de_la_d_es_lambda():
    q = np.array([1.0, 0.5, 0.0])
    c = t3i.costos(q, lam=4.0, w=2.0)
    np.testing.assert_allclose(c[:, dt.H, dt.A], [0.0, 2 * math.log(2), -2 * math.log(t3i.Q_MINIM)])
    np.testing.assert_allclose(c[:, dt.A, dt.H], c[:, dt.H, dt.A])
    for i, j in ((dt.H, dt.D), (dt.D, dt.H), (dt.A, dt.D), (dt.D, dt.A)):
        assert (c[:, i, j] == 4.0).all()


@pytest.mark.parametrize("d_min", [1, 12, 25])
def test_amb_q_igual_a_tot_arreu_es_el_decodificador_d_ara(d_min: int):
    rng = np.random.default_rng(3)
    proba = rng.dirichlet(np.ones(3) * 0.5, 600)
    prior = np.array([0.45, 0.4, 0.15])
    trams = ((1, 10, 289), (2, 300, 589))
    q = np.full(600, math.exp(-4.0 / 2.0))                           # 2 · (−ln q) = 4 = λ
    assert np.array_equal(t3i.per_trams(log_relativa(proba, prior), q, trams, 2.0, 4.0, d_min),
                          decodifica.per_trams(proba, prior, trams, 4.0, d_min))


def test_on_q_es_alta_canviar_d_equip_costa_poc():
    proba = np.tile([0.55, 0.45, 0.0], (200, 1))
    proba[100:110] = [0.45, 0.55, 0.0]                                # 10 imatges amb A, poc clar
    relativa = log_relativa(proba, np.array([0.5, 0.5, 1e-9]))
    trams = ((1, 0, 199),)
    baixa = t3i.per_trams(relativa, np.full(200, 0.01), trams, 2.0, 4.0, 1)
    q = np.full(200, 0.01)
    q[97:113] = 0.9
    alta = t3i.per_trams(relativa, q, trams, 2.0, 4.0, 1)
    assert (baixa == pm.H).all() and (alta[100:110] == pm.A).all() and (alta[:100] == pm.H).all()


def test_sense_entrenar_s_atura_si_no_hi_ha_les_probabilitats(tmp_path, monkeypatch):
    monkeypatch.setattr(t3i, "DIR_CAU", tmp_path)
    with pytest.raises(RuntimeError, match="canvis"):
        t3i.probabilitats(fonts.NOMS[0], entrena=False)


def graella(guany: dict[str, float]) -> pd.DataFrame:
    """A context, a 0,60 amb λ 4 i durada mínima 12; A contacte, a 0,61 amb λ 8 i durada mínima 1; A context amb el
    cost après, a 0,62 amb w 2, λ 4 i durada mínima 12; A canvis, a 0,60 + guany amb w 4, λ 8 i durada mínima 1; tots,
    a 0,40 amb una altra combinació."""
    millors = {t3e.CONTEXT: ((math.nan, 4.0, 12), 0.0), t3h.CONTACTE: ((math.nan, 8.0, 1), 0.01),
               t3i.CONTEXT_CANVIS: ((2.0, 4.0, 12), 0.02), t3i.CANVIS: ((4.0, 8.0, 1), None)}
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
                          {**comu, "metode": metode, "w": altre_w, "lam": 2.0, "d_min": 25, "spell_f1": 0.40}]
    return pd.DataFrame(files)


def als_quarts(dins: float, fora: float) -> dict[str, float]:
    return {e: (dins if e in t3.QUARTS else fora) for e in t3.ESCENARIS}


def test_la_tria_de_cada_metode():
    metodes, triades = t3i.tria_sense_mirar(graella(als_quarts(0.06, 0.0)))
    esperat = {t3e.CONTEXT: (4.0, 12), t3h.CONTACTE: (8.0, 1), t3i.CONTEXT_CANVIS: (2.0, 4.0, 12),
               t3i.CANVIS: (4.0, 8.0, 1)}
    assert all(t == esperat for t in triades.values())
    assert len(metodes) == len(t3i.METODES) * len(fonts.NOMS) * len(t3.ESCENARIS)


@pytest.mark.parametrize(("dins", "perd", "passa"), [(0.06, -0.03, {"quarts": True, "altres": True}),
                                                     (0.06, -0.05, {"quarts": True, "altres": False}),
                                                     (0.03, 0.0, {"quarts": False, "altres": True})])
def test_el_criteri_es_contra_a_context(dins: float, perd: float, passa: dict[str, bool]):
    metodes, _ = t3i.tria_sense_mirar(graella(als_quarts(dins, perd)))
    assert t3b.compleix(t3b.comparacio(metodes, t3i.CANVIS, t3e.CONTEXT)) == passa


def test_l_informe():
    metodes, triades = t3i.tria_sense_mirar(graella(als_quarts(0.06, 0.0)))
    c = t3b.comparacio(metodes, t3i.CANVIS, t3e.CONTEXT)
    c_contacte = t3b.comparacio(metodes, t3i.CANVIS, t3h.CONTACTE)
    c_context = t3b.comparacio(metodes, t3i.CONTEXT_CANVIS, t3e.CONTEXT)
    md = t3i.markdown(c, c_contacte, c_context, metodes, triades, t3b.compleix(c))
    assert "## A canvis contra A context (spellF1): el criteri" in md and "**Passa.**" in md
    assert "## A canvis contra A contacte (spellF1), només per saber-ho" in md
    assert "## A context amb el cost après contra A context (spellF1), només per saber-ho" in md
    assert "## Possessions predites per cada real" in md and "0.75" in md
    assert "A canvis: w = 4, λ = 8, durada mínima 1 (10 partits)" in md and "nan" not in md
