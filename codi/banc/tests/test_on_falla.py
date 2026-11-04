"""On falla A pilota morta (abans del pas següent): l'aparellament de les possessions, per què se'n perd cada una, les
que sobren i els sostres."""

from __future__ import annotations

import numpy as np

from banc import on_falla as of
from cadena.llegeix import Tracking
from possessio.oficial import possession_metrics as pm

H, A, D = pm.H, pm.A, pm.D


def tira(*trossos: tuple[int, int]) -> np.ndarray:
    """(codi, llargada), un darrere l'altre."""
    return np.concatenate([np.full(n, k, dtype=np.int8) for k, n in trossos])


def test_l_aparellament_es_el_de_la_metrica():
    rng = np.random.default_rng(0)
    for _ in range(50):
        toc = rng.choice([H, A, D], size=600).repeat(5).astype(np.int8)
        pred = toc.copy()
        canvi = rng.random(len(pred)) < 0.05
        pred[canvi] = rng.choice([H, A, D], size=canvi.sum())
        trams = [(0, len(toc))]
        gt, pr = pm.possession_spells(toc, trams), pm.possession_spells(pred, trams)
        solapa = pm.spell_overlaps(gt, pr)
        de_veritat, predites = of.aparella(solapa, len(gt), len(pr), of.IOU)
        np.testing.assert_array_equal(de_veritat, pm.matched_gt_flags(solapa, len(gt), of.IOU))
        assert predites.sum() == de_veritat.sum()


def test_per_que_se_perd_cada_possessio():
    toc = tira((H, 100), (D, 50), (A, 100), (D, 50), (H, 100), (D, 10), (H, 100), (D, 50), (A, 100), (D, 50), (H, 100))
    pred = tira((H, 100), (D, 50), (H, 100), (D, 50), (H, 210), (D, 50), (D, 100), (D, 50), (H, 20), (D, 30), (H, 20),
                (D, 30))
    files = of.causes(toc, pred, [(0, len(toc))])
    assert [f["causa"] for f in files] == ["encertada", "l'altre equip", of.AJUNTADA_D, of.AJUNTADA_D, "la D",
                                           "trencada"]
    assert [f["equip"] for f in files] == [H, A, H, H, A, H]
    assert files[0]["durada_s"] == 100 / pm.FPS


def test_una_curta_de_l_altre_equip_engolida():
    toc = tira((H, 100), (A, 30), (H, 100), (D, 50), (A, 40), (D, 50))
    pred = tira((H, 230), (D, 50), (H, 40), (D, 50))
    files = of.causes(toc, pred, [(0, len(toc))])
    assert [f["causa"] for f in files] == [of.AJUNTADA_ALTRE, "engolida", of.AJUNTADA_ALTRE, "l'altre equip"]
    assert (files[1]["de"], files[1]["fins"]) == (100, 130)


def test_les_vores():
    toc = tira((D, 100), (H, 100), (D, 100))
    pred = tira((D, 160), (H, 40), (D, 100))           # dins, però massa curta: IoU 0,4
    assert [f["causa"] for f in of.causes(toc, pred, [(0, len(toc))])] == ["les vores"]


def test_les_que_sobren():
    toc = tira((H, 200), (D, 100), (A, 200))
    pred = tira((H, 90), (A, 20), (H, 90), (D, 30), (H, 40), (D, 30), (A, 200))
    files = of.sobrants(toc, pred, [(0, len(toc))])
    assert sorted(f["on"] for f in files) == ["a l'altre equip", "a la D", "un tros", "un tros"]


def test_l_inici_es_veu_si_hi_ha_pilota_a_prop():
    toc = tira((D, 50), (H, 100), (D, 50))
    vista = np.zeros(len(toc), dtype=bool)
    files = of.causes(toc, toc, [(0, len(toc))], vista)
    assert not files[0]["inici_vist"]
    vista[50 + of.K] = True
    assert of.causes(toc, toc, [(0, len(toc))], vista)[0]["inici_vist"]
    vista[:] = False
    vista[50 + of.K + 1] = True
    assert not of.causes(toc, toc, [(0, len(toc))], vista)[0]["inici_vist"]


def test_el_sostre_arregla_la_possessio_sencera():
    toc = tira((H, 100), (D, 10), (H, 100), (D, 50), (A, 100))
    pred = tira((H, 210), (D, 50), (H, 100))
    trams = [(0, len(toc))]
    files = of.causes(toc, pred, trams)
    assert [f["causa"] for f in files] == [of.AJUNTADA_D, of.AJUNTADA_D, "l'altre equip"]
    mascara = of.mascara(len(toc), [f for f in files if f["causa"] == of.AJUNTADA_D])
    arreglada = of.amb_la_veritat(pred, toc, mascara)
    np.testing.assert_array_equal(arreglada[:210], toc[:210])
    np.testing.assert_array_equal(arreglada[210:], pred[210:])
    assert pred[105] == H                                   # no toca l'original


def test_les_durades():
    assert [of.durada(s) for s in (0.5, 2.0, 4.9, 5.0, 12.0)] == ["menys de 2 s", "de 2 a 5 s", "de 2 a 5 s",
                                                                  "de 5 a 10 s", "10 s o més"]


def test_el_toc_a_la_vista():
    n, camp = 100, (105.0, 68.0)
    x = 50.0 - 0.4 * np.abs(np.arange(n) - 50)                 # a 10 m/s, i tomba a la imatge 50
    pilota = np.stack([x, np.full(n, 34.0)], axis=1)
    pilota[80:] = np.nan
    fora = np.tile([[[50.0, 34.0]]], (n, 1, 1))                # un de l'A, on tomba la pilota
    casa = np.tile([[[50.0, 50.0]]], (n, 1, 1))                # un de l'H, lluny
    escala = np.asarray(camp)
    t = Tracking(np.arange(n), pilota / escala, casa / escala, fora / escala, "H", "A", True, camp)
    toca = of.toc_a_la_vista(t)
    np.testing.assert_array_equal(np.flatnonzero(toca[:, A]), np.arange(47, 54))
    assert not toca[:, H].any()


def test_la_veu():
    relativa = np.zeros((10, 3))
    relativa[2:6, A] = 1.0
    assert of.la_veu(relativa, 0, 10, A) == 0.4
    assert of.la_veu(relativa, 0, 10, H) == 0.0
