# Banc obert · el resum d'A girat amb fases per al document tècnic

Generat amb `uv run python -I -m banc.resum_girat`. Dades obertes: 7 partits de DFL (IDSSE, CC BY 4.0) i
els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Es puntua a la veritat de
toc, amb el Smart Tagging simulat del nivell mitjà. Com es fa: la capçalera de `banc/resum_girat.py`.

**A girat amb fases** és el model de la cadena. Els passos, des d'A xarxes, decodificador de toc, són cadascun l'anterior amb una
idea més, amb la taula del banc on es va provar. Cada un, amb el decodificador i els paràmetres de cada
partit triats amb els altres nou.

## spellF1 de cada pas (mitjana dels deu partits)

| escenari | A xarxes, decodificador de toc | A sense pilota | A equips sencers | A pilota creïble | A neteja d'aire | A camp girat | A girat amb pilota morta | A girat amb fases |
|---|---|---|---|---|---|---|---|---|
| net | 0.798 | 0.799 | 0.799 | 0.799 | 0.799 | 0.803 | 0.804 | 0.809 |
| curts ×¼ | 0.673 | 0.692 | 0.699 | 0.699 | 0.699 | 0.703 | 0.704 | 0.718 |
| llargs ×¼ | 0.651 | 0.665 | 0.688 | 0.688 | 0.688 | 0.700 | 0.704 | 0.714 |
| barreja ×¼ | 0.660 | 0.677 | 0.696 | 0.696 | 0.696 | 0.706 | 0.706 | 0.718 |
| aire ×¼ | 0.600 | 0.623 | 0.629 | 0.636 | 0.644 | 0.656 | 0.660 | 0.676 |
| curts | 0.636 | 0.653 | 0.665 | 0.665 | 0.665 | 0.678 | 0.682 | 0.693 |
| llargs | 0.599 | 0.614 | 0.640 | 0.641 | 0.640 | 0.656 | 0.660 | 0.674 |
| barreja | 0.605 | 0.627 | 0.646 | 0.646 | 0.646 | 0.666 | 0.667 | 0.675 |
| aire | 0.554 | 0.582 | 0.600 | 0.605 | 0.618 | 0.632 | 0.636 | 0.652 |
| soroll2 | 0.470 | 0.508 | 0.534 | 0.536 | 0.534 | 0.574 | 0.584 | 0.600 |
| partit ×¼ | 0.746 | 0.755 | 0.761 | 0.761 | 0.761 | 0.758 | 0.761 | 0.772 |

## A girat amb fases, sense decodificar, i les línies base (spellF1)

| escenari | A girat amb fases | sense decodificar | millor línia base | smooth50·X | macroF1, A girat amb fases |
|---|---|---|---|---|---|
| net | 0.809 | 0.671 | 0.371 (smooth125·D) | 0.311 | 0.960 |
| curts ×¼ | 0.718 | 0.533 | 0.254 (smooth125·X) | 0.221 | 0.941 |
| llargs ×¼ | 0.714 | 0.511 | 0.218 (smooth125·D) | 0.206 | 0.931 |
| barreja ×¼ | 0.718 | 0.521 | 0.221 (smooth125·X) | 0.207 | 0.935 |
| aire ×¼ | 0.676 | 0.449 | 0.225 (smooth125·X) | 0.216 | 0.925 |
| curts | 0.693 | 0.384 | 0.238 (smooth125·X) | 0.187 | 0.931 |
| llargs | 0.674 | 0.355 | 0.197 (smooth125·X) | 0.183 | 0.922 |
| barreja | 0.675 | 0.364 | 0.207 (smooth125·X) | 0.184 | 0.924 |
| aire | 0.652 | 0.324 | 0.206 (smooth125·X) | 0.183 | 0.915 |
| soroll2 | 0.600 | 0.161 | 0.164 (smooth125·X) | 0.133 | 0.875 |
| partit ×¼ | 0.772 | 0.573 | 0.385 (smooth125·D) | 0.270 | 0.952 |

*Sense decodificar: la classe més probable de cada imatge, amb el Smart Tagging i la D impossible
(λ = 0 i durada mínima 1).*

## A girat amb fases contra la millor línia base (spellF1)

| escenari | diferència | interval del 95 % | guanya |
|---|---|---|---|
| net | +0.438 | +0.422 a +0.455 | 10 de 10 |
| curts ×¼ | +0.464 | +0.451 a +0.477 | 10 de 10 |
| llargs ×¼ | +0.496 | +0.479 a +0.512 | 10 de 10 |
| barreja ×¼ | +0.497 | +0.482 a +0.513 | 10 de 10 |
| aire ×¼ | +0.452 | +0.440 a +0.463 | 10 de 10 |
| curts | +0.455 | +0.444 a +0.468 | 10 de 10 |
| llargs | +0.477 | +0.460 a +0.495 | 10 de 10 |
| barreja | +0.468 | +0.455 a +0.482 | 10 de 10 |
| aire | +0.446 | +0.433 a +0.458 | 10 de 10 |
| soroll2 | +0.437 | +0.420 a +0.452 | 10 de 10 |
| partit ×¼ | +0.387 | +0.371 a +0.403 | 10 de 10 |

## A girat amb fases contra smooth50·X (spellF1)

| escenari | diferència | interval del 95 % | guanya |
|---|---|---|---|
| net | +0.498 | +0.486 a +0.509 | 10 de 10 |
| curts ×¼ | +0.497 | +0.487 a +0.508 | 10 de 10 |
| llargs ×¼ | +0.507 | +0.488 a +0.528 | 10 de 10 |
| barreja ×¼ | +0.511 | +0.494 a +0.529 | 10 de 10 |
| aire ×¼ | +0.460 | +0.445 a +0.473 | 10 de 10 |
| curts | +0.506 | +0.489 a +0.524 | 10 de 10 |
| llargs | +0.491 | +0.472 a +0.511 | 10 de 10 |
| barreja | +0.492 | +0.478 a +0.507 | 10 de 10 |
| aire | +0.469 | +0.454 a +0.482 | 10 de 10 |
| soroll2 | +0.468 | +0.452 a +0.483 | 10 de 10 |
| partit ×¼ | +0.502 | +0.485 a +0.519 | 10 de 10 |

## A girat amb fases contra A xarxes, decodificador de toc (spellF1)

| escenari | diferència | interval del 95 % | guanya |
|---|---|---|---|
| net | +0.011 | -0.000 a +0.023 | 8 de 10 |
| curts ×¼ | +0.044 | +0.037 a +0.053 | 10 de 10 |
| llargs ×¼ | +0.062 | +0.051 a +0.074 | 10 de 10 |
| barreja ×¼ | +0.058 | +0.053 a +0.062 | 10 de 10 |
| aire ×¼ | +0.076 | +0.070 a +0.082 | 10 de 10 |
| curts | +0.057 | +0.051 a +0.064 | 10 de 10 |
| llargs | +0.074 | +0.062 a +0.086 | 10 de 10 |
| barreja | +0.070 | +0.058 a +0.081 | 10 de 10 |
| aire | +0.098 | +0.092 a +0.103 | 10 de 10 |
| soroll2 | +0.130 | +0.122 a +0.138 | 10 de 10 |
| partit ×¼ | +0.026 | +0.015 a +0.036 | 9 de 10 |

## Per nivell del Smart Tagging simulat (spellF1)

*cap: sense Smart Tagging, que és A camp girat.*

| escenari | bo | mitjà | dolent | cap |
|---|---|---|---|---|
| net | 0.834 | 0.809 | 0.800 | 0.803 |
| curts ×¼ | 0.762 | 0.718 | 0.706 | 0.703 |
| llargs ×¼ | 0.766 | 0.714 | 0.699 | 0.700 |
| barreja ×¼ | 0.757 | 0.718 | 0.703 | 0.706 |
| aire ×¼ | 0.728 | 0.676 | 0.656 | 0.656 |
| curts | 0.751 | 0.693 | 0.674 | 0.678 |
| llargs | 0.726 | 0.674 | 0.655 | 0.656 |
| barreja | 0.732 | 0.675 | 0.661 | 0.666 |
| aire | 0.709 | 0.652 | 0.627 | 0.632 |
| soroll2 | 0.679 | 0.600 | 0.577 | 0.574 |
| partit ×¼ | 0.810 | 0.772 | 0.758 | 0.758 |

## A girat amb fases, per font, i les possessions

| escenari | spellF1 DFL | spellF1 Metrica | possessions predites per cada real |
|---|---|---|---|
| net | 0.777 | 0.884 | 0.87 |
| curts ×¼ | 0.689 | 0.784 | 0.81 |
| llargs ×¼ | 0.681 | 0.789 | 0.80 |
| barreja ×¼ | 0.685 | 0.794 | 0.81 |
| aire ×¼ | 0.624 | 0.797 | 0.79 |
| curts | 0.663 | 0.762 | 0.79 |
| llargs | 0.638 | 0.757 | 0.77 |
| barreja | 0.641 | 0.755 | 0.78 |
| aire | 0.605 | 0.762 | 0.76 |
| soroll2 | 0.552 | 0.714 | 0.84 |
| partit ×¼ | 0.738 | 0.851 | 0.85 |

**El decodificador triat amb cada partit fora:** w = 4, λ = 32 i durada mínima 12 en 8 partits; w = 4, λ = 32 i durada mínima 25 en 2 partits.

**La pilota morta:** beta_d = 1, forma = per tipus, durada = 1.5, marge_s = 0 en 10 partits.

**Les fases:** gamma = 1, delta = 1, marge_s = 0 en 10 partits.
