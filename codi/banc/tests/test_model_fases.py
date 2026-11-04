"""El banc d'A fases (T3ak): la graella, la tria sense mirar el partit que es prova, les llavors, la D impossible i
que dues vegades dona exactament el mateix."""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from banc import fases_simulades as fsm
from banc import fonts
from banc import model_etiquetes_decodificador as med
from banc import model_fases as mfs
from banc import model_neteja_aire as mna
from banc import smart_tagging_simulat as sts
from cadena import decodifica_tocs as dt
from cadena.fases import Fase
from possessio.oficial import possession_metrics as pm

H, A, D = pm.H, pm.A, pm.D
TRAMS = ((1, 0, 999),)
ZERO = mfs.Suma(0.0, 0.0, 0.0)


def test_la_graella_del_pla():
    assert {s.gamma for s in mfs.GRAELLA} == {0.0, 0.05, 0.1, 0.25, 0.5, 1.0}
    assert {s.delta for s in mfs.GRAELLA} == {0.0, 0.25, 1.0}
    assert {s.marge_s for s in mfs.GRAELLA} == {0.0, 1.0, 2.0}
    assert len(mfs.GRAELLA) == 54 and len({mfs.efectiva(s) for s in mfs.GRAELLA}) == 52
    assert mfs.efectiva(mfs.Suma(0.0, 0.0, 2.0)) == mfs.efectiva(ZERO)


def files(millor_de: dict[str, mfs.Suma]) -> pd.DataFrame:
    punts = (mfs.Suma(0.1, 0.25, 1.0), mfs.Suma(0.5, 0.0, 2.0))
    return pd.DataFrame([{"partit": nom, "escenari": e, "nivell": nivell, **s._asdict(), "macro_f1": 0.5,
                          "spell_f1": 0.9 if s == millor_de.get(nom, punts[0]) else 0.5}
                         for nom, e, nivell, s in itertools.product(fonts.NOMS, med.QUARTS_T3, med.NIVELLS_TRIA,
                                                                    punts)])


def test_la_tria_d_un_partit_no_mira_les_seves_files():
    a, b = mfs.Suma(0.1, 0.25, 1.0), mfs.Suma(0.5, 0.0, 2.0)
    prova = fonts.NOMS[0]
    assert mfs.tria(files({prova: b}), prova) == a
    t = files({nom: b for nom in fonts.NOMS[:5]})            # cinc i cinc: amb el partit que es prova, empatarien
    assert mfs.tria(t, fonts.NOMS[0]) == a and mfs.tria(t, fonts.NOMS[9]) == b
    assert isinstance(mfs.tria(t, prova), mfs.Suma)


def test_les_llavors():
    assert (mfs.TRIA, mfs.PROVA, mfs.NIVELLS_TRIA) == (med.TRIA, med.PROVA, med.NIVELLS_TRIA)
    assert tuple(fsm.NIVELLS) == tuple(med.NIVELLS)
    nom, e = fonts.NOMS[0], med.QUARTS_T3[0]
    llavors = {fsm.llavor(nom, e, "mitjà", mfs.TRIA), fsm.llavor(nom, e, "mitjà", mfs.PROVA),
               sts.llavor(nom, e, "mitjà", mfs.TRIA), sts.llavor(nom, e, "mitjà", mfs.PROVA)}
    assert len(llavors) == 4


def test_la_d_continua_impossible_a_les_imatges_netejades():
    rng = np.random.default_rng(0)
    netejades = np.zeros(1000, dtype=bool)
    netejades[300:400] = True
    relativa = mna.amb_la_d_impossible(rng.normal(size=(1000, 3)), netejades)
    x = mfs.relativa_amb(relativa, (Fase(200, 599, H),), TRAMS, mfs.Suma(1.0, 1.0, 0.0), netejades)
    assert (x[netejades, dt.D] == -mna.IMPOSSIBLE).all()
    np.testing.assert_allclose(x[450:600, D], relativa[450:600, D] - 1.0)


def test_amb_zeros_o_sense_fases_es_a_pilota_morta():
    rng = np.random.default_rng(1)
    netejades = rng.random(1000) < 0.1
    relativa = mna.amb_la_d_impossible(rng.normal(size=(1000, 3)), netejades)
    fases = (Fase(100, 499, H), Fase(600, 899, A))
    np.testing.assert_array_equal(mfs.relativa_amb(relativa, fases, TRAMS, ZERO, netejades), relativa)
    np.testing.assert_array_equal(mfs.relativa_amb(relativa, (), TRAMS, mfs.Suma(1.0, 1.0, 1.0), netejades), relativa)


def test_dues_vegades_exactament_el_mateix():
    rng = np.random.default_rng(3)
    netejades = rng.random(1000) < 0.05
    relativa = mna.amb_la_d_impossible(rng.normal(size=(1000, 3)), netejades)
    fases = (Fase(100, 499, H), Fase(600, 899, A))
    for s in mfs.GRAELLA:
        np.testing.assert_array_equal(mfs.relativa_amb(relativa, fases, TRAMS, s, netejades),
                                      mfs.relativa_amb(relativa, fases, TRAMS, s, netejades))
    t = files({fonts.NOMS[3]: mfs.Suma(0.5, 0.0, 2.0)})
    assert all(mfs.tria(t, nom) == mfs.tria(t.sample(frac=1, random_state=5), nom) for nom in fonts.NOMS)
