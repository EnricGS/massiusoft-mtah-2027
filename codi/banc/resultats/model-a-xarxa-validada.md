# Banc obert · La xarxa aprèn fins que deixa de millorar (T3n)

Generat amb `uv run python -I -m banc.model_a_xarxa_validada`. Dades obertes: 7 partits de DFL (IDSSE,
CC BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3n», i la capçalera de `banc/model_a_xarxa_validada.py`.

**A context** és el model de la cadena (T3e), amb el decodificador d'ara. **A xarxa** és el de
la T3m, amb 15 passades. **A xarxa validada** és A xarxa amb les passades de cada xarxa triades amb un
partit apartat (`cadena/xarxa_validada.py`). Tots tenen els paràmetres del decodificador triats amb els
altres nou partits als escenaris ×¼.

## L'spellF1 i el macroF1 de cada mètode (mitjana dels deu partits)

**spellF1**

| escenari | A context | A xarxa | A xarxa validada |
|---|---|---|---|
| net | 0.775 | 0.803 | 0.806 |
| curts ×¼ | 0.639 | 0.683 | 0.681 |
| llargs ×¼ | 0.621 | 0.659 | 0.656 |
| barreja ×¼ | 0.631 | 0.667 | 0.666 |
| aire ×¼ | 0.556 | 0.600 | 0.610 |
| curts | 0.583 | 0.642 | 0.639 |
| llargs | 0.547 | 0.607 | 0.601 |
| barreja | 0.562 | 0.611 | 0.610 |
| aire | 0.508 | 0.563 | 0.555 |
| soroll2 | 0.373 | 0.473 | 0.463 |

**macroF1**

| escenari | A context | A xarxa | A xarxa validada |
|---|---|---|---|
| net | 0.952 | 0.953 | 0.953 |
| curts ×¼ | 0.919 | 0.925 | 0.925 |
| llargs ×¼ | 0.906 | 0.909 | 0.908 |
| barreja ×¼ | 0.910 | 0.914 | 0.914 |
| aire ×¼ | 0.886 | 0.893 | 0.894 |
| curts | 0.902 | 0.911 | 0.910 |
| llargs | 0.885 | 0.894 | 0.891 |
| barreja | 0.886 | 0.897 | 0.896 |
| aire | 0.865 | 0.876 | 0.874 |
| soroll2 | 0.697 | 0.774 | 0.752 |

## A xarxa validada contra A context (spellF1): el criteri

| escenari | A context | A xarxa validada | diferència | interval del 95 % | A xarxa validada guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.775 | 0.806 | +0.031 | +0.018 a +0.043 | 8 de 10 | no perd | ✓ |
| curts ×¼ | 0.639 | 0.681 | +0.042 | +0.027 a +0.052 | 9 de 10 | guanya clarament | ✓ |
| llargs ×¼ | 0.621 | 0.656 | +0.035 | +0.023 a +0.048 | 10 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.631 | 0.666 | +0.035 | +0.022 a +0.046 | 9 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.556 | 0.610 | +0.054 | +0.042 a +0.066 | 10 de 10 | guanya clarament | ✓ |
| curts | 0.583 | 0.639 | +0.056 | +0.044 a +0.068 | 10 de 10 | no perd | ✓ |
| llargs | 0.547 | 0.601 | +0.053 | +0.041 a +0.070 | 10 de 10 | no perd | ✓ |
| barreja | 0.562 | 0.610 | +0.048 | +0.035 a +0.062 | 10 de 10 | no perd | ✓ |
| aire | 0.508 | 0.555 | +0.047 | +0.039 a +0.054 | 10 de 10 | no perd | ✓ |
| soroll2 | 0.373 | 0.463 | +0.090 | +0.080 a +0.101 | 10 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre escenaris ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1 i el soroll2 | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## A xarxa validada contra A xarxa (spellF1), només per saber-ho

El mateix amb 15 passades: la diferència és el que hi afegeix la regla.

| escenari | A xarxa | A xarxa validada | diferència | interval del 95 % | A xarxa validada guanya |
|---|---|---|---|---|---|
| net | 0.803 | 0.806 | +0.003 | -0.003 a +0.010 | 6 de 10 |
| curts ×¼ | 0.683 | 0.681 | -0.002 | -0.008 a +0.005 | 4 de 10 |
| llargs ×¼ | 0.659 | 0.656 | -0.002 | -0.006 a +0.002 | 3 de 10 |
| barreja ×¼ | 0.667 | 0.666 | -0.001 | -0.006 a +0.004 | 4 de 10 |
| aire ×¼ | 0.600 | 0.610 | +0.010 | +0.001 a +0.019 | 7 de 10 |
| curts | 0.642 | 0.639 | -0.002 | -0.004 a -0.001 | 2 de 10 |
| llargs | 0.607 | 0.601 | -0.006 | -0.014 a +0.002 | 3 de 10 |
| barreja | 0.611 | 0.610 | -0.001 | -0.012 a +0.009 | 4 de 10 |
| aire | 0.563 | 0.555 | -0.008 | -0.014 a -0.003 | 2 de 10 |
| soroll2 | 0.473 | 0.463 | -0.009 | -0.017 a -0.003 | 2 de 10 |

## Les passades de cada xarxa, només per saber-ho

La regla s'atura quan la pèrdua del partit apartat fa 3 passades seguides sense baixar del seu mínim, o a
les 60. *Triades*, les del mínim; *fetes*, les de la primera volta. La pèrdua del partit apartat, al
mínim i a la passada 15 (les de la T3m).

| partit que es prova | xarxa | apartat | triades | fetes | pèrdua al mínim | a la 15 |
|---|---|---|---|---|---|---|
| dfl-J03WMX | grup 0 | dfl-J03WOH | 1 | 4 | 0.5797 | — |
| dfl-J03WMX | grup 1 | dfl-J03WN1 | 1 | 4 | 0.5945 | — |
| dfl-J03WMX | grup 2 | dfl-J03WN1 | 1 | 4 | 0.6189 | — |
| dfl-J03WMX | la seva | dfl-J03WN1 | 1 | 4 | 0.5898 | — |
| dfl-J03WN1 | grup 0 | dfl-J03WOH | 1 | 4 | 0.5797 | — |
| dfl-J03WN1 | grup 1 | dfl-J03WMX | 1 | 4 | 0.6227 | — |
| dfl-J03WN1 | grup 2 | dfl-J03WMX | 1 | 4 | 0.6492 | — |
| dfl-J03WN1 | la seva | dfl-J03WMX | 1 | 4 | 0.6363 | — |
| dfl-J03WOH | grup 0 | dfl-J03WN1 | 1 | 4 | 0.6178 | — |
| dfl-J03WOH | grup 1 | dfl-J03WMX | 1 | 4 | 0.6227 | — |
| dfl-J03WOH | grup 2 | dfl-J03WMX | 1 | 4 | 0.6753 | — |
| dfl-J03WOH | la seva | dfl-J03WMX | 1 | 4 | 0.6219 | — |
| dfl-J03WOY | grup 0 | dfl-J03WN1 | 1 | 4 | 0.6135 | — |
| dfl-J03WOY | grup 1 | dfl-J03WMX | 1 | 4 | 0.6649 | — |
| dfl-J03WOY | grup 2 | dfl-J03WMX | 1 | 4 | 0.6753 | — |
| dfl-J03WOY | la seva | dfl-J03WMX | 2 | 5 | 0.6218 | — |
| dfl-J03WPY | grup 0 | dfl-J03WN1 | 1 | 4 | 0.6135 | — |
| dfl-J03WPY | grup 1 | dfl-J03WMX | 1 | 4 | 0.6433 | — |
| dfl-J03WPY | grup 2 | dfl-J03WMX | 2 | 5 | 0.6784 | — |
| dfl-J03WPY | la seva | dfl-J03WMX | 2 | 5 | 0.6159 | — |
| dfl-J03WQQ | grup 0 | dfl-J03WN1 | 1 | 4 | 0.6283 | — |
| dfl-J03WQQ | grup 1 | dfl-J03WMX | 1 | 4 | 0.6433 | — |
| dfl-J03WQQ | grup 2 | dfl-J03WMX | 1 | 4 | 0.6509 | — |
| dfl-J03WQQ | la seva | dfl-J03WMX | 2 | 5 | 0.6310 | — |
| dfl-J03WR9 | grup 0 | dfl-J03WN1 | 1 | 4 | 0.6159 | — |
| dfl-J03WR9 | grup 1 | dfl-J03WMX | 1 | 4 | 0.6492 | — |
| dfl-J03WR9 | grup 2 | dfl-J03WMX | 1 | 4 | 0.6509 | — |
| dfl-J03WR9 | la seva | dfl-J03WMX | 1 | 4 | 0.6412 | — |
| metrica-1 | grup 0 | dfl-J03WN1 | 1 | 4 | 0.6159 | — |
| metrica-1 | grup 1 | dfl-J03WMX | 1 | 4 | 0.6066 | — |
| metrica-1 | grup 2 | dfl-J03WMX | 1 | 4 | 0.6239 | — |
| metrica-1 | la seva | dfl-J03WMX | 1 | 4 | 0.6249 | — |
| metrica-2 | grup 0 | dfl-J03WN1 | 1 | 4 | 0.6260 | — |
| metrica-2 | grup 1 | dfl-J03WMX | 1 | 4 | 0.6066 | — |
| metrica-2 | grup 2 | dfl-J03WMX | 2 | 5 | 0.6202 | — |
| metrica-2 | la seva | dfl-J03WMX | 3 | 6 | 0.6041 | — |
| metrica-3 | grup 0 | dfl-J03WN1 | 1 | 4 | 0.6189 | — |
| metrica-3 | grup 1 | dfl-J03WMX | 1 | 4 | 0.6133 | — |
| metrica-3 | grup 2 | dfl-J03WMX | 2 | 5 | 0.6202 | — |
| metrica-3 | la seva | dfl-J03WMX | 1 | 4 | 0.6167 | — |

Les triades: de 1 a 3, la mediana 1.

## Per font (spellF1, mitjana dels partits de cada font), només per saber-ho

| escenari | font | A context | A xarxa | A xarxa validada |
|---|---|---|---|---|
| net | dfl | 0.754 | 0.774 | 0.774 |
| net | metrica | 0.825 | 0.870 | 0.881 |
| curts ×¼ | dfl | 0.611 | 0.655 | 0.653 |
| curts ×¼ | metrica | 0.705 | 0.747 | 0.747 |
| llargs ×¼ | dfl | 0.594 | 0.627 | 0.625 |
| llargs ×¼ | metrica | 0.686 | 0.731 | 0.731 |
| barreja ×¼ | dfl | 0.604 | 0.639 | 0.638 |
| barreja ×¼ | metrica | 0.692 | 0.732 | 0.732 |
| aire ×¼ | dfl | 0.499 | 0.544 | 0.553 |
| aire ×¼ | metrica | 0.690 | 0.732 | 0.743 |
| curts | dfl | 0.560 | 0.611 | 0.610 |
| curts | metrica | 0.636 | 0.712 | 0.707 |
| llargs | dfl | 0.518 | 0.572 | 0.563 |
| llargs | metrica | 0.615 | 0.689 | 0.689 |
| barreja | dfl | 0.533 | 0.581 | 0.579 |
| barreja | metrica | 0.628 | 0.681 | 0.683 |
| aire | dfl | 0.454 | 0.511 | 0.504 |
| aire | metrica | 0.636 | 0.685 | 0.673 |
| soroll2 | dfl | 0.321 | 0.428 | 0.421 |
| soroll2 | metrica | 0.493 | 0.576 | 0.561 |

## L'encert de l'equip abans de decodificar (escenaris ×¼), només per saber-ho

A les imatges de les possessions de la veritat, la part on l'equip més probable és el de la veritat,
per durada de la possessió i segons si la pilota es veu. *El primer* és el primer
classificador d'A contacte sol.

| durada | pilota | el primer | la xarxa de la T3m sola | la xarxa validada sola | A xarxa | A xarxa validada |
|---|---|---|---|---|---|---|
| <1 s | no | 0.285 | 0.158 | 0.154 | 0.369 | 0.372 |
| <1 s | sí | 0.595 | 0.450 | 0.428 | 0.665 | 0.663 |
| 1-2 s | no | 0.436 | 0.223 | 0.202 | 0.504 | 0.512 |
| 1-2 s | sí | 0.666 | 0.607 | 0.604 | 0.735 | 0.738 |
| 2-5 s | no | 0.569 | 0.307 | 0.305 | 0.607 | 0.621 |
| 2-5 s | sí | 0.754 | 0.724 | 0.732 | 0.805 | 0.804 |
| ≥5 s | no | 0.858 | 0.427 | 0.427 | 0.862 | 0.867 |
| ≥5 s | sí | 0.947 | 0.903 | 0.897 | 0.950 | 0.950 |

## Possessions predites per cada real (mitjana dels deu partits), només per saber-ho

| escenari | A context | A xarxa | A xarxa validada |
|---|---|---|---|
| net | 0.83 | 0.93 | 0.93 |
| curts ×¼ | 0.74 | 0.84 | 0.84 |
| llargs ×¼ | 0.73 | 0.82 | 0.82 |
| barreja ×¼ | 0.72 | 0.82 | 0.82 |
| aire ×¼ | 0.72 | 0.80 | 0.80 |
| curts | 0.72 | 0.83 | 0.84 |
| llargs | 0.68 | 0.79 | 0.80 |
| barreja | 0.70 | 0.80 | 0.81 |
| aire | 0.69 | 0.77 | 0.78 |
| soroll2 | 1.03 | 0.98 | 1.01 |

## Els paràmetres triats (cada partit, amb els altres nou)

- A context: λ = 4, durada mínima 12 · A xarxa: w = 4, λ = 32, durada mínima 12 · A xarxa validada: w = 4, λ = 32, durada mínima 12 (7 partits)
- A context: λ = 2, durada mínima 25 · A xarxa: w = 4, λ = 32, durada mínima 12 · A xarxa validada: w = 4, λ = 32, durada mínima 12 (1 partits)
- A context: λ = 4, durada mínima 12 · A xarxa: w = 4, λ = 32, durada mínima 12 · A xarxa validada: w = 4, λ = 32, durada mínima 1 (1 partits)
- A context: λ = 4, durada mínima 12 · A xarxa: w = 4, λ = 16, durada mínima 12 · A xarxa validada: w = 4, λ = 32, durada mínima 12 (1 partits)
