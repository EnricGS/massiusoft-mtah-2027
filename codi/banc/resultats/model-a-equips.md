# Banc obert · Les xarxes veuen els dos equips sencers (T3v)

Generat amb `uv run python -I -m banc.model_a_equips`. Dades obertes: 7 partits de DFL (IDSSE, CC BY
4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3v», i la capçalera de `banc/model_a_equips.py`. Es puntua a la veritat
de toc.

**A xarxes** i **A sense pilota** són els de la T3t, amb les peces de la memòria cau (✓ comprovat: a cada
punt de la graella donen l'spellF1 del banc de la T3t). **A equips sencers** és A sense pilota, amb les cinc
xarxes que també veuen tots els jugadors dels dos equips.

## A equips sencers contra A xarxes, decodificador de toc (spellF1): el criteri

| escenari | A xarxes, decodificador de toc | A equips sencers | diferència | interval del 95 % | A equips sencers guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.798 | 0.799 | +0.001 | -0.004 a +0.007 | 5 de 10 | no perd | ✓ |
| curts ×¼ | 0.673 | 0.699 | +0.026 | +0.021 a +0.032 | 10 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.651 | 0.688 | +0.037 | +0.028 a +0.046 | 10 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.660 | 0.696 | +0.036 | +0.030 a +0.043 | 10 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.600 | 0.629 | +0.029 | +0.023 a +0.035 | 10 de 10 | guanya clarament | ✗ |
| curts | 0.636 | 0.665 | +0.029 | +0.023 a +0.035 | 10 de 10 | no perd | ✓ |
| llargs | 0.599 | 0.640 | +0.041 | +0.028 a +0.055 | 10 de 10 | no perd | ✓ |
| barreja | 0.605 | 0.646 | +0.041 | +0.030 a +0.052 | 10 de 10 | no perd | ✓ |
| aire | 0.554 | 0.600 | +0.045 | +0.040 a +0.050 | 10 de 10 | no perd | ✓ |
| soroll2 | 0.470 | 0.534 | +0.064 | +0.056 a +0.072 | 10 de 10 | no perd | ✓ |
| partit ×¼ | 0.746 | 0.761 | +0.015 | +0.009 a +0.022 | 8 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1, el soroll2 i «partit ×¼» | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## A equips sencers contra A sense pilota (spellF1)

| escenari | A sense pilota | A equips sencers | diferència | interval del 95 % | A equips sencers guanya |
|---|---|---|---|---|---|
| net | 0.799 | 0.799 | +0.001 | -0.005 a +0.007 | 4 de 10 |
| curts ×¼ | 0.692 | 0.699 | +0.007 | +0.004 a +0.010 | 9 de 10 |
| llargs ×¼ | 0.665 | 0.688 | +0.023 | +0.017 a +0.029 | 10 de 10 |
| barreja ×¼ | 0.677 | 0.696 | +0.020 | +0.015 a +0.025 | 10 de 10 |
| aire ×¼ | 0.623 | 0.629 | +0.006 | +0.000 a +0.013 | 8 de 10 |
| curts | 0.653 | 0.665 | +0.012 | +0.006 a +0.017 | 9 de 10 |
| llargs | 0.614 | 0.640 | +0.026 | +0.017 a +0.036 | 9 de 10 |
| barreja | 0.627 | 0.646 | +0.019 | +0.013 a +0.025 | 8 de 10 |
| aire | 0.582 | 0.600 | +0.017 | +0.009 a +0.026 | 8 de 10 |
| soroll2 | 0.508 | 0.534 | +0.026 | +0.019 a +0.034 | 9 de 10 |
| partit ×¼ | 0.755 | 0.761 | +0.006 | +0.001 a +0.012 | 6 de 10 |

## No passa: és el millor fins ara?

| | És el millor fins ara si | |
|---|---|---|
| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | ✓ |
| «partit ×¼» | la diferència no és negativa | ✓ |
| El net, els ×1 i el soroll2 | no perd (diferència ≥ −0.04) | ✓ |

**A equips sencers és el millor fins ara:** el pas següent es fa a sobre d'A equips sencers.

## A equips sencers contra A xarxes, decodificador de toc, només els partits de dfl

| escenari | A xarxes, decodificador de toc | A equips sencers | diferència | interval del 95 % | A equips sencers guanya |
|---|---|---|---|---|---|
| net | 0.766 | 0.768 | +0.002 | -0.004 a +0.009 | 4 de 7 |
| curts ×¼ | 0.642 | 0.669 | +0.027 | +0.022 a +0.035 | 7 de 7 |
| llargs ×¼ | 0.621 | 0.656 | +0.035 | +0.025 a +0.045 | 7 de 7 |
| barreja ×¼ | 0.630 | 0.664 | +0.034 | +0.027 a +0.040 | 7 de 7 |
| aire ×¼ | 0.544 | 0.571 | +0.027 | +0.022 a +0.032 | 7 de 7 |
| curts | 0.607 | 0.637 | +0.030 | +0.023 a +0.038 | 7 de 7 |
| llargs | 0.564 | 0.602 | +0.038 | +0.019 a +0.058 | 7 de 7 |
| barreja | 0.571 | 0.608 | +0.037 | +0.028 a +0.047 | 7 de 7 |
| aire | 0.501 | 0.546 | +0.045 | +0.039 a +0.052 | 7 de 7 |
| soroll2 | 0.433 | 0.491 | +0.058 | +0.050 a +0.066 | 7 de 7 |
| partit ×¼ | 0.717 | 0.729 | +0.012 | +0.004 a +0.021 | 5 de 7 |

## A equips sencers contra A sense pilota, només els partits de dfl

| escenari | A sense pilota | A equips sencers | diferència | interval del 95 % | A equips sencers guanya |
|---|---|---|---|---|---|
| net | 0.768 | 0.768 | -0.000 | -0.007 a +0.009 | 3 de 7 |
| curts ×¼ | 0.665 | 0.669 | +0.004 | -0.001 a +0.009 | 6 de 7 |
| llargs ×¼ | 0.636 | 0.656 | +0.020 | +0.014 a +0.025 | 7 de 7 |
| barreja ×¼ | 0.648 | 0.664 | +0.016 | +0.010 a +0.022 | 7 de 7 |
| aire ×¼ | 0.567 | 0.571 | +0.004 | -0.004 a +0.012 | 5 de 7 |
| curts | 0.625 | 0.637 | +0.013 | +0.005 a +0.020 | 6 de 7 |
| llargs | 0.582 | 0.602 | +0.020 | +0.008 a +0.034 | 6 de 7 |
| barreja | 0.597 | 0.608 | +0.011 | +0.003 a +0.019 | 5 de 7 |
| aire | 0.533 | 0.546 | +0.013 | +0.002 a +0.025 | 5 de 7 |
| soroll2 | 0.475 | 0.491 | +0.017 | +0.008 a +0.026 | 6 de 7 |
| partit ×¼ | 0.728 | 0.729 | +0.001 | -0.005 a +0.008 | 3 de 7 |

## A equips sencers contra A xarxes, decodificador de toc, només els partits de metrica

| escenari | A xarxes, decodificador de toc | A equips sencers | diferència | interval del 95 % | A equips sencers guanya |
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

## A equips sencers contra A sense pilota, només els partits de metrica

| escenari | A sense pilota | A equips sencers | diferència | interval del 95 % | A equips sencers guanya |
|---|---|---|---|---|---|
| net | 0.871 | 0.873 | +0.002 | -0.004 a +0.011 | 1 de 3 |
| curts ×¼ | 0.755 | 0.769 | +0.014 | +0.013 a +0.015 | 3 de 3 |
| llargs ×¼ | 0.733 | 0.763 | +0.030 | +0.015 a +0.051 | 3 de 3 |
| barreja ×¼ | 0.745 | 0.773 | +0.028 | +0.019 a +0.038 | 3 de 3 |
| aire ×¼ | 0.754 | 0.765 | +0.011 | +0.005 a +0.023 | 3 de 3 |
| curts | 0.719 | 0.729 | +0.009 | +0.004 a +0.015 | 3 de 3 |
| llargs | 0.691 | 0.730 | +0.039 | +0.030 a +0.045 | 3 de 3 |
| barreja | 0.698 | 0.736 | +0.038 | +0.030 a +0.046 | 3 de 3 |
| aire | 0.697 | 0.724 | +0.027 | +0.018 a +0.039 | 3 de 3 |
| soroll2 | 0.585 | 0.634 | +0.049 | +0.033 a +0.060 | 3 de 3 |
| partit ×¼ | 0.817 | 0.835 | +0.018 | +0.013 a +0.027 | 3 de 3 |

## On s'encerta l'equip

On la veritat de toc és d'un equip, la part de les imatges on l'equip més probable és el bo (les
xarxes, amb les seves probabilitats; el segon, amb la relativa). Un forat és un tros sense pilota a
l'escenari, amb 6 imatges més a cada banda; per durada, la del tros sense pilota. Als forats,
també segons si la possessió de la veritat es veu algun cop amb pilota o mai.

| escenari | on | n imatges | les xarxes d'A sense pilota | les xarxes noves | el segon d'A sense pilota | el segon nou |
|---|---|---|---|---|---|---|
| net | on es veu la pilota | 810813 | 0.916 | 0.919 | 0.948 | 0.947 |
| net | als forats | 7083 | 0.775 | 0.777 | 0.846 | 0.842 |
| net | forats de menys de 2 s | 3303 | 0.647 | 0.642 | 0.761 | 0.748 |
| net | forats de 2 a 5 s | 801 | 0.869 | 0.905 | 0.916 | 0.918 |
| net | forats de 5 s o més | 2979 | 0.892 | 0.891 | 0.922 | 0.927 |
| net | als forats, possessions que no es veuen mai | 0 | nan | nan | nan | nan |
| net | als forats, possessions que es veuen algun cop | 7083 | 0.775 | 0.777 | 0.846 | 0.842 |
| curts ×¼ | on es veu la pilota | 391354 | 0.926 | 0.930 | 0.946 | 0.946 |
| curts ×¼ | als forats | 426542 | 0.873 | 0.886 | 0.891 | 0.897 |
| curts ×¼ | forats de menys de 2 s | 173310 | 0.903 | 0.908 | 0.916 | 0.917 |
| curts ×¼ | forats de 2 a 5 s | 210141 | 0.863 | 0.881 | 0.883 | 0.892 |
| curts ×¼ | forats de 5 s o més | 43091 | 0.800 | 0.820 | 0.833 | 0.839 |
| curts ×¼ | als forats, possessions que no es veuen mai | 16209 | 0.567 | 0.579 | 0.620 | 0.649 |
| curts ×¼ | als forats, possessions que es veuen algun cop | 410333 | 0.885 | 0.898 | 0.902 | 0.907 |
| llargs ×¼ | on es veu la pilota | 466858 | 0.919 | 0.925 | 0.945 | 0.945 |
| llargs ×¼ | als forats | 351038 | 0.806 | 0.863 | 0.867 | 0.882 |
| llargs ×¼ | forats de menys de 2 s | 1897 | 0.642 | 0.657 | 0.724 | 0.722 |
| llargs ×¼ | forats de 2 a 5 s | 19060 | 0.888 | 0.908 | 0.910 | 0.918 |
| llargs ×¼ | forats de 5 s o més | 330081 | 0.803 | 0.861 | 0.865 | 0.881 |
| llargs ×¼ | als forats, possessions que no es veuen mai | 98440 | 0.682 | 0.753 | 0.747 | 0.778 |
| llargs ×¼ | als forats, possessions que es veuen algun cop | 252598 | 0.855 | 0.906 | 0.913 | 0.922 |
| barreja ×¼ | on es veu la pilota | 444753 | 0.919 | 0.925 | 0.945 | 0.946 |
| barreja ×¼ | als forats | 373143 | 0.838 | 0.869 | 0.874 | 0.885 |
| barreja ×¼ | forats de menys de 2 s | 50188 | 0.894 | 0.892 | 0.907 | 0.913 |
| barreja ×¼ | forats de 2 a 5 s | 56275 | 0.872 | 0.888 | 0.894 | 0.898 |
| barreja ×¼ | forats de 5 s o més | 266680 | 0.820 | 0.861 | 0.864 | 0.877 |
| barreja ×¼ | als forats, possessions que no es veuen mai | 75958 | 0.711 | 0.751 | 0.746 | 0.770 |
| barreja ×¼ | als forats, possessions que es veuen algun cop | 297185 | 0.870 | 0.900 | 0.907 | 0.914 |
| aire ×¼ | on es veu la pilota | 445789 | 0.898 | 0.909 | 0.927 | 0.929 |
| aire ×¼ | als forats | 372107 | 0.814 | 0.852 | 0.865 | 0.874 |
| aire ×¼ | forats de menys de 2 s | 48141 | 0.845 | 0.862 | 0.877 | 0.882 |
| aire ×¼ | forats de 2 a 5 s | 52628 | 0.852 | 0.866 | 0.872 | 0.875 |
| aire ×¼ | forats de 5 s o més | 271338 | 0.800 | 0.847 | 0.862 | 0.872 |
| aire ×¼ | als forats, possessions que no es veuen mai | 71623 | 0.654 | 0.700 | 0.706 | 0.729 |
| aire ×¼ | als forats, possessions que es veuen algun cop | 300484 | 0.851 | 0.888 | 0.903 | 0.908 |
| partit ×¼ | on es veu la pilota | 722620 | 0.911 | 0.918 | 0.940 | 0.940 |
| partit ×¼ | als forats | 95276 | 0.846 | 0.877 | 0.888 | 0.898 |
| partit ×¼ | forats de menys de 2 s | 3168 | 0.653 | 0.664 | 0.758 | 0.759 |
| partit ×¼ | forats de 2 a 5 s | 6891 | 0.899 | 0.926 | 0.922 | 0.914 |
| partit ×¼ | forats de 5 s o més | 85217 | 0.849 | 0.881 | 0.891 | 0.902 |
| partit ×¼ | als forats, possessions que no es veuen mai | 14713 | 0.680 | 0.711 | 0.684 | 0.719 |
| partit ×¼ | als forats, possessions que es veuen algun cop | 80563 | 0.876 | 0.907 | 0.926 | 0.931 |
| curts | on es veu la pilota | 391354 | 0.918 | 0.925 | 0.934 | 0.936 |
| llargs | on es veu la pilota | 466858 | 0.911 | 0.919 | 0.926 | 0.928 |
| barreja | on es veu la pilota | 444753 | 0.912 | 0.920 | 0.927 | 0.931 |
| aire | on es veu la pilota | 445789 | 0.890 | 0.905 | 0.913 | 0.920 |
| soroll2 | on es veu la pilota | 444190 | 0.886 | 0.902 | 0.900 | 0.906 |
| curts | als forats | 426542 | 0.866 | 0.880 | 0.882 | 0.889 |
| llargs | als forats | 351038 | 0.798 | 0.853 | 0.862 | 0.878 |
| barreja | als forats | 373143 | 0.828 | 0.861 | 0.870 | 0.878 |
| aire | als forats | 372107 | 0.805 | 0.844 | 0.860 | 0.870 |
| soroll2 | als forats | 373706 | 0.799 | 0.841 | 0.857 | 0.873 |
| curts | forats de menys de 2 s | 173310 | 0.896 | 0.902 | 0.906 | 0.908 |
| llargs | forats de menys de 2 s | 1897 | 0.634 | 0.661 | 0.637 | 0.653 |
| barreja | forats de menys de 2 s | 50188 | 0.888 | 0.890 | 0.896 | 0.899 |
| aire | forats de menys de 2 s | 48141 | 0.836 | 0.856 | 0.867 | 0.875 |
| soroll2 | forats de menys de 2 s | 50894 | 0.860 | 0.873 | 0.873 | 0.880 |
| curts | forats de 2 a 5 s | 210141 | 0.855 | 0.875 | 0.875 | 0.885 |
| llargs | forats de 2 a 5 s | 19060 | 0.883 | 0.900 | 0.906 | 0.913 |
| barreja | forats de 2 a 5 s | 56275 | 0.863 | 0.882 | 0.886 | 0.889 |
| aire | forats de 2 a 5 s | 52628 | 0.844 | 0.858 | 0.864 | 0.869 |
| soroll2 | forats de 2 a 5 s | 59772 | 0.841 | 0.867 | 0.868 | 0.878 |
| curts | forats de 5 s o més | 43091 | 0.794 | 0.812 | 0.821 | 0.831 |
| llargs | forats de 5 s o més | 330081 | 0.794 | 0.851 | 0.861 | 0.877 |
| barreja | forats de 5 s o més | 266680 | 0.810 | 0.852 | 0.861 | 0.872 |
| aire | forats de 5 s o més | 271338 | 0.792 | 0.839 | 0.858 | 0.870 |
| soroll2 | forats de 5 s o més | 263040 | 0.778 | 0.829 | 0.851 | 0.870 |
| curts | als forats, possessions que no es veuen mai | 16209 | 0.570 | 0.578 | 0.633 | 0.654 |
| llargs | als forats, possessions que no es veuen mai | 98440 | 0.673 | 0.738 | 0.746 | 0.777 |
| barreja | als forats, possessions que no es veuen mai | 75958 | 0.697 | 0.734 | 0.749 | 0.769 |
| aire | als forats, possessions que no es veuen mai | 71623 | 0.649 | 0.693 | 0.711 | 0.731 |
| soroll2 | als forats, possessions que no es veuen mai | 72576 | 0.648 | 0.702 | 0.722 | 0.761 |
| curts | als forats, possessions que es veuen algun cop | 410333 | 0.877 | 0.891 | 0.892 | 0.898 |
| llargs | als forats, possessions que es veuen algun cop | 252598 | 0.847 | 0.897 | 0.908 | 0.917 |
| barreja | als forats, possessions que es veuen algun cop | 297185 | 0.862 | 0.894 | 0.900 | 0.906 |
| aire | als forats, possessions que es veuen algun cop | 300484 | 0.842 | 0.880 | 0.896 | 0.903 |
| soroll2 | als forats, possessions que es veuen algun cop | 301130 | 0.836 | 0.874 | 0.889 | 0.900 |

## L'spellF1 de cada mètode (mitjana dels deu partits)

**spellF1 a la veritat de toc**

| escenari | A xarxes | A xarxes, decodificador de toc | A sense pilota | A equips sencers |
|---|---|---|---|---|
| net | 0.799 | 0.798 | 0.799 | 0.799 |
| curts ×¼ | 0.674 | 0.673 | 0.692 | 0.699 |
| llargs ×¼ | 0.652 | 0.651 | 0.665 | 0.688 |
| barreja ×¼ | 0.660 | 0.660 | 0.677 | 0.696 |
| aire ×¼ | 0.600 | 0.600 | 0.623 | 0.629 |
| curts | 0.636 | 0.636 | 0.653 | 0.665 |
| llargs | 0.599 | 0.599 | 0.614 | 0.640 |
| barreja | 0.605 | 0.605 | 0.627 | 0.646 |
| aire | 0.555 | 0.554 | 0.582 | 0.600 |
| soroll2 | 0.471 | 0.470 | 0.508 | 0.534 |
| partit ×¼ | 0.746 | 0.746 | 0.755 | 0.761 |

**spellF1 a la veritat de sempre**

| escenari | A xarxes | A xarxes, decodificador de toc | A sense pilota | A equips sencers |
|---|---|---|---|---|
| net | 0.808 | 0.808 | 0.810 | 0.810 |
| curts ×¼ | 0.684 | 0.684 | 0.700 | 0.708 |
| llargs ×¼ | 0.662 | 0.662 | 0.675 | 0.700 |
| barreja ×¼ | 0.671 | 0.671 | 0.688 | 0.708 |
| aire ×¼ | 0.612 | 0.612 | 0.635 | 0.643 |
| curts | 0.644 | 0.644 | 0.661 | 0.674 |
| llargs | 0.607 | 0.607 | 0.622 | 0.648 |
| barreja | 0.616 | 0.616 | 0.639 | 0.656 |
| aire | 0.564 | 0.564 | 0.593 | 0.613 |
| soroll2 | 0.478 | 0.478 | 0.515 | 0.543 |
| partit ×¼ | 0.757 | 0.757 | 0.766 | 0.772 |

## Els decodificadors triats

- **A xarxes:** w = 4, λ = 64, durada mínima 12 (1 partits); w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 32, durada mínima 1 (1 partits)
- **A xarxes, decodificador de toc:** w = 4, λ = 64, durada mínima 1 (1 partits); w = 4, λ = 32, durada mínima 12 (6 partits); w = 4, λ = 32, durada mínima 1 (3 partits)
- **A sense pilota:** w = 4, λ = 32, durada mínima 12 (9 partits); w = 4, λ = 16, durada mínima 12 (1 partits)
- **A equips sencers:** w = 4, λ = 32, durada mínima 12 (8 partits); w = 4, λ = 16, durada mínima 12 (2 partits)
