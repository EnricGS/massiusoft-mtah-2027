"""La mitjana dels dos segons (T3aa del pla per tocs, `docs/pla-tocs.md`, «T3aa»; D-59).

    cd codi && uv run python -I -m banc.model_dos_segons [--processos 12]

A equips sencers i A mostres als canvis tal qual, de la memòria cau, i a cada imatge la mitjana de les probabilitats dels
dos segons (`mitjana`). No s'entrena res.

1. **En començar,** A xarxes i A equips sencers, amb la memòria cau, han de donar a cada punt de la graella i a les dues
   veritats l'spellF1 del banc de la T3v, i A mostres als canvis, el del banc de la T3z. Els decodificadors triats de
   tots tres han de ser els d'aquells bancs.
2. **A dos segons:** la mitjana de les probabilitats dels dos segons, amb el mateix pes, i el prior i la q que tenen tots
   dos. Si no són els mateixos, s'atura (`de_qui`).
3. **El decodificador,** amb la graella de la T3j, triat amb els altres nou als quatre ×¼ a la veritat de toc.
4. **El criteri** del pla: A dos segons contra A xarxes, a la veritat de toc. Si no passa, la regla de la D-50 contra
   A equips sencers. Només per saber-ho: per font, on encerten l'equip els tres segons, qui l'encerta on els dos no
   donen el mateix, els canvis falsos i els decodificadors triats.

Escriu `resultats/model-dos-segons.json` i `resultats/model-dos-segons.md`. Tot són dades obertes. Els mòduls d'abans no
es toquen.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from banc import analisi_t3p as t3p
from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_canvis2 as t3j
from banc import model_a_partit as mp
from banc import model_a_q as mq
from banc import model_a_quart as t3b
from banc import model_a_sense_pilota as msp
from banc import model_a_toc as mt
from banc import model_mostres_canvis as mmc
from banc import model_pilota_creible as mpc
from banc import sostre_curtes as sc
from banc import sostre_sense_pilota as ssp
from banc import veritat_toc as vt
from possessio.decodificacio import log_relativa

ESCENARIS = mp.ESCENARIS                            # els deu de la T3 i «partit ×¼»
XARXES, XARXES_TOC, A_EQUIPS, A_CANVIS = mmc.XARXES, mmc.XARXES_TOC, mmc.A_EQUIPS, mmc.A_CANVIS
SEMPRE, TOC = mmc.SEMPRE, mmc.TOC
A_DOS = "A dos segons"
FONTS = mmc.FONTS
ON = mmc.ON
SEGON_EQUIPS, SEGON_CANVIS, LA_MITJANA = f"el segon d'{A_EQUIPS}", f"el segon d'{A_CANVIS}", "la mitjana"
QUI = (SEGON_EQUIPS, SEGON_CANVIS, LA_MITJANA)
DE_QUI = {A_EQUIPS: SEGON_EQUIPS, A_CANVIS: SEGON_CANVIS, A_DOS: LA_MITJANA}
CLAUS = ["partit", "escenari", "metode", "veritat", "w", "lam", "d_min"]
DIR_RESULTATS = t3.DIR_RESULTATS


def mitjana(un: np.ndarray, altre: np.ndarray) -> np.ndarray:
    """(n, 3): a cada imatge, la mitjana de les probabilitats dels dos segons, amb el mateix pes."""
    if un.shape != altre.shape:
        raise ValueError(f"Els dos segons no tenen la mateixa forma ({un.shape} i {altre.shape})")
    return (un.astype(float) + altre.astype(float)) / 2


def iguals(prior: np.ndarray, altre_prior: np.ndarray, q: dict[str, np.ndarray],
           altra_q: dict[str, np.ndarray]) -> None:
    """S'atura si els dos models no tenen el mateix prior i la mateixa q a tots els escenaris."""
    if not np.array_equal(prior, altre_prior):
        raise RuntimeError(f"{A_EQUIPS} i {A_CANVIS} no tenen el mateix prior")
    if q.keys() != altra_q.keys() or not all(np.array_equal(q[e], altra_q[e]) for e in q):
        raise RuntimeError(f"{A_EQUIPS} i {A_CANVIS} no tenen la mateixa q")


def de_qui(metode: str, nom: str) -> tuple[dict[str, np.ndarray], np.ndarray, dict[str, np.ndarray]]:
    """Les probabilitats, el prior i la q d'A dos segons, o les dels altres mètodes (`mmc.de_qui`)."""
    if metode != A_DOS:
        return mmc.de_qui(metode, nom)
    equips, prior, q = mmc.de_qui(A_EQUIPS, nom)
    canvis, prior_canvis, q_canvis = mmc.de_qui(A_CANVIS, nom)
    iguals(prior, prior_canvis, q, q_canvis)
    if equips.keys() != canvis.keys():
        raise RuntimeError(f"{A_EQUIPS} i {A_CANVIS} no tenen els mateixos escenaris")
    return {e: mitjana(equips[e], canvis[e]) for e in equips}, prior, q


def graella(tasca: tuple[str, str, tuple[str, ...]]) -> list[dict]:
    """Com `mmc.graella`, amb A dos segons també."""
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


def encerts(tasca: tuple[str, str, dict[str, tuple]]) -> dict[str, list[dict]]:
    """Un partit i un escenari, amb el decodificador triat de cada mètode, a la veritat de toc: on encerten l'equip els
    tres segons, qui l'encerta on els dos segons no donen el mateix, i els canvis falsos de cada predicció."""
    nom, escenari, triats = tasca
    de_sempre = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    trams = avalua.trams_valids(replace(de_sempre, veritat=toc))
    valides = ssp.dins(len(toc), trams)
    vista = ~np.isnan(de_sempre.tracking.pilota[:, 0])
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}
    relatives, preds = {}, {}
    for metode, qui in DE_QUI.items():
        probes, prior, q_ = de_qui(metode, nom)
        relatives[qui] = log_relativa(probes[escenari].astype(float), prior)
        w, lam, d_min = triats[metode]
        preds[metode] = t3i.per_trams(relatives[qui], q_[escenari].astype(float), de_sempre.trams, w, lam, int(d_min))
    prop = mmc.a_prop(toc, de_sempre.trams, mmc.K)
    mascares = dict(zip(ON, (prop & vista, prop & ~vista, ~prop & vista, ~prop & ~vista)))
    files, desacords = [], []
    for on, mascara in mascares.items():
        for qui in QUI:
            n, e = ssp.encerts(relatives[qui], toc, mascara & valides)
            files.append({**comu, "on": on, "qui": qui, "n": n, "encerts": e})
        m = mascara & valides
        for relativa in relatives.values():
            m = ssp.d_equip(relativa, toc, m)
        equip = {qui: ssp.l_equip(relativa[m]) for qui, relativa in relatives.items()}
        dubte = equip[SEGON_EQUIPS] != equip[SEGON_CANVIS]
        bo = toc[m][dubte]
        desacords.append({**comu, "on": on, "n": int(m.sum()), "no diuen el mateix": int(dubte.sum()),
                          **{qui: int((eq[dubte] == bo).sum()) for qui, eq in equip.items()}})
    al_forat = sc.forats(vista)
    canvis_ = [{**comu, "metode": metode, **msp.falsos(pred, toc, trams, al_forat)} for metode, pred in preds.items()]
    return {"encerts": files, "desacords": desacords, "canvis": canvis_}


def _ordena(taula: pd.DataFrame) -> pd.DataFrame:
    ordre = {**{e: i for i, e in enumerate(ESCENARIS)}, **{o: i for i, o in enumerate(ON)}}
    return taula.sort_index(key=lambda idx: idx.map(lambda x: ordre.get(x, len(ordre))))


def taula_encerts(t: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i on: quantes imatges hi ha d'un equip, i la part on cadascú hi encerta l'equip."""
    g = t.groupby(["escenari", "on", "qui"], sort=False)[["n", "encerts"]].sum()
    part = (g["encerts"] / g["n"]).unstack("qui")[list(QUI)]
    n = g["n"].xs(LA_MITJANA, level="qui").rename("n imatges")
    return _ordena(pd.concat([n, part], axis=1))


def taula_desacords(t: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i on: la part de les imatges d'un equip on els dos segons no donen el mateix, i d'aquestes, la part
    on cadascú encerta l'equip."""
    g = t.groupby(["escenari", "on"], sort=False)[["n", "no diuen el mateix", *QUI]].sum()
    taula = pd.DataFrame({"n imatges": g["n"], "part on no diuen el mateix": g["no diuen el mateix"] / g["n"],
                          **{f"hi encerta {qui}": g[qui] / g["no diuen el mateix"] for qui in QUI}})
    return _ordena(taula)


def _regla(millor: dict[str, bool]) -> list[str]:
    es = all(millor.values())
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | "
            f"{mq._marca(millor['quarts'])} |",
            f"| «{mp.PARTIT}» | la diferència no és negativa | {mq._marca(millor['partit'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {mq._marca(millor['altres'])} |",
            "", f"**{A_DOS} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_DOS if es else A_EQUIPS}.", ""]


def markdown(metodes: pd.DataFrame, triades: dict, c: pd.DataFrame, passa: dict[str, bool], c_equips: pd.DataFrame,
             millor: dict[str, bool], per_font: dict[tuple[str, str], pd.DataFrame], encerts_: pd.DataFrame,
             desacords_: pd.DataFrame, canvis_: pd.DataFrame) -> str:
    linies = ["# Banc obert · La mitjana dels dos segons (T3aa)", "",
              "Generat amb `uv run python -I -m banc.model_dos_segons`. Dades obertes: 7 partits de DFL (IDSSE, CC BY",
              "4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el criteri:",
              "`docs/pla-tocs.md`, «T3aa», i la capçalera de `banc/model_dos_segons.py`. Es puntua a la veritat de toc.",
              "",
              f"**{XARXES_TOC}** i **{A_EQUIPS}** són els de la T3v, i **{A_CANVIS}**, el de la T3z, amb les peces de",
              "la memòria cau (✓ comprovat: a cada punt de la graella donen l'spellF1 d'aquells bancs, i els",
              f"decodificadors triats són els seus). **{A_DOS}** és, a cada imatge, la mitjana de les probabilitats dels",
              f"segons d'{A_EQUIPS} i d'{A_CANVIS}, amb el prior i la q que tenen tots dos. No s'entrena res.", "",
              f"## {A_DOS} contra {XARXES_TOC} (spellF1): el criteri", "",
              *t3b._taula(c, A_DOS, XARXES_TOC), "", *mt._criteris(passa),
              f"## {A_DOS} contra {A_EQUIPS} (spellF1)", "", *t3i._comparacio(c_equips, A_DOS, A_EQUIPS), ""]
    if not all(passa.values()):
        linies += ["## No passa: és el millor fins ara?", "",
                   f"La regla de la D-50, escrita abans, contra {A_EQUIPS}:", "", *_regla(millor)]
    for (font, contra), taula in per_font.items():
        linies += [f"## {A_DOS} contra {contra}, només els partits de {font}", "",
                   *t3i._comparacio(taula, A_DOS, contra), ""]
    quarts = encerts_["escenari"].isin(mp.QUARTS)
    linies += ["## On encerten l'equip els tres segons", "",
               "On la veritat de toc és d'un equip, la part de les imatges on l'equip més probable és el bo (amb la",
               "relativa), a ±0,5 s d'un canvi d'equip de la veritat de toc i a la resta.", "",
               t3p.md(taula_encerts(encerts_[quarts])), "",
               "## On els dos segons no donen el mateix equip", "",
               "On la veritat de toc és d'un equip: la part de les imatges on l'equip més probable dels dos segons no és",
               "el mateix, i d'aquestes, la part on cadascú encerta l'equip.", "",
               t3p.md(taula_desacords(desacords_[desacords_["escenari"].isin(mp.QUARTS)])), "",
               "## Els canvis d'equip de la predicció, i quants són falsos", "",
               f"Un canvi és fals si no n'hi ha cap de real a {msp.an.TOL} imatges o menys.", "",
               t3p.md(msp.taula_canvis(canvis_)), "",
               "## L'spellF1 de cada mètode (mitjana dels deu partits)", "",
               *mt._mitjanes(metodes, [XARXES_TOC, A_EQUIPS, A_CANVIS, A_DOS]), "## Els decodificadors triats", "",
               *mq._triades(triades), ""]
    return "\n".join(linies)


def banc_t3z() -> dict:
    return json.loads((DIR_RESULTATS / "model-mostres-canvis.json").read_text())


def comprova_la_t3z(files: pd.DataFrame) -> None:
    """A mostres als canvis, amb la memòria cau, dona a cada punt de la graella i a les dues veritats l'spellF1 del banc
    de la T3z."""
    aqui = files[files["metode"] == A_CANVIS][[*CLAUS, "spell_f1"]]
    banc = pd.DataFrame(banc_t3z()["files"])
    junts = aqui.merge(banc[[*CLAUS, "spell_f1"]], on=CLAUS, suffixes=("", " del banc"), how="outer")
    if (len(junts) != len(aqui) or len(aqui) != len(banc) or junts.isna().any().any()
            or not np.allclose(junts["spell_f1"], junts["spell_f1 del banc"], rtol=0, atol=1e-12)):
        raise RuntimeError(f"{A_CANVIS} no dona el del banc de la T3z")


def comprova_les_triades(triades: dict[str, dict]) -> None:
    """Els decodificadors d'A xarxes i d'A equips sencers són els de la T3v, i els d'A mostres als canvis, els de la
    T3z."""
    mpc.comprova_les_triades(triades)
    de_la_t3z = banc_t3z()["triades"][A_CANVIS]
    for prova, triat in triades[A_CANVIS].items():
        if list(triat) != list(de_la_t3z[prova]):
            raise RuntimeError(f"{prova}: el decodificador d'{A_CANVIS} no és el de la T3z ({triat})")


def clau_dels_resultats() -> str:
    h = hashlib.sha256(mmc.clau_dels_resultats().encode())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_dos_segons as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        return list(feina.map(getattr(aquest, fes), tasques))


def files_de(metodes: tuple[str, ...], processos: int) -> pd.DataFrame:
    tasques = [(nom, e, metodes) for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    return pd.DataFrame([f for tros in en_paral_lel("graella", tasques, processos) for f in tros])


def escriu(contingut: dict, md: str) -> None:
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-dos-segons.json").write_text(json.dumps(contingut, indent=1, default=float,
                                                                    allow_nan=False))
    (DIR_RESULTATS / "model-dos-segons.md").write_text(md)
    print(md)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    args = ap.parse_args()
    for nom in fonts.NOMS:
        for metode in (XARXES, A_EQUIPS, A_CANVIS, A_DOS):
            de_qui(metode, nom)
        vt.veritat(nom)
    files = files_de((XARXES, A_EQUIPS, A_CANVIS), args.processos)
    mpc.comprova_les_d_abans(files)
    comprova_la_t3z(files)
    print(f"· {XARXES} i {A_EQUIPS} donen el del banc de la T3v, i {A_CANVIS}, el de la T3z", flush=True)
    files = pd.concat([files, files_de((A_DOS,), args.processos)], ignore_index=True)
    de_xarxes, triades_xarxes = mt.tria_sense_mirar(files, XARXES, TOC, XARXES_TOC)
    de_equips, triades_equips = mt.tria_sense_mirar(files, A_EQUIPS, TOC, A_EQUIPS)
    de_canvis, triades_canvis = mt.tria_sense_mirar(files, A_CANVIS, TOC, A_CANVIS)
    de_dos, triades_dos = mt.tria_sense_mirar(files, A_DOS, TOC, A_DOS)
    triades = {XARXES_TOC: triades_xarxes, A_EQUIPS: triades_equips, A_CANVIS: triades_canvis, A_DOS: triades_dos}
    comprova_les_triades(triades)
    metodes = pd.concat([de_xarxes, de_equips, de_canvis, de_dos], ignore_index=True)
    c = mt.comparacio(metodes, A_DOS, XARXES_TOC, TOC, amb_criteri=True)
    c_equips = mt.comparacio(metodes, A_DOS, A_EQUIPS, TOC, amb_criteri=False)
    passa, millor = mt.compleix(c), mq.millor_fins_ara(c_equips)
    per_font = {(font, contra): mt.comparacio(metodes[metodes["font"] == font], A_DOS, contra, TOC,
                                              amb_criteri=False)
                for font in FONTS for contra in (XARXES_TOC, A_EQUIPS)}
    tasques = [(nom, e, {metode: triades[metode][nom] for metode in DE_QUI})
               for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    trossos = en_paral_lel("encerts", tasques, args.processos)
    encerts_, desacords_, canvis_ = (pd.DataFrame([f for tros in trossos for f in tros[clau_]])
                                     for clau_ in ("encerts", "desacords", "canvis"))
    contingut = {"clau": clau_dels_resultats(), "passa": passa, "millor_fins_ara": millor,
                 "comparacio": t3.registres(c), "contra_a_equips_sencers": t3.registres(c_equips),
                 "triades": triades, "files": t3.registres(files[files["metode"] == A_DOS]),
                 "per_font": {f"{font} · {contra}": t3.registres(t) for (font, contra), t in per_font.items()},
                 "encerts": t3.registres(encerts_), "desacords": t3.registres(desacords_),
                 "canvis": t3.registres(canvis_)}
    escriu(contingut, markdown(metodes, triades, c, passa, c_equips, millor, per_font, encerts_, desacords_, canvis_))


if __name__ == "__main__":
    main()
