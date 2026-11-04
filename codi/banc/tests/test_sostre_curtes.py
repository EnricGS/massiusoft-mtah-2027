"""El sostre de les possessions curtes: quines possessions tria cada sostre, com hi posa la veritat, el criteri i
les taules."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from banc import sostre_curtes as sc
from possessio.oficial import possession_metrics as pm

H, A, D = pm.H, pm.A, pm.D


@pytest.mark.parametrize("imatges", [1, 11, 12, 24, 25, 49, 50, 124, 125, 500])
def test_cada_durada_cau_en_un_sol_tram(imatges):
    trams = [s for s in sc.PER_DURADA if s.nom != sc.TOTES and s.tria(imatges, 1.0)]
    assert len(trams) == 1


@pytest.mark.parametrize("imatges", [1, 12, 25, 50, 124, 125])
def test_les_de_menys_de_5_s_son_els_quatre_primers_trams(imatges):
    curtes = next(s for s in sc.CURTES if s.nom == "<5 s")
    assert curtes.tria(imatges, 1.0) == any(s.tria(imatges, 1.0) for s in sc.PER_DURADA[:4])


def test_la_pilota_vista_i_amagada_es_reparteixen_les_curtes():
    vista = next(s for s in sc.CURTES if s.nom == "<5 s, pilota vista")
    amagada = next(s for s in sc.CURTES if s.nom == "<5 s, pilota amagada")
    for part in (0.0, 0.49, 0.5, 1.0):
        assert vista.tria(30, part) != amagada.tria(30, part)
    assert not vista.tria(200, 1.0) and not amagada.tria(200, 0.0)


def test_la_part_amb_la_pilota_vista():
    vista = np.array([True, False, True, True, False, False])
    assert sc.part_vista(vista, 0, 4) == pytest.approx(0.75)
    assert sc.part_vista(vista, 4, 6) == pytest.approx(0.0)


def _cas():
    """La veritat de toc: H (0-4), un rebot d'A (4-6) i H (6-10). El model no veu el rebot i hi dona H i D."""
    toc = np.array([H] * 4 + [A, A] + [H] * 4, dtype=np.int8)
    pred = np.array([H] * 4 + [H, D] + [H] * 4, dtype=np.int8)
    return toc, pred


def test_posar_la_veritat_a_les_possessions_triades():
    toc, pred = _cas()
    nova = sc.amb_la_veritat(pred, toc, [(4, 6, A)], nomes_equip=False)
    assert np.array_equal(nova, toc)
    assert pred[4:6].tolist() == [H, D]                  # la predicció no canvia


def test_nomes_l_equip_deixa_la_d():
    toc, pred = _cas()
    nova = sc.amb_la_veritat(pred, toc, [(4, 6, A)], nomes_equip=True)
    assert nova[4:6].tolist() == [A, D]


def test_quines_possessions_tria_cada_sostre():
    toc = np.array([H] * 30 + [A] * 5 + [H] * 10, dtype=np.int8)
    vista = np.arange(len(toc)) < 32
    possessions = pm.possession_spells(toc, [(0, len(toc))])
    menys_de_0_48 = next(s for s in sc.PER_DURADA if s.nom == "<0,48 s")
    assert sc.triades(possessions, menys_de_0_48, vista) == [(30, 35, A), (35, 45, H)]
    amagada = next(s for s in sc.CURTES if s.nom == "<5 s, pilota amagada")
    assert sc.triades(possessions, amagada, vista) == [(30, 35, A), (35, 45, H)]
    vista_ = next(s for s in sc.CURTES if s.nom == "<5 s, pilota vista")
    assert sc.triades(possessions, vista_, vista) == [(0, 30, H)]


def test_el_criteri_dels_quarts():
    font = np.array(["dfl"] * 7 + ["metrica"] * 3)
    passa = sc.criteri(np.full(10, 0.05), font)
    assert passa["passa"] and passa["guanya"] == 10
    nomes_set = sc.criteri(np.array([0.08] * 7 + [-0.01] * 3), font)
    assert not nomes_set["passa"] and nomes_set["guanya"] == 7       # guanya de mitjana, però només a 7 partits
    poc = sc.criteri(np.full(10, 0.03), font)
    assert not poc["passa"]


def _relativa():
    """A les imatges 0-4, A xarxes diu H; a les 4-6, una mica A i una mica H (més A en suma); sense dades a la 6."""
    r = np.zeros((7, 3))
    r[:4] = [1.0, -1.0, 0.0]
    r[4:6] = [[-0.2, 0.5, 0.0], [0.1, -0.1, 0.0]]
    r[6] = np.nan
    return r


def test_el_vot_d_a_xarxes():
    r = _relativa()
    assert sc.vot(r, 0, 4) == H
    assert sc.vot(r, 4, 7) == A                          # suma −0,1 contra +0,4, sense comptar la imatge buida


def test_les_vores_de_la_veritat_amb_el_vot():
    pred = np.array([H, H, H, H, H, D, H], dtype=np.int8)
    nova = sc.amb_les_vores(pred, _relativa(), [(4, 7, A)])
    assert nova.tolist() == [H, H, H, H, A, A, A]
    assert pred[4:].tolist() == [H, D, H]


def test_la_q_perfecta():
    toc = np.array([H] * 10 + [A] * 10, dtype=np.int8)
    q = sc.q_perfecta(toc, [(0, len(toc))])
    assert np.flatnonzero(q == sc.Q_CANVI).tolist() == list(range(4, 17))
    assert q[0] == q[19] == sc.t3i.Q_MINIM


def test_la_d_perfecta_no_toca_l_equip_fora_de_la_d():
    toc = np.array([H, H, D, D, A], dtype=np.int8)
    r = np.tile([0.3, -0.3, 0.5], (5, 1))
    nova = sc.amb_la_d(r, toc)
    assert (nova[2:4].argmax(1) == 2).all() and (nova[[0, 1, 4]].argmax(1) == 0).all()
    assert np.array_equal(nova[[0, 1, 4], :2], r[[0, 1, 4], :2])
    assert r[2, 2] == 0.5


def test_els_forats_porten_k_imatges_a_cada_banda():
    vista = np.ones(20, dtype=bool)
    vista[10] = False
    assert np.flatnonzero(sc.forats(vista, k=2)).tolist() == [8, 9, 10, 11, 12]
    assert not sc.forats(np.ones(5, dtype=bool)).any()


def test_la_taula_dels_vots():
    vots = pd.DataFrame({"escenari": "net", "durada": ["<0,48 s", "<0,48 s", "<0,48 s", "≥5 s"],
                         "pilota": [True, True, False, True], "vot": [True, False, False, True],
                         "toc": [1.0, np.nan, 0.0, 1.0]})
    t = sc.taula_vots(vots, "vot")
    assert t.loc[("net", "<0,48 s"), "pilota vista"] == pytest.approx(0.5)
    assert t.loc[("net", "<0,48 s"), "n pilota amagada"] == 1
    assert list(t.columns) == ["pilota vista", "pilota amagada", "n pilota vista", "n pilota amagada"]
    assert sc.t3p.md(t.fillna(0)).count("\n") == len(t) + 1


class _Tracking:
    """La pilota es mou per la x; el jugador d'H hi és a sobre a les imatges 0-2, i el d'A, a les 6-9."""
    camp_m = (100.0, 50.0)

    def __init__(self):
        self.pilota = np.column_stack([np.linspace(0.1, 0.2, 10), np.full(10, 0.5)])
        self.pilota[4] = np.nan
        self.casa = np.full((10, 1, 2), 0.9)
        self.fora = np.full((10, 1, 2), 0.9)
        self.casa[:3, 0] = self.pilota[:3]
        self.fora[6:, 0] = self.pilota[6:]


def test_el_toc_de_l_inici():
    d_h, d_a = sc.distancies(_Tracking())
    assert d_h[0] == pytest.approx(0.0) and np.isinf(d_h[4])
    assert sc.del_toc(d_h, d_a, 1) == H
    assert sc.del_toc(d_h, d_a, 7) == A
    assert sc.del_toc(d_h, d_a, 4, k=0) is None


def test_les_vores_de_la_veritat_amb_el_toc():
    d_h, d_a = sc.distancies(_Tracking())
    pred = np.full(10, H, dtype=np.int8)
    r = np.zeros((10, 3))
    r[:, 0] = 1.0                                        # A xarxes diu H a tot arreu
    nova = sc.amb_el_toc(pred, r, d_h, d_a, [(7, 10, A)])
    assert nova.tolist() == [H] * 7 + [A] * 3


def test_la_taula_del_toc():
    vots = pd.DataFrame({"escenari": "net", "durada": "<0,48 s", "pilota": [True, True, True],
                         "vot": [True, True, True], "toc": [1.0, np.nan, 0.0]})
    t = sc.taula_vots(vots, "toc")
    assert t.loc[("net", "<0,48 s"), "pilota vista"] == pytest.approx(0.5)
    assert t.loc[("net", "<0,48 s"), "n pilota vista"] == 2


def _files():
    files = []
    for i, partit in enumerate(["p1", "p2"]):
        comu = {"partit": partit, "font": "dfl"}
        for escenari in sc.ESCENARIS:
            files.append({**comu, "escenari": escenari, "sostre": sc.BASE, "spell_f1": 0.5, "possessions": 0})
            files += [{**comu, "escenari": escenari, "sostre": nom, "spell_f1": 0.5 + 0.01 * (j + i),
                       "possessions": j} for j, nom in enumerate((*sc.noms(sc.SOSTRES), *sc.ON))]
    return pd.DataFrame(files)


def test_la_taula_dels_guanys():
    t = sc.taula_guany(_files(), sc.noms(sc.PER_DURADA))
    assert t.loc["net", sc.BASE] == pytest.approx(0.5)
    assert t.loc["net", sc.PER_DURADA[1].nom] == pytest.approx(0.015)
    assert list(t.columns) == [sc.BASE, *(s.nom for s in sc.PER_DURADA)]
    assert sc.t3p.md(t).count("\n") == len(t) + 1


def test_la_taula_del_criteri():
    linies = sc.taula_criteri(_files(), (*sc.noms(sc.CURTES), *sc.ON))
    assert len(linies) == 2 + len(sc.CURTES) + len(sc.ON)
    assert all(linia.count("|") == 2 + len(sc.QUARTS) for linia in linies)


def test_la_taula_de_quantes_n_hi_ha():
    t = sc.taula_quantes(_files(), sc.noms(sc.CURTES))
    assert t.loc["net", f"n {sc.CURTES[2].nom}"] == 2 * (len(sc.PER_DURADA) + 2)
