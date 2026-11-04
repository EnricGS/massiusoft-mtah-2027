# Banc obert · el resum per al document tècnic

Generat amb `uv run python -I -m banc.resum`. Dades obertes: 7 partits de DFL (IDSSE, CC BY 4.0) i
els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa: la capçalera
de `banc/resum.py`.

**A xarxes** és el model de la cadena. Els passos, de la T3c a la T3o, són cadascun l'anterior amb una
idea més, amb les files del banc on es va provar. Cada un, amb el decodificador triat amb els altres
nou partits als escenaris ×¼.

## spellF1 de cada pas (mitjana dels deu partits)

| escenari | A ×1+×¼ | A control | A context | A per possessió | A contacte | A canvis | A aturades | A xarxa | A xarxes |
|---|---|---|---|---|---|---|---|---|---|
| net | 0.625 | 0.746 | 0.775 | 0.786 | 0.789 | 0.798 | 0.801 | 0.803 | 0.808 |
| curts ×¼ | 0.569 | 0.606 | 0.639 | 0.644 | 0.647 | 0.652 | 0.659 | 0.683 | 0.684 |
| llargs ×¼ | 0.531 | 0.593 | 0.621 | 0.629 | 0.633 | 0.639 | 0.648 | 0.659 | 0.662 |
| barreja ×¼ | 0.544 | 0.601 | 0.631 | 0.647 | 0.644 | 0.653 | 0.661 | 0.667 | 0.671 |
| aire ×¼ | 0.493 | 0.525 | 0.556 | 0.564 | 0.575 | 0.577 | 0.585 | 0.600 | 0.612 |
| curts | 0.535 | 0.545 | 0.583 | 0.583 | 0.589 | 0.591 | 0.601 | 0.642 | 0.644 |
| llargs | 0.497 | 0.510 | 0.547 | 0.554 | 0.555 | 0.558 | 0.568 | 0.607 | 0.607 |
| barreja | 0.515 | 0.523 | 0.562 | 0.565 | 0.565 | 0.572 | 0.579 | 0.611 | 0.616 |
| aire | 0.466 | 0.477 | 0.508 | 0.511 | 0.520 | 0.522 | 0.526 | 0.563 | 0.564 |
| soroll2 | 0.348 | 0.333 | 0.373 | 0.381 | 0.384 | 0.384 | 0.388 | 0.473 | 0.478 |

## A xarxes, sense decodificar, i les línies base (spellF1)

| escenari | A xarxes | sense decodificar | millor línia base | smooth50·X | macroF1, A xarxes |
|---|---|---|---|---|---|
| net | 0.808 | 0.632 | 0.376 (smooth125·D) | 0.312 | 0.954 |
| curts ×¼ | 0.684 | 0.451 | 0.256 (smooth125·X) | 0.221 | 0.925 |
| llargs ×¼ | 0.662 | 0.427 | 0.219 (smooth125·D) | 0.207 | 0.910 |
| barreja ×¼ | 0.671 | 0.443 | 0.224 (smooth125·X) | 0.207 | 0.915 |
| aire ×¼ | 0.612 | 0.355 | 0.227 (smooth125·X) | 0.217 | 0.895 |
| curts | 0.644 | 0.326 | 0.240 (smooth125·X) | 0.185 | 0.912 |
| llargs | 0.607 | 0.301 | 0.199 (smooth125·X) | 0.182 | 0.894 |
| barreja | 0.616 | 0.299 | 0.209 (smooth125·X) | 0.183 | 0.898 |
| aire | 0.564 | 0.252 | 0.209 (smooth125·X) | 0.184 | 0.877 |
| soroll2 | 0.478 | 0.111 | 0.164 (smooth125·X) | 0.132 | 0.770 |

*Sense decodificar: la classe més probable de cada imatge després de dividir pel prior (λ = 0 i
durada mínima 1).*

## A xarxes contra la millor línia base (spellF1)

| escenari | diferència | interval del 95 % | guanya |
|---|---|---|---|
| net | +0.432 | +0.407 a +0.452 | 10 de 10 |
| curts ×¼ | +0.429 | +0.412 a +0.445 | 10 de 10 |
| llargs ×¼ | +0.442 | +0.421 a +0.464 | 10 de 10 |
| barreja ×¼ | +0.447 | +0.433 a +0.463 | 10 de 10 |
| aire ×¼ | +0.385 | +0.368 a +0.400 | 10 de 10 |
| curts | +0.404 | +0.386 a +0.423 | 10 de 10 |
| llargs | +0.408 | +0.383 a +0.432 | 10 de 10 |
| barreja | +0.407 | +0.385 a +0.431 | 10 de 10 |
| aire | +0.355 | +0.340 a +0.370 | 10 de 10 |
| soroll2 | +0.314 | +0.299 a +0.329 | 10 de 10 |

## A xarxes contra smooth50·X (spellF1)

| escenari | diferència | interval del 95 % | guanya |
|---|---|---|---|
| net | +0.497 | +0.477 a +0.514 | 10 de 10 |
| curts ×¼ | +0.463 | +0.448 a +0.477 | 10 de 10 |
| llargs ×¼ | +0.455 | +0.431 a +0.481 | 10 de 10 |
| barreja ×¼ | +0.464 | +0.445 a +0.482 | 10 de 10 |
| aire ×¼ | +0.395 | +0.376 a +0.412 | 10 de 10 |
| curts | +0.459 | +0.436 a +0.482 | 10 de 10 |
| llargs | +0.425 | +0.398 a +0.450 | 10 de 10 |
| barreja | +0.433 | +0.410 a +0.459 | 10 de 10 |
| aire | +0.380 | +0.363 a +0.395 | 10 de 10 |
| soroll2 | +0.345 | +0.328 a +0.362 | 10 de 10 |

## A xarxes contra A context (spellF1)

| escenari | diferència | interval del 95 % | guanya |
|---|---|---|---|
| net | +0.033 | +0.018 a +0.048 | 8 de 10 |
| curts ×¼ | +0.045 | +0.031 a +0.057 | 9 de 10 |
| llargs ×¼ | +0.040 | +0.030 a +0.050 | 10 de 10 |
| barreja ×¼ | +0.040 | +0.029 a +0.051 | 10 de 10 |
| aire ×¼ | +0.055 | +0.040 a +0.070 | 10 de 10 |
| curts | +0.061 | +0.051 a +0.070 | 10 de 10 |
| llargs | +0.060 | +0.043 a +0.078 | 10 de 10 |
| barreja | +0.055 | +0.038 a +0.073 | 10 de 10 |
| aire | +0.056 | +0.047 a +0.064 | 10 de 10 |
| soroll2 | +0.105 | +0.096 a +0.114 | 10 de 10 |

## A xarxes contra A ×1+×¼ (spellF1)

| escenari | diferència | interval del 95 % | guanya |
|---|---|---|---|
| net | +0.183 | +0.156 a +0.204 | 10 de 10 |
| curts ×¼ | +0.116 | +0.099 a +0.131 | 10 de 10 |
| llargs ×¼ | +0.130 | +0.116 a +0.145 | 10 de 10 |
| barreja ×¼ | +0.127 | +0.117 a +0.138 | 10 de 10 |
| aire ×¼ | +0.119 | +0.104 a +0.135 | 10 de 10 |
| curts | +0.109 | +0.089 a +0.130 | 10 de 10 |
| llargs | +0.110 | +0.089 a +0.130 | 10 de 10 |
| barreja | +0.101 | +0.082 a +0.122 | 10 de 10 |
| aire | +0.098 | +0.090 a +0.105 | 10 de 10 |
| soroll2 | +0.130 | +0.117 a +0.144 | 10 de 10 |

## A xarxes, per font, i les possessions

| escenari | spellF1 DFL | spellF1 Metrica | possessions predites per cada real |
|---|---|---|---|
| net | 0.775 | 0.886 | 0.93 |
| curts ×¼ | 0.653 | 0.758 | 0.84 |
| llargs ×¼ | 0.630 | 0.735 | 0.82 |
| barreja ×¼ | 0.643 | 0.737 | 0.82 |
| aire ×¼ | 0.555 | 0.744 | 0.80 |
| curts | 0.615 | 0.713 | 0.84 |
| llargs | 0.571 | 0.690 | 0.79 |
| barreja | 0.583 | 0.694 | 0.79 |
| aire | 0.510 | 0.690 | 0.77 |
| soroll2 | 0.440 | 0.567 | 0.96 |

**El decodificador triat amb cada partit fora:** w = 4, λ = 32 i durada mínima 12 en 8 partits; w = 4, λ = 64 i durada mínima 12 en 1 partits; w = 4, λ = 32 i durada mínima 1 en 1 partits.
