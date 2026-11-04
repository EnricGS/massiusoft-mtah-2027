"""L'anàlisi de la T3q: les durades, els trossos on canvia la veritat de toc, què hi dona el model, el sostre i les
taules."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from banc import analisi_t3q as an
from banc import model_a_toc as mt
from possessio.oficial import possession_metrics as pm

H, A, D = pm.H, pm.A, pm.D


@pytest.mark.parametrize(("imatges", "tram"), [(3, "<0,48 s"), (12, "0,48-1 s"), (24, "0,48-1 s"), (25, "1-2 s"),
                                               (124, "2-5 s"), (125, "≥5 s")])
def test_el_tram_de_durada(imatges, tram):
    assert an.durada(imatges) == tram


def _veritats():
    """Un rebot (A, imatges 2-4: tota la possessió és nova) i un canvi tard (A d'abans a les imatges 8-10)."""
    sempre = np.array([H] * 8 + [H, H, A, A, D, D], dtype=np.int8)
    toc = np.array([H, H, A, A, H, H, H, H] + [A, A, A, A, D, D], dtype=np.int8)
    return sempre, toc


def test_els_trossos_noves_i_avancats():
    sempre, toc = _veritats()
    assert an.trossos(sempre, toc, [(0, len(toc))]) == [(2, 4, an.NOVA), (8, 10, an.AVANCAT)]


def test_sense_canvis_no_hi_ha_trossos():
    sempre, _ = _veritats()
    assert an.trossos(sempre, sempre, [(0, len(sempre))]) == []


def test_la_mena_de_cada_imatge():
    m = an.menes(6, [(1, 3, an.NOVA), (4, 5, an.AVANCAT)])
    assert m.tolist() == [an.RESTA, an.NOVA, an.NOVA, an.RESTA, an.AVANCAT, an.RESTA]


def test_que_dona_el_model():
    toc = np.array([H, H, A, A], dtype=np.int8)
    assert an.que_dona(np.array([H, A, D, A]), toc).tolist() == ["toc", "altre", "D", "toc"]


def test_amb_la_veritat_no_toca_la_prediccio():
    sempre, toc = _veritats()
    pred = sempre.copy()
    nova = an.amb_la_veritat(pred, toc, [(2, 4, an.NOVA)])
    assert nova[2:4].tolist() == [A, A] and np.array_equal(nova[4:], sempre[4:])
    assert np.array_equal(pred, sempre)


def test_les_imatges_per_mena_i_pilota():
    sempre, toc = _veritats()
    mena = an.menes(len(toc), an.trossos(sempre, toc, [(0, len(toc))]))
    vista = np.ones(len(toc), dtype=bool)
    files = pd.DataFrame(an.imatges({}, sempre, toc, toc, mena, vista))
    nova = files[(files["mena"] == an.NOVA) & files["pilota"]].set_index("moment")
    assert nova.loc["abans", ["imatges", "toc", "altre", "D"]].tolist() == [2, 0, 2, 0]
    assert nova.loc["després", ["imatges", "toc", "altre", "D"]].tolist() == [2, 2, 0, 0]
    resta = files[(files["mena"] == an.RESTA) & files["pilota"] & (files["moment"] == "abans")]
    assert resta["imatges"].item() == 8                   # la D no és en joc


def test_el_sostre_es_el_guany_sobre_a_xarxes():
    spell = pd.DataFrame({"escenari": "net", "metode": [mt.XARXES, mt.XARXES, mt.A_TOC],
                          "spell_f1": [0.5, 0.7, 0.9]})
    so = pd.DataFrame([{"escenari": "net", "sostre": s, "spell_f1": 0.6 + 0.1 * i} for i, s in enumerate(an.SOSTRES)])
    t = an.taula_sostre(spell, so)
    assert t.loc["net", mt.XARXES] == pytest.approx(0.6)
    assert t.loc["net", "guany: totes"] == pytest.approx(0.0)
    assert t.loc["net", "guany: les avançades"] == pytest.approx(0.2)


def test_l_ordre_no_es_l_alfabetic():
    t = pd.DataFrame({"x": [1, 2, 3]}, index=pd.Index(["partit ×¼", "net", "curts ×¼"], name="escenari"))
    assert an.ordena(t).index.tolist() == ["net", "curts ×¼", "partit ×¼"]


def _taules():
    sempre, toc = _veritats()
    trossos = an.trossos(sempre, toc, [(0, len(toc))])
    mena, vista = an.menes(len(toc), trossos), np.arange(len(toc)) % 2 == 0
    imatges, possessions = [], []
    for metode in an.METODES:
        c = {"partit": "p", "font": "dfl", "escenari": "net", "metode": metode}
        imatges += an.imatges(c, sempre, toc, toc, mena, vista)
        possessions += an.possessions(c, sempre, toc, [(0, len(toc))])
    veritat = [{"font": "dfl", "mena": m, "durada": an.durada(b - a), "imatges": b - a} for a, b, m in trossos]
    return pd.DataFrame(veritat), pd.DataFrame(imatges), pd.DataFrame(possessions)


def test_les_taules_es_poden_escriure():
    veritat, imatges, possessions = _taules()
    tv = an.taula_veritat(veritat)
    assert tv["part de les imatges que canvien"].sum() == pytest.approx(1.0)
    ti = an.taula_imatges(imatges, "toc")
    assert ti.loc[("net", an.NOVA, True), f"{mt.XARXES} · després"] == pytest.approx(1.0)
    assert ti.loc[("net", an.NOVA, True), f"{mt.A_TOC} · abans"] == pytest.approx(0.0)
    assert ti.loc[("net", an.NOVA, True), "n imatges"] == 1
    tp = an.taula_possessions(possessions)
    assert list(tp.columns) == [*an.METODES, *(f"n {m}" for m in an.METODES)]
    for t in (tv, ti, an.taula_imatges(imatges, "D"), tp):
        assert an.an.md(t).count("\n") == len(t) + 1
