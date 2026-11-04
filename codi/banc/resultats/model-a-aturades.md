# Banc obert · La pilota morta, amb senyals de l'aturada (T3k)

Generat amb `uv run python -I -m banc.model_a_aturades`. Dades obertes: 7 partits de DFL (IDSSE, CC BY
4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3k», i la capçalera de `banc/model_a_aturades.py`.

**A context** és el model de la cadena (T3e), amb el decodificador d'ara. **A canvis** són les
probabilitats d'A contacte amb el decodificador que cobra w · (−ln q) per canviar d'equip, amb la q
de la T3i. **A aturades** és el mateix amb el segon classificador d'A contacte amb els senyals de
l'aturada a més dels seus. Tots tenen els paràmetres del decodificador triats amb els altres nou partits
als escenaris ×¼, i els dos amb cost, amb la mateixa graella.

## L'spellF1 i el macroF1 de cada mètode (mitjana dels deu partits)

**spellF1**

| escenari | A context | A canvis | A aturades |
|---|---|---|---|
| net | 0.775 | 0.798 | 0.801 |
| curts ×¼ | 0.639 | 0.652 | 0.659 |
| llargs ×¼ | 0.621 | 0.638 | 0.648 |
| barreja ×¼ | 0.631 | 0.653 | 0.661 |
| aire ×¼ | 0.556 | 0.577 | 0.585 |
| curts | 0.583 | 0.591 | 0.601 |
| llargs | 0.547 | 0.557 | 0.568 |
| barreja | 0.562 | 0.572 | 0.579 |
| aire | 0.508 | 0.524 | 0.526 |
| soroll2 | 0.373 | 0.386 | 0.388 |

**macroF1**

| escenari | A context | A canvis | A aturades |
|---|---|---|---|
| net | 0.952 | 0.951 | 0.953 |
| curts ×¼ | 0.919 | 0.919 | 0.921 |
| llargs ×¼ | 0.906 | 0.903 | 0.906 |
| barreja ×¼ | 0.910 | 0.909 | 0.912 |
| aire ×¼ | 0.886 | 0.887 | 0.890 |
| curts | 0.902 | 0.899 | 0.901 |
| llargs | 0.885 | 0.879 | 0.882 |
| barreja | 0.886 | 0.884 | 0.888 |
| aire | 0.865 | 0.865 | 0.868 |
| soroll2 | 0.697 | 0.689 | 0.694 |

## A aturades contra A context (spellF1): el criteri

| escenari | A context | A aturades | diferència | interval del 95 % | A aturades guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.775 | 0.801 | +0.027 | +0.014 a +0.039 | 8 de 10 | no perd | ✓ |
| curts ×¼ | 0.639 | 0.659 | +0.019 | +0.006 a +0.031 | 8 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.621 | 0.648 | +0.026 | +0.014 a +0.039 | 8 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.631 | 0.661 | +0.030 | +0.019 a +0.039 | 9 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.556 | 0.585 | +0.029 | +0.017 a +0.043 | 10 de 10 | guanya clarament | ✗ |
| curts | 0.583 | 0.601 | +0.018 | +0.009 a +0.027 | 9 de 10 | no perd | ✓ |
| llargs | 0.547 | 0.568 | +0.020 | +0.011 a +0.031 | 9 de 10 | no perd | ✓ |
| barreja | 0.562 | 0.579 | +0.018 | +0.007 a +0.029 | 8 de 10 | no perd | ✓ |
| aire | 0.508 | 0.526 | +0.018 | +0.010 a +0.026 | 10 de 10 | no perd | ✓ |
| soroll2 | 0.373 | 0.388 | +0.015 | +0.006 a +0.023 | 8 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre escenaris ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1 i el soroll2 | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## A aturades contra A canvis (spellF1), només per saber-ho

La mateixa q i la mateixa graella: la diferència és el que afegeixen els senyals de l'aturada.

| escenari | A canvis | A aturades | diferència | interval del 95 % | A aturades guanya |
|---|---|---|---|---|---|
| net | 0.798 | 0.801 | +0.003 | +0.000 a +0.006 | 6 de 10 |
| curts ×¼ | 0.652 | 0.659 | +0.007 | +0.002 a +0.012 | 7 de 10 |
| llargs ×¼ | 0.638 | 0.648 | +0.009 | +0.004 a +0.015 | 9 de 10 |
| barreja ×¼ | 0.653 | 0.661 | +0.007 | +0.002 a +0.011 | 9 de 10 |
| aire ×¼ | 0.577 | 0.585 | +0.008 | +0.001 a +0.016 | 8 de 10 |
| curts | 0.591 | 0.601 | +0.010 | +0.005 a +0.016 | 8 de 10 |
| llargs | 0.557 | 0.568 | +0.011 | +0.007 a +0.014 | 9 de 10 |
| barreja | 0.572 | 0.579 | +0.007 | +0.002 a +0.011 | 7 de 10 |
| aire | 0.524 | 0.526 | +0.002 | -0.004 a +0.008 | 6 de 10 |
| soroll2 | 0.386 | 0.388 | +0.002 | -0.005 a +0.008 | 6 de 10 |

## Les vores de les aturades (escenaris ×¼, totes les dels deu partits), només per saber-ho

*Trobades*: la part de les aturades de la veritat amb alguna imatge de D predita. *Inici* i *represa*: de les trobades, la part amb la vora errada per més de 0.5 s.

| escenari | mètode | trobades | inici | represa |
|---|---|---|---|---|
| curts ×¼ | A canvis | 0.950 | 0.325 | 0.160 |
| curts ×¼ | A aturades | 0.952 | 0.300 | 0.149 |
| llargs ×¼ | A canvis | 0.923 | 0.378 | 0.257 |
| llargs ×¼ | A aturades | 0.921 | 0.346 | 0.233 |
| barreja ×¼ | A canvis | 0.924 | 0.377 | 0.222 |
| barreja ×¼ | A aturades | 0.926 | 0.345 | 0.197 |
| aire ×¼ | A canvis | 0.931 | 0.416 | 0.265 |
| aire ×¼ | A aturades | 0.940 | 0.405 | 0.271 |

## Possessions predites per cada real (mitjana dels deu partits), només per saber-ho

| escenari | A context | A canvis | A aturades |
|---|---|---|---|
| net | 0.83 | 0.92 | 0.92 |
| curts ×¼ | 0.74 | 0.83 | 0.83 |
| llargs ×¼ | 0.73 | 0.81 | 0.81 |
| barreja ×¼ | 0.72 | 0.81 | 0.81 |
| aire ×¼ | 0.72 | 0.79 | 0.79 |
| curts | 0.72 | 0.81 | 0.82 |
| llargs | 0.68 | 0.77 | 0.77 |
| barreja | 0.70 | 0.78 | 0.79 |
| aire | 0.69 | 0.75 | 0.75 |
| soroll2 | 1.03 | 1.05 | 1.07 |

## Els paràmetres triats (cada partit, amb els altres nou)

- A context: λ = 4, durada mínima 12 · A canvis: w = 4, λ = 32, durada mínima 12 · A aturades: w = 4, λ = 32, durada mínima 12 (4 partits)
- A context: λ = 4, durada mínima 12 · A canvis: w = 4, λ = 32, durada mínima 1 · A aturades: w = 4, λ = 32, durada mínima 12 (3 partits)
- A context: λ = 2, durada mínima 25 · A canvis: w = 4, λ = 32, durada mínima 1 · A aturades: w = 4, λ = 32, durada mínima 12 (1 partits)
- A context: λ = 4, durada mínima 12 · A canvis: w = 4, λ = 32, durada mínima 1 · A aturades: w = 4, λ = 16, durada mínima 12 (1 partits)
- A context: λ = 4, durada mínima 12 · A canvis: w = 4, λ = 16, durada mínima 12 · A aturades: w = 4, λ = 32, durada mínima 12 (1 partits)
