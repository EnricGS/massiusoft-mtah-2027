# Banc obert · el decodificador amb tocs (T3)

Generat amb `uv run python -I -m banc.decodificador_tocs`. Dades obertes: 7 partits de DFL (IDSSE, CC BY
4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i els
criteris: `docs/pla-tocs.md`, «T3: els criteris», i la capçalera de `banc/decodificador_tocs.py`.

**A** té el decodificador triat amb els altres nou partits als escenaris ×¼, i **A cadena**, el de la
cadena d'ara (triat als ×1). **Tocs** és el model nou, amb la mateixa tria. Els tres fan servir el
mateix classificador.

## L'spellF1, escenari per escenari

| escenari | A cadena | A | tocs | tocs − A | interval del 95 % | tocs guanya | criteri | |
|---|---|---|---|---|---|---|---|---|
| net | 0.521 | 0.522 | 0.545 | +0.023 | +0.017 a +0.030 | 10 de 10 | no perd | ✓ |
| curts ×¼ | 0.494 | 0.495 | 0.501 | +0.006 | +0.003 a +0.010 | 9 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.461 | 0.464 | 0.473 | +0.009 | +0.007 a +0.012 | 10 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.473 | 0.476 | 0.485 | +0.009 | +0.006 a +0.011 | 10 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.428 | 0.434 | 0.436 | +0.003 | +0.001 a +0.005 | 8 de 10 | guanya clarament | ✗ |
| curts | 0.541 | 0.533 | 0.537 | +0.004 | -0.000 a +0.007 | 8 de 10 | no perd | ✓ |
| llargs | 0.504 | 0.494 | 0.497 | +0.003 | -0.001 a +0.006 | 6 de 10 | no perd | ✓ |
| barreja | 0.524 | 0.515 | 0.519 | +0.003 | -0.001 a +0.007 | 8 de 10 | no perd | ✓ |
| aire | 0.477 | 0.479 | 0.479 | -0.000 | -0.003 a +0.002 | 6 de 10 | no perd | ✓ |
| soroll2 | 0.347 | 0.344 | 0.345 | +0.001 | -0.001 a +0.003 | 7 de 10 | no perd | ✓ |

**El macroF1** (mitjana dels deu partits)

| escenari | A cadena | A | tocs |
|---|---|---|---|
| net | 0.864 | 0.864 | 0.870 |
| curts ×¼ | 0.853 | 0.854 | 0.855 |
| llargs ×¼ | 0.837 | 0.838 | 0.840 |
| barreja ×¼ | 0.841 | 0.842 | 0.844 |
| aire ×¼ | 0.822 | 0.823 | 0.824 |
| curts | 0.890 | 0.889 | 0.890 |
| llargs | 0.871 | 0.871 | 0.871 |
| barreja | 0.876 | 0.876 | 0.876 |
| aire | 0.855 | 0.856 | 0.856 |
| soroll2 | 0.663 | 0.661 | 0.661 |

## Les passades llargues (T1)

Possessions de 2 s o més, amb pilota abans del canvi i passada llarga: la part dels canvis de la
veritat on el mètode canvia a temps (a menys d'1 s) i abans d'hora (1 s o més).

| escenari | canvis | A a temps | tocs a temps | A abans d'hora | tocs abans d'hora |
|---|---|---|---|---|---|
| curts ×¼ | 121 | 43% | 44% | 2% | 2% |
| llargs ×¼ | 175 | 46% | 49% | 5% | 5% |
| barreja ×¼ | 162 | 46% | 49% | 3% | 4% |
| aire ×¼ | 178 | 29% | 29% | 6% | 6% |
| els quatre ×¼ | 636 | 41% | 42% | 4% | 4% |

## Les combinacions triades (cada partit, amb els altres nou)

- A: λ = 16, durada mínima 25 · tocs: k = 5, 5 m/s, 1.5 m; control 1, λ_vis 16, λ 16, durada mínima 25 (9 partits)
- A: λ = 16, durada mínima 25 · tocs: k = 5, 5 m/s, 1.5 m; control 1, λ_vis 16, λ 16, durada mínima 1 (1 partits)

## Els criteris

| | Passa si | |
|---|---|---|
| Els quatre escenaris ×¼ | guanya A clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1 i el soroll2 | no perd a cap (diferència ≥ −0.04) | ✓ |
| Les passades llargues, els quatre ×¼ junts | a temps puja, i abans d'hora no puja | ✗ |

**No passa.**
