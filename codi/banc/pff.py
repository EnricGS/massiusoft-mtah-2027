"""Un partit del Mundial 2022 de PFF FC al format del banc, per entrenar (T3ab del pla per tocs, `docs/pla-tocs.md`,
«T3ab»; D-60 a D-62). No es prova mai: només n'aprenen les xarxes. Les dades són a `dades/pff/`
(`dades/FONT-pff.md`).

El tracking és el de la retransmissió (Sportlogiq), a 29,97 imatges per segon (el `fps` de les metadades):
- **només les dues parts;** la pròrroga, no;
- **les imatges repetides,** fora: hi surten un cop per cada esdeveniment de possessió, iguals (si no ho són, s'atura);
- **els jugadors,** les posicions de Sportlogiq tal com són, també les estimades, amb una columna per dorsal de cada
  equip (si un dorsal surt dos cops a la mateixa imatge, el segon va a una altra columna). **Mai les suavitzades**
  (`*Smoothed`): la pilota suavitzada es fa amb els esdeveniments i porta la possessió a dins;
- **la pilota,** només on es veu (`VISIBLE`). On és estimada o no hi és, NaN.

La veritat, amb els esdeveniments de joc (`esdeveniments`, `veritat_font`), a l'hora del vídeo (la imatge de PFF és
els segons per les imatges per segon):
- **l'equip** de l'última possessió d'un jugador (`OTB`) o sacada de centre que ha començat: canvia quan comença la
  d'un jugador de l'altre equip, al primer toc, també als rebots;
- **D** des de cada pilota fora (`OUT`, també pel xiulet) i des del final de cada part (`END`) fins a la possessió
  següent, i abans de la primera;
- **no compten** els duels sense equip ni els esdeveniments que PFF anul·la després (`initialNonEvent`): gairebé tots
  són tocs entre una falta o un fora de joc i el xiulet;
- **X** (no s'aprèn) on no es veu cap jugador ni la pilota: la tele no ensenya el camp (repeticions, plans curts).

A 25 imatges per segon, dins de cada part, com a `skillcorner.py`: les posicions, en línia recta entre dues imatges de
PFF seguides (la pilota, només entre dues on es veu), i cada imatge pren la veritat de la imatge de PFF més propera.
Les coordenades passen de metres, amb el zero al mig del camp, a 0-1, com les de l'ATD.
"""

from __future__ import annotations

import bz2
import json
from pathlib import Path
from typing import NamedTuple

import numpy as np

from banc.partit import PartitBanc, trams_de_parts
from cadena.llegeix import Tracking
from possessio.oficial import possession_metrics as pm

FPS = 25
PARTS = (1, 2)
COMENCEN = ("OTB", "FIRSTKICKOFF", "SECONDKICKOFF")
MOREN = ("OUT", "END")


def fitxers(carpeta: Path, partit: int) -> tuple[Path, Path, Path]:
    """El tracking, els esdeveniments i les metadades d'un partit."""
    return (carpeta / "tracking" / f"{partit}.jsonl.bz2", carpeta / "event-data" / f"{partit}.json",
            carpeta / "metadata" / f"{partit}.json")


def esdeveniments(files: list[dict], fps: float) -> list[tuple[int, int]]:
    """(imatge de PFF on comença, pm.H, pm.A o pm.D) de cada esdeveniment de joc que fa la veritat, en ordre. Cada
    esdeveniment de joc hi surt un cop per esdeveniment de possessió: només compta el primer."""
    vistos: dict[int, dict] = {}
    for f in files:
        vistos.setdefault(f["gameEventId"], f)
    inicis = []
    for f in vistos.values():
        g = f["gameEvents"]
        if g.get("initialNonEvent"):
            continue
        if g["gameEventType"] in COMENCEN and g.get("homeTeam") is not None:
            codi = pm.H if g["homeTeam"] else pm.A
        elif g["gameEventType"] in MOREN:
            codi = pm.D
        else:
            continue
        inicis.append((int(round(f["startTime"] * fps)), codi))
    return sorted(inicis, key=lambda e: e[0])


def veritat_font(frame: np.ndarray, inicis: list[tuple[int, int]]) -> np.ndarray:
    """A cada imatge de PFF, el codi de l'últim esdeveniment que hi ha començat (`esdeveniments`); D abans del
    primer."""
    quan = np.array([e[0] for e in inicis], dtype=np.int64)
    codis = np.array([pm.D] + [e[1] for e in inicis], dtype=np.int8)
    return codis[np.searchsorted(quan, frame, side="right")]


def a_25(frame: np.ndarray, valors: np.ndarray, fps_font: float) -> tuple[np.ndarray, np.ndarray]:
    """D'una part a `fps_font` imatges per segon (`frame` seguits) a 25: els temps nous (en imatges de la font) i els
    valors interpolats en línia recta, NaN si a qualsevol de les dues imatges del costat ho és."""
    if np.any(np.diff(frame) != 1):
        raise ValueError("Falten imatges dins d'una part")
    ratio = FPS / fps_font
    nous = np.arange(np.ceil(frame[0] * ratio), np.floor(frame[-1] * ratio) + 1) / ratio
    u = nous - frame[0]
    i = np.minimum(np.floor(u).astype(int), len(frame) - 2)
    t = (u - i).reshape((-1,) + (1,) * (valors.ndim - 1))
    return nous, (1 - t) * valors[i] + t * valors[i + 1]


class Imatge(NamedTuple):
    """El que es fa servir d'una imatge de PFF: els jugadors de cada equip (dorsal, si es veu, x, y) i la pilota que
    es veu (x, y, z), si n'hi ha. La resta de la línia (també les posicions suavitzades) no es guarda."""
    frame: int
    part: int
    casa: tuple[tuple[str, bool, float, float], ...]
    fora: tuple[tuple[str, bool, float, float], ...]
    pilota: tuple[float, float, float] | None
    es_veu: bool


def _imatge(f: dict) -> Imatge:
    casa, fora = ([(str(j["jerseyNum"]), j["visibility"] == "VISIBLE", j["x"], j["y"]) for j in f[clau] or []]
                  for clau in ("homePlayers", "awayPlayers"))
    vista = [b for b in f["balls"] or [] if b["visibility"] == "VISIBLE"]
    pilota = None if not vista else (vista[0]["x"], vista[0]["y"], np.nan if vista[0]["z"] is None else vista[0]["z"])
    es_veu = pilota is not None or any(j[1] for j in casa + fora)
    return Imatge(int(f["frameNum"]), int(f["period"]), tuple(casa), tuple(fora), pilota, es_veu)


def imatges(cami: Path, partit: int) -> list[Imatge]:
    """Les imatges de les dues parts, cadascuna un cop, en ordre."""
    unes: dict[int, Imatge] = {}
    with bz2.open(cami, "rt") as entrada:
        for linia in entrada:
            if not linia.strip():
                continue
            f = json.loads(linia)
            if f["period"] not in PARTS:
                continue
            im = _imatge(f)
            ja = unes.setdefault(im.frame, im)
            if ja is not im and ja != im:
                raise ValueError(f"pff-{partit}: la imatge {im.frame} surt dos cops i no és igual")
    return [unes[k] for k in sorted(unes)]


def _columnes(jugadors: list[tuple]) -> dict[tuple[str, int], int]:
    """Una columna per dorsal (i per cada vegada que surt a la mateixa imatge), ordenades pel dorsal."""
    claus = set()
    for de_la_imatge in jugadors:
        vegades: dict[str, int] = {}
        for j in de_la_imatge:
            k = vegades[j[0]] = vegades.get(j[0], -1) + 1
            claus.add((j[0], k))
    ordre = sorted(claus, key=lambda c: (int(c[0]) if c[0].isdigit() else 1_000, c[0], c[1]))
    return {c: i for i, c in enumerate(ordre)}


def _posicions(jugadors: list[tuple]) -> np.ndarray:
    columnes = _columnes(jugadors)
    out = np.full((len(jugadors), len(columnes), 2), np.nan)
    for i, de_la_imatge in enumerate(jugadors):
        vegades: dict[str, int] = {}
        for dorsal, _, x, y in de_la_imatge:
            k = vegades[dorsal] = vegades.get(dorsal, -1) + 1
            if x is not None and y is not None:
                out[i, columnes[(dorsal, k)]] = (x, y)
    return out


def llegeix(carpeta: Path, partit: int) -> PartitBanc:
    cami_tracking, cami_esdeveniments, cami_fitxa = fitxers(carpeta, partit)
    fitxa = json.loads(cami_fitxa.read_text())[0]
    fps = float(fitxa["fps"])
    files_esdeveniments = json.loads(cami_esdeveniments.read_text())
    camp = next(f["stadiumMetadata"] for f in files_esdeveniments if f.get("stadiumMetadata"))
    llarg, ample = float(camp["pitchLength"]), float(camp["pitchWidth"])
    inicis = esdeveniments(files_esdeveniments, fps)

    files = imatges(cami_tracking, partit)
    frame = np.array([f.frame for f in files], dtype=np.int64)
    periode = np.array([f.part for f in files], dtype=np.int64)
    pilota = np.array([f.pilota if f.pilota is not None else (np.nan,) * 3 for f in files], dtype=float)
    es_veu = np.array([f.es_veu for f in files], dtype=bool)
    casa, fora = _posicions([f.casa for f in files]), _posicions([f.fora for f in files])
    jugadors = np.concatenate([casa, fora], axis=1)
    veritat = veritat_font(frame, inicis)
    veritat[~es_veu] = pm.X

    trossos = []
    for part in PARTS:
        dins = np.flatnonzero(periode == part)
        if not len(dins):
            raise ValueError(f"pff-{partit}: falta la part {part}")
        f = frame[dins]
        nous, pil = a_25(f, pilota[dins], fps)
        _, jug = a_25(f, jugadors[dins], fps)
        propera = np.clip(np.floor(nous - f[0] + 0.5).astype(int), 0, len(f) - 1)
        trossos.append((np.full(len(nous), part), pil, jug, veritat[dins][propera]))
    periode25 = np.concatenate([t[0] for t in trossos])
    pil = np.concatenate([t[1] for t in trossos])
    jug = np.concatenate([t[2] for t in trossos])
    veritat25 = np.concatenate([t[3] for t in trossos])
    veritat25[~np.isfinite(jug[..., 0]).any(axis=1)] = pm.X
    centre = np.array([llarg / 2, ample / 2])
    escala = np.array([llarg, ample])
    k = casa.shape[1]
    tracking = Tracking(
        fotograma=np.arange(len(periode25)), pilota=(pil[:, :2] + centre) / escala,
        casa=(jug[:, :k] + centre) / escala, fora=(jug[:, k:] + centre) / escala,
        nom_casa=str(fitxa["homeTeam"]["shortName"]), nom_fora=str(fitxa["awayTeam"]["shortName"]),
        casa_es_home=True, camp_m=(llarg, ample))
    return PartitBanc(nom=f"pff-{partit}", font="pff", tracking=tracking, trams=trams_de_parts(periode25),
                      veritat=veritat25, pilota_z=pil[:, 2])
