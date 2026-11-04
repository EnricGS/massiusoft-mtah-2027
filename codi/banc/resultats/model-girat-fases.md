# Banc obert · La pilota morta i les fases a sobre del camp girat (T3am)

Generat amb `uv run python -I -m banc.model_girat_fases`. Dades obertes: 7 partits de DFL (IDSSE, CC BY
4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el criteri:
`docs/pla-tocs.md`, «T3am», i la capçalera de `banc/model_girat_fases.py`. Es puntua a la veritat de toc.

**A xarxes, decodificador de toc** i **A equips sencers** són els de la T3v, **A pilota creïble**, el de la T3w, **A neteja d'aire**,
el de la T3ac, **A camp girat**, el de la T3ad, i **A fases**, el de la T3ak (✓ comprovat). **A girat amb fases** és
A camp girat amb la pilota morta i les fases a sobre, amb els punts triats de nou. ✓ Comprovat: no dona mai
la D a una imatge netejada; A camp girat d'aquí dona l'spellF1 de la T3ad; sense etiquetes ni fases, A girat amb fases
és exactament A camp girat; i sense fases, exactament A girat amb pilota morta.

## Amb el nivell mitjà: A girat amb fases contra A xarxes, decodificador de toc (spellF1), el criteri

| escenari | A xarxes, decodificador de toc | A girat amb fases | diferència | interval del 95 % | A girat amb fases guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.798 | 0.809 | +0.011 | -0.000 a +0.023 | 8 de 10 | no perd | ✓ |
| curts ×¼ | 0.673 | 0.718 | +0.044 | +0.037 a +0.053 | 10 de 10 | guanya clarament | ✓ |
| llargs ×¼ | 0.651 | 0.714 | +0.062 | +0.051 a +0.074 | 10 de 10 | guanya clarament | ✓ |
| barreja ×¼ | 0.660 | 0.718 | +0.058 | +0.053 a +0.062 | 10 de 10 | guanya clarament | ✓ |
| aire ×¼ | 0.600 | 0.676 | +0.076 | +0.070 a +0.082 | 10 de 10 | guanya clarament | ✓ |
| curts | 0.636 | 0.693 | +0.057 | +0.051 a +0.064 | 10 de 10 | no perd | ✓ |
| llargs | 0.599 | 0.674 | +0.074 | +0.062 a +0.086 | 10 de 10 | no perd | ✓ |
| barreja | 0.605 | 0.675 | +0.070 | +0.058 a +0.081 | 10 de 10 | no perd | ✓ |
| aire | 0.554 | 0.652 | +0.098 | +0.092 a +0.103 | 10 de 10 | no perd | ✓ |
| soroll2 | 0.470 | 0.600 | +0.130 | +0.122 a +0.138 | 10 de 10 | no perd | ✓ |
| partit ×¼ | 0.746 | 0.772 | +0.026 | +0.015 a +0.036 | 9 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✓ |
| El net, els ×1, el soroll2 i «partit ×¼» | no perd a cap (diferència ≥ −0.04) | ✓ |

**Passa.**

## Amb els nivells dolent i cap: A girat amb fases contra A neteja d'aire, la segona part del criteri

| Nivell | curts ×¼ | llargs ×¼ | barreja ×¼ | aire ×¼ | partit ×¼ | No baixa de −0.005 |
|---|---|---|---|---|---|---|
| dolent | +0.0065 | +0.0113 | +0.0063 | +0.0115 | -0.0027 | ✓ |
| cap | +0.0037 | +0.0116 | +0.0098 | +0.0123 | -0.0034 | ✓ |

**A girat amb fases passa el criteri sencer.**

## Amb el nivell bo: A girat amb fases contra A fases (spellF1)

| escenari | A fases | A girat amb fases | diferència | interval del 95 % | A girat amb fases guanya |
|---|---|---|---|---|---|
| net | 0.832 | 0.834 | +0.002 | -0.004 a +0.007 | 5 de 10 |
| curts ×¼ | 0.758 | 0.762 | +0.004 | -0.001 a +0.009 | 7 de 10 |
| llargs ×¼ | 0.753 | 0.766 | +0.013 | +0.006 a +0.018 | 9 de 10 |
| barreja ×¼ | 0.750 | 0.757 | +0.007 | -0.001 a +0.015 | 6 de 10 |
| aire ×¼ | 0.721 | 0.728 | +0.007 | -0.000 a +0.015 | 9 de 10 |
| curts | 0.737 | 0.751 | +0.014 | +0.007 a +0.020 | 9 de 10 |
| llargs | 0.716 | 0.726 | +0.010 | +0.006 a +0.014 | 9 de 10 |
| barreja | 0.720 | 0.732 | +0.012 | +0.005 a +0.018 | 8 de 10 |
| aire | 0.698 | 0.709 | +0.010 | +0.005 a +0.016 | 8 de 10 |
| soroll2 | 0.649 | 0.679 | +0.030 | +0.024 a +0.035 | 10 de 10 |
| partit ×¼ | 0.806 | 0.810 | +0.004 | -0.000 a +0.009 | 7 de 10 |

## Amb el nivell mitjà: A girat amb fases contra A fases (spellF1)

| escenari | A fases | A girat amb fases | diferència | interval del 95 % | A girat amb fases guanya |
|---|---|---|---|---|---|
| net | 0.803 | 0.809 | +0.006 | +0.001 a +0.012 | 7 de 10 |
| curts ×¼ | 0.711 | 0.718 | +0.007 | -0.000 a +0.013 | 8 de 10 |
| llargs ×¼ | 0.704 | 0.714 | +0.009 | +0.002 a +0.017 | 7 de 10 |
| barreja ×¼ | 0.708 | 0.718 | +0.009 | +0.003 a +0.016 | 9 de 10 |
| aire ×¼ | 0.662 | 0.676 | +0.015 | +0.010 a +0.020 | 9 de 10 |
| curts | 0.679 | 0.693 | +0.013 | +0.008 a +0.019 | 9 de 10 |
| llargs | 0.658 | 0.674 | +0.016 | +0.009 a +0.022 | 9 de 10 |
| barreja | 0.660 | 0.675 | +0.015 | +0.008 a +0.022 | 8 de 10 |
| aire | 0.635 | 0.652 | +0.017 | +0.011 a +0.025 | 9 de 10 |
| soroll2 | 0.568 | 0.600 | +0.032 | +0.027 a +0.036 | 10 de 10 |
| partit ×¼ | 0.772 | 0.772 | -0.000 | -0.004 a +0.004 | 4 de 10 |

## Amb el nivell dolent: A girat amb fases contra A fases (spellF1)

| escenari | A fases | A girat amb fases | diferència | interval del 95 % | A girat amb fases guanya |
|---|---|---|---|---|---|
| net | 0.797 | 0.800 | +0.003 | -0.002 a +0.009 | 6 de 10 |
| curts ×¼ | 0.698 | 0.706 | +0.008 | +0.002 a +0.013 | 8 de 10 |
| llargs ×¼ | 0.687 | 0.699 | +0.012 | +0.006 a +0.019 | 9 de 10 |
| barreja ×¼ | 0.695 | 0.703 | +0.008 | +0.004 a +0.012 | 8 de 10 |
| aire ×¼ | 0.644 | 0.656 | +0.011 | +0.006 a +0.016 | 9 de 10 |
| curts | 0.660 | 0.674 | +0.014 | +0.009 a +0.020 | 10 de 10 |
| llargs | 0.641 | 0.655 | +0.014 | +0.007 a +0.019 | 9 de 10 |
| barreja | 0.646 | 0.661 | +0.015 | +0.007 a +0.021 | 9 de 10 |
| aire | 0.614 | 0.627 | +0.013 | +0.008 a +0.019 | 10 de 10 |
| soroll2 | 0.546 | 0.577 | +0.031 | +0.024 a +0.038 | 10 de 10 |
| partit ×¼ | 0.760 | 0.758 | -0.001 | -0.006 a +0.004 | 5 de 10 |

## Amb el nivell cap: A girat amb fases contra A fases (spellF1)

| escenari | A fases | A girat amb fases | diferència | interval del 95 % | A girat amb fases guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.803 | +0.003 | -0.004 a +0.011 | 5 de 10 |
| curts ×¼ | 0.699 | 0.703 | +0.004 | -0.001 a +0.008 | 7 de 10 |
| llargs ×¼ | 0.688 | 0.700 | +0.012 | +0.006 a +0.017 | 9 de 10 |
| barreja ×¼ | 0.696 | 0.706 | +0.010 | +0.007 a +0.013 | 9 de 10 |
| aire ×¼ | 0.644 | 0.656 | +0.012 | +0.005 a +0.020 | 9 de 10 |
| curts | 0.665 | 0.678 | +0.014 | +0.009 a +0.019 | 9 de 10 |
| llargs | 0.640 | 0.656 | +0.016 | +0.013 a +0.019 | 10 de 10 |
| barreja | 0.646 | 0.666 | +0.019 | +0.012 a +0.026 | 9 de 10 |
| aire | 0.618 | 0.632 | +0.014 | +0.007 a +0.022 | 9 de 10 |
| soroll2 | 0.534 | 0.574 | +0.040 | +0.035 a +0.045 | 10 de 10 |
| partit ×¼ | 0.761 | 0.758 | -0.003 | -0.009 a +0.003 | 2 de 10 |

## Amb el nivell bo: A girat amb fases contra A camp girat (spellF1)

| escenari | A camp girat | A girat amb fases | diferència | interval del 95 % | A girat amb fases guanya |
|---|---|---|---|---|---|
| net | 0.803 | 0.834 | +0.031 | +0.026 a +0.037 | 10 de 10 |
| curts ×¼ | 0.703 | 0.762 | +0.059 | +0.054 a +0.067 | 10 de 10 |
| llargs ×¼ | 0.700 | 0.766 | +0.066 | +0.060 a +0.073 | 10 de 10 |
| barreja ×¼ | 0.706 | 0.757 | +0.051 | +0.044 a +0.058 | 10 de 10 |
| aire ×¼ | 0.656 | 0.728 | +0.072 | +0.067 a +0.078 | 10 de 10 |
| curts | 0.678 | 0.751 | +0.072 | +0.065 a +0.080 | 10 de 10 |
| llargs | 0.656 | 0.726 | +0.070 | +0.066 a +0.075 | 10 de 10 |
| barreja | 0.666 | 0.732 | +0.066 | +0.060 a +0.072 | 10 de 10 |
| aire | 0.632 | 0.709 | +0.077 | +0.070 a +0.083 | 10 de 10 |
| soroll2 | 0.574 | 0.679 | +0.105 | +0.097 a +0.113 | 10 de 10 |
| partit ×¼ | 0.758 | 0.810 | +0.053 | +0.042 a +0.063 | 10 de 10 |

## Amb el nivell mitjà: A girat amb fases contra A camp girat (spellF1)

| escenari | A camp girat | A girat amb fases | diferència | interval del 95 % | A girat amb fases guanya |
|---|---|---|---|---|---|
| net | 0.803 | 0.809 | +0.006 | +0.001 a +0.010 | 9 de 10 |
| curts ×¼ | 0.703 | 0.718 | +0.015 | +0.009 a +0.020 | 9 de 10 |
| llargs ×¼ | 0.700 | 0.714 | +0.014 | +0.011 a +0.017 | 10 de 10 |
| barreja ×¼ | 0.706 | 0.718 | +0.012 | +0.008 a +0.015 | 9 de 10 |
| aire ×¼ | 0.656 | 0.676 | +0.020 | +0.016 a +0.024 | 10 de 10 |
| curts | 0.678 | 0.693 | +0.014 | +0.010 a +0.019 | 10 de 10 |
| llargs | 0.656 | 0.674 | +0.018 | +0.013 a +0.024 | 10 de 10 |
| barreja | 0.666 | 0.675 | +0.010 | +0.004 a +0.015 | 8 de 10 |
| aire | 0.632 | 0.652 | +0.020 | +0.013 a +0.028 | 9 de 10 |
| soroll2 | 0.574 | 0.600 | +0.027 | +0.020 a +0.033 | 10 de 10 |
| partit ×¼ | 0.758 | 0.772 | +0.014 | +0.007 a +0.021 | 9 de 10 |

## Amb el nivell dolent: A girat amb fases contra A camp girat (spellF1)

| escenari | A camp girat | A girat amb fases | diferència | interval del 95 % | A girat amb fases guanya |
|---|---|---|---|---|---|
| net | 0.803 | 0.800 | -0.003 | -0.005 a -0.000 | 2 de 10 |
| curts ×¼ | 0.703 | 0.706 | +0.003 | -0.001 a +0.007 | 7 de 10 |
| llargs ×¼ | 0.700 | 0.699 | -0.000 | -0.004 a +0.004 | 5 de 10 |
| barreja ×¼ | 0.706 | 0.703 | -0.004 | -0.007 a +0.000 | 3 de 10 |
| aire ×¼ | 0.656 | 0.656 | -0.001 | -0.004 a +0.002 | 5 de 10 |
| curts | 0.678 | 0.674 | -0.004 | -0.010 a +0.002 | 2 de 10 |
| llargs | 0.656 | 0.655 | -0.001 | -0.007 a +0.006 | 3 de 10 |
| barreja | 0.666 | 0.661 | -0.004 | -0.009 a +0.001 | 3 de 10 |
| aire | 0.632 | 0.627 | -0.005 | -0.013 a +0.003 | 5 de 10 |
| soroll2 | 0.574 | 0.577 | +0.003 | -0.000 a +0.006 | 6 de 10 |
| partit ×¼ | 0.758 | 0.758 | +0.001 | -0.002 a +0.004 | 5 de 10 |

## Amb el nivell cap: A girat amb fases contra A camp girat (spellF1)

| escenari | A camp girat | A girat amb fases | diferència | interval del 95 % | A girat amb fases guanya |
|---|---|---|---|---|---|
| net | 0.803 | 0.803 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| curts ×¼ | 0.703 | 0.703 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| llargs ×¼ | 0.700 | 0.700 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| barreja ×¼ | 0.706 | 0.706 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| aire ×¼ | 0.656 | 0.656 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| curts | 0.678 | 0.678 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| llargs | 0.656 | 0.656 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| barreja | 0.666 | 0.666 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| aire | 0.632 | 0.632 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| soroll2 | 0.574 | 0.574 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| partit ×¼ | 0.758 | 0.758 | +0.000 | +0.000 a +0.000 | 0 de 10 |

## A girat amb fases contra A xarxes, decodificador de toc, nivell mitjà, només els partits de dfl

| escenari | A xarxes, decodificador de toc | A girat amb fases | diferència | interval del 95 % | A girat amb fases guanya |
|---|---|---|---|---|---|
| net | 0.766 | 0.777 | +0.011 | +0.004 a +0.018 | 6 de 7 |
| curts ×¼ | 0.642 | 0.689 | +0.047 | +0.037 a +0.059 | 7 de 7 |
| llargs ×¼ | 0.621 | 0.681 | +0.061 | +0.046 a +0.077 | 7 de 7 |
| barreja ×¼ | 0.630 | 0.685 | +0.055 | +0.050 a +0.060 | 7 de 7 |
| aire ×¼ | 0.544 | 0.624 | +0.080 | +0.073 a +0.087 | 7 de 7 |
| curts | 0.607 | 0.663 | +0.056 | +0.049 a +0.066 | 7 de 7 |
| llargs | 0.564 | 0.638 | +0.074 | +0.057 a +0.090 | 7 de 7 |
| barreja | 0.571 | 0.641 | +0.070 | +0.056 a +0.081 | 7 de 7 |
| aire | 0.501 | 0.605 | +0.104 | +0.097 a +0.110 | 7 de 7 |
| soroll2 | 0.433 | 0.552 | +0.119 | +0.108 a +0.129 | 7 de 7 |
| partit ×¼ | 0.717 | 0.738 | +0.021 | +0.010 a +0.031 | 6 de 7 |

## A girat amb fases contra A fases, nivell mitjà, només els partits de dfl

| escenari | A fases | A girat amb fases | diferència | interval del 95 % | A girat amb fases guanya |
|---|---|---|---|---|---|
| net | 0.772 | 0.777 | +0.004 | -0.002 a +0.010 | 5 de 7 |
| curts ×¼ | 0.682 | 0.689 | +0.007 | -0.002 a +0.016 | 5 de 7 |
| llargs ×¼ | 0.674 | 0.681 | +0.007 | -0.001 a +0.017 | 4 de 7 |
| barreja ×¼ | 0.678 | 0.685 | +0.008 | -0.002 a +0.016 | 6 de 7 |
| aire ×¼ | 0.611 | 0.624 | +0.014 | +0.007 a +0.021 | 6 de 7 |
| curts | 0.651 | 0.663 | +0.012 | +0.005 a +0.020 | 6 de 7 |
| llargs | 0.623 | 0.638 | +0.015 | +0.006 a +0.024 | 6 de 7 |
| barreja | 0.623 | 0.641 | +0.018 | +0.009 a +0.027 | 6 de 7 |
| aire | 0.586 | 0.605 | +0.019 | +0.017 a +0.023 | 7 de 7 |
| soroll2 | 0.519 | 0.552 | +0.033 | +0.028 a +0.038 | 7 de 7 |
| partit ×¼ | 0.741 | 0.738 | -0.003 | -0.008 a +0.002 | 2 de 7 |

## A girat amb fases contra A xarxes, decodificador de toc, nivell mitjà, només els partits de metrica

| escenari | A xarxes, decodificador de toc | A girat amb fases | diferència | interval del 95 % | A girat amb fases guanya |
|---|---|---|---|---|---|
| net | 0.874 | 0.884 | +0.011 | -0.023 a +0.052 | 2 de 3 |
| curts ×¼ | 0.747 | 0.784 | +0.038 | +0.033 a +0.047 | 3 de 3 |
| llargs ×¼ | 0.723 | 0.789 | +0.066 | +0.051 a +0.076 | 3 de 3 |
| barreja ×¼ | 0.730 | 0.794 | +0.064 | +0.054 a +0.072 | 3 de 3 |
| aire ×¼ | 0.731 | 0.797 | +0.066 | +0.051 a +0.074 | 3 de 3 |
| curts | 0.702 | 0.762 | +0.060 | +0.054 a +0.068 | 3 de 3 |
| llargs | 0.682 | 0.757 | +0.075 | +0.063 a +0.087 | 3 de 3 |
| barreja | 0.684 | 0.755 | +0.071 | +0.040 a +0.087 | 3 de 3 |
| aire | 0.679 | 0.762 | +0.083 | +0.069 a +0.095 | 3 de 3 |
| soroll2 | 0.557 | 0.714 | +0.157 | +0.152 a +0.163 | 3 de 3 |
| partit ×¼ | 0.813 | 0.851 | +0.039 | +0.005 a +0.056 | 3 de 3 |

## A girat amb fases contra A fases, nivell mitjà, només els partits de metrica

| escenari | A fases | A girat amb fases | diferència | interval del 95 % | A girat amb fases guanya |
|---|---|---|---|---|---|
| net | 0.873 | 0.884 | +0.012 | -0.002 a +0.027 | 2 de 3 |
| curts ×¼ | 0.779 | 0.784 | +0.006 | +0.001 a +0.014 | 3 de 3 |
| llargs ×¼ | 0.775 | 0.789 | +0.014 | +0.001 a +0.034 | 3 de 3 |
| barreja ×¼ | 0.780 | 0.794 | +0.014 | +0.009 a +0.017 | 3 de 3 |
| aire ×¼ | 0.781 | 0.797 | +0.017 | +0.014 a +0.020 | 3 de 3 |
| curts | 0.747 | 0.762 | +0.016 | +0.010 a +0.022 | 3 de 3 |
| llargs | 0.740 | 0.757 | +0.017 | +0.007 a +0.023 | 3 de 3 |
| barreja | 0.746 | 0.755 | +0.009 | -0.002 a +0.017 | 2 de 3 |
| aire | 0.750 | 0.762 | +0.013 | -0.008 a +0.037 | 2 de 3 |
| soroll2 | 0.684 | 0.714 | +0.030 | +0.019 a +0.037 | 3 de 3 |
| partit ×¼ | 0.845 | 0.851 | +0.006 | -0.000 a +0.015 | 2 de 3 |

## A girat amb fases contra A xarxes, decodificador de toc, nivell bo

| escenari | A xarxes, decodificador de toc | A girat amb fases | diferència | interval del 95 % | A girat amb fases guanya |
|---|---|---|---|---|---|
| net | 0.798 | 0.834 | +0.036 | +0.027 a +0.046 | 10 de 10 |
| curts ×¼ | 0.673 | 0.762 | +0.089 | +0.078 a +0.102 | 10 de 10 |
| llargs ×¼ | 0.651 | 0.766 | +0.114 | +0.103 a +0.127 | 10 de 10 |
| barreja ×¼ | 0.660 | 0.757 | +0.097 | +0.088 a +0.106 | 10 de 10 |
| aire ×¼ | 0.600 | 0.728 | +0.128 | +0.119 a +0.138 | 10 de 10 |
| curts | 0.636 | 0.751 | +0.115 | +0.107 a +0.123 | 10 de 10 |
| llargs | 0.599 | 0.726 | +0.127 | +0.115 a +0.138 | 10 de 10 |
| barreja | 0.605 | 0.732 | +0.127 | +0.115 a +0.141 | 10 de 10 |
| aire | 0.554 | 0.709 | +0.154 | +0.148 a +0.162 | 10 de 10 |
| soroll2 | 0.470 | 0.679 | +0.208 | +0.199 a +0.218 | 10 de 10 |
| partit ×¼ | 0.746 | 0.810 | +0.065 | +0.052 a +0.077 | 10 de 10 |

## On falla, abans i després

Amb el nivell mitjà, les causes de `banc/on_falla.py`: la part de les possessions de la veritat de
cada causa, i les predites que sobren a l'altre equip per cada 100 possessions de la veritat.

**curts ×¼**

| causa | A pilota morta | A fases | A girat amb fases |
|---|---|---|---|
| encertada | 0.647 | 0.646 | 0.653 |
| engolida | 0.103 | 0.108 | 0.105 |
| l'altre equip | 0.026 | 0.029 | 0.027 |
| la D | 0.015 | 0.015 | 0.016 |
| trencada | 0.007 | 0.006 | 0.005 |
| ajuntada, per sobre de l'altre equip | 0.133 | 0.137 | 0.133 |
| ajuntada, per sobre de la D | 0.002 | 0.001 | 0.001 |
| les vores | 0.066 | 0.058 | 0.059 |
| sobren a l'altre equip, per cada 100 | 8.692 | 7.103 | 6.986 |

**els quatre ×¼ junts**

| causa | A pilota morta | A fases | A girat amb fases |
|---|---|---|---|
| encertada | 0.626 | 0.627 | 0.639 |
| engolida | 0.101 | 0.107 | 0.103 |
| l'altre equip | 0.029 | 0.031 | 0.030 |
| la D | 0.029 | 0.028 | 0.027 |
| trencada | 0.009 | 0.006 | 0.006 |
| ajuntada, per sobre de l'altre equip | 0.132 | 0.136 | 0.131 |
| ajuntada, per sobre de la D | 0.001 | 0.001 | 0.001 |
| les vores | 0.072 | 0.063 | 0.063 |
| sobren a l'altre equip, per cada 100 | 8.686 | 6.916 | 6.776 |

**net**

| causa | A pilota morta | A fases | A girat amb fases |
|---|---|---|---|
| encertada | 0.761 | 0.754 | 0.759 |
| engolida | 0.071 | 0.075 | 0.074 |
| l'altre equip | 0.020 | 0.022 | 0.023 |
| la D | 0.005 | 0.005 | 0.005 |
| trencada | 0.004 | 0.004 | 0.004 |
| ajuntada, per sobre de l'altre equip | 0.091 | 0.096 | 0.093 |
| ajuntada, per sobre de la D | 0.001 | 0.001 | 0.000 |
| les vores | 0.046 | 0.043 | 0.042 |
| sobren a l'altre equip, per cada 100 | 6.589 | 5.724 | 5.584 |

## Les fases simulades

A curts ×¼, amb les llavors de provar, la mitjana dels deu partits: quantes fases, i la part de les
imatges on se'n resta (dins d'una fase d'un sol equip, sense el marge triat).

| nivell | fases | part_dins |
|---|---|---|
| bo | 264.000 | 0.459 |
| mitjà | 141.800 | 0.285 |
| dolent | 100.600 | 0.193 |
| cap | 0.000 | 0.000 |

## Els punts triats

A cada partit, amb els altres nou, als quatre ×¼ i a la mitjana dels nivells bo, mitjà i dolent; i el que
hi van triar la T3ah i la T3ak. La pilota morta: `beta_d`, la forma, la durada i `marge_s`; les fases:
`gamma`, `delta` i `marge_s`.

| partit | pilota morta | a la T3ah | fases | a la T3ak |
|---|---|---|---|---|
| dfl-J03WMX | 1, per tipus, 1.5, 0 | 1, per tipus, 1.5, 0 | 1, 1, 0 | 1, 1, 0 |
| dfl-J03WN1 | 1, per tipus, 1.5, 0 | 1, per tipus, 1.5, 0 | 1, 1, 0 | 1, 1, 0 |
| dfl-J03WOH | 1, per tipus, 1.5, 0 | 1, per tipus, 1.5, 0 | 1, 1, 0 | 1, 1, 0 |
| dfl-J03WOY | 1, per tipus, 1.5, 0 | 1, per tipus, 1.5, 1 | 1, 1, 0 | 1, 1, 0 |
| dfl-J03WPY | 1, per tipus, 1.5, 0 | 1, per tipus, 1.5, 0 | 1, 1, 0 | 1, 1, 0 |
| dfl-J03WQQ | 1, per tipus, 1.5, 0 | 1, per tipus, 1.5, 0 | 1, 1, 0 | 1, 1, 0 |
| dfl-J03WR9 | 1, per tipus, 1.5, 0 | 1, per tipus, 1.5, 1 | 1, 1, 0 | 1, 1, 0 |
| metrica-1 | 1, per tipus, 1.5, 0 | 1, per tipus, 1.5, 0 | 1, 1, 0 | 1, 1, 0 |
| metrica-2 | 1, per tipus, 1.5, 0 | 1, per tipus, 1.5, 0 | 1, 1, 0 | 1, 1, 0 |
| metrica-3 | 1, per tipus, 1.5, 0 | 1, per tipus, 1.5, 0 | 1, 1, 0 | 1, 1, 0 |

**La pilota morta, a la vora de la graella:** `beta_d` = 1, `marge_s` = 0, `durada` = 1.5 (per tipus).
Les fases: **A la vora de la graella:** gamma = 1, delta = 1, marge_s = 0.

## L'spellF1 de cada mètode (mitjana dels deu partits, nivell mitjà)

**spellF1 a la veritat de toc**

| escenari | A xarxes, decodificador de toc | A neteja d'aire | A camp girat | A fases | A girat amb pilota morta | A girat amb fases |
|---|---|---|---|---|---|---|
| net | 0.798 | 0.799 | 0.803 | 0.803 | 0.804 | 0.809 |
| curts ×¼ | 0.673 | 0.699 | 0.703 | 0.711 | 0.704 | 0.718 |
| llargs ×¼ | 0.651 | 0.688 | 0.700 | 0.704 | 0.704 | 0.714 |
| barreja ×¼ | 0.660 | 0.696 | 0.706 | 0.708 | 0.706 | 0.718 |
| aire ×¼ | 0.600 | 0.644 | 0.656 | 0.662 | 0.660 | 0.676 |
| curts | 0.636 | 0.665 | 0.678 | 0.679 | 0.682 | 0.693 |
| llargs | 0.599 | 0.640 | 0.656 | 0.658 | 0.660 | 0.674 |
| barreja | 0.605 | 0.646 | 0.666 | 0.660 | 0.667 | 0.675 |
| aire | 0.554 | 0.618 | 0.632 | 0.635 | 0.636 | 0.652 |
| soroll2 | 0.470 | 0.534 | 0.574 | 0.568 | 0.584 | 0.600 |
| partit ×¼ | 0.746 | 0.761 | 0.758 | 0.772 | 0.761 | 0.772 |

**spellF1 a la veritat de sempre**

| escenari | A xarxes, decodificador de toc | A neteja d'aire | A camp girat | A fases | A girat amb pilota morta | A girat amb fases |
|---|---|---|---|---|---|---|
| net | 0.808 | 0.810 | 0.812 | 0.814 | 0.814 | 0.818 |
| curts ×¼ | 0.684 | 0.708 | 0.712 | 0.720 | 0.713 | 0.726 |
| llargs ×¼ | 0.662 | 0.700 | 0.710 | 0.717 | 0.714 | 0.725 |
| barreja ×¼ | 0.671 | 0.708 | 0.719 | 0.720 | 0.719 | 0.729 |
| aire ×¼ | 0.612 | 0.658 | 0.669 | 0.677 | 0.672 | 0.690 |
| curts | 0.644 | 0.674 | 0.688 | 0.689 | 0.691 | 0.704 |
| llargs | 0.607 | 0.648 | 0.665 | 0.667 | 0.669 | 0.682 |
| barreja | 0.616 | 0.656 | 0.678 | 0.670 | 0.679 | 0.688 |
| aire | 0.564 | 0.632 | 0.643 | 0.648 | 0.646 | 0.662 |
| soroll2 | 0.478 | 0.543 | 0.584 | 0.577 | 0.595 | 0.610 |
| partit ×¼ | 0.757 | 0.772 | 0.770 | 0.782 | 0.774 | 0.784 |

## Els decodificadors

A girat amb pilota morta i A girat amb fases fan servir, a cada partit, el d'A camp girat; A fases, el d'A equips sencers.

- **A camp girat:** w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 32, durada mínima 25 (2 partits)
- **A equips sencers:** w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 16, durada mínima 12 (2 partits)
