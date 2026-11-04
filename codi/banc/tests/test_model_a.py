"""La tria del decodificador al banc: amb els altres partits, mai amb el que es puntua, i sense mirar el net."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from banc import degrada, model_a
from banc.tests import sintetic
from cadena import decodifica


def fila(partit: str, escenari: str, lam: float, spell: float, metode: str = "graella") -> dict:
    return {"partit": partit, "font": "dfl", "escenari": escenari, "metode": metode, "lam": lam, "d_min": 1,
            "spell_f1": spell, "macro_f1": 0.5, "possessions": 10, "possessions_reals": 10}


def graella(preferits: dict[str, float], escenaris=degrada.NOMS) -> pd.DataFrame:
    """Cada partit puntua 0,6 amb la seva λ preferida i 0,3 amb les altres."""
    files = [fila(p, e, lam, 0.6 if lam == bona else 0.3)
             for p, bona in preferits.items() for e in escenaris for lam in (1.0, 4.0, 16.0)]
    files += [fila(p, e, np.nan, 0.2, "smooth125·X") for p in preferits for e in escenaris]
    return pd.DataFrame(files)


def test_cada_partit_es_puntua_amb_la_tria_dels_altres():
    files = graella({"a": 1.0, "b": 4.0, "c": 4.0, "d": 4.0})
    a = model_a.tria_sense_mirar(files).query("metode == 'A'")
    assert set(a.loc[a["partit"] == "a", "lam"]) == {4.0}
    assert (a.loc[a["partit"] == "a", "spell_f1"] == 0.3).all()
    assert set(a.loc[a["partit"] == "b", "lam"]) == {4.0}
    assert len(a) == 4 * len(degrada.NOMS)


def test_el_net_no_compta_per_triar():
    files = graella({"a": 4.0, "b": 4.0})
    files.loc[(files["escenari"] == "net") & (files["lam"] == 16.0), "spell_f1"] = 0.99
    assert model_a.millor(files) == (4.0, 1)


def test_clarament_vol_mes_que_el_soroll_i_un_interval_que_no_toqui_el_zero():
    files = graella({p: 4.0 for p in "abcdef"})
    metodes = model_a.tria_sense_mirar(files)
    c = model_a.comparacio(metodes, "smooth125·X")
    assert c["clarament"].all() and (c["guanya"] == 6).all()
    np.testing.assert_allclose(c["diferencia"], 0.4)
    poc = metodes.assign(spell_f1=np.where(metodes["metode"] == "A", 0.22, metodes["spell_f1"]))
    assert not model_a.comparacio(poc, "smooth125·X")["clarament"].any()


def test_la_clau_canvia_amb_la_manera_d_entrenar(monkeypatch):
    abans = model_a.clau()
    monkeypatch.setattr(model_a.model, "PAS", model_a.model.PAS + 1)
    assert model_a.clau() != abans


def test_el_model_d_un_partit_no_s_entrena_mai_amb_ell(monkeypatch, tmp_path):
    entrena, sense_cau = model_a.model.entrena, model_a.mostres_de.__wrapped__
    vistos = []

    def espia(nom):
        vistos.append(nom)
        return sense_cau(nom)

    monkeypatch.setattr(model_a, "DIR_CAU_A", tmp_path)
    monkeypatch.setattr(model_a.fonts, "NOMS", ("a", "b", "c"))
    monkeypatch.setattr(model_a.fonts, "partit", lambda nom: sintetic.partit(n=3000, nom=nom))
    monkeypatch.setattr(model_a, "mostres_de", espia)
    monkeypatch.setattr(model_a.model, "entrena", lambda x, y: entrena(x, y, rondes=3))
    probes, prior = model_a.probabilitats("b")
    assert sorted(vistos) == ["a", "c"] and set(probes) == set(degrada.NOMS) and prior.shape == (3,)
    vistos.clear()
    desades, _ = model_a.probabilitats("b", entrena=False)
    assert vistos == [] and all(np.array_equal(desades[e], probes[e]) for e in probes)
    with pytest.raises(RuntimeError):
        model_a.probabilitats("a", entrena=False)


def test_la_clau_canvia_si_canvia_la_degradacio(monkeypatch, tmp_path):
    abans = model_a.clau()
    altra = tmp_path / "degrada.py"
    altra.write_text(Path(degrada.__file__).read_text() + "\n# un canvi\n")
    monkeypatch.setattr(degrada, "__file__", str(altra))
    assert model_a.clau() != abans


def test_la_clau_dels_resultats_canvia_si_canvia_el_decodificador(monkeypatch, tmp_path):
    abans = model_a.clau_dels_resultats()
    altre = tmp_path / "decodifica.py"
    altre.write_text(Path(decodifica.__file__).read_text() + "\n# un canvi\n")
    monkeypatch.setattr(decodifica, "__file__", str(altre))
    assert model_a.clau_dels_resultats() != abans


def test_el_json_no_porta_nan():
    files = graella({"a": 4.0})
    text = model_a.a_json(files, "clau")
    assert "NaN" not in text and json.loads(text)["files"][-1]["lam"] is None


def test_els_resultats_d_un_altre_codi_no_valen(tmp_path):
    files = graella({"a": 4.0})
    (tmp_path / "bo.json").write_text(model_a.a_json(files, model_a.CLAU_RESULTATS))
    (tmp_path / "vell.json").write_text(model_a.a_json(files, "una clau vella"))
    pd.testing.assert_frame_equal(model_a.resultats(tmp_path / "bo.json"),
                                  files.astype(object).where(files.notna(), None).infer_objects(), check_dtype=False)
    with pytest.raises(RuntimeError):
        model_a.resultats(tmp_path / "vell.json")


def test_el_bootstrap_tria_partits_dins_de_cada_font():
    dif = np.array([1.0] * 7 + [0.0] * 3)
    grups = np.array(["dfl"] * 7 + ["metrica"] * 3)
    assert model_a.interval(dif, grups) == pytest.approx((0.7, 0.7))
    baix, alt = model_a.interval(dif, np.array(["tots"] * 10))
    assert baix < 0.7 < alt
