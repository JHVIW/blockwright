# Cottagecore

**Mood:** warm, cosy, whimsical, lived-in, a little overgrown.

Cottagecore is the storybook country cottage: big roofs pulled low over small walls, timber frames over mossy stone
plinths, smoke curling from a slim chimney, shutters and flower boxes, and a garden that spills right up to the door.
Nothing is new and nothing is perfect, but everything is cared for. At a distance it is carried by **a dominant,
dark (or clearly contrasting) roof over light plaster and dark timber**, and by the soft green edge where the
building meets its garden. Even serious buildings (a town hall, a smithy) stay inviting.

This is the most battle-tested pack: its palettes, roof recipes and lessons come from a 20-building example set
whose first six buildings went through builder → critic rounds. Read [`../design/LESSONS.md`](../design/LESSONS.md)
first; the "as built" notes below show how the original palettes were corrected by those lessons.

## Set-wide cohesion (for a village or hamlet)

* **Foundation family:** every plinth draws from `cobblestone`, `mossy_cobblestone`, `stone_bricks`,
  `mossy_stone_bricks`, `cracked_stone_bricks`, `andesite`, `tuff`. Each palette sets the proportions.
* **Shared hardware:** `lantern` (iron, warm flame) for all street and door lights. Copper lanterns (green flame)
  are reserved for magical buildings (wizard, herbalist, fairy). `spruce_fence`/`spruce_fence_gate` for all garden
  fences, `cobblestone_wall`/`mossy_cobblestone_wall` for low garden walls.
* **Roof families:** about 75% of buildings use one of the "set roofs". Special buildings get special roofs: living
  moss, bamboo thatch, mushroom cap, cherry, patina copper.
* **Neighbour rule:** two buildings within 24 blocks never share both palette *and* roof family.

### Roof materials that worked

| roof field | use over | notes |
|---|---|---|
| `tuff_bricks` / `tuff_brick_stairs` (slate-like) | timber and plaster | `polished_tuff` runs as sun-bleached weathering; dark-oak trims |
| `deepslate_tiles` / `deepslate_tile_stairs` | brick, timber, mixed | `deepslate_brick_stairs` hem, `polished_deepslate_slab` ridge |
| `cinnabar_bricks` / `cinnabar_brick_stairs` (red clay tile) | cream plaster, stone | `polished_cinnabar_stairs` hem, `cinnabar_brick_wall` or slab ridge |
| `waxed_weathered_cut_copper_stairs` (patina) | spires, towers, pavilions | green against grey slate pops; dark-oak hips |
| `cherry_stairs` / `cherry_planks` | pale plaster + dark timber | needs a dark eave lip to hold the edge |
| `dark_oak_stairs`, `spruce_stairs` | **only** walls that are ≥ 40% light plaster | never over mostly-wood walls (one brown mass) |
| living moss, bamboo thatch, mushroom cap | special buildings | see techniques.md §3.1.12–3.1.13 and `b04_mushroom_cottage.py` |

## Palettes

Each palette lists the frame, infill, stone, roof and accent families with gradient members, in order of share.
Remember LESSONS.md §1: check the roof field against the walls you will actually *see*, and swap the roof for slate,
tuff or clay tile when the visible walls are mostly wood or brick.

### P1 · "Thistledown" (Tudor cottage: dark timber, cream plaster)
| slot | blocks |
|---|---|
| roof field | `dark_oak_stairs`/`dark_oak_slab` (only with ≥ 40% plaster showing), else `tuff_brick_stairs` |
| roof trim | verge/eave `spruce_stairs` or `stripped_spruce_log`; ridge `dark_oak_slab` or `tuff_brick_slab` |
| walls (infill) | `pale_oak_planks` 50% · `calcite` 25% · `mushroom_stem` 15% · `white_terracotta` 10% (darker ones low) |
| frame | `dark_oak_log` posts, `stripped_dark_oak_log` beams and sills, `dark_oak_*` stairs/slabs |
| foundation | `cobblestone` 45% · `stone_bricks` 25% · `mossy_cobblestone` 20% · `andesite` 10% |
| accent | `bricks`/`brick_stairs` chimney, `spruce_trapdoor` shutters, `spruce_door` |
| glass | `glass_pane` |
| lighting | `lantern` |

Value: frame L 48–59 against plaster L 184–224 (ΔL > 120: strong frame/fill). As built (01 cozy starter cottage),
the roof became a tuff-brick field with dark-oak trims because timber dominated the visible walls.

### P2 · "Spruce & Slate" (working waterfront)
| slot | blocks |
|---|---|
| roof field | `deepslate_tile_stairs`/`deepslate_tile_slab`, `cobbled_deepslate_stairs` only as an eave hem |
| roof trim | `dark_oak_stairs`; ridge `polished_deepslate_slab` |
| walls | `spruce_planks` 50% · `stripped_spruce_log` (axis horizontal, as boards) 30% · `oak_planks` 20%; stone ground floors |
| frame | `spruce_log`, `stripped_spruce_log`, `spruce_*` stairs/slabs/fence |
| foundation | `stone_bricks` 35% · `cobblestone` 25% · `andesite` 15% · `tuff` 15% · `mossy_stone_bricks` 10% |
| accent | `iron_chain`, `barrel`, `waxed_exposed_copper` hardware, `iron_bars`, `dark_oak_trapdoor` shutters |
| glass | `glass_pane` |
| lighting | `lantern` |

Value: slate L 55 over spruce L 89–93 and stone L 108–136. The spruce walls are mid-dark, so give them at least one
light gable or stone storey where the eye looks.

### P3 · "Brick & Bramble" (brick ground floor, timber upper)
| slot | blocks |
|---|---|
| roof field | `deepslate_tile_stairs` (as built for 02; a spruce field reads "mostly brown" here) |
| roof trim | `dark_oak_stairs` eave coves; solid 2-thick slate verge; `polished_deepslate_slab` ridge |
| walls (stone storey) | `bricks` 55% · `mud_bricks` 20% · `polished_granite` 10% · `packed_mud` 10% · `cracked_stone_bricks` 5% near the plinth |
| walls (timber storey) | `pale_oak_planks`/`white_terracotta`/`calcite` plaster gradient (birch reads tan, avoid it as plaster) |
| frame | `oak_log`/`stripped_oak_log` |
| foundation | `stone_bricks` 50% · `mossy_stone_bricks` 25% · `cobblestone` 25% |
| accent | white window frames (`pale_oak_trapdoor`, `white_concrete_stairs` lintels), `crimson_trapdoor` (plum) shutters, `dark_oak_door` or a crimson door |
| glass | `glass_pane` |
| lighting | `lantern` |

As built (02 large player house): slate field, a copper broach spire with dark-oak hips, plaster where the eye looks.
See `docs/examples/critiques/02_round2.md`.

### P4 · "Honey & Clay" (sunny: oak timber, cream walls, red clay tile)
| slot | blocks |
|---|---|
| roof field | `cinnabar_brick_stairs`/`cinnabar_brick_slab`; `polished_cinnabar_stairs` only as the eave hem |
| roof trim | `stripped_oak_log`/`spruce_stairs`; ridge `cinnabar_brick_wall` or `brick_slab` |
| walls | `smooth_sandstone` 40% · `white_terracotta` 30% · `calcite` 20% · `pale_oak_planks` 10% |
| frame | `oak_log`, `stripped_oak_log`, `oak_*` |
| foundation | `cobblestone` 40% · `mud_bricks` 25% · `packed_mud` 15% · `mossy_cobblestone` 20% |
| accent | `resin_bricks` (oven, chimney pots), wool-stair awnings (`white_wool_stairs` + `red_wool_stairs` or `yellow_wool_stairs`), `acacia_trapdoor` or `birch_trapdoor` shutters, `decorated_pot` |
| glass | `glass_pane` |
| lighting | `lantern` |

Value: red tile L 75 against stone L ≈ 120 and plaster L 184–224: a hue *and* value break.

### P5 · "Mossgrove" (fairy/witchy: dark gnarled wood, tuff, living roofs)
| slot | blocks |
|---|---|
| roof field | living roof on a `dark_oak_stairs` skeleton (`moss_carpet`, `azalea_leaves`, `flowering_azalea_leaves` patches), or `cherry_stairs` (fairy), `bamboo_mosaic_stairs` thatch (herbalist), mushroom cap, `deepslate_tile_stairs` + `polished_blackstone_brick_stairs` witch hat (wizard) |
| roof trim | `dark_oak_stairs`/`dark_oak_slab`, continuous and wooden even on green roofs |
| walls | `mushroom_stem` 40% · `pale_oak_planks` 40% · `calcite` 20%; the wizard uses `tuff_bricks` + `polished_tuff` |
| frame | `dark_oak_log`/`mangrove_log` (twisted feel), `stripped_mangrove_log` accents, `pale_oak_log` for the wizard |
| foundation | `tuff` 30% · `mossy_cobblestone` 30% · `cobbled_deepslate` 20% · `mossy_stone_bricks` 20% |
| accent | `warped_trapdoor` (teal) or `cherry_trapdoor` shutters, `cave_vines` with berries, `spore_blossom`, `shelf_mushroom`, `glow_lichen` (sparingly) |
| glass | `glass_pane` |
| lighting | `waxed_copper_lantern`, `copper_torch` (green flame) |

As built: 03 fairy flower cottage (cherry bell roof, stair-on-stair steep courses, octagonal ring metric, weeping
cherry T9) and 04 mushroom cottage (red mushroom cap on a height field).

### P6 · "Golden Poplar" (civic and genteel: greige poplar, pale stone, slate, autumn trees)
| slot | blocks |
|---|---|
| roof field | `deepslate_tile_stairs` (main); `waxed_weathered_cut_copper_stairs` for towers, spires and pavilions |
| roof trim | `dark_oak_*`; finials `lightning_rod`/`end_rod` |
| walls | `pale_oak_planks` 40% · `poplar_planks` 30% · `calcite` 20% · `stripped_poplar_log` 10% |
| frame | `poplar_log` (dark bark posts), `stripped_poplar_log` (beams), `poplar_*` stairs/slabs/fences/doors |
| foundation | `stone_bricks` 40% · `polished_andesite` 20% · `tuff_bricks` 20% · `mossy_stone_bricks` 20% |
| accent | `yellow_poplar_leaves`/`orange_poplar_leaves` trees, `golden_dandelion`, `poplar_shelf`, `chiseled_bookshelf` |
| glass | `glass_pane` |
| lighting | `lantern` |

As built (06 library): a steep 63° stair-on-stair slate nave over a heavy stone ground storey, deepslate-brick hem,
copper turret cone.

## Worked assignment: a 20-building set

Flower themes: **2 lead species + 1 filler** per building, repeated in planters, beds and pots. The filler is usually
`short_grass`, `bush`, `fern` or `wildflowers`.

| # | building | palette | roof family | lead flowers + filler |
|---|---|---|---|---|
| 01 | cozy starter cottage | P1 | tuff slate (as built) | `oxeye_daisy`, `dandelion` + `wildflowers` |
| 02 | large player house | P3 | deepslate tile + copper spire (as built) | `peony`, `pink_tulip`, `white_tulip` + `bush` |
| 03 | fairy flower cottage | P5 | cherry + living | `pink_petals`, `allium`, `lilac` + `flowering_azalea` |
| 04 | mushroom cottage | P5 | red mushroom cap | `lily_of_the_valley`, `blue_orchid` + `red_mushroom`/`brown_mushroom` (on podzol) |
| 05 | bakery | P4 | cinnabar tile | `sunflower`, `orange_tulip` + `wildflowers` |
| 06 | library | P6 | deepslate tile | `cornflower`, `azure_bluet` + `fern` |
| 07 | tavern + inn | P1 | dark oak over plaster | `poppy`, `rose_bush` + `short_grass` |
| 08 | florist + greenhouse | P4 | cinnabar tile + glass | all colours, *sorted in bands* (the exception) |
| 09 | herbalist | P5 | bamboo thatch | `allium`, `azure_bluet`, `sweet_berry_bush` + `fern` |
| 10 | fisherman + dock | P2 | deepslate tile | `blue_orchid`, `cornflower` + `sugar_cane`, `tall_grass` |
| 11 | blacksmith | P2 | deepslate tile | `torchflower`, `orange_tulip` + `tall_dry_grass` |
| 12 | farmer + garden | P3 | dark oak (barn, red `mangrove_planks` walls) | `sunflower`, `dandelion` + crops |
| 13 | watermill | P2 | deepslate tile | `blue_orchid`, `lily_of_the_valley` + `large_fern` |
| 14 | windmill | P1 | dark oak cap (white tower) | `poppy`, `cornflower` meadow + `short_grass` |
| 15 | town hall | P6 | deepslate + copper | `red_tulip`, `white_tulip` formal beds + `bush` |
| 16 | wizard cottage | P5 | witch-hat slate | `allium`, `open_eyeblossom`/`closed_eyeblossom` + `pale_moss_carpet` |
| 17 | hillside cottage | P3 | turf (moss) | `azure_bluet`, `oxeye_daisy` + `short_grass` |
| 18 | merchant shop | P3 | spruce over plaster, or slate | potted plants only (street), `pink_tulip` |
| 19 | tea house + terrace | P6 | patina copper | `pink_tulip`, `lilac`, `peony` + `flowering_azalea` |
| 20 | fantasy manor | P6 + P1 | deepslate + copper spires | `rose_bush`, `peony`, `white_tulip` + `bush` hedges |

Autumn accent trees (poplar leaves, gold birch) go near the bakery, library, farm, town hall and manor. Cherry trees
go near the fairy cottage and tea house. Azalea goes near the herbalist and hillside cottage.

## Signature motifs

- **Big roof, low walls.** Roof height 0.9–2× the wall height on one-storey cottages; catslides down to `g+3`.
- **Flared, bell-cast eaves** and, on two or three special buildings only, "horned" verge tips kicked up at the ridge
  ends (fairy, wizard, manor).
- **Timber frame over a mossy stone plinth**, with one braced panel per facade, a jetty or pent skirt between floors.
- **Slim chimney with real smoke**: exterior gable-end stacks are the most cottagey.
- **Shutters varied 2/1/0**, one flower box per main facade, window grilles on 1–2 feature windows.
- **Porch with its own small roof**, a step up, a lantern beside the transom, an accent-coloured door.
- **Dormers and eyebrow windows** in the big roof.
- **Gardens to the door**: flower drifts, a worn path, a woodpile, a well, beehives, a laundry line, a cart.
- **Small magic** for fairy and wizard builds: glow-berry strands, spore blossoms, shelf mushrooms, copper lanterns.

## Roof and wall recipes

- Default: 45° gable, ≥ 1 overhang, 2-thick edges, slab ridge, flared lowest course. Steep parts stair-on-stair.
- Hip roofs on civic wings, pavilions and the manor; gambrel on barns, shops and the windmill cap; catslide on small
  cottages and hillside houses; conical/witch-hat on towers (bent tip for a wizard).
- Walls: proud timber frame on the main facade, flush frame elsewhere; plaster gradient `white_terracotta` (low) →
  `pale_oak_planks` → `calcite` (high, gables), value noise at scale 3–4 plus a height bias.
- Stone ground storey + timber upper storey is the strongest two-material story (P3, P6).
- See `techniques.md` §3 for every diagram; `docs/examples/critiques/02_round2.md` for the reusable slate roof recipe.

## Interiors

- Enter into the living room or kitchen with a hearth (inglenook with a lit campfire, chain + lantern, mantel).
- Low beamed ceilings, plank floors with a darker border, rugs covering 15–40% of the floor.
- Bed nooks under the roof slope, wool-stair armchairs, `*_shelf` rows above counters, a pantry of barrels, hay and
  decorated pots, potted plants in every room.
- Shops get a counter and a symbol object visible from the street (a cake, an anvil, a lectern).

## Landscaping

- Cottage gardens: kidney-shaped beds of the building's 2 lead flowers + filler, tall at the back, low at the front.
- A worn `dirt_path` core with coarse dirt and podzol speckle on the edges, `leaf_litter` on grass beside it.
- Spruce picket fences with gaps, mossy cobblestone walls ending in a broken step-down.
- A bean-shaped pond with lily pads, sugar cane and dripleaf; a well; beehives in a meadow.
- Custom trees (oak dome, weeping cherry, autumn poplar) framing a roof corner, odd-numbered groups.

## Anti-patterns (on top of techniques.md §6)

- A wood roof over mostly-wood walls (the original "big brown field" failure of buildings 01–03).
- Birch planks as "plaster": they read tan, i.e. as more wood.
- Moss blocks on every roof; vines over whole walls. Overgrowth is a seasoning.
- Saturated colour on structure (bright wool walls, concrete). Colour lives in shutters, awnings, doors and flowers.
- Rainbow beds outside the florist; nine species in one bed.
- Fat 3×3 chimney crowns; log ridges; flat-lidded dormers.

## Deviations from LESSONS

None. Cottagecore is the style the lessons were learned on.

## Reference builds

- `examples/builds/b01_cozy_starter_cottage.py`: P1 with the tuff roof correction, catslide lean-to, oak dome tree,
  `shares()` light-share counter.
- `examples/builds/b03_fairy_flower_cottage.py`: P5 fairy, octagonal bell roofs (ring metric, helper stairs,
  stair-on-stair), weeping cherry T9, fairy ring, pond.
- `examples/builds/b04_mushroom_cottage.py`: P5 mushroom cap on a height field, round plan.
- Renders of the example builds: `docs/showcase/`.
- Critiques: `docs/examples/critiques/01_round2.md` (tuff roof), `02_round2.md` (slate roof recipe, plaster where
  the eye looks), `03_round2.md` (bell roof profile, T9 tree). Builder logs: `docs/examples/logs/`.
