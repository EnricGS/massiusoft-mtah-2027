"""Lectura de l'ATD (amb kloppy) i de la homografia a arrays de numpy.

Les dades es tracten com a no fiables: només es llegeixen com a text i números,
i mai no s'executa res del seu contingut.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Tracking:
    font: str
    frame_id: np.ndarray                 # (n,) tal com ve a l'ATD
    pilota: np.ndarray                   # (n, 2) coordenades 0-1, NaN si no hi és
    pilota_z: np.ndarray | None          # (n,) si l'ATD en porta
    equips: tuple[str, ...]              # noms dels equips de les metadades
    terrenys: tuple[str, ...]            # «home» / «away» segons kloppy
    slots: tuple[tuple[str, ...], ...]   # ids dels slots de cada equip
    jugadors: tuple[np.ndarray, ...]     # per equip, (n, k, 2) coordenades 0-1
    camp_metadades: tuple[float, float]
    fps: float
    altres_columnes: pd.DataFrame        # columnes que no són de jugadors ni de la pilota

    @property
    def n(self) -> int:
        return len(self.frame_id)

    @property
    def frame_video(self) -> np.ndarray:
        return self.frame_id - 1


@dataclass(frozen=True)
class Homografia:
    font: str
    frame: np.ndarray        # (n,) índex del fotograma del vídeo
    matrius: np.ndarray      # (n, 3, 3), NaN on no és vàlida
    error: np.ndarray        # (n,) error de reprojecció
    valida: np.ndarray       # (n,) bool

    def de_frames(self, frames: np.ndarray) -> np.ndarray:
        """Matrius dels fotogrames demanats (NaN si el fotograma no hi és)."""
        posicio = np.searchsorted(self.frame, frames)
        posicio = np.clip(posicio, 0, len(self.frame) - 1)
        matrius = self.matrius[posicio].copy()
        matrius[self.frame[posicio] != frames] = np.nan
        return matrius


def tracking(meta: Path, raw: Path, font: str) -> Tracking:
    from kloppy import metrica

    dataset = metrica.load_tracking_epts(meta_data=str(meta), raw_data=str(raw))
    df = dataset.to_df()
    equips, terrenys, slots, jugadors, usades = [], [], [], [], set()
    for equip in dataset.metadata.teams:
        ids = tuple(str(p.player_id) for p in equip.players if f"{p.player_id}_x" in df)
        equips.append(str(equip.name))
        terrenys.append(str(getattr(equip.ground, "value", equip.ground)))
        slots.append(ids)
        jugadors.append(np.stack([df[[f"{i}_x" for i in ids]].to_numpy(float),
                                  df[[f"{i}_y" for i in ids]].to_numpy(float)], axis=-1))
        usades |= {f"{i}_{s}" for i in ids for s in ("x", "y", "d", "s")}
    usades |= {"ball_x", "ball_y", "frame_id"}
    camp = dataset.metadata.pitch_dimensions
    return Tracking(
        font=font,
        frame_id=df["frame_id"].to_numpy(np.int64),
        pilota=df[["ball_x", "ball_y"]].to_numpy(float),
        pilota_z=df["ball_z"].to_numpy(float) if df.get("ball_z", pd.Series()).notna().any() else None,
        equips=tuple(equips), terrenys=tuple(terrenys), slots=tuple(slots),
        jugadors=tuple(jugadors),
        camp_metadades=(float(camp.pitch_length or np.nan), float(camp.pitch_width or np.nan)),
        fps=float(dataset.metadata.frame_rate),
        altres_columnes=df[[c for c in df.columns if c not in usades]],
    )


def homografia(cami: Path, font: str) -> Homografia:
    df = pd.read_csv(cami)
    columnes = [f"h{f}{c}" for f in range(3) for c in range(3)]
    valida = df["valid"].fillna(0).astype(int).to_numpy() == 1
    matrius = df[columnes].to_numpy(float).reshape(-1, 3, 3)
    matrius[~valida] = np.nan
    return Homografia(font, df["frame"].to_numpy(np.int64), matrius,
                      df["reprojection_error"].to_numpy(float), valida)


def projecta(matrius: np.ndarray, x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Coordenades del camp (0-1) a píxels; `matrius` (n, 3, 3), `x` i `y` (n,) o (n, k)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    forma = x.shape
    k = int(np.prod(forma[1:]))
    x2 = x.reshape(forma[0], k)
    y2 = y.reshape(forma[0], k)
    punts = np.stack([x2, y2, np.ones_like(x2)], axis=1)          # (n, 3, k)
    imatge = matrius @ punts                                       # (n, 3, k)
    with np.errstate(invalid="ignore", divide="ignore"):
        u, v = imatge[:, 0] / imatge[:, 2], imatge[:, 1] / imatge[:, 2]
    return u.reshape(forma), v.reshape(forma)


def estructura_xml(cami: Path) -> tuple[dict[str, int], list[tuple[str, str]], list[str]]:
    """Etiquetes de les metadades i quantes n'hi ha, els paràmetres del proveïdor i els canals."""
    arrel = ET.parse(cami).getroot()
    etiquetes: dict[str, int] = {}
    for element in arrel.iter():
        etiquetes[element.tag] = etiquetes.get(element.tag, 0) + 1
    parametres = [((p.findtext("Name") or "").strip(), (p.findtext("Value") or "").strip())
                  for p in arrel.iter("ProviderParameter")]
    canals = sorted({c.get("id", "") for c in arrel.iter("Channel")})
    return etiquetes, parametres, canals
