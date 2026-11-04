"""Els senyals del control per al classificador d'A (T3d del pla per tocs, `docs/pla-tocs.md`; D-24).

La possessió canvia quan un jugador de l'altre equip toca i controla la pilota. Els senyals de `senyals.py` diuen qui
és més a prop, de mitjana, en finestres; aquests diuen què passa amb la pilota en aquell moment:

- **Els tocs** de `tocs.py`, amb uns paràmetres permissius (`PARAMETRES`): de quin equip és el darrer (fins a la
  imatge, inclosa) i el proper (després), quant fa i quant falta, com és cada un, de quin equip és el penúltim, i
  quants n'ha fet cada equip al voltant, abans i després. Els falsos hi són: el classificador aprèn quan se'n pot
  refiar.
- **El control:** la velocitat de la pilota respecte del jugador més proper de cada equip (si van junts, la porta
  ell), i quina part de l'últim segon i del proper hi ha un jugador de cada equip a `CONTROL_M` o menys amb la pilota
  anant amb ell (a `CONTROL_MS` o menys).
- **El tremolor de la pilota** a cada part (`tocs.soroll_lliure`): diu com de fiables són els tocs i el control.

Segueixen la convenció de `senyals.py` (`_h` i `_a` per equip, `dif_` per a H − A, `@` per a les finestres), i per
això `senyals.intercanvia` també els gira. Cap finestra passa d'una part a l'altra, i fora de les parts són NaN.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cadena import senyals, tocs
from cadena.llegeix import Tracking
from possessio.oficial import possession_metrics as pm

FPS = senyals.FPS
PARAMETRES = tocs.Parametres(k=5, canvi_ms=5.0, abast_m=2.0)
MIG = 2                     # la velocitat de la pilota i del jugador, en ±2 imatges, com MIG_PILOTA
CONTROL_M = 1.5
CONTROL_MS = 3.0
FINESTRES_TOCS = (25, 75)   # al voltant
COSTAT_TOCS = 50            # abans i després
COSTAT_CONTROL = 25


def calcula(t: Tracking, trams: tuple[tuple[int, int, int], ...]) -> pd.DataFrame:
    """Una fila per imatge (float32), amb el tracking en una fila per imatge (`senyals.a_reixa`)."""
    n = len(t.fotograma)
    if not np.array_equal(t.fotograma, np.arange(n)):
        raise ValueError("Els senyals volen una fila per imatge: primer, a_reixa")
    if not trams:
        raise ValueError("No hi ha cap part")
    trobats = tocs.detecta(t, trams, PARAMETRES)
    escala = np.asarray(t.camp_m, float)
    trossos = []
    for tram in trams:
        _, inici, fi = tram
        part = slice(inici, fi + 1)
        seus = (trobats.imatge >= inici) & (trobats.imatge <= fi)
        f = _tocs(fi + 1 - inici, trobats.imatge[seus] - inici, trobats.equip[seus], trobats.canvi_ms[seus],
                  trobats.propi_m[seus], trobats.altre_m[seus])
        f |= _control(t.pilota[part] * escala, t.casa[part] * escala, t.fora[part] * escala)
        f["tremolor"] = np.full(fi + 1 - inici, tocs.soroll_lliure(t, (tram,), PARAMETRES.k))
        trossos.append(pd.DataFrame(f).set_axis(pd.RangeIndex(inici, fi + 1)))
    return pd.concat(trossos).reindex(pd.RangeIndex(n)).astype(np.float32)


# --- una part ---------------------------------------------------------------------------------------------------

def _tocs(n: int, imatge: np.ndarray, equip: np.ndarray, canvi: np.ndarray, propi: np.ndarray,
          altre: np.ndarray) -> dict[str, np.ndarray]:
    signe = np.where(equip == pm.H, 1.0, -1.0)
    de_h = equip == pm.H
    # el propi és el de l'equip del toc: el d'H i el d'A, perquè girar els equips els giri
    d_h, d_a = np.where(de_h, propi, altre), np.where(de_h, altre, propi)
    numero = np.full(n, -1)
    numero[imatge] = np.arange(len(imatge))
    idx = np.arange(n)
    on = senyals._ultima(numero >= 0)
    darrer = np.where(on >= 0, numero[np.maximum(on, 0)], -1)           # el número del toc, fins aquí (inclosa)
    proper = np.r_[np.minimum.accumulate(np.where(numero >= 0, numero, len(imatge))[::-1])[::-1][1:], len(imatge)]
    proper[proper >= len(imatge)] = -1                                  # el número del toc, des de la següent
    f = {}
    for nom, quin in (("abans", darrer), ("despres", proper)):
        f[f"dif_toc_{nom}"] = _del_toc(signe, quin)
        f[f"toc_canvi_{nom}"] = _del_toc(canvi, quin)
        f[f"toc_d_{nom}_h"] = _del_toc(d_h, quin)
        f[f"toc_d_{nom}_a"] = _del_toc(d_a, quin)
    sostre = senyals.TOPALL_S
    f["des_toc"] = np.where(darrer >= 0, np.minimum((idx - _del_toc(imatge, darrer, np.inf)) / FPS, sostre), sostre)
    f["fins_toc"] = np.where(proper >= 0, np.minimum((_del_toc(imatge, proper, np.inf) - idx) / FPS, sostre), sostre)
    f["dif_toc_penultim"] = _del_toc(signe, np.where(darrer >= 1, darrer - 1, -1))
    for e, del_equip in (("h", de_h), ("a", ~de_h)):
        compta = np.zeros(n)
        compta[imatge[del_equip]] = 1.0
        for w in FINESTRES_TOCS:
            f[f"tocs_{e}@{w}"] = senyals._finestra(compta, w, "sum")
        f[f"tocs_{e}@p{COSTAT_TOCS}"] = senyals._finestra(compta, COSTAT_TOCS, "sum", "passat")
        f[f"tocs_{e}@f{COSTAT_TOCS}"] = senyals._finestra(compta, COSTAT_TOCS, "sum", "futur")
    return f


def _del_toc(valors: np.ndarray, quin: np.ndarray, sostre: float = senyals.TOPALL_M) -> np.ndarray:
    """El valor del toc número `quin` a cada imatge, i NaN on `quin` és −1. Es talla a `sostre`: l'altre equip pot
    no veure's (inf)."""
    if not len(valors):
        return np.full(len(quin), np.nan)
    return np.where(quin >= 0, np.minimum(np.asarray(valors, float)[np.maximum(quin, 0)], sostre), np.nan)


def _control(pilota: np.ndarray, casa: np.ndarray, fora: np.ndarray) -> dict[str, np.ndarray]:
    vpil = _vector_velocitat(pilota)
    f, vrel = {}, {}
    for e, jug in (("h", casa), ("a", fora)):
        d = np.linalg.norm(jug - pilota[:, None, :], axis=2)
        lliure = np.isnan(d).all(axis=1)
        mes_proper = np.argmin(np.where(np.isnan(d), np.inf, d), axis=1)
        dist = np.where(lliure, np.nan, d[np.arange(len(d)), mes_proper])
        vjug = _vector_velocitat(jug)[np.arange(len(d)), mes_proper]
        vrel[e] = np.where(lliure, np.nan, np.linalg.norm(vpil - vjug, axis=1))
        f[f"vrel_{e}"] = np.minimum(vrel[e], senyals.TOPALL_M)
        controla = ((dist <= CONTROL_M) & (vrel[e] <= CONTROL_MS)).astype(float)
        f[f"control_{e}"] = controla
        f[f"control_{e}@p{COSTAT_CONTROL}"] = senyals._finestra(controla, COSTAT_CONTROL, "mean", "passat")
        f[f"control_{e}@f{COSTAT_CONTROL}"] = senyals._finestra(controla, COSTAT_CONTROL, "mean", "futur")
    f["dif_vrel"] = f["vrel_h"] - f["vrel_a"]
    return f


def _vector_velocitat(xy: np.ndarray) -> np.ndarray:
    """(p(t + MIG) − p(t − MIG)) en m/s, amb la mateixa forma que `xy`; NaN a les vores i on falta l'una o l'altra."""
    v = np.full(xy.shape, np.nan)
    if len(xy) > 2 * MIG:
        v[MIG:-MIG] = (xy[2 * MIG:] - xy[:-2 * MIG]) * FPS / (2 * MIG)
    return v
