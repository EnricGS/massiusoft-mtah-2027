"""L'eina que valida la pilota de l'ATD, amb un vídeo sintètic (una pilota blanca sobre verd), una homografia
coneguda i un detector fals que troba el punt més clar. Sense PyTorch ni dades del concurs."""

from __future__ import annotations

import shutil
import subprocess
import sys
import types

import numpy as np
import pytest

from cadena.llegeix import Tracking
from inspeccio.carrega import Homografia
from pilota import valida, video
from pilota.footandball import Candidats, Detector

CAMP = (105.0, 68.0)
AMPLE, ALT = 320, 180
N = 200
PAS = 25
ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="cal ffmpeg")


def matriu(ample: int = AMPLE, alt: int = ALT) -> np.ndarray:
    """De 0-1 als píxels, amb un marge de 10 px: només escala i desplaçament."""
    return np.array([[ample - 20, 0, 10], [0, alt - 20, 10], [0, 0, 1]], float)


def grava(cami, imatges: np.ndarray) -> None:
    """Un vídeo sense pèrdua (FFV1): cada píxel surt igual que entra."""
    n, alt, ample, _ = imatges.shape
    ordre = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{ample}x{alt}",
             "-r", "25", "-i", "-", "-c:v", "ffv1", "-pix_fmt", "bgr0", str(cami)]
    subprocess.run(ordre, input=imatges.tobytes(), check=True, timeout=120)


def pilota_de(n: int = N) -> np.ndarray:
    """Una pilota que va en línia recta, un píxel per imatge (en coordenades 0-1): cau sempre al centre d'un píxel."""
    u, v = 70.0 + np.arange(n), np.full(n, 90.0)
    return np.column_stack([(u - 10) / (AMPLE - 20), (v - 10) / (ALT - 20)])


def amb_la_pilota(pilota_01: np.ndarray) -> np.ndarray:
    imatges = np.zeros((len(pilota_01), ALT, AMPLE, 3), np.uint8)
    imatges[..., 1] = 120                                                # gespa
    u, v = valida.al_pixel(np.tile(matriu(), (len(pilota_01), 1, 1)), pilota_01).round().astype(int).T
    yy, xx = np.mgrid[:ALT, :AMPLE]
    for i in range(len(pilota_01)):
        imatges[i][(xx - u[i]) ** 2 + (yy - v[i]) ** 2 <= 2] = 255
    return imatges


class MesClar:
    """El detector fals: el centre dels punts blancs del tros, segur del tot."""

    def pilotes(self, imatge_bgr: np.ndarray, escala: float = 1.0) -> Candidats:
        y, x = np.nonzero(imatge_bgr.min(axis=2) == 255)
        return Candidats(x=np.array([x.mean()]), y=np.array([y.mean()]), confianca=np.array([1.0]))


def test_la_mostra_es_una_per_segon_dins_de_les_parts_i_amb_pilota():
    pilota = np.zeros((200, 2))
    pilota[50] = np.nan
    trams = ((1, 10, 60), (2, 120, 180))
    np.testing.assert_array_equal(valida.tria_mostra(pilota, trams, 25), [25, 125, 150, 175])


@ffmpeg
def test_el_video_dona_les_imatges_que_es_demanen_i_cap_mes(tmp_path):
    imatges = np.zeros((80, 16, 24, 3), np.uint8)
    imatges[...] = np.arange(80, dtype=np.uint8)[:, None, None, None] * 3     # cada imatge, el seu gris
    cami = tmp_path / "v.mkv"
    grava(cami, imatges)
    assert video.mida(cami) == (24, 16)
    donades = list(video.imatges(cami, np.array([50, 0, 25]), 25))
    assert [f for f, _ in donades] == [0, 25, 50]
    for f, imatge in donades:
        np.testing.assert_array_equal(imatge, imatges[f])
    with pytest.raises(ValueError):
        list(video.imatges(cami, np.array([10]), 25))
    with pytest.raises(RuntimeError):
        list(video.imatges(cami, np.array([100]), 25))


def test_del_camp_al_pixel_i_tornada_amb_perspectiva():
    h = np.array([[900.0, 300, 100], [0, 400, 200], [0, 0.4, 1]])
    matrius = np.tile(h, (3, 1, 1))
    punts = np.array([[0.1, 0.2], [0.5, 0.5], [0.9, 0.8]])
    px = valida.al_pixel(matrius, punts)
    np.testing.assert_allclose(valida.al_camp(matrius, px[:, None, :], np.array(CAMP))[:, 0], punts * CAMP)


def test_la_pilota_fa_al_video_la_mida_de_l_escala_mes_gran():
    camp = np.array(CAMP)
    matrius = np.tile(matriu(), (1, 1, 1))
    d = valida.diametre_px(matrius, np.array([[50.0, 30.0]]), camp)
    np.testing.assert_allclose(d, 0.22 * (AMPLE - 20) / 105)


def test_el_retall_queda_dins_de_la_imatge():
    imatge = np.arange(100 * 200 * 3, dtype=np.int64).reshape(100, 200, 3)
    tros, origen = valida.retall(imatge, np.array([5.0, 95.0]), 20)
    assert tros.shape == (40, 40, 3) and tuple(origen) == (0, 60)
    np.testing.assert_array_equal(tros, imatge[60:100, 0:40])


def mostra(atd_m: np.ndarray, cand_m: np.ndarray, confianca: np.ndarray) -> valida.Mostra:
    """Les candidates ja al camp: els píxels són els metres, perquè l'error en píxels també es pugui mirar."""
    n = len(atd_m)
    cand_px = np.concatenate([cand_m, confianca[..., None]], axis=2)
    return valida.Mostra(frame=np.arange(n) * PAS, atd_m=atd_m, atd_px=atd_m.copy(), diametre_px=np.full(n, 5.0),
                         cand_px=cand_px, cand_m=cand_m)


def test_les_mesures_i_el_cas():
    atd = np.tile([50.0, 30.0], (10, 1))
    cand = np.full((10, 2, 2), np.nan)
    conf = np.full((10, 2), np.nan)
    cand[:6, 0], conf[:6, 0] = atd[:6] + [0.3, 0], 0.95                 # coincideixen
    cand[6:8, 0], conf[6:8, 0] = atd[6:8] + [3.0, 0], 0.6               # a prop
    cand[8, 0], conf[8, 0] = atd[8] + [20.0, 0], 0.95                   # una altra, molt segura
    cand[8, 1], conf[8, 1] = atd[8] + [0.5, 0], 0.7                     # però també hi és
    cand[9, 0], conf[9, 0] = atd[9] + [0.2, 0], 0.3                     # no és segura: no es veu
    m = mostra(atd, cand, conf)
    pilota_m = np.full((N * 2, 2), np.nan)
    pilota_m[m.frame] = atd
    r = valida.mesures(m, pilota_m)
    assert r["mostra"] == 10 and r["veu"] == 0.9
    assert r["coincideix"] == pytest.approx(7 / 9) and r["una_altra"] == 0.1
    assert r["error_m_mediana"] == pytest.approx(0.3)
    assert list(valida.grups(m)) == ["coincideix"] * 6 + ["a prop"] * 2 + ["una altra", "no es veu"]
    assert valida.cas(r) == "C"
    assert valida.cas({**r, "una_altra": 0.0}) == "B"
    assert valida.cas({**r, "una_altra": 0.0, "coincideix": 0.8}) == "A"
    assert valida.cas({**r, "veu": 0.4}) == "D"
    assert valida.cas({**r, "veu": float("nan")}) == "D"


def test_el_desfasament_es_el_que_fa_quadrar_les_dues_pilotes():
    pilota_m = np.column_stack([np.arange(400) * 1.5, np.full(400, 30.0)])      # una imatge de més ja passa d'1 m
    frames = np.arange(4, 15) * PAS
    cand = pilota_m[frames + 2][:, None, :]                                     # el vídeo va dues imatges avançat
    m = valida.Mostra(frame=frames, atd_m=pilota_m[frames], atd_px=pilota_m[frames], diametre_px=np.ones(11),
                      cand_px=np.concatenate([cand, np.ones((11, 1, 1))], axis=2), cand_m=cand)
    r = valida.mesures(m, pilota_m)
    assert r["desfasament"] == 2 and r["error_per_desfasament"][2] == 0.0
    assert r["error_per_desfasament"][0] == pytest.approx(3.0)
    assert r["coincideix"] == 0.0


def test_si_el_video_no_veu_cap_pilota_el_desfasament_no_es_mesura():
    atd = np.tile([50.0, 30.0], (4, 1))
    m = mostra(atd, np.full((4, 1, 2), np.nan), np.full((4, 1), np.nan))
    r = valida.mesures(m, np.tile([50.0, 30.0], (200, 1)))
    assert r["desfasament"] is None and valida.cas(r) == "D"
    assert "El millor: **—**" in valida.informe({**r, "fora": 0, "soroll_ms": 1.0, "nivell": 0.25, "cas": "D",
                                                 "segons": 1.0}, {0.25: 1.7})


def test_el_soroll_cau_al_nivell_del_banc_mes_proper():
    nivells = {0.0: 0.001, 0.25: 1.7, 0.5: 3.3, 1.0: 6.6, 2.0: 13.3}
    assert valida.nivell(0.5, nivells) == 0.0
    assert valida.nivell(1.2, nivells) == 0.25
    assert valida.nivell(5.0, nivells) == 1.0
    assert valida.nivell(40.0, nivells) == 2.0
    assert np.isnan(valida.nivell(float("nan"), nivells))


@ffmpeg
def test_de_cap_a_peus_amb_un_video_sintetic(tmp_path, monkeypatch):
    pilota = pilota_de()
    cami = tmp_path / "v.mkv"
    grava(cami, amb_la_pilota(pilota))
    lluny = np.tile([[0.0, 0.0]], (N, 1, 1))                         # els jugadors, a la cantonada
    t = Tracking(fotograma=np.arange(N), pilota=pilota, casa=lluny, fora=lluny, nom_casa="Casa", nom_fora="Fora",
                 casa_es_home=True, camp_m=CAMP)
    h = Homografia("tactical", np.arange(N), np.tile(matriu(), (N, 1, 1)), np.zeros(N), np.ones(N, bool))
    monkeypatch.setattr(valida, "nivells_del_banc", lambda: {0.0: 0.001, 0.25: 1.7, 0.5: 3.3, 1.0: 6.6, 2.0: 13.3})
    parlat = []
    r = valida.valida(t, h, cami, MesClar(), ((1, 0, N - 1),), tmp_path / "sortida", parlat.append)
    assert r["mostra"] == 8 and r["fora"] == 0
    assert r["veu"] == 1.0 and r["coincideix"] == 1.0 and r["desfasament"] == 0
    assert r["cas"] == "A" and r["nivell"] == 0.0
    assert {p.name for p in (tmp_path / "sortida").iterdir() if not p.name.startswith(".")} == {
        "informe.md", "mostra.csv", "candidates.npz", "resultat.json"}          # cap full de retalls (D-80)
    text = (tmp_path / "sortida" / "informe.md").read_text()
    assert "## El cas: A" in text and "retalls" not in text
    assert all(not any(c.isdigit() for c in p) or p.startswith("…") for p in parlat)


def test_els_temporals_van_a_una_carpeta_que_existeix(tmp_path, monkeypatch, capsys):
    """Kloppy passa a disc els fitxers grans: la carpeta dels temporals ha d'existir quan es llegeix l'ATD."""
    vistos = []

    def localitza(dades):
        import os
        import tempfile

        vistos.append(os.path.isdir(os.environ["TMPDIR"]))
        with tempfile.SpooledTemporaryFile(max_size=1) as f:
            f.write(b"xx")                                   # passa del màxim: va a disc
        raise valida.llegeix.ErrorDeLectura("prou")

    monkeypatch.setattr(valida.llegeix, "localitza", localitza)
    monkeypatch.setattr(sys, "argv", ["valida", "--dades", str(tmp_path), "--sortida", str(tmp_path / "s"),
                                      "--permet-fora-del-volum"])
    assert valida.main() == 1
    assert vistos == [True] and capsys.readouterr().out == "✗ prou\n"
    assert [p.name for p in (tmp_path / "s").iterdir()] == []        # i en acabar, s'esborra


def test_no_escriu_fora_del_volum(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["valida", "--dades", str(tmp_path), "--sortida", str(tmp_path / "s")])
    assert valida.main() == 1
    assert capsys.readouterr().out.startswith("✗")
    assert not (tmp_path / "s").exists()


def test_els_resultats_del_banc_son_del_codi_d_ara():
    nivells = valida.nivells_del_banc()
    assert sorted(nivells) == [0.0, 0.25, 0.5, 1.0, 2.0]
    assert all(np.isfinite(list(nivells.values())))


def test_no_carrega_lightgbm():
    """LightGBM i PyTorch porten cadascun el seu OpenMP: amb LightGBM carregat abans, el detector fa caure Python."""
    codi = "import sys, pilota.valida; print(sorted({'lightgbm', 'sklearn'} & set(sys.modules)))"
    sortida = subprocess.run([sys.executable, "-I", "-c", codi], capture_output=True, text=True, check=True)
    assert sortida.stdout.strip() == "[]"


def test_el_detector_s_atura_si_lightgbm_ja_hi_es(monkeypatch):
    monkeypatch.setitem(sys.modules, "lightgbm", types.ModuleType("lightgbm"))
    monkeypatch.delitem(sys.modules, "torch", raising=False)
    with pytest.raises(RuntimeError, match="LightGBM"):
        Detector()
