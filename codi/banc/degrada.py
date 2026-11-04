"""Els escenaris de degradació: embrutir un partit net perquè s'assembli a l'ATD automàtic.

El que se'n sap és el que diu DATA.md (commit f8f2629), i res més:
- la pilota falta en el 41 % dels fotogrames puntuats, i més en aglomeracions, en duels i a l'aire;
- hi ha 46 slots per a 22 jugadors, amb l'equip i prou, que apareixen, desapareixen i canvien d'identitat;
- als fotogrames puntuats hi ha 20,5 objectes seguits de mitjana, i a vegades més de 22, per un duplicat.

Els forats de la pilota de l'ATD no els fem servir per ajustar res: els escenaris només canvien la seva llargada. La resta és
igual a tots: jugadors perduts a estones, duplicats, slots que es barregen i un error de
posició, que és suposat. Cap forat passa d'una part a l'altra.

Dos escenaris més, per posar a prova els tocs (T2 del pla per tocs, `docs/pla-tocs.md`), amb els forats de la barreja:
- **aire:** l'ATD surt del vídeo tàctic, i una pilota a l'aire hi queda projectada al terra, més lluny de la càmera
  del que és. La projectem des d'una càmera suposada a mig camp, a 15 m d'alçada i a 25 m de la banda: baixa i a
  prop, el cas pitjor. Només a DFL, que dona l'alçada de la pilota; a Metrica és com la barreja;
- **soroll2:** el doble de l'error de posició suposat, per als jugadors i per a la pilota.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

from banc.partit import PartitBanc
from possessio.oficial import possession_metrics as pm

FPS = 25
LLAVOR = 20271024
LOT = 256                               # inicis de forat que se sorteja de cop


@dataclass(frozen=True)
class Escenari:
    nom: str
    forats_s: tuple[tuple[float, float, float], ...]   # (mín, màx, pes) de la llargada dels forats de la pilota
    pilota_absent: float = 0.41                        # DATA.md: dels fotogrames puntuats
    pes_aire: float = 3.0                              # un forat hi comença 1 + 3 vegades més sovint
    pes_aglomeracio: float = 3.0
    alcada_aire_m: float = 2.0
    velocitat_aire_ms: float = 12.0                    # si la font no dona l'alçada de la pilota
    radi_aglomeracio_m: float = 3.0
    jugadors_aglomeracio: int = 3
    objectes: float = 20.5                             # DATA.md: mitjana als fotogrames puntuats
    duplicats: float = 0.005                           # dels jugadors vistos
    perdua_jugador_s: tuple[float, float] = (0.5, 10.0)
    duplicat_s: tuple[float, float] = (1.0, 4.0)
    slots_per_equip: int = 23                          # DATA.md: 46 per als dos
    sigma_jugadors_m: float = 0.5
    sigma_pilota_m: float = 1.0
    tremolor_jugadors_m: float = 0.1
    tremolor_pilota_m: float = 0.3
    camera_m: tuple[float, float] | None = None        # (alçada, distància a la banda) de la càmera, a mig camp


FORATS_BARREJA = ((0.2, 1.0, 0.4), (1.0, 3.0, 0.3), (3.0, 8.0, 0.2), (8.0, 20.0, 0.1))
ESCENARIS = {
    "curts": Escenari("curts", ((0.2, 1.0, 0.6), (1.0, 3.0, 0.4))),
    "llargs": Escenari("llargs", ((3.0, 8.0, 0.5), (8.0, 20.0, 0.5))),
    "barreja": Escenari("barreja", FORATS_BARREJA),
    "aire": Escenari("aire", FORATS_BARREJA, camera_m=(15.0, 25.0)),
    "soroll2": Escenari("soroll2", FORATS_BARREJA, sigma_jugadors_m=1.0, sigma_pilota_m=2.0,
                        tremolor_jugadors_m=0.2, tremolor_pilota_m=0.6),
}
NOMS = ("net", *ESCENARIS)


def generador(escenari: str, partit: str) -> np.random.Generator:
    return np.random.default_rng([LLAVOR, zlib.crc32(f"{escenari}|{partit}".encode())])


def puntuats(p: PartitBanc) -> np.ndarray:
    return p.veritat != pm.X


def fi_del_tram(p: PartitBanc) -> np.ndarray:
    """Per a cada fila, la primera fila del tram següent: un forat no hi pot arribar."""
    fi = np.empty(p.n, np.int64)
    for _, inici, ultim in p.trams:
        fi[inici:ultim + 1] = ultim + 1
    return fi


def aire_i_aglomeracio(p: PartitBanc, esc: Escenari) -> tuple[np.ndarray, np.ndarray]:
    t, camp = p.tracking, np.array(p.tracking.camp_m)
    pilota = t.pilota * camp
    if np.isfinite(p.pilota_z).mean() > 0.5:
        aire = np.nan_to_num(p.pilota_z) > esc.alcada_aire_m
    else:
        suau = pd.DataFrame(pilota).interpolate(limit_area="inside").rolling(5, center=True, min_periods=1).mean()
        velocitat = np.linalg.norm(np.gradient(suau.to_numpy(), axis=0), axis=1) * FPS
        aire = np.nan_to_num(velocitat) > esc.velocitat_aire_ms
    jugadors = np.concatenate([t.casa, t.fora], axis=1) * camp
    distancia = np.nan_to_num(np.linalg.norm(jugadors - pilota[:, None, :], axis=2), nan=np.inf)
    aglomeracio = (distancia <= esc.radi_aglomeracio_m).sum(axis=1) >= esc.jugadors_aglomeracio
    return aire, aglomeracio


def llargades(rng: np.random.Generator, esc: Escenari, quantes: int) -> np.ndarray:
    mins, maxs, pesos = (np.array(x, float) for x in zip(*esc.forats_s))
    k = rng.choice(len(pesos), size=quantes, p=pesos / pesos.sum())
    return np.maximum(1, np.rint(rng.uniform(mins[k], maxs[k]) * FPS)).astype(np.int64)


def omple(rng: np.random.Generator, forat: np.ndarray, grup: np.ndarray, absent: np.ndarray, pes: np.ndarray,
          fi: np.ndarray, esc: Escenari) -> None:
    """Forats que comencen al grup fins que la pilota hi falti en la fracció que toca; l'últim, retallat."""
    falten = int(round(esc.pilota_absent * grup.sum())) - int((grup & (absent | forat)).sum())
    pes = np.where(grup, pes, 0.0)
    compta = grup & ~absent                           # els que encara compten si s'amaguen
    while falten > 0:
        for inici, llarg in zip(rng.choice(len(forat), size=LOT, p=pes / pes.sum()), llargades(rng, esc, LOT)):
            final = min(inici + llarg, fi[inici])
            nous = np.cumsum(compta[inici:final] & ~forat[inici:final])
            if len(nous) and nous[-1] > falten:
                final = inici + int(np.searchsorted(nous, falten)) + 1
            falten -= int((compta[inici:final] & ~forat[inici:final]).sum())
            forat[inici:final] = True
            if falten <= 0:
                break


def forats_de_la_pilota(rng: np.random.Generator, p: PartitBanc, esc: Escenari) -> np.ndarray:
    """La fracció que toca dels puntuats amb la pilota morta, i després dels de la pilota viva.

    Per separat, perquè les fonts no són iguals: a DFL la pilota hi és sempre, i a Metrica ja hi falta quan és
    morta. Si es comptés tot junt, a Metrica no caldria cap forat nou en joc. La viva va al final perquè és la
    que compta per a les possessions: queda exacta, i la morta, com a mínim, perquè un forat que comença en
    joc pot seguir quan la pilota ja és morta.
    """
    graduats, absent = puntuats(p), np.isnan(p.tracking.pilota[:, 0])
    aire, aglomeracio = aire_i_aglomeracio(p, esc)
    pes = 1.0 + esc.pes_aire * aire + esc.pes_aglomeracio * aglomeracio
    forat, fi = np.zeros(p.n, bool), fi_del_tram(p)
    for grup in (graduats & (p.veritat == pm.D), graduats & (p.veritat != pm.D)):
        omple(rng, forat, grup, absent, pes, fi, esc)
    return forat


def peces(equip: np.ndarray) -> list[tuple[int, int, np.ndarray]]:
    """(primera, última + 1, posicions) de cada tros seguit en què es veu cada columna."""
    out = []
    for columna in range(equip.shape[1]):
        vist = np.r_[0, ~np.isnan(equip[:, columna, 0]), 0].astype(np.int8)
        vores = np.diff(vist)
        out += [(int(a), int(b), equip[a:b, columna]) for a, b in
                zip(np.flatnonzero(vores == 1), np.flatnonzero(vores == -1))]
    return out


def perd_estones(rng: np.random.Generator, equip: np.ndarray, graduats: np.ndarray, frac: float,
                 esc: Escenari) -> np.ndarray:
    """Amaga un jugador a estones fins a la fracció dels vistos als puntuats que toca."""
    out = equip.copy()
    vist = ~np.isnan(out[..., 0]) & graduats[:, None]
    falten = int(round(frac * vist.sum()))
    candidats = np.flatnonzero(vist)
    while falten > 0 and len(candidats):
        for lloc, llarg in zip(rng.choice(candidats, size=LOT),
                               np.rint(rng.uniform(*esc.perdua_jugador_s, LOT) * FPS).astype(np.int64)):
            fila, columna = divmod(int(lloc), out.shape[1])
            tros = vist[fila:fila + llarg, columna] & ~np.isnan(out[fila:fila + llarg, columna, 0])
            if tros.sum() > falten:
                llarg = int(np.searchsorted(np.cumsum(tros), falten)) + 1
                tros = tros[:llarg]
            falten -= int(tros.sum())
            out[fila:fila + llarg, columna] = np.nan
            if falten <= 0:
                break
    return out


def duplicats(rng: np.random.Generator, equip: np.ndarray, frac: float,
              esc: Escenari) -> list[tuple[int, int, np.ndarray]]:
    """Trossos fantasma: un jugador repetit a prop d'on és, una estona."""
    vist = ~np.isnan(equip[..., 0])
    falten, out = int(round(frac * vist.sum())), []
    candidats = np.flatnonzero(vist)
    while falten > 0 and len(candidats):
        fila, columna = divmod(int(rng.choice(candidats)), equip.shape[1])
        llarg = int(np.rint(rng.uniform(*esc.duplicat_s) * FPS))
        tros = equip[fila:fila + llarg, columna]
        tros = tros[:np.argmax(np.isnan(tros[:, 0]))] if np.isnan(tros[:, 0]).any() else tros
        if not len(tros):
            continue
        out.append((fila, fila + len(tros), tros + rng.normal(0, 1.0, 2) / np.array([105.0, 68.0])))
        falten -= len(tros)
    return out


def en_slots(rng: np.random.Generator, trossos: list[tuple[int, int, np.ndarray]], n: int,
             slots: int) -> np.ndarray:
    """Cada tros a un slot lliure a l'atzar, com un tracker que perd i torna a trobar la gent."""
    lliure_des_de = np.zeros(slots, np.int64)
    columnes: list[np.ndarray] = [np.full((n, 2), np.nan) for _ in range(slots)]
    for inici, final, posicions in sorted(trossos, key=lambda x: (x[0], x[1])):
        lliures = np.flatnonzero(lliure_des_de <= inici)
        if not len(lliures):
            lliure_des_de = np.r_[lliure_des_de, 0]
            columnes.append(np.full((n, 2), np.nan))
            lliures = np.array([len(columnes) - 1])
        slot = int(rng.choice(lliures))
        columnes[slot][inici:final] = posicions
        lliure_des_de[slot] = final
    return np.stack(columnes, axis=1)


def soroll(rng: np.random.Generator, xy: np.ndarray, camp: np.ndarray, sigma_m: float,
           tremolor_m: float) -> np.ndarray:
    """L'error de posició del prototip: correlacionat en un segon, més un tremolor per imatge."""
    if sigma_m == 0 and tremolor_m == 0:
        return xy
    forma = xy.shape
    blanc = pd.DataFrame(rng.standard_normal((forma[0], int(np.prod(forma[1:])))))
    suau = blanc.rolling(FPS, center=True, min_periods=1).mean().to_numpy()
    suau = (suau / (suau.std(axis=0, keepdims=True) + 1e-12)).reshape(forma)
    return xy + (suau * sigma_m + rng.normal(0, tremolor_m, forma)) / camp


def projecta(pilota_m: np.ndarray, z: np.ndarray, camp: tuple[float, float],
             camera: tuple[float, float]) -> np.ndarray:
    """On veu la pilota al terra una càmera a mig camp, a `camera` = (alçada, distància a la banda): el punt on el
    raig de la càmera a la pilota toca el terra. Sense alçada (NaN), es queda on és."""
    alcada, distancia = camera
    origen = np.array([camp[0] / 2, -distancia])
    z = np.clip(np.nan_to_num(z), 0.0, alcada - 0.5)
    return origen + (pilota_m - origen) * (alcada / (alcada - z))[:, None]


def aplica(p: PartitBanc, escenari: str | Escenari) -> PartitBanc:
    if escenari == "net":
        return p
    esc = ESCENARIS[escenari] if isinstance(escenari, str) else escenari
    rng, t = generador(esc.nom, p.nom), p.tracking
    camp, graduats = np.array(t.camp_m), puntuats(p)
    pilota = t.pilota.copy()
    if esc.camera_m is not None:
        pilota = projecta(pilota * camp, p.pilota_z, t.camp_m, esc.camera_m) / camp
    pilota[forats_de_la_pilota(rng, p, esc)] = np.nan
    vistos = ((~np.isnan(t.casa[..., 0])).sum(1) + (~np.isnan(t.fora[..., 0])).sum(1))[graduats].mean()
    perdua = max(0.0, 1 - esc.objectes / (vistos * (1 + esc.duplicats)))
    equips = []
    for equip in (t.casa, t.fora):
        perdut = perd_estones(rng, equip, graduats, perdua, esc)
        trossos = peces(perdut) + duplicats(rng, perdut, esc.duplicats, esc)
        slots = en_slots(rng, trossos, p.n, esc.slots_per_equip)
        equips.append(soroll(rng, slots, camp, esc.sigma_jugadors_m, esc.tremolor_jugadors_m))
    pilota = soroll(rng, pilota, camp, esc.sigma_pilota_m, esc.tremolor_pilota_m)
    return replace(p, tracking=replace(t, pilota=pilota, casa=equips[0], fora=equips[1]))


def resum(p: PartitBanc) -> dict[str, float]:
    """El mateix que diu DATA.md de l'ATD, mesurat al partit: per comprovar que l'escenari hi arriba."""
    t, graduats, morta = p.tracking, puntuats(p), p.veritat == pm.D
    absent = np.isnan(t.pilota[:, 0])
    vistos = (~np.isnan(t.casa[..., 0])).sum(1) + (~np.isnan(t.fora[..., 0])).sum(1)
    usats = sum(int((~np.isnan(e[..., 0])).any(axis=0).sum()) for e in (t.casa, t.fora))
    return {"pilota_absent": float(absent[graduats].mean()),
            "pilota_absent_viva": float(absent[graduats & ~morta].mean()),
            "pilota_absent_morta": float(absent[graduats & morta].mean()),
            "objectes": float(vistos[graduats].mean()), "slots": float(usats)}
