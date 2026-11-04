"""Proves de les peces de l'informe, sense dades del concurs."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

import subprocess

from inspeccio import besso, carrega, etiquetatge, informe, video
from inspeccio.esperat import Esperat
from inspeccio.homografia import diametre_pilota
from inspeccio.seccio import Seccio, comprova_aprop, executa, xifra
from inspeccio.temps import part_de, puntuats, rellotge, tirades


def test_tirades_troba_inici_i_fi_de_cada_tram():
    inicis, fins = tirades(np.array([0, 1, 1, 0, 1, 0, 0, 1], bool))
    assert inicis.tolist() == [1, 4, 7]
    assert fins.tolist() == [3, 5, 8]


def test_tirades_buida_quan_no_hi_ha_cap_true():
    inicis, fins = tirades(np.zeros(5, bool))
    assert len(inicis) == len(fins) == 0


def test_puntuats_inclou_els_dos_extrems():
    mascara = puntuats(np.arange(12), ((1, 2, 4), (2, 8, 9)))
    assert np.flatnonzero(mascara).tolist() == [2, 3, 4, 8, 9]
    assert part_de(9, ((1, 2, 4), (2, 8, 9))) == 2
    assert part_de(6, ((1, 2, 4), (2, 8, 9))) is None


def test_rellotge_en_hores_minuts_i_segons():
    assert rellotge(11185, 25) == "0:07:27"
    assert rellotge(25 * 3725, 25) == "1:02:05"


@pytest.mark.parametrize("valor, text", [
    (199319, "199.319"), (56.9, "56,9"), (0.24, "0,24"), (25.0, "25"),
    ((105.0, 68.0), "105 × 68"), (True, "sí"), ("text", "text"),
])
def test_xifra_a_la_catalana(valor, text):
    assert xifra(valor) == text


def test_la_matriu_del_besso_porta_les_cantonades_on_toca():
    h = besso.matriu(besso.CANTONADES_CAMP, besso.CANTONADES_IMATGE)
    x, y = np.array([[c[0] for c in besso.CANTONADES_CAMP]]), np.array([[c[1] for c in besso.CANTONADES_CAMP]])
    u, v = carrega.projecta(h[None], x, y)
    assert np.allclose(np.stack([u[0], v[0]], 1), besso.CANTONADES_IMATGE, atol=1e-6)


def test_diametre_de_la_pilota_amb_una_escala_coneguda():
    # 1 unitat del camp = 1000 px en x i en y: 22 cm són 220/105 px a l'ample i 220/68 a l'alt.
    n = 50
    esperat = Esperat(rangs_puntuats=((1, 0, n - 1),), camp_m=(105.0, 68.0))
    matrius = np.tile(np.diag([1000.0, 1000.0, 1.0]), (n, 1, 1))
    h = carrega.Homografia("tactical", np.arange(n), matrius, np.zeros(n), np.ones(n, bool))
    t = carrega.Tracking("tactical", np.arange(1, n + 1), np.full((n, 2), 0.5), None, ("A", "B"),
                         ("home", "away"), ((), ()), (np.empty((n, 0, 2)), np.empty((n, 0, 2))),
                         (105.0, 68.0), 25.0, None)
    diametres, _ = diametre_pilota(h, t, esperat)
    assert np.allclose(diametres, max(220 / 105, 220 / 68))


def test_la_homografia_torna_nan_on_no_hi_ha_fotograma():
    h = carrega.Homografia("tactical", np.array([0, 1, 3]), np.ones((3, 3, 3)), np.zeros(3), np.ones(3, bool))
    matrius = h.de_frames(np.array([1, 2, 3]))
    assert np.isnan(matrius[1]).all() and not np.isnan(matrius[[0, 2]]).any()


def test_llegeix_el_smart_tagging(tmp_path):
    cami = tmp_path / "st.xml"
    besso.etiquetatge(cami, 10_000)
    df = etiquetatge.instancies(cami)
    assert len(df) == len(besso.INSTANCIES)
    assert set(etiquetatge.columna(df, "team")) == {"Barcelona", "Atletic Club", "N/A"}
    assert (df["fi_s"] > df["inici_s"]).all()


def test_l_html_escapa_el_que_ve_de_les_dades():
    s = Seccio("Prova")
    s.text("fitxer `<script>alert(1)</script>.mp4` i **negreta**")
    s.taula("t", ("a",), [("<img src=x onerror=alert(1)>",)])
    text = informe.html_de([s], Path("/x"), {})
    assert "<script>" not in text and "<img src=x" not in text
    assert "<code>&lt;script&gt;" in text and "<strong>negreta</strong>" in text


def test_una_seccio_que_falla_no_atura_l_informe():
    s = executa("Falla", lambda seccio: 1 / 0)
    assert "ZeroDivisionError" in s.error


def test_una_comprovacio_amb_un_bool_de_numpy_compta_com_a_diferencia():
    s = Seccio("Prova")
    s.comprovacions([comprova_aprop("pilota", 56.9, np.float64(100.0), 0.05)])
    assert s.diferencies == 1


def test_comprova_aprop_accepta_la_tolerancia_justa():
    # 0,25 − 0,24 fa 0,010000000000000009 en coma flotant
    assert comprova_aprop("error", 0.24, 0.25, 0.01).ok is True
    assert comprova_aprop("error", 0.24, 0.26, 0.01).ok is False


def info_ffprobe(**canvis) -> dict:
    return {"width": 1920, "height": 1080, "r_frame_rate": "25/1", "avg_frame_rate": "25/1",
            "nb_read_packets": "199319", "start_time": "0.000000", "format": {"start_time": "0.000000"},
            **canvis}


def que_falla(info: dict, font: str) -> set[str]:
    return {c.que for c in video.comprovacions(info, font, Esperat()) if c.ok is False}


def test_fps_constants_compara_valors_i_no_textos():
    assert que_falla(info_ffprobe(avg_frame_rate="199319000/7972760"), "tactical") == set()
    assert "fps constants (`r_frame_rate` = `avg_frame_rate`)" in que_falla(
        info_ffprobe(avg_frame_rate="24/1"), "tactical")


def test_els_fotogrames_del_broadcast_no_es_comparen_amb_l_atd():
    # DATA.md dona 164.488 registres de l'ATD broadcast, però del vídeo només diu «its own timeline»
    assert que_falla(info_ffprobe(nb_read_packets="170000"), "broadcast") == set()
    assert "fotogrames (paquets llegits)" in que_falla(info_ffprobe(nb_read_packets="199318"), "tactical")


def test_on_comenca_el_flux_s_informa_sense_comptar_com_a_diferencia():
    info = info_ffprobe(start_time="0.080000")
    assert que_falla(info, "tactical") == set()
    assert any(c.ok is None and "comença" in c.que for c in video.comprovacions(info, "tactical", Esperat()))


def test_projecta_zero_files():
    u, v = carrega.projecta(np.empty((0, 3, 3)), np.empty((0, 4)), np.empty((0, 4)))
    assert u.shape == v.shape == (0, 4)


def test_el_smart_tagging_tolera_temps_buits_i_comes(tmp_path):
    cami = tmp_path / "st.xml"
    cami.write_text("<file><ALL_INSTANCES>"
                    "<instance><ID>1</ID><start>12,5</start><end>20</end><code>BUILD UP</code></instance>"
                    "<instance><ID>2</ID><start>30</start><end/><code>SET PIECES</code></instance>"
                    "</ALL_INSTANCES></file>")
    df = etiquetatge.instancies(cami)
    assert df["inici_s"].iloc[0] == 12.5
    assert len(etiquetatge.amb_temps(df)) == 1
    assert etiquetatge.coberta(df, np.arange(600), Esperat()).sum() == 500 - 312 + 1


def video_numerat(cami: Path, desfas_video_s: float = 0.0) -> None:
    """50 fotogrames on la lluminància diu quin és (16 + 4 × n); amb `desfas_video_s`, el vídeo comença més
    tard que l'àudio."""
    font = "color=black:s=64x64:r=25:d=2,geq=lum='16+4*N':cb=128:cr=128"
    ordre = [video.eina("ffmpeg"), "-v", "error", "-y", "-f", "lavfi", "-i", font]
    if desfas_video_s:
        ordre = [video.eina("ffmpeg"), "-v", "error", "-y", "-itsoffset", str(desfas_video_s), "-f", "lavfi",
                 "-i", font, "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", "2.5", "-c:a", "aac"]
    subprocess.run([*ordre, "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv420p", str(cami)], check=True)


@pytest.mark.parametrize("desfas", [0.0, 0.08])
def test_ffmpeg_dona_el_fotograma_demanat(tmp_path, desfas):
    cami = tmp_path / "v.mp4"
    video_numerat(cami, desfas)
    info = video.ffprobe(cami)
    for frame in (0, 1, 25, 48):
        imatge = video.fotograma(cami, frame, 25, video.desfasament(info))
        # En passar a RGB, el vermell val 255/219 × (Y − 16) = 255/219 × 4n.
        assert abs(float(imatge[..., 0].mean()) * 219 / 4 - frame) < 0.3
