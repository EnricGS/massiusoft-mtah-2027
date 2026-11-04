"""A girat amb fases dins de la cadena: del tracking i del Smart Tagging a un codi per imatge del vídeo (T3am, D-75; a
la cadena, la C2 del pla «A girat amb fases, a la cadena», D-76).

Són les set peces del banc (`banc.model_fases`, amb el model de `banc.model_final_girat`), en aquest ordre:

1. **La pilota creïble** (`pilota_creible.py`): l'ATD, en una fila per imatge (`senyals.a_reixa`), i la pilota vista a
   10 m o més fora del camp, treta (`prepara`).
2. **Les cinc xarxes del camp girat** (`xarxa_girada.py`): les quatre vistes de cada xarxa, de mitjana.
3. **El primer classificador, el de canvis (la q) i el segon** (`probabilitats`): els dos primers, els d'A xarxes; el
   segon, nou, amb les xarxes del camp girat.
4. **La D impossible** a les imatges netejades (`amb_la_d_impossible`).
5. **Les pilotes aturades del Smart Tagging**, sumades a la D (`pilota_morta.amb_les_etiquetes`).
6. **Les fases amb equip del Smart Tagging**, restades a l'altre equip i a la D (`fases.resta`); i la D impossible un
   altre cop, com al banc (`relativa`).
7. **El decodificador amb el cost après dels canvis** (`decodifica_canvis.py`), amb la w, la λ i la durada mínima del
   model, i X fora de les parts (`decodifica`).

Les imatges sense tracking (ni pilota ni cap jugador) es tracten com a A xarxes (`opcio_a.py`): enmig d'una part, el
prior a les probabilitats i a la q; a les vores d'una part, la D, fora del decodificador; una part sencera sense ningú,
X.

**L'equip de les fases** (`equip_quadra`): abans de fer-les servir, es mira que l'equip que hi diu el Smart Tagging
sigui el que dona el model sense el Smart Tagging (A camp girat amb el mateix decodificador) a més de la meitat de les
imatges de dins de les fases. Només hi compten les imatges de dins de les parts on el model dona un equip, i no les
que toquen dues fases d'equips diferents. Si no quadra, o si no hi ha cap fase, `ErrorDeLesFases` amb un text fix: la
cadena s'atura, perquè un Smart Tagging amb els equips girats restaria a l'equip bo.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np
import pandas as pd

from cadena import decodifica_canvis, model, model_girat, senyals
from cadena import fases as fs
from cadena import pilota_creible as pc
from cadena import pilota_morta as pmo
from cadena import smart_tagging as st
from cadena import smart_tagging_fases as stf
from cadena import xarxa_girada as xg
from cadena.llegeix import Tracking
from cadena.opcio_a import amb_el_context, amb_tracking, lletres, q_de, sense_tracking, senyals_del_primer, \
    senyals_del_segon
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

__all__ = ["ErrorDeLesFases", "IMPOSSIBLE", "amb_la_d_impossible", "codis", "decodifica", "equip_quadra", "lletres",
           "prepara", "probabilitats", "relativa", "sense_tracking"]

IMPOSSIBLE = 1e4            # per imatge: més que els canvis i la durada mínima de qualsevol camí sense la D (com al banc)
Trams = tuple[tuple[int, int, int], ...]

SENSE_FASES = "El Smart Tagging no té cap fase amb equip: el model d'A girat amb fases les necessita"
GIRAT = ("L'equip de les fases no és el que dona el model sense el Smart Tagging: el Smart Tagging pot tenir els "
         "equips girats")


class ErrorDeLesFases(Exception):
    """Les fases del Smart Tagging no es poden fer servir. El missatge és un text fix, sense cap dada."""


def prepara(t: Tracking, n: int) -> tuple[Tracking, np.ndarray]:
    """L'ATD a la reixa del vídeo amb la pilota creïble, i les imatges on la neteja l'ha treta."""
    t = senyals.a_reixa(t, n)
    return pc.neteja(t), pc.lluny(t)


def probabilitats(t: Tracking, trams: Trams, e: model_girat.Entrenat) -> tuple[np.ndarray, np.ndarray]:
    """(n, 3) i (n,), amb `t` ja preparat: les probabilitats del segon classificador i la q, amb el prior a les
    imatges sense tracking."""
    buides = sense_tracking(t)
    taula = _seus(senyals_del_primer(t, trams), e.columnes_primer)
    primer = model.probabilitats(e.primer, taula)
    primer[buides] = e.prior
    taula = _seus(amb_el_context(taula, primer, trams), e.columnes_canvis)
    q = q_de(e.canvis, taula)
    q[buides] = e.q_prior
    de_les_xarxes = xg.probabilitats(e.xarxes, t, trams)
    de_les_xarxes[buides] = e.prior
    taula = _seus(senyals_del_segon(taula, t, trams, de_les_xarxes), e.columnes_segon)
    proba = model.probabilitats(e.segon, taula)
    proba[buides] = e.prior
    return proba, q


def _seus(taula: pd.DataFrame, columnes: tuple[str, ...]) -> pd.DataFrame:
    if tuple(taula.columns) != columnes:
        raise model_girat.ErrorDelModel(f"Els senyals no són els del model d'A girat amb fases: {model_girat.REFES}")
    return taula


def amb_la_d_impossible(relativa_: np.ndarray, on: np.ndarray) -> np.ndarray:
    """La probabilitat relativa amb la D impossible a les imatges d'`on`; la resta, com estava (una còpia)."""
    out = relativa_.copy()
    out[on, pm.D] = -IMPOSSIBLE
    return out


def relativa(proba: np.ndarray, netejades: np.ndarray, etiquetes: tuple[st.Etiqueta, ...],
             fases: tuple[fs.Fase, ...], trams: Trams, e: model_girat.Entrenat) -> np.ndarray:
    """log(p / prior) amb les pilotes aturades, la D impossible, les fases i la D impossible un altre cop."""
    amb_pm = amb_la_d_impossible(pmo.amb_les_etiquetes(log_relativa(proba, e.prior), etiquetes, trams,
                                                       e.pilota_morta, dict(e.medianes)), netejades)
    return amb_la_d_impossible(fs.resta(amb_pm, fases, trams, e.fases.gamma, e.fases.delta, e.fases.marge_s),
                               netejades)


def decodifica(t: Tracking, relativa_: np.ndarray, q: np.ndarray, trams: Trams,
               e: model_girat.Entrenat) -> np.ndarray:
    """Els codis: el decodificador dins de cada part, D a les vores sense tracking i X fora de les parts."""
    interiors = amb_tracking(sense_tracking(t), trams)
    out = decodifica_canvis.per_trams(relativa_, q, tuple(i for i in interiors if i is not None), e.w, e.lam,
                                      e.d_min)
    for (_, inici, fi), interior in zip(trams, interiors):
        if interior is not None:
            out[inici:interior[1]] = pm.D
            out[interior[2] + 1:fi + 1] = pm.D
    return out


def equip_quadra(sense: np.ndarray, fases: tuple[fs.Fase, ...], trams: Trams) -> bool:
    """Si a més de la meitat de les imatges de dins de les fases el model sense el Smart Tagging (`sense`) dona l'equip
    de la fase. Hi compten les imatges de dins de les parts on dona H o A, i que no toquen dues fases d'equips
    diferents. Sense cap imatge per mirar, no quadra."""
    n = len(sense)
    de = np.zeros((n, 2), dtype=bool)                 # de l'H i de l'A
    for f in fases:
        de[max(f.inici, 0):min(f.final, n - 1) + 1, f.equip] = True
    dins = np.zeros(n, dtype=bool)
    for _, inici, fi in trams:
        dins[inici:fi + 1] = True
    compten = dins & (de[:, pm.H] != de[:, pm.A]) & np.isin(sense, (pm.H, pm.A))
    if not compten.any():
        return False
    equip = np.where(de[:, pm.H], pm.H, pm.A)
    return 2 * int((sense[compten] == equip[compten]).sum()) > int(compten.sum())


class Resultat(NamedTuple):
    t: Tracking               # a la reixa del vídeo, amb la pilota creïble: el que ha mirat el model
    proba: np.ndarray         # (n, 3): les probabilitats del segon classificador
    codis: np.ndarray         # (n,): un codi de la mètrica per imatge


def resultat(t: Tracking, trams: Trams, n: int, e: model_girat.Entrenat, llegit: stf.Llegit) -> Resultat:
    """Els codis, i també les probabilitats i l'ATD preparat (per a la revisió interna). S'atura
    (`ErrorDeLesFases`) si no hi ha cap fase o si el seu equip no quadra amb el model sense el Smart Tagging."""
    if not llegit.fases:
        raise ErrorDeLesFases(SENSE_FASES)
    t, netejades = prepara(t, n)
    proba, q = probabilitats(t, trams, e)
    sense = decodifica(t, relativa(proba, netejades, (), (), trams, e), q, trams, e)
    if not equip_quadra(sense, llegit.fases, trams):
        raise ErrorDeLesFases(GIRAT)
    return Resultat(t, proba, decodifica(t, relativa(proba, netejades, llegit.etiquetes, llegit.fases, trams, e),
                                         q, trams, e))


def codis(t: Tracking, trams: Trams, n: int, e: model_girat.Entrenat, llegit: stf.Llegit) -> np.ndarray:
    """Un codi de la mètrica per imatge del vídeo (0 a n − 1): H, A o D dins de les parts, i X fora (vegeu
    `resultat`)."""
    return resultat(t, trams, n, e, llegit).codis
