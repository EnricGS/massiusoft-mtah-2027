"""El model d'A girat amb fases (T3am, D-75), entrenat amb els deu partits oberts, com al banc, i desat al repositori.

    cd codi && uv run python -I -m banc.model_final_girat              # el fa i el desa a cadena/model-girat/
    cd codi && uv run python -I -m banc.model_final_girat --comprova   # el torna a fer i mira que surti idèntic

És la C1 del pla «A girat amb fases, a la cadena» (`docs/pla-tocs.md`; D-76). Com `banc/model_final.py` (A xarxes),
amb les peces d'A camp girat (T3ad) i les de la pilota morta i les fases (T3am):
- **el primer classificador i el de canvis** (la q), els d'A xarxes, exactament com a `model_final`;
- **les cinc xarxes del camp girat:** `model_camp_girat.entrena_xarxes`, amb els deu partits als sis escenaris;
- **el segon classificador:** fet amb les probabilitats d'un primer i de cinc xarxes del camp girat que no han vist el
  partit. Els partits es parteixen en els tres grups de `model_final.grups` (4, 3 i 3), i cada grup rep les d'un primer
  i de cinc xarxes entrenats amb els altres (`mostres_del_grup`);
- **el decodificador:** la w, la λ i la durada mínima d'A camp girat amb més spellF1 de mitjana als deu partits, als
  quatre ×¼ i a la veritat de toc, de les files del banc de la T3ad (`decodificador`);
- **la pilota morta i les fases:** el punt que hi trien els deu partits al banc de la T3am. Si no hi trien tots el
  mateix, el més triat; si n'hi ha dos d'empatats, s'atura (`el_de_tots`);
- **les medianes per tipus** de la pilota morta abans de cada represa, dels deu partits a la veritat de toc
  (`medianes`).
Si els resultats de la T3ad o de la T3am són d'un altre codi, s'atura: primer cal tornar a fer el banc.

La fitxa (`cadena/model_girat.py`) porta tot el que cal per aplicar-lo i d'on surt. Les xarxes dels grups i les del
model s'entrenen en paral·lel (`--processos`, 4 per defecte; cadascuna vol uns quants GB de memòria). Tot són dades
obertes. `banc/model_final.py`, `cadena/opcio_a.py` i `cadena/model-a/` no es toquen.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import NamedTuple

import lightgbm as lgb
import numpy as np
import pandas as pd
import sklearn

from banc import decodificador_tocs as t3
from banc import fonts
from banc import model_a_canvis as t3i
from banc import model_a_contacte as t3h
from banc import model_a_partit as mp
from banc import model_a_possessio as t3f
from banc import model_a_xarxes as t3o
from banc import model_camp_girat as mcg
from banc import model_fases as mfs
from banc import model_final as mf
from banc import model_girat_fases as mgf
from banc import model_pilota_morta as mpm
from cadena import model, model_girat, opcio_a, xarxa, xarxes
from cadena import pilota_morta as pmo
from cadena import xarxa_equips as xeq
from cadena import xarxa_girada as xg

RESULTATS_T3AD = mcg.DIR_RESULTATS / "model-camp-girat.json"
RESULTATS_T3AM = mgf.DIR_RESULTATS / "model-girat-fases.json"
ORDRES = {"T3ad": "python -I -m banc.model_camp_girat", "T3am": "python -I -m banc.model_girat_fases"}
Mostres = tuple[pd.DataFrame, np.ndarray]


def _desat(cami: Path, clau: str, banc: str) -> dict:
    desat = json.loads(cami.read_text())
    if desat.get("clau") != clau:
        raise RuntimeError(f"Els resultats del banc de la {banc} són d'un altre codi: torna a fer `{ORDRES[banc]}`")
    return desat


def resultats_t3ad(cami: Path = RESULTATS_T3AD) -> pd.DataFrame:
    """Les files del banc de la T3ad, si són del codi d'ara."""
    return pd.DataFrame(_desat(cami, mcg.clau_dels_resultats(), "T3ad")["files"])


def resultats_t3am(cami: Path = RESULTATS_T3AM) -> dict:
    """El banc de la T3am, si és del codi d'ara."""
    return _desat(cami, mgf.clau_dels_resultats(), "T3am")


def decodificador(files: pd.DataFrame) -> tuple[float, float, int]:
    """La w, la λ i la durada mínima d'A camp girat amb més spellF1 de mitjana als deu partits, als quatre ×¼ i a la
    veritat de toc (desempata el macroF1)."""
    seu = files[(files["metode"] == mcg.A_GIRAT) & (files["veritat"] == mcg.TOC)]
    w, lam, d_min = mp.millor(seu, ["w", "lam", "d_min"], t3.QUARTS)
    return float(w), float(lam), int(d_min)


def el_de_tots(triats: dict[str, dict], graella: tuple[NamedTuple, ...], que: str) -> NamedTuple:
    """El punt que hi trien els partits (cadascun, amb els altres nou), o el més triat. S'atura si no hi són tots els
    partits, si un punt no és a la graella o si n'hi ha dos d'empatats."""
    if sorted(triats) != sorted(fonts.NOMS):
        raise RuntimeError(f"Al banc de la T3am, {que} no hi té el punt de tots els partits")
    tipus = type(graella[0])
    punts = [tipus(**t) for t in triats.values()]
    if any(p not in graella for p in punts):
        raise RuntimeError(f"Al banc de la T3am, un partit tria {que} en un punt que no és a la graella")
    (millor, n), *altres = Counter(punts).most_common()
    if altres and altres[0][1] == n:
        raise RuntimeError(f"Al banc de la T3am, {que} té dos punts empatats: cal decidir-ho abans")
    return next(p for p in graella if p == millor)


def medianes() -> dict[str, float]:
    """Els segons de pilota morta seguida abans de cada tipus de represa, la mediana, dels deu partits."""
    return {t: float(v) for t, v in mpm.medianes_sense().items()}


def mostres_del_grup(grup: tuple[str, ...]) -> dict[tuple[str, str], tuple[Mostres, Mostres]]:
    """Les del segon classificador i les del de canvis de cada partit del grup, als sis escenaris, amb les
    probabilitats d'un primer i de cinc xarxes del camp girat entrenats amb els partits dels altres grups."""
    altres = [nom for nom in fonts.NOMS if nom not in grup]
    primer = t3h.entrena_primer(altres)
    girades, _ = mcg.entrena_xarxes(altres)
    out = {}
    for nom in grup:
        for e in t3o.ENTRENAMENT:
            p = mf.partit_de(nom, e)
            taula = opcio_a.senyals_del_primer(p.tracking, p.trams)
            amb_context = opcio_a.amb_el_context(taula, model.probabilitats(primer, taula), p.trams)
            de_les_xarxes = xg.probabilitats(girades, p.tracking, p.trams)
            segon = opcio_a.senyals_del_segon(amb_context, p.tracking, p.trams, de_les_xarxes)
            out[nom, e] = (t3f.mostres(p, segon), t3i.mostres(p, amb_context))
    return out


def xarxes_del_model() -> tuple[xarxa.Xarxa, ...]:
    """Les cinc xarxes del camp girat, entrenades amb els deu partits."""
    return mcg.entrena_xarxes(list(fonts.NOMS))[0]


def peces(processos: int) -> tuple[dict[tuple[str, str], tuple[Mostres, Mostres]], tuple[xarxa.Xarxa, ...]]:
    """Les mostres dels grups i les xarxes del model, en `processos` processos (1: en aquest)."""
    if processos <= 1:
        dels_grups, xs = [mostres_del_grup(g) for g in mf.grups()], xarxes_del_model()
    else:
        from banc import model_final_girat as aquest             # pel nom del mòdul, perquè els fills el trobin

        with ProcessPoolExecutor(max_workers=processos) as feina:
            del_model = feina.submit(aquest.xarxes_del_model)
            dels_grups, xs = list(feina.map(aquest.mostres_del_grup, mf.grups())), del_model.result()
    return {qui: m for d in dels_grups for qui, m in d.items()}, xs


def fes(decodificador_: tuple[float, float, int], pilota_morta: pmo.Abans, medianes_: dict[str, float],
        fases: mfs.Suma, processos: int = 1) -> tuple[tuple[str, str, str], tuple[xarxa.Xarxa, ...], dict]:
    """Els tres classificadors en text, les cinc xarxes del camp girat i la fitxa (sense la clau del codi ni
    l'empremta, que hi posa `model_girat.completa`)."""
    w, lam, d_min = decodificador_
    x, y = mf.junta([t3h.mostres_primer(nom) for nom in fonts.NOMS])
    primer, columnes_primer = model.entrena(x, y), list(x.columns)
    del x
    mostres, xs = peces(processos)
    ordre = [(nom, e) for nom in fonts.NOMS for e in t3o.ENTRENAMENT]
    x2, y2 = mf.junta([mostres[qui][0] for qui in ordre])
    if not np.array_equal(y, y2):
        raise RuntimeError("Les mostres del segon classificador no són les del primer")       # no hauria de passar
    segon = model.entrena(x2, y2)
    xc, yc = mf.junta([mostres[qui][1] for qui in ordre])
    canvis = lgb.train(t3i.PARAMS, lgb.Dataset(xc, label=yc, free_raw_data=True), num_boost_round=model.RONDES)
    fitxa = {
        "prior": model.prior(y).tolist(), "q_prior": float(yc.mean()), "w": w, "lam": lam, "d_min": d_min,
        "columnes_primer": columnes_primer, "columnes_canvis": list(xc.columns), "columnes_segon": list(x2.columns),
        "pilota_morta": {k: (v if k == "forma" else float(v)) for k, v in pilota_morta._asdict().items()},
        "medianes": medianes_, "fases": {k: float(v) for k, v in fases._asdict().items()},
        "partits": list(fonts.NOMS), "grups": [list(g) for g in mf.grups()], "escenaris": list(t3o.ENTRENAMENT),
        "pas": model.PAS, "minim_per_possessio": t3f.MINIM, "rondes": model.RONDES, "k_canvis": t3i.K,
        "llavors_xarxes": list(xarxes.LLAVORS), "passades_xarxes": xarxa.PASSADES, "entrades_xarxes": xeq.ENTRADES,
        "girades": xg.GIRADES,
        "clau_del_banc": {"T3ad": mcg.clau_dels_resultats(), "T3am": mgf.clau_dels_resultats()},
        "versions": {"lightgbm": lgb.__version__, "numpy": np.__version__, "pandas": pd.__version__,
                     "scikit-learn": sklearn.__version__},
    }
    return (primer.model_to_string(), segon.model_to_string(), canvis.model_to_string()), xs, fitxa


def comprova(carpeta: Path, textos: tuple[str, ...], xs: tuple[xarxa.Xarxa, ...], fitxa: dict) -> int:
    """0 si els classificadors, les xarxes i la fitxa desats són els que surten ara."""
    try:
        desats = tuple((carpeta / nom).read_text(encoding="utf-8") for nom in model_girat.CLASSIFICADORS)
        desades = tuple(xarxa.carrega(carpeta / nom) for nom in model_girat.XARXES)
        desada = json.loads((carpeta / "fitxa.json").read_text(encoding="utf-8"))
    except Exception:              # un fitxer que falta o que no es pot llegir, sigui com sigui: no hi ha cap model
        print(f"✗ No hi ha cap model desat a {carpeta}")
        return 1
    if desats != textos:
        print("✗ Els classificadors refets no són els desats")
        return 1
    if len(desades) != len(xs) or not all(mf.iguals(a, b) for a, b in zip(desades, xs)):
        print("✗ Els classificadors refets són els desats, però les xarxes no")
        return 1
    if desada != model_girat.completa(textos, xs, fitxa):
        print("✗ El model refet és el desat, però la fitxa canvia (el decodificador, la pilota morta, les fases, les "
              "claus o les versions)")
        return 1
    print("✓ El model refet és idèntic al desat, i la fitxa també")
    return 0


def parametres() -> tuple[tuple[float, float, int], pmo.Abans, mfs.Suma]:
    """El decodificador de la T3ad, i la pilota morta i les fases de la T3am."""
    t3am = resultats_t3am()
    return (decodificador(resultats_t3ad()), el_de_tots(t3am["triats_pilota_morta"], pmo.GRAELLA, "la pilota morta"),
            el_de_tots(t3am["triats_fases"], mfs.GRAELLA, "les fases"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--comprova", action="store_true", help="el torna a fer i el compara amb el desat, sense desar res")
    ap.add_argument("--processos", type=int, default=4, help="processos per a les xarxes (cadascun, uns quants GB)")
    args = ap.parse_args(argv)
    try:
        decodificador_, pilota_morta, fases = parametres()
    except (OSError, ValueError, KeyError, TypeError):
        print("✗ Els resultats del banc no hi són o no es poden llegir: fes `"
              + "` i `".join(ORDRES.values()) + "`")
        return 1
    except RuntimeError as error:                          # un text fix: d'un altre codi, o sense un punt clar
        print(f"✗ {error}")
        return 1
    fonts.prepara(processos=4)
    textos, xs, fitxa = fes(decodificador_, pilota_morta, medianes(), fases, args.processos)
    if args.comprova:
        return comprova(model_girat.DIR_MODEL, textos, xs, fitxa)
    desada = model_girat.desa(model_girat.DIR_MODEL, textos, xs, fitxa)
    print(f"✓ Model desat a {model_girat.DIR_MODEL} (empremta {desada['sha256'][:12]}…)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
