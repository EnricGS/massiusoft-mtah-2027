# Banc obert · les línies base

Generat amb `uv run python -I -m banc`. Dades obertes: 7 partits de DFL (IDSSE, CC BY 4.0) i els 3 de
mostra de Metrica. Mitjana dels partits de cada font. Cap dada del concurs.

## Sense pilota, X

**spellF1**

| línia base | net dfl | net metrica | net tots | curts dfl | curts metrica | curts tots | llargs dfl | llargs metrica | llargs tots | barreja dfl | barreja metrica | barreja tots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| raw | 0.098 | 0.085 | 0.094 | 0.047 | 0.047 | 0.047 | 0.032 | 0.033 | 0.032 | 0.036 | 0.036 | 0.036 |
| smooth25 | 0.207 | 0.200 | 0.205 | 0.138 | 0.150 | 0.142 | 0.126 | 0.142 | 0.131 | 0.131 | 0.134 | 0.132 |
| smooth50 | 0.300 | 0.339 | 0.312 | 0.178 | 0.201 | 0.185 | 0.173 | 0.204 | 0.182 | 0.182 | 0.186 | 0.183 |
| smooth125 | 0.299 | 0.382 | 0.324 | 0.219 | 0.287 | 0.240 | 0.185 | 0.231 | 0.199 | 0.202 | 0.227 | 0.209 |

**macroF1**

| línia base | net dfl | net metrica | net tots | curts dfl | curts metrica | curts tots | llargs dfl | llargs metrica | llargs tots | barreja dfl | barreja metrica | barreja tots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| raw | 0.364 | 0.529 | 0.413 | 0.283 | 0.369 | 0.309 | 0.279 | 0.361 | 0.304 | 0.282 | 0.367 | 0.307 |
| smooth25 | 0.374 | 0.538 | 0.423 | 0.321 | 0.438 | 0.356 | 0.292 | 0.380 | 0.318 | 0.302 | 0.400 | 0.331 |
| smooth50 | 0.385 | 0.552 | 0.435 | 0.342 | 0.475 | 0.382 | 0.306 | 0.399 | 0.334 | 0.321 | 0.424 | 0.352 |
| smooth125 | 0.393 | 0.547 | 0.439 | 0.363 | 0.502 | 0.405 | 0.329 | 0.429 | 0.359 | 0.342 | 0.456 | 0.376 |

**L'ordre per spellF1** (publicat: smooth50 > smooth125 > smooth25 > raw)

| escenari | font | ordre | parelles com al publicat | smooth50 > raw (partits) |
|---|---|---|---|---|
| net | dfl | smooth50 > smooth125 > smooth25 > raw | 6 de 6 | 7 de 7 |
| net | metrica | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 3 de 3 |
| net | tots | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 10 de 10 |
| curts | dfl | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 7 de 7 |
| curts | metrica | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 3 de 3 |
| curts | tots | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 10 de 10 |
| llargs | dfl | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 7 de 7 |
| llargs | metrica | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 3 de 3 |
| llargs | tots | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 10 de 10 |
| barreja | dfl | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 7 de 7 |
| barreja | metrica | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 3 de 3 |
| barreja | tots | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 10 de 10 |

## Sense pilota, D

**spellF1**

| línia base | net dfl | net metrica | net tots | curts dfl | curts metrica | curts tots | llargs dfl | llargs metrica | llargs tots | barreja dfl | barreja metrica | barreja tots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| raw | 0.098 | 0.106 | 0.101 | 0.013 | 0.016 | 0.014 | 0.022 | 0.030 | 0.024 | 0.020 | 0.024 | 0.021 |
| smooth25 | 0.207 | 0.256 | 0.222 | 0.049 | 0.070 | 0.056 | 0.096 | 0.141 | 0.109 | 0.080 | 0.108 | 0.088 |
| smooth50 | 0.300 | 0.453 | 0.346 | 0.091 | 0.125 | 0.101 | 0.144 | 0.223 | 0.167 | 0.132 | 0.175 | 0.145 |
| smooth125 | 0.299 | 0.557 | 0.376 | 0.135 | 0.185 | 0.150 | 0.164 | 0.279 | 0.198 | 0.168 | 0.247 | 0.192 |

**macroF1**

| línia base | net dfl | net metrica | net tots | curts dfl | curts metrica | curts tots | llargs dfl | llargs metrica | llargs tots | barreja dfl | barreja metrica | barreja tots |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| raw | 0.364 | 0.854 | 0.511 | 0.429 | 0.614 | 0.485 | 0.441 | 0.607 | 0.491 | 0.438 | 0.611 | 0.490 |
| smooth25 | 0.374 | 0.870 | 0.523 | 0.434 | 0.620 | 0.490 | 0.448 | 0.617 | 0.499 | 0.445 | 0.621 | 0.498 |
| smooth50 | 0.385 | 0.890 | 0.537 | 0.438 | 0.633 | 0.496 | 0.456 | 0.626 | 0.507 | 0.455 | 0.632 | 0.508 |
| smooth125 | 0.393 | 0.901 | 0.545 | 0.445 | 0.624 | 0.499 | 0.465 | 0.630 | 0.515 | 0.465 | 0.641 | 0.518 |

**L'ordre per spellF1** (publicat: smooth50 > smooth125 > smooth25 > raw)

| escenari | font | ordre | parelles com al publicat | smooth50 > raw (partits) |
|---|---|---|---|---|
| net | dfl | smooth50 > smooth125 > smooth25 > raw | 6 de 6 | 7 de 7 |
| net | metrica | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 3 de 3 |
| net | tots | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 10 de 10 |
| curts | dfl | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 7 de 7 |
| curts | metrica | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 3 de 3 |
| curts | tots | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 10 de 10 |
| llargs | dfl | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 7 de 7 |
| llargs | metrica | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 3 de 3 |
| llargs | tots | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 10 de 10 |
| barreja | dfl | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 7 de 7 |
| barreja | metrica | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 3 de 3 |
| barreja | tots | smooth125 > smooth50 > smooth25 > raw | 5 de 6 | 10 de 10 |

## Com queden els partits a cada escenari

Mitjana dels partits de cada font. La pilota absent és dels fotogrames puntuats.

| escenari | font | pilota absent | amb la pilota viva | amb la pilota morta | objectes vistos | slots |
|---|---|---|---|---|---|---|
| net | dfl | 0.0% | 0.0% | 0.0% | 21.8 | 31 |
| net | metrica | 37.5% | 0.7% | 96.7% | 22.0 | 30 |
| curts | dfl | 41.7% | 41.0% | 42.5% | 20.5 | 46 |
| curts | metrica | 62.4% | 41.0% | 96.9% | 20.5 | 46 |
| llargs | dfl | 44.2% | 41.0% | 48.1% | 20.5 | 46 |
| llargs | metrica | 62.5% | 41.0% | 97.2% | 20.5 | 46 |
| barreja | dfl | 43.4% | 41.0% | 46.3% | 20.5 | 46 |
| barreja | metrica | 62.4% | 41.0% | 96.9% | 20.5 | 46 |
