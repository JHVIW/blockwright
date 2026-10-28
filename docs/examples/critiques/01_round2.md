# 01 Cozy Starter Cottage: critique, round 2

Reviewer: independent judge pass (no build files edited).
Sources: every render in `out/previews/01_cozy_starter_cottage/` (and `round1/` for before/after), my close-ups and
prototypes in `tmp/critic01r2/`, block dumps of the `.litematic`, the QA report, the builder log, the round-1 critique
and `docs/design-guide.md` (§1, §2.2, §3.1, §6).

**Coordinates** are schematic coordinates: x east, y up, z south, ground y=2, floor y=3. Landmarks in this revision:
main walls x9..19 / z6..12, plate y9. Main ridge planks y14 + spruce cap y15 on z9. Steep top courses are
[planks + stair] at (x,12..13,8), (x,12..13,10). Wing x13..17 / z11..16 (jetty face z16, barge boards at z17), wing
ridge log y13 + cap y14 on x15. North lean-to walls x11..17 / z3, plate y6, lip slabs y6 on z2. Dormer x15..17 / z5..8.
Chimney 2×3 stack x7..8 / z8..10 from y12, crown ring y15, rim y16, pots y17.

**Prototype scripts** (scratch only, they never write build files): `tmp/critic01r2/roofproto.py` (material swaps),
`reshape.py` (45° tops, catslide kick), `combo.py` and `combo2.py` (slim chimney, combined target), `share.py`
(elevation shares), `dump.py` (sections and layers).

---

## 0. Verdict on the lead's impression

| claim | verdict | evidence |
|---|---|---|
| Clearly better than round 1 (cream front gable and porch, real bay, flower colour, organic pond and path) | **Confirmed, with caveats** | The jetty gable (14..16,8..12,16) is cream. The porch has a pale-oak round-head arch at (14,6,15)/(16,6,15). The bay glass is pushed out to z13 under a cream frieze. Shutters, sills and box fronts are pale oak. There are about 54 flower cells in drifts. Caveats: the south plaster share is still 7% (+6% pale trim), under the 10% target. The pond is a 13-cell lozenge with 3 bare `dirt` cells at (3,2,15), (4,2,15) and (3,2,17). The path is continuous but steps in rectangles. |
| The dark roof is still the dominant element on elev_s/n/w, and the house reads heavy and dark | **Confirmed on N and W, partly on S** | First-visible-block shares (`share.py`): roof is 40% of S, 53% of N, 40% of E and 33% of W. In the renders, building pixels darker than L60 are 56% on elev_s, 67% on elev_n and 63% on iso_sw. On S, as much of the darkness comes from the frame, the glass and the eave shadow as from the roof. |
| The 63° roof reads as long parallel boards | **Confirmed** | Every steep course is `dark_oak_planks` under `dark_oak_stairs` and runs the full length x9..19 (y12–13 at z8/z10, y14 at z9). The wing has the same at x14/x16, y11–12. At 63°, about 2 of every 2 rows of rise are vertical plank faces. In elev_s the top band y12–15 is therefore a 4-row wall of boards, and in iso it reads as stacked lumber. The wing ridge also reads as a plank box: a 1.5-tall beam end plus a cap at (15,13..14,17). |
| The chimney crown looks top-heavy | **Confirmed, plus a regression** | The y15 `brick_stairs` ring covers 4×5 cells (x6..9 / z7..11) around a 2×3 shaft, so the crown has 20 cells against the stack's 6. It sits at ridge height, and only 3 slim courses (y12–14) show between the shoulders and the brim, so it reads as a goblet. **Regression:** the lit campfire (8,15,9) is at crown level next to the bottom slab (9,15,9), so the flame is visible from the east (elev_e, iso_se, iso_ne, `proto/V0_current_chim_e.png`). In elev_e it looks like a torch on the ridge. §3.1.11 requires the flame to be hidden. |
| The tree is blocky | **Confirmed** | The canopy is a wedding cake. y8 has 30 leaves and y9 has 39, both 7×7 (x21..27 / z1..7). Above them sit 4×4 at y10 and 3×3 at y11. There is nothing at y7, so the underside is a flat 7×7 plate. The north branch (24,6,2..3) ends as a bare log stub 2 below the leaves. |

### Is the roof simply too big for the walls?

* **No on S, E and W.**
  * S: eave y9 to cap y15 is 7 rows over a 6-row wall (y3–8 including the plinth). Roof:wall is 1.17, inside H04's
    0.9–2.0 band.
  * Roof shares of S 40%, E 40% and W 33% are normal for a steep cottage.
  * Raising the walls would turn it into a 2-storey house and fix nothing.
* **Yes on N.** The catslide is 10 courses (lip y6 to cap y15) over a lean-to wall that shows only y3–5 (3 courses,
  one of them plinth). That makes 53% of the elevation roof.
* **The real cause of "heavy" is material, not size.** The roof field is the frame material: `dark_oak_stairs` (L47) on
  `dark_oak_log` posts (L48) and `stripped_dark_oak_log` beams (L59). With no value or hue step between roof and timber,
  roof, frame and shadowed porch merge into one dark mass. §2.2 says "the roof differs from the walls in material".
  The board-like 63° risers add to it.

### Which fix works best: measured on prototypes

Metric: share of building pixels darker than L60 in the 800×600 renders (sky, foliage and terrain excluded). Lower is
lighter.

| variant | change | elev_s | elev_n | iso_nw | read |
|---|---|---|---|---|---|
| V0 | current | 56% | 67% | 63% | |
| V1 | spruce field + dark-oak trims (the lead's suggestion) | 57% | 51% | 62% | Still reads as boards. iso_sw gets darker (64→69%) because the dark trims become the outline. **Not worth it alone.** |
| V2 | V1 + moss carpet on the low courses | 57% | 51% | 61% | Course-aligned moss reads as green stripes at this scale. |
| V3 | tuff-brick "stone slate" field, current geometry | 55% | 48% | 61% | The tile texture kills the boards, and the roof finally differs in hue from the frame. |
| V4 | 45° tops, every ridge −1 (+3×3 chimney) | 52% | 63% | 61% | Fewer boards and one course less roof. The 3×3 chimney reads as a brick tower (rejected). |
| V6 | current roof + slim chimney only | 55% | 65% | 63% | The goblet and the flame are gone. |
| **V11** | **45° tops + catslide kick + tuff-slate field + dark-oak main trims + spruce wing barge boards + slim chimney** | **46%** | **39%** | **50%** | **Reads as a stone-slate Tudor cottage. The focal gable stays warm.** |
| V12 | V11 geometry with a deepslate-tile field (village roof family), spruce trims | 53% | 64% | 64% | Reads as a roof, but stays as dark as now. |

* Comparison images:
  * `tmp/critic01r2/roof_target_compare.png` (V0 / V11 / V12 × elev_s, elev_n, iso_sw, iso_nw, eye) is the main one.
  * `roof_options_compare.png` covers V0 / V1 / V6 / V10.
  * `roof_compare.png` covers V0–V3.
  * `chimney_compare.png` covers the chimney fix.
  * `eye_compare.png` shows V0 and V11 at eye level.
  * Single views are in `tmp/critic01r2/proto/`.
* **Most effective fix:**
  * The decisive lever is a **roof field material that is not the frame material**: B1.
  * Next come **45° tops**, which cost one course of roof (improvement #1).
  * The north side needs a **catslide kick with a 1-course-taller lean-to wall**: B2.
* Rejected:
  * Raising the walls (S is already in proportion).
  * Roof-material banding (more horizontal stripes means more boards).
  * Moss as course lines (V2).
* An extra dormer helps N a little: see improvement #4, the eyebrow.
* **Palette note for the lead.** Tuff slate is not one of the three village roof families (§2, ≈75% rule), so this is
  your call.
  * Deepslate (V12) is in the family but does not lighten the house.
  * A spruce field (V1) does not separate the roof from the frame.
  * If you must stay in wood, do #1 + B2 + B3. That takes elev_s to about 52% dark and elev_n to about 63%: better, but
    the house still reads brown on brown.

---

## 1. Scores (1–10)

| category | R1 | R2 | one-line reason |
|---|---|---|---|
| Silhouette & massing | 5 | **6** | The half-hip, the raised wing ridge and the projecting bay help. In elev_s and elev_n the outline is still a flat 10-block ridge (x9..18) with the wing apex 1 below it, plus a goblet chimney. |
| Roof | 4 | **5** | The trims and weathering are now coherent, and the eyebrow, gable dormer and jerkinhead are good. Against that: the field is the frame material, the 63° board risers read as lumber, the wing ridge reads as a plank box, the north catslide shows a 3-course wall, and the flame is exposed. |
| Facade depth & detail | 5 | **7** | Real bay, cream jetty gable, round-head porch arch, joist and corbel rhythm, azalea box under the jetty window, varied pale shutters. The depth now reads in the eye view. |
| Materials & colour | 3 | **5** | Cream finally shows where it matters, and the flowers have colour. But 57% of S and 62% of N is dark-oak roof + frame, with no hue step between them. |
| Entrance | 6 | **7** | A composed porch: step with cobble cheeks, peonies, bench, barrel with azalea, transom, arch, jetty lantern. The lantern (15,6,13) hangs in front of the transom (15,6,12) and pairs with (16,6,16). |
| Interior | 6 | **7** | Inglenook, armchairs with side table, bookcase wall with chiseled bookshelf and lectern, vault with chain lantern, stone kitchen strip, cauldron sink and smoker, pantry, loft desk, bed nook in the jetty. QA is clean. |
| Landscaping | 5 | **6** | Continuous path, colour drifts, peonies at the step, azalea shrubs, a better pond. But the pond is a 13-cell lozenge with bare dirt squares, the path is a staircase of rectangles, the tree is a wedding cake, and the cart and scarecrow are a pile of yellow/orange cubes. |
| **Overall** | 4 | **5.5** | |

**Versus round 1:** every round-1 blocker was worked and the front now reads composed and cream. Round 1 also asked
for a ring on all four sides, and the chimney traded its grey speckle for a hat and an exposed flame. The roof and frame
are still one dark-oak mass, and the north side is still a roof with a skirting board. **The prototype V11 suggests ~7
is within reach without touching the plan.**

### Round-1 points: what was really fixed

| R1 item | status |
|---|---|
| B1 cream plaster and light hardware | **Mostly fixed.** One infill per panel, pale shutters, sills and box fronts, cream jetty and porch. S plaster is 7%, under the 10% target (admitted in the log). |
| B2 roof noise and outline | **Fixed.** Weathering is course-aligned, and the eave, verge and ridge are one spruce frame. That frame now outlines a field that is the frame material, which is the new B1. |
| B3 north stripe and dormer | **Fixed.** The stripe became a plate, the dormer is a 3-wide gable dormer, and the pantry window was added. The dormer ridge log (y13) is only 1 below the main ridge core (y14), and §3.1.10 wants ≥2. Improvement #1 covers it. |
| B4 east face | **Fixed.** The face is gone, there is a 1×2 window with pale shutters, the half-hip has the rod on its apex, and the woodpile is mixed. |
| B5 chimney | **Half.** The speckle and taper are fixed. The ring is now **top-heavy** and the **flame is exposed** (regression). See B3. |
| B6 path and pond | **Mostly fixed.** The path is continuous; the pond is rounded but small and has bare dirt. |
| Top-10 #1–#10 | All done: bay, arch, azalea box, joists, recess lantern, jerkinhead, planting, north vines and quoins, rafter tails, eyebrow arch, varied shutters, interior, scarecrow and cart. The eyebrow still has no candle on its inner sill (R1 #7). |

---

## 2. BLOCKERS

### B1. The roof field is the frame material, so roof and walls read as one dark mass and the steep courses read as boards
* **Where:** elev_s top band y12–15, elev_n field, elev_e (wing east slope x16..18 / z11..17), elev_w (wing west
  slope), iso_sw, iso_se, iso_nw.
* **Fix (prototype V11, `combo2.py`):** swap the **field** to stone slate and keep the **trims** in wood. Exposed roof
  cells are the `dark_oak_*`/`spruce_*` stairs, slabs and planks with y ≥ 9, or z ≤ 5 and y ≥ 6, that touch outside air,
  excluding the woodpile roof at x ≥ 20, y < 9.
  * **Main-roof trims** become `dark_oak_*`, with the same facing, half and shape:
    * verges x8 and x20 (all courses and inverted partners);
    * catslide verges x10 and x18 at z ≤ 4;
    * the north lip (see B2);
    * the south eave course on z13 at y9 (x8..11 and x19..20);
    * the dormer front (15,12,5), (16,12,5) and (17,12,5);
    * the ridge cap row on z9.
  * **Wing barge boards stay spruce**, so the focal gable stays warm:
    * (12,9,13..17) and (18,9,13..17);
    * (13,10,17), (17,10,17), (14,12,17) and (16,12,17);
    * (15,13,17) and the wing ridge cap.
  * The eyebrow arch (10..12,11,12) stays dark oak.
  * **Field: everything else**, including the current spruce "repair" runs:
    * `*_stairs` become `tuff_brick_stairs`, keeping their states;
    * `dark_oak_planks` become `tuff_bricks`;
    * field slabs become `tuff_brick_slab`.
  * **Field gradient** (no static):
    * about 15% `polished_tuff_stairs` in 3–5-long runs along a course, upper half of each slope only (sun-bleached);
    * about 20% `mossy_stone_brick_stairs` in 2–3 clusters on the two lowest north field courses, (11..17,8,4) and
      (8..20,9,5), nearest the chimney and the NE tree;
    * none on the south slope.
  * **Inside**, the tuff underside becomes the ceiling of the vault (x10..13) and the loft (x14..18, z7..11).
    * Check `cut_2` after the swap.
    * If it reads cold, line the vault with inverted `dark_oak_stairs` under the slope, which has plenty of headroom.
    * Use `spruce_trapdoor[half=top]` panels in the loft, which costs no headroom.
* **Target:** elev_s ≤ 48% and elev_n ≤ 45% dark pixels (V11 reaches 46% and 39%). In the eye view the roof should read
  as grey-green slate above a timber-and-cream house.

### B2. North elevation: 10 courses of roof over a 3-course wall
* **Where:** elev_n, iso_nw, iso_ne. Lean-to walls at z3 (x11..17), plate (11..17,6,3), lip (10..18,6,2).
* **Fix: raise the lean-to wall one course and kick the catslide foot** (§3.1.4 flare):
  1. Wall up one course:
     * (11..17,6,3) plate becomes infill `pale_oak_planks` (one cream panel per bay, as now);
     * the new plate is `stripped_dark_oak_log[axis=x]` at (11..17,7,3), replacing the `spruce_stairs` course there;
     * the verge ends (10,7,3) and (18,7,3) become air, because the verge now runs on the y8 slab. Keep their
       inverted partners at (10,6,3) and (18,6,3) as brackets.
  2. Delete the lip (10..18,6,2).
  3. Flare, x10..18 on every row:
     * (x,8,3) bottom slab, flush with the front of the (x,8,4) course (surface 8.5);
     * (x,7,2) top slab (surface 8.0);
     * (x,7,1) bottom slab, the lip (surface 7.5).
     * With B1 the first two are `tuff_brick_slab` and the lip is `dark_oak_slab`. In wood they are spruce.
     * Overhang becomes 2 and the lip rises 1.
  4. Rafter tails:
     * move the `spruce_fence` stubs from (13,5,2), (15,5,2) and (17,5,2) to (13,6,1), (15,6,1) and (17,6,1);
     * their tops meet the lip slab's underside exactly, so there is no gap.
  5. Extend the ivy at (12,·,2) and (16,·,2) to y6.
  6. Run QA enclosure for the pantry. The slab at (x,8,3) sits on the new plate, so it should stay sealed.
* **Result:** the lean-to shows plinth + 3 cream courses + plate, against plinth + 2 now. The roof foot curves out, which
  is the "curved roofline" the user asked for. The V5/V11 prototypes only raised the lip, so the real result is better
  than the prototype shows.

### B3. Chimney: goblet crown, and an exposed flame
* **Where:** elev_s, elev_e, elev_w, eye, iso_se, iso_ne. Before and after are in `tmp/critic01r2/chimney_compare.png`
  (V0 vs V6).
* **Fix (current roof):**
  1. Delete all 14 `brick_stairs` of the y15 ring:
     * (6,15,7..11);
     * (7..8,15,7) and (7..8,15,11);
     * (9,15,7), (9,15,8), (9,15,10) and (9,15,11).
  2. Move the campfire from (8,15,9) to **(8,14,9)**. Its east neighbour (9,14,9) is ridge planks, so the flame is walled
     on all four sides.
     * Make (8,15,9) air (flue) and keep (8,16,9) open.
     * The flue column stays x8/z9: (8,15,9) and (8,16,9) are open; (7,15,8..10), (8,15,8) and (8,15,10) stay
       `bricks`.
     * Smoke rises from 2 below the rim, inside §3.1.11's 1–3 rule. Check that it clears.
  3. Keep the rim at y16 and the pots at y17. Optionally make one pot a `decorated_pot`.
  * Result: a slim 2×3 shaft from y12 to y16 above the stair shoulders. It is no longer top-heavy (V6).
  * If improvement #1 is done, everything sits one lower: campfire (8,13,9) (east neighbour (9,13,9) is `bricks`),
    flue (8,14..15,9), rim y15, pots y16.
  * Do **not** go 3×3 above the roof. V4 shows it reads as a brick tower.

### B4. The NE tree is a wedding cake with a flat underside
* **Where:** iso_se, iso_ne, elev_s and elev_e (right side), `tmp/critic01r2/01_cozy_starter_cottage_c_tree.png`.
  Canopy x21..27 / z1..7, y8–11, trunk (25,3..4,4) → (24,5..8,4).
* **Fix:** rebuild the canopy as a dome (§5.4).
  * Target layer counts: y7 fringe 6–8, y8 about 22 (corners cut), y9 about 36 (widest, 2 lobes), y10 about 28, y11
    about 14, y12 3–4.
  * Generate it from an ellipsoid centred near (24, 9.5, 4) with radii about (3.6, 2.2, 3.4), with seeded ±0.6 jitter
    on the radius per cell. Keep 20% `flowering_azalea_leaves` and the rest oak + azalea, `persistent=true`.
  * Hang the fringe at irregular spots, e.g. (21,7,5), (22,7,6), (26,7,2), (27,7,4), (26,7,6) and (23,7,1). Cut the 8
    corner cells of y8.
  * Hide the branch tips:
    * put leaves on (24,7,1..2) and (23,7,2) around the stub (24,6,2);
    * give (25,7,2), which touches only diagonally, a leaf at (25,7,1) and (26,7,2), or delete it.
  * Root flare: 1-long `oak_log` stubs at (26,3,4)[axis=x] and (25,3,5)[axis=z], plus `rooted_dirt` and `moss_carpet`
    around them.

---

## 3. Top 8 improvements (after the blockers), ranked by visual impact

1. **45° tops: every ridge drops one course** (prototype V4/V11, `reshape.py`). This removes the board risers, makes the
   south roof:wall 6:6, and lets the chimney stand clear.
   * **Main roof, x10..18:**
     * (x,12,8) planks → `dark_oak_stairs[facing=south]`, and (x,13,8) → air;
     * (x,12,10) planks → `[facing=north]`, and (x,13,10) → air;
     * (x,13,9) → `dark_oak_planks` (ridge core; it replaces the chains at (11,13,9) and (16,13,9), and the lanterns
       now hang from y12);
     * (x,14,9) → the cap slab, and (x,15,9) → air.
   * **x9:** the same, with the cap at (9,14,9). The rod moves from (18,15,9) to (18,14,9).
   * **Hip (x19):**
     * (19,13,8) and (19,13,10) → air;
     * (19,12,8) → `[facing=south]` and (19,12,10) → `[facing=north]`;
     * keep (19,13,9) as the hip top and rerun `blockwright.resolve`.
   * **Wing:**
     * (14,11,11..16) → `dark_oak_stairs[facing=east]` and (16,11,11..16) → `[facing=west]`;
     * (14,12,·) and (16,12,·) → air;
     * the ridge log moves from (15,13,11..16) to (15,12,11..16), replacing (15,12,11) planks and the (15,12,16)
       calcite;
     * the cap moves from (15,14,11..16) to (15,13,11..16);
     * barge boards (14,12,17)/(16,12,17) move to (14,11,17)/(16,11,17), and (15,12,17) moves to (15,11,17).
   * **Dormer**, one course lower:
     * glass only at (16,10,6) with `calcite` at (16,11,6);
     * roof stairs at (15,11,5..7) facing east and (17,11,5..7) facing west (the front pair in the trim material);
     * ridge log (16,12,5..8);
     * delete (14,11,5..6), (18,11,5..6), (15..17,12,5..7) except the log, (16,13,5..8) and (16,14,5..7);
     * reset (14,11,7) and (18,11,7) to main-slope stairs facing south.
   * The dormer ridge is now 2 below the main cap, meeting §3.1.10.
   * Loft headroom stays at 3 (z7/z11), 4 (z8/z10) and 5 (z9). Run QA enclosure on the wing valley at z11.
2. **The wing apex "horn".** At z17 the inverted stair (15,12,17), the planks (15,13,17) and the slab (15,14,17) stack
   2.5 blocks above the verge stairs. In the eye view and elev_s it is a vertical spruce post on the gable tip.
   * End the cap at z16: (15,14,17) → air.
   * (15,13,17) → `spruce_slab[type=bottom]`, a half-height apex cap.
   * Keep (15,12,17) as the corbel.
   * Optionally use a `waxed_lightning_rod` at (15,13,17) instead of the slab, as a slim finial (H05 accent). After
     #1, everything sits one lower.
3. **Free the transom.** The lantern (15,6,13) hangs directly in front of the transom glass (15,6,12) and pairs with
   (16,6,16) at the same height, one block apart in the front view. Move it to **(14,6,13)** (it hangs from the porch
   ceiling (14,7,13)). The two lights are then staggered and the 3×3 door surround reads. Recheck H15 in the recess.
4. **North eyebrow over the vault.** It breaks the north field and mirrors the south one.
   * `glass_pane` at (11..13,10,6), replacing the `dark_oak_stairs`.
   * Arch: `dark_oak_stairs[facing=east,half=top]` at (11,11,6), `dark_oak_slab[type=top]` at (12,11,6), and
     `dark_oak_stairs[facing=west,half=top]` at (13,11,6).
   * The cells behind, (11..13,10,7), are vault air.
   * Also add the missing `white_candle[candles=2,lit=true]` on the south eyebrow's inner sill (R1 #7).
5. **Pond: from a 13-cell lozenge to an asymmetric bean of about 17 cells**, running NW→SE.
   * Add water at (7,2,15), (8,2,17) (now mud), (7,2,18) and (6,2,19).
   * Replace the bare `dirt` at (3,2,15), (4,2,15) and (3,2,17) with `moss_block` or grass + `short_grass`. Keep at
     most one mud cell on the path side.
   * Keep the boulders at the tips and the reeds. QA must still report 0 uncontained fluid.
6. **Path corners.** The track is 2 wide but steps in 4–6-long rectangles (z17 x16..19, z18 x15..19, z19 x11..16,
   z20 x7..10 and x12..14, z21 x4..10).
   * Fill the notch (11,2,20) with `dirt_path`.
   * Bridge the diagonal steps with `coarse_dirt` at (10,2,19) and (17,2,19).
   * Add `rooted_dirt` at (3,2,21).
   * Put 2 grass bites with `short_grass` on the outer edges: (19,2,17) and (7,2,20).
   * The goal is a band whose edge never runs straight for more than 4.
7. **SE lawn, cart and scarecrow restraint.** The hay plus composter cart at (20..21,3..4,21..23) and the
   pumpkin-headed scarecrow (26,4..5,20) are the most saturated objects in elev_s and the eye view. They pull the eye
   away from the door.
   * Swap the cart's `hay_block` (20,4,22) for `barrel[facing=up]`.
   * Add a 2–3-cell `wildflowers` / `bush` drift joining the cart to the veg-patch fence, so it stops floating on the
     lawn.
8. **If the ridge still reads flat after #1, clip the jerkinhead one more course.** The ridge would end at x17, with hip
   courses at x18 and x19. elev_s and elev_n then get a 3-step east shoulder instead of a 10-block bar. The 1×2 east
   window at (19,10..11,9) stays below the hip.

---

## 4. What must be kept

* **The plan:**
  * catslide north and an off-centre jettied cross-gable south;
  * the exterior gable chimney west, the woodpile lean-to east, and the half-hip;
  * 24 convex / 20 concave corners. Change skins and tops, not the footprint.
* **The front gable:**
  * cream jetty (14..16,8..12,16) with the window and the azalea box (15,8,17) on its corbel;
  * end/corbel/end joists at y7 z16;
  * the pale-oak round-head arch (14,6,15)/(16,6,15);
  * the porch with bench (14,4,13..14), barrel + potted azalea, transom, step with cobble cheeks, and peonies flanking
    it.
* **The bay:** (10..12,5..7,13), with its cream frieze, pale box and window seat inside.
* **Pale-oak hardware and the 2/1/0 shutter rhythm.** The east kitchen window with its box and the east gable 1×2 with
  pale shutters.
* **Course-aligned weathering logic.** Port it to the new field material. Also keep the continuous trim frame (verge +
  eave + ridge), now in dark oak on the main roof and spruce on the wing.
* **North lean-to dressing:** cream panels under a dark plate, quoins, the two ivy strands, the pantry window with its
  pale sill, rafter tails and the NW azalea tuck.
* **The chimney base gradient:** rubble base, moss only low on N/W, one toothing course, clean brick above, stair
  shoulders at y12. Keep the working-smoke principle: the top campfire one to three below an open rim, with open air
  above.
* **The interior:**
  * inglenook with mantel candles, armchairs and the barrel side table, the rug;
  * bookcase wall with chiseled bookshelf and lectern;
  * vault with chain lantern;
  * stone kitchen strip with cauldron sink, smoker and crafting table;
  * the pantry, the loft desk under the dormer, and the bed nook in the jetty;
  * QA: sealed, reachable, lit.
* **Landscaping:**
  * the continuous-track idea and the colour drifts (daisy and dandelion leads, cornflower, allium and pink tulip
    accents);
  * the flowering-azalea shrubs at the SW/SE corners;
  * the veg patch with its lily-pad hydration hole, the lamp post at the path mouth, the old fence line;
  * the NE tree's position (reshape the canopy only), and the pond's reeds and boulders.
