# Animal AI (mod data)

Animal behaviour is **data in a mod**, not code. A mod ships JSON files under the content type
`animal_ai`; the game turns them into a brain for every animal they apply to. No scripting, and it works
through the same mod loader as biomes, items and game rules.

```json
{ "contents": [ { "type": "animal_ai", "path": "ai/*.json" } ] }
```

Source in the repo: `assets/_ai/<id>.json` (packaged to `mods/homesteader/ai/` by
`tools/package_catalog_as_mods.py`). Reference: `assets/_schemas/animal_ai.schema.json`.
Example: `assets/_ai/dog_companion.json`.

## How an animal decides

Every ~0.25 s the animal walks through its `behaviors`:

1. Skip any behaviour on **cooldown**.
2. Skip any whose **`requires`** terms are not all true.
3. **Score** = `base` + the sum of `weight × value` for each **`score`** term.
4. The highest score wins. A running behaviour is only replaced when the newcomer beats it by 15% + 0.05,
   after it has run `min_s` seconds (a higher `priority` interrupts sooner).

This is *utility AI*: no state diagram to maintain. Add a rule and it competes with the others.

## Definition

| Key | Meaning |
| :--- | :--- |
| `id` | Unique snake_case id (also the file name). Later mods override earlier ones by id. |
| `applies_to` | Item ids, `*` wildcards (`*_cow`, `animal_cat_*`) and/or `species:<name>`. Exact id beats wildcard beats species. Not needed for a template. |
| `extends` | List of definition ids to build on (see Templates). |
| `abstract` | `true` = a template: never used by an animal directly, only extended. |
| `tags` | Sense tags this animal carries so others can react to it: `predator`, `prey`, `threat`, or your own. Merged through `extends`. |
| `needs` | `{ name: { start, rate_per_game_hour, min, max } }`. Values 0..1 that change over in-game time (respects the time-speed setting). |
| `senses` | `sight_m` (how far it notices things), `hear_m` (reserved). |
| `movement` | `walk_speed`, `run_speed`, `turn_speed_deg`, `max_slope_deg`, `arrive_dist_m`. |
| `animations` | Slot name → clip in the animal's GLB. `idle`, `walk`, `run` drive locomotion; other slots are whatever actions name. |
| `behaviors` | The rules (below). |

### Templates (`extends`) - keep an animal's AI to a few lines

A definition can build on others. Parents are merged first (in `extends` order), then the definition itself:
needs, animation slots, `senses` / `movement` keys override **by name**, behaviours override **by id**, and
`{"id": "x", "disabled": true}` removes an inherited behaviour. `applies_to` is never inherited.

```json
{ "id": "goat", "extends": ["livestock"], "applies_to": ["*_goat"],
  "movement": { "walk_speed": 1.3 },
  "behaviors": [ { "id": "herd", "disabled": true } ] }
```

Shipped in `assets/_ai/` (all editable; add your own):

| Template | For | Adds |
| :--- | :--- | :--- |
| `animal_base` | everything | hunger / thirst / energy, flee threats, eat + drink at `food` / `water` objects, sleep at night, wander, idle. Every animation slot falls back to `Idle`, so a rig with only idle / walk / run works. |
| `pet` | dogs, cats | boredom, follow the player, sit by them, greet |
| `livestock` | farm animals | graze in place, stay with the herd, lie down at night |
| `wildlife_prey` | deer, rabbits | bolt early from the player and from `predator` |
| `wildlife_predator` | wolves, foxes | hunt `prey` when hungry, keep away from people |
| `helper` | hired hands, people | work at the nearest `job` object by day (`work` animation), meals at a `table`, sleep at a `bed`, `come_here` event to follow you |

**No skating.** Set `movement.walk_native_mps` / `run_native_mps` to the ground speed the clips' feet actually cover
(`python tools/gait_fix.py measure <rig.glb>`); the clip then plays at real speed / native speed. If a clip's stride is
too short for the game speed (playback would be > ~1.3x), lengthen it: `python tools/gait_fix.py stretch <rig.glb>
--target <m/s>`. Do this for every rigged model that walks (players, helpers, animals).

**Movement medium.** `movement.medium` is `ground` (default), `water` (swims `depth_m` below the surface and never
leaves the water) or `air` (flies `hover_m` above the ground while moving and lands when it stops).

| Definition | Notes |
| :--- | :--- |
| `rooster` | extends `chicken`; crows at dawn (hours 5-7) and sounds the alarm at a `predator`; does not scatter from the player. Map the `crow` slot to a clip. |
| `fish` (`animal_fish_*`) | `medium: water`; schools with `animal:fish`, darts from the player, no eat / drink / sleep rules. Tagged `prey`. |
| `bird` (`*_bird`, `*sparrow*`, `*crow*`, `*robin*`) | `medium: air`; hops on the ground, takes off when the player is near, flocks loosely. Tagged `prey`. |
| `raptor` (`*hawk*`, `*eagle*`, `*owl*`) | a `bird` that is tagged `predator` (chickens flee it) and hunts `prey`. |

Species files using them: `cow`, `pig`, `sheep`, `goat`, `chicken`, `horse`, `cat`, `dog_companion`,
`helper_farmer` (work = `Hoe`), `helper_lumberjack` (work = `Chop`). A new animal is usually just
`{ "id": "...", "extends": ["livestock"], "applies_to": ["..."], "animations": { "eat": "Graze" } }`.

**Predators, prey and guard dogs.** Tags are how animals react to each other. `livestock` is tagged `prey` and
flees anything tagged `predator`; `wolf` (`*wolf*`) is tagged `predator` and hunts `prey`. `guard_dog` (the
labrador extends it) stays with `animal:sheep`, barks at a `predator` within 40 m and chases one within 25 m
while sheep are near. Limits: rules only measure distance from the animal itself (so "a wolf near the *flock*"
is approximated by "a wolf near me while sheep are near me"), and nothing in the game deals damage yet, so
guards drive predators off rather than kill them.

**Helpers / people** use the same system. The player rig's clips are the animation slots (`work` -> `Hoe`,
`Chop`, `Dig`, ...). Give a world object an `AnimalTarget` tag `job`, `table` or `bed`; raise
`AnimalBrain.RaiseEvent("come_here")` to call a helper over.

### Terms (used in `requires` and `score`)

One kind key per term; `weight` only matters in `score`; `not: true` inverts a true/false term.

| Term | Example | Value |
| :--- | :--- | :--- |
| need | `{"need":"hunger","above":0.6}` | true/false with `above` / `below`; otherwise the need value through `curve` (`linear`, `inverse`, `squared`, `sqrt`) |
| time | `{"time":"night"}` | `day`, `night`, `dawn`, `dusk` |
| hours | `{"hours":[20,6]}` | in-game hour range (wraps midnight) |
| weather | `{"weather":["Rain","Snow"]}` | current weather is in the list |
| season | `{"season":"Winter"}` | |
| sense | `{"sense":"player","within":7}` | nearest tagged thing within / beyond a distance; or `{"sense":"player","curve":"closer"}` scores how near it is |
| current | `{"current":"follow_player"}` | true while that behaviour runs (a small bonus makes it sticky) |
| event | `{"event":"called"}` | true while gameplay code has raised that event (`AnimalBrain.RaiseEvent`) |
| random | `{"random":0.2}` | adds `random(0..1) × 0.2` so animals do not act in lockstep |

Sense tags: `player`, `home` (where it spawned), `animal`, `animal:<species>`, and **any tag you put on a
world object** with the `AnimalTarget` component (a water trough tagged `water`, a bowl tagged `food`, a
predator tagged `threat`, a barn tagged `shelter`).

### Actions

| `type` | Does | Useful keys |
| :--- | :--- | :--- |
| `idle` | stand, optionally playing an animation | `anim`, `duration` |
| `wander` | walk to a random point | `radius`, `stay_near` (`home`, `player`, `none`), `speed` |
| `goto` | walk to a target | `target`, `speed`, `arrive_dist` |
| `follow` | keep near a target | `target`, `min_dist`, `max_dist`, `speed`, `until` |
| `flee` | run away from a target | `target`, `min_dist` (safe distance), `speed` |
| `rest` | play a held animation (sit / lay / sleep) | `anim`, `duration` or `until`, `need`, `restore_per_second` |
| `emote` | play an animation once (bark) | `anim`, `duration` |
| `consume` | go to a target, then eat / drink | `target`, `anim`, `need`, `restore_per_second` (negative to reduce hunger), `duration` |
| `sequence` | run steps in order | `steps: [ action, ... ]` |

`speed` is `walk`, `run`, or a number in m/s. `duration` is a number or `[min, max]` seconds.

### A rule

```json
{
  "id": "greet_bark",
  "action":   { "type": "emote", "anim": "bark", "duration": [1.6, 1.6] },
  "requires": [ { "sense": "player", "within": 7 }, { "sense": "player", "beyond": 1.5 } ],
  "score":    [ { "need": "boredom", "weight": 0.7 } ],
  "base": 0.2, "cooldown_s": 60
}
```

## Using it

1. **Author** it on the animal itself: open the animal in the asset kit, and the **Animal AI** card in its popup
   (needs, senses, movement, animation slots, behaviours with action / requires / score rows, plus a JSON tab)
   edits `category_fields.ai` in the animal's manifest. Save with the popup's normal Save. Shared/species-wide
   profiles can still live by hand in `assets/_ai/` (the kit validates on save through
   `POST /api/save-animal-ai`, and `python tools/animal_ai.py` checks every file from the command line).
2. **Assign** it: nothing to do; an animal's own `category_fields.ai` applies to that animal (`applies_to`
   defaults to its item id and wins over a species profile). Use "Copy from shared profile" to start from one.
3. **Ship** it: the packager writes each animal's `category_fields.ai` to `ai/<item_id>.json` and adds an `animal_ai` entry to the mod. Third-party mods add their own `ai/*.json`.
4. **Test in game** (editor): **F5** spawns the dog beside the player, **F6** toggles a debug label over every
   animal showing the running behaviour, its needs and the top three scores.

## What the runtime provides (code)

`Assets/Scripts/Animals/`: `AnimalAIDefinition` (data model + parser), `AnimalAIRegistry` (loaded definitions),
`AnimalBrain` (scoring + needs), `AnimalActions` (the built-in actions), `AnimalMover` (terrain-following
steering, no NavMesh), `AnimalSenses` (`AnimalTarget` tags), `AnimalSpawner` (spawn + dev hotkeys).

Gameplay hooks: `AnimalBrain.RaiseEvent("called")`, `SetNeed` / `AddNeed` (feeding an animal), and
`AnimalTarget` on any object to make it sense-able.

## Limits (v1)

- Movement is kinematic on the terrain; it does not path around large obstacles, only sidesteps small ones.
- Actions are the built-in list; mods cannot add new action *code* (the `script` content type is not
  executable in this build). A mod extends behaviour by composing existing actions, terms and animation slots.
- Herds, predator/prey rules and per-animal personality are not built in yet. `sense: animal:<species>` and
  `threat`-tagged targets are the hooks for them.
