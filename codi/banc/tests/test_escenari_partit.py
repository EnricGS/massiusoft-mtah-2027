"""L'escenari «partit ×¼» (T3p): hi falta el que diu, és determinista i és el mateix que fa l'eina."""

from __future__ import annotations

import numpy as np
import pytest

from banc import degrada
from banc import escenari_partit as ep
from banc import mesura_atd as m
from banc.tests import sintetic
from possessio.oficial import possession_metrics as pm


@pytest.fixture(scope="module")
def net():
    return sintetic.partit(n=20_000)


def test_es_el_candidat_que_ha_dit_l_eina_al_partit():
    """Les paraules de l'eina (D-44), una per paràmetre; les aglomeracions, que no s'han pogut mesurar, com el banc."""
    c = ep.CANDIDAT
    assert c in m.CANDIDATS and ep.PERDUA in m.PERDUES
    assert m.NOMS["morta"][c.morta] == "gairebé sempre (com Metrica)"
    assert m.NOMS["viva"][c.viva] == "un 10 %"
    assert m.NOMS["forats"][c.forats] == "llargs"
    assert m.NOMS["aire"][c.aire] == "igual que a la resta"
    assert c.aglomeracio == m.DEL_BANC.aglomeracio
    assert m.NOMS["perdua"][m.nom_perdua(ep.PERDUA)] == "llargues (de 2 a 30 s)"


def test_es_el_mateix_que_fa_l_eina(net):
    a, b = ep.aplica(net), m.aplica(net, ep.CANDIDAT, ep.PERDUA)
    for camp in ("pilota", "casa", "fora"):
        assert np.array_equal(getattr(a.tracking, camp), getattr(b.tracking, camp), equal_nan=True)


def test_hi_falta_el_que_diu(net):
    """A la viva, un 10 %; a la morta, com a mínim un 97 % (un forat en joc hi pot seguir, com a `degrada`)."""
    q = ep.aplica(net)
    falta, graduats = np.isnan(q.tracking.pilota[:, 0]), degrada.puntuats(net)
    morta = graduats & (net.veritat == pm.D)
    assert falta[graduats & ~morta].mean() == pytest.approx(0.1, abs=0.005)
    assert falta[morta].mean() >= 0.96


def test_l_error_de_posicio_es_el_de_barreja_x_quart(net):
    q = ep.aplica(net)
    vist = ~np.isnan(q.tracking.pilota[:, 0])
    error_m = np.linalg.norm((q.tracking.pilota[vist] - net.tracking.pilota[vist]) * np.array(net.tracking.camp_m),
                             axis=1)
    esc = degrada.ESCENARIS["barreja"]
    assert np.sqrt((error_m ** 2).mean() / 2) == pytest.approx(
        np.hypot(esc.sigma_pilota_m, esc.tremolor_pilota_m) / 4, rel=0.25)


def test_es_determinista_i_no_toca_el_partit(net):
    a, b = ep.aplica(net), ep.aplica(net)
    assert np.array_equal(a.tracking.pilota, b.tracking.pilota, equal_nan=True)
    assert np.array_equal(a.tracking.casa, b.tracking.casa, equal_nan=True)
    assert not np.isnan(net.tracking.pilota).any()


def test_la_clau_canvia_amb_el_candidat(monkeypatch):
    abans = ep.clau()
    monkeypatch.setattr(ep, "CANDIDAT", m.DEL_BANC)
    assert ep.clau() != abans
