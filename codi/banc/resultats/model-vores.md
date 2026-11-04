# Banc obert · Les vores dels canvis, afinades (T3ae)

Generat amb `uv run python -I -m banc.model_vores`. Dades obertes: 7 partits de DFL (IDSSE, CC BY 4.0) i
els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el criteri:
`docs/pla-tocs.md`, «T3ae», i la capçalera de `banc/model_vores.py`. Es puntua a la veritat de toc.

**A xarxes, decodificador de toc** i **A equips sencers** són els de la T3v, **A pilota creïble**, el de la T3w, i **A neteja d'aire**,
el de la T3ac, amb les peces de la memòria cau (✓ comprovat: donen l'spellF1 d'aquells bancs, i els
decodificadors triats són els seus). **A vores** és A neteja d'aire, amb el mateix decodificador, i després
un LightGBM que mou cada canvi fins a 0,5 s. Aprèn amb les prediccions dels altres nou partits fetes
sense el partit que es prova (un segon i una q nous per a cada grup). ✓ Comprovat a cada partit i
escenari: no dona mai la D a una imatge netejada.

## A vores contra A xarxes, decodificador de toc (spellF1): el criteri

| escenari | A xarxes, decodificador de toc | A vores | diferència | interval del 95 % | A vores guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.798 | 0.805 | +0.007 | +0.002 a +0.012 | 7 de 10 | no perd | ✓ |
| curts ×¼ | 0.673 | 0.699 | +0.025 | +0.021 a +0.030 | 10 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.651 | 0.688 | +0.036 | +0.028 a +0.044 | 10 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.660 | 0.696 | +0.036 | +0.030 a +0.042 | 10 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.600 | 0.644 | +0.044 | +0.038 a +0.051 | 10 de 10 | guanya clarament | ✓ |
| curts | 0.636 | 0.661 | +0.026 | +0.020 a +0.032 | 10 de 10 | no perd | ✓ |
| llargs | 0.599 | 0.640 | +0.041 | +0.028 a +0.053 | 10 de 10 | no perd | ✓ |
| barreja | 0.605 | 0.645 | +0.040 | +0.027 a +0.050 | 10 de 10 | no perd | ✓ |
| aire | 0.554 | 0.614 | +0.060 | +0.053 a +0.067 | 10 de 10 | no perd | ✓ |
| soroll2 | 0.470 | 0.529 | +0.058 | +0.051 a +0.066 | 10 de 10 | no perd | ✓ |
| partit ×¼ | 0.746 | 0.764 | +0.018 | +0.012 a +0.025 | 9 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1, el soroll2 i «partit ×¼» | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## A vores contra A neteja d'aire (spellF1)

| escenari | A neteja d'aire | A vores | diferència | interval del 95 % | A vores guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.805 | +0.005 | +0.004 a +0.007 | 10 de 10 |
| curts ×¼ | 0.699 | 0.699 | -0.000 | -0.003 a +0.002 | 4 de 10 |
| llargs ×¼ | 0.688 | 0.688 | -0.000 | -0.003 a +0.002 | 4 de 10 |
| barreja ×¼ | 0.696 | 0.696 | -0.001 | -0.002 a +0.001 | 4 de 10 |
| aire ×¼ | 0.644 | 0.644 | +0.000 | -0.002 a +0.002 | 6 de 10 |
| curts | 0.665 | 0.661 | -0.003 | -0.007 a +0.000 | 3 de 10 |
| llargs | 0.640 | 0.640 | -0.000 | -0.003 a +0.002 | 7 de 10 |
| barreja | 0.646 | 0.645 | -0.002 | -0.003 a -0.001 | 1 de 10 |
| aire | 0.618 | 0.614 | -0.003 | -0.006 a -0.001 | 2 de 10 |
| soroll2 | 0.534 | 0.529 | -0.006 | -0.008 a -0.003 | 1 de 10 |
| partit ×¼ | 0.761 | 0.764 | +0.003 | +0.001 a +0.004 | 8 de 10 |

## No passa: és el millor fins ara?

La regla de la D-50, escrita abans, contra A neteja d'aire:

| | És el millor fins ara si | |
|---|---|---|
| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | ✗ |
| «partit ×¼» | la diferència no és negativa | ✓ |
| El net, els ×1 i el soroll2 | no perd (diferència ≥ −0.04) | ✓ |

**A vores no és el millor fins ara:** el pas següent es fa a sobre d'A neteja d'aire.

## A vores contra A xarxes, decodificador de toc, només els partits de dfl

| escenari | A xarxes, decodificador de toc | A vores | diferència | interval del 95 % | A vores guanya |
|---|---|---|---|---|---|
| net | 0.766 | 0.774 | +0.008 | +0.003 a +0.014 | 6 de 7 |
| curts ×¼ | 0.642 | 0.667 | +0.025 | +0.020 a +0.032 | 7 de 7 |
| llargs ×¼ | 0.621 | 0.655 | +0.034 | +0.025 a +0.044 | 7 de 7 |
| barreja ×¼ | 0.630 | 0.662 | +0.032 | +0.026 a +0.038 | 7 de 7 |
| aire ×¼ | 0.544 | 0.592 | +0.048 | +0.042 a +0.055 | 7 de 7 |
| curts | 0.607 | 0.632 | +0.025 | +0.016 a +0.033 | 7 de 7 |
| llargs | 0.564 | 0.600 | +0.036 | +0.019 a +0.054 | 7 de 7 |
| barreja | 0.571 | 0.606 | +0.035 | +0.025 a +0.045 | 7 de 7 |
| aire | 0.501 | 0.568 | +0.067 | +0.058 a +0.077 | 7 de 7 |
| soroll2 | 0.433 | 0.484 | +0.050 | +0.042 a +0.059 | 7 de 7 |
| partit ×¼ | 0.717 | 0.733 | +0.016 | +0.007 a +0.025 | 6 de 7 |

## A vores contra A neteja d'aire, només els partits de dfl

| escenari | A neteja d'aire | A vores | diferència | interval del 95 % | A vores guanya |
|---|---|---|---|---|---|
| net | 0.768 | 0.774 | +0.006 | +0.004 a +0.008 | 7 de 7 |
| curts ×¼ | 0.669 | 0.667 | -0.002 | -0.004 a +0.000 | 3 de 7 |
| llargs ×¼ | 0.656 | 0.655 | -0.001 | -0.004 a +0.002 | 2 de 7 |
| barreja ×¼ | 0.664 | 0.662 | -0.002 | -0.004 a +0.000 | 2 de 7 |
| aire ×¼ | 0.592 | 0.592 | +0.000 | -0.002 a +0.002 | 4 de 7 |
| curts | 0.637 | 0.632 | -0.006 | -0.009 a -0.002 | 1 de 7 |
| llargs | 0.602 | 0.600 | -0.002 | -0.006 a +0.001 | 4 de 7 |
| barreja | 0.608 | 0.606 | -0.002 | -0.003 a -0.001 | 1 de 7 |
| aire | 0.572 | 0.568 | -0.004 | -0.007 a -0.001 | 1 de 7 |
| soroll2 | 0.491 | 0.484 | -0.008 | -0.010 a -0.004 | 0 de 7 |
| partit ×¼ | 0.729 | 0.733 | +0.003 | +0.002 a +0.005 | 6 de 7 |

## A vores contra A xarxes, decodificador de toc, només els partits de metrica

| escenari | A xarxes, decodificador de toc | A vores | diferència | interval del 95 % | A vores guanya |
|---|---|---|---|---|---|
| net | 0.874 | 0.876 | +0.002 | -0.006 a +0.018 | 1 de 3 |
| curts ×¼ | 0.747 | 0.772 | +0.026 | +0.014 a +0.034 | 3 de 3 |
| llargs ×¼ | 0.723 | 0.764 | +0.041 | +0.028 a +0.057 | 3 de 3 |
| barreja ×¼ | 0.730 | 0.775 | +0.045 | +0.031 a +0.063 | 3 de 3 |
| aire ×¼ | 0.731 | 0.765 | +0.034 | +0.018 a +0.054 | 3 de 3 |
| curts | 0.702 | 0.731 | +0.028 | +0.023 a +0.034 | 3 de 3 |
| llargs | 0.682 | 0.734 | +0.051 | +0.042 a +0.058 | 3 de 3 |
| barreja | 0.684 | 0.734 | +0.050 | +0.014 a +0.074 | 3 de 3 |
| aire | 0.679 | 0.723 | +0.043 | +0.037 a +0.051 | 3 de 3 |
| soroll2 | 0.557 | 0.633 | +0.076 | +0.064 a +0.096 | 3 de 3 |
| partit ×¼ | 0.813 | 0.836 | +0.024 | +0.018 a +0.034 | 3 de 3 |

## A vores contra A neteja d'aire, només els partits de metrica

| escenari | A neteja d'aire | A vores | diferència | interval del 95 % | A vores guanya |
|---|---|---|---|---|---|
| net | 0.873 | 0.876 | +0.004 | +0.001 a +0.006 | 3 de 3 |
| curts ×¼ | 0.769 | 0.772 | +0.003 | -0.002 a +0.010 | 1 de 3 |
| llargs ×¼ | 0.763 | 0.764 | +0.001 | -0.001 a +0.004 | 2 de 3 |
| barreja ×¼ | 0.773 | 0.775 | +0.002 | +0.000 a +0.004 | 2 de 3 |
| aire ×¼ | 0.765 | 0.765 | +0.000 | -0.005 a +0.004 | 2 de 3 |
| curts | 0.729 | 0.731 | +0.002 | -0.006 a +0.011 | 2 de 3 |
| llargs | 0.730 | 0.734 | +0.004 | +0.001 a +0.005 | 3 de 3 |
| barreja | 0.736 | 0.734 | -0.001 | -0.003 a +0.000 | 0 de 3 |
| aire | 0.724 | 0.723 | -0.001 | -0.005 a +0.004 | 1 de 3 |
| soroll2 | 0.634 | 0.633 | -0.001 | -0.004 a +0.003 | 1 de 3 |
| partit ×¼ | 0.835 | 0.836 | +0.001 | -0.001 a +0.003 | 2 de 3 |

## El sostre de les vores perfectes

A la veritat de toc, la mitjana dels deu partits: el sostre (cada canvi d'A neteja d'aire, al de la
veritat del mateix tipus més proper, a 12 imatges o menys), el que en treu A vores i la part.

| escenari | sostre de la comprovació 2 | sostre ara | A vores − A neteja d'aire | part del sostre | el mateix |
|---|---|---|---|---|---|
| net | 0.0109 | 0.0109 | 0.0053 | 0.4913 | ✓ |
| curts ×¼ | 0.0153 | 0.0153 | -0.0004 | -0.0291 | ✓ |
| llargs ×¼ | 0.0135 | 0.0135 | -0.0004 | -0.0316 | ✓ |
| barreja ×¼ | 0.0137 | 0.0137 | -0.0006 | -0.0409 | ✓ |
| aire ×¼ | 0.0161 | 0.0161 | 0.0002 | 0.0095 | ✓ |
| curts |  | 0.0170 | -0.0033 | -0.1963 |  |
| llargs |  | 0.0161 | -0.0004 | -0.0252 |  |
| barreja |  | 0.0154 | -0.0017 | -0.1131 |  |
| aire |  | 0.0164 | -0.0031 | -0.1910 |  |
| soroll2 |  | 0.0131 | -0.0056 | -0.4241 |  |
| partit ×¼ | 0.0108 | 0.0108 | 0.0028 | 0.2550 | ✓ |

## Com es mouen els canvis

Els canvis d'A neteja d'aire i on els deixa A vores. «A prop»: amb un canvi de la veritat del mateix
tipus a 12 imatges o menys (a la veritat de toc).

| escenari | canvis per partit | es mouen | amb el de la veritat a prop | distància abans (imatges) | distància després | a 2 o menys, abans | a 2 o menys, després | dels que es mouen i el tenen a prop: s'hi acosten | se n'allunyen |
|---|---|---|---|---|---|---|---|---|---|
| net | 475.200 | 0.674 | 0.789 | 2.114 | 0.978 | 0.713 | 0.890 | 0.839 | 0.161 |
| curts ×¼ | 452.300 | 0.767 | 0.617 | 3.340 | 3.179 | 0.548 | 0.626 | 0.605 | 0.395 |
| llargs ×¼ | 444.700 | 0.762 | 0.600 | 2.925 | 2.560 | 0.607 | 0.704 | 0.664 | 0.336 |
| barreja ×¼ | 447.200 | 0.769 | 0.610 | 3.136 | 2.801 | 0.579 | 0.676 | 0.638 | 0.362 |
| aire ×¼ | 450.800 | 0.783 | 0.527 | 3.326 | 3.183 | 0.565 | 0.636 | 0.599 | 0.401 |
| curts | 444.100 | 0.825 | 0.545 | 4.157 | 4.044 | 0.435 | 0.520 | 0.580 | 0.420 |
| llargs | 435.100 | 0.833 | 0.515 | 3.919 | 3.540 | 0.473 | 0.571 | 0.618 | 0.382 |
| barreja | 440.100 | 0.826 | 0.520 | 3.958 | 3.748 | 0.460 | 0.552 | 0.585 | 0.415 |
| aire | 444.800 | 0.839 | 0.470 | 3.969 | 3.936 | 0.461 | 0.556 | 0.564 | 0.436 |
| soroll2 | 494.500 | 0.864 | 0.341 | 4.496 | 4.995 | 0.397 | 0.437 | 0.484 | 0.516 |
| partit ×¼ | 469.900 | 0.673 | 0.733 | 2.256 | 1.330 | 0.678 | 0.841 | 0.771 | 0.229 |

## L'spellF1 de cada mètode (mitjana dels deu partits)

**spellF1 a la veritat de toc**

| escenari | A xarxes, decodificador de toc | A equips sencers | A neteja d'aire | A vores |
|---|---|---|---|---|
| net | 0.798 | 0.799 | 0.799 | 0.805 |
| curts ×¼ | 0.673 | 0.699 | 0.699 | 0.699 |
| llargs ×¼ | 0.651 | 0.688 | 0.688 | 0.688 |
| barreja ×¼ | 0.660 | 0.696 | 0.696 | 0.696 |
| aire ×¼ | 0.600 | 0.629 | 0.644 | 0.644 |
| curts | 0.636 | 0.665 | 0.665 | 0.661 |
| llargs | 0.599 | 0.640 | 0.640 | 0.640 |
| barreja | 0.605 | 0.646 | 0.646 | 0.645 |
| aire | 0.554 | 0.600 | 0.618 | 0.614 |
| soroll2 | 0.470 | 0.534 | 0.534 | 0.529 |
| partit ×¼ | 0.746 | 0.761 | 0.761 | 0.764 |

**spellF1 a la veritat de sempre**

| escenari | A xarxes, decodificador de toc | A equips sencers | A neteja d'aire | A vores |
|---|---|---|---|---|
| net | 0.808 | 0.810 | 0.810 | 0.816 |
| curts ×¼ | 0.684 | 0.708 | 0.708 | 0.707 |
| llargs ×¼ | 0.662 | 0.700 | 0.700 | 0.699 |
| barreja ×¼ | 0.671 | 0.708 | 0.708 | 0.707 |
| aire ×¼ | 0.612 | 0.643 | 0.658 | 0.658 |
| curts | 0.644 | 0.674 | 0.674 | 0.669 |
| llargs | 0.607 | 0.648 | 0.648 | 0.646 |
| barreja | 0.616 | 0.656 | 0.656 | 0.653 |
| aire | 0.564 | 0.613 | 0.632 | 0.628 |
| soroll2 | 0.478 | 0.543 | 0.543 | 0.536 |
| partit ×¼ | 0.757 | 0.772 | 0.772 | 0.774 |

## Els decodificadors triats

A neteja d'aire i A vores fan servir, a cada partit, el d'A equips sencers.

- **A xarxes, decodificador de toc:** w = 4, λ = 64, durada mínima 1 (1 partits); w = 4, λ = 32, durada mínima 12 (6 partits); w = 4, λ = 32, durada mínima 1 (3 partits)
- **A equips sencers:** w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 16, durada mínima 12 (2 partits)
