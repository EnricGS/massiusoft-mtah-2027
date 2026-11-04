"""Baixa els partits de SkillCorner Open Data (github.com/SkillCorner/opendata) i en comprova les empremtes.

Ús: python3 -I baixa_skillcorner.py <carpeta de destí>
De cada partit, la fitxa (`_match.json`), les fases de joc (`_phases_of_play.csv`) i el tracking
(`_tracking_extrapolated.jsonl`), a més de la llista dels partits (`matches.json`). Els fitxers LFS es comproven amb
el sha256 del seu punter; els altres, amb el sha1 del blob de git.
"""

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

REVISIO = "4340d274572876239c154c90bc507a9b3250a656"   # la que vam baixar el 28-10-2026 (és del 14-09-2026)
ARBRE = f"https://api.github.com/repos/SkillCorner/opendata/git/trees/{REVISIO}?recursive=1"
CRU = f"https://raw.githubusercontent.com/SkillCorner/opendata/{REVISIO}/{{}}"
LFS = f"https://media.githubusercontent.com/media/SkillCorner/opendata/{REVISIO}/{{}}"
FINALS = ("_match.json", "_phases_of_play.csv", "_tracking_extrapolated.jsonl")
BLOC = 1 << 20


def obre(url: str, timeout: int = 120):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "massiusoft-banc"}),
                                  timeout=timeout)


def punter(cami: str) -> tuple[str, int] | None:
    """L'empremta i la mida d'un fitxer LFS, o None si no ho és."""
    with obre(CRU.format(cami), 60) as resposta:
        cap = resposta.read(512).decode("utf-8", "replace")
    if not cap.startswith("version https://git-lfs.github.com/spec/v1"):
        return None
    camps = dict(linia.split(" ", 1) for linia in cap.splitlines() if " " in linia)
    return camps["oid"].removeprefix("sha256:"), int(camps["size"])


def baixa(url: str, desti: Path, lfs: bool, mida: int) -> str:
    resum = hashlib.sha256() if lfs else hashlib.sha1(f"blob {mida}\0".encode())
    parcial = desti.with_suffix(desti.suffix + ".part")
    with obre(url) as resposta, parcial.open("wb") as sortida:
        while bloc := resposta.read(BLOC):
            resum.update(bloc)
            sortida.write(bloc)
    parcial.rename(desti)
    return resum.hexdigest()


def main() -> int:
    carpeta = Path(sys.argv[1]).resolve()
    with obre(ARBRE, 60) as resposta:
        arbre = json.load(resposta)
    if arbre.get("truncated"):
        raise SystemExit("La llista del repositori ve tallada")
    volguts = [e for e in arbre["tree"] if e["type"] == "blob" and
               (e["path"] == "data/matches.json" or (e["path"].startswith("data/matches/") and e["path"].endswith(FINALS)))]
    errors = 0
    for entrada in volguts:
        cami = entrada["path"]
        desti = carpeta / Path(cami).relative_to("data")
        desti.parent.mkdir(parents=True, exist_ok=True)
        lfs = punter(cami)
        if lfs:
            esperat, mida = lfs
            obtingut = baixa(LFS.format(cami), desti, True, mida)
        else:
            esperat, mida = entrada["sha"], entrada["size"]
            obtingut = baixa(CRU.format(cami), desti, False, mida)
        ok = obtingut == esperat and desti.stat().st_size == mida
        errors += not ok
        print(f"{'✓' if ok else '✗'} {cami} ({mida / 1e6:.1f} MB)", flush=True)
    print(f"{len(volguts)} fitxers. " + ("Tot correcte" if not errors else f"{errors} no quadren"), flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
