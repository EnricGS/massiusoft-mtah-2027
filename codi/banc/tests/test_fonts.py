"""Els partits del banc: les parts, la veritat de DFL i de Metrica, i la memòria cau."""

from __future__ import annotations

import numpy as np
import pytest

from banc import dfl, fonts, metrica, partit
from banc.partit import PartitBanc, trams_de_parts
from cadena.llegeix import Tracking
from possessio import config
from possessio.oficial import possession_metrics as pm

HI_HA_DFL = (fonts.DIR_IDSSE / "README.md").exists()
HI_HA_METRICA = config.DIR_DADES.exists()


def petit(n=10, nom="prova") -> PartitBanc:
    rng = np.random.default_rng(0)
    t = Tracking(fotograma=np.arange(n), pilota=rng.random((n, 2)), casa=rng.random((n, 3, 2)),
                 fora=rng.random((n, 2, 2)), nom_casa="Casa", nom_fora="Fora", casa_es_home=True,
                 camp_m=(105.0, 68.0))
    return PartitBanc(nom=nom, font="dfl", tracking=t, trams=((1, 0, 5), (2, 6, n - 1)),
                      veritat=np.array([pm.H, pm.A, pm.D, pm.X, pm.H] * (n // 5), np.int8),
                      pilota_z=np.full(n, np.nan))


def test_les_parts_surten_del_periode():
    assert trams_de_parts(np.array([1, 1, 1, 2, 2])) == ((1, 0, 2), (2, 3, 4))
    with pytest.raises(ValueError):
        trams_de_parts(np.array([1, 1, 2, 1]))


def test_la_veritat_de_dfl():
    estat = np.array(["alive", "alive", "dead", "dead", "alive"])
    propietari = np.array(["c", "f", "c", "f", "nan"])
    assert dfl.veritat(estat, propietari, "c", "f").tolist() == [pm.H, pm.A, pm.D, pm.D, pm.X]


def test_la_memoria_cau_torna_el_mateix(tmp_path):
    p = petit()
    partit.desa(p, tmp_path / "p.npz")
    q = partit.carrega(tmp_path / "p.npz")
    assert (q.nom, q.font, q.trams, q.tracking.camp_m) == (p.nom, p.font, p.trams, p.tracking.camp_m)
    assert np.array_equal(q.veritat, p.veritat)
    np.testing.assert_allclose(q.tracking.casa, p.tracking.casa, rtol=1e-6)
    assert not list(tmp_path.glob("*.part*"))


def test_una_memoria_cau_d_una_altra_versio_no_val(tmp_path, monkeypatch):
    partit.desa(petit(), tmp_path / "p.npz")
    monkeypatch.setattr(partit, "VERSIO", partit.VERSIO + 1)
    assert partit.carrega(tmp_path / "p.npz") is None


def test_no_desa_un_partit_que_no_quadra(tmp_path):
    p = petit()
    dolent = PartitBanc(nom=p.nom, font=p.font, tracking=p.tracking, trams=((1, 0, 5),), veritat=p.veritat,
                        pilota_z=p.pilota_z)
    with pytest.raises(ValueError):
        partit.desa(dolent, tmp_path / "p.npz")


@pytest.mark.skipif(not HI_HA_DFL, reason="falten les dades de DFL (codi/banc/baixa_idsse.py)")
def test_un_partit_de_dfl():
    p = dfl.llegeix(fonts.DIR_IDSSE, "J03WPY", limit=3000)
    partit.valida(p)
    t = p.tracking
    assert p.n == 3000 and p.trams == ((1, 0, 2999),) and t.camp_m == (105.0, 68.0)
    # kloppy només fa columnes per als que surten a les imatges llegides: els onze del començament
    assert t.casa.shape[1:] == (11, 2) == t.fora.shape[1:] and np.nanmax(t.pilota) <= 1.05
    assert {pm.H, pm.A, pm.D} <= set(np.unique(p.veritat).tolist())
    assert np.isfinite(p.pilota_z).all()


@pytest.mark.skipif(not HI_HA_METRICA, reason="falten les dades de mostra de Metrica")
def test_un_partit_de_metrica():
    p = metrica.llegeix(1)
    partit.valida(p)
    assert [part for part, _, _ in p.trams] == [1, 2]
    assert set(np.unique(p.veritat).tolist()) == {pm.H, pm.A, pm.D}
    assert np.nanmax(p.tracking.casa) <= 1.2 and np.isnan(p.pilota_z).all()


def test_no_conec_un_partit_de_fora_de_la_llista():
    with pytest.raises(KeyError):
        fonts.llegeix_de_la_font("dfl-XXXXXX")
