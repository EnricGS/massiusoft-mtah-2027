"""ISSIA-CNR i la prova de FootAndBall: com es llegeixen les anotacions, i què compta com a trobada. Sense PyTorch."""

from __future__ import annotations

import numpy as np

from pilota import footandball, issia, prova_issia

XGTF = """<?xml version="1.0" encoding="UTF-8"?>
<viper xmlns="http://lamp.cfar.umd.edu/viper#" xmlns:data="http://lamp.cfar.umd.edu/viperdata#">
<data><sourcefile filename="x.avi">
<object framespan="10:20" id="0" name="BALL">
  <attribute name="BallPos">
    <data:point framespan="10:11" x="100" y="200"/>
    <data:point framespan="14:14" x="105" y="210"/>
  </attribute>
  <attribute name="BallShot"><data:bvalue framespan="10:20" value="false"/></attribute>
  <attribute name="PlayerInteractingID">
    <data:dvalue framespan="10:13" value="-1"/>
    <data:dvalue framespan="14:15" value="7"/>
  </attribute>
</object>
<object framespan="10:20" id="1" name="Person"><attribute name="BallPos"/></object>
</sourcefile></data></viper>
"""


def test_les_anotacions_van_a_la_imatge_del_video_vuit_abans(tmp_path):
    cami = tmp_path / "a.xgtf"
    cami.write_text(XGTF, encoding="utf-8")
    a = issia.llegeix(cami, imatges=20)
    amb = np.flatnonzero(~np.isnan(a.pilota[:, 0]))
    np.testing.assert_array_equal(amb, [2, 3, 6])
    np.testing.assert_array_equal(a.pilota[6], [105, 210])
    np.testing.assert_array_equal(np.flatnonzero(a.toc), [6, 7])


def test_a_les_cameres_girades_la_x_es_l_amplada_menys_la_marcada(tmp_path):
    cami = tmp_path / "a.xgtf"
    cami.write_text(XGTF, encoding="utf-8")
    a = issia.llegeix(cami, imatges=20, girada_a=1920)
    np.testing.assert_array_equal(a.pilota[2], [1820, 200])
    assert 6 in issia.GIRADES and 5 not in issia.GIRADES


def test_la_trobada_es_la_mes_probable_si_passa_del_llindar_i_es_a_prop():
    marcada = np.array([[100.0, 100.0], [100.0, 100.0], [np.nan, np.nan]])
    cand = np.full((3, 2, 3), np.nan)
    cand[0] = [[104, 100, 0.9], [500, 500, 0.2]]          # trobada, a 4 px
    cand[1] = [[500, 500, 0.8], [101, 100, 0.6]]          # la més probable és lluny; la bona, entre les candidates
    cand[2] = [[300, 300, 0.95], [0, 0, 0.1]]             # sense pilota marcada, en dona una
    r = prova_issia.mesura(cand, marcada, llindar=0.5)
    assert r["marcades"] == 2 and r["trobada"] == 0.5 and r["entre_les_candidates"] == 1.0
    assert r["error_px"] == 4.0
    assert r["sense_marcar"] == 1 and r["en_dona_sense_marcar"] == 1.0
    assert prova_issia.mesura(cand, marcada, llindar=0.99)["trobada"] == 0.0


def test_la_imatge_s_omple_fins_a_multiples_de_32_i_es_normalitza_com_a_l_entrenament():
    imatge = np.zeros((1080, 1920, 3), np.uint8)
    imatge[..., 2] = 255                                   # vermell en BGR
    omplerta = footandball.omple(imatge)
    assert omplerta.shape == (1088, 1920, 3) and omplerta[1080:].sum() == 0
    t = footandball.a_tensor(imatge[:2, :2])
    assert t.shape == (1, 3, 2, 2)
    np.testing.assert_allclose(t[0, :, 0, 0], (np.array([1.0, 0, 0]) - footandball.MITJANA) / footandball.DESVIACIO,
                               rtol=1e-6)
