"""On canvia l'equip dins dels forats, a sobre d'A equips sencers, abans de pensar com ajudar-hi a curts ×¼
(`docs/pla-tocs.md`, «On canvia l'equip dins dels forats de curts ×¼»). Només per saber-ho.

    cd codi && uv run python -I -m banc.canvis_als_forats

Amb el que ha desat el banc de la T3v (A equips sencers) i el decodificador triat a cada partit a la veritat de toc (es
comprova que l'spellF1 és el del banc de la T3v). Als quatre ×¼ i a «partit ×¼», a la veritat de toc. Un forat és un
tros sense pilota d'una part. Les imatges dels forats d'`errors_als_forats` (amb `K` imatges més a cada banda) són del
forat més proper.

1. **El tipus de cada forat,** pel que hi fa la veritat de la darrera imatge amb pilota abans del forat a la primera
   després: sense canvi; un canvi d'un equip a l'altre; una possessió de l'altre equip amagada (el mateix equip a cada
   banda i l'altre al mig); o la D o més canvis. De cada tipus, quina part hi ha de les imatges d'un equip dels forats
   i dels errors d'A equips sencers.
2. **Els sostres:** l'equip encertat del segon (`ssp.equip_encertat`) només als forats d'un tipus, i contra A xarxes.
3. **Als forats d'un canvi:** a quin quart del forat cau el canvi de la veritat, què hi fa la predicció (un sol canvi,
   cap o una altra cosa) i, si hi fa un sol canvi, a quant del de la veritat. I a quant en són tres senyals que es
   poden veure: el mig del forat, on la pilota estimada de la T3t passa més a prop d'un jugador de l'equip nou, i on el
   segon passa a l'equip nou.
4. **Als forats sense canvi:** què hi fa la predicció (cap canvi, hi inventa una possessió, hi canvia d'equip, hi
   posa la D o una altra cosa), i quina part dels errors hi ha. I els sostres només als forats on la predicció hi fa
   una cosa: un sol canvi als d'un canvi, el canvi fora del forat als d'un canvi, i un canvi als sense canvi.

Escriu `resultats/canvis-als-forats.md`. Tot són dades obertes.
"""

from __future__ import annotations

import itertools
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from banc import analisi_t3p as t3p
from banc import analisi_t3r as an
from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import errors_als_forats as eaf
from banc import marge_equips as mme
from banc import marge_sense_pilota as msm
from banc import model_a_canvis as t3i
from banc import pilota_als_forats as paf
from banc import sostre_curtes as sc
from banc import sostre_sense_pilota as ssp
from cadena import xarxa_sense_pilota as xsp
from cadena.llegeix import Tracking
from possessio.oficial import possession_metrics as pm

ESCENARIS = eaf.ESCENARIS                           # els quatre ×¼ i «partit ×¼»
QUARTS = eaf.QUARTS
A_EQUIPS, XARXES, BASE = eaf.A_EQUIPS, eaf.XARXES, eaf.BASE
K = t3i.K
H, A, D = pm.H, pm.A, pm.D
SENSE, UN, AMAGADA, ALTRES = "sense canvi", "un canvi d'equip", "una possessió amagada", "la D o més canvis"
TIPUS = (SENSE, UN, AMAGADA, ALTRES)
EQUIP = msm.EQUIP_FORATS
SOSTRES = {SENSE: "… només als forats sense canvi", UN: "… només als d'un canvi d'equip",
           AMAGADA: "… només als d'una possessió amagada", ALTRES: "… només als de la D o més canvis"}
FA_EL_CANVI, EL_D_ABANS, EL_NOU = "hi fa un sol canvi", "es queda amb l'equip d'abans", "ja hi té l'equip nou"
ALTRA_COSA = "hi fa una altra cosa"
FETS = (FA_EL_CANVI, EL_D_ABANS, EL_NOU, ALTRA_COSA)
NO_CANVIA, INVENTA = "cap canvi", "hi inventa una possessió de l'altre equip"
CANVIA, POSA_LA_D = "hi canvia d'equip (o ja hi arriba canviada)", "hi posa la D"
FETS_SENSE = (NO_CANVIA, INVENTA, CANVIA, POSA_LA_D, ALTRA_COSA)
SOSTRES_FETS = {"… només als d'un canvi on la predicció hi fa un sol canvi": (UN, (FA_EL_CANVI,)),
                "… només als d'un canvi on el fa fora del forat": (UN, (EL_D_ABANS, EL_NOU)),
                "… només als sense canvi on hi canvia d'equip": (SENSE, (CANVIA,))}
QUARTS_DEL_FORAT = ("al primer quart", "al segon", "al tercer", "al darrer")
DURADES = tuple(nom for _, _, nom in paf.FORATS)
PREDICCIO, MIG = "la predicció", "el mig del forat"
PILOTA = "on la pilota estimada passa més a prop de l'equip nou"
SEGON = "on el segon passa a l'equip nou"
SENYALS = (PREDICCIO, MIG, PILOTA, SEGON)
TOTS, AMB_UN = "a tots", "on la predicció hi fa un sol canvi"


def forats(vista: np.ndarray, parts: tuple[tuple[int, int, int], ...]) -> list[tuple[int, int, int, int]]:
    """Els trossos sense pilota de cada part: (primera, última, inici de la part, última de la part), incloses."""
    out = []
    for _, inici, ultim in parts:
        vores = np.diff(np.r_[0, (~vista[inici:ultim + 1]).astype(np.int8), 0])
        out += [(inici + int(a), inici + int(b) - 1, inici, ultim)
                for a, b in zip(np.flatnonzero(vores == 1), np.flatnonzero(vores == -1))]
    return out


def de_quin_forat(n: int, forats_: list[tuple[int, int, int, int]], al_forat: np.ndarray) -> np.ndarray:
    """A cada imatge d'`al_forat`, l'índex del forat més proper de la seva part (a la mateixa distància, el d'abans);
    −1 a la resta."""
    qui, lluny = np.full(n, -1), np.full(n, np.inf)
    for i, (a, b, inici, ultim) in enumerate(forats_):
        j = np.arange(max(a - K, inici), min(b + K, ultim) + 1)
        d = np.maximum(a - j, j - b).clip(min=0)
        millor = d < lluny[j]
        qui[j[millor]], lluny[j[millor]] = i, d[millor]
    return np.where(al_forat, qui, -1)


def seguits(x: np.ndarray) -> list[int]:
    """Els valors, sense repetir els seguits."""
    return x[np.r_[True, x[1:] != x[:-1]]].tolist() if len(x) else []


def tipus(tros: np.ndarray) -> str:
    """El tipus d'un forat per la veritat del tros (de la darrera imatge amb pilota abans a la primera després), sense
    les imatges que no es puntuen; "" si no n'hi queda cap."""
    v = tros[np.isin(tros, (H, A, D))]
    if not len(v):
        return ""
    if (v == D).any():
        return ALTRES
    return {1: SENSE, 2: UN, 3: AMAGADA}.get(len(seguits(v)), ALTRES)


def que_fa(tros: np.ndarray, vell: int, nou: int) -> tuple[str, int]:
    """Què fa la predicció en un forat d'un canvi de `vell` a `nou`, i si hi fa un sol canvi, on (dins del tros)."""
    s = seguits(tros)
    if s == [vell, nou]:
        return FA_EL_CANVI, int(np.argmax(tros == nou))
    return {(vell,): EL_D_ABANS, (nou,): EL_NOU}.get(tuple(s), ALTRA_COSA), -1


def que_fa_sense(tros: np.ndarray, equip: int) -> str:
    """Què fa la predicció en un forat sense canvi de l'`equip`."""
    s = seguits(tros)
    if s == [equip]:
        return NO_CANVIA
    if D in s:
        return POSA_LA_D
    if s == [equip, 1 - equip, equip]:
        return INVENTA
    return CANVIA if len(s) <= 2 else ALTRA_COSA


def errors_del_tros(toc: np.ndarray, pred: np.ndarray) -> int:
    """Les imatges d'un equip a la veritat on la predicció no les encerta."""
    return int(((pred != toc) & np.isin(toc, ssp.EQUIPS)).sum())


def on_canvia_el_segon(relativa: np.ndarray, vell: int, nou: int) -> int:
    """La primera imatge del tros on el segon dona més a `nou` que a `vell`; si no n'hi ha cap, la mida del tros."""
    passa = np.nan_to_num(relativa[:, nou], nan=-np.inf) > np.nan_to_num(relativa[:, vell], nan=-np.inf)
    return int(np.argmax(passa)) if passa.any() else len(relativa)


def mes_proper(jugadors: np.ndarray, pilota: np.ndarray) -> np.ndarray:
    """(n,) La distància del jugador més proper a la pilota; inf si no es veu la pilota o cap jugador."""
    d = np.hypot(*(jugadors - pilota[:, None, :]).transpose(2, 0, 1))
    return np.where(np.isnan(d), np.inf, d).min(axis=1)


def distancies(t: Tracking, parts: tuple[tuple[int, int, int], ...]) -> tuple[np.ndarray, np.ndarray]:
    """En metres, del jugador més proper de l'H i de l'A a la pilota estimada de la T3t (`xsp.estimada`), part per
    part."""
    camp = np.asarray(t.camp_m, float)
    d_h, d_a = np.full(len(t.pilota), np.inf), np.full(len(t.pilota), np.inf)
    for _, inici, ultim in parts:
        s = slice(inici, ultim + 1)
        pilota = xsp.estimada(t.pilota[s]) * camp
        d_h[s], d_a[s] = mes_proper(t.casa[s] * camp, pilota), mes_proper(t.fora[s] * camp, pilota)
    return d_h, d_a


def quart(t: int, a: int, b: int) -> str:
    """A quin quart del forat [a, b] és la imatge `t` (la primera imatge amb pilota després, al darrer)."""
    return QUARTS_DEL_FORAT[min(int(4 * (t - a) / (b - a + 1)), 3)]


def temps(errors: np.ndarray) -> dict:
    """Dels errors en segons (sense els NaN): quina part és a 0,5 s o menys i a 1 s o menys, la mediana, quina part és
    abans de la veritat i quants."""
    e = errors[np.isfinite(errors)]
    return {"a 0,5 s o menys": float((np.abs(e) <= 0.5).mean()), "a 1 s o menys": float((np.abs(e) <= 1.0).mean()),
            "mediana (s)": float(np.median(np.abs(e))), "abans": float((e < 0).mean()), "n forats": len(e)}


def un_canvi(forat: tuple[int, int, int, int], toc: np.ndarray, pred: np.ndarray, relativa: np.ndarray,
             d_h: np.ndarray, d_a: np.ndarray) -> dict:
    """Un forat d'un canvi: quant dura, a quin quart cau el canvi de la veritat, què hi fa la predicció, i a quants
    segons del canvi de la veritat són la predicció (si hi fa un sol canvi) i els senyals."""
    a, b, inici, ultim = forat
    lo, hi = max(a - 1, inici), min(b + 1, ultim)
    tros = toc[lo:hi + 1]
    vell = int(tros[np.isin(tros, ssp.EQUIPS)][0])
    nou = A if vell == H else H
    t_veritat = lo + int(np.argmax(tros == nou))
    fa, on = que_fa(pred[lo:hi + 1], vell, nou)
    d_nou = (d_h if nou == H else d_a)[a:b + 1]
    on_es = {PREDICCIO: lo + on if fa == FA_EL_CANVI else np.nan, MIG: (a + b + 1) / 2,
             PILOTA: a + int(np.argmin(d_nou)) if np.isfinite(d_nou).any() else np.nan,
             SEGON: a + on_canvia_el_segon(relativa[a:hi + 1], vell, nou)}
    return {"durada": paf.a_quin(paf.FORATS, np.array([b - a + 1]))[0], "quart": quart(t_veritat, a, b), "fa": fa,
            "errors": errors_del_tros(tros, pred[lo:hi + 1]), **{s: (t - t_veritat) / pm.FPS for s, t in on_es.items()}}


def sense_canvi(forat: tuple[int, int, int, int], toc: np.ndarray, pred: np.ndarray) -> dict:
    """Un forat sense canvi: quant dura, què hi fa la predicció i quantes imatges no encerta."""
    a, b, inici, ultim = forat
    lo, hi = max(a - 1, inici), min(b + 1, ultim)
    tros = toc[lo:hi + 1]
    equip = int(tros[np.isin(tros, ssp.EQUIPS)][0])
    return {"durada": paf.a_quin(paf.FORATS, np.array([b - a + 1]))[0], "fa": que_fa_sense(pred[lo:hi + 1], equip),
            "errors": errors_del_tros(tros, pred[lo:hi + 1])}


def tasca(nom_escenari: tuple[str, str]) -> dict[str, list[dict]]:
    """Un partit i un escenari: l'spellF1 d'A equips sencers i dels sostres, les imatges per tipus de forat i els forats
    d'un canvi."""
    nom, escenari = nom_escenari
    pr = eaf.prediccio(nom, escenari, A_EQUIPS)
    toc, vista, relativa, decodifica = pr.toc, pr.vista, pr.relativa, pr.decodifica
    pred = decodifica(relativa)
    al_forat = ssp.dins(len(toc), pr.trams) & sc.forats(vista)
    forats_ = forats(vista, pr.de_sempre.trams)
    del_forat = np.array([tipus(toc[max(a - 1, i0):min(b + 1, i1) + 1]) for a, b, i0, i1 in forats_] + [""],
                         dtype=object)
    qui = de_quin_forat(len(toc), forats_, al_forat)
    de_tipus = del_forat[qui]                                                 # −1 és l'últim: ""
    equip = np.isin(toc, ssp.EQUIPS) & al_forat
    comu = {"partit": nom, "font": pr.de_sempre.font, "escenari": escenari, "base": A_EQUIPS}

    def fila(sostre: str, prediccio: np.ndarray) -> dict:
        return {**comu, "sostre": sostre, "spell_f1": avalua.puntua(pr.p_toc, prediccio)["spell_f1"]}

    d_h, d_a = distancies(pr.de_sempre.tracking, pr.de_sempre.trams)
    canvis, sense, fet = [], [], np.full(len(forats_) + 1, "", dtype=object)
    for i, (f, t) in enumerate(zip(forats_, del_forat)):
        if t == UN:
            canvis.append(un_canvi(f, toc, pred, relativa, d_h, d_a))
            fet[i] = canvis[-1]["fa"]
        elif t == SENSE:
            sense.append(sense_canvi(f, toc, pred))
            fet[i] = sense[-1]["fa"]
    de_fet = fet[qui]
    files = [fila(BASE, pred), fila(EQUIP, decodifica(ssp.equip_encertat(relativa, toc, al_forat)))]
    files += [fila(s, decodifica(ssp.equip_encertat(relativa, toc, al_forat & (de_tipus == t))))
              for t, s in SOSTRES.items()]
    files += [fila(s, decodifica(ssp.equip_encertat(relativa, toc, al_forat & (de_tipus == t) & np.isin(de_fet, fs))))
              for s, (t, fs) in SOSTRES_FETS.items()]
    imatges = (pd.DataFrame({"tipus": de_tipus[equip], "mal": pred[equip] != toc[equip], "d": pred[equip] == D})
               .groupby("tipus").agg(n=("mal", "size"), errors=("mal", "sum"), d=("d", "sum")).reset_index())
    return {"files": files, "imatges": [{**comu, **r} for r in imatges.to_dict("records")],
            "canvis": [{**comu, **c} for c in canvis], "sense": [{**comu, **c} for c in sense]}


def taula_tipus(imatges: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i tipus: quina part de les imatges d'un equip dels forats i dels errors hi ha, on s'equivoca i
    quina part dels errors són la D."""
    g = imatges[imatges["tipus"] != ""].groupby(["escenari", "tipus"])[["n", "errors", "d"]].sum()
    totals = g.groupby("escenari").sum()
    t = pd.DataFrame({"imatges": g["n"] / totals["n"].reindex(g.index, level="escenari"),
                      "errors": g["errors"] / totals["errors"].reindex(g.index, level="escenari"),
                      "s'equivoca": g["errors"] / g["n"], "dels errors, la D": g["d"] / g["errors"]})
    return eaf.en_ordre(t, ESCENARIS, TIPUS)


def taula_guanys(files: pd.DataFrame) -> list[str]:
    """Per sostre i escenari: quant guanya a A equips sencers (mitjana dels partits)."""
    t = files.groupby(["escenari", "sostre"])["spell_f1"].mean().unstack("sostre")
    sostres = (EQUIP, *SOSTRES.values(), *SOSTRES_FETS)
    return ["| | " + " | ".join(ESCENARIS) + " |", "|---" * (1 + len(ESCENARIS)) + "|",
            f"| spellF1 d'{A_EQUIPS} | " + " | ".join(f"{t.loc[e, BASE]:.3f}" for e in ESCENARIS) + " |",
            *(f"| {s} | " + " | ".join(f"{t.loc[e, s] - t.loc[e, BASE]:+.3f}" for e in ESCENARIS) + " |"
              for s in sostres)]


def taula_criteri(files: pd.DataFrame, xarxes: pd.Series) -> list[str]:
    """Per sostre i escenari ×¼: A equips sencers amb la peça encertada contra A xarxes, i si passaria el criteri."""
    font = files.groupby("partit")["font"].first()
    linies = [f"| {A_EQUIPS} amb… | " + " | ".join(QUARTS) + " |", "|---" * (1 + len(QUARTS)) + "|"]
    for sostre in (BASE, EQUIP, *SOSTRES.values(), *SOSTRES_FETS):
        seves = files[files["sostre"] == sostre].set_index(["escenari", "partit"])["spell_f1"]
        celles = []
        for escenari in QUARTS:
            dif = (seves - xarxes).loc[escenari]
            c = sc.criteri(dif.to_numpy(), font.loc[dif.index].to_numpy())
            celles.append(f"{c['guany']:+.3f} · {c['guanya']}/{c['partits']} {'✓' if c['passa'] else '✗'}")
        linies.append(f"| {'res més' if sostre == BASE else sostre} | " + " | ".join(celles) + " |")
    return linies


def parts_de(canvis: pd.DataFrame, columna: str, ordre: tuple[str, ...]) -> pd.DataFrame:
    """Per escenari i durada del forat (i a tots): quants forats d'un canvi hi ha, i quina part per `columna`."""
    junts = pd.concat([canvis, canvis.assign(durada=TOTS)], ignore_index=True)
    n = junts.groupby(["escenari", "durada"]).size().rename("n forats")
    t = pd.crosstab([junts["escenari"], junts["durada"]], junts[columna], normalize="index")
    t = pd.concat([n, t.reindex(columns=list(ordre), fill_value=0.0)], axis=1)
    return eaf.en_ordre(t, ESCENARIS, (*DURADES, TOTS))


def forats_i_errors(forats_: pd.DataFrame, ordre: tuple[str, ...]) -> pd.DataFrame:
    """Per escenari i pel que hi fa la predicció: quina part dels forats i dels seus errors hi ha."""
    g = forats_.groupby(["escenari", "fa"])["errors"].agg(n="size", errors="sum")
    totals = g.groupby("escenari").sum()
    t = pd.DataFrame({"forats": g["n"] / totals["n"].reindex(g.index, level="escenari"),
                      "errors": g["errors"] / totals["errors"].reindex(g.index, level="escenari"),
                      "errors per forat": g["errors"] / g["n"]})
    return eaf.en_ordre(t, ESCENARIS, ordre)


def taula_temps(canvis: pd.DataFrame) -> pd.DataFrame:
    """Per escenari, forats i senyal: a quants segons del canvi de la veritat és (la predicció, només on hi fa un sol
    canvi)."""
    files = []
    for escenari, c in canvis.groupby("escenari"):
        for quins, c_ in ((AMB_UN, c[c["fa"] == FA_EL_CANVI]), (TOTS, c)):
            for senyal in SENYALS:
                if senyal == PREDICCIO and quins == TOTS:
                    continue
                files.append({"escenari": escenari, "forats": quins, "senyal": senyal,
                              **temps(c_[senyal].to_numpy(float))})
    t = pd.DataFrame(files).set_index(["escenari", "forats", "senyal"])
    return eaf.en_ordre(t, ESCENARIS, (AMB_UN, TOTS), SENYALS)


def main() -> None:
    from banc import canvis_als_forats as aquest        # pel nom del mòdul, perquè els processos fills el trobin

    with ProcessPoolExecutor(max_workers=10) as feina:
        tasques = list(feina.map(aquest.tasca, itertools.product(fonts.NOMS, ESCENARIS)))
    files, imatges, canvis, sense = (pd.DataFrame([f for t in tasques for f in t[k]])
                                     for k in ("files", "imatges", "canvis", "sense"))
    mme.comprova(files, bases=(A_EQUIPS,), escenaris=ESCENARIS)
    sortida = [
        "# Banc obert · On canvia l'equip dins dels forats", "",
        "Generat amb `uv run python -I -m banc.canvis_als_forats`, amb el que ha desat `banc.model_a_equips`. Dades",
        f"obertes. Només per saber-ho. {A_EQUIPS}, a la veritat de toc, amb el decodificador triat a cada partit a la",
        "veritat de toc (✓ comprovat: el mateix spellF1 que el banc de la T3v). Un forat és un tros sense pilota d'una",
        f"part; les imatges dels forats (amb {K} imatges més a cada banda) són del més proper.", "",
        "## El tipus de cada forat", "",
        "Pel que hi fa la veritat de la darrera imatge amb pilota abans del forat a la primera després: *sense canvi*;",
        "*un canvi d'equip* d'un a l'altre; *una possessió amagada* (el mateix equip a cada banda i l'altre al mig); o",
        "*la D o més canvis*. On la veritat és d'un equip: quina part de les imatges dels forats i dels errors hi ha, i",
        f"on s'equivoca {A_EQUIPS} (hi dona l'altre equip o la D), i quina part d'aquests errors són la D.", "",
        t3p.md(taula_tipus(imatges)), "",
        "## Els sostres", "",
        f"Quant guanya a {A_EQUIPS} (mitjana dels deu partits) el segon amb l'equip encertat als forats (l'H i l'A",
        "girats on s'equivoca, amb la confiança que tenia), a tots o només als d'un tipus. Els tres últims, només als",
        "forats d'un tipus on la predicció hi fa una cosa (vegeu més avall).", "",
        *taula_guanys(files), "",
        f"Contra {XARXES}: el guany de mitjana · en quants partits guanya · ✓ si passaria (> {t3.SOROLL},",
        f"l'interval del 95 % per sobre de zero i {t3.GUANYA_MINIM} partits de 10 o més).", "",
        *taula_criteri(files, eaf.de_xarxes()), "",
        "## Els forats d'un canvi d'equip", "",
        "A quin quart del forat cau el canvi de la veritat (la primera imatge de l'equip nou; si és la primera amb",
        "pilota després del forat, al darrer), per quant dura el forat:", "",
        t3p.md(parts_de(canvis, "quart", QUARTS_DEL_FORAT)), "",
        "Què hi fa la predicció, de la darrera imatge amb pilota abans del forat a la primera després: un sol canvi",
        "de l'equip d'abans al nou; cap, amb l'equip d'abans o ja amb el nou; o una altra cosa (la D o més canvis):", "",
        t3p.md(parts_de(canvis, "fa", FETS)), "",
        "I quina part dels errors d'aquests forats hi ha (on la veritat és d'un equip, de la darrera imatge amb pilota",
        "abans del forat a la primera després):", "",
        t3p.md(forats_i_errors(canvis, FETS)), "",
        "A quants segons del canvi de la veritat són: la predicció, on hi fa un sol canvi; el mig del forat; on la",
        "pilota estimada de la T3t (en línia recta) passa més a prop d'un jugador de l'equip nou; i on el segon passa a",
        "donar més a l'equip nou que al d'abans. *Abans* és la part que cau abans del canvi de la veritat. Als forats on la",
        "predicció hi fa un sol canvi, i a tots:", "",
        t3p.md(taula_temps(canvis)), "",
        "## Els forats sense canvi", "",
        "Què hi fa la predicció, de la darrera imatge amb pilota abans del forat a la primera després: cap canvi;",
        "hi inventa una possessió de l'altre equip (hi va i en torna); hi canvia d'equip, o ja hi arriba canviada, i no",
        "en torna; hi posa la D; o una altra cosa. Quina part dels forats i dels seus errors hi ha:", "",
        t3p.md(forats_i_errors(sense, FETS_SENSE)), "",
        "Per quant dura el forat:", "",
        t3p.md(parts_de(sense, "fa", FETS_SENSE)), "",
    ]
    an.DIR_RESULTATS.mkdir(exist_ok=True)
    (an.DIR_RESULTATS / "canvis-als-forats.md").write_text("\n".join(sortida))
    print("\n".join(sortida))


if __name__ == "__main__":
    main()
