"""El volum xifrat de l'equip (D-05): on poden anar els fitxers que surten de les dades, i els temporals.

Sense cap biblioteca pesada: el fan servir eines que carreguen PyTorch (`pilota.valida`), i LightGBM i PyTorch no
poden conviure al mateix procés (cadascun porta el seu OpenMP, i Python cau).
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

VOLUM = Path("/Volumes/mtah-dades")
VARIABLES_TEMPORALS = ("TMPDIR", "JOBLIB_TEMP_FOLDER", "MPLCONFIGDIR")


def dins_del_volum(cami: Path) -> bool:
    return VOLUM.is_mount() and cami.resolve().is_relative_to(VOLUM.resolve())


def dins_de(cami: Path, carpeta: Path) -> bool:
    """Es compara el fitxer i no el text del camí: el disc no distingeix majúscules i hi pot haver enllaços."""
    return any(p.exists() and os.path.samefile(p, carpeta) for p in (cami, *cami.absolute().parents))


@contextmanager
def temporals_dins(carpeta: Path) -> Iterator[None]:
    """Que cap biblioteca no deixi temporals fora del volum, ni avisos a la consola. En sortir, ho desfà i ho esborra."""
    entorn_abans, tempdir_abans = {v: os.environ.get(v) for v in VARIABLES_TEMPORALS}, tempfile.tempdir
    os.environ.update(dict.fromkeys(VARIABLES_TEMPORALS, str(carpeta)))
    tempfile.tempdir = str(carpeta)
    logging.disable(logging.CRITICAL)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            yield
    finally:
        logging.disable(logging.NOTSET)
        tempfile.tempdir = tempdir_abans
        for variable, valor in entorn_abans.items():
            if valor is None:
                os.environ.pop(variable, None)
            else:
                os.environ[variable] = valor
        shutil.rmtree(carpeta, ignore_errors=True)
