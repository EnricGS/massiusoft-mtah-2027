"""El contingut d'una secció de l'informe: text, taules, comprovacions i figures.

Cada mòdul d'anàlisi torna una `Seccio`; `informe.py` la converteix en HTML.
"""

from __future__ import annotations

import base64
import io
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

MARGE_COMA_FLOTANT = 1e-9    # 0,25 − 0,24 fa una mica més de 0,01


@dataclass(frozen=True)
class Paragraf:
    text: str


@dataclass(frozen=True)
class Taula:
    titol: str
    capcalera: tuple[str, ...]
    files: tuple[tuple, ...]
    nota: str = ""


@dataclass(frozen=True)
class Comprovacio:
    que: str
    esperat: str
    trobat: str
    ok: bool | None          # None: no s'ha pogut comprovar

    def __post_init__(self) -> None:
        # numpy torna np.bool_, i `np.False_ is False` és fals: es normalitza perquè compti com a diferència.
        object.__setattr__(self, "ok", None if self.ok is None else bool(self.ok))


@dataclass(frozen=True)
class Figura:
    titol: str
    dades_b64: str
    tipus: str = "png"
    peu: str = ""


@dataclass(frozen=True)
class Preformat:
    titol: str
    text: str


@dataclass
class Seccio:
    titol: str
    blocs: list = field(default_factory=list)
    error: str = ""

    def text(self, text: str) -> None:
        self.blocs.append(Paragraf(text))

    def taula(self, titol: str, capcalera: tuple[str, ...], files, nota: str = "") -> None:
        self.blocs.append(Taula(titol, tuple(capcalera), tuple(tuple(f) for f in files), nota))

    def comprovacions(self, llista: list[Comprovacio]) -> None:
        self.blocs.append(tuple(llista))

    def preformat(self, titol: str, text: str) -> None:
        self.blocs.append(Preformat(titol, text))

    def figura(self, titol: str, fig, peu: str = "", tipus: str = "png") -> None:
        self.blocs.append(Figura(titol, figura_b64(fig, tipus), tipus, peu))

    @property
    def diferencies(self) -> int:
        return sum(1 for b in self.blocs if isinstance(b, tuple)
                   for c in b if isinstance(c, Comprovacio) and c.ok is False)


def figura_b64(fig, tipus: str = "png") -> str:
    memoria = io.BytesIO()
    opcions = {"pil_kwargs": {"quality": 85}} if tipus == "jpeg" else {}
    fig.savefig(memoria, format=tipus, dpi=fig.dpi, bbox_inches="tight", **opcions)
    plt.close(fig)
    return base64.b64encode(memoria.getvalue()).decode("ascii")


def executa(titol: str, funcio: Callable[[Seccio], None]) -> Seccio:
    """Omple una secció; si falla, l'error queda a l'informe i no atura les altres."""
    seccio = Seccio(titol)
    try:
        funcio(seccio)
    except Exception:  # noqa: BLE001 - l'informe ha de seguir amb la resta
        seccio.error = traceback.format_exc()
        plt.close("all")
    return seccio


def comprova_igual(que: str, esperat, trobat) -> Comprovacio:
    return Comprovacio(que, xifra(esperat), xifra(trobat), esperat == trobat)


def comprova_aprop(que: str, esperat: float, trobat: float, tolerancia: float,
                   unitat: str = "") -> Comprovacio:
    ok = abs(esperat - trobat) <= tolerancia + MARGE_COMA_FLOTANT
    return Comprovacio(que, f"{xifra(esperat)}{unitat}", f"{xifra(trobat)}{unitat}", ok)


def xifra(valor) -> str:
    """Números a la catalana: punt de milers i coma decimal."""
    if isinstance(valor, bool):
        return "sí" if valor else "no"
    if isinstance(valor, tuple):
        return " × ".join(xifra(v) for v in valor)
    if not isinstance(valor, (int, float)):
        return str(valor)
    if isinstance(valor, int) or float(valor).is_integer():
        return f"{int(valor):,}".replace(",", ".")
    text = f"{valor:,.2f}" if abs(valor) < 10 else f"{valor:,.1f}"
    return text.replace(",", "·").replace(".", ",").replace("·", ".")


def diferencies(n: int) -> str:
    return f"{n} diferència" if n == 1 else f"{n} diferències"


def pct(part: float, tot: float) -> float:
    return 100.0 * part / tot if tot else float("nan")
