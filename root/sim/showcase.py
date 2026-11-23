"""Build the "Simulated games" section of ../root-rules.html from real simulator runs.

    python showcase.py            (writes logs/ and replaces the block between the SIM markers)

Progress is printed while the batches run.
"""
import html
import os
import re
import sys
import time
from collections import Counter, defaultdict

import data as D
import engine

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "..", "root-rules.html")
LOGS = os.path.join(HERE, "logs")
BATCH = 300
N = D.NAME
DOT = {"M": "cat", "E": "eyrie", "A": "alli", "V": "vaga"}

HIGHLIGHT = [("GAME OVER", 0), ("REVOLT", 1), ("TURMOIL", 1), ("Dominance", 1), ("coalition", 1),
             ("deposed", 2), ("Favor of", 2), ("the keep is destroyed", 1), ("A New Roost", 2),
             ("base placed", 3), ("ambush!", 3), ("is now Hostile", 3), ("Field Hospitals", 4),
             ("improves to Allied", 3), ("completes quest", 4), ("builds a", 5), ("Decree build", 5),
             ("crafts", 6), ("explores", 6), ("relationship with", 6), ("Outrage", 7), ("spreads sympathy", 7),
             ("battles", 8)]

CATEGORY = [("removed", "Removing pieces"), ("sawmill", "Buildings"), ("workshop", "Buildings"), ("recruiter", "Buildings"), ("roost", "Roosts"),
            ("sympathy", "Sympathy"), ("crafted", "Crafted items"),
            ("Despot", "Removing pieces"), ("relationship", "Relationships"), ("Allied", "Relationships"),
            ("quest", "Quests"), ("explore", "Ruins"), ("Infamy", "Infamy"), ("turmoil", "Turmoil"),
            ("Royal Claim", "Royal Claim")]


def category(reason):
    for key, cat in CATEGORY:
        if key in reason:
            return cat
    return "Card effects"


def esc(s):
    return html.escape(s, quote=False)


def write_log(g, name):
    os.makedirs(LOGS, exist_ok=True)
    with open(os.path.join(LOGS, name), "w", encoding="utf-8") as f:
        f.write("\n".join(g.lines) + "\n")
    return f"sim/logs/{name}"


def highlights(g, r, keep=7):
    start = g.round_marks[r - 2] if r > 1 else 0
    end = g.round_marks[r - 1] if r <= len(g.round_marks) else len(g.lines)
    picked = []
    for i in range(start, end):
        line = g.lines[i]
        for key, prio in HIGHLIGHT:
            if key in line:
                who, text = line[4:].split("| ", 1)
                who = who.strip()
                picked.append((prio, i, (who + ": " if who != "Game" else "") + text))
                break
    picked.sort()
    return [t for _, _, t in sorted(picked[:keep], key=lambda x: x[1])]


def pick_featured(n_players=4, seeds=80):
    """First seed with a long, close game: at least 7 rounds and a winning margin of 5 VP or less."""
    fs = D.DEFAULT_FACTIONS[n_players]
    for seed in range(1, seeds + 1):
        g = engine.Game(factions=fs, seed=seed, verbose=False)
        r = g.play()
        top = sorted(r["vp"].values(), reverse=True)
        if r["rounds"] >= 7 and r["reason"] == "30 VP" and top[0] - top[1] <= 5:
            return seed
    return 1


def featured_html(g, res, log_href):
    fs = g.factions
    win = " &amp; ".join(N[f] for f in res["winners"])
    vp = res["vp"]
    out = [f'<article class="pb sim" id="sim-featured">',
           f'<div class="pb-head"><span class="dot all">★</span><h3>Featured game · {g.n} players · seed {g.seed}</h3>'
           f'<p>{win} win{"s" * (len(res["winners"]) == 1)} in round {res["rounds"]} ({esc(res["reason"])}). Every line below '
           f'comes from the simulator\'s log; <a href="{log_href}" style="color:#fff">open the full turn-by-turn log</a>.</p></div>',
           '<div class="pb-body"><div class="pb-round"><span class="pb-label">VP after each round</span>',
           '<div class="tbl-wrap"><table class="nums"><thead><tr><th scope="col">Round</th>'
           + "".join(f'<th scope="col">{N[f]}</th>' for f in fs) + "</tr></thead><tbody>"]
    for r, snap in g.history:
        out.append(f'<tr><th scope="row">R{r}</th>' + "".join(f"<td>{snap[f]}</td>" for f in fs) + "</tr>")
    out.append('<tr><th scope="row">Final</th>' + "".join(f"<td><b>{vp[f]}</b></td>" for f in fs) + "</tr>")
    out.append("</tbody></table></div>")
    out.append('<span class="pb-label" style="margin-top:16px">Where the points came from</span>')
    cats = defaultdict(Counter)
    for f in fs:
        for reason, n in g.vp_log.get(f, {}).items():
            cats[f][category(reason)] += n
    allcats = sorted({k for f in fs for k in cats[f] if cats[f][k]}, key=lambda k: -sum(abs(cats[f][k]) for f in fs))
    out.append('<div class="tbl-wrap"><table class="nums"><thead><tr><th scope="col">Source</th>'
               + "".join(f'<th scope="col">{N[f]}</th>' for f in fs) + "</tr></thead><tbody>")
    for k in allcats:
        out.append(f'<tr><th scope="row">{esc(k)}</th>' + "".join(f"<td>{cats[f][k] or ''}</td>" for f in fs) + "</tr>")
    out.append("</tbody></table></div></div>")
    out.append('<div class="pb-ex"><span class="pb-label">Round by round</span>')
    for r in range(1, res["rounds"] + 1):
        items = "".join(f"<li>{esc(t)}</li>" for t in highlights(g, r))
        out.append(f'<div class="ex"><h4>Round {r}</h4><ul class="sim-list">{items}</ul></div>')
    out.append("</div></div></article>")
    return "\n".join(out)


def outcomes(seeds=300):
    found = {}
    for n in (2, 3, 4):
        fs = D.DEFAULT_FACTIONS[n]
        for seed in range(1, seeds + 1):
            g = engine.Game(factions=fs, seed=seed, verbose=False)
            r = g.play()
            key = (n, "+".join(r["winners"]), r["reason"])
            if key not in found:
                found[key] = (seed, r, g)
        print(f"  outcomes {n}p: {seeds} seeds searched", file=sys.stderr)
    return found


def batch_stats(n, games):
    fs = D.DEFAULT_FACTIONS[n]
    wins, vp, stats, reasons, rounds = Counter(), defaultdict(list), Counter(), Counter(), []
    t0 = time.time()
    for i, seed in enumerate(range(1, games + 1), 1):
        g = engine.Game(factions=fs, seed=seed, verbose=False)
        r = g.play()
        for f in r["winners"]:
            wins[f] += 1 / len(r["winners"])
        reasons[r["reason"]] += 1
        rounds.append(r["rounds"])
        for f, v in r["vp"].items():
            vp[f].append(v)
        stats.update(g.stats)
        if i % 100 == 0:
            el = time.time() - t0
            print(f"  {n}p batch: {i}/{games} games, {el:.0f}s, ETA {el / i * (games - i):.0f}s", file=sys.stderr)
    return fs, wins, vp, stats, reasons, sum(rounds) / len(rounds)


def build():
    t0 = time.time()
    print("choosing the featured game…", file=sys.stderr)
    seed = pick_featured()
    g = engine.Game(factions=D.DEFAULT_FACTIONS[4], seed=seed, verbose=False)
    res = g.play()
    feat = featured_html(g, res, write_log(g, f"featured-4p-seed{seed}.txt"))

    print("searching outcomes (3 × 300 games)…", file=sys.stderr)
    found = outcomes()
    rows = []
    for key in sorted(found, key=lambda k: (k[0], k[2], k[1])):
        n2, who, reason = key
        s, r, gg = found[key]
        href = write_log(gg, f"{n2}p-seed{s}.txt")
        names = " &amp; ".join(N[f] for f in who.split("+"))
        vp = " · ".join(f"{N[f]} {v}" for f, v in r["vp"].items())
        rows.append(f'<tr><th scope="row">{n2}p</th><td>{names}</td><td>{esc(reason)}</td><td>round {r["rounds"]}</td>'
                    f'<td>{vp}</td><td><a href="{href}">seed {s}</a></td></tr>')

    stat_rows, count_rows = [], []
    for n2 in (2, 3, 4):
        fs, wins, vp, stats, reasons, avg_rounds = batch_stats(n2, BATCH)
        cells = "".join(f'<td><span class="dot {DOT[f]}">{f}</span> {N[f]} <b>{wins[f] / BATCH:.0%}</b> · '
                        f'{sum(vp[f]) / len(vp[f]):.0f} VP</td>' for f in fs) + "<td></td>" * (4 - len(fs))
        ends = ", ".join(f"{k} {v / BATCH:.0%}" for k, v in reasons.most_common())
        stat_rows.append(f'<tr><th scope="row">{n2} players</th>{cells}<td>{ends}</td><td>{avg_rounds:.1f}</td></tr>')
        per = {k: v / BATCH for k, v in stats.items()}
        count_rows.append(
            f'<tr><th scope="row">{n2}p</th><td>{per.get("battles", 0):.1f}</td><td>{per.get("ambush", 0):.1f}</td>'
            f'<td>{per.get("crafted", 0):.1f}</td><td>{per.get("turmoil", 0):.1f}</td>'
            f'<td>{per.get("revolts", 0):.1f} / {per.get("outrage", 0):.1f}</td>'
            f'<td>{per.get("quests", 0):.1f} / {per.get("aids", 0):.1f}</td><td>{per.get("field_hospitals", 0):.1f}</td></tr>')

    code = 'style="display:inline;padding:1px 5px"'
    section = f"""<!-- SIM:START (generated by sim/showcase.py — do not edit by hand) -->
    <div class="break"><span>Simulated games</span></div>
    <section id="simulation">
      <div class="section-title">
        <h2>The game, played by bots</h2>
        <p>A rules simulator plays complete games from setup to the last point. Everything here comes from real runs of it ({BATCH} games per player count).</p>
      </div>
      <div class="story" data-label="HOW IT WORKS" style="margin-top:30px">
        <div class="turn-grid">
          <div class="step"><span class="step-n" aria-hidden="true">1</span><h3>Real rules</h3><p>The engine follows the <b>Law of Root</b> (Oct 2025) for all four base factions: setup, rule, movement, battle with ambushes, crafting, dominance (coalitions are in the engine and tested, but the bots never form one), Decree and turmoil, revolts and Outrage, Vagabond items, quests and relationships. 12 rule scenarios, data and setup checks, and invariant checks over 300 full games.</p></div>
          <div class="step"><span class="step-n" aria-hidden="true">2</span><h3>Real cards</h3><p>All <b>54 deck cards</b> with their printed costs and effects, the 4 Eyrie leaders, 3 Vagabond characters and 15 quests. Codebreakers and Cobbler are crafted but unused by the bots, and the Vagabond never moves or fights with Allied warriors.</p></div>
          <div class="step"><span class="step-n" aria-hidden="true">3</span><h3>Estimates</h3><p>The Autumn map's paths were read off the map picture. Faction-board numbers the booklets don't show, the dice faces and the deck's copy counts are marked <b>EST</b> in <code {code}>sim/data.py</code>.</p></div>
          <div class="step"><span class="step-n" aria-hidden="true">4</span><h3>Bots</h3><p>One per faction, following community strategy guides: everyone pressures the cats, the Eyrie dry-run their Decree a turn ahead, the Alliance revolts early, the Vagabond quests for cards and turns on a runaway leader, dominance is a comeback play. They still play the Eyrie and Vagabond weaker than good players, so win rates show <b>bot</b> behaviour, not the real game's balance.</p></div>
        </div>
      </div>
{feat}
      <div class="story" data-label="EVERY KIND OF ENDING" style="margin-top:30px">
        <h2 class="sr-only">Example endings</h2>
        <p class="story-note" style="margin:0 0 12px">One game for every winner and way of winning the bots produced in 300 seeds per player count (torch-marked mixes from <i>Learning to Play</i> p. 22: Marquise + Eyrie, + Vagabond, + Alliance). Each seed replays exactly; click it for the full log.</p>
        <div class="tbl-wrap"><table>
          <thead><tr><th scope="col">Players</th><th scope="col">Winner</th><th scope="col">How</th><th scope="col">When</th><th scope="col">Final VP</th><th scope="col">Log</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table></div>
      </div>
      <div class="story" data-label="{BATCH} GAMES PER PLAYER COUNT" style="margin-top:30px">
        <h2 class="sr-only">Statistics</h2>
        <div class="tbl-wrap"><table>
          <thead><tr><th scope="col">Game</th><th scope="col" colspan="4">Win rate · average VP</th><th scope="col">How games end</th><th scope="col">Rounds</th></tr></thead>
          <tbody>{''.join(stat_rows)}</tbody>
        </table></div>
        <div class="tbl-wrap" style="margin-top:12px"><table class="nums">
          <thead><tr><th scope="col">Per game</th><th scope="col">Battles</th><th scope="col">Ambushes</th><th scope="col">Crafts</th><th scope="col">Turmoils</th><th scope="col">Revolts / Outrage</th><th scope="col">Quests / Aids</th><th scope="col">Field Hospitals</th></tr></thead>
          <tbody>{''.join(count_rows)}</tbody>
        </table></div>
        <p class="story-note">Run it yourself: <code {code}>python sim/run.py --players 4 --seed {seed}</code> prints one game turn by turn; <code {code}>python sim/run.py --batch 300</code> repeats these statistics; <code {code}>python sim/test_rules.py</code> runs the rule checks.</p>
      </div>
    </section>
    <!-- SIM:END -->"""

    page = open(PAGE, encoding="utf-8").read()
    if "<!-- SIM:START" in page:
        page = re.sub(r"<!-- SIM:START.*?<!-- SIM:END -->", lambda m: section.strip(), page, flags=re.S)
    else:
        anchor = "    <!-- FAQ -->"
        assert page.count(anchor) == 1
        page = page.replace(anchor, "    " + section.strip() + "\n\n" + anchor)
    open(PAGE, "w", encoding="utf-8", newline="").write(page)
    print(f"page updated in {time.time() - t0:.0f}s (featured seed {seed}); logs in {LOGS}", file=sys.stderr)


if __name__ == "__main__":
    build()
