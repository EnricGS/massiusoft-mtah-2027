"""Per què no passa la T3s: quines arregla cada llindar, encerta i troba, la probabilitat per trams, la part
d'inventades als grups i al banc, i la comprovació amb el banc."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from banc import analisi_t3s as an


def test_quines_arregla_cada_llindar():
    prob = np.array([0.2, 0.5, 0.9])
    assert an.amb(0.5, prob).tolist() == [False, True, True]
    assert an.amb(an.av.MAI, prob).tolist() == [False, False, False]


def test_encerta_i_troba():
    po = pd.DataFrame({"inventada": [True, True, False, False, True]})
    r = an.encerta_i_troba(po, np.array([True, False, True, False, False]))
    assert r == {"n arreglades": 2, "encerta": pytest.approx(0.5), "troba": pytest.approx(1 / 3)}
    assert np.isnan(an.encerta_i_troba(po, np.zeros(5, dtype=bool))["encerta"])


def test_la_probabilitat_per_trams():
    possessions = pd.DataFrame({"dins": [True, True, True, True, False], "escenari": ["curts ×¼"] * 4 + ["curts ×¼"],
                                "prob": [0.05, 0.08, 0.6, 0.65, 0.9], "inventada": [False, True, True, True, True]})
    t = an.taula_calibratge(possessions)
    assert t.index.tolist() == ["0-0.1", "0.5-0.7"]
    assert t["n possessions"].tolist() == [2, 2]
    assert t["inventades"].tolist() == pytest.approx([0.5, 1.0])


def test_la_part_d_inventades_als_grups_i_al_banc():
    entrenar = pd.DataFrame([{"escenari": e, "on": on, "size": 100, "sum": s}
                             for e in an.SIS for on, s in ((an.GRUPS, 8), (an.BANC, 5))])
    t = an.taula_entrenar(entrenar)
    assert t.index.tolist() == list(an.SIS)
    assert t[an.GRUPS].tolist() == pytest.approx([0.08] * 6) and t[an.BANC].tolist() == pytest.approx([0.05] * 6)


def test_ha_de_donar_el_del_banc(monkeypatch):
    banc = {"files": [{"partit": "x", "escenari": "net", "metode": m, "spell_f1": f}
                      for m, f in ((an.BASE, 0.7), (an.TRIAT, 0.71))]}
    monkeypatch.setattr(an, "del_banc_t3s", lambda: banc)
    aqui = pd.DataFrame([{"partit": "x", "escenari": "net", "sostre": s, "spell_f1": f}
                         for s, f in ((an.BASE, 0.7), (an.TRIAT, 0.71), (an.NOMES_BONES, 0.6))])
    an.comprova(aqui)
    with pytest.raises(RuntimeError):
        an.comprova(aqui.assign(spell_f1=[0.7, 0.72, 0.6]))
