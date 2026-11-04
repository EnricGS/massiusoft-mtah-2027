"""Un partit de DFL (IDSSE, Bassek et al. 2025, CC BY 4.0) al format del banc, amb kloppy.

La veritat és la mateixa mena que la del concurs (CHALLENGE.md): D on el tracking diu que la pilota és morta
(`ball_state`), i si no, l'equip que el tracking diu que la té (`ball_owning_team_id`). H és l'equip de casa.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from banc.partit import PartitBanc, trams_de_parts
from cadena.llegeix import Tracking
from possessio.oficial import possession_metrics as pm


def fitxer(carpeta: Path, patro: str) -> Path:
    trobats = sorted(carpeta.glob(patro))
    if len(trobats) != 1:
        raise FileNotFoundError(f"Cal un sol fitxer {patro} a {carpeta}, i n'hi ha {len(trobats)}")
    return trobats[0]


def posicions(df, equip) -> np.ndarray:
    ids = [str(p.player_id) for p in equip.players if f"{p.player_id}_x" in df]
    return np.stack([df[[f"{i}_x" for i in ids]].astype(float).to_numpy(),
                     df[[f"{i}_y" for i in ids]].astype(float).to_numpy()], axis=-1)


def veritat(estat: np.ndarray, propietari: np.ndarray, id_casa: str, id_fora: str) -> np.ndarray:
    """D si és morta; si és viva, l'equip que la té; X si és viva i no en diu l'equip."""
    equip = np.where(propietari == id_casa, pm.H, np.where(propietari == id_fora, pm.A, pm.X))
    return np.where(estat == "dead", pm.D, equip).astype(np.int8)


def llegeix(carpeta: Path, partit: str, limit: int | None = None) -> PartitBanc:
    from kloppy import sportec

    meta = fitxer(carpeta, f"DFL_02_01_matchinformation_*{partit}.xml")
    pos = fitxer(carpeta, f"DFL_04_03_positions_raw_observed_*{partit}.xml")
    ds = sportec.load_tracking(raw_data=str(pos), meta_data=str(meta), limit=limit)
    df = ds.to_df()
    casa = next(e for e in ds.metadata.teams if str(getattr(e.ground, "value", e.ground)) == "home")
    fora = next(e for e in ds.metadata.teams if e is not casa)
    periode = df["period_id"].to_numpy(int)
    for _, a, b in trams_de_parts(periode):
        if np.any(np.diff(df["frame_id"].to_numpy(int)[a:b + 1]) != 1):
            raise ValueError(f"{partit}: falten imatges dins d'una part")
    estat = df["ball_state"].astype(str).to_numpy()
    if not set(np.unique(estat).tolist()) <= {"alive", "dead"}:
        raise ValueError(f"{partit}: estats de la pilota desconeguts")
    camp = ds.metadata.pitch_dimensions
    n = len(df)
    tracking = Tracking(
        fotograma=np.arange(n), pilota=df[["ball_x", "ball_y"]].astype(float).to_numpy(),
        casa=posicions(df, casa), fora=posicions(df, fora), nom_casa=str(casa.name), nom_fora=str(fora.name),
        casa_es_home=True, camp_m=(float(camp.pitch_length), float(camp.pitch_width)))
    return PartitBanc(
        nom=f"dfl-{partit}", font="dfl", tracking=tracking, trams=trams_de_parts(periode),
        veritat=veritat(estat, df["ball_owning_team_id"].astype(str).to_numpy(), str(casa.team_id),
                        str(fora.team_id)),
        pilota_z=df["ball_z"].astype(float).to_numpy())
