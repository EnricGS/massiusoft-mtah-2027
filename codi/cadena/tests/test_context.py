"""Els senyals del context: simètrics entre equips, sense passar d'una part a l'altra i NaN fora de les parts."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cadena import context, senyals
from cadena.model import GIRA

N = 1000
TRAMS = ((1, 0, 499), (2, 500, N - 1))


@pytest.fixture(scope="module")
def proba():
    p = np.random.default_rng(4).dirichlet([1, 1, 1], N)
    p[100:140] = [0.9, 0.05, 0.05]
    return p


def test_una_fila_per_imatge_i_cap_columna_sense_convencio(proba):
    taula = context.calcula(proba, TRAMS)
    assert len(taula) == N and taula.dtypes.eq(np.float32).all()
    for col in taula.columns:
        base = col.partition("@")[0]
        assert base.endswith(("_h", "_a")) or base.startswith("dif_") or base == "morta", col


def test_girar_els_equips_es_intercanviar_les_columnes(proba):
    taula = context.calcula(proba, TRAMS)
    pd.testing.assert_frame_equal(context.calcula(proba[:, GIRA], TRAMS), senyals.intercanvia(taula))


def test_cap_finestra_no_passa_d_una_part_a_l_altra(proba):
    taula = context.calcula(proba, TRAMS)
    altres = proba.copy()
    altres[500:] = np.random.default_rng(9).dirichlet([1, 1, 1], N - 500)
    pd.testing.assert_frame_equal(context.calcula(altres, TRAMS).iloc[:500], taula.iloc[:500])


def test_fora_de_les_parts_les_files_son_buides_i_els_valors_son_els_seus(proba):
    taula = context.calcula(proba, ((1, 50, 449),))
    assert taula.iloc[:50].isna().all().all() and taula.iloc[450:].isna().all().all()
    np.testing.assert_allclose(taula["dif_p"].iloc[120], 0.85, atol=1e-6)
    np.testing.assert_allclose(taula["dif_p@+12"].iloc[110], 0.85, atol=1e-6)
    assert np.isnan(taula["dif_p@-5"].iloc[52]) and np.isnan(taula["dif_p@+5"].iloc[447])
    np.testing.assert_allclose(taula["p_h@max25"].iloc[95], 0.9, atol=1e-6)
    np.testing.assert_allclose(taula["morta@p12"].iloc[139], 0.05, atol=1e-6)


def test_les_probabilitats_han_de_ser_tres_columnes():
    with pytest.raises(ValueError):
        context.calcula(np.ones((10, 2)) / 2, ((1, 0, 9),))
