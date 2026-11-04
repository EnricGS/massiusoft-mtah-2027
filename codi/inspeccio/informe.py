"""L'informe en un sol HTML, amb les figures a dins: s'obre sense xarxa i no carrega res de fora."""

from __future__ import annotations

import html
import re
from datetime import datetime
from pathlib import Path

from inspeccio.seccio import Comprovacio, Figura, Paragraf, Preformat, Seccio, Taula, diferencies

ESTIL = """
:root { --paper:#F7F6F2; --superficie:#ECEBE6; --tinta:#15171A; --tinta-2:#5A606A;
  --be:#166534; --malament:#B91C1C; --avis:#FFE45C; --ample:1080px; }
* { box-sizing:border-box; }
body { margin:0; background:var(--paper); color:var(--tinta);
  font:15px/1.5 "Avenir Next", "Helvetica Neue", system-ui, sans-serif; }
header, main { max-width:var(--ample); margin:0 auto; padding:0 24px; }
header { padding-top:28px; }
.avis { background:var(--avis); padding:10px 14px; font-weight:600; border-radius:2px; }
.guia { border-left:4px solid var(--tinta); background:var(--superficie); padding:4px 16px; margin:16px 0; }
.guia li { margin:4px 0; }
h1 { font:700 34px/1.15 Charter, Georgia, serif; margin:22px 0 6px; }
h2 { font:700 23px/1.2 Charter, Georgia, serif; margin:0 0 12px; display:flex; gap:12px; align-items:baseline; }
h3 { font-size:14px; margin:22px 0 6px; color:var(--tinta-2); text-transform:uppercase; letter-spacing:.04em; }
.meta { color:var(--tinta-2); font-size:13px; }
nav ol { columns:2; padding-left:20px; }
nav a { color:var(--tinta); }
section { border-top:2px solid var(--tinta); padding:22px 0 30px; }
table { border-collapse:collapse; width:100%; font-size:13px; font-variant-numeric:tabular-nums; margin:6px 0; }
th, td { text-align:left; padding:5px 8px; border-bottom:1px solid var(--superficie); vertical-align:top; }
th { font-weight:600; color:var(--tinta-2); border-bottom:1px solid var(--tinta-2); }
td.n, th.n { text-align:right; }
.nota { color:var(--tinta-2); font-size:12.5px; margin:2px 0 0; }
.estat { font:600 12px/1 "Avenir Next", sans-serif; padding:4px 8px; border-radius:2px; color:#fff; }
.estat.be { background:var(--be); } .estat.malament { background:var(--malament); }
.estat.avis { background:var(--avis); color:var(--tinta); }
.ok { color:var(--be); font-weight:700; } .ko { color:var(--malament); font-weight:700; }
.sense { color:var(--tinta-2); }
tr.ko-fila td { background:#FDECEC; }
figure { margin:16px 0; }
figure img { width:100%; height:auto; display:block; border:1px solid var(--superficie); }
figcaption { font-size:13px; color:var(--tinta-2); margin-top:4px; }
pre { background:var(--superficie); padding:10px; overflow-x:auto; font-size:12px; white-space:pre-wrap; }
code { font:12.5px/1.4 Menlo, monospace; background:var(--superficie); padding:0 3px; }
details summary { cursor:pointer; }
details summary h3 { display:inline-block; margin:22px 0 6px; }
details.error summary { color:var(--malament); font-weight:600; }
footer { max-width:var(--ample); margin:0 auto; padding:20px 24px 40px; color:var(--tinta-2); font-size:12px; }
@media (max-width:640px) { nav ol { columns:1; } h1 { font-size:27px; } }
"""

GUIA = """<div class="guia"><p><strong>Com triar l'enfocament amb aquest informe.</strong> Els criteris
s'han escrit abans de veure les dades. Decideix l'equip, i a cap model de llenguatge al núvol no se li passa cap xifra ni cap captura.</p>
<ol>
<li><strong>A (només el tracking) n'hi ha prou per a la pilota</strong> si la major part dels fotogrames sense
pilota són en forats curts, de 3 s o menys (taula «Forats de la pilota segons la durada»).</li>
<li><strong>Cal B (buscar la pilota al vídeo tàctic)</strong> si una part gran són forats de més de 3 s que cauen
fora de tota instància del Smart Tagging (secció «Forats de la pilota i Smart Tagging»): és pilota en joc que
l'ATD no veu.</li>
<li><strong>B és viable</strong> si a les captures dels forats veus la pilota amb els ulls i el diàmetre (la mediana) és
d'uns 4 px o més (secció «Homografia tàctica»). Si no la veus, o fa 2 o 3 px, B és una aposta llarga.</li>
<li><strong>C (un model de visió local per a la pilota morta)</strong> té sentit si a les captures es veu clar
quan el joc està aturat: jugadors quiets, un servei de banda, la pilota fora.</li>
</ol></div>"""
FILES_OBERTES = 20      # una taula més llarga surt plegada
NUMERO = re.compile(r"^[−\-–]?[\d.]+(,\d+)?( ?(%|px|s|m|m/s|GB|MB|kB|B))?$")


def marques(text: str) -> str:
    """Escapa el text i hi aplica les dues marques que fan servir les seccions: `codi` i **negreta**."""
    segur = html.escape(str(text))
    segur = re.sub(r"`([^`]+)`", r"<code>\1</code>", segur)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", segur)


def casella(valor) -> str:
    text = str(valor)
    classe = ' class="n"' if es_numero(text) else ""
    return f"<td{classe}>{marques(text)}</td>"


def es_numero(valor) -> bool:
    return bool(NUMERO.match(str(valor).strip()))


def taula(t: Taula) -> str:
    numerica = [bool(t.files) and all(es_numero(f[i]) or f[i] in ("", "—") for f in t.files)
                for i in range(len(t.capcalera))]
    classes = [' class="n"' if n else "" for n in numerica]
    capcalera = "".join(f"<th{classe}>{marques(c)}</th>" for c, classe in zip(t.capcalera, classes))
    files = "".join("<tr>" + "".join(casella(v) for v in fila) + "</tr>" for fila in t.files)
    nota = f'<p class="nota">{marques(t.nota)}</p>' if t.nota else ""
    cos = f"<table><thead><tr>{capcalera}</tr></thead><tbody>{files}</tbody></table>{nota}"
    if len(t.files) > FILES_OBERTES:
        return f"<details><summary><h3>{marques(t.titol)} ({len(t.files)} files)</h3></summary>{cos}</details>"
    return f"<h3>{marques(t.titol)}</h3>{cos}"


def comprovacions(llista: tuple[Comprovacio, ...]) -> str:
    files = []
    for c in llista:
        marca = {True: '<span class="ok">✓</span>', False: '<span class="ko">✗</span>',
                 None: '<span class="sense">—</span>'}[c.ok]
        classe = ' class="ko-fila"' if c.ok is False else ""
        files.append(f"<tr{classe}><td>{marca}</td><td>{marques(c.que)}</td>{casella(c.esperat)}{casella(c.trobat)}</tr>")
    return ("<table><thead><tr><th></th><th>Què</th><th>Documentació</th><th>Trobat</th></tr></thead>"
            f"<tbody>{''.join(files)}</tbody></table>")


def figura(f: Figura) -> str:
    titol = f"<h3>{marques(f.titol)}</h3>" if f.titol else ""
    peu = f"<figcaption>{marques(f.peu)}</figcaption>" if f.peu else ""
    alt = html.escape(f.titol or f.peu, quote=True)
    return f'{titol}<figure><img alt="{alt}" src="data:image/{f.tipus};base64,{f.dades_b64}">{peu}</figure>'


def bloc(b) -> str:
    if isinstance(b, Paragraf):
        return f"<p>{marques(b.text)}</p>"
    if isinstance(b, Taula):
        return taula(b)
    if isinstance(b, Figura):
        return figura(b)
    if isinstance(b, Preformat):
        return f"<h3>{marques(b.titol)}</h3><pre>{html.escape(b.text)}</pre>"
    return comprovacions(b)


def estat(s: Seccio) -> str:
    if s.error:
        return '<span class="estat malament">error</span>'
    if s.diferencies:
        return f'<span class="estat avis">{diferencies(s.diferencies)}</span>'
    return '<span class="estat be">tot quadra</span>'


def seccio(index: int, s: Seccio) -> str:
    cos = "".join(bloc(b) for b in s.blocs)
    if s.error:
        cos += ('<details class="error" open><summary>Ha fallat aquesta secció</summary>'
                f"<pre>{html.escape(s.error)}</pre></details>")
    return f'<section id="s{index}"><h2>{marques(s.titol)} {estat(s)}</h2>{cos}</section>'


def html_de(seccions: list[Seccio], dades: Path, versions: dict[str, str]) -> str:
    ara = datetime.now().strftime("%d-%m-%Y a les %H:%M")
    index = "".join(f'<li><a href="#s{i}">{marques(s.titol)}</a> {estat(s)}</li>' for i, s in enumerate(seccions))
    versio = " · ".join(f"{k} {v}" for k, v in versions.items())
    return f"""<!doctype html>
<html lang="ca"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'">
<title>Inspecció de les dades</title><style>{ESTIL}</style></head>
<body><header>
<p class="avis">Confidencial: dades del concurs More than a Hack 2027 (clàusula 8 de les bases). No el passis a cap
model de llenguatge al núvol, i no el treguis del volum xifrat.</p>
<h1>Inspecció de les dades · BAR-ATH</h1>
<p class="meta">Fet el {ara} sobre {marques(f"`{dades}`")}. {html.escape(versio)}.</p>
<p>Cada secció compara el que hi ha amb el que diu la documentació pública (DATA.md, al commit
<code>f8f2629</code>) i després mira el que fa falta per triar l'enfocament: on falta la pilota, quant de temps,
i si al vídeo tàctic es veu prou per anar-la a buscar.</p>
{GUIA}
<nav><ol>{index}</ol></nav></header>
<main>{"".join(seccio(i, s) for i, s in enumerate(seccions))}</main>
<footer>Generat per <code>codi/inspeccio</code> (More than a Hack 2027).</footer>
</body></html>
"""


def desa(seccions: list[Seccio], dades: Path, sortida: Path, versions: dict[str, str]) -> Path:
    cami = sortida / f"inspeccio-{datetime.now():%Y%m%d-%H%M}.html"
    cami.write_text(html_de(seccions, dades, versions), encoding="utf-8")
    return cami
