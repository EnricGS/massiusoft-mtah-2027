"""Fa el fitxer de possessió a partir de les dades del concurs. L'executa l'equip, en local.

    cd codi && uv run python -I -m cadena --dades "<carpeta de les dades>"

Les etiquetes són les d'A girat amb fases (`opcio_girat.py`), entrenat només amb dades obertes, amb el tracking i el
Smart Tagging del partit: les pilotes aturades i les fases amb equip. Abans de fer servir les fases, mira que el seu
equip sigui el que dona el model sense el Smart Tagging; si no, o si no n'hi ha cap, s'atura. Escriu el fitxer dins
del volum xifrat, en comprova el format, el compara amb l'execució anterior, hi passa el validador oficial (el que
aquest escriu va a un fitxer al costat) i mira amb la finestra pública que H i A vagin bé i que les imatges quadrin.
A la consola només surt si cada pas ha anat bé: cap xifra de les dades. Dels avisos del Smart Tagging, cadascun un
sol cop, sense dir quantes vegades hi és.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

from cadena import fitxer, llegeix, model_girat, publics
from cadena import opcio_girat as og
from cadena import smart_tagging_fases as stf
from cadena.norma import EQUIP_CASA, N_FOTOGRAMES, TRAMS_PUNTUATS
from cadena.volum import VOLUM, dins_de, dins_del_volum, temporals_dins

SORTIDA = VOLUM / "cadena" / "possessio-A.csv"
VALIDADOR = VOLUM / "informes" / "repo-oficial" / "evaluation" / "validate_submission.py"
TEMPS_VALIDADOR_S = 600
SENSE_COMPROVAR = 2                     # tot ha anat bé, però sense el validador oficial ni la finestra pública


def arguments() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="python -I -m cadena", description=__doc__.splitlines()[0])
    p.add_argument("--dades", type=Path, required=True, help="carpeta on hi ha les dades, tal com arriben")
    p.add_argument("--sortida", type=Path, default=SORTIDA, help=f"el fitxer (per defecte, {SORTIDA})")
    p.add_argument("--validador", type=Path, default=VALIDADOR,
                   help="el validate_submission.py del repo oficial (per defecte, el clon de l'informe)")
    p.add_argument("--sense-validador", action="store_true",
                   help="no passar el validador oficial: el fitxer no queda comprovat del tot")
    p.add_argument("--accepta-canvi", action="store_true",
                   help="si el fitxer canvia perquè ha canviat el codi, desar-ne l'empremta nova")
    p.add_argument("--permet-fora-del-volum", action="store_true",
                   help="escriure el fitxer fora del volum xifrat de l'equip: per reproduir-lo en una altra màquina")
    return p.parse_args()


def empremta_desada(desada: Path) -> str | None:
    """La de l'execució anterior. Si no hi és, és buida o no es pot llegir, com si no n'hi hagués."""
    try:
        paraules = desada.read_text(encoding="utf-8").split()
    except (OSError, UnicodeDecodeError):
        return None
    return paraules[0] if paraules and re.fullmatch(r"[0-9a-f]{64}", paraules[0]) else None


def desa_empremta(desada: Path, valor: str, nom: str) -> None:
    temporal = desada.with_name(desada.name + ".part")
    temporal.write_text(f"{valor}  {nom}\n", encoding="utf-8")
    temporal.replace(desada)


def compara_amb_l_anterior(cami: Path, parla: Callable[[str], None], accepta_canvi: bool = False) -> bool:
    """El fitxer ha de ser igual que el de l'execució anterior. L'empremta només es desa la primera vegada,
    o quan es diu que el canvi és volgut: si no, una segona execució s'oblidaria de la bona."""
    nova, desada = fitxer.empremta(cami), cami.with_name(cami.name + ".sha256")
    anterior = empremta_desada(desada)
    if anterior == nova:
        parla("✓ Igual que l'execució anterior (la mateixa empremta)")
        return True
    if anterior is not None and not accepta_canvi:
        parla("⚠ Diferent de l'execució anterior: la cadena no és determinista, o ha canviat el codi. "
              "Si el canvi és volgut, torna-ho a fer amb --accepta-canvi")
        return False
    desa_empremta(desada, nova, cami.name)
    parla("· Primera execució: l'empremta queda desada al costat del fitxer" if anterior is None else
          "✓ Canvi acceptat: l'empremta nova queda desada")
    return True


def valida_oficial(cami: Path, validador: Path, parla: Callable[[str], None]) -> bool:
    """El que escriu el validador oficial porta recomptes del fitxer: va a un fitxer al costat, dins del volum."""
    validador, cami = validador.resolve(), cami.resolve()
    informe = cami.with_name(cami.name + ".validacio.txt")
    informe.unlink(missing_ok=True)                      # que no en quedi un d'una execució anterior
    if not validador.is_file():
        parla("✗ No trobo el validador oficial: fes primer l'informe amb --oficial, o passa'l amb --validador")
        return False
    parla("… El validador oficial")
    try:
        resultat = subprocess.run([sys.executable, "-B", str(validador), str(cami)], cwd=validador.parent.parent,
                                  capture_output=True, text=True, encoding="utf-8", errors="replace",
                                  timeout=TEMPS_VALIDADOR_S, check=False)
    except subprocess.TimeoutExpired:
        parla("✗ El validador oficial no ha acabat a temps")
        return False
    informe.write_text(resultat.stdout + resultat.stderr, encoding="utf-8")
    if resultat.returncode == 0:
        parla(f"✓ El validador oficial l'accepta (el que diu és a {informe.name})")
        return True
    parla(f"✗ El validador oficial el rebutja (el que diu és a {informe.name})")
    return False


def nom_net(nom: str) -> str:
    """El nom d'un equip de les metadades, sense res que el terminal pugui interpretar."""
    return "".join(c for c in nom if c.isprintable())[:40]


def fes(dades: Path, sortida: Path, casa: str = EQUIP_CASA,
        trams: tuple[tuple[int, int, int], ...] = TRAMS_PUNTUATS, n: int = N_FOTOGRAMES,
        validador: Path | None = None, accepta_canvi: bool = False,
        parla: Callable[[str], None] = print) -> int:
    """Tota la cadena. Torna 0 si cada pas ha anat bé, i 1 si algun ha fallat. Sense `validador`, no passa l'oficial
    ni mira la finestra pública (és al mateix clon), i com a molt torna `SENSE_COMPROVAR`."""
    try:
        entrenat = model_girat.carrega()
        meta, raw = llegeix.localitza(dades)
        parla("… Llegint l'ATD tàctic")
        t = llegeix.tracking(meta, raw, casa)
    except (llegeix.ErrorDeLectura, model_girat.ErrorDelModel) as error:    # només aquestes: el missatge és fix
        parla(f"✗ {error}")
        return 1
    parla(f"✓ ATD tàctic llegit · H és «{nom_net(t.nom_casa)}» i A, «{nom_net(t.nom_fora)}»")
    if not t.casa_es_home:
        parla(f"⚠ A les metadades, «{nom_net(t.nom_casa)}» no és l'equip de casa. H el segueix sent (DATA.md)")
    try:
        llegit = stf.llegeix(stf.localitza(dades))
    except llegeix.ErrorDeLectura as error:
        parla(f"✗ {error}")
        return 1
    parla("✓ Smart Tagging llegit: les pilotes aturades i les fases amb equip")
    for avis in dict.fromkeys(llegit.avisos):            # cadascun un sol cop: quantes vegades, seria una xifra
        parla(avis)
    parla("… El model d'A girat amb fases: els senyals, les probabilitats, el Smart Tagging i els trams")
    try:
        codis = og.codis(t, trams, n, entrenat, llegit)
    except (model_girat.ErrorDelModel, og.ErrorDeLesFases) as error:
        parla(f"✗ {error}")
        return 1
    parla("✓ L'equip de les fases és el que dona el model sense el Smart Tagging")
    sortida.parent.mkdir(parents=True, exist_ok=True)
    fitxer.escriu(sortida, og.lletres(codis))
    parla(f"✓ Fitxer escrit: {sortida}")
    motiu = fitxer.comprova(sortida, n)
    if motiu is not None:                                # ni empremta ni validador d'un fitxer que no és bo
        parla(f"✗ Format: {motiu}")
        return 1
    parla("✓ Format correcte (les regles de SUBMISSION.md)")
    igual = compara_amb_l_anterior(sortida, parla, accepta_canvi)
    if validador is None:
        parla("⚠ Sense el validador oficial ni la finestra pública: el fitxer no queda comprovat")
        return SENSE_COMPROVAR if igual else 1
    oficial = valida_oficial(sortida, validador, parla)
    public = publics.comprova(sortida, validador.resolve().parent.parent, parla)
    return 0 if igual and oficial and public else 1


def main() -> int:
    args = arguments()
    if not args.dades.is_dir():
        print(f"✗ No trobo la carpeta {args.dades}")
        return 1
    if not (dins_del_volum(args.sortida) or args.permet_fora_del_volum):
        print(f"✗ El fitxer surt de les dades: ha d'anar dins de {VOLUM}, i el volum ha de ser muntat")
        return 1
    dades, sortida = args.dades.resolve(), args.sortida.resolve()
    if dins_de(sortida, dades):
        print("✗ El fitxer no pot anar dins de la carpeta de les dades")
        return 1
    if args.sense_validador:
        print("· Sense el validador oficial (--sense-validador): el fitxer no queda comprovat del tot")
    sortida.parent.mkdir(parents=True, exist_ok=True)
    temporals = Path(tempfile.mkdtemp(prefix=".cadena-", dir=sortida.parent))
    try:
        with temporals_dins(temporals):
            codi = fes(dades, sortida, validador=None if args.sense_validador else args.validador,
                       accepta_canvi=args.accepta_canvi)
    except Exception as error:  # noqa: BLE001 - el missatge de l'error pot portar dades: no s'imprimeix
        print(f"✗ Error intern ({type(error).__name__}); el fitxer no és bo")
        return 1
    if codi == 0:
        print("\nNo passis el fitxer ni aquesta sortida a cap LLM al núvol.")
    elif codi == SENSE_COMPROVAR:
        print("\nEl fitxer és escrit, però sense el validador oficial no es pot donar per bo.")
    else:
        print("\nAlguna cosa ha fallat (vegeu ✗ o ⚠).")
    return codi


if __name__ == "__main__":
    sys.exit(main())
