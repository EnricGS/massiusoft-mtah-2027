# Banc obert · Un detector de les possessions engolides (T3aj)

Generat amb `uv run python -I -m banc.model_engolides`. Dades obertes: 7 partits de DFL (IDSSE,
CC BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3aj», i la capçalera de `banc/model_engolides.py`. Es puntua a la
veritat de toc.

**A xarxes, decodificador de toc** i **A equips sencers** són els de la T3v, **A pilota creïble**, el de la T3w, **A neteja d'aire**, el
de la T3ac, i **A pilota morta**, el de la T3ah (✓ comprovat). **A engolides** és A pilota morta amb, dins de les
possessions predites, la del detector sumada a l'altre equip. ✓ Comprovat: no dona mai la D a una
imatge netejada; amb beta = 0 dona l'spellF1 d'A pilota morta de la T3ah, i sense etiquetes, exactament
A neteja d'aire.

## Amb el nivell mitjà: A engolides contra A xarxes, decodificador de toc (spellF1), el criteri

| escenari | A xarxes, decodificador de toc | A engolides | diferència | interval del 95 % | A engolides guanya | criteri | |
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

## Amb els nivells dolent i cap: A engolides contra A neteja d'aire, la segona part del criteri

| Nivell | curts ×¼ | llargs ×¼ | barreja ×¼ | aire ×¼ | partit ×¼ | No baixa de −0.005 |
|---|---|---|---|---|---|---|
| dolent | +0.0026 | +0.0035 | +0.0008 | +0.0035 | +0.0014 | ✓ |
| cap | +0.0000 | +0.0000 | +0.0000 | +0.0000 | +0.0000 | ✓ |

**A engolides no passa el criteri sencer.**

## Amb el nivell bo: A engolides contra A pilota morta (spellF1)

| escenari | A pilota morta | A engolides | diferència | interval del 95 % | A engolides guanya |
|---|---|---|---|---|---|
| net | 0.802 | 0.802 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| curts ×¼ | 0.703 | 0.703 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| llargs ×¼ | 0.694 | 0.694 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| barreja ×¼ | 0.699 | 0.699 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| aire ×¼ | 0.649 | 0.649 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| curts | 0.669 | 0.669 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| llargs | 0.645 | 0.645 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| barreja | 0.650 | 0.650 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| aire | 0.622 | 0.622 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| soroll2 | 0.554 | 0.554 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| partit ×¼ | 0.765 | 0.765 | +0.000 | +0.000 a +0.000 | 0 de 10 |

## Amb el nivell mitjà: A engolides contra A pilota morta (spellF1)

| escenari | A pilota morta | A engolides | diferència | interval del 95 % | A engolides guanya |
|---|---|---|---|---|---|
| net | 0.801 | 0.801 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| curts ×¼ | 0.702 | 0.702 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| llargs ×¼ | 0.691 | 0.691 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| barreja ×¼ | 0.698 | 0.698 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| aire ×¼ | 0.647 | 0.647 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| curts | 0.668 | 0.668 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| llargs | 0.645 | 0.645 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| barreja | 0.650 | 0.650 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| aire | 0.620 | 0.620 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| soroll2 | 0.549 | 0.549 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| partit ×¼ | 0.764 | 0.764 | +0.000 | +0.000 a +0.000 | 0 de 10 |

## Amb el nivell dolent: A engolides contra A pilota morta (spellF1)

| escenari | A pilota morta | A engolides | diferència | interval del 95 % | A engolides guanya |
|---|---|---|---|---|---|
| net | 0.801 | 0.801 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| curts ×¼ | 0.702 | 0.702 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| llargs ×¼ | 0.692 | 0.692 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| barreja ×¼ | 0.697 | 0.697 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| aire ×¼ | 0.648 | 0.648 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| curts | 0.668 | 0.668 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| llargs | 0.644 | 0.644 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| barreja | 0.648 | 0.648 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| aire | 0.618 | 0.618 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| soroll2 | 0.547 | 0.547 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| partit ×¼ | 0.763 | 0.763 | +0.000 | +0.000 a +0.000 | 0 de 10 |

## Amb el nivell cap: A engolides contra A pilota morta (spellF1)

| escenari | A pilota morta | A engolides | diferència | interval del 95 % | A engolides guanya |
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
| «partit ×¼» | la diferència no és negativa | ✓ |
| El net, els ×1 i el soroll2 | no perd (diferència ≥ −0.04) | ✓ |
| Dolent i cap | la segona part del criteri | ✓ |

**A engolides no és el millor fins ara:** el pas següent es fa a sobre d'A pilota morta.

## A engolides contra A xarxes, decodificador de toc, nivell mitjà, només els partits de dfl

| escenari | A xarxes, decodificador de toc | A engolides | diferència | interval del 95 % | A engolides guanya |
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

## A engolides contra A pilota morta, nivell mitjà, només els partits de dfl

| escenari | A pilota morta | A engolides | diferència | interval del 95 % | A engolides guanya |
|---|---|---|---|---|---|
| net | 0.770 | 0.770 | +0.000 | +0.000 a +0.000 | 0 de 7 |
| curts ×¼ | 0.672 | 0.672 | +0.000 | +0.000 a +0.000 | 0 de 7 |
| llargs ×¼ | 0.659 | 0.659 | +0.000 | +0.000 a +0.000 | 0 de 7 |
| barreja ×¼ | 0.666 | 0.666 | +0.000 | +0.000 a +0.000 | 0 de 7 |
| aire ×¼ | 0.594 | 0.594 | +0.000 | +0.000 a +0.000 | 0 de 7 |
| curts | 0.640 | 0.640 | +0.000 | +0.000 a +0.000 | 0 de 7 |
| llargs | 0.608 | 0.608 | +0.000 | +0.000 a +0.000 | 0 de 7 |
| barreja | 0.611 | 0.611 | +0.000 | +0.000 a +0.000 | 0 de 7 |
| aire | 0.571 | 0.571 | +0.000 | +0.000 a +0.000 | 0 de 7 |
| soroll2 | 0.506 | 0.506 | +0.000 | +0.000 a +0.000 | 0 de 7 |
| partit ×¼ | 0.733 | 0.733 | +0.000 | +0.000 a +0.000 | 0 de 7 |

## A engolides contra A xarxes, decodificador de toc, nivell mitjà, només els partits de metrica

| escenari | A xarxes, decodificador de toc | A engolides | diferència | interval del 95 % | A engolides guanya |
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

## A engolides contra A pilota morta, nivell mitjà, només els partits de metrica

| escenari | A pilota morta | A engolides | diferència | interval del 95 % | A engolides guanya |
|---|---|---|---|---|---|
| net | 0.873 | 0.873 | +0.000 | +0.000 a +0.000 | 0 de 3 |
| curts ×¼ | 0.772 | 0.772 | +0.000 | +0.000 a +0.000 | 0 de 3 |
| llargs ×¼ | 0.766 | 0.766 | +0.000 | +0.000 a +0.000 | 0 de 3 |
| barreja ×¼ | 0.773 | 0.773 | +0.000 | +0.000 a +0.000 | 0 de 3 |
| aire ×¼ | 0.770 | 0.770 | +0.000 | +0.000 a +0.000 | 0 de 3 |
| curts | 0.732 | 0.732 | +0.000 | +0.000 a +0.000 | 0 de 3 |
| llargs | 0.731 | 0.731 | +0.000 | +0.000 a +0.000 | 0 de 3 |
| barreja | 0.742 | 0.742 | +0.000 | +0.000 a +0.000 | 0 de 3 |
| aire | 0.733 | 0.733 | +0.000 | +0.000 a +0.000 | 0 de 3 |
| soroll2 | 0.649 | 0.649 | +0.000 | +0.000 a +0.000 | 0 de 3 |
| partit ×¼ | 0.838 | 0.838 | +0.000 | +0.000 a +0.000 | 0 de 3 |

## A engolides contra A xarxes, decodificador de toc, nivell bo

| escenari | A xarxes, decodificador de toc | A engolides | diferència | interval del 95 % | A engolides guanya |
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

## On falla, abans i després

Amb el nivell mitjà, les causes de `banc/on_falla.py`: la part de les possessions de la veritat de
cada causa, i les predites que sobren a l'altre equip per cada 100 possessions de la veritat.

**curts ×¼**

| causa | A pilota morta | A engolides |
|---|---|---|
| encertada | 0.647 | 0.647 |
| engolida | 0.103 | 0.103 |
| l'altre equip | 0.026 | 0.026 |
| la D | 0.015 | 0.015 |
| trencada | 0.007 | 0.007 |
| ajuntada, per sobre de l'altre equip | 0.133 | 0.133 |
| ajuntada, per sobre de la D | 0.002 | 0.002 |
| les vores | 0.066 | 0.066 |
| sobren a l'altre equip, per cada 100 | 8.692 | 8.692 |

**els quatre ×¼ junts**

| causa | A pilota morta | A engolides |
|---|---|---|
| encertada | 0.626 | 0.626 |
| engolida | 0.101 | 0.101 |
| l'altre equip | 0.029 | 0.029 |
| la D | 0.029 | 0.029 |
| trencada | 0.009 | 0.009 |
| ajuntada, per sobre de l'altre equip | 0.132 | 0.132 |
| ajuntada, per sobre de la D | 0.001 | 0.001 |
| les vores | 0.072 | 0.072 |
| sobren a l'altre equip, per cada 100 | 8.686 | 8.686 |

**net**

| causa | A pilota morta | A engolides |
|---|---|---|
| encertada | 0.761 | 0.761 |
| engolida | 0.071 | 0.071 |
| l'altre equip | 0.020 | 0.020 |
| la D | 0.005 | 0.005 |
| trencada | 0.004 | 0.004 |
| ajuntada, per sobre de l'altre equip | 0.091 | 0.091 |
| ajuntada, per sobre de la D | 0.001 | 0.001 |
| les vores | 0.046 | 0.046 |
| sobren a l'altre equip, per cada 100 | 6.589 | 6.589 |

## El detector

L'AUC a les imatges de dins de les possessions predites, amb el nivell mitjà i les llavors de
provar (la mitjana i la més baixa dels deu partits):

| escenari | mean | min |
|---|---|---|
| net | 0.895 | 0.802 |
| curts ×¼ | 0.887 | 0.841 |
| llargs ×¼ | 0.873 | 0.813 |
| barreja ×¼ | 0.874 | 0.821 |
| aire ×¼ | 0.865 | 0.823 |
| curts | 0.878 | 0.836 |
| llargs | 0.866 | 0.819 |
| barreja | 0.868 | 0.814 |
| aire | 0.859 | 0.818 |
| soroll2 | 0.826 | 0.772 |
| partit ×¼ | 0.882 | 0.802 |

Les mostres de cada un: de 1080263 a 1125546; la part on
la veritat és l'altre equip, de 0.075 a
0.082. Les columnes que més hi fan (la part del guany, a la mitjana dels
deu):

| columna | part |
|---|---|
| `rel_altre` | 0.551 |
| `rel_mateix` | 0.092 |
| `durada` | 0.075 |
| `fins_al_final` | 0.059 |
| `q` | 0.050 |
| `des_de_l_inici` | 0.044 |
| `d_altre_25` | 0.021 |
| `d_mateix_25` | 0.018 |
| `canvi_25` | 0.017 |
| `d_altre_12` | 0.011 |
| `d_mateix_12` | 0.011 |
| `sense_fins_a` | 0.010 |
| `d_mateix` | 0.010 |
| `sense_des_de` | 0.009 |
| `d_altre` | 0.009 |

## La beta triada

A cada partit, amb els altres nou, als quatre ×¼ i a la mitjana dels nivells bo, mitjà i dolent.

| partit | beta |
|---|---|
| dfl-J03WMX | 0 |
| dfl-J03WN1 | 0 |
| dfl-J03WOH | 0 |
| dfl-J03WOY | 0 |
| dfl-J03WPY | 0 |
| dfl-J03WQQ | 0 |
| dfl-J03WR9 | 0 |
| metrica-1 | 0 |
| metrica-2 | 0 |
| metrica-3 | 0 |

**A la vora de la graella:** beta = 0.

## L'spellF1 de cada mètode (mitjana dels deu partits, nivell mitjà)

**spellF1 a la veritat de toc**

| escenari | A xarxes, decodificador de toc | A equips sencers | A neteja d'aire | A pilota morta | A engolides |
|---|---|---|---|---|---|
| net | 0.798 | 0.799 | 0.799 | 0.801 | 0.801 |
| curts ×¼ | 0.673 | 0.699 | 0.699 | 0.702 | 0.702 |
| llargs ×¼ | 0.651 | 0.688 | 0.688 | 0.691 | 0.691 |
| barreja ×¼ | 0.660 | 0.696 | 0.696 | 0.698 | 0.698 |
| aire ×¼ | 0.600 | 0.629 | 0.644 | 0.647 | 0.647 |
| curts | 0.636 | 0.665 | 0.665 | 0.668 | 0.668 |
| llargs | 0.599 | 0.640 | 0.640 | 0.645 | 0.645 |
| barreja | 0.605 | 0.646 | 0.646 | 0.650 | 0.650 |
| aire | 0.554 | 0.600 | 0.618 | 0.620 | 0.620 |
| soroll2 | 0.470 | 0.534 | 0.534 | 0.549 | 0.549 |
| partit ×¼ | 0.746 | 0.761 | 0.761 | 0.764 | 0.764 |

**spellF1 a la veritat de sempre**

| escenari | A xarxes, decodificador de toc | A equips sencers | A neteja d'aire | A pilota morta | A engolides |
|---|---|---|---|---|---|
| net | 0.808 | 0.810 | 0.810 | 0.812 | 0.812 |
| curts ×¼ | 0.684 | 0.708 | 0.708 | 0.711 | 0.711 |
| llargs ×¼ | 0.662 | 0.700 | 0.700 | 0.703 | 0.703 |
| barreja ×¼ | 0.671 | 0.708 | 0.708 | 0.710 | 0.710 |
| aire ×¼ | 0.612 | 0.643 | 0.658 | 0.661 | 0.661 |
| curts | 0.644 | 0.674 | 0.674 | 0.677 | 0.677 |
| llargs | 0.607 | 0.648 | 0.648 | 0.652 | 0.652 |
| barreja | 0.616 | 0.656 | 0.656 | 0.660 | 0.660 |
| aire | 0.564 | 0.613 | 0.632 | 0.633 | 0.633 |
| soroll2 | 0.478 | 0.543 | 0.543 | 0.558 | 0.558 |
| partit ×¼ | 0.757 | 0.772 | 0.772 | 0.775 | 0.775 |

## Els decodificadors

A neteja d'aire, A pilota morta i A engolides fan servir, a cada partit, el d'A equips sencers.

- **A equips sencers:** w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 16, durada mínima 12 (2 partits)
