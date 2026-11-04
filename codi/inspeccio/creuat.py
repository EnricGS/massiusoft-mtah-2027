"""L'ATD i el Smart Tagging junts: els forats de la pilota cauen a prop de pilota aturada?

Si els forats llargs són a tocar d'una jugada a pilota aturada, molts són pilota
morta (D) i el tracking sol ja els pot resoldre. Si són enmig del joc, cal el vídeo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from inspeccio.atd import grup_de_durada
from inspeccio.carrega import Tracking
from inspeccio.esperat import Esperat
from inspeccio.etiquetatge import amb_temps, frame
from inspeccio.seccio import Seccio, pct, xifra

ABANS_DE_SORTIDA_S = 15.0     # la pilota sol ser fora una estona abans de tornar-la a posar en joc


def dins_de(frames: np.ndarray, trams: list[tuple[int, int]]) -> np.ndarray:
    dins = np.zeros(len(frames), bool)
    for inici, fi in trams:
        dins |= (frames >= inici) & (frames <= fi)
    return dins


def omple(seccio: Seccio, t: Tracking, forats: pd.DataFrame, etiquetes: pd.DataFrame,
          esperat: Esperat) -> None:
    etiquetes = amb_temps(etiquetes)
    aturada = etiquetes[etiquetes["codi"].str.upper() == "SET PIECES"]
    a_prop = [(frame(i - ABANS_DE_SORTIDA_S, esperat), frame(f, esperat))
              for i, f in zip(aturada["inici_s"], aturada["fi_s"])]
    qualsevol = [(frame(i, esperat), frame(f, esperat)) for i, f in zip(etiquetes["inici_s"], etiquetes["fi_s"])]
    mig = t.frame_video[np.clip(((forats["inici"] + forats["fi"]) // 2).to_numpy(), 0, t.n - 1)]
    taula = forats.assign(grup=grup_de_durada(forats["durada_s"].to_numpy()),
                          aturada=dins_de(mig, a_prop), etiquetada=dins_de(mig, qualsevol))
    files = []
    for nom, g in taula.groupby("grup", observed=False):
        pes = g["fotogrames"].sum()
        files.append((nom, xifra(len(g)),
                      f"{xifra(pct(g.loc[g['aturada'], 'fotogrames'].sum(), pes))} %",
                      f"{xifra(pct(g.loc[g['etiquetada'], 'fotogrames'].sum(), pes))} %",
                      f"{xifra(pct(g.loc[~g['etiquetada'], 'fotogrames'].sum(), pes))} %"))
    seccio.text(f"Per a cada forat de la pilota als fotogrames puntuats, on cau el seu fotograma del mig: "
                f"a prop d'un `SET PIECES` (des de {xifra(ABANS_DE_SORTIDA_S)} s abans que comenci fins que "
                "acaba), dins de qualsevol instància, o fora de totes. Els percentatges són de fotogrames sense pilota.")
    seccio.taula("Forats de la pilota i Smart Tagging", (
        "Durada del forat", "Forats", "A prop d'un SET PIECES", "Dins d'alguna instància", "Fora de tota instància"),
        files, "El Smart Tagging és automàtic: és un indici, no la veritat (DATA.md).")
