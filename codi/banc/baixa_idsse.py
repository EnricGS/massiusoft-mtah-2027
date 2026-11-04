"""Baixa el conjunt IDSSE (Bassek et al., 2025) de pysport/idsse-data i en comprova les empremtes.

Ús: python3 -I baixa_idsse.py <carpeta de destí>
Els fitxers LFS es comproven amb el sha256 de l'API; els altres, amb el sha1 del blob de git.
"""

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

REVISIO = "a715a38dfbaf5f58e431727c2b78d174101a703c"   # la que vam baixar el 24-10-2026 (és del 04-03-2026)
ARBRE = f"https://huggingface.co/api/datasets/pysport/idsse-data/tree/{REVISIO}"
FITXER = f"https://huggingface.co/datasets/pysport/idsse-data/resolve/{REVISIO}/{{}}"
BLOC = 1 << 20


def baixa(url: str, desti: Path, lfs: bool, mida: int) -> str:
    resum = hashlib.sha256() if lfs else hashlib.sha1(f"blob {mida}\0".encode())
    parcial = desti.with_suffix(desti.suffix + ".part")
    with urllib.request.urlopen(url, timeout=120) as resposta, parcial.open("wb") as sortida:
        while bloc := resposta.read(BLOC):
            resum.update(bloc)
            sortida.write(bloc)
    parcial.rename(desti)
    return resum.hexdigest()


def main() -> int:
    carpeta = Path(sys.argv[1]).resolve()
    carpeta.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(ARBRE, timeout=60) as resposta:
        arbre = json.load(resposta)
    errors = 0
    for entrada in arbre:
        nom = entrada["path"]
        if entrada.get("type") != "file" or nom == ".gitattributes" or "/" in nom:
            continue
        lfs = "lfs" in entrada
        esperat = entrada["lfs"]["oid"] if lfs else entrada["oid"]
        mida = entrada["lfs"]["size"] if lfs else entrada["size"]
        desti = carpeta / nom
        obtingut = baixa(FITXER.format(nom), desti, lfs, mida)
        ok = obtingut == esperat and desti.stat().st_size == mida
        errors += not ok
        print(f"{'✓' if ok else '✗'} {nom} ({mida / 1e6:.1f} MB)", flush=True)
    print("Tot correcte" if not errors else f"{errors} fitxers no quadren", flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
