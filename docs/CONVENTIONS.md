# Engineering conventions (single source of truth)

Target: **Minecraft Java 26.3** (data version **5023**) and **Litematica 0.29.1** (schematic `Version` 7, `SubVersion` 1),
the tested combination. Python 3.10+ with numpy, pillow and nbtlib.

## Ground truth sources (use these, never guess)

| What | Where |
|---|---|
| Every block, its properties, legal values, defaults, item, per-state physics and collision shapes | `blockwright/data/blocks_26.3.json` (dumped from the real game registry by `blockwright/java/RegistryDump.java`) |
| Block and fluid tags (resolved) and the block class hierarchy | `blockwright/data/tags_26.3.json` (`java/ClassAncestorsDump.java` + the jar's `data/minecraft/tags`) |
| Renderer physics (face occlusion, light dampening, shade) | `blockwright/data/render_physics_26.3.json` (`java/RenderPhysicsDump.java`) |
| Client assets (blockstates, models, textures, colormaps) | downloaded by `python -m blockwright setup` from Mojang into the user cache; never committed |
| Litematica / MaLiLib jars (validator only) | downloaded by `setup` from Modrinth into the user cache |

Regenerate all three data files for the configured version with `python -m blockwright dump-registry` (needs
`setup` with a JDK). The files are facts about the game (ids, properties, shapes, tag membership), not Mojang assets.

`blockwright/data/blocks_26.3.json` schema:
```
{ "version": "26.3", "data_version": 5023, "dirs": "down,up,north,south,west,east",
  "phys_format": "sturdyMask(bit i = dirs[i]),flags(1 canOcclude,2 fullCollision,4 solidRender,8 air),lightEmission,collisionShapeIndex",
  "shapes": ["", "0 0 0 1 1 1", "x1 y1 z1 x2 y2 z2;x1 ...", ...],          # collision boxes in block units
  "blocks": { "minecraft:oak_stairs": {
      "class": "StairBlock", "block_entity": false, "item": "minecraft:oak_stairs",
      "properties": {"facing": ["north","south","west","east"], "half": [...], ...},   # legal values, as strings
      "default": {"facing": "north", ...},
      "phys": "6,1,0,29"                       # when identical for all states, else:
      "phys_by_state": {"facing=north,half=top,shape=straight,waterlogged=false": "6,1,0,29", ...}  # keys: props sorted as the game lists them
  } } }
```
Note 26.3 names that differ from older versions: `minecraft:iron_chain` (not `chain`), copper lanterns/chains/bars/torches exist,
wooden `*_shelf` blocks exist, plus `leaf_litter`, `wildflowers`, `bush`, `firefly_bush`, `poplar_*` wood set with
`orange_/red_/yellow_poplar_leaves`, `shelf_mushroom`, `golden_dandelion`, pale oak, resin bricks, tuff bricks.

## Coordinates & orientation

* x = east (+), y = up (+), z = south (+). Same as Minecraft and Litematica.
* A build is authored in its own integer coordinates (negative allowed). On export the bounding box is normalized so the
  min corner is (0,0,0); `ground` is shifted accordingly and stored.
* `ground` = the y of the **natural terrain surface layer** (the layer a grass block occupies). Things standing on the
  ground are at `ground+1`. Foundations may go 1–2 layers below `ground`.
* Landscaping is authored as blocks at `ground` (path, coarse dirt, podzol, moss, grass under flowers) and above.
  Cells left unset stay air in the schematic, so in the world the natural terrain stays — that is how builds blend in.
  Do not fill the whole rectangle with a platform; outline landscaping organically.
* Block-state strings use vanilla command syntax: `minecraft:oak_stairs[facing=north,half=bottom]`. The namespace is
  optional on input. Unspecified properties take registry defaults. Unknown blocks/properties/values are hard errors.
* Canonical full form (used in files, reports, palettes): namespace included, **all** properties present.

## Workspace layout

A *workspace* is any folder you build in (the current directory, or `--workspace` / `$BLOCKWRIGHT_WORKSPACE`):

```
my-builds/
  builds/<slug>.py                 one bespoke script per build (python -m blockwright new <slug>)
  out/schematics/<slug>.litematic  (+ <slug>.meta.json sidecar: ground, rooms, entrances, allowed blocks)
  out/structures/<slug>.nbt        vanilla structure file (for /place template)
  out/previews/<slug>/*.png        every view + <slug>_sheet.png contact sheet
  out/reports/<slug>_qa.md|json    QA report
  out/materials/<slug>.md|json     material list
  notes/briefs/  notes/logs/  notes/critiques/  notes/LESSONS.md   the agent loop's paper trail
  scratch/critic_<slug>_r<k>/      critic prototypes (copies, never the original script)
  dist/<name>.zip                  python -m blockwright package
```

A script in `<ws>/builds/` writes to `<ws>/out/` no matter where it is run from.

## Package layout

```
blockwright/__init__.py   re-exports Build, helpers (from blockwright import *)
blockwright/config.py     config file + env vars + cache paths (nothing machine-specific is hard-coded)
blockwright/cli.py        python -m blockwright <command>
blockwright/setup_env.py  setup: Mojang client jar, assets, validator deps
blockwright/registry.py   load the registry dump + tags; parse/normalize/validate states; phys, shapes, tags
blockwright/build.py      Build (sparse voxel dict), Frame (oriented local coords), paste with rotate/mirror, finish()
blockwright/blocks.py     state helpers + material families (wood("spruce"), stone("cobblestone"), ...)
blockwright/rotate.py     rotate_state / mirror_state (match the game's own rotate/mirror)
blockwright/resolve.py    game-accurate post-processing (stair shapes, fence/wall/pane connections, leaves, ...)
blockwright/litematic.py  write_litematic / read_litematic
blockwright/structure_nbt.py  vanilla structure .nbt writer/reader
blockwright/validate.py   pure-Python file validation (always runs in finish())
blockwright/validator.py  the optional Litematica-native validator (Java)
blockwright/materials.py  material list (block -> obtainable item counts)
blockwright/palette.py    allowed-blocks constraint
blockwright/noise.py      deterministic hash/value noise for material gradients
blockwright/qa.py         automated quality checks -> report dict + markdown
blockwright/render/       numpy software renderer with the real block models and textures
blockwright/java/         RegistryDump, RenderPhysicsDump, ClassAncestorsDump, LitematicValidate
```
Builder scripts start with:
```python
from blockwright import *
```

## Core data model (shared by core, qa, render)

* A **state** is the canonical full string (`"minecraft:spruce_stairs[facing=east,half=top,shape=straight,waterlogged=false]"`).
  Air is `"minecraft:air"` and is never stored in a Build's dict (absence = air).
* A **structure** handed between modules is: `blocks: dict[tuple[int,int,int], str]` (canonical states, normalized so min
  corner is (0,0,0)), `size: (sx, sy, sz)`, and `meta: dict` with at least
  `{"slug", "title", "ground": int, "rooms": {name: (x,y,z)}, "entrances": [(x,y,z), ...], "notes": str}`.
  `blockwright.litematic.read_litematic(path)` returns `(blocks, size, metadata_dict)`.
* qa: `blockwright.qa.run_qa(blocks, size, meta, registry=None) -> dict`, `blockwright.qa.write_report(report, md_path, json_path)`.
* render: `blockwright.render.render_views(blocks, size, out_dir, meta=None, views="all"|"quick"|[...], terrain=True) -> list[paths]`
  and `blockwright.render.render_view(blocks, size, view: dict, out_path, ...)`; plus CLI `python -m blockwright render <file.litematic> <out_dir>`.

## Litematica format facts (to be verified against the decompiled 0.29.1 jar)
Gzipped NBT, root compound (empty name): `MinecraftDataVersion` Int 5023, `Version` Int 7, `SubVersion` Int 1,
`Metadata` {Name, Author, Description: String; RegionCount, TotalVolume, TotalBlocks: Int; TimeCreated, TimeModified: Long;
EnclosingSize {x,y,z Int}; optional PreviewImageData IntArray}, `Regions` {<name>: {Position{x,y,z}, Size{x,y,z},
BlockStatePalette List<Compound{Name, Properties?}> (index 0 = minecraft:air), BlockStates LongArray (LitematicaBitArray:
bits = max(2, ceil(log2(paletteSize))), entries packed back-to-back and MAY span two longs, index = (y*sizeZ + z)*sizeX + x,
length = ceil(volume*bits/64)), TileEntities, Entities, PendingBlockTicks, PendingFluidTicks: List<Compound>}}.

## Style
Plain, readable Python; small functions; docstrings on public API; no clever metaprogramming. Deterministic output
(no unseeded randomness; use `blockwright.noise`). Every builder script must be bespoke — shared helpers are *techniques*
(e.g. "stair", "door", "Frame"), never "make_house(width, depth, material)".
