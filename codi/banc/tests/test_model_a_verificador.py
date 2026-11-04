"""T3s al banc: els trets de cada possessió, girar els equips no canvia res, la regla, el llindar, amb què aprenen el
segon i la q de cada grup, els canvis falsos i dues vegades el mateix."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from banc import canvis_falsos as cf
from banc import model_a_partit as mp
from banc import model_a_verificador as av
from banc.tests import sintetic
from possessio.oficial import possession_metrics as pm

N = 6000


def etiqueta(*trossos: tuple[int, int]) -> np.ndarray:
    return np.concatenate([np.full(n, codi, dtype=np.int8) for codi, n in trossos])


def senyals(n: int, llavor: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Les probabilitats del segon, la relativa, la q i la pilota vista, a l'atzar."""
    rng = np.random.default_rng(llavor)
    probes = rng.dirichlet(np.ones(3), n)
    return probes, np.log(probes) - np.log(1 / 3), rng.uniform(0, 1, n), rng.uniform(0, 1, n) > 0.3


def moltes(llavor: int, n_trossos: int = 600) -> np.ndarray:
    """Una predicció llarga a l'atzar: trossos d'H, A i D, de 5 a 200 imatges."""
    rng = np.random.default_rng(llavor)
    codis, abans = [], None
    for _ in range(n_trossos):
        codi = rng.choice([c for c in (pm.H, pm.A, pm.D) if c != abans])
        codis.append((int(codi), int(rng.integers(5, 200))))
        abans = codi
    return etiqueta(*codis)


def gira(pred: np.ndarray, probes: np.ndarray, relativa: np.ndarray) -> tuple[np.ndarray, ...]:
    girada = pred.copy()
    girada[pred == pm.H], girada[pred == pm.A] = pm.A, pm.H
    return girada, probes[:, [1, 0, 2]], relativa[:, [1, 0, 2]]


def test_els_trets_d_una_possessio_feta_a_ma():
    pred = etiqueta((pm.H, 20), (pm.A, 20), (pm.D, 10), (pm.A, 30), (pm.H, 40))
    probes = np.zeros((len(pred), 3))
    probes[20:40] = [0.1, 0.8, 0.1]
    relativa = np.zeros((len(pred), 3))
    relativa[20:40, pm.A], relativa[20:40, pm.H] = 1.0, -1.0
    q = np.full(len(pred), 0.1)
    q[16], q[45] = 0.7, 0.4
    vista = np.ones(len(pred), dtype=bool)
    vista[20] = False
    t = av.possessions_de(pred, probes, relativa, q, vista, [(0, len(pred))])
    assert t[["a", "b", "k"]].to_numpy().tolist() == [[0, 20, pm.H], [20, 40, pm.A], [50, 80, pm.A], [80, 120, pm.H]]
    fila = t.iloc[1]
    assert fila["vores"] == cf.AL_COSTAT
    assert fila[list(av.TRETS)].to_dict() == pytest.approx({
        "durada": 20, "equip": 0.8, "l'altre": 0.1, "aturada": 0.1, "relativa": 2.0, "q a l'inici": 0.7,
        "q al final": 0.4, "vista": 0.95, "vista a l'inici": 0, "vista al final": 1, "abans": av.ALTRE,
        "després": av.ATURADA, "durada d'abans": 20, "durada de després": 10, "canvis a prop": 2})
    assert t.iloc[0]["abans"] == av.VORA and t.iloc[0]["durada d'abans"] == 0
    assert t.iloc[2]["canvis a prop"] == 2 and t.iloc[3]["després"] == av.VORA


def test_els_trams_tallen_les_possessions():
    pred = etiqueta((pm.H, 30), (pm.A, 30))
    probes, relativa, q, vista = senyals(len(pred), 0)
    t = av.possessions_de(pred, probes, relativa, q, vista, [(0, 20), (20, 60)])
    assert t[["a", "b", "k"]].to_numpy().tolist() == [[0, 20, pm.H], [20, 30, pm.H], [30, 60, pm.A]]
    assert t.iloc[1]["abans"] == av.VORA and t.iloc[0]["després"] == av.VORA


def test_girar_els_equips_no_canvia_els_trets_ni_el_que_diu_el_verificador():
    assert (pm.H, pm.A, pm.D) == (0, 1, 2)
    pred = moltes(1)
    probes, relativa, q, vista = senyals(len(pred), 2)
    trams = [(0, len(pred) // 2), (len(pred) // 2, len(pred))]
    t = av.possessions_de(pred, probes, relativa, q, vista, trams)
    pred_g, probes_g, relativa_g = gira(pred, probes, relativa)
    t_g = av.possessions_de(pred_g, probes_g, relativa_g, q, vista, trams)
    assert len(t) > 300
    pd.testing.assert_frame_equal(t.drop(columns="k"), t_g.drop(columns="k"))
    assert (t["k"] != t_g["k"]).all()
    entrenat = av.entrena(t.assign(inventada=np.random.default_rng(3).uniform(size=len(t)) < 0.2, dins=True))
    assert np.array_equal(av.probabilitat(entrenat, t), av.probabilitat(entrenat, t_g))


def test_l_objectiu_i_si_la_possessio_es_dins_de_la_veritat():
    pred = etiqueta((pm.H, 20), (pm.A, 20), (pm.H, 20))
    toc = etiqueta((pm.H, 50), (pm.X, 5), (pm.H, 5))
    probes, relativa, q, vista = senyals(len(pred), 0)
    t = av.amb_l_objectiu(av.possessions_de(pred, probes, relativa, q, vista, [(0, 60)]), toc)
    assert t["inventada"].tolist() == [False, True, False]
    assert t["dins"].tolist() == [True, True, False]


def test_la_regla_les_mira_totes_alhora_i_no_toca_la_predicció():
    pred = etiqueta((pm.H, 10), (pm.A, 5), (pm.H, 10), (pm.D, 5), (pm.A, 5))
    probes, relativa, q, vista = senyals(len(pred), 0)
    t = av.possessions_de(pred, probes, relativa, q, vista, [(0, len(pred))])
    prob = np.array([0.1, 0.8, 0.55, 0.95])
    assert av.arregla_amb(pred, t, prob, 0.9).tolist() == etiqueta(
        (pm.H, 10), (pm.A, 5), (pm.H, 10), (pm.D, 5), (pm.H, 5)).tolist()
    assert av.arregla_amb(pred, t, prob, 0.5).tolist() == etiqueta(
        (pm.H, 15), (pm.A, 10), (pm.D, 5), (pm.H, 5)).tolist()
    mai = av.arregla_amb(pred, t, prob, av.MAI)
    assert mai.tolist() == pred.tolist() and mai is not pred
    assert pred.tolist() == etiqueta((pm.H, 10), (pm.A, 5), (pm.H, 10), (pm.D, 5), (pm.A, 5)).tolist()


@pytest.mark.parametrize(("mitjanes", "triat"), [
    ({0.5: 0.70, 0.6: 0.72, 0.7: 0.72, 0.8: 0.71, 0.9: 0.71, av.MAI: 0.71}, 0.7),
    ({0.5: 0.70, 0.6: 0.70, 0.7: 0.70, 0.8: 0.70, 0.9: 0.70, av.MAI: 0.70}, av.MAI),
    ({0.5: 0.73, 0.6: 0.72, 0.7: 0.70, 0.8: 0.70, 0.9: 0.70, av.MAI: 0.70}, 0.5),
])
def test_el_llindar_amb_mes_spellf1_i_si_n_hi_ha_dos_el_mes_prudent(mitjanes, triat):
    files = pd.DataFrame([{"partit": p, "escenari": "curts ×¼", "llindar": llindar, "spell_f1": f + d}
                          for llindar, f in mitjanes.items() for p, d in (("a", 0.01), ("b", -0.01))])
    assert av.tria_llindar(files) == triat


def test_els_canvis_falsos():
    toc = etiqueta((pm.H, 100), (pm.A, 100))
    pred = etiqueta((pm.H, 50), (pm.A, 10), (pm.H, 40), (pm.A, 100))    # canvia a 50 i 60 (falsos) i a 100
    assert av.compta_canvis(pred, toc, [(0, 200)]) == {"canvis": 3, "falsos": 2}


@pytest.fixture
def grups(monkeypatch):
    """Tres grups de dos partits sintètics, cadascun amb les seves probabilitats, i qui s'ha fet servir."""
    net = sintetic.partit(n=N)
    vistos: list[str] = []

    def del_grup(llavor: int):
        def fes(tasca: tuple[str, int, tuple[str, ...]]) -> dict[tuple[str, str], np.ndarray]:
            _, i, entrenament = tasca
            rng = np.random.default_rng(llavor + 10 * i)
            return {(f"g{i}p{k}", e): rng.dirichlet(np.ones(3), N).astype(np.float32)
                    for k in range(2) for e in entrenament[:2]}
        return fes

    def degradat(nom: str, e: str):
        vistos.append(nom)
        return net

    monkeypatch.setattr(mp, "degradat", degradat)
    monkeypatch.setattr(mp, "primer_del_grup", del_grup(1))
    monkeypatch.setattr(mp, "xarxes_del_grup", del_grup(2))
    return vistos


def test_el_segon_i_la_q_del_grup_no_aprenen_amb_el_grup(grups):
    av.mostres_segon("prova", 1)
    assert set(grups) == {"g0p0", "g0p1", "g2p0", "g2p1"}
    grups.clear()
    av.mostres_q("prova", 1)
    assert set(grups) == {"g0p0", "g0p1", "g2p0", "g2p1"}


def test_les_mostres_del_grup_son_les_d_a_xarxes_sense_el_grup(grups, monkeypatch):
    x, y = av.mostres_segon("prova", 1)
    x_q, y_q = av.mostres_q("prova", 1)

    def sense_el_grup(fes):
        return lambda tasca: {} if tasca[1] == 1 else fes(tasca)

    monkeypatch.setattr(mp, "primer_del_grup", sense_el_grup(mp.primer_del_grup))
    monkeypatch.setattr(mp, "xarxes_del_grup", sense_el_grup(mp.xarxes_del_grup))
    x_abans, y_abans = mp.mostres_segon("prova", av.SIS)
    x_q_abans, y_q_abans = mp.mostres_q("prova", av.SIS)
    pd.testing.assert_frame_equal(x, x_abans)
    pd.testing.assert_frame_equal(x_q, x_q_abans)
    assert np.array_equal(y, y_abans) and np.array_equal(y_q, y_q_abans)


def test_les_peces_del_grup_son_dels_partits_del_grup_i_dues_vegades_el_mateix(grups, monkeypatch, tmp_path):
    monkeypatch.setattr(av, "DIR_CAU", tmp_path / "u")
    probes, prior, q = av.peces_del_grup(("prova", 1))
    assert set(probes) == set(q) == {("g1p0", "curts"), ("g1p0", "llargs"), ("g1p1", "curts"), ("g1p1", "llargs")}
    assert all(p.shape == (N, 3) for p in probes.values()) and all(len(x) == N for x in q.values())
    assert np.allclose(prior.sum(), 1.0)
    monkeypatch.setattr(av, "DIR_CAU", tmp_path / "v")
    probes_2, prior_2, q_2 = av.peces_del_grup(("prova", 1))
    assert np.array_equal(prior, prior_2)
    assert all(np.array_equal(probes[k], probes_2[k]) and np.array_equal(q[k], q_2[k]) for k in probes)
    llegides = av.peces_del_grup(("prova", 1), entrena=False)
    assert all(np.array_equal(probes[k], llegides[0][k]) for k in probes)
    monkeypatch.setattr(av, "DIR_CAU", tmp_path / "w")
    with pytest.raises(RuntimeError):
        av.peces_del_grup(("prova", 1), entrena=False)


def test_el_verificador_dues_vegades_exactament_el_mateix():
    pred = moltes(4)
    probes, relativa, q, vista = senyals(len(pred), 5)
    t = av.possessions_de(pred, probes, relativa, q, vista, [(0, len(pred))])
    t = t.assign(inventada=np.random.default_rng(6).uniform(size=len(t)) < 0.2, dins=True)
    assert np.array_equal(av.probabilitat(av.entrena(t), t), av.probabilitat(av.entrena(t), t))


def test_el_verificador_apren_nomes_amb_les_que_son_dins_de_la_veritat():
    pred = moltes(7)
    probes, relativa, q, vista = senyals(len(pred), 8)
    t = av.possessions_de(pred, probes, relativa, q, vista, [(0, len(pred))])
    rng = np.random.default_rng(9)
    t = t.assign(inventada=rng.uniform(size=len(t)) < 0.2, dins=rng.uniform(size=len(t)) < 0.7)
    sols = t[t["dins"]].reset_index(drop=True)
    assert np.array_equal(av.probabilitat(av.entrena(t), t), av.probabilitat(av.entrena(sols), t))
