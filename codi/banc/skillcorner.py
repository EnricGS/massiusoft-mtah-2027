"""Un partit de SkillCorner Open Data (A-League 2024/25, MIT) al format del banc, per entrenar (T3l del pla per tocs,
`docs/pla-tocs.md`, «T3l»). No es prova mai: només n'aprenen els models.

El tracking és de la retransmissió, a 10 imatges per segon. La veritat és de la mateixa mena que la de DFL:
- **D** fora de les fases de joc (`_phases_of_play.csv`: només hi són amb la pilota viva);
- dins, l'equip que té la possessió segons el tracking (`possession.group`), i on no en diu cap (una passada), el de
  l'última de la mateixa fase; abans de la primera de cada fase, **X** (no s'aprèn).

A 25 imatges per segon, dins de cada part: les posicions, interpolades en línia recta entre dues imatges de
SkillCorner seguides; la pilota, només entre dues on es veu (`is_detected`); els jugadors, també on són estimats
(fora de la imatge). Cada imatge pren la veritat de la imatge de SkillCorner més propera.

On el tracking no té cap jugador (les repeticions de la retransmissió, gairebé sempre amb la pilota morta), la veritat
és X: no s'aprèn. Al concurs, el tracking hi és sempre, i el model no ha d'aprendre que una imatge buida és D.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from banc.partit import PartitBanc, trams_de_parts
from cadena.llegeix import Tracking
from possessio.oficial import possession_metrics as pm

FPS_FONT = 10
FPS = 25
PARTS = (1, 2)
EQUIP = {"home team": pm.H, "away team": pm.A}


def fitxers(carpeta: Path, partit: int) -> tuple[Path, Path, Path]:
    d = carpeta / "matches" / str(partit)
    return d / f"{partit}_match.json", d / f"{partit}_tracking_extrapolated.jsonl", d / f"{partit}_phases_of_play.csv"


def veritat_font(periode: np.ndarray, frame: np.ndarray, grup: np.ndarray,
                 fases: list[tuple[int, int]]) -> np.ndarray:
    """A cada imatge de SkillCorner: D fora de les fases; dins, l'equip de `grup` (pm.H, pm.A o -1 si no en diu cap),
    el de l'última de la fase on no en diu cap, i X abans de la primera de la fase."""
    out = np.full(len(frame), pm.D, dtype=np.int8)
    for inici, final in sorted(fases):
        dins = np.flatnonzero((frame >= inici) & (frame <= final))
        darrer = pm.X
        for i in dins:
            if grup[i] >= 0:
                darrer = grup[i]
            out[i] = darrer
    out[~np.isin(periode, PARTS)] = pm.X
    return out


def a_25(frame: np.ndarray, valors: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """D'una part a 10 imatges per segon (`frame` seguits) a 25: els temps nous (en imatges de la font) i els valors
    interpolats en línia recta, NaN si a qualsevol de les dues imatges del costat ho és."""
    if np.any(np.diff(frame) != 1):
        raise ValueError("Falten imatges dins d'una part")
    ratio = FPS / FPS_FONT
    nous = np.arange(int(np.ceil(frame[0] * ratio)), int(np.floor(frame[-1] * ratio)) + 1) / ratio
    u = nous - frame[0]
    i = np.minimum(np.floor(u).astype(int), len(frame) - 2)
    t = (u - i).reshape((-1,) + (1,) * (valors.ndim - 1))
    return nous, (1 - t) * valors[i] + t * valors[i + 1]


def llegeix(carpeta: Path, partit: int) -> PartitBanc:
    cami_fitxa, cami_tracking, cami_fases = fitxers(carpeta, partit)
    fitxa = json.loads(cami_fitxa.read_text())
    llarg, ample = float(fitxa["pitch_length"]), float(fitxa["pitch_width"])
    id_casa = fitxa["home_team"]["id"]
    equip_de = {j["id"]: j["team_id"] for j in fitxa["players"]}
    casa_ids = sorted(j for j, e in equip_de.items() if e == id_casa)
    fora_ids = sorted(j for j, e in equip_de.items() if e != id_casa)
    columna = {j: k for k, j in enumerate(casa_ids + fora_ids)}

    files = [json.loads(linia) for linia in cami_tracking.read_text().splitlines() if linia.strip()]
    files = [f for f in files if f["period"] in PARTS]
    n = len(files)
    frame = np.array([f["frame"] for f in files], dtype=np.int64)
    periode = np.array([f["period"] for f in files], dtype=np.int64)
    pilota = np.full((n, 3), np.nan)
    jugadors = np.full((n, len(columna), 2), np.nan)
    grup = np.full(n, -1, dtype=np.int8)
    for i, f in enumerate(files):
        b = f["ball_data"]
        if b["is_detected"] and b["x"] is not None:
            pilota[i] = (b["x"], b["y"], np.nan if b["z"] is None else b["z"])
        grup[i] = EQUIP.get(f["possession"]["group"], -1)
        for j in f["player_data"]:
            if j["player_id"] in columna and j["x"] is not None:
                jugadors[i, columna[j["player_id"]]] = (j["x"], j["y"])
    fases = _fases(cami_fases)
    veritat = veritat_font(periode, frame, grup, fases)

    trossos = []
    for part in PARTS:
        dins = np.flatnonzero(periode == part)
        if not len(dins):
            raise ValueError(f"skillcorner-{partit}: falta la part {part}")
        f = frame[dins]
        nous, pil = a_25(f, pilota[dins])
        _, jug = a_25(f, jugadors[dins])
        propera = np.clip(np.floor(nous - f[0] + 0.5).astype(int), 0, len(f) - 1)
        trossos.append((np.full(len(nous), part), pil, jug, veritat[dins][propera]))
    periode25 = np.concatenate([t[0] for t in trossos])
    pil = np.concatenate([t[1] for t in trossos])
    jug = np.concatenate([t[2] for t in trossos])
    veritat25 = np.concatenate([t[3] for t in trossos])
    veritat25[~np.isfinite(jug[..., 0]).any(axis=1)] = pm.X
    centre = np.array([llarg / 2, ample / 2])
    escala = np.array([llarg, ample])
    m = len(periode25)
    tracking = Tracking(
        fotograma=np.arange(m), pilota=(pil[:, :2] + centre) / escala,
        casa=(jug[:, :len(casa_ids)] + centre) / escala, fora=(jug[:, len(casa_ids):] + centre) / escala,
        nom_casa=str(fitxa["home_team"]["short_name"]), nom_fora=str(fitxa["away_team"]["short_name"]),
        casa_es_home=True, camp_m=(llarg, ample))
    return PartitBanc(nom=f"skillcorner-{partit}", font="skillcorner", tracking=tracking,
                      trams=trams_de_parts(periode25), veritat=veritat25,
                      pilota_z=pil[:, 2])


def _fases(cami: Path) -> list[tuple[int, int]]:
    import pandas as pd

    f = pd.read_csv(cami, usecols=["frame_start", "frame_end"])
    return [(int(a), int(b)) for a, b in zip(f["frame_start"], f["frame_end"])]
