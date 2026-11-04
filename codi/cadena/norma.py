"""El que fixen les normes públiques (repo oficial, commit f8f2629). Res d'aquí no surt de les dades."""

from __future__ import annotations

PARTIT = "BAR-ATH"
N_FOTOGRAMES = 199_319                                  # SUBMISSION.md: una fila per fotograma del vídeo tàctic
TRAMS_PUNTUATS = ((1, 11_185, 90_651), (2, 110_808, 190_197))   # DATA.md: (part, primer, últim), «boundaries, not answers»
ETIQUETES = ("H", "A", "D", "X")
CAPCALERA = ("frame", "label")
EQUIP_CASA = "barcelona"                                # DATA.md: H és l'equip de casa, el Barcelona
FITXERS_ATD = (f"{PARTIT}_tactical_atd.xml", f"{PARTIT}_tactical_atd.txt")   # DATA.md: metadades i dades
