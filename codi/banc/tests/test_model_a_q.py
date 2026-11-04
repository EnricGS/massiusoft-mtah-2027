"""T3r al banc: la q aprèn amb la taula del segon i tota la resta és A xarxes, la q no canvia en girar els equips,
dues vegades fa el mateix, la comprovació d'A xarxes, quants canvis troba cada q, el criteri i la regla del millor
fins ara."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from banc import fonts
from banc import model_a_canvis as t3i
from banc import model_a_partit as mp
from banc import model_a_q as mq
from banc import model_a_toc as mt
from banc import model_a_xarxa as t3m
from banc import veritat_toc as vt
from banc.tests import sintetic
from banc.tests.test_model_a_partit import cos
from banc.tests.test_model_a_toc import metodes_de_prova
from cadena import senyals
from possessio.oficial import possession_metrics as pm

N = 6000


def probabilitats(llavor: int) -> np.ndarray:
    return np.random.default_rng(llavor).dirichlet(np.ones(3), N).astype(np.float32)


@pytest.fixture
def peces(monkeypatch):
    """A xarxes amb un partit sintètic: dos partits del primer grup per entrenar, i el que es prova."""
    net = sintetic.partit(n=N)
    primer, de_les_xarxes = probabilitats(1), probabilitats(2)

    def del_grup(probes: np.ndarray):
        def fes(tasca: tuple[str, int, tuple[str, ...]]) -> dict[tuple[str, str], np.ndarray]:
            _, i, entrenament = tasca
            return {(f"p{k}", e): probes for k, e in enumerate(entrenament[:2])} if i == 0 else {}
        return fes

    monkeypatch.setattr(mp, "degradat", lambda nom, e: net)
    monkeypatch.setattr(mp, "primer_del_grup", del_grup(primer))
    monkeypatch.setattr(mp, "xarxes_del_grup", del_grup(de_les_xarxes))
    monkeypatch.setattr(mp, "primer_de_la_prova", lambda tasca: {e: primer for e in mq.ESCENARIS})
    monkeypatch.setattr(mp, "xarxes_de_la_prova", lambda tasca: {e: de_les_xarxes for e in mq.ESCENARIS})
    monkeypatch.setattr(mq, "ESCENARIS", ("net", "barreja ×¼"))
    return net, primer, de_les_xarxes


def test_la_q_apren_amb_les_mostres_d_a_xarxes_i_la_taula_del_segon(peces):
    x, y = mq.mostres_q("prova")
    x_abans, y_abans = mp.mostres_q("prova", mq.SIS)
    x_segon, _ = mp.mostres_segon("prova", mq.SIS)
    assert np.array_equal(y, y_abans)
    pd.testing.assert_frame_equal(x[x_abans.columns], x_abans)
    assert list(x.columns) == list(x_segon.columns)
    assert len(x.columns) > len(x_abans.columns)


def test_el_codi_de_les_mostres_es_el_del_segon_amb_la_tria_de_la_q():
    """L'única diferència amb les mostres del segon d'A xarxes: les imatges i l'objectiu de la q (`t3i.mostres`)."""
    assert cos(mq.mostres_q) == cos(mp.mostres_segon, {
        "primer_del_grup((prova, i, entrenament))": "mp.primer_del_grup((prova, i, SIS))",
        "xarxes_del_grup((prova, i, entrenament))": "mp.xarxes_del_grup((prova, i, SIS))",
        "p = degradat(nom, e)": "p = mp.degradat(nom, e)",
        "t3f.mostres(": "t3i.mostres(",
    })


def test_el_banc_puntua_com_el_de_la_t3q():
    """La graella i les dues veritats, com a la T3q: només hi canvia de qui són les probabilitats i la q."""
    assert cos(mq.graella) == cos(mt.graella)


def test_girar_els_equips_no_canvia_la_q(peces):
    net, primer, de_les_xarxes = peces
    taula = t3m.taula_segon(net, primer.astype(float), de_les_xarxes.astype(float))
    entrenat = mq.entrena_q(*t3i.mostres(net, taula))
    girada = senyals.intercanvia(taula)
    pd.testing.assert_frame_equal(senyals.intercanvia(girada), taula.astype(np.float32))
    assert np.array_equal(t3i.q_de(entrenat, taula), t3i.q_de(entrenat, girada))


def test_dues_vegades_exactament_el_mateix(peces, monkeypatch, tmp_path):
    monkeypatch.setattr(mq, "DIR_CAU", tmp_path / "u")
    primera = mq.q("prova")
    assert set(primera) == set(mq.ESCENARIS)
    assert all(len(v) == N and np.nanmin(v) >= 0 and np.nanmax(v) <= 1 for v in primera.values())
    assert all(np.array_equal(primera[e], v) for e, v in mq.q("prova", entrena=False).items())
    monkeypatch.setattr(mq, "DIR_CAU", tmp_path / "dos")
    segona = mq.q("prova")
    assert all(np.array_equal(primera[e], segona[e]) for e in mq.ESCENARIS)
    monkeypatch.setattr(mq, "DIR_CAU", tmp_path / "res")
    with pytest.raises(RuntimeError):
        mq.q("prova", entrena=False)


def test_a_xarxes_ha_de_donar_el_del_banc_de_la_t3q(monkeypatch):
    claus = {"partit": "dfl-x", "escenari": "net", "w": 4.0, "lam": 32.0, "d_min": 12}
    del_banc = pd.DataFrame([{**claus, "metode": m, "veritat": v, "spell_f1": f}
                             for m, v, f in ((mq.XARXES, mq.TOC, 0.71), (mq.XARXES, mq.SEMPRE, 0.72),
                                             (mt.A_TOC, mq.TOC, 0.5))])
    monkeypatch.setattr(mq, "files_t3q", lambda: del_banc)
    aqui = del_banc[del_banc["metode"] == mq.XARXES].assign(font="dfl")
    mq.comprova_a_xarxes(aqui)
    with pytest.raises(RuntimeError):
        mq.comprova_a_xarxes(aqui.assign(spell_f1=[0.71, 0.70]))
    with pytest.raises(RuntimeError):
        mq.comprova_a_xarxes(aqui.assign(w=8.0))


def test_quants_canvis_troba_cada_q(monkeypatch):
    """Tres canvis: a 1000 i a 4000 amb la pilota, i a 2000 en un forat. La q d'A xarxes només troba el de 1000; la
    d'A q, també el del forat."""
    net = sintetic.partit(n=N)
    pilota = net.tracking.pilota.copy()
    pilota[1990:2011] = np.nan
    p = replace(net, tracking=replace(net.tracking, pilota=pilota))
    toc = np.concatenate([np.full(n, k, dtype=np.int8) for k, n in
                          ((pm.H, 1000), (pm.A, 1000), (pm.H, 1000), (pm.A, 1000), (pm.H, 2000))])
    q_xarxes, q_nova = np.zeros(N, dtype=np.float32), np.zeros(N, dtype=np.float32)
    q_xarxes[995:1006] = q_nova[995:1006] = q_nova[1998:2003] = 0.5
    monkeypatch.setattr(mp, "degradat", lambda nom, e: p)
    monkeypatch.setattr(vt, "veritat", lambda nom: toc)
    monkeypatch.setattr(mp, "q", lambda tasca, entrena=True: {"net": q_xarxes})
    monkeypatch.setattr(mq, "q", lambda nom, entrena=True: {"net": q_nova})
    files = pd.DataFrame(mq.troba(("x", "net"))).set_index(["metode", "on"])
    assert files.loc[(mq.XARXES, "amb pilota"), ["canvis", "trobats"]].tolist() == [2, 1]
    assert files.loc[(mq.XARXES, "als forats"), ["canvis", "trobats"]].tolist() == [1, 0]
    assert files.loc[(mq.A_Q, "amb pilota"), ["canvis", "trobats"]].tolist() == [2, 1]
    assert files.loc[(mq.A_Q, "als forats"), ["canvis", "trobats"]].tolist() == [1, 1]


@pytest.mark.parametrize(("dif", "passa"), [
    ({e: 0.05 for e in mq.QUARTS}, {"quarts": True, "altres": True}),
    ({e: 0.03 for e in mq.QUARTS}, {"quarts": False, "altres": True}),
    ({**{e: 0.05 for e in mq.QUARTS}, mp.PARTIT: -0.05}, {"quarts": True, "altres": False}),
])
def test_el_criteri_del_pla(dif, passa):
    metodes = metodes_de_prova(dif, mq.A_Q, mq.XARXES_TOC, mq.TOC)
    assert mt.compleix(mt.comparacio(metodes, mq.A_Q, mq.XARXES_TOC, mq.TOC, amb_criteri=True)) == passa


@pytest.mark.parametrize(("dif", "millor"), [
    ({e: 0.02 for e in mq.QUARTS}, {"quarts": True, "partit": True, "altres": True}),
    ({**{e: 0.02 for e in mq.QUARTS}, "curts ×¼": 0.0}, {"quarts": False, "partit": True, "altres": True}),
    ({**{e: 0.02 for e in mq.QUARTS}, mp.PARTIT: -0.005}, {"quarts": True, "partit": False, "altres": True}),
    ({**{e: 0.02 for e in mq.QUARTS}, "net": -0.03}, {"quarts": True, "partit": True, "altres": True}),
    ({**{e: 0.02 for e in mq.QUARTS}, "net": -0.05}, {"quarts": True, "partit": True, "altres": False}),
])
def test_la_regla_del_millor_fins_ara(dif, millor):
    metodes = metodes_de_prova(dif, mq.A_Q, mq.XARXES_TOC, mq.TOC)
    c = mt.comparacio(metodes, mq.A_Q, mq.XARXES_TOC, mq.TOC, amb_criteri=True)
    assert mq.millor_fins_ara(c) == millor


def test_la_regla_demana_l_interval_per_sobre_de_zero():
    """Als ×¼, guanyar de mitjana no n'hi ha prou: si el guany va d'un partit a l'altre, l'interval toca el zero."""
    metodes = metodes_de_prova({}, mq.A_Q, mq.XARXES_TOC, mq.TOC)
    nou = (metodes["metode"] == mq.A_Q) & metodes["escenari"].isin(mq.QUARTS)
    partits = {nom: k for k, nom in enumerate(fonts.NOMS)}
    salt = metodes.loc[nou, "partit"].map(lambda nom: 0.06 if partits[nom] % 2 else -0.05)
    metodes.loc[nou, "spell_f1"] += salt
    c = mt.comparacio(metodes, mq.A_Q, mq.XARXES_TOC, mq.TOC, amb_criteri=True)
    assert (c[c["escenari"].isin(mq.QUARTS)]["diferencia"] > 0).all()
    assert not mq.millor_fins_ara(c)["quarts"]
