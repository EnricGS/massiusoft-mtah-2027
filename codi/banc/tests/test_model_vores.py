"""El banc de la T3ae: cap peça no aprèn amb el partit que es prova (i el segon i la q de cada grup, tampoc amb els
partits del grup), les vores perfectes com a la comprovació 2, i com es compten els canvis que es mouen."""

from __future__ import annotations

import numpy as np
import pandas as pd

from banc import fonts
from banc import model_a_context as t3e
from banc import model_a_xarxa as t3m
from banc import model_vores as mvo
from banc.tests import sintetic
from cadena import vores as vo
from possessio.oficial import possession_metrics as pm

H, A, D, X = pm.H, pm.A, pm.D, pm.X
PETIT = sintetic.partit(n=600)


def del_grup(prova: str, i: int) -> dict[tuple[str, str], np.ndarray]:
    return {(nom, e): np.zeros((PETIT.n, 3)) for nom in t3e.grups(prova)[i] for e in mvo.SIS}


def test_el_segon_i_la_q_de_cada_grup_aprenen_amb_els_altres_sis(monkeypatch):
    vist = []
    monkeypatch.setattr(mvo.mp, "primer_del_grup", lambda tasca: del_grup(tasca[0], tasca[1]))
    monkeypatch.setattr(mvo.mae, "xarxes_del_grup", lambda tasca, entrena=True: del_grup(*tasca))
    monkeypatch.setattr(mvo.mp, "degradat", lambda nom, e: vist.append((nom, e)) or PETIT)
    taula = lambda p, *_: pd.DataFrame({"u": np.zeros(p.n)})  # noqa: E731
    monkeypatch.setattr(mvo.t3m, "taula_segon", taula)
    monkeypatch.setattr(mvo.t3h, "taula_segon", taula)
    una = lambda p, t: (t.iloc[:1], np.zeros(1, np.int8))  # noqa: E731
    monkeypatch.setattr(mvo.t3f, "mostres", una)
    monkeypatch.setattr(mvo.t3i, "mostres", una)
    prova = fonts.NOMS[0]
    for i in range(t3e.GRUPS):
        for mostres in (mvo.mostres_segon, mvo.mostres_q):
            vist.clear()
            x, _ = mostres(prova, i)
            noms = {nom for nom, _ in vist}
            assert noms == set(t3m.per_entrenar_el_grup(prova, i)) and len(noms) == 6
            assert not noms & {prova, *t3e.grups(prova)[i]}
            assert sorted(vist) == sorted((nom, e) for nom in noms for e in mvo.SIS) and len(x) == len(vist)


def test_les_vores_aprenen_amb_els_altres_nou(monkeypatch):
    vist = []
    monkeypatch.setattr(mvo, "segon_del_grup", lambda tasca, entrena=True: (del_grup(*tasca), np.ones(3) / 3))
    monkeypatch.setattr(mvo, "q_del_grup", lambda tasca, entrena=True: {k: v[:, 0] for k, v in del_grup(*tasca).items()})
    monkeypatch.setattr(mvo.mae, "xarxes_del_grup", lambda tasca, entrena=True: del_grup(*tasca))
    monkeypatch.setattr(mvo.mp, "degradat", lambda nom, e: vist.append((nom, e)) or PETIT)
    monkeypatch.setattr(mvo.vt, "veritat", lambda nom: PETIT.veritat)
    monkeypatch.setattr(mvo.vo, "mostres", lambda *_: (np.zeros((1, len(vo.TRETS))), np.zeros(1, np.int8)))
    prova = fonts.NOMS[3]
    x, _ = mvo.mostres_vores(prova, (4.0, 32.0, 12))
    noms = {nom for nom, _ in vist}
    assert len(noms) == 9 and prova not in noms
    assert sorted(vist) == sorted((nom, e) for nom in noms for e in mvo.SIS) and len(x) == len(vist)


def tard(veritat: np.ndarray, trams: list[tuple[int, int]], imatges: int) -> np.ndarray:
    x = veritat.copy()
    for c in vo.canvis(veritat, tuple((0, a, b - 1) for a, b in trams)):
        x[c.t:min(c.t + imatges, c.fi + 1)] = c.de
    return x


def test_les_vores_perfectes():
    p = sintetic.partit(n=3000)
    gt = p.veritat.astype(np.int8)
    trams = [(a, b + 1) for _, a, b in p.trams]
    np.testing.assert_array_equal(mvo.perfectes(tard(gt, trams, 5), gt, trams), gt)       # a 5 imatges: on toca
    lluny = tard(gt, trams, vo.RADI + 1)
    np.testing.assert_array_equal(mvo.perfectes(lluny, gt, trams), lluny)                 # a 13: no es mouen


def test_com_es_compten_els_canvis_que_es_mouen():
    trams = ((1, 0, 299),)
    toc = np.full(300, H, dtype=np.int8)
    toc[100:200], toc[200:] = A, D
    pred = toc.copy()
    pred[100:105] = H                       # H → A, 5 tard
    pred[197:200] = D                       # A → D, 3 d'hora
    pred[250:] = A                          # D → A: a la veritat no n'hi ha cap
    nova = toc.copy()
    nova[198:200] = D                       # la H → A, al lloc; la A → D, a 2 imatges, s'hi acosta
    nova[240:] = A                          # la D → A es mou, sense el de la veritat a prop
    r = mvo.comptes(pred, nova, trams, vo.de_la_veritat(toc, [(0, 300)]))
    assert r == {"canvis": 3, "moguts": 3, "amb_la_bona": 2, "distancia_abans": 8, "distancia_despres": 2,
                 "a_prop_abans": 0, "a_prop_despres": 2, "s_acosten": 2, "s_allunyen": 0}
