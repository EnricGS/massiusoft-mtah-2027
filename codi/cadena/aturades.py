"""Els senyals de l'aturada per al segon classificador d'A contacte (T3k del pla per tocs, `docs/pla-tocs.md`, «T3k»).

On més falla la pilota morta (D) és a les vores de les aturades, i sobretot a l'inici. Els senyals de `senyals.py`
miren la pilota fora del camp i els jugadors quiets en finestres centrades; aquests diuen:

- **La pilota cap a fora:** on no es veu, on seria si hagués seguit en línia recta amb la darrera velocitat (fins a
  `EXTRAPOLA_S`), i quant és fora del camp; on es veu, on és. En tots dos casos, quants segons li falten per creuar la
  línia per on sortiria, amb aquella velocitat (fins a `LINIA_S`; 0 si ja és fora). Les velocitats de més de
  `VMAX_PILOTA_MS` són un salt de la pilota, i no es fan servir.
- **Els jugadors que frenen o arrenquen:** la velocitat mitjana de tots els jugadors en els darrers 1, 2 i 4 s menys
  la dels 1, 2 i 4 s següents (positiva, frenen; negativa, arrenquen), i la part dels jugadors que frenen més de
  `FRENA_MS` del segon d'abans al d'après. Les velocitats de més de `VMAX_MS` són d'un slot que ha canviat de
  jugador, i no es compten.
- **La pilota quieta:** on es veu, quants segons fa que és quieta (a menys de `senyals.QUIET_MS`, mesurat en un segon
  com la dels jugadors: en menys temps, el soroll de la posició ja la mou) i quants en falten perquè es mogui; 0 si es
  mou.

No depenen de quin equip és quin: cap no acaba en `_h` o `_a` ni comença per `dif_`, i `senyals.intercanvia` els deixa
igual. Cap finestra passa d'una part a l'altra, i fora de les parts són NaN.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cadena import control, senyals
from cadena.llegeix import Tracking

FPS = senyals.FPS
EXTRAPOLA_S = 1.5
LINIA_S = 5.0
COSTATS_S = (1, 2, 4)
FRENA_MS = 2.0
VMAX_MS = 12.0
VMAX_PILOTA_MS = 40.0


def calcula(t: Tracking, trams: tuple[tuple[int, int, int], ...]) -> pd.DataFrame:
    """Una fila per imatge (float32), amb el tracking en una fila per imatge (`senyals.a_reixa`)."""
    n = len(t.fotograma)
    if not np.array_equal(t.fotograma, np.arange(n)):
        raise ValueError("Els senyals volen una fila per imatge: primer, a_reixa")
    if not trams:
        raise ValueError("No hi ha cap part")
    escala = np.asarray(t.camp_m, float)
    trossos = []
    for _, inici, fi in trams:
        part = slice(inici, fi + 1)
        f = _pilota(t.pilota[part] * escala, t.camp_m)
        f |= _jugadors(np.concatenate([t.casa[part], t.fora[part]], axis=1) * escala)
        trossos.append(pd.DataFrame(f).set_axis(pd.RangeIndex(inici, fi + 1)))
    return pd.concat(trossos).reindex(pd.RangeIndex(n)).astype(np.float32)


# --- una part ---------------------------------------------------------------------------------------------------

def _pilota(pilota: np.ndarray, camp: tuple[float, float]) -> dict[str, np.ndarray]:
    llarg, ample = camp
    v = control._vector_velocitat(pilota)
    vista = ~np.isnan(pilota[:, 0])
    bona = vista & (np.hypot(v[:, 0], v[:, 1]) <= VMAX_PILOTA_MS)            # NaN, tampoc
    darrera = senyals._ultima(bona)
    hi_ha = darrera >= 0
    on = np.maximum(darrera, 0)
    dt = np.minimum((np.arange(len(pilota)) - darrera) / FPS, EXTRAPOLA_S)
    pos = np.where(vista[:, None], pilota, pilota[on] + v[on] * dt[:, None])
    x, y = pos[:, 0], pos[:, 1]
    fora = np.maximum.reduce([-x, x - llarg, -y, y - ample, np.zeros(len(x))])
    vx, vy = v[on, 0], v[on, 1]
    with np.errstate(divide="ignore", invalid="ignore"):
        tx = np.where(vx > 0, (llarg - x) / vx, np.where(vx < 0, -x / vx, np.inf))
        ty = np.where(vy > 0, (ample - y) / vy, np.where(vy < 0, -y / vy, np.inf))
    a_linia = np.where(fora > 0, 0.0, np.clip(np.fmin(tx, ty), 0.0, LINIA_S))
    vp = senyals._velocitat(pilota, senyals.MIG_JUGADORS)
    no_quieta = ~(vp < senyals.QUIET_MS)                        # sense velocitat, tampoc: talla la quietud
    des = np.minimum(senyals._des_de(no_quieta) / FPS, senyals.TOPALL_S)
    fins = np.minimum(senyals._des_de(no_quieta[::-1])[::-1] / FPS, senyals.TOPALL_S)
    sense = np.isnan(vp)
    return {"aturada_fora": np.where(hi_ha, fora, np.nan), "aturada_a_linia": np.where(hi_ha, a_linia, np.nan),
            "aturada_quieta_des": np.where(sense, np.nan, des), "aturada_quieta_fins": np.where(sense, np.nan, fins)}


def _jugadors(jug: np.ndarray) -> dict[str, np.ndarray]:
    vel = senyals._velocitat(jug, senyals.MIG_JUGADORS)
    vel = np.where(vel > VMAX_MS, np.nan, vel)
    tots = senyals._mitjana(vel)
    f = {}
    for s in COSTATS_S:
        abans = senyals._finestra(senyals._desplaca(tots, -1), s * FPS, "mean", "passat")
        despres = senyals._finestra(senyals._desplaca(tots, 1), s * FPS, "mean", "futur")
        f[f"aturada_frena@{s}s"] = abans - despres
    abans, despres = _costats_per_slot(vel, FPS)
    frenen = np.where(np.isnan(abans) | np.isnan(despres), np.nan, (abans - despres > FRENA_MS).astype(float))
    f["aturada_frenen"] = senyals._mitjana(frenen)
    return f


def _costats_per_slot(valors: np.ndarray, w: int) -> tuple[np.ndarray, np.ndarray]:
    """Per a cada slot, la mitjana de les `w` imatges d'abans (sense aquesta) i de les `w` d'après, sense els NaN."""
    taula = pd.DataFrame(valors)
    abans = taula.shift(1).rolling(w, min_periods=1).mean()
    despres = taula.iloc[::-1].shift(1).rolling(w, min_periods=1).mean().iloc[::-1]
    return abans.to_numpy(), despres.to_numpy()
