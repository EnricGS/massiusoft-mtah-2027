"""Les fases amb equip simulades del banc (T3ak de `docs/pla-tocs.md`; D-73).

Cap dada oberta no té fases. Se simulen a partir de la veritat de toc, com les pilotes aturades
(`banc/smart_tagging_simulat.py`), amb tres nivells d'errors i sense fases (`cap`). Res no es tria mirant el partit
del concurs: no se sap com d'encertades són les seves fases. Amb un generador amb llavor fixa (`simula`), dins de cada
part:
1. les possessions de la veritat de menys de `minima_s` no tenen fase;
2. de les que queden, dues del mateix equip separades per menys de `junta_s`, amb una sola possessió de la veritat
   entremig i de l'altre equip, fan una sola fase, que passa per sobre de la de l'altre (DATA.md: una fase pot abastar-
   ne dues);
3. la fase es perd amb probabilitat `perdudes`;
4. l'inici i el final es mouen un desfasament uniforme de ±`desfas_s`, i amb probabilitat `curta` s'acaba en un punt a
   l'atzar de la fase (DATA.md: una fase pot quedar-se curta);
5. l'equip canvia amb probabilitat `equip_canviat`;
6. hi ha `falses` fases més, de 2 a 10 s, a imatges a l'atzar on la veritat és d'un equip, d'un equip a l'atzar.

Tot queda dins de la part, i cada fase té sempre les mateixes tirades. Les llavors (`llavor`) surten del nom del
partit, de l'escenari, del nivell i de si és per triar o per provar, amb sha256, i són unes altres que les de les
pilotes aturades.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np

from banc import fonts
from banc import smart_tagging_simulat as sts
from banc import veritat_toc as vt
from cadena.fases import Fase
from possessio.oficial import possession_metrics as pm

FPS = pm.FPS
DURADA_FALSES_S = (2, 10)


class Nivell(NamedTuple):
    minima_s: float
    junta_s: float
    perdudes: float
    desfas_s: float
    curta: float
    equip_canviat: float
    falses: int


NIVELLS: dict[str, Nivell | None] = {"bo": Nivell(2, 1, 0.10, 0.5, 0.10, 0.01, 2),
                                     "mitjà": Nivell(4, 2, 0.30, 2.0, 0.30, 0.05, 10),
                                     "dolent": Nivell(6, 4, 0.50, 4.0, 0.50, 0.15, 30),
                                     "cap": None}


def _estones(veritat: np.ndarray, a: int, b: int, nivell: Nivell) -> list[tuple[int, int, int]]:
    """Els passos 1 i 2 a la part [a, b]: les estones [inici, final) de les fases, amb l'equip."""
    possessions = pm.possession_spells(veritat, [(a, b + 1)])
    minima, junta = round(nivell.minima_s * FPS), round(nivell.junta_s * FPS)
    estones, ultima = [], -1
    for i, (de, fins, k) in enumerate(possessions):
        if fins - de < minima:
            continue
        entremig = possessions[ultima + 1:i]
        if (estones and estones[-1][2] == k and de - estones[-1][1] < junta and len(entremig) == 1
                and entremig[0][2] != k):
            estones[-1] = (estones[-1][0], fins, k)
        else:
            estones.append((de, fins, k))
        ultima = i
    return estones


def simula(veritat: np.ndarray, trams: tuple[tuple[int, int, int], ...], nivell: Nivell | None,
           llavor: int) -> tuple[Fase, ...]:
    if nivell is None:
        return ()
    rng = np.random.default_rng(llavor)
    desfas = round(nivell.desfas_s * FPS)
    fases = []
    for _, a, b in trams:
        for de, fins, k in _estones(veritat, a, b, nivell):
            u = rng.random(4)                   # sempre les mateixes tirades per fase
            d = rng.integers(-desfas, desfas + 1, size=2)
            if u[0] < nivell.perdudes:
                continue
            inici, final = int(np.clip(de + d[0], a, b)), int(np.clip(fins - 1 + d[1], a, b))
            if u[1] < nivell.curta:
                final = inici + int(u[3] * (final - inici))
            if final >= inici:
                fases.append(Fase(inici, final, k if u[2] >= nivell.equip_canviat else 1 - k))
    dins = np.zeros(len(veritat), dtype=bool)
    for _, a, b in trams:
        dins[a:b + 1] = True
    candidats = np.flatnonzero(dins & np.isin(veritat, (pm.H, pm.A)))
    if nivell.falses and len(candidats):
        for i in rng.choice(candidats, size=nivell.falses):
            dur, equip = rng.integers(DURADA_FALSES_S[0] * FPS, DURADA_FALSES_S[1] * FPS + 1), rng.integers(2)
            b = next(b for _, a, b in trams if a <= i <= b)
            fases.append(Fase(int(i), int(min(i + dur - 1, b)), int(equip)))
    return tuple(sorted(fases))


def llavor(nom: str, escenari: str, nivell: str, per: str) -> int:
    return sts.llavor(nom, escenari, nivell, per, "fases")


def fases_de(nom: str, escenari: str, nivell: str, per: str) -> tuple[Fase, ...]:
    """Les fases simulades d'un partit i un escenari, al nivell `nivell`, amb la llavor de triar o de provar."""
    return simula(vt.veritat(nom), fonts.partit(nom).trams, NIVELLS[nivell], llavor(nom, escenari, nivell, per))
