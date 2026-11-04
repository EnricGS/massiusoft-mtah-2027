"""El marge que queda a sobre d'A sense pilota: els sostres de cada candidata, a sobre d'A xarxes i a sobre d'A sense
pilota, abans de triar la idea següent (`docs/pla-tocs.md`, «El marge que queda a sobre d'A sense pilota»). Només
per saber-ho.

    cd codi && uv run python -I -m banc.marge_sense_pilota

Les dues bases, amb el que han desat els seus bancs i el decodificador triat a cada partit a la veritat de toc
(`resultats/model-a-sense-pilota.json`; es comprova que l'spellF1 de cada partit és el del banc). Al net, als quatre
×¼ i a «partit ×¼», a la veritat de toc:

1. **On són els errors d'equip** de cada predicció: on es veu la pilota i als forats (com a `sostre_curtes`).
2. **Els sostres,** cadascun amb una peça encertada i la resta com la base, tornant a decodificar:
   - **l'equip:** on el segon s'equivoca d'equip, l'H i l'A girats, amb la confiança que tenia (`ssp.equip_encertat`),
     on es veu la pilota o als forats; i *la meitat dels errors*, girats a trossos triats a l'atzar fins a la meitat;
   - **les possessions de menys de 5 s, només l'equip** (`sostre_curtes`);
   - **la q perfecta,** a tot arreu, on es veu la pilota o als forats, i **la D perfecta** (`sostre_curtes`);
   - **les inventades,** cadascuna a l'altre equip, sense tornar a decodificar (`canvis_falsos`, el verificador
     perfecte);
   - **el segon perfecte,** a tot arreu, on es veu la pilota o als forats (`sostre_sense_pilota`).
3. **El criteri, als ×¼, contra A xarxes:** si A sense pilota amb la peça encertada el passaria. Un pas a sobre d'A
   sense pilota ha de passar, sumat, el criteri sencer contra A xarxes.

Escriu `resultats/marge-sense-pilota.md`. Tot són dades obertes.
"""

from __future__ import annotations

import itertools
import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace

import numpy as np
import pandas as pd

from banc import analisi_t3p as t3p
from banc import analisi_t3q as t3q
from banc import analisi_t3r as an
from banc import avalua, fonts
from banc import canvis_falsos as cf
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_partit as mp
from banc import model_a_sense_pilota as msp
from banc import sostre_curtes as sc
from banc import sostre_sense_pilota as ssp
from banc import veritat_toc as vt
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ESCENARIS = t3q.ESCENARIS                           # el net, els quatre ×¼ i «partit ×¼»
QUARTS = t3.QUARTS
XARXES, A_SENSE = msp.XARXES_TOC, msp.A_SENSE       # les dues bases, amb el decodificador triat a la veritat de toc
BASES = (XARXES, A_SENSE)
LLAVOR = 0
PART = 0.5
EQUIP_PILOTA = "on es veu la pilota, l'equip encertat"
MEITAT_PILOTA = "on es veu la pilota, la meitat dels errors d'equip"
EQUIP_FORATS = "als forats, l'equip encertat"
MEITAT_FORATS = "als forats, la meitat dels errors d'equip"
CURTES = "<5 s, només l'equip"
Q, Q_PILOTA, Q_FORATS, D = sc.Q_PERFECTA, sc.Q_AMB_PILOTA, sc.Q_ALS_FORATS, sc.D_PERFECTA
INVENTADES = cf.REGLA
SEGON, SEGON_PILOTA, SEGON_FORATS = ssp.SEGON, ssp.SEGON_PILOTA, ssp.SEGON_FORATS
SOSTRES = (EQUIP_PILOTA, MEITAT_PILOTA, EQUIP_FORATS, MEITAT_FORATS, CURTES, Q, Q_PILOTA, Q_FORATS, D, INVENTADES,
           SEGON, SEGON_PILOTA, SEGON_FORATS)
BASE = "la base"
AMB_PILOTA, ALS_FORATS = ssp.AMB_PILOTA, ssp.ALS_FORATS
PART_ALS_FORATS = "part dels errors als forats"


def meitat_dels_errors(relativa: np.ndarray, toc: np.ndarray, on: np.ndarray, rng: np.random.Generator,
                       part: float = PART) -> np.ndarray:
    """La relativa amb l'H i l'A girats a trossos d'errors d'equip d'`on` triats a l'atzar, fins a haver-ne arreglat
    `part` de les imatges."""
    errors = ssp.errors_d_equip(relativa, toc, on)
    return ssp.gira_a_trossos(relativa, errors, int(np.ceil(part * errors.sum())), rng)


def inventades(pred: np.ndarray, toc: np.ndarray, trams: list[tuple[int, int]]) -> list[dict]:
    """Les possessions predites que són inventades (`cf.inventada`), amb les seves vores, com a `canvis_falsos`."""
    out = []
    for tram in trams:
        for a, b, k in pm.possession_spells(pred, [tram]):
            if cf.inventada(toc, a, b, k):
                out.append({"a": a, "b": b, "k": k, "vores": cf.vores(pred, a, b, tram)})
    return out


def triades() -> dict[str, dict[str, list]]:
    """El decodificador triat a cada partit a la veritat de toc, per a A xarxes i per a A sense pilota."""
    return json.loads((msp.DIR_RESULTATS / "model-a-sense-pilota.json").read_text())["triades"]


def tasca(qui: tuple[str, str, str]) -> dict[str, list[dict]]:
    nom, escenari, base = qui
    de_sempre = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    p_toc = replace(de_sempre, veritat=toc)
    trams = avalua.trams_valids(p_toc)
    valides = ssp.dins(len(toc), trams)
    vista = ~np.isnan(de_sempre.tracking.pilota[:, 0])
    al_forat = sc.forats(vista)
    probes, prior, q_ = msp.de_qui(msp.XARXES if base == XARXES else A_SENSE, nom)
    relativa = log_relativa(probes[escenari].astype(float), prior)
    q = q_[escenari].astype(float)
    w, lam, d_min = triades()[base][nom]

    def decodifica(relativa_: np.ndarray, q__: np.ndarray = q) -> np.ndarray:
        return t3i.per_trams(relativa_, q__, de_sempre.trams, w, lam, int(d_min))

    pred = decodifica(relativa)
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari, "base": base}

    def fila(sostre: str, prediccio: np.ndarray) -> dict:
        return {**comu, "sostre": sostre, "spell_f1": avalua.puntua(p_toc, prediccio)["spell_f1"]}

    pilota, forat = valides & ~al_forat, valides & al_forat
    q_bona = sc.q_perfecta(toc, trams)
    curtes = [p for p in pm.possession_spells(toc, trams) if p[1] - p[0] < sc.CURTA]
    files = [fila(BASE, pred),
             fila(EQUIP_PILOTA, decodifica(ssp.equip_encertat(relativa, toc, pilota))),
             fila(MEITAT_PILOTA, decodifica(meitat_dels_errors(relativa, toc, pilota, np.random.default_rng(LLAVOR)))),
             fila(EQUIP_FORATS, decodifica(ssp.equip_encertat(relativa, toc, forat))),
             fila(MEITAT_FORATS, decodifica(meitat_dels_errors(relativa, toc, forat, np.random.default_rng(LLAVOR)))),
             fila(CURTES, sc.amb_la_veritat(pred, toc, curtes, True)),
             fila(Q, decodifica(relativa, q_bona)),
             fila(Q_PILOTA, decodifica(relativa, np.where(al_forat, q, q_bona))),
             fila(Q_FORATS, decodifica(relativa, np.where(al_forat, q_bona, q))),
             fila(D, decodifica(sc.amb_la_d(relativa, toc))),
             fila(INVENTADES, cf.arregla(pred, inventades(pred, toc, trams))),
             fila(SEGON, decodifica(ssp.perfecte(relativa, toc, valides))),
             fila(SEGON_PILOTA, decodifica(ssp.perfecte(relativa, toc, pilota))),
             fila(SEGON_FORATS, decodifica(ssp.perfecte(relativa, toc, forat)))]
    errors = [{**comu, "on": on, **dict(zip(("n", "encerts"), ssp.encerts_pred(pred, toc, mascara)))}
              for on, mascara in ((AMB_PILOTA, pilota), (ALS_FORATS, forat))]
    return {"files": files, "errors": errors}


def comprova(files: pd.DataFrame, bases: tuple[str, ...] = BASES) -> None:
    """Les `bases` donen, a cada partit i escenari, l'spellF1 del banc de la T3t amb el decodificador triat."""
    banc = pd.DataFrame(json.loads((msp.DIR_RESULTATS / "model-a-sense-pilota.json").read_text())["files"])
    trs = triades()
    for base in bases:
        metode = msp.XARXES if base == XARXES else A_SENSE
        for nom, (w, lam, d_min) in trs[base].items():
            del_banc = banc[(banc["metode"] == metode) & (banc["veritat"] == msp.TOC) & (banc["partit"] == nom)
                            & (banc["w"] == w) & (banc["lam"] == lam) & (banc["d_min"] == d_min)]
            aqui = files[(files["base"] == base) & (files["sostre"] == BASE) & (files["partit"] == nom)]
            junts = aqui.merge(del_banc[["escenari", "spell_f1"]], on="escenari", suffixes=("", " del banc"))
            if (len(junts) != len(ESCENARIS)
                    or not np.allclose(junts["spell_f1"], junts["spell_f1 del banc"], rtol=0, atol=1e-12)):
                raise RuntimeError(f"{base} no dona el del banc de la T3t a {nom}")


def taula_errors(errors: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i base: la part de les imatges d'un equip on la predicció no hi dona aquest equip (l'altre o la
    D), on es veu la pilota i als forats, i quina part de tots aquests errors és als forats."""
    g = errors.groupby(["escenari", "base", "on"])[["n", "encerts"]].sum()
    mal = (g["n"] - g["encerts"]).unstack("on")
    n = g["n"].unstack("on")
    t = pd.DataFrame({AMB_PILOTA: mal[AMB_PILOTA] / n[AMB_PILOTA], ALS_FORATS: mal[ALS_FORATS] / n[ALS_FORATS],
                      PART_ALS_FORATS: mal[ALS_FORATS] / (mal[ALS_FORATS] + mal[AMB_PILOTA])})
    t = t.unstack("base")
    return t3q.ordena(t[[(c, b) for c in (AMB_PILOTA, ALS_FORATS, PART_ALS_FORATS) for b in BASES]])


def guanys(files: pd.DataFrame) -> pd.DataFrame:
    """Per escenari, base i sostre: quant guanya el sostre a la seva base (mitjana dels partits)."""
    t = files.groupby(["escenari", "base", "sostre"])["spell_f1"].mean().unstack("sostre")
    return t[list(SOSTRES)].sub(t[BASE], axis=0)


def taula_marge(files: pd.DataFrame) -> list[str]:
    """Per sostre (files) i escenari (columnes): el guany a sobre d'A xarxes → a sobre d'A sense pilota."""
    g = guanys(files)
    base = files[files["sostre"] == BASE].groupby(["escenari", "base"])["spell_f1"].mean()
    linies = ["| | " + " | ".join(ESCENARIS) + " |", "|---" * (1 + len(ESCENARIS)) + "|",
              "| spellF1 de la base | " + " | ".join(f"{base[(e, XARXES)]:.3f} → {base[(e, A_SENSE)]:.3f}"
                                                   for e in ESCENARIS) + " |"]
    for sostre in SOSTRES:
        linies.append(f"| {sostre} | " + " | ".join(f"{g.loc[(e, XARXES), sostre]:+.3f} → "
                                                   f"{g.loc[(e, A_SENSE), sostre]:+.3f}" for e in ESCENARIS) + " |")
    return linies


def taula_criteri(files: pd.DataFrame) -> list[str]:
    """Per sostre i escenari ×¼: A sense pilota amb la peça encertada contra A xarxes, i si passaria el criteri."""
    font = files.groupby("partit")["font"].first()
    xarxes = files[(files["base"] == XARXES) & (files["sostre"] == BASE)].set_index(["escenari", "partit"])["spell_f1"]
    linies = ["| A sense pilota amb… | " + " | ".join(QUARTS) + " |", "|---" * (1 + len(QUARTS)) + "|"]
    for sostre in (BASE, *SOSTRES):
        de_sense = files[(files["base"] == A_SENSE) & (files["sostre"] == sostre)].set_index(["escenari", "partit"])
        celles = []
        for escenari in QUARTS:
            dif = (de_sense["spell_f1"] - xarxes).loc[escenari]
            c = sc.criteri(dif.to_numpy(), font.loc[dif.index].to_numpy())
            celles.append(f"{c['guany']:+.3f} · {c['guanya']}/{c['partits']} {'✓' if c['passa'] else '✗'}")
        linies.append(f"| {'res més' if sostre == BASE else sostre} | " + " | ".join(celles) + " |")
    return linies


def main() -> None:
    from banc import marge_sense_pilota as aquest       # pel nom del mòdul, perquè els processos fills el trobin

    with ProcessPoolExecutor(max_workers=10) as feina:
        tasques = list(feina.map(aquest.tasca, itertools.product(fonts.NOMS, ESCENARIS, BASES)))
    files, errors = (pd.DataFrame([f for t in tasques for f in t[k]]) for k in ("files", "errors"))
    comprova(files)
    sortida = [
        "# Banc obert · El marge que queda a sobre d'A sense pilota", "",
        "Generat amb `uv run python -I -m banc.marge_sense_pilota`, amb el que han desat `banc.model_a_partit`,",
        "`banc.model_a_q` i `banc.model_a_sense_pilota`. Dades obertes. Només per saber-ho. A la veritat de toc, amb el",
        "decodificador de cada base triat a cada partit a la veritat de toc (✓ comprovat: el mateix spellF1 que el",
        "banc de la T3t).", "",
        "## On són els errors d'equip", "",
        "On la veritat de toc és d'un equip, la part de les imatges on la predicció dona l'altre equip o la D, on es",
        f"veu la pilota i als forats (sense pilota, amb {t3i.K} imatges més a cada banda), i quina part de tots els",
        "errors d'equip és als forats.", "",
        t3p.md(taula_errors(errors)), "",
        "## El marge que queda", "",
        f"Quant guanya cada sostre a la seva base (mitjana dels deu partits): a sobre d'{XARXES} → a sobre",
        f"d'{A_SENSE}. *L'equip encertat:* on el segon s'equivoca d'equip, l'H i l'A girats, amb la confiança que",
        "tenia; *la meitat dels errors:* girats a trossos triats a l'atzar, fins a la meitat de les imatges.",
        f"*{CURTES}:* a les possessions reals de menys de 5 s, la veritat on la base dona l'altre equip. *La q i la D",
        f"perfectes,* com a `sostre_curtes`. *{INVENTADES}:* el verificador perfecte de la T3s. *El segon perfecte,*",
        "com a `sostre_sense_pilota`.", "",
        *taula_marge(files), "",
        "## Passaria el criteri contra A xarxes?", "",
        f"{A_SENSE} amb la peça encertada, contra {XARXES}: el guany de mitjana · en quants partits guanya · ✓ si",
        f"passaria (> {t3.SOROLL}, l'interval del 95 % per sobre de zero i {t3.GUANYA_MINIM} partits de 10 o més).", "",
        *taula_criteri(files), "",
    ]
    an.DIR_RESULTATS.mkdir(exist_ok=True)
    (an.DIR_RESULTATS / "marge-sense-pilota.md").write_text("\n".join(sortida))
    print("\n".join(sortida))


if __name__ == "__main__":
    main()
