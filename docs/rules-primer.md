# Imperial Assault rules primer (campaign mode)

A condensed version of the IA core rules, focused on what matters for designing and
balancing content. Sources: `reference/imperial_assault_rules_reference_guide.pdf`
(RRG, the authoritative rules) and `reference/swi01_learn_to_play_v17.pdf`. Skirmish
mode is ignored because this project only uses the campaign.

Anything marked **[unverified]** is from memory and not found in the reference PDFs.

IA terminology is used throughout. Rebel = hero side, Imperial = Adversary side.

## Precedence

- The RRG beats the Learn to Play booklet. Card text beats the RRG. Mission rules beat
  card text.
- The word **"cannot"** is absolute and can't be overridden.
- Timing: mission rules resolve first, then the Imperial player, then the Rebels. During
  an attack, the attacker's effects resolve before the defender's.

## Round structure

- Each round has an **Activation Phase**, then a **Status Phase**.
- In the Activation Phase, the sides alternate activations and the Rebels go first. A
  hero activates alone. The Imperial player activates one **group** (all figures on one
  Deployment card), one figure at a time.
- **Two heroes:** each hero gets 2 activation tokens, and neither can take a second
  activation until both have taken their first. **Three heroes:** one hero gets a second
  token each round, and it rotates. **Four heroes:** one activation each.
- When one side runs out of activations, the other side takes all its remaining
  activations.
- **Status Phase:**
  1. The Imperial player gains threat equal to the mission's threat level.
  2. Ready all exhausted cards.
  3. The Imperial player may deploy and reinforce.
  4. Resolve end-of-round effects.
  5. Advance the round counter.

## Activations and actions

- A figure gets **2 actions** per activation: Move, Attack, Interact, Rest (heroes only),
  or a Special action (marked with the action icon; costs one action per icon).
- The same action can be taken twice, with two exceptions:
  - **Non-hero figures attack at most once per activation.** This includes special
    actions that contain an attack. Attacks granted outside the figure's own activation
    don't count toward this limit.
  - Each special action can be used once per activation.
- **Heroes can attack twice per activation.** This is the biggest structural difference
  between heroes and deployment figures.
- **Move** gives movement points equal to Speed. Points can be split before and after the
  other action, and any left over are lost when the activation ends.
- Entering a space with a hostile figure or difficult terrain costs +1 movement point.
- "Move X spaces" ignores movement costs.
- A hero's Item and Class cards ready at the start of that hero's activation. Imperial
  cards and activation tokens ready in the Status Phase.

## Attacks

Weapon dice and surge abilities are on a hero's weapon Item card, or on a Deployment
card for other figures.

1. **Declare target.** A melee attack targets an adjacent figure (up to 2 spaces with
   Reach). A ranged attack targets any figure in line of sight. A hero also declares
   which weapon they're using.
2. **Roll dice.** Both sides roll at once. Pool-adding effects must be used before this
   step.
3. **Rerolls.** Each die can be rerolled at most once per attack, by anyone.
4. **Apply modifiers.** Add or remove icons and accuracy, and resolve conversions. Each
   **evade cancels one surge.**
5. **Spend surges.** Each surge ability can be used **once per attack**. A hero may spend
   1 surge to recover 1 strain, once per attack. Unspent surges are lost.
6. **Check accuracy** (ranged only). Accuracy must be at least the distance to the
   target, and at least 1 even against an adjacent target. Otherwise the attack misses.
7. **Calculate damage.** Damage minus blocks is suffered.

- **Dodge** (white die) makes the attack **miss**. A miss deals 0 damage and cancels
  anything that needs the target to suffer damage, though effects like Recover still
  happen.
- Blast, Cleave and condition keywords need the target to suffer at least 1 damage, and
  apply after the attack.
- Damage from outside an attack (for example "suffers 2 damage") can't be blocked and
  isn't an attack.

### Dice

Face data is in `data/dice.yaml`. Averages per die:

| Die | Damage | Surge | Accuracy | Notes |
|---|---|---|---|---|
| Red | 2.17 | 0.17 | 0 | Raw damage. No accuracy, so melee only in practice. |
| Green | 1.33 | 0.50 | 1.67 | All-rounder. Short range. |
| Blue | 1.17 | 0.33 | 3.17 | Long range. |
| Yellow | 0.83 | 0.83 | 1.00 | Surges and utility. |

| Die | Block | Evade | Notes |
|---|---|---|---|
| Black | 1.50 | 0.17 | Tough. Rarely cancels surges. |
| White | 0.50 | 0.50 | Evasive. 1 face in 6 is a dodge, which is an automatic miss. |

Typical weapons roll 2 dice (for example red+yellow, or blue+green). Heroes roll 1
defense die. Large or elite figures sometimes roll 2.

## Keywords

- **Pierce X:** ignore up to X blocks. Stacks with other Pierce.
- **Blast X:** each figure *and object* adjacent to the target suffers X damage,
  **including friendly figures**. Blocks don't reduce it. Conditions don't spread to
  these figures.
- **Cleave X:** one other hostile figure the attacker could also target suffers X damage.
  Blocks don't reduce it.
- **Reach:** melee attacks reach up to 2 spaces. Needs line of sight but no accuracy.
- **Recover X:** remove X damage or strain. As a surge ability, it works even on a miss.
- **Massive:** can enter blocking and impassable terrain and hostile figures' spaces at
  no extra cost, and pushes figures aside. In a campaign it can't enter interior spaces.
- **Mobile:** ignores extra movement costs and can end in impassable or blocking
  terrain.
- **Condition keywords** (Bleed, Stun, Focus, ...): a harmful condition is applied to
  the target, and a beneficial one to the attacker. Either way the target must suffer
  at least 1 damage.

## Conditions

A figure can't have two copies of the same condition. Heroes track conditions with cards
and other figures with tokens.

These are the IA condition rules (text supplied by the designer). Stun, Bleed and Focus
are from the core game; Weaken and Hidden are from expansions.

- **Stun** (harmful, IA core): you can't attack or voluntarily leave your space. You can
  spend an action to remove it.
- **Bleed** (harmful, IA core): whenever you take an action other than removing this,
  you suffer 1 strain. You can spend an action to remove it.
  - Non-heroes suffer damage instead of strain, so Bleed is 1 damage per action for
    them.
- **Focus** (beneficial, IA core): add a green die to your next attack or attribute
  test, then discard it. It can't be saved for later.
- **Weaken** (harmful, IA expansion): −1 evade on your defense results and −1 surge on your attack
  results. It's discarded after you attack.
  - There's no action to remove it. It lasts until your next attack, or indefinitely if
    you never attack.
  - Acolyte Jin's *Toxicity* adds −1 block while an ally attacks a Weakened enemy.
- **Hidden** (beneficial, IA expansion): ranged attacks against you get −2 accuracy, and your attacks
  get +1 surge. It's discarded after you attack.

## Heroes

- A hero has **Health**, **Endurance** (maximum strain), **Speed**, a defense die, and
  three **attributes** with test dice. The hero sheet has two sides: **healthy** and
  **wounded**.
- **Wounded:** at 0 Health a healthy hero flips to wounded. All damage is cleared,
  abilities are reduced, and stats are usually lower. A wounded hero who is defeated
  **withdraws** for the rest of the mission but still gets rewards.
  - Heroes don't die. The Imperial side usually wins missions by wounding every hero or
    by running out the clock.
- **Strain:**
  - Heroes pay strain costs for many abilities, and can take 1 strain for +1 movement
    point up to twice per activation.
  - Strain can't voluntarily exceed Endurance. Forced strain beyond Endurance becomes
    damage.
  - Non-hero figures take damage instead of strain.
- **Rest** (action): recover strain equal to Endurance, and any excess heals damage.
- **Exhaust** a card: it's unusable until readied at the start of the hero's next
  activation. **Deplete** a card: it's used up for the rest of the mission.
- **Attribute test:** roll the attribute dice and pass on **1 or more surges**. Elite
  figures automatically get 1 success and regular figures automatically fail. Pass rates
  by pool:

  | Pool | Pass rate | Pool | Pass rate |
  |---|---|---|---|
  | Red | 17% | Blue+Green | 67% |
  | Blue | 33% | Blue+Blue | 56% |
  | Green | 50% | Blue+Green+Yellow | 89% |
  | Yellow | 67% | Blue+Blue+Green | 78% |
  | | | Blue+Green+Green | 83% |

- **Carry limit per mission:** 1 armor, 2 weapons and 3 equipment. Item cards can be
  traded freely between missions but not during them.
- Weapons have modification slots. Each weapon can hold one modification per trait.
- **Crates:** interact to claim one and draw a Supply card (a one-use consumable). Each
  crate is worth +50 credits at the end of the mission. The GW equivalent is **shrines**.

## Imperial side (the Adversary)

- **Deployment cards** give group size, deployment cost, reinforcement cost, Speed,
  Health, defense dice, attack dice, abilities and surges. Elite cards (red) are better
  versions of regular cards (gray). Unique figures (villains) have a bullet before the
  name.
- **Threat** is gained every round (equal to the threat level) and spent to deploy groups from the
  Imperial player's hand (the full deployment cost) or to **reinforce** single defeated
  figures. Reinforcing needs another figure from that group still on the map and no
  more figures than the group size. Threat is capped at 20.
- **Mission setup** sorts groups into:
  - **Initial groups:** on the map at the start.
  - **Reserved groups:** triggered by mission events.
  - **Open groups:** the Imperial player's secret hand, chosen at setup.

  When a non-unique group is wiped out, its card returns to the Imperial player's hand
  to be deployed again later.
- **Imperial Class deck:** chosen at campaign start and bought with XP. Its cards include
  **Attachments**, which are placed on a Deployment card and buff that whole group.
- **Agenda cards:** bought with **influence** during the Imperial Upgrade Stage (draw 4,
  buy any). Types:
  - Side missions.
  - Forced missions.
  - Ongoing effects.
  - Secret cards played later.

  The deck is built from 6 sets of 3 cards.
- **Threat-cost abilities:** some Imperial abilities cost threat.

## Campaign economy

- **Campaign structure:**
  - An introductory mission.
  - Alternating story and side missions, following the campaign log.
  - Upgrade stages between missions.
  - A **finale**. Whoever wins the finale wins the campaign.
- **Mission rewards:**
  - XP for every player, typically 1 plus a bonus for the winner.
  - Credits for the heroes, typically 100 per hero, plus 50 per crate claimed.
  - Influence for the Imperial player.
  - Sometimes Reward cards or allies.
- **Rebel Upgrade Stage:**
  - Spend XP on class cards (each hero's own 9-card deck, costing 1–4 XP).
  - Draw 6 cards from the current-tier Item deck and buy any with credits. Items sell
    for half cost, rounded up to the nearest 25.
- **Imperial Upgrade Stage:** spend XP on class cards, then influence on agendas.
- **Player count:** with 2 heroes, each gets a "Legendary" Reward card at setup; with 3
  heroes, each gets a "Heroic" one.
- **Side mission deck:**
  - One red mission per hero. These are hero-specific and mostly reward class items.
  - 4 green missions chosen by the players. These mostly reward allies.
  - 4 random gray missions. These mostly reward credits.
- **Post-mission cleanup:** heroes heal fully, and Supply cards are shuffled back.

## Map

- **Adjacency** includes diagonals, but not across walls or doors.
- **Line of sight:** draw two non-crossing lines from one corner of the attacker's space
  to two adjacent corners of the target's space. If either line passes through a wall,
  a figure, blocking terrain or a door, there's no line of sight. Adjacent figures
  always have line of sight to each other.
- **Distance** counts movement, ignoring the extra costs of figures and terrain.
- **Terrain:**
  - Blocking (solid red): blocks movement and line of sight.
  - Impassable (dashed red): blocks movement only.
  - Difficult (blue): +1 movement point.
- **Large figures:** no diagonal moves, and 1 movement point to rotate. Attackers target
  one of the spaces they occupy.

## Balance heuristics

These are general IA knowledge, not rules text.

- Heroes act far more than any single enemy figure. They can attack twice per activation
  (and get 2 activations each in a 2-hero game), and they spend strain to go further. The
  Imperial side makes up for this with numbers and reinforcement.
- Compare a deployment group's cost to its **threat** value. As an example, a regular
  Stormtrooper group (3 figures) costs 6 threat and reinforces for 2. An elite group
  costs 9 and reinforces for 3. **[unverified exact values]**
- Surge abilities are the main tuning dial. Common prices, each for 1 surge **[typical
  values]**: +1 damage, +1 or +2 accuracy, Pierce 1–2, a condition, Recover 1–2. A surge
  that adds 2 damage or Blast usually needs a strong die.
- Missions are races against the round limit, so movement and actions are worth a lot.
  Extra actions, "move X" and free attacks are among the strongest effects in the game.
