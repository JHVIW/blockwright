# Medieval

**Mood:** sturdy, crowded, weathered, practical, alive.

Medieval building is about weight and use. Stone ground floors carry timber upper storeys that jetty out over narrow
streets; steep roofs shed rain; towers, buttresses and thick walls say "this was built to last a siege and a winter".
Every building has a job you can read from the street: the smithy has its forge open to the lane, the inn hangs its
sign, the merchant's shutters fold down into a counter. Carried at a distance by **steep dark roofs, a stone base and
a crowded, varied roofline**. It is less sweet than cottagecore: fewer flowers, more mud, barrels and smoke.

## Palettes

### Burgher's Row (jettied town house: dark timber, white plaster, dark roof)
| slot | blocks |
|---|---|
| roof field | `dark_oak_stairs`/`dark_oak_slab` (walls ≥ 40% plaster), else `deepslate_tile_stairs` |
| roof trim | `spruce_stairs` barge board + inverted partner; ridge `dark_oak_slab`; `spruce_fence` rafter tails |
| walls | `white_terracotta` 40% · `pale_oak_planks` 35% · `calcite` 25% in the frame panels; `bricks` + `mud_bricks` nogging in a few lower panels |
| frame | `dark_oak_log` posts, `stripped_dark_oak_log` plates and jetty beams, `dark_oak_stairs` braces |
| foundation | `cobblestone` 45% · `stone_bricks` 25% · `andesite` 15% · `mossy_cobblestone` 15% |
| accent | `spruce_door`, `spruce_trapdoor` shutters, one `red_wool` or `blue_wool` awning, hanging signs |
| glass | `glass_pane` in small openings, `oak_trapdoor` grilles (leaded lights) |
| lighting | `lantern` on `iron_chain` or fence brackets |

Value: frame L 48–59 against plaster L 184–224; dark-oak roof L 47 over plaster (ΔL > 130) or slate L 55 over a
timber-heavy front.

### Keep & Curtain Wall (stone fortification)
| slot | blocks |
|---|---|
| roof field | `deepslate_tile_stairs` on towers and halls; conical tower caps at 63° |
| roof trim | `deepslate_brick_stairs` hem; `polished_deepslate_slab` ridge; `lightning_rod` or banner finials |
| walls | `stone_bricks` 50% · `cobblestone` 20% · `andesite` 15% · `cracked_stone_bricks` 10% · `mossy_stone_bricks` 5% (low and at corners, in runs) |
| frame | quoins and lintels `polished_andesite`, `chiseled_stone_bricks` keystones, `stone_brick_stairs` drip hoods |
| foundation | battered base of `cobblestone`, `mossy_cobblestone`, `cobbled_deepslate` |
| accent | `red_banner`/`blue_banner`, `iron_bars` portcullis, `spruce_door` double doors, dark-oak hoardings |
| glass | `iron_bars` in slits, `glass_pane` only in the hall and chapel |
| lighting | `lantern`; `soul_lantern` sparingly in dungeons |

Value: slate L 55 over stone L 118–136. Grey on grey needs the roof clearly darker; never a cobblestone roof on a
stone keep.

### Thatched Hamlet (peasant: mud, wattle and straw)
| slot | blocks |
|---|---|
| roof field | `birch_stairs`/`birch_slab` as straw, with a `hay_block` ridge roll (`axis` along the ridge), convex profile |
| roof trim | `spruce_stairs` eave and verge (a light roof needs a dark edge) |
| walls | `packed_mud` 45% · `mud_bricks` 35% · `stripped_oak_log` (horizontal wattle) 20% |
| frame | `oak_log`, `stripped_oak_log` |
| foundation | `cobblestone` 60% · `mossy_cobblestone` 25% · `gravel`-and-`coarse_dirt` ground band |
| accent | `oak_door`, `oak_trapdoor`, `hay_block`, `composter`, `barrel` |
| glass | none or a few `glass_pane`; shutters closed on most windows |
| lighting | `lantern`, `campfire` in a yard pit |

Value: straw L ≈ 175 over mud L 109–112 (ΔL ≈ 65): a light roof over darker walls, held by a dark spruce edge.

## Signature motifs

- **Jettied upper storeys**: 1 block per floor on the street side, up to twice on inns; corbels at the posts
  (techniques.md §3.2.3).
- **Stone ground floor, timber above**, the band at the floor line, stone 1 thicker than the timber.
- **Steep roofs** (45° to 63°, stair-on-stair), gables to the street, cross gables and hoist dormers with a
  `spruce_fence` arm, `iron_chain` and a hanging `barrel` or `hay_block`.
- **Buttresses** on long stone walls and churches, irregularly spaced, capped with stairs.
- **Arrow slits**: 1 wide, 2–3 tall, with a stair head inside and `iron_bars` or air, in deep walls. Crosslets get a
  1×1 cross-arm on each side.
- **Crenellations**: merlons of full blocks alternating with gaps, capped with a `stone_brick_slab`; machicolations as
  a row of inverted stairs corbelled out under the parapet.
- **Market stalls** (barrel counter, wool-slab canopy on fence posts) and **forges** (open-fronted, `blast_furnace`,
  `anvil`, `grindstone`, `smithing_table`, a `campfire` hearth under a brick hood, a water trough of
  `water_cauldron`).
- **Shop shutters as counters**: a top half of `spruce_trapdoor` open as an awning and a bottom slab counter.
- **Hanging signs** on fence brackets over the lane, a symbol object beside each.

## Roof recipes

- Town houses: 45° body, stair-on-stair 63° top third, deep 1–2 overhang on the street, contrasting barge board.
- Towers: square or octagonal cone at 63° with a 2-course flare; ring metric for round towers.
- Halls: long roof split into sections every 12–15 blocks by a cross gable, a louvre turret or a chimney.
- Gatehouses: a flat lead-grey walkway (`polished_deepslate_slab`) behind crenellations, with a small hip-roofed
  guard room on top.

## Wall recipes

- Timber frame on plaster with brick nogging in a few panels; one K-brace per facade.
- Stone walls with quoins (alternating 1 and 2 long), lintels with drip hoods, round-headed doors.
- Battered (sloped) bases on keeps: the bottom 2 courses step out 1 with stairs on top.

## Interiors

- **Hall house**: a central hearth or wall inglenook, a long trestle table (slabs on fence legs), benches, a dais at
  one end with a high table, banners on the walls.
- **Inn/tavern**: bar counter of barrels with trapdoor fronts, kegs (`barrel[facing=east]` stacks), several small
  tables, a stair up to bedrooms with `straw_bed` or plain beds.
- **Smithy**: forge and anvil by the open front, tool wall of `*_shelf` + `lightning_rod` hooks, coal store of
  barrels.
- **Shop**: a street-facing counter, shelves behind, storage loft reached by a ladder.
- **Keep**: storerooms in the base, a great hall above, spiral stair in a corner turret (techniques.md §4.5).

## Landscaping

- Streets: `cobblestone` and `gravel` cores with `dirt_path` and `coarse_dirt` seams, `mud` in low spots; no
  flower borders on busy lanes, but a few `potted_*` plants, herb boxes and a tree in the square.
- Wells, troughs, hay carts, woodpiles and barrels against walls carry the street edge instead of flowers.
- Outside the walls: wheat fields on `farmland` with water channels, a pigpen of fence and gate, an orchard.

## Anti-patterns

- Castles as cubes with crenellations on every edge and no roofs.
- Uniform grey stone with no gradient, no quoins and no openings deeper than 1.
- Big modern windows; glass in a keep's outer wall.
- Torches everywhere, or a spotless town without mud, smoke or storage.
- Every house the same width, height and gable: vary plot widths (5, 7, 9) and ridge heights along a street.

## Deviations from LESSONS

- **Glazing** (H10): 5–12% in houses, lower in fortifications (slits only).
- **Ground contact** (H14): dense town streets may run paving up to the wall; replace the vegetation share with edge
  clutter (barrels, crates, a bench, a herb box) every 3–4 blocks. Rural and outlying buildings follow H14 as written.
- **Symmetry** (H11): gatehouses and chapels may be symmetric about the entrance axis.
- Everything else, including roof-vs-wall value contrast, applies unchanged.

## Reference builds

None in the repository yet. The cottagecore examples (`examples/builds/b01_cozy_starter_cottage.py`) show the timber
frame, jetty, chimney and roof-edge techniques this style reuses.
