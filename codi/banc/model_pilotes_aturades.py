"""Les pilotes aturades del Smart Tagging (T3af del pla per tocs, `docs/pla-tocs.md`, «T3af»; D-68).

    cd codi && uv run python -I -m banc.model_pilotes_aturades [--processos 12]

**Pas 1, el sostre, sense entrenar res.** Quant en podria treure una peça perfecta:

1. **En començar:** A xarxes i A equips sencers, amb la memòria cau, han de donar el banc de la T3v, A pilota creïble,
   el de la T3w, i A neteja d'aire, amb el decodificador d'A equips sencers, el de la T3ac. Si no, s'atura. Les
   represes de cada partit, de `banc/smart_tagging_simulat.py`.
2. **A cada partit i escenari** (els onze), la predicció d'A neteja d'aire amb el seu decodificador; ha de donar
   l'spellF1 de la T3ac a la veritat de toc (si no, s'atura).
3. **A cada nivell** (bo, mitjà i dolent), el Smart Tagging simulat amb la llavor de provar, i a cada represa que el
   nivell no perd, la veritat de toc (`sostre`): des de l'inici de l'estona de pilota morta que s'hi acaba (30 s enrere
   com a màxim, dins de la part) fins a 3 s després de la represa. Les etiquetes falses i els errors de l'inici, del
   tipus i de l'equip no hi fan res: és el que en trauria una peça que les fes servir perfectament.
4. **La regla, escrita abans:** es fa el pas 2 si, amb el nivell mitjà, el sostre contra A neteja d'aire arriba a
   +0,010 a «partit ×¼» i a la mitjana dels quatre ×¼ (`cal_el_pas_2`).

**Pas 2, «A pilotes aturades».** A neteja d'aire tal qual, amb una sola diferència: el segon també veu les 17 columnes
del Smart Tagging (`cadena/smart_tagging.py`).

1. **El segon de cada partit,** entrenat amb les mostres de `mae.mostres_segon` (els altres nou, als sis escenaris
   d'entrenament), amb les etiquetes simulades del nivell de cada partit i escenari (`sts.nivell_per_aprendre`: bo,
   mitjà, dolent o cap) i la llavor d'aprendre. S'aplica com el d'A pilota creïble (al partit netejat, amb el seu
   primer i les seves cinc xarxes), a cada escenari i cada nivell, amb la llavor de provar
   (`dades/banc/pilotes-aturades/`). La resta, la d'A neteja d'aire: la q d'A pilota creïble i la D impossible on la
   neteja ha tret la pilota.
2. **El decodificador,** amb la graella de la T3j, triat amb els altres nou als quatre ×¼, amb el nivell mitjà, a la
   veritat de toc. Cap punt de la graella ni cap nivell no hi ha de donar la D a una imatge netejada.
3. **El criteri** del pla: amb el nivell mitjà, el de sempre contra A xarxes; i amb els nivells dolent i cap, contra
   A neteja d'aire, als quatre ×¼ i a «partit ×¼», la diferència no baixa de −0,005 (`aguanta`). Si no passa, la regla
   de la D-50 contra A neteja d'aire amb el nivell mitjà, i la mateixa segona part. Només per saber-ho: per font; amb
   el nivell bo; a 5 s o menys de les represes, on encerta cadascú; les possessions aparellades per durada; el pes de
   les columnes noves; i els decodificadors triats.

Escriu `resultats/sostre-pilotes-aturades.json` i `.md` (el pas 1) i `resultats/model-pilotes-aturades.json` i `.md`
(el pas 2). Tot són dades obertes. Els mòduls d'abans no es toquen.
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
from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import errors_als_forats as eaf
from banc import model_a_canvis as t3i
from banc import model_a_canvis2 as t3j
from banc import model_a_context as t3e
from banc import model_a_equips as mae
from banc import model_a_partit as mp
from banc import model_a_possessio as t3f
from banc import model_a_q as mq
from banc import model_a_quart as t3b
from banc import model_a_toc as mt
from banc import model_a_xarxa as t3m
from banc import model_camp_girat as mcg
from banc import model_neteja_aire as mna
from banc import model_pilota_creible as mpc
from banc import model_vores as mv
from banc import smart_tagging_simulat as sts
from banc import sostre_sense_pilota as ssp
from banc import veritat_toc as vt
from cadena import model
from cadena import pilota_creible as pc
from cadena import smart_tagging as st
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ESCENARIS = mp.ESCENARIS                            # els deu de la T3 i «partit ×¼»
SIS = mp.SIS
QUARTS_T3 = t3.QUARTS
PARTIT = mp.PARTIT
QUARTS = mp.QUARTS                                  # els quatre ×¼ i «partit ×¼»
XARXES, XARXES_TOC, A_EQUIPS, A_CREIBLE = mpc.XARXES, mpc.XARXES_TOC, mpc.A_EQUIPS, mpc.A_CREIBLE
A_NETEJA = mna.A_NETEJA
A_PA = "A pilotes aturades"
SEMPRE, TOC = mpc.SEMPRE, mpc.TOC
NIVELLS_SOSTRE = ("bo", "mitjà", "dolent")
NIVELLS = tuple(sts.NIVELLS)                        # bo, mitjà, dolent i cap
PER_TRIAR = "mitjà"                                 # el nivell amb què es tria el decodificador i es mira el criteri
ROBUST = ("dolent", "cap")                          # on no ha de perdre contra A neteja d'aire
MARGE_ROBUST = 0.005
ENRERE = 30 * pm.FPS
DESPRES = 3 * pm.FPS
A_PROP = 5 * pm.FPS
LLINDAR = 0.010
PER_DURADA = mcg.PER_DURADA
DIR_CAU = sts.DIR_CAU
DIR_RESULTATS = t3.DIR_RESULTATS


def sostre(pred: np.ndarray, toc: np.ndarray, trams: tuple[tuple[int, int, int], ...],
           represes: tuple[sts.Represa, ...], guardades: tuple[int, ...]) -> np.ndarray:
    """`pred` amb la veritat `toc` al voltant de cada represa de `guardades`: des de l'inici de la D que s'hi acaba
    (`ENRERE` com a màxim) fins a `DESPRES` després, tot dins de la seva part."""
    x = pred.copy()
    for i in guardades:
        r = represes[i].imatge
        a, b = next((a, b) for _, a, b in trams if a <= r <= b)
        de = r
        while de > max(a, r - ENRERE) and toc[de - 1] == pm.D:
            de -= 1
        fins = min(b + 1, r + DESPRES)
        x[de:fins] = toc[de:fins]
    return x


def informe_sostre(tasca: tuple[str, str, tuple]) -> list[dict]:
    """Un partit i un escenari: l'spellF1 d'A neteja d'aire i el del sostre de cada nivell, a la veritat de toc."""
    nom, escenari, triat = tasca
    de_sempre = mp.degradat(nom, escenari)
    if de_sempre.trams != fonts.partit(nom).trams:
        raise RuntimeError(f"{nom}, {escenari}: l'escenari canvia les parts")
    r, q_ = mcg.relativa(A_NETEJA, nom, escenari, pc.lluny(de_sempre.tracking))
    pred = mna.prediccio(r, q_, de_sempre.trams, triat).astype(np.int8)
    toc = vt.veritat(nom)
    trams = avalua.trams_valids(replace(de_sempre, veritat=toc))
    spell = lambda x: pm.spell_scores(toc, pm.fill_abstentions(x, trams), trams)["mean_f1"]  # noqa: E731
    represes = sts.represes(nom).represes
    neteja = spell(pred)
    files = []
    for nivell in NIVELLS_SOSTRE:
        s = sts.simula(represes, toc, de_sempre.trams, sts.NIVELLS[nivell], sts.llavor(nom, escenari, nivell, "provar"))
        files.append({"partit": nom, "font": de_sempre.font, "escenari": escenari, "nivell": nivell,
                      "represes": len(represes), "guardades": len(s.de_represes), "neteja": neteja,
                      "sostre": spell(sostre(pred, toc, de_sempre.trams, represes, s.de_represes))})
    return files


def comprova_la_neteja(t: pd.DataFrame, metodes: pd.DataFrame) -> None:
    """L'spellF1 d'A neteja d'aire d'aquí ha de ser el del banc de la T3ac, a cada partit i escenari."""
    de_la_t3ac = metodes[(metodes["metode"] == A_NETEJA) & (metodes["veritat"] == TOC)].set_index(
        ["partit", "escenari"])["spell_f1"]
    aqui = t.drop_duplicates(["partit", "escenari"]).set_index(["partit", "escenari"])["neteja"]
    if len(aqui) != len(fonts.NOMS) * len(ESCENARIS) or not np.allclose(aqui, de_la_t3ac.reindex(aqui.index),
                                                                        atol=1e-9, rtol=0):
        raise RuntimeError(f"{A_NETEJA} no dona l'spellF1 del banc de la T3ac")


def diferencies(t: pd.DataFrame, nivell: str) -> pd.Series:
    """Per escenari, la mitjana dels deu partits del sostre menys A neteja d'aire."""
    seves = t[t["nivell"] == nivell]
    return (seves["sostre"] - seves["neteja"]).groupby(seves["escenari"], sort=False).mean()


def cal_el_pas_2(t: pd.DataFrame) -> dict[str, bool]:
    d = diferencies(t, "mitjà")
    return {"partit": bool(d[PARTIT] >= LLINDAR - 1e-12),
            "quarts": bool(d.reindex(QUARTS_T3).mean() >= LLINDAR - 1e-12)}


def taula_sostre(t: pd.DataFrame) -> pd.DataFrame:
    """Per escenari: A neteja d'aire i, a cada nivell, el sostre menys A neteja d'aire."""
    out = pd.DataFrame({A_NETEJA: t.drop_duplicates(["partit", "escenari"]).groupby("escenari")["neteja"].mean()})
    for nivell in NIVELLS_SOSTRE:
        out[f"sostre − {A_NETEJA}, {nivell}"] = diferencies(t, nivell)
    out = out.reindex(ESCENARIS)
    out.loc["mitjana dels quatre ×¼"] = out.loc[list(QUARTS_T3)].mean()
    return out.rename_axis("escenari")


def taula_represes(t: pd.DataFrame, comptes: dict[str, sts.Represes]) -> pd.DataFrame:
    """Per partit: els esdeveniments de pilota aturada, quants no s'han pogut posar, i les represes que guarda cada
    nivell (de mitjana als onze escenaris)."""
    out = pd.DataFrame({"esdeveniments": {n: c.esdeveniments for n, c in comptes.items()},
                        "no es posen": {n: c.no_col_locades for n, c in comptes.items()},
                        "al mateix canvi": {n: c.repetides for n, c in comptes.items()},
                        "represes": {n: len(c.represes) for n, c in comptes.items()}})
    for nivell in NIVELLS_SOSTRE:
        out[f"guardades, {nivell}"] = t[t["nivell"] == nivell].groupby("partit")["guardades"].mean()
    return out.reindex(list(fonts.NOMS)).rename_axis("partit")


def markdown_sostre(t: pd.DataFrame, passa: dict[str, bool], per_font: dict[str, pd.DataFrame],
                    comptes: dict[str, sts.Represes]) -> str:
    es = all(passa.values())
    d = taula_sostre(t)
    mitja = d[f"sostre − {A_NETEJA}, mitjà"]
    linies = ["# Banc obert · Les pilotes aturades del Smart Tagging: el sostre (T3af, pas 1)", "",
              "Generat amb `uv run python -I -m banc.model_pilotes_aturades`. Dades obertes: 7 partits de DFL (IDSSE,",
              "CC BY 4.0) i els 3 de mostra de Metrica. Cap dada del concurs. Com es fa i la regla: `docs/pla-tocs.md`,",
              "«T3af», i la capçalera de `banc/model_pilotes_aturades.py`. Es puntua a la veritat de toc.", "",
              f"**{A_NETEJA}** és el de la T3ac, amb el decodificador d'{A_EQUIPS} (✓ comprovat: dona l'spellF1 d'aquell",
              "banc a cada partit i escenari). **El sostre:** la seva predicció, amb la veritat al voltant de cada",
              "represa que el nivell no perd, de l'inici de la pilota morta (30 s enrere com a màxim) a 3 s després.", "",
              "## El sostre contra A neteja d'aire (spellF1, mitjana dels deu partits)", "",
              mv._md(d, 4), "",
              "## La regla del pas 2, escrita abans", "",
              "| Amb el nivell mitjà | Cal | Surt | |", "|---|---|---|---|",
              f"| «{PARTIT}» | +{LLINDAR:.3f} | {mitja[PARTIT]:+.4f} | {_marca(passa['partit'])} |",
              f"| La mitjana dels quatre ×¼ | +{LLINDAR:.3f} | {mitja['mitjana dels quatre ×¼']:+.4f} | "
              f"{_marca(passa['quarts'])} |", "",
              f"**{'Es fa' if es else 'No es fa'} el pas 2.**", ""]
    for font, seva in per_font.items():
        linies += [f"## Només els partits de {font}", "", mv._md(taula_sostre(seva), 4), ""]
    linies += ["## Les represes de cada partit", "",
               "Els esdeveniments de pilota aturada de les dades obertes, els que no es poden posar a cap canvi de la D",
               "a un equip a 3 s o menys, els que cauen al canvi d'un altre, i les represes que guarda cada nivell.", "",
               mv._md(taula_represes(t, comptes), 1), ""]
    return "\n".join(linies)


def _marca(si: bool) -> str:
    return "✓" if si else "✗"


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_pilotes_aturades as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        return list(feina.map(getattr(aquest, fes), tasques))




def pas_1(processos: int, metodes: pd.DataFrame, triades: dict, comptes: dict[str, sts.Represes]) -> bool:
    """El sostre, als deu partits i els onze escenaris; escriu el seu informe i diu si cal el pas 2."""
    tasques = [(nom, e, triades[A_EQUIPS][nom]) for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    t = pd.DataFrame([f for tros in en_paral_lel("informe_sostre", tasques, processos) for f in tros])
    comprova_la_neteja(t, metodes)
    print(f"· {A_NETEJA}: l'spellF1 de la T3ac a cada partit i escenari", flush=True)
    passa = cal_el_pas_2(t)
    per_font = {font: t[t["font"] == font] for font in mpc.FONTS}
    contingut = {"clau": clau_dels_resultats(), "cal_el_pas_2": passa, "triades": triades[A_EQUIPS],
                 "sostre": t3.registres(taula_sostre(t).reset_index()), "files": t3.registres(t),
                 "represes": t3.registres(taula_represes(t, comptes).reset_index())}
    escriu("sostre-pilotes-aturades", contingut, markdown_sostre(t, passa, per_font, comptes))
    return all(passa.values())


# --- Pas 2: A pilotes aturades ------------------------------------------------------------------------------------


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


def cau(peca: str, prova: str) -> Path:
    return DIR_CAU / f"{peca}-{prova}.npz"


def etiquetes_de(nom: str, escenari: str, nivell: str, per: str) -> tuple[st.Etiqueta, ...]:
    """Les etiquetes simulades d'un partit i un escenari, al nivell `nivell`, amb la llavor d'aprendre o de provar."""
    return sts.simula(sts.represes(nom).represes, vt.veritat(nom), fonts.partit(nom).trams, sts.NIVELLS[nivell],
                      sts.llavor(nom, escenari, nivell, per)).etiquetes


def amb_les_etiquetes(base: pd.DataFrame, etiquetes: tuple[st.Etiqueta, ...],
                      trams: tuple[tuple[int, int, int], ...]) -> pd.DataFrame:
    """La taula del segon d'A neteja d'aire amb les 17 columnes del Smart Tagging al final."""
    return pd.concat([base.reset_index(drop=True), st.columnes(etiquetes, len(base), trams)], axis=1)


def per_aprendre(prova: str) -> list[tuple[str, str]]:
    """Els partits i escenaris de les mostres del segon de `prova`: els altres nou, als sis d'entrenament (els dels
    grups de la T3e, com a `mae.mostres_segon`)."""
    return [qui for i in range(t3e.GRUPS) for qui in mp.claus_del_grup(prova, i, SIS)]


def mostres_segon(prova: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Les de `mae.mostres_segon(prova)`, amb les columnes del Smart Tagging simulat al nivell de cada partit i
    escenari (`sts.nivell_per_aprendre`) i la llavor d'aprendre."""
    primers, de_les_xarxes = {}, {}
    for i in range(t3e.GRUPS):
        primers |= mp.primer_del_grup((prova, i, SIS))
        de_les_xarxes |= mae.xarxes_del_grup((prova, i), entrena=False)
    if sorted(primers) != sorted(per_aprendre(prova)) or any(nom == prova for nom, _ in primers):
        raise RuntimeError(f"{prova}: les mostres del segon no són les dels altres nou")
    xs, ys = [], []
    for (nom, e), primer in primers.items():
        p = mp.degradat(nom, e)
        base = t3m.taula_segon(p, primer.astype(float), de_les_xarxes[(nom, e)].astype(float))
        x, y = t3f.mostres(p, amb_les_etiquetes(base, etiquetes_de(nom, e, sts.nivell_per_aprendre(nom, e),
                                                                     "aprendre"), p.trams))
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def segon(prova: str, entrena: bool = True) -> tuple[dict[tuple[str, str], np.ndarray], np.ndarray, dict]:
    """Les probabilitats d'A pilotes aturades al partit `prova` netejat, a cada escenari i nivell (amb la llavor de
    provar), el prior i el guany de cada columna: el segon entrenat amb `mostres_segon`, i aplicat amb el primer i les
    cinc xarxes d'A pilota creïble, com a `mpc.segon`."""
    cami = cau("segon", prova)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise RuntimeError(f"Falten les probabilitats del segon d'{A_PA} de {prova}, o són d'un altre codi")
        x, y = mostres_segon(prova)
        entrenat, prior = model.entrena(x, y), model.prior(y)
        columnes = np.array(list(x.columns))
        del x
        primers, de_les_xarxes = mpc.primer(prova, entrena=False), mpc.xarxes_de_la_prova(prova, entrena=False)
        desat = {"prior": prior, "columnes": columnes, "importancia": entrenat.feature_importance("gain")}
        for i, e in enumerate(ESCENARIS):
            p = mpc.creible(prova, e)
            base = t3m.taula_segon(p, primers[e].astype(float), de_les_xarxes[e].astype(float))
            for j, nivell in enumerate(NIVELLS):
                taula = amb_les_etiquetes(base, etiquetes_de(prova, e, nivell, "provar"), p.trams)
                desat[f"e{i}_n{j}"] = model.probabilitats(entrenat, taula).astype(np.float32)
        desa(cami, **desat)
    probes = {(e, nivell): desat[f"e{i}_n{j}"] for i, e in enumerate(ESCENARIS) for j, nivell in enumerate(NIVELLS)}
    return probes, desat["prior"], dict(zip(desat["columnes"].tolist(), map(float, desat["importancia"])))


def relativa(nom: str, escenari: str, nivell: str, netejades: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """La probabilitat relativa d'A pilotes aturades amb la D impossible a les imatges `netejades`, i la q d'A pilota
    creïble."""
    probes, prior, _ = segon(nom, entrena=False)
    r = log_relativa(probes[(escenari, nivell)].astype(float), prior)
    return mna.amb_la_d_impossible(r, netejades), mpc.q(nom, entrena=False)[escenari]


def graella(tasca: tuple[str, str]) -> list[dict]:
    """Un partit i un escenari, amb el nivell `PER_TRIAR`: cada punt de la graella de la T3j, a les dues veritats.
    S'atura si a cap punt hi dona la D a una imatge netejada."""
    nom, escenari = tasca
    de_sempre = mp.degradat(nom, escenari)
    partits = {SEMPRE: de_sempre, TOC: replace(de_sempre, veritat=vt.veritat(nom))}
    netejades = pc.lluny(de_sempre.tracking)
    r, q_ = relativa(nom, escenari, PER_TRIAR, netejades)
    files = []
    for w, lam, d_min in itertools.product(t3j.WS, t3j.LAMS, t3j.DMINS):
        pred = t3i.per_trams(r, q_.astype(float), de_sempre.trams, w, lam, d_min)
        if (pred[netejades] == pm.D).any():
            raise RuntimeError(f"{nom}, {escenari}, {(w, lam, d_min)}: {A_PA} dona la D a una imatge netejada")
        for veritat, p in partits.items():
            files.append({"partit": nom, "font": p.font, "escenari": escenari, "metode": A_PA, "veritat": veritat,
                          "w": w, "lam": lam, "d_min": d_min, **avalua.puntua(p, pred)})
    return files


def a_prop(represes: tuple[sts.Represa, ...], n: int, trams: tuple[tuple[int, int, int], ...],
           radi: int = A_PROP) -> np.ndarray:
    """Les imatges a `radi` o menys d'alguna represa, dins de la seva part."""
    out = np.zeros(n, dtype=bool)
    for r in represes:
        a, b = next((a, b) for _, a, b in trams if a <= r.imatge <= b)
        out[max(a, r.imatge - radi):min(b, r.imatge + radi) + 1] = True
    return out


def informe(tasca: tuple[str, str, tuple, tuple]) -> dict[str, list[dict]]:
    """Un partit i un escenari: les files d'A pilotes aturades a cada nivell, amb el seu decodificador (`triat`), a
    les dues veritats; a prop de les represes, on encerta cadascú; i, als escenaris de `PER_DURADA` i amb el nivell
    `PER_TRIAR`, les possessions aparellades per durada d'A neteja d'aire (amb el seu decodificador, `de_la_neteja`) i
    de la nova."""
    nom, escenari, triat, de_la_neteja = tasca
    de_sempre = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    partits = {SEMPRE: de_sempre, TOC: replace(de_sempre, veritat=toc)}
    netejades = pc.lluny(de_sempre.tracking)
    trams = avalua.trams_valids(partits[TOC])
    prop = a_prop(sts.represes(nom).represes, len(toc), de_sempre.trams) & ssp.dins(len(toc), trams)
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}
    r, q_ = mcg.relativa(A_NETEJA, nom, escenari, netejades)
    preds = {(A_NETEJA, ""): mna.prediccio(r, q_, de_sempre.trams, de_la_neteja)}
    for nivell in NIVELLS:
        r, q_ = relativa(nom, escenari, nivell, netejades)
        preds[(A_PA, nivell)] = mna.prediccio(r, q_, de_sempre.trams, triat)
        if (preds[(A_PA, nivell)][netejades] == pm.D).any():
            raise RuntimeError(f"{nom}, {escenari}, {nivell}: {A_PA} dona la D a una imatge netejada")
    w, lam, d_min = triat
    files = [{**comu, "metode": A_PA, "nivell": nivell, "veritat": veritat, "w": w, "lam": lam, "d_min": d_min,
              **avalua.puntua(p, preds[(A_PA, nivell)])} for nivell in NIVELLS for veritat, p in partits.items()]
    encerts = [{**comu, "metode": metode, "nivell": nivell, "n": int(prop.sum()),
                "encerts": int((pm.fill_abstentions(pred.astype(np.int8), trams)[prop] == toc[prop]).sum())}
               for (metode, nivell), pred in preds.items()]
    durades = []
    if escenari in PER_DURADA:
        for metode, nivell in ((A_NETEJA, ""), (A_PA, PER_TRIAR)):
            durades += [{**comu, "metode": metode, **f}
                        for f in mcg.per_durada(toc, preds[(metode, nivell)], trams)]
    return {"files": files, "encerts": encerts, "durades": durades}


def aguanta(c_neteja: dict[str, pd.DataFrame]) -> dict[str, bool]:
    """La segona part del criteri: amb els nivells de `ROBUST`, contra A neteja d'aire, als quatre ×¼ i a «partit ×¼»,
    la diferència no baixa de −`MARGE_ROBUST`."""
    return {nivell: bool((c["diferencia"][c["escenari"].isin(QUARTS)] >= -MARGE_ROBUST - 1e-12).all())
            for nivell, c in c_neteja.items() if nivell in ROBUST}


def de_nivell(metodes: pd.DataFrame, nous: pd.DataFrame, nivell: str) -> pd.DataFrame:
    """Les files d'abans i les d'A pilotes aturades amb el nivell `nivell`."""
    return pd.concat([metodes, nous[nous["nivell"] == nivell].drop(columns="nivell")], ignore_index=True)


def taula_encerts(t: pd.DataFrame) -> pd.DataFrame:
    """Per escenari: a 5 s o menys d'una represa, la part de les imatges on encerta A neteja d'aire i, a cada nivell,
    A pilotes aturades."""
    g = t.groupby(["escenari", "metode", "nivell"], sort=False)[["n", "encerts"]].sum()
    part = (g["encerts"] / g["n"]).unstack(["metode", "nivell"])
    part.columns = [A_NETEJA if m == A_NETEJA else f"{A_PA}, {n}" for m, n in part.columns]
    return part[[A_NETEJA, *(f"{A_PA}, {n}" for n in NIVELLS)]].reindex(ESCENARIS).rename_axis("escenari")


def taula_durades(t: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i durada: quantes possessions de la veritat hi ha per partit, i la part aparellada de cadascú."""
    g = t.groupby(["escenari", "durada", "metode"], sort=False)[["n", "aparellades"]].sum()
    part = (g["aparellades"] / g["n"]).unstack("metode")[[A_NETEJA, A_PA]].add_prefix("aparellades · ")
    n = (g["n"].xs(A_PA, level="metode") / t["partit"].nunique()).rename("n per partit")
    return eaf.en_ordre(pd.concat([n, part], axis=1), PER_DURADA, [nom for _, _, nom in mcg.DURADES])


def taula_importancia(importancies: dict[str, dict[str, float]]) -> pd.DataFrame:
    """Del segon de cada partit, la part del guany de cada columna del Smart Tagging, i de totes juntes (mitjana dels
    deu)."""
    t = pd.DataFrame(importancies).T
    part = t.div(t.sum(axis=1), axis=0)[list(st.COLUMNES)]
    out = part.mean().rename("part del guany").to_frame()
    out.loc["les 17 juntes"] = part.sum(axis=1).mean()
    return out.rename_axis("columna")


def _regla(millor: dict[str, bool], robust: dict[str, bool]) -> list[str]:
    es = all(millor.values()) and all(robust.values())
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | "
            f"{_marca(millor['quarts'])} |",
            f"| «{PARTIT}» | la diferència no és negativa | {_marca(millor['partit'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {_marca(millor['altres'])} |",
            f"| Dolent i cap | la segona part del criteri | {_marca(all(robust.values()))} |", "",
            f"**{A_PA} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_PA if es else A_NETEJA}.", ""]


def _robustesa(c_neteja: dict[str, pd.DataFrame], robust: dict[str, bool]) -> list[str]:
    linies = [f"| Nivell | {' | '.join(QUARTS)} | No baixa de −{MARGE_ROBUST} |",
              "|---" * (len(QUARTS) + 2) + "|"]
    for nivell in ROBUST:
        d = c_neteja[nivell].set_index("escenari")["diferencia"]
        linies.append(f"| {nivell} | " + " | ".join(f"{d[e]:+.4f}" for e in QUARTS) + f" | {_marca(robust[nivell])} |")
    return linies


def markdown(metodes_mitja: pd.DataFrame, triades: dict, c: pd.DataFrame, passa: dict[str, bool],
             robust: dict[str, bool], c_neteja: dict[str, pd.DataFrame], millor: dict[str, bool],
             altres: dict[tuple[str, str], pd.DataFrame], encerts: pd.DataFrame, durades: pd.DataFrame,
             importancies: dict[str, dict[str, float]]) -> str:
    passa_tot = all(passa.values()) and all(robust.values())
    linies = ["# Banc obert · Les pilotes aturades del Smart Tagging (T3af, pas 2)", "",
              "Generat amb `uv run python -I -m banc.model_pilotes_aturades`. Dades obertes: 7 partits de DFL (IDSSE,",
              "CC BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3af», i la capçalera de `banc/model_pilotes_aturades.py`. Es puntua a la",
              "veritat de toc.", "",
              f"**{XARXES_TOC}** i **{A_EQUIPS}** són els de la T3v, **{A_CREIBLE}**, el de la T3w, i **{A_NETEJA}**,",
              "el de la T3ac, amb les peces de la memòria cau (✓ comprovat). **A pilotes aturades** és A neteja d'aire,",
              "amb un segon que també veu les 17 columnes del Smart Tagging simulat, i el decodificador triat de nou",
              f"amb el nivell {PER_TRIAR}. ✓ Comprovat a cada punt de la graella i a cada nivell: no dona mai la D a una",
              "imatge netejada.", "",
              f"## Amb el nivell {PER_TRIAR}: {A_PA} contra {XARXES_TOC} (spellF1), el criteri", "",
              *t3b._taula(c, A_PA, XARXES_TOC), "", *mt._criteris(passa),
              f"## Amb els nivells dolent i cap: {A_PA} contra {A_NETEJA}, la segona part del criteri", "",
              *_robustesa(c_neteja, robust), "",
              f"**{A_PA} {'passa' if passa_tot else 'no passa'} el criteri sencer.**", ""]
    for nivell in NIVELLS:
        linies += [f"## Amb el nivell {nivell}: {A_PA} contra {A_NETEJA} (spellF1)", "",
                   *t3i._comparacio(c_neteja[nivell], A_PA, A_NETEJA), ""]
    if not passa_tot:
        linies += ["## No passa: és el millor fins ara?", "",
                   f"La regla de la D-50, escrita abans, contra {A_NETEJA} amb el nivell {PER_TRIAR}, i la mateixa",
                   "segona part del criteri:", "", *_regla(millor, robust)]
    for (titol, contra), taula in altres.items():
        linies += [f"## {titol}", "", *t3i._comparacio(taula, A_PA, contra), ""]
    linies += ["## A 5 s o menys de cada represa", "",
               "La part de les imatges vàlides a 5 s o menys d'una represa on la predicció (amb les abstencions",
               "omplertes) és la veritat de toc.", "", t3p.md(taula_encerts(encerts)), "",
               "## Les possessions de la veritat aparellades, per durada", "",
               f"Les possessions de la veritat de toc, i la part que s'aparella amb una de la predicció a la IoU "
               f"{mcg.LLINDAR}, amb el nivell {PER_TRIAR}.", "", t3p.md(taula_durades(durades)), "",
               "## El pes de les columnes del Smart Tagging al segon", "",
               "La part del guany de cada columna, de mitjana als deu segons.", "",
               mv._md(taula_importancia(importancies), 4), "",
               f"## L'spellF1 de cada mètode (mitjana dels deu partits, nivell {PER_TRIAR})", "",
               *mt._mitjanes(metodes_mitja, [XARXES_TOC, A_EQUIPS, A_NETEJA, A_PA]), "## Els decodificadors triats", "",
               f"{A_NETEJA} fa servir, a cada partit, el d'{A_EQUIPS}.", "", *mq._triades(triades), ""]
    return "\n".join(linies)


def clau() -> str:
    """El que fa les probabilitats d'aquí: les peces d'A pilota creïble i d'A equips sencers, el Smart Tagging simulat,
    les seves columnes i això."""
    h = hashlib.sha256((mpc.CLAU + mae.CLAU + mp.CLAU + sts.CLAU + repr((SIS, ESCENARIS, NIVELLS, model.RONDES,
                                                                        model.PAS))).encode())
    h.update(Path(st.__file__).read_bytes())
    for funcio in (etiquetes_de, amb_les_etiquetes, per_aprendre, mostres_segon, segon):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + mv.CLAU + sts.CLAU + mna.clau_dels_resultats()).encode())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def entrena_els_segons(processos: int) -> None:
    from banc import model_pilotes_aturades as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        for k, (nom, _) in enumerate(zip(fonts.NOMS, feina.map(aquest.segon, fonts.NOMS)), start=1):
            print(f"· {k}/{len(fonts.NOMS)}: el segon d'{A_PA} de {nom}", flush=True)


def pas_2(processos: int, processos_models: int, metodes: pd.DataFrame, triades: dict) -> None:
    entrena_els_segons(processos_models)
    files_graella = pd.DataFrame([f for tros in en_paral_lel("graella", list(itertools.product(fonts.NOMS, QUARTS_T3)),
                                                             processos) for f in tros])
    print(f"· {A_PA}: mai la D a les imatges netejades, a cap punt de la graella", flush=True)
    _, triades[A_PA] = mt.tria_sense_mirar(files_graella, A_PA, TOC, A_PA)
    tasques = [(nom, e, triades[A_PA][nom], triades[A_EQUIPS][nom])
               for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    trossos = en_paral_lel("informe", tasques, processos)
    nous, encerts, durades = (pd.DataFrame([f for tros in trossos for f in tros[k]])
                              for k in ("files", "encerts", "durades"))
    print(f"· {A_PA}: mai la D a les imatges netejades, a cap nivell", flush=True)
    c = mt.comparacio(de_nivell(metodes, nous, PER_TRIAR), A_PA, XARXES_TOC, TOC, amb_criteri=True)
    c_neteja = {n: mt.comparacio(de_nivell(metodes, nous, n), A_PA, A_NETEJA, TOC, amb_criteri=False) for n in NIVELLS}
    passa, robust, millor = mt.compleix(c), aguanta(c_neteja), mq.millor_fins_ara(c_neteja[PER_TRIAR])
    mitja = de_nivell(metodes, nous, PER_TRIAR)
    altres = {(f"{A_PA} contra {contra}, nivell {PER_TRIAR}, només els partits de {font}", contra):
              mt.comparacio(mitja[mitja["font"] == font], A_PA, contra, TOC, amb_criteri=False)
              for font in mpc.FONTS for contra in (XARXES_TOC, A_NETEJA)}
    altres[(f"{A_PA} contra {XARXES_TOC}, nivell bo", XARXES_TOC)] = mt.comparacio(
        de_nivell(metodes, nous, "bo"), A_PA, XARXES_TOC, TOC, amb_criteri=False)
    importancies = {nom: segon(nom, entrena=False)[2] for nom in fonts.NOMS}
    contingut = {"clau": clau_dels_resultats(), "passa": passa, "aguanta": robust, "millor_fins_ara": millor,
                 "comparacio": t3.registres(c), "contra_a_neteja_d_aire": {n: t3.registres(t) for n, t in
                                                                          c_neteja.items()},
                 "triades": triades, "files": t3.registres(nous),
                 "altres": {titol: t3.registres(t) for (titol, _), t in altres.items()}, "encerts": t3.registres(encerts),
                 "durades": t3.registres(durades), "importancia": importancies}
    escriu("model-pilotes-aturades", contingut, markdown(mitja, triades, c, passa, robust, c_neteja, millor, altres,
                                                        encerts, durades, importancies))


def escriu(nom: str, contingut: dict, md: str) -> None:
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / f"{nom}.json").write_text(json.dumps(contingut, indent=1, default=float, allow_nan=False))
    (DIR_RESULTATS / f"{nom}.md").write_text(md)
    print(md)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=3, help="models alhora")
    args = ap.parse_args()
    for nom in fonts.NOMS:
        for metode in (XARXES, A_EQUIPS, A_CREIBLE):
            mpc.de_qui(metode, nom)
        mpc.primer(nom, entrena=False)
        mpc.xarxes_de_la_prova(nom, entrena=False)
        mpc.q(nom, entrena=False)
        vt.veritat(nom)
    comptes = {nom: sts.represes(nom) for nom in fonts.NOMS}
    metodes, triades = mcg.comprova_les_d_abans(args.processos)
    print(f"· {XARXES} i {A_EQUIPS} donen el del banc de la T3v, {A_CREIBLE}, el de la T3w, i {A_NETEJA}, el de "
          "la T3ac", flush=True)
    if pas_1(args.processos, metodes, triades, comptes):
        pas_2(args.processos, args.processos_models, metodes, triades)
    else:
        print("· El sostre no arriba: no es fa el pas 2", flush=True)


if __name__ == "__main__":
    main()
