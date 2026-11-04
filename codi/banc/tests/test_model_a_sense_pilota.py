"""El banc d'A sense pilota: quant dura cada forat, on es mira l'encert, els canvis falsos i les taules."""

from __future__ import annotations

import numpy as np
import pandas as pd

from banc import model_a_sense_pilota as msp
from possessio.oficial import possession_metrics as pm


def etiqueta(*trossos: tuple[int, int]) -> np.ndarray:
    return np.concatenate([np.full(n, codi, dtype=np.int8) for codi, n in trossos])


def test_quant_dura_cada_forat_tambe_a_les_imatges_del_costat():
    vista = np.ones(40, dtype=bool)
    vista[10:13] = False                            # un tros de 3
    vista[20:30] = False                            # un de 10, que toca l'anterior per les vores
    durada = msp.durada_dels_forats(vista, np.ones(40, dtype=bool), k=4)
    assert durada[:6].tolist() == [0] * 6
    assert durada[6:10].tolist() == [3] * 4 and durada[10:13].tolist() == [3] * 3
    assert durada[16:34].tolist() == [10] * 18       # on es toquen, el més llarg
    assert durada[34:].tolist() == [0] * 6


def test_les_mascares_es_parteixen_els_forats_per_durada():
    vista = np.ones(400, dtype=bool)
    vista[50:60] = False                            # menys de 2 s
    vista[150:250] = False                          # de 2 a 5 s
    valides = np.ones(400, dtype=bool)
    valides[390:] = False
    m = msp.mascares(vista, valides)
    assert set(m) == set(msp.ON)
    forats = [m[nom] for _, _, nom in msp.FORATS]
    np.testing.assert_array_equal(sum(f.astype(int) for f in forats), m[msp.ALS_FORATS].astype(int))
    assert not (m[msp.AMB_PILOTA] & m[msp.ALS_FORATS]).any()
    np.testing.assert_array_equal(m[msp.AMB_PILOTA] | m[msp.ALS_FORATS], valides)
    assert forats[0][50:60].all() and forats[1][150:250].all() and not forats[2].any()


def test_els_canvis_falsos_i_els_dels_forats():
    toc = etiqueta((pm.H, 100), (pm.A, 100))
    pred = etiqueta((pm.H, 50), (pm.A, 10), (pm.H, 55), (pm.A, 85))   # anada i tornada a 50 i 60, i el bo a 115
    al_forat = np.zeros(200, dtype=bool)
    al_forat[45:55] = True
    f = msp.falsos(pred, toc, [(0, 200)], al_forat)
    assert f == {"canvis": 3, "falsos": 2, "falsos als forats": 1}        # el de 115, a 15 imatges del real: bo
    assert msp.falsos(etiqueta((pm.H, 200)), toc, [(0, 200)], al_forat) == {"canvis": 0, "falsos": 0,
                                                                          "falsos als forats": 0}


def test_la_taula_dels_encerts():
    files = []
    for on, n, e in ((msp.AMB_PILOTA, 100, 90), (msp.ALS_FORATS, 50, 40)):
        for qui in msp.QUI:
            files.append({"partit": "p", "escenari": "net", "on": on, "qui": qui, "n": n, "encerts": e})
    t = msp.taula_encerts(pd.DataFrame(files))
    assert list(t.index) == [("net", msp.AMB_PILOTA), ("net", msp.ALS_FORATS)]
    assert list(t.columns) == ["n imatges", *msp.QUI]
    assert t.loc[("net", msp.ALS_FORATS), msp.SEGON_NOU] == 0.8 and t.loc[("net", msp.AMB_PILOTA), "n imatges"] == 100


def test_la_taula_dels_canvis():
    files = [{"partit": "p", "escenari": "net", "metode": m, "canvis": 10, "falsos": 4, "falsos als forats": 1}
             for m in (msp.XARXES_TOC, msp.A_SENSE)]
    t = msp.taula_canvis(pd.DataFrame(files))
    assert t.loc["net", ("falsos", msp.A_SENSE)] == 0.4
    assert t.loc["net", ("dels falsos, als forats", msp.XARXES_TOC)] == 0.25
