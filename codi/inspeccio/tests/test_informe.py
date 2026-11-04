"""L'informe sencer sobre un bessó petit de les dades (Metrica sample-data i sintètiques)."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from inspeccio import besso, fitxers, oficial
from inspeccio.__main__ import inspecciona
from inspeccio.esperat import Esperat
from inspeccio.seccio import Seccio

FOTOGRAMES = 1000
ESPERAT_BESSO = Esperat(rangs_puntuats=((1, 100, 450), (2, 520, 950)))


@pytest.fixture(scope="module")
def besso_petit(tmp_path_factory):
    return besso.fes(tmp_path_factory.mktemp("besso"), FOTOGRAMES, segons_video=FOTOGRAMES / 25)


def test_l_informe_surt_sencer_i_sense_errors(besso_petit, tmp_path):
    seccions, cami = inspecciona(besso_petit, tmp_path, ESPERAT_BESSO, parla=lambda s: None)
    assert [s.titol for s in seccions if s.error] == []
    text = cami.read_text(encoding="utf-8")
    assert "Inspecció de les dades" in text and "data:image/jpeg;base64," in text
    assert "<script" not in text and 'src="http' not in text


def test_l_inventari_porta_el_sha256_de_cada_fitxer(besso_petit, tmp_path):
    inspecciona(besso_petit, tmp_path, ESPERAT_BESSO, captures=False, parla=lambda s: None)
    inventari = json.loads((tmp_path / "inventari.json").read_text(encoding="utf-8"))
    assert len(inventari) == sum(1 for c in besso_petit.rglob("*") if c.is_file())
    primer = inventari[0]
    assert primer["sha256"] == fitxers.sha256(besso_petit / primer["fitxer"])


def test_la_consola_no_porta_cap_xifra_de_les_dades(besso_petit, tmp_path):
    ordre = [sys.executable, "-I", "-m", "inspeccio", "--dades", str(besso_petit), "--sortida", str(tmp_path),
             "--sense-captures", "--permet-fora-del-volum"]
    resultat = subprocess.run(ordre, capture_output=True, text=True, timeout=600)
    assert resultat.stderr == ""
    for linia in resultat.stdout.splitlines():
        if linia and not linia.startswith(("Informe:", "Obre'l")):
            assert not any(c.isdigit() for c in linia), linia


def test_no_escriu_fora_del_volum_si_no_se_li_diu(besso_petit, tmp_path):
    ordre = [sys.executable, "-I", "-m", "inspeccio", "--dades", str(besso_petit), "--sortida", str(tmp_path)]
    resultat = subprocess.run(ordre, capture_output=True, text=True, timeout=60)
    assert resultat.returncode == 1 and "ha d'anar dins" in resultat.stdout
    assert not list(tmp_path.iterdir())


def test_la_sortida_no_pot_ser_dins_de_les_dades(besso_petit):
    ordre = [sys.executable, "-I", "-m", "inspeccio", "--dades", str(besso_petit), "--sortida",
             str(besso_petit / "informes"), "--permet-fora-del-volum"]
    resultat = subprocess.run(ordre, capture_output=True, text=True, timeout=60)
    assert resultat.returncode == 1 and not (besso_petit / "informes").exists()


def repo_fals(cami, contingut_nou: str) -> str:
    """Un repo amb les quatre línies base publicades i un `baseline.py` que les torna a escriure."""
    (cami / "starter").mkdir(parents=True)
    (cami / "evaluation" / "results").mkdir(parents=True)
    noms = [f"baseline_{n}.csv" for n in ("raw", "smooth25", "smooth50", "smooth125")]
    for nom in noms:
        (cami / "evaluation" / "results" / nom).write_text("frame,label\n0,X\n")
    (cami / "starter" / "baseline.py").write_text(
        "import os, pathlib\nassert os.environ['MTAH_DATA_DIR']\n"
        f"for n in {noms!r}:\n    pathlib.Path('evaluation/results', n).write_text({contingut_nou!r})\n")
    (cami / "evaluation" / "run_evaluation.py").write_text("print('tauler')\n")
    for ordre in (["init", "-q"], ["add", "."], ["-c", "user.name=p", "-c", "user.email=p@p", "commit", "-qm", "p"]):
        subprocess.run(["git", "-C", str(cami), *ordre], check=True)
    return subprocess.run(["git", "-C", str(cami), "rev-parse", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip()


@pytest.mark.parametrize("contingut, iguals", [("frame,label\n0,X\n", True), ("frame,label\n0,H\n", False)])
def test_el_codi_oficial_diu_si_les_linies_base_coincideixen(besso_petit, tmp_path, contingut, iguals):
    commit = repo_fals(tmp_path / "origen", contingut)
    s = Seccio("Codi oficial")
    oficial.omple(s, fitxers.localitza(besso_petit), tmp_path / "sortida", str(tmp_path / "origen"), commit)
    comprovacions = {c.que: c.ok for b in s.blocs if isinstance(b, tuple) for c in b}
    assert comprovacions["starter/baseline.py acaba bé"] is True
    assert comprovacions["i són idèntics als publicats"] is iguals
