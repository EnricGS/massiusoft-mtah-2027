# Banc obert · Els senyals del control al classificador d'A (T3d)

Generat amb `uv run python -I -m banc.model_a_control`. Dades obertes: 7 partits de DFL (IDSSE, CC BY
4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3d», i la capçalera de `banc/model_a_control.py`.

**A ×1+×¼** és el classificador de la cadena d'ara (T3c), i **A control**, el mateix amb els
senyals del control (`cadena/control.py`). Tots dos tenen el decodificador triat amb els altres nou
partits als escenaris ×¼.

## L'spellF1 i el macroF1 de cada classificador (mitjana dels deu partits)

**spellF1**

| escenari | A ×1+×¼ | A control |
|---|---|---|
| net | 0.625 | 0.746 |
| curts ×¼ | 0.569 | 0.606 |
| llargs ×¼ | 0.531 | 0.593 |
| barreja ×¼ | 0.544 | 0.601 |
| aire ×¼ | 0.493 | 0.525 |
| curts | 0.535 | 0.545 |
| llargs | 0.497 | 0.510 |
| barreja | 0.515 | 0.523 |
| aire | 0.466 | 0.477 |
| soroll2 | 0.348 | 0.333 |

**macroF1**

| escenari | A ×1+×¼ | A control |
|---|---|---|
| net | 0.922 | 0.945 |
| curts ×¼ | 0.903 | 0.913 |
| llargs ×¼ | 0.883 | 0.897 |
| barreja ×¼ | 0.887 | 0.902 |
| aire ×¼ | 0.862 | 0.876 |
| curts | 0.884 | 0.890 |
| llargs | 0.865 | 0.872 |
| barreja | 0.870 | 0.874 |
| aire | 0.848 | 0.854 |
| soroll2 | 0.673 | 0.670 |

## A control contra A ×1+×¼ (spellF1): el criteri

| escenari | A ×1+×¼ | A control | diferència | interval del 95 % | A control guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.625 | 0.746 | +0.121 | +0.103 a +0.137 | 10 de 10 | no perd | ✓ |
| curts ×¼ | 0.569 | 0.606 | +0.037 | +0.029 a +0.045 | 10 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.531 | 0.593 | +0.061 | +0.049 a +0.075 | 10 de 10 | guanya clarament | ✓ |
| barreja ×¼ | 0.544 | 0.601 | +0.056 | +0.048 a +0.064 | 10 de 10 | guanya clarament | ✓ |
| aire ×¼ | 0.493 | 0.525 | +0.032 | +0.023 a +0.041 | 10 de 10 | guanya clarament | ✗ |
| curts | 0.535 | 0.545 | +0.011 | +0.000 a +0.021 | 7 de 10 | no perd | ✓ |
| llargs | 0.497 | 0.510 | +0.012 | +0.003 a +0.020 | 8 de 10 | no perd | ✓ |
| barreja | 0.515 | 0.523 | +0.008 | +0.000 a +0.015 | 6 de 10 | no perd | ✓ |
| aire | 0.466 | 0.477 | +0.011 | +0.002 a +0.019 | 8 de 10 | no perd | ✓ |
| soroll2 | 0.348 | 0.333 | -0.015 | -0.026 a -0.004 | 2 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre escenaris ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1 i el soroll2 | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## Els decodificadors triats (cada partit, amb els altres nou)

- A ×1+×¼: λ = 8, durada mínima 25 · A control: λ = 4, durada mínima 25 (10 partits)
