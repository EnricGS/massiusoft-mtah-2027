"""Les referències de l'eina que mesura l'ATD (`docs/pla-mesura-atd.md`): els candidats, aplicats als partits oberts,
i si l'eina hi torna el candidat bo.

    cd codi && uv run python -I -m banc.mesura_atd

Escriu `banc/resultats/mesura-atd.json`, que llegeix `python -I -m mesura` al partit, i `mesura-atd.md`.

Els candidats són els escenaris del banc amb el que se'n suposa canviat. Es fan aquí, sense tocar `banc.degrada`
(que entra a la clau dels models): la pilota falta a la morta i a la viva en la part que diu el candidat, i la resta
és com `degrada.aplica`. La tria és la de `mesura.tria`, la mateixa que fa l'eina.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, replace
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

from banc import degrada, fonts
from banc.decodificador_tocs import QUART, amb_error
from banc.partit import PartitBanc
from mesura import estadistiques as est
from mesura import tria as tr
from possessio.oficial import possession_metrics as pm

DIR_RESULTATS = Path(__file__).resolve().parent / "resultats"
JSON = DIR_RESULTATS / "mesura-atd.json"

FORATS = ("curts", "barreja", "llargs")
MORTES = (0.41, 0.6, 0.97)                          # de la pilota morta puntuada, la part en què falta
VIVES = (0.03, 0.1, 0.2, 0.41)                      # i de la viva
PESOS = (0.0, 3.0, 9.0)                             # un forat hi comença 1 + pes vegades més sovint
PERDUES = ((0.2, 2.0), (0.5, 10.0), (2.0, 30.0))    # quant es perd un jugador, en segons
ENCERT_MINIM = 0.8
PERCENTIL_ENCAIX = 95

NOMS = {
    "forats": {"curts": "curts", "barreja": "barreja", "llargs": "llargs"},
    "morta": {0.41: "tant com en joc (com DFL)", 0.6: "més que en joc, però no sempre",
              0.97: "gairebé sempre (com Metrica)"},
    "viva": {0.03: "un 3 % (gairebé mai)", 0.1: "un 10 %", 0.2: "un 20 %", 0.41: "un 41 % (com el banc a DFL)"},
    "aire": {0.0: "igual que a la resta", 3.0: "com el banc (4 vegades més)", 9.0: "molt més (10 vegades)"},
    "aglomeracio": {0.0: "igual que a la resta", 3.0: "com el banc (4 vegades més)", 9.0: "molt més (10 vegades)"},
    "perdua": {"0.2-2": "curtes (de 0,2 a 2 s)", "0.5-10": "com el banc (de 0,5 a 10 s)",
               "2-30": "llargues (de 2 a 30 s)"},
}
PARAMETRES_PILOTA = ("morta", "viva", "forats", "aire", "aglomeracio")
PASSOS_PILOTA: tuple[tr.Pas, ...] = ((("morta",), ("falta_quiets",)), (("viva",), ("falta_corren",)),
                                     (("forats",), est.FORATS), (("aire",), ("inici_rapida",)),
                                     (("aglomeracio",), ("inici_aglomeracio",)))
CONDICIONS = tuple(f"{m}|{v}" for m in MORTES for v in VIVES)   # al partit, la pilota morta i la viva triades
PASSOS_JUGADORS: tuple[tr.Pas, ...] = ((("perdua",), est.JUGADORS),)


@dataclass(frozen=True)
class CandidatPilota:
    forats: str
    morta: float
    viva: float
    aire: float
    aglomeracio: float


CANDIDATS = tuple(CandidatPilota(*c) for c in product(FORATS, MORTES, VIVES, PESOS, PESOS))
DEL_BANC = CandidatPilota("barreja", 0.41, 0.41, 3.0, 3.0)      # el que el banc suposa ara (a DFL)


def nom_perdua(perdua: tuple[float, float]) -> str:
    return "-".join(f"{x:g}" for x in perdua)


def fi_de_la_morta(p: PartitBanc) -> np.ndarray:
    """Com `degrada.fi_del_tram`, però dins d'una estona de pilota morta, la primera fila després de l'estona."""
    fi = degrada.fi_del_tram(p)
    inicis, finals = est.tirades(degrada.puntuats(p) & (p.veritat == pm.D))
    for inici, final in zip(inicis, finals):
        fi[inici:final] = np.minimum(fi[inici:final], final)
    return fi


def forats(rng: np.random.Generator, p: PartitBanc, esc: degrada.Escenari, morta: float, viva: float) -> np.ndarray:
    """Els forats de la pilota: a la morta puntuada, fins a la part `morta`, sense sortir de cada estona de pilota
    morta; a la viva, fins a la part `viva`. Si la font ja hi falta més sovint (Metrica, a la morta), no se n'hi posa
    cap."""
    graduats, absent = degrada.puntuats(p), np.isnan(p.tracking.pilota[:, 0])
    # la pilota «a l'aire», per la velocitat i no per l'alçada, també a DFL: al partit només es veu la velocitat
    rapida, aglomeracio = degrada.aire_i_aglomeracio(replace(p, pilota_z=np.full(p.n, np.nan)), esc)
    pes = 1.0 + esc.pes_aire * rapida + esc.pes_aglomeracio * aglomeracio
    mortes, vives = graduats & (p.veritat == pm.D), graduats & (p.veritat != pm.D)
    forat = np.zeros(p.n, bool)
    degrada.omple(rng, forat, mortes, absent, pes, fi_de_la_morta(p), replace(esc, pilota_absent=morta))
    degrada.omple(rng, forat, vives, absent, pes, degrada.fi_del_tram(p), replace(esc, pilota_absent=viva))
    return forat


def aplica(p: PartitBanc, c: CandidatPilota, perdua: tuple[float, float] = PERDUES[1]) -> PartitBanc:
    """El candidat, amb l'error de posició ×¼ (el mesurat al partit, V1). La resta, com `degrada.aplica`."""
    esc = replace(amb_error(c.forats, QUART), pes_aire=c.aire, pes_aglomeracio=c.aglomeracio,
                  perdua_jugador_s=perdua)
    rng, t = degrada.generador(f"mesura|{c}|{nom_perdua(perdua)}", p.nom), p.tracking
    camp, graduats = np.array(t.camp_m), degrada.puntuats(p)
    pilota = t.pilota.copy()
    pilota[forats(rng, p, esc, c.morta, c.viva)] = np.nan
    vistos = ((~np.isnan(t.casa[..., 0])).sum(1) + (~np.isnan(t.fora[..., 0])).sum(1))[graduats].mean()
    perdua_ = max(0.0, 1 - esc.objectes / (vistos * (1 + esc.duplicats)))
    equips = []
    for equip in (t.casa, t.fora):
        perdut = degrada.perd_estones(rng, equip, graduats, perdua_, esc)
        trossos = degrada.peces(perdut) + degrada.duplicats(rng, perdut, esc.duplicats, esc)
        slots = degrada.en_slots(rng, trossos, p.n, esc.slots_per_equip)
        equips.append(degrada.soroll(rng, slots, camp, esc.sigma_jugadors_m, esc.tremolor_jugadors_m))
    pilota = degrada.soroll(rng, pilota, camp, esc.sigma_pilota_m, esc.tremolor_pilota_m)
    return replace(p, tracking=replace(t, pilota=pilota, casa=equips[0], fora=equips[1]))


def mesures_del_partit(nom: str) -> tuple[list[dict], list[dict]]:
    """Les mesures de cada candidat aplicat al partit. A Metrica, que no té la pilota quan és morta, només els
    candidats que hi falta gairebé sempre; els dels jugadors, només a DFL."""
    p = fonts.partit(nom)
    graduats = degrada.puntuats(p)
    candidats = CANDIDATS if p.font == "dfl" else [c for c in CANDIDATS if c.morta == MORTES[-1]]
    pilota = [{"partit": nom, "font": p.font, **asdict(c), **est.de_la_pilota(aplica(p, c).tracking, graduats)}
              for c in candidats]
    jugadors = [] if p.font != "dfl" else [
        {"partit": nom, "perdua": nom_perdua(d), **est.dels_jugadors(aplica(p, DEL_BANC, d).tracking, graduats)}
        for d in PERDUES]
    return pilota, jugadors


def valida(taula: pd.DataFrame, passos: tuple[tr.Pas, ...]) -> pd.DataFrame:
    """Amb cada partit de DFL apartat, les referències dels altres i cada candidat aplicat a l'apartat: què tria."""
    files = []
    dfl = taula[taula["font"] == "dfl"] if "font" in taula else taula
    claus = [k for c, _ in passos for k in c]
    for apartat in sorted(dfl["partit"].unique()):
        referencia = dfl[dfl["partit"] != apartat]
        for _, fila in dfl[dfl["partit"] == apartat].iterrows():
            t = tr.tria(fila, referencia, passos)
            files.append({"partit": apartat, **{k: fila[k] for k in claus},
                          **{f"triat_{k}": v for k, v in t.parametres.items()}, "distancia": t.distancia})
    return pd.DataFrame(files)


def a_metrica(taula: pd.DataFrame) -> pd.DataFrame:
    """Els partits de Metrica, amb les referències de tots els de DFL."""
    dfl = taula[taula["font"] == "dfl"]
    files = []
    for _, fila in taula[taula["font"] == "metrica"].iterrows():
        t = tr.tria(fila, dfl, PASSOS_PILOTA)
        files.append({"partit": fila["partit"], **{k: fila[k] for k in PARAMETRES_PILOTA},
                      **{f"triat_{k}": v for k, v in t.parametres.items()}})
    return pd.DataFrame(files)


def encert(v: pd.DataFrame, k: str) -> float:
    return float((v[k] == v[f"triat_{k}"]).mean()) if len(v) else 0.0


def encerts_per_condicio(v: pd.DataFrame) -> dict[str, dict[str, float]]:
    """De cada paràmetre de la pilota, l'encert als casos en què l'eina tria cada pilota morta i viva: al partit, se
    sap la triada, i on comencen els forats només es veu si n'hi ha prou en joc."""
    condicio = v["triat_morta"].astype(str) + "|" + v["triat_viva"].astype(str)
    return {k: {c: encert(v[condicio == c], k) for c in CONDICIONS} for k in PARAMETRES_PILOTA}


def clau() -> str:
    h = hashlib.sha256(tr.clau().encode())
    for modul in (degrada,):
        h.update(Path(modul.__file__).read_bytes())
    h.update(Path(__file__).read_bytes())
    h.update(repr((fonts.NOMS, np.__version__, pd.__version__)).encode())
    return h.hexdigest()


def resultat(pilota: pd.DataFrame, jugadors: pd.DataFrame) -> dict:
    """El que es desa: les mesures de cada candidat a cada partit de DFL (les referències), la validació i què es pot
    mesurar."""
    dfl = pilota[pilota["font"] == "dfl"]
    v_pilota, v_jugadors = valida(pilota, PASSOS_PILOTA), valida(jugadors, PASSOS_JUGADORS)
    v_metrica = a_metrica(pilota)
    per_condicio = encerts_per_condicio(v_pilota)
    encert_metrica = {"morta": float((v_metrica["triat_morta"] == MORTES[-1]).mean()),
                      "viva": encert(v_metrica, "viva")}
    encert_jugadors = encert(v_jugadors, "perdua")
    mesurable = {k: {c: e >= ENCERT_MINIM for c, e in per_condicio[k].items()} for k in PARAMETRES_PILOTA}
    for k, e in encert_metrica.items():
        mesurable[k] = {c: si and e >= ENCERT_MINIM for c, si in mesurable[k].items()}

    def bloc(taula: pd.DataFrame, parametres: tuple[str, ...], mesures: tuple[str, ...],
             passos: tuple[tr.Pas, ...], v: pd.DataFrame) -> dict:
        return {"parametres": list(parametres), "mesures": list(mesures),
                "passos": [[list(c), list(m)] for c, m in passos],
                "files": taula[["partit", *parametres, *mesures]].to_dict(orient="records"),
                "llindar": float(np.percentile(v["distancia"], PERCENTIL_ENCAIX))}

    return {
        "clau": clau(), "clau_mesures": tr.clau(), "partits": sorted(pilota["partit"].unique().tolist()),
        "pilota": bloc(dfl, PARAMETRES_PILOTA, est.PILOTA, PASSOS_PILOTA, v_pilota),
        "jugadors": bloc(jugadors, ("perdua",), est.JUGADORS, PASSOS_JUGADORS, v_jugadors),
        "noms": {k: {str(c): n for c, n in v.items()} for k, v in NOMS.items()},
        "validacio": {"encert": {k: encert(v_pilota, k) for k in PARAMETRES_PILOTA}, "per_condicio": per_condicio,
                      "perdua": encert_jugadors, "a_metrica": encert_metrica,
                      "metrica": {k: encert(v_metrica, k) for k in PARAMETRES_PILOTA},
                      "casos_pilota": len(v_pilota), "casos_metrica": len(v_metrica),
                      "casos_jugadors": len(v_jugadors)},
        "mesurable": {"pilota": mesurable, "perdua": encert_jugadors >= ENCERT_MINIM},
    }


def informe(r: dict) -> str:
    v, m = r["validacio"], r["mesurable"]
    pct = lambda x: f"{100 * x:.0f} %"                             # noqa: E731
    files = pd.DataFrame(r["pilota"]["files"])
    del_banc = files[(files["aire"] == DEL_BANC.aire) & (files["aglomeracio"] == DEL_BANC.aglomeracio)]
    mitjanes = del_banc.groupby(["morta", "viva", "forats"])[list(est.PILOTA)].mean()
    jugadors = pd.DataFrame(r["jugadors"]["files"]).groupby("perdua")[list(est.JUGADORS)].mean()
    return "\n".join([
        "# L'eina que mesura l'ATD: les referències i la validació", "",
        "Fet amb `python -I -m banc.mesura_atd`, amb dades obertes. El pla i els criteris són a "
        "`docs/pla-mesura-atd.md`.", "",
        f"Partits: {', '.join(r['partits'])}. Candidats de la pilota: {len(CANDIDATS)} a cada partit de DFL i "
        f"{len([c for c in CANDIDATS if c.morta == MORTES[-1]])} a cada partit de Metrica; dels jugadors, "
        f"{len(PERDUES)} a cada partit de DFL.", "",
        "## Si l'eina torna el candidat bo", "",
        "Amb cada partit de DFL apartat, les referències fetes amb els altres 6 i cada candidat aplicat a l'apartat. "
        f"El criteri: un {pct(ENCERT_MINIM)} o més, als casos en què l'eina tria cada pilota morta i viva.", "",
        f"En total: {', '.join(f'{k} {pct(x)}' for k, x in v['encert'].items())}; perdua {pct(v['perdua'])} "
        f"{'✓' if m['perdua'] else '✗'}.", "",
        "| Pilota morta | Pilota viva | " + " | ".join(PARAMETRES_PILOTA) + " |",
        "|---|---|" + "---|" * len(PARAMETRES_PILOTA),
        *[f"| {NOMS['morta'][float(c.split('|')[0])]} | {NOMS['viva'][float(c.split('|')[1])]} | "
          + " | ".join(f"{pct(v['per_condicio'][k][c])} {'✓' if m['pilota'][k][c] else '✗'}"
                       for k in PARAMETRES_PILOTA) + " |" for c in CONDICIONS], "",
        f"A Metrica, amb les referències de DFL, la pilota morta surt «gairebé sempre» en un "
        f"{pct(v['a_metrica']['morta'])} dels {v['casos_metrica']} casos, i la viva encerta un "
        f"{pct(v['a_metrica']['viva'])} (el criteri, un {pct(ENCERT_MINIM)}). La resta, a Metrica: "
        + ", ".join(f"{k} {pct(x)}" for k, x in v["metrica"].items()) + ".", "",
        f"Llindar de l'encaix (el percentil {PERCENTIL_ENCAIX} de la distància al candidat triat, amb el partit "
        f"apartat): pilota {r['pilota']['llindar']:.1f}, jugadors {r['jugadors']['llindar']:.1f}.", "",
        "## Les mesures de cada candidat (la mitjana dels partits de DFL)", "",
        "Els candidats amb els pesos del banc (4 vegades més a l'aire i en aglomeracions):", "",
        *taula_md(mitjanes), "",
        "Els jugadors:", "", *taula_md(jugadors), "",
    ])


def taula_md(t: pd.DataFrame) -> list[str]:
    t = t.reset_index()
    return ["| " + " | ".join(t.columns) + " |", "|" + "---|" * len(t.columns),
            *["| " + " | ".join(f"{x:.3f}" if isinstance(x, float) else f"{x}" for x in fila) + " |"
              for fila in t.itertuples(index=False)]]


def main() -> int:
    args = argparse.ArgumentParser(prog="python -I -m banc.mesura_atd", description=__doc__.splitlines()[0])
    args.add_argument("--processos", type=int, default=4)
    processos = args.parse_args().processos
    noms = tuple(n for n in fonts.NOMS)
    with ProcessPoolExecutor(max_workers=processos) as feina:
        parts = list(feina.map(mesures_del_partit, noms))
    pilota = pd.DataFrame([f for p, _ in parts for f in p])
    jugadors = pd.DataFrame([f for _, j in parts for f in j])
    r = resultat(pilota, jugadors)
    DIR_RESULTATS.mkdir(exist_ok=True)
    JSON.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    (DIR_RESULTATS / "mesura-atd.md").write_text(informe(r), encoding="utf-8")
    print(f"✓ {JSON}")
    for k, per_condicio in r["validacio"]["per_condicio"].items():
        print(f"· {k}: " + ", ".join(f"{c} {e:.2f}{'✓' if r['mesurable']['pilota'][k][c] else '✗'}"
                                     for c, e in per_condicio.items()))
    print(f"· perdua: {r['validacio']['perdua']:.2f}{'✓' if r['mesurable']['perdua'] else '✗'}")
    print(f"· Metrica: {r['validacio']['a_metrica']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
