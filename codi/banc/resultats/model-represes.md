# Banc obert · Un segon només per a les represes (T3ai)

Generat amb `uv run python -I -m banc.model_represes`. Dades obertes: 7 partits de DFL (IDSSE,
CC BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3ai», i la capçalera de `banc/model_represes.py`. Es puntua a la
veritat de toc.

**A xarxes, decodificador de toc** i **A equips sencers** són els de la T3v, **A pilota creïble**, el de la T3w, **A neteja d'aire**, el
de la T3ac, i **A pilota morta**, el de la T3ah (✓ comprovat). **A represes** és A pilota morta amb, a l'entorn de cada
etiqueta, la probabilitat relativa del segon de les represes barrejada. ✓ Comprovat: no dona mai la D a
una imatge netejada, i sense etiquetes dona exactament A neteja d'aire.

## Amb el nivell mitjà: A represes contra A xarxes, decodificador de toc (spellF1), el criteri

| escenari | A xarxes, decodificador de toc | A represes | diferència | interval del 95 % | A represes guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.798 | 0.802 | +0.003 | -0.002 a +0.010 | 7 de 10 | no perd | ✓ |
| curts ×¼ | 0.673 | 0.702 | +0.028 | +0.023 a +0.035 | 10 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.651 | 0.691 | +0.039 | +0.031 a +0.048 | 10 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.660 | 0.699 | +0.039 | +0.033 a +0.045 | 10 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.600 | 0.647 | +0.047 | +0.041 a +0.054 | 10 de 10 | guanya clarament | ✓ |
| curts | 0.636 | 0.668 | +0.032 | +0.026 a +0.038 | 10 de 10 | no perd | ✓ |
| llargs | 0.599 | 0.644 | +0.045 | +0.033 a +0.057 | 10 de 10 | no perd | ✓ |
| barreja | 0.605 | 0.652 | +0.047 | +0.036 a +0.058 | 10 de 10 | no perd | ✓ |
| aire | 0.554 | 0.622 | +0.068 | +0.061 a +0.074 | 10 de 10 | no perd | ✓ |
| soroll2 | 0.470 | 0.550 | +0.079 | +0.072 a +0.087 | 10 de 10 | no perd | ✓ |
| partit ×¼ | 0.746 | 0.764 | +0.018 | +0.012 a +0.025 | 10 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1, el soroll2 i «partit ×¼» | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## Amb els nivells dolent i cap: A represes contra A neteja d'aire, la segona part del criteri

| Nivell | curts ×¼ | llargs ×¼ | barreja ×¼ | aire ×¼ | partit ×¼ | No baixa de −0.005 |
|---|---|---|---|---|---|---|
| dolent | +0.0032 | +0.0032 | +0.0004 | +0.0041 | +0.0010 | ✓ |
| cap | +0.0000 | +0.0000 | +0.0000 | +0.0000 | +0.0000 | ✓ |

**A represes no passa el criteri sencer.**

## Amb el nivell bo: A represes contra A pilota morta (spellF1)

| escenari | A pilota morta | A represes | diferència | interval del 95 % | A represes guanya |
|---|---|---|---|---|---|
| net | 0.802 | 0.803 | +0.001 | -0.000 a +0.002 | 6 de 10 |
| curts ×¼ | 0.703 | 0.703 | +0.000 | -0.001 a +0.002 | 6 de 10 |
| llargs ×¼ | 0.694 | 0.694 | -0.000 | -0.002 a +0.002 | 6 de 10 |
| barreja ×¼ | 0.699 | 0.700 | +0.001 | +0.000 a +0.002 | 9 de 10 |
| aire ×¼ | 0.649 | 0.649 | -0.001 | -0.003 a +0.002 | 6 de 10 |
| curts | 0.669 | 0.670 | +0.001 | -0.001 a +0.003 | 6 de 10 |
| llargs | 0.645 | 0.644 | -0.001 | -0.002 a +0.001 | 3 de 10 |
| barreja | 0.650 | 0.653 | +0.003 | -0.000 a +0.005 | 7 de 10 |
| aire | 0.622 | 0.626 | +0.004 | +0.002 a +0.007 | 9 de 10 |
| soroll2 | 0.554 | 0.555 | +0.001 | -0.001 a +0.004 | 5 de 10 |
| partit ×¼ | 0.765 | 0.763 | -0.001 | -0.002 a +0.000 | 3 de 10 |

## Amb el nivell mitjà: A represes contra A pilota morta (spellF1)

| escenari | A pilota morta | A represes | diferència | interval del 95 % | A represes guanya |
|---|---|---|---|---|---|
| net | 0.801 | 0.802 | +0.000 | -0.001 a +0.002 | 4 de 10 |
| curts ×¼ | 0.702 | 0.702 | -0.000 | -0.001 a +0.001 | 5 de 10 |
| llargs ×¼ | 0.691 | 0.691 | -0.001 | -0.002 a +0.001 | 3 de 10 |
| barreja ×¼ | 0.698 | 0.699 | +0.001 | -0.001 a +0.002 | 4 de 10 |
| aire ×¼ | 0.647 | 0.647 | +0.000 | -0.003 a +0.003 | 5 de 10 |
| curts | 0.668 | 0.668 | +0.000 | -0.002 a +0.002 | 7 de 10 |
| llargs | 0.645 | 0.644 | -0.001 | -0.002 a +0.001 | 3 de 10 |
| barreja | 0.650 | 0.652 | +0.002 | -0.000 a +0.004 | 8 de 10 |
| aire | 0.620 | 0.622 | +0.002 | +0.001 a +0.004 | 7 de 10 |
| soroll2 | 0.549 | 0.550 | +0.001 | -0.002 a +0.002 | 6 de 10 |
| partit ×¼ | 0.764 | 0.764 | -0.000 | -0.001 a +0.001 | 4 de 10 |

## Amb el nivell dolent: A represes contra A pilota morta (spellF1)

| escenari | A pilota morta | A represes | diferència | interval del 95 % | A represes guanya |
|---|---|---|---|---|---|
| net | 0.801 | 0.801 | +0.000 | -0.002 a +0.002 | 4 de 10 |
| curts ×¼ | 0.702 | 0.702 | +0.001 | -0.000 a +0.001 | 8 de 10 |
| llargs ×¼ | 0.692 | 0.691 | -0.000 | -0.002 a +0.001 | 4 de 10 |
| barreja ×¼ | 0.697 | 0.697 | -0.000 | -0.002 a +0.001 | 4 de 10 |
| aire ×¼ | 0.648 | 0.648 | +0.001 | -0.001 a +0.002 | 5 de 10 |
| curts | 0.668 | 0.667 | -0.001 | -0.002 a +0.000 | 3 de 10 |
| llargs | 0.644 | 0.645 | +0.001 | -0.000 a +0.002 | 8 de 10 |
| barreja | 0.648 | 0.648 | +0.001 | -0.001 a +0.003 | 5 de 10 |
| aire | 0.618 | 0.620 | +0.001 | -0.001 a +0.003 | 5 de 10 |
| soroll2 | 0.547 | 0.547 | -0.001 | -0.002 a +0.000 | 4 de 10 |
| partit ×¼ | 0.763 | 0.762 | -0.000 | -0.001 a +0.000 | 3 de 10 |

## Amb el nivell cap: A represes contra A pilota morta (spellF1)

| escenari | A pilota morta | A represes | diferència | interval del 95 % | A represes guanya |
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
| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | ✗ |
| «partit ×¼» | la diferència no és negativa | ✗ |
| El net, els ×1 i el soroll2 | no perd (diferència ≥ −0.04) | ✓ |
| Dolent i cap | la segona part del criteri | ✓ |

**A represes no és el millor fins ara:** el pas següent es fa a sobre d'A pilota morta.

## A represes contra A xarxes, decodificador de toc, nivell mitjà, només els partits de dfl

| escenari | A xarxes, decodificador de toc | A represes | diferència | interval del 95 % | A represes guanya |
|---|---|---|---|---|---|
| net | 0.766 | 0.771 | +0.005 | -0.000 a +0.012 | 6 de 7 |
| curts ×¼ | 0.642 | 0.671 | +0.029 | +0.023 a +0.038 | 7 de 7 |
| llargs ×¼ | 0.621 | 0.659 | +0.038 | +0.028 a +0.048 | 7 de 7 |
| barreja ×¼ | 0.630 | 0.667 | +0.037 | +0.031 a +0.043 | 7 de 7 |
| aire ×¼ | 0.544 | 0.595 | +0.051 | +0.044 a +0.059 | 7 de 7 |
| curts | 0.607 | 0.640 | +0.033 | +0.025 a +0.040 | 7 de 7 |
| llargs | 0.564 | 0.608 | +0.044 | +0.027 a +0.061 | 7 de 7 |
| barreja | 0.571 | 0.613 | +0.042 | +0.031 a +0.053 | 7 de 7 |
| aire | 0.501 | 0.575 | +0.074 | +0.064 a +0.083 | 7 de 7 |
| soroll2 | 0.433 | 0.507 | +0.073 | +0.066 a +0.080 | 7 de 7 |
| partit ×¼ | 0.717 | 0.733 | +0.016 | +0.008 a +0.025 | 7 de 7 |

## A represes contra A pilota morta, nivell mitjà, només els partits de dfl

| escenari | A pilota morta | A represes | diferència | interval del 95 % | A represes guanya |
|---|---|---|---|---|---|
| net | 0.770 | 0.771 | +0.001 | -0.001 a +0.002 | 3 de 7 |
| curts ×¼ | 0.672 | 0.671 | -0.000 | -0.002 a +0.001 | 3 de 7 |
| llargs ×¼ | 0.659 | 0.659 | -0.001 | -0.002 a +0.001 | 2 de 7 |
| barreja ×¼ | 0.666 | 0.667 | +0.001 | -0.001 a +0.003 | 3 de 7 |
| aire ×¼ | 0.594 | 0.595 | +0.001 | -0.003 a +0.005 | 4 de 7 |
| curts | 0.640 | 0.640 | -0.000 | -0.003 a +0.002 | 4 de 7 |
| llargs | 0.608 | 0.608 | -0.000 | -0.002 a +0.002 | 3 de 7 |
| barreja | 0.611 | 0.613 | +0.003 | +0.000 a +0.005 | 6 de 7 |
| aire | 0.571 | 0.575 | +0.004 | +0.001 a +0.006 | 6 de 7 |
| soroll2 | 0.506 | 0.507 | +0.000 | -0.001 a +0.001 | 4 de 7 |
| partit ×¼ | 0.733 | 0.733 | -0.000 | -0.002 a +0.001 | 3 de 7 |

## A represes contra A xarxes, decodificador de toc, nivell mitjà, només els partits de metrica

| escenari | A xarxes, decodificador de toc | A represes | diferència | interval del 95 % | A represes guanya |
|---|---|---|---|---|---|
| net | 0.874 | 0.873 | -0.001 | -0.010 a +0.014 | 1 de 3 |
| curts ×¼ | 0.747 | 0.773 | +0.026 | +0.014 a +0.033 | 3 de 3 |
| llargs ×¼ | 0.723 | 0.765 | +0.042 | +0.031 a +0.062 | 3 de 3 |
| barreja ×¼ | 0.730 | 0.773 | +0.043 | +0.034 a +0.059 | 3 de 3 |
| aire ×¼ | 0.731 | 0.768 | +0.037 | +0.024 a +0.053 | 3 de 3 |
| curts | 0.702 | 0.733 | +0.031 | +0.022 a +0.044 | 3 de 3 |
| llargs | 0.682 | 0.729 | +0.047 | +0.044 a +0.052 | 3 de 3 |
| barreja | 0.684 | 0.743 | +0.058 | +0.027 a +0.074 | 3 de 3 |
| aire | 0.679 | 0.733 | +0.054 | +0.047 a +0.060 | 3 de 3 |
| soroll2 | 0.557 | 0.650 | +0.093 | +0.076 a +0.118 | 3 de 3 |
| partit ×¼ | 0.813 | 0.838 | +0.025 | +0.014 a +0.036 | 3 de 3 |

## A represes contra A pilota morta, nivell mitjà, només els partits de metrica

| escenari | A pilota morta | A represes | diferència | interval del 95 % | A represes guanya |
|---|---|---|---|---|---|
| net | 0.873 | 0.873 | +0.000 | -0.001 a +0.002 | 1 de 3 |
| curts ×¼ | 0.772 | 0.773 | +0.000 | -0.003 a +0.002 | 2 de 3 |
| llargs ×¼ | 0.766 | 0.765 | -0.000 | -0.003 a +0.002 | 1 de 3 |
| barreja ×¼ | 0.773 | 0.773 | -0.000 | -0.003 a +0.002 | 1 de 3 |
| aire ×¼ | 0.770 | 0.768 | -0.001 | -0.004 a +0.001 | 1 de 3 |
| curts | 0.732 | 0.733 | +0.001 | +0.000 a +0.003 | 3 de 3 |
| llargs | 0.731 | 0.729 | -0.002 | -0.004 a -0.000 | 0 de 3 |
| barreja | 0.742 | 0.743 | +0.001 | -0.006 a +0.004 | 2 de 3 |
| aire | 0.733 | 0.733 | -0.000 | -0.001 a +0.001 | 1 de 3 |
| soroll2 | 0.649 | 0.650 | +0.001 | -0.006 a +0.007 | 2 de 3 |
| partit ×¼ | 0.838 | 0.838 | +0.000 | +0.000 a +0.000 | 1 de 3 |

## A represes contra A xarxes, decodificador de toc, nivell bo

| escenari | A xarxes, decodificador de toc | A represes | diferència | interval del 95 % | A represes guanya |
|---|---|---|---|---|---|
| net | 0.798 | 0.803 | +0.005 | -0.000 a +0.011 | 7 de 10 |
| curts ×¼ | 0.673 | 0.703 | +0.030 | +0.024 a +0.037 | 10 de 10 |
| llargs ×¼ | 0.651 | 0.694 | +0.043 | +0.035 a +0.050 | 10 de 10 |
| barreja ×¼ | 0.660 | 0.700 | +0.040 | +0.034 a +0.046 | 10 de 10 |
| aire ×¼ | 0.600 | 0.649 | +0.048 | +0.042 a +0.055 | 10 de 10 |
| curts | 0.636 | 0.670 | +0.034 | +0.028 a +0.041 | 10 de 10 |
| llargs | 0.599 | 0.644 | +0.044 | +0.032 a +0.058 | 10 de 10 |
| barreja | 0.605 | 0.653 | +0.048 | +0.038 a +0.056 | 10 de 10 |
| aire | 0.554 | 0.626 | +0.072 | +0.066 a +0.078 | 10 de 10 |
| soroll2 | 0.470 | 0.555 | +0.085 | +0.076 a +0.094 | 10 de 10 |
| partit ×¼ | 0.746 | 0.763 | +0.018 | +0.011 a +0.025 | 10 de 10 |

## Els errors a l'entorn de les represes

Amb el nivell mitjà, la part de les imatges vàlides de cada tram, segons on són respecte de la
represa de veritat. «Diu un equip i és D» vol dir que la predicció (amb les abstencions omplertes) és
un equip i la veritat de toc és la D.

**curts ×¼**

| tram | A pilota morta · bé | A pilota morta · diu un equip i és D | A pilota morta · diu D i és un equip | A pilota morta · l'altre equip | A represes · bé | A represes · diu un equip i és D | A represes · diu D i és un equip | A represes · l'altre equip |
|---|---|---|---|---|---|---|---|---|
| -10 a -5 s | 0.957 | 0.013 | 0.009 | 0.020 | 0.957 | 0.014 | 0.009 | 0.020 |
| -5 a -2 s | 0.969 | 0.023 | 0.003 | 0.005 | 0.970 | 0.022 | 0.003 | 0.005 |
| -2 a 0 s | 0.926 | 0.074 | 0.000 | 0.000 | 0.927 | 0.072 | 0.000 | 0.000 |
| 0 a 1 s | 0.917 | 0.000 | 0.076 | 0.007 | 0.921 | 0.001 | 0.073 | 0.006 |
| 1 a 3 s | 0.908 | 0.007 | 0.014 | 0.070 | 0.908 | 0.007 | 0.016 | 0.069 |
| 3 a 5 s | 0.866 | 0.013 | 0.005 | 0.116 | 0.864 | 0.014 | 0.006 | 0.116 |
| 5 a 10 s | 0.911 | 0.010 | 0.005 | 0.073 | 0.912 | 0.011 | 0.004 | 0.073 |

**els quatre ×¼ junts**

| tram | A pilota morta · bé | A pilota morta · diu un equip i és D | A pilota morta · diu D i és un equip | A pilota morta · l'altre equip | A represes · bé | A represes · diu un equip i és D | A represes · diu D i és un equip | A represes · l'altre equip |
|---|---|---|---|---|---|---|---|---|
| -10 a -5 s | 0.950 | 0.016 | 0.013 | 0.021 | 0.950 | 0.016 | 0.013 | 0.021 |
| -5 a -2 s | 0.957 | 0.033 | 0.004 | 0.006 | 0.961 | 0.029 | 0.004 | 0.006 |
| -2 a 0 s | 0.902 | 0.096 | 0.001 | 0.001 | 0.905 | 0.093 | 0.001 | 0.001 |
| 0 a 1 s | 0.888 | 0.001 | 0.105 | 0.007 | 0.892 | 0.001 | 0.100 | 0.007 |
| 1 a 3 s | 0.889 | 0.007 | 0.032 | 0.073 | 0.892 | 0.007 | 0.029 | 0.073 |
| 3 a 5 s | 0.854 | 0.014 | 0.018 | 0.114 | 0.855 | 0.015 | 0.016 | 0.114 |
| 5 a 10 s | 0.898 | 0.012 | 0.015 | 0.074 | 0.898 | 0.012 | 0.015 | 0.075 |

## La part del sostre de la T3af que se n'aprofita

A la veritat de toc, la mitjana dels deu partits: el sostre de la T3af menys A neteja d'aire, el que en
treu A represes, i la part.

| escenari | sostre · bo | sostre · mitjà | sostre · dolent | treu · bo | treu · mitjà | treu · dolent | part · bo | part · mitjà | part · dolent |
|---|---|---|---|---|---|---|---|---|---|
| net | 0.021 | 0.019 | 0.011 | 0.003 | 0.002 | 0.002 | 0.165 | 0.115 | 0.138 |
| curts ×¼ | 0.034 | 0.027 | 0.020 | 0.004 | 0.003 | 0.003 | 0.127 | 0.096 | 0.164 |
| llargs ×¼ | 0.041 | 0.031 | 0.027 | 0.006 | 0.003 | 0.003 | 0.150 | 0.089 | 0.120 |
| barreja ×¼ | 0.036 | 0.029 | 0.019 | 0.003 | 0.003 | 0.000 | 0.093 | 0.088 | 0.023 |
| aire ×¼ | 0.045 | 0.037 | 0.024 | 0.005 | 0.003 | 0.004 | 0.101 | 0.080 | 0.171 |
| curts | 0.040 | 0.028 | 0.023 | 0.005 | 0.003 | 0.002 | 0.127 | 0.112 | 0.086 |
| llargs | 0.048 | 0.037 | 0.029 | 0.003 | 0.004 | 0.004 | 0.072 | 0.101 | 0.151 |
| barreja | 0.044 | 0.034 | 0.031 | 0.007 | 0.006 | 0.002 | 0.148 | 0.168 | 0.069 |
| aire | 0.049 | 0.037 | 0.027 | 0.009 | 0.005 | 0.002 | 0.176 | 0.127 | 0.083 |
| soroll2 | 0.090 | 0.070 | 0.052 | 0.021 | 0.015 | 0.012 | 0.232 | 0.220 | 0.238 |
| partit ×¼ | 0.024 | 0.020 | 0.014 | 0.002 | 0.003 | 0.001 | 0.099 | 0.152 | 0.070 |

## A 5 s o menys de cada represa

La part de les imatges vàlides a 5 s o menys d'una represa on la predicció (amb les abstencions
omplertes) és la veritat de toc.

| escenari | A neteja d'aire | A pilota morta, bo | A pilota morta, mitjà | A pilota morta, dolent | A represes, bo | A represes, mitjà | A represes, dolent |
|---|---|---|---|---|---|---|---|
| net | 0.953 | 0.956 | 0.956 | 0.955 | 0.958 | 0.957 | 0.956 |
| curts ×¼ | 0.918 | 0.926 | 0.923 | 0.922 | 0.928 | 0.923 | 0.923 |
| llargs ×¼ | 0.892 | 0.905 | 0.899 | 0.898 | 0.911 | 0.902 | 0.897 |
| barreja ×¼ | 0.901 | 0.911 | 0.908 | 0.905 | 0.916 | 0.911 | 0.906 |
| aire ×¼ | 0.886 | 0.895 | 0.892 | 0.890 | 0.901 | 0.896 | 0.893 |
| curts | 0.900 | 0.911 | 0.907 | 0.905 | 0.913 | 0.909 | 0.906 |
| llargs | 0.873 | 0.885 | 0.881 | 0.881 | 0.890 | 0.884 | 0.884 |
| barreja | 0.878 | 0.889 | 0.886 | 0.883 | 0.896 | 0.891 | 0.885 |
| aire | 0.870 | 0.878 | 0.872 | 0.871 | 0.886 | 0.876 | 0.874 |
| soroll2 | 0.750 | 0.796 | 0.783 | 0.775 | 0.805 | 0.789 | 0.776 |
| partit ×¼ | 0.944 | 0.949 | 0.947 | 0.946 | 0.949 | 0.948 | 0.946 |

## L'alfa triat

A cada partit, amb els altres nou, als quatre ×¼ i a la mitjana dels nivells bo, mitjà i dolent.

| partit | alfa |
|---|---|
| dfl-J03WMX | 0.25 |
| dfl-J03WN1 | 0.25 |
| dfl-J03WOH | 0.25 |
| dfl-J03WOY | 0.25 |
| dfl-J03WPY | 0.5 |
| dfl-J03WQQ | 0.25 |
| dfl-J03WR9 | 0.25 |
| metrica-1 | 0.25 |
| metrica-2 | 0.25 |
| metrica-3 | 0.25 |

Cap partit no tria a la vora de la graella.

## El segon de les represes

Les mostres de cada un (amb les girades): de 141176 a 157014. Les 17 columnes del Smart Tagging hi fan el 2.6 % del
guany. Les 15 columnes que més hi fan (la part del guany, a la mitjana dels deu):

| columna | part |
|---|---|
| `morta` | 0.161 |
| `px_a` | 0.091 |
| `morta@5` | 0.083 |
| `px_h` | 0.057 |
| `px_h@max25` | 0.043 |
| `p_h@max25` | 0.041 |
| `p_a@max25` | 0.035 |
| `dif_px@5` | 0.034 |
| `dif_px@13` | 0.031 |
| `px_a@max25` | 0.031 |
| `dif_p` | 0.029 |
| `morta@13` | 0.025 |
| `dif_p@5` | 0.014 |
| `st_abans_s` | 0.009 |
| `morta@-5` | 0.008 |

## L'spellF1 de cada mètode (mitjana dels deu partits, nivell mitjà)

**spellF1 a la veritat de toc**

| escenari | A xarxes, decodificador de toc | A equips sencers | A neteja d'aire | A pilota morta | A represes |
|---|---|---|---|---|---|
| net | 0.798 | 0.799 | 0.799 | 0.801 | 0.802 |
| curts ×¼ | 0.673 | 0.699 | 0.699 | 0.702 | 0.702 |
| llargs ×¼ | 0.651 | 0.688 | 0.688 | 0.691 | 0.691 |
| barreja ×¼ | 0.660 | 0.696 | 0.696 | 0.698 | 0.699 |
| aire ×¼ | 0.600 | 0.629 | 0.644 | 0.647 | 0.647 |
| curts | 0.636 | 0.665 | 0.665 | 0.668 | 0.668 |
| llargs | 0.599 | 0.640 | 0.640 | 0.645 | 0.644 |
| barreja | 0.605 | 0.646 | 0.646 | 0.650 | 0.652 |
| aire | 0.554 | 0.600 | 0.618 | 0.620 | 0.622 |
| soroll2 | 0.470 | 0.534 | 0.534 | 0.549 | 0.550 |
| partit ×¼ | 0.746 | 0.761 | 0.761 | 0.764 | 0.764 |

**spellF1 a la veritat de sempre**

| escenari | A xarxes, decodificador de toc | A equips sencers | A neteja d'aire | A pilota morta | A represes |
|---|---|---|---|---|---|
| net | 0.808 | 0.810 | 0.810 | 0.812 | 0.813 |
| curts ×¼ | 0.684 | 0.708 | 0.708 | 0.711 | 0.710 |
| llargs ×¼ | 0.662 | 0.700 | 0.700 | 0.703 | 0.702 |
| barreja ×¼ | 0.671 | 0.708 | 0.708 | 0.710 | 0.710 |
| aire ×¼ | 0.612 | 0.643 | 0.658 | 0.661 | 0.661 |
| curts | 0.644 | 0.674 | 0.674 | 0.677 | 0.677 |
| llargs | 0.607 | 0.648 | 0.648 | 0.652 | 0.652 |
| barreja | 0.616 | 0.656 | 0.656 | 0.660 | 0.662 |
| aire | 0.564 | 0.613 | 0.632 | 0.633 | 0.635 |
| soroll2 | 0.478 | 0.543 | 0.543 | 0.558 | 0.560 |
| partit ×¼ | 0.757 | 0.772 | 0.772 | 0.775 | 0.776 |

## Els decodificadors

A neteja d'aire, A pilota morta i A represes fan servir, a cada partit, el d'A equips sencers.

- **A equips sencers:** w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 16, durada mínima 12 (2 partits)
