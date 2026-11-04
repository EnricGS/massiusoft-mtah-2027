"""Les fases simulades del banc (T3ak): cada pas fa el que diu, el nivell sense fases, i les llavors."""

from __future__ import annotations

import numpy as np

from banc import fases_simulades as fsm
from cadena.fases import Fase
from possessio.oficial import possession_metrics as pm

H, A, D = pm.H, pm.A, pm.D
TRAMS = ((1, 0, 2999),)
EXACTE = fsm.Nivell(minima_s=2, junta_s=1, perdudes=0.0, desfas_s=0.0, curta=0.0, equip_canviat=0.0, falses=0)


def tira(*trossos: tuple[int, int]) -> np.ndarray:
    out = np.concatenate([np.full(n, codi, dtype=np.int8) for codi, n in trossos])
    return np.concatenate([out, np.full(3000 - len(out), D, dtype=np.int8)])


VERITAT = tira((D, 100), (H, 300), (A, 15), (H, 286), (D, 50), (A, 50), (D, 50), (H, 20), (D, 100), (A, 300),
               (D, 11), (A, 200), (D, 100), (H, 200), (A, 5), (H, 5), (A, 5), (H, 200))


def test_sense_errors_les_possessions_i_les_que_en_cobreixen_dues():
    fases = fsm.simula(VERITAT, TRAMS, EXACTE, 0)
    assert fases == (Fase(100, 700, H),          # passa per sobre de l'A de 15 imatges
                     Fase(751, 800, A),          # 2 s justos: sí; l'H de 20 imatges, no
                     Fase(971, 1270, A),         # entremig, només D: no s'ajunten
                     Fase(1282, 1481, A),
                     Fase(1582, 1781, H),        # entremig, dues de l'A i una de l'H: no s'ajunten
                     Fase(1797, 1996, H))


def test_perdudes_equip_i_curtes():
    assert fsm.simula(VERITAT, TRAMS, EXACTE._replace(perdudes=1.0), 0) == ()
    girades = fsm.simula(VERITAT, TRAMS, EXACTE._replace(equip_canviat=1.0), 0)
    assert [f.equip for f in girades] == [1 - f.equip for f in fsm.simula(VERITAT, TRAMS, EXACTE, 0)]
    for llavor in range(5):
        exactes = fsm.simula(VERITAT, TRAMS, EXACTE, llavor)
        curtes = fsm.simula(VERITAT, TRAMS, EXACTE._replace(curta=1.0), llavor)
        assert len(curtes) == len(exactes)
        assert all(c.inici == e.inici and c.inici <= c.final <= e.final for c, e in zip(curtes, exactes))


def test_el_desfasament():
    exactes, d = fsm.simula(VERITAT, TRAMS, EXACTE, 0), round(0.5 * pm.FPS)
    for llavor in range(5):
        mogudes = fsm.simula(VERITAT, TRAMS, EXACTE._replace(desfas_s=0.5), llavor)
        assert len(mogudes) == len(exactes)
        assert all(abs(m.inici - e.inici) <= d and abs(m.final - e.final) <= d for m, e in zip(mogudes, exactes))
    assert any(m != e for m, e in zip(fsm.simula(VERITAT, TRAMS, EXACTE._replace(desfas_s=0.5), 1), exactes))


def test_les_falses():
    fases = fsm.simula(VERITAT, ((1, 0, 1499), (2, 1500, 2999)), EXACTE._replace(perdudes=1.0, falses=40), 3)
    assert len(fases) == 40
    for f in fases:
        part = (0, 1499) if f.inici <= 1499 else (1500, 2999)
        assert VERITAT[f.inici] in (H, A) and part[0] <= f.inici <= f.final <= part[1]
        assert f.final - f.inici + 1 <= 10 * pm.FPS and (f.final == part[1] or f.final - f.inici + 1 >= 2 * pm.FPS)
    assert {f.equip for f in fases} == {H, A}


def test_dins_de_la_part():
    trams = ((1, 0, 1000), (2, 1001, 2999))
    for llavor in range(5):
        for f in fsm.simula(VERITAT, trams, fsm.NIVELLS["dolent"], llavor):
            part = (0, 1000) if f.inici <= 1000 else (1001, 2999)
            assert part[0] <= f.inici <= f.final <= part[1] and f.equip in (H, A)


def test_sense_fases_i_les_llavors():
    assert fsm.simula(VERITAT, TRAMS, fsm.NIVELLS["cap"], 0) == ()
    a = fsm.simula(VERITAT, TRAMS, fsm.NIVELLS["mitjà"], 7)
    assert a == fsm.simula(VERITAT, TRAMS, fsm.NIVELLS["mitjà"], 7)
    assert a != fsm.simula(VERITAT, TRAMS, fsm.NIVELLS["mitjà"], 8)


def test_els_nivells_del_pla():
    assert fsm.NIVELLS == {
        "bo": fsm.Nivell(2, 1, 0.10, 0.5, 0.10, 0.01, 2),
        "mitjà": fsm.Nivell(4, 2, 0.30, 2.0, 0.30, 0.05, 10),
        "dolent": fsm.Nivell(6, 4, 0.50, 4.0, 0.50, 0.15, 30),
        "cap": None}
