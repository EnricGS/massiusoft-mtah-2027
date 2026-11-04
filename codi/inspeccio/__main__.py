"""Informe local de les dades del concurs. L'executa l'equip, en local.

    cd codi && uv run python -I -m inspeccio --dades "<carpeta de les dades>"

Escriu l'informe (HTML) i l'inventari dins del volum xifrat. A la consola només
surt si cada secció ha anat bé: cap xifra de les dades.
"""

from __future__ import annotations

import argparse
import logging
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import warnings
from importlib import metadata
from pathlib import Path

from inspeccio import atd, carrega, creuat, etiquetatge, fitxers, homografia, informe, oficial, video
from inspeccio.esperat import ESPERAT, Esperat
from inspeccio.seccio import Seccio, executa

VOLUM = Path("/Volumes/mtah-dades")


def arguments() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="python -I -m inspeccio", description=__doc__.splitlines()[0])
    p.add_argument("--dades", type=Path, required=True, help="carpeta on hi ha les dades, tal com arriben")
    p.add_argument("--sortida", type=Path, default=VOLUM / "informes",
                   help=f"on es desa l'informe (per defecte, {VOLUM / 'informes'})")
    p.add_argument("--oficial", action="store_true",
                   help="clona el repo oficial i hi torna a fer les línies base (cal xarxa)")
    p.add_argument("--sense-captures", action="store_true", help="no extreu fotogrames del vídeo")
    p.add_argument("--permet-fora-del-volum", action="store_true", help=argparse.SUPPRESS)
    return p.parse_args()


def dins_del_volum(cami: Path) -> bool:
    return VOLUM.is_mount() and cami.resolve().is_relative_to(VOLUM.resolve())


def temporals_a(carpeta: Path) -> None:
    """Que cap biblioteca no deixi temporals fora del volum, ni avisos a la consola."""
    carpeta.mkdir(parents=True, exist_ok=True)
    for variable in ("TMPDIR", "JOBLIB_TEMP_FOLDER", "MPLCONFIGDIR"):
        os.environ[variable] = str(carpeta)
    tempfile.tempdir = str(carpeta)
    warnings.simplefilter("ignore")
    logging.disable(logging.CRITICAL)


def necessari(cami: Path | None, nom: str) -> Path:
    if cami is None:
        raise FileNotFoundError(f"Falta {nom}")
    return cami


def versions() -> dict[str, str]:
    paquets = {p: metadata.version(p) for p in ("kloppy", "numpy", "pandas", "matplotlib")}
    try:
        ffmpeg = subprocess.run([video.eina("ffmpeg"), "-version"], capture_output=True, text=True,
                                timeout=30).stdout.split()[2]
    except (OSError, IndexError, subprocess.SubprocessError):
        ffmpeg = "no trobat"
    return {"Python": platform.python_version(), **paquets, "ffmpeg": ffmpeg}


def avisa(s: Seccio) -> None:
    if s.error:
        print(f"✗ {s.titol}: ha fallat (el detall és a l'informe)", flush=True)
    elif s.diferencies:
        print(f"⚠ {s.titol}: difereix de la documentació (el detall és a l'informe)", flush=True)
    else:
        print(f"✓ {s.titol}", flush=True)


def requereix(estat: dict, clau: str, que: str):
    if clau not in estat:
        raise RuntimeError(f"Cal {que}, que no s'ha pogut llegir (vegeu la seva secció)")
    return estat[clau]


def passos(dades: Path, sortida: Path, camins: dict, esperat: Esperat, captures: bool) -> list:
    """(títol, funció que omple la secció). Les primeres deixen a `estat` el que fan servir les altres."""
    tac, bro, estat = camins["tactical"], camins["broadcast"], {}

    def atd_tactic(s: Seccio) -> None:
        t = carrega.tracking(necessari(tac["atd_meta"], "l'XML de l'ATD tàctic"),
                             necessari(tac["atd_raw"], "el TXT de l'ATD tàctic"), "tactical")
        estat["t"] = t
        estat["forats"] = atd.forats_pilota(t, atd.mascara(t, esperat), esperat)
        atd.omple(s, t, tac["atd_meta"], esperat, estat["forats"])

    def homografia_tactica(s: Seccio) -> None:
        estat["h"] = carrega.homografia(necessari(tac["homografia"], "la homografia tàctica"), "tactical")
        homografia.omple(s, estat["h"], estat.get("t"), esperat)

    def smart_tagging(s: Seccio) -> None:
        estat["etiquetes"] = etiquetatge.omple(s, necessari(tac["etiquetatge"], "el Smart Tagging"), esperat)

    def creuat_(s: Seccio) -> None:
        creuat.omple(s, requereix(estat, "t", "l'ATD tàctic"), requereix(estat, "forats", "l'ATD tàctic"),
                     requereix(estat, "etiquetes", "el Smart Tagging"), esperat)

    def videos(s: Seccio) -> None:
        video.omple(s, {"tactical": tac["video"], "broadcast": bro["video"]},
                    estat.get("t") if captures else None, estat.get("h"), estat.get("forats"), esperat)

    def atd_broadcast(s: Seccio) -> None:
        t = carrega.tracking(necessari(bro["atd_meta"], "l'XML de l'ATD broadcast"),
                             necessari(bro["atd_raw"], "el TXT de l'ATD broadcast"), "broadcast")
        atd.omple(s, t, bro["atd_meta"], esperat)

    def homografia_broadcast(s: Seccio) -> None:
        h = carrega.homografia(necessari(bro["homografia"], "la homografia broadcast"), "broadcast")
        homografia.omple(s, h, None, esperat)

    return [
        ("Fitxers i inventari", lambda s: fitxers.omple(s, dades, sortida, camins)),
        ("ATD tàctic", atd_tactic),
        ("Homografia tàctica", homografia_tactica),
        ("Smart Tagging", smart_tagging),
        ("Forats de la pilota i Smart Tagging", creuat_),
        ("Vídeos", videos),
        ("ATD broadcast", atd_broadcast),
        ("Homografia broadcast", homografia_broadcast),
    ]


def inspecciona(dades: Path, sortida: Path, esperat: Esperat = ESPERAT, captures: bool = True,
                amb_oficial: bool = False, parla=avisa) -> tuple[list[Seccio], Path]:
    camins = fitxers.localitza(dades)
    llista = passos(dades, sortida, camins, esperat, captures)
    if amb_oficial:
        llista.append(("Codi oficial sobre aquestes dades", lambda s: oficial.omple(s, camins, sortida)))
    seccions = []
    for titol, pas in llista:
        print(f"… {titol}", flush=True)
        seccions.append(executa(titol, pas))
        parla(seccions[-1])
    return seccions, informe.desa(seccions, dades, sortida, versions())


def main() -> int:
    args = arguments()
    if not args.dades.is_dir():
        print(f"✗ No trobo la carpeta {args.dades}")
        return 1
    if not (dins_del_volum(args.sortida) or args.permet_fora_del_volum):
        print(f"✗ L'informe porta extractes de les dades: ha d'anar dins de {VOLUM}, i el volum ha de ser muntat")
        return 1
    dades, sortida = args.dades.resolve(), args.sortida.resolve()
    if sortida.is_relative_to(dades):
        print("✗ La sortida no pot ser dins de la carpeta de les dades: l'inventari la llegiria")
        return 1
    sortida.mkdir(parents=True, exist_ok=True)
    temporals_a(sortida / "tmp")
    try:
        seccions, cami = inspecciona(dades, sortida, captures=not args.sense_captures, amb_oficial=args.oficial)
    except Exception as error:  # noqa: BLE001 - el missatge de l'error pot portar dades: no s'imprimeix
        print(f"✗ Error intern ({type(error).__name__}); no hi ha informe")
        return 1
    finally:
        shutil.rmtree(sortida / "tmp", ignore_errors=True)
    print(f"\nInforme: {cami}\nObre'l tu (open \"{cami}\"). No el passis a cap LLM al núvol.")
    return 1 if any(s.error for s in seccions) else 0


if __name__ == "__main__":
    sys.exit(main())
