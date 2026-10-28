# Rustic (survival)

**Mood:** honest, warm, hand-made, frugal, early-game.

Rustic is the house you can actually build in your first week of survival: logs from the nearest forest, cobblestone
from the first cave, a furnace's worth of glass. It wins by craft, not by rare blocks: notched log corners, a stone
base that follows the slope, a deep porch, a smoking chimney, a fenced field and a woodpile. Carried at a distance by
**a log body under a clearly different roof** and by the working yard around it. Pair this pack with an allowed-blocks
file (`--palette`) when you want QA to hold you to what your chests contain.

## What is cheap

| tier | blocks |
|---|---|
| day 1 (hand and wood tools) | any `*_log`, `*_planks`, stripped logs, stairs, slabs, fences, doors, trapdoors, `cobblestone` and its stairs/slabs/walls, `dirt`, `coarse_dirt`, `gravel`, `crafting_table`, `chest`, `barrel`, `ladder`, `torch`, `campfire`, `composter` |
| first furnace | `stone`, `smooth_stone`, `stone_bricks` (and stairs/slabs/walls), `glass`, `glass_pane`, `smoker`, `furnace` |
| a few iron | `lantern`, `iron_bars`, `iron_chain`, `iron_trapdoor`, `cauldron`, `water` via bucket |
| a farm | `hay_block`, beds from wool, `white_wool`/carpets, `farmland` crops, `mud` → `packed_mud` → `mud_bricks`, `mossy_cobblestone` (cobble + moss or vine) |
| a clay pit | `bricks`, `terracotta`, `decorated_pot` |

## Palettes

### Spruce Cabin (dark logs, stone roof)
| slot | blocks |
|---|---|
| roof field | `cobblestone_stairs`/`cobblestone_slab`, `mossy_cobblestone_stairs` as the eave hem (runs) |
| roof trim | `spruce_stairs` verge and eave lip, `spruce_slab` ridge |
| walls | `spruce_log` laid horizontally (`axis` along the wall) 70% · `stripped_spruce_log` 30% around openings |
| frame | corner log ends alternating axis (notched corners), `stripped_spruce_log` door and window frames |
| foundation | `cobblestone` 60% · `mossy_cobblestone` 25% · `stone` 15% |
| accent | `oak_door`, `oak_trapdoor` shutters (pale against dark logs) |
| glass | `glass_pane` |
| lighting | `lantern` (or `torch` on fence posts before you have iron) |

Value: cobble roof L 127 over spruce logs L 41 (ΔL 86): light roof over dark walls, held by a dark spruce edge.

### Oak Homestead (oak planks, spruce frame, spruce roof)
| slot | blocks |
|---|---|
| roof field | `spruce_stairs`/`spruce_slab` |
| roof trim | `stripped_spruce_log` barge board + inverted `spruce_stairs`; `spruce_slab` ridge |
| walls | `oak_planks` 60% · `stripped_oak_log` (horizontal boards) 40% |
| frame | `spruce_log` posts and plates |
| foundation | `cobblestone` 50% · `stone_bricks` 30% · `mossy_cobblestone` 20% |
| accent | `spruce_door`, `spruce_trapdoor`, `hay_block` |
| glass | `glass_pane` |
| lighting | `lantern` |

Value: spruce roof L 89 over oak walls L 134–147 (ΔL ≈ 45–58); frame L 41 against oak (ΔL > 90). The margin is
modest, so keep the oak walls showing on every elevation.

### Birch & Stone (light timber, grey roof)
| slot | blocks |
|---|---|
| roof field | `stone_brick_stairs`/`stone_brick_slab`, or `spruce_stairs` |
| roof trim | `spruce_stairs` eave and verge |
| walls | `birch_planks` 60% · `stripped_birch_log` 40%; ground storey `cobblestone` |
| frame | `spruce_log` |
| foundation | `cobblestone`, `andesite`, `mossy_cobblestone` |
| accent | `spruce_door`, `spruce_trapdoor` |
| glass | `glass_pane` |
| lighting | `lantern` |

Value: birch L 175 with stone-brick roof L 122 (ΔL ≈ 53) or spruce roof L 89 (ΔL ≈ 86).

### Mud & Straw (plains and savanna)
| slot | blocks |
|---|---|
| roof field | `birch_stairs`/`birch_slab` as straw, `hay_block` ridge roll |
| roof trim | `spruce_stairs` eave and verge |
| walls | `packed_mud` 50% · `mud_bricks` 35% · `stripped_oak_log` 15% |
| frame | `oak_log` or `acacia_log` |
| foundation | `cobblestone`, `coarse_dirt` band |
| accent | `oak_door`, `acacia_trapdoor` |
| glass | few `glass_pane` |
| lighting | `lantern`, `campfire` |

Value: straw L ≈ 175 over mud L 109–112 (ΔL ≈ 65).

## Signature motifs

- **Log cabins with notched corners**: at each corner, alternate the log axis per course so the ends cross and stick
  out 1 (a crossed-log corner). Chink lines of `stripped_*_log` under the window sills.
- **Stone foundations that follow the terrain**: taller on the downhill side, stepped, mossy at the bottom.
- **Deep porch** with log posts on stone piers, a bench, a barrel and a lantern.
- **Exterior stone chimney** on the gable end, cobble at the bottom, stone bricks higher, campfire 1–2 below the rim.
- **The working yard**: woodpile under a lean-to, chopping block, fenced field (`farmland` + crops + water channel),
  animal pen (`oak_fence` + gate, `hay_block`, `water_cauldron` trough, `composter`), a well, a cart.
- **Storage that shows**: barrels and chests on the porch, a hay loft door with a hoist, a root cellar door.
- **Shutters, not glass**, on outbuildings; trapdoor shutters on the house.

## Roof recipes

- 45° gable, overhang 1–2, a 2-thick edge (stair + inverted stair or a log), slab ridge.
- Lean-tos and porches at 26.5° (slab steps) tucked under the main eave.
- A gambrel barn roof for the barn (techniques.md §3.1.8).

## Wall recipes

- Horizontal logs with stripped-log frames around openings; or planks in a log frame (posts every 4, varied 3–5).
- Ground storey in cobble on hillside builds, timber above.

## Interiors

- One-room cabin: a hearth (cobble inglenook with a lit `campfire`), a bed in a corner nook, a table of slabs on
  fences, stair chairs, a chest wall, a crafting corner (`crafting_table`, `furnace`, `smoker`), a ladder to a loft.
- Barn: hay storage, stalls of fences, a workbench.
- Light: lanterns where iron allows; early builds may use torches, but on posts or beside doors, never sprayed on
  walls. Every floor cell still needs block light ≥ 1.

## Landscaping

- Natural ground: `dirt_path` worn routes with `coarse_dirt` and `gravel` edges, tall grass, ferns, a few wild
  flowers (`dandelion`, `poppy`, `oxeye_daisy`, `cornflower`), `sweet_berry_bush`.
- Stumps and logs on the ground, a fallen log with `moss_carpet`, a natural-looking oak or spruce (techniques.md
  §5.4), a pond for water.

## Anti-patterns

- A wood roof over wood walls of the same value (an oak-on-oak cabin is one brown blob): put stone on the roof or
  change the wood.
- Plank boxes with no logs, no foundation and no porch.
- Torches on every wall.
- A perfect lawn: rustic ground is worn and varied.
- Rare blocks used to "improve" a survival build; if it is not cheap, it is not rustic.

## Deviations from LESSONS

- **Material discipline** (H09): with a tight palette, gradients come from block *shape* and orientation (log axis,
  stripped vs bark, stairs, slabs, walls) and from mossy variants, not from many block types. No per-block speckle
  still applies.
- **Allowed blocks**: when `--palette` is set, it overrides every block named here; substitute the closest allowed
  block of similar value and shape and note it in the log.
- Everything else, including the roof-vs-wall contrast rule, applies.

## Reference builds

None in the repository yet. `examples/builds/b01_cozy_starter_cottage.py` shows the woodpile shed, handcart, pond and
garden props this style relies on.
