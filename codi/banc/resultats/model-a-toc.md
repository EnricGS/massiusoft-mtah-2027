# Banc obert · La veritat del banc, al primer toc (T3q)

Generat amb `uv run python -I -m banc.model_a_toc`. Dades obertes: 7 partits de DFL (IDSSE, CC BY 4.0)
i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el criteri:
`docs/pla-tocs.md`, «T3q», i la capçalera de `banc/model_a_toc.py`. La veritat de toc:
`resultats/veritat-toc.md`.

## Pas 1: A xarxes tal com és, a la veritat de toc

El decodificador és el de la cadena, el mateix que va triar la T3p a cada partit (✓ comprovat).

| escenari | a la de sempre | a la veritat de toc | diferència | interval del 95 % | a la veritat de toc guanya |
|---|---|---|---|---|---|
| net | 0.808 | 0.799 | -0.010 | -0.017 a -0.000 | 1 de 10 |
| curts ×¼ | 0.684 | 0.674 | -0.011 | -0.016 a -0.004 | 1 de 10 |
| llargs ×¼ | 0.662 | 0.652 | -0.010 | -0.012 a -0.008 | 0 de 10 |
| barreja ×¼ | 0.671 | 0.660 | -0.011 | -0.017 a -0.005 | 1 de 10 |
| aire ×¼ | 0.612 | 0.600 | -0.011 | -0.015 a -0.008 | 0 de 10 |
| curts | 0.644 | 0.636 | -0.008 | -0.014 a -0.002 | 2 de 10 |
| llargs | 0.607 | 0.599 | -0.007 | -0.010 a -0.005 | 0 de 10 |
| barreja | 0.616 | 0.605 | -0.011 | -0.016 a -0.007 | 1 de 10 |
| aire | 0.564 | 0.555 | -0.009 | -0.013 a -0.006 | 0 de 10 |
| soroll2 | 0.478 | 0.471 | -0.007 | -0.009 a -0.006 | 0 de 10 |
| partit ×¼ | 0.757 | 0.746 | -0.012 | -0.019 a -0.004 | 1 de 10 |

Als quatre ×¼ hi perd +0.011 de mitjana. És 0.01 o més: el Pas 2 s'entrena.

## A toc contra A xarxes, a la veritat de toc (spellF1): el criteri

| escenari | A xarxes | A toc | diferència | interval del 95 % | A toc guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.799 | 0.795 | -0.004 | -0.008 a +0.001 | 4 de 10 | no perd | ✓ |
| curts ×¼ | 0.674 | 0.675 | +0.001 | -0.005 a +0.007 | 4 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.652 | 0.650 | -0.002 | -0.006 a +0.002 | 6 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.660 | 0.657 | -0.003 | -0.008 a +0.001 | 4 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.600 | 0.596 | -0.005 | -0.012 a +0.003 | 4 de 10 | guanya clarament | ✗ |
| curts | 0.636 | 0.636 | -0.000 | -0.007 a +0.006 | 5 de 10 | no perd | ✓ |
| llargs | 0.599 | 0.595 | -0.005 | -0.011 a +0.001 | 4 de 10 | no perd | ✓ |
| barreja | 0.605 | 0.601 | -0.004 | -0.011 a +0.003 | 4 de 10 | no perd | ✓ |
| aire | 0.555 | 0.561 | +0.006 | -0.000 a +0.012 | 8 de 10 | no perd | ✓ |
| soroll2 | 0.471 | 0.471 | +0.000 | -0.005 a +0.007 | 3 de 10 | no perd | ✓ |
| partit ×¼ | 0.746 | 0.738 | -0.007 | -0.012 a -0.003 | 3 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1, el soroll2 i «partit ×¼» | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## A toc contra A xarxes, a la veritat de sempre, només per saber-ho

| escenari | A xarxes | A toc | diferència | interval del 95 % | A toc guanya |
|---|---|---|---|---|---|
| net | 0.808 | 0.805 | -0.003 | -0.007 a +0.001 | 2 de 10 |
| curts ×¼ | 0.684 | 0.683 | -0.002 | -0.006 a +0.003 | 4 de 10 |
| llargs ×¼ | 0.662 | 0.659 | -0.003 | -0.007 a +0.001 | 5 de 10 |
| barreja ×¼ | 0.671 | 0.666 | -0.005 | -0.011 a +0.001 | 4 de 10 |
| aire ×¼ | 0.612 | 0.605 | -0.007 | -0.014 a +0.000 | 3 de 10 |
| curts | 0.644 | 0.644 | +0.000 | -0.007 a +0.007 | 6 de 10 |
| llargs | 0.607 | 0.602 | -0.005 | -0.013 a +0.002 | 4 de 10 |
| barreja | 0.616 | 0.610 | -0.007 | -0.015 a +0.001 | 4 de 10 |
| aire | 0.564 | 0.570 | +0.006 | -0.001 a +0.012 | 8 de 10 |
| soroll2 | 0.478 | 0.477 | -0.001 | -0.007 a +0.006 | 3 de 10 |
| partit ×¼ | 0.757 | 0.748 | -0.009 | -0.015 a -0.004 | 2 de 10 |

## A xarxes, decodificador de toc contra A xarxes, a la veritat de toc, només per saber-ho

| escenari | A xarxes | A xarxes, decodificador de toc | diferència | interval del 95 % | A xarxes, decodificador de toc guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.798 | -0.001 | -0.001 a +0.000 | 0 de 10 |
| curts ×¼ | 0.674 | 0.673 | -0.000 | -0.001 a +0.000 | 0 de 10 |
| llargs ×¼ | 0.652 | 0.651 | -0.000 | -0.000 a +0.000 | 1 de 10 |
| barreja ×¼ | 0.660 | 0.660 | +0.000 | -0.000 a +0.000 | 1 de 10 |
| aire ×¼ | 0.600 | 0.600 | -0.000 | -0.000 a +0.000 | 1 de 10 |
| curts | 0.636 | 0.636 | -0.000 | -0.000 a +0.000 | 0 de 10 |
| llargs | 0.599 | 0.599 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| barreja | 0.605 | 0.605 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| aire | 0.555 | 0.554 | -0.000 | -0.000 a +0.000 | 0 de 10 |
| soroll2 | 0.471 | 0.470 | -0.000 | -0.000 a +0.000 | 0 de 10 |
| partit ×¼ | 0.746 | 0.746 | +0.000 | -0.000 a +0.000 | 1 de 10 |

## A toc contra A xarxes, decodificador de toc, a la veritat de toc, només per saber-ho

| escenari | A xarxes, decodificador de toc | A toc | diferència | interval del 95 % | A toc guanya |
|---|---|---|---|---|---|
| net | 0.798 | 0.795 | -0.003 | -0.008 a +0.001 | 4 de 10 |
| curts ×¼ | 0.673 | 0.675 | +0.001 | -0.005 a +0.007 | 4 de 10 |
| llargs ×¼ | 0.651 | 0.650 | -0.002 | -0.005 a +0.002 | 6 de 10 |
| barreja ×¼ | 0.660 | 0.657 | -0.004 | -0.008 a +0.001 | 4 de 10 |
| aire ×¼ | 0.600 | 0.596 | -0.005 | -0.012 a +0.003 | 4 de 10 |
| curts | 0.636 | 0.636 | -0.000 | -0.007 a +0.006 | 5 de 10 |
| llargs | 0.599 | 0.595 | -0.005 | -0.011 a +0.001 | 4 de 10 |
| barreja | 0.605 | 0.601 | -0.004 | -0.011 a +0.003 | 4 de 10 |
| aire | 0.554 | 0.561 | +0.006 | -0.000 a +0.012 | 8 de 10 |
| soroll2 | 0.470 | 0.471 | +0.001 | -0.005 a +0.007 | 3 de 10 |
| partit ×¼ | 0.746 | 0.738 | -0.008 | -0.012 a -0.003 | 3 de 10 |

## L'spellF1 de cada mètode (mitjana dels deu partits)

**spellF1 a la veritat de toc**

| escenari | A xarxes | A xarxes, decodificador de toc | A toc |
|---|---|---|---|
| net | 0.799 | 0.798 | 0.795 |
| curts ×¼ | 0.674 | 0.673 | 0.675 |
| llargs ×¼ | 0.652 | 0.651 | 0.650 |
| barreja ×¼ | 0.660 | 0.660 | 0.657 |
| aire ×¼ | 0.600 | 0.600 | 0.596 |
| curts | 0.636 | 0.636 | 0.636 |
| llargs | 0.599 | 0.599 | 0.595 |
| barreja | 0.605 | 0.605 | 0.601 |
| aire | 0.555 | 0.554 | 0.561 |
| soroll2 | 0.471 | 0.470 | 0.471 |
| partit ×¼ | 0.746 | 0.746 | 0.738 |

**spellF1 a la veritat de sempre**

| escenari | A xarxes | A xarxes, decodificador de toc | A toc |
|---|---|---|---|
| net | 0.808 | 0.808 | 0.805 |
| curts ×¼ | 0.684 | 0.684 | 0.683 |
| llargs ×¼ | 0.662 | 0.662 | 0.659 |
| barreja ×¼ | 0.671 | 0.671 | 0.666 |
| aire ×¼ | 0.612 | 0.612 | 0.605 |
| curts | 0.644 | 0.644 | 0.644 |
| llargs | 0.607 | 0.607 | 0.602 |
| barreja | 0.616 | 0.616 | 0.610 |
| aire | 0.564 | 0.564 | 0.570 |
| soroll2 | 0.478 | 0.478 | 0.477 |
| partit ×¼ | 0.757 | 0.757 | 0.748 |

## Els decodificadors triats

- **A xarxes:** w = 4, λ = 64, durada mínima 12 (1 partits); w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 32, durada mínima 1 (1 partits)
- **A xarxes, decodificador de toc:** w = 4, λ = 64, durada mínima 1 (1 partits); w = 4, λ = 32, durada mínima 12 (6 partits); w = 4, λ = 32, durada mínima 1 (3 partits)
- **A toc:** w = 4, λ = 32, durada mínima 12 (9 partits); w = 4, λ = 16, durada mínima 12 (1 partits)
