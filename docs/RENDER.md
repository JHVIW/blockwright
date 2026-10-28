# blockwright.render — preview renderer

Pure-numpy software renderer that draws a structure with the **real 26.3 block models, textures, tints and
lighting rules** (extracted from the client jar), so previews look like the game. No GPU / OpenGL needed.

## Use

```python
from blockwright.render import render_views, render_view, read_litematic

paths = render_views(blocks, size, "out/previews/cozy_cottage", meta=meta)            # all views + sheet
paths = render_views(blocks, size, out_dir, meta=meta, views="quick")                 # iso_se, iso_nw, cut_1
paths = render_views(blocks, size, out_dir, meta=meta, views=["iso_se", "cut_2", "eye"])
render_view(blocks, size, {"name": "door", "target": (12, 3, 8), "radius": 4,       # close-up camera
                           "azimuth": 30, "elevation": 25}, "door.png", meta=meta)
```

* `blocks`: `{(x, y, z): state}` — canonical or partial state strings (missing properties take registry
  defaults, namespace optional). `size`: `(sx, sy, sz)`. `meta`: structure meta (`slug`, `title`, `ground`,
  `rooms`, `entrances`); `ground` is guessed when missing (lowest mostly-terrain layer, else `min y - 1`).
  Invalid states (unknown block, property or value) are drawn as the magenta/black missing-model cube and
  reported once on stderr (`[blockwright.render] WARNING ...`) — check stderr or the sheet for magenta.
* Returns PNG paths `<out_dir>/<slug>_<view>.png`, plus `<slug>_sheet.png` (labelled contact sheet) last.
  View dicts without a `name` are called `custom`, `custom_2`, ...; two different views never share a file.
* Keyword options: `terrain=True`, `width=1600, height=1200` (output size), `supersample=2`,
  `shadows=True`, `workers=None` (process pool, default min(views, cpu/2, 8)), `sheet=True`, `verbose=False`.

CLI (reads `.litematic` itself, plus the `<stem>.meta.json` sidecar and the `ground layer: y=N` description line
written by `blockwright.litematic`):

```
python -m blockwright render out/schematics/b01_x.litematic out/previews/b01_x [--quick] [--views iso_se,top,cut_1]
       [--closeup X,Y,Z[,radius[,azimuth[,elevation]]]] [--no-terrain] [--no-shadows] [--size 1600x1200]
       [--ground N] [--slug NAME] [--workers N]
```
`--quick` and `--views` combine (quick set + the listed views); `--closeup` adds close-ups to either.
A corrupt file (BlockStates array too short, palette index out of range) raises `ValueError` with the region name;
palette entry 0 is not assumed to be air.

## Views

| name | camera |
|---|---|
| `iso_se`, `iso_sw`, `iso_ne`, `iso_nw` | orthographic from that corner, elevation 32° |
| `elev_s`, `elev_e`, `elev_n`, `elev_w` | orthographic, straight at the south/east/north/west facade, elevation 10° |
| `top` | orthographic plan from above, north up |
| `cut_1`, `cut_2`, … | per storey: only blocks with `y <= cut` (re-meshed, so floors/wall tops show), from SE at 55°, framed on the part of the build that was covered |
| `eye` | perspective (70° FOV) at eye height (ground+1+1.62) in front of `meta.entrances[0]`, far enough back that the facade fits; terrain extended 48 blocks so the camera stands on grass |

`"all"` = the 9 fixed views + one cutaway per storey + `eye` (only if entrances are given). `"quick"` =
`iso_se`, `iso_nw`, `cut_1`. Storeys: from `meta.rooms` (cut = standing y + 1) or, without rooms, from floor
layers (≥25 % of the roofed footprint solid with two open layers above; cut = floor + 2).

A view dict may contain: `name`, `type` (`"ortho"` | `"eye"`), `azimuth` (0 = camera south of the build,
90 = east, 180 = north, 270 = west), `elevation` (deg), `cut` (y), `target` (x,y,z block to centre on) with
`radius` (half view height in blocks) or `zoom` (factor on the auto-framed scale), `fov`/`distance`/`side_offset`
for `eye`, `shadows` (bool), `shadow_res`.

## What is reproduced from the game (26.3 client/common source)

* **Blockstates**: `variants` (property-subset keys, `""`), `multipart` (`when` with `|`, `!`, `OR`, `AND`),
  weighted lists (deterministic per-position pick), `x`/`y`/`z` rotations (OctahedralGroup composition
  Z·Y·X), `uvlock` (BlockMath.getFaceTransformation port; a test checks that every oak-stairs face maps its
  texture to world axes exactly like a plain block, so roof planks line up).
* **State validation**: a state the game cannot hold (unknown block, unknown property, illegal value — e.g.
  `oak_fence[east=yes]`, `oak_planks[axis=y]`) is drawn as the magenta/black missing-model cube and a warning is
  printed once, instead of being half-drawn (a multipart fence would otherwise silently lose its arms). Missing
  properties still take registry defaults. A multipart state matching no part, or a model without elements
  (e.g. `pitcher_crop[age=0,half=upper]`), is invisible exactly as in the game.
* **Models**: parent chain, texture slots (a face's `texture` names a slot with or without `#`; unresolved slots
  get the missing sprite) incl. 26.x `{"sprite", "force_translucent"}` materials, elements
  with from/to, per-face `uv` (FaceBakery.defaultFaceUV when absent), face `rotation`, element rotation
  (`axis`/`angle` and 26.x `x`/`y`/`z` euler, origin, `rescale`), `tintindex`, `cullface`,
  `shade_direction_override` (26.x replacement of `shade`), `light_emission`, `ambientocclusion`; faces on a
  zero-thickness axis are skipped like UnbakedCuboidGeometry does.
* **Render layer per quad** from the sprite's alpha inside the face UV rect (26.x rule:
  any 1..254 alpha → translucent, any 0 → cutout, else solid). Animated textures: first frame.
* **Per-state physics from the game**: `blockwright/data/render_physics_26.3.json` is dumped from the real 26.3 block
  states by `blockwright/java/RenderPhysicsDump.java` (face occlusion shapes per side as 16x16 masks, legacy
  `isSolid`, `getLightDampening`, `propagatesSkylightDown`, `getShadeBrightness`, `emissiveRendering`,
  `useShapeForLightOcclusion`). Without the file the renderer falls back to approximations from the registry
  dump (collision shapes instead of occlusion shapes, class-based shade/dampening). Regenerate with
  (Git Bash, from the project root):
  `python -m blockwright dump-registry` (needs `setup` with a JDK; writes the file for the configured version).
* **Face culling**: Block.shouldRenderFace — neighbour face-occlusion shape vs own face shape, plus the
  skipRendering overrides (every HalfTransparentBlock incl. glass/stained/tinted glass, ice, blue ice, slime,
  honey, copper grates: same-block; panes/bars connection rule; fluids; mangrove roots; powder snow). Leaves never
  cull each other (cutout leaves, the 26.3 default). Quads are one-sided.
* **Shading**: CardinalLighting.DEFAULT (up 1.0, down 0.5, N/S 0.8, E/W 0.6) and smooth AO exactly as
  BlockModelLighter (corner tables, faceCubic rule, Block.getShadeBrightness — 0.2 for full-collision blocks,
  1.0 for glass, 0.2 for mud/soul sand — lightPermeable, partial-face weighting), AO disabled for light-emitting
  blocks; flat-lit quads take the light of the neighbour in their cull direction (or own cell), raised to the
  block's own emission (LightCoordsUtil.getLightCoords). Interpolated bilinearly instead of per triangle.
* **Light engine**: sky sources straight down until the first dampening/opaque/occluding cell, then propagation in
  all six directions losing max(1, dampening) per block; opaque blocks receive nothing; slabs/stairs/snow etc.
  (useShapeForLightOcclusion) stop light where both face shapes together cover the face; block light from
  `lightEmission`. Smooth per-vertex blending is LightCoordsUtil.smoothBlend (exact neighbour substitution
  rules, 1/16-level truncation).
* **Lightmap** (`lightmap.fsh` with the overworld-noon environment attributes): ambient `#0A0A0A`, white sky
  light, block light x1.4 with the warm `BLOCK_LIGHT_TINT #FFD88C` blended by the parabolic mix factor, clamp,
  notGamma mixed with gamma option 0.5; sampled per vertex with linear filtering like `terrain.vsh`. Light is an
  RGB colour per vertex: unlit interiors are ~9 % bright (not black) and mid-level lantern light is orange.
  Interiors behind windows and under roofs are dark like in the game; cutaways (roof removed) are lit.
* **Tints** (BlockColors at plains, T 0.8 / D 0.4): grass `#91BD59`, foliage `#77AB2F` (oak/jungle/acacia/
  dark oak/mangrove leaves, vines), spruce `#619961`, birch `#80A755`, dry foliage (leaf litter), petals/
  wildflowers layer 1, lily pad, water `#3F76E4`, stems, redstone. Cherry/azalea/pale oak/poplar are untinted.
* **Random offsets** for flowers/grass/ferns etc. (offsetType XZ/XYZ, exact Mth.getSeed formula).
* **Fluids**: water/lava from `water`/`lava` blocks, `waterlogged=true` and always-water plants; heights
  `amount/9`, corner averaging (neighbours with legacy `isSolid`, e.g. slabs/stairs/walls round a pond, are
  excluded like in FluidRenderer.getHeight), face rules, top face with the still sprite or — when
  FlowingFluid.getFlow is non-zero — the flowing sprite turned along the flow; sides outward-facing plus the
  reversed copy (water and lava), or the single `water_overlay` face next to glass/ice/leaves; directional
  shade on all fluid faces; water translucent.
* **Special (block-entity) renderers** rebuilt from the real entity models + textures + model transforms:
  chests (single/double, trapped, ender, copper), bell body, banners (dye colour, no patterns), shulker boxes,
  mob heads/skulls (dragon/piglin simplified), decorated pot, enchanting-table book, lectern book, copper golem
  statue, conduit, end portal/gateway (dark surface). Beds, signs and hanging signs are ordinary block models in
  26.3. Invalid states and states without a model render as the magenta/black missing-model cube.
* Extras not in vanilla: sun **shadow map** (sun at the camera's front-left, 55° high, PCF, 35 % darkening),
  synthetic terrain, sky gradient, exact per-pixel translucency sorting, 2x supersampling.

## Terrain

With `terrain=True` every **air** cell with `y <= ground` in the box plus a 4-block margin (48 for `eye`) becomes
`grass_block` (at `ground`) / `dirt` (3 layers below). Cells the build occupies are never replaced and nothing
above `ground` is filled. This mirrors pasting with Litematica's "replace with non-air" behaviour (air in the
schematic keeps the world's terrain), so a cellar left as air below `ground` is shown filled — that is what the
world would contain. Note: Litematica 0.29.1's default `pasteReplaceBehavior` is `NONE` (existing blocks are not
replaced at all), under which even the build's ground-layer blocks (paths, podzol...) would not replace grass.

## Assets

`ensure_assets()` extracts once from the vanilla client jar (downloaded by `python -m blockwright setup`) into `<cache>/minecraft/<version>/assets/minecraft/`:
`blockstates/`, `models/block/`, `textures/block/` (+ `.mcmeta`), `textures/entity/`, `textures/colormap/`.
Run `python -m blockwright setup --force` to force re-extraction (`doctor` prints the cache folder).

## Performance (this machine: Ryzen 7 5800X3D, 8C/16T)

| scene | quads (full) | all views (12 incl. 2 cutaways + eye) |
|---|---|---|
| synthetic 35x40x30 timber house (4.4k blocks) | 16.6k | 12–14 s |
| same + dense leaf masses  | — | 15 s |
| demo `b00_demo.litematic` | 3.4k | 13 s (CLI, incl. startup) |

Single iso view of the house ≈ 3 s in one process (views run in parallel, ~6–8 s each under load). Memory per worker ≈ 0.4 GB (peak, measured with tracemalloc) at 3200x2400 internal resolution.
Implementation note: arrays are processed in 64k-sample chunks — on Windows larger temporaries go straight to
VirtualAlloc and page-fault zeroing serialises the worker processes (4x slower in parallel).

## Module map

* `assets.py` — jar extraction, JSON/texture loading (first animation frame), colormap lookup, registry dump,
  class ancestry (tags dump), per-state render physics.
* `java/RenderPhysicsDump.java` — generator for `blockwright/data/render_physics_26.3.json` (see above).
* `models.py` — blockstate dispatch, model resolution and baking (`bake_state`), `Quads` container, sprite table.
* `special.py` — entity-model cuboids (ModelPart.Cube UV layout) and the special block renderers.
* `mesh.py` — scene assembly: palette/grid, terrain, culling, tints, AO, light engine, fluids → `Scene`.
* `raster.py` — atlas, cameras, quad setup (homography per quad), sample generation, z-buffer, deferred
  shading, translucency, shadow map.
* `views.py` — view presets, storey detection, framing, process pool, contact sheet.
* `litematic_io.py` — standalone `.litematic` reader (LitematicaBitArray, entries may span two longs).

## Known limitations

* Not drawn: sign text, banner patterns, items on campfires/shelves/item frames, any entities (armor stands,
  paintings, item frames), animated parts (open chests, swinging bells), beacon beams, enchant/end-portal effects.
* Light: the propagation rules are the game's, but it runs over the scene box only (no light from outside the
  box). Daylight only, overworld-noon colours. Light is evaluated per vertex and interpolated, like the game.
* Weighted random variants (grass top rotation, stone mirroring...) and flower offsets depend on the *world*
  position, which is unknown before pasting; the renderer uses schematic coordinates (offsets with the game's
  formula, variant picks with its own hash), so per-block picks differ from any particular placement.
* No biome blending (single plains biome); animated textures show their first frame (the render layer is also
  taken from the first frame; the game ORs all frames).
* Eye view needs `meta.entrances`; obstacles between the camera and the facade (trees) are not avoided, and the
  camera distance is chosen from the whole footprint width (a far-away camera for wide builds).
* `cut_N` beyond the detected storeys is skipped with a warning (pass a dict `{"name": ..., "cut": y}` instead).
* Without `render_physics_<version>.json` culling/fluids/light use the approximations described above.
