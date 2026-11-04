"""La veritat de toc del banc (T3q de `docs/pla-tocs.md`, D-47 i D-48): la possessió canvia al primer toc de l'altre
equip, també als rebots. La D i la X són les de sempre.

    cd codi && uv run python -I -m banc.veritat_toc [--processos 4]

- **DFL:** la veritat de sempre (`banc/dfl.py`), corregida als tocs. L'hora dels esdeveniments de DFL no va amb les
  imatges: cada toc es col·loca a la imatge on el jugador és més a prop de la pilota, de 3 s abans a 1 s després de
  l'hora de l'esdeveniment, si hi és a menys d'1,5 m (`col_loca`). A cada toc de l'equip que no la té (`de_toc`):
  - si DFL hi passa la possessió més de 0,2 s després del toc, és d'aquest equip des del toc («tard»);
  - si no hi passa abans que l'altre equip la torni a tocar, és d'aquest equip fins al toc següent («rebot»);
  - si abans la pilota es mor, és d'aquest equip fins que es mor («fins a la morta»);
  - si DFL hi passa la possessió en 0,2 s o menys, o si en 3 s no passa res d'això, no es toca.
- **Metrica:** les regles de `possessio/etiquetes.py` amb la convenció de toc (`toc=True`).

Cada veritat es desa a `dades/banc/toc/`, amb la clau del codi i de la veritat de sempre, i es comprova que la D i la
X no canvien. Escriu `resultats/veritat-toc.md`, quant canvia cada partit. Tot són dades obertes.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import re
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

import numpy as np

from banc import avalua, dfl, fonts
from banc.partit import PartitBanc
from possessio import etiquetes
from possessio.carrega import carrega_partit
from possessio.oficial import possession_metrics as pm

ABANS, DESPRES = 3 * pm.FPS, 1 * pm.FPS     # on es busca el toc, al voltant de l'hora de l'esdeveniment
MAX_DISTANCIA_M = 1.5
MARGE = pm.FPS // 5                         # 0,2 s
MAX_REBOT = 3 * pm.FPS
TOCS_DFL = ("Play", "OtherBallAction", "BallClaiming", "ShotAtGoal", "BallDeflection")
DUEL_AMB_TOC = ("ballcontactSucceeded", "layoff", "ballControlRetained", "ballClaimed")
CASOS = ("tard", "rebot", "fins a la morta", "dins del marge", "sense final")
DIR_CAU = fonts.DIR_CAU / "toc"
DIR_RESULTATS = Path(__file__).resolve().parent / "resultats"

_FRAME = re.compile(r'<Frame N="(\d+)" T="([^"]+)" X="([^"]+)" Y="([^"]+)"')
_POSSESSIO = re.compile(r'BallPossession="(\d)" BallStatus="(\d)"')
_ESDEVENIMENT = re.compile(r'<Event [^>]*EventTime="([^"]+)"[^>]*>(.*?)</Event>', re.DOTALL)
_TOC = re.compile(rf'<({"|".join((*TOCS_DFL, "TacklingGame"))})\b([^>]*)>')


class Toc(NamedTuple):
    temps: float        # s (hora de l'esdeveniment)
    tipus: str
    jugador: str
    equip: int          # pm.H o pm.A


class TrackingDFL(NamedTuple):
    persones: dict[str, dict[int, tuple[float, float]]]     # PersonId (i «BALL») -> imatge DFL -> (x, y) en m
    imatges: np.ndarray                                      # (n,) número d'imatge de DFL, en ordre
    temps: np.ndarray                                        # (n,) s
    veritat: np.ndarray                                      # (n,) la de sempre, com `dfl.veritat`


def tracking_dfl(cami: Path) -> TrackingDFL:
    """Les posicions en brut de DFL: cada persona i la pilota, amb l'hora i la possessió de cada imatge."""
    persones: dict[str, dict[int, tuple[float, float]]] = collections.defaultdict(dict)
    temps, codi = {}, {}
    persona = None
    with open(cami, encoding="utf-8") as f:
        for linia in f:
            if "<FrameSet" in linia:
                persona = "BALL" if "BALL" in linia else re.search(r'PersonId="([^"]+)"', linia).group(1)
                continue
            if persona is None or "<Frame " not in linia:
                continue
            m = _FRAME.search(linia)
            n = int(m.group(1))
            persones[persona][n] = (float(m.group(3)), float(m.group(4)))
            if persona == "BALL":
                temps[n] = datetime.fromisoformat(m.group(2)).timestamp()
                qui, viva = _POSSESSIO.search(linia).groups()
                codi[n] = pm.D if viva != "1" else {"1": pm.H, "2": pm.A}.get(qui, pm.X)
    imatges = np.array(sorted(temps))
    return TrackingDFL(dict(persones), imatges, np.array([temps[n] for n in imatges]),
                       np.array([codi[n] for n in imatges], dtype=np.int8))


def tocs_dfl(text: str, casa: str) -> list[Toc]:
    """Els tocs dels esdeveniments en brut de DFL: passades, altres tocs, parades, xuts, desviacions i el guanyador
    d'un duel quan toca la pilota. També dins d'una represa (la passada d'una falta o d'un córner)."""
    out = []
    for m in _ESDEVENIMENT.finditer(text):
        toc = _TOC.search(m.group(2))
        if toc is None:
            continue
        tipus, cos = toc.groups()
        if tipus == "TacklingGame":
            if not re.search(rf'WinnerResult="({"|".join(DUEL_AMB_TOC)})"', cos):
                continue
            jugador, equip = re.search(r'\bWinner="([^"]+)"', cos), re.search(r'\bWinnerTeam="([^"]+)"', cos)
        else:
            jugador, equip = re.search(r'\bPlayer="([^"]+)"', cos), re.search(r'\bTeam="([^"]+)"', cos)
        if jugador and equip:
            out.append(Toc(datetime.fromisoformat(m.group(1)).timestamp(), tipus, jugador.group(1),
                           pm.H if equip.group(1) == casa else pm.A))
    return out


def col_loca(tr: TrackingDFL, tocs: list[Toc]) -> list[tuple[int, int]]:
    """(fila, equip) de cada toc que es col·loca: la imatge on el jugador és més a prop de la pilota, de `ABANS` a
    `DESPRES` de l'hora de l'esdeveniment, si hi és a menys de `MAX_DISTANCIA_M`. En ordre."""
    pilota, out = tr.persones["BALL"], []
    for toc in tocs:
        k = int(np.searchsorted(tr.temps, toc.temps))
        if k < ABANS or k + DESPRES >= len(tr.imatges) or toc.jugador not in tr.persones:
            continue
        jugador = tr.persones[toc.jugador]
        distancies = [(float(np.hypot(jugador[n][0] - pilota[n][0], jugador[n][1] - pilota[n][1])), j)
                      for j in range(k - ABANS, k + DESPRES + 1)
                      if (n := int(tr.imatges[j])) in jugador and n in pilota]
        if distancies and min(distancies)[0] < MAX_DISTANCIA_M:
            out.append((min(distancies)[1], toc.equip))
    return sorted(out)


def _final(veritat: np.ndarray, k: int, equip: int, seguent: int | None, marge: int,
           max_rebot: int) -> tuple[int | None, str]:
    """Fins on és d'`equip` el toc de la fila `k` (exclosa), i quin cas és; None si no es toca."""
    for j in range(k, min(len(veritat), k + max_rebot)):
        if veritat[j] == equip:
            return (j, "tard") if j - k > marge else (None, "dins del marge")
        if veritat[j] in (pm.D, pm.X):
            return j, "fins a la morta"
        if seguent is not None and j >= seguent:
            return j, "rebot"
    return None, "sense final"


def de_toc(veritat: np.ndarray, tocs: list[tuple[int, int]], marge: int = MARGE,
           max_rebot: int = MAX_REBOT) -> tuple[np.ndarray, dict[str, int]]:
    """La veritat amb el canvi a cada toc de l'equip que no la té, i quants n'hi ha de cada cas. Només hi canvien
    imatges de l'altre equip: la D i la X, mai."""
    nova, compta = veritat.copy(), dict.fromkeys(CASOS, 0)
    for i, (k, equip) in enumerate(tocs):
        if veritat[k] not in (pm.H, pm.A) or veritat[k] == equip or nova[k] == equip:
            continue
        seguent = next((j for j, e in tocs[i + 1:] if e != equip and j > k), None)
        fi, cas = _final(veritat, k, equip, seguent, marge, max_rebot)
        compta[cas] += 1
        if fi is not None:
            nova[k:fi] = equip
    return nova, compta


def veritat_dfl(partit: str, de_sempre: np.ndarray) -> tuple[np.ndarray, dict[str, int]]:
    """La veritat de toc d'un partit de DFL. Comprova abans que les imatges i la veritat del fitxer en brut són les
    del banc, una a una."""
    meta = dfl.fitxer(fonts.DIR_IDSSE, f"DFL_02_01_matchinformation_*{partit}.xml")
    casa = next(re.search(r'TeamId="([^"]+)"', m.group(1)).group(1)
                for m in re.finditer(r"<Team ([^>]*)>", meta.read_text(encoding="utf-8")) if 'Role="home"' in m.group(1))
    tr = tracking_dfl(dfl.fitxer(fonts.DIR_IDSSE, f"DFL_04_03_positions_raw_observed_*{partit}.xml"))
    if not np.array_equal(tr.veritat, de_sempre):
        raise ValueError(f"{partit}: el fitxer en brut no dona la veritat del banc imatge per imatge")
    text = dfl.fitxer(fonts.DIR_IDSSE, f"DFL_03_02_events_raw_*{partit}.xml").read_text(encoding="utf-8")
    return de_toc(tr.veritat, col_loca(tr, tocs_dfl(text, casa)))


def veritat_metrica(num: int) -> np.ndarray:
    """Com `banc.metrica.llegeix`, amb la convenció de toc."""
    p = carrega_partit(num)
    y3 = etiquetes.deriva_etiquetes(p.events, p.frame, p.periode, toc=True).y3
    return np.where(y3 < 0, pm.X, y3).astype(np.int8)


def comprova(de_sempre: np.ndarray, nova: np.ndarray) -> None:
    if nova.shape != de_sempre.shape:
        raise ValueError("La veritat de toc no té la mida de la de sempre")
    for codi in (pm.D, pm.X):
        if not np.array_equal(nova == codi, de_sempre == codi):
            raise ValueError("La veritat de toc canvia la D o la X")


def empremta(veritat: np.ndarray) -> str:
    return hashlib.sha256(veritat.astype(np.int8).tobytes()).hexdigest()


def clau() -> str:
    h = hashlib.sha256()
    for modul in (etiquetes, dfl):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


CLAU = clau()


def veritat(nom: str) -> np.ndarray:
    """La veritat de toc d'un partit del banc, de la memòria cau si hi és amb aquest codi i aquesta veritat de
    sempre."""
    return _veritat_i_casos(nom)[0]


def _veritat_i_casos(nom: str) -> tuple[np.ndarray, dict[str, int]]:
    de_sempre = fonts.partit(nom).veritat
    cami = DIR_CAU / f"{nom}.npz"
    if cami.exists():
        with np.load(cami, allow_pickle=False) as desat:
            if str(desat["clau"]) == CLAU and str(desat["de_sempre"]) == empremta(de_sempre):
                return desat["veritat"].astype(np.int8), dict(zip(CASOS, desat["casos"].tolist()))
    font, quin = nom.split("-", 1)
    if font == "dfl":
        nova, casos = veritat_dfl(quin, de_sempre)
    elif font == "metrica":
        nova, casos = veritat_metrica(int(quin)), dict.fromkeys(CASOS, 0)
    else:
        raise KeyError(f"No hi ha veritat de toc per a {nom}")
    comprova(de_sempre, nova)
    DIR_CAU.mkdir(parents=True, exist_ok=True)
    temporal = cami.with_name(f"{cami.name}.part.npz")
    np.savez(temporal, clau=CLAU, de_sempre=empremta(de_sempre), veritat=nova.astype(np.int8),
             casos=np.array([casos[c] for c in CASOS], dtype=np.int64))
    temporal.replace(cami)
    return nova, casos


def partit(nom: str) -> PartitBanc:
    """El partit del banc amb la veritat de toc."""
    return replace(fonts.partit(nom), veritat=veritat(nom))


def resum(nom: str) -> dict:
    """Quant canvia la veritat d'un partit: possessions, imatges i l'spellF1 de la de sempre contra la de toc."""
    de_sempre = fonts.partit(nom)
    nova, casos = _veritat_i_casos(nom)
    trams = avalua.trams_valids(de_sempre)
    viu = np.isin(de_sempre.veritat, (pm.H, pm.A))
    durades = {}
    for quina, codis in (("sempre", de_sempre.veritat), ("toc", nova)):
        d = np.array([(b - a) / pm.FPS for a, b, _ in pm.possession_spells(codis, trams)])
        durades[quina] = (len(d), int((d < 1).sum()))
    return {"partit": nom, "possessions": durades["sempre"][0], "possessions_toc": durades["toc"][0],
            "curtes": durades["sempre"][1], "curtes_toc": durades["toc"][1],
            "canvia": float((de_sempre.veritat[viu] != nova[viu]).mean()),
            "spell_f1": pm.spell_scores(nova, de_sempre.veritat, trams)["mean_f1"], **casos}


def markdown(files: list[dict]) -> str:
    linies = ["# Banc obert · La veritat de toc (T3q)", "",
              "Generat amb `uv run python -I -m banc.veritat_toc`. Com es fa: la capçalera de `banc/veritat_toc.py` i",
              "`docs/pla-tocs.md`, «T3q». *spellF1*: el de la veritat de sempre, com si fos una predicció, contra la de",
              "toc (1: són iguals). *Canvia*: la part de les imatges en joc que canvien d'equip.", "",
              "| partit | possessions | de toc | de menys d'1 s | de toc | canvia | spellF1 | " + " | ".join(CASOS) + " |",
              "|---" * (7 + len(CASOS)) + "|"]
    for f in files:
        linies.append(f"| {f['partit']} | {f['possessions']} | {f['possessions_toc']} | {f['curtes']} | "
                      f"{f['curtes_toc']} | {100 * f['canvia']:.2f} % | {f['spell_f1']:.3f} | "
                      + " | ".join(str(f[c]) for c in CASOS) + " |")
    for font in ("dfl", "metrica"):
        seves = [f for f in files if f["partit"].startswith(font)]
        linies += ["", f"**{font}:** possessions {sum(f['possessions'] for f in seves)} → "
                   f"{sum(f['possessions_toc'] for f in seves)}; spellF1 de mitjana "
                   f"{np.mean([f['spell_f1'] for f in seves]):.3f}."]
    return "\n".join(linies + [""])


def main() -> None:
    from banc import veritat_toc as aquest       # pel nom del mòdul, perquè els processos fills el trobin

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=4)
    args = ap.parse_args()
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        files = list(feina.map(aquest.resum, fonts.NOMS))
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "veritat-toc.md").write_text(markdown(files))
    print((DIR_RESULTATS / "veritat-toc.md").read_text())


if __name__ == "__main__":
    main()
