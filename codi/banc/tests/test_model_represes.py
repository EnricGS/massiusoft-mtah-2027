"""El banc del segon de les represes (T3ai): les mostres, la tria sense mirar el partit que es prova, les llavors i la D
impossible."""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from banc import fonts
from banc import model_etiquetes_decodificador as med
from banc import model_neteja_aire as mna
from banc import model_pilotes_aturades as mpa
from banc import model_represes as mre
from cadena import decodifica_tocs as dt
from cadena import model
from cadena import represes as rp
from cadena.smart_tagging import Etiqueta
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

TOT = ((1, 0, 2999),)


def test_les_mostres_nomes_de_l_entorn_i_girades():
    veritat = np.repeat(np.array([pm.H, pm.D, pm.A, pm.H, pm.A, pm.D], dtype=np.int8), 500)
    taula = pd.DataFrame({"imatge": np.arange(3000.0), "x_h": np.arange(3000.0), "x_a": -np.arange(3000.0),
                          "st_abans_equip_h": np.ones(3000), "st_abans_equip_a": np.zeros(3000)})
    entorn = rp.entorn((Etiqueta(1000, 1100, "corner", pm.H), Etiqueta(2500, 2600, "falta", pm.A)), 3000, TOT)
    x, y = mre.mostres_entorn(veritat, [(0, 3000)], taula, entorn)
    meitat = len(x) // 2
    directa, girada = x.iloc[:meitat].reset_index(drop=True), x.iloc[meitat:].reset_index(drop=True)
    assert meitat > 0 and entorn[directa["imatge"].astype(int)].all()
    np.testing.assert_array_equal(y[:meitat], veritat[directa["imatge"].astype(int)])
    np.testing.assert_array_equal(y[meitat:], model.GIRA[y[:meitat]])
    np.testing.assert_array_equal(girada["imatge"], directa["imatge"])
    np.testing.assert_array_equal(girada["x_h"], directa["x_a"])
    assert (girada["st_abans_equip_h"] == 0).all() and (girada["st_abans_equip_a"] == 1).all()


def test_les_mostres_d_un_partit_no_en_venen_mai():
    for prova in fonts.NOMS:
        claus = mpa.per_aprendre(prova)
        assert claus and all(nom != prova for nom, _ in claus)


def test_fora_de_l_entorn_no_se_n_sap_res():
    prior = np.array([0.4, 0.4, 0.2])
    probes = np.random.default_rng(0).dirichlet(np.ones(3), 40)
    idx = np.arange(100, 140)
    x = mre.a_tot(300, idx, probes, prior)
    assert np.isnan(np.delete(x, idx, axis=0)).all()
    np.testing.assert_allclose(x[idx], log_relativa(probes.astype(float), prior))


def files(millor_de: dict[str, float]) -> pd.DataFrame:
    return pd.DataFrame([{"partit": nom, "escenari": e, "nivell": nivell, "alfa": alfa, "macro_f1": 0.5,
                          "spell_f1": 0.9 if alfa == millor_de.get(nom, 0.25) else 0.5}
                         for nom, e, nivell, alfa in itertools.product(fonts.NOMS, med.QUARTS_T3, med.NIVELLS_TRIA,
                                                                       (0.25, 0.75))])


def test_la_tria_d_un_partit_no_mira_les_seves_files():
    prova = fonts.NOMS[0]
    assert mre.tria(files({prova: 0.75}), prova) == 0.25
    t = files({nom: 0.75 for nom in fonts.NOMS[:5]})          # cinc i cinc: amb el partit que es prova, empatarien
    assert mre.tria(t, fonts.NOMS[0]) == 0.25 and mre.tria(t, fonts.NOMS[9]) == 0.75
    assert mre.tria(t, prova) in rp.ALFES


def test_les_etiquetes_son_les_de_la_t3ag():
    assert (mre.TRIA, mre.PROVA, mre.NIVELLS_TRIA) == (med.TRIA, med.PROVA, med.NIVELLS_TRIA)


def test_la_d_continua_impossible_a_les_imatges_netejades():
    r = np.zeros((1000, 3))
    de_les_represes = np.zeros((1000, 3))
    de_les_represes[:, dt.D] = 50.0
    netejades = np.zeros(1000, dtype=bool)
    netejades[850:900] = True
    entorn = rp.entorn((Etiqueta(950, 990, "falta", pm.H),), 1000, ((1, 0, 999),))
    x = mre.relativa_amb(r, de_les_represes, entorn, 1.0, netejades)
    assert (x[850:900, dt.D] == -mna.IMPOSSIBLE).all() and (x[900:1000, dt.D] == 50.0).all()


def test_amb_alfa_zero_es_a_pilota_morta():
    rng = np.random.default_rng(1)
    r, de_les_represes = rng.normal(size=(3000, 3)), rng.normal(size=(3000, 3))
    netejades = rng.random(3000) < 0.1
    entorn = rp.entorn((Etiqueta(1000, 1100, "corner", pm.H),), 3000, TOT)
    np.testing.assert_array_equal(mre.relativa_amb(r, de_les_represes, entorn, 0.0, netejades),
                                  mna.amb_la_d_impossible(r, netejades))


def test_dues_vegades_exactament_el_mateix():
    rng = np.random.default_rng(3)
    r, de_les_represes = rng.normal(size=(3000, 3)), rng.normal(size=(3000, 3))
    netejades = rng.random(3000) < 0.05
    entorn = rp.entorn((Etiqueta(400, 450, "corner", pm.H), Etiqueta(2500, 2600, "porta", pm.A)), 3000, TOT)
    for alfa in rp.ALFES:
        np.testing.assert_array_equal(mre.relativa_amb(r, de_les_represes, entorn, alfa, netejades),
                                      mre.relativa_amb(r, de_les_represes, entorn, alfa, netejades))
    t = files({fonts.NOMS[3]: 0.75})
    assert all(mre.tria(t, nom) == mre.tria(t.sample(frac=1, random_state=5), nom) for nom in fonts.NOMS)
