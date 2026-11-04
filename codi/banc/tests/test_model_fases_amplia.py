"""El banc d'A fases àmplia (T3al): la graella nova, la tria sense mirar el partit que es prova, les comprovacions
contra el banc de la T3ak, la D impossible i que dues vegades dona exactament el mateix."""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
import pytest

from banc import fonts
from banc import model_etiquetes_decodificador as med
from banc import model_fases as mfs
from banc import model_fases_amplia as mfa
from banc import model_neteja_aire as mna
from cadena import decodifica_tocs as dt
from cadena.fases import Fase
from possessio.oficial import possession_metrics as pm

H, A = pm.H, pm.A
TRAMS = ((1, 0, 999),)
Suma = mfs.Suma


def test_la_graella_del_pla():
    assert {s.gamma for s in mfa.GRAELLA} == {0.0, 0.5, 1.0, 2.0, 4.0, 8.0}
    assert {s.delta for s in mfa.GRAELLA} == {0.0, 1.0, 2.0, 4.0, 8.0}
    assert {s.marge_s for s in mfa.GRAELLA} == {0.0, 0.5, 1.0}
    assert len(mfa.GRAELLA) == 90 and len({mfs.efectiva(s) for s in mfa.GRAELLA}) == 88
    assert Suma(1.0, 1.0, 0.0) in mfa.GRAELLA                     # la cantonada que va triar la T3ak
    assert len(set(mfa.GRAELLA) & set(mfs.GRAELLA)) == 12


def files_graella(punts: tuple[Suma, ...], millor_de: dict[str, Suma], spell=None) -> pd.DataFrame:
    return pd.DataFrame([{"partit": nom, "escenari": e, "nivell": nivell, **s._asdict(), "macro_f1": 0.5,
                          "spell_f1": spell(nom, e, nivell, s) if spell else
                          (0.9 if s == millor_de.get(nom, punts[0]) else 0.5)}
                         for nom, e, nivell, s in itertools.product(fonts.NOMS, med.QUARTS_T3, med.NIVELLS_TRIA,
                                                                    punts)])


def test_la_tria_d_un_partit_no_mira_les_seves_files():
    a, b = Suma(8.0, 4.0, 0.5), Suma(2.0, 8.0, 0.0)
    prova = fonts.NOMS[0]
    assert mfs.tria(files_graella((a, b), {prova: b}), prova) == a
    t = files_graella((a, b), {nom: b for nom in fonts.NOMS[:5]})
    assert mfs.tria(t, fonts.NOMS[0]) == a and mfs.tria(t, fonts.NOMS[9]) == b


def spell(nom: str, e: str, nivell: str, s: Suma) -> float:
    return 0.5 + 0.01 * fonts.NOMS.index(nom) + 0.001 * s.gamma + 0.0001 * s.delta + 0.00001 * s.marge_s


def test_la_graella_ha_de_donar_el_de_la_t3ak_als_punts_comuns():
    aqui, t3ak = files_graella(mfa.GRAELLA, {}, spell), files_graella(mfs.GRAELLA, {}, spell)
    mfa.comprova_la_graella(aqui, t3ak)                          # els altres punts no hi compten
    t3ak.loc[(t3ak["gamma"] == 0.5) & (t3ak["delta"] == 1.0) & (t3ak["marge_s"] == 1.0), "spell_f1"] += 1e-12
    with pytest.raises(RuntimeError):
        mfa.comprova_la_graella(aqui, t3ak)
    with pytest.raises(RuntimeError):                            # hi falta un punt comú
        mfa.comprova_la_graella(aqui[~((aqui["gamma"] == 1.0) & (aqui["delta"] == 0.0))],
                                files_graella(mfs.GRAELLA, {}, spell))


def files_informe(metode: str, desfas: float = 0.0, partits=fonts.NOMS) -> pd.DataFrame:
    return pd.DataFrame([{"partit": nom, "escenari": e, "nivell": n, "veritat": v, "metode": metode,
                          "spell_f1": 0.5 + 0.01 * i + (desfas if nom == fonts.NOMS[2] else 0.0)}
                         for i, (nom, e, n, v) in enumerate(itertools.product(partits, med.ESCENARIS, med.NIVELLS,
                                                                              (med.SEMPRE, med.TOC)))])


def test_on_es_tria_el_mateix_punt_dona_el_d_a_fases():
    t3ak = {nom: Suma(1.0, 1.0, 0.0) for nom in fonts.NOMS}
    triats = {**t3ak, fonts.NOMS[2]: Suma(8.0, 8.0, 0.0)}
    nous, d_abans = files_informe(mfa.A_FA, desfas=0.1), files_informe(mfs.A_FS)
    mfa.comprova_les_mateixes(nous, d_abans, triats, t3ak)       # el que tria un altre punt no hi compta
    with pytest.raises(RuntimeError):
        mfa.comprova_les_mateixes(nous, d_abans, t3ak, t3ak)
    with pytest.raises(RuntimeError):                            # hi falta un partit
        mfa.comprova_les_mateixes(files_informe(mfa.A_FA, partits=fonts.NOMS[:9]), d_abans, triats, t3ak)


def test_el_nom_del_metode():
    r = {"files": [{"metode": mfs.A_PM, "n": 1}, {"metode": mfs.A_FS, "n": 2}], "fases": [{"fases": 3}]}
    assert mfa.reanomena(r) == {"files": [{"metode": mfs.A_PM, "n": 1}, {"metode": mfa.A_FA, "n": 2}],
                                "fases": [{"fases": 3}]}
    assert r["files"][1]["metode"] == mfs.A_FS


def test_les_vores():
    assert mfa._vores({nom: Suma(2.0, 4.0, 0.5) for nom in fonts.NOMS}) == [
        "Cap partit no tria a la vora de la graella."]
    assert mfa._vores({fonts.NOMS[0]: Suma(8.0, 2.0, 0.5), fonts.NOMS[1]: Suma(4.0, 8.0, 0.0)}) == [
        "**A la vora de la graella:** gamma = 8, delta = 8, marge_s = 0."]


def test_la_d_continua_impossible_amb_els_valors_grans():
    rng = np.random.default_rng(0)
    netejades = np.zeros(1000, dtype=bool)
    netejades[300:400] = True
    relativa = mna.amb_la_d_impossible(rng.normal(size=(1000, 3)), netejades)
    for s in mfa.GRAELLA:
        x = mfs.relativa_amb(relativa, (Fase(200, 599, H), Fase(650, 900, A)), TRAMS, s, netejades)
        assert (x[netejades, dt.D] == -mna.IMPOSSIBLE).all()


def test_dues_vegades_exactament_el_mateix():
    rng = np.random.default_rng(3)
    netejades = rng.random(1000) < 0.05
    relativa = mna.amb_la_d_impossible(rng.normal(size=(1000, 3)), netejades)
    fases = (Fase(100, 499, H), Fase(600, 899, A))
    for s in mfa.GRAELLA:
        np.testing.assert_array_equal(mfs.relativa_amb(relativa, fases, TRAMS, s, netejades),
                                      mfs.relativa_amb(relativa, fases, TRAMS, s, netejades))
    t = files_graella((Suma(8.0, 4.0, 0.5), Suma(2.0, 8.0, 0.0)), {fonts.NOMS[3]: Suma(2.0, 8.0, 0.0)})
    assert all(mfs.tria(t, nom) == mfs.tria(t.sample(frac=1, random_state=5), nom) for nom in fonts.NOMS)
