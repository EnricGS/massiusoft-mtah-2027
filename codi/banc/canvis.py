"""El desfasament dels canvis d'equip al banc obert (T1 del pla per tocs, `docs/pla-tocs.md`).

    cd codi && uv run python -I -m banc.canvis [--processos 8]

Per a cada canvi d'equip de la veritat en joc (d'H a A o al revés, sense pilota morta entremig i dins d'una part),
mira quan hi canvia el mètode:
- **a temps:** el canvi més proper cap a l'equip nou és a menys d'1 s;
- **abans d'hora** o **tard:** a 1 s o més;
- **cap canvi:** no en fa cap cap a l'equip nou en ±5 s;
- **torna:** després del seu canvi, torna a l'equip d'abans en menys de 3 s.

I classifica cada canvi de la veritat:
- **la possessió nova:** breu si dura menys de 2 s (fins que la veritat canvia d'equip o la pilota és morta);
- **la passada:** llarga si la pilota recorre 25 m o més en els 2 s d'abans, al tracking net. Si al net no hi és,
  «?»;
- **la pilota:** «sense» si al degradat falta en la meitat o més dels 2 s d'abans.

Els mètodes són A (el model de la cadena amb el decodificador triat amb els altres nou partits, com a
`model_a.py`) i la millor línia base (smooth125·X). Les X es repeteixen com fa la mètrica oficial. Fa servir les
probabilitats d'A de la memòria cau: abans, `python -I -m banc.model_a`.

Escriu `resultats/canvis.json` (la clau del codi i els resums, per font i en total) i `resultats/canvis.md`. Tot
són dades obertes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from banc import avalua, degrada, fonts, linies_base, model_a
from banc.partit import PartitBanc
from cadena import decodifica
from possessio.oficial import possession_metrics as pm

FPS = 25
FINESTRA = 5 * FPS        # on es busca el canvi del mètode, a cada costat
MARGE_S = 1.0             # per sota, a temps
TORNA = 3 * FPS
ABANS = 2 * FPS           # el tros d'abans del canvi on es mira la passada i la pilota
LLARGA_M = 25.0
MITJA_SENSE = 0.5         # la part del tros d'abans sense pilota a partir de la qual el canvi és «sense»
BREU = 2 * FPS            # una possessió nova més curta és breu
BASE = ("smooth125·X", 125)
PER = ("escenari", "metode", "possessio", "passada", "pilota")
ORDRE = {"metode": ("A", BASE[0]), "possessio": ("≥ 2 s", "< 2 s"), "passada": ("llarga", "curta", "?"),
         "pilota": ("amb", "sense")}
DIR_RESULTATS = Path(__file__).resolve().parent / "resultats"


def canvis_de_la_veritat(veritat: np.ndarray, trams: tuple[tuple[int, int, int], ...]) -> np.ndarray:
    """Les imatges on la veritat passa d'H a A o d'A a H, dins de cada part."""
    trobats = []
    for _, inici, ultim in trams:
        v = veritat[inici:ultim + 1]
        equip = np.isin(v, (pm.H, pm.A))
        trobats.append(inici + 1 + np.flatnonzero(equip[1:] & equip[:-1] & (v[1:] != v[:-1])))
    return np.concatenate(trobats) if trobats else np.array([], dtype=int)


def desfasament(pred: np.ndarray, i: int, nou: int, inici: int, ultim: int) -> int | None:
    """Les imatges del canvi del mètode cap a `nou` més proper a `i` (negatiu, abans d'hora), dins de ±FINESTRA i
    de la part; None si no n'hi ha cap. També compta el canvi que ve d'una pilota morta."""
    lo, hi = max(i - FINESTRA, inici + 1), min(i + FINESTRA, ultim)
    if hi < lo:
        return None
    salts = lo + np.flatnonzero((pred[lo:hi + 1] == nou) & (pred[lo - 1:hi] != nou))
    return int(salts[np.argmin(np.abs(salts - i))] - i) if len(salts) else None


def torna(pred: np.ndarray, j: int, vell: int, ultim: int) -> bool:
    """Si, després del canvi del mètode a `j`, torna a l'equip d'abans en menys de TORNA imatges, dins de la part."""
    return bool((pred[j + 1:min(j + TORNA, ultim + 1)] == vell).any())


def durada(veritat: np.ndarray, i: int, ultim: int) -> int:
    """Les imatges que la veritat es queda amb l'equip d'`i`, des d'`i` i dins de la part."""
    diferents = np.flatnonzero(veritat[i:ultim + 1] != veritat[i])
    return int(diferents[0]) if len(diferents) else ultim + 1 - i


def classifica(net: PartitBanc, degradat: PartitBanc, i: int, inici: int = 0) -> tuple[str, str]:
    """La passada (llarga, curta o ?) al tracking net, i si al degradat hi ha pilota (amb o sense) abans del canvi."""
    escala = np.asarray(net.tracking.camp_m, float)
    passada = "?"
    if i - ABANS >= inici:
        recorregut = np.hypot(*((net.tracking.pilota[i] - net.tracking.pilota[i - ABANS]) * escala))
        if np.isfinite(recorregut):
            passada = "llarga" if recorregut >= LLARGA_M else "curta"
    tros = degradat.tracking.pilota[max(i - ABANS, inici):i, 0]
    sense = len(tros) > 0 and np.isnan(tros).mean() >= MITJA_SENSE
    return passada, "sense" if sense else "amb"


def mesura(net: PartitBanc, degradat: PartitBanc, pred: np.ndarray, metode: str, escenari: str) -> list[dict]:
    """Una fila per canvi de la veritat. Les X del mètode es repeteixen com fa la mètrica oficial."""
    pred = pm.fill_abstentions(pred.astype(np.int8), avalua.trams_valids(net))
    files = []
    for part, inici, ultim in net.trams:
        for i in canvis_de_la_veritat(net.veritat, ((part, inici, ultim),)):
            nou, vell = net.veritat[i], net.veritat[i - 1]
            d = desfasament(pred, int(i), nou, inici, ultim)
            passada, pilota = classifica(net, degradat, int(i), inici)
            files.append({"partit": net.nom, "font": net.font, "escenari": escenari, "metode": metode,
                          "imatge": int(i), "passada": passada, "pilota": pilota,
                          "possessio": "< 2 s" if durada(net.veritat, int(i), ultim) < BREU else "≥ 2 s",
                          "desfas_s": None if d is None else d / FPS,
                          "torna": d is not None and torna(pred, int(i) + d, vell, ultim)})
    return files


def resum(files: pd.DataFrame, per: tuple[str, ...] = PER) -> pd.DataFrame:
    """Per grup: quants canvis, la part que és a temps, abans d'hora, tard o sense canvi, la que torna i la mediana."""
    d = files["desfas_s"].astype(float)
    marcat = files.assign(desfas_s=d, a_temps=d.abs() < MARGE_S, abans=d <= -MARGE_S, tard=d >= MARGE_S,
                          cap=d.isna(), torna=files["torna"].astype(bool))
    return (marcat.groupby(list(per), sort=False)
            .agg(canvis=("desfas_s", "size"), a_temps=("a_temps", "mean"), abans=("abans", "mean"),
                 tard=("tard", "mean"), cap=("cap", "mean"), torna=("torna", "mean"),
                 mediana_s=("desfas_s", "median"))
            .reset_index())


def decodificadors(files: pd.DataFrame) -> dict[str, tuple[float, int]]:
    """La λ i la durada mínima de cada partit, triades amb els altres nou (`model_a.tria_sense_mirar`)."""
    a = model_a.tria_sense_mirar(files)
    a = a[a["metode"] == "A"].drop_duplicates("partit")
    return {fila.partit: (float(fila.lam), int(fila.d_min)) for fila in a.itertuples()}


def files_de(tasca: tuple[str, str, float, int]) -> list[dict]:
    """Un partit i un escenari, amb A i la línia base (a part, perquè la cridi un procés fill)."""
    nom, escenari, lam, d_min = tasca
    net = fonts.partit(nom)
    degradat = degrada.aplica(net, escenari)
    probes, prior = model_a.probabilitats(nom, entrena=False)
    prediccions = {"A": decodifica.per_trams(probes[escenari].astype(float), prior, degradat.trams, lam, d_min),
                   BASE[0]: linies_base.prediu(degradat, BASE[1], "X")}
    return [f for metode, pred in prediccions.items() for f in mesura(net, degradat, pred, metode, escenari)]


def _ordena(r: pd.DataFrame) -> pd.DataFrame:
    claus = {col: r[col].map({v: k for k, v in enumerate(ordre)}) for col, ordre in ORDRE.items() if col in r}
    return r.assign(**{f"_{c}": v for c, v in claus.items()}).sort_values([f"_{c}" for c in claus]).drop(
        columns=[f"_{c}" for c in claus])


def markdown(r: pd.DataFrame) -> str:
    def pct(v: float) -> str:
        return f"{v:.0%}"

    def mediana(v: float) -> str:
        return "—" if pd.isna(v) else f"{v:+.2f}"

    linies = ["# Banc obert · el desfasament dels canvis d'equip", "",
              "Generat amb `uv run python -I -m banc.canvis` (T1 del pla per tocs, `docs/pla-tocs.md`). Dades obertes:",
              "7 partits de DFL (IDSSE, CC BY 4.0) i els 3 de mostra de Metrica. Cap dada del concurs.", "",
              "Per a cada canvi d'equip de la veritat en joc (d'H a A o al revés, sense pilota morta entremig), quan",
              "hi canvia el mètode: **a temps** (a menys d'1 s), **abans d'hora** o **tard** (1 s o més), o **cap**",
              "(cap canvi cap a l'equip nou en ±5 s). **Torna**: després del seu canvi, torna a l'equip d'abans en",
              "menys de 3 s. La **passada** és llarga si la pilota recorre 25 m o més en els 2 s d'abans (al tracking",
              "net; «?» si no hi és). **Sense pilota**: al degradat falta en la meitat o més d'aquests 2 s. La",
              "**mediana** és la del desfasament en segons (negatiu, abans d'hora), només dels canvis trobats. La",
              "**possessió** nova és breu si dura menys de 2 s.", ""]
    for escenari in degrada.NOMS:
        tria = _ordena(r[r["escenari"] == escenari])
        if tria.empty:
            continue
        sense_passada = int(tria.loc[tria["passada"] == "?", "canvis"].sum() / tria["metode"].nunique())
        tria = tria[tria["passada"] != "?"]
        linies += [f"**{escenari}** ({sense_passada} canvis sense la pilota al net, per mètode, no hi surten)", "",
                   "| mètode | possessió | passada | pilota | canvis | a temps | abans d'hora | tard | cap | torna "
                   "| mediana (s) |",
                   "|---|---|---|---|---|---|---|---|---|---|---|"]
        linies += [f"| {f.metode} | {f.possessio} | {f.passada} | {f.pilota} | {f.canvis} | {pct(f.a_temps)} | "
                   f"{pct(f.abans)} | "
                   f"{pct(f.tard)} | {pct(f.cap)} | {pct(f.torna)} | {mediana(f.mediana_s)} |"
                   for f in tria.itertuples()]
        linies.append("")
    return "\n".join(linies)


def clau() -> str:
    """El que fa aquests resultats: el que fa els d'A, aquest fitxer i la línia base."""
    h = hashlib.sha256(model_a.CLAU_RESULTATS.encode())
    for modul in (linies_base, avalua):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def a_json(files: pd.DataFrame) -> str:
    def registres(t: pd.DataFrame) -> list[dict]:
        return t.astype(object).where(t.notna(), None).to_dict("records")

    return json.dumps({"clau": clau(), "per_font": registres(resum(files, ("font", *PER))),
                       "total": registres(resum(files))}, indent=1, default=float)


def main() -> None:
    from banc import canvis      # pel nom del mòdul, perquè els processos fills trobin les funcions

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=8)
    args = ap.parse_args()
    triats = decodificadors(model_a.resultats())
    tasques = [(nom, escenari, *triats[nom]) for nom in fonts.NOMS for escenari in degrada.NOMS]
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        files = pd.DataFrame([f for tros in feina.map(canvis.files_de, tasques) for f in tros])
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "canvis.json").write_text(a_json(files))
    (DIR_RESULTATS / "canvis.md").write_text(markdown(resum(files)))
    print((DIR_RESULTATS / "canvis.md").read_text())


if __name__ == "__main__":
    main()
