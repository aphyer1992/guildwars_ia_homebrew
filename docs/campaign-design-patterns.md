# Campaign design patterns (from IA's *Jabba's Realm*)

Notes from the designer's copy of the *Jabba's Realm* campaign guide
(`reference/Jabbas_realm.pdf`, a scan, read 2026-09-26). The designer rates it one of
IA's best-designed campaigns: slightly Rebel-favoured, but well balanced, and
creative without being confusing. This is a paraphrased summary of *how* its missions
work, to model our missions on. It is not a copy of the text.

## Campaign structure

- **Log:** Intro (threat 2) → Side → Story 1 (3) → Side → Story 2 (4) → Side →
  **Interlude** (4) → Story 3 (5) → Side → Story 4 (6) → **Finale** (6).
  - Threat rises by 1 about every two missions.
  - Item tiers: tier 1 early, tiers 1 and 2 in the middle, tiers 2 and 3 at the
    interlude, tier 3 late.
- **Two options per story slot.** Each story slot offers two missions; the one not
  played is discarded. Both options lead to the same next pair, so the branch is a
  diamond: a choice now, without the campaign multiplying.
- **The interlude is a branch chosen by the players, not by winning or losing.**
  During *Moment of Fate* the heroes choose mid-mission whose side to take (Jabba's or
  the Rebel Alliance's). The two paths have different story missions 3 and 4, with
  different allies and rewards.
- **Two finales, selected by the second-last mission's result:**
  - Win → *Storming the Palace*: an assault on the villain's stronghold.
  - Lose → *Mutiny*: a desperate escape from execution. It's harder, but still winnable.
  - Each finale has its own win and loss ending, as described in
    `docs/rules-primer.md`.
- **Losing isn't a dead end.** Every story mission leads onward whether the heroes win
  or lose. The loser's consolation is usually small and specific:
  - Heroes: "25 credits per hero if the heroes achieved a sub-goal (defeated the
    captain, claimed 6 explosives)".
  - Imperial player: "1 XP", or "draw an extra Agenda card".
- **Win with a sting:** "Heroes win, but if only 1 hero is healthy, the Imperial player
  draws an extra Agenda card." Scraped wins still cost something.
- **Hero personal missions** (Onar, Vinto, Shyla): each hero's side mission rewards a
  hero-specific card. The Imperial player gets 2 influence if the heroes lose.
- **Agenda hand limit:** the Imperial player keeps at most 4 Agenda cards between
  missions.

## Standard mission skeleton

- **Round limit** of 6 (sometimes 7, or 8 for a finale). "Mission ends at the end of
  Round X or when all heroes are wounded."
- **Setup often starts with "threat +2× threat level and an optional deployment"**:
  the Adversary gets an immediate punch.
- **Events:** each mission has 2–4 triggers, either timed ("end of Round 2/4") or
  caused by heroes ("when the first door opens", "when the first egg is retrieved").
  Each trigger deploys reserved groups, activates new deployment points, and often
  adds "threat + threat level".
- **Locked doors** gate progress. They're unlocked by a terminal interaction (often
  with an attribute test), by destroying the door (Health 4–10, 1–2 black defense), or
  by a mission event.
- **Objects with Health and a defense die** are everywhere: barricades, power cells,
  structural supports, engines, beacons, terminals. "Attack the X" is a staple
  objective. It's the natural template for our siege weapons, trebuchets and
  ballistae.

## Mechanics worth reusing (with GW mappings)

| Mechanic | How it worked | GW use |
|---|---|---|
| **Carry-and-deliver tokens** | Spend 2 movement points to pick up, carry 1, **drop it if you suffer 3+ damage**. Both sides can carry (the spice tug-of-war) | Trebuchet parts (Fort Ranik), armour pieces (Great Northern Wall bonus), powder kegs (Borlis Pass), the Tome of the Fallen (Nolani bonus) |
| **Escort by Status Phase** | Captives move up to 5 spaces each Status Phase, **minus 1 per enemy figure adjacent** | Freeing captives (Ruins of Surmia); refugees (the Frost Gate) |
| **Hidden face-down tokens** | Randomly placed coloured tokens; studying one reveals an effect by colour (good, bad or story) | Devourer burrows (ambush or empty); Charr camp effigies |
| **Resource tokens for heroes** | Claimed explosives let a hero, once per activation, throw a small grenade (1 red die, area) | Powder kegs; Stormcaller as a one-shot weapon |
| **Mission weapon** | A ship's cannon fires each Status Phase: the owner picks a space, rolls 1 red die, and hits that space and adjacent ones | **Trebuchets / ballistae**: the Stone Summit ballistae aim at heroes, and a repaired trebuchet at Fort Ranik aims for the heroes |
| **Collapse hazard** | Destroying a support damages every figure within 4 spaces (1 green die): risky for both sides | Burning buildings in Ascalon; ice cave-ins (Borlis Pass) |
| **Deadly pit** | Ending movement in the pit = 10 damage; heroes may **shove** adjacent small enemies into it (test) | Chasms, the Shiverpeak cliffs; shoving Charr off the Great Northern Wall |
| **Leashed monster** | The Rancor is chained: it can't leave the Swamp spaces | A chained beast in a Charr camp; a caged Ice Drake |
| **Beast turned on its master** | If the Rancor ends near Kallenn, Kallenn dies | A Stone Summit Beastmaster's enslaved beast turning on him |
| **Allies that switch sides** | Mercenary allies join mid-mission, or **betray** the heroes (Gamorreans become Imperial) | Grawl mercenaries? Dwarves of uncertain loyalty in the Shiverpeaks? |
| **Named boss upgrade** | A reserved elite Officer "becomes" Kallenn: +10 Health, an extra action, multiple attacks. A disguised Terro hides among Stormtroopers | Cheap villains from existing deployment cards: Bonfaaz as an elite Fire Caller with +Health and an extra action |
| **Villain effect menu** | At the end of certain rounds, the Imperial player picks 1 of 3 effects (area damage, heal and Focus, a free interrupt attack), or pays threat to pick 2 | Bonfaaz's and Dagnar's boss turns |
| **Softer withdrawal** | Withdrawn heroes are **incapacitated** instead: 1 action per activation, move only. They must still reach the extraction point | Escape missions (the Frost Gate breakout, the Nolani escape) |
| **Siege pressure on healing** | "Each time a hero rests, threat +2; after Round 4 heroes can't rest to recover damage" | Last stands (the Frost Gate chokepoint) |
| **Mobile deployment points** | Imperial tokens act as deployment points that move 3 spaces per round | Devourers burrowing; a Charr warband advancing |
| **Moving map sections** | Tiles swapped in mid-mission; skiffs linked by ladders and hatches | Borlis Pass stages; Nolani Academy's breakout → escort → boss phases |
| **Negotiation** | Interact with a villain to negotiate: an attribute test that gets easier as he takes damage | Rurik and King Jalis; parleying with Grawl |
| **Escalating threat** | "At the start of each round, increase threat by the current round number" | Charr reinforcements at the Wall |
| **One-time surge, then a fixed pool** | "Threat +10 and an optional deployment, but no more threat gain afterwards" | A final charge at the Frost Gate |

## Takeaways for our campaign

- **Our planned structure already matches it.** Intro → alternating story and side
  missions → a second-last mission that picks the finale → a finale with its own win and
  loss endings (`docs/campaign-research.md`).
- **Add a player-choice interlude.** For example: after Nolani Academy, the heroes
  choose between following Rurik into exile or staying with King Adelbern's defence.
  Two paths, different allies, both leading to the Shiverpeaks.
- **Offer two options per story slot** to add replay value cheaply.
- **Siege weapons are just "objects with Health" plus a mission-weapon rule.** Both
  patterns are proven in IA.
- **Write consolation rewards for every mission,** so losses still feel like progress.
