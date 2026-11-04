"""Als forats, què diria la pilota i on s'equivoca el segon, abans de triar la idea següent a sobre d'A sense pilota
(`docs/pla-tocs.md`, «La idea següent a sobre d'A sense pilota»). Només per saber-ho.

    cd codi && uv run python -I -m banc.pilota_als_forats

Als forats (on l'escenari no veu la pilota), a les imatges on la veritat de toc és d'un equip, als quatre ×¼ i a
«partit ×¼»:

1. **La pilota estimada i la real.** On la pilota es veu al partit net: quant s'allunya la pilota estimada en línia
   recta (`cadena/xarxa_sense_pilota.estimada`, la que veuen les xarxes d'A sense pilota) de la real, i a quina part de
   les imatges el jugador més proper a la pilota és de l'equip bo, amb la real i amb l'estimada. I a quina part hi
   encerta l'equip el segon d'A sense pilota. Segons quant dura el forat.
2. **On s'equivoca el segon d'A sense pilota:** a les possessions de la veritat que no es veuen mai amb pilota o a les
   que sí; segons quant falta per a la pilota vista més propera; i segons quant dura la possessió.

Escriu `resultats/pilota-als-forats.md`. Tot són dades obertes.
"""

from __future__ import annotations

import itertools
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace

import numpy as np
import pandas as pd

from banc import analisi_t3p as t3p
from banc import analisi_t3r as an
from banc import avalua, fonts
from banc import model_a_partit as mp
from banc import model_a_sense_pilota as msp
from banc import sostre_sense_pilota as ssp
from banc import veritat_toc as vt
from cadena import tocs
from cadena import xarxa_sense_pilota as xsp
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ESCENARIS = (*(e for e in mp.ESCENARIS if e.endswith("×¼") and e != mp.PARTIT), mp.PARTIT)
FORATS = ((0, 2 * pm.FPS, "<2 s"), (2 * pm.FPS, 5 * pm.FPS, "2-5 s"), (5 * pm.FPS, np.inf, "≥5 s"))
LLUNY = ((0, pm.FPS, "<1 s"), (pm.FPS, 2 * pm.FPS, "1-2 s"), (2 * pm.FPS, 5 * pm.FPS, "2-5 s"),
         (5 * pm.FPS, np.inf, "≥5 s"))
POSSESSIONS = ((0, 2 * pm.FPS, "<2 s"), (2 * pm.FPS, 5 * pm.FPS, "2-5 s"), (5 * pm.FPS, np.inf, "≥5 s"))
MAI, ALGUN_COP = "mai", "algun cop"


def a_quin(limits: tuple[tuple[float, float, str], ...], x: np.ndarray) -> np.ndarray:
    out = np.full(len(x), "", dtype=object)
    for baix, alt, nom in limits:
        out[(x >= baix) & ((x < alt) | (alt == np.inf))] = nom
    return out


def equip_mes_proper(casa: np.ndarray, fora: np.ndarray, pilota: np.ndarray) -> np.ndarray:
    """L'equip del jugador més proper a la pilota a cada imatge (a la mateixa distància, l'H)."""
    return np.where(tocs._mes_proper(casa, pilota) <= tocs._mes_proper(fora, pilota), pm.H, pm.A)


def durada_dels_forats(vista: np.ndarray) -> np.ndarray:
    """A cada imatge sense pilota, quant dura el seu tros sense pilota (en imatges); 0 on es veu."""
    out = np.zeros(len(vista))
    for a, b in ssp.trossos(~vista):
        out[a:b] = b - a
    return out


def a_la_vista(vista: np.ndarray) -> np.ndarray:
    """Quantes imatges falten per a la pilota vista més propera (abans o després); infinit si no n'hi ha cap."""
    i = np.arange(len(vista))
    darrera = np.maximum.accumulate(np.where(vista, i, -1))
    seguent = np.minimum.accumulate(np.where(vista, i, len(vista))[::-1])[::-1]
    return np.minimum(np.where(darrera >= 0, i - darrera, np.inf), np.where(seguent < len(vista), seguent - i, np.inf))


def possessions(toc: np.ndarray, trams: list[ssp.Tram], vista: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """A cada imatge d'una possessió de la veritat, si la possessió es veu algun cop amb pilota i quant dura (en
    imatges); fora de les possessions, "" i 0."""
    es_veu, durada = np.full(len(toc), "", dtype=object), np.zeros(len(toc))
    for tram in trams:
        for a, b, _ in pm.possession_spells(toc, [tram]):
            es_veu[a:b] = ALGUN_COP if vista[a:b].any() else MAI
            durada[a:b] = b - a
    return es_veu, durada


def tasca(nom_escenari: tuple[str, str]) -> dict[str, list[dict]]:
    nom, escenari = nom_escenari
    p = mp.degradat(nom, escenari)
    net = fonts.partit(nom)
    toc = vt.veritat(nom)
    trams = avalua.trams_valids(replace(p, veritat=toc))
    vista = ~np.isnan(p.tracking.pilota[:, 0])
    probes, prior, _ = msp.de_qui(msp.A_SENSE, nom)
    encerta = ssp.l_equip(log_relativa(probes[escenari].astype(float), prior)) == toc
    escala = np.asarray(p.tracking.camp_m, float)
    real, estimada = np.full((len(toc), 2), np.nan), np.full((len(toc), 2), np.nan)
    for _, inici, ultim in p.trams:
        part = slice(inici, ultim + 1)
        real[part] = net.tracking.pilota[part] * escala
        estimada[part] = xsp.estimada(p.tracking.pilota[part]) * escala
    casa, fora = p.tracking.casa * escala, p.tracking.fora * escala
    d_equip = ssp.dins(len(toc), trams) & np.isin(toc, (pm.H, pm.A)) & ~vista
    comu = {"partit": nom, "font": p.font, "escenari": escenari}
    i = np.flatnonzero(d_equip & np.isfinite(real).all(axis=1))
    pilota = pd.DataFrame({
        "forat": a_quin(FORATS, durada_dels_forats(vista)[i]),
        "error": np.hypot(*(estimada[i] - real[i]).T),
        "real": equip_mes_proper(casa[i], fora[i], real[i]) == toc[i],
        "estimada": equip_mes_proper(casa[i], fora[i], estimada[i]) == toc[i],
        "segon": encerta[i]})
    es_veu, durada = possessions(toc, trams, vista)
    i = np.flatnonzero(d_equip)
    segon = pd.DataFrame({"es veu": es_veu[i], "a la vista": a_quin(LLUNY, a_la_vista(vista)[i]),
                          "possessio": a_quin(POSSESSIONS, durada[i]), "mal": ~encerta[i]})
    return {"pilota": [{**comu, **r} for r in pilota.groupby("forat").agg(
                n=("error", "size"), error_mig=("error", "median"), real=("real", "sum"),
                estimada=("estimada", "sum"), segon=("segon", "sum")).reset_index().to_dict("records")],
            "segon": [{**comu, **r} for r in segon.groupby(["es veu", "a la vista", "possessio"]).agg(
                n=("mal", "size"), mal=("mal", "sum")).reset_index().to_dict("records")]}


def ordena(t: pd.DataFrame) -> pd.DataFrame:
    return t.reindex([e for e in ESCENARIS if e in t.index.get_level_values(0)], level=0)


def taula_pilota(t: pd.DataFrame, per: str | None) -> pd.DataFrame:
    """Per escenari (i per durada del forat): les imatges, l'error mitjà de la pilota estimada (la mediana, en m), i a
    quina part l'equip del més proper és el bo, amb la real i amb l'estimada, i el segon hi encerta."""
    claus = ["escenari", per] if per else ["escenari"]
    g = t.groupby(claus)[["n", "real", "estimada", "segon"]].sum()
    taula = pd.DataFrame({"n imatges": g["n"], "el més proper a la real": g["real"] / g["n"],
                          "el més proper a l'estimada": g["estimada"] / g["n"], "el segon": g["segon"] / g["n"]})
    if per:
        taula.insert(1, "error de l'estimada (m)", t.groupby(claus)["error_mig"].median())
        taula = taula.reindex([d[2] for d in FORATS], level=per)
    return ordena(taula)


def taula_segon(t: pd.DataFrame, per: str, ordre: tuple[str, ...]) -> pd.DataFrame:
    """Per escenari i segons `per`: quina part de les imatges, quina part s'equivoca el segon i quina part de tots els
    seus errors als forats."""
    g = t.groupby(["escenari", per])[["n", "mal"]].sum()
    tot = t.groupby("escenari")[["n", "mal"]].sum()
    taula = pd.DataFrame({"part de les imatges": g["n"] / tot["n"].reindex(g.index, level=0),
                          "s'hi equivoca": g["mal"] / g["n"],
                          "part dels errors": g["mal"] / tot["mal"].reindex(g.index, level=0)})
    return ordena(taula.reindex(list(ordre), level=per))


def main() -> None:
    from banc import pilota_als_forats as aquest          # pel nom del mòdul, perquè els processos fills el trobin

    with ProcessPoolExecutor(max_workers=12) as feina:
        trossos = list(feina.map(aquest.tasca, itertools.product(fonts.NOMS, ESCENARIS)))
    pilota, segon = (pd.DataFrame([f for t in trossos for f in t[k]]) for k in ("pilota", "segon"))
    sortida = [
        "# Banc obert · Als forats, què diria la pilota i on s'equivoca el segon", "",
        "Generat amb `uv run python -I -m banc.pilota_als_forats`, amb el que ha desat `banc.model_a_sense_pilota`.",
        "Dades obertes. Només per saber-ho. Als forats (on l'escenari no veu la pilota), a les imatges on la veritat",
        "de toc és d'un equip.", "",
        "## La pilota estimada i la real", "",
        "On la pilota es veu al partit net. L'error de la pilota estimada en línia recta (la que veuen les xarxes",
        "d'A sense pilota) és la mediana de la distància a la real, en metres. Després, a quina part de les imatges",
        "el jugador més proper a la pilota és de l'equip bo, amb la real i amb l'estimada, i a quina part hi encerta",
        "l'equip el segon d'A sense pilota (l'equip més probable, amb la relativa).", "",
        t3p.md(taula_pilota(pilota, None)), "",
        "Segons quant dura el forat:", "",
        t3p.md(taula_pilota(pilota, "forat")), "",
        "## On s'equivoca el segon", "",
        "Segons si la possessió de la veritat es veu algun cop amb pilota o mai:", "",
        t3p.md(taula_segon(segon, "es veu", (ALGUN_COP, MAI))), "",
        "Segons quant falta per a la pilota vista més propera, abans o després:", "",
        t3p.md(taula_segon(segon, "a la vista", tuple(d[2] for d in LLUNY))), "",
        "Segons quant dura la possessió:", "",
        t3p.md(taula_segon(segon, "possessio", tuple(d[2] for d in POSSESSIONS))), "",
    ]
    an.DIR_RESULTATS.mkdir(exist_ok=True)
    (an.DIR_RESULTATS / "pilota-als-forats.md").write_text("\n".join(sortida))
    print("\n".join(sortida))


if __name__ == "__main__":
    main()
