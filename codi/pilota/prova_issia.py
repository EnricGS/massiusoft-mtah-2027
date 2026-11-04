"""FootAndBall a les càmeres 5 i 6 d'ISSIA-CNR, que no va veure en l'entrenament (V1 de `docs/pla-video.md`).

    cd codi && uv run --with torch --with torchvision --with opencv-python-headless python -I -m pilota.prova_issia

Totes les imatges de cada càmera, en tres variants (`VARIANTS`):
- a la mida del vídeo (1920 × 1080), on la pilota fa uns 10 px;
- a la meitat (960 × 540): la pilota en fa uns 5, com la que pot fer al vídeo tàctic;
- a la meitat i tornada a ampliar ×2 per al detector: és el que farà l'eina que valida l'ATD quan la pilota sigui
  petita (`pilota/valida.py`). La imatge té la mida de la primera, però amb el detall de la segona.

De cada imatge es guarden les `MAXIM` pilotes més probables, i després es mira, per a cada llindar de confiança:
- **amb pilota marcada:** si la més probable passa del llindar i és a `RADI_PX` o menys de la marcada (trobada), si
  n'hi ha alguna altra que hi sigui (entre les candidates), i l'error de la trobada;
- **sense pilota marcada:** si en dona alguna per sobre del llindar. No vol dir que sigui falsa: pot ser una pilota
  que no s'ha marcat, o una de fora del camp.

Les distàncies són en píxels de la mida del vídeo. Escriu `resultats/issia-footandball.md` i `.json`, i desa les
candidates a `dades/issia/cau/` per no haver de tornar a passar el detector.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from pilota import footandball, issia

CAMERES = (5, 6)
VARIANTS = ((1.0, 1.0), (0.5, 1.0), (0.5, 2.0))     # (la imatge es redueix, el detector l'amplia)
MAXIM = 10
RADI_PX = 10.0
LLINDARS = (0.1, 0.3, 0.5, 0.7, 0.9)
DIR_CAU = issia.DIR_ISSIA / "cau"
DIR_RESULTATS = Path(__file__).resolve().parent / "resultats"


def nom_variant(reduccio: float, ampliacio: float) -> str:
    return f"×{reduccio:g}" + (f", ampliada ×{ampliacio:g}" if ampliacio != 1 else "")


def candidates(camera: int, reduccio: float, ampliacio: float, detector, cau: Path = DIR_CAU) -> np.ndarray:
    """(imatges, MAXIM, 3): x, y (píxels del vídeo) i confiança de les candidates de cada imatge; NaN si n'hi ha menys."""
    import cv2

    variant = f"x{reduccio:g}" + (f"-a{ampliacio:g}" if ampliacio != 1 else "")
    cami = cau / f"footandball-c{camera}-{variant}-{footandball.SHA_PESOS[:12]}.npy"
    if cami.exists():
        return np.load(cami)
    sortida = np.full((issia.IMATGES, MAXIM, 3), np.nan)
    video = cv2.VideoCapture(str(issia.video(camera)))
    for i in range(issia.IMATGES):
        llegida, imatge = video.read()
        if not llegida:
            break
        imatge = footandball.redimensiona(imatge[:1080], reduccio)    # les càmeres 1 i 2 fan 1088 d'alt
        c = detector.pilotes(imatge, ampliacio)
        m = min(MAXIM, len(c.x))
        sortida[i, :m] = np.column_stack([c.x[:m] / reduccio, c.y[:m] / reduccio, c.confianca[:m]])
    video.release()
    cau.mkdir(parents=True, exist_ok=True)
    np.save(cami, sortida)
    return sortida


def mesura(cand: np.ndarray, marcada: np.ndarray, llindar: float, radi: float = RADI_PX) -> dict[str, float]:
    """Les mesures d'un llindar: `cand` (n, k, 3) de més a menys confiança, `marcada` (n, 2) NaN si no n'hi ha."""
    amb = ~np.isnan(marcada[:, 0])
    distancia = np.linalg.norm(cand[..., :2] - marcada[:, None, :], axis=2)
    passa = cand[..., 2] >= llindar
    a_prop = passa & (distancia <= radi)
    trobada = a_prop[:, 0]
    error = distancia[:, 0][amb & trobada]
    return {"marcades": int(amb.sum()), "trobada": float(trobada[amb].mean()) if amb.any() else np.nan,
            "entre_les_candidates": float(a_prop[amb].any(axis=1).mean()) if amb.any() else np.nan,
            "error_px": float(np.median(error)) if len(error) else np.nan,
            "sense_marcar": int((~amb).sum()),
            "en_dona_sense_marcar": float(passa[~amb].any(axis=1).mean()) if (~amb).any() else np.nan}


def markdown(t: pd.DataFrame) -> str:
    def pct(v: float) -> str:
        return "—" if pd.isna(v) else f"{v:.0%}"

    linies = ["# FootAndBall a ISSIA-CNR, càmeres 5 i 6", "",
              "Generat amb `uv run --with torch --with torchvision --with opencv-python-headless python -I -m",
              "pilota.prova_issia`. Vídeo obert (`dades/FONT-issia.md`); cap dada del concurs. El model és el publicat,",
              "entrenat amb les càmeres 1 a 4 (`dades/FONT-footandball.md`). Què es mesura: la capçalera de",
              f"`pilota/prova_issia.py`. **Trobada:** la candidata més probable passa del llindar i és a {RADI_PX:g} px o",
              "menys de la pilota marcada. **Error:** la mediana, en píxels del vídeo, de les trobades.", "",
              "| càmera | imatge | llindar | marcades | trobada | entre les candidates | error (px) | sense marcar "
              "| en dona alguna sense marcar |",
              "|---|---|---|---|---|---|---|---|---|"]
    linies += [f"| {f.camera} | {f.imatge} | {f.llindar:g} | {f.marcades} | {pct(f.trobada)} | "
               f"{pct(f.entre_les_candidates)} | {'—' if pd.isna(f.error_px) else f'{f.error_px:.1f}'} | "
               f"{f.sense_marcar} | {pct(f.en_dona_sense_marcar)} |" for f in t.itertuples()]
    return "\n".join([*linies, ""])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fils", type=int, default=None)
    args = ap.parse_args()
    detector = footandball.Detector(maxim=MAXIM, fils=args.fils)
    files = []
    for camera in CAMERES:
        marcada = issia.anotacions(camera).pilota
        for reduccio, ampliacio in VARIANTS:
            cand = candidates(camera, reduccio, ampliacio, detector)
            files += [{"camera": camera, "imatge": nom_variant(reduccio, ampliacio), "llindar": llindar,
                       **mesura(cand, marcada, llindar)} for llindar in LLINDARS]
    t = pd.DataFrame(files)
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "issia-footandball.json").write_text(json.dumps(files, indent=1))
    (DIR_RESULTATS / "issia-footandball.md").write_text(markdown(t))
    print(markdown(t))


if __name__ == "__main__":
    main()
