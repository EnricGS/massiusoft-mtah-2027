"""La figura del decodificador del document tècnic: dos minuts d'un partit del banc, en l'escenari barrejat ×¼.

    cd codi && uv run python -I -m banc.figura_decodificador ../entrega/document/figures/decoder.svg

Imatge a imatge, amb A girat amb fases, el model de la cadena (D-76): la veritat de toc; el Smart Tagging simulat del
nivell mitjà (les fases amb el seu equip i les pilotes aturades); el que diu el model sense decodificar (la classe
més probable de la relativa, amb el Smart Tagging i la D impossible, λ = 0 i durada mínima 1); la q del classificador
de canvis (la probabilitat que l'equip canviï a prop); el mateix decodificat; i on no hi ha pilota que serveixi (la
que falta al tracking degradat i la que la neteja treu). El partit, la part i el minut els tria la llavor `LLAVOR`,
no qui fa la figura. Tot ve del banc de la T3am, com al resum (`resum_girat.relativa_final`): les probabilitats
d'A camp girat de la memòria cau, de peces que no han vist el partit, i el decodificador, la pilota morta i les
fases que hi tria el banc per a aquest partit amb els altres nou. Si els resultats no són del codi d'ara, s'atura.
Tot són dades obertes.
"""

from __future__ import annotations

import argparse
from html import escape
from pathlib import Path
from typing import NamedTuple

import numpy as np

from banc import fases_simulades as fsm
from banc import fonts
from banc import model_girat_fases as mgf
from banc import model_neteja_aire as mna
from banc import model_pilotes_aturades as mpa
from banc import resum_girat as rg
from banc import veritat_toc as vt
from possessio.oficial import possession_metrics as pm

LLAVOR = 20271024
ESCENARI = "barreja ×¼"
FINESTRA = 120 * pm.FPS                  # dos minuts
CADA_TIC = 15 * pm.FPS
NIVELLS_Q = 8                            # la q, en vuit tons
OPACITAT_FASE = 0.45                     # les fases, més clares que els codis

AMPLADA, X_FRANJA, DRETA = 672, 164, 648
COLORS = {pm.H: "#2a78d6", pm.A: "#eb6834", pm.D: "#8f9391"}     # H i A validats (dataviz); D, el neutre
INK, MUTED, SOFT, RULE = "#1c1f1e", "#4b5351", "#5f6765", "rgba(28,31,30,0.16)"


class Smart(NamedTuple):
    """El Smart Tagging en imatges del partit: les fases (equip, primera, última) i les pilotes aturades (primera,
    última)."""
    fases: tuple[tuple[int, int, int], ...]
    pilotes: tuple[tuple[int, int], ...]


def tria(rng: np.random.Generator) -> tuple[str, int, int, int]:
    """El partit, la part, la primera imatge de la part i la primera de la finestra."""
    nom = str(rng.choice(fonts.NOMS))
    trams = fonts.partit(nom).trams
    part, inici, fi = trams[int(rng.integers(len(trams)))]
    return nom, part, inici, int(rng.integers(inici, fi - FINESTRA + 2))


def trams_de(codis: np.ndarray) -> list[tuple[int, int, int]]:
    """(codi, primera, última) de cada tram de codis iguals seguits."""
    vores = np.flatnonzero(np.diff(codis) != 0) + 1
    inicis, finals = np.r_[0, vores], np.r_[vores, len(codis)] - 1
    return [(int(codis[a]), int(a), int(b)) for a, b in zip(inicis, finals)]


def possessions(codis: np.ndarray) -> int:
    return sum(c in (pm.H, pm.A) for c, _, _ in trams_de(codis))


def franja(codis: np.ndarray, y: int, alt: int) -> list[str]:
    escala = (DRETA - X_FRANJA) / len(codis)
    return [f'<rect x="{X_FRANJA + a * escala:.2f}" y="{y}" width="{(b - a + 1) * escala:.2f}" height="{alt}" '
            f'fill="{COLORS[c]}"/>' for c, a, b in trams_de(codis) if c in COLORS]


def franja_q(q: np.ndarray, y: int, alt: int) -> list[str]:
    """La q en `NIVELLS_Q` tons de tinta: com més fosc, més probable que l'equip canviï a prop."""
    escala = (DRETA - X_FRANJA) / len(q)
    nivells = np.rint(np.clip(q, 0.0, 1.0) * NIVELLS_Q).astype(np.int8)
    return [f'<rect x="{X_FRANJA + a * escala:.2f}" y="{y}" width="{(b - a + 1) * escala:.2f}" height="{alt}" '
            f'fill="{INK}" fill-opacity="{n / NIVELLS_Q:.3f}"/>' for n, a, b in trams_de(nivells) if n > 0]


def franja_st(smart: Smart, inici: int, y: int, alt: int) -> list[str]:
    """El Smart Tagging dins de la finestra que comença a `inici`: les fases, clares, amb el color del seu equip, i
    les pilotes aturades a sobre, del color de la D. El que cau fora de la finestra es retalla."""
    escala = (DRETA - X_FRANJA) / FINESTRA
    trossos = [(COLORS[equip], a, b, True) for equip, a, b in smart.fases] + \
              [(COLORS[pm.D], a, b, False) for a, b in smart.pilotes]
    out = []
    for color, a, b, clara in trossos:
        a, b = max(a, inici), min(b, inici + FINESTRA - 1)
        if a > b:
            continue
        opacitat = f' fill-opacity="{OPACITAT_FASE}"' if clara else ""
        out.append(f'<rect class="st" x="{X_FRANJA + (a - inici) * escala:.2f}" y="{y}" '
                   f'width="{(b - a + 1) * escala:.2f}" height="{alt}" fill="{color}"{opacitat}/>')
    return out


def svg(nom: str, part: int, inici_part: int, inici: int, files: list[tuple[str, str, np.ndarray]], q: np.ndarray,
        falta: np.ndarray, decodificador: tuple[float, float, int], smart: Smart) -> str:
    w, lam, d_min = decodificador
    cos, y = [], 16
    for i, (titol, nota, codis) in enumerate(files):
        cos.append(f'<text class="nm" x="0" y="{y + 10}">{escape(titol)}</text>')
        cos.append(f'<text class="src" x="0" y="{y + 23}">{escape(nota)}</text>')
        cos += franja(codis, y, 24)
        y += 24 + 16
        if i == 0:                                     # el Smart Tagging, l'entrada, sota la veritat
            cos.append(f'<text class="nm" x="0" y="{y + 10}">Smart Tagging</text>')
            cos.append(f'<text class="src" x="0" y="{y + 23}">simulated, medium level</text>')
            cos.append(f'<rect x="{X_FRANJA}" y="{y}" width="{DRETA - X_FRANJA}" height="24" fill="none" '
                       f'stroke="{RULE}"/>')
            cos += franja_st(smart, inici, y, 24)
            y += 24 + 16
        if i == 1:                                     # la q, entre el que diu cada imatge i el decodificat
            cos.append(f'<text class="nm" x="0" y="{y + 10}">Change likely (q)</text>')
            cos.append(f'<text class="src" x="0" y="{y + 23}">darker: cheaper to switch</text>')
            cos.append(f'<rect x="{X_FRANJA}" y="{y}" width="{DRETA - X_FRANJA}" height="24" fill="none" '
                       f'stroke="{RULE}"/>')
            cos += franja_q(q, y, 24)
            y += 24 + 16
    cos.append(f'<text class="nm" x="0" y="{y + 8}">No usable ball</text>')
    escala = (DRETA - X_FRANJA) / len(falta)
    cos += [f'<rect x="{X_FRANJA + a * escala:.2f}" y="{y}" width="{(b - a + 1) * escala:.2f}" height="8" '
            f'fill="{INK}"/>' for c, a, b in trams_de(falta.astype(np.int8)) if c == 1]
    y += 8 + 8
    cos.append(f'<line x1="{X_FRANJA}" y1="{y}" x2="{DRETA}" y2="{y}" stroke="{RULE}"/>')
    desfas = inici - inici_part                                  # la finestra, des del començament de la part
    for k in range(-(-desfas // CADA_TIC) * CADA_TIC, desfas + FINESTRA + 1, CADA_TIC):
        x = X_FRANJA + (k - desfas) * escala
        ancora = "start" if x - 16 < X_FRANJA else "end" if x + 16 > DRETA else "middle"
        cos.append(f'<line x1="{x:.2f}" y1="{y}" x2="{x:.2f}" y2="{y + 4}" stroke="{SOFT}"/>')
        cos.append(f'<text class="src" x="{x:.2f}" y="{y + 15}" text-anchor="{ancora}">'
                   f'{k // pm.FPS // 60}:{k // pm.FPS % 60:02d}</text>')
    y += 34
    x = X_FRANJA
    for codi, text in ((pm.H, "H, home"), (pm.A, "A, away"), (pm.D, "D, dead ball")):
        cos.append(f'<rect x="{x}" y="{y}" width="12" height="12" rx="2" fill="{COLORS[codi]}"/>')
        cos.append(f'<text class="dt" x="{x + 18}" y="{y + 10}">{text}</text>')
        x += 104
    for k, codi in enumerate((pm.H, pm.A)):                     # una fase, del color clar del seu equip
        cos.append(f'<rect x="{x + 14 * k}" y="{y}" width="12" height="12" rx="2" fill="{COLORS[codi]}" '
                   f'fill-opacity="{OPACITAT_FASE}"/>')
    cos.append(f'<text class="dt" x="{x + 32}" y="{y + 10}">tagged phase</text>')
    cos.append(f'<text class="src" x="{X_FRANJA}" y="{y + 32}">'
               f'{escape(nom)} · half {part}, time from its start · mixed gaps, ¼ position error · seed {LLAVOR}</text>')
    alt = y + 44
    titol = "Two minutes of a bench match: the truth, the Smart Tagging, frame by frame, and decoded"
    descripcio = (f"Six strips over two minutes of {nom}, half {part}, with mixed ball gaps and a quarter of the "
                  f"assumed position error: the true labels, at the first touch; the simulated Smart Tagging at the "
                  f"medium level, with each tagged phase in the light colour of its team and the set pieces in grey; "
                  f"the model's most likely class per frame, with the Smart Tagging added and dead ball ruled out "
                  f"where the ball was cleaned away; q, the probability that the team changes nearby, darker where it "
                  f"is higher; the same through the decoder (switch cost {w:g} times minus log q, cost {lam:g} to "
                  f"and from dead ball, minimum length {d_min} frames); and the frames with no usable ball, missing "
                  f"or cleaned away.")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg viewBox="0 0 {AMPLADA} {alt}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="decoder-title decoder-desc" id="decoder-root">
  <title id="decoder-title">{escape(titol)}</title>
  <desc id="decoder-desc">{escape(descripcio)}</desc>
  <defs><style>
    #decoder-root .nm {{ font-family: 'Avenir Next', system-ui, sans-serif; font-size: 11px; font-weight: 600; fill: {INK}; }}
    #decoder-root .dt {{ font-family: 'Avenir Next', system-ui, sans-serif; font-size: 10px; fill: {MUTED}; }}
    #decoder-root .src {{ font-family: Menlo, ui-monospace, monospace; font-size: 9px; fill: {SOFT}; }}
  </style></defs>
  <rect width="100%" height="100%" fill="#ffffff"/>
  {chr(10).join("  " + linia for linia in cos).lstrip()}
</svg>
"""


def fes() -> str:
    nom, part, inici_part, inici = tria(np.random.default_rng(LLAVOR))
    t3am = rg.llegeix(mgf)
    triat = tuple(t3am["triades"][mgf.A_GIRAT][nom])                  # com al banc: triat amb els altres nou
    de_sempre, final, q, netejades = rg.relativa_final(nom, ESCENARI, t3am["triats_pilota_morta"][nom],
                                                       t3am["triats_fases"][nom])
    sense = rg.a_cada_imatge(final, de_sempre.trams)
    amb = mna.prediccio(final, q, de_sempre.trams, triat)
    smart = Smart(tuple((f.equip, f.inici, f.final) for f in fsm.fases_de(nom, ESCENARI, mgf.MITJA, mgf.PROVA)),
                  tuple((e.inici, e.final) for e in mpa.etiquetes_de(nom, ESCENARI, mgf.MITJA, mgf.PROVA)))
    tros = slice(inici, inici + FINESTRA)
    veritat = vt.veritat(nom)[tros]
    files_svg = [
        ("Truth", f"{possessions(veritat)} possessions", veritat),
        ("Frame by frame", f"{possessions(sense[tros])} possessions", sense[tros]),
        ("Decoded", f"{possessions(amb[tros])} possessions", amb[tros]),
    ]
    falta = np.isnan(de_sempre.tracking.pilota[tros, 0]) | netejades[tros]
    return svg(nom, part, inici_part, inici, files_svg, q[tros].astype(float), falta, triat, smart)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sortida", type=Path)
    args = ap.parse_args(argv)
    args.sortida.write_text(fes(), encoding="utf-8")
    print(f"✓ {args.sortida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
