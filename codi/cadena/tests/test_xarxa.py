"""La xarxa de la T3m: el que veu, la finestra sense passar d'una part a l'altra, la simetria entre equips, el càlcul
amb numpy igual que scikit-learn, i que aprèn."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from banc import avalua, degrada
from banc.tests import sintetic
from cadena import context, senyals, xarxa
from cadena.model import GIRA
from possessio.oficial import possession_metrics as pm


@pytest.fixture(scope="module")
def partit():
    return sintetic.partit(n=3000)


@pytest.fixture(scope="module")
def entrenada(partit):
    p = degrada.aplica(partit, "barreja")
    files = np.flatnonzero(np.isin(p.veritat, (pm.H, pm.A, pm.D)))[::5]
    x, y = xarxa.mostres(p.tracking, p.trams, files, p.veritat[files])
    return xarxa.entrena(x, y, passades=4)


def test_el_que_veu_a_cada_imatge(partit):
    p = degrada.aplica(partit, "barreja")
    c = xarxa.canals(p.tracking, p.trams)
    assert c.shape == (p.n, xarxa.CANALS) == (p.n, 29) and c.dtype == np.float32
    sense = np.isnan(p.tracking.pilota[:, 0])
    assert sense.any() and (c[sense] == 0).all() and (c[~sense, 0] == 1).all()
    for bloc in (5, 17):                                # els tres de cada equip, per ordre de distància
        d = [np.hypot(c[~sense, bloc + 4 * j], c[~sense, bloc + 4 * j + 1]) for j in range(xarxa.PROPERS)]
        assert (d[0] <= d[1]).all() and (d[1] <= d[2]).all()


def test_girar_els_equips_gira_el_camp_i_canvia_els_blocs(partit):
    t, trams = partit.tracking, partit.trams
    c, g = xarxa.canals(t, trams), xarxa.canals(xarxa.girat(t), trams)
    np.testing.assert_array_equal(g[:, 0], c[:, 0])
    np.testing.assert_array_equal(g[:, 1:5], -c[:, 1:5])
    np.testing.assert_array_equal(g[:, 5:17], -c[:, 17:29])
    np.testing.assert_array_equal(g[:, 17:29], -c[:, 5:17])


def test_la_finestra_no_passa_d_una_part_a_l_altra():
    c = np.arange(100 * 29, dtype=np.float32).reshape(100, 29) + 1
    trams = ((1, 0, 59), (2, 60, 99))
    files = np.array([0, 30, 57, 60, 99])
    x = xarxa.finestra(c, trams, files).reshape(len(files), len(xarxa.DESPLACAMENTS), 29)
    assert x.shape[0] == 5 and x.size == 5 * 725
    for i, f in enumerate(files):
        part = trams[0] if f <= 59 else trams[1]
        for j, k in enumerate(xarxa.DESPLACAMENTS):
            esperat = c[f + k] if part[1] <= f + k <= part[2] else np.zeros(29)
            np.testing.assert_array_equal(x[i, j], esperat)
    with pytest.raises(ValueError):
        xarxa.finestra(c, ((1, 10, 59),), np.array([5]))


def test_girar_els_equips_gira_exactament_les_probabilitats(partit, entrenada):
    xr, _ = entrenada
    p = degrada.aplica(partit, "barreja")
    directa = xarxa.probabilitats(xr, p.tracking, p.trams)
    girada = xarxa.probabilitats(xr, xarxa.girat(p.tracking), p.trams)
    np.testing.assert_array_equal(girada, directa[:, GIRA])
    assert not np.isnan(directa).any()
    np.testing.assert_array_equal(directa * xarxa.ARRODONIMENT, np.round(directa * xarxa.ARRODONIMENT))


def test_fora_de_les_parts_no_hi_ha_probabilitats(partit, entrenada):
    xr, _ = entrenada
    trams = ((1, 100, 1199), (2, 1500, 2899))
    p = xarxa.probabilitats(xr, partit.tracking, trams)
    fora = np.ones(partit.n, bool)
    fora[100:1200] = fora[1500:2900] = False
    assert np.isnan(p[fora]).all() and not np.isnan(p[~fora]).any()


@pytest.mark.filterwarnings("ignore::sklearn.exceptions.ConvergenceWarning")
def test_amb_numpy_dona_el_mateix_que_scikit_learn():
    from sklearn.neural_network import MLPClassifier

    rng = np.random.default_rng(3)
    x = rng.normal(size=(2000, 725)).astype(np.float32)
    y = (x[:, 0] > 0).astype(int) + (x[:, 1] > 1)
    m = MLPClassifier(hidden_layer_sizes=xarxa.OCULTES, max_iter=3, random_state=1).fit(x, y)
    xr = xarxa.Xarxa(np.zeros(725), np.ones(725), tuple(w.astype(float) for w in m.coefs_),
                     tuple(b.astype(float) for b in m.intercepts_))
    np.testing.assert_allclose(xarxa.endavant(xr, x[:200]), m.predict_proba(x[:200]), atol=1e-5)


def test_apren_i_sempre_igual(partit, entrenada):
    xr, perdua = entrenada
    assert len(perdua) == 4 and perdua[-1] < perdua[0]
    p = degrada.aplica(partit, "barreja")
    files = np.flatnonzero(np.isin(p.veritat, (pm.H, pm.A, pm.D)))[::5]
    x, y = xarxa.mostres(p.tracking, p.trams, files, p.veritat[files])
    altra, _ = xarxa.entrena(x, y, passades=4)
    for a, b in zip(xr.pesos + xr.biaixos, altra.pesos + altra.biaixos):
        np.testing.assert_array_equal(a, b)


def test_les_mostres_porten_les_dues_vistes(partit):
    files = np.array([10, 20, 1600])
    etiquetes = np.array([pm.H, pm.A, pm.D], dtype=np.int8)
    x, y = xarxa.mostres(partit.tracking, partit.trams, files, etiquetes)
    assert x.shape == (6, 725) and y.tolist() == [pm.H, pm.A, pm.D, pm.A, pm.H, pm.D]


def test_desa_i_carrega(entrenada, tmp_path):
    xr, _ = entrenada
    xarxa.desa(xr, tmp_path / "xarxa.npz")
    llegida = xarxa.carrega(tmp_path / "xarxa.npz")
    for a, b in zip((xr.mitjana, xr.escala, *xr.pesos, *xr.biaixos),
                    (llegida.mitjana, llegida.escala, *llegida.pesos, *llegida.biaixos)):
        np.testing.assert_array_equal(a, b)


def test_els_senyals_del_segon_giren_amb_els_equips_i_no_es_repeteixen():
    proba = np.random.default_rng(4).dirichlet([1, 1, 1], 600)
    trams = ((1, 0, 299), (2, 300, 599))
    taula = xarxa.senyals_segon(proba, trams)
    assert taula.dtypes.eq(np.float32).all() and len(taula) == 600
    assert not set(taula.columns) & set(context.calcula(proba, trams).columns)
    pd.testing.assert_frame_equal(xarxa.senyals_segon(proba[:, GIRA], trams), senyals.intercanvia(taula))


def test_les_mostres_son_les_de_la_tria(partit):
    """Amb les imatges que tria el banc (la tria de la T3f), també a les vores de les parts."""
    from banc import model_a_possessio as t3f

    p = degrada.aplica(partit, "curts")
    files = t3f.tria(p.veritat, avalua.trams_valids(p))
    x, y = xarxa.mostres(p.tracking, p.trams, files, p.veritat[files])
    assert len(x) == 2 * len(files) and np.isfinite(x).all()
