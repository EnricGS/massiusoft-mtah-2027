"""Com són els errors d'equip als forats, a sobre d'A equips sencers, abans de triar la idea següent
(`docs/pla-tocs.md`, «Com són els errors d'equip als forats»). Només per saber-ho.

    cd codi && uv run python -I -m banc.errors_als_forats

Amb el que han desat els bancs de la T3t i la T3v (les probabilitats d'A sense pilota i d'A equips sencers, i la q
d'A xarxes) i el decodificador de cada base triat a cada partit a la veritat de toc (es comprova que l'spellF1 de
cada partit és el del banc de la T3v). Als quatre ×¼ i a «partit ×¼», a la veritat de toc, als forats (els trossos
sense pilota, amb `t3i.K` imatges més a cada banda, com a `marge_equips`) on la veritat és d'un equip:

1. **Els errors de cada base,** les imatges on la predicció no hi dona aquest equip: si hi dona l'altre o la D, i on
   el segon (l'equip més probable, sense la D) ja s'equivoca. Segons on és la imatge (a la vora del forat, amb la
   pilota a la vista, o dins d'un forat de menys de 2 s, de 2 a 5 s o de més) i si la possessió de la veritat es veu
   algun cop amb pilota (com a `pilota_als_forats`).
2. **Dels errors d'A equips sencers:** on cauen dins la possessió (tota, al començament, al final o al mig, com a
   `errors_amb_pilota`), si el toc més proper (el començament o el final de la possessió de la veritat) es veu o és
   sense pilota, a quina distància és, quant dura la possessió, i què en diu el segon: l'encerta, hi dona la D, hi
   dubta o n'està segur.
3. **Els sostres,** a sobre d'A equips sencers: l'equip encertat del segon només en una part dels forats, la D
   perfecta als forats, i on el segon ja encerta l'equip i la predicció no, el segon perfecte. Amb el criteri contra
   A xarxes, als ×¼.

Escriu `resultats/errors-als-forats.md`. Tot són dades obertes.
"""

from __future__ import annotations

import itertools
import json
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

from banc import analisi_t3p as t3p
from banc import analisi_t3q as t3q
from banc import analisi_t3r as an
from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import errors_amb_pilota as eap
from banc import marge_equips as mme
from banc import model_a_canvis as t3i
from banc import model_a_equips as mae
from banc import model_a_partit as mp
from banc import pilota_als_forats as paf
from banc import sostre_curtes as sc
from banc import sostre_sense_pilota as ssp
from banc import veritat_toc as vt
from banc.partit import PartitBanc
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

QUARTS = t3.QUARTS
ESCENARIS = (*QUARTS, mp.PARTIT)
XARXES, A_SENSE, A_EQUIPS = mme.XARXES, mme.A_SENSE, mme.A_EQUIPS
BASES = (A_SENSE, A_EQUIPS)
BASE = mme.BASE
BE = "l'equip bo"
L_ALTRE, LA_D = eap.L_ALTRE, eap.LA_D
DONA = (L_ALTRE, LA_D)
VORA = "a la vora (es veu la pilota)"
FORATS = (VORA, *(f"forat {nom}" for _, _, nom in paf.FORATS))
ES_VEU = (paf.MAI, paf.ALGUN_COP)
TOC_VIST, TOC_SENSE = "es veu", "sense pilota"
TOCS = (TOC_VIST, TOC_SENSE)
DONA_D = "el segon hi dona la D"
SEGONS = (eap.ENCERTA, DONA_D, eap.DUBTA, eap.SEGUR)
TRETS = ("dona", "es veu", "forat", "lloc", "toc", "distancia", "durada", "segon")
EQUIP = mme.msm.EQUIP_FORATS
A_LA_VORA = "… només a la vora"
CURTS = "… només als forats de menys de 2 s"
MITJANS = "… només als de 2 a 5 s"
LLARGS = "… només als de 5 s o més"
SI_DUBTA = "… només on el segon dubta"
SI_SEGUR = "… només on el segon n'està segur"
D_FORATS = "als forats, la D perfecta"
DECODIFICADOR = "als forats, on el segon encerta l'equip i la predicció no, el segon perfecte"
SOSTRES = (EQUIP, A_LA_VORA, CURTS, MITJANS, LLARGS, SI_DUBTA, SI_SEGUR, D_FORATS, DECODIFICADOR)
PER_FORAT = dict(zip(FORATS, (A_LA_VORA, CURTS, MITJANS, LLARGS)))


def on_del_forat(vista: np.ndarray) -> np.ndarray:
    """A cada imatge dels forats, on és: a la vora (es veu la pilota) o dins d'un forat, segons quant dura; "" fora."""
    out = np.full(len(vista), "", dtype=object)
    out[sc.forats(vista) & vista] = VORA
    sense = ~vista
    out[sense] = [f"forat {nom}" for nom in paf.a_quin(paf.FORATS, paf.durada_dels_forats(vista)[sense])]
    return out


def toc_proper(toc: np.ndarray, trams: list[ssp.Tram], vista: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """A cada imatge d'una possessió de la veritat, el toc més proper (el començament o el final de la possessió, la
    primera imatge de la següent): si es veu la pilota, i a quantes imatges és."""
    inici, final, _ = eap.possessions(toc, trams)
    i = np.arange(len(toc))
    al_inici, al_final = i - inici, final - i
    on = np.clip(np.where(al_inici <= al_final, inici, final), 0, len(toc) - 1)
    return np.where(vista[on], TOC_VIST, TOC_SENSE), np.minimum(al_inici, al_final)


def segon(relativa: np.ndarray, toc: np.ndarray) -> np.ndarray:
    """Com `errors_amb_pilota.segon`, i on la D hi és la més alta de les tres, que el segon hi dona la D."""
    out = eap.segon(relativa, toc)
    d = np.isin(toc, ssp.EQUIPS) & (np.argmax(np.nan_to_num(relativa, nan=-np.inf), axis=1) == pm.D)
    out[d] = DONA_D
    return out


def d_perfecta(relativa: np.ndarray, toc: np.ndarray, on: np.ndarray) -> np.ndarray:
    """La relativa amb la D perfecta (`sostre_curtes.amb_la_d`) només a les imatges d'`on`."""
    out = relativa.copy()
    out[on] = sc.amb_la_d(relativa, toc)[on]
    return out


def trets(pred: np.ndarray, toc: np.ndarray, relativa: np.ndarray, vista: np.ndarray, al_forat: np.ndarray,
          trams: list[ssp.Tram]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Als forats on la veritat és d'un equip: totes les imatges, comptades per on són, si la possessió es veu, què
    hi dona la predicció i què en diu el segon; i les imatges on la predicció s'equivoca, amb tots els seus trets."""
    inici, final, _ = eap.possessions(toc, trams)
    es_veu, _ = paf.possessions(toc, trams, vista)
    on, diu = on_del_forat(vista), segon(relativa, toc)
    i = np.flatnonzero(al_forat & (inici >= 0))
    altre = np.where(toc[i] == pm.H, pm.A, pm.H)
    dona = np.where(pred[i] == toc[i], BE, np.where(pred[i] == altre, L_ALTRE, np.where(pred[i] == pm.D, LA_D,
                                                                                         eap.RES)))
    totes = pd.DataFrame({"forat": on[i], "es veu": es_veu[i], "dona": dona, "segon": diu[i]})
    mal = dona != BE
    j = i[mal]
    vist, lluny = toc_proper(toc, trams, vista)
    errors = pd.DataFrame({
        "dona": dona[mal], "es veu": es_veu[j], "forat": on[j], "lloc": eap.llocs(pred, toc, trams)[j],
        "toc": vist[j], "distancia": eap.a_quina(eap.LIMITS_DISTANCIA, eap.DISTANCIES, lluny[j]),
        "durada": eap.a_quina(t3q.LIMITS, eap.DURADES, (final - inici)[j]), "segon": diu[j]})
    return (totes.groupby(list(totes.columns)).size().rename("n").reset_index(),
            errors.groupby(list(TRETS)).size().rename("n").reset_index())


def mascares(on: np.ndarray, diu: np.ndarray, al_forat: np.ndarray) -> dict[str, np.ndarray]:
    """On s'encerta l'equip a cada sostre (el segon només hi canvia on s'equivoca)."""
    return {EQUIP: al_forat, **{s: al_forat & (on == f) for f, s in PER_FORAT.items()},
            SI_DUBTA: al_forat & (diu == eap.DUBTA), SI_SEGUR: al_forat & (diu == eap.SEGUR)}


@dataclass(frozen=True)
class Prediccio:
    """El que cal per mirar una base en un partit i un escenari, a la veritat de toc."""
    de_sempre: PartitBanc
    p_toc: PartitBanc
    toc: np.ndarray
    trams: list[ssp.Tram]
    vista: np.ndarray
    relativa: np.ndarray
    decodifica: Callable[[np.ndarray], np.ndarray]


def prediccio(nom: str, escenari: str, base: str) -> Prediccio:
    """Les probabilitats de la base i el seu decodificador, triat al partit a la veritat de toc."""
    de_sempre = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    p_toc = replace(de_sempre, veritat=toc)
    probes, prior, q_ = mae.de_qui(mme.METODE[base], nom)
    q = q_[escenari].astype(float)
    w, lam, d_min = mme.triades()[base][nom]

    def decodifica(relativa_: np.ndarray) -> np.ndarray:
        return t3i.per_trams(relativa_, q, de_sempre.trams, w, lam, int(d_min))

    return Prediccio(de_sempre, p_toc, toc, avalua.trams_valids(p_toc), ~np.isnan(de_sempre.tracking.pilota[:, 0]),
                     log_relativa(probes[escenari].astype(float), prior), decodifica)


def tasca(qui: tuple[str, str, str]) -> dict[str, list[dict]]:
    """Un partit, un escenari i una base: l'spellF1 de la base (i, a A equips sencers, dels sostres) i els errors
    dels forats."""
    nom, escenari, base = qui
    pr = prediccio(nom, escenari, base)
    de_sempre, p_toc, toc, trams, vista, relativa, decodifica = (pr.de_sempre, pr.p_toc, pr.toc, pr.trams, pr.vista,
                                                                 pr.relativa, pr.decodifica)
    al_forat = ssp.dins(len(toc), trams) & sc.forats(vista)
    pred = decodifica(relativa)
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari, "base": base}

    def fila(sostre: str, prediccio: np.ndarray) -> dict:
        return {**comu, "sostre": sostre, "spell_f1": avalua.puntua(p_toc, prediccio)["spell_f1"]}

    files = [fila(BASE, pred)]
    if base == A_EQUIPS:
        diu = segon(relativa, toc)
        files += [fila(s, decodifica(ssp.equip_encertat(relativa, toc, m)))
                  for s, m in mascares(on_del_forat(vista), diu, al_forat).items()]
        decodificador = al_forat & (diu == eap.ENCERTA) & (pred != toc)
        files += [fila(D_FORATS, decodifica(d_perfecta(relativa, toc, al_forat))),
                  fila(DECODIFICADOR, decodifica(ssp.perfecte(relativa, toc, decodificador)))]
    totes, errors = trets(pred, toc, relativa, vista, al_forat, trams)
    return {"files": files, "imatges": [{**comu, **r} for r in totes.to_dict("records")],
            "errors": [{**comu, **r} for r in errors.to_dict("records")]}


def de_xarxes() -> pd.Series:
    """L'spellF1 d'A xarxes a cada escenari i partit, amb el decodificador triat a la veritat de toc (del banc de la
    T3v)."""
    banc = pd.DataFrame(json.loads((mae.DIR_RESULTATS / "model-a-equips.json").read_text())["files"])
    triats = [banc[(banc["metode"] == mae.XARXES) & (banc["veritat"] == mae.TOC) & (banc["partit"] == nom)
                   & (banc["w"] == w) & (banc["lam"] == lam) & (banc["d_min"] == d_min)]
              for nom, (w, lam, d_min) in mme.triades()[XARXES].items()]
    return pd.concat(triats).set_index(["escenari", "partit"])["spell_f1"]


def en_ordre(t: pd.DataFrame | pd.Series, *nivells: tuple[str, ...]) -> pd.DataFrame | pd.Series:
    """L'índex en l'ordre dels `nivells` (els que hi són)."""
    if len(nivells) == 1:
        return t.reindex([x for x in nivells[0] if x in t.index])
    return t.reindex([x for x in itertools.product(*nivells) if x in t.index])


def taula_bases(imatges: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i base: on la predicció s'equivoca (l'altre equip o la D) i on el segon ja s'hi equivoca."""
    n = imatges.groupby(["escenari", "base"])["n"].sum()

    def part(m: pd.Series) -> pd.Series:
        return imatges[m].groupby(["escenari", "base"])["n"].sum().reindex(n.index, fill_value=0) / n

    t = pd.DataFrame({"errors": part(imatges["dona"] != BE), L_ALTRE: part(imatges["dona"] == L_ALTRE),
                      LA_D: part(imatges["dona"] == LA_D), "el segon s'equivoca": part(imatges["segon"] != eap.ENCERTA)})
    return en_ordre(t.unstack("base").reindex(columns=[(c, b) for c in t.columns for b in BASES]), ESCENARIS)


def taula_d_per_font(imatges: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i font: la part de les imatges on la predicció de cada base hi dona la D."""
    claus = ["escenari", "font", "base"]
    n = imatges.groupby(claus)["n"].sum()
    d = imatges[imatges["dona"] == LA_D].groupby(claus)["n"].sum().reindex(n.index, fill_value=0)
    t = (d / n).unstack("base")[list(BASES)]
    return en_ordre(t.rename(columns=lambda b: f"la D · {b}"), ESCENARIS, tuple(sorted(imatges["font"].unique())))


def taula_on(imatges: pd.DataFrame, tret: str, ordre: tuple[str, ...]) -> pd.DataFrame:
    """Per escenari i valor del `tret`: quina part de les imatges dels forats hi ha, on s'equivoca la predicció de cada
    base, i quina part dels errors d'A equips sencers hi és."""
    claus = ["escenari", tret]
    equips = imatges[imatges["base"] == A_EQUIPS]
    n = equips.groupby(claus)["n"].sum()
    t = pd.DataFrame({"imatges": n / n.groupby("escenari").transform("sum")})
    for base in BASES:
        de_la_base = imatges[imatges["base"] == base]
        mal = de_la_base[de_la_base["dona"] != BE].groupby(claus)["n"].sum().reindex(n.index, fill_value=0)
        t[f"errors · {base}"] = mal / de_la_base.groupby(claus)["n"].sum()
    mal = equips[equips["dona"] != BE].groupby(claus)["n"].sum().reindex(n.index, fill_value=0)
    t[f"la D · {A_EQUIPS}"] = equips[equips["dona"] == LA_D].groupby(claus)["n"].sum().reindex(n.index,
                                                                                             fill_value=0) / n
    t[f"part dels errors · {A_EQUIPS}"] = mal / mal.groupby("escenari").transform("sum")
    return en_ordre(t, ESCENARIS, ordre)


def parts(errors: pd.DataFrame, tret: str, ordre: tuple[str, ...]) -> pd.DataFrame:
    """Per escenari: dels errors d'A equips sencers als forats, quina part és de cada valor del `tret`."""
    e = errors[errors["base"] == A_EQUIPS]
    t = e.groupby(["escenari", tret])["n"].sum().unstack(tret, fill_value=0).reindex(columns=list(ordre), fill_value=0)
    return en_ordre(t.div(t.sum(axis=1), axis=0), ESCENARIS)


def creuada(errors: pd.DataFrame, escenari: str, files: tuple[str, tuple[str, ...]],
            columnes: tuple[str, tuple[str, ...]]) -> pd.DataFrame:
    """A l'`escenari`: dels errors d'A equips sencers als forats, quina part és de cada parell."""
    e = errors[(errors["base"] == A_EQUIPS) & (errors["escenari"] == escenari)]
    t = e.groupby([files[0], columnes[0]])["n"].sum().unstack(columnes[0], fill_value=0)
    t = t.reindex(index=list(files[1]), columns=list(columnes[1]), fill_value=0)
    return (t / t.to_numpy().sum()).rename_axis(index=files[0])


def taula_guanys(files: pd.DataFrame) -> list[str]:
    """Per sostre (files) i escenari (columnes): quant guanya a A equips sencers (mitjana dels partits)."""
    t = files[files["base"] == A_EQUIPS].groupby(["escenari", "sostre"])["spell_f1"].mean().unstack("sostre")
    g = t[list(SOSTRES)].sub(t[BASE], axis=0)
    return ["| | " + " | ".join(ESCENARIS) + " |", "|---" * (1 + len(ESCENARIS)) + "|",
            f"| spellF1 d'{A_EQUIPS} | " + " | ".join(f"{t.loc[e, BASE]:.3f}" for e in ESCENARIS) + " |",
            *(f"| {s} | " + " | ".join(f"{g.loc[e, s]:+.3f}" for e in ESCENARIS) + " |" for s in SOSTRES)]


def taula_criteri(files: pd.DataFrame, xarxes: pd.Series) -> list[str]:
    """Per sostre i escenari ×¼: A equips sencers amb la peça encertada contra A xarxes, i si passaria el criteri."""
    font = files.groupby("partit")["font"].first()
    linies = [f"| {A_EQUIPS} amb… | " + " | ".join(QUARTS) + " |", "|---" * (1 + len(QUARTS)) + "|"]
    for sostre in (BASE, *SOSTRES):
        seves = files[(files["base"] == A_EQUIPS) & (files["sostre"] == sostre)].set_index(["escenari", "partit"])
        celles = []
        for escenari in QUARTS:
            dif = (seves["spell_f1"] - xarxes).loc[escenari]
            c = sc.criteri(dif.to_numpy(), font.loc[dif.index].to_numpy())
            celles.append(f"{c['guany']:+.3f} · {c['guanya']}/{c['partits']} {'✓' if c['passa'] else '✗'}")
        linies.append(f"| {'res més' if sostre == BASE else sostre} | " + " | ".join(celles) + " |")
    return linies


def per_escenari(errors: pd.DataFrame, escenari: str) -> list[str]:
    """Les creuades d'un escenari: on cauen i on són, pel que en diu el segon."""
    return [f"### {escenari}", "",
            t3p.md(creuada(errors, escenari, ("lloc", eap.LLOCS), ("segon", SEGONS))), "",
            t3p.md(creuada(errors, escenari, ("forat", FORATS), ("segon", SEGONS))), "",
            t3p.md(creuada(errors, escenari, ("lloc", eap.LLOCS), ("toc", TOCS))), ""]


def main() -> None:
    from banc import errors_als_forats as aquest        # pel nom del mòdul, perquè els processos fills el trobin

    with ProcessPoolExecutor(max_workers=10) as feina:
        tasques = list(feina.map(aquest.tasca, itertools.product(fonts.NOMS, ESCENARIS, BASES)))
    files, imatges, errs = (pd.DataFrame([f for t in tasques for f in t[k]]) for k in ("files", "imatges", "errors"))
    mme.comprova(files, bases=BASES, escenaris=ESCENARIS)
    sortida = [
        "# Banc obert · Com són els errors d'equip als forats", "",
        "Generat amb `uv run python -I -m banc.errors_als_forats`, amb el que han desat `banc.model_a_sense_pilota` i",
        f"`banc.model_a_equips`. Dades obertes. Només per saber-ho. {A_SENSE} i {A_EQUIPS}, a la veritat de toc, amb",
        "el decodificador de cada base triat a cada partit a la veritat de toc (✓ comprovat: el mateix spellF1 que el",
        f"banc de la T3v). Els forats: els trossos sense pilota, amb {t3i.K} imatges més a cada banda. On la veritat és",
        "d'un equip.", "",
        "## Els errors de cada base", "",
        "La part de les imatges on la predicció s'equivoca (hi dona l'altre equip o la D), i on el segon ja s'hi",
        "equivoca (l'equip més probable, sense la D, no és el bo).", "",
        t3p.md(taula_bases(imatges)), "",
        "La D, per font. A aire, la pilota a l'aire es veu projectada més lluny només a DFL; a Metrica és com la",
        "barreja (`banc/degrada.py`).", "",
        t3p.md(taula_d_per_font(imatges)), "",
        "## On són", "",
        "Segons on és la imatge: a la vora d'un forat (es veu la pilota) o dins d'un forat, segons quant dura. Quina",
        "part de les imatges hi ha, on s'equivoca la predicció de cada base, on hi dona la D i quina part dels errors",
        f"d'{A_EQUIPS} hi és.", "",
        t3p.md(taula_on(imatges, "forat", FORATS)), "",
        "Segons si la possessió de la veritat es veu algun cop amb pilota:", "",
        t3p.md(taula_on(imatges, "es veu", ES_VEU)), "",
        f"## Com són els errors d'{A_EQUIPS}", "",
        "*Tota la possessió:* la predicció no hi dona mai el seu equip. *Al començament:* hi arriba tard. *Al final:*",
        "se'n va d'hora. *Al mig:* hi dona una altra cosa i hi torna.", "",
        t3p.md(parts(errs, "lloc", eap.LLOCS)), "",
        "El toc més proper (el començament o el final de la possessió de la veritat): si es veu la pilota o no, i a",
        "quina distància és:", "",
        t3p.md(parts(errs, "toc", TOCS)), "",
        t3p.md(parts(errs, "distancia", eap.DISTANCIES)), "",
        "Quant dura la possessió de la veritat:", "",
        t3p.md(parts(errs, "durada", eap.DURADES)), "",
        "Què en diu el segon: l'encerta (s'equivoca el decodificador), hi dona la D, o hi dona l'altre equip i dubta",
        f"o n'està segur (la probabilitat que dona a l'equip bo davant de l'altre, {eap.DUBTE} o més, o menys).", "",
        t3p.md(parts(errs, "segon", SEGONS)), "",
        "Per escenari, la part de tots els errors: on cauen i on són, pel que en diu el segon, i on cauen, pel toc més",
        "proper.", "",
        *(linia for escenari in ESCENARIS for linia in per_escenari(errs, escenari)),
        "## Els sostres", "",
        f"Quant guanya a {A_EQUIPS} (mitjana dels deu partits) el segon amb l'equip encertat als forats (l'H i l'A",
        "girats on s'equivoca, amb la confiança que tenia), a tot arreu o només en una part; la D perfecta als forats;",
        "i on el segon ja encerta l'equip i la predicció no, el segon perfecte.", "",
        *taula_guanys(files), "",
        f"Contra {XARXES}: el guany de mitjana · en quants partits guanya · ✓ si passaria (> {t3.SOROLL},",
        f"l'interval del 95 % per sobre de zero i {t3.GUANYA_MINIM} partits de 10 o més).", "",
        *taula_criteri(files, de_xarxes()), "",
    ]
    an.DIR_RESULTATS.mkdir(exist_ok=True)
    (an.DIR_RESULTATS / "errors-als-forats.md").write_text("\n".join(sortida))
    print("\n".join(sortida))


if __name__ == "__main__":
    main()
