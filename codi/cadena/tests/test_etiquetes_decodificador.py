"""Les etiquetes de pilota aturada al decodificador (T3ag): què sumen a la probabilitat relativa, on i quant."""

from __future__ import annotations

import numpy as np

from cadena import decodifica_tocs as dt
from cadena import etiquetes_decodificador as ed
from cadena.smart_tagging import Etiqueta
from possessio.oficial import possession_metrics as pm

H, A = pm.H, pm.A
S = ed.Suma(beta_d=0.5, abans_s=4, beta_e=1.0, despres_s=2, marge_s=1)        # 100, 50 i 25 imatges


def test_sense_etiquetes_no_suma_res():
    relativa = np.random.default_rng(0).normal(size=(3000, 3))
    np.testing.assert_array_equal(ed.suma((), 3000, ((1, 0, 2999),), S), np.zeros((3000, 3)))
    nova = ed.amb_les_etiquetes(relativa, (), ((1, 0, 2999),), S)
    np.testing.assert_array_equal(nova, relativa)
    assert nova is not relativa


def test_la_d_abans_i_l_equip_despres_amb_el_marge():
    x = ed.suma((Etiqueta(1000, 1100, "corner", H),), 3000, ((1, 0, 2999),), S)
    np.testing.assert_array_equal(np.flatnonzero(x[:, dt.D]), np.arange(875, 975))
    assert (x[875:975, dt.D] == 0.5).all()
    np.testing.assert_array_equal(np.flatnonzero(x[:, dt.H]), np.arange(1025, 1075))
    assert (x[1025:1075, dt.H] == 1.0).all() and not x[:, dt.A].any()


def test_sense_equip_es_resta_a_la_d():
    x = ed.suma((Etiqueta(1000, 1100, "banda", None),), 3000, ((1, 0, 2999),), S)
    assert (x[1025:1075, dt.D] == -1.0).all() and (x[875:975, dt.D] == 0.5).all()
    assert not x[:, [dt.H, dt.A]].any()
    assert not x[975:1025, dt.D].any() and not x[1075:, dt.D].any()


def test_tot_dins_de_la_part_de_l_etiqueta():
    trams = ((1, 0, 999), (2, 1000, 1999))
    x = ed.suma((Etiqueta(1030, 1100, "falta", A), Etiqueta(1990, 2000, "falta", A)), 2000, trams, S)
    assert not x[:1000].any()
    np.testing.assert_array_equal(np.flatnonzero(x[:, dt.D]), [*range(1000, 1005), *range(1865, 1965)])
    np.testing.assert_array_equal(np.flatnonzero(x[:, dt.A]), [*range(1055, 1105)])     # la de 1990, sense després


def test_les_etiquetes_fora_de_les_parts_no_hi_son():
    x = ed.suma((Etiqueta(1500, 1600, "corner", H),), 2000, ((1, 0, 999),), S)
    assert not x.any()


def test_dues_etiquetes_que_es_toquen_no_se_sumen():
    x = ed.suma((Etiqueta(1000, 1100, "corner", H), Etiqueta(1010, 1100, "falta", H)), 3000, ((1, 0, 2999),), S)
    assert x[:, dt.H].max() == 1.0 and x[:, dt.D].max() == 0.5
    # la D d'abans de la segona cau on la primera resta (sense equip): la més gran de cada, i després la resta
    y = ed.suma((Etiqueta(1000, 1100, "banda", None), Etiqueta(1150, 1200, "falta", A)), 3000, ((1, 0, 2999),), S)
    assert (y[1025:1075, dt.D] == 0.5 - 1.0).all() and (y[1075:1125, dt.D] == 0.5).all()


def test_girar_els_equips_gira_el_que_rep_cada_equip():
    etiquetes = (Etiqueta(500, 600, "corner", H), Etiqueta(1500, 1600, "falta", A))
    girades = tuple(e._replace(equip={H: A, A: H}[e.equip]) for e in etiquetes)
    x, g = (ed.suma(t, 2500, ((1, 0, 2499),), S) for t in (etiquetes, girades))
    np.testing.assert_array_equal(g[:, [dt.H, dt.A, dt.D]], x[:, [dt.A, dt.H, dt.D]])


def test_la_graella_del_pla():
    assert len(ed.GRAELLA) == 192 and len(set(ed.GRAELLA)) == 192
    assert {s.beta_d for s in ed.GRAELLA} == {s.beta_e for s in ed.GRAELLA} == {0.0, 0.25, 0.5, 1.0}
    assert {s.abans_s for s in ed.GRAELLA} == {4, 10} and {s.despres_s for s in ed.GRAELLA} == {2, 4}
    assert {s.marge_s for s in ed.GRAELLA} == {0, 1, 2}


def test_els_punts_que_sumen_el_mateix_tenen_la_mateixa_clau():
    etiquetes = (Etiqueta(1000, 1100, "corner", H), Etiqueta(2000, 2100, "banda", None))
    per_clau: dict = {}
    for s in ed.GRAELLA:
        per_clau.setdefault(ed.efectiva(s), []).append(ed.suma(etiquetes, 3000, ((1, 0, 2999),), s))
    for sumes in per_clau.values():
        assert all(np.array_equal(sumes[0], x) for x in sumes[1:])
    assert len(per_clau) == 145
