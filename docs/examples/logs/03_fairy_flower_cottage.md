# 03 Fairy Flower Cottage: build log

## Plan

**Concept:** Direction A, "Blossom Bell". A round main room (a 9-wide Minecraft circle, radius 4.5) sits under a
bell-cast cherry roof: a flat slab kick at the lip, then a 45 degree middle and a 63 degree crown that ends in a
spire and finial. A smaller round bay turret on the west has its own little bell, which nestles into the flank of
the big one. A crooked tuff and mossy-cobble chimney hugs the north wall. A leaning cherry tree on the NE drapes its
canopy over the roof. The house should read as a flower bell turned upside down, standing in a petal meadow.

**Footprint (top view, x to the east, z to the south, main centre at 0,0):**
```
            z-7   . . T T . . .          T  cherry tree (trunk ~ (5,-6), leaning SW)
            z-5      . C C .             C  chimney stack (2 wide, tapering), outside the north wall
            z-4    # # # # #
              -3  #         #
          b b b #             #          b  west bay turret, circle r2.3 centred at (-6,0), wall shared at x=-4
        b       .   (round      #           (3 wide opening = arched nook)
        b   seat .   room)      #
        b       .               #
          b b b #             #
              +3  #         #
            z+4    # # D # #             D  door, south, arched surround and trellis
                     s s s               steps, then stepping stones S, pond SW, fairy ring SE
```

**Massing heights (g = 0):** foundation y-1..0, stone plinth y1 (= the floor level), walls y2..y6 with a sill
beam at y2 and a top plate band at y6, wall plate y7 under the roof, roof lip at y7. Loft floor at y6 (stand y7).
Main bell: tip block about y15, finial to about y18. Turret walls y2..y5, lip y6, tip about y11 or y12.

**Roof system:** a height field in half-block units. Every column gets a ring index from its distance to the bell
centre, and each ring gets a surface height (profile table). The pieces come from the height difference to the
neighbouring columns. A half step is a slab (the flare), a full step on an odd half-height is a stair (45 degrees),
and a double step is a block plus a stair (63 degrees). The union of the two bells is the max of the two fields, so
the turret bell dies cleanly into the main roof. Stairs face the highest neighbour, with ties broken toward the bell
centre, and `blockwright.resolve` computes the corner shapes. Columns are filled down to the cover height of their lowest
neighbour, so the shell is closed. Trim is a dark-oak lip ring (the dark edge that holds the light pink) on
inverted dark-oak brackets. Living patches of moss and flowering azalea go on the north and NE (tree side), under
30% of the roof.

**Palette (P5 Mossgrove, blossom variant):**
* frame: `dark_oak_log` posts, `stripped_mangrove_log` sill beam and top plate, `dark_oak_stairs`/`_slab` trims
* infill: `mushroom_stem` 40%, `stripped_birch_log` 30%, `pale_oak_planks` 30% (value-noise patches, darker low)
* plinth: `tuff`, `mossy_cobblestone`, `cobbled_deepslate`, `mossy_stone_bricks` (mossy at the bottom)
* roof: `cherry_stairs`/`cherry_slab`/`cherry_planks`, ridge and spire `stripped_cherry_wood`, living patches
  `moss_block`, `flowering_azalea_leaves`, `pink_petals`
* accents: `waxed_copper_lantern` (green flame), `cherry_trapdoor` shutters, `cherry_door`, cave vines with glow
  berries, `spore_blossom`, `end_rod` finial
* flowers: `pink_petals`, `allium`, `lilac` + `flowering_azalea` filler, with `blue_orchid` at the pond as the
  single cool accent

**Signature details:** the bell-cast roof with a dark lip; the second, smaller bell on the turret; the round porthole
windows; the arched door with a flowering-azalea trellis arch; glow-berry strands under the lip; a copper lantern
finial; the crooked chimney with real smoke (campfire 1 below the rim); the cherry tree canopy draped over the NE
roof.

**Room program:**
* Ground floor (round room): hearth in the north wall (tuff surround, mantel); kitchen arc NE (smoker, cauldron
  sink, barrels, cherry shelves); round table with stools in the centre; turret window-seat nook on the west.
  Under-stair storage on the east.
* A curved stair along the east wall leads up to a loft (a gallery over the north half, floor y6) with a bed nook,
  a nightstand, a chest and a chiseled bookshelf. The south half is double height, open into the bell, with a
  chandelier.
* Lighting: a copper lantern chandelier, a hearth campfire, candles, and a lantern by the bed.

**Landscaping plan:** a pink-petal carpet under the cherry canopy (NE), fading to wildflowers and grass; a fairy
ring of red and brown mushrooms on podzol (SE); an irregular pond (SW) with lily pads, dripleaf, sugar cane, blue
orchid and mossy boulders; a stepping-stone path wandering south from the steps; allium and lilac drifts along the
plinth; azalea bushes NW; two firefly bushes by the pond; a copper lamp post at the path start; a small bench.
All edges are organic, and unset cells stay natural terrain.

## Iterations
1. **Massing v1** (rings from distance, height field): the 3-ring slab brim read as a flat disk and the stairs
   never got corner shapes, so the roof looked like a terraced ziggurat.
2. **Profiles A/B/C** compared (concave witch hat / ogee beehive / straight cone). Concave A has the fairy
   silhouette. Lip variants: a dark slab ledge under a cherry stair ring (A2) reads best. A petal-scalloped lip
   read as broken chunks at r=6 and was rejected.
3. **Corner technique.** Thickening the rings into 4-connected loops fails, because thin 4-connected loops
   cannot stay round (they ate the centre). The fix is to keep the true circle rings and add a hidden *helper
   stair* in the inner cell of every diagonal joint at the ring's own level. `blockwright.resolve` then makes
   outer/inner/outer corner triplets and the skirt reads as a smooth round hip.
4. **Walls +1 course** (walls y2..y7, lip y7): the walls looked squat under the deep eave. Roof/wall ratio is now
   about 1.7. The chimney base was slimmed (3x2 footing, 2x2 stack, lean toward the bell).
5. **Facade details.** Brackets, trellis arch, eyebrow window, east window and turret plus-window. The porthole
   box on the east read as a dark cube and was replaced by a shuttered window. The trellis uses cherry posts
   (dark posts doubled the main posts).
6. **QA leaks.** The plus-window corner stairs in the wall plane tunnel through the wall, so the glass moved to
   L-1 with plaster backing (also "frame proud, glass back"). Living-roof moss swaps changed neighbouring corner
   shapes and opened a gap, so moss swaps now only go on shape-safe straight cells and other patches are leaf
   clumps resting on top of the stairs.
7. **Interior** (hearth breast, kitchen arc, under-stair storage, table, reading corner, nook seat, chandelier,
   loft bedroom with lattice railing). The first stair step turns east so it can be reached from the room.
8. **Landscaping and tree** (petal carpet, fairy ring, pond, stepping stones, lamp post, bench, bushes, fade
   ring). Tree v2: overlapping-column lean, bark root knuckles, one wide canopy with drips.
9. **Roof material tests.** Pale-oak speckle read as snow (rejected). Stripped-cherry risers on the 63 deg crown
   read as shingle courses (kept). Hip "ribs" (dark oak/granite/spruce) turned most of the roof brown (on a
   circle almost every cell is a corner; rejected). Added a gabled east dormer with a dark verge to break the
   cone.
10. **Close-up pass.** The dark dormer face, then its dark verge, read as a black hook, so the dormer is now all
    cherry with pale cheeks. The chimney is 1 shorter with a corbel under the lean. The lamp post moved off the
    door axis and potted flowers went into the niche. The landscaping is clamped to x -12..9 / z -10..11, so
    the box is 22x22.
11. **Flowers.** The plinth beds were scattered dots, so a continuous drift band now runs around the walls with
    species per side (allium + petals in front, lilac east, ferns/moss/lilac in the shady north, petals + azalea
    west). Added a spore blossom under the turret eave, a spruce garden fence with an open gate at the path
    start, and a copper lantern hanging from the cherry limb.
12. **Tree v3.** Edge-connected (vanilla-style) diagonal logs fail the QA floating check, so the limbs are now
    single-axis paths: sideways logs on the runs, bark at the elbows. The result is a slender leaning trunk.
13. **Crown test.** A 45 deg top ring (rounded shoulder) read squat and let the chimney compete, so it was
    reverted. The spires (blunt pink columns, "candles on a cake") became slim finials: main = dark post + green
    copper lantern, turret = cherry post + end rod. The chandelier chain length now follows the shell.

## Final state
* 22 x 20 x 22 box, 1571 blocks, 180 states. House with eaves is about 17 x 13. Lantern finial at g+17.
* QA: PASS (0 errors, 0 warnings). One info: 28 dark grass spots at the box corners at night, which is natural
  terrain outside the garden.
* `tools/validate.sh`: PASS (Litematica loads it, and all 9680 cells are identical to the native decode).
* Rooms: main round room (hearth, table, reading corner), kitchen arc (NE, under the loft), turret window-seat
  nook, loft bedroom (stair along the east wall). All are sealed, reachable and lit (min light 7).

## Would still improve
* The 45 deg skirt still reads a little "stepped/tiered" up close. A hand builder would break a few ring
  corners with slabs or a slight sag on the shady side.
* The bell's underside inside is plain cherry planks and stairs. Radial rafters or a collar ring would finish
  the vault.
* The north wall and the loft have no window (hearth and chimney side). A tiny NW loft window would help.
* The fairy-ring podzol band reads as brown squares from directly above.
* The tree limbs show elbow zigzags in straight elevations (face-connectivity constraint).

## Round 2 (critique `docs/critiques/03_round1.md`, critic score 5/10, roof 4/10)
* **B1 roof.**
  * Octagonal offset rings `k = max(|dx|,|dz|,|dx|+|dz|-c)` (main c=2, turret c=1). Every ring is exactly 1 cell
    wide, the facets are straight and there are 8 clean hip lines. The helper-stair trick still closes the
    diagonal joints.
  * Option A profile: dark lip slab @8, cherry top slab @8, cherry slab @9 on the wall line (two-step flare),
    stairs @10/@12/@14, cap @15.
  * The dark brim is a uniform 1-cell band.
  * New QA catch: a top slab sitting on a wall line leaves a half-block gap over the wall top (the turret wall
    ring, and a main/turret tie at the turret's north wall). Any top slab that lands on a wall line is now a full
    block.
* **B2.** Plain plank risers (no stripped-cherry bands). Each bell has one cap block plus a needle: dark fence +
  copper lantern on the main bell, cherry fence + end rod on the turret.
* **B3.** The stray leaf cubes and the living-roof code are gone. The pale dormer cheeks went with the dormer.
* **B4.** The east dormer became a 2-wide eyebrow. The eyebrows are now S (3 wide), E (2) and N (2, lighting the
  loft bed). One eyebrow fill (next to the NW diagonal wall) has to stay closed, or it leaks past that wall's slab.
* **B5 chimney.**
  * 3×2 footing with tuff shoulders, a 2×2 stack, and a polished-tuff string course where it leaves the roof.
  * The stack leans north on corbels and ends in a corbelled 3×3 tuff-brick crown that encloses the campfire.
  * A slab rim is 1 above the fire with the flue open to the sky. Moss and a potted allium sit on the rim.
  * Material gradient: mossy cobble at the foot, tuff and deepslate in the middle, tuff bricks at the top.
* **B6 tree.**
  * Free-standing at the NE corner: 3 roots (lengths 3/2/1), a 2×2 base and a 1×1 trunk leaning NW.
  * Four limbs with bark tips.
  * Two domed lobes (radius per course), kept ≥2 air above the roof column everywhere, plus ≤12 drips and a
    lantern under the east limb.
  * An earlier try (base under the canopy) read as a lollipop, so the base moved to the corner.
* **B7 turret.**
  * Axis moved to plan (-6,+2). It now has overhang 1, its eave at the main eave height (one continuous dark
    band) and a steep crown.
  * The arched opening is now x=-4, z 0..2.
  * In elev_w it still sits in front of the main bell (orthographic overlap). In every iso view it reads as its
    own bell.
* **Improvements:**
  * NE-facet kitchen window and a north loft eyebrow.
  * Three bloom zones: moss + petals on the NE 1-out ring with azalea spilling over the lip, the round azalea
    entrance arch, and an azalea climber on the turret SW post with a spore blossom.
  * Bell vault: a dark collar ring under the 5×5 ring and rafter feet on the hip cells.
  * 4 glow strands (lengths 1/4/3/2).
  * An SE porthole with dark backers on the plus window.
  * Knee-brace + lip-bracket pairs.
  * Infill gradient restored (mushroom stem, stripped birch, pale oak).
  * Path meanders ±1 with a 2-cell stone, and the gate stands on the last stone.
  * Lobed bushes. The fairy ring has podzol only under its 8 mushrooms.
  * A round rug.
  * Room markers moved into their spaces (nook (-6,2,2), kitchen (2,2,-2)).
* **QA note.** All four rooms report the same floor area because they are one connected air space (the nook
  opens through an arch, the kitchen is part of the round room, the loft opens over a railing). That is by
  design.
* **Result:** QA 0 errors / 0 warnings, validator PASS, box 23×20×23, 1658 blocks.
  Before/after: `out/previews/03_fairy_flower_cottage/extra/before_after_round2.png`.

## Round 3 (critique `docs/critiques/03_round2.md`, 5.5/10)
* **Roof VB.** In `roof_blocks()`, every plank riser under a top stair becomes a stair with the same facing, and
  inner planks back it. The turret profile is now {3:17 slab, 2:19 stair, 1:23 stair, 0:24 cap}, with the cap at
  plan y11. The apex columns are filled solid: the riser back-fill had cut the chandelier chain, which left the
  main cap floating.
* **Tree T9 ported:** bark tube trunk along the S-lean, 4 limbs, mushroom-cap canopy plus 3 bulges, rim drips, and
  the lantern at (9,6,-4). An east root knuckle and moss break up the flat base patch.
* **Chimney C4:** one lean course; the crown ring at y11 encloses the campfire (open air above, checked). Two full
  rim corners carry the pot and the moss carpet flush.
* South eyebrow centre lid is now a north-facing stair. The SE porthole keeps one dark sill.
* **Not done (optional):** turret axis (-6,+3) and R4 stairs.
* **Result:** QA 0/0, validator PASS, 1602 blocks. Comparison: `out/previews/03_fairy_flower_cottage/compare_r2_r3.png`.
