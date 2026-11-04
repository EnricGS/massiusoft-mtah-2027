"""El model de la cadena (A xarxes): el que es desa és el que la cadena accepta, el segon classificador i el de canvis
s'entrenen amb peces que no han vist el partit, els senyals són els del banc, i `--comprova` veu si el desat és un
altre."""

from __future__ import annotations

import json
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from banc import decodificador_tocs as t3
from banc import degrada, fonts, model_final
from banc import model_a_contacte as t3h
from banc import model_a_context as t3e
from banc import model_a_xarxa as t3m
from banc import model_a_xarxes as t3o
from banc.tests import sintetic
from banc.tests.test_model_a import fila
from cadena import opcio_a, xarxa, xarxes

# les mostres sintètiques són menys que un lot de la xarxa, i sklearn ho diu
pytestmark = pytest.mark.filterwarnings("ignore:Got `batch_size` less than 1 or larger than sample size")


def graella(bona: tuple[float, float, int]) -> pd.DataFrame:
    """Els resultats de la T3o: A xarxes puntua 0,6 amb la combinació `bona` i 0,3 amb les altres; A context prefereix
    λ = 1, i als escenaris ×1, A xarxes prefereix una altra combinació (no compten)."""
    combinacions = ((2.0, 16.0, 12), (4.0, 32.0, 12), (4.0, 32.0, 25))
    files = [{**fila(p, e, lam, 0.6 if (w, lam, d) == bona else 0.3, t3o.XARXES), "w": w, "d_min": d}
             for p in ("s1", "s2") for e in t3.QUARTS for w, lam, d in combinacions]
    files += [{**fila(p, e, lam, 0.9 if lam == 1.0 else 0.1, t3e.CONTEXT), "w": np.nan}
              for p in ("s1", "s2") for e in t3.QUARTS for lam in (1.0, 4.0)]
    files += [{**fila(p, "barreja", 8.0, 0.9, t3o.XARXES), "w": 1.0, "d_min": 1} for p in ("s1", "s2")]
    return pd.DataFrame(files)


@pytest.fixture
def banc_petit(monkeypatch, tmp_path):
    """Dos partits sintètics en lloc dels deu (i un sol escenari), uns resultats de la T3o que trien w = 2, λ = 16 i
    durada mínima 12, xarxes de dues passades i el model a una carpeta de prova."""
    partits = {nom: sintetic.partit(n=6000, nom=nom, llavor=i) for i, nom in enumerate(("s1", "s2"), 1)}
    vistos = []

    def partit(nom: str):
        vistos.append(nom)
        return partits[nom]

    monkeypatch.setattr(fonts, "NOMS", tuple(partits))
    monkeypatch.setattr(fonts, "prepara", lambda processos: None)
    monkeypatch.setattr(fonts, "partit", partit)
    for modul in (t3h, t3o):
        monkeypatch.setattr(modul, "ENTRENAMENT", ("curts",))
    original = xarxes.entrena
    monkeypatch.setattr(xarxes, "entrena", lambda x, y: original(x, y, passades=2))
    monkeypatch.setattr(model_final, "resultats", lambda: graella((2.0, 16.0, 12)))
    monkeypatch.setattr(opcio_a, "DIR_MODEL", tmp_path / "model-a")
    t3h.mostres_primer.cache_clear()                     # la memòria del procés, amb els partits d'un altre test
    yield tmp_path / "model-a", vistos
    t3h.mostres_primer.cache_clear()


def test_desa_un_model_que_la_cadena_accepta_i_que_es_torna_a_fer_igual(banc_petit, capsys):
    carpeta, _ = banc_petit
    assert model_final.main(["--processos", "1"]) == 0
    entrenat = opcio_a.carrega()
    assert (entrenat.w, entrenat.lam, entrenat.d_min) == (2.0, 16.0, 12)
    assert len(entrenat.xarxes) == 5 and 0 < entrenat.q_prior < 1
    assert sorted(f.name for f in carpeta.iterdir()) == sorted([*opcio_a.FITXERS, "fitxa.json"])    # cap temporal
    fitxa = json.loads((carpeta / "fitxa.json").read_text())
    assert fitxa["partits"] == ["s1", "s2"] and fitxa["clau_del_banc"] == t3o.clau_dels_resultats()
    assert fitxa["escenaris"] == ["curts"] and fitxa["grups"] == [["s1"], ["s2"]]
    assert fitxa["llavors_xarxes"] == list(xarxes.LLAVORS)
    assert fitxa["columnes_canvis"] == fitxa["columnes_segon"][:len(fitxa["columnes_canvis"])]
    assert fitxa["columnes_primer"] == fitxa["columnes_canvis"][:len(fitxa["columnes_primer"])]
    assert "px_h" in fitxa["columnes_segon"] and "dif_p" in fitxa["columnes_canvis"]
    p = sintetic.partit(n=3000, nom="prova", llavor=9)
    assert set(opcio_a.codis(p.tracking, p.trams, p.n, entrenat).tolist()) >= {0, 1}
    assert model_final.main(["--comprova", "--processos", "1"]) == 0
    assert "✓ El model refet és idèntic al desat, i la fitxa també" in capsys.readouterr().out


def test_el_segon_i_el_de_canvis_s_entrenen_amb_peces_que_no_han_vist_el_partit(banc_petit, monkeypatch):
    primers, de_les_xarxes = [], []
    entrena_primer, entrena_xarxes = t3h.entrena_primer, t3o.entrena_xarxes

    def primer(noms):
        primers.append(list(noms))
        return entrena_primer(noms)

    def xarxes_de(noms):
        de_les_xarxes.append(list(noms))
        return entrena_xarxes(noms)

    monkeypatch.setattr(t3h, "entrena_primer", primer)
    monkeypatch.setattr(t3o, "entrena_xarxes", xarxes_de)
    mostres, xs = model_final.peces(1)
    # el grup d's1 rep les d'un primer i de cinc xarxes entrenats amb s2, i al revés; les del model, amb tots dos
    assert primers == [["s2"], ["s1"]] and de_les_xarxes == [["s2"], ["s1"], ["s1", "s2"]] and len(xs) == 5
    assert sorted(mostres) == [("s1", "curts"), ("s2", "curts")]
    (x2, y2), (xc, yc) = mostres["s1", "curts"]
    assert len(x2) == len(y2) and len(xc) == len(yc) and set(np.unique(yc).tolist()) == {0, 1}


def test_els_senyals_de_la_cadena_son_els_del_banc():
    """Les taules de cada classificador, fetes amb les funcions de la cadena, són les del banc de la T3o."""
    p = degrada.aplica(sintetic.partit(n=3000), "barreja")
    rng = np.random.default_rng(1)
    primer, de_les_xarxes = rng.dirichlet((1, 1, 1), p.n), rng.dirichlet((1, 1, 1), p.n)
    taula = opcio_a.senyals_del_primer(p.tracking, p.trams)
    pd.testing.assert_frame_equal(taula, t3h.taula_primer(p))
    amb_context = opcio_a.amb_el_context(taula, primer, p.trams)
    pd.testing.assert_frame_equal(amb_context, t3h.taula_segon(p, primer))
    pd.testing.assert_frame_equal(opcio_a.senyals_del_segon(amb_context, p.tracking, p.trams, de_les_xarxes),
                                  t3m.taula_segon(p, primer, de_les_xarxes))


def test_els_grups_parteixen_els_deu_partits():
    """Tres grups, com al banc (aquí de 4, 3 i 3, perquè són els deu), i cada partit en un de sol."""
    g = model_final.grups()
    assert len(g) == 3 and sorted(len(x) for x in g) == [3, 3, 4] and sorted(sum(g, ())) == sorted(fonts.NOMS)


def test_comprova_veu_que_el_decodificador_ha_canviat(banc_petit, monkeypatch, capsys):
    model_final.main(["--processos", "1"])
    monkeypatch.setattr(model_final, "resultats", lambda: graella((4.0, 32.0, 12)))
    assert model_final.main(["--comprova", "--processos", "1"]) == 1
    assert "la fitxa canvia" in capsys.readouterr().out


def test_comprova_veu_que_una_xarxa_ha_canviat(banc_petit, capsys):
    carpeta, _ = banc_petit
    model_final.main(["--processos", "1"])
    xr = xarxa.carrega(carpeta / opcio_a.XARXES[2])
    xarxa.desa(replace(xr, biaixos=(xr.biaixos[0] + 1e-9, *xr.biaixos[1:])), carpeta / opcio_a.XARXES[2])
    assert model_final.main(["--comprova", "--processos", "1"]) == 1
    assert "les xarxes no" in capsys.readouterr().out


def test_sense_resultats_del_codi_d_ara_s_atura_amb_un_missatge(banc_petit, monkeypatch, capsys):
    def d_un_altre_codi():
        raise RuntimeError("Els resultats del banc són d'un altre codi")
    monkeypatch.setattr(model_final, "resultats", d_un_altre_codi)
    assert model_final.main(["--processos", "1"]) == 1 and not banc_petit[0].exists()
    assert capsys.readouterr().out.startswith("✗ Els resultats del banc")


def test_sense_els_resultats_del_banc_ho_diu(banc_petit, monkeypatch, capsys):
    def no_hi_son():
        raise FileNotFoundError("model-a-xarxes.json")
    monkeypatch.setattr(model_final, "resultats", no_hi_son)
    assert model_final.main(["--processos", "1"]) == 1 and not banc_petit[0].exists()
    assert capsys.readouterr().out.startswith("✗ Els resultats del banc no hi són o no es poden llegir")


def test_un_error_de_disc_en_entrenar_no_es_confon_amb_els_resultats(banc_petit, monkeypatch):
    def disc_ple(nom: str):
        raise OSError("el disc és ple")
    monkeypatch.setattr(fonts, "partit", disc_ple)
    with pytest.raises(OSError, match="el disc és ple"):
        model_final.main(["--processos", "1"])
    assert not banc_petit[0].exists()


def test_els_resultats_d_un_altre_codi_no_valen(tmp_path):
    cami = tmp_path / "model-a-xarxes.json"
    cami.write_text(json.dumps({"clau": "una altra", "files": []}))
    with pytest.raises(RuntimeError, match="un altre codi"):
        model_final.resultats(cami)
    files = graella((4.0, 32.0, 25)).replace({np.nan: None}).to_dict("records")
    cami.write_text(json.dumps({"clau": t3o.clau_dels_resultats(), "files": files}))
    assert model_final.millor(model_final.resultats(cami)) == (4.0, 32.0, 25)
