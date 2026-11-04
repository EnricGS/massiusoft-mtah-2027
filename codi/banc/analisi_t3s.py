"""Per què no passa la T3s (`docs/pla-tocs.md`, «Per què no passa la T3s»).

    cd codi && uv run python -I -m banc.analisi_t3s

Amb el que han desat els bancs de la T3p (A xarxes) i de la T3s (el segon i la q de cada grup). A cada partit, el
verificador del banc, entrenat amb els tres grups dels altres nou, i el llindar que hi va triar el banc. Es comprova
que A verificador dona l'spellF1 del banc de la T3s. Al net, als quatre ×¼ i a «partit ×¼», a la veritat de toc:

1. **Com canvien encerta i troba amb el llindar,** de 0,1 a 0,9, i quant guanyaria A verificador amb cada un, el
   mateix a tots els partits. Només per saber-ho: el banc tria el llindar amb els altres nou.
2. **Si la probabilitat del verificador diu el que és:** per trams de probabilitat, quantes possessions hi ha i la
   part que són inventades.
3. **Què guanya i què perd:** al llindar triat, arreglant només les inventades que arregla, o només les bones.
4. **Quines no veu:** l'AUC per durada i entre què són.
5. **Amb què aprèn:** la part d'inventades a les possessions dels grups (les d'entrenar) i a les del banc, als sis
   escenaris d'entrenament.

Escriu `resultats/analisi-t3s.md`. Dades obertes, només per saber-ho.
"""

from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from banc import analisi_t3p as t3p
from banc import analisi_t3q as t3q
from banc import canvis_falsos as cf
from banc import fonts
from banc import decodificador_tocs as t3
from banc import model_a_context as t3e
from banc import model_a_verificador as av
from banc import veritat_toc as vt

ESCENARIS = t3q.ESCENARIS                           # el net, els quatre ×¼ i «partit ×¼»
QUARTS = t3.QUARTS
SIS = av.SIS
BASE, TRIAT = av.XARXES_TOC, av.A_VERIFICADOR
NOMES_INVENTADES = "arreglant-ne només les inventades"
NOMES_BONES = "arreglant-ne només les bones"
LLINDARS = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
TRAMS_PROB = (0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0)
GRUPS, BANC = "grups (per entrenar)", "banc"
DIR_RESULTATS = av.DIR_RESULTATS


def del_banc_t3s() -> dict:
    return json.loads((DIR_RESULTATS / "model-a-verificador.json").read_text())


def amb(llindar: float | str, prob: np.ndarray) -> np.ndarray:
    """Les possessions que el verificador arregla amb `llindar`."""
    return np.zeros(len(prob), dtype=bool) if llindar == av.MAI else prob >= llindar


def tasca(nom: str) -> dict[str, list[dict]]:
    """Un partit: A xarxes, A verificador amb el llindar del banc i amb cada llindar d'aquí, i arreglant només les
    inventades o només les bones; les possessions amb la probabilitat; i la part d'inventades als grups i al banc."""
    grups = [av.del_grup(nom, g) for g in range(t3e.GRUPS)]
    verificador = av.entrena(pd.concat(grups, ignore_index=True))
    llindar = del_banc_t3s()["llindars"][nom]
    toc = vt.veritat(nom)
    files, possessions = [], []
    for e in ESCENARIS:
        b = av.del_banc((nom, e))
        po, pred = b["possessions"], b["pred"]
        prob = av.probabilitat(verificador, po)
        tria, inventada = amb(llindar, prob), po["inventada"].to_numpy(dtype=bool)
        comu = {"partit": nom, "font": b["font"], "escenari": e}

        def fila(sostre: str, prediccio: np.ndarray) -> dict:
            return {**comu, "sostre": sostre, "spell_f1": av.puntua(toc, b["trams"], prediccio)}

        files += [{**comu, "sostre": BASE, "spell_f1": b["spell_f1"]},
                  fila(TRIAT, av.arregla_amb(pred, po, prob, llindar)),
                  fila(NOMES_INVENTADES, cf.arregla(pred, po[tria & inventada].to_dict("records"))),
                  fila(NOMES_BONES, cf.arregla(pred, po[tria & ~inventada].to_dict("records"))),
                  *(fila(f"{llindar_:g}", av.arregla_amb(pred, po, prob, llindar_)) for llindar_ in LLINDARS)]
        possessions.append(po[["vores", "dins", "inventada", "durada"]].assign(
            **comu, prob=prob, arreglada=tria, tram=[t3q.durada(d) for d in po["durada"]]))
    d_entrenar = [g[g["dins"]].groupby("escenari")["inventada"].agg(["size", "sum"]).assign(on=GRUPS) for g in grups]
    del_banc = []
    for e in SIS:
        po = av.del_banc((nom, e))["possessions"]
        del_banc.append({"escenari": e, "size": int(po["dins"].sum()), "sum": int(po[po["dins"]]["inventada"].sum()),
                         "on": BANC})
    entrenar = pd.concat([*d_entrenar, pd.DataFrame(del_banc).set_index("escenari")]).reset_index()
    return {"files": files, "possessions": pd.concat(possessions, ignore_index=True).to_dict("records"),
            "entrenar": entrenar.to_dict("records")}


def comprova(files: pd.DataFrame) -> None:
    """A xarxes i A verificador, amb el llindar del banc, donen l'spellF1 del banc de la T3s, partit a partit."""
    banc = pd.DataFrame(del_banc_t3s()["files"]).rename(columns={"metode": "sostre"})
    aqui = files[files["sostre"].isin([BASE, TRIAT])]
    junts = aqui.merge(banc, on=["sostre", "partit", "escenari"], suffixes=("", " del banc"), how="left")
    if (aqui.empty or junts["spell_f1 del banc"].isna().any()
            or not np.allclose(junts["spell_f1"], junts["spell_f1 del banc"], rtol=0, atol=1e-12)):
        raise RuntimeError("A verificador no dona el del banc de la T3s")


def guany(files: pd.DataFrame, sostres: list[str]) -> pd.DataFrame:
    """Per escenari: quant guanya cada sostre a A xarxes (la mitjana dels partits)."""
    t = files.groupby(["escenari", "sostre"], sort=False)["spell_f1"].mean().unstack("sostre")
    return t3q.ordena(t[sostres].sub(t[BASE], axis=0))


def encerta_i_troba(po: pd.DataFrame, tria: np.ndarray) -> dict[str, float]:
    inv = po["inventada"].to_numpy(dtype=bool)
    return {"n arreglades": int(tria.sum()), "encerta": float(inv[tria].mean()) if tria.any() else np.nan,
            "troba": float(tria[inv].mean()) if inv.any() else np.nan}


def taula_llindars(possessions: pd.DataFrame, files: pd.DataFrame) -> pd.DataFrame:
    """Als quatre ×¼ junts, per llindar: quantes n'arregla, la part que encerta, la part de les inventades que troba,
    i el guany de mitjana a A xarxes."""
    po = possessions[possessions["dins"] & possessions["escenari"].isin(QUARTS)]
    g = guany(files[files["escenari"].isin(QUARTS)], [f"{llindar:g}" for llindar in LLINDARS]).mean()
    t = pd.DataFrame.from_dict({f"{llindar:g}": {**encerta_i_troba(po, po["prob"].to_numpy() >= llindar),
                                                  "guany als ×¼": g[f"{llindar:g}"]} for llindar in LLINDARS},
                               orient="index")
    t.index.name = "llindar"
    return t


def taula_calibratge(possessions: pd.DataFrame) -> pd.DataFrame:
    """Als quatre ×¼ junts, per trams de probabilitat: quantes possessions hi ha, la probabilitat mitjana i la part
    que són inventades."""
    po = possessions[possessions["dins"] & possessions["escenari"].isin(QUARTS)]
    noms = [f"{a:g}-{b:g}" for a, b in zip(TRAMS_PROB, TRAMS_PROB[1:])]
    trams = pd.cut(po["prob"], TRAMS_PROB, labels=noms, include_lowest=True).rename("probabilitat")
    g = po.groupby(trams, observed=True)
    t = pd.DataFrame({"n possessions": g.size(), "probabilitat": g["prob"].mean(), "inventades": g["inventada"].mean()})
    t.index = t.index.astype(str)
    return t


def taula_arreglades(possessions: pd.DataFrame) -> pd.DataFrame:
    """Per escenari, al llindar triat: quantes inventades i quantes bones arregla."""
    po = possessions[possessions["dins"] & possessions["arreglada"]]
    g = po.groupby("escenari", sort=False)["inventada"]
    return t3q.ordena(pd.DataFrame({"n inventades": g.sum(), "n bones": g.size() - g.sum()}))


def taula_auc(possessions: pd.DataFrame) -> pd.DataFrame:
    """Als quatre ×¼ junts: l'AUC i la part que troba al llindar triat, per durada i entre què són."""
    po = possessions[possessions["dins"] & possessions["escenari"].isin(QUARTS)]
    files = {}
    for columna, valors in (("tram", t3q.NOMS_DURADA), ("vores", (cf.INSERIDA, cf.AL_COSTAT))):
        for valor in valors:
            t = po[po[columna] == valor]
            inv = t["inventada"].to_numpy(dtype=bool)
            files[valor] = {"n possessions": len(t), "n inventades": int(inv.sum()),
                            "AUC": float(roc_auc_score(inv, t["prob"])) if 0 < inv.sum() < len(inv) else np.nan,
                            "troba": float(t["arreglada"].to_numpy(dtype=bool)[inv].mean()) if inv.any() else np.nan}
    t = pd.DataFrame.from_dict(files, orient="index")
    t.index.name = "possessions"
    return t


def taula_entrenar(entrenar: pd.DataFrame) -> pd.DataFrame:
    """Per escenari d'entrenament: la part d'inventades a les possessions dels grups i a les del banc."""
    g = entrenar.groupby(["escenari", "on"], sort=False)[["size", "sum"]].sum()
    return (g["sum"] / g["size"]).unstack("on").reindex(list(SIS))[[GRUPS, BANC]]


def main() -> None:
    with ProcessPoolExecutor(max_workers=10) as feina:
        tasques = list(feina.map(tasca, fonts.NOMS))
    files, possessions, entrenar = (pd.DataFrame([f for t in tasques for f in t[k]])
                                    for k in ("files", "possessions", "entrenar"))
    comprova(files)
    sortida = [
        "# Banc obert · Per què no passa la T3s", "",
        "Generat amb `uv run python -I -m banc.analisi_t3s`, amb el que han desat `banc.model_a_partit` i",
        "`banc.model_a_verificador`. Dades obertes, només per saber-ho. A la veritat de toc, amb el verificador i el",
        f"llindar del banc a cada partit (✓ comprovat: {BASE} i {TRIAT} donen l'spellF1 del banc de la T3s).", "",
        "## Com canvien encerta i troba amb el llindar", "",
        "Als quatre ×¼ junts, les possessions dins de la veritat dels deu partits. *encerta:* de les que arregla, la",
        "part que són inventades; *troba:* de les inventades, la part que arregla. El guany és el de mitjana dels",
        "quatre ×¼, amb el mateix llindar a tots els partits.", "", t3p.md(taula_llindars(possessions, files)), "",
        "El guany a cada escenari, amb el mateix llindar a tots els partits:", "",
        t3p.md(guany(files, [f"{llindar:g}" for llindar in LLINDARS])), "",
        "## Si la probabilitat diu el que és", "",
        "Als quatre ×¼ junts, per trams de la probabilitat que dona el verificador: quantes possessions hi ha, la",
        "probabilitat mitjana i la part que són inventades.", "", t3p.md(taula_calibratge(possessions)), "",
        "## Què guanya i què perd", "",
        f"Al llindar triat a cada partit: quant guanya {TRIAT} a {BASE}, i quant si només arreglés les inventades que",
        "arregla o només les bones. I quantes n'arregla de cada.", "",
        t3p.md(guany(files, [TRIAT, NOMES_INVENTADES, NOMES_BONES]).join(taula_arreglades(possessions))), "",
        "## Quines no veu", "",
        "Als quatre ×¼ junts: l'AUC per durada de la possessió i entre què és, i la part de les inventades que troba",
        "al llindar triat.", "", t3p.md(taula_auc(possessions)), "",
        "## Amb què aprèn", "",
        "Als sis escenaris d'entrenament, la part de les possessions dins de la veritat que són inventades: a les que",
        "decodifiquen el segon i la q dels grups (amb les que aprèn el verificador) i a les del banc (les d'A xarxes).",
        "", t3p.md(taula_entrenar(entrenar)), "",
    ]
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "analisi-t3s.md").write_text("\n".join(sortida))
    print("\n".join(sortida))


if __name__ == "__main__":
    main()
