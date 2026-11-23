# Hegemony: Lead Your Class to Victory: Full Rules Reference

Based on the **official English rulebook v1.1** (June 2023, 40 pages, Tabletopia copy). Where v1.1 changed
the original 2021 rulebook (v1.0), the old value is noted as *(v1.0: …)*. Numbers printed only on the
player boards (Wealth table, Prosperity tracks, Legitimacy→Influence row, Foreign Market base prices) are
not in the rulebook text. Read those off your own boards.

- **Rulebook v1.2 (Nov 2023)** only adds clarifications to v1.1:
  - A struck company produces nothing **and pays no wage**.
  - Each Production step is finished by all players before the next one starts.
  - A strike token is removed if its company loses its workers.
  - For the Demonstration cap, the State's face-down Public Companies count as its empty spaces.
  - A Middle Class employee slot with no Middle Class worker running the company is not an open job.
- **Card texts:** English translations of all action, Event and Agenda cards are in `cards/`. They come from the unofficial Italian file v2.1 by F. Santoro.
- **Simulator:** `sim/` plays complete games. Use `python sim/run.py --players 4 --seed 9` for one game and `python sim/test_rules.py` for the rule checks.
- Designers: Varnavas Timotheou, Vangelis Bagiartakis. Publisher: Hegemonic Project Games (2021).
- 2–4 players, asymmetric, card-driven. 5 rounds. Most VP wins.
- A digital version exists on Board Game Arena. The *Crisis & Control* expansion (included in the Extended
  Edition) and *Historical Events* have their own rulebooks; they are **not** covered here.

---

## 1. The idea in one paragraph

Each player runs a social class in one country. The **Capitalist Class** builds companies and wants profit.
The **Working Class** supplies labour, buys food, health, education and luxury, and wants **Prosperity**. The
**Middle Class** does a bit of both: it works, runs small companies and also wants Prosperity. The **State**
runs public services and wants **Legitimacy** with all three classes. Everyone fights over **7 Policies** on the
Politics Table (wages, taxes, welfare, trade, immigration…). Bills are proposed during the round and decided
by elections, where votes are cubes drawn from a bag plus secretly spent Influence.

## 2. Roles by player count

| Players | Roles |
|---|---|
| 2 | Capitalist + Working Class (recommended for a first game) |
| 3 | + Middle Class |
| 4 | + State |

When the State is not a player, the public sector still produces, pays wages from the State Treasury and
collects taxes automatically. Legitimacy symbols, Events, Political Agendas and State Benefits are ignored.

## 3. Components (key ones)

- Main board: Politics Table, Tax Multiplier track, Vote Results, Business Deals, Export, Import, State
  Treasury, Public Services, Public Sector, Private Sector, Unemployed Workers, Immigration, Events and State
  Benefits (4p only), VP track, Round track.
- 4 player boards, 4 player aids, rule aids.
- 160 Action cards (40 per role).
- Companies: 28 Capitalist, 17 Middle Class, 12 Public, 2 Cooperative Farms (Working Class).
- 16 Export cards, 25 Immigration cards, 20 Business Deal cards, 25 Event cards, 10 Political Agenda cards, 10 Loans.
- 6 Storage tiles, 1 Free Trade Zone tile, 2 Welfare tiles, 6 Machinery tokens, 7 Strike tokens,
  1 Demonstration token, 18 Legitimacy tokens.
- Resources: Food, Luxury, Health, Education, Influence. Money is "Vardis" (₩).
- 48 Working Class and 42 Middle Class Workers (gray = unskilled; colored = skilled in one industry).
- 75 Voting cubes in 3 colours (WC / MC / CC; the State has none), cloth bag, Bill markers (3 per player),
  Vote tokens.

**5 industries (company colour):** Agriculture (green → Food), Luxury (blue → Luxury), Healthcare (red/white
meeple → Health), Education (orange → Education), Media (purple → Influence).

**Company card:** name, cost, industry, output, required worker slots (coloured slot = skilled worker of
that industry), 3 wage levels (L1 / L2 / L3), Machinery bonus. **Automated** companies have no slots, always
produce, pay no wage and count as having Machinery.

---

## 4. Setup (v1.1)

### Main board
1. Board in the middle.
2. Capitalist starting companies **Supermarket, Shopping Mall, College, Clinic** in the Capitalist area; wage marker on **L2**.
3. Public companies: remove the 3 not for your player count (2 diamonds = 2p, 3 diamonds = 3–4p). 3 starting
   ones face-up in row 1 (under their resource), wage on **L2**. One of each type face-down in row 2, the
   rest face-down in row 3.
4. 3–4p: Middle Class starting companies **Convenience Store, Doctor's Office**, wage on **L2**.
5. Shuffle Business Deals; 1 face-up.
6. Shuffle Exports; 1 face-up. Import marker on the **middle** space.
7. Shuffle Immigration deck onto its space.
8. **Starting policies: 1C · 2B · 3A · 4B · 5C · 6B · 7B.**
9. State Treasury: **120₩** *(v1.0: 120 in 2p, 140 in 3–4p)*.
10. Public Services: 2p = 5 Health, 5 Education, 3 Influence; 3–4p = 6 / 6 / 4.
11. Round marker on 1, **Tax Multiplier on 5** (= 3 from 3A + 1×2 from 4B + 0 from 5C).
12. Scoring markers on 0.
13. **8 cubes of each colour** in the bag, all 3 colours even in 2p *(v1.0: 6 each)*.
14. Supply piles: resources, money, Machinery, Loans, Storage, Strike, Demonstration, Legitimacy tokens.
15. Workers sorted by class/colour (2p: Middle Class workers back in the box).
16. General Player Aid.

Suggested seating: Capitalist next to State, Middle next to Working.

### Working Class
- Population marker at **10**, Prosperity **0**, **30₩ + 1 Influence**, 3 red Bill markers + Vote token.
- Shuffle deck, **draw 7** *(v1.0: 8)*. Cooperative Farm cards aside.
- Workers on companies:
  - 2p: Supermarket (green + gray), Shopping Mall (blue + gray), Public Hospital (white + gray), Public University (orange + gray).
  - 3–4p: Supermarket (green + gray), College (orange + gray), University Hospital (white + 2 gray).
- 1 gray worker in Unemployed, plus Immigration cards (1 in 2p, 2 in 3–4p): add the WC worker shown on each, cards to bottom.

### Middle Class (3–4p)
- Population **10**, Prosperity **0**, **40₩ + 1 Influence**, **1 Food + 1 Health** in storage.
- Prices: Food **12**, others **8** *(v1.0: Food 11)*. 3 yellow Bill markers + Vote token. **Draw 7.**
- Company deck: reveal **3** as your Market.
- Workers: Technical University (orange + 2 gray), Shopping Mall (blue + gray), Convenience Store (green), Doctor's Office (white).
- 1 skilled MC worker of your choice in Unemployed, then 2 Immigration cards (MC worker on each).

### Capitalist Class
- **120₩ in Revenue**, marker next to the Wealth table.
- **1 Food, 2 Luxury, 2 Education, 1 Influence**. Prices: Food **12**, others **8**.
- Free Trade Zone tile, 3 blue Bill markers + Vote token, **draw 7**, company deck: reveal **4** as Market.

### State (4p)
- Legitimacy markers on the **2nd space** of each of the 3 tracks. **1 Influence**, 3 gray Bill markers + Vote token, **draw 7**.
- Events: reveal 2 (a "Rounds 2–5 only" card is reshuffled and replaced in round 1).
- Political Agenda: reveal 1 face-up.
- Health Welfare tile under Public Health, **4B side** up; Education Welfare tile aside (5C = none).

---

## 5. Round structure

5 rounds, each: **Preparation → Action → Production → Elections → Scoring**. Preparation is **skipped in round 1**.

### 5.1 Preparation (rounds 2–5)
Move the Round marker, then each role does its own steps (order per General Player Aid):

| Role | Steps |
|---|---|
| Working | Pay 5₩ interest per Loan → Prosperity −1 (no VP lost) → draw 5 (hand 7) → +2 gray workers, plus Immigration (7B: +1 card, 7C: +2 cards) |
| Middle | Interest → Prosperity **−2** → draw 5 → refill company Market to 3 (may discard first) → +1 gray **and** +1 skilled of choice, plus Immigration cards |
| Capitalist | Interest → draw 5 → refill Market to 4 (may discard first) → discard old Business Deals, draw new per Policy 6 (A 0 / B 1 / C 2) → replace Export card. *Done before the other classes get workers.* |
| State | Interest → reveal 2 Events → reveal a new Political Agenda → draw 5 |

Each class draws its **own** Immigration cards (never share one card).

### 5.2 Action phase
- Turn order: **Working → Middle → Capitalist → State**. Each player takes **5 turns** *(v1.0: 6)*; the
  2 cards left in hand carry over.
- On a turn: **one Main Action** = play a card for its effect (only if its requirement, usually a policy, is
  met) **or** discard any card to take a **Basic Action**; plus **one Free Action** before or after.
- Legitimacy symbols on the bottom of a card (4p) move the State's Legitimacy tracks when the card is
  **played for its effect** by anyone. They are ignored when the card is discarded for a Basic Action.

### 5.3 Production phase (reverse order: State → Capitalist → Middle → Working)
1. **Produce Goods & Services:** owners pay each company's wage **once per company** (not per worker) to the
   worker owner, then add output to storage. Committed workers stand up after producing *(v1.0: they stood
   up in the next Preparation)*.
2. **Cover Needs:** WC and MC must consume **Food = Population**. Use your own food first, then buy from
   anyone. Mandatory: take a Loan if you can't pay.
3. **Check IMF** (new in v1.1): see §8.
4. **Pay Taxes** to the State Treasury, never to the supply.

Public Services storage limit = production of the available public companies **+6** *(v1.0: +4)*; excess is lost.

### 5.4 Elections phase
Skipped entirely if no Bill is pending.

**Refill Bag:**
- Working: cubes = **½ Population** (round up).
- Capitalist: **½ operational companies** (round up). Automated companies count.
- Middle: the higher of ½ Population or ½ operational companies.
- 2p: still add 5 Middle cubes.
- State: no cubes; gains **Personal Influence** shown above its lowest Legitimacy track.
- *(v1.0 used full values, not halves.)*

**Each election (Policy 1 → 7 order):**
1. In player order everyone declares **For / Against** (no abstaining; flip your Vote token). The proposer is For.
   The State must declare if it has any Personal Influence; with none it sits out.
2. **Draw 5 cubes**; each is one vote for its owner's side.
3. Everyone announces their Influence, secretly hides any amount in a fist, and all reveal together. Each Influence is +1 vote.
4. **For ≥ Against → passes** (ties pass). Move the policy marker and apply its effects immediately.
   Proposer **+3 VP**; every other For-player who actually contributed a cube or an Influence gets **+1 VP**.
   No VP if the bill fails.
5. Discard the winning side's cubes and **all** spent Influence; the losing side's cubes go back in the bag.
- 2p: drawn Middle cubes count toward the 5 but are discarded and neutral. If all 5 are Middle and no Influence is spent, the bill passes.
- If everyone agrees, still draw 5 and discard them; VP as normal.
- Bag empty when you need to draw: run Refill Bag **twice** (no Influence to the State), then draw.

### 5.5 Scoring phase
Role-specific (see §6). The State first applies Event penalties.

### 5.6 Game end (after round 5)
1. **Loans:** the Capitalist loses **5 VP per Loan**. The others may pay **55₩ per Loan**. What they can't pay
   is paid in steps of 5₩, at −1 VP per unpaid 5₩.
2. End-game scoring per role (§6).
3. **Tiebreak:** most Policies 1–5 in "your" section (WC = A, MC = B, CC = C, State = matching its Agenda) →
   if the State is tied, the State wins → most Voting cubes → shared win.

---

## 6. The roles in detail

### Shared basics
- **Propose Bill** (all roles): put a Bill marker on the section **adjacent** to the current one of a policy
  with no marker on it. You may pay **1 Influence for an Immediate Vote**, which is resolved now and returns the
  marker. 3 markers means at most 3 pending bills per round.
- **Apply Political Pressure** (WC, MC, CC): add **3** of your cubes to the bag.
- **Buy Goods & Services** (WC, MC): choose **one** resource and buy from **up to 2 sources**, at most
  **Population** tokens from each source. Prices: CC/MC set them on their boards; Foreign Market = board
  price **+ tariff** (tariff paid to the State); State Health/Education per Policies 4/5; State Influence fixed.
  The Middle Class "buys" from itself for free, and that counts as one of the 2 sources.
- **Committed workers** (lying down): cannot be reassigned, can't have their wage lowered, and their company
  can't be sold. They are committed when assigned or when the wage is raised by a Free Action.
- **Assign Workers** (WC, MC): move up to **3** of your workers from anywhere, uncommitted ones only. A company is
  either fully staffed or empty; any partial leftovers go to Unemployed (checked after the whole action).
  Skilled slots take only that industry's skilled worker; unskilled slots take anyone.
- **Loans:** only forced, never voluntary. +50₩ (Capitalist: into Capital). 5₩ interest each Preparation.
  The Pay Off Loan free action costs 50₩.
- **Receive Benefits** (WC, MC, CC; 4p only, **Free Action** in v1.1): take what the State put in your
  State Benefits area. Voting cubes there go straight into the bag. The State gets **+1 VP** *(v1.0: Basic Action, +2 VP)*.

### 6.1 Working Class: goal Prosperity
**Basic actions:** Propose Bill · Assign Workers · Buy Goods & Services · Strike · Demonstration · Apply Political Pressure.

- **Strike:** Strike tokens on up to 2 companies where your workers are (not committed, not L3 wage; public
  companies only in 4p). At the start of Production, tokens on L3 companies are removed. Each other struck,
  operational company **does not produce** and you gain **1 Influence**. On a Middle Class company only the
  employee's production bonus is lost.
- **Demonstration:** allowed if your unemployed workers exceed the open slots for your class by **≥2**. Place
  the token. It is cancelled if someone builds a company, assigns your workers and the condition is no longer
  met. Otherwise in Production you gain **1 Influence** and the others lose VP in total =
  **unemployed + Trade Unions** (you split it). Each player's loss is capped at their empty company spaces.
- **Trade Unions:** assign a **skilled** worker to the union of an industry where you have **≥4 other workers**.
  It is always committed and gets no wage. It gives **+1 Influence** each Production and **+2 VP** each Scoring.
  If you drop below 4, it dissolves.

**Free actions:**
- **Use Healthcare:** spend Health = Population → +1 Prosperity, **+2 VP**, +1 gray worker.
- **Use Education:** spend Education = Population → +1 Prosperity, upgrade one worker to a skilled colour.
- **Use Luxury:** spend Luxury = Population → +1 Prosperity.
- **Swap Workers:** a skilled worker in an unskilled slot swaps with an unemployed worker (repeatable).
- Receive Benefits · Pay Off Loan.

**Prosperity:** each step up scores **VP = the new track value**. Drops don't cost VP.

**Production:** paid wages; Cooperative Farm makes 2 Food. Cover Needs (Food = Population).
**Income tax = per-Population rate × Population** (table in §7.3).
**Scoring:** 2 VP per Trade Union.
**End:** Socialist (A) policies among 1–5: 1/2/3/4/5 → **1/4/8/12/18 VP**; **1 VP per 10₩, max 15 VP**.

**Cooperative Farm:** built only via WC cards. Needs 3 unskilled workers, makes 2 Food, not on the board. Its
workers count toward the Agriculture union.

### 6.2 Middle Class: goal Prosperity plus its own businesses
**Basic actions:** Propose Bill · Assign Workers · Build Company · Sell Company · Sell to Foreign Market · Buy Goods & Services · Extra Shift · Apply Political Pressure.

- **Build Company:** from your 3-card Market. You need the required MC worker(s) free (unemployed or
  uncommitted). Two types: 1 MC worker + an optional WC employee slot, or 2 MC workers. Pay the cost, place
  workers committed, set the employee wage (≥ Labor Market minimum) and optionally hire an unemployed WC worker
  (unskilled first). **Max 8 companies.**
- **Sell Company:** discard it (no committed workers), workers go to Unemployed, gain its cost.
- **Sell to Foreign Market:** use the current Export card; each listed transaction **once per action**, only
  from storage. **+1 VP per transaction.**
- **Extra Shift:** a company with uncommitted MC worker(s): commit them and produce now. Pay the employee's
  wage. If only the employee is committed, they don't contribute (no wage, no bonus).

**Free actions:** Use Healthcare / Education / Luxury (as WC) · Adjust Prices · Adjust Wages (raising commits; can't lower on a committed employee) · Swap Workers · Receive Benefits · Pay Off Loan.

**Production:** own MC-only companies produce with no wage; pay WC employees and get their bonus. Storage
holds 8 per resource; Influence goes straight to Goods & Services (no limit). Cover Needs: own Food first.
**Taxes:** Income tax = rate (§7.3) × number of **other players' companies** where you have workers;
**Employment tax** = operational own companies × Tax Multiplier.
**Scoring:** if Prosperity < number of **fully operational** companies (2 workers inside), +1 Prosperity (with its VP).
**End:** B policies among 1–5: 1/2/3/4/5 → **1/3/6/10/15 VP** *(v1.0: 1/4/8/12/18)*; 1 VP per
2 Food / 3 Luxury / 3 Health / 3 Education in storage; **1 VP per 15₩**.

### 6.3 Capitalist Class: goal profit (Wealth)
Money comes in to **Revenue** (untaxed) and is moved to **Capital** at scoring. Spending comes from Revenue,
then Capital.

**Basic actions:** Propose Bill · Build Company · Sell Company · Sell to Foreign Market · Make Business Deal · Lobby · Apply Political Pressure.

- **Build Company:** from your 4-card Market, paid from Revenue. Set any wage ≥ the minimum. You may staff it at
  once with unemployed workers **all from one class**, unskilled first for unskilled slots. **Max 12 companies.**
- **Sell Company / Sell to Foreign Market:** as above, but no VP per transaction. Influence can never be sold.
- **Make Business Deal:** buy a deal's Food/Luxury cheaply. Either store normally (pay the card cost **+ tariff to
  the State**, can sell to players) or put it all in the **Free Trade Zone** (no tariff, but it can only be
  sold abroad; excess is lost).
- **Lobby:** pay **30₩ from Capital** → **3 Influence**.

**Free actions:** Adjust Prices · Adjust Wages · **Give Bonus** (5₩ to a company's worker owner, commits them) · **Buy Storage** (20₩, max 1 per resource; doubles capacity) · Receive Benefits · Pay Off Loan (50₩ from Capital).

**Machinery tokens** (from cards): one per eligible company, adds that company's printed bonus. The company
still needs workers (it isn't automated).

**Production:** pay wages, produce. Storage 8 Food, 12 others. Excess Food/Luxury can go to the FTZ.
**Taxes:** Employment tax = operational companies × Tax Multiplier; **then** Corporate tax on what is left in
Revenue (table in §7.4).
**Scoring:** move Revenue to Capital; score the Wealth table VP for your Capital. If that is a new high, move
the Wealth marker right and gain **+3 VP per space** *(v1.0: +2)*. It never moves back.
**End:** Neoliberal (C) policies among 1–5 → **1/4/8/12/18 VP**; 1 VP per 2 Food / 3 Lux / 3 Health / 3 Edu
(FTZ included); **−5 VP per Loan**.

### 6.4 The State (4p only): goal Legitimacy
- **Legitimacy tracks** (one per class) rise when the State helps a class and fall when it hurts one. They
  start on space 2.
- **Media Influence** (made by public companies, sold to players) is different from **Personal Influence**
  (on the State board, used for votes and actions). Campaign converts Media into Personal.
- **Selling cheap services:** Health/Education sold at 5 (policy B) → **+1 VP** per sale. Given free (policy A)
  → **+1 Legitimacy with that class per 3 tokens**.
- **Provide** (Events/cards): place items in a class's State Benefits area. You may buy what you lack first
  (not from that class; no tariff to yourself). New items replace old ones.

**Basic actions:**
- Propose Bill (no cubes, so you need Influence or allies).
- **Event Action:** resolve one face-up Event, make its choice and take the reward.
- Sell to Foreign Market (goods only).
- **Meet with a Party's MPs:** give 2 Personal Influence to a player → +1 Legitimacy with that class.
- **Extra Tax:** take 10₩ from each player (they take Loans if needed) → −1 Legitimacy with the two lowest classes. Needs Legitimacy to lose.
- **Campaign:** move up to 3 Media Influence → Personal Influence.

**Free actions:** Adjust Wages · Pay Off Loan.

**Elections:** gain Personal Influence per the lowest Legitimacy. Must declare a side if holding any Influence.
**Scoring:**
1. Apply the "NO ACTION" penalty of each unresolved Event and discard it.
2. **VP = sum of the two lowest Legitimacy values**. Then halve all three (round up), and +1 per Legitimacy
   token for that class (a token also gives +1 immediately when gained).
3. **Political Agenda:** +1 VP per matching policy; discard the card.

**End:** 1 VP per 2 Food / 3 Lux / 3 Health / 3 Edu / 3 Media Influence in storage; **1 VP per 30₩** in the Treasury.

---

## 7. The Politics Table

A = Socialism … C = Neoliberalism for Policies 1–5. A = Nationalism … C = Globalism for 6–7. A bill can move a
policy only **one step**.

| # | Policy | A | B | C |
|---|---|---|---|---|
| 1 | **Fiscal** | 9 public companies; IMF at 2 Loans | 6; IMF at 2 Loans | 3; IMF at 1 Loan (start) |
| 2 | **Labor Market** (min wage) | L3 only | L2+ (start) | any (L1+) |
| 3 | **Taxation** (Tax Multiplier) | base 3, welfare mods ×2 (start) | base 2, mods ×1 | base 1, mods ignored |
| 4 | **Welfare: Health & Benefits** | Public Health free; mod +2 | 5₩; mod +1 (start) | 10₩; mod 0 |
| 5 | **Welfare: Education** | Public Education free; mod +2 | 5₩; mod +1 | 10₩; mod 0 (start) |
| 6 | **Foreign Trade** | tariff Food +10, Lux +6; 0 Business Deals | Food +5, Lux +3; 1 deal (start) | no tariffs; 2 deals |
| 7 | **Immigration** | +0 extra workers | +1 each (start) | +2 each |

### 7.1 Effects when a policy changes
- **Fiscal up** (C→B→A): the State buys the newly opened public companies (2–3p: the whole next row, 60₩,
  paid from the Treasury and taking a Loan if short). Matching unemployed workers are auto-assigned and
  committed. In 2–3p the worker owner picks which company; if both classes can fill it, the Middle Class decides.
- **Fiscal down:** public companies close (the State gets their cost; in 2–3p the bottom row = +60₩). Their
  workers become unemployed, **even if committed**.
- **Labor Market:** every company must lift its wage to the new minimum at once; owners may also adjust other
  wages. A non-player State always uses the minimum.
- **Taxation / Welfare:** recalculate the Tax Multiplier at once. Flip or remove the Welfare tiles. CC/MC may
  re-price Health/Education.
- **Foreign Trade:** move the Import marker; CC/MC may re-price goods. Business Deal counts apply only at the
  next Preparation.

### 7.2 Tax Multiplier
`Multiplier = base(Policy 3) + factor(Policy 3) × [mod(Policy 4) + mod(Policy 5)]`
with base A3/B2/C1, factor A×2/B×1/C×0 and mods A+2/B+1/C0.
Start: 3 + 2×(1+0) = **5**. Example: 3B, 4A, 5A → 2 + 1×(2+2) = **6**.

### 7.3 Income tax per unit (WC: × Population; MC: × other players' companies employing its workers)

| Labor Market ↓ / Taxation → | 3A | 3B | 3C |
|---|---|---|---|
| 2A | 7 | 6 | 5 |
| 2B | 4 | 4 | 4 |
| 2C | 1 | 2 | 3 |

### 7.4 Capitalist Corporate tax (Revenue left after Employment tax)

| Revenue | A | B | C |
|---|---|---|---|
| 5–9 | 1 | 2 | 2 |
| 10–24 | 5 | 5 | 4 |
| 25–49 | 12 | 10 | 7 |
| 50–99 | 24 | 15 | 10 |
| 100–199 | 40 | 30 | 20 |
| 200–299 | 100 | 70 | 40 |
| 300+ | 160 | 120 | 60 |

*(The rows come from the PDF text layer and are confirmed by the rulebook example: 81₩ at 3A pays 24. Check
the two lowest rows against your player aid.)*

---

## 8. Loans, State collapse and the IMF

- **State loans:** a 2–3p State takes Loans automatically when the Treasury runs dry. Each Preparation it pays
  interest and then repays a Loan if it holds more than 50₩.
- **Check IMF** (Production, after Cover Needs; checked only then): if the State has reached Policy 1's Loan
  number (**1 Loan at Fiscal C, 2 at A or B**), it may first repay at **55₩ each**. If it still can't, the **IMF intervenes**:
  1. All pending bills are discarded; each player gets **1 Influence per discarded bill**.
  2. Policies are forced to **1C · 2C · 3A · 4B · 5C · 6B** (Immigration stays B in the rulebook example).
     All effects apply: public companies sold down to 3 (State gets their cost), **all wages to L1**, Tax
     Multiplier recalculated, welfare tiles and Import marker moved. CC/MC may re-price.
  3. This round's WC/MC tax still uses the **old Labor Market** section.
  4. The State repays Loans at 55₩ each as far as it can; the rest are **written off**.
  5. All 3 Legitimacy tracks are halved (round up).
- The rulebook encourages warning everyone when the State is near collapse.

## 9. Component limits
Pieces are limited except money. With no cubes left you can't add more; with no Influence in the supply nobody
can gain it. With no skilled worker of a colour, you can't train into it and immigration gives an unskilled one
instead. With no unskilled worker, add a skilled one of your choice.

## 10. Selected official clarifications (v1.1 FAQ)
- Workers on a struck company can still be reassigned if they are uncommitted; the company can be sold. A strike
  on a company that is now empty gives nothing.
- Mixing committed and uncommitted workers on one company (non-MC) makes them **all uncommitted**.
- Assign Workers can't be used just to re-commit workers who are already in place.
- A Middle Class owner can't pull its own worker out of a company whose WC employee is committed.
- Wages raised by a **policy change** do not commit workers. Raises by a **free action** do.
- Prosperity already at the end of the track: the marker stays and you still score that space's VP.
- Half-price Health/Education cards: half the **total**, rounded up (5 × 5₩ = 25 → 13₩). The State still gets its welfare +1 VP.
- Two-bill cards: each Immediate Vote costs its own Influence, and the bills must be on different policies.
- Privatization permanently removes one public company (max 8 / 5 / 2). A later Fiscal change targets the new section's count.
- Emergency State–type policy changes give **no VP** (VP only from elections).
- Extra Tax, Denial of Free Speech and Higher VAT can't be used if the affected Legitimacy is already at 1.

## 11. Strategy notes (from the rules' own incentives)
- **Working Class:** Prosperity VP grows with the track value, so climb early and keep climbing (it drops 1 each
  round). Health also adds workers (more cubes, more food to buy). Trade Unions are steady VP plus Influence.
  Push policies toward A, cheap public services, high minimum wage.
- **Middle Class:** Prosperity drops by 2 per round, so it needs constant Use actions. Fully staffed companies
  give free Prosperity at scoring, and export sales give 1 VP each. Wins tiebreaks with B policies.
- **Capitalist:** VP is mostly the Wealth table plus the 3-VP bonus for each new high, so a few big Capital
  peaks beat steady small gains. Keep taxes (3C, low Tax Multiplier) and wages (2C) low. Free trade (6C) gives
  more Business Deals and no tariffs. Avoid Loans (−5 VP each at the end).
- **State:** score = the **two lowest** Legitimacy values, so balance matters more than any one peak. Resolve
  Events (penalties hit Legitimacy). Watch the Treasury against Fiscal Policy to avoid the IMF.

---

### Sources
- Official rulebook v1.1 (2023): https://c.tabletopia.com/games/hegemony-lead-your-class-to-victory/rules/hegemony-english-rulebook-v11/en
- Original rulebook v1.0 (2021): https://www.spiele-offensive.de/gfx/cf/hegemony/Hegemony_Rulebook_EN.pdf
- Crisis & Control expansion rulebook: https://c.tabletopia.com/games/hegemony-lead-your-class-to-victory/rules/crisis-control-english-rulebook-v11/en
- RulesPal FAQ: https://rulespal.com/hegemony/faq · Board Game Arena: https://en.boardgamearena.com/gamepanel?game=hegemony
