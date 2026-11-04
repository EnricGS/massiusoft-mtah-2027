# Banc obert · La pilota morta d'abans de la represa, més llarga i més forta (T3ah)

Generat amb `uv run python -I -m banc.model_pilota_morta`. Dades obertes: 7 partits de DFL (IDSSE,
CC BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3ah», i la capçalera de `banc/model_pilota_morta.py`. Es puntua a la
veritat de toc.

**A xarxes, decodificador de toc** i **A equips sencers** són els de la T3v, **A pilota creïble**, el de la T3w, i **A neteja d'aire**,
el de la T3ac, amb les peces de la memòria cau (✓ comprovat). **A pilota morta** és A neteja d'aire amb
el seu decodificador, i abans de decodificar, el que les etiquetes simulades sumen a la D. ✓ Comprovat:
no dona mai la D a una imatge netejada, sense etiquetes dona exactament A neteja d'aire, i els punts de
la T3ag donen el mateix que a la graella de la T3ag.

## Amb el nivell mitjà: A pilota morta contra A xarxes, decodificador de toc (spellF1), el criteri

| escenari | A xarxes, decodificador de toc | A pilota morta | diferència | interval del 95 % | A pilota morta guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.798 | 0.801 | +0.003 | -0.002 a +0.009 | 6 de 10 | no perd | ✓ |
| curts ×¼ | 0.673 | 0.702 | +0.029 | +0.023 a +0.035 | 10 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.651 | 0.691 | +0.040 | +0.031 a +0.049 | 10 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.660 | 0.698 | +0.038 | +0.032 a +0.044 | 10 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.600 | 0.647 | +0.047 | +0.040 a +0.054 | 10 de 10 | guanya clarament | ✓ |
| curts | 0.636 | 0.668 | +0.032 | +0.027 a +0.038 | 10 de 10 | no perd | ✓ |
| llargs | 0.599 | 0.645 | +0.045 | +0.032 a +0.058 | 10 de 10 | no perd | ✓ |
| barreja | 0.605 | 0.650 | +0.045 | +0.034 a +0.055 | 10 de 10 | no perd | ✓ |
| aire | 0.554 | 0.620 | +0.065 | +0.059 a +0.071 | 10 de 10 | no perd | ✓ |
| soroll2 | 0.470 | 0.549 | +0.079 | +0.072 a +0.085 | 10 de 10 | no perd | ✓ |
| partit ×¼ | 0.746 | 0.764 | +0.019 | +0.012 a +0.026 | 10 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1, el soroll2 i «partit ×¼» | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## Amb els nivells dolent i cap: A pilota morta contra A neteja d'aire, la segona part del criteri

| Nivell | curts ×¼ | llargs ×¼ | barreja ×¼ | aire ×¼ | partit ×¼ | No baixa de −0.005 |
|---|---|---|---|---|---|---|
| dolent | +0.0026 | +0.0035 | +0.0008 | +0.0035 | +0.0014 | ✓ |
| cap | +0.0000 | +0.0000 | +0.0000 | +0.0000 | +0.0000 | ✓ |

**A pilota morta no passa el criteri sencer.**

## Amb el nivell bo: A pilota morta contra A neteja d'aire (spellF1)

| escenari | A neteja d'aire | A pilota morta | diferència | interval del 95 % | A pilota morta guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.802 | +0.003 | +0.001 a +0.004 | 8 de 10 |
| curts ×¼ | 0.699 | 0.703 | +0.004 | +0.001 a +0.007 | 8 de 10 |
| llargs ×¼ | 0.688 | 0.694 | +0.006 | +0.005 a +0.008 | 10 de 10 |
| barreja ×¼ | 0.696 | 0.699 | +0.002 | +0.000 a +0.004 | 7 de 10 |
| aire ×¼ | 0.644 | 0.649 | +0.005 | +0.003 a +0.007 | 9 de 10 |
| curts | 0.665 | 0.669 | +0.004 | +0.001 a +0.006 | 8 de 10 |
| llargs | 0.640 | 0.645 | +0.004 | +0.001 a +0.008 | 8 de 10 |
| barreja | 0.646 | 0.650 | +0.004 | +0.000 a +0.008 | 6 de 10 |
| aire | 0.618 | 0.622 | +0.005 | +0.001 a +0.008 | 7 de 10 |
| soroll2 | 0.534 | 0.554 | +0.020 | +0.016 a +0.024 | 10 de 10 |
| partit ×¼ | 0.761 | 0.765 | +0.004 | +0.003 a +0.005 | 9 de 10 |

## Amb el nivell mitjà: A pilota morta contra A neteja d'aire (spellF1)

| escenari | A neteja d'aire | A pilota morta | diferència | interval del 95 % | A pilota morta guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.801 | +0.002 | +0.000 a +0.003 | 7 de 10 |
| curts ×¼ | 0.699 | 0.702 | +0.003 | +0.001 a +0.005 | 7 de 10 |
| llargs ×¼ | 0.688 | 0.691 | +0.003 | +0.002 a +0.005 | 9 de 10 |
| barreja ×¼ | 0.696 | 0.698 | +0.002 | +0.000 a +0.003 | 8 de 10 |
| aire ×¼ | 0.644 | 0.647 | +0.003 | +0.000 a +0.005 | 7 de 10 |
| curts | 0.665 | 0.668 | +0.003 | +0.001 a +0.005 | 9 de 10 |
| llargs | 0.640 | 0.645 | +0.004 | +0.002 a +0.007 | 8 de 10 |
| barreja | 0.646 | 0.650 | +0.004 | +0.002 a +0.007 | 7 de 10 |
| aire | 0.618 | 0.620 | +0.002 | -0.001 a +0.006 | 6 de 10 |
| soroll2 | 0.534 | 0.549 | +0.015 | +0.012 a +0.019 | 10 de 10 |
| partit ×¼ | 0.761 | 0.764 | +0.003 | +0.002 a +0.005 | 9 de 10 |

## Amb el nivell dolent: A pilota morta contra A neteja d'aire (spellF1)

| escenari | A neteja d'aire | A pilota morta | diferència | interval del 95 % | A pilota morta guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.801 | +0.001 | +0.001 a +0.002 | 7 de 10 |
| curts ×¼ | 0.699 | 0.702 | +0.003 | +0.002 a +0.004 | 10 de 10 |
| llargs ×¼ | 0.688 | 0.692 | +0.003 | +0.001 a +0.005 | 8 de 10 |
| barreja ×¼ | 0.696 | 0.697 | +0.001 | -0.001 a +0.002 | 6 de 10 |
| aire ×¼ | 0.644 | 0.648 | +0.004 | +0.001 a +0.006 | 8 de 10 |
| curts | 0.665 | 0.668 | +0.003 | +0.002 a +0.004 | 10 de 10 |
| llargs | 0.640 | 0.644 | +0.003 | +0.001 a +0.006 | 9 de 10 |
| barreja | 0.646 | 0.648 | +0.001 | -0.002 a +0.005 | 7 de 10 |
| aire | 0.618 | 0.618 | +0.001 | -0.003 a +0.005 | 7 de 10 |
| soroll2 | 0.534 | 0.547 | +0.013 | +0.010 a +0.017 | 10 de 10 |
| partit ×¼ | 0.761 | 0.763 | +0.001 | +0.000 a +0.002 | 9 de 10 |

## Amb el nivell cap: A pilota morta contra A neteja d'aire (spellF1)

| escenari | A neteja d'aire | A pilota morta | diferència | interval del 95 % | A pilota morta guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.799 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| curts ×¼ | 0.699 | 0.699 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| llargs ×¼ | 0.688 | 0.688 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| barreja ×¼ | 0.696 | 0.696 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| aire ×¼ | 0.644 | 0.644 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| curts | 0.665 | 0.665 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| llargs | 0.640 | 0.640 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| barreja | 0.646 | 0.646 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| aire | 0.618 | 0.618 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| soroll2 | 0.534 | 0.534 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| partit ×¼ | 0.761 | 0.761 | +0.000 | +0.000 a +0.000 | 0 de 10 |

## No passa: és el millor fins ara?

La regla de la D-50, escrita abans, contra A neteja d'aire amb el nivell mitjà, i la mateixa
segona part del criteri:

| | És el millor fins ara si | |
|---|---|---|
| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | ✓ |
| «partit ×¼» | la diferència no és negativa | ✓ |
| El net, els ×1 i el soroll2 | no perd (diferència ≥ −0.04) | ✓ |
| Dolent i cap | la segona part del criteri | ✓ |

**A pilota morta és el millor fins ara:** el pas següent es fa a sobre d'A pilota morta.

## Amb el nivell bo: A pilota morta contra A etiquetes al decodificador, la T3ag (spellF1)

| escenari | A etiquetes al decodificador | A pilota morta | diferència | interval del 95 % | A pilota morta guanya |
|---|---|---|---|---|---|
| net | 0.801 | 0.802 | +0.001 | -0.000 a +0.002 | 7 de 10 |
| curts ×¼ | 0.701 | 0.703 | +0.002 | +0.001 a +0.003 | 7 de 10 |
| llargs ×¼ | 0.692 | 0.694 | +0.002 | +0.001 a +0.003 | 8 de 10 |
| barreja ×¼ | 0.699 | 0.699 | -0.000 | -0.002 a +0.001 | 4 de 10 |
| aire ×¼ | 0.649 | 0.649 | +0.000 | -0.001 a +0.001 | 6 de 10 |
| curts | 0.667 | 0.669 | +0.001 | +0.000 a +0.003 | 8 de 10 |
| llargs | 0.643 | 0.645 | +0.002 | +0.000 a +0.004 | 8 de 10 |
| barreja | 0.649 | 0.650 | +0.001 | -0.001 a +0.003 | 6 de 10 |
| aire | 0.621 | 0.622 | +0.001 | -0.002 a +0.003 | 6 de 10 |
| soroll2 | 0.546 | 0.554 | +0.008 | +0.005 a +0.012 | 9 de 10 |
| partit ×¼ | 0.763 | 0.765 | +0.002 | +0.001 a +0.003 | 8 de 10 |

## Amb el nivell mitjà: A pilota morta contra A etiquetes al decodificador, la T3ag (spellF1)

| escenari | A etiquetes al decodificador | A pilota morta | diferència | interval del 95 % | A pilota morta guanya |
|---|---|---|---|---|---|
| net | 0.800 | 0.801 | +0.001 | -0.000 a +0.002 | 7 de 10 |
| curts ×¼ | 0.700 | 0.702 | +0.002 | +0.001 a +0.003 | 9 de 10 |
| llargs ×¼ | 0.690 | 0.691 | +0.001 | -0.000 a +0.002 | 5 de 10 |
| barreja ×¼ | 0.698 | 0.698 | +0.000 | -0.001 a +0.001 | 4 de 10 |
| aire ×¼ | 0.647 | 0.647 | +0.000 | -0.002 a +0.002 | 6 de 10 |
| curts | 0.667 | 0.668 | +0.001 | +0.000 a +0.002 | 7 de 10 |
| llargs | 0.642 | 0.645 | +0.002 | +0.001 a +0.004 | 8 de 10 |
| barreja | 0.649 | 0.650 | +0.001 | +0.000 a +0.002 | 7 de 10 |
| aire | 0.620 | 0.620 | +0.000 | -0.003 a +0.003 | 6 de 10 |
| soroll2 | 0.543 | 0.549 | +0.006 | +0.003 a +0.009 | 9 de 10 |
| partit ×¼ | 0.762 | 0.764 | +0.002 | +0.001 a +0.004 | 8 de 10 |

## Amb el nivell dolent: A pilota morta contra A etiquetes al decodificador, la T3ag (spellF1)

| escenari | A etiquetes al decodificador | A pilota morta | diferència | interval del 95 % | A pilota morta guanya |
|---|---|---|---|---|---|
| net | 0.800 | 0.801 | +0.001 | +0.000 a +0.001 | 8 de 10 |
| curts ×¼ | 0.699 | 0.702 | +0.003 | +0.002 a +0.004 | 9 de 10 |
| llargs ×¼ | 0.689 | 0.692 | +0.002 | +0.000 a +0.004 | 8 de 10 |
| barreja ×¼ | 0.697 | 0.697 | +0.000 | -0.001 a +0.002 | 6 de 10 |
| aire ×¼ | 0.646 | 0.648 | +0.002 | -0.000 a +0.003 | 8 de 10 |
| curts | 0.666 | 0.668 | +0.002 | +0.001 a +0.003 | 8 de 10 |
| llargs | 0.642 | 0.644 | +0.002 | +0.000 a +0.004 | 8 de 10 |
| barreja | 0.647 | 0.648 | +0.001 | -0.001 a +0.002 | 7 de 10 |
| aire | 0.618 | 0.618 | +0.001 | -0.002 a +0.003 | 6 de 10 |
| soroll2 | 0.540 | 0.547 | +0.007 | +0.005 a +0.009 | 9 de 10 |
| partit ×¼ | 0.761 | 0.763 | +0.001 | +0.000 a +0.002 | 8 de 10 |

## A pilota morta contra A xarxes, decodificador de toc, nivell mitjà, només els partits de dfl

| escenari | A xarxes, decodificador de toc | A pilota morta | diferència | interval del 95 % | A pilota morta guanya |
|---|---|---|---|---|---|
| net | 0.766 | 0.770 | +0.005 | -0.001 a +0.012 | 5 de 7 |
| curts ×¼ | 0.642 | 0.672 | +0.030 | +0.025 a +0.038 | 7 de 7 |
| llargs ×¼ | 0.621 | 0.659 | +0.039 | +0.028 a +0.049 | 7 de 7 |
| barreja ×¼ | 0.630 | 0.666 | +0.036 | +0.029 a +0.042 | 7 de 7 |
| aire ×¼ | 0.544 | 0.594 | +0.050 | +0.044 a +0.058 | 7 de 7 |
| curts | 0.607 | 0.640 | +0.033 | +0.026 a +0.040 | 7 de 7 |
| llargs | 0.564 | 0.608 | +0.044 | +0.025 a +0.062 | 7 de 7 |
| barreja | 0.571 | 0.611 | +0.039 | +0.030 a +0.049 | 7 de 7 |
| aire | 0.501 | 0.571 | +0.070 | +0.061 a +0.078 | 7 de 7 |
| soroll2 | 0.433 | 0.506 | +0.073 | +0.066 a +0.080 | 7 de 7 |
| partit ×¼ | 0.717 | 0.733 | +0.016 | +0.007 a +0.025 | 7 de 7 |

## A pilota morta contra A neteja d'aire, nivell mitjà, només els partits de dfl

| escenari | A neteja d'aire | A pilota morta | diferència | interval del 95 % | A pilota morta guanya |
|---|---|---|---|---|---|
| net | 0.768 | 0.770 | +0.002 | +0.001 a +0.004 | 6 de 7 |
| curts ×¼ | 0.669 | 0.672 | +0.003 | +0.001 a +0.005 | 6 de 7 |
| llargs ×¼ | 0.656 | 0.659 | +0.003 | +0.001 a +0.006 | 6 de 7 |
| barreja ×¼ | 0.664 | 0.666 | +0.002 | +0.000 a +0.004 | 6 de 7 |
| aire ×¼ | 0.592 | 0.594 | +0.002 | -0.001 a +0.005 | 4 de 7 |
| curts | 0.637 | 0.640 | +0.003 | +0.002 a +0.004 | 7 de 7 |
| llargs | 0.602 | 0.608 | +0.006 | +0.003 a +0.009 | 7 de 7 |
| barreja | 0.608 | 0.611 | +0.003 | -0.000 a +0.007 | 4 de 7 |
| aire | 0.572 | 0.571 | -0.001 | -0.005 a +0.004 | 3 de 7 |
| soroll2 | 0.491 | 0.506 | +0.015 | +0.012 a +0.020 | 7 de 7 |
| partit ×¼ | 0.729 | 0.733 | +0.003 | +0.002 a +0.005 | 7 de 7 |

## A pilota morta contra A xarxes, decodificador de toc, nivell mitjà, només els partits de metrica

| escenari | A xarxes, decodificador de toc | A pilota morta | diferència | interval del 95 % | A pilota morta guanya |
|---|---|---|---|---|---|
| net | 0.874 | 0.873 | -0.001 | -0.012 a +0.015 | 1 de 3 |
| curts ×¼ | 0.747 | 0.772 | +0.026 | +0.014 a +0.033 | 3 de 3 |
| llargs ×¼ | 0.723 | 0.766 | +0.042 | +0.031 a +0.060 | 3 de 3 |
| barreja ×¼ | 0.730 | 0.773 | +0.043 | +0.032 a +0.059 | 3 de 3 |
| aire ×¼ | 0.731 | 0.770 | +0.039 | +0.023 a +0.054 | 3 de 3 |
| curts | 0.702 | 0.732 | +0.030 | +0.022 a +0.040 | 3 de 3 |
| llargs | 0.682 | 0.731 | +0.049 | +0.044 a +0.052 | 3 de 3 |
| barreja | 0.684 | 0.742 | +0.058 | +0.023 a +0.080 | 3 de 3 |
| aire | 0.679 | 0.733 | +0.054 | +0.047 a +0.059 | 3 de 3 |
| soroll2 | 0.557 | 0.649 | +0.092 | +0.082 a +0.111 | 3 de 3 |
| partit ×¼ | 0.813 | 0.838 | +0.025 | +0.014 a +0.036 | 3 de 3 |

## A pilota morta contra A neteja d'aire, nivell mitjà, només els partits de metrica

| escenari | A neteja d'aire | A pilota morta | diferència | interval del 95 % | A pilota morta guanya |
|---|---|---|---|---|---|
| net | 0.873 | 0.873 | +0.000 | -0.002 a +0.003 | 1 de 3 |
| curts ×¼ | 0.769 | 0.772 | +0.003 | -0.001 a +0.010 | 1 de 3 |
| llargs ×¼ | 0.763 | 0.766 | +0.003 | +0.001 a +0.004 | 3 de 3 |
| barreja ×¼ | 0.773 | 0.773 | +0.001 | -0.001 a +0.001 | 2 de 3 |
| aire ×¼ | 0.765 | 0.770 | +0.005 | +0.003 a +0.006 | 3 de 3 |
| curts | 0.729 | 0.732 | +0.003 | -0.000 a +0.010 | 2 de 3 |
| llargs | 0.730 | 0.731 | +0.001 | -0.001 a +0.003 | 1 de 3 |
| barreja | 0.736 | 0.742 | +0.006 | +0.006 a +0.007 | 3 de 3 |
| aire | 0.724 | 0.733 | +0.009 | +0.004 a +0.014 | 3 de 3 |
| soroll2 | 0.634 | 0.649 | +0.015 | +0.011 a +0.020 | 3 de 3 |
| partit ×¼ | 0.835 | 0.838 | +0.003 | -0.001 a +0.007 | 2 de 3 |

## A pilota morta contra A xarxes, decodificador de toc, nivell bo

| escenari | A xarxes, decodificador de toc | A pilota morta | diferència | interval del 95 % | A pilota morta guanya |
|---|---|---|---|---|---|
| net | 0.798 | 0.802 | +0.004 | -0.002 a +0.010 | 6 de 10 |
| curts ×¼ | 0.673 | 0.703 | +0.030 | +0.025 a +0.036 | 10 de 10 |
| llargs ×¼ | 0.651 | 0.694 | +0.043 | +0.033 a +0.052 | 10 de 10 |
| barreja ×¼ | 0.660 | 0.699 | +0.039 | +0.033 a +0.044 | 10 de 10 |
| aire ×¼ | 0.600 | 0.649 | +0.049 | +0.042 a +0.056 | 10 de 10 |
| curts | 0.636 | 0.669 | +0.033 | +0.028 a +0.038 | 10 de 10 |
| llargs | 0.599 | 0.645 | +0.045 | +0.033 a +0.058 | 10 de 10 |
| barreja | 0.605 | 0.650 | +0.045 | +0.036 a +0.054 | 10 de 10 |
| aire | 0.554 | 0.622 | +0.068 | +0.063 a +0.073 | 10 de 10 |
| soroll2 | 0.470 | 0.554 | +0.083 | +0.076 a +0.091 | 10 de 10 |
| partit ×¼ | 0.746 | 0.765 | +0.019 | +0.012 a +0.026 | 10 de 10 |

## La part del sostre de la T3af que se n'aprofita

A la veritat de toc, la mitjana dels deu partits: el sostre de la T3af menys A neteja d'aire, el que en
treu A pilota morta, i la part.

| escenari | sostre · bo | sostre · mitjà | sostre · dolent | treu · bo | treu · mitjà | treu · dolent | part · bo | part · mitjà | part · dolent |
|---|---|---|---|---|---|---|---|---|---|
| net | 0.021 | 0.019 | 0.011 | 0.003 | 0.002 | 0.001 | 0.121 | 0.090 | 0.127 |
| curts ×¼ | 0.034 | 0.027 | 0.020 | 0.004 | 0.003 | 0.003 | 0.116 | 0.107 | 0.132 |
| llargs ×¼ | 0.041 | 0.031 | 0.027 | 0.006 | 0.003 | 0.003 | 0.152 | 0.105 | 0.131 |
| barreja ×¼ | 0.036 | 0.029 | 0.019 | 0.002 | 0.002 | 0.001 | 0.063 | 0.064 | 0.043 |
| aire ×¼ | 0.045 | 0.037 | 0.024 | 0.005 | 0.003 | 0.004 | 0.113 | 0.073 | 0.147 |
| curts | 0.040 | 0.028 | 0.023 | 0.004 | 0.003 | 0.003 | 0.094 | 0.109 | 0.120 |
| llargs | 0.048 | 0.037 | 0.029 | 0.004 | 0.004 | 0.003 | 0.089 | 0.115 | 0.117 |
| barreja | 0.044 | 0.034 | 0.031 | 0.004 | 0.004 | 0.001 | 0.091 | 0.107 | 0.044 |
| aire | 0.049 | 0.037 | 0.027 | 0.005 | 0.002 | 0.001 | 0.091 | 0.060 | 0.035 |
| soroll2 | 0.090 | 0.070 | 0.052 | 0.020 | 0.015 | 0.013 | 0.218 | 0.213 | 0.251 |
| partit ×¼ | 0.024 | 0.020 | 0.014 | 0.004 | 0.003 | 0.001 | 0.148 | 0.158 | 0.105 |

## A 5 s o menys de cada represa

La part de les imatges vàlides a 5 s o menys d'una represa on la predicció (amb les abstencions
omplertes) és la veritat de toc.

| escenari | A neteja d'aire | A pilota morta, bo | A pilota morta, mitjà | A pilota morta, dolent | A pilota morta, cap |
|---|---|---|---|---|---|
| net | 0.953 | 0.956 | 0.956 | 0.955 | 0.953 |
| curts ×¼ | 0.918 | 0.926 | 0.923 | 0.922 | 0.918 |
| llargs ×¼ | 0.892 | 0.905 | 0.899 | 0.898 | 0.892 |
| barreja ×¼ | 0.901 | 0.911 | 0.908 | 0.905 | 0.901 |
| aire ×¼ | 0.886 | 0.895 | 0.892 | 0.890 | 0.886 |
| curts | 0.900 | 0.911 | 0.907 | 0.905 | 0.900 |
| llargs | 0.873 | 0.885 | 0.881 | 0.881 | 0.873 |
| barreja | 0.878 | 0.889 | 0.886 | 0.883 | 0.878 |
| aire | 0.870 | 0.878 | 0.872 | 0.871 | 0.870 |
| soroll2 | 0.750 | 0.796 | 0.783 | 0.775 | 0.750 |
| partit ×¼ | 0.944 | 0.949 | 0.947 | 0.946 | 0.944 |

## Les medianes per tipus

A cada partit, la mediana dels segons de pilota morta seguida abans de les represes de cada tipus, a la
veritat de toc dels altres nou.

| partit | banda | corner | porta | falta | sortida |
|---|---|---|---|---|---|
| dfl-J03WMX | 11.2 | 30.9 | 23.2 | 30.3 | 55.9 |
| dfl-J03WN1 | 11.0 | 30.9 | 22.4 | 27.1 | 54.6 |
| dfl-J03WOH | 11.3 | 31.0 | 22.8 | 30.5 | 55.3 |
| dfl-J03WOY | 10.6 | 30.9 | 24.6 | 28.8 | 57.3 |
| dfl-J03WPY | 11.5 | 30.5 | 21.8 | 28.6 | 55.9 |
| dfl-J03WQQ | 11.7 | 31.7 | 23.7 | 28.4 | 55.3 |
| dfl-J03WR9 | 11.0 | 31.2 | 24.6 | 27.7 | 55.3 |
| metrica-1 | 11.7 | 32.7 | 22.8 | 30.0 | 57.3 |
| metrica-2 | 12.0 | 31.2 | 22.8 | 30.7 | 54.6 |
| metrica-3 | 11.9 | 31.0 | 22.8 | 31.0 | 60.2 |

## Els paràmetres triats

A cada partit, amb els altres nou, als quatre ×¼ i a la mitjana dels nivells bo, mitjà i dolent.

| partit | beta_d | forma | durada | marge_s |
|---|---|---|---|---|
| dfl-J03WMX | 1.00 | per tipus | 1.50 | 0.00 |
| dfl-J03WN1 | 1.00 | per tipus | 1.50 | 0.00 |
| dfl-J03WOH | 1.00 | per tipus | 1.50 | 0.00 |
| dfl-J03WOY | 1.00 | per tipus | 1.50 | 1.00 |
| dfl-J03WPY | 1.00 | per tipus | 1.50 | 0.00 |
| dfl-J03WQQ | 1.00 | per tipus | 1.50 | 0.00 |
| dfl-J03WR9 | 1.00 | per tipus | 1.50 | 1.00 |
| metrica-1 | 1.00 | per tipus | 1.50 | 0.00 |
| metrica-2 | 1.00 | per tipus | 1.50 | 0.00 |
| metrica-3 | 1.00 | per tipus | 1.50 | 0.00 |

**A la vora de la graella** (algun partit tria el valor més baix o el més alt): `beta_d` = 1, `marge_s` = 0, `durada` = 1.5 (per tipus).

## L'spellF1 de cada mètode (mitjana dels deu partits, nivell mitjà)

**spellF1 a la veritat de toc**

| escenari | A xarxes, decodificador de toc | A equips sencers | A neteja d'aire | A pilota morta |
|---|---|---|---|---|
| net | 0.798 | 0.799 | 0.799 | 0.801 |
| curts ×¼ | 0.673 | 0.699 | 0.699 | 0.702 |
| llargs ×¼ | 0.651 | 0.688 | 0.688 | 0.691 |
| barreja ×¼ | 0.660 | 0.696 | 0.696 | 0.698 |
| aire ×¼ | 0.600 | 0.629 | 0.644 | 0.647 |
| curts | 0.636 | 0.665 | 0.665 | 0.668 |
| llargs | 0.599 | 0.640 | 0.640 | 0.645 |
| barreja | 0.605 | 0.646 | 0.646 | 0.650 |
| aire | 0.554 | 0.600 | 0.618 | 0.620 |
| soroll2 | 0.470 | 0.534 | 0.534 | 0.549 |
| partit ×¼ | 0.746 | 0.761 | 0.761 | 0.764 |

**spellF1 a la veritat de sempre**

| escenari | A xarxes, decodificador de toc | A equips sencers | A neteja d'aire | A pilota morta |
|---|---|---|---|---|
| net | 0.808 | 0.810 | 0.810 | 0.812 |
| curts ×¼ | 0.684 | 0.708 | 0.708 | 0.711 |
| llargs ×¼ | 0.662 | 0.700 | 0.700 | 0.703 |
| barreja ×¼ | 0.671 | 0.708 | 0.708 | 0.710 |
| aire ×¼ | 0.612 | 0.643 | 0.658 | 0.661 |
| curts | 0.644 | 0.674 | 0.674 | 0.677 |
| llargs | 0.607 | 0.648 | 0.648 | 0.652 |
| barreja | 0.616 | 0.656 | 0.656 | 0.660 |
| aire | 0.564 | 0.613 | 0.632 | 0.633 |
| soroll2 | 0.478 | 0.543 | 0.543 | 0.558 |
| partit ×¼ | 0.757 | 0.772 | 0.772 | 0.775 |

## Els decodificadors

A neteja d'aire i A pilota morta fan servir, a cada partit, el d'A equips sencers.

- **A equips sencers:** w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 16, durada mínima 12 (2 partits)
