"""El banc de la T3ad: cap xarxa no aprèn amb els partits que ha de provar, les mostres són les de la T3v amb la meitat
girades (amb una llavor per partit i escenari), i les possessions de la veritat aparellades per durada."""

from __future__ import annotations

import numpy as np
import pytest

from banc import degrada, fonts
from banc import model_a_context as t3e
from banc import model_a_equips as mae
from banc import model_camp_girat as mcg
from banc.tests import sintetic
from possessio.oficial import possession_metrics as pm

H, A, D, X = pm.H, pm.A, pm.D, pm.X


class Prou(Exception):
    pass


def test_cap_xarxa_no_apren_amb_els_partits_que_ha_de_provar(monkeypatch, tmp_path):
    vist = []

    def entrena(noms):
        vist.append(list(noms))
        raise Prou

    monkeypatch.setattr(mcg, "entrena_xarxes", entrena)
    monkeypatch.setattr(mcg, "DIR_CAU", tmp_path)
    prova = fonts.NOMS[0]
    for i in range(t3e.GRUPS):
        with pytest.raises(Prou):
            mcg.xarxes_del_grup((prova, i))
        assert len(vist[-1]) == 6 and not set(vist[-1]) & {prova, *t3e.grups(prova)[i]}
    with pytest.raises(Prou):
        mcg.xarxes_de_la_prova(prova)
    assert len(vist[-1]) == 9 and prova not in vist[-1]


def partits_fets() -> dict[tuple[str, str], object]:
    return {(nom, e): degrada.aplica(sintetic.partit(n=1500, llavor=k), mae.t3.ESCENARIS[e])
            for k, (nom, e) in enumerate((nom, e) for nom in ("u", "dos") for e in mcg.SIS)}


def test_les_mostres_son_les_de_la_t3v_la_meitat_girades(monkeypatch):
    partits = partits_fets()
    monkeypatch.setattr(mcg.mp, "degradat", lambda nom, e: partits[(nom, e)])
    vist = []
    monkeypatch.setattr(mcg.xarxes, "entrena", lambda x, y: vist.append((x.copy(), y.copy())))
    mae.entrena_xarxes(["u", "dos"])
    mcg.entrena_xarxes(["u", "dos"])
    mcg.entrena_xarxes(["u", "dos"])
    (x_t3v, y_t3v), (x, y), (x_altre, y_altre) = vist
    np.testing.assert_array_equal(y, y_t3v)
    assert x.shape == x_t3v.shape
    assert 0.4 < (x != x_t3v).any(axis=1).mean() < 0.6
    np.testing.assert_array_equal(x_altre, x)                     # la llavor de cada partit i escenari, la mateixa
    np.testing.assert_array_equal(y_altre, y)


def _per_durada(toc: np.ndarray, pred: np.ndarray, trams: list[tuple[int, int]]) -> dict[str, tuple[int, int]]:
    return {f["durada"]: (f["n"], f["aparellades"]) for f in mcg.per_durada(toc, pred, trams)}


def test_les_possessions_aparellades_per_durada():
    toc = np.array([H] * 12 + [A] * 37 + [H] * 75 + [A] * 175 + [H] * 300 + [D] * 20, dtype=np.int8)
    trams = [(0, len(toc))]
    totes = _per_durada(toc, toc, trams)
    assert list(totes) == [nom for _, _, nom in mcg.DURADES]
    assert all(v == (1, 1) for v in totes.values())
    pred = toc.copy()
    pred[:12] = A                         # la curta, de l'altre equip: la del costat encara s'hi aparella
    pred[200:210] = X                     # una abstenció, omplerta com a l'spellF1
    files = _per_durada(toc, pred, trams)
    assert files["de menys d'1 s"] == (1, 0) and files["d'1 a 2 s"] == (1, 1)
    assert sum(n for n, _ in files.values()) == 5 and sum(a for _, a in files.values()) == 4
