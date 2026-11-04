# Banc obert · Les fases de defensar a sobre d'A girat amb fases (T3an)

Generat amb `uv run python -I -m banc.model_girat_defenses`. Dades obertes: 7 partits de DFL (IDSSE, CC
BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3an», i la capçalera de `banc/model_girat_defenses.py`. Es puntua a la
veritat de toc.

**A girat amb fases** és el de la T3am, el de la cadena, refet aquí amb els punts que hi va triar cada partit (✓
comprovat: en dona les files). **A girat amb defenses** és A girat amb fases amb les fases de defensar simulades, girades, a
sobre, amb els mateixos paràmetres; no s'entrena ni es tria res. ✓ Comprovat: no dona mai la D a una
imatge netejada; amb `lligades` = 1, i sense fases, és exactament A girat amb fases.

## atac mitjà, defensar mitjà, lligades 0.5: A girat amb defenses contra A girat amb fases (spellF1), el criteri

| escenari | A girat amb fases | A girat amb defenses | diferència | interval del 95 % | A girat amb defenses guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.809 | 0.810 | +0.001 | -0.002 a +0.003 | 5 de 10 | no perd | ✓ |
| curts ×¼ | 0.718 | 0.718 | +0.001 | -0.002 a +0.004 | 6 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.714 | 0.719 | +0.006 | +0.003 a +0.008 | 9 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.718 | 0.720 | +0.002 | -0.002 a +0.005 | 7 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.676 | 0.676 | +0.000 | -0.003 a +0.003 | 5 de 10 | guanya clarament | ✗ |
| curts | 0.693 | 0.696 | +0.003 | +0.001 a +0.006 | 7 de 10 | no perd | ✓ |
| llargs | 0.674 | 0.674 | +0.000 | -0.002 a +0.003 | 6 de 10 | no perd | ✓ |
| barreja | 0.675 | 0.676 | +0.000 | -0.002 a +0.003 | 5 de 10 | no perd | ✓ |
| aire | 0.652 | 0.655 | +0.002 | -0.000 a +0.005 | 7 de 10 | no perd | ✓ |
| soroll2 | 0.600 | 0.599 | -0.001 | -0.003 a +0.001 | 4 de 10 | no perd | ✓ |
| partit ×¼ | 0.772 | 0.775 | +0.003 | +0.001 a +0.005 | 7 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1, el soroll2 i «partit ×¼» | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## atac mitjà, defensar dolent, lligades 0: la segona part del criteri

| curts ×¼ | llargs ×¼ | barreja ×¼ | aire ×¼ | partit ×¼ | No baixa de −0.005 |
|---|---|---|---|---|---|
| -0.0022 | -0.0017 | -0.0026 | -0.0035 | -0.0010 | ✓ |

**A girat amb defenses no passa el criteri sencer.**

## No passa: és el millor fins ara?

La regla de la D-50, escrita abans, contra A girat amb fases a atac mitjà, defensar mitjà, lligades 0.5, i la mateixa segona
part del criteri:

| | És el millor fins ara si | |
|---|---|---|
| Els quatre ×¼ | la diferència és positiva i l'interval del 95 % no toca el zero | ✗ |
| «partit ×¼» | la diferència no és negativa | ✓ |
| El net, els ×1 i el soroll2 | no perd (diferència ≥ −0.04) | ✓ |
| atac mitjà, defensar dolent, lligades 0 | la segona part del criteri | ✓ |

**A girat amb defenses no és el millor fins ara:** el pas següent es fa a sobre d'A girat amb fases.

## atac bo, defensar bo, lligades 0: A girat amb defenses contra A girat amb fases (spellF1)

| escenari | A girat amb fases | A girat amb defenses | diferència | interval del 95 % | A girat amb defenses guanya |
|---|---|---|---|---|---|
| net | 0.834 | 0.834 | +0.000 | -0.002 a +0.002 | 5 de 10 |
| curts ×¼ | 0.762 | 0.770 | +0.008 | +0.004 a +0.012 | 9 de 10 |
| llargs ×¼ | 0.766 | 0.774 | +0.008 | +0.004 a +0.011 | 8 de 10 |
| barreja ×¼ | 0.757 | 0.766 | +0.008 | +0.006 a +0.012 | 10 de 10 |
| aire ×¼ | 0.728 | 0.736 | +0.008 | +0.002 a +0.013 | 9 de 10 |
| curts | 0.751 | 0.754 | +0.004 | +0.001 a +0.007 | 7 de 10 |
| llargs | 0.726 | 0.736 | +0.010 | +0.006 a +0.016 | 10 de 10 |
| barreja | 0.732 | 0.742 | +0.010 | +0.008 a +0.013 | 9 de 10 |
| aire | 0.709 | 0.721 | +0.012 | +0.009 a +0.015 | 10 de 10 |
| soroll2 | 0.679 | 0.695 | +0.017 | +0.013 a +0.020 | 10 de 10 |
| partit ×¼ | 0.810 | 0.817 | +0.006 | +0.003 a +0.010 | 9 de 10 |

## atac bo, defensar bo, lligades 0.5: A girat amb defenses contra A girat amb fases (spellF1)

| escenari | A girat amb fases | A girat amb defenses | diferència | interval del 95 % | A girat amb defenses guanya |
|---|---|---|---|---|---|
| net | 0.834 | 0.834 | +0.000 | -0.001 a +0.002 | 4 de 10 |
| curts ×¼ | 0.762 | 0.766 | +0.004 | +0.000 a +0.007 | 8 de 10 |
| llargs ×¼ | 0.766 | 0.769 | +0.004 | +0.002 a +0.005 | 9 de 10 |
| barreja ×¼ | 0.757 | 0.762 | +0.005 | +0.003 a +0.007 | 9 de 10 |
| aire ×¼ | 0.728 | 0.733 | +0.004 | +0.002 a +0.007 | 9 de 10 |
| curts | 0.751 | 0.753 | +0.002 | -0.001 a +0.004 | 6 de 10 |
| llargs | 0.726 | 0.731 | +0.005 | +0.001 a +0.008 | 8 de 10 |
| barreja | 0.732 | 0.737 | +0.005 | +0.003 a +0.007 | 8 de 10 |
| aire | 0.709 | 0.716 | +0.007 | +0.005 a +0.009 | 10 de 10 |
| soroll2 | 0.679 | 0.685 | +0.006 | +0.003 a +0.010 | 9 de 10 |
| partit ×¼ | 0.810 | 0.815 | +0.004 | +0.001 a +0.008 | 9 de 10 |

## atac bo, defensar bo, lligades 1: A girat amb defenses contra A girat amb fases (spellF1)

| escenari | A girat amb fases | A girat amb defenses | diferència | interval del 95 % | A girat amb defenses guanya |
|---|---|---|---|---|---|
| net | 0.834 | 0.834 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| curts ×¼ | 0.762 | 0.762 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| llargs ×¼ | 0.766 | 0.766 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| barreja ×¼ | 0.757 | 0.757 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| aire ×¼ | 0.728 | 0.728 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| curts | 0.751 | 0.751 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| llargs | 0.726 | 0.726 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| barreja | 0.732 | 0.732 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| aire | 0.709 | 0.709 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| soroll2 | 0.679 | 0.679 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| partit ×¼ | 0.810 | 0.810 | +0.000 | +0.000 a +0.000 | 0 de 10 |

## atac mitjà, defensar mitjà, lligades 0: A girat amb defenses contra A girat amb fases (spellF1)

| escenari | A girat amb fases | A girat amb defenses | diferència | interval del 95 % | A girat amb defenses guanya |
|---|---|---|---|---|---|
| net | 0.809 | 0.811 | +0.002 | -0.001 a +0.005 | 6 de 10 |
| curts ×¼ | 0.718 | 0.721 | +0.003 | -0.001 a +0.007 | 6 de 10 |
| llargs ×¼ | 0.714 | 0.723 | +0.009 | +0.006 a +0.012 | 10 de 10 |
| barreja ×¼ | 0.718 | 0.721 | +0.003 | -0.001 a +0.008 | 6 de 10 |
| aire ×¼ | 0.676 | 0.679 | +0.003 | -0.001 a +0.007 | 7 de 10 |
| curts | 0.693 | 0.697 | +0.005 | +0.001 a +0.008 | 7 de 10 |
| llargs | 0.674 | 0.677 | +0.003 | -0.000 a +0.006 | 6 de 10 |
| barreja | 0.675 | 0.679 | +0.004 | -0.001 a +0.009 | 6 de 10 |
| aire | 0.652 | 0.654 | +0.002 | -0.002 a +0.006 | 5 de 10 |
| soroll2 | 0.600 | 0.603 | +0.003 | -0.002 a +0.008 | 7 de 10 |
| partit ×¼ | 0.772 | 0.778 | +0.006 | +0.002 a +0.011 | 8 de 10 |

## atac mitjà, defensar mitjà, lligades 1: A girat amb defenses contra A girat amb fases (spellF1)

| escenari | A girat amb fases | A girat amb defenses | diferència | interval del 95 % | A girat amb defenses guanya |
|---|---|---|---|---|---|
| net | 0.809 | 0.809 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| curts ×¼ | 0.718 | 0.718 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| llargs ×¼ | 0.714 | 0.714 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| barreja ×¼ | 0.718 | 0.718 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| aire ×¼ | 0.676 | 0.676 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| curts | 0.693 | 0.693 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| llargs | 0.674 | 0.674 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| barreja | 0.675 | 0.675 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| aire | 0.652 | 0.652 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| soroll2 | 0.600 | 0.600 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| partit ×¼ | 0.772 | 0.772 | +0.000 | +0.000 a +0.000 | 0 de 10 |

## atac dolent, defensar dolent, lligades 0: A girat amb defenses contra A girat amb fases (spellF1)

| escenari | A girat amb fases | A girat amb defenses | diferència | interval del 95 % | A girat amb defenses guanya |
|---|---|---|---|---|---|
| net | 0.800 | 0.796 | -0.004 | -0.006 a -0.001 | 2 de 10 |
| curts ×¼ | 0.706 | 0.707 | +0.002 | -0.002 a +0.005 | 8 de 10 |
| llargs ×¼ | 0.699 | 0.698 | -0.001 | -0.006 a +0.004 | 5 de 10 |
| barreja ×¼ | 0.703 | 0.708 | +0.005 | +0.002 a +0.008 | 8 de 10 |
| aire ×¼ | 0.656 | 0.655 | -0.001 | -0.005 a +0.003 | 4 de 10 |
| curts | 0.674 | 0.670 | -0.004 | -0.008 a -0.001 | 2 de 10 |
| llargs | 0.655 | 0.654 | -0.001 | -0.006 a +0.003 | 5 de 10 |
| barreja | 0.661 | 0.659 | -0.002 | -0.006 a +0.002 | 4 de 10 |
| aire | 0.627 | 0.625 | -0.002 | -0.008 a +0.003 | 3 de 10 |
| soroll2 | 0.577 | 0.575 | -0.002 | -0.008 a +0.002 | 5 de 10 |
| partit ×¼ | 0.758 | 0.760 | +0.002 | -0.001 a +0.005 | 5 de 10 |

## atac dolent, defensar dolent, lligades 0.5: A girat amb defenses contra A girat amb fases (spellF1)

| escenari | A girat amb fases | A girat amb defenses | diferència | interval del 95 % | A girat amb defenses guanya |
|---|---|---|---|---|---|
| net | 0.800 | 0.797 | -0.003 | -0.004 a -0.002 | 1 de 10 |
| curts ×¼ | 0.706 | 0.708 | +0.002 | -0.001 a +0.005 | 6 de 10 |
| llargs ×¼ | 0.699 | 0.697 | -0.002 | -0.005 a +0.001 | 4 de 10 |
| barreja ×¼ | 0.703 | 0.707 | +0.004 | +0.002 a +0.006 | 8 de 10 |
| aire ×¼ | 0.656 | 0.657 | +0.001 | -0.002 a +0.004 | 5 de 10 |
| curts | 0.674 | 0.673 | -0.002 | -0.004 a +0.000 | 3 de 10 |
| llargs | 0.655 | 0.656 | +0.000 | -0.002 a +0.003 | 6 de 10 |
| barreja | 0.661 | 0.659 | -0.003 | -0.006 a +0.001 | 2 de 10 |
| aire | 0.627 | 0.626 | -0.002 | -0.005 a +0.003 | 2 de 10 |
| soroll2 | 0.577 | 0.575 | -0.002 | -0.005 a +0.001 | 2 de 10 |
| partit ×¼ | 0.758 | 0.760 | +0.001 | -0.001 a +0.004 | 7 de 10 |

## atac dolent, defensar dolent, lligades 1: A girat amb defenses contra A girat amb fases (spellF1)

| escenari | A girat amb fases | A girat amb defenses | diferència | interval del 95 % | A girat amb defenses guanya |
|---|---|---|---|---|---|
| net | 0.800 | 0.800 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| curts ×¼ | 0.706 | 0.706 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| llargs ×¼ | 0.699 | 0.699 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| barreja ×¼ | 0.703 | 0.703 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| aire ×¼ | 0.656 | 0.656 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| curts | 0.674 | 0.674 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| llargs | 0.655 | 0.655 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| barreja | 0.661 | 0.661 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| aire | 0.627 | 0.627 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| soroll2 | 0.577 | 0.577 | +0.000 | +0.000 a +0.000 | 0 de 10 |
| partit ×¼ | 0.758 | 0.758 | +0.000 | +0.000 a +0.000 | 0 de 10 |

## atac mitjà, defensar mitjà, lligades 0.5, només els partits de dfl

| escenari | A girat amb fases | A girat amb defenses | diferència | interval del 95 % | A girat amb defenses guanya |
|---|---|---|---|---|---|
| net | 0.777 | 0.779 | +0.002 | -0.001 a +0.006 | 5 de 7 |
| curts ×¼ | 0.689 | 0.690 | +0.001 | -0.003 a +0.005 | 4 de 7 |
| llargs ×¼ | 0.681 | 0.688 | +0.006 | +0.004 a +0.009 | 7 de 7 |
| barreja ×¼ | 0.685 | 0.686 | +0.001 | -0.004 a +0.006 | 4 de 7 |
| aire ×¼ | 0.624 | 0.625 | +0.001 | -0.003 a +0.004 | 4 de 7 |
| curts | 0.663 | 0.666 | +0.003 | -0.000 a +0.007 | 4 de 7 |
| llargs | 0.638 | 0.640 | +0.001 | -0.001 a +0.004 | 5 de 7 |
| barreja | 0.641 | 0.642 | +0.001 | -0.003 a +0.004 | 4 de 7 |
| aire | 0.605 | 0.608 | +0.003 | +0.001 a +0.005 | 6 de 7 |
| soroll2 | 0.552 | 0.551 | -0.001 | -0.004 a +0.001 | 3 de 7 |
| partit ×¼ | 0.738 | 0.741 | +0.003 | +0.001 a +0.006 | 5 de 7 |

## atac mitjà, defensar mitjà, lligades 0.5, només els partits de metrica

| escenari | A girat amb fases | A girat amb defenses | diferència | interval del 95 % | A girat amb defenses guanya |
|---|---|---|---|---|---|
| net | 0.884 | 0.882 | -0.003 | -0.007 a +0.000 | 0 de 3 |
| curts ×¼ | 0.784 | 0.785 | +0.001 | -0.001 a +0.004 | 2 de 3 |
| llargs ×¼ | 0.789 | 0.792 | +0.003 | -0.004 a +0.008 | 2 de 3 |
| barreja ×¼ | 0.794 | 0.797 | +0.003 | +0.002 a +0.004 | 3 de 3 |
| aire ×¼ | 0.797 | 0.796 | -0.001 | -0.006 a +0.005 | 1 de 3 |
| curts | 0.762 | 0.765 | +0.003 | +0.001 a +0.004 | 3 de 3 |
| llargs | 0.757 | 0.755 | -0.002 | -0.007 a +0.004 | 1 de 3 |
| barreja | 0.755 | 0.754 | -0.001 | -0.003 a +0.002 | 1 de 3 |
| aire | 0.762 | 0.764 | +0.002 | -0.005 a +0.012 | 1 de 3 |
| soroll2 | 0.714 | 0.713 | -0.001 | -0.003 a +0.002 | 1 de 3 |
| partit ×¼ | 0.851 | 0.853 | +0.002 | -0.001 a +0.005 | 2 de 3 |

## On falla, abans i després

A atac mitjà, defensar mitjà, lligades 0.5, les causes de `banc/on_falla.py`: la part de les possessions de la veritat
de cada causa, i les predites que sobren a l'altre equip per cada 100 possessions de la veritat.

**curts ×¼**

| causa | A girat amb fases | A girat amb defenses |
|---|---|---|
| encertada | 0.653 | 0.652 |
| engolida | 0.105 | 0.107 |
| l'altre equip | 0.027 | 0.027 |
| la D | 0.016 | 0.016 |
| trencada | 0.005 | 0.006 |
| ajuntada, per sobre de l'altre equip | 0.133 | 0.134 |
| ajuntada, per sobre de la D | 0.001 | 0.001 |
| les vores | 0.059 | 0.057 |
| sobren a l'altre equip, per cada 100 | 6.986 | 6.776 |

**els quatre ×¼ junts**

| causa | A girat amb fases | A girat amb defenses |
|---|---|---|
| encertada | 0.639 | 0.639 |
| engolida | 0.103 | 0.104 |
| l'altre equip | 0.030 | 0.030 |
| la D | 0.027 | 0.027 |
| trencada | 0.006 | 0.005 |
| ajuntada, per sobre de l'altre equip | 0.131 | 0.132 |
| ajuntada, per sobre de la D | 0.001 | 0.001 |
| les vores | 0.063 | 0.060 |
| sobren a l'altre equip, per cada 100 | 6.776 | 6.291 |

**net**

| causa | A girat amb fases | A girat amb defenses |
|---|---|---|
| encertada | 0.759 | 0.758 |
| engolida | 0.074 | 0.074 |
| l'altre equip | 0.023 | 0.024 |
| la D | 0.005 | 0.005 |
| trencada | 0.004 | 0.004 |
| ajuntada, per sobre de l'altre equip | 0.093 | 0.093 |
| ajuntada, per sobre de la D | 0.000 | 0.000 |
| les vores | 0.042 | 0.041 |
| sobren a l'altre equip, per cada 100 | 5.584 | 5.374 |

## Les fases simulades

A curts ×¼, amb les llavors de provar, la mitjana dels deu partits: quantes fases d'atac i de defensar;
de les imatges de dins de les parts, la part amb alguna fase (d'atac, o de qualsevol) i la part on es
resta (dins de fases d'un sol equip, sense el marge triat).

| cas | fases | de_defensar | part_atac | part_alguna | resta_atac | resta_amb |
|---|---|---|---|---|---|---|
| atac bo, defensar bo, lligades 0 | 264.000 | 258.900 | 0.463 | 0.541 | 0.459 | 0.522 |
| atac bo, defensar bo, lligades 0.5 | 264.000 | 261.600 | 0.463 | 0.502 | 0.459 | 0.491 |
| atac bo, defensar bo, lligades 1 | 264.000 | 264.000 | 0.463 | 0.463 | 0.459 | 0.459 |
| atac mitjà, defensar mitjà, lligades 0 | 141.800 | 140.900 | 0.290 | 0.423 | 0.285 | 0.394 |
| atac mitjà, defensar mitjà, lligades 0.5 | 141.800 | 140.700 | 0.290 | 0.355 | 0.285 | 0.340 |
| atac mitjà, defensar mitjà, lligades 1 | 141.800 | 141.800 | 0.290 | 0.290 | 0.285 | 0.285 |
| atac dolent, defensar dolent, lligades 0 | 100.600 | 98.800 | 0.199 | 0.332 | 0.193 | 0.298 |
| atac dolent, defensar dolent, lligades 0.5 | 100.600 | 100.300 | 0.199 | 0.263 | 0.193 | 0.243 |
| atac dolent, defensar dolent, lligades 1 | 100.600 | 100.600 | 0.199 | 0.199 | 0.193 | 0.193 |
| atac cap, defensar cap, lligades 0 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| atac cap, defensar cap, lligades 0.5 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| atac cap, defensar cap, lligades 1 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| atac mitjà, defensar dolent, lligades 0 | 141.800 | 98.800 | 0.290 | 0.388 | 0.285 | 0.351 |

## L'spellF1 de cada mètode (mitjana dels deu partits, atac mitjà, defensar mitjà, lligades 0.5)

**spellF1 a la veritat de toc**

| escenari | A girat amb fases | A girat amb defenses |
|---|---|---|
| net | 0.809 | 0.810 |
| curts ×¼ | 0.718 | 0.718 |
| llargs ×¼ | 0.714 | 0.719 |
| barreja ×¼ | 0.718 | 0.720 |
| aire ×¼ | 0.676 | 0.676 |
| curts | 0.693 | 0.696 |
| llargs | 0.674 | 0.674 |
| barreja | 0.675 | 0.676 |
| aire | 0.652 | 0.655 |
| soroll2 | 0.600 | 0.599 |
| partit ×¼ | 0.772 | 0.775 |

**spellF1 a la veritat de sempre**

| escenari | A girat amb fases | A girat amb defenses |
|---|---|---|
| net | 0.818 | 0.819 |
| curts ×¼ | 0.726 | 0.727 |
| llargs ×¼ | 0.725 | 0.730 |
| barreja ×¼ | 0.729 | 0.730 |
| aire ×¼ | 0.690 | 0.689 |
| curts | 0.704 | 0.707 |
| llargs | 0.682 | 0.683 |
| barreja | 0.688 | 0.687 |
| aire | 0.662 | 0.664 |
| soroll2 | 0.610 | 0.608 |
| partit ×¼ | 0.784 | 0.785 |

## Els punts i els decodificadors

Els de la T3am, a cada partit: la pilota morta i les fases d'A girat amb fases, i el decodificador d'A camp girat.
