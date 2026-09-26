# Translating Guild Wars skills to IA mechanics

Research and proposals (2026-09-26, from wiki.guildwars.com skill lists). Nothing here
is decided. It's a menu for the designer. Rules background is in `docs/rules-primer.md`;
the setting is in `docs/setting.md`.

## The core translation problem

GW is real-time, with energy, recharge timers, cast times, armour penetration, and
hexes and enchantments measured in seconds. IA has **two actions per activation**,
**strain** as the hero's resource, **exhaust** as a once-per-round limit, **deplete** as
a once-per-mission limit, and **rounds** as the only clock.

| GW concept | Suggested IA equivalent | Notes |
|---|---|---|
| Energy cost | Strain cost | Already used (for example Cynn's *Fireball*: 2 strain) |
| Recharge time | Exhaust (short), deplete (long or elite) | |
| Elite skill | 4 XP card, or elite-variant ability for enemies | |
| Cast time / interrupt | IA's **interrupt** timing | The mesmer identity: Norgu, Mind Spark, Charr Hunter |
| Adrenaline (warriors) | "After you damage a target, gain a charge token", or Focus | IA has no adrenaline; tokens on a card are an established IA pattern (for example Loku's recon tokens) |
| Enchantment (a buff on you) | Beneficial condition or an exhaust card with a lasting effect | Enchantment removal → "discard a beneficial condition", or "exhaust one class card" (much stronger) |
| Hex (a debuff on a foe) | Harmful condition, or a token with custom text | IA has only a few conditions, so tokens let hexes stay distinct |
| Knockdown | **Stun** | Stun is worth about 2.25 against heroes (`tools/value_model.yaml`) |
| Bleeding, Burning | **Bleed** | Decided |
| Poison (mostly), Disease | **Weaken** | Decided |
| Blindness | −accuracy (for example −2), or a "miss on a 1-in-N" rule | IA has no Blind. Hidden on the attacker is the closest official effect |
| Crippled / slowed | Lose movement points, or −1 Speed | Norgu's *Stolen Speed* already does this |
| Weakness (−damage) | "−1 damage on next attack" | Faintheartedness, Enervating Charge |
| Armour penetration | Pierce | Mesmers get Pierce 3 (decided); lightning also ignores armour in GW |
| Area of effect | Blast, Cleave, "each adjacent figure" | **Note: GW area spells never hit allies; IA's Blast does** (see below) |
| Healing | Recover | See the Monk section: the action economy is the whole problem |
| Resurrection | Nothing equivalent: IA heroes are wounded, then withdraw, and never die | A "return a withdrawn hero" effect would be huge; handle with care |

### Friendly fire

IA's Blast damages **every** adjacent figure, friend or foe. GW area spells hit only
foes (apart from rare exceptions such as *Heal Area*, which also heals foes). Cynn's
*Liquid Flame* already works around this by letting her exempt spaces. The options are:

- **Keep IA's rule:** positioning matters and fire is dangerous. That suits the Charr
  shooting into melee scrums, and the value model already penalises Blast next to
  friendly figures.
- **Add a keyword, such as "Blast X (foes)":** it only hits hostile figures. It's
  cleaner for hero spellcasters, but noticeably stronger, since the only limit on
  firing into a melee disappears.

Suggestion: keep IA's rule by default, and use exemption effects like *Liquid Flame* as
the upgrade path. That makes Elementalist class cards about controlling their fire.

## Elementalists

The four elements already have distinct identities in GW, and each one maps onto a
different IA lever:

| Element | GW identity | Iconic skills | IA lever |
|---|---|---|---|
| **Fire** | Raw area damage, Burning | Fireball, Flare, Inferno, Fire Storm, Meteor, Meteor Shower, Lava Font, Immolate, Searing Flames, Conjure Flame | Blast, Bleed, "each adjacent figure" (Inferno); Meteor → Blast plus Stun (Cynn already has this) |
| **Air** | Armour-piercing single target, interrupts, Blindness, knockdown | Lightning Orb, Chain Lightning, Lightning Javelin, Enervating Charge, Blinding Flash, Gale, Shock | **Pierce**, interrupts, Cleave-like chaining ("Chain Lightning: Cleave 1, then Cleave 1 again"), Stun (Gale, Shock), −accuracy |
| **Earth** | Armour, blocking, knockdown, Blindness | Obsidian Flesh, Armor of Earth, Magnetic Aura, Stoneflesh Aura, Aftershock, Earthquake, Eruption, Stone Daggers | **Defensive**: +block, re-rolled defense, damage reduction; area Stun (Earthquake). This is the tank Argo already is, and it's why black versus white is genuinely unclear for him |
| **Water** | Slowing, snares, control | Ice Spikes, Frozen Burst, Deep Freeze, Ice Prison, Maelstrom, Armor of Frost, Blurred Vision | **Movement denial**: lose movement points, −Speed, or "cannot move more than 1 space"; area slow |
| Energy Storage | Energy management | Aura of Restoration, Ether Renewal, Master of Magic, Elemental Attunement | Strain recovery and "cast more"; *Master of Magic* is already a Cynn card |

**Glyphs** (*Glyph of Concentration*, *Intensity*, and so on) are "empower your next
spell" effects. In IA they map neatly onto Focus, or onto an exhaust card that upgrades
the next attack.

## Monks

**The problem:** in the MMO a monk is almost a pure healer, and in IA pure healing is
weak.

- **Heroes heal themselves cheaply.** Rest recovers Endurance (about 4) for one action.
  So one hero action is worth about **4 damage-equivalents**, and a heal that costs an
  action needs to beat 4 to be worth taking.
- **The Adversary wins by spiking a hero to wounded within one round.** Healing *after*
  the spike does nothing to stop that. **Prevention beats healing.**
- **Healing between missions is free.** Heroes fully recover after every mission.

**How IA handled it:** MHD-19 is IA's medic. None of his cards is a plain heal action:
- *Bacta Injector* (1 XP): strain plus exhaust. An adjacent friendly figure recovers 1
  or discards a harmful condition.
- *Field Surgeon* (2 XP): a surge on his attacks makes an adjacent friendly figure
  recover 2.
- *Bacta Radiator* (4 XP): at the start of each round, every friendly figure within 2
  spaces recovers a little.

The pattern is **healing as a rider on something else**: on an attack, on an exhaust,
or as a passive aura. It's never a standalone heal action.

**Proposed monk archetypes:** pick one per monk hero, or mix them.

1. **Protector (Protection Prayers): the strongest fit for IA.**
   - *Protective Spirit*: "while defending, the target suffers at most 3 damage from
     this attack." It directly counters spiking.
   - *Guardian*: a friendly figure in line of sight applies +1 block, or rolls an extra
     white die, until the end of the round.
   - *Aegis*: an elite-level effect, "each friendly figure applies +1 block this round."
   - *Reversal of Fortune*: an interrupt when a friendly figure is attacked, adding
     block equal to its missing Health, capped low.
   - *Spell Breaker*: "cannot be targeted by abilities" (attacks still work).
   - *Divine Intervention* (4 XP): an interrupt when a friendly figure would be wounded;
     prevent it and have that figure recover a small amount instead. Deplete it.
2. **Cleanser (Mend Condition, Remove Hex, Restore Condition).** Conditions are worth a
   lot (Stun about 2.25, Bleed 1.5). Removing them freely, or as a rider on moving or
   attacking, is real value. Acolyte Jin's *Mending Touch* and Olias's card already
   show the pattern. A monk could make it their core identity.
3. **Healer (Healing Prayers).** Only as riders:
   - *Orison of Healing* as a surge: "an ally in line of sight recovers 2".
   - *Heal Area* as a Blast-shaped heal that also heals adjacent enemies, a fun
     drawback straight from the MMO.
   - *Infuse Health*: suffer damage to heal an ally for more. That turns the monk's own
     Health into a resource.
   - *Healing Breeze* / *Mending*: an aura like *Bacta Radiator*.
4. **Smiter (Smiting Prayers): the monk as an attacker.**
   - *Smite*: +2 damage if the target attacked this round.
   - *Signet of Judgment*: the target is Stunned, and adjacent figures suffer 1.
   - *Balthazar's Aura*: at the start of your activation, each adjacent hostile figure
     suffers 1.
   - *Shield of Judgment*: a hostile figure that makes a melee attack against a chosen
     ally becomes Stunned.
   - *Banish*: +damage against summoned figures such as minions and phantasms.

**Enemy monks** (Charr Shaman, Dolyak Rider, Shiverpeak Protector, Grawl Ulodyte,
Resurrect Gargoyle) are easier to get right. Healing enemies undoes the heroes' work,
which the heroes feel directly.
- **Precedent:** the Imperial class card *Technical Support* ("adjacent friendly
  figure: discard all conditions, become Focused, or recover 3").
- **Keep it modest.** An enemy healer that sits behind cover is a classic
  "kill it first" priority, and that's good gameplay.

## Area damage over time (Fire Storm, Lava Font, Meteor Shower, Maelstrom, Eruption)

**How it works in the MMO:** *Fire Storm* is 10 energy with a 2-second cast. It creates
a zone around the target's location that damages adjacent foes every second for 10
seconds. **Anyone can walk out of it**, and in practice most of its value was forcing
enemies to scatter, or catching enemies that couldn't move (melee-locked, casting, or
knocked down).

**IA has no persistent zones in the core game.** Lingering effects use **tokens**.
Three ways to translate it:

**A. Zone token (area denial): recommended for "storm" spells.**
- *Fire Storm*: place a Fire Storm token in a space within line of sight. At the end of
  the round, each hostile figure in or adjacent to that space suffers 2 damage (and is
  Bled?). Then remove the token.
- **Why it's faithful:** targets get their activations to walk out, so like the MMO
  it's mostly **area denial**. It costs them movement (heroes pay strain), or it hurts
  whatever can't or won't move: figures holding an objective, figures in melee, or a
  freshly deployed group clustered on its deployment point.
- **Tuning dial:** lasts one round, or "until the start of your next activation".
  Damage X, which should be modest since it's not blockable.
- **Value intuition** (from the value model's reasoning):
  - **Against heroes** it's weak, because they're mobile and forcing a hero to spend a
    move is worth maybe 1–2.
  - **Against Adversary groups** at a deployment point, or anything holding a point,
    it's strong.
  - Hero Elementalists therefore get more out of it than enemy casters do.

**B. Condition rider: recommended for "burning" spells.**
- *Immolate*, *Incendiary Bonds*, *Searing Flames*: normal attacks or effects that apply
  **Bleed** (Burning).
- It reuses an existing mechanic. The damage over time is the condition itself, and the
  target clears it with an action. That fits Bleed's IA value (about 1.5).
- *Searing Flames*' GW twist (extra damage to targets already Burning) becomes "+2
  damage if the target is Bleeding" in IA.

**C. Delayed Blast: for Meteor Shower and Eruption.**
- "Place a token. At the start of your next activation, perform Blast 2 centered on it
  (and Stun each figure damaged, for Meteor Shower)."
- The warning gives enemies a chance to move, just like the MMO's telegraphed area
  spells.

Maelstrom (water: cold damage plus interrupting spells in an area) fits option A, but
with "figures in the zone cannot use exhaust abilities" in place of damage. That's a
control zone rather than a damage zone.

## Other professions, in brief

- **Warrior:** adrenaline → charge tokens; stances → exhaust-card buffs (Wild Blow
  strips them); knockdown hammers → Stun; axes → Cleave; swords → Bleed (for example
  Hundred Blades hitting adjacent figures).
- **Ranger:** preparations (*Ignite Arrows*, *Apply Poison*) → strain for "your attacks
  this activation gain X" (Acolyte Jin's *Apply Poison* already does this); pets →
  **IA companion cards**.
  - IA's companion cards (from later expansions; 7 are in `reference/ia_cards.json`,
    for example Salacious B. Crumb and J4X-7) are small figures with 1–6 Health, one
    die or none, and one or two abilities, activated with their hero.
  - They're a ready-made template for Joe and for necromancer minions.
- **Necromancer:** life steal → Recover surges; minions → companion-style tokens
  (Olias); curses → Weaken, −damage and "suffer damage when attacking" hexes; blood
  magic → pay Health in place of strain (Olias already does this).
- **Mesmer:** energy denial → strain damage; interrupts; hexes that punish actions
  (Empathy, Backfire: "suffer 1 damage when you attack or use an ability");
  enchantment removal; Pierce 3 (decided).
- **Assassin** (Zenmai): combo chains (lead, off-hand, dual attacks) → "if you attacked
  this target earlier this activation, +X" conditionals; shadow steps → place (a
  teleport, ignoring terrain); white defense for evasion.
- **Paragon** (Morgahn, Cynn's secondary): shouts and chants → an aura of buffs for
  allies within X spaces (IA's *Leader* trait and cards such as Gideon's *Command* are
  the precedent, and a warning: *Masterstroke*-style free extra activations for allies
  are what broke Gideon); spears → ranged attacks with a melee-capable weapon.
