"""El banc de la pilota morta d'abans de la represa (T3ah): les medianes i la tria sense mirar el partit que es prova,
les llavors i la D impossible."""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from banc import fonts
from banc import model_etiquetes_decodificador as med
from banc import model_neteja_aire as mna
from banc import model_pilota_morta as mpm
from cadena import decodifica_tocs as dt
from cadena import pilota_morta as pmo
from cadena.smart_tagging import TIPUS, Etiqueta
from possessio.oficial import possession_metrics as pm

FIX1, FIX2 = pmo.GRAELLA[:2]
PT = next(a for a in pmo.GRAELLA if a.forma == pmo.PER_TIPUS)
MEDIANES = {t: 6.0 for t in TIPUS}


def fila(nom: str, e: str, nivell: str, a: pmo.Abans, sense: str, spell: float) -> dict:
    return {"partit": nom, "escenari": e, "nivell": nivell, "sense": sense, **a._asdict(), "spell_f1": spell,
            "macro_f1": 0.5}


def files(millor_de: dict[str, pmo.Abans]) -> pd.DataFrame:
    """Dos punts fixos a cada partit, ×¼ i nivell: el de `millor_de` del partit hi treu més."""
    return pd.DataFrame([fila(nom, e, nivell, a, "", 0.9 if a == millor_de.get(nom, FIX1) else 0.5)
                         for nom, e, nivell, a in itertools.product(fonts.NOMS, med.QUARTS_T3, med.NIVELLS_TRIA,
                                                                    (FIX1, FIX2))])


def test_la_tria_d_un_partit_no_mira_les_seves_files():
    prova = fonts.NOMS[0]
    t = files({prova: FIX2})
    assert mpm.tria(t, prova) == FIX1
    t = files({nom: FIX2 for nom in fonts.NOMS[:5]})          # cinc i cinc: amb el partit que es prova, empatarien
    assert mpm.tria(t, fonts.NOMS[0]) == FIX1 and mpm.tria(t, fonts.NOMS[9]) == FIX2
    assert isinstance(mpm.tria(t, prova), pmo.Abans) and mpm.tria(t, prova) in pmo.GRAELLA


def test_per_tipus_la_tria_nomes_mira_les_medianes_sense_el_partit():
    """Les files per tipus d'un partit es fan amb les medianes sense ell i sense un altre (`sense`): la tria d'un partit
    només mira les que no el tenen."""
    diana = fonts.NOMS[4]
    fixes = [fila(nom, e, n, FIX1, "", 0.7) for nom, e, n in itertools.product(fonts.NOMS, med.QUARTS_T3,
                                                                                med.NIVELLS_TRIA)]
    per_tipus = [fila(nom, e, n, PT, altre, 0.9 if altre == diana else 0.5)
                 for nom, e, n in itertools.product(fonts.NOMS, med.QUARTS_T3, med.NIVELLS_TRIA)
                 for altre in fonts.NOMS if altre != nom]
    t = pd.DataFrame(fixes + per_tipus)
    assert mpm.tria(t, diana) == PT
    assert all(mpm.tria(t, nom) == FIX1 for nom in fonts.NOMS if nom != diana)


def test_les_medianes_d_un_partit_no_miren_mai_la_seva_veritat(monkeypatch):
    seves = {nom: (("falta", float(k)),) for k, nom in enumerate(fonts.NOMS)}
    monkeypatch.setattr(mpm, "mortes", lambda nom: seves[nom])
    prova = fonts.NOMS[9]
    m = mpm.medianes_sense(prova)
    assert m["falta"] == 4.0                                 # 0 a 8
    seves[prova] = (("falta", 1000.0),) * 50
    assert mpm.medianes_sense(prova) == m
    assert mpm.medianes_sense(prova, fonts.NOMS[0])["falta"] == 4.5          # 1 a 8
    seves[fonts.NOMS[1]] = (("falta", 1000.0),) * 50
    assert mpm.medianes_sense(prova) != m


def test_les_etiquetes_son_les_de_la_t3ag():
    assert (mpm.TRIA, mpm.PROVA, mpm.NIVELLS_TRIA) == (med.TRIA, med.PROVA, med.NIVELLS_TRIA)
    assert mpm.TRIA != mpm.PROVA


def test_la_d_continua_impossible_a_les_imatges_netejades():
    r = np.zeros((1000, 3))
    netejades = np.zeros(1000, dtype=bool)
    netejades[850:900] = True
    x = mpm.relativa_amb(r, (Etiqueta(950, 990, "falta", pm.H),), ((1, 0, 999),), pmo.Abans(8.0, pmo.FIXA, 10.0, 0.0),
                         MEDIANES, netejades)
    assert (x[850:900, dt.D] == -mna.IMPOSSIBLE).all() and (x[700:850, dt.D] == 8.0).all()
    assert not x[:, [dt.H, dt.A]].any()


def test_sense_etiquetes_la_relativa_es_la_d_a_neteja_d_aire():
    r = np.random.default_rng(1).normal(size=(500, 3))
    netejades = np.random.default_rng(2).random(500) < 0.1
    for a in pmo.GRAELLA[::11]:
        np.testing.assert_array_equal(mpm.relativa_amb(r, (), ((1, 0, 499),), a, MEDIANES, netejades),
                                      mna.amb_la_d_impossible(r, netejades))


def test_dues_vegades_exactament_el_mateix():
    r = np.random.default_rng(3).normal(size=(3000, 3))
    netejades = np.random.default_rng(4).random(3000) < 0.05
    trams = ((1, 0, 1499), (2, 1500, 2999))
    etiquetes = (Etiqueta(400, 450, "corner", pm.H), Etiqueta(1000, 1100, "banda", None),
                 Etiqueta(1490, 1520, "falta", pm.A), Etiqueta(2500, 2600, "porta", pm.A))
    for a in pmo.GRAELLA[::7]:
        np.testing.assert_array_equal(mpm.relativa_amb(r, etiquetes, trams, a, MEDIANES, netejades),
                                      mpm.relativa_amb(r, etiquetes, trams, a, MEDIANES, netejades))
    t = files({fonts.NOMS[3]: FIX2})
    assert all(mpm.tria(t, nom) == mpm.tria(t.sample(frac=1, random_state=5), nom) for nom in fonts.NOMS)
