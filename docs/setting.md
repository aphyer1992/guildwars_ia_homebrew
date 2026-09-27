# Guild Wars setting primer

Background for designing content. Sources: the official Guild Wars wiki
(wiki.guildwars.com), researched 2026-09-26. The planned first campaign covers the
opening of **Guild Wars: Prophecies**, from pre-Searing Ascalon through the mission
**The Frost Gate**. See `docs/campaign-research.md` for the missions and enemies, and
`docs/skills-translation.md` for turning GW mechanics into IA ones.

## The world

- **Tyria** is the continent. The early Prophecies campaign takes place in its
  north-east: the human kingdom of **Ascalon**, then the **Shiverpeak Mountains** that
  separate it from **Kryta**.
- **Dates** use the AE calendar. Pre-Searing Ascalon is **1070 AE**. The post-Searing
  missions pick up about two years later.
- **Humans** worship the Six Gods: Dwayna (healing), Balthazar (war), Grenth (death),
  Lyssa (illusion), Melandru (nature) and Kormir (later). Monk "prayers" are directed
  to them. Grenth matters to necromancers such as Olias, and Lyssa to mesmers such as
  Norgu and General Morgahn.

## Ascalon and the Searing

- **Pre-Searing Ascalon** is green, prosperous and confident. Its defence against the
  Charr is the **Great Northern Wall**.
  - King **Adelbern** rules. His heir, **Prince Rurik**, leads the **Ascalon Vanguard**,
    a force outside the king's direct control.
  - The pre-Searing threats are small: **Grawl** (primitive ape-like tribes), wildlife,
    and a Charr infiltrator, **Vatlaaw Doomtooth**, hiding in a bunker in the Catacombs
    under the capital.
- **The Searing.** The Charr shaman caste, through **Bonfaaz Burntfur**, called down
  burning crystals from the sky using the **Cauldron of Cataclysm** and the power of
  the Charr's gods, the Titans.
  - Forests burned, rivers dried up, and the cities of Ascalon, **Rin** and **Surmia**
    were ruined.
  - The Wall itself survived, but the kingdom was broken and the Charr poured south.
  - This is the campaign's hinge. After the intro mission there is no going back.
- **Post-Searing Ascalon** is ash, craters and ruins, overrun by Charr warbands,
  burrowing **devourers** and **gargoyles**.
  - Rurik fights back: he retakes the Wall, rescues captives and finds the horn
    **Stormcaller**, which saves Rin.
  - King Adelbern refuses to abandon Ascalon and **banishes Rurik**.
  - Rurik leads refugees over the Shiverpeaks towards Kryta.

## Factions

### Charr (Adversary)

- **Who they are:** feline, horned, bestial and industrious. They see ambush as just as
  honourable as open battle.
- **Religion:** they worship the Titans through a powerful **Shaman caste** and keep
  sacred, ever-burning flames in **Flame Temples**, tended by Flame Keepers.
  - Warbands carry braziers lit from the temple fires and burn effigies at camp.
    Humans learned to read the effigies as signs that Charr were nearby.
  - **Ember Bearers** carry the sacred flame.
- **Organisation:** warbands within four High Legions: Ash, Blood, Flame and Iron.
  - The **Ash Legion** supplies front-line dark magic (for example the Ash Walker).
  - The shamans are effectively the **Flame Legion**.
- **In battle:** Charr field every GW profession.
  - Warriors: axe and sword infantry.
  - Rangers: fire-arrow archers.
  - Monks: shamans.
  - Necromancers: Ash Walker, Ashen Claw.
  - Mesmers: Mind Spark, Chaot.
  - Elementalists: Fire Caller, Flame Wielder.
  - The "Fiend"/"Storm"/"Claw" names are the tougher versions of basic units, which
    maps neatly onto IA's regular and elite figures.
- **Key figures:**
  - **Bonfaaz Burntfur:** shaman-chieftain and fire Elementalist of the Burnt Warband.
    He caused the Searing and is the villain of the Ascalon act, defeated in Nolani
    Academy.
  - **Vatlaaw Doomtooth:** a Charr ranger, the boss of the intro mission.

### Stone Summit (Adversary)

- **Who they are:** an extremist, xenophobic dwarf faction that broke from the
  **Deldrimor** dwarves. They believe only they are fit to rule.
- **Leader:** **Dagnar Stonepate**, cousin of the Deldrimor king **Jalis Ironhammer**.
  He started a dwarven civil war.
- **Style:** brute force.
  - They use enslaved creatures: giants, dolyaks, snow beasts.
  - They build **ice golems**, using the Heart of Ice.
  - They man **ballistae and catapults**; Engineers crew the siege weapons.
- **In the story:** they blockade the passes the refugees need. At the Frost Gate,
  Dagnar (riding an **Ice Drake**) kills Prince Rurik while Rurik covers the refugees'
  escape. **In this campaign, that only happens if the heroes lose the finale** (see
  `docs/campaign-research.md`).
- **Level gap:** they're tougher than the Charr (roughly levels 9–13 against 5–8). They
  fit a higher threat level in the campaign's second act.

### Beasts of Tyria

- **Devourers:** huge two-tailed scorpion-beasts.
  - They **burrow and ambush**, bursting out of the ground when prey comes near, and
    hunt in groups.
  - They can be tamed from eggs, like Old Mac's Joe, and Charr rangers sometimes keep
    them as pets.
  - Ascalonians eat the eggs and use the stingers as medicine.
  - They're vulnerable to cold.
- **Gargoyles:** stone-winged casters found in the Catacombs before the Searing and all
  over Ascalon after it.
  - They're **fragile**, with low armour for their level.
  - The Shatter Gargoyle is a mesmer, the Flash Gargoyle an air elementalist and the
    Resurrect Gargoyle a monk.
- **Grawl:** primitive ape-like tribes with a religious hierarchy.
  - They gather at shrines to Tyria's gods.
  - Post-Searing, they're split between rival sects: Petitioners and Heretics.
  - **Adversary** in this project (designer, 2026-09-26): they're organised and have
    shamans. How to include them without a third basic melee unit is still open; see
    `docs/campaign-research.md`.
- **Elementals:** **Boulder Elementals** are rock brutes, hard to cut but vulnerable to
  hammers. **Ice Golems** are Stone Summit constructs, so they count as **Adversary**,
  not Beast (designer, 2026-09-26).
- **Shiverpeak creatures:**
  - **Centaurs:** Shiverpeak warriors, longbows and protector-monks, resistant to cold.
  - **Snow Ettins:** ogre hammer-warriors.
  - **Minotaurs:** so stubborn that people domesticated dolyaks instead.
  - **Frostfire Dryders:** spider-centaur necromancers who hex their targets with
    damage over time.
  - **Dolyaks:** yak-like beasts. The Stone Summit ride armoured ones.

### Allies

- **Ascalon:** Prince Rurik, a bold and reckless Warrior who leads from the front. He's
  the natural **IA ally card**, and the story's protect or escort target. Also:
  Captain Calhaan (at the Wall), Warmaster/Sir Tydus, Siegemaster Lormar, Ascalon
  guards and militia, and the refugees.
- **Deldrimor dwarves:** King Jalis Ironhammer (a Warrior, whose skills include *"I
  Will Avenge You!"*, also the name of an Old Mac card), and **Rornak Stonesledge**, a
  dwarf ranger and spy who drives both Shiverpeak bonus objectives.

## Where the heroes come from

The heroes are NPCs gathered from across all of Guild Wars, not just Prophecies. Some
are anachronistic for 1070–1072 AE. That's a deliberate homebrew choice.

| Hero | GW profession | Origin |
|---|---|---|
| Old Mac | Warrior | Pre-Searing Ascalon farmer. He hatched Joe the devourer from an egg taken as compensation for his bull, and later fled over the Shiverpeaks with the refugees. **Native to this campaign.** |
| Cynn | Fire Elementalist (Paragon secondary) | Prophecies henchman, born in **Surmia** around 1051 AE. A former child prodigy with a dark streak who bites off more than she can chew. **Native: Ruins of Surmia is her ruined hometown.** |
| Argo | Elementalist | Factions: champion of the Luxon Turtle Clan. Honourable and merciful. As a henchman he casts fire; as a boss he uses earth magic (*Stoneflesh Aura*), which fits this project's earth-armour Argo. |
| Acolyte Jin | Ranger (Marksmanship) | Nightfall hero: a grim, action-first Canthan archer of the Zaishen Order. |
| Olias | Necromancer | Nightfall hero, obsessed with Grenth and death. Minions and life drain. |
| Zenmai | Assassin | Nightfall hero: a stoic dagger assassin atoning for her past with the Am Fah gang. |
| Norgu | Mesmer | Nightfall hero: a theatrical, egotistical, food-loving Vabbian actor and leader of the Lyssan Fools. |
| General Morgahn | Paragon (Ranger secondary) | Nightfall hero: a veteran Kournan spear-general who turned against Warmarshal Varesh, devoted to Lyssa and seeking redemption. |

**Side-mission hooks.** IA gives each hero a personal side mission (the red side-mission
cards):
- **Old Mac:** a pre-Searing farm or devourer-egg story, echoing the quest *A Mesmer's
  Burden*.
- **Cynn:** returning to Surmia.

## Naming notes

- **Charr Flame Wielder:** named after the MMO's Level 8 Charr fire Elementalist. The
  MMO's weaker version is the **Charr Fire Caller**. Casters stay as single cards, with
  no regular/elite split (designer, 2026-09-26).
- **Charr Axe Warrior / Axe Fiend** and **Blade Warrior / Blade Storm:** regular/elite
  pairs named as in the MMO (Fort Ranik, the Great Northern Wall).
