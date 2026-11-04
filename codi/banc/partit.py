"""Un partit del banc: el tracking igual que el de la cadena, les parts i la veritat per imatge.

El tracking és un `cadena.llegeix.Tracking`, amb les coordenades 0-1 de l'ATD: així el que es tria al banc és
exactament el que després corre sobre les dades del concurs. Cada fila és una imatge (25 per segon), i el
`fotograma` és l'índex de la fila.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from cadena.llegeix import Tracking
from possessio.oficial import possession_metrics as pm

VERSIO = 1          # si canvia el que es desa, la memòria cau es refà


@dataclass(frozen=True)
class PartitBanc:
    nom: str
    font: str                                   # «dfl» o «metrica»
    tracking: Tracking
    trams: tuple[tuple[int, int, int], ...]     # (part, primera fila, última), incloses, com TRAMS_PUNTUATS
    veritat: np.ndarray                         # (n,) codis de la mètrica oficial: pm.H, pm.A, pm.D o pm.X
    pilota_z: np.ndarray                        # (n,) alçada de la pilota en metres; NaN si la font no en dona

    @property
    def n(self) -> int:
        return len(self.veritat)


def trams_de_parts(periode: np.ndarray) -> tuple[tuple[int, int, int], ...]:
    """(part, primera fila, última) de cada part, que han de ser seguides."""
    vores = np.flatnonzero(np.diff(periode) != 0) + 1
    inicis, finals = np.r_[0, vores], np.r_[vores, len(periode)] - 1
    if len(set(periode[inicis].tolist())) != len(inicis):
        raise ValueError("Una part surt en dos trossos")
    return tuple((int(periode[a]), int(a), int(b)) for a, b in zip(inicis, finals))


def valida(p: PartitBanc) -> None:
    t, n = p.tracking, p.n
    if not np.array_equal(t.fotograma, np.arange(n)):
        raise ValueError(f"{p.nom}: el fotograma ha de ser l'índex de la fila")
    if t.pilota.shape != (n, 2) or t.casa.shape[0] != n or t.fora.shape[0] != n or p.pilota_z.shape != (n,):
        raise ValueError(f"{p.nom}: mides que no quadren")
    if not set(np.unique(p.veritat).tolist()) <= {pm.H, pm.A, pm.D, pm.X}:
        raise ValueError(f"{p.nom}: codis de veritat desconeguts")
    if p.trams[0][1] != 0 or p.trams[-1][2] != n - 1 or any(a[2] + 1 != b[1] for a, b in zip(p.trams, p.trams[1:])):
        raise ValueError(f"{p.nom}: les parts no cobreixen el partit d'un cap a l'altre")


def desa(p: PartitBanc, cami: Path) -> None:
    """En npz sense compressió (es llegeix en un segon) i sense pickle; primer a un temporal al costat."""
    valida(p)
    t = p.tracking
    temporal = cami.with_name(cami.name + ".part.npz")
    np.savez(temporal, versio=VERSIO, nom=p.nom, font=p.font, trams=np.array(p.trams, np.int64),
             veritat=p.veritat.astype(np.int8), pilota_z=p.pilota_z.astype(np.float32),
             pilota=t.pilota.astype(np.float32), casa=t.casa.astype(np.float32), fora=t.fora.astype(np.float32),
             nom_casa=t.nom_casa, nom_fora=t.nom_fora, camp_m=np.array(t.camp_m, float))
    temporal.replace(cami)


def carrega(cami: Path) -> PartitBanc | None:
    """None si el fitxer és d'una altra versió."""
    with np.load(cami, allow_pickle=False) as z:
        if int(z["versio"]) != VERSIO:
            return None
        n = len(z["veritat"])
        tracking = Tracking(
            fotograma=np.arange(n), pilota=z["pilota"].astype(float), casa=z["casa"].astype(float),
            fora=z["fora"].astype(float), nom_casa=str(z["nom_casa"]), nom_fora=str(z["nom_fora"]),
            casa_es_home=True, camp_m=tuple(float(x) for x in z["camp_m"]))
        trams = tuple(tuple(int(x) for x in fila) for fila in z["trams"])
        return PartitBanc(nom=str(z["nom"]), font=str(z["font"]), tracking=tracking, trams=trams,
                          veritat=z["veritat"].astype(np.int8), pilota_z=z["pilota_z"].astype(float))
