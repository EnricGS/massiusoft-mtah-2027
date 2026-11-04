"""El banc de la T3y: la taula del segon és la de la T3v amb les columnes noves, que girar els equips no canvia; les
mostres del segon no tenen el partit que es prova; i on encerta l'equip."""

from __future__ import annotations

import numpy as np
import pandas as pd

from banc import degrada, fonts
from banc import model_a_partit as mp
from banc import model_a_xarxa as t3m
from banc import model_forats_al_segon as mfs
from banc.tests import sintetic
from cadena import forats_curts as fc
from cadena import senyals


def test_la_taula_del_segon_es_la_de_la_t3v_i_les_columnes_noves():
    p = degrada.aplica(sintetic.partit(n=3000, llavor=2), mfs.t3.ESCENARIS[mfs.CURTS])
    rng = np.random.default_rng(0)
    primer, xarxes = rng.dirichlet(np.ones(3), len(p.veritat)), rng.dirichlet(np.ones(3), len(p.veritat))
    pilota = p.tracking.pilota.copy()
    nova, vella = mfs.taula_segon(p, primer, xarxes), t3m.taula_segon(p, primer, xarxes)
    assert list(nova.columns) == [*vella.columns, *fc.COLUMNES]
    assert nova[list(vella.columns)].equals(vella)
    assert nova[list(fc.COLUMNES)].equals(fc.columnes_del_segon(p.tracking, p.trams))
    assert nova["forat_on"].notna().sum() > 0                               # n'hi ha
    girada = senyals.intercanvia(nova)
    assert girada[list(fc.COLUMNES)].equals(nova[list(fc.COLUMNES)].astype(np.float32))
    np.testing.assert_array_equal(p.tracking.pilota, pilota)               # el que rep, igual


def test_les_mostres_del_segon_no_tenen_el_partit_que_es_prova(monkeypatch):
    prova, vist = fonts.NOMS[0], []

    def del_grup(tasca, entrena=False):
        return {k: np.zeros((5, 3)) for k in mp.claus_del_grup(tasca[0], tasca[1], mfs.SIS)}

    monkeypatch.setattr(mfs.mp, "primer_del_grup", del_grup)
    monkeypatch.setattr(mfs.mae, "xarxes_del_grup", del_grup)
    monkeypatch.setattr(mfs.mp, "degradat", lambda nom, e: (nom, e))
    monkeypatch.setattr(mfs, "taula_segon", lambda p, primer, xarxes: vist.append(p) or pd.DataFrame({"x": [1.0]}))
    monkeypatch.setattr(mfs.t3f, "mostres", lambda p, taula: (taula, np.zeros(1, np.int8)))
    x, y = mfs.mostres_segon(prova)
    assert sorted(vist) == sorted((nom, e) for nom in fonts.NOMS if nom != prova for e in mfs.SIS)
    assert len(x) == len(y) == 9 * len(mfs.SIS)


def test_la_taula_dels_encerts():
    files = pd.DataFrame([{"escenari": e, "on": on, "qui": qui, "n": 100, "encerts": enc}
                          for e in (mfs.CURTS, "aire ×¼") for on in (mfs.ALS_CURTS, mfs.AMB_PILOTA)
                          for qui, enc in zip(mfs.QUI, (60, 70))])
    t = mfs.taula_encerts(files)
    assert list(t.index) == [(mfs.CURTS, mfs.AMB_PILOTA), (mfs.CURTS, mfs.ALS_CURTS), ("aire ×¼", mfs.AMB_PILOTA),
                             ("aire ×¼", mfs.ALS_CURTS)]
    assert t.loc[(mfs.CURTS, mfs.ALS_CURTS)].tolist() == [100, 0.6, 0.7]
