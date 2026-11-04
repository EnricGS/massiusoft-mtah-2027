"""El marge que queda a sobre d'A equips sencers: els forats segons la possessió, els sostres i les taules."""

from __future__ import annotations

import numpy as np
import pandas as pd

from banc import marge_equips as mme
from possessio.oficial import possession_metrics as pm

H, A, D = pm.H, pm.A, pm.D


def test_els_forats_segons_si_la_possessio_es_veu_algun_cop():
    toc = np.array([H] * 10 + [A] * 10 + [D] * 5 + [H] * 15, dtype=np.int8)
    vista = np.ones(40, dtype=bool)
    vista[3:22] = False
    forat = ~vista
    mai, algun_cop = mme.per_possessio(toc, [(0, 40)], vista, forat)
    assert np.flatnonzero(mai).tolist() == list(range(10, 20))
    assert np.flatnonzero(algun_cop).tolist() == list(range(3, 10))


def test_cada_sostre_te_la_seva_prediccio_i_la_base_no_es_toca():
    toc = np.array([H] * 30 + [A] * 30 + [H] * 40, dtype=np.int8)
    vista = np.ones(100, dtype=bool)
    vista[35:55] = False
    bona, dolenta = (1.0, -1.0, 0.0), (-1.0, 1.0, 0.0)
    relativa = np.array([bona] * 30 + [dolenta] * 30 + [bona] * 40)
    q = np.zeros(100)
    pred = np.where(relativa[:, 0] > 0, H, A).astype(np.int8)

    def decodifica(r: np.ndarray, q_: np.ndarray = q) -> np.ndarray:
        return np.where(r[:, 0] >= r[:, 1], H, A).astype(np.int8)

    copia = relativa.copy()
    s = mme.sostres(relativa, q, pred, toc, [(0, 100)], vista, decodifica)
    assert set(s) == set(mme.SOSTRES)
    np.testing.assert_array_equal(relativa, copia)
    assert (s[mme.msm.SEGON] == toc).all()
    assert (s[mme.EQUIP_MAI] == pred).all()                      # l'A es veu a 30-34 i 55-59: no n'hi ha cap «mai»
    assert (s[mme.EQUIP_ALGUN_COP][35:55] == A).all()


def files_de_prova() -> pd.DataFrame:
    files = []
    for k, (nom, font) in enumerate((("p1", "dfl"), ("p2", "dfl"), ("p3", "metrica"))):
        for escenari in mme.ESCENARIS:
            files.append({"partit": nom, "font": font, "escenari": escenari, "base": mme.XARXES, "sostre": mme.BASE,
                          "spell_f1": 0.60 + 0.001 * k})
            for base, nivell in ((mme.A_SENSE, 0.62), (mme.A_EQUIPS, 0.63)):
                for sostre in (mme.BASE, *mme.SOSTRES):
                    guany = 0.05 if sostre == mme.EQUIP_MAI else 0.0
                    files.append({"partit": nom, "font": font, "escenari": escenari, "base": base, "sostre": sostre,
                                  "spell_f1": nivell + guany + 0.001 * k})
    return pd.DataFrame(files)


def test_la_taula_del_marge_va_d_a_sense_pilota_a_a_equips_sencers():
    linies = mme.taula_marge(files_de_prova())
    assert linies[2].split(" | ")[1] == "0.621 → 0.631"
    mai = next(linia for linia in linies if linia.startswith(f"| {mme.EQUIP_MAI} |"))
    assert mai.split(" | ")[1] == "+0.050 → +0.050"


def test_la_taula_del_criteri_es_contra_a_xarxes():
    linies = mme.taula_criteri(files_de_prova())
    res_mes = next(linia for linia in linies if linia.startswith("| res més |"))
    assert res_mes.split(" | ")[1].startswith("+0.030 · 3/3")
    mai = next(linia for linia in linies if linia.startswith(f"| {mme.EQUIP_MAI} |"))
    assert mai.split(" | ")[1].startswith("+0.080 · 3/3")


def test_la_taula_dels_errors_te_les_tres_bases():
    errors = pd.DataFrame([{"partit": "p", "escenari": "net", "base": base, "on": on, "n": 100, "encerts": e}
                           for base in mme.TOTES for on, e in ((mme.AMB_PILOTA, 90), (mme.ALS_FORATS, 70))])
    t = mme.taula_errors(errors)
    assert t.loc["net", (mme.AMB_PILOTA, mme.A_EQUIPS)] == 0.1
    assert t.loc["net", (mme.PART_ALS_FORATS, mme.XARXES)] == 0.75
