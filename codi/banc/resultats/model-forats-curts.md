# Banc obert · Un model de cada forat curt, al decodificador (T3x)

Generat amb `uv run python -I -m banc.model_forats_curts`. Dades obertes: 7 partits de DFL (IDSSE, CC BY
4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3x», i la capçalera de `banc/model_forats_curts.py`. Es puntua a la
veritat de toc.

**A xarxes, decodificador de toc** i **A equips sencers** són els de la T3v, amb les probabilitats de la memòria cau (✓
comprovat: decodificats de nou, donen l'spellF1 del banc de la T3v; A equips sencers, amb β = 0).
**A forats curts** és A equips sencers amb el cost dels canvis d'equip de dins dels forats curts canviat pel
model del forat.

## A forats curts contra A xarxes, decodificador de toc (spellF1): el criteri

| escenari | A xarxes, decodificador de toc | A forats curts | diferència | interval del 95 % | A forats curts guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.798 | 0.800 | +0.002 | -0.004 a +0.008 | 5 de 10 | no perd | ✓ |
| curts ×¼ | 0.673 | 0.700 | +0.026 | +0.021 a +0.033 | 10 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.651 | 0.689 | +0.037 | +0.028 a +0.047 | 10 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.660 | 0.697 | +0.037 | +0.031 a +0.043 | 10 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.600 | 0.630 | +0.029 | +0.024 a +0.035 | 10 de 10 | guanya clarament | ✗ |
| curts | 0.636 | 0.666 | +0.030 | +0.023 a +0.037 | 10 de 10 | no perd | ✓ |
| llargs | 0.599 | 0.641 | +0.041 | +0.028 a +0.055 | 9 de 10 | no perd | ✓ |
| barreja | 0.605 | 0.646 | +0.041 | +0.031 a +0.051 | 10 de 10 | no perd | ✓ |
| aire | 0.554 | 0.600 | +0.045 | +0.041 a +0.051 | 10 de 10 | no perd | ✓ |
| soroll2 | 0.470 | 0.535 | +0.065 | +0.058 a +0.072 | 10 de 10 | no perd | ✓ |
| partit ×¼ | 0.746 | 0.762 | +0.016 | +0.009 a +0.023 | 8 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1, el soroll2 i «partit ×¼» | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## A forats curts contra A equips sencers (spellF1)

| escenari | A equips sencers | A forats curts | diferència | interval del 95 % | A forats curts guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.800 | +0.000 | +0.000 a +0.001 | 2 de 10 |
| curts ×¼ | 0.699 | 0.700 | +0.001 | -0.001 a +0.002 | 7 de 10 |
| llargs ×¼ | 0.688 | 0.689 | +0.001 | +0.000 a +0.001 | 3 de 10 |
| barreja ×¼ | 0.696 | 0.697 | +0.001 | +0.000 a +0.001 | 8 de 10 |
| aire ×¼ | 0.629 | 0.630 | +0.000 | -0.000 a +0.001 | 5 de 10 |
| curts | 0.665 | 0.666 | +0.001 | -0.001 a +0.004 | 7 de 10 |
| llargs | 0.640 | 0.641 | +0.000 | -0.000 a +0.001 | 3 de 10 |
| barreja | 0.646 | 0.646 | +0.000 | -0.001 a +0.001 | 5 de 10 |
| aire | 0.600 | 0.600 | +0.000 | -0.000 a +0.001 | 2 de 10 |
| soroll2 | 0.534 | 0.535 | +0.001 | -0.000 a +0.002 | 6 de 10 |
| partit ×¼ | 0.761 | 0.762 | +0.001 | +0.000 a +0.001 | 3 de 10 |

## No passa: és el millor fins ara?

La regla dels passos que només van a un escenari (D-55), escrita abans, a curts ×¼, contra A equips sencers:

| | És el millor fins ara si | |
|---|---|---|
| curts ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | ✗ |
| Els altres tres ×¼ i «partit ×¼» | la diferència no és negativa | ✓ |
| El net, els ×1 i el soroll2 | no perd (diferència ≥ −0.04) | ✓ |

**A forats curts no és el millor fins ara:** el pas següent es fa a sobre d'A equips sencers.

## A forats curts contra A xarxes, decodificador de toc, només els partits de dfl

| escenari | A xarxes, decodificador de toc | A forats curts | diferència | interval del 95 % | A forats curts guanya |
|---|---|---|---|---|---|
| net | 0.766 | 0.768 | +0.002 | -0.004 a +0.009 | 4 de 7 |
| curts ×¼ | 0.642 | 0.669 | +0.027 | +0.021 a +0.037 | 7 de 7 |
| llargs ×¼ | 0.621 | 0.657 | +0.036 | +0.025 a +0.047 | 7 de 7 |
| barreja ×¼ | 0.630 | 0.665 | +0.035 | +0.028 a +0.041 | 7 de 7 |
| aire ×¼ | 0.544 | 0.571 | +0.027 | +0.022 a +0.032 | 7 de 7 |
| curts | 0.607 | 0.638 | +0.031 | +0.022 a +0.039 | 7 de 7 |
| llargs | 0.564 | 0.602 | +0.038 | +0.019 a +0.057 | 6 de 7 |
| barreja | 0.571 | 0.608 | +0.037 | +0.028 a +0.048 | 7 de 7 |
| aire | 0.501 | 0.546 | +0.045 | +0.039 a +0.052 | 7 de 7 |
| soroll2 | 0.433 | 0.492 | +0.059 | +0.052 a +0.066 | 7 de 7 |
| partit ×¼ | 0.717 | 0.729 | +0.012 | +0.004 a +0.021 | 5 de 7 |

## A forats curts contra A equips sencers, només els partits de dfl

| escenari | A equips sencers | A forats curts | diferència | interval del 95 % | A forats curts guanya |
|---|---|---|---|---|---|
| net | 0.768 | 0.768 | +0.000 | +0.000 a +0.000 | 0 de 7 |
| curts ×¼ | 0.669 | 0.669 | +0.000 | -0.002 a +0.002 | 4 de 7 |
| llargs ×¼ | 0.656 | 0.657 | +0.001 | +0.000 a +0.002 | 2 de 7 |
| barreja ×¼ | 0.664 | 0.665 | +0.001 | +0.000 a +0.002 | 5 de 7 |
| aire ×¼ | 0.571 | 0.571 | -0.000 | -0.001 a +0.001 | 3 de 7 |
| curts | 0.637 | 0.638 | +0.000 | -0.003 a +0.003 | 4 de 7 |
| llargs | 0.602 | 0.602 | -0.000 | -0.001 a +0.001 | 1 de 7 |
| barreja | 0.608 | 0.608 | +0.000 | -0.000 a +0.001 | 3 de 7 |
| aire | 0.546 | 0.546 | -0.000 | -0.001 a -0.000 | 1 de 7 |
| soroll2 | 0.491 | 0.492 | +0.001 | -0.000 a +0.002 | 4 de 7 |
| partit ×¼ | 0.729 | 0.729 | +0.000 | +0.000 a +0.000 | 1 de 7 |

## A forats curts contra A xarxes, decodificador de toc, només els partits de metrica

| escenari | A xarxes, decodificador de toc | A forats curts | diferència | interval del 95 % | A forats curts guanya |
|---|---|---|---|---|---|
| net | 0.874 | 0.874 | +0.000 | -0.009 a +0.015 | 1 de 3 |
| curts ×¼ | 0.747 | 0.770 | +0.024 | +0.016 a +0.031 | 3 de 3 |
| llargs ×¼ | 0.723 | 0.763 | +0.040 | +0.028 a +0.059 | 3 de 3 |
| barreja ×¼ | 0.730 | 0.773 | +0.043 | +0.032 a +0.060 | 3 de 3 |
| aire ×¼ | 0.731 | 0.766 | +0.036 | +0.017 a +0.050 | 3 de 3 |
| curts | 0.702 | 0.733 | +0.030 | +0.018 a +0.041 | 3 de 3 |
| llargs | 0.682 | 0.732 | +0.049 | +0.044 a +0.055 | 3 de 3 |
| barreja | 0.684 | 0.736 | +0.052 | +0.021 a +0.070 | 3 de 3 |
| aire | 0.679 | 0.726 | +0.046 | +0.038 a +0.055 | 3 de 3 |
| soroll2 | 0.557 | 0.635 | +0.078 | +0.065 a +0.099 | 3 de 3 |
| partit ×¼ | 0.813 | 0.837 | +0.024 | +0.019 a +0.035 | 3 de 3 |

## A forats curts contra A equips sencers, només els partits de metrica

| escenari | A equips sencers | A forats curts | diferència | interval del 95 % | A forats curts guanya |
|---|---|---|---|---|---|
| net | 0.873 | 0.874 | +0.001 | +0.000 a +0.003 | 2 de 3 |
| curts ×¼ | 0.769 | 0.770 | +0.001 | +0.000 a +0.001 | 3 de 3 |
| llargs ×¼ | 0.763 | 0.763 | +0.000 | +0.000 a +0.001 | 1 de 3 |
| barreja ×¼ | 0.773 | 0.773 | +0.001 | +0.001 a +0.001 | 3 de 3 |
| aire ×¼ | 0.765 | 0.766 | +0.001 | +0.000 a +0.004 | 2 de 3 |
| curts | 0.729 | 0.733 | +0.004 | +0.001 a +0.006 | 3 de 3 |
| llargs | 0.730 | 0.732 | +0.002 | +0.000 a +0.003 | 2 de 3 |
| barreja | 0.736 | 0.736 | +0.000 | -0.004 a +0.004 | 2 de 3 |
| aire | 0.724 | 0.726 | +0.002 | +0.000 a +0.005 | 1 de 3 |
| soroll2 | 0.634 | 0.635 | +0.001 | -0.001 a +0.004 | 2 de 3 |
| partit ×¼ | 0.835 | 0.837 | +0.002 | +0.000 a +0.004 | 2 de 3 |

## El model dels forats

Als forats curts amb les dues vores als trams vàlids, dels deu partits, cadascun amb el model que no l'ha
vist: quants n'hi ha, quina part tenen canvi d'equip, i l'AUC del model.

| escenari | n forats | amb canvi | AUC |
|---|---|---|---|
| net | 222 | 0.752 | 0.884 |
| curts ×¼ | 8347 | 0.161 | 0.863 |
| llargs ×¼ | 309 | 0.489 | 0.832 |
| barreja ×¼ | 2332 | 0.173 | 0.872 |
| aire ×¼ | 2260 | 0.193 | 0.799 |
| curts | 8347 | 0.161 | 0.827 |
| llargs | 309 | 0.489 | 0.819 |
| barreja | 2332 | 0.173 | 0.843 |
| aire | 2260 | 0.193 | 0.754 |
| soroll2 | 2384 | 0.185 | 0.803 |
| partit ×¼ | 310 | 0.526 | 0.890 |

## Què hi fa la predicció als forats curts de curts ×¼

Als d'un canvi i als sense canvi, com a `canvis_als_forats.py`, amb la β triada a cada partit.

| tipus | fa | n A equips sencers | n A forats curts |
|---|---|---|---|
| sense canvi | cap canvi | 5970 | 5977 |
| sense canvi | hi canvia d'equip (o ja hi arriba canviada) | 466 | 458 |
| sense canvi | hi fa una altra cosa | 1 | 1 |
| sense canvi | hi inventa una possessió de l'altre equip | 7 | 8 |
| sense canvi | hi posa la D | 44 | 44 |
| un canvi d'equip | es queda amb l'equip d'abans | 284 | 257 |
| un canvi d'equip | hi fa un sol canvi | 563 | 591 |
| un canvi d'equip | hi fa una altra cosa | 45 | 53 |
| un canvi d'equip | ja hi té l'equip nou | 168 | 159 |

## Les β triades

- β = 1 (w = 4, λ = 16, durada mínima 12): 2 partits
- β = 1 (w = 4, λ = 32, durada mínima 12): 8 partits

## L'spellF1 de cada mètode (mitjana dels deu partits)

**spellF1 a la veritat de toc**

| escenari | A xarxes, decodificador de toc | A equips sencers | A forats curts |
|---|---|---|---|
| net | 0.798 | 0.799 | 0.800 |
| curts ×¼ | 0.673 | 0.699 | 0.700 |
| llargs ×¼ | 0.651 | 0.688 | 0.689 |
| barreja ×¼ | 0.660 | 0.696 | 0.697 |
| aire ×¼ | 0.600 | 0.629 | 0.630 |
| curts | 0.636 | 0.665 | 0.666 |
| llargs | 0.599 | 0.640 | 0.641 |
| barreja | 0.605 | 0.646 | 0.646 |
| aire | 0.554 | 0.600 | 0.600 |
| soroll2 | 0.470 | 0.534 | 0.535 |
| partit ×¼ | 0.746 | 0.761 | 0.762 |

**spellF1 a la veritat de sempre**

| escenari | A xarxes, decodificador de toc | A equips sencers | A forats curts |
|---|---|---|---|
| net | 0.808 | 0.810 | 0.811 |
| curts ×¼ | 0.684 | 0.708 | 0.709 |
| llargs ×¼ | 0.662 | 0.700 | 0.700 |
| barreja ×¼ | 0.671 | 0.708 | 0.708 |
| aire ×¼ | 0.612 | 0.643 | 0.643 |
| curts | 0.644 | 0.674 | 0.675 |
| llargs | 0.607 | 0.648 | 0.648 |
| barreja | 0.616 | 0.656 | 0.656 |
| aire | 0.564 | 0.613 | 0.613 |
| soroll2 | 0.478 | 0.543 | 0.544 |
| partit ×¼ | 0.757 | 0.772 | 0.773 |
