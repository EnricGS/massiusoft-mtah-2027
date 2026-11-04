"""Les fases de defensar simulades del banc (T3an): les tirades d'atac són les de `fases_simulades`; amb `lligades` = 1,
són les d'atac amb l'equip girat; amb 0, les tirades són unes altres; l'equip és el que defensa; el nivell sense fases,
i les llavors."""

from __future__ import annotations

import pytest

from banc import fases_defensar as fd
from banc import fases_simulades as fsm
from banc.tests import test_fases_simulades as tfs
from cadena.fases import Fase
from possessio.oficial import possession_metrics as pm

H, A = pm.H, pm.A
VERITAT, EXACTE = tfs.VERITAT, tfs.EXACTE
UNA, DUES = ((1, 0, 2999),), ((1, 0, 1499), (2, 1500, 2999))
AMB_ERRORS = (fsm.NIVELLS["bo"], fsm.NIVELLS["mitjà"], fsm.NIVELLS["dolent"], EXACTE._replace(falses=40))


def girades(fases: tuple[Fase, ...]) -> tuple[Fase, ...]:
    return tuple(sorted(Fase(f.inici, f.final, 1 - f.equip) for f in fases))


def test_les_tirades_d_atac_donen_les_fases_d_atac():
    for nivell in AMB_ERRORS:
        for trams in (UNA, DUES):
            for llavor in range(10):
                assert fd.d_atac(VERITAT, trams, nivell, llavor) == fsm.simula(VERITAT, trams, nivell, llavor)


def test_sense_errors_l_equip_que_defensa_a_les_mateixes_estones():
    for lligades in fd.LLIGADES:
        assert fd.simula(VERITAT, UNA, EXACTE, 3, 4, lligades) == girades(fsm.simula(VERITAT, UNA, EXACTE, 4))


def test_lligades_1_son_les_d_atac_girades():
    for nivell in AMB_ERRORS:
        for trams in (UNA, DUES):
            for llavor in range(10):
                assert (fd.simula(VERITAT, trams, nivell, 100 + llavor, llavor, 1.0)
                        == girades(fsm.simula(VERITAT, trams, nivell, llavor)))


def test_lligades_0_no_miren_les_d_atac():
    mitja = fsm.NIVELLS["mitjà"]
    for llavor in range(10):
        defensar = fd.simula(VERITAT, DUES, mitja, 100 + llavor, llavor, 0.0)
        assert defensar == fd.simula(VERITAT, DUES, mitja, 100 + llavor, llavor + 1, 0.0)
    assert any(fd.simula(VERITAT, DUES, mitja, 100 + llavor, llavor, 0.0)
               != girades(fsm.simula(VERITAT, DUES, mitja, llavor)) for llavor in range(10))


def test_amb_lligades_a_mitges_cada_fase_es_d_una_o_de_l_altra():
    """Les tirades pròpies no depenen de `lligades`: amb 0,5, cada fase és la d'atac girada o la de `lligades` = 0."""
    dolent = fsm.NIVELLS["dolent"]
    entremig = 0
    for llavor in range(10):
        juntes, soles = (set(fd.simula(VERITAT, DUES, dolent, 100 + llavor, llavor, x)) for x in (1.0, 0.0))
        mig = set(fd.simula(VERITAT, DUES, dolent, 100 + llavor, llavor, 0.5))
        assert mig <= juntes | soles
        entremig += mig != juntes and mig != soles
    assert entremig > 0


def test_dins_de_la_part():
    for llavor in range(5):
        for lligades in fd.LLIGADES:
            for f in fd.simula(VERITAT, DUES, fsm.NIVELLS["dolent"], llavor, llavor + 7, lligades):
                part = (0, 1499) if f.inici <= 1499 else (1500, 2999)
                assert part[0] <= f.inici <= f.final <= part[1] and f.equip in (H, A)


def test_sense_fases_i_les_llavors():
    assert fd.LLIGADES == (0.0, 0.5, 1.0)
    for lligades in fd.LLIGADES:
        assert fd.simula(VERITAT, UNA, fsm.NIVELLS["cap"], 0, 0, lligades) == ()
    mitja = fsm.NIVELLS["mitjà"]
    a = fd.simula(VERITAT, DUES, mitja, 7, 1, 0.5)
    assert a == fd.simula(VERITAT, DUES, mitja, 7, 1, 0.5)
    assert a != fd.simula(VERITAT, DUES, mitja, 8, 1, 0.5)
    for nivell in fsm.NIVELLS:
        assert fd.llavor("x", "curts ×¼", nivell, "provar") != fsm.llavor("x", "curts ×¼", nivell, "provar")
    assert fd.llavor("x", "curts ×¼", "mitjà", "provar") != fd.llavor("x", "curts ×¼", "mitjà", "triar")


def test_lligades_ha_d_anar_de_0_a_1():
    for lligades in (-0.1, 1.1):
        with pytest.raises(ValueError):
            fd.simula(VERITAT, UNA, fsm.NIVELLS["mitjà"], 0, 0, lligades)


def test_fases_de_fa_servir_les_llavors_de_cada_banda(monkeypatch):
    crides = []
    monkeypatch.setattr(fd.vt, "veritat", lambda nom: VERITAT)
    monkeypatch.setattr(fd.fonts, "partit", lambda nom: type("P", (), {"trams": DUES})())
    monkeypatch.setattr(fd, "simula", lambda *a: crides.append(a) or ())
    fd.fases_de("x", "curts ×¼", "mitjà", "provar", 0.5)
    (veritat, trams, nivell, llavor, llavor_atac, lligades), = crides
    assert veritat is VERITAT and trams == DUES and nivell == fsm.NIVELLS["mitjà"] and lligades == 0.5
    assert llavor == fd.llavor("x", "curts ×¼", "mitjà", "provar")
    assert llavor_atac == fsm.llavor("x", "curts ×¼", "mitjà", "provar")
