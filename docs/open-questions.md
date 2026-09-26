# Open questions

Ambiguities found while transcribing the original Word docs into `data/`
(2026-09-26). Where a guess was needed to fill a field, the guess is noted. Resolve by
editing the data and deleting the item here.

## Terminology

1. **The third attribute has three names**: *Intellect* (Olias, Jin, Zenmai), *Spellcraft*
   (Argo), *Arcana* (Cynn), and Norgu's cards say *Arcane check*. The data uses
   `intellect` for now. Pick one; it will be printed on cards.
2. **Attribute dice letters**: in `Strength BG`, is `B` blue or black? Kept as raw
   letters until decided.
   *Suggestion (Claude):* almost certainly blue. Attribute tests pass on surges, and
   defense dice have no surge faces, so a black die could never contribute. Every hero
   also follows the same B → BG → BGY ladder, which fits blue/green/yellow. Pass rates:
   B 33%, BG 67%, BGY 89% (see `docs/rules-primer.md`).
3. **Move vs Speed**: Zenmai's sheet says *Speed 5*; the others say *Move*. The data uses
   `speed`.
4. **Penetrating Attack** (Jin, 3XP) says "martial weapon". The item categories are
   melee / ranged / magical. Should it be "melee or ranged"? It also says "a die showing
   3 or more range"; is that accuracy?
5. **Beast trait**: Charr Stalker, Old Mac's *Here, Joe!* and the Beasts of Tyria agenda
   all refer to Beast figures, but no enemy has traits assigned yet. Which groups are
   Beasts (Devourers? Charr?)?

## Missing stats

6. **Speed** is missing for Olias, Acolyte Jin, Charr Ash Walker, Charr Mind Spark.
7. **Attributes** are missing for General Morgahn and Old Mac; Norgu has no stats at all.
8. **Group size** is missing for every enemy deployment.
9. **Single-figure enemies**: Ash Walker, Mind Spark and Flamecaller have one cost (5), no
   reinforcement cost and no elite version. Are they single-figure groups, or not finished?
10. **XP costs** are missing on several class cards: Zenmai *Mo Zing*; Old Mac *I Will
    Avenge You!*, *Heal as One*; all of Argo's and Cynn's class cards; the Adversary class
    cards.

## Guesses made in the data

11. **Attack type** (melee or ranged) is only stated for the Carrion Devourer. Inferred:
    Stalker ranged, Axe Warrior melee, Blade Storm melee, Mind Spark ranged, Flamecaller
    ranged. **Ash Walker is left blank.**
12. **Charr Stalker "Move (Rampage) as One"** was split into a regular *Move as One* (ally
    moves) and an elite *Rampage as One* (ally attacks).
13. **"Charr Axe Warrior (Fiend)"** was read as: the elite version is named *Charr Axe Fiend*.

## Unfinished or inconsistent cards

14. **Argo**: *Shockwave* refers to "Crystal Wave", which doesn't exist yet. *Sliver
    Armor* appears twice: once as an ability and once as an unfinished class card.
15. **Old Mac, I Will Avenge You!**: the second sentence ("If Old Mac is wounded, exhaust
    this card during your activation. Joe interrupts to perform an action.") reads like a
    separate effect. Is it an alternative trigger, or the wounded-side version?
16. **Charr Flamecaller**: the surge ability is blank.
17. **Stone Summit Wrath**: the 2-influence agenda card has no name. **Beasts of Tyria**:
    the 1-influence discard card has no name or text.
