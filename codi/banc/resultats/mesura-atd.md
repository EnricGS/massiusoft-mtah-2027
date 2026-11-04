# L'eina que mesura l'ATD: les referències i la validació

Fet amb `python -I -m banc.mesura_atd`, amb dades obertes. El pla i els criteris són a `docs/pla-mesura-atd.md`.

Partits: dfl-J03WMX, dfl-J03WN1, dfl-J03WOH, dfl-J03WOY, dfl-J03WPY, dfl-J03WQQ, dfl-J03WR9, metrica-1, metrica-2, metrica-3. Candidats de la pilota: 324 a cada partit de DFL i 108 a cada partit de Metrica; dels jugadors, 3 a cada partit de DFL.

## Si l'eina torna el candidat bo

Amb cada partit de DFL apartat, les referències fetes amb els altres 6 i cada candidat aplicat a l'apartat. El criteri: un 80 % o més, als casos en què l'eina tria cada pilota morta i viva.

En total: morta 100 %, viva 100 %, forats 100 %, aire 84 %, aglomeracio 66 %; perdua 95 % ✓.

| Pilota morta | Pilota viva | morta | viva | forats | aire | aglomeracio |
|---|---|---|---|---|---|---|
| tant com en joc (com DFL) | un 3 % (gairebé mai) | 100 % ✓ | 99 % ✓ | 100 % ✓ | 66 % ✗ | 53 % ✗ |
| tant com en joc (com DFL) | un 10 % | 100 % ✓ | 100 % ✓ | 100 % ✓ | 80 % ✓ | 60 % ✗ |
| tant com en joc (com DFL) | un 20 % | 100 % ✓ | 100 % ✓ | 100 % ✓ | 91 % ✓ | 72 % ✗ |
| tant com en joc (com DFL) | un 41 % (com el banc a DFL) | 100 % ✓ | 100 % ✓ | 100 % ✓ | 92 % ✓ | 81 % ✓ |
| més que en joc, però no sempre | un 3 % (gairebé mai) | 100 % ✓ | 100 % ✓ | 100 % ✓ | 68 % ✗ | 57 % ✗ |
| més que en joc, però no sempre | un 10 % | 99 % ✓ | 100 % ✓ | 100 % ✓ | 85 % ✓ | 66 % ✗ |
| més que en joc, però no sempre | un 20 % | 99 % ✓ | 100 % ✓ | 100 % ✓ | 94 % ✓ | 74 % ✗ |
| més que en joc, però no sempre | un 41 % (com el banc a DFL) | 97 % ✓ | 100 % ✓ | 100 % ✓ | 95 % ✓ | 79 % ✗ |
| gairebé sempre (com Metrica) | un 3 % (gairebé mai) | 100 % ✓ | 100 % ✓ | 96 % ✓ | 64 % ✗ | 48 % ✗ |
| gairebé sempre (com Metrica) | un 10 % | 100 % ✓ | 100 % ✓ | 99 % ✓ | 84 % ✓ | 54 % ✗ |
| gairebé sempre (com Metrica) | un 20 % | 100 % ✓ | 100 % ✓ | 100 % ✓ | 90 % ✓ | 71 % ✗ |
| gairebé sempre (com Metrica) | un 41 % (com el banc a DFL) | 100 % ✓ | 100 % ✓ | 100 % ✓ | 97 % ✓ | 82 % ✓ |

A Metrica, amb les referències de DFL, la pilota morta surt «gairebé sempre» en un 100 % dels 324 casos, i la viva encerta un 99 % (el criteri, un 80 %). La resta, a Metrica: morta 100 %, viva 99 %, forats 91 %, aire 58 %, aglomeracio 46 %.

Llindar de l'encaix (el percentil 95 de la distància al candidat triat, amb el partit apartat): pilota 21.8, jugadors 3.5.

## Les mesures de cada candidat (la mitjana dels partits de DFL)

Els candidats amb els pesos del banc (4 vegades més a l'aire i en aglomeracions):

| morta | viva | forats | falta_quiets | falta_corren | forats_fins_1s | forats_1_3s | forats_3_8s | forats_8_20s | forats_mes_20s | inici_rapida | inici_aglomeracio |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.410 | 0.030 | barreja | 0.470 | 0.037 | 0.120 | 0.289 | 0.339 | 0.218 | 0.034 | 0.016 | -0.306 |
| 0.410 | 0.030 | curts | 0.414 | 0.040 | 0.242 | 0.530 | 0.217 | 0.011 | 0.000 | 0.402 | 0.526 |
| 0.410 | 0.030 | llargs | 0.473 | 0.035 | 0.003 | 0.027 | 0.458 | 0.458 | 0.054 | 0.145 | -0.878 |
| 0.410 | 0.100 | barreja | 0.439 | 0.114 | 0.090 | 0.221 | 0.351 | 0.307 | 0.031 | 0.624 | -0.089 |
| 0.410 | 0.100 | curts | 0.410 | 0.108 | 0.252 | 0.561 | 0.180 | 0.008 | 0.000 | 0.655 | 0.711 |
| 0.410 | 0.100 | llargs | 0.481 | 0.106 | 0.003 | 0.008 | 0.385 | 0.520 | 0.084 | 0.454 | 0.844 |
| 0.410 | 0.200 | barreja | 0.456 | 0.221 | 0.086 | 0.219 | 0.320 | 0.323 | 0.051 | 0.747 | 0.874 |
| 0.410 | 0.200 | curts | 0.410 | 0.212 | 0.237 | 0.554 | 0.203 | 0.006 | 0.000 | 0.709 | 0.822 |
| 0.410 | 0.200 | llargs | 0.446 | 0.206 | 0.002 | 0.008 | 0.325 | 0.578 | 0.087 | 0.524 | 0.343 |
| 0.410 | 0.410 | barreja | 0.466 | 0.432 | 0.065 | 0.155 | 0.285 | 0.407 | 0.088 | 0.786 | 0.755 |
| 0.410 | 0.410 | curts | 0.416 | 0.419 | 0.184 | 0.500 | 0.307 | 0.009 | 0.000 | 0.838 | 0.830 |
| 0.410 | 0.410 | llargs | 0.502 | 0.434 | 0.001 | 0.005 | 0.241 | 0.495 | 0.258 | 0.690 | 0.401 |
| 0.600 | 0.030 | barreja | 0.642 | 0.047 | 0.106 | 0.241 | 0.334 | 0.273 | 0.046 | 0.136 | 0.246 |
| 0.600 | 0.030 | curts | 0.590 | 0.046 | 0.187 | 0.433 | 0.350 | 0.029 | 0.000 | 0.274 | 0.763 |
| 0.600 | 0.030 | llargs | 0.668 | 0.037 | 0.004 | 0.031 | 0.398 | 0.498 | 0.069 | -0.097 | -0.802 |
| 0.600 | 0.100 | barreja | 0.643 | 0.115 | 0.085 | 0.218 | 0.339 | 0.308 | 0.049 | 0.356 | 0.531 |
| 0.600 | 0.100 | curts | 0.587 | 0.117 | 0.189 | 0.478 | 0.309 | 0.024 | 0.000 | 0.537 | 0.647 |
| 0.600 | 0.100 | llargs | 0.665 | 0.111 | 0.003 | 0.018 | 0.318 | 0.586 | 0.075 | 0.482 | 0.399 |
| 0.600 | 0.200 | barreja | 0.646 | 0.215 | 0.082 | 0.205 | 0.347 | 0.326 | 0.039 | 0.613 | 0.708 |
| 0.600 | 0.200 | curts | 0.592 | 0.216 | 0.197 | 0.511 | 0.268 | 0.024 | 0.000 | 0.614 | 0.867 |
| 0.600 | 0.200 | llargs | 0.693 | 0.219 | 0.002 | 0.008 | 0.283 | 0.591 | 0.116 | 0.507 | 0.772 |
| 0.600 | 0.410 | barreja | 0.644 | 0.445 | 0.069 | 0.169 | 0.274 | 0.389 | 0.099 | 0.653 | 0.734 |
| 0.600 | 0.410 | curts | 0.600 | 0.431 | 0.175 | 0.451 | 0.354 | 0.021 | 0.000 | 0.801 | 0.812 |
| 0.600 | 0.410 | llargs | 0.704 | 0.456 | 0.001 | 0.005 | 0.231 | 0.540 | 0.222 | 0.685 | 0.174 |
| 0.970 | 0.030 | barreja | 0.957 | 0.061 | 0.039 | 0.097 | 0.237 | 0.425 | 0.203 | -0.339 | 0.386 |
| 0.970 | 0.030 | curts | 0.946 | 0.063 | 0.067 | 0.155 | 0.284 | 0.385 | 0.110 | 0.324 | 0.319 |
| 0.970 | 0.030 | llargs | 0.961 | 0.053 | 0.001 | 0.021 | 0.184 | 0.480 | 0.315 | -0.891 | 0.211 |
| 0.970 | 0.100 | barreja | 0.958 | 0.132 | 0.056 | 0.118 | 0.272 | 0.330 | 0.224 | 0.372 | 0.686 |
| 0.970 | 0.100 | curts | 0.945 | 0.131 | 0.118 | 0.271 | 0.243 | 0.284 | 0.085 | 0.561 | 0.675 |
| 0.970 | 0.100 | llargs | 0.961 | 0.137 | 0.000 | 0.013 | 0.232 | 0.486 | 0.268 | -0.112 | -1.152 |
| 0.970 | 0.200 | barreja | 0.964 | 0.242 | 0.061 | 0.157 | 0.284 | 0.345 | 0.152 | 0.495 | 0.502 |
| 0.970 | 0.200 | curts | 0.950 | 0.234 | 0.136 | 0.357 | 0.234 | 0.224 | 0.050 | 0.594 | 0.868 |
| 0.970 | 0.200 | llargs | 0.964 | 0.226 | 0.001 | 0.009 | 0.257 | 0.476 | 0.258 | 0.334 | -0.233 |
| 0.970 | 0.410 | barreja | 0.970 | 0.445 | 0.057 | 0.139 | 0.262 | 0.348 | 0.193 | 0.576 | 0.765 |
| 0.970 | 0.410 | curts | 0.955 | 0.450 | 0.130 | 0.350 | 0.308 | 0.171 | 0.041 | 0.777 | 0.730 |
| 0.970 | 0.410 | llargs | 0.969 | 0.447 | 0.000 | 0.003 | 0.188 | 0.454 | 0.353 | 0.651 | -0.037 |

Els jugadors:

| perdua | peces_fins_2s | peces_2_10s | peces_10_60s | peces_mes_60s |
|---|---|---|---|---|
| 0.2-2 | 0.008 | 0.124 | 0.726 | 0.142 |
| 0.5-10 | 0.001 | 0.011 | 0.176 | 0.811 |
| 2-30 | 0.001 | 0.005 | 0.029 | 0.965 |
