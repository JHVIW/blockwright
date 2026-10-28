# 02 Large Player House ("Brambleworth Farmhouse"): critique, round 1

Reviewer: an independent judge pass. No build files were edited.
Sources:
* every render in `out/previews/02_large_player_house/`
* my own close-ups in `tmp/critic02/` (`entrance`, `entrance_sw`, `spire`, `roof_sw`, `roof_main_s`, `roof_n`, `dormer_n`, `dormer_e`, `west_gable`, `porch_w`, `wing_s`, `east`, `north_low`, `nw_chim`, `tree_se`, `eye_far`, and `int_*` for every floor)
* block dumps and cross-sections of the `.litematic`
* the QA report, the builder log and `docs/design-guide.md`

**Coordinates.** All coordinates are schematic coordinates: x east, y up, z south. The grass is y=2, so the ground floor block is y=3, the upper floor y=8 and the attic floor y=12. Script/log coordinates are **schematic minus (4, 2, 6)**.

Landmarks:

| part | location |
|---|---|
| Main block | x8..24 / z12..19, north wall z12, plate y12. Upper-storey jetty face z20 on x8..13. Bay window z21 on x9..13. |
| Main roof | North eave stair (x,12,11), then 45° to (x,15,14), then the "steep top" plank+stair at z15 (y16..17), then the ridge: a stripped dark-oak log at y18 on z16. South side mirrored. |
| Stair tower | x14..18 / z19..23. Front door (16,4..5,23). Lookout walls y15..18. Brim y19..20. Spire tip y24, plus fence y25 and rod y26. |
| Wing | x18..24 / z20..26. Gable face z26 with a pent skirt at y8 on z27. Ridge log y15 on x21. |
| Lean-to | x13..19 / z7..11. |
| West chimney | x5..7 / z15..17, crown y19..21. |
| Kitchen chimney | x21..22 / z10..12, crown y15..17. |
| Trees (trunks) | SW (3,3,25), SE (28,3,29), NE (29,3,12), N (16,3,2). |

---

## Verdict on the lead's first impression

| claim | verdict | evidence |
|---|---|---|
| The eye-level front view is the strongest: layered, deep, flower boxes, shutters | **Confirmed, with a catch** | The south front has real depth: the jetty, the bay under the jetty, the pent skirt, flower boxes, plum and white shutters, and the plinth. But the eye view reads as a **symmetric triptych**. A dark gable on the left (the dormer at x9..11) and a dark gable on the right (the wing) have finials at almost the same height. They flank a centred grey tower, and a tree bookends each side. |
| The tower sits dead centre in front of the entrance, so the door feels cramped/hidden | **Partly** | The door is *in* the tower's south face at (16,4..5,23), not behind it. The cramping comes from three things: (1) the wing's west wall at x18 projects 3 blocks past the tower face (to z26), so the door sits in an inside corner only 1 block from that wall; (2) the "awning" is a 3×1 slab hood at (15..17,6..7,24); (3) clutter fills the corner: a decorated pot at (15,3,24), white pale-oak trapdoors at (17,4,25) and (17,5,24), and a fence lamp arm at (14..15,4..6,25). The door is spruce, so it is dark on dark grey stone. |
| Very brown; brick reads pink; no light plaster | **Strongly confirmed** | `white_terracotta`: **1 block** in the whole build, a stray at (19,10,12). The "birch plaster" is 108 birch planks, and they read tan (L175), not white. First visible block per elevation, plants ignored: light materials **S 2% / N 3% / E 9% / W 1%**; roof, dark trim and mid-brown timber **S 64% / N 65% / E 66% / W 56%**. |
| The dark-oak patches in the roofs read as random noise | **Confirmed, and worse than that** | `roof_wood()` uses `value2(x+3y, z-2y, scale=1.7) > 0.84`. The scale is near per-cell and the patches are skewed per course, so you get isolated single dark specks. Spruce is L89 and dark oak L47, a ΔL of 42, so they show as static. The bigger dark-oak problem is the **solid** dark areas: (a) the three bottom courses of the main south roof west of the tower, (7..13, 12..13, 20..22), are all dark oak and read as a flat, heavy ledge; (b) the south gable dormer and the wing's east wall dormer are clad in dark oak and read as dark triangles painted on the roof; (c) the spire hips put dark oak at the corners of every ring. |
| The spire and roof slopes look stepped | **Confirmed** | **Spire:** a 7×7 45° brim at y20, a 5×5 ring at y21, a **3×3 full-plank cube** at y22, a 3×3 stair ring at y23, a 1×1 block at y24, then fence and rod. It is a squat wedding cake whose tip is only 6 above the main ridge (y24 vs y18). **Main roof:** the single steep-top step (plank+stair at z15 and z17, y16..17) runs the full 17-block length of both slopes as one horizontal crease, so it reads as a terrace, not a curve. |
| The north elevation is one big brown roof mass | **Confirmed** | In elev_n there is a straight ridge, a straight eave and a straight crease, all 17 long. The lean-to's slab roof adds a second parallel band. Both north dormers sit inside the slope plane, so they read as holes (see B3). |
| Busy composition, no clear hierarchy | **Confirmed for the west half of the south facade and the whole west elevation** | West of the tower, about 9 small pieces compete in a 6×13 area: the chimney with shoulders, the balcony, the porch post, the jetty, the flower box, the plum shutter, the dark ledge, the dark gable dormer and its finial. The wing gable is calm and good. |
| The trees are blocky | **Confirmed** | There are 4 trees with 48–78 leaves each. Their canopies are stacked cuboids with straight 4–6-block faces. The SE tree has a dark notch cut into its trunk. The SW and SE trees bookend the front symmetrically. |

Additional findings the lead didn't list:
* The **east facade is one flat 15-block plane**. The main block's east gable and the wing's east side wall are both at x=24.
* The **west gable doesn't read** as a gable. You can't find a clean triangle behind the chimney.
* The white **pale-oak trapdoor sills** (17 of them) read as white plastic tabs.
* There are **single-block noise patches** on the chimneys and the tower.
* The kids' **beds show through the attic dormer glass** from outside.

---

## 1. Scores (1–10)

| category | score | one-line reason |
|---|---|---|
| Silhouette & massing | **6** | The bones are right: an L-plan, a stair tower, a lean-to, an exterior gable chimney, 3 ridge heights and 37 convex corners. But the N and E elevations read as a box with a lid, the spire is squat, and the eye view is a centred triptych. |
| Roof | **4** | It has verge trims, inverted-stair soffits, valleys and working smoke. Against that: one 2-up crease instead of a curve, a squat stepped spire, dormers sunk into the slope like holes, cheek-log stubs on the roof face, static dark-oak speckle, and a 3-course dark ledge. |
| Facade depth & detail | **6** | The south front is a 7: jetty, bay, pent skirt, flower boxes, varied shutters. The north, east and west are 4s: flat planes, recessed dormers, white tabs, and a jumbled west gable. |
| Materials & colour | **4** | Brown on brown on salmon brick, with a grey tower as a third family in the middle. The guide's plaster is practically absent. Noise: single mud bricks and mossy cobble mid-chimney, a cobble stripe on the tower, one stray white terracotta. |
| Entrance | **4** | It has a step, a transom, a lantern, a path and flowers. But it is a 1-wide dark door in an inside corner under a 1-deep slab hood, with clutter. It has no porch, no presence and no colour. |
| Interior | **7** | A complete, working survival program: enchanting with 15 valid shelves, 6 double chests plus 8 barrels, a workshop with every job block, a kitchen with hood, a bathroom, a spiral stair. Everything is lit, sealed and reachable, and the lanterns hang from beams. Minus points: loud rug and bed colours, beds visible through the dormer glass, a pot as the table centrepiece. |
| Landscaping | **6** | A real farm story: a kitchen garden with a channel, beehives, a laundry line, a well, a woodpile, a hay cart and gradient paths with bends. But the trees are boxy and bookending, coarse-dirt beds are squared off, and large flat lawn gaps fill the 3–6 ring. |
| Would a talented builder be proud of it? | **5** | The program and the south front are genuinely good. The roofs, the colour and the entrance would get it called "AI farmhouse" on PMC. |

---

## 2. BLOCKERS (things that make the user say "this looks AI-generated")

### B1. The squat "wedding cake" spire

* **Where:** every view, worst in `spire.png`, `iso_*` and `eye`. Tower roof x13..19 / z18..24 / y19..26.
* **Problem:** it reads as a stack of rings. The 45° 7×7 brim makes a pagoda hat, then a 3×3 plank cube at y22 and a 1×1 cube at y24. The tip is only 6 above the main ridge, and the dark-oak hip stubs at the corners of every ring make it look studded.
* **Fix:** rebuild it as a slender broach spire using the guide's §3.1.9 "63° with a flare". In the rings below, R0 is the perimeter of the 7×7 (x13..19 / z18..24), R1 the perimeter of the 5×5 (x14..18 / z19..23), R2 the perimeter of the 3×3 (x15..17 / z20..22), and C is (16, *, 21).

  | y | block |
  |---|---|
  | y19 | Keep the inverted-stair soffit under R0 (facing in). |
  | y20 | R0: stairs facing in (the only 45° course, the flare kick). Inside R0: planks (the lookout ceiling). |
  | y21 | R1: full blocks (the riser). |
  | y22 | R1: stairs facing in. |
  | y23 | R2: full blocks. |
  | y24 | R2: stairs facing in. |
  | y25–26 | C: two full blocks (the needle). |
  | y27 | `dark_oak_fence` |
  | y28 | `lightning_rod` |

  * The tip ends 2 higher and the outline is a clean 2:1 from R1 up.
  * **Use one field material, with no speckle.** Option A, recommended: `waxed_weathered_cut_copper_stairs` + `waxed_weathered_cut_copper` in the field. It is the single cool accent this all-brown house is missing, and it makes the tower the clear hero. Option B, palette-pure: `dark_oak_stairs`/`dark_oak_planks` in the field, which makes the cap darker than the spruce roofs.
  * **Hips:** the 4 corner columns of every course are the trim stair (`dark_oak` on copper, `spruce` on dark oak), resolved to `outer_*`, so each hip is one continuous diagonal line, not a stub per ring.

### B2. No light plaster: the whole house is brown

* **Where:** all elevations. Upper-storey infill on the jetty x8..13 z20 y9..11, the north upper wall z12 y9..11, the east gable x24 y12..17, the west gable x8 y12..17, the wing south gable z26 y9..14, and the lookout walls x14..18 z19..23 y15..18.
* **Fix:**
  1. **Change `infill_at()`** to:

     | material | share | placement |
     |---|---|---|
     | `pale_oak_planks` | 40% | |
     | `white_terracotta` | 30% | |
     | `calcite` | 15% | upper rows / gable apexes |
     | `birch_planks` | 15% | only the course directly above each floor beam: weathering, darker at the bottom |

     Use value noise at scale 3–4 and keep `stripped_birch_log` only as horizontal boards in gable apexes. This gives the dark oak-log frame the ΔL ≥ 90 it needs to read as half-timbering.
  2. **Dark oak only as trim, never as fill.**
     * The main south roof west of the tower: change (7..13,13,20) and (7..13,12,21) from `dark_oak_stairs` to `spruce_stairs`. Only the outer lip (7..13,12,22) stays dark oak.
     * The dormer gables (B3) get plaster, not dark-oak planks.
  3. Remove the stray `white_terracotta` at (19,10,12). Once the infill is light it will belong.

### B3. Dormers read as holes cut into the roof, with stubs standing on the roof face

**Where:**
* `dormer_n.png`, `roof_n.png`, `nw_chim.png`. The north shed dormer:
  * glass at (16..18,13..14,13), behind the main eave course (15..19,13,12), which hides the lower half of the glass;
  * `oak_log` cheeks at (15,13..14,13) and (19,13..14,13), whose log ends stick up out of the slope;
  * a slab roof at y15..16 on z12..14, only half a block above the main slope.

  It reads as a slot with two posts, not a dormer.
* `dormer_e.png`, `elev_e`: the wing's east wall dormer at about x24..25 / y10..14 / z22..24. Structurally it already is a small gable, but its triangle and roof are `dark_oak_planks`/`dark_oak_stairs` with a 1×1 window and a white trapdoor sill. It reads as a dark ghost gable painted on the slope.
* `elev_s`, `roof_main_s.png`: the south gable dormer at x9..11 / z18..21 (glass (10,13..14,19), ridge log (10,16,18..20)) is a dark triangle, and the attic beds show through its glass.

**Fix:**
* **North:** replace the shed dormer with a **5-wide gabled wall dormer**, face in the north wall plane z12 at x15..19 (rising through the eave above the lean-to). This also breaks the 17-long north eave and ridge rectangle.
  * Face: `oak_log` posts (15,13,12) and (19,13,12) continuing the wall posts; glass 3×2 at (16..18,13..14,12); king post `oak_log` (17,15,12). Remove the old cheeks, the glass at z13 and the slab roof.
  * Roof: one stair course per row, each running from the verge at z11 back until it meets the main slope:

    | columns | block | runs |
    |---|---|---|
    | x14 / x20 | `spruce_stairs[facing=east]` / `[facing=west]` at y13 | z11 |
    | x15 / x19 | `spruce_stairs` facing east / west at y14 | z11..13 |
    | x16 / x18 | `spruce_stairs` facing east / west at y15 | z11..14 |
    | x17 | ridge `stripped_dark_oak_log[axis=z]` at y16 | z11..15, dying into the main slope's plank at z15 |

  * The ridge is 2 below the main ridge (y18). The main-roof stairs it cuts become valley stairs.
  * Verge: z11, with inverted `dark_oak_stairs` underneath.
  * Keep the existing dark-oak eave stairs at (15..19,12,11) as a drip skirt under the face.
  * Inside, the attic gets a real window. Put a chest or window seat under it, not a bed.
* **Wing east dormer:** keep the geometry and fix the cladding.
  * Gable triangle: plaster (B2).
  * Frame: `oak_log` posts at both sides of the window.
  * Window: 1×2 instead of 1×1, with `spruce_trapdoor` shutters at x25 facing east.
  * Dormer roof: `spruce_stairs`. Dark oak only as the verge, with inverted partners.
  * Delete the white `pale_oak_trapdoor` sill.
* **South gable dormer:** delete it and continue the spruce slope (see improvement 4). If it must stay, re-clad it the same way as the wing dormer.

### B4. Static noise instead of gradients

**Where:**
* Roof speckle on every slope: `top.png`, `iso_*`.
* West chimney: a lone `mossy_cobblestone`/`mud_bricks` mid-shaft at about (5..7,11..12,15), visible in `porch_w.png` and `elev_w`. Tan `mud_bricks` singles show on both chimney faces.
* Kitchen chimney: a multi-course `mud_bricks` band at about y9..15 plus a single `cobblestone` at (21,13,11), visible in `nw_chim.png`.
* Tower south face: a vertical `cobblestone` stripe at (14,9..10,23) and cobble pairs at (17..18,14,23), visible in `eye` and `entrance_sw.png`.

**Fix:**
* **Roof:** speckle along courses, not as static. Use `value2(x, z, scale≥3.5)` with no per-course skew, at about 8%. Apply it as 2–4-cell horizontal "repair strips" lying in one course, 3–5 strips per slope. Never put speckle on verges, ridges, dormers or the spire.
* **Chimneys:** weather only at the base and the roof line, per guide §3.1.11.
  * West chimney: the bottom 4 courses (y3..6) are `stone_bricks`/`mossy_stone_bricks`/`cobblestone`, continuing the plinth. Above that, bricks with at most 10% `mud_bricks` as vertical 2-block pairs at the edges. Make the 2 courses just above the roof exit sooty (`cobblestone` 30%).
  * Kitchen chimney: one material (`bricks`) from y3 to the crown.
* **Tower:** replace the stripe with clean `stone_bricks`. Put weathering into the corner quoins instead (improvement 3).

### B5. The entrance is hidden, dark and cluttered

* **Where:** `entrance.png`, `entrance_sw.png`, `eye`. Door (16,4..5,23); the inside corner x14..17 / z24..26 between the tower face (z23) and the wing's west wall (x18).
* **Remove:** the 1-deep hood (15..17,6..7,24); the lantern (16,6,24); the fence lamp arm (14,4..6,25), (15,6,25) and its lantern (15,5,25); the decorated pot (15,3,24); the white trapdoors (17,4,25) and (17,5,24).
* **Build a small gabled timber porch on the door axis:**

  | element | spec |
  |---|---|
  | Deck | x14..17 / z24..26 at y3 in `polished_andesite` + `stone_bricks`, with `mossy_stone_bricks` on the exposed outer edge. Walking level y4 = the threshold. |
  | Steps | `stone_brick_stairs[facing=north]` at (15..16,3,27), plus outward-turned stairs at (14,3,27)[facing=east] and (17,3,27)[facing=west] so the step flares into the path. |
  | Post and beam | One `oak_log` post at (14,4..6,26). A `stripped_oak_log[axis=x]` tie beam at (15..17,7,26), which replaces the stone-brick stairs at (17,7,25..26). Inverted `spruce_stairs` brackets under the beam next to the post and against the wing wall. The wing wall carries the east side: no second post beside it, which would be the FFF rule. Clear height under the beam is 3 (y4..6). |
  | Roof | A gable on x14..17, ridge N–S on x16. West slope: `spruce_stairs[facing=east]` at (14,7,24..27), resting on the post top, and (15,8,24..27). Ridge: `stripped_dark_oak_log[axis=z]` at (16,9,24..27). East slope: `spruce_stairs[facing=west]` at (17,8,24..27), against the wing wall. Where it overlaps, the porch roof replaces the tower's stone string course at (15..17,8,24). Verge on z27 in `dark_oak_stairs` with inverted partners. Gable infill (16,8,26) in plaster (B2). |
  | Door | `crimson_door` (plum, matching the crimson shutters) instead of the spruce one. This is the focal colour accent of the front. Keep the transom glass at (16,6,23). |
  | Dressing | A `lantern[hanging=true]` on an `iron_chain` under the ridge at (16,8,25). A bench on the west side at (14,4,24..25): `spruce_stairs` with `spruce_trapdoor` arms. Two potted plants at the step ends. Keep x15..16 clear: a 2-wide approach. |

### B6. Boxy, bookending trees

* **Where:** `eye`, `tree_se.png`, `iso_se`. SE tree trunk (28,3,29), canopy x24..30 / z25..31 / y7..11, which touches the wing corner. SW tree trunk (3,3,25), canopy x2..5 / z23..28.
* **Fix:**
  * **Placement:** move the SE trunk 2–3 farther out, to about (30,3,31), so its canopy clears the wing by ≥ 2 and stops mirroring the SW tree. Better still, swap it for a small flowering tree (`flowering_azalea_leaves` canopy, 3-tall trunk) and keep the big oak only on the SW.
  * **Rebuild every canopy:**
    * **Trunk and branches.** The trunk is 3–4 tall and must not be notched: replace the dark notch on the SE trunk with log. Add 2–3 `oak_log` branches with axis x or z, 2–3 long, each rising 1 per 2 blocks.
    * **Leaf blobs.** Each branch ends in a blob of radius 1.5–2.5: drop the 8 corner cells of every 3×3 or 5×5 layer. Offset the blobs 1–2 in height so the top outline is lumpy.
    * **Edges.** On about 20% of the edge cells, hang a 1-block leaf drip below the canopy edge. No straight leaf face longer than 3, and the canopy is at least 1.5× wider than it is tall.
    * **Leaf mix.** Mix the leaves in clumps, not per cell: 70% `oak_leaves`, 20% `azalea_leaves`, 10% `flowering_azalea_leaves`.
    * **Lean.** Give one tree a 1-block lean.

---

## 3. Top 10 improvements (after the blockers), ranked by visual impact

### 1. Turn the single roof crease into a bell-cast curve

* **Where:** both long slopes of the main roof, x7..25; visible in every iso and elevation.
* **Fix:** keep the steep top, but add the guide's §3.1.4 flat kick at the eaves:
  * **North eave:** add a `spruce_slab[bottom]` lip one block out at (7..12,12,10) and (20..25,12,10). Skip x13..19, where the lean-to tucks under. Move the dark-oak trim from the current eave course to that lip only.
  * **South eave:** keep the lip (7..13,12,22) but make the two courses above it spruce (B2).
  * **Verge feet:** at the four verge feet of the main and wing gables, add one extra outward stair on the last step, so the barge boards kick out.
* **Result:** the profile becomes flat lip, 45°, steep top. It reads as a concave curve instead of a terrace with one step.

### 2. Give the flat east facade depth with a back porch

* **Where:** `elev_e`, `east.png`. The x=24 plane from z12 to z26, where the main gable and the wing side are coplanar. The doors are at (24,4..5,18) and (24,4..5,23).
* **Fix:** a farm back porch under a pent roof, covering both doors. It replaces the two lantern brackets over the doors: bracket at (25,6,18|23), lantern at (25,7,18|23), and over the first one also the inverted oak stair at (25,8,18).

  | element | spec |
  |---|---|
  | Deck | `spruce_planks` at (25..26,3,16..25). |
  | Posts | `oak_log` at (26,4..6,16), (26,4..6,20) and (26,4..6,25), with inverted `spruce_stairs` brackets beside each post at y6. |
  | Roof | `spruce_stairs[facing=west]` at (25,8,15..26) and (26,7,15..26), with a `spruce_slab[bottom]` kick at (27,7,15..26). It meets the wing's pent skirt at the SE corner (≈(25,8,27)), so one continuous skirt wraps the wing. |

  Move the hay bales and barrels under it, and hang one `lantern` per door from the roof underside.
* **Optional:** jetty the main east gable's upper storey 1 block out (x25, y9..11, z12..19) on corbels, so the main gable stands proud of the wing.

### 3. Articulate the tower shaft so it reads as masonry, not a silo

* **Where:** `eye`, `entrance_sw.png`, `elev_s`. Tower faces x14..18 / z19..23 / y3..14. It is the centre of the hero view.
* **Fix:**
  * **Quoins:** at the 4 vertical edges, alternate `polished_andesite`/`stone_bricks` in a long-short pattern: 2 courses on the face, 1 on the return.
  * **Battered foot:** `stone_brick_stairs[half=bottom]` facing in, around the base at y3, except at the porch.
  * **Windows:** the west face has three identical 1×2 windows stacked in one column, 4 apart: (14,5..6,21), (14,9..10,21) and (14,13..14,21). This is the "spreadsheet" pattern. Stagger them so they follow the spiral, e.g. z22 → z21 → z20. Make the middle one 1×3 with an inverted `stone_brick_stairs` arch head, and give each a `stone_brick_slab` sill. Shift the south face's 1×2 at (16,10..11,23) to x17, so it isn't on the door axis directly above the transom.
  * **Vines:** one vine run of 3–5 cells starting at the ground on the SW corner, no more.

### 4. Simplify the west half of the south facade so there is one hierarchy

* **Where:** `eye`, `elev_s`, `roof_sw.png`. The area x5..13 / z18..22 / y8..18.
* **Fix:**
  * **Delete the south gable dormer** (x9..11 / z18..21) and continue the spruce slope over it. Attic daylight comes from the new north wall dormer and the eyebrow. This kills the left/right mirror gables, and the eye view becomes copper spire (hero), then the wing gable (second), then the jetty (quiet base).
  * **Balcony:** deepen it from 1 to 2 at x5..7 / z18..19, with a `spruce_fence` rail. Give it a tiny `spruce_slab` shed roof under the main verge, so it reads as a designed loggia, not a shelf.

### 5. Rework the chimneys

* **Where:** `elev_w`, `iso_nw`, `porch_w.png`, `nw_chim.png`. From the NW the two chimneys look like a matched pair of pink pillars with identical stone-brick ring caps.
* **West chimney:** a stone breast at y3..7 on x5..7 / z15..17, in the plinth family. A brick flue above, stepping 3×3 to 2×3 to 2×2 as it does now. Keep the corbelled crown and add 2 chimney pots: `decorated_pot` on two crown corners, leaving the flue open.
* **Kitchen chimney:** make it the slim sister, not a twin.
  * Drop the 3×3 stone-brick ring cap (x20..22 / z10..12 / y15..17).
  * Run the 2×2 brick stack (x21..22 / z11..12) up 2 more courses, to a rim at y19. It then shows just above the ridge line from the south: a small second accent off-centre, not a mirror of the west stack.
  * Crown it with one course of inverted `brick_stairs` facing out, plus a 1-high `brick_wall` "pot" on one corner.
  * Keep the campfire in one of the 4 cells, 1 below the rim and open to the sky. Do not hood it: smoke particles collide with blocks and would die under a hood.
  * Use plain `bricks` all the way (B4).

### 6. Make the west gable legible

* **Where:** `elev_w`, `west_gable.png`. The gable x8 / z12..20 / y12..17 behind the chimney.
* **Fix:**
  * Infill: plaster per B2.
  * Frame: the `stripped_oak_log` plate at y12 as the tie beam, an `oak_log` king post on z16 behind the chimney, and one `oak_stairs` brace on each visible side, around (8,13..14,13..14) and (8,13..14,18..19).
  * Make the verge on x7 one continuous trim (spruce stairs + inverted dark oak) and remove the vertical log "boards" on the lean-to's west end.
* **Result:** the red chimney then stands against a pale triangle framed by dark barge boards. That is the classic exterior gable-stack picture.

### 7. Replace the white plastic-looking sills

* **Where:** `north_low.png`, `east.png`, `nw_chim.png`. 17 `pale_oak_trapdoor[half=top]` sills, for example (10..11,4,11), (20,4,11), (23,4,11), (25,4,14..15), (25,4,21) and (7,4,13).
* **Fix:**
  * On brick or stone walls: `stone_brick_slab[top]` sills.
  * On timber walls: `spruce_trapdoor[half=top]`.
  * Keep pale oak only as the wing's white shutters, where it is an intentional accent.

### 8. Landscaping: fill the flat lawn ring and soften the edges

* **Where:** `top`, `iso_*`. Bare grass in the 3–6 ring on the SE, E and W sides; square coarse-dirt and podzol beds.
* **Fix:**
  * **Shrub masses:** at the house corners and the porch ends, 2–3-block masses (`azalea_leaves` + `bush` + `fern` + `tall_grass`).
  * **Bed edges:** give the beds irregular edges (no straight run over 3, with notches). Edge the front bed with 3–4 loose `mossy_cobblestone_wall`/`cobblestone` stones.
  * **Front path:** where it meets the new porch steps, flare it to 3 wide with `packed_mud`/`gravel` grading into grass.
  * **Seating:** a bench under the SW oak.
  * **Flowers:** keep exactly the current palette (peony, pink and white tulip, plus bush). Repeat it, don't add species.

### 9. North slope finish

* **Where:** `roof_n.png`, `iso_nw`.
* **Fix:**
  * **Eyebrow:** with the gabled wall dormer in place (B3), keep the 3-wide eyebrow at (9..11,14,13) as the second dormer type. Make it read per §3.1.10: a slab arch `s t s` over the glass at (9..11,15,13), and a `spruce_trapdoor[half=top]` sill.
  * **Moss:** add 1–2 small `moss_block` patches of 3–4 cells low on the shady north slope next to the kitchen chimney and the dormer valley. Per §3.1.12 small version: a little natural green on the north side only.

### 10. Interior polish

* **Where:** `int_attic`, `int_up_e`, `int_living`, `int_kitchen`.
* **Fix:**
  * **Attic:** move the pink (9..10,13,15) and lime (9..10,13,17) beds out of sight of the dormer and eyebrow glass, and recolour them `brown_bed`/`light_gray_bed`.
  * **Guest loft:** the yellow/white checker rug becomes `brown_carpet` + `white_carpet`.
  * **Living room:** the pink/magenta rug becomes `red_carpet` + `brown_carpet` + `white_carpet`.
  * **Rug palette:** one family house-wide (brick red, brown, cream). The enchanting room may keep its purple.
  * **Kitchen table:** replace the `decorated_pot` centrepiece at (18,5,16) with 2 `white_candle` + a `potted_pink_tulip`.
  * **Storage hall:** in the empty middle of the 3-wide aisle, add a 1×2 sorting table (`spruce_slab[top]` on `barrel`s) against the east wall. Keep the aisle at least 2 wide.

---

## 4. What already works and must be kept

* **Massing concept.** A brick core, a later cross-wing, a stair tower in the inside corner of the L, a workshop lean-to and an exterior gable chimney. It is asymmetric in plan, with 3 ridge heights; H01, H02 and H05 pass honestly. Don't flatten any of it.
* **The wing's south gable composition**, the best piece of the build:
  * a 3-wide window over a brick apron and a stone-brick plinth;
  * a pent-roof skirt at y8;
  * a 2×2 window with white pale-oak shutters and a flower box in the gable;
  * a finial.

  Only its infill colour (B2) and the verge-foot kick (improvement 1) should change.
* **The jetty**, with corbels and the bay window under it, the crimson shutters on brick, and the flower boxes. Variety without spam (6 window types).
* **Plinth.** A stone-brick plinth with a mossy, cobbly foot. The ground floor is raised, with a step at every door.
* **Working chimney smoke.** Campfires sit one course under open crowns, plus the hearth campfire for glow.
* **Interior program and engineering.** All of it passes QA honestly: sealed, reachable and lit rooms with lanterns on beams, a spiral stair round a core, an enchanting room with 15 valid shelves, a full workshop, a storage hall, a kitchen with a smoker and furnace under a brick hood, a bathroom and a lookout with a cartography table.
* **Farm storytelling.** The kitchen garden with its water channel, beehives, laundry line, well, woodpile shed, hay cart, and the hay door with hoist and hanging bale on the east gable.
* **Paths and flowers.** Gradient dirt-path paths with 3 bends and stepping stones, and the flower discipline (2 leads + filler).
