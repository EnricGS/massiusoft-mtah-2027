"""Com són els errors d'equip d'A sense pilota on es veu la pilota, abans de triar la idea següent (`docs/pla-tocs.md`,
«Com són els errors d'equip on es veu la pilota»). Només per saber-ho.

    cd codi && uv run python -I -m banc.errors_amb_pilota

Amb el que ha desat el banc de la T3t (les probabilitats d'A sense pilota i la q d'A xarxes) i el decodificador triat
a cada partit a la veritat de toc (es comprova que l'spellF1 de cada partit és el del banc). Al net, als quatre ×¼ i a
«partit ×¼», a la veritat de toc, on es veu la pilota (fora dels forats, com a `marge_sense_pilota`) i la veritat és
d'un equip:

1. **Els errors,** les imatges on la predicció no hi dona aquest equip: si hi dona l'altre o la D. I dels que hi
   donen l'altre equip:
   - **de quina possessió de la veritat són:** quant dura (com a `analisi_t3q`) i què hi ha abans (una aturada,
     l'altre equip o la vora del tram);
   - **on cauen dins la possessió:** tota (la predicció no hi dona mai el seu equip), al començament (hi arriba
     tard), al final (se'n va d'hora) o al mig;
   - **a quina distància del toc:** del començament o del final de la possessió, el que sigui més a prop;
   - **què en diu el segon:** si hi encerta l'equip (aleshores, el que s'equivoca és el decodificador) i, si no, si
     hi dubta o n'està segur (la probabilitat que dona a l'equip bo davant de l'altre, amb la relativa).
2. **Els sostres,** l'equip encertat del segon (`ssp.equip_encertat`) només en una part d'aquests errors, tornant a
   decodificar: a les possessions de menys de 5 s o a les altres, a menys d'1 s del toc o més lluny, on el segon
   dubta o on n'està segur. I on el segon ja encerta i la predicció dona l'altre equip, el segon perfecte: el que hi
   perd el decodificador. Amb el criteri contra A xarxes, als ×¼.

Escriu `resultats/errors-amb-pilota.md`. Tot són dades obertes.
"""

from __future__ import annotations

import itertools
import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace

import numpy as np
import pandas as pd

from banc import analisi_t3p as t3p
from banc import analisi_t3q as t3q
from banc import analisi_t3r as an
from banc import avalua, fonts
from banc import canvis_falsos as cf
from banc import decodificador_tocs as t3
from banc import marge_sense_pilota as mm
from banc import model_a_canvis as t3i
from banc import model_a_partit as mp
from banc import model_a_sense_pilota as msp
from banc import sostre_curtes as sc
from banc import sostre_sense_pilota as ssp
from banc import veritat_toc as vt
from possessio.decodificacio import log_relativa
from possessio.oficial import possession_metrics as pm

ESCENARIS = t3q.ESCENARIS                           # el net, els quatre ×¼ i «partit ×¼»
QUARTS = t3.QUARTS
A_SENSE = msp.A_SENSE
BASE = mm.BASE
TOL = cf.TOL                                        # 1 s
DUBTE = 0.1                                         # per sota, el segon està segur de l'altre equip
L_ALTRE, LA_D, RES = "l'altre equip", "la D", "res"
DONA = (L_ALTRE, LA_D)
DESPRES_D, DESPRES_ALTRE, VORA = "després d'una aturada", "després de l'altre equip", "a la vora del tram"
ABANS = (DESPRES_D, DESPRES_ALTRE, VORA)
TOTA, AL_COMENCAMENT, AL_FINAL, AL_MIG = "tota la possessió", "al començament (tard)", "al final (d'hora)", "al mig"
LLOCS = (TOTA, AL_COMENCAMENT, AL_FINAL, AL_MIG)
LIMITS_DISTANCIA = (0, pm.FPS // 2, pm.FPS, 2 * pm.FPS, np.inf)
DISTANCIES = ("<0,5 s del toc", "0,5-1 s", "1-2 s", "≥2 s")
ENCERTA, DUBTA, SEGUR = "el segon l'encerta", f"el segon dubta (≥{DUBTE})", f"el segon n'està segur (<{DUBTE})"
SEGONS = (ENCERTA, DUBTA, SEGUR)
DURADES = t3q.NOMS_DURADA
TRETS = ("dona", "durada", "abans", "lloc", "distancia", "segon")
EQUIP = mm.EQUIP_PILOTA
CURTES = "… a les possessions de menys de 5 s"
LLARGUES = "… a les de 5 s o més"
A_PROP = "… a menys d'1 s del toc"
LLUNY = "… a 1 s o més"
SI_DUBTA = "… on el segon dubta"
SI_SEGUR = "… on el segon n'està segur"
DECODIFICADOR = "on el segon encerta l'equip i la predicció dona l'altre, el segon perfecte"
SOSTRES = (EQUIP, CURTES, LLARGUES, A_PROP, LLUNY, SI_DUBTA, SI_SEGUR, DECODIFICADOR)
QUARTS_JUNTS = "els quatre ×¼"


def possessions(toc: np.ndarray, trams: list[ssp.Tram]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """A cada imatge d'una possessió de la veritat, on comença i on acaba ([inici, final); −1 fora de les
    possessions) i què hi ha abans."""
    n = len(toc)
    inici, final, abans = np.full(n, -1), np.full(n, -1), np.full(n, "", dtype=object)
    for tram in trams:
        for a, b, _ in pm.possession_spells(toc, [tram]):
            inici[a:b], final[a:b] = a, b
            abans[a:b] = (VORA if a == tram[0] else DESPRES_D if toc[a - 1] == pm.D
                          else DESPRES_ALTRE if toc[a - 1] in pm.POSSESSION_LABELS else VORA)
    return inici, final, abans


def llocs(pred: np.ndarray, toc: np.ndarray, trams: list[ssp.Tram]) -> np.ndarray:
    """A cada imatge d'una possessió de la veritat on la predicció no hi dona el seu equip, on cau dins la
    possessió."""
    out = np.full(len(toc), "", dtype=object)
    for tram in trams:
        for a, b, k in pm.possession_spells(toc, [tram]):
            dolentes = pred[a:b] != k
            if dolentes.all():
                out[a:b] = TOTA
                continue
            for s, e in ssp.trossos(dolentes):
                out[a + s:a + e] = AL_COMENCAMENT if s == 0 else AL_FINAL if e == b - a else AL_MIG
    return out


def segon(relativa: np.ndarray, toc: np.ndarray) -> np.ndarray:
    """A cada imatge on la veritat és d'un equip, què en diu el segon: l'encerta, hi dubta o està segur de l'altre
    (la probabilitat de l'equip bo davant de l'altre, amb la relativa, per sota de `DUBTE`)."""
    out = np.full(len(toc), "", dtype=object)
    i = np.flatnonzero(ssp.d_equip(relativa, toc, np.ones(len(toc), dtype=bool)))
    k = toc[i]
    d = relativa[i, k] - relativa[i, np.where(k == pm.H, pm.A, pm.H)]
    out[i] = np.where(ssp.l_equip(relativa[i]) == k, ENCERTA, np.where(1 / (1 + np.exp(-d)) >= DUBTE, DUBTA, SEGUR))
    return out


def a_quina(limits: tuple[float, ...], noms: tuple[str, ...], x: np.ndarray) -> np.ndarray:
    return np.asarray(noms, dtype=object)[np.searchsorted(limits, x, side="right") - 1]


def errors(pred: np.ndarray, toc: np.ndarray, relativa: np.ndarray, on: np.ndarray,
           trams: list[ssp.Tram]) -> pd.DataFrame:
    """Les imatges d'`on` on la veritat és d'un equip i la predicció no hi dona aquest equip, amb els seus trets."""
    inici, final, abans = possessions(toc, trams)
    i = np.flatnonzero(on & (inici >= 0) & (pred != toc))
    altre = np.where(toc[i] == pm.H, pm.A, pm.H)
    return pd.DataFrame({
        "dona": np.where(pred[i] == altre, L_ALTRE, np.where(pred[i] == pm.D, LA_D, RES)),
        "durada": a_quina(t3q.LIMITS, DURADES, final[i] - inici[i]),
        "abans": abans[i],
        "lloc": llocs(pred, toc, trams)[i],
        "distancia": a_quina(LIMITS_DISTANCIA, DISTANCIES, np.minimum(i - inici[i], final[i] - i)),
        "segon": segon(relativa, toc)[i],
    })


def mascares(toc: np.ndarray, relativa: np.ndarray, pilota: np.ndarray,
             trams: list[ssp.Tram]) -> dict[str, np.ndarray]:
    """On s'encerta l'equip a cada sostre (el segon només hi canvia on s'equivoca)."""
    inici, final, _ = possessions(toc, trams)
    i = np.arange(len(toc))
    dins = inici >= 0
    curta = dins & (final - inici < sc.CURTA)
    a_prop = dins & (np.minimum(i - inici, final - i) < TOL)
    diu = segon(relativa, toc)
    return {EQUIP: pilota, CURTES: pilota & curta, LLARGUES: pilota & dins & ~curta, A_PROP: pilota & a_prop,
            LLUNY: pilota & dins & ~a_prop, SI_DUBTA: pilota & (diu == DUBTA), SI_SEGUR: pilota & (diu == SEGUR)}


def tasca(nom_escenari: tuple[str, str]) -> dict[str, list[dict]]:
    nom, escenari = nom_escenari
    de_sempre = mp.degradat(nom, escenari)
    toc = vt.veritat(nom)
    p_toc = replace(de_sempre, veritat=toc)
    trams = avalua.trams_valids(p_toc)
    vista = ~np.isnan(de_sempre.tracking.pilota[:, 0])
    pilota = ssp.dins(len(toc), trams) & ~sc.forats(vista)
    probes, prior, q_ = msp.de_qui(A_SENSE, nom)
    relativa = log_relativa(probes[escenari].astype(float), prior)
    q = q_[escenari].astype(float)
    w, lam, d_min = mm.triades()[A_SENSE][nom]

    def decodifica(relativa_: np.ndarray) -> np.ndarray:
        return t3i.per_trams(relativa_, q, de_sempre.trams, w, lam, int(d_min))

    pred = decodifica(relativa)
    comu = {"partit": nom, "font": de_sempre.font, "escenari": escenari}

    def fila(sostre: str, prediccio: np.ndarray) -> dict:
        return {**comu, "base": A_SENSE, "sostre": sostre, "spell_f1": avalua.puntua(p_toc, prediccio)["spell_f1"]}

    altre = np.where(toc == pm.H, pm.A, pm.H)
    decodificador = pilota & (segon(relativa, toc) == ENCERTA) & (pred == altre)
    files = [fila(BASE, pred),
             *(fila(s, decodifica(ssp.equip_encertat(relativa, toc, m)))
               for s, m in mascares(toc, relativa, pilota, trams).items()),
             fila(DECODIFICADOR, decodifica(ssp.perfecte(relativa, toc, decodificador)))]
    e = errors(pred, toc, relativa, pilota, trams)
    comptes = e.groupby(list(TRETS)).size().rename("n").reset_index()
    inici, final, _ = possessions(toc, trams)
    m = pilota & (inici >= 0)
    imatges = pd.Series(a_quina(t3q.LIMITS, DURADES, (final - inici)[m])).value_counts()
    return {"files": files,
            "errors": [{**comu, **r} for r in comptes.to_dict("records")],
            "imatges": [{**comu, "durada": d, "n": int(n)} for d, n in imatges.items()]}


def de_xarxes() -> pd.Series:
    """L'spellF1 d'A xarxes a cada escenari i partit, amb el decodificador triat a la veritat de toc (del banc de la
    T3t)."""
    banc = pd.DataFrame(json.loads((msp.DIR_RESULTATS / "model-a-sense-pilota.json").read_text())["files"])
    triats = [banc[(banc["metode"] == msp.XARXES) & (banc["veritat"] == msp.TOC) & (banc["partit"] == nom)
                   & (banc["w"] == w) & (banc["lam"] == lam) & (banc["d_min"] == d_min)]
              for nom, (w, lam, d_min) in mm.triades()[mm.XARXES].items()]
    return pd.concat(triats).set_index(["escenari", "partit"])["spell_f1"]


def taula_errors(errors: pd.DataFrame, imatges: pd.DataFrame) -> pd.DataFrame:
    """Per escenari: les imatges d'un equip on es veu la pilota, i la part on la predicció hi dona l'altre o la D."""
    n = imatges.groupby("escenari")["n"].sum()
    dona = errors.groupby(["escenari", "dona"])["n"].sum().unstack("dona", fill_value=0)
    t = pd.DataFrame({"n imatges": n, "errors": dona.sum(axis=1) / n,
                      **{d: dona.get(d, pd.Series(0, index=n.index)) / n for d in DONA}})
    return t3q.ordena(t)


def parts(errors: pd.DataFrame, tret: str, ordre: tuple[str, ...]) -> pd.DataFrame:
    """Per escenari: de les imatges on la predicció dona l'altre equip, quina part és de cada valor del `tret`."""
    e = errors[errors["dona"] == L_ALTRE]
    t = e.groupby(["escenari", tret])["n"].sum().unstack(tret, fill_value=0).reindex(columns=list(ordre),
                                                                                       fill_value=0)
    return t3q.ordena(t.div(t.sum(axis=1), axis=0))


def taxa(errors: pd.DataFrame, imatges: pd.DataFrame) -> pd.DataFrame:
    """Per escenari i durada de la possessió: la part de les seves imatges on la predicció dona l'altre equip."""
    n = imatges.groupby(["escenari", "durada"])["n"].sum()
    e = errors[errors["dona"] == L_ALTRE].groupby(["escenari", "durada"])["n"].sum().reindex(n.index, fill_value=0)
    return t3q.ordena((e / n).unstack("durada")).reindex(columns=list(DURADES))


def creuada(errors: pd.DataFrame, escenaris: tuple[str, ...], files: tuple[str, tuple[str, ...]],
            columnes: tuple[str, tuple[str, ...]]) -> pd.DataFrame:
    """Als `escenaris`, junts: de les imatges on la predicció dona l'altre equip, quina part és de cada parell."""
    e = errors[(errors["dona"] == L_ALTRE) & errors["escenari"].isin(escenaris)]
    t = e.groupby([files[0], columnes[0]])["n"].sum().unstack(columnes[0], fill_value=0)
    t = t.reindex(index=list(files[1]), columns=list(columnes[1]), fill_value=0)
    return t / t.to_numpy().sum()


def taula_guanys(files: pd.DataFrame) -> list[str]:
    """Per sostre (files) i escenari (columnes): quant guanya a A sense pilota (mitjana dels partits)."""
    t = files.groupby(["escenari", "sostre"])["spell_f1"].mean().unstack("sostre")
    g = t[list(SOSTRES)].sub(t[BASE], axis=0)
    return ["| | " + " | ".join(ESCENARIS) + " |", "|---" * (1 + len(ESCENARIS)) + "|",
            f"| spellF1 d'{A_SENSE} | " + " | ".join(f"{t.loc[e, BASE]:.3f}" for e in ESCENARIS) + " |",
            *(f"| {s} | " + " | ".join(f"{g.loc[e, s]:+.3f}" for e in ESCENARIS) + " |" for s in SOSTRES)]


def taula_criteri(files: pd.DataFrame, xarxes: pd.Series) -> list[str]:
    """Per sostre i escenari ×¼: A sense pilota amb la peça encertada contra A xarxes, i si passaria el criteri."""
    font = files.groupby("partit")["font"].first()
    linies = [f"| {A_SENSE} amb… | " + " | ".join(QUARTS) + " |", "|---" * (1 + len(QUARTS)) + "|"]
    for sostre in (BASE, *SOSTRES):
        de_sense = files[files["sostre"] == sostre].set_index(["escenari", "partit"])["spell_f1"]
        celles = []
        for escenari in QUARTS:
            dif = (de_sense - xarxes).loc[escenari]
            c = sc.criteri(dif.to_numpy(), font.loc[dif.index].to_numpy())
            celles.append(f"{c['guany']:+.3f} · {c['guanya']}/{c['partits']} {'✓' if c['passa'] else '✗'}")
        linies.append(f"| {'res més' if sostre == BASE else sostre} | " + " | ".join(celles) + " |")
    return linies


def amb_nom(t: pd.DataFrame, nom: str) -> pd.DataFrame:
    return t.rename_axis(index=nom)


def main() -> None:
    from banc import errors_amb_pilota as aquest        # pel nom del mòdul, perquè els processos fills el trobin

    with ProcessPoolExecutor(max_workers=10) as feina:
        tasques = list(feina.map(aquest.tasca, itertools.product(fonts.NOMS, ESCENARIS)))
    files, errs, imatges = (pd.DataFrame([f for t in tasques for f in t[k]]) for k in ("files", "errors", "imatges"))
    mm.comprova(files, bases=(A_SENSE,))
    xarxes = de_xarxes()
    sortida = [
        "# Banc obert · Com són els errors d'equip on es veu la pilota", "",
        "Generat amb `uv run python -I -m banc.errors_amb_pilota`, amb el que ha desat `banc.model_a_sense_pilota`.",
        f"Dades obertes. Només per saber-ho. {A_SENSE}, a la veritat de toc, amb el decodificador triat a cada partit",
        "a la veritat de toc (✓ comprovat: el mateix spellF1 que el banc de la T3t). On es veu la pilota: fora dels",
        f"forats (els trossos sense pilota, amb {t3i.K} imatges més a cada banda).", "",
        "## Els errors", "",
        "On es veu la pilota i la veritat és d'un equip: quantes imatges hi ha, i la part on la predicció hi dona",
        "l'altre equip o la D. La resta de l'informe és dels errors a l'altre equip.", "",
        t3p.md(taula_errors(errs, imatges)), "",
        "## De quines possessions són", "",
        "Quina part dels errors és a les possessions de la veritat de cada durada:", "",
        t3p.md(parts(errs, "durada", DURADES)), "",
        "I a cada durada, la part de les seves imatges on la predicció dona l'altre equip:", "",
        t3p.md(taxa(errs, imatges)), "",
        "Què hi ha abans de la possessió de la veritat:", "",
        t3p.md(parts(errs, "abans", ABANS)), "",
        "## On cauen dins la possessió", "",
        "*Tota la possessió:* la predicció no hi dona mai el seu equip. *Al començament:* la predicció hi arriba tard",
        "(encara hi dona l'equip d'abans). *Al final:* se'n va d'hora. *Al mig:* hi dona l'altre equip i hi torna.", "",
        t3p.md(parts(errs, "lloc", LLOCS)), "",
        "## A quina distància del toc", "",
        "Del començament o del final de la possessió de la veritat (el toc de l'equip nou o de l'altre, o l'aturada),",
        "el que sigui més a prop:", "",
        t3p.md(parts(errs, "distancia", DISTANCIES)), "",
        "## Què en diu el segon", "",
        "Si el segon hi encerta l'equip, el que s'equivoca és el decodificador. Si no, si dubta o si n'està segur: la",
        f"probabilitat que dona a l'equip bo davant de l'altre (amb la relativa), {DUBTE} o més, o menys.", "",
        t3p.md(parts(errs, "segon", SEGONS)), "",
        f"Als {QUARTS_JUNTS} junts, per durada i pel que en diu el segon (la part de tots els errors a l'altre equip):",
        "",
        t3p.md(amb_nom(creuada(errs, QUARTS, ("durada", DURADES), ("segon", SEGONS)), "durada")), "",
        "I per on cauen i pel que en diu el segon:", "",
        t3p.md(amb_nom(creuada(errs, QUARTS, ("lloc", LLOCS), ("segon", SEGONS)), "lloc")), "",
        "A «partit ×¼», igual:", "",
        t3p.md(amb_nom(creuada(errs, ("partit ×¼",), ("durada", DURADES), ("segon", SEGONS)), "durada")), "",
        t3p.md(amb_nom(creuada(errs, ("partit ×¼",), ("lloc", LLOCS), ("segon", SEGONS)), "lloc")), "",
        "## Els sostres", "",
        f"Quant guanya a {A_SENSE} (mitjana dels deu partits) el segon amb l'equip encertat on es veu la pilota",
        "(l'H i l'A girats on s'equivoca, amb la confiança que tenia), a tot arreu o només en una part. I on el segon",
        "ja encerta l'equip i la predicció dona l'altre, el segon perfecte.", "",
        *taula_guanys(files), "",
        f"Contra {mm.XARXES}: el guany de mitjana · en quants partits guanya · ✓ si passaria (> {t3.SOROLL},",
        f"l'interval del 95 % per sobre de zero i {t3.GUANYA_MINIM} partits de 10 o més).", "",
        *taula_criteri(files, xarxes), "",
    ]
    an.DIR_RESULTATS.mkdir(exist_ok=True)
    (an.DIR_RESULTATS / "errors-amb-pilota.md").write_text("\n".join(sortida))
    print("\n".join(sortida))


if __name__ == "__main__":
    main()
