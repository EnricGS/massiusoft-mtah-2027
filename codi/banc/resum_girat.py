"""El resum del banc d'A girat amb fases per al document tècnic (C4 del pla «A girat amb fases, a la cadena»,
`docs/pla-tocs.md`; D-76): el model de la cadena contra les línies base i contra A xarxes, a la veritat de toc, i què
hi afegeix cada pas des d'A xarxes.

    cd codi && uv run python -I -m banc.resum_girat [--processos 12]

Tot es puntua a la veritat de toc (D-47, D-48), als onze escenaris dels bancs, amb el Smart Tagging simulat del nivell
mitjà, que és el del criteri, i amb les llavors de provar.

1. **Els passos** (`PASSOS`), cadascun l'anterior amb una idea més, des d'A xarxes amb el decodificador triat a la
   veritat de toc: la mitjana de cada escenari, de la taula del criteri del banc on es va provar (`comparacio`),
   amb el decodificador i els paràmetres de cada partit triats amb els altres nou. A girat amb pilota morta, de les
   files del banc de la T3am. A xarxes ha de ser el mateix a tots els bancs, i les files d'A girat amb fases han de
   donar la seva taula; si no, o si els resultats d'un banc són d'un altre codi, s'atura.
2. **A girat amb fases per nivell del Smart Tagging simulat** (`per_nivell`): bo, mitjà, dolent i cap (sense Smart
   Tagging, que és A camp girat).
3. **La classe més probable de cada imatge** (`a_cada_imatge_de`): la relativa d'A girat amb fases, amb les pilotes
   aturades, les fases i la D impossible, sense decodificar (λ = 0 i durada mínima 1). La decodificada ha de donar la
   fila del banc de la T3am; si no, s'atura.
4. **Les vuit línies base** (`linies_base.prediu`), a cada partit i escenari, a la veritat de toc.
5. **La comparació:** A girat amb fases contra la millor línia base de cada escenari (la de més spellF1 de mitjana) i
   contra smooth50·X, la publicada: la diferència, l'interval del 95 % (`resum.compara`) i en quants partits guanya;
   i contra A xarxes, la del banc de la T3am.

Escriu `resultats/resum-girat.json` (la clau del codi i el resum) i `resultats/resum-girat.md`. Tot són dades obertes.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import itertools
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path
from types import ModuleType

import numpy as np
import pandas as pd

from banc import avalua, degrada, fonts, linies_base
from banc import decodificador_tocs as t3
from banc import fases_simulades as fsm
from banc import model_a_equips as mae
from banc import model_a_partit as mp
from banc import model_a_sense_pilota as msp
from banc import model_camp_girat as mcg
from banc import model_fases as mfs
from banc import model_girat_fases as mgf
from banc import model_neteja_aire as mna
from banc import model_pilota_creible as mpc
from banc import resum as rs
from banc import veritat_toc as vt
from cadena import pilota_morta as pmo
from cadena.model import CLASSES
from possessio.oficial import possession_metrics as pm

NOU, XARXES_TOC, PUBLICADA = mgf.A_GFS, mgf.XARXES_TOC, rs.PUBLICADA
ESCENARIS, NIVELLS, MITJA, PROVA, TOC = mgf.ESCENARIS, mgf.NIVELLS, mgf.MITJA, mgf.PROVA, mgf.TOC
# Cada pas: el mètode i el banc on es va provar. Cada un és l'anterior amb una idea més.
PASSOS = ((msp.A_SENSE, msp), (mae.A_EQUIPS, mae), (mpc.A_CREIBLE, mpc), (mna.A_NETEJA, mna), (mcg.A_GIRAT, mcg),
          (mgf.A_GPM, mgf), (NOU, mgf))
METODES = (XARXES_TOC, *(metode for metode, _ in PASSOS))
FITXERS = {msp: "model-a-sense-pilota.json", mae: "model-a-equips.json", mpc: "model-pilota-creible.json",
           mna: "model-neteja-aire.json", mcg: "model-camp-girat.json", mgf: "model-girat-fases.json"}
DIR_RESULTATS = t3.DIR_RESULTATS
CONTRA = {"millor base": "la millor línia base", "publicada": PUBLICADA, XARXES_TOC: XARXES_TOC}


def moduls() -> tuple[ModuleType, ...]:
    return tuple(dict.fromkeys(modul for _, modul in PASSOS))


def llegeix(modul: ModuleType, cami: Path | None = None) -> dict:
    """Els resultats desats del banc d'un pas, si són del codi d'ara; si no, s'atura (cal tornar a fer el banc)."""
    desat = json.loads((cami or DIR_RESULTATS / FITXERS[modul]).read_text())
    if desat.get("clau") != modul.clau_dels_resultats():
        raise RuntimeError(f"Els resultats del banc són d'un altre codi: torna a fer `python -I -m {modul.__name__}`")
    return desat


def desats_de_tots() -> dict[ModuleType, dict]:
    return {modul: llegeix(modul) for modul in moduls()}


def de_toc(files: pd.DataFrame, metode: str, nivell: str = MITJA) -> pd.DataFrame:
    return files[(files["metode"] == metode) & (files["nivell"] == nivell) & (files["veritat"] == TOC)]


def del_nou(desat: dict) -> pd.DataFrame:
    """Les files d'A girat amb fases de cada partit i escenari, amb el nivell mitjà, a la veritat de toc."""
    return de_toc(pd.DataFrame(desat["files"]), NOU).reset_index(drop=True)


def _mitjanes(files: pd.DataFrame) -> pd.Series:
    return files.groupby("escenari")["spell_f1"].mean().reindex(ESCENARIS)


def passos(desats: dict[ModuleType, dict]) -> pd.DataFrame:
    """L'spellF1 de cada pas a cada escenari (la mitjana dels partits), de la taula del criteri del seu banc."""
    taules = {modul: pd.DataFrame(d["comparacio"]).set_index("escenari").reindex(ESCENARIS)
              for modul, d in desats.items()}
    xarxes = taules[mgf]["contra"]
    if not all(np.allclose(t["contra"], xarxes, atol=1e-12, rtol=0) for t in taules.values()):
        raise RuntimeError(f"{XARXES_TOC} no és el mateix a tots els bancs dels passos")
    files = pd.DataFrame(desats[mgf]["files"])
    if not np.allclose(_mitjanes(de_toc(files, NOU)), taules[mgf]["nou"], atol=1e-12, rtol=0):
        raise RuntimeError(f"Les files de {NOU} no donen la taula del criteri del banc de la T3am")
    columnes = {XARXES_TOC: xarxes, **{metode: taules[modul]["nou"] for metode, modul in PASSOS if modul is not mgf},
                mgf.A_GPM: _mitjanes(de_toc(files, mgf.A_GPM)), NOU: taules[mgf]["nou"]}
    return pd.DataFrame(columnes)[list(METODES)].rename_axis("escenari")


def per_nivell(desat: dict) -> pd.DataFrame:
    """A girat amb fases a cada escenari i nivell del Smart Tagging simulat, a la veritat de toc."""
    files = pd.DataFrame(desat["files"])
    return pd.DataFrame({n: _mitjanes(de_toc(files, NOU, n)) for n in NIVELLS}).rename_axis("escenari")


def linies_base_de(tasca: tuple[str, str]) -> list[dict]:
    """Les vuit línies base en un partit i un escenari, a la veritat de toc."""
    nom, escenari = tasca
    p = replace(mp.degradat(nom, escenari), veritat=vt.veritat(nom))
    comu = {"partit": nom, "font": p.font, "escenari": escenari}
    return [{**comu, "metode": f"{base}·{sense}", **avalua.puntua(p, linies_base.prediu(p, finestra, sense))}
            for sense in linies_base.SENSE_PILOTA for base, finestra in linies_base.FINESTRES.items()]


def a_cada_imatge(relativa: np.ndarray, trams: tuple[tuple[int, int, int], ...]) -> np.ndarray:
    """La classe més probable de cada imatge (la de més log(p / prior)) dins de les parts, i X fora."""
    out = np.full(len(relativa), pm.X, dtype=np.int8)
    for _, inici, fi in trams:
        out[inici:fi + 1] = np.asarray(CLASSES)[np.argmax(relativa[inici:fi + 1], axis=1)]
    return out


def relativa_final(nom: str, escenari: str, a: dict, s: dict) -> tuple:
    """El partit degradat, la relativa d'A girat amb fases, la q i les imatges netejades, com al banc de la T3am: A camp
    girat, amb les pilotes aturades (`a`) i les fases (`s`) simulades del nivell mitjà i les llavors de provar, i la
    D impossible on la neteja ha tret la pilota."""
    de_sempre, r, q_, netejades = mgf.base(mgf.A_GIRAT, nom, escenari)
    relativa = mfs.relativa_pm(nom, escenari, MITJA, PROVA, pmo.Abans(**a), de_sempre, r, netejades)
    final = mfs.relativa_amb(relativa, fsm.fases_de(nom, escenari, MITJA, PROVA), de_sempre.trams, mfs.Suma(**s),
                             netejades)
    return de_sempre, final, q_, netejades


def a_cada_imatge_de(tasca: tuple[str, str, tuple, dict, dict, float]) -> dict:
    """L'spellF1 d'A girat amb fases sense decodificar en un partit i un escenari, amb el decodificador (`triat`), la
    pilota morta (`a`) i les fases (`s`) del partit, com al banc de la T3am. Decodificada, ha de donar `esperat`."""
    nom, escenari, triat, a, s, esperat = tasca
    de_sempre, final, q_, _ = relativa_final(nom, escenari, a, s)
    p = replace(de_sempre, veritat=vt.veritat(nom))
    if avalua.puntua(p, mna.prediccio(final, q_, de_sempre.trams, tuple(triat)))["spell_f1"] != esperat:
        raise RuntimeError(f"{NOU} decodificat no dona la fila del banc de la T3am ({nom}, {escenari})")
    return {"partit": nom, "escenari": escenari, "spell_f1": avalua.puntua(p, a_cada_imatge(final, p.trams))["spell_f1"]}


def resum(metodes: pd.DataFrame, de_passos: pd.DataFrame, crues: dict[str, float],
             contra_xarxes: list[dict]) -> pd.DataFrame:
    """Una fila per escenari: els passos, A girat amb fases sense decodificar (`crues`), la millor línia base, la
    publicada i les comparacions."""
    bases = metodes[metodes["metode"] != NOU]
    xarxes = pd.DataFrame(contra_xarxes).set_index("escenari")
    files = []
    for escenari in ESCENARIS:
        del_escenari = metodes[metodes["escenari"] == escenari]
        mitjanes = del_escenari.groupby("metode")[["spell_f1", "macro_f1"]].mean()
        de_bases = mitjanes.loc[mitjanes.index.isin(bases["metode"])]
        millor = de_bases.sort_values(["spell_f1", "macro_f1"], ascending=False).index[0]
        nostre = del_escenari[del_escenari["metode"] == NOU]
        per_font = nostre.groupby("font")["spell_f1"].mean()
        x = xarxes.loc[escenari]
        files.append({
            "escenari": escenari,
            **{f"spell {m}": float(de_passos.loc[escenari, m]) for m in METODES},
            "macro": float(mitjanes.loc[NOU, "macro_f1"]), "spell sense decodificar": crues[escenari],
            **{f"spell {font}": float(per_font.get(font, float("nan"))) for font in ("dfl", "metrica")},
            "possessions per real": float((nostre["possessions"] / nostre["possessions_reals"]).mean()),
            "millor base": millor, "spell millor base": float(de_bases.loc[millor, "spell_f1"]),
            "spell publicada": float(mitjanes.loc[PUBLICADA, "spell_f1"]),
            **{f"{k} {quina}": v for quina, qui in (("millor base", millor), ("publicada", PUBLICADA))
               for k, v in rs.compara(metodes, escenari, NOU, qui).items()},
            **{f"{k} {XARXES_TOC}": (int(x[k]) if k in ("guanya", "partits") else float(x[k]))
               for k in ("diferencia", "baix", "alt", "guanya", "partits")},
        })
    return pd.DataFrame(files)



def compta(valors: list[str]) -> str:
    return "; ".join(f"{v} en {n} partits" for v, n in collections.Counter(valors).most_common())


def _triat(parametres: dict) -> str:
    return ", ".join(f"{k} = {v:g}" if isinstance(v, float) else f"{k} = {v}" for k, v in parametres.items())


def markdown(r: pd.DataFrame, nivells: pd.DataFrame, triats: dict) -> str:
    linies = ["# Banc obert · el resum d'A girat amb fases per al document tècnic", "",
              "Generat amb `uv run python -I -m banc.resum_girat`. Dades obertes: 7 partits de DFL (IDSSE, CC BY 4.0) i",
              "els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Es puntua a la veritat de",
              "toc, amb el Smart Tagging simulat del nivell mitjà. Com es fa: la capçalera de `banc/resum_girat.py`.", "",
              f"**{NOU}** és el model de la cadena. Els passos, des d'{XARXES_TOC}, són cadascun l'anterior amb una",
              "idea més, amb la taula del banc on es va provar. Cada un, amb el decodificador i els paràmetres de cada",
              "partit triats amb els altres nou.", "",
              "## spellF1 de cada pas (mitjana dels deu partits)", "",
              f"| escenari | {' | '.join(METODES)} |", "|---|" + "---|" * len(METODES)]
    linies += [f"| {f['escenari']} | " + " | ".join(f"{f[f'spell {m}']:.3f}" for m in METODES) + " |"
               for _, f in r.iterrows()]
    linies += ["", f"## {NOU}, sense decodificar, i les línies base (spellF1)", "",
               f"| escenari | {NOU} | sense decodificar | millor línia base | {PUBLICADA} | macroF1, {NOU} |",
               "|---|---|---|---|---|---|"]
    linies += [f"| {f['escenari']} | {f[f'spell {NOU}']:.3f} | {f['spell sense decodificar']:.3f} | "
               f"{f['spell millor base']:.3f} ({f['millor base']}) | {f['spell publicada']:.3f} | {f['macro']:.3f} |"
               for _, f in r.iterrows()]
    linies += ["", "*Sense decodificar: la classe més probable de cada imatge, amb el Smart Tagging i la D impossible",
               "(λ = 0 i durada mínima 1).*"]
    for quina, nom in CONTRA.items():
        linies += ["", f"## {NOU} contra {nom} (spellF1)", "",
                   "| escenari | diferència | interval del 95 % | guanya |", "|---|---|---|---|"]
        linies += [f"| {f['escenari']} | {f[f'diferencia {quina}']:+.3f} | {f[f'baix {quina}']:+.3f} a "
                   f"{f[f'alt {quina}']:+.3f} | {f[f'guanya {quina}']} de {f[f'partits {quina}']} |"
                   for _, f in r.iterrows()]
    linies += ["", "## Per nivell del Smart Tagging simulat (spellF1)", "",
               "*cap: sense Smart Tagging, que és A camp girat.*", "",
               f"| escenari | {' | '.join(NIVELLS)} |", "|---|" + "---|" * len(NIVELLS)]
    linies += [f"| {e} | " + " | ".join(f"{f[n]:.3f}" for n in NIVELLS) + " |" for e, f in nivells.iterrows()]
    linies += ["", f"## {NOU}, per font, i les possessions", "",
               "| escenari | spellF1 DFL | spellF1 Metrica | possessions predites per cada real |", "|---|---|---|---|"]
    linies += [f"| {f['escenari']} | {f['spell dfl']:.3f} | {f['spell metrica']:.3f} | {f['possessions per real']:.2f} |"
               for _, f in r.iterrows()]
    linies += ["", "**El decodificador triat amb cada partit fora:** "
               + compta([rs.triat(tuple(t)) for t in triats["decodificador"].values()]) + ".",
               "", "**La pilota morta:** " + compta([_triat(a) for a in triats["pilota_morta"].values()]) + ".",
               "", "**Les fases:** " + compta([_triat(s) for s in triats["fases"].values()]) + ".", ""]
    return "\n".join(linies)


def clau() -> str:
    """Els resultats de cada pas i el codi de les línies base i d'aquí: si canvien, el resum s'ha de tornar a fer."""
    h = hashlib.sha256("".join(modul.clau_dels_resultats() for modul in moduls()).encode())
    for modul in (linies_base, avalua, degrada, mp):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    from banc import resum_girat as aquest               # pel nom del mòdul, perquè els processos fills el trobin

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=12)
    args = ap.parse_args(argv)
    try:
        desats = desats_de_tots()
        de_passos = passos(desats)
    except (OSError, ValueError, KeyError):
        print("✗ Els resultats d'algun banc dels passos no hi són o no es poden llegir")
        return 1
    except RuntimeError as error:                          # un text fix
        print(f"✗ {error}")
        return 1
    t3am = desats[mgf]
    nous = del_nou(t3am)
    triats = {"decodificador": t3am["triades"][mgf.A_GIRAT], "pilota_morta": t3am["triats_pilota_morta"],
              "fases": t3am["triats_fases"]}
    esperats = nous.set_index(["partit", "escenari"])["spell_f1"]
    tasques = list(itertools.product(fonts.NOMS, ESCENARIS))
    fonts.prepara(processos=4)
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        bases = pd.DataFrame([f for tros in feina.map(aquest.linies_base_de, tasques) for f in tros])
        crues = pd.DataFrame(list(feina.map(aquest.a_cada_imatge_de, [
            (nom, e, triats["decodificador"][nom], triats["pilota_morta"][nom], triats["fases"][nom],
             esperats.loc[(nom, e)]) for nom, e in tasques])))
    r = resum(pd.concat([nous, bases], ignore_index=True), de_passos, rs.sense_decodificar(crues),
              t3am["comparacio"])
    nivells = per_nivell(t3am)
    desa = {"clau": clau(), "resum": t3.registres(r), "per_nivell": t3.registres(nivells.reset_index()),
            "triats": triats}
    (DIR_RESULTATS / "resum-girat.json").write_text(json.dumps(desa, indent=1, default=float, allow_nan=False))
    (DIR_RESULTATS / "resum-girat.md").write_text(markdown(r, nivells, triats))
    print((DIR_RESULTATS / "resum-girat.md").read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
