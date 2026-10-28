# Technique catalogue

Audience: builder and critic agents writing bespoke build scripts (`builds/<slug>.py`). It turns what skilled human
builders do into rules you can measure and recipes you can copy at block level. It is **style-neutral**: palettes,
motifs and style-specific exceptions live in the style packs (`docs/styles/*.md`), and the short list of mistakes
that cost real rounds lives in [`LESSONS.md`](LESSONS.md). Read LESSONS first; use this file as the reference you
look things up in.

All block ids are checked against `blockwright/data/blocks_26.3.json`, and mechanics claims were checked against the
decompiled Minecraft Java 26.3 source.

**The goal:** every building should look as if a skilled human built it by hand over an evening. It must never look
like the output of `make_house(w, d)`. Anything here that seems like overkill exists to prevent the "plain rectangle
with a basic roof" look.

Examples in this file are mostly drawn from pitched-roof, timber-and-stone vernacular builds, because that is where
the recipes were battle-tested. Swap the materials for your style pack's; the geometry carries over.

## Notation

* Block states use vanilla syntax, namespace omitted: `spruce_stairs[facing=north,half=top]`.
* Facade-relative directions: **`<out>`** = the facade's outward normal (the direction you face when you walk out
  of the door). **`<in>`** = its opposite. **`<left>`/`<right>`** = along the facade, as seen from outside.
  `facing=<out>` means "set facing to whatever compass value is the outward normal of this facade". Use the Frame
  helper (`b.frame(...)`, see `docs/API.md`) to resolve these. Hard-coding compass values per facade is error prone.
* Depth layers of a facade: **L-1** is one block behind the main wall plane (inside), **L0** is the main wall plane,
  **L+1** is one block proud of it (outside), and **L+2** is two blocks out.
* `g` = ground (the y of the natural grass layer). Things standing on the ground are at `g+1`. A ground-floor *floor
  block* sits at `g+1`, so the player stands at `g+2`. See H06.
* ASCII legend (unless a figure says otherwise): `S` = stair (bottom half), `i` = inverted stair (`half=top`),
  `s` = bottom slab, `t` = top slab, `B` = full block, `L` = log, `W` = wall block (infill), `G` = glass pane,
  `T` = trapdoor, `F` = fence, `.` = air, `~` = water, `#` = stone, `%` = moss/leaves, `*` = flowers.

Facts about stair and trapdoor orientation, verified from the collision shapes in the 26.3 registry dump:

* `X_stairs[facing=north,half=bottom]`: the bottom half is full and the tall back is on the **north** side, so you
  walk up it going north. On a roof slope, **stairs face the ridge** (`facing=<in>` of that slope).
* `X_stairs[facing=north,half=top]` (inverted): the top half is full and the lower quarter is on the **north** side.
* `X_trapdoor[facing=north,open=true]`: the panel hugs the **south** edge of its cell. A trapdoor that should lie
  flat against a wall behind it therefore uses **`facing=<out>`** (away from the wall). This covers shutters,
  planter fronts and cabinet doors.
* `X_trapdoor[half=top,open=false]` is a thin plate at the **top** of the cell (y 13/16–16/16). Use it for sills,
  soffits and shelves. `half=bottom` is a plate on the floor of the cell.
* Wall-attached blocks (`wall_torch`, `ladder`, `*_wall_banner`, `*_wall_sign`, button/lever `face=wall`) use
  `facing=<out>`, pointing away from the block they hang on.

---

## 1. Handcrafted vs procedural: measurable rules

Procedural boxes share one look: one rectangle, one wall material, one flat facade plane, evenly spaced identical
windows, a 45° gable with no overhang, floors at ground level, and a rectangle of grass or path around them. The rules
below are designed so the QA and metrics in `docs/QA.md` can check most of them. **Hard** rules must pass. **Soft**
rules may be broken only with a written reason in `meta["notes"]`.

A style pack may override a rule for a reason that belongs to the style (a modern flat roof does not need a 45°
pitch; a Japanese engawa replaces the plinth step). Overrides are listed in each pack's "Deviations from LESSONS"
section. Everything else applies.

### 1.1 Rules

| id | rule | metric / threshold | hard? |
|---|---|---|---|
| H01 | **Massing: one main volume + 1–3 subordinate volumes.** Subordinates include wings, lean-tos, porches, bays, towers and dormer clusters. | Largest axis-aligned rectangle in the footprint ≤ 75% of the footprint area. At least one re-entrant corner (L/T/U/cross) or a projection ≥ 2 deep and ≥ 3 wide. | hard |
| H02 | **Subordinates really are subordinate.** | Each subordinate ridge is ≥ 1 block (better 2–3) lower than the main ridge, or the subordinate is a tower ≥ 3 blocks *higher*. Its width is ≤ 0.75 × the main volume's width. | hard |
| H03 | **Roof overhang.** | Eaves overhang ≥ 1 block past the outer wall plane on every eave. Gable verges (rakes) overhang ≥ 1. A 2-block overhang is good on big roofs (≥ 11 span) and on porch-side eaves. | hard |
| H04 | **Roof dominance** (pitched-roof styles). | Main roof height (eave line to ridge) ÷ wall height (floor to eave): 1-storey 0.9–2.0, 2-storey 0.6–1.3, 3-storey ≥ 0.5. Main-roof pitch ≥ 45°. Pitches shallower than 45° are allowed only for porches, lean-tos, shed dormers and the flared lowest course. Flat-roof styles replace this with a parapet/fascia rule in their pack. | hard |
| H05 | **Silhouette has several heights.** | Footprints > 9×9 need ≥ 2 distinct ridge (or roof) heights. Every building needs ≥ 3 vertical accents among chimney, dormer, finial, tower/turret, tall tree within 4 blocks. | hard |
| H06 | **Raised floor and visible plinth.** | Ground floor block at `g+1` or higher, with a step (stair or slab) up to every exterior door. A plinth at least 1 course tall (`g+1`) is visible on ≥ 70% of the perimeter, and its bottom course carries a weathering gradient (§3.2.7). The foundation goes 1 block below `g` so no gap shows on uneven terrain. | hard |
| H07 | **No long flat wall plane.** | Along any facade row, at most **5** consecutive cells may share the same outermost depth *and* the same block. Stone plinths and long stone walls may go to **7**. Vertically, at most **4** cells before a horizontal break: floor beam, jetty, sill band, pent roof or material change. | hard |
| H08 | **At least three depth layers per facade.** | Every facade longer than 4 blocks has blocks at L0 and L+1 (posts, sills, shutters, planters, beam ends, brackets), and glass or a door at L-1 or set behind a proud frame. The pattern "frame out, glass in" applies to every window. | hard |
| H09 | **Material discipline.** | 3–5 main materials per facade plus 1–2 accent materials. Every main material uses a 2–4 block gradient (§2.2). No main surface ≥ 12 cells may be 100% one block. | hard |
| H10 | **Windows vary.** | ≥ 2 window types per building (width, height, shape or treatment). Spacing along a facade is not perfectly regular: at least one gap differs by ≥ 1. Upper-floor windows are equal or smaller in width than ground-floor ones. Glazed area is 8–20% of the facade (gables, greenhouses and glazing-led styles are exempt). | soft |
| H11 | **Asymmetry.** | The whole building is not mirror-symmetric on either axis. A single gable end may be locally symmetric, and formal buildings (town hall, manor, temple) may have a symmetric centre block provided their wings or setting differ. | soft |
| H12 | **Odd spans for gables.** | Gable spans (outer wall to outer wall) are odd (5, 7, 9, 11, 13), so the ridge lands on a single centre column. Even spans need a deliberate ridge solution (§3.1.2). | soft |
| H13 | **Detail density.** | Per 8 blocks of facade length, ≥ 2 detail elements: lantern, planter, shutters, bracket, sign, bench, vine patch, potted plant, barrel or woodpile. Vines, leaves and lichen together cover ≤ 12% of any facade's area. | soft |
| H14 | **Ground contact is soft.** | ≥ 60% of the perimeter has vegetation (flowers, grass, bush, leaves, moss) within 2 blocks of the wall. No landscaping edge runs straight for more than **7** blocks. No rectangular platform: the landscaped area's outline has ≥ 8 convex/concave turns. | hard |
| H15 | **Lighting prevents spawns.** | Every interior air cell that a mob could stand in has block light ≥ 1. The overworld's `monster_spawn_block_light_limit` is **0** in 26.3. The exterior is lit by lights along every path and at every door. | hard |
| H16 | **Circulation works.** | Every door has a free 1×2 cell in front and behind it. Every room is reachable through cells with ≥ 2 air above the floor. Stairs have ≥ 2 air above every step and landing. Main walkways are 2 wide in houses with interior width ≥ 9 and 1 wide elsewhere. | hard |
| H17 | **Every room is furnished.** | Each room has 1 focal piece (bed, hearth, table, counter, shelf wall) and furniture along 30–60% of its wall-adjacent floor cells, and the centre stays free. Walls and floor differ in material, and walls and ceiling differ in material. | hard |
| H18 | **Blocks only, plausible states.** | No entities (no item frames, paintings, armour stands, minecarts or boats). Leaves `persistent=true`. Two-part blocks are complete and consistent: door `half=lower/upper`, bed `part=foot/head`, and tall plants (`lilac`, `peony`, `rose_bush`, `sunflower`, `tall_grass`, `large_fern`, `pitcher_plant`, `small_dripleaf`) `half=lower/upper`. Gravity blocks (`gravel`, `sand`, `anvil`, concrete powder) need support. Plants on legal substrates (§5.0). No creative-only blocks (`light`, `barrier`, `structure_void`, `petrified_oak_slab`, command blocks, `infested_*`, spawners). | hard |

### 1.2 The look checklist (eyeball pass on the renders)

1. **Squint test:** from 30 blocks away, is the silhouette interesting? There should be a big roof (or a strong
   roofline), at least one secondary volume, a chimney or vertical accent, and maybe a tower or a tree. If it reads
   as a box with a lid, go back to H01, H02 and H05.
2. **Shadow test:** in the noon render, do eaves, jetties, sills and posts cast shadow lines? If a facade is evenly
   lit, it is flat, so go back to H07 and H08.
3. **Story test:** can you tell who lives there and what they do from outside alone (woodpile, anvil, flowers,
   nets, barrels)?
4. **Edge test:** where the build meets the terrain, does it fade out through planting, path gradients and
   scattered stones? A crisp border means you should go back to H14 and §5.
5. **Restraint test:** is anything spammed, such as vines everywhere, lanterns every 2 blocks, or 9 flower species?
   Pick 2–3 flower species per bed (one or two flowers per yard plus a filler) and let surfaces breathe.

### 1.3 Proportion cheat sheet

* **Storey module:** floor block (1) + clear height 3 (cosy rooms, bedrooms) or 4 (main living room, shop, hall).
  The upper storey is often 1 lower than the ground storey.
* **Footprints:** small cottage main volume 7×9 or 7×11; medium house 9×13; hall or inn 11×17. Wings are 5 or 7
  wide.
* **Eave height:** 1-storey cottage eave at `g+5`…`g+6`. A catslide side can drop to `g+3`.
* **Door:** 1 wide × 2 tall (doors are 2 blocks). Give it a 3-wide surround and a transom or lintel above it, so
  the opening reads 3×3 or 3×4.
* **Windows:** 1×1 (attic, pantry), 1×2 (standard), 2×2, 3×2 (living room, shop), 1×3 (stair tower, gable).
* **Chimney:** 1×1 flue inside a 2×2 or 3×2 stack. The top is ≥ 1 above the ridge for ridge chimneys, or ≥ 2 above
  the roof surface where it exits.
* **Odd numbers** everywhere: spans, post spacing (3 or 5 between posts), dormer widths (3 or 5).

---

## 2. Materials, value and cohesion

### 2.0 Cohesion across a set

When several buildings form a set (a village, a street, a campus), cohesion comes from **shared families**, and
variety comes from **how they are mixed**:

* **One foundation family** for the whole set (for example the cobblestone/stone-brick/andesite/tuff family), with
  each building's palette setting the proportions.
* **Shared hardware:** one lantern type for street and door lights, one fence type for garden fences, one low-wall
  type. Reserve a special variant (for example copper lanterns with their green flame) for a few special buildings.
* **Roof families:** most buildings (about 75%) use one of two or three "set roofs"; special buildings get special
  roofs.
* **Neighbour rule:** two buildings within about 24 blocks of each other never share both the same palette *and* the
  same roof family.

The style pack names the families; the cottagecore pack shows a complete worked assignment for a 20-building set.

### 2.1 Measured texture colours (26.3 client jar, mean RGB of opaque pixels, L = luminance 0–255)

Use these numbers to order gradients and to check contrast. Small luminance steps (≤ 25) blend. Large steps (≥ 60)
read as frame against fill. LESSONS.md §1 asks for ≥ 40 L (or a clear hue change) between the roof field and the
dominant wall material.

| material | hex | L | | material | hex | L |
|---|---|---|---|---|---|---|
| `stripped_pale_oak_log` | f6eeed | 240 | | `oak_planks` | a2834f | 134 |
| `calcite` | dfe0dd | 224 | | `andesite` | 888889 | 136 |
| `pale_oak_planks` | e4dad8 | 220 | | `cobblestone` | 807f80 | 127 |
| `smooth_sandstone`/`sandstone` | d8cb9c | 203 | | `jungle_planks` | a07351 | 122 |
| `mushroom_stem` | cbc5ba | 197 | | `stone_bricks` | 7a7a7a | 122 |
| `polished_diorite` | c1c1c3 | 193 | | `mossy_stone_bricks` | 737969 | 119 |
| `cherry_planks` | e3b3ad | 189 | | `cracked_stone_bricks` | 767676 | 118 |
| `white_terracotta` | d2b2a1 | 184 | | `polished_granite` | 9a6b59 | 116 |
| `stripped_birch_log` | c5b076 | 176 | | `mossy_cobblestone` | 6e765f | 115 |
| `birch_planks` | c0af79 | 175 | | `packed_mud` | 8e6b50 | 112 |
| `bamboo_mosaic` | beaa4e | 168 | | `mud_bricks` | 89684f | 109 |
| `sulfur_bricks` | bba85b | 166 | | `resin_bricks` | ce5818 | 109 |
| `stripped_cherry_log` | d79195 | 160 | | `tuff` | 6c6d67 | 108 |
| `stripped_poplar_log` | a5998c | 154 | | `bricks` | 976253 | 108 |
| `stripped_oak_log` | b19056 | 147 | | `stripped_acacia_log` | af5d3c | 108 |
| `poplar_planks` | 96897f | 139 | | `tuff_bricks` | 62675f | 101 |
| `hay_block` | a68926 | 136 | | `moss_block` | 596e2d | 101 |
| `stripped_jungle_log` | ab8555 | 138 | | `cinnabar` | 98534e | 97 |
| `stripped_spruce_log` | 745a34 | 93 | | `spruce_planks` | 735531 | 89 |
| `oak_log` | 6d5533 | 88 | | `cobbled_deepslate` | 4d4d51 | 78 |
| `polished_cinnabar` | 993a37 | 78 | | `cinnabar_bricks` | 943836 | 75 |
| `polished_deepslate` | 484949 | 73 | | `deepslate_bricks` | 474747 | 71 |
| `mangrove_planks` | 763631 | 67 | | `poplar_log` | 4f3d2b | 63 |
| `stripped_dark_oak_log` | 493924 | 59 | | `deepslate_tiles` | 373737 | 55 |
| `dark_oak_planks` | 432b14 | 47 | | `dark_oak_log` | 3c2f1a | 48 |
| `spruce_log` | 3b2611 | 41 | | `cherry_log` | 37212c | 38 |

Notes:

* `poplar_*` (new in 26.3) is a cool greige wood. Its bark (`poplar_log`) is dark brown and its leaves exist only in
  autumn colours: `yellow_poplar_leaves`, `orange_poplar_leaves`, `red_poplar_leaves`. There is no green poplar
  leaf.
* `cinnabar*` is a red stone. `cinnabar_bricks`/`cinnabar_brick_stairs` make a convincing clay-tile roof.
* `resin_bricks` is vivid orange. Use it only as an accent (chimney pots, an oven).
* `sulfur*` is acid-yellow stone. Use it at most as a small accent.
* `calcite`, `white_terracotta`, `mushroom_stem` and `packed_mud` have **no** stairs or slabs. For white trim use
  `white_concrete_stairs`/`_slab`, `pale_oak_stairs`/`_slab`, `smooth_quartz_stairs` or `diorite_stairs`.
* **New in 26.3:** all 16 colours of `*_wool_stairs`/`*_wool_slab` and `*_concrete_stairs`/`*_concrete_slab` exist.
  They work well for awnings, upholstery, coloured roof trims and crisp modern edges.
* **Biome tint warning:** `oak_leaves`, `dark_oak_leaves`, `jungle_leaves`, `acacia_leaves`, `mangrove_leaves`,
  `vine`, `short_grass`, `tall_grass`, `fern`, `bush`, `leaf_litter`, `grass_block`, `pink_petals`/`wildflowers`
  stems and water all change colour with the biome they are pasted into. For a guaranteed colour use
  `azalea_leaves`, `flowering_azalea_leaves`, `cherry_leaves`, `spruce_leaves`, `birch_leaves`, `pale_oak_leaves`,
  the poplar leaves, or `moss_block`/`moss_carpet`.

### 2.2 Gradient rules (apply to every main surface)

* **60/30/10:** base block 60%, variant 30%, accent 10%. Choose per cell with the deterministic noise helpers
  (`docs/API.md` §7; never `random`). Use value noise at scale 3–5 blocks for patches, not per-cell white noise,
  which looks like static. Per-cell noise is acceptable only for the sparse 10% accent, and LESSONS.md §2 tightens
  this further: weathering goes in runs of 2–5.
* **Weathering bias, bottom-up and at corners** ("bleeding"): increase mossy variants within 2 blocks of the
  ground and at outside corners, and cracked variants at corners and around openings. Make walls lighter higher up.
* **Dither boundaries:** where two materials meet (stone plinth to timber wall, light infill to darker base), mix
  them in a 1–2 row checker or band. Use this sparingly, because over-dithering looks messy.
* **Frame against fill:** the frame material must differ from the fill by ΔL ≥ 50 (dark timber on light plaster)
  *or* by hue (oak on stone). A frame member never runs parallel and adjacent to another frame member: two posts
  side by side read as a fat blob.
* **The roof differs from the walls** in material and usually in value. Roofs read best darker than walls. Light
  roofs (cherry, bamboo, copper) need dark eave and verge trims to hold the edge.

---

## 3. Technique catalogue

### 3.1 Roofs

**Universal roof rules**

1. Build the **highest roof first** and join lower roofs into it. Remove buried blocks afterwards.
2. A roof is **two layers thick** wherever you can see its edge. The top layer is stairs/slabs. Under every exposed
   eave and verge stair goes an inverted stair or a full block (§3.1.3). A single stair layer looks like cardboard.
3. Above roughly 15×15, never use one simple roof. Split it into sections.
4. Stair shapes at corners and valleys (`inner_*`/`outer_*`) are computed by `resolve` when the build finishes.
   Place the straight stairs facing the correct way and let it resolve.
5. Inside, cover the roof underside. Use inverted stairs under the slope for an attic ceiling, or a flat ceiling
   with beams (§4.2).

#### 3.1.1 Pitch profiles (side sections; the ridge is to the right)

```
45° (1 up : 1 in)       63° "steep" (2 up : 1 in)      26.5° "low" (1 up : 2 in)
           S                       S                          ss
         S                         S                       ss
       S                         S                      ss
     S                           S                   ss
                               S
stairs, each one up and in     stair-on-stair per step     bottom/top slab alternation:
                               (a stair directly under a    s t s t ... (half-block rise per column)
                                stair, same facing)
```
* Steep courses use **stair-on-stair**, not a stair on a plank riser: the plank face reads as a "wedding cake" step
  (LESSONS.md §3).
* Custom pitch: repeat a 2–3 column pattern, e.g. `s`, `i`, `S` per column (5 up per 7 across). It needs a big roof
  to read.
* 45° is the default. 63° is for towers, A-frames and whimsical or gothic roofs. 26.5° is for porches, lean-tos, the
  flare course and shed dormers.

#### 3.1.2 Gable (45°, 7-wide house, 1 overhang): cross-section across the ridge

```
col:      0  1  2  3  4  5  6  7  8          E = eave level (y of the top wall course)
E+4                   R                      R = ridge: a low cap (bottom slab of the field family), a full
E+3                S  B  S                       block only under a finial
E+2             S  B  B  B  S                 S = roof stair facing the ridge
E+1          S  B  .  .  .  B  S               B = under-layer (full block or i) - only needed where seen
E         S  W  .  .  .  .  .  W  S           W = wall top course at cols 1 and 7
E-1       i  W                 W  i           i = inverted stair bracket under the eave stair, facing=<in>
```
* Span 7 gives 4 stair courses and a ridge at `E+4`. In general a 45° roof height = (span+1)/2 and a 63° roof
  height ≈ span+1.
* **Even span** (avoid): two stair courses meet back to back at the top. Cap them with a slab row of trim material
  at +1.
* **Ridge caps:** a slab row of the field family, or a `*_wall` row (`cobblestone_wall`, `cinnabar_brick_wall`,
  `deepslate_tile_wall`) for a rounded tile ridge. Log ridges read as beams lying on the roof. Put a finial at each
  end: `lightning_rod`, an `end_rod` + `*_wall` stack, or a `*_fence` + `lantern`.

#### 3.1.3 Eave edge and verge (rake) trims: the "thick edge"

```
Eave (long side), section:                 Verge (gable end) - elevation of the gable from outside:
      S  <- roof                                         R
   S  B                                              Sv iv Sv          Sv = verge stair facing up-slope
 S  B                                             Sv iv     iv Sv      iv = inverted stair under it, facing
 i  W   <- inverted stair, facing=<in>         Sv iv           iv Sv         down-slope (away from ridge)
    W     (bracket/cove)                     Sv iv  [gable infill]  iv Sv
 T        optional: trapdoor[half=top]       iv                        iv  <- verge foot: inverted stair
          soffit one more out on big roofs                                    or a log end (beam end)
```
* **Verge, two options (pick one per building):**
  * (a) a **solid 2-thick verge in the field material** (stair plus inverted stair of the same block) when the gable
    wall is light: calm, and the wall gives the contrast;
  * (b) a **contrasting barge board** (stair plus partner in a trim wood) when the field is dark and the gable is not
    light. This is the single biggest upgrade over a procedural roof.
  Never both dark. Verge, eave lip and ridge together form one continuous trim frame.
* **Rafter tails/brackets:** under the verge foot and under the eave every 2–3 blocks, add a `*_fence` stub
  sticking out (+1), or an inverted stair as a corbel, or a log end (`axis` = `<out>` axis).
* **Fascia drop:** on large roofs (span ≥ 11) the eave course can step *down* one more course at L+2 (overhang 2),
  using a slab row (`s` at E-1) for a flicked edge.

#### 3.1.4 Flared / bell-cast eave (concave curve)

```
section, ridge to the right; one column per step
                          S        <- top: steep stair-on-stair courses
                          S
                       S
                       S
                    S              <- middle: 45° stairs
                 S
              s t                  <- flare: slabs at 1:2 (bottom slab, then top slab one column in)
          s  s                     <- lip: two bottom slabs at the same height = flat kick
        i                          <- inverted stair under the lip (facing=<in>), or trapdoor soffit
```
* The flare covers the bottom 2–3 columns. The main slope is 45°, steepening to 63° in the top third for tall roofs.
* The **convex** (rounded, thatch-like) profile is the reverse: steep courses at the bottom (2 stacked), then 45°
  stairs, then slabs flattening at the top, then a rounded ridge of `*_wall` or slabs. Make the eave 1.5–2 blocks
  thick (a block row + inverted stair under it) to read as straw.
* **Upturned (kicked) corners**, as in East Asian roofs: lift the last 1–2 cells of each eave corner by a half or full
  block with a slab or an extra stair, so the hip line sweeps up at the tip.
* Kick the gable verge up 1 block at the ridge ends ("horned" tip) with an extra stair or a `*_wall` + `end_rod`
  spike. Reserve it for a few special buildings, not every one.

#### 3.1.5 Hip roof (top view, 9×7 footprint + 1 overhang)

```
roof footprint 11 x 9 (north at top)       v ^ > < = stair facing (direction it ascends = toward the ridge)
  o v v v v v v v v v o      ring 0 at E    o = corner stair; resolve turns it into outer_left/outer_right
  > o v v v v v v v o <      ring 1 at E+1  R = ridge cap at E+4 (block or slab), length = long - short + 1 = 3
  > > o v v v v v o < <      ring 2 at E+2
  > > > o v v v o < < <      ring 3 at E+3
  > > > > R R R < < < <      ring 4 = ridge
  > > > o ^ ^ ^ o < < <
  > > o ^ ^ ^ ^ ^ o < <
  > o ^ ^ ^ ^ ^ ^ ^ o <
  o ^ ^ ^ ^ ^ ^ ^ ^ ^ o
```
Read it as concentric rings. Ring *k* sits at `E+k` and every stair faces the centre line (north edge
`facing=south`, west edge `facing=east`, and so on). Corners resolve to `outer_*`. Use hips on pavilions, civic
buildings and wings. The look is calmer than gables, so a hip roof needs dormers, a cupola, flared eaves or upturned
corners to carry character.

**Round and octagonal roofs** use the ring metric `k = max(|dx|, |dz|, |dx|+|dz|-c)` around the centre (c = 2 in the
example builds; a larger c cuts smaller corners, c = 0 gives a diamond; see LESSONS.md §3). Every ring is then exactly one cell
wide and the hip lines are clean. Where two cells of a ring only touch diagonally, add a hidden helper stair in the
inner cell so `resolve` shapes the corner. Working code: `octk`/`cone_rings` in
`examples/builds/b03_fairy_flower_cottage.py` and `b04_mushroom_cottage.py`.

#### 3.1.6 Cross-gable and valleys (top view of an L-joint)

```
main ridge E-W at height H; wing (to the south) with ridge N-S at height H-2; one row = one stair course
   v v v v v v v v v v v v v      <- main north slope: stairs facing=south (toward the main ridge)
   R R R R R R R R R R R R R      <- main ridge, H
   ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^      <- main south slope, course H-1: facing=north
   ^ ^ ^ ^ ^ n R n ^ ^ ^ ^ ^      <- course H-2: wing ridge R dies into the main slope; n = valley cells
   ^ ^ ^ ^ n > R < n ^ ^ ^ ^      <- course H-3: valleys widen diagonally (inner_* shapes, resolved)
   ^ ^ ^ n > > R < < n ^ ^ ^      <- course H-4
           > > R < <              <- wing slopes: west half facing=east, east half facing=west
           > > R < <                 (wing eave at the main eave height = clean wrap)
```
* The wing ridge dies into the main slope. Where they cross, stairs get `inner_*` shapes. Optionally put a
  **contrasting block** in the valley line: a different material reads better than a sea of corner stairs.
* Keep the wing eave at the **same height** as the main eave (a clean wrap) or ≥ 2 lower (a clearly subordinate
  lean-to). Never 1 lower, which looks like a mistake.

#### 3.1.7 Catslide (asymmetric gable: one slope runs down over a lean-to)

```
                 R
              S  B  S
           S  B     B  S
        S  B           B  S     <- front: eave at g+6 (normal)
     S  B              W  i
  S  B   (lean-to)     W
  i  W                 W        <- back: the same 45° slope continues down to g+3
     W    pantry       W
  ###########################   plinth
```
The single unbroken slope is one of the most homely forms. Put a small shed dormer or a skylight row in the long
slope.

#### 3.1.8 Gambrel (barn, shop, mill cap)

The lower slope is 63° (stair-on-stair, 2–3 courses) and the upper slope is 45° or 26.5°. The knuckle is a log beam or
an inverted-stair row. Barn ends get a hay door with a hoist beam (`*_fence` arm + `iron_chain` + `hay_block`).

#### 3.1.9 Mansard and tower roofs

* **Mansard** (manor, town hall): a steep 63° lower roof with **dormers in every bay**, and a low hip or flat cap
  with a balustrade (`*_wall` + `*_fence`).
* **Pyramidal/conical tower roof:** a square or octagonal ring of stairs, 63° (a steep "witch hat" is 63° with a
  2-course flare at the base). For a round tower use the ring metric (§3.1.5): each ring traced in stairs facing the
  centre. Top it with a finial: `lightning_rod`, or `end_rod`, or `*_fence`×2 + `lantern` + `iron_chain`.
* **Bent witch hat:** offset the top 3–4 rings by 1 block sideways so the tip leans.
* **Flat roof with parapet:** a 1-high parapet of a slab or `*_wall` cap set flush or 1 proud, a thin fascia line
  (slab or stair course) at the roof edge, and a slight fall hidden behind the parapet. Used by modern and some
  desert styles; see the pack.

#### 3.1.10 Dormers and eyebrow windows

```
gable dormer front (3 wide)        section through the dormer             shed dormer (5 wide)
      s                              main roof slope →                       s s s s s   <- 26.5° slab roof
    S i S        <- dormer roof         S                                    L G G G L
  S i   i S         (45°, its own       B  S                                 L G G G L
  L  G  L        <- posts + glass      [L G L]  S   <- face set back ≥1 from the eave
  L  T  L        <- sill: trapdoor     main roof continues below
```
* A dormer is a **real gabled dormer** with its own slab ridge, or a deliberate shed dormer. Never a flat-lidded box
  or a log stub lying on the slope.
* The dormer ridge is ≥ 2 below the main ridge. The face is set back ≥ 1 from the main eave line (never flush with
  the wall below unless it is a wall dormer on purpose). Spacing is ≥ 3 between dormers, and at most 1 per 5–6
  blocks of slope.
* Vary dormers on a building: one gable dormer + one shed, or two gables of different widths.
* **Eyebrow window:** a 3-wide, 1-tall window low in the roof with the roof surface rising over it in a slab arch
  (`s s t s s` across the columns above the glass). Cheap and charming.

#### 3.1.11 Chimneys with real smoke

Mechanics (decompiled `CampfireBlock`, `CampfireBlockEntity`, `CampfireSmokeParticle`):
* A **lit** `campfire` (block-entity ticker) emits smoke particles that spawn 0–2 blocks above it and rise at about
  0.07 blocks/tick. "Cosy" smoke lives 80–129 ticks, so it is visible to about **6–9 blocks above the campfire**.
  With a `hay_block` directly **below** the campfire, `signal_fire=true` makes it live 280–329 ticks (≈ 20–23
  blocks). Reserve that for a watchtower or mill, if anywhere.
* Smoke particles **collide with blocks** (`hasPhysics`). Any block with a collision box above the campfire stops
  them, so the flue above a campfire must be **open air** all the way out.
* Campfires never spread fire. `fire` blocks do spread to flammable neighbours, so never place `fire`/`netherrack`
  fires in or near wooden builds.

Recipe:
```
section through a 3x3 stack (flue in the centre)         plan at the campfire level
   . . .      <- open sky                                  # # #
   i . i      <- crown: inverted stairs facing out          # C #     C = campfire[lit=true] (flue)
   # . #         (a corbelled lip), optional pots           # # #
   # C #      <- campfire 1 block below the rim: the flame is hidden, smoke pours out
   # B #      <- block under the campfire (stone; hay_block ONLY for a signal plume)
   # # #      <- stack continues down to the hearth
```
* Put the campfire **1–2 (max 3) blocks below the rim**, walled in on all sides, so the smoke clears the top and no
  flame shows from outside. Do not put the hearth campfire at the bottom of a 10-block flue and expect smoke on the
  roof: the shaft's own particles die inside. Use a **second campfire at the top**. The hearth campfire indoors is
  for the glow and crackle.
* The stack is slim above the roof (2×2 or 2×3) in the stone family or `bricks`/`mud_bricks`. It **tapers**: a wider
  base (3×2) at the ground with stair or slab "shoulders" stepping in above the eave. The top rises 1–2 above the
  ridge (ridge chimney) or ≥ 2 above the roof surface where it exits (slope chimney). Big 3×3 or 4×5 crowns read as
  boxes or hats.
* Finish with a rim and 1–2 pots (`decorated_pot`, `flower_pot`, or a short `*_wall` stub). Never stand a pot or
  carpet on a bottom slab: it floats half a block.
* Material: clean brick or a deliberate gradient (stone base → stepped course → brick). No random grey squares.
* An **exterior gable-end stack** (the stack stands outside the gable wall, poking 1 into it) is the most rustic.
  A **ridge stack** reads more "town house".

#### 3.1.12 Living roofs (moss, turf, flowers)

* The skeleton is a normal stair roof. On a roof that is *meant* to be green (turf, fairy, hobbit), cover 20–40% of
  the field in organic patches: `moss_carpet` on stairs, `moss_block` only where a full block belongs (ridge, flat
  tops), clumps of `azalea_leaves`/`flowering_azalea_leaves` (persistent) at the eaves and ridge.
* Plant on `moss_block` cells: `short_grass`, `fern`, `wildflowers`, `pink_petals`, and 1–2 tall flowers (`lilac`,
  `peony`) near the ridge. Moss is a valid substrate (`#supports_vegetation` includes `#moss_blocks`).
* Keep the eave and verge trim **wooden and continuous**. The green must sit inside a crisp frame or it looks like
  a hill.
* On normal roofs, weathering moss is `moss_carpet` only, on the lowest 1–2 courses of shady (north/east) slopes and
  valley feet, ≤ 10% of the slope. `moss_block` cubes inside a stair field read as holes.

#### 3.1.13 Thatch (bamboo/hay)

* The surface is `bamboo_mosaic_stairs`/`bamboo_mosaic_slab` (striated yellow) with some `bamboo_stairs`, using
  the **convex** profile (§3.1.4) and a 2-thick eave (`hay_block` row with `axis` along the eave, plus
  `bamboo_mosaic_slab` under it). The ridge is a `hay_block` roll (`axis` along the ridge) capped with `moss_carpet`
  in spots. Mix the second stair in runs, not per cell.
* Thatch eaves droop: give them overhang 2 at the corners and 1 mid-span (an irregular eave line).

#### 3.1.14 Roof field texture: calm field, weathered hem

* **One field material.** No single-course "repair strips" and no random speckle.
* **Weathering hem on the eaves only**, using a *same-value* neighbour block so it reads as weathering, not patches:
  course 1 at about 50%, course 2 at about 20%, in runs chosen with value noise stretched along the course; nothing
  above course 2.

  | field | hem |
  |---|---|
  | `deepslate_tile_stairs` | `deepslate_brick_stairs` |
  | `dark_oak_stairs` | `spruce_stairs` (lighter) or moss carpet only |
  | `spruce_stairs` | `dark_oak_stairs` at most 30%, course 1 only |
  | `cinnabar_brick_stairs` | `polished_cinnabar_stairs` |
  | `tuff_brick_stairs` | `polished_tuff_stairs` |

* Texture otherwise comes from the trim frame and the shadow lines. Check a render without shadows before calling
  something noise: sun shadows on a flat field make dark rectangles too. The worked example is
  `docs/examples/critiques/02_round2.md`, "Reusable roof recipe".

### 3.2 Walls

#### 3.2.1 Timber-frame grid (elevation, one storey, 9 wide)

```
 L  =  =  =  L  =  =  =  L       <- top plate: stripped log, axis along the wall (beam ends at corners L+1)
 L  W  W  W  L  W  G  W  L       <- posts every 4 (vary: 3 or 5 is fine; never all equal on long walls)
 L  W  /  W  L  W  G  W  L       <- brace '/' made of stairs (see 3.2.2) in one panel only
 L  /  W  W  L  W  T  W  L       <- window panel has sill (trapdoor/slab) at L+1
 L  =  =  =  L  =  =  =  L       <- sill plate/floor beam (stripped log), over the stone plinth
 #  #  #  #  #  #  #  #  #       <- plinth (g+1), weathering gradient
```
* **Posts** are logs `axis=y`. **Plates/beams** are stripped logs with `axis` along the wall. **Beam ends** stick
  out at corners and floor lines as a log with `axis=<out>` at L+1: a 1-block nub.
* **Proud frame (depth option A):** posts and plates sit at L+1 and infill at L0, so each wall is 2 thick at the
  frame. This gives the most depth. Use it on the main facade.
* **Flush frame (option B):** frame and infill are both at L0, and depth comes from sills, planters, jetties and
  window recesses. Use it on side and back walls.
* Do not put a frame member next to another parallel one. Where a window meets a post, the post *is* the window's
  jamb.

#### 3.2.2 Braces with stairs

```
3x3 panel, diagonal brace bottom-left to top-right:      "K" brace (two braces meeting at a mid post)
  W  W  S                                                  S  W  S'
  W  S  i      S = stair facing toward the brace's top      i  L  i'
  S  i  W      i = inverted stair filling the underside     L  L  L
```
* A brace is a pair: a bottom stair and an inverted stair below it in the next column, stepping diagonally. Use
  frame wood. In plaster panels the stair's open quarter shows plaster, which is fine and reads as a beam.
* Use one or two braced panels per facade (at corners or under a jetty), never all of them.

#### 3.2.3 Jetty (upper floor overhangs the lower)

```
section (outside to the right)
      W               <- upper wall at L+1 (one block further out)
      W
  =  =  i             <- floor beam row (stripped log) + inverted stair or log end at L+1 as joist tails
  W     i             <- optional: second corbel row on posts only (inverted stairs facing=<in>)
  W                   <- lower wall at L0
  ###                 <- plinth
```
* Jetty by 1 on the eave side or the gable end, or both (an inn can step out twice). The underside row is
  `dark_oak_stairs[half=top,facing=<in>]` all along (a cove) or only at posts (corbels), with joist ends
  (`stripped_*_log[axis=<out>]`) between them.
* Hang a `lantern[hanging=true]` from the jetty underside beside the door.

#### 3.2.4 Pent roof / skirt between floors

A single course of roof stairs (`facing=<in>`) at L+1 running around the building at the upper floor line, with an
inverted stair at L+1 below it at the posts. It casts a strong shadow line, breaks the H07 vertical run and is a
ready-made rain hood for the ground-floor windows.

#### 3.2.5 Infill choices

* **Plaster:** `pale_oak_planks`, `calcite`, `mushroom_stem`, `white_terracotta`, `smooth_sandstone` (warm). Shade
  darker downward (a worked gradient: `white_terracotta` low, `pale_oak_planks` mid, `calcite` high, chosen with
  value noise at scale 3–4 plus a height bias). `birch_planks` reads tan, i.e. as wood, not plaster.
* **Boards:** `stripped_spruce_log`/`stripped_oak_log` laid horizontally (`axis` along the wall), or vertical
  planks with an occasional `*_trapdoor[open=true,facing=<out>]` batten at L+1.
* **Brick nogging** (lower panels of a timber frame): `bricks` + `mud_bricks` + `packed_mud`.
* **Stone ground storey, timber upper storey:** the strongest two-material story. Put the band at the floor line
  and make the stone 1 thicker than the timber (the timber sits flush or is jettied).

#### 3.2.6 Stone walls

* Stone gradient per §2.2, with larger/smoother blocks (`stone_bricks`, `polished_andesite`) as **quoins** at the
  corners, alternating 1 and 2 long per course (a zipper of lighter blocks on each corner).
* **Buttresses** on stone walls longer than 7 blocks or on mills, forges and churches: 2 deep at the base, 1 deep
  from 2/3 of the height, capped with stairs. Place them at corners or every 4–6 blocks, irregularly.
* **Window and door heads** in stone walls:
  * **Straight:** a lintel course of a contrasting block (`polished_andesite`, `stone_bricks`) spanning the
    opening + 1 each side, with a drip hood of `stone_brick_stairs[half=top,facing=<out>]` at L+1 above it.
  * **Round head:** fill the opening's two top corner cells with inverted stairs whose `facing` points **toward
    the nearest jamb**. The lower quarter hugs the jamb, leaving a curved notch toward the centre. Put a keystone
    block above the middle.

#### 3.2.7 Foundations with a weathering gradient

```
elevation (bottom 3 courses)
  =  =  =  =  =  =  =  =  =  =      <- sill beam (timber) or first wall course
  #  c  #  #  b  #  #  #  c  #      g+1 visible plinth: stone 70% / cobble 20% / mossy 10%
  m  #  m  m  #  m  c  m  m  m      g   (and g-1): mossy-heavy 50%+ ; usually hidden by grass/moss carpet
  %  *  %     %     *  %  %         <- plants at g+1 outside: moss_carpet, short_grass, fern, flowers, bushes
```
* The plinth projects at L+1 relative to timber walls, or is flush on stone walls with a slab or stair "water
  table" ledge at L+1 on top: `stone_brick_stairs[facing=<in>]` running along the top of the plinth.
* At `g` (terrain level) put `moss_block`/`mossy_cobblestone` partly under the plinth face, plus a scatter of
  `coarse_dirt` and `rooted_dirt`. That is where the drip line would erode.
* Weathering variants go in runs of 2–5 along a course, not as single speckled cells.

### 3.3 Windows

**Every window recipe is "frame proud, glass back".** The glass (`glass_pane`) sits ≥ 1 block behind the outermost
frame block around it. Panes auto-connect (resolve handles it). For a 1-wide window, side panes simply attach to
the wall.

#### 3.3.1 Standard 1×2 or 2×2 window with shutters and sill

```
elevation (outside)                          section (outside to the right)
     i  i  i        <- lintel: inverted stairs facing=<out>       i       <- lintel/hood at L+1
  T  L  G  L  T     <- open trapdoor shutters (facing=<out>)  L  G       <- glass at L0 (or L-1 if the frame is at L0)
  T  L  G  L  T        at L+1 beside the jambs                L  G
     t  t  t        <- sill: trapdoor[half=top] or top slab   W  t       <- sill ledge at L+1
     *  *  *        <- optional planter (3.3.2) below sill
```
* Shutters: `spruce_trapdoor`/`dark_oak_trapdoor` (solid plank), `pale_oak_trapdoor` (white slats),
  `crimson_trapdoor` (plum slats), `warped_trapdoor` (teal), `acacia_trapdoor` (orange), `cherry_trapdoor` (pink
  lattice), `bamboo_trapdoor` (pale slats), or `copper_trapdoor` (X-braced; waxed forms keep their colour).
  **Vary them:** 2/1/0 shutters per window, about 20% with only one shutter or one closed flat over a blind spot, and
  attics get none. Pale trim on dark walls stops windows reading as black holes; on white plaster pale trim vanishes,
  so use a dark wood there.
* Window grilles: put an `oak_trapdoor` or `jungle_trapdoor` (they have window holes) standing vertical
  (`open=true,facing=<out>`) at L+1 directly in front of the glass, for a leaded-light look. Use them only on 1–2
  feature windows.

#### 3.3.2 Flower box

```
section (outside to the right)                  elevation
  G                                              T  *  *  *  T      <- end trapdoors (facing = left/right, away from box)
  W  t   <- sill (optional)                         D  D  D         D = planter soil: rooted_dirt / moss_block / coarse_dirt
  W  D  T   <- D at L+1, front trapdoor at L+2,     i     i         <- brackets: inverted stairs facing=<in> under the ends
  W  i       facing=<out> (hugs D's front face)
```
* Plant on `D`: 2 species + 1 filler, e.g. `poppy`, `azure_bluet`, `short_grass`. Pot alternative: a row of
  `potted_*` blocks on a top slab sill. For a bushy box, replace `D` and its flowers with
  `flowering_azalea_leaves[persistent=true]` and keep the front trapdoor.
* Use one box per facade on the main side and none on the back. Repeat the same species set across the building.

#### 3.3.3 Bay window (ground floor) and oriel (upper floor)

```
plan (outside down)                                elevation of an oriel
   W  W  W  W  W  W                                 S  S  S  S  S     <- small roof: stairs facing=<in> (+ slab ends)
   W  .  .  .  .  W  <- inside: window seat           L  G  G  G  L
      L  G  G  L     <- bay at L+1, 4 wide            L  G  G  G  L
      .  G  G  .         (corner posts are logs,       i  i  i  i  i     <- corbel row (inverted stairs facing=<in>)
                          side panes on the returns)      i     i        <- second corbel row under the posts only
```
* The bay projects 1 (max 2) and is 3–5 wide. It gets its own mini roof (a 26.5° slab roof or a stair course) and
  a plinth if it reaches the ground.
* Inside: a window seat (`*_stairs` facing into the room, or a `*_slab` with a `*_carpet` cushion) and 2 potted
  plants.

#### 3.3.4 Round and arched windows

```
3x3 "porthole" (glass in centre)    5x5 round window (rose window, gable feature)
   i  B  i                            .  i  B  i  .
   B  G  B     corner stairs:         i  i  G  i  i      inverted stairs on the upper ring, upright stairs
   S  B  S     facing = horizontally  B  G  G  G  B      on the lower ring; every corner stair's facing points
               AWAY from the centre   S  S  G  S  S      horizontally away from the window centre, so its open
               (the open notch then   .  S  B  S  .      notch faces the glass; B = frame blocks
               faces the glass)
```
Arched window: a 2-wide, 3-tall opening whose two top cells are inverted stairs with `facing` toward their own jamb
(a round head). Put a `*_slab[type=top]` keystone above it.

#### 3.3.5 Window rhythm

On each facade use **one large feature window** (3×2, a bay or a round one) + 1–3 standard windows + optional small
1×1 windows near stairs, pantries and attics. Space them by the room behind (not evenly). No window sits closer
than 1 block to an interior partition wall, so plan rooms first.

### 3.4 Doors, porches, balconies, awnings

#### 3.4.1 Door surround

```
elevation (3 wide surround, 1 wide door, outside)
  i  s  i       <- hood: stairs or slabs at L+1 on brackets (or a full porch roof)
  L  .  L       <- transom: glass_pane or a closed trapdoor at the top of the opening (door is 2 tall, opening 3)
  L  D  L       <- door (2 tall) at L0 or L-1 (recessed = better)
  L  D  L
  S  S  S       <- step: stairs facing=<in> at L+1 (floor is g+1, so one step up from ground)
```
* Doors: `spruce_door` (solid), `dark_oak_door` (solid, dark), `oak_door` (windowed), `jungle_door` (arched
  windows), `cherry_door` (pink), `mangrove_door` (red, ornate), `poplar_door` (greige, diamond window),
  `pale_oak_door` (white), `bamboo_door` (slatted), `birch_door` (pale, windowed), `iron_door`, `copper_door` (waxed
  forms keep their colour). Set `hinge` so the door swings against the near wall.
* Double doors: `hinge=left` + `hinge=right`, for inns, halls and temples.
* The entrance must be the obvious way in: a step, a lantern **beside** the transom (not in front of it), an
  accent-coloured door, ideally its own small roof. Beside the door: a potted plant or `decorated_pot`, and a bench
  or barrel. Keep it clear of clutter.

#### 3.4.2 Porch (3–5 wide, 2–3 deep)

```
plan                                   elevation
  W  W  D  W  W  W                       S  S  S  S  S      <- lean-to roof (stairs facing=<in>) or a cross-gable
  .  .  .  .  .  .  <- porch floor          L           L     <- posts: log or *_fence on a stone pier
  F  .  .  .  F                           F  .   .   .  F    <- railing: *_fence (gaps at the steps)
  L  F  .  F  L     <- posts at corners     #  S   S   S  #   <- piers + steps
     S  S  S        <- steps
```
* Floor: planks or top slabs at `g+1`, flush with the interior floor. The edge band is a stripped log. Railings are
  fences with a gap for the steps.
* Furnish it: a rocking chair (a stair with open trapdoors as arms), a `potted_*` or `decorated_pot`, a
  `lantern[hanging=true]` from the roof, and a firewood stack.
* A porch roof under the main eave can be a **catslide extension** of the main roof (a continuous slope) or a
  separate lean-to whose top tucks under the eave (≥ 1 below the eave stair).

#### 3.4.3 Balcony (upper floor)

* The floor is 1–2 deep at the upper floor level, made of `*_slab[type=top]` or planks. It is carried by inverted
  stairs as corbels under every other block, or by diagonal braces (stair pairs) down to the wall.
* Railing: `*_fence`, or trapdoors `open=true` on the outer edge (solid balustrade look), or `*_wall` for stone.
  Put a planter on the railing corners. Use a door or a full-height window for access.
* A gable-end balcony under the verge, with the roof's overhang deepened to 2 to shelter it, is very effective.

#### 3.4.4 Awnings

* **Striped fabric (wool stairs):** a course of `white_wool_stairs` alternating with `red_wool_stairs` (or
  `pink_`, `light_blue_`, `yellow_`) at L+1 above the shop window, `facing=<in>`. Add a valance of
  `*_wool_slab[type=top]` underneath at L+2 (an inverted wool stair at L+2 works too). The stripe width is 1. Hang
  the ends on fence brackets.
* **Timber hood:** a `*_stairs` course on inverted-stair brackets.
* **Canvas over a terrace:** wool slabs on `*_fence` posts (top slabs at post-top + 1) with an alternating stripe,
  and 1-block droops at the ends.

### 3.5 Lighting, signage, plant decor

#### 3.5.1 Exterior lights (all need a legal support; lantern support = sturdy centre above/below)

* **Wall bracket:** `*_fence` at L+1 on the wall (it connects to nothing, so it is a stub) with
  `lantern[hanging=true]` directly below it at L+1. Or `iron_chain[axis=y]` ×1 below the bracket, then the lantern.
* **Eave lantern:** an `iron_chain` 1–2 long hanging from the eave stair underside or a jetty, with a lantern.
* **Lamp post A (street):** a `cobblestone_wall` (g+1), `spruce_fence` ×2 (g+2, g+3), `spruce_fence` (g+4) + side
  arm `spruce_fence` (g+4, one block out) + `lantern[hanging=true]` under the arm at g+3. Put `moss_carpet` or
  `short_grass` at the base.
* **Lamp post B (garden):** a `stone_brick_wall` stub 1–2 high + `lantern[hanging=false]` on top. Or a
  `*_fence` + `copper_torch`/`torch`.
* **Candles** in windows: `candle[candles=2,lit=true]` (light 6) on the inner sill.
* **Spacing:** a light every 6–9 blocks along paths. Every door gets one.
* **Firefly bush** (`firefly_bush`, light 2) in garden corners gives evening particles, but it does not count as
  spawn-proofing.

Light levels (26.3 dump): `lantern`/`copper_lantern`/`glowstone`/`shroomlight`/froglights/`campfire`/`sea_lantern`
= 15. `torch`/`copper_torch`/`end_rod` = 14. `cave_vines[berries=true]` = 14. `soul_lantern`/`soul_campfire` = 10.
`glow_lichen` = 7. `enchanting_table` = 7. A candle gives 3 per candle when lit (max 12). `firefly_bush` = 2.
`furnace`/`smoker` are 13 only while burning; **a schematic furnace with `lit=true` will go out**, so do not count
it. `copper_lantern`, `copper_chain` and `copper_bars` weather over time; use the `waxed_*` variants to freeze
their colour.

#### 3.5.2 Signage (block entities exist but carry no text or patterns: the pipeline writes block states only)

* `*_wall_hanging_sign[facing=<left> or <right>]`: place it in the cell at L+1 in front of the wall. It hangs from
  a bracket attached to the block on its clockwise or counter-clockwise side (`WallHangingSignBlock.canPlace`), so
  `facing` runs **along** the wall and the board sticks out perpendicular to it like a classic shop sign. The
  alternative is a `*_hanging_sign` under a fence arm or beam (it needs a sturdy-centre block above). The blank board
  still reads as a shop sign. Put a symbol object next to it: a `cake` at a bakery, `anvil` + `grindstone` at a
  smithy, `lectern[has_book=true]` in a library window, `barrel`s at a tavern, `decorated_pot`s at a florist.
* Plain standing banners (`white_banner`, `red_banner`, …) on fence poles as flags, and `*_wall_banner` beside
  civic doors.

#### 3.5.3 Vines, leaves and moss on buildings (subtle)

* **Vines** (`vine`) in 1–3 places per facade only: down from a planter, beside a door, on a shady corner of the
  plinth. Each patch is 1–2 wide and 2–4 long. Vines need a full face to attach to, and further vine cells can
  hang below a supported vine on the same face. **Total ≤ 12% of the facade (H13).**
* **Leaf clumps** (`azalea_leaves[persistent=true]`) at outside corners of the plinth and under eaves at gable
  ends, 1–3 blocks each.
* `moss_carpet` on ledges, plinth tops and wall caps, in patches.
* For magical builds: glow-berry strands hanging 1–3 under eaves. Use `cave_vines_plant[berries=true]` for the
  upper segments and `cave_vines[berries=true]` for the lowest tip (vines grow downward, so the head is at the
  bottom). Each lit cell gives light 14. Use `pale_hanging_moss` (`tip=true` on the lowest) under gloomy eaves.
  Place `spore_blossom` under a balcony. Put `shelf_mushroom[facing=<out>]` on tree trunks and the plinth (it needs a
  sturdy face behind it).
* `glow_lichen` only in dark nooks, 1–2 faces.

---

## 4. Interiors

### 4.1 Room program and layout rules

* Plan rooms **before** placing windows. Enter into a living room, hall or shop, never directly into a bedroom.
  Kitchens adjoin the hearth wall. Stairs start near the entrance.
* Room minimums (interior clear): bedroom 4×4, small living room 5×5, kitchen 3×4, pantry 2×3, bathroom 2×3,
  library alcove 3×3, workshop 4×5.
* Family rooms connect through **open arches** (2–3 wide, with an inverted-stair top) rather than doors. Doors go
  only on bedrooms, pantries, bathrooms and exteriors.
* Clear heights: 3 (cosy) or 4 (main rooms). Attic rooms use the roof slope; keep 2 clear headroom over walkways.
* **Different materials** for walls, floor and ceiling (walls and ceiling may share if beams intervene).
* The interior is complete for the building's function: every item the program lists has a block-built answer.

### 4.2 Ceilings and floors

* **Beams:** a stripped log (`axis` across the short span) every 3–4 blocks, the ceiling plane between them in
  planks or top slabs. Add inverted stairs at the wall ends of each beam as brackets. Hang lanterns from beams.
* **Crown moulding:** inverted stairs (`facing=<into the wall>`) along the wall/ceiling junction in main rooms with
  clear height 4.
* **Attic:** the roof underside is visible as inverted stairs (rafters) every 2 columns with planks between, and a
  collar beam (log) at 2/3 height.
* **Floors:** a planks field with a 1-wide border of a darker wood, or alternating plank types in rows. Kitchens and
  workshops get stone (`polished_andesite`, `tuff_bricks`, `mud_bricks`, `stone_bricks`).
* **Rugs:** `*_carpet`, 3×4 to 5×6, with a 1-cell border in a second colour and 1–2 accent cells. They cover
  15–40% of a living room floor and are never wall to wall.

### 4.3 Furniture recipes (blocks only)

| piece | recipe |
|---|---|
| chair | `*_stairs` (back away from the table: `facing` = away from the table). Optional arms: `*_trapdoor[open=true]` on both sides facing away from the seat. |
| armchair/sofa | 2–3 `*_wool_stairs` in a row (upholstered) facing the back wall, arms of `*_trapdoor[open=true]` or wool slabs, a `*_wool_slab` footstool. |
| dining table | `*_fence` legs with a `*_pressure_plate` or `*_carpet` top (1×1). Long table: a row of `*_slab[type=top]` on fence legs at the ends. Or two inverted stairs back to back. Or `scaffolding[bottom=false,distance=0]` (looks like a small wooden table). |
| side/coffee table | `barrel[facing=up]`, or a top slab, with a `flower_pot`/`potted_*` or `candle` on it. |
| counter | full blocks (`barrel[facing=up]`, `stripped_oak_log`, `polished_andesite`) with `*_trapdoor[open=true,facing=<out of counter>]` doors on the front face. Mix a `smoker` and a `furnace` (`lit=false`) in the run, and add a `cauldron`/`water_cauldron[level=3]` sink with a `lever[face=wall]` or `tripwire_hook` above as the tap. |
| hob/stove | `smoker` + `campfire[lit=false]` or a `*_carpet` on top; hood: inverted stairs + `bricks` chimney above. |
| range in a hearth | an inglenook: a 3-wide, 3-tall brick recess with `campfire[lit=true]` on the hearth floor, `iron_chain` + `lantern` hanging inside, and a mantel of inverted stairs + slabs with `candle`s and `decorated_pot`s. |
| wall shelf | the `*_shelf` blocks (`oak_shelf[facing=<into room>]`): put 2–4 side by side on walls above counters and desks. Otherwise `*_trapdoor[half=top]` plates with pots and candles on them. |
| bookcase wall | `bookshelf` + `chiseled_bookshelf` with **varied** `slot_N_occupied` states (some gaps) + `*_shelf`. Never a solid wall of identical bookshelves: break it every 3 with a post, a lantern niche or a window. |
| bed | vanilla beds (`red_bed`, `white_bed`, …) or the rustic `straw_bed`. Canopy: `*_fence` posts at the corners, 2 high, with a `*_wool_slab[type=top]` or carpet canopy. |
| bed nook | a bed in a 3-wide alcove under the roof slope, with a `*_shelf` above the head and a `lantern` or `candle` on a `chiseled_bookshelf` nightstand. |
| nightstand/dresser | `barrel` or `chiseled_bookshelf` (1–2 slots occupied), a top with a `flower_pot`. Dresser: 2–3 `barrel`s with trapdoor fronts. |
| wardrobe | 2 tall: `*_planks` + a front of `*_door` (closed, hinge in), or stacked `barrel`s with trapdoors. |
| pantry | `barrel` (mixed facings), `hay_block`, `dried_kelp_block`, `pumpkin`, `melon`, `composter`, `decorated_pot`, a single `honeycomb_block` or `honey_block` as a "jar". |
| workshop | `crafting_table`, `smithing_table`, `fletching_table`, `loom`, `cartography_table`, `stonecutter`, `grindstone[face=floor]`, tool wall = `*_shelf` + `lightning_rod` hooks. |
| library | `lectern[has_book=true]`, `chiseled_bookshelf`, reading chair, `candle`s, a globe-ish `decorated_pot`, a `ladder` on a tall shelf wall. |
| bathroom | tub: a 1×2 recess with `water` (source) edged by `smooth_quartz_slab`/`white_concrete_slab[type=top]`, or a `water_cauldron[level=3]`. Basin: `cauldron` + `tripwire_hook` tap. Mirror: `glass_pane` framed by `*_trapdoor`s. Towel rail: `iron_chain[axis=x]` between two blocks. |
| chandelier | from a ceiling beam: `iron_chain` ×1–2, then a ring of 4 `*_trapdoor[half=top]` or `*_fence` around a centre chain, with `lantern`s or lit `candle`s on the ring. |

### 4.4 Lighting interiors (H15)

* Overworld hostile mobs spawn only at block light 0 (26.3 `monster_spawn_block_light_limit = 0`), so **every**
  floor cell must have block light ≥ 1. A lantern (15) lights every cell within Manhattan distance ≤ 14 through
  air. In practice: ≥ 1 light of level ≥ 12 per room, and no floor cell more than 10 steps (Manhattan, through the
  room) from a light. Attics and cellars count as rooms.
* Mix types: a hanging lantern (ambient), candles (tables, sills, mantel), a hearth campfire (focal). A light under
  a carpet works (`glowstone` or a froglight under `*_carpet` lights the room): carpets do not use their shape for
  light occlusion (`CarpetBlock` does not override `useShapeForLightOcclusion`), so this is good for floors that
  need extra light without visible fixtures.
* No exposed glowstone ceilings; hide strong sources behind beams, in lanterns or under carpet.

### 4.5 Circulation and stairs (H16)

* Keep the 1×2 cells in front of and behind every door free of furniture. Carpet is fine.
* Walkways: 2 wide in rooms ≥ 9 wide, 1 wide in small cottages. Keep a 1-wide clear lane along beds and counters.
* **Straight stair:** rise 4–5 per storey, so 4–5 stairs + a landing. Cut the ceiling opening so every step has
  ≥ 2 air above it. Put a railing (`*_fence` or trapdoors) on the open side.
* **L-stair with landing:** a quarter landing (1×1 or 2×2 full block/slab) at mid height. It fits a 3×4 corner.
* **Spiral stair (3×3 around a 1×1 log or fence core):** step around the core with slabs alternating `bottom`/`top`
  (half-block rise per cell) or stairs on the corners, making 8 cells per loop = 4 blocks rise. It needs a 3×3
  shaft open between floors. Use it for towers.
* **Ladder:** `ladder[facing=<out from the wall it hangs on>]` in tight spots (attic hatch, mill, lookout). The top
  opening is an `*_trapdoor[open=true]` hatch.

---

## 5. Landscaping

### 5.0 Substrate and survival rules (26.3 tags)

* Small and tall flowers, `short_grass`, `fern`, `bush`, `firefly_bush`, `wildflowers`, `pink_petals`, saplings
  and `sweet_berry_bush` need a block in `#supports_vegetation` below: `dirt`, `coarse_dirt`, `rooted_dirt`,
  `grass_block`, `podzol`, `mycelium`, `moss_block`, `pale_moss_block`, `mud`, `muddy_mangrove_roots`, `farmland`.
  **Not** `dirt_path`, `gravel` or stone.
* `red_mushroom`/`brown_mushroom` survive in any light on `podzol`/`mycelium` (tag
  `#overrides_mushroom_light_requirement`). On anything else they need a solid opaque block below **and** raw
  light < 13, which fails in daylight, so they pop off. Put outdoor mushrooms on `podzol`.
* `short_dry_grass`/`tall_dry_grass` also accept sand and terracotta. `azalea`/`flowering_azalea` also accept
  `clay`.
* `leaf_litter` needs a **sturdy top face** below (grass, dirt, cobble, planks). It does not work on `dirt_path`
  (not full height) or slabs.
* `cactus_flower` needs a sturdy top or `cactus`/`farmland`. Crops need `farmland`. Farmland only stays farmland
  with a crop on it or water within 4 blocks.
* `lily_pad` on a water surface. `sugar_cane` on dirt, grass or sand **with water adjacent** to that block.
  `seagrass` in water.
* Leaves: always `persistent=true` (otherwise they decay without a log within 6). `resolve` forces it anyway.
* `shelf_mushroom[facing=<out>]` needs a sturdy face behind it. `pale_hanging_moss` and `cave_vines` need a full
  face above.

### 5.1 Paths

* **Width:** main street/spine 3 (varying 2–4), house paths 1–2, garden stepping stones 1.
* **Gradient, centre to edge** (all at `g`, replacing grass): `dirt_path` (core, 60% of the centre) → `coarse_dirt`
  / `rooted_dirt` / `packed_mud` speckle (centre edge and worn spots) → edge band of `podzol`, `coarse_dirt` and
  `gravel` (1 cell, broken) → grass with `short_grass` and `leaf_litter` (on full blocks only) → normal grass.
  Optional mossy edge: `moss_block` with a `moss_carpet` tuft at g+1. Keep the core one continuous worn path; the
  speckle belongs on its edges only.
* **Edges are never straight:** jog the edge by ±1 every 2–5 blocks, and never more than 7 blocks straight. Bulge at
  junctions, doors and benches. Let grass and flowers creep into the edge.
* **Stone paths** (squares, formal approaches): `cobblestone` + `stone_bricks` + `andesite` + `mossy_cobblestone`,
  with grass gaps and dirt-path seams near the edges (a dissolving edge).
* **Stepping stones:** 1-cell `polished_andesite`/`tuff`/`stone` at `g` with grass between, or `*_slab` at `g+1` on
  top of grass (raised stones), staggered left and right.
* **Steps on slopes:** stairs or slabs following the terrain. Never cut a flat platform.

### 5.2 Flower beds and borders

* Beds have organic outlines (kidney or teardrop), 2–4 deep, with a soil border of `coarse_dirt`/`rooted_dirt`
  cells at `g` and flowers at `g+1`.
* **Planting density:** 60–80% of bed cells planted, the rest grass, fern or empty soil. Cluster each species in
  drifts of 3–7. Tall (`peony`, `lilac`, `rose_bush`, `sunflower`, `pitcher_plant`) at the back against the wall,
  medium in the middle, low (`pink_petals`, `wildflowers`, `azure_bluet`) at the front.
* Colour in drifts, and not only white/yellow: the pinks, blues and purples carry far better in renders.
* Along the plinth: a 1–2 deep strip of mixed `short_grass`, `fern`, `bush` and the building's flower theme, broken
  by an `azalea`/`flowering_azalea` shrub every 4–6 blocks.

### 5.3 Custom bushes (side and top view)

```
small (1-2 tall)          medium (2-3 tall, 3x3 base)          hedge segment (topiary)
   %                         . % .                              % % % % %     <- top layer missing 1-2 cells
  %F%    F = *_fence/log     % % %    + 1-2 flowering             % % % % %
  ...    core (optional)    %%F%%      azalea leaves mixed       % % % % %     <- cobble wall/stone edge at g+1
                             % % %
```
* Use `azalea_leaves` 60% + `oak_leaves` 30% + `flowering_azalea_leaves` 10% (persistent). Put the `azalea`/
  `flowering_azalea` *block* (a small shrub with a leafy top) at the edges.
* Shapes are irregular blobs: remove 1–3 corner cells per layer and add 1 bump cell. No two bushes are identical
  (seed noise per bush). Never 2×2×2 cubes.
* At the base: `moss_carpet`, `fern`, `short_grass`.

### 5.4 Custom trees (persistent leaves, trunks with branches)

General: branches leave the trunk at **different heights**. Leaves cluster at branch ends, not on the trunk. The
canopy is a dome or umbrella, widest at the branch level and tapering upward, with an irregular edge, cut corners and
a lighter underside. Roots flare at the base. Use stairs and slabs to thicken bends, and fences as twigs. Logs must
touch face to face (QA's floating check), limb tips hide inside leaves, and canopies keep ≥ 2 air from any roof. See
LESSONS.md §5 and the worked tree in `examples/builds/b03_fairy_flower_cottage.py`.

**T1 · Small orchard/oak (height 6–8, canopy 5–7)**
```
side view
      % % %
    % % % % %
   % % L % % %       L = oak_log (axis=y), branches oak_log axis=x/z 1-2 long
    % L % L %        at y+3 (left, short) and y+4 (right, longer)
      L L            % = oak_leaves 70% + azalea_leaves 30% (fruit tree: +10% flowering_azalea_leaves)
       L
     s L S           <- root flare: stairs/slabs of oak around the base, rooted_dirt/coarse_dirt at g
```

**T2 · Autumn poplar (columnar form; height 10–14, canopy 3–5)**
```
       %
      %%%           % = yellow_poplar_leaves 60% / orange_poplar_leaves 30% / red_poplar_leaves 10%
      %%%               (colour bands: yellow top, orange mid, a few red low on the sun side)
     %%L%%          L = poplar_log, 1x1, up to 2 below the top; tiny side branches (poplar_fence)
     %%L%%
     %%L%%          canopy: 3x3 core, 5-wide bulges at 1-2 levels, egg-shaped, tallest part 2/3 up
      %L%
       L
       L            leaf_litter (segment_amount 2-4, varied facing) on the grass in a 3-radius ring
```

**T3 · Birch with gold leaves:** a `birch_log` trunk (1×1, slight kink via a 1-block offset at 2/3 height), canopy
`yellow_poplar_leaves` + `birch_leaves`, rounded and 5–7 wide.

**T4 · Cherry blossom:** a `cherry_log` trunk leaning 1 block, 2–3 long horizontal branches (`cherry_log`
`axis=x/z`, `cherry_wood` at joints), a wide flat canopy (7–9 wide, 3–4 tall) of `cherry_leaves` with
`flowering_azalea_leaves` 5%, and `pink_petals` (`flower_amount` 1–4) carpet underneath.

**T5 · Willow by water:** an `oak_log`/`mangrove_log` trunk leaning toward the water, a dome of `oak_leaves` and
`azalea_leaves`, and **curtains** of `vine` hanging 2–4 below the leaf edges (vines attach to the leaf side faces,
then continue below on the same face).

**T6 · Gnarled pale oak:** `pale_oak_log` 2×2 base tapering to 1×1, crooked offsets, `pale_oak_leaves` canopy,
`pale_hanging_moss` drapes, `shelf_mushroom` on the trunk, and `pale_moss_carpet` at the base.

**T7 · Big landmark tree (square, manor):** a 2×2 → 1×1 `dark_oak_log`/`oak_log` trunk, `mangrove_roots` and
`rooted_dirt` flare, 3–4 major branches at 3 heights, and a multi-lobed canopy 11–15 wide. Add a bench ring around
it.

**T9 · Weeping umbrella (battle-tested):** a tapering trunk tube along a leaning polyline (a 6-connected core walk
guarantees face contact; radius ≥ 0.6 gives a 2-wide band that reads as a smooth lean), 3–4 limbs from one split, a
canopy built as a union of domed ellipsoids with value-noise roughness, and 1–3-long drips hanging from the rim only.
Full numbers: `docs/examples/critiques/03_round2.md` §2.

Placement: trees overlap the building's roof edge or corner (they frame it), are never in a grid, and come in
odd-numbered groups (1, 3, 5) of different sizes. Avoid "bookend" trees mirrored either side of the front.

### 5.5 Fences, gates, low walls

* Fences: posts 1 high, with **gaps and breaks** (a missing segment, a leaning post replaced by a `*_wall` stub). A
  fence gate at each path crossing, sometimes `open=true`. Keep posts bare. Lanterns go only on gate posts, and
  climbing plants are allowed on 1 in 5 posts (a `vine` cannot hang on a fence, so use an `azalea_leaves` tuft on
  top).
* Low stone walls: `cobblestone_wall` + `mossy_cobblestone_wall` (60/40), 1 high. Every 3–5 cells raise a post
  (`up=true` is resolved automatically when a wall ends or turns). Cap posts with moss carpet or a lantern at the
  gate. Let walls end in a broken step-down, not a clean stop.
* Hedges (§5.3) as an alternative boundary for formal buildings.

### 5.6 Garden props

| prop | recipe |
|---|---|
| bench | 2–3 `*_stairs` facing away from the view (the back is the stair's tall part), with `*_trapdoor[open=true]` armrests on the ends. Or a `*_slab` seat on `*_fence` legs. |
| well | a 3×3 (or round 5×5) ring of `cobblestone`/`mossy_cobblestone` 1–2 high around a 1×1 or 3×3 water shaft (`water` at g-1…g-3, `mossy_cobblestone` bottom). Two `*_log` posts on opposite sides, 3 high, a cross beam (log `axis` across), a small gable roof of stairs, and `iron_chain[axis=y]` hanging from the beam, ending 1 above the water. Add `moss_carpet` on the rim and a `*_trapdoor` lid half open. |
| woodpile | `*_log[axis=x or z]` stacked 2–3 high, 3–5 long, against a wall under a 1-deep lean-to (stairs on fence posts). Mix in 2 log types. Chopping block: `stripped_oak_log[axis=y]` with a `lever[face=floor]` on top as the axe handle. |
| cart | body: 2×3 `spruce_slab[type=top]` (or `barrel`s) at g+2, wheels: `grindstone[face=wall,facing=<out>]` on both sides at g+1, a `spruce_fence` handle, load: `hay_block`, `pumpkin`, `barrel`, `composter`. |
| beehives | `beehive[facing=…]` on a `*_fence` post or a stone pier, 2–3 in a row in a flower meadow, a `bee_nest` on one tree. |
| laundry line | two `*_fence` posts 3 high, a line of `*_fence` between the tops (it auto-connects) or `iron_chain[axis=x/z]`, "sheets" of `white_carpet`/`light_blue_carpet` laid on the fence line, and `*_trapdoor[half=top,open=true]` hanging below as cloth. Keep it to 3–5 long. |
| compost & tools | `composter[level=4..8]`, a `barrel`, `scaffolding` as a potting bench, `*_trapdoor` tool rack. |
| pond | an irregular, bean-shaped outline 3–9 across, 1–2 deep: `water` at g (and g-1 in the middle), a bottom of `clay`/`dirt`/`gravel` (gravity: `gravel` must sit on a block), banks of `coarse_dirt`/`mud`/`moss_block`/`mossy_cobblestone` boulders with no bare dirt showing, and `lily_pad` (on water), `sugar_cane` (on the bank, water adjacent), `seagrass`, `small_dripleaf`/`big_dripleaf` at the edge. Contain water: every water cell's horizontal and lower neighbours must be water or a solid block **placed in the schematic** (otherwise it flows). Do not rely on unset cells being terrain at the pond rim. |
| stream/race | 1–2 wide `water` channel at g with stone or mossy edges. Flowing water from a source must stay inside the schematic. |
| scarecrow | `*_fence` 2 high, `hay_block` body, a `carved_pumpkin` head, and `*_trapdoor[open=true]` arms. |
| crop beds | `farmland[moisture=7]` rows with crops at max age: `wheat[age=7]`, `carrots[age=7]`, `potatoes[age=7]`, `beetroots[age=3]`. `water` channels every 9 cells (hydrates 4 each way). Add `pumpkin`/`melon` with `attached_*_stem` beside them. |
| market stall | 2×3 counter of `barrel`s, a wool-slab canopy on `*_fence` posts, crates (`barrel`, `composter`), `decorated_pot`s. |

### 5.7 Fading into the terrain (no platforms)

* The landscaping outline is the union of 3–6 overlapping irregular blobs (path, beds, yard, trees), never the
  bounding box. Cells outside the blobs are **unset**, so the natural world shows through.
* Fade intensity outward over 3–6 blocks. Ring 0 (at the walls) gets dense planting and paths. Ring 1 gets beds,
  bushes and props. Ring 2 gets scattered single flowers, grass tufts, a few `leaf_litter`, coarse-dirt specks and a
  lone stone. Ring 3 is natural.
* Terrain shaping inside the footprint: use full `grass_block` over `dirt` mounds (1–2 high) with organic outlines
  and plants. There are no grass slabs, so never fake slopes with wood or stone slabs in the lawn. Double-layer any
  raised terrain (dirt under grass) so no holes show.
* On slopes: terrace with low stone retaining walls (`cobblestone`/`mossy_cobblestone`, irregular top, stairs to
  soften) and stair paths.

---

## 6. Anti-patterns (instant rejection)

1. A single rectangular box with a single gable or hip roof. Also *two* identical boxes stuck together.
2. A roof without overhang, without a verge trim, or a one-layer stair roof with visible undersides.
3. A roof in the same value and family as the walls (a wood roof over mostly-wood walls).
4. A floor at ground level, no plinth, a door opening straight onto grass with no step.
5. A wall that is one material, flat, and windows evenly spaced along it like a spreadsheet.
6. Windows flush with the wall surface (glass in the same plane as the frame).
7. Shutters, planters and lanterns on *every* window. Repetition without variation.
8. Per-block speckle noise in roofs, walls, chimneys or towers.
9. Vines or leaves sprayed over whole walls. Moss on every roof. `moss_block` cubes inside a stair field.
10. Perfect bilateral symmetry of the entire building (formal buildings may centre a core, but the wings or setting
    differ).
11. Square or rectangular "landscaping pads", paths drawn with a ruler, the path material stopping at a hard line,
    or flowers in a single row.
12. Nine flower species in one bed. Rainbow beds anywhere except a florist.
13. Lollipop trees (a 1-high trunk under a perfect sphere or cube of leaves), flat stacked leaf layers, identical
    copies of one tree, trees planted on a grid.
14. Torches on walls everywhere. Exposed glowstone as a ceiling. Lanterns every 2 blocks.
15. Empty rooms, or rooms crammed so you cannot walk. Furniture blocking doors. A bed against a window.
16. Every storey the same height with the same window pattern stacked (no jetty, band or variation).
17. Even spans with a messy ridge. Corner-stair spaghetti at valleys (use a contrasting valley line). "Wedding cake"
    plank risers on steep roofs. Log ridges.
18. A chimney that does not reach above the roof, a fat crown, or a campfire buried 10 blocks deep "for smoke" (no
    smoke reaches the top).
19. Leaves with `persistent=false`, crops on grass, flowers on dirt paths, floating gravel, uncontained water.
20. Entities (item frames, paintings, armour stands) or relying on sign text, banner patterns, chest contents or
    pot sherds. None of these survive the block-only pipeline.
21. Making a building more "fantasy" by adding random colour. Use colour as an accent (shutters, awning, flowers),
    while structure stays in natural woods and stones.
22. A build that would look the same with its landscaping deleted. The landscaping is part of the composition.

---

## 7. Builder workflow (recommended order)

1. Read the brief, LESSONS.md and the style pack. Sketch the top view and **two elevations** in ASCII in the script
   docstring and in your log.
2. Volumes: main + subordinates (H01, H02). Fix spans (odd), storey heights and the ground line.
3. Roofs, highest first, with verge, eave and ridge trims. Add chimneys (with smoke physics), dormers, finials.
   Render with `--quick` and look at all four iso views before going on.
4. Walls: frame grid → infill gradient → plinth gradient → window and door surrounds → jetty, pent roof, bays.
   Measure the light-material share per elevation (LESSONS.md §1).
5. Facade details: shutters (varied), planters (1–2), lights, signage, vines (subtle).
6. Interior: floors, ceilings, beams, stairs, furniture per room, lighting check (H15).
7. Landscaping: paths (gradient, organic), beds, bushes, trees, props, fade-out rings (H14).
8. Run QA, look at the renders (squint, shadow, story, edge, restraint), and iterate. Write any soft-rule
   exceptions into `meta["notes"]`.
