# Banc obert · A fases amb la graella ampliada (T3al)

Generat amb `uv run python -I -m banc.model_fases_amplia`. Dades obertes: 7 partits de DFL (IDSSE, CC BY
4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el criteri:
`docs/pla-tocs.md`, «T3al», i la capçalera de `banc/model_fases_amplia.py`. Es puntua a la veritat de toc.

**A xarxes, decodificador de toc** i **A equips sencers** són els de la T3v, **A pilota creïble**, el de la T3w, **A neteja d'aire**,
el de la T3ac, **A pilota morta**, el de la T3ah, i **A fases**, el de la T3ak (✓ comprovat). **A fases àmplia** és A fases
amb la graella més ampla. ✓ Comprovat: no dona mai la D a una imatge netejada; els punts de la graella de la
T3ak hi donen exactament el mateix; A pilota morta d'aquí dona l'spellF1 de la T3ah; sense etiquetes, exactament
A neteja d'aire; sense fases, A fases àmplia és exactament A pilota morta; i on es tria el punt de la T3ak, exactament A fases.

## Amb el nivell mitjà: A fases àmplia contra A xarxes, decodificador de toc (spellF1), el criteri

| escenari | A xarxes, decodificador de toc | A fases àmplia | diferència | interval del 95 % | A fases àmplia guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.798 | 0.801 | +0.003 | -0.004 a +0.010 | 7 de 10 | no perd | ✓ |
| curts ×¼ | 0.673 | 0.711 | +0.037 | +0.030 a +0.046 | 10 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.651 | 0.703 | +0.052 | +0.043 a +0.061 | 10 de 10 | guanya clarament | ✓ |
| barreja ×¼ | 0.660 | 0.708 | +0.048 | +0.041 a +0.054 | 10 de 10 | guanya clarament | ✓ |
| aire ×¼ | 0.600 | 0.664 | +0.064 | +0.058 a +0.070 | 10 de 10 | guanya clarament | ✓ |
| curts | 0.636 | 0.679 | +0.043 | +0.038 a +0.048 | 10 de 10 | no perd | ✓ |
| llargs | 0.599 | 0.659 | +0.059 | +0.048 a +0.071 | 10 de 10 | no perd | ✓ |
| barreja | 0.605 | 0.662 | +0.057 | +0.044 a +0.068 | 10 de 10 | no perd | ✓ |
| aire | 0.554 | 0.638 | +0.083 | +0.079 a +0.087 | 10 de 10 | no perd | ✓ |
| soroll2 | 0.470 | 0.570 | +0.099 | +0.092 a +0.106 | 10 de 10 | no perd | ✓ |
| partit ×¼ | 0.746 | 0.772 | +0.026 | +0.017 a +0.035 | 10 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1, el soroll2 i «partit ×¼» | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## Amb els nivells dolent i cap: A fases àmplia contra A neteja d'aire, la segona part del criteri

| Nivell | curts ×¼ | llargs ×¼ | barreja ×¼ | aire ×¼ | partit ×¼ | No baixa de −0.005 |
|---|---|---|---|---|---|---|
| dolent | -0.0030 | -0.0030 | -0.0021 | -0.0005 | -0.0030 | ✓ |
| cap | +0.0000 | +0.0000 | +0.0000 | +0.0000 | +0.0000 | ✓ |

**A fases àmplia no passa el criteri sencer.**

## Amb el nivell bo: A fases àmplia contra A fases (spellF1)

| escenari | A fases | A fases àmplia | diferència | interval del 95 % | A fases àmplia guanya |
|---|---|---|---|---|---|
| net | 0.832 | 0.832 | -0.000 | -0.001 a +0.001 | 4 de 10 |
| curts ×¼ | 0.758 | 0.760 | +0.003 | +0.001 a +0.004 | 9 de 10 |
| llargs ×¼ | 0.753 | 0.758 | +0.004 | +0.003 a +0.007 | 9 de 10 |
| barreja ×¼ | 0.750 | 0.757 | +0.007 | +0.005 a +0.008 | 10 de 10 |
| aire ×¼ | 0.721 | 0.732 | +0.011 | +0.008 a +0.015 | 10 de 10 |
| curts | 0.737 | 0.740 | +0.003 | +0.000 a +0.006 | 8 de 10 |
| llargs | 0.716 | 0.723 | +0.007 | +0.004 a +0.010 | 9 de 10 |
| barreja | 0.720 | 0.731 | +0.011 | +0.006 a +0.015 | 9 de 10 |
| aire | 0.698 | 0.716 | +0.017 | +0.013 a +0.022 | 10 de 10 |
| soroll2 | 0.649 | 0.655 | +0.006 | +0.004 a +0.008 | 10 de 10 |
| partit ×¼ | 0.806 | 0.808 | +0.002 | +0.001 a +0.003 | 7 de 10 |

## Amb el nivell mitjà: A fases àmplia contra A fases (spellF1)

| escenari | A fases | A fases àmplia | diferència | interval del 95 % | A fases àmplia guanya |
|---|---|---|---|---|---|
| net | 0.803 | 0.801 | -0.001 | -0.003 a -0.000 | 2 de 10 |
| curts ×¼ | 0.711 | 0.711 | -0.000 | -0.001 a +0.000 | 4 de 10 |
| llargs ×¼ | 0.704 | 0.703 | -0.001 | -0.003 a +0.000 | 4 de 10 |
| barreja ×¼ | 0.708 | 0.708 | -0.001 | -0.002 a +0.000 | 4 de 10 |
| aire ×¼ | 0.662 | 0.664 | +0.003 | +0.001 a +0.004 | 8 de 10 |
| curts | 0.679 | 0.679 | -0.001 | -0.002 a +0.000 | 3 de 10 |
| llargs | 0.658 | 0.659 | +0.000 | -0.001 a +0.002 | 5 de 10 |
| barreja | 0.660 | 0.662 | +0.002 | -0.001 a +0.004 | 6 de 10 |
| aire | 0.635 | 0.638 | +0.003 | +0.001 a +0.005 | 8 de 10 |
| soroll2 | 0.568 | 0.570 | +0.001 | -0.000 a +0.003 | 7 de 10 |
| partit ×¼ | 0.772 | 0.772 | -0.000 | -0.001 a +0.001 | 4 de 10 |

## Amb el nivell dolent: A fases àmplia contra A fases (spellF1)

| escenari | A fases | A fases àmplia | diferència | interval del 95 % | A fases àmplia guanya |
|---|---|---|---|---|---|
| net | 0.797 | 0.794 | -0.003 | -0.004 a -0.002 | 1 de 10 |
| curts ×¼ | 0.698 | 0.696 | -0.002 | -0.003 a -0.001 | 0 de 10 |
| llargs ×¼ | 0.687 | 0.685 | -0.002 | -0.003 a -0.001 | 1 de 10 |
| barreja ×¼ | 0.695 | 0.694 | -0.001 | -0.002 a +0.001 | 2 de 10 |
| aire ×¼ | 0.644 | 0.644 | -0.001 | -0.002 a +0.000 | 4 de 10 |
| curts | 0.660 | 0.659 | -0.001 | -0.002 a -0.000 | 2 de 10 |
| llargs | 0.641 | 0.640 | -0.002 | -0.004 a +0.000 | 3 de 10 |
| barreja | 0.646 | 0.646 | -0.001 | -0.002 a +0.001 | 3 de 10 |
| aire | 0.614 | 0.615 | +0.001 | -0.000 a +0.003 | 6 de 10 |
| soroll2 | 0.546 | 0.544 | -0.002 | -0.004 a +0.000 | 2 de 10 |
| partit ×¼ | 0.760 | 0.758 | -0.001 | -0.002 a -0.001 | 1 de 10 |

## Amb el nivell cap: A fases àmplia contra A fases (spellF1)

| escenari | A fases | A fases àmplia | diferència | interval del 95 % | A fases àmplia guanya |
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

## Amb el nivell bo: A fases àmplia contra A pilota morta (spellF1)

| escenari | A pilota morta | A fases àmplia | diferència | interval del 95 % | A fases àmplia guanya |
|---|---|---|---|---|---|
| net | 0.802 | 0.832 | +0.030 | +0.024 a +0.036 | 10 de 10 |
| curts ×¼ | 0.703 | 0.760 | +0.057 | +0.050 a +0.065 | 10 de 10 |
| llargs ×¼ | 0.694 | 0.758 | +0.063 | +0.060 a +0.067 | 10 de 10 |
| barreja ×¼ | 0.699 | 0.757 | +0.058 | +0.053 a +0.064 | 10 de 10 |
| aire ×¼ | 0.649 | 0.732 | +0.083 | +0.075 a +0.092 | 10 de 10 |
| curts | 0.669 | 0.740 | +0.072 | +0.066 a +0.077 | 10 de 10 |
| llargs | 0.645 | 0.723 | +0.079 | +0.073 a +0.085 | 10 de 10 |
| barreja | 0.650 | 0.731 | +0.081 | +0.075 a +0.087 | 10 de 10 |
| aire | 0.622 | 0.716 | +0.093 | +0.085 a +0.103 | 10 de 10 |
| soroll2 | 0.554 | 0.655 | +0.101 | +0.092 a +0.110 | 10 de 10 |
| partit ×¼ | 0.765 | 0.808 | +0.043 | +0.035 a +0.052 | 10 de 10 |

## Amb el nivell mitjà: A fases àmplia contra A pilota morta (spellF1)

| escenari | A pilota morta | A fases àmplia | diferència | interval del 95 % | A fases àmplia guanya |
|---|---|---|---|---|---|
| net | 0.801 | 0.801 | +0.000 | -0.005 a +0.004 | 7 de 10 |
| curts ×¼ | 0.702 | 0.711 | +0.009 | +0.003 a +0.014 | 9 de 10 |
| llargs ×¼ | 0.691 | 0.703 | +0.012 | +0.008 a +0.016 | 10 de 10 |
| barreja ×¼ | 0.698 | 0.708 | +0.009 | +0.004 a +0.015 | 9 de 10 |
| aire ×¼ | 0.647 | 0.664 | +0.018 | +0.014 a +0.021 | 10 de 10 |
| curts | 0.668 | 0.679 | +0.011 | +0.008 a +0.014 | 10 de 10 |
| llargs | 0.645 | 0.659 | +0.014 | +0.010 a +0.018 | 10 de 10 |
| barreja | 0.650 | 0.662 | +0.012 | +0.005 a +0.019 | 8 de 10 |
| aire | 0.620 | 0.638 | +0.018 | +0.011 a +0.024 | 10 de 10 |
| soroll2 | 0.549 | 0.570 | +0.021 | +0.016 a +0.026 | 10 de 10 |
| partit ×¼ | 0.764 | 0.772 | +0.008 | -0.000 a +0.016 | 8 de 10 |

## Amb el nivell dolent: A fases àmplia contra A pilota morta (spellF1)

| escenari | A pilota morta | A fases àmplia | diferència | interval del 95 % | A fases àmplia guanya |
|---|---|---|---|---|---|
| net | 0.801 | 0.794 | -0.007 | -0.010 a -0.004 | 1 de 10 |
| curts ×¼ | 0.702 | 0.696 | -0.006 | -0.009 a -0.002 | 3 de 10 |
| llargs ×¼ | 0.692 | 0.685 | -0.006 | -0.011 a -0.001 | 2 de 10 |
| barreja ×¼ | 0.697 | 0.694 | -0.003 | -0.008 a +0.001 | 4 de 10 |
| aire ×¼ | 0.648 | 0.644 | -0.004 | -0.008 a +0.001 | 5 de 10 |
| curts | 0.668 | 0.659 | -0.009 | -0.014 a -0.004 | 1 de 10 |
| llargs | 0.644 | 0.640 | -0.004 | -0.010 a +0.000 | 3 de 10 |
| barreja | 0.648 | 0.646 | -0.002 | -0.005 a +0.002 | 5 de 10 |
| aire | 0.618 | 0.615 | -0.004 | -0.010 a +0.003 | 5 de 10 |
| soroll2 | 0.547 | 0.544 | -0.003 | -0.009 a +0.002 | 4 de 10 |
| partit ×¼ | 0.763 | 0.758 | -0.004 | -0.008 a -0.001 | 4 de 10 |

## Amb el nivell cap: A fases àmplia contra A pilota morta (spellF1)

| escenari | A pilota morta | A fases àmplia | diferència | interval del 95 % | A fases àmplia guanya |
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

La regla de la D-50, escrita abans, contra A fases amb el nivell mitjà, i la mateixa segona part
del criteri:

| | És el millor fins ara si | |
|---|---|---|
| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | ✗ |
| «partit ×¼» | la diferència no és negativa | ✗ |
| El net, els ×1 i el soroll2 | no perd (diferència ≥ −0.04) | ✓ |
| Dolent i cap | la segona part del criteri | ✓ |

**A fases àmplia no és el millor fins ara:** el pas següent es fa a sobre d'A fases.

## A fases àmplia contra A xarxes, decodificador de toc, nivell mitjà, només els partits de dfl

| escenari | A xarxes, decodificador de toc | A fases àmplia | diferència | interval del 95 % | A fases àmplia guanya |
|---|---|---|---|---|---|
| net | 0.766 | 0.771 | +0.005 | +0.001 a +0.010 | 6 de 7 |
| curts ×¼ | 0.642 | 0.681 | +0.039 | +0.029 a +0.052 | 7 de 7 |
| llargs ×¼ | 0.621 | 0.673 | +0.052 | +0.042 a +0.062 | 7 de 7 |
| barreja ×¼ | 0.630 | 0.676 | +0.046 | +0.039 a +0.054 | 7 de 7 |
| aire ×¼ | 0.544 | 0.615 | +0.071 | +0.063 a +0.078 | 7 de 7 |
| curts | 0.607 | 0.648 | +0.041 | +0.035 a +0.047 | 7 de 7 |
| llargs | 0.564 | 0.624 | +0.060 | +0.044 a +0.076 | 7 de 7 |
| barreja | 0.571 | 0.624 | +0.053 | +0.042 a +0.062 | 7 de 7 |
| aire | 0.501 | 0.589 | +0.088 | +0.083 a +0.092 | 7 de 7 |
| soroll2 | 0.433 | 0.519 | +0.086 | +0.078 a +0.093 | 7 de 7 |
| partit ×¼ | 0.717 | 0.740 | +0.023 | +0.016 a +0.030 | 7 de 7 |

## A fases àmplia contra A fases, nivell mitjà, només els partits de dfl

| escenari | A fases | A fases àmplia | diferència | interval del 95 % | A fases àmplia guanya |
|---|---|---|---|---|---|
| net | 0.772 | 0.771 | -0.002 | -0.003 a +0.000 | 2 de 7 |
| curts ×¼ | 0.682 | 0.681 | -0.001 | -0.002 a +0.000 | 2 de 7 |
| llargs ×¼ | 0.674 | 0.673 | -0.001 | -0.003 a +0.000 | 3 de 7 |
| barreja ×¼ | 0.678 | 0.676 | -0.001 | -0.003 a -0.000 | 2 de 7 |
| aire ×¼ | 0.611 | 0.615 | +0.004 | +0.003 a +0.006 | 7 de 7 |
| curts | 0.651 | 0.648 | -0.002 | -0.003 a -0.001 | 1 de 7 |
| llargs | 0.623 | 0.624 | +0.001 | -0.001 a +0.002 | 4 de 7 |
| barreja | 0.623 | 0.624 | +0.001 | -0.001 a +0.002 | 4 de 7 |
| aire | 0.586 | 0.589 | +0.003 | +0.001 a +0.006 | 6 de 7 |
| soroll2 | 0.519 | 0.519 | +0.000 | -0.001 a +0.001 | 5 de 7 |
| partit ×¼ | 0.741 | 0.740 | -0.001 | -0.002 a +0.001 | 2 de 7 |

## A fases àmplia contra A xarxes, decodificador de toc, nivell mitjà, només els partits de metrica

| escenari | A xarxes, decodificador de toc | A fases àmplia | diferència | interval del 95 % | A fases àmplia guanya |
|---|---|---|---|---|---|
| net | 0.874 | 0.872 | -0.002 | -0.022 a +0.023 | 1 de 3 |
| curts ×¼ | 0.747 | 0.779 | +0.033 | +0.031 a +0.034 | 3 de 3 |
| llargs ×¼ | 0.723 | 0.774 | +0.050 | +0.038 a +0.071 | 3 de 3 |
| barreja ×¼ | 0.730 | 0.781 | +0.051 | +0.040 a +0.065 | 3 de 3 |
| aire ×¼ | 0.731 | 0.780 | +0.049 | +0.038 a +0.056 | 3 de 3 |
| curts | 0.702 | 0.749 | +0.047 | +0.036 a +0.057 | 3 de 3 |
| llargs | 0.682 | 0.740 | +0.058 | +0.051 a +0.067 | 3 de 3 |
| barreja | 0.684 | 0.750 | +0.065 | +0.027 a +0.100 | 3 de 3 |
| aire | 0.679 | 0.752 | +0.073 | +0.061 a +0.082 | 3 de 3 |
| soroll2 | 0.557 | 0.687 | +0.130 | +0.115 a +0.149 | 3 de 3 |
| partit ×¼ | 0.813 | 0.845 | +0.033 | +0.002 a +0.057 | 3 de 3 |

## A fases àmplia contra A fases, nivell mitjà, només els partits de metrica

| escenari | A fases | A fases àmplia | diferència | interval del 95 % | A fases àmplia guanya |
|---|---|---|---|---|---|
| net | 0.873 | 0.872 | -0.001 | -0.001 a -0.000 | 0 de 3 |
| curts ×¼ | 0.779 | 0.779 | +0.001 | +0.000 a +0.002 | 2 de 3 |
| llargs ×¼ | 0.775 | 0.774 | -0.001 | -0.004 a +0.002 | 1 de 3 |
| barreja ×¼ | 0.780 | 0.781 | +0.001 | -0.001 a +0.002 | 2 de 3 |
| aire ×¼ | 0.781 | 0.780 | -0.001 | -0.003 a +0.002 | 1 de 3 |
| curts | 0.747 | 0.749 | +0.003 | +0.000 a +0.004 | 2 de 3 |
| llargs | 0.740 | 0.740 | -0.000 | -0.003 a +0.003 | 1 de 3 |
| barreja | 0.746 | 0.750 | +0.004 | -0.002 a +0.012 | 2 de 3 |
| aire | 0.750 | 0.752 | +0.002 | -0.001 a +0.005 | 2 de 3 |
| soroll2 | 0.684 | 0.687 | +0.003 | -0.003 a +0.007 | 2 de 3 |
| partit ×¼ | 0.845 | 0.845 | +0.000 | +0.000 a +0.001 | 2 de 3 |

## A fases àmplia contra A xarxes, decodificador de toc, nivell bo

| escenari | A xarxes, decodificador de toc | A fases àmplia | diferència | interval del 95 % | A fases àmplia guanya |
|---|---|---|---|---|---|
| net | 0.798 | 0.832 | +0.034 | +0.024 a +0.043 | 10 de 10 |
| curts ×¼ | 0.673 | 0.760 | +0.087 | +0.077 a +0.100 | 10 de 10 |
| llargs ×¼ | 0.651 | 0.758 | +0.106 | +0.097 a +0.116 | 10 de 10 |
| barreja ×¼ | 0.660 | 0.757 | +0.097 | +0.089 a +0.106 | 10 de 10 |
| aire ×¼ | 0.600 | 0.732 | +0.132 | +0.124 a +0.141 | 10 de 10 |
| curts | 0.636 | 0.740 | +0.104 | +0.096 a +0.112 | 10 de 10 |
| llargs | 0.599 | 0.723 | +0.124 | +0.110 a +0.136 | 10 de 10 |
| barreja | 0.605 | 0.731 | +0.126 | +0.118 a +0.136 | 10 de 10 |
| aire | 0.554 | 0.716 | +0.161 | +0.151 a +0.172 | 10 de 10 |
| soroll2 | 0.470 | 0.655 | +0.184 | +0.176 a +0.195 | 10 de 10 |
| partit ×¼ | 0.746 | 0.808 | +0.062 | +0.051 a +0.073 | 10 de 10 |

## On falla, abans i després

Amb el nivell mitjà, les causes de `banc/on_falla.py`: la part de les possessions de la veritat de
cada causa, i les predites que sobren a l'altre equip per cada 100 possessions de la veritat.

**curts ×¼**

| causa | A pilota morta | A fases | A fases àmplia |
|---|---|---|---|
| encertada | 0.647 | 0.646 | 0.646 |
| engolida | 0.103 | 0.108 | 0.108 |
| l'altre equip | 0.026 | 0.029 | 0.029 |
| la D | 0.015 | 0.015 | 0.014 |
| trencada | 0.007 | 0.006 | 0.006 |
| ajuntada, per sobre de l'altre equip | 0.133 | 0.137 | 0.137 |
| ajuntada, per sobre de la D | 0.002 | 0.001 | 0.001 |
| les vores | 0.066 | 0.058 | 0.058 |
| sobren a l'altre equip, per cada 100 | 8.692 | 7.103 | 7.079 |

**els quatre ×¼ junts**

| causa | A pilota morta | A fases | A fases àmplia |
|---|---|---|---|
| encertada | 0.626 | 0.627 | 0.628 |
| engolida | 0.101 | 0.107 | 0.107 |
| l'altre equip | 0.029 | 0.031 | 0.032 |
| la D | 0.029 | 0.028 | 0.025 |
| trencada | 0.009 | 0.006 | 0.006 |
| ajuntada, per sobre de l'altre equip | 0.132 | 0.136 | 0.137 |
| ajuntada, per sobre de la D | 0.001 | 0.001 | 0.001 |
| les vores | 0.072 | 0.063 | 0.063 |
| sobren a l'altre equip, per cada 100 | 8.686 | 6.916 | 6.898 |

**net**

| causa | A pilota morta | A fases | A fases àmplia |
|---|---|---|---|
| encertada | 0.761 | 0.754 | 0.753 |
| engolida | 0.071 | 0.075 | 0.075 |
| l'altre equip | 0.020 | 0.022 | 0.021 |
| la D | 0.005 | 0.005 | 0.005 |
| trencada | 0.004 | 0.004 | 0.004 |
| ajuntada, per sobre de l'altre equip | 0.091 | 0.096 | 0.096 |
| ajuntada, per sobre de la D | 0.001 | 0.001 | 0.001 |
| les vores | 0.046 | 0.043 | 0.044 |
| sobren a l'altre equip, per cada 100 | 6.589 | 5.724 | 5.748 |

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

A cada partit, amb els altres nou, als quatre ×¼ i a la mitjana dels nivells bo, mitjà i dolent; i el
que hi va triar la T3ak.

| partit | gamma | delta | marge_s | a la T3ak |
|---|---|---|---|---|
| dfl-J03WMX | 1 | 4 | 0 | 1, 1, 0 |
| dfl-J03WN1 | 1 | 4 | 0 | 1, 1, 0 |
| dfl-J03WOH | 1 | 4 | 0 | 1, 1, 0 |
| dfl-J03WOY | 1 | 4 | 0 | 1, 1, 0 |
| dfl-J03WPY | 1 | 4 | 0 | 1, 1, 0 |
| dfl-J03WQQ | 1 | 4 | 0 | 1, 1, 0 |
| dfl-J03WR9 | 1 | 4 | 0 | 1, 1, 0 |
| metrica-1 | 1 | 4 | 0 | 1, 1, 0 |
| metrica-2 | 1 | 4 | 0 | 1, 1, 0 |
| metrica-3 | 1 | 4 | 0 | 1, 1, 0 |

**A la vora de la graella:** marge_s = 0.

## L'spellF1 de cada mètode (mitjana dels deu partits, nivell mitjà)

**spellF1 a la veritat de toc**

| escenari | A xarxes, decodificador de toc | A equips sencers | A neteja d'aire | A pilota morta | A fases | A fases àmplia |
|---|---|---|---|---|---|---|
| net | 0.798 | 0.799 | 0.799 | 0.801 | 0.803 | 0.801 |
| curts ×¼ | 0.673 | 0.699 | 0.699 | 0.702 | 0.711 | 0.711 |
| llargs ×¼ | 0.651 | 0.688 | 0.688 | 0.691 | 0.704 | 0.703 |
| barreja ×¼ | 0.660 | 0.696 | 0.696 | 0.698 | 0.708 | 0.708 |
| aire ×¼ | 0.600 | 0.629 | 0.644 | 0.647 | 0.662 | 0.664 |
| curts | 0.636 | 0.665 | 0.665 | 0.668 | 0.679 | 0.679 |
| llargs | 0.599 | 0.640 | 0.640 | 0.645 | 0.658 | 0.659 |
| barreja | 0.605 | 0.646 | 0.646 | 0.650 | 0.660 | 0.662 |
| aire | 0.554 | 0.600 | 0.618 | 0.620 | 0.635 | 0.638 |
| soroll2 | 0.470 | 0.534 | 0.534 | 0.549 | 0.568 | 0.570 |
| partit ×¼ | 0.746 | 0.761 | 0.761 | 0.764 | 0.772 | 0.772 |

**spellF1 a la veritat de sempre**

| escenari | A xarxes, decodificador de toc | A equips sencers | A neteja d'aire | A pilota morta | A fases | A fases àmplia |
|---|---|---|---|---|---|---|
| net | 0.808 | 0.810 | 0.810 | 0.812 | 0.814 | 0.813 |
| curts ×¼ | 0.684 | 0.708 | 0.708 | 0.711 | 0.720 | 0.719 |
| llargs ×¼ | 0.662 | 0.700 | 0.700 | 0.703 | 0.717 | 0.716 |
| barreja ×¼ | 0.671 | 0.708 | 0.708 | 0.710 | 0.720 | 0.719 |
| aire ×¼ | 0.612 | 0.643 | 0.658 | 0.661 | 0.677 | 0.679 |
| curts | 0.644 | 0.674 | 0.674 | 0.677 | 0.689 | 0.689 |
| llargs | 0.607 | 0.648 | 0.648 | 0.652 | 0.667 | 0.668 |
| barreja | 0.616 | 0.656 | 0.656 | 0.660 | 0.670 | 0.672 |
| aire | 0.564 | 0.613 | 0.632 | 0.633 | 0.648 | 0.651 |
| soroll2 | 0.478 | 0.543 | 0.543 | 0.558 | 0.577 | 0.578 |
| partit ×¼ | 0.757 | 0.772 | 0.772 | 0.775 | 0.782 | 0.782 |

## Els decodificadors

A neteja d'aire, A pilota morta, A fases i A fases àmplia fan servir, a cada partit, el d'A equips sencers.

- **A equips sencers:** w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 16, durada mínima 12 (2 partits)
