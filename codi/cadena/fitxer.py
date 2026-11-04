"""El fitxer de possessió: escriure'l i comprovar-lo amb les regles de SUBMISSION.md.

Els motius d'un rebuig no porten cap xifra: surten a la consola.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import numpy as np

from cadena.norma import CAPCALERA, ETIQUETES


def escriu(cami: Path, etiquetes: np.ndarray) -> None:
    """Primer a un fitxer temporal al costat: un fitxer a mitges no queda mai amb el nom bo."""
    temporal = cami.with_name(cami.name + ".part")
    linies = [",".join(CAPCALERA)] + [f"{i},{e}" for i, e in enumerate(etiquetes)]
    temporal.write_text("\n".join(linies) + "\n", encoding="utf-8")
    temporal.replace(cami)


def comprova(cami: Path, n: int) -> str | None:
    """None si el fitxer és vàlid; si no, el motiu en una línia."""
    with cami.open(encoding="utf-8", newline="") as f:
        files = list(csv.reader(f))
    if not files or [c.strip().lower() for c in files[0]] != list(CAPCALERA):
        return "la capçalera no és frame,label"
    dades = files[1:]
    if len(dades) != n:
        return "no té el nombre de files que toca"
    if any(len(fila) != 2 for fila in dades):
        return "hi ha files que no tenen exactament dues columnes"
    # el text tal qual, i no int(): int() admet «０５», «0_5» o «+5», i l'oficial potser no
    for i, fila in enumerate(dades):
        valor = fila[0].strip()
        if valor != str(i):
            if valor.isascii() and valor.isdigit():
                return "la columna frame no va del primer fotograma a l'últim, en ordre"
            return "la columna frame no és de nombres enters escrits només amb xifres"
    etiquetes = [fila[1].strip().upper() for fila in dades]
    if "" in etiquetes:
        return "hi ha etiquetes buides (per abstenir-se, cal una X)"
    if set(etiquetes) - set(ETIQUETES):
        return "hi ha etiquetes que no són H, A, D ni X"
    return None


def empremta(cami: Path) -> str:
    resum = hashlib.sha256()
    with cami.open("rb") as f:
        while bloc := f.read(1 << 20):
            resum.update(bloc)
    return resum.hexdigest()
