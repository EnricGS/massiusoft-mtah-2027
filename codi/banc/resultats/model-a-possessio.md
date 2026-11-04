# Banc obert · Cada possessió, amb prou mostres (T3f)

Generat amb `uv run python -I -m banc.model_a_possessio`. Dades obertes: 7 partits de DFL (IDSSE, CC
BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3f», i la capçalera de `banc/model_a_possessio.py`.

**A context** és el model de la cadena (T3e), i **A per possessió**, el mateix amb una altra tria de
les imatges que s'aprenen: cada possessió de la veritat, com a mínim amb 8. Tots dos tenen el
decodificador triat amb els altres nou partits als escenaris ×¼.

## L'spellF1 i el macroF1 de cada classificador (mitjana dels deu partits)

**spellF1**

| escenari | A context | A per possessió |
|---|---|---|
| net | 0.775 | 0.786 |
| curts ×¼ | 0.639 | 0.644 |
| llargs ×¼ | 0.621 | 0.629 |
| barreja ×¼ | 0.631 | 0.647 |
| aire ×¼ | 0.556 | 0.564 |
| curts | 0.583 | 0.583 |
| llargs | 0.547 | 0.554 |
| barreja | 0.562 | 0.565 |
| aire | 0.508 | 0.511 |
| soroll2 | 0.373 | 0.381 |

**macroF1**

| escenari | A context | A per possessió |
|---|---|---|
| net | 0.952 | 0.951 |
| curts ×¼ | 0.919 | 0.917 |
| llargs ×¼ | 0.906 | 0.903 |
| barreja ×¼ | 0.910 | 0.908 |
| aire ×¼ | 0.886 | 0.881 |
| curts | 0.902 | 0.897 |
| llargs | 0.885 | 0.880 |
| barreja | 0.886 | 0.882 |
| aire | 0.865 | 0.861 |
| soroll2 | 0.697 | 0.683 |

## A per possessió contra A context (spellF1): el criteri

| escenari | A context | A per possessió | diferència | interval del 95 % | A per possessió guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.775 | 0.786 | +0.011 | +0.001 a +0.021 | 7 de 10 | no perd | ✓ |
| curts ×¼ | 0.639 | 0.644 | +0.005 | -0.010 a +0.018 | 7 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.621 | 0.629 | +0.007 | -0.002 a +0.017 | 5 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.631 | 0.647 | +0.016 | +0.005 a +0.026 | 9 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.556 | 0.564 | +0.008 | -0.003 a +0.020 | 7 de 10 | guanya clarament | ✗ |
| curts | 0.583 | 0.583 | -0.000 | -0.009 a +0.008 | 5 de 10 | no perd | ✓ |
| llargs | 0.547 | 0.554 | +0.006 | -0.002 a +0.014 | 7 de 10 | no perd | ✓ |
| barreja | 0.562 | 0.565 | +0.004 | -0.008 a +0.016 | 5 de 10 | no perd | ✓ |
| aire | 0.508 | 0.511 | +0.003 | -0.005 a +0.011 | 5 de 10 | no perd | ✓ |
| soroll2 | 0.373 | 0.381 | +0.008 | +0.002 a +0.014 | 7 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre escenaris ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1 i el soroll2 | no perd a cap (diferència ≥ −0.04) | ✓ |

**No passa.**

## Possessions predites per cada real (mitjana dels deu partits), només per saber-ho

| escenari | A context | A per possessió |
|---|---|---|
| net | 0.83 | 0.91 |
| curts ×¼ | 0.74 | 0.82 |
| llargs ×¼ | 0.73 | 0.81 |
| barreja ×¼ | 0.72 | 0.81 |
| aire ×¼ | 0.72 | 0.81 |
| curts | 0.72 | 0.80 |
| llargs | 0.68 | 0.77 |
| barreja | 0.70 | 0.79 |
| aire | 0.69 | 0.78 |
| soroll2 | 1.03 | 1.08 |

## L'encert de l'equip per durada de la possessió, només per saber-ho

Als quatre escenaris ×¼: la part de les imatges de cada possessió de la veritat amb l'equip bo, de
mitjana per possessió. *Abans*, la P(H) contra la P(A) de cada imatge; *després*, amb el decodificador.

| durada | A context, abans | A context, després | A per possessió, abans | A per possessió, després |
|---|---|---|---|---|
| <1 s | 0.413 | 0.320 | 0.556 | 0.455 |
| 1-2 s | 0.552 | 0.493 | 0.644 | 0.573 |
| 2-5 s | 0.692 | 0.641 | 0.724 | 0.675 |
| 5-10 s | 0.866 | 0.835 | 0.846 | 0.820 |
| >10 s | 0.956 | 0.942 | 0.941 | 0.930 |

## Els decodificadors triats (cada partit, amb els altres nou)

- A context: λ = 4, durada mínima 12 · A per possessió: λ = 8, durada mínima 12 (9 partits)
- A context: λ = 2, durada mínima 25 · A per possessió: λ = 8, durada mínima 12 (1 partits)
