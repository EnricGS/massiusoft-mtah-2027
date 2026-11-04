"""El Smart Tagging simulat del banc: les pilotes aturades de cada partit obert, amb els errors de cada nivell (T3af
de `docs/pla-tocs.md`; D-68).

Els partits del banc no tenen Smart Tagging. Les pilotes aturades surten dels esdeveniments oberts, i les etiquetes
se simulen al damunt, amb errors de quatre nivells. Res no es tria mirant el partit del concurs: els nivells van de
gairebé perfecte a cap etiqueta, perquè no se sap com d'encertat és el Smart Tagging del partit.

- **Les represes** (`represes`): de DFL, els `ThrowIn`, `CornerKick`, `GoalKick`, `FreeKick`, `KickOff` i `Penalty`
  dels esdeveniments en brut, a l'hora de l'esdeveniment (`EventTime`), passada a la fila del banc amb les hores del
  tracking en brut (`veritat_toc.tracking_dfl`); de Metrica, els `SET PIECE`. El penal va com una falta. Cada una es
  col·loca al canvi de la D a un equip més proper de la veritat de toc, a 3 s o menys i dins de la mateixa part, i a
  l'equip de l'esdeveniment si en diu un (`col_loca`); l'equip de la represa és el de la veritat. Si dues cauen al
  mateix canvi, hi va la primera. Es desen a `dades/banc/pilotes-aturades/`, amb la clau del codi i de la veritat.
- **Les etiquetes** (`simula`), amb un generador amb llavor fixa i les mateixes tirades per cada represa:
  1. cada represa perd l'etiqueta amb probabilitat `perdudes`;
  2. l'inici és la represa més un desfasament uniforme de `desfas_s`, i dura de 2 a 10 s; tot dins de la part;
  3. el tipus canvia a un dels altres amb probabilitat `tipus_canviat`;
  4. l'equip canvia amb probabilitat `equip_canviat`; la de banda mai no en porta (al Smart Tagging del partit, cap
     de banda no en porta: DATA.md);
  5. hi ha `falses` etiquetes més, a imatges a l'atzar on la veritat és d'un equip, d'un tipus a l'atzar i de l'equip
     de la veritat (que també canvia amb probabilitat `equip_canviat`).
- **Les llavors** (`llavor`) surten del nom del partit, de l'escenari, del nivell i de si és per aprendre o per
  provar, amb sha256: no depenen de l'atzar del procés. Per aprendre, cada partit i escenari té un nivell
  (`nivell_per_aprendre`).
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

import numpy as np

from banc import dfl, fonts
from banc import veritat_toc as vt
from cadena import smart_tagging as st
from possessio.carrega import carrega_partit
from possessio.oficial import possession_metrics as pm

FPS = pm.FPS
RADI = 3 * FPS
DURADA_S = (2, 10)
DIR_CAU = fonts.DIR_CAU / "pilotes-aturades"
TIPUS_DFL = {"ThrowIn": "banda", "CornerKick": "corner", "GoalKick": "porta", "FreeKick": "falta",
             "KickOff": "sortida", "Penalty": "falta"}
TIPUS_METRICA = (("THROW IN", "banda"), ("CORNER KICK", "corner"), ("GOAL KICK", "porta"), ("FREE KICK", "falta"),
                 ("PENALTY", "falta"), ("KICK OFF", "sortida"))
EQUIPS_METRICA = {"Home": pm.H, "Away": pm.A}

_ESDEVENIMENT = re.compile(r'<Event [^>]*EventTime="([^"]+)"[^>]*>(.*?)</Event>', re.DOTALL)
_REPRESA = re.compile(rf'<({"|".join(TIPUS_DFL)})\b([^>]*)>')


class Nivell(NamedTuple):
    perdudes: float
    desfas_s: tuple[float, float]
    tipus_canviat: float
    equip_canviat: float
    falses: int


NIVELLS = {"bo": Nivell(0.10, (-1.0, 1.0), 0.0, 0.02, 2),
           "mitjà": Nivell(0.30, (-3.0, 2.0), 0.10, 0.10, 8),
           "dolent": Nivell(0.50, (-8.0, 4.0), 0.25, 0.25, 20),
           "cap": Nivell(1.0, (0.0, 0.0), 0.0, 0.0, 0)}


class Represa(NamedTuple):
    imatge: int         # fila del banc: la primera de l'equip després de la D
    tipus: str          # un de st.TIPUS
    equip: int          # pm.H o pm.A, el de la veritat


class Represes(NamedTuple):
    represes: tuple[Represa, ...]
    esdeveniments: int
    no_col_locades: int
    repetides: int


class Simulat(NamedTuple):
    etiquetes: tuple[st.Etiqueta, ...]     # primer les de les represes, en ordre; després les falses
    de_represes: tuple[int, ...]           # l'índex de la represa de cada una de les primeres


def tipus_metrica(subtipus: str) -> str | None:
    return next((t for prefix, t in TIPUS_METRICA if str(subtipus).startswith(prefix)), None)


def _part(trams: tuple[tuple[int, int, int], ...], k: int) -> tuple[int, int] | None:
    return next(((a, b) for _, a, b in trams if a <= k <= b), None)


def col_loca(veritat: np.ndarray, trams: tuple[tuple[int, int, int], ...], imatge: int, equip: int | None = None,
             radi: int = RADI) -> int | None:
    """La fila del canvi de la D a un equip (a `equip`, si en diu un) més proper a `imatge`, a `radi` o menys i dins
    d'una part; si n'hi ha dos a la mateixa distància, el primer. None si no n'hi ha cap."""
    millor = None
    for _, a, b in trams:
        de, fins = max(a + 1, imatge - radi), min(b, imatge + radi)
        if de > fins:
            continue
        k = np.arange(de, fins + 1)
        canvi = (veritat[k - 1] == pm.D) & (np.isin(veritat[k], (pm.H, pm.A)) if equip is None else veritat[k] == equip)
        for j in k[canvi]:
            if millor is None or abs(int(j) - imatge) < abs(millor - imatge):
                millor = int(j)
    return millor


def represes_de(veritat: np.ndarray, trams: tuple[tuple[int, int, int], ...],
                esdeveniments: list[tuple[int, str, int | None]]) -> Represes:
    """Les represes dels esdeveniments (fila, tipus, equip o cap), en ordre de fila."""
    vistes: dict[int, Represa] = {}
    no_col_locades = repetides = 0
    for imatge, tipus, equip in esdeveniments:
        k = col_loca(veritat, trams, imatge, equip)
        if k is None:
            no_col_locades += 1
        elif k in vistes:
            repetides += 1
        else:
            vistes[k] = Represa(k, tipus, int(veritat[k]))
    return Represes(tuple(vistes[k] for k in sorted(vistes)), len(esdeveniments), no_col_locades, repetides)


def esdeveniments_dfl(partit: str, de_sempre: np.ndarray) -> list[tuple[int, str, int | None]]:
    meta = dfl.fitxer(fonts.DIR_IDSSE, f"DFL_02_01_matchinformation_*{partit}.xml")
    casa = next(re.search(r'TeamId="([^"]+)"', m.group(1)).group(1)
                for m in re.finditer(r"<Team ([^>]*)>", meta.read_text(encoding="utf-8")) if 'Role="home"' in m.group(1))
    tr = vt.tracking_dfl(dfl.fitxer(fonts.DIR_IDSSE, f"DFL_04_03_positions_raw_observed_*{partit}.xml"))
    if not np.array_equal(tr.veritat, de_sempre):
        raise ValueError(f"{partit}: el fitxer en brut no dona la veritat del banc imatge per imatge")
    text = dfl.fitxer(fonts.DIR_IDSSE, f"DFL_03_02_events_raw_*{partit}.xml").read_text(encoding="utf-8")
    out = []
    for m in _ESDEVENIMENT.finditer(text):
        represa = _REPRESA.search(m.group(2))
        if represa is None:
            continue
        tipus, cos = represa.groups()
        equip = re.search(r'\bTeam="([^"]+)"', cos)
        k = int(np.searchsorted(tr.temps, datetime.fromisoformat(m.group(1)).timestamp()))
        out.append((min(k, len(tr.temps) - 1), TIPUS_DFL[tipus],
                    None if equip is None else (pm.H if equip.group(1) == casa else pm.A)))
    return out


def esdeveniments_metrica(num: int) -> list[tuple[int, str, int | None]]:
    p = carrega_partit(num)
    s = p.events[p.events["type"] == "SET PIECE"]
    files = p.index_de_frame(s["start_frame"].to_numpy())
    return [(int(k), t, EQUIPS_METRICA.get(equip)) for k, subtipus, equip in zip(files, s["subtype"], s["team"])
            if (t := tipus_metrica(subtipus)) is not None]


def clau() -> str:
    h = hashlib.sha256(Path(__file__).read_bytes())
    h.update(vt.CLAU.encode())
    return h.hexdigest()


CLAU = clau()


def represes(nom: str) -> Represes:
    """Les represes d'un partit del banc, de la memòria cau si hi són amb aquest codi i aquesta veritat."""
    partit = fonts.partit(nom)
    veritat = vt.veritat(nom)
    cami = DIR_CAU / f"{nom}.npz"
    if cami.exists():
        with np.load(cami, allow_pickle=False) as desat:
            if str(desat["clau"]) == CLAU and str(desat["veritat"]) == vt.empremta(veritat):
                return Represes(tuple(Represa(int(k), st.TIPUS[int(t)], int(e)) for k, t, e in desat["represes"]),
                                *(int(x) for x in desat["comptes"]))
    font, quin = nom.split("-", 1)
    if font == "dfl":
        esdeveniments = esdeveniments_dfl(quin, partit.veritat)
    elif font == "metrica":
        esdeveniments = esdeveniments_metrica(int(quin))
    else:
        raise KeyError(f"No hi ha pilotes aturades per a {nom}")
    r = represes_de(veritat, partit.trams, esdeveniments)
    DIR_CAU.mkdir(parents=True, exist_ok=True)
    temporal = cami.with_name(f"{cami.name}.part.npz")
    np.savez(temporal, clau=CLAU, veritat=vt.empremta(veritat),
             represes=np.array([(x.imatge, st.TIPUS.index(x.tipus), x.equip) for x in r.represes],
                               dtype=np.int64).reshape(-1, 3),
             comptes=np.array([r.esdeveniments, r.no_col_locades, r.repetides], dtype=np.int64))
    temporal.replace(cami)
    return r


def llavor(*parts: str) -> int:
    return int.from_bytes(hashlib.sha256("|".join(parts).encode()).digest()[:8], "big")


def nivell_per_aprendre(nom: str, escenari: str) -> str:
    noms = tuple(NIVELLS)
    return noms[llavor(nom, escenari, "nivell per aprendre") % len(noms)]


def _altre(equip: int) -> int:
    return pm.A if equip == pm.H else pm.H


def _etiqueta(inici: int, b: int, durada: int, tipus: str, equip: int, canvia: bool) -> st.Etiqueta:
    equip_final = None if tipus == "banda" else (_altre(equip) if canvia else equip)
    return st.Etiqueta(inici, min(inici + durada, b), tipus, equip_final)


def simula(represes_: tuple[Represa, ...], veritat: np.ndarray, trams: tuple[tuple[int, int, int], ...],
           nivell: Nivell, llavor: int) -> Simulat:
    rng = np.random.default_rng(llavor)
    desfas = (round(nivell.desfas_s[0] * FPS), round(nivell.desfas_s[1] * FPS))
    durada = (DURADA_S[0] * FPS, DURADA_S[1] * FPS)
    etiquetes, de_represes = [], []
    for i, r in enumerate(represes_):
        u = rng.random(3)                       # sempre les mateixes tirades per represa
        d, dur, nou = rng.integers(desfas[0], desfas[1] + 1), rng.integers(durada[0], durada[1] + 1), rng.integers(4)
        part = _part(trams, r.imatge)
        if u[0] < nivell.perdudes or part is None:
            continue
        a, b = part
        tipus = r.tipus if u[1] >= nivell.tipus_canviat else [t for t in st.TIPUS if t != r.tipus][int(nou)]
        etiquetes.append(_etiqueta(int(np.clip(r.imatge + d, a, b)), b, int(dur), tipus, r.equip,
                                   u[2] < nivell.equip_canviat))
        de_represes.append(i)
    dins = np.zeros(len(veritat), dtype=bool)
    for _, a, b in trams:
        dins[a:b + 1] = True
    candidats = np.flatnonzero(dins & np.isin(veritat, (pm.H, pm.A)))
    if nivell.falses and len(candidats):
        for k in rng.choice(candidats, size=nivell.falses):
            tipus, dur, canvia = st.TIPUS[int(rng.integers(len(st.TIPUS)))], rng.integers(durada[0], durada[1] + 1), \
                rng.random() < nivell.equip_canviat
            _, b = _part(trams, int(k))
            etiquetes.append(_etiqueta(int(k), b, int(dur), tipus, int(veritat[k]), canvia))
    return Simulat(tuple(etiquetes), tuple(de_represes))
