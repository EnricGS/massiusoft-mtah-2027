"""La comprovació amb la finestra pública: el que diu en cada cas, i que no s'atura mai si no és per H i A girats."""

from __future__ import annotations

import numpy as np
import pytest

from cadena import publics
from possessio.oficial import possession_metrics as pm


@pytest.mark.parametrize("tal, girat, esperat", [
    ((0.6, 0.9), (0.1, 0.3), True),
    ((0.1, 0.3), (0.6, 0.9), False),
    ((0.0, 0.0), (0.0, 0.38), False),          # un empat a l'spellF1 no amaga que estan girats
    ((0.0, 0.38), (0.0, 0.0), True),
    ((0.6, 0.3), (0.1, 0.9), None),
    ((0.5, 0.5), (0.5, 0.5), None),
])
def test_ben_orientats(tal, girat, esperat):
    assert publics.ben_orientats(tal, girat) is esperat


def test_mou_endavant_i_enrere():
    pred = np.array([pm.H, pm.A, pm.D, pm.H], dtype=np.int8)
    np.testing.assert_array_equal(publics.mou(pred, 1), [pm.X, pm.H, pm.A, pm.D])
    np.testing.assert_array_equal(publics.mou(pred, -1), [pm.A, pm.D, pm.H, pm.X])


def escriu(cami, codis):
    cami.parent.mkdir(parents=True, exist_ok=True)
    lletres = np.array(["H", "A", "D", "X"])[codis]
    cami.write_text("frame,label\n" + "".join(f"{i},{e}\n" for i, e in enumerate(lletres)))
    return cami


def possessions(n=3000, llavor=1):
    """Possessions d'uns segons, amb pilota morta entremig."""
    rng = np.random.default_rng(llavor)
    codis, i = np.empty(n, np.int8), 0
    while i < n:
        llarg = int(rng.integers(150, 400))
        codis[i:i + llarg] = rng.choice([pm.H, pm.A, pm.D], p=[0.4, 0.4, 0.2])
        i += llarg
    return codis


def comprova(tmp_path, veritat, pred, finestres=1):
    for k in range(finestres):
        escriu(tmp_path / "clon" / "evaluation" / "gt" / f"P{k}_possession_gt_public.csv", veritat)
    missatges = []
    bo = publics.comprova(escriu(tmp_path / "a.csv", pred), tmp_path / "clon", missatges.append)
    return bo, missatges


def test_les_etiquetes_bones(tmp_path):
    veritat = possessions()
    assert comprova(tmp_path, veritat, veritat) == (True, ["✓ H i A, ben orientats (la finestra pública)",
                                                           "✓ Sense desfasament de segons (la finestra pública)"])


def test_h_i_a_girats_aturen(tmp_path):
    veritat = possessions()
    bo, missatges = comprova(tmp_path, veritat, publics.GIRA[veritat])
    assert not bo and "✗ H i A semblen girats (la finestra pública)" in missatges


def test_un_fitxer_desfasat_avisa_i_no_atura(tmp_path):
    veritat = possessions()
    bo, missatges = comprova(tmp_path, veritat, publics.mou(veritat, 250))
    assert bo and "⚠ Amb la finestra pública, el fitxer potser va desfasat uns segons" in missatges


@pytest.mark.parametrize("finestres", [0, 2])
def test_sense_una_sola_finestra_avisa_i_no_atura(tmp_path, finestres):
    veritat = possessions()
    bo, missatges = comprova(tmp_path, veritat, veritat, finestres)
    assert bo and missatges == ["⚠ No trobo la finestra pública al clon oficial: no he mirat si H i A van bé"]


def test_si_no_es_pot_puntuar_avisa_amb_el_tipus_i_prou(tmp_path):
    veritat = possessions()
    bo, missatges = comprova(tmp_path, veritat, veritat[:-7])
    assert bo and missatges == ["⚠ No he pogut puntuar la finestra pública (ValueError): no he mirat si H i A van bé"]
