"""On falla A pilota morta (T3ah), abans de triar el pas següent (`docs/pla-tocs.md`, «On falla A pilota morta»). Només
per saber-ho.

    cd codi && uv run python -I -m banc.on_falla [--processos 10]

A pilota morta tal com la prova el banc de la T3ah: amb el nivell mitjà de les etiquetes, les llavors de provar, i els
paràmetres i el decodificador que hi va triar cada partit. Es comprova que l'spellF1 de cada partit i escenari és el del
banc de la T3ah. Als quatre ×¼, a «partit ×¼», al net i a curts, a la veritat de toc, amb les abstencions omplertes
com a la mètrica:

1. **Les possessions de la veritat** (les d'un equip), aparellades com la mètrica, amb una IoU de 0,5 (`aparella`): si
   s'encerta, i si no, per què (`causes`). O no hi és, perquè la predicció hi dona l'altre equip (engolida entre dues
   de l'altre equip, o no) o la D; o hi és, però trencada en més d'una, ajuntada amb una altra del mateix equip (per
   sobre de l'altre equip o de la D), o amb les vores lluny. També quant dura, i si la pilota es veu a `K` imatges o
   menys del seu inici, el toc que la comença.
2. **Les possessions predites que sobren** (`sobrants`): un tros d'una possessió de la veritat del mateix equip, o a la
   D o a l'altre equip de la veritat.
3. **Les engolides i les encertades de menys de 5 s: les veu el model?** A quina part de les imatges la probabilitat
   relativa que rep el decodificador dona més a l'equip de la veritat que a l'altre (`la_veu`), la q més alta a `K`
   imatges o menys de l'inici, i si a l'inici hi ha un toc a la vista de l'equip de la veritat (`toc_a_la_vista`, fet
   a mà, sense aprendre res). També quants tocs a la vista de l'altre equip hi ha dins les possessions de 10 s o més,
   lluny de les vores: les falses alarmes.
4. **Els sostres:** A pilota morta amb la veritat a les possessions de cada causa (la possessió sencera i les predites
   del mateix equip que la toquen), a les que sobren de cada mena, a les perdudes de cada durada, a les perdudes amb
   l'inici amb pilota o sense, i a les engolides amb el toc a la vista o amb pilota a l'inici. La mitjana dels deu
   partits del que hi guanya l'spellF1.

Escriu `resultats/on-falla.json` i `.md`. Tot són dades obertes.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace

import numpy as np
import pandas as pd

from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_etiquetes_decodificador as med
from banc import model_neteja_aire as mna
from banc import model_pilota_morta as mpm
from banc import model_pilotes_aturades as mpa
from banc import model_vores as mv
from banc import veritat_toc as vt
from cadena import pilota_morta as pmo
from cadena.llegeix import Tracking
from possessio.oficial import possession_metrics as pm

IOU = pm.SPELL_IOU_HEADLINE
K = t3i.K
ALTRE = {pm.H: pm.A, pm.A: pm.H}
AJUNTADA_ALTRE, AJUNTADA_D = "ajuntada, per sobre de l'altre equip", "ajuntada, per sobre de la D"
CAUSES = ("encertada", "engolida", "l'altre equip", "la D", "trencada", AJUNTADA_ALTRE, AJUNTADA_D, "les vores")
ON = ("un tros", "a la D", "a l'altre equip")
DURADES = (("menys de 2 s", 2.0), ("de 2 a 5 s", 5.0), ("de 5 a 10 s", 10.0), ("10 s o més", np.inf))
QUARTS_T3, PARTIT = med.QUARTS_T3, med.PARTIT
ESCENARIS = (*QUARTS_T3, PARTIT, "net", "curts")
CANVI_MS, A_TOCAR_M, MIG = 3.0, 1.5, 3            # el toc a la vista
LLARGA, LLUNY_DE_LES_VORES = 10 * pm.FPS, pm.FPS   # on es compten les falses alarmes
A_PM, A_EQUIPS, XARXES_TOC = mpm.A_PM, med.A_EQUIPS, med.XARXES_TOC
MITJA, PROVA, TOC = med.MITJA, med.PROVA, med.TOC
CRITERI = 0.04
DIR_RESULTATS = t3.DIR_RESULTATS


def durada(segons: float) -> str:
    return next(nom for nom, fins in DURADES if segons < fins)


def aparella(solapa: list[tuple[float, int, int]], n_gt: int, n_pred: int,
             llindar: float) -> tuple[np.ndarray, np.ndarray]:
    """Les possessions de la veritat i les predites aparellades, com `pm.matched_gt_flags`, però de totes dues bandes."""
    de_veritat, predites = np.zeros(n_gt, dtype=bool), np.zeros(n_pred, dtype=bool)
    for iou, i, j in solapa:
        if iou < llindar:
            break
        if de_veritat[i] or predites[j]:
            continue
        de_veritat[i] = predites[j] = True
    return de_veritat, predites


def _possessions(toc: np.ndarray, pred: np.ndarray, trams: list[tuple[int, int]]) -> tuple:
    gt, pr = pm.possession_spells(toc, trams), pm.possession_spells(pred, trams)
    de_veritat, predites = aparella(pm.spell_overlaps(gt, pr), len(gt), len(pr), IOU)
    return np.array(gt, dtype=np.int64).reshape(-1, 3), np.array(pr, dtype=np.int64).reshape(-1, 3), de_veritat, predites


def _toquen(a: int, b: int, k: int, possessions: np.ndarray) -> np.ndarray:
    """Les possessions de l'equip `k` que toquen [a, b)."""
    return possessions[(possessions[:, 2] == k) & (possessions[:, 0] < b) & (a < possessions[:, 1])]


def causes(toc: np.ndarray, pred: np.ndarray, trams: list[tuple[int, int]],
           vista: np.ndarray | None = None) -> list[dict]:
    """Una fila per possessió de la veritat: l'equip, quant dura, la causa (`CAUSES`), si la pilota es veu a prop del
    seu inici, i les imatges que la deixarien perfecta (`de`, `fins`: ella i les predites del mateix equip que la
    toquen). `pred`, amb les abstencions omplertes. «Engolida»: una sola possessió predita de l'altre equip la cobreix
    sencera i toca dues possessions o més d'aquest equip a la veritat (les d'abans i d'després). «Ajuntada»: la toca una
    sola possessió predita, que també en toca una altra del mateix equip, per sobre de l'altre equip si entremig la
    veritat hi té l'altre equip, o si no, per sobre de la D."""
    gt, pr, de_veritat, _ = _possessions(toc, pred, trams)
    files = []
    for (a, b, k), encertada in zip(gt.tolist(), de_veritat):
        toquen = _toquen(a, b, k, pr)
        if encertada:
            causa = "encertada"
        elif not len(toquen):
            tros, altre = pred[a:b], _toquen(a, b, ALTRE[k], pr)
            if (len(altre) == 1 and altre[0, 0] <= a and b <= altre[0, 1]
                    and len(_toquen(int(altre[0, 0]), int(altre[0, 1]), ALTRE[k], gt)) > 1):
                causa = "engolida"
            else:
                causa = "l'altre equip" if (tros == ALTRE[k]).sum() >= (tros == pm.D).sum() else "la D"
        elif len(toquen) > 1:
            causa = "trencada"
        elif len(_toquen(c := int(toquen[0, 0]), d := int(toquen[0, 1]), k, gt)) > 1:
            causa = AJUNTADA_ALTRE if (toc[c:d] == ALTRE[k]).any() else AJUNTADA_D
        else:
            causa = "les vores"
        files.append({"inici": a, "final": b, "equip": k, "durada_s": (b - a) / pm.FPS, "causa": causa,
                      "de": int(min(a, *toquen[:, 0])) if len(toquen) else a,
                      "fins": int(max(b, *toquen[:, 1])) if len(toquen) else b,
                      "inici_vist": None if vista is None else bool(vista[max(0, a - K):a + K + 1].any())})
    return files


def sobrants(toc: np.ndarray, pred: np.ndarray, trams: list[tuple[int, int]]) -> list[dict]:
    """Una fila per possessió predita que no s'aparella: l'equip, quant dura i on és (`ON`): un tros si la meitat o més
    és d'una possessió del mateix equip a la veritat, i si no, a la D o a l'altre equip, on n'hi ha més."""
    _, pr, _, predites = _possessions(toc, pred, trams)
    files = []
    for (a, b, k), aparellada in zip(pr.tolist(), predites):
        if aparellada:
            continue
        tros = toc[a:b]
        mateix, d, altre = (tros == k).sum(), (tros == pm.D).sum(), (tros == ALTRE[k]).sum()
        on = "un tros" if 2 * mateix >= len(tros) else "a la D" if d >= altre else "a l'altre equip"
        files.append({"inici": a, "final": b, "equip": k, "durada_s": (b - a) / pm.FPS, "on": on, "de": a, "fins": b})
    return files


def _mes_a_prop(jugadors: np.ndarray, pilota: np.ndarray) -> np.ndarray:
    d = np.linalg.norm(jugadors - pilota[:, None, :], axis=2)
    return np.where(np.isnan(d), np.inf, d).min(axis=1)


def toc_a_la_vista(t: Tracking) -> np.ndarray:
    """(n, 2) booleà, de l'H i de l'A: la velocitat de la pilota canvia `CANVI_MS` o més entre `MIG` imatges abans i
    `MIG` després, i el jugador de l'equip més a prop de la pilota hi és a `A_TOCAR_M` o menys, i més a prop que tots
    els de l'altre. On no es veu la pilota, mai."""
    camp = np.asarray(t.camp_m, float)
    pilota = t.pilota * camp
    v = np.full_like(pilota, np.nan)
    v[1:-1] = (pilota[2:] - pilota[:-2]) / 2 * pm.FPS
    canvi = np.full(len(pilota), np.nan)
    canvi[MIG:-MIG] = np.linalg.norm(v[2 * MIG:] - v[:-2 * MIG], axis=1)
    dist = np.stack([_mes_a_prop(t.casa * camp, pilota), _mes_a_prop(t.fora * camp, pilota)], axis=1)
    brusc = np.nan_to_num(canvi, nan=0.0) >= CANVI_MS
    return np.stack([brusc & (dist[:, k] <= A_TOCAR_M) & (dist[:, k] < dist[:, ALTRE[k]]) for k in (pm.H, pm.A)],
                    axis=1)


def la_veu(relativa: np.ndarray, a: int, b: int, k: int) -> float:
    """La part de les imatges de [a, b) on la probabilitat relativa dona més a l'equip `k` que a l'altre."""
    return float((relativa[a:b, k] > relativa[a:b, ALTRE[k]]).mean())


def falses_alarmes(toc: np.ndarray, trams: list[tuple[int, int]], toca: np.ndarray) -> tuple[int, int]:
    """Els tocs a la vista de l'altre equip dins de les possessions de la veritat de `LLARGA` imatges o més, a més de
    `LLUNY_DE_LES_VORES` de les vores, i quantes imatges s'hi han mirat."""
    alarmes, imatges = 0, 0
    for a, b, k in pm.possession_spells(toc, trams):
        if b - a >= LLARGA:
            alarmes += int(toca[a + LLUNY_DE_LES_VORES:b - LLUNY_DE_LES_VORES, ALTRE[k]].sum())
            imatges += b - a - 2 * LLUNY_DE_LES_VORES
    return alarmes, imatges


def mascara(n: int, files: list[dict]) -> np.ndarray:
    dins = np.zeros(n, dtype=bool)
    for f in files:
        dins[f["de"]:f["fins"]] = True
    return dins


def amb_la_veritat(pred: np.ndarray, toc: np.ndarray, on: np.ndarray) -> np.ndarray:
    nova = pred.copy()
    nova[on] = toc[on]
    return nova


def prediccio(nom: str, escenari: str, a_pm: pmo.Abans, triat: tuple) -> tuple:
    """El partit amb la veritat de toc, la predicció d'A pilota morta com al banc de la T3ah (nivell mitjà, llavors de
    provar), la probabilitat relativa i la q que en rep el decodificador."""
    de_sempre, r, q_, netejades = med.base(nom, escenari)
    etiquetes = mpa.etiquetes_de(nom, escenari, MITJA, PROVA)
    relativa = mna.amb_la_d_impossible(pmo.amb_les_etiquetes(r, etiquetes, de_sempre.trams, a_pm,
                                                              mpm.medianes_sense(nom)), netejades)
    pred = mna.prediccio(relativa, q_, de_sempre.trams, triat)
    return replace(de_sempre, veritat=vt.veritat(nom)), pred, relativa, q_.astype(float)


def sostres(perdudes: list[dict], sobren: list[dict]) -> dict[str, list[dict]]:
    """Les imatges de cada sostre: on es posa la veritat."""
    perd = [f for f in perdudes if f["causa"] != "encertada"]
    return {"totes les perdudes i les que sobren": perd + sobren,
            **{f"perdudes: {c}": [f for f in perd if f["causa"] == c] for c in CAUSES[1:]},
            "perdudes: engolides i ajuntades per sobre de l'altre equip": [
                f for f in perd if f["causa"] in ("engolida", AJUNTADA_ALTRE)],
            **{f"sobren: {on}": [f for f in sobren if f["on"] == on] for on in ON},
            **{f"perdudes: {d}": [f for f in perd if durada(f["durada_s"]) == d] for d, _ in DURADES},
            "perdudes: amb l'inici sense pilota": [f for f in perd if not f["inici_vist"]],
            "perdudes: amb l'inici vist": [f for f in perd if f["inici_vist"]],
            "perdudes: engolides amb pilota a l'inici": [f for f in perd if f["causa"] == "engolida" and f["inici_vist"]],
            "perdudes: engolides amb el toc a la vista": [f for f in perd if f["causa"] == "engolida" and f["toc_vist"]]}


def tasca(qui: tuple[str, str, pmo.Abans, tuple]) -> dict[str, list[dict]]:
    nom, escenari, a_pm, triat = qui
    p, pred, relativa, q = prediccio(nom, escenari, a_pm, triat)
    toc, trams = p.veritat.astype(np.int8), avalua.trams_valids(p)
    omplerta = pm.fill_abstentions(pred.astype(np.int8), trams)
    toca = toc_a_la_vista(p.tracking)
    perdudes = [{**f, "veu": la_veu(relativa, f["inici"], f["final"], f["equip"]),
                 "q_inici": float(q[max(0, f["inici"] - K):f["inici"] + K + 1].max()),
                 "toc_vist": bool(toca[max(0, f["inici"] - K):f["inici"] + K + 1, f["equip"]].any())}
                for f in causes(toc, omplerta, trams, ~np.isnan(p.tracking.pilota[:, 0]))]
    sobren = sobrants(toc, omplerta, trams)
    comu = {"partit": nom, "font": p.font, "escenari": escenari}
    base = avalua.puntua(p, pred)["spell_f1"]
    alarmes, imatges = falses_alarmes(toc, trams, toca)
    return {"possessions": [{**comu, **{k: f[k] for k in ("equip", "durada_s", "causa", "inici_vist", "veu", "q_inici",
                                                          "toc_vist")}}
                            for f in perdudes],
            "alarmes": [{**comu, "alarmes": alarmes, "imatges": imatges}],
            "sobrants": [{**comu, **{k: f[k] for k in ("equip", "durada_s", "on")}} for f in sobren],
            "sostres": [{**comu, "sostre": s, "base": base,
                         "spell_f1": avalua.puntua(p, amb_la_veritat(omplerta, toc, mascara(len(toc), fs)))["spell_f1"]}
                        for s, fs in sostres(perdudes, sobren).items()]}


def de_la_t3ah() -> tuple[dict[str, pmo.Abans], dict[str, tuple], pd.Series, list[dict]]:
    """Del banc de la T3ah: els paràmetres i el decodificador de cada partit, l'spellF1 d'A pilota morta amb el nivell
    mitjà a la veritat de toc, i la comparació amb A xarxes."""
    desat = json.loads((DIR_RESULTATS / "model-pilota-morta.json").read_text())
    if desat["clau"] != mpm.clau_dels_resultats():
        raise RuntimeError("El banc de la T3ah no és d'aquest codi")
    f = pd.DataFrame(desat["files"])
    f = f[(f["metode"] == A_PM) & (f["nivell"] == MITJA) & (f["veritat"] == TOC)]
    return ({nom: pmo.Abans(**a) for nom, a in desat["triats"].items()},
            {nom: tuple(t) for nom, t in desat["triades"][A_EQUIPS].items()},
            f.set_index(["partit", "escenari"])["spell_f1"], desat["comparacio"])


def comprova(sost: pd.DataFrame, de_la_t3ah_: pd.Series) -> None:
    aqui = sost.drop_duplicates(["partit", "escenari"]).set_index(["partit", "escenari"])["base"]
    esperat = de_la_t3ah_.reindex(aqui.index)
    if esperat.isna().any() or not np.allclose(aqui, esperat, atol=1e-12, rtol=0):
        raise RuntimeError(f"{A_PM} d'aquí no dona l'spellF1 del banc de la T3ah")


def taula_causes(poss: pd.DataFrame) -> pd.DataFrame:
    g = poss.groupby(["escenari", "causa"]).size()
    t = (g / g.groupby("escenari").transform("sum")).unstack("escenari")
    t = t.reindex(index=list(CAUSES), columns=list(ESCENARIS)).fillna(0.0)
    t.index.name = "causa"
    return t


def taula_durades(poss: pd.DataFrame, escenaris: tuple[str, ...]) -> pd.DataFrame:
    t = poss[poss["escenari"].isin(escenaris)].assign(durada=lambda d: d["durada_s"].map(durada))
    n = t.groupby("durada").size()
    perd = t[t["causa"] != "encertada"]
    n_perd = perd.groupby("durada").size()
    per_causa = perd.groupby(["durada", "causa"]).size().unstack("causa").reindex(columns=list(CAUSES[1:])).fillna(0)
    out = pd.DataFrame({"de la veritat": n / n.sum(), "se'n perden": n_perd / n, "de les perdudes": n_perd / n_perd.sum()})
    out = out.join(per_causa.div(n_perd, axis=0)).reindex([d for d, _ in DURADES]).fillna(0.0)
    out.index.name = "durada"
    return out


def taula_inici(poss: pd.DataFrame, escenaris: tuple[str, ...]) -> pd.DataFrame:
    t = poss[poss["escenari"].isin(escenaris)]
    out = pd.DataFrame({"de la veritat": t.groupby("causa").size() / len(t),
                        "amb l'inici sense pilota": t.groupby("causa")["inici_vist"].apply(lambda v: 1 - v.mean())})
    out = out.reindex(list(CAUSES)).fillna(0.0)
    out.index.name = "causa"
    return out


def taula_sobrants(sob: pd.DataFrame, poss: pd.DataFrame) -> pd.DataFrame:
    g = sob.groupby(["escenari", "on"]).size()
    t = (g / poss.groupby("escenari").size()).unstack("escenari").reindex(index=list(ON), columns=list(ESCENARIS))
    t.loc["totes"] = t.sum()
    t.index.name = "per possessió de la veritat"
    return t.fillna(0.0)


def taula_sostres(sost: pd.DataFrame, comparacio: list[dict]) -> pd.DataFrame:
    guany = sost.assign(guany=sost["spell_f1"] - sost["base"]).groupby(["sostre", "escenari"])["guany"].mean()
    t = guany.unstack("escenari").reindex(index=list(dict.fromkeys(sost["sostre"])), columns=list(ESCENARIS))
    t.loc[f"calen contra {XARXES_TOC}"] = pd.Series(
        {c["escenari"]: max(0.0, CRITERI - c["diferencia"]) for c in comparacio if c["escenari"] in QUARTS_T3})
    t.index.name = "sostre"
    return t


def taula_engolides(poss: pd.DataFrame, alarmes: pd.DataFrame) -> pd.DataFrame:
    curtes = poss[poss["durada_s"] < 5]
    files = {}
    for nom, causa in (("engolides", "engolida"), ("encertades", "encertada")):
        per = curtes[curtes["causa"] == causa].groupby("escenari")
        files[f"{nom}: la veu a més de la meitat de les imatges"] = per["veu"].apply(lambda v: (v > 0.5).mean())
        files[f"{nom}: la q a l'inici (mediana)"] = per["q_inici"].median()
        files[f"{nom}: amb pilota a l'inici"] = per["inici_vist"].mean()
        files[f"{nom}: amb el toc a la vista a l'inici"] = per["toc_vist"].mean()
    a = alarmes.groupby("escenari")[["alarmes", "imatges"]].sum()
    files["falses alarmes del toc a la vista, per minut"] = a["alarmes"] / a["imatges"] * pm.FPS * 60
    t = pd.DataFrame(files).T.reindex(columns=list(ESCENARIS))
    t.index.name = "possessions de menys de 5 s"
    return t


def taula_fonts(poss: pd.DataFrame, escenari: str) -> pd.DataFrame:
    t = poss[poss["escenari"] == escenari]
    g = t.groupby(["font", "causa"]).size()
    out = (g / g.groupby("font").transform("sum")).unstack("font").reindex(list(CAUSES)).fillna(0.0)
    out.index.name = "causa"
    return out


def markdown(r: dict) -> str:
    linies = ["# Banc obert · On falla A pilota morta", "",
              "Generat amb `uv run python -I -m banc.on_falla`. Dades obertes: 7 partits de DFL (IDSSE, CC BY 4.0) i",
              "els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa: la capçalera de",
              "`banc/on_falla.py`. Només per saber-ho.", "",
              f"**{A_PM}** és el de la T3ah, amb el nivell {MITJA} i les llavors de provar (✓ comprovat: l'spellF1 de",
              "cada partit i escenari és el del banc de la T3ah). A la veritat de toc, amb les abstencions omplertes.",
              f"Una possessió s'encerta si la mètrica l'aparella amb una IoU de {IOU:g} o més. Les parts són de totes",
              "les possessions dels deu partits juntes.", "",
              "## Les possessions de la veritat, per causa", "",
              "«Engolida», «l'altre equip» i «la D»: cap possessió predita del mateix equip no la toca. «Engolida»: una",
              "sola possessió predita de l'altre equip la cobreix sencera i toca les de l'altre equip d'abans i",
              "d'després. «Trencada»: la toquen dues possessions predites del mateix equip o més. «Ajuntada»: només una,",
              "que també toca una altra possessió del mateix equip a la veritat; per sobre de l'altre equip si",
              "entremig la veritat hi té l'altre equip, i si no, per sobre de la D. «Les vores»: només una, sola, però",
              "amb la IoU per sota.", "", mv._md(r["causes"], 3), "",
              f"Possessions de la veritat a cada partit, de mitjana: {r['n_veritat']:.0f}.", ""]
    for titol, clau in (("curts ×¼", "durades_curts"), ("els quatre ×¼ junts", "durades_quarts")):
        linies += [f"## Per durada, a {titol}", "",
                   "Quina part de les possessions de la veritat és de cada durada, quina part se'n perd, quina part de",
                   "les perdudes és de cada durada i, de les perdudes de cada durada, per quina causa.", "",
                   mv._md(r[clau], 3), ""]
    for titol, clau in (("curts ×¼", "inici_curts"), ("els quatre ×¼ junts", "inici_quarts")):
        linies += [f"## L'inici, amb pilota o sense, a {titol}", "",
                   f"Sense pilota: no es veu a {K} imatges o menys de l'inici de la possessió de la veritat.", "",
                   mv._md(r[clau], 3), ""]
    linies += ["## Les possessions predites que sobren", "",
               "Quantes n'hi ha per cada possessió de la veritat. «Un tros»: la meitat o més és d'una possessió del",
               "mateix equip a la veritat.", "", mv._md(r["sobrants"], 3), "",
               "## Les engolides: les veu el model?", "",
               "Les possessions de la veritat de menys de 5 s, engolides o encertades. «La veu»: la probabilitat",
               "relativa que rep el decodificador hi dona més a l'equip de la veritat que a l'altre a més de la meitat",
               f"de les imatges. «La q a l'inici»: la més alta a {K} imatges o menys de l'inici. «El toc a la vista»: fet",
               f"a mà, sense aprendre res, a {K} imatges o menys de l'inici; la velocitat de la pilota hi canvia",
               f"{CANVI_MS:g} m/s o més en ±{MIG} imatges, i el més proper, a {A_TOCAR_M:g} m o menys, és de l'equip de la",
               "veritat. Les falses alarmes: els tocs a la vista de l'altre equip dins de les possessions de 10 s o",
               "més, a més d'1 s de les vores.", "", mv._md(r["engolides"], 3), "",
               f"## Els sostres: {A_PM} amb la veritat a una part", "",
               "El que guanya l'spellF1, a la mitjana dels deu partits, posant la veritat a les possessions perdudes",
               "de cada mena (ella sencera i les predites del mateix equip que la toquen) o a les que sobren. L'última",
               f"fila és el que falta contra {XARXES_TOC}, amb el nivell {MITJA}, perquè la diferència arribi a "
               f"{CRITERI:g}.", "", mv._md(r["sostres"], 3), "",
               "## Per font, a curts ×¼", "", mv._md(r["fonts"], 3), ""]
    return "\n".join(linies)


def clau() -> str:
    return hashlib.sha256((inspect.getsource(causes) + inspect.getsource(sobrants) + inspect.getsource(tasca)
                           + mpm.clau_dels_resultats()).encode()).hexdigest()


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import on_falla as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        return list(feina.map(getattr(aquest, fes), tasques))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=10)
    args = ap.parse_args()
    a_pm, triades, spell, comparacio = de_la_t3ah()
    trossos = en_paral_lel("tasca", [(nom, e, a_pm[nom], triades[nom]) for nom in fonts.NOMS for e in ESCENARIS],
                           args.processos)
    poss, sob, sost, alarmes = (pd.DataFrame([f for tros in trossos for f in tros[k]])
                                for k in ("possessions", "sobrants", "sostres", "alarmes"))
    comprova(sost, spell)
    print(f"· {A_PM}: l'spellF1 de cada partit i escenari és el del banc de la T3ah", flush=True)
    r = {"causes": taula_causes(poss), "n_veritat": len(poss) / (len(fonts.NOMS) * len(ESCENARIS)),
         "durades_curts": taula_durades(poss, ("curts ×¼",)), "durades_quarts": taula_durades(poss, QUARTS_T3),
         "inici_curts": taula_inici(poss, ("curts ×¼",)), "inici_quarts": taula_inici(poss, QUARTS_T3),
         "sobrants": taula_sobrants(sob, poss), "engolides": taula_engolides(poss, alarmes),
         "sostres": taula_sostres(sost, comparacio),
         "fonts": taula_fonts(poss, "curts ×¼")}
    DIR_RESULTATS.mkdir(parents=True, exist_ok=True)
    (DIR_RESULTATS / "on-falla.json").write_text(json.dumps(
        {"clau": clau(), "sostres": sost.to_dict("records"),
         **{k: (v.to_dict() if isinstance(v, pd.DataFrame) else v) for k, v in r.items()}},
        ensure_ascii=False, indent=1))
    (DIR_RESULTATS / "on-falla.md").write_text(markdown(r))
    print(markdown(r), flush=True)


if __name__ == "__main__":
    main()
