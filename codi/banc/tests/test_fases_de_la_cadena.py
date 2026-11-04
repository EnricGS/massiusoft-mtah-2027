"""La comprovació de l'equip de les fases de la cadena (C2), als deu partits oberts: amb les fases simulades als nivells
bo, mitjà i dolent quadra amb A camp girat sense el Smart Tagging, i amb els equips girats, no.

A camp girat és el del banc de la T3ad (cada partit, amb peces que no l'han vist i el decodificador que va triar), de la
memòria cau, i les fases, les simulades de la T3ak amb les llavors de provar."""

from __future__ import annotations

import pytest

from banc import fases_simulades as fsm
from banc import fonts
from banc import model_a_partit as mp
from banc import model_camp_girat as mcg
from banc import model_fases as mfs
from banc import model_girat_fases as mgf
from banc import model_neteja_aire as mna
from cadena import opcio_girat as og


def _hi_ha_el_banc() -> bool:
    """Si hi ha les probabilitats d'A camp girat a la memòria cau del banc: les fa `python -I -m banc.model_camp_girat`,
    i un clon nou no les té."""
    try:
        mcg.de_qui(mcg.A_GIRAT, fonts.NOMS[0])
    except RuntimeError:
        return False
    return True


pytestmark = pytest.mark.skipif(not _hi_ha_el_banc(), reason="falta la memòria cau del banc d'A camp girat "
                                                               "(python -I -m banc.model_camp_girat)")


@pytest.fixture(scope="module")
def triades():
    return mgf.de_la_t3ad()["triades"][mcg.A_GIRAT]


@pytest.mark.parametrize("escenari", ["net", mp.PARTIT])
@pytest.mark.parametrize("nom", fonts.NOMS)
def test_l_equip_de_les_fases_quadra_als_deu_partits_i_girat_no(triades, nom, escenari):
    de_sempre, r, q, netejades = mgf.base(mcg.A_GIRAT, nom, escenari)
    sense = mna.prediccio(mna.amb_la_d_impossible(r, netejades), q, de_sempre.trams, tuple(triades[nom]))
    for nivell in ("bo", mfs.MITJA, "dolent"):
        fases = fsm.fases_de(nom, escenari, nivell, mfs.PROVA)
        assert fases and og.equip_quadra(sense, fases, de_sempre.trams), nivell
        girades = tuple(f._replace(equip=1 - f.equip) for f in fases)
        assert not og.equip_quadra(sense, girades, de_sempre.trams), nivell
