"""Els tocs dels esdeveniments: de quines accions surten, a quina imatge van i què se'n deixa fora."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from banc import tocs_reals
from banc.partit import PartitBanc
from banc.tests import sintetic
from possessio.oficial import possession_metrics as pm

POSICIONS = """<?xml version="1.0" encoding="UTF-8"?>
<PutDataRequest>
<FrameSet GameSection="firstHalf" TeamId="BALL" PersonId="DFL-OBJ-0000XT">
<Frame N="10000" T="2023-05-27T13:30:12.600+00:00" X="0" Y="0"/>
<Frame N="10001" T="2023-05-27T13:30:12.640+00:00" X="0" Y="0"/>
<Frame N="10002" T="2023-05-27T13:30:12.680+00:00" X="0" Y="0"/>
</FrameSet>
<FrameSet GameSection="firstHalf" TeamId="T1" PersonId="P1">
<Frame N="10001" T="2023-05-27T13:30:12.640+00:00" X="0" Y="0"/>
<Frame N="10003" T="2023-05-27T13:30:12.720+00:00" X="0" Y="0"/>
</FrameSet>
<FrameSet GameSection="secondHalf" TeamId="BALL" PersonId="DFL-OBJ-0000XT">
<Frame N="20000" T="2023-05-27T14:30:00.000+00:00" X="0" Y="0"/>
<Frame N="20001" T="2023-05-27T14:30:00.040+00:00" X="0" Y="0"/>
</FrameSet>
</PutDataRequest>
"""

META = """<?xml version="1.0" encoding="UTF-8"?>
<PutDataRequest><MatchInformation><Teams>
<Team TeamId="CASA" Role="home"/><Team TeamId="FORA" Role="guest"/>
</Teams></MatchInformation></PutDataRequest>
"""

EVENTS = """<?xml version="1.0" encoding="UTF-8"?>
<PutDataRequest>
<Event EventTime="2023-05-27T15:30:12.640+02:00"><KickOff Team="CASA"><Play Team="CASA" Player="a"><Pass/></Play></KickOff></Event>
<Event EventTime="2023-05-27T15:30:12.700+02:00"><TacklingGame WinnerTeam="FORA" Winner="b"/></Event>
<Event EventTime="2023-05-27T15:30:12.720+02:00"><OtherBallAction Team="FORA" Player="b"/></Event>
<Event EventTime="2023-05-27T16:30:00.040+02:00"><ShotAtGoal Team="FORA" Player="c"><ShotWide/></ShotAtGoal></Event>
<Event EventTime="2023-05-27T16:30:00.040+02:00"><Foul TeamFouler="CASA"/></Event>
<Event EventTime="2023-05-27T16:30:09.000+02:00"><BallClaiming Team="CASA" Player="d"/></Event>
</PutDataRequest>
"""


@pytest.fixture
def fitxers(tmp_path):
    for nom, text in (("pos.xml", POSICIONS), ("meta.xml", META), ("events.xml", EVENTS)):
        (tmp_path / nom).write_text(text, encoding="utf-8")
    return tmp_path


def banc_amb_parts(llargades: tuple[int, int]) -> PartitBanc:
    p = sintetic.partit(n=sum(llargades))
    return PartitBanc(nom="dfl-prova", font="dfl", tracking=p.tracking,
                      trams=((1, 0, llargades[0] - 1), (2, llargades[0], sum(llargades) - 1)),
                      veritat=p.veritat, pilota_z=p.pilota_z)


def test_cada_part_comenca_a_la_primera_imatge_de_qualsevol_persona_i_en_compta_les_imatges(fitxers):
    parts = tocs_reals.parts_de_posicions(fitxers / "pos.xml")
    assert parts["firstHalf"] == (tocs_reals.hora("2023-05-27T13:30:12.600+00:00"), 4)
    assert parts["secondHalf"] == (tocs_reals.hora("2023-05-27T14:30:00.000+00:00"), 2)


def test_nomes_les_accions_amb_pilota_i_l_equip_de_casa_es_h(fitxers):
    accions = tocs_reals.accions_dfl(fitxers / "events.xml", fitxers / "meta.xml")
    assert [e for _, e in accions] == [pm.H, pm.A, pm.A, pm.H]          # ni l'entrada ni la falta


def test_cada_accio_va_a_la_imatge_de_la_seva_part_i_les_de_fora_no_hi_son(fitxers):
    parts = tocs_reals.parts_de_posicions(fitxers / "pos.xml")
    accions = tocs_reals.accions_dfl(fitxers / "events.xml", fitxers / "meta.xml")
    r = tocs_reals.a_imatges(accions, parts, banc_amb_parts((4, 2)))
    np.testing.assert_array_equal(r.imatge, [1, 3, 5])                  # la recuperació cau fora de la segona part
    np.testing.assert_array_equal(r.equip, [pm.H, pm.A, pm.A])


def test_si_les_parts_no_quadren_amb_el_banc_s_atura(fitxers):
    parts = tocs_reals.parts_de_posicions(fitxers / "pos.xml")
    with pytest.raises(ValueError, match="no quadren"):
        tocs_reals.a_imatges([], parts, banc_amb_parts((5, 2)))


def test_a_metrica_els_inicis_i_les_recepcions_sense_els_duels_ni_els_repetits():
    events = pd.DataFrame([
        {"type": "SET PIECE", "team": "Home", "start_frame": 11, "end_frame": 11},
        {"type": "PASS", "team": "Home", "start_frame": 11, "end_frame": 20},
        {"type": "CHALLENGE", "team": "Away", "start_frame": 25, "end_frame": 25},
        {"type": "RECOVERY", "team": "Away", "start_frame": 30, "end_frame": 30},
        {"type": "BALL LOST", "team": "Away", "start_frame": 40, "end_frame": 41},
        {"type": "SHOT", "team": "Home", "start_frame": 99, "end_frame": 120},      # aquesta imatge no hi és
    ])
    frames = np.arange(10, 60)
    r = tocs_reals.de_metrica(events, frames)
    np.testing.assert_array_equal(r.imatge, [1, 10, 20, 30])
    np.testing.assert_array_equal(r.equip, [pm.H, pm.H, pm.A, pm.A])
