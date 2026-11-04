# FootAndBall a ISSIA-CNR, càmeres 5 i 6

Generat amb `uv run --with torch --with torchvision --with opencv-python-headless python -I -m
pilota.prova_issia`. Vídeo obert (`dades/FONT-issia.md`); cap dada del concurs. El model és el publicat,
entrenat amb les càmeres 1 a 4 (`dades/FONT-footandball.md`). Què es mesura: la capçalera de
`pilota/prova_issia.py`. **Trobada:** la candidata més probable passa del llindar i és a 10 px o
menys de la pilota marcada. **Error:** la mediana, en píxels del vídeo, de les trobades.

| càmera | imatge | llindar | marcades | trobada | entre les candidates | error (px) | sense marcar | en dona alguna sense marcar |
|---|---|---|---|---|---|---|---|---|
| 5 | ×1 | 0.1 | 327 | 86% | 87% | 2.1 | 2675 | 7% |
| 5 | ×1 | 0.3 | 327 | 83% | 83% | 2.1 | 2675 | 3% |
| 5 | ×1 | 0.5 | 327 | 81% | 81% | 2.1 | 2675 | 1% |
| 5 | ×1 | 0.7 | 327 | 78% | 78% | 2.1 | 2675 | 0% |
| 5 | ×1 | 0.9 | 327 | 75% | 75% | 2.1 | 2675 | 0% |
| 5 | ×0.5 | 0.1 | 327 | 0% | 0% | — | 2675 | 13% |
| 5 | ×0.5 | 0.3 | 327 | 0% | 0% | — | 2675 | 7% |
| 5 | ×0.5 | 0.5 | 327 | 0% | 0% | — | 2675 | 5% |
| 5 | ×0.5 | 0.7 | 327 | 0% | 0% | — | 2675 | 3% |
| 5 | ×0.5 | 0.9 | 327 | 0% | 0% | — | 2675 | 1% |
| 5 | ×0.5, ampliada ×2 | 0.1 | 327 | 82% | 82% | 2.5 | 2675 | 4% |
| 5 | ×0.5, ampliada ×2 | 0.3 | 327 | 78% | 78% | 2.5 | 2675 | 0% |
| 5 | ×0.5, ampliada ×2 | 0.5 | 327 | 76% | 76% | 2.5 | 2675 | 0% |
| 5 | ×0.5, ampliada ×2 | 0.7 | 327 | 73% | 73% | 2.5 | 2675 | 0% |
| 5 | ×0.5, ampliada ×2 | 0.9 | 327 | 65% | 65% | 2.5 | 2675 | 0% |
| 6 | ×1 | 0.1 | 253 | 96% | 96% | 2.9 | 2749 | 2% |
| 6 | ×1 | 0.3 | 253 | 96% | 96% | 2.9 | 2749 | 1% |
| 6 | ×1 | 0.5 | 253 | 96% | 96% | 2.9 | 2749 | 0% |
| 6 | ×1 | 0.7 | 253 | 94% | 94% | 2.9 | 2749 | 0% |
| 6 | ×1 | 0.9 | 253 | 92% | 92% | 2.9 | 2749 | 0% |
| 6 | ×0.5 | 0.1 | 253 | 30% | 31% | 5.8 | 2749 | 4% |
| 6 | ×0.5 | 0.3 | 253 | 16% | 16% | 5.1 | 2749 | 2% |
| 6 | ×0.5 | 0.5 | 253 | 11% | 11% | 5.0 | 2749 | 1% |
| 6 | ×0.5 | 0.7 | 253 | 7% | 7% | 5.0 | 2749 | 1% |
| 6 | ×0.5 | 0.9 | 253 | 2% | 2% | 3.0 | 2749 | 0% |
| 6 | ×0.5, ampliada ×2 | 0.1 | 253 | 96% | 96% | 3.5 | 2749 | 4% |
| 6 | ×0.5, ampliada ×2 | 0.3 | 253 | 95% | 95% | 3.5 | 2749 | 2% |
| 6 | ×0.5, ampliada ×2 | 0.5 | 253 | 95% | 95% | 3.5 | 2749 | 1% |
| 6 | ×0.5, ampliada ×2 | 0.7 | 253 | 94% | 94% | 3.5 | 2749 | 0% |
| 6 | ×0.5, ampliada ×2 | 0.9 | 253 | 89% | 89% | 3.5 | 2749 | 0% |
