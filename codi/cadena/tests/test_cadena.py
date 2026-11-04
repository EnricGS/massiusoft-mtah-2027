"""La cadena sencera sobre un bessó obert de les dades (l'ATD del partit 3 de Metrica), amb A girat amb fases i un
Smart Tagging fet de les etiquetes i les fases simulades del mateix partit, com al banc."""

from __future__ import annotations

import functools
import json
import shutil
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from banc import fases_simulades as fsm
from banc import fonts
from banc import model_a_canvis as t3i
from banc import model_a_contacte as t3h
from banc import model_a_xarxa as t3m
from banc import model_fases as mfs
from banc import model_neteja_aire as mna
from banc import model_pilotes_aturades as mpa
from cadena import fases as fs
from cadena import fitxer, model, model_girat
from cadena import opcio_girat as og
from cadena import pilota_creible as pc
from cadena import pilota_morta as pmo
from cadena import smart_tagging as st
from cadena import xarxa_girada as xg
from cadena.__main__ import SENSE_COMPROVAR, fes, main
from inspeccio import besso
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

FOTOGRAMES = 3000
N = 4000                                       # el vídeo del bessó és més llarg que el seu ATD
TRAMS = ((1, 100, 1399), (2, 1600, 3499))
CASA = "team a"                                # el partit 3 de Metrica es diu «Team A» contra «Team B»
EQUIPS = {pm.H: "Barcelona", pm.A: "Atletic Club", None: "N/A"}           # els noms del Smart Tagging (DATA.md)
DEL_TIPUS = {"banda": "Throw-in", "corner": "Corner Kick", "porta": "Goal Kick", "falta": "Free Kick",
             "sortida": "Kick Off (After Goal)"}


def simulat(nivell: str = mfs.MITJA) -> tuple[tuple, tuple]:
    """Les etiquetes i les fases simulades del partit 3 de Metrica, com al banc (amb les llavors de provar), les del
    tros que porta el bessó."""
    etiquetes = tuple(e for e in mpa.etiquetes_de("metrica-3", "net", nivell, mfs.PROVA) if e.final < FOTOGRAMES)
    fases = tuple(f for f in fsm.fases_de("metrica-3", "net", nivell, mfs.PROVA) if f.final < FOTOGRAMES)
    return etiquetes, fases


def escriu_smart_tagging(cami: Path, etiquetes: tuple, fases: tuple, gira: bool = False) -> None:
    """Un fitxer SportsCode com el de DATA.md: les etiquetes, «SET PIECES» amb el tipus, i les fases, amb els sis codis
    per torn. Amb `gira`, els equips canviats."""
    equips = {**EQUIPS, pm.H: EQUIPS[pm.A], pm.A: EQUIPS[pm.H]} if gira else EQUIPS
    instancies = [(e.inici, e.final, "SET PIECES", equips[e.equip], DEL_TIPUS[e.tipus]) for e in etiquetes]
    instancies += [(f.inici, f.final, fs.CODIS[i % len(fs.CODIS)].upper(), equips[f.equip], None)
                   for i, f in enumerate(fases)]
    linies = ['<?xml version="1.0" encoding="utf-8"?>', "<file>", "<ALL_INSTANCES>"]
    for id_, (inici, final, codi, equip, tipus) in enumerate(sorted(instancies, key=lambda i: i[:2]), 1):
        grups = [("Team", equip), ("Half", "1st Half")] + ([("Type", tipus)] if tipus else [])
        linies.append(f"<instance><ID>{id_}</ID><start>{inici / 25:.3f}</start><end>{final / 25:.3f}</end>"
                      f"<code>{codi}</code>"
                      + "".join(f"<label><group>{g}</group><text>{v}</text></label>" for g, v in grups)
                      + "</instance>")
    cami.write_text("\n".join([*linies, "</ALL_INSTANCES>", "</file>"]) + "\n", encoding="utf-8")


@pytest.fixture(scope="module")
def dades(tmp_path_factory):
    arrel = besso.fes(tmp_path_factory.mktemp("besso"), FOTOGRAMES, segons_video=1)
    escriu_smart_tagging(arrel / "tactical" / st.FITXER, *simulat())
    return arrel


def amb_un_altre_smart_tagging(dades: Path, desti: Path, escriu=None) -> Path:
    """Una còpia del bessó amb el Smart Tagging que fa `escriu` (sense, si no se'n dona)."""
    shutil.copytree(dades, desti)
    (desti / "tactical" / st.FITXER).unlink()
    if escriu is not None:
        escriu(desti / "tactical" / st.FITXER)
    return desti


def executa(dades, sortida, **opcions):
    missatges = []
    codi = fes(dades, sortida, casa=CASA, trams=TRAMS, n=N, parla=missatges.append, **opcions)
    return codi, missatges


def etiquetes_de(cami: Path) -> list[str]:
    return [ls.split(",")[1] for ls in cami.read_text().splitlines()[1:]]


def test_escriu_un_fitxer_valid(dades, tmp_path):
    codi, missatges = executa(dades, tmp_path / "a.csv")
    assert codi == SENSE_COMPROVAR, missatges
    assert "⚠ Sense el validador oficial ni la finestra pública: el fitxer no queda comprovat" in missatges
    assert fitxer.comprova(tmp_path / "a.csv", N) is None
    etiquetes = etiquetes_de(tmp_path / "a.csv")
    assert set(etiquetes[100:1400]) <= {"H", "A", "D"} and {"H", "A"} <= set(etiquetes[100:1400])
    # fora de les parts, X; dins de la segona, on l'ATD ja no té ningú (s'acaba al 3000), la pilota és morta
    assert set(etiquetes[:100] + etiquetes[1400:1600] + etiquetes[3500:]) == {"X"}
    assert set(etiquetes[3000:3500]) == {"D"}
    assert "✓ Smart Tagging llegit: les pilotes aturades i les fases amb equip" in missatges
    assert "✓ L'equip de les fases és el que dona el model sense el Smart Tagging" in missatges
    assert not any(m.startswith("⚠ Smart Tagging") for m in missatges)


def test_fa_el_mateix_que_el_model_al_banc(dades, tmp_path):
    """L'ATD del bessó és el partit 3 de Metrica: llegit per la cadena, amb el Smart Tagging del fitxer, ha de donar el
    que donen les peces del banc d'A girat amb fases sobre el mateix partit, amb el mateix model i les mateixes
    etiquetes i fases, sense cap regla de més: la neteja, els senyals de les taules del banc, les probabilitats, la q,
    les pilotes aturades, les fases, la D impossible i el decodificador. És la prova que la lectura, l'orientació i les
    imatges quadren de cap a cap, també les del Smart Tagging: amb el `frame_id` sense el − 1, ja no hi quadraria."""
    trams = ((1, 0, FOTOGRAMES - 1),)
    assert fes(dades, tmp_path / "a.csv", casa=CASA, trams=trams, n=FOTOGRAMES, parla=[].append) == SENSE_COMPROVAR
    b = fonts.partit("metrica-3").tracking
    tros = replace(b, fotograma=b.fotograma[:FOTOGRAMES], pilota=b.pilota[:FOTOGRAMES], casa=b.casa[:FOTOGRAMES],
                   fora=b.fora[:FOTOGRAMES])
    netejades, net = pc.lluny(tros), pc.neteja(tros)
    assert not og.sense_tracking(net).any()                  # cap imatge buida: el prior no hi té res a fer
    p = SimpleNamespace(tracking=net, trams=trams)           # el que miren les taules del banc d'un partit
    e = model_girat.carrega()
    primer = model.probabilitats(e.primer, t3h.taula_primer(p))
    q = t3i.q_de(e.canvis, t3h.taula_segon(p, primer))
    proba = model.probabilitats(e.segon, t3m.taula_segon(p, primer, xg.probabilitats(e.xarxes, net, trams)))
    etiquetes, fases = simulat()
    assert etiquetes and fases
    amb_pm = mna.amb_la_d_impossible(pmo.amb_les_etiquetes(log_relativa(proba, e.prior), etiquetes, trams,
                                                           e.pilota_morta, dict(e.medianes)), netejades)
    relativa = mfs.relativa_amb(amb_pm, fases, trams, mfs.Suma(*e.fases), netejades)
    del_banc = og.lletres(mna.prediccio(relativa, q, trams, (e.w, e.lam, e.d_min)))
    np.testing.assert_array_equal(etiquetes_de(tmp_path / "a.csv"), del_banc)


def clon_oficial(carpeta: Path, finestra: np.ndarray | None) -> Path:
    """Un clon fals: el validador i, si se'n dona, la finestra pública (X fora de la finestra)."""
    validador = validador_fals(carpeta, 0)
    if finestra is not None:
        (carpeta / "evaluation" / "gt").mkdir()
        (carpeta / "evaluation" / "gt" / "BAR-ATH_possession_gt_public.csv").write_text(
            "frame,label\n" + "".join(f"{i},{e}\n" for i, e in enumerate(finestra)))
    return validador


def finestra_de(etiquetes: list[str], gira: bool = False) -> np.ndarray:
    veritat = np.full(N, "X", dtype=object)
    veritat[200:1300] = etiquetes[200:1300]
    return np.array([{"H": "A", "A": "H"}.get(e, e) for e in veritat]) if gira else veritat


def test_mira_amb_la_finestra_publica_que_h_i_a_vagin_be(dades, tmp_path):
    executa(dades, tmp_path / "primer.csv")
    etiquetes = etiquetes_de(tmp_path / "primer.csv")
    (tmp_path / "be").mkdir()
    codi, missatges = executa(dades, tmp_path / "be" / "a.csv",
                              validador=clon_oficial(tmp_path / "be", finestra_de(etiquetes)))
    assert codi == 0 and "✓ H i A, ben orientats (la finestra pública)" in missatges
    assert "✓ Sense desfasament de segons (la finestra pública)" in missatges
    (tmp_path / "girat").mkdir()
    codi, missatges = executa(dades, tmp_path / "girat" / "a.csv",
                              validador=clon_oficial(tmp_path / "girat", finestra_de(etiquetes, gira=True)))
    assert codi == 1 and "✗ H i A semblen girats (la finestra pública)" in missatges


def test_sense_la_finestra_publica_ho_diu_i_no_s_atura(dades, tmp_path):
    codi, missatges = executa(dades, tmp_path / "a.csv", validador=clon_oficial(tmp_path, None))
    assert codi == 0 and any(m.startswith("⚠ No trobo la finestra pública") for m in missatges)


def test_un_model_que_no_quadra_atura_la_cadena(dades, tmp_path, monkeypatch):
    shutil.copytree(model_girat.DIR_MODEL, tmp_path / "model-girat")
    fitxa = json.loads((tmp_path / "model-girat" / "fitxa.json").read_text())
    (tmp_path / "model-girat" / "fitxa.json").write_text(json.dumps({**fitxa, "lam": 0.0}))
    monkeypatch.setattr(model_girat, "DIR_MODEL", tmp_path / "model-girat")
    codi, missatges = executa(dades, tmp_path / "a.csv")
    assert codi == 1 and not (tmp_path / "a.csv").exists()
    assert any(m.startswith("✗ El model d'A girat amb fases no és el que diu la seva fitxa") for m in missatges)


def test_s_atura_si_l_equip_de_les_fases_surt_girat(dades, tmp_path):
    """Amb els equips del Smart Tagging canviats, les fases no quadren amb el model sense el Smart Tagging."""
    girat = amb_un_altre_smart_tagging(dades, tmp_path / "girat",
                                       lambda c: escriu_smart_tagging(c, *simulat(), gira=True))
    codi, missatges = executa(girat, tmp_path / "a.csv")
    assert codi == 1 and not (tmp_path / "a.csv").exists()
    assert any(m.startswith("✗ L'equip de les fases no és el que dona el model sense el Smart Tagging")
               for m in missatges)


@pytest.mark.parametrize("escriu, que", [
    (None, "✗ No trobo el Smart Tagging"),
    (lambda c: c.write_text("<file><ALL_INSTANCES><instance><start>no", encoding="utf-8"),
     "✗ El Smart Tagging no es pot llegir"),
    (lambda c: escriu_smart_tagging(c, simulat()[0], ()), "✗ El Smart Tagging no té cap fase amb equip"),
], ids=["sense", "mal fet", "sense fases"])
def test_sense_un_smart_tagging_que_es_pugui_fer_servir_s_atura(dades, tmp_path, escriu, que):
    altre = amb_un_altre_smart_tagging(dades, tmp_path / "altre", escriu)
    codi, missatges = executa(altre, tmp_path / "a.csv")
    assert codi == 1 and not (tmp_path / "a.csv").exists()
    assert any(m.startswith(que) for m in missatges), missatges


def test_cada_avis_del_smart_tagging_surt_un_sol_cop(dades, tmp_path):
    """Un avís que surt tres vegades diria quantes n'hi ha: surt un sol cop."""
    def amb_codis_nous(cami: Path) -> None:
        escriu_smart_tagging(cami, *simulat())
        nous = "".join(f"<instance><ID>{900 + i}</ID><start>{i}.0</start><end>{i}.5</end><code>UN CODI NOU</code>"
                       "</instance>" for i in range(3))
        cami.write_text(cami.read_text().replace("</ALL_INSTANCES>", nous + "</ALL_INSTANCES>"), encoding="utf-8")
    altre = amb_un_altre_smart_tagging(dades, tmp_path / "altre", amb_codis_nous)
    codi, missatges = executa(altre, tmp_path / "a.csv")
    assert codi == SENSE_COMPROVAR and missatges.count(st.AVIS_CODI) == 1


def test_dues_execucions_donen_el_mateix_fitxer(dades, tmp_path):
    executa(dades, tmp_path / "a.csv")
    primera = fitxer.empremta(tmp_path / "a.csv")
    codi, missatges = executa(dades, tmp_path / "a.csv")
    assert codi == SENSE_COMPROVAR and fitxer.empremta(tmp_path / "a.csv") == primera
    assert any("Igual que l'execució anterior" in m for m in missatges)
    assert (tmp_path / "a.csv.sha256").read_text().split()[0] == primera


def test_un_fitxer_diferent_no_s_accepta_fins_que_es_diu(dades, tmp_path):
    (tmp_path / "a.csv.sha256").write_text("0" * 64 + "  a.csv\n")
    for _ in range(2):                                   # no s'oblida de l'empremta bona a la segona
        codi, missatges = executa(dades, tmp_path / "a.csv")
        assert codi == 1 and any("Diferent de l'execució anterior" in m for m in missatges)
    assert (tmp_path / "a.csv.sha256").read_text().startswith("0" * 64)
    codi, _ = executa(dades, tmp_path / "a.csv", accepta_canvi=True)
    assert codi == SENSE_COMPROVAR and executa(dades, tmp_path / "a.csv")[0] == SENSE_COMPROVAR


def test_una_empremta_buida_compta_com_a_primera_execucio(dades, tmp_path):
    (tmp_path / "a.csv.sha256").write_text("")
    codi, missatges = executa(dades, tmp_path / "a.csv")
    assert codi == SENSE_COMPROVAR and any("Primera execució" in m for m in missatges)


@pytest.mark.parametrize("cas", ["sense validador", "finestra bona", "finestra girada", "sense finestra"])
def test_a_la_consola_no_hi_ha_cap_xifra(dades, tmp_path, capfd, cas):
    opcions = {}
    if cas != "sense validador":
        executa(dades, tmp_path / "primer.csv")
        finestra = None if cas == "sense finestra" else finestra_de(etiquetes_de(tmp_path / "primer.csv"),
                                                                     gira=cas == "finestra girada")
        (tmp_path / "clon").mkdir()
        opcions["validador"] = clon_oficial(tmp_path / "clon", finestra)
    capfd.readouterr()
    _, missatges = executa(dades, tmp_path / "a.csv", **opcions)
    assert len(missatges) > 5
    assert not any(c.isdigit() for m in missatges if not m.startswith("✓ Fitxer escrit") for c in m)
    assert capfd.readouterr() == ("", "")                # res no surt a la consola sense passar pels missatges


def test_sense_validador_l_ordre_no_el_dona_per_bo(dades, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("cadena.__main__.fes", functools.partial(fes, casa=CASA, trams=TRAMS, n=N))
    monkeypatch.setattr(sys, "argv", ["cadena", "--dades", str(dades), "--sortida", str(tmp_path / "a.csv"),
                                      "--permet-fora-del-volum", "--sense-validador"])
    assert main() == SENSE_COMPROVAR
    assert "sense el validador oficial no es pot donar per bo" in capsys.readouterr().out


def test_s_atura_si_no_troba_l_equip_de_casa(dades, tmp_path):
    missatges = []
    codi = fes(dades, tmp_path / "a.csv", casa="barcelona", trams=TRAMS, n=N, parla=missatges.append)
    assert codi == 1 and not (tmp_path / "a.csv").exists()
    assert any("equip" in m for m in missatges)


def test_s_atura_si_falta_l_atd(tmp_path):
    (tmp_path / "buida").mkdir()
    codi, missatges = executa(tmp_path / "buida", tmp_path / "a.csv")
    assert codi == 1 and any("ATD" in m for m in missatges)


def validador_fals(carpeta, surt):
    """Com l'oficial: escriu recomptes del fitxer i surt amb 0 si l'accepta o amb 1 si el rebutja."""
    validador = carpeta / "evaluation" / "validate_submission.py"
    validador.parent.mkdir()
    validador.write_text("import sys\nassert len(sys.argv) == 2\n"
                         f"print('OK' if {surt} == 0 else 'FAIL', '199319 rows, 412 possessions')\nsys.exit({surt})\n")
    return validador


@pytest.mark.parametrize("surt, accepta", [(0, True), (1, False)])
def test_passa_el_validador_oficial(dades, tmp_path, surt, accepta):
    codi, missatges = executa(dades, tmp_path / "a.csv", validador=validador_fals(tmp_path, surt))
    assert (codi == 0) is accepta
    assert any(("l'accepta" if accepta else "el rebutja") in m for m in missatges)


def test_el_que_escriu_el_validador_va_a_un_fitxer_i_no_a_la_consola(dades, tmp_path, capfd):
    _, missatges = executa(dades, tmp_path / "a.csv", validador=validador_fals(tmp_path, 0))
    assert "412 possessions" not in capfd.readouterr().out and not any("412" in m for m in missatges)
    assert "412 possessions" in (tmp_path / "a.csv.validacio.txt").read_text()


def test_el_validador_amb_un_cami_relatiu(dades, tmp_path, monkeypatch):
    # el validador s'executa des de la seva carpeta pare: un camí relatiu a on som ja no hi seria
    validador_fals(tmp_path, 0)
    monkeypatch.chdir(tmp_path.parent)
    relatiu = Path(tmp_path.name) / "evaluation" / "validate_submission.py"
    codi, _ = executa(dades, Path(tmp_path.name) / "a.csv", validador=relatiu)
    assert codi == 0


def test_sense_validador_oficial_no_dona_el_fitxer_per_bo(dades, tmp_path):
    codi, missatges = executa(dades, tmp_path / "a.csv", validador=tmp_path / "no-hi-es.py")
    assert codi == 1 and any(m.startswith("✗") and "validador" in m for m in missatges)


def test_un_error_de_biblioteca_no_porta_el_seu_text_a_la_consola(dades, tmp_path, monkeypatch, capsys):
    def falla(*_):
        raise IndexError("index 199320 is out of bounds for axis 0 with size 199319")
    monkeypatch.setattr("cadena.llegeix.tracking", falla)
    monkeypatch.setattr(sys, "argv", ["cadena", "--dades", str(dades), "--sortida", str(tmp_path / "a.csv"),
                                      "--permet-fora-del-volum", "--sense-validador"])
    assert main() == 1
    sortida = capsys.readouterr().out
    assert "IndexError" in sortida and "199320" not in sortida


def test_l_ordre_no_esborra_res_del_costat_de_la_sortida(dades, tmp_path, monkeypatch):
    (tmp_path / "tmp").mkdir()
    (tmp_path / "tmp" / "altres.txt").write_text("no l'esborris")
    monkeypatch.setattr(sys, "argv", ["cadena", "--dades", str(dades), "--sortida", str(tmp_path / "a.csv"),
                                      "--permet-fora-del-volum", "--sense-validador"])
    main()
    assert (tmp_path / "tmp" / "altres.txt").exists()
    assert not list(tmp_path.glob(".cadena-*"))


def test_l_ordre_no_escriu_fora_del_volum(dades, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["cadena", "--dades", str(dades), "--sortida", str(tmp_path / "a.csv")])
    assert main() == 1
    assert "ha d'anar dins" in capsys.readouterr().out
    assert not (tmp_path / "a.csv").exists()


def test_l_ordre_no_escriu_dins_de_les_dades(dades, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["cadena", "--dades", str(dades), "--sortida", str(dades / "a.csv"),
                                      "--permet-fora-del-volum"])
    assert main() == 1
    assert "dins de la carpeta de les dades" in capsys.readouterr().out


def test_ni_dins_de_les_dades_amb_majuscules_diferents(tmp_path, monkeypatch, capsys):
    (tmp_path / "Dades").mkdir()
    if not (tmp_path / "dades").exists():
        pytest.skip("aquest disc distingeix majúscules")
    monkeypatch.setattr(sys, "argv", ["cadena", "--dades", str(tmp_path / "Dades"),
                                      "--sortida", str(tmp_path / "dades" / "a.csv"), "--permet-fora-del-volum"])
    assert main() == 1
    assert "dins de la carpeta de les dades" in capsys.readouterr().out
