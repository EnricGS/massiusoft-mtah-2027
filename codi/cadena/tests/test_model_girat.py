"""El model d'A girat amb fases, desat (C1): les peces que es desen són les que es llegeixen, i un model tocat, mal fet
o d'un altre codi no es fa servir."""

from __future__ import annotations

import json
import shutil
from dataclasses import replace

import lightgbm as lgb
import numpy as np
import pandas as pd
import pytest

from banc import degrada
from banc import model_a_canvis as t3i
from banc.tests import sintetic
from cadena import fases as fs
from cadena import model, model_girat, opcio_a, xarxa, xarxes
from cadena import pilota_creible as pc
from cadena import pilota_morta as pmo
from cadena import xarxa_equips as xeq
from cadena import xarxa_girada as xg
from cadena.smart_tagging import TIPUS

RONDES = 30
PILOTA_MORTA = pmo.Abans(1.0, pmo.PER_TIPUS, 1.5, 0.0)
FASES = model_girat.Fases(1.0, 1.0, 0.0)
MEDIANES = {t: 2.0 + i for i, t in enumerate(TIPUS)}

# les mostres sintètiques són menys que un lot de la xarxa, i sklearn ho diu
pytestmark = pytest.mark.filterwarnings("ignore:Got `batch_size` less than 1 or larger than sample size")


@pytest.fixture(scope="module")
def desat(tmp_path_factory):
    """Un model petit, fet amb les peces d'A girat amb fases però amb tres partits sintètics, sense grups (aquí només
    compta que es desi i es llegeixi com toca) i xarxes de dues passades."""
    partits = [degrada.aplica(sintetic.partit(n=6000, nom=f"s{i}", llavor=i), "curts") for i in (1, 2, 3)]
    veritats = [p.veritat for p in partits]
    taules = [opcio_a.senyals_del_primer(p.tracking, p.trams) for p in partits]
    x, y = model.mostres(taules, veritats, 2)
    primer = model.entrena(x, y, rondes=RONDES)
    amb_context = [opcio_a.amb_el_context(t, model.probabilitats(primer, t), p.trams) for t, p in zip(taules, partits)]
    mc = [t3i.mostres(p, a) for p, a in zip(partits, amb_context)]
    xc, yc = pd.concat([m[0] for m in mc], ignore_index=True), np.concatenate([m[1] for m in mc])
    canvis = lgb.train(t3i.PARAMS, lgb.Dataset(xc, label=yc), num_boost_round=RONDES)
    mx = []
    for k, p in enumerate(partits):
        files = np.flatnonzero(np.isin(p.veritat, model.CLASSES))[::8]
        mx.append(xg.mostres(p.tracking, p.trams, files, p.veritat[files], k))
    entrenades, _ = xarxes.entrena(np.concatenate([m[0] for m in mx]), np.concatenate([m[1] for m in mx]),
                                   passades=2)
    segon = [opcio_a.senyals_del_segon(a, p.tracking, p.trams, xg.probabilitats(entrenades, p.tracking, p.trams))
             for a, p in zip(amb_context, partits)]
    x2, _ = model.mostres(segon, veritats, 2)
    segon = model.entrena(x2, y, rondes=RONDES)
    carpeta = tmp_path_factory.mktemp("model-girat")
    fitxa = {"prior": model.prior(y).tolist(), "q_prior": float(yc.mean()), "w": 4.0, "lam": 32.0, "d_min": 25,
             "columnes_primer": list(x.columns), "columnes_canvis": list(xc.columns),
             "columnes_segon": list(x2.columns), "pilota_morta": PILOTA_MORTA._asdict(), "medianes": MEDIANES,
             "fases": FASES._asdict()}
    textos = (primer.model_to_string(), segon.model_to_string(), canvis.model_to_string())
    model_girat.desa(carpeta, textos, entrenades, fitxa)
    return carpeta, (primer, segon, canvis, entrenades), textos, fitxa


@pytest.fixture(scope="module")
def entrenat(desat):
    return model_girat.carrega(desat[0])


def copia(desat, desti):
    shutil.copytree(desat[0], desti)
    return desti


def test_les_peces_desades_son_les_que_es_llegeixen(desat, entrenat):
    primer, segon, canvis, entrenades = desat[1]
    p = sintetic.partit(n=6000, nom="prova", llavor=9)
    taula = opcio_a.senyals_del_primer(p.tracking, p.trams)
    proba = model.probabilitats(entrenat.primer, taula)
    np.testing.assert_array_equal(proba, model.probabilitats(primer, taula))
    taula = opcio_a.amb_el_context(taula, proba, p.trams)
    np.testing.assert_array_equal(opcio_a.q_de(entrenat.canvis, taula), opcio_a.q_de(canvis, taula))
    de_les_xarxes = xg.probabilitats(entrenat.xarxes, p.tracking, p.trams)
    np.testing.assert_array_equal(de_les_xarxes, xg.probabilitats(entrenades, p.tracking, p.trams))
    taula = opcio_a.senyals_del_segon(taula, p.tracking, p.trams, de_les_xarxes)
    np.testing.assert_array_equal(model.probabilitats(entrenat.segon, taula), model.probabilitats(segon, taula))
    assert (entrenat.w, entrenat.lam, entrenat.d_min) == (4.0, 32.0, 25) and 0 < entrenat.q_prior < 1
    assert entrenat.pilota_morta == PILOTA_MORTA and isinstance(entrenat.pilota_morta, pmo.Abans)
    assert entrenat.fases == FASES and dict(entrenat.medianes) == MEDIANES
    assert not entrenat.prior.flags.writeable
    with pytest.raises(TypeError):
        entrenat.medianes["banda"] = 0.0


def test_desa_nomes_els_fitxers_del_model(desat):
    assert sorted(f.name for f in desat[0].iterdir()) == sorted([*model_girat.FITXERS, "fitxa.json"])


def toca_la_fitxa(carpeta, canvi):
    cami = carpeta / "fitxa.json"
    cami.write_text(json.dumps(canvi(json.loads(cami.read_text()))))


def toca_una_xarxa(carpeta):
    xr = xarxa.carrega(carpeta / "xarxa-3.npz")
    xarxa.desa(replace(xr, pesos=(xr.pesos[0] * 1.001, *xr.pesos[1:])), carpeta / "xarxa-3.npz")


@pytest.mark.parametrize("toca", [
    lambda c: (c / "primer.txt").open("a").write("\n"),
    lambda c: (c / "segon.txt").unlink(),
    toca_una_xarxa,
    lambda c: (c / "xarxa-4.npz").unlink(),
    lambda c: (c / "fitxa.json").write_text("{"),
    lambda c: toca_la_fitxa(c, lambda f: {**f, "pilota_morta": {**f["pilota_morta"], "beta_d": 2.0}}),
    lambda c: toca_la_fitxa(c, lambda f: {**f, "medianes": {**f["medianes"], "corner": 9.0}}),
    lambda c: toca_la_fitxa(c, lambda f: {**f, "fases": {**f["fases"], "gamma": 0.5}}),
    lambda c: toca_la_fitxa(c, lambda f: {**f, "d_min": 12}),
    lambda c: toca_la_fitxa(c, lambda f: {k: v for k, v in f.items() if k != "sha256"}),
], ids=["primer", "sense segon", "una xarxa", "sense una xarxa", "fitxa trencada", "pilota morta", "medianes", "fases",
        "decodificador", "sense empremta"])
def test_un_model_tocat_no_es_fa_servir(desat, tmp_path, toca):
    carpeta = copia(desat, tmp_path / "model-girat")
    toca(carpeta)
    with pytest.raises(model_girat.ErrorDelModel):
        model_girat.carrega(carpeta)


def test_una_fitxa_o_unes_xarxes_mal_fetes_tampoc_encara_que_l_empremta_hi_quadri(desat, tmp_path):
    _, (_, _, _, entrenades), textos, fitxa = desat
    pm_, fs_ = fitxa["pilota_morta"], fitxa["fases"]
    canvis_de_la_fitxa = (
        {"pilota_morta": {**pm_, "forma": "una altra"}}, {"pilota_morta": {**pm_, "durada": -1.0}},
        {"pilota_morta": {**pm_, "beta_d": float("inf")}}, {"pilota_morta": {**pm_, "marge_s": "0"}},
        {"pilota_morta": {k: v for k, v in pm_.items() if k != "durada"}}, {"pilota_morta": [1.0, "per tipus"]},
        {"medianes": {t: 2.0 for t in TIPUS[1:]}}, {"medianes": {**MEDIANES, "una altra": 2.0}},
        {"medianes": {**MEDIANES, "banda": -1.0}}, {"medianes": {**MEDIANES, "banda": True}},
        {"fases": {**fs_, "gamma": float("inf")}}, {"fases": {**fs_, "delta": -1.0}}, {"fases": {**fs_, "marge_s": "0"}},
        {"fases": {k: v for k, v in fs_.items() if k != "delta"}}, {"fases": None},
        {"prior": [0.5, 0.5]}, {"d_min": 0}, {"d_min": 25.0}, {"q_prior": 1.5}, {"w": -1.0},
        {"columnes_segon": fitxa["columnes_segon"][::-1]})
    casos = [(textos, entrenades, {**fitxa, **canvi}) for canvi in canvis_de_la_fitxa]
    sense_equips = tuple(replace(xr, mitjana=xr.mitjana[:725], escala=xr.escala[:725],
                                 pesos=(xr.pesos[0][:725], *xr.pesos[1:])) for xr in entrenades)
    casos += [(textos, sense_equips, fitxa),                  # les d'A xarxes, que no veuen els equips sencers
              (textos, (*entrenades[:4], replace(entrenades[4], escala=-entrenades[4].escala)), fitxa)]
    for i, (t, xs, f) in enumerate(casos):
        model_girat.desa(tmp_path / str(i), t, xs, f)
        with pytest.raises(model_girat.ErrorDelModel, match="no són com han de ser"):
            model_girat.carrega(tmp_path / str(i))
    with pytest.raises(model_girat.ErrorDelModel, match="No trobo"):
        model_girat.carrega(tmp_path / "no-hi-es")
    with pytest.raises(ValueError):
        model_girat.desa(tmp_path / "quatre", textos, entrenades[:4], fitxa)


def test_un_model_d_un_altre_codi_no_es_fa_servir(desat, tmp_path, monkeypatch):
    carpeta = copia(desat, tmp_path / "model-girat")
    monkeypatch.setattr(model_girat, "clau_del_codi", lambda: "una altra")
    with pytest.raises(model_girat.ErrorDelModel, match="un altre codi"):
        model_girat.carrega(carpeta)


def opcio_a_moduls():
    from cadena import (aturades, contacte, context, control, decodifica_canvis, decodifica_tocs, senyals, tocs)
    from possessio import decodificacio
    return (senyals, control, tocs, contacte, context, aturades, decodifica_canvis, decodifica_tocs, decodificacio)


def test_la_clau_del_codi_cobreix_totes_les_peces():
    """Les de A xarxes, i també la neteja de la pilota, les xarxes del camp girat, la pilota morta i les fases."""
    assert {pc, xeq, xg, pmo, fs, xarxes, xarxa, model}.issubset(model_girat.MODULS)
    assert set(opcio_a_moduls()).issubset(model_girat.MODULS)


def test_els_missatges_no_porten_cap_dada(desat, tmp_path):
    """Un text fix, sense res del model ni de la carpeta."""
    carpeta = copia(desat, tmp_path / "un-nom-que-no-ha-de-sortir")
    (carpeta / "segon.txt").unlink()
    with pytest.raises(model_girat.ErrorDelModel) as error:
        model_girat.carrega(carpeta)
    assert "un-nom-que-no-ha-de-sortir" not in str(error.value) and "banc.model_final_girat" in str(error.value)


def test_el_model_desat_al_repositori_es_del_codi_d_ara():
    """Si canvia cap peça, cal refer el model: `python -I -m banc.model_final_girat`."""
    entrenat = model_girat.carrega()
    p = sintetic.partit(n=6000, nom="prova", llavor=9)
    taula = opcio_a.senyals_del_primer(p.tracking, p.trams)
    assert tuple(taula.columns) == entrenat.columnes_primer
    taula = opcio_a.amb_el_context(taula, np.full((p.n, 3), 1 / 3), p.trams)
    assert tuple(taula.columns) == entrenat.columnes_canvis
    taula = opcio_a.senyals_del_segon(taula, p.tracking, p.trams, np.full((p.n, 3), 1 / 3))
    assert tuple(taula.columns) == entrenat.columnes_segon
    assert len(entrenat.xarxes) == xarxes.N and entrenat.xarxes[0].mitjana.shape == (xeq.ENTRADES,)
