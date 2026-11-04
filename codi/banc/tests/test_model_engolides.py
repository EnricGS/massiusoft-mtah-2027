"""El banc del detector d'engolides (T3aj): les mostres, la tria sense mirar el partit que es prova, les llavors, la D
impossible i que dues vegades dona exactament el mateix."""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from banc import fonts
from banc import model_engolides as meg
from banc import model_etiquetes_decodificador as med
from banc import model_neteja_aire as mna
from banc import smart_tagging_simulat as sts
from cadena import decodifica_tocs as dt
from cadena import engolides as eg
from possessio.oficial import possession_metrics as pm

H, A, D = pm.H, pm.A, pm.D


def test_les_mostres_nomes_de_dins_de_les_possessions_predites():
    n = 400
    toc = np.repeat(np.array([H, A, H, D], dtype=np.int8), 100)
    equip = np.repeat(np.array([H, -1, A, H], dtype=np.int8), 100)
    x = pd.DataFrame({"imatge": np.arange(n, dtype=float), "altra": np.arange(n, dtype=float) * 2})
    xs, y = meg.mostres_del_partit(toc, [(0, 350)], x, equip)
    i = xs["imatge"].to_numpy().astype(int)
    np.testing.assert_array_equal(i, np.flatnonzero((equip >= 0) & (np.arange(n) < 350))[::meg.PAS])
    np.testing.assert_array_equal(xs["altra"], 2 * xs["imatge"])
    np.testing.assert_array_equal(y, (toc[i] == 1 - equip[i]).astype(np.int8))
    assert y[(i >= 200) & (i < 300)].all() and not y[i < 100].any() and not y[i >= 300].any()


def test_les_mostres_d_un_partit_no_en_venen_mai():
    for prova in fonts.NOMS:
        altres = meg.altres(prova)
        assert prova not in altres and len(altres) == len(fonts.NOMS) - 1


def files(millor_de: dict[str, float]) -> pd.DataFrame:
    return pd.DataFrame([{"partit": nom, "escenari": e, "nivell": nivell, "beta": beta, "macro_f1": 0.5,
                          "spell_f1": 0.9 if beta == millor_de.get(nom, 0.5) else 0.5}
                         for nom, e, nivell, beta in itertools.product(fonts.NOMS, med.QUARTS_T3, med.NIVELLS_TRIA,
                                                                       (0.5, 2.0))])


def test_la_tria_d_un_partit_no_mira_les_seves_files():
    prova = fonts.NOMS[0]
    assert meg.tria(files({prova: 2.0}), prova) == 0.5
    t = files({nom: 2.0 for nom in fonts.NOMS[:5]})          # cinc i cinc: amb el partit que es prova, empatarien
    assert meg.tria(t, fonts.NOMS[0]) == 0.5 and meg.tria(t, fonts.NOMS[9]) == 2.0
    assert meg.tria(t, prova) in meg.BETES


def test_les_etiquetes_son_les_de_la_t3ag():
    assert (meg.TRIA, meg.PROVA, meg.NIVELLS_TRIA) == (med.TRIA, med.PROVA, med.NIVELLS_TRIA)
    nom, e = fonts.NOMS[0], med.QUARTS_T3[0]
    assert sts.llavor(nom, e, "mitjà", meg.TRIA) != sts.llavor(nom, e, "mitjà", meg.PROVA)


def test_la_d_continua_impossible_a_les_imatges_netejades():
    rng = np.random.default_rng(0)
    netejades = np.zeros(1000, dtype=bool)
    netejades[300:400] = True
    relativa = mna.amb_la_d_impossible(rng.normal(size=(1000, 3)), netejades)
    equip = np.repeat(np.array([H, A, -1, H, A], dtype=np.int8), 200)
    x = meg.relativa_amb(relativa, rng.random(1000), equip, 2.0, netejades)
    assert (x[netejades, dt.D] == -mna.IMPOSSIBLE).all()
    np.testing.assert_array_equal(x[:, D], relativa[:, D])
    np.testing.assert_array_equal(x[equip < 0], relativa[equip < 0])


def test_amb_beta_zero_es_a_pilota_morta():
    rng = np.random.default_rng(1)
    netejades = rng.random(1000) < 0.1
    relativa = mna.amb_la_d_impossible(rng.normal(size=(1000, 3)), netejades)
    equip = np.repeat(np.array([H, A, -1, H, A], dtype=np.int8), 200)
    np.testing.assert_array_equal(meg.relativa_amb(relativa, rng.random(1000), equip, 0.0, netejades), relativa)
    assert meg.BETES[0] == 0.0


def sintetiques(n: int = 6000, llavor: int = 2) -> tuple[pd.DataFrame, np.ndarray]:
    rng = np.random.default_rng(llavor)
    x = pd.DataFrame(rng.normal(size=(n, len(eg.COLUMNES))), columns=list(eg.COLUMNES))
    y = (x["canvi"] + 0.5 * rng.normal(size=n) > 1.0).astype(np.int8).to_numpy()
    return x, y


def test_el_detector_dues_vegades_exactament_el_mateix():
    x, y = sintetiques()
    a, b = meg.entrena_detector(x, y, rondes=20), meg.entrena_detector(x, y, rondes=20)
    assert a.model_to_string() == b.model_to_string()
    pa = meg.prediu(a, x)
    np.testing.assert_array_equal(pa, meg.prediu(b, x))
    assert ((pa > 0) & (pa < 1)).all() and pa[y == 1].mean() > pa[y == 0].mean()
    t = files({fonts.NOMS[3]: 2.0})
    assert all(meg.tria(t, nom) == meg.tria(t.sample(frac=1, random_state=5), nom) for nom in fonts.NOMS)


def test_el_detector_es_binari_amb_els_parametres_del_segon():
    assert meg.PARAMS["objective"] == "binary" and "num_class" not in meg.PARAMS
    assert {k: v for k, v in meg.PARAMS.items() if k != "objective"} == {
        k: v for k, v in meg.model.PARAMS.items() if k not in ("objective", "num_class")}
    assert meg.RONDES == meg.model.RONDES
