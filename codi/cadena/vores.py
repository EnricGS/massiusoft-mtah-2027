"""Les vores dels canvis, afinades (T3ae del pla per tocs, `docs/pla-tocs.md`, «T3ae»; D-66).

Després del decodificador, cada canvi de la predicció es pot moure fins a `RADI` imatges (0,5 s) endavant o endarrere:

- **Els canvis** (`canvis`): a cada part, cada imatge on la predicció canvia d'un equip a l'altre, d'un equip a la D o
  de la D a un equip. La imatge del canvi és la primera de la possessió nova.
- **On es pot moure** (`finestra` i `mou`): a `RADI` imatges o menys, dins de la part, sense passar mai el canvi d'abans
  ni el de després, sense que cap possessió es faci més curta que la durada mínima del decodificador (si ja ho era, no
  s'escurça més) i sense posar mai la D a una imatge netejada. Els canvis es mouen per ordre, de l'inici de la part al
  final.
- **Les vores** (`amb_les_vores`): un LightGBM dona a cada imatge on es pot moure el canvi la probabilitat que el canvi
  de la veritat sigui allà, i el canvi va a la més probable. Si n'hi ha més d'una, la més a prop del canvi: si totes
  són iguals, no es mou.
- **El que mira** (`trets`): a quantes imatges és del canvi i de quin tipus és, les probabilitats del segon i de les
  cinc xarxes i com canvien de `LLUNY` imatges abans a `LLUNY` després, la q, la pilota (si es veu, la velocitat, i
  quant li canvien la velocitat i la direcció) i la distància de la pilota al jugador més proper de cada equip. Els
  equips hi surten com l'equip del canvi (el que entra; si el canvi és cap a la D, el que surt) i l'altre: girar els
  equips no canvia res.
- **Amb què aprèn** (`mostres`): a cada canvi de la predicció, totes les imatges de la finestra, i la bona és la del
  canvi de la veritat del mateix tipus més proper, si n'hi ha un a `RADI` imatges o menys (`la_bona`); si no, cap.
"""

from __future__ import annotations

from dataclasses import dataclass

import lightgbm as lgb
import numpy as np

from cadena import model
from cadena.llegeix import Tracking
from possessio.oficial import possession_metrics as pm

RADI = 12                       # imatges a banda i banda: 0,48 s
LLUNY = 3                       # com canvien les probabilitats: de 3 imatges abans a 3 després
DIRECCIO = 2                    # la velocitat de la pilota abans i després del toc, en 2 imatges
QUIETA = 0.5                    # m/s: més lenta, la direcció no es mira
EQUIP_A_EQUIP, A_LA_D, DE_LA_D = range(3)
H, A, D = (model.CLASSES.index(c) for c in (pm.H, pm.A, pm.D))
TRETS = ("desplaçament", "tipus",
         "segon de l'equip", "segon de l'altre", "segon de la D",
         "canvi del segon de l'equip", "canvi del segon de l'altre", "canvi del segon de la D",
         "xarxes de l'equip", "xarxes de l'altre", "xarxes de la D",
         "canvi de les xarxes de l'equip", "canvi de les xarxes de l'altre", "canvi de les xarxes de la D",
         "q", "es veu la pilota", "velocitat de la pilota", "canvi de velocitat", "canvi de direcció",
         "jugador més proper de l'equip", "jugador més proper de l'altre")
PARAMS = {k: v for k, v in model.PARAMS.items() if k != "num_class"} | {"objective": "binary"}
RONDES = model.RONDES
Trams = tuple[tuple[int, int, int], ...]


@dataclass(frozen=True)
class Canvi:
    t: int          # la primera imatge de la possessió nova
    de: int         # el codi de la mètrica d'abans
    a: int          # i el de després
    inici: int      # la primera imatge de la part
    fi: int         # l'última, inclosa


@dataclass(frozen=True)
class Senyals:
    segon: np.ndarray       # (n, 3) les probabilitats del segon, a les columnes de `model.CLASSES`
    xarxes: np.ndarray      # (n, 3) les de les cinc xarxes
    q: np.ndarray           # (n,)
    pilota: np.ndarray      # (n, 4) si es veu, la velocitat (m/s), quant canvia la velocitat i quant la direcció (rad)
    propers: np.ndarray     # (n, 2) la distància (m) de la pilota al jugador més proper d'H i al d'A; NaN sense pilota


def canvis(x: np.ndarray, trams: Trams) -> list[Canvi]:
    """Els canvis de `x` (codis de la mètrica) dins de cada part, per ordre."""
    out = []
    for _, inici, fi in trams:
        w = x[inici:fi + 1]
        out += [Canvi(inici + int(k), int(w[k - 1]), int(w[k]), inici, fi) for k in np.flatnonzero(w[1:] != w[:-1]) + 1]
    return out


def tipus(c: Canvi) -> int:
    return A_LA_D if c.a == pm.D else DE_LA_D if c.de == pm.D else EQUIP_A_EQUIP


def equips(c: Canvi) -> tuple[int, int]:
    """L'equip del canvi (el que entra; si el canvi és cap a la D, el que surt) i l'altre, com a columnes."""
    equip = model.CLASSES.index(c.de if c.a == pm.D else c.a)
    return equip, A if equip == H else H


def finestra(c: Canvi) -> np.ndarray:
    """On pot anar el canvi: a `RADI` imatges o menys, dins de la part, i mai a la primera (la possessió d'abans hi
    desapareixeria)."""
    return np.arange(max(c.inici + 1, c.t - RADI), min(c.fi, c.t + RADI) + 1)


def de_la_veritat(toc: np.ndarray, valids: list[tuple[int, int]]) -> dict[tuple[int, int], np.ndarray]:
    """Els canvis de la veritat dins de cada tram vàlid ([inici, fi)), per tipus (de quina classe a quina)."""
    out: dict[tuple[int, int], list[int]] = {}
    for c in canvis(toc, tuple((0, a, b - 1) for a, b in valids)):
        out.setdefault((c.de, c.a), []).append(c.t)
    return {k: np.array(v) for k, v in out.items()}


def la_bona(c: Canvi, de_la_veritat_: dict[tuple[int, int], np.ndarray]) -> int | None:
    """La imatge del canvi de la veritat del mateix tipus més proper, si és a `RADI` imatges o menys; si n'hi ha dos a
    la mateixa distància, el primer."""
    ts = de_la_veritat_.get((c.de, c.a))
    if ts is None or not len(ts):
        return None
    j = np.searchsorted(ts, c.t)
    propers = [int(ts[k]) for k in (j - 1, j) if 0 <= k < len(ts)]
    millor = min(propers, key=lambda t: (abs(t - c.t), t))
    return millor if abs(millor - c.t) <= RADI else None


def _desplacat(x: np.ndarray, k: int) -> np.ndarray:
    """`x[i + k]` a cada `i`, i NaN on cau fora."""
    out = np.full_like(x, np.nan)
    if k > 0:
        out[:-k] = x[k:]
    elif k < 0:
        out[-k:] = x[:k]
    else:
        out[:] = x
    return out


def _pilota(xy: np.ndarray) -> np.ndarray:
    """(m, 4) d'una part, amb la pilota en metres."""
    norma = lambda v: np.sqrt((v ** 2).sum(-1))  # noqa: E731
    velocitat = norma(_desplacat(xy, 1) - _desplacat(xy, -1)) * pm.FPS / 2
    abans = (xy - _desplacat(xy, -DIRECCIO)) * pm.FPS / DIRECCIO
    despres = (_desplacat(xy, DIRECCIO) - xy) * pm.FPS / DIRECCIO
    v_abans, v_despres = norma(abans), norma(despres)
    with np.errstate(invalid="ignore", divide="ignore"):
        cos = (abans * despres).sum(-1) / (v_abans * v_despres)
    direccio = np.where((v_abans > QUIETA) & (v_despres > QUIETA), np.arccos(np.clip(cos, -1.0, 1.0)), np.nan)
    return np.column_stack([~np.isnan(xy[:, 0]), velocitat, v_despres - v_abans, direccio])


def _mes_proper(jugadors: np.ndarray, pilota: np.ndarray) -> np.ndarray:
    d = np.sqrt(((jugadors - pilota[:, None, :]) ** 2).sum(-1))
    d = np.where(np.isnan(d), np.inf, d).min(axis=1, initial=np.inf)
    return np.where(np.isinf(d), np.nan, d)


def senyals(t: Tracking, trams: Trams, segon: np.ndarray, xarxes: np.ndarray, q: np.ndarray) -> Senyals:
    """Els senyals de cada imatge d'un partit. La pilota, dins de cada part (a la vora, NaN)."""
    escala = np.asarray(t.camp_m, float)
    xy = t.pilota * escala
    pilota = np.full((len(xy), 4), np.nan)
    for _, inici, fi in trams:
        pilota[inici:fi + 1] = _pilota(xy[inici:fi + 1])
    propers = np.column_stack([_mes_proper(t.casa * escala, xy), _mes_proper(t.fora * escala, xy)])
    return Senyals(np.asarray(segon, float), np.asarray(xarxes, float), np.asarray(q, float), pilota, propers)


def trets(c: Canvi, finestra_: np.ndarray, s: Senyals) -> np.ndarray:
    """(len(finestra_), len(TRETS)): el que mira el LightGBM a cada imatge on pot anar el canvi."""
    equip, altre = equips(c)
    abans = np.clip(finestra_ - LLUNY, c.inici, c.fi)
    despres = np.clip(finestra_ + LLUNY, c.inici, c.fi)
    cols = [finestra_ - c.t, np.full(len(finestra_), tipus(c))]
    for p in (s.segon, s.xarxes):
        canvi = p[despres] - p[abans]
        cols += [p[finestra_, equip], p[finestra_, altre], p[finestra_, D],
                 canvi[:, equip], canvi[:, altre], canvi[:, D]]
    cols += [s.q[finestra_], *s.pilota[finestra_].T, s.propers[finestra_, equip], s.propers[finestra_, altre]]
    return np.column_stack(cols).astype(float)


def mostres(pred: np.ndarray, trams: Trams, s: Senyals,
            de_la_veritat_: dict[tuple[int, int], np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """Totes les imatges de la finestra de cada canvi de `pred`, i 1 a la bona."""
    xs, ys = [np.empty((0, len(TRETS)))], [np.empty(0, np.int8)]
    for c in canvis(pred, trams):
        f = finestra(c)
        xs.append(trets(c, f, s))
        ys.append((f == la_bona(c, de_la_veritat_)).astype(np.int8))
    return np.concatenate(xs), np.concatenate(ys)


def entrena(x: np.ndarray, y: np.ndarray, rondes: int = RONDES) -> lgb.Booster:
    return lgb.train(PARAMS, lgb.Dataset(x, label=y, free_raw_data=True), num_boost_round=rondes)


def mou(pred: np.ndarray, d_min: int, netejades: np.ndarray, canvis_: list[Canvi], finestres: list[np.ndarray],
        puntuacions: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """La predicció amb cada canvi a la imatge de més puntuació de la seva finestra on pot anar, i on ha anat cada
    canvi. `canvis_` són els de `pred`, per ordre, amb la seva finestra i la puntuació de cada imatge."""
    out = pred.copy()
    posicions = np.array([c.t for c in canvis_], dtype=np.int64)
    for k, (c, f, punts) in enumerate(zip(canvis_, finestres, puntuacions)):
        mateixa_part = lambda j: 0 <= j < len(canvis_) and canvis_[j].inici == c.inici  # noqa: E731
        abans = posicions[k - 1] if mateixa_part(k - 1) else c.inici
        despres = canvis_[k + 1].t if mateixa_part(k + 1) else c.fi + 1
        pot = (f - abans >= min(d_min, c.t - abans)) & (despres - f >= min(d_min, despres - c.t))
        if c.a == pm.D:                          # endarrere, la D s'allarga
            pot &= np.array([not netejades[t:c.t].any() for t in f])
        if c.de == pm.D:                         # endavant, també
            pot &= np.array([not netejades[c.t:t].any() for t in f])
        candidates = np.flatnonzero(pot)
        millor = min(candidates, key=lambda i: (-punts[i], abs(f[i] - c.t), f[i]))
        posicions[k] = f[millor]
    for k, c in enumerate(canvis_):
        t = int(posicions[k])
        if t < c.t:
            out[t:c.t] = c.a
        elif t > c.t:
            out[c.t:t] = c.de
    return out, posicions


def amb_les_vores(entrenat: lgb.Booster, pred: np.ndarray, trams: Trams, d_min: int, netejades: np.ndarray,
                  s: Senyals) -> tuple[np.ndarray, list[Canvi], np.ndarray]:
    """La predicció amb les vores del LightGBM, els seus canvis d'abans i on ha anat cadascun."""
    canvis_ = canvis(pred, trams)
    if not canvis_:
        return pred.copy(), canvis_, np.empty(0, np.int64)
    finestres = [finestra(c) for c in canvis_]
    p = entrenat.predict(np.concatenate([trets(c, f, s) for c, f in zip(canvis_, finestres)]))
    puntuacions = np.split(p, np.cumsum([len(f) for f in finestres])[:-1])
    out, posicions = mou(pred, d_min, netejades, canvis_, finestres, puntuacions)
    return out, canvis_, posicions
