"""L'opció A al banc: el model de la cadena, entrenat deixant cada partit fora, i el decodificador triat amb els
altres partits.

    cd codi && uv run python -I -m banc.model_a [--processos 2]

1. Per a cada partit, un model entrenat amb els altres nou, amb els tres escenaris degradats junts. El tracking del
   concurs és brut, però no sabem com; el net només es prova.
2. Les probabilitats del partit que queda fora, als quatre escenaris, a la memòria cau (`dades/banc/a/`). Es refà
   sola si canvia el codi que les fa (els senyals, el model, la degradació, els partits, com s'entrena aquí) o la
   versió del LightGBM, del numpy o del pandas. La clau es calcula un sol cop, en començar.
3. Cada combinació de penalització i durada mínima, a cada partit i escenari, i les dues línies base de referència.
4. Per a cada partit, la combinació que va millor de mitjana als ALTRES nou, als escenaris degradats, i amb aquesta,
   la seva puntuació. Ni el model ni el decodificador no han vist el partit que es puntua. Els models dels altres
   partits sí que l'han vist, a l'entrenament: és l'única drecera, i només toca dos números.

Escriu `resultats/model-a.json` (la clau del codi que fa els resultats i totes les files) i `resultats/model-a.md`
(el resum). Tot són dades obertes. `model_final.py` en treu el decodificador de la cadena, si la clau és la del codi d'ara.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import inspect
import itertools
import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import lightgbm
import numpy as np
import pandas as pd

from banc import avalua, degrada, dfl, fonts, linies_base, metrica, partit
from cadena import decodifica, model, senyals
from possessio import decodificacio
from possessio.oficial import possession_metrics as pm

ESCENARIS_ENTRENAMENT = ("curts", "llargs", "barreja")
REFERENCIES = {"smooth125·X": 125, "smooth50·X": 50}       # la millor línia base al banc, i la publicada
DIR_CAU_A = fonts.DIR_CAU / "a"
DIR_RESULTATS = Path(__file__).resolve().parent / "resultats"
SOROLL = pm.SPELL_NOISE_BAND                                 # per sota, una diferència d'spellF1 és soroll
LLAVOR_BOOTSTRAP = 20271024


@functools.cache
def mostres_de(nom: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Les mostres d'entrenament d'un partit, dels tres escenaris (un cop per procés: cada model en fa servir nou)."""
    xs, ys = [], []
    for escenari in ESCENARIS_ENTRENAMENT:
        p = degrada.aplica(fonts.partit(nom), escenari)
        x, y = model.mostres([senyals.calcula(p.tracking, p.trams)], [p.veritat], model.PAS)
        xs.append(x)
        ys.append(y)
    return pd.concat(xs, ignore_index=True), np.concatenate(ys)


def probabilitats(prova: str, entrena: bool = True) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Les del partit `prova` a cada escenari, amb el model entrenat amb els altres, i el prior de l'entrenament.
    Amb `entrena=False`, només les llegeix de la memòria cau, i si no hi són o són d'un altre codi, s'atura."""
    cami = DIR_CAU_A / f"{prova}.npz"
    if cami.exists():
        with np.load(cami, allow_pickle=False) as desat:
            if str(desat["clau"]) == CLAU:
                return {e: desat[e] for e in degrada.NOMS}, desat["prior"]
    if not entrena:
        raise RuntimeError(f"Falten les probabilitats de {prova} a la memòria cau, o són d'un altre codi")
    mostres = [mostres_de(nom) for nom in fonts.NOMS if nom != prova]
    x, y = pd.concat([m[0] for m in mostres], ignore_index=True), np.concatenate([m[1] for m in mostres])
    entrenat = model.entrena(x, y)
    prior = model.prior(y)
    probes = {}
    for escenari in degrada.NOMS:
        p = degrada.aplica(fonts.partit(prova), escenari)
        probes[escenari] = model.probabilitats(entrenat, senyals.calcula(p.tracking, p.trams)).astype(np.float32)
    DIR_CAU_A.mkdir(parents=True, exist_ok=True)
    temporal = cami.with_name(f"{cami.name}.{os.getpid()}.part.npz")
    np.savez(temporal, clau=CLAU, prior=prior, **probes)
    temporal.replace(cami)
    return probes, prior


def graella(prova_i_escenari: tuple[str, str]) -> list[dict]:
    """Totes les combinacions del decodificador, i les referències, en un partit i un escenari."""
    prova, escenari = prova_i_escenari
    probes, prior = probabilitats(prova, entrena=False)
    p = degrada.aplica(fonts.partit(prova), escenari)
    comu = {"partit": prova, "font": p.font, "escenari": escenari}
    files = [{**comu, "metode": nom, **avalua.puntua(p, linies_base.prediu(p, finestra, "X"))}
             for nom, finestra in REFERENCIES.items()]
    for lam, d_min in itertools.product(decodifica.GRAELLA_LAMBDA, decodifica.GRAELLA_DMIN):
        pred = decodifica.per_trams(probes[escenari].astype(float), prior, p.trams, lam, d_min)
        files.append({**comu, "metode": "graella", "lam": lam, "d_min": d_min, **avalua.puntua(p, pred)})
    return files


def millor(files: pd.DataFrame) -> tuple[float, int]:
    """La combinació amb més spellF1 de mitjana als escenaris degradats (desempata el macroF1)."""
    tria = files[(files["metode"] == "graella") & files["escenari"].isin(ESCENARIS_ENTRENAMENT)]
    mitjanes = tria.groupby(["lam", "d_min"])[["spell_f1", "macro_f1"]].mean()
    lam, d_min = mitjanes.sort_values(["spell_f1", "macro_f1"], ascending=False).index[0]
    return float(lam), int(d_min)


def tria_sense_mirar(files: pd.DataFrame) -> pd.DataFrame:
    """El mètode A de cada partit: amb la combinació triada amb els altres nou."""
    triats = []
    for prova in files["partit"].unique():
        lam, d_min = millor(files[files["partit"] != prova])
        seu = files[(files["partit"] == prova) & (files["metode"] == "graella")
                    & (files["lam"] == lam) & (files["d_min"] == d_min)]
        triats.append(seu.assign(metode="A"))
    return pd.concat([files[files["metode"] != "graella"], *triats], ignore_index=True)


def interval(diferencies: np.ndarray, grups: np.ndarray, vegades: int = 10_000) -> tuple[float, float]:
    """L'interval del 95 % de la diferència mitjana, tornant a treure partits dins de cada font (bootstrap
    estratificat: sempre 7 de DFL i 3 de Metrica, que no són iguals entre si)."""
    rng = np.random.default_rng(LLAVOR_BOOTSTRAP)
    suma = np.zeros(vegades)
    for grup in np.unique(grups):
        tria = diferencies[grups == grup]
        suma += rng.choice(tria, (vegades, len(tria))).sum(axis=1)
    mitjanes = suma / len(diferencies)
    return float(np.quantile(mitjanes, 0.025)), float(np.quantile(mitjanes, 0.975))


def comparacio(metodes: pd.DataFrame, referencia: str) -> pd.DataFrame:
    """Per escenari: la mitjana d'A i de la referència, la diferència, l'interval i en quants partits guanya A."""
    files = []
    for escenari in degrada.NOMS:
        tria = metodes[metodes["escenari"] == escenari].pivot_table(index="partit", columns="metode",
                                                                   values="spell_f1")
        dif = (tria["A"] - tria[referencia]).to_numpy()
        font = metodes.groupby("partit")["font"].first().loc[tria.index].to_numpy()
        baix, alt = interval(dif, font)
        files.append({"escenari": escenari, "A": tria["A"].mean(), referencia: tria[referencia].mean(),
                      "diferencia": dif.mean(), "baix": baix, "alt": alt, "guanya": int((dif > 0).sum()),
                      "partits": len(dif), "clarament": bool(dif.mean() > SOROLL and baix > 0)})
    return pd.DataFrame(files)


def per_font(metodes: pd.DataFrame, columna: str) -> pd.DataFrame:
    per = metodes.pivot_table(index="metode", columns=["escenari", "font"], values=columna, aggfunc="mean")
    tots = metodes.pivot_table(index="metode", columns="escenari", values=columna, aggfunc="mean")
    tots.columns = pd.MultiIndex.from_tuples([(e, "tots") for e in tots.columns])
    out = pd.concat([per, tots], axis=1)
    columnes = [(e, f) for e in degrada.NOMS for f in ("dfl", "metrica", "tots") if (e, f) in out.columns]
    return out.loc[["A", *REFERENCIES], columnes]


def markdown(files: pd.DataFrame, metodes: pd.DataFrame) -> str:
    linies = ["# Banc obert · el model A", "",
              "Generat amb `uv run python -I -m banc.model_a`. Dades obertes: 7 partits de DFL (IDSSE, CC BY 4.0) i",
              "els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs.", ""]
    for columna, nom in (("spell_f1", "spellF1"), ("macro_f1", "macroF1")):
        t = per_font(metodes, columna)
        capcalera = ["mètode"] + [f"{e} {f}" for e, f in t.columns]
        linies += [f"**{nom}** (mitjana dels partits de cada font)", "",
                   "| " + " | ".join(capcalera) + " |", "|" + "---|" * len(capcalera)]
        linies += ["| " + " | ".join([m] + [f"{v:.3f}" for v in fila]) + " |" for m, fila in t.iterrows()]
        linies.append("")
    for referencia in REFERENCIES:
        c = comparacio(metodes, referencia)
        linies += [f"**A contra {referencia}** (spellF1; «clarament»: la diferència passa de {SOROLL} i l'interval",
                   "del 95 %, triant partits dins de cada font, no toca el zero)", "",
                   "| escenari | A | referència | diferència | interval del 95 % | A guanya | clarament |",
                   "|---|---|---|---|---|---|---|"]
        linies += [f"| {f['escenari']} | {f['A']:.3f} | {f[referencia]:.3f} | {f['diferencia']:+.3f} | "
                   f"{f['baix']:+.3f} a {f['alt']:+.3f} | {f['guanya']} de {f['partits']} | "
                   f"{'sí' if f['clarament'] else 'no'} |" for _, f in c.iterrows()]
        linies.append("")
    a = metodes[metodes["metode"] == "A"]
    lam, d_min = millor(files)
    linies += ["**El decodificador**", "",
               f"- Triat amb cada partit fora: {_triades(a)}.",
               f"- Amb els deu partits (el de la cadena): λ = {lam:g}, durada mínima = {d_min}.",
               "- Possessions predites per cada possessió real, de mitjana: "
               + ", ".join(f"{e} {r:.2f}" for e, r in _rati_possessions(a).items()) + ".", "",
               "*Ni el model ni el decodificador d'un partit no l'han vist. Els models dels altres partits, amb què",
               "es tria el decodificador, sí que l'han tingut a l'entrenament: és l'única drecera, i només toca dos",
               "números (λ i la durada mínima).*", ""]
    return "\n".join(linies)


def _triades(a: pd.DataFrame) -> str:
    compta = a.drop_duplicates("partit").groupby(["lam", "d_min"]).size()
    return "; ".join(f"λ = {lam:g} i durada mínima {int(d)} en {n} partits" for (lam, d), n in compta.items())


def _rati_possessions(a: pd.DataFrame) -> dict[str, float]:
    return {e: float((g["possessions"] / g["possessions_reals"]).mean())
            for e, g in a.groupby("escenari", sort=False)}


def a_json(files: pd.DataFrame, clau_del_codi: str) -> str:
    """JSON vàlid: les caselles buides (la λ de les línies base) hi són null, no NaN."""
    return json.dumps({"clau": clau_del_codi, "files": files.astype(object).where(files.notna(), None).to_dict("records")},
                      indent=1, default=float)


def resultats(cami: Path = DIR_RESULTATS / "model-a.json") -> pd.DataFrame:
    """Les files del banc, si són del codi d'ara; si no, s'atura (cal tornar a fer el banc)."""
    desat = json.loads(cami.read_text())
    if desat.get("clau") != CLAU_RESULTATS:
        raise RuntimeError("Els resultats del banc són d'un altre codi: torna a fer `python -I -m banc.model_a`")
    return pd.DataFrame(desat["files"])


def clau() -> str:
    """El que fa les probabilitats: el codi (també el d'aquest fitxer que entrena), els paràmetres i les versions."""
    h = hashlib.sha256()
    for modul in (senyals, model, degrada, partit, dfl, metrica):
        h.update(Path(modul.__file__).read_bytes())
    for funcio in (mostres_de, probabilitats):
        h.update(inspect.getsource(funcio).encode())
    h.update(repr((model.PAS, ESCENARIS_ENTRENAMENT, fonts.NOMS, lightgbm.__version__, np.__version__,
                   pd.__version__)).encode())
    return h.hexdigest()


def clau_dels_resultats() -> str:
    """El que fa els resultats a partir de les probabilitats: el decodificador, la seva graella, la mètrica i la tria."""
    h = hashlib.sha256(CLAU.encode())
    for modul in (decodifica, decodificacio, avalua, pm):
        h.update(Path(modul.__file__).read_bytes())
    for funcio in (graella, millor):
        h.update(inspect.getsource(funcio).encode())
    return h.hexdigest()


CLAU = clau()          # un sol cop: si el codi canvia mentre corre, el que es desa porta la clau del codi que ho ha fet
CLAU_RESULTATS = clau_dels_resultats()


def main() -> None:
    from banc import model_a      # pel nom del mòdul, perquè els processos fills trobin les funcions

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=2, help="models alhora (cadascun fa servir 8 fils)")
    ap.add_argument("--processos-graella", type=int, default=12)
    args = ap.parse_args()
    fonts.prepara(processos=4)
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        for nom, _ in zip(fonts.NOMS, feina.map(model_a.probabilitats, fonts.NOMS)):
            print(f"· {nom}: model fet", flush=True)
    with ProcessPoolExecutor(max_workers=args.processos_graella) as feina:
        tasques = list(itertools.product(fonts.NOMS, degrada.NOMS))
        files = pd.DataFrame([f for tros in feina.map(model_a.graella, tasques) for f in tros])
    metodes = tria_sense_mirar(files)
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "model-a.json").write_text(a_json(files, CLAU_RESULTATS))
    (DIR_RESULTATS / "model-a.md").write_text(markdown(files, metodes))
    print((DIR_RESULTATS / "model-a.md").read_text())


if __name__ == "__main__":
    main()
