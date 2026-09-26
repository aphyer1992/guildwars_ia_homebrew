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
- `tools/check_data.py` — validates all data and lists unfinished entries/TODOs.
  Run it after any data edit: `python tools/check_data.py`.
- `docs/open-questions.md` — design ambiguities awaiting the designer's decision.
- `archive/original-docx/` — the Word docs the data was transcribed from (2026-09-26).
  Historical only; do not edit or treat as current.

## Data conventions

- Dice are full lowercase colour names. Attack: `red blue green yellow`.
  Defense: `black white`. (The original docs used letters, where `B` meant blue
  in attack pools and black in defense pools.)
- Hero `attributes` keys: `strength`, `agility`, `intellect`. Values are kept as the
  original letter strings (e.g. `BGY`) until the attribute-dice question in
  `docs/open-questions.md` is settled.
- `healthy_only: true` marks a hero ability that only works while Healthy (not Wounded).
- Class card `xp`: `1`–`4`, `mission` (mission reward), or `null` (not yet decided).
- Enemies: shared stats at the top level; anything that differs between regular and
  elite (cost, reinforce, health, surges, name, variant-specific abilities) goes in
  `variants.regular` / `variants.elite`. Parenthesised values in the original docs
  meant the elite value.
- `surges` is a list; each string is one surge ability (costs 1 surge unless stated).
- Unfinished content: `status: stub`, a missing `text`/`dice`, or a `# TODO` comment.
  Keep placeholders rather than deleting them — they're the designer's to-do list.
- Rules text is the designer's wording. Don't silently reword, "fix" or rebalance it;
  propose changes and flag ambiguities in `docs/open-questions.md` instead.

## Game rules primer

TODO: summary of Imperial Assault core rules (dice faces, surges, accuracy, conditions,
strain, exhaust vs deplete, threat, influence, card sizes) and GW → IA mapping notes.
