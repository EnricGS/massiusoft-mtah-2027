# Banc obert · Entrenar també com el partit (T3p)

Generat amb `uv run python -I -m banc.model_a_partit`. Dades obertes: 7 partits de DFL (IDSSE, CC BY
4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3p», i la capçalera de `banc/model_a_partit.py`.

**A context** i **A xarxes** són els de la T3e i la T3o, tal com són, amb el decodificador triat
als quatre ×¼. **A partit** és A xarxes entrenat també a «partit ×¼» (`banc/escenari_partit.py`),
amb el decodificador triat als cinc ×¼. Cada partit, amb els paràmetres triats amb els altres nou.

## Pas 1: els models refets

A la memòria cau només hi ha les probabilitats als deu escenaris de la T3: per tenir-les a
«partit ×¼», els models del partit que es prova es tornen a fer igual. Contra les de la memòria cau, als
deu escenaris i al prior:

| peça | la diferència més gran (els deu partits) | |
|---|---|---|
| A context | 0 | ✓ la mateixa |
| el primer | 0 | ✓ la mateixa |
| les cinc xarxes | 0 | ✓ la mateixa |
| A xarxes | 0 | ✓ la mateixa |
| el de canvis | 0 | ✓ la mateixa |

## L'spellF1 i el macroF1 de cada mètode (mitjana dels deu partits)

**spellF1**

| escenari | A context | A xarxes | A partit |
|---|---|---|---|
| net | 0.775 | 0.808 | 0.814 |
| curts ×¼ | 0.639 | 0.684 | 0.687 |
| llargs ×¼ | 0.621 | 0.662 | 0.667 |
| barreja ×¼ | 0.631 | 0.671 | 0.675 |
| aire ×¼ | 0.556 | 0.612 | 0.602 |
| curts | 0.583 | 0.644 | 0.645 |
| llargs | 0.547 | 0.607 | 0.604 |
| barreja | 0.562 | 0.616 | 0.612 |
| aire | 0.508 | 0.564 | 0.564 |
| soroll2 | 0.373 | 0.478 | 0.469 |
| partit ×¼ | 0.711 | 0.757 | 0.765 |

**macroF1**

| escenari | A context | A xarxes | A partit |
|---|---|---|---|
| net | 0.952 | 0.954 | 0.954 |
| curts ×¼ | 0.919 | 0.925 | 0.926 |
| llargs ×¼ | 0.906 | 0.910 | 0.910 |
| barreja ×¼ | 0.910 | 0.915 | 0.916 |
| aire ×¼ | 0.886 | 0.895 | 0.889 |
| curts | 0.902 | 0.912 | 0.912 |
| llargs | 0.885 | 0.894 | 0.893 |
| barreja | 0.886 | 0.898 | 0.898 |
| aire | 0.865 | 0.877 | 0.877 |
| soroll2 | 0.697 | 0.770 | 0.766 |
| partit ×¼ | 0.936 | 0.940 | 0.944 |

## A partit contra A xarxes (spellF1): el criteri

| escenari | A xarxes | A partit | diferència | interval del 95 % | A partit guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.808 | 0.814 | +0.006 | +0.001 a +0.011 | 7 de 10 | no perd | ✓ |
| curts ×¼ | 0.684 | 0.687 | +0.003 | -0.001 a +0.006 | 8 de 10 | no perd | ✓ |
| llargs ×¼ | 0.662 | 0.667 | +0.005 | +0.002 a +0.010 | 6 de 10 | no perd | ✓ |
| barreja ×¼ | 0.671 | 0.675 | +0.004 | -0.000 a +0.007 | 7 de 10 | no perd | ✓ |
| aire ×¼ | 0.612 | 0.602 | -0.009 | -0.017 a -0.002 | 3 de 10 | no perd | ✓ |
| curts | 0.644 | 0.645 | +0.001 | -0.003 a +0.007 | 5 de 10 | no perd | ✓ |
| llargs | 0.607 | 0.604 | -0.003 | -0.010 a +0.004 | 5 de 10 | no perd | ✓ |
| barreja | 0.616 | 0.612 | -0.004 | -0.010 a +0.001 | 3 de 10 | no perd | ✓ |
| aire | 0.564 | 0.564 | -0.000 | -0.006 a +0.005 | 4 de 10 | no perd | ✓ |
| soroll2 | 0.478 | 0.469 | -0.009 | -0.013 a -0.004 | 1 de 10 | no perd | ✓ |
| partit ×¼ | 0.757 | 0.765 | +0.008 | -0.001 a +0.016 | 6 de 10 | guanya clarament | ✗ |

| | Passa si | |
|---|---|---|
| «partit ×¼» | guanya clarament (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| Els quatre ×¼ d'ara, el net, els ×1 i el soroll2 | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## Pas 1: A xarxes contra A context (spellF1), només per saber-ho

Si a «partit ×¼» l'ordre és el mateix que als ×¼ d'ara.

| escenari | A context | A xarxes | diferència | interval del 95 % | A xarxes guanya |
|---|---|---|---|---|---|
| net | 0.775 | 0.808 | +0.033 | +0.018 a +0.048 | 8 de 10 |
| curts ×¼ | 0.639 | 0.684 | +0.045 | +0.031 a +0.057 | 9 de 10 |
| llargs ×¼ | 0.621 | 0.662 | +0.040 | +0.030 a +0.050 | 10 de 10 |
| barreja ×¼ | 0.631 | 0.671 | +0.040 | +0.029 a +0.051 | 10 de 10 |
| aire ×¼ | 0.556 | 0.612 | +0.055 | +0.040 a +0.070 | 10 de 10 |
| curts | 0.583 | 0.644 | +0.061 | +0.051 a +0.070 | 10 de 10 |
| llargs | 0.547 | 0.607 | +0.060 | +0.043 a +0.078 | 10 de 10 |
| barreja | 0.562 | 0.616 | +0.055 | +0.038 a +0.073 | 10 de 10 |
| aire | 0.508 | 0.564 | +0.056 | +0.047 a +0.064 | 10 de 10 |
| soroll2 | 0.373 | 0.478 | +0.105 | +0.096 a +0.114 | 10 de 10 |
| partit ×¼ | 0.711 | 0.757 | +0.046 | +0.030 a +0.062 | 10 de 10 |

## Per font (spellF1, mitjana dels partits de cada font), només per saber-ho

| escenari | font | A context | A xarxes | A partit |
|---|---|---|---|---|
| net | dfl | 0.754 | 0.775 | 0.781 |
| net | metrica | 0.825 | 0.886 | 0.892 |
| curts ×¼ | dfl | 0.611 | 0.653 | 0.656 |
| curts ×¼ | metrica | 0.705 | 0.758 | 0.760 |
| llargs ×¼ | dfl | 0.594 | 0.630 | 0.632 |
| llargs ×¼ | metrica | 0.686 | 0.735 | 0.749 |
| barreja ×¼ | dfl | 0.604 | 0.643 | 0.648 |
| barreja ×¼ | metrica | 0.692 | 0.737 | 0.738 |
| aire ×¼ | dfl | 0.499 | 0.555 | 0.539 |
| aire ×¼ | metrica | 0.690 | 0.744 | 0.750 |
| curts | dfl | 0.560 | 0.615 | 0.614 |
| curts | metrica | 0.636 | 0.713 | 0.718 |
| llargs | dfl | 0.518 | 0.571 | 0.567 |
| llargs | metrica | 0.615 | 0.690 | 0.688 |
| barreja | dfl | 0.533 | 0.583 | 0.580 |
| barreja | metrica | 0.628 | 0.694 | 0.687 |
| aire | dfl | 0.454 | 0.510 | 0.511 |
| aire | metrica | 0.636 | 0.690 | 0.687 |
| soroll2 | dfl | 0.321 | 0.440 | 0.432 |
| soroll2 | metrica | 0.493 | 0.567 | 0.556 |
| partit ×¼ | dfl | 0.686 | 0.728 | 0.738 |
| partit ×¼ | metrica | 0.768 | 0.824 | 0.827 |

## Possessions predites per cada real (mitjana dels deu partits), només per saber-ho

| escenari | A context | A xarxes | A partit |
|---|---|---|---|
| net | 0.83 | 0.93 | 0.94 |
| curts ×¼ | 0.74 | 0.84 | 0.84 |
| llargs ×¼ | 0.73 | 0.82 | 0.82 |
| barreja ×¼ | 0.72 | 0.82 | 0.83 |
| aire ×¼ | 0.72 | 0.80 | 0.80 |
| curts | 0.72 | 0.84 | 0.84 |
| llargs | 0.68 | 0.79 | 0.79 |
| barreja | 0.70 | 0.79 | 0.80 |
| aire | 0.69 | 0.77 | 0.77 |
| soroll2 | 1.03 | 0.96 | 0.98 |
| partit ×¼ | 0.80 | 0.91 | 0.93 |

## Els paràmetres triats (cada partit, amb els altres nou)

- A context: λ = 4, durada mínima 12 · A xarxes: w = 4, λ = 64, durada mínima 12 · A partit: w = 4, λ = 32, durada mínima 12 (1 partits)
- A context: λ = 4, durada mínima 12 · A xarxes: w = 4, λ = 32, durada mínima 12 · A partit: w = 4, λ = 32, durada mínima 12 (7 partits)
- A context: λ = 2, durada mínima 25 · A xarxes: w = 4, λ = 32, durada mínima 12 · A partit: w = 4, λ = 32, durada mínima 12 (1 partits)
- A context: λ = 4, durada mínima 12 · A xarxes: w = 4, λ = 32, durada mínima 1 · A partit: w = 4, λ = 32, durada mínima 12 (1 partits)
