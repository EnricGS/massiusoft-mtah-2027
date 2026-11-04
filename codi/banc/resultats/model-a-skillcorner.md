# Banc obert · Més partits per entrenar, els de SkillCorner (T3l)

Generat amb `uv run python -I -m banc.model_a_skillcorner`. Dades obertes: es proven els 7 partits de DFL
(IDSSE, CC BY 4.0) i els 3 de mostra de Metrica, deixant cada partit fora; s'entrena també amb els 20 de
SkillCorner Open Data (A-League 2024/25, MIT), que no es proven mai. Cap dada del concurs. Com es fa i el
criteri: `docs/pla-tocs.md`, «T3l», i la capçalera de `banc/model_a_skillcorner.py`.

**A context** és el model de la cadena (T3e), amb el decodificador d'ara. **A aturades** és el de la
T3k. **A amb SkillCorner** és A aturades amb tots els models entrenats també amb SkillCorner. Tots tenen
els paràmetres del decodificador triats amb els altres nou partits als escenaris ×¼.

## L'spellF1 i el macroF1 de cada mètode (mitjana dels deu partits)

**spellF1**

| escenari | A context | A aturades | A amb SkillCorner |
|---|---|---|---|
| net | 0.775 | 0.801 | 0.789 |
| curts ×¼ | 0.639 | 0.659 | 0.632 |
| llargs ×¼ | 0.621 | 0.648 | 0.617 |
| barreja ×¼ | 0.631 | 0.661 | 0.635 |
| aire ×¼ | 0.556 | 0.585 | 0.516 |
| curts | 0.583 | 0.601 | 0.521 |
| llargs | 0.547 | 0.568 | 0.500 |
| barreja | 0.562 | 0.579 | 0.516 |
| aire | 0.508 | 0.526 | 0.466 |
| soroll2 | 0.373 | 0.388 | 0.381 |

**macroF1**

| escenari | A context | A aturades | A amb SkillCorner |
|---|---|---|---|
| net | 0.952 | 0.953 | 0.951 |
| curts ×¼ | 0.919 | 0.921 | 0.916 |
| llargs ×¼ | 0.906 | 0.906 | 0.902 |
| barreja ×¼ | 0.910 | 0.912 | 0.908 |
| aire ×¼ | 0.886 | 0.890 | 0.861 |
| curts | 0.902 | 0.901 | 0.887 |
| llargs | 0.885 | 0.882 | 0.872 |
| barreja | 0.886 | 0.888 | 0.877 |
| aire | 0.865 | 0.868 | 0.841 |
| soroll2 | 0.697 | 0.694 | 0.743 |

## A amb SkillCorner contra A context (spellF1): el criteri

| escenari | A context | A amb SkillCorner | diferència | interval del 95 % | A amb SkillCorner guanya | criteri | |
|---|---|---|---|---|---|---|---|
| net | 0.775 | 0.789 | +0.014 | +0.003 a +0.025 | 8 de 10 | no perd | ✓ |
| curts ×¼ | 0.639 | 0.632 | -0.007 | -0.017 a +0.003 | 3 de 10 | guanya clarament | ✗ |
| llargs ×¼ | 0.621 | 0.617 | -0.004 | -0.016 a +0.007 | 5 de 10 | guanya clarament | ✗ |
| barreja ×¼ | 0.631 | 0.635 | +0.004 | -0.007 a +0.014 | 6 de 10 | guanya clarament | ✗ |
| aire ×¼ | 0.556 | 0.516 | -0.040 | -0.050 a -0.029 | 3 de 10 | guanya clarament | ✗ |
| curts | 0.583 | 0.521 | -0.062 | -0.072 a -0.052 | 0 de 10 | no perd | ✗ |
| llargs | 0.547 | 0.500 | -0.047 | -0.060 a -0.036 | 1 de 10 | no perd | ✗ |
| barreja | 0.562 | 0.516 | -0.046 | -0.058 a -0.033 | 0 de 10 | no perd | ✗ |
| aire | 0.508 | 0.466 | -0.042 | -0.055 a -0.031 | 0 de 10 | no perd | ✗ |
| soroll2 | 0.373 | 0.381 | +0.008 | -0.007 a +0.023 | 6 de 10 | no perd | ✓ |

| | Passa si | |
|---|---|---|
| Els quatre escenaris ×¼ | guanya clarament a cada un (diferència > 0.04, interval > 0, 8 partits de 10 o més) | ✗ |
| El net, els ×1 i el soroll2 | no perd a cap (diferència ≥ −0.04) | ✗ |

**No passa.**

## A amb SkillCorner contra A aturades (spellF1), només per saber-ho

El mateix, sense els partits de SkillCorner: la diferència és el que hi afegeixen.

| escenari | A aturades | A amb SkillCorner | diferència | interval del 95 % | A amb SkillCorner guanya |
|---|---|---|---|---|---|
| net | 0.801 | 0.789 | -0.013 | -0.020 a -0.005 | 1 de 10 |
| curts ×¼ | 0.659 | 0.632 | -0.027 | -0.035 a -0.018 | 1 de 10 |
| llargs ×¼ | 0.648 | 0.617 | -0.030 | -0.043 a -0.018 | 0 de 10 |
| barreja ×¼ | 0.661 | 0.635 | -0.026 | -0.033 a -0.020 | 0 de 10 |
| aire ×¼ | 0.585 | 0.516 | -0.069 | -0.089 a -0.050 | 1 de 10 |
| curts | 0.601 | 0.521 | -0.080 | -0.093 a -0.066 | 0 de 10 |
| llargs | 0.568 | 0.500 | -0.067 | -0.080 a -0.056 | 0 de 10 |
| barreja | 0.579 | 0.516 | -0.064 | -0.079 a -0.051 | 0 de 10 |
| aire | 0.526 | 0.466 | -0.060 | -0.076 a -0.047 | 0 de 10 |
| soroll2 | 0.388 | 0.381 | -0.007 | -0.024 a +0.007 | 5 de 10 |

## Per font (spellF1, mitjana dels partits de cada font), només per saber-ho

| escenari | font | A context | A aturades | A amb SkillCorner |
|---|---|---|---|---|
| net | dfl | 0.754 | 0.778 | 0.766 |
| net | metrica | 0.825 | 0.857 | 0.841 |
| curts ×¼ | dfl | 0.611 | 0.632 | 0.604 |
| curts ×¼ | metrica | 0.705 | 0.721 | 0.698 |
| llargs ×¼ | dfl | 0.594 | 0.617 | 0.585 |
| llargs ×¼ | metrica | 0.686 | 0.719 | 0.693 |
| barreja ×¼ | dfl | 0.604 | 0.636 | 0.604 |
| barreja ×¼ | metrica | 0.692 | 0.718 | 0.705 |
| aire ×¼ | dfl | 0.499 | 0.528 | 0.435 |
| aire ×¼ | metrica | 0.690 | 0.719 | 0.706 |
| curts | dfl | 0.560 | 0.574 | 0.491 |
| curts | metrica | 0.636 | 0.664 | 0.590 |
| llargs | dfl | 0.518 | 0.532 | 0.459 |
| llargs | metrica | 0.615 | 0.650 | 0.595 |
| barreja | dfl | 0.533 | 0.551 | 0.487 |
| barreja | metrica | 0.628 | 0.645 | 0.582 |
| aire | dfl | 0.454 | 0.473 | 0.407 |
| aire | metrica | 0.636 | 0.649 | 0.604 |
| soroll2 | dfl | 0.321 | 0.343 | 0.353 |
| soroll2 | metrica | 0.493 | 0.492 | 0.446 |

## L'encert de l'equip abans de decodificar (escenaris ×¼), només per saber-ho

A les imatges de les possessions de la veritat, la part on l'equip més probable és el de la veritat,
per durada de la possessió i segons si la pilota es veu.

| durada | pilota | A aturades | A amb SkillCorner |
|---|---|---|---|
| <1 s | no | 0.381 | 0.287 |
| <1 s | sí | 0.659 | 0.593 |
| 1-2 s | no | 0.511 | 0.443 |
| 1-2 s | sí | 0.716 | 0.665 |
| 2-5 s | no | 0.609 | 0.548 |
| 2-5 s | sí | 0.779 | 0.730 |
| ≥5 s | no | 0.863 | 0.864 |
| ≥5 s | sí | 0.947 | 0.939 |

## La veritat de cada font (els partits nets), només per saber-ho

*Sense veritat*: la part de les imatges de les parts que no es puntua ni s'aprèn (a SkillCorner, sobretot
les repeticions de la retransmissió, on no hi ha cap jugador). La resta, sobre les que tenen veritat.

| font | partits | sense veritat | pilota morta | possessions per minut | durada mediana (s) | de menys de 2 s | pilota vista, en joc |
|---|---|---|---|---|---|---|---|
| dfl | 7 | 0.000 | 0.449 | 4.58 | 3.77 | 0.296 | 1.000 |
| metrica | 3 | 0.000 | 0.384 | 3.63 | 5.50 | 0.215 | 0.993 |
| skillcorner | 20 | 0.261 | 0.292 | 4.43 | 5.87 | 0.219 | 0.946 |

## Possessions predites per cada real (mitjana dels deu partits), només per saber-ho

| escenari | A context | A aturades | A amb SkillCorner |
|---|---|---|---|
| net | 0.83 | 0.92 | 0.90 |
| curts ×¼ | 0.74 | 0.83 | 0.79 |
| llargs ×¼ | 0.73 | 0.81 | 0.78 |
| barreja ×¼ | 0.72 | 0.81 | 0.77 |
| aire ×¼ | 0.72 | 0.79 | 0.63 |
| curts | 0.72 | 0.82 | 0.61 |
| llargs | 0.68 | 0.77 | 0.59 |
| barreja | 0.70 | 0.79 | 0.61 |
| aire | 0.69 | 0.75 | 0.59 |
| soroll2 | 1.03 | 1.07 | 0.73 |

## Els paràmetres triats (cada partit, amb els altres nou)

- A context: λ = 4, durada mínima 12 · A aturades: w = 4, λ = 32, durada mínima 12 · A amb SkillCorner: w = 2, λ = 16, durada mínima 25 (7 partits)
- A context: λ = 2, durada mínima 25 · A aturades: w = 4, λ = 32, durada mínima 12 · A amb SkillCorner: w = 2, λ = 16, durada mínima 25 (1 partits)
- A context: λ = 4, durada mínima 12 · A aturades: w = 4, λ = 32, durada mínima 12 · A amb SkillCorner: w = 2, λ = 8, durada mínima 25 (1 partits)
- A context: λ = 4, durada mínima 12 · A aturades: w = 4, λ = 16, durada mínima 12 · A amb SkillCorner: w = 2, λ = 16, durada mínima 25 (1 partits)
