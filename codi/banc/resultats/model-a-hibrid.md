# Banc obert · L'híbrid, cada model on toca (T3g)

Generat amb `uv run python -I -m banc.model_a_hibrid`. Dades obertes: 7 partits de DFL (IDSSE, CC BY
4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3g», i la capçalera de `banc/model_a_hibrid.py`.

**A context** és el model de la cadena (T3e). **A híbrid** fa servir A per possessió (T3f) a les
imatges de les possessions que aquest mateix prediu de menys de T s, i A context a la resta. T, λ i la
durada mínima es trien junts amb els altres nou partits als escenaris ×¼; amb T = 0, és A context.

## L'spellF1 i el macroF1 de cada classificador (mitjana dels deu partits)

**spellF1**

| escenari | A context | A híbrid |
|---|---|---|
| net | 0.775 | 0.785 |
| curts ×¼ | 0.639 | 0.644 |
| llargs ×¼ | 0.621 | 0.634 |
| barreja ×¼ | 0.631 | 0.649 |
| aire ×¼ | 0.556 | 0.568 |
| curts | 0.583 | 0.587 |
| llargs | 0.547 | 0.559 |
| barreja | 0.562 | 0.568 |
| aire | 0.508 | 0.517 |
| soroll2 | 0.373 | 0.379 |

**macroF1**

| escenari | A context | A híbrid |
|---|---|---|
| net | 0.952 | 0.951 |
| curts ×¼ | 0.919 | 0.916 |
| llargs ×¼ | 0.906 | 0.905 |
| barreja ×¼ | 0.910 | 0.910 |
| aire ×¼ | 0.886 | 0.885 |
| curts | 0.902 | 0.899 |
| llargs | 0.885 | 0.883 |
| barreja | 0.886 | 0.883 |
| aire | 0.865 | 0.863 |
| soroll2 | 0.697 | 0.687 |

## A híbrid contra A context (spellF1): el criteri

| escenari | A context | A híbrid | diferència | interval del 95 % | A híbrid guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.775 | 0.785 | +0.011 | +0.000 a +0.021 | 7 de 10 | no perd | ✓ |
| curts ×¼ | 0.639 | 0.644 | +0.005 | -0.009 a +0.018 | 7 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.621 | 0.634 | +0.012 | +0.003 a +0.022 | 8 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.631 | 0.649 | +0.019 | +0.007 a +0.029 | 9 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.556 | 0.568 | +0.011 | +0.003 a +0.021 | 8 de 10 | guanya clarament | ✗ |
| curts | 0.583 | 0.587 | +0.004 | -0.005 a +0.013 | 6 de 10 | no perd | ✓ |
| llargs | 0.547 | 0.559 | +0.012 | +0.003 a +0.021 | 7 de 10 | no perd | ✓ |
| barreja | 0.562 | 0.568 | +0.006 | -0.004 a +0.017 | 5 de 10 | no perd | ✓ |
| aire | 0.508 | 0.517 | +0.009 | +0.000 a +0.018 | 7 de 10 | no perd | ✓ |
| soroll2 | 0.373 | 0.379 | +0.006 | +0.000 a +0.011 | 8 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre escenaris ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1 i el soroll2 | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## Possessions predites per cada real (mitjana dels deu partits), només per saber-ho

| escenari | A context | A híbrid |
|---|---|---|
| net | 0.83 | 0.91 |
| curts ×¼ | 0.74 | 0.83 |
| llargs ×¼ | 0.73 | 0.81 |
| barreja ×¼ | 0.72 | 0.81 |
| aire ×¼ | 0.72 | 0.81 |
| curts | 0.72 | 0.81 |
| llargs | 0.68 | 0.78 |
| barreja | 0.70 | 0.79 |
| aire | 0.69 | 0.78 |
| soroll2 | 1.03 | 1.10 |

## La part de les imatges puntuades que la porta marca com a curtes, només per saber-ho

Mitjana dels deu partits als quatre escenaris ×¼.

| T | curtes |
|---|---|
| 0 s | 0 % |
| 1 s | 0 % |
| 2 s | 1 % |
| 5 s | 7 % |

## Els decodificadors triats (cada partit, amb els altres nou)

- A context: λ = 4, durada mínima 12 · A híbrid: T = 5 s, λ = 8, durada mínima 1 (1 partits)
- A context: λ = 4, durada mínima 12 · A híbrid: T = 5 s, λ = 8, durada mínima 12 (8 partits)
- A context: λ = 2, durada mínima 25 · A híbrid: T = 5 s, λ = 8, durada mínima 12 (1 partits)
