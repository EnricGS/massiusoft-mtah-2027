"""T3p al banc: els escenaris, que les peces s'entrenen com les d'A xarxes (amb un escenari més), la memòria cau, la
tria del decodificador als ×¼ de cada mètode, el criteri del pla i l'informe."""

from __future__ import annotations

import ast
import inspect
import math
import textwrap

import numpy as np
import pandas as pd
import pytest

from banc import degrada, fonts
from banc import decodificador_tocs as t3
from banc import escenari_partit as ep
from banc import model_a_canvis as t3i
from banc import model_a_contacte as t3h
from banc import model_a_context as t3e
from banc import model_a_possessio as t3f
from banc import model_a_partit as mp
from banc import model_a_xarxes as t3o
from banc.tests import sintetic
from cadena import model

DEGRADA = "degrada.aplica(fonts.partit(nom), t3.ESCENARIS[e])"


def test_els_escenaris():
    assert mp.SIS == t3o.ENTRENAMENT and mp.SET == (*t3o.ENTRENAMENT, ep.NOM)
    assert mp.ESCENARIS == (*t3.ESCENARIS, ep.NOM) and mp.QUARTS == (*t3.QUARTS, ep.NOM)
    assert mp.ENTRENAMENT == {t3o.XARXES: mp.SIS, mp.A_PARTIT: mp.SET}
    assert mp.QUARTS_DE[t3o.XARXES] == t3.QUARTS and mp.QUARTS_DE[mp.A_PARTIT] == mp.QUARTS


def test_degradat_fa_l_escenari_del_partit_o_el_de_la_t3(monkeypatch):
    net = sintetic.partit(n=6000)
    monkeypatch.setattr(fonts, "partit", lambda nom: net)
    for escenari, esperat in ((ep.NOM, ep.aplica(net)), ("barreja ×¼", degrada.aplica(net, t3.ESCENARIS["barreja ×¼"])),
                              ("net", net)):
        assert np.array_equal(mp.degradat("x", escenari).tracking.pilota, esperat.tracking.pilota, equal_nan=True)


def cos(f, canvis: dict[str, str] | None = None) -> list[str]:
    """Les sentències de la funció, sense el docstring, amb els trossos de text de `canvis` canviats."""
    font = textwrap.dedent(inspect.getsource(f))
    for abans, despres in (canvis or {}).items():
        assert abans in font, abans
        font = font.replace(abans, despres)
    return [ast.dump(s) for s in ast.parse(font).body[0].body[1:]]


@pytest.mark.parametrize(("aqui", "alla", "canvis"), [
    (mp.entrena_xarxes, t3o.entrena_xarxes, {"ENTRENAMENT": "entrenament", DEGRADA: "degradat(nom, e)"}),
    (mp.mostres_segon, t3o.mostres_segon, {"t3h.primer_del_grup((prova, i))": "primer_del_grup((prova, i, entrenament))",
                                           "xarxes_del_grup((prova, i))": "xarxes_del_grup((prova, i, entrenament))",
                                           DEGRADA: "degradat(nom, e)"}),
    (mp.mostres_q, t3i.mostres_de, {"t3h.primer_del_grup((prova, i))": "primer_del_grup((prova, i, entrenament))",
                                    DEGRADA: "degradat(nom, e)", "x, y = mostres(": "x, y = t3i.mostres("}),
])
def test_les_mostres_son_les_d_a_xarxes_amb_els_escenaris_que_es_diuen(aqui, alla, canvis):
    assert cos(aqui) == cos(alla, canvis)


def test_el_primer_apren_les_mateixes_mostres_que_el_de_la_t3h(monkeypatch):
    """Amb els sis escenaris, les mateixes files i en el mateix ordre que `t3h.entrena_primer`."""
    monkeypatch.setattr(fonts, "partit", lambda nom: nom)
    monkeypatch.setattr(degrada, "aplica", lambda p, e: f"{p}|{e if isinstance(e, str) else e.nom}")
    monkeypatch.setattr(t3h, "taula_primer", lambda p: pd.DataFrame({"qui": [p, p]}))
    monkeypatch.setattr(t3f, "mostres", lambda p, taula: (taula, np.array([0, 1])))
    apres = []
    monkeypatch.setattr(model, "entrena", lambda x, y: apres.append((x, y)))
    for f in (t3h.mostres_primer, mp.mostres_primer):
        f.cache_clear()
    try:
        noms = list(fonts.NOMS[:3])
        t3h.entrena_primer(noms)
        mp.entrena_primer(noms, mp.SIS)
    finally:
        for f in (t3h.mostres_primer, mp.mostres_primer):
            f.cache_clear()
    (x_t3h, y_t3h), (x, y) = apres
    pd.testing.assert_frame_equal(x, x_t3h)
    np.testing.assert_array_equal(y, y_t3h)
    assert len(x) == 2 * 3 * len(mp.SIS)


def test_amb_els_sis_escenaris_els_grups_son_els_de_la_memoria_cau(monkeypatch):
    monkeypatch.setattr(t3h, "primer_del_grup", lambda tasca: {"de": ("t3h", tasca)})
    monkeypatch.setattr(t3o, "xarxes_del_grup", lambda tasca: {"de": ("t3o", tasca)})
    assert mp.primer_del_grup(("x", 1, mp.SIS)) == {"de": ("t3h", ("x", 1))}
    assert mp.xarxes_del_grup(("x", 2, mp.SIS)) == {"de": ("t3o", ("x", 2))}


def test_la_memoria_cau_porta_la_clau_i_separa_les_llistes(tmp_path, monkeypatch):
    cami = tmp_path / "x.npz"
    mp.desa(cami, a=np.arange(3))
    np.testing.assert_array_equal(mp.llegeix(cami)["a"], np.arange(3))
    assert mp.cau("segon", mp.SIS, "p") != mp.cau("segon", mp.SET, "p")
    monkeypatch.setattr(mp, "CLAU", "una altra")
    assert mp.llegeix(cami) is None


@pytest.mark.parametrize("de_qui", [lambda nom: mp.segon((nom, mp.SET), entrena=False),
                                    lambda nom: mp.q((nom, mp.SIS), entrena=False),
                                    lambda nom: mp.a_context(nom, entrena=False)])
def test_sense_entrenar_s_atura_si_no_hi_son(tmp_path, monkeypatch, de_qui):
    monkeypatch.setattr(mp, "DIR_CAU", tmp_path)
    with pytest.raises(RuntimeError, match="Falten"):
        de_qui(fonts.NOMS[0])


def test_la_diferencia():
    a = np.array([[0.2, np.nan], [0.5, 0.5]])
    assert mp.diferencia(a, a.copy()) == 0.0
    assert mp.diferencia(a, a + 0.01) == pytest.approx(0.01)
    assert mp.diferencia(a, np.nan_to_num(a)) == math.inf
    assert mp.diferencia(a, a[:1]) == math.inf


COMBOS = {t3e.CONTEXT: ((math.nan, 4.0, 12), (math.nan, 8.0, 25)), t3o.XARXES: ((2.0, 32.0, 1), (1.0, 8.0, 25)),
          mp.A_PARTIT: ((2.0, 32.0, 1), (1.0, 8.0, 25))}


def graella(spell) -> pd.DataFrame:
    """De cada mètode, dues combinacions del decodificador; `spell(metode, combinacio, escenari, i)`."""
    files = []
    for i, nom in enumerate(fonts.NOMS):
        for escenari in mp.ESCENARIS:
            comu = {"partit": nom, "font": "dfl" if i < 7 else "metrica", "escenari": escenari, "macro_f1": 0.8,
                    "possessions": 300, "possessions_reals": 400}
            for metode, combos in COMBOS.items():
                files += [{**comu, "metode": metode, "w": w, "lam": lam, "d_min": d_min,
                           "spell_f1": spell(metode, k, escenari, i)} for k, (w, lam, d_min) in enumerate(combos)]
    return pd.DataFrame(files)


def test_a_partit_tria_als_cinc_x_quart_i_els_altres_als_quatre():
    """La primera combinació, 0,60 als ×¼ d'ara i 0,90 a «partit ×¼»; la segona, 0,65 a tots: als cinc guanya la
    primera, i als quatre, la segona."""
    def spell(metode, k, escenari, i):
        return (0.90 if escenari == ep.NOM else 0.60) if k == 0 else 0.65

    _, triades = mp.tria_sense_mirar(graella(spell))
    assert all(t[mp.A_PARTIT] == (2.0, 32.0, 1) and t[t3o.XARXES] == (1.0, 8.0, 25)
               and t[t3e.CONTEXT] == (8.0, 25) for t in triades.values())


def amb_guany(guany: dict[str, float]):
    def spell(metode, k, escenari, i):
        if k == 1:
            return 0.40
        return 0.60 + 0.01 * ((i % 3) - 1) + (guany.get(escenari, 0.0) if metode == mp.A_PARTIT else 0.0)
    return spell


@pytest.mark.parametrize(("guany", "passa"), [({ep.NOM: 0.06, "net": -0.03}, {"partit": True, "altres": True}),
                                              ({ep.NOM: 0.06, "llargs ×¼": -0.05}, {"partit": True, "altres": False}),
                                              ({ep.NOM: 0.03}, {"partit": False, "altres": True})])
def test_el_criteri_es_contra_a_xarxes_i_guanya_a_partit(guany, passa):
    metodes, _ = mp.tria_sense_mirar(graella(amb_guany(guany)))
    c = mp.comparacio(metodes, mp.A_PARTIT, t3o.XARXES)
    assert mp.compleix(c) == passa
    assert set(c["criteri"]) == {"guanya clarament", "no perd"} and (c["criteri"] == "guanya clarament").sum() == 1


def test_l_informe():
    metodes, triades = mp.tria_sense_mirar(graella(amb_guany({ep.NOM: 0.06})))
    c = mp.comparacio(metodes, mp.A_PARTIT, t3o.XARXES)
    c_pas1 = mp.comparacio(metodes, t3o.XARXES, t3e.CONTEXT)
    r = {nom: dict.fromkeys(mp.PECES, 0.0) for nom in fonts.NOMS}
    r[fonts.NOMS[0]]["les cinc xarxes"] = 1e-3
    md = mp.markdown(c, c_pas1, metodes, triades, mp.compleix(c), r)
    assert "## A partit contra A xarxes (spellF1): el criteri" in md and "**Passa.**" in md
    assert "| A xarxes | 0 | ✓ la mateixa |" in md and "| les cinc xarxes | 0.001 | ⚠ no és la mateixa |" in md
    assert "| partit ×¼ |" in md and "A partit: w = 2, λ = 32, durada mínima 1 (10 partits)" in md
    assert "nan" not in md
