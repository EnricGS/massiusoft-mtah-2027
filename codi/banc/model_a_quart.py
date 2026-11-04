"""A entrenat amb l'error de posició del partit, i els tocs a sobre (T3b del pla per tocs, `docs/pla-tocs.md`, «T3b»).

    cd codi && uv run python -I -m banc.model_a_quart [--processos 8]

1. **El classificador A ×¼:** el d'A (`cadena.model`: els mateixos paràmetres, una imatge de cada 16 i els equips
   girats), entrenat deixant cada partit fora, però amb curts, llargs i barreja amb l'error de posició ×¼ en lloc del
   ×1. Les probabilitats del partit que queda fora, als deu escenaris de la T3, a la memòria cau
   (`dades/banc/a-entrenat-quart/`).
2. **La graella de la T3,** a cada partit i escenari: totes les combinacions del decodificador d'A, amb el
   classificador d'ara (A) i amb A ×¼, i les del decodificador amb tocs a sobre d'A ×¼, amb el detector de la T3.
3. **Per a cada partit,** la combinació de cada mètode que va millor de mitjana als altres nou, als escenaris ×¼, com a
   la T3. A més, A amb el decodificador de la cadena d'ara.
4. **Els criteris** del pla: A ×¼ contra A, i els tocs a sobre d'A ×¼ contra A ×¼, amb les passades llargues.

Escriu `resultats/model-a-quart.json` (la clau del codi i les files) i `resultats/model-a-quart.md`. Tot són dades
obertes.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import inspect
import itertools
import json
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from banc import avalua, canvis, degrada, fonts, model_a, tocs_desats
from banc import decodificador_tocs as t3
from cadena import decodifica, model, senyals
from cadena import decodifica_tocs as dt
from cadena import tocs

ENTRENAMENT = tuple(f"{e} ×¼" for e in model_a.ESCENARIS_ENTRENAMENT)
ARA, QUART = "ara", "×¼"                       # els dos classificadors
A_QUART, TOCS_QUART = "A ×¼", "tocs ×¼"
DIR_CAU = fonts.DIR_CAU / "a-entrenat-quart"
DIR_RESULTATS = t3.DIR_RESULTATS


@functools.cache
def mostres_de(nom: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Les mostres d'entrenament d'un partit, dels tres escenaris amb l'error ×¼ (un cop per procés)."""
    xs, ys = [], []
    for escenari in ENTRENAMENT:
        p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[escenari])
        x, y = model.mostres([senyals.calcula(p.tracking, p.trams)], [p.veritat], model.PAS)
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def probabilitats(prova: str, entrena: bool = True) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Les d'A ×¼ al partit `prova`, a cada escenari de la T3, amb el model entrenat amb els altres, i el prior. Amb
    `entrena=False`, només les llegeix de la memòria cau, i si no hi són o són d'un altre codi, s'atura."""
    cami = DIR_CAU / f"{prova}.npz"
    if cami.exists():
        with np.load(cami, allow_pickle=False) as desat:
            if str(desat["clau"]) == CLAU:
                return {e: desat[f"e{i}"] for i, e in enumerate(t3.ESCENARIS)}, desat["prior"]
    if not entrena:
        raise RuntimeError(f"Falten les probabilitats d'A ×¼ de {prova}, o són d'un altre codi")
    mostres = [mostres_de(nom) for nom in fonts.NOMS if nom != prova]
    x, y = pd.concat([m[0] for m in mostres], ignore_index=True), np.concatenate([m[1] for m in mostres])
    entrenat = model.entrena(x, y)
    prior = model.prior(y)
    probes = {}
    for i, escenari in enumerate(t3.ESCENARIS.values()):
        p = degrada.aplica(fonts.partit(prova), escenari)
        probes[f"e{i}"] = model.probabilitats(entrenat, senyals.calcula(p.tracking, p.trams)).astype(np.float32)
    DIR_CAU.mkdir(parents=True, exist_ok=True)
    temporal = cami.with_name(f"{cami.name}.{os.getpid()}.part.npz")
    np.savez(temporal, clau=CLAU, prior=prior, **probes)
    temporal.replace(cami)
    return {e: probes[f"e{i}"] for i, e in enumerate(t3.ESCENARIS)}, prior


def graella(tasca: tuple[str, str, tuple[tocs.Parametres, ...]]) -> list[dict]:
    """Un partit i un escenari: les combinacions d'A amb els dos classificadors, i les del decodificador amb tocs a
    sobre d'A ×¼ per a cada detector. Les files porten el classificador, i el mètode com a la T3 (A o tocs)."""
    nom, escenari, detectors = tasca
    p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[escenari])
    comu = {"partit": nom, "font": p.font, "escenari": escenari}
    files = []
    de = {ARA: t3.probabilitats(nom, entrena=False), QUART: probabilitats(nom, entrena=False)}
    for classificador, (probes, prior) in de.items():
        proba = probes[escenari].astype(float)
        for lam, d_min in itertools.product(decodifica.GRAELLA_LAMBDA, decodifica.GRAELLA_DMIN):
            pred = decodifica.per_trams(proba, prior, p.trams, lam, d_min)
            files.append({**comu, "classificador": classificador, "metode": "A", "lam": lam, "d_min": d_min,
                          **avalua.puntua(p, pred)})
    probes, prior = de[QUART]
    proba = probes[escenari].astype(float)
    visible = ~np.isnan(p.tracking.pilota[:, 0])
    for det in detectors:
        trobats = tocs.detecta(p.tracking, p.trams, det)
        for par in t3.GRAELLA_TOCS:
            pred = dt.per_trams(proba, prior, p.trams, visible, trobats, par)
            files.append({**comu, "classificador": QUART, "metode": "tocs", **asdict(det), **asdict(par),
                          **avalua.puntua(p, pred)})
    return files


def tria_sense_mirar(files: pd.DataFrame, dets: dict[str, tocs.Parametres],
                     cadena: dict[str, tuple[float, int]]) -> tuple[pd.DataFrame, dict]:
    """Les files de cada mètode a cada partit, amb la combinació triada amb els altres nou als escenaris ×¼, i les
    triades: A ×¼ i els tocs, amb la tria de la T3; A, igual que A ×¼, i A cadena, amb el decodificador de la cadena."""
    nous, de_la_t3 = t3.tria_sense_mirar(files[files["classificador"] == QUART], dets, cadena)
    nous = nous[nous["metode"] != "A cadena"].replace({"metode": {"A": A_QUART, "tocs": TOCS_QUART}})
    a = files[(files["classificador"] == ARA) & (files["metode"] == "A")]
    triats, triades = [], {}
    for prova in fonts.NOMS:
        lam, d_min = t3.millor(a[a["partit"] != prova], ["lam", "d_min"])
        lam_c, d_c = cadena[prova]
        seves = a[a["partit"] == prova]
        triats += [seves[(seves["lam"] == lam) & (seves["d_min"] == d_min)],
                   seves[(seves["lam"] == lam_c) & (seves["d_min"] == d_c)].assign(metode="A cadena")]
        t = de_la_t3[prova]
        triades[prova] = {"A": (float(lam), int(d_min)), A_QUART: t["A"], "detector": t["detector"],
                          TOCS_QUART: t["tocs"]}
    return pd.concat([*triats, nous], ignore_index=True), triades


def comparacio(metodes: pd.DataFrame, nou: str, contra: str) -> pd.DataFrame:
    """Per escenari: `nou` contra `contra`, i si compleix el criteri del pla (el de la T3)."""
    files = []
    for escenari in t3.ESCENARIS:
        tria = metodes[metodes["escenari"] == escenari].pivot_table(index="partit", columns="metode",
                                                                   values="spell_f1")
        dif = (tria[nou] - tria[contra]).to_numpy()
        font = metodes.groupby("partit")["font"].first().loc[tria.index].to_numpy()
        baix, alt = model_a.interval(dif, font)
        guanya = int((dif > 0).sum())
        if escenari in t3.QUARTS:
            criteri = "guanya clarament"
            passa = bool(dif.mean() > t3.SOROLL and baix > 0 and guanya >= t3.GUANYA_MINIM)
        else:
            criteri, passa = "no perd", bool(dif.mean() >= -t3.SOROLL)
        files.append({"escenari": escenari, "contra": tria[contra].mean(), "nou": tria[nou].mean(),
                      "diferencia": dif.mean(), "baix": baix, "alt": alt, "guanya": guanya, "partits": len(dif),
                      "criteri": criteri, "passa": passa})
    return pd.DataFrame(files)


def compleix(c: pd.DataFrame) -> dict[str, bool]:
    quarts = c["escenari"].isin(t3.QUARTS)
    return {"quarts": bool(c[quarts]["passa"].all()), "altres": bool(c[~quarts]["passa"].all())}


def canvis_de(tasca: tuple[str, str, tuple[float, int], tocs.Parametres, dt.Parametres]) -> list[dict]:
    """El desfasament dels canvis (T1) d'A ×¼ i dels tocs a sobre, amb les combinacions triades, a un partit."""
    nom, escenari, (lam, d_min), det, par = tasca
    net = fonts.partit(nom)
    p = degrada.aplica(net, t3.ESCENARIS[escenari])
    probes, prior = probabilitats(nom, entrena=False)
    proba = probes[escenari].astype(float)
    trobats = tocs.detecta(p.tracking, p.trams, det)
    prediccions = {A_QUART: decodifica.per_trams(proba, prior, p.trams, lam, d_min),
                   TOCS_QUART: dt.per_trams(proba, prior, p.trams, ~np.isnan(p.tracking.pilota[:, 0]), trobats, par)}
    return [f for metode, pred in prediccions.items() for f in canvis.mesura(net, p, pred, metode, escenari)]


def criteri_passades(passades: pd.DataFrame) -> bool:
    """El de la T3, amb A ×¼ al lloc d'A."""
    return t3.criteri_passades(passades.replace({"metode": {A_QUART: "A", TOCS_QUART: "tocs"}}))


def _taula(c: pd.DataFrame, nou: str, contra: str) -> list[str]:
    linies = [f"| escenari | {contra} | {nou} | diferència | interval del 95 % | {nou} guanya | criteri | |",
              "|---|---|---|---|---|---|---|---|"]
    return linies + [f"| {f.escenari} | {f.contra:.3f} | {f.nou:.3f} | {f.diferencia:+.3f} | {f.baix:+.3f} a "
                     f"{f.alt:+.3f} | {f.guanya} de {f.partits} | {f.criteri} | {'✓' if f.passa else '✗'} |"
                     for f in c.itertuples()]


def _criteris(passa: dict[str, bool], amb_passades: bool) -> list[str]:
    def marca(v: bool) -> str:
        return "✓" if v else "✗"

    linies = ["| | Passa si | |", "|---|---|---|",
              f"| Els quatre escenaris ×¼ | guanya clarament a cada un (diferència > {t3.SOROLL}, interval > 0, "
              f"{t3.GUANYA_MINIM} partits de 10 o més) | {marca(passa['quarts'])} |",
              f"| El net, els ×1 i el soroll2 | no perd a cap (diferència ≥ −{t3.SOROLL}) | {marca(passa['altres'])} |"]
    if amb_passades:
        linies.append(f"| Les passades llargues, els quatre ×¼ junts | a temps puja, i abans d'hora no puja | "
                      f"{marca(passa['passades'])} |")
    return linies + ["", f"**{'Passa' if all(passa.values()) else 'No passa'}.**", ""]


def markdown(c1: pd.DataFrame, c2: pd.DataFrame, metodes: pd.DataFrame, triades: dict, passades: pd.DataFrame,
             passa: dict[str, dict[str, bool]]) -> str:
    def pct(v: float) -> str:
        return f"{v:.0%}"

    ordre = ["A cadena", "A", A_QUART, TOCS_QUART]
    linies = ["# Banc obert · A entrenat amb l'error del partit (T3b)", "",
              "Generat amb `uv run python -I -m banc.model_a_quart`. Dades obertes: 7 partits de DFL (IDSSE, CC BY",
              "4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i els",
              "criteris: `docs/pla-tocs.md`, «T3b», i la capçalera de `banc/model_a_quart.py`.", "",
              "**A** és el classificador d'ara, entrenat amb l'error de posició ×1, i **A ×¼**, el mateix entrenat amb",
              "l'error ×¼. Tots dos tenen el decodificador triat amb els altres nou partits als escenaris ×¼. **A",
              "cadena** és A amb el decodificador de la cadena d'ara, i **tocs ×¼**, el decodificador amb tocs a sobre",
              "d'A ×¼, amb la tria de la T3.", "",
              "## L'spellF1 i el macroF1 de cada mètode (mitjana dels deu partits)", ""]
    for columna, nom in (("spell_f1", "spellF1"), ("macro_f1", "macroF1")):
        t = metodes.pivot_table(index="escenari", columns="metode", values=columna, sort=False)[ordre]
        linies += [f"**{nom}**", "", "| escenari | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 1) + "|"]
        linies += [f"| {e} | " + " | ".join(f"{v:.3f}" for v in f) + " |" for e, f in t.iterrows()]
        linies.append("")
    linies += ["## 1. A ×¼ contra A (spellF1)", "", *_taula(c1, A_QUART, "A"), "", *_criteris(passa["1"], False),
               "## 2. Els tocs a sobre d'A ×¼, contra A ×¼ (spellF1)", "", *_taula(c2, TOCS_QUART, A_QUART), "",
               "**Les passades llargues (T1).** Possessions de 2 s o més, amb pilota abans del canvi i passada",
               "llarga: la part dels canvis de la veritat on el mètode canvia a temps (a menys d'1 s) i abans d'hora",
               "(1 s o més).", "",
               f"| escenari | canvis | {A_QUART} a temps | {TOCS_QUART} a temps | {A_QUART} abans d'hora | "
               f"{TOCS_QUART} abans d'hora |", "|---|---|---|---|---|---|"]
    for escenari, g in passades.groupby("escenari", sort=False):
        f = g.set_index("metode")
        linies.append(f"| {escenari} | {int(f.loc[A_QUART, 'canvis'])} | {pct(f.loc[A_QUART, 'a_temps'])} | "
                      f"{pct(f.loc[TOCS_QUART, 'a_temps'])} | {pct(f.loc[A_QUART, 'abans'])} | "
                      f"{pct(f.loc[TOCS_QUART, 'abans'])} |")
    linies += ["", *_criteris(passa["2"], True), "## Les combinacions triades (cada partit, amb els altres nou)", ""]
    compta: dict[str, int] = {}
    for t in triades.values():
        d, p = t["detector"], t[TOCS_QUART]
        lam_vis = "impossible" if np.isinf(p.lam_vis) else f"{p.lam_vis:g}"
        clau_ = (f"A: λ = {t['A'][0]:g}, durada mínima {t['A'][1]} · A ×¼: λ = {t[A_QUART][0]:g}, durada mínima "
                 f"{t[A_QUART][1]} · tocs ×¼: k = {d.k}, {d.canvi_ms:g} m/s, {d.abast_m:g} m; control {p.control}, "
                 f"λ_vis {lam_vis}, λ {p.lam:g}, durada mínima {p.d_min}")
        compta[clau_] = compta.get(clau_, 0) + 1
    linies += [f"- {k} ({n} partits)" for k, n in compta.items()]
    return "\n".join(linies + [""])


def clau() -> str:
    """El que fa les probabilitats d'A ×¼: el codi d'A (`model_a.CLAU`), els escenaris i l'entrenament d'aquí."""
    h = hashlib.sha256((model_a.CLAU + repr(list(t3.ESCENARIS.values())) + repr(ENTRENAMENT)).encode())
    for funcio in (mostres_de, probabilitats):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + t3.CLAU_CAU + model_a.CLAU_RESULTATS + tocs_desats.clau()).encode())
    for modul in (t3, dt, tocs, decodifica, canvis, avalua, degrada):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def main() -> None:
    from banc import model_a_quart as aquest      # pel nom del mòdul, perquè els processos fills el trobin

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=8)
    ap.add_argument("--processos-models", type=int, default=2, help="models alhora (cadascun fa servir 8 fils)")
    args = ap.parse_args()
    desat = json.loads((tocs_desats.DIR_RESULTATS / "tocs.json").read_text())
    if desat.get("clau") != tocs_desats.clau():
        raise RuntimeError("Els resultats del banc de tocs són d'un altre codi: torna a fer `python -I -m banc.tocs`")
    dets = t3.detectors(pd.DataFrame(desat["files"]))
    for nom in fonts.NOMS:
        t3.probabilitats(nom, entrena=False)       # les d'A, de la T3: si falten, abans cal fer-la
    with ProcessPoolExecutor(max_workers=args.processos_models) as feina:
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.probabilitats, fonts.NOMS)):
            print(f"· {nom}: A ×¼ fet", flush=True)
    diferents = tuple(dict.fromkeys(dets.values()))
    tasques = [(nom, escenari, diferents) for nom in fonts.NOMS for escenari in t3.ESCENARIS]
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        files = pd.DataFrame([f for tros in feina.map(aquest.graella, tasques) for f in tros])
    print("· la graella, feta", flush=True)
    metodes, triades = tria_sense_mirar(files, dets, canvis.decodificadors(model_a.resultats()))
    c1, c2 = comparacio(metodes, A_QUART, "A"), comparacio(metodes, TOCS_QUART, A_QUART)
    tasques_canvis = [(nom, q, triades[nom][A_QUART], triades[nom]["detector"], triades[nom][TOCS_QUART])
                      for nom in fonts.NOMS for q in t3.QUARTS]
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        files_canvis = pd.DataFrame([f for tros in feina.map(aquest.canvis_de, tasques_canvis) for f in tros])
    passades = t3.passades_llargues(files_canvis)
    passa = {"1": compleix(c1), "2": {**compleix(c2), "passades": criteri_passades(passades)}}
    desa = {"clau": clau_dels_resultats(), "passa": passa, "comparacio_1": t3.registres(c1),
            "comparacio_2": t3.registres(c2), "passades": t3.registres(passades),
            "triades": {n: {"A": t["A"], A_QUART: t[A_QUART], "detector": asdict(t["detector"]),
                            TOCS_QUART: {**asdict(t[TOCS_QUART]), "lam_vis": str(t[TOCS_QUART].lam_vis)}}
                        for n, t in triades.items()},
            "files": t3.registres(files)}
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-a-quart.json").write_text(json.dumps(desa, indent=1, default=float, allow_nan=False))
    (DIR_RESULTATS / "model-a-quart.md").write_text(markdown(c1, c2, metodes, triades, passades, passa))
    print((DIR_RESULTATS / "model-a-quart.md").read_text())


if __name__ == "__main__":
    main()
