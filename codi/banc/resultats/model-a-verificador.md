# Banc obert · Un verificador de les possessions (T3s)

Generat amb `uv run python -I -m banc.model_a_verificador`. Dades obertes: 7 partits de DFL (IDSSE, CC
BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3s», i la capçalera de `banc/model_a_verificador.py`. Es puntua a la
veritat de toc.

**A xarxes, decodificador de toc** és A xarxes amb el decodificador triat a la veritat de toc, de la memòria cau (✓
comprovat: a cada partit dona l'spellF1 del banc de la T3r). **A verificador** és el mateix, amb les
possessions que el verificador diu inventades passades a l'altre equip.

## A verificador contra A xarxes, decodificador de toc (spellF1): el criteri

| escenari | A xarxes, decodificador de toc | A verificador | diferència | interval del 95 % | A verificador guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.798 | 0.799 | +0.000 | -0.001 a +0.002 | 5 de 10 | no perd | ✓ |
| curts ×¼ | 0.673 | 0.674 | +0.000 | -0.001 a +0.002 | 5 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.651 | 0.652 | +0.001 | -0.000 a +0.002 | 4 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.660 | 0.661 | +0.001 | -0.001 a +0.003 | 7 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.600 | 0.601 | +0.001 | -0.001 a +0.002 | 4 de 10 | guanya clarament | ✗ |
| curts | 0.636 | 0.636 | +0.000 | -0.000 a +0.001 | 4 de 10 | no perd | ✓ |
| llargs | 0.599 | 0.599 | -0.000 | -0.001 a +0.001 | 3 de 10 | no perd | ✓ |
| barreja | 0.605 | 0.604 | -0.001 | -0.002 a +0.001 | 3 de 10 | no perd | ✓ |
| aire | 0.554 | 0.556 | +0.001 | +0.000 a +0.003 | 6 de 10 | no perd | ✓ |
| soroll2 | 0.470 | 0.471 | +0.001 | -0.000 a +0.002 | 5 de 10 | no perd | ✓ |
| partit ×¼ | 0.746 | 0.746 | +0.001 | -0.001 a +0.002 | 4 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1, el soroll2 i «partit ×¼» | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## No passa: és el millor fins ara?

| | És el millor fins ara si | |
|---|---|---|
| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | ✗ |
| «partit ×¼» | la diferència no és negativa | ✓ |
| El net, els ×1 i el soroll2 | no perd (diferència ≥ −0.04) | ✓ |

**A verificador no és el millor fins ara:** el pas següent es fa a sobre d'A xarxes.

## A verificador contra A xarxes, decodificador de toc, només els partits de dfl

| escenari | A xarxes, decodificador de toc | A verificador | diferència | interval del 95 % | A verificador guanya |
|---|---|---|---|---|---|
| net | 0.766 | 0.766 | +0.000 | -0.001 a +0.002 | 4 de 7 |
| curts ×¼ | 0.642 | 0.642 | +0.000 | -0.001 a +0.002 | 4 de 7 |
| llargs ×¼ | 0.621 | 0.621 | +0.000 | -0.001 a +0.002 | 2 de 7 |
| barreja ×¼ | 0.630 | 0.631 | +0.001 | -0.002 a +0.003 | 5 de 7 |
| aire ×¼ | 0.544 | 0.545 | +0.000 | -0.001 a +0.002 | 3 de 7 |
| curts | 0.607 | 0.607 | +0.000 | -0.001 a +0.001 | 2 de 7 |
| llargs | 0.564 | 0.564 | -0.000 | -0.002 a +0.001 | 2 de 7 |
| barreja | 0.571 | 0.569 | -0.002 | -0.003 a +0.000 | 1 de 7 |
| aire | 0.501 | 0.503 | +0.002 | +0.000 a +0.004 | 4 de 7 |
| soroll2 | 0.433 | 0.433 | +0.000 | -0.001 a +0.001 | 3 de 7 |
| partit ×¼ | 0.717 | 0.717 | +0.000 | -0.002 a +0.002 | 2 de 7 |

## A verificador contra A xarxes, decodificador de toc, només els partits de metrica

| escenari | A xarxes, decodificador de toc | A verificador | diferència | interval del 95 % | A verificador guanya |
|---|---|---|---|---|---|
| net | 0.874 | 0.874 | +0.001 | -0.003 a +0.004 | 1 de 3 |
| curts ×¼ | 0.747 | 0.746 | -0.000 | -0.002 a +0.002 | 1 de 3 |
| llargs ×¼ | 0.723 | 0.725 | +0.002 | +0.000 a +0.003 | 2 de 3 |
| barreja ×¼ | 0.730 | 0.732 | +0.002 | +0.000 a +0.004 | 2 de 3 |
| aire ×¼ | 0.731 | 0.732 | +0.001 | -0.001 a +0.003 | 1 de 3 |
| curts | 0.702 | 0.703 | +0.000 | +0.000 a +0.001 | 2 de 3 |
| llargs | 0.682 | 0.682 | -0.000 | -0.001 a +0.001 | 1 de 3 |
| barreja | 0.684 | 0.686 | +0.002 | +0.000 a +0.005 | 2 de 3 |
| aire | 0.679 | 0.680 | +0.001 | +0.000 a +0.002 | 2 de 3 |
| soroll2 | 0.557 | 0.559 | +0.002 | +0.000 a +0.005 | 2 de 3 |
| partit ×¼ | 0.813 | 0.814 | +0.002 | +0.000 a +0.003 | 2 de 3 |

## El verificador

Les possessions d'A xarxes dins de la veritat, als deu partits. *Inventada:* la veritat de toc no hi
té el seu equip a 1 s o menys. *encerta:* de les que arregla, la part que són inventades; *troba:* de les
inventades, la part que arregla. *inserida:* entre dues de l'altre equip; *al costat d'una aturada:*
tocant una aturada o la vora del tram.

| escenari | n possessions | n inventades | AUC | n arreglades | encerta | troba | n arreglades · inserida | encerta · inserida | n arreglades · al costat d'una aturada | encerta · al costat d'una aturada |
|---|---|---|---|---|---|---|---|---|---|---|
| net | 3798 | 154 | 0.920 | 35 | 0.600 | 0.136 | 5 | 0.000 | 30 | 0.700 |
| curts ×¼ | 3432 | 200 | 0.923 | 24 | 0.500 | 0.060 | 1 | 1.000 | 23 | 0.478 |
| llargs ×¼ | 3326 | 184 | 0.916 | 24 | 0.500 | 0.065 | 1 | 0.000 | 23 | 0.522 |
| barreja ×¼ | 3329 | 173 | 0.913 | 27 | 0.519 | 0.081 | 4 | 0.500 | 23 | 0.522 |
| aire ×¼ | 3229 | 191 | 0.891 | 33 | 0.545 | 0.094 | 8 | 0.500 | 25 | 0.560 |
| partit ×¼ | 3700 | 182 | 0.919 | 31 | 0.484 | 0.082 | 4 | 0.250 | 27 | 0.519 |
| curts | 3387 | 233 | 0.910 | 36 | 0.472 | 0.073 | 3 | 0.667 | 33 | 0.455 |
| llargs | 3195 | 218 | 0.899 | 32 | 0.438 | 0.064 | 4 | 0.250 | 28 | 0.464 |
| barreja | 3210 | 219 | 0.906 | 36 | 0.556 | 0.091 | 5 | 0.200 | 31 | 0.613 |
| aire | 3107 | 224 | 0.893 | 37 | 0.459 | 0.076 | 7 | 0.571 | 30 | 0.433 |
| soroll2 | 3909 | 719 | 0.838 | 26 | 0.615 | 0.022 | 13 | 0.615 | 13 | 0.615 |

## Els canvis d'equip falsos

Els canvis d'equip de cada mètode, i la part sense cap canvi de la veritat a 25 imatges (1 s) o
menys.

| escenari | n canvis · A xarxes, decodificador de toc | falsos · A xarxes, decodificador de toc | n canvis · A verificador | falsos · A verificador |
|---|---|---|---|---|
| net | 3490 | 0.170 | 3462 | 0.164 |
| curts ×¼ | 3088 | 0.281 | 3068 | 0.278 |
| llargs ×¼ | 2967 | 0.296 | 2948 | 0.292 |
| barreja ×¼ | 2977 | 0.290 | 2950 | 0.286 |
| aire ×¼ | 2819 | 0.337 | 2780 | 0.332 |
| partit ×¼ | 3392 | 0.216 | 3357 | 0.212 |
| curts | 3009 | 0.324 | 2970 | 0.322 |
| llargs | 2800 | 0.353 | 2770 | 0.351 |
| barreja | 2817 | 0.344 | 2773 | 0.337 |
| aire | 2663 | 0.384 | 2623 | 0.379 |
| soroll2 | 3536 | 0.529 | 3506 | 0.525 |

## L'spellF1 de cada mètode (mitjana dels deu partits)

| escenari | A xarxes, decodificador de toc | A verificador |
|---|---|---|
| net | 0.798 | 0.799 |
| curts ×¼ | 0.673 | 0.674 |
| llargs ×¼ | 0.651 | 0.652 |
| barreja ×¼ | 0.660 | 0.661 |
| aire ×¼ | 0.600 | 0.601 |
| curts | 0.636 | 0.636 |
| llargs | 0.599 | 0.599 |
| barreja | 0.605 | 0.604 |
| aire | 0.554 | 0.556 |
| soroll2 | 0.470 | 0.471 |
| partit ×¼ | 0.746 | 0.746 |

## Els llindars triats

0.7 (1 partits); 0.6 (3 partits); 0.5 (3 partits); mai (2 partits); 0.8 (1 partits).
