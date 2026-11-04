# Open data

Nothing here is committed. Put here the open data you need, and **never the data bundle of the challenge**.

**To reproduce the submission file, you need none of it:** the model is in the repository.

## Metrica sample data (the tests, and the bench)

```bash
git clone https://github.com/metrica-sports/sample-data dades/metrica-sample
git -C dades/metrica-sample checkout e706dd506b360d69d9d123d5b8026e7294b13996
```

The commit is the one we used. Run these from the root of the repository.

## DFL/IDSSE (the bench, and retraining the model)

Seven matches of the 2022/23 Bundesliga 1 and 2: positions of every player and the ball at 25 frames per second,
with `BallStatus` (alive or dead) and `BallPossession` (home or away) on every frame, and the event data, which
the first-touch labels and the simulated Smart Tagging use. About 2.4 GB.

```bash
python3 -I codi/banc/baixa_idsse.py dades/idsse
```

It downloads revision `a715a38` of the copy that kloppy uses (`pysport/idsse-data` on Hugging Face), the one we
used, and checks every file against the fingerprint the API reports.

Source: Bassek, M., Rein, R., Weber, H. et al. "An integrated dataset of spatiotemporal and event data in elite
soccer". *Scientific Data* 12, 195 (2025). https://doi.org/10.1038/s41597-025-04505-y. Licence CC BY 4.0.

## FootAndBall and ISSIA-CNR (only `codi/pilota/`)

The pipeline does not use them. `codi/pilota/valida.py` (the check of TECHNICAL.md §2) needs FootAndBall, and
`codi/pilota/prova_issia.py`, which measures FootAndBall on open video to set the check's thresholds, needs
ISSIA-CNR. Both also need PyTorch, torchvision and OpenCV, which are not in `uv.lock`: the commands add them with
`uv run --with torch --with torchvision --with opencv-python-headless`.

```bash
git clone https://github.com/jac99/FootAndBall dades/footandball/repo
git -C dades/footandball/repo checkout 01261092a93de55026745e532a2e12188ad86801
```

The model we used, `models/model_20201019_1416_final.pth`, has the sha256
`42fbc1f457fc34d804b403e26138524fc40facde303ccd7b4be73121e8da4cd5`, and `codi/pilota/footandball.py` checks it
before loading it. Source: Komorowski, J., Kurzejamski, G., Sarwas, G. "FootAndBall: Integrated Player and Ball
Detector". VISAPP 2020. MIT.

ISSIA-CNR (D'Orazio, T. et al., AVSS 2009) goes in `dades/issia/`, from the copy linked in FootAndBall's README. We
found no licence text for it, so it is only used to test, and nothing in the submission depends on it.

## SkillCorner (only one dropped step of the bench)

Twenty matches of the 2024/25 A-League, with SkillCorner's broadcast tracking at 10 frames per second. Only
`banc.model_a_skillcorner` uses them, a step we dropped (TECHNICAL.md §3): the model is not trained on them. About
1.9 GB.

```bash
python3 -I codi/banc/baixa_skillcorner.py dades/skillcorner
```

It downloads revision `4340d274572876239c154c90bc507a9b3250a656` of github.com/SkillCorner/opendata, the one we
used, and checks every file against its fingerprint. Licence MIT (© 2020 SkillCorner).

## PFF FC (only one closed step of the bench)

The 64 matches of the FIFA World Cup 2022, with the broadcast tracking of Sportlogiq and PFF FC's events. Only
`banc.pff_al_costat` uses them, a step we closed before training anything (TECHNICAL.md §3): the model is not trained
on them. PFF FC, now Gradient Sports, gives them through the form at
https://www.blog.fc.pff.com/blog/pff-fc-release-2022-world-cup-data, which leads to a shared folder. We found no
licence text for them. `codi/banc/pff.py` reads that folder's `tracking/`, `event-data/` and `metadata/` from
`dades/pff/`. About 3.7 GB.

## The bench cache

`dades/banc/` is written by the bench the first time it runs: the ten matches in a common structure, and the
model probabilities. You can delete it at any time.
