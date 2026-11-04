"""Les xarxes veuen els dos equips sencers (T3v del pla per tocs, `docs/pla-tocs.md`, «T3v»; D-54).

    cd codi && uv run python -I -m banc.model_a_equips [--processos 12] [--processos-models 4]

A sense pilota tal qual, amb una sola diferència: les cinc xarxes també veuen tots els jugadors dels dos equips
(`cadena/xarxa_equips.py`). El primer i la q són els d'A xarxes, de la memòria cau de la T3p.

1. **En començar,** A xarxes i A sense pilota, amb la memòria cau, han de donar a cada punt de la graella i a les dues
   veritats l'spellF1 del banc de la T3t.
2. **Les xarxes noves:** les cinc de cada grup (entrenades amb els altres sis partits, per entrenar el segon) i les
   cinc del partit que es prova (amb els altres nou), amb les mostres d'A sense pilota. 200 xarxes
   (`dades/banc/a-equips/`).
3. **El segon,** entrenat com el d'A sense pilota, amb les probabilitats de les xarxes noves.
4. **El decodificador,** amb la graella de la T3j, triat amb els altres nou als quatre ×¼ a la veritat de toc.
5. **El criteri** del pla: A equips sencers contra A xarxes, a la veritat de toc. Si no passa, la regla del millor
   fins ara, contra A sense pilota. Només per saber-ho: per font, i on encerten l'equip les xarxes i el segon d'A sense
   pilota i els nous (on es veu la pilota i als forats, segons quant duren i segons si la possessió es veu algun cop
   amb pilota).

Escriu `resultats/model-a-equips.json` i `resultats/model-a-equips.md`. Tot són dades obertes. Els mòduls d'abans no es
toquen.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import itertools
import json
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from banc import analisi_t3p as t3p
from banc import analisi_t3q as t3q
from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_canvis2 as t3j
from banc import model_a_context as t3e
from banc import model_a_partit as mp
from banc import model_a_possessio as t3f
from banc import model_a_q as mq
from banc import model_a_quart as t3b
from banc import model_a_sense_pilota as msp
from banc import model_a_toc as mt
from banc import model_a_tocs_apresos as mta
from banc import model_a_xarxa as t3m
from banc import pilota_als_forats as paf
from banc import sostre_sense_pilota as ssp
from banc import veritat_toc as vt
from cadena import model, xarxa, xarxes
from cadena import xarxa_equips as xeq
from possessio.decodificacio import log_relativa

ESCENARIS = mp.ESCENARIS                            # els deu de la T3 i «partit ×¼»
SIS = mp.SIS
XARXES, XARXES_TOC = mt.XARXES, mt.XARXES_TOC       # A xarxes, amb el decodificador de la cadena i triat a la de toc
A_SENSE = msp.A_SENSE
A_EQUIPS = "A equips sencers"
SEMPRE, TOC = mt.SEMPRE, mt.TOC
FONTS = msp.FONTS
AMB_PILOTA, ALS_FORATS = msp.AMB_PILOTA, msp.ALS_FORATS
MAI, ALGUN_COP = f"{ALS_FORATS}, possessions que no es veuen mai", f"{ALS_FORATS}, possessions que es veuen algun cop"
ON = (*msp.ON, MAI, ALGUN_COP)
XARXES_SENSE, XARXES_NOVES = f"les xarxes d'{A_SENSE}", "les xarxes noves"
SEGON_SENSE, SEGON_NOU = f"el segon d'{A_SENSE}", "el segon nou"
QUI = (XARXES_SENSE, XARXES_NOVES, SEGON_SENSE, SEGON_NOU)
DIR_CAU = fonts.DIR_CAU / "a-equips"
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


def entrena_xarxes(noms: list[str]) -> tuple[tuple[xarxa.Xarxa, ...], list[list[float]]]:
    """Com `msp.entrena_xarxes`: les mateixes imatges i etiquetes, amb el que veuen les xarxes noves. Les mostres van
    directament a una sola matriu, per la memòria."""
    triades = {(nom, e): t3f.tria(p.veritat, avalua.trams_valids(p))
               for nom in noms for e in SIS for p in (mp.degradat(nom, e),)}
    x = np.empty((2 * sum(map(len, triades.values())), xeq.ENTRADES), np.float32)
    y = np.empty(len(x), np.int8)
    fet = 0
    for (nom, e), files in triades.items():
        p = mp.degradat(nom, e)
        x_, y_ = xeq.mostres(p.tracking, p.trams, files, p.veritat[files])
        x[fet:fet + len(x_)], y[fet:fet + len(y_)] = x_, y_
        fet += len(x_)
    return xarxes.entrena(x, y)


def xarxes_del_grup(tasca: tuple[str, int], entrena: bool = True) -> dict[tuple[str, str], np.ndarray]:
    """La mitjana de les cinc xarxes noves als partits del grup `i` de `prova`, als sis escenaris d'entrenament,
    entrenades amb els altres sis partits."""
    prova, i = tasca
    claus = mp.claus_del_grup(prova, i, SIS)
    cami = cau("xarxes-grup", prova, i)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les xarxes noves del grup {i} de {prova}, o són d'un altre codi")
        entrenades, perdues = entrena_xarxes(t3m.per_entrenar_el_grup(prova, i))
        desat = {}
        for (nom, e), clau_ in claus.items():
            p = mp.degradat(nom, e)
            desat[clau_] = xeq.probabilitats(entrenades, p.tracking, p.trams).astype(np.float32)
        desa(cami, perdues=np.array(perdues), **desat)
    return {qui: desat[nom] for qui, nom in claus.items()}


def xarxes_de_la_prova(prova: str, entrena: bool = True) -> dict[str, np.ndarray]:
    """La mitjana de les cinc xarxes noves al partit `prova`, a tots els escenaris, entrenades amb els altres nou."""
    cami = cau("xarxes", prova)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les xarxes noves de {prova}, o són d'un altre codi")
        entrenades, perdues = entrena_xarxes([nom for nom in fonts.NOMS if nom != prova])
        desat = {}
        for i, e in enumerate(ESCENARIS):
            p = mp.degradat(prova, e)
            desat[f"e{i}"] = xeq.probabilitats(entrenades, p.tracking, p.trams).astype(np.float32)
        desa(cami, perdues=np.array(perdues), **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(ESCENARIS)}


def mostres_segon(prova: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Com `msp.mostres_segon`: el primer de cada grup (de la memòria cau) i les xarxes noves del grup."""
    primers, de_les_xarxes = {}, {}
    for i in range(t3e.GRUPS):
        primers |= mp.primer_del_grup((prova, i, SIS))
        de_les_xarxes |= xarxes_del_grup((prova, i), entrena=False)
    xs, ys = [], []
    for (nom, e), primer in primers.items():
        p = mp.degradat(nom, e)
        x, y = t3f.mostres(p, t3m.taula_segon(p, primer.astype(float), de_les_xarxes[(nom, e)].astype(float)))
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def segon(prova: str, entrena: bool = True) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Les probabilitats d'A equips sencers al partit `prova`, a tots els escenaris, i el prior: com el segon d'A sense
    pilota (`msp.segon`), amb les xarxes noves. Amb `entrena=False`, només les llegeix de la memòria cau."""
    cami = cau("segon", prova)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les probabilitats del segon d'{A_EQUIPS} de {prova}, o són d'un altre codi")
        x, y = mostres_segon(prova)
        entrenat, prior = model.entrena(x, y), model.prior(y)
        del x
        primers = mp.primer_de_la_prova((prova, SIS))
        de_les_xarxes = xarxes_de_la_prova(prova, entrena=False)
        desat = {"prior": prior}
        for i, e in enumerate(ESCENARIS):
            p = mp.degradat(prova, e)
            taula = t3m.taula_segon(p, primers[e].astype(float), de_les_xarxes[e].astype(float))
            desat[f"e{i}"] = model.probabilitats(entrenat, taula).astype(np.float32)
        desa(cami, **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(ESCENARIS)}, desat["prior"]


def de_qui(metode: str, nom: str) -> tuple[dict[str, np.ndarray], np.ndarray, dict[str, np.ndarray]]:
    """Les probabilitats i el prior d'A xarxes (de la memòria cau de la T3p), d'A sense pilota (de la de la T3t) o
    d'A equips sencers, amb la q d'A xarxes."""
    if metode == XARXES:
        probes, prior = mp.segon((nom, SIS), entrena=False)
    elif metode == A_SENSE:
        probes, prior = msp.segon(nom, entrena=False)
    else:
        probes, prior = segon(nom, entrena=False)
    return probes, prior, mp.q((nom, SIS), entrena=False)


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


def mascares(vista: np.ndarray, valides: np.ndarray, toc: np.ndarray, trams: list[ssp.Tram]) -> dict[str, np.ndarray]:
    """Les de `msp.mascares` i, als forats, les possessions de la veritat que no es veuen mai amb pilota i les que sí
    (com a `pilota_als_forats.py`)."""
    out = msp.mascares(vista, valides)
    es_veu, _ = paf.possessions(toc, trams, vista)
    return {**out, MAI: out[ALS_FORATS] & (es_veu == paf.MAI), ALGUN_COP: out[ALS_FORATS] & (es_veu == paf.ALGUN_COP)}


def encerts(tasca: tuple[str, str]) -> list[dict]:
    """Un partit i un escenari: on encerten l'equip les xarxes i el segon d'A sense pilota i els nous."""
    nom, escenari = tasca
    de_sempre = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    trams = avalua.trams_valids(replace(de_sempre, veritat=toc))
    vista = ~np.isnan(de_sempre.tracking.pilota[:, 0])
    probes = {XARXES_SENSE: msp.xarxes_de_la_prova(nom, entrena=False)[escenari].astype(float),
              XARXES_NOVES: xarxes_de_la_prova(nom, entrena=False)[escenari].astype(float)}
    for qui, metode in ((SEGON_SENSE, A_SENSE), (SEGON_NOU, A_EQUIPS)):
        de_l_un, prior, _ = de_qui(metode, nom)
        probes[qui] = log_relativa(de_l_un[escenari].astype(float), prior)
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}
    files = []
    for on, mascara in mascares(vista, ssp.dins(len(toc), trams), toc, trams).items():
        for qui in QUI:
            n, e = ssp.encerts(probes[qui], toc, mascara)
            files.append({**comu, "on": on, "qui": qui, "n": n, "encerts": e})
    return files


def taula_encerts(t: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i on: quantes imatges hi ha d'un equip, i la part on cadascú hi encerta l'equip."""
    g = t.groupby(["escenari", "on", "qui"], sort=False)[["n", "encerts"]].sum()
    part = (g["encerts"] / g["n"]).unstack("qui")[list(QUI)]
    n = g["n"].xs(SEGON_NOU, level="qui").rename("n imatges")
    ordre = {**t3q.ORDRE, **{o: i for i, o in enumerate(ON)}}
    return pd.concat([n, part], axis=1).sort_index(key=lambda idx: idx.map(lambda x: ordre.get(x, len(ordre))))


def _regla(millor: dict[str, bool]) -> list[str]:
    es = all(millor.values())
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | "
            f"{mq._marca(millor['quarts'])} |",
            f"| «{mp.PARTIT}» | la diferència no és negativa | {mq._marca(millor['partit'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {mq._marca(millor['altres'])} |",
            "", f"**{A_EQUIPS} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_EQUIPS if es else A_SENSE}.", ""]


def markdown(metodes: pd.DataFrame, triades: dict, c: pd.DataFrame, passa: dict[str, bool], c_sense: pd.DataFrame,
             millor: dict[str, bool], per_font: dict[tuple[str, str], pd.DataFrame], encerts_: pd.DataFrame) -> str:
    linies = ["# Banc obert · Les xarxes veuen els dos equips sencers (T3v)", "",
              "Generat amb `uv run python -I -m banc.model_a_equips`. Dades obertes: 7 partits de DFL (IDSSE, CC BY",
              "4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3v», i la capçalera de `banc/model_a_equips.py`. Es puntua a la veritat",
              "de toc.", "",
              f"**{XARXES}** i **{A_SENSE}** són els de la T3t, amb les peces de la memòria cau (✓ comprovat: a cada",
              f"punt de la graella donen l'spellF1 del banc de la T3t). **{A_EQUIPS}** és {A_SENSE}, amb les cinc",
              "xarxes que també veuen tots els jugadors dels dos equips.", "",
              f"## {A_EQUIPS} contra {XARXES_TOC} (spellF1): el criteri", "",
              *t3b._taula(c, A_EQUIPS, XARXES_TOC), "", *mt._criteris(passa),
              f"## {A_EQUIPS} contra {A_SENSE} (spellF1)", "", *t3i._comparacio(c_sense, A_EQUIPS, A_SENSE), ""]
    if not all(passa.values()):
        linies += ["## No passa: és el millor fins ara?", "", *_regla(millor)]
    for (font, contra), taula in per_font.items():
        linies += [f"## {A_EQUIPS} contra {contra}, només els partits de {font}", "",
                   *t3i._comparacio(taula, A_EQUIPS, contra), ""]
    linies += ["## On s'encerta l'equip", "",
               "On la veritat de toc és d'un equip, la part de les imatges on l'equip més probable és el bo (les",
               "xarxes, amb les seves probabilitats; el segon, amb la relativa). Un forat és un tros sense pilota a",
               f"l'escenari, amb {t3i.K} imatges més a cada banda; per durada, la del tros sense pilota. Als forats,",
               "també segons si la possessió de la veritat es veu algun cop amb pilota o mai.", "",
               t3p.md(taula_encerts(encerts_)), "",
               "## L'spellF1 de cada mètode (mitjana dels deu partits)", "",
               *mt._mitjanes(metodes, [XARXES, XARXES_TOC, A_SENSE, A_EQUIPS]), "## Els decodificadors triats", "",
               *mq._triades(triades), ""]
    return "\n".join(linies)


def clau() -> str:
    """El que fa les probabilitats d'aquí: les peces d'A sense pilota, el que veuen les xarxes noves i això."""
    h = hashlib.sha256((msp.CLAU + repr((SIS, ESCENARIS, xarxes.LLAVORS, model.RONDES, model.PAS))).encode())
    h.update(Path(xeq.__file__).read_bytes())
    for funcio in (entrena_xarxes, xarxes_del_grup, xarxes_de_la_prova, mostres_segon, segon):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + vt.CLAU + msp.clau_dels_resultats()).encode())
    h.update(Path(paf.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_a_equips as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        return list(feina.map(getattr(aquest, fes), tasques))


def entrena_les_peces(processos: int) -> None:
    """Les xarxes dels grups i dels partits, i després el segon de cada partit."""
    from banc import model_a_equips as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        grups = [(nom, i) for nom in fonts.NOMS for i in range(t3e.GRUPS)]
        for k, ((nom, i), _) in enumerate(zip(grups, feina.map(aquest.xarxes_del_grup, grups)), start=1):
            print(f"· {k}/{len(grups)}: les xarxes noves del grup {i} de {nom}", flush=True)
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.xarxes_de_la_prova, fonts.NOMS)):
            print(f"· les xarxes noves de {nom}", flush=True)
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.segon, fonts.NOMS)):
            print(f"· el segon d'{A_EQUIPS} de {nom}", flush=True)


def files_de(metodes: tuple[str, ...], processos: int) -> pd.DataFrame:
    tasques = [(nom, e, metodes) for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    return pd.DataFrame([f for tros in en_paral_lel("graella", tasques, processos) for f in tros])


def escriu(contingut: dict, md: str) -> None:
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-a-equips.json").write_text(json.dumps(contingut, indent=1, default=float,
                                                                   allow_nan=False))
    (DIR_RESULTATS / "model-a-equips.md").write_text(md)
    print(md)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=4, help="models alhora")
    args = ap.parse_args()
    for nom in fonts.NOMS:
        de_qui(XARXES, nom)
        de_qui(A_SENSE, nom)
        msp.xarxes_de_la_prova(nom, entrena=False)
        vt.veritat(nom)
    files = files_de((XARXES, A_SENSE), args.processos)
    mta.comprova_les_d_abans(files)
    print(f"· {XARXES} i {A_SENSE} donen el del banc de la T3t", flush=True)
    entrena_les_peces(args.processos_models)
    files = pd.concat([files, files_de((A_EQUIPS,), args.processos)], ignore_index=True)
    de_xarxes, triades_xarxes = mt.tria_sense_mirar(files, XARXES, SEMPRE, XARXES)
    mt.comprova_el_decodificador(triades_xarxes)
    xarxes_toc, triades_xarxes_toc = mt.tria_sense_mirar(files, XARXES, TOC, XARXES_TOC)
    de_sense, triades_sense = mt.tria_sense_mirar(files, A_SENSE, TOC, A_SENSE)
    de_equips, triades_equips = mt.tria_sense_mirar(files, A_EQUIPS, TOC, A_EQUIPS)
    metodes = pd.concat([de_xarxes, xarxes_toc, de_sense, de_equips], ignore_index=True)
    c = mt.comparacio(metodes, A_EQUIPS, XARXES_TOC, TOC, amb_criteri=True)
    c_sense = mt.comparacio(metodes, A_EQUIPS, A_SENSE, TOC, amb_criteri=False)
    passa, millor = mt.compleix(c), mq.millor_fins_ara(c_sense)
    per_font = {(font, contra): mt.comparacio(metodes[metodes["font"] == font], A_EQUIPS, contra, TOC,
                                              amb_criteri=False)
                for font in FONTS for contra in (XARXES_TOC, A_SENSE)}
    encerts_ = pd.DataFrame([f for tros in en_paral_lel("encerts", list(itertools.product(fonts.NOMS, ESCENARIS)),
                                                         args.processos) for f in tros])
    triades = {XARXES: triades_xarxes, XARXES_TOC: triades_xarxes_toc, A_SENSE: triades_sense,
               A_EQUIPS: triades_equips}
    contingut = {"clau": clau_dels_resultats(), "passa": passa, "millor_fins_ara": millor,
                 "comparacio": t3.registres(c), "contra_a_sense_pilota": t3.registres(c_sense), "triades": triades,
                 "files": t3.registres(files),
                 "per_font": {f"{font} · {contra}": t3.registres(t) for (font, contra), t in per_font.items()},
                 "encerts": t3.registres(encerts_)}
    escriu(contingut, markdown(metodes, triades, c, passa, c_sense, millor, per_font, encerts_))


if __name__ == "__main__":
    main()
