"""El banc de les etiquetes al decodificador (T3ag): la tria sense mirar el partit que es prova, les llavors i la D
impossible."""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from banc import fonts
from banc import model_etiquetes_decodificador as med
from banc import model_neteja_aire as mna
from banc import smart_tagging_simulat as sts
from cadena import decodifica_tocs as dt
from cadena import etiquetes_decodificador as ed
from cadena.smart_tagging import Etiqueta
from possessio.oficial import possession_metrics as pm

P1, P2 = ed.GRAELLA[5], ed.GRAELLA[100]


def files(millor_de: dict[str, ed.Suma]) -> pd.DataFrame:
    """Dos punts de la graella a cada partit, escenari i nivell: el de `millor_de` del partit hi treu més."""
    out = []
    for nom, e, nivell, s in itertools.product(fonts.NOMS, med.QUARTS_T3, med.NIVELLS_TRIA, (P1, P2)):
        bo = s == millor_de.get(nom, P1)
        out.append({"partit": nom, "escenari": e, "nivell": nivell, **s._asdict(),
                    "spell_f1": 0.9 if bo else 0.5, "macro_f1": 0.5})
    return pd.DataFrame(out)


def test_la_tria_d_un_partit_no_mira_les_seves_files():
    prova = fonts.NOMS[0]
    t = files({prova: P2})
    assert med.tria(t, prova) == P1
    t = files({nom: P2 for nom in fonts.NOMS[:5]})          # cinc i cinc: amb el partit que es prova, empatarien
    assert med.tria(t, fonts.NOMS[0]) == P1 and med.tria(t, fonts.NOMS[9]) == P2
    assert isinstance(med.tria(t, prova), ed.Suma) and med.tria(t, prova) in ed.GRAELLA


def test_les_etiquetes_de_triar_no_son_les_de_provar():
    assert med.TRIA != med.PROVA
    assert sts.llavor("metrica-1", "net", "mitjà", med.TRIA) != sts.llavor("metrica-1", "net", "mitjà", med.PROVA)
    assert set(med.NIVELLS_TRIA) == {"bo", "mitjà", "dolent"}


def test_la_d_continua_impossible_a_les_imatges_netejades():
    r = np.zeros((1000, 3))
    netejades = np.zeros(1000, dtype=bool)
    netejades[850:900] = True
    s = ed.Suma(1.0, 10, 1.0, 4, 0)
    x = med.relativa_amb(r, (Etiqueta(950, 990, "falta", pm.H),), ((1, 0, 999),), s, netejades)
    assert (x[850:900, dt.D] == -mna.IMPOSSIBLE).all() and (x[700:850, dt.D] == 1.0).all()


def test_sense_etiquetes_la_relativa_es_la_d_a_neteja_d_aire():
    r = np.random.default_rng(1).normal(size=(500, 3))
    netejades = np.random.default_rng(2).random(500) < 0.1
    for s in ed.GRAELLA[::17]:
        np.testing.assert_array_equal(med.relativa_amb(r, (), ((1, 0, 499),), s, netejades),
                                      mna.amb_la_d_impossible(r, netejades))


def test_dues_vegades_exactament_el_mateix():
    r = np.random.default_rng(3).normal(size=(3000, 3))
    netejades = np.random.default_rng(4).random(3000) < 0.05
    trams = ((1, 0, 1499), (2, 1500, 2999))
    etiquetes = (Etiqueta(400, 450, "corner", pm.H), Etiqueta(1000, 1100, "banda", None),
                 Etiqueta(1490, 1520, "falta", pm.A), Etiqueta(2500, 2600, "porta", pm.A))
    for s in ed.GRAELLA[::23]:
        np.testing.assert_array_equal(med.relativa_amb(r, etiquetes, trams, s, netejades),
                                      med.relativa_amb(r, etiquetes, trams, s, netejades))
    t = files({fonts.NOMS[3]: P2})
    assert all(med.tria(t, nom) == med.tria(t.sample(frac=1, random_state=5), nom) for nom in fonts.NOMS)
