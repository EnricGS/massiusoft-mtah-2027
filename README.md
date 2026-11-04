# Team possession per video frame · More than a Hack 2027, Phase 1

This repository turns the provided **tactical ATD** (automatic tracking data) and **Smart Tagging** of the match into
the possession file of the challenge: one label per frame of the tactical video, `H`, `A`, `D` or `X`. It is
everything needed to go from the data bundle to our submission, and it regenerates the same file, byte for byte.

**How it works, in one paragraph.** A ball seen far outside the pitch is treated as missing. Each video frame then
gets 152 collective signals from the tracking: where the ball is, which team is closest to it and by how much, how
each team's block sits and moves, which team touched the ball last and will touch it next, which team was last in
contact with it, whether the ball moves with a player of either team, and, when the ball is missing, how things
looked the last time it was seen and the next time it is. A first LightGBM classifier turns them into P(H), P(A) and
P(D). Five small neural networks read the positions themselves: the ball (or, where it is missing, an estimate of
it), the three players of each team nearest to it, and both whole teams, each seen four ways (as is, with the teams
swapped, with the pitch flipped, and both). A second classifier looks at the first one's probabilities up to 5 s
around each frame, at the networks' and at signs of a stoppage, and gives the final ones. A third one, the change
model, gives the probability q that the team changes there. The Smart Tagging then adds its evidence: dead ball before
each tagged set piece, and, inside each tagged phase of a team (Build Up, Progression…), less for the other team. A
Viterbi decoder turns all of it into whole possessions: switching team costs less where q is high, going in or out of
dead ball costs a fixed penalty, and every possession but the first and the last of a half lasts at least 12 frames.
Everything was trained and tuned **only on open data**: 7 matches of the DFL/IDSSE dataset and the 3 Metrica sample
games, degraded to look like the ATD, with a simulated Smart Tagging. No label of the provided match was used; one
measurement of its tracking set the position error of half the training scenarios. [TECHNICAL.md](TECHNICAL.md) says
exactly what we took from the match, and has the details.

The code, its comments and its console messages are in Catalan. This README and the technical document are in
English.

## Layout

| Path | What |
|---|---|
| `codi/cadena/` | The command that writes the possession file (`python -I -m cadena`), and the pieces it runs: reading the ATD and the Smart Tagging (`llegeix.py`, `smart_tagging.py`, `smart_tagging_fases.py`), the credible ball (`pilota_creible.py`), the signals (`senyals.py`, `tocs.py`, `control.py`, `contacte.py`, `context.py`, `aturades.py`), the networks (`xarxa.py`, `xarxes.py`, `xarxa_sense_pilota.py`, `xarxa_equips.py`, `xarxa_girada.py`), the classifiers (`model.py`), the Smart Tagging evidence (`pilota_morta.py`, `fases.py`), the decoder (`decodifica_canvis.py`), the whole model (`opcio_girat.py`) and the checks |
| `codi/cadena/model-girat/` | The trained model: the first classifier (`primer.txt`), the second (`segon.txt`), the change model (`canvis.txt`), the five networks (`xarxa-0.npz` to `xarxa-4.npz`, plain arrays) and their record (`fitxa.json`: prior, decoder and Smart Tagging settings, signal columns, provenance, code key and fingerprint) |
| `codi/cadena/model-a/` | The model of our previous submission, in the same form. The pipeline does not use it; its tests do |
| `codi/banc/` | The open bench: the open matches in a common structure, the first-touch labels, the degradation scenarios, the simulated Smart Tagging, leave-one-match-out evaluation with the official metric, the baselines, each step of the method, and the scripts that train the models above |
| `codi/banc/resultats/` | The bench results. `resum-girat.md` has every number of TECHNICAL.md §1 from the previous submission on, and `resum.md` the steps before it; the others are the steps (`model-girat-fases.md` is the last one) |
| `codi/mesura/` | The measurement of the ATD's ball gaps, run locally by the team on the match's tracking, which prints only words (TECHNICAL.md §2). The bench uses its code to apply what it says to the open matches |
| `codi/inspeccio/` | The first look at the data bundle (a report run locally by the team), and the open "twin" of the bundle used by the tests |
| `codi/pilota/` | The check of the ATD ball against the tactical video (`valida.py`, run locally by the team; TECHNICAL.md §2), and the measurement of the open detector on open video that sets its thresholds (`prova_issia.py`). The pipeline does not use it |
| `codi/possessio/` | The modules of our earlier prototype that the above still uses, and the official metric (`oficial/possession_metrics.py`, MIT, © Metrica Sports) |
| `dades/` | Empty. Where the open data goes, if you want to retrain the model or run the tests ([dades/README.md](dades/README.md)) |

**No match data is in this repository.** What we took from the match, and how, is in TECHNICAL.md §2.

## Reproduce the submission file

You need the data bundle of the challenge, [uv](https://docs.astral.sh/uv/) and git. uv installs Python 3.12 and
the exact versions in `codi/uv.lock`. LightGBM also needs the OpenMP runtime of the system: `brew install libomp` on
macOS, `apt-get install libgomp1` on Debian or Ubuntu.

1. **Install:**

   ```bash
   cd codi
   uv sync --frozen
   ```

2. **Get the official repository**, for its validator and its public 5-minute window, at the commit whose rules
   we followed:

   ```bash
   git clone https://github.com/metrica-sports/more-than-a-hack-2027 ../oficial
   git -C ../oficial checkout f8f2629
   ```

3. **Run the command** (29 s on the open twin of the bundle on an Apple M-series laptop, before the validator).
   `--dades` is the folder of the data bundle: the command finds `BAR-ATH_tactical_atd.xml`,
   `BAR-ATH_tactical_atd.txt` and `BAR-ATH_tactical_smart_tagging.xml` anywhere inside it, by their exact names.

   ```bash
   uv run python -I -m cadena --dades /path/to/data-bundle --sortida possession.csv \
       --validador ../oficial/evaluation/validate_submission.py --permet-fora-del-volum
   ```

   `--permet-fora-del-volum` lets the file be written anywhere. Without it, the command only writes inside the
   team's encrypted volume, where the match data lives.

4. **Compare** with the submitted file: `shasum -a 256 possession.csv`.

**Where this has been checked.** On the open twin of the data bundle that the tests use, the same file, byte for
byte, comes out on macOS 27 (Apple Silicon, libomp 22.1.2) from a fresh clone of this repository, and on Linux arm64
and amd64 (Debian 12, in the `ghcr.io/astral-sh/uv:0.9.5-python3.12-bookworm-slim` image). On the data bundle itself,
on macOS, two runs from our working copy and one from this repository, with a new environment, gave the same
file. From the same fresh clone, `banc.model_final_girat --comprova` rebuilt the model from the open data, identical
to the saved one.

**What the command prints.** It checks its own work, and prints one line per step: ✓ when it went well, ⚠ when
something deserves a look, ✗ when it failed. It never prints a figure from the data, nor anything the Smart Tagging
says. It exits with 0 if no check failed, 1 if one did, and 2 with `--sense-validador`, which skips the validator and
the public window. Only the ⚠ of a file different from the previous run changes the exit code.

| Line | Meaning |
|---|---|
| `✓ ATD tàctic llegit · H és «…» i A, «…»` | ATD read. H is the team whose name contains "Barcelona", the home team ([DATA.md](https://github.com/metrica-sports/more-than-a-hack-2027/blob/f8f2629ff1e0985f81d7e59d8413678514ee1530/DATA.md)) |
| `⚠ A les metadades, «…» no és l'equip de casa. H el segueix sent (DATA.md)` | The metadata give the other team as home. H is still the Barcelona team |
| `✓ Smart Tagging llegit: les pilotes aturades i les fases amb equip` | Smart Tagging read with kloppy's SportsCode reader. If it is missing, there is more than one, or it is not a SportsCode file, ✗ |
| `⚠ Smart Tagging: …` | Something DATA.md does not describe: a code (left out), a set piece of another type or with none (left out), a set piece of a team that is neither (kept, without a team), a phase of a team that is neither (left out). Each warning is printed once, never with a count |
| `✓ L'equip de les fases és el que dona el model sense el Smart Tagging` | Decoded without the Smart Tagging, the model gives the phases' team in more than half of their frames (TECHNICAL.md §1, stage 8). If not, or if there is no phase with a team, ✗ and no file: the Smart Tagging may have the teams the other way round |
| `✓ Fitxer escrit: …` | The file, written |
| `✓ Format correcte (les regles de SUBMISSION.md)` | The file follows SUBMISSION.md |
| `· Primera execució…` / `✓ Igual que l'execució anterior…` | First run: the sha256 is stored next to the file. Later runs must give the same one, or ⚠ and exit code 1. `--accepta-canvi` stores the new one, when the change is wanted |
| `✓ El validador oficial l'accepta…` | `validate_submission.py` accepts it. What it prints goes to `<file>.validacio.txt` |
| `✓ H i A, ben orientats (la finestra pública)` | On the public window, neither spellF1 nor macroF1 is lower than with H and A swapped, and at least one is higher. The other way round, ✗. Unclear, or no window to compare with, ⚠ |
| `✓ Sense desfasament de segons (la finestra pública)` | On the public window, macroF1 is higher as written than shifted 5 s either way. If not, ⚠ |

The public window is used only to check that the pipeline is wired correctly, never to choose anything
(SUBMISSION.md, Rules).

## Retrain the model (optional)

Reproducing the file does not need this: the model is in the repository. To rebuild it from the open data, with
the decoder and Smart Tagging settings of the bench results in `codi/banc/resultats/`:

```bash
cd codi
uv run python -I -m banc.model_final_girat --comprova   # retrains the model and checks it is identical to the saved one
```

It needs the open data in `dades/` ([dades/README.md](dades/README.md)). Training is deterministic (LightGBM with
fixed threads and seed, and the networks with fixed seeds); `--comprova` prints `✓ El model refet és idèntic al
desat, i la fitxa també` when the rebuilt classifiers, networks and record match the saved ones. It trains the
networks in 4 processes (`--processos`), each of which needs a few GB of memory; from a fresh clone, on a Mac with
Apple Silicon, it took 22 minutes. It reads the settings from
`model-camp-girat.json` and `model-girat-fases.json`, and stops if they come from other code. The previous
submission's model is rebuilt the same way, with `banc.model_final --comprova`.

To redo the bench results themselves, run these in order. Each one writes its results to `banc/resultats/`, and
stops if what it builds on is missing or comes from other code. Each step takes from minutes to a few hours.

```bash
# up to the previous submission
uv run python -I -m banc                        # the baselines
uv run python -I -m banc.model_a                # one classifier, assumed position error
uv run python -I -m banc.tocs                   # the touch detector against the open event data
uv run python -I -m banc.decodificador_tocs     # the decoder with touches (dropped)
uv run python -I -m banc.model_a_quart          # trained with a quarter of the error only (dropped)
uv run python -I -m banc.model_a_dos_errors     # trained with both levels of error
uv run python -I -m banc.model_a_control        # with the touch and control signals
uv run python -I -m banc.model_a_context        # with the second classifier
uv run python -I -m banc.model_a_possessio      # at least 8 training frames per possession
uv run python -I -m banc.model_a_hibrid         # each of two models where it seems better (dropped)
uv run python -I -m banc.model_a_contacte       # with the contact signals
uv run python -I -m banc.model_a_canvis         # with the change model and its decoder
uv run python -I -m banc.model_a_canvis2        # a second change model (dropped)
uv run python -I -m banc.model_a_aturades       # with the stoppage signals
uv run python -I -m banc.model_a_skillcorner    # with 20 SkillCorner matches too (dropped; needs their open data)
uv run python -I -m banc.model_a_xarxa          # with one network
uv run python -I -m banc.model_a_xarxa_validada # each network stopped early on a held-out match (dropped)
uv run python -I -m banc.model_a_xarxes         # with five networks: the previous submission
uv run python -I -m banc.resum                  # the tables of those steps
# from the previous submission to this one
uv run python -I -m banc.mesura_atd             # how well the gap measurement tells patterns apart, on open data
uv run python -I -m banc.model_a_partit         # also trained with match ×¼ (dropped)
uv run python -I -m banc.veritat_toc            # the labels at the first touch
uv run python -I -m banc.model_a_toc            # trained at the first touch (dropped)
uv run python -I -m banc.model_a_q              # a change model that sees what the second classifier sees (dropped)
uv run python -I -m banc.model_a_verificador    # a verifier of the decoded possessions (dropped)
uv run python -I -m banc.model_a_sense_pilota   # the networks see an estimated ball in the gaps
uv run python -I -m banc.model_a_tocs_apresos   # a learned touch detector (dropped)
uv run python -I -m banc.model_a_equips         # the networks see both whole teams
uv run python -I -m banc.model_pilota_creible   # the credible ball
uv run python -I -m banc.model_forats_curts     # a model of the short gaps, at the decoder (dropped)
uv run python -I -m banc.model_forats_al_segon  # the same, as signals (dropped)
uv run python -I -m banc.model_mostres_canvis   # more network training near the changes (dropped)
uv run python -I -m banc.model_dos_segons       # the mean of two second classifiers (dropped)
uv run python -I -m banc.pff_al_costat          # PFF's tracking next to the others (closed; needs PFF's data)
uv run python -I -m banc.model_neteja_aire      # no dead ball where the ball was removed
uv run python -I -m banc.model_camp_girat       # the networks learn the pitch flipped too
uv run python -I -m banc.model_vores            # each change moved to where it is likeliest (dropped)
uv run python -I -m banc.model_pilotes_aturades # the set pieces as signals (dropped)
uv run python -I -m banc.model_etiquetes_decodificador  # the set pieces at the decoder, with their team (dropped)
uv run python -I -m banc.model_pilota_morta     # the set pieces as evidence for dead ball
uv run python -I -m banc.model_represes         # a classifier around the restarts (dropped)
uv run python -I -m banc.model_engolides        # swallowed possessions of the other team (dropped)
uv run python -I -m banc.model_fases            # the phases
uv run python -I -m banc.model_fases_amplia     # a wider grid for the phases (dropped)
uv run python -I -m banc.model_girat_fases      # set pieces and phases on the flipped pitch: this submission
uv run python -I -m banc.resum_girat            # the tables of TECHNICAL.md §1
uv run python -I -m banc.figura_decodificador   # Figure 2
```

## Tests

```bash
cd codi
uv run pytest -q
```

They run on synthetic data, on the open matches and on an open twin of the data bundle, built from Metrica sample
game 3. They need the Metrica and DFL data in `dades/` and `ffmpeg` on the `PATH`. From a fresh clone, 1,115 pass and
20 are skipped: the check of the phases' team on the ten open matches needs the bench's probabilities of the
flipped-pitch model, which the bench steps up to `banc.model_camp_girat` leave in `dades/banc/`.

## Licence

MIT, © 2026 MassiuSoft ([LICENSE](LICENSE)), except the official metric in `codi/possessio/oficial/`, which keeps its
own MIT licence (© Metrica Sports). No data is included: the open data you download keeps its own terms.

## Attribution

- **FootAndBall** (only `codi/pilota/`, which the pipeline does not use): Komorowski, J., Kurzejamski, G., Sarwas,
  G. "FootAndBall: Integrated Player and Ball Detector". VISAPP 2020, 47-56. https://doi.org/10.5220/0008916000470056.
  MIT. Not included: [dades/README.md](dades/README.md) says how to get it.
- **Official metric:** `codi/possessio/oficial/possession_metrics.py` is copied unchanged from the challenge
  repository, and is identical to the one at commit `f8f2629` (MIT, © 2026-2027 Metrica Sports; licence in
  `codi/possessio/oficial/LICENSE`).
- **DFL/IDSSE data:** Bassek, M., Rein, R., Weber, H. et al. "An integrated dataset of spatiotemporal and event data
  in elite soccer". *Scientific Data* 12, 195 (2025). https://doi.org/10.1038/s41597-025-04505-y. CC BY 4.0.
- **Metrica sample data:** https://github.com/metrica-sports/sample-data
- **SkillCorner open data** (only `banc.model_a_skillcorner`, a dropped step; the model is not trained on it):
  https://github.com/SkillCorner/opendata. MIT, © 2020 SkillCorner. Not included.
- **PFF FC FIFA World Cup 2022 data** (only `banc.pff_al_costat`, a closed step; the model is not trained on it):
  released by PFF FC, now Gradient Sports, at https://www.blog.fc.pff.com/blog/pff-fc-release-2022-world-cup-data.
  Not included.
