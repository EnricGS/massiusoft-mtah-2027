# Banc obert · Els trets dels forats curts, al segon (T3y)

Generat amb `uv run python -I -m banc.model_forats_al_segon`. Dades obertes: 7 partits de DFL (IDSSE, CC
BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3y», i la capçalera de `banc/model_forats_al_segon.py`. Es puntua a la
veritat de toc.

**A xarxes, decodificador de toc** i **A equips sencers** són els de la T3v, amb les peces de la memòria cau (✓ comprovat: a
cada punt de la graella donen l'spellF1 del banc de la T3v; i, sense les columnes noves, la taula del
segon és la de la T3v). **A forats al segon** és A equips sencers, amb el segon que també veu els trets del forat
curt més proper.

## A forats al segon contra A xarxes, decodificador de toc (spellF1): el criteri

| escenari | A xarxes, decodificador de toc | A forats al segon | diferència | interval del 95 % | A forats al segon guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.798 | 0.797 | -0.001 | -0.006 a +0.005 | 4 de 10 | no perd | ✓ |
| curts ×¼ | 0.673 | 0.700 | +0.027 | +0.022 a +0.033 | 10 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.651 | 0.691 | +0.040 | +0.031 a +0.048 | 10 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.660 | 0.694 | +0.034 | +0.027 a +0.042 | 10 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.600 | 0.631 | +0.031 | +0.023 a +0.038 | 10 de 10 | guanya clarament | ✗ |
| curts | 0.636 | 0.665 | +0.029 | +0.023 a +0.036 | 10 de 10 | no perd | ✓ |
| llargs | 0.599 | 0.641 | +0.041 | +0.029 a +0.054 | 10 de 10 | no perd | ✓ |
| barreja | 0.605 | 0.643 | +0.038 | +0.027 a +0.048 | 10 de 10 | no perd | ✓ |
| aire | 0.554 | 0.601 | +0.046 | +0.040 a +0.053 | 10 de 10 | no perd | ✓ |
| soroll2 | 0.470 | 0.534 | +0.064 | +0.055 a +0.072 | 10 de 10 | no perd | ✓ |
| partit ×¼ | 0.746 | 0.760 | +0.014 | +0.005 a +0.022 | 8 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1, el soroll2 i «partit ×¼» | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## A forats al segon contra A equips sencers (spellF1)

| escenari | A equips sencers | A forats al segon | diferència | interval del 95 % | A forats al segon guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.797 | -0.002 | -0.005 a +0.001 | 5 de 10 |
| curts ×¼ | 0.699 | 0.700 | +0.001 | -0.001 a +0.004 | 5 de 10 |
| llargs ×¼ | 0.688 | 0.691 | +0.003 | -0.001 a +0.006 | 7 de 10 |
| barreja ×¼ | 0.696 | 0.694 | -0.002 | -0.007 a +0.003 | 4 de 10 |
| aire ×¼ | 0.629 | 0.631 | +0.002 | -0.001 a +0.006 | 6 de 10 |
| curts | 0.665 | 0.665 | +0.000 | -0.003 a +0.003 | 4 de 10 |
| llargs | 0.640 | 0.641 | +0.000 | -0.003 a +0.003 | 6 de 10 |
| barreja | 0.646 | 0.643 | -0.003 | -0.006 a +0.000 | 3 de 10 |
| aire | 0.600 | 0.601 | +0.001 | -0.002 a +0.004 | 6 de 10 |
| soroll2 | 0.534 | 0.534 | -0.000 | -0.004 a +0.004 | 6 de 10 |
| partit ×¼ | 0.761 | 0.760 | -0.001 | -0.005 a +0.002 | 5 de 10 |

## No passa: és el millor fins ara?

La regla dels passos que només van a un escenari (D-55), escrita abans, a curts ×¼, contra A equips sencers:

| | És el millor fins ara si | |
|---|---|---|
| curts ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | ✗ |
| Els altres tres ×¼ i «partit ×¼» | la diferència no és negativa | ✗ |
| El net, els ×1 i el soroll2 | no perd (diferència ≥ −0.04) | ✓ |

**A forats al segon no és el millor fins ara:** el pas següent es fa a sobre d'A equips sencers.

## A forats al segon contra A xarxes, decodificador de toc, només els partits de dfl

| escenari | A xarxes, decodificador de toc | A forats al segon | diferència | interval del 95 % | A forats al segon guanya |
|---|---|---|---|---|---|
| net | 0.766 | 0.766 | +0.000 | -0.005 a +0.006 | 3 de 7 |
| curts ×¼ | 0.642 | 0.669 | +0.027 | +0.020 a +0.036 | 7 de 7 |
| llargs ×¼ | 0.621 | 0.661 | +0.040 | +0.029 a +0.051 | 7 de 7 |
| barreja ×¼ | 0.630 | 0.663 | +0.033 | +0.023 a +0.042 | 7 de 7 |
| aire ×¼ | 0.544 | 0.574 | +0.030 | +0.022 a +0.037 | 7 de 7 |
| curts | 0.607 | 0.636 | +0.029 | +0.021 a +0.038 | 7 de 7 |
| llargs | 0.564 | 0.605 | +0.041 | +0.023 a +0.059 | 7 de 7 |
| barreja | 0.571 | 0.607 | +0.036 | +0.026 a +0.046 | 7 de 7 |
| aire | 0.501 | 0.546 | +0.045 | +0.037 a +0.054 | 7 de 7 |
| soroll2 | 0.433 | 0.490 | +0.057 | +0.048 a +0.064 | 7 de 7 |
| partit ×¼ | 0.717 | 0.730 | +0.013 | +0.002 a +0.023 | 5 de 7 |

## A forats al segon contra A equips sencers, només els partits de dfl

| escenari | A equips sencers | A forats al segon | diferència | interval del 95 % | A forats al segon guanya |
|---|---|---|---|---|---|
| net | 0.768 | 0.766 | -0.002 | -0.006 a +0.002 | 4 de 7 |
| curts ×¼ | 0.669 | 0.669 | +0.000 | -0.003 a +0.004 | 2 de 7 |
| llargs ×¼ | 0.656 | 0.661 | +0.005 | +0.001 a +0.008 | 6 de 7 |
| barreja ×¼ | 0.664 | 0.663 | -0.001 | -0.008 a +0.005 | 4 de 7 |
| aire ×¼ | 0.571 | 0.574 | +0.003 | -0.001 a +0.009 | 4 de 7 |
| curts | 0.637 | 0.636 | -0.001 | -0.004 a +0.002 | 2 de 7 |
| llargs | 0.602 | 0.605 | +0.003 | -0.000 a +0.006 | 5 de 7 |
| barreja | 0.608 | 0.607 | -0.001 | -0.004 a +0.003 | 3 de 7 |
| aire | 0.546 | 0.546 | +0.000 | -0.005 a +0.005 | 3 de 7 |
| soroll2 | 0.491 | 0.490 | -0.001 | -0.007 a +0.003 | 4 de 7 |
| partit ×¼ | 0.729 | 0.730 | +0.000 | -0.003 a +0.004 | 4 de 7 |

## A forats al segon contra A xarxes, decodificador de toc, només els partits de metrica

| escenari | A xarxes, decodificador de toc | A forats al segon | diferència | interval del 95 % | A forats al segon guanya |
|---|---|---|---|---|---|
| net | 0.874 | 0.870 | -0.004 | -0.014 a +0.012 | 1 de 3 |
| curts ×¼ | 0.747 | 0.773 | +0.026 | +0.022 a +0.033 | 3 de 3 |
| llargs ×¼ | 0.723 | 0.762 | +0.039 | +0.020 a +0.054 | 3 de 3 |
| barreja ×¼ | 0.730 | 0.769 | +0.039 | +0.029 a +0.052 | 3 de 3 |
| aire ×¼ | 0.731 | 0.765 | +0.034 | +0.011 a +0.051 | 3 de 3 |
| curts | 0.702 | 0.732 | +0.029 | +0.022 a +0.036 | 3 de 3 |
| llargs | 0.682 | 0.724 | +0.042 | +0.037 a +0.045 | 3 de 3 |
| barreja | 0.684 | 0.728 | +0.044 | +0.012 a +0.068 | 3 de 3 |
| aire | 0.679 | 0.727 | +0.048 | +0.041 a +0.057 | 3 de 3 |
| soroll2 | 0.557 | 0.637 | +0.080 | +0.058 a +0.101 | 3 de 3 |
| partit ×¼ | 0.813 | 0.829 | +0.017 | +0.002 a +0.033 | 3 de 3 |

## A forats al segon contra A equips sencers, només els partits de metrica

| escenari | A equips sencers | A forats al segon | diferència | interval del 95 % | A forats al segon guanya |
|---|---|---|---|---|---|
| net | 0.873 | 0.870 | -0.003 | -0.008 a +0.000 | 1 de 3 |
| curts ×¼ | 0.769 | 0.773 | +0.004 | +0.001 a +0.007 | 3 de 3 |
| llargs ×¼ | 0.763 | 0.762 | -0.001 | -0.007 a +0.008 | 1 de 3 |
| barreja ×¼ | 0.773 | 0.769 | -0.004 | -0.007 a -0.002 | 0 de 3 |
| aire ×¼ | 0.765 | 0.765 | -0.000 | -0.005 a +0.004 | 2 de 3 |
| curts | 0.729 | 0.732 | +0.003 | -0.004 a +0.010 | 2 de 3 |
| llargs | 0.730 | 0.724 | -0.006 | -0.012 a +0.001 | 1 de 3 |
| barreja | 0.736 | 0.728 | -0.008 | -0.012 a -0.004 | 0 de 3 |
| aire | 0.724 | 0.727 | +0.003 | +0.003 a +0.004 | 3 de 3 |
| soroll2 | 0.634 | 0.637 | +0.003 | -0.003 a +0.011 | 2 de 3 |
| partit ×¼ | 0.835 | 0.829 | -0.006 | -0.016 a +0.000 | 1 de 3 |

## Què hi fa la predicció als forats curts de curts ×¼

Als d'un canvi i als sense canvi amb les dues vores als trams vàlids, com a `canvis_als_forats.py`, amb
el decodificador triat de cada mètode a cada partit.

| tipus | fa | n A equips sencers | n A forats al segon |
|---|---|---|---|
| sense canvi | cap canvi | 5970 | 5979 |
| sense canvi | hi canvia d'equip (o ja hi arriba canviada) | 466 | 466 |
| sense canvi | hi fa una altra cosa | 1 | 1 |
| sense canvi | hi inventa una possessió de l'altre equip | 7 | 6 |
| sense canvi | hi posa la D | 44 | 36 |
| un canvi d'equip | es queda amb l'equip d'abans | 284 | 269 |
| un canvi d'equip | hi fa un sol canvi | 563 | 578 |
| un canvi d'equip | hi fa una altra cosa | 45 | 41 |
| un canvi d'equip | ja hi té l'equip nou | 168 | 172 |

## On encerta l'equip el segon

On la veritat de toc és d'un equip, la part de les imatges on l'equip més probable (amb la relativa) és
el bo. Als forats: els trossos sense pilota, amb 6 imatges més a cada banda. Als forats curts:
les imatges amb les columnes noves.

| escenari | on | n imatges | el segon d'A equips sencers | el segon nou |
|---|---|---|---|---|
| curts ×¼ | on es veu la pilota | 391354 | 0.946 | 0.946 |
| curts ×¼ | als forats | 426542 | 0.897 | 0.897 |
| curts ×¼ | als forats curts | 384429 | 0.903 | 0.903 |
| llargs ×¼ | on es veu la pilota | 466858 | 0.945 | 0.945 |
| llargs ×¼ | als forats | 351038 | 0.882 | 0.882 |
| llargs ×¼ | als forats curts | 21019 | 0.901 | 0.899 |
| barreja ×¼ | on es veu la pilota | 444753 | 0.946 | 0.946 |
| barreja ×¼ | als forats | 373143 | 0.885 | 0.885 |
| barreja ×¼ | als forats curts | 107057 | 0.905 | 0.904 |
| aire ×¼ | on es veu la pilota | 445789 | 0.929 | 0.929 |
| aire ×¼ | als forats | 372107 | 0.874 | 0.875 |
| aire ×¼ | als forats curts | 101499 | 0.878 | 0.878 |
| partit ×¼ | on es veu la pilota | 722620 | 0.940 | 0.940 |
| partit ×¼ | als forats | 95276 | 0.898 | 0.898 |
| partit ×¼ | als forats curts | 10074 | 0.866 | 0.863 |

## L'spellF1 de cada mètode (mitjana dels deu partits)

**spellF1 a la veritat de toc**

| escenari | A xarxes, decodificador de toc | A equips sencers | A forats al segon |
|---|---|---|---|
| net | 0.798 | 0.799 | 0.797 |
| curts ×¼ | 0.673 | 0.699 | 0.700 |
| llargs ×¼ | 0.651 | 0.688 | 0.691 |
| barreja ×¼ | 0.660 | 0.696 | 0.694 |
| aire ×¼ | 0.600 | 0.629 | 0.631 |
| curts | 0.636 | 0.665 | 0.665 |
| llargs | 0.599 | 0.640 | 0.641 |
| barreja | 0.605 | 0.646 | 0.643 |
| aire | 0.554 | 0.600 | 0.601 |
| soroll2 | 0.470 | 0.534 | 0.534 |
| partit ×¼ | 0.746 | 0.761 | 0.760 |

**spellF1 a la veritat de sempre**

| escenari | A xarxes, decodificador de toc | A equips sencers | A forats al segon |
|---|---|---|---|
| net | 0.808 | 0.810 | 0.808 |
| curts ×¼ | 0.684 | 0.708 | 0.709 |
| llargs ×¼ | 0.662 | 0.700 | 0.701 |
| barreja ×¼ | 0.671 | 0.708 | 0.706 |
| aire ×¼ | 0.612 | 0.643 | 0.645 |
| curts | 0.644 | 0.674 | 0.674 |
| llargs | 0.607 | 0.648 | 0.648 |
| barreja | 0.616 | 0.656 | 0.653 |
| aire | 0.564 | 0.613 | 0.613 |
| soroll2 | 0.478 | 0.543 | 0.542 |
| partit ×¼ | 0.757 | 0.772 | 0.771 |

## Els decodificadors triats

- **A xarxes, decodificador de toc:** w = 4, λ = 64, durada mínima 1 (1 partits); w = 4, λ = 32, durada mínima 12 (6 partits); w = 4, λ = 32, durada mínima 1 (3 partits)
- **A equips sencers:** w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 16, durada mínima 12 (2 partits)
- **A forats al segon:** w = 4, λ = 32, durada mínima 12 (5 partits); w = 4, λ = 16, durada mínima 12 (5 partits)
