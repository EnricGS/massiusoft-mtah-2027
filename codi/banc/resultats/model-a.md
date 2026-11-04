# Banc obert · el model A

Generat amb `uv run python -I -m banc.model_a`. Dades obertes: 7 partits de DFL (IDSSE, CC BY 4.0) i
els 3 de mostra de Metrica, deixant cada partit fora. Cap dada del concurs.

**spellF1** (mitjana dels partits de cada font)

| mètode | net dfl | net metrica | net tots | curts dfl | curts metrica | curts tots | llargs dfl | llargs metrica | llargs tots | barreja dfl | barreja metrica | barreja tots | aire dfl | aire metrica | aire tots | soroll2 dfl | soroll2 metrica | soroll2 tots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 0.499 | 0.573 | 0.521 | 0.514 | 0.604 | 0.541 | 0.471 | 0.579 | 0.504 | 0.495 | 0.592 | 0.524 | 0.428 | 0.592 | 0.477 | 0.311 | 0.431 | 0.347 |
| smooth125·X | 0.299 | 0.382 | 0.324 | 0.219 | 0.287 | 0.240 | 0.185 | 0.231 | 0.199 | 0.202 | 0.227 | 0.209 | 0.197 | 0.236 | 0.209 | 0.156 | 0.182 | 0.164 |
| smooth50·X | 0.300 | 0.339 | 0.312 | 0.178 | 0.201 | 0.185 | 0.173 | 0.204 | 0.182 | 0.182 | 0.186 | 0.183 | 0.183 | 0.186 | 0.184 | 0.129 | 0.141 | 0.132 |

**macroF1** (mitjana dels partits de cada font)

| mètode | net dfl | net metrica | net tots | curts dfl | curts metrica | curts tots | llargs dfl | llargs metrica | llargs tots | barreja dfl | barreja metrica | barreja tots | aire dfl | aire metrica | aire tots | soroll2 dfl | soroll2 metrica | soroll2 tots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 0.862 | 0.868 | 0.864 | 0.885 | 0.900 | 0.890 | 0.864 | 0.888 | 0.871 | 0.870 | 0.890 | 0.876 | 0.840 | 0.892 | 0.855 | 0.630 | 0.742 | 0.663 |
| smooth125·X | 0.393 | 0.547 | 0.439 | 0.363 | 0.502 | 0.405 | 0.329 | 0.429 | 0.359 | 0.342 | 0.456 | 0.376 | 0.343 | 0.450 | 0.375 | 0.327 | 0.420 | 0.355 |
| smooth50·X | 0.385 | 0.552 | 0.435 | 0.342 | 0.475 | 0.382 | 0.306 | 0.399 | 0.334 | 0.321 | 0.424 | 0.352 | 0.323 | 0.418 | 0.352 | 0.300 | 0.387 | 0.326 |

**A contra smooth125·X** (spellF1; «clarament»: la diferència passa de 0.04 i l'interval
del 95 %, triant partits dins de cada font, no toca el zero)

| escenari | A | referència | diferència | interval del 95 % | A guanya | clarament |
|---|---|---|---|---|---|---|
| net | 0.521 | 0.324 | +0.198 | +0.178 a +0.218 | 10 de 10 | sí |
| curts | 0.541 | 0.240 | +0.301 | +0.286 a +0.317 | 10 de 10 | sí |
| llargs | 0.504 | 0.199 | +0.305 | +0.287 a +0.323 | 10 de 10 | sí |
| barreja | 0.524 | 0.209 | +0.315 | +0.299 a +0.330 | 10 de 10 | sí |
| aire | 0.477 | 0.209 | +0.268 | +0.253 a +0.282 | 10 de 10 | sí |
| soroll2 | 0.347 | 0.164 | +0.183 | +0.163 a +0.203 | 10 de 10 | sí |

**A contra smooth50·X** (spellF1; «clarament»: la diferència passa de 0.04 i l'interval
del 95 %, triant partits dins de cada font, no toca el zero)

| escenari | A | referència | diferència | interval del 95 % | A guanya | clarament |
|---|---|---|---|---|---|---|
| net | 0.521 | 0.312 | +0.210 | +0.183 a +0.235 | 10 de 10 | sí |
| curts | 0.541 | 0.185 | +0.356 | +0.336 a +0.374 | 10 de 10 | sí |
| llargs | 0.504 | 0.182 | +0.322 | +0.301 a +0.343 | 10 de 10 | sí |
| barreja | 0.524 | 0.183 | +0.341 | +0.322 a +0.359 | 10 de 10 | sí |
| aire | 0.477 | 0.184 | +0.293 | +0.274 a +0.310 | 10 de 10 | sí |
| soroll2 | 0.347 | 0.132 | +0.215 | +0.193 a +0.234 | 10 de 10 | sí |

**El decodificador**

- Triat amb cada partit fora: λ = 8 i durada mínima 25 en 10 partits.
- Amb els deu partits (el de la cadena): λ = 8, durada mínima = 25.
- Possessions predites per cada possessió real, de mitjana: net 0.71, curts 0.68, llargs 0.66, barreja 0.66, aire 0.69, soroll2 0.92.

*Ni el model ni el decodificador d'un partit no l'han vist. Els models dels altres partits, amb què
es tria el decodificador, sí que l'han tingut a l'entrenament: és l'única drecera, i només toca dos
números (λ i la durada mínima).*
