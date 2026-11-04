"""Lectura de l'ATD tàctic (FIFA/EPTS, amb kloppy) a arrays de numpy.

Les dades es tracten com a no fiables: només es llegeixen com a text i números.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from cadena.norma import FITXERS_ATD


class ErrorDeLectura(Exception):
    """Les dades no són com diuen les normes. El missatge és un text fix, sense cap dada: pot sortir a la consola."""


@dataclass(frozen=True)
class Tracking:
    fotograma: np.ndarray        # (n,) fotograma del vídeo: el frame_id de l'ATD menys u (DATA.md)
    pilota: np.ndarray           # (n, 2) coordenades 0-1, NaN si no hi és
    casa: np.ndarray             # (n, k, 2) els slots de l'equip H
    fora: np.ndarray             # (n, m, 2) els slots de l'equip A
    nom_casa: str
    nom_fora: str
    casa_es_home: bool           # si les metadades també el marquen com a equip de casa
    camp_m: tuple[float, float]


def localitza(dades: Path) -> tuple[Path, Path]:
    """Les metadades i les dades de l'ATD tàctic, pel nom exacte de DATA.md."""
    camins = []
    for nom in FITXERS_ATD:
        trobats = [c for c in dades.rglob(nom) if c.is_file()]
        if not trobats:
            raise ErrorDeLectura(f"No trobo l'ATD tàctic ({nom})")
        if len(trobats) > 1:
            raise ErrorDeLectura(f"Hi ha més d'un {nom}")
        camins.append(trobats[0])
    return camins[0], camins[1]


def tracking(meta: Path, raw: Path, casa: str) -> Tracking:
    """L'equip H és el que porta `casa` al nom; si no n'hi ha exactament un, s'atura."""
    from kloppy import metrica

    dataset = metrica.load_tracking_epts(meta_data=str(meta), raw_data=str(raw))
    df = dataset.to_df()
    equips = list(dataset.metadata.teams)
    de_casa = [e for e in equips if casa.lower() in str(e.name).lower()]
    if len(de_casa) != 1 or len(equips) != 2:
        raise ErrorDeLectura(f"No trobo un sol equip de casa («{casa}») a les metadades de l'ATD")
    h = de_casa[0]
    a = next(e for e in equips if e is not h)

    def posicions(equip) -> np.ndarray:
        ids = [str(p.player_id) for p in equip.players if f"{p.player_id}_x" in df]
        return np.stack([df[[f"{i}_x" for i in ids]].to_numpy(float),
                         df[[f"{i}_y" for i in ids]].to_numpy(float)], axis=-1)

    camp = dataset.metadata.pitch_dimensions
    return Tracking(
        fotograma=df["frame_id"].to_numpy(np.int64) - 1,
        pilota=df[["ball_x", "ball_y"]].to_numpy(float),
        casa=posicions(h), fora=posicions(a),
        nom_casa=str(h.name), nom_fora=str(a.name),
        casa_es_home=str(getattr(h.ground, "value", h.ground)) == "home",
        camp_m=(float(camp.pitch_length), float(camp.pitch_width)),
    )
