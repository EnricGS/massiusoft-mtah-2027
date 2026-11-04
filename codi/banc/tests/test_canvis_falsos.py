"""Els canvis falsos d'A xarxes: quines possessions predites són inventades, entre què són, el vet amb la q, els trets
de cada possessió, l'AUC de cada tret i les taules."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from banc import canvis_falsos as cf
from banc import model_a_canvis as t3i
from possessio.oficial import possession_metrics as pm


def etiqueta(*trossos: tuple[int, int]) -> np.ndarray:
    return np.concatenate([np.full(n, codi, dtype=np.int8) for codi, n in trossos])


def test_una_possessio_es_inventada_si_la_veritat_no_hi_te_aquest_equip_a_prop():
    toc = etiqueta((pm.H, 100), (pm.A, 100))
    assert cf.inventada(toc, 150, 170, pm.H, tol=25)
    assert not cf.inventada(toc, 150, 170, pm.A, tol=25)
    assert not cf.inventada(toc, 110, 130, pm.H, tol=25)      # l'H de la veritat acaba a 100, a 10 imatges


@pytest.mark.parametrize(("pred", "a", "b", "tram", "vores"), [
    (etiqueta((pm.H, 10), (pm.A, 5), (pm.H, 10)), 10, 15, (0, 25), cf.INSERIDA),
    (etiqueta((pm.D, 10), (pm.A, 5), (pm.H, 10)), 10, 15, (0, 25), cf.AL_COSTAT),
    (etiqueta((pm.H, 10), (pm.A, 5), (pm.D, 10)), 10, 15, (0, 25), cf.AL_COSTAT),
    (etiqueta((pm.H, 10), (pm.A, 5), (pm.H, 10)), 10, 15, (10, 25), cf.AL_COSTAT),   # comença amb el tram
])
def test_les_vores_de_la_possessio(pred, a, b, tram, vores):
    assert cf.vores(pred, a, b, tram) == vores


def test_el_vet_posa_la_q_al_minim_a_la_possessio_i_a_les_vores():
    q = np.full(30, 0.5)
    vetada = cf.veta(q, [(10, 15)], k=2)
    assert np.all(vetada[8:17] == t3i.Q_MINIM)
    assert np.all(vetada[:8] == 0.5) and np.all(vetada[17:] == 0.5)
    assert np.all(q == 0.5)


def test_el_verificador_posa_l_altre_equip_o_una_aturada():
    pred = etiqueta((pm.H, 10), (pm.A, 5), (pm.H, 10), (pm.D, 5), (pm.A, 5))
    possessions = [{"a": 10, "b": 15, "k": pm.A, "vores": cf.INSERIDA},
                   {"a": 30, "b": 35, "k": pm.A, "vores": cf.AL_COSTAT}]
    assert cf.arregla(pred, possessions).tolist() == etiqueta((pm.H, 25), (pm.D, 5), (pm.H, 5)).tolist()
    assert cf.arregla(pred, possessions, pm.D).tolist() == etiqueta((pm.H, 25), (pm.D, 10)).tolist()
    assert pred[10] == pm.A


def test_tantes_bones_com_inventades_de_la_mateixa_durada():
    possessions = [{"a": i, "tram": t, "inventada": inv}
                   for i, (t, inv) in enumerate((("curta", True), ("curta", False), ("curta", False),
                                                 ("llarga", True), ("llarga", True), ("llarga", False)))]
    triades = cf.bones_com(possessions, np.random.default_rng(0))
    assert sum(f["tram"] == "curta" for f in triades) == 1
    assert [f["a"] for f in triades if f["tram"] == "llarga"] == [5]
    assert not any(f["inventada"] for f in triades)
    assert triades == cf.bones_com(possessions, np.random.default_rng(0))


def test_els_trets_de_la_possessio():
    probes = np.zeros((40, 3))
    probes[:, pm.A] = 0.6
    probes[20:25, pm.A] = 0.9
    q = np.full(40, 0.1)
    q[18] = 0.7
    vista = np.ones(40, dtype=bool)
    vista[20:22] = False
    t = cf.trets(probes, q, vista, 20, 25, pm.A, finestra=3)
    assert t == pytest.approx({"durada": 5, "confiança": 0.9, "vista": 0.6, "q a l'inici": 0.7})


def test_l_auc_de_cada_tret_diu_que_com_mes_baix_mes_inventada():
    possessions = pd.DataFrame({"inventada": [True, True, False, False],
                                "durada": [10, 20, 30, 40], "confiança": [0.9, 0.5, 0.6, 0.7]})
    assert cf.auc(possessions, "durada") == pytest.approx(1.0)
    assert cf.auc(possessions, "confiança") == pytest.approx(0.5)
    assert np.isnan(cf.auc(possessions[~possessions["inventada"]], "durada"))


def test_la_taula_de_les_inventades():
    possessions = pd.DataFrame([
        {"escenari": "net", "partit": p, "durada": d, "tram": t, "inventada": inv, "vores": v}
        for p in ("a", "b")
        for d, t, inv, v in ((20, "0,48-1 s", True, cf.INSERIDA), (40, "1-2 s", False, cf.INSERIDA),
                             (60, "2-5 s", True, cf.AL_COSTAT), (200, "≥5 s", False, cf.AL_COSTAT))])
    t = cf.taula_inventades(possessions)
    fila = t.loc["net"]
    assert fila["n predites"] == 8 and fila["n inventades"] == 4
    assert fila["part inventada"] == pytest.approx(0.5)
    assert fila["0,48-1 s"] == pytest.approx(1.0) and fila["≥5 s"] == pytest.approx(0.0)
    assert fila[f"n {cf.INSERIDA}"] == 2 and fila[f"n {cf.AL_COSTAT}"] == 2


@pytest.mark.parametrize(("abans", "ara", "mena"), [
    ({"inventada": False}, {"inventada": True}, cf.ENTRA),
    ({"inventada": True}, {"inventada": False}, cf.SURT),
    ({"inventada": True}, {"inventada": True}, cf.ENTRA),
    ({"inventada": False}, {"inventada": False}, cf.A_DESTEMPS),
])
def test_d_on_ve_un_canvi(abans, ara, mena):
    assert cf.mena(abans, ara) == mena


def test_el_desfasament_es_des_del_canvi_real_mes_proper():
    reals = np.array([100, 300])
    assert cf.desfasament(140, reals) == 40
    assert cf.desfasament(260, reals) == -40
    assert np.isnan(cf.desfasament(10, np.array([], dtype=int)))


def test_la_taula_dels_canvis_falsos():
    canvis = pd.DataFrame([
        {"escenari": "net", "fals": f, "mena": m, "desfasament": d, "al forat": af}
        for f, m, d, af in ((False, cf.A_DESTEMPS, 2.0, False), (True, cf.ENTRA, 0.0, False),
                            (True, cf.SURT, 0.0, True), (True, cf.A_DESTEMPS, 50.0, True),
                            (True, cf.A_DESTEMPS, -100.0, False))])
    fila = cf.taula_falsos(canvis).loc["net"]
    assert fila["n canvis"] == 5 and fila["n falsos"] == 4
    assert fila[f"n {cf.ENTRA}"] == 1 and fila[f"n {cf.SURT}"] == 1 and fila[f"n {cf.A_DESTEMPS}"] == 2
    assert fila["tard"] == pytest.approx(0.5) and fila["als forats"] == pytest.approx(0.5)
    assert fila["mediana (s)"] == pytest.approx(75 / pm.FPS)
