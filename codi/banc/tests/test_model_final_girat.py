"""El model d'A girat amb fases (C1): el que es desa és el que es llegeix, el segon s'entrena amb peces que no han vist
el partit, els paràmetres són els del banc (el decodificador de la T3ad, i la pilota morta i les fases que trien els
partits a la T3am), les medianes són dels deu partits, i `--comprova` veu si el desat és un altre."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from banc import decodificador_tocs as t3
from banc import fonts
from banc import model_a_contacte as t3h
from banc import model_a_xarxes as t3o
from banc import model_camp_girat as mcg
from banc import model_fases as mfs
from banc import model_final_girat as mfg
from banc import model_girat_fases as mgf
from banc import model_pilota_morta as mpm
from banc.tests import sintetic
from cadena import model_girat, xarxa, xarxes
from cadena import pilota_morta as pmo
from cadena import xarxa_equips as xeq
from cadena.smart_tagging import TIPUS

PILOTA_MORTA = pmo.Abans(1.0, pmo.PER_TIPUS, 1.5, 0.0)
FASES = mfs.Suma(1.0, 1.0, 0.0)
MEDIANES = {t: 2.0 + i for i, t in enumerate(TIPUS)}
COMBINACIONS = ((2.0, 16.0, 12), (4.0, 32.0, 12), (4.0, 32.0, 25))

# les mostres sintètiques són menys que un lot de la xarxa, i sklearn ho diu
pytestmark = pytest.mark.filterwarnings("ignore:Got `batch_size` less than 1 or larger than sample size")


def fila(partit: str, escenari: str, w: float, lam: float, d_min: int, spell: float, metode: str = mcg.A_GIRAT,
         veritat: str = mcg.TOC) -> dict:
    return {"partit": partit, "font": "dfl", "escenari": escenari, "metode": metode, "veritat": veritat, "w": w,
            "lam": lam, "d_min": d_min, "spell_f1": spell, "macro_f1": 0.5}


def files_t3ad(bona: tuple[float, float, int], partits=("s1", "s2")) -> pd.DataFrame:
    """Les files de la T3ad: A camp girat puntua 0,6 amb `bona` als ×¼ a la veritat de toc, i 0,3 amb les altres. A la
    veritat de sempre, a net i amb un altre mètode, guanya una altra (no compten)."""
    files = [fila(p, e, *c, 0.6 if c == bona else 0.3) for p in partits for e in t3.QUARTS for c in COMBINACIONS]
    altra = next(c for c in COMBINACIONS if c != bona)
    files += [fila(p, e, *c, 0.9 if c == altra else 0.1, veritat=mcg.SEMPRE)
              for p in partits for e in t3.QUARTS for c in COMBINACIONS]
    files += [fila(p, "net", *c, 0.9 if c == altra else 0.1) for p in partits for c in COMBINACIONS]
    files += [fila(p, e, *c, 0.9 if c == altra else 0.1, metode=mcg.A_NETEJA)
              for p in partits for e in t3.QUARTS for c in COMBINACIONS]
    return pd.DataFrame(files)


def t3am(pilota_morta: dict[str, pmo.Abans], fases: dict[str, mfs.Suma]) -> dict:
    """El que en llegeix el model: el punt que hi tria cada partit."""
    return {"triats_pilota_morta": {nom: a._asdict() for nom, a in pilota_morta.items()},
            "triats_fases": {nom: s._asdict() for nom, s in fases.items()}}


def tots(punt, partits=("s1", "s2")) -> dict:
    return {nom: punt for nom in partits}


@pytest.fixture
def banc_petit(monkeypatch, tmp_path):
    """Dos partits sintètics en lloc dels deu (i un sol escenari), uns resultats de la T3ad que trien w = 4, λ = 32 i
    durada mínima 25, els punts de la T3am, xarxes de dues passades i el model a una carpeta de prova."""
    partits = {nom: sintetic.partit(n=6000, nom=nom, llavor=i) for i, nom in enumerate(("s1", "s2"), 1)}
    monkeypatch.setattr(fonts, "NOMS", tuple(partits))
    monkeypatch.setattr(fonts, "prepara", lambda processos: None)
    monkeypatch.setattr(fonts, "partit", lambda nom: partits[nom])
    for modul in (t3h, t3o):
        monkeypatch.setattr(modul, "ENTRENAMENT", ("curts",))
    monkeypatch.setattr(mcg, "SIS", ("curts",))
    original = xarxes.entrena
    monkeypatch.setattr(xarxes, "entrena", lambda x, y: original(x, y, passades=2))
    monkeypatch.setattr(mfg, "resultats_t3ad", lambda: files_t3ad((4.0, 32.0, 25)))
    monkeypatch.setattr(mfg, "resultats_t3am", lambda: t3am(tots(PILOTA_MORTA), tots(FASES)))
    monkeypatch.setattr(mfg, "medianes", lambda: MEDIANES)
    monkeypatch.setattr(model_girat, "DIR_MODEL", tmp_path / "model-girat")
    t3h.mostres_primer.cache_clear()                     # la memòria del procés, amb els partits d'un altre test
    yield tmp_path / "model-girat"
    t3h.mostres_primer.cache_clear()


def test_desa_un_model_que_es_llegeix_i_que_es_torna_a_fer_igual(banc_petit, capsys):
    assert mfg.main(["--processos", "1"]) == 0
    entrenat = model_girat.carrega()
    assert (entrenat.w, entrenat.lam, entrenat.d_min) == (4.0, 32.0, 25)
    assert entrenat.pilota_morta == PILOTA_MORTA and tuple(entrenat.fases) == tuple(FASES)
    assert dict(entrenat.medianes) == MEDIANES and 0 < entrenat.q_prior < 1
    assert len(entrenat.xarxes) == xarxes.N and entrenat.xarxes[0].mitjana.shape == (xeq.ENTRADES,)
    assert sorted(f.name for f in banc_petit.iterdir()) == sorted([*model_girat.FITXERS, "fitxa.json"])
    fitxa = json.loads((banc_petit / "fitxa.json").read_text())
    assert fitxa["partits"] == ["s1", "s2"] and fitxa["grups"] == [["s1"], ["s2"]] and fitxa["escenaris"] == ["curts"]
    assert fitxa["clau_del_banc"] == {"T3ad": mcg.clau_dels_resultats(), "T3am": mgf.clau_dels_resultats()}
    assert fitxa["llavors_xarxes"] == list(xarxes.LLAVORS) and fitxa["entrades_xarxes"] == xeq.ENTRADES
    assert fitxa["columnes_canvis"] == fitxa["columnes_segon"][:len(fitxa["columnes_canvis"])]
    assert "px_h" in fitxa["columnes_segon"] and "dif_p" in fitxa["columnes_canvis"]
    assert "✓ Model desat" in capsys.readouterr().out
    assert mfg.main(["--comprova", "--processos", "1"]) == 0
    assert "✓ El model refet és idèntic al desat, i la fitxa també" in capsys.readouterr().out


def test_el_segon_s_entrena_amb_peces_que_no_han_vist_el_partit(banc_petit, monkeypatch):
    """Les del primer i les de les xarxes del camp girat, entrenades amb els altres partits; les del model, amb tots."""
    primers, girades = [], []
    entrena_primer, entrena_xarxes = t3h.entrena_primer, mcg.entrena_xarxes

    def primer(noms):
        primers.append(list(noms))
        return entrena_primer(noms)

    def xarxes_de(noms):
        girades.append(list(noms))
        return entrena_xarxes(noms)

    monkeypatch.setattr(t3h, "entrena_primer", primer)
    monkeypatch.setattr(mcg, "entrena_xarxes", xarxes_de)
    mostres, xs = mfg.peces(1)
    assert primers == [["s2"], ["s1"]] and girades == [["s2"], ["s1"], ["s1", "s2"]]
    assert len(xs) == xarxes.N and all(xr.mitjana.shape == (xeq.ENTRADES,) for xr in xs)
    assert sorted(mostres) == [("s1", "curts"), ("s2", "curts")]
    (x2, y2), (xc, yc) = mostres["s1", "curts"]
    assert len(x2) == len(y2) and len(xc) == len(yc) and set(np.unique(yc).tolist()) == {0, 1}


def test_el_decodificador_es_el_millor_d_a_camp_girat_als_quarts_a_la_veritat_de_toc():
    for bona in COMBINACIONS:
        assert mfg.decodificador(files_t3ad(bona)) == bona
    w, lam, d_min = mfg.decodificador(files_t3ad((4.0, 32.0, 25)))
    assert type(w) is float and type(lam) is float and type(d_min) is int


def test_el_punt_que_trien_tots_o_el_mes_triat(monkeypatch):
    monkeypatch.setattr(fonts, "NOMS", ("s1", "s2", "s3"))
    altra = pmo.Abans(2.0, pmo.FIXA, 20.0, 1.0)
    assert altra in pmo.GRAELLA
    tres = {"s1": PILOTA_MORTA._asdict(), "s2": PILOTA_MORTA._asdict(), "s3": PILOTA_MORTA._asdict()}
    assert mfg.el_de_tots(tres, pmo.GRAELLA, "la pilota morta") == PILOTA_MORTA
    assert mfg.el_de_tots({**tres, "s2": altra._asdict()}, pmo.GRAELLA, "la pilota morta") == PILOTA_MORTA
    assert mfg.el_de_tots({nom: FASES._asdict() for nom in fonts.NOMS}, mfs.GRAELLA, "les fases") == FASES


@pytest.mark.parametrize("triats, que", [
    ({"s1": PILOTA_MORTA._asdict(), "s2": pmo.Abans(2.0, pmo.FIXA, 20.0, 1.0)._asdict()}, "empatats"),
    ({"s1": PILOTA_MORTA._asdict(), "s2": pmo.Abans(3.0, pmo.FIXA, 20.0, 1.0)._asdict()}, "no és a la graella"),
    ({"s1": PILOTA_MORTA._asdict()}, "tots els partits"),
    ({"s1": PILOTA_MORTA._asdict(), "s2": PILOTA_MORTA._asdict(), "s3": PILOTA_MORTA._asdict()}, "tots els partits"),
], ids=["empatats", "fora de la graella", "en falta un", "n'hi ha un de més"])
def test_si_no_hi_ha_un_punt_clar_s_atura(monkeypatch, triats, que):
    monkeypatch.setattr(fonts, "NOMS", ("s1", "s2"))
    with pytest.raises(RuntimeError, match=que):
        mfg.el_de_tots(triats, pmo.GRAELLA, "la pilota morta")


def test_les_medianes_son_dels_deu_partits(monkeypatch):
    crides = []

    def medianes_sense(*fora):
        crides.append(fora)
        return {t: 1 for t in TIPUS}

    monkeypatch.setattr(mpm, "medianes_sense", medianes_sense)
    m = mfg.medianes()
    assert crides == [()] and m == {t: 1.0 for t in TIPUS} and all(type(v) is float for v in m.values())


def test_els_resultats_d_un_altre_codi_no_valen(tmp_path):
    ad, am = tmp_path / "model-camp-girat.json", tmp_path / "model-girat-fases.json"
    for cami, llegeix in ((ad, mfg.resultats_t3ad), (am, mfg.resultats_t3am)):
        cami.write_text(json.dumps({"clau": "una altra", "files": []}))
        with pytest.raises(RuntimeError, match="un altre codi"):
            llegeix(cami)
    ad.write_text(json.dumps({"clau": mcg.clau_dels_resultats(), "files": files_t3ad((2.0, 16.0, 12)).to_dict("records")}))
    assert mfg.decodificador(mfg.resultats_t3ad(ad)) == (2.0, 16.0, 12)
    am.write_text(json.dumps({"clau": mgf.clau_dels_resultats(), **t3am(tots(PILOTA_MORTA), tots(FASES))}))
    assert mfg.resultats_t3am(am)["triats_fases"] == {nom: FASES._asdict() for nom in ("s1", "s2")}


def test_comprova_veu_que_les_fases_han_canviat(banc_petit, monkeypatch, capsys):
    mfg.main(["--processos", "1"])
    monkeypatch.setattr(mfg, "resultats_t3am", lambda: t3am(tots(PILOTA_MORTA), tots(mfs.Suma(0.5, 1.0, 0.0))))
    assert mfg.main(["--comprova", "--processos", "1"]) == 1
    assert "la fitxa canvia" in capsys.readouterr().out


def test_comprova_veu_que_una_xarxa_ha_canviat(banc_petit, capsys):
    mfg.main(["--processos", "1"])
    cami = banc_petit / model_girat.XARXES[2]
    xr = xarxa.carrega(cami)
    xarxa.desa(xarxa.Xarxa(xr.mitjana, xr.escala, xr.pesos, (xr.biaixos[0] + 1e-9, *xr.biaixos[1:])), cami)
    assert mfg.main(["--comprova", "--processos", "1"]) == 1
    assert "les xarxes no" in capsys.readouterr().out


def test_sense_model_desat_comprova_ho_diu(banc_petit, capsys):
    assert mfg.main(["--comprova", "--processos", "1"]) == 1 and not banc_petit.exists()
    assert "✗ No hi ha cap model desat" in capsys.readouterr().out


def test_sense_resultats_del_codi_d_ara_s_atura_amb_un_missatge(banc_petit, monkeypatch, capsys):
    def d_un_altre_codi():
        raise RuntimeError("Els resultats del banc de la T3am són d'un altre codi")
    monkeypatch.setattr(mfg, "resultats_t3am", d_un_altre_codi)
    assert mfg.main(["--processos", "1"]) == 1 and not banc_petit.exists()
    assert capsys.readouterr().out.startswith("✗ Els resultats del banc de la T3am")


def test_sense_els_resultats_del_banc_ho_diu(banc_petit, monkeypatch, capsys):
    def no_hi_son():
        raise FileNotFoundError("model-camp-girat.json")
    monkeypatch.setattr(mfg, "resultats_t3ad", no_hi_son)
    assert mfg.main(["--processos", "1"]) == 1 and not banc_petit.exists()
    assert capsys.readouterr().out.startswith("✗ Els resultats del banc no hi són o no es poden llegir")


def test_un_empat_als_punts_s_atura_abans_d_entrenar(banc_petit, monkeypatch, capsys):
    altra = mfs.Suma(0.5, 1.0, 0.0)
    monkeypatch.setattr(mfg, "resultats_t3am", lambda: t3am(tots(PILOTA_MORTA), {"s1": FASES, "s2": altra}))
    monkeypatch.setattr(mfg, "fes", lambda *a, **k: pytest.fail("no havia d'entrenar res"))
    assert mfg.main(["--processos", "1"]) == 1 and not banc_petit.exists()
    out = capsys.readouterr().out
    assert out.startswith("✗ ") and "empatats" in out
