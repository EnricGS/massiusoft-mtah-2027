"""El resum del banc per al document: els passos, cadascun del seu banc, la millor línia base de cada escenari, les
comparacions amb el model de la cadena i les línies base als escenaris de la T3."""

from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd
import pytest

from banc import avalua, degrada, fonts, linies_base, resum
from banc import decodificador_tocs as t3
from banc import model_a_aturades as t3k
from banc import model_a_canvis as t3i
from banc import model_a_contacte as t3h
from banc import model_a_context as t3e
from banc import model_a_possessio as t3f
from banc import model_a_xarxa as t3m
from banc import model_a_xarxes as t3o
from banc.tests import sintetic
from banc.tests.test_model_a import fila
from cadena import decodifica

CRUES = {e: 0.25 for e in t3.ESCENARIS}


def metodes(context: float = 0.6) -> pd.DataFrame:
    """Quatre partits (tres de DFL i un de Metrica) a tots els escenaris: A xarxes fa `context` (0,1 més a
    Metrica), els altres passos 0,5, smooth125·X 0,3 (0,35 a «net») i smooth50·X 0,2."""
    files = []
    for i, p in enumerate(("a", "b", "c", "d")):
        font = "metrica" if i == 3 else "dfl"
        for e in t3.ESCENARIS:
            puntua = {resum.NOU: context + (0.1 if font == "metrica" else 0), "smooth125·X": 0.35 if e == "net"
                      else 0.3, resum.PUBLICADA: 0.2, "smooth125·D": 0.32 if e == "net" else 0.1}
            puntua |= {m: 0.5 for m in resum.CLASSIFICADORS if m != resum.NOU}
            files += [{**fila(p, e, np.nan, s, m), "font": font, "possessions": 8} for m, s in puntua.items()]
    return pd.DataFrame(files)


def test_sense_decodificar_es_la_mitjana_de_cada_escenari():
    files = pd.DataFrame([{"partit": "a", "escenari": "net", "spell_f1": 0.2},
                          {"partit": "b", "escenari": "net", "spell_f1": 0.4},
                          {"partit": "a", "escenari": "curts", "spell_f1": 0.9}])
    assert resum.sense_decodificar(files) == {"net": pytest.approx(0.3), "curts": pytest.approx(0.9)}


def test_sense_decodificar_es_la_classe_mes_probable_de_cada_imatge_amb_les_probabilitats_d_a_xarxes(monkeypatch):
    """Amb les probabilitats d'A xarxes de l'escenari, λ = 0 i durada mínima 1: el mateix que fa el decodificador."""
    partit = sintetic.partit(n=6000)
    rng = np.random.default_rng(3)
    probes = {e: rng.dirichlet((1, 1, 1), partit.n).astype(np.float32) for e in t3.ESCENARIS}
    prior = np.array([0.4, 0.4, 0.2])
    monkeypatch.setattr(fonts, "partit", lambda nom: partit)
    monkeypatch.setattr(t3o, "probabilitats", lambda nom, entrena: (probes, prior))
    fila_ = resum.sense_decodificar_de(("sintetic", "llargs ×¼"))
    p = degrada.aplica(partit, t3.ESCENARIS["llargs ×¼"])
    pred = decodifica.per_trams(probes["llargs ×¼"].astype(float), prior, p.trams, 0.0, 1)
    assert fila_ == {"partit": "sintetic", "escenari": "llargs ×¼", "spell_f1": avalua.puntua(p, pred)["spell_f1"]}


def test_compara_dona_la_diferencia_l_interval_i_els_partits_que_guanya():
    c = resum.compara(metodes(), "net", resum.NOU, resum.PUBLICADA)
    assert c["diferencia"] == pytest.approx(0.425) and c["guanya"] == 4 and c["partits"] == 4
    assert 0 < c["baix"] <= c["diferencia"] <= c["alt"]


def test_la_millor_linia_base_es_la_de_mes_spell_a_cada_escenari():
    r = resum.resum(metodes(), CRUES).set_index("escenari")
    assert list(r.index) == list(t3.ESCENARIS)
    assert r.loc["curts ×¼", "millor base"] == "smooth125·X" and r.loc["curts ×¼", "spell millor base"] == 0.3
    assert r.loc["net", "millor base"] == "smooth125·X" and r.loc["net", "spell millor base"] == 0.35
    assert r.loc["aire", "spell publicada"] == pytest.approx(0.2)
    assert r.loc["aire", "diferencia millor base"] == pytest.approx(0.325)
    assert r.loc["aire", f"spell {resum.NOU}"] == pytest.approx(0.625)
    assert r.loc["aire", f"diferencia {t3e.CONTEXT}"] == pytest.approx(0.125)
    assert r.loc["aire", f"guanya {t3e.CONTEXT}"] == 4


def test_per_font_i_les_possessions():
    r = resum.resum(metodes(), CRUES).set_index("escenari")
    assert r.loc["net", "spell dfl"] == pytest.approx(0.6) and r.loc["net", "spell metrica"] == pytest.approx(0.7)
    assert r.loc["net", "possessions per real"] == pytest.approx(0.8)


def test_sense_partits_d_una_font_no_s_atura():
    m = metodes()
    r = resum.resum(m[m["font"] == "dfl"], CRUES).set_index("escenari")
    assert np.isnan(r.loc["net", "spell metrica"])


def test_l_informe_porta_totes_les_taules():
    triades = {p: {resum.NOU: (4.0, 32.0, 12)} for p in ("a", "b", "c")} | {"d": {resum.NOU: (2.0, 16.0, 25)}}
    text = resum.markdown(resum.resum(metodes(), CRUES), triades)
    assert "## A xarxes contra la millor línia base (spellF1)" in text and "smooth125·X" in text
    assert "## A xarxes contra A context (spellF1)" in text and "## A xarxes contra A ×1+×¼ (spellF1)" in text
    assert "w = 4, λ = 32 i durada mínima 12 en 3 partits; w = 2, λ = 16 i durada mínima 25 en 1 partits" in text
    assert "nan" not in text


def test_les_linies_base_a_un_escenari_de_la_t3(monkeypatch):
    partit = sintetic.partit(n=6000)
    monkeypatch.setattr(fonts, "partit", lambda nom: partit)
    files = resum.linies_base_de(("sintetic", "curts ×¼"))
    assert len(files) == len(linies_base.FINESTRES) * len(linies_base.SENSE_PILOTA)
    assert {f["metode"] for f in files} >= {"smooth125·X", resum.PUBLICADA, "raw·D"}
    assert all(0 <= f["spell_f1"] <= 1 and f["escenari"] == "curts ×¼" for f in files)


def test_amb_resultats_d_un_altre_codi_s_atura(monkeypatch, capsys):
    def d_un_altre_codi():
        raise RuntimeError("Els resultats del banc són d'un altre codi")
    monkeypatch.setattr(resum, "resultats", d_un_altre_codi)
    assert resum.main([]) == 1
    assert capsys.readouterr().out.startswith("✗ Els resultats del banc són d'un altre codi")


def test_sense_els_resultats_d_un_banc_ho_diu(monkeypatch, capsys):
    def no_hi_son():
        raise FileNotFoundError("model-a-xarxa.json")
    monkeypatch.setattr(resum, "resultats", no_hi_son)
    assert resum.main([]) == 1
    assert capsys.readouterr().out.startswith("✗ Els resultats d'algun banc dels passos no hi són")


def test_els_resultats_d_un_altre_codi_no_valen(tmp_path):
    cami = tmp_path / "model-a-context.json"
    cami.write_text(json.dumps({"clau": "una altra", "files": []}))
    with pytest.raises(RuntimeError, match="un altre codi: torna a fer `python -I -m banc.model_a_context`"):
        resum.llegeix(t3e, cami)
    files = [fila("s1", "curts ×¼", 4.0, 0.6, t3e.CONTEXT)]
    cami.write_text(json.dumps({"clau": t3e.clau_dels_resultats(), "files": files}))
    assert resum.llegeix(t3e, cami).to_dict("records") == files


AMB_COST = {t3i.CANVIS, t3i.CONTEXT_CANVIS, t3k.ATURADES, t3m.XARXA, t3o.XARXES}
METODES_DEL_BANC = {t3e: t3e.CLASSIFICADORS, t3f: t3f.CLASSIFICADORS, t3h: t3h.CLASSIFICADORS, t3i: t3i.METODES,
                    t3k: t3k.METODES, t3m: t3m.METODES, t3o: t3o.METODES}


def banc_fals(modul, preferida: dict[str, tuple]) -> pd.DataFrame:
    """Les files d'un banc: cada mètode puntua 0,6 amb la seva combinació `preferida` i 0,3 amb les altres, més una
    centèsima per cada banc (`resum.moduls`), per saber de quin banc ve cada fila."""
    marca = resum.moduls().index(modul) / 100
    files = []
    for metode in METODES_DEL_BANC[modul]:
        combinacions = [(w, lam, 12) for w in ((1.0, 4.0) if metode in AMB_COST else (math.nan,)) for lam in (4.0, 32.0)]
        for p, e, (w, lam, d_min) in ((p, e, c) for p in fonts.NOMS for e in t3.QUARTS for c in combinacions):
            seva = preferida.get(metode, (1.0, 4.0, 12) if metode in AMB_COST else (4.0, 12))
            bo = (w, lam, d_min)[-len(seva):] == seva
            files.append({**fila(p, e, lam, (0.6 if bo else 0.3) + marca, metode), "w": w, "d_min": d_min})
    return pd.DataFrame(files)


def test_cada_pas_ve_del_seu_banc_amb_la_seva_tria(monkeypatch):
    """A context és a tots els bancs, però les seves files són les de la T3e; A xarxes, les de la T3o, amb la w, la λ
    i la durada mínima que hi trien els altres partits."""
    monkeypatch.setattr(fonts, "NOMS", ("s1", "s2", "s3"))
    preferides = {t3e.CONTEXT: (32.0, 12), t3o.XARXES: (4.0, 32.0, 12), t3k.ATURADES: (1.0, 32.0, 12)}
    monkeypatch.setattr(resum, "llegeix", lambda modul: banc_fals(modul, preferides))
    triats, triades = resum.resultats()
    assert sorted(triats["metode"].unique()) == sorted(resum.CLASSIFICADORS)
    assert len(triats) == len(resum.CLASSIFICADORS) * 3 * len(t3.QUARTS)            # una fila per partit i escenari
    for metode, modul in resum.PASSOS:
        assert np.allclose(triats.loc[triats["metode"] == metode, "spell_f1"], 0.6 + resum.moduls().index(modul) / 100)
    assert triades["s1"][t3e.CONTEXT] == (32.0, 12) and triades["s1"][t3o.XARXES] == (4.0, 32.0, 12)
    assert triades["s2"][t3k.ATURADES] == (1.0, 32.0, 12) and set(triades["s3"]) == set(resum.CLASSIFICADORS)


def test_els_passos_van_de_la_t3c_a_la_t3o_i_l_ultim_es_el_de_la_cadena():
    assert resum.CLASSIFICADORS[0] == "A ×1+×¼" and resum.CLASSIFICADORS[-1] == resum.NOU == t3o.XARXES
    assert set(resum.moduls()) == set(resum.FITXERS) == set(resum.ORDRES)
