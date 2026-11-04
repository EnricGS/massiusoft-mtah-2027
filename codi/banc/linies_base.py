"""Les quatre línies base de l'organització, refetes a partir de la descripció d'EVALUATION.md, sense `starter/`.

«Nearest tracked player to the ball, then a majority vote over a window», amb finestres d'1, 25, 50 i 125
imatges. Són les funcions de la cadena (`cadena.regla`): el que es mesura al banc és el que corre
sobre l'ATD. La descripció no diu què fan quan no hi ha pilota, i n'hi ha dues variants:
- «X»: s'abstenen, i la mètrica hi repeteix l'etiqueta anterior;
- «D»: hi diuen pilota morta.
"""

from __future__ import annotations

import numpy as np

from banc import avalua, fonts
from banc.partit import PartitBanc
from cadena import regla
from possessio.oficial import possession_metrics as pm

FINESTRES = {"raw": 1, "smooth25": 25, "smooth50": 50, "smooth125": 125}
SENSE_PILOTA = ("X", "D")
ORDRE_PUBLICAT = ("smooth50", "smooth125", "smooth25", "raw")      # per spellF1, al partit sencer (EVALUATION.md)


def codis(lletres: np.ndarray) -> np.ndarray:
    return np.select([lletres == "H", lletres == "A", lletres == "D"], [pm.H, pm.A, pm.D], pm.X).astype(np.int8)


def prediu(p: PartitBanc, finestra: int, sense_pilota: str = "X") -> np.ndarray:
    t = p.tracking
    etiquetes = regla.jugador_mes_proper(t.pilota, t.casa, t.fora, t.camp_m)
    if sense_pilota == "D":
        etiquetes = np.where(np.isnan(t.pilota[:, 0]), "D", etiquetes)
    return codis(regla.per_fotograma(t.fotograma, etiquetes, p.n, p.trams, finestra))


def metode(nom: str, sense_pilota: str):
    """La línia base com a mètode del banc: no aprèn res dels altres partits."""
    def prediu_prova(entrenament: tuple[str, ...], escenari: str, prova: PartitBanc) -> np.ndarray:
        return prediu(prova, FINESTRES[nom], sense_pilota)
    return prediu_prova


def metodes() -> dict[str, avalua.Metode]:
    return {f"{base}·{sense}": metode(base, sense) for sense in SENSE_PILOTA for base in FINESTRES}


def feina(escenari_i_partit: tuple[str, str]) -> list[dict]:
    """Totes les línies base en un partit i un escenari (és aquí i no a __main__ perquè la cridi un procés fill)."""
    escenari, nom = escenari_i_partit
    return avalua.avalua(metodes(), fonts.NOMS, escenari, proves=(nom,))
