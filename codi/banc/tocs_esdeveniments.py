"""Els tocs dels esdeveniments i el que aprèn el detector de tocs a cada imatge (T3u del pla per tocs,
`docs/pla-tocs.md`, «T3u»; D-53).

- **Els tocs** (`tocs`): la fila i l'equip de cada toc, en ordre. Els mateixos que fa servir la veritat de toc:
  - a DFL, els esdeveniments de toc (`veritat_toc.tocs_dfl`), cadascun a la imatge on el jugador és més a prop de la
    pilota (`veritat_toc.col_loca`) (`de_dfl`);
  - a Metrica, l'inici de cada esdeveniment de possessió (`etiquetes.TIPUS_POSSESSIO`) i de cada duel guanyat sense
    falta (`etiquetes._es_duel_guanyat`), de l'equip que el fa (`de_metrica`).

  Es desen a `dades/banc/tocs-esdeveniments/`, amb la clau del codi.
- **El que aprèn el detector** (`etiquetes_de_toc`): a cada imatge d'una part, H si hi ha un toc de l'H a `A_PROP`
  imatges o menys, A si n'hi ha un de l'A, i D (cap) si no. Si n'hi ha de tots dos equips, el més proper; a la mateixa
  distància, el primer. Mai d'una part a l'altra; fora de les parts, D.
- **Les imatges que s'aprenen** (`files`): totes les de les parts puntuades amb un toc a prop, i una de cada `PAS` de
  la resta.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import numpy as np
import pandas as pd

from banc import dfl, fonts
from banc import veritat_toc as vt
from possessio import etiquetes
from possessio.carrega import carrega_partit
from possessio.oficial import possession_metrics as pm

A_PROP = 3                  # imatges a cada banda del toc
PAS = 32                    # de les imatges sense cap toc a prop, una de cada
EQUIPS = {"Home": pm.H, "Away": pm.A}
DIR_CAU = fonts.DIR_CAU / "tocs-esdeveniments"
Trams = tuple[tuple[int, int, int], ...]


def de_dfl(partit: str, de_sempre: np.ndarray) -> list[tuple[int, int]]:
    """Els tocs d'un partit de DFL, com els col·loca la veritat de toc. Comprova abans que les imatges del fitxer en
    brut són les del banc, una a una."""
    meta = dfl.fitxer(fonts.DIR_IDSSE, f"DFL_02_01_matchinformation_*{partit}.xml")
    casa = next(re.search(r'TeamId="([^"]+)"', m.group(1)).group(1)
                for m in re.finditer(r"<Team ([^>]*)>", meta.read_text(encoding="utf-8")) if 'Role="home"' in m.group(1))
    tr = vt.tracking_dfl(dfl.fitxer(fonts.DIR_IDSSE, f"DFL_04_03_positions_raw_observed_*{partit}.xml"))
    if not np.array_equal(tr.veritat, de_sempre):
        raise ValueError(f"{partit}: el fitxer en brut no dona la veritat del banc imatge per imatge")
    text = dfl.fitxer(fonts.DIR_IDSSE, f"DFL_03_02_events_raw_*{partit}.xml").read_text(encoding="utf-8")
    return vt.col_loca(tr, vt.tocs_dfl(text, casa))


def de_metrica(events: pd.DataFrame, frame: np.ndarray, periode: np.ndarray) -> list[tuple[int, int]]:
    """(fila, equip) de cada toc de Metrica: la imatge on comença cada esdeveniment de possessió i cada duel guanyat
    sense falta, de l'equip que el fa. En ordre. Si la imatge no hi és, o és d'una altra part, s'atura."""
    fila_de = {int(f): i for i, f in enumerate(frame)}
    out = []
    for _, ev in events.iterrows():
        if ev["type"] not in etiquetes.TIPUS_POSSESSIO and not etiquetes._es_duel_guanyat(ev):
            continue
        fila = fila_de.get(int(ev["start_frame"]))
        if fila is None or periode[fila] != ev["period"]:
            raise ValueError(f"Un esdeveniment sense imatge a la seva part: {ev['type']} a {ev['start_frame']}")
        out.append((fila, EQUIPS[ev["team"]]))
    return sorted(out)


def clau() -> str:
    h = hashlib.sha256(vt.CLAU.encode())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


CLAU = clau()


def tocs(nom: str) -> np.ndarray:
    """(k, 2) int64: la fila i l'equip de cada toc d'un partit del banc, en ordre; de la memòria cau si hi és amb
    aquest codi."""
    cami = DIR_CAU / f"{nom}.npz"
    if cami.exists():
        with np.load(cami, allow_pickle=False) as desat:
            if str(desat["clau"]) == CLAU:
                return desat["tocs"]
    font, quin = nom.split("-", 1)
    if font == "dfl":
        trobats = de_dfl(quin, fonts.partit(nom).veritat)
    elif font == "metrica":
        p = carrega_partit(int(quin))
        if p.n != len(fonts.partit(nom).veritat):
            raise ValueError(f"{nom}: les imatges no són les del banc")
        trobats = de_metrica(p.events, p.frame, p.periode)
    else:
        raise KeyError(f"No hi ha tocs dels esdeveniments per a {nom}")
    out = np.array(trobats, dtype=np.int64).reshape(-1, 2)
    DIR_CAU.mkdir(parents=True, exist_ok=True)
    temporal = cami.with_name(f"{cami.name}.part.npz")
    np.savez(temporal, clau=CLAU, tocs=out)
    temporal.replace(cami)
    return out


def etiquetes_de_toc(tocs_: np.ndarray, n: int, trams: Trams, a_prop: int = A_PROP) -> np.ndarray:
    """(n,) int8: a cada imatge d'una part, l'equip del toc més proper de la mateixa part, a `a_prop` imatges o menys
    (a la mateixa distància, el primer de `tocs_`); D on no n'hi ha cap i fora de les parts."""
    out = np.full(n, pm.D, dtype=np.int8)
    distancia = np.full(n, np.inf)
    for _, inici, ultim in trams:
        for fila, equip in tocs_[(tocs_[:, 0] >= inici) & (tocs_[:, 0] <= ultim)]:
            j = np.arange(max(fila - a_prop, inici), min(fila + a_prop, ultim) + 1)
            mes_a_prop = np.abs(j - fila) < distancia[j]
            distancia[j[mes_a_prop]] = np.abs(j - fila)[mes_a_prop]
            out[j[mes_a_prop]] = equip
    return out


def files(etiqueta: np.ndarray, trams: list[tuple[int, int]], pas: int = PAS) -> np.ndarray:
    """Les imatges que s'aprenen, en ordre: totes les de les parts puntuades (`trams`, [inici, final)) amb un toc a
    prop (H o A), i una de cada `pas` de la resta."""
    dins = np.zeros(len(etiqueta), dtype=bool)
    for inici, final in trams:
        dins[inici:final] = True
    triades = dins & (etiqueta != pm.D)
    triades[np.flatnonzero(dins & ~triades)[::pas]] = True
    return np.flatnonzero(triades)
