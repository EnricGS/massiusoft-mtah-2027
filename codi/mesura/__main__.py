"""Mesura a l'ATD del partit el que el banc suposa, i diu a quin candidat s'assembla (`docs/pla-mesura-atd.md`).
L'executa l'Enric, en local.

    cd codi && uv run python -I -m mesura --dades "<carpeta de les dades>"

Llegeix l'ATD tàctic com la cadena, en calcula les mesures a les imatges puntuades i les compara amb les referències
del banc (`banc/resultats/mesura-atd.json`, fetes amb dades obertes per `python -I -m banc.mesura_atd`). A la consola
surt el candidat de cada cosa, en paraules, i si el partit hi encaixa: cap xifra. Les xifres van a l'informe, dins del
volum xifrat.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

from cadena import llegeix, senyals
from cadena.norma import EQUIP_CASA, N_FOTOGRAMES, TRAMS_PUNTUATS
from cadena.volum import VOLUM, dins_de, dins_del_volum, temporals_dins
from mesura import estadistiques as est
from mesura import tria as tr

REFERENCIES = Path(__file__).resolve().parents[1] / "banc" / "resultats" / "mesura-atd.json"
INICI_SEGONA = 113_742         # FAQ.md: la segona part es puntua abans del xiulet, i aquestes imatges són totes D
TRAMS_DE_JOC = ((1, *TRAMS_PUNTUATS[0][1:]), (2, INICI_SEGONA, TRAMS_PUNTUATS[1][2]))   # com els partits oberts
CARPETA = VOLUM / "mesura"
ARA_AL_BANC = {"forats": "barreja", "morta": 0.41, "viva": 0.41, "aire": 3.0, "aglomeracio": 3.0, "perdua": "0.5-10"}

QUE_ES = {
    "morta": "Quan la pilota és morta, falta",
    "viva": "En joc, la pilota falta",
    "forats": "Els forats de la pilota en joc són",
    "aire": "Els forats comencen amb la pilota ràpida",
    "aglomeracio": "Els forats comencen en aglomeracions",
    "perdua": "Les estones que es perden els jugadors són",
}
GRUPS = {"la pilota que falta quan els jugadors van quiets": ("falta_quiets",),
         "la pilota que falta quan els jugadors corren": ("falta_corren",), "la llargada dels forats en joc": est.FORATS,
         "els forats amb la pilota ràpida": ("inici_rapida",), "els forats en aglomeracions": ("inici_aglomeracio",),
         "les estones dels jugadors": est.JUGADORS}


class ErrorDeReferencies(Exception):
    """Les referències del banc no hi són o no valen. El missatge és fix, sense cap dada."""


def carrega_referencies(cami: Path) -> dict:
    if not cami.is_file():
        raise ErrorDeReferencies("No trobo les referències del banc: fes primer `python -I -m banc.mesura_atd`")
    r = json.loads(cami.read_text(encoding="utf-8"))
    if r.get("clau_mesures") != tr.clau():
        raise ErrorDeReferencies("Les referències del banc són d'unes altres mesures: torna a fer "
                                 "`python -I -m banc.mesura_atd`")
    return r


def files(bloc: dict) -> pd.DataFrame:
    """Les mesures de cada candidat a cada partit obert: les referències."""
    return pd.DataFrame(bloc["files"])


def nom_de(r: dict, parametre: str, valor: object) -> str:
    return r["noms"][parametre].get(str(valor), str(valor))


def es_mesurable(r: dict, parametre: str, triat_pilota: tr.Triat) -> bool:
    if parametre == "perdua":
        return bool(r["mesurable"]["perdua"])
    condicio = f"{triat_pilota.parametres['morta']}|{triat_pilota.parametres['viva']}"
    return bool(r["mesurable"]["pilota"][parametre][condicio])


def linies_de_la_consola(r: dict, pilota: tr.Triat, jugadors: tr.Triat) -> list[str]:
    triats = {**pilota.parametres, **jugadors.parametres}
    linies = [linia(r, k, triats[k], es_mesurable(r, k, pilota)) for k in (*r["pilota"]["parametres"], "perdua")]
    linies.append(encaix(pilota, r["pilota"]["llindar"], "La pilota"))
    linies.append(encaix(jugadors, r["jugadors"]["llindar"], "Els jugadors"))
    return linies


def linia(r: dict, parametre: str, valor: object, mesurable: bool) -> str:
    if not mesurable:
        return f"· {QUE_ES[parametre]}: no es pot mesurar amb prou seguretat (al banc, en aquest cas, no es distingeix)"
    return f"✓ {QUE_ES[parametre]}: «{nom_de(r, parametre, valor)}»"


def encaix(triat: tr.Triat, llindar: float, que: str) -> str:
    if triat.distancia <= llindar:
        return f"✓ {que}: el partit s'assembla al candidat triat com els partits oberts al seu"
    parts = {grup: sum(triat.parts.get(k, 0.0) for k in mesures) for grup, mesures in GRUPS.items()}
    return f"⚠ {que}: el partit queda lluny de tots els candidats, sobretot per {max(parts, key=parts.get)}"


def informe(mesures_p: dict, mesures_j: dict, pilota: tr.Triat, jugadors: tr.Triat, r: dict) -> str:
    """Per a l'equip, dins del volum: les xifres del partit, les del candidat triat i les del que el banc suposa ara,
    i els grups de cada pas de la tria."""
    def mitjana_de(taula: pd.DataFrame, triat: dict, mesures: list[str]) -> pd.Series:
        t = taula
        for k, v in triat.items():
            t = t[t[k] == v]
        return t[mesures].mean()

    fp, fj = files(r["pilota"]), files(r["jugadors"])
    mp, mj = r["pilota"]["mesures"], r["jugadors"]["mesures"]
    triat_p = mitjana_de(fp, pilota.parametres, mp)
    ara_p = mitjana_de(fp, {k: ARA_AL_BANC[k] for k in r["pilota"]["parametres"]}, mp)
    triat_j, ara_j = mitjana_de(fj, jugadors.parametres, mj), mitjana_de(fj, {"perdua": ARA_AL_BANC["perdua"]}, mj)

    def comparacio(mesures: dict, triat: pd.Series, ara: pd.Series) -> list[str]:
        return ["| Mesura | Partit | Candidat triat | El banc ara (DFL) |", "|---|---|---|---|",
                *[f"| {k} | {v:.3f} | {triat[k]:.3f} | {ara[k]:.3f} |" for k, v in mesures.items()]]

    def pas(t: pd.DataFrame) -> list[str]:
        cap = "| " + " | ".join(t.columns) + " |"
        return [cap, "|" + "---|" * len(t.columns),
                *["| " + " | ".join(f"{x:.3f}" if isinstance(x, float) else str(x) for x in f) + " |"
                  for f in t.head(5).itertuples(index=False)], ""]

    return "\n".join([
        "# L'ATD del partit, comparat amb el banc", "",
        "**Dades del partit: no ho passis a cap LLM al núvol.** Mesures de `codi/mesura/estadistiques.py`, tria de "
        "`codi/mesura/tria.py`; els candidats i els criteris, a `docs/pla-mesura-atd.md`.", "",
        "## La pilota", "",
        f"Triat: {pilota.parametres}. Distància {pilota.distancia:.2f} (llindar de l'encaix: "
        f"{r['pilota']['llindar']:.2f}).", "",
        *comparacio(mesures_p, triat_p, ara_p), "",
        "Els grups més propers de cada pas:", "", *[x for t in pilota.passos for x in pas(t)],
        "## Els jugadors", "",
        f"Triat: {jugadors.parametres}. Distància {jugadors.distancia:.2f} (llindar de l'encaix: "
        f"{r['jugadors']['llindar']:.2f}).", "",
        *comparacio(mesures_j, triat_j, ara_j), "",
        "## Què es pot mesurar", "",
        *[f"- {QUE_ES[k]}: {'sí' if es_mesurable(r, k, pilota) else 'no'}" for k in (*r["pilota"]["parametres"],
                                                                                  "perdua")], "",
    ])


def fes(dades: Path, sortida: Path, casa: str = EQUIP_CASA,
        trams: tuple[tuple[int, int, int], ...] = TRAMS_DE_JOC, n: int = N_FOTOGRAMES,
        referencies: Path = REFERENCIES, parla: Callable[[str], None] = print) -> int:
    """Torna 0 si ha pogut mesurar, i 1 si no."""
    try:
        r = carrega_referencies(referencies)
        parla("… Llegint l'ATD tàctic")
        meta, raw = llegeix.localitza(dades)
        t = senyals.a_reixa(llegeix.tracking(meta, raw, casa), n)
    except (ErrorDeReferencies, llegeix.ErrorDeLectura) as error:        # només aquestes: el missatge és fix
        parla(f"✗ {error}")
        return 1
    parla("✓ ATD tàctic llegit")
    parla("… Les mesures, comparades amb els candidats del banc")
    puntuat = est.puntuades(n, trams)
    mesures_p, mesures_j = est.de_la_pilota(t, puntuat), est.dels_jugadors(t, puntuat)
    if not all(np.isfinite(v) for v in (*mesures_p.values(), *mesures_j.values())):
        parla("✗ Alguna mesura no s'ha pogut calcular (hi ha massa poques imatges amb jugadors o pilota)")
        return 1
    pilota = tr.tria(mesures_p, files(r["pilota"]), tr.passos_de(r["pilota"]))
    jugadors = tr.tria(mesures_j, files(r["jugadors"]), tr.passos_de(r["jugadors"]))
    sortida.mkdir(parents=True, exist_ok=True)
    (sortida / "informe.md").write_text(informe(mesures_p, mesures_j, pilota, jugadors, r), encoding="utf-8")
    for text in linies_de_la_consola(r, pilota, jugadors):
        parla(text)
    parla(f"· Les xifres són a {sortida / 'informe.md'}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="python -I -m mesura", description=__doc__.splitlines()[0])
    p.add_argument("--dades", type=Path, required=True, help="carpeta on hi ha les dades, tal com arriben")
    p.add_argument("--sortida", type=Path, default=CARPETA, help=f"la carpeta de l'informe (per defecte, {CARPETA})")
    args = p.parse_args()
    if not args.dades.is_dir():
        print(f"✗ No trobo la carpeta {args.dades}")
        return 1
    if not dins_del_volum(args.sortida):
        print(f"✗ L'informe porta xifres del partit: ha d'anar dins de {VOLUM}, i el volum ha de ser muntat")
        return 1
    dades, sortida = args.dades.resolve(), args.sortida.resolve()
    if dins_de(sortida, dades):
        print("✗ L'informe no pot anar dins de la carpeta de les dades")
        return 1
    sortida.mkdir(parents=True, exist_ok=True)
    try:
        with temporals_dins(Path(tempfile.mkdtemp(prefix=".mesura-", dir=sortida))):
            codi = fes(dades, sortida)
    except Exception as error:  # noqa: BLE001 - el missatge de l'error pot portar dades: no s'imprimeix
        print(f"✗ Error intern ({type(error).__name__}); no hi ha mesures")
        return 1
    print("\nL'informe és per a l'equip: no el passis, ni aquesta sortida, a cap LLM al núvol." if codi == 0 else
          "\nAlguna cosa ha fallat (vegeu ✗).")
    return codi


if __name__ == "__main__":
    sys.exit(main())
