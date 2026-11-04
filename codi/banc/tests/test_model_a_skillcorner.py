"""T3l al banc: els grups amb els partits de SkillCorner, que només s'entrenen; la tria dels paràmetres, el criteri del
pla contra A context i l'informe."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from banc import fonts
from banc import decodificador_tocs as t3
from banc import model_a_aturades as t3k
from banc import model_a_context as t3e
from banc import model_a_quart as t3b
from banc import model_a_skillcorner as t3l


def test_els_grups_porten_els_de_skillcorner_un_cop_i_mai_el_que_es_prova():
    for prova in fonts.NOMS:
        g = t3l.grups(prova)
        tots = [nom for grup in g for nom in grup]
        assert len(tots) == len(set(tots)) == 9 + len(fonts.NOMS_SKILLCORNER) and prova not in tots
        assert all(tuple(n for n in grup if n in fonts.NOMS) == banc for grup, banc in zip(g, t3e.grups(prova)))
        assert set(t3l.per_entrenar(prova)) == set(tots)
    assert not set(fonts.NOMS_SKILLCORNER) & set(fonts.NOMS)


def test_sense_entrenar_s_atura_si_no_hi_ha_les_probabilitats(tmp_path, monkeypatch):
    monkeypatch.setattr(t3l, "DIR_CAU", tmp_path)
    with pytest.raises(RuntimeError, match="SkillCorner"):
        t3l.probabilitats(fonts.NOMS[0], entrena=False)


def graella(guany: dict[str, float]) -> pd.DataFrame:
    """A context, a 0,60 amb λ 4 i durada mínima 12; A aturades, a 0,62 amb w 4, λ 32 i durada mínima 12; A amb
    SkillCorner, a 0,60 + guany amb w 2, λ 16 i durada mínima 1; tots, a 0,40 amb una altra combinació."""
    millors = {t3e.CONTEXT: ((math.nan, 4.0, 12), 0.0), t3k.ATURADES: ((4.0, 32.0, 12), 0.02),
               t3l.SKILLCORNER: ((2.0, 16.0, 1), None)}
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
    metodes, triades = t3l.tria_sense_mirar(graella(als_quarts(0.06, 0.0)))
    esperat = {t3e.CONTEXT: (4.0, 12), t3k.ATURADES: (4.0, 32.0, 12), t3l.SKILLCORNER: (2.0, 16.0, 1)}
    assert all(t == esperat for t in triades.values())
    assert len(metodes) == len(t3l.METODES) * len(fonts.NOMS) * len(t3.ESCENARIS)


@pytest.mark.parametrize(("dins", "perd", "passa"), [(0.06, -0.03, {"quarts": True, "altres": True}),
                                                     (0.06, -0.05, {"quarts": True, "altres": False}),
                                                     (0.03, 0.0, {"quarts": False, "altres": True})])
def test_el_criteri_es_contra_a_context(dins: float, perd: float, passa: dict[str, bool]):
    metodes, _ = t3l.tria_sense_mirar(graella(als_quarts(dins, perd)))
    assert t3b.compleix(t3b.comparacio(metodes, t3l.SKILLCORNER, t3e.CONTEXT)) == passa


def test_l_informe():
    metodes, triades = t3l.tria_sense_mirar(graella(als_quarts(0.06, 0.0)))
    c = t3b.comparacio(metodes, t3l.SKILLCORNER, t3e.CONTEXT)
    c_aturades = t3b.comparacio(metodes, t3l.SKILLCORNER, t3k.ATURADES)
    enc = pd.DataFrame([{"partit": "p", "escenari": e, "metode": m, "durada": d, "pilota": v, "encert": 0.7,
                         "imatges": 10} for e in t3.QUARTS for m in (t3k.ATURADES, t3l.SKILLCORNER)
                        for d in t3l.NOMS_DURADA for v in (False, True)])
    ver = pd.DataFrame([{"partit": f"{f}-{i}", "font": f, "sense_veritat": 0.25, "d": 0.3, "possessions_min": 4.4,
                         "durada_mediana": 5.9, "menys_2s": 0.22, "pilota_viva": 0.95}
                        for f in ("dfl", "metrica", "skillcorner") for i in range(2)])
    md = t3l.markdown(c, c_aturades, metodes, enc, ver, triades, t3b.compleix(c))
    assert "## A amb SkillCorner contra A context (spellF1): el criteri" in md and "**Passa.**" in md
    assert "## A amb SkillCorner contra A aturades (spellF1), només per saber-ho" in md
    assert "| <1 s | sí | 0.700 | 0.700 |" in md and "| skillcorner | 2 | 0.250 | 0.300 | 4.40 |" in md
    assert "A amb SkillCorner: w = 2, λ = 16, durada mínima 1 (10 partits)" in md and "nan" not in md
