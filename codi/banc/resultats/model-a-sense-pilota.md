# Banc obert · Les xarxes veuen els jugadors també sense pilota (T3t)

Generat amb `uv run python -I -m banc.model_a_sense_pilota`. Dades obertes: 7 partits de DFL (IDSSE,
CC BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3t», i la capçalera de `banc/model_a_sense_pilota.py`. Es puntua a la
veritat de toc.

**A xarxes** és el de la cadena, amb les peces de la memòria cau de la T3p (✓ comprovat: a cada punt de
la graella dona l'spellF1 del banc de la T3q). **A sense pilota** és el mateix, amb les cinc xarxes que
veuen una pilota estimada on no es veu la pilota.

## A sense pilota contra A xarxes, decodificador de toc (spellF1): el criteri

| escenari | A xarxes, decodificador de toc | A sense pilota | diferència | interval del 95 % | A sense pilota guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.798 | 0.799 | +0.001 | -0.006 a +0.008 | 5 de 10 | no perd | ✓ |
| curts ×¼ | 0.673 | 0.692 | +0.019 | +0.013 a +0.025 | 10 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.651 | 0.665 | +0.014 | +0.006 a +0.021 | 9 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.660 | 0.677 | +0.017 | +0.012 a +0.022 | 10 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.600 | 0.623 | +0.023 | +0.015 a +0.030 | 9 de 10 | guanya clarament | ✗ |
| curts | 0.636 | 0.653 | +0.017 | +0.010 a +0.023 | 9 de 10 | no perd | ✓ |
| llargs | 0.599 | 0.614 | +0.015 | +0.010 a +0.021 | 10 de 10 | no perd | ✓ |
| barreja | 0.605 | 0.627 | +0.022 | +0.011 a +0.033 | 9 de 10 | no perd | ✓ |
| aire | 0.554 | 0.582 | +0.028 | +0.018 a +0.037 | 9 de 10 | no perd | ✓ |
| soroll2 | 0.470 | 0.508 | +0.037 | +0.026 a +0.049 | 10 de 10 | no perd | ✓ |
| partit ×¼ | 0.746 | 0.755 | +0.009 | +0.003 a +0.016 | 9 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1, el soroll2 i «partit ×¼» | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## No passa: és el millor fins ara?

| | És el millor fins ara si | |
|---|---|---|
| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | ✓ |
| «partit ×¼» | la diferència no és negativa | ✓ |
| El net, els ×1 i el soroll2 | no perd (diferència ≥ −0.04) | ✓ |

**A sense pilota és el millor fins ara:** el pas següent es fa a sobre d'A sense pilota.

## A sense pilota contra A xarxes, decodificador de toc, només els partits de dfl

| escenari | A xarxes, decodificador de toc | A sense pilota | diferència | interval del 95 % | A sense pilota guanya |
|---|---|---|---|---|---|
| net | 0.766 | 0.768 | +0.002 | -0.006 a +0.011 | 4 de 7 |
| curts ×¼ | 0.642 | 0.665 | +0.023 | +0.016 a +0.032 | 7 de 7 |
| llargs ×¼ | 0.621 | 0.636 | +0.016 | +0.005 a +0.025 | 6 de 7 |
| barreja ×¼ | 0.630 | 0.648 | +0.018 | +0.010 a +0.024 | 7 de 7 |
| aire ×¼ | 0.544 | 0.567 | +0.023 | +0.014 a +0.030 | 6 de 7 |
| curts | 0.607 | 0.625 | +0.018 | +0.008 a +0.025 | 6 de 7 |
| llargs | 0.564 | 0.582 | +0.018 | +0.010 a +0.026 | 7 de 7 |
| barreja | 0.571 | 0.597 | +0.026 | +0.015 a +0.038 | 7 de 7 |
| aire | 0.501 | 0.533 | +0.032 | +0.021 a +0.045 | 7 de 7 |
| soroll2 | 0.433 | 0.475 | +0.041 | +0.026 a +0.056 | 7 de 7 |
| partit ×¼ | 0.717 | 0.728 | +0.011 | +0.005 a +0.018 | 7 de 7 |

## A sense pilota contra A xarxes, decodificador de toc, només els partits de metrica

| escenari | A xarxes, decodificador de toc | A sense pilota | diferència | interval del 95 % | A sense pilota guanya |
|---|---|---|---|---|---|
| net | 0.874 | 0.871 | -0.003 | -0.017 a +0.012 | 1 de 3 |
| curts ×¼ | 0.747 | 0.755 | +0.009 | +0.001 a +0.016 | 3 de 3 |
| llargs ×¼ | 0.723 | 0.733 | +0.010 | +0.004 a +0.018 | 3 de 3 |
| barreja ×¼ | 0.730 | 0.745 | +0.015 | +0.010 a +0.021 | 3 de 3 |
| aire ×¼ | 0.731 | 0.754 | +0.023 | +0.010 a +0.045 | 3 de 3 |
| curts | 0.702 | 0.719 | +0.017 | +0.009 a +0.026 | 3 de 3 |
| llargs | 0.682 | 0.691 | +0.008 | +0.007 a +0.011 | 3 de 3 |
| barreja | 0.684 | 0.698 | +0.014 | -0.013 a +0.037 | 2 de 3 |
| aire | 0.679 | 0.697 | +0.018 | -0.001 a +0.030 | 2 de 3 |
| soroll2 | 0.557 | 0.585 | +0.028 | +0.010 a +0.046 | 3 de 3 |
| partit ×¼ | 0.813 | 0.817 | +0.005 | -0.011 a +0.021 | 2 de 3 |

## On s'encerta l'equip

On la veritat de toc és d'un equip, la part de les imatges on l'equip més probable és el bo (les
xarxes, amb les seves probabilitats; el segon, amb la relativa) i on la predicció hi dona el bo. Un
forat és un tros sense pilota a l'escenari, amb 6 imatges més a cada banda; per durada, la del
tros sense pilota.

| escenari | on | n imatges | les xarxes d'ara | les xarxes noves | el segon d'ara | el segon nou | A xarxes, decodificador de toc | A sense pilota |
|---|---|---|---|---|---|---|---|---|
| net | on es veu la pilota | 810813 | 0.914 | 0.916 | 0.946 | 0.948 | 0.947 | 0.947 |
| net | als forats | 7083 | 0.761 | 0.775 | 0.845 | 0.846 | 0.819 | 0.817 |
| net | forats de menys de 2 s | 3303 | 0.647 | 0.647 | 0.757 | 0.761 | 0.768 | 0.770 |
| net | forats de 2 a 5 s | 801 | 0.865 | 0.869 | 0.919 | 0.916 | 0.898 | 0.899 |
| net | forats de 5 s o més | 2979 | 0.858 | 0.892 | 0.922 | 0.922 | 0.855 | 0.848 |
| curts ×¼ | on es veu la pilota | 391354 | 0.921 | 0.926 | 0.944 | 0.946 | 0.941 | 0.945 |
| curts ×¼ | als forats | 426542 | 0.835 | 0.873 | 0.886 | 0.891 | 0.877 | 0.884 |
| curts ×¼ | forats de menys de 2 s | 173310 | 0.885 | 0.903 | 0.911 | 0.916 | 0.910 | 0.914 |
| curts ×¼ | forats de 2 a 5 s | 210141 | 0.824 | 0.863 | 0.878 | 0.883 | 0.868 | 0.876 |
| curts ×¼ | forats de 5 s o més | 43091 | 0.684 | 0.800 | 0.823 | 0.833 | 0.785 | 0.800 |
| llargs ×¼ | on es veu la pilota | 466858 | 0.919 | 0.919 | 0.944 | 0.945 | 0.945 | 0.944 |
| llargs ×¼ | als forats | 351038 | 0.634 | 0.806 | 0.855 | 0.867 | 0.823 | 0.838 |
| llargs ×¼ | forats de menys de 2 s | 1897 | 0.657 | 0.642 | 0.744 | 0.724 | 0.754 | 0.763 |
| llargs ×¼ | forats de 2 a 5 s | 19060 | 0.825 | 0.888 | 0.895 | 0.910 | 0.888 | 0.897 |
| llargs ×¼ | forats de 5 s o més | 330081 | 0.622 | 0.803 | 0.854 | 0.865 | 0.820 | 0.835 |
| barreja ×¼ | on es veu la pilota | 444753 | 0.916 | 0.919 | 0.944 | 0.945 | 0.944 | 0.945 |
| barreja ×¼ | als forats | 373143 | 0.694 | 0.838 | 0.865 | 0.874 | 0.836 | 0.852 |
| barreja ×¼ | forats de menys de 2 s | 50188 | 0.877 | 0.894 | 0.904 | 0.907 | 0.898 | 0.906 |
| barreja ×¼ | forats de 2 a 5 s | 56275 | 0.823 | 0.872 | 0.888 | 0.894 | 0.880 | 0.888 |
| barreja ×¼ | forats de 5 s o més | 266680 | 0.632 | 0.820 | 0.852 | 0.864 | 0.815 | 0.834 |
| aire ×¼ | on es veu la pilota | 445789 | 0.893 | 0.898 | 0.925 | 0.927 | 0.921 | 0.925 |
| aire ×¼ | als forats | 372107 | 0.678 | 0.814 | 0.855 | 0.865 | 0.789 | 0.814 |
| aire ×¼ | forats de menys de 2 s | 48141 | 0.841 | 0.845 | 0.877 | 0.877 | 0.841 | 0.863 |
| aire ×¼ | forats de 2 a 5 s | 52628 | 0.806 | 0.852 | 0.865 | 0.872 | 0.814 | 0.845 |
| aire ×¼ | forats de 5 s o més | 271338 | 0.624 | 0.800 | 0.849 | 0.862 | 0.774 | 0.800 |
| partit ×¼ | on es veu la pilota | 722620 | 0.907 | 0.911 | 0.938 | 0.940 | 0.941 | 0.941 |
| partit ×¼ | als forats | 95276 | 0.677 | 0.846 | 0.867 | 0.888 | 0.834 | 0.862 |
| partit ×¼ | forats de menys de 2 s | 3168 | 0.652 | 0.653 | 0.750 | 0.758 | 0.765 | 0.757 |
| partit ×¼ | forats de 2 a 5 s | 6891 | 0.814 | 0.899 | 0.907 | 0.922 | 0.920 | 0.935 |
| partit ×¼ | forats de 5 s o més | 85217 | 0.667 | 0.849 | 0.869 | 0.891 | 0.830 | 0.860 |
| curts | on es veu la pilota | 391354 | 0.911 | 0.918 | 0.932 | 0.934 | 0.927 | 0.931 |
| llargs | on es veu la pilota | 466858 | 0.909 | 0.911 | 0.925 | 0.926 | 0.922 | 0.923 |
| barreja | on es veu la pilota | 444753 | 0.908 | 0.912 | 0.925 | 0.927 | 0.922 | 0.925 |
| aire | on es veu la pilota | 445789 | 0.885 | 0.890 | 0.911 | 0.913 | 0.900 | 0.907 |
| soroll2 | on es veu la pilota | 444190 | 0.881 | 0.886 | 0.897 | 0.900 | 0.899 | 0.900 |
| curts | als forats | 426542 | 0.821 | 0.866 | 0.875 | 0.882 | 0.864 | 0.873 |
| llargs | als forats | 351038 | 0.628 | 0.798 | 0.850 | 0.862 | 0.809 | 0.825 |
| barreja | als forats | 373143 | 0.686 | 0.828 | 0.856 | 0.870 | 0.822 | 0.843 |
| aire | als forats | 372107 | 0.671 | 0.805 | 0.849 | 0.860 | 0.759 | 0.789 |
| soroll2 | als forats | 373706 | 0.667 | 0.799 | 0.838 | 0.857 | 0.830 | 0.845 |
| curts | forats de menys de 2 s | 173310 | 0.873 | 0.896 | 0.897 | 0.906 | 0.892 | 0.902 |
| llargs | forats de menys de 2 s | 1897 | 0.635 | 0.634 | 0.649 | 0.637 | 0.688 | 0.649 |
| barreja | forats de menys de 2 s | 50188 | 0.868 | 0.888 | 0.888 | 0.896 | 0.886 | 0.898 |
| aire | forats de menys de 2 s | 48141 | 0.832 | 0.836 | 0.865 | 0.867 | 0.822 | 0.842 |
| soroll2 | forats de menys de 2 s | 50894 | 0.841 | 0.860 | 0.865 | 0.873 | 0.865 | 0.872 |
| curts | forats de 2 a 5 s | 210141 | 0.809 | 0.855 | 0.869 | 0.875 | 0.859 | 0.867 |
| llargs | forats de 2 a 5 s | 19060 | 0.811 | 0.883 | 0.888 | 0.906 | 0.882 | 0.892 |
| barreja | forats de 2 a 5 s | 56275 | 0.808 | 0.863 | 0.873 | 0.886 | 0.862 | 0.877 |
| aire | forats de 2 a 5 s | 52628 | 0.794 | 0.844 | 0.856 | 0.864 | 0.787 | 0.824 |
| soroll2 | forats de 2 a 5 s | 59772 | 0.783 | 0.841 | 0.855 | 0.868 | 0.855 | 0.867 |
| curts | forats de 5 s o més | 43091 | 0.675 | 0.794 | 0.815 | 0.821 | 0.777 | 0.784 |
| llargs | forats de 5 s o més | 330081 | 0.617 | 0.794 | 0.849 | 0.861 | 0.805 | 0.823 |
| barreja | forats de 5 s o més | 266680 | 0.626 | 0.810 | 0.846 | 0.861 | 0.802 | 0.826 |
| aire | forats de 5 s o més | 271338 | 0.619 | 0.792 | 0.845 | 0.858 | 0.743 | 0.773 |
| soroll2 | forats de 5 s o més | 263040 | 0.607 | 0.778 | 0.829 | 0.851 | 0.818 | 0.835 |

## Els canvis falsos que queden

Els canvis d'equip predits (deu partits), la part que són falsos (cap de real a 25 imatges o
menys, com a `canvis_falsos.py`) i, dels falsos, la part als forats.

| escenari | n canvis · A xarxes, decodificador de toc | n canvis · A sense pilota | falsos · A xarxes, decodificador de toc | falsos · A sense pilota | dels falsos, als forats · A xarxes, decodificador de toc | dels falsos, als forats · A sense pilota |
|---|---|---|---|---|---|---|
| net | 3490 | 3504 | 0.170 | 0.168 | 0.039 | 0.032 |
| curts ×¼ | 3088 | 3169 | 0.281 | 0.264 | 0.649 | 0.671 |
| llargs ×¼ | 2967 | 3079 | 0.296 | 0.296 | 0.580 | 0.582 |
| barreja ×¼ | 2977 | 3079 | 0.290 | 0.269 | 0.635 | 0.618 |
| aire ×¼ | 2819 | 2980 | 0.337 | 0.327 | 0.509 | 0.521 |
| partit ×¼ | 3392 | 3432 | 0.216 | 0.214 | 0.282 | 0.267 |
| curts | 3009 | 3082 | 0.324 | 0.309 | 0.648 | 0.642 |
| llargs | 2800 | 2881 | 0.353 | 0.352 | 0.532 | 0.527 |
| barreja | 2817 | 2998 | 0.344 | 0.332 | 0.563 | 0.579 |
| aire | 2663 | 2817 | 0.384 | 0.372 | 0.501 | 0.508 |
| soroll2 | 3536 | 3601 | 0.529 | 0.497 | 0.444 | 0.430 |

## L'spellF1 de cada mètode (mitjana dels deu partits)

**spellF1 a la veritat de toc**

| escenari | A xarxes | A xarxes, decodificador de toc | A sense pilota |
|---|---|---|---|
| net | 0.799 | 0.798 | 0.799 |
| curts ×¼ | 0.674 | 0.673 | 0.692 |
| llargs ×¼ | 0.652 | 0.651 | 0.665 |
| barreja ×¼ | 0.660 | 0.660 | 0.677 |
| aire ×¼ | 0.600 | 0.600 | 0.623 |
| curts | 0.636 | 0.636 | 0.653 |
| llargs | 0.599 | 0.599 | 0.614 |
| barreja | 0.605 | 0.605 | 0.627 |
| aire | 0.555 | 0.554 | 0.582 |
| soroll2 | 0.471 | 0.470 | 0.508 |
| partit ×¼ | 0.746 | 0.746 | 0.755 |

**spellF1 a la veritat de sempre**

| escenari | A xarxes | A xarxes, decodificador de toc | A sense pilota |
|---|---|---|---|
| net | 0.808 | 0.808 | 0.810 |
| curts ×¼ | 0.684 | 0.684 | 0.700 |
| llargs ×¼ | 0.662 | 0.662 | 0.675 |
| barreja ×¼ | 0.671 | 0.671 | 0.688 |
| aire ×¼ | 0.612 | 0.612 | 0.635 |
| curts | 0.644 | 0.644 | 0.661 |
| llargs | 0.607 | 0.607 | 0.622 |
| barreja | 0.616 | 0.616 | 0.639 |
| aire | 0.564 | 0.564 | 0.593 |
| soroll2 | 0.478 | 0.478 | 0.515 |
| partit ×¼ | 0.757 | 0.757 | 0.766 |

## Els decodificadors triats

- **A xarxes:** w = 4, λ = 64, durada mínima 12 (1 partits); w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 32, durada mínima 1 (1 partits)
- **A xarxes, decodificador de toc:** w = 4, λ = 64, durada mínima 1 (1 partits); w = 4, λ = 32, durada mínima 12 (6 partits); w = 4, λ = 32, durada mínima 1 (3 partits)
- **A sense pilota:** w = 4, λ = 32, durada mínima 12 (9 partits); w = 4, λ = 16, durada mínima 12 (1 partits)
