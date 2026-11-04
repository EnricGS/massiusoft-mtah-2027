"""El Smart Tagging simulat del banc (T3af): les represes, al canvi de la D a un equip més proper, i les etiquetes de
cada nivell, amb els seus errors."""

from __future__ import annotations

import numpy as np

from banc import smart_tagging_simulat as sts
from cadena import smart_tagging as st
from possessio.oficial import possession_metrics as pm

H, A, D, X = pm.H, pm.A, pm.D, pm.X
SENSE_ERRORS = sts.Nivell(perdudes=0.0, desfas_s=(0.0, 0.0), tipus_canviat=0.0, equip_canviat=0.0, falses=0)


def veritat_amb_aturades(n: int, aturades: list[tuple[int, int, int]]) -> np.ndarray:
    """H a tot arreu, i D de `de` a `fins` (exclosa), seguida de l'equip que treu."""
    v = np.full(n, H, dtype=np.int8)
    for de, fins, equip in aturades:
        v[de:fins] = D
        v[fins:fins + 50] = equip
    return v


def test_la_represa_va_al_canvi_de_la_d_a_un_equip_mes_proper():
    v = veritat_amb_aturades(1000, [(100, 150, A), (250, 300, H), (320, 340, A)])
    trams = ((1, 0, 999),)
    assert sts.col_loca(v, trams, 160) == 150
    assert sts.col_loca(v, trams, 150 - 75) == 150 and sts.col_loca(v, trams, 150 - 76) is None    # 3 s o menys
    assert sts.col_loca(v, trams, 335) == 340                                   # el 340 és a 5; el 300, a 35
    assert sts.col_loca(v, trams, 335, equip=H) == 300                          # si l'esdeveniment diu l'equip
    assert sts.col_loca(v, trams, 500) is None


def test_un_canvi_entre_dues_parts_no_es_una_represa():
    v = np.r_[np.full(100, D), np.full(100, H)].astype(np.int8)
    assert sts.col_loca(v, ((1, 0, 99), (2, 100, 199)), 100) is None
    assert sts.col_loca(v, ((1, 0, 199),), 100) == 100


def test_les_represes_es_compten_i_les_repetides_no_hi_tornen():
    v = veritat_amb_aturades(1000, [(100, 150, A), (400, 450, H)])
    r = sts.represes_de(v, ((1, 0, 999),), [(150, "falta", A), (160, "falta", A), (800, "banda", H),
                                             (440, "corner", H)])
    assert r.represes == (sts.Represa(150, "falta", A), sts.Represa(450, "corner", H))
    assert (r.esdeveniments, r.no_col_locades, r.repetides) == (4, 1, 1)


def test_sense_errors_una_etiqueta_a_cada_represa_i_la_de_banda_sense_equip():
    v = veritat_amb_aturades(3000, [(100, 150, A), (1000, 1100, H)])
    represes = (sts.Represa(150, "corner", A), sts.Represa(1100, "banda", H))
    s = sts.simula(represes, v, ((1, 0, 2999),), SENSE_ERRORS, llavor=3)
    assert [(e.inici, e.tipus, e.equip) for e in s.etiquetes] == [(150, "corner", A), (1100, "banda", None)]
    assert s.de_represes == (0, 1)
    assert all(2 * 25 <= e.final - e.inici <= 10 * 25 for e in s.etiquetes)


def test_la_de_banda_mai_porta_equip_i_les_falses_nomes_on_la_veritat_es_d_un_equip():
    rng = np.random.default_rng(0)
    v = rng.choice(np.array([H, A, D, X], np.int8), 20_000)
    represes = tuple(sts.Represa(int(k), "banda", H) for k in range(100, 19_000, 400))
    tot = sts.Nivell(perdudes=0.0, desfas_s=(0.0, 0.0), tipus_canviat=0.0, equip_canviat=1.0, falses=300)
    s = sts.simula(represes, v, ((1, 0, 19_999),), tot, llavor=1)
    de_represes = s.etiquetes[:len(represes)]
    assert all(e.equip is None for e in de_represes)
    falses = s.etiquetes[len(represes):]
    assert len(falses) == 300 and all(v[e.inici] in (H, A) for e in falses)
    assert all(e.equip is None for e in falses if e.tipus == "banda")
    assert {e.tipus for e in falses} == set(st.TIPUS)


def test_un_nivell_amb_errors():
    v = np.full(400_000, H, dtype=np.int8)
    represes = tuple(sts.Represa(int(k), "corner", A) for k in range(1000, 390_000, 150))
    nivell = sts.NIVELLS["mitjà"]
    s = sts.simula(represes, v, ((1, 0, len(v) - 1),), nivell, llavor=11)
    perdudes = 1 - len(s.de_represes) / len(represes)
    assert abs(perdudes - nivell.perdudes) < 0.03
    de_represes = s.etiquetes[:len(s.de_represes)]
    desfas = np.array([e.inici - represes[i].imatge for e, i in zip(de_represes, s.de_represes)])
    assert desfas.min() >= round(nivell.desfas_s[0] * 25) and desfas.max() <= round(nivell.desfas_s[1] * 25)
    assert abs(np.mean([e.tipus != "corner" for e in de_represes]) - nivell.tipus_canviat) < 0.03
    amb_equip = [e for e in de_represes if e.tipus != "banda"]
    assert abs(np.mean([e.equip == H for e in amb_equip]) - nivell.equip_canviat) < 0.03
    assert len(s.etiquetes) - len(s.de_represes) == nivell.falses


def test_amb_la_mateixa_llavor_surt_igual_i_amb_una_altra_no():
    v = np.full(50_000, H, dtype=np.int8)
    represes = tuple(sts.Represa(int(k), "falta", A) for k in range(500, 49_000, 300))
    trams = ((1, 0, 49_999),)
    a, b = (sts.simula(represes, v, trams, sts.NIVELLS["dolent"], llavor=5) for _ in range(2))
    assert a == b
    assert sts.simula(represes, v, trams, sts.NIVELLS["dolent"], llavor=6) != a


def test_sense_etiquetes_no_n_hi_ha_cap():
    v = np.full(5000, H, dtype=np.int8)
    s = sts.simula((sts.Represa(100, "falta", A),), v, ((1, 0, 4999),), sts.NIVELLS["cap"], llavor=1)
    assert s.etiquetes == () and s.de_represes == ()


def test_l_inici_no_surt_de_la_part_ni_el_final():
    v = np.full(1000, H, dtype=np.int8)
    enrere = sts.Nivell(perdudes=0.0, desfas_s=(-8.0, -8.0), tipus_canviat=0.0, equip_canviat=0.0, falses=0)
    s = sts.simula((sts.Represa(510, "falta", A), sts.Represa(990, "falta", A)), v, ((1, 0, 499), (2, 500, 999)),
                   enrere, llavor=2)
    assert [e.inici for e in s.etiquetes] == [500, 790]
    assert all(e.final <= 999 for e in s.etiquetes)


def test_les_llavors_no_depenen_de_l_atzar_del_proces_i_les_de_provar_no_son_les_d_aprendre():
    assert sts.llavor("dfl-J03WMX", "net", "mitjà", "provar") == sts.llavor("dfl-J03WMX", "net", "mitjà", "provar")
    assert sts.llavor("dfl-J03WMX", "net", "mitjà", "provar") != sts.llavor("dfl-J03WMX", "net", "mitjà", "aprendre")
    nivells = {sts.nivell_per_aprendre(f"p{i}", e) for i in range(30) for e in ("net", "curts")}
    assert nivells == set(sts.NIVELLS)


def test_els_tipus_dels_esdeveniments():
    assert [sts.TIPUS_DFL[k] for k in ("ThrowIn", "CornerKick", "GoalKick", "FreeKick", "KickOff", "Penalty")] == \
        ["banda", "corner", "porta", "falta", "sortida", "falta"]
    assert [sts.tipus_metrica(s) for s in ("THROW IN", "THROW IN-RETAKEN", "CORNER KICK", "FREE KICK-INDIRECT",
                                            "KICK OFF", "KICK OFF-RETAKEN", "PENALTY", "GOAL KICK", "ALTRA")] == \
        ["banda", "banda", "corner", "falta", "sortida", "sortida", "falta", "porta", None]
