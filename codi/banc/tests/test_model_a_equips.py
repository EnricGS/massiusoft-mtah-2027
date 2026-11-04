"""El banc d'A equips sencers: les mostres de les xarxes, a una sola matriu, són les de `xarxa_equips.mostres` en
ordre; els forats, segons si la possessió es veu algun cop amb pilota; i la taula."""

from __future__ import annotations

import numpy as np
import pandas as pd

from banc import degrada
from banc import model_a_equips as mae
from banc.tests import sintetic
from cadena import xarxa_equips as xeq
from possessio.oficial import possession_metrics as pm

H, A, D = pm.H, pm.A, pm.D


def test_les_mostres_de_les_xarxes_van_a_una_sola_matriu_en_ordre(monkeypatch):
    partits = {(nom, e): degrada.aplica(sintetic.partit(n=1500, llavor=k), mae.t3.ESCENARIS[e])
               for k, (nom, e) in enumerate((nom, e) for nom in ("u", "dos") for e in mae.SIS)}
    monkeypatch.setattr(mae.mp, "degradat", lambda nom, e: partits[(nom, e)])
    vist = {}
    monkeypatch.setattr(mae.xarxes, "entrena", lambda x, y: vist.update(x=x, y=y))
    mae.entrena_xarxes(["u", "dos"])
    xs, ys = [], []
    for p in partits.values():
        files = mae.t3f.tria(p.veritat, mae.avalua.trams_valids(p))
        x, y = xeq.mostres(p.tracking, p.trams, files, p.veritat[files])
        xs.append(x)
        ys.append(y)
    np.testing.assert_array_equal(vist["x"], np.concatenate(xs))
    np.testing.assert_array_equal(vist["y"], np.concatenate(ys))
    assert vist["x"].dtype == np.float32 and vist["x"].shape[1] == xeq.ENTRADES


def test_als_forats_segons_si_la_possessio_es_veu_algun_cop():
    toc = np.array([H] * 10 + [A] * 10 + [D] * 5 + [H] * 15, dtype=np.int8)
    vista = np.ones(40, dtype=bool)
    vista[3:22] = False                                  # l'A, sencera dins del forat; l'H del principi, no
    valides = np.ones(40, dtype=bool)
    m = mae.mascares(vista, valides, toc, [(0, 40)])
    al_forat = m[mae.ALS_FORATS]
    assert al_forat[10:20].all() and m[mae.MAI][10:20].all() and not m[mae.ALGUN_COP][10:20].any()
    assert m[mae.ALGUN_COP][3:10].all() and not m[mae.MAI][:10].any()
    assert not (m[mae.MAI] & m[mae.ALGUN_COP]).any()
    np.testing.assert_array_equal(m[mae.MAI] | m[mae.ALGUN_COP], al_forat & (toc != D))
    assert set(m) == set(mae.ON)


def test_la_taula_dels_encerts():
    files = pd.DataFrame([{"escenari": e, "on": on, "qui": qui, "n": 100, "encerts": enc}
                          for e in ("curts ×¼", "net") for on in (mae.MAI, mae.AMB_PILOTA)
                          for qui, enc in zip(mae.QUI, (60, 70, 80, 90))])
    t = mae.taula_encerts(files)
    assert list(t.index) == [("net", mae.AMB_PILOTA), ("net", mae.MAI), ("curts ×¼", mae.AMB_PILOTA),
                             ("curts ×¼", mae.MAI)]
    assert t.loc[("net", mae.MAI)].tolist() == [100, 0.6, 0.7, 0.8, 0.9]
