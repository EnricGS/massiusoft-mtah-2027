"""Els senyals del darrer contacte per al classificador d'A (T3h del pla per tocs, `docs/pla-tocs.md`, «T3h»).

Els tocs de `control.py` es dedueixen d'un canvi de velocitat de la pilota, i amb soroll el detector se n'inventa i
se'n deixa. Aquests ho diuen per proximitat: a cada imatge amb la pilota, un jugador hi és en contacte si és a `r` m
o menys, i si n'hi ha dels dos equips compta l'equip del més proper. Un contacte són les imatges seguides amb el
mateix equip en contacte. Sense la pilota no n'hi ha, i el darrer es porta endavant. Per a cada radi de `RADIS_M`:

- l'equip del darrer contacte (fins a la imatge, inclosa), el del proper (després) i el del penúltim;
- quant fa que ha acabat el darrer (0 si hi ha contacte) i quant falta perquè comenci el proper, en segons;
- quant ha durat el darrer i quant durarà el proper, en segons: un toc de pas o una conducció;
- a la darrera imatge del darrer, la distància del jugador més proper de cada equip: si l'altre també hi era, era
  disputat.

Segueixen la convenció de `senyals.py` (`_h` i `_a` per equip, `dif_` per a H − A), i per això `senyals.intercanvia`
també els gira. Cap senyal passa d'una part a l'altra, i fora de les parts són NaN.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cadena import senyals
from cadena.llegeix import Tracking

FPS = senyals.FPS
RADIS_M = (1.0, 2.0)


def calcula(t: Tracking, trams: tuple[tuple[int, int, int], ...]) -> pd.DataFrame:
    """Una fila per imatge (float32), amb el tracking en una fila per imatge (`senyals.a_reixa`)."""
    n = len(t.fotograma)
    if not np.array_equal(t.fotograma, np.arange(n)):
        raise ValueError("Els senyals volen una fila per imatge: primer, a_reixa")
    if not trams:
        raise ValueError("No hi ha cap part")
    escala = np.asarray(t.camp_m, float)
    trossos = []
    for _, inici, fi in trams:
        part = slice(inici, fi + 1)
        pilota = t.pilota[part] * escala
        d_h, d_a = _mes_proper(t.casa[part] * escala, pilota), _mes_proper(t.fora[part] * escala, pilota)
        f = {}
        for r in RADIS_M:
            f |= _contactes(d_h, d_a, r, f"contacte{r:g}")
        trossos.append(pd.DataFrame(f).set_axis(pd.RangeIndex(inici, fi + 1)))
    return pd.concat(trossos).reindex(pd.RangeIndex(n)).astype(np.float32)


# --- una part ---------------------------------------------------------------------------------------------------

def _mes_proper(jugadors: np.ndarray, pilota: np.ndarray) -> np.ndarray:
    """La distància del jugador de l'equip més proper a la pilota; inf si no es veu la pilota o cap jugador."""
    d = np.linalg.norm(jugadors - pilota[:, None, :], axis=2)
    return np.where(np.isnan(d), np.inf, d).min(axis=1)


def _contactes(d_h: np.ndarray, d_a: np.ndarray, r: float, nom: str) -> dict[str, np.ndarray]:
    n = len(d_h)
    equip = np.where(np.minimum(d_h, d_a) <= r, np.where(d_h <= d_a, 1, -1), 0)        # +1 H, −1 A, 0 cap
    canvia = np.r_[True, equip[1:] != equip[:-1]]
    inici = np.flatnonzero((equip != 0) & canvia)
    fi = np.flatnonzero((equip != 0) & np.r_[canvia[1:], True])                         # la darrera, inclosa
    comencats = np.cumsum((equip != 0) & canvia)
    darrer = comencats - 1                                                              # −1 si encara no n'hi ha
    proper = np.where(comencats < len(inici), comencats, -1)
    idx = np.arange(n)
    ultima = senyals._ultima(equip != 0)
    sostre = senyals.TOPALL_S
    signe, durada = equip[inici].astype(float), (fi - inici + 1) / FPS
    return {
        f"dif_{nom}_abans": _del(signe, darrer),
        f"dif_{nom}_despres": _del(signe, proper),
        f"dif_{nom}_penultim": _del(signe, np.where(darrer >= 1, darrer - 1, -1)),
        f"{nom}_des": np.where(ultima >= 0, np.minimum((idx - ultima) / FPS, sostre), sostre),
        f"{nom}_fins": np.where(proper >= 0, np.minimum((_del(inici, proper) - idx) / FPS, sostre), sostre),
        f"{nom}_durada_abans": _del(durada, darrer),
        f"{nom}_durada_despres": _del(durada, proper),
        f"{nom}_d_abans_h": np.minimum(_del(d_h[fi], darrer), senyals.TOPALL_M),
        f"{nom}_d_abans_a": np.minimum(_del(d_a[fi], darrer), senyals.TOPALL_M),
    }


def _del(valors: np.ndarray, quin: np.ndarray) -> np.ndarray:
    """El valor del contacte número `quin` a cada imatge, i NaN on `quin` és −1."""
    if not len(valors):
        return np.full(len(quin), np.nan)
    return np.where(quin >= 0, np.asarray(valors, float)[np.maximum(quin, 0)], np.nan)
