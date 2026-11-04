"""Els senyals del darrer contacte: de qui és el darrer, el proper i el penúltim, quant fa, quant falta, quant duren
i si eren disputats; per a cada radi, simètrics entre equips i sense passar d'una part a l'altra."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from banc import degrada
from banc.tests import sintetic
from cadena import contacte, control, senyals
from cadena.tests.test_tocs import N, quiet, tracking, una_part

PILOTA = (50.0, 30.0)
LLUNY_H, LLUNY_A = (10.0, 10.0), (90.0, 60.0)


@pytest.fixture(scope="module")
def partit():
    return degrada.aplica(sintetic.partit(n=6000), "barreja")


@pytest.fixture(scope="module")
def taula(partit):
    return contacte.calcula(partit.tracking, partit.trams)


def amb(casa: dict[tuple[int, int], float] | None = None, fora: dict[tuple[int, int], float] | None = None,
        sense_pilota: tuple[int, int] | None = None):
    """La pilota quieta a `PILOTA`, i un jugador de cada equip lluny, que s'hi acosta a les imatges [a, b) a la
    distància que diu el diccionari, en metres."""
    pilota = np.tile(PILOTA, (N, 1)).astype(float)
    if sense_pilota:
        pilota[slice(*sense_pilota)] = np.nan
    jugadors = []
    for lluny, a_prop in ((LLUNY_H, casa or {}), (LLUNY_A, fora or {})):
        j = quiet(*lluny)
        for (a, b), d in a_prop.items():
            j[a:b, 0] = (PILOTA[0] + d, PILOTA[1])
        jugadors.append(j)
    return contacte.calcula(tracking(pilota, *jugadors), una_part())


def test_una_fila_per_imatge_i_cap_columna_sense_convencio(partit, taula):
    assert len(taula) == partit.n and taula.dtypes.eq(np.float32).all()
    assert len(taula.columns) == 9 * len(contacte.RADIS_M)
    simetrics = {f"contacte{r:g}_{nom}" for r in contacte.RADIS_M
                 for nom in ("des", "fins", "durada_abans", "durada_despres")}
    for col in taula.columns:
        assert col.endswith(("_h", "_a")) or col.startswith("dif_") or col in simetrics, col
    altres = set(senyals.calcula(partit.tracking, partit.trams).columns)
    assert not set(taula.columns) & (altres | set(control.calcula(partit.tracking, partit.trams).columns))


def test_intercanviar_els_equips_es_intercanviar_les_columnes(partit, taula):
    t = partit.tracking
    girat = replace(t, casa=t.fora, fora=t.casa)
    pd.testing.assert_frame_equal(contacte.calcula(girat, partit.trams), senyals.intercanvia(taula),
                                  check_exact=False, rtol=1e-5)


@pytest.mark.parametrize("quina", [0, 1])
def test_cap_senyal_no_passa_d_una_part_a_l_altra(partit, taula, quina):
    t = partit.tracking
    _, inici, fi = partit.trams[quina]
    rng = np.random.default_rng(5)
    canvia = {}
    for camp in ("pilota", "casa", "fora"):
        valors = getattr(t, camp).copy()
        valors[inici:fi + 1] = rng.random(valors[inici:fi + 1].shape)
        canvia[camp] = valors
    canviat = contacte.calcula(replace(t, **canvia), partit.trams)
    altra = np.ones(partit.n, bool)
    altra[inici:fi + 1] = False
    pd.testing.assert_frame_equal(canviat[altra], taula[altra])


def test_fora_de_les_parts_les_files_son_buides():
    pilota = np.tile(PILOTA, (N, 1)).astype(float)
    t = tracking(pilota, quiet(PILOTA[0] + 0.5, PILOTA[1]), quiet(*LLUNY_A))
    f = contacte.calcula(t, ((1, 50, 249),))
    assert f.iloc[:50].isna().all().all() and f.iloc[250:].isna().all().all()


def test_el_darrer_contacte_el_proper_i_el_penultim():
    f = amb(casa={(50, 80): 0.5}, fora={(150, 200): 0.6})
    assert np.isnan(f["dif_contacte1_abans"].iloc[20]) and f["dif_contacte1_despres"].iloc[20] == 1
    assert f["dif_contacte1_abans"].iloc[100] == 1 and f["dif_contacte1_despres"].iloc[100] == -1
    assert f["dif_contacte1_abans"].iloc[160] == -1 and np.isnan(f["dif_contacte1_despres"].iloc[160])
    assert np.isnan(f["dif_contacte1_penultim"].iloc[100]) and f["dif_contacte1_penultim"].iloc[160] == 1
    assert f["dif_contacte1_abans"].iloc[60] == 1 and f["dif_contacte1_despres"].iloc[60] == -1   # dins del primer


def test_quant_fa_quant_falta_i_quant_duren():
    f = amb(casa={(50, 80): 0.5}, fora={(150, 200): 0.6})
    np.testing.assert_allclose(f["contacte1_des"].iloc[[60, 100, 160, 250]], [0, 21 / 25, 0, 51 / 25], atol=1e-6)
    np.testing.assert_allclose(f["contacte1_fins"].iloc[[20, 60, 100]], [30 / 25, 90 / 25, 50 / 25], atol=1e-6)
    assert f["contacte1_des"].iloc[20] == senyals.TOPALL_S and f["contacte1_fins"].iloc[160] == senyals.TOPALL_S
    np.testing.assert_allclose(f["contacte1_durada_abans"].iloc[[60, 100, 160]], [30 / 25, 30 / 25, 50 / 25],
                               atol=1e-6)
    np.testing.assert_allclose(f["contacte1_durada_despres"].iloc[[20, 100]], [30 / 25, 50 / 25], atol=1e-6)
    assert np.isnan(f["contacte1_durada_abans"].iloc[20]) and np.isnan(f["contacte1_durada_despres"].iloc[160])


def test_la_distancia_de_cada_equip_al_final_del_darrer():
    f = amb(casa={(50, 80): 0.5}, fora={(70, 90): 3.0})
    assert f["contacte1_d_abans_h"].iloc[100] == pytest.approx(0.5, abs=1e-4)
    assert f["contacte1_d_abans_a"].iloc[100] == pytest.approx(3.0, abs=1e-4)      # a prop: disputat
    assert np.isnan(f["contacte1_d_abans_h"].iloc[20])
    lluny = amb(casa={(50, 80): 0.5})
    assert lluny["contacte1_d_abans_a"].iloc[100] == pytest.approx(np.hypot(40, 30), abs=1e-3)


def test_cada_radi_te_els_seus_contactes():
    f = amb(casa={(50, 80): 1.5})
    assert np.isnan(f["dif_contacte1_abans"].iloc[100]) and f["dif_contacte2_abans"].iloc[100] == 1


def test_si_hi_son_tots_dos_compta_el_mes_proper():
    f = amb(casa={(50, 80): 0.8}, fora={(50, 80): 0.4})
    assert f["dif_contacte1_abans"].iloc[100] == -1
    assert np.isnan(f["dif_contacte1_penultim"].iloc[100])


def test_canviar_d_equip_sense_deixar_la_pilota_son_dos_contactes():
    f = amb(casa={(50, 80): 0.5}, fora={(80, 120): 0.5})
    assert f["dif_contacte1_abans"].iloc[100] == -1 and f["dif_contacte1_penultim"].iloc[100] == 1
    assert f["contacte1_durada_abans"].iloc[100] == pytest.approx(40 / 25)


def test_sense_pilota_no_hi_ha_contacte_i_el_darrer_es_porta_endavant():
    f = amb(casa={(50, 150): 0.5}, sense_pilota=(80, 120))
    assert f["dif_contacte1_abans"].iloc[100] == 1 and f["dif_contacte1_despres"].iloc[100] == 1
    assert f["contacte1_des"].iloc[100] == pytest.approx(21 / 25) and f["contacte1_fins"].iloc[100] == pytest.approx(20 / 25)
    assert f["dif_contacte1_penultim"].iloc[130] == 1 and f["contacte1_durada_abans"].iloc[130] == pytest.approx(30 / 25)
