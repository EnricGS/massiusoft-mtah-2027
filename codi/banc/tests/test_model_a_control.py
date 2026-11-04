"""T3d al banc: A amb els senyals del control, la tria sense mirar el partit que es puntua i el criteri del pla."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from banc import decodificador_tocs as t3
from banc import fonts
from banc import model_a_control as t3d
from banc import model_a_dos_errors as t3c
from banc import model_a_quart as t3b
from banc.tests import sintetic
from cadena import control, senyals


def test_la_taula_son_els_senyals_d_a_i_els_del_control():
    p = sintetic.partit(n=3000)
    x = t3d.taula(p)
    assert list(x.columns) == [*senyals.calcula(p.tracking, p.trams).columns,
                               *control.calcula(p.tracking, p.trams).columns]
    assert len(x) == p.n and t3d.ENTRENAMENT == t3c.ENTRENAMENT


def test_sense_entrenar_s_atura_si_no_hi_ha_les_probabilitats(tmp_path, monkeypatch):
    monkeypatch.setattr(t3d, "DIR_CAU", tmp_path)
    with pytest.raises(RuntimeError, match="A control"):
        t3d.probabilitats(fonts.NOMS[0], entrena=False)


def graella(guany: dict[str, float]) -> pd.DataFrame:
    """Cada classificador, a 0,40 amb λ 2; A ×1+×¼, a 0,50 amb λ 8; A control, a 0,50 + guany amb λ 4."""
    millors = {t3c.DOS: (8.0, False), t3d.CONTROL: (4.0, True)}
    files = []
    for i, nom in enumerate(fonts.NOMS):
        font = "dfl" if i < 7 else "metrica"
        soroll = 0.01 * ((i % 3) - 1)
        for escenari in t3.ESCENARIS:
            comu = {"partit": nom, "font": font, "escenari": escenari, "macro_f1": 0.8}
            for metode, (lam, nou) in millors.items():
                spell = 0.50 + (guany[escenari] + soroll if nou else 0.0)
                files += [{**comu, "metode": metode, "lam": lam, "d_min": 25, "spell_f1": spell},
                          {**comu, "metode": metode, "lam": 2.0, "d_min": 1, "spell_f1": 0.40}]
    return pd.DataFrame(files)


def als_quarts(dins: float, fora: float) -> dict[str, float]:
    return {e: (dins if e in t3.QUARTS else fora) for e in t3.ESCENARIS}


def test_la_tria_de_cada_classificador():
    metodes, triades = t3d.tria_sense_mirar(graella(als_quarts(0.06, 0.0)))
    assert all(t == {t3c.DOS: (8.0, 25), t3d.CONTROL: (4.0, 25)} for t in triades.values())
    assert set(metodes["metode"]) == set(t3d.CLASSIFICADORS)
    assert len(metodes) == 2 * len(fonts.NOMS) * len(t3.ESCENARIS)
    net = metodes[metodes["escenari"] == "net"].groupby("metode")["spell_f1"].mean()
    assert np.isclose(net[t3c.DOS], 0.50) and np.isclose(net[t3d.CONTROL], 0.50, atol=0.002)


@pytest.mark.parametrize(("dins", "perd", "passa"), [(0.06, -0.03, {"quarts": True, "altres": True}),
                                                     (0.06, -0.05, {"quarts": True, "altres": False}),
                                                     (0.03, 0.0, {"quarts": False, "altres": True})])
def test_el_criteri_contra_a_dos_errors(dins: float, perd: float, passa: dict[str, bool]):
    metodes, _ = t3d.tria_sense_mirar(graella(als_quarts(dins, perd)))
    assert t3b.compleix(t3b.comparacio(metodes, t3d.CONTROL, t3c.DOS)) == passa


def test_l_informe():
    metodes, triades = t3d.tria_sense_mirar(graella(als_quarts(0.06, 0.0)))
    c = t3b.comparacio(metodes, t3d.CONTROL, t3c.DOS)
    md = t3d.markdown(c, metodes, triades, t3b.compleix(c))
    assert "## A control contra A ×1+×¼ (spellF1): el criteri" in md and "**Passa.**" in md
    assert "nan" not in md and "A control: λ = 4, durada mínima 25 (10 partits)" in md
