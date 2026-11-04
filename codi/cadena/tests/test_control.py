"""Els senyals del control: de qui és el darrer toc i el proper, si la pilota va amb algú, simètrics entre equips i
sense passar d'una part a l'altra."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from banc import degrada
from banc.tests import sintetic
from cadena import control, senyals
from cadena.tests.test_tocs import N, quiet, tracking, una_part, xut


@pytest.fixture(scope="module")
def partit():
    return degrada.aplica(sintetic.partit(n=6000), "barreja")


@pytest.fixture(scope="module")
def taula(partit):
    return control.calcula(partit.tracking, partit.trams)


def test_una_fila_per_imatge_i_cap_columna_sense_convencio(partit, taula):
    assert len(taula) == partit.n and taula.dtypes.eq(np.float32).all()
    simetrics = {"des_toc", "fins_toc", "tremolor", "toc_canvi_abans", "toc_canvi_despres"}
    for col in taula.columns:
        base = col.partition("@")[0]
        assert base.endswith(("_h", "_a")) or base.startswith("dif_") or base in simetrics, col
    assert not set(taula.columns) & set(senyals.calcula(partit.tracking, partit.trams).columns)


def test_intercanviar_els_equips_es_intercanviar_les_columnes(partit, taula):
    t = partit.tracking
    girat = replace(t, casa=t.fora, fora=t.casa)
    pd.testing.assert_frame_equal(control.calcula(girat, partit.trams), senyals.intercanvia(taula),
                                  check_exact=False, rtol=1e-5)


@pytest.mark.parametrize("quina", [0, 1])
def test_cap_finestra_no_passa_d_una_part_a_l_altra(partit, taula, quina):
    t = partit.tracking
    _, inici, fi = partit.trams[quina]
    rng = np.random.default_rng(5)
    canvia = {}
    for camp in ("pilota", "casa", "fora"):
        valors = getattr(t, camp).copy()
        valors[inici:fi + 1] = rng.random(valors[inici:fi + 1].shape)
        canvia[camp] = valors
    canviat = control.calcula(replace(t, **canvia), partit.trams)
    altra = np.ones(partit.n, bool)
    altra[inici:fi + 1] = False
    pd.testing.assert_frame_equal(canviat[altra], taula[altra])


def test_fora_de_les_parts_les_files_son_buides():
    t = tracking(xut(100, 15.0), quiet(19.5, 25.0), quiet(40, 40))
    taula = control.calcula(t, ((1, 50, 249),))
    assert taula.iloc[:50].isna().all().all() and taula.iloc[250:].isna().all().all()
    assert taula.iloc[50:250].drop(columns="dif_toc_penultim").notna().any().all()     # amb un sol toc, no n'hi ha


def test_el_darrer_toc_i_el_proper():
    pilota = xut(100, 15.0)
    torna = 160
    pilota[torna:, 0] = pilota[torna, 0] - 15.0 / 25 * (np.arange(N - torna))   # el rival la torna enrere
    t = tracking(pilota, quiet(19.5, 25.0), quiet(*pilota[torna] + [0.6, 0.0]))
    f = control.calcula(t, una_part())
    assert np.isnan(f["dif_toc_abans"].iloc[50]) and f["dif_toc_despres"].iloc[50] == 1
    assert f["dif_toc_abans"].iloc[130] == 1 and f["dif_toc_despres"].iloc[130] == -1
    assert f["dif_toc_abans"].iloc[200] == -1 and np.isnan(f["dif_toc_despres"].iloc[200])
    assert f["dif_toc_penultim"].iloc[200] == 1 and np.isnan(f["dif_toc_penultim"].iloc[130])
    np.testing.assert_allclose(f["des_toc"].iloc[[130, 200]], [30 / 25, 40 / 25], atol=1 / 25)
    np.testing.assert_allclose(f["fins_toc"].iloc[130], 30 / 25, atol=1 / 25)
    assert f["fins_toc"].iloc[200] == senyals.TOPALL_S and f["des_toc"].iloc[50] == senyals.TOPALL_S
    # al toc del rival, el seu jugador és a prop i el de casa, lluny
    assert f["toc_d_abans_a"].iloc[200] < 1 < f["toc_d_abans_h"].iloc[200]
    assert f["tocs_h@75"].iloc[100] == 1 and f["tocs_a@75"].iloc[100] == 0
    assert f["tocs_a@f50"].iloc[130] == 1 and f["tocs_a@p50"].iloc[130] == 0


def test_la_pilota_que_va_amb_un_jugador_la_controla_ell():
    n = 200
    pilota = np.column_stack([np.linspace(20, 40, n), np.full(n, 25.0)])            # a 2,5 m/s
    casa = pilota[:, None, :] + [0.5, 0.0]                                            # la porta un de casa
    t = tracking(pilota, casa, quiet(30, 30, n))
    f = control.calcula(t, una_part(n))
    mig = f.iloc[50:150]
    assert (mig["control_h"] == 1).all() and (mig["control_a"] == 0).all()
    assert (mig["vrel_h"] < 0.1).all() and (mig["vrel_a"] > 2).all() and (mig["dif_vrel"] < 0).all()
    assert (mig["control_h@p25"] == 1).all() and (mig["control_h@f25"] == 1).all()


def test_sense_pilota_no_hi_ha_control():
    n = 200
    pilota = np.column_stack([np.linspace(20, 40, n), np.full(n, 25.0)])
    pilota[80:120] = np.nan
    t = tracking(pilota, pilota[:, None, :] + [0.5, 0.0], quiet(30, 30, n))
    f = control.calcula(t, una_part(n))
    assert f["vrel_h"].iloc[85:115].isna().all() and (f["control_h"].iloc[85:115] == 0).all()
