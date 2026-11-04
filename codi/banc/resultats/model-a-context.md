# Banc obert · Un segon classificador d'A, que mira el primer al voltant (T3e)

Generat amb `uv run python -I -m banc.model_a_context`. Dades obertes: 7 partits de DFL (IDSSE, CC BY
4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3e», i la capçalera de `banc/model_a_context.py`.

**A ×1+×¼** és el classificador de la cadena d'ara (T3c); **A control**, el mateix amb els
senyals del control (T3d); i **A context**, un segon classificador que mira les probabilitats
d'A control al voltant de cada imatge. Tots tenen el decodificador triat amb els altres nou
partits als escenaris ×¼.

## L'spellF1 i el macroF1 de cada classificador (mitjana dels deu partits)

**spellF1**

| escenari | A ×1+×¼ | A control | A context |
|---|---|---|---|
| net | 0.625 | 0.746 | 0.775 |
| curts ×¼ | 0.569 | 0.606 | 0.639 |
| llargs ×¼ | 0.531 | 0.593 | 0.621 |
| barreja ×¼ | 0.544 | 0.601 | 0.631 |
| aire ×¼ | 0.493 | 0.525 | 0.556 |
| curts | 0.535 | 0.545 | 0.583 |
| llargs | 0.497 | 0.510 | 0.547 |
| barreja | 0.515 | 0.523 | 0.562 |
| aire | 0.466 | 0.477 | 0.508 |
| soroll2 | 0.348 | 0.333 | 0.373 |

**macroF1**

| escenari | A ×1+×¼ | A control | A context |
|---|---|---|---|
| net | 0.922 | 0.945 | 0.952 |
| curts ×¼ | 0.903 | 0.913 | 0.919 |
| llargs ×¼ | 0.883 | 0.897 | 0.906 |
| barreja ×¼ | 0.887 | 0.902 | 0.910 |
| aire ×¼ | 0.862 | 0.876 | 0.886 |
| curts | 0.884 | 0.890 | 0.902 |
| llargs | 0.865 | 0.872 | 0.885 |
| barreja | 0.870 | 0.874 | 0.886 |
| aire | 0.848 | 0.854 | 0.865 |
| soroll2 | 0.673 | 0.670 | 0.697 |

## A context contra A ×1+×¼ (spellF1): el criteri

| escenari | A ×1+×¼ | A context | diferència | interval del 95 % | A context guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.625 | 0.775 | +0.149 | +0.131 a +0.164 | 10 de 10 | no perd | ✓ |
| curts ×¼ | 0.569 | 0.639 | +0.071 | +0.059 a +0.082 | 10 de 10 | guanya clarament | ✓ |
| llargs ×¼ | 0.531 | 0.621 | +0.090 | +0.074 a +0.107 | 10 de 10 | guanya clarament | ✓ |
| barreja ×¼ | 0.544 | 0.631 | +0.086 | +0.075 a +0.098 | 10 de 10 | guanya clarament | ✓ |
| aire ×¼ | 0.493 | 0.556 | +0.064 | +0.049 a +0.077 | 10 de 10 | guanya clarament | ✓ |
| curts | 0.535 | 0.583 | +0.048 | +0.037 a +0.060 | 10 de 10 | no perd | ✓ |
| llargs | 0.497 | 0.547 | +0.050 | +0.036 a +0.061 | 10 de 10 | no perd | ✓ |
| barreja | 0.515 | 0.562 | +0.046 | +0.037 a +0.055 | 10 de 10 | no perd | ✓ |
| aire | 0.466 | 0.508 | +0.042 | +0.033 a +0.050 | 10 de 10 | no perd | ✓ |
| soroll2 | 0.348 | 0.373 | +0.025 | +0.018 a +0.034 | 8 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre escenaris ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✓ |
| El net, els ×1 i el soroll2 | no perd a cap (diferència ≥ −0.04) | ✓ |

**Passa.**

## A context contra A control (spellF1), només per saber-ho

| escenari | A control | A context | diferència | interval del 95 % | A context guanya |
|---|---|---|---|---|---|
| net | 0.746 | 0.775 | +0.029 | +0.021 a +0.037 | 10 de 10 |
| curts ×¼ | 0.606 | 0.639 | +0.034 | +0.027 a +0.040 | 10 de 10 |
| llargs ×¼ | 0.593 | 0.621 | +0.029 | +0.020 a +0.036 | 10 de 10 |
| barreja ×¼ | 0.601 | 0.631 | +0.030 | +0.025 a +0.036 | 10 de 10 |
| aire ×¼ | 0.525 | 0.556 | +0.031 | +0.020 a +0.042 | 9 de 10 |
| curts | 0.545 | 0.583 | +0.038 | +0.031 a +0.045 | 10 de 10 |
| llargs | 0.510 | 0.547 | +0.038 | +0.030 a +0.045 | 10 de 10 |
| barreja | 0.523 | 0.562 | +0.039 | +0.032 a +0.045 | 10 de 10 |
| aire | 0.477 | 0.508 | +0.031 | +0.022 a +0.040 | 10 de 10 |
| soroll2 | 0.333 | 0.373 | +0.040 | +0.031 a +0.048 | 9 de 10 |

## Els decodificadors triats (cada partit, amb els altres nou)

- A ×1+×¼: λ = 8, durada mínima 25 · A control: λ = 4, durada mínima 25 · A context: λ = 4, durada mínima 12 (9 partits)
- A ×1+×¼: λ = 8, durada mínima 25 · A control: λ = 4, durada mínima 25 · A context: λ = 2, durada mínima 25 (1 partits)
