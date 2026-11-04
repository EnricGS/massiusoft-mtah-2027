"""El banc d'A girat amb defenses (T3an): les fases de defensar es giren i s'afegeixen a les d'atac, una de cada banda
del mateix equip compta com una, girant els equips dona el mateix girat, els casos del pla, les comprovacions d'en
començar, la segona part del criteri i que dues vegades dona exactament el mateix."""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
import pytest

from banc import fases_defensar as fd
from banc import fonts
from banc import model_fases as mfs
from banc import model_girat_defenses as mgd
from banc import model_girat_fases as mgf
from cadena import fases as fs
from cadena.fases import Fase
from possessio.oficial import possession_metrics as pm

H, A, D = pm.H, pm.A, pm.D
TRAMS = ((1, 0, 999),)
GIRA = [A, H, D]


def test_els_casos_del_pla():
    assert mgd.CRITERI == mgd.Cas("mitjà", "mitjà", 0.5)
    assert mgd.SEGONA == mgd.Cas("mitjà", "dolent", 0.0)
    assert set(mgd.CASOS) == {mgd.Cas(n, n, x) for n in mgd.NIVELLS for x in fd.LLIGADES} | {mgd.SEGONA}
    assert len(mgd.CASOS) == len(set(mgd.CASOS)) and mgd.A_GFS == mgf.A_GFS


def test_les_de_defensar_es_giren_i_s_afegeixen():
    atac, defensar = (Fase(100, 300, H),), (Fase(200, 400, A), Fase(600, 700, H))
    assert mgd.amb_les_de_defensar(atac, defensar) == (Fase(100, 300, H), Fase(200, 400, H), Fase(600, 700, A))
    assert mgd.amb_les_de_defensar(atac, ()) == atac
    assert mgd.amb_les_de_defensar((), ()) == ()


def test_una_de_defensar_i_una_d_atac_del_mateix_equip_compten_com_una():
    r = np.random.default_rng(0).normal(size=(1000, 3))
    amb = mgd.amb_les_de_defensar((Fase(100, 300, H),), (Fase(200, 400, A),))
    for gamma, delta in ((1.0, 1.0), (0.25, 0.0)):
        np.testing.assert_array_equal(fs.resta(r, amb, TRAMS, gamma, delta, 0.0),
                                      fs.resta(r, (Fase(100, 400, H),), TRAMS, gamma, delta, 0.0))
        np.testing.assert_array_equal(fs.resta(r, mgd.amb_les_de_defensar((Fase(100, 300, H),), (Fase(100, 300, H),)),
                                               TRAMS, gamma, delta, 0.0), r)    # diuen equips diferents: res


def test_girant_els_equips_dona_el_mateix_girat():
    rng = np.random.default_rng(1)
    r, netejades = rng.normal(size=(1000, 3)), rng.random(1000) < 0.1
    atac = (Fase(50, 300, H), Fase(320, 500, A), Fase(800, 990, H))
    defensar = (Fase(100, 200, A), Fase(450, 700, H), Fase(900, 999, A))
    girades = lambda fases: tuple(Fase(f.inici, f.final, 1 - f.equip) for f in fases)  # noqa: E731
    for s in (mfs.Suma(1.0, 1.0, 0.0), mfs.Suma(0.05, 0.25, 2.0)):
        x = mfs.relativa_amb(r, mgd.amb_les_de_defensar(atac, defensar), TRAMS, s, netejades)
        y = mfs.relativa_amb(r[:, GIRA], mgd.amb_les_de_defensar(girades(atac), girades(defensar)), TRAMS, s, netejades)
        np.testing.assert_array_equal(y, x[:, GIRA])


def preds_iguals(pred: np.ndarray) -> tuple[dict, dict]:
    return {n: pred.copy() for n in mgd.NIVELLS}, {c: pred.copy() for c in mgd.CASOS}


def test_amb_lligades_1_i_sense_fases_ha_de_ser_a_girat_amb_fases():
    pred = np.random.default_rng(2).integers(0, 3, 200).astype(np.int8)
    sense, amb = preds_iguals(pred)
    mgd.comprova_les_lligades(sense, amb, "x", "curts ×¼")
    for cas in [mgd.Cas(n, n, 1.0) for n in mgd.NIVELLS] + [mgd.Cas("cap", "cap", x) for x in fd.LLIGADES]:
        with pytest.raises(RuntimeError):
            mgd.comprova_les_lligades(sense, amb | {cas: np.roll(pred, 1)}, "x", "curts ×¼")
    mgd.comprova_les_lligades(sense, amb | {mgd.CRITERI: np.roll(pred, 1), mgd.SEGONA: np.roll(pred, 2)}, "x", "e")


def files_t3am() -> tuple[pd.DataFrame, pd.DataFrame]:
    files = [{"partit": nom, "font": "dfl", "escenari": e, "metode": m, "nivell": n, "veritat": v,
              "spell_f1": 0.5 + 0.001 * i, "macro_f1": 0.4, "possessions": 10 + i, "possessions_reals": 12}
             for i, (nom, e, m, n, v) in enumerate(itertools.product(
                 fonts.NOMS, ("net", "curts ×¼"), (mgf.A_GIRAT, mgf.A_GPM, mgf.A_GFS), mgd.NIVELLS,
                 (mgd.SEMPRE, mgd.TOC)))]
    t3am = pd.DataFrame(files)
    return t3am, t3am[t3am["metode"] == mgf.A_GFS].sample(frac=1, random_state=3).reset_index(drop=True)


def test_a_girat_amb_fases_refet_ha_de_donar_el_de_la_t3am():
    t3am, refet = files_t3am()
    mgd.comprova_la_t3am(refet, t3am)
    tocat = refet.copy()
    tocat.loc[0, "spell_f1"] += 1e-6
    with pytest.raises(RuntimeError):
        mgd.comprova_la_t3am(tocat, t3am)
    tocat = refet.copy()
    tocat.loc[0, "possessions"] += 1
    with pytest.raises(RuntimeError):
        mgd.comprova_la_t3am(tocat, t3am)
    with pytest.raises(RuntimeError):                            # hi falta una fila
        mgd.comprova_la_t3am(refet.iloc[1:], t3am)


def files_casos(diferencia: dict[mgd.Cas, dict[str, float]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """A girat amb fases a 0,5 a tot arreu; A girat amb defenses, amb la diferència de `diferencia` (0 si no hi és)."""
    gfs, gdf = [], []
    for nom, e, v in itertools.product(fonts.NOMS, mgd.ESCENARIS, (mgd.SEMPRE, mgd.TOC)):
        comu = {"partit": nom, "font": "dfl" if nom.startswith("dfl") else "metrica", "escenari": e, "veritat": v}
        gfs += [{**comu, "metode": mgd.A_GFS, "nivell": n, "spell_f1": 0.5} for n in mgd.NIVELLS]
        gdf += [{**comu, "metode": mgd.A_GDF, **c._asdict(), "spell_f1": 0.5 + diferencia.get(c, {}).get(e, 0.0)}
                for c in mgd.CASOS]
    return pd.DataFrame(gfs), pd.DataFrame(gdf)


def test_de_cas_agafa_el_nivell_i_les_lligades():
    gfs, gdf = files_casos({mgd.CRITERI: {"net": 0.1}, mgd.SEGONA: {"net": 0.2}})
    for cas, esperat in ((mgd.CRITERI, 0.6), (mgd.SEGONA, 0.7), (mgd.Cas("bo", "bo", 0.5), 0.5)):
        t = mgd.de_cas(gfs, gdf, cas)
        assert set(t["metode"]) == {mgd.A_GFS, mgd.A_GDF} and "nivell" not in t and "lligades" not in t
        assert len(t) == 2 * len(fonts.NOMS) * len(mgd.ESCENARIS) * 2
        nou = t[(t["metode"] == mgd.A_GDF) & (t["escenari"] == "net")]["spell_f1"]
        assert np.allclose(nou, esperat)


def test_la_segona_part_del_criteri():
    def aguanta(dif: dict[str, float]) -> bool:
        gfs, gdf = files_casos({mgd.SEGONA: dif})
        return mgd.comparacions(gfs, gdf)["aguanta"]

    assert aguanta({})
    assert aguanta({e: -0.005 for e in mgd.QUARTS})
    assert not aguanta({mgd.QUARTS_T3[0]: -0.0051})
    assert not aguanta({mgd.PARTIT: -0.006})
    assert aguanta({"net": -0.03})                               # fora dels ×¼, no hi compta


def test_el_criteri_i_el_millor_fins_ara_miren_el_cas_del_pla():
    gfs, gdf = files_casos({mgd.CRITERI: {e: 0.05 for e in mgd.QUARTS_T3},
                            mgd.Cas("bo", "bo", 0.5): {e: -0.3 for e in mgd.ESCENARIS}})
    r = mgd.comparacions(gfs, gdf)
    assert r["c"]["diferencia"][r["c"]["escenari"].isin(mgd.QUARTS_T3)].round(6).eq(0.05).all()
    assert r["aguanta"] and set(r["casos"]) == set(mgd.CASOS) - {mgd.CRITERI, mgd.SEGONA} - {
        mgd.Cas("cap", "cap", x) for x in fd.LLIGADES}
    gfs, gdf = files_casos({mgd.CRITERI: {e: -0.01 for e in mgd.QUARTS_T3}})
    r = mgd.comparacions(gfs, gdf)
    assert not r["passa"]["quarts"]
    assert not r["millor"]["quarts"]


def test_dues_vegades_exactament_el_mateix():
    gfs, gdf = files_casos({mgd.CRITERI: {e: 0.01 * i for i, e in enumerate(mgd.ESCENARIS)},
                            mgd.SEGONA: {mgd.PARTIT: -0.002}})
    a = mgd.comparacions(gfs, gdf)
    b = mgd.comparacions(gfs.sample(frac=1, random_state=5), gdf.sample(frac=1, random_state=6))
    pd.testing.assert_frame_equal(a["c"], b["c"])
    assert a["passa"] == b["passa"] and a["aguanta"] == b["aguanta"] and a["millor"] == b["millor"]
    t3am, refet = files_t3am()
    mgd.comprova_la_t3am(refet.sample(frac=1, random_state=7), t3am.sample(frac=1, random_state=8))


def test_la_cobertura_de_les_fases():
    trams = ((1, 0, 499), (2, 600, 999))                         # 900 imatges de dins de les parts
    atac = (Fase(0, 89, H),)
    totes = mgd.amb_les_de_defensar(atac, (Fase(50, 139, A), Fase(600, 689, A)))
    c = mgd.cobertura(atac, totes, 1000, trams, 0.0)
    assert c == {"part_atac": pytest.approx(90 / 900), "part_alguna": pytest.approx(230 / 900),
                 "resta_atac": pytest.approx(90 / 900), "resta_amb": pytest.approx(230 / 900)}
    c = mgd.cobertura(atac, mgd.amb_les_de_defensar(atac, (Fase(0, 89, H),)), 1000, trams, 0.0)
    assert c["part_alguna"] == pytest.approx(90 / 900) and c["resta_amb"] == 0.0
