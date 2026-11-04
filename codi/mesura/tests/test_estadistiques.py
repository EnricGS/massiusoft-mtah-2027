"""Les mesures de l'ATD, amb un tracking sintètic on se sap què ha de sortir."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from cadena.llegeix import Tracking
from mesura import estadistiques as est

CAMP = (105.0, 68.0)
FPS = est.FPS


def tracking(pilota_m: np.ndarray, jugadors_m: np.ndarray) -> Tracking:
    escala = np.array(CAMP)
    return Tracking(fotograma=np.arange(len(pilota_m)), pilota=pilota_m / escala, casa=jugadors_m[:, :11] / escala,
                    fora=jugadors_m[:, 11:] / escala, nom_casa="Casa", nom_fora="Fora", casa_es_home=True,
                    camp_m=CAMP)


def test_les_tirades_son_els_trossos_seguits():
    inicis, finals = est.tirades(np.array([0, 1, 1, 0, 1, 0, 0, 1], bool))
    assert inicis.tolist() == [1, 4, 7] and finals.tolist() == [3, 5, 8]


def test_la_llargada_dels_forats_es_compta_per_imatges():
    llargades = np.array([FPS // 2, 2 * FPS, 30 * FPS])               # 0,5 s, 2 s i 30 s
    parts = est.parts_per_llargada(llargades, est.VORES_FORAT_S)
    assert parts.sum() == pytest.approx(1.0)
    assert parts.tolist() == pytest.approx([12 / 812, 50 / 812, 0, 0, 750 / 812])


def test_les_imatges_que_no_es_puntuen_tallen_els_forats():
    n = 10 * FPS
    pilota = np.full((n, 2), 50.0)
    pilota[2 * FPS:8 * FPS] = np.nan                                  # un forat de 6 s
    jugadors = np.full((n, 22, 2), 40.0)
    jugadors[..., 0] += 3.0 * np.arange(n)[:, None] / FPS              # corren: el forat és en joc
    puntuat = est.puntuades(n, ((1, 0, 5 * FPS - 1), (2, 5 * FPS, n - 1)))
    puntuat[5 * FPS] = False                                          # el tall entre les parts
    m = est.de_la_pilota(tracking(pilota, jugadors), puntuat)
    assert m["forats_1_3s"] + m["forats_3_8s"] == pytest.approx(1.0)
    assert m["forats_3_8s"] == pytest.approx(0.5, abs=0.01)           # dos de 3 s, i no un de 6


def amb_estones_quietes(n: int, falta_quiet: float, falta_actiu: float, llavor: int = 3) -> Tracking:
    """Jugadors que corren a estones de 10 s i van quiets a les altres; la pilota hi falta a cada tipus d'estona en
    la part que es diu."""
    rng = np.random.default_rng(llavor)
    quiet = (np.arange(n) // (10 * FPS)) % 2 == 0
    velocitat = np.where(quiet, 0.3, 5.0)[:, None, None] / FPS
    jugadors = 50 + np.cumsum(velocitat * np.ones((n, 22, 2)), axis=0) % 40
    pilota = jugadors[:, 0] + 1.0
    falta = np.where(quiet, rng.random(n) < falta_quiet, rng.random(n) < falta_actiu)
    pilota[falta] = np.nan
    return tracking(pilota, jugadors)


def test_si_la_pilota_falta_quan_els_jugadors_van_quiets_ho_diu():
    n = 200 * FPS
    puntuat = np.ones(n, bool)
    morta = est.de_la_pilota(amb_estones_quietes(n, 0.9, 0.1), puntuat)
    assert morta["falta_quiets"] == pytest.approx(0.9, abs=0.03) and morta["falta_corren"] == pytest.approx(0.1, abs=0.03)
    assert est.de_la_pilota(amb_estones_quietes(n, 0.4, 0.4), puntuat)["falta_quiets"] == pytest.approx(0.4, abs=0.03)


def test_nomes_compten_els_forats_sense_cap_imatge_quieta():
    quiet = np.zeros(100, bool)
    quiet[50] = True
    inicis, finals = np.array([0, 40, 70]), np.array([10, 60, 95])     # el del mig té una imatge quieta
    assert est.forats_en_joc(inicis, finals, quiet).tolist() == [10, 25]


def test_la_falta_amb_els_jugadors_quiets_no_depen_de_quanta_estona_van_quiets():
    rng = np.random.default_rng(7)
    for part_quiets in (0.15, 0.4):
        activitat = np.where(rng.random(20_000) < part_quiets, 0.3, 4.0)
        falta = np.where(activitat < 1, rng.random(20_000) < 0.95, rng.random(20_000) < 0.3)
        quiets = est.quiets(activitat, np.ones(20_000, bool))
        assert est.falta_si(falta, quiets) == pytest.approx(0.95, abs=0.02)


def test_els_forats_que_comencen_amb_la_pilota_rapida():
    n = 200 * FPS
    t = np.arange(n)
    rapida = (t // FPS) % 4 == 0                                       # un segon de cada quatre, a 20 m/s
    pilota = np.cumsum(np.where(rapida, 20.0, 2.0)[:, None] / FPS * np.array([[1.0, 0.0]]), axis=0) % 100
    pilota[:, 1] = 30.0
    jugadors = np.full((n, 22, 2), np.nan)
    rng = np.random.default_rng(5)                                     # els jugadors, a velocitats que no hi tenen
    passos = np.repeat(rng.uniform(0.5, 6.0, n // FPS + 1), FPS)[:n] / FPS   # res a veure, perquè n'hi hagi
    jugadors[:, 0, 0] = 5.0 + np.cumsum(passos) % 30                   # de quiets i d'actius
    jugadors[:, 0, 1] = 60.0
    falta = np.zeros(n, bool)
    for inici in np.flatnonzero(rapida & (t % FPS == FPS - 2))[::2]:  # forats que comencen al final d'un segon ràpid
        falta[inici + 1:inici + 10] = True
    pilota[falta] = np.nan
    m = est.de_la_pilota(tracking(pilota, jugadors), np.ones(n, bool))
    assert m["inici_rapida"] > 1.0 and m["inici_aglomeracio"] == pytest.approx(0.0, abs=0.05)


def test_les_estones_dels_jugadors():
    n = 100 * FPS
    jugadors = np.full((n, 22, 2), 30.0)
    jugadors[:, 0] = np.nan
    jugadors[:FPS, 0] = 30.0                                           # un tros d'1 s
    jugadors[: 5 * FPS, 1] = np.nan                                    # un tros de 95 s, i la resta, de 100 s
    m = est.dels_jugadors(tracking(np.full((n, 2), 50.0), jugadors), np.ones(n, bool))
    total = FPS + 95 * FPS + 20 * n
    assert m["peces_fins_2s"] == pytest.approx(FPS / total) and m["peces_mes_60s"] == pytest.approx(1 - FPS / total)


def test_un_quocient_sense_cap_cas_es_zero_i_amb_pocs_casos_s_acosta_a_zero():
    assert est.quocient(0, 30, 0, 5000) == 0.0
    assert abs(est.quocient(1, 2, 100, 5000)) < abs(est.quocient(50, 100, 100, 5000))


def test_la_clau_canvia_si_canvien_les_mesures(tmp_path, monkeypatch):
    clau = est.clau()
    copia = tmp_path / "estadistiques.py"
    copia.write_bytes(Path(est.__file__).read_bytes() + b"\n# canvi\n")
    monkeypatch.setattr(est, "__file__", str(copia))
    assert est.clau() != clau
