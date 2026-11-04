"""El detector de tocs: un canvi de cop de la pilota amb un jugador a l'abast, de l'equip del més proper, sense
passar d'una part a l'altra ni mirar on falta la pilota."""

from __future__ import annotations

import numpy as np

from cadena import tocs
from cadena.llegeix import Tracking
from possessio.oficial import possession_metrics as pm

CAMP = (100.0, 50.0)
N = 300
P = tocs.Parametres()


def tracking(pilota_m: np.ndarray, casa_m: np.ndarray, fora_m: np.ndarray) -> Tracking:
    """Les posicions en metres, amb un jugador o més per equip: (n, 2) la pilota i (n, k, 2) cada equip."""
    escala = np.array(CAMP)
    return Tracking(fotograma=np.arange(len(pilota_m)), pilota=pilota_m / escala, casa=casa_m / escala,
                    fora=fora_m / escala, nom_casa="Casa", nom_fora="Fora", casa_es_home=True, camp_m=CAMP)


def quiet(x: float, y: float, n: int = N) -> np.ndarray:
    return np.tile([x, y], (n, 1, 1)).astype(float)


def xut(des_de: int, velocitat_ms: float, origen=(20.0, 25.0), n: int = N) -> np.ndarray:
    """La pilota quieta a `origen` i, des de la imatge `des_de`, en línia recta cap a la dreta."""
    x = origen[0] + velocitat_ms / 25 * np.clip(np.arange(n) - des_de, 0, None)
    return np.column_stack([x, np.full(n, origen[1])])


def una_part(n: int = N) -> tuple[tuple[int, int, int], ...]:
    return ((1, 0, n - 1),)


def test_una_pilota_que_va_recta_no_te_cap_toc():
    pilota = np.column_stack([np.linspace(10, 90, N), np.full(N, 25.0)])
    t = tracking(pilota, quiet(50, 25.5), quiet(60, 24.5))          # passa per sota de tots dos
    assert len(tocs.detecta(t, una_part(), P).imatge) == 0


def test_un_xut_es_un_toc_de_l_equip_que_el_fa():
    t = tracking(xut(100, 15.0), quiet(19.5, 25.0), quiet(40, 40))
    trobats = tocs.detecta(t, una_part(), P)
    assert len(trobats.imatge) == 1
    assert abs(int(trobats.imatge[0]) - 100) <= 1 and trobats.equip[0] == pm.H


def test_una_recepcio_es_un_toc_de_l_equip_que_la_para():
    pilota = xut(50, 15.0)
    para = 150
    pilota[para:] = pilota[para]                                     # s'atura als peus del rival
    t = tracking(pilota, quiet(20.5, 25.0, ), quiet(*pilota[para] + [0.5, 0.0]))
    trobats = tocs.detecta(t, una_part(), P)
    a = trobats.imatge[trobats.equip == pm.A]
    assert len(a) == 1 and abs(int(a[0]) - para) <= 1


def test_un_bot_sense_ningu_a_l_abast_no_es_cap_toc():
    pilota = xut(50, 15.0)
    pilota[150:, 1] = pilota[150, 1] + 0.3 * (np.arange(N - 150))   # canvia de direcció a 20 m de tothom
    t = tracking(pilota, quiet(19.5, 25.0), quiet(90, 5))
    trobats = tocs.detecta(t, una_part(), P)
    assert not (np.abs(trobats.imatge - 150) <= P.k).any()


def test_l_equip_es_el_del_jugador_mes_proper():
    pilota = xut(100, 15.0)
    t = tracking(pilota, quiet(20.0, 26.2), quiet(20.0, 25.4))      # els dos a l'abast; el de fora, més a prop
    trobats = tocs.detecta(t, una_part(), P)
    assert len(trobats.imatge) == 1 and trobats.equip[0] == pm.A
    np.testing.assert_allclose([trobats.propi_m[0], trobats.altre_m[0]], [0.4, 1.2], atol=0.05)


def test_on_falta_la_pilota_no_es_busca_cap_toc():
    pilota = xut(100, 15.0)
    pilota[100 - 2:100 + 2] = np.nan
    t = tracking(pilota, quiet(19.5, 25.0), quiet(40, 40))
    assert len(tocs.detecta(t, una_part(), P).imatge) == 0


def test_les_finestres_no_passen_d_una_part_a_l_altra():
    pilota = xut(150, 15.0)                                          # el xut, just on comença la segona part
    t = tracking(pilota, quiet(19.5, 25.0), quiet(40, 40))
    trams = ((1, 0, 149), (2, 150, N - 1))
    assert len(tocs.detecta(t, trams, P).imatge) == 0
    assert len(tocs.detecta(t, ((1, 0, 199),), P).imatge) == 1


def test_fora_de_les_parts_no_hi_ha_tocs():
    t = tracking(xut(100, 15.0), quiet(19.5, 25.0), quiet(40, 40))
    assert len(tocs.detecta(t, ((1, 150, N - 1),), P).imatge) == 0


def test_el_tremolor_de_la_pilota_no_fa_tocs():
    rng = np.random.default_rng(3)
    pilota = np.column_stack([np.linspace(10, 90, 3000), np.full(3000, 25.0)]) + rng.normal(0, 0.1, (3000, 2))
    jugadors = pilota[:, None, :] + [0.5, 0.0]                        # un jugador l'acompanya tota l'estona
    t = tracking(pilota, jugadors, quiet(90, 5, 3000))
    assert len(tocs.detecta(t, una_part(3000), P).imatge) == 0


def test_sense_cap_jugador_vist_no_hi_ha_toc():
    t = tracking(xut(100, 15.0), np.full((N, 1, 2), np.nan), np.full((N, 1, 2), np.nan))
    assert len(tocs.detecta(t, una_part(), P).imatge) == 0


def test_cada_toc_es_un_maxim_local_i_n_hi_ha_un_per_canvi():
    pilota = xut(100, 15.0)
    torna = 160
    pilota[torna:, 0] = pilota[torna, 0] - 15.0 / 25 * (np.arange(N - torna))   # el rival la torna enrere
    fora = quiet(*pilota[torna] + [0.6, 0.0])
    t = tracking(pilota, quiet(19.5, 25.0), fora)
    trobats = tocs.detecta(t, una_part(), P)
    assert list(trobats.equip) == [pm.H, pm.A]
    assert np.all(np.diff(trobats.imatge) > P.k)
