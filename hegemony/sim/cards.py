"""Action cards (base game, 40 per class), the 25 base Event cards and Political Agendas.

Card texts: English translation in ../cards/*.md (from the unofficial Italian file v2.1 by F. Santoro).
Each card: requirement, effect fn(bot), score fn(bot) -> number or None (None = not worth / not playable),
and the fixed Legitimacy change printed on the card (4 players). Variable Legitimacy is applied inside fn.
A few cards are not modelled (marked SKIP); bots then only ever discard them for a Basic Action.
"""
import math
from collections import Counter

import data as D

# ------------------------------------------------------------------ deck lists (base game, copies)
DECKS = {
    "W": {"Affordable housing": 1, "Boost domestic tourism": 2, "Cooperative farm": 2, "Fake news": 1,
          "General strike": 2, "Healthcare benefits": 2, "Healthcare movement": 1, "Highlight social issues": 1,
          "Immigration": 2, "Immigration reform": 1, "Interest groups": 1, "Labor market deregulation": 2,
          "Need for change": 3, "Proletarians of the world, unite!": 2, "Public opinion polling": 1,
          "Public sector overtime": 2, "Radical reforms": 1, "Signing bonus": 2, "Specialization": 2,
          "State Scholarship": 2, "Student movement": 1, "Supplemental income program": 2,
          "Unemployment benefits": 2, "Workers' movement": 1, "Workplace accident": 1},
    "M": {"Employment subsidy": 2, "Export subsidy": 2, "Fake news": 1, "Foreign market insight": 2,
          "Growing business": 2, "Health crisis": 1, "Healthcare benefits": 1, "Higher education program": 1,
          "Highlight social issues": 1, "Immigration": 3, "Immigration reform": 1, "Import subsidy": 2,
          "Interest groups": 1, "Investment opportunities": 2, "Labor market deregulation": 1,
          "Land of opportunity": 2, "New theme park": 1, "Personal consumption": 2, "Public opinion polling": 2,
          "Public sector overtime": 1, "Small business grant": 2, "Specialization": 2, "State Scholarship": 1,
          "Supplemental income program": 2, "Unemployment initiative program": 1,
          "Voice of middle class workers": 1},
    "C": {"Bid rigging": 1, "Business expansion": 2, "Business grants": 1, "Buy private island": 1,
          "Competitive wages": 2, "Endorse political campaign": 1, "Exit strategy": 2, "Extra shift": 2,
          "Fake news": 1, "Foreign market insight": 2, "Foreign partner": 2, "Foreign recruitment": 2,
          "Global branding": 1, "Global food crisis": 1, "Health crisis": 1, "Higher education program": 1,
          "Industrialization": 1, "Interest groups": 1, "Investment opportunities": 2, "Offshore companies": 2,
          "Public opinion polling": 1, "Push political agenda": 1, "Radical reforms": 1,
          "Tap into new markets": 1, "Taxed enough already": 1, "Technological progress": 3,
          "Trade protectionism lobby": 1, "Unemployment initiative program": 2},
    "S": {"A matter of high priority": 2, "Agenda-setting": 2, "Allowances and subsidies": 2, "Business grants": 1,
          "Construction boom": 1, "Denial of free speech": 1, "Emergency state": 1,
          "Employment support scheme": 1, "Foreign financial assistance": 2, "Foreign investment program": 2,
          "Foreign students": 1, "Geopolitical support": 2, "Growth in tourism": 1, "Healthcare program": 1,
          "Higher VAT": 2, "Immediate response": 2, "Literacy program": 1, "Medical tourism": 1,
          "Nationalization": 1, "Pressing matters": 2, "Privatization": 1, "Public sector overtime": 2,
          "Quantitative easing": 1, "Radical reforms": 1, "Shift focus": 2, "Step for representation": 2,
          "Supplemental income program": 1, "Unemployment initiative program": 1},
}
for _c, _d in DECKS.items():
    assert sum(_d.values()) == 40, (_c, sum(_d.values()))


def action_deck(cls, rng):
    deck = [name for name, n in DECKS[cls].items() for _ in range(n)]
    rng.shuffle(deck)
    return deck


# ------------------------------------------------------------------ helpers
def req_ok(req, g):
    if not req:
        return True
    return any(g.policies[int(r[0])] == r[1] for r in req.split("/"))


def nxt_vp(b):
    g = b.g
    track = D.WC_PROSPERITY if b.c == "W" else D.MC_PROSPERITY
    return track[min(10, g.prosperity[b.c] + 1)]


def add_cubes(b, n):
    got = b.g.add_cubes(b.c, n)
    b.g.log(f"adds {got} cubes to the bag", b.c)
    return True


def bill_value(b, only=None, any_section=False):
    best = b.best_bill(only, any_section)
    if not best or b.g.bill_markers[b.c] <= 0:
        return None
    return 1.0 + best[0]


def two_bills(b):
    b.do_bill(allow_immediate=False)
    b.do_bill(allow_immediate=False)
    return True


def score_two_bills(b):
    g = b.g
    good = 0
    for p in range(1, 8):
        if p not in g.bills and p not in g.blocked and g.policies[p] != b.pref(p):
            good += 1
    if good < 2 or g.bill_markers[b.c] < 2:
        return None
    return 2 + (bill_value(b) or 0)


def polling(b):
    g = b.g
    best = b.best_bill()
    if not best:
        return False
    _, p, target = best
    preview = g.draw_cubes(5)
    cur = g.policies[p]
    fav = sum(1 for cube in preview if cube in g.roles and (cube == b.c or g.bots[cube].vote(p, cur, target)))
    g.propose(b.c, p, target)
    g.log(f"Public opinion polling reveals {''.join(preview)}", b.c)
    if fav >= 3:
        g.log("calls a free Immediate Vote with the revealed cubes", b.c)
        g.election(p, preview=preview)
    else:
        for cube in preview:
            g.bag[cube] += 1
    return True


def fake_news(b):
    g = b.g
    drawn = g.draw_cubes(6)
    removed = 0
    for cube in drawn:
        if cube != b.c and removed < 4 and cube in g.cube_supply:
            g.cube_supply[cube] += 1
            removed += 1
        else:
            g.bag[cube] += 1
    g.log(f"Fake news removes {removed} opposing cubes from the bag", b.c)
    return True


def interest_groups(b):
    g = b.g
    others = 0
    revealed = []
    while others < 3 and sum(g.bag.values()):
        cube = g.draw_cubes(1)[0]
        revealed.append(cube)
        if cube != b.c:
            others += 1
    replaced = 0
    for cube in revealed:
        if cube != b.c and replaced < 3 and g.cube_supply.get(b.c, 0) > 0:
            g.cube_supply[cube] += 1
            g.cube_supply[b.c] -= 1
            g.bag[b.c] += 1
            replaced += 1
        else:
            g.bag[cube] += 1
    g.log(f"Interest groups swaps {replaced} cubes for own", b.c)
    return True


def emigration(b):
    g = b.g
    un = g.unemployed(b.c)
    if len(un) < 4:
        return False
    out = sorted(un, key=lambda w: w.skill is not None)[:2]
    money = 0
    for w in out:
        money += 10 if w.skill else 5
        del g.workers[w.id]
    g.receive(b.c, money)
    g.log(f"Immigration (emigration): 2 unemployed leave, +{money}₩", b.c)
    return True


def half_price_state(b, res):
    return b.do_buy(res, half=True, only=["S"], max_sources=1)


def score_half(b, res, req_src="S"):
    g = b.g
    need = g.pop(b.c) - g.gs[b.c][res]
    if need <= 0 or g.stock(req_src, res) < need:
        return None
    cost = math.ceil(g.unit_price(b.c, req_src, res) * need / 2)
    if cost > b.spendable():
        return None
    return nxt_vp(b) + (2.5 if res == "health" else 1.5)


def pso_target(b):
    g = b.g
    best = None
    for co in g.public():
        if co.operational() and co.ind in ("health", "edu"):
            if best is None or g.services[co.ind] < g.services[best.ind]:
                best = co
    return best


def public_overtime(b):
    g = b.g
    co = pso_target(b)
    if not co:
        return False
    payee = g.workers[co.workers[0]].cls
    g.pay("S", co.wage(), to=payee, why="Public sector overtime")
    added = g.store("S", D.PRODUCT[co.ind], co.production())
    g.log(f"Public sector overtime at {co.name}: +{added} {co.ind} for the State", b.c)
    if b.c in ("W", "M"):
        b.do_buy(co.ind, only=["S"], max_sources=1)
    return True


def score_pso(b):
    g = b.g
    co = pso_target(b)
    if not co or b.c not in ("W", "M"):
        return None
    need = g.pop(b.c) - g.gs[b.c][co.ind]
    if g.services[co.ind] + co.production() < need:
        return None
    cost = g.unit_price(b.c, "S", co.ind) * need
    if cost > b.spendable():
        return None
    return nxt_vp(b) + 2


def coop_farm(b):
    g = b.g
    un = sorted(g.unemployed("W"), key=lambda w: w.skill is not None)
    if len(un) < 3:
        return False
    spec = dict(name="Cooperative Farm", ind="food", cost=0, slots=[None, None, None], out=2, wages=(0, 0, 0))
    co = g.new_company(spec, "W")
    co.coop = True
    for i, w in enumerate(un[:3]):
        g.put(w, co, i, committed=True)
        w.loc = ("coop", co.id, i)
    g.coops.append(co)
    g.log("starts a Cooperative Farm with 3 workers", "W")
    return True


def specialization(b):
    g = b.g
    w = g.new_worker("W", b.pick_skill())
    g.log(f"Specialization: new skilled worker ({w.skill})", b.c)
    if b.c == "W":
        b.do_assign(3)
    else:
        mc_hire(b, 3)
    return True


def mc_hire(b, n, pay_state=0):
    """Middle Class assigns unemployed Working Class workers into its own employee slots."""
    g = b.g
    hired = 0
    for co in g.co_of("M"):
        if hired >= n:
            break
        if co.emp and co.operational() and co.emp_worker is None:
            cand = [w for w in g.unemployed("W") if w.skill is None] or g.unemployed("W")
            if not cand:
                break
            g.put(cand[0], co, "emp", committed=True)
            hired += 1
    if pay_state and hired:
        g.pay("S", pay_state * hired, to="M", why="Unemployment initiative")
    g.log(f"hires {hired} Working Class employee(s)", "M")
    return hired > 0


def open_emp_slots(g):
    return sum(1 for co in g.co_of("M") if co.emp and co.operational() and co.emp_worker is None)


def sell_to_state(b, res, cap, price=10):
    g = b.g
    have = g.storage[b.c][res]
    keep = g.pop(b.c) if b.c == "M" else 0
    n = min(cap, max(0, have - keep))
    if res in ("health", "edu"):
        n = min(n, max(0, g.service_cap(res) - g.services[res]))
    if n <= 0:
        return False
    g.storage[b.c][res] -= n
    if res in ("health", "edu"):
        g.services[res] += n
    elif "S" in g.roles:
        g.state_goods[res] += n
    g.pay("S", n * price, to=b.c, why=f"buys {res}")
    g.log(f"sells {n} {res} to the State for {n * price}₩", b.c)
    g.legit_change(b.c, n // 3, "sold to the State")
    return True


def score_sell_state(b, res, cap):
    g = b.g
    keep = g.pop(b.c) if b.c == "M" else 0
    n = min(cap, max(0, g.storage[b.c][res] - keep))
    if res in ("health", "edu"):
        n = min(n, max(0, g.service_cap(res) - g.services[res]))
    if n < 2:
        return None
    return n * 10 / 12


def tech_progress(b):
    g = b.g
    target = best_machinery(g)
    if not target or g.machinery_supply <= 0:
        return False
    g.pay("C", 20, why="Technological progress")
    target.machinery = True
    g.machinery_supply -= 1
    g.log(f"puts a Machinery token on {target.name} (+{target.mach_bonus})", "C")
    return True


def best_machinery(g):
    cands = [c for c in g.co_of("C") if c.mach_bonus and not c.machinery and not c.auto and c.operational()]
    return max(cands, key=lambda c: c.mach_bonus, default=None)


def cc_extra_shift(b):
    g = b.g
    best = None
    for co in g.co_of("C"):
        if co.operational() and not co.auto and not co.strike:
            val = co.production() * b.value(D.PRODUCT[co.ind]) - co.wage()
            room = g.cap("C", D.PRODUCT[co.ind]) - g.storage["C"][D.PRODUCT[co.ind]]
            if room >= co.production() and (best is None or val > best[0]):
                best = (val, co)
    if not best or best[0] <= 0:
        return False
    co = best[1]
    g.pay("C", co.wage(), to=g.workers[co.workers[0]].cls, why="extra shift")
    g.store("C", D.PRODUCT[co.ind], co.production())
    g.log(f"Extra shift at {co.name}", "C")
    return True


def score_cc_extra_shift(b):
    g = b.g
    best = None
    for co in g.co_of("C"):
        if co.operational() and not co.auto and not co.strike:
            room = g.cap("C", D.PRODUCT[co.ind]) - g.storage["C"][D.PRODUCT[co.ind]]
            if room >= co.production():
                val = co.production() * b.value(D.PRODUCT[co.ind]) - co.wage()
                best = max(best or 0, val)
    return best / 10 if best and best > 5 and b.spendable() > 20 else None


def foreign_insight(b, look=1, mult=1):
    g = b.g
    cands = [g.export] + [g.export_deck.pop() for _ in range(look) if g.export_deck]

    def worth(card):
        old = g.export
        g.export = card
        t = b.export_plan()[0]
        g.export = old
        return t
    best = max(cands, key=worth)
    g.export = best
    if b.c == "M":
        return b.do_export(mult=mult)
    return b.do_export()


def add_benefit(g, target, key, n):
    """Items placed in a State Benefits area replace what an earlier action left there (rulebook);
    several items placed by the same action (same turn) add up."""
    stamp = getattr(g, "action_stamp", None)
    if g.__dict__.setdefault("benefit_stamp", {}).get(target) != stamp:
        g.benefits[target] = Counter()
        g.benefit_stamp[target] = stamp
    g.benefits[target][key] += n


def provide(g, target, res, n, why, dry=False):
    """State Provides n of res (or money) to target's State Benefits area, buying what it lacks
    from other players (not the target) or the Foreign Market at its base price. All or nothing."""
    if n <= 0:
        return False
    if res == "money":
        if g.treasury < n:
            return False
        if not dry:
            g.treasury -= n
            add_benefit(g, target, "money", n)
            g.log(f"Provides {n}₩ to {target} ({why})", "S")
        return True
    take = min(g.stock("S", res), n)
    short = n - take
    bought, cost = Counter(), 0
    for src in ("C", "M", "F"):
        if not short:
            break
        if src == target or (src not in g.roles and src != "F") or (src == "F" and res not in ("food", "lux")):
            continue
        k = min(short, g.stock(src, res))
        if k <= 0:
            continue
        unit = D.IMPORT_BASE[res] if src == "F" else g.prices[src][res]
        bought[src] = k
        cost += unit * k
        short -= k
    if short or cost > g.treasury:
        return False
    if dry:
        return True
    for src, k in bought.items():
        unit = D.IMPORT_BASE[res] if src == "F" else g.prices[src][res]
        g.pay("S", unit * k, to=None if src == "F" else src, why="Provide")
        if src != "F":
            g.storage[src][res] -= k
    if res in ("health", "edu"):
        g.services[res] -= take
    elif res == "infl":
        g.media -= take
    else:
        g.state_goods[res] -= take
    add_benefit(g, target, res, n)
    g.log(f"Provides {n} {res} to {target} ({why})", "S")
    return True


def can_provide(g, target, res, n):
    return provide(g, target, res, n, "", dry=True)


def split_parts(n, ress):
    """'X and Y in any combination, at least 1 of each': split n as evenly as possible."""
    n = max(n, len(ress))
    return [(r, n // len(ress) + (1 if i < n % len(ress) else 0)) for i, r in enumerate(ress)]


def can_provide_all(g, target, parts):
    """Check several Provides against the Treasury together (they are paid one after the other)."""
    saved = g.treasury
    ok = True
    for r, k in parts:
        if not provide(g, target, r, k, "", dry=True):
            ok = False
            break
        # reserve the money this part would cost
        take = min(g.stock("S", r), k)
        if k - take:
            prices = [D.IMPORT_BASE[r]] if r in ("food", "lux") else []
            prices += [g.prices[s][r] for s in ("C", "M") if s in g.roles and s != target and g.stock(s, r)]
            g.treasury -= (k - take) * max(prices or [0])
    g.treasury = saved
    return ok


# ------------------------------------------------------------------ the card table
SKIP = {"Competitive wages", "Nationalization", "Denial of free speech", "Privatization"}


def C(req, fn, score, legit=None):
    return dict(req=req, fn=fn, score=score, legit=legit or {})


def card_table():
    t = {}
    # ---------- shared names (behaviour depends on the playing class)
    t["Fake news"] = C(None, fake_news, lambda b: 1.2 if b.g.bills else None)
    t["Interest groups"] = C(None, interest_groups, lambda b: 1.6 if b.g.bills else 1.0)
    t["Public opinion polling"] = C(None, polling, lambda b: (bill_value(b) or -9) + 1.5 if bill_value(b) else None)
    t["Radical reforms"] = C(None, lambda b: b.do_bill(any_section=True, allow_immediate=False),
                             lambda b: (bill_value(b, any_section=True) or 0) + 0.5 if bill_value(b) else None)
    t["Immigration"] = C(None, emigration,
                         lambda b: (2.5 if b.c == "M" else 0.8) if len(b.g.unemployed(b.c)) >= 4 else None)
    t["Immigration reform"] = C(None, lambda b: (add_cubes(b, 2), b.do_bill(only=7))[1],
                                lambda b: bill_value(b, only=7) and bill_value(b, only=7) + 1)
    t["Labor market deregulation"] = C("2B/2C", lambda b: b.do_assign(99),
                                       lambda b: 3 + len(b.assign_options()) if len(b.assign_options()) >= 2 else None)
    t["Highlight social issues"] = C(None, lambda b: buy_influence(b),
                                     lambda b: 1.8 if b.g.media >= 3 and b.spendable() >= 30 and b.g.bills else None, {"self": 1})
    t["Public sector overtime"] = C(None, public_overtime, lambda b: score_pso(b) if b.c in "WM" else (
        2.0 if b.c == "S" and any(c.operational() and c.ind in ("health", "edu") for c in b.g.public())
        and b.spendable() > 40 else None))
    # ---------- Working Class
    t["Affordable housing"] = C(None, affordable_housing,
                                lambda b: (5.5 if b.g.round == 5 else 3) if "C" in b.g.roles and b.spendable() >= 20 else None)
    t["Boost domestic tourism"] = C("1A/1B", lambda b: b.do_buy("lux", half=True, only=["C", "M"], max_sources=1,
                                                                 state_pays_half=True),
                                    lambda b: score_half(b, "lux", "C") if "C" in b.g.roles else None,
                                    {"W": 1})
    t["Cooperative farm"] = C(None, coop_farm, lambda b: 5 if len(b.g.unemployed("W")) >= 3 else None)
    t["General strike"] = C("2B/2C", lambda b: b.do_strike(2 + len(b.g.unions)),
                            lambda b: 3 if b.strike_targets() and b.g.money["W"] > b.reserve() + 20 else None)
    t["Healthcare movement"] = C(None, lambda b: (add_cubes(b, 2), b.do_bill(only=4))[1],
                                 lambda b: bill_value(b, only=4) and bill_value(b, only=4) + 1)
    t["Student movement"] = C(None, lambda b: (add_cubes(b, 2), b.do_bill(only=5))[1],
                              lambda b: bill_value(b, only=5) and bill_value(b, only=5) + 1)
    t["Workers' movement"] = C(None, lambda b: (add_cubes(b, 2), b.do_bill(only=2))[1],
                               lambda b: bill_value(b, only=2) and bill_value(b, only=2) + 1)
    t["Need for change"] = C(None, two_bills, score_two_bills)
    t["Proletarians of the world, unite!"] = C(None, lambda b: add_cubes(b, b.g.pop("W")),
                                               lambda b: 1.5 + b.g.pop("W") / 4 if b.g.bills else 1.0)
    t["Signing bonus"] = C("2B/2C", lambda b: b.do_assign(4, pay_each=4),
                           lambda b: 4 + len(b.assign_options()) if b.assign_options() else None)
    t["Specialization"] = C("7B/7C", specialization,
                            lambda b: 3.5 if (b.c == "W" and b.assign_options()) or
                            (b.c == "M" and open_emp_slots(b.g)) else None)
    t["Supplemental income program"] = C("2B/2C", supplemental_income, score_supplemental)
    t["Unemployment benefits"] = C("4A/4B", unemployment_benefits,
                                   lambda b: 1 + len(b.g.unemployed("W")) * 5 / 8 if b.g.unemployed("W") else None)
    t["Workplace accident"] = C(None, workplace_accident, lambda b: workplace_value(b) / 10 or None)
    t["Healthcare benefits"] = C("4B/4C", lambda b: half_price_state(b, "health"),
                                 lambda b: score_half(b, "health"), {"self": 1})
    t["State Scholarship"] = C("5B/5C", lambda b: half_price_state(b, "edu"),
                               lambda b: score_half(b, "edu"), {"self": 1})
    # ---------- Middle Class
    t["Employment subsidy"] = C("1A/1B", employment_subsidy,
                                lambda b: 1 + sum(1 for c in b.g.co_of("M") if c.emp_worker) * 5 / 8
                                if any(c.emp_worker for c in b.g.co_of("M")) else None)
    t["Export subsidy"] = C("1A/1B", lambda b: b.do_export(bonus_each=5),
                            lambda b: b.export_plan()[1] * 1.6 + b.export_plan()[0] / 25 if b.export_plan()[1] else None,
                            {"M": 1})
    t["Foreign market insight"] = C(None, lambda b: foreign_insight(b, 1 if b.c == "M" else 2, 2 if b.c == "M" else 1),
                                    lambda b: (b.export_plan()[0] / 10 + 1) if b.export_plan()[1] else None)
    t["Growing business"] = C(None, growing_business, lambda b: 3.5 if b.c == "M" else None)
    t["Health crisis"] = C(None, lambda b: sell_to_state(b, "health", 6 if b.c == "M" else 9),
                           lambda b: score_sell_state(b, "health", 6 if b.c == "M" else 9))
    t["Higher education program"] = C(None, lambda b: sell_to_state(b, "edu", 6 if b.c == "M" else 9),
                                      lambda b: score_sell_state(b, "edu", 6 if b.c == "M" else 9))
    t["Import subsidy"] = C("6A/6B", import_subsidy, score_import_subsidy)
    t["Investment opportunities"] = C(None, lambda b: b.do_build(discount=8 if b.c == "M" else 10),
                                      lambda b: (b.build_options(8 if b.c == "M" else 10) or [[None]])[0][0]
                                      and b.build_options(8 if b.c == "M" else 10)[0][0] + 1.5)
    t["Land of opportunity"] = C("7B/7C", land_of_opportunity, lambda b: 4 if b.g.mc_market and
                                 b.spendable() >= min(s["cost"] for s in b.g.mc_market) else None)
    t["New theme park"] = C(None, theme_park,
                            lambda b: nxt_vp(b) - 6 * b.g.pop("M") / 15 if b.spendable() >= 6 * b.g.pop("M") else None)
    t["Personal consumption"] = C(None, lambda b: b.do_buy(max_sources=3),
                                  lambda b: (b.buy_target() or [None])[0] and b.buy_target()[0] + 0.7)
    t["Small business grant"] = C("1A/1B", lambda b: b.do_build(state_pays=True),
                                  lambda b: 5 if b.build_options(99) else None, {"M": 1})
    t["Unemployment initiative program"] = C("4A/4B", unemployment_initiative, score_unemployment_initiative)
    t["Voice of middle class workers"] = C(None, lambda b: add_cubes(b, 2 + mc_outside(b.g)),
                                           lambda b: 1.5 + mc_outside(b.g) / 2 if b.g.bills else 1.0)
    # ---------- Capitalist
    t["Bid rigging"] = C(None, lambda b: sell_to_state(b, "lux", 6) and b.g.influence.update({"C": 1}) is None,
                         lambda b: score_sell_state(b, "lux", 6))
    t["Business expansion"] = C(None, business_expansion,
                                lambda b: 6 if len(b.build_options()) >= 2 and b.build_options()[1][0] > 0 else None)
    t["Business grants"] = C("1A/1B", business_grants_cc, lambda b: len(b.g.co_of("C")) * 5 / 10 + 1)
    t["Buy private island"] = C(None, private_island,
                                lambda b: 6 if b.g.round == 5 and b.g.capital >= 50 + b.reserve() else None)
    t["Endorse political campaign"] = C(None, lambda b: b.g.pay("C", 15, forced=False) and add_cubes(b, 6),
                                        lambda b: 2.8 if b.g.bills and b.spendable() > 30 else None)
    t["Exit strategy"] = C(None, exit_strategy, score_exit)
    t["Extra shift"] = C(None, cc_extra_shift, score_cc_extra_shift)
    t["Foreign partner"] = C("6B/6C", lambda b: (b.do_deal(), b.do_export(only=("food", "lux")))[0],
                             lambda b: b.deal_option() and b.deal_option()[0] + 2)
    t["Foreign recruitment"] = C("7B/7C", foreign_recruitment, score_foreign_recruitment)
    t["Global branding"] = C(None, lambda b: b.do_export(extra=("lux", 6, 10)),
                             lambda b: (b.export_plan()[0] + 10 * min(6, b.g.storage["C"]["lux"])) / 11 or None)
    t["Global food crisis"] = C(None, lambda b: b.do_export(extra=("food", 4, 15)),
                                lambda b: (b.export_plan()[0] + 15 * min(4, b.g.storage["C"]["food"])) / 11 or None)
    t["Industrialization"] = C("1A/1B", lambda b: b.do_build(filt=lambda s: s["ind"] in ("food", "lux"),
                                                              state_half=True),
                               lambda b: 5 if b.build_options(filt=lambda s: s["ind"] in ("food", "lux")) else None,
                               {"C": 1})
    t["Offshore companies"] = C(None, offshore, lambda b: b.g.revenue / 30 if b.g.revenue >= 60 else None)
    t["Push political agenda"] = C(None, lambda b: b.g.pay("C", 25, forced=False) and two_bills(b),
                                   lambda b: score_two_bills(b) and b.spendable() > 40 and score_two_bills(b) - 1)
    t["Tap into new markets"] = C(None, lambda b: (add_cubes(b, 2), b.do_bill(only=6))[1],
                                  lambda b: bill_value(b, only=6) and bill_value(b, only=6) + 1)
    t["Taxed enough already"] = C(None, lambda b: (add_cubes(b, 2), b.do_bill(only=3))[1],
                                  lambda b: bill_value(b, only=3) and bill_value(b, only=3) + 1.5)
    t["Technological progress"] = C(None, tech_progress,
                                    lambda b: (best_machinery(b.g).mach_bonus * 2.5 * (6 - b.g.round) - 20) / 10
                                    if best_machinery(b.g) and b.g.machinery_supply and b.spendable() > 30 else None)
    t["Trade protectionism lobby"] = C("6A/6B", lambda b: add_cubes(b, 2 * protection_count(b.g)),
                                       lambda b: 1 + protection_count(b.g) / 2 if b.g.bills else None)
    # ---------- State
    t["A matter of high priority"] = C(None, lambda b: state_extra_event(b), lambda b: event_score(b) + 0.5)
    t["Shift focus"] = C(None, lambda b: state_extra_event(b, replace=True), lambda b: event_score(b) + 0.7)
    t["Immediate response"] = C(None, immediate_response, lambda b: event_score(b) * 1.8 if event_score(b) > 2 else None)
    t["Agenda-setting"] = C(None, lambda b: gain_infl(b, agenda_matches(b.g)), lambda b: agenda_matches(b.g) * 0.9)
    t["Allowances and subsidies"] = C(None, allowances, lambda b: 4 if b.spendable() > 30 else None)
    t["Construction boom"] = C(None, lambda b: boom(b, ("S", "W", "C")), lambda b: 4.5, {"W": 1, "C": 1})
    t["Growth in tourism"] = C(None, lambda b: boom(b, ("S", "M", "C")), lambda b: 4.5, {"M": 1, "C": 1})
    t["Emergency state"] = C(None, emergency_state, lambda b: 3.5 if len(b.g.bills) >= 3 and emergency_pick(b) else None)
    t["Employment support scheme"] = C(None, employment_support, lambda b: 3.5 if b.spendable() > 30 else None,
                                       {"W": 1, "M": 1})
    t["Foreign financial assistance"] = C(None, lambda b: b.g.receive("S", 10 * agenda_matches(b.g)) or True,
                                          lambda b: agenda_matches(b.g) * 10 / 9)
    t["Foreign investment program"] = C(None, foreign_investment,
                                        lambda b: 4 if b.g.influence["S"] >= 2 and b.g.treasury < 60 else None)
    t["Foreign students"] = C("1A/1B", lambda b: state_export(b, "edu"), lambda b: state_export_score(b, "edu"))
    t["Medical tourism"] = C("1A/1B", lambda b: state_export(b, "health"), lambda b: state_export_score(b, "health"))
    t["Geopolitical support"] = C(None, lambda b: b.g.receive("S", {"A": 15, "B": 30, "C": 45}[b.g.policies[6]]) or True,
                                  lambda b: {"A": 15, "B": 30, "C": 45}[b.g.policies[6]] / 9)
    t["Healthcare program"] = C("4A/4B", lambda b: welfare_program(b, "health"), lambda b: welfare_score(b, "health"))
    t["Literacy program"] = C("5A/5B", lambda b: welfare_program(b, "edu"), lambda b: welfare_score(b, "edu"))
    t["Higher VAT"] = C(None, higher_vat, lambda b: 4 if b.g.treasury < 60 and sorted(b.g.legit.values())[1] > 1 else None)
    t["Pressing matters"] = C(None, lambda b: b.do_bill(free_immediate=True),
                              lambda b: bill_value(b) and bill_value(b) + 1.5)
    t["Quantitative easing"] = C(None, lambda b: b.g.receive("S", 35 if b.g.state_loans else 25) or True,
                                 lambda b: 3.2 if b.g.treasury < 120 else 2.0)
    t["Step for representation"] = C(None, step_representation,
                                     lambda b: 3.5 if b.g.influence["S"] >= 1 else None)
    t["Unemployment initiative program"] = C("4A/4B", unemployment_initiative, score_unemployment_initiative)
    # State versions of names shared with other classes (different card text)
    t["S:Supplemental income program"] = C("2B/2C", state_supplemental, score_state_supplemental)
    t["S:Business grants"] = C("1A/1B", state_business_grants,
                               lambda b: 2.5 if "C" in b.g.roles and b.spendable() >= 5 * len(b.g.co_of("C")) else None)
    return t


def state_supplemental(b):
    g = b.g
    c = min((x for x in ("W", "M") if x in g.roles), key=lambda x: g.legit[x])
    n = sum(1 for w in g.class_workers(c) if w.loc)
    if not provide(g, c, "money", n, "Supplemental income program"):
        return False
    g.legit_change(c, n // 10, "Supplemental income program")
    return True


def score_state_supplemental(b):
    g = b.g
    n = max(sum(1 for w in g.class_workers(c) if w.loc) for c in ("W", "M") if c in g.roles)
    return 1 + n // 10 * 1.5 if n >= 10 and b.spendable() >= n else None


def state_business_grants(b):
    g = b.g
    n = len(g.co_of("C"))
    if not provide(g, "C", "money", 5 * n, "Business grants"):
        return False
    g.legit_change("C", n // 3, "Business grants")
    return True


# ------------------------------------------------------------------ effect functions (cont.)
def buy_influence(b):
    g = b.g
    n = min(3, g.media)
    if n <= 0 or not g.pay(b.c, 15, to="S", why="Influence", forced=False):
        return False
    g.media -= n
    g.influence[b.c] += n
    g.log(f"buys {n} Influence from the State for 15₩", b.c)
    return True


def affordable_housing(b):
    g = b.g
    if "C" in g.roles and g.pay("W", 20, to="C", forced=False):
        g.gain_vp("W", 5, "Affordable housing")
    elif "M" in g.roles and g.pay("W", 10, to="M", forced=False):
        g.gain_vp("W", 3, "Affordable housing")
    return True


def supplemental_income(b):
    g = b.g
    if b.c == "W":
        n = sum(1 for w in g.class_workers("W") if w.loc)
        g.pay("S", n, to="W", why="Supplemental income")
        g.legit_change("W", n // 10, "Supplemental income")
    else:
        n = mc_outside_workers(g)
        g.pay("S", 2 * n, to="M", why="Supplemental income")
        g.legit_change("M", n // 5, "Supplemental income")
    g.log(f"receives {n if b.c == 'W' else 2 * n}₩ from the State", b.c)
    b.do_buy()
    return True


def score_supplemental(b):
    g = b.g
    money = sum(1 for w in g.class_workers("W") if w.loc) if b.c == "W" else 2 * mc_outside_workers(g)
    t = b.buy_target()
    return money / 8 + (t[0] if t else 0) + 0.3


def unemployment_benefits(b):
    g = b.g
    n = len(g.unemployed("W"))
    g.pay("S", 5 * n, to="W", why="Unemployment benefits")
    g.legit_change("W", n // 3, "Unemployment benefits")
    g.log(f"receives {5 * n}₩ unemployment benefits", "W")
    b.do_buy(only=["S"], max_sources=1)
    return True


def workplace_value(b):
    g = b.g
    best = 0
    for owner in ("C", "M"):
        if owner not in g.roles:
            continue
        for ind in D.IND:
            n = sum(1 for co in g.co_of(owner) if co.ind == ind and any(
                i and g.workers[i].cls == "W" for i in co.workers + [co.emp_worker]))
            best = max(best, 8 * n)
    return best


def workplace_accident(b):
    g = b.g
    best = (0, None, None)
    for owner in ("C", "M"):
        if owner not in g.roles:
            continue
        for ind in D.IND:
            n = sum(1 for co in g.co_of(owner) if co.ind == ind and any(
                i and g.workers[i].cls == "W" for i in co.workers + [co.emp_worker]))
            if 8 * n > best[0]:
                best = (8 * n, owner, ind)
    if not best[1]:
        return False
    g.pay(best[1], best[0], to="W", why="Workplace accident")
    g.log(f"takes {best[0]}₩ from the {best[1]} ({best[2]} companies)", "W")
    return True


def employment_subsidy(b):
    g = b.g
    cos = [c for c in g.co_of("M") if c.emp_worker]
    g.pay("S", 5 * len(cos), to="M", why="Employment subsidy")
    g.legit_change("M", len(cos) // 3, "Employment subsidy")
    g.log(f"receives {5 * len(cos)}₩ Employment subsidy", "M")
    for co in cos:
        if all(not g.workers[i].committed for i in co.workers if i):
            return b.do_extra_shift(co) or True
    return True


def growing_business(b):
    g = b.g
    prod = Counter()
    for co in g.co_of("M"):
        prod[D.PRODUCT[co.ind]] += co.production()
    res = next((r for r, _ in prod.most_common() if r in ("food", "lux", "health", "edu")
                and r not in g.extra_storage["M"]), None)
    if res:
        g.extra_storage["M"].add(res)
        g.log(f"builds a free {res} Storage", "M")
    b.do_build(discount=4, discount_res=res)
    return True


def import_subsidy(b):
    g = b.g
    res = "food"
    if g.gs["M"]["lux"] < g.pop("M") and b.spendable() >= g.pop("M") * D.IMPORT_BASE["lux"]:
        res = "lux"
    n = g.pop("M")
    cost = D.IMPORT_BASE[res] * n
    if not g.pay("M", cost, forced=False):
        return False
    g.gs["M"][res] += n
    g.legit_change("M", n // 4, "Import subsidy")
    g.log(f"imports {n} {res} without tariff for {cost}₩", "M")
    return True


def score_import_subsidy(b):
    g = b.g
    if g.gs["M"]["lux"] + g.pop("M") >= g.pop("M") and b.spendable() >= g.pop("M") * 6 and g.policies[6] != "C":
        return nxt_vp(b) + 0.3
    return None


def land_of_opportunity(b):
    g = b.g
    for spec in sorted(g.mc_market, key=lambda s: s["cost"]):
        if spec["cost"] <= b.spendable() + 10 and len(spec["mc"]) == 1:
            w = g.new_worker("M", spec["mc"][0])
            g.log(f"Land of opportunity: new skilled worker ({w.skill})", "M")
            return b.do_build(spec_only=spec)
    return False


def theme_park(b):
    g = b.g
    cost = 6 * g.pop("M")
    if not g.pay("M", cost, forced=False):
        return False
    g.gain_prosperity("M", "New theme park")
    return True


def unemployment_initiative(b):
    g = b.g
    if b.c == "M":
        ok = mc_hire(b, 3, pay_state=5)
        g.legit_change("M", 1, "card")
        return ok
    owner = b.c
    for co in g.co_of(owner) if owner == "C" else g.public():
        if co.operational() or co.auto:
            continue
        for cls in ("W", "M"):
            if cls not in g.roles:
                continue
            team = b.pick_team(co, g.unemployed(cls))
            if team:
                for slot, w in team:
                    g.put(w, co, slot, committed=True)
                if owner == "C":
                    g.pay("S", 5 * len(team), to="C", why="Unemployment initiative")
                    g.legit_change("C", 1, "card")
                g.log(f"staffs {co.name} with {len(team)} unemployed", owner)
                return True
    return False


def score_unemployment_initiative(b):
    g = b.g
    if b.c == "M":
        return 3 + open_emp_slots(g) if open_emp_slots(g) and g.unemployed("W") else None
    cos = g.co_of("C") if b.c == "C" else g.public()
    for co in cos:
        if not co.operational() and not co.auto:
            for cls in ("W", "M"):
                if cls in g.roles and b.pick_team(co, g.unemployed(cls)):
                    return 4
    return None


def mc_outside(g):
    return len({w.loc[1] for w in g.class_workers("M") if w.loc and w.loc[0] == "co"
                and g.companies[w.loc[1]].owner != "M"})


def mc_outside_workers(g):
    return sum(1 for w in g.class_workers("M") if w.loc and w.loc[0] == "co" and g.companies[w.loc[1]].owner != "M")


def business_expansion(b):
    g = b.g
    b.do_build(n=2)
    for _ in range(2):
        if g.cc_deck:
            g.cc_market.append(g.cc_deck.pop())
    return True


def business_grants_cc(b):
    g = b.g
    n = len(g.co_of("C"))
    g.pay("S", 5 * n, to="C", why="Business grants")
    g.legit_change("C", n // 3, "Business grants")
    g.log(f"receives {5 * n}₩ Business grants", "C")
    return True


def private_island(b):
    g = b.g
    g.pay("C", 50, to="S", why="private island", from_capital=True)
    g.gain_vp("C", 7, "Buy private island")
    return True


def exit_target(b):
    g = b.g
    cands = [c for c in g.co_of("C") if not c.auto and not c.machinery and not c.operational()]
    return max(cands, key=lambda c: c.cost, default=None)


def exit_strategy(b):
    g = b.g
    co = exit_target(b)
    if not co:
        return False
    g.clear_company(co)
    del g.companies[co.id]
    g.receive("C", 2 * co.cost)
    g.log(f"Exit strategy: sells {co.name} for {2 * co.cost}₩", "C")
    return True


def score_exit(b):
    co = exit_target(b)
    return co.cost / 10 + 0.5 if co and b.g.round >= 3 else None


def foreign_recruitment(b):
    g = b.g
    for co in g.co_of("C"):
        if not co.operational() and not co.auto:
            g.pay("C", 10, why="Foreign recruitment")
            for i, s in enumerate(co.slots):
                w = g.new_worker("W", s)
                g.put(w, co, i, committed=True)
            g.log(f"Foreign recruitment staffs {co.name} with {len(co.slots)} new workers", "C")
            return True
    return False


def score_foreign_recruitment(b):
    g = b.g
    return 4 if any(not c.operational() and not c.auto for c in g.co_of("C")) and b.spendable() > 10 else None


def offshore(b):
    g = b.g
    half = g.revenue // 2
    g.revenue -= half
    g.capital += half
    g.log(f"Offshore companies: {half}₩ moved from Revenue to Capital", "C")
    return True


def protection_count(g):
    n = sum(1 for c in g.co_of("C") if c.ind == "food")
    if g.policies[6] == "A":
        n += sum(1 for c in g.co_of("C") if c.ind == "lux")
    return n


def agenda_matches(g):
    return sum(1 for p, s in g.agenda["targets"].items() if g.policies[p] == s) if g.agenda else 0


def gain_infl(b, n):
    b.g.influence["S"] += n
    b.g.log(f"gains {n} Personal Influence", "S")
    return True


def allowances(b):
    g = b.g
    low = min(g.legit, key=g.legit.get)
    if provide(g, low, "money", 20, "Allowances and subsidies"):
        g.legit_token(low, "Allowances and subsidies")
    return True


def boom(b, who):
    g = b.g
    for c in who:
        if c == "S" or c in g.roles:
            g.receive(c, 15)
    g.log(f"{', '.join(who)} each gain 15₩", "S")
    return True


def employment_support(b):
    g = b.g
    for c in ("W", "M"):
        if c in g.roles:
            provide(g, c, "money", 15, "Employment support scheme")
    return True


def emergency_pick(b):
    g = b.g
    for p in range(1, 8):
        if p not in g.bills and g.policies[p] != b.pref(p):
            return p
    return None


def emergency_state(b):
    from bots import step_toward
    g = b.g
    p = emergency_pick(b)
    if not p:
        return False
    target = step_toward(g.policies[p], b.pref(p))
    g.log(f"Emergency state moves Policy {p} to {target}", "S")
    g.set_policy(p, target)
    return True


def foreign_investment(b):
    g = b.g
    g.influence["S"] -= 2
    g.receive("S", 40)
    g.log("spends 2 Influence for 40₩", "S")
    return True


def state_export(b, res):
    g = b.g
    price = g.state_price(res)
    n = min(8, g.services[res])
    g.services[res] -= n
    g.receive("S", n * price)
    g.log(f"sells {n} {res} abroad for {n * price}₩", "S")
    return True


def state_export_score(b, res):
    g = b.g
    price = g.state_price(res)
    return min(8, g.services[res]) * price / 15 if price and g.services[res] >= 3 else None


def welfare_target(b, res):
    g = b.g
    best = None
    for c in ("W", "M"):
        if c in g.roles and can_provide(g, c, res, g.pop(c)):
            if best is None or g.legit[c] < g.legit[best]:
                best = c
    return best


def welfare_program(b, res):
    g = b.g
    c = welfare_target(b, res)
    if not c:
        return False
    if provide(g, c, res, g.pop(c), "welfare program"):
        g.legit_token(c, "welfare program")
    return True


def welfare_score(b, res):
    return 5 if welfare_target(b, res) else None


def higher_vat(b):
    g = b.g
    for c in "WMC":
        if c in g.roles:
            g.pay(c, 15, to="S", why="Higher VAT")
    for c in sorted(g.legit, key=lambda c: -g.legit[c])[:2]:
        g.legit_change(c, -1, "Higher VAT")
    return True


def step_representation(b):
    g = b.g
    low = min(g.legit, key=g.legit.get)
    g.influence["S"] -= 1
    add_benefit(g, low, "infl", 1)
    add_benefit(g, low, "cubes", 2)
    g.legit_change(low, 2, "Step for representation")
    return True


def event_score(b):
    e = best_event(b)
    return e[0] if e else 0


def state_extra_event(b, replace=False):
    g = b.g
    if g.event_deck:
        if len(g.events) < 2 or replace:
            new = g.draw_event(first_round=g.round == 1)
            if replace and g.events:
                worst = min(g.events, key=lambda e: event_value(b, e)[0])
                g.events.remove(worst)
            g.events.append(new)
            g.log(f"places Event {new['name']}", "S")
    e = best_event(b)
    if e:
        resolve_event(b, e[1], e[2])
    return True


def immediate_response(b):
    e = best_event(b)
    if not e:
        return False
    resolve_event(b, e[1], e[2], twice=True)
    return True


# ------------------------------------------------------------------ evaluation API used by bots
TABLE = None


def evaluate(card, bot):
    """(playable_and_wanted, score, fn) for a card in the bot's hand."""
    global TABLE
    TABLE = TABLE or card_table()
    spec = lookup(card, bot.c)
    if card in SKIP or spec is None:
        return False, 0, None
    g = bot.g
    if not req_ok(spec["req"], g):
        return False, 0, None
    s = spec["score"](bot)                      # errors surface instead of hiding a broken card
    if s is None or s is False:
        return False, 0, None
    return True, float(s), lambda: spec["fn"](bot)


def static_value(card):
    return 0.0 if card in SKIP else 0.5


def lookup(card, cls):
    global TABLE
    TABLE = TABLE or card_table()
    return TABLE.get(f"{cls}:{card}") or TABLE.get(card)


def apply_legitimacy(card, bot):
    spec = lookup(card, bot.c)
    if spec:
        for cls, n in spec["legit"].items():
            bot.g.legit_change(bot.c if cls == "self" else cls, n, f"card {card}")


# ------------------------------------------------------------------ Events (25 base cards)
HALF_POP = lambda g, c: math.ceil(g.pop(c) / 2)
HALF_OPS = lambda g, c: math.ceil(sum(1 for x in g.co_of(c) if x.operational()) / 2) if c != "W" else HALF_POP(g, c)


def EV(name, kind, choices, penalty, r25=False, **kw):
    return dict(name=name, kind=kind, choices=choices, penalty=penalty, rounds_2_5=r25, **kw)


EVENTS = [
    EV("Outdated public sector infrastructure", "buy_from", {"M": ("per", 3), "C": ("per", 3)},
       {"M": -1, "C": -1}, True, res="lux"),
    EV("Low university ratings", "buy_from", {"M": ("per", 3), "C": ("per", 3)}, {"M": -1, "C": -1}, True, res="edu"),
    EV("Pandemic", "buy_from", {"M": ("per", 3), "C": ("per", 3)}, {"M": -1, "C": -1}, True, res="health"),
    EV("Political polarization", "cubes", {"W": ("per", 2, -1), "C": ("per", 2)}, {"W": -1, "C": -1}, money=30),
    EV("Strike at the port", "provide", {"W": ("token",), "C": ("token",)}, {"W": -1, "C": -1},
       res="infl", amount=lambda g, c: 2),
    EV("Developing countries in need", "spend", {}, "choose2", res="edu", cap=6),
    EV("Earthquake", "provide", {"W": ("per", 2), "M": ("per", 2)}, {"W": -1, "M": -1},
       res="food+health", amount=HALF_POP),
    EV("Unfair representation", "represent", {"W": ("flat", 1), "M": ("flat", 1), "C": ("flat", 1)}, "choose2"),
    EV("Drought", "provide", {"W": ("token",), "C": ("token",)}, {"W": -1, "C": -1}, res="food", amount=HALF_OPS),
    EV("Demand for higher welfare standards", "provide", {"W": ("flat", 1), "M": ("flat", 1)}, {"W": -1, "M": -1},
       res="health+edu", amount=HALF_POP),
    EV("Technological illiteracy", "provide", {"W": ("per", 2), "C": ("per", 2)}, {"W": -1, "C": -1},
       res="lux+edu", amount=HALF_OPS),
    EV("Need for sustainability initiative", "money2", {"W": ("token",), "M": ("token",), "C": ("token",)},
       "choose2", money=25),
    EV("Companies demand better internet", "provide", {"M": ("per", 2), "C": ("per", 2)}, {"M": -1, "C": -1},
       res="lux", amount=HALF_OPS),
    EV("Demand for pension reform", "provide_money", {"W": ("vp_per", 15, 2), "M": ("token_per", 20)},
       {"W": -1, "M": -1}, amount=lambda g, c: 5 * g.pop(c)),
    EV("Need for stimulus package", "stimulus", {}, "choose2"),
    EV("Fear of deflation", "spend_money", {}, "choose2"),
    EV("Neighbors at war", "spend", {}, "choose2", res="health", cap=6),
    EV("Low education index", "provide", {"W": ("flat", 1), "M": ("flat", 1)}, {"W": -1, "M": -1},
       res="edu", amount=HALF_POP),
    EV("Declining birth rate", "provide", {"W": ("flat", 1), "M": ("flat", 1)}, {"W": -1, "M": -1},
       res="health", amount=HALF_POP),
    EV("Global supply chain crisis", "provide", {"W": ("per", 2), "M": ("vp_res", 1)}, {"W": -1, "M": -1},
       res="food+lux", amount=HALF_POP),
    EV("Civil unrest", "bill", {"W": ("flat", 2), "C": ("flat", 2)}, {"W": -1, "C": -1}),
    EV("Infant industry requires help", "build_for", {"M": ("token",), "C": ("token",)}, {"M": -1, "C": -1}),
    EV("Demand for thirteen month pay", "provide_money", {"W": ("token_per", 25), "M": ("per_money", 15)},
       {"W": -1, "M": -1}, amount=lambda g, c: 5 * sum(1 for w in g.class_workers(c) if w.loc and w.loc[0] == "co"
                                                         and g.companies[w.loc[1]].owner == "S")),
    EV("Political scandal", "scandal", {"W": ("per", 1), "M": ("per", 1), "C": ("per", 1)}, "choose2", money=25),
    EV("Local industries in turmoil", "provide_money", {"M": ("token_per", 20), "C": ("vp_per", 15, 2)},
       {"M": -1, "C": -1}, amount=lambda g, c: 5 * sum(1 for x in g.co_of(c) if x.operational())),
]
assert len(EVENTS) == 25

# EST: the 10 base Political Agenda cards are not in any source we have; target sections are estimates.
AGENDAS = [
    dict(name="Welfare State", targets={1: "B", 2: "B", 3: "A", 4: "B", 5: "B"}),
    dict(name="Minimal State", targets={1: "C", 2: "C", 3: "C", 4: "C", 5: "C"}),
    dict(name="Socialist Program", targets={1: "A", 2: "A", 3: "A", 4: "A", 5: "A"}),
    dict(name="Labour Coalition", targets={1: "B", 2: "A", 3: "B", 4: "A", 5: "B"}),
    dict(name="Business Friendly", targets={1: "C", 2: "B", 3: "B", 4: "B", 5: "C"}),
    dict(name="Public Investment", targets={1: "A", 2: "B", 3: "A", 4: "B", 5: "A"}),
    dict(name="Austerity", targets={1: "B", 2: "C", 3: "A", 4: "C", 5: "B"}),
    dict(name="Status Quo", targets={1: "C", 2: "B", 3: "A", 4: "B", 5: "C"}),
    dict(name="Education First", targets={1: "B", 2: "B", 3: "B", 4: "A", 5: "A"}),
    dict(name="Third Way", targets={1: "A", 2: "C", 3: "B", 4: "B", 5: "B"}),
]


def event_and_agenda_decks(rng):
    ev = [dict(e) for e in EVENTS]
    ag = [dict(a) for a in AGENDAS]
    rng.shuffle(ev)
    rng.shuffle(ag)
    return ev, ag


def reward_value(g, e, c, units):
    r = e["choices"].get(c)
    if not r:
        return 0
    kind = r[0]
    if kind == "token":
        return 3
    if kind == "flat":
        return r[1] * (1.5 if g.legit[c] <= sorted(g.legit.values())[1] else 0.8)
    if kind == "per":
        sign = r[2] if len(r) > 2 else 1
        return sign * (units // r[1]) * 1.2
    if kind in ("vp_per",):
        return (units // r[1]) * r[2]
    if kind == "token_per":
        return 3 * (units // r[1])
    if kind == "per_money":
        return units // r[1]
    if kind == "vp_res":
        return units
    return 0


def event_value(b, e):
    """Best (value, choice) for an Event, or (0, None) if the State can't do it."""
    g = b.g
    k = e["kind"]
    penalty = 2 if e["penalty"] == "choose2" else 1.5
    best = (0, None)
    if k == "provide":
        for c in e["choices"]:
            if c not in g.roles:
                continue
            n = e["amount"](g, c)
            ress = e["res"].split("+")
            ok = n > 0 and can_provide_all(g, c, split_parts(n, ress))
            if ok:
                v = reward_value(g, e, c, n) + penalty
                best = max(best, (v, c))
    elif k == "provide_money":
        for c in e["choices"]:
            if c not in g.roles:
                continue
            n = e["amount"](g, c)
            if n > 0 and g.treasury - n > 20:
                best = max(best, (reward_value(g, e, c, n) + penalty - n / 25, c))
    elif k == "money2":
        if g.treasury > 70:
            best = (6 + penalty - 2, "low2")
    elif k == "spend":
        n = min(e["cap"], g.services[e["res"]])
        if n >= 2:
            best = (n * 0.8 + penalty, None)
    elif k == "spend_money":
        amt = 45 if g.treasury > 110 else 30 if g.treasury > 70 else 15 if g.treasury > 40 else 0
        if amt:
            best = (2 * amt / 15 + penalty - amt / 20, amt)
    elif k == "stimulus":
        n = len([c for c in "WMC" if c in g.roles])
        if g.treasury > 15 * n + 30:
            best = (3 + penalty, 15)
        elif g.treasury > 10 * n + 30:
            best = (3 + penalty - 1, 10)
    elif k == "represent":
        if g.influence["S"] >= 1:
            low = min(g.legit, key=g.legit.get)
            best = (1.5 + penalty, low)
    elif k == "cubes":
        if g.treasury > 50:
            best = (2 + penalty, "C")
    elif k == "scandal":
        if g.treasury > 45 and g.media >= 1:
            best = (min(3, g.media) * 1.2 + penalty - 1, None)
    elif k == "buy_from":
        for c in e["choices"]:
            if c in g.roles and g.storage.get(c, Counter())[e["res"]] >= 3:
                n = min(len(g.public()), g.storage[c][e["res"]])
                cost = n * g.prices[c][e["res"]]
                if g.treasury - cost > 20:
                    best = max(best, (n // 3 * 1.2 + penalty - cost / 30, c))
    elif k == "bill":
        for c in e["choices"]:
            if c in g.roles and g.bill_markers["S"] > 0:
                best = max(best, (2 + penalty, c))
    elif k == "build_for":
        for c in e["choices"]:
            if c not in g.roles:
                continue
            market = g.cc_market if c == "C" else g.mc_market
            for spec in market:
                if spec["cost"] >= 15 and g.treasury - spec["cost"] > 20:
                    if c == "M" and not b.pick_team(type("X", (), {"slots": spec["mc"]}), g.unemployed("M")):
                        continue
                    best = max(best, (3 + penalty - spec["cost"] / 25, c))
                    break
    return best


def best_event(b):
    g = b.g
    best = None
    for e in g.events:
        v, choice = event_value(b, e)
        if choice is not None or v > 0:
            if v > 0 and (best is None or v > best[0]):
                best = (v, e, choice)
    return best


def resolve_event(b, e, choice, twice=False):
    g = b.g
    k = e["kind"]
    g.log(f"Event Action: {e['name']}", "S")
    g.stats["events"] += 1
    for rep in range(2 if twice else 1):
        if k == "provide":
            c = choice
            parts = split_parts(e["amount"](g, c), e["res"].split("+"))
            if not can_provide_all(g, c, parts):                 # task must be done in full
                g.log(f"cannot fully do {e['name']}: action not performed", "S")
                return False
            done = sum(k2 for r, k2 in parts if provide(g, c, r, k2, e["name"]))
            give_reward(g, e, c, done)
        elif k == "provide_money":
            n = e["amount"](g, choice)
            if not provide(g, choice, "money", n, e["name"]):
                return False
            give_reward(g, e, choice, n)
        elif k == "money2":
            for c in sorted([c for c in "WMC" if c in g.roles], key=lambda c: g.legit[c])[:2]:
                provide(g, c, "money", 25, e["name"])
                g.legit_token(c, e["name"])
        elif k == "spend":
            n = min(e["cap"], g.services[e["res"]])
            g.services[e["res"]] -= n
            g.gain_vp("S", n, e["name"])
        elif k == "spend_money":
            amt = choice if isinstance(choice, int) else 15
            g.pay("S", amt, why=e["name"])
            g.gain_vp("S", 2 * amt // 15, e["name"])
        elif k == "stimulus":
            amt = choice or 10
            for c in "WMC":
                if c in g.roles:
                    provide(g, c, "money", amt, e["name"])
                    if amt == 15:
                        g.legit_change(c, 1, e["name"])
            if amt == 10:
                g.gain_vp("S", 3, e["name"])
        elif k == "represent":
            c = choice
            g.influence["S"] -= 1
            add_benefit(g, c, "infl", 1)
            add_benefit(g, c, "cubes", 2)
            g.legit_change(c, 1, e["name"])
        elif k == "cubes":
            g.pay("S", 30, why=e["name"])
            add_benefit(g, "C", "cubes", 4)
            g.legit_change("C", 2, e["name"])
        elif k == "scandal":
            g.pay("S", 25, why=e["name"])
            n = min(3, g.media)
            for i in range(n):
                c = min(g.legit, key=g.legit.get)
                g.media -= 1
                add_benefit(g, c, "infl", 1)
                g.legit_change(c, 1, e["name"])
        elif k == "buy_from":
            c = choice
            n = min(len(g.public()), g.storage[c][e["res"]])
            cost = n * g.prices[c][e["res"]]
            g.storage[c][e["res"]] -= n
            g.pay("S", cost, to=c, why=e["name"])
            g.store("S", e["res"], n)
            g.legit_change(c, n // 3, e["name"])
        elif k == "bill":
            c = choice
            from bots import step_toward
            p = g.bots[c].best_bill()
            if p:
                g.propose("S", p[1], p[2])
            g.legit_change(c, 2, e["name"])
        elif k == "build_for":
            c = choice
            if c == "C":
                spec = next((s for s in g.cc_market if s["cost"] >= 15), None)
                if spec:
                    g.pay("S", spec["cost"], why=e["name"])
                    g.cc_market.remove(spec)
                    co = g.new_company(spec, "C")
                    co.level = g.min_wage()
                    g.log(f"builds {co.name} for the Capitalist", "S")
            else:
                for spec in g.mc_market:
                    team = b.pick_team(type("X", (), {"slots": spec["mc"]}), g.unemployed("M"))
                    if spec["cost"] >= 15 and team:
                        g.pay("S", spec["cost"], why=e["name"])
                        g.mc_market.remove(spec)
                        co = g.new_company(spec, "M")
                        for slot, w in team:
                            g.put(w, co, slot, committed=True)
                        g.log(f"builds {co.name} for the Middle Class", "S")
                        break
            g.legit_token(c, e["name"])
        if twice and rep == 0:
            v, choice = event_value(b, e)
            if not v:
                break
    if e in g.events:
        g.events.remove(e)


def give_reward(g, e, c, units):
    r = e["choices"].get(c)
    if not r:
        return
    kind = r[0]
    if kind == "token":
        g.legit_token(c, e["name"])
    elif kind == "flat":
        g.legit_change(c, r[1], e["name"])
    elif kind == "per":
        sign = r[2] if len(r) > 2 else 1
        g.legit_change(c, sign * (units // r[1]), e["name"])
    elif kind == "vp_per":
        g.gain_vp("S", (units // r[1]) * r[2], e["name"])
    elif kind == "token_per":
        for _ in range(units // r[1]):
            g.legit_token(c, e["name"])
    elif kind == "per_money":
        g.legit_change(c, units // r[1], e["name"])
    elif kind == "vp_res":
        g.gain_vp("S", units, e["name"])
