"""Els escenaris de degradació: que arribin al que diu DATA.md, que siguin deterministes i que no inventin res."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from banc import degrada
from banc.tests import sintetic
from possessio.oficial import possession_metrics as pm

SENSE_SOROLL = dict(sigma_jugadors_m=0.0, sigma_pilota_m=0.0, tremolor_jugadors_m=0.0, tremolor_pilota_m=0.0)


@pytest.fixture(scope="module")
def net():
    return sintetic.partit()


def llargades(absent: np.ndarray) -> np.ndarray:
    vores = np.diff(np.r_[0, absent.astype(np.int8), 0])
    return np.flatnonzero(vores == -1) - np.flatnonzero(vores == 1)


def test_l_escenari_net_no_toca_res(net):
    assert degrada.aplica(net, "net") is net


@pytest.mark.parametrize("nom", list(degrada.ESCENARIS))
def test_arriba_al_que_diu_data_md(net, nom):
    resum = degrada.resum(degrada.aplica(net, nom))
    assert resum["pilota_absent_viva"] == pytest.approx(0.41, abs=0.005)
    assert 0.405 <= resum["pilota_absent_morta"] <= 0.55 and resum["pilota_absent"] == pytest.approx(0.41, abs=0.04)
    assert resum["objectes"] == pytest.approx(20.5, abs=0.25)
    assert resum["slots"] == pytest.approx(46, abs=2)


def test_els_forats_curts_son_mes_curts_que_els_llargs(net):
    curts = llargades(np.isnan(degrada.aplica(net, "curts").tracking.pilota[:, 0]))
    llargs = llargades(np.isnan(degrada.aplica(net, "llargs").tracking.pilota[:, 0]))
    assert np.median(curts) < 3 * degrada.FPS < np.median(llargs)


def test_es_determinista_i_cada_partit_te_la_seva_llavor(net):
    a, b = degrada.aplica(net, "barreja"), degrada.aplica(net, "barreja")
    assert np.array_equal(a.tracking.pilota, b.tracking.pilota, equal_nan=True)
    assert np.array_equal(a.tracking.casa, b.tracking.casa, equal_nan=True)
    altre = degrada.aplica(replace(net, nom="un altre"), "barreja")
    assert not np.array_equal(a.tracking.pilota, altre.tracking.pilota, equal_nan=True)


def test_la_pilota_es_perd_mes_a_l_aire_i_en_aglomeracions(net):
    esc = degrada.ESCENARIS["curts"]
    aire, aglomeracio = degrada.aire_i_aglomeracio(net, esc)
    absent = np.isnan(degrada.aplica(net, "curts").tracking.pilota[:, 0])
    dificil = aire | aglomeracio
    assert dificil.any() and (~dificil).any()
    assert absent[dificil].mean() > absent[~dificil].mean()


def test_sense_alcada_fa_servir_la_velocitat(net):
    sense_z = replace(net, pilota_z=np.full(net.n, np.nan))
    aire, _ = degrada.aire_i_aglomeracio(sense_z, degrada.ESCENARIS["curts"])
    assert aire.dtype == bool and len(aire) == net.n


def test_els_slots_nous_nomes_porten_posicions_que_hi_eren(net):
    esc = replace(degrada.ESCENARIS["barreja"], duplicats=0.0, **SENSE_SOROLL)
    brut = degrada.aplica(net, esc)
    for equip in ("casa", "fora"):
        abans, despres = getattr(net.tracking, equip), getattr(brut.tracking, equip)
        for f in range(0, net.n, 997):
            vistes = despres[f][~np.isnan(despres[f, :, 0])]
            assert all(np.isclose(abans[f], v).all(axis=1).any() for v in vistes)
            assert len(vistes) <= len(abans[f])


def test_els_duplicats_fan_passar_de_vint_i_dos(net):
    brut = degrada.aplica(net, replace(degrada.ESCENARIS["barreja"], duplicats=0.05))
    vistos = (~np.isnan(brut.tracking.casa[..., 0])).sum(1) + (~np.isnan(brut.tracking.fora[..., 0])).sum(1)
    assert vistos.max() > 22


def test_no_treu_la_pilota_d_on_no_es_puntua_ni_passa_d_una_part_a_l_altra(net):
    # la segona part sense veritat, i forats d'un minut a la primera, tota en joc: si un forat hi passés, es veuria
    sense_veritat = np.where(net.veritat == pm.D, pm.H, net.veritat).astype(np.int8)
    _, inici, fi = net.trams[1]
    sense_veritat[inici:fi + 1] = pm.X
    esc = replace(degrada.ESCENARIS["llargs"], forats_s=((60.0, 60.0, 1.0),), **SENSE_SOROLL)
    brut = degrada.aplica(replace(net, veritat=sense_veritat), esc)
    assert not np.isnan(brut.tracking.pilota[inici:, 0]).any()
    assert np.isnan(brut.tracking.pilota[:inici, 0]).mean() == pytest.approx(0.41, abs=0.02)


def test_si_la_font_ja_no_te_la_pilota_quan_es_morta_la_viva_tambe_s_embruta(net):
    # com a Metrica: sense pilota a totes les aturades
    t = net.tracking
    pilota = t.pilota.copy()
    pilota[net.veritat == pm.D] = np.nan
    com_metrica = replace(net, tracking=replace(t, pilota=pilota))
    resum = degrada.resum(degrada.aplica(com_metrica, "curts"))
    assert resum["pilota_absent_viva"] == pytest.approx(0.41, abs=0.02)
    assert resum["pilota_absent_morta"] == 1.0


def test_la_projeccio_no_mou_la_pilota_que_va_per_terra():
    pilota = np.array([[30.0, 20.0], [80.0, 60.0]])
    np.testing.assert_allclose(degrada.projecta(pilota, np.zeros(2), (105.0, 68.0), (15.0, 25.0)), pilota)


def test_la_projeccio_allunya_de_la_camera_la_pilota_alta():
    # la càmera és a mig camp, a 25 m de la banda i a 15 m d'alçada: (52,5, −25, 15)
    sortida = degrada.projecta(np.array([[52.5, 34.0]]), np.array([5.0]), (105.0, 68.0), (15.0, 25.0))
    np.testing.assert_allclose(sortida, [[52.5, -25.0 + 59.0 * 15.0 / 10.0]])


def test_sense_l_alcada_de_la_pilota_no_es_projecta():
    pilota = np.array([[30.0, 20.0], [np.nan, np.nan]])
    sortida = degrada.projecta(pilota, np.full(2, np.nan), (105.0, 68.0), (15.0, 25.0))
    np.testing.assert_array_equal(np.isnan(sortida), np.isnan(pilota))
    np.testing.assert_allclose(sortida[0], pilota[0])


def test_l_escenari_aire_mou_la_pilota_alta_i_la_baixa_no(net):
    sense = replace(degrada.ESCENARIS["aire"], **SENSE_SOROLL)
    brut = degrada.aplica(net, sense)
    camp = np.array(net.tracking.camp_m)
    vista = ~np.isnan(brut.tracking.pilota[:, 0])
    desplacada = np.linalg.norm((brut.tracking.pilota - net.tracking.pilota) * camp, axis=1)
    alta = np.nan_to_num(net.pilota_z) > 3                   # 4 m: com a mínim, 25 m · 4 / 11 de la càmera
    assert desplacada[vista & alta].min() > 5
    assert desplacada[vista & ~alta].max() < 2               # 0,2 m: el centre de la pilota, per terra


def test_el_soroll_doble_dobla_l_error_de_la_barreja():
    barreja, doble = degrada.ESCENARIS["barreja"], degrada.ESCENARIS["soroll2"]
    assert doble.forats_s == barreja.forats_s
    for camp in SENSE_SOROLL:
        assert getattr(doble, camp) == 2 * getattr(barreja, camp)
