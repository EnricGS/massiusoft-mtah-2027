"""El banc de la T3z: els canvis, les imatges noves, que sense canvis les mostres són les de la T3v, i que cap xarxa no
aprèn amb els partits que ha de provar."""

from __future__ import annotations

import numpy as np
import pytest

from banc import degrada, fonts
from banc import model_a_context as t3e
from banc import model_a_equips as mae
from banc import model_mostres_canvis as mmc
from banc.tests import sintetic
from possessio.oficial import possession_metrics as pm

H, A, D, X = pm.H, pm.A, pm.D, pm.X


def test_els_canvis_d_equip_dins_de_cada_part():
    v = np.array([H, H, A, A, D, D, H, X, X, A, H, H, D, H], dtype=np.int8)
    assert mmc.canvis(v, ((1, 0, len(v) - 1),)).tolist() == [2, 6, 9, 10]          # la D i la X no compten
    assert mmc.canvis(v, ((1, 0, 4), (2, 5, len(v) - 1))).tolist() == [2, 9, 10]   # d'una part a l'altra, no
    assert mmc.canvis(np.full(10, D, np.int8), ((1, 0, 9),)).tolist() == []


def test_les_imatges_noves():
    v = np.full(100, H, np.int8)
    v[30:] = A                                         # un canvi a 30
    v[34:] = H                                         # i un altre a 34, tan a prop que s'encavallen
    v[22] = X
    trams = [(0, 41), (50, 100)]
    nous = mmc.imatges_noves(v, ((1, 0, 99),), trams)
    esperat = sorted(set(range(18, 43, 2)) | set(range(22, 47, 2)))
    esperat = [j for j in esperat if j != 22 and j < 41]                          # la X i fora dels trams, no
    assert nous.tolist() == esperat
    assert len(set(nous)) == len(nous)


def test_a_prop_dels_canvis():
    v = np.array([H] * 20 + [A] * 20, dtype=np.int8)
    m = mmc.a_prop(v, ((1, 0, 39),), 3)
    assert np.flatnonzero(m).tolist() == list(range(17, 24))


def partits_fets() -> dict[tuple[str, str], object]:
    return {(nom, e): degrada.aplica(sintetic.partit(n=1500, llavor=k), mae.t3.ESCENARIS[e])
            for k, (nom, e) in enumerate((nom, e) for nom in ("u", "dos") for e in mmc.SIS)}


def test_hi_continua_la_tria_de_la_t3f_i_sense_canvis_les_mostres_son_les_de_la_t3v(monkeypatch):
    partits = partits_fets()
    for p in partits.values():
        ara = mae.t3f.tria(p.veritat, mae.avalua.trams_valids(p))
        nova = mmc.tria(p)
        assert np.isin(ara, nova).all() and len(nova) > len(ara)
    monkeypatch.setattr(mmc.mp, "degradat", lambda nom, e: partits[(nom, e)])
    vist = []
    monkeypatch.setattr(mmc.xarxes, "entrena", lambda x, y: vist.append((x.copy(), y.copy())))
    mae.entrena_xarxes(["u", "dos"])
    monkeypatch.setattr(mmc, "canvis", lambda veritat, parts: np.zeros(0, int))
    mmc.entrena_xarxes(["u", "dos"])
    (x_t3v, y_t3v), (x, y) = vist
    np.testing.assert_array_equal(x, x_t3v)
    np.testing.assert_array_equal(y, y_t3v)


class Prou(Exception):
    pass


def test_cap_xarxa_no_apren_amb_els_partits_que_ha_de_provar(monkeypatch, tmp_path):
    vist = []

    def entrena(noms):
        vist.append(list(noms))
        raise Prou

    monkeypatch.setattr(mmc, "entrena_xarxes", entrena)
    monkeypatch.setattr(mmc, "DIR_CAU", tmp_path)
    prova = fonts.NOMS[0]
    for i in range(t3e.GRUPS):
        with pytest.raises(Prou):
            mmc.xarxes_del_grup((prova, i))
        assert len(vist[-1]) == 6 and not set(vist[-1]) & {prova, *t3e.grups(prova)[i]}
    with pytest.raises(Prou):
        mmc.xarxes_de_la_prova(prova)
    assert len(vist[-1]) == 9 and prova not in vist[-1]
