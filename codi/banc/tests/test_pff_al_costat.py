"""Les mesures del pas 1 de la T3ab: els trossos i els canvis dins de cada part, i la taula de la T3l amb un partit
fet a mà."""

from __future__ import annotations

import numpy as np

from banc import pff_al_costat as pac
from banc.partit import PartitBanc
from cadena.llegeix import Tracking
from possessio.oficial import possession_metrics as pm

H, A, D, X = pm.H, pm.A, pm.D, pm.X
CAMP = (100.0, 50.0)


def test_els_trossos_i_els_canvis_no_passen_d_una_part_a_l_altra():
    v = np.array([H, H, A, A, D, H, H, A, A, X], dtype=np.int8)
    trams = ((1, 0, 5), (2, 6, 9))
    assert pac.trossos(v, trams) == [(0, 1, H), (2, 3, A), (4, 4, D), (5, 5, H), (6, 6, H), (7, 8, A), (9, 9, X)]
    assert pac.canvis(v, trams) == [2, 7]                  # de 3 a 4 hi ha la D; de 5 a 6, la part


def partit() -> PartitBanc:
    """Una part de 4 s: H fins a 2 s, on A toca la pilota (el seu jugador hi és a 0,5 m) i la té fins a 3 s; llavors
    la pilota surt del camp 0,4 s abans de la D, i s'hi queda quieta i a la vista fins al final."""
    n = 4 * pac.FPS
    pilota = np.zeros((n, 2))
    pilota[:, 0] = np.linspace(40, 60, n)
    pilota[:, 1] = 25.0
    k_sortida = 3 * pac.FPS - 10                             # 0,4 s abans de la D
    pilota[k_sortida:, 1] = 51.0                             # fora del camp
    pilota[k_sortida:] = pilota[k_sortida]                   # i quieta
    casa = np.repeat((pilota + [0.0, 0.4])[:, None, :], 2, axis=1)
    casa[:, 1] += [10.0, 0.0]
    fora = np.repeat((pilota + [0.0, 3.0])[:, None, :], 2, axis=1)
    k = 2 * pac.FPS
    fora[k - 5:, 0] = pilota[k - 5:] + [0.0, 0.5]            # el d'A arriba a la pilota 0,2 s abans del canvi
    casa[k - 5:, 0] = pilota[k - 5:] + [0.0, 2.0]
    veritat = np.full(n, H, dtype=np.int8)
    veritat[k:3 * pac.FPS] = A
    veritat[3 * pac.FPS:] = D
    escala = np.array(CAMP)
    t = Tracking(fotograma=np.arange(n), pilota=pilota / escala, casa=casa / escala, fora=fora / escala,
                 nom_casa="Casa", nom_fora="Fora", casa_es_home=True, camp_m=CAMP)
    return PartitBanc(nom="a-ma", font="pff", tracking=t, trams=((1, 0, n - 1),), veritat=veritat,
                      pilota_z=np.zeros(n))


def test_la_taula_de_la_t3l_amb_un_partit_fet_a_ma():
    p = partit()
    m = pac.mesura(p, p.veritat)
    assert m["possessions"] == 2 and m["durades"] == [2.0, 1.0] and m["D"] == pac.FPS
    assert m["canvis_vistos"] == 1 and m["canvis_proper_nou"] == 1
    assert m["moments"] == [-0.2]                             # el d'A és més a prop des de 0,2 s abans
    assert m["sortides"] == [-0.4] and m["inicis_D"] == 1
    assert m["D_amb_pilota"] == pac.FPS and max(m["D_velocitats"]) == 0.0
    a = pac.agrega([m])
    assert a["canvi_proper_nou"] == 1.0 and a["moment_a_0_2s"] == 1.0 and a["D_amb_pilota"] == 1.0
    assert a["terra_a_1m"] == 1.0                             # a terra i en joc, sempre hi ha algú a 0,4 o 0,5 m
