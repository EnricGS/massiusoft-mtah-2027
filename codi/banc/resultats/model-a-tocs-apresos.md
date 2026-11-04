# Banc obert · Un detector de tocs après (T3u)

Generat amb `uv run python -I -m banc.model_a_tocs_apresos`. Dades obertes: 7 partits de DFL (IDSSE,
CC BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3u», i la capçalera de `banc/model_a_tocs_apresos.py`. Es puntua a la
veritat de toc.

**A xarxes** i **A sense pilota** són els de la T3t, amb les peces de la memòria cau (✓ comprovat: a cada
punt de la graella donen l'spellF1 del banc de la T3t). **A tocs apresos** és A sense pilota, amb el segon que
també rep les probabilitats d'un detector de tocs après.

## A tocs apresos contra A xarxes, decodificador de toc (spellF1): el criteri

| escenari | A xarxes, decodificador de toc | A tocs apresos | diferència | interval del 95 % | A tocs apresos guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.798 | 0.802 | +0.004 | +0.000 a +0.008 | 7 de 10 | no perd | ✓ |
| curts ×¼ | 0.673 | 0.695 | +0.022 | +0.014 a +0.029 | 10 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.651 | 0.671 | +0.020 | +0.013 a +0.026 | 10 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.660 | 0.679 | +0.019 | +0.012 a +0.026 | 9 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.600 | 0.625 | +0.025 | +0.018 a +0.032 | 10 de 10 | guanya clarament | ✗ |
| curts | 0.636 | 0.656 | +0.020 | +0.015 a +0.025 | 10 de 10 | no perd | ✓ |
| llargs | 0.599 | 0.619 | +0.019 | +0.013 a +0.026 | 10 de 10 | no perd | ✓ |
| barreja | 0.605 | 0.629 | +0.024 | +0.014 a +0.033 | 9 de 10 | no perd | ✓ |
| aire | 0.554 | 0.589 | +0.034 | +0.026 a +0.043 | 10 de 10 | no perd | ✓ |
| soroll2 | 0.470 | 0.520 | +0.049 | +0.038 a +0.061 | 10 de 10 | no perd | ✓ |
| partit ×¼ | 0.746 | 0.759 | +0.014 | +0.007 a +0.021 | 9 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1, el soroll2 i «partit ×¼» | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## A tocs apresos contra A sense pilota (spellF1)

| escenari | A sense pilota | A tocs apresos | diferència | interval del 95 % | A tocs apresos guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.802 | +0.003 | -0.002 a +0.008 | 7 de 10 |
| curts ×¼ | 0.692 | 0.695 | +0.003 | -0.001 a +0.006 | 8 de 10 |
| llargs ×¼ | 0.665 | 0.671 | +0.006 | +0.002 a +0.010 | 9 de 10 |
| barreja ×¼ | 0.677 | 0.679 | +0.002 | -0.001 a +0.007 | 5 de 10 |
| aire ×¼ | 0.623 | 0.625 | +0.002 | -0.002 a +0.006 | 7 de 10 |
| curts | 0.653 | 0.656 | +0.003 | -0.003 a +0.008 | 7 de 10 |
| llargs | 0.614 | 0.619 | +0.004 | +0.000 a +0.008 | 8 de 10 |
| barreja | 0.627 | 0.629 | +0.002 | -0.005 a +0.009 | 4 de 10 |
| aire | 0.582 | 0.589 | +0.006 | +0.001 a +0.012 | 8 de 10 |
| soroll2 | 0.508 | 0.520 | +0.012 | +0.006 a +0.017 | 10 de 10 |
| partit ×¼ | 0.755 | 0.759 | +0.005 | +0.002 a +0.007 | 9 de 10 |

## No passa: és el millor fins ara?

| | És el millor fins ara si | |
|---|---|---|
| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | ✗ |
| «partit ×¼» | la diferència no és negativa | ✓ |
| El net, els ×1 i el soroll2 | no perd (diferència ≥ −0.04) | ✓ |

**A tocs apresos no és el millor fins ara:** el pas següent es fa a sobre d'A sense pilota.

## A tocs apresos contra A xarxes, decodificador de toc, només els partits de dfl

| escenari | A xarxes, decodificador de toc | A tocs apresos | diferència | interval del 95 % | A tocs apresos guanya |
|---|---|---|---|---|---|
| net | 0.766 | 0.768 | +0.002 | -0.002 a +0.007 | 4 de 7 |
| curts ×¼ | 0.642 | 0.666 | +0.024 | +0.015 a +0.034 | 7 de 7 |
| llargs ×¼ | 0.621 | 0.642 | +0.021 | +0.013 a +0.029 | 7 de 7 |
| barreja ×¼ | 0.630 | 0.648 | +0.018 | +0.008 a +0.028 | 6 de 7 |
| aire ×¼ | 0.544 | 0.566 | +0.022 | +0.016 a +0.029 | 7 de 7 |
| curts | 0.607 | 0.627 | +0.020 | +0.013 a +0.026 | 7 de 7 |
| llargs | 0.564 | 0.587 | +0.023 | +0.015 a +0.032 | 7 de 7 |
| barreja | 0.571 | 0.597 | +0.026 | +0.016 a +0.033 | 7 de 7 |
| aire | 0.501 | 0.536 | +0.035 | +0.025 a +0.046 | 7 de 7 |
| soroll2 | 0.433 | 0.481 | +0.048 | +0.034 a +0.062 | 7 de 7 |
| partit ×¼ | 0.717 | 0.731 | +0.014 | +0.008 a +0.020 | 7 de 7 |

## A tocs apresos contra A sense pilota, només els partits de dfl

| escenari | A sense pilota | A tocs apresos | diferència | interval del 95 % | A tocs apresos guanya |
|---|---|---|---|---|---|
| net | 0.768 | 0.768 | -0.001 | -0.007 a +0.005 | 4 de 7 |
| curts ×¼ | 0.665 | 0.666 | +0.001 | -0.004 a +0.006 | 5 de 7 |
| llargs ×¼ | 0.636 | 0.642 | +0.005 | +0.000 a +0.011 | 6 de 7 |
| barreja ×¼ | 0.648 | 0.648 | +0.000 | -0.004 a +0.007 | 2 de 7 |
| aire ×¼ | 0.567 | 0.566 | -0.000 | -0.006 a +0.005 | 4 de 7 |
| curts | 0.625 | 0.627 | +0.002 | -0.005 a +0.009 | 5 de 7 |
| llargs | 0.582 | 0.587 | +0.005 | +0.002 a +0.009 | 6 de 7 |
| barreja | 0.597 | 0.597 | -0.000 | -0.009 a +0.009 | 2 de 7 |
| aire | 0.533 | 0.536 | +0.002 | -0.006 a +0.010 | 5 de 7 |
| soroll2 | 0.475 | 0.481 | +0.007 | +0.003 a +0.011 | 7 de 7 |
| partit ×¼ | 0.728 | 0.731 | +0.003 | -0.001 a +0.006 | 6 de 7 |

## A tocs apresos contra A xarxes, decodificador de toc, només els partits de metrica

| escenari | A xarxes, decodificador de toc | A tocs apresos | diferència | interval del 95 % | A tocs apresos guanya |
|---|---|---|---|---|---|
| net | 0.874 | 0.883 | +0.009 | +0.003 a +0.017 | 3 de 3 |
| curts ×¼ | 0.747 | 0.762 | +0.016 | +0.003 a +0.024 | 3 de 3 |
| llargs ×¼ | 0.723 | 0.740 | +0.017 | +0.007 a +0.031 | 3 de 3 |
| barreja ×¼ | 0.730 | 0.752 | +0.022 | +0.017 a +0.031 | 3 de 3 |
| aire ×¼ | 0.731 | 0.762 | +0.031 | +0.012 a +0.053 | 3 de 3 |
| curts | 0.702 | 0.723 | +0.021 | +0.013 a +0.029 | 3 de 3 |
| llargs | 0.682 | 0.692 | +0.010 | +0.003 a +0.019 | 3 de 3 |
| barreja | 0.684 | 0.704 | +0.020 | -0.010 a +0.035 | 2 de 3 |
| aire | 0.679 | 0.712 | +0.033 | +0.014 a +0.044 | 3 de 3 |
| soroll2 | 0.557 | 0.609 | +0.052 | +0.033 a +0.076 | 3 de 3 |
| partit ×¼ | 0.813 | 0.826 | +0.013 | -0.005 a +0.034 | 2 de 3 |

## A tocs apresos contra A sense pilota, només els partits de metrica

| escenari | A sense pilota | A tocs apresos | diferència | interval del 95 % | A tocs apresos guanya |
|---|---|---|---|---|---|
| net | 0.871 | 0.883 | +0.012 | +0.005 a +0.020 | 3 de 3 |
| curts ×¼ | 0.755 | 0.762 | +0.007 | +0.002 a +0.011 | 3 de 3 |
| llargs ×¼ | 0.733 | 0.740 | +0.007 | +0.003 a +0.013 | 3 de 3 |
| barreja ×¼ | 0.745 | 0.752 | +0.007 | +0.006 a +0.010 | 3 de 3 |
| aire ×¼ | 0.754 | 0.762 | +0.008 | +0.002 a +0.013 | 3 de 3 |
| curts | 0.719 | 0.723 | +0.004 | -0.006 a +0.013 | 2 de 3 |
| llargs | 0.691 | 0.692 | +0.002 | -0.008 a +0.013 | 2 de 3 |
| barreja | 0.698 | 0.704 | +0.006 | -0.002 a +0.019 | 2 de 3 |
| aire | 0.697 | 0.712 | +0.016 | +0.014 a +0.018 | 3 de 3 |
| soroll2 | 0.585 | 0.609 | +0.024 | +0.005 a +0.036 | 3 de 3 |
| partit ×¼ | 0.817 | 0.826 | +0.009 | +0.007 a +0.013 | 3 de 3 |

## Com encerta els tocs el detector

El detector entrenat amb els altres nou partits, a les parts puntuades. Als tocs dels esdeveniments,
la part on l'equip del toc és més probable que l'altre; i l'AUC de la probabilitat de toc (1 − P(cap))
per distingir les imatges a 3 o menys d'un toc de les altres (mitjana dels deu partits).

| escenari | n tocs | l'equip del toc | AUC |
|---|---|---|---|
| net | 14479 | 0.897 | 0.916 |
| curts ×¼ | 14479 | 0.860 | 0.861 |
| llargs ×¼ | 14479 | 0.833 | 0.847 |
| barreja ×¼ | 14479 | 0.844 | 0.851 |
| aire ×¼ | 14479 | 0.812 | 0.825 |
| curts | 14479 | 0.850 | 0.836 |
| llargs | 14479 | 0.822 | 0.822 |
| barreja | 14479 | 0.832 | 0.825 |
| aire | 14479 | 0.797 | 0.801 |
| soroll2 | 14479 | 0.795 | 0.755 |
| partit ×¼ | 14479 | 0.878 | 0.896 |

## Als canvis d'equip on es veu la pilota

Un canvi: el començament d'una possessió de la veritat de toc que ve de l'altre equip, amb la pilota a
la vista (com a `tocs_als_canvis.py`). *Troba el toc:* el detector après, si la probabilitat de toc de l'equip
nou hi arriba a 0.5 a ±0,5 s; el fet a mà (`cadena/tocs.py`), si hi té un toc de l'equip nou a
±0,5 s. *Tard:* a la primera mitja segona de la possessió, la predicció hi dona l'equip nou a menys de
la meitat de les imatges; a tots els canvis, i segons si el detector après hi troba el toc.

| escenari | n canvis | troba el toc: el detector après | troba el toc: el fet a mà | tard: A sense pilota | tard: A tocs apresos | tard si el troba: A sense pilota | tard si el troba: A tocs apresos | tard si no el troba: A sense pilota | tard si no el troba: A tocs apresos |
|---|---|---|---|---|---|---|---|---|---|
| net | 3091 | 0.735 | 0.662 | 0.218 | 0.218 | 0.112 | 0.101 | 0.511 | 0.541 |
| curts ×¼ | 1123 | 0.696 | 0.633 | 0.258 | 0.265 | 0.147 | 0.142 | 0.513 | 0.548 |
| llargs ×¼ | 1596 | 0.724 | 0.650 | 0.241 | 0.239 | 0.133 | 0.119 | 0.524 | 0.553 |
| barreja ×¼ | 1435 | 0.723 | 0.635 | 0.256 | 0.256 | 0.138 | 0.132 | 0.565 | 0.580 |
| aire ×¼ | 1488 | 0.727 | 0.485 | 0.349 | 0.345 | 0.265 | 0.254 | 0.571 | 0.586 |
| curts | 1123 | 0.782 | 0.574 | 0.364 | 0.367 | 0.251 | 0.247 | 0.771 | 0.796 |
| llargs | 1596 | 0.809 | 0.584 | 0.353 | 0.347 | 0.253 | 0.238 | 0.777 | 0.810 |
| barreja | 1435 | 0.795 | 0.566 | 0.374 | 0.369 | 0.266 | 0.257 | 0.796 | 0.803 |
| aire | 1488 | 0.797 | 0.421 | 0.440 | 0.422 | 0.366 | 0.336 | 0.732 | 0.762 |
| soroll2 | 1447 | 0.888 | 0.335 | 0.419 | 0.406 | 0.365 | 0.349 | 0.846 | 0.858 |
| partit ×¼ | 2766 | 0.727 | 0.644 | 0.247 | 0.248 | 0.135 | 0.127 | 0.546 | 0.568 |

## Els errors d'equip on es veu la pilota

On es veu la pilota i la veritat de toc és d'un equip: la part de les imatges on la predicció no hi
dona aquest equip, on hi dona l'altre, i on hi dona l'altre i el segon dubta (com a
`errors_amb_pilota.py`: la probabilitat de l'equip bo davant de l'altre, 0.1 o més).

| escenari | n imatges | errors · A sense pilota | errors · A tocs apresos | a l'altre equip · A sense pilota | a l'altre equip · A tocs apresos | on el segon dubta · A sense pilota | on el segon dubta · A tocs apresos |
|---|---|---|---|---|---|---|---|
| net | 810813 | 0.053 | 0.051 | 0.049 | 0.048 | 0.036 | 0.034 |
| curts ×¼ | 391354 | 0.055 | 0.055 | 0.050 | 0.050 | 0.038 | 0.038 |
| llargs ×¼ | 466858 | 0.056 | 0.055 | 0.051 | 0.050 | 0.039 | 0.037 |
| barreja ×¼ | 444753 | 0.055 | 0.055 | 0.051 | 0.052 | 0.038 | 0.038 |
| aire ×¼ | 445789 | 0.075 | 0.072 | 0.068 | 0.066 | 0.053 | 0.052 |
| curts | 391354 | 0.069 | 0.067 | 0.060 | 0.059 | 0.047 | 0.045 |
| llargs | 466858 | 0.077 | 0.075 | 0.069 | 0.066 | 0.053 | 0.051 |
| barreja | 444753 | 0.075 | 0.073 | 0.068 | 0.066 | 0.053 | 0.051 |
| aire | 445789 | 0.093 | 0.089 | 0.079 | 0.074 | 0.062 | 0.059 |
| soroll2 | 444190 | 0.100 | 0.096 | 0.094 | 0.091 | 0.076 | 0.073 |
| partit ×¼ | 722620 | 0.059 | 0.058 | 0.056 | 0.054 | 0.042 | 0.041 |

## L'spellF1 de cada mètode (mitjana dels deu partits)

**spellF1 a la veritat de toc**

| escenari | A xarxes | A xarxes, decodificador de toc | A sense pilota | A tocs apresos |
|---|---|---|---|---|
| net | 0.799 | 0.798 | 0.799 | 0.802 |
| curts ×¼ | 0.674 | 0.673 | 0.692 | 0.695 |
| llargs ×¼ | 0.652 | 0.651 | 0.665 | 0.671 |
| barreja ×¼ | 0.660 | 0.660 | 0.677 | 0.679 |
| aire ×¼ | 0.600 | 0.600 | 0.623 | 0.625 |
| curts | 0.636 | 0.636 | 0.653 | 0.656 |
| llargs | 0.599 | 0.599 | 0.614 | 0.619 |
| barreja | 0.605 | 0.605 | 0.627 | 0.629 |
| aire | 0.555 | 0.554 | 0.582 | 0.589 |
| soroll2 | 0.471 | 0.470 | 0.508 | 0.520 |
| partit ×¼ | 0.746 | 0.746 | 0.755 | 0.759 |

**spellF1 a la veritat de sempre**

| escenari | A xarxes | A xarxes, decodificador de toc | A sense pilota | A tocs apresos |
|---|---|---|---|---|
| net | 0.808 | 0.808 | 0.810 | 0.815 |
| curts ×¼ | 0.684 | 0.684 | 0.700 | 0.705 |
| llargs ×¼ | 0.662 | 0.662 | 0.675 | 0.682 |
| barreja ×¼ | 0.671 | 0.671 | 0.688 | 0.692 |
| aire ×¼ | 0.612 | 0.612 | 0.635 | 0.638 |
| curts | 0.644 | 0.644 | 0.661 | 0.665 |
| llargs | 0.607 | 0.607 | 0.622 | 0.628 |
| barreja | 0.616 | 0.616 | 0.639 | 0.642 |
| aire | 0.564 | 0.564 | 0.593 | 0.599 |
| soroll2 | 0.478 | 0.478 | 0.515 | 0.529 |
| partit ×¼ | 0.757 | 0.757 | 0.766 | 0.771 |

## Els decodificadors triats

- **A xarxes:** w = 4, λ = 64, durada mínima 12 (1 partits); w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 32, durada mínima 1 (1 partits)
- **A xarxes, decodificador de toc:** w = 4, λ = 64, durada mínima 1 (1 partits); w = 4, λ = 32, durada mínima 12 (6 partits); w = 4, λ = 32, durada mínima 1 (3 partits)
- **A sense pilota:** w = 4, λ = 32, durada mínima 12 (9 partits); w = 4, λ = 16, durada mínima 12 (1 partits)
- **A tocs apresos:** w = 4, λ = 32, durada mínima 12 (10 partits)
