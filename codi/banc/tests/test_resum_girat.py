"""El resum d'A girat amb fases per al document (C4): els passos des d'A xarxes, cadascun del seu banc, A girat amb fases
per nivell del Smart Tagging simulat, la classe més probable de cada imatge, les línies base a la veritat de toc i les
comparacions."""

from __future__ import annotations

import json
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from banc import avalua, fonts, linies_base
from banc import fases_simulades as fsm
from banc import model_a_partit as mp
from banc import model_fases as mfs
from banc import model_girat_fases as mgf
from banc import model_neteja_aire as mna
from banc import resum_girat as rg
from banc import veritat_toc as vt
from banc.tests import sintetic
from possessio.oficial import possession_metrics as pm

H, A, D, X = pm.H, pm.A, pm.D, pm.X
ESCENARIS = rg.ESCENARIS


def comparacio(nou: float, contra: float = 0.5) -> list[dict]:
    return [{"escenari": e, "contra": contra + i / 1000, "nou": nou + i / 1000, "diferencia": nou - contra,
             "baix": nou - contra - 0.01, "alt": nou - contra + 0.01, "guanya": 9, "partits": 10}
            for i, e in enumerate(ESCENARIS)]


def files_t3am(gfs: float = 0.7, gpm: float = 0.65) -> list[dict]:
    """Dos partits: A girat amb fases fa `gfs` al nivell mitjà (0,1 més al bo, 0,1 menys al dolent i 0,2 menys sense
    Smart Tagging) i A girat amb pilota morta, `gpm`; a la veritat de sempre, 0,1 menys."""
    per_nivell = {"bo": 0.1, "mitjà": 0.0, "dolent": -0.1, "cap": -0.2}
    files = []
    for partit, font in (("a", "dfl"), ("b", "metrica")):
        for i, e in enumerate(ESCENARIS):
            for metode, s in ((rg.NOU, gfs), (mgf.A_GPM, gpm)):
                for nivell, mes in per_nivell.items():
                    for veritat, menys in ((rg.TOC, 0.0), (mgf.SEMPRE, 0.1)):
                        files.append({"partit": partit, "font": font, "escenari": e, "metode": metode,
                                      "nivell": nivell, "veritat": veritat, "spell_f1": s + mes - menys + i / 1000,
                                      "macro_f1": 0.9, "possessions": 8, "possessions_reals": 10})
    return files


def desats(gfs: float = 0.7) -> dict:
    d = {modul: {"comparacio": comparacio(0.6 + k / 100)} for k, (_, modul) in enumerate(rg.PASSOS[:-2])}
    d[mgf] = {"comparacio": comparacio(gfs), "files": files_t3am(gfs)}
    return d


def test_cada_pas_ve_del_seu_banc():
    p = rg.passos(desats())
    assert list(p.index) == list(ESCENARIS) and list(p.columns) == list(rg.METODES)
    assert p.loc["net", rg.XARXES_TOC] == pytest.approx(0.5) and p.loc["aire ×¼", rg.XARXES_TOC] == pytest.approx(0.504)
    for k, (metode, _) in enumerate(rg.PASSOS[:-2]):
        assert p.loc["net", metode] == pytest.approx(0.6 + k / 100)
    assert p.loc["curts ×¼", mgf.A_GPM] == pytest.approx(0.651) and p.loc["curts ×¼", rg.NOU] == pytest.approx(0.701)


def test_els_passos_s_aturen_si_a_xarxes_no_es_el_mateix_a_tots_els_bancs():
    d = desats()
    d[rg.PASSOS[1][1]] = {"comparacio": comparacio(0.6, contra=0.4)}
    with pytest.raises(RuntimeError, match="no és el mateix a tots els bancs"):
        rg.passos(d)


def test_els_passos_s_aturen_si_les_files_d_a_girat_amb_fases_no_donen_la_seva_comparacio():
    d = desats()
    d[mgf]["comparacio"] = comparacio(0.69)
    with pytest.raises(RuntimeError, match="no donen"):
        rg.passos(d)


def test_els_passos_van_d_a_xarxes_a_a_girat_amb_fases():
    assert rg.METODES[0] == rg.XARXES_TOC and rg.METODES[-1] == rg.NOU == mgf.A_GFS
    assert [m for _, m in rg.PASSOS[-2:]] == [mgf, mgf]


def test_a_girat_amb_fases_per_nivell_a_la_veritat_de_toc():
    n = rg.per_nivell({"files": files_t3am()})
    assert list(n.columns) == list(mgf.NIVELLS) and list(n.index) == list(ESCENARIS)
    assert n.loc["net", "bo"] == pytest.approx(0.8) and n.loc["net", "cap"] == pytest.approx(0.5)
    files = rg.del_nou({"files": files_t3am()})
    assert len(files) == 2 * len(ESCENARIS) and set(files["metode"]) == {rg.NOU}
    assert files.loc[files["escenari"] == "net", "spell_f1"].tolist() == pytest.approx([0.7, 0.7])


def test_els_resultats_d_un_altre_codi_no_valen(tmp_path):
    modul = SimpleNamespace(__name__="banc.un_banc", clau_dels_resultats=lambda: "la d'ara")
    cami = tmp_path / "un-banc.json"
    cami.write_text(json.dumps({"clau": "una altra", "comparacio": []}))
    with pytest.raises(RuntimeError, match="un altre codi: torna a fer `python -I -m banc.un_banc`"):
        rg.llegeix(modul, cami)
    cami.write_text(json.dumps({"clau": "la d'ara", "comparacio": []}))
    assert rg.llegeix(modul, cami) == {"clau": "la d'ara", "comparacio": []}


def test_a_cada_imatge_es_la_classe_mes_probable_dins_de_les_parts_i_x_fora():
    r = np.array([[0.0, -1, -2], [-1, 0, -2], [-2, -1, 0], [0, -1, -2], [-1, 0, -2]])
    np.testing.assert_array_equal(rg.a_cada_imatge(r, ((1, 1, 3),)), [X, A, D, H, X])


@pytest.fixture
def partit(monkeypatch):
    """Un partit sintètic, amb la veritat de toc girada perquè no sigui la de sempre."""
    p = sintetic.partit(n=6000)
    toc = np.where(p.veritat == H, A, np.where(p.veritat == A, H, p.veritat)).astype(p.veritat.dtype)
    monkeypatch.setattr(fonts, "partit", lambda nom: p)
    monkeypatch.setattr(vt, "veritat", lambda nom: toc)
    return p, toc


def test_les_linies_base_es_puntuen_a_la_veritat_de_toc(partit):
    _, toc = partit
    files = rg.linies_base_de(("sintetic", "curts ×¼"))
    assert len(files) == len(linies_base.FINESTRES) * len(linies_base.SENSE_PILOTA)
    p = replace(mp.degradat("sintetic", "curts ×¼"), veritat=toc)
    esperat = avalua.puntua(p, linies_base.prediu(p, 125, "X"))
    fila = next(f for f in files if f["metode"] == "smooth125·X")
    assert fila["spell_f1"] == esperat["spell_f1"] and fila["escenari"] == "curts ×¼"


def test_la_classe_mes_probable_amb_la_relativa_d_a_girat_amb_fases(partit, monkeypatch):
    """La de la T3am, amb les pilotes aturades i les fases del nivell mitjà: el decodificat ha de donar la fila del
    banc, i si no, s'atura."""
    p, toc = partit
    rng = np.random.default_rng(5)
    r, q = rng.normal(size=(p.n, 3)), rng.random(p.n)
    netejades = np.zeros(p.n, dtype=bool)
    monkeypatch.setattr(mgf, "base", lambda sota, nom, escenari: (p, r, q, netejades))
    monkeypatch.setattr(mfs, "relativa_pm", lambda *_: r + 0.5)
    monkeypatch.setattr(fsm, "fases_de", lambda *_: ())
    triat, a, s = (4.0, 32.0, 12), {"beta_d": 1.0, "forma": "fixa", "durada": 10.0, "marge_s": 0.0}, \
        {"gamma": 1.0, "delta": 1.0, "marge_s": 0.0}
    pt = replace(p, veritat=toc)
    decodificat = avalua.puntua(pt, mna.prediccio(r + 0.5, q, p.trams, triat))["spell_f1"]
    fila = rg.a_cada_imatge_de(("sintetic", "curts ×¼", triat, a, s, decodificat))
    assert fila == {"partit": "sintetic", "escenari": "curts ×¼",
                    "spell_f1": avalua.puntua(pt, rg.a_cada_imatge(r + 0.5, p.trams))["spell_f1"]}
    with pytest.raises(RuntimeError, match="no dona la fila del banc"):
        rg.a_cada_imatge_de(("sintetic", "curts ×¼", triat, a, s, decodificat + 0.01))


def metodes() -> pd.DataFrame:
    """Quatre partits (tres de DFL i un de Metrica): A girat amb fases fa 0,7 (0,1 més a Metrica), smooth125·X 0,3
    (0,35 a «net») i smooth50·X 0,2."""
    files = []
    for i, partit in enumerate(("a", "b", "c", "d")):
        font = "metrica" if i == 3 else "dfl"
        for e in ESCENARIS:
            for metode, s in ((rg.NOU, 0.7 + (0.1 if font == "metrica" else 0)),
                              ("smooth125·X", 0.35 if e == "net" else 0.3), (rg.PUBLICADA, 0.2)):
                files.append({"partit": partit, "font": font, "escenari": e, "metode": metode, "spell_f1": s,
                              "macro_f1": 0.9, "possessions": 8, "possessions_reals": 10})
    return pd.DataFrame(files)


def test_el_resum_compara_amb_la_millor_linia_base_la_publicada_i_a_xarxes():
    d = desats()
    r = rg.resum(metodes(), rg.passos(d), {e: 0.25 for e in ESCENARIS}, d[mgf]["comparacio"]).set_index("escenari")
    assert list(r.index) == list(ESCENARIS)
    assert r.loc["net", "millor base"] == "smooth125·X" and r.loc["net", "spell millor base"] == 0.35
    assert r.loc["aire ×¼", "diferencia millor base"] == pytest.approx(0.425)
    assert r.loc["aire ×¼", "guanya publicada"] == 4 and r.loc["aire ×¼", "spell sense decodificar"] == 0.25
    assert r.loc["net", "spell metrica"] == pytest.approx(0.8) and r.loc["net", "possessions per real"] == 0.8
    assert r.loc["net", f"diferencia {rg.XARXES_TOC}"] == pytest.approx(0.2)
    assert r.loc["net", f"spell {rg.NOU}"] == pytest.approx(0.7)


def test_l_informe_porta_totes_les_taules():
    d = desats()
    r = rg.resum(metodes(), rg.passos(d), {e: 0.25 for e in ESCENARIS}, d[mgf]["comparacio"])
    triats = {"decodificador": {"a": [4.0, 32.0, 12], "b": [4.0, 64.0, 12]},
              "pilota_morta": {n: {"beta_d": 1.0, "forma": "per tipus", "durada": 1.5, "marge_s": 0.0} for n in "ab"},
              "fases": {n: {"gamma": 1.0, "delta": 1.0, "marge_s": 0.0} for n in "ab"}}
    text = rg.markdown(r, rg.per_nivell({"files": files_t3am()}), triats)
    for titol in ("## spellF1 de cada pas", f"## {rg.NOU} contra la millor línia base",
                  f"## {rg.NOU} contra {rg.PUBLICADA}", f"## {rg.NOU} contra {rg.XARXES_TOC}",
                  "## Per nivell del Smart Tagging simulat", f"## {rg.NOU}, per font, i les possessions"):
        assert titol in text
    assert "w = 4, λ = 32 i durada mínima 12 en 1 partits; w = 4, λ = 64 i durada mínima 12 en 1 partits" in text
    assert "nan" not in text


def test_amb_resultats_d_un_altre_codi_s_atura(monkeypatch, capsys):
    def d_un_altre_codi():
        raise RuntimeError("Els resultats del banc són d'un altre codi")
    monkeypatch.setattr(rg, "desats_de_tots", d_un_altre_codi)
    assert rg.main([]) == 1
    assert capsys.readouterr().out.startswith("✗ Els resultats del banc són d'un altre codi")


def test_sense_els_resultats_d_un_banc_ho_diu(monkeypatch, capsys):
    def no_hi_son():
        raise FileNotFoundError("model-camp-girat.json")
    monkeypatch.setattr(rg, "desats_de_tots", no_hi_son)
    assert rg.main([]) == 1
    assert capsys.readouterr().out.startswith("✗ Els resultats d'algun banc dels passos no hi són")
