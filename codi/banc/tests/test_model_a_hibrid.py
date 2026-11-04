"""T3g al banc: la porta, la mescla, el decodificador sobre la mescla, la tria de T, el criteri del pla i l'informe."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from banc import decodificador_tocs as t3
from banc import fonts
from banc import model_a_context as t3e
from banc import model_a_hibrid as t3g
from banc import model_a_possessio as t3f
from banc import model_a_quart as t3b
from cadena import decodifica
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm


def etiqueta(*trossos: tuple[int, int]) -> np.ndarray:
    return np.concatenate([np.full(n, codi, dtype=np.int8) for codi, n in trossos])


def test_les_curtes_son_les_imatges_de_les_possessions_predites_de_menys_de_t():
    porta = etiqueta((pm.H, 100), (pm.A, 20), (pm.H, 100))
    curta = t3g.curtes(porta, [(0, len(porta))], 1.0)                 # 1 s, 25 imatges
    assert curta[100:120].all() and not curta[:100].any() and not curta[120:].any()


def test_amb_t_0_no_n_hi_ha_cap_de_curta():
    porta = etiqueta((pm.H, 100), (pm.A, 1), (pm.H, 100))
    assert not t3g.curtes(porta, [(0, len(porta))], 0.0).any()


def test_la_d_i_la_x_no_son_curtes():
    porta = etiqueta((pm.H, 100), (pm.D, 10), (pm.X, 10), (pm.H, 100))
    assert not t3g.curtes(porta, [(0, 110), (120, 220)], 2.0)[100:120].any()


def test_les_possessions_de_la_porta_son_les_de_la_metrica_cada_part_a_part():
    porta = etiqueta((pm.H, 30), (pm.H, 30))
    assert t3g.curtes(porta, [(0, 30), (30, 60)], 1.5).all()         # dues possessions de 30 imatges
    assert not t3g.curtes(porta, [(0, 60)], 1.5).any()               # una de 60


def test_la_mescla_pren_a_per_possessio_a_les_curtes_i_a_context_a_la_resta():
    context, possessio = np.zeros((5, 3)), np.ones((5, 3))
    curta = np.array([False, True, True, False, False])
    m = t3g.mescla(context, possessio, curta)
    assert np.array_equal(m[curta], possessio[curta]) and np.array_equal(m[~curta], context[~curta])


@pytest.mark.parametrize(("lam", "d_min"), [(0.0, 1), (4.0, 12), (8.0, 25)])
def test_el_decodificador_sobre_les_relatives_es_el_de_la_cadena(lam: float, d_min: int):
    rng = np.random.default_rng(3)
    proba = rng.dirichlet(np.ones(3), 600)
    prior = np.array([0.45, 0.4, 0.15])
    trams = ((1, 10, 289), (2, 300, 589))
    assert np.array_equal(t3g.per_trams(log_relativa(proba, prior), trams, lam, d_min),
                          decodifica.per_trams(proba, prior, trams, lam, d_min))


def test_la_porta_es_el_decodificador_de_la_t3f_si_els_resultats_son_del_codi_d_ara(tmp_path, monkeypatch):
    monkeypatch.setattr(t3f, "clau_dels_resultats", lambda: "ara")
    cami = tmp_path / "model-a-possessio.json"
    triades = {nom: {t3e.CONTEXT: [4.0, 12], t3f.POSSESSIO: [8.0, 12]} for nom in fonts.NOMS}
    cami.write_text(json.dumps({"clau": "ara", "triades": triades}))
    assert t3g.portes(cami) == {nom: (8.0, 12) for nom in fonts.NOMS}
    cami.write_text(json.dumps({"clau": "abans", "triades": triades}))
    with pytest.raises(RuntimeError, match="banc.model_a_possessio"):
        t3g.portes(cami)


def graella(guany: dict[str, float]) -> pd.DataFrame:
    """T = 0 (A context), a 0,60 amb λ 4 i durada mínima 12; T = 2, a 0,60 + guany amb λ 8 i durada mínima 12; la
    resta de combinacions, a 0,40."""
    files = []
    for i, nom in enumerate(fonts.NOMS):
        soroll = 0.01 * ((i % 3) - 1)
        for escenari in t3.ESCENARIS:
            comu = {"partit": nom, "font": "dfl" if i < 7 else "metrica", "escenari": escenari, "macro_f1": 0.8,
                    "possessions": 300, "possessions_reals": 400}
            for t in t3g.TS:
                for lam, d_min in ((4.0, 12), (8.0, 12), (2.0, 1)):
                    if (t, lam, d_min) == (0.0, 4.0, 12):
                        spell = 0.60
                    elif (t, lam, d_min) == (2.0, 8.0, 12):
                        spell = 0.60 + guany[escenari] + soroll
                    else:
                        spell = 0.40
                    files.append({**comu, "T": t, "lam": lam, "d_min": d_min, "part_curta": t / 10,
                                  "spell_f1": spell})
    return pd.DataFrame(files)


def als_quarts(dins: float, fora: float) -> dict[str, float]:
    return {e: (dins if e in t3.QUARTS else fora) for e in t3.ESCENARIS}


def test_a_context_es_t_0_i_l_hibrid_tria_t_lambda_i_la_durada_junts():
    metodes, triades = t3g.tria_sense_mirar(graella(als_quarts(0.06, 0.0)))
    assert all(t == {t3e.CONTEXT: (4.0, 12), t3g.HIBRID: (2.0, 8.0, 12)} for t in triades.values())
    assert len(metodes) == 2 * len(fonts.NOMS) * len(t3.ESCENARIS)
    assert set(metodes["metode"]) == {t3e.CONTEXT, t3g.HIBRID}


def test_si_cap_t_no_ajuda_l_hibrid_tria_t_0_i_es_a_context():
    metodes, triades = t3g.tria_sense_mirar(graella(als_quarts(-0.1, -0.1)))
    assert all(t[t3g.HIBRID] == (0.0, 4.0, 12) for t in triades.values())
    c = t3b.comparacio(metodes, t3g.HIBRID, t3e.CONTEXT)
    assert (c["diferencia"] == 0).all()


@pytest.mark.parametrize(("dins", "perd", "passa"), [(0.06, -0.03, {"quarts": True, "altres": True}),
                                                     (0.06, -0.05, {"quarts": True, "altres": False}),
                                                     (0.03, 0.0, {"quarts": False, "altres": True})])
def test_el_criteri_es_contra_a_context(dins: float, perd: float, passa: dict[str, bool]):
    metodes, _ = t3g.tria_sense_mirar(graella(als_quarts(dins, perd)))
    assert t3b.compleix(t3b.comparacio(metodes, t3g.HIBRID, t3e.CONTEXT)) == passa


def test_l_informe():
    files = graella(als_quarts(0.06, 0.0))
    metodes, triades = t3g.tria_sense_mirar(files)
    c = t3b.comparacio(metodes, t3g.HIBRID, t3e.CONTEXT)
    md = t3g.markdown(c, metodes, triades, t3b.compleix(c), files)
    assert "## A híbrid contra A context (spellF1): el criteri" in md and "**Passa.**" in md
    assert "## Possessions predites per cada real" in md and "0.75" in md
    assert "A híbrid: T = 2 s, λ = 8, durada mínima 12 (10 partits)" in md
    assert "| 2 s | 20 % |" in md and "nan" not in md
