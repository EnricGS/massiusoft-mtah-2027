"""El lector de PFF: la veritat dels esdeveniments, el pas de 29,97 a 25 imatges per segon i un partit petit escrit en
el format de PFF (el tracking en `.jsonl.bz2`, els esdeveniments i les metadades)."""

from __future__ import annotations

import bz2
import json

import numpy as np
import pytest

from banc import pff
from possessio.oficial import possession_metrics as pm

H, A, D, X = pm.H, pm.A, pm.D, pm.X
FPS = 29.97


def test_la_veritat_es_la_de_l_ultim_esdeveniment_que_ha_començat():
    frame = np.arange(100, 112)
    inicis = [(98, H), (103, A), (106, D), (109, H)]       # el primer, abans de la part: ja hi mana
    assert pff.veritat_font(frame, inicis).tolist() == [H, H, H, A, A, A, D, D, D, H, H, H]
    assert pff.veritat_font(frame, [(104, A)]).tolist()[:5] == [D, D, D, D, A]     # abans del primer, D


def test_a_25_interpola_a_l_hora_del_video_i_deixa_nan_on_falta_un_costat():
    frame = np.arange(300, 331)                            # 30 imatges de 29,97: un segon
    valors = frame.astype(float) / FPS                     # el temps, que s'ha d'interpolar exacte
    valors[10] = np.nan
    nous, v = pff.a_25(frame, valors, FPS)
    assert np.allclose(nous * 25 / FPS, np.round(nous * 25 / FPS))                  # la graella de 25 per segon
    assert nous[0] >= 300 and nous[-1] <= 330 and len(nous) == 25
    bons = np.isfinite(v)
    assert np.allclose(v[bons], nous[bons] / FPS)
    assert np.isnan(v[(nous > 9 + 300) & (nous < 11 + 300)]).all() and bons.sum() == len(nous) - 2


def test_a_25_s_atura_si_falten_imatges():
    with pytest.raises(ValueError):
        pff.a_25(np.array([0, 1, 3]), np.zeros(3), FPS)


def jugadors(n: int, x0: float, vista: bool) -> list[dict]:
    return [{"jerseyNum": str(n + k), "confidence": "HIGH", "visibility": "VISIBLE" if vista else "ESTIMATED",
             "x": x0 + k, "y": 10.0} for k in range(2)]


def escriu_partit(carpeta, partit: int = 9) -> None:
    """Dues parts de 60 imatges de PFF (2 s), una mica de pròrroga, una imatge repetida, la pilota que es veu, és
    estimada o no hi és, i on la tele no ensenya el camp. La pilota suavitzada és en un altre lloc: no s'ha de llegir."""
    for d in ("tracking", "event-data", "metadata"):
        (carpeta / d).mkdir()
    files = []
    for part, inici in ((1, 3000), (2, 6000), (3, 9000)):
        for k in range(60):
            f = inici + k
            pilota = [] if k % 10 == 9 else [{"visibility": "ESTIMATED" if k % 10 == 8 else "VISIBLE",
                                               "x": float(k) - 30.0, "y": -5.0, "z": 0.5}]
            amagat = part == 2 and 20 <= k < 30                 # cap jugador ni la pilota a la vista
            if amagat:
                pilota = [{"visibility": "ESTIMATED", "x": 0.0, "y": 0.0, "z": 0.0}]
            fila = {"frameNum": f, "videoTimeMs": f / FPS * 1000, "period": part,
                    "homePlayers": jugadors(4, -20.0, not amagat), "awayPlayers": jugadors(7, 20.0, not amagat),
                    "homePlayersSmoothed": jugadors(4, 0.0, True), "awayPlayersSmoothed": jugadors(7, 0.0, True),
                    "balls": pilota, "ballsSmoothed": {"visibility": "VISIBLE", "x": 50.0, "y": 30.0, "z": 9.0}}
            files.append(fila)
            if f == 3010:
                files.append(dict(fila))                        # dos esdeveniments de possessió a la mateixa imatge
    with bz2.open(carpeta / "tracking" / f"{partit}.jsonl.bz2", "wt") as sortida:
        sortida.write("\n".join(json.dumps(f) for f in files) + "\n")

    def esdeveniment(id_, segons, tipus, casa=None, anul_lat=False):
        return {"gameEventId": id_, "startTime": segons, "gameEvents": {
            "gameEventType": tipus, "homeTeam": casa, "initialNonEvent": anul_lat},
            "stadiumMetadata": {"pitchLength": 100.0, "pitchWidth": 60.0}}
    esdeveniments = [
        esdeveniment(1, 3000 / FPS, "FIRSTKICKOFF", True),
        esdeveniment(2, 3020 / FPS, "OTB", False),
        esdeveniment(2, 3020 / FPS, "OTB", False),            # el mateix, amb un altre esdeveniment de possessió
        esdeveniment(3, 3030 / FPS, "OTB", True, anul_lat=True),
        esdeveniment(4, 3035 / FPS, "OTB", None),              # un duel sense equip: no compta
        esdeveniment(5, 3040 / FPS, "OUT"),
        esdeveniment(6, 3050 / FPS, "OTB", True),
        esdeveniment(7, 3059 / FPS, "END"),
        esdeveniment(8, 6000 / FPS, "SECONDKICKOFF", False),
        esdeveniment(9, 6040 / FPS, "OTB", True),
    ]
    (carpeta / "event-data" / f"{partit}.json").write_text(json.dumps(esdeveniments))
    (carpeta / "metadata" / f"{partit}.json").write_text(json.dumps([{
        "fps": FPS, "homeTeam": {"shortName": "CAS"}, "awayTeam": {"shortName": "FOR"}}]))


def test_els_esdeveniments_de_la_veritat(tmp_path):
    escriu_partit(tmp_path)
    _, cami, _ = pff.fitxers(tmp_path, 9)
    inicis = pff.esdeveniments(json.loads(cami.read_text()), FPS)
    assert inicis == [(3000, H), (3020, A), (3040, D), (3050, H), (3059, D), (6000, A), (6040, H)]


def graella(primera: int, darrera: int) -> np.ndarray:
    """Les imatges de 25 per segon dins d'una part de PFF, en imatges de PFF."""
    r = 25 / FPS
    return np.arange(np.ceil(primera * r), np.floor(darrera * r) + 1) / r


def test_un_partit_petit(tmp_path):
    escriu_partit(tmp_path)
    p = pff.llegeix(tmp_path, 9)
    assert p.nom == "pff-9" and p.font == "pff"
    u1, u2 = graella(3000, 3059) - 3000, graella(6000, 6059) - 6000
    assert [(part, b - a + 1) for part, a, b in p.trams] == [(1, len(u1)), (2, len(u2))]      # sense la pròrroga
    t = p.tracking
    assert t.casa.shape[1:] == (2, 2) and t.fora.shape[1:] == (2, 2) and t.camp_m == (100.0, 60.0)
    assert t.nom_casa == "CAS" and t.nom_fora == "FOR"
    # els jugadors i la pilota de Sportlogiq, mai els suavitzats, de metres a 0-1
    np.testing.assert_allclose(t.casa[0], [[0.3, 40 / 60], [0.31, 40 / 60]])
    np.testing.assert_allclose(t.fora[0], [[0.7, 40 / 60], [0.71, 40 / 60]])
    assert t.pilota[0].tolist() == pytest.approx([(u1[0] - 30 + 50) / 100, 25 / 60])
    assert np.nanmax(t.pilota[:, 0]) < 0.95 and np.nanmax(p.pilota_z) == pytest.approx(0.5)
    # la pilota estimada (la 8 de cada deu) o que no hi és (la 9), NaN també entre la 7 i la 8
    sense = np.isin(np.floor(u1) % 10, (7, 8, 9))
    pilota1 = t.pilota[: len(u1), 0]
    assert np.isnan(pilota1[sense]).all() and np.isfinite(pilota1[~sense]).all()
    # la veritat, a la imatge de PFF més propera; a la part 2, X on la tele no ensenya el camp
    propera1 = np.clip(np.floor(u1 + 0.5), 0, 59).astype(int)
    esperada1 = np.select([propera1 < 20, propera1 < 40, propera1 < 50, propera1 < 59], [H, A, D, H], D)
    assert p.veritat[: len(u1)].tolist() == esperada1.tolist()
    propera2 = np.clip(np.floor(u2 + 0.5), 0, 59).astype(int)
    esperada2 = np.select([(propera2 >= 20) & (propera2 < 30), propera2 < 40], [X, A], H)
    assert p.veritat[len(u1):].tolist() == esperada2.tolist()


def test_s_atura_si_una_imatge_repetida_no_es_igual(tmp_path):
    escriu_partit(tmp_path)
    cami, _, _ = pff.fitxers(tmp_path, 9)
    files = [json.loads(linia) for linia in bz2.open(cami, "rt")]
    k = next(i for i, f in enumerate(files) if f["frameNum"] == 3010)
    files[k + 1]["homePlayers"][0]["x"] = 0.0
    with bz2.open(cami, "wt") as sortida:
        sortida.write("\n".join(json.dumps(f) for f in files) + "\n")
    with pytest.raises(ValueError):
        pff.llegeix(tmp_path, 9)
