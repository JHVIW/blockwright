# 02 Large Player House ("Brambleworth Farmhouse"): critique, round 2

Reviewer: an independent judge pass. No build files or build outputs were edited. All prototypes are scratch edits of the
current `.litematic`, in `tmp/critic02r2/` (scripts `proto_roof.py`, `proto_walls.py`, `final.py`, `stats.py`, `qa.py`).

**Coordinates.** Schematic coordinates throughout: x east, y up, z south. Grass is y=2. Script/log coordinates are
**schematic minus (4, 2, 6)**. Landmarks (unchanged from round 1): main block x8..24 / z12..19 (jetty z20), main eave lip
y12 on z10 and z22, main ridge y18 on z16, gable verges x7 and x25. Wing x18..24 / z20..26, gable face z26, verge z27,
eaves x17/x25 at y10, ridge y15 on x21. Tower x14..18 / z19..23, spire axis (16, *, 21). Lean-to x13..19 / z7..11.

## Comparison images (all labelled)

| file | what it shows |
|---|---|
| `tmp/critic02r2/FINAL_A.png` | **current vs palette-pure best vs winner**: eye, elev_s, iso_se, iso_sw |
| `tmp/critic02r2/FINAL_B.png` | same three: elev_n, elev_e, elev_w, iso_nw |
| `tmp/critic02r2/FINAL_C.png` | same three: north-slope close-up, front close-up, iso_ne |
| `tmp/critic02r2/roof_compare_A.png` | R0 current / R1 calm spruce + moss hem / R2 graded dark-oak hem |
| `tmp/critic02r2/roof_compare_B.png` | R0 / R3 slate field / R4 dark-oak field + spruce trims |
| `tmp/critic02r2/roof_compare_C.png`, `slate_trim_compare.png`, `efg_cu.png`, `cmp_eye_0eg.png` | slate edge variants: R3 (timber trims), R3b (all slate), R3c (spruce verge), R3d/R3e (oak barge, slab ridge), R3f/R3g (slate verge, R3g = solid 2-thick slate verge) |
| `tmp/critic02r2/walls_compare_R0.png` | W0..W3 plaster levels on the current roof (the "plaster alone does nothing" proof) |
| `tmp/critic02r2/walls_compare_R3b.png`, `walls_cu.png` | W4 calm wing gable, with and without slate |
| `tmp/critic02r2/spire_compare.png` | spire hips: dark oak (keep) / copper / exposed copper |
| `tmp/critic02r2/cur/cur_elev_s_nosh.png` | current elev_s **without the renderer's sun shadows** (patch evidence) |

The winner, `P2_winner_slate`, passes `blockwright.qa.run_qa` with 0 errors and 0 warnings, and every state parses (`tmp/critic02r2/qa.py`, `val.py`).

---

## Verdict on the lead's impression

| claim | verdict | evidence |
|---|---|---|
| Real progress: copper broach spire as the one cool accent, clear hierarchy, proper porch with crimson door, some plaster, north dormer | **Confirmed** | The eye view is no longer a triptych. The spire is the hero. The porch reads as an entrance. |
| The big spruce planes dominate every elevation | **Confirmed, but not because the roof is oversized** | H04: roof height 6 (y12 to y18) over wall height 9 is 0.67, inside the 2-storey band. The roof dominates because it has the **same value and hue as the walls**. Spruce is L89, the oak posts L88, the brick L108 and the stripped oak L147. On top of that, the projections hide most of the wall. First-visible-block shares for timber of any kind: **S 63 % / N 61 % / E 68 % / W 55 %**. |
| Visible darker rectangular patches read as noise | **Partly refuted** | On the main **south** slope there are **no repair strips** (see `cur_elev_s_nosh.png`). The dark rectangles there are the renderer's sun shadow (spire, chimney, wing ridge) plus the dark-oak lip and verge. Real noise does exist: 3–4-cell dark-oak strips at (23..24,15,14), (13..14,17,15), (24,17,17) on the north slope, and on the lean-to at (15..17,9,10) and (18..19,7,7). Worse are the **8 `moss_block` cubes** stuck into the slope, which read as green holes: (12,13,12), (12,14,13), (13,14,13), (23,13,12), (23,14,13), (24,13,12) and the wing bay box. A flat untextured field also turns every cast shadow into a hard rectangle, which shaders and the renders will always show. |
| Plaster only in small amounts, so the house reads brown | **Confirmed, and it can't be fixed with infill alone** | Plaster is **1 % S / 4 % N / 6 % E / 1 % W** of the visible surface, the same as round 1. I tested three levels: W1 birch to plaster plus a re-centred jetty light, W2 plus a timber-framed wing ground storey, and W3 plus lime-washing the whole brick core. Plaster moved by at most +3 points. In `walls_compare_R0.png` the renders barely change, because the upper storey sits mostly inside the roof (plate y12, only 3 courses above the y8 beam) and the bay, porch, lean-to, oriel and trees cover the ground storey. |
| Facades read busy | **Confirmed** | The front stacks two brown A-frames (wing verge, then porch gable), and the wing gable carries a flower box, shutters, a pent skirt, a beam and a finial. The west elevation is a cascade of roof edges. |

What was really fixed from round 1:

| item | status |
|---|---|
| B1 spire | **Fixed.** Broach, 2:1, copper. Keep the dark hips: the all-copper version reads as a green ziggurat (`spire_compare.png`). |
| B2 plaster | **Not fixed in effect** (see above). |
| B3 dormers | **Half fixed.** The geometry is right. But the ridge logs (16,16,11..14) and (23..25,13,23) read as beams lying on the roof, and the north eyebrow (9..11,14,13) reads as a slot with a lid. |
| B4 noise | **Half fixed.** The chimneys and tower are clean. The new moss cubes are noise, and the cobble cells (6,18,16), (6,18,17) and (7,19,17) on the west stack read as grey squares in elev_s/w. |
| B5 entrance | **Fixed.** |
| B6 trees | **Fixed** (good enough). |
| Improvements 1–8 and 10 | **Done.** |
| Improvement 9 (moss) | **Done badly:** cubes instead of carpet. |

---

## 1. Scores (1–10)

| category | round 1 | round 2 (current) | with the recommended roof + walls |
|---|---|---|---|
| Silhouette & massing | 6 | **7**: spire hierarchy, 3 ridge heights, no triptych | 7 |
| Roof | 4 | **5**: good forms (broach, bell-cast lip, wall dormer, valleys); a flat brown field the same value as the walls, moss cubes, log stubs | **7** |
| Facade depth & detail | 6 | **6**: the south is a 7, the west still a jumble, busy | 7 |
| Materials & colour | 4 | **5**: crimson and copper accents, but 55–68 % timber | **7** |
| Entrance | 4 | **7**: gabled porch, crimson door, flared step, bench, lantern | 7 |
| Interior | 7 | **7**: unchanged and solid | 7 |
| Landscaping | 6 | **7**: shrub masses, edged beds, SE tree moved, path flare | 7 |
| Would a talented builder be proud? | 5 | **6** | 7+ |
| **Overall** | **5** | **6** | **≈ 7** |

---

## 2. Chosen roof treatment: "Slate field, calm, weathered hem" (variant R3g, final build `P2_winner_slate`)

Picked by looking (`FINAL_A/B/C.png`, `cmp_eye_0eg.png`):
* **Slate beats spruce.** The roof is the only large surface that can change the value balance. A grey slate roof on a brick
  and timber farmhouse is a real-world type (a Victorian brick farmhouse with a copper-capped turret). The copper spire
  still pops, as green against grey.
* **The solid slate verge (R3g) beats the dark-oak barge board (R3e).** R3e left two nested brown A-frames on the front (the
  wing verge with the porch gable in front of it). R3g turns the wing into a grey roof with a white gable, and the timber
  porch reads as a separate piece in front.
* **The slate partner (R3g) also beats the oak partner (R3f).** An oak partner under a slate verge reads as teeth.

Timber stays where timber belongs: the eave coves, the porch roofs, the loggia, the well and the back-porch pent.

The recipe (applied to the main, wing, lean-to and both dormers; the spire and porches are untouched):

| element | cells | block |
|---|---|---|
| Field stairs | every exposed roof stair of main/wing/dormers that is not an inverted partner | `deepslate_tile_stairs`, same `facing`/`half` as now |
| Field blocks (steep-top B / fill F, exposed) | e.g. (x,16,15), (x,16,17), wing (20,13,z)/(22,13,z) | `deepslate_tiles` |
| Repair strips | (23..24,15,14), (13..14,17,15), (24,17,17), (13,13,20), lean-to (15..17,9,10), (18..19,7,7) | field material (no strips at all) |
| Moss cubes | (12,13,12), (12,14,13), (13,14,13), (23,13,12), (23,14,13), (24,13,12) | `deepslate_tile_stairs[facing=south]` |
| Weathering hem, course 1 (main y13, wing y11) | runs along the course, about 50 %, chosen by `value2(along/1.8, y*5, seed=97, scale=1) > 0.5` | `deepslate_brick_stairs` (same value, finer texture; **not** `cobbled_deepslate`, whose light rough patches read as noise in R3) |
| Hem, course 2 (main y14, wing y12) | same noise > 0.8 (about 20 %) | `deepslate_brick_stairs` |
| Lean-to slabs | all field slabs; z ≤ 7 with noise > 0.55 → brick | `deepslate_tile_slab` / `deepslate_brick_slab` (keep the `type`) |
| Eave course + bell-cast lip | lip slabs (8..13,12,22), (8..12,12,10), (20,12,10), (23..24,12,10); wing eave stairs x17/x25 y10 | `deepslate_tile_slab[type=bottom]` / `deepslate_tile_stairs` |
| Eave coves (inverted stairs under eave courses on the **long** sides) | e.g. (7..12,11,21), the wing coves | **keep `dark_oak_stairs[half=top]`**: the thin timber soffit line |
| Gable verges | main x7/x25 and wing z27: verge stairs **and** their inverted partners, plus verge blocks (`dark_oak_planks`) | `deepslate_tile_stairs` (bottom and top), `deepslate_tiles`: a solid 2-thick slate edge |
| Ridges | main (8..24,18,16), wing (21,15,20..26) | `polished_deepslate_slab[type=bottom]`; keep a full `polished_deepslate` under each finial (x7/x25 at y18, (21,15,27)) |
| Dormer ridges | north (16,16,11..14), wing east (23..25,13,23) | `deepslate_tile_slab[type=bottom]` (no log stubs) |
| Eyebrow | add `deepslate_tile_slab[type=bottom]` at (8,15,13) and (12,15,13) | the arch becomes `s s t s s`, so the roof swells over the light |
| Moss hem (north- and east-facing slopes only) | course 1: `moss_carpet` on top of the stair where `value2(along/2.2, y*3.1, seed=91, scale=1) > 0.45`; course 2 only directly up-slope of a course-1 clump, 55 % | `moss_carpet` (valid on any non-air block, `CarpetBlock#canSurvive`). Never `moss_block` |
| Spire | unchanged | keep the copper field + dark-oak hips |

**Palette-pure fallback** (if P3 must keep spruce): `P1_spruce_best` in `FINAL_*.png`.
* No strips and no moss cubes (all field = `spruce_stairs`).
* Moss-carpet hem as above.
* Ridge logs → `dark_oak_slab[type=bottom]`.
* Same wall and fix pass as the winner.

It is calmer than now, but still about 63 % timber per elevation, so it does **not** fix "reads mostly brown". If you take
the winner, update the guide's §2.4 row 02 to read "roof: deepslate tile (P2 slate) + copper spire". The neighbour rule
stays satisfied: no other P3 building within 24 blocks uses deepslate.

---

## 3. Chosen wall treatment: W4 "calm plaster wing gable" (in `P2_winner_slate`)

Plaster swaps that nobody sees don't help, so W4 puts plaster where the eye view looks and takes clutter away:

| change | cells | block |
|---|---|---|
| Wing gable tie beam out | (18,10,26), (19,10,26), (22..24,10,26) `stripped_oak_log` | plaster |
| Roof planks in the gable face | (20,13,26), (22,13,26) `spruce_planks` | plaster |
| Gable flower box removed (the pent skirt already gives the shadow line) | (19..22,9,27), (20..21,9,28), plants (20..21,10,27) | air |
| Bay head frieze | (20..22,7,27) `stripped_oak_log` | plaster (a white band under the pent skirt, light where the eye looks) |
| Gable shutters | (19,10..11,27) and (22,10..11,27) | `spruce_trapdoor[facing=south,open=true]`, half bottom/top. Pale oak disappears on white plaster |
| Jetty light re-centred | (10..11,10..11,20) glass; (9,10..11,20) and (12,10..11,20) plaster; middle post (11,9..11,20) removed (y9 → plaster) | the crimson shutter moves from (13,10..11,21) to (9,·,21) **and** (12,·,21), so it flanks the opening |
| All `birch_planks` / `stripped_birch_log` in exposed walls (tan, reads as wood) | e.g. (9,9,20), (12,9,20), (8,9,16..17), (24,13,15), (24,13,17), lookout (15,16,19), (17,16,19), (18,16,20) | plaster |
| Wing ground storey east, timber framed | x24, z20..26, y4..7: `oak_log` posts at z20, z22, z24, z26; `bricks` nogging at y4; `stripped_oak_log[axis=z]` door head at (24,6,23); keep the window (24,5..6,21) and the door (24,4..5,23) | plaster above the nogging |
| Wing ground storey west | x18, z24..25 | as above; post at z26 |
| Wing south corners | (18,4..7,26), (24,4..7,26) stone quoins | `oak_log` posts |

**Plaster gradient** (use it for every plaster cell above):
* Compute `t = 0.6·value3(x,y,z, seed=41, scale=3.5) + 0.4·clamp((y−4)/10)`.
* `t < 0.36` → `white_terracotta` (the warm, darker one, low).
* `t < 0.66` → `pale_oak_planks`.
* otherwise → `calcite` (high).

That gives patches, darker toward the bottom, and never per-cell static.

Honest limit: even with W4, plaster is only 3 % S / 8 % E. The **value** split comes from the slate. Getting real plaster
area would need massing: raise the main plate one course (y12 → y13) so the upper storey shows 4 courses under the eave.
That is a builder decision for round 3, not required for a 7.

---

## 4. Remaining blockers

1. **The roof field shares the walls' value and hue.** Fix: §2 (slate, calm, hem, slab ridges).
2. **North slope clutter**: the wall-dormer ridge log, the eyebrow slot and the moss cubes. Fixes are in §2. Also:
   * Move the attic chests at (9..10,13,14) and (12,13,14) out from behind the eyebrow glass. A seat or a pot of fern
     works there instead.
   * The dormer's stepped side cheeks ((14,14,12..13), (15,15,12..14), (17,15,12..14), (18,14,12..13)) are still busy. In
     slate they read acceptably (`FINAL_C.png` cu_n).
3. **The front stacks brown frames.** Fixed by the slate verge (R3g) together with W4.

## 5. Top 6 other improvements (block level)

1. **West stack soot cells.** (6,18,16), (6,18,17), (7,19,17) `cobblestone` → `bricks`. One loose course reads as grey
   noise squares in elev_s/elev_w. Either do a full 2-course ring or nothing.
2. **West elevation calm-down** (elev_w is still the busiest).
   * The lean-to west verge x12: make it one straight `dark_oak_slab` rake. Drop the vertical spruce-plank end boards at
     x13 (y5..6, z7..11) and fill them with plaster panels between the existing posts.
   * The loggia slab roof at (4..7,12,18): extend it to y12 z17..19 so it reads as one shed, not a shelf.
3. **Lookout band.** The `stripped_oak_log` sills at (15..17,15,23) and (15..17,15,19), plus the birch/plaster row at
   y16: make y16 all plaster and keep the y15 sill only under the glass. The lookout then reads as a white lantern under
   the copper.
4. **Wing east dormer face** (24,11..13,22..24). After the slab ridge, replace the `pale_oak_planks` at (24,12,23) with
   `calcite`. Make sure the shutters (25,11,22) and (25,11,24) are `spruce_trapdoor` (they are). Then the dormer is a white
   triangle like the main gable, not a dark ghost.
5. **Porch ridge end** (16,9,27): the `stripped_dark_oak_log` end grain reads as a box above the verge. Put
   `dark_oak_slab[type=bottom]` at (16,9,24..27) on top of `spruce_planks` at (16,8,24..27). Keep the chain lantern hung
   from (16,8,25) via a block above it.
6. **Ridge finials**: 3 waxed lightning rods at the same visual height (x7, x25 and (21,16,27)) read as a row of pins. Keep
   (21,16,27) on the wing and the one on the spire. Replace the main-ridge ends with a `polished_deepslate` block plus a
   `deepslate_tile_wall` stub (no rod).

## 6. What to keep

* The **copper broach spire with dark-oak hips** (the all-copper hips are worse).
* The **gabled entrance porch and crimson door**.
* The **massing**: brick core, cross-wing, stair tower, lean-to, gable stack.
* The **jetty with bay and corbels**, and the **pent skirt**.
* The **east back porch**.
* The **tower masonry**: quoins, battered foot, staggered lights.
* The **chimneys** with pots and working smoke.
* The **full interior** with 15 valid shelves.
* The **farm story** and the **landscaping**.
* The **bell-cast lip geometry** (in slate now).

---

## Reusable roof recipe for the village

Use this on every house roof that reads as a "big brown field" (01, 02 and 03 all have that problem).

1. **Value/hue check first.** Look at the field material and the material that dominates the visible walls (first-hit
   shares, `tmp/critic02r2/stats.py`). The field must differ from it by **≥ 40 L or by hue**.
   * Mostly timber/brick walls → slate (`deepslate_tile`) or clay tile (`cinnabar_brick`).
   * ≥ 40 % plaster walls → a wood field (dark oak / spruce) is fine.
   * Never a wood field over mostly-wood walls.
2. **One field material, calm.**
   * No single-course "repair strips" and no random speckle.
   * No full moss/turf blocks inside a stair field.
   * Texture comes only from the hem (step 3) and from shadow lines.
3. **Weathering hem, eaves only.** Use a *same-value* neighbour so the hem reads as weathering, not patches:
   * course 1 at about 50 %, course 2 at about 20 %;
   * pick runs with value noise stretched along the course (`along/1.8`);
   * nothing above course 2.

   | field | hem |
   |---|---|
   | deepslate tile | `deepslate_brick` |
   | dark oak | `spruce` (lighter) or moss only |
   | spruce | `dark_oak` at most 30 %, course 1 only |
   | cinnabar brick | `polished_cinnabar` |
4. **Moss = carpet, shady slopes only.**
   * `moss_carpet` clumps on the lowest 1–2 courses of north/east-facing slopes, plus valley feet.
   * Course 2 only directly above a course-1 clump.
   * At most 10 % of the slope.
5. **Edges (one choice per building, never both dark):**
   * (a) a **solid 2-thick verge in the field material** (stair plus inverted stair of the same block) when the gable
     wall is plaster: calm, and the plaster gives the contrast;
   * (b) a **contrasting timber barge board** (stair plus partner in wood) when the field is dark and the gable is not
     light.
   * Long-side eave coves stay a thin timber line (`dark_oak_stairs[half=top]`).
6. **Ridges are low caps, not logs.**
   * Use a bottom slab of the field family (`polished_deepslate_slab`, `deepslate_tile_slab`, `dark_oak_slab`,
     `cinnabar_brick_slab`), or a `*_wall` row.
   * Use a full block only under a finial.
   * Dormers and porches follow the same rule. Log ridges read as beams lying on the roof.
7. **Lower roofs.** Porches, loggias, wells and back porches may stay timber. They read as attached woodwork in front of
   the main roof and help the hierarchy.
8. **Always check without shadows** (`shadows: False` view). If a "patch" disappears, it was a cast shadow on a flat field,
   and the cure is the hem plus calm texture, not more block noise.

Code for all of this is in `tmp/critic02r2/proto_roof.py`:
* `calm`, `moss_hem`, `slate_full`, `verge_partners`, `slab_ridge`;
* the roof-cell classifier is in `roofcls.py`.

Porting to another house only needs that house's eave y per region and its verge columns.
