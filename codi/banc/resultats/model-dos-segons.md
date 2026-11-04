# Banc obert · La mitjana dels dos segons (T3aa)

Generat amb `uv run python -I -m banc.model_dos_segons`. Dades obertes: 7 partits de DFL (IDSSE, CC BY
4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el criteri:
`docs/pla-tocs.md`, «T3aa», i la capçalera de `banc/model_dos_segons.py`. Es puntua a la veritat de toc.

**A xarxes, decodificador de toc** i **A equips sencers** són els de la T3v, i **A mostres als canvis**, el de la T3z, amb les peces de
la memòria cau (✓ comprovat: a cada punt de la graella donen l'spellF1 d'aquells bancs, i els
decodificadors triats són els seus). **A dos segons** és, a cada imatge, la mitjana de les probabilitats dels
segons d'A equips sencers i d'A mostres als canvis, amb el prior i la q que tenen tots dos. No s'entrena res.

## A dos segons contra A xarxes, decodificador de toc (spellF1): el criteri

| escenari | A xarxes, decodificador de toc | A dos segons | diferència | interval del 95 % | A dos segons guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.798 | 0.799 | +0.001 | -0.003 a +0.005 | 5 de 10 | no perd | ✓ |
| curts ×¼ | 0.673 | 0.702 | +0.028 | +0.022 a +0.035 | 10 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.651 | 0.691 | +0.040 | +0.032 a +0.047 | 10 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.660 | 0.698 | +0.038 | +0.029 a +0.046 | 10 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.600 | 0.629 | +0.029 | +0.021 a +0.038 | 10 de 10 | guanya clarament | ✗ |
| curts | 0.636 | 0.667 | +0.032 | +0.027 a +0.036 | 10 de 10 | no perd | ✓ |
| llargs | 0.599 | 0.641 | +0.042 | +0.029 a +0.055 | 10 de 10 | no perd | ✓ |
| barreja | 0.605 | 0.648 | +0.043 | +0.034 a +0.053 | 10 de 10 | no perd | ✓ |
| aire | 0.554 | 0.602 | +0.048 | +0.041 a +0.054 | 10 de 10 | no perd | ✓ |
| soroll2 | 0.470 | 0.540 | +0.070 | +0.062 a +0.077 | 10 de 10 | no perd | ✓ |
| partit ×¼ | 0.746 | 0.763 | +0.018 | +0.010 a +0.026 | 8 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1, el soroll2 i «partit ×¼» | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## A dos segons contra A equips sencers (spellF1)

| escenari | A equips sencers | A dos segons | diferència | interval del 95 % | A dos segons guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.799 | -0.001 | -0.004 a +0.003 | 3 de 10 |
| curts ×¼ | 0.699 | 0.702 | +0.003 | -0.001 a +0.006 | 6 de 10 |
| llargs ×¼ | 0.688 | 0.691 | +0.003 | +0.000 a +0.006 | 7 de 10 |
| barreja ×¼ | 0.696 | 0.698 | +0.001 | -0.003 a +0.005 | 4 de 10 |
| aire ×¼ | 0.629 | 0.629 | -0.000 | -0.004 a +0.005 | 2 de 10 |
| curts | 0.665 | 0.667 | +0.003 | -0.001 a +0.007 | 6 de 10 |
| llargs | 0.640 | 0.641 | +0.001 | -0.003 a +0.004 | 6 de 10 |
| barreja | 0.646 | 0.648 | +0.002 | -0.002 a +0.005 | 7 de 10 |
| aire | 0.600 | 0.602 | +0.003 | -0.001 a +0.006 | 7 de 10 |
| soroll2 | 0.534 | 0.540 | +0.006 | +0.002 a +0.009 | 7 de 10 |
| partit ×¼ | 0.761 | 0.763 | +0.002 | -0.000 a +0.004 | 7 de 10 |

## No passa: és el millor fins ara?

La regla de la D-50, escrita abans, contra A equips sencers:

| | És el millor fins ara si | |
|---|---|---|
| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | ✗ |
| «partit ×¼» | la diferència no és negativa | ✓ |
| El net, els ×1 i el soroll2 | no perd (diferència ≥ −0.04) | ✓ |

**A dos segons no és el millor fins ara:** el pas següent es fa a sobre d'A equips sencers.

## A dos segons contra A xarxes, decodificador de toc, només els partits de dfl

| escenari | A xarxes, decodificador de toc | A dos segons | diferència | interval del 95 % | A dos segons guanya |
|---|---|---|---|---|---|
| net | 0.766 | 0.767 | +0.001 | -0.003 a +0.007 | 4 de 7 |
| curts ×¼ | 0.642 | 0.670 | +0.028 | +0.021 a +0.037 | 7 de 7 |
| llargs ×¼ | 0.621 | 0.658 | +0.038 | +0.030 a +0.046 | 7 de 7 |
| barreja ×¼ | 0.630 | 0.665 | +0.036 | +0.025 a +0.045 | 7 de 7 |
| aire ×¼ | 0.544 | 0.571 | +0.027 | +0.019 a +0.034 | 7 de 7 |
| curts | 0.607 | 0.638 | +0.031 | +0.025 a +0.037 | 7 de 7 |
| llargs | 0.564 | 0.604 | +0.040 | +0.023 a +0.058 | 7 de 7 |
| barreja | 0.571 | 0.612 | +0.041 | +0.033 a +0.051 | 7 de 7 |
| aire | 0.501 | 0.548 | +0.047 | +0.039 a +0.054 | 7 de 7 |
| soroll2 | 0.433 | 0.495 | +0.061 | +0.053 a +0.069 | 7 de 7 |
| partit ×¼ | 0.717 | 0.730 | +0.013 | +0.002 a +0.024 | 5 de 7 |

## A dos segons contra A equips sencers, només els partits de dfl

| escenari | A equips sencers | A dos segons | diferència | interval del 95 % | A dos segons guanya |
|---|---|---|---|---|---|
| net | 0.768 | 0.767 | -0.001 | -0.005 a +0.004 | 2 de 7 |
| curts ×¼ | 0.669 | 0.670 | +0.001 | -0.002 a +0.004 | 4 de 7 |
| llargs ×¼ | 0.656 | 0.658 | +0.002 | -0.002 a +0.006 | 4 de 7 |
| barreja ×¼ | 0.664 | 0.665 | +0.002 | -0.004 a +0.008 | 3 de 7 |
| aire ×¼ | 0.571 | 0.571 | -0.000 | -0.005 a +0.006 | 1 de 7 |
| curts | 0.637 | 0.638 | +0.001 | -0.003 a +0.006 | 3 de 7 |
| llargs | 0.602 | 0.604 | +0.002 | -0.004 a +0.007 | 5 de 7 |
| barreja | 0.608 | 0.612 | +0.004 | +0.001 a +0.007 | 6 de 7 |
| aire | 0.546 | 0.548 | +0.002 | -0.003 a +0.006 | 4 de 7 |
| soroll2 | 0.491 | 0.495 | +0.003 | -0.002 a +0.008 | 4 de 7 |
| partit ×¼ | 0.729 | 0.730 | +0.001 | -0.002 a +0.004 | 4 de 7 |

## A dos segons contra A xarxes, decodificador de toc, només els partits de metrica

| escenari | A xarxes, decodificador de toc | A dos segons | diferència | interval del 95 % | A dos segons guanya |
|---|---|---|---|---|---|
| net | 0.874 | 0.873 | -0.001 | -0.008 a +0.009 | 1 de 3 |
| curts ×¼ | 0.747 | 0.776 | +0.029 | +0.020 a +0.040 | 3 de 3 |
| llargs ×¼ | 0.723 | 0.768 | +0.045 | +0.030 a +0.065 | 3 de 3 |
| barreja ×¼ | 0.730 | 0.773 | +0.042 | +0.029 a +0.062 | 3 de 3 |
| aire ×¼ | 0.731 | 0.766 | +0.035 | +0.015 a +0.061 | 3 de 3 |
| curts | 0.702 | 0.735 | +0.033 | +0.022 a +0.041 | 3 de 3 |
| llargs | 0.682 | 0.728 | +0.046 | +0.037 a +0.053 | 3 de 3 |
| barreja | 0.684 | 0.733 | +0.049 | +0.024 a +0.074 | 3 de 3 |
| aire | 0.679 | 0.728 | +0.049 | +0.039 a +0.062 | 3 de 3 |
| soroll2 | 0.557 | 0.646 | +0.089 | +0.074 a +0.109 | 3 de 3 |
| partit ×¼ | 0.813 | 0.840 | +0.028 | +0.023 a +0.036 | 3 de 3 |

## A dos segons contra A equips sencers, només els partits de metrica

| escenari | A equips sencers | A dos segons | diferència | interval del 95 % | A dos segons guanya |
|---|---|---|---|---|---|
| net | 0.873 | 0.873 | +0.000 | -0.003 a +0.006 | 1 de 3 |
| curts ×¼ | 0.769 | 0.776 | +0.006 | -0.003 a +0.013 | 2 de 3 |
| llargs ×¼ | 0.763 | 0.768 | +0.005 | +0.003 a +0.007 | 3 de 3 |
| barreja ×¼ | 0.773 | 0.773 | -0.000 | -0.003 a +0.003 | 1 de 3 |
| aire ×¼ | 0.765 | 0.766 | +0.000 | -0.008 a +0.011 | 1 de 3 |
| curts | 0.729 | 0.735 | +0.007 | +0.000 a +0.010 | 3 de 3 |
| llargs | 0.730 | 0.728 | -0.002 | -0.004 a +0.001 | 1 de 3 |
| barreja | 0.736 | 0.733 | -0.002 | -0.014 a +0.007 | 1 de 3 |
| aire | 0.724 | 0.728 | +0.004 | +0.001 a +0.008 | 3 de 3 |
| soroll2 | 0.634 | 0.646 | +0.012 | +0.009 a +0.013 | 3 de 3 |
| partit ×¼ | 0.835 | 0.840 | +0.005 | +0.001 a +0.009 | 3 de 3 |

## On encerten l'equip els tres segons

On la veritat de toc és d'un equip, la part de les imatges on l'equip més probable és el bo (amb la
relativa), a ±0,5 s d'un canvi d'equip de la veritat de toc i a la resta.

| escenari | on | n imatges | el segon d'A equips sencers | el segon d'A mostres als canvis | la mitjana |
|---|---|---|---|---|---|
| curts ×¼ | a ±0,5 s d'un canvi, amb pilota | 42290 | 0.747 | 0.755 | 0.752 |
| curts ×¼ | a ±0,5 s d'un canvi, sense pilota | 44103 | 0.638 | 0.640 | 0.641 |
| curts ×¼ | a la resta, amb pilota | 440269 | 0.959 | 0.959 | 0.960 |
| curts ×¼ | a la resta, sense pilota | 291234 | 0.929 | 0.930 | 0.931 |
| llargs ×¼ | a ±0,5 s d'un canvi, amb pilota | 46711 | 0.772 | 0.780 | 0.776 |
| llargs ×¼ | a ±0,5 s d'un canvi, sense pilota | 39682 | 0.622 | 0.613 | 0.618 |
| llargs ×¼ | a la resta, amb pilota | 435848 | 0.963 | 0.962 | 0.963 |
| llargs ×¼ | a la resta, sense pilota | 295655 | 0.915 | 0.914 | 0.916 |
| barreja ×¼ | a ±0,5 s d'un canvi, amb pilota | 45110 | 0.766 | 0.769 | 0.768 |
| barreja ×¼ | a ±0,5 s d'un canvi, sense pilota | 41283 | 0.629 | 0.630 | 0.631 |
| barreja ×¼ | a la resta, amb pilota | 437449 | 0.962 | 0.962 | 0.962 |
| barreja ×¼ | a la resta, sense pilota | 294054 | 0.916 | 0.916 | 0.918 |
| aire ×¼ | a ±0,5 s d'un canvi, amb pilota | 46423 | 0.720 | 0.721 | 0.721 |
| aire ×¼ | a ±0,5 s d'un canvi, sense pilota | 39970 | 0.605 | 0.606 | 0.606 |
| aire ×¼ | a la resta, amb pilota | 436136 | 0.949 | 0.948 | 0.949 |
| aire ×¼ | a la resta, sense pilota | 295367 | 0.907 | 0.909 | 0.910 |
| partit ×¼ | a ±0,5 s d'un canvi, amb pilota | 78041 | 0.775 | 0.782 | 0.780 |
| partit ×¼ | a ±0,5 s d'un canvi, sense pilota | 8352 | 0.581 | 0.587 | 0.582 |
| partit ×¼ | a la resta, amb pilota | 658065 | 0.959 | 0.958 | 0.959 |
| partit ×¼ | a la resta, sense pilota | 73438 | 0.932 | 0.930 | 0.933 |

## On els dos segons no donen el mateix equip

On la veritat de toc és d'un equip: la part de les imatges on l'equip més probable dels dos segons no és
el mateix, i d'aquestes, la part on cadascú encerta l'equip.

| escenari | on | n imatges | part on no diuen el mateix | hi encerta el segon d'A equips sencers | hi encerta el segon d'A mostres als canvis | hi encerta la mitjana |
|---|---|---|---|---|---|---|
| curts ×¼ | a ±0,5 s d'un canvi, amb pilota | 42290 | 0.049 | 0.415 | 0.585 | 0.530 |
| curts ×¼ | a ±0,5 s d'un canvi, sense pilota | 44103 | 0.079 | 0.486 | 0.514 | 0.519 |
| curts ×¼ | a la resta, amb pilota | 440269 | 0.011 | 0.513 | 0.487 | 0.548 |
| curts ×¼ | a la resta, sense pilota | 291234 | 0.022 | 0.496 | 0.504 | 0.563 |
| llargs ×¼ | a ±0,5 s d'un canvi, amb pilota | 46711 | 0.045 | 0.408 | 0.592 | 0.511 |
| llargs ×¼ | a ±0,5 s d'un canvi, sense pilota | 39682 | 0.089 | 0.547 | 0.453 | 0.508 |
| llargs ×¼ | a la resta, amb pilota | 435848 | 0.010 | 0.540 | 0.460 | 0.574 |
| llargs ×¼ | a la resta, sense pilota | 295655 | 0.032 | 0.512 | 0.488 | 0.564 |
| barreja ×¼ | a ±0,5 s d'un canvi, amb pilota | 45110 | 0.046 | 0.467 | 0.533 | 0.526 |
| barreja ×¼ | a ±0,5 s d'un canvi, sense pilota | 41283 | 0.084 | 0.492 | 0.508 | 0.515 |
| barreja ×¼ | a la resta, amb pilota | 437449 | 0.010 | 0.529 | 0.471 | 0.535 |
| barreja ×¼ | a la resta, sense pilota | 294054 | 0.029 | 0.502 | 0.498 | 0.555 |
| aire ×¼ | a ±0,5 s d'un canvi, amb pilota | 46423 | 0.064 | 0.496 | 0.504 | 0.516 |
| aire ×¼ | a ±0,5 s d'un canvi, sense pilota | 39970 | 0.095 | 0.494 | 0.506 | 0.507 |
| aire ×¼ | a la resta, amb pilota | 436136 | 0.017 | 0.528 | 0.472 | 0.559 |
| aire ×¼ | a la resta, sense pilota | 295367 | 0.037 | 0.484 | 0.516 | 0.542 |
| partit ×¼ | a ±0,5 s d'un canvi, amb pilota | 78041 | 0.046 | 0.414 | 0.586 | 0.527 |
| partit ×¼ | a ±0,5 s d'un canvi, sense pilota | 8352 | 0.099 | 0.470 | 0.530 | 0.477 |
| partit ×¼ | a la resta, amb pilota | 658065 | 0.011 | 0.531 | 0.469 | 0.551 |
| partit ×¼ | a la resta, sense pilota | 73438 | 0.024 | 0.538 | 0.462 | 0.551 |

## Els canvis d'equip de la predicció, i quants són falsos

Un canvi és fals si no n'hi ha cap de real a 25 imatges o menys.

| escenari | n canvis · A equips sencers | n canvis · A mostres als canvis | n canvis · A dos segons | falsos · A equips sencers | falsos · A mostres als canvis | falsos · A dos segons | dels falsos, als forats · A equips sencers | dels falsos, als forats · A mostres als canvis | dels falsos, als forats · A dos segons |
|---|---|---|---|---|---|---|---|---|---|
| net | 3468 | 3497 | 3471 | 0.165 | 0.169 | 0.167 | 0.039 | 0.029 | 0.031 |
| curts ×¼ | 3222 | 3243 | 3210 | 0.256 | 0.257 | 0.250 | 0.662 | 0.669 | 0.662 |
| llargs ×¼ | 3143 | 3159 | 3141 | 0.271 | 0.273 | 0.267 | 0.573 | 0.587 | 0.576 |
| barreja ×¼ | 3152 | 3177 | 3154 | 0.262 | 0.260 | 0.258 | 0.617 | 0.621 | 0.627 |
| aire ×¼ | 3016 | 3024 | 2993 | 0.318 | 0.317 | 0.309 | 0.549 | 0.535 | 0.542 |
| partit ×¼ | 3440 | 3452 | 3446 | 0.208 | 0.209 | 0.206 | 0.280 | 0.260 | 0.274 |
| curts | 3131 | 3166 | 3132 | 0.293 | 0.291 | 0.285 | 0.645 | 0.657 | 0.646 |
| llargs | 2999 | 3025 | 2987 | 0.325 | 0.324 | 0.319 | 0.524 | 0.518 | 0.516 |
| barreja | 3067 | 3118 | 3056 | 0.312 | 0.318 | 0.308 | 0.575 | 0.568 | 0.575 |
| aire | 2919 | 2889 | 2884 | 0.350 | 0.345 | 0.342 | 0.523 | 0.518 | 0.523 |
| soroll2 | 3523 | 3583 | 3526 | 0.463 | 0.456 | 0.458 | 0.437 | 0.446 | 0.430 |

## L'spellF1 de cada mètode (mitjana dels deu partits)

**spellF1 a la veritat de toc**

| escenari | A xarxes, decodificador de toc | A equips sencers | A mostres als canvis | A dos segons |
|---|---|---|---|---|
| net | 0.798 | 0.799 | 0.799 | 0.799 |
| curts ×¼ | 0.673 | 0.699 | 0.698 | 0.702 |
| llargs ×¼ | 0.651 | 0.688 | 0.687 | 0.691 |
| barreja ×¼ | 0.660 | 0.696 | 0.696 | 0.698 |
| aire ×¼ | 0.600 | 0.629 | 0.628 | 0.629 |
| curts | 0.636 | 0.665 | 0.665 | 0.667 |
| llargs | 0.599 | 0.640 | 0.640 | 0.641 |
| barreja | 0.605 | 0.646 | 0.648 | 0.648 |
| aire | 0.554 | 0.600 | 0.597 | 0.602 |
| soroll2 | 0.470 | 0.534 | 0.541 | 0.540 |
| partit ×¼ | 0.746 | 0.761 | 0.758 | 0.763 |

**spellF1 a la veritat de sempre**

| escenari | A xarxes, decodificador de toc | A equips sencers | A mostres als canvis | A dos segons |
|---|---|---|---|---|
| net | 0.808 | 0.810 | 0.810 | 0.810 |
| curts ×¼ | 0.684 | 0.708 | 0.708 | 0.711 |
| llargs ×¼ | 0.662 | 0.700 | 0.697 | 0.701 |
| barreja ×¼ | 0.671 | 0.708 | 0.705 | 0.707 |
| aire ×¼ | 0.612 | 0.643 | 0.642 | 0.642 |
| curts | 0.644 | 0.674 | 0.673 | 0.677 |
| llargs | 0.607 | 0.648 | 0.650 | 0.650 |
| barreja | 0.616 | 0.656 | 0.658 | 0.659 |
| aire | 0.564 | 0.613 | 0.606 | 0.613 |
| soroll2 | 0.478 | 0.543 | 0.547 | 0.548 |
| partit ×¼ | 0.757 | 0.772 | 0.770 | 0.775 |

## Els decodificadors triats

- **A xarxes, decodificador de toc:** w = 4, λ = 64, durada mínima 1 (1 partits); w = 4, λ = 32, durada mínima 12 (6 partits); w = 4, λ = 32, durada mínima 1 (3 partits)
- **A equips sencers:** w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 16, durada mínima 12 (2 partits)
- **A mostres als canvis:** w = 4, λ = 32, durada mínima 12 (2 partits); w = 4, λ = 16, durada mínima 12 (8 partits)
- **A dos segons:** w = 4, λ = 32, durada mínima 12 (6 partits); w = 4, λ = 16, durada mínima 12 (4 partits)
