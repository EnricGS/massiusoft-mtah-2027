"""A girat amb fases dins de la cadena (C2): amb el model desat, cada peça fa el mateix que al banc, sense el Smart
Tagging és A camp girat, la comprovació de l'equip de les fases, i les vores i les imatges fora de les parts."""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from banc import model_a_canvis as t3i
from banc import model_a_contacte as t3h
from banc import model_a_xarxa as t3m
from banc import model_fases as mfs
from banc import model_neteja_aire as mna
from banc.tests import sintetic
from cadena import model, model_girat, senyals
from cadena import opcio_girat as og
from cadena import pilota_creible as pc
from cadena import pilota_morta as pmo
from cadena import smart_tagging_fases as stf
from cadena import xarxa_girada as xg
from cadena.fases import Fase
from cadena.smart_tagging import Etiqueta
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

H, A, D, X = pm.H, pm.A, pm.D, pm.X
ETIQUETES = (Etiqueta(2000, 2100, "corner", H), Etiqueta(4000, 4050, "banda", None), Etiqueta(5200, 5300, "porta", A))
FASES = (Fase(500, 1500, H), Fase(2500, 3500, A), Fase(3400, 3600, H))


@pytest.fixture(scope="module")
def entrenat():
    return model_girat.carrega()


@pytest.fixture(scope="module")
def partit():
    """Un partit sintètic amb la pilota vista lluny del camp en un tros, perquè la neteja hi tregui alguna cosa."""
    p = sintetic.partit(n=6000, nom="prova", llavor=9)
    pilota = p.tracking.pilota.copy()
    pilota[1000:1100] = (1.6, 0.5)
    return replace(p, tracking=replace(p.tracking, pilota=pilota))


def test_cada_peca_fa_el_que_fa_al_banc(entrenat, partit):
    """La neteja, les probabilitats del primer, la q, les xarxes del camp girat i el segon (amb les taules del banc), la
    relativa amb les pilotes aturades, les fases i la D impossible (`model_fases.relativa_amb`), i el decodificador."""
    e, trams = entrenat, partit.trams
    t, netejades = og.prepara(partit.tracking, partit.n)
    assert netejades[1000:1100].all() and netejades.sum() == 100
    np.testing.assert_array_equal(t.pilota, pc.neteja(senyals.a_reixa(partit.tracking, partit.n)).pilota)
    assert not og.sense_tracking(t).any()                    # cap imatge buida: el prior no hi té res a fer
    proba, q = og.probabilitats(t, trams, e)
    p = SimpleNamespace(tracking=t, trams=trams)              # el que miren les taules del banc d'un partit
    primer = model.probabilitats(e.primer, t3h.taula_primer(p))
    np.testing.assert_array_equal(q, t3i.q_de(e.canvis, t3h.taula_segon(p, primer)))
    de_les_xarxes = xg.probabilitats(e.xarxes, t, trams)
    np.testing.assert_array_equal(proba, model.probabilitats(e.segon, t3m.taula_segon(p, primer, de_les_xarxes)))
    r = og.relativa(proba, netejades, ETIQUETES, FASES, trams, e)
    amb_pm = mna.amb_la_d_impossible(pmo.amb_les_etiquetes(log_relativa(proba, e.prior), ETIQUETES, trams,
                                                           e.pilota_morta, dict(e.medianes)), netejades)
    del_banc = mfs.relativa_amb(amb_pm, FASES, trams, mfs.Suma(*e.fases), netejades)
    np.testing.assert_array_equal(r, del_banc)
    np.testing.assert_array_equal(og.decodifica(t, r, q, trams, e),
                                  mna.prediccio(del_banc, q, trams, (e.w, e.lam, e.d_min)))


def test_la_d_impossible_es_la_del_banc():
    rng = np.random.default_rng(3)
    r, on = rng.normal(size=(50, 3)), rng.random(50) < 0.3
    abans = r.copy()
    np.testing.assert_array_equal(og.amb_la_d_impossible(r, on), mna.amb_la_d_impossible(r, on))
    np.testing.assert_array_equal(r, abans)                  # una còpia


def test_sense_el_smart_tagging_es_a_camp_girat(entrenat, partit):
    """Sense etiquetes ni fases, la relativa és la d'A camp girat: la del segon, amb la D impossible i prou."""
    t, netejades = og.prepara(partit.tracking, partit.n)
    proba, _ = og.probabilitats(t, partit.trams, entrenat)
    np.testing.assert_array_equal(og.relativa(proba, netejades, (), (), partit.trams, entrenat),
                                  mna.amb_la_d_impossible(log_relativa(proba, entrenat.prior), netejades))


def codis_amb(fases: tuple[Fase, ...], n: int = 100) -> np.ndarray:
    out = np.full(n, D, dtype=np.int8)
    for f in fases:
        out[f.inici:f.final + 1] = f.equip
    return out


def test_l_equip_de_les_fases_quadra_si_mes_de_la_meitat_hi_coincideix():
    trams = ((1, 0, 99),)
    fases = (Fase(10, 39, H), Fase(50, 79, A))
    sense = codis_amb(fases)
    assert og.equip_quadra(sense, fases, trams)
    assert not og.equip_quadra(sense, tuple(f._replace(equip=1 - f.equip) for f in fases), trams)
    # només hi compten les imatges on el model sense el Smart Tagging dona un equip
    sense_mig = sense.copy()
    sense_mig[10:35] = D
    assert og.equip_quadra(sense_mig, fases, trams)
    # la meitat justa no n'és més de la meitat
    meitat = codis_amb((Fase(10, 24, H), Fase(25, 39, A)))
    assert not og.equip_quadra(meitat, (Fase(10, 39, H),), trams)
    # on es toquen dues fases d'equips diferents, no hi compta; i sense cap imatge per mirar, no quadra
    assert og.equip_quadra(codis_amb((Fase(10, 39, H),)), (Fase(10, 39, H), Fase(30, 60, A)), trams)
    assert not og.equip_quadra(codis_amb(()), fases, trams)
    assert not og.equip_quadra(sense, (), trams)
    assert not og.equip_quadra(sense, (Fase(10, 39, H),), ((1, 50, 99),))          # fora de les parts no hi és


def test_codis_s_atura_si_l_equip_de_les_fases_surt_girat(entrenat, partit):
    t, netejades = og.prepara(partit.tracking, partit.n)
    proba, q = og.probabilitats(t, partit.trams, entrenat)
    sense = og.decodifica(t, og.relativa(proba, netejades, (), (), partit.trams, entrenat), q, partit.trams,
                          entrenat)
    fases = tuple(Fase(int(a), int(b) - 1, int(k)) for a, b, k in pm.possession_spells(sense, [(0, partit.n)])
                  if k in (H, A) and b - a > 50)
    assert fases
    llegit = stf.Llegit(ETIQUETES, fases, ())
    codis = og.codis(partit.tracking, partit.trams, partit.n, entrenat, llegit)
    relativa = og.relativa(proba, netejades, ETIQUETES, fases, partit.trams, entrenat)
    np.testing.assert_array_equal(codis, og.decodifica(t, relativa, q, partit.trams, entrenat))
    girades = stf.Llegit(ETIQUETES, tuple(f._replace(equip=1 - f.equip) for f in fases), ())
    with pytest.raises(og.ErrorDeLesFases, match="girat"):
        og.codis(partit.tracking, partit.trams, partit.n, entrenat, girades)
    with pytest.raises(og.ErrorDeLesFases, match="cap fase"):
        og.codis(partit.tracking, partit.trams, partit.n, entrenat, stf.Llegit(ETIQUETES, (), ()))


def test_el_resultat_porta_els_codis_les_probabilitats_i_l_atd_que_ha_mirat_el_model(entrenat, partit):
    """El que necessita la revisió interna per al document: els mateixos codis que `codis`, les probabilitats del
    segon classificador i l'ATD a la reixa amb la pilota creïble."""
    t, netejades = og.prepara(partit.tracking, partit.n)
    proba, q = og.probabilitats(t, partit.trams, entrenat)
    sense = og.decodifica(t, og.relativa(proba, netejades, (), (), partit.trams, entrenat), q, partit.trams,
                          entrenat)
    fases = tuple(Fase(int(a), int(b) - 1, int(k)) for a, b, k in pm.possession_spells(sense, [(0, partit.n)])
                  if k in (H, A) and b - a > 50)
    llegit = stf.Llegit(ETIQUETES, fases, ())
    r = og.resultat(partit.tracking, partit.trams, partit.n, entrenat, llegit)
    np.testing.assert_array_equal(r.codis, og.codis(partit.tracking, partit.trams, partit.n, entrenat, llegit))
    np.testing.assert_array_equal(r.proba, proba)
    np.testing.assert_array_equal(r.t.pilota, t.pilota)
    with pytest.raises(og.ErrorDeLesFases, match="cap fase"):
        og.resultat(partit.tracking, partit.trams, partit.n, entrenat, stf.Llegit(ETIQUETES, (), ()))

def test_x_fora_de_les_parts_i_d_on_l_atd_encara_no_hi_es(entrenat):
    """Abans que l'ATD hi tingui ningú, la pilota és morta (D) i el prior a les probabilitats; fora, X."""
    p = sintetic.partit(n=3000, nom="prova", llavor=9)
    abans = np.arange(3000) < 200
    t = replace(p.tracking, pilota=np.where(abans[:, None], np.nan, p.tracking.pilota),
                casa=np.where(abans[:, None, None], np.nan, p.tracking.casa),
                fora=np.where(abans[:, None, None], np.nan, p.tracking.fora))
    trams = ((1, 100, 2899),)
    fases = (Fase(400, 900, H),)
    t_, netejades = og.prepara(t, 3000)
    proba, q = og.probabilitats(t_, trams, entrenat)
    assert (proba[100:200] == entrenat.prior).all() and (q[100:200] == entrenat.q_prior).all()
    codis = og.decodifica(t_, og.relativa(proba, netejades, (), fases, trams, entrenat), q, trams, entrenat)
    assert set(codis[:100].tolist()) == set(codis[2900:].tolist()) == {X}
    assert set(codis[100:200].tolist()) == {D} and set(codis[200:2900].tolist()) <= {H, A, D}
