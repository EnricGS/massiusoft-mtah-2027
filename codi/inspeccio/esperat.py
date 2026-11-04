"""Què diu la documentació pública que hi ha d'haver (repo oficial, commit f8f2629).

Tots els valors surten de DATA.md, EVALUATION.md i SUBMISSION.md, que són públics.
L'informe compara el que troba amb això; cap valor d'aquí no surt de les dades.
"""

from __future__ import annotations

from dataclasses import dataclass, field

PARTIT = "BAR-ATH"
COMMIT_OFICIAL = "f8f2629ff1e0985f81d7e59d8413678514ee1530"
REPO_OFICIAL = "https://github.com/metrica-sports/more-than-a-hack-2027"

# Noms dels fitxers tal com arriben (DATA.md, «Getting it»).
FITXERS = {
    "tactical": {
        "video": f"{PARTIT}_tactical.mp4",
        "atd_meta": f"{PARTIT}_tactical_atd.xml",
        "atd_raw": f"{PARTIT}_tactical_atd.txt",
        "homografia": f"{PARTIT}_tactical_homography.csv",
        "etiquetatge": f"{PARTIT}_tactical_smart_tagging.xml",
    },
    "broadcast": {
        "video": f"{PARTIT}_broadcast.mp4",
        "atd_meta": f"{PARTIT}_broadcast_atd.xml",
        "atd_raw": f"{PARTIT}_broadcast_atd.txt",
        "homografia": f"{PARTIT}_broadcast_homography.csv",
    },
}


@dataclass(frozen=True)
class Esperat:
    fps: int = 25
    amplada_px: int = 1920
    alcada_px: int = 1080
    camp_m: tuple[float, float] = (105.3, 68.0)      # games.py; les metadades diuen 105 × 68
    # (part, primer fotograma, últim fotograma), en fotogrames del vídeo tàctic
    rangs_puntuats: tuple[tuple[int, int, int], ...] = ((1, 11185, 90651), (2, 110808, 190197))
    fotogrames: dict = field(default_factory=lambda: {"tactical": 199319, "broadcast": 164488})
    slots: dict = field(default_factory=lambda: {"tactical": 46, "broadcast": 51})
    pilota_visible_pct: dict = field(default_factory=lambda: {"tactical": 56.9, "broadcast": 50.5})
    pilota_visible_puntuats: tuple[int, int] = (94214, 158857)
    pilota_visible_tots: tuple[int, int] = (113488, 199319)
    objectes_mitjana_puntuats: float = 20.5
    homografia_valida_pct: dict = field(default_factory=lambda: {"tactical": 100.0, "broadcast": 65.8})
    homografia_trams_invalids_broadcast: int = 122
    homografia_tram_mes_llarg_broadcast_s: float = 90.0   # «over a minute and a half»
    error_reprojeccio_mediana_joc: float = 0.24
    error_reprojeccio_descans: float = 1.5               # «about 1.5»
    error_reprojeccio_max_broadcast: float = 304.0
    etiquetatge_instancies: int = 638
    etiquetatge_codis: dict = field(default_factory=lambda: {
        "PLAYERS IN THE BOX": 97, "BALL IN FINAL THIRD": 93, "BALL IN THE BOX": 72,
        "PROGRESSION": 66, "DEFENDING IN MIDDLE THIRD": 66, "SET PIECES": 59,
        "CREATING CHANCES": 30, "DEFENDING IN DEFENSIVE THIRD": 30, "LONG BALL": 29,
        "ATTACKING TRANSITION": 24, "DEFENSIVE TRANSITION": 24, "BUILD UP": 22,
        "DEFENDING IN ATTACKING THIRD": 22, "GOALS": 4,
    })
    etiquetatge_equip: dict = field(default_factory=lambda: {
        "Barcelona": 314, "Atletic Club": 288, "N/A": 36,
    })
    etiquetatge_tipus: dict = field(default_factory=lambda: {
        "Throw-in": 26, "Corner Kick": 12, "Goal Kick": 10, "Free Kick": 5,
        "Kick Off (After Goal)": 4, "Kick Off (Start)": 2,
    })

    @property
    def frames_puntuats(self) -> int:
        return sum(fi - inici + 1 for _, inici, fi in self.rangs_puntuats)


ESPERAT = Esperat()

# Llindars de l'anàlisi (no són normes: només com s'agrupa el que es mira).
DIAMETRE_PILOTA_M = 0.22
TRAMS_FORAT_S = (0.2, 1.0, 3.0, 10.0, 30.0)    # límits dels grups de forats de la pilota
VELOCITAT_PILOTA_MAX_MS = 40.0                  # per sobre, un salt de detecció
VELOCITAT_JUGADOR_MAX_MS = 12.0                 # per sobre, un canvi d'identitat del slot
CAPTURES_PER_GRUP = 3
