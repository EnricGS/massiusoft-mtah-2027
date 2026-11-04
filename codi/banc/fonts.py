"""Els partits del banc i la seva memòria cau (`dades/banc/`, fora del codi).

Llegir un partit de DFL amb kloppy tarda gairebé un minut; de la memòria cau, un segon.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from banc import dfl, metrica, pff, skillcorner
from banc.partit import PartitBanc, carrega, desa

ARREL = Path(__file__).resolve().parents[2]
DIR_IDSSE = ARREL / "dades" / "idsse"
DIR_SKILLCORNER = ARREL / "dades" / "skillcorner"
DIR_PFF = ARREL / "dades" / "pff"
DIR_CAU = ARREL / "dades" / "banc"
PARTITS_DFL = ("J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WPY", "J03WQQ", "J03WR9")
PARTITS_METRICA = (1, 2, 3)
NOMS = tuple(f"dfl-{p}" for p in PARTITS_DFL) + tuple(f"metrica-{n}" for n in PARTITS_METRICA)
PARTITS_SKILLCORNER = (1874553, 1886347, 1899585, 1925299, 1927964, 1953632, 1959846, 1986691, 1996435, 1996436,
                       2006229, 2006363, 2007448, 2007721, 2010085, 2011166, 2013725, 2015213, 2016236, 2017461)
NOMS_SKILLCORNER = tuple(f"skillcorner-{p}" for p in PARTITS_SKILLCORNER)   # només per entrenar (T3l): no es proven
PARTITS_PFF = (3812, 3813, 3814, 3815, 3816, 3817, 3818, 3819, 3820, 3821, 3822, 3823, 3824, 3825, 3826, 3827, 3828,
               3829, 3830, 3831, 3832, 3833, 3834, 3835, 3836, 3837, 3838, 3839, 3840, 3841, 3842, 3843, 3844, 3845,
               3846, 3847, 3848, 3849, 3850, 3851, 3852, 3853, 3854, 3855, 3856, 3857, 3858, 3859, 10502, 10503,
               10504, 10505, 10506, 10507, 10508, 10509, 10510, 10511, 10512, 10513, 10514, 10515, 10516, 10517)
NOMS_PFF = tuple(f"pff-{p}" for p in PARTITS_PFF)        # només per entrenar les xarxes (T3ab): no es proven


def llegeix_de_la_font(nom: str) -> PartitBanc:
    font, clau = nom.split("-", 1)
    if font == "dfl" and clau in PARTITS_DFL:
        return dfl.llegeix(DIR_IDSSE, clau)
    if font == "metrica" and clau.isdigit() and int(clau) in PARTITS_METRICA:
        return metrica.llegeix(int(clau))
    if font == "skillcorner" and clau.isdigit() and int(clau) in PARTITS_SKILLCORNER:
        return skillcorner.llegeix(DIR_SKILLCORNER, int(clau))
    if font == "pff" and clau.isdigit() and int(clau) in PARTITS_PFF:
        return pff.llegeix(DIR_PFF, int(clau))
    raise KeyError(f"No conec el partit {nom}")


def partit(nom: str, cau: Path = DIR_CAU) -> PartitBanc:
    cami = cau / f"{nom}.npz"
    if cami.exists() and (p := carrega(cami)) is not None:
        return p
    p = llegeix_de_la_font(nom)
    cau.mkdir(parents=True, exist_ok=True)
    desa(p, cami)
    return p


def _prepara(nom: str) -> str:
    partit(nom)
    return nom


def prepara(noms: tuple[str, ...] = NOMS, processos: int = 4) -> None:
    """Fa la memòria cau dels que no la tenen, en paral·lel."""
    falten = [n for n in noms if not (DIR_CAU / f"{n}.npz").exists()]
    with ProcessPoolExecutor(max_workers=max(1, min(processos, len(falten)))) as feina:
        for nom in feina.map(_prepara, falten):
            print(f"· {nom} a la memòria cau", flush=True)
