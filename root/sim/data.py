"""Static game data for the Root base game (Autumn map, base deck, faction boards).

Comments mark every number:
  REAL  printed in the Law of Root (Oct 2025), Learning to Play, Walking Through Root or on the official cards
  EST   not in any of those sources (faction-board values from the printed boards, dice faces, map paths read
        off the map picture); see ../root-rules.md section 16.
"""

FACTIONS = ("M", "E", "A", "V")                     # setup order A, B, C, D (REAL, 5.1.7)
NAME = {"M": "Marquise", "E": "Eyrie", "A": "Alliance", "V": "Vagabond"}
REACH = {"M": 10, "E": 7, "V": 5, "A": 3}           # REAL 5.2
MIN_REACH = {2: 17, 3: 18, 4: 21}                   # REAL 5.2
# Torch-marked mixes, Learning to Play p. 22 (REAL). Both 3-player rows carry the torch (M+E+V and M+E+A);
# the booklet's own first-game setup (p. 3) uses M+E+A, we use M+E+V so every player count shows a new faction.
DEFAULT_FACTIONS = {2: "ME", 3: "MEV", 4: "MEAV"}
WIN_VP = 30                                         # REAL 3.1

# --- Autumn map -------------------------------------------------------------------------------------------
# Numbering follows the common clearing order: 1-4 corners (1 top-left, 2 top-right, 3 bottom-right,
# 4 bottom-left). Suits, slots, ruins and corners: REAL (read off the setup picture, Walking Through Root p. 3
# and p. 15; 4 clearings per suit, 4 ruins). Paths: EST (read off the same picture; 18 paths).
CLEARINGS = {
    1: dict(suit="fox", slots=1, pos=(115, 120)),
    2: dict(suit="mouse", slots=2, pos=(860, 210)),
    3: dict(suit="rabbit", slots=2, pos=(800, 780)),
    4: dict(suit="rabbit", slots=1, pos=(75, 745)),
    5: dict(suit="rabbit", slots=2, pos=(530, 100)),
    6: dict(suit="fox", slots=2, pos=(900, 500)),
    7: dict(suit="mouse", slots=2, pos=(590, 730)),
    8: dict(suit="fox", slots=2, pos=(295, 810)),
    9: dict(suit="mouse", slots=2, pos=(110, 400)),
    10: dict(suit="rabbit", slots=2, pos=(430, 240)),
    11: dict(suit="mouse", slots=3, pos=(660, 420)),
    12: dict(suit="fox", slots=2, pos=(260, 500)),
}
PATHS = [(1, 5), (1, 9), (1, 10), (2, 5), (2, 6), (2, 10), (3, 6), (3, 7), (3, 11), (4, 8), (4, 9), (4, 12),
         (6, 11), (7, 8), (7, 12), (9, 12), (10, 12), (11, 12)]
ADJ = {c: sorted({b for a, b in PATHS if a == c} | {a for a, b in PATHS if b == c}) for c in CLEARINGS}
CORNERS = (1, 2, 3, 4)
OPPOSITE = {1: 3, 3: 1, 2: 4, 4: 2}
RUINS = (6, 10, 11, 12)                             # REAL (4 "R" slots)
# Forests = the 7 faces of the path graph, listed as their ring of clearings (EST, follows from PATHS).
FORESTS = {
    "F1": (1, 5, 2, 10), "F2": (1, 10, 12, 9), "F3": (10, 2, 6, 11, 12), "F4": (9, 12, 4),
    "F5": (12, 11, 3, 7), "F6": (11, 6, 3), "F7": (4, 12, 7, 8),
}


def _ring_edges(ring):
    return {frozenset((ring[i], ring[(i + 1) % len(ring)])) for i in range(len(ring))}


# Forests are adjacent when separated by one path (REAL rule 2.4.1); clearings touching a forest are adjacent to it.
FOREST_ADJ = {f: sorted(g for g in FORESTS if g != f and _ring_edges(FORESTS[f]) & _ring_edges(FORESTS[g]))
              for f in FORESTS}

# --- Items -------------------------------------------------------------------------------------------------
ITEM_SUPPLY = {"boot": 2, "bag": 2, "crossbow": 1, "hammer": 1, "sword": 2, "tea": 2, "coins": 2}   # REAL 5.1.5
RUIN_ITEMS = ("bag", "boot", "hammer", "sword")     # REAL 9.3.4
TRACK_ITEMS = ("tea", "coins", "bag")               # REAL 9.2.5.I

# --- Faction boards ----------------------------------------------------------------------------------------
# Marquise: index = buildings of that type already on the map (the first is placed in setup).
M_COST = [0, 1, 2, 3, 3, 4]                         # EST (2nd = 1: REAL, Walking Through p. 7)
M_VP = {"sawmill": [0, 1, 2, 3, 4, 5],              # EST
        "workshop": [0, 2, 2, 3, 4, 5],             # EST (2nd = 2: REAL, Walking Through p. 7)
        "recruiter": [0, 1, 2, 3, 3, 4]}            # EST
M_RECRUITER_DRAW = (3, 5)                           # EST: draw bonus uncovered by the 3rd and 5th recruiter
M_WARRIORS, M_WOOD = 25, 8                          # REAL 6.3.1
M_BUILDINGS = 6                                     # REAL (6 of each)

ROOST_VP = [0, 0, 1, 2, 3, 4, 4, 5]                 # index = roosts on map; 2 -> 1, 3 -> 2 REAL (Walking Through)
ROOST_DRAW = (3, 6)                                 # 3rd roost: REAL (Walking Through p. 10); 6th: EST
E_WARRIORS, E_ROOSTS = 20, 7                        # REAL 7.3.1, C.1.2
LEADERS = {                                         # REAL 7.8: Loyal Vizier columns and ability
    "Builder": ("recruit", "move"),
    "Charismatic": ("recruit", "battle"),
    "Commander": ("move", "battle"),
    "Despot": ("move", "build"),
}
DECREE_COLS = ("recruit", "move", "battle", "build")

SYM_COST = [1, 1, 1, 2, 2, 2, 3, 3, 3, 3]           # EST (4th = 2: REAL, Learning to Play p. 15)
SYM_VP = [0, 1, 1, 1, 2, 2, 3, 4, 4, 4]             # EST (2nd = 1: REAL; picture p. 9 of Walking Through agrees)
A_WARRIORS, A_SYMPATHY = 10, 10                     # REAL 8.3.1, 8.2.5
A_SUPPORTER_CAP = 5                                 # REAL 8.2.3.I
# Each base on the map uncovers one draw bonus (REAL in spirit: Walking Through p. 15 "a base lets you draw another card").

V_REL_COST = [1, 2, 3]                              # REAL (Learning to Play p. 19 board picture)
V_REL_VP = [1, 2, 2]                                # REAL (same picture)
V_ALLIED_AID_VP = 2                                 # REAL 9.2.9.IIa
CHARACTERS = {                                      # REAL Appendix V
    "Thief": ("boot", "torch", "tea", "sword"),
    "Tinker": ("boot", "torch", "bag", "hammer"),
    "Ranger": ("boot", "torch", "crossbow", "sword"),
}
QUESTS = [                                          # REAL (quest card images)
    ("Errand", "fox", ("tea", "boot")), ("Fundraising", "fox", ("tea", "coins")),
    ("Give a Speech", "fox", ("torch", "tea")), ("Logistics Help", "fox", ("boot", "bag")),
    ("Repair a Shed", "fox", ("torch", "hammer")), ("Escort", "mouse", ("boot", "boot")),
    ("Expel Bandits", "mouse", ("sword", "sword")), ("Fend off a Bear", "mouse", ("torch", "crossbow")),
    ("Guard Duty", "mouse", ("torch", "sword")), ("Logistics Help", "mouse", ("boot", "bag")),
    ("Errand", "rabbit", ("tea", "boot")), ("Expel Bandits", "rabbit", ("sword", "sword")),
    ("Fend off a Bear", "rabbit", ("torch", "crossbow")), ("Give a Speech", "rabbit", ("torch", "tea")),
    ("Guard Duty", "rabbit", ("torch", "sword")),
]

# Battle dice: twelve-sided, faces 0-3. EST: each value on three faces.
DIE = (0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3)

HAND_LIMIT = 5                                      # REAL
START_HAND = 3                                      # REAL 5.1.3

# --- Base deck (54 cards) -------------------------------------------------------------------------------------
# (name, suit, copies, kind, cost, item, vp). kind: ambush, dominance, item, persistent, favor.
# Names, suits, costs, items, points: REAL (card images). Copies: EST (standard composition, see cards/deck.md).
F, R, Mo, B, ANY = "fox", "rabbit", "mouse", "bird", "any"
DECK = [
    ("Ambush!", B, 2, "ambush", (), None, 0), ("Dominance", B, 1, "dominance", (), None, 0),
    ("Armorers", B, 2, "persistent", (F,), None, 0), ("Arms Trader", B, 1, "item", (F, F), "sword", 2),
    ("Birdy Bindle", B, 1, "item", (Mo,), "bag", 1), ("Brutal Tactics", B, 2, "persistent", (F, F), None, 0),
    ("Crossbow", B, 1, "item", (F,), "crossbow", 1), ("Royal Claim", B, 1, "persistent", (ANY,) * 4, None, 0),
    ("Sappers", B, 2, "persistent", (Mo,), None, 0), ("Woodland Runners", B, 1, "item", (R,), "boot", 1),

    ("Ambush!", F, 1, "ambush", (), None, 0), ("Dominance", F, 1, "dominance", (), None, 0),
    ("Anvil", F, 1, "item", (F,), "hammer", 2), ("Favor of the Foxes", F, 1, "favor", (F, F, F), None, 0),
    ("Foxfolk Steel", F, 1, "item", (F, F), "sword", 2), ("Gently Used Knapsack", F, 1, "item", (Mo,), "bag", 1),
    ("Protection Racket", F, 1, "item", (R, R), "coins", 3), ("Root Tea", F, 1, "item", (Mo,), "tea", 2),
    ("Stand and Deliver!", F, 2, "persistent", (Mo, Mo, Mo), None, 0),
    ("Tax Collector", F, 3, "persistent", (R, F, Mo), None, 0), ("Travel Gear", F, 1, "item", (R,), "boot", 1),

    ("Ambush!", Mo, 1, "ambush", (), None, 0), ("Dominance", Mo, 1, "dominance", (), None, 0),
    ("Codebreakers", Mo, 2, "persistent", (Mo,), None, 0), ("Crossbow", Mo, 1, "item", (F,), "crossbow", 1),
    ("Favor of the Mice", Mo, 1, "favor", (Mo, Mo, Mo), None, 0), ("Investments", Mo, 1, "item", (R, R), "coins", 3),
    ("Mouse-in-a-Sack", Mo, 1, "item", (Mo,), "bag", 1), ("Root Tea", Mo, 1, "item", (Mo,), "tea", 2),
    ("Scouting Party", Mo, 2, "persistent", (Mo, Mo), None, 0), ("Sword", Mo, 1, "item", (F, F), "sword", 2),
    ("Travel Gear", Mo, 1, "item", (R,), "boot", 1),

    ("Ambush!", R, 1, "ambush", (), None, 0), ("Dominance", R, 1, "dominance", (), None, 0),
    ("A Visit to Friends", R, 1, "item", (R,), "boot", 1), ("Bake Sale", R, 1, "item", (R, R), "coins", 3),
    ("Better Burrow Bank", R, 2, "persistent", (R, R), None, 0), ("Cobbler", R, 2, "persistent", (R, R), None, 0),
    ("Command Warren", R, 2, "persistent", (R, R), None, 0),
    ("Favor of the Rabbits", R, 1, "favor", (R, R, R), None, 0), ("Root Tea", R, 1, "item", (Mo,), "tea", 2),
    ("Smuggler's Trail", R, 1, "item", (Mo,), "bag", 1),
]


def build_deck():
    """Return the 54 cards as dicts with a unique id."""
    cards, n = [], 0
    for name, suit, copies, kind, cost, item, vp in DECK:
        for _ in range(copies):
            n += 1
            cards.append(dict(id=n, name=name, suit=suit, kind=kind, cost=cost, item=item, vp=vp))
    return cards


assert len(build_deck()) == 54
assert sum(1 for c in CLEARINGS.values() if c["suit"] == "fox") == 4
assert sum(c["slots"] for c in CLEARINGS.values()) == 23
assert len(PATHS) == 18 and len(FORESTS) == len(PATHS) - len(CLEARINGS) + 1   # Euler: inner faces = E - V + 1
