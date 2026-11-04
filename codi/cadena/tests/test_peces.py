"""Les peces de la línia base: la regla, la majoria, el pas a fotogrames del vídeo i el format del fitxer."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cadena import fitxer, regla
from possessio.oficial import possession_metrics as oficial

CAMP = (105.0, 68.0)
N = 3000
TRAMS = ((1, 100, 1399), (2, 1600, 2899))


def test_el_jugador_mes_proper_dona_l_equip():
    pilota = np.array([[0.5, 0.5], [0.1, 0.1], [np.nan, np.nan]])
    casa = np.array([[[0.51, 0.5]], [[0.9, 0.9]], [[0.5, 0.5]]])
    fora = np.array([[[0.6, 0.5]], [[0.12, 0.1]], [[0.5, 0.5]]])
    assert regla.jugador_mes_proper(pilota, casa, fora, CAMP).tolist() == ["H", "A", "X"]


def test_la_distancia_es_en_metres_i_no_en_coordenades():
    # en coordenades, el de casa és més a prop (0,05 contra 0,06); en metres, el de fora (3,4 m contra 5,3 m)
    pilota = np.array([[0.5, 0.5]])
    casa = np.array([[[0.55, 0.5]]])
    fora = np.array([[[0.5, 0.56]]])
    assert regla.jugador_mes_proper(pilota, casa, fora, CAMP).tolist() == ["A"]


def test_un_equip_sense_cap_jugador_vist_no_trenca_la_regla():
    pilota = np.array([[0.5, 0.5], [0.5, 0.5]])
    casa = np.full((2, 3, 2), np.nan)
    fora = np.array([[[0.6, 0.5], [np.nan, np.nan], [0.7, 0.5]], [[np.nan, np.nan]] * 3])
    assert regla.jugador_mes_proper(pilota, casa, fora, CAMP).tolist() == ["A", "X"]


def test_la_majoria_ignora_les_x_i_un_empat_es_x():
    assert regla.majoria(np.array(["H", "X", "A"]), 3).tolist() == ["H", "X", "A"]
    assert regla.majoria(np.array(["H", "A", "H", "H", "A"]), 3).tolist() == ["X", "H", "H", "H", "X"]


def test_la_majoria_tambe_compta_la_d():
    assert regla.majoria(np.array(["D", "D", "H", "A"]), 3).tolist() == ["D", "D", "X", "X"]
    assert regla.majoria(np.array(["D", "H", "H"]), 3).tolist() == ["X", "H", "H"]


def test_la_majoria_no_passa_d_una_part_a_l_altra():
    # tot H fins al començament de la segona part: si la finestra la creués, el primer fotograma seria un empat
    etiquetes = np.array(["H"] * 1600 + ["A"] * 1400)
    sortida = regla.per_fotograma(np.arange(N), etiquetes, N, TRAMS, finestra=50)
    assert set(sortida[1600:2900]) == {"A"} and set(sortida[100:1400]) == {"H"}


def test_fora_de_les_parts_tot_es_x():
    sortida = regla.per_fotograma(np.arange(N), np.full(N, "H"), N, TRAMS, finestra=50)
    dins = np.zeros(N, bool)
    for _, inici, fi in TRAMS:
        dins[inici:fi + 1] = True
    assert set(sortida[dins]) == {"H"} and set(sortida[~dins]) == {"X"}


def test_la_fila_de_l_atd_va_al_fotograma_que_toca():
    # DATA.md: el fotograma del vídeo és el frame_id de l'ATD menys u
    frame_id = np.arange(1, N + 1)
    etiquetes = np.where(np.arange(N) < 500, "H", "A")
    sortida = regla.per_fotograma(frame_id - 1, etiquetes, N, ((1, 0, N - 1),), finestra=1)
    assert sortida[499] == "H" and sortida[500] == "A"


def test_els_fotogrames_que_l_atd_no_porta_son_x():
    sortida = regla.per_fotograma(np.array([200, 201]), np.array(["H", "H"]), N, TRAMS, finestra=1)
    assert sortida[200] == sortida[201] == "H" and sortida[202] == "X" and len(sortida) == N


def test_un_fotograma_repetit_a_l_atd_s_atura():
    with pytest.raises(ValueError):
        regla.per_fotograma(np.array([5, 5]), np.array(["H", "A"]), N, TRAMS, finestra=1)


@pytest.fixture
def bo(tmp_path):
    cami = tmp_path / "bo.csv"
    fitxer.escriu(cami, np.where(np.arange(N) % 7 == 0, "D", "H"))
    return cami


def valida_oficial(cami, n=N):
    try:
        return oficial.validate_submission(oficial.read_label_csv(cami), n)
    except ValueError as error:
        return str(error)


def test_el_fitxer_escrit_passa_la_validacio_propia_i_l_oficial(bo):
    assert fitxer.comprova(bo, N) is None
    assert valida_oficial(bo) is None
    assert bo.read_text(encoding="utf-8").splitlines()[:3] == ["frame,label", "0,D", "1,H"]


def corromp(cami, canvi):
    linies = cami.read_text(encoding="utf-8").splitlines()
    cami.write_text("\n".join(canvi(linies)) + "\n", encoding="utf-8")


@pytest.mark.parametrize("canvi", [
    lambda ls: ls[:-1],                                              # falta ls'última fila
    lambda ls: ["frame;label"] + ls[1:],                             # capçalera
    lambda ls: ls[:1] + [ls[2], ls[1]] + ls[3:],                        # fotogrames desordenats
    lambda ls: ls[:5] + ["4,Z"] + ls[6:],                             # etiqueta de fora
    lambda ls: ls[:5] + ["4,"] + ls[6:],                              # casella buida
    lambda ls: ls[:1] + ["0.5,H"] + ls[2:],                           # fotograma que no és enter
], ids=["files", "capcalera", "ordre", "etiqueta", "buida", "enter"])
def test_la_comprovacio_rebutja_el_mateix_que_l_oficial(bo, canvi):
    corromp(bo, canvi)
    assert fitxer.comprova(bo, N) is not None
    assert valida_oficial(bo) is not None


def test_la_comprovacio_accepta_el_mateix_que_l_oficial(bo):
    # SUBMISSION.md: majúscules i espais a la capçalera i a les etiquetes s'admeten
    corromp(bo, lambda ls: [" Frame , Label "] + [f"{f}, {e.lower()} " for f, e in (x.split(",") for x in ls[1:])])
    assert fitxer.comprova(bo, N) is None
    assert valida_oficial(bo) is None


@pytest.mark.parametrize("fotograma", ["５", "٥", "0_5", "05", " +5"])
def test_la_columna_frame_nomes_admet_xifres_ascii_tal_qual(bo, fotograma):
    # l'oficial rebutja (o no sap llegir) els dígits que no són ASCII: nosaltres, mai més permissius
    corromp(bo, lambda ls: ls[:6] + [f"{fotograma},H"] + ls[7:])
    assert fitxer.comprova(bo, N) is not None


def test_les_missatges_no_porten_xifres(bo):
    corromp(bo, lambda ls: ls[:-1])
    assert not any(c.isdigit() for c in fitxer.comprova(bo, N))


def test_l_empremta_es_el_sha256(bo):
    import hashlib
    assert fitxer.empremta(bo) == hashlib.sha256(bo.read_bytes()).hexdigest()
    assert pd.read_csv(bo).shape == (N, 2)
