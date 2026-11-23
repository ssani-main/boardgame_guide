# Root: A Game of Woodland Might and Right: Full Rules Reference

Based on the **official Law of Root, October 13, 2025** (Leder Games, 32 pages), plus the base game's
*Learning to Play* and *Walking Through Root* booklets (both Oct 15, 2020). Section numbers like **(4.3.1)**
point to the Law. Where the Law and *Learning to Play* differ, the Law wins (1.1.1).

- **Scope: base game only.** Marquise de Cat, Eyrie Dynasties, Woodland Alliance, Vagabond (Thief, Tinker,
  Ranger), the Autumn and Winter maps and the 54-card base deck. Riverfolk, Underworld, Marauder,
  Homeland, hirelings, landmarks and Clockwork bots are **not** covered.
- **Simulator:** `sim/` plays complete games with one bot per faction. Use `python sim/run.py --players 4 --seed 3` for
  one game and `python sim/test_rules.py` for the rule checks.
- **Card texts:** every base deck card, Eyrie leader, Vagabond character and quest is in `cards/`. They come
  from Leder Games' official card library (cards.ledergames.com). Copy counts are worked out in `cards/deck.md`.
- **Board numbers:** building costs, victory point tracks and draw bonuses are printed on the faction boards
  and not written in the Law. Section 16 lists them, marked **(board)**. Check them against your own boards.
- Designer: Cole Wehrle. Art: Kyle Ferrin. Publisher: Leder Games (2018).
- 2–4 players (base box), asymmetric, 60–90 minutes. First to **30 victory points** wins.
- A digital version exists (Direwolf Digital, *Root* on Steam and mobile).

---

## 1. The idea in one paragraph

The Woodland is twelve clearings joined by paths. Each player runs a faction that wants something different
from it. The **Marquise de Cat** has occupied the forest and builds an industrial empire fed by wood. The
**Eyrie Dynasties** want their old domain back and must follow an ever-growing **Decree** of orders, or
fall into turmoil. The **Woodland Alliance** spreads **sympathy** among the oppressed creatures and erupts in
revolts. The **Vagabond** wanders between them all, trading, questing and picking fights. Everyone shares one
deck of cards in three clearing suits (fox, rabbit, mouse) plus wild birds, and everyone races to 30 points.

## 2. Factions and player counts

| Faction | Colour | Style | Reach (5.2) | Scores by |
|---|---|---|---|---|
| Marquise de Cat | orange | militant, starts everywhere | 10 | placing buildings (sawmills, workshops, recruiters) |
| Eyrie Dynasties | blue | militant, programmable | 7 | roosts on the map, every Evening |
| Vagabond | grey | insurgent, a single pawn | 5 | aiding factions, hostile kills, quests |
| Woodland Alliance | green | insurgent, slow start | 3 | placing sympathy tokens |

**Reach.** Choose factions whose reach adds up to at least the total for your player count (5.2). Groups
can play any mix with 17+ reach.

| Players | 2 | 3 | 4 |
|---|---|---|---|
| Minimum total reach | 17+ | 18+ | 21+ |

With the base box this means: 2 players = **Marquise + Eyrie** (17) is the only pair that reaches 17;
3 players = Marquise + any two (Eyrie + Vagabond + Alliance is only 15); 4 players = all four (25).
The older *Learning to Play* booklet also lists 2-player games with the Alliance or Vagabond and a 3-player
Eyrie + Alliance + Vagabond game. Those fall below even the Law's 17 floor for "adventurous" groups; they are
*Learning to Play* suggestions only.

**Faction combinations** (*Learning to Play*, p. 22; ★ = marked with a torch as recommended for new players):
- **2 players:** ★ Eyrie vs Marquise is the ideal learning game; the Eyrie must grow explosively to keep the Marquise
  in check. Alliance vs Marquise or Eyrie lets Alliance players practise in a hard spot. Eyrie vs Vagabond makes the
  Eyrie build a Decree that survives nimble attacks.
- **3 players:** ★ Marquise + Eyrie + Vagabond and ★ Marquise + Eyrie + Alliance: the Marquise–Eyrie fight defines the
  game. Eyrie + Alliance + Vagabond: the Vagabond has a natural friend in the Alliance; both should watch for dominance.
- **4 players:** ★ all four. With the map full of interlopers, the Marquise must keep policing the Woodland; if she
  loses control she will not easily regain it.
- **2-player games:** remove the 4 dominance cards. The booklet suggests playing twice, swapping factions,
  and adding both scores.

## 3. Components (C.1)

- **Board:** Autumn map on one side, Winter map on the other.
- **Cardboard:** 28 buildings (7 roosts, 6 sawmills, 6 workshops, 6 recruiters, 3 bases), 19 tokens
  (10 sympathy, 8 wood, 1 keep), 12 clearing suit markers (4 per suit), 4 ruins, 4 victory point markers,
  3 relationship markers, 23 items (4 boots, 4 swords, 4 bags, 3 hammers, 3 tea, 2 coins, 2 crossbows, 1 torch).
- **Wood:** 55 warriors (25 Marquise, 20 Eyrie, 10 Alliance), 1 Vagabond pawn.
- **Cards:** 54 shared deck cards, 16 faction overviews, 4 Eyrie leaders, 2 Loyal Viziers, 3 Vagabond characters,
  15 quests, 4 walkthrough cards.
- **Other:** 2 battle dice (twelve-sided, faces 0–3, as pictured in *Learning to Play*), 4 faction boards.

**Piece types** (Glossary, Appendix G):
- **Warriors** (wooden figures) move, battle and count for rule.
- **Buildings** (square cardboard) fill slots and count for rule.
- **Tokens** (round cardboard: wood, sympathy, keep) do **not** fill slots and do **not** count for rule.
- **The Vagabond pawn** moves and battles but is not a warrior: it never rules and cannot be removed.
- **Items** belong to no faction. They are not faction pieces and cannot be enemy pieces.
- **Ruins** fill the slots marked "R" until the Vagabond explores them empty.

## 4. Key concepts

### 4.1 Cards (2.1)
- One **shared deck**, one shared discard pile. If the deck runs out, shuffle the discards at once into a new deck.
- Every card has a **suit**: fox, rabbit, mouse or **bird**. Most cards can also be **crafted** (section 8).
- **Birds are wild** (2.1.1). A bird can stand in for any suit. Two edge cases:
  - If you are *forced* to discard or give a non-bird suit, birds count as that suit and must go if you have them.
  - If something asks for a *bird* card, a non-bird card cannot stand in.
- **Ambush cards** (5: one fox, one rabbit, one mouse, two birds) cannot be crafted. Use one when defending (4.3.1).
- **Dominance cards** (4, one per suit) cannot be crafted. They change how you win (section 7).
- **Play area** (2.1.4): crafted persistent effects and activated dominance cards sit next to your board.
  They are not in your hand.
- **Hidden information:** the number of cards in hand is public; contents are not. Face-up piles (discard)
  may be searched; the deck may not. Players may only give cards when an effect says so (1.3.2).
- **Hand limit:** at the end of Evening every faction discards down to **five** cards.

### 4.2 The map (2.2–2.4)
- **Clearings** (12) are linked by **paths**. Two clearings are **adjacent** if a path links them.
- Each clearing has a **suit** (fox, rabbit, mouse) and a number of **building slots**.
- **Ruins** start in the four slots marked "R".
- **Forests** are the areas enclosed by paths and clearings. Only the Vagabond can enter them.
- **Rivers** do nothing in the base game unless an effect says so (2.3). On the Winter map the river splits
  forests like a path (M.2.1).
- The four **corner clearings** matter for setup and bird dominance.
- **Autumn map facts:** 12 clearings (4 per suit), 23 building slots (four of them start under ruins), 18 paths
  and 7 forests. Corners: top-left fox (1 slot), top-right mouse (2), bottom-right rabbit (2), bottom-left rabbit (1).

### 4.3 Rule (2.5)
You **rule** a clearing if you have more **warriors plus buildings** there than each other player.
Tokens and pawns do not count. **A tie means no one rules**, except that the Eyrie win ties where they have
a piece (Lords of the Forest, 7.2.2).

Rule decides who can move (section 9), where the Marquise and Eyrie can build, and dominance wins.

## 5. Golden rules (section 1)

- **Precedence:** a card beats the Law; the Law beats *Learning to Play*; a faction rule beats a general rule
  when both cannot be followed (1.1.1).
- **"Cannot" is absolute** unless something explicitly overrides it (1.1.2).
- **Unclear order or chooser:** the player whose turn it is decides (1.1.3).
- **Deals are allowed but not binding.** Actions never need consent (1.3).
- **No interrupts:** you cannot break into an action, ability or persistent effect unless it says so (1.4.2).
- **Piece limits:** you are limited to the pieces in the box. Never use proxies (1.5.1). If you can't
  place, take or remove the full number, do as many as you can, but you still pay costs in full (1.5.4).
- **Forced actions** (for example "force a player to move") are resolved as if that player chose them, with their
  abilities (1.5.5).

## 6. Turn structure and victory

### 6.1 Turns (1.4)
Each turn has three phases: **Birdsong → Daylight → Evening**. "At start of" effects come before everything
else in that phase; "at end of" effects come after everything else. Then the next player clockwise goes.
Once you start the last step of your turn, you can only take "end of Evening/turn" actions (1.4.3).

### 6.2 Victory (3.1)
The first player to reach **30 victory points** wins **immediately**, even in the middle of someone's turn. On a
simultaneous tie, the tied player closest clockwise to the current player (including the current player) wins.

### 6.3 Points anyone can score (3.2)
- **+1** for each **enemy building or token** you remove, in battle or any other way (3.2.1).
- **Crafting an item:** score the points printed on the card (3.2.2). The Eyrie score only 1 (Disdain for Trade).
- Plus each faction's own engine (sections 12–15).

## 7. Dominance (3.3)

- **Activate:** in your Daylight, with **at least 10 points**, place a dominance card from your hand in your
  play area. Remove your score marker: you can never score points again.
- **Win condition:** you win if you **rule three clearings of that suit** at the **start of your Birdsong**.
  **Bird dominance:** rule **two opposite corner clearings** at the start of your Birdsong.
- An activated dominance card stays forever and cannot be swapped.
- **Spending for suit:** a dominance card can be spent like any card of its suit. When a dominance card would go
  to the discard pile, it goes **near the map** instead. In Daylight anyone can **take** an available dominance
  card by spending a card of its suit (a bird dominance needs a bird card).
- **Vagabond coalition** (9.2.8): the Vagabond cannot use dominance normally. In 4+ player games he plays it to
  join the player with the **fewest points** (he picks if tied). He stops scoring; if his partner wins, he wins too.
  He may even ally with a Hostile faction; their marker then moves to Indifferent.
- **2 players:** dominance cards are removed in setup.

## 8. Crafting (4.1)

- To craft a card, **activate crafting pieces** whose clearing suits match the icons in the card's
  bottom-left corner. Each crafting piece works **once per turn**. A **three-colour "?"** icon means any suit.
  - Marquise: **workshops**. Eyrie: **roosts**. Alliance: **sympathy tokens**. Vagabond: exhaust **hammers**
    (his clearing must match every icon).
- **Immediate effect** (paper box): resolve it, then discard the card. If it shows an **item**, take that item
  from the item supply on the map into your Crafted Items box and score the points. **If the supply has no such
  item left, you cannot craft the card.**
- **Persistent effect** (stone box): place it in your play area. You cannot have two identical persistent effects.
- Items in your Crafted Items box do nothing for most factions. They are trade goods: the Vagabond can take them
  when he Aids you.

**Item supply at setup** (5.1.5): 2 boots, 2 bags, 1 crossbow, 1 hammer, 2 swords, 2 tea, 2 coins = 12 items.

## 9. Movement (4.2)

- A **move** takes any number (at least one) of your warriors from one clearing to **one adjacent** clearing.
- **You must rule the origin, the destination, or both.**
- The same pieces may move any number of times. Several moves may move the same or different groups.
- Exceptions: the Vagabond is **Nimble** (moves regardless of rule). The keep blocks other factions from
  **placing**, not moving.

## 10. Battle (4.3)

Choose a clearing with your warriors (or the Vagabond pawn) and an enemy there as defender. You need no rule.

1. **Defender may ambush** (4.3.1). Play an ambush card matching the clearing (or a bird ambush).
   - The **attacker may foil it** with their own matching ambush card: the defender's ambush is discarded with
     no effect.
   - Otherwise the defender deals **2 hits at once**, then discards the ambush. If no attacking warriors or pawn
     remain, the battle ends.
2. **Before-roll effects** (attacker picks order).
3. **Roll both dice** (4.3.3). The **attacker deals the higher** roll, the **defender the lower**. The Alliance
   as defender reverses this (Guerrilla War). Each side's rolled hits are capped by **its warriors in the
   clearing** (the Vagabond: his undamaged swords).
4. **After-roll effects** (Armorers, Sappers, Brutal Tactics…).
5. **Count hits** (4.3.5). **Extra hits** ignore the warrior cap. A **defenseless** defender (no warriors in
   the clearing) takes **1 extra hit**.
6. **Deal hits** (4.3.6). Each hit removes one enemy piece. The side taking hits chooses which, but **all
   warriors go before any buildings or tokens**. Score **+1** per enemy building or token removed.

Each die shows 0–3, so rolled hits per side are at most 3 (plus extra hits).

## 11. Setup

### 11.1 Standard setup (5.1)
1. **Factions and seats.** Assign factions; pick the first player and seating at random. Take your board and pieces.
2. **Score markers** on 0.
3. **Hands.** 2 players: remove the 4 dominance cards. Shuffle; everyone draws **3** cards.
4. **Ruins** in the four "R" slots.
5. **Item supply:** 2 boots, 2 bags, 1 crossbow, 1 hammer, 2 swords, 2 tea, 2 coins on the board's item spaces.
6. **Overview cards and the 2 battle dice** near the map.
7. **Faction setup in order: Marquise (A), Eyrie (B), Alliance (C), Vagabond (D).**

| Faction | Setup (Law) |
|---|---|
| **Marquise** (6.3) | Supply: 25 warriors, 8 wood. Keep in **any corner clearing**. **1 warrior in every clearing except the diagonally opposite corner.** Place 1 sawmill, 1 workshop, 1 recruiter in the keep clearing and/or adjacent clearings. Put the other 5 of each building on the tracks, right to left (leftmost space stays empty). |
| **Eyrie** (7.3) | Supply: 20 warriors. **1 roost + 6 warriors** in a corner that is not another player's start corner, diagonally opposite one if possible. Choose 1 of 4 **leaders**; the other 3 face up beside you. Tuck the 2 **Loyal Viziers** into the Decree columns named on the leader. Remaining 6 roosts on the track, right to left. |
| **Alliance** (8.3) | Supply: 10 warriors. 3 bases in the Bases box. 10 sympathy tokens on the track. Draw **3 cards face down as supporters**. No pieces on the map. |
| **Vagabond** (9.3) | Choose a **character** (Thief, Tinker, Ranger). Pawn in **any forest**. Shuffle quests, deal **3 face up**. **Ruins:** take the 4 ruins and the 4 "R" items (bag, boot, hammer, sword), put one item under each ruin, shuffle, put the ruins back in the empty "R" slots. Take the character's "S" starting items (tracks for tea, coins, bags; the rest in the Satchel). Relationship markers for each other faction on **Indifferent**. |

### 11.2 Advanced setup (Appendix A, short)
- **Map:** on any non-Autumn map, shuffle the 12 suit markers face down and put one on each clearing.
- **Hands:** everyone draws **5** and keeps **3**, shuffling the other 2 back.
- **Faction draft** uses setup cards from the Marauder/Homeland expansions, so it is outside base-game scope.

### 11.3 The Winter map
The back of the board. **Before setup, deal the 12 suit markers face down at random onto the clearings**, then
flip them (*Learning to Play* p. 23; the Law puts this in Advanced Setup, A.1). Ruins sit in different slots than on Autumn. **The river divides forests like a path** (M.2.1).
*Learning to Play* recommends it only for experienced players: random suits can help or hurt some factions.

## 12. Marquise de Cat (section 6)

**Goal:** build sawmills, workshops and recruiters. Every building scores the points uncovered on her board,
more for each further building of the same type. She starts on almost the whole map but has to defend a long
supply line of wood.

**Abilities**
- **Crafting** (6.2.1): activates **workshops** during Daylight.
- **The Keep** (6.2.2): only the Marquise can **place** pieces in the keep clearing (others may still move in and
  battle). If the keep token is removed, it never comes back.
- **Field Hospitals** (6.2.3): whenever Marquise warriors are removed from a clearing, she may spend **one card
  matching that clearing** to put them all back at the keep. This works only while the keep is on the map.

**Birdsong:** place **1 wood at each sawmill**.

**Daylight:** first craft with workshops. Then take **up to 3 actions**, plus **1 extra action for each bird card
spent** (Hawks for Hire), in any order and mix:
- **Battle.**
- **March:** up to two moves.
- **Recruit:** 1 warrior at **each** recruiter. **Once per turn.**
- **Build:** choose a clearing you **rule** with an open slot and a building type; you place the leftmost
  building of that type. **Pay its wood cost** (top of its column) from the chosen clearing or any clearings you
  rule that **connect to it through clearings you rule**. Score the points on the uncovered space.
- **Overwork:** spend a card matching a sawmill's clearing to place 1 wood there.

**Evening:** draw **1 + uncovered draw bonuses**, then discard down to 5.

**Play tips** (Learning to Play / overview card): sawmills feed everything, workshops craft, recruiters bring
warriors and card draw. Protect connected chains of ruled clearings so wood can reach build sites. Her keep is
the weak spot: destroying it ends Field Hospitals.

## 13. Eyrie Dynasties (section 7)

**Goal:** spread **roosts**. Every Evening they score the rightmost empty space of the Roosts track, so the more
roosts on the map, the more they score each turn. Their actions come from the **Decree**, which only grows. If they
cannot carry it out, they fall into **turmoil**.

**Abilities**
- **Crafting** (7.2.1): activates **roosts**, before resolving the Decree.
- **Lords of the Forest** (7.2.2): the Eyrie **rule tied clearings** if they have at least one piece there.
- **Disdain for Trade** (7.2.3): crafted items score only **1 point** (bonuses from other effects still apply).

**Birdsong**
1. **Emergency Orders:** if your hand is empty, draw 1.
2. **Add to the Decree:** you **must** add 1 or 2 cards from your hand to any Decree columns (Recruit, Move, Battle,
   Build). **At most one of them may be a bird.**
3. **A New Roost:** if you have no roosts on the map, place a roost and 3 warriors in a clearing with the **fewest
   warriors** where they all fit.

**Daylight**
1. **Craft** with roosts.
2. **Resolve the Decree**, left column to right. For **every** card you must do that column's action in a clearing
   matching the card's suit (birds match any clearing):
   - **Recruit:** 1 warrior in a matching clearing with a roost.
   - **Move:** move at least one warrior from a matching clearing.
   - **Battle:** battle in a matching clearing.
   - **Build:** place a roost in a matching clearing you **rule** that has **no roost**.
   If any single action cannot be fully done, you fall into **turmoil** at once. An empty column is simply skipped
   (*Walking Through Root*).

**Evening**
1. **Score** the rightmost empty space on the Roosts track.
2. **Draw 1 + uncovered draw bonuses**, discard down to 5.

**Turmoil** (7.7), in order:
1. **Humiliate:** lose **1 point per bird card** in the Decree (Viziers included).
2. **Purge:** discard all Decree cards **except the two Loyal Viziers**.
3. **Depose:** flip your leader face down and set it aside. Choose a new one from the face-up leaders, and tuck the
   Viziers where the new leader says. If none are face up, flip all four face up first (A New Clutch).
4. **Rest:** end Daylight and go to Evening (you still score roosts and draw).

**Leaders** (7.8)

| Leader | Viziers start on | Ability |
|---|---|---|
| Builder | Recruit + Move | Ignore Disdain for Trade when crafting (full item points). |
| Charismatic | Recruit + Battle | Each Recruit places **2** warriors. |
| Commander | Move + Battle | As attacker, deal **1 extra hit**. |
| Despot | Move + Build | Removing at least one enemy building or token in battle scores **1 extra point**. |

**Play tips:** every card added is a promise you must keep next turn. Birds make the Decree flexible but cost points
in turmoil. Opponents break the Eyrie by emptying the clearings of a suit they need, or by taking their roosts.

## 14. Woodland Alliance (section 8)

**Goal:** place **sympathy tokens**; each one scores the points it uncovers on the board. The Alliance spends
**supporters** (cards face down on its board) to spread sympathy and to **revolt**. Revolts wipe out a clearing and
plant a **base**, which lets it train **officers** for military operations.

**Abilities**
- **Crafting** (8.2.1): activates **sympathy tokens**.
- **Guerrilla War** (8.2.2): as **defender**, the Alliance deals the **higher** roll and the attacker the lower.
- **Supporters stack** (8.2.3): face-down cards spent only **for their suit**. They do not count against hand size.
  **Without any base on the map the stack holds at most 5**; extra cards are discarded. With a base it is unlimited.
- **Removing a base** (8.2.4): the Alliance discards **all supporters matching the base's suit (birds too)** and
  removes **half its officers, rounded up**. With no bases left and more than 5 supporters, discard down to 5.
- **Sympathy limit:** one sympathy per clearing. 10 tokens total.
- **Outrage** (8.2.6): when **another player removes a sympathy token or moves warriors into a sympathetic
  clearing**, they must give the Alliance a **card matching that clearing** (birds count) for the Supporters stack.
  With no matching card they **show their hand**, and the Alliance draws a card from the deck as a supporter instead.

**Birdsong** (in order, each any number of times)
1. **Revolt:** choose a **sympathetic** clearing **without a base** whose suit matches a base still on your board.
   Spend **2 supporters of that suit**. Remove **all enemy pieces** there (score +1 per building/token removed),
   place the base (it is a building, so it needs an open slot once the enemy pieces are gone, 2.2.3), place **warriors equal to sympathetic clearings of that suit**, and **1 officer**.
2. **Spread Sympathy:** choose an unsympathetic clearing **adjacent to a sympathetic one** (any clearing if none are
   sympathetic). Spend supporters of its suit; how many is printed above the next token. **Martial Law:** +1 supporter
   if another player has **3 or more warriors** there. Place the token and score its points.

**Daylight** (any order and number)
- **Craft** with sympathy tokens.
- **Mobilize:** add a card from hand to the Supporters stack.
- **Train:** spend a card matching a **base on the map** to put a warrior in the Officers box (an officer).

**Evening**
1. **Military Operations:** take actions up to your **number of officers**: **Move**, **Battle**, **Recruit** (1 warrior in a
   clearing with a base) or **Organize** (remove 1 Alliance warrior from an unsympathetic clearing to place sympathy there
   and score it; no supporters needed).
2. **Draw 1 + uncovered draw bonuses**, discard down to 5.

**Play tips:** the first sympathy is cheap and can go anywhere. Outrage punishes anyone who marches through sympathy.
Revolts are the comeback move: a revolt in a crowded clearing can remove several buildings at once.

## 15. Vagabond (section 9)

**Goal:** score by **improving relationships** (Aid), **removing warriors of Hostile factions**, **completing quests**,
exploring ruins and crafting. He is one pawn that plays every side.

### 15.1 Abilities
- **Crafting** (9.2.1): exhaust **hammers**, one per crafting icon. His **clearing** must match all icons. He ignores the
  once-per-turn limit. A crafted item can go straight into his pack.
- **Lone Wanderer** (9.2.2): not a warrior, never rules, **cannot be removed**. If an effect removes all enemy pieces in
  his clearing (revolt, Favor card), he **damages 3 items** instead.
- **Nimble** (9.2.3): moves regardless of rule.
- **Defenseless** (9.2.4): as defender he is defenseless if he has **no undamaged sword**.
- **Battle cap** (9.2.6): his maximum rolled hits = his **undamaged swords** (face up or down) in the Satchel.
- **Taking hits** (9.2.7): each hit **damages** one undamaged item (to the Damaged box). No items left: extra hits are ignored.
- **Forests** (9.2.10): Slip can enter forests; normal moves can only leave a forest to an adjacent clearing.

### 15.2 Items (9.2.5)
| Item | Used for |
|---|---|
| **Boot** | Move (one boot per move; +1 into a clearing with Hostile warriors) |
| **Sword** | Battle; also caps his rolled hits |
| **Crossbow** | Strike |
| **Hammer** | Repair, Craft |
| **Torch** | Explore, special action |
| **Tea** | Track: refresh 2 extra items per face-up tea in Birdsong |
| **Coins** | Track: +1 card draw per face-up coins in Evening |
| **Bag** | Track: +2 item limit per face-up bag |

Items are **face up** (ready) or **face down** (exhausted), and **undamaged** or **damaged**. Tea, coins and bags sit on their
three tracks (max 3 each) while face up. Exhausting one moves it to the Satchel.

### 15.3 Relationships (9.2.9)
Each other faction has a marker on his Relationships chart: **Hostile** box, then **Indifferent → … → Allied**.
- **Improve:** Aid a non-Hostile faction the number of times printed between its space and the next **in one turn**.
  Move the marker one step right and score the points on the new space.
- **Allied:** each further Aid to that faction scores **2 points**. When he moves, he may take Allied warriors along. As
  attacker he may treat one Allied faction's warriors in the clearing as his own (cap = their warriors + his undamaged
  swords) and take hits on them. If he takes **more hits on Allied warriors than on his own items** in that battle, that
  faction turns Hostile.
- **Hostile:** removing a warrior of a non-Hostile faction makes it **Hostile**. Hostile factions cannot be improved by
  Aid. **Infamy:** +1 point for each piece of a Hostile faction he removes in battle on his turn (not the warrior that
  made them Hostile). Moving into a clearing with Hostile warriors costs an extra boot.

### 15.4 Turn
**Birdsong**
1. **Refresh:** flip up **3 exhausted items + 2 per face-up tea** on the track (tea flipped up in this step doesn't count).
2. **Slip:** may move to an adjacent clearing **or forest** for free (no boot, even into a clearing with Hostile warriors).

**Daylight:** exhaust items for actions, any order and number:
- **Move:** 1 boot (+1 boot if Hostile warriors are at the destination). He cannot enter forests this way.
- **Battle:** 1 sword.
- **Explore:** 1 torch. Take the item under a ruin in his clearing and **score 1**. An empty ruin is removed (the slot opens).
- **Aid:** exhaust **any** item and give a card **matching his clearing** to a player with pieces there. He may take one
  item from their Crafted Items box. Check the relationship.
- **Quest:** in a clearing matching a quest's suit, exhaust its two listed items. Then **score 1 per completed quest of
  that suit (this one included)**, or **draw 2 cards**. Replace the quest from the quest deck.
- **Strike:** 1 crossbow. Remove one enemy warrior in his clearing, or another piece if they have no warriors there.
- **Repair:** 1 hammer. Move a damaged item back to the Satchel, keeping its side.
- **Craft:** hammers as crafting pieces.
- **Special action:** see his character.

**Evening**
1. **Rest:** if in a **forest**, repair **all** damaged items and flip them face up.
2. **Draw 1 + 1 per face-up coins.**
3. **Discard down to 5.**
4. **Item limit:** if Satchel + Damaged box hold more than **6 + 2 per face-up bag**, remove the extra items from the game.

### 15.5 Characters (Appendix V)
| Character | Starting items | Special action (exhaust a torch) |
|---|---|---|
| **Thief** | boot, torch, tea, sword | **Steal:** take a random card from a player with pieces in his clearing. |
| **Tinker** | boot, torch, bag, hammer | **Day Labor:** take a card from the discard pile matching his clearing (a bird always works). |
| **Ranger** | boot, torch, crossbow, sword | **Hideout:** repair 3 items, then end Daylight and go to Evening. |

**Play tips** (overview card): crafting an item he wants is an easy way to win his favour, but if he gets too strong,
hit him when he is light on swords. A sound beating sends him to the forest for a turn of repairs.

## 16. Faction board numbers (board)

These are printed on the faction boards, not in the Law. The roost and sympathy values agree with the
scoring in *Walking Through Root* (2nd roost scores 1, 3rd roost scores 2; 2nd sympathy scores 1); the rest is
copied from the board layout as commonly printed. **Check them against your own boards.**

**Marquise** — cost row is the same for each building type; the first building of each type is placed in setup.

| Building number | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Wood cost | (setup) | 1 | 2 | 3 | 3 | 4 |
| Sawmill VP | (setup) | 1 | 2 | 3 | 4 | 5 |
| Workshop VP | (setup) | 2 | 2 | 3 | 4 | 5 |
| Recruiter VP | (setup) | 1 | 2 | 3 | 3 | 4 |

Card draw bonuses sit under some recruiter spaces; each uncovered one adds a card in Evening.

**Eyrie** — score the rightmost empty space each Evening (one roost starts on the map):

| Roosts on map | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| Evening VP | 0 | 1 | 2 | 3 | 4 | 4 | 5 |

Some roost spaces hide card draw bonuses.

**Alliance** — the sympathy track (cost in supporters of the clearing's suit, VP when placed):

| Token | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Cost | 1 | 1 | 1 | 2 | 2 | 2 | 3 | 3 | 3 | 3 |
| VP | 0 | 1 | 1 | 1 | 2 | 2 | 3 | 4 | 4 | 4 |

Bases in the Bases box cover draw bonuses: placing a base uncovers its bonus.

**Vagabond** — Relationships chart: Indifferent → 1 Aid (+1 VP) → 2 Aids (+2 VP) → 3 Aids to **Allied** (+2 VP); each later
Aid to an Allied faction +2 VP. All three steps are confirmed by the board picture on *Learning to Play* p. 19.

## 17. Common mistakes

- **Moving without rule.** You need rule at the start **or** the end. Moving into a tied clearing from a tied clearing is illegal.
- **Tokens and pawns don't rule.** Wood, sympathy, the keep and the Vagabond never count for rule.
- **Warriors die first.** Buildings and tokens can only be hit once all of that side's warriors in the clearing are gone.
- **Defenseless = +1 hit,** not "automatic win". The roll still happens, capped by the attacker's warriors.
- **Ambush is defence only,** and the attacker can foil it with another matching ambush (birds match anything).
- **Crafting needs the item in the supply.** If both swords are gone, Sword cards can only be spent for suit.
- **Field Hospitals costs a matching card** per clearing, not per warrior, and stops if the keep is lost.
- **Eyrie: at most one bird per Birdsong** added to the Decree, and turmoil hits **every** bird in it, Viziers included.
- **Alliance supporters are capped at 5** until the first base is on the map.
- **Outrage triggers on removing sympathy (also in battle) or moving warriors in.** Warriors already standing
  in a clearing when sympathy arrives cause nothing.
- **Vagabond Aid needs a card matching his clearing,** and only Aids in the **same turn** add up toward the next step.
- **Dominance needs 10 points to play** and ends all scoring. You win at the start of your own Birdsong, not when you take the clearing.

## 18. Sources

- *The Law of Root*, October 13, 2025 — ledergames.com/pages/resources ("Law of Root, Oct 2025").
- *Learning to Play* and *Walking Through Root*, Oct 15, 2020 — same page.
- Card texts and images: Leder Card Library (cards.ledergames.com; data at github.com/LederCards/cards).
- Base deck suit totals (14 bird, 14 fox, 13 mouse, 13 rabbit): BoardGameGeek wiki.
