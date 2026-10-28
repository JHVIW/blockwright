# 03 Fairy Flower Cottage ("Blossom Bell"): critique, round 1

Reviewer: independent judge pass (no build files edited).
Sources: every render in `out/previews/03_fairy_flower_cottage/` (sheet, 4 iso, 4 elev, top, cut_1/2, eye, extra/*),
my own close-ups and interior eye shots in `tmp/critic03/`, block dumps of the `.litematic`, the QA report, the
builder log, the brief and `docs/design-guide.md`. I also built test roofs in `tmp/critic03/rooftest.py` (a scratch
script, not a build file) to check the roof fix before proposing it. The key image is
`tmp/critic03/roof_current_vs_proposed.png`.

**Coordinates.** Unless marked "plan", all coordinates are schematic coordinates (x east, y up, z south; ground
`g` is y=2). The build script's plan coordinates are **schematic minus (12, 2, 10)**. Example: the main bell axis
is schematic (12,·,10) = plan (0,·,0).
Landmarks: main wall octagon x8..16 / z6..14, walls y4..8, lip and wall plate y9. Dark lip ring x6..18 / z4..16.
Turret axis (6,·,10), turret walls x4..8 / z8..12. Door (12,4..5,13), step/entrance (12,3,16). Chimney x12..13 /
z4..6, y3..16, campfire (12,15,6). Tree trunk base (18,3,3), canopy x13..21 / z1..8 / y11..15. Loft floor y8, bed
(10,9,7..8).

---

## Verdict on the lead's first impression

| claim | verdict | evidence |
|---|---|---|
| The concept and silhouette (bell, turret, leaning chimney, cherry tree) are strong | **Partly confirmed.** | The concept is the right one, and elev_s and elev_e are the best views of the whole set: concave bell, second bell, finial, tree. Two views fail, though. In **elev_w** the turret axis (z=10) lines up with the main axis, so the turret bell stands dead centre in front of the main bell and the two read as one stacked wedding cake (close-up `tmp/critic03/..._closeup_7_11_10.png`). In **iso_ne / iso_nw** the canopy lies directly on the roof, so the NE quarter of the silhouette is a single pink blob. |
| The cherry roof reads lumpy and stepped, like a tiered cake or a pile of boxes | **Confirmed, and I found the root cause.** | Ring k is `ceil(dist - 0.5)` on a Euclidean circle. That makes every ring **1 cell thick on the four axes but 2–3 cells thick on the diagonals.** For example, ring 4 is the L (−3,−3),(−2,−3),(−3,−2) in plan, and ring 6 is 2 wide at (−4,−4),(−5,−4),(−4,−5),(−3,−5). Where a ring is thick, its stairs form flat plateaus followed by double risers, and the outer-corner pegs land in different places on every ring. That is the "pile of boxes". On top of that, the 63° crown uses `stripped_cherry_wood` risers (23 blocks), which are darker and more saturated than the planks and so read as frosting bands. Test: the same profile on uniform octagonal rings (variant B in `roofcmp_se.png`) is already clean. |
| The pink roof and the pink canopy blend together | **Confirmed.** | The canopy leaves sit directly on roof blocks with **0 air gap**: at (15,·,5) the roof top is y11 and the leaves are y12–14; at (14,·,6) and (15,·,7) the roof top is y11 and the leaves are y13–14; at (16,·,6) the roof top is y9 and the leaves are y12–14. |
| The canopy is made of squarish leaf blobs | **Confirmed.** | There are only 111 cherry leaves, in 3 flat layers (y12: 27, y13: 46, y14: 26) with a rectangular outline in the top view. |
| The chimney is a plain stone column | **Confirmed, and it is worse than that.** | The campfire at (12,15,6) has **open air on its west (11,15,6) and south (12,15,7) sides**. It is not in a flue: it sits on an exposed shelf, and you can see the flames from the west and south (elev_w, iso_sw, iso_se). |
| The north side lacks windows | **Confirmed.** | QA reports "north 0". The NE and NW diagonals have none either, and the loft bedroom has **no window at all**. |

Other findings the lead did not list: the turret roof is oversized and its eave is 1 below the main eave (B7). The
east "dormer" is a lump with white cheeks (B4). Single leaf cubes are dropped on the roof (B3). The inside of the bell is
raw stair undersides (#3). The living roof ended at **0 moss cells** (meta notes), so it does not exist. The glow
berries are repetitive (#5). The path runs into a fence post (#8).

---

## 1. Scores (1–10)

| category | score | one-line reason |
|---|---|---|
| Silhouette & massing | **6** | Round body, second bell, finial, chimney and tree: the right ingredients, and elev_s is lovely. But the W view stacks the turret on the main axis, the NE view fuses the tree into the roof, and the 9-wide turret bell on a 5-wide turret is an "oversized roof on a tiny building". |
| Roof | **4** | The flare, the dark lip and the eyebrow window are good ideas, but the surface reads as terraces and pegs, the crown as cake tiers, and there are dropped cubes and a flat-topped dormer lump. |
| Facade depth & detail | **5** | It has a recessed door, shutters, sills, a flower box, glow berries and brackets. But the walls sit in deep shadow under a 2-deep brim, the infill is nearly one material (main wall ring y4..8: 25 pale_oak_planks, 4 mushroom_stem, 0 stripped_birch_log; the plan said 40/30/30), the north is blank, and the glow berries hang from almost every post. |
| Materials & colour | **6** | The palette discipline is good: pink, green, dark wood, white, plus purple and one blue accent, and no rainbow. Against that: stripped-cherry banding, two random white blocks, pink-on-pink at the tree, and a brown "plate" of uneven width around the roof. |
| Entrance | **6.5** | A recessed cherry door with a transom and a hanging copper lantern, potted alliums, a mossy step, a trellis on cherry posts, a lamp post and the eyebrow window above: a real composition. The trellis reads as a square leaf frame, and the path is a ruler line. |
| Interior | **6** | Hearth with a mantel and candles, a barrel table with stools, a bookshelf reading seat, a kitchen arc, a window nook and a loft (bed, nightstand lantern, chest, lattice rail). It is lit and reachable. But the bell vault is raw stair undersides (`tmp/critic03/loft_up.png`), the loft has no window, and the carpet is a blocky cross. |
| Landscaping | **6.5** | The petal carpet under the tree is the best element in the build. Pond, mushroom ring, drift bands and fade-out are all present. Weak points: cube bushes, a podzol "C" glyph, a straight stepping-stone line, a 4-cell fence fragment with a hole, and a symmetric root "plus". |
| Would a talented builder be proud of it? | **5** | They'd be proud of the idea and the south elevation. On Planet Minecraft the comments would say "cute concept, the roof needs smoothing and the tree looks pasted on". Fix B1–B7 and this becomes a 7.5–8. |

---

## 2. BLOCKERS (each one alone says "AI-generated")

### B1. The roof surface reads as a pile of boxes, and the dark brim varies in width
* **Where:** the whole main bell; most visible in iso_se, iso_sw, top and `closeup_13_12_11`. The brim is 2 cells wide at the
  NW/NE/SW diagonals and 1 cell elsewhere (top view).
* **Why:** Euclidean ring quantization makes ring thickness non-uniform (see the verdict table). The helper stairs keep the shell
  closed but cannot fix plateaus and double risers.
* **Fix: octagonal offset rings with uniform thickness, plus a real two-step slab flare.**
  Ring metric (main): `k = max(|dx|, |dz|, |dx| + |dz| - 2)` around plan (0,0). **Ring 4 of this metric is exactly the
  existing wall plan** (rows 5/7/9/9/9/9/9/7/5), so the walls don't move. Every ring is then exactly one cell wide.
  The N/E/S/W facets are 5-cell straight runs at every ring, and the four diagonal facets are clean 45° staircases, so
  corner stairs line up on 8 hip lines instead of being scattered. Keep the helper-stair trick for the diagonal joints;
  it works unchanged. The lip ring becomes a uniform 1-cell dark band.

  **Per-ring profile. Option A (recommended): walls one course taller, so the lip moves from y9 to y10 (plan y7 → y8).**

  | ring | where | top piece, plan y (schematic y) | under it | tread | step |
  |---|---|---|---|---|---|
  | R6 | lip, 2 out | `dark_oak_slab[bottom]` @8 (10) | inverted `dark_oak_stairs` bracket @7 every 2–3 cells, as now | 8.5 | — |
  | R5 | 1 out | `cherry_slab[top]` @8 (10) | — | 9.0 | +½ = 26° flare |
  | R4 | wall line | `cherry_slab[bottom]` @9 (11) | wall plate @8 | 9.5 | +½ = 26° flare |
  | R3 | 7-wide octagon | `cherry_stairs` facing centre @10 (12) | `cherry_slab[top]` @9 | 10.5 | +1 = 45° |
  | R2 | 5×5 | `cherry_stairs` @12 (14) | **`cherry_planks`** @11 (no stripped cherry) | 12.5 | +2 = 63° |
  | R1 | 3×3 | `cherry_stairs` @14 (16) | **`cherry_planks`** @13 | 14.5 | +2 = 63° |
  | R0 | centre | one block @15 (17) (planks or stripped cherry; it is a single cell) | — | 16 | +1 |
  | finial | | `dark_oak_fence` @16 (18) + `waxed_copper_lantern` @17 (19), as now | | | |

  In the script's half-block units:
  `MAIN_PROFILE = {6: (17,"slab"), 5: (18,"slab"), 4: (19,"slab"), 3: (21,"stair"), 2: (25,"stair"), 1: (29,"stair"), 0: (31,"spire")}`.
  R3–R1 keep their **current** heights (21/25/29), so loft headroom is unchanged (bed cell (10,9,7) keeps ≥2 clear).
  Only the eave lifts one course and becomes a slab flare. The extra wall course also answers the user's "oversized
  roof on a tiny building" complaint: the walls currently sit in shadow under the 2-deep brim.

  *Option B (walls unchanged):* `{6:(15,slab), 5:(16,slab), 4:(17,slab), 3:(19,stair), 2:(23,stair), 1:(27,stair), 0:(29,spire)}`.
  The crown drops one block. Under R3 only 1.5 stays clear, so the loft shrinks to the 5×5 core unless the loft floor
  drops from y8 to y7 (plan y6 → y5).

  Evidence: `tmp/critic03/roof_current_vs_proposed.png` (top row: current Euclidean geometry, bottom row: Option A),
  `roofcmp_se/s/sw.png` (variants A–F), `tallcmp_*.png` (B/I/J). Variant J has the same shape one course lower and
  reads as the best bell in elevation.

### B2. The crown is a tiered cake, and both spires are "candles"
* **Where:** main crown y13–17 and turret crown; elev_s, elev_w, `closeup_12_12_10`, `closeup_6_9_12`.
* **What:** a 5-wide and a 3-wide box tier, each with a darker stripped-cherry riser band, and a 1×1 pink cube on top.
  The turret is the same in miniature: a 3×3 cube tier, then a 1×1 cube with an end rod.
* **Fix:** set `ROOF_VARIANT = ""` so the risers are `cherry_planks`. The test variant H (`risercmp_se.png`) shows how
  strongly stripped risers band. Inverted-stair risers (variant G) open a dark crack, so don't use them either. The
  spire is a single block exactly 1 above the R1 stair backs (spire s = R1 s + 2), and the needle above it is
  fence + lantern (main) or `cherry_fence` + `end_rod` (turret). Never 2 solid blocks above the last stair ring.

### B3. Things dropped on the roof: lone leaf cubes and white cheeks
* **Where:** `flowering_azalea_leaves` cubes at (15,12,12) (centre of the SE skirt, very visible in iso_se),
  (15,13,9) and (4,10,8). `pale_oak_planks` "cheeks" at (17,11,9) and (17,11,11) show as a random white square (iso_se,
  elev_s, `closeup_17_11_10`).
* **Fix:** delete all three cubes and both pale cheeks (make the cheeks cherry planks). The living roof comes back
  properly under improvement #2. On the new slab rings it is shape-safe: a `moss_block` in place of an R5 top slab is
  flush (both tops at 9.0), so it changes no stair corners.

### B4. The east "dormer" is a lump with a flat slab tongue
* **Where:** x15..18, z9..11, y11..13: glass (17,11,10), stairs (15..18,12,9) and (15..18,12,11), and a 4-long flat
  `cherry_slab` ridge (15..18,13,10) running from the crown to the eave. In the top view it is the flat plank strip on
  the east. In iso_se it is a flat shelf next to the tree.
* **Fix:** remove it. A gable dormer on a bell roof fights the curve. Replace it with a **second eyebrow** (2 wide)
  in the E/NE skirt, using the same technique as the south eyebrow but a different width so the two read as a family.
  If a gable dormer stays, follow §3.1.10: face at R4 set back ≥1 from the lip, its own 45° stair roof, ridge ≥2 below
  the crown, no flat slab ridge, all-cherry cheeks.

### B5. Chimney: the fire sits on an open shelf, and the stack is a plain column
* **Where:** stack x12..13 / z4..5 up to y12, offset to z5..6 for y13..16. Campfire (12,15,6) is open to (11,15,6)
  and (12,15,7). An 11-cell flat `mossy_cobblestone` patch on the north face is QA's "largest flat patch".
* **Fix (block level):**
  1. Corbel the top out to a 3×3 crown (x11..13, z5..7, y14..16) on inverted `tuff_brick_stairs` facing out at y14.
     The campfire stays at (12,15,6), now enclosed on all 4 sides. Leave (12,16,6) and everything above it open air.
     Put a rim of inverted `tuff_brick_stairs`/`tuff_brick_slab` at y16 around the hole, one `moss_carpet` tuft, and
     optionally a `potted` allium on one rim corner as a fairy chimney pot.
  2. Taper: a 3-wide base to y5 with `tuff_stairs` shoulders stepping in to the 2×2 stack.
  3. Add a string course of `polished_tuff`/`tuff_brick_slab` where the stack passes the roof.
  4. Use a gradient: `mossy_cobblestone` only in the bottom 2–3 courses, `tuff`/`cobbled_deepslate` in the middle,
     `tuff_bricks` with 10–15% `mossy_stone_bricks` at the top.
  5. Lean the top outward (north) instead of toward the crown, so the chimney reads as its own vertical accent.

### B6. The tree is pasted onto the roof: a pink slab canopy on a zigzag trunk
* **Where:**
  * The trunk is 1 wide with right-angle elbows.
  * There is a symmetric root "plus" at y3: (17,3,3),(19,3,3),(18,3,2),(18,3,4) around (18,3,3).
  * There is a symmetric T crossbar at y8: (17,8,2),(17,8,3),(17,8,4).
  * There is a flat 10-block branch plate at y10 (x15..19, z1..5).
  * Pink log end grain is exposed under the canopy (iso_nw, `closeup_17_12_4`).
  * The canopy has a 0 gap to the roof (see the verdict table).
* **Fix:**
  * **Roots:** replace the plus with 3 roots of lengths 1, 2 and 3 in different directions. Use `cherry_wood` at y3,
    tapering to `cherry_log[axis=x|z]` sunk into the grass layer (y2), with a little `rooted_dirt`/`moss_block`. The
    petals continue over them.
  * **Trunk:** a 2×2 base (x17..18, z3..4, y3..5) tapering to 1×1. Lean 1 cell every 2–3 courses, and bridge each step
    with one `cherry_log` along the step axis, never a 3-wide T. Split into 2 limbs around y9–10, and put `cherry_wood`
    at every limb tip so no end grain shows.
  * **Canopy:** 2–3 overlapping domed lobes. Each lobe is 5×5 minus corners at the bottom, 7×7 minus corners in the
    middle and 5×5 minus corners on top, with ±1 edge jitter. The main lobe sits NE of the chimney (≈ x17..21,
    z0..5, y13..16). A smaller lobe reaches toward the NE eave only (≈ x14..16, z4..7, y13..14). Never put leaves
    over the crown.
  * **Clearance:** keep ≥2 air between the leaves and the roof surface everywhere. Hang 8–12 drips of 1–2
    `cherry_leaves` from lobe undersides; none may touch the roof.
  * **Separation:** the dark limbs visible in that gap, plus the green NE living-roof patch (#2), separate the two pinks.

### B7. Turret: oversized bell, eave 1 lower than the main eave, and stacked on the main axis
* **Where:** turret axis plan (−6,0) = (6,·,10). Its bell has overhang 2 (ring 4), so it is 9 wide on a 5-wide turret.
  Its lip is at plan y6 against the main lip at y7, and §3.1.6 says "never 1 lower, it looks like a mistake". In
  elev_w it sits exactly in front of the main bell.
* **Fix:**
  1. Move the axis to plan (−6,+2) = (6,·,12). It then shares the main west wall at z10..12 and sits in front of the
     house in elev_s, with its spire 2 to the side of the main spire in elev_w. Check the pond bank at z15.
  2. Use overhang 1 and an eave at the main eave height (one continuous dark band). Turret walls go up to plan y7 like
     the main walls. Ring metric `k = max(|dx|,|dz|,|dx|+|dz|-1)`, where ring 2 is the existing 5×5-minus-corners
     wall: `TUR_PROFILE = {3:(17,"slab"), 2:(18,"slab"), 1:(21,"stair"), 0:(23,"spire")}`. That gives a dark slab
     lip @8, a cherry top slab @8 on the wall line, 3×3 stairs @10 on planks @9, a centre block @11, `cherry_fence`
     @12 and `end_rod` @13 (plan y). The turret tip ends about 4 below the main finial: clearly subordinate, and
     clearly its own bell rising from the main flank.

---

## 3. Top 10 improvements (ranked by visual impact)

1. **North side and loft daylight.**
   * Put a 1×2 window over the kitchen sink in the NE diagonal wall cell (≈ (15,5..6,7)). Glass goes at L−1, with one
     `cherry_trapdoor` shutter (one side only), a `dark_oak_trapdoor[half=top]` sill and one potted plant.
   * Put a 2-wide eyebrow in the NW skirt (R4/R5 at ≈ x9..11, z5..6) looking into the bed nook at (10,9,7). The north
     elevation gets a feature, and the bedroom gets a window.
2. **Make it read "flower-covered" with 3 bloom zones on the building**, not more singles on the lawn.
   * **(a) NE living eave under the tree.** Swap 6–10 adjacent R5 top slabs near x14..17 / z4..6 for `moss_block`
     with `moss_carpet`. Plant `pink_petals` (3–4) on them as fallen blossom. Add 2–3 `flowering_azalea_leaves`
     clumps sitting on the lip so they spill over the dark edge. This green band also separates roof pink from canopy
     pink.
   * **(b) The entrance arch** (#4).
   * **(c) The turret.** Keep the flower box and add a `flowering_azalea_leaves` climber stepping up its SW post into
     the eave, with the `spore_blossom` beneath.
3. **Finish the bell vault inside** (`tmp/critic03/loft_up.png` shows raw stair undersides; guide §3.1 rule 5).
   * Wherever a roof stair's underside is visible from interior air, put `cherry_planks` one below it, so the vault
     reads as smooth stepped planks.
   * Run 8 hip rafters (`dark_oak_stairs[half=top]` / `stripped_dark_oak_log`) along the 8 octagon hip lines from the
     wall plate up to a collar ring (`stripped_dark_oak_log`, horizontal) at R2 inside, ≈ y13.
   * Hang the chandelier from the collar centre.
4. **Entrance trellis as a real arch.**
   * Remove the square corners (10,8,15) and (14,8,15). The leaves then step from (10,7,15)/(14,7,15) to (11..13,8,15),
     which makes a rounded arch.
   * Hang one 1-long glow berry or a `spore_blossom` from the apex.
   * After the wall raise, give the arch 1 more course (posts to y7, shoulders y8, crown y9).
5. **Glow-berry restraint.** There are 7 strands now, at (4,·,13), (4,·,7), (7,·,14), (7,·,6), (10,·,16), (17,·,13)
   and (18,·,9), almost one per post and all 2–3 long. Keep 4 (door (10,·,16), (17,·,13), (4,·,7), (18,·,9)) at
   lengths 1, 4, 2 and 3. Delete the rest.
6. **South facade balance and window legibility.**
   * The infill right of the door (≈ x13..15, z13..14, y5..7) is blank. Add the second round window the brief asked
     for: a 1×1 porthole with glass at L−1 and a cherry trapdoor frame.
   * The turret plus-window (5,6..8,9..11) reads as one pane in a white wall. Frame it dark (`dark_oak_trapdoor`s
     around it) so the plus shape shows.
7. **Shadow lines on the walls.**
   * With the extra wall course, add knee braces (`dark_oak_stairs[half=top,facing=<in>]` at the top of every second
     post, L+1).
   * Add a `dark_oak_trapdoor[half=top]` drip ledge over the plinth on the S and E faces.
   * Restore the infill gradient: `mushroom_stem` low, `stripped_birch_log` middle, `pale_oak_planks` high (§2.2).
8. **Path and gate.**
   * The stones run in a straight line x=12, z16..19 straight into a fence post at (12,3,20). The gate is at (13,3,20),
     and (14,3,20) is a hole in a 4-cell fence fragment.
   * Meander the stones ±1 (e.g. z17 x12, z18 x11, z19 x12, gate aligned on the last stone). Make one 2-cell stone and
     fade the far end with `moss_carpet`/coarse dirt.
   * Either make the fence a 5–7-cell curved run ending in a bush (no hole), or remove it.
9. **Bushes and fairy ring.**
   * The azalea bushes are 2×2×2 leaf cubes (NW ≈ x2..4/z1..4, W ≈ x1..3/z14..16, SE). Give each a 1-high skirt, a
     2-high off-centre core, an `azalea`/`flowering_azalea` shrub block on top and a `moss_carpet` ring (§5.3).
   * The podzol band (16..20, 2, 15..20) reads as a brown "C" from above. Put podzol only under each of 8 mushrooms on
     an imperfect circle (r≈2.5 around (18,·,18)), with grass and moss between and one gap.
10. **Interior polish.**
    * Replace the white/pink carpet cross with a round rug (5×5 minus corners, pink with a white 3×3-minus-corners
      centre).
    * Give the nook seat 2 windows after the turret move.
    * Check that the kitchen arc still has a 1-wide working aisle beside the east stair.
    * *QA note for the lead:* all four rooms report the identical floor area 87, so the room flood fill treats them as
      one space. That is not a build defect, but QA is not checking them separately.

---

## 4. What already works (keep it)

* **The story and the composition:** round bell house, a second smaller bell, crooked chimney with real smoke, leaning
  cherry tree, petals, pond, mushroom ring. It is exactly the brief's mood.
* **The south elevation:** the eyebrow window directly over a recessed cherry door with a transom and a hanging green
  copper lantern, potted alliums in the niche, the mossy step, cherry trellis posts, and the lamp post off-axis.
* **The dark lip + inverted-stair bracket idea** that holds the light pink. Keep it, but as a uniform 1-cell band (B1).
* **Copper lantern finial,** the green-flame accent family, the spore blossom, and glow berries (fewer of them).
* **Smoke physics:** campfire 1 below the rim and an open flue above. Keep this when you enclose it.
* **The plinth:** tuff/mossy-cobble gradient with drift bands per side (allium and petals S, lilac E, ferns/moss N).
* **The petal carpet under the tree, fading out** (iso_ne). It is the best landscaping element. Also the organic pond
  with lily pads and the single cool accent (blue orchid).
* **The interior program:** hearth with mantel, candles and potted azalea; barrel table and stools; bookshelf
  reading seat; kitchen barrels, smoker and cauldron; loft with cherry trapdoor lattice rail; bed, nightstand lantern,
  chest and chiseled bookshelf; chandelier. All lit (min 7) and reachable.
* **Colour discipline:** pink, green, dark wood, white, with purple and one blue accent. No rainbow.
* **Clean QA:** 0 floating, every state legal, the Litematica round-trip identical.

---

## Appendix: test harness for the roof fix

`tmp/critic03/rooftest.py` (scratch) copies the builder's ring, helper and fill logic and swaps the ring metric
(`k_euclid` vs `k_oct(c)`) and profile. Variant **K** is Option A above. Run
`python tmp/critic03/rooftest.py A,K` for the current-vs-proposed renders, or `B,C,D,E,F,G,H,I,J` for the other
tested profiles (riser materials: E planks / G inverted stairs / H stripped cherry).
