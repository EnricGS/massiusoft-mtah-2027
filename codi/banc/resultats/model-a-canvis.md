# Banc obert · El cost de canviar d'equip, après (T3i)

Generat amb `uv run python -I -m banc.model_a_canvis`. Dades obertes: 7 partits de DFL (IDSSE, CC BY
4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3i», i la capçalera de `banc/model_a_canvis.py`.

**A context** és el model de la cadena (T3e), i **A contacte**, el de la T3h, tots dos amb el
decodificador d'ara. **A canvis** són les probabilitats d'A contacte amb el decodificador que cobra
w · (−ln q) per canviar d'equip, amb q la probabilitat d'un canvi a 6 imatges o menys, d'un classificador
de canvis. **A context amb el cost après** és el mateix amb les probabilitats d'A context. Tots tenen els
paràmetres del decodificador triats amb els altres nou partits als escenaris ×¼.

## L'spellF1 i el macroF1 de cada mètode (mitjana dels deu partits)

**spellF1**

| escenari | A context | A contacte | A context amb el cost après | A canvis |
|---|---|---|---|---|
| net | 0.775 | 0.789 | 0.782 | 0.798 |
| curts ×¼ | 0.639 | 0.647 | 0.644 | 0.652 |
| llargs ×¼ | 0.621 | 0.633 | 0.627 | 0.639 |
| barreja ×¼ | 0.631 | 0.644 | 0.639 | 0.653 |
| aire ×¼ | 0.556 | 0.575 | 0.563 | 0.577 |
| curts | 0.583 | 0.589 | 0.586 | 0.591 |
| llargs | 0.547 | 0.555 | 0.550 | 0.558 |
| barreja | 0.562 | 0.565 | 0.566 | 0.572 |
| aire | 0.508 | 0.520 | 0.511 | 0.522 |
| soroll2 | 0.373 | 0.384 | 0.377 | 0.384 |

**macroF1**

| escenari | A context | A contacte | A context amb el cost après | A canvis |
|---|---|---|---|---|
| net | 0.952 | 0.950 | 0.953 | 0.952 |
| curts ×¼ | 0.919 | 0.918 | 0.919 | 0.918 |
| llargs ×¼ | 0.906 | 0.903 | 0.906 | 0.903 |
| barreja ×¼ | 0.910 | 0.908 | 0.911 | 0.909 |
| aire ×¼ | 0.886 | 0.887 | 0.886 | 0.887 |
| curts | 0.902 | 0.899 | 0.903 | 0.899 |
| llargs | 0.885 | 0.879 | 0.885 | 0.880 |
| barreja | 0.886 | 0.884 | 0.887 | 0.885 |
| aire | 0.865 | 0.864 | 0.866 | 0.864 |
| soroll2 | 0.697 | 0.694 | 0.695 | 0.692 |

## A canvis contra A context (spellF1): el criteri

| escenari | A context | A canvis | diferència | interval del 95 % | A canvis guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.775 | 0.798 | +0.024 | +0.011 a +0.035 | 7 de 10 | no perd | ✓ |
| curts ×¼ | 0.639 | 0.652 | +0.012 | +0.001 a +0.023 | 8 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.621 | 0.639 | +0.017 | +0.006 a +0.029 | 8 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.631 | 0.653 | +0.023 | +0.011 a +0.033 | 9 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.556 | 0.577 | +0.021 | +0.008 a +0.035 | 7 de 10 | guanya clarament | ✗ |
| curts | 0.583 | 0.591 | +0.008 | -0.002 a +0.019 | 6 de 10 | no perd | ✓ |
| llargs | 0.547 | 0.558 | +0.010 | +0.002 a +0.021 | 8 de 10 | no perd | ✓ |
| barreja | 0.562 | 0.572 | +0.010 | +0.003 a +0.018 | 7 de 10 | no perd | ✓ |
| aire | 0.508 | 0.522 | +0.014 | +0.007 a +0.021 | 9 de 10 | no perd | ✓ |
| soroll2 | 0.373 | 0.384 | +0.011 | +0.005 a +0.017 | 8 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre escenaris ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1 i el soroll2 | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## A canvis contra A contacte (spellF1), només per saber-ho

Les mateixes probabilitats d'equip: la diferència és el que afegeix el decodificador.

| escenari | A contacte | A canvis | diferència | interval del 95 % | A canvis guanya |
|---|---|---|---|---|---|
| net | 0.789 | 0.798 | +0.010 | +0.006 a +0.013 | 10 de 10 |
| curts ×¼ | 0.647 | 0.652 | +0.004 | +0.001 a +0.008 | 8 de 10 |
| llargs ×¼ | 0.633 | 0.639 | +0.006 | +0.001 a +0.010 | 9 de 10 |
| barreja ×¼ | 0.644 | 0.653 | +0.009 | +0.005 a +0.013 | 10 de 10 |
| aire ×¼ | 0.575 | 0.577 | +0.003 | -0.002 a +0.007 | 6 de 10 |
| curts | 0.589 | 0.591 | +0.003 | -0.001 a +0.006 | 6 de 10 |
| llargs | 0.555 | 0.558 | +0.003 | -0.001 a +0.006 | 8 de 10 |
| barreja | 0.565 | 0.572 | +0.007 | +0.002 a +0.010 | 9 de 10 |
| aire | 0.520 | 0.522 | +0.002 | -0.001 a +0.004 | 6 de 10 |
| soroll2 | 0.384 | 0.384 | -0.000 | -0.004 a +0.004 | 5 de 10 |

## A context amb el cost après contra A context (spellF1), només per saber-ho

El decodificador sol, sobre el model de la cadena.

| escenari | A context | A context amb el cost après | diferència | interval del 95 % | A context amb el cost après guanya |
|---|---|---|---|---|---|
| net | 0.775 | 0.782 | +0.008 | +0.004 a +0.011 | 9 de 10 |
| curts ×¼ | 0.639 | 0.644 | +0.005 | +0.002 a +0.008 | 8 de 10 |
| llargs ×¼ | 0.621 | 0.627 | +0.006 | +0.002 a +0.010 | 8 de 10 |
| barreja ×¼ | 0.631 | 0.639 | +0.008 | +0.003 a +0.013 | 9 de 10 |
| aire ×¼ | 0.556 | 0.563 | +0.006 | +0.001 a +0.012 | 7 de 10 |
| curts | 0.583 | 0.586 | +0.003 | -0.000 a +0.007 | 8 de 10 |
| llargs | 0.547 | 0.550 | +0.002 | -0.000 a +0.005 | 6 de 10 |
| barreja | 0.562 | 0.566 | +0.004 | +0.001 a +0.007 | 9 de 10 |
| aire | 0.508 | 0.511 | +0.003 | -0.000 a +0.006 | 8 de 10 |
| soroll2 | 0.373 | 0.377 | +0.004 | +0.002 a +0.006 | 8 de 10 |

## Possessions predites per cada real (mitjana dels deu partits), només per saber-ho

| escenari | A context | A contacte | A context amb el cost après | A canvis |
|---|---|---|---|---|
| net | 0.83 | 0.91 | 0.84 | 0.92 |
| curts ×¼ | 0.74 | 0.82 | 0.74 | 0.83 |
| llargs ×¼ | 0.73 | 0.81 | 0.73 | 0.81 |
| barreja ×¼ | 0.72 | 0.80 | 0.72 | 0.81 |
| aire ×¼ | 0.72 | 0.79 | 0.70 | 0.80 |
| curts | 0.72 | 0.80 | 0.71 | 0.81 |
| llargs | 0.68 | 0.77 | 0.67 | 0.78 |
| barreja | 0.70 | 0.78 | 0.69 | 0.79 |
| aire | 0.69 | 0.76 | 0.66 | 0.76 |
| soroll2 | 1.03 | 1.07 | 0.98 | 1.09 |

## Els paràmetres triats (cada partit, amb els altres nou)

- A context: λ = 4, durada mínima 12 · A contacte: λ = 8, durada mínima 1 · A context amb el cost après: w = 2, λ = 16, durada mínima 12 · A canvis: w = 4, λ = 16, durada mínima 12 (4 partits)
- A context: λ = 4, durada mínima 12 · A contacte: λ = 8, durada mínima 12 · A context amb el cost après: w = 2, λ = 16, durada mínima 12 · A canvis: w = 4, λ = 16, durada mínima 12 (1 partits)
- A context: λ = 4, durada mínima 12 · A contacte: λ = 8, durada mínima 1 · A context amb el cost après: w = 2, λ = 16, durada mínima 12 · A canvis: w = 4, λ = 16, durada mínima 1 (3 partits)
- A context: λ = 2, durada mínima 25 · A contacte: λ = 8, durada mínima 1 · A context amb el cost après: w = 2, λ = 16, durada mínima 12 · A canvis: w = 4, λ = 16, durada mínima 12 (1 partits)
- A context: λ = 4, durada mínima 12 · A contacte: λ = 8, durada mínima 12 · A context amb el cost après: w = 1, λ = 16, durada mínima 12 · A canvis: w = 4, λ = 16, durada mínima 12 (1 partits)
