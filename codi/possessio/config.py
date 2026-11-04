"""Configuració central: camins, constants físiques i paràmetres per defecte.

Tot el que és un llindar o una mida es defineix aquí perquè els experiments
siguin reproduïbles i fàcils d'ajustar quan arribin les dades del hackathon.
"""

from __future__ import annotations

from pathlib import Path

# --- Camins -----------------------------------------------------------------
ARREL_PROJECTE = Path(__file__).resolve().parents[2]
DIR_DADES = ARREL_PROJECTE / "dades" / "metrica-sample" / "data"
DIR_FIGURES = ARREL_PROJECTE / "figures" / "possessio"
DIR_CODI = Path(__file__).resolve().parent
DIR_CACHE = DIR_CODI / ".cache"
FITXER_RESULTATS = DIR_CODI / "results.json"

# --- Camp i temps -----------------------------------------------------------
LLARG_CAMP_M = 105.0
AMPLE_CAMP_M = 68.0
FPS = 25
DT = 1.0 / FPS

# --- Classes ----------------------------------------------------------------
HOME, AWAY, ATURAT = 0, 1, 2
NOMS_CLASSES = {HOME: "Home", AWAY: "Away", ATURAT: "Aturat"}
SENSE_ETIQUETA = -1  # frames abans del primer servei de cada part

# --- Forats de pilota -------------------------------------------------------
# Classificació de forats (NaN) de la pilota segons la durada, en frames.
FORAT_CURT_MAX = 12      # <= 0,5 s: oclusió puntual
FORAT_MITJA_MAX = 75     # <= 3 s: oclusió llarga / pilota alta
# > 3 s: forat llarg (sovint pilota fora o joc aturat)

# --- Features ---------------------------------------------------------------
RADIS_M = (2.0, 5.0, 10.0)
DESFASAMENTS_FRAMES = (-50, -25, -12, 12, 25, 50)   # ±0,5 s, ±1 s, ±2 s
FINESTRES_FRAMES = (13, 25, 51)                     # ~0,5 s, 1 s, 2 s
SUAVITZAT_VELOCITAT_FRAMES = 5
TOC_DIST_MAX_M = 2.5          # un "toc" requereix un jugador a prop
TOC_CANVI_DIRECCIO_GRAUS = 25.0
TOC_CANVI_VELOCITAT_MS = 2.0

# --- Avaluació ---------------------------------------------------------------
FINESTRA_TRANSICIO_FRAMES = FPS   # "a menys d'1 s d'un canvi de possessió"
LLAVOR = 20271009
