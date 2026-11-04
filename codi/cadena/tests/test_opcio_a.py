"""El model A dins de la cadena (A xarxes): les peces que es desen són les que es fan servir, un model tocat no es fa
servir, i les imatges sense tracking."""

from __future__ import annotations

import json
from dataclasses import replace

import lightgbm as lgb
import numpy as np
import pandas as pd
import pytest

from banc import degrada
from banc import model_a_canvis as t3i
from banc.tests import sintetic
from cadena import model, opcio_a, xarxa, xarxes
from possessio.oficial import possession_metrics as pm

RONDES = 30


@pytest.fixture(scope="module")
def desat(tmp_path_factory):
    """Un model petit, fet com el de `banc.model_final` però amb tres partits sintètics, sense grups (aquí només
    compta que les peces es desin i es facin servir com toca) i xarxes de dues passades."""
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
    for p in partits:
        files = np.flatnonzero(np.isin(p.veritat, model.CLASSES))[::8]
        mx.append(xarxa.mostres(p.tracking, p.trams, files, p.veritat[files]))
    entrenades, _ = xarxes.entrena(np.concatenate([m[0] for m in mx]), np.concatenate([m[1] for m in mx]),
                                   passades=2)
    segon = [opcio_a.senyals_del_segon(a, p.tracking, p.trams, xarxes.probabilitats(entrenades, p.tracking, p.trams))
             for a, p in zip(amb_context, partits)]
    x2, _ = model.mostres(segon, veritats, 2)
    segon = model.entrena(x2, y, rondes=RONDES)
    carpeta = tmp_path_factory.mktemp("model-a")
    fitxa = {"prior": model.prior(y).tolist(), "q_prior": float(yc.mean()), "w": 4.0, "lam": 32.0, "d_min": 12,
             "columnes_primer": list(x.columns), "columnes_canvis": list(xc.columns),
             "columnes_segon": list(x2.columns)}
    textos = (primer.model_to_string(), segon.model_to_string(), canvis.model_to_string())
    opcio_a.desa(carpeta, textos, entrenades, fitxa)
    return carpeta, (primer, segon, canvis, entrenades), textos, fitxa


@pytest.fixture(scope="module")
def entrenat(desat):
    return opcio_a.carrega(desat[0])


def partit_de_prova():
    return sintetic.partit(n=6000, nom="prova", llavor=9)


def test_les_peces_desades_son_les_mateixes(desat, entrenat):
    primer, segon, canvis, entrenades = desat[1]
    p = partit_de_prova()
    taula = opcio_a.senyals_del_primer(p.tracking, p.trams)
    proba = model.probabilitats(entrenat.primer, taula)
    np.testing.assert_array_equal(proba, model.probabilitats(primer, taula))
    taula = opcio_a.amb_el_context(taula, proba, p.trams)
    np.testing.assert_array_equal(opcio_a.q_de(entrenat.canvis, taula), opcio_a.q_de(canvis, taula))
    de_les_xarxes = xarxes.probabilitats(entrenat.xarxes, p.tracking, p.trams)
    np.testing.assert_array_equal(de_les_xarxes, xarxes.probabilitats(entrenades, p.tracking, p.trams))
    taula = opcio_a.senyals_del_segon(taula, p.tracking, p.trams, de_les_xarxes)
    np.testing.assert_array_equal(model.probabilitats(entrenat.segon, taula), model.probabilitats(segon, taula))
    assert (entrenat.w, entrenat.lam, entrenat.d_min) == (4.0, 32.0, 12) and 0 < entrenat.q_prior < 1


def test_la_q_es_la_del_banc(desat):
    """La mitjana de la vista directa i de la girada, com `model_a_canvis.q_de`."""
    primer, _, canvis, _ = desat[1]
    p = partit_de_prova()
    taula = opcio_a.senyals_del_primer(p.tracking, p.trams)
    taula = opcio_a.amb_el_context(taula, model.probabilitats(primer, taula), p.trams)
    np.testing.assert_array_equal(opcio_a.q_de(canvis, taula), t3i.q_de(canvis, taula))


def copia(desat, carpeta):
    carpeta.mkdir()
    for nom in (*opcio_a.FITXERS, "fitxa.json"):
        (carpeta / nom).write_bytes((desat[0] / nom).read_bytes())
    return carpeta


def toca_la_fitxa(carpeta, canvi):
    fitxa = json.loads((carpeta / "fitxa.json").read_text())
    (carpeta / "fitxa.json").write_text(json.dumps(canvi(fitxa)))


def toca_una_xarxa(carpeta):
    xr = xarxa.carrega(carpeta / "xarxa-3.npz")
    xarxa.desa(replace(xr, pesos=(xr.pesos[0] * 1.001, *xr.pesos[1:])), carpeta / "xarxa-3.npz")


@pytest.mark.parametrize("toca", [
    lambda c: (c / "primer.txt").open("a").write("\n"),
    lambda c: (c / "canvis.txt").open("a").write("\n"),
    lambda c: (c / "segon.txt").unlink(),
    toca_una_xarxa,
    lambda c: (c / "xarxa-4.npz").unlink(),
    lambda c: (c / "xarxa-1.npz").write_bytes("no és cap xarxa".encode()),
    lambda c: (c / "fitxa.json").unlink(),
    lambda c: (c / "fitxa.json").write_text("{"),
    lambda c: (c / "fitxa.json").write_text("[]"),
    lambda c: (c / "fitxa.json").write_text("[" * 100_000 + "]" * 100_000),
    lambda c: np.save(c / "xarxa-0.npy", np.zeros(3)) or (c / "xarxa-0.npy").replace(c / "xarxa-0.npz"),
    lambda c: toca_la_fitxa(c, lambda f: {**f, "lam": 0.0}),
    lambda c: toca_la_fitxa(c, lambda f: {**f, "w": 1.0}),
    lambda c: toca_la_fitxa(c, lambda f: {**f, "q_prior": 0.5}),
    lambda c: toca_la_fitxa(c, lambda f: {**f, "prior": [1 / 3] * 3}),
    lambda c: toca_la_fitxa(c, lambda f: {k: v for k, v in f.items() if k != "sha256"}),
], ids=["primer", "canvis", "sense segon", "una xarxa", "sense una xarxa", "una xarxa trencada", "sense fitxa",
        "fitxa trencada", "fitxa que no és un diccionari", "fitxa massa fonda", "una xarxa que és una matriu", "λ", "w", "q", "prior", "sense empremta"])
def test_un_model_tocat_no_es_fa_servir(desat, tmp_path, toca):
    carpeta = copia(desat, tmp_path / "model-a")
    toca(carpeta)
    with pytest.raises(opcio_a.ErrorDelModel):
        opcio_a.carrega(carpeta)


def sense_una_capa(xr: xarxa.Xarxa) -> xarxa.Xarxa:
    return replace(xr, pesos=xr.pesos[1:], biaixos=xr.biaixos[1:])


def test_una_fitxa_o_unes_xarxes_mal_fetes_tampoc_encara_que_l_empremta_hi_quadri(desat, tmp_path):
    _, (_, _, _, entrenades), textos, fitxa = desat
    canvis_de_la_fitxa = ({"prior": [0.5, 0.5]}, {"d_min": 0}, {"lam": float("inf")}, {"w": -1.0}, {"q_prior": 0.0},
                          {"q_prior": 1.5}, {"columnes_primer": fitxa["columnes_primer"][::-1]},
                          {"columnes_canvis": fitxa["columnes_canvis"][::-1]},
                          {"columnes_segon": fitxa["columnes_segon"][::-1]}, {"d_min": 12.0}, {"d_min": True},
                          {"d_min": "12"}, {"d_min": float("inf")}, {"w": "4"}, {"q_prior": True}, {"lam": 10 ** 400},
                          {"prior": "0.3"})
    casos = [(textos, entrenades, {**fitxa, **canvi}) for canvi in canvis_de_la_fitxa]
    casos += [(textos, (sense_una_capa(entrenades[0]), *entrenades[1:]), fitxa),
              (textos, (*entrenades[:4], replace(entrenades[4], escala=-entrenades[4].escala)), fitxa),
              ((textos[0], textos[1], textos[0]), entrenades, {**fitxa, "columnes_canvis": fitxa["columnes_primer"]})]
    for i, (t, xs, f) in enumerate(casos):
        opcio_a.desa(tmp_path / str(i), t, xs, f)
        with pytest.raises(opcio_a.ErrorDelModel, match="no són com han de ser"):
            opcio_a.carrega(tmp_path / str(i))
    with pytest.raises(opcio_a.ErrorDelModel):
        opcio_a.carrega(tmp_path / "no-hi-es")
    with pytest.raises(ValueError):
        opcio_a.desa(tmp_path / "quatre", textos, entrenades[:4], fitxa)


def test_un_model_d_un_altre_codi_no_es_fa_servir(desat, tmp_path, monkeypatch):
    carpeta = copia(desat, tmp_path / "model-a")
    monkeypatch.setattr(opcio_a, "clau_del_codi", lambda: "una altra")
    with pytest.raises(opcio_a.ErrorDelModel, match="un altre codi"):
        opcio_a.carrega(carpeta)


def test_el_model_desat_al_repositori_es_del_codi_d_ara():
    """Si canvien els senyals, els models o el decodificador, cal refer el model: `python -I -m banc.model_final`."""
    entrenat = opcio_a.carrega()
    p = partit_de_prova()
    taula = opcio_a.senyals_del_primer(p.tracking, p.trams)
    assert tuple(taula.columns) == entrenat.columnes_primer
    taula = opcio_a.amb_el_context(taula, np.full((p.n, 3), 1 / 3), p.trams)
    assert tuple(taula.columns) == entrenat.columnes_canvis
    taula = opcio_a.senyals_del_segon(taula, p.tracking, p.trams, np.full((p.n, 3), 1 / 3))
    assert tuple(taula.columns) == entrenat.columnes_segon
    assert not entrenat.prior.flags.writeable and len(entrenat.xarxes) == xarxes.N


@pytest.mark.parametrize("quines", ["columnes_primer", "columnes_canvis", "columnes_segon"])
def test_uns_senyals_que_no_son_els_del_model_aturen_la_cadena(entrenat, quines):
    p = partit_de_prova()
    altre = replace(entrenat, **{quines: getattr(entrenat, quines)[::-1]})
    with pytest.raises(opcio_a.ErrorDelModel):
        opcio_a.codis(p.tracking, p.trams, p.n, altre)


def amb_un_buit(t, *trossos: slice):
    buit = {c: getattr(t, c).copy() for c in ("pilota", "casa", "fora")}
    for valors in buit.values():
        for tros in trossos:
            valors[tros] = np.nan
    return replace(t, **buit)


def test_sense_tracking_el_prior_i_la_q_de_l_entrenament(entrenat, monkeypatch):
    """Enmig d'una part, les imatges sense tracking no diuen res: el prior a les probabilitats (també a les del primer
    i de les xarxes, abans de fer-ne els senyals del segon) i la q de les mostres."""
    p = partit_de_prova()
    t = amb_un_buit(p.tracking, slice(2000, 2100))
    vistes = {}
    del_segon, del_context = opcio_a.senyals_del_segon, opcio_a.amb_el_context

    def segon(amb_context, t_, trams, de_les_xarxes):
        vistes["xarxes"] = de_les_xarxes.copy()
        return del_segon(amb_context, t_, trams, de_les_xarxes)

    def context(taula, primer, trams):
        vistes["primer"] = primer.copy()
        return del_context(taula, primer, trams)

    monkeypatch.setattr(opcio_a, "senyals_del_segon", segon)
    monkeypatch.setattr(opcio_a, "amb_el_context", context)
    proba, q = opcio_a.probabilitats(t, p.trams, entrenat)
    for de_qui in (proba, vistes["primer"], vistes["xarxes"]):
        assert (de_qui[2000:2100] == entrenat.prior).all() and not (de_qui[1000:1100] == entrenat.prior).all()
    assert (q[2000:2100] == entrenat.q_prior).all() and not (q[1000:1100] == entrenat.q_prior).all()


def test_x_fora_de_les_parts_i_d_on_l_atd_encara_no_hi_es(entrenat):
    p = partit_de_prova()
    # el principi de la segona part, sense ningú, i el final
    t = amb_un_buit(p.tracking, slice(3000, 3400), slice(5800, None))
    trams = ((1, 200, 2999), (2, 3000, 5999))
    codis = opcio_a.codis(t, trams, 6500, entrenat)
    assert len(codis) == 6500 and (codis[:200] == pm.X).all() and (codis[6000:] == pm.X).all()
    assert (codis[3000:3400] == pm.D).all() and (codis[5800:6000] == pm.D).all()
    assert set(codis[200:3000].tolist()) >= {pm.H, pm.A} and set(codis[3400:5800].tolist()) >= {pm.H, pm.A}


@pytest.mark.filterwarnings("ignore:All-NaN slice")   # el sentit d'atac d'una part buida, que no es fa servir
@pytest.mark.filterwarnings("ignore:Mean of empty slice")
def test_una_part_sense_cap_tracking_es_x(entrenat):
    p = partit_de_prova()
    t = amb_un_buit(p.tracking, slice(3000, None))
    codis = opcio_a.codis(t, ((1, 200, 2999), (2, 3000, 5999)), 6000, entrenat)
    assert (codis[3000:] == pm.X).all() and {pm.H, pm.A} <= set(codis[200:3000].tolist())


def test_un_forat_enmig_no_trenca_la_possessio(entrenat, monkeypatch):
    p = partit_de_prova()
    t = p.tracking
    sencer = opcio_a.codis(t, p.trams, p.n, entrenat)
    # una possessió llarga, i un forat de tot el tracking dins seu, més llarg que la durada mínima
    vores = np.flatnonzero(np.diff(sencer)) + 1
    inicis, finals = np.r_[0, vores], np.r_[vores, p.n]
    llarga = np.argmax(np.where(sencer[inicis] != pm.D, finals - inicis, 0))
    a, b = inicis[llarga], finals[llarga]
    assert b - a > 200
    mig = (a + b) // 2
    # el model, sense res a la imatge, hi diria pilota morta: és el prior el que fa que no compti
    original = model.probabilitats

    def diu_d_al_forat(m, taula):
        proba = original(m, taula)
        proba[mig - 30:mig + 30] = (0.001, 0.001, 0.998)
        return proba

    monkeypatch.setattr(model, "probabilitats", diu_d_al_forat)
    amb_forat = opcio_a.codis(amb_un_buit(t, slice(mig - 30, mig + 30)), p.trams, p.n, entrenat)
    assert (amb_forat[mig - 30:mig + 30] == sencer[a]).all()


def test_els_equips_girats_giren_h_i_a(entrenat):
    p = partit_de_prova()
    t = p.tracking
    codis = opcio_a.codis(t, p.trams, p.n, entrenat)
    girats = opcio_a.codis(replace(t, casa=t.fora, fora=t.casa), p.trams, p.n, entrenat)
    gira = np.array([pm.A, pm.H, pm.D, pm.X])
    assert {pm.H, pm.A} <= set(codis.tolist()) and (girats == gira[codis]).mean() > 0.999


def test_les_lletres():
    np.testing.assert_array_equal(opcio_a.lletres(np.array([pm.H, pm.A, pm.D, pm.X])), ["H", "A", "D", "X"])
