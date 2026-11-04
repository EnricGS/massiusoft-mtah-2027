"""Més partits per entrenar, els de SkillCorner (T3l del pla per tocs, `docs/pla-tocs.md`, «T3l»).

    cd codi && uv run python -I -m banc.model_a_skillcorner [--processos 12] [--processos-models 2]

A aturades (T3k) tal qual, amb tots els models entrenats també amb els 20 partits de SkillCorner
(`banc/skillcorner.py`). Els mateixos senyals, el mateix LightGBM, les mateixes mostres, i el decodificador amb la
graella de la T3j.

1. **Els primers dels grups:** el grup i és el de la T3e (tres partits del banc) i un de cada tres de SkillCorner
   (`grups`). Cada un, entrenat amb la resta, sense el partit que es prova (`dades/banc/a-skillcorner-grups/`).
2. **El primer del partit que es prova,** entrenat amb els altres nou del banc i els vint de SkillCorner
   (`dades/banc/a-skillcorner-primer/`).
3. **El segon** (la taula d'A aturades) **i la q** (la taula d'A contacte, com a la T3i), entrenats amb les
   probabilitats dels primers dels grups, als nou partits i als vint, i als sis escenaris
   (`dades/banc/a-skillcorner/`).
4. **El criteri** del pla: A amb SkillCorner contra A context, el de la cadena. Només per saber-ho, contra A aturades
   (el mateix sense SkillCorner), per font, l'encert de l'equip per durada amb pilota i sense, i la veritat de
   SkillCorner al costat de la del banc.

Només es proven els deu partits del banc. Escriu `resultats/model-a-skillcorner.json` (la clau del codi i les files)
i `resultats/model-a-skillcorner.md`. Tot són dades obertes. Els mòduls de la T3e a la T3k no es toquen.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import itertools
import json
import math
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from banc import avalua, degrada, fonts, partit, skillcorner
from banc import decodificador_tocs as t3
from banc import model_a_aturades as t3k
from banc import model_a_canvis as t3i
from banc import model_a_canvis2 as t3j
from banc import model_a_contacte as t3h
from banc import model_a_context as t3e
from banc import model_a_possessio as t3f
from banc import model_a_quart as t3b
from cadena import decodifica, model
from cadena import decodifica_tocs as dt
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ENTRENAMENT = t3h.ENTRENAMENT
EXTRA = fonts.NOMS_SKILLCORNER
SKILLCORNER = "A amb SkillCorner"
METODES = (t3e.CONTEXT, t3k.ATURADES, SKILLCORNER)
DURADES = (0, 1, 2, 5, math.inf)                    # s, per saber-ho
NOMS_DURADA = ("<1 s", "1-2 s", "2-5 s", "≥5 s")
DIR_CAU = fonts.DIR_CAU / "a-skillcorner"
DIR_CAU_PRIMER = fonts.DIR_CAU / "a-skillcorner-primer"
DIR_CAU_GRUPS = fonts.DIR_CAU / "a-skillcorner-grups"
DIR_RESULTATS = t3.DIR_RESULTATS


def grups(prova: str) -> tuple[tuple[str, ...], ...]:
    """Els de la T3e (els altres nou del banc, en tres grups de tres) i un de cada tres de SkillCorner a cada un."""
    return tuple(banc + EXTRA[i::t3e.GRUPS] for i, banc in enumerate(t3e.grups(prova)))


def per_entrenar(prova: str) -> tuple[str, ...]:
    return tuple(nom for nom in fonts.NOMS if nom != prova) + EXTRA


def desa(cami: Path, **arrays: np.ndarray) -> None:
    cami.parent.mkdir(parents=True, exist_ok=True)
    temporal = cami.with_name(f"{cami.name}.{os.getpid()}.part.npz")
    np.savez(temporal, clau=CLAU, **arrays)
    temporal.replace(cami)


def llegeix(cami: Path) -> dict[str, np.ndarray] | None:
    if cami.exists():
        with np.load(cami, allow_pickle=False) as desat:
            if str(desat["clau"]) == CLAU:
                return {k: desat[k] for k in desat.files if k != "clau"}
    return None


def primer_de_la_prova(prova: str) -> dict[str, np.ndarray]:
    """Les probabilitats del primer al partit `prova`, als deu escenaris, entrenat amb els altres nou i els vint."""
    cami = DIR_CAU_PRIMER / f"{prova}.npz"
    desat = llegeix(cami)
    if desat is None:
        entrenat = t3h.entrena_primer(list(per_entrenar(prova)))
        desat = {f"e{i}": model.probabilitats(entrenat, t3h.taula_primer(degrada.aplica(fonts.partit(prova), e))
                                              ).astype(np.float32) for i, e in enumerate(t3.ESCENARIS.values())}
        desa(cami, **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(t3.ESCENARIS)}


def primer_del_grup(tasca: tuple[str, int]) -> dict[tuple[str, str], np.ndarray]:
    """Les probabilitats del primer als partits del grup `i` de `prova`, als sis escenaris d'entrenament, entrenat amb
    els altres partits per entrenar."""
    prova, i = tasca
    grup = grups(prova)[i]
    claus = {(nom, e): f"p{j}_{k}" for j, nom in enumerate(grup) for k, e in enumerate(ENTRENAMENT)}
    cami = DIR_CAU_GRUPS / f"{prova}-{i}.npz"
    desat = llegeix(cami)
    if desat is None:
        entrenat = t3h.entrena_primer([nom for nom in per_entrenar(prova) if nom not in grup])
        desat = {clau_: model.probabilitats(entrenat, t3h.taula_primer(degrada.aplica(fonts.partit(nom),
                                                                                     t3.ESCENARIS[e]))
                                            ).astype(np.float32) for (nom, e), clau_ in claus.items()}
        desa(cami, **desat)
    return {qui: desat[nom] for qui, nom in claus.items()}


def mostres_segon_i_q(prova: str) -> tuple[tuple[pd.DataFrame, np.ndarray], tuple[pd.DataFrame, np.ndarray]]:
    """Les mostres del segon (la taula d'A aturades, la tria de la T3f) i les de la q (la taula d'A contacte, la tria
    de la T3i), als partits per entrenar i als sis escenaris, amb les probabilitats dels primers dels grups."""
    primers = {}
    for i in range(t3e.GRUPS):
        primers |= primer_del_grup((prova, i))
    segon, q = ([], []), ([], [])
    for (nom, e), primer in primers.items():
        p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[e])
        taula = t3k.taula_segon(p, primer.astype(float))
        for llista, (x, y) in ((segon, t3f.mostres(p, taula)),
                               (q, t3i.mostres(p, taula[[c for c in taula.columns if not c.startswith("aturada_")]]))):
            llista[0].append(x)
            llista[1].append(y)
    return ((pd.concat(segon[0], ignore_index=True), np.concatenate(segon[1])),
            (pd.concat(q[0], ignore_index=True), np.concatenate(q[1])))


def probabilitats(prova: str, entrena: bool = True) -> tuple[dict[str, np.ndarray], np.ndarray, dict[str, np.ndarray]]:
    """Les d'A amb SkillCorner al partit `prova`, a cada escenari de la T3, el prior i la q. Amb `entrena=False`, només
    les llegeix de la memòria cau, i si no hi són o són d'un altre codi, s'atura."""
    cami = DIR_CAU / f"{prova}.npz"
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les probabilitats d'{SKILLCORNER} de {prova}, o són d'un altre codi")
        t3h.mostres_primer.cache_clear()                # les del primer, que aquest procés potser guarda: la memòria
        (x, y), (xq, yq) = mostres_segon_i_q(prova)
        segon, prior = model.entrena(x, y), model.prior(y)
        del x
        canvis = lgb.train(t3i.PARAMS, lgb.Dataset(xq, label=yq, free_raw_data=True), num_boost_round=model.RONDES)
        columnes_q = list(xq.columns)
        del xq
        primers = primer_de_la_prova(prova)
        desat = {"prior": prior}
        for i, (nom_e, escenari) in enumerate(t3.ESCENARIS.items()):
            p = degrada.aplica(fonts.partit(prova), escenari)
            taula = t3k.taula_segon(p, primers[nom_e].astype(float))
            desat[f"e{i}"] = model.probabilitats(segon, taula).astype(np.float32)
            desat[f"q{i}"] = t3i.q_de(canvis, taula[columnes_q]).astype(np.float32)
        desa(cami, **desat)
    return ({e: desat[f"e{i}"] for i, e in enumerate(t3.ESCENARIS)}, desat["prior"],
            {e: desat[f"q{i}"] for i, e in enumerate(t3.ESCENARIS)})


def graella(tasca: tuple[str, str]) -> list[dict]:
    """Un partit i un escenari: A context amb el decodificador d'ara; A aturades amb la q de la T3i i A amb
    SkillCorner amb la seva, totes dues amb la graella de la T3j."""
    nom, escenari = tasca
    p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[escenari])
    comu = {"partit": nom, "font": p.font, "escenari": escenari}
    probes, prior = t3e.probabilitats(nom, entrena=False)
    files = []
    for lam, d_min in itertools.product(decodifica.GRAELLA_LAMBDA, decodifica.GRAELLA_DMIN):
        pred = decodifica.per_trams(probes[escenari].astype(float), prior, p.trams, lam, d_min)
        files.append({**comu, "metode": t3e.CONTEXT, "w": math.nan, "lam": lam, "d_min": d_min,
                      **avalua.puntua(p, pred)})
    for metode, (probes, prior, q) in amb_q(nom).items():
        relativa = log_relativa(probes[escenari].astype(float), prior)
        for w, lam, d_min in itertools.product(t3j.WS, t3j.LAMS, t3j.DMINS):
            pred = t3i.per_trams(relativa, q[escenari].astype(float), p.trams, w, lam, d_min)
            files.append({**comu, "metode": metode, "w": w, "lam": lam, "d_min": d_min, **avalua.puntua(p, pred)})
    return files


def amb_q(nom: str) -> dict[str, tuple[dict, np.ndarray, dict]]:
    """Les probabilitats, el prior i la q dels dos mètodes amb cost."""
    probes, prior = t3k.probabilitats(nom, entrena=False)
    return {t3k.ATURADES: (probes, prior, t3i.probabilitats(nom, entrena=False)),
            SKILLCORNER: probabilitats(nom, entrena=False)}


def tria_sense_mirar(files: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Les files de cada mètode a cada partit, amb els paràmetres triats amb els altres nou als escenaris ×¼. També
    les triades."""
    triats, triades = [], {}
    for prova in fonts.NOMS:
        triades[prova] = {}
        for metode in METODES:
            seu = files[files["metode"] == metode]
            columnes = t3k.parametres(metode)
            millor = t3.millor(seu[seu["partit"] != prova], columnes)
            del_partit = seu[seu["partit"] == prova]
            tria = np.logical_and.reduce([del_partit[c] == v for c, v in zip(columnes, millor)])
            triats.append(del_partit[tria])
            triades[prova][metode] = tuple(int(v) if c == "d_min" else float(v) for c, v in zip(columnes, millor))
    return pd.concat(triats, ignore_index=True), triades


def encert(tasca: tuple[str, str]) -> list[dict]:
    """Un partit i un escenari ×¼: a les possessions H o A de la veritat, la part de les imatges on l'equip més probable
    és el de la veritat, per mètode, durada de la possessió i si la pilota es veu (abans de decodificar)."""
    nom, escenari = tasca
    p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[escenari])
    gt = p.veritat.astype(np.int8)
    vista = ~np.isnan(p.tracking.pilota[:, 0])
    durada = np.full(p.n, np.nan)
    for s, e, _ in pm.possession_spells(gt, avalua.trams_valids(p)):
        durada[s:e] = (e - s) / pm.FPS
    tram = pd.cut(durada, DURADES, labels=NOMS_DURADA, right=False)
    dins = ~np.isnan(durada)
    files = []
    for metode, (probes, _, _) in amb_q(nom).items():
        bo = np.asarray(model.CLASSES)[probes[escenari].argmax(1)] == gt
        t = pd.DataFrame({"tram": tram[dins], "pilota": vista[dins], "bo": bo[dins]})
        files += [{"partit": nom, "escenari": escenari, "metode": metode, "durada": d, "pilota": bool(v),
                   "encert": float(g["bo"].mean()), "imatges": len(g)}
                  for (d, v), g in t.groupby(["tram", "pilota"], observed=True)]
    return files


def veritat(nom: str) -> dict:
    """Per saber-ho: com és la veritat d'un partit (net)."""
    p = fonts.partit(nom)
    trams = avalua.trams_valids(p)
    v = p.veritat.astype(np.int8)
    dins = np.zeros(p.n, bool)
    for a, b in trams:
        dins[a:b] = True
    viva = np.isin(v, (pm.H, pm.A))
    durades = np.array([(e - s) / pm.FPS for s, e, _ in pm.possession_spells(v, trams)])
    minuts = dins.sum() / pm.FPS / 60
    return {"partit": nom, "font": p.font, "sense_veritat": float(1 - dins.mean()), "d": float((v[dins] == pm.D).mean()),
            "possessions_min": len(durades) / minuts, "durada_mediana": float(np.median(durades)),
            "menys_2s": float((durades < 2).mean()), "pilota_viva": float(np.isfinite(p.tracking.pilota[viva, 0]).mean())}


def markdown(c: pd.DataFrame, c_aturades: pd.DataFrame, metodes: pd.DataFrame, enc: pd.DataFrame, ver: pd.DataFrame,
             triades: dict, passa: dict[str, bool]) -> str:
    ordre = list(METODES)
    linies = ["# Banc obert · Més partits per entrenar, els de SkillCorner (T3l)", "",
              "Generat amb `uv run python -I -m banc.model_a_skillcorner`. Dades obertes: es proven els 7 partits de DFL",
              "(IDSSE, CC BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora; s'entrena també amb els 20 de",
              "SkillCorner Open Data (A-League 2024/25, MIT), que no es proven mai. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3l», i la capçalera de `banc/model_a_skillcorner.py`.", "",
              f"**{t3e.CONTEXT}** és el model de la cadena (T3e), amb el decodificador d'ara. **{t3k.ATURADES}** és el de la",
              f"T3k. **{SKILLCORNER}** és {t3k.ATURADES} amb tots els models entrenats també amb SkillCorner. Tots tenen",
              "els paràmetres del decodificador triats amb els altres nou partits als escenaris ×¼.", "",
              "## L'spellF1 i el macroF1 de cada mètode (mitjana dels deu partits)", ""]
    for columna, nom in (("spell_f1", "spellF1"), ("macro_f1", "macroF1")):
        t = metodes.pivot_table(index="escenari", columns="metode", values=columna, sort=False)[ordre]
        linies += [f"**{nom}**", "", "| escenari | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 1) + "|"]
        linies += [f"| {e} | " + " | ".join(f"{x:.3f}" for x in f) + " |" for e, f in t.iterrows()]
        linies.append("")
    linies += [f"## {SKILLCORNER} contra {t3e.CONTEXT} (spellF1): el criteri", "",
               *t3b._taula(c, SKILLCORNER, t3e.CONTEXT), "", *t3b._criteris(passa, False),
               f"## {SKILLCORNER} contra {t3k.ATURADES} (spellF1), només per saber-ho", "",
               "El mateix, sense els partits de SkillCorner: la diferència és el que hi afegeixen.", "",
               *t3i._comparacio(c_aturades, SKILLCORNER, t3k.ATURADES), "",
               "## Per font (spellF1, mitjana dels partits de cada font), només per saber-ho", "",
               "| escenari | font | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 2) + "|"]
    per_font = metodes.pivot_table(index=["escenari", "font"], columns="metode", values="spell_f1", sort=False)[ordre]
    linies += [f"| {e} | {f} | " + " | ".join(f"{x:.3f}" for x in fila) + " |" for (e, f), fila in per_font.iterrows()]
    linies += ["", "## L'encert de l'equip abans de decodificar (escenaris ×¼), només per saber-ho", "",
               "A les imatges de les possessions de la veritat, la part on l'equip més probable és el de la veritat,",
               "per durada de la possessió i segons si la pilota es veu.", "",
               "| durada | pilota | " + " | ".join(ordre[1:]) + " |", "|---" * (len(ordre) + 1) + "|"]
    pes = enc.assign(bons=enc["encert"] * enc["imatges"]).groupby(["durada", "pilota", "metode"], sort=False)
    taxa = (pes["bons"].sum() / pes["imatges"].sum()).unstack()[ordre[1:]]
    linies += [f"| {d} | {'sí' if v else 'no'} | " + " | ".join(f"{x:.3f}" for x in fila) + " |"
               for (d, v), fila in taxa.iterrows()]
    linies += ["", "## La veritat de cada font (els partits nets), només per saber-ho", "",
               "*Sense veritat*: la part de les imatges de les parts que no es puntua ni s'aprèn (a SkillCorner, sobretot",
               "les repeticions de la retransmissió, on no hi ha cap jugador). La resta, sobre les que tenen veritat.", "",
               "| font | partits | sense veritat | pilota morta | possessions per minut | durada mediana (s) | "
               "de menys de 2 s | pilota vista, en joc |", "|---|---|---|---|---|---|---|---|"]
    for font, g in ver.groupby("font", sort=False):
        linies.append(f"| {font} | {len(g)} | {g['sense_veritat'].mean():.3f} | {g['d'].mean():.3f} | "
                      f"{g['possessions_min'].mean():.2f} | {g['durada_mediana'].mean():.2f} | {g['menys_2s'].mean():.3f} | "
                      f"{g['pilota_viva'].mean():.3f} |")
    linies += ["", "## Possessions predites per cada real (mitjana dels deu partits), només per saber-ho", "",
               "| escenari | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 1) + "|"]
    rati = (metodes["possessions"] / metodes["possessions_reals"]).groupby(
        [metodes["escenari"], metodes["metode"]], sort=False).mean().unstack()[ordre]
    linies += [f"| {e} | " + " | ".join(f"{x:.2f}" for x in f) + " |" for e, f in rati.iterrows()]
    linies += ["", "## Els paràmetres triats (cada partit, amb els altres nou)", ""]
    compta: dict[str, int] = {}
    for t in triades.values():
        trossos = []
        for m, valors in t.items():
            noms = dict(zip(t3k.parametres(m), valors))
            w = f"w = {noms['w']:g}, " if "w" in noms else ""
            trossos.append(f"{m}: {w}λ = {noms['lam']:g}, durada mínima {noms['d_min']}")
        clau_ = " · ".join(trossos)
        compta[clau_] = compta.get(clau_, 0) + 1
    linies += [f"- {k} ({n} partits)" for k, n in compta.items()]
    return "\n".join(linies + [""])


def clau() -> str:
    """El que fa les probabilitats d'A amb SkillCorner: les claus d'A aturades i de la q, els partits, el lector de
    SkillCorner i això."""
    h = hashlib.sha256((t3k.CLAU + t3i.CLAU + repr((t3e.GRUPS, fonts.NOMS, EXTRA, partit.VERSIO))).encode())
    h.update(Path(skillcorner.__file__).read_bytes())
    for funcio in (grups, per_entrenar, primer_de_la_prova, primer_del_grup, mostres_segon_i_q, probabilitats):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + t3k.clau_dels_resultats()).encode())
    for modul in (t3k, t3j, t3i, t3h, t3f, t3e, t3b, t3, decodifica, dt, avalua, degrada):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def refes_skillcorner() -> None:
    """La memòria cau dels partits de SkillCorner, refeta si el lector és més nou."""
    lector = Path(skillcorner.__file__).stat().st_mtime
    for nom in EXTRA:
        cami = fonts.DIR_CAU / f"{nom}.npz"
        if cami.exists() and cami.stat().st_mtime < lector:
            cami.unlink()
    fonts.prepara(EXTRA, processos=8)


def main() -> None:
    from banc import model_a_skillcorner as aquest      # pel nom del mòdul, perquè els processos fills el trobin

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=2, help="models alhora (cadascun fa servir 8 fils)")
    args = ap.parse_args()
    refes_skillcorner()
    for nom in fonts.NOMS:                              # les d'A context, d'A aturades i la q de la T3i: abans cal fer-les
        t3e.probabilitats(nom, entrena=False)
        t3k.probabilitats(nom, entrena=False)
        t3i.probabilitats(nom, entrena=False)
    with ProcessPoolExecutor(max_workers=args.processos_models) as feina:
        tasques = [(nom, i) for nom in fonts.NOMS for i in range(t3e.GRUPS)]
        for (nom, i), _ in zip(tasques, feina.map(aquest.primer_del_grup, tasques)):
            print(f"· {nom}: el primer del grup {i} fet", flush=True)
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.primer_de_la_prova, fonts.NOMS)):
            print(f"· {nom}: el primer fet", flush=True)
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.probabilitats, fonts.NOMS)):
            print(f"· {nom}: {SKILLCORNER} fet", flush=True)
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        files = pd.DataFrame([f for tros in feina.map(aquest.graella, itertools.product(fonts.NOMS, t3.ESCENARIS))
                              for f in tros])
        enc = pd.DataFrame([f for tros in feina.map(aquest.encert, itertools.product(fonts.NOMS, t3.QUARTS))
                            for f in tros])
        ver = pd.DataFrame(list(feina.map(aquest.veritat, fonts.NOMS + EXTRA)))
    metodes, triades = tria_sense_mirar(files)
    c = t3b.comparacio(metodes, SKILLCORNER, t3e.CONTEXT)
    c_aturades = t3b.comparacio(metodes, SKILLCORNER, t3k.ATURADES)
    passa = t3b.compleix(c)
    desa_ = {"clau": clau_dels_resultats(), "passa": passa, "comparacio": t3.registres(c),
             "comparacio_aturades": t3.registres(c_aturades), "encert": t3.registres(enc),
             "veritat": t3.registres(ver), "triades": triades, "files": t3.registres(files)}
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-a-skillcorner.json").write_text(json.dumps(desa_, indent=1, default=float, allow_nan=False))
    (DIR_RESULTATS / "model-a-skillcorner.md").write_text(markdown(c, c_aturades, metodes, enc, ver, triades, passa))
    print((DIR_RESULTATS / "model-a-skillcorner.md").read_text())


if __name__ == "__main__":
    main()
