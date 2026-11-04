# Banc obert · Les xarxes aprenen més a prop dels canvis (T3z)

Generat amb `uv run python -I -m banc.model_mostres_canvis`. Dades obertes: 7 partits de DFL (IDSSE, CC
BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3z», i la capçalera de `banc/model_mostres_canvis.py`. Es puntua a la
veritat de toc.

**A xarxes, decodificador de toc** i **A equips sencers** són els de la T3v, amb les peces de la memòria cau (✓ comprovat: a
cada punt de la graella donen l'spellF1 del banc de la T3v). **A mostres als canvis** és A equips sencers, amb les
xarxes que també aprenen una de cada 2 imatges a ±0,5 s de cada canvi d'equip.

## A mostres als canvis contra A xarxes, decodificador de toc (spellF1): el criteri

| escenari | A xarxes, decodificador de toc | A mostres als canvis | diferència | interval del 95 % | A mostres als canvis guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.798 | 0.799 | +0.001 | -0.004 a +0.007 | 4 de 10 | no perd | ✓ |
| curts ×¼ | 0.673 | 0.698 | +0.025 | +0.018 a +0.032 | 10 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.651 | 0.687 | +0.035 | +0.027 a +0.042 | 10 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.660 | 0.696 | +0.036 | +0.028 a +0.044 | 10 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.600 | 0.628 | +0.028 | +0.019 a +0.035 | 10 de 10 | guanya clarament | ✗ |
| curts | 0.636 | 0.665 | +0.029 | +0.024 a +0.035 | 10 de 10 | no perd | ✓ |
| llargs | 0.599 | 0.640 | +0.041 | +0.030 a +0.055 | 10 de 10 | no perd | ✓ |
| barreja | 0.605 | 0.648 | +0.043 | +0.034 a +0.053 | 10 de 10 | no perd | ✓ |
| aire | 0.554 | 0.597 | +0.042 | +0.035 a +0.050 | 10 de 10 | no perd | ✓ |
| soroll2 | 0.470 | 0.541 | +0.070 | +0.061 a +0.078 | 10 de 10 | no perd | ✓ |
| partit ×¼ | 0.746 | 0.758 | +0.013 | +0.005 a +0.020 | 8 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1, el soroll2 i «partit ×¼» | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## A mostres als canvis contra A equips sencers (spellF1)

| escenari | A equips sencers | A mostres als canvis | diferència | interval del 95 % | A mostres als canvis guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.799 | -0.001 | -0.004 a +0.003 | 4 de 10 |
| curts ×¼ | 0.699 | 0.698 | -0.001 | -0.006 a +0.006 | 3 de 10 |
| llargs ×¼ | 0.688 | 0.687 | -0.001 | -0.006 a +0.003 | 6 de 10 |
| barreja ×¼ | 0.696 | 0.696 | -0.000 | -0.006 a +0.005 | 4 de 10 |
| aire ×¼ | 0.629 | 0.628 | -0.001 | -0.006 a +0.004 | 5 de 10 |
| curts | 0.665 | 0.665 | +0.000 | -0.004 a +0.005 | 6 de 10 |
| llargs | 0.640 | 0.640 | +0.000 | -0.006 a +0.005 | 4 de 10 |
| barreja | 0.646 | 0.648 | +0.002 | -0.004 a +0.007 | 6 de 10 |
| aire | 0.600 | 0.597 | -0.003 | -0.008 a +0.003 | 3 de 10 |
| soroll2 | 0.534 | 0.541 | +0.006 | +0.001 a +0.013 | 5 de 10 |
| partit ×¼ | 0.761 | 0.758 | -0.003 | -0.005 a -0.000 | 4 de 10 |

## No passa: és el millor fins ara?

La regla de la D-50, escrita abans, contra A equips sencers:

| | És el millor fins ara si | |
|---|---|---|
| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | ✗ |
| «partit ×¼» | la diferència no és negativa | ✗ |
| El net, els ×1 i el soroll2 | no perd (diferència ≥ −0.04) | ✓ |

**A mostres als canvis no és el millor fins ara:** el pas següent es fa a sobre d'A equips sencers.

## A mostres als canvis contra A xarxes, decodificador de toc, només els partits de dfl

| escenari | A xarxes, decodificador de toc | A mostres als canvis | diferència | interval del 95 % | A mostres als canvis guanya |
|---|---|---|---|---|---|
| net | 0.766 | 0.765 | -0.001 | -0.008 a +0.007 | 2 de 7 |
| curts ×¼ | 0.642 | 0.665 | +0.023 | +0.014 a +0.032 | 7 de 7 |
| llargs ×¼ | 0.621 | 0.651 | +0.031 | +0.021 a +0.038 | 7 de 7 |
| barreja ×¼ | 0.630 | 0.664 | +0.034 | +0.023 a +0.045 | 7 de 7 |
| aire ×¼ | 0.544 | 0.569 | +0.024 | +0.016 a +0.032 | 7 de 7 |
| curts | 0.607 | 0.636 | +0.029 | +0.023 a +0.035 | 7 de 7 |
| llargs | 0.564 | 0.606 | +0.042 | +0.026 a +0.061 | 7 de 7 |
| barreja | 0.571 | 0.614 | +0.043 | +0.033 a +0.054 | 7 de 7 |
| aire | 0.501 | 0.542 | +0.041 | +0.033 a +0.050 | 7 de 7 |
| soroll2 | 0.433 | 0.490 | +0.056 | +0.048 a +0.065 | 7 de 7 |
| partit ×¼ | 0.717 | 0.725 | +0.008 | -0.002 a +0.019 | 5 de 7 |

## A mostres als canvis contra A equips sencers, només els partits de dfl

| escenari | A equips sencers | A mostres als canvis | diferència | interval del 95 % | A mostres als canvis guanya |
|---|---|---|---|---|---|
| net | 0.768 | 0.765 | -0.004 | -0.007 a +0.000 | 1 de 7 |
| curts ×¼ | 0.669 | 0.665 | -0.004 | -0.010 a +0.004 | 1 de 7 |
| llargs ×¼ | 0.656 | 0.651 | -0.005 | -0.010 a +0.001 | 3 de 7 |
| barreja ×¼ | 0.664 | 0.664 | +0.000 | -0.008 a +0.009 | 3 de 7 |
| aire ×¼ | 0.571 | 0.569 | -0.002 | -0.009 a +0.005 | 3 de 7 |
| curts | 0.637 | 0.636 | -0.001 | -0.008 a +0.005 | 3 de 7 |
| llargs | 0.602 | 0.606 | +0.004 | -0.005 a +0.012 | 4 de 7 |
| barreja | 0.608 | 0.614 | +0.006 | -0.000 a +0.011 | 5 de 7 |
| aire | 0.546 | 0.542 | -0.004 | -0.010 a +0.004 | 2 de 7 |
| soroll2 | 0.491 | 0.490 | -0.002 | -0.007 a +0.005 | 2 de 7 |
| partit ×¼ | 0.729 | 0.725 | -0.004 | -0.007 a -0.001 | 2 de 7 |

## A mostres als canvis contra A xarxes, decodificador de toc, només els partits de metrica

| escenari | A xarxes, decodificador de toc | A mostres als canvis | diferència | interval del 95 % | A mostres als canvis guanya |
|---|---|---|---|---|---|
| net | 0.874 | 0.879 | +0.005 | -0.003 a +0.012 | 2 de 3 |
| curts ×¼ | 0.747 | 0.777 | +0.031 | +0.022 a +0.041 | 3 de 3 |
| llargs ×¼ | 0.723 | 0.769 | +0.046 | +0.028 a +0.060 | 3 de 3 |
| barreja ×¼ | 0.730 | 0.770 | +0.040 | +0.032 a +0.053 | 3 de 3 |
| aire ×¼ | 0.731 | 0.766 | +0.035 | +0.014 a +0.054 | 3 de 3 |
| curts | 0.702 | 0.733 | +0.030 | +0.017 a +0.042 | 3 de 3 |
| llargs | 0.682 | 0.721 | +0.038 | +0.034 a +0.046 | 3 de 3 |
| barreja | 0.684 | 0.728 | +0.044 | +0.023 a +0.065 | 3 de 3 |
| aire | 0.679 | 0.724 | +0.045 | +0.028 a +0.054 | 3 de 3 |
| soroll2 | 0.557 | 0.659 | +0.102 | +0.078 a +0.115 | 3 de 3 |
| partit ×¼ | 0.813 | 0.836 | +0.023 | +0.016 a +0.031 | 3 de 3 |

## A mostres als canvis contra A equips sencers, només els partits de metrica

| escenari | A equips sencers | A mostres als canvis | diferència | interval del 95 % | A mostres als canvis guanya |
|---|---|---|---|---|---|
| net | 0.873 | 0.879 | +0.006 | +0.000 a +0.017 | 3 de 3 |
| curts ×¼ | 0.769 | 0.777 | +0.008 | -0.001 a +0.015 | 2 de 3 |
| llargs ×¼ | 0.763 | 0.769 | +0.006 | +0.001 a +0.017 | 3 de 3 |
| barreja ×¼ | 0.773 | 0.770 | -0.003 | -0.006 a +0.001 | 1 de 3 |
| aire ×¼ | 0.765 | 0.766 | +0.001 | -0.003 a +0.004 | 2 de 3 |
| curts | 0.729 | 0.733 | +0.004 | +0.001 a +0.006 | 3 de 3 |
| llargs | 0.730 | 0.721 | -0.009 | -0.014 a -0.007 | 0 de 3 |
| barreja | 0.736 | 0.728 | -0.008 | -0.020 a +0.007 | 1 de 3 |
| aire | 0.724 | 0.724 | -0.000 | -0.010 a +0.010 | 1 de 3 |
| soroll2 | 0.634 | 0.659 | +0.025 | +0.015 a +0.043 | 3 de 3 |
| partit ×¼ | 0.835 | 0.836 | +0.000 | -0.003 a +0.005 | 2 de 3 |

## Els errors d'equip a prop dels canvis

On la veritat de toc és d'un equip i la predicció no hi encerta l'equip: quants n'hi ha, i la part a
±0,5 s i a ±1 s d'un canvi d'equip de la veritat de toc.

| escenari | a | n errors, A equips sencers | n errors, A mostres als canvis | a prop, A equips sencers | a prop, A mostres als canvis |
|---|---|---|---|---|---|
| curts ×¼ | ±0,5 s | 69431 | 69601 | 0.397 | 0.392 |
| curts ×¼ | ±1 s | 69431 | 69601 | 0.608 | 0.601 |
| llargs ×¼ | ±0,5 s | 77390 | 77508 | 0.352 | 0.352 |
| llargs ×¼ | ±1 s | 77390 | 77508 | 0.556 | 0.553 |
| barreja ×¼ | ±0,5 s | 76226 | 75713 | 0.356 | 0.357 |
| barreja ×¼ | ±1 s | 76226 | 75713 | 0.557 | 0.557 |
| aire ×¼ | ±0,5 s | 101883 | 101454 | 0.325 | 0.325 |
| aire ×¼ | ±1 s | 101883 | 101454 | 0.530 | 0.528 |
| partit ×¼ | ±0,5 s | 54387 | 55237 | 0.378 | 0.368 |
| partit ×¼ | ±1 s | 54387 | 55237 | 0.580 | 0.569 |

## On encerten l'equip les xarxes i el segon

On la veritat de toc és d'un equip, la part de les imatges on l'equip més probable és el bo (les
xarxes, amb les seves probabilitats; el segon, amb la relativa).

| escenari | on | n imatges | les xarxes d'A equips sencers | les xarxes noves | el segon d'A equips sencers | el segon nou |
|---|---|---|---|---|---|---|
| curts ×¼ | a ±0,5 s d'un canvi, amb pilota | 42290 | 0.680 | 0.702 | 0.747 | 0.755 |
| curts ×¼ | a ±0,5 s d'un canvi, sense pilota | 44103 | 0.619 | 0.625 | 0.638 | 0.640 |
| curts ×¼ | a la resta, amb pilota | 440269 | 0.949 | 0.949 | 0.959 | 0.959 |
| curts ×¼ | a la resta, sense pilota | 291234 | 0.920 | 0.919 | 0.929 | 0.930 |
| llargs ×¼ | a ±0,5 s d'un canvi, amb pilota | 46711 | 0.684 | 0.712 | 0.772 | 0.780 |
| llargs ×¼ | a ±0,5 s d'un canvi, sense pilota | 39682 | 0.607 | 0.608 | 0.622 | 0.613 |
| llargs ×¼ | a la resta, amb pilota | 435848 | 0.949 | 0.948 | 0.963 | 0.962 |
| llargs ×¼ | a la resta, sense pilota | 295655 | 0.896 | 0.895 | 0.915 | 0.914 |
| barreja ×¼ | a ±0,5 s d'un canvi, amb pilota | 45110 | 0.677 | 0.700 | 0.766 | 0.769 |
| barreja ×¼ | a ±0,5 s d'un canvi, sense pilota | 41283 | 0.612 | 0.617 | 0.629 | 0.630 |
| barreja ×¼ | a la resta, amb pilota | 437449 | 0.948 | 0.948 | 0.962 | 0.962 |
| barreja ×¼ | a la resta, sense pilota | 294054 | 0.902 | 0.903 | 0.916 | 0.916 |
| aire ×¼ | a ±0,5 s d'un canvi, amb pilota | 46423 | 0.652 | 0.668 | 0.720 | 0.721 |
| aire ×¼ | a ±0,5 s d'un canvi, sense pilota | 39970 | 0.584 | 0.589 | 0.605 | 0.606 |
| aire ×¼ | a la resta, amb pilota | 436136 | 0.934 | 0.931 | 0.949 | 0.948 |
| aire ×¼ | a la resta, sense pilota | 295367 | 0.885 | 0.885 | 0.907 | 0.909 |
| partit ×¼ | a ±0,5 s d'un canvi, amb pilota | 78041 | 0.687 | 0.712 | 0.775 | 0.782 |
| partit ×¼ | a ±0,5 s d'un canvi, sense pilota | 8352 | 0.573 | 0.573 | 0.581 | 0.587 |
| partit ×¼ | a la resta, amb pilota | 658065 | 0.945 | 0.942 | 0.959 | 0.958 |
| partit ×¼ | a la resta, sense pilota | 73438 | 0.912 | 0.910 | 0.932 | 0.930 |

## Els canvis d'equip de la predicció, i quants són falsos

Un canvi és fals si no n'hi ha cap de real a 25 imatges o menys.

| escenari | n canvis · A equips sencers | n canvis · A mostres als canvis | falsos · A equips sencers | falsos · A mostres als canvis | dels falsos, als forats · A equips sencers | dels falsos, als forats · A mostres als canvis |
|---|---|---|---|---|---|---|
| net | 3468 | 3497 | 0.165 | 0.169 | 0.039 | 0.029 |
| curts ×¼ | 3222 | 3243 | 0.256 | 0.257 | 0.662 | 0.669 |
| llargs ×¼ | 3143 | 3159 | 0.271 | 0.273 | 0.573 | 0.587 |
| barreja ×¼ | 3152 | 3177 | 0.262 | 0.260 | 0.617 | 0.621 |
| aire ×¼ | 3016 | 3024 | 0.318 | 0.317 | 0.549 | 0.535 |
| partit ×¼ | 3440 | 3452 | 0.208 | 0.209 | 0.280 | 0.260 |
| curts | 3131 | 3166 | 0.293 | 0.291 | 0.645 | 0.657 |
| llargs | 2999 | 3025 | 0.325 | 0.324 | 0.524 | 0.518 |
| barreja | 3067 | 3118 | 0.312 | 0.318 | 0.575 | 0.568 |
| aire | 2919 | 2889 | 0.350 | 0.345 | 0.523 | 0.518 |
| soroll2 | 3523 | 3583 | 0.463 | 0.456 | 0.437 | 0.446 |

## L'spellF1 de cada mètode (mitjana dels deu partits)

**spellF1 a la veritat de toc**

| escenari | A xarxes, decodificador de toc | A equips sencers | A mostres als canvis |
|---|---|---|---|
| net | 0.798 | 0.799 | 0.799 |
| curts ×¼ | 0.673 | 0.699 | 0.698 |
| llargs ×¼ | 0.651 | 0.688 | 0.687 |
| barreja ×¼ | 0.660 | 0.696 | 0.696 |
| aire ×¼ | 0.600 | 0.629 | 0.628 |
| curts | 0.636 | 0.665 | 0.665 |
| llargs | 0.599 | 0.640 | 0.640 |
| barreja | 0.605 | 0.646 | 0.648 |
| aire | 0.554 | 0.600 | 0.597 |
| soroll2 | 0.470 | 0.534 | 0.541 |
| partit ×¼ | 0.746 | 0.761 | 0.758 |

**spellF1 a la veritat de sempre**

| escenari | A xarxes, decodificador de toc | A equips sencers | A mostres als canvis |
|---|---|---|---|
| net | 0.808 | 0.810 | 0.810 |
| curts ×¼ | 0.684 | 0.708 | 0.708 |
| llargs ×¼ | 0.662 | 0.700 | 0.697 |
| barreja ×¼ | 0.671 | 0.708 | 0.705 |
| aire ×¼ | 0.612 | 0.643 | 0.642 |
| curts | 0.644 | 0.674 | 0.673 |
| llargs | 0.607 | 0.648 | 0.650 |
| barreja | 0.616 | 0.656 | 0.658 |
| aire | 0.564 | 0.613 | 0.606 |
| soroll2 | 0.478 | 0.543 | 0.547 |
| partit ×¼ | 0.757 | 0.772 | 0.770 |

## Els decodificadors triats

- **A xarxes, decodificador de toc:** w = 4, λ = 64, durada mínima 1 (1 partits); w = 4, λ = 32, durada mínima 12 (6 partits); w = 4, λ = 32, durada mínima 1 (3 partits)
- **A equips sencers:** w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 16, durada mínima 12 (2 partits)
- **A mostres als canvis:** w = 4, λ = 32, durada mínima 12 (2 partits); w = 4, λ = 16, durada mínima 12 (8 partits)
