# Banc obert · el detector de tocs

Generat amb `uv run python -I -m banc.tocs` (T2 del pla per tocs, `docs/pla-tocs.md`). Dades obertes:
7 partits de DFL (IDSSE, CC BY 4.0) i els 3 de mostra de Metrica. Cap dada del concurs. Què es mesura i
com: la capçalera de `banc/tocs.py`. **De l'altre sense acció**: els tocs que el detector dona a l'equip
que no té la pilota, lluny de cap canvi i sense cap acció d'aquest equip a prop, per minut de joc.

## El soroll de la pilota lliure

La mediana del canvi de velocitat (k = 5) on la pilota és a 5 m o més de tothom, en
m/s: el que el detector veu com un toc quan no n'hi ha cap.

| escenari | DFL | Metrica |
|---|---|---|
| net | 0.0 | 0.0 |
| curts | 6.6 | 6.5 |
| llargs | 6.6 | 6.7 |
| barreja | 6.6 | 6.5 |
| aire | 7.7 | 6.5 |
| soroll2 | 13.3 | 13.4 |
| barreja, soroll ×0 | 0.0 | 0.0 |
| barreja, soroll ×0.25 | 1.7 | 1.7 |
| barreja, soroll ×0.5 | 3.3 | 3.3 |
| barreja, soroll ×1 | 6.6 | 6.5 |
| barreja, soroll ×2 | 13.2 | 13.5 |

## Els paràmetres

Les mitjanes dels cinc escenaris degradats (cada escenari, els deu partits junts), de millor a pitjor
benefici; **pitjor** és el benefici de l'escenari on en té menys. Els deu primers:

| k | canvi (m/s) | abast (m) | canvis amb pilota | de l'altre sense acció (/min) | benefici | pitjor |
|---|---|---|---|---|---|---|
| 12 | 16 | 1.5 | 10% | 0.3 | +0.01 | -0.10 |
| 12 | 16 | 1 | 5% | 0.1 | +0.01 | -0.05 |
| 12 | 12 | 1 | 7% | 0.2 | -0.00 | -0.08 |
| 8 | 16 | 1 | 7% | 0.2 | -0.00 | -0.12 |
| 12 | 16 | 2.5 | 16% | 0.5 | -0.01 | -0.24 |
| 12 | 12 | 1.5 | 14% | 0.4 | -0.01 | -0.17 |
| 8 | 16 | 1.5 | 13% | 0.4 | -0.01 | -0.25 |
| 8 | 12 | 1 | 9% | 0.4 | -0.03 | -0.16 |
| 12 | 8 | 1 | 10% | 0.4 | -0.03 | -0.11 |
| 5 | 16 | 1 | 10% | 0.4 | -0.05 | -0.23 |

Al tracking net, els cinc primers:

| k | canvi (m/s) | abast (m) | canvis amb pilota | de l'altre sense acció (/min) | benefici | pitjor |
|---|---|---|---|---|---|---|
| 5 | 5 | 2.5 | 68% | 0.4 | +0.61 | +0.61 |
| 3 | 5 | 2.5 | 68% | 0.4 | +0.61 | +0.61 |
| 3 | 5 | 1.5 | 67% | 0.3 | +0.61 | +0.61 |
| 5 | 5 | 1.5 | 66% | 0.3 | +0.60 | +0.60 |
| 8 | 5 | 2.5 | 66% | 0.3 | +0.60 | +0.60 |

## Els triats (k = 12, 16 m/s, 1.5 m), escenari per escenari

| escenari | font | canvis | canvis amb pilota | accions | tocs (/min) | de l'altre (/min) | de l'altre sense acció (/min) | benefici |
|---|---|---|---|---|---|---|---|---|
| net | dfl | 24% | 24% | 23% | 7.7 | 0.1 | 0.1 | +0.23 |
| curts | dfl | 4% | 8% | 6% | 2.2 | 0.2 | 0.1 | +0.04 |
| llargs | dfl | 7% | 14% | 8% | 2.9 | 0.2 | 0.2 | +0.09 |
| barreja | dfl | 6% | 11% | 8% | 2.7 | 0.2 | 0.2 | +0.05 |
| aire | dfl | 4% | 8% | 7% | 2.4 | 0.3 | 0.2 | +0.01 |
| soroll2 | dfl | 3% | 6% | 5% | 2.0 | 0.5 | 0.5 | -0.08 |
| net | metrica | 22% | 22% | 18% | 6.5 | 0.1 | 0.0 | +0.21 |
| curts | metrica | 3% | 6% | 4% | 1.7 | 0.2 | 0.2 | -0.02 |
| llargs | metrica | 7% | 13% | 6% | 2.5 | 0.2 | 0.2 | +0.03 |
| barreja | metrica | 7% | 15% | 6% | 2.2 | 0.2 | 0.2 | +0.05 |
| aire | metrica | 6% | 10% | 6% | 2.3 | 0.2 | 0.2 | -0.00 |
| soroll2 | metrica | 4% | 7% | 3% | 1.9 | 0.5 | 0.5 | -0.16 |

## Quant soroll aguanta

La barreja amb l'error de posició (de la pilota i dels jugadors) multiplicat per un factor, i el millor
joc de paràmetres de cada factor:

| factor | soroll DFL (m/s) | soroll Metrica (m/s) | k | canvi (m/s) | abast (m) | canvis amb pilota | de l'altre sense acció (/min) | benefici |
|---|---|---|---|---|---|---|---|---|
| ×0 | 0.0 | 0.0 | 3 | 5 | 1.5 | 61% | 0.3 | +0.51 |
| ×0.25 | 1.7 | 1.7 | 5 | 5 | 1.5 | 59% | 0.4 | +0.47 |
| ×0.5 | 3.3 | 3.3 | 8 | 8 | 2.5 | 49% | 0.5 | +0.32 |
| ×1 | 6.6 | 6.5 | 12 | 12 | 2.5 | 29% | 0.6 | +0.09 |
| ×2 | 13.2 | 13.5 | 12 | 16 | 1 | 4% | 0.2 | -0.03 |
