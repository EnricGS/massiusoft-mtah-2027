"""La xarxa de la T3n: la regla s'atura on toca, el partit apartat no és a la primera volta i sí a la segona, la
segona volta és la de la T3m, i dues vegades, exactament el mateix."""

from __future__ import annotations

import numpy as np
import pytest

from banc import degrada
from banc.tests import sintetic
from cadena import xarxa, xarxa_validada as xv
from possessio.oficial import possession_metrics as pm

PASSADES_PROVA = 5


def volta(corba: list[float]) -> tuple[int, int]:
    """On s'atura la primera volta amb aquesta corba del partit apartat, i les passades triades."""
    for n in range(1, len(corba) + 1):
        if xv.s_atura(corba[:n]):
            return n, xv.triades(corba[:n])
    raise AssertionError("No s'atura")


@pytest.mark.parametrize(("corba", "s_atura", "triades"), [
    ([1.0 - 0.01 * i for i in range(70)], 60, 60),                          # baixa sempre: el màxim
    ([1.0, 1.1, 1.2, 1.3, 1.4], 4, 1),                                      # puja des de la primera
    ([1.0, 0.9, 0.8, 0.82, 0.81, 0.83, 0.7], 6, 3),                         # un mínim i soroll al darrere
    ([1.0, 0.8, 0.85, 0.9, 0.79, 0.95, 0.96, 0.97, 0.5], 8, 5),             # torna a baixar a la tercera
    ([1.0, 0.8, 0.8, 0.8, 0.8, 0.7], 5, 2),                                 # igualar el mínim no és baixar
])
def test_la_regla(corba: list[float], s_atura: int, triades: int):
    assert volta(corba) == (s_atura, triades)
    assert not xv.s_atura([])


@pytest.fixture(scope="module")
def per_partit():
    """Tres «partits»: el sintètic, amb tres escenaris diferents."""
    p0 = sintetic.partit(n=3000)
    mostres = []
    for escenari in ("barreja", "curts", "llargs"):
        p = degrada.aplica(p0, escenari)
        files = np.flatnonzero(np.isin(p.veritat, (pm.H, pm.A, pm.D)))[::10]
        mostres.append(xarxa.mostres(p.tracking, p.trams, files, p.veritat[files]))
    return mostres


def test_la_primera_volta_s_atura_amb_la_regla(per_partit):
    (xa, ya), *resta = per_partit
    apartat, primera = xv.corba(np.concatenate([x for x, _ in resta]), np.concatenate([y for _, y in resta]),
                                xa.copy(), ya, maxim=PASSADES_PROVA)
    assert len(apartat) == len(primera) <= PASSADES_PROVA and np.isfinite(apartat).all()
    assert all(not xv.s_atura(apartat[:n]) for n in range(1, len(apartat)))
    assert xv.s_atura(apartat) or len(apartat) == PASSADES_PROVA


def test_l_apartat_no_apren_a_la_primera_volta_i_si_a_la_segona(per_partit, monkeypatch):
    vist = {}
    corba, entrena = xv.corba, xarxa.entrena

    def corba_espia(x, y, x_apartat, y_apartat, maxim):
        vist["primera"], vist["apartat"] = len(x), len(x_apartat)
        return corba(x, y, x_apartat, y_apartat, maxim)

    def entrena_espia(x, y, passades):
        vist["segona"] = len(x)
        return entrena(x, y, passades=passades)

    monkeypatch.setattr(xv, "corba", corba_espia)
    monkeypatch.setattr(xarxa, "entrena", entrena_espia)
    xv.entrena(per_partit, maxim=PASSADES_PROVA)
    mides = [len(x) for x, _ in per_partit]
    assert vist == {"apartat": mides[0], "primera": sum(mides[1:]), "segona": sum(mides)}


def test_la_segona_volta_es_la_de_la_t3m_i_sempre_igual(per_partit):
    xr, c = xv.entrena(per_partit, maxim=PASSADES_PROVA)
    assert c["passades"] == xv.triades(c["apartat"]) and len(c["segona"]) == c["passades"]
    t3m, _ = xarxa.entrena(np.concatenate([x for x, _ in per_partit]), np.concatenate([y for _, y in per_partit]),
                           passades=c["passades"])
    altra, c2 = xv.entrena(per_partit, maxim=PASSADES_PROVA)
    assert c2 == c
    for a, b, d in zip(xr.pesos + xr.biaixos, t3m.pesos + t3m.biaixos, altra.pesos + altra.biaixos):
        np.testing.assert_array_equal(a, b)
        np.testing.assert_array_equal(a, d)


def test_les_mostres_dels_partits_no_es_toquen(per_partit):
    abans = [x.copy() for x, _ in per_partit]
    xv.entrena(per_partit, maxim=2)
    for a, (x, _) in zip(abans, per_partit):
        np.testing.assert_array_equal(a, x)


def test_cal_un_partit_apartat_i_un_per_aprendre(per_partit):
    with pytest.raises(ValueError):
        xv.entrena(per_partit[:1])
