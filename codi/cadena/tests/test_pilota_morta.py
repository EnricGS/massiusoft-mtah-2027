"""La pilota morta d'abans de la represa (T3ah): què suma a la D, on i quant, i les medianes per tipus."""

from __future__ import annotations

import numpy as np

from cadena import decodifica_tocs as dt
from cadena import etiquetes_decodificador as ed
from cadena import pilota_morta as pmo
from cadena.smart_tagging import TIPUS, Etiqueta
from possessio.oficial import possession_metrics as pm

H, A, D = pm.H, pm.A, pm.D
TOT = ((1, 0, 2999),)
MEDIANES = {"banda": 2.0, "corner": 8.0, "porta": 4.0, "falta": 6.0, "sortida": 10.0}


def test_sense_etiquetes_no_suma_res():
    relativa = np.random.default_rng(0).normal(size=(3000, 3))
    a = pmo.Abans(2.0, pmo.FIXA, 20.0, 1.0)
    np.testing.assert_array_equal(pmo.suma((), 3000, TOT, a, MEDIANES), np.zeros((3000, 3)))
    nova = pmo.amb_les_etiquetes(relativa, (), TOT, a, MEDIANES)
    np.testing.assert_array_equal(nova, relativa)
    assert nova is not relativa


def test_nomes_la_d_i_nomes_abans():
    x = pmo.suma((Etiqueta(1000, 1100, "corner", H),), 3000, TOT, pmo.Abans(2.0, pmo.FIXA, 4.0, 1.0), MEDIANES)
    np.testing.assert_array_equal(np.flatnonzero(x[:, dt.D]), np.arange(875, 975))
    assert (x[875:975, dt.D] == 2.0).all() and not x[:, [dt.H, dt.A]].any()
    y = pmo.suma((Etiqueta(1000, 1100, "banda", None),), 3000, TOT, pmo.Abans(1.0, pmo.FIXA, 4.0, 0.0), MEDIANES)
    np.testing.assert_array_equal(np.flatnonzero(y[:, dt.D]), np.arange(900, 1000))
    assert not y[:, [dt.H, dt.A]].any()


def test_per_tipus_cada_etiqueta_la_mediana_del_seu():
    etiquetes = (Etiqueta(1000, 1100, "banda", None), Etiqueta(2000, 2100, "falta", A))
    x = pmo.suma(etiquetes, 3000, TOT, pmo.Abans(1.0, pmo.PER_TIPUS, 0.5, 0.0), MEDIANES)
    np.testing.assert_array_equal(np.flatnonzero(x[:, dt.D]), [*range(975, 1000), *range(1925, 2000)])
    assert pmo.finestres(pmo.Abans(1.0, pmo.PER_TIPUS, 1.5, 0.0), MEDIANES) == {
        "banda": 75, "corner": 300, "porta": 150, "falta": 225, "sortida": 375}
    assert set(pmo.finestres(pmo.Abans(1.0, pmo.FIXA, 10.0, 0.0), MEDIANES).values()) == {250}


def test_tot_dins_de_la_part_de_l_etiqueta():
    trams = ((1, 0, 999), (2, 1000, 1999))
    x = pmo.suma((Etiqueta(1030, 1100, "falta", A), Etiqueta(2500, 2600, "corner", H)), 3000, trams,
                 pmo.Abans(1.0, pmo.FIXA, 4.0, 0.0), MEDIANES)
    np.testing.assert_array_equal(np.flatnonzero(x[:, dt.D]), np.arange(1000, 1030))


def test_el_punt_fix_es_el_de_la_t3ag_sense_equip():
    rng = np.random.default_rng(7)
    trams = ((1, 0, 1499), (2, 1500, 2999))
    etiquetes = tuple(Etiqueta(int(i), int(i) + 50, TIPUS[int(rng.integers(5))], (None, H, A)[int(rng.integers(3))])
                      for i in rng.integers(0, 3000, 25))
    for marge in (0.0, 1.0, 2.0):
        for durada in (4.0, 10.0):
            np.testing.assert_array_equal(
                pmo.suma(etiquetes, 3000, trams, pmo.Abans(1.0, pmo.FIXA, durada, marge), MEDIANES),
                ed.suma(etiquetes, 3000, trams, ed.Suma(1.0, durada, 0.0, 2, marge)))


def test_dues_etiquetes_que_es_toquen_no_se_sumen():
    x = pmo.suma((Etiqueta(1000, 1100, "corner", H), Etiqueta(1050, 1100, "falta", H)), 3000, TOT,
                 pmo.Abans(4.0, pmo.FIXA, 10.0, 0.0), MEDIANES)
    assert x[:, dt.D].max() == 4.0
    np.testing.assert_array_equal(np.flatnonzero(x[:, dt.D]), np.arange(750, 1050))


def test_les_durades_de_la_pilota_morta_abans_de_cada_represa():
    veritat = np.full(3000, H, dtype=np.int8)
    veritat[400:500] = D                     # 4 s abans de la represa de 500
    veritat[1000:1100] = D                   # comença la part a 1050: 2 s dins
    veritat[2000:2100] = A                   # cap D abans de la de 2100
    trams = ((1, 0, 1049), (2, 1050, 2999))
    durades = pmo.durades(veritat, trams, ((500, "falta"), (1100, "sortida"), (2100, "banda"), (3500, "corner")))
    assert durades == (("falta", 4.0), ("sortida", 2.0), ("banda", 0.0))


def test_les_medianes_per_tipus():
    durades = (("falta", 10.0), ("falta", 20.0), ("falta", 40.0), ("banda", 4.0), ("banda", 6.0))
    m = pmo.medianes(durades)
    assert set(m) == set(TIPUS)
    assert m["falta"] == 20.0 and m["banda"] == 5.0
    assert m["corner"] == m["porta"] == m["sortida"] == 10.0          # sense cap represa: la de totes


def test_la_graella_del_pla():
    assert len(pmo.GRAELLA) == 96 and len(set(pmo.GRAELLA)) == 96
    assert {a.beta_d for a in pmo.GRAELLA} == {1.0, 2.0, 4.0, 8.0}
    assert {a.durada for a in pmo.GRAELLA if a.forma == pmo.FIXA} == {10.0, 20.0, 30.0, 45.0}
    assert {a.durada for a in pmo.GRAELLA if a.forma == pmo.PER_TIPUS} == {0.5, 0.75, 1.0, 1.5}
    assert {a.marge_s for a in pmo.GRAELLA} == {0.0, 1.0, 2.0}
    assert pmo.Abans(1.0, pmo.FIXA, 10.0, 1.0) in pmo.GRAELLA


def test_la_mateixa_clau_suma_el_mateix():
    etiquetes = tuple(Etiqueta(300 * k + 200, 300 * k + 250, t, H) for k, t in enumerate(TIPUS))
    iguals = {t: 10.0 for t in TIPUS}
    per_clau: dict = {}
    for a in pmo.GRAELLA:
        for m in (MEDIANES, iguals):
            per_clau.setdefault(pmo.efectiva(a, m), []).append(pmo.suma(etiquetes, 3000, TOT, a, m))
    for sumes in per_clau.values():
        assert all(np.array_equal(sumes[0], x) for x in sumes[1:])
    assert pmo.efectiva(pmo.Abans(1.0, pmo.FIXA, 10.0, 1.0), MEDIANES) == pmo.efectiva(
        pmo.Abans(1.0, pmo.PER_TIPUS, 1.0, 1.0), iguals)
