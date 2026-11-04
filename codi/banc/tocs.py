"""El detector de tocs al banc obert (T2 del pla per tocs, `docs/pla-tocs.md`).

    cd codi && uv run python -I -m banc.tocs [--processos 8]

Per a cada partit, escenari i joc de paràmetres de `GRAELLA`, el detector (`cadena.tocs`) sobre el tracking
degradat, i tres mesures contra el net:
- **els canvis:** de cada canvi d'equip de la veritat en joc, si troba un toc de l'equip nou a ±0,4 s. A DFL, la
  veritat canvia en el moment del toc (T1). També quants en troba dels que tenen la pilota a la imatge del canvi;
- **les accions:** dels tocs dels esdeveniments (`tocs_reals`), quants en troba de l'equip que toca, amb el marge de
  cada font;
- **els tocs de l'equip sense pilota:** els que dona a l'equip que, segons la veritat, no la té, lluny (més d'1 s)
  de cap canvi cap a aquest equip. N'hi ha de reals (una desviació, un rebuig) i d'inventats; els que no tenen cap
  acció d'aquell equip a prop són els més sospitosos. Per minut de pilota viva.

**El benefici** d'un joc de paràmetres: (canvis trobats − tocs de l'equip sense pilota sense cap acció a prop) /
canvis, tots dos amb la pilota a la imatge del canvi. Un toc inventat de l'equip que no té la pilota costa com un
canvi perdut. Es tria el que en té més de mitjana als escenaris degradats.

**El soroll de la pilota lliure:** la mediana del canvi de velocitat (k = 5) a les imatges on la pilota és a 5 m o
més de tothom, on no hi pot haver cap toc. Diu com de brusc és l'error de la pilota de cada escenari. Per veure quant
en aguanta el detector, la barreja es repeteix amb l'error de posició multiplicat per 0, ¼, ½, 1 i 2 (els mateixos
forats).

Escriu `resultats/tocs.json` (la clau del codi i totes les files) i `resultats/tocs.md`. Tot són dades obertes.
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace

import numpy as np
import pandas as pd

from banc import canvis, degrada, fonts, tocs_reals
from banc.partit import PartitBanc
from banc.tocs_desats import DIR_RESULTATS, FACTORS_SOROLL, clau, nom_soroll
from cadena import tocs
from possessio.oficial import possession_metrics as pm

FPS = 25
MARGE_CANVI = 10          # ±0,4 s: el toc de l'equip nou al voltant d'un canvi de la veritat
LLUNY_CANVI = 25          # a menys d'1 s d'un canvi cap a l'equip del toc, no és un toc de l'equip sense pilota
GRAELLA = tuple(tocs.Parametres(k, canvi, abast)
                for k in (3, 5, 8, 12) for canvi in (5.0, 8.0, 12.0, 16.0) for abast in (1.0, 1.5, 2.5))
DEGRADATS = tuple(e for e in degrada.NOMS if e != "net")
K_SOROLL, LLUNY_M = 5, 5.0
COMPTES = ("minuts", "canvis", "canvis_trobats", "canvis_amb_pilota", "trobats_amb_pilota", "accions",
           "accions_trobades", "tocs", "de_l_altre", "de_l_altre_sense_accio")


def a_prop(imatges: np.ndarray, referencia: np.ndarray, marge: int) -> np.ndarray:
    """Per a cada imatge, si n'hi ha alguna de `referencia` (en ordre) a ±marge."""
    if len(referencia) == 0 or len(imatges) == 0:
        return np.zeros(len(imatges), bool)
    j = np.searchsorted(referencia, imatges)
    abans = referencia[np.clip(j - 1, 0, len(referencia) - 1)]
    despres = referencia[np.clip(j, 0, len(referencia) - 1)]
    return (np.abs(imatges - abans) <= marge) | (np.abs(despres - imatges) <= marge)


def del_mateix_equip(imatges: np.ndarray, equips: np.ndarray, consulta: np.ndarray, equips_consulta: np.ndarray,
                     marge: int) -> np.ndarray:
    """Per a cada imatge de `consulta`, si n'hi ha alguna de les seves, del mateix equip, a ±marge."""
    trobat = np.zeros(len(consulta), bool)
    for equip in (pm.H, pm.A):
        de_l_equip = equips_consulta == equip
        trobat[de_l_equip] = a_prop(consulta[de_l_equip], np.sort(imatges[equips == equip]), marge)
    return trobat


def mesura(net: PartitBanc, degradat: PartitBanc, reals: tocs_reals.Reals, trobats: tocs.Tocs) -> dict[str, float]:
    """Els comptes d'un partit i un escenari: es poden sumar entre partits abans de fer-ne les proporcions."""
    v = net.veritat
    viva = np.isin(v, (pm.H, pm.A))
    c = canvis.canvis_de_la_veritat(v, net.trams)
    nou = v[c]
    trobat = del_mateix_equip(trobats.imatge, trobats.equip, c, nou, MARGE_CANVI)
    amb_pilota = ~np.isnan(degradat.tracking.pilota[c, 0])
    marge = tocs_reals.MARGE[net.font]
    en_joc = viva[reals.imatge]
    accions = del_mateix_equip(trobats.imatge, trobats.equip, reals.imatge[en_joc], reals.equip[en_joc], marge)
    viu = viva[trobats.imatge]
    i, e = trobats.imatge[viu], trobats.equip[viu]
    de_l_altre = (e != v[i]) & ~del_mateix_equip(c, nou, i, e, LLUNY_CANVI)
    amb_accio = del_mateix_equip(reals.imatge, reals.equip, i, e, marge)
    return {"minuts": viva.sum() / FPS / 60, "canvis": len(c), "canvis_trobats": int(trobat.sum()),
            "canvis_amb_pilota": int(amb_pilota.sum()), "trobats_amb_pilota": int((trobat & amb_pilota).sum()),
            "accions": int(en_joc.sum()), "accions_trobades": int(accions.sum()), "tocs": len(i),
            "de_l_altre": int(de_l_altre.sum()), "de_l_altre_sense_accio": int((de_l_altre & ~amb_accio).sum())}


def amb_soroll(factor: float) -> degrada.Escenari:
    """La barreja (els mateixos forats, que depenen del nom) amb l'error de posició multiplicat per `factor`."""
    b = degrada.ESCENARIS["barreja"]
    return replace(b, sigma_jugadors_m=b.sigma_jugadors_m * factor, sigma_pilota_m=b.sigma_pilota_m * factor,
                   tremolor_jugadors_m=b.tremolor_jugadors_m * factor, tremolor_pilota_m=b.tremolor_pilota_m * factor)


ESCENARIS = {**{e: e for e in degrada.NOMS}, **{nom_soroll(f): amb_soroll(f) for f in FACTORS_SOROLL}}


def soroll_lliure(p: PartitBanc) -> float:
    """La mediana del canvi de velocitat de la pilota (k = K_SOROLL) on és a LLUNY_M o més de tothom. És la mateixa
    mesura que fa `pilota.valida` amb l'ATD del partit, per triar l'escenari que s'hi assembla."""
    return tocs.soroll_lliure(p.tracking, p.trams, K_SOROLL, LLUNY_M)


def files_de(tasca: tuple[str, str]) -> list[dict]:
    """Un partit i un escenari, amb tota la graella (a part, perquè la cridi un procés fill)."""
    nom, escenari = tasca
    net = fonts.partit(nom)
    degradat = degrada.aplica(net, ESCENARIS[escenari])
    reals = tocs_reals.reals(nom, net)
    comu = {"partit": nom, "font": net.font, "escenari": escenari, "soroll_ms": soroll_lliure(degradat)}
    return [{**comu, **asdict(par), **mesura(net, degradat, reals, tocs.detecta(degradat.tracking, net.trams, par))}
            for par in GRAELLA]


def proporcions(files: pd.DataFrame, per: list[str]) -> pd.DataFrame:
    """Les proporcions i els ritmes, amb els comptes sumats per grup."""
    s = files.groupby(per, sort=False)[list(COMPTES)].sum()
    return pd.DataFrame({
        "canvis": s["canvis_trobats"] / s["canvis"],
        "canvis_amb_pilota": s["trobats_amb_pilota"] / s["canvis_amb_pilota"],
        "accions": s["accions_trobades"] / s["accions"],
        "tocs_min": s["tocs"] / s["minuts"],
        "altre_min": s["de_l_altre"] / s["minuts"],
        "altre_sense_accio_min": s["de_l_altre_sense_accio"] / s["minuts"],
        "benefici": (s["trobats_amb_pilota"] - s["de_l_altre_sense_accio"]) / s["canvis_amb_pilota"],
    }).reset_index()


PARAMETRES = ["k", "canvi_ms", "abast_m"]


def per_parametres(files: pd.DataFrame, escenaris: tuple[str, ...]) -> pd.DataFrame:
    """Per joc de paràmetres: la mitjana de les proporcions dels escenaris (cada escenari, els deu partits junts) i
    el benefici del pitjor escenari, de millor a pitjor benefici."""
    t = proporcions(files[files["escenari"].isin(escenaris)], ["escenari", *PARAMETRES])
    mitjana = t.groupby(PARAMETRES)[["canvis_amb_pilota", "altre_sense_accio_min", "benefici"]].mean()
    mitjana["pitjor"] = t.groupby(PARAMETRES)["benefici"].min()
    return mitjana.sort_values("benefici", ascending=False).reset_index()


def triats(files: pd.DataFrame) -> tocs.Parametres:
    """Els del millor benefici de mitjana als escenaris degradats."""
    millor = per_parametres(files, DEGRADATS).iloc[0]
    return tocs.Parametres(int(millor["k"]), float(millor["canvi_ms"]), float(millor["abast_m"]))


def corba_del_soroll(files: pd.DataFrame) -> pd.DataFrame:
    """Per a cada factor del soroll: el soroll de la pilota lliure i el millor joc de paràmetres d'aquell factor."""
    files_corba = []
    for factor in FACTORS_SOROLL:
        nom = nom_soroll(factor)
        millor = per_parametres(files, (nom,)).iloc[0]
        soroll = files[files["escenari"] == nom].groupby("font")["soroll_ms"].median()
        files_corba.append({"factor": factor, "soroll_dfl": soroll.get("dfl"), "soroll_metrica": soroll.get("metrica"),
                            **{c: millor[c] for c in [*PARAMETRES, "canvis_amb_pilota", "altre_sense_accio_min",
                                                      "benefici"]}})
    return pd.DataFrame(files_corba)


def markdown(files: pd.DataFrame) -> str:
    def pct(v: float) -> str:
        return f"{v:.0%}"

    def num(v: float) -> str:
        return "—" if pd.isna(v) else f"{v:.1f}"

    def taula_parametres(t: pd.DataFrame) -> list[str]:
        return ["| k | canvi (m/s) | abast (m) | canvis amb pilota | de l'altre sense acció (/min) | benefici | pitjor |",
                "|---|---|---|---|---|---|---|",
                *(f"| {f.k:.0f} | {f.canvi_ms:g} | {f.abast_m:g} | {pct(f.canvis_amb_pilota)} | "
                  f"{num(f.altre_sense_accio_min)} | {f.benefici:+.2f} | {f.pitjor:+.2f} |" for f in t.itertuples())]

    par = triats(files)
    soroll = (files.drop_duplicates(["partit", "escenari"]).groupby(["escenari", "font"], sort=False)["soroll_ms"]
              .median().unstack())
    linies = ["# Banc obert · el detector de tocs", "",
              "Generat amb `uv run python -I -m banc.tocs` (T2 del pla per tocs, `docs/pla-tocs.md`). Dades obertes:",
              "7 partits de DFL (IDSSE, CC BY 4.0) i els 3 de mostra de Metrica. Cap dada del concurs. Què es mesura i",
              "com: la capçalera de `banc/tocs.py`. **De l'altre sense acció**: els tocs que el detector dona a l'equip",
              "que no té la pilota, lluny de cap canvi i sense cap acció d'aquest equip a prop, per minut de joc.", "",
              "## El soroll de la pilota lliure", "",
              f"La mediana del canvi de velocitat (k = {K_SOROLL}) on la pilota és a {LLUNY_M:g} m o més de tothom, en",
              "m/s: el que el detector veu com un toc quan no n'hi ha cap.", "",
              "| escenari | DFL | Metrica |", "|---|---|---|",
              *(f"| {e} | {num(f.get('dfl'))} | {num(f.get('metrica'))} |" for e, f in soroll.iterrows()), "",
              "## Els paràmetres", "",
              "Les mitjanes dels cinc escenaris degradats (cada escenari, els deu partits junts), de millor a pitjor",
              "benefici; **pitjor** és el benefici de l'escenari on en té menys. Els deu primers:", "",
              *taula_parametres(per_parametres(files, DEGRADATS).head(10)), "",
              "Al tracking net, els cinc primers:", "",
              *taula_parametres(per_parametres(files, ("net",)).head(5)), "",
              f"## Els triats (k = {par.k}, {par.canvi_ms:g} m/s, {par.abast_m:g} m), escenari per escenari", "",
              "| escenari | font | canvis | canvis amb pilota | accions | tocs (/min) | de l'altre (/min) "
              "| de l'altre sense acció (/min) | benefici |",
              "|---|---|---|---|---|---|---|---|---|"]
    d = files[(files["k"] == par.k) & (files["canvi_ms"] == par.canvi_ms) & (files["abast_m"] == par.abast_m)
              & files["escenari"].isin(degrada.NOMS)]
    linies += [f"| {f.escenari} | {f.font} | {pct(f.canvis)} | {pct(f.canvis_amb_pilota)} | {pct(f.accions)} | "
               f"{num(f.tocs_min)} | {num(f.altre_min)} | {num(f.altre_sense_accio_min)} | {f.benefici:+.2f} |"
               for f in proporcions(d, ["escenari", "font"]).itertuples()]
    linies += ["", "## Quant soroll aguanta", "",
               "La barreja amb l'error de posició (de la pilota i dels jugadors) multiplicat per un factor, i el millor",
               "joc de paràmetres de cada factor:", "",
               "| factor | soroll DFL (m/s) | soroll Metrica (m/s) | k | canvi (m/s) | abast (m) | canvis amb pilota "
               "| de l'altre sense acció (/min) | benefici |",
               "|---|---|---|---|---|---|---|---|---|"]
    linies += [f"| ×{f.factor:g} | {num(f.soroll_dfl)} | {num(f.soroll_metrica)} | {f.k:.0f} | {f.canvi_ms:g} | "
               f"{f.abast_m:g} | {pct(f.canvis_amb_pilota)} | {num(f.altre_sense_accio_min)} | {f.benefici:+.2f} |"
               for f in corba_del_soroll(files).itertuples()]
    return "\n".join([*linies, ""])


def main() -> None:
    from banc import tocs as aquest      # pel nom del mòdul, perquè els processos fills trobin les funcions

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processos", type=int, default=8)
    args = ap.parse_args()
    for nom in fonts.NOMS:
        tocs_reals.reals(nom)                                      # la memòria cau, abans de repartir la feina
    tasques = [(nom, escenari) for nom in fonts.NOMS for escenari in ESCENARIS]
    with ProcessPoolExecutor(max_workers=args.processos) as feina:
        files = pd.DataFrame([f for tros in feina.map(aquest.files_de, tasques) for f in tros])
    DIR_RESULTATS.mkdir(exist_ok=True)
    (DIR_RESULTATS / "tocs.json").write_text(json.dumps({"clau": clau(), "files": files.to_dict("records")},
                                                        indent=1, default=float))
    (DIR_RESULTATS / "tocs.md").write_text(markdown(files))
    print((DIR_RESULTATS / "tocs.md").read_text())


if __name__ == "__main__":
    main()
