# QA checks (`blockwright/qa.py`)

Automated quality checks for a finished structure (Minecraft Java **26.3**). Self-contained: stdlib + numpy, reads
`blockwright/data/blocks_26.3.json` and the vanilla block tags resolved from the 26.3 jar
(`blockwright/data/tags_26.3.json`; regenerate both with `python -m blockwright dump-registry`). A rule asking for a tag that does not exist raises `KeyError` instead of silently matching
nothing.

```python
from blockwright.qa import run_qa, write_report
report = run_qa(blocks, size, meta)            # registry=None (a blockwright.registry.Registry exposing .dump/.data/.raw is reused)
write_report(report, "out/reports/01_x_qa.md", "out/reports/01_x_qa.json")
```
CLI: `python -m blockwright qa out/schematics/01_x.litematic [out_dir] [--meta meta.json] [--ground Y]` (uses
`blockwright.litematic.read_litematic`; meta defaults to the sidecar `01_x.meta.json` next to the schematic, then the
litematic metadata; prints the markdown, writes `<slug>_qa.md/.json` to out_dir (default `out/reports`); exit code
0 = no errors).

`meta`: `ground` (y of the terrain surface layer), `rooms` `{name: (x,y,z)}` (feet position inside the room),
`entrances` `[(x,y,z)]` (feet position outside the main door), `slug`, `title`. A missing or `None` `ground`
(e.g. a .litematic without the "ground layer" description line) gives a warning and ground 0.

## World model (used by every check)

* The box is `size = (sx, sy, sz)`, blocks at `0 <= x < sx` etc. Blocks outside the box are reported (validity).
* Unset cells at `y <= ground` are **natural terrain**: `grass_block[snowy=false]` at `y == ground`, `dirt` below,
  inside the box **and outside it** (the world continues as flat terrain). Unset cells above ground are air.
  Explicit `minecraft:air`/`cave_air`/`void_air` entries are treated **exactly like unset cells**: a .litematic
  stores air as palette entry 0 (`blockwright.litematic` omits it) and Litematica's paste (replace behaviour None /
  With non-air) leaves the world block there, so air can never carve terrain. Explicit air at/below ground is a
  **warn** ("cannot carve terrain"); above ground an info. A cellar below `ground` therefore cannot be expressed.
* Internally the box is padded by one cell on every side (`World`, grid index = coordinate + 1). Floods that
  "reach the outside" mean reaching that padding ring.

## Ground truth and how it was verified

Everything below is ported from the decompiled 26.3 sources (`net/minecraft/...`, Mojang names). The per-state
facts qa derives (CENTER/RIGID support masks, legacy `isSolid`, heightmap motion blocking tag, `isValidSpawn` for a
zombie, `isSignalSource`, fluid state, `EntityType#isBlockDangerous`, light opacity, `useShapeForLightOcclusion` and
the 6 face occlusion shapes) were compared **for all 35,723 block states** with the values the running game reports
(a Java dump harness, tags bound from the jar): 100 % match. The `canSurvive` ports were compared with the
game's own `BlockState#canSurvive` (run through a proxy `LevelReader`) on ~4,600
randomly generated placements across ~85 block classes plus hand-made cases: 0 mismatches. Scripts:
compare and fuzz scripts (not shipped).

Review pass: 1,179 hand-made placements (14 plants x 15 soils, 40 supports x 25 dependent
blocks: lanterns, torches, candles, carpets, plates, signs, banners, doors, snow, leaf litter, wall torches, ladders,
buttons, hanging signs, spore blossom, hanging moss, glow lichen, bells, moss carpet, cave vines, vines) compared with
the game's `canSurvive` (`survive_cases.py`): 0 mismatches after fixing the vine up-face rule. The light dampening
rule used for sky light matches the game's `getLightDampening` for all 35,723 states, and the falling-block
"free" set is the game's `FallingBlock.isFree` for every state (`java/RvDump.java`).

Support shape = collision shape (`BlockBehaviour#getBlockSupportShape` default in 26.3) except: leaves (empty), mud /
soul sand / closed shulker box (full), snow layer (`SHAPES[layers]`), fence gate (closed: `column(16,4,5,24)` rotated,
open: empty), chorus flower, ceiling and wall hanging signs (outline shape). Face tests use the exact slice rule of
`VoxelShape#getFaceShape` (boxes crossing the plane 1e-7 inside the face) on a 32x32 raster:
FULL = whole face, CENTER = projection of `column(2,0,10)` (the 2x2 px centre on top/bottom faces),
RIGID = face minus `column(12,0,16)` (a 2 px rim on top/bottom; whole face on the sides).

## Severity

`error` = will visibly break / is wrong in game (block pops off, room leaks, unreachable room, mobs spawn inside);
`warn` = suspicious but legal, or a slow change (non-canonical state string, vine face that will be trimmed, chimney
flue, explicit air below ground, flowing fluid states, dry bare farmland, saplings that will grow);
`info` = facts for critics (metrics, dark landscaping spots, unported rules). `summary.passed` = no errors.

## 1. Validity
* State string parses as `ns:name[k=v,...]`; block exists in the dump; every property exists and its value is
  legal -> otherwise **error** (one issue per distinct bad state, with count and first position).
* Missing properties / missing namespace -> **warn** (defaults assumed; canonical form requires all properties).
* Block positions outside `size` -> **error**.

## 2. Floating blocks
6-connected components of non-air cells (fluids included; implied terrain included). Components that do not touch
implied terrain are **errors** (bbox, size, the 5 most common blocks). Leaves connected through logs, lanterns on
chains etc. are fine because they are connected. At most 50 components are listed individually.

## 3. Support rules (`survives()`), plus double-block pairs
Each authored block with a `canSurvive` override is checked against its neighbours (implied terrain counts).
`canSupportCenter(pos, DOWN)` is false for `#unstable_bottom_center` (fence gates).

| Block (26.3 class) | Rule |
|---|---|
| lanterns (`LanternBlock`, copper variants) | hanging: block above `canSupportCenter(DOWN)`; standing: block below `canSupportCenter(UP)` |
| torches (`BaseTorchBlock`: torch, soul, copper, redstone) | block below `canSupportCenter(UP)` |
| wall torches (`WallTorchBlock`, `RedstoneWallTorchBlock`) | block at `pos - facing` has a FULL-sturdy `facing` face |
| candles (`CandleBlock`) | block below `canSupportCenter(UP)` |
| cake, candle cake, standing banner, standing sign | block below `isSolid()` (legacy solid flag) |
| wall sign, wall banner | block behind (`pos - facing`) `isSolid()` |
| ceiling hanging sign | block above CENTER-sturdy on DOWN (no unstable check) |
| wall hanging sign | always survives (no override); info if it could not be placed by hand (`canPlace`) |
| carpets incl. moss carpet (`CarpetBlock`) | block below is not air |
| pale moss carpet (`MossyCarpetBlock`) | base: below not air; side part: base carpet below |
| doors | lower: FULL-sturdy UP below; upper: same door block below |
| vegetation (`VegetationBlock#mayPlaceOn`) | flowers, grass, ferns, saplings, bushes, firefly bush, sweet berry bush, pink petals, wildflowers, eyeblossom, tall plants (lower half): `#supports_vegetation` (= `#substrate_overworld` dirt/mud/moss/grass + farmland); crops / pitcher: `#supports_crops` (farmland); stems: `#supports_pumpkin_stem`/`#supports_melon_stem`; dry grass: `#supports_dry_vegetation`; azalea: `#supports_azalea`; nether plants and wither rose: their tags; mangrove propagule: `#supports_mangrove_propagule` (hanging: `#supports_hanging_mangrove_propagule` above); lily pad: water fluid (or `#supports_lily_pad` ice) below and no fluid in its cell; seagrass: sturdy UP and not `#cannot_support_seagrass`; sea pickle: any collision top face below; cactus flower: `#support_override_cactus_flower` or CENTER UP; small dripleaf: `#supports_small_dripleaf` or vegetation soil under water; mushrooms: `#overrides_mushroom_light_requirement` (mycelium, podzol, nylium), or a solid-render block **and** raw light < 13; crops / pitcher crop (lower half): raw light >= 8. Raw light = `getRawBrightness(pos, 0)` = max(sky light, block light), time of day ignored: a mushroom under open sky (15) or right inside a window or door (13-14) pops off |
| upper halves of double plants | same block, `half=lower` below |
| leaf litter (`LeafLitterBlock`) | FULL-sturdy UP below |
| sugar cane | sugar cane below, or `#supports_sugar_cane` below with water (fluid) / frosted ice horizontally next to that block |
| vines (`VineBlock`) | at least one face survives. Up face: the block above must have a full **UP** face (vanilla quirk: `isAcceptableNeighbour(level, above, Direction.DOWN)` tests the side opposite to DOWN), so a vine hangs under a full block or a top slab but **not under a bottom slab / bottom stair**. Side faces: a full (support or collision) face on that side, or the same face on a vine directly above (vines hang from vines). Faces that would be trimmed -> warn |
| glow lichen, sculk vein, resin clump (`MultifaceBlock`) | every face set needs a full face (support or collision shape) on that neighbour, and >= 1 face |
| cave vines, weeping/twisting vines, kelp (`GrowingPlantBlock`) | same plant or FULL-sturdy face in growth direction at the attachment side |
| spore blossom | CENTER support above and no water |
| hanging roots | FULL-sturdy DOWN face above |
| pale hanging moss | full face above (multiface rule) or hanging moss above |
| shelf mushroom (`ShelfMushroomBlock`) | block at `pos - facing` FULL-sturdy on `facing` |
| buttons, levers (`FaceAttachedHorizontalDirectionalBlock`) | the attached neighbour is FULL-sturdy on the touching face; grindstone always survives |
| pressure plates | block below RIGID or CENTER on UP |
| bell | floor: sturdy UP below; ceiling: `canSupportCenter` above; wall: sturdy face beside |
| ladder | block at `pos - facing` FULL-sturdy on `facing` |
| rails / repeaters & comparators / redstone wire | RIGID UP below / RIGID UP below / sturdy UP or hopper below |
| tripwire hook, amethyst buds, wall corals | FULL-sturdy face behind; corals: sturdy UP below |
| cocoa | jungle log (`#supports_cocoa`) at `pos + facing` |
| scaffolding | `getDistance < 7` from the neighbours' `distance` values |
| snow layer | below not `#cannot_support_snow_layer`; `#support_override_snow_layer` ok; else full collision top face or 8 layers |
| farmland, dirt path | the block above is not `isSolid()` (path: fence gates allowed; farmland: `#maintains_farmland` allowed) |
| cactus, bamboo, big dripleaf (+stem) | as in their classes |
| chains, flower pots, beds, trapdoors, fences, etc. | no survival rule in 26.3 (fine anywhere) |

Not ported (reported as info "unchecked"): fire, soul fire, chorus plant/flower, frogspawn, bubble column, pointed
dripstone / sulfur spike.

Other things that change right after pasting (all reported by the `support` check):
* **Falling blocks** (`FallingBlock` / `BrushableBlock#tick`, scheduled by `onPlace`, which Litematica's paste
  triggers): sand, red sand, gravel, concrete powder, anvils, dragon egg, suspicious sand/gravel over a block for which
  `FallingBlock.isFree` is true (air, fire, water, lava and the `replaceable` blocks: short/tall grass, ferns, bush,
  dead bush, dry grass, vines, glow lichen, resin clump, hanging roots, leaf litter, snow layers, seagrass, roots,
  sprouts) -> **error**. Sand on a flower, carpet or slab holds.
* **Fluids** (`FlowingFluid#spread`): every water/lava cell (sources, flowing states and waterlogged blocks) that can
  flow down or sideways into a fluid-free neighbour that `canHoldAnyFluid` (`#washed_away_by_fluids`: air, plants,
  torches, carpets, ...; waterloggable blocks never take flowing water) through a face that is not closed
  (`canPassThroughWall`: neither collision shape is a full cube and the two face slices do not cover the face) ->
  **error** (grouped per fluid). Flowing (level != 0) fluid cells -> **warn** (recomputed on the first tick).
* **Random ticks**: non-persistent leaves with `distance=7` stored, or with no log/wood (`#prevents_nearby_leaf_decay`)
  within 6 leaves -> **error** (decay); snow layers with block light > 11 and ice with block light > 11 - dampening ->
  **error** (melt); farmland with no `#maintains_farmland` block on top and no water within x/z +-4, y +0..1 ->
  **warn** (turns to dirt); saplings / mangrove propagules with raw light >= 9 above them -> **warn** (grow into trees).

Double blocks (`#updateShape` turns orphans into air on the next update) -> **error**: door/double-plant half without
the matching other half (doors must also agree on facing/hinge/open), bed part without its matching part at
`pos ± facing`.

## 4. Enclosure (leaks) and rain
The flood runs on a **face graph**, not on whole cells, so half blocks are handled exactly. Each state gets a kind
from the six face slices of its collision shape (same slice rule as above):
* **solid**: all six faces full (full cubes), or no face full but the "chunky" heuristic says it blocks: closed fence
  gates, fences, panes, bars and walls (always), and blocks whose collision top is > 3/16 with horizontal bounds
  >= 0.5 block (chests, anvils, cauldrons, hoppers, ...);
* **partial**: some but not all faces full - slabs, stairs, doors, trapdoors, carpets, beds, snow layers, lecterns,
  composters, campfires, ladders, ... Their free space is assumed to be one connected region;
* **open**: no full face and not chunky - air, plants, lanterns, pots, candles, chains, open gates, ...

Two neighbouring cells are connected unless one is solid or their two face slices on the shared face cover it
together (like `Shapes.faceShapeOccludes`). So a stair or bottom slab used as a wall block, a closed trapdoor lying in
a window hole, a wall course of bottom slabs under the roof, roof stairs facing the wrong way, or two stairs whose open
quarters meet diagonally all **leak**, while an open trapdoor or a door panel that covers the hole seals it. A closed
door's cell belongs to the side its panel does not cover (a door niche is part of the room when the panel is on the
outer side).

For each room marker (if the marker cell is solid the cell above is used; else error) flood across open faces. If the
room flood reaches the padding ring -> **leak error**, located like this: shortest path marker -> padding ring; the
*breach* is the path cell that a 3x3x3 morphological closing of the walls (solid cells and partial cells taller than
3/16) fills, that is not solid, and that has the most walls around it across the direction of travel (ties: nearest
the outside); without such a cell, the path cell most hemmed in by walls. `kind` = roof/ceiling (path goes straight up
there), floor, or wall. The 3x3x3 around the breach is then plugged and the search repeats (max 8 holes, so one long
gap can produce several issues). An escape that rises straight up from a campfire/fire (chimney flue) is a **warn**
instead. For a leaking room the analysed room volume is the part inside the closed envelope (or the roofed cells
around the marker when the gap is too wide).

**Rain test**: every room floor cell (a room cell that is not itself a wall cell, with a wall cell below) needs a
block that is motion-blocking for the `MOTION_BLOCKING` heightmap (tag `#blocks_motion_in_heightmap` or any fluid)
somewhere above it in the box -> otherwise **error** (rain reaches the floor). The cell directly above a fire/campfire
is exempt.

## 5. Walkability
Player: 0.6 wide, 1.8 tall, step-up 0.6, jump apex 1.25, safe drop <= 3 (more is allowed only into water or past a
climbable block). The player stands centred in a column (footprint `[0.2,0.8]^2`); moving to a neighbour passes a
**straddle footprint** (0.6 x 0.6 square centred on the shared edge, built from both columns' collision boxes), so
half-blocks behave realistically: bottom slabs / stairs are stepped onto, a stair approached from its high side or a
full block needs a jump, carpets are 1/16, fence posts (1.5 high) block, panes block.

Collision used: the dump's collision shapes, with doors and fence gates treated as **open** (passable), trapdoors
directly above/below a climbable block treated as open hatches, scaffolding passable, and dangerous blocks
(fire, lava, magma, lit campfire, cactus, sweet berry bush, wither rose, powder snow) as solid cubes that cannot be
stood on.

Nodes are (column, feet height). Standing nodes: top of a collision interval with >= 1.8 free above. Climbing
nodes: feet inside a `#climbable` cell (ladders, vines, scaffolding, cave/weeping/twisting vines), a water cell, or a
trapdoor directly above a ladder with the same `facing` (`LivingEntity#trapdoorUsableAsLadder`, once opened), at
integer heights. Moves: horizontal via the straddle (walk if the rise <= 0.6; jump if <= 1.25 and the start column is
free up to target + 1.8; from a climbing node up to 1.6 because the feet can rise to the top of the ladder cell; falls
land on the highest support below and must be <= 3 unless water/climbable is in the fall path), climb up/down inside
climbable/water cells, drop off the bottom of a ladder. BFS starts from every entrance (nearest node within ±1 of
the given feet y; error if none).

A room is **reachable** if a visited node is in the marker's column with feet in `[y-0.5, y+1)`; otherwise
**error** with the nearest visited spot (and a note if the marker itself is not standable).
**Doors**: for every lower door half, both cells along its facing axis must have a standing node with feet in
`[y-1, y+0.6]` (i.e. 1.8 clear above a floor) -> otherwise **error** naming the blocking blocks.

## 6. Lighting and hostile spawns
Block light like `BlockLightEngine#propagateIncrease`: sources = state light emission; a neighbour gets
`level - max(1, lightDampening)` where dampening is 15 for solid-render blocks (and tinted glass), else <= 1; light
does not cross a face when `Shapes.faceShapeOccludes` says the two face occlusion shapes together cover it (only
blocks with `useShapeForLightOcclusion`: slabs, stairs, snow layers, farmland, paths, lecterns, ...). Iterated to a
fixed point (numpy). Doors, panes, trapdoors and glass do not occlude light (dampening 0, no occlusion shape -
verified per state), so light passes a closed door losing 1.

**Sky light** (used only by the mushroom / crop / sapling rules, not for spawning): `ChunkSkyLightSources` - going down
each column from the open sky above the box, every cell is a level-15 source until the first edge where the lower
cell's light dampening is not 0 or the two occlusion faces cover the face; then the same propagation as block light
with `max(1, dampening)`. Dampening = 15 for solid-render blocks and tinted glass, 1 for leaves, else 0 if
`propagatesSkylightDown` (default: outline not a full cube and no fluid; class overrides ported) else 1 - this
matches the game for all 35,723 states. Outside the box: flat terrain at `ground` under open sky.

Hostile spawn spot (zombie-sized, `SpawnPlacementTypes.ON_GROUND` + `NaturalSpawner`): block below `isValidSpawn`
(default: FULL-sturdy top face and emission < 14; never on glass/copper grates, trapdoors, ice, magma, barrier,
bedrock, scaffolding, leaves have no sturdy top; jack o'lantern and redstone lamp always), the feet and head cells
pass `isValidEmptySpawnBlock` (not full collision, not a signal source, no fluid, not `#prevent_mob_spawning_inside`,
not dangerous), the 0.6 x 1.95 spawn box touches no collision box (so carpets, slabs, pressure plate... floors are
safe), and **block light 0** at the feet. Inside a room region -> **error** (count + first 50 positions); elsewhere in
the box -> one **info** with the count (normal for grass at night). Per room: min/mean light.

## 7. Architecture metrics (info, `checks.metrics`)
* `footprint`: in the 3 layers above ground, cells that are building fabric (enclosure walls minus
  fences/walls/gates/leaves/plants/carpets/snow, plus doors and glass panes/bars) and room cells, holes filled,
  largest 4-connected component. `convex_corners` / `concave_corners` of its outline (rectangle = 4 / 0), `area`.
* `roof`: per footprint column the highest building-fabric block (height map). Ridge cells = local maxima
  (>= their 4 neighbours) that either continue horizontally (a same-height local-max neighbour) or are strict apexes;
  this drops the diagonal hip lines of hip roofs. Connected ridge cells of one height spanning >= 3 cells are ridge
  lines (`ridge_lengths`); shorter ones made only of stairs/slabs are `apex_peaks` (hip-roof tops; chimneys of other
  blocks are ignored). `ridge_heights` / `distinct_ridge_heights` cover both; `max_height_above_ground`.
* `facades`: exterior wall cells = fabric cells above ground whose horizontal neighbour (N/S/E/W) is outside air.
  `windows` = connected groups of glass (blocks or panes) in one facade plane. `longest_flat_run` = longest
  horizontal run of the same block id in one facade plane at one height (no depth change); `largest_flat_patch` =
  largest 4-connected same-block patch in one facade plane.
* `distinct_blocks` (ids) / `distinct_states`; `building_blocks` (authored blocks in footprint columns, foundation
  to roof) vs `landscaping_blocks` (all other authored blocks), `landscaping_fraction`,
  `footprint_fraction_of_box`.
* `rooms`: floor area per room = room cells (not themselves a slab/stair/full-top block) standing on a walkable
  floor block (wall cell with a FULL-sturdy top, or a slab/stair), total and per feet level (`by_floor_y`). Rooms
  whose markers share one region report the same area; door niches that belong to the room count. (The rain test
  uses all room cells above any wall cell, furniture included.)

## Report format
`run_qa` returns a JSON-serialisable dict:
```
{ "slug", "title", "size": [sx,sy,sz], "ground",
  "summary": {"errors", "warnings", "infos", "passed"},
  "checks": {"validity": {...}, "floating": {...},
             "support": {"checked", "failed", "unchecked_types", "falling", "fluid_escapes", "decaying_leaves", "melting"},
             "enclosure": {"rooms": {name: {"marker",
             "leaks": [{"breach": [x,y,z], "kind", "path_len"}], "volume", "floor_cells", "uncovered_floor"?}}},
             "walkability": {"entrances": [...], "rooms": {name: {"marker", "reachable", "nearest"?}}, "doors": [...],
             "reachable_nodes"}, "lighting": {"rooms": {name: {"spawnable_spots", "min_light", "mean_light"}},
             "landscape_spawnable_spots", "light_source_types"}, "metrics": {...}},
  "issues": [{"check", "severity", "message", "pos"?: [x,y,z], "block"?, "count"?, "positions"?, "room"?}, ...],
  "timing_s": {...}, "qa_version": 1, "game_version": "26.3" }
```
Issues are sorted errors -> warnings -> infos, then by check order. `write_report` writes the markdown summary
(`report_markdown`) and the JSON.

## Performance
45 x 45 x 40 set-sized box with 16 two-storey huts: ~0.2 s. Random registry states in 45x45x40 (1.5k / 8k / 24k
blocks, 16 rooms): 0.8 / 1.3 / 2.1 s; 16 huts with every room leaking plus ponds, mushrooms, crops and
gravel: 0.9 s; a 42k-block maze of slabs/stairs/trapdoors/panes: 1.0 s.

## Known limitations
* Block and sky light are ports of the engine's propagation rules (their per-state inputs are verified) but the
  resulting light maps were not compared with the in-game light engine. Time of day, weather and redstone power are
  not simulated; spawning uses block light only (night).
* The movement model does not crouch: a passage that only a sneaking player (1.5 high) fits through - e.g. a 2-high
  doorway directly followed by a slab or stair step up - is reported as unreachable / blocked.
* Enclosure assumes the free space inside a partial cell (slab, stair, trapdoor, bed, ...) is one region; fences,
  panes, bars and walls are solid cells even where their thin shape would leave a gap (e.g. an unconnected pane post).
* The movement model is a conservative grid approximation (centred footprints + edge straddles): it does not model
  sprint-jumps across gaps, crawling under 1.5-high gaps, ladders entered sideways mid-air, boats, or parkour; a
  stair approached from the side is treated as its higher half (needs a jump, usually fine with headroom).
* Light occlusion between two partially covering faces is exact only on a 1/32 raster.
* Enclosure connectivity is face-based (6-connectivity between cells, exact face slices on a 1/32 raster): gaps
  that only exist along a cell edge or corner between full blocks never leak, which matches air/mob movement.
* Fluids: only "does it move at all" is checked (first spread step), not where the water ends up; concrete powder
  next to water and fire spread are not checked. Random-tick checks use the engine thresholds but ignore rain
  (rain keeps farmland wet while it lasts) and whether a sapling has room to grow.
* Hostile spawn spots are zombie-sized (0.6 x 1.95); a spider (1.4 wide, 0.9 high) can also spawn under a dark
  1.5-high gap such as a large top-slab table, which is not reported.
* Footprint / ridge / facade metrics are heuristics intended for critics, not ground truth.

## palette (allowed-blocks constraint)

Enabled when the build carries an allowed-blocks list (`Build(..., allowed_blocks=...)`, `--palette=FILE`,
`$BLOCKWRIGHT_PALETTE`, or `python -m blockwright qa file.litematic --allowed FILE`). The structure's material list
(`blockwright.materials`: the items a player needs, e.g. one `oak_door` per door, `torch` for a wall torch) is compared
with the list; every item outside it is an **error** with an example position. Entries are item ids, globs
(`*_planks`) or block tags (`#minecraft:logs`, expanded to their items); see `blockwright/palette.py`.
