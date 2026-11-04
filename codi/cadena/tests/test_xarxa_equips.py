"""Les xarxes de la T3v: els equips (l'ordre, els que falten, els duplicats, quants se'n veuen), la finestra (els 31
d'A sense pilota tal qual), que gira exactament amb els equips, numpy com scikit-learn i dues vegades, exactament el
mateix."""

from __future__ import annotations

import numpy as np
import pytest

from banc import degrada
from banc.tests import sintetic
from cadena import senyals, xarxa, xarxes
from cadena import xarxa_equips as xeq
from cadena import xarxa_sense_pilota as xsp
from cadena.model import GIRA
from possessio.oficial import possession_metrics as pm

PASSADES_PROVA = 2
NAN = np.nan
PER = xeq.PER_EQUIP


@pytest.fixture(scope="module")
def partit():
    return sintetic.partit(n=3000)


@pytest.fixture(scope="module")
def barreja(partit):
    return degrada.aplica(partit, "barreja")


@pytest.fixture(scope="module")
def mostres(barreja):
    files = np.flatnonzero(np.isin(barreja.veritat, (pm.H, pm.A, pm.D)))[::5]
    return xeq.mostres(barreja.tracking, barreja.trams, files, barreja.veritat[files])


@pytest.fixture(scope="module")
def entrenades(mostres):
    x, y = mostres
    return xarxes.entrena(x.copy(), y, llavors=xarxes.LLAVORS[:2], passades=PASSADES_PROVA)


def _jugadors(bloc: np.ndarray) -> np.ndarray:
    """(n, 11, 4) d'un bloc de 45: x, y, vx i vy de cada jugador."""
    return bloc[:, :xeq.ONZE * xeq.PER_JUGADOR].reshape(len(bloc), xeq.ONZE, xeq.PER_JUGADOR)


def test_l_ordre_els_que_falten_i_quants_se_n_veuen():
    jug = np.full((5, 5, 2), NAN)
    jug[:, 0] = np.column_stack([10.0 + np.arange(5), np.zeros(5)])      # corre cap a les x positives, a 1 m per imatge
    jug[:, 1] = [-5.0, 1.0]
    jug[:, 2] = [3.0, 2.0]
    cap_endavant = xeq.un_equip(jug, 1.0)
    assert cap_endavant.shape == (5, PER) and (cap_endavant[:, -1] == 3).all()
    j = _jugadors(cap_endavant)[2]
    mig = [(12.0 - 5.0 + 3.0) / 3, (0.0 + 1.0 + 2.0) / 3]
    np.testing.assert_allclose(j[0], [-5.0, 1.0, 0.0, 0.0])
    np.testing.assert_allclose(j[1], [3.0, 2.0, 0.0, 0.0])
    np.testing.assert_allclose(j[2:10], np.tile([*mig, 0.0, 0.0], (8, 1)))           # al mig i quiets
    np.testing.assert_allclose(j[10], [12.0, 0.0, xarxa.FPS, 0.0])
    cap_enrere = _jugadors(xeq.un_equip(jug, -1.0))[2]
    np.testing.assert_array_equal(cap_enrere, j[::-1])


def test_si_no_se_n_veu_cap_tot_es_0():
    np.testing.assert_array_equal(xeq.un_equip(np.full((3, 14, 2), NAN), 1.0), np.zeros((3, PER)))


def test_els_duplicats_es_treuen_fins_que_en_queden_11():
    jug = np.column_stack([np.arange(13) * 10.0, np.zeros(13)])[None].repeat(2, axis=0)
    jug[:, 11] = jug[:, 3] + [0.1, 0.0]
    jug[:, 12] = jug[:, 7] + [0.0, 0.2]
    vist = np.ones((2, 13), dtype=bool)
    vist[1, [11, 12]] = False                                      # a la segona imatge, en són 11
    queden = xeq.sense_duplicats(jug, vist)
    assert queden[0].tolist() == [k not in (3, 7) for k in range(13)]    # dels dos de cada parell, el primer slot
    np.testing.assert_array_equal(queden[1], vist[1])
    assert (xeq.un_equip(jug, 1.0)[:, -1] == [13, 13]).all()


def test_on_son_els_jugadors_al_partit_net(partit):
    t, (_, inici, fi) = partit.tracking, partit.trams[0]
    e = xeq.equips(t, partit.trams)
    assert e.shape == (partit.n, xeq.CANALS) == (partit.n, 90) and e.dtype == np.float32
    escala = np.asarray(t.camp_m, float)
    casa, fora = t.casa[inici:fi + 1] * escala, t.fora[inici:fi + 1] * escala
    sentit = 1.0 if np.nanmedian(senyals._mitjana(casa[..., 0])) <= np.nanmedian(senyals._mitjana(fora[..., 0])) else -1.0
    f = 500
    casa_x, fora_x = (np.sort((jug[f - inici, :, 0] - escala[0] / 2) * sentit) for jug in (casa, fora))
    np.testing.assert_allclose(_jugadors(e[f:f + 1, :PER])[0, :, 0], casa_x, rtol=1e-6)
    np.testing.assert_allclose(_jugadors(e[f:f + 1, PER:])[0, :, 0], fora_x[::-1], rtol=1e-6)
    assert (e[f, [PER - 1, 2 * PER - 1]] == 11).all()


def test_girar_els_equips_dona_el_bloc_de_l_altre_canviat_de_signe(barreja):
    t = barreja.tracking
    assert ((~np.isnan(t.casa[..., 0])).sum(axis=1) > xeq.ONZE).any()    # també hi ha duplicats
    assert ((~np.isnan(t.casa[..., 0])).sum(axis=1) < xeq.ONZE).any()    # i en falten
    e, girat = xeq.equips(t, barreja.trams), xeq.equips(xarxa.girat(t), barreja.trams)
    for de, a in ((slice(0, PER), slice(PER, 2 * PER)), (slice(PER, 2 * PER), slice(0, PER))):
        np.testing.assert_array_equal(girat[:, de][:, :-1], -e[:, a][:, :-1])
        np.testing.assert_array_equal(girat[:, de][:, -1], e[:, a][:, -1])


def test_la_finestra_porta_els_31_d_a_sense_pilota_tal_qual_i_els_equips_a_9_imatges(barreja):
    t, trams = barreja.tracking, barreja.trams
    c, e = xsp.canals(t, trams), xeq.equips(t, trams)
    inici_2 = trams[1][1]
    files = np.array([30, 700, inici_2 - 3, inici_2 + 4])
    x = xeq.finestra(c, e, trams, files)
    assert x.shape == (4, xeq.ENTRADES) == (4, 1585) and x.dtype == np.float32
    np.testing.assert_array_equal(x[:, :775], xarxa.finestra(c, trams, files))
    equips_ = x[:, 775:].reshape(4, len(xeq.DESPLACAMENTS_EQUIPS), xeq.CANALS)
    for i, f in enumerate(files):
        for k, d in enumerate(xeq.DESPLACAMENTS_EQUIPS):
            mateixa_part = (f < inici_2) == (f + d < inici_2) and 0 <= f + d < barreja.n
            np.testing.assert_array_equal(equips_[i, k], e[f + d] if mateixa_part else 0.0)
    np.testing.assert_array_equal(xeq._finestra(c, trams, files, xarxa.DESPLACAMENTS), xarxa.finestra(c, trams, files))


def test_les_mostres_porten_les_dues_vistes_i_1585_valors(mostres):
    x, y = mostres
    assert x.shape[1] == xeq.ENTRADES
    n = len(y) // 2
    np.testing.assert_array_equal(y[n:], GIRA[y[:n]])


def test_girar_els_equips_gira_exactament_les_probabilitats(barreja, entrenades):
    xs, _ = entrenades
    directa = xeq.probabilitats(xs, barreja.tracking, barreja.trams)
    girada = xeq.probabilitats(xs, xarxa.girat(barreja.tracking), barreja.trams)
    np.testing.assert_array_equal(girada, directa[:, GIRA])
    dins = ~np.isnan(directa[:, 0])
    assert dins.any() and not np.isnan(directa[dins]).any()
    np.testing.assert_allclose(directa[dins].sum(axis=1), 1.0, atol=3 / xarxa.ARRODONIMENT)


@pytest.mark.filterwarnings("ignore::sklearn.exceptions.ConvergenceWarning")
def test_amb_numpy_dona_el_mateix_que_scikit_learn():
    from sklearn.neural_network import MLPClassifier

    rng = np.random.default_rng(3)
    x = rng.normal(size=(2000, xeq.ENTRADES)).astype(np.float32)
    y = (x[:, 0] > 0).astype(int) + (x[:, 1] > 1)
    m = MLPClassifier(hidden_layer_sizes=xarxa.OCULTES, max_iter=3, random_state=1).fit(x, y)
    xr = xarxa.Xarxa(np.zeros(xeq.ENTRADES), np.ones(xeq.ENTRADES), tuple(w.astype(float) for w in m.coefs_),
                     tuple(b.astype(float) for b in m.intercepts_))
    np.testing.assert_allclose(xarxa.endavant(xr, x[:200]), m.predict_proba(x[:200]), atol=1e-5)


def test_dues_vegades_exactament_el_mateix(barreja, mostres, entrenades):
    x, y = mostres
    xs, perdues = entrenades
    altres, altres_perdues = xarxes.entrena(x.copy(), y, llavors=xarxes.LLAVORS[:2], passades=PASSADES_PROVA)
    assert perdues == altres_perdues
    for a, b in zip(xs, altres):
        for u, v in zip(a.pesos + a.biaixos, b.pesos + b.biaixos):
            np.testing.assert_array_equal(u, v)
    np.testing.assert_array_equal(xeq.probabilitats(xs, barreja.tracking, barreja.trams),
                                  xeq.probabilitats(altres, barreja.tracking, barreja.trams))
