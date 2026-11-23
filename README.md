# Boardgame Guide

A collection of board game write-ups: rules digests, setup guides, visual references, and sometimes a
small simulator that plays the game to show how a full game unfolds. Each game lives in its own folder.

These are personal, unofficial notes for learning and teaching games. They are not affiliated with
the publishers. Game names, rulebook images and card texts belong to their owners.

## Games

| Folder | Game | What's inside |
|---|---|---|
| [`hegemony/`](hegemony/) | *Hegemony: Lead Your Class to Victory* (Hegemonic Project Games, 2021) | Full rules reference, one-page illustrated rules digest, English card texts, a rules simulator with example games |
| [`root/`](root/) | *Root: A Game of Woodland Might and Right* (Leder Games, 2018), base game | Full rules reference (Law of Root, Oct 2025), one-page illustrated rules digest, all 54 deck cards plus leaders, characters and quests with official card images, a rules simulator with example games |

## How a game folder is usually laid out

- `<game>-rules.md`: the detailed rules reference in plain Markdown.
- `<game>-rules.html`: a one-page visual guide. Open it in a browser; pictures load from `img/`.
- `img/`: pictures used by the page.
- Anything extra the game needs, such as a card list (`cards/`) or a simulator (`sim/`).
- `CLAUDE.md`: notes for an AI coding assistant working in that folder (what the files are, how to run and rebuild things).

## Viewing the pages

Clone the repository and open the `.html` file of a game in any browser. No build step is needed.
