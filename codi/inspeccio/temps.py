"""Trams de fotogrames: els que es puntuen, i les tirades d'una màscara."""

from __future__ import annotations

import numpy as np


def tirades(mascara: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Inici i fi (exclusiu) de cada tirada de True."""
    m = np.concatenate([[0], np.asarray(mascara, np.int8), [0]])
    canvis = np.flatnonzero(np.diff(m))
    return canvis[0::2], canvis[1::2]


def puntuats(frame_video: np.ndarray, rangs) -> np.ndarray:
    mascara = np.zeros(len(frame_video), bool)
    for _, inici, fi in rangs:
        mascara |= (frame_video >= inici) & (frame_video <= fi)
    return mascara


def part_de(frame_video: int, rangs) -> int | None:
    for part, inici, fi in rangs:
        if inici <= frame_video <= fi:
            return part
    return None


def rellotge(frame_video: int, fps: float) -> str:
    segons = int(frame_video / fps)
    h, resta = divmod(segons, 3600)
    return f"{h}:{resta // 60:02d}:{resta % 60:02d}"
