"""La homografia: si és la que diu DATA.md, com es mou la càmera i quants píxels fa la pilota.

La mida de la pilota en píxels és la dada que decideix si val la pena buscar-la
al vídeo tàctic (enfocament B).
"""

from __future__ import annotations

import numpy as np

from inspeccio import grafic
from inspeccio.carrega import Homografia, Tracking, projecta
from inspeccio.esperat import DIAMETRE_PILOTA_M, Esperat
from inspeccio.seccio import Seccio, comprova_aprop, comprova_igual, pct, xifra
from inspeccio.temps import puntuats, tirades

CADA = 25       # una mostra per segon
QUANTILS = (5, 25, 50, 75, 95)


def comprovacions(h: Homografia, esperat: Esperat) -> list:
    n = esperat.fotogrames[h.font]
    llista = [
        comprova_igual("files", n, len(h.frame)),
        comprova_igual("frame de 0 a n − 1, seguits", True,
                       bool(len(h.frame) and h.frame[0] == 0 and np.all(np.diff(h.frame) == 1))),
        comprova_aprop("matrius vàlides", esperat.homografia_valida_pct[h.font],
                       round(pct(h.valida.sum(), len(h.valida)), 1), 0.05, " %"),
    ]
    if h.font == "tactical":
        joc = puntuats(h.frame, esperat.rangs_puntuats)
        (_, _, fi1), (_, inici2, _) = esperat.rangs_puntuats[:2]
        descans = (h.frame > fi1) & (h.frame < inici2)
        llista += [
            comprova_aprop("error de reprojecció, mediana en joc", esperat.error_reprojeccio_mediana_joc,
                           round(float(np.nanmedian(h.error[joc])), 2), 0.01),
            comprova_aprop("error de reprojecció, mediana al descans", esperat.error_reprojeccio_descans,
                           round(float(np.nanmedian(h.error[descans])), 2), 0.25),
        ]
    else:
        inicis, fins = tirades(~h.valida)
        mes_llarg = float((fins - inicis).max()) / esperat.fps if len(inicis) else 0.0
        llista += [
            comprova_igual("trams sense matriu", esperat.homografia_trams_invalids_broadcast, len(inicis)),
            comprova_igual("el tram més llarg passa d'1,5 min", True,
                           mes_llarg > esperat.homografia_tram_mes_llarg_broadcast_s),
            comprova_aprop("error de reprojecció màxim", esperat.error_reprojeccio_max_broadcast,
                           round(float(np.nanmax(h.error)), 0), 1.0),
        ]
    return llista


def diametre_pilota(h: Homografia, t: Tracking, esperat: Esperat) -> tuple[np.ndarray, np.ndarray]:
    """Diàmetre aparent de la pilota (px) on l'ATD la té, un cop per segon puntuat."""
    dins = puntuats(t.frame_video, esperat.rangs_puntuats) & ~np.isnan(t.pilota[:, 0])
    files = np.flatnonzero(dins)[::CADA]
    matrius = h.de_frames(t.frame_video[files])
    x, y = t.pilota[files, 0], t.pilota[files, 1]
    dx, dy = DIAMETRE_PILOTA_M / esperat.camp_m[0] / 2, DIAMETRE_PILOTA_M / esperat.camp_m[1] / 2
    u = projecta(matrius, np.stack([x - dx, x + dx, x, x], 1), np.stack([y, y, y - dy, y + dy], 1))
    ample = np.hypot(u[0][:, 1] - u[0][:, 0], u[1][:, 1] - u[1][:, 0])
    alt = np.hypot(u[0][:, 3] - u[0][:, 2], u[1][:, 3] - u[1][:, 2])
    # La silueta d'una esfera és rodona: fa el que fa l'eix que la perspectiva no escurça.
    return np.maximum(ample, alt), t.pilota[files]


def taula_zones(diametres: np.ndarray, posicions: np.ndarray) -> list[tuple]:
    """Mediana del diàmetre per terços del camp (al llarg i a l'ample)."""
    terc_x = np.clip((posicions[:, 0] * 3).astype(int), 0, 2)
    terc_y = np.clip((posicions[:, 1] * 3).astype(int), 0, 2)
    noms_y = ("banda de dalt (y < 1/3)", "centre", "banda de baix (y > 2/3)")
    files = []
    for j, nom in enumerate(noms_y):
        fila = [nom]
        for i in range(3):
            tria = (terc_x == i) & (terc_y == j) & np.isfinite(diametres)
            fila.append(f"{xifra(float(np.median(diametres[tria])))} px ({tria.sum()})" if tria.any() else "—")
        files.append(tuple(fila))
    return files


def camera(h: Homografia, esperat: Esperat) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """On cau el centre del camp a la imatge i quants píxels fa 1 m allà, un cop per segon."""
    tria = np.arange(0, len(h.frame), CADA)
    matrius = h.matrius[tria]
    metre = 1 / esperat.camp_m[0]
    u, v = projecta(matrius, np.tile([0.5, 0.5 + metre], (len(tria), 1)), np.full((len(tria), 2), 0.5))
    return h.frame[tria], np.stack([u[:, 0], v[:, 0]], 1), np.hypot(u[:, 1] - u[:, 0], v[:, 1] - v[:, 0])


def cantonades_visibles(h: Homografia, esperat: Esperat) -> float:
    index = np.flatnonzero(puntuats(h.frame, esperat.rangs_puntuats) & h.valida)[::CADA]
    u, v = projecta(h.matrius[index], np.tile([0, 1, 0, 1], (len(index), 1)),
                    np.tile([0, 0, 1, 1], (len(index), 1)))
    dins = (u >= 0) & (u < esperat.amplada_px) & (v >= 0) & (v < esperat.alcada_px)
    return pct(dins.all(axis=1).sum(), len(index))


def figura_error(h: Homografia, esperat: Esperat):
    fig, ax = grafic.figura(2.6)
    if h.font == "tactical":
        grafic.ombreja_rangs(ax, esperat.rangs_puntuats, esperat.fps)
    ax.plot(h.frame[::CADA] / esperat.fps / 60, h.error[::CADA], color=grafic.TINTA, lw=0.6)
    if np.nanmax(h.error, initial=0) > 0:
        ax.set_yscale("log")
    ax.set_ylabel("error de reprojecció")
    ax.set_xlabel("minut del vídeo")
    return fig


def figura_camera(frames, centre, pixels_metre, esperat: Esperat):
    fig, (ax1, ax2) = grafic.figura(3.6, 2, 1, sharex=True)
    minuts = frames / esperat.fps / 60
    for ax in (ax1, ax2):
        grafic.ombreja_rangs(ax, esperat.rangs_puntuats, esperat.fps)
    ax1.plot(minuts, centre[:, 0], color=grafic.LOCAL, lw=0.7, label="x (px)")
    ax1.plot(minuts, centre[:, 1], color=grafic.VISITANT, lw=0.7, label="y (px)")
    ax1.set_ylabel("centre del camp")
    ax1.legend(frameon=False, ncols=2)
    ax2.plot(minuts, pixels_metre, color=grafic.TINTA, lw=0.7)
    ax2.ticklabel_format(axis="y", useOffset=False)
    ax2.set_ylim(bottom=0)
    ax2.set_ylabel("px per metre al centre")
    ax2.set_xlabel("minut del vídeo")
    return fig


def figura_diametre(diametres: np.ndarray):
    fig, ax = grafic.figura(2.6)
    valids = diametres[np.isfinite(diametres)]
    if len(valids):
        ax.hist(valids, bins=np.linspace(0, np.percentile(valids, 99.5) * 1.05, 50), color=grafic.TINTA_2)
    ax.set_xlabel("diàmetre aparent de la pilota (px)")
    ax.set_ylabel("segons")
    return fig


def omple(seccio: Seccio, h: Homografia, t: Tracking | None, esperat: Esperat) -> None:
    seccio.comprovacions(comprovacions(h, esperat))
    seccio.figura("Error de reprojecció (escala logarítmica, un valor per segon)", figura_error(h, esperat))
    if h.font != "tactical":
        return
    seccio.text(f"El camp sencer cap a la imatge en el {xifra(cantonades_visibles(h, esperat))} % "
                "dels segons puntuats (les quatre cantonades dins dels píxels).")
    frames, centre, pixels_metre = camera(h, esperat)
    seccio.figura("La càmera: on cau el centre del camp i quants píxels fa un metre", figura_camera(
        frames, centre, pixels_metre, esperat), "Si les línies són planes, la càmera no es mou.")
    if t is None:
        return
    diametres, posicions = diametre_pilota(h, t, esperat)
    valids = diametres[np.isfinite(diametres)]
    if not len(valids):
        seccio.text("No hi ha cap fotograma puntuat amb pilota i matriu per mesurar-ne la mida.")
        return
    seccio.text(f"**La pilota fa {xifra(float(np.median(valids)))} px de diàmetre (mediana)**, "
                f"comptant {DIAMETRE_PILOTA_M * 100:.0f} cm sobre la gespa en la direcció que la perspectiva "
                f"no escurça, en {xifra(len(valids))} "
                "segons puntuats on l'ATD la té. És la mida que hauria de trobar un detector al vídeo "
                "tàctic; a l'aire es veu una mica més gran.")
    seccio.taula("Diàmetre aparent de la pilota", tuple(f"p{q}" for q in QUANTILS),
                 [tuple(f"{xifra(float(np.percentile(valids, q)))} px" for q in QUANTILS)])
    seccio.taula("Diàmetre (mediana) per zona del camp; entre parèntesis, els segons mirats",
                 ("", "terç esquerre (x < 1/3)", "terç central", "terç dret (x > 2/3)"),
                 taula_zones(diametres, posicions))
    seccio.figura("Diàmetre aparent de la pilota on l'ATD la té", figura_diametre(diametres))
