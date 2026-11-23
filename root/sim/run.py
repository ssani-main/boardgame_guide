"""Run the Root simulator.

  python run.py --players 4 --seed 7               one game, full turn-by-turn log to the console
  python run.py --factions MEA --seed 7            pick the factions (M, E, A, V)
  python run.py --players 4 --seed 7 --log g.txt   same, log written to a file
  python run.py --batch 300                        300 games per player count, summary statistics
"""
import argparse
import io
import sys
import time
import traceback
from collections import Counter, defaultdict

import data as D
import engine


def one(factions, seed, log=None):
    g = engine.Game(factions=factions, seed=seed, verbose=log is None)
    r = g.play()
    if log:
        with open(log, "w", encoding="utf-8") as f:
            f.write("\n".join(g.lines) + "\n")
        print(f"{len(g.lines)} log lines written to {log}")
    return g, r


def batch(n, counts=(2, 3, 4)):
    report = {}
    t0 = time.time()
    for players in counts:
        fs = D.DEFAULT_FACTIONS[players]
        wins, reasons, vp, rounds, errors, stats = Counter(), Counter(), defaultdict(list), [], [], Counter()
        for i, seed in enumerate(range(1, n + 1), 1):
            try:
                g = engine.Game(factions=fs, seed=seed, verbose=False)
                r = g.play()
            except Exception:
                errors.append((seed, traceback.format_exc().splitlines()[-1]))
                continue
            for f in r["winners"]:
                wins[f] += 1 / len(r["winners"])
            reasons[r["reason"]] += 1
            rounds.append(r["rounds"])
            for f, v in r["vp"].items():
                vp[f].append(v)
            stats.update(g.stats)
            if i % 50 == 0 or i == n:
                el = time.time() - t0
                print(f"  {players}p: {i}/{n} games, {el:.0f}s elapsed, {i / max(el, 1e-9):.0f} games/s", file=sys.stderr)
        done = n - len(errors)
        report[players] = dict(done=done, wins=wins, reasons=reasons, errors=errors,
                               rounds=sum(rounds) / max(1, len(rounds)),
                               vp={f: sum(v) / len(v) for f, v in vp.items()},
                               stats={k: v / max(1, done) for k, v in stats.items()})
        print(f"\n=== {players} players ({', '.join(D.NAME[f] for f in fs)}): {done} games, {len(errors)} errors ===")
        for f in fs:
            print(f"  {D.NAME[f]:<9} wins {wins[f] / max(1, done):6.1%}   VP avg {report[players]['vp'].get(f, 0):5.1f}")
        print(f"  ends: {dict(reasons)}; rounds avg {report[players]['rounds']:.1f}")
        for e in errors[:5]:
            print("  ERROR seed", e[0], e[1])
        s = report[players]["stats"]
        keys = ["battles", "ambush", "crafted", "favors", "revolts", "sympathy", "turmoil", "outrage",
                "field_hospitals", "explored", "quests", "aids", "hostile", "dominance"]
        print("  per game: " + ", ".join(f"{k} {s.get(k, 0):.1f}" for k in keys))
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--players", type=int, default=4)
    ap.add_argument("--factions")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--log")
    ap.add_argument("--batch", type=int)
    a = ap.parse_args()
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if a.batch:
        batch(a.batch)
    else:
        one(a.factions or D.DEFAULT_FACTIONS[a.players], a.seed, a.log)
