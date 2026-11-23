"""Heuristic bot players, one per class. They only choose; every rule lives in engine.py.

Each turn a bot lists its legal Basic Actions and playable cards with a rough score (VP-ish units),
plays the best one (a card for its effect, or the weakest card discarded for a Basic Action) and
uses one Free Action before or after.
"""
import math
from collections import Counter

import data as D

SECT = "ABC"
PREF = {  # preferred section per policy (from the classes' interests described in rulebook + guides)
    "W": {1: "A", 2: "A", 3: "B", 4: "A", 5: "A", 6: "C", 7: "A"},
    "M": {1: "B", 2: "B", 3: "B", 4: "B", 5: "B", 6: "C", 7: "A"},
    "C": {1: "C", 2: "C", 3: "C", 4: "C", 5: "C", 6: "A", 7: "C"},
    "S": {1: "B", 2: "B", 3: "A", 4: "B", 5: "B", 6: "B", 7: "B"},
}
WEIGHT = {
    "W": {1: 1, 2: 3, 3: 1, 4: 3, 5: 2, 6: 2, 7: 1},
    "M": {1: 1, 2: 1, 3: 2, 4: 2, 5: 2, 6: 2, 7: 2},
    "C": {1: 2, 2: 3, 3: 3, 4: 2, 5: 2, 6: 2, 7: 1},
    "S": {1: 2, 2: 1, 3: 3, 4: 2, 5: 2, 6: 1, 7: 1},
}


def dist(a, b):
    return abs(SECT.index(a) - SECT.index(b))


def step_toward(cur, want):
    i, j = SECT.index(cur), SECT.index(want)
    return SECT[i + (1 if j > i else -1)]


class Bot:
    def __init__(self, cls, game):
        self.c = cls
        self.g = game
        self.free_used = False

    # ---------------------------------------------------------------- politics
    def pref(self, p):
        if self.c == "S" and self.g.agenda and p in self.g.agenda["targets"]:
            return self.g.agenda["targets"][p]
        return PREF[self.c][p]

    def weight(self, p):
        return WEIGHT[self.c][p]

    def vote(self, p, cur, target):
        return dist(target, self.pref(p)) < dist(cur, self.pref(p))

    def spend_influence(self, p, side, tally, owner):
        g = self.g
        mine, theirs = tally[side], tally[not side]
        need = (theirs - mine) if side else (mine - theirs + 1)
        if side is False:
            need = theirs - mine + 1 if theirs >= mine else 0
            need = tally[True] - tally[False] + 1 if tally[True] >= tally[False] else 0
        else:
            need = max(0, tally[False] - tally[True])
        if need <= 0:
            return 0
        if need <= g.influence[self.c] and (owner == self.c or self.weight(p) >= 2):
            return need
        return 0

    def best_bill(self, only=None, any_section=False):
        g = self.g
        best = None
        for p in range(1, 8):
            if only and p != only:
                continue
            if p in g.bills or p in g.blocked:
                continue
            cur, want = g.policies[p], self.pref(p)
            if cur == want:
                continue
            target = want if any_section else step_toward(cur, want)
            sc = self.weight(p) * dist(cur, want)
            if best is None or sc > best[0]:
                best = (sc, p, target)
        return best

    def support_share(self, p, target):
        g = self.g
        cur = g.policies[p]
        tot = sum(g.bag.values()) or 1
        fav = 0
        for c in "WMC":
            if c not in g.roles:
                continue
            if c == self.c or g.bots[c].vote(p, cur, target):
                fav += g.bag[c]
        return fav / tot

    def do_bill(self, only=None, any_section=False, allow_immediate=True, free_immediate=False, extra_cubes=0):
        g = self.g
        if extra_cubes:
            g.add_cubes(self.c, extra_cubes)
        b = self.best_bill(only, any_section)
        if not b or g.bill_markers[self.c] <= 0:
            return False
        _, p, target = b
        share = self.support_share(p, target) if self.c != "S" else 0.4
        immediate = allow_immediate and (free_immediate or g.influence[self.c] >= 2) and share >= 0.55
        return g.propose(self.c, p, target, immediate=immediate, free_immediate=free_immediate)

    def bill_score(self):
        b = self.best_bill()
        if not b or self.g.bill_markers[self.c] <= 0:
            return None
        return 1.0 + 0.6 * b[0]

    # ---------------------------------------------------------------- workers
    def pick_team(self, co, pool):
        """Choose workers from pool to fill every slot of co, or None."""
        free = [w for w in pool if not w.committed]
        team, used = [], set()
        for i, skill in enumerate(co.slots):
            if skill is not None:
                cand = [w for w in free if w.id not in used and w.skill == skill]
            else:
                cand = [w for w in free if w.id not in used and w.skill is None] or \
                       [w for w in free if w.id not in used]
            if not cand:
                return None
            w = cand[0]
            used.add(w.id)
            team.append((i, w))
        return team

    def upgrade_worker(self):
        g = self.g
        need = Counter()
        for co in g.companies.values():
            if co.face_up and not co.operational() and not co.auto:
                for s in co.slots:
                    if s:
                        need[s] += 1
        unsk = [w for w in g.class_workers(self.c) if w.skill is None]
        if not unsk:
            return
        w = sorted(unsk, key=lambda w: w.loc is not None)[0]
        w.skill = need.most_common(1)[0][0] if need else "health"
        g.log(f"trains a worker → skilled ({w.skill})", self.c)

    def pick_skill(self):
        g = self.g
        need = Counter()
        for co in g.companies.values():
            if co.face_up and not co.operational():
                for s in co.slots:
                    if s:
                        need[s] += 1
        for spec in g.mc_market:
            if spec["mc"][0]:
                need[spec["mc"][0]] += 2
        return need.most_common(1)[0][0] if need else "food"

    def wage_of(self, co, cls):
        if co.owner == "M" and cls == "W":
            return co.emp_wage()
        return co.wage() / max(1, len(co.slots))

    def assign_options(self, cls=None):
        """Companies this class could staff now with unemployed workers: list of (score, co, team)."""
        g = self.g
        cls = cls or self.c
        pool = g.unemployed(cls)
        opts = []
        for co in g.companies.values():
            if not co.face_up or co.coop:
                continue
            if co.owner == "M" and cls == "W":
                if co.emp and co.operational() and co.emp_worker is None:
                    cand = [w for w in pool if w.skill is None] or pool
                    if cand:
                        opts.append((co.emp_wage(), co, [("emp", cand[0])]))
                continue
            if co.owner == "M" and cls == "M" and not co.operational():
                team = self.pick_team(co, pool)
                if team:
                    opts.append((99, co, team))
                continue
            if co.owner == "M" or co.operational() or co.auto:
                continue
            team = self.pick_team(co, pool)
            if team:
                opts.append((co.wage() / len(co.slots), co, team))
        opts.sort(key=lambda o: -o[0])
        return opts

    def do_assign(self, max_n=3, pay_each=0):
        g = self.g
        left = max_n
        placed = 0
        for _ in range(6):
            opts = [o for o in self.assign_options() if len(o[2]) <= left]
            if not opts:
                break
            _, co, team = opts[0]
            for slot, w in team:
                g.put(w, co, slot, committed=True)
                if pay_each and co.owner != self.c:
                    g.pay(co.owner, pay_each, to=self.c, why="Signing bonus")
            left -= len(team)
            placed += len(team)
            g.log(f"assigns {len(team)} worker(s) to {co.name} ({CLS(co.owner)})", self.c)
        if self.c == "W" and left > 0:
            placed += self.form_union()
        g.stats[f"assigned_{self.c}"] += placed
        return placed > 0

    def form_union(self):
        g = self.g
        for w in g.unemployed("W"):
            if w.skill and w.skill not in g.unions and g.industry_count("W", w.skill) >= 4:
                g.unions[w.skill] = w.id
                w.loc = ("union", w.skill)
                w.committed = True
                g.log(f"forms the {w.skill} Trade Union", "W")
                g.stats["unions"] += 1
                return 1
        return 0

    # ---------------------------------------------------------------- shared helpers
    def food_unit(self):
        g = self.g
        prices = [g.unit_price(self.c, s, "food") for s in g.sources(self.c, "food") if s != self.c]
        return min(prices) if prices else 15

    def expected_wages(self):
        g = self.g
        tot = 0
        for co in g.companies.values():
            if not co.face_up or not co.operational() or co.auto:
                continue
            if co.owner == "M" and co.emp_worker and g.workers[co.emp_worker].cls == self.c:
                tot += co.emp_wage()
            elif co.owner != "M" and co.workers and co.workers[0] and g.workers[co.workers[0]].cls == self.c:
                tot += co.wage()
        return tot

    def receive_benefits(self):
        g = self.g
        b = g.benefits.get(self.c)
        if not b or not sum(b.values()):
            return False
        for k, n in b.items():
            if k == "money":
                g.receive(self.c, n)
            elif k == "cubes":
                g.add_cubes(self.c, n)
            elif k == "infl":
                g.influence[self.c] += n
            elif self.c in ("W", "M"):
                g.gs[self.c][k] += n
            else:
                g.storage["C"][k] += n
        g.log(f"Receive Benefits: {dict(b)}", self.c)
        g.benefits[self.c] = Counter()
        g.gain_vp("S", 1, "Benefits received")
        return True

    def pay_loan_if_rich(self):
        g = self.g
        if g.loans[self.c] and g.cash(self.c) >= 50 + self.reserve():
            g.pay(self.c, 50, why="pay off Loan", from_capital=True, forced=False)
            g.loans[self.c] -= 1
            g.log("pays off a Loan (50₩)", self.c)
            return True
        return False

    def reserve(self):
        return 0

    def on_strike(self, co):
        pass

    def after_labor_change(self):
        pass

    def set_prices(self):
        pass

    def refresh_market(self):
        pass

    # ---------------------------------------------------------------- turn
    def take_turn(self):
        g = self.g
        self.free_used = False
        self.free_action(before=True)
        options = self.basic_options()
        best_basic = max(options, key=lambda o: o[0]) if options else (0, None, "nothing")
        best_card = None
        for card in sorted(set(g.hands[self.c])):
            ok, score, fn = g.cards.evaluate(card, self)
            if ok and (best_card is None or score > best_card[0]):
                best_card = (score, card, fn)
        if best_card and best_card[0] > best_basic[0]:
            score, card, fn = best_card
            g.hands[self.c].remove(card)
            g.discards[self.c].append(card)
            g.log(f"plays card «{card}»", self.c)
            g.cards_played[(self.c, card)] += 1
            g.stats["cards_played"] += 1
            if fn() is not False:
                g.cards.apply_legitimacy(card, self)
        else:
            card = self.worst_card()
            g.hands[self.c].remove(card)
            g.discards[self.c].append(card)
            g.stats["basic_actions"] += 1
            if best_basic[1]:
                g.log(f"discards «{card}» → Basic Action: {best_basic[2]}", self.c)
                best_basic[1]()
        self.free_action(before=False)

    def worst_card(self):
        g = self.g
        scored = []
        for card in g.hands[self.c]:
            ok, score, _ = g.cards.evaluate(card, self)
            scored.append((score if ok else g.cards.static_value(card), card))
        return min(scored)[1]

    def free_action(self, before):
        if self.free_used:
            return
        if self.free_choice(before):
            self.free_used = True

    def free_choice(self, before):
        return False


def CLS(c):
    return {"W": "Working", "M": "Middle", "C": "Capitalist", "S": "State"}[c]


# ============================================================================ Working Class
class WorkingBot(Bot):
    def reserve(self):
        g = self.g
        rate = D.INCOME_TAX[g.policies[2]][g.policies[3]]
        return g.pop("W") * (self.food_unit() + rate) + 5 * g.loans["W"] - self.expected_wages()

    def spendable(self):
        return max(0, min(self.g.money["W"], self.g.money["W"] - max(0, self.reserve())))

    def buy_plan(self, res, budget=None, half=False, only=None):
        """Cost to reach Population units of res (from up to 2 sources), or None."""
        g = self.g
        need = g.pop(self.c) - g.gs[self.c][res]
        if need <= 0:
            return 0, 0
        srcs = sorted([s for s in g.sources(self.c, res) if only is None or s in only],
                      key=lambda s: g.unit_price(self.c, s, res))
        cost, got = 0, 0
        for s in srcs[:2]:
            n = min(need - got, g.stock(s, res), g.pop(self.c))
            unit = g.unit_price(self.c, s, res)
            if s == "F":
                unit = sum(g.import_price(res))
            cost += unit * n
            got += n
            if got >= need:
                break
        if got < need:
            return None
        if half:
            cost = math.ceil(cost / 2)
        return cost, need

    def buy_target(self, half=False, only=None, ress=("health", "edu", "lux")):
        g = self.g
        budget = self.spendable()
        nxt = (D.WC_PROSPERITY if self.c == "W" else D.MC_PROSPERITY)[min(10, g.prosperity[self.c] + 1)]
        best = None
        for res in ress:
            plan = self.buy_plan(res, half=half, only=only)
            if plan is None or plan[1] == 0:
                continue
            cost, n = plan
            if cost > budget:
                continue
            val = nxt + 2 + (2 if res == "health" else 1 if res == "edu" else 0) - cost / 25
            if g.round == 5 or g.money[self.c] > 120:
                val += 3
            if best is None or val > best[0]:
                best = (val, res)
        return best

    def do_buy(self, res=None, half=False, only=None, cap=None, max_sources=2, state_pays_half=False):
        g = self.g
        if res is None:
            t = self.buy_target(half=half, only=only)
            if not t:
                return False
            res = t[1]
        need = max(1, g.pop(self.c) - g.gs[self.c][res])
        got = g.buy_best(self.c, res, max_sources=max_sources, cap=cap or need, only=only, half_price=half,
                         budget=self.spendable(), state_pays_half=state_pays_half)
        return got > 0

    def basic_options(self):
        g = self.g
        o = []
        a = self.assign_options()
        if a and g.unemployed("W"):
            o.append((3 + min(3, len(a)), lambda: self.do_assign(3), "Assign Workers"))
        elif self.can_union():
            o.append((4, lambda: self.do_assign(3), "Assign Workers (Trade Union)"))
        t = self.buy_target()
        if t:
            o.append((t[0], lambda r=t[1]: self.do_buy(r), f"Buy {t[1]}"))
        if g.demo_condition() and not g.demonstration:
            o.append((3 + (len(g.unemployed("W")) + len(g.unions)) / 3, self.do_demo, "Demonstration"))
        s = self.strike_targets()
        if s and g.money["W"] > self.reserve() + 20:
            o.append((2.5, lambda: self.do_strike(2), "Strike"))
        b = self.bill_score()
        if b:
            o.append((b, self.do_bill, "Propose Bill"))
        o.append((1.5, lambda: g.add_cubes("W", 3) and g.log("adds 3 cubes to the bag (Political Pressure)", "W"),
                  "Apply Political Pressure"))
        return o

    def can_union(self):
        g = self.g
        return any(w.skill and w.skill not in g.unions and g.industry_count("W", w.skill) >= 4
                   for w in g.unemployed("W"))

    def strike_targets(self):
        g = self.g
        out = []
        for co in g.companies.values():
            if co.owner in ("C",) or (co.owner == "S" and "S" in g.roles) or (co.owner == "M" and co.emp_worker):
                ids = [co.emp_worker] if co.owner == "M" else co.workers
                ws = [g.workers[i] for i in ids if i]
                if ws and all(w.cls == "W" and not w.committed for w in ws) and co.level < 3 and \
                        co.operational() and not co.strike:
                    out.append(co)
        return out

    def do_strike(self, n):
        for co in self.strike_targets()[:n]:
            co.strike = True
            self.g.log(f"Strike token on {co.name}", "W")
            self.g.stats["strikes"] += 1
            self.g.bots[co.owner].on_strike(co)
        return True

    def do_demo(self):
        self.g.demonstration = True
        self.g.stats["demonstrations"] += 1
        self.g.log(f"Demonstration ({len(self.g.unemployed('W'))} unemployed)", "W")
        return True

    def free_choice(self, before):
        g = self.g
        for res in ("health", "edu", "lux"):
            if g.gs[self.c][res] >= g.pop(self.c):
                return g.use_resource(self.c, res)
        if self.receive_benefits():
            return True
        if not before and self.swap_workers():
            return True
        if not before:
            return self.pay_loan_if_rich()
        return False

    def swap_workers(self):
        g = self.g
        for w in g.class_workers(self.c):
            if w.skill and w.loc and w.loc[0] == "co" and w.loc[2] != "emp":
                co = g.companies[w.loc[1]]
                if co.slots[w.loc[2]] is None:
                    for u in g.unemployed(self.c):
                        if u.skill is None:
                            slot = w.loc[2]
                            committed = w.committed
                            g.unplace(w)
                            g.put(u, co, slot, committed)
                            g.log(f"swaps a skilled {w.skill} worker out of {co.name}", self.c)
                            return True
        return False

    def on_strike(self, co):
        pass


# ============================================================================ Middle Class
class MiddleBot(WorkingBot):
    def reserve(self):
        g = self.g
        own_food = sum(c.production() for c in g.co_of("M") if c.ind == "food" and c.operational())
        short = max(0, g.pop("M") - own_food - g.storage["M"]["food"])
        rate = D.INCOME_TAX[g.policies[2]][g.policies[3]]
        jobs = len({w.loc[1] for w in g.class_workers("M") if w.loc and w.loc[0] == "co"
                    and g.companies[w.loc[1]].owner != "M"})
        ops = sum(1 for c in g.co_of("M") if c.operational())
        emp_wages = sum(c.emp_wage() for c in g.co_of("M") if c.emp_worker)
        return short * self.food_unit() + rate * jobs + ops * g.tax_mult() + emp_wages + 5 * g.loans["M"] \
            - self.expected_wages()

    def spendable(self):
        return max(0, min(self.g.money["M"], self.g.money["M"] - max(0, self.reserve())))

    def buy_plan(self, res, budget=None, half=False, only=None):
        g = self.g
        need = g.pop("M") - g.gs["M"][res]
        if need <= 0:
            return 0, 0
        own = min(need, g.storage["M"][res], g.pop("M")) if (only is None or "M" in only) else 0
        rest = need - own
        cost = 0
        if rest > 0:
            srcs = sorted([s for s in g.sources("M", res) if s != "M" and (only is None or s in only)],
                          key=lambda s: g.unit_price("M", s, res))
            if not srcs:
                return None
            s = srcs[0]
            n = min(rest, g.stock(s, res), g.pop("M"))
            if n < rest:
                return None
            unit = sum(g.import_price(res)) if s == "F" else g.unit_price("M", s, res)
            cost = unit * n
        return (math.ceil(cost / 2) if half else cost), need

    def do_buy(self, res=None, half=False, only=None, cap=None, max_sources=2):
        g = self.g
        if res is None:
            t = self.buy_target(half=half, only=only)
            if not t:
                return False
            res = t[1]
        need = g.pop("M") - g.gs["M"][res]
        own = min(need, g.storage["M"][res], g.pop("M"))
        got = 0
        if own and (only is None or "M" in only):
            g.storage["M"][res] -= own
            g.gs["M"][res] += own
            g.log(f"moves {own} {res} from own storage", "M")
            got += own
            max_sources -= 1
        if need - got > 0 and max_sources > 0:
            got += g.buy_best("M", res, max_sources=max_sources, cap=need - got,
                              only=[s for s in (only or "CSF") if s != "M"], half_price=half,
                              budget=self.spendable())
        return got > 0

    def build_options(self, discount=0):
        g = self.g
        opts = []
        if len(g.co_of("M")) >= 8:
            return opts
        for spec in g.mc_market:
            cost = max(0, spec["cost"] - discount)
            if cost > self.spendable() + 10:
                continue
            fake = type("X", (), {"slots": spec["mc"]})
            team = self.pick_team(fake, g.unemployed("M"))
            if not team:
                continue
            val = spec["out"] + spec.get("bonus", 0) / 2
            opts.append((3 + val / 2 - cost / 20, spec, team))
        opts.sort(key=lambda o: -o[0])
        return opts

    def do_build(self, discount=0, state_pays=False, discount_res=None, spec_only=None):
        g = self.g
        opts = self.build_options(discount if not state_pays else 99)
        if spec_only is not None:
            opts = [o for o in opts if o[1] is spec_only]
        if not opts:
            return False
        _, spec, team = opts[0]
        if discount_res and D.PRODUCT[spec["ind"]] != discount_res:
            discount = 0
        cost = max(0, spec["cost"] - discount)
        if state_pays:
            g.pay("S", spec["cost"], why="Small business grant")
        elif not g.pay("M", cost, why="build", forced=False):
            return False
        g.mc_market.remove(spec)
        co = g.new_company(spec, "M")
        co.level = g.min_wage()
        for slot, w in team:
            g.put(w, co, slot, committed=True)
        if co.emp:
            cand = [w for w in g.unemployed("W") if w.skill is None] or g.unemployed("W")
            if cand:
                g.put(cand[0], co, "emp", committed=True)
        g.log(f"builds {co.name} ({spec['cost']}₩{' paid by State' if state_pays else ''})", "M")
        g.cancel_demonstration(co.emp_worker is not None)
        g.stats["built_M"] += 1
        return True

    def export_plan(self, mult=1):
        g = self.g
        need = Counter()
        p = g.pop("M")
        st = g.storage["M"]
        total, n, plan = 0, 0, []
        for res, offers in g.export.items():
            keep = 0 if res == "food" else min(p, st[res]) if g.gs["M"][res] < p else 0
            avail = st[res] - (p if res == "food" else 0) - keep
            for amount, price in sorted(offers, key=lambda o: -o[1] / o[0]):
                for _ in range(mult):
                    if avail >= amount:
                        plan.append((res, amount, price))
                        avail -= amount
                        total += price
                        n += 1
        return total, n, plan

    def do_export(self, mult=1, bonus_each=0):
        g = self.g
        total, n, plan = self.export_plan(mult)
        if not n:
            return False
        for res, amount, price in plan:
            g.storage["M"][res] -= amount
        g.receive("M", total)
        g.log(f"sells to the Foreign Market: {n} offer(s) for {total}₩", "M")
        g.gain_vp("M", n, "export transactions")
        if bonus_each:
            g.pay("S", bonus_each * n, to="M", why="Export subsidy")
        return True

    def extra_shift_target(self):
        g = self.g
        for co in g.co_of("M"):
            mcw = [g.workers[i] for i in co.workers if i]
            if co.operational() and mcw and not any(w.committed for w in mcw) and not co.strike:
                return co
        return None

    def do_extra_shift(self, co=None):
        g = self.g
        co = co or self.extra_shift_target()
        if not co:
            return False
        for i in co.workers:
            g.workers[i].committed = True
        emp_on = co.emp_worker and not g.workers[co.emp_worker].committed
        if emp_on:
            if not g.pay("M", co.emp_wage(), to="W", why="extra shift wage", forced=False):
                emp_on = False
        amount = co.out + (co.bonus if emp_on else 0)
        g.store("M", D.PRODUCT[co.ind], amount)
        g.log(f"Extra Shift at {co.name}: +{amount} {D.PRODUCT[co.ind]}", "M")
        return True

    def basic_options(self):
        g = self.g
        o = []
        b = self.build_options()
        if b:
            o.append((b[0][0], self.do_build, f"Build Company ({b[0][1]['name']})"))
        a = self.assign_options()
        if a and g.unemployed("M"):
            o.append((2.5 + min(2, len(a)), lambda: self.do_assign(3), "Assign Workers"))
        t = self.buy_target()
        if t:
            o.append((t[0], lambda r=t[1]: self.do_buy(r), f"Buy {t[1]}"))
        total, n, _ = self.export_plan()
        if n:
            o.append((n + total / 25, self.do_export, "Sell to Foreign Market"))
        es = self.extra_shift_target()
        if es:
            o.append((1.5 + es.out / 3, self.do_extra_shift, "Extra Shift"))
        bs = self.bill_score()
        if bs:
            o.append((bs, self.do_bill, "Propose Bill"))
        o.append((1.5, lambda: g.add_cubes("M", 3) and g.log("adds 3 cubes (Political Pressure)", "M"),
                  "Apply Political Pressure"))
        return o

    def free_choice(self, before):
        g = self.g
        for res in ("health", "edu", "lux"):
            if g.gs["M"][res] >= g.pop("M"):
                return g.use_resource("M", res)
        if self.receive_benefits():
            return True
        if not before:
            return self.set_prices(log=False) or self.pay_loan_if_rich()
        return False

    def set_prices(self, log=True):
        return set_prices(self.g, "M")

    def refresh_market(self):
        g = self.g
        while len(g.mc_market) < 3 and g.mc_deck:
            g.mc_market.append(g.mc_deck.pop())

    def after_labor_change(self):
        g = self.g
        for co in g.co_of("M"):
            if not (co.emp_worker and g.workers[co.emp_worker].committed):
                co.level = g.min_wage()

    def on_strike(self, co):
        pass


def set_prices(g, cls):
    """Owners price local goods just under the imported price (Food, Luxury) or the State price."""
    changed = False
    for res, slots in D.PRICE_SLOTS.items():
        if res in ("food", "lux"):
            ref = sum(g.import_price(res))
        else:
            ref = g.state_price(res) if g.stock("S", res) else 12
            ref = max(ref, 9)
        ok = [s for s in slots if s < ref] or [slots[0]]
        new = max(ok)
        if g.prices[cls][res] != new:
            g.prices[cls][res] = new
            changed = True
    return changed


# ============================================================================ Capitalist
class CapitalistBot(Bot):
    def reserve(self):
        g = self.g
        wages = sum(c.wage() for c in g.co_of("C") if c.operational() and not c.auto)
        ops = sum(1 for c in g.co_of("C") if c.operational())
        return wages + ops * g.tax_mult() + 10

    def spendable(self):
        return max(0, self.g.cash("C") - self.reserve())

    def value(self, res):
        g = self.g
        best = 0
        for amount, price in g.export.get(res, []):
            best = max(best, price / amount)
        local = g.prices["C"].get(res, 0)
        return max(best, local * 0.6) if res != "infl" else 6

    def company_value(self, spec):
        g = self.g
        res = D.PRODUCT[spec["ind"]]
        rev = spec["out"] * self.value(res)
        wage = spec["wages"][g.min_wage() - 1] if not spec.get("auto") else 0
        return rev - wage - g.tax_mult()

    def build_options(self, discount=0, filt=None):
        g = self.g
        if len(g.co_of("C")) >= 12:
            return []
        opts = []
        for spec in g.cc_market:
            if filt and not filt(spec):
                continue
            cost = max(0, spec["cost"] - discount)
            if cost > self.spendable():
                continue
            team = None
            if not spec.get("auto"):
                fake = type("X", (), {"slots": spec["slots"]})
                for cls in ("W", "M"):
                    if cls in g.roles:
                        team = self.pick_team(fake, g.unemployed(cls))
                        if team:
                            break
            profit = self.company_value(spec)
            rounds_left = 6 - g.round
            sc = (profit * rounds_left - cost) / 15 + (2 if team or spec.get("auto") else -1)
            opts.append((sc, spec, team))
        opts.sort(key=lambda o: -o[0])
        return opts

    def do_build(self, discount=0, filt=None, state_half=False, n=1):
        g = self.g
        done = 0
        for _ in range(n):
            opts = self.build_options(discount, filt)
            if not opts or opts[0][0] < 0:
                break
            _, spec, team = opts[0]
            cost = max(0, spec["cost"] - discount)
            if state_half:
                half = math.ceil(spec["cost"] / 2)
                g.pay("C", half, why="build")
                g.pay("S", spec["cost"] - half, why="Industrialization")
            else:
                g.pay("C", cost, why="build")
            g.cc_market.remove(spec)
            co = g.new_company(spec, "C")
            co.level = g.min_wage()
            staffed = ""
            if team:
                for slot, w in team:
                    g.put(w, co, slot, committed=True)
                staffed = f", hires {len(team)} {CLS(team[0][1].cls)} worker(s)"
            g.log(f"builds {co.name} for {cost}₩ (wage L{co.level}){staffed}", "C")
            g.cancel_demonstration(bool(team) and team[0][1].cls == "W")
            g.stats["built_C"] += 1
            done += 1
        return done > 0

    def export_plan(self, mult=1, extra=None):
        g = self.g
        st = g.storage["C"] + g.ftz
        total, n, plan = 0, 0, []
        for res, offers in g.export.items():
            avail = st[res] - (2 if res == "food" else 0)
            for amount, price in sorted(offers, key=lambda o: -o[1] / o[0]):
                if avail >= amount:
                    plan.append((res, amount, price))
                    avail -= amount
                    total += price
                    n += 1
        return total, n, plan

    def do_export(self, extra=None, only=None):
        g = self.g
        total, n, plan = self.export_plan()
        plan = [p for p in plan if only is None or p[0] in only]
        total = sum(p[2] for p in plan)
        for res, amount, price in plan:
            take = min(amount, g.ftz[res])
            g.ftz[res] -= take
            g.storage["C"][res] -= amount - take
        if extra:
            res, k, price = extra
            sold = min(k, g.storage["C"][res])
            g.storage["C"][res] -= sold
            total += sold * price
        if total <= 0:
            return False
        g.receive("C", total)
        g.log(f"sells to the Foreign Market for {total}₩", "C")
        return True

    def deal_option(self):
        g = self.g
        best = None
        for d in g.deals:
            food, lux, cost = d
            tariff = (food + lux) * {"A": 2, "B": 1, "C": 0}[g.policies[6]]
            val = food * self.value("food") + lux * self.value("lux")
            room = (g.cap("C", "food") - g.storage["C"]["food"]) >= food and \
                   (g.cap("C", "lux") - g.storage["C"]["lux"]) >= lux
            if room and cost + tariff <= self.spendable() and val > cost + tariff:
                sc = (val - cost - tariff) / 10
                if best is None or sc > best[0]:
                    best = (sc, d, tariff)
        return best

    def do_deal(self):
        g = self.g
        b = self.deal_option()
        if not b:
            return False
        _, d, tariff = b
        g.pay("C", d[2], why="Business Deal")
        g.pay("C", tariff, to="S", why="tariff")
        g.storage["C"]["food"] += d[0]
        g.storage["C"]["lux"] += d[1]
        g.deals.remove(d)
        g.log(f"Business Deal: {d[0]} Food + {d[1]} Luxury for {d[2]}₩ + {tariff}₩ tariff", "C")
        return True

    def basic_options(self):
        g = self.g
        o = []
        b = self.build_options()
        if b and b[0][0] > 0:
            o.append((b[0][0] + 2, self.do_build, f"Build Company ({b[0][1]['name']})"))
        total, n, _ = self.export_plan()
        if n:
            o.append((total / 12, self.do_export, "Sell to Foreign Market"))
        d = self.deal_option()
        if d:
            o.append((d[0] + 1, self.do_deal, "Make Business Deal"))
        bs = self.bill_score()
        if bs:
            o.append((bs + 0.5, self.do_bill, "Propose Bill"))
        if g.capital >= 80 and g.bills and g.influence["C"] < 3:
            o.append((2.2, self.do_lobby, "Lobby"))
        o.append((1.5, lambda: g.add_cubes("C", 3) and g.log("adds 3 cubes (Political Pressure)", "C"),
                  "Apply Political Pressure"))
        return o

    def do_lobby(self):
        g = self.g
        g.pay("C", 30, why="Lobby", from_capital=True)
        g.influence["C"] += 3
        g.log("Lobby: 30₩ from Capital → 3 Influence", "C")
        return True

    def free_choice(self, before):
        g = self.g
        if self.receive_benefits():
            return True
        if before:
            return False
        if self.lower_wages():
            return True
        if set_prices(g, "C"):
            return True
        for res in ("lux", "edu", "health"):
            if res not in g.extra_storage["C"] and g.storage["C"][res] >= g.cap("C", res) - 1 and \
                    self.spendable() > 40:
                g.extra_storage["C"].add(res)
                g.pay("C", 20, why="storage")
                g.log(f"buys a {res} Storage (20₩)", "C")
                return True
        return self.pay_loan_if_rich()

    def lower_wages(self):
        g = self.g
        mw = g.min_wage()
        changed = False
        for co in g.co_of("C"):
            ws = [g.workers[i] for i in co.workers if i]
            if co.level > mw and not any(w.committed for w in ws) and not co.strike:
                co.level = mw
                changed = True
        if changed:
            g.log(f"lowers wages to L{mw}", "C")
        return changed

    def after_labor_change(self):
        self.lower_wages()

    def set_prices(self):
        return set_prices(self.g, "C")

    def on_strike(self, co):
        g = self.g
        res = D.PRODUCT[co.ind]
        gain = co.production() * self.value(res)
        if gain > co.wages[2] and co.owner == "C":
            co.level = 3
            for i in co.workers:
                if i:
                    g.workers[i].committed = True
            co.strike = False
            g.log(f"raises {co.name} to L3 to end the Strike", "C")

    def refresh_market(self):
        g = self.g
        if g.cc_market and len(g.cc_deck) > 4:
            worst = min(g.cc_market, key=self.company_value)
            if self.company_value(worst) < 0:
                g.cc_market.remove(worst)
        while len(g.cc_market) < 4 and g.cc_deck:
            g.cc_market.append(g.cc_deck.pop())


# ============================================================================ State
class StateBot(Bot):
    def reserve(self):
        g = self.g
        return sum(c.wage() for c in g.public() if c.operational()) + 10

    def spendable(self):
        return max(0, self.g.treasury - self.reserve())

    def basic_options(self):
        g = self.g
        o = []
        ev = g.cards.best_event(self)
        if ev:
            o.append((ev[0], lambda e=ev: g.cards.resolve_event(self, e[1], e[2]), f"Event Action ({ev[1]['name']})"))
        low = min(g.legit, key=g.legit.get)
        if g.influence["S"] >= 3:
            o.append((2.5, lambda c=low: self.meet_mps(c), "Meet with a Party's MPs"))
        if g.treasury < 40 and min(g.legit.values()) > 1:
            o.append((3.5, self.extra_tax, "Extra Tax"))
        if g.media >= 2:
            o.append((1.5 + min(3, g.media) / 2, self.campaign, "Campaign"))
        bs = self.bill_score()
        if bs:
            o.append((bs + (1 if g.influence["S"] >= 2 else -1), self.do_bill, "Propose Bill"))
        o.append((0.5, self.campaign, "Campaign"))
        return o

    def meet_mps(self, cls):
        g = self.g
        g.influence["S"] -= 2
        g.influence[cls] += 2
        g.legit_change(cls, 1, "Meet with MPs")
        return True

    def extra_tax(self):
        g = self.g
        for c in "WMC":
            if c in g.roles:
                g.pay(c, 10, to="S", why="Extra Tax")
        for c in sorted(g.legit, key=g.legit.get)[:2]:
            g.legit_change(c, -1, "Extra Tax")
        g.log("Extra Tax: 10₩ from each class", "S")
        return True

    def campaign(self):
        g = self.g
        n = min(3, g.media)
        g.media -= n
        g.influence["S"] += n
        g.log(f"Campaign: {n} Media → Personal Influence", "S")
        return True

    def free_choice(self, before):
        g = self.g
        if not before and g.state_loans and g.treasury > 90:
            g.treasury -= 50
            g.state_loans -= 1
            g.log("pays off a Loan (50₩)", "S")
            return True
        return False

    def after_labor_change(self):
        g = self.g
        for co in g.public():
            if not any(i and g.workers[i].committed for i in co.workers):
                co.level = g.min_wage()


def make_bot(cls, game):
    return {"W": WorkingBot, "M": MiddleBot, "C": CapitalistBot, "S": StateBot}[cls](cls, game)
