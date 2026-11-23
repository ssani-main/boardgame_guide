"""Hegemony rules engine (base game, rulebook v1.2). Bots live in bots.py, card effects in cards.py.

The engine owns the state and every rule: setup, the five phases, buying, production, taxes,
elections, the IMF, scoring and the end game. Bots only choose between legal options.
"""
import math
import random
from collections import Counter

import data as D

CLS_NAME = {"W": "Working", "M": "Middle", "C": "Capitalist", "S": "State"}
ROLES_BY_COUNT = {2: "WC", 3: "WMC", 4: "WMCS"}
RES = ("food", "lux", "health", "edu", "infl")


class Worker:
    __slots__ = ("id", "cls", "skill", "loc", "committed")

    def __init__(self, wid, cls, skill):
        self.id, self.cls, self.skill, self.loc, self.committed = wid, cls, skill, None, False


class Company:
    """Capitalist, public, Middle Class or co-op company.

    slots: required skills (None = unskilled) for the main workers. Middle Class companies also have
    an optional Working Class employee slot (emp=True) with its own wage and production bonus.
    """

    def __init__(self, cid, spec, owner):
        self.id, self.owner = cid, owner
        self.name, self.ind, self.cost = spec["name"], spec["ind"], spec["cost"]
        self.slots = list(spec.get("slots", spec.get("mc", [])))
        self.out = spec["out"]
        self.wages = spec.get("wages", (0, 0, 0))
        self.mach_bonus = spec.get("mach", 0)
        self.auto = spec.get("auto", False)
        self.emp = spec.get("emp", False)
        self.bonus = spec.get("bonus", 0)
        self.emp_wages = spec.get("emp_wages", (0, 0, 0))
        self.emp_skill = None
        self.workers = [None] * len(self.slots)
        self.emp_worker = None
        self.level = 2
        self.machinery = False
        self.strike = False
        self.face_up = True
        self.coop = False
        self.spec = spec

    def operational(self):
        return self.auto or (bool(self.slots) and all(w is not None for w in self.workers))

    def fully_operational(self):            # Middle Class scoring: 2 workers inside
        return self.operational() and (not self.emp or self.emp_worker is not None)

    def wage(self):
        return self.wages[self.level - 1]

    def emp_wage(self):
        return self.emp_wages[self.level - 1]

    def production(self):
        n = self.out + (self.mach_bonus if self.machinery else 0)
        if self.emp and self.emp_worker is not None:
            n += self.bonus
        return n

    def __repr__(self):
        return f"{self.name}"


class Game:
    def __init__(self, players=4, seed=1, verbose=True, bot_overrides=None):
        assert players in (2, 3, 4)
        self.n = players
        self.roles = ROLES_BY_COUNT[players]
        self.rng = random.Random(seed)
        self.seed = seed
        self.verbose = verbose
        self.lines = []
        self.vp_rounds = []          # VP after each round's Scoring
        self.round_marks = []        # log length at the end of each round
        self.round = 1
        self.phase = "Setup"
        self.workers = {}
        self.companies = {}
        self._wid = 0
        self._cid = 0
        self.vp = {c: 0 for c in self.roles}
        self.vp_log = {c: Counter() for c in self.roles}     # where VP came from
        self.loans = Counter()
        self.state_loans = 0                                 # 2-3p automated State
        self.bills = {}                                      # policy -> (owner, target section)
        self.bill_markers = {c: 3 for c in self.roles}
        self.blocked = set()
        self.cards_played = Counter()
        self.stats = Counter()
        import bots
        import cards
        self.bots = {c: bots.make_bot(c, self) for c in self.roles}
        if bot_overrides:
            self.bots.update(bot_overrides)
        self.cards = cards
        self.setup()

    # ------------------------------------------------------------------ logging
    def log(self, msg, who=None):
        tag = f"R{self.round} {self.phase:<11}"
        line = f"{tag} | {CLS_NAME[who] + ': ' if who else ''}{msg}"
        self.lines.append(line)
        if self.verbose:
            print(line)

    def gain_vp(self, cls, n, why):
        if cls not in self.vp or n == 0:
            return
        self.vp[cls] += n
        self.vp_log[cls][why] += n
        self.log(f"{'+' if n > 0 else ''}{n} VP ({why}) → {self.vp[cls]}", cls)

    # ------------------------------------------------------------------ setup (rulebook v1.1/1.2 p.8-10)
    def new_worker(self, cls, skill=None):
        self._wid += 1
        w = Worker(self._wid, cls, skill)
        self.workers[w.id] = w
        return w

    def new_company(self, spec, owner):
        self._cid += 1
        c = Company(self._cid, spec, owner)
        self.companies[c.id] = c
        return c

    def setup(self):
        rng = self.rng
        self.policies = dict(D.START_POLICIES)
        self.treasury = 120
        self.media = 3 if self.n == 2 else 4
        self.services = {"health": 5 if self.n == 2 else 6, "edu": 5 if self.n == 2 else 6}
        self.state_goods = Counter()
        self.bag = Counter({"W": 8, "M": 8, "C": 8})
        self.cube_supply = {"W": 25 - 8, "M": 25 - 8, "C": 25 - 8}
        self.machinery_supply = 6
        # companies
        for spec in D.CC_START:
            self.new_company(spec, "C")
        rows = D.PUBLIC_2 if self.n == 2 else D.PUBLIC_34
        self.public_rows = []
        for r, row in enumerate(rows):
            ids = []
            for spec in row:
                c = self.new_company(spec, "S")
                c.face_up = (r == 0)
                ids.append(c.id)
            self.public_rows.append(ids)
        if "M" in self.roles:
            for spec in D.MC_START:
                self.new_company(spec, "M")
        self.cc_deck = [dict(s) for s in D.CC_DECK]
        self.mc_deck = [dict(s) for s in D.MC_DECK]
        rng.shuffle(self.cc_deck)
        rng.shuffle(self.mc_deck)
        self.cc_market = [self.cc_deck.pop() for _ in range(4)]
        self.mc_market = [self.mc_deck.pop() for _ in range(3)] if "M" in self.roles else []
        self.deal_deck = list(D.DEAL_DECK)
        rng.shuffle(self.deal_deck)
        self.deals = [self.deal_deck.pop()]
        self.export_deck = [dict(e) for e in D.EXPORT_DECK]
        rng.shuffle(self.export_deck)
        self.export = self.export_deck.pop()
        self.immigration = list(D.IMMIGRATION_DECK)
        rng.shuffle(self.immigration)
        # money / resources
        self.money = {"W": 30, "M": 40}
        self.revenue, self.capital = 120, 0
        self.influence = Counter({c: 1 for c in self.roles})
        self.storage = {"C": Counter(food=1, lux=2, edu=2, infl=1), "M": Counter(food=1, health=1)}
        self.extra_storage = {"C": set(), "M": set()}
        self.ftz = Counter()
        self.gs = {"W": Counter(), "M": Counter()}
        self.prices = {"C": {"food": 12, "lux": 8, "health": 8, "edu": 8},
                       "M": {"food": 12, "lux": 8, "health": 8, "edu": 8}}
        self.prosperity = {"W": 0, "M": 0}
        self.wealth_marker = -1
        self.unions = {}
        self.coops = []
        self.demonstration = False
        self.legit = {"W": 2, "M": 2, "C": 2}
        self.legit_tokens = Counter()
        self.benefits = {"W": Counter(), "M": Counter(), "C": Counter()}
        self.events = []
        self.agenda = None
        self.event_deck, self.agenda_deck = self.cards.event_and_agenda_decks(rng)
        # decks and hands
        self.decks, self.hands, self.discards = {}, {}, {}
        for c in self.roles:
            self.decks[c] = self.cards.action_deck(c, rng)
            self.hands[c] = [self.decks[c].pop() for _ in range(7)]
            self.discards[c] = []
        # workers on starting companies
        by = {c.name: c for c in self.companies.values() if c.face_up}
        if self.n == 2:
            place = [("Supermarket", "W"), ("Shopping Mall", "W"), ("Public Hospital", "W"), ("Public University", "W")]
        else:
            place = [("Supermarket", "W"), ("College", "W"), ("University Hospital", "W"),
                     ("Technical University", "M"), ("Shopping Mall", "M"),
                     ("Convenience Store", "M"), ("Doctor's Office", "M")]
        for name, cls in place:
            co = by[name]
            for i, skill in enumerate(co.slots):
                w = self.new_worker(cls, skill)
                self.put(w, co, i)
        self.new_worker("W")
        for _ in range(1 if self.n == 2 else 2):
            self.immigrate("W")
        if "M" in self.roles:
            self.new_worker("M", self.bots["M"].pick_skill())
            for _ in range(2):
                self.immigrate("M")
        if "S" in self.roles:
            self.events = [self.draw_event(first_round=True) for _ in range(2)]
            self.agenda = self.agenda_deck.pop()
        self.log(f"Setup for {self.n} players: {', '.join(CLS_NAME[c] for c in self.roles)}. "
                 f"Policies {self.policy_str()}, Treasury 120₩, Tax Multiplier {self.tax_mult()}.")

    # ------------------------------------------------------------------ helpers
    def policy_str(self):
        return " ".join(f"{p}{self.policies[p]}" for p in range(1, 8))

    def tax_mult(self):
        return D.tax_multiplier(self.policies[3], self.policies[4], self.policies[5])

    def min_wage(self):
        return D.MIN_WAGE[self.policies[2]]

    def class_workers(self, cls):
        return [w for w in self.workers.values() if w.cls == cls]

    def pop(self, cls):
        return D.population(len(self.class_workers(cls)))

    def unemployed(self, cls):
        return [w for w in self.class_workers(cls) if w.loc is None]

    def co_of(self, owner):
        return [c for c in self.companies.values() if c.owner == owner and c.face_up and not c.coop]

    def public(self):
        return [c for c in self.companies.values() if c.owner == "S" and c.face_up]

    def immigrate(self, cls):
        card = self.immigration.pop(0)
        self.immigration.append(card)
        skill = card[0] if cls == "W" else card[1]
        return self.new_worker(cls, skill)

    def put(self, w, co, slot, committed=False):
        """Place worker w into company slot (slot == 'emp' for the Middle Class employee slot)."""
        if slot == "emp":
            co.emp_worker = w.id
        else:
            co.workers[slot] = w.id
        w.loc = ("co", co.id, slot)
        w.committed = committed

    def unplace(self, w):
        if w.loc is None:
            return
        kind = w.loc[0]
        if kind == "co":
            co = self.companies[w.loc[1]]
            if w.loc[2] == "emp":
                co.emp_worker = None
            else:
                co.workers[w.loc[2]] = None
        elif kind == "union":
            del self.unions[w.loc[1]]
        w.loc = None
        w.committed = False

    def clear_company(self, co, reason=""):
        """Send everyone in co to Unemployed (company left partly staffed or closed)."""
        ids = [i for i in co.workers if i is not None] + ([co.emp_worker] if co.emp_worker else [])
        for i in ids:
            self.unplace(self.workers[i])
        if ids and reason:
            self.log(f"{len(ids)} worker(s) leave {co.name} ({reason})")
        if co.strike and not co.operational():
            co.strike = False                                  # v1.2: token removed
        self.check_unions()

    def check_unions(self):
        for ind, wid in list(self.unions.items()):
            if self.industry_count("W", ind, exclude=wid) < 4:
                self.unplace(self.workers[wid])
                self.log(f"{ind} Trade Union dissolves (fewer than 4 workers)", "W")

    def industry_count(self, cls, ind, exclude=None):
        n = 0
        for w in self.class_workers(cls):
            if w.id == exclude or w.loc is None or w.loc[0] == "union":
                continue
            if w.loc[0] == "coop" and ind == "food":
                n += 1
            elif w.loc[0] == "co" and self.companies[w.loc[1]].ind == ind:
                n += 1
        return n

    # ------------------------------------------------------------------ money
    def cash(self, cls):
        if cls == "C":
            return self.revenue + self.capital
        if cls == "S":
            return self.treasury
        return self.money[cls]

    def receive(self, cls, amount, why=""):
        if amount <= 0:
            return
        if cls == "C":
            self.revenue += amount
        elif cls == "S":
            self.treasury += amount
        else:
            self.money[cls] += amount

    def pay(self, cls, amount, to=None, why="", from_capital=False, forced=True):
        """Pay amount; take forced Loans (+50₩) if short. Returns True if paid."""
        if amount <= 0:
            return True
        if not forced and self.cash(cls) < amount:
            return False
        while self.cash(cls) < amount:
            self.take_loan(cls, why)
        if cls == "C":
            first, second = ("capital", "revenue") if from_capital else ("revenue", "capital")
            a = min(getattr(self, first), amount)
            setattr(self, first, getattr(self, first) - a)
            setattr(self, second, getattr(self, second) - (amount - a))
        elif cls == "S":
            self.treasury -= amount
        else:
            self.money[cls] -= amount
        if to:
            self.receive(to, amount)
        return True

    def take_loan(self, cls, why):
        if cls == "S":
            self.state_loans += 1
            self.treasury += 50
            self.log(f"State takes a Loan ({why}) → {self.state_loans} Loan(s)", None)
            self.stats["state_loans"] += 1
            return
        self.loans[cls] += 1
        if cls == "C":
            self.capital += 50
        else:
            self.money[cls] += 50
        self.log(f"forced Loan +50₩ ({why})", cls)
        self.stats[f"loans_{cls}"] += 1

    # ------------------------------------------------------------------ prices and buying
    def import_price(self, res):
        return D.IMPORT_BASE[res], D.TARIFF[self.policies[6]][res]

    def state_price(self, res):
        if res == "health":
            return D.WELFARE_PRICE[self.policies[4]]
        if res == "edu":
            return D.WELFARE_PRICE[self.policies[5]]
        if res == "infl":
            return D.STATE_INFL_PRICE
        return {"food": 12, "lux": 8}[res]                       # EST: State's printed goods prices

    def stock(self, src, res):
        if src == "C":
            return self.storage["C"][res] if res != "infl" else 0
        if src == "M":
            return self.storage["M"][res] if res != "infl" else 0
        if src == "S":
            if res in ("health", "edu"):
                return self.services[res]
            if res == "infl":
                return self.media
            return self.state_goods[res]
        if src == "F":
            return 99 if res in ("food", "lux") else 0
        return 0

    def unit_price(self, buyer, src, res):
        if src == buyer:
            return 0
        if src in ("C", "M"):
            return self.prices[src][res]
        if src == "S":
            return self.state_price(res)
        base, tariff = self.import_price(res)
        return base + tariff

    def sources(self, buyer, res):
        out = []
        for src in ("C", "M", "S", "F"):
            if src in ("C", "M") and src not in self.roles:
                continue
            if src == buyer and buyer != "M":
                continue
            if self.stock(src, res) > 0:
                out.append(src)
        return out

    def buy(self, buyer, res, src, qty, half_price=False, to_gs=True, state_pays_half=False):
        """Buy qty of res from src for buyer. Returns units bought. Handles State bonuses and tariffs."""
        qty = min(qty, self.stock(src, res))
        if qty <= 0:
            return 0
        unit = self.unit_price(buyer, src, res)
        if src == "F":
            base, tariff = self.import_price(res)
            unit = base
        total = unit * qty
        pay_now = math.ceil(total / 2) if half_price else total
        if pay_now > self.cash(buyer):
            return 0
        # take goods
        if src in ("C", "M"):
            self.storage[src][res] -= qty
        elif src == "S":
            if res in ("health", "edu"):
                self.services[res] -= qty
            elif res == "infl":
                self.media -= qty
            else:
                self.state_goods[res] -= qty
        receiver = None if src == "F" else (None if src == buyer else src)
        self.pay(buyer, pay_now, to=receiver, why=f"buy {res}", forced=False)
        if state_pays_half and receiver and total - pay_now > 0:
            self.pay("S", total - pay_now, to=receiver, why="half-price card")
        if src == "F":
            tariff = self.import_price(res)[1] * qty
            if tariff:
                self.pay(buyer, tariff, to="S", why="tariff", forced=False)
        if to_gs:
            self.gs[buyer][res] += qty
        # State bonuses for cheap welfare (4 players)
        if src == "S" and "S" in self.roles and res in ("health", "edu"):
            sect = self.policies[4 if res == "health" else 5]
            if sect == "B":
                self.gain_vp("S", 1, "welfare sold at 5₩")
            elif sect == "A":
                self.legit_change(buyer, qty // 3, "free welfare")
        what = f"{qty} {res} from {CLS_NAME.get(src, 'Foreign Market')}"
        self.log(f"buys {what} for {pay_now + (self.import_price(res)[1] * qty if src == 'F' else 0)}₩", buyer)
        return qty

    def buy_best(self, buyer, res, max_sources=2, cap=None, only=None, half_price=False, budget=None,
                 state_pays_half=False):
        """Buy Goods & Services action: one resource, up to 2 sources, up to Population from each."""
        per = cap if cap is not None else self.pop(buyer)
        srcs = [s for s in self.sources(buyer, res) if only is None or s in only]
        srcs.sort(key=lambda s: self.unit_price(buyer, s, res))
        got, used = 0, 0
        budget = self.cash(buyer) if budget is None else budget
        for s in srcs:
            if used >= max_sources:
                break
            price = self.unit_price(buyer, s, res)
            afford = per if price == 0 else min(per, budget // max(1, math.ceil(price / (2 if half_price else 1))))
            n = min(afford, self.stock(s, res))
            if n <= 0:
                continue
            b = self.buy(buyer, res, s, n, half_price=half_price, state_pays_half=state_pays_half)
            if b:
                got += b
                used += 1
                budget -= b * price
        return got

    # ------------------------------------------------------------------ prosperity
    def gain_prosperity(self, cls, why):
        track = D.WC_PROSPERITY if cls == "W" else D.MC_PROSPERITY
        self.prosperity[cls] = min(len(track) - 1, self.prosperity[cls] + 1)
        self.gain_vp(cls, track[self.prosperity[cls]], f"Prosperity ({why})")

    def use_resource(self, cls, res):
        """Free action Use Healthcare / Education / Luxury."""
        p = self.pop(cls)
        if self.gs[cls][res] < p:
            return False
        self.gs[cls][res] -= p
        self.gain_prosperity(cls, {"health": "Healthcare", "edu": "Education", "lux": "Luxury"}[res])
        if res == "health":
            self.gain_vp(cls, 2, "Healthcare bonus")
            self.new_worker(cls)
            self.log("+1 unskilled worker from Healthcare", cls)
        elif res == "edu":
            self.bots[cls].upgrade_worker()
        self.stats[f"use_{res}_{cls}"] += 1
        return True

    # ------------------------------------------------------------------ legitimacy
    def legit_change(self, cls, n, why):
        if "S" not in self.roles or cls not in self.legit or n == 0:
            return
        self.legit[cls] = max(1, min(10, self.legit[cls] + n))
        self.log(f"Legitimacy {CLS_NAME[cls]} {n:+d} ({why}) → {self.legit[cls]}", "S")

    def legit_token(self, cls, why):
        if "S" not in self.roles:
            return
        self.legit_tokens[cls] += 1
        self.legit_change(cls, 1, why + ", token")

    # ------------------------------------------------------------------ voting
    def add_cubes(self, cls, n):
        n = min(n, self.cube_supply.get(cls, 0))
        if n > 0:
            self.cube_supply[cls] -= n
            self.bag[cls] += n
        return n

    def refill_bag(self, state_influence=True):
        self.add_cubes("W", math.ceil(self.pop("W") / 2))
        ops = sum(1 for c in self.co_of("C") if c.operational())
        self.add_cubes("C", math.ceil(ops / 2))
        if "M" in self.roles:
            mops = sum(1 for c in self.co_of("M") if c.operational())
            self.add_cubes("M", max(math.ceil(self.pop("M") / 2), math.ceil(mops / 2)))
        else:
            self.add_cubes("M", 5)
        if "S" in self.roles and state_influence:
            g = D.legit_influence(min(self.legit.values()))
            self.influence["S"] += g
            self.log(f"gains {g} Influence from lowest Legitimacy", "S")

    def draw_cubes(self, k=5):
        drawn = []
        for _ in range(k):
            if sum(self.bag.values()) == 0:
                self.refill_bag(False)
                self.refill_bag(False)
            pool = [c for c, n in self.bag.items() for _ in range(n)]
            if not pool:
                break
            c = self.rng.choice(pool)
            self.bag[c] -= 1
            drawn.append(c)
        return drawn

    def propose(self, cls, policy, target, immediate=False, free_immediate=False, preview=None):
        if policy in self.bills or policy in self.blocked:
            return False
        self.bills[policy] = (cls, target)
        self.bill_markers[cls] -= 1
        self.log(f"proposes Bill {policy}{self.policies[policy]} → {policy}{target}", cls)
        self.stats["bills"] += 1
        if immediate and (free_immediate or self.influence[cls] >= 1):
            if not free_immediate:
                self.influence[cls] -= 1
            self.log("calls an Immediate Vote", cls)
            self.election(policy, preview=preview)
        return True

    def election(self, policy, preview=None):
        owner, target = self.bills[policy]
        current = self.policies[policy]
        side = {}
        for c in self.roles:
            if c == "S" and self.influence["S"] == 0 and owner != "S":
                continue
            side[c] = True if c == owner else self.bots[c].vote(policy, current, target)
        drawn = preview if preview is not None else self.draw_cubes(5)
        votes = {True: 0, False: 0}
        contributed = Counter()
        for cube in drawn:
            if cube == "M" and "M" not in self.roles:
                continue                                       # 2p: neutral, discarded
            if cube in side:
                votes[side[cube]] += 1
                contributed[cube] += 1
        tally = dict(votes)
        spent = {}
        for c in side:
            k = self.bots[c].spend_influence(policy, side[c], dict(tally), owner)
            k = min(k, self.influence[c])
            spent[c] = k
        for c, k in spent.items():
            self.influence[c] -= k
            votes[side[c]] += k
            if k:
                contributed[c] += k
        passed = votes[True] >= votes[False]
        winners = [cube for cube in drawn if side.get(cube) == passed]
        losers = [cube for cube in drawn if cube in side and side.get(cube) != passed]
        for cube in drawn:
            if cube in losers:
                self.bag[cube] += 1
            elif cube in self.cube_supply:
                self.cube_supply[cube] += 1                   # winning (and neutral) cubes leave the bag
        desc = " ".join(f"{CLS_NAME[c][0]}:{'for' if s else 'against'}" for c, s in side.items())
        inf = ", ".join(f"{CLS_NAME[c]} {k}" for c, k in spent.items() if k)
        self.log(f"Vote {policy}{current}→{policy}{target} [{desc}] cubes {''.join(drawn)}"
                 f"{' + Influence ' + inf if inf else ''}: {votes[True]}–{votes[False]} "
                 f"{'PASSED' if passed else 'failed'}")
        self.stats["votes"] += 1
        del self.bills[policy]
        self.bill_markers[owner] += 1
        if passed:
            self.stats["passed"] += 1
            self.gain_vp(owner, 3, "own Bill passed")
            for c in side:
                if c != owner and side[c] and contributed[c]:
                    self.gain_vp(c, 1, "supported a Bill")
            self.set_policy(policy, target)
        return passed

    def set_policy(self, policy, target, imf=False):
        old = self.policies[policy]
        if old == target:
            return
        self.policies[policy] = target
        if not imf:
            self.log(f"Policy {policy} is now {target}")
        if policy == 1:
            self.resize_public()
        elif policy == 2:
            mw = self.min_wage()
            for c in self.companies.values():
                if c.level < mw:
                    c.level = mw
            if "S" not in self.roles:
                for c in self.companies.values():
                    if c.owner == "S":
                        c.level = mw
            for c in self.roles:
                self.bots[c].after_labor_change()
        elif policy == 6:
            for c in ("C", "M"):
                if c in self.roles:
                    self.bots[c].set_prices()

    def resize_public(self):
        want = D.PUBLIC_OPEN[self.policies[1]]
        have = [c for c in self.public()]
        if len(have) < want:
            hidden = [self.companies[i] for row in self.public_rows for i in row if not self.companies[i].face_up]
            for co in hidden[: want - len(have)]:
                co.face_up = True
                self.pay("S", co.cost, why="open public company")
                co.level = self.min_wage()
                self.log(f"Public Sector grows: {co.name} opens (−{co.cost}₩)", "S")
                self.auto_staff_public(co)
        elif len(have) > want:
            ranked = sorted(have, key=lambda c: (c.operational(), -c.id))
            if "S" not in self.roles:                           # 2-3p: whole bottom row
                ranked = sorted(have, key=lambda c: -c.id)
            for co in ranked[: len(have) - want]:
                self.clear_company(co, "public company closed")
                co.face_up = False
                self.receive("S", co.cost)
                self.log(f"Public Sector shrinks: {co.name} closes (+{co.cost}₩)", "S")

    def auto_staff_public(self, co):
        for cls in ("M", "W") if "M" in self.roles else ("W",):
            team = self.bots[cls].pick_team(co, self.unemployed(cls))
            if team:
                for slot, w in team:
                    self.put(w, co, slot, committed=True)
                self.log(f"{len(team)} unemployed worker(s) auto-assigned to {co.name}", cls)
                return

    # ------------------------------------------------------------------ events helpers (State)
    def draw_event(self, first_round=False):
        while True:
            e = self.event_deck.pop()
            if first_round and e.get("rounds_2_5"):
                self.event_deck.insert(0, e)
                continue
            return e

    # ------------------------------------------------------------------ phases
    def play(self):
        for r in range(1, 6):
            self.round = r
            if r > 1:
                self.preparation()
            self.action_phase()
            self.production()
            self.elections()
            self.scoring()
            self.vp_rounds.append(dict(self.vp))
            self.round_marks.append(len(self.lines))
        return self.game_end()

    def preparation(self):
        self.phase = "Preparation"
        self.log(f"--- Round {self.round} begins ---")
        for c in self.roles:
            if self.loans[c]:
                self.pay(c, 5 * self.loans[c], why="Loan interest", from_capital=(c == "C"))
                self.log(f"pays {5 * self.loans[c]}₩ Loan interest", c)
        if self.state_loans:
            self.pay("S", 5 * self.state_loans, why="Loan interest")
            self.log(f"pays {5 * self.state_loans}₩ Loan interest", "S")
            if "S" not in self.roles and self.treasury > 50:
                self.treasury -= 50
                self.state_loans -= 1
                self.log("automated State pays off a Loan")
        # Capitalist first (before the other classes receive workers)
        self.draw_up("C")
        self.bots["C"].refresh_market()
        self.deals = [self.deal_deck.pop() for _ in range(D.DEALS_DRAWN[self.policies[6]]) if self.deal_deck]
        self.export = self.export_deck.pop() if self.export_deck else self.export
        for c in ("W", "M"):
            if c not in self.roles:
                continue
            self.prosperity[c] = max(0, self.prosperity[c] - (1 if c == "W" else 2))
            self.draw_up(c)
            if c == "M":
                self.bots["M"].refresh_market()
                self.new_worker("M")
                self.new_worker("M", self.bots["M"].pick_skill())
            else:
                self.new_worker("W")
                self.new_worker("W")
            for _ in range(D.IMMIGRANTS[self.policies[7]]):
                self.immigrate(c)
            self.log(f"Prosperity drops to {self.prosperity[c]}; workers now {len(self.class_workers(c))} "
                     f"(Population {self.pop(c)})", c)
        if "S" in self.roles:
            self.events = [self.draw_event() for _ in range(2)]
            self.agenda = self.agenda_deck.pop() if self.agenda_deck else self.agenda
            self.draw_up("S")
            self.log(f"Events: {', '.join(e['name'] for e in self.events)}. Agenda: {self.agenda['name']}", "S")
        self.blocked = set()

    def draw_up(self, c):
        while len(self.hands[c]) < 7:
            if not self.decks[c]:
                self.decks[c] = self.discards[c]
                self.discards[c] = []
                self.rng.shuffle(self.decks[c])
                if not self.decks[c]:
                    break
            self.hands[c].append(self.decks[c].pop())

    def action_phase(self):
        self.phase = "Action"
        for turn in range(1, 6):
            for c in self.roles:
                self.turn = turn
                self.action_stamp = (self.round, turn, c)
                self.bots[c].take_turn()

    def production(self):
        self.phase = "Production"
        order = [c for c in "SCMW" if c in self.roles or c == "S"]
        # strikes resolve first (v1.2)
        for co in self.companies.values():
            if co.strike and (co.level == 3 or not co.operational()):
                co.strike = False
        # 1. produce goods & services, owner by owner in reverse order
        if "S" not in self.roles:
            order = ["S"] + [c for c in "CMW" if c in self.roles]
        for owner in order:
            if owner == "W":
                self.produce_working()
                continue
            for co in sorted(self.companies.values(), key=lambda c: c.id):
                if co.owner != owner or not co.face_up or co.coop or not co.operational():
                    continue
                if co.strike and co.level < 3:
                    if owner == "M":                              # only the employee's part stops
                        self.produce(co, employee=False)
                    else:
                        self.log(f"{co.name} is on strike: no production, no wage")
                    w_owner = "W"
                    self.influence["W"] += 1
                    self.log("+1 Influence from a Strike", "W")
                    co.strike = False
                    continue
                self.produce(co)
        for w in self.workers.values():
            if w.loc and w.loc[0] != "union":
                w.committed = False
        if self.demonstration:
            self.resolve_demonstration()
        # 2. cover needs
        for c in ("M", "W"):
            if c in self.roles:
                self.cover_needs(c)
        # 3. check IMF
        self.check_imf()
        # 4. taxes
        self.pay_taxes()

    def produce(self, co, employee=True):
        owner = co.owner
        if not co.auto:
            payee = self.workers[co.workers[0]].cls if co.workers else None
            if owner == "M":
                if co.emp and co.emp_worker and employee:
                    self.pay("M", co.emp_wage(), to="W", why="wages")
            else:
                self.pay(owner, co.wage(), to=payee, why=f"wages {co.name}")
        amount = co.out + (co.mach_bonus if co.machinery else 0)
        if owner == "M" and employee and co.emp and co.emp_worker:
            amount += co.bonus
        res = D.PRODUCT[co.ind]
        stored = self.store(owner, res, amount)
        self.stats[f"produced_{owner}"] += stored
        if owner == "M":
            wage = f", pays {co.emp_wage()}₩ to its employee" if (co.emp and co.emp_worker and employee) else ""
        else:
            wage = "" if co.auto else f", pays {co.wage()}₩ wage (L{co.level})"
        self.log(f"{co.name}{wage}, produces {amount} {res}" + (f" ({stored} stored)" if stored < amount else ""), owner)

    def store(self, owner, res, amount):
        if owner == "S":
            if res in ("health", "edu", "infl"):
                cap = self.service_cap(res)
                cur = self.media if res == "infl" else self.services[res]
                add = max(0, min(amount, cap - cur))
                if res == "infl":
                    self.media += add
                else:
                    self.services[res] += add
                return add
            self.state_goods[res] += amount
            return amount
        if res == "infl":
            if owner == "M":
                self.gs["M"]["infl"] += amount
            self.influence[owner] += amount if owner == "C" else 0
            if owner == "M":
                self.influence["M"] += amount
            return amount
        cap = self.cap(owner, res)
        room = max(0, cap - self.storage[owner][res])
        add = min(room, amount)
        self.storage[owner][res] += add
        extra = amount - add
        if extra and owner == "C" and res in ("food", "lux"):
            ftz_room = (6 if res == "food" else 12) - self.ftz[res]   # EST: FTZ tile capacity
            f = max(0, min(extra, ftz_room))
            self.ftz[res] += f
            add += f
        return add

    def cap(self, owner, res):
        base = (8 if res == "food" else 12) if owner == "C" else 8
        return base * (2 if res in self.extra_storage.get(owner, ()) else 1)

    def service_cap(self, res):
        ind = {"health": "health", "edu": "edu", "infl": "media"}[res]
        return sum(c.out for c in self.public() if c.ind == ind) + 6

    def produce_working(self):
        for co in self.coops:
            if co.operational():
                self.gs["W"]["food"] += 2
                self.log("Cooperative Farm produces 2 Food", "W")
        if self.unions:
            self.influence["W"] += len(self.unions)
            self.log(f"+{len(self.unions)} Influence from Trade Unions", "W")

    def resolve_demonstration(self):
        self.demonstration = False
        self.influence["W"] += 1
        penalty = len(self.unemployed("W")) + len(self.unions)
        self.log(f"Demonstration! {penalty} VP penalty to share out", "W")
        room = {"C": 12 - len(self.co_of("C")), "M": 8 - len(self.co_of("M")),
                "S": sum(1 for row in self.public_rows for i in row if not self.companies[i].face_up)}
        for c in sorted([c for c in self.roles if c != "W"], key=lambda c: -self.vp[c]):
            take = min(penalty, room.get(c, 0))
            if take:
                self.gain_vp(c, -take, "Demonstration")
                penalty -= take

    def cancel_demonstration(self, hired_working):
        """Rule: discarded when someone builds a Company, assigns Working Class workers there,
        and the Demonstration condition is no longer met."""
        if self.demonstration and hired_working and not self.demo_condition():
            self.demonstration = False
            self.log("Demonstration ends: new jobs were created")

    def demo_condition(self):
        return len(self.unemployed("W")) - self.open_slots("W") >= 2

    def open_slots(self, cls):
        n = 0
        for co in self.companies.values():
            if not co.face_up or co.coop:
                continue
            if not co.operational() and not co.auto and co.owner != "M":
                n += len(co.slots)
            if cls == "W" and co.owner == "M" and co.emp and co.operational() and co.emp_worker is None:
                n += 1
        return n

    def cover_needs(self, c):
        need = self.pop(c)
        if c == "M":
            own = min(need, self.storage["M"]["food"])
            self.storage["M"]["food"] -= own
            need -= own
        g = min(need, self.gs[c]["food"])
        self.gs[c]["food"] -= g
        need -= g
        spent = 0
        while need > 0:
            srcs = [s for s in self.sources(c, "food") if s != c]
            srcs.sort(key=lambda s: self.unit_price(c, s, "food"))
            s = srcs[0]
            n = min(need, self.stock(s, "food"))
            unit = self.unit_price(c, s, "food")
            if self.cash(c) < unit * n:
                self.take_loan(c, "food")
                continue
            got = self.buy(c, "food", s, n, to_gs=False)
            spent += unit * got
            need -= got
        self.log(f"covers Food for Population {self.pop(c)}", c)

    def check_imf(self):
        loans = self.state_loans
        limit = D.IMF_LOANS[self.policies[1]]
        if loans < limit:
            return
        while self.state_loans and self.treasury >= 55:
            self.treasury -= 55
            self.state_loans -= 1
        if self.state_loans < limit:
            return
        self.imf()

    def imf(self):
        self.log("*** IMF INTERVENTION ***")
        self.stats["imf"] += 1
        self.imf_round = self.round
        for p, (owner, _) in list(self.bills.items()):
            self.influence[owner] += 1
            self.bill_markers[owner] += 1
        self.bills = {}
        self.old_labor = self.policies[2]
        for p, s in D.IMF_POLICIES.items():
            self.set_policy(p, s, imf=True)
        for c in self.companies.values():
            c.level = 1
        self.log(f"Policies forced to {self.policy_str()}; all wages to L1")
        while self.state_loans and self.treasury >= 55:
            self.treasury -= 55
            self.state_loans -= 1
        if self.state_loans:
            self.treasury = 0                                  # pays all it has, the rest is discarded
            self.log(f"{self.state_loans} State Loan(s) written off")
        self.state_loans = 0
        for c in self.legit:
            self.legit[c] = math.ceil(self.legit[c] / 2)

    def pay_taxes(self):
        labor = getattr(self, "old_labor", None) or self.policies[2]
        self.old_labor = None
        rate = D.INCOME_TAX[labor][self.policies[3]]
        mult = self.tax_mult()
        before = self.treasury
        if "C" in self.roles:
            ops = sum(1 for c in self.co_of("C") if c.operational())
            emp = ops * mult
            self.pay("C", emp, to="S", why="Employment tax")
            corp = D.corporate_tax(self.revenue, self.policies[3])
            self.pay("C", corp, to="S", why="Corporate tax")
            self.log(f"taxes: Employment {ops}×{mult}={emp}₩, Corporate {corp}₩", "C")
        if "M" in self.roles:
            others = {self.workers[w].loc[1] for w in [x.id for x in self.class_workers("M")]
                      if self.workers[w].loc and self.workers[w].loc[0] == "co"
                      and self.companies[self.workers[w].loc[1]].owner != "M"}
            inc = rate * len(others)
            mops = sum(1 for c in self.co_of("M") if c.operational())
            emp = mops * mult
            self.pay("M", inc + emp, to="S", why="taxes")
            self.log(f"taxes: Income {rate}×{len(others)}={inc}₩, Employment {mops}×{mult}={emp}₩", "M")
        inc = rate * self.pop("W")
        self.pay("W", inc, to="S", why="Income tax")
        self.log(f"Income tax {rate}×{self.pop('W')}={inc}₩", "W")
        self.log(f"State Treasury {before}₩ → {self.treasury}₩")

    def elections(self):
        self.phase = "Elections"
        if not self.bills:
            self.log("no Bills: Elections skipped")
            return
        self.refill_bag()
        for p in sorted(self.bills):
            if p in self.bills:
                self.election(p)

    def scoring(self):
        self.phase = "Scoring"
        if self.unions:
            self.gain_vp("W", 2 * len(self.unions), "Trade Unions")
        if "M" in self.roles:
            full = sum(1 for c in self.co_of("M") if c.fully_operational())
            if self.prosperity["M"] < full:
                self.gain_prosperity("M", "scoring bonus")
        if "C" in self.roles:
            self.capital += self.revenue
            self.revenue = 0
            space = D.wealth_space(self.capital)
            if space >= 0:
                self.gain_vp("C", space + 1, f"Wealth table, Capital {self.capital}₩")
            if space > self.wealth_marker:
                moved = space - self.wealth_marker
                self.wealth_marker = space
                self.gain_vp("C", 3 * moved, f"Wealth marker +{moved} space(s)")
        if "S" in self.roles:
            for e in self.events:
                pen = e["penalty"]
                if pen == "choose2":                   # "2 of your choice": the State picks its two highest
                    pen = {c: -1 for c in sorted(self.legit, key=lambda c: -self.legit[c])[:2]}
                for cls, n in pen.items():
                    self.legit_change(cls, n, f"ignored Event {e['name']}")
            self.events = []
            low2 = sorted(self.legit.values())[:2]
            self.gain_vp("S", sum(low2), f"Legitimacy {self.legit['W']}/{self.legit['M']}/{self.legit['C']}")
            for c in self.legit:
                self.legit[c] = math.ceil(self.legit[c] / 2) + self.legit_tokens[c]
                self.legit[c] = min(10, self.legit[c])
            match = sum(1 for p, s in self.agenda["targets"].items() if self.policies[p] == s)
            self.gain_vp("S", match, f"Political Agenda '{self.agenda['name']}'")

    def game_end(self):
        self.phase = "Game end"
        self.log("=== GAME END ===")
        for c in self.roles:
            if not self.loans[c]:
                continue
            if c == "C":
                self.gain_vp("C", -5 * self.loans[c], "unpaid Loans")
                continue
            for _ in range(self.loans[c]):
                pay = min(55, (self.cash(c) // 5) * 5)
                self.pay(c, pay, why="pay off Loan", forced=False)
                if pay < 55:
                    self.gain_vp(c, -((55 - pay) // 5), "unpaid Loan")
            self.loans[c] = 0
        if "S" in self.roles:
            for _ in range(self.state_loans):
                pay = min(55, (self.treasury // 5) * 5)
                self.treasury -= pay
                if pay < 55:
                    self.gain_vp("S", -((55 - pay) // 5), "unpaid Loan")
            self.state_loans = 0
        sec = {"W": "A", "M": "B", "C": "C"}
        for c in ("W", "M", "C"):
            if c not in self.roles:
                continue
            n = sum(1 for p in range(1, 6) if self.policies[p] == sec[c])
            table = D.POLICY_VP_MC if c == "M" else D.POLICY_VP_WC_CC
            self.gain_vp(c, table[n], f"{n} policies in {sec[c]}")
        self.gain_vp("W", min(15, self.money["W"] // 10), f"money {self.money['W']}₩")
        if "M" in self.roles:
            st = self.storage["M"]
            goods = st["food"] // 2 + st["lux"] // 3 + st["health"] // 3 + st["edu"] // 3
            self.gain_vp("M", goods, "goods in storage")
            self.gain_vp("M", self.money["M"] // 15, f"money {self.money['M']}₩")
        st = self.storage["C"] + self.ftz
        goods = st["food"] // 2 + st["lux"] // 3 + st["health"] // 3 + st["edu"] // 3
        self.gain_vp("C", goods, "goods in storage")
        if "S" in self.roles:
            g = self.state_goods
            goods = (g["food"] // 2 + g["lux"] // 3 + self.services["health"] // 3
                     + self.services["edu"] // 3 + self.media // 3)
            self.gain_vp("S", goods, "goods in storage")
            self.gain_vp("S", self.treasury // 30, f"Treasury {self.treasury}₩")
        return self.winner()

    def winner(self):
        best = max(self.vp.values())
        tied = [c for c in self.roles if self.vp[c] == best]
        reason = "most VP"
        if len(tied) > 1:
            sec = {"W": "A", "M": "B", "C": "C"}

            def pol(c):
                if c == "S":
                    return sum(1 for p, s in self.agenda["targets"].items() if p <= 5 and self.policies[p] == s)
                return sum(1 for p in range(1, 6) if self.policies[p] == sec[c])
            m = max(pol(c) for c in tied)
            tied = [c for c in tied if pol(c) == m]
            reason = "tie → most policies in own section"
            if len(tied) > 1 and "S" in tied:
                tied, reason = ["S"], "tie → the State wins ties"
            elif len(tied) > 1:
                m = max(self.bag[c] for c in tied)               # Voting cubes in the bag
                tied = [c for c in tied if self.bag[c] == m]
                reason = "tie → most Voting cubes"
                if len(tied) > 1:
                    reason = "tie → shared victory"
        self.result = {"vp": dict(self.vp), "winners": tied, "reason": reason}
        self.log(f"Final VP: {', '.join(f'{CLS_NAME[c]} {v}' for c, v in self.vp.items())}. "
                 f"Winner: {' & '.join(CLS_NAME[c] for c in tied)} ({reason})")
        return self.result
