"""Per què no passa la T3r: els canvis que fa el decodificador, la q perfecta només en una banda, la q com a
classificador, la comprovació amb el banc i les taules."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from banc import analisi_t3r as an
from banc import model_a_canvis as t3i
from banc import model_a_canvis2 as t3j
from banc import sostre_curtes as sc


def test_a_prop_mira_el_mes_proper_de_l_altra_llista():
    de = np.array([10, 50, 100])
    assert an.a_prop(de, np.array([70, 12]), 5).tolist() == [True, False, False]
    assert an.a_prop(de, np.array([70, 12]), 20).tolist() == [True, True, False]
    assert an.a_prop(de, np.array([], dtype=int), 20).tolist() == [False, False, False]
    assert an.a_prop(np.array([], dtype=int), np.array([5]), 20).tolist() == []


def test_els_canvis_es_compten_amb_la_pilota_i_als_forats():
    al_forat = np.zeros(1000, dtype=bool)
    al_forat[480:520] = al_forat[880:920] = True
    files = an.compta_canvis(np.array([100, 500]), np.array([102, 300, 900]), al_forat, tol=10)
    per_on = {f["on"]: f for f in files}
    assert per_on[an.AMB_PILOTA] == {"on": an.AMB_PILOTA, "n reals": 1, "n trobats": 1, "n predits": 2,
                                     "n encertats": 1}
    assert per_on[an.ALS_FORATS] == {"on": an.ALS_FORATS, "n reals": 1, "n trobats": 0, "n predits": 1,
                                     "n encertats": 0}


def test_la_q_perfecta_en_una_sola_banda():
    q = np.array([0.2, 0.4, 0.6, 0.8])
    a_prop = np.array([True, False, True, False])
    assert an.q_als_canvis(q, a_prop).tolist() == [sc.Q_CANVI, 0.4, sc.Q_CANVI, 0.8]
    assert an.q_fora_dels_canvis(q, a_prop).tolist() == [0.2, t3i.Q_MINIM, 0.6, t3i.Q_MINIM]


def test_la_q_com_a_classificador():
    a_prop = np.array([True, True, False, False, False, False])
    q = np.array([0.9, 0.8, 0.1, 0.5, 0.2, 0.95])
    tria = np.array([True, True, True, True, True, False])
    r = an.classificador(q, a_prop, tria)
    assert r["auc"] == pytest.approx(1.0)
    assert r["alarmes"] == pytest.approx(1 / 3)
    assert t3j.Q_ALTA == 0.3
    sense_canvis = an.classificador(q, a_prop, np.array([False, False, True, True, True, False]))
    assert np.isnan(sense_canvis["auc"]) and sense_canvis["alarmes"] == pytest.approx(1 / 3)


def banc_de_prova() -> pd.DataFrame:
    files = []
    for metode in (an.XARXES, an.A_Q):
        for w in (4.0, 8.0):
            for veritat, f in ((an.TOC, 0.70), (an.SEMPRE, 0.75)):
                files.append({"partit": "dfl-x", "escenari": "net", "metode": metode, "veritat": veritat, "w": w,
                              "lam": 32.0, "d_min": 12, "spell_f1": f + (0.01 if w == 4.0 else 0.0)
                              + (0.001 if metode == an.A_Q else 0.0)})
    return pd.DataFrame(files)


def test_les_prediccions_han_de_ser_les_del_banc(monkeypatch):
    monkeypatch.setattr(an, "files_del_banc", banc_de_prova)
    monkeypatch.setattr(an, "triades", lambda: {an.XARXES_TOC: {"dfl-x": [4.0, 32.0, 12]},
                                                an.A_Q: {"dfl-x": [8.0, 32.0, 12]}})
    aqui = pd.DataFrame([{"partit": "dfl-x", "escenari": "net", "sostre": an.XARXES, "spell_f1": 0.71},
                         {"partit": "dfl-x", "escenari": "net", "sostre": an.A_Q, "spell_f1": 0.701},
                         {"partit": "dfl-x", "escenari": "net", "sostre": sc.Q_PERFECTA, "spell_f1": 0.9}])
    an.comprova(aqui)
    with pytest.raises(RuntimeError):
        an.comprova(aqui.assign(spell_f1=[0.71, 0.711, 0.9]))
    with pytest.raises(RuntimeError):
        an.comprova(aqui[aqui["sostre"] != an.A_Q])


def test_la_taula_dels_canvis():
    canvis = pd.DataFrame([
        {"partit": p, "escenari": "net", "metode": m, "on": an.AMB_PILOTA, "n reals": 10, "n trobats": t,
         "n predits": n, "n encertats": e}
        for p in ("a", "b") for m, t, n, e in ((an.XARXES, 6, 8, 4), (an.A_Q, 8, 12, 6))])
    t = an.taula_canvis(canvis)
    fila = t.loc[("net", an.AMB_PILOTA)]
    assert fila["n reals"] == 20
    assert fila[f"n predits · {an.XARXES}"] == 16 and fila[f"n predits · {an.A_Q}"] == 24
    assert fila[f"troba · {an.XARXES}"] == pytest.approx(0.6) and fila[f"troba · {an.A_Q}"] == pytest.approx(0.8)
    assert fila[f"encerta · {an.XARXES}"] == pytest.approx(0.5)
