"""On és cada fitxer i l'inventari de tot el que ha arribat (mida i SHA-256).

L'inventari serveix per saber quines còpies hi ha, per poder
comprovar una còpia i, al final, esborrar-ho tot (clàusula 8).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from inspeccio.esperat import FITXERS
from inspeccio.seccio import Comprovacio, Seccio, xifra

BLOC = 8 * 1024 * 1024


@dataclass(frozen=True)
class Fitxer:
    cami: Path
    relatiu: str
    bytes: int
    sha256: str


def localitza(dades: Path) -> dict[str, dict[str, Path | None]]:
    """Busca cada fitxer pel nom, sigui a la carpeta que sigui."""
    trobats: dict[str, list[Path]] = {}
    for cami in sorted(dades.rglob("*")):
        if cami.is_file():
            trobats.setdefault(cami.name, []).append(cami)
    return {font: {clau: (trobats.get(nom) or [None])[0] for clau, nom in noms.items()}
            for font, noms in FITXERS.items()}


def duplicats(dades: Path) -> list[str]:
    noms = [c.name for c in dades.rglob("*") if c.is_file() and not c.name.startswith(".")]
    return sorted({n for n in noms if noms.count(n) > 1})


def sha256(cami: Path) -> str:
    resum = hashlib.sha256()
    with cami.open("rb") as f:
        while bloc := f.read(BLOC):
            resum.update(bloc)
    return resum.hexdigest()


def inventari(dades: Path) -> list[Fitxer]:
    return [Fitxer(c, str(c.relative_to(dades)), c.stat().st_size, sha256(c))
            for c in sorted(dades.rglob("*")) if c.is_file()]


def mida(bytes_: int) -> str:
    for unitat, factor in (("GB", 1e9), ("MB", 1e6), ("kB", 1e3)):
        if bytes_ >= factor:
            return f"{xifra(round(bytes_ / factor, 2))} {unitat}"
    return f"{bytes_} B"


def desa_inventari(fitxers: list[Fitxer], dades: Path, sortida: Path) -> None:
    ara = datetime.now().strftime("%d-%m-%Y %H:%M")
    linies = [
        "# Inventari de les dades del concurs", "",
        f"Fet el {ara} sobre `{dades}`.", "",
        "Al final del concurs (clàusula 8) s'han d'esborrar aquests fitxers i totes les còpies,",
        "derivats, incrustacions i pesos que se n'hagin fet. Aquest fitxer és dins del volum xifrat.", "",
        "| Fitxer | Mida | SHA-256 |", "|---|---:|---|",
        *[f"| `{f.relatiu}` | {mida(f.bytes)} | `{f.sha256}` |" for f in fitxers],
    ]
    (sortida / "INVENTARI.md").write_text("\n".join(linies) + "\n", encoding="utf-8")
    (sortida / "inventari.json").write_text(json.dumps(
        [{"fitxer": f.relatiu, "bytes": f.bytes, "sha256": f.sha256} for f in fitxers],
        ensure_ascii=False, indent=1), encoding="utf-8")


def omple(seccio: Seccio, dades: Path, sortida: Path, camins: dict) -> None:
    fitxers = inventari(dades)
    desa_inventari(fitxers, dades, sortida)
    seccio.text(f"Carpeta: `{dades}`. {len(fitxers)} fitxers, "
                f"{mida(sum(f.bytes for f in fitxers))} en total. L'inventari amb els SHA-256 "
                "és a `INVENTARI.md`, al costat d'aquest informe.")
    seccio.comprovacions([
        Comprovacio(f"{font} · {FITXERS[font][clau]}", "hi és",
                    str(cami.relative_to(dades)) if cami else "no hi és", cami is not None)
        for font, claus in camins.items() for clau, cami in claus.items()
    ] + [Comprovacio("noms repetits", "cap", ", ".join(duplicats(dades)) or "cap",
                     not duplicats(dades))])
    coneguts = {c for claus in camins.values() for c in claus.values() if c}
    altres = [f for f in fitxers if f.cami not in coneguts]
    if altres:
        seccio.taula("Fitxers que DATA.md no esmenta", ("Fitxer", "Mida"),
                     [(f"`{f.relatiu}`", mida(f.bytes)) for f in altres])
    seccio.taula("Tots els fitxers", ("Fitxer", "Mida", "SHA-256 (inici)"),
                 [(f"`{f.relatiu}`", mida(f.bytes), f"`{f.sha256[:16]}…`")
                  for f in fitxers])
