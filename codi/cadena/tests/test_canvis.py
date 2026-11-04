"""El context de la q per al segon classificador de canvis: una fila per imatge, simètric entre equips, sense passar
d'una part a l'altra, i la q desplaçada, en finestres, els màxims i els pics."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cadena import canvis, senyals

N = 400
TRAMS = ((1, 0, 199), (2, 200, 399))


@pytest.fixture(scope="module")
def q():
    return np.random.default_rng(4).beta(0.5, 5, N)


@pytest.fixture(scope="module")
def taula(q):
    return canvis.calcula(q, TRAMS)


def test_una_fila_per_imatge_simetrica_entre_equips(taula):
    assert len(taula) == N and taula.dtypes.eq(np.float32).all()
    for col in taula.columns:
        assert col.startswith("canvi_") and not col.partition("@")[0].endswith(("_h", "_a")), col
    pd.testing.assert_frame_equal(senyals.intercanvia(taula), taula)


def test_fora_de_les_parts_les_files_son_buides(q):
    t = canvis.calcula(q, ((1, 50, 249),))
    assert t.iloc[:50].isna().all().all() and t.iloc[250:].isna().all().all()
    assert t.iloc[50:250].notna().any().all()


def test_cap_finestra_no_passa_d_una_part_a_l_altra(q, taula):
    canviada = q.copy()
    canviada[:200] = 1 - canviada[:200]
    pd.testing.assert_frame_equal(canvis.calcula(canviada, TRAMS).iloc[200:], taula.iloc[200:])


def test_la_q_desplacada_les_finestres_i_els_pics():
    q = np.full(N, 0.02)
    q[100] = 0.9
    t = canvis.calcula(q, ((1, 0, N - 1),))
    assert t["canvi_q@+5"].iloc[95] == pytest.approx(0.9) and t["canvi_q@-5"].iloc[105] == pytest.approx(0.9)
    assert t["canvi_q@max13"].iloc[94] == pytest.approx(0.9) and t["canvi_q@max13"].iloc[93] == pytest.approx(0.02)
    assert t["canvi_q@p12"].iloc[101] > t["canvi_q@f12"].iloc[101]
    assert t["canvi_pic"].iloc[100] == 1 and t["canvi_pic"].iloc[97] == 0 and t["canvi_pic"].iloc[105] == 0


def test_la_q_ha_de_ser_una_serie():
    with pytest.raises(ValueError):
        canvis.calcula(np.zeros((N, 3)), TRAMS)
