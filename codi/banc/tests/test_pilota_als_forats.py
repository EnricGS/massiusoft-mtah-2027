"""Als forats: el més proper a la pilota, quant duren els forats, la pilota vista més propera, les possessions que no
es veuen mai i les taules."""

from __future__ import annotations

import numpy as np
import pandas as pd

from banc import pilota_als_forats as paf
from possessio.oficial import possession_metrics as pm

NAN = np.nan


def test_l_equip_del_mes_proper_a_la_pilota():
    casa = np.array([[[0.0, 0.0], [NAN, NAN]], [[10.0, 0.0], [20.0, 0.0]]])
    fora = np.array([[[3.0, 0.0], [9.0, 9.0]], [[0.0, 1.0], [NAN, NAN]]])
    pilota = np.array([[1.0, 0.0], [1.0, 1.0]])
    assert paf.equip_mes_proper(casa, fora, pilota).tolist() == [pm.H, pm.A]


def test_quant_duren_els_forats_i_on_es_la_pilota_vista_mes_propera():
    vista = np.array([True, False, False, True, False, False, False])
    assert paf.durada_dels_forats(vista).tolist() == [0, 2, 2, 0, 3, 3, 3]
    assert paf.a_la_vista(vista).tolist() == [0, 1, 1, 0, 1, 2, 3]
    assert np.isinf(paf.a_la_vista(np.zeros(3, dtype=bool))).all()


def test_les_possessions_que_no_es_veuen_mai():
    toc = np.array([pm.H] * 4 + [pm.A] * 3 + [pm.D] * 2 + [pm.H] * 3, dtype=np.int8)
    vista = np.zeros(12, dtype=bool)
    vista[[1, 10]] = True
    es_veu, durada = paf.possessions(toc, [(0, 12)], vista)
    assert es_veu.tolist() == [paf.ALGUN_COP] * 4 + [paf.MAI] * 3 + [""] * 2 + [paf.ALGUN_COP] * 3
    assert durada.tolist() == [4] * 4 + [3] * 3 + [0] * 2 + [3] * 3


def test_a_quin_tros():
    assert paf.a_quin(paf.FORATS, np.array([0, 49, 50, 125, np.inf])).tolist() == ["<2 s", "<2 s", "2-5 s", "≥5 s",
                                                                                  "≥5 s"]


def test_les_taules():
    pilota = pd.DataFrame([{"escenari": "curts ×¼", "forat": f, "n": 10, "error_mig": e, "real": 8, "estimada": 6,
                            "segon": 9} for f, e in (("<2 s", 1.0), ("≥5 s", 10.0))])
    t = paf.taula_pilota(pilota, None).loc["curts ×¼"]
    assert (t["n imatges"], t["el més proper a la real"], t["el segon"]) == (20, 0.8, 0.9)
    t = paf.taula_pilota(pilota, "forat")
    assert list(t.index) == [("curts ×¼", "<2 s"), ("curts ×¼", "≥5 s")]
    assert t.loc[("curts ×¼", "≥5 s"), "error de l'estimada (m)"] == 10.0
    segon = pd.DataFrame([{"escenari": "curts ×¼", "es veu": v, "n": n, "mal": m}
                          for v, n, m in ((paf.ALGUN_COP, 80, 8), (paf.MAI, 20, 8))])
    t = paf.taula_segon(segon, "es veu", (paf.ALGUN_COP, paf.MAI))
    assert t.loc[("curts ×¼", paf.MAI)].tolist() == [0.2, 0.4, 0.5]
