# Banc obert · Les fases amb equip del Smart Tagging, al decodificador (T3ak)

Generat amb `uv run python -I -m banc.model_fases`. Dades obertes: 7 partits de DFL (IDSSE, CC BY 4.0)
i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el criteri:
`docs/pla-tocs.md`, «T3ak», i la capçalera de `banc/model_fases.py`. Es puntua a la veritat de toc.

**A xarxes, decodificador de toc** i **A equips sencers** són els de la T3v, **A pilota creïble**, el de la T3w, **A neteja d'aire**, el
de la T3ac, i **A pilota morta**, el de la T3ah (✓ comprovat). **A fases** és A pilota morta amb, dins de les fases
simulades de l'equip que té la pilota, l'altre equip i la D restats. ✓ Comprovat: no dona mai la D a una
imatge netejada; A pilota morta d'aquí dona l'spellF1 de la T3ah; sense etiquetes, exactament A neteja d'aire; i
sense fases, A fases és exactament A pilota morta.

## Amb el nivell mitjà: A fases contra A xarxes, decodificador de toc (spellF1), el criteri

| escenari | A xarxes, decodificador de toc | A fases | diferència | interval del 95 % | A fases guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.798 | 0.803 | +0.004 | -0.002 a +0.012 | 7 de 10 | no perd | ✓ |
| curts ×¼ | 0.673 | 0.711 | +0.038 | +0.031 a +0.046 | 10 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.651 | 0.704 | +0.053 | +0.045 a +0.061 | 10 de 10 | guanya clarament | ✓ |
| barreja ×¼ | 0.660 | 0.708 | +0.048 | +0.042 a +0.054 | 10 de 10 | guanya clarament | ✓ |
| aire ×¼ | 0.600 | 0.662 | +0.061 | +0.055 a +0.068 | 10 de 10 | guanya clarament | ✓ |
| curts | 0.636 | 0.679 | +0.044 | +0.038 a +0.049 | 10 de 10 | no perd | ✓ |
| llargs | 0.599 | 0.658 | +0.059 | +0.047 a +0.071 | 10 de 10 | no perd | ✓ |
| barreja | 0.605 | 0.660 | +0.055 | +0.044 a +0.065 | 10 de 10 | no perd | ✓ |
| aire | 0.554 | 0.635 | +0.080 | +0.075 a +0.085 | 10 de 10 | no perd | ✓ |
| soroll2 | 0.470 | 0.568 | +0.098 | +0.091 a +0.105 | 10 de 10 | no perd | ✓ |
| partit ×¼ | 0.746 | 0.772 | +0.027 | +0.017 a +0.035 | 10 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1, el soroll2 i «partit ×¼» | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## Amb els nivells dolent i cap: A fases contra A neteja d'aire, la segona part del criteri

| Nivell | curts ×¼ | llargs ×¼ | barreja ×¼ | aire ×¼ | partit ×¼ | No baixa de −0.005 |
|---|---|---|---|---|---|---|
| dolent | -0.0011 | -0.0010 | -0.0015 | +0.0004 | -0.0015 | ✓ |
| cap | +0.0000 | +0.0000 | +0.0000 | +0.0000 | +0.0000 | ✓ |

**A fases no passa el criteri sencer.**

## Amb el nivell bo: A fases contra A pilota morta (spellF1)

| escenari | A pilota morta | A fases | diferència | interval del 95 % | A fases guanya |
|---|---|---|---|---|---|
| net | 0.802 | 0.832 | +0.030 | +0.024 a +0.037 | 10 de 10 |
| curts ×¼ | 0.703 | 0.758 | +0.055 | +0.048 a +0.062 | 10 de 10 |
| llargs ×¼ | 0.694 | 0.753 | +0.059 | +0.055 a +0.063 | 10 de 10 |
| barreja ×¼ | 0.699 | 0.750 | +0.052 | +0.046 a +0.058 | 10 de 10 |
| aire ×¼ | 0.649 | 0.721 | +0.072 | +0.065 a +0.079 | 10 de 10 |
| curts | 0.669 | 0.737 | +0.069 | +0.063 a +0.074 | 10 de 10 |
| llargs | 0.645 | 0.716 | +0.072 | +0.068 a +0.075 | 10 de 10 |
| barreja | 0.650 | 0.720 | +0.070 | +0.064 a +0.076 | 10 de 10 |
| aire | 0.622 | 0.698 | +0.076 | +0.070 a +0.083 | 10 de 10 |
| soroll2 | 0.554 | 0.649 | +0.095 | +0.086 a +0.104 | 10 de 10 |
| partit ×¼ | 0.765 | 0.806 | +0.041 | +0.033 a +0.050 | 10 de 10 |

## Amb el nivell mitjà: A fases contra A pilota morta (spellF1)

| escenari | A pilota morta | A fases | diferència | interval del 95 % | A fases guanya |
|---|---|---|---|---|---|
| net | 0.801 | 0.803 | +0.001 | -0.003 a +0.006 | 7 de 10 |
| curts ×¼ | 0.702 | 0.711 | +0.009 | +0.004 a +0.014 | 8 de 10 |
| llargs ×¼ | 0.691 | 0.704 | +0.013 | +0.010 a +0.017 | 10 de 10 |
| barreja ×¼ | 0.698 | 0.708 | +0.010 | +0.005 a +0.015 | 9 de 10 |
| aire ×¼ | 0.647 | 0.662 | +0.015 | +0.012 a +0.018 | 10 de 10 |
| curts | 0.668 | 0.679 | +0.012 | +0.008 a +0.015 | 10 de 10 |
| llargs | 0.645 | 0.658 | +0.014 | +0.010 a +0.017 | 10 de 10 |
| barreja | 0.650 | 0.660 | +0.010 | +0.004 a +0.016 | 9 de 10 |
| aire | 0.620 | 0.635 | +0.015 | +0.009 a +0.021 | 9 de 10 |
| soroll2 | 0.549 | 0.568 | +0.019 | +0.015 a +0.025 | 10 de 10 |
| partit ×¼ | 0.764 | 0.772 | +0.008 | +0.000 a +0.016 | 8 de 10 |

## Amb el nivell dolent: A fases contra A pilota morta (spellF1)

| escenari | A pilota morta | A fases | diferència | interval del 95 % | A fases guanya |
|---|---|---|---|---|---|
| net | 0.801 | 0.797 | -0.004 | -0.007 a -0.002 | 1 de 10 |
| curts ×¼ | 0.702 | 0.698 | -0.004 | -0.007 a -0.000 | 3 de 10 |
| llargs ×¼ | 0.692 | 0.687 | -0.005 | -0.009 a -0.000 | 4 de 10 |
| barreja ×¼ | 0.697 | 0.695 | -0.002 | -0.008 a +0.002 | 5 de 10 |
| aire ×¼ | 0.648 | 0.644 | -0.003 | -0.008 a +0.002 | 5 de 10 |
| curts | 0.668 | 0.660 | -0.008 | -0.012 a -0.003 | 1 de 10 |
| llargs | 0.644 | 0.641 | -0.002 | -0.008 a +0.003 | 4 de 10 |
| barreja | 0.648 | 0.646 | -0.001 | -0.005 a +0.002 | 5 de 10 |
| aire | 0.618 | 0.614 | -0.005 | -0.010 a +0.001 | 4 de 10 |
| soroll2 | 0.547 | 0.546 | -0.001 | -0.006 a +0.003 | 6 de 10 |
| partit ×¼ | 0.763 | 0.760 | -0.003 | -0.006 a +0.000 | 4 de 10 |

## Amb el nivell cap: A fases contra A pilota morta (spellF1)

| escenari | A pilota morta | A fases | diferència | interval del 95 % | A fases guanya |
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

La regla de la D-50, escrita abans, contra A pilota morta amb el nivell mitjà, i la mateixa segona part
del criteri:

| | És el millor fins ara si | |
|---|---|---|
| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | ✓ |
| «partit ×¼» | la diferència no és negativa | ✓ |
| El net, els ×1 i el soroll2 | no perd (diferència ≥ −0.04) | ✓ |
| Dolent i cap | la segona part del criteri | ✓ |

**A fases és el millor fins ara:** el pas següent es fa a sobre d'A fases.

## A fases contra A xarxes, decodificador de toc, nivell mitjà, només els partits de dfl

| escenari | A xarxes, decodificador de toc | A fases | diferència | interval del 95 % | A fases guanya |
|---|---|---|---|---|---|
| net | 0.766 | 0.772 | +0.007 | +0.002 a +0.012 | 6 de 7 |
| curts ×¼ | 0.642 | 0.682 | +0.040 | +0.031 a +0.052 | 7 de 7 |
| llargs ×¼ | 0.621 | 0.674 | +0.054 | +0.044 a +0.062 | 7 de 7 |
| barreja ×¼ | 0.630 | 0.678 | +0.048 | +0.041 a +0.055 | 7 de 7 |
| aire ×¼ | 0.544 | 0.611 | +0.066 | +0.059 a +0.074 | 7 de 7 |
| curts | 0.607 | 0.651 | +0.043 | +0.037 a +0.050 | 7 de 7 |
| llargs | 0.564 | 0.623 | +0.059 | +0.042 a +0.077 | 7 de 7 |
| barreja | 0.571 | 0.623 | +0.052 | +0.044 a +0.060 | 7 de 7 |
| aire | 0.501 | 0.586 | +0.085 | +0.079 a +0.089 | 7 de 7 |
| soroll2 | 0.433 | 0.519 | +0.086 | +0.078 a +0.093 | 7 de 7 |
| partit ×¼ | 0.717 | 0.741 | +0.024 | +0.017 a +0.031 | 7 de 7 |

## A fases contra A pilota morta, nivell mitjà, només els partits de dfl

| escenari | A pilota morta | A fases | diferència | interval del 95 % | A fases guanya |
|---|---|---|---|---|---|
| net | 0.770 | 0.772 | +0.002 | -0.002 a +0.006 | 5 de 7 |
| curts ×¼ | 0.672 | 0.682 | +0.011 | +0.004 a +0.017 | 6 de 7 |
| llargs ×¼ | 0.659 | 0.674 | +0.015 | +0.011 a +0.020 | 7 de 7 |
| barreja ×¼ | 0.666 | 0.678 | +0.011 | +0.005 a +0.019 | 6 de 7 |
| aire ×¼ | 0.594 | 0.611 | +0.016 | +0.013 a +0.020 | 7 de 7 |
| curts | 0.640 | 0.651 | +0.010 | +0.007 a +0.013 | 7 de 7 |
| llargs | 0.608 | 0.623 | +0.016 | +0.010 a +0.021 | 7 de 7 |
| barreja | 0.611 | 0.623 | +0.013 | +0.004 a +0.021 | 6 de 7 |
| aire | 0.571 | 0.586 | +0.014 | +0.007 a +0.020 | 6 de 7 |
| soroll2 | 0.506 | 0.519 | +0.013 | +0.007 a +0.020 | 7 de 7 |
| partit ×¼ | 0.733 | 0.741 | +0.008 | +0.002 a +0.016 | 6 de 7 |

## A fases contra A xarxes, decodificador de toc, nivell mitjà, només els partits de metrica

| escenari | A xarxes, decodificador de toc | A fases | diferència | interval del 95 % | A fases guanya |
|---|---|---|---|---|---|
| net | 0.874 | 0.873 | -0.001 | -0.021 a +0.024 | 1 de 3 |
| curts ×¼ | 0.747 | 0.779 | +0.032 | +0.031 a +0.033 | 3 de 3 |
| llargs ×¼ | 0.723 | 0.775 | +0.052 | +0.042 a +0.069 | 3 de 3 |
| barreja ×¼ | 0.730 | 0.780 | +0.050 | +0.038 a +0.063 | 3 de 3 |
| aire ×¼ | 0.731 | 0.781 | +0.050 | +0.037 a +0.059 | 3 de 3 |
| curts | 0.702 | 0.747 | +0.044 | +0.032 a +0.053 | 3 de 3 |
| llargs | 0.682 | 0.740 | +0.058 | +0.055 a +0.064 | 3 de 3 |
| barreja | 0.684 | 0.746 | +0.062 | +0.027 a +0.088 | 3 de 3 |
| aire | 0.679 | 0.750 | +0.071 | +0.058 a +0.077 | 3 de 3 |
| soroll2 | 0.557 | 0.684 | +0.127 | +0.118 a +0.144 | 3 de 3 |
| partit ×¼ | 0.813 | 0.845 | +0.033 | +0.001 a +0.056 | 3 de 3 |

## A fases contra A pilota morta, nivell mitjà, només els partits de metrica

| escenari | A pilota morta | A fases | diferència | interval del 95 % | A fases guanya |
|---|---|---|---|---|---|
| net | 0.873 | 0.873 | +0.000 | -0.015 a +0.010 | 2 de 3 |
| curts ×¼ | 0.772 | 0.779 | +0.006 | -0.001 a +0.017 | 2 de 3 |
| llargs ×¼ | 0.766 | 0.775 | +0.009 | +0.005 a +0.013 | 3 de 3 |
| barreja ×¼ | 0.773 | 0.780 | +0.007 | +0.005 a +0.010 | 3 de 3 |
| aire ×¼ | 0.770 | 0.781 | +0.011 | +0.005 a +0.015 | 3 de 3 |
| curts | 0.732 | 0.747 | +0.015 | +0.005 a +0.026 | 3 de 3 |
| llargs | 0.731 | 0.740 | +0.010 | +0.007 a +0.012 | 3 de 3 |
| barreja | 0.742 | 0.746 | +0.004 | +0.001 a +0.008 | 3 de 3 |
| aire | 0.733 | 0.750 | +0.016 | +0.002 a +0.029 | 3 de 3 |
| soroll2 | 0.649 | 0.684 | +0.035 | +0.033 a +0.037 | 3 de 3 |
| partit ×¼ | 0.838 | 0.845 | +0.007 | -0.013 a +0.031 | 2 de 3 |

## A fases contra A xarxes, decodificador de toc, nivell bo

| escenari | A xarxes, decodificador de toc | A fases | diferència | interval del 95 % | A fases guanya |
|---|---|---|---|---|---|
| net | 0.798 | 0.832 | +0.034 | +0.025 a +0.044 | 10 de 10 |
| curts ×¼ | 0.673 | 0.758 | +0.084 | +0.074 a +0.097 | 10 de 10 |
| llargs ×¼ | 0.651 | 0.753 | +0.102 | +0.091 a +0.112 | 10 de 10 |
| barreja ×¼ | 0.660 | 0.750 | +0.090 | +0.082 a +0.099 | 10 de 10 |
| aire ×¼ | 0.600 | 0.721 | +0.121 | +0.112 a +0.130 | 10 de 10 |
| curts | 0.636 | 0.737 | +0.101 | +0.094 a +0.108 | 10 de 10 |
| llargs | 0.599 | 0.716 | +0.117 | +0.103 a +0.129 | 10 de 10 |
| barreja | 0.605 | 0.720 | +0.115 | +0.104 a +0.126 | 10 de 10 |
| aire | 0.554 | 0.698 | +0.144 | +0.135 a +0.152 | 10 de 10 |
| soroll2 | 0.470 | 0.649 | +0.179 | +0.171 a +0.189 | 10 de 10 |
| partit ×¼ | 0.746 | 0.806 | +0.061 | +0.049 a +0.071 | 10 de 10 |

## On falla, abans i després

Amb el nivell mitjà, les causes de `banc/on_falla.py`: la part de les possessions de la veritat de
cada causa, i les predites que sobren a l'altre equip per cada 100 possessions de la veritat.

**curts ×¼**

| causa | A pilota morta | A fases |
|---|---|---|
| encertada | 0.647 | 0.646 |
| engolida | 0.103 | 0.108 |
| l'altre equip | 0.026 | 0.029 |
| la D | 0.015 | 0.015 |
| trencada | 0.007 | 0.006 |
| ajuntada, per sobre de l'altre equip | 0.133 | 0.137 |
| ajuntada, per sobre de la D | 0.002 | 0.001 |
| les vores | 0.066 | 0.058 |
| sobren a l'altre equip, per cada 100 | 8.692 | 7.103 |

**els quatre ×¼ junts**

| causa | A pilota morta | A fases |
|---|---|---|
| encertada | 0.626 | 0.627 |
| engolida | 0.101 | 0.107 |
| l'altre equip | 0.029 | 0.031 |
| la D | 0.029 | 0.028 |
| trencada | 0.009 | 0.006 |
| ajuntada, per sobre de l'altre equip | 0.132 | 0.136 |
| ajuntada, per sobre de la D | 0.001 | 0.001 |
| les vores | 0.072 | 0.063 |
| sobren a l'altre equip, per cada 100 | 8.686 | 6.916 |

**net**

| causa | A pilota morta | A fases |
|---|---|---|
| encertada | 0.761 | 0.754 |
| engolida | 0.071 | 0.075 |
| l'altre equip | 0.020 | 0.022 |
| la D | 0.005 | 0.005 |
| trencada | 0.004 | 0.004 |
| ajuntada, per sobre de l'altre equip | 0.091 | 0.096 |
| ajuntada, per sobre de la D | 0.001 | 0.001 |
| les vores | 0.046 | 0.043 |
| sobren a l'altre equip, per cada 100 | 6.589 | 5.724 |

## Les fases simulades

A curts ×¼, amb les llavors de provar, la mitjana dels deu partits: quantes fases, i la part de les
imatges on se'n resta (dins d'una fase d'un sol equip, sense el marge triat).

| nivell | fases | part_dins |
|---|---|---|
| bo | 264.000 | 0.459 |
| mitjà | 141.800 | 0.285 |
| dolent | 100.600 | 0.193 |
| cap | 0.000 | 0.000 |

## El punt triat

A cada partit, amb els altres nou, als quatre ×¼ i a la mitjana dels nivells bo, mitjà i dolent.

| partit | gamma | delta | marge_s |
|---|---|---|---|
| dfl-J03WMX | 1 | 1 | 0 |
| dfl-J03WN1 | 1 | 1 | 0 |
| dfl-J03WOH | 1 | 1 | 0 |
| dfl-J03WOY | 1 | 1 | 0 |
| dfl-J03WPY | 1 | 1 | 0 |
| dfl-J03WQQ | 1 | 1 | 0 |
| dfl-J03WR9 | 1 | 1 | 0 |
| metrica-1 | 1 | 1 | 0 |
| metrica-2 | 1 | 1 | 0 |
| metrica-3 | 1 | 1 | 0 |

**A la vora de la graella:** gamma = 1, delta = 1, marge_s = 0.

## L'spellF1 de cada mètode (mitjana dels deu partits, nivell mitjà)

**spellF1 a la veritat de toc**

| escenari | A xarxes, decodificador de toc | A equips sencers | A neteja d'aire | A pilota morta | A fases |
|---|---|---|---|---|---|
| net | 0.798 | 0.799 | 0.799 | 0.801 | 0.803 |
| curts ×¼ | 0.673 | 0.699 | 0.699 | 0.702 | 0.711 |
| llargs ×¼ | 0.651 | 0.688 | 0.688 | 0.691 | 0.704 |
| barreja ×¼ | 0.660 | 0.696 | 0.696 | 0.698 | 0.708 |
| aire ×¼ | 0.600 | 0.629 | 0.644 | 0.647 | 0.662 |
| curts | 0.636 | 0.665 | 0.665 | 0.668 | 0.679 |
| llargs | 0.599 | 0.640 | 0.640 | 0.645 | 0.658 |
| barreja | 0.605 | 0.646 | 0.646 | 0.650 | 0.660 |
| aire | 0.554 | 0.600 | 0.618 | 0.620 | 0.635 |
| soroll2 | 0.470 | 0.534 | 0.534 | 0.549 | 0.568 |
| partit ×¼ | 0.746 | 0.761 | 0.761 | 0.764 | 0.772 |

**spellF1 a la veritat de sempre**

| escenari | A xarxes, decodificador de toc | A equips sencers | A neteja d'aire | A pilota morta | A fases |
|---|---|---|---|---|---|
| net | 0.808 | 0.810 | 0.810 | 0.812 | 0.814 |
| curts ×¼ | 0.684 | 0.708 | 0.708 | 0.711 | 0.720 |
| llargs ×¼ | 0.662 | 0.700 | 0.700 | 0.703 | 0.717 |
| barreja ×¼ | 0.671 | 0.708 | 0.708 | 0.710 | 0.720 |
| aire ×¼ | 0.612 | 0.643 | 0.658 | 0.661 | 0.677 |
| curts | 0.644 | 0.674 | 0.674 | 0.677 | 0.689 |
| llargs | 0.607 | 0.648 | 0.648 | 0.652 | 0.667 |
| barreja | 0.616 | 0.656 | 0.656 | 0.660 | 0.670 |
| aire | 0.564 | 0.613 | 0.632 | 0.633 | 0.648 |
| soroll2 | 0.478 | 0.543 | 0.543 | 0.558 | 0.577 |
| partit ×¼ | 0.757 | 0.772 | 0.772 | 0.775 | 0.782 |

## Els decodificadors

A neteja d'aire, A pilota morta i A fases fan servir, a cada partit, el d'A equips sencers.

- **A equips sencers:** w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 16, durada mínima 12 (2 partits)
