# Banc obert · Una xarxa que mira les posicions al voltant de la pilota (T3m)

Generat amb `uv run python -I -m banc.model_a_xarxa`. Dades obertes: 7 partits de DFL (IDSSE, CC BY 4.0)
i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el criteri:
`docs/pla-tocs.md`, «T3m», i la capçalera de `banc/model_a_xarxa.py`.

**A context** és el model de la cadena (T3e), amb el decodificador d'ara. **A aturades** és el de la
T3k. **A xarxa** és A aturades amb les probabilitats de la xarxa (`cadena/xarxa.py`) al segon
classificador. Tots tenen els paràmetres del decodificador triats amb els altres nou partits als
escenaris ×¼.

## L'spellF1 i el macroF1 de cada mètode (mitjana dels deu partits)

**spellF1**

| escenari | A context | A aturades | A xarxa |
|---|---|---|---|
| net | 0.775 | 0.801 | 0.803 |
| curts ×¼ | 0.639 | 0.659 | 0.683 |
| llargs ×¼ | 0.621 | 0.648 | 0.659 |
| barreja ×¼ | 0.631 | 0.661 | 0.667 |
| aire ×¼ | 0.556 | 0.585 | 0.600 |
| curts | 0.583 | 0.601 | 0.642 |
| llargs | 0.547 | 0.568 | 0.607 |
| barreja | 0.562 | 0.579 | 0.611 |
| aire | 0.508 | 0.526 | 0.563 |
| soroll2 | 0.373 | 0.388 | 0.473 |

**macroF1**

| escenari | A context | A aturades | A xarxa |
|---|---|---|---|
| net | 0.952 | 0.953 | 0.953 |
| curts ×¼ | 0.919 | 0.921 | 0.925 |
| llargs ×¼ | 0.906 | 0.906 | 0.909 |
| barreja ×¼ | 0.910 | 0.912 | 0.914 |
| aire ×¼ | 0.886 | 0.890 | 0.893 |
| curts | 0.902 | 0.901 | 0.911 |
| llargs | 0.885 | 0.882 | 0.894 |
| barreja | 0.886 | 0.888 | 0.897 |
| aire | 0.865 | 0.868 | 0.876 |
| soroll2 | 0.697 | 0.694 | 0.774 |

## A xarxa contra A context (spellF1): el criteri

| escenari | A context | A xarxa | diferència | interval del 95 % | A xarxa guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.775 | 0.803 | +0.028 | +0.012 a +0.042 | 8 de 10 | no perd | ✓ |
| curts ×¼ | 0.639 | 0.683 | +0.043 | +0.028 a +0.056 | 10 de 10 | guanya clarament | ✓ |
| llargs ×¼ | 0.621 | 0.659 | +0.037 | +0.024 a +0.052 | 10 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.631 | 0.667 | +0.036 | +0.021 a +0.050 | 9 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.556 | 0.600 | +0.044 | +0.027 a +0.061 | 9 de 10 | guanya clarament | ✓ |
| curts | 0.583 | 0.642 | +0.059 | +0.047 a +0.069 | 10 de 10 | no perd | ✓ |
| llargs | 0.547 | 0.607 | +0.059 | +0.045 a +0.075 | 10 de 10 | no perd | ✓ |
| barreja | 0.562 | 0.611 | +0.050 | +0.032 a +0.068 | 10 de 10 | no perd | ✓ |
| aire | 0.508 | 0.563 | +0.055 | +0.045 a +0.063 | 10 de 10 | no perd | ✓ |
| soroll2 | 0.373 | 0.473 | +0.100 | +0.089 a +0.110 | 10 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre escenaris ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1 i el soroll2 | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## A xarxa contra A aturades (spellF1), només per saber-ho

El mateix sense la xarxa: la diferència és el que hi afegeix.

| escenari | A aturades | A xarxa | diferència | interval del 95 % | A xarxa guanya |
|---|---|---|---|---|---|
| net | 0.801 | 0.803 | +0.001 | -0.008 a +0.009 | 4 de 10 |
| curts ×¼ | 0.659 | 0.683 | +0.024 | +0.020 a +0.028 | 10 de 10 |
| llargs ×¼ | 0.648 | 0.659 | +0.011 | +0.003 a +0.020 | 8 de 10 |
| barreja ×¼ | 0.661 | 0.667 | +0.007 | -0.001 a +0.015 | 7 de 10 |
| aire ×¼ | 0.585 | 0.600 | +0.015 | +0.007 a +0.023 | 9 de 10 |
| curts | 0.601 | 0.642 | +0.041 | +0.033 a +0.049 | 10 de 10 |
| llargs | 0.568 | 0.607 | +0.039 | +0.031 a +0.049 | 10 de 10 |
| barreja | 0.579 | 0.611 | +0.032 | +0.023 a +0.042 | 10 de 10 |
| aire | 0.526 | 0.563 | +0.037 | +0.028 a +0.046 | 10 de 10 |
| soroll2 | 0.388 | 0.473 | +0.085 | +0.071 a +0.098 | 10 de 10 |

## Per font (spellF1, mitjana dels partits de cada font), només per saber-ho

| escenari | font | A context | A aturades | A xarxa |
|---|---|---|---|---|
| net | dfl | 0.754 | 0.778 | 0.774 |
| net | metrica | 0.825 | 0.857 | 0.870 |
| curts ×¼ | dfl | 0.611 | 0.632 | 0.655 |
| curts ×¼ | metrica | 0.705 | 0.721 | 0.747 |
| llargs ×¼ | dfl | 0.594 | 0.617 | 0.627 |
| llargs ×¼ | metrica | 0.686 | 0.719 | 0.731 |
| barreja ×¼ | dfl | 0.604 | 0.636 | 0.639 |
| barreja ×¼ | metrica | 0.692 | 0.718 | 0.732 |
| aire ×¼ | dfl | 0.499 | 0.528 | 0.544 |
| aire ×¼ | metrica | 0.690 | 0.719 | 0.732 |
| curts | dfl | 0.560 | 0.574 | 0.611 |
| curts | metrica | 0.636 | 0.664 | 0.712 |
| llargs | dfl | 0.518 | 0.532 | 0.572 |
| llargs | metrica | 0.615 | 0.650 | 0.689 |
| barreja | dfl | 0.533 | 0.551 | 0.581 |
| barreja | metrica | 0.628 | 0.645 | 0.681 |
| aire | dfl | 0.454 | 0.473 | 0.511 |
| aire | metrica | 0.636 | 0.649 | 0.685 |
| soroll2 | dfl | 0.321 | 0.343 | 0.428 |
| soroll2 | metrica | 0.493 | 0.492 | 0.576 |

## L'encert de l'equip abans de decodificar (escenaris ×¼), només per saber-ho

A les imatges de les possessions de la veritat, la part on l'equip més probable és el de la veritat,
per durada de la possessió i segons si la pilota es veu. *El primer* és el primer classificador
d'A contacte sol, i *la xarxa sola*, la xarxa sola.

| durada | pilota | el primer | la xarxa sola | A aturades | A xarxa |
|---|---|---|---|---|---|
| <1 s | no | 0.285 | 0.158 | 0.381 | 0.369 |
| <1 s | sí | 0.595 | 0.450 | 0.659 | 0.665 |
| 1-2 s | no | 0.436 | 0.223 | 0.511 | 0.504 |
| 1-2 s | sí | 0.666 | 0.607 | 0.716 | 0.735 |
| 2-5 s | no | 0.569 | 0.307 | 0.609 | 0.607 |
| 2-5 s | sí | 0.754 | 0.724 | 0.779 | 0.805 |
| ≥5 s | no | 0.858 | 0.427 | 0.863 | 0.862 |
| ≥5 s | sí | 0.947 | 0.903 | 0.947 | 0.950 |

## Possessions predites per cada real (mitjana dels deu partits), només per saber-ho

| escenari | A context | A aturades | A xarxa |
|---|---|---|---|
| net | 0.83 | 0.92 | 0.93 |
| curts ×¼ | 0.74 | 0.83 | 0.84 |
| llargs ×¼ | 0.73 | 0.81 | 0.82 |
| barreja ×¼ | 0.72 | 0.81 | 0.82 |
| aire ×¼ | 0.72 | 0.79 | 0.80 |
| curts | 0.72 | 0.82 | 0.83 |
| llargs | 0.68 | 0.77 | 0.79 |
| barreja | 0.70 | 0.79 | 0.80 |
| aire | 0.69 | 0.75 | 0.77 |
| soroll2 | 1.03 | 1.07 | 0.98 |

## Els paràmetres triats (cada partit, amb els altres nou)

- A context: λ = 4, durada mínima 12 · A aturades: w = 4, λ = 32, durada mínima 12 · A xarxa: w = 4, λ = 32, durada mínima 12 (7 partits)
- A context: λ = 2, durada mínima 25 · A aturades: w = 4, λ = 32, durada mínima 12 · A xarxa: w = 4, λ = 32, durada mínima 12 (1 partits)
- A context: λ = 4, durada mínima 12 · A aturades: w = 4, λ = 16, durada mínima 12 · A xarxa: w = 4, λ = 32, durada mínima 12 (1 partits)
- A context: λ = 4, durada mínima 12 · A aturades: w = 4, λ = 32, durada mínima 12 · A xarxa: w = 4, λ = 16, durada mínima 12 (1 partits)
