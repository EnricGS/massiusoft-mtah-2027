"""El model A dins de la cadena: del tracking a un codi per imatge del vídeo. És A xarxes (T3o, D-43).

1. L'ATD, en una fila per imatge (`senyals.a_reixa`), i els seus senyals dins de cada part puntuada.
2. Les peces desades a `model-a/`, entrenades només amb les dades obertes del banc (`python -I -m banc.model_final`):
   - **el primer classificador** (T3h): P(H), P(A) i P(D) amb els senyals d'A (`senyals.py`), els del control
     (`control.py`) i els del contacte (`contacte.py`);
   - **el classificador de canvis** (T3i): la q, la probabilitat que hi hagi un canvi d'equip a 6 imatges o menys,
     amb aquests senyals i el context de les probabilitats del primer (`context.py`);
   - **les cinc xarxes** (T3o, `xarxes.py`): la mitjana de les seves P(H), P(A) i P(D), fetes de les posicions al
     voltant de la pilota;
   - **el segon classificador** (T3o): amb els senyals del primer, el context, els de l'aturada (`aturades.py`) i
     els de les xarxes (`xarxa.senyals_segon`).

   Abans de fer-les servir, se'n comprova:
   - l'empremta, que cobreix els tres classificadors, les cinc xarxes i la seva fitxa;
   - que siguin del codi d'ara (els senyals, els models, el decodificador i les versions de les biblioteques);
   - que els senyals siguin els seus, i que les xarxes tinguin la forma que toca.
3. **Les imatges sense tracking** (ni pilota ni cap jugador):
   - enmig d'una part, no diuen res. Hi posem el prior a les probabilitats del primer (abans de fer el context), a
     les de les xarxes i a les del segon, i a la q, la part de les imatges d'entrenament que són a prop d'un canvi
     (`q_prior`). El decodificador continua el que venia;
   - al principi d'una part, abans que l'ATD hi tingui ningú, o al final, quan ja no hi ha ningú, la pilota és
     morta (D). Una part no ha començat fins al servei, i el mateix val per al final. Aquestes vores no entren al
     decodificador, perquè no hi allarguin cap possessió;
   - una part sencera sense ningú: X. No en sabem res.
4. El decodificador amb el cost après dels canvis (`decodifica_canvis.py`), amb la w, la λ i la durada mínima
   triades al banc, i X fora de les parts.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from lightgbm.basic import LightGBMError

from cadena import (aturades, contacte, context, control, decodifica_canvis, decodifica_tocs, model, senyals, tocs,
                    xarxa, xarxes)
from cadena.llegeix import Tracking
from possessio import decodificacio
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

DIR_MODEL = Path(__file__).resolve().parent / "model-a"
LLETRES = np.array(["H", "A", "D", "X"])           # pel codi de la mètrica: H = 0, A = 1, D = 2, X = 3
CLASSIFICADORS = ("primer.txt", "segon.txt", "canvis.txt")
XARXES = tuple(f"xarxa-{i}.npz" for i in range(xarxes.N))
FITXERS = (*CLASSIFICADORS, *XARXES)              # i la fitxa


class ErrorDelModel(Exception):
    """El model desat no és el que toca. El missatge és un text fix, sense cap dada: pot sortir a la consola."""


@dataclass(frozen=True)
class Entrenat:
    primer: lgb.Booster                 # P(H), P(A) i P(D) amb els senyals del primer
    segon: lgb.Booster                  # el mateix, amb el context, l'aturada i les xarxes
    canvis: lgb.Booster                 # la q
    xarxes: tuple[xarxa.Xarxa, ...]
    prior: np.ndarray                   # H, A i D a les mostres dels dos classificadors
    q_prior: float                      # la part de les mostres del classificador de canvis a prop d'un canvi
    w: float
    lam: float
    d_min: int
    columnes_primer: tuple[str, ...]
    columnes_canvis: tuple[str, ...]
    columnes_segon: tuple[str, ...]


def clau_del_codi() -> str:
    """El codi que fa servir el model: els senyals, els models, el decodificador i les versions de les
    biblioteques."""
    h = hashlib.sha256()
    for modul in (senyals, control, tocs, contacte, context, aturades, xarxa, xarxes, model, decodifica_canvis,
                  decodifica_tocs, decodificacio):
        h.update(Path(modul.__file__).read_bytes())
    h.update(repr((lgb.__version__, np.__version__, pd.__version__)).encode())
    return h.hexdigest()


def _de_la_xarxa(xr: xarxa.Xarxa) -> bytes:
    h = hashlib.sha256()
    for a in (xr.mitjana, xr.escala, *xr.pesos, *xr.biaixos):
        a = np.ascontiguousarray(a)
        h.update(repr((a.dtype.str, a.shape)).encode())
        h.update(a.tobytes())
    return h.digest()


def empremta(textos: tuple[str, ...], xs: tuple[xarxa.Xarxa, ...], fitxa: dict) -> str:
    """Els classificadors, les xarxes (els valors, no els fitxers) i la fitxa (sense l'empremta mateixa): si se'n toca
    res, no quadra."""
    h = hashlib.sha256()
    for text in textos:
        h.update(hashlib.sha256(text.encode("utf-8")).digest())
    for xr in xs:
        h.update(_de_la_xarxa(xr))
    sense = {clau: valor for clau, valor in fitxa.items() if clau != "sha256"}
    h.update(json.dumps(sense, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    return h.hexdigest()


def completa(textos: tuple[str, ...], xs: tuple[xarxa.Xarxa, ...], fitxa: dict) -> dict:
    """La fitxa que es desa: la clau del codi d'ara i l'empremta."""
    fitxa = {**fitxa, "clau_del_codi": clau_del_codi()}
    return {**fitxa, "sha256": empremta(textos, xs, fitxa)}


def desa(carpeta: Path, textos: tuple[str, ...], xs: tuple[xarxa.Xarxa, ...], fitxa: dict) -> dict:
    """Els classificadors en text, les xarxes en matrius i la fitxa completa. Cada fitxer, primer a un temporal al
    costat."""
    if len(textos) != len(CLASSIFICADORS) or len(xs) != len(XARXES):
        raise ValueError(f"Calen {len(CLASSIFICADORS)} classificadors i {len(XARXES)} xarxes")
    carpeta.mkdir(parents=True, exist_ok=True)
    fitxa = completa(textos, xs, fitxa)
    for nom, xr in zip(XARXES, xs):
        temporal = carpeta / f"{Path(nom).stem}.part.npz"           # np.savez hi vol el .npz
        xarxa.desa(xr, temporal)
        temporal.replace(carpeta / nom)
    for nom, contingut in (*zip(CLASSIFICADORS, textos),
                           ("fitxa.json", json.dumps(fitxa, indent=1, ensure_ascii=False) + "\n")):
        temporal = carpeta / f"{nom}.part"
        temporal.write_text(contingut, encoding="utf-8")
        temporal.replace(carpeta / nom)
    return fitxa


REFES = "torna'l a fer amb python -I -m banc.model_final"


def carrega(carpeta: Path | None = None) -> Entrenat:
    """El model desat (per defecte, `DIR_MODEL`), només si quadra amb la seva fitxa i amb el codi d'ara."""
    carpeta = DIR_MODEL if carpeta is None else carpeta
    try:
        textos = tuple((carpeta / nom).read_text(encoding="utf-8") for nom in CLASSIFICADORS)
        xs = tuple(xarxa.carrega(carpeta / nom) for nom in XARXES)
        fitxa = json.loads((carpeta / "fitxa.json").read_text(encoding="utf-8"))
    except Exception:           # un fitxer que falta o que no es pot llegir, sigui com sigui, vol dir que no hi ha model
        raise ErrorDelModel("No trobo el model A (cadena/model-a/): fes-lo amb python -I -m banc.model_final") from None
    try:
        quadra = isinstance(fitxa, dict) and fitxa.get("sha256") == empremta(textos, xs, fitxa)
    except (TypeError, ValueError, RecursionError):         # una fitxa o unes xarxes que no es poden resumir
        quadra = False
    if not quadra:
        raise ErrorDelModel(f"El model A no és el que diu la seva fitxa: {REFES}")
    if fitxa.get("clau_del_codi") != clau_del_codi():
        raise ErrorDelModel(f"El model A és d'un altre codi (els senyals, els models o el decodificador): {REFES}")
    try:
        entrenat = Entrenat(
            primer=lgb.Booster(model_str=textos[0]), segon=lgb.Booster(model_str=textos[1]),
            canvis=lgb.Booster(model_str=textos[2]), xarxes=xs, prior=np.array([_nombre(v) for v in fitxa["prior"]]),
            q_prior=_nombre(fitxa["q_prior"]), w=_nombre(fitxa["w"]), lam=_nombre(fitxa["lam"]),
            d_min=_enter(fitxa["d_min"]), columnes_primer=tuple(fitxa["columnes_primer"]),
            columnes_canvis=tuple(fitxa["columnes_canvis"]), columnes_segon=tuple(fitxa["columnes_segon"]))
        bo = _es_bo(entrenat)
    except (KeyError, TypeError, ValueError, OverflowError, LightGBMError):
        bo = False
    if not bo:
        raise ErrorDelModel(f"La fitxa o les xarxes del model A no són com han de ser: {REFES}")
    entrenat.prior.setflags(write=False)
    return entrenat


def _nombre(v: object) -> float:
    """Un nombre de la fitxa: ni un text ni un booleà, encara que Python els sàpiga convertir."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise TypeError("No és un nombre")
    return float(v)


def _enter(v: object) -> int:
    if type(v) is not int:
        raise TypeError("No és un enter")
    return v


def _es_bo(e: Entrenat) -> bool:
    """El prior, la q, el decodificador, els senyals de cada classificador i la forma de les xarxes."""
    return (e.prior.shape == (len(model.CLASSES),) and np.isfinite(e.prior).all() and (e.prior > 0).all()
            and abs(e.prior.sum() - 1) < 1e-6 and 0 < e.q_prior < 1
            and all(math.isfinite(v) and v >= 0 for v in (e.w, e.lam)) and e.d_min >= 1
            and tuple(e.primer.feature_name()) == e.columnes_primer
            and tuple(e.canvis.feature_name()) == e.columnes_canvis
            and tuple(e.segon.feature_name()) == e.columnes_segon
            and e.primer.num_model_per_iteration() == e.segon.num_model_per_iteration() == len(model.CLASSES)
            and e.canvis.num_model_per_iteration() == 1
            and len(e.xarxes) == xarxes.N and all(_xarxa_bona(xr) for xr in e.xarxes))


def _xarxa_bona(xr: xarxa.Xarxa) -> bool:
    """Les capes de `xarxa.OCULTES`, de les 725 entrades a les tres classes, amb valors finits i l'escala positiva."""
    entrades = len(xarxa.DESPLACAMENTS) * xarxa.CANALS
    totes = (xr.mitjana, xr.escala, *xr.pesos, *xr.biaixos)
    if not all(np.issubdtype(a.dtype, np.floating) and np.isfinite(a).all() for a in totes):
        return False
    if xr.mitjana.shape != (entrades,) or xr.escala.shape != (entrades,) or not (xr.escala > 0).all():
        return False
    mides = (entrades, *xarxa.OCULTES, len(model.CLASSES))
    return (len(xr.pesos) == len(xr.biaixos) == len(mides) - 1
            and all(w.shape == (a, b) and bi.shape == (b,)
                    for w, bi, a, b in zip(xr.pesos, xr.biaixos, mides[:-1], mides[1:])))


def sense_tracking(t: Tracking) -> np.ndarray:
    """Les imatges sense pilota i sense cap jugador de cap equip."""
    return (np.isnan(t.pilota[:, 0]) & np.isnan(t.casa[..., 0]).all(axis=1)
            & np.isnan(t.fora[..., 0]).all(axis=1))


def amb_tracking(buides: np.ndarray,
                 trams: tuple[tuple[int, int, int], ...]) -> tuple[tuple[int, int, int] | None, ...]:
    """Per a cada part, de la primera imatge amb tracking a l'última; None si no n'hi ha cap."""
    interiors = []
    for part, inici, fi in trams:
        amb = inici + np.flatnonzero(~buides[inici:fi + 1])
        interiors.append((part, int(amb[0]), int(amb[-1])) if len(amb) else None)
    return tuple(interiors)


def codis(t: Tracking, trams: tuple[tuple[int, int, int], ...], n: int, entrenat: Entrenat) -> np.ndarray:
    """Un codi de la mètrica per imatge del vídeo (0 a n − 1): H, A o D dins de les parts, i X fora."""
    t = senyals.a_reixa(t, n)
    proba, q = probabilitats(t, trams, entrenat)
    return de_les_probabilitats(t, proba, q, trams, entrenat)


def probabilitats(t: Tracking, trams: tuple[tuple[int, int, int], ...],
                  entrenat: Entrenat) -> tuple[np.ndarray, np.ndarray]:
    """(n, 3) i (n,), amb `t` ja a la reixa: les probabilitats del segon classificador i la q, amb el prior a les
    imatges sense tracking."""
    buides = sense_tracking(t)
    taula = _seus(senyals_del_primer(t, trams), entrenat.columnes_primer)
    primer = model.probabilitats(entrenat.primer, taula)
    primer[buides] = entrenat.prior
    taula = _seus(amb_el_context(taula, primer, trams), entrenat.columnes_canvis)
    q = q_de(entrenat.canvis, taula)
    q[buides] = entrenat.q_prior
    de_les_xarxes = xarxes.probabilitats(entrenat.xarxes, t, trams)
    de_les_xarxes[buides] = entrenat.prior
    taula = _seus(senyals_del_segon(taula, t, trams, de_les_xarxes), entrenat.columnes_segon)
    proba = model.probabilitats(entrenat.segon, taula)
    proba[buides] = entrenat.prior
    return proba, q


def _seus(taula: pd.DataFrame, columnes: tuple[str, ...]) -> pd.DataFrame:
    if tuple(taula.columns) != columnes:
        raise ErrorDelModel(f"Els senyals no són els del model A: {REFES}")
    return taula


def senyals_del_primer(t: Tracking, trams: tuple[tuple[int, int, int], ...]) -> pd.DataFrame:
    """Els del primer: els d'A, els del control i els del contacte (`model_a_contacte.taula_primer` al banc)."""
    return pd.concat([senyals.calcula(t, trams), control.calcula(t, trams), contacte.calcula(t, trams)], axis=1)


def amb_el_context(taula: pd.DataFrame, primer: np.ndarray, trams: tuple[tuple[int, int, int], ...]) -> pd.DataFrame:
    """Els del classificador de canvis: els del primer i el context de les seves probabilitats
    (`model_a_contacte.taula_segon`)."""
    return pd.concat([taula, context.calcula(primer, trams)], axis=1)


def senyals_del_segon(amb_context: pd.DataFrame, t: Tracking, trams: tuple[tuple[int, int, int], ...],
                      de_les_xarxes: np.ndarray) -> pd.DataFrame:
    """Els del segon: els del classificador de canvis, els de l'aturada i els de les xarxes
    (`model_a_xarxa.taula_segon`)."""
    return pd.concat([amb_context, aturades.calcula(t, trams), xarxa.senyals_segon(de_les_xarxes, trams)], axis=1)


def q_de(canvis: lgb.Booster, taula: pd.DataFrame) -> np.ndarray:
    """La q: la mitjana de la vista original i de la girada (un canvi ho és igual amb els equips girats)."""
    return (canvis.predict(taula) + canvis.predict(senyals.intercanvia(taula))) / 2


def de_les_probabilitats(t: Tracking, proba: np.ndarray, q: np.ndarray, trams: tuple[tuple[int, int, int], ...],
                         entrenat: Entrenat) -> np.ndarray:
    """Els codis: el decodificador dins de cada part, D a les vores sense tracking i X fora de les parts."""
    buides = sense_tracking(t)
    interiors = amb_tracking(buides, trams)
    out = decodifica_canvis.per_trams(log_relativa(proba, entrenat.prior), q,
                                      tuple(i for i in interiors if i is not None), entrenat.w, entrenat.lam,
                                      entrenat.d_min)
    for (_, inici, fi), interior in zip(trams, interiors):
        if interior is not None:
            out[inici:interior[1]] = pm.D
            out[interior[2] + 1:fi + 1] = pm.D
    return out


def lletres(codis_: np.ndarray) -> np.ndarray:
    return LLETRES[codis_]
