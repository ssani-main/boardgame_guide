"""Run the Hegemony simulator.

  python run.py --players 4 --seed 7            one game, full turn-by-turn log to the console
  python run.py --players 4 --seed 7 --log g.txt   same, log written to a file
  python run.py --batch 300                     300 games per player count, summary statistics
"""
import argparse
import io
import sys
import time
import traceback
from collections import Counter, defaultdict

import engine

NAMES = engine.CLS_NAME


def one(players, seed, log=None):
    g = engine.Game(players=players, seed=seed, verbose=log is None)
    r = g.play()
    if log:
        with open(log, "w", encoding="utf-8") as f:
            f.write("\n".join(g.lines) + "\n")
        print(f"{len(g.lines)} log lines written to {log}")
    return g, r


def batch(n):
    report = {}
    t0 = time.time()
    for players in (2, 3, 4):
        wins, ties, vp, errors = Counter(), Counter(), defaultdict(list), []
        stats = Counter()
        for i, seed in enumerate(range(1, n + 1), 1):
            try:
                g = engine.Game(players=players, seed=seed, verbose=False)
                r = g.play()
            except Exception:
                errors.append((seed, traceback.format_exc().splitlines()[-1]))
                continue
            for c in r["winners"]:
                wins[c] += 1 / len(r["winners"])
            if len(r["winners"]) > 1 or r["reason"] != "most VP":
                ties[r["reason"]] += 1
            for c, v in r["vp"].items():
                vp[c].append(v)
            stats.update(g.stats)
            if i % 50 == 0 or i == n:
                el = time.time() - t0
                print(f"  {players}p: {i}/{n} games, {el:.0f}s elapsed", file=sys.stderr)
        done = n - len(errors)
        report[players] = dict(done=done, wins=wins, ties=ties, errors=errors,
                               vp={c: (sum(v) / len(v), min(v), max(v)) for c, v in vp.items()},
                               stats={k: v / max(1, done) for k, v in stats.items()})
        print(f"\n=== {players} players: {done} games ({len(errors)} errors) ===")
        for c in engine.ROLES_BY_COUNT[players]:
            avg, lo, hi = report[players]["vp"].get(c, (0, 0, 0))
            print(f"  {NAMES[c]:<11} wins {wins[c] / max(1, done):6.1%}   VP avg {avg:5.1f}  (min {lo}, max {hi})")
        if ties:
            print("  tie-breaks:", dict(ties))
        for e in errors[:5]:
            print("  ERROR seed", e[0], e[1])
        s = report[players]["stats"]
        keys = ["bills", "passed", "cards_played", "basic_actions", "built_C", "built_M", "strikes",
                "demonstrations", "imf", "state_loans", "events", "unions"]
        print("  per game: " + ", ".join(f"{k} {s.get(k, 0):.1f}" for k in keys))
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--players", type=int, default=4)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--log")
    ap.add_argument("--batch", type=int)
    a = ap.parse_args()
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if a.batch:
        batch(a.batch)
    else:
        one(a.players, a.seed, a.log)
