"""Self-check: rulebook numbers, election/tiebreak/IMF rules, and invariants over many full games.

    python test_rules.py
"""
import io
import sys
from collections import Counter

import data as D
import engine


def quiet(players=4, seed=1):
    return engine.Game(players=players, seed=seed, verbose=False)


def test_tables():
    # rulebook examples (v1.1 / v1.2)
    assert D.tax_multiplier("A", "B", "C") == 5          # start of game
    assert D.tax_multiplier("B", "A", "A") == 6          # Taxation example 2
    assert D.corporate_tax(81, "A") == 24                # Capitalist example
    assert D.INCOME_TAX["C"]["B"] == 2                   # Working Class example: 2C + 3B → 2 per Population
    assert D.INCOME_TAX["A"]["C"] * 3 == 15              # Middle Class example: 3 companies at 2A/3C
    assert D.wealth_space(57) + 1 == 3 and D.wealth_space(34) + 1 == 2 and D.wealth_space(166) + 1 == 7
    assert D.wealth_space(166) - D.wealth_space(57) == 4  # marker moves 4 spaces in round 3
    assert [D.population(n) for n in (10, 11, 12, 19, 21, 29, 30, 45)] == [3, 3, 4, 6, 7, 9, 10, 10]
    assert [D.legit_influence(n) for n in (1, 2, 3, 4, 7, 8, 10)] == [0, 1, 1, 2, 3, 4, 5]
    assert D.MC_PROSPERITY[4] == 4 and D.WC_PROSPERITY[5] == 5


def test_setup():
    for n in (2, 3, 4):
        g = quiet(n)
        assert g.policy_str() == "1C 2B 3A 4B 5C 6B 7B"
        assert g.treasury == 120 and g.tax_mult() == 5
        assert len(g.class_workers("W")) == 10 and g.pop("W") == 3
        assert all(len(g.hands[c]) == 7 for c in g.roles)
        assert sum(g.bag.values()) == 24
        if n >= 3:
            assert len(g.class_workers("M")) == 10 and g.money["M"] == 40
        assert len(g.public()) == 3
        assert g.services["health"] == (5 if n == 2 else 6)


def test_election_tie_passes():
    g = quiet(3)
    g.influence.update({"W": 1 - g.influence["W"], "C": 1 - g.influence["C"], "M": -g.influence["M"]})
    g.bills[4] = ("W", "A")
    g.bill_markers["W"] -= 1
    vp = dict(g.vp)
    passed = g.election(4, preview=["W", "W", "C", "C", "C"])   # 2 for, 3 against; W spends 1 → 3–3
    assert passed and g.policies[4] == "A", g.lines[-3:]
    assert g.vp["W"] == vp["W"] + 3


def test_tiebreak():
    g = quiet(3)
    g.vp = {"W": 50, "M": 50, "C": 49}
    g.policies.update({1: "A", 2: "A", 3: "B", 4: "B", 5: "C"})
    g.bag = Counter({"W": 9, "M": 4, "C": 2})
    r = g.winner()
    assert r["winners"] == ["W"] and "cubes" in r["reason"], r
    g4 = quiet(4)
    g4.vp = {"W": 60, "M": 10, "C": 10, "S": 60}
    g4.policies.update({1: "B", 2: "B", 3: "B", 4: "B", 5: "B"})
    g4.agenda = {"name": "x", "targets": {1: "C", 2: "C", 3: "C", 4: "C", 5: "C"}}
    r = g4.winner()
    assert r["winners"] == ["S"] and "State" in r["reason"], r


def test_imf():
    g = quiet(4)
    g.policies.update({1: "B", 2: "A", 3: "C", 4: "A", 5: "A", 6: "C"})
    g.state_loans = 2
    g.treasury = 27
    g.legit = {"W": 6, "M": 8, "C": 7}
    g.check_imf()
    assert g.policy_str().startswith("1C 2C 3A 4B 5C 6B"), g.policy_str()
    assert g.tax_mult() == 5 and g.state_loans == 0
    assert g.legit == {"W": 3, "M": 4, "C": 4}
    assert all(c.level == 1 for c in g.companies.values())


def test_review_fixes():
    import cards
    # State pays Loan interest in a 4p game
    g = quiet(4)
    g.state_loans, g.round, t0 = 1, 2, g.treasury
    g.preparation()
    assert g.treasury == t0 - 5, (t0, g.treasury)
    # IMF: Treasury 87 with 2 Loans → pays all it has, rest discarded (rulebook example)
    g = quiet(4)
    g.policies[1] = "B"
    g.state_loans, g.treasury = 2, 87
    g.imf()
    assert g.treasury == 0 and g.state_loans == 0
    # State Benefits: kept through Scoring, replaced by a later action, stacked within one action
    g = quiet(4)
    g.action_stamp = (1, 1, "S")
    cards.provide(g, "W", "money", 20, "test")
    g.scoring()
    assert g.benefits["W"]["money"] == 20
    g.action_stamp = (2, 1, "S")
    cards.add_benefit(g, "W", "infl", 1)
    cards.add_benefit(g, "W", "cubes", 2)
    assert dict(g.benefits["W"]) == {"infl": 1, "cubes": 2}
    # half price with the State paying the rest (Boost domestic tourism)
    g = quiet(4)
    g.storage["C"]["lux"], g.prices["C"]["lux"] = 4, 8
    rev, t0, m0 = g.revenue, g.treasury, g.money["W"]
    got = g.buy("W", "lux", "C", 4, half_price=True, state_pays_half=True)
    assert got == 4 and g.revenue == rev + 32 and g.treasury == t0 - 16 and g.money["W"] == m0 - 16
    # an Event the State cannot fully Provide is not performed
    g = quiet(4)
    g.treasury, g.state_goods["food"] = 5, 0
    assert not cards.can_provide_all(g, "W", [("food", 4)])


def test_full_games(n=150):
    for players in (2, 3, 4):
        for seed in range(1, n + 1):
            g = quiet(players, seed)
            r = g.play()
            assert r["winners"], seed
            for w in g.workers.values():                 # a worker is in at most one place
                if w.loc and w.loc[0] == "co":
                    co = g.companies[w.loc[1]]
                    assert (co.emp_worker if w.loc[2] == "emp" else co.workers[w.loc[2]]) == w.id
            for co in g.companies.values():              # companies are fully staffed or empty
                filled = [i for i in co.workers if i]
                assert not filled or len(filled) == len(co.slots), (seed, co.name)
            assert len(g.co_of("C")) <= 12 and len(g.co_of("M")) <= 8
            assert g.money["W"] >= 0 and (players < 3 or g.money["M"] >= 0)
            assert min(g.storage["C"].values(), default=0) >= 0
            assert g.services["health"] >= 0 and g.services["edu"] >= 0 and g.media >= 0
            if "S" in g.roles:
                assert all(1 <= v <= 10 for v in g.legit.values())
            assert sum(g.bag.values()) + sum(g.cube_supply.values()) <= 75


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"{len(tests)} test groups passed")
