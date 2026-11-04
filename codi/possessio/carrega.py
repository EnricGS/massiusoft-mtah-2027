"""Lectura dels tres partits de mostra de Metrica a una estructura comuna.

Les dades es tracten com a no fiables: només es llegeixen com a text/números
(csv, json, kloppy per a l'EPTS) i mai s'executa res del seu contingut.

Representació comuna (`Partit`):
- coordenades en metres, x en [0, 105], y en [0, 68], origen a dalt a l'esquerra
  (la mateixa convenció que Metrica, escalada);
- `home`/`away`: arrays (n_frames, n_jugadors, 2) amb NaN quan el jugador no és al camp;
- `pilota`: (n_frames, 2) amb els NaN originals (sense interpolar);
- `events`: DataFrame amb columnes normalitzades (vegeu `COLUMNES_EVENTS`).
"""

from __future__ import annotations

import csv
import json
import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from possessio import config

COLUMNES_EVENTS = [
    "team", "type", "subtype", "period", "start_frame", "end_frame",
    "from_player", "to_player", "start_x", "start_y", "end_x", "end_y",
]


@dataclass(frozen=True)
class Partit:
    nom: str
    frame: np.ndarray        # (n,) identificador de frame de Metrica
    periode: np.ndarray      # (n,)
    temps: np.ndarray        # (n,) segons
    home: np.ndarray         # (n, nh, 2) metres
    away: np.ndarray         # (n, na, 2) metres
    pilota: np.ndarray       # (n, 2) metres, NaN si no hi ha pilota
    ids_home: tuple[str, ...]
    ids_away: tuple[str, ...]
    events: pd.DataFrame

    @property
    def n(self) -> int:
        return len(self.frame)

    def index_de_frame(self, frames: np.ndarray) -> np.ndarray:
        """Converteix identificadors de frame de Metrica a índexs de fila."""
        idx = np.searchsorted(self.frame, frames)
        return np.clip(idx, 0, self.n - 1)


# --- Partits 1 i 2: CSV de Metrica ------------------------------------------

def _llegeix_tracking_csv(cami: Path) -> tuple[pd.DataFrame, list[str]]:
    with cami.open(newline="") as f:
        lector = csv.reader(f)
        next(lector)
        next(lector)
        capcalera = next(lector)
    jugadors = [c for c in capcalera[3:] if c and c != "Ball"]
    noms = ["periode", "frame", "temps"]
    for j in jugadors:
        noms += [f"{j}_x", f"{j}_y"]
    noms += ["ball_x", "ball_y"]
    df = pd.read_csv(cami, skiprows=3, header=None, names=noms, na_values=["NaN"])
    return df, jugadors


def _a_metres(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.stack([x * config.LLARG_CAMP_M, y * config.AMPLE_CAMP_M], axis=-1)


def _matriu_jugadors(df: pd.DataFrame, jugadors: list[str]) -> np.ndarray:
    xs = df[[f"{j}_x" for j in jugadors]].to_numpy(dtype=float)
    ys = df[[f"{j}_y" for j in jugadors]].to_numpy(dtype=float)
    return _a_metres(xs, ys)


def _llegeix_events_csv(cami: Path) -> pd.DataFrame:
    df = pd.read_csv(cami)
    ev = pd.DataFrame({
        "team": df["Team"].astype(str),
        "type": df["Type"].astype(str),
        "subtype": df["Subtype"].fillna("").astype(str),
        "period": df["Period"].astype(int),
        "start_frame": df["Start Frame"].astype(int),
        "end_frame": df["End Frame"].astype(int),
        "from_player": df["From"].fillna("").astype(str),
        "to_player": df["To"].fillna("").astype(str),
        "start_x": df["Start X"] * config.LLARG_CAMP_M,
        "start_y": df["Start Y"] * config.AMPLE_CAMP_M,
        "end_x": df["End X"] * config.LLARG_CAMP_M,
        "end_y": df["End Y"] * config.AMPLE_CAMP_M,
    })
    return ev[COLUMNES_EVENTS]


def _carrega_csv(num: int) -> Partit:
    base = config.DIR_DADES / f"Sample_Game_{num}"
    dh, jh = _llegeix_tracking_csv(base / f"Sample_Game_{num}_RawTrackingData_Home_Team.csv")
    da, ja = _llegeix_tracking_csv(base / f"Sample_Game_{num}_RawTrackingData_Away_Team.csv")
    if not np.array_equal(dh["frame"].to_numpy(), da["frame"].to_numpy()):
        raise ValueError(f"Partit {num}: els frames de Home i Away no coincideixen")
    pilota = _a_metres(dh["ball_x"].to_numpy(float), dh["ball_y"].to_numpy(float))
    return Partit(
        nom=f"Partit {num}",
        frame=dh["frame"].to_numpy(int),
        periode=dh["periode"].to_numpy(int),
        temps=dh["temps"].to_numpy(float),
        home=_matriu_jugadors(dh, jh),
        away=_matriu_jugadors(da, ja),
        pilota=pilota,
        ids_home=tuple(jh),
        ids_away=tuple(ja),
        events=_llegeix_events_csv(base / f"Sample_Game_{num}_RawEventsData.csv"),
    )


# --- Partit 3: EPTS FIFA (kloppy) + JSON d'esdeveniments ----------------------

def _nom_subtipus(sub: object) -> str:
    if sub is None:
        return ""
    elements = sub if isinstance(sub, list) else [sub]
    return "-".join(str(s.get("name", "")) for s in elements if isinstance(s, dict))


def _llegeix_events_json(cami: Path, equip_a_banda: dict[str, str]) -> pd.DataFrame:
    with cami.open() as f:
        dades = json.load(f)["data"]
    files = []
    for e in dades:
        inici, fi = e.get("start") or {}, e.get("end") or {}
        equip = (e.get("team") or {}).get("id", "")
        files.append({
            "team": equip_a_banda.get(equip, "Desconegut"),
            "type": (e.get("type") or {}).get("name", ""),
            "subtype": _nom_subtipus(e.get("subtypes")),
            "period": int(e.get("period") or 0),
            "start_frame": int(inici.get("frame") or 0),
            "end_frame": int(fi.get("frame") or 0),
            "from_player": ((e.get("from") or {}).get("name") or ""),
            "to_player": ((e.get("to") or {}).get("name") or ""),
            "start_x": _escala(inici.get("x"), config.LLARG_CAMP_M),
            "start_y": _escala(inici.get("y"), config.AMPLE_CAMP_M),
            "end_x": _escala(fi.get("x"), config.LLARG_CAMP_M),
            "end_y": _escala(fi.get("y"), config.AMPLE_CAMP_M),
        })
    return pd.DataFrame(files, columns=COLUMNES_EVENTS)


def _escala(v: object, factor: float) -> float:
    return float(v) * factor if isinstance(v, (int, float)) else np.nan


def _carrega_epts() -> Partit:
    from kloppy import metrica

    base = config.DIR_DADES / "Sample_Game_3"
    ds = metrica.load_tracking_epts(
        meta_data=str(base / "Sample_Game_3_metadata.xml"),
        raw_data=str(base / "Sample_Game_3_tracking.txt"),
        coordinates="metrica",
    )
    home_team, away_team = ds.metadata.teams
    df = ds.to_df()

    def matriu(equip) -> tuple[np.ndarray, list[str]]:
        ids = [p.player_id for p in equip.players if f"{p.player_id}_x" in df.columns]
        xs = df[[f"{i}_x" for i in ids]].to_numpy(dtype=float)
        ys = df[[f"{i}_y" for i in ids]].to_numpy(dtype=float)
        return _a_metres(xs, ys), [p.name for p in equip.players if p.player_id in ids]

    home, nh = matriu(home_team)
    away, na = matriu(away_team)
    pilota = _a_metres(df["ball_x"].to_numpy(float), df["ball_y"].to_numpy(float))
    temps = df["timestamp"].dt.total_seconds().to_numpy(float)
    bandes = {home_team.team_id: "Home", away_team.team_id: "Away"}
    return Partit(
        nom="Partit 3",
        frame=df["frame_id"].to_numpy(int),
        periode=df["period_id"].to_numpy(int),
        temps=temps,
        home=home,
        away=away,
        pilota=pilota,
        ids_home=tuple(nh),
        ids_away=tuple(na),
        events=_llegeix_events_json(base / "Sample_Game_3_events.json", bandes),
    )


# --- API -------------------------------------------------------------------

def carrega_partit(num: int, usa_cache: bool = True) -> Partit:
    """Carrega el partit `num` (1, 2 o 3), amb memòria cau local en pickle."""
    cache = config.DIR_CACHE / f"partit_{num}.pkl"
    if usa_cache and cache.exists():
        with cache.open("rb") as f:
            return pickle.load(f)
    partit = _carrega_csv(num) if num in (1, 2) else _carrega_epts()
    _valida(partit)
    config.DIR_CACHE.mkdir(parents=True, exist_ok=True)
    with cache.open("wb") as f:
        pickle.dump(partit, f)
    return partit


def _valida(p: Partit) -> None:
    if np.any(np.diff(p.frame) <= 0):
        raise ValueError(f"{p.nom}: frames no estrictament creixents")
    if p.home.shape[0] != p.n or p.away.shape[0] != p.n or p.pilota.shape[0] != p.n:
        raise ValueError(f"{p.nom}: mides inconsistents")
    if not set(p.events["team"]).issubset({"Home", "Away"}):
        raise ValueError(f"{p.nom}: equips d'esdeveniments desconeguts")
