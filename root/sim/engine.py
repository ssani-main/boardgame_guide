"""Root base-game rules engine (Law of Root, Oct 2025). Bots only choose; every rule lives here.

Section numbers in comments point to the Law. Shortcuts are marked `SKIP:` with what is left out.
"""
import random
from collections import Counter

import data as D

SUITS = ("fox", "rabbit", "mouse")


class GameOver(Exception):
    pass


class IllegalAction(Exception):
    pass


def matches(card_suit, suit):
    """Birds are wild (2.1.1): a bird card matches any clearing suit."""
    return card_suit == "bird" or card_suit == suit


class Game:
    def __init__(self, factions=None, players=4, seed=1, verbose=True, bots=None):
        import bots as B
        self.rng = random.Random(seed)
        self.seed = seed
        self.verbose = verbose
        self.lines = []
        self.stats = Counter()
        self.factions = list(factions or D.DEFAULT_FACTIONS[players])
        self.n = len(self.factions)
        self.bots = bots or {f: B.make(f, self) for f in self.factions}
        self.round = 0
        self.turn_of = None
        self.winners = None
        self.reason = None
        self.history = []                      # (round, {f: vp}) after each full round
        self.round_marks = []                  # index into lines at the end of each round
        self.vp_log = {}                       # f -> Counter(reason -> points)
        self._setup()

    # ------------------------------------------------------------------ logging
    def log(self, text, f=None):
        who = D.NAME[f] if f else "Game"
        line = f"R{self.round:02d} {who:<9}| {text}"
        self.lines.append(line)
        if self.verbose:
            print(line)

    # ------------------------------------------------------------------ setup (5.1)
    def _setup(self):
        r = self.rng
        self.order = self.factions[:]
        r.shuffle(self.order)                  # 5.1.1 random seating and first player
        self.vp = {f: 0 for f in self.factions}
        self.dominance = {f: None for f in self.factions}
        self.coalition = None                  # faction the Vagabond joined
        self.deck = D.build_deck()
        if self.n == 2:                        # 5.1.3 remove dominance in 2 players
            self.deck = [c for c in self.deck if c["kind"] != "dominance"]
        r.shuffle(self.deck)
        self.discard, self.avail_dom = [], []
        self.hands = {f: [] for f in self.factions}
        for f in self.factions:
            self.draw(f, D.START_HAND, quiet=True)
        self.cl = {c: dict(w=Counter(), b=[], wood=0, keep=False, sym=False) for c in D.CLEARINGS}
        for c in D.RUINS:                      # 5.1.4
            self.cl[c]["b"].append(("ruin", "ruin"))
        self.items = dict(D.ITEM_SUPPLY)       # 5.1.5
        self.supply = {"M": D.M_WARRIORS, "E": D.E_WARRIORS, "A": D.A_WARRIORS, "V": 0}
        self.crafted = {f: [] for f in self.factions}
        self.persist = {f: [] for f in self.factions}
        self.used_craft = {f: Counter() for f in self.factions}
        self.once = set()                      # once-per-turn effects used this turn
        self.play_area = {f: [] for f in self.factions}
        self.battle_removed = Counter()
        self.start_corner = {}
        self.vag = None
        self.keep = None
        self.log(f"Factions {', '.join(D.NAME[f] for f in self.factions)}; seating {' → '.join(D.NAME[f] for f in self.order)}")
        for f in D.FACTIONS:                   # 5.1.7 setup order A, B, C, D
            if f in self.factions:
                getattr(self, "_setup_" + f)()

    def _setup_M(self):
        bot = self.bots["M"]
        self.wood_supply = D.M_WOOD
        self.m_on_map = Counter()
        keep = bot.choose_keep(self, list(D.CORNERS))
        self.keep = keep
        self.cl[keep]["keep"] = True
        self.start_corner["M"] = keep
        for c in D.CLEARINGS:                  # 6.3.3 garrison
            if c != D.OPPOSITE[keep]:
                self._place_warriors("M", c, 1)
        spots = [keep] + D.ADJ[keep]
        for c, t in bot.choose_start_buildings(self, spots):
            assert c in spots and self.open_slots(c) > 0 and t not in self.m_on_map
            self.cl[c]["b"].append(("M", t))
            self.m_on_map[t] += 1
        self.log(f"keep in {self.cname(keep)}; sawmill/workshop/recruiter at "
                 f"{', '.join(self.cname(c) for c in self.m_buildings())}", "M")

    def _setup_E(self):
        bot = self.bots["E"]
        taken = set(self.start_corner.values())
        free = [c for c in D.CORNERS if c not in taken]
        opp = [c for c in free if any(D.OPPOSITE[t] == c for t in taken)]
        corner = bot.choose_eyrie_corner(self, opp or free)   # 7.3.2
        self.start_corner["E"] = corner
        self.cl[corner]["b"].append(("E", "roost"))
        self._place_warriors("E", corner, 6)
        self.leader = bot.choose_leader(self, list(D.LEADERS))
        self.leaders_up = [l for l in D.LEADERS if l != self.leader]
        self.decree = {col: [] for col in D.DECREE_COLS}
        self._tuck_viziers()
        self.log(f"roost and 6 warriors in {self.cname(corner)}; leader {self.leader}", "E")

    def _tuck_viziers(self):
        for i, col in enumerate(D.LEADERS[self.leader]):
            self.decree[col].append(dict(id=-1 - i, name="Loyal Vizier", suit="bird", kind="vizier"))

    def _setup_A(self):
        self.supporters = []
        self.officers = 0
        self.sym_placed = 0
        self.bases = {}                        # suit -> clearing
        for _ in range(3):                     # 8.3.4
            self.supporters.append(self._deal())
        self.log("3 supporters drawn; nothing on the map", "A")

    def _setup_V(self):
        bot = self.bots["V"]
        self.char = bot.choose_character(self, list(D.CHARACTERS))
        self.vag = bot.choose_forest(self, sorted(D.FORESTS))
        qs = list(D.QUESTS)
        self.rng.shuffle(qs)
        self.quests, self.quest_deck = qs[:3], qs[3:]
        self.done_quests = []
        ruin_items = list(D.RUIN_ITEMS)
        self.rng.shuffle(ruin_items)
        self.ruin_items = {c: [ruin_items[i]] for i, c in enumerate(D.RUINS)}
        self.vitems = [dict(t=t, up=True, dmg=False) for t in D.CHARACTERS[self.char]]
        self.rel = {f: 0 for f in self.factions if f != "V"}   # 0..3 (3 = Allied) or "H"
        self.aids = Counter()
        self.log(f"{self.char} in forest {self.vag}; quests {', '.join(f'{q[0]} ({q[1]})' for q in self.quests)}", "V")

    # ------------------------------------------------------------------ cards (2.1)
    def _deal(self):
        if not self.deck:
            self.deck, self.discard = self.discard, []
            self.rng.shuffle(self.deck)
            self.log("deck empty: discard pile shuffled into a new deck")
        return self.deck.pop() if self.deck else None

    def draw(self, f, n=1, quiet=False):
        got = 0
        for _ in range(n):
            c = self._deal()
            if c:
                self.hands[f].append(c)
                got += 1
        if not quiet and got:
            self.stats["cards_drawn"] += got
        return got

    def discard_card(self, card):
        """Spend/discard: dominance cards go beside the map instead (3.3.3)."""
        if card["kind"] == "dominance":
            self.avail_dom.append(card)
        elif card["kind"] != "vizier":
            self.discard.append(card)

    def spend(self, f, card):
        self.hands[f].remove(card)
        self.discard_card(card)

    def cards_matching(self, f, suit):
        return [c for c in self.hands[f] if matches(c["suit"], suit)]

    def discard_down(self, f):
        extra = len(self.hands[f]) - D.HAND_LIMIT
        if extra > 0:
            out = self.bots[f].discard_down(self, extra)
            assert len(out) == extra and all(c in self.hands[f] for c in out), "discard down"
            for c in out:
                self.spend(f, c)
            self.log(f"discards {extra} down to {D.HAND_LIMIT}", f)

    # ------------------------------------------------------------------ map queries (2.2-2.5)
    def cname(self, c):
        return f"{D.CLEARINGS[c]['suit']}-{c}"

    def suit(self, c):
        return D.CLEARINGS[c]["suit"]

    def open_slots(self, c):
        return D.CLEARINGS[c]["slots"] - len(self.cl[c]["b"])

    def buildings(self, c, f):
        return [t for o, t in self.cl[c]["b"] if o == f]

    def presence(self, c, f):
        """Warriors + buildings for rule (2.5)."""
        return self.cl[c]["w"][f] + len(self.buildings(c, f))

    def ruler(self, c):
        best, who = 0, []
        for f in self.factions:
            p = self.presence(c, f)
            if p > best:
                best, who = p, [f]
            elif p == best and p > 0:
                who.append(f)
        if len(who) == 1:
            return who[0]
        if "E" in who:                          # Lords of the Forest (7.2.2)
            return "E"
        return None

    def rules(self, f, c):
        return self.ruler(c) == f

    def has_pieces(self, c, f):
        x = self.cl[c]
        if f == "V":
            return self.vag == c
        tokens = (f == "M" and (x["wood"] or x["keep"])) or (f == "A" and x["sym"])
        return bool(x["w"][f] or self.buildings(c, f) or tokens)

    def can_place(self, f, c):
        """The keep blocks other factions from placing pieces (6.2.2)."""
        return not (self.cl[c]["keep"] and f != "M")

    def m_buildings(self):
        return [c for c in D.CLEARINGS for o, t in self.cl[c]["b"] if o == "M"]

    def roosts(self):
        return [c for c in D.CLEARINGS if "roost" in self.buildings(c, "E")]

    def sympathetic(self):
        return [c for c in D.CLEARINGS if self.cl[c]["sym"]]

    # ------------------------------------------------------------------ scoring (3.2)
    def score(self, f, n, why):
        if n == 0 or f not in self.vp:
            return
        if self.dominance[f] is not None or (f == "V" and self.coalition):
            return                               # 3.3.1 / 9.2.8: no more points
        before = self.vp[f]
        self.vp[f] = max(0, self.vp[f] + n)     # EST: the track has no negative spaces
        self.vp_log.setdefault(f, Counter())[why] += self.vp[f] - before
        self.log(f"{'+' if n > 0 else ''}{n} VP ({why}) → {self.vp[f]}", f)
        if self.vp[f] >= D.WIN_VP:
            self._win([f], f"{D.WIN_VP} VP")

    def _win(self, fs, reason):
        if self.coalition and self.coalition in fs and "V" not in fs:
            fs = fs + ["V"]
        self.winners, self.reason = fs, reason
        raise GameOver()

    # ------------------------------------------------------------------ placing and removing (G.20, G.24)
    def _place_warriors(self, f, c, n):
        n = min(n, self.supply[f])
        self.supply[f] -= n
        self.cl[c]["w"][f] += n
        return n

    def place_building(self, f, c, t):
        if self.open_slots(c) <= 0 or not self.can_place(f, c):
            raise IllegalAction(f"no slot for {t} in {c}")
        self.cl[c]["b"].append((f, t))

    def remove_warriors(self, c, f, n, by=None, battle=False, hospital=True):
        n = min(n, self.cl[c]["w"][f])
        if n <= 0:
            return 0
        self.cl[c]["w"][f] -= n
        self.supply[f] += n
        self.stats[f"warriors_lost_{f}"] += n
        if by == "V" and f != "V":
            for _ in range(n):                  # each warrior counts on its own (9.2.9.III)
                self._vag_removed(f, warrior=True, battle=battle)
        if f == "M" and hospital:
            self.field_hospitals(c, n)
        return n

    def field_hospitals(self, c, n):
        """6.2.3. Called once all pieces removed at the same time are gone (1.5.4), so a keep lost too can't help."""
        if n <= 0 or not self.keep:
            return
        card = self.bots["M"].field_hospital(self, c, n)
        if card:
            assert card in self.hands["M"] and matches(card["suit"], self.suit(c)), "Field Hospitals card"
            self.spend("M", card)
            back = min(n, self.supply["M"])
            self.supply["M"] -= back
            self.cl[self.keep]["w"]["M"] += back
            self.stats["field_hospitals"] += 1
            self.log(f"Field Hospitals: spends {card['name']} ({card['suit']}), {back} warriors back to the keep", "M")

    def remove_piece(self, c, f, piece, by=None, battle=False):
        """Remove one building or token. piece: building type, 'wood', 'keep' or 'sym'."""
        x = self.cl[c]
        if piece == "wood":
            x["wood"] -= 1
            self.wood_supply += 1
        elif piece == "keep":
            x["keep"] = False
            self.keep = None
            self.log("the keep is destroyed: no more Field Hospitals", "M")
        elif piece == "sym":
            x["sym"] = False
            self.sym_placed -= 1
            if by and by != "A":
                self.outrage(by, c)
        else:
            x["b"].remove((f, piece))
            if f == "M":
                self.m_on_map[piece] -= 1
            elif f == "A":
                self._base_removed(piece)
        self.stats["pieces_removed"] += 1
        if by and by != f:
            self.score(by, 1, f"removed {D.NAME[f]} {piece}")   # 3.2.1
            if by == "V":
                self._vag_removed(f, warrior=False, battle=battle)

    def removable(self, c, f):
        """Non-warrior pieces of f in c: buildings then tokens."""
        x = self.cl[c]
        out = list(self.buildings(c, f))
        if f == "M":
            out += ["wood"] * x["wood"] + (["keep"] if x["keep"] else [])
        if f == "A" and x["sym"]:
            out.append("sym")
        return out

    def remove_all_enemies(self, c, by, hospital=True):
        """Revolt / Favor: remove every enemy piece in c (9.2.2.I for the Vagabond). Returns cat warriors removed."""
        cats = 0
        for f in self.factions:
            if not self.enemies(by, f):
                continue
            if f == "V":
                if self.vag == c:
                    self.vag_damage(3, "everything in the clearing removed")
                continue
            n = self.remove_warriors(c, f, self.cl[c]["w"][f], by=by, hospital=False)
            if f == "M":
                cats = n
            for p in self.removable(c, f):
                self.remove_piece(c, f, p, by=by)
        if hospital:
            self.field_hospitals(c, cats)
        return cats

    def enemies(self, a, b):
        """G.8: players in a coalition are not enemies."""
        return a != b and not (self.coalition and {a, b} == {"V", self.coalition})

    # ------------------------------------------------------------------ Alliance hooks
    def _base_removed(self, base):
        suit = base.split("_")[1]
        del self.bases[suit]
        lost = [s for s in self.supporters if matches(s["suit"], suit)]
        for s in lost:                          # 8.2.4 discard matching supporters, birds too
            self.supporters.remove(s)
            self.discard_card(s)
        off = (self.officers + 1) // 2
        self.officers -= off
        self.supply["A"] += off
        if not self.bases:
            while len(self.supporters) > D.A_SUPPORTER_CAP:
                self.discard_card(self.supporters.pop(0))
        self.log(f"{suit} base lost: {len(lost)} supporters and {off} officers gone", "A")

    def add_supporter(self, card):
        if not self.bases and len(self.supporters) >= D.A_SUPPORTER_CAP:
            self.discard_card(card)             # 8.2.3.I stack full
            return False
        self.supporters.append(card)
        return True

    def outrage(self, f, c):
        """8.2.6: another player removed sympathy or moved warriors into a sympathetic clearing."""
        if "A" not in self.factions or f == "A":
            return
        suit = self.suit(c)
        opts = self.cards_matching(f, suit)
        if opts:
            card = self.bots[f].outrage_card(self, opts)
            self.hands[f].remove(card)
            self.add_supporter(card)
            self.log(f"Outrage in {self.cname(c)}: {D.NAME[f]} gives {card['name']} ({card['suit']}) as a supporter", "A")
        else:
            card = self._deal()
            if card:
                self.add_supporter(card)
            self.log(f"Outrage in {self.cname(c)}: {D.NAME[f]} has no {suit} card, shows hand; Alliance draws a supporter", "A")
        self.stats["outrage"] += 1

    # ------------------------------------------------------------------ movement (4.2)
    def can_move(self, f, a, b):
        if b not in D.ADJ[a]:
            return False
        return f == "V" or self.rules(f, a) or self.rules(f, b)

    def move(self, f, a, b, n):
        if n <= 0 or self.cl[a]["w"][f] < n or not self.can_move(f, a, b):
            raise IllegalAction(f"{f} move {n} {a}->{b}")
        self.cl[a]["w"][f] -= n
        self.cl[b]["w"][f] += n
        self.stats["moves"] += 1
        self.log(f"moves {n} warrior{'s' * (n > 1)} {self.cname(a)} → {self.cname(b)}", f)
        if self.cl[b]["sym"] and f != "A":
            self.outrage(f, b)

    # ------------------------------------------------------------------ battle (4.3)
    def can_battle(self, f, c, d):
        if d not in self.factions or not self.enemies(f, d):
            return False
        att = self.vag == c if f == "V" else self.cl[c]["w"][f] > 0
        return att and self.has_pieces(c, d)

    def battle(self, f, c, d):
        if not self.can_battle(f, c, d):
            raise IllegalAction(f"{f} battle {d} in {c}")
        self.stats["battles"] += 1
        self.battle_removed = Counter()
        self.log(f"battles {D.NAME[d]} in {self.cname(c)}", f)
        hits = {f: 0, d: 0}                     # hits dealt BY each side
        # 4.3.1 ambush
        if "Scouting Party" not in self.persist[f]:
            amb = [x for x in self.hands[d] if x["kind"] == "ambush" and matches(x["suit"], self.suit(c))]
            if amb and self.bots[d].ambush(self, f, c):
                card = amb[0]
                foil = [x for x in self.hands[f] if x["kind"] == "ambush" and matches(x["suit"], self.suit(c))]
                self.stats["ambush"] += 1
                if foil and self.bots[f].foil(self, d, c):
                    self.spend(f, foil[0])
                    self.spend(d, card)
                    self.stats["ambush_foiled"] += 1
                    self.log(f"ambush! foiled by {D.NAME[f]}'s own ambush", d)
                else:
                    self.spend(d, card)
                    self.log("ambush! 2 immediate hits", d)
                    self._take_hits(c, f, 2, by=d, battle=True)
                    if f != "V" and self.cl[c]["w"][f] == 0:
                        self.log("no attacking warriors left: battle ends", d)
                        self._despot(f, d)
                        return
        # 4.3.3 roll
        r1, r2 = self.rng.choice(D.DIE), self.rng.choice(D.DIE)
        hi, lo = max(r1, r2), min(r1, r2)
        att_roll, def_roll = (lo, hi) if d == "A" else (hi, lo)   # Guerrilla War (8.2.2)
        hits[f] = min(att_roll, self.max_roll(f, c))
        hits[d] = min(def_roll, self.max_roll(d, c))
        extra = []
        # 4.3.4-4.3.5 after-roll effects and extra hits
        if self.defenseless(d, c):
            hits[f] += 1
            extra.append("defenseless +1")
        if f == "E" and self.leader == "Commander":
            hits[f] += 1
            extra.append("Commander +1")
        if "Brutal Tactics" in self.persist[f] and self.bots[f].brutal(self, d, c):
            hits[f] += 1
            extra.append("Brutal Tactics +1")
            self.score(d, 1, "Brutal Tactics used against them")
        if "Sappers" in self.persist[d] and self.bots[d].sappers(self, f, c):
            self._discard_persistent(d, "Sappers")
            hits[d] += 1
            extra.append("Sappers +1")
        for side, other in ((f, d), (d, f)):
            rolled = min(att_roll if side == f else def_roll, self.max_roll(side, c))
            if "Armorers" in self.persist[other] and rolled > 0 and self.bots[other].armorers(self, side, c, rolled):
                self._discard_persistent(other, "Armorers")
                hits[side] -= rolled
                extra.append(f"Armorers ignores {rolled}")
        self.log(f"rolls {hi}/{lo}: deals {hits[f]}, takes {hits[d]}" + (f" ({'; '.join(extra)})" if extra else ""), f)
        # 4.3.6 deal hits (simultaneous)
        self._take_hits(c, d, hits[f], by=f, battle=True)
        self._take_hits(c, f, hits[d], by=d, battle=True)
        self._despot(f, d)

    def _despot(self, f, d):
        if "E" in (f, d) and self.leader == "Despot" and self.battle_removed["E"]:
            self.score("E", 1, "Despot")   # 7.8.4

    def max_roll(self, f, c):
        if f == "V":
            return sum(1 for i in self.vitems if i["t"] == "sword" and not i["dmg"])   # 9.2.6
        return self.cl[c]["w"][f]                                                     # 4.3.3.I

    def defenseless(self, f, c):
        if f == "V":
            return not any(i["t"] == "sword" and not i["dmg"] for i in self.vitems)   # 9.2.4
        return self.cl[c]["w"][f] == 0

    def _discard_persistent(self, f, name):
        self.persist[f].remove(name)
        card = next(x for x in self.play_area[f] if x["name"] == name)
        self.play_area[f].remove(card)
        self.discard_card(card)

    def _take_hits(self, c, f, n, by, battle):
        if n <= 0:
            return
        if f == "V":
            self.vag_damage(n, "battle")
            return
        w = min(n, self.cl[c]["w"][f])
        self.remove_warriors(c, f, w, by=by, battle=battle, hospital=False)
        n -= w
        if n > 0:                               # warriors first, then buildings/tokens (owner chooses)
            for p in self.bots[f].order_losses(self, c, self.removable(c, f))[:n]:
                self.remove_piece(c, f, p, by=by, battle=battle)
                self.battle_removed[by] += 1
        if f == "M":
            self.field_hospitals(c, w)          # after the keep may have gone in the same hits (1.5.4)

    # ------------------------------------------------------------------ crafting (4.1)
    def craft_pieces(self, f):
        cnt = Counter()
        for c in D.CLEARINGS:
            s = self.suit(c)
            if f == "M":
                cnt[s] += self.buildings(c, "M").count("workshop")
            elif f == "E":
                cnt[s] += self.buildings(c, "E").count("roost")
            elif f == "A":
                cnt[s] += int(self.cl[c]["sym"])
        return cnt - self.used_craft[f]

    def can_craft(self, f, card):
        if card["kind"] not in ("item", "persistent", "favor"):
            return False
        if card["kind"] == "persistent" and card["name"] in self.persist[f]:
            return False                        # 4.1.4
        if card["kind"] == "item" and self.items.get(card["item"], 0) <= 0:
            return False                        # 4.1.2
        cost = card["cost"]
        if f == "V":
            if not isinstance(self.vag, int):
                return False
            s = self.suit(self.vag)
            return all(x in (s, "any") for x in cost) and len(self.v_ready("hammer")) >= len(cost)
        avail = self.craft_pieces(f)
        need = Counter(x for x in cost if x != "any")
        if any(avail[s] < k for s, k in need.items()):
            return False
        return sum(avail.values()) >= len(cost)

    def craft(self, f, card):
        if card not in self.hands[f] or not self.can_craft(f, card):
            raise IllegalAction(f"{f} craft {card['name']}")
        if f == "V":
            for _ in card["cost"]:
                self.v_exhaust("hammer")
        else:
            avail = self.craft_pieces(f)
            for x in sorted(card["cost"], key=lambda s: s == "any"):
                if x == "any":
                    x = max(SUITS, key=lambda s: (avail[s], s))
                self.used_craft[f][x] += 1
                avail[x] -= 1
        self.hands[f].remove(card)
        self.stats["crafted"] += 1
        k = card["kind"]
        if k == "item":
            self.items[card["item"]] -= 1
            vp = card["vp"]
            if f == "E" and self.leader != "Builder":
                vp = 1                          # Disdain for Trade (7.2.3)
            if f == "V":
                self.vitems.append(dict(t=card["item"], up=True, dmg=False))
            else:
                self.crafted[f].append(card["item"])
            self.discard_card(card)
            self.log(f"crafts {card['name']} ({card['item']})", f)
            self.score(f, vp, f"crafted {card['item']}")
        elif k == "persistent":
            self.persist[f].append(card["name"])
            self.play_area[f].append(card)
            self.log(f"crafts {card['name']} (persistent)", f)
        else:
            suit = card["name"].split()[-1].lower()
            suit = {"foxes": "fox", "mice": "mouse", "rabbits": "rabbit"}[suit]
            self.log(f"crafts {card['name']}: every enemy piece in {suit} clearings is removed", f)
            self.discard_card(card)
            self.stats["favors"] += 1
            lost = {c: self.remove_all_enemies(c, f, hospital=False) for c in D.CLEARINGS if self.suit(c) == suit}
            for c, n in lost.items():           # one simultaneous removal: hospitals only if the keep survived
                self.field_hospitals(c, n)

    # ------------------------------------------------------------------ dominance (3.3)
    def can_activate_dominance(self, f, card):
        if card not in self.hands[f] or card["kind"] != "dominance" or self.dominance[f] is not None:
            return False
        if f == "V":
            return self.n >= 4 and self.coalition is None and self.coalition_target() is not None
        return self.vp[f] >= 10

    def coalition_target(self):
        others = [f for f in self.factions if f != "V"]
        low = min(self.vp[f] for f in others)
        return sorted(f for f in others if self.vp[f] == low)[0]

    def activate_dominance(self, f, card):
        if not self.can_activate_dominance(f, card):
            raise IllegalAction("dominance")
        self.hands[f].remove(card)
        self.stats["dominance"] += 1
        if f == "V":
            self.coalition = self.coalition_target()
            self.dominance["V"] = card
            if self.rel.get(self.coalition) == "H":
                self.rel[self.coalition] = 0
            self.log(f"plays {card['suit']} Dominance: coalition with {D.NAME[self.coalition]}", "V")
            return
        self.dominance[f] = card
        self.log(f"activates {card['suit']} Dominance at {self.vp[f]} VP and stops scoring", f)

    def dominance_won(self, f):
        card = self.dominance.get(f)
        if not card or f == "V":
            return False
        if card["suit"] == "bird":
            return any(self.rules(f, a) and self.rules(f, b) for a, b in ((1, 3), (2, 4)))
        return sum(1 for c in D.CLEARINGS if self.suit(c) == card["suit"] and self.rules(f, c)) >= 3

    def take_dominance(self, f, dom, pay):
        if dom not in self.avail_dom or pay not in self.hands[f]:
            raise IllegalAction("take dominance")
        if dom["suit"] == "bird" and pay["suit"] != "bird" or not matches(pay["suit"], dom["suit"]):
            raise IllegalAction("take dominance: wrong suit")   # 3.3.4
        self.spend(f, pay)
        self.avail_dom.remove(dom)
        self.hands[f].append(dom)
        self.log(f"takes the available {dom['suit']} Dominance", f)

    # ------------------------------------------------------------------ generic Daylight options
    def daylight_common(self, f):
        """Craft, dominance and available-dominance choices any faction may make in Daylight."""
        bot = self.bots[f]
        for card in bot.crafts(self):
            if card in self.hands[f] and self.can_craft(f, card):
                self.craft(f, card)
        d = bot.dominance(self)
        if d:
            self.activate_dominance(f, d)
        t = bot.take_dominance(self)
        if t:
            self.take_dominance(f, *t)

    def persistent_start_birdsong(self, f):
        bot = self.bots[f]
        if "Better Burrow Bank" in self.persist[f]:
            other = bot.bbb_target(self)
            if other:
                assert other in self.factions and other != f, "Better Burrow Bank target"
                self.draw(f)
                self.draw(other)
                self.log(f"Better Burrow Bank: draws, and so does {D.NAME[other]}", f)
        if "Stand and Deliver!" in self.persist[f]:
            other = bot.stand_and_deliver(self)
            if other and self.hands[other]:
                assert other in self.factions and other != f, "Stand and Deliver! target"
                card = self.rng.choice(self.hands[other])
                self.hands[other].remove(card)
                self.hands[f].append(card)
                self.log(f"Stand and Deliver!: takes a random card from {D.NAME[other]}", f)
                self.score(other, 1, "Stand and Deliver! victim")
        if "Royal Claim" in self.persist[f] and bot.royal_claim(self):
            n = sum(1 for c in D.CLEARINGS if self.rules(f, c))
            self._discard_persistent(f, "Royal Claim")
            self.log(f"discards Royal Claim", f)
            self.score(f, n, "Royal Claim")

    def persistent_daylight(self, f):
        bot = self.bots[f]
        if "Command Warren" in self.persist[f]:
            b = bot.free_battle(self)
            if b:
                self.log("Command Warren battle", f)
                self.battle(f, *b)
        if "Tax Collector" in self.persist[f]:
            c = bot.tax_collector(self)
            if c is not None and self.cl[c]["w"][f] > 0:
                self.remove_warriors(c, f, 1)
                self.draw(f)
                self.log(f"Tax Collector: removes a warrior in {self.cname(c)} to draw", f)

    def persistent_evening(self, f):
        if "Cobbler" in self.persist[f]:
            m = self.bots[f].free_move(self)
            if m:
                self.log("Cobbler move", f)
                self.move(f, *m)
    # SKIP: Codebreakers (looking at a hand) changes nothing for these bots; it is crafted but has no effect.

    # ------------------------------------------------------------------ turn loop
    def play(self, max_rounds=60):
        try:
            while self.round < max_rounds:
                self.round += 1
                for f in self.order:
                    self.turn_of = f
                    self.take_turn(f)
                self.history.append((self.round, dict(self.vp)))
                self.round_marks.append(len(self.lines))
            best = max(self.vp.values())
            self._win(sorted(f for f in self.factions if self.vp[f] == best), "turn limit")
        except GameOver:
            pass
        self.log(f"GAME OVER: {' & '.join(D.NAME[f] for f in self.winners)} win ({self.reason}); "
                 + ", ".join(f"{D.NAME[f]} {self.vp[f]}" for f in self.factions))
        return dict(winners=self.winners, reason=self.reason, vp=dict(self.vp), rounds=self.round)

    def take_turn(self, f):
        self.used_craft[f] = Counter()
        self.once = set()
        if self.dominance_won(f):              # 3.3.1 checked at start of Birdsong
            self.log(f"rules the clearings on its {self.dominance[f]['suit']} Dominance card", f)
            self._win([f], "dominance")
        self.persistent_start_birdsong(f)
        getattr(self, "turn_" + f)()

    # ------------------------------------------------------------------ Marquise de Cat (6)
    def turn_M(self):
        bot = self.bots["M"]
        self.m_birdsong()
        self.persistent_daylight("M")
        self.daylight_common("M")
        self.m_actions, self.m_recruited = 3, False
        while True:
            if self.m_actions <= 0:             # Hawks for Hire: pay the bird before choosing the action
                bird = bot.hawks_for_hire(self)
                if not bird:
                    break
                assert bird in self.hands["M"] and bird["suit"] == "bird", "Hawks for Hire"
                self.spend("M", bird)
                self.m_actions += 1
                self.log("spends a bird card for an extra action (Hawks for Hire)", "M")
            act = bot.marquise_action(self)
            if not act:
                break
            self.m_actions -= 1
            self.stats["actions_M"] += 1
            getattr(self, "m_" + act[0])(*act[1:])
        self.persistent_evening("M")
        n = 1 + sum(1 for k in D.M_RECRUITER_DRAW if self.m_on_map["recruiter"] >= k)
        self.draw("M", n)
        self.log(f"Evening: draws {n}", "M")
        self.discard_down("M")

    def m_birdsong(self):
        placed = 0
        for c in D.CLEARINGS:                   # 6.4 one wood per sawmill
            k = min(self.buildings(c, "M").count("sawmill"), self.wood_supply)
            self.cl[c]["wood"] += k
            self.wood_supply -= k
            placed += k
        if placed:
            self.log(f"Birdsong: {placed} wood at sawmills", "M")

    def m_battle(self, c, d):
        self.battle("M", c, d)

    def m_march(self, moves):
        for a, b, n in moves[:2]:
            self.move("M", a, b, n)

    def m_recruit(self):
        if self.m_recruited:
            raise IllegalAction("recruit once per turn")
        self.m_recruited = True
        cs = [c for c in D.CLEARINGS for t in self.buildings(c, "M") if t == "recruiter"]
        n = 0
        for c in cs:
            n += self._place_warriors("M", c, 1)
        self.log(f"recruits {n} warrior{'s' * (n != 1)}", "M")

    def m_wood_reach(self, c):
        """Clearings whose wood can pay for a build in c: c plus clearings linked to it through ruled clearings."""
        seen, todo = {c}, [c]
        while todo:
            x = todo.pop()
            for y in D.ADJ[x]:
                if y not in seen and self.rules("M", y):
                    seen.add(y)
                    todo.append(y)
        return seen

    def m_build_cost(self, t):
        k = self.m_on_map[t]
        return None if k >= D.M_BUILDINGS else D.M_COST[k]

    def m_can_build(self, c, t):
        cost = self.m_build_cost(t)
        if cost is None or not self.rules("M", c) or self.open_slots(c) <= 0:
            return False
        return sum(self.cl[x]["wood"] for x in self.m_wood_reach(c)) >= cost

    def m_build(self, c, t):
        if not self.m_can_build(c, t):
            raise IllegalAction(f"build {t} in {c}")
        cost = self.m_build_cost(t)
        reach = sorted(self.m_wood_reach(c), key=lambda x: (x != c, x))
        for x in reach:
            while cost and self.cl[x]["wood"]:
                self.cl[x]["wood"] -= 1
                self.wood_supply += 1
                cost -= 1
        vp = D.M_VP[t][self.m_on_map[t]]
        self.place_building("M", c, t)
        self.m_on_map[t] += 1
        self.stats["built_M"] += 1
        self.log(f"builds a {t} in {self.cname(c)}", "M")
        self.score("M", vp, f"{t} #{self.m_on_map[t]}")

    def m_overwork(self, c, card):
        if "sawmill" not in self.buildings(c, "M") or not matches(card["suit"], self.suit(c)) or not self.wood_supply:
            raise IllegalAction("overwork")
        self.spend("M", card)
        self.cl[c]["wood"] += 1
        self.wood_supply -= 1
        self.log(f"overworks the sawmill in {self.cname(c)}", "M")

    # ------------------------------------------------------------------ Eyrie Dynasties (7)
    def turn_E(self):
        bot = self.bots["E"]
        if not self.hands["E"]:                 # 7.4.1
            self.draw("E")
            self.log("Emergency Orders: draws a card", "E")
        adds = bot.decree_add(self)             # 7.4.2
        if not adds and self.hands["E"]:
            adds = [(self.hands["E"][0], "move")]
        if len(adds) > 2 or sum(1 for c, _ in adds if c["suit"] == "bird") > 1:
            raise IllegalAction("decree add")
        for card, col in adds:
            self.hands["E"].remove(card)
            self.decree[col].append(card)
        if adds:
            self.log("adds " + ", ".join(f"{c['suit']} to {col}" for c, col in adds) + " → Decree "
                     + self.decree_str(), "E")
        self.e_new_roost()
        self.persistent_daylight("E")
        self.daylight_common("E")
        if not self.resolve_decree():
            self.turmoil()
        self.persistent_evening("E")
        k = len(self.roosts())
        self.score("E", D.ROOST_VP[k], f"{k} roost{'s' * (k != 1)}")
        n = 1 + sum(1 for x in D.ROOST_DRAW if k >= x)
        self.draw("E", n)
        self.log(f"Evening: draws {n}", "E")
        self.discard_down("E")

    def e_new_roost(self):
        if self.roosts():                       # 7.4.3 A New Roost
            return
        opts = [c for c in D.CLEARINGS if self.open_slots(c) > 0 and self.can_place("E", c)]
        if opts:
            low = min(sum(self.cl[c]["w"].values()) for c in opts)
            c = self.bots["E"].new_roost(self, [c for c in opts if sum(self.cl[c]["w"].values()) == low])
            self.place_building("E", c, "roost")
            self._place_warriors("E", c, 3)
            self.log(f"A New Roost in {self.cname(c)}", "E")

    def decree_str(self):
        short = {"fox": "F", "rabbit": "R", "mouse": "M", "bird": "B"}
        return " | ".join(f"{col[:3]} " + "".join(short[c["suit"]] for c in self.decree[col]) for col in D.DECREE_COLS)

    def decree_options(self, col, suit):
        n_rec = 2 if self.leader == "Charismatic" else 1
        out = []
        for c in D.CLEARINGS:
            if not matches(suit, self.suit(c)):
                continue
            if col == "recruit" and "roost" in self.buildings(c, "E") and self.supply["E"] >= n_rec:
                out.append(c)
            elif col == "move" and self.cl[c]["w"]["E"]:
                out += [(c, b) for b in D.ADJ[c] if self.can_move("E", c, b)]
            elif col == "battle" and self.cl[c]["w"]["E"]:
                out += [(c, d) for d in self.factions if self.can_battle("E", c, d)]
            elif col == "build" and self.rules("E", c) and self.open_slots(c) > 0 and "roost" not in self.buildings(c, "E") \
                    and len(self.roosts()) < D.E_ROOSTS and self.can_place("E", c):
                out.append(c)
        return out

    def resolve_decree(self):
        """7.5.2: every card, left to right by column; birds last within a column. False = turmoil."""
        bot = self.bots["E"]
        for col in D.DECREE_COLS:
            for card in sorted(self.decree[col], key=lambda x: x["suit"] == "bird"):
                opts = self.decree_options(col, card["suit"])
                if not opts:
                    self.log(f"cannot {col} in a {card['suit']} clearing", "E")
                    return False
                o = bot.decree_target(self, col, card, opts)
                assert o in opts, "decree target"
                self.stats["decree_actions"] += 1
                if col == "recruit":
                    n = self._place_warriors("E", o, 2 if self.leader == "Charismatic" else 1)
                    self.log(f"Decree recruit: {n} in {self.cname(o)}", "E")
                elif col == "move":
                    a, b = o
                    self.move("E", a, b, bot.move_count(self, a, b))
                elif col == "battle":
                    self.battle("E", *o)
                else:
                    self.place_building("E", o, "roost")
                    self.log(f"Decree build: roost in {self.cname(o)}", "E")
        return True

    def turmoil(self):
        """7.7 Humiliate, Purge, Depose, Rest."""
        birds = sum(1 for col in D.DECREE_COLS for c in self.decree[col] if c["suit"] == "bird")
        self.stats["turmoil"] += 1
        self.log(f"TURMOIL: humiliated for {birds} bird cards", "E")
        self.score("E", -birds, "turmoil")
        for col in D.DECREE_COLS:
            for c in self.decree[col]:
                self.discard_card(c)
        self.decree = {col: [] for col in D.DECREE_COLS}
        if not self.leaders_up:                 # A New Clutch
            self.leaders_up = list(D.LEADERS)
        old = self.leader
        self.leader = self.bots["E"].choose_leader(self, list(self.leaders_up))
        self.leaders_up.remove(self.leader)
        self._tuck_viziers()
        self.log(f"{old} deposed; new leader {self.leader}", "E")

    # ------------------------------------------------------------------ Woodland Alliance (8)
    def a_spend_supporters(self, suit, n):
        """Spend n supporters of suit; birds are wild. Returns False if not enough."""
        exact = [s for s in self.supporters if s["suit"] == suit]
        birds = [s for s in self.supporters if s["suit"] == "bird"]
        if len(exact) + len(birds) < n:
            return False
        for s in (exact + birds)[:n]:
            self.supporters.remove(s)
            self.discard_card(s)
        return True

    def a_supporters_of(self, suit):
        return sum(1 for s in self.supporters if matches(s["suit"], suit))

    def a_revolt_options(self):
        out = []
        for c in self.sympathetic():
            s = self.suit(c)
            if s in self.bases or any(t.startswith("base") for t in self.buildings(c, "A")):
                continue
            free = self.open_slots(c) + sum(1 for o, t in self.cl[c]["b"] if o not in ("A", "ruin"))
            if free > 0 and self.a_supporters_of(s) >= 2:
                out.append(c)
        return out

    def a_revolt(self, c):
        if c not in self.a_revolt_options():
            raise IllegalAction("revolt")
        s = self.suit(c)
        self.a_spend_supporters(s, 2)
        self.log(f"REVOLT in {self.cname(c)}", "A")
        self.stats["revolts"] += 1
        self.remove_all_enemies(c, "A")
        self.place_building("A", c, f"base_{s}")
        self.bases[s] = c
        n = sum(1 for x in self.sympathetic() if self.suit(x) == s)
        n = self._place_warriors("A", c, n)
        if self.supply["A"]:
            self.supply["A"] -= 1
            self.officers += 1
        self.log(f"base placed with {n} warriors; officers {self.officers}", "A")

    def a_sympathy_cost(self, c):
        cost = D.SYM_COST[self.sym_placed]
        if any(f != "A" and self.cl[c]["w"][f] >= 3 for f in self.factions):
            cost += 1                           # Martial Law (8.4.2.IIa)
        return cost

    def a_spread_options(self):
        if self.sym_placed >= D.A_SYMPATHY:
            return []
        sym = self.sympathetic()
        cand = [c for c in D.CLEARINGS if not self.cl[c]["sym"] and self.can_place("A", c)
                and (not sym or any(self.cl[a]["sym"] for a in D.ADJ[c]))]
        return [c for c in cand if self.a_supporters_of(self.suit(c)) >= self.a_sympathy_cost(c)]

    def a_place_sympathy(self, c, why):
        vp = D.SYM_VP[self.sym_placed]
        self.cl[c]["sym"] = True
        self.sym_placed += 1
        self.stats["sympathy"] += 1
        self.log(f"{why}: sympathy in {self.cname(c)}", "A")
        self.score("A", vp, f"sympathy #{self.sym_placed}")

    def a_spread(self, c):
        if c not in self.a_spread_options():
            raise IllegalAction("spread")
        self.a_spend_supporters(self.suit(c), self.a_sympathy_cost(c))
        self.a_place_sympathy(c, "spreads sympathy")

    def turn_A(self):
        bot = self.bots["A"]
        while True:                             # 8.4.1 Revolt
            c = bot.revolt(self)
            if c is None:
                break
            self.a_revolt(c)
        while True:                             # 8.4.2 Spread Sympathy
            c = bot.spread(self)
            if c is None:
                break
            self.a_spread(c)
        self.persistent_daylight("A")
        self.daylight_common("A")
        for card in bot.mobilize(self):         # 8.5.2
            if card in self.hands["A"]:
                self.hands["A"].remove(card)
                self.add_supporter(card)
                self.log(f"mobilizes a {card['suit']} card", "A")
        for card in bot.train(self):            # 8.5.3
            if card in self.hands["A"] and self.supply["A"] and any(matches(card["suit"], s) for s in self.bases):
                self.spend("A", card)
                self.supply["A"] -= 1
                self.officers += 1
                self.log(f"trains an officer ({self.officers})", "A")
        self.persistent_evening("A")
        done = 0
        while done < self.officers:              # 8.6.1 Military Operations (officers can be lost mid-turn)
            done += 1
            op = bot.operation(self)
            if not op:
                break
            self.stats["operations"] += 1
            kind = op[0]
            if kind == "move":
                self.move("A", *op[1:])
            elif kind == "battle":
                self.battle("A", *op[1:])
            elif kind == "recruit":
                c = op[1]
                if not any(t.startswith("base") for t in self.buildings(c, "A")):
                    raise IllegalAction("recruit needs a base")
                self._place_warriors("A", c, 1)
                self.log(f"recruits in {self.cname(c)}", "A")
            elif kind == "organize":
                c = op[1]
                if self.cl[c]["sym"] or not self.cl[c]["w"]["A"] or self.sym_placed >= D.A_SYMPATHY or not self.can_place("A", c):
                    raise IllegalAction("organize")
                self.cl[c]["w"]["A"] -= 1
                self.supply["A"] += 1
                self.a_place_sympathy(c, "organizes")
        n = 1 + len(self.bases)
        self.draw("A", n)
        self.log(f"Evening: draws {n}; supporters {len(self.supporters)}", "A")
        self.discard_down("A")

    # ------------------------------------------------------------------ Vagabond (9)
    def v_ready(self, t):
        return [i for i in self.vitems if i["t"] == t and i["up"] and not i["dmg"]]

    def v_exhaust(self, t):
        it = self.v_ready(t)
        if not it:
            raise IllegalAction(f"no ready {t}")
        it[0]["up"] = False
        return it[0]

    def v_track(self, t):
        return min(3, len(self.v_ready(t)))     # face-up items on their track (max 3)

    def v_satchel(self):
        """Items in the Satchel or Damaged box: everything except face-up tea/coins/bags on their tracks."""
        on_track, out = Counter(), []
        for i in self.vitems:
            if i["t"] in D.TRACK_ITEMS and i["up"] and not i["dmg"] and on_track[i["t"]] < 3:
                on_track[i["t"]] += 1
            else:
                out.append(i)
        return out

    def vag_damage(self, n, why):
        done = 0
        for _ in range(n):
            ok = [i for i in self.vitems if not i["dmg"]]
            if not ok:
                break                            # 9.2.7 remaining hits ignored
            it = self.bots["V"].damage_item(self, ok)
            it["dmg"] = True
            done += 1
        self.log(f"{done} item{'s' * (done != 1)} damaged ({why}); undamaged items "
                 f"{sum(1 for i in self.vitems if not i['dmg'])}", "V")

    def _vag_removed(self, f, warrior, battle):
        """Relationships after the Vagabond removes a piece of f (9.2.9.III)."""
        if f not in self.rel:
            return
        if warrior and self.rel[f] != "H":
            self.rel[f] = "H"
            self.log(f"{D.NAME[f]} is now Hostile", "V")
            self.stats["hostile"] += 1
            return
        if battle and self.rel[f] == "H" and self.turn_of == "V":
            self.score("V", 1, f"Infamy ({D.NAME[f]})")

    def v_move_cost(self, dst):
        hostile = any(self.rel.get(f) == "H" and self.cl[dst]["w"][f] for f in self.factions if f != "V")
        return 2 if hostile else 1

    def v_slip_options(self):
        if isinstance(self.vag, int):
            return list(D.ADJ[self.vag]) + [f for f, ring in D.FORESTS.items() if self.vag in ring]
        return list(D.FORESTS[self.vag]) + list(D.FOREST_ADJ[self.vag])

    def v_move_options(self):
        src = D.FORESTS[self.vag] if isinstance(self.vag, str) else D.ADJ[self.vag]
        return [c for c in src if len(self.v_ready("boot")) >= self.v_move_cost(c)]

    def v_set_pos(self, dst, how):
        self.vag = dst
        self.log(f"{how} to {self.cname(dst) if isinstance(dst, int) else 'forest ' + dst}", "V")

    def turn_V(self):
        bot = self.bots["V"]
        n = 3 + 2 * self.v_track("tea")         # 9.4.1 Refresh (tea counted before flipping)
        down = [i for i in self.vitems if not i["up"]]
        for it in bot.refresh_order(self, down)[:n]:
            it["up"] = True
        dst = bot.slip(self)                    # 9.4.2
        if dst is not None:
            if dst not in self.v_slip_options():
                raise IllegalAction("slip")
            self.v_set_pos(dst, "slips")
        self.aids = Counter()
        self.persistent_daylight("V")
        self.daylight_common("V")
        hideout = False
        while True:
            act = bot.vagabond_action(self)
            if not act:
                break
            self.stats["actions_V"] += 1
            if getattr(self, "v_" + act[0])(*act[1:]) == "hideout":
                hideout = True
                break
        self.persistent_evening("V")
        self.v_rest()
        n = 1 + self.v_track("coins")
        self.draw("V", n)
        self.log(f"Evening: draws {n}", "V")
        self.discard_down("V")
        while len(self.v_satchel()) > 6 + 2 * self.v_track("bag"):   # 9.6.4: Satchel + Damaged box only
            it = bot.drop_item(self, self.v_satchel())
            self.vitems.remove(it)
            self.log(f"over item limit: {it['t']} removed from the game", "V")

    def v_rest(self):
        if isinstance(self.vag, str):           # 9.6.1 Rest: only damaged items are repaired and flipped up
            for it in self.vitems:
                if it["dmg"]:
                    it["dmg"], it["up"] = False, True
            self.log("rests in the forest: damaged items repaired", "V")

    def v_move(self, dst):
        if not isinstance(dst, int) or dst not in self.v_move_options():
            raise IllegalAction("vagabond move")
        for _ in range(self.v_move_cost(dst)):
            self.v_exhaust("boot")
        self.v_set_pos(dst, "moves")

    def v_battle(self, d):
        self.v_exhaust("sword")
        self.battle("V", self.vag, d)

    def v_explore(self):
        c = self.vag
        if not isinstance(c, int) or not self.ruin_items.get(c) or not self.v_ready("torch"):
            raise IllegalAction("explore")
        self.v_exhaust("torch")
        t = self.ruin_items[c].pop()
        self.vitems.append(dict(t=t, up=True, dmg=False))
        self.cl[c]["b"].remove(("ruin", "ruin"))
        self.log(f"explores the ruin in {self.cname(c)}: finds a {t}", "V")
        self.stats["explored"] += 1
        self.score("V", 1, "explore")

    def v_aid_options(self):
        if not isinstance(self.vag, int) or not any(i["up"] and not i["dmg"] for i in self.vitems):
            return []
        cards = self.cards_matching("V", self.suit(self.vag))
        if not cards:
            return []
        return [f for f in self.factions if f != "V" and self.has_pieces(self.vag, f)]

    def v_aid(self, f, card, take=None):
        if f not in self.v_aid_options() or card not in self.cards_matching("V", self.suit(self.vag)):
            raise IllegalAction("aid")
        ready = [i for i in self.vitems if i["up"] and not i["dmg"]]
        self.bots["V"].aid_item(self, ready)["up"] = False
        self.hands["V"].remove(card)
        self.hands[f].append(card)
        self.stats["aids"] += 1
        got = ""
        if take and take in self.crafted[f]:
            self.crafted[f].remove(take)
            self.vitems.append(dict(t=take, up=True, dmg=False))
            got = f", takes their {take}"
        self.log(f"aids {D.NAME[f]} with a {card['suit']} card{got}", "V")
        r = self.rel[f]
        if r == "H":
            return
        if r == 3:
            self.score("V", D.V_ALLIED_AID_VP, f"aided Allied {D.NAME[f]}")
            return
        self.aids[f] += 1
        if self.aids[f] >= D.V_REL_COST[r]:
            self.aids[f] = 0
            self.rel[f] = r + 1
            self.log(f"relationship with {D.NAME[f]} improves to {'Allied' if r + 1 == 3 else r + 1}", "V")
            self.score("V", D.V_REL_VP[r], f"relationship {D.NAME[f]}")

    def v_quest_options(self):
        if not isinstance(self.vag, int):
            return []
        s = self.suit(self.vag)
        out = []
        for q in self.quests:
            need = Counter(q[2])
            if q[1] == s and all(len(self.v_ready(t)) >= k for t, k in need.items()):
                out.append(q)
        return out

    def v_quest(self, q, reward):
        if q not in self.v_quest_options():
            raise IllegalAction("quest")
        for t in q[2]:
            self.v_exhaust(t)
        self.quests.remove(q)
        self.done_quests.append(q[1])
        if self.quest_deck:
            self.quests.append(self.quest_deck.pop())
        self.stats["quests"] += 1
        self.log(f"completes quest {q[0]} ({q[1]})", "V")
        if reward == "vp":
            self.score("V", self.done_quests.count(q[1]), f"quest {q[0]}")
        else:
            self.draw("V", 2)
            self.log("draws 2 for the quest", "V")

    def v_strike(self, f):
        c = self.vag
        if not isinstance(c, int) or not self.has_pieces(c, f) or f == "V":
            raise IllegalAction("strike")
        self.v_exhaust("crossbow")
        self.stats["strikes"] += 1
        if self.cl[c]["w"][f]:
            self.log(f"strikes a {D.NAME[f]} warrior in {self.cname(c)}", "V")
            self.remove_warriors(c, f, 1, by="V")
        else:
            opts = self.removable(c, f)
            p = self.bots["V"].strike_piece(self, opts)
            assert p in opts, "strike piece"
            self.log(f"strikes the {D.NAME[f]} {p} in {self.cname(c)}", "V")
            self.remove_piece(c, f, p, by="V")

    def v_repair(self):
        dmg = [i for i in self.vitems if i["dmg"]]
        if not dmg:
            raise IllegalAction("repair")
        self.v_exhaust("hammer")
        it = self.bots["V"].repair_choice(self, dmg)
        it["dmg"] = False
        self.log(f"repairs a {it['t']}", "V")

    def v_craft(self, card):
        self.craft("V", card)

    def v_special(self, target=None):
        c = self.vag
        if not isinstance(c, int) and self.char != "Ranger":
            raise IllegalAction("special")
        self.v_exhaust("torch")
        self.stats["special_" + self.char] += 1
        if self.char == "Thief":                # V.1.2 Steal
            if not self.has_pieces(c, target) or not self.hands[target]:
                raise IllegalAction("steal")
            card = self.rng.choice(self.hands[target])
            self.hands[target].remove(card)
            self.hands["V"].append(card)
            self.log(f"steals a random card from {D.NAME[target]}", "V")
        elif self.char == "Tinker":             # V.2.2 Day Labor
            opts = [x for x in self.discard if matches(x["suit"], self.suit(c))]
            if not opts:
                raise IllegalAction("day labor")
            card = self.bots["V"].day_labor(self, opts)
            self.discard.remove(card)
            self.hands["V"].append(card)
            self.log(f"Day Labor: takes {card['name']} from the discard pile", "V")
        else:                                   # V.3.2 Hideout
            for it in sorted((i for i in self.vitems if i["dmg"]), key=lambda i: i["t"])[:3]:
                it["dmg"] = False
            self.log("Hideout: repairs three items and ends Daylight", "V")
            return "hideout"
    # SKIP: Allied warriors moving or fighting with the Vagabond (9.2.9.IIb-d) are not used by the bots.
