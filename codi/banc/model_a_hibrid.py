"""L'híbrid, cada model on toca (T3g del pla per tocs, `docs/pla-tocs.md`, «T3g»).

    cd codi && uv run python -I -m banc.model_a_hibrid [--processos 12]

No entrena res: fa servir les probabilitats d'A context (T3e) i d'A per possessió (T3f) que ja són a la memòria cau,
de models que no han vist el partit que es prova.

1. **La porta:** A per possessió, decodificat amb el decodificador que la T3f li ha triat en aquell partit (amb els
   altres nou, `resultats/model-a-possessio.json`). Les imatges de les possessions que hi surten de menys de T s són
   «curtes».
2. **La mescla:** a les curtes, el log(P / prior) d'A per possessió; a la resta, el d'A context.
3. **El decodificador** de sempre sobre la mescla. T (0, 1, 2 o 5 s; amb 0 no hi ha cap curta i és A context sol),
   λ i la durada mínima es trien junts amb els altres nou partits als escenaris ×¼, com fins ara.
4. **El criteri** del pla: A híbrid contra A context, el de la cadena, amb el seu decodificador triat igual (entre
   les combinacions amb T = 0).

Escriu `resultats/model-a-hibrid.json` (la clau del codi i les files) i `resultats/model-a-hibrid.md`. Tot són dades
obertes.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from banc import avalua, degrada, fonts
from banc import decodificador_tocs as t3
from banc import model_a_context as t3e
from banc import model_a_possessio as t3f
from banc import model_a_quart as t3b
from cadena import decodifica, model
from possessio import decodificacio
from possessio.decodificacio import _viterbi_durada_minima, log_relativa
from possessio.oficial import possession_metrics as pm

HIBRID = "A híbrid"
METODES = (t3e.CONTEXT, HIBRID)
TS = (0.0, 1.0, 2.0, 5.0)                   # s: les possessions de la porta més curtes, d'A per possessió
DIR_RESULTATS = t3.DIR_RESULTATS
RESULTATS_T3F = DIR_RESULTATS / "model-a-possessio.json"


def portes(cami: Path = RESULTATS_T3F) -> dict[str, tuple[float, int]]:
    """El decodificador d'A per possessió triat a la T3f a cada partit, si els resultats són del codi d'ara."""
    desat = json.loads(cami.read_text())
    if desat.get("clau") != t3f.clau_dels_resultats():
        raise RuntimeError("Els resultats de la T3f són d'un altre codi: torna a fer "
                           "`uv run python -I -m banc.model_a_possessio`")
    return {nom: (float(t[t3f.POSSESSIO][0]), int(t[t3f.POSSESSIO][1])) for nom, t in desat["triades"].items()}


def curtes(porta: np.ndarray, trams: list[tuple[int, int]], t: float) -> np.ndarray:
    """Les imatges de les possessions de la porta (les de la mètrica, dins de `trams`) de menys de `t` s."""
    curta = np.zeros(len(porta), dtype=bool)
    for inici, final, _ in pm.possession_spells(porta.astype(np.int8), trams):
        if final - inici < t * degrada.FPS:
            curta[inici:final] = True
    return curta


def mescla(context: np.ndarray, possessio: np.ndarray, curta: np.ndarray) -> np.ndarray:
    """Les puntuacions que es decodifiquen: les d'A per possessió a les imatges curtes, i les d'A context a la resta."""
    return np.where(curta[:, None], possessio, context)


def per_trams(relativa: np.ndarray, trams: tuple[tuple[int, int, int], ...], lam: float, d_min: int) -> np.ndarray:
    """`decodifica.per_trams` amb les puntuacions ja fetes (log(P / prior)) al lloc de les probabilitats."""
    out = np.full(len(relativa), pm.X, dtype=np.int8)
    for _, inici, fi in trams:
        out[inici:fi + 1] = np.asarray(model.CLASSES)[_viterbi_durada_minima(relativa[inici:fi + 1], lam, d_min)]
    return out


def graella(tasca: tuple[str, str, tuple[float, int]]) -> list[dict]:
    """Un partit i un escenari: cada T, λ i durada mínima, amb la porta de la T3f."""
    nom, escenari, porta_triada = tasca
    p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[escenari])
    probes_c, prior_c = t3e.probabilitats(nom, entrena=False)
    probes_p, prior_p = t3f.probabilitats(nom, entrena=False)
    proba_p = probes_p[escenari].astype(float)
    porta = decodifica.per_trams(proba_p, prior_p, p.trams, *porta_triada)
    context, possessio = log_relativa(probes_c[escenari].astype(float), prior_c), log_relativa(proba_p, prior_p)
    valids = avalua.trams_valids(p)
    puntuades = sum(final - inici for inici, final in valids)
    comu = {"partit": nom, "font": p.font, "escenari": escenari}
    files = []
    for t in TS:
        curta = curtes(porta, valids, t)
        relativa = mescla(context, possessio, curta)
        for lam, d_min in itertools.product(decodifica.GRAELLA_LAMBDA, decodifica.GRAELLA_DMIN):
            files.append({**comu, "T": t, "lam": lam, "d_min": d_min, "part_curta": curta.sum() / puntuades,
                          **avalua.puntua(p, per_trams(relativa, p.trams, lam, d_min))})
    return files


def tria_sense_mirar(files: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Les files d'A context (T = 0, triant λ i la durada) i d'A híbrid (triant T, λ i la durada) a cada partit, amb
    el decodificador triat amb els altres nou als escenaris ×¼. També les triades."""
    triats, triades = [], {}
    for prova in fonts.NOMS:
        altres, seu = files[files["partit"] != prova], files[files["partit"] == prova]
        lam_c, d_c = t3.millor(altres[altres["T"] == 0], ["lam", "d_min"])
        t, lam_h, d_h = t3.millor(altres, ["T", "lam", "d_min"])
        for metode, (t_, lam, d_min) in ((t3e.CONTEXT, (0.0, lam_c, d_c)), (HIBRID, (t, lam_h, d_h))):
            triats.append(seu[(seu["T"] == t_) & (seu["lam"] == lam) & (seu["d_min"] == d_min)].assign(metode=metode))
        triades[prova] = {t3e.CONTEXT: (float(lam_c), int(d_c)), HIBRID: (float(t), float(lam_h), int(d_h))}
    return pd.concat(triats, ignore_index=True), triades


def markdown(c: pd.DataFrame, metodes: pd.DataFrame, triades: dict, passa: dict[str, bool],
             files: pd.DataFrame) -> str:
    ordre = list(METODES)
    linies = ["# Banc obert · L'híbrid, cada model on toca (T3g)", "",
              "Generat amb `uv run python -I -m banc.model_a_hibrid`. Dades obertes: 7 partits de DFL (IDSSE, CC BY",
              "4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el",
              "criteri: `docs/pla-tocs.md`, «T3g», i la capçalera de `banc/model_a_hibrid.py`.", "",
              f"**{t3e.CONTEXT}** és el model de la cadena (T3e). **{HIBRID}** fa servir {t3f.POSSESSIO} (T3f) a les",
              "imatges de les possessions que aquest mateix prediu de menys de T s, i A context a la resta. T, λ i la",
              "durada mínima es trien junts amb els altres nou partits als escenaris ×¼; amb T = 0, és A context.", "",
              "## L'spellF1 i el macroF1 de cada classificador (mitjana dels deu partits)", ""]
    for columna, nom in (("spell_f1", "spellF1"), ("macro_f1", "macroF1")):
        t = metodes.pivot_table(index="escenari", columns="metode", values=columna, sort=False)[ordre]
        linies += [f"**{nom}**", "", "| escenari | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 1) + "|"]
        linies += [f"| {e} | " + " | ".join(f"{v:.3f}" for v in f) + " |" for e, f in t.iterrows()]
        linies.append("")
    linies += [f"## {HIBRID} contra {t3e.CONTEXT} (spellF1): el criteri", "",
               *t3b._taula(c, HIBRID, t3e.CONTEXT), "", *t3b._criteris(passa, False),
               "## Possessions predites per cada real (mitjana dels deu partits), només per saber-ho", "",
               "| escenari | " + " | ".join(ordre) + " |", "|---" * (len(ordre) + 1) + "|"]
    rati = (metodes["possessions"] / metodes["possessions_reals"]).groupby(
        [metodes["escenari"], metodes["metode"]], sort=False).mean().unstack()[ordre]
    linies += [f"| {e} | " + " | ".join(f"{v:.2f}" for v in f) + " |" for e, f in rati.iterrows()]
    linies += ["", "## La part de les imatges puntuades que la porta marca com a curtes, només per saber-ho", "",
               "Mitjana dels deu partits als quatre escenaris ×¼.", "", "| T | curtes |", "|---|---|"]
    quarts = files[files["escenari"].isin(t3.QUARTS)]
    linies += [f"| {t:g} s | {100 * v:.0f} % |" for t, v in quarts.groupby("T")["part_curta"].mean().items()]
    linies += ["", "## Els decodificadors triats (cada partit, amb els altres nou)", ""]
    compta: dict[str, int] = {}
    for t in triades.values():
        lam_c, d_c = t[t3e.CONTEXT]
        t_h, lam_h, d_h = t[HIBRID]
        clau_ = (f"{t3e.CONTEXT}: λ = {lam_c:g}, durada mínima {d_c} · "
                 f"{HIBRID}: T = {t_h:g} s, λ = {lam_h:g}, durada mínima {d_h}")
        compta[clau_] = compta.get(clau_, 0) + 1
    linies += [f"- {k} ({n} partits)" for k, n in compta.items()]
    return "\n".join(linies + [""])


def clau_dels_resultats() -> str:
    """La de la T3f (que porta la d'A context i el codi de tots dos) i el codi de la porta, la mescla i aquest."""
    h = hashlib.sha256(t3f.clau_dels_resultats().encode())
    for modul in (t3f, decodificacio):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def main() -> None:
    from banc import model_a_hibrid as aquest           # pel nom del mòdul, perquè els processos fills el trobin

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    args = ap.parse_args()
    triades_t3f = portes()
    for nom in fonts.NOMS:                              # abans de començar: les de tots dos han de ser a la cau
        t3e.probabilitats(nom, entrena=False)
        t3f.probabilitats(nom, entrena=False)
    tasques = [(nom, e, triades_t3f[nom]) for nom, e in itertools.product(fonts.NOMS, t3.ESCENARIS)]
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        trossos = []
        for (nom, escenari, _), tros in zip(tasques, feina.map(aquest.graella, tasques)):
            trossos.append(tros)
            if escenari == list(t3.ESCENARIS)[-1]:
                print(f"· {nom}: fet", flush=True)
    files = pd.DataFrame([f for tros in trossos for f in tros])
    metodes, triades = tria_sense_mirar(files)
    c = t3b.comparacio(metodes, HIBRID, t3e.CONTEXT)
    passa = t3b.compleix(c)
    desa = {"clau": clau_dels_resultats(), "passa": passa, "comparacio": t3.registres(c), "triades": triades,
            "files": t3.registres(files)}
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-a-hibrid.json").write_text(json.dumps(desa, indent=1, default=float, allow_nan=False))
    (DIR_RESULTATS / "model-a-hibrid.md").write_text(markdown(c, metodes, triades, passa, files))
    print((DIR_RESULTATS / "model-a-hibrid.md").read_text())


if __name__ == "__main__":
    main()
