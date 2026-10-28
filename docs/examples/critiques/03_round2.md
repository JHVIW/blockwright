# 03 Fairy Flower Cottage ("Blossom Bell"): critique, round 2

Reviewer: independent judge pass. No build files were edited. All prototypes are scratch scripts in `tmp/critic03r2/`
that read the real schematic, swap parts, run `blockwright.resolve` + `blockwright.qa.run_qa` and render.
**Coordinates:** schematic = plan + (12, 2, 11). Plan = the build script's coordinates. Both are given below.

## Verdict on the lead's impression

| claim | verdict |
|---|---|
| Octagonal rings fixed the lumpiness | **Confirmed** for R3-R6. But R2 (5x5) and R1 (3x3) are plain squares with c=2, so the crown is a square two-tier box. |
| Bells read as stepped pyramids: plank risers + stair on top | **Confirmed. Root cause:** every 63° step is a full `cherry_planks` riser under a stair, so each tier shows a 1.5-tall flat face (R2 risers at sch y13, R1 at y15). The turret is worse: R1 sits on **two** plank risers (sch y11-12), which makes a 3x3 box with a lid. |
| Tree = square block cluster on a zig-zag trunk | **Confirmed.** 164 leaves in 3-4 flat layers (y10-12 plan) with vertical sides. The trunk changes direction every block (1-wide face-connected staircase). |
| Chimney 3x3 crown = grey box hovering | **Confirmed**, and there is a bug too: the potted allium (sch 11,16,5) and the moss carpet (sch 13,16,3) stand on **bottom slabs**, so they float 0.5 above them (`tmp/critic03r2/cmp_chimney.png`, top row). From S/SW the shaft is hidden behind the bell, so only the 2.5-tall box shows. In elev_s, crown fragments peek out on both sides of the bell tip. |
| elev_w: turret stacks in front of the main bell | **Confirmed but minor** (an orthographic artifact, fine in every iso view). The lower turret hat below reduces it. |

## Scores (1-10)

| category | round 1 | round 2 now | with the fixes below (prototyped) |
|---|---|---|---|
| Silhouette & massing | 6 | 6.5 | 7.5 |
| Roof | 4 | 5 | 7 |
| Facade depth & detail | 5 | 6.5 | 6.5 |
| Materials & colour | 6 | 6.5 | 7 |
| Entrance | 6.5 | 6.5 | 7 |
| Interior | 6 | 6.5 | 6.5 |
| Landscaping (incl. tree) | 6.5 | 6.5 | 7.5 |
| **Overall / "would a talented builder be proud"** | **5** | **5.5** | **≈7** |

## 1. Roof: chosen construction = "stair-on-stair" steep courses (variant VB)

Tested on the real schematic. All variants pass QA (0 errors, 0 warnings):

| variant | idea | result |
|---|---|---|
| V0 | current | 63° tiers show 1.5-tall flat plank faces: wedding cake |
| VA / VH | all-stair 45° body + flare (+ 2-fence needle / plus tip) | smooth but squat. The tip drops to plan y13 and the chimney competes. Rejected. |
| VA2 / VG | 45° body + short 63° tip | still squat, with a small box at the tip |
| **VB** | **current heights, each plank riser replaced by a stair with the same facing (stair on stair)** | **every course is now ½ block, with a shadow line under each one. Reads as a steep shingled witch-hat. No flat faces, same concave silhouette. WINNER** |
| VC | cherry trapdoors on the risers | reads as rows of little windows (pagoda). Rejected. |
| VD / VE / VL | rounder ring 2 (5x5 minus corners) | small notches on the diagonals. No better than VB in iso. |
| VF / VI / VJ | plus-shaped tip (4 stairs round the cap) | best in elev_s/elev_w (pointier), but spiky in iso (cross ridges). It is a fallback if the lead prefers a rounder tip. VF/VI need the plank back-fill described below. |
| VJ / VK | R4 wall line as stairs | slightly cleaner skirt, but it opens a leak at the north eyebrow (sch 9,11,8 / plan -3,9,-3). It needs a plank at plan (-2,9,-3). The gain is marginal, so it is not recommended now. |

Upside-down-stair risers were also reasoned through and rejected. Facing in, they open a dark ½x½ pocket (the round-1 "crack"). Facing out, they look identical to planks from outside.

### Profile table (drop-in)

`MAIN_PROFILE` is **unchanged**: `{6:(17,"slab"),5:(18,"slab"),4:(19,"slab"),3:(21,"stair"),2:(25,"stair"),1:(29,"stair"),0:(31,"spire")}`
`TUR_PROFILE = {3:(17,"slab"), 2:(19,"stair"), 1:(23,"stair"), 0:(24,"spire")}` (was `2:(18,"block")`, `0:(25,...)`)

**New rule in `roof_blocks()`:** a `fill` cell that is `cherry_planks` directly under a `top` stair in the same column becomes `cherry.stairs(f)`, using the same facing `f` as the stair above. `blockwright.resolve` gives it the same corner shape as its top stair. This hits exactly the 63° risers. For the square rings no back-fill is needed (QA sealed). With plus/round tips (VF/VI), also plank any empty 4-neighbour at that y whose column is the same ring or an inner one.

| bell | ring | top piece: plan y / sch y | under it: plan y / sch y |
|---|---|---|---|
| main | R6 lip | `dark_oak_slab[bottom]` 8 / 10 | brackets as now |
| main | R5 | `cherry_slab[top]` 8 / 10 | – |
| main | R4 (wall line) | `cherry_slab[bottom]` 9 / 11 | wall plate |
| main | R3 | `cherry_stairs[in]` 10 / 12 | `cherry_slab[top]` 9 / 11 |
| main | R2 (5x5, 16 cells x10..14 z9..13 sch) | `cherry_stairs[in]` 12 / 14 | **`cherry_stairs[in]` 11 / 13** (was planks) |
| main | R1 (3x3, x11..13 z10..12 sch) | `cherry_stairs[in]` 14 / 16 | **`cherry_stairs[in]` 13 / 15** (was planks) |
| main | R0 (sch 12,·,11) | `cherry_planks` 15 / 17. Above it: `dark_oak_fence` 16/18, `waxed_copper_lantern` 17/19 | – |
| turret | R3 lip | `dark_oak_slab[bottom]` 8 / 10 | – |
| turret | R2 (wall ring) | **`cherry_stairs[in]` 9 / 11** (new) | `cherry_planks` 8 / 10 (as now) |
| turret | R1 (3x3, x5..7 z12..14 sch) | `cherry_stairs[in]` 11 / 13 | **`cherry_stairs[in]` 10 / 12** (was planks at 9 and 10). The 4 hidden corner helpers at 9 / 11 come automatically. |
| turret | R0 (sch 6,·,13) | **`cherry_planks` 11 / 13** (was 12). Above it: `cherry_fence` 12/14, `end_rod` 13/15 | nook chain plan (-6, 7..10, 2) |

The turret walls must follow the new roof bottom, which the script already does. Example: (-5,0) plan gets dark oak planks at y8.

Images:
* `tmp/critic03r2/cmp_roof_A.png`, `cmp_roof_B.png`, `cmp_roof_close.png`
* `cmp_roof_round.png`, `cmp_roof_round_close.png`, `cmp_tip.png`, `cmp_crown.png` (crown close-ups: VB vs VL vs VF), `cmp_R4stair.png`
* Per-view PNGs: `tmp/critic03r2/img/<variant>_<view>.png`
* Harness: `tmp/critic03r2/harness.py`, `roofvariants.py`

## 2. Tree: chosen recipe = "mushroom-cap umbrella", T9

Tested: T1 vase + lobes, T2/T5 cloud pads, T3 lobed umbrella, T4 five lobes, T6/T7 cap, T8 cap + east tuft, **T9**.
* The pads read as plates or mushrooms.
* The fat tube trunk (r=1.0) read as a column.
* The T8 tuft read as a second lollipop.

T9 reads as a weeping cherry from every side. It has 37 wood, about 81 leaves and about 20 drips, and passes QA. Builder steps (plan coords; the scratch code is in `tmp/critic03r2/tree.py`, functions `tube`, `lobe`, `place_tree`, `recipe_T9`):

1. **Keep** the 2x2 flare at y1-2 and the 3 roots. All wood is `cherry_wood` (bark on every face, so no pink end grain).
2. **Trunk** = cells within radius r of the polyline (7.5,2.6,-4.5) r0.75 → (7.8,4.4,-5.1) r0.66 → (7.5,6.2,-6.0) r0.58 → (6.9,8.0,-6.9) r0.52.
   * A 6-connected core walk (step along the axis with the largest remaining error) guarantees face contact for QA.
   * The radius ≥0.6 makes a 2-wide band, so the lean reads as one smooth diagonal instead of a zig-zag.
3. **Limbs** (r 0.5), all from the split at (6.9,8.0,-6.9):
   * W: (5.6,9.2,-6.6) → (4.4,10.2,-6.2)
   * NE: (7.8,9.4,-8.4) → (8.6,10.2,-9.4)
   * centre: (6.6,9.6,-7.8) → (6.3,10.6,-8.2)
   * low E from (7.6,5.4,-5.6): (8.6,6.3,-5.0) → (9.2,6.8,-4.3). It ends below the eave line, so no dark stub floats behind the roof from SW.
   * Lantern hanging at (9,6,-4) = sch (21,8,7).
4. **Canopy** = union of domed ellipsoids `((dx/rx)²+(dz/rz)²+(dy/ry)²) ≤ 1 + (value3(x*1.3,y*1.3,z*1.3,seed,1.6)-0.5)*2*rough`, where ry = top above the centre and bottom below it:
   * main cap (6.6,11.6,-7.6) rx4.0 rz3.5 top2.0 bot0.6 rough0.22
   * W rim bulge (3.9,11.0,-6.4) 1.7/1.6, 1.1/0.6
   * NE bulge (9.0,12.0,-9.6) 1.5/1.4, 1.0/0.5
   * off-centre crown bump (5.6,13.4,-8.4) 1.6/1.4, 0.8/0.4 (all rough 0.2)
   * 6% `flowering_azalea_leaves`.
5. **Constraints:**
   * ≥2 air above the house (leaf y ≥ rooftop + 3)
   * skip x -2..2 / z -9..-5 (chimney crown and smoke)
   * stay inside x ≤ 10, z ≥ -11 (the 23x23 box)
6. **Drips**, rim only: underside leaves with `((x-6.6)/4)²+((z+7.6)/3.5)² ≥ 0.45` hang 1 (2 at 35%, 3 at 15%) cherry leaves at 38% probability. This is the weeping edge.
7. Soft QA note: the trunk base now gives "largest flat patch 12 x cherry_wood, east" at sch (20,3,5). Break it with 1-2 `moss_block`/`rooted_dirt` knuckles or a `cherry_wood` root on the east side.

Images: `tmp/critic03r2/cmp_tree_1.png` … `cmp_tree_4.png`, `cmp_tree_final.png` (T0/T7/T8/T9).

## 3. All fixes together

`tmp/critic03r2/final.py` = VB + T9 + chimney C4 + S-eyebrow lid. QA PASS, 0/0, 1612 blocks.
* Full sheet: `tmp/critic03r2/final/final_sheet.png`
* Before/after: `tmp/critic03r2/before_after_proto.png`

## 4. Remaining blockers

1. **B1 roof risers.** Section 1 above.
2. **B2 tree.** Section 2 above.
3. **B3 chimney crown + floating pot/moss** (variant C4, prototyped, plan → sch).
   * Remove everything in the crown from plan y10 up.
   * One lean course instead of two: plan y10, x0..1, z-6..-7 (sch y12, x12..13, z4..5) in tuff bricks, with `tuff_brick_stairs[north]` shoulders at (0..1,10,-5).
   * Inverted `tuff_brick_stairs` corbels at y10 under the overhanging ring cells.
   * Crown ring at plan y11 (sch 13): x-1..1, z-8..-6, full tuff bricks. One cell is `mossy_stone_bricks` at (1,11,-6).
   * Campfire at (0,11,-7) = sch (12,13,4), fully enclosed.
   * Rim at plan y12 (sch 14): `tuff_brick_slab[bottom]`, except **full `tuff_bricks` at (-1,12,-6) and (1,12,-8)**. The potted allium sits on the first at y13, and the `moss_carpet` on the second at y13: both flush.
   * This hides the crown behind the bell in elev_s and shows more shaft from SE.
   * From SW it still peeks; if that is unacceptable, the next step is a 2x2 cap.
   * Image: `cmp_chimney.png`.

## 5. Top 6 other improvements (block level)

1. **South eyebrow lid bump.** The centre lid `cherry_planks` at plan (0,10,4) / sch (12,12,15) sticks up as a box. Make it `cherry_stairs[facing=north]` so it continues the R3 ring (prototyped).
2. **SE porthole plates.** Four cherry trapdoor plates float like shelves on the diagonal facet:
   * sill (top half) at plan (3,3,4), (4,3,3) = sch (15,5,15), (16,5,14)
   * hood (bottom half) at plan (3,5,4), (4,5,3) = sch (15,7,15), (16,7,14)
   * Keep one `dark_oak_trapdoor[half=top]` sill under the pane at (3,3,4) only.
   * Replace the hoods with a single `dark_oak_stairs[half=top]` at (3,5,4), or delete them.
3. **Turret in elev_w.** The prototype's lower hat (cap at plan 11) already helps. If more separation is wanted, move `TUR_C` to plan (-6,+3). Check the pond bank at z≥6 and the arch at x=-4.
4. **Skirt diagonals.** The R4/R5 slab rings make a saw-tooth on the four diagonal facets. R4 as stairs (`4:(19,"stair")`) is the clean fix, but it needs a plank kept at plan (-2,9,-3) (the existing KEEP_FILL cell, which would otherwise become a helper stair) and re-checked eyebrow cells. Do this after B1-B3.
5. **Tree trunk base patch.** See Section 2, step 7. Also let the petal carpet run over one root.
6. **Restraint pass on the east face.** The stair window shutters + pot, glow strand (5,·,3), knee brace and porthole all sit within 4 cells. Dropping the porthole hoods (#2) is enough. Do not add more there.

## 6. Keep

* The octagonal 1-cell ring metric, the helper-stair joints, the uniform dark lip with brackets, and the two-step slab flare.
* The concave height profile itself. Only the risers change.
* Single cap + needle finials: copper lantern on the main bell, end rod on the turret.
* South entrance: recessed door, transom, hanging copper lantern, potted alliums, azalea arch, mossy step.
* Infill gradient, plinth gradient and knee braces.
* Petal carpet, pond, fairy ring, meandering path, gate.
* Interior program and the vault collar.
* Clean QA.
