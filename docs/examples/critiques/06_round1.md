# 06 Village Library ("Quillwood Library"): critique, round 1

Reviewer: independent judge pass. No build files were edited. The prototypes live in `tmp/critic06/harness.py`: it reads the real
schematic, swaps parts, then runs `blockwright.resolve`, `blockwright.qa.run_qa` and the renders. Run it with `python tmp/critic06/harness.py clay+spire2+trees iso_se,eye`.
**Coordinates:** schematic = plan + (13, 1, 5). The plan coordinates are the ones in `builds/b06_village_library.py`. Both are given below.
QA: base and every chosen variant have **0 errors and 0 warnings** (the 264-dark-spots info is unchanged).

## Verdict on the lead's impression

| claim | verdict |
|---|---|
| Strong silhouette: copper turret, rose window, dormers | **Confirmed.** The massing is the best of the village so far: the tall nave, the off-centre turret and the wing all step down. |
| Too dark, grey and gothic (haunted chapel) | **Confirmed. This is the main problem.** The deepslate is about 50% of every iso view, the stone storey is another 25–30%, and there is little plaster below the eaves. The only warm notes are the poplars, and they are pure orange. The roof does contrast with the walls (by luminance), but both are cold, so the whole mass reads grey-black. |
| The copper spire is a stacked pagoda | **Confirmed. Root cause:** the cone is 7-wide, then 5-wide, then a **3x3 column of stairs stacked 3 high** (sch y21–23). Each ring shows as a separate tier, the top is a square box, and there is no flare. |
| The poplars are orange blobs | **Confirmed.** The egg radius table (max r 2.35) makes 5-wide round masses with flat sides. Both trees are the same orange, bookend the porch, and in the eye view they hide half the facade. |
| The west roof is a big plain field | **Confirmed.** QA reports the longest flat run as 17 x deepslate_tile_stairs and the largest same-material patch as 34. The west plaster share is 6%, under the 10% rule. |
| The chimney is a plain column | **Confirmed, but minor.** It is a 2-wide grey stack with one shoulder. The crown is fine. |

## 1. Scores (1–10)

| category | now | with the prototyped fixes |
|---|---|---|
| Silhouette & massing | 7 | 7.5 |
| Roof (incl. spire) | 4.5 | 6.5 |
| Facade depth & detail | 6.5 | 6.5 |
| Materials & colour (cottagecore warmth) | 4 | 6.5 |
| Entrance | 6 | 6.5 |
| Interior | 6.5 | 6.5 |
| Landscaping (incl. trees) | 5.5 | 6.5 |
| **Overall** | **5.5** | **≈6.5 → 7 with improvements 4–6** |

## 2. Blockers (block-level)

1. **Cold palette.** The roof is deepslate tile/brick on the nave, wing, porch, oriel and dormers.
   - Fix: switch the field to a clay-tile roof. The recipe is in §4A.
   - In the build script: `roof_stair()` uses `blk = "brick"` with hem `"mud_brick"`, and every other roof material changes as listed in the table in §4A.
   - Keep the grey stone storey. Under a red roof it reads as a dignified plinth, and that keeps the gravitas.
2. **The spire reads as a pagoda.** Replace the cone with the flared witch hat in §4B. Its top rises from sch y25 to y26.
3. **The poplars are blobs.** Replace them with lobed flame poplars (§4C) in two different tones.
4. **The west roof field and west plaster share (6%).**
   - Not prototyped. The QA flat run starts at sch (15,16,4), which is plan (2,15,-1).
   - Break the field with one small 45° gabled dormer on the west slope at plan x0..1, z2..4 (sch x13..14, z7..9), plate plan y12.
     Give it a plaster cheek, a 1x2 light, its own dark-oak slab ridge, and a pale-oak sill plus a flower box. This mirrors the east clerestory rhythm without copying it.
   - Raise the plaster share by making the oriel jetty face calcite/pale_oak_planks. The oriel is plan x-2, z8..12 (sch x11, z13..17), y7..9 plan (sch 8..10).
   - Bring a calcite triangle into the dormer gable. That should push the west elevation past 10%.

## 3. Top 6 improvements

1. **Clay-tile roof field** (prototyped, §4A). This is the biggest single change in mood, from haunted chapel to village library. The weathered-green copper turret on the red roof is a complementary pair that reads as storybook.
2. **Flared witch-hat spire** (prototyped, §4B): a 9-wide copper flare ring, a concave rise, a rounded tip and a taller needle.
3. **Flame poplars** (prototyped, §4C). They are 3 wide instead of 5, have a pointed crown, and use different tones (one gold, one orange with a red skirt), so they no longer bookend.
   They still need a slightly wider lower skirt: in elev_w the prototype looks a little thin and gappy. Add a 4th lobe at dy 2.2 with rx 1.9.
4. **Flower colour and boxes.** The beds are only cornflower, azure bluet and white. Add pink and purple drifts:
   - `pink_petals` / `peony` / `allium` in the forecourt beds at plan (-1..1, 19..21) and (7..9, 18..20).
   - Flower boxes under the four south and east timber windows: an open `pale_oak_trapdoor` on the outer face (L+2), with `rooted_dirt` at L+1 under the sill and `pink_petals` or `potted_allium` on top.
   - Pale oak, not poplar, so the boxes read against the poplar timber.
5. **Chimney articulation.** Do not brick it: it would merge with the clay roof.
   - At plan y13 (sch y14) add a corbel band of upside-down `stone_brick_stairs` facing out around the stack (plan x6..7, z-2..-1 → sch x19..20, z3..4).
   - Above the band, add a one-course `tuff_bricks` band at plan y15 (sch 16).
   - Add a second `decorated_pot` on a full block of the crown, never on a slab. The current slabs are at plan (7,19,-2) and (6,19,-1), sch (20,20,3) and (19,20,4).
6. **Porch and entrance.**
   - The lean-to over the portal is dark and deep, so the copper door disappears in the eye view.
   - With the clay roof the porch gets lighter. Also hang a `lantern` under the porch eave beside the door (not in front of the transom).
   - Make the 1-block step a `poplar_slab` or `stone_brick_stairs` with a moss-carpet edge.
   - Move the front lamp post at plan (7,25), sch (20,26,30), a block off the path axis so it no longer stands in front of the door in the eye view.

Minor items:
- The birch canopy (plan -10,4) is clear of the building (it keeps ≥3 air everywhere). It only overlaps in projection.
- Cut views: the interior reads well: shelf aisles, reading table, fireplace, U-gallery and the enchanting ring.
- The hall floor is poplar planks with dark oak. A long runner of `light_blue_carpet` would tie the blues together. It is fine as is.

## 4. Prototype recipes

### A. Clay-tile roof (variant `clay`)
Swap these on every roof part (nave, wing, porch lean-to, oriel gable, dormers, verges). Keep facing and half.

| now | new |
|---|---|
| `deepslate_tile_stairs` (field, 358) | `brick_stairs` |
| `deepslate_brick_stairs` (hem runs on the 2 eave courses) | `mud_brick_stairs` |
| `deepslate_tiles` (F cells under the ridge, dormer cheek backing) | `bricks` |
| `polished_deepslate` (verge fills, ridge-end finial plan (4,18,15) / sch (17,19,20)) | `dark_oak_planks` |
| `polished_deepslate_slab` (ridges) | `dark_oak_slab[type=bottom]` |
| `deepslate_tile_wall` finial plan (4,19,15) / sch (17,20,20) | `dark_oak_fence` |

The dark-oak eave coves, barge boards and moss carpets stay.
- Tried as well: `spruce` reads brown-on-brown with the poplar timber, and the west field becomes a wooden wall.
- `granite` (granite stairs, brick hem) is a softer pink, a valid alternative if the brick mortar lines look too masonry-like up close.
- The chosen variant is `clay`.

Images: `tmp/critic06/compare_roofs.png` (deepslate / spruce / brick / granite), plus `tmp/critic06/try_roof2.png` (eye, iso_sw, elev_w).

### B. Flared witch-hat spire (variant `spire2`)
- Axis: sch (23,·,19) = plan TC (10,14).
- Rings use the existing `octk(TC, 1)` metric with **kmax 4** (one ring wider than now). The 4 diagonal cells of ring 1, sch (22/24,·,18/20), are treated as ring "1.5", which rounds the tip.
- Facing comes from the existing `cone_facing`.
- Keep the build's hidden helper stairs (`make_cone_rings`) for diagonal ring contacts. My prototype skipped them, so elev_s shows 2–3 dark pinholes at the k3/k2 diagonals.

| ring | sch y (plan y = sch − 1) | blocks |
|---|---|---|
| k4 (new flare, 9-wide octagon) | 19 | `waxed_weathered_cut_copper_slab[bottom]`; at 18: `dark_oak_stairs[half=top, facing=f]` bracket |
| k3 | 19 | `waxed_weathered_cut_copper_stairs` (was the lip slab); keep a dark-oak bracket at 18 |
| k2 | 19 fill `spruce_planks`; 20, 21 stairs | stair-on-stair (was 19, 20) |
| k1 edges (4 cells) | 19–20 fill; 22, 23, 24 stairs | |
| k1 corners ("1.5") | 19–20 fill; 22, 23 stairs | rounds the 3x3 column off |
| k0 | 19–21 fill; 22–25 `waxed_weathered_cut_copper`; 26 `waxed_weathered_lightning_rod` | top is 1 higher than now |

In the build's terms (plan, `T_ = 17`):
```
CONE = {4: [(T_+1, "lip")],
        3: [(T_+1, "S")],
        2: [(T_+2, "S"), (T_+3, "S")],
        1: [(T_+4, "S"), (T_+5, "S"), (T_+6, "S")],
        "1.5": [(T_+4, "S"), (T_+5, "S")],
        0: needle T_+4..T_+7, then rod T_+8}
```
Fill `spruce_planks` under each ring down to T_+1.
- Tested: `spire1` (hips on the current profile; my hip predicate took whole faces, and the variant leaked when the core was removed), `spire3` (same, flared) and `spire4` (lower, 2-2 stacks). The flared hat `spire2` reads best.
- Still a small weakness: the flare is a flat 1-course slab ring. A real bell kick would take a second slab ring at k4 one course lower (sch 18) on `dark_oak` brackets.

Image: `tmp/critic06/compare_spire.png` (iso close-up + south elevation, before/after), plus `tmp/critic06/try_spire.png` (all variants).

### C. Flame poplars (variant `trees`, `poplar_v2` in the harness)
- Trunks at sch (10,·,28) h13 and (24,·,28) h12, i.e. plan (-3,23) and (11,23). Each is a 1x1 `poplar_log[axis=y]` from sch y2 to top−2.
- Canopy: a union of 5 ellipsoid lobes up the trunk, `(dy, offset x, offset z, rx, ry)` scaled by h/12:
  `(3.2,0,0,1.55,1.9) (5.4,.4,-.3,1.85,2.0) (7.4,-.4,.3,1.6,1.8) (9.0,.2,.2,1.25,1.5) (10.6,0,0,0.8,1.4)`.
  Each lobe's centre is jittered by ±0.3 and its edge is roughened with `value3(scale 1.6) ±0.28`. There are no leaves below y g+2, and a single leaf tip sits on top.
- Colour comes in drifts by relative height: t = rel + value3(scale 3)±0.17.
  - Tree 1 (W, "turning"): `yellow_poplar_leaves` above 0.45, a little `orange` low.
  - Tree 2 (E, "yellow"): yellow above 0.38, orange body, and a `red_poplar_leaves` skirt only on the SE sun side.
- Twig stubs: `poplar_fence` inside the canopy at 45% and 62% of the height.
- Drips: 1–2 blocks long from the lowest lobe rim at (−2,0), (1,2) and (2,−1).
- Add (not yet in the prototype): a 4th low lobe, dy 2.2 and rx 1.9, to give a fuller skirt.

Image: `tmp/critic06/compare_trees.png`.

### Combined
`tmp/critic06/compare_overall.png` shows iso_se, iso_sw, eye and elev_w, before and after `clay+spire2+trees`. QA: 0 errors, 0 warnings.
The per-view PNGs are in `tmp/critic06/img/<variant>_<view>.png`.

## 5. What to keep
- The massing hierarchy: tall nave → turret → enchanting wing → porch. The turret's stone shaft, corbel ring and plaster lantern stage.
- The rose window: a proud 5x5 stone ring with a chiseled keystone and a yellow centre pane. It is the hero of the south front.
- The east clerestory dormers: plaster cheeks and dark-oak barges, a good rhythm.
- The stone storey with polished-andesite quoins and a mossy foot. Under a warm roof it becomes the gravitas.
- The north stack with a real campfire and a woodpile lean-to.
- The interior: the U-gallery reached by the turret spiral, the double-height hall, the fireplace nook and a valid enchanting ring.
- The landscaping structure: the forecourt that dissolves into stepping stones, the reading garden with its bench, lectern and lamp, and the golden birch NW.
