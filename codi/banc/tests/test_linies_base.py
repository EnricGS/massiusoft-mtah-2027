"""Les línies base al banc i la mètrica oficial deixant un partit fora."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from banc import avalua, degrada, linies_base
from banc.tests import sintetic
from cadena import regla
from possessio.oficial import possession_metrics as pm


@pytest.fixture(scope="module")
def net():
    return sintetic.partit()


def test_raw_es_la_regla_de_la_cadena_imatge_per_imatge(net):
    t = net.tracking
    esperat = linies_base.codis(regla.jugador_mes_proper(t.pilota, t.casa, t.fora, t.camp_m))
    assert np.array_equal(linies_base.prediu(net, finestra=1), esperat)


def test_la_variant_d_posa_d_on_no_hi_ha_pilota(net):
    brut = degrada.aplica(net, "curts")
    sense = np.isnan(brut.tracking.pilota[:, 0])
    d = linies_base.prediu(brut, finestra=1, sense_pilota="D")
    x = linies_base.prediu(brut, finestra=1, sense_pilota="X")
    assert (d[sense] == pm.D).all() and (x[sense] == pm.X).all() and np.array_equal(d[~sense], x[~sense])


def test_suavitzar_fa_menys_possessions(net):
    brut = degrada.aplica(net, "barreja")
    raw = avalua.puntua(brut, linies_base.prediu(brut, finestra=1))
    suau = avalua.puntua(brut, linies_base.prediu(brut, finestra=50))
    assert suau["possessions"] < raw["possessions"]


def test_una_prediccio_perfecta_puntua_u(net):
    puntuacio = avalua.puntua(net, net.veritat)
    assert puntuacio["spell_f1"] == puntuacio["macro_f1"] == 1.0
    assert puntuacio["possessions"] == puntuacio["possessions_reals"]


def test_cap_tram_no_passa_d_una_part_a_l_altra_ni_inclou_la_x(net):
    veritat = net.veritat.copy()
    veritat[100:200] = pm.X
    trams = avalua.trams_valids(replace(net, veritat=veritat))
    _, inici, _ = net.trams[1]
    assert (0, 100) in trams and (200, inici) in trams and (inici, net.n) in trams


def test_deixa_fora_el_partit_que_prova():
    partits = {n: sintetic.partit(n=3000, nom=n, llavor=i) for i, n in enumerate(("a", "b", "c"))}
    vistos = []

    def metode(entrenament, escenari, prova):
        vistos.append((entrenament, prova.nom))
        return prova.veritat

    files = avalua.avalua({"perfecte": metode}, tuple(partits), "curts", carrega=partits.__getitem__)
    assert vistos == [(("b", "c"), "a"), (("a", "c"), "b"), (("a", "b"), "c")]
    assert [f["spell_f1"] for f in files] == [1.0, 1.0, 1.0]
    assert files[0]["metode"] == "perfecte" and files[0]["escenari"] == "curts"


def test_cada_partit_es_degrada_un_sol_cop_per_a_tots_els_metodes(monkeypatch):
    partits = {"a": sintetic.partit(n=3000, nom="a")}
    vegades = []
    original = degrada.aplica
    monkeypatch.setattr(degrada, "aplica", lambda p, e: vegades.append(p.nom) or original(p, e))
    metodes = {n: linies_base.metode(n, "X") for n in linies_base.FINESTRES}
    files = avalua.avalua(metodes, ("a",), "curts", carrega=partits.__getitem__)
    assert vegades == ["a"] and [f["metode"] for f in files] == list(linies_base.FINESTRES)
    assert files[0]["pilota_absent"] == pytest.approx(0.41, abs=0.01)


def test_les_parelles_en_el_mateix_ordre_que_el_publicat():
    from banc.__main__ import acords
    assert acords(linies_base.ORDRE_PUBLICAT, linies_base.ORDRE_PUBLICAT) == 6
    assert acords(tuple(reversed(linies_base.ORDRE_PUBLICAT)), linies_base.ORDRE_PUBLICAT) == 0
    assert acords(("smooth125", "smooth50", "smooth25", "raw"), linies_base.ORDRE_PUBLICAT) == 5
