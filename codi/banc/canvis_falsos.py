"""Els canvis falsos d'A xarxes, i el sostre de no fer-los (`docs/pla-tocs.md`, «La idea següent: els canvis
falsos»).

    cd codi && uv run python -I -m banc.canvis_falsos

Amb el que ha desat el banc de la T3p (les probabilitats d'A xarxes i la seva q) i el decodificador triat a cada partit
a la veritat de toc pel banc de la T3r. Es comprova que l'spellF1 de cada partit és el del banc. Al net, als quatre ×¼
i a «partit ×¼», a la veritat de toc:

1. **Les possessions inventades:** les predites d'un equip que la veritat no té a 1 s o menys. Quantes n'hi ha, de
   quina durada, i entre què són: entre dues de l'altre equip (*inserides*, un canvi fals d'anada i tornada) o al
   costat d'una aturada o de la vora del tram (l'equip, equivocat).
2. **El sostre de no fer-les:** A xarxes amb la veritat de toc a les inventades (totes, o les de menys de 5 s), i amb
   un vet: la q a 0,0001 a la possessió i a 6 imatges a cada banda, i tornar a decodificar (a totes, o a les
   inserides). I el que faria un verificador perfecte: cada inventada a l'altre equip (o, al costat d'una aturada,
   una aturada), i el cost d'equivocar-se: tantes bones com inventades, a l'altre equip.
3. **Com es distingeixen** de les bones: l'AUC de cada tret de la possessió, sense entrenar res (com més baix, més
   inventada): la durada, la confiança del segon en l'equip, la part amb la pilota vista i la q a l'inici.

Escriu `resultats/canvis-falsos.md`. Dades obertes, només per saber-ho.
"""

from __future__ import annotations

import itertools
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from banc import analisi_t3p as t3p
from banc import analisi_t3q as t3q
from banc import analisi_t3r as an
from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_partit as mp
from banc import sostre_curtes as sc
from banc import veritat_toc as vt
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ESCENARIS = t3q.ESCENARIS                           # el net, els quatre ×¼ i «partit ×¼»
BASE = sc.BASE                                      # A xarxes
TOL = an.TOL                                        # 1 s
CURTA = sc.CURTA                                    # 5 s
INSERIDA, AL_COSTAT = "inserida", "al costat d'una aturada"
VERITAT, VERITAT_CURTES = "veritat a les inventades", "veritat a les inventades de menys de 5 s"
VET, VET_INSERIDES = "vet a les inventades", "vet a les inserides"
REGLA = "l'altre equip a les inventades"
REGLA_D = "l'altre equip a les inserides i D a les altres"
BONES = "l'altre equip a tantes bones com inventades"
SOSTRES = (VERITAT, VERITAT_CURTES, VET, VET_INSERIDES, REGLA, REGLA_D, BONES)
LLAVOR = 0
TRETS = ("durada", "confiança", "vista", "q a l'inici")
ENTRA, SURT, A_DESTEMPS = "entra a una inventada", "surt d'una inventada", "a destemps"
Tram = tuple[int, int]


def inventada(toc: np.ndarray, a: int, b: int, k: int, tol: int = TOL) -> bool:
    """Si la veritat no té l'equip `k` enlloc de [a − `tol`, b + `tol`)."""
    return not bool(np.any(toc[max(a - tol, 0):b + tol] == k))


def vores(pred: np.ndarray, a: int, b: int, tram: Tram) -> str:
    """Entre dues possessions de l'altre equip, o al costat d'una aturada o de la vora del tram."""
    abans = pred[a - 1] if a > tram[0] else pm.X
    despres = pred[b] if b < tram[1] else pm.X
    return INSERIDA if abans == despres and abans in pm.POSSESSION_LABELS else AL_COSTAT


def veta(q: np.ndarray, trossos: list[tuple[int, int]], k: int = t3i.K) -> np.ndarray:
    """La q a `t3i.Q_MINIM` a cada tros [a, b) i a `k` imatges a cada banda: el decodificador no hi pot canviar
    d'equip."""
    out = q.copy()
    for a, b in trossos:
        out[max(a - k, 0):b + k] = t3i.Q_MINIM
    return out


def arregla(pred: np.ndarray, possessions: list[dict], al_costat: int | None = None) -> np.ndarray:
    """`pred`, amb cada possessió a l'altre equip; al costat d'una aturada, amb `al_costat` si no és None. És el que
    faria un verificador que les reconegués."""
    out = pred.copy()
    for f in possessions:
        altre = pm.A if f["k"] == pm.H else pm.H
        out[f["a"]:f["b"]] = al_costat if al_costat is not None and f["vores"] == AL_COSTAT else altre
    return out


def bones_com(possessions: list[dict], rng: np.random.Generator) -> list[dict]:
    """Per cada inventada, una possessió bona de la mateixa durada triada a l'atzar (sense repetir-ne cap; si se
    n'acaben, cap): les que un verificador equivocat arreglaria."""
    triades = []
    for tram in dict.fromkeys(f["tram"] for f in possessions):
        del_tram = [f for f in possessions if f["tram"] == tram]
        bones = [f for f in del_tram if not f["inventada"]]
        n = min(sum(f["inventada"] for f in del_tram), len(bones))
        triades += [bones[i] for i in sorted(rng.choice(len(bones), n, replace=False))]
    return triades


def trets(probes: np.ndarray, q: np.ndarray, vista: np.ndarray, a: int, b: int, k: int,
          finestra: int = t3i.K) -> dict[str, float]:
    """La durada, la confiança del segon en l'equip `k`, la part amb la pilota vista i la q més alta a `finestra`
    imatges o menys de l'inici."""
    return {"durada": b - a, "confiança": float(np.nanmean(probes[a:b, k])), "vista": float(vista[a:b].mean()),
            "q a l'inici": float(q[max(a - finestra, 0):a + finestra + 1].max())}


def mena(abans: dict, ara: dict) -> str:
    """D'on ve un canvi d'equip, de la possessió predita `abans` a la següent, `ara`: si entra a una inventada, si en
    surt, o si totes dues hi són a la veritat i el canvi és a destemps."""
    if ara["inventada"]:
        return ENTRA
    return SURT if abans["inventada"] else A_DESTEMPS


def desfasament(c: int, reals: np.ndarray) -> float:
    """Imatges des del canvi real més proper fins a `c` (positiu: `c` és tard)."""
    if len(reals) == 0:
        return np.nan
    return float(c - reals[np.argmin(np.abs(reals - c))])


def auc(possessions: pd.DataFrame, tret: str) -> float:
    """Com separa el tret les inventades de les altres, si com més baix, més inventada (0,5: gens)."""
    y = possessions["inventada"].to_numpy()
    if len(np.unique(y)) < 2:
        return np.nan
    return float(roc_auc_score(y, -possessions[tret].to_numpy(dtype=float)))


def tasca(nom_escenari: tuple[str, str]) -> dict[str, list[dict]]:
    nom, escenari = nom_escenari
    de_sempre = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    p_toc = replace(de_sempre, veritat=toc)
    trams = avalua.trams_valids(p_toc)
    vista = ~np.isnan(de_sempre.tracking.pilota[:, 0])
    probes, prior = mp.segon((nom, mp.SIS), entrena=False)
    proba = probes[escenari].astype(float)
    relativa = log_relativa(proba, prior)
    q = mp.q((nom, mp.SIS), entrena=False)[escenari].astype(float)
    w, lam, d_min = an.triades()[an.XARXES_TOC][nom]

    def decodifica(q_: np.ndarray) -> np.ndarray:
        return t3i.per_trams(relativa, q_, de_sempre.trams, w, lam, int(d_min))

    pred = decodifica(q)
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}
    possessions = []
    for tram in trams:
        for a, b, k in pm.possession_spells(pred, [tram]):
            possessions.append({**comu, "a": a, "b": b, "k": k, "tram": t3q.durada(b - a),
                                "inventada": inventada(toc, a, b, k), "vores": vores(pred, a, b, tram),
                                **trets(proba, q, vista, a, b, k)})
    reals, al_forat = t3i.canvis(toc, trams), sc.forats(vista)
    canvis = []
    for tram in trams:
        del_tram = [f for f in possessions if tram[0] <= f["a"] < tram[1]]
        for abans, ara in zip(del_tram, del_tram[1:]):
            if ara["k"] != abans["k"]:
                c = ara["a"]
                canvis.append({**comu, "fals": not bool(an.a_prop(np.array([c]), reals, TOL)[0]),
                               "mena": mena(abans, ara), "desfasament": desfasament(c, reals),
                               "al forat": bool(al_forat[c])})
    inventades = [(f["a"], f["b"], f["k"]) for f in possessions if f["inventada"]]
    inserides = [(f["a"], f["b"]) for f in possessions if f["inventada"] and f["vores"] == INSERIDA]

    def fila(sostre: str, prediccio: np.ndarray) -> dict:
        return {**comu, "sostre": sostre, "spell_f1": avalua.puntua(p_toc, prediccio)["spell_f1"]}

    files = [fila(BASE, pred), fila(VERITAT, sc.amb_la_veritat(pred, toc, inventades, False)),
             fila(VERITAT_CURTES, sc.amb_la_veritat(pred, toc, [p for p in inventades if p[1] - p[0] < CURTA],
                                                    False)),
             fila(VET, decodifica(veta(q, [(a, b) for a, b, _ in inventades]))),
             fila(VET_INSERIDES, decodifica(veta(q, inserides))),
             fila(REGLA, arregla(pred, [f for f in possessions if f["inventada"]])),
             fila(REGLA_D, arregla(pred, [f for f in possessions if f["inventada"]], pm.D)),
             fila(BONES, arregla(pred, bones_com(possessions, np.random.default_rng(LLAVOR))))]
    return {"files": files, "possessions": possessions, "canvis": canvis}


def taula_inventades(possessions: pd.DataFrame) -> pd.DataFrame:
    """Per escenari: quantes possessions predites hi ha, quantes són inventades, la part inventada per durada i entre
    què són les inventades."""
    g = possessions.groupby("escenari", sort=False)
    t = pd.DataFrame({"n predites": g.size(), "n inventades": g["inventada"].sum(), "part inventada":
                      g["inventada"].mean()})
    per_durada = possessions.groupby(["escenari", "tram"], sort=False)["inventada"].mean().unstack("tram")
    t = t.join(per_durada[[d for d in t3q.NOMS_DURADA if d in per_durada.columns]])
    on = possessions[possessions["inventada"]].groupby(["escenari", "vores"])["inventada"].size().unstack("vores")
    for vora in (INSERIDA, AL_COSTAT):
        t[f"n {vora}"] = on[vora] if vora in on.columns else 0
    return t.fillna(0)


def taula_falsos(canvis: pd.DataFrame) -> pd.DataFrame:
    """Per escenari: els canvis d'equip predits, quants són falsos (cap de real a 1 s o menys) i d'on vénen; dels que
    són a destemps, quants són tard, quants són als forats i quant de desfasats (la mediana, en segons)."""
    falsos = canvis[canvis["fals"]]
    destemps = falsos[falsos["mena"] == A_DESTEMPS]
    t = pd.DataFrame({"n canvis": canvis.groupby("escenari", sort=False).size(),
                      "n falsos": falsos.groupby("escenari", sort=False).size()})
    for m in (ENTRA, SURT, A_DESTEMPS):
        t[f"n {m}"] = falsos[falsos["mena"] == m].groupby("escenari").size()
    g = destemps.groupby("escenari")
    t["tard"] = g["desfasament"].apply(lambda d: float((d > 0).mean()))
    t["als forats"] = g["al forat"].mean()
    t["mediana (s)"] = g["desfasament"].apply(lambda d: float(np.median(np.abs(d))) / pm.FPS)
    return t.fillna(0)


def taula_auc(possessions: pd.DataFrame) -> pd.DataFrame:
    """Per escenari: l'AUC de cada tret, i quantes possessions predites hi ha."""
    files = {}
    for escenari, de_l_escenari in possessions.groupby("escenari", sort=False):
        files[escenari] = {"n predites": len(de_l_escenari), **{t: auc(de_l_escenari, t) for t in TRETS}}
    t = pd.DataFrame.from_dict(files, orient="index")
    t.index.name = "escenari"
    return t


def comprova(files: pd.DataFrame) -> None:
    """A xarxes, amb el decodificador triat a la veritat de toc, dona l'spellF1 del banc de la T3r."""
    an.comprova(files, (an.XARXES,))


def main() -> None:
    with ProcessPoolExecutor(max_workers=10) as feina:
        tasques = list(feina.map(tasca, itertools.product(fonts.NOMS, ESCENARIS)))
    files, possessions, canvis = (pd.DataFrame([f for t in tasques for f in t[k]])
                                  for k in ("files", "possessions", "canvis"))
    comprova(files)
    sortida = [
        "# Banc obert · Els canvis falsos d'A xarxes", "",
        "Generat amb `uv run python -I -m banc.canvis_falsos`, amb el que han desat `banc.model_a_partit` i",
        f"`banc.model_a_q`. Dades obertes. Només per saber-ho. A la veritat de toc, amb el decodificador d'{BASE}",
        "triat a cada partit a la veritat de toc (✓ comprovat: el mateix spellF1 que el banc de la T3r).", "",
        "## Les possessions inventades", "",
        f"Una possessió predita és *inventada* si la veritat no té el seu equip enlloc a {TOL} imatges (1 s) o menys.",
        f"Per durada, la part de les predites que són inventades. *{INSERIDA}:* entre dues de l'altre equip (un",
        f"canvi fals d'anada i tornada); *{AL_COSTAT}:* tocant una aturada o la vora del tram (l'equip, equivocat).",
        "", t3p.md(taula_inventades(possessions)), "",
        "## D'on vénen els canvis falsos", "",
        f"Els canvis d'equip predits (deu partits) i els *falsos*, sense cap canvi real a {TOL} imatges (1 s) o menys:",
        f"*{ENTRA}* o *{SURT}*, o *{A_DESTEMPS}* (les dues possessions hi són a la veritat, però el canvi és a més",
        "d'1 s del real). Dels que són a destemps: la part que és tard, la part als forats i la mediana del",
        "desfasament.", "", t3p.md(taula_falsos(canvis)), "",
        "## El sostre de no fer-les", "",
        f"spellF1 d'{BASE} (mitjana dels deu partits) i quant hi guanya. *{VERITAT}:* la veritat de toc a cada",
        f"inventada. *{VET}:* la q a {t3i.Q_MINIM:g} a la inventada i a {t3i.K} imatges a cada banda, i tornar a",
        "decodificar: el que faria un model que les reconegués i no deixés canviar d'equip. Al costat d'una aturada,",
        "el vet no hi fa res: l'equip no hi entra canviant des de l'altre.", "",
        f"*{REGLA}:* el que faria un verificador perfecte: cada inventada, sencera, a l'altre equip (l'inserida",
        f"s'ajunta amb les del costat). *{REGLA_D}:* al costat d'una aturada, una aturada. *{BONES}:* el cost",
        "d'equivocar-se: tantes possessions bones com inventades, de la mateixa durada i triades a l'atzar, a l'altre",
        "equip.", "",
        t3p.md(sc.taula_guany(files, SOSTRES)), "",
        "## Com es distingeixen de les bones", "",
        "L'AUC de cada tret de la possessió predita per separar les inventades de les altres, sense entrenar res: 1,",
        "del tot; 0,5, gens. Com més baix el tret, més inventada. *confiança:* la probabilitat mitjana que el segon",
        f"dona a l'equip de la possessió; *vista:* la part amb la pilota vista; *q a l'inici:* la q més alta a {t3i.K}",
        "imatges o menys de l'inici.", "",
        t3p.md(taula_auc(possessions)), "",
        "## Passaria el criteri als ×¼?", "",
        f"El guany de mitjana · en quants partits guanya · ✓ si passaria (> {t3.SOROLL}, l'interval del 95 % per",
        f"sobre de zero i {t3.GUANYA_MINIM} partits de 10 o més).", "",
        *sc.taula_criteri(files, SOSTRES), "",
    ]
    an.DIR_RESULTATS.mkdir(exist_ok=True)
    (an.DIR_RESULTATS / "canvis-falsos.md").write_text("\n".join(sortida))
    print("\n".join(sortida))


if __name__ == "__main__":
    main()
