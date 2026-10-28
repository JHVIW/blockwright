# 01 Cozy Starter Cottage: critique, round 1

Reviewer: independent judge pass (no build files edited).
Sources: every render in `out/previews/01_cozy_starter_cottage/`, my own close-ups in `tmp/critic01/`
(`c_roof_se`, `c_catslide_n`, `c_entrance`, `c_bay`, `c_chimney`, `c_east`), block dumps of the `.litematic`, the
QA report, the builder log and `docs/design-guide.md`.

**Coordinates.** All coordinates are schematic coordinates (x east, y up, z south; ground `g` is y=2, so the floor
is y=3). The build script uses plan coordinates, which are **schematic minus (6, 2, 2)**. Example: the door at
schematic (15,4,12) is script (9,2,10).
Landmarks: main walls x9..19 / z6..12, plate y8, ridge planks y13 + cap y14 on z9. Front wing (porch + jetty)
x13..17 / z13..16 (jetty face z16), wing ridge log y11 on x15. Catslide lean-to x11..17 / z3..5, lip y5 on z2.
Chimney base x5..8 / z8..10 (y3..6), stack x6..8 / z8..10 (y7..15). East gable x19, verge x20. North shed dormer
x14..19, face z6.

---

## Verdict on the lead's first impression

| claim | verdict | evidence |
|---|---|---|
| Roof is a heavy dark mass that hides the walls on S and N | **N: confirmed. S: partly.** | I counted the first visible block per cell in each elevation, ignoring plants. **North:** 54% roof, 0% plaster. The catslide hides the walls by design, and the only wall that shows is a 2-course stone strip. **South:** 45% roof. The roof-to-wall height is about 1.2, inside the guide's 0.9–2.0 band for one storey. The roof looks oversized because it has the same value as the walls: dark posts, dark trapdoors and a spruce porch. Nothing light separates the roof from the walls. |
| The lighter roof patches read as noise | **Confirmed.** | `roof_wood()` uses `value3(scale=1.6) > 0.76`, which makes isolated 1–2-cell spruce blobs. They follow no eave, verge or course. The worst are on the ridge itself: (11,14,9) is a spruce_slab, and (17,13,9) + (17,14,9) are spruce. These show as two pale rectangles at the very top of elev_s and elev_n. There is also an L-shaped pale patch at the top-left of elev_n. |
| The palette is monotone brown, with no cream plaster and little flower colour | **Strongly confirmed.** | Visible plaster: S 3%, N 0%, E 5%, W 6%. Dark roof plus dark timber: S 62%, N 64%, E 69%, W 46%. There are 90 plaster blocks in total, but about 35 sit on the north main wall inside the pantry, and the east gable's plaster is boxed in at x20. The garden has about 27 flower cells, all white or yellow. |
| Window count and variety are low | **Refuted on count, confirmed on readability.** | There are 8 openings of 6 kinds: a 3×2 window, a 3×1 eyebrow, three 1×2 windows, a 2×2 kitchen window, a 2×2 dormer, 1×1 windows and a transom. That is enough. They don't read because every one is dark glass in a dark frame with a dark shutter or none. Every window has exactly 1 spruce shutter, which looks like a missing shutter rather than a choice. |

---

## 1. Scores (1–10)

| category | score | one-line reason |
|---|---|---|
| Silhouette & massing | **5** | The plan is right: catslide, off-centre wing, gable chimney and woodpile lean-to, with 22 convex corners. But elev_s and elev_n each read as a flat-topped rectangle plus a chimney, because the wing apex stays inside the main roof outline. |
| Roof | **4** | Good techniques (2-thick spruce verges, catslide, valleys, working smoke). Against that: a monotone surface, speckle noise on the ridge, the eave lip and verge in different woods, a flat-lidded 6-wide dormer and a grey stripe on the catslide. |
| Facade depth & detail | **5** | It has a jetty, a recessed porch, flower boxes, a rain chain and lanterns. The depth doesn't show because every L+1 element is dark wood. The "bay" is a flush window, and the east gable reads as a face. |
| Materials & colour | **3** | Brown on brown. The P1 cream plaster is practically absent outside. The chimney is pocked with random grey squares, and white_terracotta reads pink next to calcite. |
| Entrance | **6** | A recessed porch under a jettied gable, with a hanging lantern, step, bench, barrel, potted azalea and transom: a real composition. But it's a dark hole in the eye view, the jetty plaster is split grey/pink, and there's no arch or light trim. |
| Interior | **6** | Inglenook with a mantel and candles, armchairs facing the fire, bookcase wall with a lectern, vault with a tie beam and chain lantern, sink/smoker/counter, table for two, 2-wide arch to the pantry, railed loft, and a bed nook in the jetty. It's cramped (the living area is 3–4 wide), very dark-wood-heavy, and has 10 barrels. |
| Landscaping | **5** | The pieces are good: pond, vegetable patch with a hydration hole, scarecrow, cart, orchard tree, bench, lamp post. But the path is a patchwork of 1×1 tiles, the pond is a rectangle in a dirt frame, flowers are sparse and single-tone, and a lot of the lawn is bare. |
| Would a talented builder be proud of it? | **4** | The bones are good: the right volumes and an honest interior. From any elevation, though, it reads as a dark wooden box with a lid and some stuff around it. |

---

## 2. BLOCKERS (things that would make the user say "this looks AI-generated")

### B1. Brown on brown: no cream plaster or light trim where anyone can see it
* **Where:** every elevation, worst in elev_e, elev_s, eye and iso_ne. The porch cheek walls show pink white_terracotta
  in cut_1 and iso_se.
* **Why it fails:** P1 is "dark timber, cream plaster". The frame-vs-fill contrast rule (§2.2, ΔL ≥ 50) is met
  nowhere outside. Every element that projects to L+1 is dark: spruce shutters, spruce sills, spruce box fronts,
  dark oak posts, dark slab hoods. So the depth that exists doesn't cast readable shadow lines.
* **Fix:**
  1. East gable: reveal the plaster that is already there. See B4.
  2. Make the front jetty face (z16) one cream panel. Set (15,8,16) and (16,8,16) mushroom_stem to
     `pale_oak_planks`, and (16,9,16) white_terracotta to `pale_oak_planks`. It's currently split grey on the left
     and pink on the right.
  3. Make the porch cheeks (x13 and x17, z13..14, y4..8) one material per panel: `pale_oak_planks` for y5..8 and
     `mushroom_stem` only at y4. Replace every white_terracotta in (17,5..9,13..15) and (16,5..6,12) with
     `pale_oak_planks`.
  4. Script rule: in `plaster()`, choose **one infill per framed panel** (seed the noise by panel id, not per cell).
     Use `calcite` only at y ≥ 9, and `white_terracotta` only in the lowest infill course (y4). Small panels made of
     2–3 different whites look like mistakes.
  5. Light hardware:
     * Change the shutter trapdoors (8,5..6,12), (19,5..6,13) and (20,5..6,6) from `spruce_trapdoor` to
       `pale_oak_trapdoor`, keeping the same states.
     * Change the sills (8,4,11), (18,4,13) and (18,4,5) from `spruce_trapdoor[half=top]` to
       `pale_oak_trapdoor[half=top]`.
     * A white sill and shutter line on dark timber is the classic Tudor cue, and it makes the 8 windows visible.
  6. North dormer face gets plaster (B3).
* **Target:** plaster ≥ 10% of the S and E projections and ≥ 5% of N. Cream must be visible on the jetty and on
  both porch cheeks in the eye view.

### B2. The roof surface reads as noise and its outline is only half drawn
* **Where:** elev_s and elev_n (top band), iso_se, c_roof_se.
* **What:**
  * The spruce speckle is per-cell static (scale 1.6). It even lands on the ridge cap: (11,14,9) spruce_slab, and
    (17,13,9) + (17,14,9) spruce.
  * The verges are light spruce while the eave lips are dark oak, so the roof plane has no consistent border:
    * dark_oak_slab at (9..11,8,13) and (19,8,13);
    * on the north lip, dark_oak_slab at (11..17,5,2).
  * The two full plank rows of the 63° part (y11 on z10/z8, y13 on z9) run the whole length (x9..20) and read as
    stacked boards.
* **Fix:**
  1. Ridge as a deliberate light line:
     * (9..19,14,9) all `spruce_slab[type=bottom]` (P1 allows a spruce ridge);
     * (9..19,13,9) all `dark_oak_planks`.
     * If you do improvement #3, the ridge ends at x18.
  2. Eave lips in spruce, matching the verges:
     * (8..11,8,13) and (19..20,8,13) → `spruce_slab[type=bottom]`;
     * (11..17,5,2) → `spruce_slab[type=bottom]` (x10 and x18 are already spruce).
     * The roof then has a continuous light frame (verge + eave + ridge) around a dark field. Good cottage roofs
       look like this.
  3. Replace `roof_wood()` with a **weathering gradient**:
     * p(spruce) ≈ 0.30 on the lowest 2 courses and on the course next to each verge, 0.10 mid-slope, and 0 on the
       top 2 courses, the ridge and the 63° block row.
     * Stretch the noise along the course (scale ~4 along x on the main slopes and along z on the wing, ~1 across
       courses). Repairs then become 3–5-long runs one course tall, never 2×1 vertical blocks.
     * That is §3.1.14 ("speckle each course with the same rule, so patches look like repairs").

### B3. North elevation: a 13×10 brown ramp with a glitch stripe and a boxy lid
* **Where:** elev_n, iso_nw, iso_ne, c_catslide_n.
* **What:**
  * **Grey stripe.** The lip at (10..18,5,2) is bottom slabs. The upper half of the cobble lean-to wall top
    (11..17,5,3) shows above it as a half-block grey stripe across the roof, with polished_andesite end caps at x11
    and x17. It reads as a gap or render error.
  * **Boxy dormer.** The shed dormer is 6 wide (x14..19) and runs flush into the east gable plane (x19). It has a
    flat slab lid (x14..19, y11, z5..6), and its face is dark planks around 2×2 glass. In iso_ne it is a
    flat-topped box. Guide §3.1.10 says dormer faces are set back and have a real pitch.
* **Fix:**
  1. Change (11..17,5,3) to `stripped_dark_oak_log[axis=x]` (a wall plate) and make the lip spruce (B2.2). The
     stripe becomes a shadowed eave line.
  2. Rebuild the dormer as a **3-wide gable dormer centred on x16**, ≥ 2 in from the east gable:
     * posts `dark_oak_log` (15,9..10,6) and (17,9..10,6);
     * `glass_pane` (16,9..10,6), with a `pale_oak_trapdoor[half=top]` sill at (16,8,5);
     * `calcite` in the dormer gable at (16,11,6);
     * roof stairs facing the dormer ridge at x14/x18 on y10 and x15/x17 on y11, running from z5 back until they
       die into the main slope;
     * ridge (16,12,5..8) with a `spruce_slab` cap. That is ridge y12 against the main y13/14, so H02 is OK.
     * Remove the old lid (14..19,11,5..7) and restore the plain catslide courses at x18..19.
     * Loft headroom at z7 is still 2 (y8–9).
  3. Add a 1×1 pantry window: `glass_pane` at (14,4,3). The lip above acts as its hood.

### B4. The east gable reads as a face, with crates under it
* **Where:** elev_e, c_east, iso_se (right end).
* **What:**
  * At x20 there is a 3×3 ring of dark planks and stairs, (20,8..10,8..10), around the 1×1 pane (19,9,9). Two
    lighter notches over a "mouth" window make a face.
  * The plastered gable at x19, (19,9..12,7..11), is hidden behind it.
  * The woodpile below shows a grid of square log ends (crates).
  * The ridge finial is a 2-block dark post, (20,13..14,9) + rod, that reads as a second chimney stub.
* **Fix:**
  1. Delete (20,8,8), (20,8,9), (20,8,10), (20,9,8), (20,9,10), (20,10,8), (20,10,9) and (20,10,10). Keep all
     spruce verge cells.
  2. Make the window 1×2:
     * `glass_pane` at (19,10,9), replacing pale_oak_planks;
     * sill `pale_oak_trapdoor[half=top]` at (20,8,9);
     * shutters `pale_oak_trapdoor[open=true,facing=east]` at (20,9..10,8) and (20,9..10,10).
  3. Make the gable lighter upward: (19,11,9) mushroom_stem → `calcite`, and (19,12,9) white_terracotta →
     `calcite`.
  4. Finial: delete the vertical log (20,14,9) and put `waxed_lightning_rod` at (20,14,9) on the beam end (20,13,9).
  5. Woodpile (x20..21, y3..5, z9..11): turn about a third of the logs to `axis=z` so bark sides show, and use
     `birch_log` ends for 2–3 cells. This breaks the crate grid.

### B5. Chimney: random grey squares, a lopsided hat and a tower-like shaft
* **Where:** c_chimney, iso_sw, iso_se, elev_s, elev_w.
* **What:**
  * Stone_bricks cells are sprinkled through the brick band: (6,12,8), (6,13,8), (6,13,10), (6,14,8), (6,15,8)
    and (7,12,10). There is also a cracked cell at (8,14,9) and a stone_brick block at (7..8,8,10) + (7,9,10).
    They read as missing textures, not soot.
  * The brick_stairs crown at y14 wraps only the W, N and S sides ((5,14,8..10), (6..8,14,7), (6..8,14,11)). In
    elev_s and elev_n it juts out on one side only.
  * The 3×3 shaft rises from y7 to y15 without a taper. The guide asks for a 2×2 or 3×2 stack that tapers (§1.3,
    §3.1.11).
* **Fix:**
  1. Set all the grey cells listed above at y ≥ 9 to `bricks`. Make y7–y8 a 2-course dither (y7: about ⅔ cobble /
     ⅓ brick, y8: the reverse) instead of stone-brick squares. Moss only at y3–4, on the N and W corners.
  2. Taper above the eave:
     * remove the west column (6,11..15,8..10);
     * put `brick_stairs[facing=east,half=bottom]` shoulders at (6,11,8..10).
     * The stack becomes 2×3 (x7..8). The flue moves with it; see step 4.
  3. Crown as a full ring around the 2×3 at y14, all `brick_stairs[half=top]`:
     * (6,14,8..10) facing=east;
     * (7..8,14,7) facing=south and (7..8,14,11) facing=north;
     * (9,14,8) and (9,14,10) facing=west. The ridge slab fills (9,14,9).
     * Delete the old (5,14,8..10), (6,14,7) and (6,14,11).
  4. A 1×1 flue in a 2-wide stack has to sit on an edge, so move the top campfire from (7,14,9) to (8,14,9). The
     block under it, (8,13,9), is bricks. (7,14,9) becomes bricks.
     * Rim at y15 in bricks: (7,15,8..10), (8,15,8) and (8,15,10). Leave (8,15,9) open, with open air above.
     * Pots at (7,16,8) and (7,16,10).
     * Check that smoke still clears the top.

### B6. Ground: a patchwork path and a rectangular pond
* **Where:** top, iso_sw, iso_se.
* **What:**
  * **Path.** South of the house there are 34 `dirt_path` cells against about 42 one-cell speckle tiles (28
    coarse_dirt, 7 rooted_dirt, 3 podzol, 3 gravel, 1 packed_mud, 1 mud). It reads as a quilt of brown squares, not
    a worn track. This is the "random texture noise" the user hates.
  * **Pond.** The pond is a 5×3 water rectangle (x3..7, z15..17, one notched corner) inside a one-cell coarse/rooted
    dirt frame. That is design-guide anti-pattern 9.
* **Fix:**
  1. Path:
     * a continuous 2-wide `dirt_path` core from the step (14..16,2,17) bending SW to the site exit around
       (3..5,2,21..23);
     * speckle only on the outermost path cells, ≤ 25% of them, using `coarse_dirt`/`rooted_dirt` only (no gravel,
       packed_mud or podzol in the track);
     * let 2–3 grass cells bite into each edge.
  2. Pond as a bean shape:
     * water (5..6,2,15), (3..7,2,16), (4..7,2,17), (5..6,2,18), deepened to y1 under (4..6,·,16..17);
     * banks mostly grass and `moss_block`, with coarse_dirt/mud on only 3–4 cells on the path side;
     * 2 `mossy_cobblestone` boulders at the W and E tips;
     * 2–3 `sugar_cane` on the far (west) bank;
     * keep the water contained as before.

---

## 3. Top 10 improvements (after the blockers), ranked by visual impact

1. **Build the bay window the log promises** (south facade, c_bay).
   * **Now:** the glass (10..12,5..6,12) sits in the wall plane, flush with its posts. The "bay" is only a crate
     planter at (10..12,4,13) under a heavy slab hood at (9..11,8,13).
   * **Fix:**
     * Push the glazing out to z13: new post `dark_oak_log` (9,4..7,13); the wing wall (13,·,13) is the east jamb;
       `glass_pane` (10..12,5..6,13).
     * Sill beam `stripped_dark_oak_log[axis=x]` (10..12,4,13) on a cobble plinth at (10..12,3,13), replacing the
       inverted-stair brackets.
     * Head beam (10..12,7,13). Mini roof `spruce_stairs[facing=north]` at (9..11,8,13), replacing the slab hood.
       (12,8,13) is already the wing's eave stair and covers the east end.
     * Flower box moves to (10..12,4,14), with front trapdoors at z15, on brackets
       `dark_oak_stairs[half=top,facing=north]` at (10,3,14) and (12,3,14).
     * Inside: clear (10..12,4..6,12), floor (10..12,3,12), and move the window seat into the bay.
2. **Make the front gable the hero** (c_entrance, eye).
   * **Porch arch:** `dark_oak_stairs[half=top]` at (14,6,15) facing=west and (16,6,15) facing=east (round-head
     recipe).
   * **Jetty flower box:** a `flowering_azalea_leaves[persistent=true]` box at (15,8,17) on a bracket
     `dark_oak_stairs[facing=north,half=top]` at (15,7,17), right under the jetty window. Pink lands on the focal
     point.
   * **Joist rhythm:** change (15,7,16) from a log end to `dark_oak_stairs[facing=north,half=top]`, so it reads
     end, corbel, end instead of three "crates".
   * **Light the door recess:** `lantern[hanging=true]` at (14,6,13) under the porch ceiling.
   * **Optional ridge:** raise the wing ridge from y11 to y12 (log) with a `spruce_slab` cap at y13, using a
     [block+stair] course at x14/x16. The front gable then climbs nearly to the main ridge in elev_s and breaks the
     flat bar.
3. **Clip the east roof end (half-hip / jerkinhead).**
   * End the ridge at x18 and turn the top two courses at x19..20 (y12..14) into a hip: stairs facing west, with
     resolved outer corners.
   * The spruce verge stops at y11, and the gable plaster stays visible at y9..11.
   * elev_s and elev_n then get a sloped right shoulder instead of a rectangle. That is the "irregular roofline" the
     user asked for, and it removes the stub finial for good (put the rod on the hip apex at (18,15,9)).
   * Alternative: step the ridge down 2 for x18..20 as a lower kitchen end.
4. **Planting density and colour.**
   * Double the flower cells to 55–60, in drifts of 3–5 oxeye_daisy and 3–5 dandelion with wildflowers filler, in
     2-deep strips:
     * S front x8..12 / z15..16 (in front of the new bay box);
     * x18..20 / z13..14;
     * E plinth x22 / z5..8 and z12..13;
     * both sides of the porch step, (13,3,16) and (17,3,16).
   * Add 2 `flowering_azalea` shrubs at the SW (8,3,13) and SE (20,3,14) corners for pink.
   * Optional and noted in meta: 2 `peony` flanking the step.
5. **Light the north slope.**
   * Two `vine[south=true]` strands on the lean-to cobble, at (12,3..4,2) and (16,3..4,2).
   * A 2–3-block `azalea_leaves[persistent=true]` clump tucked into the NW corner where the chimney shades the
     catslide, e.g. (10,4,2), (10,5,1), (11,5,1).
   * Raise the share of mossy_cobblestone in the lean-to's bottom course (y3) to about 50% at the corners.
   * Stone-brick quoins alternating 1/2 at (11,3..4,3) and (17,3..4,3).
6. **Rafter tails under the long eaves.** Add `spruce_fence` stubs under the S eave lip at (19,7,13), and under
   the catslide lip at (13,4,2) and (17,4,2), away from the vines in #5 and the pantry window. Guide §3.1.3 asks
   for one every 2–3 blocks. This gives a dotted shadow line, which the shadow test asks for.
7. **The eyebrow window should read as an eyebrow.** Right now (10..12,9,12) glass under a flat slab row
   (10..12,10,12) reads as a slot. Give it the s–t–s arch from §3.1.10, or lower the slabs at x10 and x12 to
   `dark_oak_stairs[half=top]` facing the window centre. Either way, add a `white_candle[candles=2,lit=true]` on
   the inner sill so it glows.
8. **Break the one-shutter-everywhere pattern.** (18,5..6,12) has a single shutter that reads as missing. Give
   it a `pale_oak_trapdoor[half=top]` sill at (18,4,13) and either a pair of shutters or none. Every window now has
   exactly one shutter. Vary it: 2 / 1 / 0.
9. **Interior warmth and space.**
   * Once the bay exists, the living area gains a seat nook.
   * Put a side table (`barrel[facing=up]` + `white_candle`) between the armchairs at (12,4,9), and shift the rug so
     the centre stays free.
   * Swap 3 of the 10 barrels for other storage (`chiseled_bookshelf`, `dark_oak_shelf`, `decorated_pot`).
   * Pick one floor field material per zone: a spruce field in the living area, and the stone corner (x16..18,
     z7..8) extended to the whole kitchen strip, so the two zones read apart.
10. **Props restraint and the site edge.**
    * The scarecrow's hay plus carved pumpkin at (26,4..5,20) and the cart load (hay + pumpkin at
      (18..19,4,22)) read as saturated orange/yellow cubes from the south.
    * The scarecrow head is `carved_pumpkin[facing=west]`, so from the south and in the eye view it shows a blank
      side. Turn it to facing=south, toward the main approach.
    * Swap the cart's pumpkin for a `barrel` or `composter`, and nudge the cart so its handle touches the path edge.
    * The patch pumpkin (24,3,19) is correctly attached to its stem. Keep it.
    * Thin the lone fade tufts beyond about 5 blocks from the walls, so the garden reads as a composed blob rather
      than a 26×23 lawn.

---

## 4. What already works and must be kept

* **The massing concept:** catslide north, off-centre cross-gabled entrance wing, fat exterior gable chimney,
  woodpile lean-to east. 22 convex / 18 concave corners and three ridge heights is the right skeleton. Change the
  skins, not the plan.
* **Working chimney smoke:** the top campfire (7,14,9) sits one below an open rim with open air above, per
  §3.1.11. Keep that setup when it moves to (8,14,9) in B5.
* **The recessed porch under a jettied gable:** step, porch bench (14,4,13..14), barrel + potted azalea by the
  door, transom (15,6,12), hanging lantern (15,6,16). This is the best area of the build.
* **The 2-thick spruce verges** with inverted partners on the main gables. Extend that look to the eaves and ridge;
  don't remove it.
* **The interior program:**
  * a 3-wide inglenook (9,4..5,8..10) with the fire set back at (8,4,9), a mantel with candles and a potted
    dandelion;
  * armchairs facing the hearth, a rug that isn't wall to wall, a bookcase wall with a lectern;
  * a vault with a tie beam and chain lantern (11,9,9);
  * a kitchen run with a cauldron sink and smoker, a table for two;
  * a 2-wide arched pantry opening (14..15,4..5,6);
  * a railed loft with a desk, and the bed nook in the jetty.
  * QA is clean (lit, reachable, sealed).
* **Story props:** rain chain into a water cauldron (20,3..6,13), kitchen flower box on the east, vegetable patch
  with a lily-pad hydration hole, scarecrow, bench under the orchard tree, lamp post at the path mouth, and a
  coherent W fence line with a wall stub.
* **The NE orchard tree** framing the corner, and the NW azalea clump. These are the right plant scale.
* **Mossy foundation gradient** at the bottom course, and ivy at the chimney base. Subtle, as the guide wants.
