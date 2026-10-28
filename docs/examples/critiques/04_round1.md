# 04 Woodland Mushroom Cottage ("Toadstool Hollow"): critique round 1

**Coordinates.** All coordinates are **schematic** coordinates, unless marked *plan*.
Schematic = plan (the coordinates in `builds/b04_mushroom_cottage.py`) + **(13, 1, 11)**. The stem axis is x=13, z=11 and the ground is y=1.

**Prototypes.** The scratch prototypes are in `tmp/critic04/`:
- `h.py`: the harness;
- `cap.py`, `brown.py`, `stem.py`: the three prototypes;
- `sheet.py`: the comparison-sheet maker.

None of them touches the build script. All three prototypes stacked: **QA 0 errors, 0 warnings.**

## 1. Scores

| category | score | note |
|---|---|---|
| Silhouette / massing | **8** | An unmistakable toadstool. The tapering stem with a shoulder, the layered brown caps and the lamp toadstool make a real hierarchy. |
| Roof (cap) construction | **4** | Full-block terraces 1 ring wide and 1 high. That gives a ziggurat profile in elevation and saw-teeth on every diagonal. The 2-thick rim is a vertical red curtain. |
| Secondary caps | **4** | The pantry and porch caps are two stacked flat discs. They read as plates, not caps. |
| Materials / contrast | **6** | Red over cream is great contrast. But the grey polished-diorite shoulder band reads as a castle cornice, and the stem is one flat cream colour. |
| Facade depth / detail | **6** | Shelf mushrooms, shutters, sills and the teal door are good. The stem bays between them are flat cream panels. |
| Chimney | **4** | A 2×2 grey column about 19 tall, standing proud of the north face, with a 3×3 crenellated crown. That breaks lesson 4 ("3×3 crowns read as boxes/hats"). It reads like a castle turret bolted on. |
| Interior | **6** | Every room has a focal piece: the main room has the hearth, toadstool table, bay seat and shelves; the pantry has a smoker, cauldron and chests; the loft has a bed, chest and nightstand. The loft and pantry are thin. |
| Landscaping | **6** | Good species choice and the woodland-floor idea is right. But the podzol/coarse dirt is scattered as 1–2-cell squares (a checkerboard in `top`). The path is a 1-wide sunken dog-leg. Some bushes are boxy. |
| Story / charm | **8** | It clearly belongs to a forest gnome. The teal door, glow berries, fallen log bench and toadstool lamp all help. |
| **Overall** | **6.0** | With the three prototypes applied, I would put it at about **7.0**. With the chimney and landscaping fixes added, about **7.5**. |

## 2. Blockers (block-level fixes)

### B1. The red cap is stepped full blocks
Today it is a ziggurat with saw-tooth diagonals. The cap columns cover x 5..21, z 3..19, with tops at y13..17.

**Fix (prototyped, P1).** Every top cell of a cap column that has a lower (or no) 4-neighbour becomes `red_wool_stairs[half=bottom]`. Its facing points to the higher neighbour, the one opposite a lower side, preferring the direction toward the stem axis. An isolated peak becomes `red_wool_slab[type=bottom]`. That is 130 cells. With rings 1 wide, this turns the whole flank into a continuous 45° stair slope, and `blockwright.resolve` shapes the diagonal corners.

Recolour the adjacent faces: a full `red_mushroom_block` next to a new stair gets that face set to `true` (red skin), otherwise beige pore faces show through.

### B2. The warts are white carpets on terrace noses
After the chamfer they would float or sit on stairs. **Fix (P1b).** On a nose cell, delete the carpet and make the cell a `white_wool_stairs` with the same facing, so the wart is flush and follows the profile. Keep the carpets only on plateau cells.

### B3. The brown pantry and porch caps are flat two-tier plates
- Pantry cap: plate y7 / crown y8, centre about (22, 12).
- Porch cap: plate y6 at x11..15, z17..19, crown y7 at x12..14, z17.

**Fix (prototyped, P2).** Every edge top cell becomes `brown_wool_stairs[half=bottom]`, facing inward. That covers both the plate rim and the crown nose. On the porch, the crown row is forced to `facing=north`, leaning on the wall. Without that it turns into a three-tooth battlement.

Add a **curled lip**. Under each outermost cell, where that cell and the one below are air and the inner neighbour is air, place `brown_wool_stairs[half=top]` facing inward, one block below the cap underside (pantry y6, porch y5). Then recolour the faces as in B1. That is 57 cells in total.

### B4. The chimney is a plain grey column with a 3×3 crenellated crown
- Stack: x11..12, z4..5, y0..16.
- West footing: x10, z4..5, y0..5, with a tuff stair at y6.
- Crown: x11..13, z3..5, y16..18.
- Pot: (13, 19, 3).

**Fix (recipe, not prototyped).**
- Remove the 3×3 crown ring at y17..18 and keep the stack 2×2.
- Make it **crooked**: at y14..15, shift the upper 2×2 one block north (z3..4). Carry the shift with `tuff_brick_stairs[half=top]` corbels on the north face at y13, and `tuff_brick_stairs[half=bottom,facing=north]` steps on the south side at y14.
- Rim: `polished_tuff_slab[type=top]` rim around the flue mouth at y16.
- Pots: `decorated_pot` on one corner plus a `flower_pot` on the opposite corner, both on full blocks.
- Fire: put the campfire one below the rim, walled on 3 sides by the stack and on the fourth by a `tuff_brick_wall`. Leave the sky above open.
- Gradient below the cap: y0..3 `mossy_cobblestone`/`cobbled_deepslate`, then a stepped course of `tuff_stairs` (outward) at y4, then `tuff` y5..9, then `tuff_bricks` above the cap. Run it in courses, not speckle.
- Battered foot: widen the north face at y1..2 (z3) with `tuff_stairs[facing=south]`. This partly exists already.
- Drop ivy from y10..13 on the north face, but only on the 1 column already there.

### B5. The polished-diorite shoulder reads as a grey castle cornice
The shoulder is the ring max(|dx|,|dz|,|dx|+|dz|-2)=5 around (13,11), at y8. **Fix (prototyped, P3).** Swap every `polished_diorite_stairs` (same facing/half) for `pale_oak_stairs`. It becomes a soft cream annulus with a fine grain, and the shadow line stays.

## 3. Top 6 improvements (by impact)

1. **Chamfer the red cap with `red_wool_stairs`** (B1). This is the biggest single gain: the ziggurat becomes a dome. Red wool (L75) is a little darker than the mushroom block (L93). It reads as ring shading, which helps the curvature.
2. **Round and curl the brown caps with `brown_wool_stairs`** (B3). It gives a toasted-bun dome with a dark curled gill edge. I picked brown wool over mud brick (reads as a brick roof) and granite (speckle); see `cmp_brown_mats.png`. It also matches the wool language of the red cap.
3. **Flush white wool-stair warts** (B2). The amanita spots finally read from the elevations, and nothing floats.
4. **Rebuild the chimney top** (B4): crooked 2×2, slab rim, 2 pots, a deliberate course gradient, no 3×3 crown.
5. **Make the stem a stem.**
   - Use the pale-oak annulus (B5, done).
   - Add a drooping skirt: `pale_oak_stairs[half=top]` on ring 6 at y7, facing the stem, where the cell and the one below are free. Only 10 cells qualified, so it is weak.
   - **Stronger, not prototyped:** add vertical relief on the ground storey. In every 3rd–4th stem bay between windows, set a 1-wide pilaster of `mushroom_stem` at L+1 for y3..6. Cap it with a `pale_oak_stairs[half=top]` bracket under the shoulder. These are the stem's "fibre ribs". They break the flat cream panels (QA flags an 18-cell flat `mushroom_stem` patch on the W facade).
   - I also prototyped `stripped_pale_oak_log` vertical streaks. They are too close in tone to show; drop them.
6. **Landscaping cleanup.**
   - Merge the scattered 1–2-cell podzol/coarse-dirt squares into 2–3 bean-shaped drifts under the birch pair (NW, about x2..8, z0..8) and the spruce (NE, about x24..28, z2..8). Fade the edges with moss_carpet and leaf_litter, not lone squares.
   - Widen the path to 2 at the porch step (z20..21). Give it stepping-stone edges (`mossy_cobblestone_slab`/`tuff_slab` on the grass) instead of a 1-wide sunken `dirt_path` strip.
   - Reshape the 2×3 boxy bushes SE of the porch so their corners are cut.
   - Round the **toadstool lamp** cap: today it is a flat 3×3 square plus a cube at x6..8, z19..21, y5, top (7, 6, 20). Turn the four corners into `red_wool_stairs[half=bottom]` facing the centre and the top cube into `red_wool_slab`.
   - Smaller:
     - The loft needs one more piece, such as a bookshelf nook or a rug under the bed.
     - The pantry wants a hanging-herb rack (`iron_chain` + `potted` or `hay` bundles) so it reads as a kitchen.

## 4. Prototype recipes and comparison images

Run order: `python tmp/critic04/cap.py`, then `brown.py`, then `stem.py`. Each script re-applies the previous steps.

**P1: red cap chamfer** (`tmp/critic04/cap.py`, `chamfer(P, "red_wool", warts_flush=True)`)
- Cap columns = `red_mushroom_block` cells with plan y≥9 and |x|,|z|≤8. Column top T(x,z) = the highest such cell.
- If a top cell has leaf litter or chimney above it: skip.
- If any 4-neighbour T is lower (or there is no cap):
  - with no higher neighbour, it becomes `red_wool_slab[type=bottom]`;
  - otherwise it becomes `red_wool_stairs[facing=F,half=bottom]`. F is a higher-side neighbour whose opposite side is lower, with the tie broken toward the stem axis.
- A wart carpet on such a cell is removed, and the cell becomes `white_wool_stairs[facing=F]` instead.
- `repaint()`: each face of a `red_mushroom_block` that touches a new stair or slab is set to `true`.
- Result: 130 cells changed, QA 0/0.

**P2: brown caps** (`tmp/critic04/brown.py`, `round_brown(P, "brown_wool")`)
- Brown columns = `brown_mushroom_block` cells with plan y 3..8.
- Every edge top cell becomes `brown_wool_stairs[half=bottom]`, facing inward: toward the pantry centre (22, 12) for x≥17, toward the porch (13, 16) otherwise.
- The porch crown cells (x12..14, y7, z17) are forced to `facing=north`.
- Lip: for edge cells with an uncapped neighbour, put `brown_wool_stairs[half=top]` with the same inward facing at the cap underside −1, where that cell, the one below it and the inner neighbour are all air.
- Repaint the faces as in P1.
- Result: 57 cells, QA 0/0.

**P3: stem** (`tmp/critic04/stem.py`)
- `skirt(P, "pale_oak", shoulder="pale_oak")`:
  - every `polished_diorite_stairs` becomes `pale_oak_stairs` (same state);
  - ring 6 at schematic y7 gets `pale_oak_stairs[half=top]` facing the stem, where the stem is behind and the cell and the one below are air (10 cells).
- `fibres()` (stripped pale oak streaks): has almost no visual effect. **Do not adopt it.** Use the pilaster ribs from improvement 5 instead.
- QA 0/0.

**Images** (all in `tmp/critic04/` of the example project):

| image | what it shows |
|---|---|
| `cmp_cap.png` | before / A (wool-stair noses) / B (+ flush white warts + repaint): iso_se, elev_s and a close-up |
| `cmp_brown_mats.png` | before vs mud_brick vs granite vs brown_wool, on the pantry and porch close-ups |
| `cmp_stem.png` | before / skirt + pale-oak shoulder / + fibres, porch-side stem close-up |
| `cmp_all.png` | **overall before/after** (all 3 prototypes stacked): iso_se, iso_nw, elev_s, eye |

The individual renders are in `tmp/critic04/img/`:
- `capB_*` and `br2_brown_wool_*` are the adopted variants;
- `stSF_iso_sw` / `stSF_iso_ne` show the full combo from the other sides.

## 5. What to keep

- **The overall silhouette and massing:** the tapering stem with the shoulder, the cap overhang of 3, the layered brown caps tucked under the red rim, and the lamp toadstool as the third mushroom. The hierarchy is right; don't touch it.
- **The cap's height field, warts and gills:**
  - the round rings (the octagon test was right to be rejected);
  - the per-face mushroom states, with pores underneath;
  - the stem-block gill ribs;
  - the glow berries and spore blossom under the rim.
- **The porch and door:** the teal warped door as the single accent, the dark-oak round-headed frame, the lantern beside the door, the step.
- **The stone plinth and volva flare stairs in runs:** good ground contact.
- **The interior layout:** the hearth on the north wall with the mantel, the central toadstool table, the bay seat, and the loft over the north half with a ladder.
- **The garden:** the fallen hollow log bench, the stump with shelf mushrooms, the birch pair and spruce kept 2+ clear of the cap, the leaf litter on the shady NW cap terraces, and the flower choice (lily of the valley + blue orchid + mushrooms).
