"""Per què no passa la T3q: on canvia la veritat de toc i què hi fan A xarxes i A toc (`docs/pla-tocs.md`, «Per
què no passa la T3q»). Només per saber-ho.

    cd codi && uv run python -I -m banc.analisi_t3q

Amb les probabilitats i les q que han desat `banc.model_a_partit` (A xarxes) i `banc.model_a_toc` (A toc), i el
decodificador triat a cada partit (`resultats/model-a-toc.json`); tot puntuat a la veritat de toc:

1. **On canvia la veritat de toc:** els trossos d'imatges que canvien d'equip. Una *possessió nova* si tota la
   possessió de toc on és hi és nova (els rebots i els tocs que acaben a la morta); si no, un *canvi avançat* (la
   possessió ja hi era, i ara comença abans). La durada mínima del decodificador triat és de 12 imatges (0,48 s).
2. **Què hi fan els models,** abans i després de decodificar: la part de les imatges on donen l'equip de toc o la
   D, segons la mena i si la pilota es veu.
3. **El sostre:** A xarxes, amb les imatges que canvien posades com la veritat de toc. És el màxim que s'hi guanya
   encertant-les, sense tocar res més.
4. **Les possessions per durada,** com a la T3p.

Escriu `resultats/analisi-t3q.md`. Tot són dades obertes.
"""

from __future__ import annotations

import functools
import itertools
import json
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace

import numpy as np
import pandas as pd

from banc import analisi_t3p as an
from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_partit as mp
from banc import model_a_toc as mt
from banc import veritat_toc as vt
from cadena import model
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

METODES = (mt.XARXES, mt.A_TOC)
ESCENARIS = ("net", *t3.QUARTS, mp.PARTIT)
D_MIN = 12                                       # la durada mínima del decodificador triat, en imatges
LIMITS = (0, D_MIN, pm.FPS, 2 * pm.FPS, 5 * pm.FPS, np.inf)
NOMS_DURADA = ("<0,48 s", "0,48-1 s", "1-2 s", "2-5 s", "≥5 s")
NOVA, AVANCAT, RESTA = "possessió nova", "canvi avançat", "la resta en joc"
MENES = (NOVA, AVANCAT, RESTA)
DONA = ("toc", "altre", "D")                     # l'equip de toc, l'altre equip (a les que canvien, el de sempre), la D
Tros = tuple[int, int, str]
SOSTRES: dict[str, Callable[[Tros], bool]] = {
    "totes": lambda t: True,
    "les noves": lambda t: t[2] == NOVA,
    "les avançades": lambda t: t[2] == AVANCAT,
    "totes menys les noves de <0,48 s": lambda t: not (t[2] == NOVA and t[1] - t[0] < D_MIN),
}
ORDRE = {nom: i for i, nom in enumerate((*ESCENARIS, *MENES, *NOMS_DURADA, "reals", "predites", *METODES,
                                         "abans", "després", "dfl", "metrica", *SOSTRES, True, False))}


@functools.cache
def triades() -> dict[str, dict[str, list]]:
    """El decodificador triat a cada partit pel banc de la T3q."""
    return json.loads((mt.DIR_RESULTATS / "model-a-toc.json").read_text())["triades"]


def durada(imatges: int) -> str:
    return NOMS_DURADA[int(np.searchsorted(LIMITS, imatges, side="right")) - 1]


def trossos(sempre: np.ndarray, toc: np.ndarray, trams: list[tuple[int, int]]) -> list[Tros]:
    """Els trossos d'imatges on la veritat de toc canvia d'equip: tota una possessió de toc (nova) o un tros d'una
    que ja hi era (avançat)."""
    canvia = sempre != toc
    out = []
    for a, b, _ in pm.possession_spells(toc, trams):
        dins = canvia[a:b]
        if dins.all():
            out.append((a, b, NOVA))
        elif dins.any():
            out += [(a + i, a + j, AVANCAT) for i, j, k in pm.segments(dins.astype(np.int8), [(0, b - a)]) if k]
    return out


def menes(n: int, trossos_: list[Tros]) -> np.ndarray:
    """La mena de cada imatge: la del seu tros, o RESTA."""
    out = np.full(n, RESTA, dtype=object)
    for a, b, mena in trossos_:
        out[a:b] = mena
    return out


def que_dona(codis: np.ndarray, toc: np.ndarray) -> np.ndarray:
    """A cada imatge en joc: «toc» si dona l'equip de toc, «D» si dona la D i, si no, «altre»."""
    return np.select([codis == toc, codis == pm.D], ["toc", "D"], "altre")


def amb_la_veritat(pred: np.ndarray, toc: np.ndarray, trossos_: list[Tros]) -> np.ndarray:
    """`pred`, amb les imatges dels trossos posades com la veritat de toc."""
    out = pred.copy()
    for a, b, _ in trossos_:
        out[a:b] = toc[a:b]
    return out


def imatges(comu: dict, abans: np.ndarray, pred: np.ndarray, toc: np.ndarray, mena: np.ndarray,
            vista: np.ndarray) -> list[dict]:
    """Les imatges en joc, per mena i si la pilota es veu: què hi dona el model, abans i després de decodificar."""
    en_joc = np.isin(toc, pm.POSSESSION_LABELS)
    files = []
    for m, v in itertools.product(MENES, (True, False)):
        sel = en_joc & (mena == m) & (vista == v)
        for moment, codis in (("abans", abans), ("després", pred)):
            dona = que_dona(codis[sel], toc[sel])
            files.append({**comu, "mena": m, "pilota": v, "moment": moment, "imatges": int(sel.sum()),
                          **{k: int((dona == k).sum()) for k in DONA}})
    return files


def possessions(comu: dict, pred: np.ndarray, toc: np.ndarray, trams: list[tuple[int, int]]) -> list[dict]:
    """Les possessions reals i les predites, per durada, i si s'aparellen (com la mètrica)."""
    reals = pm.possession_spells(toc, trams)
    predites = pm.possession_spells(pm.fill_abstentions(pred, trams), trams)
    files = []
    for qui, de, contra in (("reals", reals, predites), ("predites", predites, reals)):
        files += [{**comu, "qui": qui, "durada": durada(b - a), "aparellada": m}
                  for (a, b, _), m in zip(de, an.aparellats(de, contra))]
    return files


def tasca(nom_escenari: tuple[str, str]) -> dict[str, list[dict]]:
    nom, escenari = nom_escenari
    de_sempre = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    p_toc = replace(de_sempre, veritat=toc)
    trams = avalua.trams_valids(p_toc)
    trossos_ = trossos(de_sempre.veritat.astype(np.int8), toc, trams)
    mena = menes(len(toc), trossos_)
    vista = ~np.isnan(de_sempre.tracking.pilota[:, 0])
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}
    out = {"veritat": [], "spell": [], "imatges": [], "possessions": [], "sostre": []}
    if escenari == "net":
        out["veritat"] = [{**comu, "mena": m, "durada": durada(b - a), "imatges": b - a} for a, b, m in trossos_]
    for metode in METODES:
        probes, prior, q = mt.de_qui(metode, nom)
        w, lam, d_min = triades()[metode][nom]
        pred = t3i.per_trams(log_relativa(probes[escenari].astype(float), prior), q[escenari].astype(float),
                             de_sempre.trams, w, lam, int(d_min))
        abans = np.asarray(model.CLASSES)[np.nan_to_num(probes[escenari], nan=-1.0).argmax(1)]
        c = {**comu, "metode": metode}
        out["spell"].append({**c, "w": w, "lam": lam, "d_min": d_min,
                             "spell_f1": avalua.puntua(p_toc, pred)["spell_f1"]})
        out["imatges"] += imatges(c, abans, pred, toc, mena, vista)
        out["possessions"] += possessions(c, pred, toc, trams)
        if metode == mt.XARXES:
            out["sostre"] += [{**c, "sostre": s, "spell_f1": avalua.puntua(
                p_toc, amb_la_veritat(pred, toc, [t for t in trossos_ if quins(t)]))["spell_f1"]}
                for s, quins in SOSTRES.items()]
    return out


def ordena(t: pd.DataFrame) -> pd.DataFrame:
    """L'índex en l'ordre d'ORDRE (els escenaris, les menes, les durades…), i no l'alfabètic."""
    return t.sort_index(key=lambda idx: idx.map(lambda x: ORDRE.get(x, len(ORDRE))))


def comprova(spell: pd.DataFrame) -> None:
    """Les prediccions d'aquí són les del banc de la T3q: el mateix spellF1, partit a partit."""
    files = pd.DataFrame(json.loads((mt.DIR_RESULTATS / "model-a-toc.json").read_text())["files"])
    claus = ["partit", "escenari", "metode", "w", "lam", "d_min"]
    del_banc = files[files["veritat"] == mt.TOC][[*claus, "spell_f1"]]
    junts = spell.merge(del_banc, on=claus, suffixes=("", " del banc"), how="left")
    if junts["spell_f1 del banc"].isna().any() or not np.allclose(junts["spell_f1"], junts["spell_f1 del banc"]):
        raise RuntimeError("Les prediccions no són les del banc de la T3q")


def taula_veritat(v: pd.DataFrame) -> pd.DataFrame:
    g = v.groupby(["font", "mena", "durada"])["imatges"].agg(["size", "sum"])
    t = pd.DataFrame({"n trossos": g["size"], "segons": g["sum"] / pm.FPS,
                      "part de les imatges que canvien": g["sum"] / g["sum"].groupby(level="font").transform("sum")})
    return ordena(t)


def taula_imatges(im: pd.DataFrame, que: str) -> pd.DataFrame:
    """La part de les imatges on el model dona `que`, per escenari, mena i pilota (columnes: mètode · moment)."""
    g = im.groupby(["escenari", "mena", "pilota", "metode", "moment"])[[que, "imatges"]].sum()
    t = (g[que] / g["imatges"]).unstack(["metode", "moment"])
    n = g["imatges"].xs((mt.XARXES, "abans"), level=["metode", "moment"]).rename("n imatges")
    t = t.reindex(columns=pd.MultiIndex.from_product([METODES, ("abans", "després")]))
    t.columns = [" · ".join(c) for c in t.columns]
    return ordena(t.join(n))


def taula_sostre(spell: pd.DataFrame, so: pd.DataFrame) -> pd.DataFrame:
    base = spell[spell["metode"] == mt.XARXES].groupby("escenari")["spell_f1"].mean().rename(mt.XARXES)
    guany = so.groupby(["escenari", "sostre"])["spell_f1"].mean().unstack("sostre").sub(base, axis=0)
    guany = guany[list(SOSTRES)].add_prefix("guany: ")
    return ordena(pd.concat([base, guany], axis=1))


def taula_possessions(po: pd.DataFrame) -> pd.DataFrame:
    rec = po.groupby(["escenari", "qui", "durada", "metode"])["aparellada"].agg(["mean", "size"])
    t = rec["mean"].unstack("metode")[list(METODES)].join(rec["size"].unstack("metode")[list(METODES)].add_prefix("n "))
    return ordena(t)


def main() -> None:
    with ProcessPoolExecutor(max_workers=10) as feina:
        trossos_ = list(feina.map(tasca, itertools.product(fonts.NOMS, ESCENARIS)))
    t = {k: pd.DataFrame([f for tros in trossos_ for f in tros[k]]) for k in trossos_[0]}
    comprova(t["spell"])
    sortida = [
        "## On canvia la veritat de toc", "",
        "*Possessió nova:* tota la possessió de toc hi és nova (els rebots i els tocs que acaben a la morta). *Canvi",
        "avançat:* la possessió ja hi era, i ara comença abans. La durada d'una nova és la de la possessió; la d'un",
        "avançat, quant s'avança. El decodificador no fa trossos de menys de 12 imatges (0,48 s).", "",
        an.md(taula_veritat(t["veritat"])), "",
        "## Què hi donen els models: l'equip de toc", "",
        "La part de les imatges en joc on donen l'equip de toc, abans de decodificar (la classe més probable) i",
        "després. A les que canvien, l'altre equip és el de la veritat de sempre.", "",
        an.md(taula_imatges(t["imatges"], "toc")), "",
        "## Què hi donen els models: la D", "",
        an.md(taula_imatges(t["imatges"], "D")), "",
        "## El sostre: A xarxes, amb les imatges que canvien posades com la veritat de toc", "",
        "spellF1 a la veritat de toc (mitjana dels deu partits), i quant hi guanya.", "",
        an.md(taula_sostre(t["spell"], t["sostre"])), "",
        "## Possessions per durada, a la veritat de toc: la part aparellada (mitjana dels llindars d'IoU)", "",
        "*reals*: el record; *predites*: la precisió. *n*: quantes n'hi ha (els deu partits).", "",
        an.md(taula_possessions(t["possessions"])), "",
    ]
    cap = ["# Banc obert · Per què no passa la T3q", "",
           "Generat amb `uv run python -I -m banc.analisi_t3q`, amb el que han desat `banc.model_a_partit` i",
           "`banc.model_a_toc`. Dades obertes. Només per saber-ho. Les prediccions són les del banc de la T3q (✓",
           "comprovat: el mateix spellF1 a cada partit).", ""]
    (mt.DIR_RESULTATS / "analisi-t3q.md").write_text("\n".join(cap + sortida))
    print("\n".join(sortida))


if __name__ == "__main__":
    main()
