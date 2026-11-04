"""El vídeo obert d'ISSIA-CNR (`dades/FONT-issia.md`): sis càmeres fixes d'estadi d'un partit de la Sèrie A, amb la
pilota i el jugador que la toca marcats a mà.

- **Les anotacions** (`Annotation Files/*.xgtf`, format ViPER) diuen, per trams d'imatges: on és la pilota (en
  píxels), si és un xut i quin jugador la toca (−1 si cap). Es llegeixen com a text, sense executar res.
- **Les imatges:** la *n* de les anotacions és la *n* − 8 del vídeo (`DESFASAMENT`), com fa FootAndBall.
- **Les càmeres 2 i 6** tenen la x de la pilota girada: la del vídeo és l'amplada menys la marcada (`GIRADES`), com
  corregeix FootAndBall (`data/issia_utils.py`). Sense girar-la, a la càmera 6 no en coincideix cap.
- **On no hi ha pilota marcada,** la pilota no és a la vista d'aquella càmera, o no s'ha marcat.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ARREL = Path(__file__).resolve().parents[2]
DIR_ISSIA = ARREL / "dades" / "issia"
DESFASAMENT = -8
IMATGES = 3002                  # les de cada vídeo
GIRADES = (2, 6)
AMPLADA = 1920


@dataclass(frozen=True)
class Anotacions:
    pilota: np.ndarray          # (IMATGES, 2) píxels de cada imatge del vídeo, NaN si no n'hi ha de marcada
    toc: np.ndarray             # (IMATGES,) bool: algun jugador la toca


def video(camera: int, carpeta: Path = DIR_ISSIA) -> Path:
    return carpeta / f"filmrole{camera}.avi"


def fitxer(camera: int, carpeta: Path = DIR_ISSIA) -> Path:
    trobats = sorted((carpeta / "Annotation Files").glob(f"Film Role-0 ID-{camera} *.xgtf"))
    if len(trobats) != 1:
        raise FileNotFoundError(f"càmera {camera}: hi ha {len(trobats)} fitxers d'anotacions")
    return trobats[0]


def _trams(element: ET.Element):
    """(primera, última, element) de cada valor d'un atribut dinàmic de ViPER."""
    for valor in element:
        primera, ultima = map(int, valor.get("framespan").split(":"))
        yield primera + DESFASAMENT, ultima + DESFASAMENT, valor


def llegeix(cami: Path, imatges: int = IMATGES, girada_a: int | None = None) -> Anotacions:
    """`girada_a`: si la x de la pilota està girada, l'amplada de la imatge."""
    pilota = np.full((imatges, 2), np.nan)
    toc = np.zeros(imatges, bool)
    for objecte in ET.parse(cami).getroot().iter():
        if not (objecte.tag.endswith("object") and objecte.get("name") == "BALL"):
            continue
        for atribut in objecte:
            for primera, ultima, valor in _trams(atribut):
                tria = slice(max(primera, 0), min(ultima, imatges - 1) + 1)
                if atribut.get("name") == "BallPos":
                    x = float(valor.get("x"))
                    pilota[tria] = (girada_a - x if girada_a else x, float(valor.get("y")))
                elif atribut.get("name") == "PlayerInteractingID" and int(valor.get("value")) > -1:
                    toc[tria] = True
    return Anotacions(pilota=pilota, toc=toc)


def anotacions(camera: int, carpeta: Path = DIR_ISSIA) -> Anotacions:
    return llegeix(fitxer(camera, carpeta), girada_a=AMPLADA if camera in GIRADES else None)
