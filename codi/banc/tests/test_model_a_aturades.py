"""T3k al banc: la taula del segon amb els senyals de l'aturada, les vores de les aturades, la tria dels paràmetres,
el criteri del pla i l'informe."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from banc import fonts
from banc import decodificador_tocs as t3
from banc import model_a_aturades as t3k
from banc import model_a_canvis as t3i
from banc import model_a_contacte as t3h
from banc import model_a_context as t3e
from banc import model_a_quart as t3b
from banc.tests import sintetic
from possessio.oficial import possession_metrics as pm


def etiqueta(*trossos: tuple[int, int]) -> np.ndarray:
    return np.concatenate([np.full(n, codi, dtype=np.int8) for codi, n in trossos])


def test_la_taula_del_segon_es_la_d_a_contacte_i_les_aturades():
    p = sintetic.partit(n=3000)
    primer = np.random.default_rng(1).dirichlet(np.ones(3), p.n)
    t = t3k.taula_segon(p, primer)
    base = t3h.taula_segon(p, primer)
    assert len(t) == p.n and list(t.columns[:len(base.columns)]) == list(base.columns)
    assert all(c.startswith("aturada_") for c in t.columns[len(base.columns):]) and "aturada_frenen" in t.columns


def test_les_vores_de_les_aturades():
    veritat = etiqueta((pm.H, 100), (pm.D, 50), (pm.A, 100), (pm.D, 10), (pm.H, 100))
    pred = etiqueta((pm.H, 110), (pm.D, 40), (pm.A, 110), (pm.H, 100))          # l'una, tard i bé; l'altra, no
    v = t3k.vores(veritat, pred, [(0, len(veritat))])
    assert v[0] == {"trobada": True, "inici_s": 10 / 25, "represa_s": 0.0}
    assert v[1]["trobada"] is False and math.isnan(v[1]["inici_s"])
    r = t3k.resum_de_les_vores(pd.DataFrame([{"escenari": "e", "metode": "m", **f} for f in v]))
    assert r.iloc[0][["trobades", "inici", "represa"]].tolist() == [0.5, 0.0, 0.0]


def test_sense_entrenar_s_atura_si_no_hi_ha_les_probabilitats(tmp_path, monkeypatch):
    monkeypatch.setattr(t3k, "DIR_CAU", tmp_path)
    with pytest.raises(RuntimeError, match="A aturades"):
        t3k.probabilitats(fonts.NOMS[0], entrena=False)


def graella(guany: dict[str, float]) -> pd.DataFrame:
    """A context, a 0,60 amb λ 4 i durada mínima 12; A canvis, a 0,62 amb w 4, λ 16 i durada mínima 12; A aturades,
    a 0,60 + guany amb w 2, λ 32 i durada mínima 1; tots, a 0,40 amb una altra combinació."""
    millors = {t3e.CONTEXT: ((math.nan, 4.0, 12), 0.0), t3i.CANVIS: ((4.0, 16.0, 12), 0.02),
               t3k.ATURADES: ((2.0, 32.0, 1), None)}
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
    metodes, triades = t3k.tria_sense_mirar(graella(als_quarts(0.06, 0.0)))
    esperat = {t3e.CONTEXT: (4.0, 12), t3i.CANVIS: (4.0, 16.0, 12), t3k.ATURADES: (2.0, 32.0, 1)}
    assert all(t == esperat for t in triades.values())
    assert len(metodes) == len(t3k.METODES) * len(fonts.NOMS) * len(t3.ESCENARIS)


@pytest.mark.parametrize(("dins", "perd", "passa"), [(0.06, -0.03, {"quarts": True, "altres": True}),
                                                     (0.06, -0.05, {"quarts": True, "altres": False}),
                                                     (0.03, 0.0, {"quarts": False, "altres": True})])
def test_el_criteri_es_contra_a_context(dins: float, perd: float, passa: dict[str, bool]):
    metodes, _ = t3k.tria_sense_mirar(graella(als_quarts(dins, perd)))
    assert t3b.compleix(t3b.comparacio(metodes, t3k.ATURADES, t3e.CONTEXT)) == passa


def test_l_informe():
    metodes, triades = t3k.tria_sense_mirar(graella(als_quarts(0.06, 0.0)))
    c = t3b.comparacio(metodes, t3k.ATURADES, t3e.CONTEXT)
    c_canvis = t3b.comparacio(metodes, t3k.ATURADES, t3i.CANVIS)
    v = pd.DataFrame([{"escenari": e, "metode": m, "trobades": 0.95, "inici": inici, "represa": 0.2}
                      for e in t3.QUARTS for m, inici in ((t3i.CANVIS, 0.37), (t3k.ATURADES, 0.3))])
    md = t3k.markdown(c, c_canvis, metodes, v, triades, t3b.compleix(c))
    assert "## A aturades contra A context (spellF1): el criteri" in md and "**Passa.**" in md
    assert "## A aturades contra A canvis (spellF1), només per saber-ho" in md
    assert f"| {t3.QUARTS[0]} | A aturades | 0.950 | 0.300 | 0.200 |" in md
    assert "## Possessions predites per cada real" in md and "0.75" in md
    assert "A aturades: w = 2, λ = 32, durada mínima 1 (10 partits)" in md and "nan" not in md
