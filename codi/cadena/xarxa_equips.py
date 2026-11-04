"""Les xarxes veuen els dos equips sencers (T3v del pla per tocs, `docs/pla-tocs.md`, «T3v»; D-54).

Les xarxes d'A sense pilota (`xarxa_sense_pilota.py`) veuen tres jugadors de cada equip, els més propers a la pilota o
a la pilota estimada. Aquí també veuen tots els jugadors dels dos equips:

- **Els equips** (`equips`, 90 valors per imatge), en metres des del mig del camp i girats com a `xarxa.py` (l'equip
  de casa ataca cap a les x positives):
  - de cada equip, `ONZE` jugadors amb on són (x, y) i la seva velocitat (vx, vy), calculada com a `xarxa.py`, a cada
    slot;
  - ordenats del més a prop de la seva porteria al més a prop de la contrària: els de casa, de menys x a més, i els de
    fora, de més x a menys. Així, girar els equips dona exactament el bloc de l'altre equip, canviat de signe;
  - si se'n veuen menys d'11, els que falten són al mig dels que es veuen (la mitjana) i quiets, i s'ordenen amb els
    altres; si no se'n veu cap, tots a 0;
  - si se'n veuen més d'11 (duplicats), es treu cada vegada el que és més a prop d'un altre del seu equip (a la mateixa
    distància, el primer slot), fins que en queden 11 (`sense_duplicats`);
  - de cada equip, quants se'n veuen (abans de treure'n els duplicats).
- **La finestra** (`finestra`): els 31 valors de `xarxa_sense_pilota.canals` a les 25 imatges de `xarxa.DESPLACAMENTS`,
  i els 90 dels equips a les 9 de `DESPLACAMENTS_EQUIPS`, fins als mateixos ±2 s: 775 + 810 = 1.585 valors. Fora de la
  part de la imatge, 0.
- **L'entrenament i les probabilitats,** els de `xarxes.py` amb aquesta finestra (`mostres`, `probabilitats`).

`xarxa.py`, `xarxes.py` i `xarxa_sense_pilota.py` no es toquen: la cadena d'ara i el banc de la T3t els fan servir.
"""

from __future__ import annotations

import numpy as np

from cadena import senyals, xarxa
from cadena import xarxa_sense_pilota as xsp
from cadena.llegeix import Tracking
from cadena.model import CLASSES, GIRA

ONZE = 11
PER_JUGADOR = 4                                     # x, y, vx i vy
PER_EQUIP = ONZE * PER_JUGADOR + 1                  # i quants se'n veuen
CANALS = 2 * PER_EQUIP
DESPLACAMENTS_EQUIPS = (-50, -25, -12, -6, 0, 6, 12, 25, 50)
ENTRADES = xsp.CANALS * len(xarxa.DESPLACAMENTS) + CANALS * len(DESPLACAMENTS_EQUIPS)
Trams = xsp.Trams


def equips(t: Tracking, trams: Trams) -> np.ndarray:
    """(n, 90) float32: els dos equips a cada imatge, primer el de casa. Fora de les parts, 0."""
    n = len(t.fotograma)
    if not np.array_equal(t.fotograma, np.arange(n)):
        raise ValueError("La xarxa vol una fila per imatge: primer, a_reixa")
    if not trams:
        raise ValueError("No hi ha cap part")
    escala = np.asarray(t.camp_m, float)
    out = np.zeros((n, CANALS), np.float32)
    for _, inici, fi in trams:
        part = slice(inici, fi + 1)
        casa, fora = t.casa[part] * escala, t.fora[part] * escala
        casa_x, fora_x = np.nanmedian(senyals._mitjana(casa[..., 0])), np.nanmedian(senyals._mitjana(fora[..., 0]))
        sentit = 1.0 if casa_x <= fora_x else -1.0              # com a `xarxa._una_part`
        centre = escala / 2
        out[part] = np.concatenate([un_equip((casa - centre) * sentit, 1.0),
                                    un_equip((fora - centre) * sentit, -1.0)], axis=1)
    return out


def un_equip(jug: np.ndarray, cap: float) -> np.ndarray:
    """(n, 45): els `ONZE` jugadors d'un equip, ordenats de la seva porteria a la contrària (`cap`: 1 si ataca cap a
    les x positives, −1 si no), cadascun amb x, y, vx i vy, i al final quants se'n veuen. `jug`, (n, slots, 2), ja
    girat."""
    n = len(jug)
    if jug.shape[1] < ONZE:
        jug = np.concatenate([jug, np.full((n, ONZE - jug.shape[1], 2), np.nan)], axis=1)
    vel = xarxa._velocitat(jug)
    vist = ~np.isnan(jug).any(axis=2)
    quants = vist.sum(axis=1)
    vist = sense_duplicats(jug, vist)
    files = np.arange(n)[:, None]
    tria = np.argsort(~vist, axis=1, kind="stable")[:, :ONZE]     # els vistos, i tants dels altres com en falten
    pos, v, de_debo = jug[files, tria], vel[files, tria], vist[files, tria]
    k = de_debo.sum(axis=1)[:, None]
    mig = np.where(k > 0, np.where(de_debo[..., None], pos, 0.0).sum(axis=1) / np.maximum(k, 1), 0.0)
    pos = np.where(de_debo[..., None], pos, mig[:, None, :])
    v = np.where(de_debo[..., None], v, 0.0)
    ordre = np.argsort(cap * pos[..., 0], axis=1, kind="stable")
    jugadors = np.concatenate([pos[files, ordre], v[files, ordre]], axis=2)
    return np.concatenate([jugadors.reshape(n, ONZE * PER_JUGADOR), quants[:, None]], axis=1)


def sense_duplicats(jug: np.ndarray, vist: np.ndarray) -> np.ndarray:
    """`vist` sense els que sobren d'`ONZE` a cada imatge: es treu cada vegada el vist que és més a prop d'un altre
    vist (a la mateixa distància, el primer slot)."""
    vist = vist.copy()
    massa = np.flatnonzero(vist.sum(axis=1) > ONZE)
    lluny_d_ell = ~np.eye(jug.shape[1], dtype=bool)
    for s in range(0, len(massa), xarxa.TROS):
        f = massa[s:s + xarxa.TROS]
        p = jug[f]
        d = np.hypot(p[:, :, None, 0] - p[:, None, :, 0], p[:, :, None, 1] - p[:, None, :, 1])
        v = vist[f]
        while (sobren := v.sum(axis=1) > ONZE).any():
            proper = np.where(v[:, :, None] & v[:, None, :] & lluny_d_ell, d, np.inf).min(axis=2)
            treu = np.argmin(proper, axis=1)
            v[np.flatnonzero(sobren), treu[sobren]] = False
        vist[f] = v
    return vist


def finestra(c: np.ndarray, e: np.ndarray, trams: Trams, files: np.ndarray) -> np.ndarray:
    """(len(files), 1.585) float32: els canals `c` (31) a les imatges de `xarxa.DESPLACAMENTS` i els equips `e` (90) a
    les de `DESPLACAMENTS_EQUIPS`, cadascun com `xarxa.finestra`."""
    return np.concatenate([xarxa.finestra(c, trams, files), _finestra(e, trams, files, DESPLACAMENTS_EQUIPS)], axis=1)


def mostres(t: Tracking, trams: Trams, files: np.ndarray, etiquetes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Com `xarxa.mostres`, amb aquesta finestra: les de `files` i també amb els equips girats."""
    x = np.concatenate([_finestres(t, trams, files), _finestres(xarxa.girat(t), trams, files)])
    return x, np.concatenate([etiquetes, GIRA[etiquetes]]).astype(np.int8)


def probabilitats(xarxes: tuple[xarxa.Xarxa, ...], t: Tracking, trams: Trams) -> np.ndarray:
    """Com `xarxes.probabilitats`, amb aquesta finestra: (n, 3), la mitjana de les xarxes (cadascuna, de la vista
    directa i de la girada), arrodonida; NaN fora de les parts."""
    if not xarxes:
        raise ValueError("Cal almenys una xarxa")
    girat = xarxa.girat(t)
    c, e = xsp.canals(t, trams), equips(t, trams)
    c_girat, e_girat = xsp.canals(girat, trams), equips(girat, trams)
    out = np.full((len(c), len(CLASSES)), np.nan)
    dins = np.concatenate([np.arange(a, b + 1) for _, a, b in trams])
    for s in range(0, len(dins), xarxa.TROS):
        f = dins[s:s + xarxa.TROS]
        directa, girada = finestra(c, e, trams, f), finestra(c_girat, e_girat, trams, f)
        suma = np.zeros((len(f), len(CLASSES)))
        for xr in xarxes:
            suma += (xarxa.endavant(xr, directa) + xarxa.endavant(xr, girada)[:, GIRA]) / 2
        out[f] = np.round(suma / len(xarxes) * xarxa.ARRODONIMENT) / xarxa.ARRODONIMENT
    return out


def _finestres(t: Tracking, trams: Trams, files: np.ndarray) -> np.ndarray:
    return finestra(xsp.canals(t, trams), equips(t, trams), trams, files)


def _finestra(c: np.ndarray, trams: Trams, files: np.ndarray, desplacaments: tuple[int, ...]) -> np.ndarray:
    """`xarxa.finestra` amb uns altres desplaçaments."""
    inicis = np.array([a for _, a, _ in trams])
    finals = np.array([b for _, _, b in trams])
    files = np.asarray(files, dtype=np.int64)
    k = np.searchsorted(inicis, files, side="right") - 1
    if np.any(k < 0) or np.any(files > finals[np.maximum(k, 0)]):
        raise ValueError("Hi ha imatges fora de les parts")
    idx = files[:, None] + np.asarray(desplacaments)[None, :]
    dins = (idx >= inicis[k][:, None]) & (idx <= finals[k][:, None])
    x = c[np.clip(idx, 0, len(c) - 1)] * dins[..., None]
    return x.reshape(len(files), -1).astype(np.float32)
