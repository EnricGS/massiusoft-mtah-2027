"""Les vores de la T3ae: els canvis de la predicció, la imatge bona de cada un, on es poden moure (sense passar el del
costat, sense escurçar cap possessió per sota de la durada mínima i mai amb la D a una imatge netejada), el que mira el
LightGBM (igual amb els equips girats) i, dues vegades, el mateix."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from banc.tests import sintetic
from cadena import vores as vo
from cadena import xarxa
from cadena.model import GIRA
from possessio.oficial import possession_metrics as pm

H, A, D, X = pm.H, pm.A, pm.D, pm.X
TRAMS = ((1, 0, 199), (2, 200, 399))
D_MIN = 12


def prediccio() -> np.ndarray:
    x = np.full(420, X, dtype=np.int8)                 # després de la segona part, res
    for de, fins, c in ((0, 50, H), (50, 80, A), (80, 95, D), (95, 150, A), (150, 200, H),
                        (200, 260, A), (260, 300, H), (300, 400, D)):
        x[de:fins] = c
    return x


def netejades() -> np.ndarray:
    on = np.zeros(420, bool)
    on[60:80] = True                                   # just abans de la D: no s'hi pot allargar
    on[296:300] = True
    return on


def per_trossos(x: np.ndarray, trams=TRAMS) -> list[list[tuple[int, int]]]:
    """De cada part, cada possessió: (classe, durada)."""
    out = []
    for _, a, b in trams:
        w = x[a:b + 1]
        vores = [0, *(np.flatnonzero(w[1:] != w[:-1]) + 1), len(w)]
        out.append([(int(w[i]), j - i) for i, j in zip(vores[:-1], vores[1:])])
    return out


def mou(x: np.ndarray, puntua) -> tuple[np.ndarray, np.ndarray]:
    cs = vo.canvis(x, TRAMS)
    finestres = [vo.finestra(c) for c in cs]
    return vo.mou(x, D_MIN, netejades(), cs, finestres, [puntua(c, f) for c, f in zip(cs, finestres)])


def test_els_canvis_de_cada_part():
    cs = vo.canvis(prediccio(), TRAMS)
    assert [(c.t, c.de, c.a) for c in cs] == [(50, H, A), (80, A, D), (95, D, A), (150, A, H), (260, A, H),
                                              (300, H, D)]                       # a la 200 comença una part
    assert [(c.inici, c.fi) for c in cs] == [(0, 199)] * 4 + [(200, 399)] * 2
    assert [vo.tipus(c) for c in cs] == [vo.EQUIP_A_EQUIP, vo.A_LA_D, vo.DE_LA_D, vo.EQUIP_A_EQUIP,
                                         vo.EQUIP_A_EQUIP, vo.A_LA_D]
    assert [vo.equips(c) for c in cs] == [(A, H), (A, H), (A, H), (H, A), (H, A), (H, A)]
    c = cs[0]
    np.testing.assert_array_equal(vo.finestra(c), np.arange(38, 63))
    np.testing.assert_array_equal(vo.finestra(replace(c, t=5)), np.arange(1, 18))  # mai la primera de la part


def test_la_imatge_bona():
    toc = np.full(420, X, dtype=np.int8)
    toc[0:44], toc[44:70], toc[70:150], toc[150:200] = H, A, D, A
    canvis_ = vo.de_la_veritat(toc, [(0, 200)])
    c = vo.canvis(prediccio(), TRAMS)
    assert vo.la_bona(c[0], canvis_) == 44                        # H → A, a 6 imatges
    assert vo.la_bona(c[1], canvis_) == 70                        # A → D, a 10
    assert vo.la_bona(c[2], canvis_) is None                      # D → A, a 55: massa lluny
    assert vo.la_bona(c[3], canvis_) is None                      # A → H: a la veritat no n'hi ha cap
    assert vo.la_bona(replace(c[0], t=57), canvis_) is None       # a 13 imatges, massa lluny
    toc[0:70] = H
    toc[38:41], toc[50:70] = A, A                                 # dues H → A, a la 38 i a la 50
    canvis_ = vo.de_la_veritat(toc, [(0, 200)])
    assert vo.la_bona(replace(c[0], t=44), canvis_) == 38         # a la mateixa distància, la primera


@pytest.mark.parametrize("llavor", range(20))
def test_el_moviment_respecta_les_condicions(llavor):
    rng = np.random.default_rng(llavor)
    x = prediccio()
    nova, posicions = mou(x, lambda c, f: rng.random(len(f)))
    np.testing.assert_array_equal(nova[400:], x[400:])                                  # fora de les parts, res
    for abans, ara in zip(per_trossos(x), per_trossos(nova)):
        assert [c for c, _ in ara] == [c for c, _ in abans]                             # cap canvi no passa l'altre
        assert all(d >= min(D_MIN, d0) for (_, d), (_, d0) in zip(ara, abans))         # ni escurça per sota
    assert not ((nova == D) & (x != D) & netejades()).any()                             # mai la D a una netejada
    cs = vo.canvis(x, TRAMS)
    np.testing.assert_array_equal(posicions, [c.t for c in vo.canvis(nova, TRAMS)])
    assert np.all(np.abs(posicions - np.array([c.t for c in cs])) <= vo.RADI)


def test_si_prefereix_la_imatge_del_canvi_no_canvia_res():
    x = prediccio()
    nova, _ = mou(x, lambda c, f: -np.abs(f - c.t))
    np.testing.assert_array_equal(nova, x)
    nova, _ = mou(x, lambda c, f: np.zeros(len(f)))                # empatades: també es queda
    np.testing.assert_array_equal(nova, x)


def test_va_a_la_imatge_mes_probable_si_pot():
    volgudes = {50: 45, 80: 65, 95: 85, 150: 160, 260: 270, 300: 297}
    x = prediccio()
    _, posicions = mou(x, lambda c, f: (f == volgudes[c.t]).astype(float))
    # la 80 no hi va (la D a les netejades), la 95 tampoc (deixaria la D en 5 imatges), ni la 300 (netejades)
    np.testing.assert_array_equal(posicions, [45, 80, 95, 160, 270, 300])


def test_es_mouen_per_ordre():
    x = prediccio()
    # la 150 (A → H) vol anar a la 140; la 95 (D → A), a la 107: l'A que queda al mig, 33 imatges
    _, posicions = mou(x, lambda c, f: (f == {95: 107, 150: 140}.get(c.t, c.t)).astype(float))
    np.testing.assert_array_equal(posicions, [50, 80, 107, 140, 260, 300])
    # ara la 95 vol anar a la 107 i la 150 a la 118: l'A del mig, d'11, quedaria més curta que la durada mínima
    _, posicions = mou(x, lambda c, f: (f == {95: 107, 150: 118}.get(c.t, c.t)).astype(float))
    np.testing.assert_array_equal(posicions, [50, 80, 107, 150, 260, 300])


@pytest.fixture(scope="module")
def partit():
    return sintetic.partit()


def senyals_de(p, llavor: int = 3) -> tuple[vo.Senyals, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(llavor)
    n = p.n
    segon = rng.dirichlet(np.ones(3), n)
    xarxes = rng.dirichlet(np.ones(3), n)
    q = rng.random(n)
    return vo.senyals(p.tracking, p.trams, segon, xarxes, q), segon, xarxes


def tard(veritat: np.ndarray, trams, imatges: int) -> np.ndarray:
    """La veritat, amb cada canvi `imatges` més tard."""
    x = veritat.copy()
    for c in vo.canvis(veritat, trams):
        x[c.t:min(c.t + imatges, c.fi + 1)] = c.de
    return x


def test_el_que_mira_el_lightgbm(partit):
    s, segon, xarxes = senyals_de(partit)
    c = vo.canvis(partit.veritat, partit.trams)[3]
    f = vo.finestra(c)
    t = vo.trets(c, f, s)
    assert t.shape == (len(f), len(vo.TRETS))
    col = {nom: t[:, k] for k, nom in enumerate(vo.TRETS)}
    np.testing.assert_array_equal(col["desplaçament"], f - c.t)
    assert (col["tipus"] == vo.tipus(c)).all()
    e, o = vo.equips(c)
    np.testing.assert_array_equal(col["segon de l'equip"], segon[f, e])
    np.testing.assert_array_equal(col["xarxes de l'altre"], xarxes[f, o])
    abans, despres = np.clip(f - vo.LLUNY, c.inici, c.fi), np.clip(f + vo.LLUNY, c.inici, c.fi)
    np.testing.assert_allclose(col["canvi del segon de la D"], segon[despres, D] - segon[abans, D])


def test_la_pilota_i_els_propers():
    n = 60
    escala = np.array(sintetic.CAMP)
    x = 30.0 + 0.4 * np.arange(n)                      # a 10 m/s, i a la 30 torna enrere
    x[30:] = x[30] - 0.4 * np.arange(n - 30)
    pilota = np.stack([x, np.full(n, 34.0)], -1)
    pilota[50:] = np.nan
    casa = np.full((n, 2, 2), np.nan)
    casa[:, 0] = pilota + [3.0, 4.0]                    # a 5 m
    fora = np.stack([pilota + [0.0, 2.0]], 1)           # a 2 m
    t = replace(sintetic.partit(n=n).tracking, fotograma=np.arange(n), pilota=pilota / escala, casa=casa / escala,
                fora=fora / escala)
    s = vo.senyals(t, ((1, 0, n - 1),), np.zeros((n, 3)), np.zeros((n, 3)), np.zeros(n))
    vista, velocitat, canvi_v, direccio = s.pilota.T
    np.testing.assert_array_equal(vista, ~np.isnan(pilota[:, 0]))
    np.testing.assert_allclose(velocitat[5:25], 10.0)
    np.testing.assert_allclose(canvi_v[5:25], 0.0, atol=1e-9)
    np.testing.assert_allclose(direccio[5:25], 0.0, atol=1e-6)
    np.testing.assert_allclose(direccio[30], np.pi)
    assert np.isnan(velocitat[0]) and np.isnan(direccio[1]) and np.isnan(velocitat[55])     # a la vora i sense pilota
    np.testing.assert_allclose(s.propers[:50], [[5.0, 2.0]] * 50)
    assert np.isnan(s.propers[50:]).all()


def test_les_mostres(partit):
    s, _, _ = senyals_de(partit)
    pred = tard(partit.veritat, partit.trams, 4)
    canvis_ = vo.de_la_veritat(partit.veritat, [(a, b + 1) for _, a, b in partit.trams])
    x, y = vo.mostres(pred, partit.trams, s, canvis_)
    cs = vo.canvis(pred, partit.trams)
    finestres = [vo.finestra(c) for c in cs]
    assert x.shape == (sum(map(len, finestres)), len(vo.TRETS)) and len(y) == len(x)
    dins = np.cumsum([0, *map(len, finestres)])
    for c, f, a, b in zip(cs, finestres, dins[:-1], dins[1:]):
        bona = vo.la_bona(c, canvis_)
        assert y[a:b].sum() == (bona is not None) and (bona is None or y[a + list(f).index(bona)])
    assert y.sum() > 0.9 * len(cs)                     # quatre imatges tard: gairebé totes tenen la bona


def girat(pred: np.ndarray) -> np.ndarray:
    return np.where(pred == H, A, np.where(pred == A, H, pred)).astype(np.int8)


def test_amb_els_equips_girats_i_dues_vegades_el_mateix(partit):
    s, segon, xarxes = senyals_de(partit)
    pred = tard(partit.veritat, partit.trams, 4)
    canvis_ = vo.de_la_veritat(partit.veritat, [(a, b + 1) for _, a, b in partit.trams])
    x, y = vo.mostres(pred, partit.trams, s, canvis_)
    entrenat = vo.entrena(x, y, rondes=20)
    on = np.zeros(partit.n, bool)
    nova, cs, posicions = vo.amb_les_vores(entrenat, pred, partit.trams, D_MIN, on, s)
    assert len(cs) == len(posicions) and (posicions != [c.t for c in cs]).any()           # n'ha mogut algun
    s_girat = vo.senyals(xarxa.girat(partit.tracking), partit.trams, segon[:, GIRA], xarxes[:, GIRA], s.q)
    x_girat, y_girat = vo.mostres(girat(pred), partit.trams, s_girat,
                                  vo.de_la_veritat(girat(partit.veritat), [(a, b + 1) for _, a, b in partit.trams]))
    np.testing.assert_array_equal(x_girat, x)
    np.testing.assert_array_equal(y_girat, y)
    nova_girada, _, _ = vo.amb_les_vores(entrenat, girat(pred), partit.trams, D_MIN, on, s_girat)
    np.testing.assert_array_equal(nova_girada, girat(nova))
    np.testing.assert_array_equal(vo.amb_les_vores(vo.entrena(x, y, rondes=20), pred, partit.trams, D_MIN, on, s)[0],
                                  nova)


def test_sense_canvis_res():
    x = np.full(100, H, dtype=np.int8)
    trams = ((1, 0, 99),)
    assert vo.canvis(x, trams) == []
    s = vo.senyals(sintetic.partit(n=100).tracking, trams, np.zeros((100, 3)), np.zeros((100, 3)), np.zeros(100))
    xs, ys = vo.mostres(x, trams, s, {})
    assert xs.shape == (0, len(vo.TRETS)) and ys.shape == (0,)
