"""El desfasament dels canvis d'equip (T1 del pla per tocs): quins canvis de la veritat es miren, com es mesura
el canvi del mètode i com es classifica cada passada."""

from __future__ import annotations

import numpy as np
import pandas as pd

from banc import canvis
from banc.partit import PartitBanc
from banc.tests import sintetic
from cadena.llegeix import Tracking
from possessio.oficial import possession_metrics as pm

H, A, D = pm.H, pm.A, pm.D
CAMP = (100.0, 50.0)


def codis(text: str) -> np.ndarray:
    return np.array([{"H": H, "A": A, "D": D}[c] for c in text], dtype=np.int8)


def partit_amb_pilota(cami_m: np.ndarray, veritat: np.ndarray) -> PartitBanc:
    """Una part sola, amb la pilota on diu `cami_m` (en metres; NaN si falta) i un jugador quiet per equip."""
    n = len(cami_m)
    escala = np.array(CAMP)
    jugadors = np.broadcast_to(np.array([10.0, 10.0, 90.0, 40.0]).reshape(2, 1, 1, 2) / escala, (2, n, 1, 2))
    t = Tracking(fotograma=np.arange(n), pilota=cami_m / escala, casa=jugadors[0].copy(), fora=jugadors[1].copy(),
                 nom_casa="Casa", nom_fora="Fora", casa_es_home=True, camp_m=CAMP)
    return PartitBanc(nom="prova", font="dfl", tracking=t, trams=((1, 0, n - 1),), veritat=veritat,
                      pilota_z=np.full(n, np.nan))


def test_nomes_els_canvis_dins_d_una_part_i_sense_pilota_morta_entremig():
    veritat = codis("HHAADHH" + "AA")
    trams = ((1, 0, 6), (2, 7, 8))
    np.testing.assert_array_equal(canvis.canvis_de_la_veritat(veritat, trams), [2])


def test_el_desfasament_es_el_canvi_del_metode_mes_proper_cap_a_l_equip_nou():
    pred = np.full(1000, H, dtype=np.int8)
    pred[470:] = A
    assert canvis.desfasament(pred, 500, A, 0, 999) == -30
    pred[470:] = H
    pred[540:] = A
    assert canvis.desfasament(pred, 500, A, 0, 999) == 40


def test_si_el_metode_no_canvia_dins_de_la_finestra_no_hi_ha_desfasament():
    pred = np.full(1000, H, dtype=np.int8)
    assert canvis.desfasament(pred, 500, A, 0, 999) is None
    pred[500 + canvis.FINESTRA + 1:] = A
    assert canvis.desfasament(pred, 500, A, 0, 999) is None


def test_el_desfasament_no_surt_de_la_part():
    pred = np.full(1000, A, dtype=np.int8)
    pred[:300] = H
    assert canvis.desfasament(pred, 320, A, 310, 999) is None      # el canvi del mètode és a la part d'abans


def test_el_canvi_des_d_una_pilota_morta_tambe_compta():
    pred = codis("H" * 100 + "D" * 10 + "A" * 100)
    assert canvis.desfasament(pred, 105, A, 0, 209) == 5


def test_torna_si_el_metode_recupera_l_equip_d_abans_poc_despres():
    pred = np.full(1000, H, dtype=np.int8)
    pred[500:] = A
    assert not canvis.torna(pred, 500, H, 999)
    pred[500 + canvis.TORNA - 1:] = H
    assert canvis.torna(pred, 500, H, 999)
    assert not canvis.torna(pred, 500, H, 500 + canvis.TORNA - 2)    # la tornada cau fora de la part


def recta(metres_per_imatge: float, n: int = 200) -> np.ndarray:
    """La pilota quieta, i des de la imatge 100 fins a la 150, en línia recta."""
    x = 10 + metres_per_imatge * np.clip(np.arange(n) - 100, 0, 50)
    return np.column_stack([x, np.full(n, 25.0)])


def test_una_passada_es_llarga_si_la_pilota_recorre_prou_metres_abans_del_canvi():
    veritat = codis("H" * 150 + "A" * 50)
    p = partit_amb_pilota(recta(0.8), veritat)                     # 40 m en 2 s
    assert canvis.classifica(p, p, 150) == ("llarga", "amb")
    p = partit_amb_pilota(recta(0.2), veritat)                     # 10 m
    assert canvis.classifica(p, p, 150) == ("curta", "amb")


def test_sense_la_pilota_al_net_la_passada_no_es_pot_classificar():
    cami = recta(0.8)
    cami[150 - canvis.ABANS] = np.nan
    p = partit_amb_pilota(cami, codis("H" * 150 + "A" * 50))
    assert canvis.classifica(p, p, 150)[0] == "?"


def test_sense_pilota_si_al_degradat_falta_en_la_meitat_o_mes_dels_2_s_d_abans():
    cami = recta(0.2)
    net = partit_amb_pilota(cami, codis("H" * 150 + "A" * 50))
    brut = cami.copy()
    brut[150 - canvis.ABANS // 2:150] = np.nan
    assert canvis.classifica(net, partit_amb_pilota(brut, net.veritat), 150)[1] == "sense"
    brut[150 - canvis.ABANS // 2] = cami[150 - canvis.ABANS // 2]
    assert canvis.classifica(net, partit_amb_pilota(brut, net.veritat), 150)[1] == "amb"


def test_la_possessio_nova_dura_fins_que_la_veritat_canvia_o_s_acaba_la_part():
    veritat = codis("HHAAAD" + "AAAA")
    assert canvis.durada(veritat, 2, 9) == 3                      # la pilota morta l'acaba
    assert canvis.durada(veritat, 6, 7) == 2                      # la part, també


def test_una_possessio_nova_de_menys_de_2_s_es_breu():
    veritat = codis("H" * 100 + "A" * (canvis.BREU - 1) + "H" * 100)
    p = partit_amb_pilota(recta(0.2, len(veritat)), veritat)
    files = canvis.mesura(p, p, veritat, "perfecte", "net")
    assert [f["possessio"] for f in files] == ["< 2 s", "≥ 2 s"]


def test_el_metode_perfecte_canvia_sempre_a_temps():
    p = sintetic.partit(n=3000)
    files = pd.DataFrame(canvis.mesura(p, p, p.veritat, "perfecte", "net"))
    assert len(files) > 0
    assert (files["desfas_s"] == 0).all() and not files["torna"].any()
    r = canvis.resum(files)
    assert (r["a_temps"] == 1).all() and (r["cap"] == 0).all()


def test_el_resum_compta_cada_categoria():
    base = {"partit": "p", "font": "dfl", "escenari": "net", "metode": "m", "possessio": "≥ 2 s",
            "passada": "llarga", "pilota": "amb"}
    files = pd.DataFrame([{**base, "desfas_s": d, "torna": t}
                          for d, t in ((0.0, False), (-2.0, True), (1.5, False), (None, False))])
    r = canvis.resum(files).iloc[0]
    assert r["canvis"] == 4
    assert (r["a_temps"], r["abans"], r["tard"], r["cap"], r["torna"]) == (0.25, 0.25, 0.25, 0.25, 0.25)
    assert r["mediana_s"] == 0.0


def test_el_decodificador_de_cada_partit_es_el_triat_amb_els_altres():
    files = pd.DataFrame([{"partit": p, "font": "dfl", "escenari": e, "metode": "graella", "lam": lam, "d_min": 1,
                           "spell_f1": 0.6 if lam == bona else 0.3, "macro_f1": 0.5}
                          for p, bona in {"a": 1.0, "b": 4.0, "c": 4.0, "d": 4.0}.items()
                          for e in ("curts", "llargs", "barreja") for lam in (1.0, 4.0)])
    assert canvis.decodificadors(files) == {p: (4.0, 1) for p in "abcd"}


def test_el_markdown_no_porta_nan_i_te_cada_escenari():
    base = {"partit": "p", "font": "dfl", "metode": "A", "possessio": "≥ 2 s", "pilota": "amb", "torna": False}
    files = pd.DataFrame([{**base, "escenari": e, "passada": pas, "desfas_s": d}
                          for e in ("net", "barreja") for pas in ("llarga", "curta") for d in (0.0, None)]
                         + [{**base, "escenari": "net", "passada": "?", "desfas_s": None}])    # cap mediana
    text = canvis.markdown(canvis.resum(files))
    assert "nan" not in text.lower()
    assert "net" in text and "barreja" in text
