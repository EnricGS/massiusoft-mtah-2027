# Banc obert · A entrenat amb els dos errors (T3c)

Generat amb `uv run python -I -m banc.model_a_dos_errors`. Dades obertes: 7 partits de DFL (IDSSE, CC
BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3c», i la capçalera de `banc/model_a_dos_errors.py`.

**A** és el classificador d'ara, entrenat amb l'error de posició ×1; **A ×¼**, el de la T3b, entrenat
amb l'error ×¼; i **A ×1+×¼**, entrenat amb tots dos. Els tres tenen el decodificador triat amb els
altres nou partits als escenaris ×¼. **A cadena** és A amb el decodificador de la cadena d'ara.

## L'spellF1 i el macroF1 de cada classificador (mitjana dels deu partits)

**spellF1**

| escenari | A cadena | A | A ×¼ | A ×1+×¼ |
|---|---|---|---|---|
| net | 0.521 | 0.522 | 0.644 | 0.625 |
| curts ×¼ | 0.494 | 0.495 | 0.587 | 0.569 |
| llargs ×¼ | 0.461 | 0.464 | 0.552 | 0.531 |
| barreja ×¼ | 0.473 | 0.476 | 0.562 | 0.544 |
| aire ×¼ | 0.428 | 0.434 | 0.503 | 0.493 |
| curts | 0.541 | 0.533 | 0.395 | 0.535 |
| llargs | 0.504 | 0.494 | 0.395 | 0.497 |
| barreja | 0.524 | 0.515 | 0.397 | 0.515 |
| aire | 0.477 | 0.479 | 0.368 | 0.466 |
| soroll2 | 0.347 | 0.344 | 0.325 | 0.348 |

**macroF1**

| escenari | A cadena | A | A ×¼ | A ×1+×¼ |
|---|---|---|---|---|
| net | 0.864 | 0.864 | 0.926 | 0.922 |
| curts ×¼ | 0.853 | 0.854 | 0.907 | 0.903 |
| llargs ×¼ | 0.837 | 0.838 | 0.890 | 0.883 |
| barreja ×¼ | 0.841 | 0.842 | 0.894 | 0.887 |
| aire ×¼ | 0.822 | 0.823 | 0.866 | 0.862 |
| curts | 0.890 | 0.889 | 0.683 | 0.884 |
| llargs | 0.871 | 0.871 | 0.703 | 0.865 |
| barreja | 0.876 | 0.876 | 0.694 | 0.870 |
| aire | 0.855 | 0.856 | 0.680 | 0.848 |
| soroll2 | 0.663 | 0.661 | 0.586 | 0.673 |

## A ×1+×¼ contra A (spellF1): el criteri

| escenari | A | A ×1+×¼ | diferència | interval del 95 % | A ×1+×¼ guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.522 | 0.625 | +0.104 | +0.092 a +0.117 | 10 de 10 | no perd | ✓ |
| curts ×¼ | 0.495 | 0.569 | +0.074 | +0.060 a +0.089 | 10 de 10 | guanya clarament | ✓ |
| llargs ×¼ | 0.464 | 0.531 | +0.067 | +0.059 a +0.077 | 10 de 10 | guanya clarament | ✓ |
| barreja ×¼ | 0.476 | 0.544 | +0.068 | +0.055 a +0.084 | 10 de 10 | guanya clarament | ✓ |
| aire ×¼ | 0.434 | 0.493 | +0.059 | +0.051 a +0.068 | 10 de 10 | guanya clarament | ✓ |
| curts | 0.533 | 0.535 | +0.001 | -0.005 a +0.007 | 6 de 10 | no perd | ✓ |
| llargs | 0.494 | 0.497 | +0.003 | -0.002 a +0.009 | 5 de 10 | no perd | ✓ |
| barreja | 0.515 | 0.515 | -0.000 | -0.009 a +0.008 | 5 de 10 | no perd | ✓ |
| aire | 0.479 | 0.466 | -0.013 | -0.021 a -0.006 | 2 de 10 | no perd | ✓ |
| soroll2 | 0.344 | 0.348 | +0.004 | -0.005 a +0.010 | 7 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre escenaris ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✓ |
| El net, els ×1 i el soroll2 | no perd a cap (diferència ≥ −0.04) | ✓ |

**Passa.**

## A ×1+×¼ contra A ×¼ (spellF1), només per saber-ho

| escenari | A ×¼ | A ×1+×¼ | diferència | interval del 95 % | A ×1+×¼ guanya |
|---|---|---|---|---|---|
| net | 0.644 | 0.625 | -0.018 | -0.025 a -0.011 | 0 de 10 |
| curts ×¼ | 0.587 | 0.569 | -0.018 | -0.027 a -0.011 | 1 de 10 |
| llargs ×¼ | 0.552 | 0.531 | -0.021 | -0.029 a -0.012 | 0 de 10 |
| barreja ×¼ | 0.562 | 0.544 | -0.018 | -0.023 a -0.013 | 0 de 10 |
| aire ×¼ | 0.503 | 0.493 | -0.010 | -0.019 a -0.002 | 3 de 10 |
| curts | 0.395 | 0.535 | +0.140 | +0.131 a +0.148 | 10 de 10 |
| llargs | 0.395 | 0.497 | +0.103 | +0.096 a +0.108 | 10 de 10 |
| barreja | 0.397 | 0.515 | +0.119 | +0.109 a +0.129 | 10 de 10 |
| aire | 0.368 | 0.466 | +0.099 | +0.087 a +0.110 | 10 de 10 |
| soroll2 | 0.325 | 0.348 | +0.023 | +0.011 a +0.032 | 9 de 10 |

## Els decodificadors triats (cada partit, amb els altres nou)

- A: λ = 16, durada mínima 25 · A ×¼: λ = 8, durada mínima 25 · A ×1+×¼: λ = 8, durada mínima 25 (10 partits)
