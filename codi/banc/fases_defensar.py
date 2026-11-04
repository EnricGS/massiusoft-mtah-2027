"""Les fases de defensar simulades del banc (T3an de `docs/pla-tocs.md`; D-82).

Les quatre fases de defensar del Smart Tagging diuen l'equip que defensa (DATA.md i l'OVERVIEW: `Team` és l'equip
que fa l'acció), i la pilota és de l'altre. Cap dada oberta no en té, i se simulen com les d'atac
(`banc/fases_simulades.py`): a partir de les mateixes estones de la veritat de toc i amb el mateix nivell, però amb unes
altres tirades. Es perden, es mouen, es queden curtes, canvien d'equip i n'hi ha de falses pel seu compte.

**`lligades`:** amb aquesta probabilitat, una estona (o una fase falsa) té, a la de defensar, exactament les tirades de
la d'atac: si la d'atac s'ha perdut, la de defensar també. Amb 1, les de defensar són les d'atac amb l'equip girat;
amb 0, no les miren. Les tirades pròpies es fan sempre, i no depenen de `lligades`.

Les tirades d'atac es tornen a fer amb la llavor de `fases_simulades` i en el seu mateix ordre (`d_atac`, que dona
exactament les seves fases). Les pròpies surten d'una altra llavor (`llavor`), amb sha256, i són unes altres que les de
les fases d'atac i de les pilotes aturades. Cada fase porta l'equip que defensa; el model les gira.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np

from banc import fases_simulades as fsm
from banc import fonts
from banc import smart_tagging_simulat as sts
from banc import veritat_toc as vt
from cadena.fases import Fase
from possessio.oficial import possession_metrics as pm

FPS = pm.FPS
LLIGADES = (0.0, 0.5, 1.0)


class Estona(NamedTuple):
    de: int
    fins: int               # exclosa
    equip: int              # el que té la pilota
    a: int                  # la part
    b: int


class Tirades(NamedTuple):
    u: np.ndarray           # (estones, 4)
    d: np.ndarray           # (estones, 2): el desfasament de l'inici i del final
    imatges: np.ndarray     # (falses,): on comencen les falses
    durades: np.ndarray     # (falses,)
    equips: np.ndarray      # (falses,)


def _estones(veritat: np.ndarray, trams: tuple[tuple[int, int, int], ...], nivell: fsm.Nivell) -> list[Estona]:
    return [Estona(de, fins, k, a, b) for _, a, b in trams for de, fins, k in fsm._estones(veritat, a, b, nivell)]


def _candidats(veritat: np.ndarray, trams: tuple[tuple[int, int, int], ...]) -> np.ndarray:
    dins = np.zeros(len(veritat), dtype=bool)
    for _, a, b in trams:
        dins[a:b + 1] = True
    return np.flatnonzero(dins & np.isin(veritat, (pm.H, pm.A)))


def _tira(rng: np.random.Generator, estones: int, nivell: fsm.Nivell, candidats: np.ndarray) -> Tirades:
    """Les tirades de `fases_simulades.simula`, en el seu ordre: per estona, `u` i `d`; després, les falses."""
    desfas = round(nivell.desfas_s * FPS)
    u, d = np.empty((estones, 4)), np.empty((estones, 2), dtype=np.int64)
    for j in range(estones):
        u[j] = rng.random(4)
        d[j] = rng.integers(-desfas, desfas + 1, size=2)
    imatges = rng.choice(candidats, size=nivell.falses) if nivell.falses and len(candidats) else np.empty(0, np.int64)
    durades, equips = np.empty(len(imatges), dtype=np.int64), np.empty(len(imatges), dtype=np.int64)
    for j in range(len(imatges)):
        durades[j] = rng.integers(fsm.DURADA_FALSES_S[0] * FPS, fsm.DURADA_FALSES_S[1] * FPS + 1)
        equips[j] = rng.integers(2)
    return Tirades(u, d, imatges, durades, equips)


def _fases(estones: list[Estona], t: Tirades, nivell: fsm.Nivell,
           trams: tuple[tuple[int, int, int], ...]) -> tuple[Fase, ...]:
    """Les fases amb l'equip que té la pilota, com a `fases_simulades.simula`."""
    fases = []
    for e, u, d in zip(estones, t.u, t.d):
        if u[0] < nivell.perdudes:
            continue
        inici, final = int(np.clip(e.de + d[0], e.a, e.b)), int(np.clip(e.fins - 1 + d[1], e.a, e.b))
        if u[1] < nivell.curta:
            final = inici + int(u[3] * (final - inici))
        if final >= inici:
            fases.append(Fase(inici, final, e.equip if u[2] >= nivell.equip_canviat else 1 - e.equip))
    for i, dur, equip in zip(t.imatges, t.durades, t.equips):
        b = next(b for _, a, b in trams if a <= i <= b)
        fases.append(Fase(int(i), int(min(i + dur - 1, b)), int(equip)))
    return tuple(sorted(fases))


def d_atac(veritat: np.ndarray, trams: tuple[tuple[int, int, int], ...], nivell: fsm.Nivell | None,
           llavor: int) -> tuple[Fase, ...]:
    """Les fases d'atac, amb les tirades refetes: exactament `fases_simulades.simula`."""
    if nivell is None:
        return ()
    estones = _estones(veritat, trams, nivell)
    return _fases(estones, _tira(np.random.default_rng(llavor), len(estones), nivell, _candidats(veritat, trams)),
                  nivell, trams)


def _barreja(atac: Tirades, propies: Tirades, lliga_estones: np.ndarray, lliga_falses: np.ndarray) -> Tirades:
    e, f = lliga_estones[:, None], lliga_falses
    return Tirades(np.where(e, atac.u, propies.u), np.where(e, atac.d, propies.d),
                   np.where(f, atac.imatges, propies.imatges), np.where(f, atac.durades, propies.durades),
                   np.where(f, atac.equips, propies.equips))


def simula(veritat: np.ndarray, trams: tuple[tuple[int, int, int], ...], nivell: fsm.Nivell | None, llavor: int,
           llavor_atac: int, lligades: float) -> tuple[Fase, ...]:
    """Les fases de defensar al nivell `nivell`, amb l'equip que defensa; les d'atac són les del mateix nivell, amb
    `llavor_atac`."""
    if not 0.0 <= lligades <= 1.0:
        raise ValueError(f"lligades ha d'anar de 0 a 1, i és {lligades}")
    if nivell is None:
        return ()
    estones, candidats = _estones(veritat, trams, nivell), _candidats(veritat, trams)
    atac = _tira(np.random.default_rng(llavor_atac), len(estones), nivell, candidats)
    rng = np.random.default_rng(llavor)
    propies = _tira(rng, len(estones), nivell, candidats)
    lliga_estones, lliga_falses = rng.random(len(estones)) < lligades, rng.random(len(propies.imatges)) < lligades
    fases = _fases(estones, _barreja(atac, propies, lliga_estones, lliga_falses), nivell, trams)
    return tuple(sorted(Fase(f.inici, f.final, 1 - f.equip) for f in fases))


def llavor(nom: str, escenari: str, nivell: str, per: str) -> int:
    return sts.llavor(nom, escenari, nivell, per, "defensar")


def fases_de(nom: str, escenari: str, nivell: str, per: str, lligades: float) -> tuple[Fase, ...]:
    """Les fases de defensar simulades d'un partit i un escenari, al nivell `nivell`, amb la llavor de triar o de
    provar; les d'atac amb què es lliguen són les de `fases_simulades.fases_de` amb els mateixos arguments."""
    return simula(vt.veritat(nom), fonts.partit(nom).trams, fsm.NIVELLS[nivell], llavor(nom, escenari, nivell, per),
                  fsm.llavor(nom, escenari, nivell, per), lligades)
