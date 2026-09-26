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
ATTACK_DICE_NAMES = {"red", "blue", "green", "yellow"}


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
    hero: bool = False                           # heroes may surge to recover strain

    @property
    def perspective(self):
        """Default value-model perspective: heroes attack enemies, enemies attack heroes."""
        return "vs_enemies" if self.hero else "vs_heroes"

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
            f"{v.get('name', e['name'])} [{vname}]", v.get("dice") or e["attack"]["dice"],
            v.get("surges") or [],
            bonus=e["attack"].get("bonus"), type=e["attack"].get("type"),
            stats={"cost": v.get("cost"), "reinforce": v.get("reinforce"),
                   "health": v.get("health"), "speed": e.get("speed"),
                   "group": v.get("group_size", e.get("group_size")),
                   "defense": e.get("defense"), "source": "ours"}))
    return out


def ia_attacks(name=None):
    """Official deployment cards (campaign-legal, no skirmish upgrades).

    Includes Rebel ally cards (Rebellion) as benchmarks: they are peers of Adversary
    figures in cost and stats, even though the heroes control them in IA.
    """
    cards = json.loads(IA_CARDS.read_text(encoding="utf-8"))["DeploymentCards"]
    out = []
    for c in cards:
        if (c["Affiliation"] not in ("Empire", "Mercenaries", "Rebellion") or c["Restriction"] == "SkirmishOnly"
                or "Skirmish Upgrade" in c["Traits"] or not c["Attack"]):
            continue
        if name and c["Name"].lower() != name.lower():
            continue
        if any(d.lower() not in ATTACK_DICE_NAMES for d in c["Attack"]):
            continue  # variable attacks (General Weiss, IG-88) are listed as 'Unknown'
        surges, bonus = [], Counter()
        for s in c["SimpleAbilities"]:
            cost = s.count("<surge>:") and s.split(":")[0].count("<surge>")
            text = ia_text(s.split(":", 1)[1] if cost else s)
            eff = parse_effect(text, strict=False)
            if cost:
                surges.append((cost, eff))
            else:  # always-on modifier; ignore keywords like Mobile/Reach and defense bonuses
                bonus.update({k: v for k, v in eff.items() if k in NUMERIC or k in CONDITIONS})
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
                   "unique": c["IsUnique"], "rebel": c["Affiliation"] == "Rebellion"},
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

def damage_score(eff, dmg):
    """Default objective: most damage; ties go to more extras."""
    return (dmg, sum(v for k, v in eff.items() if k not in NOT_EXTRAS and v > 0))


def best_surge_spend(surges, available, base, block, rng, score=damage_score):
    """Choose which surge abilities to use. Returns (target damage, effect used, score)."""
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
            key = (score(eff, dmg), dmg)
            if best is None or key > best[0]:
                best = (key, dmg, eff)
    return best[1], best[2], best[0][0]


# ---------------------------------------------------------------- value model

VALUE_MODEL = Path(__file__).resolve().parent / "value_model.yaml"
HERO_STRAIN_SURGE = (1, Counter({"strain": 1}))  # IA: a hero may spend 1 surge to recover 1 strain


def load_perspectives():
    return load_yaml(VALUE_MODEL)["perspectives"]


HERO_HEALTH = 12  # assumed attacker health for hero attacks (Focus scaling)


def value_scorer(model, situation, attacker_hp=None):
    """Score an attack result in damage-equivalents for one situation (see value_model.yaml)."""
    kill = model["kill_bonus"]
    worth = dict(model["conditions"])
    # Focus is only worth its full value if the attacker survives to use it.
    worth["focus"] = worth.get("focus", 0) * min(1, ((attacker_hp or HERO_HEALTH) + 2) / 10)
    hp = situation.get("target_hp", 99)
    cleave_hp = situation.get("cleave_hp")
    blast_hps = situation.get("blast") or []
    friendly = situation.get("blast_friendly", 0)
    missing_hp = situation.get("attacker_missing_hp", 0)
    missing_strain = situation.get("attacker_missing_strain", 0)
    cleave_w = model.get("cleave_weight", 1.0)  # worth of a point of cleave damage vs main-target damage
    blast_w = model.get("blast_weight", 1.0)

    def score(eff, dmg):
        v = min(dmg, hp) + (kill if dmg >= hp else 0)
        if dmg:
            if eff["cleave"] and cleave_hp:
                v += (min(eff["cleave"], cleave_hp) * cleave_w
                      + (kill if eff["cleave"] >= cleave_hp else 0))
            if eff["blast"]:
                v += sum(min(eff["blast"], b) * blast_w + (kill if eff["blast"] >= b else 0)
                         for b in blast_hps)
                v -= eff["blast"] * friendly
            for cond, w in worth.items():
                if eff[cond] and (cond in ("focus", "hidden") or dmg < hp):
                    v += w  # every condition keyword needs >= 1 damage on the target
        v += min(eff["recover"], missing_hp) * model["recover_weight"]
        v += min(eff["strain"], missing_strain) * model["strain_value"]
        return v
    return score


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


def resolve(attack, defense_dice, rng=None, defense_reroll=0, score=None):
    """Return (damage distribution, trigger rates of extra effects, expected score).

    `score(eff, dmg)` is the objective surges and rerolls are chosen for (default:
    damage). With rerolls, both players reroll optimally for the expected score: the
    attacker first (seeing both pools), then the defender (seeing the new result).
    """
    if attack.type == "melee":
        rng = None
    value_mode = score is not None
    score = score or damage_score
    surges = attack.surges + ([HERO_STRAIN_SURGE] if attack.hero else [])

    @lru_cache(maxsize=None)
    def final(at, dt):
        """Outcome of fully-rolled pools: (score, target damage, triggered extras)."""
        (dmg, surge, acc), (block, evade, dodge) = at, dt
        base = Counter(attack.bonus)
        base["damage"] += dmg
        base["accuracy"] += acc
        available = max(0, surge + base.pop("surge", 0) - evade)
        # A dodge is a miss (infinite accuracy needed), but surges can still recover.
        done, eff, s = best_surge_spend(surges, available, base, block,
                                        float("inf") if dodge else rng, score)
        if done:  # blast/cleave/conditions need the target to suffer damage
            trig = tuple(sorted(f"{k} {v}" if k in NUMERIC else k
                                for k, v in eff.items() if k not in NOT_EXTRAS and v > 0))
        else:  # recover works even on a miss
            trig = (f"recover {eff['recover']}",) if eff["recover"] else ()
        return (s if value_mode else done, done, trig)

    if not attack.reroll and not defense_reroll:
        dist = Counter()
        for at, pa in pool_distribution(tuple(attack.dice), "attack").items():
            for dt, pd in pool_distribution(tuple(defense_dice), "defense").items():
                dist[final(at, dt)] += pa * pd
    else:
        dist = _resolve_with_rerolls(attack, defense_dice, defense_reroll, final)

    damage, triggers, total = Counter(), Counter(), 0.0
    for (s, done, trig), p in dist.items():
        damage[done] += p
        total += s * p
        for t in trig:
            triggers[t] += p
    return damage, triggers, total


def value(attack, defense_dice, perspective, rng=None, defense_reroll=0):
    """Weighted value across a perspective's situations, plus the per-situation values."""
    model = load_perspectives()[perspective]
    per = []
    for sit in model["situations"]:
        scorer = value_scorer(model, sit, None if attack.hero else attack.stats.get("health"))
        v = resolve(attack, defense_dice, rng, defense_reroll, scorer)[2]
        per.append((sit["name"], sit["weight"], v))
    total_w = sum(w for _, w, _ in per)
    return sum(w * v for _, w, v in per) / total_w, per


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


RANGES = (1, 4, 6)  # adjacent, medium, long


def value_ranges(attack):
    """Ranges to value an attack at: range 1 for everything, plus 4 and 6 if ranged."""
    return RANGES if attack.type == "ranged" else RANGES[:1]


def range_values(attack, perspective=None, defense_reroll=0):
    """{range: value averaged over black and white} for the attack's value ranges."""
    persp = perspective or attack.perspective
    return {r: sum(value(attack, [d], persp, r, defense_reroll)[0] for d in ("black", "white")) / 2
            for r in value_ranges(attack)}


def fmt_ranges(vals):
    return "  ".join(f"{vals[r]:5.2f}" if r in vals else "    -" for r in RANGES)


def report(attack, rng, defenses, defense_reroll=0, perspective=None):
    print(f"\n{attack.name}")
    bonus = ", ".join(f"{k} {v:+}" for k, v in attack.bonus.items() if v)
    print(f"  dice: {' '.join(attack.dice)}   surges: {describe_surges(attack)}"
          + (f"   always: {bonus}" if bonus else "")
          + (f"   reroll: {attack.reroll} attack" if attack.reroll else "")
          + (f"   defender reroll: {defense_reroll}" if defense_reroll else "")
          + (f"   range: {rng}" if rng is not None and attack.type != "melee" else "   (accuracy ignored)"))
    for d in defenses:
        dist, trig, _ = resolve(attack, d, rng, defense_reroll)
        at_least = "  ".join(f">={k}:{sum(p for j, p in dist.items() if j >= k):4.0%}"
                             for k in range(1, max(dist) + 1))
        print(f"  vs {'+'.join(d) or 'none':6} expected {expected(dist):4.2f}   {at_least}")
        if trig:
            print(" " * 13 + "triggers: " + ", ".join(f"{k} {p:.0%}" for k, p in sorted(trig.items())))
        if perspective:
            v, per = value(attack, d, perspective, rng, defense_reroll)
            print(" " * 13 + f"VALUE {v:4.2f} ({perspective}): "
                  + ", ".join(f"{name} {x:.2f}" for name, _, x in per))
    if perspective and rng is None:
        vals = range_values(attack, perspective, defense_reroll)
        print("  VALUE by range (avg of black & white): "
              + ", ".join(f"range {r}: {v:.2f}" for r, v in vals.items())
              + ("" if attack.type == "ranged" else "   (melee/unknown type: range 1 only)"))
    for note in attack.notes:
        print(f"  not modelled: {note}")


RANGE_HEAD = f"{'V@1':>5}  {'V@4':>5}  {'V@6':>5}"
RANGE_NOTE = ("V@1/V@4/V@6 = value-model score at range 1/4/6, averaged over black and white"
              " (tools/value_model.yaml). Ranged attacks need accuracy >= range; melee and"
              " unknown-type attacks are valued at range 1 only.")


def sort_key(sort_by, cost_first=False):
    def v(r, rng):
        return -r["vals"].get(rng, -99)
    keys = {"black": lambda r: -r["black"], "white": lambda r: -r["white"],
            "hp": lambda r: -(r.get("hp") or 0), "value": lambda r: v(r, 1),
            "v4": lambda r: v(r, 4), "v6": lambda r: v(r, 6)}
    if sort_by == "cost":
        return (lambda r: (r["cost"], v(r, 1))) if cost_first else keys["value"]
    return keys[sort_by]


def compare(costs, sort_by):
    attacks = [a for f in sorted((DATA / "enemies").glob("*.yaml")) for a in enemy_attacks(f.stem)]
    attacks += ia_attacks()
    rows = []
    for a in attacks:
        if a.stats.get("cost") not in costs:
            continue
        vb, vw = (expected(resolve(a, [d])[0]) for d in ("black", "white"))
        s = a.stats
        rows.append({"name": a.name, "src": s["source"], "unique": s.get("unique"),
                     "rebel": s.get("rebel"), "cost": s["cost"],
                     "reinf": s["reinforce"] or "-", "grp": s["group"] or "?",
                     "hp": s["health"], "spd": s["speed"] or "?",
                     "def": "+".join(s["defense"] or []) or "?",
                     "type": (a.type or "?")[:6], "dice": " ".join(a.dice),
                     "black": vb, "white": vw, "vals": range_values(a),
                     "rr": a.reroll, "notes": bool(a.notes)})
    rows.sort(key=sort_key(sort_by, cost_first=True))
    head = (f"{'':1} {'name':38} {'cost':>4} {'rnf':>3} {'grp':>3} {'hp':>3} {'spd':>3} {'def':11} "
            f"{'type':6} {'dice':22} {'rr':>2} {'dmgB':>5} {'dmgW':>5}  {RANGE_HEAD}")
    print(head)
    print("-" * len(head))
    for r in rows:
        mark = "*" if r["src"] == "ours" else "u" if r["unique"] else "r" if r["rebel"] else " "
        rr = (str(r["rr"]) if r["rr"] else "") + ("~" if r["notes"] else "") or "-"
        print(f"{mark} {r['name'][:38]:38} {r['cost']:>4} {r['reinf']:>3} {r['grp']:>3} {r['hp']:>3} "
              f"{r['spd']:>3} {r['def'][:11]:11} {r['type']:6} {r['dice'][:22]:22} {rr:>2} "
              f"{r['black']:5.2f} {r['white']:5.2f}  {fmt_ranges(r['vals'])}")
    print("\n* = this project's enemies; u = official unique figure (often overcosted);"
          " r = official Rebel ally card (a benchmark peer).")
    print("dmgB/dmgW = expected damage per figure per attack vs black/white, accuracy ignored.")
    print(RANGE_NOTE + " Enemies use the vs_heroes perspective.")
    print("rr = attack dice rerolled (optimally); ~ = has reroll text that isn't modelled"
          " (conditional or costed; see --ia NAME).")
    print("Official cards: surges, always-on modifiers and unconditional attack rerolls only;"
          " other card text isn't modelled.")


def weapon_attacks():
    doc = load_yaml(DATA / "items" / "weapons.yaml")
    return [(cat, Attack.from_strings(w["name"], w["dice"], w.get("surges") or [], hero=True,
                                      type="melee" if cat == "melee" else "ranged"))
            for cat in ("melee", "ranged", "magical") for w in doc.get(cat, []) if w.get("dice")]


def compare_weapons(sort_by):
    rows = []
    for cat, a in weapon_attacks():
        vb, vw = (expected(resolve(a, [d])[0]) for d in ("black", "white"))
        rows.append({"name": a.name, "cat": cat, "dice": " ".join(a.dice),
                     "surges": describe_surges(a), "black": vb, "white": vw,
                     "vals": range_values(a)})
    rows.sort(key=sort_key(sort_by))
    head = f"{'name':18} {'category':8} {'dice':18} {'dmgB':>5} {'dmgW':>5}  {RANGE_HEAD}   surges"
    print(head)
    print("-" * (len(head) + 30))
    for r in rows:
        print(f"{r['name'][:18]:18} {r['cat']:8} {r['dice'][:18]:18} {r['black']:5.2f} {r['white']:5.2f}"
              f"  {fmt_ranges(r['vals'])}   {r['surges']}")
    print("\ndmgB/dmgW = expected damage vs black/white, accuracy ignored.")
    print(RANGE_NOTE + " Weapons use the vs_enemies perspective (hero attacking).")
    print("Magical weapons are treated as ranged.")


CALIBRATION_SURGES = ["+1 damage", "+2 damage", "Cleave 1", "Cleave 2", "Blast 1", "Blast 2",
                      "Pierce 1", "Pierce 2", "Recover 1", "Recover 2",
                      "Stun", "Bleed", "Weaken", "Focus"]
CALIBRATION_POOLS = [["red", "green"], ["blue", "green"], ["green", "yellow"]]


def calibrate(perspectives):
    """Marginal value of each single surge ability added to typical attacks."""
    for persp in perspectives:
        hero = persp == "vs_enemies"
        print(f"\n{persp}: value added by one surge ability "
              f"(avg over pools {', '.join('+'.join(p) for p in CALIBRATION_POOLS)}; black & white)")

        def avg_value(surges):
            vals = [value(Attack.from_strings("cal", pool, surges, hero=hero,
                                              stats={"health": 6}), [d], persp)[0]
                    for pool in CALIBRATION_POOLS for d in ("black", "white")]
            return sum(vals) / len(vals)

        base = avg_value([])
        print(f"  (base value, no surge abilities: {base:.2f})")
        targets = load_perspectives()[persp].get("targets") or []
        needed = set(CALIBRATION_SURGES) | {s for t in targets for s in re.split(r" [<>] ", t)}
        rows = {s: avg_value([s]) - base for s in needed}
        for s in sorted(CALIBRATION_SURGES, key=lambda s: -rows[s]):
            print(f"  {s:12} {rows[s]:+5.2f}  {'#' * round(rows[s] * 20)}")
        for t in targets:
            left, op, right = re.fullmatch(r"(.+) ([<>]) (.+)", t).groups()
            ok = rows[left] < rows[right] if op == "<" else rows[left] > rows[right]
            print(f"  target {'PASS' if ok else 'FAIL'}: {t}  ({rows[left]:+.2f} vs {rows[right]:+.2f})")


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
    ap.add_argument("--sort", choices=["cost", "black", "white", "hp", "value", "v4", "v6"], default="cost")
    ap.add_argument("--compare-weapons", action="store_true",
                    help="table of every weapon with value at range 1/4/6")
    ap.add_argument("--value", action="store_true",
                    help="also score by the value model (tools/value_model.yaml)")
    ap.add_argument("--perspective", choices=["vs_heroes", "vs_enemies"],
                    help="value-model perspective (default: vs_enemies for weapons and --hero, else vs_heroes)")
    ap.add_argument("--calibrate", action="store_true",
                    help="show the value each single surge ability adds, per perspective")
    ap.add_argument("--hero", action="store_true",
                    help="treat a --dice attack as a hero's (may surge to recover strain)")
    a = ap.parse_args()
    defenses = a.defense or [["black"], ["white"]]
    extra = parse_effect(a.bonus) if a.bonus else Counter()

    if a.calibrate:
        return calibrate([a.perspective] if a.perspective else ["vs_heroes", "vs_enemies"])
    if a.compare_weapons:
        return compare_weapons(a.sort)
    if a.compare:
        return compare(set(a.compare), a.sort)
    if a.enemy:
        attacks = enemy_attacks(a.enemy, a.variant)
        if not attacks:
            raise SystemExit(f"{a.enemy} has no attack yet")
    elif a.ia:
        attacks = ia_attacks(a.ia)
        if not attacks:
            raise SystemExit(f"no official deployment card named {a.ia!r}")
    elif a.weapon:
        w, cat = find_weapon(a.weapon)
        attacks = [Attack.from_strings(w["name"], w["dice"], w.get("surges") or [],
                                       type="melee" if cat == "melee" else "ranged", hero=True)]
    elif a.dice:
        attacks = [Attack.from_strings("custom attack", a.dice, a.surge, hero=a.hero)]
    else:
        ap.error("give an enemy, --ia, --weapon, --dice or --compare")
    for atk in attacks:
        atk.bonus.update(extra)
        atk.reroll += a.reroll
        persp = (a.perspective or atk.perspective) if (a.value or a.perspective) else None
        report(atk, a.range, defenses, a.defense_reroll, persp)


if __name__ == "__main__":
    main()
