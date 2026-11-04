# Banc obert · Les xarxes aprenen també amb el camp girat de dalt a baix (T3ad)

Generat amb `uv run python -I -m banc.model_camp_girat`. Dades obertes: 7 partits de DFL (IDSSE, CC BY
4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3ad», i la capçalera de `banc/model_camp_girat.py`. Es puntua a la
veritat de toc.

**A xarxes, decodificador de toc** i **A equips sencers** són els de la T3v, **A pilota creïble**, el de la T3w, i **A neteja d'aire**,
el de la T3ac, amb les peces de la memòria cau (✓ comprovat: donen l'spellF1 d'aquells bancs, i els
decodificadors triats són els seus). **A camp girat** és A neteja d'aire, amb les cinc xarxes que aprenen i
s'apliquen també amb el camp girat de dalt a baix, i el decodificador triat de nou. ✓ Comprovat a cada
punt de la graella: no dona mai la D a una imatge netejada.

## A camp girat contra A xarxes, decodificador de toc (spellF1): el criteri

| escenari | A xarxes, decodificador de toc | A camp girat | diferència | interval del 95 % | A camp girat guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.798 | 0.803 | +0.005 | -0.004 a +0.014 | 6 de 10 | no perd | ✓ |
| curts ×¼ | 0.673 | 0.703 | +0.029 | +0.022 a +0.037 | 10 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.651 | 0.700 | +0.048 | +0.039 a +0.058 | 10 de 10 | guanya clarament | ✓ |
| barreja ×¼ | 0.660 | 0.706 | +0.046 | +0.041 a +0.052 | 10 de 10 | guanya clarament | ✓ |
| aire ×¼ | 0.600 | 0.656 | +0.056 | +0.048 a +0.064 | 10 de 10 | guanya clarament | ✓ |
| curts | 0.636 | 0.678 | +0.043 | +0.038 a +0.048 | 10 de 10 | no perd | ✓ |
| llargs | 0.599 | 0.656 | +0.056 | +0.043 a +0.070 | 10 de 10 | no perd | ✓ |
| barreja | 0.605 | 0.666 | +0.061 | +0.050 a +0.071 | 10 de 10 | no perd | ✓ |
| aire | 0.554 | 0.632 | +0.077 | +0.068 a +0.088 | 10 de 10 | no perd | ✓ |
| soroll2 | 0.470 | 0.574 | +0.103 | +0.095 a +0.111 | 10 de 10 | no perd | ✓ |
| partit ×¼ | 0.746 | 0.758 | +0.012 | +0.008 a +0.016 | 9 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1, el soroll2 i «partit ×¼» | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## A camp girat contra A neteja d'aire (spellF1)

| escenari | A neteja d'aire | A camp girat | diferència | interval del 95 % | A camp girat guanya |
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

## No passa: és el millor fins ara?

La regla de la D-50, escrita abans, contra A neteja d'aire:

| | És el millor fins ara si | |
|---|---|---|
| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | ✗ |
| «partit ×¼» | la diferència no és negativa | ✗ |
| El net, els ×1 i el soroll2 | no perd (diferència ≥ −0.04) | ✓ |

**A camp girat no és el millor fins ara:** el pas següent es fa a sobre d'A neteja d'aire.

## A camp girat contra A xarxes, decodificador de toc, només els partits de dfl

| escenari | A xarxes, decodificador de toc | A camp girat | diferència | interval del 95 % | A camp girat guanya |
|---|---|---|---|---|---|
| net | 0.766 | 0.769 | +0.004 | -0.004 a +0.011 | 5 de 7 |
| curts ×¼ | 0.642 | 0.674 | +0.032 | +0.022 a +0.042 | 7 de 7 |
| llargs ×¼ | 0.621 | 0.665 | +0.044 | +0.032 a +0.058 | 7 de 7 |
| barreja ×¼ | 0.630 | 0.670 | +0.040 | +0.033 a +0.047 | 7 de 7 |
| aire ×¼ | 0.544 | 0.606 | +0.062 | +0.053 a +0.069 | 7 de 7 |
| curts | 0.607 | 0.647 | +0.040 | +0.033 a +0.047 | 7 de 7 |
| llargs | 0.564 | 0.619 | +0.055 | +0.036 a +0.074 | 7 de 7 |
| barreja | 0.571 | 0.630 | +0.059 | +0.046 a +0.072 | 7 de 7 |
| aire | 0.501 | 0.584 | +0.083 | +0.071 a +0.096 | 7 de 7 |
| soroll2 | 0.433 | 0.527 | +0.094 | +0.082 a +0.103 | 7 de 7 |
| partit ×¼ | 0.717 | 0.723 | +0.006 | +0.001 a +0.011 | 6 de 7 |

## A camp girat contra A neteja d'aire, només els partits de dfl

| escenari | A neteja d'aire | A camp girat | diferència | interval del 95 % | A camp girat guanya |
|---|---|---|---|---|---|
| net | 0.768 | 0.769 | +0.001 | -0.008 a +0.011 | 3 de 7 |
| curts ×¼ | 0.669 | 0.674 | +0.005 | -0.002 a +0.011 | 5 de 7 |
| llargs ×¼ | 0.656 | 0.665 | +0.009 | +0.002 a +0.015 | 6 de 7 |
| barreja ×¼ | 0.664 | 0.670 | +0.006 | +0.003 a +0.009 | 6 de 7 |
| aire ×¼ | 0.592 | 0.606 | +0.014 | +0.005 a +0.024 | 6 de 7 |
| curts | 0.637 | 0.647 | +0.010 | +0.004 a +0.017 | 6 de 7 |
| llargs | 0.602 | 0.619 | +0.017 | +0.013 a +0.021 | 7 de 7 |
| barreja | 0.608 | 0.630 | +0.022 | +0.016 a +0.028 | 7 de 7 |
| aire | 0.572 | 0.584 | +0.012 | +0.004 a +0.020 | 6 de 7 |
| soroll2 | 0.491 | 0.527 | +0.036 | +0.029 a +0.043 | 7 de 7 |
| partit ×¼ | 0.729 | 0.723 | -0.006 | -0.013 a +0.001 | 1 de 7 |

## A camp girat contra A xarxes, decodificador de toc, només els partits de metrica

| escenari | A xarxes, decodificador de toc | A camp girat | diferència | interval del 95 % | A camp girat guanya |
|---|---|---|---|---|---|
| net | 0.874 | 0.881 | +0.007 | -0.009 a +0.037 | 1 de 3 |
| curts ×¼ | 0.747 | 0.771 | +0.024 | +0.013 a +0.033 | 3 de 3 |
| llargs ×¼ | 0.723 | 0.781 | +0.058 | +0.047 a +0.064 | 3 de 3 |
| barreja ×¼ | 0.730 | 0.792 | +0.062 | +0.055 a +0.071 | 3 de 3 |
| aire ×¼ | 0.731 | 0.773 | +0.042 | +0.017 a +0.056 | 3 de 3 |
| curts | 0.702 | 0.752 | +0.049 | +0.043 a +0.054 | 3 de 3 |
| llargs | 0.682 | 0.743 | +0.061 | +0.053 a +0.068 | 3 de 3 |
| barreja | 0.684 | 0.749 | +0.065 | +0.047 a +0.085 | 3 de 3 |
| aire | 0.679 | 0.744 | +0.065 | +0.048 a +0.082 | 3 de 3 |
| soroll2 | 0.557 | 0.684 | +0.127 | +0.119 a +0.140 | 3 de 3 |
| partit ×¼ | 0.813 | 0.838 | +0.025 | +0.015 a +0.031 | 3 de 3 |

## A camp girat contra A neteja d'aire, només els partits de metrica

| escenari | A neteja d'aire | A camp girat | diferència | interval del 95 % | A camp girat guanya |
|---|---|---|---|---|---|
| net | 0.873 | 0.881 | +0.008 | -0.002 a +0.025 | 2 de 3 |
| curts ×¼ | 0.769 | 0.771 | +0.002 | -0.002 a +0.004 | 2 de 3 |
| llargs ×¼ | 0.763 | 0.781 | +0.018 | +0.006 a +0.029 | 3 de 3 |
| barreja ×¼ | 0.773 | 0.792 | +0.019 | +0.012 a +0.028 | 3 de 3 |
| aire ×¼ | 0.765 | 0.773 | +0.008 | +0.001 a +0.020 | 3 de 3 |
| curts | 0.729 | 0.752 | +0.023 | +0.013 a +0.031 | 3 de 3 |
| llargs | 0.730 | 0.743 | +0.013 | +0.011 a +0.015 | 3 de 3 |
| barreja | 0.736 | 0.749 | +0.014 | -0.012 a +0.030 | 2 de 3 |
| aire | 0.724 | 0.744 | +0.020 | +0.010 a +0.040 | 3 de 3 |
| soroll2 | 0.634 | 0.684 | +0.050 | +0.040 a +0.057 | 3 de 3 |
| partit ×¼ | 0.835 | 0.838 | +0.003 | -0.004 a +0.014 | 1 de 3 |

## Les possessions de la veritat aparellades, per durada

Les possessions de la veritat de toc, i la part que s'aparella amb una de la predicció a la IoU 0.5
(com a l'spellF1), de cada mètode amb el seu decodificador.

| escenari | durada | n per partit | aparellades · A neteja d'aire | aparellades · A camp girat |
|---|---|---|---|---|
| net | de menys d'1 s | 55 | 0.328 | 0.304 |
| net | d'1 a 2 s | 75 | 0.609 | 0.629 |
| net | de 2 a 5 s | 124 | 0.786 | 0.793 |
| net | de 5 a 10 s | 76 | 0.908 | 0.904 |
| net | de 10 s o més | 98 | 0.971 | 0.975 |
| curts ×¼ | de menys d'1 s | 55 | 0.161 | 0.156 |
| curts ×¼ | d'1 a 2 s | 75 | 0.406 | 0.419 |
| curts ×¼ | de 2 a 5 s | 124 | 0.658 | 0.663 |
| curts ×¼ | de 5 a 10 s | 76 | 0.837 | 0.839 |
| curts ×¼ | de 10 s o més | 98 | 0.943 | 0.945 |
| partit ×¼ | de menys d'1 s | 55 | 0.259 | 0.246 |
| partit ×¼ | d'1 a 2 s | 75 | 0.573 | 0.578 |
| partit ×¼ | de 2 a 5 s | 124 | 0.743 | 0.738 |
| partit ×¼ | de 5 a 10 s | 76 | 0.867 | 0.875 |
| partit ×¼ | de 10 s o més | 98 | 0.954 | 0.958 |

## On encerten l'equip les xarxes i el segon

On la veritat de toc és d'un equip, la part de les imatges on l'equip més probable és el bo (les
xarxes, amb les seves probabilitats; el segon, amb la relativa). Amb pilota i sense, al partit netejat.

| escenari | on | n imatges | xarxes d'A neteja d'aire | xarxes noves | segon d'A neteja d'aire | segon nou |
|---|---|---|---|---|---|---|
| curts ×¼ | amb pilota | 482559 | 0.926 | 0.932 | 0.941 | 0.944 |
| curts ×¼ | sense pilota | 335337 | 0.880 | 0.889 | 0.891 | 0.894 |
| llargs ×¼ | amb pilota | 482559 | 0.924 | 0.930 | 0.944 | 0.946 |
| llargs ×¼ | sense pilota | 335337 | 0.861 | 0.873 | 0.880 | 0.885 |
| barreja ×¼ | amb pilota | 482559 | 0.923 | 0.931 | 0.944 | 0.946 |
| barreja ×¼ | sense pilota | 335337 | 0.866 | 0.879 | 0.881 | 0.885 |
| aire ×¼ | amb pilota | 463608 | 0.917 | 0.922 | 0.932 | 0.935 |
| aire ×¼ | sense pilota | 354288 | 0.858 | 0.870 | 0.875 | 0.880 |
| partit ×¼ | amb pilota | 736106 | 0.917 | 0.924 | 0.939 | 0.941 |
| partit ×¼ | sense pilota | 81790 | 0.877 | 0.881 | 0.896 | 0.896 |

## L'spellF1 de cada mètode (mitjana dels deu partits)

**spellF1 a la veritat de toc**

| escenari | A xarxes, decodificador de toc | A equips sencers | A neteja d'aire | A camp girat |
|---|---|---|---|---|
| net | 0.798 | 0.799 | 0.799 | 0.803 |
| curts ×¼ | 0.673 | 0.699 | 0.699 | 0.703 |
| llargs ×¼ | 0.651 | 0.688 | 0.688 | 0.700 |
| barreja ×¼ | 0.660 | 0.696 | 0.696 | 0.706 |
| aire ×¼ | 0.600 | 0.629 | 0.644 | 0.656 |
| curts | 0.636 | 0.665 | 0.665 | 0.678 |
| llargs | 0.599 | 0.640 | 0.640 | 0.656 |
| barreja | 0.605 | 0.646 | 0.646 | 0.666 |
| aire | 0.554 | 0.600 | 0.618 | 0.632 |
| soroll2 | 0.470 | 0.534 | 0.534 | 0.574 |
| partit ×¼ | 0.746 | 0.761 | 0.761 | 0.758 |

**spellF1 a la veritat de sempre**

| escenari | A xarxes, decodificador de toc | A equips sencers | A neteja d'aire | A camp girat |
|---|---|---|---|---|
| net | 0.808 | 0.810 | 0.810 | 0.812 |
| curts ×¼ | 0.684 | 0.708 | 0.708 | 0.712 |
| llargs ×¼ | 0.662 | 0.700 | 0.700 | 0.710 |
| barreja ×¼ | 0.671 | 0.708 | 0.708 | 0.719 |
| aire ×¼ | 0.612 | 0.643 | 0.658 | 0.669 |
| curts | 0.644 | 0.674 | 0.674 | 0.688 |
| llargs | 0.607 | 0.648 | 0.648 | 0.665 |
| barreja | 0.616 | 0.656 | 0.656 | 0.678 |
| aire | 0.564 | 0.613 | 0.632 | 0.643 |
| soroll2 | 0.478 | 0.543 | 0.543 | 0.584 |
| partit ×¼ | 0.757 | 0.772 | 0.772 | 0.770 |

## Els decodificadors triats

A neteja d'aire fa servir, a cada partit, el d'A equips sencers.

- **A xarxes, decodificador de toc:** w = 4, λ = 64, durada mínima 1 (1 partits); w = 4, λ = 32, durada mínima 12 (6 partits); w = 4, λ = 32, durada mínima 1 (3 partits)
- **A equips sencers:** w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 16, durada mínima 12 (2 partits)
- **A camp girat:** w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 32, durada mínima 25 (2 partits)
