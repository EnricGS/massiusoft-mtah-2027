# PFF al costat del banc i de SkillCorner (pas 1 de la T3ab)

`codi/banc/pff_al_costat.py`. Dades obertes. Abans d'entrenar res (`docs/pla-tocs.md`, «T3ab»).

## Els partits de PFF que es deixen fora

- Cap.

## El tracking de PFF

- Minuts per part: de 46,0 a 59,0.
- Columnes de jugadors per equip: de 11 a 17.
- La pilota es veu a un 41 % de les imatges; X (la tele no ensenya el camp), un 40 % (de 29 % a 54 % per partit).

## La veritat

| | DFL, de sempre | DFL, de toc | Metrica, de sempre | Metrica, de toc | SkillCorner | PFF |
|---|---|---|---|---|---|---|
| Partits | 7 | 7 | 3 | 3 | 20 | 64 |
| D, de totes les imatges | 45 % | 45 % | 38 % | 38 % | 22 % | 8 % |
| X, de totes les imatges | 0 % | 0 % | 0 % | 0 % | 26 % | 40 % |
| D, de les que tenen veritat | 45 % | 45 % | 38 % | 38 % | 29 % | 14 % |
| Possessions per minut de pilota en joc | 8,3 | 8,7 | 5,9 | 6,1 | 6,2 | 8,1 |
| Durada mediana d'una possessió | 3,7 s | 3,4 s | 5,5 s | 5,1 s | 5,8 s | 4,1 s |
| Possessions de menys de 2 s | 30 % | 33 % | 22 % | 23 % | 22 % | 26 % |

## La taula de «Per què la T3l no hi arriba», mesurada de nou

| | DFL, de sempre | DFL, de toc | Metrica, de sempre | Metrica, de toc | SkillCorner | PFF |
|---|---|---|---|---|---|---|
| Al canvi d'equip, el jugador més proper a la pilota (a menys d'1,5 m) és del nou equip | 87 % | 85 % | 73 % | 72 % | 31 % | 54 % |
| El moment en què el nou equip és més a prop de la pilota, respecte del canvi (mediana) | +0,00 s | +0,00 s | +0,00 s | +0,00 s | +0,32 s | +0,04 s |
| Canvis amb aquest moment a ±0,2 s | 72 % | 74 % | 84 % | 82 % | 23 % | 37 % |
| Quan surt la pilota del camp, respecte de l'inici de la D (quartils) | −0,24 s a −0,08 s | −0,24 s a −0,08 s | −0,24 s a −0,04 s | −0,24 s a −0,04 s | −0,32 s a +1,44 s | −0,36 s a +0,04 s |
| Inicis de D amb la pilota que surt del camp a ±3 s | 68 % | 68 % | 63 % | 63 % | 50 % | 27 % |
| A la D, la pilota es veu | 100 % | 100 % | 4 % | 4 % | 45 % | 44 % |
| A la D, la velocitat de la pilota (mediana) | 0,0 m/s | 0,0 m/s | 0,1 m/s | 0,1 m/s | 1,5 m/s | 0,9 m/s |
| Amb la pilota a terra i en joc, el jugador més proper hi és a menys d'1 m | 47 % | 47 % | 54 % | 54 % | 34 % | 34 % |
| A les possessions de menys d'1 s, el jugador més proper (a menys d'1,5 m) és de l'equip de la veritat | 33 % | 35 % | 41 % | 42 % | 15 % | 25 % |

La de la T3l, per comparar-hi (`docs/pla-tocs.md`; mesurada llavors amb un altre codi):

| | DFL, de sempre | Metrica, de sempre | SkillCorner |
|---|---|---|---|
| Al canvi d'equip, el jugador més proper a la pilota (a menys d'1,5 m) és del nou equip | 87 % | 72 % | 31 % |
| El moment en què el nou equip és més a prop de la pilota, respecte del canvi (mediana) | 0 s | 0 s | 0,44 s després |
| Canvis amb aquest moment a ±0,2 s | 50 % | 77 % | 13 % |
| Quan surt la pilota del camp, respecte de l'inici de la D (quartils) | de 0,24 a 0,08 s abans | de 0,28 a 0,08 s abans | de 0,48 s abans a 1,4 s després |
| A la D, la pilota es veu (i com es mou) | sempre, quieta | gairebé mai (3 %) | la meitat, 1,5 m/s |
| Amb la pilota a terra i en joc, el jugador més proper hi és a menys d'1 m | 47 % | 54 % | 34 % |
| A les possessions de menys d'1 s, el jugador més proper (a menys d'1,5 m) és de l'equip de la veritat | 33 % | 41 % | 15 % |

## La tria

- Un partit del banc, de mitjana: 9975 imatges triades; nou partits, 89779.
- Els 64 de PFF, entre tots: 429832.
- **La part de les de PFF que es queda:** 0,2089.
