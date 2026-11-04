"""Un partit sintètic petit per als tests del banc: jugadors que es mouen, una pilota que va d'un a l'altre i
una veritat que la segueix."""

from __future__ import annotations

import numpy as np

from banc.partit import PartitBanc
from cadena.llegeix import Tracking
from possessio.oficial import possession_metrics as pm

CAMP = (105.0, 68.0)


def partit(n: int = 12_000, nom: str = "sintetic", llavor: int = 7, amb_z: bool = True) -> PartitBanc:
    rng = np.random.default_rng(llavor)
    passos = rng.normal(0, 0.15, (n, 22, 2)).cumsum(axis=0)
    inici = rng.uniform([10, 10], [95, 58], (22, 2))
    jugadors = np.clip(inici + passos, [0, 0], CAMP)
    # la pilota és a tocar d'un jugador, que canvia cada 4 s; mitja part de l'estona, de cada equip
    qui = np.repeat(rng.integers(0, 22, n // 100 + 1), 100)[:n]
    pilota = jugadors[np.arange(n), qui] + rng.normal(0, 0.3, (n, 2))
    veritat = np.where(qui < 11, pm.H, pm.A).astype(np.int8)
    veritat[(np.arange(n) // 500) % 5 == 4] = pm.D                     # una aturada de 20 s de cada 100
    escala = np.array(CAMP)
    t = Tracking(fotograma=np.arange(n), pilota=pilota / escala, casa=jugadors[:, :11] / escala,
                 fora=jugadors[:, 11:] / escala, nom_casa="Casa", nom_fora="Fora", casa_es_home=True, camp_m=CAMP)
    # la pilota és a l'aire a estones d'un segon, una de cada deu
    z = np.repeat(np.where(rng.random(n // 25 + 1) < 0.1, 4.0, 0.2), 25)[:n] if amb_z else np.full(n, np.nan)
    meitat = n // 2
    return PartitBanc(nom=nom, font="dfl", tracking=t, trams=((1, 0, meitat - 1), (2, meitat, n - 1)),
                      veritat=veritat, pilota_z=z)
