"""Valida la pilota de l'ATD contra el vídeo tàctic (V1 de `docs/pla-video.md`). L'executa l'Enric, en local.

    cd codi && uv run --with torch --with torchvision --with opencv-python-headless \\
        python -I -m pilota.valida --dades "<carpeta de les dades>"

Per a una imatge per segon de les parts puntuades, de les que l'ATD té la pilota:
1. **On l'ATD diu que és,** al píxel del vídeo, amb l'homografia d'aquella imatge, i la mida que hi fa una pilota
   al terra (`DIAMETRE_PILOTA_M`).
2. **El detector** (FootAndBall, `pilota/footandball.py`) busca pilotes en un quadrat del vídeo de ±`RETALL_M` al
   voltant d'aquest punt, ampliat perquè la pilota hi faci la mida de l'entrenament (`DIAMETRE_ENTRENAMENT_PX`): a
   la meitat en troba poques o cap. Les candidates tornen al camp amb la inversa de l'homografia, en metres.
3. **Les mesures:** si el vídeo hi veu una pilota (una candidata segura a `BUSCA_M` o menys), si coincideix (a
   `COINCIDEIX_M` o menys), l'error en metres i si la més segura de totes és lluny (en veu una altra). I el
   desfasament: la pilota del vídeo es compara amb la de l'ATD d'unes imatges abans i després, i el bo és el que
   dona l'error més petit (si la pilota es mou, una imatge de més ja l'allunya).
4. **El soroll de la pilota lliure** de l'ATD (`cadena.tocs.soroll_lliure`), comparat amb els escenaris del banc de
   tocs, per triar els paràmetres del detector de tocs.
5. **El cas,** amb els criteris escrits abans de mirar (`docs/pla-video.md`, «V1: els criteris»).

Escriu dins del volum xifrat l'informe (`informe.md`), la mostra (`mostra.csv`), les candidates (`candidates.npz`) i
el resultat (`resultat.json`). Cap imatge del vídeo: no fa cap full de retalls (D-80). A la consola només surt si cada
pas ha anat bé, el cas i el nivell de soroll: cap xifra.
"""

from __future__ import annotations

import argparse
import faulthandler
import json
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np
import pandas as pd

from banc import tocs_desats
from cadena import llegeix, senyals, tocs
from cadena.norma import EQUIP_CASA, N_FOTOGRAMES, PARTIT, TRAMS_PUNTUATS
from cadena.volum import VOLUM, dins_del_volum, temporals_dins
from inspeccio.carrega import Homografia, homografia, projecta
from pilota import video as videos
from pilota.footandball import Candidats

SORTIDA = VOLUM / "pilota" / "valida"
VIDEO, HOMOGRAFIA = f"{PARTIT}_tactical.mp4", f"{PARTIT}_tactical_homography.csv"
PAS = 25                            # una imatge per segon
MAXIM = 10                          # les candidates que es guarden de cada imatge
DIAMETRE_PILOTA_M = 0.22
DIAMETRE_ENTRENAMENT_PX = 10.0      # el de la pilota a ISSIA-CNR, on es va entrenar FootAndBall
ESCALES = (0.5, 4.0)                # quant es pot encongir o ampliar el retall, com a molt
RETALL_M = 8.0                      # el detector mira ±8 m al voltant de la pilota de l'ATD
# Els criteris (`docs/pla-video.md`, «V1: els criteris»), escrits abans de mirar:
LLINDAR = 0.5                       # una candidata és segura d'aquí amunt (a ISSIA, poques sense pilota)
LLINDAR_ALT = 0.9                   # i molt segura d'aquí amunt (a ISSIA, cap sense pilota)
COINCIDEIX_M = 1.0
BUSCA_M = 5.0
DESFASAMENTS = tuple(range(-3, 4))
VEU_MINIM = 0.5                     # D si el vídeo hi veu la pilota en menys de la meitat de la mostra
UNA_ALTRA_MAXIM = 0.05              # C si en més d'un 5 % la més segura de totes és a més de BUSCA_M
COINCIDEIX_MINIM = 0.8              # A si, on la veu, coincideix en un 80 % o més; si no, B
CASOS = {
    "A": ("La pilota de l'ATD és bona tal com és",
          "Es fa servir tal com és on hi és, i V2 la busca només on falta"),
    "B": ("El vídeo la veu a prop de la de l'ATD, però sovint a més d'1 m",
          "V2 també refà la posició on l'ATD la té, amb la del vídeo"),
    "C": ("Sovint el vídeo veu clarament una pilota lluny de la de l'ATD",
          "O l'ATD s'equivoca de lloc o el detector confon una altra cosa"),
    "D": ("El detector no veu la pilota al voltant de la de l'ATD en la meitat de la mostra o més",
          "Amb aquest detector no es pot validar: en aquest vídeo veu massa poques pilotes"),
}
GRUPS = ("coincideix", "a prop", "no es veu", "una altra")


class Detector(Protocol):
    def pilotes(self, imatge_bgr: np.ndarray, escala: float = 1.0) -> Candidats: ...


@dataclass(frozen=True)
class Mostra:
    frame: np.ndarray           # (n,) les imatges del vídeo
    atd_m: np.ndarray           # (n, 2) la pilota de l'ATD, en metres
    atd_px: np.ndarray          # (n, 2) i al vídeo
    diametre_px: np.ndarray     # (n,) la mida que hi fa una pilota al terra
    cand_px: np.ndarray         # (n, MAXIM, 3) x, y i confiança de les candidates, de més a menys; NaN si n'hi ha menys
    cand_m: np.ndarray          # (n, MAXIM, 2) les candidates al camp, en metres


def tria_mostra(pilota: np.ndarray, trams, pas: int = PAS) -> np.ndarray:
    """Les imatges múltiples de `pas`, dins de les parts puntuades, on l'ATD té la pilota."""
    dins = np.zeros(len(pilota), bool)
    for _, inici, ultim in trams:
        dins[inici:ultim + 1] = True
    return np.flatnonzero(dins & (np.arange(len(pilota)) % pas == 0) & ~np.isnan(pilota[:, 0]))


def al_pixel(matrius: np.ndarray, punts_01: np.ndarray) -> np.ndarray:
    u, v = projecta(matrius, punts_01[:, 0], punts_01[:, 1])
    return np.column_stack([u, v])


def al_camp(matrius: np.ndarray, px: np.ndarray, camp_m: np.ndarray) -> np.ndarray:
    """Píxels (n, k, 2) al camp, en metres, amb la inversa de l'homografia de cada imatge."""
    x, y = projecta(np.linalg.inv(matrius), px[..., 0], px[..., 1])
    return np.stack([x, y], axis=-1) * camp_m


def diametre_px(matrius: np.ndarray, punts_m: np.ndarray, camp_m: np.ndarray) -> np.ndarray:
    """La mida que fa al vídeo una pilota al terra: la més gran de les dues escales del camp en aquell punt (píxels
    per metre), perquè una esfera no s'aplana com el terra."""
    escales = []
    for pas in (np.array([0.5, 0.0]), np.array([0.0, 0.5])):
        abans, despres = al_pixel(matrius, (punts_m - pas) / camp_m), al_pixel(matrius, (punts_m + pas) / camp_m)
        escales.append(np.linalg.norm(despres - abans, axis=1))
    return DIAMETRE_PILOTA_M * np.fmax(*escales)


def retall(imatge: np.ndarray, centre: np.ndarray, mig: int) -> tuple[np.ndarray, np.ndarray]:
    """Un quadrat de costat 2·`mig` al voltant de `centre`, desplaçat perquè quedi dins de la imatge."""
    alt, ample = imatge.shape[:2]
    mig = int(min(mig, alt // 2, ample // 2))
    x0 = int(np.clip(np.round(centre[0]) - mig, 0, ample - 2 * mig))
    y0 = int(np.clip(np.round(centre[1]) - mig, 0, alt - 2 * mig))
    return np.ascontiguousarray(imatge[y0:y0 + 2 * mig, x0:x0 + 2 * mig]), np.array([x0, y0], float)


def passa_detector(video: Path, m: Mostra, detector: Detector, parla: Callable[[str], None],
                   pas: int = PAS, mides: tuple[int, int] | None = None) -> np.ndarray:
    """Les candidates de cada imatge de la mostra, en píxels del vídeo."""
    n = len(m.frame)
    cand = np.full((n, MAXIM, 3), np.nan)
    escala = np.clip(DIAMETRE_ENTRENAMENT_PX / m.diametre_px, *ESCALES)
    mig = np.ceil(RETALL_M * m.diametre_px / DIAMETRE_PILOTA_M).astype(int)
    fila = {int(f): i for i, f in enumerate(m.frame)}
    desenes = 1                                         # el progrés, de 10 en 10 %
    for f, imatge in videos.imatges(video, m.frame, pas, mides):
        i = fila[f]
        tros, origen = retall(imatge, m.atd_px[i], mig[i])
        c = detector.pilotes(tros, float(escala[i]))
        k = min(MAXIM, len(c.x))
        cand[i, :k] = np.column_stack([c.x[:k] + origen[0], c.y[:k] + origen[1], c.confianca[:k]])
        while desenes < 10 and f >= desenes / 10 * m.frame[-1]:
            parla(f"… {desenes * 10} %")
            desenes += 1
    return cand


def distancies(cand_px: np.ndarray, cand_m: np.ndarray, atd_m: np.ndarray, llindar: float = LLINDAR):
    """(la distància de la candidata segura més propera, la de la més segura de totes), en metres; inf si no n'hi ha."""
    d = np.linalg.norm(cand_m - atd_m[:, None, :], axis=2)
    segura = (cand_px[..., 2] >= llindar) & ~np.isnan(d)
    return np.where(segura, d, np.inf).min(axis=1), np.where(np.isnan(d[:, 0]), np.inf, d[:, 0])


def grups(m: Mostra) -> np.ndarray:
    propera, primera = distancies(m.cand_px, m.cand_m, m.atd_m)
    una_altra = (m.cand_px[:, 0, 2] >= LLINDAR_ALT) & (primera > BUSCA_M)
    return np.select([una_altra, propera > BUSCA_M, propera <= COINCIDEIX_M], ["una altra", "no es veu", "coincideix"],
                     "a prop")


def error_per_desfasament(m: Mostra, pilota_m: np.ndarray) -> dict[int, float]:
    """La mediana de la distància entre la pilota que veu el vídeo a la imatge f (la segura més propera a la de l'ATD,
    on n'hi ha) i la de l'ATD a f + s, per a cada s. `pilota_m`: la de l'ATD a totes les imatges, en metres."""
    d = np.linalg.norm(m.cand_m - m.atd_m[:, None, :], axis=2)
    segura = (m.cand_px[..., 2] >= LLINDAR) & ~np.isnan(d)
    d = np.where(segura, d, np.inf)
    veu = d.min(axis=1) <= BUSCA_M
    vista = m.cand_m[np.arange(len(d)), d.argmin(axis=1)][veu]
    errors = {}
    for s in DESFASAMENTS:
        on = m.frame[veu] + s
        dins = (on >= 0) & (on < len(pilota_m))
        e = np.linalg.norm(vista[dins] - pilota_m[on[dins]], axis=1)
        e = e[~np.isnan(e)]
        errors[s] = float(np.median(e)) if len(e) else float("nan")
    return errors


def mesures(m: Mostra, pilota_m: np.ndarray) -> dict:
    """`pilota_m`: la de l'ATD a totes les imatges, en metres (per al desfasament)."""
    propera, primera = distancies(m.cand_px, m.cand_m, m.atd_m)
    veu = propera <= BUSCA_M
    d_px = np.linalg.norm(m.cand_px[..., :2] - m.atd_px[:, None, :], axis=2)
    segura = m.cand_px[..., 2] >= LLINDAR
    px = np.where(segura & ~np.isnan(d_px), d_px, np.inf).min(axis=1)[veu]
    per_desfasament = error_per_desfasament(m, pilota_m)
    mesurats = [s for s in DESFASAMENTS if np.isfinite(per_desfasament[s])]
    millor = min(mesurats, key=lambda s: (per_desfasament[s], abs(s))) if mesurats else None
    return {
        "mostra": len(m.frame),
        "veu": float(veu.mean()) if len(veu) else float("nan"),
        "coincideix": float((propera[veu] <= COINCIDEIX_M).mean()) if veu.any() else float("nan"),
        "error_m_mediana": float(np.median(propera[veu])) if veu.any() else float("nan"),
        "error_m_p90": float(np.percentile(propera[veu], 90)) if veu.any() else float("nan"),
        "error_px_mediana": float(np.median(px)) if len(px) else float("nan"),
        "una_altra": float(((m.cand_px[:, 0, 2] >= LLINDAR_ALT) & (primera > BUSCA_M)).mean()) if len(veu) else
        float("nan"),
        "desfasament": millor,                  # None si no s'ha pogut mesurar
        "error_per_desfasament": per_desfasament,
        "diametre_px": [float(v) for v in np.percentile(m.diametre_px, [10, 50, 90])] if len(veu) else [],
    }


def cas(r: dict) -> str:
    """Els criteris, en aquest ordre: sense un detector que hi arribi, la resta no es pot jutjar."""
    if not r["veu"] >= VEU_MINIM:
        return "D"
    if r["una_altra"] > UNA_ALTRA_MAXIM:
        return "C"
    return "A" if r["coincideix"] >= COINCIDEIX_MINIM else "B"


def nivells_del_banc(cami: Path | None = None) -> dict[float, float]:
    """El soroll de la pilota lliure de cada escenari «barreja, soroll ×f» del banc de tocs (la mitjana dels partits).
    Es llegeix de `banc.tocs_desats` i no de `banc.tocs`, que carrega LightGBM: amb PyTorch al mateix procés, cau."""
    desat = json.loads((cami or tocs_desats.DIR_RESULTATS / "tocs.json").read_text())
    if desat.get("clau") != tocs_desats.clau():
        raise RuntimeError("Els resultats del banc de tocs són d'un altre codi: torna a fer `python -I -m banc.tocs`")
    files = pd.DataFrame(desat["files"])
    return {f: float(files.loc[files["escenari"] == tocs_desats.nom_soroll(f), "soroll_ms"].mean())
            for f in tocs_desats.FACTORS_SOROLL}


def nivell(soroll: float, nivells: dict[float, float]) -> float:
    """El factor de soroll del banc més proper (en proporció); 0 si no arriba a la meitat del més petit."""
    positius = {f: v for f, v in nivells.items() if f > 0}
    if not np.isfinite(soroll) or not positius:
        return float("nan")
    if soroll < min(positius.values()) / 2:
        return 0.0
    return min(positius, key=lambda f: abs(np.log(soroll / positius[f])))


def informe(r: dict, nivells: dict[float, float]) -> str:
    def pct(v: float) -> str:
        return "—" if not np.isfinite(v) else f"{v:.0%}"

    def num(v: float, decimals: int = 2) -> str:
        return "—" if not np.isfinite(v) else f"{v:.{decimals}f}"

    titol, que = CASOS[r["cas"]]
    linies = [
        "# La pilota de l'ATD contra el vídeo tàctic", "",
        "Fet amb `pilota/valida.py` (V1 de `docs/pla-video.md`). Dades del concurs: no surt del volum.", "",
        f"## El cas: {r['cas']} · {titol}", "", f"{que}.", "",
        "## Les mesures", "",
        "| Mesura | Valor | Criteri |", "|---|---|---|",
        f"| Imatges de la mostra (una per segon, amb pilota a l'ATD) | {r['mostra']} | |",
        f"| Fora de la imatge del vídeo (no compten) | {r['fora']} | |",
        f"| El vídeo hi veu una pilota (segura, a {BUSCA_M:g} m o menys) | {pct(r['veu'])} | D si < {VEU_MINIM:.0%} |",
        f"| La més segura de totes és a més de {BUSCA_M:g} m (≥ {LLINDAR_ALT:g}) | {pct(r['una_altra'])} | "
        f"C si > {UNA_ALTRA_MAXIM:.0%} |",
        f"| On la veu, coincideix (a {COINCIDEIX_M:g} m o menys) | {pct(r['coincideix'])} | "
        f"A si ≥ {COINCIDEIX_MINIM:.0%}, si no B |",
        f"| Error on la veu: mediana i percentil 90 (m) | {num(r['error_m_mediana'])} · {num(r['error_m_p90'])} | |",
        f"| Error on la veu: mediana (px) | {num(r['error_px_mediana'], 1)} | |",
        "| Mida de la pilota al vídeo: percentils 10, 50 i 90 (px) | "
        + " · ".join(num(v, 1) for v in r["diametre_px"]) + " | |",
        f"| Temps (minuts) | {r['segons'] / 60:.1f} | |", "",
        "## El desfasament", "",
        "La mediana de l'error si la pilota del vídeo es compara amb la de l'ATD unes quantes imatges abans o "
        "després. Si la més petita no és la del 0, el vídeo i l'ATD no van a la mateixa imatge.", "",
        "| Imatges | Error (m) |", "|---|---|",
        *[f"| {s:+d} | {num(v)} |" for s, v in r["error_per_desfasament"].items()], "",
        f"El millor: **{'—' if r['desfasament'] is None else format(r['desfasament'], '+d')}**.", "",
        "## El soroll de la pilota lliure", "",
        f"La mediana del canvi de velocitat (k = 5) on la pilota és a 5 m o més de tothom: **{num(r['soroll_ms'])} m/s**,",
        f"el més proper al banc ×{r['nivell']:g}. Els del banc (`banc/resultats/tocs.md`):", "",
        "| Escenari | m/s |", "|---|---|", *[f"| ×{f:g} | {num(v)} |" for f, v in nivells.items()], ""]
    return "\n".join(linies)


def valida(t: llegeix.Tracking, h: Homografia, video: Path, detector: Detector, trams, sortida: Path,
           parla: Callable[[str], None], pas: int = PAS) -> dict:
    """Tot, amb el tracking en una fila per imatge (`senyals.a_reixa`). Escriu a `sortida` i torna les mesures."""
    inici = time.monotonic()
    camp = np.asarray(t.camp_m, float)
    ample, alt = videos.mida(video)
    frames = tria_mostra(t.pilota, trams, pas)
    matrius = h.de_frames(frames)
    atd_px = al_pixel(matrius, t.pilota[frames])
    dins = np.isfinite(matrius).all(axis=(1, 2)) & (atd_px[:, 0] >= 0) & (atd_px[:, 0] < ample) & \
        (atd_px[:, 1] >= 0) & (atd_px[:, 1] < alt)
    frames, matrius, atd_px = frames[dins], matrius[dins], atd_px[dins]
    nivells = nivells_del_banc()                        # abans del detector: si s'ha d'aturar, que sigui de seguida
    soroll = tocs.soroll_lliure(t, trams)
    atd_m = t.pilota[frames] * camp
    m = Mostra(frame=frames, atd_m=atd_m, atd_px=atd_px, diametre_px=diametre_px(matrius, atd_m, camp),
               cand_px=np.empty((len(frames), MAXIM, 3)), cand_m=np.empty((len(frames), MAXIM, 2)))
    parla("… El detector, al voltant de la pilota de l'ATD, una imatge per segon de joc")
    cand_px = passa_detector(video, m, detector, parla, pas, (ample, alt))
    m = Mostra(frame=m.frame, atd_m=m.atd_m, atd_px=m.atd_px, diametre_px=m.diametre_px, cand_px=cand_px,
               cand_m=al_camp(matrius, cand_px[..., :2], camp))
    parla("✓ La mostra, passada pel detector")
    r = {**mesures(m, t.pilota * camp), "fora": int((~dins).sum())}
    r["soroll_ms"] = soroll
    r["nivell"] = nivell(soroll, nivells)
    r["cas"] = cas(r)
    r["segons"] = time.monotonic() - inici
    grup = grups(m)
    sortida.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"frame": m.frame, "grup": grup, "atd_x_m": m.atd_m[:, 0], "atd_y_m": m.atd_m[:, 1],
                  "atd_u": m.atd_px[:, 0], "atd_v": m.atd_px[:, 1], "diametre_px": m.diametre_px,
                  "propera_m": distancies(m.cand_px, m.cand_m, m.atd_m)[0],
                  "primera_confianca": m.cand_px[:, 0, 2]}).to_csv(sortida / "mostra.csv", index=False)
    np.savez_compressed(sortida / "candidates.npz", frame=m.frame, cand_px=m.cand_px, cand_m=m.cand_m)
    (sortida / "resultat.json").write_text(json.dumps(r, indent=1, default=float), encoding="utf-8")
    (sortida / "informe.md").write_text(informe(r, nivells), encoding="utf-8")
    return r


def localitza(dades: Path, nom: str) -> Path:
    trobats = [c for c in dades.rglob(nom) if c.is_file()]
    if len(trobats) != 1:
        raise llegeix.ErrorDeLectura(f"No trobo un sol {nom}")
    return trobats[0]


def arguments() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="python -I -m pilota.valida", description=__doc__.splitlines()[0])
    p.add_argument("--dades", type=Path, required=True, help="carpeta on hi ha les dades, tal com arriben")
    p.add_argument("--sortida", type=Path, default=SORTIDA, help=f"on es desa tot (per defecte, {SORTIDA})")
    p.add_argument("--fils", type=int, default=None, help="fils del processador per al detector")
    p.add_argument("--permet-fora-del-volum", action="store_true", help=argparse.SUPPRESS)
    return p.parse_args()


def main() -> int:
    faulthandler.enable(sys.__stderr__)     # si Python cau (PyTorch, OpenMP), on era: només el codi, cap dada
    args = arguments()
    if not args.permet_fora_del_volum and not dins_del_volum(args.sortida):
        print(f"✗ La sortida ha de ser dins del volum xifrat ({VOLUM}), i el volum, muntat")
        return 1
    args.sortida.mkdir(parents=True, exist_ok=True)
    with temporals_dins(Path(tempfile.mkdtemp(prefix=".valida-", dir=args.sortida))):
        try:
            meta, raw = llegeix.localitza(args.dades)
            t = senyals.a_reixa(llegeix.tracking(meta, raw, EQUIP_CASA), N_FOTOGRAMES)
            h = homografia(localitza(args.dades, HOMOGRAFIA), "tactical")
            video = localitza(args.dades, VIDEO)
        except llegeix.ErrorDeLectura as error:
            print(f"✗ {error}")
            return 1
        except Exception as error:  # noqa: BLE001 - el missatge podria portar dades: només el tipus
            print(f"✗ No s'han pogut llegir les dades ({type(error).__name__})")
            return 1
        print("✓ L'ATD, l'homografia i el vídeo tàctic, llegits")
        try:
            from pilota.footandball import Detector as FootAndBall

            r = valida(t, h, video, FootAndBall(maxim=MAXIM, fils=args.fils), TRAMS_PUNTUATS, args.sortida, print)
        except Exception as error:  # noqa: BLE001
            print(f"✗ La validació s'ha aturat ({type(error).__name__})")
            return 1
    if r["desfasament"] is None:
        print("⚠ No s'ha pogut mirar si la pilota del vídeo i la de l'ATD van a la mateixa imatge")
    else:
        print("✓ La pilota del vídeo i la de l'ATD van a la mateixa imatge" if r["desfasament"] == 0 else
              "⚠ La pilota del vídeo i la de l'ATD no van a la mateixa imatge (quantes, a l'informe)")
    print(f"Cas {r['cas']}: {CASOS[r['cas']][0]}")
    print(f"Soroll de la pilota lliure: com el banc ×{r['nivell']:g}" if np.isfinite(r["nivell"]) else
          "⚠ No s'ha pogut mesurar el soroll de la pilota lliure")
    print(f"· L'informe és a {args.sortida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
