"""L'ATD: si és el que diu DATA.md, on falta la pilota i com es comporten els slots."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from inspeccio import grafic
from inspeccio.carrega import Tracking, estructura_xml
from inspeccio.esperat import (TRAMS_FORAT_S, VELOCITAT_JUGADOR_MAX_MS, VELOCITAT_PILOTA_MAX_MS,
                               Esperat)
from inspeccio.seccio import Seccio, comprova_aprop, comprova_igual, pct, xifra
from inspeccio.temps import puntuats, tirades


def mascara(t: Tracking, esperat: Esperat) -> np.ndarray:
    """Al tàctic, els fotogrames puntuats; al broadcast, tots (té una altra línia de temps)."""
    if t.font == "tactical":
        return puntuats(t.frame_video, esperat.rangs_puntuats)
    return np.ones(t.n, bool)


def metres(punts: np.ndarray, esperat: Esperat) -> np.ndarray:
    return punts * np.asarray(esperat.camp_m)


def grup_de_durada(segons: np.ndarray) -> pd.Categorical:
    limits = (0.0, *TRAMS_FORAT_S, np.inf)
    noms = [f"≤ {xifra(TRAMS_FORAT_S[0])} s"]
    noms += [f"{xifra(a)}–{xifra(b)} s" for a, b in zip(TRAMS_FORAT_S, TRAMS_FORAT_S[1:])]
    noms += [f"> {xifra(TRAMS_FORAT_S[-1])} s"]
    return pd.cut(segons, limits, labels=noms, include_lowest=True)


def forats_pilota(t: Tracking, dins: np.ndarray, esperat: Esperat) -> pd.DataFrame:
    """Una fila per forat de la pilota dins dels fotogrames que es miren."""
    falta = np.isnan(t.pilota[:, 0])
    inicis, fins = tirades(falta & dins)
    pilota_m = metres(t.pilota, esperat)
    abans, despres = inicis - 1, fins
    ok_abans = (abans >= 5) & ~falta[np.clip(abans, 0, None)]
    ok_despres = (despres < t.n) & ~falta[np.clip(despres, None, t.n - 1)]
    a = np.clip(abans, 5, None)
    d = np.clip(despres, None, t.n - 1)
    velocitat = np.linalg.norm(pilota_m[a] - pilota_m[a - 5], axis=1) * t.fps / 5
    tots = metres(np.concatenate(t.jugadors, axis=1), esperat)
    distancies = np.linalg.norm(tots[a] - pilota_m[a][:, None], axis=2)
    distancia = np.where(np.isnan(distancies), np.inf, distancies).min(axis=1, initial=np.inf)
    desplacament = np.linalg.norm(pilota_m[d] - pilota_m[a], axis=1)
    return pd.DataFrame({
        "inici": inicis, "fi": fins, "fotogrames": fins - inicis,
        "durada_s": (fins - inicis) / t.fps,
        "velocitat_abans": np.where(ok_abans, velocitat, np.nan),
        "jugador_mes_proper_m": np.where(ok_abans & np.isfinite(distancia), distancia, np.nan),
        "desplacament_m": np.where(ok_abans & ok_despres, desplacament, np.nan),
    })


def taula_forats(forats: pd.DataFrame, falten: int) -> list[tuple]:
    grups = forats.assign(grup=grup_de_durada(forats["durada_s"].to_numpy()))
    files = []
    for nom, g in grups.groupby("grup", observed=False):
        files.append((nom, xifra(len(g)), xifra(int(g["fotogrames"].sum())),
                      f"{xifra(pct(g['fotogrames'].sum(), falten))} %",
                      xifra(g["velocitat_abans"].median()),
                      xifra(g["jugador_mes_proper_m"].median()),
                      xifra(g["desplacament_m"].median())))
    return files


def salts(punts_m: np.ndarray, fps: float, llindar: float) -> int:
    """Passos d'un fotograma al següent més ràpids que `llindar` m/s."""
    velocitat = np.linalg.norm(np.diff(punts_m, axis=0), axis=-1) * fps
    return int(np.nansum(velocitat > llindar))


def comprovacions(t: Tracking, dins: np.ndarray, esperat: Esperat) -> list:
    present = ~np.isnan(t.pilota[:, 0])
    objectes = sum((~np.isnan(j[..., 0])).sum(axis=1) for j in t.jugadors)
    llista = [
        comprova_igual("registres", esperat.fotogrames[t.font], t.n),
        comprova_igual("primer frame_id", 1, int(t.frame_id[0])),
        comprova_igual("últim frame_id", esperat.fotogrames[t.font], int(t.frame_id[-1])),
        comprova_igual("frame_id seguits, sense salts", True, bool(np.all(np.diff(t.frame_id) == 1))),
        comprova_igual("fotogrames per segon", esperat.fps, t.fps),
        comprova_igual("equips", 2, len(t.equips)),
        comprova_igual("slots", esperat.slots[t.font], sum(len(s) for s in t.slots)),
        comprova_aprop("pilota visible, tots els fotogrames", esperat.pilota_visible_pct[t.font],
                       round(pct(present.sum(), t.n), 1), 0.05, " %"),
        comprova_igual("camp a les metadades (m)", (105.0, 68.0), t.camp_metadades),
    ]
    if t.font == "tactical":
        llista += [
            comprova_igual("fotogrames puntuats", esperat.pilota_visible_puntuats[1], int(dins.sum())),
            comprova_igual("puntuats amb pilota", esperat.pilota_visible_puntuats[0],
                           int((present & dins).sum())),
            comprova_aprop("objectes per fotograma puntuat (mitjana)", esperat.objectes_mitjana_puntuats,
                           round(float(objectes[dins].mean()), 1), 0.05),
        ]
    return llista


def metadades(seccio: Seccio, meta: Path) -> None:
    etiquetes, parametres, canals = estructura_xml(meta)
    seccio.taula("Metadades: etiquetes de l'XML", ("Etiqueta", "Quantes"),
                 [(f"`{k}`", xifra(v)) for k, v in etiquetes.items()])
    seccio.taula("Metadades: canals", ("Canal",), [(f"`{c}`",) for c in canals])
    if parametres:
        seccio.taula("Metadades: paràmetres del proveïdor", ("Nom", "Valor"),
                     [(n, v[:120]) for n, v in parametres])


def altres_columnes(seccio: Seccio, t: Tracking) -> None:
    files = []
    for nom in t.altres_columnes.columns:
        col = t.altres_columnes[nom]
        valors = ", ".join(map(str, col.dropna().unique()[:5]))
        files.append((f"`{nom}`", f"{xifra(pct(col.notna().sum(), len(col)))} %", valors))
    seccio.taula("Columnes que no són de jugadors (kloppy)", ("Columna", "Plenes", "Primers valors"),
                 files, "Si `ball_state` o `ball_owning_team_id` vinguessin plenes, caldria "
                        "saber d'on surten abans de fer-les servir.")


def slots(seccio: Seccio, t: Tracking, dins: np.ndarray, esperat: Esperat) -> None:
    files, minuts = [], dins.sum() / t.fps / 60
    for nom, terreny, ids, j in zip(t.equips, t.terrenys, t.slots, t.jugadors):
        hi_es = ~np.isnan(j[..., 0])
        trams = [tirades(hi_es[:, k]) for k in range(len(ids))]
        llargades = np.concatenate([fi - ini for ini, fi in trams]) if trams else np.array([])
        per_fotograma = hi_es[dins].sum(axis=1)
        mirats = metres(np.where(dins[:, None, None], j, np.nan), esperat)   # sense unir les dues parts
        canvis = sum(salts(mirats[:, k], t.fps, VELOCITAT_JUGADOR_MAX_MS) for k in range(len(ids)))
        files.append((f"{nom} ({terreny})", xifra(len(ids)), xifra(len(llargades)),
                      xifra(float(np.median(llargades)) / t.fps if len(llargades) else np.nan),
                      xifra(float(per_fotograma.mean())), f"{xifra(pct((per_fotograma >= 10).sum(), dins.sum()))} %",
                      xifra(canvis / minuts if minuts else np.nan)))
    seccio.taula("Slots per equip", ("Equip", "Slots", "Aparicions", "Aparició mediana (s)",
                                     "Objectes per fotograma", "Fotogrames amb ≥ 10",
                                     f"Salts > {xifra(VELOCITAT_JUGADOR_MAX_MS)} m/s per minut"),
                 files, "Un salt és un pas d'un fotograma al següent impossible per a una persona: "
                        "sovint, el slot ha passat a seguir una altra persona.")


def figura_forats(forats: pd.DataFrame) -> tuple:
    fig, (ax1, ax2) = grafic.figura(3.0, 1, 2)
    durada = forats["durada_s"].to_numpy()
    if len(durada):
        limits = np.logspace(np.log10(1 / 25), np.log10(max(durada.max(), 1)), 40)
        ax1.hist(durada, bins=limits, color=grafic.TINTA_2)
        ordre = np.sort(durada)
        pes = np.cumsum(ordre) / ordre.sum()
        ax2.plot(ordre, pes, color=grafic.TINTA, lw=1.6)
    for ax in (ax1, ax2):
        ax.set_xscale("log")
        ax.set_xlabel("durada del forat (s)")
        for limit in TRAMS_FORAT_S:
            ax.axvline(limit, color=grafic.TINTA_2, lw=0.6, alpha=0.5)
    ax1.set_ylabel("forats")
    ax2.set_ylabel("part dels fotogrames sense pilota")
    ax2.set_ylim(0, 1)
    return fig


def figura_cronologia(t: Tracking, esperat: Esperat) -> tuple:
    fig, (ax1, ax2) = grafic.figura(4.2, 2, 1, sharex=True)
    tram = int(30 * t.fps)
    n = t.n // tram * tram
    minuts = t.frame_video[:n:tram] / t.fps / 60
    present = (~np.isnan(t.pilota[:n, 0])).reshape(-1, tram).mean(axis=1)
    ax1.fill_between(minuts, present, step="post", color=grafic.PILOTA, lw=0)
    ax1.step(minuts, present, where="post", color=grafic.TINTA, lw=0.8)
    ax1.set_ylabel("pilota present")
    ax1.set_ylim(0, 1)
    for index, (nom, j) in enumerate(zip(t.equips, t.jugadors)):
        per_tram = (~np.isnan(j[:n, :, 0])).sum(axis=1).reshape(-1, tram).mean(axis=1)
        ax2.step(minuts, per_tram, where="post", color=grafic.color_equip(index), lw=1.0, label=nom)
    ax2.axhline(11, color=grafic.TINTA_2, lw=0.6, ls="--")
    ax2.set_ylabel("objectes per equip")
    ax2.set_xlabel("minut del vídeo")
    ax2.legend(loc="lower center", ncols=2, frameon=False)
    for ax in (ax1, ax2):
        if t.font == "tactical":
            grafic.ombreja_rangs(ax, esperat.rangs_puntuats, esperat.fps)
    return fig


def omple(seccio: Seccio, t: Tracking, meta: Path, esperat: Esperat, forats: pd.DataFrame | None = None) -> None:
    dins = mascara(t, esperat)
    on = "puntuats" if t.font == "tactical" else "de tot el vídeo"
    seccio.comprovacions(comprovacions(t, dins, esperat))
    forats = forats_pilota(t, dins, esperat) if forats is None else forats
    falten = int(forats["fotogrames"].sum())
    seccio.text(f"**La pilota als fotogrames {on}.** Hi falta en {xifra(falten)} de "
                f"{xifra(int(dins.sum()))} ({xifra(pct(falten, dins.sum()))} %), repartits en "
                f"{xifra(len(forats))} forats. La pregunta per triar l'enfocament és com són de "
                "llargs: els curts es poden omplir amb el tracking; els llargs, o són pilota "
                "morta, o cal anar-la a buscar al vídeo.")
    seccio.taula("Forats de la pilota segons la durada",
                 ("Durada", "Forats", "Fotogrames", "Dels que falten", "Velocitat abans (m/s, mediana)",
                  "Jugador més proper en perdre-la (m)", "Desplaçament fins que torna (m)"),
                 taula_forats(forats, falten),
                 "La velocitat és la dels 5 fotogrames abans del forat. El desplaçament és la "
                 "distància entre on es perd i on torna a sortir.")
    if t.font == "tactical":
        seccio.figura("Forats de la pilota: quants n'hi ha i quina part dels fotogrames sense "
                      "pilota s'acumula fins a cada durada", figura_forats(forats))
        seccio.figura("La pilota i els jugadors al llarg del vídeo (trams de 30 s; en gris, el "
                      "que es puntua)", figura_cronologia(t, esperat))
    present_m = metres(np.where(dins[:, None], t.pilota, np.nan), esperat)
    inicis, fins = tirades(~np.isnan(t.pilota[:, 0]) & dins)
    seccio.taula("Deteccions de la pilota sospitoses", ("Què", "Quantes"), [
        (f"passos de més de {xifra(VELOCITAT_PILOTA_MAX_MS)} m/s",
         xifra(salts(present_m, t.fps, VELOCITAT_PILOTA_MAX_MS))),
        ("aparicions d'1 o 2 fotogrames", xifra(int(((fins - inicis) <= 2).sum()))),
        ("alçada (z) a l'ATD", "sí" if t.pilota_z is not None else "no"),
    ])
    slots(seccio, t, dins, esperat)
    altres_columnes(seccio, t)
    metadades(seccio, meta)
