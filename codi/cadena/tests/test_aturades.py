"""Els senyals de l'aturada: una fila per imatge, simètrics entre equips, sense passar d'una part a l'altra; la pilota
que va cap a fora quan es perd, els jugadors que frenen o arrenquen i la pilota quieta."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from banc import degrada
from banc.tests import sintetic
from cadena import aturades, senyals
from cadena.tests.test_tocs import N, quiet, tracking, una_part


@pytest.fixture(scope="module")
def partit():
    return degrada.aplica(sintetic.partit(n=6000), "barreja")


@pytest.fixture(scope="module")
def taula(partit):
    return aturades.calcula(partit.tracking, partit.trams)


def test_una_fila_per_imatge_simetrica_entre_equips(partit, taula):
    assert len(taula) == partit.n and taula.dtypes.eq(np.float32).all()
    for col in taula.columns:
        assert col.startswith("aturada_") and not col.partition("@")[0].endswith(("_h", "_a")), col
    pd.testing.assert_frame_equal(senyals.intercanvia(taula), taula)
    t = partit.tracking
    pd.testing.assert_frame_equal(aturades.calcula(replace(t, casa=t.fora, fora=t.casa), partit.trams), taula)
    assert not set(taula.columns) & set(senyals.calcula(t, partit.trams).columns)


def test_cap_finestra_no_passa_d_una_part_a_l_altra(partit, taula):
    (_, a, b), (_, c, d) = partit.trams[:2]
    t = partit.tracking
    pilota, casa = t.pilota.copy(), t.casa.copy()
    pilota[a:b + 1], casa[a:b + 1] = pilota[a:b + 1][::-1], casa[a:b + 1][::-1]
    canviada = aturades.calcula(replace(t, pilota=pilota, casa=casa), partit.trams)
    pd.testing.assert_frame_equal(canviada.iloc[c:d + 1], taula.iloc[c:d + 1])
    assert taula.iloc[:a].isna().all().all()


def test_la_pilota_que_va_cap_a_fora_quan_es_perd():
    pilota = np.column_stack([50.0 + 20.0 / 25 * np.arange(N), np.full(N, 25.0)])       # 20 m/s cap a x = 100
    pilota[30:] = np.nan                                       # es perd a x = 74; la darrera velocitat, a 71,6 m
    t = aturades.calcula(tracking(pilota, quiet(10, 10), quiet(10, 40)), una_part())
    assert t["aturada_fora"].iloc[20] == 0 and t["aturada_a_linia"].iloc[20] == pytest.approx(1.7, abs=0.01)
    assert t["aturada_fora"].iloc[60] == 0 and t["aturada_a_linia"].iloc[60] == pytest.approx(0.1, abs=0.01)
    assert t["aturada_fora"].iloc[100] == pytest.approx(71.6 + 20 * aturades.EXTRAPOLA_S - 100, abs=0.01)
    assert t["aturada_a_linia"].iloc[100] == 0 and t["aturada_fora"].iloc[200] == t["aturada_fora"].iloc[100]


def test_un_salt_de_la_pilota_no_es_una_velocitat():
    pilota = np.tile([50.0, 25.0], (N, 1))
    pilota[30:34] = (95.0, 25.0)                                # salta 45 m d'una imatge a l'altra i es perd
    pilota[34:] = np.nan
    t = aturades.calcula(tracking(pilota, quiet(10, 10), quiet(10, 40)), una_part())
    assert t["aturada_fora"].iloc[100] == 0 and t["aturada_a_linia"].iloc[100] == aturades.LINIA_S


def test_els_jugadors_que_frenen_i_arrenquen():
    def corre(y: float) -> np.ndarray:
        x = np.concatenate([5.0 / 25 * np.arange(100), np.full(100, 20.0),                # 5 m/s, quiets, 5 m/s
                            20.0 + 5.0 / 25 * np.arange(N - 200)])
        return np.column_stack([x, np.full(N, y)])[:, None, :]

    t = aturades.calcula(tracking(quiet(50, 25)[:, 0], corre(10), corre(40)), una_part())
    assert t["aturada_frena@1s"].iloc[100] > 3 and t["aturada_frena@1s"].iloc[200] < -3
    assert t["aturada_frena@1s"].iloc[150] == pytest.approx(0.0, abs=0.01)
    assert t["aturada_frena@4s"].iloc[100] > t["aturada_frena@1s"].iloc[100]
    assert t["aturada_frenen"].iloc[100] == 1 and t["aturada_frenen"].iloc[150] == 0


def test_la_pilota_quieta():
    pilota = np.column_stack([np.concatenate([np.full(150, 50.0), 50.0 + 10.0 / 25 * np.arange(N - 150)]),
                              np.full(N, 25.0)])
    pilota[250:] = np.nan
    t = aturades.calcula(tracking(pilota, quiet(10, 10), quiet(10, 40)), una_part())
    assert t["aturada_quieta_des"].iloc[100] == pytest.approx((100 - 11) / 25, abs=0.05)   # la velocitat, en ±12
    assert t["aturada_quieta_fins"].iloc[100] == pytest.approx((141 - 100) / 25, abs=0.05)
    assert t["aturada_quieta_des"].iloc[200] == 0 and np.isnan(t["aturada_quieta_des"].iloc[270])


@pytest.mark.parametrize("trams", [()])
def test_sense_parts_s_atura(partit, trams):
    with pytest.raises(ValueError):
        aturades.calcula(partit.tracking, trams)
