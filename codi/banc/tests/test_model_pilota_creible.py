"""El banc de la T3w: la regla dels passos que només van a un escenari, les comprovacions (l'entrenament no canvia, i
on la neteja no canvia res, les peces surten iguals que a la memòria cau) i la taula de la D d'aire ×¼."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from banc import la_d_a_aire as lda
from banc import model_pilota_creible as mpc

AIRE = mpc.AIRE
SOROLL = mpc.t3.SOROLL


def comparacio(**canvis: tuple[float, float]) -> pd.DataFrame:
    """Una comparació amb la diferència i el límit de baix de l'interval: 0 a tot arreu, i a aire ×¼ hi guanya, tret
    del que es diu (amb el nom de l'escenari sense espais ni ×)."""
    noms = {e.replace(" ×¼", "_q").replace(" ", "_"): e for e in mpc.ESCENARIS}
    files = {e: (0.0, 0.0) for e in mpc.ESCENARIS} | {AIRE: (0.01, 0.002)}
    files |= {noms[k]: v for k, v in canvis.items()}
    return pd.DataFrame([{"escenari": e, "diferencia": d, "baix": b} for e, (d, b) in files.items()])


def test_la_regla_dels_passos_d_un_sol_escenari():
    assert mpc.millor_d_un_escenari(comparacio(), AIRE) == {"escenari": True, "quarts": True, "altres": True}
    assert not mpc.millor_d_un_escenari(comparacio(aire_q=(0.01, -0.001)), AIRE)["escenari"]
    assert not mpc.millor_d_un_escenari(comparacio(aire_q=(0.0, 0.0)), AIRE)["escenari"]
    assert not mpc.millor_d_un_escenari(comparacio(curts_q=(-1e-6, -0.001)), AIRE)["quarts"]
    assert not mpc.millor_d_un_escenari(comparacio(partit_q=(-1e-6, -0.001)), AIRE)["quarts"]
    assert mpc.millor_d_un_escenari(comparacio(aire=(-SOROLL + 0.001, -0.05)), AIRE)["altres"]
    assert not mpc.millor_d_un_escenari(comparacio(soroll2=(-SOROLL - 0.001, -0.05)), AIRE)["altres"]


def test_la_regla_vol_tots_els_escenaris_i_un_dels_quatre_quarts():
    with pytest.raises(ValueError):
        mpc.millor_d_un_escenari(comparacio().iloc[1:], AIRE)
    with pytest.raises(ValueError):
        mpc.millor_d_un_escenari(comparacio(), "aire")


def canvis(partit: str = "a", escenari: str = "aire", n: int = 3) -> pd.DataFrame:
    return pd.DataFrame([{"partit": p, "font": "dfl", "escenari": e, "vistes": 100,
                          "canvien": n if (p, e) == (partit, escenari) else 0}
                         for p in ("a", "b") for e in mpc.ESCENARIS])


def test_l_entrenament_no_pot_canviar():
    mpc.comprova_l_entrenament(canvis())
    with pytest.raises(RuntimeError, match="barreja ×¼"):
        mpc.comprova_l_entrenament(canvis(escenari="barreja ×¼"))


def test_els_escenaris_on_la_neteja_no_canvia_res():
    assert mpc.sense_canvis(canvis(), "a") == [e for e in mpc.ESCENARIS if e != "aire"]
    assert mpc.sense_canvis(canvis(), "b") == list(mpc.ESCENARIS)


def test_on_no_canvia_res_la_peca_ha_de_sortir_igual():
    desat = {"net": np.array([[0.1, 0.9], [np.nan, np.nan]], np.float32), "aire": np.array([[0.3, 0.7]], np.float32)}
    nou = {"net": desat["net"].copy(), "aire": np.array([[0.4, 0.6]], np.float32)}
    mpc.comprova_igual("el primer", "a", nou, desat, ["net"])
    with pytest.raises(RuntimeError, match="aire"):
        mpc.comprova_igual("el primer", "a", nou, desat, ["net", "aire"])
    nou["net"][0, 0] = np.float32(0.1) + np.float32(1e-7)
    with pytest.raises(RuntimeError, match="net"):
        mpc.comprova_igual("el primer", "a", nou, desat, ["net"])


def test_la_taula_de_la_d():
    lluny, dins = lda.DISTANCIES[2][2], lda.DISTANCIES[0][2]
    files = []
    for metode, d_lluny in ((mpc.A_EQUIPS, 40), (mpc.A_CREIBLE, 5)):
        files += [{"metode": metode, "on": lda.AL_FORAT, "veritat": lda.D_UN_EQUIP, "distancia": lluny, "n": 100,
                   "d": d_lluny},
                  {"metode": metode, "on": lda.ES_VEU, "veritat": lda.D_UN_EQUIP, "distancia": dins, "n": 300, "d": 3},
                  {"metode": metode, "on": lda.AL_FORAT, "veritat": lda.LA_D, "distancia": lluny, "n": 50, "d": 40}]
    t = mpc.taula_la_d(pd.DataFrame(files))
    assert list(t.index) == [(lda.ES_VEU, dins), (lda.AL_FORAT, lluny), (mpc.TOTES, "")]
    assert t.loc[(lda.AL_FORAT, lluny)].tolist() == [0.25, 0.4, 0.05]
    assert t.loc[(lda.ES_VEU, dins)].tolist() == [0.75, 0.01, 0.01]
    np.testing.assert_allclose(t.loc[(mpc.TOTES, "")].tolist(), [1.0, 43 / 400, 8 / 400])
