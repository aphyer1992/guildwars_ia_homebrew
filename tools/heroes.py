"""Hero rules shared by the tools: deriving a hero's wounded side.

Default wounded rule (the designer's, matching official IA heroes):
  1. Speed and endurance each drop by 1.
  2. In each attribute pool, the most-surgy die (yellow, else green, else blue)
     becomes red. e.g. blue green yellow -> red blue green; blue -> red.
  3. Abilities marked `healthy_only: true` are lost.
A hero file can override any of speed / endurance / attributes with a `wounded:` block.
"""

SURGE_ORDER = ["yellow", "green", "blue"]  # most surgy first
DIE_ORDER = ["red", "blue", "green", "yellow"]  # display order, least surgy first
WOUNDED_OVERRIDES = {"speed", "endurance", "attributes"}


def wound_pool(pool):
    pool = list(pool)
    for colour in SURGE_ORDER:
        if colour in pool:
            pool[pool.index(colour)] = "red"
            break
    return sorted(pool, key=DIE_ORDER.index)


def wounded_stats(hero):
    """Return the hero's wounded-side stats; None stays None for unfinished heroes."""
    minus1 = lambda v: None if v is None else v - 1
    attrs = hero.get("attributes")
    stats = {
        "health": hero.get("health"),
        "speed": minus1(hero.get("speed")),
        "endurance": minus1(hero.get("endurance")),
        "defense": hero.get("defense"),
        "attributes": None if attrs is None else {k: wound_pool(v) for k, v in attrs.items()},
        "abilities": [a for a in hero.get("abilities") or [] if not a.get("healthy_only")],
    }
    stats.update(hero.get("wounded") or {})
    return stats
