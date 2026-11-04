"""El pas 1 de la T3ab (`docs/pla-tocs.md`, «T3ab»): els 64 partits de PFF al format del banc, i la seva veritat i el
seu tracking al costat dels de DFL, Metrica i SkillCorner, abans d'entrenar res.

    cd codi && uv run python -I -m banc.pff_al_costat [--processos 8]

1. **Cada partit de PFF, a la memòria cau** (`banc/pff.py`, `fonts.partit`). Un partit que no es pot llegir o que no
   quadra (les dues parts, de 44 a 60 minuts cadascuna, i el camp) es deixa fora, i es diu.
2. **La veritat:** la part de D i de X, les possessions per minut de pilota en joc i com duren. DFL i Metrica, amb la
   veritat de sempre (la que aprenen les xarxes) i amb la de toc (la que puntua).
3. **La taula de «Per què la T3l no hi arriba»,** mesurada de nou amb el mateix codi per a totes les fonts:
   - al canvi d'equip de la veritat (de H a A o al revés), si el jugador més proper a la pilota hi és a menys d'1,5 m
     i és del nou equip; i en quin moment, a ±1 s, el nou equip és més a prop de la pilota;
   - quan surt la pilota del camp, a ±3 s de l'inici de la D;
   - a la D, si la pilota es veu i com es mou;
   - amb la pilota a terra i en joc, si el jugador més proper hi és a menys d'1 m;
   - a les possessions de menys d'1 s, si el jugador més proper a la pilota (a menys d'1,5 m) és de l'equip de la
     veritat.
4. **La tria:** quantes imatges en tria `model_a_possessio.tria` a cada partit (sense degradar), i quina part de les
   de PFF s'ha de quedar perquè entre tots facin tantes mostres com nou partits del banc.

Escriu `resultats/pff-al-costat.json` i `resultats/pff-al-costat.md`. Tot són dades obertes.
"""

from __future__ import annotations

import argparse
import json
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from banc import avalua, fonts
from banc import model_a_possessio as t3f
from banc import veritat_toc as vt
from banc.partit import PartitBanc
from possessio.oficial import possession_metrics as pm

RESULTATS = Path(__file__).resolve().parent / "resultats"
FPS = pm.FPS
A_PROP_M, MOLT_A_PROP_M = 1.5, 1.0
FINESTRA_CANVI, FINESTRA_SORTIDA = 1 * FPS, 3 * FPS
MINUTS_PART = (44.0, 60.0)
EQUIPS = (pm.H, pm.A)
ORDRE = ("DFL, de sempre", "DFL, de toc", "Metrica, de sempre", "Metrica, de toc", "SkillCorner", "PFF")
T3L = {"DFL, de sempre": ("87 %", "0 s", "50 %", "de 0,24 a 0,08 s abans", "sempre, quieta", "47 %", "33 %"),
       "Metrica, de sempre": ("72 %", "0 s", "77 %", "de 0,28 a 0,08 s abans", "gairebé mai (3 %)", "54 %", "41 %"),
       "SkillCorner": ("31 %", "0,44 s després", "13 %", "de 0,48 s abans a 1,4 s després",
                       "la meitat, 1,5 m/s", "34 %", "15 %")}


def trossos(veritat: np.ndarray, trams: tuple[tuple[int, int, int], ...]) -> list[tuple[int, int, int]]:
    """(primera, última, codi) de cada tros seguit amb el mateix codi, dins de cada part."""
    out = []
    for _, inici, ultim in trams:
        v = veritat[inici:ultim + 1]
        vores = np.flatnonzero(np.diff(v) != 0) + 1
        for a, b in zip(np.r_[0, vores], np.r_[vores, len(v)]):
            out.append((inici + int(a), inici + int(b) - 1, int(v[a])))
    return out


def distancies(p: PartitBanc) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """La pilota en metres, i a cada imatge la distància del jugador de cada equip més proper a la pilota (NaN si no
    hi ha pilota o cap jugador de l'equip)."""
    t = p.tracking
    escala = np.asarray(t.camp_m, float)
    pilota = t.pilota * escala
    with warnings.catch_warnings(), np.errstate(invalid="ignore"):
        warnings.simplefilter("ignore", RuntimeWarning)
        casa = np.nanmin(np.linalg.norm(t.casa * escala - pilota[:, None, :], axis=2), axis=1)
        fora = np.nanmin(np.linalg.norm(t.fora * escala - pilota[:, None, :], axis=2), axis=1)
    return pilota, casa, fora


def canvis(veritat: np.ndarray, trams: tuple[tuple[int, int, int], ...]) -> list[int]:
    """Les imatges on la veritat passa d'un equip a l'altre, dins d'una part."""
    out = []
    for _, inici, ultim in trams:
        v = veritat[inici:ultim + 1]
        k = np.flatnonzero(np.isin(v[1:], EQUIPS) & np.isin(v[:-1], EQUIPS) & (v[1:] != v[:-1])) + 1
        out.extend((inici + k).tolist())
    return out


def part_de(trams: tuple[tuple[int, int, int], ...], n: int) -> np.ndarray:
    part = np.zeros(n, dtype=np.int64)
    for k, inici, ultim in trams:
        part[inici:ultim + 1] = k
    return part


def mesura(p: PartitBanc, veritat: np.ndarray) -> dict:
    """Els comptes d'un partit amb una veritat; `agrega` els suma per font."""
    n = len(veritat)
    part = part_de(p.trams, n)
    pilota, casa, fora = distancies(p)
    de = {pm.H: casa, pm.A: fora}
    vista = np.isfinite(pilota[:, 0])
    proper = np.where(casa <= fora, pm.H, pm.A)
    a_prop = np.fmin(casa, fora) < A_PROP_M
    trs = trossos(veritat, p.trams)
    possessions = [(a, b) for a, b, c in trs if c in EQUIPS]
    m = {"imatges": n, "D": int((veritat == pm.D).sum()), "X": int((veritat == pm.X).sum()),
         "en_joc": int(np.isin(veritat, EQUIPS).sum()), "possessions": len(possessions),
         "durades": [(b - a + 1) / FPS for a, b in possessions]}

    # al canvi d'equip
    ks = canvis(veritat, p.trams)
    vistos = [k for k in ks if vista[k] and np.isfinite(casa[k]) and np.isfinite(fora[k])]
    m["canvis_vistos"] = len(vistos)
    m["canvis_proper_nou"] = int(sum(a_prop[k] and proper[k] == veritat[k] for k in vistos))
    moments = []
    for k in ks:
        finestra = np.arange(max(0, k - FINESTRA_CANVI), min(n, k + FINESTRA_CANVI + 1))
        finestra = finestra[part[finestra] == part[k]]
        d = de[int(veritat[k])][finestra]
        if np.isfinite(d).any():
            moments.append(float(finestra[np.nanargmin(d)] - k) / FPS)
    m["moments"] = moments

    # quan surt la pilota del camp, respecte de l'inici de la D
    llarg, ample = p.tracking.camp_m
    fora_del_camp = vista & ((pilota[:, 0] < 0) | (pilota[:, 0] > llarg) | (pilota[:, 1] < 0) | (pilota[:, 1] > ample))
    surt = np.flatnonzero(fora_del_camp[1:] & ~fora_del_camp[:-1] & vista[:-1] & (part[1:] == part[:-1])) + 1
    sortides = []
    for k, (a, b, c) in enumerate(trs):
        if c != pm.D or k == 0 or trs[k - 1][2] not in EQUIPS or trs[k - 1][1] + 1 != a:
            continue
        prop = surt[(surt >= a - FINESTRA_SORTIDA) & (surt <= a + FINESTRA_SORTIDA) & (part[surt] == part[a])]
        if len(prop):
            sortides.append(float(prop[np.argmin(np.abs(prop - a))] - a) / FPS)
    m["sortides"] = sortides
    m["inicis_D"] = sum(1 for k, (a, _, c) in enumerate(trs) if c == pm.D and k and trs[k - 1][2] in EQUIPS)

    # la pilota a la D
    morta = veritat == pm.D
    m["D_amb_pilota"] = int((morta & vista).sum())
    seguides = morta[1:] & vista[1:] & vista[:-1] & (part[1:] == part[:-1])
    m["D_velocitats"] = (np.linalg.norm(np.diff(pilota, axis=0), axis=1)[seguides] * FPS).tolist()

    # a terra i en joc; i a les possessions de menys d'1 s
    z = p.pilota_z
    a_terra = np.isin(veritat, EQUIPS) & vista & np.isfinite(casa) & np.isfinite(fora) & ~(z >= 0.5)
    m["terra"] = int(a_terra.sum())
    m["terra_a_1m"] = int((a_terra & (np.fmin(casa, fora) < MOLT_A_PROP_M)).sum())
    curtes = np.zeros(n, dtype=bool)
    for a, b in possessions:
        if b - a + 1 < FPS:
            curtes[a:b + 1] = True
    curtes &= vista & np.isfinite(casa) & np.isfinite(fora)
    m["curtes"] = int(curtes.sum())
    m["curtes_de_l_equip"] = int((curtes & a_prop & (proper == veritat)).sum())
    return m


def quadra(p: PartitBanc) -> str | None:
    """Per què un partit de PFF no quadra, o None."""
    if [k for k, _, _ in p.trams] != [1, 2]:
        return f"les parts són {[k for k, _, _ in p.trams]}"
    for k, inici, ultim in p.trams:
        minuts = (ultim - inici + 1) / FPS / 60
        if not MINUTS_PART[0] <= minuts <= MINUTS_PART[1]:
            return f"la part {k} fa {minuts:.1f} minuts"
    llarg, ample = p.tracking.camp_m
    if not (90 <= llarg <= 120 and 45 <= ample <= 90):
        return f"el camp fa {llarg} × {ample} m"
    return None


def un(nom: str) -> dict:
    """Les mesures d'un partit, amb les seves veritats; per a PFF, també si quadra i el tracking."""
    try:
        p = fonts.partit(nom)
    except (ValueError, KeyError, OSError) as e:
        return {"nom": nom, "error": f"{type(e).__name__}: {e}"}
    font = p.font
    sortida = {"nom": nom, "font": font, "tria": int(len(t3f.tria(p.veritat, avalua.trams_valids(p))))}
    if font in ("dfl", "metrica"):
        nom_font = "DFL" if font == "dfl" else "Metrica"
        sortida["mesures"] = {f"{nom_font}, de sempre": mesura(p, p.veritat),
                              f"{nom_font}, de toc": mesura(p, vt.veritat(nom))}
    else:
        sortida["mesures"] = {"SkillCorner" if font == "skillcorner" else "PFF": mesura(p, p.veritat)}
    if font == "pff":
        t = p.tracking
        sortida["no_quadra"] = quadra(p)
        sortida["tracking"] = {
            "minuts": [round((b - a + 1) / FPS / 60, 1) for _, a, b in p.trams],
            "columnes": [t.casa.shape[1], t.fora.shape[1]], "camp": list(t.camp_m),
            "pilota_vista": float(np.isfinite(t.pilota[:, 0]).mean()), "X": float((p.veritat == pm.X).mean())}
    return sortida


def agrega(llista: list[dict]) -> dict:
    """Suma els comptes de diversos partits i en treu les parts i les medianes."""
    s = {k: sum(m[k] for m in llista) for k in llista[0] if not isinstance(llista[0][k], list)}
    durades = np.concatenate([m["durades"] for m in llista])
    moments = np.concatenate([m["moments"] for m in llista])
    sortides = np.concatenate([m["sortides"] for m in llista])
    velocitats = np.concatenate([m["D_velocitats"] for m in llista])
    minuts_en_joc = s["en_joc"] / FPS / 60

    def part(a: str, b: str) -> float:
        return s[a] / s[b] if s[b] else float("nan")
    return {
        "partits": len(llista), "D": s["D"] / s["imatges"], "X": s["X"] / s["imatges"],
        "D_de_les_que_tenen_veritat": s["D"] / (s["imatges"] - s["X"]),
        "possessions_per_minut": s["possessions"] / minuts_en_joc if minuts_en_joc else float("nan"),
        "durada_mediana_s": float(np.median(durades)), "possessions_de_menys_de_2s": float((durades < 2).mean()),
        "canvi_proper_nou": part("canvis_proper_nou", "canvis_vistos"),
        "moment_mediana_s": float(np.median(moments)) if len(moments) else float("nan"),
        "moment_a_0_2s": float((np.abs(moments) <= 0.2 + 1e-9).mean()) if len(moments) else float("nan"),
        "sortida_quartils_s": [float(q) for q in np.percentile(sortides, [25, 75])] if len(sortides) else [],
        "inicis_D_amb_sortida": len(sortides) / s["inicis_D"] if s["inicis_D"] else float("nan"),
        "D_amb_pilota": part("D_amb_pilota", "D"),
        "D_velocitat_mediana": float(np.median(velocitats)) if len(velocitats) else float("nan"),
        "terra_a_1m": part("terra_a_1m", "terra"), "curtes_de_l_equip": part("curtes_de_l_equip", "curtes")}


def tant_per_cent(x: float) -> str:
    return "—" if not np.isfinite(x) else f"{100 * x:.0f} %".replace(".", ",")


def segons(x: float) -> str:
    return "—" if not np.isfinite(x) else f"{x:+.2f} s".replace(".", ",").replace("-", "−")


def coma(x: float, decimals: int = 1) -> str:
    return f"{x:.{decimals}f}".replace(".", ",")


def markdown(r: dict) -> str:
    a = r["agregat"]
    cols = [c for c in ORDRE if c in a]
    capcalera = "| | " + " | ".join(cols) + " |\n|---|" + "---|" * len(cols) + "\n"
    files = [
        ("Partits", lambda x: str(x["partits"])),
        ("D, de totes les imatges", lambda x: tant_per_cent(x["D"])),
        ("X, de totes les imatges", lambda x: tant_per_cent(x["X"])),
        ("D, de les que tenen veritat", lambda x: tant_per_cent(x["D_de_les_que_tenen_veritat"])),
        ("Possessions per minut de pilota en joc", lambda x: f"{x['possessions_per_minut']:.1f}".replace(".", ",")),
        ("Durada mediana d'una possessió", lambda x: f"{x['durada_mediana_s']:.1f} s".replace(".", ",")),
        ("Possessions de menys de 2 s", lambda x: tant_per_cent(x["possessions_de_menys_de_2s"])),
    ]
    taula_veritat = capcalera + "".join(f"| {nom} | " + " | ".join(f(a[c]) for c in cols) + " |\n" for nom, f in files)
    files_t3l = [
        ("Al canvi d'equip, el jugador més proper a la pilota (a menys d'1,5 m) és del nou equip",
         lambda x: tant_per_cent(x["canvi_proper_nou"])),
        ("El moment en què el nou equip és més a prop de la pilota, respecte del canvi (mediana)",
         lambda x: segons(x["moment_mediana_s"])),
        ("Canvis amb aquest moment a ±0,2 s", lambda x: tant_per_cent(x["moment_a_0_2s"])),
        ("Quan surt la pilota del camp, respecte de l'inici de la D (quartils)",
         lambda x: " a ".join(segons(q) for q in x["sortida_quartils_s"]) or "—"),
        ("Inicis de D amb la pilota que surt del camp a ±3 s", lambda x: tant_per_cent(x["inicis_D_amb_sortida"])),
        ("A la D, la pilota es veu", lambda x: tant_per_cent(x["D_amb_pilota"])),
        ("A la D, la velocitat de la pilota (mediana)",
         lambda x: f"{x['D_velocitat_mediana']:.1f} m/s".replace(".", ",") if np.isfinite(x["D_velocitat_mediana"])
         else "—"),
        ("Amb la pilota a terra i en joc, el jugador més proper hi és a menys d'1 m", lambda x: tant_per_cent(x["terra_a_1m"])),
        ("A les possessions de menys d'1 s, el jugador més proper (a menys d'1,5 m) és de l'equip de la veritat",
         lambda x: tant_per_cent(x["curtes_de_l_equip"])),
    ]
    taula_t3l = capcalera + "".join(f"| {nom} | " + " | ".join(f(a[c]) for c in cols) + " |\n" for nom, f in files_t3l)
    files_abans = ["| | " + " | ".join(T3L) + " |", "|---|" + "---|" * len(T3L)]
    noms = [n for n, _ in files_t3l[:3]] + [files_t3l[3][0], files_t3l[5][0] + " (i com es mou)", files_t3l[7][0],
                                            files_t3l[8][0]]
    for k, nom in enumerate(noms):
        files_abans.append(f"| {nom} | " + " | ".join(v[k] for v in T3L.values()) + " |")
    fora = [f"- `{x['nom']}`: {x.get('error') or x.get('no_quadra')}" for x in r["fora"]] or ["- Cap."]
    t = r["tracking_pff"]
    tria = r["tria"]
    return "\n".join([
        "# PFF al costat del banc i de SkillCorner (pas 1 de la T3ab)", "",
        "`codi/banc/pff_al_costat.py`. Dades obertes. Abans d'entrenar res (`docs/pla-tocs.md`, «T3ab»).", "",
        "## Els partits de PFF que es deixen fora", "", *fora, "",
        "## El tracking de PFF", "",
        f"- Minuts per part: de {coma(t['minuts'][0])} a {coma(t['minuts'][1])}.",
        f"- Columnes de jugadors per equip: de {t['columnes'][0]} a {t['columnes'][1]}.",
        f"- La pilota es veu a un {tant_per_cent(t['pilota_vista'])} de les imatges; X (la tele no ensenya el camp), un "
        f"{tant_per_cent(t['X'])} (de {tant_per_cent(t['X_min'])} a {tant_per_cent(t['X_max'])} per partit).", "",
        "## La veritat", "", taula_veritat,
        "## La taula de «Per què la T3l no hi arriba», mesurada de nou", "", taula_t3l,
        "La de la T3l, per comparar-hi (`docs/pla-tocs.md`; mesurada llavors amb un altre codi):", "",
        "\n".join(files_abans), "",
        "## La tria", "",
        f"- Un partit del banc, de mitjana: {tria['banc_mitjana']:.0f} imatges triades; nou partits, "
        f"{tria['nou_del_banc']:.0f}.",
        f"- Els {tria['partits_pff']} de PFF, entre tots: {tria['pff_total']:.0f}.",
        f"- **La part de les de PFF que es queda:** {coma(tria['part'], 4)}.", ""])


def main() -> None:
    args = argparse.ArgumentParser()
    args.add_argument("--processos", type=int, default=8)
    a = args.parse_args()
    noms = (*fonts.NOMS, *fonts.NOMS_SKILLCORNER, *fonts.NOMS_PFF)
    with ProcessPoolExecutor(max_workers=a.processos) as feina:
        tots = list(feina.map(un, noms))
    fora = [x for x in tots if "error" in x or x.get("no_quadra")]
    bons = [x for x in tots if x not in fora]
    per_font: dict[str, list[dict]] = {}
    for x in bons:
        for c, m in x["mesures"].items():
            per_font.setdefault(c, []).append(m)
    pffs = [x for x in bons if x["font"] == "pff"]
    banc = [x["tria"] for x in bons if x["font"] in ("dfl", "metrica")]
    nou = 9 * float(np.mean(banc))
    total = float(sum(x["tria"] for x in pffs))
    xs = [x["tracking"]["X"] for x in pffs]
    r = {"agregat": {c: agrega(ms) for c, ms in per_font.items()},
         "fora": [{k: x.get(k) for k in ("nom", "error", "no_quadra")} for x in fora],
         "tracking_pff": {"minuts": [min(min(x["tracking"]["minuts"]) for x in pffs),
                                     max(max(x["tracking"]["minuts"]) for x in pffs)],
                          "columnes": [min(min(x["tracking"]["columnes"]) for x in pffs),
                                       max(max(x["tracking"]["columnes"]) for x in pffs)],
                          "pilota_vista": float(np.mean([x["tracking"]["pilota_vista"] for x in pffs])),
                          "X": float(np.mean(xs)), "X_min": float(min(xs)), "X_max": float(max(xs))},
         "tria": {"banc_mitjana": float(np.mean(banc)), "nou_del_banc": nou, "partits_pff": len(pffs),
                  "pff_total": total, "part": nou / total},
         "per_partit": [{k: v for k, v in x.items() if k != "mesures"} for x in tots]}
    RESULTATS.mkdir(exist_ok=True)
    (RESULTATS / "pff-al-costat.json").write_text(json.dumps(r, indent=1, ensure_ascii=False) + "\n")
    (RESULTATS / "pff-al-costat.md").write_text(markdown(r))
    print(markdown(r))


if __name__ == "__main__":
    main()
