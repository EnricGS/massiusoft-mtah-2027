"""Etiquetes de veritat: possessió d'equip per frame derivada dels esdeveniments.

Regles:

R1  Qualsevol esdeveniment "de possessió" (PASS, CARRY, RECOVERY, SET PIECE,
    SHOT, BALL LOST, BALL OUT) assigna la possessió a l'equip que el fa a partir
    del seu frame d'inici. La possessió es manté fins al següent canvi
    (definició de Metrica: el jugador continua en possessió fins que un altre
    en pren el control, la pilota surt o l'àrbitre atura el joc).
R2  BALL LOST no canvia l'equip: durant la passada interceptada la possessió
    continua sent de l'equip que la perd; canvia al RECOVERY/PASS del rival.
R2b Un BALL LOST anotat <= 2 s després d'un esdeveniment de possessió del
    rival és el registre endarrerit d'una pèrdua ja materialitzada (THEFT):
    no retorna la possessió a l'equip que la perd.
R3  CHALLENGE (sense falta) i CARD no canvien res: el resultat del duel el
    defineix l'esdeveniment següent (RECOVERY, PASS...).
R4  Pilota fora: BALL OUT -> "aturat" des del seu frame final; SHOT amb
    resultat OUT o GOAL -> "aturat" des del frame final del xut.
R5  Faltes i aturades arbitrals: FAULT RECEIVED i CHALLENGE amb subtipus FAULT
    -> "aturat" des del seu frame; BALL LOST amb FORCED / HAND BALL /
    END HALF / VOLUNTARY i qualsevol esdeveniment amb OFFSIDE -> "aturat" des
    del frame final. ADVANTAGE no atura.
R6  L'aturada dura fins al següent esdeveniment que pot reprendre el joc
    (SET PIECE, PASS, CARRY, RECOVERY, SHOT). Un BALL LOST o BALL OUT anotat
    durant l'aturada (p. ex. la pèrdua causada per la falta) no la talla.
R10 (regla oficial) La possessió només canvia quan un rival té la pilota sota
    control: BALL OUT no canvia de possessió (l'últim que la toca abans que
    surti pot ser un rival que la desvia sense controlar-la); només marca
    l'aturada.
R11 (regla oficial) Un toc sense control no és un canvi: un tram d'un equip de
    menys de MIN_CONTROL_FRAMES entre dos trams de l'altre equip (sense joc
    aturat entremig) s'assigna a l'equip que l'envolta.
R9  Tot SET PIECE implica pilota morta abans: si entre el final de l'últim
    esdeveniment i el SET PIECE hi ha més d'1 s, aquest interval és "aturat"
    (cobreix aturades no anotades: fores de joc amb jugada posterior al xiulet,
    lesions...).
R7  Abans del primer esdeveniment de cada part i després de l'últim -> "aturat".
R8  Si entre l'inici i el final d'un esdeveniment d'aturada hi ha anotats
    altres esdeveniments (típicament el BALL LOST endarrerit d'una THEFT just
    abans que la pilota surti), s'apliquen abans i l'aturada comença igualment
    al frame final. Només si entremig hi ha un SET PIECE (contradicció real)
    la marca d'aturada s'ignora. Tots dos casos es compten.

Convenció de toc (`toc=True`, D-47 i T3q de `docs/pla-tocs.md`): la possessió canvia al primer toc de l'altre
equip, també als rebots. No s'apliquen la R10 (si la pilota surt, la possessió és de l'últim que la toca) ni la R11
(un toc curt de l'altre equip és una possessió), i un duel guanyat sense falta (CHALLENGE ...-WON) és un toc de
l'equip que el guanya, que no reprèn el joc. Per defecte, les regles de sempre.

Versions: `y3` (Home/Away/Aturat), `y2` = `y3` amb màscara dels frames vius
(ignorant l'aturat) i `y2_tot` (cada frame aturat s'assigna a l'equip que
reprèn el joc; variant per si l'avaluació oficial demana Home/Away a tots els
frames).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from possessio.config import ATURAT, AWAY, HOME

TIPUS_POSSESSIO = frozenset({
    "PASS", "CARRY", "RECOVERY", "SET PIECE", "SHOT", "BALL LOST", "BALL OUT",
})
ATURA_BALL_LOST = frozenset({"FORCED", "OFFSIDE", "HAND BALL", "END HALF", "VOLUNTARY"})
NO_REPRENEN = frozenset({"BALL LOST", "BALL OUT"})
NO_CANVIEN_POSSESSIO = frozenset({"BALL OUT"})   # R10
MIN_CONTROL_FRAMES = 12                          # R11 (≈ 0,5 s)
DUEL_SENSE_TOC = frozenset({"FAULT", "ADVANTAGE"})   # convenció de toc: aquests duels guanyats no compten
MIN_BUIT_ABANS_SERVEI = 25          # frames (1 s), regla R9
EQUIP_A_CLASSE = {"Home": HOME, "Away": AWAY}
MAX_ENDARRERIMENT_BALL_LOST = 50   # frames (2 s), regla R2b


@dataclass(frozen=True)
class Etiquetes:
    y3: np.ndarray                 # (n,) HOME / AWAY / ATURAT
    y2_tot: np.ndarray             # (n,) HOME / AWAY a tots els frames
    anomalies: dict = field(default_factory=dict)

    @property
    def viu(self) -> np.ndarray:
        return self.y3 != ATURAT

    @property
    def y2(self) -> np.ndarray:
        """Etiqueta binària; només té sentit amb la màscara `viu`."""
        return np.where(self.viu, self.y3, -1)


def _tokens(subtipus: str) -> set[str]:
    return {t.strip() for t in str(subtipus).split("-") if t.strip()}


def _frame_final(ev: pd.Series) -> int:
    fi = int(ev["end_frame"])
    return fi if fi >= int(ev["start_frame"]) else int(ev["start_frame"])


def _marca_aturada(ev: pd.Series) -> tuple[bool, int]:
    """Retorna (atura?, frame on comença l'aturada) segons R4 i R5."""
    tipus, toks = ev["type"], _tokens(ev["subtype"])
    if tipus == "BALL OUT":
        return True, _frame_final(ev)
    if tipus == "SHOT" and toks & {"OUT", "GOAL"}:
        return True, _frame_final(ev)
    if tipus == "FAULT RECEIVED":
        return True, int(ev["start_frame"])
    if tipus == "CHALLENGE" and "FAULT" in toks:
        return True, int(ev["start_frame"])
    if tipus == "BALL LOST" and toks & ATURA_BALL_LOST:
        return True, _frame_final(ev)
    if "OFFSIDE" in toks:
        return True, _frame_final(ev)
    return False, -1


def _es_duel_guanyat(ev: pd.Series) -> bool:
    """Convenció de toc: CHALLENGE guanyat sense falta ni avantatge."""
    toks = _tokens(ev["subtype"])
    return ev["type"] == "CHALLENGE" and "WON" in toks and not toks & DUEL_SENSE_TOC


def _es_ball_lost_endarrerit(ev: pd.Series, equip_anterior: str | None, inici_anterior: int) -> bool:
    """R2b: BALL LOST anotat just després d'un esdeveniment del rival.

    És el registre (endarrerit) de la pèrdua que el rival ja ha materialitzat
    (RECOVERY THEFT, o una PASS immediata); no retorna la pilota a l'equip.
    """
    return (
        ev["type"] == "BALL LOST"
        and equip_anterior is not None
        and equip_anterior != ev["team"]
        and int(ev["start_frame"]) - inici_anterior <= MAX_ENDARRERIMENT_BALL_LOST
    )


def _aturades_abans_de_servei(ev: pd.DataFrame, es_poss: np.ndarray) -> list[tuple[int, int, int, int, bool]]:
    """R9: interval sense esdeveniments abans de cada SET PIECE -> aturat."""
    out = []
    finals = np.array([_frame_final(e) for _, e in ev.iterrows()])
    rellevant = es_poss | (ev["type"] == "CHALLENGE").to_numpy()
    for i in np.flatnonzero((ev["type"] == "SET PIECE").to_numpy()):
        anteriors = np.flatnonzero(rellevant[:i])
        if len(anteriors) == 0:
            continue
        ultim = int(finals[anteriors].max())
        if int(ev["start_frame"].iat[i]) - ultim > MIN_BUIT_ABANS_SERVEI:
            out.append((ultim + 1, int(anteriors[-1]), 1, ATURAT, True))
    return out


def _filtra_represes(canvis: list[tuple[int, int, int, int, bool]], anomalies: dict) -> list[tuple[int, int, int, int]]:
    """R6: durant una aturada, els esdeveniments que no reprenen el joc s'ignoren."""
    out, estat = [], ATURAT
    for frame, ordre, sub, nou, pot_reprendre in sorted(canvis):
        if estat == ATURAT and nou != ATURAT and not pot_reprendre:
            anomalies["ignorats_durant_aturada"] += 1
            continue
        out.append((frame, ordre, sub, nou))
        estat = nou
    return out


def punts_de_canvi(events: pd.DataFrame, toc: bool = False) -> tuple[list[tuple[int, int, int, int]], dict]:
    """Llista ordenada de (frame, ordre, sub, estat) i recompte d'anomalies. Amb `toc`, la convenció de toc."""
    ev = events.reset_index(drop=True)
    ordre = np.argsort(ev["start_frame"].to_numpy(), kind="stable")
    ev = ev.iloc[ordre].reset_index(drop=True)
    duel = np.array([toc and _es_duel_guanyat(e) for _, e in ev.iterrows()], dtype=bool)
    es_poss = ev["type"].isin(TIPUS_POSSESSIO).to_numpy() | duel
    es_represa = (ev["type"] == "SET PIECE").to_numpy()
    inicis = ev["start_frame"].to_numpy(int)
    canvis: list[tuple[int, int, int, int, bool]] = []
    anomalies = {
        "aturades_contradictories": 0,
        "aturades_amb_esdeveniments_entremig": 0,
        "ball_lost_endarrerits": 0,
        "ignorats_durant_aturada": 0,
        "ball_out_sense_canvi": 0,
        "aturades_inferides_abans_de_servei": 0,
        "esdeveniments_fora_ordre": int(np.sum(np.diff(events["start_frame"].to_numpy()) < 0)),
    }
    equip_anterior, inici_anterior = None, -10**9
    for i, e in ev.iterrows():
        if es_poss[i]:
            if _es_ball_lost_endarrerit(e, equip_anterior, inici_anterior):
                anomalies["ball_lost_endarrerits"] += 1   # R2b
            elif not toc and e["type"] in NO_CANVIEN_POSSESSIO:
                anomalies["ball_out_sense_canvi"] += 1    # R10
            else:
                pot_reprendre = e["type"] not in NO_REPRENEN and not duel[i]
                canvis.append((int(e["start_frame"]), i, 0, EQUIP_A_CLASSE[e["team"]], pot_reprendre))
            equip_anterior, inici_anterior = e["team"], int(e["start_frame"])
        atura, frame_aturada = _marca_aturada(e)
        if not atura:
            continue
        # Esdeveniments simultanis (mateix frame d'inici, p. ex. RECOVERY +
        # BALL OUT + CARRY de 1 frame al partit 3) no contradiuen l'aturada.
        entremig = (inicis[i + 1:] > inicis[i]) & (inicis[i + 1:] < frame_aturada)
        if np.any(entremig & es_represa[i + 1:]):
            anomalies["aturades_contradictories"] += 1      # R8
            continue
        if np.any(entremig & es_poss[i + 1:]):
            anomalies["aturades_amb_esdeveniments_entremig"] += 1
        canvis.append((frame_aturada, i, 1, ATURAT, True))
    r9 = _aturades_abans_de_servei(ev, es_poss)
    anomalies["aturades_inferides_abans_de_servei"] = len(r9)
    return _filtra_represes(canvis + r9, anomalies), anomalies


def _omple_periode(frames: np.ndarray, canvis: list[tuple[int, int, int, int]]) -> np.ndarray:
    estat = np.full(len(frames), ATURAT, dtype=int)
    if not canvis:
        return estat
    fr = np.array([c[0] for c in canvis])
    st = np.array([c[3] for c in canvis])
    idx = np.searchsorted(fr, frames, side="right") - 1
    valid = idx >= 0
    estat[valid] = st[idx[valid]]
    return estat


def deriva_etiquetes(events: pd.DataFrame, frames: np.ndarray, periode: np.ndarray, toc: bool = False) -> Etiquetes:
    """Etiquetes per frame aplicant les regles per separat a cada part. Amb `toc`, la convenció de toc."""
    y3 = np.full(len(frames), ATURAT, dtype=int)
    anomalies_tot: dict = {}
    for per in np.unique(periode):
        mask = periode == per
        ev_p = events[(events["period"] == per) & (events["type"] != "CARD")]
        if ev_p.empty:
            continue
        canvis, anom = punts_de_canvi(ev_p, toc)
        for k, v in anom.items():
            anomalies_tot[k] = anomalies_tot.get(k, 0) + v
        final_part = int(max(ev_p["end_frame"].max(), ev_p["start_frame"].max()))
        canvis.append((final_part + 1, len(ev_p) + 1, 2, ATURAT))   # R7
        omplert = _omple_periode(frames[mask], canvis)
        y3[mask], n_tocs = (omplert, 0) if toc else _fusiona_tocs_sense_control(omplert)
        anomalies_tot["tocs_sense_control"] = anomalies_tot.get("tocs_sense_control", 0) + n_tocs
    return Etiquetes(y3=y3, y2_tot=_assigna_aturat(y3, periode), anomalies=anomalies_tot)


def _fusiona_tocs_sense_control(y: np.ndarray, min_frames: int = MIN_CONTROL_FRAMES) -> tuple[np.ndarray, int]:
    """R11: A-B-A amb B (equip) més curt que min_frames -> A-A-A."""
    out = y.copy()
    inicis = segments(y)
    finals = np.r_[inicis[1:], len(y)]
    n = 0
    for i in range(1, len(inicis) - 1):
        abans, aquest, despres = y[inicis[i - 1]], y[inicis[i]], y[inicis[i + 1]]
        curt = finals[i] - inicis[i] < min_frames
        if curt and aquest != ATURAT and abans == despres and abans not in (ATURAT, aquest):
            out[inicis[i]:finals[i]] = abans
            n += 1
    return out, n


def _assigna_aturat(y3: np.ndarray, periode: np.ndarray) -> np.ndarray:
    """Variant 2 classes a tots els frames: l'aturat passa a l'equip que reprèn.

    Si no hi ha represa posterior dins de la part, s'usa l'últim equip.
    """
    out = y3.copy()
    for per in np.unique(periode):
        idx = np.flatnonzero(periode == per)
        s = pd.Series(np.where(y3[idx] == ATURAT, np.nan, y3[idx]).astype(float))
        omplert = s.bfill().ffill().fillna(HOME).to_numpy(int)
        out[idx] = omplert
    return out


def segments(y: np.ndarray) -> np.ndarray:
    """Inicis dels trams constants (índexs on canvia el valor, incloent 0)."""
    if len(y) == 0:
        return np.array([], dtype=int)
    return np.concatenate([[0], np.flatnonzero(np.diff(y) != 0) + 1])
