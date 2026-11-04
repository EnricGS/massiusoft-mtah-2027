"""Opcional (`--oficial`): el codi oficial sobre aquestes dades.

Clona el repo públic al commit llegit, li prepara la carpeta `data/` que espera
`games.py` (enllaços als fitxers, sense copiar-los), torna a fer les quatre línies
base i les puntua amb la veritat pública de 5 minuts. Si les línies base surten
idèntiques a les publicades, les dades són les mateixes que les de l'organització.

Tot queda dins de la carpeta de sortida, que és al volum xifrat.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

from inspeccio.esperat import COMMIT_OFICIAL, REPO_OFICIAL
from inspeccio.seccio import Comprovacio, Seccio

MINUTS_MAX = 60
RESULTATS = "evaluation/results"


def git(*arguments: str, on: Path | None = None) -> str:
    ordre = ["git", *(["-C", str(on)] if on else []), *arguments]
    return subprocess.run(ordre, capture_output=True, text=True, check=True, timeout=600).stdout.strip()


def prepara_repo(repo: Path, url: str, commit: str) -> str:
    if not repo.exists():
        git("clone", "--quiet", url, str(repo))
    if git("remote", "get-url", "origin", on=repo) != url:
        raise RuntimeError(f"{repo} és un clon d'un altre repo: esborra'l i torna-ho a provar")
    git("checkout", "--quiet", commit, on=repo)
    git("checkout", "--quiet", "--", ".", on=repo)    # desfà una execució anterior
    git("clean", "-fdq", on=repo)
    if git("rev-parse", "HEAD", on=repo) != commit:
        raise RuntimeError(f"El repo no és al commit {commit}")
    return commit[:7]


def prepara_dades(dades: Path, camins: dict[str, dict[str, Path | None]]) -> None:
    for font, claus in camins.items():
        carpeta = dades / font
        carpeta.mkdir(parents=True, exist_ok=True)
        for cami in filter(None, claus.values()):
            enllac = carpeta / cami.name
            if enllac.is_symlink() or enllac.exists():
                enllac.unlink()
            enllac.symlink_to(cami)


def executa(repo: Path, dades: Path, script: str) -> tuple[int, str]:
    temporals = repo.parent / "tmp-oficial"
    temporals.mkdir(exist_ok=True)
    entorn = {**os.environ, "MTAH_DATA_DIR": str(dades),
              **{v: str(temporals) for v in ("TMPDIR", "JOBLIB_TEMP_FOLDER", "MPLCONFIGDIR")}}
    resultat = subprocess.run([sys.executable, "-B", script], cwd=repo, env=entorn, capture_output=True,
                              text=True, timeout=MINUTS_MAX * 60)
    return resultat.returncode, (resultat.stdout + resultat.stderr).strip()


def omple(seccio: Seccio, camins: dict, sortida: Path, url: str = REPO_OFICIAL,
          commit: str = COMMIT_OFICIAL) -> None:
    repo, dades = sortida / "repo-oficial", sortida / "dades-oficial"
    commit = prepara_repo(repo, url, commit)
    prepara_dades(dades, camins)
    seccio.text(f"Repo oficial a `{repo}`, commit `{commit}`. Carpeta de dades per a `MTAH_DATA_DIR`: "
                f"`{dades}` (només enllaços).")
    abans = time.time()
    codi, text = executa(repo, dades, "starter/baseline.py")
    seccio.preformat("python starter/baseline.py", text or "(sense sortida)")
    refets = sorted(str(f.relative_to(repo)) for f in (repo / RESULTATS).glob("*.csv")
                    if f.stat().st_mtime >= abans)
    canviats = git("status", "--porcelain", "--", *refets, on=repo) if refets else ""
    seccio.comprovacions([
        Comprovacio("starter/baseline.py acaba bé", "codi 0", f"codi {codi}", codi == 0),
        Comprovacio(f"CSV de `{RESULTATS}` tornats a escriure", "els 4 de les línies base",
                    ", ".join(refets) or "cap", len(refets) == 4),
        Comprovacio("i són idèntics als publicats", "cap canvi", canviats or "cap canvi",
                    (not canviats) if refets else None),
    ])
    seccio.preformat("git status (tot el repo)", git("status", "--short", on=repo) or "net")
    codi, text = executa(repo, dades, "evaluation/run_evaluation.py")
    seccio.preformat("python evaluation/run_evaluation.py", text or "(sense sortida)")
    seccio.comprovacions([Comprovacio("evaluation/run_evaluation.py acaba bé", "codi 0", f"codi {codi}",
                                      codi == 0)])
