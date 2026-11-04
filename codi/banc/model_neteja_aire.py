"""A aire ×¼, la neteja de la T3w i la D impossible on s'ha tret la pilota (T3ac del pla per tocs, `docs/pla-tocs.md`,
«T3ac»; D-64).

    cd codi && uv run python -I -m banc.model_neteja_aire [--processos 12]

A pilota creïble (T3w) tal qual, de la memòria cau (`banc/model_pilota_creible.py`), amb dues diferències:

- **la D impossible a les imatges on la neteja ha tret la pilota** (`cadena/pilota_creible.py`, la pilota vista a
  10 m o més fora del camp): abans de decodificar, la seva probabilitat relativa hi passa a −`IMPOSSIBLE`, i l'H i
  l'A, com estaven (`amb_la_d_impossible`). Els sostres hi posen −30, però amb λ = 32 i 12 imatges de durada mínima
  el decodificador encara hi pot deixar la D; `IMPOSSIBLE` és més que el que costa qualsevol camí sense la D;
- **el decodificador de cada partit, el d'A equips sencers,** sense tornar-lo a triar: la regla de la D-64 per als
  passos que només canvien l'entrada d'alguns escenaris.

No s'entrena res.

1. **En començar:** A xarxes i A equips sencers, amb la memòria cau, han de donar a cada punt de la graella i a les
   dues veritats l'spellF1 del banc de la T3v, i A pilota creïble, el del banc de la T3w. Els decodificadors triats de
   tots tres han de ser els d'aquells bancs.
2. **A cada partit i escenari,** amb el decodificador d'A equips sencers: A neteja d'aire no hi ha de donar mai la D a
   les imatges netejades, i on la neteja no treu res, A neteja d'aire i A pilota creïble han de donar exactament la
   predicció d'A equips sencers. Si no, s'atura.
3. **El criteri** del pla: A neteja d'aire contra A xarxes, a la veritat de toc. Si no passa, la regla de la D-55 a
   aire ×¼, contra A equips sencers. Només per saber-ho: per font; A pilota creïble amb el decodificador d'A equips
   sencers, que és la neteja sola; a aire ×¼ de DFL, on la veritat és d'un equip, la part on cadascú hi dona la D
   segons a quina distància s'ha vist la pilota (`banc/la_d_a_aire.py`); i la D de la veritat que cau a les imatges
   on la D és impossible.

Escriu `resultats/model-neteja-aire.json` i `resultats/model-neteja-aire.md`. Tot són dades obertes. Els mòduls d'abans
no es toquen.
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
from banc import errors_als_forats as eaf
from banc import la_d_a_aire as lda
from banc import model_a_canvis as t3i
from banc import model_a_partit as mp
from banc import model_a_q as mq
from banc import model_a_quart as t3b
from banc import model_a_toc as mt
from banc import model_pilota_creible as mpc
from banc import sostre_sense_pilota as ssp
from banc import veritat_toc as vt
from cadena import decodifica_tocs as dt
from cadena import pilota_creible as pc
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ESCENARIS = mp.ESCENARIS                            # els deu de la T3 i «partit ×¼»
AIRE = mpc.AIRE                                     # l'escenari on va
XARXES, XARXES_TOC, A_EQUIPS, A_CREIBLE = mpc.XARXES, mpc.XARXES_TOC, mpc.A_EQUIPS, mpc.A_CREIBLE
A_NETEJA = "A neteja d'aire"
A_CREIBLE_EQ = "A pilota creïble, decodificador d'A equips sencers"    # la neteja sola: només per saber-ho
SEMPRE, TOC = mpc.SEMPRE, mpc.TOC
FONTS = mpc.FONTS
LA_D_DE = (A_EQUIPS, A_CREIBLE_EQ, A_NETEJA)
CLAUS = ["partit", "escenari", "metode", "veritat", "w", "lam", "d_min"]
IMPOSSIBLE = 1e4          # per imatge: més que els canvis i la durada mínima de qualsevol camí sense la D
DIR_RESULTATS = t3.DIR_RESULTATS


def amb_la_d_impossible(relativa: np.ndarray, on: np.ndarray) -> np.ndarray:
    """La probabilitat relativa amb la D impossible a les imatges d'`on`; l'H, l'A i la resta d'imatges, com estaven."""
    out = relativa.copy()
    out[on, dt.D] = -IMPOSSIBLE
    return out


def d_de_la_veritat(toc: np.ndarray, on: np.ndarray, valides: np.ndarray) -> dict[str, int]:
    """A les imatges vàlides: quantes n'hi ha d'`on`, quantes són D a la veritat, i quantes d'aquestes són d'`on`."""
    d = valides & (toc == pm.D)
    return {"netejades": int((on & valides).sum()), "d": int(d.sum()), "d_netejades": int((d & on).sum())}


def prediccio(relativa: np.ndarray, q: np.ndarray, trams: tuple, triat: tuple) -> np.ndarray:
    w, lam, d_min = triat
    return t3i.per_trams(relativa, q.astype(float), trams, w, lam, int(d_min))


def fixes(tasca: tuple[str, str, tuple]) -> dict[str, list[dict]]:
    """Un partit i un escenari, amb el decodificador d'A equips sencers (`triat`): les files d'A neteja d'aire i d'A
    pilota creïble a les dues veritats, la D de la veritat a les imatges netejades i, a aire ×¼, la D per distància.
    S'atura si A neteja d'aire dona la D a una imatge netejada, o si on la neteja no treu res no dona exactament el
    que A equips sencers."""
    nom, escenari, triat = tasca
    de_sempre = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    partits = {SEMPRE: de_sempre, TOC: replace(de_sempre, veritat=toc)}
    netejades = pc.lluny(de_sempre.tracking)
    equips, prior, q_ = mpc.de_qui(A_EQUIPS, nom)
    creible, prior_creible, q_creible = mpc.de_qui(A_CREIBLE, nom)       # la q, la d'A pilota creïble (T3w)
    relatives = {A_EQUIPS: log_relativa(equips[escenari].astype(float), prior),
                 A_CREIBLE_EQ: log_relativa(creible[escenari].astype(float), prior_creible)}
    relatives[A_NETEJA] = amb_la_d_impossible(relatives[A_CREIBLE_EQ], netejades)
    qs = {A_EQUIPS: q_[escenari], A_CREIBLE_EQ: q_creible[escenari], A_NETEJA: q_creible[escenari]}
    preds = {metode: prediccio(r, qs[metode], de_sempre.trams, triat) for metode, r in relatives.items()}
    if (preds[A_NETEJA][netejades] == pm.D).any():
        raise RuntimeError(f"{nom}, {escenari}: {A_NETEJA} dona la D a una imatge netejada")
    if not netejades.any() and not all(np.array_equal(preds[m], preds[A_EQUIPS]) for m in (A_CREIBLE_EQ, A_NETEJA)):
        raise RuntimeError(f"{nom}, {escenari}: la neteja no treu res, i la predicció no és la d'{A_EQUIPS}")
    w, lam, d_min = triat
    files = [{"partit": nom, "font": p.font, "escenari": escenari, "metode": metode, "veritat": veritat, "w": w,
              "lam": lam, "d_min": d_min, **avalua.puntua(p, preds[metode])}
             for metode in (A_CREIBLE_EQ, A_NETEJA) for veritat, p in partits.items()]
    valides = ssp.dins(len(toc), avalua.trams_valids(partits[TOC]))
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}
    perduda = [{**comu, **d_de_la_veritat(toc, netejades, valides)}]
    la_d_ = []
    if escenari == AIRE:
        vista, distancia = ~np.isnan(de_sempre.tracking.pilota[:, 0]), lda.distancies(de_sempre)
        for metode in LA_D_DE:
            c = lda.comptes(preds[metode], toc, relatives[metode], vista, distancia, valides)
            la_d_ += [{**comu, "metode": metode, **r} for r in c.to_dict("records")]
    return {"files": files, "perduda": perduda, "la_d": la_d_}


def banc_t3w() -> dict:
    return json.loads((DIR_RESULTATS / "model-pilota-creible.json").read_text())


def comprova_la_t3w(files: pd.DataFrame) -> None:
    """A pilota creïble, amb la memòria cau, dona a cada punt de la graella i a les dues veritats l'spellF1 del banc de
    la T3w."""
    aqui = files[files["metode"] == A_CREIBLE][[*CLAUS, "spell_f1"]]
    banc = pd.DataFrame(banc_t3w()["files"])
    junts = aqui.merge(banc[[*CLAUS, "spell_f1"]], on=CLAUS, suffixes=("", " del banc"), how="outer")
    if (len(junts) != len(aqui) or len(aqui) != len(banc) or junts.isna().any().any()
            or not np.allclose(junts["spell_f1"], junts["spell_f1 del banc"], rtol=0, atol=1e-12)):
        raise RuntimeError(f"{A_CREIBLE} no dona el del banc de la T3w")


def comprova_les_triades(triades: dict[str, dict]) -> None:
    """Els decodificadors d'A xarxes i d'A equips sencers són els de la T3v, i els d'A pilota creïble, els de la T3w."""
    mpc.comprova_les_triades(triades)
    de_la_t3w = banc_t3w()["triades"][A_CREIBLE]
    for prova, triat in triades[A_CREIBLE].items():
        if list(triat) != list(de_la_t3w[prova]):
            raise RuntimeError(f"{prova}: el decodificador d'{A_CREIBLE} no és el de la T3w ({triat})")


def taula_perduda(t: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i font, on la neteja treu alguna imatge: les imatges netejades, la D de la veritat i quina part
    d'aquesta D cau a les netejades."""
    g = t.groupby(["escenari", "font"])[["netejades", "d", "d_netejades"]].sum()
    g = g[g["netejades"] > 0]
    g = g.assign(part=g["d_netejades"] / g["d"]).rename(columns={
        "netejades": "n imatges netejades", "d": "n D de la veritat", "d_netejades": "n d'aquesta, a les netejades"})
    return eaf.en_ordre(g, ESCENARIS, FONTS)


def taula_la_d(t: pd.DataFrame) -> pd.DataFrame:
    """On la veritat és d'un equip: per on es veu la pilota i la distància, quina part d'aquestes imatges hi ha, i a
    quina part la predicció de cada mètode hi dona la D. A sota, a totes."""
    equip = t[t["veritat"] == lda.D_UN_EQUIP]
    g = equip.groupby(["on", "distancia", "metode"])[["n", "d"]].sum()
    n = g["n"].xs(A_NETEJA, level="metode")
    files = pd.concat([(n / n.sum()).rename("imatges d'un equip"),
                       (g["d"] / g["n"]).unstack("metode")[list(LA_D_DE)].add_prefix("la D · ")], axis=1)
    files = eaf.en_ordre(files, lda.ONS, lda.NOMS)
    totes = equip.groupby("metode")[["n", "d"]].sum()
    files.loc[(mpc.TOTES, ""), :] = [1.0, *(totes["d"] / totes["n"])[list(LA_D_DE)]]
    return files.rename_axis(["on", "distància"])


def _regla(millor: dict[str, bool]) -> list[str]:
    es = all(millor.values())
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| {AIRE} | la diferència és positiva i l'interval del 95 % no toca el zero | "
            f"{mq._marca(millor['escenari'])} |",
            f"| Els altres tres ×¼ i «{mp.PARTIT}» | la diferència no és negativa | {mq._marca(millor['quarts'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {mq._marca(millor['altres'])} |",
            "", f"**{A_NETEJA} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_NETEJA if es else A_EQUIPS}.", ""]


def markdown(metodes: pd.DataFrame, triades: dict, c: pd.DataFrame, passa: dict[str, bool], c_equips: pd.DataFrame,
             millor: dict[str, bool], c_sola: pd.DataFrame, per_font: dict[tuple[str, str], pd.DataFrame],
             perduda: pd.DataFrame, la_d_: pd.DataFrame) -> str:
    linies = ["# Banc obert · A aire ×¼, la neteja de la T3w i la D impossible on s'ha tret la pilota (T3ac)", "",
              "Generat amb `uv run python -I -m banc.model_neteja_aire`. Dades obertes: 7 partits de DFL (IDSSE, CC BY",
              "4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3ac», i la capçalera de `banc/model_neteja_aire.py`. Es puntua a la",
              "veritat de toc.", "",
              f"**{XARXES_TOC}** i **{A_EQUIPS}** són els de la T3v, i **{A_CREIBLE}**, el de la T3w, amb les peces de",
              "la memòria cau (✓ comprovat: a cada punt de la graella donen l'spellF1 d'aquells bancs, i els",
              f"decodificadors triats són els seus). **{A_NETEJA}** és {A_CREIBLE}, amb la D impossible a les imatges",
              "on la neteja ha tret la pilota, i el decodificador d'A equips sencers a cada partit (la regla de la",
              "D-64). No s'entrena res. ✓ Comprovat a cada partit i escenari: no dona mai la D a una imatge",
              f"netejada, i on la neteja no treu res, dona exactament la predicció d'{A_EQUIPS}.", "",
              "## La D de la veritat que cau a les imatges netejades", "",
              "Als trams vàlids, on la neteja treu alguna imatge: allà la D és impossible, i la de la veritat es perd.",
              "", t3p.md(taula_perduda(perduda)), "",
              f"## {A_NETEJA} contra {XARXES_TOC} (spellF1): el criteri", "",
              *t3b._taula(c, A_NETEJA, XARXES_TOC), "", *mt._criteris(passa),
              f"## {A_NETEJA} contra {A_EQUIPS} (spellF1)", "", *t3i._comparacio(c_equips, A_NETEJA, A_EQUIPS), ""]
    if not all(passa.values()):
        linies += ["## No passa: és el millor fins ara?", "",
                   "La regla dels passos que només van a un escenari (D-55), escrita abans, contra "
                   f"{A_EQUIPS}:", "", *_regla(millor)]
    for (font, contra), taula in per_font.items():
        linies += [f"## {A_NETEJA} contra {contra}, només els partits de {font}", "",
                   *t3i._comparacio(taula, A_NETEJA, contra), ""]
    linies += [f"## La neteja sola, amb el decodificador d'{A_EQUIPS}: contra {A_EQUIPS}", "",
               f"{A_CREIBLE} sense la D impossible, i amb el mateix decodificador que {A_EQUIPS}. Només per saber-ho.",
               "", *t3i._comparacio(c_sola, A_CREIBLE_EQ, A_EQUIPS), "",
               f"## La D a {AIRE}, a DFL", "",
               "Als trams vàlids, on la veritat de toc és d'un equip: per on es veu la pilota i a quants metres de la",
               "línia s'ha vist fora del camp (on es veu, la seva; als forats, la més gran de la pilota vista just",
               "abans i just després), quina part d'aquestes imatges hi ha, i a quina part la predicció hi dona la D.",
               f"Tot, a l'escenari sense netejar, i els tres amb el decodificador d'{A_EQUIPS}.", "",
               t3p.md(taula_la_d(la_d_[la_d_["font"] == "dfl"])), "",
               "## L'spellF1 de cada mètode (mitjana dels deu partits)", "",
               *mt._mitjanes(metodes, [XARXES_TOC, A_EQUIPS, A_CREIBLE_EQ, A_NETEJA]),
               "## Els decodificadors triats", "",
               f"{A_NETEJA} i {A_CREIBLE_EQ} fan servir, a cada partit, el d'{A_EQUIPS}. El d'{A_CREIBLE}, el de la",
               "T3w, només per comprovar-lo.", "", *mq._triades(triades), ""]
    return "\n".join(linies)


def clau_dels_resultats() -> str:
    h = hashlib.sha256(mpc.clau_dels_resultats().encode())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_neteja_aire as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        return list(feina.map(getattr(aquest, fes), tasques))


def escriu(contingut: dict, md: str) -> None:
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-neteja-aire.json").write_text(json.dumps(contingut, indent=1, default=float,
                                                                     allow_nan=False))
    (DIR_RESULTATS / "model-neteja-aire.md").write_text(md)
    print(md)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    args = ap.parse_args()
    for nom in fonts.NOMS:
        for metode in (XARXES, A_EQUIPS, A_CREIBLE):
            mpc.de_qui(metode, nom)
        vt.veritat(nom)
    files = mpc.files_de((XARXES, A_EQUIPS, A_CREIBLE), args.processos)
    mpc.comprova_les_d_abans(files)
    comprova_la_t3w(files)
    de_xarxes, triades_xarxes = mt.tria_sense_mirar(files, XARXES, TOC, XARXES_TOC)
    de_equips, triades_equips = mt.tria_sense_mirar(files, A_EQUIPS, TOC, A_EQUIPS)
    _, triades_creible = mt.tria_sense_mirar(files, A_CREIBLE, TOC, A_CREIBLE)
    triades = {XARXES_TOC: triades_xarxes, A_EQUIPS: triades_equips, A_CREIBLE: triades_creible}
    comprova_les_triades(triades)
    print(f"· {XARXES} i {A_EQUIPS} donen el del banc de la T3v, i {A_CREIBLE}, el de la T3w", flush=True)
    tasques = [(nom, e, triades_equips[nom]) for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    trossos = en_paral_lel("fixes", tasques, args.processos)
    fixes_, perduda, la_d_ = (pd.DataFrame([f for tros in trossos for f in tros[clau_]])
                              for clau_ in ("files", "perduda", "la_d"))
    print(f"· {A_NETEJA}: mai la D a les imatges netejades, i on no se'n neteja cap, la d'{A_EQUIPS}", flush=True)
    metodes = pd.concat([de_xarxes, de_equips, fixes_], ignore_index=True)
    c = mt.comparacio(metodes, A_NETEJA, XARXES_TOC, TOC, amb_criteri=True)
    c_equips = mt.comparacio(metodes, A_NETEJA, A_EQUIPS, TOC, amb_criteri=False)
    c_sola = mt.comparacio(metodes, A_CREIBLE_EQ, A_EQUIPS, TOC, amb_criteri=False)
    passa, millor = mt.compleix(c), mpc.millor_d_un_escenari(c_equips, AIRE)
    per_font = {(font, contra): mt.comparacio(metodes[metodes["font"] == font], A_NETEJA, contra, TOC,
                                              amb_criteri=False)
                for font in FONTS for contra in (XARXES_TOC, A_EQUIPS)}
    contingut = {"clau": clau_dels_resultats(), "passa": passa, "millor_fins_ara": millor,
                 "comparacio": t3.registres(c), "contra_a_equips_sencers": t3.registres(c_equips),
                 "la_neteja_sola": t3.registres(c_sola), "triades": triades, "files": t3.registres(fixes_),
                 "per_font": {f"{font} · {contra}": t3.registres(t) for (font, contra), t in per_font.items()},
                 "perduda": t3.registres(perduda), "la_d": t3.registres(la_d_)}
    escriu(contingut, markdown(metodes, triades, c, passa, c_equips, millor, c_sola, per_font, perduda, la_d_))


if __name__ == "__main__":
    main()
