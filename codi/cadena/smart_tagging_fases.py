"""El Smart Tagging del partit a la cadena, amb les fases (la C2 del pla «A girat amb fases, a la cadena»,
`docs/pla-tocs.md`; D-76): on és el fitxer, les pilotes aturades i les fases que diuen l'equip que té la pilota.

- **On és** (`localitza`): pel nom de DATA.md (`smart_tagging.FITXER`), a qualsevol lloc de la carpeta de les dades,
  i només un.
- **Les pilotes aturades** i els seus avisos són els de `smart_tagging.llegeix` (T3af), tal qual.
- **Les fases** (`fases.CODIS`: Build Up, Progression…), amb el seu equip (`fases`), com les pilotes aturades: els
  segons passen a imatges amb `round(segons × 25)`, i «Barcelona» és l'H i «Atletic Club», l'A, sense distingir
  majúscules. Una fase sense equip («N/A», o sense l'etiqueta) no hi va: no se sap de qui és. D'un equip que no és cap
  dels dos, es deixa amb un avís de text fix (`AVIS_EQUIP_FASE`). Les de defensar i les altres no hi van (`fases.py`).

Va a part de `smart_tagging.py` perquè els bancs del Smart Tagging (de la T3af a la T3am) porten aquell fitxer sencer
a la seva clau: tocar-lo els faria tornar a fer, i el que fan no canviaria. Si el fitxer no hi és o és mal fet,
`ErrorDeLectura` amb un text fix. Cap missatge no porta res del fitxer.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from cadena import fases as fs
from cadena import smart_tagging as st
from cadena.llegeix import ErrorDeLectura

AVIS_EQUIP_FASE = "⚠ Smart Tagging: una fase d'un equip que no és cap dels dos; es deixa"
MAL_FET = "El Smart Tagging no es pot llegir: no és un fitxer SportsCode com diu DATA.md"


class Llegit(NamedTuple):
    etiquetes: tuple[st.Etiqueta, ...]  # les pilotes aturades
    fases: tuple[fs.Fase, ...]          # les fases amb equip
    avisos: tuple[str, ...]             # els de les pilotes aturades i, després, els de les fases


def localitza(dades: Path) -> Path:
    """El fitxer del Smart Tagging, pel nom exacte de DATA.md, a qualsevol lloc de `dades`."""
    trobats = [c for c in Path(dades).rglob(st.FITXER) if c.is_file()]
    if not trobats:
        raise ErrorDeLectura(f"No trobo el Smart Tagging ({st.FITXER})")
    if len(trobats) > 1:
        raise ErrorDeLectura(f"Hi ha més d'un {st.FITXER}")
    return trobats[0]


def fases(cami: Path) -> tuple[tuple[fs.Fase, ...], tuple[str, ...]]:
    """Les fases amb equip del fitxer, en l'ordre del fitxer, i els avisos."""
    from kloppy import sportscode

    if not Path(cami).is_file():
        raise ErrorDeLectura(f"No trobo el Smart Tagging ({st.FITXER})")
    try:
        crues = [(str(c.code).strip().lower(), {str(k).strip().lower(): str(v).strip() for k, v in c.labels.items()},
                  (c.period.start_timestamp + c.timestamp).total_seconds(),
                  (c.period.start_timestamp + c.end_timestamp).total_seconds())
                 for c in sportscode.load(str(cami)).records]
    except Exception as e:                                    # el text de l'excepció pot portar el que diu el fitxer
        raise ErrorDeLectura(MAL_FET) from e
    fetes, avisos = [], []
    for codi, etiquetes, inici, final in crues:
        if codi not in fs.CODIS:
            continue
        nom = etiquetes.get("team", st.SENSE_EQUIP).lower()
        if nom in st.EQUIPS:
            fetes.append(fs.Fase(st.imatge(inici), st.imatge(final), st.EQUIPS[nom]))
        elif nom != st.SENSE_EQUIP:
            avisos.append(AVIS_EQUIP_FASE)
    return tuple(fetes), tuple(avisos)


def llegeix(cami: Path) -> Llegit:
    """Les pilotes aturades i les fases amb equip del fitxer, i els avisos de totes dues."""
    etiquetes, avisos = st.llegeix(cami)
    de_les_fases, avisos_fases = fases(cami)
    return Llegit(etiquetes, de_les_fases, (*avisos, *avisos_fases))
