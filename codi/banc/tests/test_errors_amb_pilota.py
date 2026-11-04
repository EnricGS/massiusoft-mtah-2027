"""Com són els errors d'equip on es veu la pilota: les possessions, on cauen, el segon, els sostres i les taules."""

from __future__ import annotations

import numpy as np
import pandas as pd

from banc import errors_amb_pilota as eap
from possessio.oficial import possession_metrics as pm


def etiqueta(*trossos: tuple[int, int]) -> np.ndarray:
    return np.concatenate([np.full(n, codi, dtype=np.int8) for codi, n in trossos])


def test_les_possessions_de_la_veritat_i_que_hi_ha_abans():
    toc = etiqueta((pm.H, 10), (pm.D, 10), (pm.A, 20), (pm.H, 10))
    inici, final, abans = eap.possessions(toc, [(0, 50)])
    assert (inici[[0, 15, 20, 45]].tolist(), final[[0, 15, 20, 45]].tolist()) == ([0, -1, 20, 40], [10, -1, 40, 50])
    assert abans[[0, 15, 20, 45]].tolist() == [eap.VORA, "", eap.DESPRES_D, eap.DESPRES_ALTRE]


def test_on_cauen_dins_la_possessio():
    toc = etiqueta((pm.H, 10), (pm.A, 10), (pm.H, 10), (pm.A, 10))
    pred = etiqueta((pm.A, 10), (pm.H, 3), (pm.A, 7), (pm.H, 5), (pm.A, 2), (pm.H, 3), (pm.A, 8), (pm.H, 2))
    esperat = ([eap.TOTA] * 10 + [eap.AL_COMENCAMENT] * 3 + [""] * 12 + [eap.AL_MIG] * 2 + [""] * 11
               + [eap.AL_FINAL] * 2)
    assert eap.llocs(pred, toc, [(0, 40)]).tolist() == esperat


def test_que_en_diu_el_segon():
    toc = np.array([pm.H, pm.H, pm.H, pm.A, pm.D])
    relativa = np.array([[0.0, -1, 0], [0, 1, 0], [0, 3, 0], [2, 0, 0], [0, 0, 5]])
    assert eap.segon(relativa, toc).tolist() == [eap.ENCERTA, eap.DUBTA, eap.SEGUR, eap.DUBTA, ""]


def test_els_errors_amb_els_seus_trets_i_nomes_on_es_diu():
    toc = etiqueta((pm.D, 10), (pm.H, 40), (pm.A, 10))
    pred = etiqueta((pm.D, 12), (pm.H, 45), (pm.A, 3))
    on = np.ones(60, dtype=bool)
    on[50:55] = False
    e = eap.errors(pred, toc, np.zeros((60, 3)), on, [(0, 60)])
    d = (eap.LA_D, eap.DURADES[2], eap.DESPRES_D, eap.AL_COMENCAMENT, eap.DISTANCIES[0], eap.ENCERTA)
    altre = (eap.L_ALTRE, eap.DURADES[0], eap.DESPRES_ALTRE, eap.AL_COMENCAMENT, eap.DISTANCIES[0], eap.DUBTA)
    assert list(e[list(eap.TRETS)].itertuples(index=False, name=None)) == [d, d, altre, altre]


def test_les_mascares_dels_sostres():
    toc = etiqueta((pm.H, 200), (pm.A, 50))
    m = eap.mascares(toc, np.zeros((250, 3)), np.ones(250, dtype=bool), [(0, 250)])
    assert {s: int(x.sum()) for s, x in m.items()} == {
        eap.EQUIP: 250, eap.CURTES: 50, eap.LLARGUES: 200, eap.A_PROP: 25 + 24 + 25 + 24, eap.LLUNY: 250 - 98,
        eap.SI_DUBTA: 50, eap.SI_SEGUR: 0}


def errors_de_prova() -> tuple[pd.DataFrame, pd.DataFrame]:
    errors = pd.DataFrame([
        {"escenari": "net", "dona": eap.L_ALTRE, "durada": eap.DURADES[0], "segon": eap.DUBTA, "n": 30},
        {"escenari": "net", "dona": eap.L_ALTRE, "durada": eap.DURADES[4], "segon": eap.SEGUR, "n": 10},
        {"escenari": "net", "dona": eap.LA_D, "durada": eap.DURADES[4], "segon": eap.ENCERTA, "n": 20}])
    imatges = pd.DataFrame([{"escenari": "net", "durada": eap.DURADES[0], "n": 100},
                            {"escenari": "net", "durada": eap.DURADES[4], "n": 900}])
    return errors, imatges


def test_les_taules_dels_errors():
    errors, imatges = errors_de_prova()
    t = eap.taula_errors(errors, imatges)
    assert t.loc["net"].tolist() == [1000, 0.06, 0.04, 0.02]
    assert eap.parts(errors, "durada", eap.DURADES).loc["net"].tolist() == [0.75, 0, 0, 0, 0.25]
    taxa = eap.taxa(errors, imatges).loc["net"]
    assert (taxa[eap.DURADES[0]], taxa[eap.DURADES[4]]) == (0.3, 10 / 900)
    c = eap.creuada(errors, ("net",), ("durada", eap.DURADES), ("segon", eap.SEGONS))
    assert (c.loc[eap.DURADES[0], eap.DUBTA], c.loc[eap.DURADES[4], eap.SEGUR], c.to_numpy().sum()) == (0.75, 0.25, 1)


def test_el_criteri_es_contra_a_xarxes():
    files, xarxes = [], {}
    for k, (nom, font) in enumerate((("p1", "dfl"), ("p2", "dfl"), ("p3", "metrica"))):
        for escenari in eap.QUARTS:
            xarxes[(escenari, nom)] = 0.60 + 0.001 * k
            for sostre in (eap.BASE, *eap.SOSTRES):
                guany = 0.05 if sostre == eap.CURTES else 0.0
                files.append({"partit": nom, "font": font, "escenari": escenari, "sostre": sostre,
                              "spell_f1": 0.62 + guany + 0.001 * k})
    linies = eap.taula_criteri(pd.DataFrame(files), pd.Series(xarxes).rename_axis(["escenari", "partit"]))
    assert next(linia for linia in linies if linia.startswith("| res més |")).split(" | ")[1].startswith("+0.020 · 3/3")
    assert next(linia for linia in linies if linia.startswith(f"| {eap.CURTES} |")).split(" | ")[1].startswith(
        "+0.070 · 3/3")
