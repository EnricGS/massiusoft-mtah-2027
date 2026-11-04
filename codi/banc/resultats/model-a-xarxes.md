# Banc obert · La mitjana de cinc xarxes (T3o)

Generat amb `uv run python -I -m banc.model_a_xarxes`. Dades obertes: 7 partits de DFL (IDSSE, CC BY
4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3o», i la capçalera de `banc/model_a_xarxes.py`.

**A context** és el model de la cadena (T3e), amb el decodificador d'ara. **A xarxa** és el de
la T3m, amb una xarxa. **A xarxes** és A xarxa amb la mitjana de cinc xarxes entrenades igual, cadascuna
amb la seva llavor (`cadena/xarxes.py`; la primera és la de la T3m). Tots tenen els paràmetres del
decodificador triats amb els altres nou partits als escenaris ×¼.

## L'spellF1 i el macroF1 de cada mètode (mitjana dels deu partits)

**spellF1**

| escenari | A context | A xarxa | A xarxes |
|---|---|---|---|
| net | 0.775 | 0.803 | 0.808 |
| curts ×¼ | 0.639 | 0.683 | 0.684 |
| llargs ×¼ | 0.621 | 0.659 | 0.662 |
| barreja ×¼ | 0.631 | 0.667 | 0.671 |
| aire ×¼ | 0.556 | 0.600 | 0.612 |
| curts | 0.583 | 0.642 | 0.644 |
| llargs | 0.547 | 0.607 | 0.607 |
| barreja | 0.562 | 0.611 | 0.616 |
| aire | 0.508 | 0.563 | 0.564 |
| soroll2 | 0.373 | 0.473 | 0.478 |

**macroF1**

| escenari | A context | A xarxa | A xarxes |
|---|---|---|---|
| net | 0.952 | 0.953 | 0.954 |
| curts ×¼ | 0.919 | 0.925 | 0.925 |
| llargs ×¼ | 0.906 | 0.909 | 0.910 |
| barreja ×¼ | 0.910 | 0.914 | 0.915 |
| aire ×¼ | 0.886 | 0.893 | 0.895 |
| curts | 0.902 | 0.911 | 0.912 |
| llargs | 0.885 | 0.894 | 0.894 |
| barreja | 0.886 | 0.897 | 0.898 |
| aire | 0.865 | 0.876 | 0.877 |
| soroll2 | 0.697 | 0.774 | 0.770 |

## A xarxes contra A context (spellF1): el criteri

| escenari | A context | A xarxes | diferència | interval del 95 % | A xarxes guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.775 | 0.808 | +0.033 | +0.018 a +0.048 | 8 de 10 | no perd | ✓ |
| curts ×¼ | 0.639 | 0.684 | +0.045 | +0.031 a +0.057 | 9 de 10 | guanya clarament | ✓ |
| llargs ×¼ | 0.621 | 0.662 | +0.040 | +0.030 a +0.050 | 10 de 10 | guanya clarament | ✓ |
| barreja ×¼ | 0.631 | 0.671 | +0.040 | +0.029 a +0.051 | 10 de 10 | guanya clarament | ✓ |
| aire ×¼ | 0.556 | 0.612 | +0.055 | +0.040 a +0.070 | 10 de 10 | guanya clarament | ✓ |
| curts | 0.583 | 0.644 | +0.061 | +0.051 a +0.070 | 10 de 10 | no perd | ✓ |
| llargs | 0.547 | 0.607 | +0.060 | +0.043 a +0.078 | 10 de 10 | no perd | ✓ |
| barreja | 0.562 | 0.616 | +0.055 | +0.038 a +0.073 | 10 de 10 | no perd | ✓ |
| aire | 0.508 | 0.564 | +0.056 | +0.047 a +0.064 | 10 de 10 | no perd | ✓ |
| soroll2 | 0.373 | 0.478 | +0.105 | +0.096 a +0.114 | 10 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre escenaris ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✓ |
| El net, els ×1 i el soroll2 | no perd a cap (diferència ≥ −0.04) | ✓ |

**Passa.**

## A xarxes contra A xarxa (spellF1), només per saber-ho

El mateix amb una sola xarxa: la diferència és el que hi afegeix la mitjana.

| escenari | A xarxa | A xarxes | diferència | interval del 95 % | A xarxes guanya |
|---|---|---|---|---|---|
| net | 0.803 | 0.808 | +0.006 | +0.001 a +0.010 | 8 de 10 |
| curts ×¼ | 0.683 | 0.684 | +0.002 | -0.004 a +0.007 | 6 de 10 |
| llargs ×¼ | 0.659 | 0.662 | +0.003 | -0.004 a +0.010 | 5 de 10 |
| barreja ×¼ | 0.667 | 0.671 | +0.004 | -0.001 a +0.009 | 6 de 10 |
| aire ×¼ | 0.600 | 0.612 | +0.011 | +0.005 a +0.017 | 9 de 10 |
| curts | 0.642 | 0.644 | +0.002 | -0.002 a +0.006 | 7 de 10 |
| llargs | 0.607 | 0.607 | +0.000 | -0.005 a +0.005 | 4 de 10 |
| barreja | 0.611 | 0.616 | +0.005 | +0.000 a +0.010 | 8 de 10 |
| aire | 0.563 | 0.564 | +0.001 | -0.006 a +0.008 | 5 de 10 |
| soroll2 | 0.473 | 0.478 | +0.005 | -0.003 a +0.014 | 6 de 10 |

## Per font (spellF1, mitjana dels partits de cada font), només per saber-ho

| escenari | font | A context | A xarxa | A xarxes |
|---|---|---|---|---|
| net | dfl | 0.754 | 0.774 | 0.775 |
| net | metrica | 0.825 | 0.870 | 0.886 |
| curts ×¼ | dfl | 0.611 | 0.655 | 0.653 |
| curts ×¼ | metrica | 0.705 | 0.747 | 0.758 |
| llargs ×¼ | dfl | 0.594 | 0.627 | 0.630 |
| llargs ×¼ | metrica | 0.686 | 0.731 | 0.735 |
| barreja ×¼ | dfl | 0.604 | 0.639 | 0.643 |
| barreja ×¼ | metrica | 0.692 | 0.732 | 0.737 |
| aire ×¼ | dfl | 0.499 | 0.544 | 0.555 |
| aire ×¼ | metrica | 0.690 | 0.732 | 0.744 |
| curts | dfl | 0.560 | 0.611 | 0.615 |
| curts | metrica | 0.636 | 0.712 | 0.713 |
| llargs | dfl | 0.518 | 0.572 | 0.571 |
| llargs | metrica | 0.615 | 0.689 | 0.690 |
| barreja | dfl | 0.533 | 0.581 | 0.583 |
| barreja | metrica | 0.628 | 0.681 | 0.694 |
| aire | dfl | 0.454 | 0.511 | 0.510 |
| aire | metrica | 0.636 | 0.685 | 0.690 |
| soroll2 | dfl | 0.321 | 0.428 | 0.440 |
| soroll2 | metrica | 0.493 | 0.576 | 0.567 |

## L'encert de l'equip abans de decodificar (escenaris ×¼), només per saber-ho

A les imatges de les possessions de la veritat, la part on l'equip més probable és el de la veritat,
per durada de la possessió i segons si la pilota es veu. *El primer* és el primer
classificador d'A contacte sol.

| durada | pilota | el primer | la xarxa de la T3m sola | la mitjana de les cinc sola | A xarxa | A xarxes |
|---|---|---|---|---|---|---|
| <1 s | no | 0.285 | 0.158 | 0.160 | 0.369 | 0.369 |
| <1 s | sí | 0.595 | 0.450 | 0.445 | 0.665 | 0.657 |
| 1-2 s | no | 0.436 | 0.223 | 0.231 | 0.504 | 0.513 |
| 1-2 s | sí | 0.666 | 0.607 | 0.620 | 0.735 | 0.743 |
| 2-5 s | no | 0.569 | 0.307 | 0.317 | 0.607 | 0.615 |
| 2-5 s | sí | 0.754 | 0.724 | 0.746 | 0.805 | 0.809 |
| ≥5 s | no | 0.858 | 0.427 | 0.440 | 0.862 | 0.865 |
| ≥5 s | sí | 0.947 | 0.903 | 0.916 | 0.950 | 0.951 |

## Possessions predites per cada real (mitjana dels deu partits), només per saber-ho

| escenari | A context | A xarxa | A xarxes |
|---|---|---|---|
| net | 0.83 | 0.93 | 0.93 |
| curts ×¼ | 0.74 | 0.84 | 0.84 |
| llargs ×¼ | 0.73 | 0.82 | 0.82 |
| barreja ×¼ | 0.72 | 0.82 | 0.82 |
| aire ×¼ | 0.72 | 0.80 | 0.80 |
| curts | 0.72 | 0.83 | 0.84 |
| llargs | 0.68 | 0.79 | 0.79 |
| barreja | 0.70 | 0.80 | 0.79 |
| aire | 0.69 | 0.77 | 0.77 |
| soroll2 | 1.03 | 0.98 | 0.96 |

## Els paràmetres triats (cada partit, amb els altres nou)

- A context: λ = 4, durada mínima 12 · A xarxa: w = 4, λ = 32, durada mínima 12 · A xarxes: w = 4, λ = 64, durada mínima 12 (1 partits)
- A context: λ = 4, durada mínima 12 · A xarxa: w = 4, λ = 32, durada mínima 12 · A xarxes: w = 4, λ = 32, durada mínima 12 (6 partits)
- A context: λ = 2, durada mínima 25 · A xarxa: w = 4, λ = 32, durada mínima 12 · A xarxes: w = 4, λ = 32, durada mínima 12 (1 partits)
- A context: λ = 4, durada mínima 12 · A xarxa: w = 4, λ = 32, durada mínima 12 · A xarxes: w = 4, λ = 32, durada mínima 1 (1 partits)
- A context: λ = 4, durada mínima 12 · A xarxa: w = 4, λ = 16, durada mínima 12 · A xarxes: w = 4, λ = 32, durada mínima 12 (1 partits)
