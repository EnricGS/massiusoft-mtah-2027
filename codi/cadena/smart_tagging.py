"""El Smart Tagging del partit, de dades d'entrada: les pilotes aturades (T3af del pla per tocs, `docs/pla-tocs.md`,
«T3af»; D-68).

El Smart Tagging és l'anotació automàtica de Metrica del vídeo tàctic (DATA.md, «Smart Tagging»): un fitxer SportsCode
amb intervals, cadascun amb un codi i unes etiquetes. Aquí només es fan servir els de pilota aturada (`SET PIECES`):
cada un és una represa, i cada represa acaba una estona de pilota morta. Les fases (Build Up, Progression…) no hi van.

- **La lectura** (`llegeix`), amb kloppy. Els segons passen a imatges amb `round(segons × 25)` (DATA.md). L'equip
  «Barcelona» és l'H i «Atletic Club» és l'A, sense distingir majúscules; «N/A», cap. Els tipus són els de DATA.md, i
  els codis es comparen sense distingir majúscules. El que no coneix es deixa, amb un avís de text fix (`AVIS_*`): un
  codi, un tipus o un equip desconeguts. Si el fitxer no hi és o és mal fet, `ErrorDeLectura` amb un text fix. Cap
  missatge no porta res del fitxer.
- **Les columnes del segon** (`columnes`), a cada imatge, dins de la seva part:
  - de l'etiqueta més propera d'abans (la darrera que comença en aquesta imatge o abans) i de la més propera de després
    (la primera que comença més tard), a `FINESTRA_S` o menys: quants segons hi ha entre la imatge i l'inici, el tipus
    (una columna per tipus) i l'equip (`_h` i `_a`, totes dues a 0 si no en té). Sense cap etiqueta a `FINESTRA_S` o
    menys, NaN;
  - `st_dins`: si la imatge és dins d'una etiqueta (de l'inici al final, tots dos inclosos).

  Fora de les parts, tot NaN. Cap finestra passa d'una part a l'altra, i una etiqueta és de la part on comença; les que
  no comencen dins de cap part no hi són. Girar els equips (`senyals.intercanvia`) només intercanvia les de l'equip.

Al banc, les etiquetes simulades (`banc/smart_tagging_simulat.py`) passen per les mateixes `columnes`.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd

from cadena import norma
from cadena.llegeix import ErrorDeLectura
from possessio.oficial import possession_metrics as pm

FITXER = f"{norma.PARTIT}_tactical_smart_tagging.xml"          # DATA.md, a `data/tactical/`
FPS = pm.FPS
FINESTRA_S = 20
CODI = "set pieces"
CODIS = {CODI, "players in the box", "ball in final third", "ball in the box", "progression",   # DATA.md
         "defending in middle third", "creating chances", "defending in defensive third", "long ball",
         "attacking transition", "defensive transition", "build up", "defending in attacking third", "goals"}
TIPUS = ("banda", "corner", "porta", "falta", "sortida")
DEL_FITXER = {"throw-in": "banda", "corner kick": "corner", "goal kick": "porta", "free kick": "falta",
              "kick off (after goal)": "sortida", "kick off (start)": "sortida"}
EQUIPS = {norma.EQUIP_CASA: pm.H, "atletic club": pm.A}
SENSE_EQUIP = "n/a"
AVIS_CODI = "⚠ Smart Tagging: un codi que DATA.md no diu; es deixa"
AVIS_TIPUS = "⚠ Smart Tagging: una pilota aturada d'un tipus que DATA.md no diu, o sense tipus; es deixa"
AVIS_EQUIP = "⚠ Smart Tagging: una pilota aturada d'un equip que no és cap dels dos; va sense equip"
QUANS = ("abans", "despres")
COLUMNES = (*(f"st_{q}_{k}" for q in QUANS for k in ("s", *TIPUS, "equip_h", "equip_a")), "st_dins")


class Etiqueta(NamedTuple):
    inici: int              # imatge del vídeo tàctic
    final: int              # inclosa
    tipus: str              # un de TIPUS
    equip: int | None       # pm.H, pm.A o cap


def imatge(segons: float) -> int:
    return int(round(segons * FPS))


def llegeix(cami: Path) -> tuple[tuple[Etiqueta, ...], tuple[str, ...]]:
    """Les pilotes aturades del fitxer, en l'ordre del fitxer, i els avisos."""
    from kloppy import sportscode

    if not Path(cami).is_file():
        raise ErrorDeLectura(f"No trobo el Smart Tagging ({FITXER})")
    try:
        codis = sportscode.load(str(cami)).records
        crues = [(str(c.code).strip().lower(), {str(k).strip().lower(): str(v).strip() for k, v in c.labels.items()},
                  (c.period.start_timestamp + c.timestamp).total_seconds(),
                  (c.period.start_timestamp + c.end_timestamp).total_seconds()) for c in codis]
    except Exception as e:                                    # el text de l'excepció pot portar el que diu el fitxer
        raise ErrorDeLectura("El Smart Tagging no es pot llegir: no és un fitxer SportsCode com diu DATA.md") from e
    etiquetes, avisos = [], []
    for codi, etiquetes_, inici, final in crues:
        if codi != CODI:
            if codi not in CODIS:
                avisos.append(AVIS_CODI)
            continue
        tipus = DEL_FITXER.get(etiquetes_.get("type", "").lower())
        if tipus is None:
            avisos.append(AVIS_TIPUS)
            continue
        nom = etiquetes_.get("team", SENSE_EQUIP).lower()
        if nom != SENSE_EQUIP and nom not in EQUIPS:
            avisos.append(AVIS_EQUIP)
        etiquetes.append(Etiqueta(imatge(inici), imatge(final), tipus, EQUIPS.get(nom)))
    return tuple(etiquetes), tuple(avisos)


def _de_l_etiqueta(e: Etiqueta) -> list[float]:
    return [*(float(e.tipus == t) for t in TIPUS), float(e.equip == pm.H), float(e.equip == pm.A)]


def columnes(etiquetes: tuple[Etiqueta, ...], n: int, trams: tuple[tuple[int, int, int], ...]) -> pd.DataFrame:
    """Les `COLUMNES` a cada una de les `n` imatges."""
    finestra = FINESTRA_S * FPS
    valors = {q: np.full((n, 1 + len(TIPUS) + 2), np.nan) for q in QUANS}
    dins = np.full(n, np.nan)
    for _, a, b in trams:
        dins[a:b + 1] = 0.0
        seves = sorted((e for e in etiquetes if a <= e.inici <= b), key=lambda e: e.inici)
        for i, e in enumerate(seves):
            dins[e.inici:min(e.final, b) + 1] = 1.0
            fi = min(e.inici + finestra, b, seves[i + 1].inici - 1 if i + 1 < len(seves) else b)
            # abans: de l'inici fins a la propera que comença (si dues comencen igual, mana la segona)
            k = np.arange(e.inici, fi + 1)
            valors["abans"][k] = np.c_[(k - e.inici) / FPS, np.tile(_de_l_etiqueta(e), (len(k), 1))]
            # després: de la que comença abans (si n'hi ha) fins a la imatge d'abans de l'inici
            de = max(e.inici - finestra, a, seves[i - 1].inici if i > 0 else a)
            k = np.arange(de, e.inici)
            valors["despres"][k] = np.c_[(e.inici - k) / FPS, np.tile(_de_l_etiqueta(e), (len(k), 1))]
    noms = [f"st_{q}_{k}" for q in QUANS for k in ("s", *TIPUS, "equip_h", "equip_a")]
    taula = pd.DataFrame(np.c_[valors["abans"], valors["despres"]], columns=noms)
    taula["st_dins"] = dins
    return taula[list(COLUMNES)]
