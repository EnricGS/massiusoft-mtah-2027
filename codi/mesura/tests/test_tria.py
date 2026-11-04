"""La tria per passos: cada pas, entre els candidats que encaixen amb el que s'ha triat abans."""

from __future__ import annotations

import pandas as pd
import pytest

from mesura import tria as tr


def test_la_distancia_divideix_per_com_varia_cada_mesura():
    mitjanes = pd.DataFrame({"x": [0.0, 1.0], "y": [0.0, 0.0]}, index=["a", "b"])
    p = tr.parts({"x": 0.4, "y": 3.0}, mitjanes, pd.Series({"x": 0.1, "y": 100.0}))
    assert p.sum(axis=1).idxmin() == "a" and p.loc["a", "x"] == pytest.approx(16.0)


def taula() -> pd.DataFrame:
    """Dos paràmetres: «a» es veu a la mesura u; «b», a la mesura v, però només quan «a» és 1 (quan és 0, v no
    diu res i va pel seu compte)."""
    files = []
    for partit in range(3):
        for a in (0, 1):
            for b in ("x", "y"):
                v = (10.0 if b == "y" else 0.0) if a == 1 else 5.0 + partit
                files.append({"partit": partit, "a": a, "b": b, "u": a + 0.01 * partit, "v": v + 0.1 * partit})
    return pd.DataFrame(files)


PASSOS = ((("a",), ("u",)), (("b",), ("v",)))


def test_el_segon_pas_nomes_mira_els_candidats_del_primer():
    t = tr.tria({"u": 0.98, "v": 9.5}, taula(), PASSOS)
    assert t.parametres == {"a": 1, "b": "y"}
    assert set(t.passos[1]["b"]) == {"x", "y"} and len(t.passos[1]) == 2


def test_la_distancia_es_la_suma_dels_passos_al_triat():
    t = tr.tria({"u": 0.98, "v": 9.5}, taula(), PASSOS)
    assert t.distancia == pytest.approx(t.passos[0]["distancia"].iloc[0] + t.passos[1]["distancia"].iloc[0])
    assert set(t.parts) == {"u", "v"}


def test_els_valors_triats_son_de_python():
    t = tr.tria({"u": 0.0, "v": 5.0}, taula(), PASSOS)
    assert type(t.parametres["a"]) is int


def test_els_passos_del_json():
    assert tr.passos_de({"passos": [[["a"], ["u"]], [["b"], ["v", "w"]]]}) == ((("a",), ("u",)), (("b",), ("v", "w")))
