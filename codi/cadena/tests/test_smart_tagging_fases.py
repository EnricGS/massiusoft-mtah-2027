"""El Smart Tagging a la cadena (C2): les fases amb equip, amb el seu avís, les pilotes aturades de sempre, i on és el
fitxer."""

from __future__ import annotations

import pytest

from cadena import fases as fs
from cadena import smart_tagging as st
from cadena import smart_tagging_fases as stf
from cadena.llegeix import ErrorDeLectura
from cadena.tests.test_smart_tagging import fitxer, instancia
from possessio.oficial import possession_metrics as pm

H, A = pm.H, pm.A


def test_llegeix_les_fases_amb_l_equip(tmp_path):
    """Les sis que diuen l'equip que té la pilota (`fases.CODIS`); les de defensar i les altres, no. Sense equip
    (N/A), no hi van, i sense avís: DATA.md diu que n'hi ha."""
    cami = fitxer(tmp_path,
                  instancia(30.0, 41.5, "BUILD UP", Team="Atletic Club", Half="1st Half"),
                  instancia(50.0, 55.0, "progression", Team="BARCELONA"),
                  instancia(60.0, 64.0, "CREATING CHANCES", Team="Barcelona"),
                  instancia(70.0, 74.0, "BALL IN FINAL THIRD", Team="Atletic Club"),
                  instancia(80.0, 84.0, "BALL IN THE BOX", Team="N/A"),                    # sense equip
                  instancia(90.0, 94.0, "ATTACKING TRANSITION", Team="Barcelona"),
                  instancia(95.0, 99.0, "DEFENDING IN MIDDLE THIRD", Team="Barcelona"),    # de defensar: no
                  instancia(100.0, 104.0, "PLAYERS IN THE BOX", Team="Barcelona"),         # no és una fase
                  instancia(110.0, 114.0, "BALL IN THE BOX"),                              # sense cap equip
                  instancia(120.0, 124.0, "SET PIECES", Team="Barcelona", Type="Corner Kick"))
    etiquetes, fases, avisos = stf.llegeix(cami)
    assert fases == (fs.Fase(750, 1038, A), fs.Fase(1250, 1375, H), fs.Fase(1500, 1600, H), fs.Fase(1750, 1850, A),
                     fs.Fase(2250, 2350, H))
    assert etiquetes == (st.Etiqueta(3000, 3100, "corner", H),) and avisos == ()
    assert {c.lower() for c in ("BUILD UP", "PROGRESSION", "CREATING CHANCES", "BALL IN FINAL THIRD", "BALL IN THE BOX",
                                "ATTACKING TRANSITION")} == set(fs.CODIS) <= st.CODIS


def test_una_fase_d_un_equip_que_no_coneix_es_deixa_amb_un_avis_fix(tmp_path):
    cami = fitxer(tmp_path, instancia(10.0, 12.0, "BUILD UP", Team="Un altre"),
                  instancia(20.0, 22.0, "PROGRESSION", Team="Barcelona"))
    _, fases, avisos = stf.llegeix(cami)
    assert fases == (fs.Fase(500, 550, H),) and avisos == (stf.AVIS_EQUIP_FASE,)
    assert "Un altre" not in stf.AVIS_EQUIP_FASE and not any(c.isdigit() for c in stf.AVIS_EQUIP_FASE)


def test_troba_el_fitxer_pel_nom_de_data_md(tmp_path):
    (tmp_path / "data" / "tactical").mkdir(parents=True)
    cami = fitxer(tmp_path / "data" / "tactical")
    assert stf.localitza(tmp_path) == cami
    with pytest.raises(ErrorDeLectura, match="No trobo el Smart Tagging") as e:
        stf.localitza(tmp_path / "data" / "broadcast")
    assert str(tmp_path) not in str(e.value)
    (tmp_path / "copia").mkdir()
    fitxer(tmp_path / "copia")
    with pytest.raises(ErrorDeLectura, match="més d'un"):
        stf.localitza(tmp_path)


def test_les_pilotes_aturades_i_els_seus_avisos_son_els_de_sempre(tmp_path):
    cami = fitxer(tmp_path, instancia(10.0, 12.0, "SET PIECES", Team="Barcelona", Type="Penalty"),
                  instancia(20.0, 22.0, "BUILD UP", Team="Un altre"),
                  instancia(30.0, 32.0, "SET PIECES", Team="Barcelona", Type="Corner Kick"))
    etiquetes, avisos = st.llegeix(cami)
    assert stf.llegeix(cami) == stf.Llegit(etiquetes, (), (*avisos, stf.AVIS_EQUIP_FASE))


@pytest.mark.parametrize("contingut", [None, "<file><ALL_INSTANCES><instance><start>no és un número</start>"])
def test_si_no_hi_es_o_es_mal_fet_s_atura_amb_un_missatge_fix(tmp_path, contingut):
    cami = tmp_path / st.FITXER
    if contingut is not None:
        cami.write_text(contingut, encoding="utf-8")
    for llegeix in (stf.llegeix, stf.fases):
        with pytest.raises(ErrorDeLectura) as e:
            llegeix(cami)
        assert str(tmp_path) not in str(e.value) and "número" not in str(e.value)
