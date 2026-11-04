"""Els tocs que diuen els esdeveniments dels partits oberts, per comprovar el detector (T2 del pla per tocs).

- **Metrica:** l'inici de cada passada, recuperació, pèrdua, xut i jugada a pilota aturada, i el final de cada
  passada (la recepció), de l'equip que la fa. Van a la imatge: a l'inici d'una passada, la pilota és a menys de
  0,1 m d'un jugador de l'equip (mediana), i a la recepció, a 0,2 m. Es comparen amb ±0,2 s de marge.
- **DFL:** les passades, els xuts, les accions amb pilota (`OtherBallAction`) i les recuperacions (`BallClaiming`),
  de l'equip que les fa. L'hora és la de l'esdeveniment (`EventTime`), que no va sincronitzada amb el tracking: amb
  el millor desfasament, la pilota només és a menys d'1,5 m d'un jugador de l'equip la meitat de les vegades. Es
  comparen amb ±1 s de marge. Les recepcions no hi són.

La imatge de DFL surt de l'hora de la primera imatge de cada part al fitxer de posicions. Es comprova que el nombre
d'imatges de cada part hi quadri amb el del banc.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np

from banc import fonts
from banc.dfl import fitxer
from banc.partit import PartitBanc
from possessio.oficial import possession_metrics as pm

FPS = 25
MARGE = {"metrica": 5, "dfl": 25}                 # imatges de marge a cada costat
VERSIO = 1
DIR_CAU = fonts.DIR_CAU / "tocs"
SECCIONS = ("firstHalf", "secondHalf")
ACCIONS_DFL = ("Play", "ShotAtGoal", "OtherBallAction", "BallClaiming")
INICIS_METRICA = ("PASS", "RECOVERY", "BALL LOST", "SHOT", "SET PIECE")


@dataclass(frozen=True)
class Reals:
    imatge: np.ndarray      # (m,) en ordre
    equip: np.ndarray       # (m,) pm.H o pm.A


def hora(text: str) -> float:
    return datetime.fromisoformat(text).timestamp()


def parts_de_posicions(cami: Path) -> dict[str, tuple[float, int]]:
    """Per a cada part del fitxer de posicions de DFL: l'hora de la primera imatge i quantes n'hi ha."""
    primera, darrera = {}, {}
    seccio, anterior, esperant = None, "", False
    hora_de = re.compile(r' T="([^"]+)"')
    with cami.open(encoding="utf-8") as f:
        for linia in f:
            if linia.startswith("<FrameSet"):
                seccio = re.search(r'GameSection="([^"]+)"', linia).group(1)
                esperant = True
            elif esperant:
                t = hora(hora_de.search(linia).group(1))
                primera[seccio] = min(primera.get(seccio, t), t)
                esperant = False
            elif linia.startswith("</FrameSet"):
                t = hora(hora_de.search(anterior).group(1))
                darrera[seccio] = max(darrera.get(seccio, t), t)
            anterior = linia
    return {s: (primera[s], round((darrera[s] - primera[s]) * FPS) + 1) for s in primera}


def accions_dfl(events: Path, meta: Path) -> list[tuple[float, int]]:
    """(hora, equip) de cada acció amb pilota dels esdeveniments de DFL."""
    casa = next(e.get("TeamId") for e in ET.parse(meta).getroot().iter("Team") if e.get("Role") == "home")
    accions = []
    for event in ET.parse(events).getroot().iter("Event"):
        accio = next((fill for fill in event.iter() if fill.tag in ACCIONS_DFL and fill.get("Team")), None)
        if accio is not None:
            accions.append((hora(event.get("EventTime")), pm.H if accio.get("Team") == casa else pm.A))
    return accions


def a_imatges(accions: list[tuple[float, int]], parts: dict[str, tuple[float, int]], p: PartitBanc) -> Reals:
    """Cada acció a la imatge del banc de la seva part; les que cauen fora de les parts no hi són."""
    if [n for _, n in (parts[s] for s in SECCIONS)] != [ultim - inici + 1 for _, inici, ultim in p.trams]:
        raise ValueError(f"{p.nom}: les parts del fitxer de posicions no quadren amb les del banc")
    imatges, equips = [], []
    for t, equip in accions:
        for seccio, (_, inici, ultim) in zip(SECCIONS, p.trams):
            i = inici + round((t - parts[seccio][0]) * FPS)
            if inici <= i <= ultim:
                imatges.append(i)
                equips.append(equip)
                break
    return ordena(np.array(imatges, dtype=int), np.array(equips, dtype=np.int8))


def de_metrica(events, frames: np.ndarray) -> Reals:
    """De la taula d'esdeveniments del prototip (`possessio.carrega`) i del fotograma de cada fila del banc."""
    imatges, equips = [], []
    for tipus, columna in [(t, "start_frame") for t in INICIS_METRICA] + [("PASS", "end_frame")]:
        tria = events[events["type"] == tipus]
        fila = np.searchsorted(frames, tria[columna].to_numpy(int))
        hi_es = (fila < len(frames)) & (frames[np.minimum(fila, len(frames) - 1)] == tria[columna].to_numpy(int))
        imatges.append(fila[hi_es])
        equips.append(np.where(tria["team"].to_numpy(str)[hi_es] == "Home", pm.H, pm.A))
    return ordena(np.concatenate(imatges), np.concatenate(equips).astype(np.int8))


def ordena(imatge: np.ndarray, equip: np.ndarray) -> Reals:
    """En ordre i sense repetits (una passada que surt d'una jugada a pilota aturada, per exemple)."""
    unics = np.unique(np.stack([imatge, equip.astype(int)]), axis=1)
    return Reals(imatge=unics[0].astype(int), equip=unics[1].astype(np.int8))


def llegeix(nom: str, p: PartitBanc) -> Reals:
    font, clau = nom.split("-", 1)
    if font == "dfl":
        parts = parts_de_posicions(fitxer(fonts.DIR_IDSSE, f"DFL_04_03_positions_raw_observed_*{clau}.xml"))
        accions = accions_dfl(fitxer(fonts.DIR_IDSSE, f"DFL_03_02_events_raw_*{clau}.xml"),
                              fitxer(fonts.DIR_IDSSE, f"DFL_02_01_matchinformation_*{clau}.xml"))
        return a_imatges(accions, parts, p)
    from possessio.carrega import carrega_partit

    prototip = carrega_partit(int(clau))
    return de_metrica(prototip.events, np.asarray(prototip.frame, int))


def reals(nom: str, p: PartitBanc | None = None, cau: Path = DIR_CAU) -> Reals:
    """Els tocs dels esdeveniments d'un partit del banc, de la memòria cau si hi són."""
    cami = cau / f"{nom}.npz"
    if cami.exists():
        with np.load(cami) as desat:
            if int(desat["versio"]) == VERSIO:
                return Reals(imatge=desat["imatge"], equip=desat["equip"])
    r = llegeix(nom, fonts.partit(nom) if p is None else p)
    cau.mkdir(parents=True, exist_ok=True)
    temporal = cami.with_name(f"{cami.stem}.part.npz")
    np.savez(temporal, versio=VERSIO, imatge=r.imatge, equip=r.equip)
    temporal.replace(cami)
    return r
