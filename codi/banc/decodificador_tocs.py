"""El decodificador amb tocs al banc obert (T3 del pla per tocs, `docs/pla-tocs.md`, «T3: els criteris»).

    cd codi && uv run python -I -m banc.decodificador_tocs [--processos 8]

1. **Els escenaris:** el net; curts, llargs, barreja i aire amb l'error de posició ×¼ (el de l'ATD del partit, segons
   la V1 del pla del vídeo), amb els mateixos forats; i els degradats tal com són (×1) i el soroll2.
2. **Les probabilitats d'A:** les de `model_a` (la memòria cau) i, per als ×¼, les del mateix model, refet deixant
   cada partit fora. Abans es comprova que el model refet dona exactament les mateixes probabilitats a la barreja.
3. **Els tocs** (`cadena.tocs`) de cada partit, amb els paràmetres de més benefici a la barreja ×¼ als altres nou
   (`resultats/tocs.json`, T2).
4. **Totes les combinacions** del decodificador d'A (λ i la durada mínima) i del decodificador amb tocs
   (`cadena.decodifica_tocs`: el control, λ_vis, λ i la durada mínima), a cada partit i escenari.
5. **Per a cada partit,** la combinació de cada mètode que va millor de mitjana als altres nou, als escenaris ×¼. A
   més, A amb el decodificador de la cadena d'ara.
6. **Els criteris** del pla, i el desfasament dels canvis a les passades llargues (`canvis.mesura`, T1).

Escriu `resultats/decodificador-tocs.json` (la clau del codi i les files) i `resultats/decodificador-tocs.md`. Tot
són dades obertes.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pandas as pd

from banc import avalua, canvis, degrada, fonts, model_a, tocs_desats
from banc import tocs as banc_tocs
from cadena import decodifica, model, senyals
from cadena import decodifica_tocs as dt
from cadena import tocs

BASES = ("curts", "llargs", "barreja", "aire")
QUART = 0.25
QUARTS = tuple(f"{e} ×¼" for e in BASES)
GRAELLA_TOCS = tuple(dt.Parametres(control, lam_vis, lam, d_min) for control in (1, 2)
                     for lam_vis in (16.0, 64.0, math.inf) for lam in (4.0, 8.0, 16.0) for d_min in (1, 25))
DIR_CAU = fonts.DIR_CAU / "a-quart"
DIR_RESULTATS = Path(__file__).resolve().parent / "resultats"
SOROLL = model_a.SOROLL
GUANYA_MINIM = 8                    # partits de 10
COLUMNES_TOCS = ["control", "lam_vis", "lam", "d_min"]
COLUMNES_DETECTOR = ["k", "canvi_ms", "abast_m"]


def amb_error(nom: str, factor: float) -> degrada.Escenari:
    """L'escenari, amb els mateixos forats (depenen del nom) i l'error de posició multiplicat per `factor`."""
    e = degrada.ESCENARIS[nom]
    return replace(e, sigma_jugadors_m=e.sigma_jugadors_m * factor, sigma_pilota_m=e.sigma_pilota_m * factor,
                   tremolor_jugadors_m=e.tremolor_jugadors_m * factor,
                   tremolor_pilota_m=e.tremolor_pilota_m * factor)


ESCENARIS = {"net": "net", **{q: amb_error(b, QUART) for q, b in zip(QUARTS, BASES)},
             **{e: e for e in (*BASES, "soroll2")}}
CLAU_CAU = hashlib.sha256((model_a.CLAU + repr([ESCENARIS[q] for q in QUARTS])).encode()).hexdigest()


def probabilitats(prova: str, entrena: bool = True) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Les d'A a tots els escenaris d'aquí, i el prior. Les ×¼, del mateix model refet, a `DIR_CAU`."""
    probes, prior = model_a.probabilitats(prova, entrena=False)
    cami = DIR_CAU / f"{prova}.npz"
    if cami.exists():
        with np.load(cami, allow_pickle=False) as desat:
            if str(desat["clau"]) == CLAU_CAU:
                return {**probes, **{q: desat[f"q{i}"] for i, q in enumerate(QUARTS)}}, prior
    if not entrena:
        raise RuntimeError(f"Falten les probabilitats ×¼ de {prova}, o són d'un altre codi")
    mostres = [model_a.mostres_de(nom) for nom in fonts.NOMS if nom != prova]
    x, y = pd.concat([m[0] for m in mostres], ignore_index=True), np.concatenate([m[1] for m in mostres])
    entrenat = model.entrena(x, y)

    def de(escenari: str | degrada.Escenari) -> np.ndarray:
        p = degrada.aplica(fonts.partit(prova), escenari)
        return model.probabilitats(entrenat, senyals.calcula(p.tracking, p.trams)).astype(np.float32)

    if not np.array_equal(de("barreja"), probes["barreja"]) or not np.array_equal(model.prior(y), prior):
        raise RuntimeError(f"{prova}: el model refet no dona les probabilitats d'A")
    quarts = {f"q{i}": de(ESCENARIS[q]) for i, q in enumerate(QUARTS)}
    DIR_CAU.mkdir(parents=True, exist_ok=True)
    temporal = cami.with_name(f"{cami.name}.{os.getpid()}.part.npz")
    np.savez(temporal, clau=CLAU_CAU, **quarts)
    temporal.replace(cami)
    return {**probes, **{q: quarts[f"q{i}"] for i, q in enumerate(QUARTS)}}, prior


def detectors(files_t2: pd.DataFrame) -> dict[str, tocs.Parametres]:
    """Per a cada partit, els paràmetres del detector de tocs amb més benefici a la barreja ×¼ als altres nou."""
    escenari = tocs_desats.nom_soroll(QUART)
    triats = {}
    for prova in fonts.NOMS:
        millor = banc_tocs.per_parametres(files_t2[files_t2["partit"] != prova], (escenari,)).iloc[0]
        triats[prova] = tocs.Parametres(int(millor["k"]), float(millor["canvi_ms"]), float(millor["abast_m"]))
    return triats


def graella(tasca: tuple[str, str, tuple[tocs.Parametres, ...]]) -> list[dict]:
    """Un partit i un escenari: totes les combinacions d'A, i les del decodificador amb tocs per a cada detector."""
    nom, escenari, detectors_ = tasca
    p = degrada.aplica(fonts.partit(nom), ESCENARIS[escenari])
    probes, prior = probabilitats(nom, entrena=False)
    proba = probes[escenari].astype(float)
    comu = {"partit": nom, "font": p.font, "escenari": escenari}
    files = []
    for lam, d_min in itertools.product(decodifica.GRAELLA_LAMBDA, decodifica.GRAELLA_DMIN):
        pred = decodifica.per_trams(proba, prior, p.trams, lam, d_min)
        files.append({**comu, "metode": "A", "lam": lam, "d_min": d_min, **avalua.puntua(p, pred)})
    visible = ~np.isnan(p.tracking.pilota[:, 0])
    for det in detectors_:
        trobats = tocs.detecta(p.tracking, p.trams, det)
        for par in GRAELLA_TOCS:
            pred = dt.per_trams(proba, prior, p.trams, visible, trobats, par)
            files.append({**comu, "metode": "tocs", **asdict(det), **asdict(par), **avalua.puntua(p, pred)})
    return files


def millor(files: pd.DataFrame, columnes: list[str]) -> tuple:
    """La combinació amb més spellF1 de mitjana als escenaris ×¼ (desempata el macroF1)."""
    tria = files[files["escenari"].isin(QUARTS)]
    mitjanes = tria.groupby(columnes, dropna=False)[["spell_f1", "macro_f1"]].mean()
    return mitjanes.sort_values(["spell_f1", "macro_f1"], ascending=False).index[0]


def del_detector(files: pd.DataFrame, det: tocs.Parametres) -> pd.DataFrame:
    return files[(files["metode"] == "tocs") & (files["k"] == det.k) & (files["canvi_ms"] == det.canvi_ms)
                 & (files["abast_m"] == det.abast_m)]


def tria_sense_mirar(files: pd.DataFrame, dets: dict[str, tocs.Parametres],
                     cadena: dict[str, tuple[float, int]]) -> tuple[pd.DataFrame, dict]:
    """Les files de cada mètode a cada partit, amb la combinació triada amb els altres nou, i les triades."""
    a, t = files[files["metode"] == "A"], files[files["metode"] == "tocs"]
    triats, triades = [], {}
    for prova in fonts.NOMS:
        lam, d_min = millor(a[a["partit"] != prova], ["lam", "d_min"])
        de_t = del_detector(t, dets[prova])
        combinacio = millor(de_t[de_t["partit"] != prova], COLUMNES_TOCS)
        par = dt.Parametres(int(combinacio[0]), float(combinacio[1]), float(combinacio[2]), int(combinacio[3]))
        lam_c, d_c = cadena[prova]
        seves_a = a[a["partit"] == prova]
        triats += [seves_a[(seves_a["lam"] == lam) & (seves_a["d_min"] == d_min)],
                   seves_a[(seves_a["lam"] == lam_c) & (seves_a["d_min"] == d_c)].assign(metode="A cadena")]
        seves_t = de_t[de_t["partit"] == prova]
        triats.append(seves_t[np.logical_and.reduce([seves_t[c] == v for c, v in asdict(par).items()])])
        triades[prova] = {"A": (float(lam), int(d_min)), "detector": dets[prova], "tocs": par}
    return pd.concat(triats, ignore_index=True), triades


def comparacio(metodes: pd.DataFrame) -> pd.DataFrame:
    """Per escenari: el model amb tocs contra A, i si compleix el criteri del pla."""
    files = []
    for escenari in ESCENARIS:
        tria = metodes[metodes["escenari"] == escenari].pivot_table(index="partit", columns="metode",
                                                                   values="spell_f1")
        dif = (tria["tocs"] - tria["A"]).to_numpy()
        font = metodes.groupby("partit")["font"].first().loc[tria.index].to_numpy()
        baix, alt = model_a.interval(dif, font)
        guanya = int((dif > 0).sum())
        if escenari in QUARTS:
            criteri, passa = "guanya clarament", bool(dif.mean() > SOROLL and baix > 0 and guanya >= GUANYA_MINIM)
        else:
            criteri, passa = "no perd", bool(dif.mean() >= -SOROLL)
        files.append({"escenari": escenari, "A cadena": tria["A cadena"].mean(), "A": tria["A"].mean(),
                      "tocs": tria["tocs"].mean(), "diferencia": dif.mean(), "baix": baix, "alt": alt,
                      "guanya": guanya, "partits": len(dif), "criteri": criteri, "passa": passa})
    return pd.DataFrame(files)


def canvis_de(tasca: tuple[str, str, tuple[float, int], tocs.Parametres, dt.Parametres]) -> list[dict]:
    """El desfasament dels canvis (T1) d'A i del model amb tocs, amb les combinacions triades, a un partit."""
    nom, escenari, (lam, d_min), det, par = tasca
    net = fonts.partit(nom)
    p = degrada.aplica(net, ESCENARIS[escenari])
    probes, prior = probabilitats(nom, entrena=False)
    proba = probes[escenari].astype(float)
    trobats = tocs.detecta(p.tracking, p.trams, det)
    prediccions = {"A": decodifica.per_trams(proba, prior, p.trams, lam, d_min),
                   "tocs": dt.per_trams(proba, prior, p.trams, ~np.isnan(p.tracking.pilota[:, 0]), trobats, par)}
    return [f for metode, pred in prediccions.items() for f in canvis.mesura(net, p, pred, metode, escenari)]


def passades_llargues(files: pd.DataFrame) -> pd.DataFrame:
    """A temps i abans d'hora, a les possessions de 2 s o més amb pilota i passada llarga: per escenari i juntes."""
    llargues = files[(files["possessio"] == "≥ 2 s") & (files["passada"] == "llarga") & (files["pilota"] == "amb")]
    per = canvis.resum(llargues, ("escenari", "metode"))
    juntes = canvis.resum(llargues.assign(escenari="els quatre ×¼"), ("escenari", "metode"))
    return pd.concat([per, juntes], ignore_index=True)


def criteri_passades(t: pd.DataFrame) -> bool:
    juntes = t[t["escenari"] == "els quatre ×¼"].set_index("metode")
    return bool(juntes.loc["tocs", "a_temps"] > juntes.loc["A", "a_temps"]
                and juntes.loc["tocs", "abans"] <= juntes.loc["A", "abans"])


def markdown(c: pd.DataFrame, metodes: pd.DataFrame, triades: dict, passades: pd.DataFrame, passa: dict) -> str:
    def pct(v: float) -> str:
        return f"{v:.0%}"

    def lam(v: float) -> str:
        return "impossible" if math.isinf(v) else f"{v:g}"

    linies = ["# Banc obert · el decodificador amb tocs (T3)", "",
              "Generat amb `uv run python -I -m banc.decodificador_tocs`. Dades obertes: 7 partits de DFL (IDSSE, CC BY",
              "4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i els",
              "criteris: `docs/pla-tocs.md`, «T3: els criteris», i la capçalera de `banc/decodificador_tocs.py`.", "",
              "**A** té el decodificador triat amb els altres nou partits als escenaris ×¼, i **A cadena**, el de la",
              "cadena d'ara (triat als ×1). **Tocs** és el model nou, amb la mateixa tria. Els tres fan servir el",
              "mateix classificador.", "",
              "## L'spellF1, escenari per escenari", "",
              "| escenari | A cadena | A | tocs | tocs − A | interval del 95 % | tocs guanya | criteri | |",
              "|---|---|---|---|---|---|---|---|---|"]
    linies += [f"| {f.escenari} | {f.a_cadena:.3f} | {f.A:.3f} | {f.tocs:.3f} | {f.diferencia:+.3f} | {f.baix:+.3f} a "
               f"{f.alt:+.3f} | {f.guanya} de {f.partits} | {f.criteri} | {'✓' if f.passa else '✗'} |"
               for f in c.rename(columns={"A cadena": "a_cadena"}).itertuples()]
    macro = metodes.pivot_table(index="escenari", columns="metode", values="macro_f1", sort=False)
    linies += ["", "**El macroF1** (mitjana dels deu partits)", "", "| escenari | A cadena | A | tocs |",
               "|---|---|---|---|"]
    linies += [f"| {e} | {f['A cadena']:.3f} | {f['A']:.3f} | {f['tocs']:.3f} |" for e, f in macro.iterrows()]
    linies += ["", "## Les passades llargues (T1)", "",
               "Possessions de 2 s o més, amb pilota abans del canvi i passada llarga: la part dels canvis de la",
               "veritat on el mètode canvia a temps (a menys d'1 s) i abans d'hora (1 s o més).", "",
               "| escenari | canvis | A a temps | tocs a temps | A abans d'hora | tocs abans d'hora |",
               "|---|---|---|---|---|---|"]
    for escenari, g in passades.groupby("escenari", sort=False):
        f = g.set_index("metode")
        linies.append(f"| {escenari} | {int(f.loc['A', 'canvis'])} | {pct(f.loc['A', 'a_temps'])} | "
                      f"{pct(f.loc['tocs', 'a_temps'])} | {pct(f.loc['A', 'abans'])} | {pct(f.loc['tocs', 'abans'])} |")
    linies += ["", "## Les combinacions triades (cada partit, amb els altres nou)", ""]
    compta: dict[str, int] = {}
    for t in triades.values():
        d, p = t["detector"], t["tocs"]
        clau_ = (f"A: λ = {t['A'][0]:g}, durada mínima {t['A'][1]} · tocs: k = {d.k}, {d.canvi_ms:g} m/s, "
                 f"{d.abast_m:g} m; control {p.control}, λ_vis {lam(p.lam_vis)}, λ {p.lam:g}, durada mínima {p.d_min}")
        compta[clau_] = compta.get(clau_, 0) + 1
    linies += [f"- {k} ({n} partits)" for k, n in compta.items()]
    linies += ["", "## Els criteris", "", "| | Passa si | |", "|---|---|---|",
               f"| Els quatre escenaris ×¼ | guanya A clarament a cada un (diferència > {SOROLL}, interval > 0, "
               f"{GUANYA_MINIM} partits de 10 o més) | {'✓' if passa['quarts'] else '✗'} |",
               f"| El net, els ×1 i el soroll2 | no perd a cap (diferència ≥ −{SOROLL}) | "
               f"{'✓' if passa['altres'] else '✗'} |",
               f"| Les passades llargues, els quatre ×¼ junts | a temps puja, i abans d'hora no puja | "
               f"{'✓' if passa['passades'] else '✗'} |", "",
               f"**{'Passa' if all(passa.values()) else 'No passa'}.**", ""]
    return "\n".join(linies)


def registres(t: pd.DataFrame) -> list[dict]:
    """JSON vàlid: sense NaN (null) ni infinits (el λ_vis impossible, «inf»)."""
    return t.replace([math.inf], "inf").astype(object).where(t.notna(), None).to_dict("records")


def clau() -> str:
    h = hashlib.sha256((CLAU_CAU + model_a.CLAU_RESULTATS + tocs_desats.clau()).encode())
    for modul in (dt, tocs, decodifica, canvis, avalua, degrada):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def main() -> None:
    from banc import decodificador_tocs as aquest     # pel nom del mòdul, perquè els processos fills el trobin

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=8)
    ap.add_argument("--processos-models", type=int, default=2, help="models alhora (cadascun fa servir 8 fils)")
    args = ap.parse_args()
    desat = json.loads((tocs_desats.DIR_RESULTATS / "tocs.json").read_text())
    if desat.get("clau") != tocs_desats.clau():
        raise RuntimeError("Els resultats del banc de tocs són d'un altre codi: torna a fer `python -I -m banc.tocs`")
    dets = detectors(pd.DataFrame(desat["files"]))
    with ProcessPoolExecutor(max_workers=args.processos_models) as feina:
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.probabilitats, fonts.NOMS)):
            print(f"· {nom}: probabilitats ×¼ fetes", flush=True)
    diferents = tuple(dict.fromkeys(dets.values()))
    tasques = [(nom, escenari, diferents) for nom in fonts.NOMS for escenari in ESCENARIS]
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        files = pd.DataFrame([f for tros in feina.map(aquest.graella, tasques) for f in tros])
    print("· la graella, feta", flush=True)
    cadena = canvis.decodificadors(model_a.resultats())
    metodes, triades = tria_sense_mirar(files, dets, cadena)
    c = comparacio(metodes)
    tasques_canvis = [(nom, q, triades[nom]["A"], triades[nom]["detector"], triades[nom]["tocs"])
                      for nom in fonts.NOMS for q in QUARTS]
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        files_canvis = pd.DataFrame([f for tros in feina.map(aquest.canvis_de, tasques_canvis) for f in tros])
    passades = passades_llargues(files_canvis)
    passa = {"quarts": bool(c[c["escenari"].isin(QUARTS)]["passa"].all()),
             "altres": bool(c[~c["escenari"].isin(QUARTS)]["passa"].all()), "passades": criteri_passades(passades)}
    DIR_RESULTATS.mkdir(exist_ok=True)
    desa = {"clau": clau(), "passa": passa, "comparacio": registres(c), "passades": registres(passades),
            "triades": {n: {"A": t["A"], "detector": asdict(t["detector"]),
                            "tocs": {**asdict(t["tocs"]), "lam_vis": str(t["tocs"].lam_vis)}}
                        for n, t in triades.items()},
            "files": registres(files)}
    (DIR_RESULTATS / "decodificador-tocs.json").write_text(json.dumps(desa, indent=1, default=float,
                                                                       allow_nan=False))
    (DIR_RESULTATS / "decodificador-tocs.md").write_text(markdown(c, metodes, triades, passades, passa))
    print((DIR_RESULTATS / "decodificador-tocs.md").read_text())


if __name__ == "__main__":
    main()
