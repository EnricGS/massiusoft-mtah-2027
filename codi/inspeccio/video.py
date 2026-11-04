"""Els vídeos: què diu ffprobe, i captures del tàctic amb el tracking a sobre.

Les captures serveixen per mirar amb els ulls si, quan l'ATD perd la pilota, al
vídeo encara es veu (enfocament B). Els fotogrames passen per memòria: ffmpeg
els dona per una canonada i no se'n desa cap a disc fora de l'informe.
"""

from __future__ import annotations

import io
import json
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from inspeccio import grafic
from inspeccio.atd import grup_de_durada
from inspeccio.carrega import Homografia, Tracking, projecta
from inspeccio.esperat import CAPTURES_PER_GRUP, Esperat
from inspeccio.seccio import Comprovacio, Seccio, comprova_igual, xifra
from inspeccio.temps import part_de, puntuats, rellotge

RETALL_PX = 180      # mig costat del retall al voltant de la pilota
DPI_CAPTURA = 160    # més que les gràfiques: la pilota pot fer pocs píxels
TOLERANCIA_FPS = 0.01


def eina(nom: str) -> str:
    cami = shutil.which(nom) or f"/opt/homebrew/bin/{nom}"
    if not Path(cami).exists():
        raise FileNotFoundError(f"No trobo {nom}: cal instal·lar ffmpeg")
    return cami


def ffprobe(video: Path) -> dict:
    ordre = [eina("ffprobe"), "-v", "error", "-select_streams", "v:0", "-count_packets",
             "-show_streams", "-show_format", "-print_format", "json", str(video)]
    sortida = subprocess.run(ordre, capture_output=True, text=True, check=True, timeout=1800)
    dades = json.loads(sortida.stdout)
    return {**dades["streams"][0], "format": dades.get("format", {})}


def taula_ffprobe(info: dict) -> list[tuple]:
    claus = ("codec_name", "profile", "width", "height", "pix_fmt", "r_frame_rate", "avg_frame_rate",
             "nb_frames", "nb_read_packets", "duration", "start_time", "bit_rate", "color_space",
             "color_transfer", "color_primaries", "field_order")
    files = [(f"`{k}`", str(info[k])) for k in claus if k in info]
    formats = info.get("format", {})
    files += [(f"`format.{k}`", str(formats[k]))
              for k in ("format_name", "duration", "start_time", "size") if k in formats]
    return files


def fps_de(info: dict) -> float:
    try:
        return float(Fraction(info.get("r_frame_rate", "0/1")))
    except (ValueError, ZeroDivisionError):
        return float("nan")


def desfasament(info: dict) -> float:
    """Segons entre l'inici del contenidor i el del flux de vídeo (ffmpeg compta `-ss` des del contenidor)."""
    try:
        return float(info.get("start_time") or 0) - float(info.get("format", {}).get("start_time") or 0)
    except ValueError:
        return float("nan")


def fps_constants(info: dict) -> bool:
    """El mateix valor pot venir escrit diferent (`25/1` i `199319000/7972760`)."""
    try:
        mitjana = float(Fraction(info.get("avg_frame_rate", "0/1")))
    except (ValueError, ZeroDivisionError):
        return False
    return abs(mitjana - fps_de(info)) < TOLERANCIA_FPS


def comprovacions(info: dict, font: str, esperat: Esperat) -> list:
    """Contra DATA.md. El que DATA.md no diu surt a la taula, però no compta com a diferència."""
    fotogrames = int(info.get("nb_read_packets") or info.get("nb_frames") or 0)
    llista = [comprova_igual("fotogrames per segon", esperat.fps, fps_de(info)),
              comprova_igual("fps constants (`r_frame_rate` = `avg_frame_rate`)", True, fps_constants(info)),
              Comprovacio("on comença el flux de vídeo respecte del contenidor (les captures ho compensen)",
                          "no ho diu", f"{xifra(round(desfasament(info), 3))} s", None)]
    if font == "tactical":
        return [comprova_igual("mida", f"{esperat.amplada_px}×{esperat.alcada_px}",
                               f"{info['width']}×{info['height']}"),
                comprova_igual("fotogrames (paquets llegits)", esperat.fotogrames[font], fotogrames),
                *llista]
    return [Comprovacio("fotogrames (paquets llegits)", "no ho diu: té la seva línia de temps",
                        xifra(fotogrames), None), *llista]


def fotograma(video: Path, frame: int, fps: float, desfas_s: float = 0.0) -> np.ndarray:
    """El fotograma `frame` (començant per 0), descodificat per ffmpeg.

    `desfas_s`: on comença el flux de vídeo respecte del contenidor (vegeu `desfasament`).
    """
    segons = max(0.0, (frame - 0.25) / fps + desfas_s)
    ordre = [eina("ffmpeg"), "-v", "error", "-ss", f"{segons:.4f}", "-i", str(video), "-frames:v", "1",
             "-f", "image2pipe", "-vcodec", "png", "-"]
    sortida = subprocess.run(ordre, capture_output=True, check=True, timeout=120)
    return plt.imread(io.BytesIO(sortida.stdout), format="png")


def tria_captures(t: Tracking, forats: pd.DataFrame, esperat: Esperat, maxim: int) -> list[dict]:
    """Uns quants fotogrames amb pilota i el mig d'uns quants forats de cada grup de durada."""
    dins = puntuats(t.frame_video, esperat.rangs_puntuats) & (t.frame_video < maxim)
    amb_pilota = np.flatnonzero(dins & ~np.isnan(t.pilota[:, 0]))
    captures = [{"fila": int(f), "forat": None} for f in amb_pilota[np.linspace(
        0, len(amb_pilota) - 1, CAPTURES_PER_GRUP).astype(int)]] if len(amb_pilota) else []
    forats = forats.assign(grup=grup_de_durada(forats["durada_s"].to_numpy()),
                           mig=(forats["inici"] + forats["fi"]) // 2)
    forats = forats[t.frame_video[np.clip(forats["mig"].to_numpy(), 0, t.n - 1)] < maxim]
    for _, g in forats.groupby("grup", observed=True):
        tria = g.iloc[np.unique(np.linspace(0, len(g) - 1, CAPTURES_PER_GRUP).astype(int))]
        captures += [{"fila": int(f["mig"]), "forat": f} for _, f in tria.iterrows()]
    return captures


def punts_pilota(t: Tracking, captura: dict) -> list[tuple[np.ndarray, str, str]]:
    """(posició 0-1, estil, nom) de la pilota que es dibuixa a la captura."""
    forat = captura["forat"]
    if forat is None:
        return [(t.pilota[captura["fila"]], "-", "pilota (ATD)")]
    punts = []
    if forat["inici"] > 0:
        punts.append((t.pilota[int(forat["inici"]) - 1], "--", "on es perd"))
    if forat["fi"] < t.n:
        punts.append((t.pilota[int(forat["fi"])], ":", "on torna"))
    return punts


def dibuixa(imatge: np.ndarray, matriu: np.ndarray, t: Tracking, captura: dict):
    fila = captura["fila"]
    fig, (ax, ax_retall) = plt.subplots(1, 2, figsize=(grafic.AMPLE_IN, 3.3), dpi=DPI_CAPTURA,
                                        gridspec_kw={"width_ratios": (2.4, 1)})
    for eix in (ax, ax_retall):
        eix.imshow(imatge)
        eix.axis("off")
        for index, j in enumerate(t.jugadors):
            u, v = projecta(matriu[None], j[fila, :, 0][None], j[fila, :, 1][None])
            eix.scatter(u, v, s=40, facecolors="none", edgecolors=grafic.color_equip(index), lw=1.2)
        for punt, estil, nom in punts_pilota(t, captura):
            u, v = projecta(matriu[None], punt[None, :1], punt[None, 1:])
            eix.scatter(u, v, s=150, facecolors="none", edgecolors=grafic.PILOTA, lw=1.8,
                        linestyles=estil, label=nom)
    centre = next((p for p, _, _ in punts_pilota(t, captura) if not np.isnan(p).any()), None)
    if centre is not None:
        u, v = projecta(matriu[None], centre[None, :1], centre[None, 1:])
        cu, cv = float(u[0, 0]), float(v[0, 0])
        if np.isfinite([cu, cv]).all():
            ax_retall.set_xlim(cu - RETALL_PX, cu + RETALL_PX)
            ax_retall.set_ylim(cv + RETALL_PX, cv - RETALL_PX)
    ax.legend(loc="lower left", fontsize=7, framealpha=0.8)
    fig.tight_layout()
    return fig


def peu(t: Tracking, captura: dict, esperat: Esperat) -> str:
    frame = int(t.frame_video[captura["fila"]])
    lloc = f"fotograma {xifra(frame)} ({rellotge(frame, esperat.fps)}, part {part_de(frame, esperat.rangs_puntuats)})"
    forat = captura["forat"]
    if forat is None:
        return f"{lloc}: l'ATD té la pilota."
    return (f"{lloc}: al mig d'un forat de {xifra(float(forat['durada_s']))} s ({forat['grup']}). "
            "Groc ratllat, on l'ATD la perd; groc puntejat, on la torna a trobar.")


def omple(seccio: Seccio, videos: dict[str, Path | None], t: Tracking | None, h: Homografia | None,
          forats: pd.DataFrame | None, esperat: Esperat) -> None:
    infos = {}
    for font, video in videos.items():
        if video is None:
            continue
        seccio.text(f"**Vídeo {font}.**")
        try:
            infos[font] = ffprobe(video)
        except (subprocess.SubprocessError, OSError, ValueError, KeyError, IndexError) as error:
            seccio.comprovacions([Comprovacio("ffprobe el pot llegir", "sí", type(error).__name__, False)])
            continue
        seccio.comprovacions(comprovacions(infos[font], font, esperat))
        seccio.taula(f"ffprobe · {font}", ("Camp", "Valor"), taula_ffprobe(infos[font]))
    falta = [nom for nom, cosa in (("el vídeo tàctic", infos.get("tactical")), ("l'ATD tàctic", t),
                                   ("la homografia tàctica", h), ("els forats de la pilota", forats)) if cosa is None]
    if falta:
        seccio.text(f"**Sense captures:** falta {', '.join(falta)} (o s'ha demanat `--sense-captures`).")
        return
    maxim = int(infos["tactical"].get("nb_read_packets") or 0)
    desfas = desfasament(infos["tactical"])
    desfas = 0.0 if not np.isfinite(desfas) else desfas
    captures = tria_captures(t, forats, esperat, maxim)
    seccio.text(f"**{len(captures)} captures del vídeo tàctic** amb el tracking projectat amb la seva "
                "homografia: cercles blaus i taronja, els slots de cada equip; groc, la pilota. A la dreta, "
                "el mateix fotograma ampliat al voltant de la pilota. Si els cercles no cauen sobre els "
                "jugadors, el fotograma i el tracking no estan alineats.")
    for captura in captures:
        frame = int(t.frame_video[captura["fila"]])
        try:
            imatge = fotograma(videos["tactical"], frame, esperat.fps, desfas)
            matriu = h.de_frames(np.array([frame]))[0]
            seccio.figura("", dibuixa(imatge, matriu, t, captura), peu(t, captura, esperat), tipus="jpeg")
        except Exception as error:  # noqa: BLE001 - una captura que falla no ha d'aturar les altres
            plt.close("all")
            seccio.text(f"La captura del fotograma {xifra(frame)} no s'ha pogut fer ({type(error).__name__}).")
