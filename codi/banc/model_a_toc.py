"""La veritat del banc, al primer toc (T3q del pla per tocs, `docs/pla-tocs.md`, «T3q»; D-48).

    cd codi && uv run python -I -m banc.model_a_toc [--nomes-pas-1] [--processos 12] [--processos-models 4]

La veritat de toc és la de `banc/veritat_toc.py`, i a partir d'ara el banc hi puntua.

1. **Pas 1, només per saber-ho, sense entrenar res:** A xarxes tal com és, amb les probabilitats i les q de la
   memòria cau de la T3p (als deu escenaris de la T3 i a «partit ×¼»). El decodificador és el de la cadena: es tria
   amb els altres nou, als quatre ×¼, a la veritat de sempre, i ha de ser el que va triar la T3p. Es puntua a la
   veritat de sempre i a la de toc. Si als quatre ×¼ hi perd menys de 0,01 de mitjana, el Pas 2 no s'entrena.
2. **Pas 2: A toc.** A xarxes tal qual, amb la veritat de toc per entrenar, per triar el decodificador i per puntuar:
   el primer, les cinc xarxes, el segon i el de canvis, amb els sis escenaris d'ara (`dades/banc/a-toc/`). El
   decodificador, amb la graella de la T3j, triat amb els altres nou als quatre ×¼ a la veritat de toc.
3. **El criteri** del pla: A toc contra A xarxes, puntuats tots dos a la veritat de toc. Als quatre ×¼ guanya
   clarament; al net, als ×1, al soroll2 i a «partit ×¼», no perd. Només per saber-ho: tots dos a la veritat de
   sempre, i A xarxes amb el decodificador triat a la veritat de toc.

Escriu `resultats/model-a-toc.json` i `resultats/model-a-toc.md`. Tot són dades obertes. Els mòduls d'abans no es
toquen.
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
from dataclasses import replace
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from banc import avalua, fonts, model_a
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_canvis2 as t3j
from banc import model_a_contacte as t3h
from banc import model_a_context as t3e
from banc import model_a_partit as mp
from banc import model_a_possessio as t3f
from banc import model_a_quart as t3b
from banc import model_a_xarxa as t3m
from banc import model_a_xarxes as t3o
from banc import veritat_toc as vt
from banc.partit import PartitBanc
from cadena import model, xarxa, xarxes
from possessio.decodificacio import log_relativa

ESCENARIS = mp.ESCENARIS                            # els deu de la T3 i «partit ×¼»
QUARTS = t3.QUARTS
SIS = t3o.ENTRENAMENT
XARXES = t3o.XARXES
A_TOC = "A toc"
XARXES_TOC = "A xarxes, decodificador de toc"      # només per saber-ho
SEMPRE, TOC = "sempre", "toc"
ALTRES = ((A_TOC, XARXES, SEMPRE), (XARXES_TOC, XARXES, TOC), (A_TOC, XARXES_TOC, TOC))   # només per saber-ho
PERD_MINIM = 0.01                                   # Pas 1: si als ×¼ perd menys, el Pas 2 no s'entrena
DIR_CAU = fonts.DIR_CAU / "a-toc"
DIR_RESULTATS = t3.DIR_RESULTATS


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


def cau(peca: str, *qui: object) -> Path:
    return DIR_CAU / f"{peca}-{'-'.join(map(str, qui))}.npz"


def degradat(nom: str, escenari: str) -> PartitBanc:
    """El partit `nom` a l'escenari, amb la veritat de toc (la degradació només mira la D i la X, que no canvien)."""
    return replace(mp.degradat(nom, escenari), veritat=vt.veritat(nom))


@functools.cache
def mostres_primer(nom: str, escenari: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Les mostres del primer d'A contacte (T3h), amb la tria de la T3f, a la veritat de toc (un cop per procés)."""
    p = degradat(nom, escenari)
    return t3f.mostres(p, t3h.taula_primer(p))


def entrena_primer(noms: list[str]) -> lgb.Booster:
    """Com `mp.entrena_primer` amb els sis escenaris, a la veritat de toc."""
    m = [mostres_primer(nom, e) for nom in noms for e in SIS]
    return model.entrena(pd.concat([x for x, _ in m], ignore_index=True), np.concatenate([y for _, y in m]))


def primer_del_grup(tasca: tuple[str, int]) -> dict[tuple[str, str], np.ndarray]:
    """Les del primer als partits del grup `i` de `prova`, als sis escenaris, entrenat amb els altres sis."""
    prova, i = tasca
    claus = mp.claus_del_grup(prova, i, SIS)
    cami = cau("primer-grup", prova, i)
    desat = llegeix(cami)
    if desat is None:
        entrenat = entrena_primer(t3m.per_entrenar_el_grup(prova, i))
        desat = {clau_: model.probabilitats(entrenat, t3h.taula_primer(degradat(nom, e))).astype(np.float32)
                 for (nom, e), clau_ in claus.items()}
        desa(cami, **desat)
    return {qui: desat[nom] for qui, nom in claus.items()}


def primer_de_la_prova(prova: str) -> dict[str, np.ndarray]:
    """Les del primer al partit `prova`, a tots els escenaris, entrenat amb els altres nou."""
    cami = cau("primer", prova)
    desat = llegeix(cami)
    if desat is None:
        entrenat = entrena_primer([nom for nom in fonts.NOMS if nom != prova])
        desat = {f"e{i}": model.probabilitats(entrenat, t3h.taula_primer(degradat(prova, e))).astype(np.float32)
                 for i, e in enumerate(ESCENARIS)}
        desa(cami, **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(ESCENARIS)}


def entrena_xarxes(noms: list[str]) -> tuple[tuple[xarxa.Xarxa, ...], list[list[float]]]:
    """Com `mp.entrena_xarxes` amb els sis escenaris, a la veritat de toc."""
    xs, ys = [], []
    for nom in noms:
        for e in SIS:
            p = degradat(nom, e)
            files = t3f.tria(p.veritat, avalua.trams_valids(p))
            x, y = xarxa.mostres(p.tracking, p.trams, files, p.veritat[files])
            xs.append(x)
            ys.append(y)
    x = np.concatenate(xs)
    del xs
    return xarxes.entrena(x, np.concatenate(ys))


def xarxes_del_grup(tasca: tuple[str, int]) -> dict[tuple[str, str], np.ndarray]:
    """La mitjana de les cinc xarxes als partits del grup `i` de `prova`, als sis escenaris, entrenades amb els
    altres sis."""
    prova, i = tasca
    claus = mp.claus_del_grup(prova, i, SIS)
    cami = cau("xarxes-grup", prova, i)
    desat = llegeix(cami)
    if desat is None:
        entrenades, perdues = entrena_xarxes(t3m.per_entrenar_el_grup(prova, i))
        desat = {}
        for (nom, e), clau_ in claus.items():
            p = degradat(nom, e)
            desat[clau_] = xarxes.probabilitats(entrenades, p.tracking, p.trams).astype(np.float32)
        desa(cami, perdues=np.array(perdues), **desat)
    return {qui: desat[nom] for qui, nom in claus.items()}


def xarxes_de_la_prova(prova: str) -> dict[str, np.ndarray]:
    """La mitjana de les cinc xarxes al partit `prova`, a tots els escenaris, entrenades amb els altres nou."""
    cami = cau("xarxes", prova)
    desat = llegeix(cami)
    if desat is None:
        entrenades, perdues = entrena_xarxes([nom for nom in fonts.NOMS if nom != prova])
        desat = {}
        for i, e in enumerate(ESCENARIS):
            p = degradat(prova, e)
            desat[f"e{i}"] = xarxes.probabilitats(entrenades, p.tracking, p.trams).astype(np.float32)
        desa(cami, perdues=np.array(perdues), **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(ESCENARIS)}


def mostres_segon(prova: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Com `mp.mostres_segon` amb els sis escenaris, a la veritat de toc."""
    primers, de_les_xarxes = {}, {}
    for i in range(t3e.GRUPS):
        primers |= primer_del_grup((prova, i))
        de_les_xarxes |= xarxes_del_grup((prova, i))
    xs, ys = [], []
    for (nom, e), primer in primers.items():
        p = degradat(nom, e)
        x, y = t3f.mostres(p, t3m.taula_segon(p, primer.astype(float), de_les_xarxes[(nom, e)].astype(float)))
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def segon(prova: str, entrena: bool = True) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Les d'A toc al partit `prova`, a tots els escenaris, i el prior. Amb `entrena=False`, només les llegeix de la
    memòria cau, i si no hi són o són d'un altre codi, s'atura."""
    cami = cau("segon", prova)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les probabilitats del segon d'{A_TOC} de {prova}, o són d'un altre codi")
        x, y = mostres_segon(prova)
        entrenat, prior = model.entrena(x, y), model.prior(y)
        del x
        primers, de_les_xarxes = primer_de_la_prova(prova), xarxes_de_la_prova(prova)
        desat = {"prior": prior}
        for i, e in enumerate(ESCENARIS):
            p = degradat(prova, e)
            taula = t3m.taula_segon(p, primers[e].astype(float), de_les_xarxes[e].astype(float))
            desat[f"e{i}"] = model.probabilitats(entrenat, taula).astype(np.float32)
        desa(cami, **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(ESCENARIS)}, desat["prior"]


def mostres_q(prova: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Com `mp.mostres_q` amb els sis escenaris, a la veritat de toc."""
    primers = {}
    for i in range(t3e.GRUPS):
        primers |= primer_del_grup((prova, i))
    xs, ys = [], []
    for (nom, e), primer in primers.items():
        p = degradat(nom, e)
        x, y = t3i.mostres(p, t3h.taula_segon(p, primer.astype(float)))
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def q(prova: str, entrena: bool = True) -> dict[str, np.ndarray]:
    """Les q del de canvis d'A toc al partit `prova`, a tots els escenaris. Amb `entrena=False`, només les llegeix de
    la memòria cau, i si no hi són o són d'un altre codi, s'atura."""
    cami = cau("q", prova)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les q d'{A_TOC} de {prova}, o són d'un altre codi")
        x, y = mostres_q(prova)
        entrenat = lgb.train(t3i.PARAMS, lgb.Dataset(x, label=y, free_raw_data=True), num_boost_round=model.RONDES)
        del x
        primers = primer_de_la_prova(prova)
        desat = {}
        for i, e in enumerate(ESCENARIS):
            p = degradat(prova, e)
            desat[f"e{i}"] = t3i.q_de(entrenat, t3h.taula_segon(p, primers[e].astype(float))).astype(np.float32)
        desa(cami, **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(ESCENARIS)}


def de_qui(metode: str, nom: str) -> tuple[dict[str, np.ndarray], np.ndarray, dict[str, np.ndarray]]:
    """Les probabilitats, el prior i les q d'A xarxes (de la memòria cau de la T3p) o d'A toc."""
    if metode == XARXES:
        probes, prior = mp.segon((nom, SIS), entrena=False)
        return probes, prior, mp.q((nom, SIS), entrena=False)
    probes, prior = segon(nom, entrena=False)
    return probes, prior, q(nom, entrena=False)


def graella(tasca: tuple[str, str, tuple[str, ...]]) -> list[dict]:
    """Un partit, un escenari i els mètodes: cada punt de la graella de la T3j, puntuat a les dues veritats."""
    nom, escenari, metodes = tasca
    de_sempre = mp.degradat(nom, escenari)
    partits = {SEMPRE: de_sempre, TOC: replace(de_sempre, veritat=vt.veritat(nom))}
    files = []
    for metode in metodes:
        probes, prior, q_ = de_qui(metode, nom)
        relativa = log_relativa(probes[escenari].astype(float), prior)
        for w, lam, d_min in itertools.product(t3j.WS, t3j.LAMS, t3j.DMINS):
            pred = t3i.per_trams(relativa, q_[escenari].astype(float), de_sempre.trams, w, lam, d_min)
            for veritat, p in partits.items():
                files.append({"partit": nom, "font": p.font, "escenari": escenari, "metode": metode,
                              "veritat": veritat, "w": w, "lam": lam, "d_min": d_min, **avalua.puntua(p, pred)})
    return files


def tria_sense_mirar(files: pd.DataFrame, metode: str, veritat: str, com: str) -> tuple[pd.DataFrame, dict]:
    """De `metode`, a cada partit, les files (a les dues veritats) amb els paràmetres triats amb els altres nou als
    quatre ×¼ a `veritat`; amb el nom `com`. També les triades."""
    seu = files[files["metode"] == metode]
    triats, triades = [], {}
    for prova in fonts.NOMS:
        mira = seu[(seu["partit"] != prova) & (seu["veritat"] == veritat)]
        millor_ = mp.millor(mira, ["w", "lam", "d_min"], QUARTS)
        del_partit = seu[seu["partit"] == prova]
        tria = (del_partit["w"] == millor_[0]) & (del_partit["lam"] == millor_[1]) & (del_partit["d_min"] == millor_[2])
        triats.append(del_partit[tria].assign(metode=com))
        triades[prova] = (float(millor_[0]), float(millor_[1]), int(millor_[2]))
    return pd.concat(triats, ignore_index=True), triades


def triades_t3p() -> dict[str, dict[str, list]]:
    """El decodificador triat a cada partit pel banc de la T3p."""
    return json.loads((mp.DIR_RESULTATS / "model-a-partit.json").read_text())["triades"]


def comprova_el_decodificador(triades: dict) -> None:
    """Pas 1: A xarxes, amb el decodificador que va triar la T3p a cada partit."""
    de_la_t3p = triades_t3p()
    for prova, triat in triades.items():
        if list(triat) != list(de_la_t3p[prova][XARXES]):
            raise RuntimeError(f"{prova}: el decodificador d'{XARXES} no és el de la T3p ({triat})")


def comparacio(metodes: pd.DataFrame, nou: str, contra: str, veritat: str, amb_criteri: bool) -> pd.DataFrame:
    """Per escenari, a `veritat`: `nou` contra `contra`; amb el criteri del pla, si `amb_criteri` (als quatre ×¼,
    guanya clarament; a la resta, no perd)."""
    files = []
    for escenari in ESCENARIS:
        tria = metodes[(metodes["escenari"] == escenari) & (metodes["veritat"] == veritat)].pivot_table(
            index="partit", columns="metode", values="spell_f1")
        dif = (tria[nou] - tria[contra]).to_numpy()
        font = metodes.groupby("partit")["font"].first().loc[tria.index].to_numpy()
        baix, alt = model_a.interval(dif, font)
        guanya = int((dif > 0).sum())
        if escenari in QUARTS:
            criteri = "guanya clarament"
            passa = bool(dif.mean() > t3.SOROLL and baix > 0 and guanya >= t3.GUANYA_MINIM)
        else:
            criteri, passa = "no perd", bool(dif.mean() >= -t3.SOROLL)
        files.append({"escenari": escenari, "contra": tria[contra].mean(), "nou": tria[nou].mean(),
                      "diferencia": dif.mean(), "baix": baix, "alt": alt, "guanya": guanya, "partits": len(dif),
                      "criteri": criteri if amb_criteri else "", "passa": passa if amb_criteri else True})
    return pd.DataFrame(files)


def pas_1(de_xarxes: pd.DataFrame) -> pd.DataFrame:
    """A xarxes a la veritat de toc contra la de sempre, per escenari (diferència: toc − sempre)."""
    return comparacio(de_xarxes.assign(metode=de_xarxes["veritat"], veritat=TOC), TOC, SEMPRE, TOC, amb_criteri=False)


def perd_als_quarts(c1: pd.DataFrame) -> float:
    return float(-c1[c1["escenari"].isin(QUARTS)]["diferencia"].mean())


def compleix(c: pd.DataFrame) -> dict[str, bool]:
    quarts = c["escenari"].isin(QUARTS)
    return {"quarts": bool(c[quarts]["passa"].all()), "altres": bool(c[~quarts]["passa"].all())}


def _criteris(passa: dict[str, bool]) -> list[str]:
    def marca(v: bool) -> str:
        return "✓" if v else "✗"

    return ["| | Passa si | |", "|---|---|---|",
            f"| Els quatre ×¼ | guanya clarament a cada un (diferència > {t3.SOROLL}, interval > 0, "
            f"{t3.GUANYA_MINIM} partits de 10 o més) | {marca(passa['quarts'])} |",
            f"| El net, els ×1, el soroll2 i «{mp.PARTIT}» | no perd a cap (diferència ≥ −{t3.SOROLL}) | "
            f"{marca(passa['altres'])} |", "", f"**{'Passa' if all(passa.values()) else 'No passa'}.**", ""]


def _mitjanes(metodes: pd.DataFrame, ordre: list[str]) -> list[str]:
    linies = []
    for veritat in (TOC, SEMPRE):
        t = metodes[metodes["veritat"] == veritat].pivot_table(index="escenari", columns="metode", values="spell_f1",
                                                              sort=False)
        t = t[[m for m in ordre if m in t.columns]]
        linies += [f"**spellF1 a la veritat {'de toc' if veritat == TOC else 'de sempre'}**", "",
                   "| escenari | " + " | ".join(t.columns) + " |", "|---" * (len(t.columns) + 1) + "|"]
        linies += [f"| {e} | " + " | ".join(f"{x:.3f}" for x in f) + " |" for e, f in t.iterrows()]
        linies.append("")
    return linies


def nom_de(nou: str, contra: str, veritat: str) -> str:
    return f"{nou} contra {contra}, a la veritat {'de toc' if veritat == TOC else 'de sempre'}"


def markdown(c1: pd.DataFrame, metodes: pd.DataFrame, triades: dict, c: pd.DataFrame | None,
             altres: dict[tuple[str, str, str], pd.DataFrame], passa: dict[str, bool] | None) -> str:
    perd = perd_als_quarts(c1)
    linies = ["# Banc obert · La veritat del banc, al primer toc (T3q)", "",
              "Generat amb `uv run python -I -m banc.model_a_toc`. Dades obertes: 7 partits de DFL (IDSSE, CC BY 4.0)",
              "i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el criteri:",
              "`docs/pla-tocs.md`, «T3q», i la capçalera de `banc/model_a_toc.py`. La veritat de toc:",
              "`resultats/veritat-toc.md`.", "",
              f"## Pas 1: {XARXES} tal com és, a la veritat de toc", "",
              "El decodificador és el de la cadena, el mateix que va triar la T3p a cada partit (✓ comprovat).", "",
              *t3i._comparacio(c1, "a la veritat de toc", "a la de sempre"), "",
              f"Als quatre ×¼ hi perd {perd:+.3f} de mitjana. "
              + (f"És menys de {PERD_MINIM}: el Pas 2 no s'entrena." if perd < PERD_MINIM
                 else f"És {PERD_MINIM} o més: el Pas 2 s'entrena."), ""]
    if c is None:
        return "\n".join(linies + _mitjanes(metodes, [XARXES]))
    linies += [f"## {A_TOC} contra {XARXES}, a la veritat de toc (spellF1): el criteri", "",
               *t3b._taula(c, A_TOC, XARXES), "", *_criteris(passa)]
    for (nou, contra, veritat), taula in altres.items():
        linies += [f"## {nom_de(nou, contra, veritat)}, només per saber-ho", "", *t3i._comparacio(taula, nou, contra),
                   ""]
    linies += ["## L'spellF1 de cada mètode (mitjana dels deu partits)", "",
               *_mitjanes(metodes, [XARXES, XARXES_TOC, A_TOC]), "## Els decodificadors triats", ""]
    for metode, t in triades.items():
        compta: dict[str, int] = {}
        for w, lam, d_min in t.values():
            clau_ = f"w = {w:g}, λ = {lam:g}, durada mínima {d_min}"
            compta[clau_] = compta.get(clau_, 0) + 1
        linies.append(f"- **{metode}:** " + "; ".join(f"{k} ({n} partits)" for k, n in compta.items()))
    return "\n".join(linies + [""])


def clau() -> str:
    """El que fa les probabilitats d'aquí: les peces d'A xarxes, la veritat de toc i això."""
    h = hashlib.sha256((mp.CLAU + vt.CLAU + repr((SIS, ESCENARIS))).encode())
    for funcio in (degradat, mostres_primer, entrena_primer, primer_del_grup, primer_de_la_prova, entrena_xarxes,
                   xarxes_del_grup, xarxes_de_la_prova, mostres_segon, segon, mostres_q, q):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + mp.clau_dels_resultats()).encode())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def pas_2(feina: ProcessPoolExecutor) -> None:
    """A toc: els grups, i després el partit que es prova."""
    from banc import model_a_toc as aquest           # pel nom del mòdul, perquè els processos fills el trobin

    grups = [(nom, i) for nom in fonts.NOMS for i in range(t3e.GRUPS)]
    for peca, fes in (("el primer", aquest.primer_del_grup), ("les xarxes", aquest.xarxes_del_grup)):
        for (nom, i), _ in zip(grups, feina.map(fes, grups)):
            print(f"· Pas 2, {nom}: {peca} del grup {i} fet", flush=True)
    for peca, fes in (("el primer", aquest.primer_de_la_prova), ("les xarxes", aquest.xarxes_de_la_prova),
                      ("el segon", aquest.segon), ("el de canvis", aquest.q)):
        for nom, _ in zip(fonts.NOMS, feina.map(fes, fonts.NOMS)):
            print(f"· Pas 2, {nom}: {peca} fet", flush=True)


def files_de(metodes: tuple[str, ...], processos: int) -> pd.DataFrame:
    from banc import model_a_toc as aquest

    tasques = [(nom, e, metodes) for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    with ProcessPoolExecutor(max_workers=processos) as feina:
        return pd.DataFrame([f for tros in feina.map(aquest.graella, tasques) for f in tros])


def escriu(contingut: dict, md: str) -> None:
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-a-toc.json").write_text(json.dumps(contingut, indent=1, default=float, allow_nan=False))
    (DIR_RESULTATS / "model-a-toc.md").write_text(md)
    print(md)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--nomes-pas-1", action="store_true", help="només el Pas 1")
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=4, help="models alhora")
    args = ap.parse_args()
    for nom in fonts.NOMS:
        de_qui(XARXES, nom)
        vt.veritat(nom)
    files = files_de((XARXES,), args.processos)
    de_xarxes, triades_xarxes = tria_sense_mirar(files, XARXES, SEMPRE, XARXES)
    comprova_el_decodificador(triades_xarxes)
    c1 = pas_1(de_xarxes)
    contingut = {"clau": clau_dels_resultats(), "pas_1": t3.registres(c1), "perd_als_quarts": perd_als_quarts(c1),
                 "triades": {XARXES: triades_xarxes}}
    if args.nomes_pas_1 or perd_als_quarts(c1) < PERD_MINIM:
        escriu(contingut | {"files": t3.registres(files)}, markdown(c1, de_xarxes, {}, None, {}, None))
        return
    with ProcessPoolExecutor(max_workers=args.processos_models) as feina:
        pas_2(feina)
    files = pd.concat([files, files_de((A_TOC,), args.processos)], ignore_index=True)
    de_toc, triades_toc = tria_sense_mirar(files, A_TOC, TOC, A_TOC)
    xarxes_toc, triades_xarxes_toc = tria_sense_mirar(files, XARXES, TOC, XARXES_TOC)
    metodes = pd.concat([de_xarxes, xarxes_toc, de_toc], ignore_index=True)
    c = comparacio(metodes, A_TOC, XARXES, TOC, amb_criteri=True)
    passa = compleix(c)
    altres = {qui: comparacio(metodes, *qui, amb_criteri=False) for qui in ALTRES}
    triades = {XARXES: triades_xarxes, XARXES_TOC: triades_xarxes_toc, A_TOC: triades_toc}
    contingut |= {"passa": passa, "comparacio": t3.registres(c), "triades": triades, "files": t3.registres(files),
                  "altres": {nom_de(*qui): t3.registres(t) for qui, t in altres.items()}}
    escriu(contingut, markdown(c1, metodes, triades, c, altres, passa))


if __name__ == "__main__":
    main()
