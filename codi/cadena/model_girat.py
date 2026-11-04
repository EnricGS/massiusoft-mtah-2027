"""El model d'A girat amb fases, desat (C1 del pla «A girat amb fases, a la cadena», `docs/pla-tocs.md`; D-76).

Les peces, entrenades només amb les dades obertes del banc (`python -I -m banc.model_final_girat`), a `model-girat/`:
- **el primer classificador i el de canvis** (la q), els d'A xarxes (`opcio_a.py`);
- **les cinc xarxes del camp girat** (T3ad, `xarxa_girada.py`), que veuen una pilota estimada on no es veu
  (`xarxa_sense_pilota.py`) i els dos equips sencers (`xarxa_equips.py`);
- **el segon classificador,** amb les probabilitats d'aquestes xarxes;
- **la fitxa:** el prior, la q de les imatges sense tracking, el decodificador, la pilota morta d'abans de les represes
  (`pilota_morta.Abans`) amb les medianes per tipus dels deu partits, les fases (`Fases`), d'on surt tot plegat, la
  clau del codi d'ara i una empremta que cobreix els tres classificadors, les cinc xarxes i la fitxa.

Abans de fer-lo servir, com a `opcio_a.py`, se'n comprova l'empremta, que sigui del codi d'ara (`MODULS` i les
versions de les biblioteques) i que les peces siguin com han de ser. Aquí només es desa i es llegeix: el que l'aplica
és la cadena (C2). `opcio_a.py` i `model-a/` no es toquen.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import NamedTuple

import lightgbm as lgb
import numpy as np
import pandas as pd
from lightgbm.basic import LightGBMError

from cadena import (aturades, contacte, context, control, decodifica_canvis, decodifica_tocs, fases, model,
                    pilota_creible, pilota_morta, senyals, tocs, xarxa, xarxa_equips, xarxa_girada,
                    xarxa_sense_pilota, xarxes)
from cadena.smart_tagging import TIPUS
from possessio import decodificacio

DIR_MODEL = Path(__file__).resolve().parent / "model-girat"
CLASSIFICADORS = ("primer.txt", "segon.txt", "canvis.txt")
XARXES = tuple(f"xarxa-{i}.npz" for i in range(xarxes.N))
FITXERS = (*CLASSIFICADORS, *XARXES)              # i la fitxa
MODULS = (senyals, control, tocs, contacte, context, aturades, xarxa, xarxes, xarxa_sense_pilota, xarxa_equips,
          xarxa_girada, pilota_creible, pilota_morta, fases, model, decodifica_canvis, decodifica_tocs, decodificacio)
REFES = "torna'l a fer amb python -I -m banc.model_final_girat"


class ErrorDelModel(Exception):
    """El model desat no és el que toca. El missatge és un text fix, sense cap dada: pot sortir a la consola."""


class Fases(NamedTuple):
    gamma: float            # per imatge, a l'altre equip
    delta: float            # per imatge, a la D
    marge_s: float          # a cada vora de la fase


@dataclass(frozen=True)
class Entrenat:
    primer: lgb.Booster                 # P(H), P(A) i P(D) amb els senyals del primer
    segon: lgb.Booster                  # el mateix, amb el context, l'aturada i les xarxes del camp girat
    canvis: lgb.Booster                 # la q
    xarxes: tuple[xarxa.Xarxa, ...]     # les del camp girat
    prior: np.ndarray                   # H, A i D a les mostres dels dos classificadors
    q_prior: float                      # la part de les mostres del classificador de canvis a prop d'un canvi
    w: float
    lam: float
    d_min: int
    columnes_primer: tuple[str, ...]
    columnes_canvis: tuple[str, ...]
    columnes_segon: tuple[str, ...]
    pilota_morta: pilota_morta.Abans
    medianes: MappingProxyType          # els segons de pilota morta abans de cada tipus de represa
    fases: Fases


def clau_del_codi() -> str:
    """El codi que fa servir el model, i les versions de les biblioteques."""
    h = hashlib.sha256()
    for modul in MODULS:
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
    """Els classificadors, les xarxes (els valors, no els fitxers) i la fitxa (sense l'empremta mateixa)."""
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


def carrega(carpeta: Path | None = None) -> Entrenat:
    """El model desat (per defecte, `DIR_MODEL`), només si quadra amb la seva fitxa i amb el codi d'ara."""
    carpeta = DIR_MODEL if carpeta is None else carpeta
    try:
        textos = tuple((carpeta / nom).read_text(encoding="utf-8") for nom in CLASSIFICADORS)
        xs = tuple(xarxa.carrega(carpeta / nom) for nom in XARXES)
        fitxa = json.loads((carpeta / "fitxa.json").read_text(encoding="utf-8"))
    except Exception:           # un fitxer que falta o que no es pot llegir, sigui com sigui, vol dir que no hi ha model
        raise ErrorDelModel("No trobo el model d'A girat amb fases (cadena/model-girat/): fes-lo amb "
                            "python -I -m banc.model_final_girat") from None
    try:
        quadra = isinstance(fitxa, dict) and fitxa.get("sha256") == empremta(textos, xs, fitxa)
    except (TypeError, ValueError, RecursionError):         # una fitxa o unes xarxes que no es poden resumir
        quadra = False
    if not quadra:
        raise ErrorDelModel(f"El model d'A girat amb fases no és el que diu la seva fitxa: {REFES}")
    if fitxa.get("clau_del_codi") != clau_del_codi():
        raise ErrorDelModel(f"El model d'A girat amb fases és d'un altre codi: {REFES}")
    try:
        entrenat = _de_la_fitxa(textos, xs, fitxa)
        bo = _es_bo(entrenat)
    except (KeyError, TypeError, ValueError, OverflowError, AttributeError, LightGBMError):
        bo = False
    if not bo:
        raise ErrorDelModel(f"La fitxa o les xarxes del model d'A girat amb fases no són com han de ser: {REFES}")
    entrenat.prior.setflags(write=False)
    return entrenat


def _de_la_fitxa(textos: tuple[str, ...], xs: tuple[xarxa.Xarxa, ...], fitxa: dict) -> Entrenat:
    pm_, fs_, medianes = fitxa["pilota_morta"], fitxa["fases"], fitxa["medianes"]
    if set(pm_) != set(pilota_morta.Abans._fields) or set(fs_) != set(Fases._fields) or set(medianes) != set(TIPUS):
        raise KeyError("Hi falten o hi sobren camps")
    if not isinstance(pm_["forma"], str):
        raise TypeError("La forma no és un text")
    return Entrenat(
        primer=lgb.Booster(model_str=textos[0]), segon=lgb.Booster(model_str=textos[1]),
        canvis=lgb.Booster(model_str=textos[2]), xarxes=xs, prior=np.array([_nombre(v) for v in fitxa["prior"]]),
        q_prior=_nombre(fitxa["q_prior"]), w=_nombre(fitxa["w"]), lam=_nombre(fitxa["lam"]),
        d_min=_enter(fitxa["d_min"]), columnes_primer=tuple(fitxa["columnes_primer"]),
        columnes_canvis=tuple(fitxa["columnes_canvis"]), columnes_segon=tuple(fitxa["columnes_segon"]),
        pilota_morta=pilota_morta.Abans(_nombre(pm_["beta_d"]), pm_["forma"], _nombre(pm_["durada"]),
                                        _nombre(pm_["marge_s"])),
        medianes=MappingProxyType({t: _nombre(medianes[t]) for t in TIPUS}),
        fases=Fases(*(_nombre(fs_[k]) for k in Fases._fields)))


def _nombre(v: object) -> float:
    """Un nombre de la fitxa: ni un text ni un booleà, encara que Python els sàpiga convertir."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise TypeError("No és un nombre")
    return float(v)


def _enter(v: object) -> int:
    if type(v) is not int:
        raise TypeError("No és un enter")
    return v


def _positius(*valors: float) -> bool:
    return all(math.isfinite(v) and v >= 0 for v in valors)


def _es_bo(e: Entrenat) -> bool:
    """El prior, la q, el decodificador, la pilota morta, les medianes, les fases, els senyals de cada classificador i
    la forma de les xarxes."""
    a = e.pilota_morta
    return (e.prior.shape == (len(model.CLASSES),) and np.isfinite(e.prior).all() and (e.prior > 0).all()
            and abs(e.prior.sum() - 1) < 1e-6 and 0 < e.q_prior < 1 and _positius(e.w, e.lam) and e.d_min >= 1
            and a.forma in (pilota_morta.FIXA, pilota_morta.PER_TIPUS) and _positius(a.beta_d, a.marge_s)
            and math.isfinite(a.durada) and a.durada > 0 and _positius(*e.medianes.values()) and _positius(*e.fases)
            and tuple(e.primer.feature_name()) == e.columnes_primer
            and tuple(e.canvis.feature_name()) == e.columnes_canvis
            and tuple(e.segon.feature_name()) == e.columnes_segon
            and e.primer.num_model_per_iteration() == e.segon.num_model_per_iteration() == len(model.CLASSES)
            and e.canvis.num_model_per_iteration() == 1
            and len(e.xarxes) == xarxes.N and all(_xarxa_bona(xr) for xr in e.xarxes))


def _xarxa_bona(xr: xarxa.Xarxa) -> bool:
    """Les capes de `xarxa.OCULTES`, de les entrades de `xarxa_equips` a les tres classes, amb valors finits i l'escala
    positiva."""
    entrades = xarxa_equips.ENTRADES
    totes = (xr.mitjana, xr.escala, *xr.pesos, *xr.biaixos)
    if not all(np.issubdtype(a.dtype, np.floating) and np.isfinite(a).all() for a in totes):
        return False
    if xr.mitjana.shape != (entrades,) or xr.escala.shape != (entrades,) or not (xr.escala > 0).all():
        return False
    mides = (entrades, *xarxa.OCULTES, len(model.CLASSES))
    return (len(xr.pesos) == len(xr.biaixos) == len(mides) - 1
            and all(w.shape == (a, b) and bi.shape == (b,)
                    for w, bi, a, b in zip(xr.pesos, xr.biaixos, mides[:-1], mides[1:])))
