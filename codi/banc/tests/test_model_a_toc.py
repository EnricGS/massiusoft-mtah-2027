"""T3q al banc: només hi canvia la veritat, les peces aprenen com les d'A xarxes, el decodificador es tria a la
veritat que toca, el Pas 1 i el criteri del pla."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from banc import fonts
from banc import model_a_partit as mp
from banc import model_a_toc as mt
from banc import veritat_toc as vt
from banc.tests import sintetic
from banc.tests.test_model_a_partit import cos
from possessio.oficial import possession_metrics as pm


def test_degradat_nomes_hi_canvia_la_veritat(monkeypatch):
    net = sintetic.partit(n=6000)
    de_toc = np.where(net.veritat == pm.H, pm.A, net.veritat).astype(np.int8)
    monkeypatch.setattr(fonts, "partit", lambda nom: net)
    monkeypatch.setattr(vt, "veritat", lambda nom: de_toc)
    p, de_sempre = mt.degradat("x", "barreja ×¼"), mp.degradat("x", "barreja ×¼")
    assert np.array_equal(p.veritat, de_toc)
    assert np.array_equal(p.tracking.pilota, de_sempre.tracking.pilota, equal_nan=True)
    assert p.trams == de_sempre.trams


@pytest.mark.parametrize(("aqui", "alla", "canvis"), [
    (mt.entrena_primer, mp.entrena_primer, {"for e in entrenament": "for e in SIS"}),
    (mt.entrena_xarxes, mp.entrena_xarxes, {"for e in entrenament": "for e in SIS"}),
    (mt.mostres_segon, mp.mostres_segon, {"primer_del_grup((prova, i, entrenament))": "primer_del_grup((prova, i))",
                                          "xarxes_del_grup((prova, i, entrenament))": "xarxes_del_grup((prova, i))"}),
    (mt.mostres_q, mp.mostres_q, {"primer_del_grup((prova, i, entrenament))": "primer_del_grup((prova, i))"}),
])
def test_les_peces_aprenen_com_les_d_a_xarxes(aqui, alla, canvis):
    """El mateix codi que A xarxes (amb els sis escenaris): la diferència és el `degradat` d'aquí."""
    assert cos(aqui) == cos(alla, canvis)


def files_de_prova(millor: dict[str, tuple[float, float, int]]) -> pd.DataFrame:
    """Dos punts de graella; a cada veritat, el de `millor` hi treu més a tots els partits i escenaris."""
    files = []
    for nom in fonts.NOMS:
        for escenari in mt.ESCENARIS:
            for veritat in (mt.SEMPRE, mt.TOC):
                for punt in ((1.0, 4.0, 1), (2.0, 8.0, 12)):
                    files.append({"partit": nom, "font": nom.split("-")[0], "escenari": escenari,
                                  "metode": mt.XARXES, "veritat": veritat, "w": punt[0], "lam": punt[1],
                                  "d_min": punt[2], "spell_f1": 0.7 if punt == millor[veritat] else 0.6,
                                  "macro_f1": 0.5})
    return pd.DataFrame(files)


def test_el_decodificador_es_tria_a_la_veritat_que_es_diu():
    files = files_de_prova({mt.SEMPRE: (1.0, 4.0, 1), mt.TOC: (2.0, 8.0, 12)})
    for veritat, esperat in ((mt.SEMPRE, (1.0, 4.0, 1)), (mt.TOC, (2.0, 8.0, 12))):
        triats, triades = mt.tria_sense_mirar(files, mt.XARXES, veritat, "triat")
        assert set(triades.values()) == {esperat}
        assert set(triats["metode"]) == {"triat"} and set(triats["veritat"]) == {mt.SEMPRE, mt.TOC}
        assert len(triats) == len(fonts.NOMS) * len(mt.ESCENARIS) * 2


def test_el_decodificador_d_a_xarxes_ha_de_ser_el_de_la_t3p(monkeypatch):
    triades = {nom: (4.0, 32.0, 12) for nom in fonts.NOMS}
    monkeypatch.setattr(mt, "triades_t3p", lambda: {nom: {mt.XARXES: [4.0, 32.0, 12]} for nom in fonts.NOMS})
    mt.comprova_el_decodificador(triades)
    with pytest.raises(RuntimeError):
        mt.comprova_el_decodificador(triades | {fonts.NOMS[0]: (4.0, 16.0, 12)})


def metodes_de_prova(dif: dict[str, float], nou: str, contra: str, veritat: str) -> pd.DataFrame:
    files = []
    for k, nom in enumerate(fonts.NOMS):
        for escenari in mt.ESCENARIS:
            base = 0.6 + 0.001 * k
            files += [{"partit": nom, "font": nom.split("-")[0], "escenari": escenari, "veritat": veritat,
                       "metode": contra, "spell_f1": base},
                      {"partit": nom, "font": nom.split("-")[0], "escenari": escenari, "veritat": veritat,
                       "metode": nou, "spell_f1": base + dif.get(escenari, 0.0)}]
    return pd.DataFrame(files)


def test_el_pas_1_diu_quant_perd_a_la_veritat_de_toc():
    de_xarxes = metodes_de_prova({e: -0.02 for e in mt.QUARTS}, mt.TOC, mt.SEMPRE, mt.TOC)
    de_xarxes = de_xarxes.assign(veritat=de_xarxes["metode"], metode=mt.XARXES)
    c1 = mt.pas_1(de_xarxes)
    assert mt.perd_als_quarts(c1) == pytest.approx(0.02)
    assert c1.set_index("escenari").loc["net", "diferencia"] == pytest.approx(0.0)


@pytest.mark.parametrize(("dif", "passa"), [
    ({e: 0.05 for e in mt.QUARTS}, {"quarts": True, "altres": True}),
    ({e: 0.03 for e in mt.QUARTS}, {"quarts": False, "altres": True}),
    ({**{e: 0.05 for e in mt.QUARTS}, mp.PARTIT: -0.05}, {"quarts": True, "altres": False}),
])
def test_el_criteri_del_pla(dif, passa):
    metodes = metodes_de_prova(dif, mt.A_TOC, mt.XARXES, mt.TOC)
    c = mt.comparacio(metodes, mt.A_TOC, mt.XARXES, mt.TOC, amb_criteri=True)
    assert mt.compleix(c) == passa
    assert set(c[c["escenari"].isin(mt.QUARTS)]["criteri"]) == {"guanya clarament"}
