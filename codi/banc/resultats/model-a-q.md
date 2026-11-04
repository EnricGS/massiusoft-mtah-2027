# Banc obert · La q veu el que veu el segon (T3r)

Generat amb `uv run python -I -m banc.model_a_q`. Dades obertes: 7 partits de DFL (IDSSE, CC BY 4.0) i
els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el criteri:
`docs/pla-tocs.md`, «T3r», i la capçalera de `banc/model_a_q.py`. Es puntua a la veritat de toc, llevat
d'on es diu.

**A xarxes** és el de la cadena, amb les peces de la memòria cau de la T3p (✓ comprovat: a cada punt de
la graella dona l'spellF1 del banc de la T3q). **A q** és el mateix, amb la q apresa amb la taula del
segon.

## A q contra A xarxes, decodificador de toc (spellF1): el criteri

| escenari | A xarxes, decodificador de toc | A q | diferència | interval del 95 % | A q guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.798 | 0.799 | +0.001 | -0.001 a +0.003 | 4 de 10 | no perd | ✓ |
| curts ×¼ | 0.673 | 0.676 | +0.003 | +0.000 a +0.006 | 7 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.651 | 0.653 | +0.002 | -0.002 a +0.005 | 6 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.660 | 0.662 | +0.002 | -0.003 a +0.006 | 8 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.600 | 0.601 | +0.001 | -0.004 a +0.005 | 5 de 10 | guanya clarament | ✗ |
| curts | 0.636 | 0.637 | +0.001 | -0.002 a +0.005 | 5 de 10 | no perd | ✓ |
| llargs | 0.599 | 0.601 | +0.002 | -0.001 a +0.005 | 5 de 10 | no perd | ✓ |
| barreja | 0.605 | 0.605 | -0.000 | -0.004 a +0.005 | 3 de 10 | no perd | ✓ |
| aire | 0.554 | 0.559 | +0.005 | +0.001 a +0.008 | 7 de 10 | no perd | ✓ |
| soroll2 | 0.470 | 0.472 | +0.001 | -0.002 a +0.006 | 6 de 10 | no perd | ✓ |
| partit ×¼ | 0.746 | 0.746 | +0.000 | -0.002 a +0.003 | 5 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1, el soroll2 i «partit ×¼» | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## No passa: és el millor fins ara?

| | És el millor fins ara si | |
|---|---|---|
| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | ✗ |
| «partit ×¼» | la diferència no és negativa | ✓ |
| El net, els ×1 i el soroll2 | no perd (diferència ≥ −0.04) | ✓ |

**A q no és el millor fins ara:** el pas següent es fa a sobre d'A xarxes.

## A q contra A xarxes, a la veritat de toc, només per saber-ho

| escenari | A xarxes | A q | diferència | interval del 95 % | A q guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.799 | +0.000 | -0.001 a +0.002 | 4 de 10 |
| curts ×¼ | 0.674 | 0.676 | +0.002 | -0.000 a +0.005 | 6 de 10 |
| llargs ×¼ | 0.652 | 0.653 | +0.002 | -0.002 a +0.005 | 6 de 10 |
| barreja ×¼ | 0.660 | 0.662 | +0.002 | -0.003 a +0.006 | 8 de 10 |
| aire ×¼ | 0.600 | 0.601 | +0.001 | -0.004 a +0.005 | 5 de 10 |
| curts | 0.636 | 0.637 | +0.001 | -0.002 a +0.004 | 5 de 10 |
| llargs | 0.599 | 0.601 | +0.002 | -0.001 a +0.005 | 5 de 10 |
| barreja | 0.605 | 0.605 | -0.000 | -0.004 a +0.005 | 3 de 10 |
| aire | 0.555 | 0.559 | +0.004 | +0.001 a +0.008 | 7 de 10 |
| soroll2 | 0.471 | 0.472 | +0.001 | -0.003 a +0.005 | 6 de 10 |
| partit ×¼ | 0.746 | 0.746 | +0.000 | -0.002 a +0.003 | 5 de 10 |

## A q contra A xarxes, decodificador de toc, a la veritat de sempre, només per saber-ho

| escenari | A xarxes, decodificador de toc | A q | diferència | interval del 95 % | A q guanya |
|---|---|---|---|---|---|
| net | 0.808 | 0.809 | +0.002 | -0.001 a +0.005 | 5 de 10 |
| curts ×¼ | 0.684 | 0.687 | +0.003 | +0.001 a +0.005 | 7 de 10 |
| llargs ×¼ | 0.662 | 0.664 | +0.002 | -0.002 a +0.005 | 6 de 10 |
| barreja ×¼ | 0.671 | 0.673 | +0.002 | -0.002 a +0.005 | 8 de 10 |
| aire ×¼ | 0.612 | 0.613 | +0.001 | -0.003 a +0.005 | 5 de 10 |
| curts | 0.644 | 0.646 | +0.003 | -0.002 a +0.006 | 8 de 10 |
| llargs | 0.607 | 0.608 | +0.001 | -0.002 a +0.004 | 5 de 10 |
| barreja | 0.616 | 0.616 | -0.001 | -0.004 a +0.003 | 4 de 10 |
| aire | 0.564 | 0.569 | +0.005 | +0.001 a +0.008 | 8 de 10 |
| soroll2 | 0.478 | 0.479 | +0.001 | -0.003 a +0.005 | 5 de 10 |
| partit ×¼ | 0.757 | 0.758 | +0.001 | -0.002 a +0.003 | 6 de 10 |

## A q contra A xarxes, decodificador de toc, només els partits de dfl

| escenari | A xarxes, decodificador de toc | A q | diferència | interval del 95 % | A q guanya |
|---|---|---|---|---|---|
| net | 0.766 | 0.766 | +0.000 | -0.002 a +0.002 | 3 de 7 |
| curts ×¼ | 0.642 | 0.647 | +0.005 | +0.001 a +0.008 | 5 de 7 |
| llargs ×¼ | 0.621 | 0.621 | +0.000 | -0.005 a +0.005 | 4 de 7 |
| barreja ×¼ | 0.630 | 0.632 | +0.002 | -0.004 a +0.008 | 6 de 7 |
| aire ×¼ | 0.544 | 0.546 | +0.001 | -0.005 a +0.007 | 4 de 7 |
| curts | 0.607 | 0.609 | +0.002 | -0.002 a +0.006 | 4 de 7 |
| llargs | 0.564 | 0.567 | +0.003 | -0.001 a +0.007 | 4 de 7 |
| barreja | 0.571 | 0.574 | +0.003 | -0.002 a +0.009 | 3 de 7 |
| aire | 0.501 | 0.506 | +0.005 | -0.000 a +0.009 | 4 de 7 |
| soroll2 | 0.433 | 0.436 | +0.003 | -0.003 a +0.009 | 5 de 7 |
| partit ×¼ | 0.717 | 0.718 | +0.001 | -0.002 a +0.004 | 4 de 7 |

## A q contra A xarxes, decodificador de toc, només els partits de metrica

| escenari | A xarxes, decodificador de toc | A q | diferència | interval del 95 % | A q guanya |
|---|---|---|---|---|---|
| net | 0.874 | 0.876 | +0.002 | -0.003 a +0.009 | 1 de 3 |
| curts ×¼ | 0.747 | 0.745 | -0.001 | -0.006 a +0.002 | 2 de 3 |
| llargs ×¼ | 0.723 | 0.728 | +0.005 | -0.001 a +0.011 | 2 de 3 |
| barreja ×¼ | 0.730 | 0.730 | +0.000 | -0.004 a +0.003 | 2 de 3 |
| aire ×¼ | 0.731 | 0.730 | -0.001 | -0.006 a +0.003 | 1 de 3 |
| curts | 0.702 | 0.703 | +0.001 | -0.005 a +0.007 | 1 de 3 |
| llargs | 0.682 | 0.681 | -0.001 | -0.003 a +0.002 | 1 de 3 |
| barreja | 0.684 | 0.677 | -0.007 | -0.010 a -0.005 | 0 de 3 |
| aire | 0.679 | 0.683 | +0.004 | +0.001 a +0.008 | 3 de 3 |
| soroll2 | 0.557 | 0.556 | -0.002 | -0.004 a +0.002 | 1 de 3 |
| partit ×¼ | 0.813 | 0.811 | -0.001 | -0.004 a +0.002 | 1 de 3 |

## Quants canvis troba cada q

Els canvis d'equip de la veritat de toc on la q arriba a 0.3 a 6 imatges o menys. Els
forats són les imatges sense pilota i les que en són a 6 o menys.

| escenari | on | canvis | A xarxes | A q |
|---|---|---|---|---|
| net | amb pilota | 3600 | 76 % | 76 % |
| net | als forats | 395 | 88 % | 90 % |
| curts ×¼ | amb pilota | 1343 | 68 % | 69 % |
| curts ×¼ | als forats | 2652 | 32 % | 38 % |
| llargs ×¼ | amb pilota | 1851 | 76 % | 76 % |
| llargs ×¼ | als forats | 2144 | 17 % | 20 % |
| barreja ×¼ | amb pilota | 1682 | 74 % | 74 % |
| barreja ×¼ | als forats | 2313 | 23 % | 26 % |
| aire ×¼ | amb pilota | 1742 | 64 % | 67 % |
| aire ×¼ | als forats | 2253 | 21 % | 24 % |
| curts | amb pilota | 1343 | 44 % | 46 % |
| curts | als forats | 2652 | 23 % | 30 % |
| llargs | amb pilota | 1851 | 48 % | 53 % |
| llargs | als forats | 2144 | 13 % | 17 % |
| barreja | amb pilota | 1682 | 46 % | 52 % |
| barreja | als forats | 2313 | 17 % | 21 % |
| aire | amb pilota | 1742 | 46 % | 54 % |
| aire | als forats | 2253 | 16 % | 20 % |
| soroll2 | amb pilota | 1698 | 57 % | 67 % |
| soroll2 | als forats | 2297 | 16 % | 20 % |
| partit ×¼ | amb pilota | 2768 | 72 % | 73 % |
| partit ×¼ | als forats | 1227 | 65 % | 66 % |

## L'spellF1 de cada mètode (mitjana dels deu partits)

**spellF1 a la veritat de toc**

| escenari | A xarxes | A xarxes, decodificador de toc | A q |
|---|---|---|---|
| net | 0.799 | 0.798 | 0.799 |
| curts ×¼ | 0.674 | 0.673 | 0.676 |
| llargs ×¼ | 0.652 | 0.651 | 0.653 |
| barreja ×¼ | 0.660 | 0.660 | 0.662 |
| aire ×¼ | 0.600 | 0.600 | 0.601 |
| curts | 0.636 | 0.636 | 0.637 |
| llargs | 0.599 | 0.599 | 0.601 |
| barreja | 0.605 | 0.605 | 0.605 |
| aire | 0.555 | 0.554 | 0.559 |
| soroll2 | 0.471 | 0.470 | 0.472 |
| partit ×¼ | 0.746 | 0.746 | 0.746 |

**spellF1 a la veritat de sempre**

| escenari | A xarxes | A xarxes, decodificador de toc | A q |
|---|---|---|---|
| net | 0.808 | 0.808 | 0.809 |
| curts ×¼ | 0.684 | 0.684 | 0.687 |
| llargs ×¼ | 0.662 | 0.662 | 0.664 |
| barreja ×¼ | 0.671 | 0.671 | 0.673 |
| aire ×¼ | 0.612 | 0.612 | 0.613 |
| curts | 0.644 | 0.644 | 0.646 |
| llargs | 0.607 | 0.607 | 0.608 |
| barreja | 0.616 | 0.616 | 0.616 |
| aire | 0.564 | 0.564 | 0.569 |
| soroll2 | 0.478 | 0.478 | 0.479 |
| partit ×¼ | 0.757 | 0.757 | 0.758 |

## Els decodificadors triats

- **A xarxes:** w = 4, λ = 64, durada mínima 12 (1 partits); w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 32, durada mínima 1 (1 partits)
- **A xarxes, decodificador de toc:** w = 4, λ = 64, durada mínima 1 (1 partits); w = 4, λ = 32, durada mínima 12 (6 partits); w = 4, λ = 32, durada mínima 1 (3 partits)
- **A q:** w = 4, λ = 32, durada mínima 12 (10 partits)
