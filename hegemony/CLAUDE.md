# Hegemony guide: notes for AI assistants

Unofficial learning material for *Hegemony: Lead Your Class to Victory* (2-4 players, asymmetric:
Working Class, Middle Class, Capitalist Class, State). Rules follow the official English rulebook
**v1.2** (Nov 2023); v1.2 only adds clarifications to v1.1.

## Files

| Path | What it is |
|---|---|
| `hegemony-rules.md` | Detailed rules reference (setup, round, every class, Politics Table, IMF, end game). Source of truth for wording. |
| `hegemony-rules.html` | One-page illustrated digest in a black-and-white manga style. Opens in any browser; pictures from `img/`. |
| `img/` | Crops of the official rulebook (components, card anatomy, board, player boards, setup photo, election and IMF examples). |
| `cards/` | English card texts: `working.md`, `middle.md`, `capitalist.md`, `state.md` (40 base + 5 Crisis & Control each), `events-agendas.md` (25 base Events, C&C events; the 10 base Political Agendas are not in the source). Translated from the unofficial Italian card file v2.1 by F. Santoro. |
| `sim/` | Rules simulator. Bots play complete games; see below. |

## Simulator (`sim/`)

- `data.py`: numbers. Comments mark **REAL** (from the rulebook or its pictures) and **EST** (estimates:
  the full company decks, Export / Business Deal / Immigration decks, State goods prices, Free Trade Zone
  capacity). `cards.py` holds the Political Agendas, also EST.
- `engine.py`: every rule (setup, phases, buying, production, taxes, elections, IMF, scoring, end game, tiebreak).
  Bots only choose; rules never live in `bots.py`.
- `bots.py`: one heuristic bot per class. Each turn: score Basic Actions and playable cards, play the best,
  take one Free Action.
- `cards.py`: effects for the 160 base action cards (four are SKIP: Competitive wages, Nationalization,
  Denial of free speech, Privatization) and the 25 base Events. Class-specific versions of shared card
  names use keys like `"S:Business grants"`.
- `run.py`: `python run.py --players 4 --seed 9` (one game, full log), `--log file.txt`, `--batch 300` (statistics).
- `test_rules.py`: rulebook number checks, rule scenarios (election ties, tiebreak, IMF, review fixes) and
  invariants over 450 full games. Run it after every engine/card change.
- `showcase.py`: plays the featured game, finds an example for every outcome, runs 300 games per player
  count, writes `logs/` and replaces the block between `<!-- SIM:START` and `<!-- SIM:END -->` in
  `hegemony-rules.html`. Takes about 45 s. Never edit that block by hand.

Games are deterministic per seed (sort sets before iterating; no hash-order dependence). On Windows,
run with `PYTHONIOENCODING=utf-8` because logs contain `₩` and arrows.

## Conventions

- Keep the page's look (ink panels, sketchy SVG filters, Bangers/Anton/Barlow Condensed fonts). Hand-drawn
  outlines are `::after` overlays filtered by `#sketchy`, not the elements' own borders.
- Rule claims must be checked against the rulebook text; card claims against `cards/*.md`. Mark anything
  not printed in a source as an estimate.
- Win rates from the simulator describe the bots, not the real game's balance. Say so wherever they appear.
