"""Les xarxes de la T3ad: el camp girat de dalt a baix, el que hi veuen les xarxes (la y i la vy canviades de signe,
la resta igual), les mostres (les de la T3v, la meitat girades a l'atzar) i les probabilitats (la mitjana de les quatre
vistes)."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from banc import degrada
from banc.tests import sintetic
from cadena import xarxa, xarxes
from cadena import xarxa_equips as xeq
from cadena import xarxa_girada as xg
from cadena import xarxa_sense_pilota as xsp
from cadena.model import GIRA
from possessio.oficial import possession_metrics as pm

PASSADES_PROVA = 2
TOL = {"rtol": 1e-5, "atol": 1e-4}           # el float32 dels canals
# de `xarxa.canals`: la y i la vy de la pilota, i la dy i la vy de cada jugador més proper
Y_CANALS = [2, 4, *(5 + 4 * k + d for k in range(2 * xarxa.PROPERS) for d in (1, 3))]
# de `xarxa_equips.equips`: la y i la vy de cada jugador dels dos equips
Y_EQUIPS = [e * xeq.PER_EQUIP + j * xeq.PER_JUGADOR + d for e in range(2) for j in range(xeq.ONZE) for d in (1, 3)]


@pytest.fixture(scope="module")
def barreja():
    return degrada.aplica(sintetic.partit(n=3000), "barreja")


@pytest.fixture(scope="module")
def files(barreja):
    return np.flatnonzero(np.isin(barreja.veritat, (pm.H, pm.A, pm.D)))[::5]


@pytest.fixture(scope="module")
def entrenades(barreja, files):
    x, y = xg.mostres(barreja.tracking, barreja.trams, files, barreja.veritat[files], llavor=1)
    return xarxes.entrena(x, y, llavors=xarxes.LLAVORS[:2], passades=PASSADES_PROVA)[0]


def _arrays(t) -> tuple[np.ndarray, ...]:
    return t.pilota, t.casa, t.fora


def test_el_camp_girat(barreja):
    t = barreja.tracking
    assert np.isnan(t.pilota).any()
    abans = tuple(a.copy() for a in _arrays(t))
    girat = xg.de_dalt_a_baix(t)
    for de, a in zip(abans, _arrays(girat)):
        np.testing.assert_array_equal(np.isnan(a), np.isnan(de))         # on no es veu res, igual
        np.testing.assert_array_equal(a[..., 0], de[..., 0])               # la x, igual
        np.testing.assert_allclose(a[..., 1], 1.0 - de[..., 1], rtol=0, atol=0)
    for de, ara in zip(abans, _arrays(t)):
        np.testing.assert_array_equal(ara, de)                             # el que rep, igual
    for de, a in zip(abans, _arrays(xg.de_dalt_a_baix(girat))):
        np.testing.assert_allclose(a, de, rtol=0, atol=1e-12)              # dues vegades, l'original
    assert (girat.camp_m, girat.nom_casa, girat.nom_fora) == (t.camp_m, t.nom_casa, t.nom_fora)
    np.testing.assert_array_equal(girat.fotograma, t.fotograma)


@pytest.mark.parametrize("slots_casa", [None, 2])         # amb 2, al tercer més proper de casa sempre hi falta
def test_el_que_hi_veuen_les_xarxes_la_y_i_la_vy_canviades_de_signe(barreja, slots_casa):
    t, trams = barreja.tracking, barreja.trams
    if slots_casa:
        t = replace(t, casa=t.casa[:, :slots_casa])
    girat = xg.de_dalt_a_baix(t)
    c, c_girat = xsp.canals(t, trams), xsp.canals(girat, trams)
    signe = np.ones(xsp.CANALS)
    signe[Y_CANALS] = -1.0
    esperat = c * signe
    falten = 0
    for k in range(2 * xarxa.PROPERS):                     # els que falten, lluny i quiets: al mateix lloc fix
        dx, dy = 5 + 4 * k, 6 + 4 * k
        falta = (c[:, dx] == xarxa.LLUNY_M) & (c[:, dy] == xarxa.LLUNY_M)
        esperat[falta, dy] = xarxa.LLUNY_M
        falten += falta.sum()
    assert (falten > 0) == bool(slots_casa)
    np.testing.assert_allclose(c_girat, esperat, **TOL)
    e, e_girat = xeq.equips(t, trams), xeq.equips(girat, trams)
    signe = np.ones(xeq.CANALS)
    signe[Y_EQUIPS] = -1.0
    np.testing.assert_allclose(e_girat, e * signe, **TOL)


def test_les_mostres_son_les_de_la_t3v_la_meitat_girades(barreja, files):
    t, trams, etiquetes = barreja.tracking, barreja.trams, barreja.veritat[files]
    x, y = xg.mostres(t, trams, files, etiquetes, llavor=1)
    x_t3v, y_t3v = xeq.mostres(t, trams, files, etiquetes)
    x_girat, y_girat = xeq.mostres(xg.de_dalt_a_baix(t), trams, files, etiquetes)
    np.testing.assert_array_equal(y_girat, y_t3v)                          # girar el camp no canvia de qui és
    np.testing.assert_array_equal(y, y_t3v)
    tal_qual, girada = (x == x_t3v).all(axis=1), (x == x_girat).all(axis=1)
    assert x.shape == x_t3v.shape and (tal_qual | girada).all() and not (tal_qual & girada).any()
    assert 0.45 < girada.mean() < 0.55
    np.testing.assert_array_equal(xg.mostres(t, trams, files, etiquetes, llavor=1)[0], x)
    assert not np.array_equal(xg.mostres(t, trams, files, etiquetes, llavor=2)[0], x)


def test_la_llavor_de_cada_partit_i_escenari():
    assert xg.llavor("u", "curts") == xg.llavor("u", "curts")
    assert len({xg.llavor(nom, e) for nom in ("u", "dos") for e in ("curts", "curts ×¼")}) == 4


def test_les_probabilitats_son_la_mitjana_de_les_quatre_vistes(barreja, entrenades):
    t, trams = barreja.tracking, barreja.trams
    p = xg.probabilitats(entrenades, t, trams)
    directa = xeq.probabilitats(entrenades, t, trams)
    girada = xeq.probabilitats(entrenades, xg.de_dalt_a_baix(t), trams)
    assert not np.allclose(directa, girada, equal_nan=True)                # el camp girat hi diu una altra cosa
    np.testing.assert_array_equal(np.isnan(p), np.isnan(directa))
    np.testing.assert_allclose(p, (directa + girada) / 2, rtol=0, atol=1.5 / xarxa.ARRODONIMENT)
    np.testing.assert_allclose(xg.probabilitats(entrenades, xg.de_dalt_a_baix(t), trams), p, rtol=0,
                               atol=1.5 / xarxa.ARRODONIMENT)
    np.testing.assert_array_equal(xg.probabilitats(entrenades, xarxa.girat(t), trams), p[:, GIRA])


def test_al_mig_del_camp_el_mateix_que_sense_girar(barreja, entrenades):
    t = barreja.tracking
    mig = replace(t, **{nom: np.where(np.isnan(a), np.nan, np.stack([a[..., 0], np.full(a.shape[:-1], 0.5)], -1))
                        for nom, a in zip(("pilota", "casa", "fora"), _arrays(t))})
    np.testing.assert_array_equal(xg.probabilitats(entrenades, mig, barreja.trams),
                                  xeq.probabilitats(entrenades, mig, barreja.trams))
    with pytest.raises(ValueError):
        xg.probabilitats((), t, barreja.trams)
