"""El banc d'A girat amb fases (T3am): les graelles, la base de sota, la tria sense mirar el partit que es prova, la
comprovació contra el banc de la T3ad, la de sense etiquetes ni fases, la D impossible i que dues vegades dona
exactament el mateix."""

from __future__ import annotations

import itertools
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from banc import fonts
from banc import model_etiquetes_decodificador as med
from banc import model_fases as mfs
from banc import model_girat_fases as mgf
from banc import model_neteja_aire as mna
from banc import model_pilota_morta as mpm
from cadena import decodifica_tocs as dt
from cadena import pilota_morta as pmo
from cadena import smart_tagging as st
from cadena.fases import Fase
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

H, A = pm.H, pm.A
TRAMS = ((1, 0, 999),)
FIXA = next(a for a in pmo.GRAELLA if a.forma == pmo.FIXA)
PER_TIPUS = next(a for a in pmo.GRAELLA if a.forma == pmo.PER_TIPUS)


def test_les_graelles_de_la_t3ah_i_de_la_t3ak():
    assert mgf.GRAELLA_PM == pmo.GRAELLA and len(mgf.GRAELLA_PM) == 96
    assert mgf.GRAELLA_FS == mfs.GRAELLA and len(mgf.GRAELLA_FS) == 54
    assert mgf.ZERO == mfs.Suma(0.0, 0.0, 0.0)


def test_la_base_de_sota(monkeypatch):
    rng = np.random.default_rng(0)
    de_sempre, netejades = SimpleNamespace(tracking="el tracking"), rng.random(50) < 0.2
    probes, prior = {"curts ×¼": rng.dirichlet((1, 1, 1), 50).astype(np.float32)}, np.array([0.45, 0.45, 0.1])
    q_ = {"curts ×¼": rng.random(50)}
    monkeypatch.setattr(mgf.mp, "degradat", lambda nom, e: de_sempre)
    monkeypatch.setattr(mgf.pc, "lluny", lambda tracking: netejades if tracking == "el tracking" else None)
    monkeypatch.setattr(mgf.mcg, "de_qui", lambda metode, nom: (probes, prior, q_) if metode == mgf.A_GIRAT else None)
    monkeypatch.setattr(mgf.med, "base", lambda nom, e: ("d'A neteja d'aire", nom, e))
    b = mgf.base(mgf.A_GIRAT, "x", "curts ×¼")
    assert b[0] is de_sempre and b[2] is q_["curts ×¼"] and b[3] is netejades
    np.testing.assert_array_equal(b[1], log_relativa(probes["curts ×¼"].astype(float), prior))
    assert mgf.base(mgf.A_NETEJA, "x", "curts ×¼") == ("d'A neteja d'aire", "x", "curts ×¼")
    with pytest.raises(ValueError):
        mgf.base(med.XARXES, "x", "curts ×¼")


def files_pm(prova: str) -> pd.DataFrame:
    """El partit que es prova, i les medianes fetes amb la seva veritat, afavoreixen PER_TIPUS; la resta, FIXA."""
    files = []
    for nom, e, nivell in itertools.product(fonts.NOMS, med.QUARTS_T3, med.NIVELLS_TRIA):
        comu = {"partit": nom, "escenari": e, "nivell": nivell, "macro_f1": 0.5}
        files.append({**comu, "sense": "", **FIXA._asdict(), "spell_f1": 0.6 if nom != prova else 0.1})
        files += [{**comu, "sense": altre, **PER_TIPUS._asdict(),
                   "spell_f1": 0.9 if nom == prova or altre != prova else 0.5} for altre in fonts.NOMS if altre != nom]
    return pd.DataFrame(files)


def files_fs(millor_de: dict[str, mfs.Suma]) -> pd.DataFrame:
    punts = (mfs.Suma(0.1, 0.25, 1.0), mfs.Suma(0.5, 0.0, 2.0))
    return pd.DataFrame([{"partit": nom, "escenari": e, "nivell": nivell, **s._asdict(), "macro_f1": 0.5,
                          "spell_f1": 0.9 if s == millor_de.get(nom, punts[0]) else 0.5}
                         for nom, e, nivell, s in itertools.product(fonts.NOMS, med.QUARTS_T3, med.NIVELLS_TRIA,
                                                                    punts)])


def test_la_tria_d_un_partit_no_mira_les_seves_files():
    prova = fonts.NOMS[4]
    assert mpm.tria(files_pm(prova), prova) == FIXA
    assert mpm.tria(files_pm(prova), fonts.NOMS[0]) == PER_TIPUS
    a, b = mfs.Suma(0.1, 0.25, 1.0), mfs.Suma(0.5, 0.0, 2.0)
    assert mfs.tria(files_fs({prova: b}), prova) == a


def files_t3ad(triades: dict[str, tuple]) -> tuple[pd.DataFrame, pd.DataFrame]:
    punts = ((4.0, 32.0, 12), (4.0, 32.0, 25), (4.0, 16.0, 12))
    t3ad = pd.DataFrame([{"partit": nom, "escenari": e, "veritat": v, "w": w, "lam": lam, "d_min": d,
                          "spell_f1": 0.5 + 0.01 * i}
                         for i, (nom, e, v, (w, lam, d)) in enumerate(itertools.product(
                             fonts.NOMS, med.ESCENARIS, (med.SEMPRE, med.TOC), punts))])
    tria = [(w, lam, d) == tuple(triades[nom])
            for nom, w, lam, d in t3ad[["partit", "w", "lam", "d_min"]].itertuples(index=False)]
    return t3ad, t3ad[tria][["partit", "escenari", "veritat", "spell_f1"]].sample(frac=1, random_state=2)


def test_a_camp_girat_ha_de_donar_el_de_la_t3ad():
    triades = {nom: (4.0, 32.0, 12) for nom in fonts.NOMS} | {fonts.NOMS[3]: (4.0, 32.0, 25)}
    t3ad, aqui = files_t3ad(triades)
    mgf.comprova_la_t3ad(aqui, t3ad, triades)
    with pytest.raises(RuntimeError):                            # un altre decodificador
        mgf.comprova_la_t3ad(aqui, t3ad, triades | {fonts.NOMS[3]: (4.0, 16.0, 12)})
    tocat = aqui.copy()
    tocat.iloc[0, tocat.columns.get_loc("spell_f1")] += 1e-6
    with pytest.raises(RuntimeError):
        mgf.comprova_la_t3ad(tocat, t3ad, triades)
    with pytest.raises(RuntimeError):                            # hi falta una fila
        mgf.comprova_la_t3ad(aqui.iloc[1:], t3ad, triades)


def test_sense_etiquetes_ni_fases():
    rng = np.random.default_rng(1)
    pred = rng.integers(0, 3, 200).astype(np.int8)
    preds = {(m, n): pred.copy() for m in (mgf.A_GIRAT, mgf.A_GPM, mgf.A_GFS) for n in med.NIVELLS}
    mgf.comprova_sense_res(preds, "x", "curts ×¼")
    for metode in (mgf.A_GPM, mgf.A_GFS):
        tocades = dict(preds)
        tocades[(metode, "cap")] = np.roll(pred, 1)
        with pytest.raises(RuntimeError):
            mgf.comprova_sense_res(tocades, "x", "curts ×¼")
    mgf.comprova_sense_res(preds | {(mgf.A_GFS, "mitjà"): np.roll(pred, 1)}, "x", "curts ×¼")


def test_la_d_continua_impossible_a_les_dues_capes():
    rng = np.random.default_rng(2)
    netejades = np.zeros(1000, dtype=bool)
    netejades[300:400] = True
    r = rng.normal(size=(1000, 3))
    etiquetes = (st.Etiqueta(250, 260, st.TIPUS[0], H), st.Etiqueta(700, 705, st.TIPUS[-1], None))
    medianes = {tipus: 3.0 for tipus in st.TIPUS}
    for a in pmo.GRAELLA:
        capa = mpm.relativa_amb(r, etiquetes, TRAMS, a, medianes, netejades)
        for s in (mfs.Suma(1.0, 1.0, 0.0), mfs.Suma(0.05, 0.25, 2.0)):
            x = mfs.relativa_amb(capa, (Fase(200, 599, H), Fase(650, 900, A)), TRAMS, s, netejades)
            assert (x[netejades, dt.D] == -mna.IMPOSSIBLE).all()


def test_dues_vegades_exactament_el_mateix():
    for prova in fonts.NOMS:
        t = files_pm(prova)
        assert mpm.tria(t, prova) == mpm.tria(t.sample(frac=1, random_state=5), prova)
    t = files_fs({fonts.NOMS[3]: mfs.Suma(0.5, 0.0, 2.0)})
    assert all(mfs.tria(t, nom) == mfs.tria(t.sample(frac=1, random_state=5), nom) for nom in fonts.NOMS)
    triades = {nom: (4.0, 32.0, 12) for nom in fonts.NOMS}
    t3ad, aqui = files_t3ad(triades)
    mgf.comprova_la_t3ad(aqui.sample(frac=1, random_state=7), t3ad.sample(frac=1, random_state=8), triades)
