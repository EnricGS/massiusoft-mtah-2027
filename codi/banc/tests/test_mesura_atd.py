"""Els candidats de l'eina que mesura l'ATD: que facin la pilota que falta que diuen, i que la tria torni el bo."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from banc import degrada
from banc import mesura_atd as m
from banc.tests import sintetic
from possessio.oficial import possession_metrics as pm


@pytest.fixture(scope="module")
def net():
    return sintetic.partit(n=20_000)


def parts(p, q):
    falta, graduats = np.isnan(q.tracking.pilota[:, 0]), degrada.puntuats(p)
    morta = graduats & (p.veritat == pm.D)
    return falta[graduats].mean(), falta[morta].mean(), falta[graduats & ~morta].mean()


@pytest.mark.parametrize(("morta", "viva"), [(0.41, 0.41), (0.97, 0.03), (0.6, 0.2), (0.97, 0.41)])
def test_a_la_morta_i_a_la_viva_hi_falta_el_que_diu_el_candidat(net, morta, viva):
    """La viva, exacta; la morta, com a mínim la que diu: un forat en joc pot seguir quan la pilota ja és morta, com
    a `degrada`, i al partit sintètic, amb estones mortes de 20 s, n'hi pot afegir fins a un 20 %."""
    _, a_la_morta, a_la_viva = parts(net, m.aplica(net, m.CandidatPilota("barreja", morta, viva, 3.0, 3.0)))
    assert a_la_viva == pytest.approx(viva, abs=0.005)
    assert morta - 0.01 <= a_la_morta <= morta + 0.2


def test_els_forats_de_la_pilota_morta_no_surten_de_l_estona(net):
    p = net
    q = m.aplica(p, m.CandidatPilota("llargs", 0.97, 0.03, 0.0, 0.0))
    falta, morta = np.isnan(q.tracking.pilota[:, 0]), p.veritat == pm.D
    finals = np.flatnonzero(morta[:-1] & ~morta[1:])                    # l'última imatge de cada estona morta
    assert falta[finals].mean() > 0.9                                   # la morta, gairebé tota sense pilota
    assert falta[finals + 1].mean() < 0.5                               # i en joc, de seguida hi torna a ser


def test_es_determinista_i_no_toca_el_partit(net):
    c = m.CandidatPilota("curts", 0.6, 0.1, 9.0, 0.0)
    a, b = m.aplica(net, c), m.aplica(net, c)
    assert np.array_equal(a.tracking.pilota, b.tracking.pilota, equal_nan=True)
    assert not np.isnan(net.tracking.pilota).any()


def test_la_validacio_torna_el_candidat_mes_proper_amb_el_partit_apartat():
    rng = np.random.default_rng(0)
    files = [{"partit": f"dfl-{i}", "font": "dfl", "perdua": c, "peces_fins_2s": base + rng.normal(0, 0.01),
              "peces_2_10s": 0.0, "peces_10_60s": 0.0, "peces_mes_60s": 1 - base}
             for i in range(5) for c, base in (("a", 0.1), ("b", 0.5))]
    v = m.valida(pd.DataFrame(files), m.PASSOS_JUGADORS)
    assert len(v) == 10 and m.encert(v, "perdua") == 1.0


def test_l_encert_es_compta_segons_la_pilota_morta_i_viva_triades():
    v = pd.DataFrame({"morta": [0.41, 0.41, 0.97, 0.97], "triat_morta": [0.41, 0.41, 0.97, 0.97],
                      "viva": [0.41, 0.41, 0.03, 0.03], "triat_viva": [0.41, 0.41, 0.03, 0.03],
                      "aire": [0.0, 9.0, 0.0, 9.0], "triat_aire": [0.0, 9.0, 9.0, 0.0],
                      "forats": ["curts"] * 4, "triat_forats": ["curts"] * 4,
                      "aglomeracio": [0.0] * 4, "triat_aglomeracio": [0.0] * 4})
    e = m.encerts_per_condicio(v)
    assert e["aire"]["0.41|0.41"] == 1.0 and e["aire"]["0.97|0.03"] == 0.0 and e["aire"]["0.6|0.1"] == 0.0
    assert e["forats"]["0.97|0.03"] == 1.0


def test_els_passos_comencen_per_la_pilota_morta_i_acaben_on_comencen_els_forats():
    assert [c for c, _ in m.PASSOS_PILOTA] == [("morta",), ("viva",), ("forats",), ("aire",), ("aglomeracio",)]
    assert {x for _, cols in m.PASSOS_PILOTA for x in cols} == set(m.est.PILOTA)
