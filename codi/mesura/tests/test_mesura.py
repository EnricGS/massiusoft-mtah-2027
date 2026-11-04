"""L'eina sencera sobre un bessó obert de les dades (l'ATD del partit 3 de Metrica), amb unes referències fetes a
mà: que llegeixi, mesuri i ho digui en paraules, sense cap xifra a la consola."""

from __future__ import annotations

import json
import re
import sys

import pytest

from inspeccio import besso
from mesura import estadistiques as est
from mesura import tria as tr
from mesura.__main__ import fes, main

FOTOGRAMES = 3000
N = 4000
TRAMS = ((1, 100, 1399), (2, 1600, 3499))
CASA = "team a"


@pytest.fixture(scope="module")
def dades(tmp_path_factory):
    return besso.fes(tmp_path_factory.mktemp("besso"), FOTOGRAMES, segons_video=1)


def referencies(cami, mesurable_forats: bool = True, clau: str | None = None):
    """Dos candidats de la pilota i dos dels jugadors, molt separats, a dos partits; el llindar, prou gran."""
    def files(params: dict, mesures: tuple[str, ...], valor: float) -> list[dict]:
        return [{"partit": f"obert-{i}", **params, **dict.fromkeys(mesures, valor + 0.1 * i)} for i in range(2)]

    pilota = ("morta", "viva", "forats", "aire", "aglomeracio")
    r = {
        "clau_mesures": clau or tr.clau(),
        "pilota": {"parametres": list(pilota), "mesures": list(est.PILOTA),
                   "passos": [[["morta"], ["falta_quiets"]], [["viva"], ["falta_corren"]], [["forats"], list(est.FORATS)],
                              [["aire", "aglomeracio"], ["inici_rapida", "inici_aglomeracio"]]],
                   "files": [*files({"forats": "curts", "morta": 0.41, "viva": 0.41, "aire": 3.0, "aglomeracio": 3.0},
                                    est.PILOTA, 0.0),
                             *files({"forats": "llargs", "morta": 0.97, "viva": 0.03, "aire": 0.0, "aglomeracio": 9.0},
                                    est.PILOTA, 50.0)],
                   "llindar": 1e9},
        "jugadors": {"parametres": ["perdua"], "mesures": list(est.JUGADORS), "passos": [[["perdua"],
                                                                                       list(est.JUGADORS)]],
                     "files": [*files({"perdua": "0.5-10"}, est.JUGADORS, 0.0),
                               *files({"perdua": "2-30"}, est.JUGADORS, 50.0)],
                     "llindar": 0.0},
        "noms": {"forats": {"curts": "curts", "llargs": "llargs"},
                 "morta": {"0.41": "tant com en joc (com DFL)", "0.97": "gairebé sempre (com Metrica)"},
                 "viva": {"0.03": "un 3 % (gairebé mai)", "0.41": "un 41 % (com el banc a DFL)"},
                 "aire": {"0.0": "igual que a la resta", "3.0": "com el banc (4 vegades més)"},
                 "aglomeracio": {"3.0": "com el banc (4 vegades més)", "9.0": "molt més (10 vegades)"},
                 "perdua": {"0.5-10": "com el banc (de 0,5 a 10 s)", "2-30": "llargues (de 2 a 30 s)"}},
        "mesurable": {"pilota": {"forats": {"0.41|0.41": mesurable_forats, "0.97|0.03": True},
                                 **{k: {"0.41|0.41": True, "0.97|0.03": True}
                                    for k in ("morta", "viva", "aire", "aglomeracio")}},
                      "perdua": True},
    }
    cami.write_text(json.dumps(r), encoding="utf-8")
    return cami


def executa(dades, tmp_path, **kw):
    missatges = []
    codi = fes(dades, tmp_path / "sortida", casa=CASA, trams=TRAMS, n=N,
               referencies=referencies(tmp_path / "ref.json", **kw), parla=missatges.append)
    return codi, missatges


def test_mesura_i_ho_diu_en_paraules(dades, tmp_path):
    codi, missatges = executa(dades, tmp_path)
    assert codi == 0
    assert any(m.startswith("✓ Els forats de la pilota en joc són: «curts»") for m in missatges)
    assert any(m.startswith("✓ En joc, la pilota falta: «un 41 %") for m in missatges)
    assert any(m.startswith("✓ Quan la pilota és morta, falta: «tant com en joc") for m in missatges)
    assert any(m.startswith("✓ La pilota: el partit s'assembla") for m in missatges)
    assert any(m.startswith("⚠ Els jugadors: el partit queda lluny") for m in missatges)   # llindar 0
    assert (tmp_path / "sortida" / "informe.md").is_file()


def test_a_la_consola_no_hi_ha_cap_xifra(dades, tmp_path):
    _, missatges = executa(dades, tmp_path)
    sense_cami = [m for m in missatges if not m.startswith("· Les xifres són a")]
    noms = json.loads((tmp_path / "ref.json").read_text())["noms"]
    permesos = {n for v in noms.values() for n in v.values()}           # els noms dels candidats, fixats abans
    for m in sense_cami:
        for nom in permesos:
            m = m.replace(nom, "")
        assert not re.search(r"\d", m), m


def test_el_que_no_es_pot_mesurar_no_es_diu(dades, tmp_path):
    _, missatges = executa(dades, tmp_path, mesurable_forats=False)
    linia = next(m for m in missatges if m.startswith("· Els forats de la pilota en joc són"))
    assert "no es pot mesurar" in linia and "curts" not in linia


def test_unes_referencies_d_unes_altres_mesures_aturen_l_eina(dades, tmp_path):
    codi, missatges = executa(dades, tmp_path, clau="una altra")
    assert codi == 1 and missatges[-1].startswith("✗ Les referències del banc són d'unes altres mesures")
    assert not (tmp_path / "sortida").exists()


def test_l_ordre_no_escriu_fora_del_volum(dades, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["mesura", "--dades", str(dades), "--sortida", str(tmp_path / "fora")])
    assert main() == 1
    assert "ha d'anar dins de" in capsys.readouterr().out and not (tmp_path / "fora").exists()
