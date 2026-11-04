"""Les imatges del vídeo, en ordre i sense desar-ne cap: ffmpeg les descodifica totes d'una tirada i per la canonada
només en passen les que es demanen.

- **Una de cada `pas`:** el filtre `select` de ffmpeg deixa passar les imatges *n* amb *n* múltiple de `pas`,
  comptades des de la primera del vídeo (la 0), com les files de l'entrega. Descodificar-ho tot en ordre és exacte:
  no depèn d'on ffmpeg troba la imatge en saltar, com passa amb `-ss`.
- **Per memòria:** cada imatge arriba en cru (BGR, 8 bits) i es torna com a array. No toca el disc.
- **S'atura** en passar l'última imatge demanada.
"""

from __future__ import annotations

import subprocess
from collections.abc import Iterator
from pathlib import Path

import numpy as np

from inspeccio.video import eina


def mida(video: Path) -> tuple[int, int]:
    """(amplada, alçada) en píxels, del primer flux de vídeo."""
    ordre = [eina("ffprobe"), "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
             "-of", "csv=p=0", str(video)]
    sortida = subprocess.run(ordre, capture_output=True, text=True, check=True, timeout=120)
    ample, alt = (int(v) for v in sortida.stdout.strip().split(",")[:2])
    return ample, alt


def imatges(video: Path, frames: np.ndarray, pas: int, mides: tuple[int, int] | None = None
            ) -> Iterator[tuple[int, np.ndarray]]:
    """(imatge, array BGR (alt, ample, 3)) de cada una de `frames`, en ordre. Totes han de ser múltiples de `pas`."""
    frames = np.unique(np.asarray(frames, dtype=np.int64))
    if len(frames) == 0:
        return
    if (frames % pas).any() or frames[0] < 0:
        raise ValueError(f"les imatges han de ser múltiples de {pas}")
    ample, alt = mides or mida(video)
    mida_bytes = ample * alt * 3
    sortides = int(frames[-1]) // pas + 1
    ordre = [eina("ffmpeg"), "-v", "error", "-nostdin", "-i", str(video), "-an", "-sn", "-dn",
             "-vf", f"select=not(mod(n\\,{pas}))", "-fps_mode", "passthrough", "-frames:v", str(sortides),
             "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    proces = subprocess.Popen(ordre, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    volgudes = set(frames.tolist())
    try:
        for j in range(sortides):
            dades = _llegeix(proces.stdout, mida_bytes)
            if len(dades) < mida_bytes:
                raise RuntimeError("El vídeo s'acaba abans de l'última imatge demanada")
            if j * pas in volgudes:
                yield j * pas, np.frombuffer(dades, np.uint8).reshape(alt, ample, 3)
    finally:
        proces.kill()
        proces.wait()


def _llegeix(flux, n: int) -> bytes:
    """Exactament `n` bytes, o menys si el flux s'acaba."""
    trossos, falten = [], n
    while falten:
        tros = flux.read(falten)
        if not tros:
            break
        trossos.append(tros)
        falten -= len(tros)
    return b"".join(trossos)
