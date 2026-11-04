"""D'on surt la D que A equips sencers posa a aire ×¼ on la veritat és d'un equip, abans de pensar com treure-la
(`docs/pla-tocs.md`, «Tres maneres de treure la D d'aire ×¼»). Només per saber-ho.

    cd codi && uv run python -I -m banc.la_d_a_aire

A aire, la pilota a l'aire es veu projectada al terra des d'una càmera suposada (`banc/degrada.py`), i només a DFL,
que dona l'alçada. Al net, a barreja ×¼ (els mateixos forats, sense la projecció) i a aire ×¼, a la veritat de toc,
amb A equips sencers i el decodificador triat a cada partit a la veritat de toc (es comprova que l'spellF1 és el del
banc de la T3v), segons a quina distància de la línia s'ha vist la pilota fora del camp:

1. **On es veu la pilota,** la seva.
2. **Als forats** (on no es veu), la de la pilota vista just abans o just després del forat, la que és més lluny de
   les dues.

De cada distància: quina part de les imatges hi ha, on la veritat és d'un equip i on és la D; i on la veritat és d'un
equip, on la predicció i el segon hi donen la D.

Escriu `resultats/la-d-a-aire.md`. Tot són dades obertes.
"""

from __future__ import annotations

import itertools
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from banc import analisi_t3p as t3p
from banc import analisi_t3r as an
from banc import avalua, fonts
from banc import errors_als_forats as eaf
from banc import marge_equips as mme
from banc import pilota_als_forats as paf
from banc import sostre_sense_pilota as ssp
from possessio.oficial import possession_metrics as pm

ESCENARIS = ("net", "barreja ×¼", "aire ×¼")
A_EQUIPS = mme.A_EQUIPS
ES_VEU, AL_FORAT = "es veu la pilota", "al forat"
ONS = (ES_VEU, AL_FORAT)
D_UN_EQUIP, LA_D = "d'un equip", "la D"
DISTANCIES = ((0, 1, "dins del camp (a 1 m o menys)"), (1, 10, "fora, a 1-10 m"), (10, 50, "fora, a 10-50 m"),
              (50, np.inf, "fora, a 50 m o més"))
CAP = "no s'ha vist"
NOMS = (*(nom for _, _, nom in DISTANCIES), CAP)
LLUNY_M = (10.0, 1.0)                               # els sostres: la D perfecta on la pilota s'ha vist tan fora o més
SOSTRES = tuple(f"la D perfecta on la pilota s'ha vist a {m:.0f} m o més fora del camp" for m in LLUNY_M)


def fora_del_camp(pilota_m: np.ndarray, camp: np.ndarray) -> np.ndarray:
    """A quants metres de la línia és la pilota, fora del camp (0 a dins; NaN on no es veu)."""
    x, y = pilota_m[:, 0], pilota_m[:, 1]
    return np.hypot(np.maximum(0.0, np.maximum(-x, x - camp[0])), np.maximum(0.0, np.maximum(-y, y - camp[1])))


def amb_els_forats(fora: np.ndarray) -> np.ndarray:
    """On es veu la pilota, la seva distància; on no, la més gran de la pilota vista just abans i just després (NaN si
    no se n'ha vist cap)."""
    n, vista = len(fora), ~np.isnan(fora)
    i = np.arange(n)
    darrera = np.maximum.accumulate(np.where(vista, i, -1))
    seguent = np.minimum.accumulate(np.where(vista, i, n)[::-1])[::-1]
    abans = np.where(darrera >= 0, fora[np.clip(darrera, 0, n - 1)], np.nan)
    despres = np.where(seguent < n, fora[np.clip(seguent, 0, n - 1)], np.nan)
    return np.where(vista, fora, np.fmax(abans, despres))


def distancies(de_sempre) -> np.ndarray:
    """A cada imatge, la distància de `amb_els_forats`, part per part (un forat no passa d'una part a l'altra)."""
    camp = np.asarray(de_sempre.tracking.camp_m, float)
    out = np.full(de_sempre.n, np.nan)
    for _, inici, ultim in de_sempre.trams:
        part = slice(inici, ultim + 1)
        out[part] = amb_els_forats(fora_del_camp(de_sempre.tracking.pilota[part] * camp, camp))
    return out


def comptes(pred: np.ndarray, toc: np.ndarray, relativa: np.ndarray, vista: np.ndarray, distancia: np.ndarray,
            valides: np.ndarray) -> pd.DataFrame:
    """A les imatges vàlides on la veritat és d'un equip o la D: quantes n'hi ha per on són, la veritat i la distància,
    i a quantes la predicció i el segon (la més alta de les tres) hi donen la D."""
    i = np.flatnonzero(valides & np.isin(toc, (pm.H, pm.A, pm.D)))
    nom = paf.a_quin(DISTANCIES, distancia[i])
    t = pd.DataFrame({"on": np.where(vista[i], ES_VEU, AL_FORAT),
                      "veritat": np.where(toc[i] == pm.D, LA_D, D_UN_EQUIP),
                      "distancia": np.where(nom == "", CAP, nom),
                      "d": pred[i] == pm.D,
                      "segon_d": np.argmax(np.nan_to_num(relativa[i], nan=-np.inf), axis=1) == pm.D})
    return t.groupby(["on", "veritat", "distancia"]).agg(n=("d", "size"), d=("d", "sum"),
                                                         segon_d=("segon_d", "sum")).reset_index()


def tasca(nom_escenari: tuple[str, str]) -> dict[str, list[dict]]:
    nom, escenari = nom_escenari
    pr = eaf.prediccio(nom, escenari, A_EQUIPS)
    pred = pr.decodifica(pr.relativa)
    comu = {"partit": nom, "font": pr.de_sempre.font, "escenari": escenari, "base": A_EQUIPS}
    valides, distancia = ssp.dins(len(pr.toc), pr.trams), distancies(pr.de_sempre)
    c = comptes(pred, pr.toc, pr.relativa, pr.vista, distancia, valides)
    preds = {mme.BASE: pred} | {s: pr.decodifica(eaf.d_perfecta(pr.relativa, pr.toc, valides & (distancia >= m)))
                                for s, m in zip(SOSTRES, LLUNY_M)}
    return {"files": [{**comu, "sostre": s, "spell_f1": avalua.puntua(pr.p_toc, x)["spell_f1"]}
                      for s, x in preds.items()],
            "comptes": [{**comu, **r} for r in c.to_dict("records")]}


def taula_sostres(files: pd.DataFrame, xarxes: pd.Series) -> list[str]:
    """Per sostre i escenari: quant guanya a A equips sencers (mitjana dels partits); i a aire ×¼, contra A xarxes,
    el guany · en quants partits guanya · si passaria."""
    t = files.groupby(["escenari", "sostre"])["spell_f1"].mean().unstack("sostre")
    font = files.groupby("partit")["font"].first()
    linies = ["| | " + " | ".join(ESCENARIS) + " | aire ×¼, contra A xarxes |", "|---" * (2 + len(ESCENARIS)) + "|"]
    for s in (mme.BASE, *SOSTRES):
        seus = files[files["sostre"] == s].set_index(["escenari", "partit"])["spell_f1"]
        dif = (seus - xarxes).loc["aire ×¼"]
        c = eaf.sc.criteri(dif.to_numpy(), font.loc[dif.index].to_numpy())
        celles = [f"{t.loc[e, s]:.3f}" if s == mme.BASE else f"{t.loc[e, s] - t.loc[e, mme.BASE]:+.3f}"
                  for e in ESCENARIS]
        linies.append(f"| {'spellF1 d' + chr(39) + A_EQUIPS if s == mme.BASE else s} | " + " | ".join(celles)
                      + f" | {c['guany']:+.3f} · {c['guanya']}/{c['partits']} {'✓' if c['passa'] else '✗'} |")
    return linies


def taula(c: pd.DataFrame, on: str) -> pd.DataFrame:
    """Per escenari i distància, a `on`: quina part de les imatges d'un equip i de la D hi ha; on la veritat és d'un
    equip, on la predicció i el segon hi donen la D; i quina part de tota la D falsa (a `on` i fora) hi és."""
    totals = c.groupby(["escenari", "veritat"])["n"].sum().unstack("veritat")
    falsa = c[c["veritat"] == D_UN_EQUIP].groupby("escenari")["d"].sum()
    aqui = c[c["on"] == on].groupby(["escenari", "distancia", "veritat"])[["n", "d", "segon_d"]].sum()
    aqui = aqui.unstack("veritat", fill_value=0).reindex(
        columns=pd.MultiIndex.from_product([["n", "d", "segon_d"], [D_UN_EQUIP, LA_D]]), fill_value=0)
    esc = aqui.index.get_level_values("escenari")
    t = pd.DataFrame({
        f"imatges · {D_UN_EQUIP}": aqui[("n", D_UN_EQUIP)] / totals[D_UN_EQUIP].reindex(esc).to_numpy(),
        f"imatges · {LA_D}": aqui[("n", LA_D)] / totals[LA_D].reindex(esc).to_numpy(),
        "la D predita": aqui[("d", D_UN_EQUIP)] / aqui[("n", D_UN_EQUIP)],
        "la D del segon": aqui[("segon_d", D_UN_EQUIP)] / aqui[("n", D_UN_EQUIP)],
        "part de la D falsa": aqui[("d", D_UN_EQUIP)] / falsa.reindex(esc).to_numpy()})
    return eaf.en_ordre(t, ESCENARIS, NOMS)


def main() -> None:
    from banc import la_d_a_aire as aquest              # pel nom del mòdul, perquè els processos fills el trobin

    with ProcessPoolExecutor(max_workers=10) as feina:
        tasques = list(feina.map(aquest.tasca, itertools.product(fonts.NOMS, ESCENARIS)))
    files, tots = (pd.DataFrame([f for t in tasques for f in t[k]]) for k in ("files", "comptes"))
    mme.comprova(files, bases=(A_EQUIPS,), escenaris=ESCENARIS)
    sortida = [
        "# Banc obert · D'on surt la D d'aire ×¼", "",
        "Generat amb `uv run python -I -m banc.la_d_a_aire`, amb el que ha desat `banc.model_a_equips`. Dades obertes.",
        f"Només per saber-ho. {A_EQUIPS}, a la veritat de toc, amb el decodificador triat a cada partit a la veritat",
        "de toc (✓ comprovat: el mateix spellF1 que el banc de la T3v). Les imatges dels trams vàlids on la veritat és",
        "d'un equip o la D. La distància és a quants metres de la línia s'ha vist la pilota fora del camp: on es veu,",
        "la seva; als forats, la més gran de la pilota vista just abans i just després del forat.", "",
    ]
    sortida += ["## Els sostres", "",
                f"Quant guanya a {A_EQUIPS} (mitjana dels deu partits) la D perfecta només on la pilota s'ha vist fora",
                "del camp a 10 m o més, o a 1 m o més (on es veu, la seva; als forats, la de just abans o just després).",
                "A aire ×¼, contra A xarxes, amb el criteri de sempre.", "",
                *taula_sostres(files, eaf.de_xarxes()), ""]
    for font in sorted(tots["font"].unique()):
        c = tots[tots["font"] == font]
        for on in ONS:
            sortida += [f"## {font} · {on}", "", t3p.md(taula(c, on)), ""]
    an.DIR_RESULTATS.mkdir(exist_ok=True)
    (an.DIR_RESULTATS / "la-d-a-aire.md").write_text("\n".join(sortida))
    print("\n".join(sortida))


if __name__ == "__main__":
    main()
