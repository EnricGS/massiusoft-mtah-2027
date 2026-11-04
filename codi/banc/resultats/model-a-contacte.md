# Banc obert · El darrer contacte, com a senyal (T3h)

Generat amb `uv run python -I -m banc.model_a_contacte`. Dades obertes: 7 partits de DFL (IDSSE, CC
BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3h», i la capçalera de `banc/model_a_contacte.py`.

**A context** és el model de la cadena (T3e); **A per possessió**, el mateix amb una altra tria
de les imatges que s'aprenen (T3f); i **A contacte**, A per possessió amb els senyals del darrer
contacte al primer classificador. Tots tenen el decodificador triat amb els altres nou partits als
escenaris ×¼.

## L'spellF1 i el macroF1 de cada classificador (mitjana dels deu partits)

**spellF1**

| escenari | A context | A per possessió | A contacte |
|---|---|---|---|
| net | 0.775 | 0.786 | 0.789 |
| curts ×¼ | 0.639 | 0.644 | 0.647 |
| llargs ×¼ | 0.621 | 0.629 | 0.633 |
| barreja ×¼ | 0.631 | 0.647 | 0.644 |
| aire ×¼ | 0.556 | 0.564 | 0.575 |
| curts | 0.583 | 0.583 | 0.589 |
| llargs | 0.547 | 0.554 | 0.555 |
| barreja | 0.562 | 0.565 | 0.565 |
| aire | 0.508 | 0.511 | 0.520 |
| soroll2 | 0.373 | 0.381 | 0.384 |

**macroF1**

| escenari | A context | A per possessió | A contacte |
|---|---|---|---|
| net | 0.952 | 0.951 | 0.950 |
| curts ×¼ | 0.919 | 0.917 | 0.918 |
| llargs ×¼ | 0.906 | 0.903 | 0.903 |
| barreja ×¼ | 0.910 | 0.908 | 0.908 |
| aire ×¼ | 0.886 | 0.881 | 0.887 |
| curts | 0.902 | 0.897 | 0.899 |
| llargs | 0.885 | 0.880 | 0.879 |
| barreja | 0.886 | 0.882 | 0.884 |
| aire | 0.865 | 0.861 | 0.864 |
| soroll2 | 0.697 | 0.683 | 0.694 |

## A contacte contra A context (spellF1): el criteri

| escenari | A context | A contacte | diferència | interval del 95 % | A contacte guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.775 | 0.789 | +0.014 | +0.002 a +0.024 | 7 de 10 | no perd | ✓ |
| curts ×¼ | 0.639 | 0.647 | +0.008 | -0.003 a +0.018 | 7 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.621 | 0.633 | +0.011 | +0.003 a +0.019 | 8 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.631 | 0.644 | +0.013 | -0.000 a +0.025 | 8 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.556 | 0.575 | +0.018 | +0.005 a +0.032 | 8 de 10 | guanya clarament | ✗ |
| curts | 0.583 | 0.589 | +0.006 | -0.005 a +0.016 | 6 de 10 | no perd | ✓ |
| llargs | 0.547 | 0.555 | +0.007 | +0.000 a +0.017 | 7 de 10 | no perd | ✓ |
| barreja | 0.562 | 0.565 | +0.004 | -0.005 a +0.013 | 6 de 10 | no perd | ✓ |
| aire | 0.508 | 0.520 | +0.012 | +0.005 a +0.020 | 8 de 10 | no perd | ✓ |
| soroll2 | 0.373 | 0.384 | +0.012 | +0.003 a +0.020 | 6 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre escenaris ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1 i el soroll2 | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## A contacte contra A per possessió (spellF1), només per saber-ho

Les mateixes mostres: la diferència és el que afegeixen els senyals del contacte.

| escenari | A per possessió | A contacte | diferència | interval del 95 % | A contacte guanya |
|---|---|---|---|---|---|
| net | 0.786 | 0.789 | +0.002 | -0.002 a +0.007 | 5 de 10 |
| curts ×¼ | 0.644 | 0.647 | +0.003 | -0.004 a +0.010 | 8 de 10 |
| llargs ×¼ | 0.629 | 0.633 | +0.004 | -0.002 a +0.011 | 3 de 10 |
| barreja ×¼ | 0.647 | 0.644 | -0.003 | -0.009 a +0.003 | 4 de 10 |
| aire ×¼ | 0.564 | 0.575 | +0.010 | +0.005 a +0.017 | 10 de 10 |
| curts | 0.583 | 0.589 | +0.006 | +0.002 a +0.010 | 8 de 10 |
| llargs | 0.554 | 0.555 | +0.001 | -0.004 a +0.006 | 6 de 10 |
| barreja | 0.565 | 0.565 | +0.000 | -0.008 a +0.008 | 5 de 10 |
| aire | 0.511 | 0.520 | +0.009 | +0.004 a +0.015 | 7 de 10 |
| soroll2 | 0.381 | 0.384 | +0.003 | -0.005 a +0.012 | 5 de 10 |

## Possessions predites per cada real (mitjana dels deu partits), només per saber-ho

| escenari | A context | A per possessió | A contacte |
|---|---|---|---|
| net | 0.83 | 0.91 | 0.91 |
| curts ×¼ | 0.74 | 0.82 | 0.82 |
| llargs ×¼ | 0.73 | 0.81 | 0.81 |
| barreja ×¼ | 0.72 | 0.81 | 0.80 |
| aire ×¼ | 0.72 | 0.81 | 0.79 |
| curts | 0.72 | 0.80 | 0.80 |
| llargs | 0.68 | 0.77 | 0.77 |
| barreja | 0.70 | 0.79 | 0.78 |
| aire | 0.69 | 0.78 | 0.76 |
| soroll2 | 1.03 | 1.08 | 1.07 |

## L'encert de l'equip per durada de la possessió, només per saber-ho

Als quatre escenaris ×¼: la part de les imatges de cada possessió de la veritat amb l'equip bo, de
mitjana per possessió. *Abans*, la P(H) contra la P(A) de cada imatge; *després*, amb el decodificador.

| durada | A context, abans | A context, després | A per possessió, abans | A per possessió, després | A contacte, abans | A contacte, després |
|---|---|---|---|---|---|---|
| <1 s | 0.413 | 0.320 | 0.556 | 0.455 | 0.556 | 0.456 |
| 1-2 s | 0.552 | 0.493 | 0.644 | 0.573 | 0.654 | 0.582 |
| 2-5 s | 0.692 | 0.641 | 0.724 | 0.675 | 0.725 | 0.679 |
| 5-10 s | 0.866 | 0.835 | 0.846 | 0.820 | 0.848 | 0.828 |
| >10 s | 0.956 | 0.942 | 0.941 | 0.930 | 0.942 | 0.931 |

## Els decodificadors triats (cada partit, amb els altres nou)

- A context: λ = 4, durada mínima 12 · A per possessió: λ = 8, durada mínima 12 · A contacte: λ = 8, durada mínima 1 (7 partits)
- A context: λ = 4, durada mínima 12 · A per possessió: λ = 8, durada mínima 12 · A contacte: λ = 8, durada mínima 12 (2 partits)
- A context: λ = 2, durada mínima 25 · A per possessió: λ = 8, durada mínima 12 · A contacte: λ = 8, durada mínima 1 (1 partits)
