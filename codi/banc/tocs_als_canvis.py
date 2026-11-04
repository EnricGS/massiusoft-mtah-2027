"""Als canvis d'equip on es veu la pilota, què hi troba el detector de tocs fet a mà (`cadena/tocs.py`, el dels
senyals del control), abans de triar la idea següent (`docs/pla-tocs.md`, «Tres maneres d'ajudar el segon a prop
dels tocs»). Només per saber-ho.

    cd codi && uv run python -I -m banc.tocs_als_canvis

Un canvi és el començament d'una possessió de la veritat de toc que ve de l'altre equip, amb la pilota a la vista
(fora dels forats, com a `marge_sense_pilota`). Al net, als quatre ×¼ i a «partit ×¼», amb A sense pilota i el
decodificador triat a cada partit a la veritat de toc:

1. **Què hi troba el detector** a ±0,5 s: un toc de l'equip nou, només de l'equip d'abans, o cap.
2. **Si la predicció hi arriba tard:** si a la primera mitja segona de la possessió (o menys, si és més curta) hi
   dona l'equip nou a menys de la meitat de les imatges. I què en diu el segon (com a `errors_amb_pilota`).
3. **On no troba el de l'equip nou, com és el toc** a ±3 imatges del canvi: el jugador de l'equip nou més a prop de
   la pilota hi és a 2 m o menys i més a prop que cap de l'altre equip, amb un canvi de velocitat de la pilota com el
   que busca el detector (*fort*) o més petit (*suau*); o hi ha un de l'altre equip igual o més a prop
   (*disputat*); o no n'hi ha cap a 2 m (*lluny*).

Escriu `resultats/tocs-als-canvis.md`. Tot són dades obertes.
"""

from __future__ import annotations

import itertools
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace

import numpy as np
import pandas as pd

from banc import analisi_t3p as t3p
from banc import analisi_t3q as t3q
from banc import analisi_t3r as an
from banc import avalua, fonts
from banc import errors_amb_pilota as eap
from banc import marge_sense_pilota as mm
from banc import model_a_canvis as t3i
from banc import model_a_partit as mp
from banc import model_a_sense_pilota as msp
from banc import sostre_curtes as sc
from banc import veritat_toc as vt
from cadena import tocs
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ESCENARIS = t3q.ESCENARIS
A_SENSE = msp.A_SENSE
FINESTRA = pm.FPS // 2                              # 0,5 s
AL_VOLTANT = 3                                      # imatges a cada banda on es mira qui és a prop
PAR = tocs.Parametres()
BO, D_ABANS, CAP = "de l'equip nou", "de l'equip d'abans, només", "cap"
TROBATS = (BO, D_ABANS, CAP)
FORT, SUAU, DISPUTAT, LLUNY = "a prop, fort", "a prop, suau", "disputat", "lluny"
MENES = (FORT, SUAU, DISPUTAT, LLUNY)
TARD = "tard"


def canvis(toc: np.ndarray, trams: list[tuple[int, int]], forat: np.ndarray) -> list[tuple[int, int, int]]:
    """Les possessions de la veritat (a, b, k) que vénen de l'altre equip, amb la pilota a la vista a l'inici."""
    return [(a, b, k) for tram in trams for a, b, k in pm.possession_spells(toc, [tram])
            if a > tram[0] and toc[a - 1] in pm.POSSESSION_LABELS and not forat[a]]


def trobat(imatges: np.ndarray, equips: np.ndarray, a: int, k: int, finestra: int = FINESTRA) -> str:
    """Què troba el detector a ±`finestra` imatges del canvi a l'equip `k`."""
    prop = (imatges >= a - finestra) & (imatges <= a + finestra)
    return BO if np.any(equips[prop] == k) else D_ABANS if prop.any() else CAP


def mena(casa: np.ndarray, fora: np.ndarray, pilota: np.ndarray, canvi: np.ndarray, a: int, k: int) -> str:
    """Com és el toc a ±`AL_VOLTANT` imatges del canvi a l'equip `k` (en metres; `canvi`, el de la velocitat de la
    pilota, en m/s)."""
    j = np.arange(max(a - AL_VOLTANT, 0), min(a + AL_VOLTANT + 1, len(pilota)))
    d_h, d_a = tocs._mes_proper(casa[j], pilota[j]), tocs._mes_proper(fora[j], pilota[j])
    nou, abans = (d_h, d_a) if k == pm.H else (d_a, d_h)
    m = int(np.argmin(nou))
    if nou[m] > PAR.abast_m:
        return LLUNY
    if abans[m] <= nou[m]:
        return DISPUTAT
    c = canvi[max(a - 2 * AL_VOLTANT, 0):a + 2 * AL_VOLTANT + 1]
    return FORT if np.isfinite(c).any() and np.nanmax(c) >= PAR.canvi_ms else SUAU


def tasca(nom_escenari: tuple[str, str]) -> list[dict]:
    nom, escenari = nom_escenari
    p = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    trams = avalua.trams_valids(replace(p, veritat=toc))
    forat = sc.forats(~np.isnan(p.tracking.pilota[:, 0]))
    probes, prior, q_ = msp.de_qui(A_SENSE, nom)
    relativa = log_relativa(probes[escenari].astype(float), prior)
    w, lam, d_min = mm.triades()[A_SENSE][nom]
    pred = t3i.per_trams(relativa, q_[escenari].astype(float), p.trams, w, lam, int(d_min))
    diu = eap.segon(relativa, toc)
    det = tocs.detecta(p.tracking, p.trams, PAR)
    escala = np.asarray(p.tracking.camp_m, float)
    pilota, casa, fora = p.tracking.pilota * escala, p.tracking.casa * escala, p.tracking.fora * escala
    canvi = np.full(len(pilota), np.nan)
    for _, inici, ultim in p.trams:
        canvi[inici:ultim + 1] = tocs._canvi_de_velocitat(pilota[inici:ultim + 1], PAR.k)
    files = []
    for a, b, k in canvis(toc, trams, forat):
        primera = slice(a, a + min(FINESTRA, b - a))
        files.append({"partit": nom, "font": p.font, "escenari": escenari,
                      "trobat": trobat(det.imatge, det.equip, a, k), "mena": mena(casa, fora, pilota, canvi, a, k),
                      TARD: bool(np.mean(pred[primera] == k) < 0.5), "segon": pd.Series(diu[primera]).mode().iloc[0]})
    return files


def parts(files: pd.DataFrame, tret: str, ordre: tuple[str, ...]) -> pd.DataFrame:
    """Per escenari, quina part dels canvis de `files` és de cada valor del `tret`."""
    t = pd.crosstab(files["escenari"], files[tret], normalize="index").reindex(columns=list(ordre), fill_value=0)
    return t3q.ordena(t.rename_axis(index="escenari", columns=None))


def taula_canvis(files: pd.DataFrame) -> pd.DataFrame:
    """Per escenari: quants canvis, què hi troba el detector, i a quina part hi arriba tard la predicció (a tots i
    segons el que troba)."""
    t = parts(files, "trobat", TROBATS)
    tard = files.groupby(["escenari", "trobat"])[TARD].mean().unstack("trobat").reindex(columns=list(TROBATS))
    return pd.concat([files.groupby("escenari").size().rename("n canvis"), t,
                      files.groupby("escenari")[TARD].mean().rename("tard, a tots"),
                      tard.rename(columns=lambda c: f"tard, si troba {c}")], axis=1).pipe(t3q.ordena)


def main() -> None:
    from banc import tocs_als_canvis as aquest           # pel nom del mòdul, perquè els processos fills el trobin

    with ProcessPoolExecutor(max_workers=10) as feina:
        files = pd.DataFrame([f for t in feina.map(aquest.tasca, itertools.product(fonts.NOMS, ESCENARIS)) for f in t])
    tard = files[files[TARD]]
    sense = files[files["trobat"] != BO]
    net = sense[sense["escenari"] == "net"]
    sortida = [
        "# Banc obert · Què troba el detector de tocs als canvis d'equip", "",
        "Generat amb `uv run python -I -m banc.tocs_als_canvis`, amb el que ha desat `banc.model_a_sense_pilota`.",
        f"Dades obertes. Només per saber-ho. {A_SENSE}, a la veritat de toc, amb el decodificador triat a cada partit a",
        "la veritat de toc. Un canvi: el començament d'una possessió de la veritat que ve de l'altre equip, amb la pilota",
        f"a la vista. El detector de tocs és el de `cadena/tocs.py` (canvi de velocitat de {PAR.canvi_ms} m/s o més, amb",
        f"un jugador a {PAR.abast_m} m o menys).", "",
        "## Què hi troba el detector", "",
        "A ±0,5 s del canvi: quina part dels canvis hi té un toc de l'equip nou, només de l'equip d'abans o cap. I a",
        "quina part la predicció hi arriba tard (a la primera mitja segona de la possessió hi dona l'equip nou a menys",
        "de la meitat de les imatges), a tots els canvis i segons el que troba el detector.", "",
        t3p.md(taula_canvis(files)), "",
        "Dels canvis on la predicció hi arriba tard, què hi troba el detector, i què en diu el segon (el que més hi",
        "diu a la primera mitja segona, com a `errors_amb_pilota`):", "",
        t3p.md(pd.concat([parts(tard, "trobat", TROBATS), parts(tard, "segon", eap.SEGONS)], axis=1)), "",
        "## On no troba el de l'equip nou, com és el toc", "",
        f"A ±{AL_VOLTANT} imatges del canvi. *A prop:* el jugador de l'equip nou més a prop de la pilota hi és a",
        f"{PAR.abast_m} m o menys, i més a prop que cap de l'altre equip; *fort*, si la pilota hi canvia de velocitat",
        f"{PAR.canvi_ms} m/s o més (a ±{2 * AL_VOLTANT} imatges), i *suau*, si no. *Disputat:* n'hi ha un de l'equip",
        f"d'abans igual o més a prop. *Lluny:* cap de l'equip nou a {PAR.abast_m} m o menys.", "",
        t3p.md(parts(sense, "mena", MENES)), "",
        "I només on, a més, la predicció hi arriba tard:", "",
        t3p.md(parts(sense[sense[TARD]], "mena", MENES)), "",
        "Al net, per font:", "",
        t3p.md(pd.crosstab(net["font"], net["mena"], normalize="index").reindex(columns=list(MENES), fill_value=0)
               .rename_axis(index="font", columns=None)), "",
    ]
    an.DIR_RESULTATS.mkdir(exist_ok=True)
    (an.DIR_RESULTATS / "tocs-als-canvis.md").write_text("\n".join(sortida))
    print("\n".join(sortida))


if __name__ == "__main__":
    main()
