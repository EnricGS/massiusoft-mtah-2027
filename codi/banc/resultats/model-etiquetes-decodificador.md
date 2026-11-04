# Banc obert · Les etiquetes de pilota aturada al decodificador (T3ag)

Generat amb `uv run python -I -m banc.model_etiquetes_decodificador`. Dades obertes: 7 partits de DFL
(IDSSE, CC BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es
fa i el criteri: `docs/pla-tocs.md`, «T3ag», i la capçalera de `banc/model_etiquetes_decodificador.py`.
Es puntua a la veritat de toc.

**A xarxes, decodificador de toc** i **A equips sencers** són els de la T3v, **A pilota creïble**, el de la T3w, i **A neteja d'aire**,
el de la T3ac, amb les peces de la memòria cau (✓ comprovat). **A etiquetes al decodificador** és A
neteja d'aire amb el seu decodificador, i abans de decodificar, el que hi sumen les etiquetes simulades.
✓ Comprovat: no dona mai la D a una imatge netejada, i sense etiquetes dona exactament A neteja d'aire.

## Amb el nivell mitjà: A etiquetes al decodificador contra A xarxes, decodificador de toc (spellF1), el criteri

| escenari | A xarxes, decodificador de toc | A etiquetes al decodificador | diferència | interval del 95 % | A etiquetes al decodificador guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.798 | 0.800 | +0.002 | -0.003 a +0.008 | 5 de 10 | no perd | ✓ |
| curts ×¼ | 0.673 | 0.700 | +0.026 | +0.021 a +0.032 | 10 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.651 | 0.690 | +0.039 | +0.031 a +0.047 | 10 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.660 | 0.698 | +0.038 | +0.032 a +0.044 | 10 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.600 | 0.647 | +0.046 | +0.040 a +0.053 | 10 de 10 | guanya clarament | ✓ |
| curts | 0.636 | 0.667 | +0.031 | +0.025 a +0.037 | 10 de 10 | no perd | ✓ |
| llargs | 0.599 | 0.642 | +0.043 | +0.029 a +0.056 | 10 de 10 | no perd | ✓ |
| barreja | 0.605 | 0.649 | +0.044 | +0.033 a +0.054 | 10 de 10 | no perd | ✓ |
| aire | 0.554 | 0.620 | +0.065 | +0.060 a +0.070 | 10 de 10 | no perd | ✓ |
| soroll2 | 0.470 | 0.543 | +0.073 | +0.066 a +0.079 | 10 de 10 | no perd | ✓ |
| partit ×¼ | 0.746 | 0.762 | +0.016 | +0.009 a +0.024 | 8 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1, el soroll2 i «partit ×¼» | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## Amb els nivells dolent i cap: A etiquetes al decodificador contra A neteja d'aire, la segona part del criteri

| Nivell | curts ×¼ | llargs ×¼ | barreja ×¼ | aire ×¼ | partit ×¼ | No baixa de −0.005 |
|---|---|---|---|---|---|---|
| dolent | -0.0001 | +0.0012 | +0.0005 | +0.0020 | +0.0003 | ✓ |
| cap | +0.0000 | +0.0000 | +0.0000 | +0.0000 | +0.0000 | ✓ |

**A etiquetes al decodificador no passa el criteri sencer.**

## Amb el nivell bo: A etiquetes al decodificador contra A neteja d'aire (spellF1)

| escenari | A neteja d'aire | A etiquetes al decodificador | diferència | interval del 95 % | A etiquetes al decodificador guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.801 | +0.002 | +0.001 a +0.002 | 9 de 10 |
| curts ×¼ | 0.699 | 0.701 | +0.002 | +0.001 a +0.004 | 8 de 10 |
| llargs ×¼ | 0.688 | 0.692 | +0.004 | +0.003 a +0.006 | 10 de 10 |
| barreja ×¼ | 0.696 | 0.699 | +0.003 | +0.001 a +0.004 | 8 de 10 |
| aire ×¼ | 0.644 | 0.649 | +0.005 | +0.003 a +0.007 | 10 de 10 |
| curts | 0.665 | 0.667 | +0.002 | +0.001 a +0.004 | 8 de 10 |
| llargs | 0.640 | 0.643 | +0.002 | +0.001 a +0.004 | 7 de 10 |
| barreja | 0.646 | 0.649 | +0.003 | +0.001 a +0.006 | 7 de 10 |
| aire | 0.618 | 0.621 | +0.004 | +0.002 a +0.006 | 8 de 10 |
| soroll2 | 0.534 | 0.546 | +0.012 | +0.009 a +0.014 | 10 de 10 |
| partit ×¼ | 0.761 | 0.763 | +0.002 | +0.001 a +0.002 | 7 de 10 |

## Amb el nivell mitjà: A etiquetes al decodificador contra A neteja d'aire (spellF1)

| escenari | A neteja d'aire | A etiquetes al decodificador | diferència | interval del 95 % | A etiquetes al decodificador guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.800 | +0.001 | +0.000 a +0.001 | 8 de 10 |
| curts ×¼ | 0.699 | 0.700 | +0.001 | -0.001 a +0.002 | 6 de 10 |
| llargs ×¼ | 0.688 | 0.690 | +0.002 | +0.002 a +0.003 | 10 de 10 |
| barreja ×¼ | 0.696 | 0.698 | +0.002 | +0.000 a +0.003 | 8 de 10 |
| aire ×¼ | 0.644 | 0.647 | +0.003 | +0.002 a +0.004 | 9 de 10 |
| curts | 0.665 | 0.667 | +0.002 | +0.001 a +0.003 | 9 de 10 |
| llargs | 0.640 | 0.642 | +0.002 | +0.001 a +0.003 | 9 de 10 |
| barreja | 0.646 | 0.649 | +0.002 | +0.000 a +0.005 | 7 de 10 |
| aire | 0.618 | 0.620 | +0.002 | +0.000 a +0.004 | 8 de 10 |
| soroll2 | 0.534 | 0.543 | +0.009 | +0.007 a +0.011 | 10 de 10 |
| partit ×¼ | 0.761 | 0.762 | +0.001 | +0.000 a +0.002 | 6 de 10 |

## Amb el nivell dolent: A etiquetes al decodificador contra A neteja d'aire (spellF1)

| escenari | A neteja d'aire | A etiquetes al decodificador | diferència | interval del 95 % | A etiquetes al decodificador guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.800 | +0.001 | +0.000 a +0.001 | 6 de 10 |
| curts ×¼ | 0.699 | 0.699 | -0.000 | -0.001 a +0.001 | 3 de 10 |
| llargs ×¼ | 0.688 | 0.689 | +0.001 | -0.000 a +0.003 | 6 de 10 |
| barreja ×¼ | 0.696 | 0.697 | +0.000 | -0.000 a +0.001 | 7 de 10 |
| aire ×¼ | 0.644 | 0.646 | +0.002 | +0.001 a +0.003 | 9 de 10 |
| curts | 0.665 | 0.666 | +0.001 | -0.000 a +0.002 | 8 de 10 |
| llargs | 0.640 | 0.642 | +0.001 | +0.000 a +0.003 | 7 de 10 |
| barreja | 0.646 | 0.647 | +0.001 | -0.001 a +0.003 | 6 de 10 |
| aire | 0.618 | 0.618 | +0.000 | -0.001 a +0.002 | 4 de 10 |
| soroll2 | 0.534 | 0.540 | +0.006 | +0.004 a +0.009 | 10 de 10 |
| partit ×¼ | 0.761 | 0.761 | +0.000 | -0.000 a +0.001 | 4 de 10 |

## Amb el nivell cap: A etiquetes al decodificador contra A neteja d'aire (spellF1)

| escenari | A neteja d'aire | A etiquetes al decodificador | diferència | interval del 95 % | A etiquetes al decodificador guanya |
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
| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | ✗ |
| «partit ×¼» | la diferència no és negativa | ✓ |
| El net, els ×1 i el soroll2 | no perd (diferència ≥ −0.04) | ✓ |
| Dolent i cap | la segona part del criteri | ✓ |

**A etiquetes al decodificador no és el millor fins ara:** el pas següent es fa a sobre d'A neteja d'aire.

## A etiquetes al decodificador contra A xarxes, decodificador de toc, nivell mitjà, només els partits de dfl

| escenari | A xarxes, decodificador de toc | A etiquetes al decodificador | diferència | interval del 95 % | A etiquetes al decodificador guanya |
|---|---|---|---|---|---|
| net | 0.766 | 0.769 | +0.003 | -0.002 a +0.010 | 4 de 7 |
| curts ×¼ | 0.642 | 0.669 | +0.027 | +0.023 a +0.036 | 7 de 7 |
| llargs ×¼ | 0.621 | 0.658 | +0.038 | +0.028 a +0.047 | 7 de 7 |
| barreja ×¼ | 0.630 | 0.665 | +0.035 | +0.029 a +0.041 | 7 de 7 |
| aire ×¼ | 0.544 | 0.594 | +0.050 | +0.043 a +0.057 | 7 de 7 |
| curts | 0.607 | 0.639 | +0.032 | +0.025 a +0.039 | 7 de 7 |
| llargs | 0.564 | 0.605 | +0.041 | +0.022 a +0.060 | 7 de 7 |
| barreja | 0.571 | 0.610 | +0.039 | +0.030 a +0.049 | 7 de 7 |
| aire | 0.501 | 0.572 | +0.071 | +0.064 a +0.078 | 7 de 7 |
| soroll2 | 0.433 | 0.501 | +0.067 | +0.061 a +0.074 | 7 de 7 |
| partit ×¼ | 0.717 | 0.730 | +0.014 | +0.004 a +0.023 | 5 de 7 |

## A etiquetes al decodificador contra A neteja d'aire, nivell mitjà, només els partits de dfl

| escenari | A neteja d'aire | A etiquetes al decodificador | diferència | interval del 95 % | A etiquetes al decodificador guanya |
|---|---|---|---|---|---|
| net | 0.768 | 0.769 | +0.001 | +0.000 a +0.002 | 6 de 7 |
| curts ×¼ | 0.669 | 0.669 | +0.000 | -0.001 a +0.002 | 4 de 7 |
| llargs ×¼ | 0.656 | 0.658 | +0.002 | +0.001 a +0.003 | 7 de 7 |
| barreja ×¼ | 0.664 | 0.665 | +0.001 | -0.000 a +0.003 | 5 de 7 |
| aire ×¼ | 0.592 | 0.594 | +0.002 | +0.001 a +0.003 | 6 de 7 |
| curts | 0.637 | 0.639 | +0.002 | +0.000 a +0.003 | 6 de 7 |
| llargs | 0.602 | 0.605 | +0.003 | +0.001 a +0.005 | 7 de 7 |
| barreja | 0.608 | 0.610 | +0.002 | -0.000 a +0.006 | 4 de 7 |
| aire | 0.572 | 0.572 | +0.000 | -0.002 a +0.002 | 5 de 7 |
| soroll2 | 0.491 | 0.501 | +0.009 | +0.007 a +0.012 | 7 de 7 |
| partit ×¼ | 0.729 | 0.730 | +0.001 | +0.000 a +0.002 | 5 de 7 |

## A etiquetes al decodificador contra A xarxes, decodificador de toc, nivell mitjà, només els partits de metrica

| escenari | A xarxes, decodificador de toc | A etiquetes al decodificador | diferència | interval del 95 % | A etiquetes al decodificador guanya |
|---|---|---|---|---|---|
| net | 0.874 | 0.873 | -0.001 | -0.009 a +0.012 | 1 de 3 |
| curts ×¼ | 0.747 | 0.770 | +0.024 | +0.010 a +0.032 | 3 de 3 |
| llargs ×¼ | 0.723 | 0.765 | +0.042 | +0.029 a +0.060 | 3 de 3 |
| barreja ×¼ | 0.730 | 0.775 | +0.045 | +0.032 a +0.060 | 3 de 3 |
| aire ×¼ | 0.731 | 0.769 | +0.038 | +0.021 a +0.056 | 3 de 3 |
| curts | 0.702 | 0.731 | +0.029 | +0.017 a +0.042 | 3 de 3 |
| llargs | 0.682 | 0.730 | +0.048 | +0.039 a +0.054 | 3 de 3 |
| barreja | 0.684 | 0.738 | +0.054 | +0.021 a +0.077 | 3 de 3 |
| aire | 0.679 | 0.730 | +0.051 | +0.046 a +0.056 | 3 de 3 |
| soroll2 | 0.557 | 0.642 | +0.085 | +0.071 a +0.105 | 3 de 3 |
| partit ×¼ | 0.813 | 0.835 | +0.023 | +0.016 a +0.034 | 3 de 3 |

## A etiquetes al decodificador contra A neteja d'aire, nivell mitjà, només els partits de metrica

| escenari | A neteja d'aire | A etiquetes al decodificador | diferència | interval del 95 % | A etiquetes al decodificador guanya |
|---|---|---|---|---|---|
| net | 0.873 | 0.873 | +0.001 | +0.000 a +0.001 | 2 de 3 |
| curts ×¼ | 0.769 | 0.770 | +0.001 | -0.005 a +0.006 | 2 de 3 |
| llargs ×¼ | 0.763 | 0.765 | +0.002 | +0.001 a +0.004 | 3 de 3 |
| barreja ×¼ | 0.773 | 0.775 | +0.002 | +0.001 a +0.005 | 3 de 3 |
| aire ×¼ | 0.765 | 0.769 | +0.004 | +0.002 a +0.006 | 3 de 3 |
| curts | 0.729 | 0.731 | +0.002 | +0.001 a +0.005 | 3 de 3 |
| llargs | 0.730 | 0.730 | +0.000 | -0.002 a +0.001 | 2 de 3 |
| barreja | 0.736 | 0.738 | +0.003 | +0.001 a +0.005 | 3 de 3 |
| aire | 0.724 | 0.730 | +0.006 | +0.001 a +0.009 | 3 de 3 |
| soroll2 | 0.634 | 0.642 | +0.008 | +0.005 a +0.010 | 3 de 3 |
| partit ×¼ | 0.835 | 0.835 | +0.000 | -0.001 a +0.002 | 1 de 3 |

## A etiquetes al decodificador contra A xarxes, decodificador de toc, nivell bo

| escenari | A xarxes, decodificador de toc | A etiquetes al decodificador | diferència | interval del 95 % | A etiquetes al decodificador guanya |
|---|---|---|---|---|---|
| net | 0.798 | 0.801 | +0.003 | -0.002 a +0.009 | 6 de 10 |
| curts ×¼ | 0.673 | 0.701 | +0.028 | +0.023 a +0.034 | 10 de 10 |
| llargs ×¼ | 0.651 | 0.692 | +0.041 | +0.032 a +0.049 | 10 de 10 |
| barreja ×¼ | 0.660 | 0.699 | +0.039 | +0.033 a +0.045 | 10 de 10 |
| aire ×¼ | 0.600 | 0.649 | +0.049 | +0.042 a +0.056 | 10 de 10 |
| curts | 0.636 | 0.667 | +0.031 | +0.025 a +0.037 | 10 de 10 |
| llargs | 0.599 | 0.643 | +0.043 | +0.030 a +0.056 | 10 de 10 |
| barreja | 0.605 | 0.649 | +0.044 | +0.033 a +0.054 | 10 de 10 |
| aire | 0.554 | 0.621 | +0.067 | +0.062 a +0.072 | 10 de 10 |
| soroll2 | 0.470 | 0.546 | +0.075 | +0.069 a +0.082 | 10 de 10 |
| partit ×¼ | 0.746 | 0.763 | +0.017 | +0.010 a +0.024 | 9 de 10 |

## La part del sostre de la T3af que se n'aprofita

A la veritat de toc, la mitjana dels deu partits: el sostre de la T3af menys A neteja d'aire, el que en
treu A etiquetes al decodificador, i la part.

| escenari | sostre · bo | sostre · mitjà | sostre · dolent | treu · bo | treu · mitjà | treu · dolent | part · bo | part · mitjà | part · dolent |
|---|---|---|---|---|---|---|---|---|---|
| net | 0.021 | 0.019 | 0.011 | 0.002 | 0.001 | 0.001 | 0.074 | 0.050 | 0.046 |
| curts ×¼ | 0.034 | 0.027 | 0.020 | 0.002 | 0.001 | -0.000 | 0.061 | 0.023 | -0.003 |
| llargs ×¼ | 0.041 | 0.031 | 0.027 | 0.004 | 0.002 | 0.001 | 0.099 | 0.077 | 0.044 |
| barreja ×¼ | 0.036 | 0.029 | 0.019 | 0.003 | 0.002 | 0.000 | 0.072 | 0.060 | 0.026 |
| aire ×¼ | 0.045 | 0.037 | 0.024 | 0.005 | 0.003 | 0.002 | 0.112 | 0.069 | 0.081 |
| curts | 0.040 | 0.028 | 0.023 | 0.002 | 0.002 | 0.001 | 0.059 | 0.067 | 0.035 |
| llargs | 0.048 | 0.037 | 0.029 | 0.002 | 0.002 | 0.001 | 0.046 | 0.052 | 0.049 |
| barreja | 0.044 | 0.034 | 0.031 | 0.003 | 0.002 | 0.001 | 0.069 | 0.067 | 0.027 |
| aire | 0.049 | 0.037 | 0.027 | 0.004 | 0.002 | 0.000 | 0.079 | 0.053 | 0.013 |
| soroll2 | 0.090 | 0.070 | 0.052 | 0.012 | 0.009 | 0.006 | 0.128 | 0.127 | 0.116 |
| partit ×¼ | 0.024 | 0.020 | 0.014 | 0.002 | 0.001 | 0.000 | 0.065 | 0.043 | 0.020 |

## A 5 s o menys de cada represa

La part de les imatges vàlides a 5 s o menys d'una represa on la predicció (amb les abstencions
omplertes) és la veritat de toc.

| escenari | A neteja d'aire | A etiquetes al decodificador, bo | A etiquetes al decodificador, mitjà | A etiquetes al decodificador, dolent | A etiquetes al decodificador, cap |
|---|---|---|---|---|---|
| net | 0.953 | 0.955 | 0.955 | 0.954 | 0.953 |
| curts ×¼ | 0.918 | 0.924 | 0.922 | 0.920 | 0.918 |
| llargs ×¼ | 0.892 | 0.903 | 0.899 | 0.896 | 0.892 |
| barreja ×¼ | 0.901 | 0.910 | 0.907 | 0.903 | 0.901 |
| aire ×¼ | 0.886 | 0.895 | 0.892 | 0.889 | 0.886 |
| curts | 0.900 | 0.910 | 0.905 | 0.904 | 0.900 |
| llargs | 0.873 | 0.883 | 0.881 | 0.878 | 0.873 |
| barreja | 0.878 | 0.889 | 0.886 | 0.881 | 0.878 |
| aire | 0.870 | 0.879 | 0.873 | 0.871 | 0.870 |
| soroll2 | 0.750 | 0.789 | 0.779 | 0.763 | 0.750 |
| partit ×¼ | 0.944 | 0.948 | 0.946 | 0.946 | 0.944 |

## Els paràmetres triats

A cada partit, amb els altres nou, als quatre ×¼ i a la mitjana dels nivells bo, mitjà i dolent.

| partit | beta_d | abans_s | beta_e | despres_s | marge_s |
|---|---|---|---|---|---|
| dfl-J03WMX | 1.00 | 10.00 | 0.00 | 2.00 | 1.00 |
| dfl-J03WN1 | 1.00 | 10.00 | 0.00 | 2.00 | 1.00 |
| dfl-J03WOH | 1.00 | 10.00 | 0.00 | 2.00 | 1.00 |
| dfl-J03WOY | 1.00 | 10.00 | 0.00 | 2.00 | 1.00 |
| dfl-J03WPY | 1.00 | 10.00 | 0.00 | 2.00 | 1.00 |
| dfl-J03WQQ | 1.00 | 10.00 | 0.00 | 2.00 | 1.00 |
| dfl-J03WR9 | 1.00 | 10.00 | 0.00 | 2.00 | 1.00 |
| metrica-1 | 1.00 | 10.00 | 0.00 | 2.00 | 1.00 |
| metrica-2 | 1.00 | 10.00 | 0.00 | 2.00 | 1.00 |
| metrica-3 | 1.00 | 10.00 | 0.00 | 2.00 | 1.00 |

**A la vora de la graella** (algun partit tria el valor més alt): `beta_d`, `abans_s`.

## L'spellF1 de cada mètode (mitjana dels deu partits, nivell mitjà)

**spellF1 a la veritat de toc**

| escenari | A xarxes, decodificador de toc | A equips sencers | A neteja d'aire | A etiquetes al decodificador |
|---|---|---|---|---|
| net | 0.798 | 0.799 | 0.799 | 0.800 |
| curts ×¼ | 0.673 | 0.699 | 0.699 | 0.700 |
| llargs ×¼ | 0.651 | 0.688 | 0.688 | 0.690 |
| barreja ×¼ | 0.660 | 0.696 | 0.696 | 0.698 |
| aire ×¼ | 0.600 | 0.629 | 0.644 | 0.647 |
| curts | 0.636 | 0.665 | 0.665 | 0.667 |
| llargs | 0.599 | 0.640 | 0.640 | 0.642 |
| barreja | 0.605 | 0.646 | 0.646 | 0.649 |
| aire | 0.554 | 0.600 | 0.618 | 0.620 |
| soroll2 | 0.470 | 0.534 | 0.534 | 0.543 |
| partit ×¼ | 0.746 | 0.761 | 0.761 | 0.762 |

**spellF1 a la veritat de sempre**

| escenari | A xarxes, decodificador de toc | A equips sencers | A neteja d'aire | A etiquetes al decodificador |
|---|---|---|---|---|
| net | 0.808 | 0.810 | 0.810 | 0.811 |
| curts ×¼ | 0.684 | 0.708 | 0.708 | 0.709 |
| llargs ×¼ | 0.662 | 0.700 | 0.700 | 0.702 |
| barreja ×¼ | 0.671 | 0.708 | 0.708 | 0.709 |
| aire ×¼ | 0.612 | 0.643 | 0.658 | 0.661 |
| curts | 0.644 | 0.674 | 0.674 | 0.676 |
| llargs | 0.607 | 0.648 | 0.648 | 0.650 |
| barreja | 0.616 | 0.656 | 0.656 | 0.658 |
| aire | 0.564 | 0.613 | 0.632 | 0.633 |
| soroll2 | 0.478 | 0.543 | 0.543 | 0.552 |
| partit ×¼ | 0.757 | 0.772 | 0.772 | 0.773 |

## Els decodificadors

A neteja d'aire i A etiquetes al decodificador fan servir, a cada partit, el d'A equips sencers.

- **A equips sencers:** w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 16, durada mínima 12 (2 partits)
