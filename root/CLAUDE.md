# Root guide: notes for AI assistants

Unofficial learning material for *Root: A Game of Woodland Might and Right* (Leder Games, 2018; 2–4 players in the
base box, asymmetric: Marquise de Cat, Eyrie Dynasties, Woodland Alliance, Vagabond). Rules follow **The Law of Root,
October 13, 2025**. Scope is the **base game only**: no Riverfolk, Underworld, Marauder, Homeland, hirelings,
landmarks or Clockwork bots.

## Files

| Path | What it is |
|---|---|
| `root-rules.md` | Detailed rules reference (map, setup, turn, crafting, battle, dominance, each faction, board numbers, common mistakes). Source of truth for wording. Law section numbers in brackets. |
| `root-rules.html` | One-page illustrated digest in the manga style of `../hegemony/hegemony-rules.html`, recoloured with Root's suit and faction colours. Opens in any browser; pictures from `img/`. The card gallery is built by a small script from a data array (keep it in sync with `cards/deck.md`; a `console.assert` checks the 54-card total). |
| `img/` | Crops of *Learning to Play* (cover, map anatomy, battle example, piece glossary, faction banners) and *Walking Through Root* (map after setup). |
| `img/cards/` | Official card images (240 px JPEG) from the Leder card library: 42 deck faces (`card-*`), 4 Eyrie leaders (`bird-*`), 3 Vagabond characters (`vagabond-*`), 15 quests (`quest-*`), 4 faction overviews (`intro-*`). |
| `cards/deck.md` | All 54 deck cards: suit, copies, crafting cost, type and effect, plus item-supply totals. |
| `cards/factions.md` | Eyrie leaders, Vagabond characters, the 15 quests with their items, faction overview texts. |

## Simulator (`sim/`)

- `data.py`: map, deck, faction boards, quests, characters, leaders. Comments mark **REAL** (from a source) and **EST**
  (map paths read off the picture, unconfirmed board numbers, dice faces, deck copy counts).
- `engine.py`: every rule (setup, rule, movement, battle with ambush and battle cards, crafting, dominance and
  coalition, Marquise, Eyrie Decree and turmoil, Alliance supporters/revolt/Outrage/officers, Vagabond items,
  relationships, quests and specials). Bots only choose; rules never live in `bots.py`. Shortcuts are marked `SKIP:`
  (Codebreakers and Cobbler are never used by the bots; the Vagabond never moves or fights with Allied warriors).
- `bots.py`: one bot per faction, built on community strategy (Sprites and Dice "The Strategy of Root", Elusive Meeple
  "Root strategy tips"): pressure on the cats, Eyrie Decree dry-run one turn ahead on a copy of the game (own dice),
  early Alliance revolts, Vagabond quests for cards and goes hostile on a runaway leader, dominance only as a comeback.
  The Eyrie and Vagabond bots still play below good players, so the Marquise wins most bot games. Win rates describe
  the bots, not the game.
- `run.py`: `python run.py --players 4 --seed 3` (one game), `--factions MEA`, `--log file.txt`, `--batch 300`.
- `test_rules.py`: source numbers, setup, rule scenarios (rule ties, battle, ambush, crafting, dominance, coalition,
  turmoil, Outrage, revolt, Field Hospitals, Vagabond relationships, item limit, Infamy) and invariants over 300 full
  games (pieces and cards conserved, slots never overfilled). Run it after every engine or bot change.
- `showcase.py`: picks the featured game, finds an example for every outcome, runs 300 games per player count, writes
  `logs/` and replaces the block between `<!-- SIM:START` and `<!-- SIM:END -->` in `root-rules.html`. About 30 s.
  Never edit that block by hand.

Games are deterministic per seed. On Windows run with `PYTHONIOENCODING=utf-8` (logs contain arrows).

## Sources

- Rule PDFs (Law of Root Oct 2025, Learning to Play, Walking Through Root): ledergames.com/pages/resources. Local copies
  and their text extracts were kept in `~/Downloads/root-pdfs/` when the guide was written.
- Card data: github.com/LederCards/cards (`content/card-data/root/en-US/rootbasegame.yml` and `content/card-images/root/en-US/`).
- Base deck suit totals (14 bird, 14 fox, 13 mouse, 13 rabbit): BoardGameGeek wiki.

## Known estimates

- **Copy counts** in the deck are not printed by any official source; they are the standard composition and match the
  suit totals. The second copies of Codebreakers and Scouting Party are the least certain.
- **Faction board numbers** (Marquise costs and VP, roost track, sympathy costs and VP, Vagabond relationship steps,
  draw-bonus positions) are printed on the boards, not in the Law. Only a few are confirmed by the booklets (2nd roost
  = 1, 3rd = 2; 2nd sympathy = 1; 4th sympathy costs 2; Vagabond steps 1/2/3 Aids for +1/+2/+2, Learning to Play p. 19). Mark them **(board)** and
  say so wherever they appear.

## Conventions

- Keep the page's look (ink panels, sketchy SVG filters, Bangers/Anton/Barlow Condensed, suit colours fox/rabbit/mouse/bird
  and faction colours). Hand-drawn outlines are `::after` overlays filtered by `#sketchy`, not the elements' own borders.
- The fox, Marquise and Alliance tokens are darkened on purpose so small white text on them passes WCAG AA. Don't brighten them.
- Rule claims must be checked against the Law; card claims against `cards/*.md`. Mark anything not printed in a source.
