"""El decodificador amb tocs (T3 del pla per tocs, `docs/pla-tocs.md`; D-24).

És el Viterbi d'A (`cadena.decodifica`), amb la durada mínima i les mateixes probabilitats, però el cost de canviar
depèn de la imatge:
- **Els candidats:** els tocs (`cadena.tocs`) en sèries seguides del mateix equip, fins que toca l'altre. Una sèrie
  és un candidat a canvi al seu primer toc si té `control` tocs o més: amb 2, un toc i prou (un rebot, una
  desviació) no ho és. Cap sèrie passa d'una part a l'altra.
- **Zero** per passar a l'equip d'un candidat, a la imatge del seu primer toc (també des de la D).
- **`lam_vis`** per passar d'H a A, o al revés, amb la pilota visible i cap candidat: car, o impossible (`inf`).
- **`lam`, com A**, dins d'un forat de la pilota, i per qualsevol altre canvi amb la D.

El Viterbi d'aquí fa el mateix que `possessio.decodificacio._viterbi_durada_minima` (amb costos iguals a totes les
imatges dona el mateix camí), però amb el cost de cada imatge, i en Python pla: amb tres classes, les sumes de
cada classe es fan amb sumes acumulades i va més de pressa que amb numpy imatge a imatge.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from cadena.model import CLASSES
from cadena.tocs import Tocs
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

H, A, D = (CLASSES.index(c) for c in (pm.H, pm.A, pm.D))
SENSE = -1


@dataclass(frozen=True)
class Parametres:
    control: int = 2            # tocs seguits del mateix equip perquè la sèrie sigui un candidat
    lam_vis: float = 64.0       # canviar d'H a A amb la pilota visible i cap candidat (math.inf: impossible)
    lam: float = 8.0            # dins d'un forat, i amb la D
    d_min: int = 25


def candidats(tocs: Tocs, trams: tuple[tuple[int, int, int], ...], control: int) -> tuple[np.ndarray, np.ndarray]:
    """(imatges, equips) del primer toc de cada sèrie de `control` tocs o més, en ordre."""
    imatges, equips = [], []
    for _, inici, ultim in trams:
        dins = (tocs.imatge >= inici) & (tocs.imatge <= ultim)
        i, e = tocs.imatge[dins], tocs.equip[dins]
        if len(i) == 0:
            continue
        nova = np.r_[True, e[1:] != e[:-1]]
        inicis = np.flatnonzero(nova)
        llargades = np.diff(np.r_[inicis, len(i)])
        bones = inicis[llargades >= control]
        imatges.append(i[bones])
        equips.append(e[bones])
    if not imatges:
        return np.array([], dtype=int), np.array([], dtype=np.int8)
    return np.concatenate(imatges).astype(int), np.concatenate(equips).astype(np.int8)


def costos(visible: np.ndarray, imatges: np.ndarray, equips: np.ndarray, par: Parametres) -> np.ndarray:
    """(n, 3, 3): el cost de passar de la classe i a la j a cada imatge (la diagonal no es fa servir)."""
    n = len(visible)
    c = np.full((n, 3, 3), par.lam, float)
    entre_equips = np.where(visible, par.lam_vis, par.lam)
    c[:, H, A] = entre_equips
    c[:, A, H] = entre_equips
    a_quin = np.full(n, SENSE)
    a_quin[imatges] = [CLASSES.index(e) for e in equips]
    for j in (H, A):
        c[a_quin == j, :, j] = 0.0
    return c


def viterbi(em: np.ndarray, cost: np.ndarray, d: int) -> np.ndarray:
    """El camí (índexs de classe) que maximitza la suma de `em` menys els costos dels canvis, sense cap tram de
    menys de `d` imatges llevat del primer i de l'últim. `em` (n, k); `cost` (n, k, k)."""
    n, k = em.shape
    menys_inf = -math.inf
    e, c = em.tolist(), cost.tolist()
    p = np.cumsum(em, axis=0).tolist()
    madur = [[menys_inf] * k for _ in range(n)]       # el millor amb un tram de d imatges o més, que acaba a t
    entra = [[menys_inf] * k for _ in range(n)]       # el millor entrant a la classe j a t
    de = [[0] * k for _ in range(n)]
    queda = [[True] * k for _ in range(n)]
    madur[0] = list(e[0])
    for t in range(1, n):
        abans, ara, ct = madur[t - 1], e[t], c[t]
        s = t - d + 1
        for j in range(k):
            millor, origen = menys_inf, 0
            for i in range(k):
                if i != j:
                    v = abans[i] - ct[i][j]
                    if v > millor:
                        millor, origen = v, i
            entra[t][j] = millor + ara[j]
            de[t][j] = origen
            seguir = abans[j] + ara[j]
            madura = entra[s][j] + p[t][j] - p[s][j] if s >= 1 else menys_inf
            if seguir >= madura:
                madur[t][j] = seguir
            else:
                madur[t][j], queda[t][j] = madura, False
    return _enrere(madur, entra, de, queda, p, n, k, d)


def _enrere(madur, entra, de, queda, p, n: int, k: int, d: int) -> np.ndarray:
    """L'últim tram pot ser més curt que `d`: també es mira entrar a les últimes d − 1 imatges."""
    millor, j, inici = -math.inf, 0, None
    for classe in range(k):
        if madur[n - 1][classe] > millor:
            millor, j, inici = madur[n - 1][classe], classe, None
        for s in range(max(1, n - d + 1), n):
            v = entra[s][classe] + p[n - 1][classe] - p[s][classe]
            if v > millor:
                millor, j, inici = v, classe, s
    cami = np.empty(n, dtype=np.int64)
    t = n - 1
    while t >= 0:
        if inici is None:
            while t > 0 and queda[t][j]:
                cami[t] = j
                t -= 1
            if t == 0:
                cami[0] = j
                break
            inici = t - d + 1
        cami[inici:t + 1] = j
        j, t, inici = de[inici][j], inici - 1, None
    return cami


def per_trams(proba: np.ndarray, prior: np.ndarray, trams: tuple[tuple[int, int, int], ...], visible: np.ndarray,
              tocs: Tocs, par: Parametres) -> np.ndarray:
    """Els codis de la mètrica: H, A o D dins de cada part, i X fora (com `cadena.decodifica.per_trams`)."""
    relativa = log_relativa(proba, prior)
    imatges, equips = candidats(tocs, trams, par.control)
    cost = costos(visible, imatges, equips, par)
    out = np.full(len(proba), pm.X, dtype=np.int8)
    for _, inici, fi in trams:
        cami = viterbi(relativa[inici:fi + 1], cost[inici:fi + 1], par.d_min)
        out[inici:fi + 1] = np.asarray(CLASSES)[cami]
    return out
