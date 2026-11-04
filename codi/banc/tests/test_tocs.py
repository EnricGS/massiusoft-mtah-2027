"""El detector de tocs al banc (T2 del pla per tocs): què compta com a trobat, què com a toc de l'equip sense
pilota, el soroll de la pilota lliure i com es trien els paràmetres."""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from banc import degrada, tocs_reals
from banc import tocs as banc_tocs
from banc.partit import PartitBanc
from cadena import tocs
from cadena.llegeix import Tracking
from possessio.oficial import possession_metrics as pm

H, A = pm.H, pm.A
CAMP = (100.0, 50.0)


def partit(cami_m: np.ndarray, veritat: np.ndarray) -> PartitBanc:
    """Una part sola, amb la pilota on diu `cami_m` (en metres) i un jugador quiet per equip."""
    n = len(cami_m)
    escala = np.array(CAMP)
    jugadors = np.broadcast_to(np.array([10.0, 10.0, 90.0, 40.0]).reshape(2, 1, 1, 2) / escala, (2, n, 1, 2))
    t = Tracking(fotograma=np.arange(n), pilota=cami_m / escala, casa=jugadors[0].copy(), fora=jugadors[1].copy(),
                 nom_casa="Casa", nom_fora="Fora", casa_es_home=True, camp_m=CAMP)
    return PartitBanc(nom="prova", font="dfl", tracking=t, trams=((1, 0, n - 1),), veritat=veritat,
                      pilota_z=np.full(n, np.nan))


def trobats(imatges: list[int], equips: list[int]) -> tocs.Tocs:
    m = len(imatges)
    return tocs.Tocs(imatge=np.array(imatges), equip=np.array(equips, dtype=np.int8), propi_m=np.zeros(m),
                     altre_m=np.full(m, np.inf), canvi_ms=np.full(m, 10.0))


def test_a_prop_mira_els_dos_costats_amb_el_marge():
    referencia = np.array([100, 200])
    np.testing.assert_array_equal(banc_tocs.a_prop(np.array([90, 89, 211, 150]), referencia, 10),
                                  [True, False, False, False])
    assert banc_tocs.a_prop(np.array([5]), np.array([], dtype=int), 10).tolist() == [False]


def test_del_mateix_equip_no_barreja_els_equips():
    imatges, equips = np.array([100, 200]), np.array([H, A], dtype=np.int8)
    trobat = banc_tocs.del_mateix_equip(imatges, equips, np.array([102, 102, 198]), np.array([H, A, A]), 5)
    np.testing.assert_array_equal(trobat, [True, False, True])


def test_mesura_els_canvis_les_accions_i_els_tocs_de_l_equip_sense_pilota():
    n = 400
    veritat = np.full(n, H, dtype=np.int8)
    veritat[100:] = A
    cami = np.column_stack([np.linspace(20, 80, n), np.full(n, 25.0)])
    net = partit(cami, veritat)
    reals = tocs_reals.Reals(imatge=np.array([100, 300]), equip=np.array([A, A], dtype=np.int8))
    # 50: de l'equip sense pilota, lluny del canvi i de les accions; 60: de l'equip que la té; 102: el canvi
    r = banc_tocs.mesura(net, net, reals, trobats([50, 60, 102], [A, H, A]))
    assert r["minuts"] == n / 25 / 60
    assert (r["canvis"], r["canvis_trobats"], r["canvis_amb_pilota"], r["trobats_amb_pilota"]) == (1, 1, 1, 1)
    assert (r["accions"], r["accions_trobades"]) == (2, 1)
    assert (r["tocs"], r["de_l_altre"], r["de_l_altre_sense_accio"]) == (3, 1, 1)


def test_un_toc_de_l_altre_equip_amb_una_accio_seva_a_prop_no_es_sospitos():
    n = 400
    veritat = np.full(n, H, dtype=np.int8)
    cami = np.column_stack([np.linspace(20, 80, n), np.full(n, 25.0)])
    net = partit(cami, veritat)
    reals = tocs_reals.Reals(imatge=np.array([210]), equip=np.array([A], dtype=np.int8))     # una desviació
    r = banc_tocs.mesura(net, net, reals, trobats([200], [A]))
    assert (r["de_l_altre"], r["de_l_altre_sense_accio"]) == (1, 0)


def test_sense_pilota_al_degradat_el_canvi_no_compta_com_a_amb_pilota():
    n = 400
    veritat = np.full(n, H, dtype=np.int8)
    veritat[100:] = A
    cami = np.column_stack([np.linspace(20, 80, n), np.full(n, 25.0)])
    net = partit(cami, veritat)
    forat = cami.copy()
    forat[90:110] = np.nan
    r = banc_tocs.mesura(net, partit(forat, veritat), tocs_reals.Reals(np.array([], int), np.array([], np.int8)),
                         trobats([102], [A]))
    assert (r["canvis_trobats"], r["canvis_amb_pilota"], r["trobats_amb_pilota"]) == (1, 0, 0)


def test_el_soroll_de_la_pilota_lliure_es_zero_si_va_recta_i_no_n_hi_ha_si_sempre_es_a_tocar():
    n = 300
    veritat = np.full(n, H, dtype=np.int8)
    recta = np.column_stack([np.linspace(30, 70, n), np.full(n, 25.0)])
    assert banc_tocs.soroll_lliure(partit(recta, veritat)) < 1e-9
    enganxada = np.tile([10.0, 11.0], (n, 1))
    assert np.isnan(banc_tocs.soroll_lliure(partit(enganxada, veritat)))


def test_el_soroll_de_la_barreja_es_multiplica_i_es_queda_amb_els_seus_forats():
    barreja = degrada.ESCENARIS["barreja"]
    doble, zero = banc_tocs.amb_soroll(2.0), banc_tocs.amb_soroll(0.0)
    assert doble.nom == zero.nom == "barreja" and doble.forats_s == barreja.forats_s
    assert doble.sigma_pilota_m == 2 * barreja.sigma_pilota_m
    assert doble.tremolor_jugadors_m == 2 * barreja.tremolor_jugadors_m
    assert zero.sigma_jugadors_m == zero.tremolor_pilota_m == 0
    assert banc_tocs.ESCENARIS[banc_tocs.nom_soroll(1.0)] == barreja


def files_falses(benefici: dict[tuple[int, float, float], dict[str, int]]) -> pd.DataFrame:
    """Una fila per escenari, font i joc de paràmetres; `benefici` diu, per a alguns jocs i escenaris, quants
    canvis troba i quants tocs inventa (dels 100 canvis amb pilota de cada fila)."""
    files = []
    for escenari, font, par in itertools.product(banc_tocs.ESCENARIS, ("dfl", "metrica"), banc_tocs.GRAELLA):
        clau = (par.k, par.canvi_ms, par.abast_m)
        trobats_, inventats = benefici.get(clau, {}).get(escenari, (10, 20))
        files.append({"partit": f"{font}-1", "font": font, "escenari": escenari, "soroll_ms": 3.0, "k": par.k,
                      "canvi_ms": par.canvi_ms, "abast_m": par.abast_m, "minuts": 45.0, "canvis": 120,
                      "canvis_trobats": trobats_ + 5, "canvis_amb_pilota": 100, "trobats_amb_pilota": trobats_,
                      "accions": 500, "accions_trobades": 200, "tocs": 900, "de_l_altre": inventats + 5,
                      "de_l_altre_sense_accio": inventats})
    return pd.DataFrame(files)


def test_es_trien_els_del_millor_benefici_de_mitjana_als_degradats_i_es_guarda_el_pitjor():
    bo = (12, 16.0, 1.5)
    millors = {e: (50, 10) for e in banc_tocs.DEGRADATS} | {"aire": (30, 25)}
    files = files_falses({bo: millors, (3, 5.0, 2.5): {"net": (95, 0)}})
    t = banc_tocs.per_parametres(files, banc_tocs.DEGRADATS)
    primer = t.iloc[0]
    assert (primer["k"], primer["canvi_ms"], primer["abast_m"]) == bo
    assert np.isclose(primer["pitjor"], 0.05)
    assert banc_tocs.triats(files) == tocs.Parametres(*bo)


def test_el_markdown_te_cada_escenari_i_cap_nan():
    text = banc_tocs.markdown(files_falses({}))
    assert "nan" not in text.lower()
    for escenari in banc_tocs.ESCENARIS:
        assert f"| {escenari} |" in text
    for factor in banc_tocs.FACTORS_SOROLL:
        assert f"| ×{factor:g} |" in text
