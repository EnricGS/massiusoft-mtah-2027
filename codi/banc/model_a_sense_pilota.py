"""Les xarxes veuen els jugadors també sense pilota (T3t del pla per tocs, `docs/pla-tocs.md`, «T3t»; D-52).

    cd codi && uv run python -I -m banc.model_a_sense_pilota [--processos 12] [--processos-models 4]

A xarxes tal qual, amb una sola diferència: on no es veu la pilota, les cinc xarxes veuen una pilota estimada i
quant fa i quant falta perquè es vegi (`cadena/xarxa_sense_pilota.py`). El primer i la q són els d'A xarxes, de la
memòria cau de la T3p.

1. **En començar,** A xarxes, amb la memòria cau, ha de donar a cada punt de la graella i a les dues veritats
   l'spellF1 del banc de la T3q.
2. **Les xarxes noves:** les cinc de cada grup (entrenades amb els altres sis partits, per entrenar el segon) i les
   cinc del partit que es prova (amb els altres nou), com les d'A xarxes. 200 xarxes (`dades/banc/a-sense-pilota/`).
3. **El segon,** entrenat com el d'A xarxes, amb les probabilitats de les xarxes noves.
4. **El decodificador,** amb la graella de la T3j, triat amb els altres nou als quatre ×¼ a la veritat de toc; el d'A
   xarxes, igual.
5. **El criteri** del pla: A sense pilota contra A xarxes, a la veritat de toc. Als quatre ×¼ guanya clarament; al
   net, als ×1, al soroll2 i a «partit ×¼», no perd. Si no passa, la regla del millor fins ara. Només per saber-ho:
   per font, on encerten l'equip les xarxes, el segon i les prediccions (on es veu la pilota i als forats, segons
   quant duren), i els canvis falsos que queden.

Escriu `resultats/model-a-sense-pilota.json` i `resultats/model-a-sense-pilota.md`. Tot són dades obertes. Els mòduls
d'abans no es toquen.
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
from banc import analisi_t3r as an
from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_canvis2 as t3j
from banc import model_a_context as t3e
from banc import model_a_partit as mp
from banc import model_a_possessio as t3f
from banc import model_a_q as mq
from banc import model_a_quart as t3b
from banc import model_a_toc as mt
from banc import model_a_xarxa as t3m
from banc import sostre_curtes as sc
from banc import sostre_sense_pilota as ssp
from banc import veritat_toc as vt
from cadena import model, xarxa, xarxes
from cadena import xarxa_sense_pilota as xsp
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ESCENARIS = mp.ESCENARIS                            # els deu de la T3 i «partit ×¼»
SIS = mp.SIS
XARXES, XARXES_TOC = mt.XARXES, mt.XARXES_TOC       # A xarxes, amb el decodificador de la cadena i triat a la de toc
A_SENSE = "A sense pilota"
SEMPRE, TOC = mt.SEMPRE, mt.TOC
FONTS = ("dfl", "metrica")
AMB_PILOTA, ALS_FORATS = ssp.AMB_PILOTA, ssp.ALS_FORATS
FORATS = ((0, 2 * pm.FPS, "forats de menys de 2 s"), (2 * pm.FPS, 5 * pm.FPS, "forats de 2 a 5 s"),
          (5 * pm.FPS, np.inf, "forats de 5 s o més"))           # segons quant dura el tros sense pilota
ON = (AMB_PILOTA, ALS_FORATS, *(nom for _, _, nom in FORATS))
XARXES_ARA, XARXES_NOVES = "les xarxes d'ara", "les xarxes noves"
SEGON_ARA, SEGON_NOU = "el segon d'ara", "el segon nou"
QUI = (XARXES_ARA, XARXES_NOVES, SEGON_ARA, SEGON_NOU, XARXES_TOC, A_SENSE)
DIR_CAU = fonts.DIR_CAU / "a-sense-pilota"
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
    """Com `mp.entrena_xarxes` amb els sis escenaris d'ara: les mateixes imatges i etiquetes, amb el que veuen les
    xarxes noves."""
    xs, ys = [], []
    for nom in noms:
        for e in SIS:
            p = mp.degradat(nom, e)
            files = t3f.tria(p.veritat, avalua.trams_valids(p))
            x, y = xsp.mostres(p.tracking, p.trams, files, p.veritat[files])
            xs.append(x)
            ys.append(y)
    x = np.concatenate(xs)
    del xs
    return xarxes.entrena(x, np.concatenate(ys))


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
            desat[clau_] = xsp.probabilitats(entrenades, p.tracking, p.trams).astype(np.float32)
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
            desat[f"e{i}"] = xsp.probabilitats(entrenades, p.tracking, p.trams).astype(np.float32)
        desa(cami, perdues=np.array(perdues), **desat)
    return {e: desat[f"e{i}"] for i, e in enumerate(ESCENARIS)}


def mostres_segon(prova: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Com `mp.mostres_segon`: el primer de cada grup (de la memòria cau) i les xarxes noves del grup."""
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
    """Les probabilitats d'A sense pilota al partit `prova`, a tots els escenaris, i el prior: com el segon d'A xarxes
    (`mp.segon`), amb les xarxes noves. Amb `entrena=False`, només les llegeix de la memòria cau."""
    cami = cau("segon", prova)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les probabilitats del segon d'{A_SENSE} de {prova}, o són d'un altre codi")
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
    """Les probabilitats i el prior d'A xarxes (de la memòria cau de la T3p) o d'A sense pilota, amb la q d'A xarxes."""
    probes, prior = mp.segon((nom, SIS), entrena=False) if metode == XARXES else segon(nom, entrena=False)
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


def durada_dels_forats(vista: np.ndarray, valides: np.ndarray, k: int = t3i.K) -> np.ndarray:
    """A cada imatge d'un forat (`sc.forats`), quant dura el tros sense pilota (en imatges; a les `k` del costat, el
    més llarg dels que hi toquen). 0 fora dels forats."""
    out = np.zeros(len(vista), dtype=float)
    for a, b in ssp.trossos(~vista & valides):
        out[max(a - k, 0):b + k] = np.maximum(out[max(a - k, 0):b + k], b - a)
    return out


def mascares(vista: np.ndarray, valides: np.ndarray) -> dict[str, np.ndarray]:
    """On es veu la pilota, als forats, i als forats segons quant dura el tros sense pilota (només a les `valides`)."""
    al_forat = sc.forats(vista) & valides
    durada = durada_dels_forats(vista, valides)
    return {AMB_PILOTA: valides & ~al_forat, ALS_FORATS: al_forat,
            **{nom: al_forat & (durada >= baix) & (durada < alt) for baix, alt, nom in FORATS}}


def falsos(pred: np.ndarray, toc: np.ndarray, trams: list[tuple[int, int]], al_forat: np.ndarray) -> dict[str, int]:
    """Els canvis d'equip predits, quants són falsos (cap de real a `an.TOL` imatges o menys) i quants d'aquests són
    als forats."""
    canvis, reals = t3i.canvis(pred, trams), t3i.canvis(toc, trams)
    fals = ~an.a_prop(canvis, reals, an.TOL)
    return {"canvis": len(canvis), "falsos": int(fals.sum()), "falsos als forats": int((fals & al_forat[canvis]).sum())}


def encerts(tasca: tuple[str, str, dict[str, tuple]]) -> dict[str, list[dict]]:
    """Un partit i un escenari, amb els decodificadors triats: on encerten l'equip les xarxes, el segon i les
    prediccions, i els canvis falsos de cada predicció."""
    nom, escenari, triats = tasca
    de_sempre = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    trams = avalua.trams_valids(replace(de_sempre, veritat=toc))
    valides = ssp.dins(len(toc), trams)
    vista = ~np.isnan(de_sempre.tracking.pilota[:, 0])
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}
    relatives, preds = {}, {}
    for qui, metode in ((SEGON_ARA, XARXES), (SEGON_NOU, A_SENSE)):
        probes, prior, q_ = de_qui(metode, nom)
        relatives[qui] = log_relativa(probes[escenari].astype(float), prior)
        w, lam, d_min = triats[XARXES_TOC if metode == XARXES else A_SENSE]
        preds[XARXES_TOC if metode == XARXES else A_SENSE] = t3i.per_trams(
            relatives[qui], q_[escenari].astype(float), de_sempre.trams, w, lam, int(d_min))
    probes = {XARXES_ARA: mp.xarxes_de_la_prova((nom, SIS))[escenari].astype(float),
              XARXES_NOVES: xarxes_de_la_prova(nom, entrena=False)[escenari].astype(float), **relatives}
    files = []
    for on, mascara in mascares(vista, valides).items():
        for qui in QUI:
            n, e = ssp.encerts_pred(preds[qui], toc, mascara) if qui in preds else ssp.encerts(probes[qui], toc,
                                                                                               mascara)
            files.append({**comu, "on": on, "qui": qui, "n": n, "encerts": e})
    al_forat = sc.forats(vista)
    canvis = [{**comu, "metode": qui, **falsos(pred, toc, trams, al_forat)} for qui, pred in preds.items()]
    return {"encerts": files, "canvis": canvis}


def taula_encerts(t: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i on: quantes imatges hi ha d'un equip, i la part on cadascú hi encerta l'equip."""
    g = t.groupby(["escenari", "on", "qui"], sort=False)[["n", "encerts"]].sum()
    part = (g["encerts"] / g["n"]).unstack("qui")[list(QUI)]
    n = g["n"].xs(XARXES_TOC, level="qui").rename("n imatges")
    taula = pd.concat([n, part], axis=1)
    return taula.sort_index(key=lambda idx: idx.map(lambda x: {**t3q.ORDRE, **{o: i for i, o in enumerate(ON)}}
                                                     .get(x, len(t3q.ORDRE))))


def taula_canvis(t: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i mètode: els canvis predits, la part falsa i, dels falsos, la part als forats."""
    g = t.groupby(["escenari", "metode"], sort=False)[["canvis", "falsos", "falsos als forats"]].sum()
    taula = pd.DataFrame({"n canvis": g["canvis"], "falsos": g["falsos"] / g["canvis"],
                          "dels falsos, als forats": g["falsos als forats"] / g["falsos"]}).unstack("metode")
    return t3q.ordena(taula)


def _regla(millor: dict[str, bool]) -> list[str]:
    es = all(millor.values())
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | "
            f"{mq._marca(millor['quarts'])} |",
            f"| «{mp.PARTIT}» | la diferència no és negativa | {mq._marca(millor['partit'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {mq._marca(millor['altres'])} |",
            "", f"**{A_SENSE} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_SENSE if es else XARXES}.", ""]


def markdown(metodes: pd.DataFrame, triades: dict, c: pd.DataFrame, passa: dict[str, bool],
             millor: dict[str, bool], per_font: dict[str, pd.DataFrame], encerts_: pd.DataFrame,
             canvis: pd.DataFrame) -> str:
    linies = ["# Banc obert · Les xarxes veuen els jugadors també sense pilota (T3t)", "",
              "Generat amb `uv run python -I -m banc.model_a_sense_pilota`. Dades obertes: 7 partits de DFL (IDSSE,",
              "CC BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3t», i la capçalera de `banc/model_a_sense_pilota.py`. Es puntua a la",
              "veritat de toc.", "",
              f"**{XARXES}** és el de la cadena, amb les peces de la memòria cau de la T3p (✓ comprovat: a cada punt de",
              f"la graella dona l'spellF1 del banc de la T3q). **{A_SENSE}** és el mateix, amb les cinc xarxes que",
              "veuen una pilota estimada on no es veu la pilota.", "",
              f"## {A_SENSE} contra {XARXES_TOC} (spellF1): el criteri", "",
              *t3b._taula(c, A_SENSE, XARXES_TOC), "", *mt._criteris(passa)]
    if not all(passa.values()):
        linies += ["## No passa: és el millor fins ara?", "", *_regla(millor)]
    for font, taula in per_font.items():
        linies += [f"## {A_SENSE} contra {XARXES_TOC}, només els partits de {font}", "",
                   *t3i._comparacio(taula, A_SENSE, XARXES_TOC), ""]
    linies += ["## On s'encerta l'equip", "",
               "On la veritat de toc és d'un equip, la part de les imatges on l'equip més probable és el bo (les",
               "xarxes, amb les seves probabilitats; el segon, amb la relativa) i on la predicció hi dona el bo. Un",
               f"forat és un tros sense pilota a l'escenari, amb {t3i.K} imatges més a cada banda; per durada, la del",
               "tros sense pilota.", "", t3p.md(taula_encerts(encerts_)), "",
               "## Els canvis falsos que queden", "",
               f"Els canvis d'equip predits (deu partits), la part que són falsos (cap de real a {an.TOL} imatges o",
               "menys, com a `canvis_falsos.py`) i, dels falsos, la part als forats.", "",
               t3p.md(taula_canvis(canvis)), "",
               "## L'spellF1 de cada mètode (mitjana dels deu partits)", "",
               *mt._mitjanes(metodes, [XARXES, XARXES_TOC, A_SENSE]), "## Els decodificadors triats", "",
               *mq._triades(triades), ""]
    return "\n".join(linies)


def clau() -> str:
    """El que fa les probabilitats d'aquí: les peces d'A xarxes, el que veuen les xarxes noves i això."""
    h = hashlib.sha256((mp.CLAU + repr((SIS, ESCENARIS, xarxes.LLAVORS, model.RONDES, model.PAS))).encode())
    h.update(Path(xsp.__file__).read_bytes())
    for funcio in (entrena_xarxes, xarxes_del_grup, xarxes_de_la_prova, mostres_segon, segon):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + vt.CLAU + mt.clau_dels_resultats()).encode())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_a_sense_pilota as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        return list(feina.map(getattr(aquest, fes), tasques))


def entrena_les_peces(processos: int) -> None:
    """Les xarxes dels grups i dels partits, i després el segon de cada partit."""
    from banc import model_a_sense_pilota as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        grups = [(nom, i) for nom in fonts.NOMS for i in range(t3e.GRUPS)]
        for k, ((nom, i), _) in enumerate(zip(grups, feina.map(aquest.xarxes_del_grup, grups)), start=1):
            print(f"· {k}/{len(grups)}: les xarxes noves del grup {i} de {nom}", flush=True)
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.xarxes_de_la_prova, fonts.NOMS)):
            print(f"· les xarxes noves de {nom}", flush=True)
        for nom, _ in zip(fonts.NOMS, feina.map(aquest.segon, fonts.NOMS)):
            print(f"· el segon d'{A_SENSE} de {nom}", flush=True)


def files_de(metodes: tuple[str, ...], processos: int) -> pd.DataFrame:
    tasques = [(nom, e, metodes) for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    return pd.DataFrame([f for tros in en_paral_lel("graella", tasques, processos) for f in tros])


def escriu(contingut: dict, md: str) -> None:
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-a-sense-pilota.json").write_text(json.dumps(contingut, indent=1, default=float,
                                                                         allow_nan=False))
    (DIR_RESULTATS / "model-a-sense-pilota.md").write_text(md)
    print(md)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=4, help="models alhora")
    args = ap.parse_args()
    for nom in fonts.NOMS:
        de_qui(XARXES, nom)
        mp.xarxes_de_la_prova((nom, SIS))
        vt.veritat(nom)
    files = files_de((XARXES,), args.processos)
    mq.comprova_a_xarxes(files)
    print(f"· {XARXES} dona el del banc de la T3q", flush=True)
    entrena_les_peces(args.processos_models)
    files = pd.concat([files, files_de((A_SENSE,), args.processos)], ignore_index=True)
    de_xarxes, triades_xarxes = mt.tria_sense_mirar(files, XARXES, SEMPRE, XARXES)
    mt.comprova_el_decodificador(triades_xarxes)
    xarxes_toc, triades_xarxes_toc = mt.tria_sense_mirar(files, XARXES, TOC, XARXES_TOC)
    de_sense, triades_sense = mt.tria_sense_mirar(files, A_SENSE, TOC, A_SENSE)
    metodes = pd.concat([de_xarxes, xarxes_toc, de_sense], ignore_index=True)
    c = mt.comparacio(metodes, A_SENSE, XARXES_TOC, TOC, amb_criteri=True)
    passa, millor = mt.compleix(c), mq.millor_fins_ara(c)
    per_font = {font: mt.comparacio(metodes[metodes["font"] == font], A_SENSE, XARXES_TOC, TOC, amb_criteri=False)
                for font in FONTS}
    tasques = [(nom, e, {XARXES_TOC: triades_xarxes_toc[nom], A_SENSE: triades_sense[nom]})
               for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    trossos = en_paral_lel("encerts", tasques, args.processos)
    encerts_, canvis = (pd.DataFrame([f for t in trossos for f in t[k]]) for k in ("encerts", "canvis"))
    triades = {XARXES: triades_xarxes, XARXES_TOC: triades_xarxes_toc, A_SENSE: triades_sense}
    contingut = {"clau": clau_dels_resultats(), "passa": passa, "millor_fins_ara": millor,
                 "comparacio": t3.registres(c), "triades": triades, "files": t3.registres(files),
                 "per_font": {font: t3.registres(t) for font, t in per_font.items()},
                 "encerts": t3.registres(encerts_), "canvis": t3.registres(canvis)}
    escriu(contingut, markdown(metodes, triades, c, passa, millor, per_font, encerts_, canvis))


if __name__ == "__main__":
    main()
