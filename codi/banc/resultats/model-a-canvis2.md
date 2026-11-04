# Banc obert · Un segon classificador de canvis (T3j)

Generat amb `uv run python -I -m banc.model_a_canvis2`. Dades obertes: 7 partits de DFL (IDSSE, CC BY
4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3j», i la capçalera de `banc/model_a_canvis2.py`.

**A context** és el model de la cadena (T3e), amb el decodificador d'ara. **A canvis** són les
probabilitats d'A contacte amb el decodificador que cobra w · (−ln q) per canviar d'equip, amb la q
del classificador de canvis de la T3i. **A canvis 2** és el mateix amb la q d'un segon classificador
de canvis, que també mira la q del primer al voltant de cada imatge. Tots tenen els paràmetres del
decodificador triats amb els altres nou partits als escenaris ×¼, i els dos amb cost, amb la mateixa
graella.

## L'spellF1 i el macroF1 de cada mètode (mitjana dels deu partits)

**spellF1**

| escenari | A context | A canvis | A canvis 2 |
|---|---|---|---|
| net | 0.775 | 0.798 | 0.799 |
| curts ×¼ | 0.639 | 0.652 | 0.651 |
| llargs ×¼ | 0.621 | 0.638 | 0.639 |
| barreja ×¼ | 0.631 | 0.653 | 0.654 |
| aire ×¼ | 0.556 | 0.577 | 0.580 |
| curts | 0.583 | 0.591 | 0.593 |
| llargs | 0.547 | 0.557 | 0.558 |
| barreja | 0.562 | 0.572 | 0.572 |
| aire | 0.508 | 0.524 | 0.525 |
| soroll2 | 0.373 | 0.386 | 0.389 |

**macroF1**

| escenari | A context | A canvis | A canvis 2 |
|---|---|---|---|
| net | 0.952 | 0.951 | 0.951 |
| curts ×¼ | 0.919 | 0.919 | 0.919 |
| llargs ×¼ | 0.906 | 0.903 | 0.903 |
| barreja ×¼ | 0.910 | 0.909 | 0.909 |
| aire ×¼ | 0.886 | 0.887 | 0.888 |
| curts | 0.902 | 0.899 | 0.899 |
| llargs | 0.885 | 0.879 | 0.879 |
| barreja | 0.886 | 0.884 | 0.884 |
| aire | 0.865 | 0.865 | 0.865 |
| soroll2 | 0.697 | 0.689 | 0.690 |

## A canvis 2 contra A context (spellF1): el criteri

| escenari | A context | A canvis 2 | diferència | interval del 95 % | A canvis 2 guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.775 | 0.799 | +0.024 | +0.010 a +0.036 | 7 de 10 | no perd | ✓ |
| curts ×¼ | 0.639 | 0.651 | +0.012 | +0.000 a +0.023 | 8 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.621 | 0.639 | +0.017 | +0.005 a +0.029 | 7 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.631 | 0.654 | +0.023 | +0.013 a +0.032 | 9 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.556 | 0.580 | +0.023 | +0.010 a +0.037 | 7 de 10 | guanya clarament | ✗ |
| curts | 0.583 | 0.593 | +0.010 | +0.000 a +0.020 | 6 de 10 | no perd | ✓ |
| llargs | 0.547 | 0.558 | +0.011 | +0.002 a +0.022 | 7 de 10 | no perd | ✓ |
| barreja | 0.562 | 0.572 | +0.011 | +0.003 a +0.019 | 7 de 10 | no perd | ✓ |
| aire | 0.508 | 0.525 | +0.016 | +0.010 a +0.024 | 8 de 10 | no perd | ✓ |
| soroll2 | 0.373 | 0.389 | +0.016 | +0.008 a +0.024 | 8 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre escenaris ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1 i el soroll2 | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## A canvis 2 contra A canvis (spellF1), només per saber-ho

Les mateixes probabilitats d'equip i la mateixa graella: la diferència és el que afegeix el segon
classificador de canvis.

| escenari | A canvis | A canvis 2 | diferència | interval del 95 % | A canvis 2 guanya |
|---|---|---|---|---|---|
| net | 0.798 | 0.799 | +0.000 | -0.001 a +0.002 | 5 de 10 |
| curts ×¼ | 0.652 | 0.651 | -0.000 | -0.002 a +0.001 | 5 de 10 |
| llargs ×¼ | 0.638 | 0.639 | +0.000 | -0.001 a +0.001 | 6 de 10 |
| barreja ×¼ | 0.653 | 0.654 | +0.000 | -0.001 a +0.001 | 6 de 10 |
| aire ×¼ | 0.577 | 0.580 | +0.002 | +0.000 a +0.005 | 7 de 10 |
| curts | 0.591 | 0.593 | +0.002 | +0.000 a +0.004 | 7 de 10 |
| llargs | 0.557 | 0.558 | +0.001 | -0.002 a +0.004 | 7 de 10 |
| barreja | 0.572 | 0.572 | +0.000 | -0.002 a +0.002 | 5 de 10 |
| aire | 0.524 | 0.525 | +0.001 | -0.003 a +0.004 | 5 de 10 |
| soroll2 | 0.386 | 0.389 | +0.003 | +0.001 a +0.005 | 7 de 10 |

## Com és la q (escenaris ×¼, mitjana dels deu partits), només per saber-ho

L'AUC és contra l'objectiu (un canvi a 6 imatges o menys). «Canvis amb q alta» és la part dels canvis de la veritat amb la q a 0.3 o més a 6 imatges o menys.

| escenari | AUC, A canvis | AUC, A canvis 2 | canvis amb q alta, A canvis | canvis amb q alta, A canvis 2 |
|---|---|---|---|---|
| curts ×¼ | 0.937 | 0.939 | 0.446 | 0.456 |
| llargs ×¼ | 0.930 | 0.932 | 0.450 | 0.452 |
| barreja ×¼ | 0.934 | 0.937 | 0.450 | 0.456 |
| aire ×¼ | 0.904 | 0.904 | 0.408 | 0.399 |

## Possessions predites per cada real (mitjana dels deu partits), només per saber-ho

| escenari | A context | A canvis | A canvis 2 |
|---|---|---|---|
| net | 0.83 | 0.92 | 0.92 |
| curts ×¼ | 0.74 | 0.83 | 0.83 |
| llargs ×¼ | 0.73 | 0.81 | 0.80 |
| barreja ×¼ | 0.72 | 0.81 | 0.81 |
| aire ×¼ | 0.72 | 0.79 | 0.79 |
| curts | 0.72 | 0.81 | 0.81 |
| llargs | 0.68 | 0.77 | 0.77 |
| barreja | 0.70 | 0.78 | 0.79 |
| aire | 0.69 | 0.75 | 0.74 |
| soroll2 | 1.03 | 1.05 | 1.03 |

## Els paràmetres triats (cada partit, amb els altres nou)

- A context: λ = 4, durada mínima 12 · A canvis: w = 4, λ = 32, durada mínima 12 · A canvis 2: w = 4, λ = 32, durada mínima 12 (4 partits)
- A context: λ = 4, durada mínima 12 · A canvis: w = 4, λ = 32, durada mínima 1 · A canvis 2: w = 4, λ = 32, durada mínima 12 (3 partits)
- A context: λ = 2, durada mínima 25 · A canvis: w = 4, λ = 32, durada mínima 1 · A canvis 2: w = 4, λ = 32, durada mínima 12 (1 partits)
- A context: λ = 4, durada mínima 12 · A canvis: w = 4, λ = 32, durada mínima 1 · A canvis 2: w = 4, λ = 32, durada mínima 1 (1 partits)
- A context: λ = 4, durada mínima 12 · A canvis: w = 4, λ = 16, durada mínima 12 · A canvis 2: w = 4, λ = 16, durada mínima 12 (1 partits)
