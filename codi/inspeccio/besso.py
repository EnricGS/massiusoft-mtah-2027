"""Un bessó obert de les dades del concurs, per provar l'informe sense tocar-les.

L'ATD és el partit 3 de Metrica sample-data, que ve en el mateix format (FIFA/EPTS).
La homografia, el Smart Tagging i els vídeos són sintètics, amb els formats de DATA.md.

    uv run python -I -m inspeccio.besso <carpeta> [--fotogrames N] [--segons-video S]
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import numpy as np

from inspeccio.esperat import ESPERAT, FITXERS
from inspeccio.video import eina

ORIGEN = Path(__file__).resolve().parents[2] / "dades" / "metrica-sample" / "data" / "Sample_Game_3"
# On cau cada cantonada del camp (0-1) a la imatge: una càmera alta i centrada.
CANTONADES_CAMP = ((0, 0), (1, 0), (1, 1), (0, 1))
CANTONADES_IMATGE = ((330, 230), (1590, 230), (1980, 1040), (-60, 1040))
INSTANCIES = (   # (segons, durada, codi, equip, tipus); les tres primeres caben en un bessó curt
    (5, 3, "SET PIECES", "N/A", "Throw-in"),
    (12, 8, "BUILD UP", "Barcelona", None),
    (24, 6, "PROGRESSION", "Atletic Club", None),
    (11185 / 25, 6, "SET PIECES", "Barcelona", "Kick Off (Start)"),
    (470, 18, "BUILD UP", "Barcelona", None),
    (505, 9, "SET PIECES", "N/A", "Throw-in"),
    (520, 14, "PROGRESSION", "Atletic Club", None),
    (560, 25, "DEFENDING IN MIDDLE THIRD", "Barcelona", None),
    (610, 7, "SET PIECES", "Atletic Club", "Corner Kick"),
    (110808 / 25, 6, "SET PIECES", "Atletic Club", "Kick Off (Start)"),
)


def matriu(origen, desti) -> np.ndarray:
    """Homografia que porta els quatre punts d'`origen` als de `desti` (DLT)."""
    files = []
    for (x, y), (u, v) in zip(origen, desti):
        files.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
        files.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    _, _, vt = np.linalg.svd(np.asarray(files, float))
    h = vt[-1].reshape(3, 3)
    return h / h[2, 2]


def homografia(cami: Path, n: int, trams_invalids: int = 0) -> None:
    base = matriu(CANTONADES_CAMP, CANTONADES_IMATGE)
    frames = np.arange(n)
    pas = 120 * np.sin(2 * np.pi * frames / 3000)          # la càmera es mou a poc a poc
    error = 0.24 + 0.02 * np.sin(frames / 7.0)
    (_, _, fi1), (_, inici2, _) = ESPERAT.rangs_puntuats
    error[(frames > fi1) & (frames < inici2)] = 1.5
    valida = np.ones(n, int)
    for k in range(trams_invalids):
        inici = (k + 1) * n // (trams_invalids + 1)
        valida[inici:inici + 60] = 0
    with cami.open("w", encoding="utf-8") as f:
        f.write("frame,h00,h01,h02,h10,h11,h12,h20,h21,h22,reprojection_error,valid\n")
        for i in frames:
            h = np.array([[1, 0, pas[i]], [0, 1, 0], [0, 0, 1]]) @ base
            valors = ",".join(f"{x:.7g}" for x in h.ravel()) if valida[i] else ",".join(["NaN"] * 9)
            f.write(f"{i},{valors},{error[i]:.4f},{valida[i]}\n")


def etiquetatge(cami: Path, segons_max: float) -> None:
    linies = ["<file>", "<ALL_INSTANCES>"]
    for id_, (inici, durada, codi, equip, tipus) in enumerate(INSTANCIES, 1):
        if inici + durada > segons_max:
            continue
        etiquetes = [("Team", equip), ("Half", "1st Half")] + ([("Type", tipus)] if tipus else [])
        linies += [f"<instance><ID>{id_}</ID><start>{inici:.3f}</start><end>{inici + durada:.3f}</end>"
                   f"<code>{codi}</code>",
                   *[f"<label><group>{g}</group><text>{t}</text></label>" for g, t in etiquetes],
                   "</instance>"]
    linies += ["</ALL_INSTANCES>", "</file>"]
    cami.write_text("\n".join(linies) + "\n", encoding="utf-8")


def video(cami: Path, segons: float) -> None:
    ordre = [eina("ffmpeg"), "-v", "error", "-y", "-f", "lavfi", "-i",
             f"testsrc2=size={ESPERAT.amplada_px}x{ESPERAT.alcada_px}:rate={ESPERAT.fps}", "-t", str(segons),
             "-c:v", "libx264", "-preset", "ultrafast", "-crf", "35", "-pix_fmt", "yuv420p", str(cami)]
    subprocess.run(ordre, check=True, timeout=1800)


def atd(meta: Path, raw: Path, n: int | None) -> int:
    shutil.copyfile(ORIGEN / "Sample_Game_3_metadata.xml", meta)
    with (ORIGEN / "Sample_Game_3_tracking.txt").open(encoding="utf-8") as origen, raw.open("w") as desti:
        for i, linia in enumerate(origen):
            if n is not None and i >= n:
                break
            desti.write(linia)
    return i + 1 if n is None else min(n, i + 1)


def fes(carpeta: Path, fotogrames: int | None = None, segons_video: float = 60.0) -> Path:
    arrel = carpeta / "Dades del bessó (Metrica sample-data i sintètiques)"
    for font, noms in FITXERS.items():
        (arrel / font).mkdir(parents=True, exist_ok=True)
        n = atd(arrel / font / noms["atd_meta"], arrel / font / noms["atd_raw"], fotogrames)
        homografia(arrel / font / noms["homografia"], n, trams_invalids=0 if font == "tactical" else 5)
        video(arrel / font / noms["video"], segons_video if font == "tactical" else 4.0)
        if "etiquetatge" in noms:
            etiquetatge(arrel / font / noms["etiquetatge"], n / ESPERAT.fps)
    (arrel / "docs").mkdir(exist_ok=True)
    (arrel / "docs" / "LLEGEIX.txt").write_text("Un fitxer que DATA.md no esmenta.\n", encoding="utf-8")
    return arrel


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("carpeta", type=Path)
    p.add_argument("--fotogrames", type=int, default=None, help="talla l'ATD (per defecte, sencer)")
    p.add_argument("--segons-video", type=float, default=60.0)
    a = p.parse_args()
    print(fes(a.carpeta, a.fotogrames, a.segons_video))
