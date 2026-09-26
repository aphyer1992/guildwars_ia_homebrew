"""Exact attack-damage calculator.

Usage:
  python tools/attack.py charr_ash_walker                 # enemy file, all variants
  python tools/attack.py charr_stalker --variant elite --range 5
  python tools/attack.py --weapon "Dragon Sword"
  python tools/attack.py --ia "Royal Guard"               # official IA deployment card
  python tools/attack.py --dice red green --surge "+1 damage" --surge "Pierce 2"
  python tools/attack.py charr_ash_walker --bonus "+1 damage"   # e.g. Shadow Strike active
  python tools/attack.py --compare 4 5                    # every figure costing 4 or 5
  python tools/attack.py --ia Stormtrooper --reroll 1     # e.g. Squad Training active
  python tools/attack.py --weapon Gladius --defense-reroll 1

Every combination of die faces is enumerated (no Monte Carlo), against one black
and one white defense die by default. Attack steps follow IA: evades cancel surges,
dodge is a miss, each surge ability can be used once per attack (an ability listed
twice can be used twice), pierce ignores blocks, and ranged attacks need accuracy >=
range when --range is given (melee attacks ignore --range).

Rerolls are played optimally for expected damage. The attacker decides first, seeing
both pools, and then the defender, seeing the attacker's new result. Each die is
rerolled at most once.

Surges are spent to maximise damage to the target; ties go to the choice with more
"extras" (Blast, Cleave, Recover, conditions). Blast/Cleave/Recover/conditions are
parsed but not yet counted as damage: they're shown as how often they trigger.

Official cards come from reference/ia_cards.json (gitignored; see CLAUDE.md). Only
their surge abilities and always-on attack modifiers are modelled; conditional
abilities in their card text are not.
"""
import argparse
import itertools
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
IA_CARDS = ROOT / "reference" / "ia_cards.json"
CONDITIONS = {"bleed", "stun", "weaken", "focus", "hidden"}
NUMERIC = {"damage", "pierce", "accuracy", "blast", "cleave", "recover", "surge"}
NOT_EXTRAS = {"damage", "pierce", "accuracy", "surge"}


# ---------------------------------------------------------------- parsing

def parse_effect(text, strict=True):
    """'+1 damage, Recover 1' -> {'damage': 1, 'recover': 1}.

    Unknown parts raise when strict; otherwise they're counted under 'other'.
    """
    effect = Counter()
    for part in (p.strip() for p in text.split(",") if p.strip()):
        low = part.lower()
        if m := re.fullmatch(r"([+-]\d+) (damage|accuracy|surge)", low):
            effect[m[2]] += int(m[1])
        elif m := re.fullmatch(r"(pierce|blast|cleave|recover) (\d+)", low):
            effect[m[1]] += int(m[2])
        elif low in CONDITIONS:
            effect[low] += 1
        elif strict:
            raise ValueError(f"can't parse surge/bonus part {part!r} (in {text!r})")
        else:
            effect["other"] += 1
    return effect


def parse_surge(text, strict=True):
    """'+1 damage' -> (1, effect); '2 surges: +3 damage' -> (2, effect)."""
    if m := re.fullmatch(r"(\d+) surges?: (.*)", text.strip(), re.I):
        return int(m[1]), parse_effect(m[2], strict)
    return 1, parse_effect(text, strict)


def ia_text(s):
    """Convert Kensei card markup to our surge notation."""
    s = re.sub(r"([+-]\d+) ?<(damage|surge)>", r"\1 \2", s)  # '+1<damage>' -> '+1 damage'
    s = re.sub(r"(\d+|X)<damage>", r"\1", s)            # 'Recover 2<damage>' -> 'Recover 2'
    s = re.sub(r"<(block|evade)>", r" \1", s)
    s = s.replace(" Ac.", " Accuracy").replace("Hide", "Hidden")
    return s


@dataclass
class Attack:
    name: str
    dice: list
    surges: list = field(default_factory=list)   # [(cost, effect)]
    bonus: Counter = field(default_factory=Counter)
    type: str | None = None                      # melee / ranged / None (unknown)
    stats: dict = field(default_factory=dict)    # cost, health etc. for comparisons
    reroll: int = 0                              # attack dice it may reroll per attack
    notes: list = field(default_factory=list)    # card text we don't model

    @classmethod
    def from_strings(cls, name, dice, surges, bonus=None, **kw):
        return cls(name, list(dice), [parse_surge(s) for s in surges if s],
                   parse_effect(bonus) if bonus else Counter(), **kw)


def load_yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def enemy_attacks(file_stem, variant=None):
    e = load_yaml(DATA / "enemies" / f"{file_stem}.yaml")
    if e.get("status") == "stub" or not (e.get("attack") or {}).get("dice"):
        return []
    out = []
    for vname, v in e["variants"].items():
        if variant and vname != variant:
            continue
        out.append(Attack.from_strings(
            f"{v.get('name', e['name'])} [{vname}]", e["attack"]["dice"], v.get("surges") or [],
            type=e["attack"].get("type"),
            stats={"cost": v.get("cost"), "reinforce": v.get("reinforce"),
                   "health": v.get("health"), "speed": e.get("speed"),
                   "group": v.get("group_size", e.get("group_size")),
                   "defense": e.get("defense"), "source": "ours"}))
    return out


def ia_attacks(name=None):
    """Official Imperial/Mercenary deployment cards (campaign-legal, no upgrades)."""
    cards = json.loads(IA_CARDS.read_text(encoding="utf-8"))["DeploymentCards"]
    out = []
    for c in cards:
        if (c["Affiliation"] not in ("Empire", "Mercenaries") or c["Restriction"] == "SkirmishOnly"
                or "Skirmish Upgrade" in c["Traits"] or not c["Attack"]):
            continue
        if name and c["Name"].lower() != name.lower():
            continue
        surges, bonus = [], Counter()
        for s in c["SimpleAbilities"]:
            cost = s.count("<surge>:") and s.split(":")[0].count("<surge>")
            text = ia_text(s.split(":", 1)[1] if cost else s)
            eff = parse_effect(text, strict=False)
            if cost:
                surges.append((cost, eff))
            else:  # always-on modifier; ignore keywords like Mobile/Reach and defense bonuses
                bonus.update({k: v for k, v in eff.items() if k in NUMERIC})
        reroll, notes = 0, []
        for ability in c["ComplexAbilities"]:
            plain = re.sub(r"<[^>]+>", "", ability).strip()
            body = plain.split(":", 1)[1].strip() if ":" in plain.split(".")[0] else plain
            if m := re.fullmatch(r"While attacking, you may reroll (\d) attack dic?e\.", body):
                reroll += int(m[1])
            elif "reroll" in plain.lower():
                notes.append(plain)
        label = c["Name"] + (f", {c['SubName']}" if c["SubName"] else "")
        out.append(Attack(
            f"{label} [{'elite' if c['IsElite'] else 'regular'}]",
            [d.lower() for d in c["Attack"]], surges, bonus, c["AttackType"].lower(),
            stats={"cost": c["PointsCost"], "reinforce": c["ReinforcementCost"] or None,
                   "health": c["Health"], "speed": c["Speed"], "group": c["GroupSize"],
                   "defense": [d.lower() for d in c["Defense"]], "source": "IA",
                   "unique": c["IsUnique"]},
            reroll=reroll, notes=notes))
    return out


# ---------------------------------------------------------------- dice

def load_dice():
    d = load_yaml(DATA / "dice.yaml")
    return d["attack"], d["defense"]


ATTACK_FACES, DEFENSE_FACES = load_dice()


@lru_cache(maxsize=None)
def pool_distribution(dice, kind):
    """Distribution of summed results for a pool: {(field totals...): probability}."""
    faces, fields = ((ATTACK_FACES, ("damage", "surge", "accuracy")) if kind == "attack"
                     else (DEFENSE_FACES, ("block", "evade", "dodge")))
    dist = Counter({(0, 0, 0): 1.0})
    for die in dice:
        new = Counter()
        for totals, p in dist.items():
            for face in faces[die]:
                vals = tuple(t + int(face.get(f, 0)) for t, f in zip(totals, fields))
                new[vals] += p / len(faces[die])
        dist = new
    return dist


# ---------------------------------------------------------------- resolution

def best_surge_spend(surges, available, base, block, rng):
    """Choose which surge abilities to use. Returns (target damage, effect used)."""
    best = None
    for n in range(len(surges) + 1):
        for combo in itertools.combinations(surges, n):
            if sum(cost for cost, _ in combo) > available:
                continue
            eff = Counter(base)
            for _, s in combo:
                eff.update(s)
            if rng is not None and eff["accuracy"] < max(rng, 1):
                dmg = 0  # miss
            else:
                dmg = max(0, eff["damage"] - max(0, block - eff["pierce"]))
            extras = sum(v for k, v in eff.items() if k not in NOT_EXTRAS and v > 0)
            key = (dmg, extras)
            if best is None or key > best[0]:
                best = (key, dmg, eff)
    return best[1], best[2]


ATK_FIELDS = ("damage", "surge", "accuracy")
DEF_FIELDS = ("block", "evade", "dodge")


def face_totals(faces, fields):
    return tuple(sum(int(f.get(k, 0)) for f in faces) for k in fields)


def mean_damage(dist):
    """Expected damage of an outcome distribution {(damage, triggers): p}."""
    return sum(o[0] * p for o, p in dist.items())


def mix(weighted):
    """Combine [(distribution, weight)] into one distribution."""
    out = Counter()
    for dist, w in weighted:
        for o, p in dist.items():
            out[o] += p * w
    return out


def resolve(attack, defense_dice, rng=None, defense_reroll=0):
    """Return (damage distribution, trigger rates of extra effects).

    With rerolls, both players reroll optimally for expected damage: the attacker
    first (seeing both pools), then the defender (seeing the attacker's new result).
    """
    if attack.type == "melee":
        rng = None

    @lru_cache(maxsize=None)
    def final(at, dt):
        """Outcome of fully-rolled pools: (target damage, tuple of triggered extras)."""
        (dmg, surge, acc), (block, evade, dodge) = at, dt
        if dodge:
            return (0, ())
        base = Counter(attack.bonus)
        base["damage"] += dmg
        base["accuracy"] += acc
        available = max(0, surge + base.pop("surge", 0) - evade)
        done, eff = best_surge_spend(attack.surges, available, base, block, rng)
        if done:  # blast/cleave/conditions need the target to suffer damage
            trig = tuple(sorted(f"{k} {v}" if k in NUMERIC else k
                                for k, v in eff.items() if k not in NOT_EXTRAS and v > 0))
        else:  # recover works even on a miss
            trig = (f"recover {eff['recover']}",) if eff["recover"] else ()
        return (done, trig)

    if not attack.reroll and not defense_reroll:
        dist = Counter()
        for at, pa in pool_distribution(tuple(attack.dice), "attack").items():
            for dt, pd in pool_distribution(tuple(defense_dice), "defense").items():
                dist[final(at, dt)] += pa * pd
    else:
        dist = _resolve_with_rerolls(attack, defense_dice, defense_reroll, final)

    damage, triggers = Counter(), Counter()
    for (done, trig), p in dist.items():
        damage[done] += p
        for t in trig:
            triggers[t] += p
    return damage, triggers


def _reroll_choices(n, k):
    return [s for size in range(1, min(n, k) + 1) for s in itertools.combinations(range(n), size)]


def _resolve_with_rerolls(attack, defense_dice, defense_reroll, final):
    a_faces = [ATTACK_FACES[d] for d in attack.dice]
    d_faces = [DEFENSE_FACES[d] for d in defense_dice]
    a_choices = _reroll_choices(len(a_faces), attack.reroll)
    d_choices = _reroll_choices(len(d_faces), defense_reroll)

    def rerolled(idx, subset, faces):
        """All (new index tuple, probability) after rerolling the dice in subset."""
        options = [range(len(faces[i])) for i in subset]
        weight = 1 / max(1, len(list(itertools.product(*options))))
        for new in itertools.product(*options):
            out = list(idx)
            for i, f in zip(subset, new):
                out[i] = f
            yield tuple(out), weight

    @lru_cache(maxsize=None)
    def dtot(idx):
        return face_totals([d_faces[i][f] for i, f in enumerate(idx)], DEF_FIELDS)

    @lru_cache(maxsize=None)
    def atot(idx):
        return face_totals([a_faces[i][f] for i, f in enumerate(idx)], ATK_FIELDS)

    @lru_cache(maxsize=None)
    def a_rerolled(aidx, subset):
        """Attack totals after rerolling subset, grouped: ((totals, probability), ...)."""
        out = Counter()
        for n, w in rerolled(aidx, subset, a_faces):
            out[atot(n)] += w
        return tuple(out.items())

    # Choices are made on expected damage (cheap floats); the full outcome
    # distribution is only built for the option actually chosen.
    @lru_cache(maxsize=None)
    def defender_choice(at, didx):
        best, best_exp = None, final(at, dtot(didx))[0]  # keep; ties favour not rerolling
        for s in d_choices:
            e = sum(final(at, dtot(n))[0] * w for n, w in rerolled(didx, s, d_faces))
            if e < best_exp:
                best, best_exp = s, e
        return best, best_exp

    @lru_cache(maxsize=None)
    def defender_dist(at, didx):
        s, _ = defender_choice(at, didx)
        if s is None:
            return {final(at, dtot(didx)): 1.0}
        return mix(({final(at, dtot(n)): 1.0}, w) for n, w in rerolled(didx, s, d_faces))

    @lru_cache(maxsize=None)
    def attacker_dist(aidx, didx):
        best, best_exp = None, defender_choice(atot(aidx), didx)[1]
        for s in a_choices:
            e = sum(defender_choice(at, didx)[1] * w for at, w in a_rerolled(aidx, s))
            if e > best_exp:
                best, best_exp = s, e
        if best is None:
            return defender_dist(atot(aidx), didx)
        return mix((defender_dist(at, didx), w) for at, w in a_rerolled(aidx, best))

    all_a = list(itertools.product(*[range(len(f)) for f in a_faces]))
    all_d = list(itertools.product(*[range(len(f)) for f in d_faces]))
    if not d_choices:  # without defender rerolls only the defense totals matter
        d_groups = Counter(dtot(d) for d in all_d)
        canon = {t: next(d for d in all_d if dtot(d) == t) for t in d_groups}
        d_weighted = [(canon[t], n) for t, n in d_groups.items()]
    else:
        d_weighted = [(d, 1) for d in all_d]
    w = 1 / (len(all_a) * len(all_d))
    return mix((attacker_dist(a, d), w * n) for a in all_a for d, n in d_weighted)


def expected(dist):
    return sum(k * p for k, p in dist.items())


# ---------------------------------------------------------------- CLI

def describe_surges(attack):
    def one(cost, eff):
        txt = ", ".join(f"{k} {v}" if k in NUMERIC else k for k, v in eff.items())
        return f"{cost}s: {txt}" if cost > 1 else txt
    return "; ".join(one(c, e) for c, e in attack.surges) or "none"


def report(attack, rng, defenses, defense_reroll=0):
    print(f"\n{attack.name}")
    bonus = ", ".join(f"{k} {v:+}" for k, v in attack.bonus.items() if v)
    print(f"  dice: {' '.join(attack.dice)}   surges: {describe_surges(attack)}"
          + (f"   always: {bonus}" if bonus else "")
          + (f"   reroll: {attack.reroll} attack" if attack.reroll else "")
          + (f"   defender reroll: {defense_reroll}" if defense_reroll else "")
          + (f"   range: {rng}" if rng is not None and attack.type != "melee" else "   (accuracy ignored)"))
    for d in defenses:
        dist, trig = resolve(attack, d, rng, defense_reroll)
        at_least = "  ".join(f">={k}:{sum(p for j, p in dist.items() if j >= k):4.0%}"
                             for k in range(1, max(dist) + 1))
        print(f"  vs {'+'.join(d) or 'none':6} expected {expected(dist):4.2f}   {at_least}")
        if trig:
            print(" " * 13 + "triggers: " + ", ".join(f"{k} {p:.0%}" for k, p in sorted(trig.items())))
    for note in attack.notes:
        print(f"  not modelled: {note}")


def compare(costs, rng, sort_by):
    attacks = [a for f in sorted((DATA / "enemies").glob("*.yaml")) for a in enemy_attacks(f.stem)]
    attacks += ia_attacks()
    rows = []
    for a in attacks:
        if a.stats.get("cost") not in costs:
            continue
        vb, vw = (expected(resolve(a, [d], rng)[0]) for d in ("black", "white"))
        s = a.stats
        rows.append({"name": a.name, "src": s["source"], "unique": s.get("unique"), "cost": s["cost"],
                     "reinf": s["reinforce"] or "-", "grp": s["group"] or "?",
                     "hp": s["health"], "spd": s["speed"] or "?",
                     "def": "+".join(s["defense"] or []) or "?",
                     "type": (a.type or "?")[:6], "dice": " ".join(a.dice),
                     "black": vb, "white": vw, "rr": a.reroll, "notes": bool(a.notes)})
    key = {"cost": lambda r: (r["cost"], -r["black"]), "black": lambda r: -r["black"],
           "white": lambda r: -r["white"], "hp": lambda r: -(r["hp"] or 0)}[sort_by]
    rows.sort(key=key)
    head = f"{'':1} {'name':40} {'cost':>4} {'rnf':>3} {'grp':>3} {'hp':>3} {'spd':>3} {'def':12} {'type':6} {'dice':24} {'rr':>2} {'vsBlk':>5} {'vsWht':>5}"
    print(head)
    print("-" * len(head))
    for r in rows:
        mark = "*" if r["src"] == "ours" else "u" if r["unique"] else " "
        rr = (str(r["rr"]) if r["rr"] else "") + ("~" if r["notes"] else "") or "-"
        print(f"{mark} {r['name'][:40]:40} {r['cost']:>4} {r['reinf']:>3} {r['grp']:>3} {r['hp']:>3} "
              f"{r['spd']:>3} {r['def'][:12]:12} {r['type']:6} {r['dice'][:24]:24} {rr:>2} {r['black']:5.2f} {r['white']:5.2f}")
    print("\n* = this project's enemies; u = official unique figure (often overcosted).")
    print("Expected damage is per figure, per attack"
          + (f", at range {rng}." if rng is not None else ", accuracy ignored."))
    print("rr = attack dice rerolled (optimally); ~ = has reroll text that isn't modelled"
          " (conditional or costed; see --ia NAME).")
    print("Official cards: surges, always-on modifiers and unconditional attack rerolls only;"
          " other card text isn't modelled.")


def find_weapon(name):
    doc = load_yaml(DATA / "items" / "weapons.yaml")
    for cat in ("melee", "ranged", "magical"):
        for w in doc.get(cat, []):
            if w["name"].lower() == name.lower():
                if not w.get("dice"):
                    raise SystemExit(f"{w['name']} has no dice yet")
                return w, cat
    raise SystemExit(f"no weapon named {name!r}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("enemy", nargs="?", help="enemy file name, e.g. charr_ash_walker")
    ap.add_argument("--variant", choices=["regular", "elite"])
    ap.add_argument("--weapon", help="weapon name from data/items/weapons.yaml")
    ap.add_argument("--ia", help="official IA deployment card name, e.g. 'Royal Guard'")
    ap.add_argument("--dice", nargs="+", help="attack dice, e.g. red green")
    ap.add_argument("--surge", action="append", default=[], help="surge ability (repeatable)")
    ap.add_argument("--bonus", help="always-on modifier, e.g. '+1 damage, Pierce 1'")
    ap.add_argument("--range", type=int, help="distance to target; enforces accuracy for ranged attacks")
    ap.add_argument("--defense", nargs="*", action="append",
                    help="defense pool(s) to test (default: black, then white)")
    ap.add_argument("--reroll", type=int, default=0, help="extra attack dice the attacker may reroll")
    ap.add_argument("--defense-reroll", type=int, default=0, help="defense dice the defender may reroll")
    ap.add_argument("--compare", nargs="+", type=int, metavar="COST",
                    help="table of every figure (ours and official) at these costs")
    ap.add_argument("--sort", choices=["cost", "black", "white", "hp"], default="cost")
    a = ap.parse_args()
    defenses = a.defense or [["black"], ["white"]]
    extra = parse_effect(a.bonus) if a.bonus else Counter()

    if a.compare:
        return compare(set(a.compare), a.range, a.sort)
    if a.enemy:
        attacks = enemy_attacks(a.enemy, a.variant)
        if not attacks:
            raise SystemExit(f"{a.enemy} has no attack yet")
    elif a.ia:
        attacks = ia_attacks(a.ia)
        if not attacks:
            raise SystemExit(f"no official Imperial/Mercenary deployment card named {a.ia!r}")
    elif a.weapon:
        w, cat = find_weapon(a.weapon)
        attacks = [Attack.from_strings(w["name"], w["dice"], w.get("surges") or [],
                                       type="melee" if cat == "melee" else "ranged")]
    elif a.dice:
        attacks = [Attack.from_strings("custom attack", a.dice, a.surge)]
    else:
        ap.error("give an enemy, --ia, --weapon, --dice or --compare")
    for atk in attacks:
        atk.bonus.update(extra)
        atk.reroll += a.reroll
        report(atk, a.range, defenses, a.defense_reroll)


if __name__ == "__main__":
    main()
