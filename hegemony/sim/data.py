"""Game data for the Hegemony rules simulator.

REAL  = read from the official rulebook v1.1/v1.2 text or its pictures (setup photo, player boards).
EST   = estimate: the rulebook does not print it (full company decks, export / business-deal /
        immigration decks). Estimates follow the patterns of the real cards next to them.
"""

IND = ("food", "lux", "health", "edu", "media")  # industries; media produces Influence ("infl")
PRODUCT = {"food": "food", "lux": "lux", "health": "health", "edu": "edu", "media": "infl"}

# ---------------------------------------------------------------- tracks (REAL)
# workers on the Population track -> Population value (Working and Middle board)
def population(workers):
    for limit, pop in ((11, 3), (14, 4), (17, 5), (20, 6), (23, 7), (26, 8), (29, 9)):
        if workers <= limit:
            return pop
    return 10

WC_PROSPERITY = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]          # VP shown on each space
MC_PROSPERITY = [0, 1, 2, 3, 4, 5, 5, 6, 6, 7, 7]
WEALTH = [10, 25, 50, 75, 100, 125, 150, 175, 200, 250, 300, 350, 400, 450, 500]  # space i -> i+1 VP

def wealth_space(capital):
    """Index of the highest Wealth space reached (0-based), -1 if below 10."""
    s = -1
    for i, t in enumerate(WEALTH):
        if capital >= t:
            s = i
    return s

def legit_influence(legit):                     # Influence printed above the State's tracks
    return 0 if legit <= 1 else min(5, legit // 2)

# ---------------------------------------------------------------- tax tables (REAL)
INCOME_TAX = {"A": {"A": 7, "B": 6, "C": 5}, "B": {"A": 4, "B": 4, "C": 4}, "C": {"A": 1, "B": 2, "C": 3}}  # [labor][taxation]
CORP_BRACKETS = [(5, 1, 2, 2), (10, 5, 5, 4), (25, 12, 10, 7), (50, 24, 15, 10),
                 (100, 40, 30, 20), (200, 100, 70, 40), (300, 160, 120, 60)]  # (min revenue, A, B, C)

def corporate_tax(revenue, taxation):
    tax = 0
    col = "ABC".index(taxation) + 1
    for row in CORP_BRACKETS:
        if revenue >= row[0]:
            tax = row[col]
    return tax

def tax_multiplier(p3, p4, p5):
    base = {"A": 3, "B": 2, "C": 1}[p3]
    factor = {"A": 2, "B": 1, "C": 0}[p3]
    mod = {"A": 2, "B": 1, "C": 0}
    return base + factor * (mod[p4] + mod[p5])

# ---------------------------------------------------------------- policies (REAL)
START_POLICIES = {1: "C", 2: "B", 3: "A", 4: "B", 5: "C", 6: "B", 7: "B"}
IMF_POLICIES = {1: "C", 2: "C", 3: "A", 4: "B", 5: "C", 6: "B"}
PUBLIC_OPEN = {"A": 9, "B": 6, "C": 3}
IMF_LOANS = {"A": 2, "B": 2, "C": 1}
MIN_WAGE = {"A": 3, "B": 2, "C": 1}
WELFARE_PRICE = {"A": 0, "B": 5, "C": 10}
IMPORT_BASE = {"food": 10, "lux": 6}
TARIFF = {"A": {"food": 10, "lux": 6}, "B": {"food": 5, "lux": 3}, "C": {"food": 0, "lux": 0}}
DEALS_DRAWN = {"A": 0, "B": 1, "C": 2}
IMMIGRANTS = {"A": 0, "B": 1, "C": 2}
STATE_INFL_PRICE = 10                     # printed on the Public Services area
PRICE_SLOTS = {"food": (9, 12, 15), "lux": (5, 8, 10), "health": (5, 8, 10), "edu": (5, 8, 10)}  # REAL (boards)

# end-game policy scoring (REAL)
POLICY_VP_WC_CC = [0, 1, 4, 8, 12, 18]
POLICY_VP_MC = [0, 1, 3, 6, 10, 15]

# ---------------------------------------------------------------- companies
# slots: list of skill letters, None = unskilled slot. wages = (L1, L2, L3).
def co(name, ind, cost, slots, out, wages, mach=0, auto=False):
    return dict(name=name, ind=ind, cost=cost, slots=slots, out=out, wages=wages, mach=mach, auto=auto)

# REAL: the four starting Capitalist companies (setup photo, rulebook p.9)
CC_START = [
    co("Clinic", "health", 16, ["health", None, None], 6, (10, 20, 30), mach=2),
    co("College", "edu", 10, ["edu", None], 6, (10, 20, 30), mach=2),
    co("Shopping Mall", "lux", 20, ["lux", None], 6, (15, 20, 25), mach=3),   # cost hidden in photo: EST
    co("Supermarket", "food", 18, ["food", None], 4, (15, 20, 25), mach=1),
]
# EST: the 28-card Capitalist deck, built from the patterns above
CC_DECK = [
    co("Farm", "food", 20, ["food", None], 4, (15, 20, 25), 1),
    co("Big Farm", "food", 30, ["food", None, None], 6, (20, 25, 35), 2),
    co("Fishery", "food", 22, ["food", None], 4, (15, 20, 25), 1),
    co("Grocery Chain", "food", 28, ["food", None, None], 6, (20, 25, 35), 2),
    co("Food Factory (automated)", "food", 45, [], 3, (0, 0, 0), auto=True),
    co("Bakery", "food", 16, ["food", None], 3, (15, 20, 25), 1),
    co("Electronics Store", "lux", 22, ["lux", None], 6, (15, 20, 25), 3),
    co("Car Dealer", "lux", 30, ["lux", None, None], 9, (20, 25, 35), 3),
    co("Fashion Outlet", "lux", 20, ["lux", None], 5, (15, 20, 25), 2),
    co("Luxury Factory (automated)", "lux", 45, [], 4, (0, 0, 0), auto=True),
    co("Jewellery", "lux", 26, ["lux", None], 6, (15, 20, 25), 3),
    co("Department Store", "lux", 32, ["lux", None, None], 9, (20, 25, 35), 3),
    co("Hospital", "health", 25, ["health", None, None], 6, (10, 20, 30), 2),
    co("Medical Center", "health", 20, ["health", None], 4, (10, 20, 30), 2),
    co("Pharmacy", "health", 14, ["health", None], 3, (10, 15, 25), 1),
    co("Private Hospital", "health", 30, ["health", "health", None], 8, (15, 25, 35), 2),
    co("Laboratory", "health", 24, ["health", None, None], 6, (10, 20, 30), 2),
    co("Institute of Technology", "edu", 20, ["edu", None, None], 7, (10, 20, 30), 2),  # name REAL (rulebook example)
    co("Private School", "edu", 16, ["edu", None], 5, (10, 20, 30), 2),
    co("Language School", "edu", 12, ["edu", None], 4, (10, 15, 25), 1),
    co("University", "edu", 28, ["edu", "edu", None], 8, (15, 25, 35), 2),
    co("Training Center", "edu", 18, ["edu", None], 5, (10, 20, 30), 2),
    co("TV Station", "media", 25, ["media", None, None], 4, (15, 25, 35), 1),
    co("Newspaper", "media", 15, ["media", None], 2, (10, 20, 30), 1),
    co("Radio", "media", 18, ["media", None], 3, (10, 20, 30), 1),
    co("Advertising Agency", "media", 20, ["media", None], 3, (15, 20, 25), 1),
    co("Social Network", "media", 30, ["media", None, None], 5, (15, 25, 35), 1),
    co("Cinema", "lux", 18, ["lux", None], 4, (15, 20, 25), 2),
]
assert len(CC_DECK) == 28

# Public companies. REAL: row 1 for 3-4 players (setup photo): 3 workers each, wages 25/30/35.
# REAL from rules: rows 2-3 cost 20 each (60 per row). Outputs of rows 2-3 and the 2p row are EST.
def pub(name, ind, slots, out, cost=20, wages=(25, 30, 35)):
    return co(name, ind, cost, slots, out, wages)

PUBLIC_34 = [
    [pub("University Hospital", "health", ["health", None, None], 6, 30),
     pub("Technical University", "edu", ["edu", None, None], 6, 30),
     pub("National Public Broadcasting", "media", ["media", None, None], 4, 30)],
    [pub("City Hospital", "health", ["health", None, None], 6),
     pub("State University", "edu", ["edu", None, None], 6),
     pub("National Radio", "media", ["media", None, None], 3)],
    [pub("Regional Hospital", "health", ["health", None, None], 5),
     pub("Public College", "edu", ["edu", None, None], 5),
     pub("Public TV Channel", "media", ["media", None, None], 3)],
]
PUBLIC_2 = [
    [pub("Public Hospital", "health", ["health", None], 5, 20, (20, 25, 30)),
     pub("Public University", "edu", ["edu", None], 5, 20, (20, 25, 30)),
     pub("Public Radio", "media", ["media", None], 3, 20, (20, 25, 30))],
] + PUBLIC_34[1:]

# Middle Class companies. REAL: the two starting ones (setup photo).
# mc = Middle Class worker slots; emp = optional Working Class employee slot (None = unskilled), bonus = extra output.
def mco(name, ind, cost, mc, out, emp=False, bonus=0, emp_wages=(6, 8, 10)):
    return dict(name=name, ind=ind, cost=cost, mc=mc, out=out, emp=emp, bonus=bonus, emp_wages=emp_wages)

MC_START = [
    mco("Doctor's Office", "health", 12, ["health"], 2, emp=True, bonus=2),
    mco("Convenience Store", "food", 14, ["food"], 2, emp=True, bonus=1),
]
MC_DECK = [  # EST, 17 cards
    mco("Bistro", "food", 14, ["food"], 2, True, 1), mco("Fast Food Restaurant", "food", 18, ["food", None], 4),
    mco("Organic Farm", "food", 16, ["food"], 2, True, 2), mco("Deli", "food", 14, ["food"], 2, True, 1),
    mco("Gift Shop", "lux", 12, ["lux"], 2, True, 2), mco("Boutique", "lux", 16, ["lux", None], 4),
    mco("Phone Shop", "lux", 14, ["lux"], 3, True, 2), mco("Dentist", "health", 14, ["health"], 2, True, 2),
    mco("Physiotherapy", "health", 18, ["health", None], 4), mco("Pharmacy Corner", "health", 12, ["health"], 2, True, 1),
    mco("Tutoring Center", "edu", 12, ["edu"], 2, True, 2), mco("Driving School", "edu", 16, ["edu", None], 4),
    mco("Music School", "edu", 14, ["edu"], 3, True, 1), mco("PR Agency", "media", 16, ["media"], 1, True, 1),
    mco("Local Newspaper", "media", 18, ["media", None], 2), mco("Craft Workshop", "lux", 14, ["lux"], 2, True, 2),
    mco("Private Clinic", "health", 20, ["health", "health"], 5),
]
assert len(MC_DECK) == 17

# ---------------------------------------------------------------- foreign market decks (EST from rulebook examples)
# Export card: per resource two offers (amount, price). Examples in the rulebook: 3 Food->25/35,
# 4 Lux->25, 8 Lux->45, 2 Lux->10, 6 Lux->35, 3 Health->20, 5 Health->35, 3 Edu->20, 5 Edu->35.
EXPORT_DECK = [
    {"food": [(3, 25), (5, 40)], "lux": [(4, 25), (8, 45)], "health": [(3, 20), (5, 35)], "edu": [(3, 20), (5, 35)]},
    {"food": [(3, 35), (6, 60)], "lux": [(2, 10), (6, 35)], "health": [(3, 20), (5, 35)], "edu": [(2, 15), (6, 35)]},
    {"food": [(2, 20), (5, 45)], "lux": [(3, 20), (7, 40)], "health": [(2, 15), (6, 40)], "edu": [(3, 20), (5, 30)]},
    {"food": [(4, 35), (6, 50)], "lux": [(4, 25), (6, 35)], "health": [(3, 25), (4, 30)], "edu": [(2, 15), (5, 35)]},
] * 4

# Business Deal: (food, lux, cost). Tariff = 2 per good at 6A, 1 per good at 6B (REAL example: 7 Food + 5 Lux, 70, A+24, B+12).
DEAL_DECK = [(7, 5, 70), (6, 0, 40), (0, 8, 40), (4, 4, 45), (8, 0, 55), (0, 10, 50), (5, 5, 55), (3, 6, 45),
             (6, 3, 50), (8, 4, 70), (4, 0, 25), (0, 6, 30), (5, 2, 40), (2, 8, 50), (6, 6, 65), (7, 0, 45),
             (0, 12, 60), (3, 3, 30), (9, 3, 70), (4, 7, 55)]

# Immigration card: (Working worker skill, Middle worker skill); None = unskilled. EST mix.
_S = [None, "food", "lux", "health", "edu", "media"]
IMMIGRATION_DECK = [(_S[i % 6], _S[(i * 4 + 3) % 6]) for i in range(25)]
