# `blockwright` core library — builder reference

Minecraft Java **26.3** (data version 5023) + Litematica **0.29.1**. Everything here is validated against the
real registry dump / decompiled game + Litematica sources; typos fail loudly at the line that made them.
Paths/conventions: `docs/CONVENTIONS.md`. Working example: `examples/builds/b00_demo.py`.

```python
from blockwright import *

b = Build("cozy_cottage", "Cozy Cottage", ground=0, description="Two-room starter cottage.")
spruce, oak = wood("spruce"), wood("oak")
b.fill(0, 0, 0, 8, 0, 6, "cobblestone")              # foundation in the ground layer
b.walls(0, 1, 0, 8, 3, 6, oak.planks)                 # hollow outline
front = b.frame((4, 1, 6), "south")                   # facade frame (see Frames)
front.door(0, 0, 0, "spruce")                         # facing="in" by default
front.entrance(0, 0, 1)
b.room("living", 4, 1, 3)
if __name__ == "__main__":
    b.finish()
```
Run `python builds/cozy_cottage.py [--quick] [--no-render] [--no-qa] [--views=iso_se,cut_1] [--lenient] [--palette=my_blocks.txt]`
(or `python -m blockwright build cozy_cottage --quick`). `python -m blockwright new <slug>` scaffolds a script.

Allowed-blocks constraint: `Build(..., allowed_blocks="my_blocks.txt")`, `b.set_allowed_blocks(path_or_list)`, `--palette=FILE` or `$BLOCKWRIGHT_PALETTE`; QA then reports every needed item outside the list as an error in the `palette` check (format: `blockwright/palette.py`).

---------------------------------------------------------------------------------------------------------------
## 1. Coordinates, ground, states

* x = east, y = up, z = south. Author in any integers (negative OK); `finish()` shifts the bounding box to (0,0,0).
* `ground` = y of the natural terrain surface layer (where grass would be). Standing things go at `ground+1`.
  Unset cells stay air in the schematic = **the natural terrain stays**: author landscaping (grass, path, podzol, moss…)
  at `ground` only where you want it; never fill a platform.
  Paste with Litematica's **Replace = "with non-air"**: the default "none" places a block only where the world has
  air (`SchematicPlacingUtils`), so ground-layer paths/foundations would not replace the grass; "all" also pastes the
  schematic's air and clears the whole bounding box. With "with non-air", terrain inside rooms is NOT cleared either
  (schematic air is never pasted) – pick a flat site or clear it first.
* A **state** is a vanilla command string: `"oak_stairs[facing=east,half=top]"`. Namespace optional, missing
  properties get registry defaults. Everything you set is converted to the canonical full form
  `minecraft:oak_stairs[facing=east,half=top,shape=straight,waterlogged=false]`.
* Unknown block/property/value → `ValueError` with suggestions (`chain` → "Did you mean: iron_chain?").
* Air is never stored (`b.set(..., "air")` deletes). `AIR == "minecraft:air"`.
* **Do not hand-set derived properties** – `finish()` runs `blockwright.resolve`, which recomputes them exactly like the game
  (see §8): stair `shape`, fence/pane/bars/wall sides + wall `up`, gate `in_wall`, leaves `distance` (+ forces
  `persistent=true`), `snowy`, campfire `signal_fire`, mushroom-block faces toward the same block, shelf `side_chain`,
  vine faces, chest `type` pairing, cave/weeping/twisting vines + kelp head/body, `pale_hanging_moss` `tip`,
  door upper half.

26.3 names that differ from memory: `iron_chain` (not chain), `short_grass`, `dirt_path`; new: wooden `*_shelf`,
`leaf_litter`, `wildflowers`, `bush`, `firefly_bush`, `poplar_*` wood (leaves are `orange_/red_/yellow_poplar_leaves`),
`pale_oak_*`, resin & tuff bricks, wool/concrete stairs+slabs, `straw_bed`, copper lanterns/chains/bars/torches.

---------------------------------------------------------------------------------------------------------------
## 2. Block helpers (`blockwright.blocks`, all re-exported)

All return canonical states. Directional args (`facing`) accept the Frame aliases `"out"|"in"|"left"|"right"`
(only usable through a Frame, §4).

### Families
```python
w = wood("spruce")     # oak spruce birch jungle acacia dark_oak pale_oak mangrove cherry poplar bamboo crimson warped
w.planks  w.fence  w.pressure_plate  w.leaves (persistent)  w.mosaic (bamboo)        # states or None
w.door  (id for b.door)   w.ids (role -> id or None)   w.leaves_variants (e.g. poplar: orange/red/yellow)
w.log(axis="y")  w.wood(axis)  w.stripped_log(axis)  w.stripped_wood(axis)          # bamboo: log = bamboo_block, no wood
w.stairs(facing, half="bottom")  w.slab(type="bottom")  w.gate(facing, open=False)
w.trapdoor(facing, half="bottom", open=False)  w.button(facing="north", face="wall")
w.sign(rotation=0)  w.wall_sign(facing)  w.hanging_sign(rotation=0, attached=False)  w.wall_hanging_sign(facing)
w.shelf(facing)  w.mosaic_stairs(facing, half)  w.mosaic_slab(type)
```
Missing members: attributes are `None`, methods raise `ValueError` (e.g. `wood("crimson").leaves is None`).

```python
s = stone("cobblestone")   # also "stone_brick"/"stone_bricks", "mossy_stone_brick", "brick", "mud_brick", "tuff_brick",
                           # "polished_tuff", "deepslate_tile", "deepslate_brick", "cobbled_deepslate", "andesite",
                           # "granite", "sandstone", "smooth_stone", "resin_brick", "quartz", ...
s.block  s.wall            # states or None (smooth_stone has no stairs/wall -> stairs_id/wall_id None)
s.block_id s.stairs_id s.slab_id s.wall_id
s.stairs(facing, half="bottom")   s.slab(type="bottom")
```

### Generic helpers
| helper | notes |
|---|---|
| `state(name, **props)` | any block; bool/int values OK: `state("oak_trapdoor", facing="east", open=True)` |
| `stairs(material, facing, half="bottom")` | `"spruce"`, `"oak_planks"`, `"stone_bricks"`, `"cobblestone"`, `"white_wool"`… |
| `slab(material, type="bottom")`, `wall(material)`, `fence(material)`, `gate(material, facing, open=False)` | |
| `log(material, axis="y")`, `trapdoor(material, facing, half="bottom", open=False)` | `log("crimson")` → crimson_stem |
| `door_id(wood)`, `bed_id(color)` | ids for `b.door` / `b.bed` |
| `lantern(hanging=False, kind="lantern")` | kind: `lantern`/`soul`/`copper`/`exposed_copper`/`waxed_copper`… |
| `torch(facing=None, kind="torch")` | `facing` given → wall torch pointing away from its wall |
| `candle(color=None, count=1, lit=True)` | |
| `leaves(kind)` | always `persistent=true`: `leaves("oak")`, `leaves("orange_poplar")`, `leaves("flowering_azalea")` |
| `vine(*faces)` | `vine("north","up")`; `vine()` = let resolve attach to every supporting neighbour |
| `potted(plant)` | `potted("red_tulip")`, `potted("azalea_bush")`, `potted("fern")` |
| `campfire(facing="north", lit=True, kind="campfire")` | `kind="soul"` for soul campfire; signal smoke is automatic (hay below) |
| `chain(axis="y", kind="iron")` | id `iron_chain` / `copper_chain` … |
| `barrel(facing, open=False)`, `chest(facing, type="single", kind="chest")`, `shelf(material, facing)` | |
| `pane(color=None)`, `glass(color=None)`, `wool(color)`, `carpet(color)` (`carpet("moss")`) | `glass("tinted")` = tinted_glass |

Facing semantics (verified in the 26.3 sources):
* **stairs** `facing` = side of the tall back. A roof slope rising toward the north uses `facing=north`.
* **door** `facing` = direction a player looks when placing it; the panel sits on the cell edge *toward* that player
  (door facing north hugs the south edge). `hinge` left/right as seen by that player.
* **open trapdoor** facing F lies against the cell edge opposite F (shutter on a south wall: put it in the cell
  outside the wall with `facing="out"`, `open=True`).
* **wall torch / ladder / wall sign / shelf / chest / barrel**: facing = the way the front points (away from the
  supporting wall / toward the player who placed it). **campfire** facing = the direction the placing player looked
  (only turns the logs). **bed** facing = foot→head direction. **sign `rotation`** 0 = south, 4 = west, 8 = north,
  12 = east.
* **double chest**: use `b.double_chest(...)` (§3). By hand: `type=left` has its partner at `facing` turned clockwise
  (chest facing north, type=left → partner to the east); a half without its partner is reset to single by resolve.

---------------------------------------------------------------------------------------------------------------
## 3. `Build`

```python
b = Build(slug, title, *, ground=0, author=None, description="", allowed_blocks=None)   # author None = config "author"
b.set(x, y, z, state)      b[x, y, z] = state      b.get(x, y, z) -> state | "minecraft:air"
b.remove(x, y, z)          del b[x, y, z]          (x, y, z) in b      len(b)
b.fill(x1,y1,z1, x2,y2,z2, state, where=None)      # inclusive, any corner order; returns #cells written
b.walls(x1,y1,z1, x2,y2,z2, state, where=None)     # 4 vertical sides of the box, no floor/ceiling
b.line((x1,y1,z1), (x2,y2,z2), state, where=None)  # 3D Bresenham, both ends included
b.disk(cx, y, cz, r, state, filled=True, where=None)
b.ellipse(cx, y, cz, rx, rz, state, filled=True, where=None)   # filled=False -> 1-block outline
b.ellipsoid(cx, cy, cz, rx, ry, rz, state, where=None, filled=True)
b.replace(match, new, region=None)     # match: "oak_planks" (any state) | full state | "#minecraft:logs" | fn(x,y,z,s)
                                       # new: state | fn(x,y,z,old)->state ("air" deletes); region=(x1,y1,z1,x2,y2,z2)
b.bounds() -> ((minx,miny,minz),(maxx,maxy,maxz)) | None     b.size()     b.count(id_or_#tag=None)
b.palette() -> Counter{state: n}        b.copy(slug=None, title=None)       b.blocks  (the raw dict; don't bypass set)
```
* `slug` must be lowercase `[a-z0-9_-]` (it becomes the file name; Litematica mangles names with special characters
  or the substrings COM/PRN). `title` is free text (shown in Litematica).
* `where`: `None` (overwrite) | `"air"` (only empty cells) | `"occupied"` | `fn(x, y, z, current_state) -> bool`.
* `state` may be a callable `fn(x, y, z) -> state` in `fill/walls/line/disk/ellipse/ellipsoid` for per-block
  variation, e.g. `b.fill(..., lambda x,y,z: gradient([(0,"mossy_cobblestone"),(2,"cobblestone")], x,y,z, seed=3))`.
* Coordinates must be ints (floats raise `TypeError`).

### Multi-block helpers (all parts placed with consistent properties)
```python
b.door(x, y, z, wood, facing, hinge="left", open=False)   # lower half at y; wood: "spruce"|"iron"|"copper"|id|WoodFamily
b.bed(x, y, z, color, facing)                              # FOOT at (x,y,z), HEAD at (x,y,z)+facing; color or "straw"
b.tall(x, y, z, plant, upper_waterlogged=False, **props)   # any DoublePlantBlock: lilac rose_bush peony sunflower
                                                           # tall_grass large_fern pitcher_plant small_dripleaf(facing=)...
b.double_chest(x, y, z, facing, side, kind="chest", waterlogged=False)   # 2nd half one block toward `side`
```
* These produce exactly what a player's placement creates (`DoorBlock`/`AbstractBedBlock.setPlacedBy`,
  `DoublePlantBlock.setPlacedBy`). `tall`: the upper half copies the lower's properties, but **not** `waterlogged`
  (the game takes it from the water at the upper position) – a waterlogged `small_dripleaf` gets a dry upper half
  unless `upper_waterlogged=True`. `pitcher_crop` below age 3 is a single block: use `b.set`.
* `double_chest`: `side` must be perpendicular to `facing`; `kind`: chest | trapped_chest | copper_chest | …
* `b.count("oak_stairs")` counts every state of the block; `b.count("oak_stairs[facing=east]")` that exact state
  (like `replace`).

### QA markers
```python
b.room("kitchen", x, y, z)   # player FEET position inside the room (that cell + the one above must be passable)
b.entrance(x, y, z)          # feet position just OUTSIDE the main door
b.note("free text for the QA/report")
```

---------------------------------------------------------------------------------------------------------------
## 4. Frames — author a facade once, place it on any side

```python
f = b.frame(origin, facing)          # facing: "south" | "west" | "north" | "east"  (the way the facade faces)
```
Write everything in the **canonical orientation "facade faces south"**:

```
            north (= "in")
    u = +x  (viewer's right, "right" = east)            v = up
    w = +z  (outward, toward the viewer, "out" = south)
            viewer stands outside, looking at the facade
```
`origin` is the world position of local (0,0,0). The frame rotates **positions and states** (facing, axis, rotation,
fence/wall sides, rails, hinge…) to its real facing. Inside a frame every direction is canonical: `"north"` means
"in", `"south"` = "out", `"west"` = "left", `"east"` = "right" — and the aliases `facing=out|in|left|right` are
accepted (helpers accept them as arguments: `spruce.stairs("out")`). Outside a frame aliases are rejected.

```python
f.set(u, v, w, state)   f.get(u, v, w)   (returns the state in canonical orientation)   f.remove(u, v, w)
f.fill(u1,v1,w1, u2,v2,w2, state, where=None)   f.walls(...)   f.line(p1, p2, state)
f.door(u, v, w, wood, facing="in", hinge="left", open=False)    # "in" = placed from outside
f.bed(u, v, w, color, facing)   f.tall(u, v, w, plant)   f.room(name, u, v, w)   f.entrance(u, v, w)
f.double_chest(u, v, w, facing, side)                           # e.g. ("out", "right")
f.paste(prefab, at=(u, v, w), rot=0, mirror=None, markers=False) # prefab authored in canonical orientation
f.at(u, v, w) -> world (x,y,z)   f.to_local(x, y, z)   f.dir("out") -> world direction   f.state(s) -> world state
f.frame(at, facing="south")      # nested frame; facing relative to this frame
```
Callables passed to frame methods receive LOCAL coordinates (and local-orientation states).

Example — one window technique on three facades:
```python
def window(f, u, v, flower):
    f.set(u, v, 0, pane()); f.set(u, v + 1, 0, pane())
    for du in (-1, 1):                                   # open shutters folded against the wall, outside
        f.set(u + du, v, 1, spruce.trapdoor("out", "bottom", open=True))
        f.set(u + du, v + 1, 1, spruce.trapdoor("out", "top", open=True))
    f.set(u, v - 1, 1, spruce.stairs("in", "top"))       # upside-down stair sill
    f.set(u, v, 1, potted(flower))

window(b.frame((8, 1, 5), "east"), 0, 0, "red_tulip")
window(b.frame((5, 1, 3), "north"), 0, 0, "cornflower")
```

## 5. Prefabs: `paste`
```python
b.paste(other_build, at=(x, y, z), rot=0, mirror=None, where=None, markers=False)
```
`other`'s (0,0,0) lands on `at`. Order: mirror first (`"x"`: x→−x, east↔west; `"z"`: z→−z, north↔south), then
`rot` clockwise quarter turns seen from above (north→east→south→west; `(x,z)→(−z,x)`), then translate.
States are mirrored/rotated geometrically correctly (stairs shape, door hinge and chest halves swap handedness).
Checked against the game's own `BlockState.rotate/mirror` for all 35,723 states of 26.3: identical except where
vanilla is geometrically wrong (stair/chest/shelf handedness under some mirrors, anvil mirror, fire/chorus sides not
rotated) – see `tests/test_core_gamecheck.py`. Chiseled-bookshelf slots and brewing-stand bottles are not remapped
(same as vanilla). Tile entities of pasted blocks come along (NBT not rotated).
`markers=True` also copies the prefab's rooms/entrances (a room name that already exists raises `ValueError`).

Low level: `rotate_state(state, quarter_turns_cw)`, `mirror_state(state, "x"|"z")`.

---------------------------------------------------------------------------------------------------------------
## 6. `finish()`

```python
result = b.finish(views="all", qa=True)    # kwargs: render=True, strict=True, out_dir=None, argv=None
```
Pipeline: resolve → normalize to (0,0,0) (ground/markers shifted) → strict validation → `out/schematics/<slug>.litematic`
(+ `out/structures/<slug>.nbt` for `/place template`, + `out/schematics/<slug>.meta.json`) → read-back check
(the file is parsed back and compared block by block) → materials `out/materials/<slug>.md|json` → `blockwright.qa.run_qa`
→ `out/reports/<slug>_qa.md|json` → `blockwright.render.render_views` → `out/previews/<slug>/` and a 120×120 thumbnail
embedded in the litematic (`PreviewImageData`). Missing/crashing qa or render modules only warn.

Strict validation errors (raise `BuildError`, all problems listed): unpaired door/bed/double-plant halves, illegal or
non-canonical states (only if you wrote `b.blocks` directly), room markers outside the box or inside solid blocks,
entrance markers in solid blocks. `--lenient` (or `strict=False`) exports anyway with warnings.

CLI flags (read from `sys.argv` by `finish()`): `--quick` (fewer views), `--no-render`, `--no-qa`,
`--views=a,b` (renderer view names: `iso_se`, `iso_nw`, `elev_n`, `top`, `cut_1`, `eye`, …), `--lenient`.

Prints a summary (size, block count, palette size, resolve changes, QA headline, output paths) and returns a dict
(`litematic`, `structure`, `materials`, `qa_report`, `previews`, `size`, `blocks`, `palette_size`, `resolve`, `warnings`, …).
Determinism: same script → byte-identical files except the two timestamps; set `CC_TIME_MS=<ms>` (> 0) to pin those too.
`b.structure()` returns `(blocks, size, meta, resolve_stats)` without writing anything.

---------------------------------------------------------------------------------------------------------------
## 7. Noise (never use `random`)

```python
gradient([(0, "mossy_cobblestone"), (2, "cobblestone"), (5, "stone_bricks")], x, y, z, seed=7, jitter=1.5, scale=3.0)
# band starting heights in ascending order; edges wobble smoothly by +-jitter (neighbours agree: no salt & pepper)
value2(x, z, seed, scale=4.0)  value3(x, y, z, seed, scale=4.0)  fbm2(x, z, seed, scale=8, octaves=3)  fbm3(...)   # [0,1]
hash3(x, y, z, seed) -> uint32   hash01(x, y, z, seed) -> [0,1)   chance(p, x, y, z, seed)   pick(choices, x, y, z, seed, weights=None)
```
Use smooth noise (`gradient`, `value*`, `fbm*`) for material transitions; per-block `chance/pick` only for sparse accents.

## 8. What `blockwright.resolve` computes (ported from the 26.3 sources; verified against the game's own `updateShape`)
| rule | source |
|---|---|
| stair `shape` (inner/outer corners) | `StairBlock.getStairsShape` |
| fence sides (fences/wooden_fences tags, sturdy faces, gates, exceptions: leaves, pumpkins, melons, barrier, shulker boxes) | `FenceBlock.connectsTo` |
| glass pane / iron & copper bars sides | `IronBarsBlock.attachsTo` |
| wall sides none/low/tall + post `up` (uses the collision shape of the block above, `#wall_post_override`) | `WallBlock.updateShape/shouldRaisePost` |
| gate `in_wall` | `FenceGateBlock` |
| leaves `distance` (BFS from `#prevents_nearby_leaf_decay` = logs, max 7) and `persistent=true` | `LeavesBlock.updateDistance` |
| `snowy` (snow/snow_block/powder_snow above) | `SnowyBlock` |
| campfire `signal_fire` (hay below) | `CampfireBlock.isSmokeSource` |
| mushroom-block faces toward the same block → false; other faces keep what you wrote (default = all true, i.e. the placement result; an all-`false` "pores" block stays) | `HugeMushroomBlock.updateShape` |
| shelf `side_chain` = unconnected unless powered | `ShelfBlock`/`SideChainPartBlock` |
| vine faces: unsupported faces dropped (a vine with none left is removed + warning); `vine()` with no faces attaches to every supporting side (or the ceiling) | `VineBlock` |
| chest `type`: a left/right half without a connectable chest on its partner side → single (+ warning); a single chest next to a half pointing at it (same facing) becomes the other half; copper chest pairs end up one oxidation stage (least oxidized) | `ChestBlock/CopperChestBlock.updateShape` |
| cave/weeping/twisting vines, kelp: a head (`cave_vines`) with its plant continuing in the growth direction becomes the body (`cave_vines_plant`, berries kept); a body at the end becomes the head with `age=25` (no further growth) | `GrowingPlantHeadBlock/BodyBlock.updateShape` |
| `pale_hanging_moss` `tip` = no hanging moss below | `HangingMossBlock.updateShape` |
| door upper half copies the lower half; unpaired doors/beds/double plants are errors (a `pitcher_crop` below age 3 is one block) | `DoorBlock/AbstractBedBlock/DoublePlantBlock.updateShape` |

Neighbours outside the build count as air. Not handled (author them yourself): pale moss carpet sides, glow lichen /
multiface faces, redstone, note-block instruments, dripstone thickness, bamboo, scaffolding distance, bed `occupied`,
block support (a torch on air) — QA reports unsupported blocks. Every rule output is checked to be a fixpoint of the
game's own `updateShape` code (`tests/test_core_gamecheck.py`). Vine/cave-vine heads with `age` < 25 keep growing in
the world.

## 9. Registry API (`blockwright.registry`, also `R`)
```python
parse_state(s) -> canonical          make_state("candle", candles=3, lit=True)        props(s) -> dict   prop(s, "facing")
# prop() -> None when the block lacks that property; a name no 26.3 block has (typo) raises ValueError.
# has_tag/is_a/block_class raise ValueError for unknown block ids (never a silent False).
block_id(s)    with_props(s, open=True)    with_block(s, "spruce_stairs")  (keeps compatible props)    item(s)
phys(s) -> Phys(sturdy_faces: frozenset, can_occlude, full_collision, solid_render, light, collision_boxes)
has_tag(s_or_id, "minecraft:fences")   tag_members("#logs")   is_a(s_or_id, "LeavesBlock")   block_class(s)
R.info(id) -> BlockInfo(id, cls, block_entity, item, properties, default)   R.exists(id)   R.all_blocks()   R.is_air(s)
```

## 10. Files & lower-level I/O
```python
from blockwright import litematic, structure_nbt, validate, materials
litematic.write_litematic(path, blocks, size, *, name, author, description="", region_name=None,
                          preview_argb=None, tile_entities=None, ground=None, time_ms=None) -> info dict
litematic.read_litematic(path) -> (blocks, size, metadata)    # metadata["ground"] parsed from the description
litematic.preview_from_image(png_or_PIL) -> 120*120 ARGB ints
structure_nbt.write_structure(path, blocks, size)   structure_nbt.read_structure(path) -> (blocks, size, data_version)
validate.validate_file(path, expected=(blocks, size)) -> {"ok", "errors", "warnings", "stats"}
materials.material_list(blocks) -> {"items", "groups", "total_items", "warnings", "notes"}
```
The verified Litematica format facts (tag names/types, palette index 0 = air, bits = max(2, ceil(log2 n)), entries
spanning longs, index `(y*sz + z)*sx + x`, 120×120 ARGB preview) are documented at the top of `blockwright/litematic.py`.
Materials count obtainable items: doors/beds/double plants once, double slabs ×2, candles/pickles/petals/leaf litter
by amount, `potted_X` → flower_pot + X, wall variants → their item, water source / waterlogged → water_bucket,
crops → seeds, cave vines → glow berries, farmland/dirt_path → dirt; creative-only blocks are warnings.
