"""Els senyals del model d'A: simètrics entre equips, sense passar d'una part a l'altra i amb la pilota que falta."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from banc import degrada
from banc.tests import sintetic
from cadena import senyals


@pytest.fixture(scope="module")
def partit():
    return degrada.aplica(sintetic.partit(n=6000), "barreja")


@pytest.fixture(scope="module")
def taula(partit):
    return senyals.calcula(partit.tracking, partit.trams)


def test_una_fila_per_imatge_i_cap_columna_sense_convencio(partit, taula):
    assert len(taula) == partit.n and taula.dtypes.eq(np.float32).all()
    for col in taula.columns:
        base = col.partition("@")[0]
        assert base.endswith(("_h", "_a")) or base.startswith("dif_") or base in senyals.SIMETRICS, col


def test_intercanviar_els_equips_es_intercanviar_les_columnes(partit, taula):
    t = partit.tracking
    girat = replace(t, casa=t.fora, fora=t.casa)
    esperat = senyals.intercanvia(taula)
    pd.testing.assert_frame_equal(senyals.calcula(girat, partit.trams), esperat, check_exact=False, rtol=1e-5)
    pd.testing.assert_frame_equal(senyals.intercanvia(esperat), taula)


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
    canviat = senyals.calcula(replace(t, **canvia), partit.trams)
    altra = np.ones(partit.n, bool)
    altra[inici:fi + 1] = False
    pd.testing.assert_frame_equal(canviat[altra], taula[altra])


def test_fora_de_les_parts_les_files_son_buides():
    p = sintetic.partit(n=3000)
    trams = ((1, 100, 1199), (2, 1500, 2899))
    s = senyals.calcula(p.tracking, trams)
    dins = np.zeros(p.n, bool)
    for _, inici, fi in trams:
        dins[inici:fi + 1] = True
    assert s[~dins].isna().all().all() and s[dins].notna().any(axis=1).all()


def test_sense_pilota_els_seus_senyals_son_nan_i_la_memoria_hi_es(partit, taula):
    sense = np.isnan(partit.tracking.pilota[:, 0])
    assert sense.any()
    assert taula.loc[sense, "d1_h"].isna().all() and taula.loc[~sense, "d1_h"].notna().all()
    assert (taula.loc[sense, "des_vista"] > 0).all() and (taula.loc[~sense, "des_vista"] == 0).all()
    assert taula.loc[sense, "dif_d1_abans"].notna().mean() > 0.9


def test_la_memoria_hi_es_dins_dels_forats(partit, taula):
    hi_es = ~np.isnan(partit.tracking.pilota[:, 0])
    entremig = np.zeros(partit.n, bool)              # amb pilota abans i després, a la mateixa part
    for _, inici, fi in partit.trams:
        vista = inici + np.flatnonzero(hi_es[inici:fi + 1])
        entremig[vista[0]:vista[-1] + 1] = True
    forat = entremig & ~hi_es
    memoria = [c for c in taula.columns if "_abans" in c or "_despres" in c]
    assert len(memoria) == 2 * (len(senyals.MEMORIA_SIMETRICA) + 2 * len(senyals.MEMORIA_D_EQUIP) + 1)
    for col in memoria:
        assert taula.loc[forat, col].notna().mean() > 0.95, col


def test_la_pilota_a_fora_del_camp():
    p = sintetic.partit(n=2000)
    t = p.tracking
    pilota = t.pilota.copy()
    pilota[:100] = [1.1, 0.5]                      # més enllà de la línia de fons
    s = senyals.calcula(replace(t, pilota=pilota), p.trams)
    assert (s["fora_camp"].iloc[:100] > 5).all() and (s["fora_camp"].iloc[200:] == 0).all()


def test_el_sentit_d_atac_surt_de_la_posicio_dels_equips():
    p = sintetic.partit(n=2000)
    t = p.tracking
    casa = t.casa.copy()
    casa[..., 0] = 0.2                              # H a l'esquerra: ataca cap a la dreta
    fora = t.fora.copy()
    fora[..., 0] = 0.8
    s = senyals.calcula(replace(t, casa=casa, fora=fora), p.trams)
    assert s["cx_h"].iloc[50] == pytest.approx(0.2 * 105, abs=0.5)
    assert s["cx_a"].iloc[50] == pytest.approx(0.2 * 105, abs=0.5)
    assert (s["propi_h"] == 1).all() and (s["propi_a"] == 1).all()


def test_a_la_reixa_del_video():
    p = sintetic.partit(n=200)
    t = replace(p.tracking, fotograma=np.arange(200) + 10)
    r = senyals.a_reixa(t, 300)
    assert r.pilota.shape == (300, 2) and np.isnan(r.pilota[:10]).all() and np.isnan(r.pilota[210:]).all()
    np.testing.assert_array_equal(r.pilota[10:210], t.pilota)
    assert np.array_equal(r.fotograma, np.arange(300))
