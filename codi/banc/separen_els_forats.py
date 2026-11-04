"""Si els trets dels forats curts separen els d'un canvi dels sense canvi, sense entrenar res (pas 1 de la T3x,
`docs/pla-tocs.md`, «T3x»; D-56).

    cd codi && uv run python -I -m banc.separen_els_forats

A sobre d'A equips sencers, amb el decodificador triat a cada partit a la veritat de toc (es comprova que l'spellF1 és
el del banc de la T3v). Als quatre ×¼ i a «partit ×¼», a la veritat de toc:

1. **Els forats** de `cadena/forats_curts.py` (de menys de 5 s, amb la pilota vista a les dues vores, a la mateixa
   part), amb totes les imatges de la vora d'abans a la de després als trams vàlids. El tipus de cada forat i el que
   hi fa la predicció, com a `canvis_als_forats.py`.
2. **Els trets** de cada forat (`forats_curts.trets`), els nous i els que la cadena ja sap.
3. **Els grups,** els dos errors de «Tres maneres»: on la predicció hi canvia (els d'un canvi on hi fa el canvi, contra
   els sense canvi on hi canvia d'equip) i on no hi canvia (els d'un canvi on el fa fora, contra els sense canvi on no
   hi canvia). I tots els d'un canvi contra tots els sense canvi.
4. **L'AUC de cada tret a cada grup,** amb els forats dels deu partits junts, sense els que no tenen el tret.

**La porta, escrita abans:** es fa el pas 2 si, a curts ×¼, algun tret nou té un AUC de 0,60 o més, o de 0,40 o menys,
en algun dels dos grups.

Escriu `resultats/separen-els-forats.md`. Tot són dades obertes.
"""

from __future__ import annotations

import itertools
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from banc import analisi_t3p as t3p
from banc import avalua, fonts
from banc import canvis_als_forats as caf
from banc import decodificador_tocs as t3
from banc import errors_als_forats as eaf
from banc import marge_equips as mme
from banc import sostre_sense_pilota as ssp
from cadena import forats_curts as fc

ESCENARIS = eaf.ESCENARIS                           # els quatre ×¼ i «partit ×¼»
CURTS = "curts ×¼"                                  # on es mira la porta
A_EQUIPS = mme.A_EQUIPS
H, A = caf.H, caf.A
HI_CANVIA = "la predicció hi canvia"
NO_HI_CANVIA = "la predicció no hi canvia"
TOTS = "tots"
GRUPS = {HI_CANVIA: ((caf.FA_EL_CANVI,), (caf.CANVIA,)),            # (els d'un canvi, els sense canvi)
         NO_HI_CANVIA: ((caf.EL_D_ABANS, caf.EL_NOU), (caf.NO_CANVIA,))}
PORTA = 0.10                                        # l'AUC, a 0,10 o més de 0,5


def del_forat(toc: np.ndarray, pred: np.ndarray, a: int, b: int) -> tuple[str, str]:
    """El tipus del forat [a, b] i què hi fa la predicció (només als d'un canvi i als sense canvi)."""
    tros, p = toc[a - 1:b + 2], pred[a - 1:b + 2]
    tipus = caf.tipus(tros)
    equips = tros[np.isin(tros, ssp.EQUIPS)]
    if tipus == caf.UN:
        vell = int(equips[0])
        return tipus, caf.que_fa(p, vell, A if vell == H else H)[0]
    if tipus == caf.SENSE:
        return tipus, caf.que_fa_sense(p, int(equips[0]))
    return tipus, ""


def tasca(nom_escenari: tuple[str, str]) -> dict[str, list[dict]]:
    """Un partit i un escenari: l'spellF1 d'A equips sencers, i el tipus, el que hi fa la predicció i els trets de cada
    forat curt."""
    nom, escenari = nom_escenari
    pr = eaf.prediccio(nom, escenari, A_EQUIPS)
    pred = pr.decodifica(pr.relativa)
    comu = {"partit": nom, "font": pr.de_sempre.font, "escenari": escenari}
    valides = ssp.dins(len(pr.toc), pr.trams)
    forats_ = fc.forats(pr.vista, pr.de_sempre.trams)
    forats_ = forats_[[valides[a - 1:b + 2].all() for a, b, _, _ in forats_]]
    trets = fc.trets(pr.de_sempre.tracking, forats_, pr.de_sempre.trams)
    de_cada = [del_forat(pr.toc, pred, a, b) for a, b, _, _ in forats_]
    forats_d = [{**comu, "tipus": t, "fa": fa, **x} for (t, fa), x in zip(de_cada, trets.to_dict("records"))]
    return {"files": [{**comu, "base": A_EQUIPS, "sostre": mme.BASE,
                       "spell_f1": avalua.puntua(pr.p_toc, pred)["spell_f1"]}],
            "forats": forats_d}


def auc(x: pd.Series, un: pd.Series) -> float:
    """L'AUC del tret `x` per separar els d'un canvi (`un`) dels sense canvi, sense els que no el tenen; NaN si en
    falta un dels dos."""
    hi_es = x.notna()
    y = un[hi_es]
    return float(roc_auc_score(y, x[hi_es])) if y.nunique() == 2 else np.nan


def dels_grups(forats_: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Els forats de cada grup, amb la columna «un» (si és d'un canvi)."""
    un, sense = forats_["tipus"] == caf.UN, forats_["tipus"] == caf.SENSE
    out = {g: forats_[(un & forats_["fa"].isin(fa_un)) | (sense & forats_["fa"].isin(fa_sense))]
           for g, (fa_un, fa_sense) in GRUPS.items()}
    out[TOTS] = forats_[un | sense]
    return {g: f.assign(un=f["tipus"] == caf.UN) for g, f in out.items()}


def taula_auc(forats_: pd.DataFrame) -> pd.DataFrame:
    """A cada grup, quants forats d'un canvi i sense canvi hi ha, i l'AUC de cada tret."""
    files = []
    for g, f in dels_grups(forats_).items():
        files.append({"grup": g, "n d'un canvi": int(f["un"].sum()), "n sense canvi": int((~f["un"]).sum()),
                      **{x: auc(f[x], f["un"]) for x in fc.TRETS}})
    return pd.DataFrame(files).set_index("grup")


def porta(forats_: pd.DataFrame) -> tuple[bool, pd.DataFrame]:
    """La porta, a curts ×¼: si algun tret nou s'allunya `PORTA` o més de 0,5 en algun dels dos grups; i els que ho
    fan."""
    t = taula_auc(forats_[forats_["escenari"] == CURTS]).loc[list(GRUPS), list(fc.NOUS)]
    llarg = t.stack().rename("AUC").reset_index().rename(columns={"level_1": "tret"})
    lluny = llarg[(llarg["AUC"] - 0.5).abs() >= PORTA - 1e-12]
    return len(lluny) > 0, lluny


def per_escenari(forats_: pd.DataFrame, grup: str) -> pd.DataFrame:
    """L'AUC de cada tret a `grup`, a cada escenari."""
    t = pd.DataFrame({e: taula_auc(forats_[forats_["escenari"] == e]).loc[grup, list(fc.TRETS)] for e in ESCENARIS})
    return t.rename_axis("tret")


def tipus_i_fets(forats_: pd.DataFrame) -> pd.DataFrame:
    """A cada escenari, quants forats curts de cada tipus i què hi fa la predicció."""
    f = forats_[forats_["tipus"].isin((caf.UN, caf.SENSE))]
    t = f.groupby(["tipus", "fa", "escenari"]).size().unstack("escenari").reindex(columns=list(ESCENARIS)).fillna(0)
    t.columns = [f"n {c}" for c in t.columns]
    return t


def markdown(forats_: pd.DataFrame, passa: bool, lluny: pd.DataFrame) -> str:
    curts = forats_[forats_["escenari"] == CURTS]
    linies = ["# Banc obert · Si els trets dels forats curts els separen (pas 1 de la T3x)", "",
              "Generat amb `uv run python -I -m banc.separen_els_forats`, amb el que ha desat `banc.model_a_equips`.",
              f"Dades obertes. Sense entrenar res. {A_EQUIPS}, a la veritat de toc, amb el decodificador triat a cada",
              "partit a la veritat de toc (✓ comprovat: el mateix spellF1 que el banc de la T3v). Els forats són els de",
              "`cadena/forats_curts.py` (de menys de 5 s, amb la pilota vista a les dues vores), amb",
              "les dues vores als trams vàlids. Com es fa i la porta: `docs/pla-tocs.md`, «T3x».", "",
              "L'AUC és la probabilitat que, d'un forat d'un canvi i un de sense canvi triats a l'atzar, el tret sigui",
              "més gran al d'un canvi: amb 1 o 0, els separa del tot; amb 0,5, gens. Els forats dels deu partits, junts;",
              "a cada tret, sense els forats que no el tenen.", "",
              f"## La porta, a {CURTS}", "",
              f"Es fa el pas 2 si algun tret nou ({', '.join(fc.NOUS)}) té un AUC de {0.5 + PORTA:.2f} o més, o de",
              f"{0.5 - PORTA:.2f} o menys, a «{HI_CANVIA}» o a «{NO_HI_CANVIA}».", ""]
    if passa:
        linies += ["**✓ Es fa el pas 2.** Els que hi arriben:", "", t3p.md(lluny.set_index(["grup", "tret"])), ""]
    else:
        linies += ["**✗ No es fa el pas 2:** cap tret nou no hi arriba.", ""]
    t = taula_auc(curts)
    linies += [f"## Tots els trets, a {CURTS}", "", t3p.md(t[list(fc.TRETS)].T.rename_axis("tret")), "",
               f"Els nous són els {len(fc.NOUS)} primers. Quants forats hi ha a cada grup:", "",
               t3p.md(t[["n d'un canvi", "n sense canvi"]]), ""]
    for grup in (*GRUPS, TOTS):
        linies += [f"## «{grup}», a cada escenari", "", t3p.md(per_escenari(forats_, grup)), ""]
    linies += ["## Els forats curts, per tipus i pel que hi fa la predicció", "", t3p.md(tipus_i_fets(forats_)), ""]
    return "\n".join(linies)


def main() -> None:
    from banc import separen_els_forats as aquest       # pel nom del mòdul, perquè els processos fills el trobin

    with ProcessPoolExecutor(max_workers=10) as feina:
        tasques = list(feina.map(aquest.tasca, itertools.product(fonts.NOMS, ESCENARIS)))
    files, forats_ = (pd.DataFrame([f for t in tasques for f in t[k]]) for k in ("files", "forats"))
    mme.comprova(files, bases=(A_EQUIPS,), escenaris=ESCENARIS)
    passa, lluny = porta(forats_)
    md = markdown(forats_, passa, lluny)
    (t3.DIR_RESULTATS / "separen-els-forats.md").write_text(md)
    print(md)


if __name__ == "__main__":
    main()
