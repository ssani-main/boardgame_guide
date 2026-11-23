"""Self-check: source numbers, rule scenarios and invariants over many full games.

    python test_rules.py
"""
import io
import sys
from collections import Counter

import data as D
import engine


class Dice:
    """Stand-in for the game's RNG in battle scenarios: returns the queued die faces."""
    def __init__(self, faces, rng):
        self.faces, self.rng = list(faces), rng

    def choice(self, seq):
        return self.faces.pop(0) if seq is D.DIE and self.faces else self.rng.choice(seq)

    def __getattr__(self, name):
        return getattr(self.rng, name)


def quiet(factions="MEAV", seed=1):
    return engine.Game(factions=factions, seed=seed, verbose=False)


def empty_map(g):
    """Clear every piece from the map (supplies refilled) for hand-built scenarios."""
    for c, x in g.cl.items():
        for f in list(x["w"]):
            g.supply[f] += x["w"][f]
        x["w"] = Counter()
        x["b"] = [b for b in x["b"] if b[0] == "ruin"]
        x["wood"], x["keep"], x["sym"] = 0, False, False
    if "M" in g.factions:
        g.m_on_map, g.keep, g.wood_supply = Counter(), None, D.M_WOOD
    if "A" in g.factions:
        g.sym_placed, g.bases = 0, {}


def card(g, name, suit=None):
    for pile in [g.deck, g.discard] + list(g.hands.values()) + [getattr(g, "supporters", [])]:
        for c in pile:
            if c["name"] == name and (suit is None or c["suit"] == suit):
                pile.remove(c)
                return c
    raise KeyError(name)


def total_cards(g):
    n = len(g.deck) + len(g.discard) + len(g.avail_dom) + sum(len(h) for h in g.hands.values())
    n += sum(len(p) for p in g.play_area.values()) + sum(1 for d in g.dominance.values() if d)
    if "E" in g.factions:
        n += sum(1 for col in D.DECREE_COLS for c in g.decree[col] if c["kind"] != "vizier")
    if "A" in g.factions:
        n += len(g.supporters)
    return n


# --------------------------------------------------------------------------- data
def test_data():
    deck = D.build_deck()
    suits = Counter(c["suit"] for c in deck)
    assert suits == {"bird": 14, "fox": 14, "mouse": 13, "rabbit": 13}
    assert sum(c["kind"] == "ambush" for c in deck) == 5 and sum(c["kind"] == "dominance" for c in deck) == 4
    assert sum(c["kind"] == "item" for c in deck) == 20
    assert sum(D.ITEM_SUPPLY.values()) == 12
    assert Counter(c["suit"] for c in D.CLEARINGS.values()) == {"fox": 4, "rabbit": 4, "mouse": 4}
    assert all(b in D.ADJ[a] and a in D.ADJ[b] for a, b in D.PATHS)
    assert len(D.FORESTS) == 7 and all(D.FOREST_ADJ[f] for f in D.FORESTS)
    assert [D.ROOST_VP[k] for k in (1, 2, 3)] == [0, 1, 2]          # Walking Through Root
    assert D.M_COST[1] == 1 and D.M_VP["workshop"][1] == 2           # Walking Through Root p. 7
    assert D.V_REL_COST == [1, 2, 3] and D.V_REL_VP == [1, 2, 2]     # Learning to Play p. 19
    assert sum(D.REACH[f] for f in "ME") == 17 and sum(D.REACH[f] for f in "EAV") < 18


# --------------------------------------------------------------------------- setup
def test_setup():
    for fs in ("ME", "MEV", "MEAV"):
        g = quiet(fs)
        assert all(len(g.hands[f]) == 3 for f in g.factions)
        on_map = sum(g.cl[c]["w"]["M"] for c in D.CLEARINGS)
        assert on_map == 11 and g.cl[D.OPPOSITE[g.keep]]["w"]["M"] == 0
        assert sum(g.m_on_map.values()) == 3 and g.keep in D.CORNERS
        e = g.start_corner["E"]
        assert e == D.OPPOSITE[g.keep] and g.cl[e]["w"]["E"] == 6 and g.roosts() == [e]
        assert sum(g.decree[col] != [] for col in D.DECREE_COLS) == 2
        assert total_cards(g) == (50 if fs == "ME" else 54)
        if "V" in g.factions:
            assert len(g.vitems) == 4 and len(g.quests) == 3 and isinstance(g.vag, str)
            assert sorted(i for v in g.ruin_items.values() for i in v) == sorted(D.RUIN_ITEMS)
        if "A" in g.factions:
            assert len(g.supporters) == 3


# --------------------------------------------------------------------------- rule, movement
def test_rule_and_move():
    g = quiet("MEA")
    empty_map(g)
    g.cl[12]["w"].update({"M": 2, "A": 2})
    assert g.ruler(12) is None                                       # tie: nobody rules (2.5)
    g.cl[12]["w"]["E"] = 1
    g.cl[12]["w"]["A"] = 1
    g.cl[12]["w"]["M"] = 1
    assert g.ruler(12) == "E"                                         # Lords of the Forest (7.2.2)
    g.cl[9]["w"]["M"] = 1
    assert g.can_move("M", 12, 9)                                     # rules the destination
    assert g.can_move("M", 9, 12)                                     # rules the origin
    assert 10 in D.ADJ[12] and not g.can_move("M", 12, 10)            # adjacent, rules neither


# --------------------------------------------------------------------------- battle
def test_battle_basics():
    g = quiet("ME")
    g.leader = "Builder"                                              # no Commander / Despot bonus
    empty_map(g)
    g.cl[2]["w"]["E"] = 2
    g.cl[2]["b"] += [("M", "workshop"), ("M", "sawmill")]
    g.cl[2]["wood"] = 2
    g.wood_supply -= 2
    g.m_on_map.update({"workshop": 1, "sawmill": 1})
    g.hands = {"M": [], "E": []}
    g.rng = Dice([3, 1], g.rng)
    vp = g.vp["E"]
    g.battle("E", 2, "M")
    # roll 3/1: 3 capped at 2 warriors, +1 defenseless = exactly 3 hits on 4 pieces; the owner keeps the workshop
    assert g.buildings(2, "M") == ["workshop"] and g.cl[2]["wood"] == 0 and g.vp["E"] == vp + 3
    assert g.cl[2]["w"]["E"] == 2                                     # defender had no warriors: 0 hits back


def test_warriors_first_and_guerrilla():
    g = quiet("EA")
    g.leader = "Builder"
    empty_map(g)
    g.cl[11]["w"].update({"E": 3, "A": 1})
    g.cl[11]["sym"] = True
    g.sym_placed = 1
    g.hands = {"E": [], "A": []}
    g.rng = Dice([3, 1], g.rng)
    g.battle("E", 11, "A")
    # Guerrilla War: attacker gets the lower roll (1), defender the higher (3, capped at 1 warrior)
    assert g.cl[11]["w"]["A"] == 0 and g.cl[11]["sym"]               # 1 hit: the warrior, token stays
    assert g.cl[11]["w"]["E"] == 2


def test_ambush_and_foil():
    g = quiet("ME")
    empty_map(g)
    g.cl[2]["w"].update({"E": 2, "M": 1})
    g.hands = {"M": [card(g, "Ambush!", "mouse")], "E": []}
    g.battle("E", 2, "M")
    assert g.cl[2]["w"]["E"] == 0                                     # 2 immediate hits end the battle
    g.cl[2]["w"]["E"] = 2
    g.hands = {"M": [card(g, "Ambush!", "bird")], "E": [card(g, "Ambush!", "bird")]}
    g.rng = Dice([0, 0], g.rng)
    g.battle("E", 2, "M")
    assert g.cl[2]["w"]["E"] == 2 and not g.hands["M"] and not g.hands["E"]   # foiled


# --------------------------------------------------------------------------- crafting
def test_crafting():
    g = quiet("ME")
    empty_map(g)
    g.cl[2]["b"].append(("E", "roost"))
    g.cl[5]["b"].append(("E", "roost"))
    g.leader = "Commander"                                            # not the Builder
    sword = card(g, "Sword")                                          # costs fox, fox
    steel = card(g, "Foxfolk Steel")
    g.hands["E"] = [sword]
    assert not g.can_craft("E", sword)                                # no fox roosts
    g.cl[6]["b"].append(("E", "roost"))
    g.cl[1]["b"].append(("E", "roost"))
    assert g.can_craft("E", sword)
    vp = g.vp["E"]
    g.craft("E", sword)
    assert g.vp["E"] == vp + 1 and g.items["sword"] == 1             # Disdain for Trade: 1 VP, not 2
    g.items["sword"] = 0
    g.hands["E"].append(steel)
    g.used_craft["E"] = Counter()
    assert not g.can_craft("E", steel)                                # item supply empty (4.1.2)


# --------------------------------------------------------------------------- dominance
def test_dominance():
    g = quiet("MEAV")
    dom = card(g, "Dominance", "fox")
    g.hands["M"].append(dom)
    g.vp["M"] = 9
    assert not g.can_activate_dominance("M", dom)
    g.vp["M"] = 10
    g.activate_dominance("M", dom)
    g.score("M", 5, "test")
    assert g.vp["M"] == 10                                            # no more points
    empty_map(g)
    for c in (1, 6, 8):
        g.cl[c]["w"]["M"] = 1
    try:
        g.take_turn("M")
        assert False, "should have won"
    except engine.GameOver:
        assert g.winners == ["M"] and g.reason == "dominance"


def test_coalition():
    g = quiet("MEAV")
    dom = card(g, "Dominance", "bird")
    g.hands["V"].append(dom)
    g.vp.update({"M": 12, "E": 3, "A": 7, "V": 5})
    g.activate_dominance("V", dom)
    assert g.coalition == "E"
    empty_map(g)
    g.vag = 12
    g.cl[12]["w"]["E"] = 2
    assert not g.can_battle("V", 12, "E") and not g.can_battle("E", 12, "V")   # not enemies (G.8)
    try:
        g.score("E", 30, "test")
        assert False, "should have won"
    except engine.GameOver:
        assert sorted(g.winners) == ["E", "V"]


def test_birdsong_wood():
    g = quiet("ME")
    empty_map(g)
    g.cl[5]["b"] += [("M", "sawmill"), ("M", "workshop")]
    g.cl[2]["b"] += [("M", "sawmill"), ("M", "sawmill")]
    g.m_birdsong()
    assert g.cl[5]["wood"] == 1 and g.cl[2]["wood"] == 2                # one wood per sawmill (6.4)


def test_rest_repairs_only_damaged():
    g = quiet("MEV")
    g.vag = "F1"
    g.vitems = [dict(t="coins", up=False, dmg=False), dict(t="boot", up=False, dmg=True)]
    g.v_rest()
    assert g.vitems[0] == dict(t="coins", up=False, dmg=False)        # exhausted stays exhausted (9.6.1)
    assert g.vitems[1] == dict(t="boot", up=True, dmg=False)


def test_field_hospitals_lost_with_keep():
    g = quiet("MA")
    empty_map(g)
    g.keep = 12
    g.cl[12]["keep"] = True
    g.cl[12]["w"]["M"] = 3
    g.cl[12]["sym"] = True
    g.sym_placed = 1
    fox = card(g, "Anvil")
    sup = [card(g, "Foxfolk Steel"), card(g, "Arms Trader")]
    g.hands["M"] = [fox]
    g.supporters = sup
    g.a_revolt(12)
    # keep and warriors go at the same time (1.5.4): no keep left to send them to
    assert g.keep is None and g.cl[12]["w"]["M"] == 0 and g.hands["M"] == [fox]


def test_despot_after_ambush():
    g = quiet("ME")
    g.leader = "Despot"
    empty_map(g)
    g.cl[2]["w"].update({"M": 1, "E": 1})
    g.cl[2]["b"].append(("M", "sawmill"))
    g.m_on_map["sawmill"] = 1
    g.hands = {"M": [], "E": [card(g, "Ambush!", "mouse")]}
    vp = g.vp["E"]
    g.battle("M", 2, "E")
    # the ambush removes the warrior and the sawmill and ends the battle: +1 sawmill, +1 Despot (7.8.4)
    assert g.cl[2]["w"]["M"] == 0 and g.buildings(2, "M") == [] and g.vp["E"] == vp + 2


# --------------------------------------------------------------------------- factions
def test_turmoil():
    g = quiet("ME")
    g.vp["E"] = 5
    g.decree["build"].append(card(g, "Armorers"))                     # a bird card
    g.decree["move"].append(card(g, "Anvil"))
    g.turmoil()
    assert g.vp["E"] == 5 - 3                                         # 2 Viziers + 1 bird
    assert sum(len(v) for v in g.decree.values()) == 2                # only the Viziers stay
    assert all(c["kind"] == "vizier" for col in D.DECREE_COLS for c in g.decree[col])


def test_outrage_and_revolt():
    g = quiet("MA")
    empty_map(g)
    g.cl[12]["sym"] = True
    g.sym_placed = 1
    g.cl[9]["w"]["M"] = 3
    fox = card(g, "Anvil")
    extra = [card(g, "Foxfolk Steel"), card(g, "Arms Trader")]      # fox + bird
    g.hands["M"] = [fox]
    g.supporters = []
    g.move("M", 9, 12, 3)
    assert g.supporters == [fox] and not g.hands["M"]                 # Outrage (8.2.6)
    g.supporters += extra
    g.cl[12]["b"].append(("M", "sawmill"))
    g.m_on_map["sawmill"] = 1
    vp = g.vp["A"]
    g.a_revolt(12)
    assert g.cl[12]["w"]["M"] == 0 and g.buildings(12, "M") == [] and g.vp["A"] == vp + 1
    assert g.bases == {"fox": 12} and g.officers == 1 and g.cl[12]["w"]["A"] == 1


def test_field_hospitals():
    g = quiet("ME")
    empty_map(g)
    g.keep = 1
    g.cl[1]["keep"] = True
    g.cl[11]["w"].update({"M": 3, "E": 5})
    mouse = [card(g, "Mouse-in-a-Sack")]
    g.hands = {"M": mouse, "E": []}
    g.rng = Dice([3, 0], g.rng)
    g.battle("E", 11, "M")
    assert g.cl[11]["w"]["M"] == 0 and g.cl[1]["w"]["M"] == 3 and not g.hands["M"]


def test_vagabond_relationship_and_items():
    g = quiet("MEV")
    empty_map(g)
    g.vag = 5
    g.cl[5]["w"]["M"] = 1
    g.vitems = [dict(t="boot", up=True, dmg=False) for _ in range(6)]
    g.hands["V"] = [card(g, "Bake Sale"), card(g, "Cobbler"), card(g, "Cobbler"), card(g, "Smuggler's Trail"),
                    card(g, "Better Burrow Bank"), card(g, "Command Warren")]
    scores = []
    for _ in range(6):
        g.v_aid("M", g.hands["V"][0])
        scores.append(g.vp["V"])
        g.aids["E"] = 0
    # costs 1, 2, 3 Aids for +1, +2, +2: after aid 1 → 1, aid 3 → 3, aid 6 → 5 (Allied)
    assert scores == [1, 1, 3, 3, 3, 5] and g.rel["M"] == 3
    g.vitems = [dict(t="tea", up=True, dmg=False)] * 3 + [dict(t="boot", up=True, dmg=False) for _ in range(6)]
    assert len(g.v_satchel()) == 6                                    # track items don't count (9.6.4)


def test_infamy():
    g = quiet("MEV")
    empty_map(g)
    g.turn_of = "V"
    g.vag = 9
    g.cl[9]["w"]["M"] = 3
    g.vitems = [dict(t="sword", up=True, dmg=False) for _ in range(3)]
    g.hands = {f: [] for f in g.factions}
    g.rng = Dice([3, 0], g.rng)
    g.v_battle("M")
    # first warrior makes the Marquise Hostile; the other two score Infamy
    assert g.rel["M"] == "H" and g.vp["V"] == 2


# --------------------------------------------------------------------------- full games
def check_invariants(g):
    totals = {"M": D.M_WARRIORS, "E": D.E_WARRIORS, "A": D.A_WARRIORS}
    for f in g.factions:
        if f in totals:
            on_map = sum(g.cl[c]["w"][f] for c in D.CLEARINGS)
            extra = g.officers if f == "A" else 0
            assert on_map + g.supply[f] + extra == totals[f], (f, on_map, g.supply[f])
    for c in D.CLEARINGS:
        assert len(g.cl[c]["b"]) <= D.CLEARINGS[c]["slots"], c
    assert total_cards(g) == (50 if g.n == 2 else 54), total_cards(g)
    assert all(v >= 0 for v in g.vp.values())
    if "E" in g.factions:
        assert len(g.roosts()) <= D.E_ROOSTS
    if "A" in g.factions:
        assert len(g.sympathetic()) == g.sym_placed <= D.A_SYMPATHY
    if "M" in g.factions:
        assert sum(g.cl[c]["wood"] for c in D.CLEARINGS) + g.wood_supply == D.M_WOOD


def test_full_games(n=150):
    ends = Counter()
    for fs in ("ME", "MEV", "MEAV", "MEA", "EAV"):
        for seed in range(1, n // 5 * 2 + 1):
            g = quiet(fs, seed)
            orig = g.take_turn

            def turn(f, g=g, orig=orig):
                orig(f)
                check_invariants(g)
            g.take_turn = turn
            r = g.play()
            check_invariants(g)
            ends[r["reason"]] += 1
            assert r["winners"]
    return ends


def test_determinism():
    a, b = quiet("MEAV", 42), quiet("MEAV", 42)
    a.play()
    b.play()
    assert a.lines == b.lines


TESTS = [test_data, test_setup, test_rule_and_move, test_battle_basics, test_warriors_first_and_guerrilla,
         test_ambush_and_foil, test_crafting, test_dominance, test_coalition, test_turmoil, test_outrage_and_revolt,
         test_field_hospitals, test_vagabond_relationship_and_items, test_infamy, test_birdsong_wood,
         test_rest_repairs_only_damaged, test_field_hospitals_lost_with_keep, test_despot_after_ambush,
         test_determinism]

if __name__ == "__main__":
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    for t in TESTS:
        t()
        print("ok ", t.__name__)
    print("full games:", dict(test_full_games()))
    print("all tests passed")
