"""El model de la cadena: A xarxes (T3o, D-43), entrenat amb els deu partits oberts, com al banc, i desat al repositori.

    cd codi && uv run python -I -m banc.model_final              # el fa i el desa a cadena/model-a/
    cd codi && uv run python -I -m banc.model_final --comprova   # el torna a fer i mira que surti idèntic

- **El mateix que A xarxes al banc (T3o), però amb els deu partits.** Les peces de `cadena/opcio_a.py`:
  - **el primer classificador** (T3h): les mostres de `model_a_contacte.mostres_primer` (curts, llargs i barreja amb
    l'error de posició ×1 i amb el ×¼, amb la tria de la T3f, amb els senyals d'A, del control i del contacte) i
    `model.entrena`;
  - **les cinc xarxes** (T3o): `model_a_xarxes.entrena_xarxes`, amb els mateixos partits i escenaris;
  - **el segon classificador** (T3o) i **el de canvis** (T3i): fets amb les probabilitats d'un primer i de cinc
    xarxes que no han vist el partit. Com al banc, els partits es parteixen en tres grups (`grups`; aquí, els deu,
    de 4, 3 i 3), i cada grup rep les d'un primer i de cinc xarxes entrenats amb els altres (`mostres_del_grup`). Les mostres del segon, amb la tria de
    la T3f; les del de canvis, com a la T3i (`model_a_canvis.mostres`). Els senyals, els de la cadena: un test mira
    que són els del banc.
- **El decodificador:** la w, la λ i la durada mínima que trien els deu partits al banc de la T3o, als escenaris ×¼
  (`millor`), dels resultats del codi d'ara. Si els resultats són d'un altre codi, s'atura: primer cal tornar a fer
  el banc.
- **La fitxa** (`fitxa.json`) porta el prior, la q de les imatges sense tracking, el decodificador, les columnes dels
  senyals de cada classificador, d'on surt tot plegat, la clau del codi de la cadena i una empremta que cobreix els
  tres classificadors, les cinc xarxes i la fitxa. La cadena no fa servir un model que no quadri amb la seva fitxa o
  amb el seu codi.

Les xarxes dels grups i les del model s'entrenen en paral·lel (`--processos`, 4 per defecte; cadascuna vol uns
quants GB de memòria). Regenerar el fitxer del concurs, doncs, només vol dir aplicar aquest model: no cal baixar les
dades obertes. Qui en vulgui refer el model, les baixa (`banc/baixa_idsse.py`) i fa `--comprova`.
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import sklearn

from banc import decodificador_tocs as t3
from banc import degrada, fonts
from banc import model_a_canvis as t3i
from banc import model_a_contacte as t3h
from banc import model_a_context as t3e
from banc import model_a_possessio as t3f
from banc import model_a_xarxes as t3o
from banc.partit import PartitBanc
from cadena import model, opcio_a, xarxa, xarxes

RESULTATS = t3o.DIR_RESULTATS / "model-a-xarxes.json"
ORDRE_DEL_BANC = "python -I -m banc.model_a_xarxes"


def resultats(cami: Path = RESULTATS) -> pd.DataFrame:
    """Les files del banc de la T3o, si són del codi d'ara; si no, s'atura (cal tornar a fer el banc)."""
    desat = json.loads(cami.read_text())
    if desat.get("clau") != t3o.clau_dels_resultats():
        raise RuntimeError(f"Els resultats del banc són d'un altre codi: torna a fer `{ORDRE_DEL_BANC}`")
    return pd.DataFrame(desat["files"])


def millor(files: pd.DataFrame) -> tuple[float, float, int]:
    """La w, la λ i la durada mínima d'A xarxes amb més spellF1 de mitjana als deu partits, als escenaris ×¼
    (desempata el macroF1)."""
    w, lam, d_min = t3.millor(files[files["metode"] == t3o.XARXES], ["w", "lam", "d_min"])
    return float(w), float(lam), int(d_min)


def grups() -> tuple[tuple[str, ...], ...]:
    """Els deu partits en tres grups, sempre els mateixos (per l'ordre dels noms), com al banc."""
    return tuple(g for g in (tuple(fonts.NOMS[i::t3e.GRUPS]) for i in range(t3e.GRUPS)) if g)


def partit_de(nom: str, escenari: str) -> PartitBanc:
    return degrada.aplica(fonts.partit(nom), t3.ESCENARIS[escenari])


def junta(mostres: list[tuple[pd.DataFrame, np.ndarray]]) -> tuple[pd.DataFrame, np.ndarray]:
    return pd.concat([m[0] for m in mostres], ignore_index=True), np.concatenate([m[1] for m in mostres])


Mostres = tuple[pd.DataFrame, np.ndarray]


def mostres_del_grup(grup: tuple[str, ...]) -> dict[tuple[str, str], tuple[Mostres, Mostres]]:
    """Les del segon classificador i les del de canvis de cada partit del grup, als sis escenaris, amb les
    probabilitats d'un primer i de cinc xarxes entrenats amb els partits dels altres grups."""
    altres = [nom for nom in fonts.NOMS if nom not in grup]
    primer = t3h.entrena_primer(altres)
    entrenades, _ = t3o.entrena_xarxes(altres)
    out = {}
    for nom in grup:
        for e in t3o.ENTRENAMENT:
            p = partit_de(nom, e)
            taula = opcio_a.senyals_del_primer(p.tracking, p.trams)
            amb_context = opcio_a.amb_el_context(taula, model.probabilitats(primer, taula), p.trams)
            de_les_xarxes = xarxes.probabilitats(entrenades, p.tracking, p.trams)
            segon = opcio_a.senyals_del_segon(amb_context, p.tracking, p.trams, de_les_xarxes)
            out[nom, e] = (t3f.mostres(p, segon), t3i.mostres(p, amb_context))
    return out


def xarxes_del_model() -> tuple[xarxa.Xarxa, ...]:
    """Les cinc xarxes de la cadena, entrenades amb els deu partits."""
    return t3o.entrena_xarxes(list(fonts.NOMS))[0]


def peces(processos: int) -> tuple[dict[tuple[str, str], tuple[Mostres, Mostres]], tuple[xarxa.Xarxa, ...]]:
    """Les mostres dels grups i les xarxes del model, en `processos` processos (1: en aquest)."""
    if processos <= 1:
        dels_grups, xs = [mostres_del_grup(g) for g in grups()], xarxes_del_model()
    else:
        with ProcessPoolExecutor(max_workers=processos) as feina:
            del_model = feina.submit(xarxes_del_model)
            dels_grups, xs = list(feina.map(mostres_del_grup, grups())), del_model.result()
    return {qui: m for d in dels_grups for qui, m in d.items()}, xs


def fes(decodificador: tuple[float, float, int],
        processos: int = 1) -> tuple[tuple[str, str, str], tuple[xarxa.Xarxa, ...], dict]:
    """Els tres classificadors en text, les cinc xarxes i la fitxa (sense la clau del codi ni l'empremta, que hi
    posa `opcio_a.completa`), amb el decodificador `(w, λ, durada mínima)` de `millor`."""
    w, lam, d_min = decodificador
    x, y = junta([t3h.mostres_primer(nom) for nom in fonts.NOMS])
    primer, columnes_primer = model.entrena(x, y), list(x.columns)
    del x
    mostres, xs = peces(processos)
    ordre = [(nom, e) for nom in fonts.NOMS for e in t3o.ENTRENAMENT]
    x2, y2 = junta([mostres[qui][0] for qui in ordre])
    if not np.array_equal(y, y2):
        raise RuntimeError("Les mostres del segon classificador no són les del primer")       # no hauria de passar
    segon = model.entrena(x2, y2)
    xc, yc = junta([mostres[qui][1] for qui in ordre])
    canvis = lgb.train(t3i.PARAMS, lgb.Dataset(xc, label=yc, free_raw_data=True), num_boost_round=model.RONDES)
    fitxa = {
        "prior": model.prior(y).tolist(), "q_prior": float(yc.mean()), "w": w, "lam": lam, "d_min": d_min,
        "columnes_primer": columnes_primer, "columnes_canvis": list(xc.columns), "columnes_segon": list(x2.columns),
        "partits": list(fonts.NOMS), "grups": [list(g) for g in grups()], "escenaris": list(t3o.ENTRENAMENT),
        "pas": model.PAS, "minim_per_possessio": t3f.MINIM, "rondes": model.RONDES, "k_canvis": t3i.K,
        "llavors_xarxes": list(xarxes.LLAVORS), "passades_xarxes": xarxa.PASSADES,
        "clau_del_banc": t3o.clau_dels_resultats(),
        "versions": {"lightgbm": lgb.__version__, "numpy": np.__version__, "pandas": pd.__version__,
                     "scikit-learn": sklearn.__version__},
    }
    return (primer.model_to_string(), segon.model_to_string(), canvis.model_to_string()), xs, fitxa


def iguals(a: xarxa.Xarxa, b: xarxa.Xarxa) -> bool:
    """Les mateixes matrius, amb el mateix tipus, la mateixa forma i els mateixos valors."""
    de_a, de_b = (a.mitjana, a.escala, *a.pesos, *a.biaixos), (b.mitjana, b.escala, *b.pesos, *b.biaixos)
    return len(de_a) == len(de_b) and all(u.dtype == v.dtype and np.array_equal(u, v) for u, v in zip(de_a, de_b))


def comprova(carpeta: Path, textos: tuple[str, ...], xs: tuple[xarxa.Xarxa, ...], fitxa: dict) -> int:
    """0 si els classificadors, les xarxes i la fitxa desats són els que surten ara."""
    try:
        desats = tuple((carpeta / nom).read_text(encoding="utf-8") for nom in opcio_a.CLASSIFICADORS)
        desades = tuple(xarxa.carrega(carpeta / nom) for nom in opcio_a.XARXES)
        desada = json.loads((carpeta / "fitxa.json").read_text(encoding="utf-8"))
    except Exception:              # un fitxer que falta o que no es pot llegir, sigui com sigui: no hi ha cap model
        print(f"✗ No hi ha cap model desat a {carpeta}")
        return 1
    if desats != textos:
        print("✗ Els classificadors refets no són els desats")
        return 1
    if len(desades) != len(xs) or not all(iguals(a, b) for a, b in zip(desades, xs)):
        print("✗ Els classificadors refets són els desats, però les xarxes no")
        return 1
    if desada != opcio_a.completa(textos, xs, fitxa):
        print("✗ El model refet és el desat, però la fitxa canvia (el decodificador, les claus o les versions)")
        return 1
    print("✓ El model refet és idèntic al desat, i la fitxa també")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--comprova", action="store_true", help="el torna a fer i el compara amb el desat, sense desar res")
    ap.add_argument("--processos", type=int, default=4, help="processos per a les xarxes (cadascun, uns quants GB)")
    args = ap.parse_args(argv)
    try:
        decodificador = millor(resultats())
    except (OSError, ValueError):
        print(f"✗ Els resultats del banc no hi són o no es poden llegir: fes `{ORDRE_DEL_BANC}`")
        return 1
    except RuntimeError as error:                          # un text fix: són d'un altre codi
        print(f"✗ {error}")
        return 1
    fonts.prepara(processos=4)
    textos, xs, fitxa = fes(decodificador, args.processos)
    if args.comprova:
        return comprova(opcio_a.DIR_MODEL, textos, xs, fitxa)
    desada = opcio_a.desa(opcio_a.DIR_MODEL, textos, xs, fitxa)
    print(f"✓ Model desat a {opcio_a.DIR_MODEL} (empremta {desada['sha256'][:12]}…)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
