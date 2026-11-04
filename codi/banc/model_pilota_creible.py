"""La pilota a 10 m o més fora del camp, com un forat (T3w del pla per tocs, `docs/pla-tocs.md`, «T3w»; D-55).

    cd codi && uv run python -I -m banc.model_pilota_creible [--processos 12] [--processos-models 3]

A equips sencers tal qual, amb una sola diferència: a l'entrada de la cadena, la pilota vista a 10 m o més de la
línia, fora del camp, es tracta com si no es veiés (`cadena/pilota_creible.py`). L'alçada de la pilota no es toca: cap
peça no la llegeix.

1. **On canvia l'entrada,** a cada partit i escenari. Als sis escenaris d'entrenament no hi pot canviar res: si
   canviés, s'atura. Així les peces dels grups (entrenades amb els altres partits) són les de la memòria cau.
2. **En començar,** A xarxes i A equips sencers, amb la memòria cau, han de donar a cada punt de la graella i a les
   dues veritats l'spellF1 del banc de la T3v.
3. **Les peces del partit que es prova,** entrenades com a la T3v amb els altres nou (el primer i la q, els d'A
   xarxes; les cinc xarxes i el segon, els d'A equips sencers) i aplicades al partit netejat. El banc de la T3v només
   en desa les probabilitats, i per tenir-les on la neteja canvia l'entrada cal tornar-les a entrenar. A mesura que
   surt cada peça, als escenaris on la neteja no canvia res, ha de ser exactament la de la memòria cau; si no, s'atura
   (`dades/banc/pilota-creible/`).
4. **El decodificador,** amb la graella de la T3j, triat amb els altres nou als quatre ×¼ a la veritat de toc. Els
   d'A xarxes i d'A equips sencers han de ser els de la T3v.
5. **El criteri** del pla: A pilota creïble contra A xarxes, a la veritat de toc. Si no passa, la regla del millor
   fins ara per als passos que només van a un escenari (D-55), contra A equips sencers, a aire ×¼. Només per saber-ho:
   per font, quantes imatges canvia la neteja, i a aire ×¼ de DFL, on la veritat és d'un equip, la part on la
   predicció hi dona la D segons a quina distància s'ha vist la pilota (`banc/la_d_a_aire.py`).

Escriu `resultats/model-pilota-creible.json` i `resultats/model-pilota-creible.md`. Tot són dades obertes. Els mòduls
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

import lightgbm as lgb
import numpy as np
import pandas as pd

from banc import analisi_t3p as t3p
from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import errors_als_forats as eaf
from banc import la_d_a_aire as lda
from banc import model_a_canvis as t3i
from banc import model_a_canvis2 as t3j
from banc import model_a_contacte as t3h
from banc import model_a_equips as mae
from banc import model_a_partit as mp
from banc import model_a_q as mq
from banc import model_a_quart as t3b
from banc import model_a_toc as mt
from banc import model_a_xarxa as t3m
from banc import sostre_sense_pilota as ssp
from banc import veritat_toc as vt
from banc.partit import PartitBanc
from cadena import model
from cadena import pilota_creible as pc
from cadena import xarxa_equips as xeq
from possessio.decodificacio import log_relativa

ESCENARIS = mp.ESCENARIS                            # els deu de la T3 i «partit ×¼»
SIS = mp.SIS
AIRE = "aire ×¼"                                    # l'escenari on va
XARXES, XARXES_TOC = mt.XARXES, mt.XARXES_TOC
A_EQUIPS = mae.A_EQUIPS
A_CREIBLE = "A pilota creïble"
SEMPRE, TOC = mt.SEMPRE, mt.TOC
FONTS = mae.FONTS
PECES = {"el primer": "primer", "la q": "q", "les cinc xarxes": "xarxes_de_la_prova", "el segon": "segon"}
TOTES = "totes"
DIR_CAU = fonts.DIR_CAU / "pilota-creible"
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


def cau(peca: str, prova: str) -> Path:
    return DIR_CAU / f"{peca}-{prova}.npz"


def per_escenari(desat: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    return {e: desat[f"e{i}"] for i, e in enumerate(ESCENARIS)}


def creible(nom: str, escenari: str) -> PartitBanc:
    """El partit degradat, amb la pilota netejada."""
    p = mp.degradat(nom, escenari)
    return replace(p, tracking=pc.neteja(p.tracking))


def falta(peca: str, prova: str) -> RuntimeError:
    return RuntimeError(f"Falta {peca} d'{A_CREIBLE} de {prova}, o és d'un altre codi")


def primer(prova: str, entrena: bool = True) -> dict[str, np.ndarray]:
    """Les del primer al partit `prova` netejat, a tots els escenaris: entrenat com a `mp.primer_de_la_prova`, amb els
    altres nou als sis escenaris d'entrenament."""
    cami = cau("primer", prova)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise falta("el primer", prova)
        entrenat = mp.entrena_primer([nom for nom in fonts.NOMS if nom != prova], SIS)
        mp.mostres_primer.cache_clear()                # per la memòria: el procés fa després les altres peces
        desat = {f"e{i}": model.probabilitats(entrenat, t3h.taula_primer(creible(prova, e))).astype(np.float32)
                 for i, e in enumerate(ESCENARIS)}
        desa(cami, **desat)
    return per_escenari(desat)


def q(prova: str, entrena: bool = True) -> dict[str, np.ndarray]:
    """Les q al partit `prova` netejat, a tots els escenaris: entrenat com a `mp.q`, amb el primer d'aquí."""
    cami = cau("q", prova)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise falta("la q", prova)
        x, y = mp.mostres_q(prova, SIS)
        entrenat = lgb.train(t3i.PARAMS, lgb.Dataset(x, label=y, free_raw_data=True), num_boost_round=model.RONDES)
        del x
        primers = primer(prova, entrena=False)
        desat = {}
        for i, e in enumerate(ESCENARIS):
            p = creible(prova, e)
            desat[f"e{i}"] = t3i.q_de(entrenat, t3h.taula_segon(p, primers[e].astype(float))).astype(np.float32)
        desa(cami, **desat)
    return per_escenari(desat)


def xarxes_de_la_prova(prova: str, entrena: bool = True) -> dict[str, np.ndarray]:
    """La mitjana de les cinc xarxes d'A equips sencers al partit `prova` netejat, a tots els escenaris: entrenades com
    a `mae.xarxes_de_la_prova`, amb els altres nou."""
    cami = cau("xarxes", prova)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise falta("les cinc xarxes", prova)
        entrenades, perdues = mae.entrena_xarxes([nom for nom in fonts.NOMS if nom != prova])
        desat = {}
        for i, e in enumerate(ESCENARIS):
            p = creible(prova, e)
            desat[f"e{i}"] = xeq.probabilitats(entrenades, p.tracking, p.trams).astype(np.float32)
        desa(cami, perdues=np.array(perdues), **desat)
    return per_escenari(desat)


def segon(prova: str, entrena: bool = True) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Les probabilitats d'A pilota creïble al partit `prova`, a tots els escenaris, i el prior: el segon entrenat com
    a `mae.segon`, amb el primer i les xarxes d'aquí."""
    cami = cau("segon", prova)
    desat = llegeix(cami)
    if desat is None:
        if not entrena:
            raise falta("el segon", prova)
        x, y = mae.mostres_segon(prova)
        entrenat, prior = model.entrena(x, y), model.prior(y)
        del x
        primers, de_les_xarxes = primer(prova, entrena=False), xarxes_de_la_prova(prova, entrena=False)
        desat = {"prior": prior}
        for i, e in enumerate(ESCENARIS):
            p = creible(prova, e)
            taula = t3m.taula_segon(p, primers[e].astype(float), de_les_xarxes[e].astype(float))
            desat[f"e{i}"] = model.probabilitats(entrenat, taula).astype(np.float32)
        desa(cami, **desat)
    return per_escenari(desat), desat["prior"]


def de_la_t3v(peca: str, nom: str) -> dict[str, np.ndarray]:
    """La peça d'A equips sencers, de la memòria cau (el segon, amb el prior)."""
    if peca == "el primer":
        desat = mp.llegeix(mp.cau("primer", SIS, nom))
        if desat is None:
            raise RuntimeError(f"Falta el primer de {nom} a la memòria cau de la T3p, o és d'un altre codi")
        return per_escenari(desat)
    if peca == "la q":
        return mp.q((nom, SIS), entrena=False)
    if peca == "les cinc xarxes":
        return mae.xarxes_de_la_prova(nom, entrena=False)
    probes, prior = mae.segon(nom, entrena=False)
    return {**probes, "prior": prior}


def canvis(tasca: tuple[str, str]) -> dict:
    """Un partit i un escenari: on es veu la pilota, i quantes d'aquestes imatges canvia la neteja."""
    nom, escenari = tasca
    p = mp.degradat(nom, escenari)
    return {"partit": nom, "font": p.font, "escenari": escenari,
            "vistes": int((~np.isnan(p.tracking.pilota[:, 0])).sum()), "canvien": int(pc.lluny(p.tracking).sum())}


def comprova_l_entrenament(canvis_: pd.DataFrame) -> None:
    """Als sis escenaris d'entrenament, la neteja no hi pot canviar cap imatge de cap partit."""
    dolents = canvis_[canvis_["escenari"].isin(SIS) & (canvis_["canvien"] > 0)]
    if len(dolents):
        raise RuntimeError("La neteja canvia escenaris d'entrenament: "
                           + ", ".join(f"{f.partit} a {f.escenari}" for f in dolents.itertuples()))


def sense_canvis(canvis_: pd.DataFrame, prova: str) -> list[str]:
    """Els escenaris on la neteja no canvia cap imatge del partit `prova`, en ordre."""
    seus = canvis_[(canvis_["partit"] == prova) & (canvis_["canvien"] == 0)]["escenari"]
    return [e for e in ESCENARIS if e in set(seus)]


def comprova_igual(peca: str, prova: str, nou: dict[str, np.ndarray], desat: dict[str, np.ndarray],
                   claus: list[str]) -> None:
    """A cada clau, `nou` ha de ser exactament `desat`."""
    for k in claus:
        if mp.diferencia(nou[k], desat[k]) != 0:
            raise RuntimeError(f"{prova}, {k}: {peca} no surt igual que a la memòria cau, i la neteja no hi canvia "
                               "res")


def entrena_les_peces(processos: int, canvis_: pd.DataFrame) -> None:
    """Les peces del partit que es prova, una darrere l'altra. Cadascuna, a mesura que surt, igual que la de la
    memòria cau on la neteja no canvia res."""
    from banc import model_pilota_creible as aquest     # pel nom del mòdul, perquè els processos fills el trobin

    with ProcessPoolExecutor(max_workers=processos) as feina:
        for peca, fes in PECES.items():
            for nom, nou in zip(fonts.NOMS, feina.map(getattr(aquest, fes), fonts.NOMS)):
                if peca == "el segon":
                    nou = {**nou[0], "prior": nou[1]}
                claus = sense_canvis(canvis_, nom) + (["prior"] if peca == "el segon" else [])
                comprova_igual(peca, nom, nou, de_la_t3v(peca, nom), claus)
                print(f"· {peca} de {nom}: fet, i igual que a la T3v a {len(claus)} escenaris", flush=True)


def de_qui(metode: str, nom: str) -> tuple[dict[str, np.ndarray], np.ndarray, dict[str, np.ndarray]]:
    """Les probabilitats, el prior i la q d'A pilota creïble, o les d'A xarxes o A equips sencers (`mae.de_qui`)."""
    if metode != A_CREIBLE:
        return mae.de_qui(metode, nom)
    probes, prior = segon(nom, entrena=False)
    return probes, prior, q(nom, entrena=False)


def graella(tasca: tuple[str, str, tuple[str, ...]]) -> list[dict]:
    """Com `mae.graella`, amb A pilota creïble també."""
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


def banc_t3v() -> dict:
    return json.loads((DIR_RESULTATS / "model-a-equips.json").read_text())


def comprova_les_d_abans(files: pd.DataFrame) -> None:
    """A xarxes i A equips sencers, amb la memòria cau, donen a cada punt de la graella i a les dues veritats
    l'spellF1 del banc de la T3v."""
    claus = ["partit", "escenari", "metode", "veritat", "w", "lam", "d_min"]
    aqui = files[files["metode"].isin((XARXES, A_EQUIPS))][[*claus, "spell_f1"]]
    banc = pd.DataFrame(banc_t3v()["files"])
    banc = banc[banc["metode"].isin((XARXES, A_EQUIPS))]
    junts = aqui.merge(banc[[*claus, "spell_f1"]], on=claus, suffixes=("", " del banc"), how="outer")
    if (len(junts) != len(aqui) or junts.isna().any().any()
            or not np.allclose(junts["spell_f1"], junts["spell_f1 del banc"], rtol=0, atol=1e-12)):
        raise RuntimeError(f"{XARXES} o {A_EQUIPS} no donen el del banc de la T3v")


def comprova_les_triades(triades: dict[str, dict]) -> None:
    """Els decodificadors d'A xarxes i d'A equips sencers, triats aquí, són els de la T3v."""
    de_la_t3v = banc_t3v()["triades"]
    for metode in (XARXES_TOC, A_EQUIPS):
        for prova, triat in triades[metode].items():
            if list(triat) != list(de_la_t3v[metode][prova]):
                raise RuntimeError(f"{prova}: el decodificador d'{metode} no és el de la T3v ({triat})")


def millor_d_un_escenari(c: pd.DataFrame, escenari: str) -> dict[str, bool]:
    """La regla dels passos que només van a un escenari (D-55), escrita abans: a `escenari`, la diferència és positiva
    i l'interval del 95 % no toca el zero; als altres tres ×¼ i a «partit ×¼», no és negativa; a la resta, no baixa
    de −`t3.SOROLL`."""
    if sorted(c["escenari"]) != sorted(ESCENARIS) or escenari not in t3.QUARTS:
        raise ValueError(f"Cal una comparació a tots els escenaris, i un dels quatre ×¼ (no {escenari})")
    seu = c["escenari"] == escenari
    quarts = c["escenari"].isin(mp.QUARTS) & ~seu
    return {"escenari": bool(((c["diferencia"] > 0) & (c["baix"] > 0))[seu].all()),
            "quarts": bool((c["diferencia"] >= 0)[quarts].all()),
            "altres": bool((c["diferencia"] >= -t3.SOROLL)[~seu & ~quarts].all())}


def la_d(tasca: tuple[str, dict[str, dict]]) -> list[dict]:
    """Un partit, a aire ×¼: els comptes de `lda.comptes` d'A equips sencers i d'A pilota creïble, amb el decodificador
    triat de cadascun. On es veu la pilota i la distància són les de l'escenari sense netejar, per a tots dos."""
    nom, triades = tasca
    de_sempre = mp.degradat(nom, AIRE)
    toc = vt.veritat(nom)
    valides = ssp.dins(len(toc), avalua.trams_valids(replace(de_sempre, veritat=toc)))
    vista, distancia = ~np.isnan(de_sempre.tracking.pilota[:, 0]), lda.distancies(de_sempre)
    files = []
    for metode in (A_EQUIPS, A_CREIBLE):
        probes, prior, q_ = de_qui(metode, nom)
        relativa = log_relativa(probes[AIRE].astype(float), prior)
        w, lam, d_min = triades[metode][nom]
        pred = t3i.per_trams(relativa, q_[AIRE].astype(float), de_sempre.trams, w, lam, int(d_min))
        c = lda.comptes(pred, toc, relativa, vista, distancia, valides)
        files += [{"partit": nom, "font": de_sempre.font, "metode": metode, **r} for r in c.to_dict("records")]
    return files


def taula_la_d(t: pd.DataFrame) -> pd.DataFrame:
    """On la veritat és d'un equip: per on es veu la pilota i la distància, quina part d'aquestes imatges hi ha, i a
    quina part la predicció de cada mètode hi dona la D. A sota, a totes."""
    equip = t[t["veritat"] == lda.D_UN_EQUIP]
    g = equip.groupby(["on", "distancia", "metode"])[["n", "d"]].sum()
    n = g["n"].xs(A_CREIBLE, level="metode")
    files = pd.concat([(n / n.sum()).rename("imatges d'un equip"),
                       (g["d"] / g["n"]).unstack("metode")[[A_EQUIPS, A_CREIBLE]].add_prefix("la D · ")], axis=1)
    files = eaf.en_ordre(files, lda.ONS, lda.NOMS)
    totes = equip.groupby("metode")[["n", "d"]].sum()
    files.loc[(TOTES, ""), :] = [1.0, *(totes["d"] / totes["n"])[[A_EQUIPS, A_CREIBLE]]]
    return files.rename_axis(["on", "distància"])


def taula_canvis(canvis_: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i font: les imatges on es veu la pilota, les que canvia la neteja i quina part són."""
    g = canvis_.groupby(["escenari", "font"])[["vistes", "canvien"]].sum()
    g = g.assign(part=g["canvien"] / g["vistes"]).rename(columns={"vistes": "n vistes", "canvien": "n canvien"})
    return eaf.en_ordre(g, ESCENARIS, FONTS)


def _regla(millor: dict[str, bool]) -> list[str]:
    es = all(millor.values())
    return ["| | És el millor fins ara si | |", "|---|---|---|",
            f"| {AIRE} | la diferència és positiva i l'interval del 95 % no toca el zero | "
            f"{mq._marca(millor['escenari'])} |",
            f"| Els altres tres ×¼ i «{mp.PARTIT}» | la diferència no és negativa | {mq._marca(millor['quarts'])} |",
            f"| El net, els ×1 i el soroll2 | no perd (diferència ≥ −{t3.SOROLL}) | {mq._marca(millor['altres'])} |",
            "", f"**{A_CREIBLE} {'és' if es else 'no és'} el millor fins ara:** el pas següent es fa a sobre "
            f"d'{A_CREIBLE if es else A_EQUIPS}.", ""]


def markdown(metodes: pd.DataFrame, triades: dict, c: pd.DataFrame, passa: dict[str, bool], c_equips: pd.DataFrame,
             millor: dict[str, bool], per_font: dict[tuple[str, str], pd.DataFrame], canvis_: pd.DataFrame,
             la_d_: pd.DataFrame) -> str:
    linies = ["# Banc obert · La pilota a 10 m o més fora del camp, com un forat (T3w)", "",
              "Generat amb `uv run python -I -m banc.model_pilota_creible`. Dades obertes: 7 partits de DFL (IDSSE,",
              "CC BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3w», i la capçalera de `banc/model_pilota_creible.py`. Es puntua a la",
              "veritat de toc.", "",
              f"**{XARXES}** i **{A_EQUIPS}** són els de la T3v, amb les peces de la memòria cau (✓ comprovat: a",
              f"cada punt de la graella donen l'spellF1 del banc de la T3v). **{A_CREIBLE}** és {A_EQUIPS}, amb la",
              "pilota vista a 10 m o més fora del camp tractada com si no es veiés. Les peces del partit que es prova",
              "s'han tornat a entrenar (✓ comprovat: on la neteja no canvia res, són exactament les de la memòria",
              "cau).", "",
              "## On canvia l'entrada", "",
              "Les imatges on es veu la pilota, i quantes en canvia la neteja (✓ cap als sis escenaris",
              "d'entrenament).", "", t3p.md(taula_canvis(canvis_)), "",
              f"## {A_CREIBLE} contra {XARXES_TOC} (spellF1): el criteri", "",
              *t3b._taula(c, A_CREIBLE, XARXES_TOC), "", *mt._criteris(passa),
              f"## {A_CREIBLE} contra {A_EQUIPS} (spellF1)", "", *t3i._comparacio(c_equips, A_CREIBLE, A_EQUIPS), ""]
    if not all(passa.values()):
        linies += ["## No passa: és el millor fins ara?", "",
                   "La regla dels passos que només van a un escenari (D-55), escrita abans, contra "
                   f"{A_EQUIPS}:", "", *_regla(millor)]
    for (font, contra), taula in per_font.items():
        linies += [f"## {A_CREIBLE} contra {contra}, només els partits de {font}", "",
                   *t3i._comparacio(taula, A_CREIBLE, contra), ""]
    linies += [f"## La D a {AIRE}, a DFL", "",
               "Als trams vàlids, on la veritat de toc és d'un equip: per on es veu la pilota i a quants metres de la",
               "línia s'ha vist fora del camp (on es veu, la seva; als forats, la més gran de la pilota vista just",
               "abans i just després), quina part d'aquestes imatges hi ha, i a quina part la predicció hi dona la D.",
               "Tot, a l'escenari sense netejar, per als dos mètodes.", "",
               t3p.md(taula_la_d(la_d_[la_d_["font"] == "dfl"])), "",
               "## L'spellF1 de cada mètode (mitjana dels deu partits)", "",
               *mt._mitjanes(metodes, [XARXES_TOC, A_EQUIPS, A_CREIBLE]), "## Els decodificadors triats", "",
               *mq._triades(triades), ""]
    return "\n".join(linies)


def clau() -> str:
    """El que fa les probabilitats d'aquí: les peces d'A equips sencers i d'A xarxes, la neteja i això."""
    h = hashlib.sha256((mae.CLAU + mp.CLAU).encode())
    h.update(Path(pc.__file__).read_bytes())
    for funcio in (per_escenari, creible, primer, q, xarxes_de_la_prova, segon):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet


def clau_dels_resultats() -> str:
    h = hashlib.sha256((CLAU + vt.CLAU + mae.clau_dels_resultats()).encode())
    h.update(Path(lda.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def en_paral_lel(fes: str, tasques: list, processos: int) -> list:
    """`fes` d'aquest mòdul a cada tasca, pel nom del mòdul perquè els processos fills el trobin."""
    from banc import model_pilota_creible as aquest

    with ProcessPoolExecutor(max_workers=processos) as feina:
        return list(feina.map(getattr(aquest, fes), tasques))


def files_de(metodes: tuple[str, ...], processos: int) -> pd.DataFrame:
    tasques = [(nom, e, metodes) for nom, e in itertools.product(fonts.NOMS, ESCENARIS)]
    return pd.DataFrame([f for tros in en_paral_lel("graella", tasques, processos) for f in tros])


def escriu(contingut: dict, md: str) -> None:
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-pilota-creible.json").write_text(json.dumps(contingut, indent=1, default=float,
                                                                        allow_nan=False))
    (DIR_RESULTATS / "model-pilota-creible.md").write_text(md)
    print(md)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    ap.add_argument("--processos-models", type=int, default=3, help="models alhora")
    args = ap.parse_args()
    for nom in fonts.NOMS:
        for metode in (XARXES, A_EQUIPS):
            mae.de_qui(metode, nom)
        for peca in PECES:
            de_la_t3v(peca, nom)
        vt.veritat(nom)
    canvis_ = pd.DataFrame(en_paral_lel("canvis", list(itertools.product(fonts.NOMS, ESCENARIS)), args.processos))
    comprova_l_entrenament(canvis_)
    print("· la neteja no canvia cap imatge dels sis escenaris d'entrenament", flush=True)
    files = files_de((XARXES, A_EQUIPS), args.processos)
    comprova_les_d_abans(files)
    print(f"· {XARXES} i {A_EQUIPS} donen el del banc de la T3v", flush=True)
    entrena_les_peces(args.processos_models, canvis_)
    files = pd.concat([files, files_de((A_CREIBLE,), args.processos)], ignore_index=True)
    de_xarxes, triades_xarxes = mt.tria_sense_mirar(files, XARXES, TOC, XARXES_TOC)
    de_equips, triades_equips = mt.tria_sense_mirar(files, A_EQUIPS, TOC, A_EQUIPS)
    de_creible, triades_creible = mt.tria_sense_mirar(files, A_CREIBLE, TOC, A_CREIBLE)
    triades = {XARXES_TOC: triades_xarxes, A_EQUIPS: triades_equips, A_CREIBLE: triades_creible}
    comprova_les_triades(triades)
    metodes = pd.concat([de_xarxes, de_equips, de_creible], ignore_index=True)
    c = mt.comparacio(metodes, A_CREIBLE, XARXES_TOC, TOC, amb_criteri=True)
    c_equips = mt.comparacio(metodes, A_CREIBLE, A_EQUIPS, TOC, amb_criteri=False)
    passa, millor = mt.compleix(c), millor_d_un_escenari(c_equips, AIRE)
    per_font = {(font, contra): mt.comparacio(metodes[metodes["font"] == font], A_CREIBLE, contra, TOC,
                                              amb_criteri=False)
                for font in FONTS for contra in (XARXES_TOC, A_EQUIPS)}
    la_d_ = pd.DataFrame([f for tros in en_paral_lel("la_d", [(nom, triades) for nom in fonts.NOMS], args.processos)
                          for f in tros])
    contingut = {"clau": clau_dels_resultats(), "passa": passa, "millor_fins_ara": millor,
                 "comparacio": t3.registres(c), "contra_a_equips_sencers": t3.registres(c_equips),
                 "triades": triades, "files": t3.registres(files[files["metode"] == A_CREIBLE]),
                 "per_font": {f"{font} · {contra}": t3.registres(t) for (font, contra), t in per_font.items()},
                 "canvis": t3.registres(canvis_), "la_d": t3.registres(la_d_)}
    escriu(contingut, markdown(metodes, triades, c, passa, c_equips, millor, per_font, canvis_, la_d_))


if __name__ == "__main__":
    main()
