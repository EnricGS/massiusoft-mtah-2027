"""Una xarxa neuronal petita que mira les posicions al voltant de la pilota (T3m del pla per tocs, `docs/pla-tocs.md`,
«T3m»).

Els senyals de `senyals.py` a `aturades.py` són resums fets a mà. Aquesta xarxa aprèn ella mateixa, de les posicions,
com es veu qui rep la pilota, i les seves probabilitats van al segon classificador (`senyals_segon`).

- **El que veu a cada imatge** (`canals`, 29 valors), en metres des del mig del camp, girat perquè l'equip H ataqui
  cap a les x positives (el sentit surt d'on és cada equip, de mitjana, a cada part, com a `senyals.py`):
  - la pilota: si hi és (1 o 0), on és (x, y) i la seva velocitat (vx, vy);
  - de cada equip, els `PROPERS` jugadors més propers a la pilota, per ordre de distància: on són respecte de la
    pilota (dx, dy) i la seva velocitat (vx, vy).

  Sense pilota, tots els que en depenen són 0. Si un equip té menys jugadors a la imatge, els que falten són lluny
  (dx = dy = `LLUNY_M`) i quiets. Les velocitats, en ±`MIG` imatges, i 0 on no n'hi ha.
- **La finestra** (`finestra`): aquests valors a les imatges de `DESPLACAMENTS` al voltant (fins a ±2 s), 725 en
  total. Cap no passa d'una part a l'altra: fora de la part, tot és 0.
- **La xarxa** (`entrena`): un perceptró de scikit-learn (`OCULTES`, ReLU, Adam, `PASSADES` passades, lots de `LOT`,
  L2 de `L2` i la llavor del model), amb els valors estandarditzats. Aprèn H, A i D, cada imatge també amb els equips
  girats (`mostres`). Es desa com a matrius (`Xarxa`, `desa`, `carrega`), sense pickle.
- **Les probabilitats** (`probabilitats`), amb numpy: la mitjana de la vista directa i de la girada, com
  `model.probabilitats`, arrodonides a 1/`ARRODONIMENT`. El Mac i Linux poden diferir a l'última xifra de les
  multiplicacions, i arrodonides donen el mateix. Fora de les parts, NaN.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd

from cadena import context, senyals
from cadena.llegeix import Tracking
from cadena.model import CLASSES, GIRA, LLAVOR
from possessio.oficial import possession_metrics as pm

FPS = senyals.FPS
PROPERS = 3
MIG = 2                         # com la velocitat de la pilota a `senyals.py`
LLUNY_M = senyals.TOPALL_M
DESPLACAMENTS = (-50, -40, -30, -25, -20, -16, -12, -9, -6, -4, -2, -1, 0, 1, 2, 4, 6, 9, 12, 16, 20, 25, 30, 40, 50)
CANALS = 5 + 2 * PROPERS * 4
OCULTES = (256, 128)
PASSADES = 15
LOT = 1024
L2 = 1e-4
ARRODONIMENT = 1024
TROS = 20_000                   # imatges per càlcul, per la memòria
H, A, D = (CLASSES.index(c) for c in (pm.H, pm.A, pm.D))


@dataclass(frozen=True)
class Xarxa:
    mitjana: np.ndarray                 # (725,) per estandarditzar
    escala: np.ndarray                  # (725,)
    pesos: tuple[np.ndarray, ...]       # de cada capa, (entrades, sortides)
    biaixos: tuple[np.ndarray, ...]


def girat(t: Tracking) -> Tracking:
    """El mateix tracking amb els equips canviats."""
    return replace(t, casa=t.fora, fora=t.casa)


def canals(t: Tracking, trams: tuple[tuple[int, int, int], ...]) -> np.ndarray:
    """(n, 29) float32: el que veu la xarxa a cada imatge. Fora de les parts, 0."""
    n = len(t.fotograma)
    if not np.array_equal(t.fotograma, np.arange(n)):
        raise ValueError("La xarxa vol una fila per imatge: primer, a_reixa")
    if not trams:
        raise ValueError("No hi ha cap part")
    escala = np.asarray(t.camp_m, float)
    out = np.zeros((n, CANALS), np.float32)
    for _, inici, fi in trams:
        part = slice(inici, fi + 1)
        out[part] = _una_part(t.pilota[part] * escala, t.casa[part] * escala, t.fora[part] * escala, escala)
    return out


def finestra(c: np.ndarray, trams: tuple[tuple[int, int, int], ...], files: np.ndarray) -> np.ndarray:
    """(len(files), 725) float32: els canals `c` de cada imatge de `files` a cada desplaçament (primer el desplaçament,
    després el canal). Fora de la part de la imatge, 0."""
    inicis = np.array([a for _, a, _ in trams])
    finals = np.array([b for _, _, b in trams])
    files = np.asarray(files, dtype=np.int64)
    k = np.searchsorted(inicis, files, side="right") - 1
    if np.any(k < 0) or np.any(files > finals[np.maximum(k, 0)]):
        raise ValueError("Hi ha imatges fora de les parts")
    idx = files[:, None] + np.asarray(DESPLACAMENTS)[None, :]
    dins = (idx >= inicis[k][:, None]) & (idx <= finals[k][:, None])
    x = c[np.clip(idx, 0, len(c) - 1)] * dins[..., None]
    return x.reshape(len(files), -1).astype(np.float32)


def mostres(t: Tracking, trams: tuple[tuple[int, int, int], ...], files: np.ndarray,
            etiquetes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Les finestres de `files` amb les seves etiquetes, i també amb els equips girats (com `model.mostres`)."""
    x = np.concatenate([finestra(canals(t, trams), trams, files), finestra(canals(girat(t), trams), trams, files)])
    return x, np.concatenate([etiquetes, GIRA[etiquetes]]).astype(np.int8)


def entrena(x: np.ndarray, y: np.ndarray, passades: int = PASSADES) -> tuple[Xarxa, list[float]]:
    """La xarxa, i la pèrdua de cada passada. `x` (float32) s'estandarditza al seu lloc, per la memòria."""
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.neural_network import MLPClassifier

    mitjana, escala = _mitjana_i_escala(x)
    x -= mitjana.astype(np.float32)
    x /= escala.astype(np.float32)
    xarxa = MLPClassifier(hidden_layer_sizes=OCULTES, activation="relu", solver="adam", alpha=L2, batch_size=LOT,
                          max_iter=passades, shuffle=True, random_state=LLAVOR, early_stopping=False, tol=0.0,
                          n_iter_no_change=passades + 1)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)          # fa les passades que toca, ni més ni menys
        xarxa.fit(x, y)
    if list(xarxa.classes_) != list(range(len(CLASSES))):
        raise ValueError("Per entrenar la xarxa calen imatges de H, d'A i de D")
    return (Xarxa(mitjana, escala, tuple(w.astype(np.float64) for w in xarxa.coefs_),
                  tuple(b.astype(np.float64) for b in xarxa.intercepts_)), [float(p) for p in xarxa.loss_curve_])


def probabilitats(xarxa: Xarxa, t: Tracking, trams: tuple[tuple[int, int, int], ...]) -> np.ndarray:
    """(n, 3): P(H), P(A) i P(D), la mitjana de la vista directa i de la girada, arrodonides; NaN fora de les parts."""
    c, c_girat = canals(t, trams), canals(girat(t), trams)
    out = np.full((len(c), len(CLASSES)), np.nan)
    dins = np.concatenate([np.arange(a, b + 1) for _, a, b in trams])
    for s in range(0, len(dins), TROS):
        f = dins[s:s + TROS]
        p = (endavant(xarxa, finestra(c, trams, f)) + endavant(xarxa, finestra(c_girat, trams, f))[:, GIRA]) / 2
        out[f] = np.round(p * ARRODONIMENT) / ARRODONIMENT
    return out


def endavant(xarxa: Xarxa, x: np.ndarray) -> np.ndarray:
    """Les probabilitats de la xarxa per a cada fila de `x`, amb numpy (en float64)."""
    h = (x.astype(np.float64) - xarxa.mitjana) / xarxa.escala
    for w, b in zip(xarxa.pesos[:-1], xarxa.biaixos[:-1]):
        h = np.maximum(h @ w + b, 0.0)
    z = h @ xarxa.pesos[-1] + xarxa.biaixos[-1]
    e = np.exp(z - z.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)


def senyals_segon(proba: np.ndarray, trams: tuple[tuple[int, int, int], ...]) -> pd.DataFrame:
    """Per al segon classificador: les tres probabilitats de la xarxa i el seu context (`context.calcula`), amb noms
    propis (`px`) i la convenció de `senyals.py`, perquè `senyals.intercanvia` també els giri."""
    ctx = context.calcula(proba, trams)
    ctx.columns = [_nom(c) for c in ctx.columns]
    seves = pd.DataFrame({"px_h": proba[:, H], "px_a": proba[:, A], "px_d": proba[:, D]}).astype(np.float32)
    return pd.concat([seves, ctx], axis=1)


def desa(xarxa: Xarxa, cami: Path) -> None:
    capes = {f"w{i}": w for i, w in enumerate(xarxa.pesos)} | {f"b{i}": b for i, b in enumerate(xarxa.biaixos)}
    np.savez(cami, mitjana=xarxa.mitjana, escala=xarxa.escala, **capes)


def carrega(cami: Path) -> Xarxa:
    with np.load(cami, allow_pickle=False) as z:
        n = sum(1 for k in z.files if k.startswith("w"))
        return Xarxa(z["mitjana"], z["escala"], tuple(z[f"w{i}"] for i in range(n)),
                     tuple(z[f"b{i}"] for i in range(n)))


# --- una part ---------------------------------------------------------------------------------------------------

def _una_part(pilota: np.ndarray, casa: np.ndarray, fora: np.ndarray, camp: np.ndarray) -> np.ndarray:
    casa_x, fora_x = np.nanmedian(senyals._mitjana(casa[..., 0])), np.nanmedian(senyals._mitjana(fora[..., 0]))
    sentit = 1.0 if casa_x <= fora_x else -1.0               # com a `senyals.py`
    centre = camp / 2

    def gira(xy: np.ndarray) -> np.ndarray:                   # des del mig del camp, amb H atacant cap a les x positives
        return (xy - centre) * sentit

    pil = gira(pilota)
    hi_es = ~np.isnan(pil[:, 0])
    columnes = [hi_es[:, None].astype(float), np.where(hi_es[:, None], pil, 0.0),
                np.where(hi_es[:, None], _velocitat(pil), 0.0)]
    for jugadors in (casa, fora):
        columnes.append(_propers(gira(jugadors), pil, hi_es))
    return np.concatenate(columnes, axis=1)


def _propers(jug: np.ndarray, pil: np.ndarray, hi_es: np.ndarray) -> np.ndarray:
    """(n, PROPERS × 4): dx, dy, vx i vy dels jugadors més propers a la pilota, per ordre."""
    n = len(jug)
    if jug.shape[1] < PROPERS:
        jug = np.concatenate([jug, np.full((n, PROPERS - jug.shape[1], 2), np.nan)], axis=1)
    d = np.hypot(jug[..., 0] - pil[:, None, 0], jug[..., 1] - pil[:, None, 1])
    d = np.where(np.isnan(d), np.inf, d)
    ordre = np.argsort(d, axis=1, kind="stable")[:, :PROPERS]
    files = np.arange(n)[:, None]
    lluny = ~np.isfinite(d[files, ordre])[..., None]
    rel = np.where(lluny, LLUNY_M, jug[files, ordre] - pil[:, None])
    vel = np.where(lluny, 0.0, _velocitat(jug)[files, ordre])
    sense = ~hi_es[:, None, None]
    return np.concatenate([np.where(sense, 0.0, rel), np.where(sense, 0.0, vel)], axis=2).reshape(n, PROPERS * 4)


def _velocitat(xy: np.ndarray) -> np.ndarray:
    """(p(t + MIG) − p(t − MIG)) en m/s; 0 a les vores de la part i on falta l'una o l'altra."""
    v = np.zeros(xy.shape)
    if len(xy) > 2 * MIG:
        v[MIG:-MIG] = np.nan_to_num((xy[2 * MIG:] - xy[:-2 * MIG]) * FPS / (2 * MIG), nan=0.0)
    return v


def _mitjana_i_escala(x: np.ndarray, tros: int = 100_000) -> tuple[np.ndarray, np.ndarray]:
    """La mitjana i la desviació de cada columna, a trossos i en float64 (sense una còpia sencera en float64)."""
    suma = np.zeros(x.shape[1])
    quadrats = np.zeros(x.shape[1])
    for s in range(0, len(x), tros):
        bloc = x[s:s + tros].astype(np.float64)
        suma += bloc.sum(axis=0)
        quadrats += (bloc ** 2).sum(axis=0)
    mitjana = suma / len(x)
    escala = np.sqrt(np.maximum(quadrats / len(x) - mitjana ** 2, 0.0))
    return mitjana, np.where(escala > 0, escala, 1.0)


def _nom(col: str) -> str:
    """Els noms de `context.calcula` amb `px` (dif_p → dif_px, morta → mortax, p_h → px_h)."""
    if col.startswith("dif_p"):
        return "dif_px" + col[len("dif_p"):]
    if col.startswith("morta"):
        return "mortax" + col[len("morta"):]
    if col.startswith("p_"):
        return "px_" + col[len("p_"):]
    raise ValueError(f"Un senyal del context que no conec: {col}")
