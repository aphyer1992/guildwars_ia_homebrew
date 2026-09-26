"""Load every data file, check basic structure, and report what's unfinished.

Usage:  python tools/check_data.py
Exits non-zero if any file fails to parse or has a structural error.
"""
import re
import sys
from pathlib import Path

import yaml

from heroes import WOUNDED_OVERRIDES, wounded_stats

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

ATTACK_DICE = {"red", "blue", "green", "yellow"}
DEFENSE_DICE = {"black", "white"}
ATTRIBUTES = {"strength", "agility", "arcana"}
COMPLETE_DECK_XP = [1, 1, 2, 2, 3, 3, 4, 4]
AFFILIATIONS = {"adversary", "beast"}  # like IA's Imperial vs Mercenary
# Attribute tests pass on surges: surge faces per die (see data/dice.yaml).
SURGE_FACES = {"red": 1, "blue": 2, "green": 3, "yellow": 5}
TYPICAL_ATTRIBUTE_SURGES = 17  # Good (BGY) 10 + Okay (BG) 5 + Bad (B) 2; official heroes range 14-23

errors: list[str] = []
stubs: dict[str, list[str]] = {}  # group -> names


def err(where, msg):
    errors.append(f"{where}: {msg}")


def stub(group, name="(whole entry)"):
    stubs.setdefault(group, []).append(str(name))


flags: list[str] = []  # departures from typical values, to confirm are deliberate (not errors)


def flag(where, msg):
    flags.append(f"{where}: {msg}")


def load(path):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        err(path.relative_to(ROOT), f"YAML parse error: {e}")
        return None


def check_dice(where, dice, allowed):
    if dice is None:
        return
    if not isinstance(dice, list) or not all(d in allowed for d in dice):
        err(where, f"bad dice {dice!r} (allowed: {sorted(allowed)})")


def check_hero(where, h):
    if h.get("status") == "stub":
        stub(where)
    check_dice(where, h.get("defense"), DEFENSE_DICE)
    attrs = h.get("attributes")
    if attrs is not None:
        if set(attrs) != ATTRIBUTES:
            err(where, f"attributes should be {sorted(ATTRIBUTES)}, got {sorted(attrs)}")
        for name, pool in attrs.items():
            check_dice(f"{where} [{name}]", pool, ATTACK_DICE)
        total = sum(SURGE_FACES.get(d, 0) for pool in attrs.values() for d in pool or [])
        if total != TYPICAL_ATTRIBUTE_SURGES:
            flag(where, f"attribute surge faces total {total} (typical {TYPICAL_ATTRIBUTE_SURGES};"
                        " fine if deliberate, official heroes range 14-23)")
    if h.get("endurance") not in (None, 4):
        flag(where, f"endurance {h['endurance']} (default 4; 5 is a very big edge)")
    extra = set(h.get("wounded") or {}) - WOUNDED_OVERRIDES
    if extra:
        err(where, f"wounded can only override {sorted(WOUNDED_OVERRIDES)}, got {sorted(extra)}")
    wounded_stats(h)
    # A complete hero: a Healthy-only ability, and class cards costing 1,1,2,2,3,3,4,4 XP
    # (20 XP total; mission-reward cards don't count).
    if not any(a.get("healthy_only") for a in h.get("abilities") or []):
        stub(where, "no healthy_only ability")
    xp = sorted(c.get("xp") for c in h.get("class_cards") or [] if isinstance(c.get("xp"), int))
    if xp != COMPLETE_DECK_XP:
        stub(where, f"class card XP {xp}, want {COMPLETE_DECK_XP}")
    for key in ("abilities", "class_cards"):
        for card in h.get(key) or []:
            cw = f"{where} / {card.get('name')}"
            if card.get("status") == "stub" or not card.get("text"):
                stub(where, card.get("name"))
            if key == "class_cards" and card.get("xp") not in (1, 2, 3, 4, "mission", None):
                err(cw, f"bad xp {card.get('xp')!r}")


def check_enemy(where, e):
    if e.get("affiliation") not in AFFILIATIONS:
        err(where, f"affiliation should be one of {sorted(AFFILIATIONS)}, got {e.get('affiliation')!r}")
    if e.get("status") == "stub":
        stub(where)
        return
    check_dice(where, e.get("defense"), DEFENSE_DICE)
    attack = e.get("attack") or {}
    check_dice(where, attack.get("dice"), ATTACK_DICE)
    if attack.get("type") not in ("melee", "ranged", None):
        err(where, f"bad attack type {attack.get('type')!r}")
    if e.get("group_size") is None:
        stub(where, "group size")
    elif not isinstance(e["group_size"], int) or e["group_size"] < 1:
        err(where, f"bad group_size {e['group_size']!r}")
    variants = e.get("variants") or {}
    if not variants:
        err(where, "no variants")
    for vname, v in variants.items():
        for field in ("cost", "health"):
            if field not in v:
                err(f"{where} [{vname}]", f"missing {field}")
        if None in (v.get("surges") or []):
            stub(where, f"{vname}: blank surge")


def check_card_list(where, cards, required="text"):
    for c in cards or []:
        done = c.get(required) or (c.get("reward") or {}).get(required)
        if c.get("status") == "stub" or not done:
            stub(where, c.get("name"))


def check_dice_faces(where, doc):
    kinds = {"attack": (ATTACK_DICE, {"damage", "surge", "accuracy"}),
             "defense": (DEFENSE_DICE, {"block", "evade", "dodge"})}
    for kind, (colours, fields) in kinds.items():
        dice = doc.get(kind) or {}
        if set(dice) != colours:
            err(where, f"{kind} dice should be {sorted(colours)}, got {sorted(dice)}")
        for colour, faces in dice.items():
            if len(faces) != 6:
                err(f"{where} / {colour}", f"expected 6 faces, got {len(faces)}")
            for face in faces:
                if not set(face) <= fields:
                    err(f"{where} / {colour}", f"bad face {face!r} (fields: {sorted(fields)})")


def main():
    for path in sorted(DATA.rglob("*.yaml")):
        rel = path.relative_to(ROOT).as_posix()
        doc = load(path)
        if doc is None:
            continue
        if rel.startswith("data/heroes/"):
            check_hero(rel, doc)
        elif rel.startswith("data/enemies/"):
            check_enemy(rel, doc)
        elif rel == "data/items/weapons.yaml":
            for cat in ("melee", "ranged", "magical"):
                for w in doc.get(cat, []):
                    check_dice(f"{rel} / {w['name']}", w.get("dice"), ATTACK_DICE)
                check_card_list(f"{rel} [{cat}]", doc.get(cat), required="dice")
        elif rel == "data/items/attachments.yaml":
            for kind in ("prefixes", "suffixes"):
                check_card_list(f"{rel} [{kind}]", doc.get(kind))
        elif rel.startswith("data/adversary/"):
            for deck in doc:
                check_card_list(f"{rel} / {deck['name']}", deck["cards"])
        elif rel == "data/dice.yaml":
            check_dice_faces(rel, doc)
        elif rel == "data/shrines.yaml":
            check_card_list(rel, doc["cards"])
        elif rel == "data/items/accessories.yaml":
            check_card_list(rel, doc)
        else:
            err(rel, "unrecognised data file (add a check for it)")

    todos = []
    for path in sorted(DATA.rglob("*.yaml")):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"#\s*TODO", line):
                todos.append(f"{path.relative_to(ROOT).as_posix()}:{n}: {line.split('#', 1)[1].strip()}")

    print(f"Unfinished entries ({sum(map(len, stubs.values()))}):")
    for group, names in stubs.items():
        print(f"   {group}: {', '.join(names)}")
    print(f"\nTODO comments ({len(todos)}):")
    for t in todos:
        print("  ", t)
    print(f"\nBalance flags ({len(flags)}):")
    for f in flags:
        print("  ", f)
    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print("  ", e)
        sys.exit(1)
    print("\nNo structural errors.")


if __name__ == "__main__":
    main()
