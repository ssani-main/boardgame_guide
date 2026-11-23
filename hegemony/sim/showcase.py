"""Build the "Simulated games" section of ../hegemony-rules.html from real simulator runs.

    python showcase.py            (writes logs/ and replaces the block between the SIM markers)

Progress is printed while the batch runs.
"""
import html
import io
import os
import re
import sys
import time
from collections import Counter, defaultdict

import engine

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "..", "hegemony-rules.html")
LOGS = os.path.join(HERE, "logs")
FEATURED = (4, 9)
BATCH = 300
N = engine.CLS_NAME
DOT = {"W": "r", "M": "y", "C": "b", "S": "g"}

HIGHLIGHT = [("IMF INTERVENTION", 0), ("Policies forced", 0), ("Demonstration!", 1), ("Demonstration (", 1),
             ("PASSED", 2), ("builds ", 3), ("plays card", 4), ("forms the", 3), ("Strike token", 4),
             ("Event Action:", 4), ("forced Loan", 2), ("State takes a Loan", 2), ("Wealth table", 5),
             ("VP (Legitimacy", 5), ("Political Agenda", 6), ("Trade Union", 6), ("Prosperity (", 7)]

CATEGORY = [("Prosperity", "Prosperity"), ("Healthcare bonus", "Prosperity"), ("Bill", "Bills & votes"),
            ("Wealth", "Wealth table"), ("Legitimacy", "Legitimacy"), ("Agenda", "Political Agenda"),
            ("policies in", "End: policies"), ("money", "End: money"), ("Treasury", "End: money"),
            ("goods in storage", "End: goods"), ("Trade Unions", "Trade Unions"), ("Demonstration", "Demonstration"),
            ("Loan", "Loans"), ("export", "Exports"), ("welfare", "Cheap welfare"), ("Benefits", "Benefits taken")]


def category(reason):
    for key, cat in CATEGORY:
        if key in reason:
            return cat
    return "Events & cards"


def write_log(g, name):
    os.makedirs(LOGS, exist_ok=True)
    path = os.path.join(LOGS, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(g.lines) + "\n")
    return f"sim/logs/{name}"


def highlights(g, r):
    start = g.round_marks[r - 2] if r > 1 else 0
    end = g.round_marks[r - 1] if r <= len(g.round_marks) else len(g.lines)
    picked = []
    for i in range(start, end):
        line = g.lines[i]
        for key, prio in HIGHLIGHT:
            if key in line:
                picked.append((prio, i, line.split("| ", 1)[1]))
                break
    picked.sort()
    keep = sorted(picked[:11], key=lambda x: x[1])
    return [t for _, _, t in keep]


def esc(s):
    return html.escape(s, quote=False)


def featured_html(g, res, log_href):
    roles = g.roles
    win = " & ".join(N[c] for c in res["winners"])
    vp = res["vp"]
    top = sorted(vp.values(), reverse=True)
    out = [f'<article class="pb" id="sim-featured">',
           f'<div class="pb-head"><span class="dot g">★</span><h3>Featured game · {g.n} players · seed {g.seed}</h3>'
           f'<p>{win} wins {top[0]}–{top[1]}. Every line below comes from the simulator\'s log; '
           f'<a href="{log_href}" style="color:#fff">open the full turn-by-turn log</a>.</p></div>',
           '<div class="pb-body"><div class="pb-round"><span class="pb-label">VP after each round</span>',
           '<div class="tbl-wrap"><table><thead><tr><th scope="col">Round</th>'
           + "".join(f'<th scope="col">{N[c]}</th>' for c in roles) + "</tr></thead><tbody>"]
    for i, snap in enumerate(g.vp_rounds, 1):
        out.append(f'<tr><th scope="row">R{i}</th>' + "".join(f"<td>{snap[c]}</td>" for c in roles) + "</tr>")
    out.append('<tr><th scope="row">Final</th>' + "".join(f"<td><b>{vp[c]}</b></td>" for c in roles) + "</tr>")
    out.append("</tbody></table></div>")
    # VP sources
    out.append('<span class="pb-label" style="margin-top:16px">Where the points came from</span>')
    cats = defaultdict(Counter)
    for c in roles:
        for reason, n in g.vp_log[c].items():
            cats[c][category(reason)] += n
    allcats = sorted({k for c in roles for k in cats[c]}, key=lambda k: -sum(cats[c][k] for c in roles))
    out.append('<div class="tbl-wrap"><table><thead><tr><th scope="col">Source</th>'
               + "".join(f'<th scope="col">{N[c][0]}</th>' for c in roles) + "</tr></thead><tbody>")
    for k in allcats:
        out.append(f'<tr><th scope="row">{esc(k)}</th>' + "".join(
            f"<td>{cats[c][k] or ''}</td>" for c in roles) + "</tr>")
    out.append("</tbody></table></div></div>")
    # round highlights
    out.append('<div class="pb-ex"><span class="pb-label">Round by round</span>')
    for r in range(1, 6):
        items = "".join(f"<li>{esc(t)}</li>" for t in highlights(g, r))
        out.append(f'<div class="ex"><h4>Round {r}</h4><ul class="sim-list">{items}</ul></div>')
    out.append(f'<p class="tip"><b>Result:</b> {esc(g.lines[-1].split("| ", 1)[1])}</p>')
    out.append("</div></div></article>")
    return "\n".join(out)


def outcomes(players_list=(2, 3, 4), seeds=300):
    found = {}
    for n in players_list:
        for seed in range(1, seeds + 1):
            g = engine.Game(players=n, seed=seed, verbose=False)
            r = g.play()
            key = (n, "+".join(r["winners"]), r["reason"])
            if key not in found:
                found[key] = (seed, r, g)
    return found


def batch_stats(n, games):
    wins, vp, stats, ties = Counter(), defaultdict(list), Counter(), Counter()
    t0 = time.time()
    for i, seed in enumerate(range(1, games + 1), 1):
        g = engine.Game(players=n, seed=seed, verbose=False)
        r = g.play()
        for c in r["winners"]:
            wins[c] += 1 / len(r["winners"])
        if r["reason"] != "most VP":
            ties[r["reason"]] += 1
        for c, v in r["vp"].items():
            vp[c].append(v)
        stats.update(g.stats)
        if i % 100 == 0:
            print(f"  {n}p batch: {i}/{games} games, {time.time() - t0:.0f}s", file=sys.stderr)
    return wins, vp, stats, ties


def build():
    t0 = time.time()
    print("featured game…", file=sys.stderr)
    n, seed = FEATURED
    g = engine.Game(players=n, seed=seed, verbose=False)
    res = g.play()
    feat = featured_html(g, res, write_log(g, f"featured-{n}p-seed{seed}.txt"))

    print("searching outcomes (3 × 300 games)…", file=sys.stderr)
    found = outcomes()
    rows = []
    order = lambda k: (k[0], k[2] != "most VP", k[1])
    for key in sorted(found, key=order):
        n2, who, reason = key
        s, r, gg = found[key]
        href = write_log(gg, f"{n2}p-seed{s}.txt")
        names = " &amp; ".join(N[c] for c in who.split("+"))
        vp = " · ".join(f"{N[c][0]} {v}" for c, v in r["vp"].items())
        rows.append(f'<tr><th scope="row">{n2}p</th><td>{names}</td><td>{esc(reason)}</td><td>{vp}</td>'
                    f'<td><a href="{href}">seed {s}</a></td></tr>')

    stat_rows, count_rows = [], []
    for n2 in (2, 3, 4):
        wins, vp, stats, ties = batch_stats(n2, BATCH)
        roles = engine.ROLES_BY_COUNT[n2]
        cells = "".join(f"<td>{N[c]} {wins[c] / BATCH:.0%} · {sum(vp[c]) / len(vp[c]):.0f} VP</td>" for c in roles)
        cells += "<td></td>" * (4 - len(roles))
        stat_rows.append(f'<tr><th scope="row">{n2} players</th>{cells}<td>{sum(ties.values())}</td></tr>')
        per = {k: stats[k] / BATCH for k in stats}
        count_rows.append(
            f'<tr><th scope="row">{n2}p</th><td>{per.get("bills", 0):.0f} ({per.get("passed", 0):.0f} pass)</td>'
            f'<td>{per.get("cards_played", 0):.0f} / {per.get("basic_actions", 0):.0f}</td>'
            f'<td>{per.get("built_C", 0) + per.get("built_M", 0):.1f}</td><td>{per.get("strikes", 0):.1f}</td>'
            f'<td>{per.get("demonstrations", 0):.1f}</td><td>{per.get("imf", 0):.2f}</td>'
            f'<td>{per.get("events", 0):.1f}</td></tr>')

    section = f"""<!-- SIM:START (generated by sim/showcase.py — do not edit by hand) -->
    <div class="break"><span>Simulated games</span></div>
    <section id="simulation">
      <div class="section-title">
        <h2>The game, played by bots</h2>
        <p>A rules simulator plays complete games from setup to the final tiebreak. Everything here comes from real runs of it ({BATCH} games per player count).</p>
      </div>
      <div class="story" data-label="HOW IT WORKS" style="margin-top:30px">
        <div class="turn-grid">
          <div class="step"><span class="step-n" aria-hidden="true">1</span><h3>Real rules</h3><p>The engine follows rulebook <b>v1.2</b>: setup, all 5 phases, taxes, elections, IMF, scoring, Loans and the full tiebreak. 7 test groups check it against the rulebook's own examples.</p></div>
          <div class="step"><span class="step-n" aria-hidden="true">2</span><h3>Real cards</h3><p>All <b>160 base action cards</b> and <b>25 Events</b>, translated to English in <code style="display:inline;padding:1px 5px">cards/</code>. 156 are modelled; 4 complex ones are only ever discarded for a Basic Action.</p></div>
          <div class="step"><span class="step-n" aria-hidden="true">3</span><h3>Estimates</h3><p>Not published anywhere: the full company decks, Export, Business Deal and Immigration decks, the 10 Political Agendas. These follow the real cards' patterns and are marked <b>EST</b> in <code style="display:inline;padding:1px 5px">sim/data.py</code>.</p></div>
          <div class="step"><span class="step-n" aria-hidden="true">4</span><h3>Simple bots</h3><p>Each turn a bot scores its options (Basic Actions and playable cards), plays the best, and uses one Free Action. Win rates show <b>bot</b> behaviour, not the real game's balance.</p></div>
        </div>
      </div>
{feat}
      <div class="story" data-label="EVERY KIND OF ENDING" style="margin-top:30px">
        <h2 class="sr-only">Example endings</h2>
        <p class="story-note" style="margin:0 0 12px">One game for every winner and every tiebreak the bots produced in 300 seeds per player count. Each seed replays exactly; click it for the full log.</p>
        <div class="tbl-wrap"><table>
          <thead><tr><th scope="col">Players</th><th scope="col">Winner</th><th scope="col">Decided by</th><th scope="col">Final VP</th><th scope="col">Log</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table></div>
      </div>
      <div class="story" data-label="{BATCH} GAMES PER PLAYER COUNT" style="margin-top:30px">
        <h2 class="sr-only">Statistics</h2>
        <div class="tbl-wrap"><table>
          <thead><tr><th scope="col">Game</th><th scope="col" colspan="4">Win rate · average VP</th><th scope="col">Ties broken</th></tr></thead>
          <tbody>{''.join(stat_rows)}</tbody>
        </table></div>
        <div class="tbl-wrap" style="margin-top:12px"><table>
          <thead><tr><th scope="col">Per game</th><th scope="col">Bills</th><th scope="col">Cards played / discarded</th><th scope="col">Companies built</th><th scope="col">Strikes</th><th scope="col">Demos</th><th scope="col">IMF</th><th scope="col">Events</th></tr></thead>
          <tbody>{''.join(count_rows)}</tbody>
        </table></div>
        <p class="story-note">Run it yourself: <code style="display:inline;padding:1px 5px">python sim/run.py --players 4 --seed 9</code> prints one game turn by turn; <code style="display:inline;padding:1px 5px">python sim/run.py --batch 300</code> repeats these statistics; <code style="display:inline;padding:1px 5px">python sim/test_rules.py</code> runs the rule checks.</p>
      </div>
    </section>
    <!-- SIM:END -->"""

    page = open(PAGE, encoding="utf-8").read()
    if "<!-- SIM:START" in page:
        page = re.sub(r"<!-- SIM:START.*?<!-- SIM:END -->", lambda m: section.strip(), page, flags=re.S)
    else:
        anchor = '    <!-- FAQ -->'
        assert page.count(anchor) == 1
        page = page.replace(anchor, section + "\n\n" + anchor)
    open(PAGE, "w", encoding="utf-8", newline="\n").write(page)
    print(f"page updated in {time.time() - t0:.0f}s; logs in {LOGS}", file=sys.stderr)


if __name__ == "__main__":
    build()
