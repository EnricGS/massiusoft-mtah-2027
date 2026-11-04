# Banc obert · Les pilotes aturades del Smart Tagging (T3af, pas 2)

Generat amb `uv run python -I -m banc.model_pilotes_aturades`. Dades obertes: 7 partits de DFL (IDSSE,
CC BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3af», i la capçalera de `banc/model_pilotes_aturades.py`. Es puntua a la
veritat de toc.

**A xarxes, decodificador de toc** i **A equips sencers** són els de la T3v, **A pilota creïble**, el de la T3w, i **A neteja d'aire**,
el de la T3ac, amb les peces de la memòria cau (✓ comprovat). **A pilotes aturades** és A neteja d'aire,
amb un segon que també veu les 17 columnes del Smart Tagging simulat, i el decodificador triat de nou
amb el nivell mitjà. ✓ Comprovat a cada punt de la graella i a cada nivell: no dona mai la D a una
imatge netejada.

## Amb el nivell mitjà: A pilotes aturades contra A xarxes, decodificador de toc (spellF1), el criteri

| escenari | A xarxes, decodificador de toc | A pilotes aturades | diferència | interval del 95 % | A pilotes aturades guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.798 | 0.798 | +0.000 | -0.007 a +0.008 | 4 de 10 | no perd | ✓ |
| curts ×¼ | 0.673 | 0.700 | +0.026 | +0.022 a +0.033 | 10 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.651 | 0.692 | +0.040 | +0.029 a +0.051 | 10 de 10 | guanya clarament | ✓ |
| barreja ×¼ | 0.660 | 0.696 | +0.036 | +0.029 a +0.043 | 10 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.600 | 0.648 | +0.048 | +0.042 a +0.054 | 10 de 10 | guanya clarament | ✓ |
| curts | 0.636 | 0.665 | +0.029 | +0.024 a +0.035 | 10 de 10 | no perd | ✓ |
| llargs | 0.599 | 0.644 | +0.044 | +0.034 a +0.055 | 10 de 10 | no perd | ✓ |
| barreja | 0.605 | 0.649 | +0.044 | +0.033 a +0.055 | 10 de 10 | no perd | ✓ |
| aire | 0.554 | 0.620 | +0.066 | +0.060 a +0.073 | 10 de 10 | no perd | ✓ |
| soroll2 | 0.470 | 0.541 | +0.071 | +0.064 a +0.078 | 10 de 10 | no perd | ✓ |
| partit ×¼ | 0.746 | 0.758 | +0.013 | +0.007 a +0.018 | 9 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1, el soroll2 i «partit ×¼» | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## Amb els nivells dolent i cap: A pilotes aturades contra A neteja d'aire, la segona part del criteri

| Nivell | curts ×¼ | llargs ×¼ | barreja ×¼ | aire ×¼ | partit ×¼ | No baixa de −0.005 |
|---|---|---|---|---|---|---|
| dolent | +0.0006 | +0.0029 | -0.0035 | +0.0016 | -0.0032 | ✓ |
| cap | -0.0010 | +0.0005 | -0.0036 | -0.0004 | -0.0051 | ✗ |

**A pilotes aturades no passa el criteri sencer.**

## Amb el nivell bo: A pilotes aturades contra A neteja d'aire (spellF1)

| escenari | A neteja d'aire | A pilotes aturades | diferència | interval del 95 % | A pilotes aturades guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.799 | -0.000 | -0.004 a +0.004 | 6 de 10 |
| curts ×¼ | 0.699 | 0.701 | +0.002 | +0.000 a +0.003 | 7 de 10 |
| llargs ×¼ | 0.688 | 0.696 | +0.008 | +0.005 a +0.013 | 9 de 10 |
| barreja ×¼ | 0.696 | 0.698 | +0.002 | -0.002 a +0.005 | 7 de 10 |
| aire ×¼ | 0.644 | 0.649 | +0.005 | +0.001 a +0.010 | 7 de 10 |
| curts | 0.665 | 0.667 | +0.003 | -0.001 a +0.006 | 6 de 10 |
| llargs | 0.640 | 0.647 | +0.006 | +0.001 a +0.011 | 7 de 10 |
| barreja | 0.646 | 0.651 | +0.005 | -0.001 a +0.011 | 7 de 10 |
| aire | 0.618 | 0.623 | +0.005 | +0.003 a +0.008 | 7 de 10 |
| soroll2 | 0.534 | 0.547 | +0.012 | +0.008 a +0.016 | 10 de 10 |
| partit ×¼ | 0.761 | 0.759 | -0.002 | -0.004 a +0.001 | 3 de 10 |

## Amb el nivell mitjà: A pilotes aturades contra A neteja d'aire (spellF1)

| escenari | A neteja d'aire | A pilotes aturades | diferència | interval del 95 % | A pilotes aturades guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.798 | -0.001 | -0.005 a +0.003 | 5 de 10 |
| curts ×¼ | 0.699 | 0.700 | +0.001 | -0.001 a +0.002 | 7 de 10 |
| llargs ×¼ | 0.688 | 0.692 | +0.004 | -0.001 a +0.009 | 8 de 10 |
| barreja ×¼ | 0.696 | 0.696 | -0.001 | -0.004 a +0.002 | 4 de 10 |
| aire ×¼ | 0.644 | 0.648 | +0.004 | -0.001 a +0.009 | 7 de 10 |
| curts | 0.665 | 0.665 | +0.000 | -0.002 a +0.003 | 4 de 10 |
| llargs | 0.640 | 0.644 | +0.003 | -0.003 a +0.009 | 6 de 10 |
| barreja | 0.646 | 0.649 | +0.003 | -0.002 a +0.007 | 6 de 10 |
| aire | 0.618 | 0.620 | +0.003 | -0.000 a +0.005 | 6 de 10 |
| soroll2 | 0.534 | 0.541 | +0.007 | +0.004 a +0.010 | 9 de 10 |
| partit ×¼ | 0.761 | 0.758 | -0.003 | -0.006 a -0.000 | 3 de 10 |

## Amb el nivell dolent: A pilotes aturades contra A neteja d'aire (spellF1)

| escenari | A neteja d'aire | A pilotes aturades | diferència | interval del 95 % | A pilotes aturades guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.798 | -0.001 | -0.005 a +0.003 | 5 de 10 |
| curts ×¼ | 0.699 | 0.700 | +0.001 | -0.001 a +0.003 | 6 de 10 |
| llargs ×¼ | 0.688 | 0.691 | +0.003 | -0.002 a +0.008 | 6 de 10 |
| barreja ×¼ | 0.696 | 0.693 | -0.003 | -0.005 a -0.001 | 1 de 10 |
| aire ×¼ | 0.644 | 0.646 | +0.002 | -0.003 a +0.006 | 5 de 10 |
| curts | 0.665 | 0.663 | -0.001 | -0.005 a +0.002 | 3 de 10 |
| llargs | 0.640 | 0.643 | +0.003 | -0.002 a +0.008 | 6 de 10 |
| barreja | 0.646 | 0.646 | -0.001 | -0.005 a +0.003 | 5 de 10 |
| aire | 0.618 | 0.619 | +0.002 | -0.002 a +0.005 | 7 de 10 |
| soroll2 | 0.534 | 0.536 | +0.002 | +0.000 a +0.004 | 6 de 10 |
| partit ×¼ | 0.761 | 0.758 | -0.003 | -0.007 a +0.000 | 3 de 10 |

## Amb el nivell cap: A pilotes aturades contra A neteja d'aire (spellF1)

| escenari | A neteja d'aire | A pilotes aturades | diferència | interval del 95 % | A pilotes aturades guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.797 | -0.002 | -0.006 a +0.002 | 5 de 10 |
| curts ×¼ | 0.699 | 0.698 | -0.001 | -0.002 a +0.001 | 5 de 10 |
| llargs ×¼ | 0.688 | 0.689 | +0.001 | -0.004 a +0.005 | 3 de 10 |
| barreja ×¼ | 0.696 | 0.693 | -0.004 | -0.006 a -0.001 | 2 de 10 |
| aire ×¼ | 0.644 | 0.644 | -0.000 | -0.004 a +0.003 | 4 de 10 |
| curts | 0.665 | 0.664 | -0.001 | -0.004 a +0.002 | 2 de 10 |
| llargs | 0.640 | 0.640 | -0.000 | -0.004 a +0.003 | 4 de 10 |
| barreja | 0.646 | 0.645 | -0.002 | -0.005 a +0.002 | 4 de 10 |
| aire | 0.618 | 0.617 | -0.001 | -0.004 a +0.002 | 4 de 10 |
| soroll2 | 0.534 | 0.529 | -0.005 | -0.008 a -0.002 | 1 de 10 |
| partit ×¼ | 0.761 | 0.756 | -0.005 | -0.008 a -0.002 | 1 de 10 |

## No passa: és el millor fins ara?

La regla de la D-50, escrita abans, contra A neteja d'aire amb el nivell mitjà, i la mateixa
segona part del criteri:

| | És el millor fins ara si | |
|---|---|---|
| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | ✗ |
| «partit ×¼» | la diferència no és negativa | ✗ |
| El net, els ×1 i el soroll2 | no perd (diferència ≥ −0.04) | ✓ |
| Dolent i cap | la segona part del criteri | ✗ |

**A pilotes aturades no és el millor fins ara:** el pas següent es fa a sobre d'A neteja d'aire.

## A pilotes aturades contra A xarxes, decodificador de toc, nivell mitjà, només els partits de dfl

| escenari | A xarxes, decodificador de toc | A pilotes aturades | diferència | interval del 95 % | A pilotes aturades guanya |
|---|---|---|---|---|---|
| net | 0.766 | 0.767 | +0.001 | -0.006 a +0.007 | 3 de 7 |
| curts ×¼ | 0.642 | 0.668 | +0.026 | +0.021 a +0.035 | 7 de 7 |
| llargs ×¼ | 0.621 | 0.660 | +0.039 | +0.026 a +0.051 | 7 de 7 |
| barreja ×¼ | 0.630 | 0.661 | +0.031 | +0.024 a +0.039 | 7 de 7 |
| aire ×¼ | 0.544 | 0.597 | +0.053 | +0.046 a +0.059 | 7 de 7 |
| curts | 0.607 | 0.637 | +0.030 | +0.023 a +0.037 | 7 de 7 |
| llargs | 0.564 | 0.606 | +0.042 | +0.027 a +0.057 | 7 de 7 |
| barreja | 0.571 | 0.613 | +0.042 | +0.030 a +0.054 | 7 de 7 |
| aire | 0.501 | 0.571 | +0.070 | +0.063 a +0.079 | 7 de 7 |
| soroll2 | 0.433 | 0.496 | +0.063 | +0.056 a +0.070 | 7 de 7 |
| partit ×¼ | 0.717 | 0.727 | +0.010 | +0.003 a +0.016 | 6 de 7 |

## A pilotes aturades contra A neteja d'aire, nivell mitjà, només els partits de dfl

| escenari | A neteja d'aire | A pilotes aturades | diferència | interval del 95 % | A pilotes aturades guanya |
|---|---|---|---|---|---|
| net | 0.768 | 0.767 | -0.001 | -0.006 a +0.002 | 4 de 7 |
| curts ×¼ | 0.669 | 0.668 | -0.001 | -0.002 a +0.001 | 4 de 7 |
| llargs ×¼ | 0.656 | 0.660 | +0.004 | +0.000 a +0.008 | 6 de 7 |
| barreja ×¼ | 0.664 | 0.661 | -0.002 | -0.006 a +0.001 | 2 de 7 |
| aire ×¼ | 0.592 | 0.597 | +0.004 | -0.002 a +0.011 | 4 de 7 |
| curts | 0.637 | 0.637 | -0.000 | -0.003 a +0.003 | 3 de 7 |
| llargs | 0.602 | 0.606 | +0.004 | -0.004 a +0.011 | 4 de 7 |
| barreja | 0.608 | 0.613 | +0.005 | -0.000 a +0.010 | 5 de 7 |
| aire | 0.572 | 0.571 | -0.001 | -0.005 a +0.003 | 3 de 7 |
| soroll2 | 0.491 | 0.496 | +0.005 | +0.001 a +0.009 | 6 de 7 |
| partit ×¼ | 0.729 | 0.727 | -0.003 | -0.007 a +0.001 | 3 de 7 |

## A pilotes aturades contra A xarxes, decodificador de toc, nivell mitjà, només els partits de metrica

| escenari | A xarxes, decodificador de toc | A pilotes aturades | diferència | interval del 95 % | A pilotes aturades guanya |
|---|---|---|---|---|---|
| net | 0.874 | 0.872 | -0.001 | -0.013 a +0.022 | 1 de 3 |
| curts ×¼ | 0.747 | 0.773 | +0.026 | +0.019 a +0.034 | 3 de 3 |
| llargs ×¼ | 0.723 | 0.766 | +0.043 | +0.018 a +0.060 | 3 de 3 |
| barreja ×¼ | 0.730 | 0.775 | +0.045 | +0.035 a +0.065 | 3 de 3 |
| aire ×¼ | 0.731 | 0.768 | +0.037 | +0.022 a +0.052 | 3 de 3 |
| curts | 0.702 | 0.731 | +0.028 | +0.020 a +0.040 | 3 de 3 |
| llargs | 0.682 | 0.731 | +0.049 | +0.042 a +0.056 | 3 de 3 |
| barreja | 0.684 | 0.733 | +0.048 | +0.024 a +0.073 | 3 de 3 |
| aire | 0.679 | 0.735 | +0.055 | +0.048 a +0.065 | 3 de 3 |
| soroll2 | 0.557 | 0.645 | +0.088 | +0.077 a +0.110 | 3 de 3 |
| partit ×¼ | 0.813 | 0.832 | +0.019 | +0.011 a +0.031 | 3 de 3 |

## A pilotes aturades contra A neteja d'aire, nivell mitjà, només els partits de metrica

| escenari | A neteja d'aire | A pilotes aturades | diferència | interval del 95 % | A pilotes aturades guanya |
|---|---|---|---|---|---|
| net | 0.873 | 0.872 | -0.000 | -0.008 a +0.010 | 1 de 3 |
| curts ×¼ | 0.769 | 0.773 | +0.003 | +0.002 a +0.005 | 3 de 3 |
| llargs ×¼ | 0.763 | 0.766 | +0.003 | -0.009 a +0.018 | 2 de 3 |
| barreja ×¼ | 0.773 | 0.775 | +0.002 | -0.002 a +0.005 | 2 de 3 |
| aire ×¼ | 0.765 | 0.768 | +0.003 | +0.002 a +0.006 | 3 de 3 |
| curts | 0.729 | 0.731 | +0.002 | -0.001 a +0.008 | 1 de 3 |
| llargs | 0.730 | 0.731 | +0.001 | -0.007 a +0.007 | 2 de 3 |
| barreja | 0.736 | 0.733 | -0.003 | -0.015 a +0.007 | 1 de 3 |
| aire | 0.724 | 0.735 | +0.011 | +0.010 a +0.011 | 3 de 3 |
| soroll2 | 0.634 | 0.645 | +0.011 | +0.007 a +0.017 | 3 de 3 |
| partit ×¼ | 0.835 | 0.832 | -0.004 | -0.005 a -0.002 | 0 de 3 |

## A pilotes aturades contra A xarxes, decodificador de toc, nivell bo

| escenari | A xarxes, decodificador de toc | A pilotes aturades | diferència | interval del 95 % | A pilotes aturades guanya |
|---|---|---|---|---|---|
| net | 0.798 | 0.799 | +0.001 | -0.006 a +0.009 | 4 de 10 |
| curts ×¼ | 0.673 | 0.701 | +0.027 | +0.022 a +0.034 | 10 de 10 |
| llargs ×¼ | 0.651 | 0.696 | +0.045 | +0.035 a +0.054 | 10 de 10 |
| barreja ×¼ | 0.660 | 0.698 | +0.038 | +0.031 a +0.045 | 10 de 10 |
| aire ×¼ | 0.600 | 0.649 | +0.049 | +0.043 a +0.055 | 10 de 10 |
| curts | 0.636 | 0.667 | +0.032 | +0.025 a +0.038 | 10 de 10 |
| llargs | 0.599 | 0.647 | +0.047 | +0.036 a +0.058 | 10 de 10 |
| barreja | 0.605 | 0.651 | +0.046 | +0.037 a +0.055 | 10 de 10 |
| aire | 0.554 | 0.623 | +0.069 | +0.064 a +0.074 | 10 de 10 |
| soroll2 | 0.470 | 0.547 | +0.076 | +0.068 a +0.084 | 10 de 10 |
| partit ×¼ | 0.746 | 0.759 | +0.014 | +0.008 a +0.019 | 9 de 10 |

## A 5 s o menys de cada represa

La part de les imatges vàlides a 5 s o menys d'una represa on la predicció (amb les abstencions
omplertes) és la veritat de toc.

| escenari | A neteja d'aire | A pilotes aturades, bo | A pilotes aturades, mitjà | A pilotes aturades, dolent | A pilotes aturades, cap |
|---|---|---|---|---|---|
| net | 0.953 | 0.956 | 0.955 | 0.953 | 0.950 |
| curts ×¼ | 0.918 | 0.928 | 0.922 | 0.920 | 0.916 |
| llargs ×¼ | 0.892 | 0.914 | 0.902 | 0.894 | 0.888 |
| barreja ×¼ | 0.901 | 0.918 | 0.909 | 0.900 | 0.897 |
| aire ×¼ | 0.886 | 0.902 | 0.893 | 0.887 | 0.881 |
| curts | 0.900 | 0.914 | 0.905 | 0.902 | 0.896 |
| llargs | 0.873 | 0.897 | 0.882 | 0.877 | 0.869 |
| barreja | 0.878 | 0.899 | 0.890 | 0.878 | 0.872 |
| aire | 0.870 | 0.889 | 0.877 | 0.872 | 0.868 |
| soroll2 | 0.750 | 0.804 | 0.782 | 0.755 | 0.737 |
| partit ×¼ | 0.944 | 0.950 | 0.946 | 0.945 | 0.939 |

## Les possessions de la veritat aparellades, per durada

Les possessions de la veritat de toc, i la part que s'aparella amb una de la predicció a la IoU 0.5, amb el nivell mitjà.

| escenari | durada | n per partit | aparellades · A neteja d'aire | aparellades · A pilotes aturades |
|---|---|---|---|---|
| net | de menys d'1 s | 55 | 0.328 | 0.322 |
| net | d'1 a 2 s | 75 | 0.609 | 0.608 |
| net | de 2 a 5 s | 124 | 0.786 | 0.785 |
| net | de 5 a 10 s | 76 | 0.908 | 0.905 |
| net | de 10 s o més | 98 | 0.971 | 0.970 |
| curts ×¼ | de menys d'1 s | 55 | 0.161 | 0.158 |
| curts ×¼ | d'1 a 2 s | 75 | 0.406 | 0.396 |
| curts ×¼ | de 2 a 5 s | 124 | 0.658 | 0.656 |
| curts ×¼ | de 5 a 10 s | 76 | 0.837 | 0.841 |
| curts ×¼ | de 10 s o més | 98 | 0.943 | 0.942 |
| partit ×¼ | de menys d'1 s | 55 | 0.259 | 0.248 |
| partit ×¼ | d'1 a 2 s | 75 | 0.573 | 0.573 |
| partit ×¼ | de 2 a 5 s | 124 | 0.743 | 0.736 |
| partit ×¼ | de 5 a 10 s | 76 | 0.867 | 0.863 |
| partit ×¼ | de 10 s o més | 98 | 0.954 | 0.957 |

## El pes de les columnes del Smart Tagging al segon

La part del guany de cada columna, de mitjana als deu segons.

| columna | part del guany |
|---|---|
| st_abans_s | 0.0009 |
| st_abans_banda | 0.0001 |
| st_abans_corner | 0.0000 |
| st_abans_porta | 0.0000 |
| st_abans_falta | 0.0001 |
| st_abans_sortida | 0.0000 |
| st_abans_equip_h | 0.0000 |
| st_abans_equip_a | 0.0000 |
| st_despres_s | 0.0020 |
| st_despres_banda | 0.0003 |
| st_despres_corner | 0.0002 |
| st_despres_porta | 0.0001 |
| st_despres_falta | 0.0011 |
| st_despres_sortida | 0.0000 |
| st_despres_equip_h | 0.0000 |
| st_despres_equip_a | 0.0000 |
| st_dins | 0.0001 |
| les 17 juntes | 0.0050 |

## L'spellF1 de cada mètode (mitjana dels deu partits, nivell mitjà)

**spellF1 a la veritat de toc**

| escenari | A xarxes, decodificador de toc | A equips sencers | A neteja d'aire | A pilotes aturades |
|---|---|---|---|---|
| net | 0.798 | 0.799 | 0.799 | 0.798 |
| curts ×¼ | 0.673 | 0.699 | 0.699 | 0.700 |
| llargs ×¼ | 0.651 | 0.688 | 0.688 | 0.692 |
| barreja ×¼ | 0.660 | 0.696 | 0.696 | 0.696 |
| aire ×¼ | 0.600 | 0.629 | 0.644 | 0.648 |
| curts | 0.636 | 0.665 | 0.665 | 0.665 |
| llargs | 0.599 | 0.640 | 0.640 | 0.644 |
| barreja | 0.605 | 0.646 | 0.646 | 0.649 |
| aire | 0.554 | 0.600 | 0.618 | 0.620 |
| soroll2 | 0.470 | 0.534 | 0.534 | 0.541 |
| partit ×¼ | 0.746 | 0.761 | 0.761 | 0.758 |

**spellF1 a la veritat de sempre**

| escenari | A xarxes, decodificador de toc | A equips sencers | A neteja d'aire | A pilotes aturades |
|---|---|---|---|---|
| net | 0.808 | 0.810 | 0.810 | 0.809 |
| curts ×¼ | 0.684 | 0.708 | 0.708 | 0.709 |
| llargs ×¼ | 0.662 | 0.700 | 0.700 | 0.702 |
| barreja ×¼ | 0.671 | 0.708 | 0.708 | 0.707 |
| aire ×¼ | 0.612 | 0.643 | 0.658 | 0.663 |
| curts | 0.644 | 0.674 | 0.674 | 0.675 |
| llargs | 0.607 | 0.648 | 0.648 | 0.652 |
| barreja | 0.616 | 0.656 | 0.656 | 0.658 |
| aire | 0.564 | 0.613 | 0.632 | 0.634 |
| soroll2 | 0.478 | 0.543 | 0.543 | 0.550 |
| partit ×¼ | 0.757 | 0.772 | 0.772 | 0.770 |

## Els decodificadors triats

A neteja d'aire fa servir, a cada partit, el d'A equips sencers.

- **A xarxes, decodificador de toc:** w = 4, λ = 64, durada mínima 1 (1 partits); w = 4, λ = 32, durada mínima 12 (6 partits); w = 4, λ = 32, durada mínima 1 (3 partits)
- **A equips sencers:** w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 16, durada mínima 12 (2 partits)
- **A pilotes aturades:** w = 4, λ = 32, durada mínima 12 (10 partits)
