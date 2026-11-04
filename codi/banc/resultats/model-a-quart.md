# Banc obert · A entrenat amb l'error del partit (T3b)

Generat amb `uv run python -I -m banc.model_a_quart`. Dades obertes: 7 partits de DFL (IDSSE, CC BY
4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i els
criteris: `docs/pla-tocs.md`, «T3b», i la capçalera de `banc/model_a_quart.py`.

**A** és el classificador d'ara, entrenat amb l'error de posició ×1, i **A ×¼**, el mateix entrenat amb
l'error ×¼. Tots dos tenen el decodificador triat amb els altres nou partits als escenaris ×¼. **A
cadena** és A amb el decodificador de la cadena d'ara, i **tocs ×¼**, el decodificador amb tocs a sobre
d'A ×¼, amb la tria de la T3.

## L'spellF1 i el macroF1 de cada mètode (mitjana dels deu partits)

**spellF1**

| escenari | A cadena | A | A ×¼ | tocs ×¼ |
|---|---|---|---|---|
| net | 0.521 | 0.522 | 0.644 | 0.653 |
| curts ×¼ | 0.494 | 0.495 | 0.587 | 0.593 |
| llargs ×¼ | 0.461 | 0.464 | 0.552 | 0.556 |
| barreja ×¼ | 0.473 | 0.476 | 0.562 | 0.566 |
| aire ×¼ | 0.428 | 0.434 | 0.503 | 0.501 |
| curts | 0.541 | 0.533 | 0.395 | 0.399 |
| llargs | 0.504 | 0.494 | 0.395 | 0.393 |
| barreja | 0.524 | 0.515 | 0.397 | 0.398 |
| aire | 0.477 | 0.479 | 0.368 | 0.371 |
| soroll2 | 0.347 | 0.344 | 0.325 | 0.335 |

**macroF1**

| escenari | A cadena | A | A ×¼ | tocs ×¼ |
|---|---|---|---|---|
| net | 0.864 | 0.864 | 0.926 | 0.930 |
| curts ×¼ | 0.853 | 0.854 | 0.907 | 0.908 |
| llargs ×¼ | 0.837 | 0.838 | 0.890 | 0.892 |
| barreja ×¼ | 0.841 | 0.842 | 0.894 | 0.895 |
| aire ×¼ | 0.822 | 0.823 | 0.866 | 0.867 |
| curts | 0.890 | 0.889 | 0.683 | 0.684 |
| llargs | 0.871 | 0.871 | 0.703 | 0.703 |
| barreja | 0.876 | 0.876 | 0.694 | 0.695 |
| aire | 0.855 | 0.856 | 0.680 | 0.681 |
| soroll2 | 0.663 | 0.661 | 0.586 | 0.588 |

## 1. A ×¼ contra A (spellF1)

| escenari | A | A ×¼ | diferència | interval del 95 % | A ×¼ guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.522 | 0.644 | +0.122 | +0.111 a +0.136 | 10 de 10 | no perd | ✓ |
| curts ×¼ | 0.495 | 0.587 | +0.092 | +0.078 a +0.106 | 10 de 10 | guanya clarament | ✓ |
| llargs ×¼ | 0.464 | 0.552 | +0.088 | +0.075 a +0.102 | 10 de 10 | guanya clarament | ✓ |
| barreja ×¼ | 0.476 | 0.562 | +0.086 | +0.070 a +0.104 | 10 de 10 | guanya clarament | ✓ |
| aire ×¼ | 0.434 | 0.503 | +0.069 | +0.055 a +0.087 | 10 de 10 | guanya clarament | ✓ |
| curts | 0.533 | 0.395 | -0.138 | -0.145 a -0.131 | 0 de 10 | no perd | ✗ |
| llargs | 0.494 | 0.395 | -0.100 | -0.110 a -0.088 | 0 de 10 | no perd | ✗ |
| barreja | 0.515 | 0.397 | -0.119 | -0.133 a -0.105 | 0 de 10 | no perd | ✗ |
| aire | 0.479 | 0.368 | -0.112 | -0.129 a -0.095 | 0 de 10 | no perd | ✗ |
| soroll2 | 0.344 | 0.325 | -0.019 | -0.029 a -0.007 | 1 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre escenaris ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✓ |
| El net, els ×1 i el soroll2 | no perd a cap (diferència ≥ −0.04) | ✗ |

**No passa.**

## 2. Els tocs a sobre d'A ×¼, contra A ×¼ (spellF1)

| escenari | A ×¼ | tocs ×¼ | diferència | interval del 95 % | tocs ×¼ guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.644 | 0.653 | +0.009 | +0.003 a +0.015 | 7 de 10 | no perd | ✓ |
| curts ×¼ | 0.587 | 0.593 | +0.005 | +0.001 a +0.010 | 8 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.552 | 0.556 | +0.004 | -0.000 a +0.009 | 6 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.562 | 0.566 | +0.004 | +0.002 a +0.006 | 9 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.503 | 0.501 | -0.002 | -0.006 a +0.002 | 4 de 10 | guanya clarament | ✗ |
| curts | 0.395 | 0.399 | +0.004 | +0.000 a +0.008 | 8 de 10 | no perd | ✓ |
| llargs | 0.395 | 0.393 | -0.002 | -0.008 a +0.004 | 5 de 10 | no perd | ✓ |
| barreja | 0.397 | 0.398 | +0.001 | -0.003 a +0.004 | 5 de 10 | no perd | ✓ |
| aire | 0.368 | 0.371 | +0.003 | -0.001 a +0.007 | 8 de 10 | no perd | ✓ |
| soroll2 | 0.325 | 0.335 | +0.010 | +0.007 a +0.013 | 10 de 10 | no perd | ✓ |

**Les passades llargues (T1).** Possessions de 2 s o més, amb pilota abans del canvi i passada
llarga: la part dels canvis de la veritat on el mètode canvia a temps (a menys d'1 s) i abans d'hora
(1 s o més).

| escenari | canvis | A ×¼ a temps | tocs ×¼ a temps | A ×¼ abans d'hora | tocs ×¼ abans d'hora |
|---|---|---|---|---|---|
| curts ×¼ | 121 | 54% | 54% | 2% | 2% |
| llargs ×¼ | 175 | 53% | 57% | 3% | 4% |
| barreja ×¼ | 162 | 52% | 55% | 2% | 3% |
| aire ×¼ | 178 | 37% | 33% | 3% | 3% |
| els quatre ×¼ | 636 | 49% | 49% | 3% | 3% |

| | Passa si | |
|---|---|---|
| Els quatre escenaris ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1 i el soroll2 | no perd a cap (diferència ≥ −0.04) | ✓ |
| Les passades llargues, els quatre ×¼ junts | a temps puja, i abans d'hora no puja | ✗ |

**No passa.**

## Les combinacions triades (cada partit, amb els altres nou)

- A: λ = 16, durada mínima 25 · A ×¼: λ = 8, durada mínima 25 · tocs ×¼: k = 5, 5 m/s, 1.5 m; control 1, λ_vis 16, λ 8, durada mínima 25 (10 partits)
