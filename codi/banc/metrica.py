"""Els tres partits de mostra de Metrica al format del banc.

La lectura i les etiquetes són les del prototip (`possessio.carrega`, `possessio.etiquetes`): la veritat surt dels
esdeveniments amb les regles R1-R11 de `possessio/etiquetes.py`, i no d'un tracking corregit com a DFL i al concurs.
"""

from __future__ import annotations

import numpy as np

from banc.partit import PartitBanc, trams_de_parts
from cadena.llegeix import Tracking
from possessio import config
from possessio.carrega import carrega_partit
from possessio.etiquetes import deriva_etiquetes
from possessio.oficial import possession_metrics as pm

assert (config.HOME, config.AWAY, config.ATURAT) == (pm.H, pm.A, pm.D)


def llegeix(num: int) -> PartitBanc:
    p = carrega_partit(num)
    camp = np.array([config.LLARG_CAMP_M, config.AMPLE_CAMP_M])
    y3 = deriva_etiquetes(p.events, p.frame, p.periode).y3
    tracking = Tracking(
        fotograma=np.arange(p.n), pilota=p.pilota / camp, casa=p.home / camp, fora=p.away / camp,
        nom_casa="Home", nom_fora="Away", casa_es_home=True, camp_m=(float(camp[0]), float(camp[1])))
    return PartitBanc(
        nom=f"metrica-{num}", font="metrica", tracking=tracking, trams=trams_de_parts(p.periode),
        veritat=np.where(y3 < 0, pm.X, y3).astype(np.int8), pilota_z=np.full(p.n, np.nan))
