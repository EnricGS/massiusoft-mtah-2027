"""El sostre de les possessions curtes: quant guanyaria A xarxes si encertés les possessions de toc reals d'una
durada, abans de triar la idea següent (`docs/pla-tocs.md`, «El sostre de les possessions curtes»). Només per
saber-ho.

    cd codi && uv run python -I -m banc.sostre_curtes

Amb les probabilitats i les q que ha desat `banc.model_a_partit` (A xarxes) i el decodificador triat a cada partit
(`resultats/model-a-toc.json`), tot puntuat a la veritat de toc. Cada sostre agafa la predicció d'A xarxes i hi
posa la veritat de toc a unes possessions reals, sense tocar res més:

1. **Per durada:** les d'un tram. Les de menys de 0,48 s, el decodificador triat no les pot fer.
2. **Les de menys de 5 s:** totes, les de fins a 1 o 2 s, les que el decodificador pot fer (0,48-5 s), segons si
   la pilota es veu (a la meitat de la possessió o més, a l'escenari) i *només l'equip* (on A xarxes dona l'altre
   equip; on dona la D, la D).
3. **D'on ve el marge:** *les vores de la veritat, l'equip d'A xarxes* (a cada possessió real de menys de 5 s,
   l'equip que A xarxes hi dona sumant totes les seves imatges: si l'encerta, el que falta és trobar on comença i on
   acaba) i *la q perfecta* (el decodificador sap on canvia l'equip: 0,99 a 6 imatges o menys d'un canvi de la
   veritat, i 0,0001 a la resta, com l'oracle de la T3i) i *les vores de la veritat, l'equip del toc* (l'equip del
   jugador que passa més a prop de la pilota a 3 imatges o menys de l'inici; sense pilota, el vot). I, per a cada
   possessió real, si el vot d'A xarxes i el toc hi encerten l'equip. La q perfecta, també partida: *on es veu la
   pilota* (perfecta fora dels forats, i la d'A xarxes als forats) i *als forats* (al revés). Un forat és un tros
   sense pilota a l'escenari, amb 6 imatges més a cada banda (com a «Per què la T3j no hi arriba»). I *la D
   perfecta*: el decodificador sap on és la pilota morta, i l'equip i la q són els d'A xarxes.
4. **El criteri, als ×¼:** si el sostre passaria (+0,04 de mitjana, l'interval del 95 % per sobre de zero i 8
   partits de 10). Si el sostre no hi passa, cap idea que només millori aquestes possessions no hi pot passar.

Escriu `resultats/sostre-curtes.md`. Tot són dades obertes.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

from banc import analisi_t3p as t3p
from banc import analisi_t3q as t3q
from banc import avalua, fonts, model_a
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_partit as mp
from banc import model_a_toc as mt
from banc import veritat_toc as vt
from cadena import model
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ESCENARIS = t3q.ESCENARIS
QUARTS = t3.QUARTS
BASE = mt.XARXES
TOTES = "totes"
CURTA = 5 * pm.FPS                               # una possessió curta: de menys de 5 s
MEITAT = 0.5                                     # la pilota «es veu» si es veu a la meitat de la possessió o més
VORES = "<5 s: les vores de la veritat, l'equip d'A xarxes"
TOC = "<5 s: les vores de la veritat, l'equip del toc"
Q_PERFECTA = "la q perfecta"
Q_AMB_PILOTA = "la q perfecta on es veu la pilota"
Q_ALS_FORATS = "la q perfecta als forats"
D_PERFECTA = "la D perfecta"
ON = (VORES, TOC, Q_PERFECTA, Q_AMB_PILOTA, Q_ALS_FORATS, D_PERFECTA)      # d'on ve el marge
SEGUR = 30.0                                     # la D perfecta: la probabilitat relativa de la D, ±SEGUR
A_PROP_DEL_TOC = 3                               # imatges a banda i banda de l'inici d'una possessió
Q_CANVI = 0.99                                   # la q perfecta a prop d'un canvi (com l'oracle de la T3i)
Possessio = tuple[int, int, int]


@dataclass(frozen=True)
class Sostre:
    nom: str
    tria: Callable[[int, float], bool]           # (imatges, part amb la pilota vista) → si s'hi posa la veritat
    nomes_equip: bool = False                    # només on el model dona l'altre equip: on dona la D, la D


def entre(baix: float, alt: float) -> Callable[[int, float], bool]:
    return lambda imatges, vista: baix <= imatges < alt


PER_DURADA = (*(Sostre(nom, entre(baix, alt)) for nom, baix, alt in zip(t3q.NOMS_DURADA, t3q.LIMITS, t3q.LIMITS[1:])),
              Sostre(TOTES, lambda imatges, vista: True))
CURTES = (
    Sostre("<1 s", entre(0, pm.FPS)),
    Sostre("<2 s", entre(0, 2 * pm.FPS)),
    Sostre("<5 s", entre(0, CURTA)),
    Sostre("0,48-5 s", entre(t3q.D_MIN, CURTA)),
    Sostre("<5 s, pilota vista", lambda imatges, vista: imatges < CURTA and vista >= MEITAT),
    Sostre("<5 s, pilota amagada", lambda imatges, vista: imatges < CURTA and vista < MEITAT),
    Sostre("<5 s, només l'equip", entre(0, CURTA), nomes_equip=True),
)
SOSTRES = (*PER_DURADA, *CURTES)


def noms(sostres: tuple[Sostre, ...]) -> tuple[str, ...]:
    return tuple(s.nom for s in sostres)


def part_vista(vista: np.ndarray, a: int, b: int) -> float:
    return float(vista[a:b].mean())


def triades(possessions: list[Possessio], sostre: Sostre, vista: np.ndarray) -> list[Possessio]:
    """Les possessions reals on el sostre posa la veritat."""
    return [(a, b, e) for a, b, e in possessions if sostre.tria(b - a, part_vista(vista, a, b))]


def amb_la_veritat(pred: np.ndarray, toc: np.ndarray, possessions: list[Possessio], nomes_equip: bool) -> np.ndarray:
    """`pred`, amb les possessions posades com la veritat de toc (si `nomes_equip`, només on dona un equip)."""
    out = pred.copy()
    for a, b, _ in possessions:
        canvia = np.isin(out[a:b], pm.POSSESSION_LABELS) if nomes_equip else np.ones(b - a, dtype=bool)
        out[a:b][canvia] = toc[a:b][canvia]
    return out


def vot(relativa: np.ndarray, a: int, b: int) -> int:
    """L'equip que A xarxes dona a la possessió [a, b): el de més probabilitat relativa, sumada a totes les imatges."""
    suma = np.nansum(relativa[a:b, :2], axis=0)
    return int(model.CLASSES[int(np.argmax(suma))])


def amb_les_vores(pred: np.ndarray, relativa: np.ndarray, possessions: list[Possessio]) -> np.ndarray:
    """`pred`, amb cada possessió posada sencera amb el vot d'A xarxes."""
    out = pred.copy()
    for a, b, _ in possessions:
        out[a:b] = vot(relativa, a, b)
    return out


def distancies(t) -> tuple[np.ndarray, np.ndarray]:
    """A cada imatge, la distància (m) del jugador d'H i del d'A més propers a la pilota; inf sense pilota."""
    escala = np.asarray(t.camp_m, float)
    pilota = t.pilota * escala

    def mes_proper(jugadors: np.ndarray) -> np.ndarray:
        d = np.linalg.norm(jugadors * escala - pilota[:, None, :], axis=2)
        return np.where(np.isnan(d), np.inf, d).min(axis=1)

    return mes_proper(t.casa), mes_proper(t.fora)


def del_toc(d_h: np.ndarray, d_a: np.ndarray, a: int, k: int = A_PROP_DEL_TOC) -> int | None:
    """L'equip del jugador que passa més a prop de la pilota a `k` imatges o menys de `a`; None si no s'hi veu."""
    finestra = slice(max(a - k, 0), a + k + 1)
    h, a_ = d_h[finestra].min(), d_a[finestra].min()
    if not np.isfinite(min(h, a_)):
        return None
    return pm.H if h <= a_ else pm.A


def amb_el_toc(pred: np.ndarray, relativa: np.ndarray, d_h: np.ndarray, d_a: np.ndarray,
               possessions: list[Possessio]) -> np.ndarray:
    """`pred`, amb cada possessió posada sencera amb l'equip del toc de l'inici (sense pilota, el vot)."""
    out = pred.copy()
    for a, b, _ in possessions:
        equip = del_toc(d_h, d_a, a)
        out[a:b] = vot(relativa, a, b) if equip is None else equip
    return out


def q_perfecta(toc: np.ndarray, trams: list[tuple[int, int]]) -> np.ndarray:
    return np.where(t3i.objectiu(toc, trams), Q_CANVI, t3i.Q_MINIM)


def amb_la_d(relativa: np.ndarray, toc: np.ndarray) -> np.ndarray:
    """La probabilitat relativa amb la D perfecta: segura on la veritat és D, impossible a la resta."""
    out = relativa.copy()
    d = toc == pm.D
    out[:, 2] = np.where(d, SEGUR, -SEGUR)
    out[d, :2] = -SEGUR
    return out


def forats(vista: np.ndarray, k: int = t3i.K) -> np.ndarray:
    """Les imatges sense pilota, i les que en són a `k` o menys."""
    sense = (~vista).astype(float)
    return np.convolve(sense, np.ones(2 * k + 1), mode="same") > 0


def criteri(dif: np.ndarray, font: np.ndarray) -> dict:
    """El criteri dels ×¼: guanya de mitjana més que el soroll, l'interval per sobre de zero i prou partits."""
    baix, _ = model_a.interval(dif, font)
    guanya = int((dif > 0).sum())
    return {"guany": float(dif.mean()), "baix": baix, "guanya": guanya, "partits": len(dif),
            "passa": bool(dif.mean() > t3.SOROLL and baix > 0 and guanya >= t3.GUANYA_MINIM)}


def tasca(nom_escenari: tuple[str, str]) -> dict[str, list[dict]]:
    nom, escenari = nom_escenari
    de_sempre = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    p_toc = replace(de_sempre, veritat=toc)
    trams = avalua.trams_valids(p_toc)
    reals = pm.possession_spells(toc, trams)
    vista = ~np.isnan(de_sempre.tracking.pilota[:, 0])
    probes, prior, q = mt.de_qui(BASE, nom)
    w, lam, d_min = t3q.triades()[BASE][nom]
    relativa = log_relativa(probes[escenari].astype(float), prior)
    pred = t3i.per_trams(relativa, q[escenari].astype(float), de_sempre.trams, w, lam, int(d_min))
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}

    def fila(sostre: str, possessions: int, prediccio: np.ndarray) -> dict:
        return {**comu, "sostre": sostre, "possessions": possessions,
                "spell_f1": avalua.puntua(p_toc, prediccio)["spell_f1"]}

    files = [{**fila(BASE, 0, pred), "w": w, "lam": lam, "d_min": d_min}]
    for s in SOSTRES:
        tria = triades(reals, s, vista)
        files.append(fila(s.nom, len(tria), amb_la_veritat(pred, toc, tria, s.nomes_equip)))
    curtes = [p for p in reals if p[1] - p[0] < CURTA]
    files.append(fila(VORES, len(curtes), amb_les_vores(pred, relativa, curtes)))
    d_h, d_a = distancies(de_sempre.tracking)
    files.append(fila(TOC, len(curtes), amb_el_toc(pred, relativa, d_h, d_a, curtes)))
    q_apresa, q_bona, al_forat = q[escenari].astype(float), q_perfecta(toc, trams), forats(vista)
    for nom_q, q_ in ((Q_PERFECTA, q_bona), (Q_AMB_PILOTA, np.where(al_forat, q_apresa, q_bona)),
                      (Q_ALS_FORATS, np.where(al_forat, q_bona, q_apresa))):
        files.append(fila(nom_q, 0, t3i.per_trams(relativa, q_, de_sempre.trams, w, lam, int(d_min))))
    files.append(fila(D_PERFECTA, 0, t3i.per_trams(amb_la_d(relativa, toc), q_apresa, de_sempre.trams, w, lam,
                                                    int(d_min))))
    vots = []
    for a, b, e in reals:
        toc_ = del_toc(d_h, d_a, a)
        vots.append({**comu, "durada": t3q.durada(b - a), "pilota": part_vista(vista, a, b) >= MEITAT,
                     "vot": vot(relativa, a, b) == e, "toc": np.nan if toc_ is None else float(toc_ == e)})
    return {"files": files, "vots": vots}


def per_partit(files: pd.DataFrame, escenari: str) -> pd.DataFrame:
    """L'spellF1 de cada partit (files) amb cada sostre (columnes), en un escenari."""
    return files[files["escenari"] == escenari].pivot_table(index="partit", columns="sostre", values="spell_f1")


def taula_guany(files: pd.DataFrame, noms_: tuple[str, ...]) -> pd.DataFrame:
    """Per escenari: l'spellF1 d'A xarxes i quant hi guanya cada sostre (mitjana dels partits)."""
    t = files.groupby(["escenari", "sostre"])["spell_f1"].mean().unstack("sostre")
    guany = t[list(noms_)].sub(t[BASE], axis=0)
    return t3q.ordena(pd.concat([t[BASE], guany], axis=1))


def taula_criteri(files: pd.DataFrame, noms_: tuple[str, ...]) -> list[str]:
    """Per sostre i escenari ×¼: el guany, en quants partits guanya i si passaria el criteri."""
    font = files.groupby("partit")["font"].first()
    linies = ["| sostre | " + " | ".join(QUARTS) + " |", "|---" * (1 + len(QUARTS)) + "|"]
    for nom in noms_:
        celles = []
        for escenari in QUARTS:
            t = per_partit(files, escenari)
            c = criteri((t[nom] - t[BASE]).to_numpy(), font.loc[t.index].to_numpy())
            celles.append(f"{c['guany']:+.3f} · {c['guanya']}/{c['partits']} {'✓' if c['passa'] else '✗'}")
        linies.append(f"| {nom} | " + " | ".join(celles) + " |")
    return linies


def taula_quantes(files: pd.DataFrame, noms_: tuple[str, ...]) -> pd.DataFrame:
    """Per escenari: quantes possessions reals tria cada sostre (els deu partits)."""
    t = files.groupby(["escenari", "sostre"])["possessions"].sum().unstack("sostre")
    return t3q.ordena(t[list(noms_)].add_prefix("n "))


def taula_vots(vots: pd.DataFrame, que: str) -> pd.DataFrame:
    """Per escenari i durada: la part de les possessions reals on `que` (el vot o el toc) encerta l'equip, segons si
    la pilota es veu (n: on diu alguna cosa)."""
    g = vots.groupby(["escenari", "durada", "pilota"])[que].agg(["mean", "count"]).unstack("pilota")
    g = g.reindex(columns=pd.MultiIndex.from_product([["mean", "count"], [True, False]]))
    noms_pilota = {True: "pilota vista", False: "pilota amagada"}
    t = g["mean"].rename(columns=noms_pilota).join(g["count"].rename(columns=noms_pilota).add_prefix("n "))
    return t3q.ordena(t)


def main() -> None:
    with ProcessPoolExecutor(max_workers=10) as feina:
        tasques = list(feina.map(tasca, itertools.product(fonts.NOMS, ESCENARIS)))
    files, vots = (pd.DataFrame([f for t in tasques for f in t[k]]) for k in ("files", "vots"))
    t3q.comprova(files[files["sostre"] == BASE].assign(metode=BASE))
    sortida = [
        "## Quantes possessions reals hi ha", "",
        "A la veritat de toc, els deu partits. La pilota «es veu» si es veu a la meitat de la possessió o més.", "",
        t3p.md(taula_quantes(files, noms((*PER_DURADA, *CURTES[4:6])))), "",
        "## El sostre per durada", "",
        f"spellF1 d'{BASE} a la veritat de toc (mitjana dels deu partits), i quant hi guanya si encerta les",
        "possessions reals de cada tram (totes les imatges, posades com la veritat de toc).", "",
        t3p.md(taula_guany(files, noms(PER_DURADA))), "",
        "## El sostre de les possessions de menys de 5 s", "",
        "*0,48-5 s:* les que el decodificador triat pot fer. *Només l'equip:* on A xarxes dona l'altre equip; on",
        "dona la D, la D.", "",
        t3p.md(taula_guany(files, noms(CURTES))), "",
        "## D'on ve el marge", "",
        "*Les vores de la veritat, l'equip d'A xarxes:* a cada possessió real de menys de 5 s, l'equip que A xarxes hi",
        "dona sumant la probabilitat relativa de totes les seves imatges. *La q perfecta:* el decodificador sap on",
        "canvia l'equip (0,99 a 6 imatges o menys d'un canvi de la veritat, 0,0001 a la resta), amb les probabilitats",
        "d'A xarxes; *on es veu la pilota*, perfecta fora dels forats (els trossos sense pilota, amb 6 imatges més a",
        "cada banda) i la d'A xarxes als forats; *als forats*, al revés. *La D perfecta:* el decodificador sap on és",
        "la pilota morta; l'equip i la q, els d'A xarxes.", "",
        t3p.md(taula_guany(files, ON)), "",
        "## El vot d'A xarxes a cada possessió real", "",
        "La part de les possessions reals on l'equip que A xarxes hi dona (sumant totes les seves imatges) és el bo.", "",
        t3p.md(taula_vots(vots, "vot")), "",
        "## El toc de l'inici, a cada possessió real", "",
        f"La part de les possessions reals on el jugador que passa més a prop de la pilota a {A_PROP_DEL_TOC} imatges o",
        "menys de l'inici és de l'equip bo (*n*: les que hi tenen la pilota).", "",
        t3p.md(taula_vots(vots, "toc")), "",
        "## Passaria el criteri als ×¼?", "",
        f"El guany de mitjana · en quants partits guanya · ✓ si passaria (> {t3.SOROLL}, l'interval del 95 % per",
        f"sobre de zero i {t3.GUANYA_MINIM} partits de 10 o més).", "",
        *taula_criteri(files, (*noms(SOSTRES), *ON)), "",
    ]
    cap = ["# Banc obert · El sostre de les possessions curtes", "",
           "Generat amb `uv run python -I -m banc.sostre_curtes`, amb el que ha desat `banc.model_a_partit`. Dades",
           f"obertes. Només per saber-ho. Les prediccions d'{BASE} són les del banc de la T3q (✓ comprovat: el mateix",
           "spellF1 a cada partit).", ""]
    (mt.DIR_RESULTATS / "sostre-curtes.md").write_text("\n".join(cap + sortida))
    print("\n".join(sortida))


if __name__ == "__main__":
    main()
