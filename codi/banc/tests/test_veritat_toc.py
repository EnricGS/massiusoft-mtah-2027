"""La veritat de toc (T3q): cada cas de `de_toc`, la lectura dels tocs de DFL i on es col·loquen."""

from __future__ import annotations

import numpy as np
import pytest

from banc import veritat_toc as vt
from possessio.oficial import possession_metrics as pm

H, A, D, X = pm.H, pm.A, pm.D, pm.X


def tros(*parts: tuple[int, int]) -> np.ndarray:
    return np.concatenate([np.full(n, codi, dtype=np.int8) for codi, n in parts])


def test_dfl_tard_es_de_l_equip_nou_des_del_toc():
    v = tros((H, 100), (A, 100))                       # DFL hi passa la possessió a la 100
    nova, casos = vt.de_toc(v, [(70, A)])
    assert np.all(nova[:70] == H) and np.all(nova[70:] == A)
    assert casos["tard"] == 1


def test_dins_del_marge_no_es_toca():
    v = tros((H, 100), (A, 100))
    nova, casos = vt.de_toc(v, [(100 - vt.MARGE, A)])
    assert np.array_equal(nova, v)
    assert casos["dins del marge"] == 1


def test_un_rebot_es_una_possessio_fins_al_toc_seguent():
    v = tros((H, 200))
    nova, casos = vt.de_toc(v, [(50, A), (60, H)])
    assert np.all(nova[50:60] == A) and np.all(nova[:50] == H) and np.all(nova[60:] == H)
    assert casos["rebot"] == 1


def test_un_toc_que_acaba_a_la_morta():
    v = tros((H, 100), (D, 50), (H, 50))
    nova, casos = vt.de_toc(v, [(80, A)])
    assert np.all(nova[80:100] == A) and np.all(nova[100:150] == D)
    assert casos["fins a la morta"] == 1


def test_sense_final_no_es_toca():
    v = tros((H, 200))
    nova, casos = vt.de_toc(v, [(10, A)])
    assert np.array_equal(nova, v)
    assert casos["sense final"] == 1


def test_el_toc_de_l_equip_que_ja_la_te_i_a_la_morta_no_fa_res():
    v = tros((H, 100), (D, 100))
    nova, casos = vt.de_toc(v, [(20, H), (150, A)])
    assert np.array_equal(nova, v)
    assert sum(casos.values()) == 0


def test_la_d_i_la_x_no_canvien_mai():
    rng = np.random.default_rng(3)
    v = np.repeat(rng.choice([H, A, D, X], 200), rng.integers(1, 40, 200)).astype(np.int8)
    tocs = sorted((int(k), int(e)) for k, e in zip(rng.integers(0, len(v), 300), rng.choice([H, A], 300)))
    nova, _ = vt.de_toc(v, tocs)
    vt.comprova(v, nova)
    assert np.all(nova[v == H] != D) and np.all(np.isin(nova[np.isin(v, (H, A))], (H, A)))


def test_comprova_atura_si_canvia_la_d():
    v = tros((H, 10), (D, 10))
    with pytest.raises(ValueError):
        vt.comprova(v, tros((H, 11), (D, 9)))


ESDEVENIMENTS = """<Event MatchId="M" EventTime="2023-05-27T15:30:15.000+02:00" EventId="1">
 <Play Player="P1" Team="CASA" Evaluation="successfullyCompleted">
  <Pass/>
 </Play>
</Event>
<Event MatchId="M" EventTime="2023-05-27T15:30:16.000+02:00" EventId="2">
 <TacklingGame WinnerTeam="FORA" Winner="P2" WinnerResult="ballcontactSucceeded" LoserTeam="CASA" Loser="P1"/>
</Event>
<Event MatchId="M" EventTime="2023-05-27T15:30:17.000+02:00" EventId="3">
 <TacklingGame WinnerTeam="FORA" Winner="P2" WinnerResult="fouled" LoserTeam="CASA" Loser="P1"/>
</Event>
<Event MatchId="M" EventTime="2023-05-27T15:30:18.000+02:00" EventId="4">
 <Foul TeamFouler="CASA" Fouler="P1"/>
</Event>
<Event MatchId="M" EventTime="2023-05-27T15:30:19.000+02:00" EventId="5">
 <OtherBallAction Player="P2" Team="FORA"/>
</Event>
<Event MatchId="M" EventTime="2023-05-27T15:30:25.000+02:00" EventId="6">
 <FreeKick Team="CASA">
  <Play Player="P3" Team="CASA">
   <Pass/>
  </Play>
 </FreeKick>
</Event>
"""


def test_tocs_dfl_llegeix_els_tocs_els_duels_amb_toc_i_les_represes():
    """També l'esdeveniment que va just després d'un d'una sola línia (el duel amb falta)."""
    tocs = vt.tocs_dfl(ESDEVENIMENTS, "CASA")
    assert [(t.tipus, t.jugador, t.equip) for t in tocs] == [
        ("Play", "P1", H), ("TacklingGame", "P2", A), ("OtherBallAction", "P2", A), ("Play", "P3", H)]
    assert tocs[1].temps - tocs[0].temps == pytest.approx(1.0)


def test_col_loca_a_la_imatge_mes_propera_i_no_si_es_lluny():
    n = 400
    imatges = np.arange(1000, 1000 + n)
    temps = np.arange(n) / pm.FPS
    pilota = {int(i): (float(k), 0.0) for k, i in enumerate(imatges)}           # la pilota avança 1 m per imatge
    a_prop = {int(i): (230.5, 0.0) for i in imatges}                             # a 0,5 m de la pilota a la 230
    lluny = {int(i): (230.0, 5.0) for i in imatges}                              # mai a menys de 5 m
    tr = vt.TrackingDFL({"BALL": pilota, "P1": a_prop, "P2": lluny}, imatges, temps, np.full(n, H, np.int8))
    tocs = [vt.Toc(250 / pm.FPS, "Play", "P1", A), vt.Toc(250 / pm.FPS, "Play", "P2", A),
            vt.Toc(250 / pm.FPS, "Play", "P3", A)]
    assert vt.col_loca(tr, tocs) == [(230, A)]
