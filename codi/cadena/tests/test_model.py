"""El classificador d'A: aprèn amb els partits sintètics, és simètric entre equips i determinista."""

from __future__ import annotations

import numpy as np
import pytest

from banc import degrada
from banc.tests import sintetic
from cadena import model, senyals
from possessio.oficial import possession_metrics as pm


def taula_i_veritat(llavor: int, escenari: str = "curts"):
    p = degrada.aplica(sintetic.partit(n=6000, nom=f"s{llavor}", llavor=llavor), escenari)
    return senyals.calcula(p.tracking, p.trams), p.veritat


@pytest.fixture(scope="module")
def entrenat():
    dades = [taula_i_veritat(llavor) for llavor in (1, 2, 3)]
    return model.entrena(*model.mostres([t for t, _ in dades], [v for _, v in dades], pas=2), rondes=40)


def test_apren_qui_te_la_pilota_en_un_partit_que_no_ha_vist(entrenat):
    taula, veritat = taula_i_veritat(9)
    proba = model.probabilitats(entrenat, taula)
    assert proba.shape == (len(taula), 3)
    np.testing.assert_allclose(proba.sum(axis=1), 1, rtol=1e-6)
    hi_es = ~taula["falta"].astype(bool).to_numpy()
    encerts = np.asarray(model.CLASSES)[proba.argmax(axis=1)] == veritat
    assert encerts[hi_es & (veritat != pm.D)].mean() > 0.9


def test_els_equips_girats_donen_les_probabilitats_girades(entrenat):
    taula, _ = taula_i_veritat(9)
    proba = model.probabilitats(entrenat, taula)
    girades = model.probabilitats(entrenat, senyals.intercanvia(taula))
    np.testing.assert_allclose(girades, proba[:, [1, 0, 2]], atol=1e-6)


def test_dues_vegades_el_mateix_model():
    dades = [taula_i_veritat(llavor) for llavor in (1, 2)]
    x, y = model.mostres([t for t, _ in dades], [v for _, v in dades], pas=3)
    uns, altres = (model.entrena(x, y, rondes=10) for _ in range(2))
    taula, _ = taula_i_veritat(9)
    np.testing.assert_array_equal(model.probabilitats(uns, taula), model.probabilitats(altres, taula))


def test_no_apren_de_les_imatges_x():
    taula, veritat = taula_i_veritat(1)
    veritat = veritat.copy()
    veritat[:3000] = pm.X
    x, y = model.mostres([taula], [veritat], pas=1)
    assert len(x) == 2 * (len(taula) - 3000) and set(np.unique(y).tolist()) <= set(model.CLASSES)
    assert (y == pm.H).sum() == (y == pm.A).sum()


def test_el_prior_es_el_de_les_mostres():
    taula, veritat = taula_i_veritat(1)
    x, y = model.mostres([taula], [veritat], pas=1)
    np.testing.assert_allclose(model.prior(y), [np.mean(y == c) for c in model.CLASSES])
