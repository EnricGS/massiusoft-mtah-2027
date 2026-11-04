"""El marge que queda a sobre d'A equips sencers: els sostres de cada candidata, a sobre d'A sense pilota i a sobre
d'A equips sencers, abans de triar la idea següent (`docs/pla-tocs.md`, «El marge que queda a sobre d'A equips
sencers»). Només per saber-ho.

    cd codi && uv run python -I -m banc.marge_equips

Com a `marge_sense_pilota.py`, amb les bases que ha desat el banc de la T3v i el decodificador triat a cada partit a
la veritat de toc (`resultats/model-a-equips.json`; es comprova que l'spellF1 de cada partit és el del banc). Al net,
als quatre ×¼ i a «partit ×¼», a la veritat de toc:

1. **On són els errors d'equip** de cada predicció (A xarxes, A sense pilota i A equips sencers): on es veu la pilota i
   als forats.
2. **Els sostres** de `marge_sense_pilota.py`, cadascun amb una peça encertada i la resta com la base, i dos més:
   l'equip encertat als forats només a les possessions de la veritat que no es veuen mai amb pilota, o només a les que
   es veuen algun cop (com a `pilota_als_forats.py`).
3. **El criteri, als ×¼, contra A xarxes:** si A equips sencers amb la peça encertada el passaria.

Escriu `resultats/marge-equips.md`. Tot són dades obertes.
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
from banc import marge_sense_pilota as msm
from banc import model_a_canvis as t3i
from banc import model_a_equips as mae
from banc import model_a_partit as mp
from banc import pilota_als_forats as paf
from banc import sostre_curtes as sc
from banc import sostre_sense_pilota as ssp
from banc import veritat_toc as vt
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ESCENARIS = msm.ESCENARIS                           # el net, els quatre ×¼ i «partit ×¼»
QUARTS = msm.QUARTS
XARXES, A_SENSE, A_EQUIPS = mae.XARXES_TOC, mae.A_SENSE, mae.A_EQUIPS
BASES = (A_SENSE, A_EQUIPS)                         # les dues bases dels sostres
TOTES = (XARXES, *BASES)                            # i A xarxes, per als errors i el criteri
METODE = {XARXES: mae.XARXES, A_SENSE: A_SENSE, A_EQUIPS: A_EQUIPS}
EQUIP_MAI = "als forats, l'equip encertat a les possessions que no es veuen mai"
EQUIP_ALGUN_COP = "als forats, l'equip encertat a les possessions que es veuen algun cop"
SOSTRES = (*msm.SOSTRES[:4], EQUIP_MAI, EQUIP_ALGUN_COP, *msm.SOSTRES[4:])
BASE = msm.BASE
AMB_PILOTA, ALS_FORATS, PART_ALS_FORATS = msm.AMB_PILOTA, msm.ALS_FORATS, msm.PART_ALS_FORATS


def triades() -> dict[str, dict[str, list]]:
    """El decodificador triat a cada partit a la veritat de toc, per a cada base (el banc de la T3v)."""
    return json.loads((mae.DIR_RESULTATS / "model-a-equips.json").read_text())["triades"]


def per_possessio(toc: np.ndarray, trams: list[tuple[int, int]], vista: np.ndarray,
                  forat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Les imatges de `forat` a possessions de la veritat que no es veuen mai amb pilota, i a les que sí."""
    es_veu, _ = paf.possessions(toc, trams, vista)
    return forat & (es_veu == paf.MAI), forat & (es_veu == paf.ALGUN_COP)


def sostres(relativa: np.ndarray, q: np.ndarray, pred: np.ndarray, toc: np.ndarray, trams: list[tuple[int, int]],
            vista: np.ndarray, decodifica) -> dict[str, np.ndarray]:
    """La predicció de cada sostre: una peça encertada i la resta com la base."""
    valides, al_forat = ssp.dins(len(toc), trams), sc.forats(vista)
    pilota, forat = valides & ~al_forat, valides & al_forat
    mai, algun_cop = per_possessio(toc, trams, vista, forat)
    q_bona = sc.q_perfecta(toc, trams)
    curtes = [p for p in pm.possession_spells(toc, trams) if p[1] - p[0] < sc.CURTA]

    def meitat(on: np.ndarray) -> np.ndarray:
        return decodifica(msm.meitat_dels_errors(relativa, toc, on, np.random.default_rng(msm.LLAVOR)))

    return {msm.EQUIP_PILOTA: decodifica(ssp.equip_encertat(relativa, toc, pilota)),
            msm.MEITAT_PILOTA: meitat(pilota),
            msm.EQUIP_FORATS: decodifica(ssp.equip_encertat(relativa, toc, forat)),
            msm.MEITAT_FORATS: meitat(forat),
            EQUIP_MAI: decodifica(ssp.equip_encertat(relativa, toc, mai)),
            EQUIP_ALGUN_COP: decodifica(ssp.equip_encertat(relativa, toc, algun_cop)),
            msm.CURTES: sc.amb_la_veritat(pred, toc, curtes, True),
            msm.Q: decodifica(relativa, q_bona),
            msm.Q_PILOTA: decodifica(relativa, np.where(al_forat, q, q_bona)),
            msm.Q_FORATS: decodifica(relativa, np.where(al_forat, q_bona, q)),
            msm.D: decodifica(sc.amb_la_d(relativa, toc)),
            msm.INVENTADES: cf.arregla(pred, msm.inventades(pred, toc, trams)),
            msm.SEGON: decodifica(ssp.perfecte(relativa, toc, valides)),
            msm.SEGON_PILOTA: decodifica(ssp.perfecte(relativa, toc, pilota)),
            msm.SEGON_FORATS: decodifica(ssp.perfecte(relativa, toc, forat))}


def tasca(qui: tuple[str, str, str]) -> dict[str, list[dict]]:
    """Un partit, un escenari i una base: l'spellF1 de la base i dels sostres (d'A xarxes, només el de la base), i els
    errors d'equip on es veu la pilota i als forats."""
    nom, escenari, base = qui
    de_sempre = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    p_toc = replace(de_sempre, veritat=toc)
    trams = avalua.trams_valids(p_toc)
    vista = ~np.isnan(de_sempre.tracking.pilota[:, 0])
    probes, prior, q_ = mae.de_qui(METODE[base], nom)
    relativa = log_relativa(probes[escenari].astype(float), prior)
    q = q_[escenari].astype(float)
    w, lam, d_min = triades()[base][nom]

    def decodifica(relativa_: np.ndarray, q__: np.ndarray = q) -> np.ndarray:
        return t3i.per_trams(relativa_, q__, de_sempre.trams, w, lam, int(d_min))

    pred = decodifica(relativa)
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari, "base": base}
    preds = {BASE: pred} | (sostres(relativa, q, pred, toc, trams, vista, decodifica) if base in BASES else {})
    files = [{**comu, "sostre": s, "spell_f1": avalua.puntua(p_toc, p)["spell_f1"]} for s, p in preds.items()]
    valides, al_forat = ssp.dins(len(toc), trams), sc.forats(vista)
    errors = [{**comu, "on": on, **dict(zip(("n", "encerts"), ssp.encerts_pred(pred, toc, mascara)))}
              for on, mascara in ((AMB_PILOTA, valides & ~al_forat), (ALS_FORATS, valides & al_forat))]
    return {"files": files, "errors": errors}


def comprova(files: pd.DataFrame, bases: tuple[str, ...] = TOTES, escenaris: tuple[str, ...] = ESCENARIS) -> None:
    """Cada base dona, a cada partit i escenari, l'spellF1 del banc de la T3v amb el decodificador triat."""
    banc = pd.DataFrame(json.loads((mae.DIR_RESULTATS / "model-a-equips.json").read_text())["files"])
    for base, triats in triades().items():
        if base not in bases:
            continue
        for nom, (w, lam, d_min) in triats.items():
            del_banc = banc[(banc["metode"] == METODE[base]) & (banc["veritat"] == mae.TOC) & (banc["partit"] == nom)
                            & (banc["w"] == w) & (banc["lam"] == lam) & (banc["d_min"] == d_min)]
            aqui = files[(files["base"] == base) & (files["sostre"] == BASE) & (files["partit"] == nom)]
            junts = aqui.merge(del_banc[["escenari", "spell_f1"]], on="escenari", suffixes=("", " del banc"))
            if (len(junts) != len(escenaris)
                    or not np.allclose(junts["spell_f1"], junts["spell_f1 del banc"], rtol=0, atol=1e-12)):
                raise RuntimeError(f"{base} no dona el del banc de la T3v a {nom}")


def taula_errors(errors: pd.DataFrame) -> pd.DataFrame:
    """Com `msm.taula_errors`, amb les tres bases."""
    g = errors.groupby(["escenari", "base", "on"])[["n", "encerts"]].sum()
    mal = (g["n"] - g["encerts"]).unstack("on")
    n = g["n"].unstack("on")
    t = pd.DataFrame({AMB_PILOTA: mal[AMB_PILOTA] / n[AMB_PILOTA], ALS_FORATS: mal[ALS_FORATS] / n[ALS_FORATS],
                      PART_ALS_FORATS: mal[ALS_FORATS] / (mal[ALS_FORATS] + mal[AMB_PILOTA])}).unstack("base")
    return t3q.ordena(t[[(c, b) for c in (AMB_PILOTA, ALS_FORATS, PART_ALS_FORATS) for b in TOTES]])


def taula_marge(files: pd.DataFrame) -> list[str]:
    """Per sostre (files) i escenari (columnes): el guany a sobre d'A sense pilota → a sobre d'A equips sencers."""
    de_les_bases = files[files["base"].isin(BASES)]
    t = de_les_bases.groupby(["escenari", "base", "sostre"])["spell_f1"].mean().unstack("sostre")
    g = t[list(SOSTRES)].sub(t[BASE], axis=0)
    linies = ["| | " + " | ".join(ESCENARIS) + " |", "|---" * (1 + len(ESCENARIS)) + "|",
              "| spellF1 de la base | " + " | ".join(f"{t.loc[(e, A_SENSE), BASE]:.3f} → {t.loc[(e, A_EQUIPS), BASE]:.3f}"
                                                   for e in ESCENARIS) + " |"]
    for sostre in SOSTRES:
        linies.append(f"| {sostre} | " + " | ".join(f"{g.loc[(e, A_SENSE), sostre]:+.3f} → "
                                                   f"{g.loc[(e, A_EQUIPS), sostre]:+.3f}" for e in ESCENARIS) + " |")
    return linies


def taula_criteri(files: pd.DataFrame) -> list[str]:
    """Per sostre i escenari ×¼: A equips sencers amb la peça encertada contra A xarxes, i si passaria el criteri."""
    font = files.groupby("partit")["font"].first()
    xarxes = files[(files["base"] == XARXES) & (files["sostre"] == BASE)].set_index(["escenari", "partit"])["spell_f1"]
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


def main() -> None:
    from banc import marge_equips as aquest           # pel nom del mòdul, perquè els processos fills el trobin

    with ProcessPoolExecutor(max_workers=10) as feina:
        tasques = list(feina.map(aquest.tasca, itertools.product(fonts.NOMS, ESCENARIS, TOTES)))
    files, errors = (pd.DataFrame([f for t in tasques for f in t[k]]) for k in ("files", "errors"))
    comprova(files)
    sortida = [
        "# Banc obert · El marge que queda a sobre d'A equips sencers", "",
        "Generat amb `uv run python -I -m banc.marge_equips`, amb el que han desat `banc.model_a_partit`,",
        "`banc.model_a_sense_pilota` i `banc.model_a_equips`. Dades obertes. Només per saber-ho. A la veritat de toc,",
        "amb el decodificador de cada base triat a cada partit a la veritat de toc (✓ comprovat: el mateix spellF1",
        "que el banc de la T3v).", "",
        "## On són els errors d'equip", "",
        "On la veritat de toc és d'un equip, la part de les imatges on la predicció dona l'altre equip o la D, on es",
        f"veu la pilota i als forats (sense pilota, amb {t3i.K} imatges més a cada banda), i quina part de tots els",
        "errors d'equip és als forats.", "",
        t3p.md(taula_errors(errors)), "",
        "## El marge que queda", "",
        f"Quant guanya cada sostre a la seva base (mitjana dels deu partits): a sobre d'{A_SENSE} → a sobre",
        f"d'{A_EQUIPS}. Els sostres, com a `marge_sense_pilota.py`; els dos nous, l'equip encertat als forats només a",
        "les possessions de la veritat que no es veuen mai amb pilota, o només a les que es veuen algun cop.", "",
        *taula_marge(files), "",
        "## Passaria el criteri contra A xarxes?", "",
        f"{A_EQUIPS} amb la peça encertada, contra {XARXES}: el guany de mitjana · en quants partits guanya · ✓ si",
        f"passaria (> {t3.SOROLL}, l'interval del 95 % per sobre de zero i {t3.GUANYA_MINIM} partits de 10 o més).", "",
        *taula_criteri(files), "",
    ]
    an.DIR_RESULTATS.mkdir(exist_ok=True)
    (an.DIR_RESULTATS / "marge-equips.md").write_text("\n".join(sortida))
    print("\n".join(sortida))


if __name__ == "__main__":
    main()
