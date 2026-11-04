"""Com són els errors d'equip als forats: on és cada imatge, el toc més proper, el segon, els trets, els sostres i les
taules."""

from __future__ import annotations

import numpy as np
import pandas as pd

from banc import errors_als_forats as eaf
from possessio.oficial import possession_metrics as pm

H, A, D = pm.H, pm.A, pm.D
K = eaf.t3i.K


def etiqueta(*trossos: tuple[int, int]) -> np.ndarray:
    return np.concatenate([np.full(n, codi, dtype=np.int8) for codi, n in trossos])


def test_on_es_cada_imatge_dels_forats():
    curt, llarg = pm.FPS, 3 * pm.FPS
    vista = np.concatenate([np.ones(100, bool), np.zeros(curt, bool), np.ones(100, bool), np.zeros(llarg, bool),
                            np.ones(100, bool)])
    on = eaf.on_del_forat(vista)
    primer, segon = 100, 200 + curt
    assert set(on[primer - K:primer]) == {eaf.VORA} and on[primer - K - 1] == ""
    assert set(on[primer:primer + curt]) == {eaf.FORATS[1]}
    assert set(on[primer + curt:primer + curt + K]) == {eaf.VORA} and on[primer + curt + K] == ""
    assert set(on[segon:segon + llarg]) == {eaf.FORATS[2]}


def test_el_toc_mes_proper_si_es_veu_i_a_quina_distancia():
    toc = etiqueta((H, 10), (A, 10), (H, 10))
    vista = np.ones(30, dtype=bool)
    vista[8:15] = False
    vist, lluny = eaf.toc_proper(toc, [(0, 30)], vista)
    assert (vist[12], lluny[12]) == (eaf.TOC_SENSE, 2)                  # el toc que comença l'A, sense pilota
    assert (vist[18], lluny[18]) == (eaf.TOC_VIST, 2)                   # el que l'acaba, a la vista
    assert (vist[0], lluny[0]) == (eaf.TOC_VIST, 0)


def test_que_en_diu_el_segon_tambe_la_d():
    toc = np.array([H, H, H, H, D])
    relativa = np.array([[0.0, -1, 0], [0, 1, 0], [0, 3, 0], [0, 0, 5], [0, 0, 5]])
    assert eaf.segon(relativa, toc).tolist() == [eaf.eap.ENCERTA, eaf.eap.DUBTA, eaf.eap.SEGUR, eaf.DONA_D, ""]


def test_la_d_perfecta_nomes_on_es_diu():
    toc = np.array([H, D, H, D])
    relativa = np.zeros((4, 3))
    on = np.array([True, True, False, False])
    out = eaf.d_perfecta(relativa, toc, on)
    assert out[0, D] < 0 and out[1, D] > 0 and out[1, H] < 0
    np.testing.assert_array_equal(out[2:], relativa[2:])
    assert (relativa == 0).all()


def test_els_trets_dels_errors_als_forats():
    toc = etiqueta((H, 20), (A, 20))
    pred = etiqueta((H, 25), (A, 15))                                    # hi arriba 5 imatges tard
    vista = np.ones(40, dtype=bool)
    vista[15:31] = False
    al_forat = eaf.sc.forats(vista)
    totes, errors = eaf.trets(pred, toc, np.zeros((40, 3)), vista, al_forat, [(0, 40)])
    assert totes["n"].sum() == al_forat.sum() and totes.loc[totes["dona"] != eaf.BE, "n"].sum() == 5
    assert errors[list(eaf.TRETS)].values.tolist() == [[eaf.L_ALTRE, eaf.paf.ALGUN_COP, eaf.FORATS[1],
                                                        eaf.eap.AL_COMENCAMENT, eaf.TOC_SENSE, eaf.eap.DISTANCIES[0],
                                                        eaf.eap.DURADES[1], eaf.eap.DUBTA]]
    assert errors["n"].tolist() == [5]


def test_les_mascares_dels_sostres():
    on = np.array([eaf.VORA, eaf.FORATS[1], eaf.FORATS[1], eaf.FORATS[3], ""], dtype=object)
    diu = np.array([eaf.eap.DUBTA, eaf.eap.SEGUR, eaf.eap.ENCERTA, eaf.eap.DUBTA, eaf.eap.DUBTA], dtype=object)
    m = eaf.mascares(on, diu, on != "")
    assert {s: int(x.sum()) for s, x in m.items()} == {eaf.EQUIP: 4, eaf.A_LA_VORA: 1, eaf.CURTS: 2, eaf.MITJANS: 0,
                                                      eaf.LLARGS: 1, eaf.SI_DUBTA: 2, eaf.SI_SEGUR: 1}


def imatges_de_prova() -> pd.DataFrame:
    files = []
    for base, (vora, forat) in ((eaf.A_SENSE, (20, 50)), (eaf.A_EQUIPS, (10, 40))):
        for on, mal, dona in ((eaf.VORA, vora, eaf.L_ALTRE), (eaf.FORATS[1], forat, eaf.LA_D)):
            files += [{"escenari": "curts ×¼", "base": base, "forat": on, "es veu": eaf.paf.MAI, "dona": eaf.BE,
                       "segon": eaf.eap.ENCERTA, "n": 100 - mal},
                      {"escenari": "curts ×¼", "base": base, "forat": on, "es veu": eaf.paf.MAI, "dona": dona,
                       "segon": eaf.eap.DUBTA if dona == eaf.L_ALTRE else eaf.eap.ENCERTA, "n": mal}]
    return pd.DataFrame(files)


def test_la_taula_de_les_bases():
    t = eaf.taula_bases(imatges_de_prova())
    assert t.loc["curts ×¼", ("errors", eaf.A_SENSE)] == 0.35
    assert t.loc["curts ×¼", ("errors", eaf.A_EQUIPS)] == 0.25
    assert t.loc["curts ×¼", (eaf.LA_D, eaf.A_EQUIPS)] == 0.2
    assert t.loc["curts ×¼", ("el segon s'equivoca", eaf.A_EQUIPS)] == 0.05


def test_la_d_per_font():
    imatges = imatges_de_prova().assign(font="dfl")
    t = eaf.taula_d_per_font(pd.concat([imatges, imatges.assign(font="metrica", n=imatges["n"] * 2)]))
    assert list(t.index) == [("curts ×¼", "dfl"), ("curts ×¼", "metrica")]
    assert t.loc[("curts ×¼", "dfl")].tolist() == [0.25, 0.2]


def test_la_taula_d_on_son():
    t = eaf.taula_on(imatges_de_prova(), "forat", eaf.FORATS)
    assert list(t.index) == [("curts ×¼", eaf.VORA), ("curts ×¼", eaf.FORATS[1])]
    assert t.loc[("curts ×¼", eaf.VORA)].tolist() == [0.5, 0.2, 0.1, 0.0, 0.2]
    assert t.loc[("curts ×¼", eaf.FORATS[1])].tolist() == [0.5, 0.5, 0.4, 0.4, 0.8]


def test_les_parts_i_la_creuada_son_d_a_equips_sencers():
    errors = pd.DataFrame([{"escenari": "aire ×¼", "base": base, "lloc": lloc, "segon": segon, "n": n}
                           for base in eaf.BASES
                           for lloc, segon, n in ((eaf.eap.TOTA, eaf.eap.SEGUR, 30), (eaf.eap.AL_FINAL, eaf.DONA_D, 10))])
    p = eaf.parts(errors, "lloc", eaf.eap.LLOCS)
    assert p.loc["aire ×¼"].tolist() == [0.75, 0.0, 0.25, 0.0]
    c = eaf.creuada(errors, "aire ×¼", ("lloc", eaf.eap.LLOCS), ("segon", eaf.SEGONS))
    assert c.loc[eaf.eap.TOTA, eaf.eap.SEGUR] == 0.75 and c.to_numpy().sum() == 1
