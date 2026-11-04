"""Els senyals de cada imatge per al model d'A.

- **Col·lectius.** Els slots de l'ATD no tenen identitat (46 per a 22 jugadors). Només fem servir coses de l'equip
  sencer: el més proper a la pilota, quants n'hi ha a prop, on és el bloc i com de pressa es mou.
- **En metres, i en el sentit d'atac de cada equip.** Surt d'on és cada equip, de mitjana, a cada part. (Si tots
  dos equips tinguessin exactament la mateixa mitjana, el sentit no seria simètric; no passa mai amb dades reals.)
- **Sense pilota:** quant fa que no es veu i quant falta perquè torni, i com era tot la darrera vegada i la propera.
  Els senyals de la pilota hi són NaN, que el LightGBM ja sap tractar.
- **La pilota morta:** fora del camp, a tocar d'una línia, d'un córner o del centre, quieta, amb els jugadors quiets
  o tots al seu camp.
- Cap finestra passa d'una part a l'altra, i fora de les parts les files són NaN.

Els noms segueixen una convenció: `_h` i `_a` per equip, `dif_` per a H − A, i
`@` per a les finestres i els desplaçaments. Els de `SIMETRICS` no depenen de quin equip és quin. Amb això,
`intercanvia` dona la mateixa situació amb els equips girats, que és com el model aprèn sense biaix de casa.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from cadena.llegeix import Tracking

FPS = 25
TOPALL_M = 60.0          # les distàncies a la pilota es tallen aquí
TOPALL_S = 120.0         # i el temps sense veure-la
MARGE_LINIA_M = 1.0      # l'error del tracking a les línies: fins aquí, la pilota encara és dins
RADIS_M = (3.0, 10.0)
QUIET_MS = 1.0
MIG_JUGADORS = 12        # la velocitat d'un jugador, en un segon: el tremolor d'una imatge no la fa saltar
MIG_PILOTA = 2           # la de la pilota, en 0,16 s: va més de pressa i canvia de cop
FINESTRES = (25, 125, 250)
DESPLACAMENTS = (-50, -25, 25, 50)

DE_LA_PILOTA = ("vpil", "fora_camp", "dist_linia", "dist_corner", "dist_centre", "pilota_y")
MEMORIA_SIMETRICA = ("vpil", "fora_camp", "dist_linia")
MEMORIA_D_EQUIP = ("d1", "pilota_x")
SIMETRICS = (*DE_LA_PILOTA, "des_vista", "fins_vista", "falta", "vjug_tots", "quiets_tots", "sep", "propi_tots",
             *(f"{k}_{quan}" for k in MEMORIA_SIMETRICA for quan in ("abans", "despres")))


def a_reixa(t: Tracking, n: int) -> Tracking:
    """Una fila per imatge del vídeo, de 0 a n − 1: les que l'ATD no porta, buides (NaN)."""
    if len(np.unique(t.fotograma)) != len(t.fotograma):
        raise ValueError("L'ATD repeteix algun fotograma")
    dins = (t.fotograma >= 0) & (t.fotograma < n)

    def posa(valors: np.ndarray) -> np.ndarray:
        reixa = np.full((n, *valors.shape[1:]), np.nan)
        reixa[t.fotograma[dins]] = valors[dins]
        return reixa

    return replace(t, fotograma=np.arange(n), pilota=posa(t.pilota), casa=posa(t.casa), fora=posa(t.fora))


def calcula(t: Tracking, trams: tuple[tuple[int, int, int], ...]) -> pd.DataFrame:
    """Una fila per imatge (float32), amb els senyals calculats dins de cada part."""
    n = len(t.fotograma)
    if not np.array_equal(t.fotograma, np.arange(n)):
        raise ValueError("Els senyals volen una fila per imatge: primer, a_reixa")
    if not trams:
        raise ValueError("No hi ha cap part")
    escala = np.asarray(t.camp_m, float)
    trossos = []
    for _, inici, fi in trams:
        part = slice(inici, fi + 1)
        senyals = _una_part(t.pilota[part] * escala, t.casa[part] * escala, t.fora[part] * escala, t.camp_m)
        trossos.append(senyals.set_axis(pd.RangeIndex(inici, fi + 1)))
    return pd.concat(trossos).reindex(pd.RangeIndex(n)).astype(np.float32)


def parella(col: str) -> str:
    base, sep, finestra = col.partition("@")
    if base.endswith("_h"):
        base = base[:-2] + "_a"
    elif base.endswith("_a"):
        base = base[:-2] + "_h"
    return base + sep + finestra


def intercanvia(taula: pd.DataFrame) -> pd.DataFrame:
    """La mateixa situació amb els equips girats: `_h` i `_a` es canvien, i `dif_` canvia de signe."""
    cols = {}
    for col in taula.columns:
        valors = taula[parella(col)].to_numpy()
        cols[col] = -valors if col.startswith("dif_") else valors
    return pd.DataFrame(cols, index=taula.index).astype(np.float32)


# --- una part ---------------------------------------------------------------------------------------------------

def _una_part(pilota: np.ndarray, casa: np.ndarray, fora: np.ndarray, camp: tuple[float, float]) -> pd.DataFrame:
    llarg = camp[0]
    sentit_h = 1.0 if np.nanmedian(_mitjana(casa[..., 0])) <= np.nanmedian(_mitjana(fora[..., 0])) else -1.0
    hi_es = ~np.isnan(pilota[:, 0])
    h, a = _equip(casa, pilota, sentit_h, camp), _equip(fora, pilota, -sentit_h, camp)
    f = {f"{k}_h": v for k, v in h.items()} | {f"{k}_a": v for k, v in a.items()}
    f.update({f"dif_{k}": h[k] - a[k] for k in h})
    f.update(_de_la_pilota(pilota, camp))
    f["pilota_x_h"] = pilota[:, 0] if sentit_h > 0 else llarg - pilota[:, 0]
    f["pilota_x_a"] = llarg - f["pilota_x_h"]
    f["falta"] = (~hi_es).astype(float)
    f["des_vista"] = np.minimum(_des_de(hi_es), TOPALL_S * FPS) / FPS
    f["fins_vista"] = np.minimum(_des_de(hi_es[::-1])[::-1], TOPALL_S * FPS) / FPS
    f["vjug_tots"] = (h["vjug"] + a["vjug"]) / 2
    f["quiets_tots"] = (h["quiets"] + a["quiets"]) / 2
    f["propi_tots"] = np.fmin(h["propi"], a["propi"])
    f["sep"] = np.abs(_mitjana(casa[..., 0]) - _mitjana(fora[..., 0]))
    f.update(_memoria(f))
    f.update(_context(f))
    return pd.DataFrame(f)


def _equip(jug: np.ndarray, pilota: np.ndarray, sentit: float, camp: tuple[float, float]) -> dict[str, np.ndarray]:
    llarg, ample = camp
    x = jug[..., 0] if sentit > 0 else llarg - jug[..., 0]          # des de la línia de fons pròpia
    vist = ~np.isnan(x)
    hi_es = ~np.isnan(pilota[:, 0])
    d = np.hypot(jug[..., 0] - pilota[:, None, 0], jug[..., 1] - pilota[:, None, 1])
    ordenat = np.sort(np.where(np.isnan(d), np.inf, d), axis=1)
    segon = ordenat[:, 1] if ordenat.shape[1] > 1 else np.full(len(d), np.inf)
    velocitat = _velocitat(jug, MIG_JUGADORS)

    def amb_pilota(valors: np.ndarray) -> np.ndarray:
        return np.where(hi_es, valors, np.nan)

    return {
        "d1": amb_pilota(np.minimum(ordenat[:, 0], TOPALL_M)),
        "d2": amb_pilota(np.minimum(segon, TOPALL_M)),
        "n3": amb_pilota((d <= RADIS_M[0]).sum(axis=1)),
        "n10": amb_pilota((d <= RADIS_M[1]).sum(axis=1)),
        "cx": _mitjana(x),
        "avancat": np.fmax.reduce(x, axis=1),
        "endarrerit": np.fmin.reduce(x, axis=1),
        "disp_x": _desviacio(x),
        "disp_y": _desviacio(jug[..., 1]),
        "propi": _mitjana(np.where(vist, x < llarg / 2, np.nan)),
        "vjug": _mitjana(velocitat),
        "quiets": _mitjana(np.where(np.isnan(velocitat), np.nan, velocitat < QUIET_MS)),
        "njug": vist.sum(axis=1).astype(float),
        "y_bloc": np.abs(_mitjana(jug[..., 1]) - ample / 2),
    }


def _de_la_pilota(pilota: np.ndarray, camp: tuple[float, float]) -> dict[str, np.ndarray]:
    llarg, ample = camp
    x, y = pilota[:, 0], pilota[:, 1]
    fora = np.maximum.reduce([-x, x - llarg, -y, y - ample, np.zeros_like(x)])     # NaN si no hi és
    corners = [np.hypot(x - cx, y - cy) for cx in (0, llarg) for cy in (0, ample)]
    return {
        "vpil": _velocitat(pilota, MIG_PILOTA),
        "fora_camp": np.maximum(fora - MARGE_LINIA_M, 0),
        "dist_linia": np.minimum.reduce([x, llarg - x, y, ample - y]),
        "dist_corner": np.minimum.reduce(corners),
        "dist_centre": np.hypot(x - llarg / 2, y - ample / 2),
        "pilota_y": np.abs(y - ample / 2),
    }


def _memoria(f: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Com era cada senyal la darrera imatge que hi era, i la propera (la mateixa, si en aquesta hi és). Cadascun
    mira on és definit ell: la velocitat de la pilota, per exemple, falta dues imatges més a cada vora d'un forat."""
    out = {}
    for k in MEMORIA_SIMETRICA:
        out[f"{k}_abans"], out[f"{k}_despres"] = _a_les_vores(f[k])
    for k in MEMORIA_D_EQUIP:
        for e in ("h", "a"):
            out[f"{k}_abans_{e}"], out[f"{k}_despres_{e}"] = _a_les_vores(f[f"{k}_{e}"])
    out["dif_d1_abans"], out["dif_d1_despres"] = _a_les_vores(f["dif_d1"])
    return out


def _context(f: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """El que passa al voltant: mitjanes, màxims i mínims en finestres, i alguns valors d'abans i de després."""
    prop = np.sign(f["d1_a"] - f["d1_h"])                  # +1 si H és més a prop; NaN sense pilota
    out = {"dif_prop": prop}
    for w in FINESTRES:
        out[f"dif_prop@{w}"] = _finestra(prop, w, "mean")
        out[f"falta@{w}"] = _finestra(f["falta"], w, "mean")
        out[f"vjug_tots@{w}"] = _finestra(f["vjug_tots"], w, "mean")
        out[f"quiets_tots@{w}"] = _finestra(f["quiets_tots"], w, "mean")
    for w in (50, 125):
        out[f"dif_prop@p{w}"] = _finestra(prop, w, "mean", "passat")
        out[f"dif_prop@f{w}"] = _finestra(prop, w, "mean", "futur")
    for e in ("h", "a"):
        out[f"d1_{e}@min25"] = _finestra(f[f"d1_{e}"], 25, "min")
        out[f"n3_{e}@25"] = _finestra(f[f"n3_{e}"], 25, "mean")
        out[f"vjug_{e}@125"] = _finestra(f[f"vjug_{e}"], 125, "mean")
    out["dif_cx@125"] = _finestra(f["dif_cx"], 125, "mean")
    out["vpil@max25"] = _finestra(f["vpil"], 25, "max")
    out["vpil@125"] = _finestra(f["vpil"], 125, "mean")
    out["fora_camp@max25"] = _finestra(f["fora_camp"], 25, "max")
    out["fora_camp@max125"] = _finestra(f["fora_camp"], 125, "max")
    for k in DESPLACAMENTS:
        out[f"dif_d1@{k:+d}"] = _desplaca(f["dif_d1"], k)
    return out


# --- eines ------------------------------------------------------------------------------------------------------

def _mitjana(valors: np.ndarray) -> np.ndarray:
    """La mitjana de cada fila sense els NaN (NaN si no n'hi ha cap), sense avisos de numpy."""
    compta = (~np.isnan(valors)).sum(axis=1)
    return np.where(compta > 0, np.nansum(valors, axis=1) / np.maximum(compta, 1), np.nan)


def _desviacio(valors: np.ndarray) -> np.ndarray:
    mitjana = _mitjana(valors)
    return np.sqrt(np.maximum(_mitjana(valors ** 2) - mitjana ** 2, 0))


def _velocitat(xy: np.ndarray, mig: int) -> np.ndarray:
    """|p(t + mig) − p(t − mig)| en m/s; NaN a les vores de la part i on falta l'una o l'altra."""
    v = np.full(xy.shape[:-1], np.nan)
    if len(xy) > 2 * mig:
        dif = xy[2 * mig:] - xy[:-2 * mig]
        v[mig:-mig] = np.hypot(dif[..., 0], dif[..., 1]) * FPS / (2 * mig)
    return v


def _ultima(hi_es: np.ndarray) -> np.ndarray:
    """L'índex de la darrera imatge on és cert, fins aquí (−1 si encara no n'hi ha hagut cap)."""
    return np.maximum.accumulate(np.where(hi_es, np.arange(len(hi_es)), -1))


def _a_les_vores(valors: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """El valor de la darrera imatge on n'hi ha (fins aquí) i el de la propera (des d'aquí); NaN si no n'hi ha."""
    definit = ~np.isnan(valors)
    abans = _ultima(definit)
    despres = _ultima(definit[::-1])[::-1]
    despres = np.where(despres >= 0, len(valors) - 1 - despres, -1)
    return tuple(np.where(idx >= 0, valors[np.maximum(idx, 0)], np.nan) for idx in (abans, despres))


def _des_de(hi_es: np.ndarray) -> np.ndarray:
    """Imatges des de la darrera amb pilota (0 si hi és). Si no se n'ha vist cap a la part, des de l'inici, més u."""
    return np.arange(len(hi_es)) - _ultima(hi_es)


def _finestra(valors: np.ndarray, w: int, com: str, on: str = "centre") -> np.ndarray:
    """Sense els NaN, i només amb el que hi ha dins de la part (les vores fan servir el que tenen)."""
    s = pd.Series(valors)
    if on == "futur":
        return getattr(s.iloc[::-1].rolling(w, min_periods=1), com)().iloc[::-1].to_numpy()
    return getattr(s.rolling(w, center=on == "centre", min_periods=1), com)().to_numpy()


def _desplaca(valors: np.ndarray, k: int) -> np.ndarray:
    """valors[t + k], amb NaN fora de la part."""
    out = np.full(len(valors), np.nan)
    if k > 0:
        out[:-k] = valors[k:]
    elif k < 0:
        out[-k:] = valors[:k]
    else:
        out[:] = valors
    return out
