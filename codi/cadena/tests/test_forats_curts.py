"""Els forats curts (T3x): quins són, els seus trets, i el cost del decodificador, que no toca res més."""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from cadena import decodifica_tocs as dt
from cadena import forats_curts as fc
from cadena.llegeix import Tracking

CAMP = (100.0, 50.0)
NAN = np.nan


def tracking(pilota_m: np.ndarray, casa_m: np.ndarray, fora_m: np.ndarray) -> Tracking:
    """Un tracking amb la pilota i els jugadors on es diu, en metres."""
    camp = np.array(CAMP)
    return Tracking(fotograma=np.arange(len(pilota_m)), pilota=pilota_m / camp, casa=casa_m / camp,
                    fora=fora_m / camp, nom_casa="H", nom_fora="A", casa_es_home=True, camp_m=CAMP)


def en_linia(n: int, forat: slice, pas: tuple[float, float]) -> np.ndarray:
    """Una pilota que va en línia recta des de (20, 25), `pas` metres per imatge, i no es veu a `forat`."""
    p = np.array([20.0, 25.0]) + np.arange(n)[:, None] * np.array(pas)
    p[forat] = NAN
    return p


def jugadors(n: int, on: list[tuple[float, float]]) -> np.ndarray:
    return np.repeat(np.array(on, float)[None], n, axis=0)


def test_els_forats_curts_amb_les_dues_vores_a_la_part():
    vista = np.ones(400, bool)
    vista[0:3] = False                       # a l'inici de la part: no
    vista[10:20] = False                     # sí
    vista[30:30 + fc.CURT] = False           # de 5 s: no
    vista[200:210] = False                   # sí
    vista[250:260] = False                   # passa d'una part a l'altra: no
    vista[395:400] = False                   # al final: no
    parts = ((1, 0, 254), (2, 255, 399))
    np.testing.assert_array_equal(fc.forats(vista, parts), [[10, 19, 0, 254], [200, 209, 0, 254]])
    assert fc.forats(np.ones(10, bool), parts[:1]).shape == (0, 4)


def test_les_imatges_seguides_dins_de_cada_part():
    vista = np.array([1, 1, 0, 1, 1, 1, 1, 1], bool)
    enrere, endavant = fc.seguides(vista, ((1, 0, 4), (2, 5, 7)))
    assert enrere.tolist() == [1, 2, 0, 1, 2, 1, 2, 3]
    assert endavant.tolist() == [2, 1, 0, 2, 1, 3, 2, 1]


def test_una_pilota_en_linia_recta_no_gira():
    n = 60
    t = tracking(en_linia(n, slice(20, 30), (0.4, 0.0)), jugadors(n, [(10, 10), (60, 40)]),
                 jugadors(n, [(30, 30), (90, 5)]))
    parts = ((1, 0, n - 1),)
    f = fc.forats(~np.isnan(t.pilota[:, 0]), parts)
    x = fc.trets(t, f, parts).iloc[0]
    np.testing.assert_allclose(x["desplacament"], 0.4 * 11)              # de la imatge 19 a la 30
    np.testing.assert_allclose(x["velocitat"], 0.4 * 25)
    np.testing.assert_allclose([x["v_sortida"], x["v_tornada"]], [10.0, 10.0])
    np.testing.assert_allclose([x["gir"], x["gir_sortida"], x["gir_tornada"]], [0, 0, 0], atol=1e-6)
    np.testing.assert_allclose(x["durada"], 10 / 25)
    np.testing.assert_allclose(x["linia_sortida"], 25.0)                # a (27,6, 25): a 25 m de les bandes


def test_una_pilota_que_torna_enrere_gira_180():
    n = 60
    p = en_linia(n, slice(20, 30), (0.4, 0.0))
    p[30:] = p[19] - (np.arange(30, n) - 29)[:, None] * np.array([0.4, 0.0])
    t = tracking(p, jugadors(n, [(10, 10)]), jugadors(n, [(90, 5)]))
    parts = ((1, 0, n - 1),)
    x = fc.trets(t, fc.forats(~np.isnan(p[:, 0]), parts), parts).iloc[0]
    np.testing.assert_allclose(x["gir"], 180.0, atol=1e-6)
    np.testing.assert_allclose(x["gir_sortida"], 180.0, atol=1e-6)      # torna 0,4 m enrere
    np.testing.assert_allclose(x["gir_tornada"], 0.0, atol=1e-6)


def test_qui_hi_ha_a_prop_a_les_dues_vores():
    n = 60
    p = en_linia(n, slice(20, 30), (0.0, 0.0))                          # quieta a (20, 25)
    casa = jugadors(n, [(21, 25), (50, 25)])
    fora = jugadors(n, [(24, 25), (80, 25)])
    t = tracking(p, casa, fora)
    parts = ((1, 0, n - 1),)
    f = fc.forats(~np.isnan(p[:, 0]), parts)
    x = fc.trets(t, f, parts).iloc[0]
    np.testing.assert_allclose([x["seu_sortida"], x["altre_sortida"], x["seu_tornada"], x["altre_tornada"]],
                               [1, 4, 1, 4])
    assert x["mateix_jugador"] == 1 and x["es_del_seu"] == 1
    assert np.isnan(x["gir"])                                           # quieta: no té direcció
    casa2 = casa.copy()
    casa2[30:, 0] = (60, 25)                                            # a la tornada, el de casa se'n va
    y = fc.trets(tracking(p, casa2, fora), f, parts).iloc[0]
    assert y["mateix_jugador"] == 0 and y["es_del_seu"] == 0
    np.testing.assert_allclose([y["seu_tornada"], y["altre_tornada"]], [30, 4])


def test_girar_els_equips_no_canvia_cap_tret():
    n, rng = 300, np.random.default_rng(3)
    p = np.cumsum(rng.normal(0, 0.5, (n, 2)), axis=0) + np.array([50, 25])
    for a, llarg in ((40, 10), (90, 30), (150, 5), (220, 50)):
        p[a:a + llarg] = NAN
    casa, fora = rng.uniform(0, 100, (n, 11, 2)), rng.uniform(0, 50, (n, 11, 2))
    casa[:, 3] = NAN
    parts = ((1, 0, n - 1),)
    t = tracking(p, casa, fora)
    f = fc.forats(~np.isnan(p[:, 0]), parts)
    a, b = fc.trets(t, f, parts), fc.trets(replace(t, casa=t.fora, fora=t.casa), f, parts)
    assert len(f) == 4 and list(a.columns) == list(fc.TRETS)
    np.testing.assert_array_equal(a.to_numpy(), b.to_numpy())


def test_el_r_de_cada_forat():
    np.testing.assert_allclose(fc.r_de(np.array([0.2, 0.5, 0.0, 1.0]), 0.2),
                               [0, np.log(4), np.log(1e-3 / 0.999) + np.log(4), np.log(0.999 / 1e-3) + np.log(4)])


def test_el_cost_nomes_canvia_d_un_equip_a_l_altre_dins_dels_forats():
    rng = np.random.default_rng(0)
    c = rng.uniform(0, 5, (40, 3, 3))
    abans = c.copy()
    f = np.array([[5, 7, 0, 39], [20, 22, 0, 39]])
    nou = fc.cost(c, f, np.array([-1.0, 10.0]), 2.0)
    np.testing.assert_array_equal(c, abans)                             # el que rep, igual
    dins = np.zeros(40, bool)
    dins[5:9] = dins[20:24] = True
    canvia = np.zeros((3, 3), bool)
    canvia[dt.H, dt.A] = canvia[dt.A, dt.H] = True
    np.testing.assert_array_equal(nou[~dins], c[~dins])
    np.testing.assert_array_equal(nou[dins][:, ~canvia], c[dins][:, ~canvia])
    np.testing.assert_allclose(nou[5:9][:, canvia], c[5:9][:, canvia] + 2.0)       # no hi ha canvi: costa més
    np.testing.assert_array_equal(nou[20:24][:, canvia], 0.0)                       # n'hi ha: res, mai negatiu
    np.testing.assert_array_equal(fc.cost(c, f, np.array([-1.0, 10.0]), 0.0), c)


def test_de_quin_forat_es_cada_imatge():
    f = np.array([[3, 5, 0, 39], [10, 12, 0, 39], [20, 22, 0, 39]])
    qui, on = fc.de_quin(40, f)
    assert qui[:12].tolist() == [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1]       # a 8, a 3 del primer i a 2 del segon
    assert on[:12].tolist() == [-3, -2, -1, 0, 0, 0, 1, 2, -2, -1, 0, 0]
    assert qui[16] == 1 and on[16] == 4                                     # a 4 dels dos: el d'abans
    assert qui[17] == 2 and on[17] == -3
    assert (qui[29:] == -1).all() and qui[28] == 2 and on[28] == 6          # a K, encara; a K + 1, cap


def test_les_columnes_del_segon():
    n, rng = 300, np.random.default_rng(3)
    p = np.cumsum(rng.normal(0, 0.5, (n, 2)), axis=0) + np.array([50, 25])
    for a, llarg in ((40, 10), (90, 30), (150, 5), (220, 200)):             # l'últim, massa llarg
        p[a:a + llarg] = NAN
    casa, fora = rng.uniform(0, 100, (n, 11, 2)), rng.uniform(0, 50, (n, 11, 2))
    parts = ((1, 0, 199), (2, 200, n - 1))
    t = tracking(p, casa, fora)
    abans = {k: getattr(t, k).copy() for k in ("pilota", "casa", "fora")}
    c = fc.columnes_del_segon(t, parts)
    assert list(c.columns) == list(fc.COLUMNES) and len(c) == n and (c.dtypes == np.float32).all()
    f = fc.forats(~np.isnan(p[:, 0]), parts)
    x = fc.trets(t, f, parts)
    assert len(f) == 3
    np.testing.assert_array_equal(c.iloc[34:56, :-1].to_numpy(), np.tile(x.iloc[0].to_numpy(np.float32), (22, 1)))
    assert c["forat_on"].iloc[34] == -6 and c["forat_on"].iloc[55] == 6
    assert c.iloc[:34].isna().all().all() and c.iloc[200:].isna().all().all()       # la part 2 no en té cap
    assert c.iloc[150:155].notna().all(axis=None) and c["forat_on"].iloc[150:155].eq(0).all()
    girada = replace(t, casa=t.fora, fora=t.casa)
    np.testing.assert_array_equal(fc.columnes_del_segon(girada, parts).to_numpy(), c.to_numpy())
    for k, v in abans.items():
        np.testing.assert_array_equal(getattr(t, k), v)                    # el que rep, igual
