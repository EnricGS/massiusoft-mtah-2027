"""El resum del banc per al document tècnic (T6 del pla per tocs): el model de la cadena contra les línies base, als
deu escenaris de la T3, i què hi afegeix cada pas.

    cd codi && uv run python -I -m banc.resum [--processos 12]

1. **A xarxes** (T3o, `model_a_xarxes.py`, D-43), el model de la cadena, i els passos que l'han fet (`PASSOS`), de
   la T3c a la T3o. Les files de cada pas són les del banc on es va provar (`resultats`), amb el decodificador de cada
   partit triat amb els altres nou com allà (el `tria_sense_mirar` de cada mòdul). Si les d'un banc són d'un altre
   codi, s'atura.
2. **A xarxes sense decodificar** (`sense_decodificar_de`): la classe més probable de cada imatge després de dividir
   pel prior, amb les probabilitats de la memòria cau de la T3o.
3. **Les vuit línies base** (`linies_base.prediu`), a cada partit i escenari: el banc de les línies base
   (`python -m banc`) només té el net i els tres primers escenaris amb l'error ×1.
4. **La comparació:** A xarxes contra la millor línia base de cada escenari (la de més spellF1 de mitjana), contra
   smooth50·X, la publicada, i contra dos passos (`CONTRA`): A context, el model de la cadena fins a la T3o, i
   A ×1+×¼, un sol classificador. La diferència, l'interval del 95 % (`model_a.interval`) i en quants partits guanya.

Escriu `resultats/resum.json` (la clau del codi i el resum) i `resultats/resum.md`. Tot són dades obertes.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from types import ModuleType

import pandas as pd

from banc import avalua, degrada, fonts, linies_base, model_a
from banc import decodificador_tocs as t3
from banc import model_a_aturades as t3k
from banc import model_a_canvis as t3i
from banc import model_a_contacte as t3h
from banc import model_a_context as t3e
from banc import model_a_control as t3d
from banc import model_a_dos_errors as t3c
from banc import model_a_possessio as t3f
from banc import model_a_xarxa as t3m
from banc import model_a_xarxes as t3o
from cadena import decodifica, regla

PUBLICADA = "smooth50·X"
NOU = t3o.XARXES
# Cada pas: el mètode i el banc on es va provar. Cada un és l'anterior amb una idea més.
PASSOS = ((t3c.DOS, t3e), (t3d.CONTROL, t3e), (t3e.CONTEXT, t3e), (t3f.POSSESSIO, t3f), (t3h.CONTACTE, t3h),
          (t3i.CANVIS, t3i), (t3k.ATURADES, t3k), (t3m.XARXA, t3m), (NOU, t3o))
CLASSIFICADORS = tuple(metode for metode, _ in PASSOS)
CONTRA = (t3e.CONTEXT, t3c.DOS)
FITXERS = {t3e: "model-a-context.json", t3f: "model-a-possessio.json", t3h: "model-a-contacte.json",
           t3i: "model-a-canvis.json", t3k: "model-a-aturades.json", t3m: "model-a-xarxa.json",
           t3o: "model-a-xarxes.json"}
ORDRES = {t3e: "python -I -m banc.model_a_context", t3f: "python -I -m banc.model_a_possessio",
          t3h: "python -I -m banc.model_a_contacte", t3i: "python -I -m banc.model_a_canvis",
          t3k: "python -I -m banc.model_a_aturades", t3m: "python -I -m banc.model_a_xarxa",
          t3o: "python -I -m banc.model_a_xarxes"}
DIR_RESULTATS = t3.DIR_RESULTATS


def moduls() -> tuple[ModuleType, ...]:
    """Els bancs dels passos, sense repetir i per ordre."""
    return tuple(dict.fromkeys(modul for _, modul in PASSOS))


def llegeix(modul: ModuleType, cami: Path | None = None) -> pd.DataFrame:
    """Les files del banc d'un pas, si són del codi d'ara; si no, s'atura (cal tornar a fer el banc)."""
    desat = json.loads((cami or DIR_RESULTATS / FITXERS[modul]).read_text())
    if desat.get("clau") != modul.clau_dels_resultats():
        raise RuntimeError(f"Els resultats del banc són d'un altre codi: torna a fer `{ORDRES[modul]}`")
    return pd.DataFrame(desat["files"])


def resultats() -> tuple[pd.DataFrame, dict[str, dict]]:
    """Les files de cada pas a cada partit, amb el decodificador triat amb els altres nou, del banc on es va provar, i
    les triades. Les files d'un pas que surt a més d'un banc (A context hi és a tots) són les del seu."""
    triats, triades = [], {nom: {} for nom in fonts.NOMS}
    for modul in moduls():
        del_banc, del_banc_triades = modul.tria_sense_mirar(llegeix(modul))
        seus = [metode for metode, de in PASSOS if de is modul]
        triats.append(del_banc[del_banc["metode"].isin(seus)])
        for nom in fonts.NOMS:
            triades[nom] |= {metode: del_banc_triades[nom][metode] for metode in seus}
    return pd.concat(triats, ignore_index=True), triades


def linies_base_de(tasca: tuple[str, str]) -> list[dict]:
    """Les vuit línies base en un partit i un escenari."""
    nom, escenari = tasca
    p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[escenari])
    comu = {"partit": nom, "font": p.font, "escenari": escenari}
    return [{**comu, "metode": f"{base}·{sense}", **avalua.puntua(p, linies_base.prediu(p, finestra, sense))}
            for sense in linies_base.SENSE_PILOTA for base, finestra in linies_base.FINESTRES.items()]


def sense_decodificar_de(tasca: tuple[str, str]) -> dict:
    """L'spellF1 d'A xarxes sense decodificador en un partit i un escenari: la classe més probable de cada imatge
    després de dividir pel prior (λ = 0 i durada mínima 1)."""
    nom, escenari = tasca
    p = degrada.aplica(fonts.partit(nom), t3.ESCENARIS[escenari])
    probes, prior = t3o.probabilitats(nom, entrena=False)
    pred = decodifica.per_trams(probes[escenari].astype(float), prior, p.trams, 0.0, 1)
    return {"partit": nom, "escenari": escenari, "spell_f1": avalua.puntua(p, pred)["spell_f1"]}


def sense_decodificar(files: pd.DataFrame) -> dict[str, float]:
    """La mitjana dels partits a cada escenari."""
    return {e: float(g["spell_f1"].mean()) for e, g in files.groupby("escenari")}


def compara(metodes: pd.DataFrame, escenari: str, nou: str, contra: str) -> dict:
    """`nou` contra `contra` en un escenari: la diferència d'spellF1, l'interval i en quants partits guanya."""
    tria = metodes[metodes["escenari"] == escenari].pivot_table(index="partit", columns="metode", values="spell_f1")
    dif = (tria[nou] - tria[contra]).to_numpy()
    font = metodes.groupby("partit")["font"].first().loc[tria.index].to_numpy()
    baix, alt = model_a.interval(dif, font)
    return {"diferencia": float(dif.mean()), "baix": baix, "alt": alt, "guanya": int((dif > 0).sum()),
            "partits": len(dif)}


def resum(metodes: pd.DataFrame, crues: dict[str, float]) -> pd.DataFrame:
    """Una fila per escenari: els passos, A xarxes sense decodificar (`crues`), la millor línia base, la publicada i
    les comparacions."""
    bases = metodes[~metodes["metode"].isin(CLASSIFICADORS)]
    files = []
    for escenari in t3.ESCENARIS:
        del_escenari = metodes[metodes["escenari"] == escenari]
        mitjanes = del_escenari.groupby("metode")[["spell_f1", "macro_f1"]].mean()
        de_bases = mitjanes.loc[mitjanes.index.isin(bases["metode"])]
        millor = de_bases.sort_values(["spell_f1", "macro_f1"], ascending=False).index[0]
        nostre = del_escenari[del_escenari["metode"] == NOU]
        per_font = nostre.groupby("font")["spell_f1"].mean()
        contra = {"millor base": millor, "publicada": PUBLICADA} | {m: m for m in CONTRA}
        files.append({
            "escenari": escenari,
            **{f"spell {m}": float(mitjanes.loc[m, "spell_f1"]) for m in CLASSIFICADORS},
            "macro": float(mitjanes.loc[NOU, "macro_f1"]), "spell sense decodificar": crues[escenari],
            **{f"spell {font}": float(per_font.get(font, float("nan"))) for font in ("dfl", "metrica")},
            "possessions per real": float((nostre["possessions"] / nostre["possessions_reals"]).mean()),
            "millor base": millor, "spell millor base": float(de_bases.loc[millor, "spell_f1"]),
            "spell publicada": float(mitjanes.loc[PUBLICADA, "spell_f1"]),
            **{f"{k} {quina}": v for quina, qui in contra.items()
               for k, v in compara(metodes, escenari, NOU, qui).items()},
        })
    return pd.DataFrame(files)


def triat(parametres: tuple) -> str:
    """El decodificador triat, en paraules: w, λ i la durada mínima, o només λ i la durada mínima."""
    *w, lam, d_min = parametres
    return ", ".join([*(f"w = {v:g}" for v in w), f"λ = {lam:g}"]) + f" i durada mínima {d_min}"


def markdown(r: pd.DataFrame, triades: dict) -> str:
    linies = ["# Banc obert · el resum per al document tècnic", "",
              "Generat amb `uv run python -I -m banc.resum`. Dades obertes: 7 partits de DFL (IDSSE, CC BY 4.0) i",
              "els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa: la capçalera",
              "de `banc/resum.py`.", "",
              f"**{NOU}** és el model de la cadena. Els passos, de la T3c a la T3o, són cadascun l'anterior amb una",
              "idea més, amb les files del banc on es va provar. Cada un, amb el decodificador triat amb els altres",
              "nou partits als escenaris ×¼.", "",
              "## spellF1 de cada pas (mitjana dels deu partits)", "",
              f"| escenari | {' | '.join(CLASSIFICADORS)} |", "|---|" + "---|" * len(CLASSIFICADORS)]
    linies += [f"| {f['escenari']} | " + " | ".join(f"{f[f'spell {m}']:.3f}" for m in CLASSIFICADORS) + " |"
               for _, f in r.iterrows()]
    linies += ["", f"## {NOU}, sense decodificar, i les línies base (spellF1)", "",
               f"| escenari | {NOU} | sense decodificar | millor línia base | {PUBLICADA} | macroF1, {NOU} |",
               "|---|---|---|---|---|---|"]
    linies += [f"| {f['escenari']} | {f[f'spell {NOU}']:.3f} | {f['spell sense decodificar']:.3f} | "
               f"{f['spell millor base']:.3f} ({f['millor base']}) | {f['spell publicada']:.3f} | {f['macro']:.3f} |"
               for _, f in r.iterrows()]
    linies += ["", "*Sense decodificar: la classe més probable de cada imatge després de dividir pel prior (λ = 0 i",
               "durada mínima 1).*"]
    for quina, nom in (("millor base", "la millor línia base"), ("publicada", PUBLICADA),
                       *((m, m) for m in CONTRA)):
        linies += ["", f"## {NOU} contra {nom} (spellF1)", "",
                   "| escenari | diferència | interval del 95 % | guanya |", "|---|---|---|---|"]
        linies += [f"| {f['escenari']} | {f[f'diferencia {quina}']:+.3f} | {f[f'baix {quina}']:+.3f} a "
                   f"{f[f'alt {quina}']:+.3f} | {f[f'guanya {quina}']} de {f[f'partits {quina}']} |"
                   for _, f in r.iterrows()]
    compta = pd.Series([t[NOU] for t in triades.values()]).value_counts()
    linies += ["", f"## {NOU}, per font, i les possessions", "",
               "| escenari | spellF1 DFL | spellF1 Metrica | possessions predites per cada real |", "|---|---|---|---|"]
    linies += [f"| {f['escenari']} | {f['spell dfl']:.3f} | {f['spell metrica']:.3f} | {f['possessions per real']:.2f} |"
               for _, f in r.iterrows()]
    linies += ["", "**El decodificador triat amb cada partit fora:** "
               + "; ".join(f"{triat(p)} en {n} partits" for p, n in compta.items()) + ".", ""]
    return "\n".join(linies)


def clau() -> str:
    """Els resultats de cada pas i el codi de les línies base i d'aquí: si canvien, el resum s'ha de tornar a fer."""
    h = hashlib.sha256("".join(modul.clau_dels_resultats() for modul in moduls()).encode())
    for modul in (linies_base, regla, avalua, degrada, decodifica):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    from banc import resum as aquest                     # pel nom del mòdul, perquè els processos fills el trobin

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    args = ap.parse_args(argv)
    try:
        triats, triades = resultats()
    except (OSError, ValueError, KeyError):
        print("✗ Els resultats d'algun banc dels passos no hi són o no es poden llegir")
        return 1
    except RuntimeError as error:                          # un text fix: són d'un altre codi
        print(f"✗ {error}")
        return 1
    fonts.prepara(processos=4)
    tasques = list(itertools.product(fonts.NOMS, t3.ESCENARIS))
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        bases = pd.DataFrame([f for tros in feina.map(aquest.linies_base_de, tasques) for f in tros])
        crues = pd.DataFrame(list(feina.map(aquest.sense_decodificar_de, tasques)))
    r = resum(pd.concat([triats, bases], ignore_index=True), sense_decodificar(crues))
    DIR_RESULTATS.mkdir(exist_ok=True)
    desa = {"clau": clau(), "resum": t3.registres(r), "triades": triades}
    (DIR_RESULTATS / "resum.json").write_text(json.dumps(desa, indent=1, default=float, allow_nan=False))
    (DIR_RESULTATS / "resum.md").write_text(markdown(r, triades))
    print((DIR_RESULTATS / "resum.md").read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
