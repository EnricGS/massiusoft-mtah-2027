"""El Smart Tagging del partit (T3af): la lectura del fitxer SportsCode, amb els casos que no són com cal, i les
columnes del segon, que es giren amb els equips."""

from __future__ import annotations

import numpy as np
import pytest

from cadena import senyals
from cadena import smart_tagging as st
from cadena.llegeix import ErrorDeLectura
from possessio.oficial import possession_metrics as pm

H, A = pm.H, pm.A
NAN = np.nan


def instancia(inici: float, final: float, codi: str, **etiquetes: str) -> str:
    labels = "".join(f"<label><group>{g}</group><text>{t}</text></label>" for g, t in etiquetes.items())
    return f"<instance><ID>1</ID><start>{inici}</start><end>{final}</end><code>{codi}</code>{labels}</instance>"


def fitxer(tmp_path, *instancies: str):
    cami = tmp_path / st.FITXER
    cami.write_text('<?xml version="1.0" encoding="utf-8"?><file><ALL_INSTANCES>' + "".join(instancies)
                    + "</ALL_INSTANCES></file>", encoding="utf-8")
    return cami


def test_llegeix_les_pilotes_aturades(tmp_path):
    cami = fitxer(tmp_path,
                  instancia(12.48, 20.0, "SET PIECES", Team="Barcelona", Type="Corner Kick", Half="1st Half"),
                  instancia(30.0, 41.5, "BUILD UP", Team="Atletic Club"),                   # una fase: a part
                  instancia(50.0, 55.0, "set pieces", Team="ATLETIC CLUB", Type="free kick"),
                  instancia(60.0, 64.0, "SET PIECES", Team="N/A", Type="Throw-in"),
                  instancia(70.0, 74.0, "SET PIECES", Team="Barcelona", Type="Goal Kick"),
                  instancia(80.0, 84.0, "SET PIECES", Team="N/A", Type="Kick Off (Start)"),
                  instancia(90.0, 94.0, "SET PIECES", Team="Atletic Club", Type="Kick Off (After Goal)"))
    etiquetes, avisos = st.llegeix(cami)
    assert etiquetes == (st.Etiqueta(312, 500, "corner", H), st.Etiqueta(1250, 1375, "falta", A),
                         st.Etiqueta(1500, 1600, "banda", None), st.Etiqueta(1750, 1850, "porta", H),
                         st.Etiqueta(2000, 2100, "sortida", None), st.Etiqueta(2250, 2350, "sortida", A))
    assert avisos == ()


def test_el_que_no_coneix_es_deixa_amb_un_avis_fix(tmp_path):
    cami = fitxer(tmp_path,
                  instancia(10.0, 12.0, "SET PIECES", Team="Barcelona", Type="Penalty"),     # tipus desconegut
                  instancia(20.0, 22.0, "UN CODI NOU", Team="Barcelona"),                      # codi desconegut
                  instancia(30.0, 32.0, "SET PIECES", Team="Un altre", Type="Corner Kick"),    # equip desconegut
                  instancia(40.0, 42.0, "SET PIECES", Team="Barcelona"))                       # sense tipus
    etiquetes, avisos = st.llegeix(cami)
    assert etiquetes == (st.Etiqueta(750, 800, "corner", None),)
    assert avisos == (st.AVIS_TIPUS, st.AVIS_CODI, st.AVIS_EQUIP, st.AVIS_TIPUS)
    assert all("Penalty" not in a and "UN CODI NOU" not in a and "Un altre" not in a for a in avisos)


def test_si_no_hi_es_o_es_mal_fet_s_atura_amb_un_missatge_fix(tmp_path):
    with pytest.raises(ErrorDeLectura) as e:
        st.llegeix(tmp_path / st.FITXER)
    assert str(tmp_path) not in str(e.value)
    dolent = tmp_path / st.FITXER
    dolent.write_text("<file><ALL_INSTANCES><instance><start>no és un número</start>", encoding="utf-8")
    with pytest.raises(ErrorDeLectura) as e:
        st.llegeix(dolent)
    assert "número" not in str(e.value)


def test_les_columnes_a_20_s_o_menys_i_dins_de_la_part():
    n, trams = 2000, ((1, 0, 999), (2, 1000, 1999))
    etiquetes = (st.Etiqueta(500, 600, "corner", H), st.Etiqueta(700, 800, "banda", None),
                 st.Etiqueta(1010, 1050, "falta", A))
    c = st.columnes(etiquetes, n, trams)
    assert list(c.columns) == list(st.COLUMNES) and len(st.COLUMNES) == 17 and len(c) == n
    assert c.loc[400, "st_despres_s"] == 4.0 and c.loc[400, "st_despres_corner"] == 1
    assert c.loc[400, "st_despres_equip_h"] == 1 and c.loc[400, "st_despres_equip_a"] == 0
    assert c.loc[400, ["st_abans_s", "st_abans_corner", "st_abans_equip_h"]].isna().all()
    assert c.loc[500, "st_abans_s"] == 0.0 and c.loc[500, "st_despres_s"] == 8.0      # la de banda, 200 imatges
    assert c.loc[650, "st_abans_s"] == 6.0 and c.loc[650, "st_abans_corner"] == 1
    assert c.loc[750, "st_abans_banda"] == 1 and c.loc[750, ["st_abans_equip_h", "st_abans_equip_a"]].tolist() == [0, 0]
    assert c.loc[750, ["st_despres_s", "st_despres_falta"]].isna().all()       # la falta és a l'altra part
    assert c.loc[1510, "st_abans_s"] == 20.0 and np.isnan(c.loc[1511, "st_abans_s"])         # 20 s: 500 imatges
    assert c.loc[0, "st_despres_s"] == 20.0
    assert c.loc[[499, 500, 600, 601, 700, 1050], "st_dins"].tolist() == [0, 1, 1, 0, 1, 1]
    assert c.loc[999, "st_abans_s"] == (999 - 700) / 25 and np.isnan(c.loc[1000, "st_abans_s"])


def test_fora_de_les_parts_tot_es_nan_i_sense_etiquetes_nomes_dins_es_zero():
    c = st.columnes((st.Etiqueta(10, 20, "porta", H),), 100, ((1, 0, 49),))
    assert c.iloc[50:].isna().all().all()
    buit = st.columnes((), 100, ((1, 0, 99),))
    assert (buit["st_dins"] == 0).all() and buit.drop(columns="st_dins").isna().all().all()


def test_girar_els_equips_intercanvia_nomes_els_de_l_equip():
    etiquetes = (st.Etiqueta(100, 150, "corner", H), st.Etiqueta(300, 350, "falta", A))
    c = st.columnes(etiquetes, 600, ((1, 0, 599),)).astype(np.float32)
    g = senyals.intercanvia(c)
    for quan in ("abans", "despres"):
        np.testing.assert_array_equal(g[f"st_{quan}_equip_h"], c[f"st_{quan}_equip_a"])
        np.testing.assert_array_equal(g[f"st_{quan}_equip_a"], c[f"st_{quan}_equip_h"])
    altres = [k for k in c.columns if "equip" not in k]
    np.testing.assert_array_equal(g[altres].to_numpy(), c[altres].to_numpy())


def test_les_etiquetes_fora_del_partit_no_hi_son():
    c = st.columnes((st.Etiqueta(-30, -5, "falta", H), st.Etiqueta(120, 130, "falta", H)), 100, ((1, 0, 99),))
    assert c["st_abans_s"].isna().all() and c["st_despres_s"].isna().all() and (c["st_dins"] == 0).all()
