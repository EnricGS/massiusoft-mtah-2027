# Banc obert · La pilota a 10 m o més fora del camp, com un forat (T3w)

Generat amb `uv run python -I -m banc.model_pilota_creible`. Dades obertes: 7 partits de DFL (IDSSE,
CC BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3w», i la capçalera de `banc/model_pilota_creible.py`. Es puntua a la
veritat de toc.

**A xarxes** i **A equips sencers** són els de la T3v, amb les peces de la memòria cau (✓ comprovat: a
cada punt de la graella donen l'spellF1 del banc de la T3v). **A pilota creïble** és A equips sencers, amb la
pilota vista a 10 m o més fora del camp tractada com si no es veiés. Les peces del partit que es prova
s'han tornat a entrenar (✓ comprovat: on la neteja no canvia res, són exactament les de la memòria
cau).

## On canvia l'entrada

Les imatges on es veu la pilota, i quantes en canvia la neteja (✓ cap als sis escenaris
d'entrenament).

| escenari | font | n vistes | n canvien | part |
|---|---|---|---|---|
| net | dfl | 1002644 | 0 | 0.000 |
| net | metrica | 268959 | 0 | 0.000 |
| curts ×¼ | dfl | 584925 | 0 | 0.000 |
| curts ×¼ | metrica | 161751 | 0 | 0.000 |
| llargs ×¼ | dfl | 559723 | 0 | 0.000 |
| llargs ×¼ | metrica | 161209 | 0 | 0.000 |
| barreja ×¼ | dfl | 567967 | 0 | 0.000 |
| barreja ×¼ | metrica | 161836 | 0 | 0.000 |
| aire ×¼ | dfl | 563809 | 18951 | 0.034 |
| aire ×¼ | metrica | 161557 | 0 | 0.000 |
| curts | dfl | 584925 | 0 | 0.000 |
| curts | metrica | 161751 | 0 | 0.000 |
| llargs | dfl | 559723 | 0 | 0.000 |
| llargs | metrica | 161209 | 0 | 0.000 |
| barreja | dfl | 567967 | 0 | 0.000 |
| barreja | metrica | 161836 | 0 | 0.000 |
| aire | dfl | 563809 | 19014 | 0.034 |
| aire | metrica | 161557 | 0 | 0.000 |
| soroll2 | dfl | 565674 | 6 | 0.000 |
| soroll2 | metrica | 161432 | 1 | 0.000 |
| partit ×¼ | dfl | 510017 | 0 | 0.000 |
| partit ×¼ | metrica | 241233 | 0 | 0.000 |

## A pilota creïble contra A xarxes, decodificador de toc (spellF1): el criteri

| escenari | A xarxes, decodificador de toc | A pilota creïble | diferència | interval del 95 % | A pilota creïble guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.798 | 0.799 | +0.001 | -0.004 a +0.007 | 5 de 10 | no perd | ✓ |
| curts ×¼ | 0.673 | 0.699 | +0.026 | +0.021 a +0.032 | 10 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.651 | 0.688 | +0.037 | +0.028 a +0.046 | 10 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.660 | 0.696 | +0.036 | +0.030 a +0.043 | 10 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.600 | 0.636 | +0.036 | +0.027 a +0.044 | 10 de 10 | guanya clarament | ✗ |
| curts | 0.636 | 0.665 | +0.029 | +0.023 a +0.035 | 10 de 10 | no perd | ✓ |
| llargs | 0.599 | 0.641 | +0.041 | +0.028 a +0.055 | 10 de 10 | no perd | ✓ |
| barreja | 0.605 | 0.646 | +0.041 | +0.030 a +0.052 | 10 de 10 | no perd | ✓ |
| aire | 0.554 | 0.605 | +0.051 | +0.045 a +0.056 | 10 de 10 | no perd | ✓ |
| soroll2 | 0.470 | 0.536 | +0.066 | +0.058 a +0.074 | 10 de 10 | no perd | ✓ |
| partit ×¼ | 0.746 | 0.761 | +0.015 | +0.009 a +0.022 | 8 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1, el soroll2 i «partit ×¼» | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## A pilota creïble contra A equips sencers (spellF1)

| escenari | A equips sencers | A pilota creïble | diferència | interval del 95 % | A pilota creïble guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.799 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| curts ×¼ | 0.699 | 0.699 | +0.000 | -0.000 a +0.001 | 1 de 10 |
| llargs ×¼ | 0.688 | 0.688 | +0.000 | -0.000 a +0.000 | 1 de 10 |
| barreja ×¼ | 0.696 | 0.696 | -0.000 | -0.000 a +0.000 | 0 de 10 |
| aire ×¼ | 0.629 | 0.636 | +0.007 | +0.002 a +0.010 | 6 de 10 |
| curts | 0.665 | 0.665 | +0.000 | -0.000 a +0.000 | 1 de 10 |
| llargs | 0.640 | 0.641 | +0.000 | +0.000 a +0.001 | 2 de 10 |
| barreja | 0.646 | 0.646 | -0.000 | -0.001 a +0.000 | 1 de 10 |
| aire | 0.600 | 0.605 | +0.005 | +0.000 a +0.010 | 5 de 10 |
| soroll2 | 0.534 | 0.536 | +0.002 | +0.000 a +0.004 | 2 de 10 |
| partit ×¼ | 0.761 | 0.761 | -0.000 | -0.001 a +0.000 | 1 de 10 |

## No passa: és el millor fins ara?

La regla dels passos que només van a un escenari (D-55), escrita abans, contra A equips sencers:

| | És el millor fins ara si | |
|---|---|---|
| aire ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | ✓ |
| Els altres tres ×¼ i «partit ×¼» | la diferència no és negativa | ✗ |
| El net, els ×1 i el soroll2 | no perd (diferència ≥ −0.04) | ✓ |

**A pilota creïble no és el millor fins ara:** el pas següent es fa a sobre d'A equips sencers.

## A pilota creïble contra A xarxes, decodificador de toc, només els partits de dfl

| escenari | A xarxes, decodificador de toc | A pilota creïble | diferència | interval del 95 % | A pilota creïble guanya |
|---|---|---|---|---|---|
| net | 0.766 | 0.768 | +0.002 | -0.004 a +0.009 | 4 de 7 |
| curts ×¼ | 0.642 | 0.669 | +0.027 | +0.022 a +0.035 | 7 de 7 |
| llargs ×¼ | 0.621 | 0.656 | +0.035 | +0.025 a +0.046 | 7 de 7 |
| barreja ×¼ | 0.630 | 0.663 | +0.033 | +0.027 a +0.040 | 7 de 7 |
| aire ×¼ | 0.544 | 0.581 | +0.036 | +0.026 a +0.047 | 7 de 7 |
| curts | 0.607 | 0.637 | +0.030 | +0.023 a +0.038 | 7 de 7 |
| llargs | 0.564 | 0.602 | +0.038 | +0.019 a +0.058 | 7 de 7 |
| barreja | 0.571 | 0.608 | +0.037 | +0.028 a +0.047 | 7 de 7 |
| aire | 0.501 | 0.554 | +0.053 | +0.046 a +0.061 | 7 de 7 |
| soroll2 | 0.433 | 0.494 | +0.061 | +0.052 a +0.069 | 7 de 7 |
| partit ×¼ | 0.717 | 0.729 | +0.012 | +0.004 a +0.020 | 5 de 7 |

## A pilota creïble contra A equips sencers, només els partits de dfl

| escenari | A equips sencers | A pilota creïble | diferència | interval del 95 % | A pilota creïble guanya |
|---|---|---|---|---|---|
| net | 0.768 | 0.768 | +0.000 | +0.000 a +0.000 | 0 de 7 |
| curts ×¼ | 0.669 | 0.669 | +0.000 | -0.000 a +0.001 | 1 de 7 |
| llargs ×¼ | 0.656 | 0.656 | +0.000 | -0.000 a +0.001 | 1 de 7 |
| barreja ×¼ | 0.664 | 0.663 | -0.000 | -0.001 a +0.000 | 0 de 7 |
| aire ×¼ | 0.571 | 0.581 | +0.010 | +0.002 a +0.015 | 6 de 7 |
| curts | 0.637 | 0.637 | +0.000 | -0.000 a +0.000 | 1 de 7 |
| llargs | 0.602 | 0.602 | +0.000 | +0.000 a +0.001 | 2 de 7 |
| barreja | 0.608 | 0.608 | -0.000 | -0.001 a +0.000 | 1 de 7 |
| aire | 0.546 | 0.554 | +0.008 | +0.000 a +0.015 | 5 de 7 |
| soroll2 | 0.491 | 0.494 | +0.003 | +0.000 a +0.006 | 2 de 7 |
| partit ×¼ | 0.729 | 0.729 | -0.000 | -0.001 a +0.001 | 1 de 7 |

## A pilota creïble contra A xarxes, decodificador de toc, només els partits de metrica

| escenari | A xarxes, decodificador de toc | A pilota creïble | diferència | interval del 95 % | A pilota creïble guanya |
|---|---|---|---|---|---|
| net | 0.874 | 0.873 | -0.001 | -0.010 a +0.012 | 1 de 3 |
| curts ×¼ | 0.747 | 0.769 | +0.023 | +0.014 a +0.031 | 3 de 3 |
| llargs ×¼ | 0.723 | 0.763 | +0.040 | +0.027 a +0.059 | 3 de 3 |
| barreja ×¼ | 0.730 | 0.773 | +0.043 | +0.031 a +0.060 | 3 de 3 |
| aire ×¼ | 0.731 | 0.765 | +0.034 | +0.017 a +0.050 | 3 de 3 |
| curts | 0.702 | 0.729 | +0.026 | +0.012 a +0.041 | 3 de 3 |
| llargs | 0.682 | 0.730 | +0.048 | +0.041 a +0.053 | 3 de 3 |
| barreja | 0.684 | 0.736 | +0.051 | +0.017 a +0.074 | 3 de 3 |
| aire | 0.679 | 0.724 | +0.045 | +0.038 a +0.055 | 3 de 3 |
| soroll2 | 0.557 | 0.634 | +0.077 | +0.061 a +0.100 | 3 de 3 |
| partit ×¼ | 0.813 | 0.835 | +0.023 | +0.016 a +0.035 | 3 de 3 |

## A pilota creïble contra A equips sencers, només els partits de metrica

| escenari | A equips sencers | A pilota creïble | diferència | interval del 95 % | A pilota creïble guanya |
|---|---|---|---|---|---|
| net | 0.873 | 0.873 | +0.000 | +0.000 a +0.000 | 0 de 3 |
| curts ×¼ | 0.769 | 0.769 | +0.000 | +0.000 a +0.000 | 0 de 3 |
| llargs ×¼ | 0.763 | 0.763 | +0.000 | +0.000 a +0.000 | 0 de 3 |
| barreja ×¼ | 0.773 | 0.773 | +0.000 | +0.000 a +0.000 | 0 de 3 |
| aire ×¼ | 0.765 | 0.765 | +0.000 | +0.000 a +0.000 | 0 de 3 |
| curts | 0.729 | 0.729 | +0.000 | +0.000 a +0.000 | 0 de 3 |
| llargs | 0.730 | 0.730 | +0.000 | +0.000 a +0.000 | 0 de 3 |
| barreja | 0.736 | 0.736 | +0.000 | +0.000 a +0.000 | 0 de 3 |
| aire | 0.724 | 0.724 | +0.000 | +0.000 a +0.000 | 0 de 3 |
| soroll2 | 0.634 | 0.634 | +0.000 | +0.000 a +0.000 | 0 de 3 |
| partit ×¼ | 0.835 | 0.835 | +0.000 | +0.000 a +0.000 | 0 de 3 |

## La D a aire ×¼, a DFL

Als trams vàlids, on la veritat de toc és d'un equip: per on es veu la pilota i a quants metres de la
línia s'ha vist fora del camp (on es veu, la seva; als forats, la més gran de la pilota vista just
abans i just després), quina part d'aquestes imatges hi ha, i a quina part la predicció hi dona la D.
Tot, a l'escenari sense netejar, per als dos mètodes.

| on | distància | imatges d'un equip | la D · A equips sencers | la D · A pilota creïble |
|---|---|---|---|---|
| es veu la pilota | dins del camp (a 1 m o menys) | 0.536 | 0.003 | 0.004 |
| es veu la pilota | fora, a 1-10 m | 0.020 | 0.052 | 0.105 |
| es veu la pilota | fora, a 10-50 m | 0.021 | 0.101 | 0.336 |
| es veu la pilota | fora, a 50 m o més | 0.013 | 0.114 | 0.431 |
| al forat | dins del camp (a 1 m o menys) | 0.305 | 0.043 | 0.042 |
| al forat | fora, a 1-10 m | 0.045 | 0.172 | 0.175 |
| al forat | fora, a 10-50 m | 0.034 | 0.351 | 0.246 |
| al forat | fora, a 50 m o més | 0.026 | 0.647 | 0.289 |
| totes |  | 1.000 | 0.056 | 0.054 |

## L'spellF1 de cada mètode (mitjana dels deu partits)

**spellF1 a la veritat de toc**

| escenari | A xarxes, decodificador de toc | A equips sencers | A pilota creïble |
|---|---|---|---|
| net | 0.798 | 0.799 | 0.799 |
| curts ×¼ | 0.673 | 0.699 | 0.699 |
| llargs ×¼ | 0.651 | 0.688 | 0.688 |
| barreja ×¼ | 0.660 | 0.696 | 0.696 |
| aire ×¼ | 0.600 | 0.629 | 0.636 |
| curts | 0.636 | 0.665 | 0.665 |
| llargs | 0.599 | 0.640 | 0.641 |
| barreja | 0.605 | 0.646 | 0.646 |
| aire | 0.554 | 0.600 | 0.605 |
| soroll2 | 0.470 | 0.534 | 0.536 |
| partit ×¼ | 0.746 | 0.761 | 0.761 |

**spellF1 a la veritat de sempre**

| escenari | A xarxes, decodificador de toc | A equips sencers | A pilota creïble |
|---|---|---|---|
| net | 0.808 | 0.810 | 0.810 |
| curts ×¼ | 0.684 | 0.708 | 0.708 |
| llargs ×¼ | 0.662 | 0.700 | 0.700 |
| barreja ×¼ | 0.671 | 0.708 | 0.708 |
| aire ×¼ | 0.612 | 0.643 | 0.650 |
| curts | 0.644 | 0.674 | 0.674 |
| llargs | 0.607 | 0.648 | 0.648 |
| barreja | 0.616 | 0.656 | 0.656 |
| aire | 0.564 | 0.613 | 0.619 |
| soroll2 | 0.478 | 0.543 | 0.545 |
| partit ×¼ | 0.757 | 0.772 | 0.772 |

## Els decodificadors triats

- **A xarxes, decodificador de toc:** w = 4, λ = 64, durada mínima 1 (1 partits); w = 4, λ = 32, durada mínima 12 (6 partits); w = 4, λ = 32, durada mínima 1 (3 partits)
- **A equips sencers:** w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 16, durada mínima 12 (2 partits)
- **A pilota creïble:** w = 4, λ = 32, durada mínima 12 (10 partits)
