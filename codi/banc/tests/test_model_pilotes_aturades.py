"""El sostre de les pilotes aturades (T3af, pas 1): la veritat al voltant de cada represa que el nivell no perd, i la
regla per fer el pas 2."""

from __future__ import annotations

import numpy as np
import pandas as pd

from banc import model_pilotes_aturades as mpa
from banc import smart_tagging_simulat as sts
from possessio.oficial import possession_metrics as pm

H, A, D = pm.H, pm.A, pm.D


def test_sense_cap_represa_guardada_es_la_predicció_tal_qual():
    pred = np.random.default_rng(0).choice(np.array([H, A, D], np.int8), 3000)
    toc = np.full(3000, H, dtype=np.int8)
    represes = (sts.Represa(500, "falta", H), sts.Represa(1500, "banda", H))
    x = mpa.sostre(pred, toc, ((1, 0, 2999),), represes, ())
    np.testing.assert_array_equal(x, pred)
    assert x is not pred


def test_la_veritat_des_de_la_d_fins_a_3_s_despres():
    toc = np.r_[np.full(100, H), np.full(50, D), np.full(150, H)].astype(np.int8)
    pred = np.full(300, A, dtype=np.int8)
    x = mpa.sostre(pred, toc, ((1, 0, 299),), (sts.Represa(150, "falta", H),), (0,))
    np.testing.assert_array_equal(x[:100], A)
    np.testing.assert_array_equal(x[100:150], D)
    np.testing.assert_array_equal(x[150:225], H)
    np.testing.assert_array_equal(x[225:], A)


def test_30_s_enrere_com_a_maxim_i_dins_de_la_part():
    toc = np.r_[np.full(1000, D), np.full(200, H)].astype(np.int8)
    pred = np.full(1200, A, dtype=np.int8)
    x = mpa.sostre(pred, toc, ((1, 0, 1199),), (sts.Represa(1000, "porta", H),), (0,))
    assert (x[:250] == A).all() and (x[250:1000] == D).all() and (x[1000:1075] == H).all() and (x[1075:] == A).all()
    x = mpa.sostre(pred, toc, ((1, 0, 899), (2, 900, 1049)), (sts.Represa(1000, "porta", H),), (0,))
    assert (x[:900] == A).all() and (x[900:1000] == D).all() and (x[1000:1050] == H).all() and (x[1050:] == A).all()


def test_nomes_les_represes_guardades():
    toc = np.r_[np.full(100, D), np.full(200, H), np.full(100, D), np.full(200, A)].astype(np.int8)
    pred = np.full(600, H, dtype=np.int8)
    represes = (sts.Represa(100, "falta", H), sts.Represa(400, "corner", A))
    x = mpa.sostre(pred, toc, ((1, 0, 599),), represes, (1,))
    assert (x[:300] == H).all() and (x[300:400] == D).all() and (x[400:475] == A).all() and (x[475:] == H).all()


def test_la_regla_del_pas_2():
    quarts = {q: 0.012 for q in mpa.QUARTS_T3}
    fila = lambda e, d: {"escenari": e, "nivell": "mitjà", "neteja": 0.5, "sostre": 0.5 + d}  # noqa: E731
    t = pd.DataFrame([fila(e, d) for e, d in {**quarts, mpa.PARTIT: 0.010, "net": 0.0}.items()]
                     + [fila(mpa.PARTIT, 0.0) | {"nivell": "bo"}])
    assert mpa.cal_el_pas_2(t) == {"partit": True, "quarts": True}
    t.loc[t["escenari"] == mpa.PARTIT, "sostre"] = 0.5 + 0.0099
    assert mpa.cal_el_pas_2(t) == {"partit": False, "quarts": True}
    t.loc[t["escenari"] == mpa.QUARTS_T3[0], "sostre"] = 0.5 + 0.006            # mitjana dels quatre: 0,0105
    assert mpa.cal_el_pas_2(t)["quarts"]
    t.loc[t["escenari"] == mpa.QUARTS_T3[1], "sostre"] = 0.5 + 0.004            # 0,0085
    assert not mpa.cal_el_pas_2(t)["quarts"]


def test_cap_peca_no_apren_amb_el_partit_que_es_prova():
    from banc import fonts
    for prova in fonts.NOMS:
        claus = mpa.per_aprendre(prova)
        assert all(nom != prova for nom, _ in claus)
        assert len(claus) == len(set(claus)) == (len(fonts.NOMS) - 1) * len(mpa.SIS)


def test_les_columnes_del_smart_tagging_s_afegeixen_a_la_taula_del_segon():
    base = pd.DataFrame({"pr_h": np.linspace(0, 1, 600), "dif_x": np.arange(600.0)})
    taula = mpa.amb_les_etiquetes(base, (sts.st.Etiqueta(100, 150, "corner", H),), ((1, 0, 599),))
    assert list(taula.columns) == [*base.columns, *sts.st.COLUMNES] and len(taula) == len(base)
    pd.testing.assert_frame_equal(taula[base.columns], base)
    assert taula.loc[100, "st_abans_corner"] == 1 and taula.loc[100, "st_dins"] == 1


def test_a_prop_de_les_represes():
    m = mpa.a_prop((sts.Represa(200, "falta", H), sts.Represa(990, "banda", A)), 1000, ((1, 0, 499), (2, 500, 999)))
    assert m[[75, 200, 325, 865, 999]].all() and not m[[74, 326, 864]].any()
    assert m.sum() == 251 + 135


def test_aguanta_amb_etiquetes_dolentes_i_sense():
    fila = lambda e, d: {"escenari": e, "diferencia": d}  # noqa: E731
    bo = pd.DataFrame([fila(e, -0.005) for e in mpa.QUARTS] + [fila("net", -0.03)])
    assert mpa.aguanta({"dolent": bo, "cap": bo}) == {"dolent": True, "cap": True}
    dolent = bo.assign(diferencia=np.where(bo["escenari"] == mpa.PARTIT, -0.0051, bo["diferencia"]))
    assert mpa.aguanta({"dolent": dolent, "cap": bo}) == {"dolent": False, "cap": True}
