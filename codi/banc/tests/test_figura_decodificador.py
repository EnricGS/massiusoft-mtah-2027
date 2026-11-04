"""La figura del decodificador: els trams, el recompte de possessions i un SVG que es pot obrir sol."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import numpy as np
import pytest

from banc import figura_decodificador as fig
from possessio.oficial import possession_metrics as pm

H, A, D = pm.H, pm.A, pm.D


def test_els_trams_son_els_codis_iguals_seguits():
    assert fig.trams_de(np.array([H, H, D, A, A, A])) == [(H, 0, 1), (D, 2, 2), (A, 3, 5)]


def test_una_possessio_es_un_tram_d_h_o_d_a_i_la_d_no_compta():
    assert fig.possessions(np.array([H, H, D, H, A, D, D])) == 3
    assert fig.possessions(np.array([D, D])) == 0


def test_l_svg_es_un_fitxer_que_s_obre_sol_amb_el_titol_primer():
    codis = np.tile(np.repeat([H, D, A], fig.FINESTRA // 3), 1)
    falta = np.zeros(len(codis), dtype=bool)
    falta[100:300] = True
    q = np.linspace(0.0, 1.0, len(codis))
    files = [(titol, "1 possession", codis) for titol in ("Truth", "Frame by frame", "Decoded")]
    smart = fig.Smart(fases=((H, 1000, 1400),), pilotes=((1500, 1600),))
    text = fig.svg("dfl-prova", 1, 0, 1000, files, q, falta, (4.0, 32.0, 12), smart)
    arrel = ET.fromstring(text.encode())
    espai = "{http://www.w3.org/2000/svg}"
    assert arrel[0].tag == f"{espai}title" and arrel[1].tag == f"{espai}desc"
    franges = [r for r in arrel.iter(f"{espai}rect") if r.get("fill") in fig.COLORS.values() and r.get("class") != "st"]
    amplades = sum(float(r.get("width")) for r in franges if r.get("height") == "24")
    assert abs(amplades - 3 * (fig.DRETA - fig.X_FRANJA)) < 0.1      # cada franja omple l'amplada, sense forats
    assert "Change likely (q)" in text and any(r.get("fill-opacity") for r in arrel.iter(f"{espai}rect"))
    assert "Smart Tagging" in text and len([r for r in arrel.iter(f"{espai}rect") if r.get("class") == "st"]) == 2


def test_el_smart_tagging_es_retalla_a_la_finestra():
    escala = (fig.DRETA - fig.X_FRANJA) / fig.FINESTRA
    smart = fig.Smart(fases=((A, 900, 1099), (H, 1000 + fig.FINESTRA - 50, 1000 + fig.FINESTRA + 500),
                             (H, 0, 500)),
                      pilotes=((1200, 1209),))
    rects = fig.franja_st(smart, 1000, 0, 24)
    xs = [(float(r.split(' x="')[1].split('"')[0]), float(r.split('width="')[1].split('"')[0])) for r in rects]
    assert len(rects) == 3                                             # la fase de tot fora no hi és
    assert xs[0] == pytest.approx((fig.X_FRANJA, 100 * escala), abs=0.01)
    assert xs[1] == pytest.approx((fig.DRETA - 50 * escala, 50 * escala), abs=0.01)
    assert xs[2] == pytest.approx((fig.X_FRANJA + 200 * escala, 10 * escala), abs=0.01)
    assert f'fill="{fig.COLORS[A]}"' in rects[0] and 'fill-opacity' in rects[0]
    assert f'fill="{fig.COLORS[D]}"' in rects[2] and 'fill-opacity' not in rects[2]


def test_la_q_es_dibuixa_en_nivells_i_la_que_no_hi_arriba_no_es_dibuixa():
    q = np.array([0.0, 0.0, 0.5, 0.5, 1.0])
    rects = fig.franja_q(q, 0, 24)
    opacitats = [float(r.split('fill-opacity="')[1].split('"')[0]) for r in rects]
    assert opacitats == [0.5, 1.0]                                    # la q 0 no fa cap rectangle


def test_la_finestra_cau_dins_d_una_part(monkeypatch):
    class Partit:
        trams = ((1, 0, 9999), (2, 10000, 19999))

    monkeypatch.setattr(fig.fonts, "partit", lambda nom: Partit())
    for llavor in range(50):
        _, part, inici_part, inici = fig.tria(np.random.default_rng(llavor))
        _, primera, ultima = Partit.trams[part - 1]
        assert inici_part == primera and primera <= inici and inici + fig.FINESTRA - 1 <= ultima
