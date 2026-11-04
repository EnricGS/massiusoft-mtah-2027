"""El marge que queda a sobre d'A sense pilota: la meitat dels errors, les inventades i les taules."""

from __future__ import annotations

import numpy as np
import pandas as pd

from banc import canvis_falsos as cf
from banc import marge_sense_pilota as msm
from banc import sostre_sense_pilota as ssp
from possessio.oficial import possession_metrics as pm


def etiqueta(*trossos: tuple[int, int]) -> np.ndarray:
    return np.concatenate([np.full(n, codi, dtype=np.int8) for codi, n in trossos])


def test_la_meitat_dels_errors_gira_trossos_fins_a_la_meitat_i_nomes_on_es_diu():
    toc = np.full(40, pm.H)
    bona, dolenta = (1.0, -1.0, 0.0), (-1.0, 1.0, 0.0)
    r = np.array(([bona] * 2 + [dolenta] * 2) * 10)            # 20 errors, en trossos de 2
    on = np.arange(40) < 32                                     # els 16 de les 32 primeres
    out = msm.meitat_dels_errors(r, toc, on, np.random.default_rng(0))
    assert ssp.encerts(out, toc, on) == (32, 24)               # la meitat dels 16: quatre trossos
    np.testing.assert_array_equal(out[32:], r[32:])
    np.testing.assert_array_equal(out, msm.meitat_dels_errors(r, toc, on, np.random.default_rng(0)))


def test_les_inventades_amb_les_seves_vores():
    toc = etiqueta((pm.H, 100), (pm.D, 30), (pm.H, 70))
    pred = etiqueta((pm.H, 40), (pm.A, 10), (pm.H, 50), (pm.D, 30), (pm.A, 10), (pm.H, 60))
    f = msm.inventades(pred, toc, [(0, 200)])
    assert [(p["a"], p["b"], p["k"], p["vores"]) for p in f] == [(40, 50, pm.A, cf.INSERIDA),
                                                                (130, 140, pm.A, cf.AL_COSTAT)]


def files_de_prova() -> pd.DataFrame:
    files = []
    for k, (nom, font) in enumerate((("p1", "dfl"), ("p2", "dfl"), ("p3", "metrica"))):
        for escenari in msm.ESCENARIS:
            for base, nivell in ((msm.XARXES, 0.60), (msm.A_SENSE, 0.62)):
                for sostre in (msm.BASE, *msm.SOSTRES):
                    guany = 0.05 if sostre == msm.D else 0.0
                    files.append({"partit": nom, "font": font, "escenari": escenari, "base": base, "sostre": sostre,
                                  "spell_f1": nivell + guany + 0.001 * k})
    return pd.DataFrame(files)


def test_la_taula_del_marge():
    linies = msm.taula_marge(files_de_prova())
    assert linies[2].split(" | ")[1] == "0.601 → 0.621"
    d = next(linia for linia in linies if linia.startswith(f"| {msm.D} |"))
    assert d.split(" | ")[1] == "+0.050 → +0.050"


def test_la_taula_del_criteri_es_contra_a_xarxes():
    linies = msm.taula_criteri(files_de_prova())
    res_mes = next(linia for linia in linies if linia.startswith("| res més |"))
    assert res_mes.split(" | ")[1].startswith("+0.020 · 3/3")
    d = next(linia for linia in linies if linia.startswith(f"| {msm.D} |"))
    assert d.split(" | ")[1].startswith("+0.070 · 3/3")


def test_la_taula_dels_errors():
    errors = pd.DataFrame([{"partit": "p", "escenari": "net", "base": base, "on": on, "n": 100, "encerts": e}
                           for base in msm.BASES for on, e in ((msm.AMB_PILOTA, 90), (msm.ALS_FORATS, 70))])
    t = msm.taula_errors(errors)
    assert t.loc["net", (msm.AMB_PILOTA, msm.A_SENSE)] == 0.1
    assert t.loc["net", (msm.PART_ALS_FORATS, msm.XARXES)] == 0.75
