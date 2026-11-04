"""El lector de SkillCorner: la veritat de la mateixa mena que la de DFL, el pas a 25 imatges per segon i un partit
petit escrit en el format de SkillCorner."""

from __future__ import annotations

import json

import numpy as np
import pytest

from banc import skillcorner
from possessio.oficial import possession_metrics as pm

H, A = pm.H, pm.A


def test_la_veritat_d_fora_de_les_fases_i_l_equip_de_l_ultima_possessio():
    frame = np.arange(12)
    periode = np.ones(12, dtype=int)
    grup = np.array([H, -1, -1, A, -1, -1, -1, -1, H, -1, -1, A], dtype=np.int8)
    fases = [(1, 5), (7, 10)]                  # la segona comença sense possessió: X fins a la primera
    v = skillcorner.veritat_font(periode, frame, grup, fases)
    assert v.tolist() == [pm.D, pm.X, pm.X, A, A, A, pm.D, pm.X, H, H, H, pm.D]


def test_a_25_interpola_i_deixa_nan_on_falta_un_costat():
    frame = np.arange(10, 15)
    valors = np.array([0.0, 1.0, np.nan, 3.0, 4.0])
    nous, v = skillcorner.a_25(frame, valors)
    assert nous[0] == 10 and nous[-1] == 14 and len(nous) == 11            # 4 imatges de 0,1 s = 10 de 0,04 s
    assert v[1] == pytest.approx(0.4) and np.isnan(v[3]) and np.isnan(v[5]) and v[-1] == 4.0


def test_a_25_s_atura_si_falten_imatges():
    with pytest.raises(ValueError):
        skillcorner.a_25(np.array([0, 1, 3]), np.zeros(3))


def escriu_partit(carpeta, partit: int = 7, n: int = 40) -> None:
    d = carpeta / "matches" / str(partit)
    d.mkdir(parents=True)
    jugadors = [{"id": 100 + k, "team_id": 1 if k < 2 else 2} for k in range(4)]
    (d / f"{partit}_match.json").write_text(json.dumps({
        "pitch_length": 100, "pitch_width": 60, "home_team": {"id": 1, "short_name": "Casa"},
        "away_team": {"id": 2, "short_name": "Fora"}, "players": jugadors}))
    files = []
    for f in range(n):
        periode = None if f < 2 else (1 if f < 20 else 2)
        buit = 30 <= f < 33                                     # una repetició: cap jugador
        files.append({"frame": f, "period": periode,
                      "ball_data": {"x": float(f), "y": 0.0, "z": 0.1, "is_detected": f % 7 != 0},
                      "possession": {"player_id": None, "group": "home team" if f < 25 else "away team"},
                      "player_data": [] if buit else [{"player_id": 100 + k, "x": -50.0 + k, "y": 30.0,
                                                        "is_detected": True} for k in range(4)]})
    (d / f"{partit}_tracking_extrapolated.jsonl").write_text("\n".join(json.dumps(f) for f in files) + "\n")
    (d / f"{partit}_phases_of_play.csv").write_text("frame_start,frame_end\n2,15\n21,39\n")


def test_un_partit_petit(tmp_path):
    escriu_partit(tmp_path)
    p = skillcorner.llegeix(tmp_path, 7)
    assert p.nom == "skillcorner-7" and p.font == "skillcorner"
    assert [(part, b - a + 1) for part, a, b in p.trams] == [(1, 43), (2, 48)]      # 2-19 i 20-39, a 25 per segon
    assert p.tracking.casa.shape[1:] == (2, 2) and p.tracking.fora.shape[1:] == (2, 2)
    assert p.tracking.casa[0, 0].tolist() == [0.0, 1.0] and p.tracking.camp_m == (100.0, 60.0)
    v = p.veritat
    viva = 39 - 5                         # fins a la imatge 38 (15,2 de la font), la més propera és la 15: viva
    assert set(v[:viva].tolist()) == {H} and set(v[viva:43].tolist()) == {pm.D}
    i_buit = round(30 * 2.5) - 50 + 43                                                   # la imatge 30, a la part 2
    assert v[i_buit] == pm.X and v[43 + round(23 * 2.5) - 50] == H
    assert np.isnan(p.tracking.pilota[round(7 * 2.5) - 5, 0])                           # 7 no es veu
