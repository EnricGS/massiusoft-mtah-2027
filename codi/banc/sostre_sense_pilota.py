"""El sostre de les xarxes que veuen els jugadors també sense pilota: quant guanyaria A xarxes si el segon encertés
als forats, abans d'escriure'n el pla (`docs/pla-tocs.md`, «El sostre de les xarxes sense pilota»). Només per saber-ho.

    cd codi && uv run python -I -m banc.sostre_sense_pilota

Sense pilota, tot el que veuen les xarxes d'ara és 0 (`cadena/xarxa.py`): als forats (els trossos sense pilota a
l'escenari, amb 6 imatges més a cada banda, com a `sostre_curtes`) només hi arriba el que veuen a ±2 s. Unes xarxes
que veiessin els jugadors també sense pilota canviarien les probabilitats del segon als forats, i res més. Amb el que
ha desat el banc de la T3p (les probabilitats d'A xarxes i la seva q) i el decodificador triat a cada partit a la
veritat de toc pel banc de la T3r (es comprova que l'spellF1 de cada partit és el del banc), a la veritat de toc:

1. **Quant falla ara:** la part de les imatges puntuades que són als forats, i on la veritat és d'un equip, la part
   on el segon, les xarxes i A xarxes hi encerten l'equip, on es veu la pilota i als forats.
2. **El sostre:** A xarxes, tornant a decodificar, amb el segon perfecte (a tot arreu, on es veu la pilota o als
   forats), i als forats, només l'equip: *segur* (l'altre equip, impossible; la D, com estava), *encertat* (l'H i l'A
   girats on el segon s'hi equivoca, amb la confiança que tenia) i *com on es veu la pilota* (girats a trossos
   d'errors triats a l'atzar, fins que el segon hi encerta l'equip tant com on es veu la pilota; i fent-ne només la
   meitat o una quarta part del camí). I amb la q perfecta als forats, sola (la de `sostre_curtes`) i amb l'equip
   segur.
3. **El criteri, als ×¼:** si el sostre passaria. Si el segon perfecte als forats no hi passa, cap xarxa que només
   hi millori l'equip no hi pot passar.

Escriu `resultats/sostre-sense-pilota.md`. Tot són dades obertes.
"""

from __future__ import annotations

import itertools
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace

import numpy as np
import pandas as pd

from banc import analisi_t3p as t3p
from banc import analisi_t3q as t3q
from banc import analisi_t3r as an
from banc import avalua, fonts
from banc import decodificador_tocs as t3
from banc import model_a_canvis as t3i
from banc import model_a_partit as mp
from banc import sostre_curtes as sc
from banc import veritat_toc as vt
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ESCENARIS = t3q.ESCENARIS                           # el net, els quatre ×¼ i «partit ×¼»
BASE = sc.BASE                                      # A xarxes
SEGUR = sc.SEGUR
LLAVOR = 0
SEGON = "el segon perfecte"
SEGON_PILOTA = "el segon perfecte on es veu la pilota"
SEGON_FORATS = "el segon perfecte als forats"
EQUIP_SEGUR = "als forats, l'equip segur"
EQUIP_ENCERTAT = "als forats, l'equip encertat"
COM_AMB_PILOTA = "als forats, l'equip com on es veu la pilota"
MIG_CAMI = "als forats, l'equip a mig camí"
QUART_DE_CAMI = "als forats, l'equip a un quart del camí"
CAMI = {COM_AMB_PILOTA: 1.0, MIG_CAMI: 0.5, QUART_DE_CAMI: 0.25}  # quina part dels encerts que falten
Q_FORATS = sc.Q_ALS_FORATS                          # la q perfecta als forats
EQUIP_I_Q = "als forats, l'equip segur i la q perfecta"
SOSTRES = (SEGON, SEGON_PILOTA, SEGON_FORATS, EQUIP_SEGUR, EQUIP_ENCERTAT, *CAMI, Q_FORATS, EQUIP_I_Q)
AMB_PILOTA, ALS_FORATS = "on es veu la pilota", "als forats"
SEGON_, XARXES_ = "el segon", "les xarxes"
QUI = (SEGON_, XARXES_, BASE)
EQUIPS = list(pm.POSSESSION_LABELS)                 # les columnes de l'H i l'A
GIRATS = EQUIPS[::-1]
Tram = tuple[int, int]


def dins(n: int, trams: list[Tram]) -> np.ndarray:
    """Les imatges de `trams` ([inici, final))."""
    out = np.zeros(n, dtype=bool)
    for a, b in trams:
        out[a:b] = True
    return out


def d_equip(probes: np.ndarray, toc: np.ndarray, on: np.ndarray) -> np.ndarray:
    """Les imatges d'`on` on la veritat és d'un equip i les probabilitats (o la relativa) hi diuen alguna cosa."""
    return on & np.isin(toc, EQUIPS) & np.isfinite(probes[:, EQUIPS]).all(axis=1)


def l_equip(probes: np.ndarray) -> np.ndarray:
    """A cada imatge, l'equip que hi dona més probabilitat (o relativa): l'H o l'A."""
    return np.asarray(EQUIPS)[np.argmax(np.nan_to_num(probes[:, EQUIPS], nan=-np.inf), axis=1)]


def encerts(probes: np.ndarray, toc: np.ndarray, on: np.ndarray) -> tuple[int, int]:
    """A les imatges d'`on` on la veritat és d'un equip: quantes n'hi ha, i a quantes l'equip més probable és el bo."""
    m = d_equip(probes, toc, on)
    return int(m.sum()), int((l_equip(probes[m]) == toc[m]).sum())


def encerts_pred(pred: np.ndarray, toc: np.ndarray, on: np.ndarray) -> tuple[int, int]:
    """A les imatges d'`on` on la veritat és d'un equip: quantes n'hi ha, i a quantes la predicció hi dona aquest."""
    m = on & np.isin(toc, EQUIPS)
    return int(m.sum()), int((pred[m] == toc[m]).sum())


def perfecte(relativa: np.ndarray, toc: np.ndarray, on: np.ndarray) -> np.ndarray:
    """La relativa amb el segon perfecte a les imatges d'`on`: segura a la classe de la veritat, impossible a les
    altres (on la veritat és X, com estava)."""
    out = relativa.copy()
    m = on & np.isin(toc, (pm.H, pm.A, pm.D))
    out[m] = -SEGUR
    out[np.flatnonzero(m), toc[m]] = SEGUR
    return out


def equip_encertat(relativa: np.ndarray, toc: np.ndarray, on: np.ndarray) -> np.ndarray:
    """La relativa amb l'H i l'A girats a les imatges d'`on` on el segon s'equivoca d'equip: el bo, amb la confiança
    que tenia l'altre. La D, com estava."""
    out = relativa.copy()
    m = d_equip(relativa, toc, on)
    gira = np.flatnonzero(m)[l_equip(relativa[m]) != toc[m]]
    out[np.ix_(gira, EQUIPS)] = relativa[np.ix_(gira, GIRATS)]
    return out


def equip_segur(relativa: np.ndarray, toc: np.ndarray, on: np.ndarray) -> np.ndarray:
    """Com `equip_encertat`, i l'altre equip, impossible: el segon sap l'equip del cert, i si és pilota morta, com
    estava."""
    out = equip_encertat(relativa, toc, on)
    m = np.flatnonzero(d_equip(relativa, toc, on))
    altre = np.where(toc[m] == pm.H, pm.A, pm.H)
    out[m, altre] = -SEGUR
    return out


def trossos(mascara: np.ndarray) -> list[Tram]:
    """Els trossos [a, b) seguits de `mascara`."""
    vores = np.diff(np.concatenate([[0], mascara.astype(np.int8), [0]]))
    return list(zip(np.flatnonzero(vores == 1).tolist(), np.flatnonzero(vores == -1).tolist()))


def errors_d_equip(relativa: np.ndarray, toc: np.ndarray, on: np.ndarray) -> np.ndarray:
    """Les imatges d'`on` on la veritat és d'un equip i el segon dona més probabilitat a l'altre."""
    m = d_equip(relativa, toc, on)
    errors = np.zeros(len(toc), dtype=bool)
    errors[np.flatnonzero(m)[l_equip(relativa[m]) != toc[m]]] = True
    return errors


def gira_a_trossos(relativa: np.ndarray, errors: np.ndarray, falten: int, rng: np.random.Generator) -> np.ndarray:
    """La relativa amb l'H i l'A girats a trossos seguits d'`errors` triats a l'atzar, fins a haver-ne girat `falten`
    imatges o més (si `falten` ≤ 0, com estava)."""
    out = relativa.copy()
    tria = trossos(errors)
    for i in rng.permutation(len(tria)):
        if falten <= 0:
            break
        a, b = tria[i]
        out[a:b, EQUIPS] = relativa[a:b, GIRATS]
        falten -= b - a
    return out


def com_amb_pilota(relativa: np.ndarray, toc: np.ndarray, al_forat: np.ndarray, valides: np.ndarray,
                   rng: np.random.Generator, part: float = 1.0) -> np.ndarray:
    """La relativa amb l'H i l'A girats, als forats, a trossos d'errors d'equip triats a l'atzar, fins que el segon
    hi encerta l'equip tant com on es veu la pilota (si ja hi encerta tant, com estava). Amb `part`, només aquesta
    part dels encerts que li falten. Només a les `valides`."""
    n_pilota, e_pilota = encerts(relativa, toc, valides & ~al_forat)
    n_forat, e_forat = encerts(relativa, toc, valides & al_forat)
    if n_pilota == 0 or n_forat == 0:
        return relativa.copy()
    falten = int(np.ceil(part * (e_pilota / n_pilota * n_forat - e_forat)))
    return gira_a_trossos(relativa, errors_d_equip(relativa, toc, valides & al_forat), falten, rng)


def tasca(nom_escenari: tuple[str, str]) -> dict[str, list[dict]]:
    nom, escenari = nom_escenari
    de_sempre = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    p_toc = replace(de_sempre, veritat=toc)
    trams = avalua.trams_valids(p_toc)
    valides = dins(len(toc), trams)
    vista = ~np.isnan(de_sempre.tracking.pilota[:, 0])
    al_forat = sc.forats(vista)
    probes, prior = mp.segon((nom, mp.SIS), entrena=False)
    relativa = log_relativa(probes[escenari].astype(float), prior)
    q = mp.q((nom, mp.SIS), entrena=False)[escenari].astype(float)
    de_les_xarxes = mp.xarxes_de_la_prova((nom, mp.SIS))[escenari].astype(float)
    w, lam, d_min = an.triades()[an.XARXES_TOC][nom]

    def decodifica(relativa_: np.ndarray, q_: np.ndarray = q) -> np.ndarray:
        return t3i.per_trams(relativa_, q_, de_sempre.trams, w, lam, int(d_min))

    pred = decodifica(relativa)
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}

    def fila(sostre: str, prediccio: np.ndarray) -> dict:
        return {**comu, "sostre": sostre, "spell_f1": avalua.puntua(p_toc, prediccio)["spell_f1"]}

    forat = valides & al_forat
    q_bona = np.where(al_forat, sc.q_perfecta(toc, trams), q)
    files = [fila(BASE, pred),
             fila(SEGON, decodifica(perfecte(relativa, toc, valides))),
             fila(SEGON_PILOTA, decodifica(perfecte(relativa, toc, valides & ~al_forat))),
             fila(SEGON_FORATS, decodifica(perfecte(relativa, toc, forat))),
             fila(EQUIP_SEGUR, decodifica(equip_segur(relativa, toc, forat))),
             fila(EQUIP_ENCERTAT, decodifica(equip_encertat(relativa, toc, forat))),
             *(fila(nom_, decodifica(com_amb_pilota(relativa, toc, al_forat, valides, np.random.default_rng(LLAVOR),
                                                    part))) for nom_, part in CAMI.items()),
             fila(Q_FORATS, decodifica(relativa, q_bona)),
             fila(EQUIP_I_Q, decodifica(equip_segur(relativa, toc, forat), q_bona))]
    quants = []
    for on, mascara in ((AMB_PILOTA, valides & ~al_forat), (ALS_FORATS, forat)):
        puntuades = int((mascara & (toc != pm.X)).sum())
        for qui, (n, e) in ((SEGON_, encerts(relativa, toc, mascara)), (XARXES_, encerts(de_les_xarxes, toc, mascara)),
                            (BASE, encerts_pred(pred, toc, mascara))):
            quants.append({**comu, "on": on, "qui": qui, "puntuades": puntuades, "n": n, "encerts": e})
    return {"files": files, "quants": quants}


def taula_forats(quants: pd.DataFrame) -> pd.DataFrame:
    """Per escenari: la part de les imatges puntuades que són als forats, i la part de les d'un equip on cadascú hi
    encerta l'equip, on es veu la pilota i als forats (els deu partits junts)."""
    una = quants[quants["qui"] == BASE].groupby(["escenari", "on"])["puntuades"].sum().unstack("on")
    t = pd.DataFrame({"part als forats": una[ALS_FORATS] / (una[ALS_FORATS] + una[AMB_PILOTA])})
    g = quants.groupby(["escenari", "qui", "on"])[["n", "encerts"]].sum()
    part = (g["encerts"] / g["n"]).unstack(["qui", "on"])
    for qui in QUI:
        for on in (AMB_PILOTA, ALS_FORATS):
            t[f"{qui}, {on}"] = part[(qui, on)]
    errors = (g["n"] - g["encerts"]).xs(BASE, level="qui").unstack("on")
    t[f"errors d'{BASE} als forats"] = errors[ALS_FORATS] / (errors[ALS_FORATS] + errors[AMB_PILOTA])
    return t3q.ordena(t)


def main() -> None:
    with ProcessPoolExecutor(max_workers=10) as feina:
        tasques = list(feina.map(tasca, itertools.product(fonts.NOMS, ESCENARIS)))
    files, quants = (pd.DataFrame([f for t in tasques for f in t[k]]) for k in ("files", "quants"))
    an.comprova(files, (an.XARXES,))
    sortida = [
        "# Banc obert · El sostre de les xarxes sense pilota", "",
        "Generat amb `uv run python -I -m banc.sostre_sense_pilota`, amb el que han desat `banc.model_a_partit` i",
        f"`banc.model_a_q`. Dades obertes. Només per saber-ho. A la veritat de toc, amb el decodificador d'{BASE}",
        "triat a cada partit a la veritat de toc (✓ comprovat: el mateix spellF1 que el banc de la T3r).", "",
        "## Quant falla ara als forats", "",
        f"Un *forat* és un tros sense pilota a l'escenari, amb {t3i.K} imatges més a cada banda. *Part als forats:*",
        "de les imatges puntuades. A la resta, on la veritat és d'un equip, la part on l'equip més probable és el bo",
        f"(*{SEGON_}*, amb la relativa; *{XARXES_}*, la mitjana de les cinc) i on {BASE} hi dona el bo, on es veu la",
        f"pilota i als forats. *Errors d'{BASE} als forats:* dels seus errors d'equip, la part que hi és.", "",
        t3p.md(taula_forats(quants)), "",
        "## El sostre", "",
        f"spellF1 d'{BASE} (mitjana dels deu partits) i quant hi guanya, tornant a decodificar. *{SEGON}:* segur a",
        "la classe de la veritat (H, A o D) i impossible a les altres; a tot arreu, on es veu la pilota o als forats.",
        "*Als forats, l'equip:* només on la veritat és d'un equip; *segur*, l'altre equip impossible i la D com",
        "estava; *encertat*, l'H i l'A girats on el segon s'hi equivoca, amb la confiança que tenia; *com on es veu la",
        "pilota*, girats a trossos d'errors triats a l'atzar fins que el segon hi encerta l'equip tant com on es veu",
        "la pilota; *a mig camí* i *a un quart del camí*, només la meitat o la quarta part dels encerts que li",
        f"falten. *{Q_FORATS}:* la de `sostre_curtes`, sola i amb l'equip segur.", "",
        t3p.md(sc.taula_guany(files, SOSTRES)), "",
        "## Passaria el criteri als ×¼?", "",
        f"El guany de mitjana · en quants partits guanya · ✓ si passaria (> {t3.SOROLL}, l'interval del 95 % per",
        f"sobre de zero i {t3.GUANYA_MINIM} partits de 10 o més).", "",
        *sc.taula_criteri(files, SOSTRES), "",
    ]
    an.DIR_RESULTATS.mkdir(exist_ok=True)
    (an.DIR_RESULTATS / "sostre-sense-pilota.md").write_text("\n".join(sortida))
    print("\n".join(sortida))


if __name__ == "__main__":
    main()
