"""Heuristic bots, one per faction. They only choose; the engine checks every choice.

The bots play a sensible, greedy game. They are not strong players, so win rates describe these bots,
not the real game's balance.
"""
import copy
from itertools import combinations

import data as D
from engine import SUITS, GameOver, IllegalAction, matches

KEEP_ITEMS = ("sword", "boot", "torch", "hammer", "crossbow", "coins", "tea", "bag")   # most useful first (V)
GOOD_PERSIST = {"Armorers": 3, "Sappers": 3, "Brutal Tactics": 2, "Royal Claim": 4, "Command Warren": 3,
                "Cobbler": 2, "Tax Collector": 2, "Better Burrow Bank": 2, "Stand and Deliver!": 2,
                "Scouting Party": 2, "Codebreakers": 0}


def make(f, g):
    return {"M": Marquise, "E": Eyrie, "A": Alliance, "V": Vagabond}[f](f)


class Bot:
    def __init__(self, f):
        self.f = f

    # ---------------------------------------------------------------- card values
    def card_value(self, g, c):
        k = c["kind"]
        v = {"ambush": 6, "dominance": 4, "favor": 2}.get(k, 1)
        if k == "item":
            v = 1 + c["vp"] * (0.5 if self.f == "E" else 1)
        elif k == "persistent":
            v = 1 + GOOD_PERSIST.get(c["name"], 1) * (c["name"] not in g.persist[self.f])
        if c["suit"] == "bird":
            v += 1
        return v

    def cheapest(self, g, cards):
        return min(cards, key=lambda c: (self.card_value(g, c), c["id"]))

    def discard_down(self, g, n):
        return sorted(g.hands[self.f], key=lambda c: (self.card_value(g, c), c["id"]))[:n]

    def outrage_card(self, g, opts):
        return self.cheapest(g, opts)

    # ---------------------------------------------------------------- battle reactions
    def ambush(self, g, attacker, c):
        return True

    def foil(self, g, defender, c):
        return True

    def armorers(self, g, dealer, c, rolled):
        return rolled >= 2

    def sappers(self, g, attacker, c):
        return True

    def brutal(self, g, defender, c):
        return g.vp[defender] < 26

    def order_losses(self, g, c, pieces):
        rank = {"wood": 0, "sym": 1, "sawmill": 2, "recruiter": 3, "workshop": 4, "roost": 5, "keep": 9}
        return sorted(pieces, key=lambda p: (rank.get(p, 6), p))

    def field_hospital(self, g, c, n):
        return None

    # ---------------------------------------------------------------- shared Daylight choices
    def crafts(self, g):
        f = self.f
        out = []
        for c in sorted(g.hands[f], key=lambda c: -self.card_value(g, c)):
            if not g.can_craft(f, c):
                continue
            if c["kind"] == "item" and (c["vp"] >= 2 or f == "V" or len(g.hands[f]) >= 4):
                out.append(c)
            elif c["kind"] == "persistent" and GOOD_PERSIST.get(c["name"], 0) >= 2:
                out.append(c)
            elif c["kind"] == "favor" and self.favor_gain(g, c) >= 3:
                out.append(c)
        return out[:2]

    def favor_gain(self, g, card):
        suit = {"Foxes": "fox", "Mice": "mouse", "Rabbits": "rabbit"}[card["name"].split()[-1]]
        gain = 0
        for c in D.CLEARINGS:
            if g.suit(c) == suit:
                for d in g.factions:
                    if d not in (self.f, "V"):
                        gain += len(g.removable(c, d)) + g.cl[c]["w"][d] * 0.3
        return gain

    def dominance(self, g):
        f = self.f
        if f == "V" or g.vp[f] < 10 or g.vp[f] >= 24:
            return None
        # Dominance gives up all future points: a comeback tool, not something to play while winning the race
        if max(g.vp[x] for x in g.factions if x != f) < g.vp[f] - 2:
            return None
        for c in g.hands[f]:
            if c["kind"] != "dominance" or not g.can_activate_dominance(f, c):
                continue
            if c["suit"] == "bird":
                ok = any(g.rules(f, a) and g.rules(f, b) for a, b in ((1, 3), (2, 4)))
            else:
                ok = sum(1 for x in D.CLEARINGS if g.suit(x) == c["suit"] and g.rules(f, x)) >= 3
            if ok:
                return c
        return None

    def take_dominance(self, g):
        return None

    def bbb_target(self, g):
        others = [d for d in g.factions if d != self.f]
        return min(others, key=lambda d: (g.vp[d], d))

    def stand_and_deliver(self, g):
        others = [d for d in g.factions if d != self.f and g.hands[d] and g.vp[d] < 27]
        return max(others, key=lambda d: (len(g.hands[d]), -g.vp[d], d)) if others else None

    def royal_claim(self, g):
        return sum(1 for c in D.CLEARINGS if g.rules(self.f, c)) >= 4

    def free_battle(self, g):
        return self.best_battle(g)

    def tax_collector(self, g):
        if len(g.hands[self.f]) >= 4 or self.f == "V":
            return None
        spots = [c for c in D.CLEARINGS if g.cl[c]["w"][self.f] >= 3]
        return max(spots, key=lambda c: (g.cl[c]["w"][self.f], c)) if spots else None

    def free_move(self, g):
        return None

    # ---------------------------------------------------------------- battle targeting
    def dominance_threat(self, g, c, d):
        """True if d has an activated dominance card that c helps it win."""
        card = g.dominance.get(d)
        if not card or d == "V" or not g.rules(d, c):
            return False
        return c in D.CORNERS if card["suit"] == "bird" else g.suit(c) == card["suit"]

    def battle_value(self, g, c, d):
        f = self.f
        if not g.can_battle(f, c, d):
            return None
        if self.dominance_threat(g, c, d):
            return 10 + g.cl[c]["w"][f]
        if d == "V":
            return 0.5 if g.cl[c]["w"][f] >= 3 and g.rel.get(f) == "H" else None
        mine, theirs = g.cl[c]["w"][f], g.cl[c]["w"][d]
        stuff = len(g.removable(c, d))
        if d == "M" and g.cl[c]["keep"]:
            stuff += 2                          # "destroying her keep is a mighty blow" (overview card)
        p = self.pressure(g, d)
        if theirs == 0 and stuff:
            return 2 + stuff + 2 * p
        if mine >= theirs + (0 if p else 1) and mine >= 2:
            return 1 + 0.5 * min(theirs, 3) + 0.5 * stuff + 2 * p
        return None

    def pressure(self, g, d):
        """Guides: everyone pressures the cats from the start, and anyone pulling away gets reined in."""
        others = [g.vp[x] for x in g.factions if x not in (self.f, d)]
        runaway = g.vp[d] >= 10 and g.vp[d] >= max(others + [g.vp[self.f]]) + 3
        return runaway or (d == "M" and g.n >= 3)

    def best_battle(self, g):
        best = None
        for c in D.CLEARINGS:
            for d in g.factions:
                v = self.battle_value(g, c, d)
                if v is not None and (best is None or v > best[0]):
                    best = (v, c, d)
        return (best[1], best[2]) if best else None


# ==================================================================== Marquise
class Marquise(Bot):
    def choose_keep(self, g, corners):
        return g.rng.choice(corners)

    def choose_start_buildings(self, g, spots):
        free = {c: g.open_slots(c) for c in spots}
        out = []
        for t in ("sawmill", "workshop", "recruiter"):
            c = max(spots, key=lambda c: (c == spots[0], free[c], -c)) if free[spots[0]] else \
                max(spots[1:], key=lambda c: (free[c], -c))
            if free[c] <= 0:
                c = max(spots, key=lambda c: (free[c], -c))
            free[c] -= 1
            out.append((c, t))
        return out

    def field_hospital(self, g, c, n):
        if n < 2:
            return None
        opts = [x for x in g.cards_matching("M", g.suit(c)) if x["kind"] not in ("ambush", "dominance")]
        return self.cheapest(g, opts) if opts else None

    def hawks_for_hire(self, g):
        """Return the bird card to spend for one more action, or None."""
        birds = [c for c in g.hands["M"] if c["suit"] == "bird" and c["kind"] not in ("ambush", "dominance")]
        if len(g.hands["M"]) < 4 or not birds:
            return None
        bird = self.cheapest(g, birds)
        g.hands["M"].remove(bird)                # look ahead without the bird in hand
        useful = self.build_choice(g) or self.best_battle(g)
        g.hands["M"].append(bird)
        return bird if useful else None

    def build_choice(self, g):
        best = None
        for t in ("sawmill", "workshop", "recruiter"):
            cost = g.m_build_cost(t)
            if cost is None:
                continue
            for c in D.CLEARINGS:
                if not g.m_can_build(c, t):
                    continue
                vp = D.M_VP[t][g.m_on_map[t]]
                safety = g.cl[c]["w"]["M"] - max([g.cl[c]["w"][d] for d in g.factions if d != "M"] + [0])
                pref = {"sawmill": 1.2 if g.m_on_map["sawmill"] < 3 else 0.4, "workshop": 0.8, "recruiter": 1.0}[t]
                v = vp + pref + 0.2 * safety - 0.15 * cost
                if best is None or v > best[0]:
                    best = (v, c, t)
        return best

    def marquise_action(self, g):
        b = self.build_choice(g)
        if b:
            return ("build", b[1], b[2])
        if not g.m_recruited and g.m_on_map["recruiter"] and g.supply["M"]:
            return ("recruit",)
        t = self.best_battle(g)
        if t:
            return ("battle",) + t
        ow = self.overwork_choice(g)
        if ow:
            return ("overwork",) + ow
        moves = self.march_choice(g)
        if moves:
            return ("march", moves)
        return None

    def overwork_choice(self, g):
        if not g.wood_supply or len(g.hands["M"]) < 3:
            return None
        for c in D.CLEARINGS:
            if "sawmill" in g.buildings(c, "M"):
                opts = [x for x in g.cards_matching("M", g.suit(c)) if x["kind"] not in ("ambush", "dominance")
                        and not g.can_craft("M", x)]
                if opts:
                    return (c, self.cheapest(g, opts))
        return None

    def march_choice(self, g):
        moves = []
        src = sorted((c for c in D.CLEARINGS if g.cl[c]["w"]["M"] >= 3), key=lambda c: -g.cl[c]["w"]["M"])
        for a in src:
            for b in sorted(D.ADJ[a], key=lambda b: (g.rules("M", b), -g.open_slots(b), b)):
                if g.rules("M", b) or not g.can_move("M", a, b):
                    continue
                need = max([g.cl[b]["w"][d] + len(g.buildings(b, d)) for d in g.factions if d != "M"] + [0]) + 1
                n = min(g.cl[a]["w"]["M"] - 1, max(need, 2))
                if n > 0:
                    moves.append((a, b, n))
                    break
            if len(moves) == 2:
                break
        return moves


# ==================================================================== Eyrie
class Eyrie(Bot):
    def choose_eyrie_corner(self, g, opts):
        return opts[0]

    def choose_leader(self, g, opts):
        pref = ("Builder", "Charismatic", "Commander", "Despot")   # safest Vizier columns first
        if not hasattr(self, "led"):
            self.led = 0
        self.led += 1
        if self.led == 1 and "Charismatic" in opts:
            return "Charismatic"                # the guides' starting pick: two warriors per recruit
        return sorted(opts, key=lambda l: pref.index(l))[0]

    def new_roost(self, g, opts):
        return g.rng.choice(opts)

    def demand(self, g, col, suit):
        """Cards already in this column that need a clearing of this suit (birds need one anywhere)."""
        return sum(1 for c in g.decree[col] if c["suit"] in (suit, "bird"))

    def enemy_presence(self, g, c):
        return max([g.presence(c, d) for d in g.factions if d != "E"] + [0])

    def spare(self, g, a):
        """Warriors that can leave a without losing rule there."""
        w = g.cl[a]["w"]["E"]
        hold = self.enemy_presence(g, a) if "roost" in g.buildings(a, "E") else 0
        return max(0, w - max(1, hold) if "roost" in g.buildings(a, "E") else w)

    def takeable(self, g, c):
        """A clearing the Eyrie can rule this turn by moving in (Lords of the Forest: a tie is enough)."""
        if g.rules("E", c):
            return True
        need = self.enemy_presence(g, c) - g.presence(c, "E")
        return any(g.cl[a]["w"]["E"] and self.spare(g, a) >= max(1, need) and g.can_move("E", a, c) for a in D.ADJ[c])

    def potential(self, g, col, suit):
        """Clearings of this suit where the column could act next turn (looks one move ahead)."""
        cs = [c for c in D.CLEARINGS if matches(suit, g.suit(c))]
        if col == "recruit":
            return sum(1 for c in cs if "roost" in g.buildings(c, "E"))
        if col == "move":
            return sum(1 for c in cs if g.cl[c]["w"]["E"])
        if col == "battle":                     # any warrior next to an enemy will do, even a doomed one
            return sum(1 for c in cs if g.cl[c]["w"]["E"] >= 1
                       and any(g.has_pieces(c, d) for d in g.factions if d not in ("E", "V")))
        if len(g.roosts()) >= D.E_ROOSTS:
            return 0
        return max(0, sum(1 for c in cs if g.open_slots(c) > 0 and "roost" not in g.buildings(c, "E")
                          and g.can_place("E", c) and self.takeable(g, c)) - 1)

    def try_decree(self, g, adds):
        """Dry-run this turn's Decree with the added cards on a copy of the game (own dice). Returns (ok, value)."""
        sim = copy.deepcopy(g)
        sim.verbose = False
        for card, col in adds:
            c2 = next(x for x in sim.hands["E"] if x["id"] == card["id"])
            sim.hands["E"].remove(c2)
            sim.decree[col].append(c2)
        vp0 = sim.vp["E"]
        threats = [d for d in sim.factions if d != "E" and sim.dominance_won(d)]
        try:
            sim.e_new_roost()
            ok = sim.resolve_decree()
        except GameOver:
            return True, 1000
        except IllegalAction:
            ok = False
        nxt = 0
        if ok:                                  # one turn ahead: does the same Decree still resolve?
            ahead = copy.deepcopy(sim)
            try:
                ahead.e_new_roost()
                nxt = 0 if ahead.resolve_decree() else -8
            except GameOver:
                nxt = 0
            except IllegalAction:
                nxt = -8
        warriors = sum(sim.cl[c]["w"]["E"] for c in D.CLEARINGS)
        size = sum(len(v) for v in sim.decree.values())
        birds = sum(1 for _, col in adds if _["suit"] == "bird")
        broken = sum(15 if not sim.dominance_won(d) else -5 for d in threats)   # stop a dominance win
        value = broken + nxt + 4 * len(sim.roosts()) + 0.4 * warriors + (sim.vp["E"] - vp0) - 0.5 * size - 1.5 * birds \
            - 0.8 * sum(1 for c, col in adds if col in ("build", "battle") and c["suit"] != "bird")
        return ok, value

    def decree_add(self, g):
        """Plan like an experienced Eyrie player: only add cards whose whole Decree still resolves this turn."""
        hand = [c for c in g.hands["E"] if c["kind"] not in ("dominance", "ambush")] or list(g.hands["E"])
        if not hand:
            return []
        singles = []
        for c in hand:
            for col in D.DECREE_COLS:
                ok, v = self.try_decree(g, [(c, col)])
                if ok:
                    singles.append((v, c["id"], c, col))
        singles.sort(key=lambda x: (-x[0], x[1]))
        best = (singles[0][0], [(singles[0][2], singles[0][3])]) if singles else None
        if len(g.hands["E"]) >= 3:
            top = singles[:6]
            for a, b in combinations(top, 2):
                if a[2] is b[2] or (a[2]["suit"] == "bird" and b[2]["suit"] == "bird"):
                    continue
                adds = [(a[2], a[3]), (b[2], b[3])]
                ok, v = self.try_decree(g, adds)
                if ok and v > best[0]:
                    best = (v, adds)
        if best:
            return best[1]
        return self.decree_add_fallback(g)

    def decree_add_fallback(self, g):
        hand = [c for c in g.hands["E"] if c["kind"] not in ("dominance", "ambush")] or list(g.hands["E"])
        if not hand:
            return []
        size = sum(len(v) for v in g.decree.values())
        want = 2 if len(g.hands["E"]) >= 3 and size < 7 else 1
        picks, birds = [], 0
        for _ in range(want):
            best = None
            for c in hand:
                if c in [p[0] for p in picks] or (c["suit"] == "bird" and birds):
                    continue
                for col in D.DECREE_COLS:
                    if c["suit"] == "bird":             # a bird competes with every card in the column
                        room = sum(self.potential(g, col, s) for s in SUITS)
                        taken = len(g.decree[col]) + sum(1 for p in picks if p[1] == col)
                    else:
                        room = self.potential(g, col, c["suit"])
                        taken = self.demand(g, col, c["suit"]) + sum(1 for p in picks if p[1] == col)
                    if room <= taken:
                        continue
                    v = {"build": 4, "recruit": 3, "move": 2, "battle": 2.5}[col] - 0.8 * len(g.decree[col])
                    v += 0.4 * min(room - taken, 3) - (2 if c["suit"] == "bird" else 0)
                    if best is None or v > best[0]:
                        best = (v, c, col)
            if not best:
                break
            picks.append((best[1], best[2]))
            birds += best[1]["suit"] == "bird"
        if not picks:                           # must add a card (7.4.2): pick the least risky
            c = min(hand, key=lambda c: (c["suit"] == "bird", self.card_value(g, c)))
            col = max(D.DECREE_COLS, key=lambda col: (self.potential(g, col, c["suit"] if c["suit"] != "bird" else "fox")
                                                     - self.demand(g, col, c["suit"]), col == "move"))
            picks = [(c, col)]
        return picks

    def wanted_suits(self, g):
        return [c["suit"] for c in g.decree["build"]] + [c["suit"] for c in g.decree["battle"]]

    def decree_target(self, g, col, card, opts):
        if col == "recruit":
            return max(opts, key=lambda c: (self.enemy_presence(g, c) - g.cl[c]["w"]["E"], -c))
        if col == "move":
            want = self.wanted_suits(g)
            def v(o):
                a, b = o
                spare = self.spare(g, a)
                build_here = g.open_slots(b) > 0 and "roost" not in g.buildings(b, "E") and g.can_place("E", b)                     and any(matches(s, g.suit(b)) for s in want)
                need = self.enemy_presence(g, b) - g.presence(b, "E") + 1
                return (spare > 0, build_here and spare >= need, len(g.removable(b, "M")) if "M" in g.factions else 0,
                        spare, -b)
            return max(opts, key=v)
        if col == "battle":
            def bv(o):
                c, d = o
                stuff = len(g.removable(c, d)) if d != "V" else -2
                return (self.dominance_threat(g, c, d), stuff, g.cl[c]["w"]["E"] - g.cl[c]["w"][d], -c)
            return max(opts, key=bv)
        return max(opts, key=lambda c: (g.cl[c]["w"]["E"] - self.enemy_presence(g, c), -c))

    def move_count(self, g, a, b):
        spare = max(1, self.spare(g, a))
        need = self.enemy_presence(g, b) - g.presence(b, "E") + 1
        return min(g.cl[a]["w"]["E"], max(need, min(spare, need + 2), 1))


# ==================================================================== Alliance
class Alliance(Bot):
    def order_losses(self, g, c, pieces):
        return sorted(pieces, key=lambda p: (p.startswith("base"), p))

    def revolt(self, g):
        opts = g.a_revolt_options()
        if not opts:
            return None
        def v(c):
            return (5 * any(self.dominance_threat(g, c, d) for d in g.factions if d != "A")
                    + sum(len(g.removable(c, d)) for d in g.factions if d != "A")
                    + 0.3 * sum(g.cl[c]["w"][d] for d in g.factions if d != "A")
                    + sum(1 for x in g.sympathetic() if g.suit(x) == g.suit(c)))
        best = max(opts, key=lambda c: (v(c), -c))
        big = any(self.pressure(g, d) for d in g.factions if d != "A" and any(g.cl[best]["w"][d] or
                                                                              g.removable(best, d) for _ in [0]))
        return best if v(best) >= 2 or not g.bases or big else None

    def spread(self, g):
        opts = g.a_spread_options()
        if not opts:
            return None
        def v(c):
            danger = max([g.cl[c]["w"][d] for d in g.factions if d != "A"] + [0])
            return (-g.a_sympathy_cost(c), -danger, -c)
        best = max(opts, key=v)
        # keep two supporters of a suit for a revolt once three or more sympathies stand
        s = g.suit(best)
        if len(g.sympathetic()) >= 3 and not g.bases and g.a_supporters_of(s) - g.a_sympathy_cost(best) < 2 \
                and len(g.a_revolt_options()) == 0 and len(g.supporters) < 4:
            return None
        return best

    def mobilize(self, g):
        hand = sorted(g.hands["A"], key=lambda c: (self.card_value(g, c), c["id"]))
        keep = 2 if g.bases else 0              # guides: max out the Supporters stack early
        room = 99 if g.bases else D.A_SUPPORTER_CAP - len(g.supporters)
        out = [c for c in hand if c["kind"] not in ("ambush",) and not g.can_craft("A", c)]
        return out[:max(0, min(room, len(hand) - keep))]

    def train(self, g):
        if not g.bases or len(g.hands["A"]) < 2 or g.officers >= 4:
            return []
        opts = [c for c in g.hands["A"] if c["kind"] != "ambush" and any(matches(c["suit"], s) for s in g.bases)]
        return [self.cheapest(g, opts)] if opts else []

    def operation(self, g):
        if g.sym_placed < D.A_SYMPATHY:
            for c in D.CLEARINGS:
                if g.cl[c]["w"]["A"] and not g.cl[c]["sym"] and g.can_place("A", c):
                    return ("organize", c)
        t = self.best_battle(g)
        if t:
            return ("battle",) + t
        for c in sorted(g.bases.values()):
            if g.supply["A"]:
                return ("recruit", c)
        for a in D.CLEARINGS:
            if g.cl[a]["w"]["A"] >= 2:
                for b in D.ADJ[a]:
                    if not g.cl[b]["sym"] and g.can_move("A", a, b) and g.can_place("A", b):
                        return ("move", a, b, 1)
        return None


# ==================================================================== Vagabond
class Vagabond(Bot):
    def choose_character(self, g, opts):
        return g.rng.choice(opts)

    def choose_forest(self, g, opts):
        return g.rng.choice(opts)

    def card_value(self, g, c):
        v = super().card_value(g, c)
        return v + (1 if c["kind"] == "item" and c["item"] in ("boot", "sword", "hammer") else 0)

    def rank(self, it):
        return KEEP_ITEMS.index(it["t"])

    def refresh_order(self, g, down):
        return sorted(down, key=lambda i: (i["dmg"], self.rank(i)))

    def damage_item(self, g, ok):
        return max(ok, key=lambda i: (not i["up"], self.rank(i)))

    def drop_item(self, g, items):
        return max(items, key=lambda i: (i["t"] != "bag", i["dmg"], self.rank(i)))

    def strike_piece(self, g, opts):
        """9.5.6: the Vagabond picks which building or token to strike."""
        rank = {"keep": 0, "roost": 1}
        return min(opts, key=lambda p: (rank.get(p, 2 if not p.startswith("base") else 1), p))

    def repair_choice(self, g, dmg):
        return min(dmg, key=self.rank)

    def aid_item(self, g, ready):
        return max(ready, key=lambda i: (i["t"] not in ("boot", "sword", "torch", "hammer"), self.rank(i)))

    def day_labor(self, g, opts):
        return max(opts, key=lambda c: (self.card_value(g, c), c["id"]))

    def hurt(self, g):
        return sum(1 for i in g.vitems if i["dmg"])

    def clearing_value(self, g, c):
        v = 0
        if g.ruin_items.get(c) and g.v_ready("torch"):
            v += 3
        s = g.suit(c)
        if any(q[1] == s and all(any(i["t"] == t and not i["dmg"] for i in g.vitems) for t in q[2]) for q in g.quests):
            v += 3
        cards = len(g.cards_matching("V", s))
        ready = sum(1 for i in g.vitems if i["up"] and not i["dmg"])
        for f in g.factions:                    # aid only counts where a whole relationship step fits this turn
            if f == "V" or not g.has_pieces(c, f) or g.rel[f] == "H":
                continue
            need = 1 if g.rel[f] == 3 else D.V_REL_COST[g.rel[f]] - g.aids[f]
            if need <= min(cards, ready):
                v += 2 if g.rel[f] == 3 else D.V_REL_VP[g.rel[f]]
        v += sum(1 for f in g.factions if f != "V" and g.rel[f] == "H" and g.has_pieces(c, f)) * 0.5
        if any(self.dominance_threat(g, c, f) for f in g.factions if f != "V"):
            v += 4
        return v

    def slip(self, g):
        opts = g.v_slip_options()
        if self.hurt(g) >= 3 and isinstance(g.vag, int):
            forests = [o for o in opts if isinstance(o, str)]
            if forests:
                return forests[0]
        clear = [o for o in opts if isinstance(o, int)]
        here = self.clearing_value(g, g.vag) if isinstance(g.vag, int) else -1
        if not clear:
            return None
        best = max(clear, key=lambda c: (self.clearing_value(g, c), -c))
        if self.clearing_value(g, best) > here:
            return best
        return None

    def vagabond_action(self, g):
        c = g.vag
        if self.hurt(g) >= 3 and isinstance(c, str):
            return None                                  # resting in the forest
        if isinstance(c, int):
            if g.ruin_items.get(c) and g.v_ready("torch"):
                return ("explore",)
            qs = g.v_quest_options()
            if qs:
                early = g.round <= 3 or len(g.hands["V"]) < 3
                return ("quest", qs[0], "draw" if early and g.done_quests.count(qs[0][1]) == 0 else "vp")
            if g.v_ready("hammer") and any(i["dmg"] for i in g.vitems):
                return ("repair",)
            aid = self.aid_choice(g)
            if aid:
                return aid
            t = self.v_battle_target(g)
            if t:
                return ("battle", t)
            if g.v_ready("crossbow"):
                for f in g.factions:
                    hit = g.rel.get(f) == "H" or (g.round >= 4 and self.pressure(g, f) and f != "M") \
                        or (f == "M" and g.round >= 4 and g.vp["M"] >= max(g.vp.values()) and g.vp["M"] >= 12)
                    if f != "V" and hit and g.has_pieces(c, f):
                        return ("strike", f)
            sp = self.special(g)
            if sp:
                return sp
        moves = [m for m in g.v_move_options() if m != c]
        if moves and len(g.v_ready("boot")) >= 1:  # nothing left to do here: go where there is
            best = max(moves, key=lambda x: (self.clearing_value(g, x), -x))
            if self.clearing_value(g, best) > 0:
                return ("move", best)
        return None

    def aid_choice(self, g):
        """Aid only when the whole next relationship step fits in this turn (or the faction is Allied)."""
        c = g.vag
        opts = g.v_aid_options()
        cards = g.cards_matching("V", g.suit(c))
        ready = [i for i in g.vitems if i["up"] and not i["dmg"]]
        leader = max(g.vp.values())
        best = None
        for f in opts:
            r = g.rel[f]
            others = [g.vp[x] for x in g.factions if x not in ("V", f)]
            if r == "H" or (g.vp[f] == leader and g.vp[f] >= max(others + [0]) + 5) or g.vp[f] >= 24:
                continue                        # don't feed a runaway leader
            left = 1 if r == 3 else D.V_REL_COST[r] - g.aids[f]
            if left > min(len(cards), len(ready)):
                continue
            v = (2 if r == 3 else D.V_REL_VP[r]) / left + (g.aids[f] > 0) * 2 - g.vp[f] / 30
            if best is None or v > best[0]:
                best = (v, f)
        if not best:
            return None
        f = best[1]
        take = next((t for t in KEEP_ITEMS if t in g.crafted[f]), None)
        return ("aid", f, self.cheapest(g, cards), take)

    def v_battle_target(self, g):
        c = g.vag
        swords = sum(1 for i in g.vitems if i["t"] == "sword" and not i["dmg"])
        if not g.v_ready("sword"):
            return None
        for f in g.factions:
            if f != "V" and g.cl[c]["w"][f] and self.dominance_threat(g, c, f):
                return f
        if swords < 2:
            return None
        best = None
        for f in g.factions:
            if f == "V" or not g.has_pieces(c, f):
                continue
            hostile = g.rel[f] == "H"
            stuff = len(g.removable(c, f))
            w = g.cl[c]["w"][f]
            others = [g.vp[x] for x in g.factions if x not in ("V", f)]
            runaway = g.round >= 4 and g.vp[f] >= 12 and g.vp[f] >= max(others + [g.vp["V"]]) + 4
            if (hostile or runaway) and w <= swords + 1:
                v = 2 + stuff + 2 * runaway
            elif w == 0 and stuff and g.rel[f] in (0,):
                v = stuff
            else:
                continue
            if best is None or v > best[0]:
                best = (v, f)
        return best[1] if best else None

    def special(self, g):
        c = g.vag
        if not g.v_ready("torch"):
            return None
        if g.char == "Thief":
            opts = [f for f in g.factions if f != "V" and g.has_pieces(c, f) and g.hands[f]]
            if opts:
                return ("special", max(opts, key=lambda f: (len(g.hands[f]), f)))
        elif g.char == "Tinker":
            if any(matches(x["suit"], g.suit(c)) for x in g.discard) and len(g.hands["V"]) < 5:
                return ("special",)
        elif self.hurt(g) >= 3:
            return ("special",)
        return None
