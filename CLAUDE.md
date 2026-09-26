# Guild Wars × Imperial Assault

A homebrew conversion: Star Wars: Imperial Assault (campaign mode) mechanics, re-themed
as the MMO Guild Wars (heroes, professions, Charr, Factions spirits, GW item names).
Personal project; the end product is printable cards (cardstock, cut, sleeved) plus
balance tooling.

## Layout

- `data/` — **source of truth** for all game content, as YAML.
  - `heroes/<name>.yaml` — one hero per file (hero sheet + class deck).
  - `enemies/<name>.yaml` — one deployment group per file.
  - `adversary/class_decks.yaml`, `adversary/agendas.yaml` — Adversary (Imperial player) cards.
  - `items/weapons.yaml`, `items/attachments.yaml`, `items/accessories.yaml`.
  - `shrines.yaml` — the "ashes of the spirits" shrine items (IA crates equivalent).
  - `dice.yaml` — the six faces of each IA die (standard IA dice, unchanged). Use this
    for any damage/probability maths rather than recalling faces from memory.
- `tools/check_data.py` — validates all data and lists unfinished entries/TODOs.
  Run it after any data edit: `python tools/check_data.py`.
- `tools/attack.py` — exact expected-damage calculator for an enemy, weapon or custom
  dice pool vs black/white defense (`python tools/attack.py charr_ash_walker`). It
  parses surge strings like `+1 damage`, `Pierce 2`, `Blast 1`, `Recover 1` and
  conditions.
  - `--ia "Royal Guard"` runs an official deployment card.
  - `--compare 4 5` tables every figure at those costs, ours and official, from
    `reference/ia_cards.json`. For official cards, only surges, always-on modifiers and
    the unconditional "reroll 1 attack die" wording are modelled. Conditional rerolls
    are flagged, not applied.
  - `--reroll N` and `--defense-reroll N`: both sides reroll optimally (exact, not a
    heuristic). The attacker decides first, then the defender. The choice uses the same
    objective as surge spending, so it will follow the value model too.
  - `--value` scores an attack by situational *value* in damage-equivalents, using
    `tools/value_model.yaml`. The model counts overkill, kill or wound bonuses,
    Cleave/Blast targets, Recover when hurt, a hero's surge-for-strain, and condition
    values.
    - Surges and rerolls are re-optimised for each listed situation, then averaged.
    - Weapons use the `vs_enemies` perspective; enemies use `vs_heroes`.
    - Values are given at range 1 for every attack, plus ranges 4 and 6 (medium and
      long) for ranged attacks, where accuracy must reach the range. `--compare` shows
      these as V@1/V@4/V@6. `--compare-weapons` gives the same table for all weapons.
      `--sort value|v4|v6` sorts by them.
    - The model's numbers are the designer's to tune.
    - `--calibrate` shows the value each single surge adds in each perspective. It
      also checks the designer's `targets` in the YAML (for example "Cleave 2 > +2
      damage" for heroes). Re-run it after any tuning.
- `docs/open-questions.md` — design ambiguities awaiting the designer's decision.
- `docs/rules-primer.md` — condensed IA campaign rules and dice statistics.
- `reference/` — official IA material (FFG's copyrighted content). Gitignored, so it's
  local only.
  - The Rules Reference Guide and Learn to Play PDFs.
  - `ia_cards.json` — every official IA card as JSON: `DeploymentCards`, `HeroSheets`
    (healthy and wounded stats), `RewardCards` (hero and Imperial class cards; see
    `ClassName` and `CostAmount` XP), `ItemCards` (by `Tier`), `AgendaCards`,
    `ConditionCards`, and more.
    - Extracted from the Kensei Imperial Assault Tools Suite
      (`C:\Program Files\Kensei\...\ImpAss.Common.dll`, embedded JSON).
    - Card text uses tags like `<surge>`, `<damage>`, `<strain>`, `<action>`.
    - Use it to look up real benchmark stats instead of recalling them.
    - It's not quite complete: 7 of the 21 hero class decks are missing cards (for
      example, Biv and Shyla have only 6). Treat an odd-looking gap as missing data, not
      as the real design.
  - Fallback source: the IA wiki (for example,
    https://imperial-assault.fandom.com/wiki/Shyla_Varad_(Hero)). WebFetch gets HTTP 402
    from it, so read it with the in-app browser instead.
- `archive/original-docx/` — the Word docs the data was transcribed from (2026-09-26).
  Historical only; do not edit or treat as current.

## Data conventions

- Dice are full lowercase colour names. Attack: `red blue green yellow`.
  Defense: `black white`. (The original docs used letters, where `B` meant blue
  in attack pools and black in defense pools.)
- Hero `attributes` are keyed `strength`, `agility` and `arcana`. Tech doesn't fit the GW
  theme. Values are attack-dice lists; the original docs' `B` meant blue here.
- **Wounded side is derived, not stored**. `tools/heroes.py:wounded_stats` works it out
  from the default rule:
  - Speed and endurance each drop by 1.
  - In each attribute pool, the most-surgy die (yellow, else green, else blue) becomes
    red.
  - `healthy_only` abilities are lost.

  A hero that breaks the rule gets a `wounded:` block overriding `speed`, `endurance`
  and/or `attributes`.
- `healthy_only: true` marks a hero ability that only works while Healthy (not Wounded).
- Class card `xp`: `1`–`4`, `mission` (mission reward), or `null` (not yet decided).
- **A complete hero** has:
  - At least one `healthy_only` ability.
  - 8 XP-costed class cards, two each at 1, 2, 3 and 4 XP (20 XP total), which is the
    official IA standard.

  `check_data.py` lists heroes that don't meet this as unfinished. Most heroes are still
  in progress, so expect them there.
- Enemies: shared stats at the top level; anything that differs between regular and
  elite (cost, reinforce, health, surges, name, variant-specific abilities) goes in
  `variants.regular` / `variants.elite`. Parenthesised values in the original docs
  meant the elite value.
- `surges` is a list; each string is one surge ability (costs 1 surge unless stated).
- Unfinished content: `status: stub`, a missing `text`/`dice`, or a `# TODO` comment.
  Keep placeholders rather than deleting them — they're the designer's to-do list.
- Rules text is the designer's wording. Don't silently reword, "fix" or rebalance it;
  propose changes and flag ambiguities in `docs/open-questions.md` instead.

## Game rules

The base rules are standard Imperial Assault campaign mode. **Read
`docs/rules-primer.md` before commenting on rules or balance.** It condenses the rules,
has the dice statistics, and marks which details are unverified. For exact rulings, the
source PDFs are in `reference/`: the Rules Reference Guide (authoritative) and Learn to
Play. The IA text in those files can be extracted with `pdftotext`.

Key facts that are easy to get wrong:
- Heroes may attack twice per activation. Non-hero figures may attack only once.
- Each surge ability can be triggered only once per attack.
- Evade cancels surges. Dodge (white die) is an automatic miss.
- Blast and Cleave damage ignores blocks, and Blast hits friendly figures too.
- An attribute test passes on 1 or more surges. Only heroes roll; elite figures get 1
  automatic success and regular figures automatically fail.
- Heroes are wounded, then withdraw. They never die, and they heal fully between
  missions.

GW terminology: Rebels/heroes = heroes, Imperial player = **Adversary**, crates =
**shrines** (ashes of the spirits).

## Design intent

- The IA mechanics are theme-agnostic. IA itself grew out of the fantasy game Descent.
  The goal is for the game to **feel like Guild Wars**.
- Enemies, skills and items should be Guild Wars ones, and each should *feel like* its GW
  version, even though real-time numbers don't translate (a 91-damage Fireball makes no
  sense when 15 Health is a lot). For example, *Inferno* belongs on a fire Elementalist
  and damages adjacent figures.
- Faithful-but-risky designs are deliberate. Norgu is a Mesmer, which in GW means
  interrupts and denying abilities. That's hard to do well on a board, and he may end up
  too strong or too weak, but it's being attempted anyway. When commenting on designs
  like this, help make them work. Don't steer them back to safe IA patterns.
- **IA cards are a starting point for balance, not a gold standard.** Many are badly
  balanced, especially early ones. The designer's assessment:
  - Heroes:
    - Gideon is hugely overpowered.
    - Shyla, Fenn, and Diala (when built as support) are very overpowered.
    - Saska is too weak to function.
    - Biv and Davith are very weak.
  - Deployment cards: almost all core-set uniques (Darth Vader, IG-88, Han Solo, etc.)
    are badly overcosted for what they do.

  So benchmark against IA content that is mid-strength, not against outliers.
- **Some IA mechanics are repurposed for GW flavour:**
  - The Weaken condition mostly stands in for GW **Poison**.
  - Pierce 3, which IA mostly put on lightsabers, now goes on **Mesmers**, whose attacks
    ignore armor.

TODO (designer): player count and difficulty targets, and any house rules.
