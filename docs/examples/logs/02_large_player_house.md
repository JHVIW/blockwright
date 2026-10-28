# 02 Large player house -- "Brambleworth Farmhouse" -- builder log

Script: `builds/b02_large_player_house.py`. Outputs: `out/schematics/02_large_player_house.litematic`,
`out/previews/02_large_player_house/`, `out/reports/02_large_player_house_qa.md`.

## Concept
Direction A ("Farmhouse with stair tower"), adapted. A prosperous family farmhouse that grew over generations:
an old **brick core** (main block, E-W ridge) whose upper storey is **oak-framed birch plaster, jettied** over the
front garden; a later **east cross-wing** (gable to the south, 1.5 storeys, N-S ridge 3 lower) holding the storage
hall + still room and a guest loft; a **stone stair tower** jammed into the inner corner of the L (the tallest
element, timber lookout storey under a flared, hip-trimmed spire); a **workshop lean-to** on the north side; two
brick chimneys with real smoke (big tapering stack on the west gable for the living-room hearth, a slope stack on
the north side for the kitchen range); a gable-end balcony beside the west chimney that doubles as a covered side
porch. Farm story outside: kitchen garden with raised beds and a channel, beehives, laundry line, well, woodpile
shed, hay cart, hay-loft door with a hoist and a hanging bale.

Palette P3 "Brick & Bramble": bricks/mud bricks/packed mud/granite gradient, stone-brick plinth + quoins,
oak frame + birch plaster (birch planks/stripped birch/white terracotta), spruce roofs with ~10 % dark-oak repair
patches, dark-oak verge/eave trims, stripped dark oak ridge, stone-brick drip hoods + white pale-oak sills,
plum (crimson) shutters on the main block, white (pale oak) shutters on the wing. Flowers: peony, pink tulip,
white tulip + bush filler (plus ferns in shade).

## Coordinates (ground g = 0; floor blocks y=1 / 6 / 10; schematic offset is in the meta sidecar)
```
x->  0         1         2
     0123456789012345678901234
z 0  .........=======.........   lean-to roof overhang
z 1  .........#######.........   LEAN-TO x9..15 (workshop), slab roof tucked under the main eave
z 5  .........#.....#.KK......   K = kitchen slope chimney x17..18 z5..6
z 6  ....#################....   MAIN x4..20, north wall z6
z 9  .ccc#.....:.........#....   c = living-room chimney (3x3 -> 2x3 -> 2x2 + corbelled cap)
z12  .ppp#.....:.........#....   p = balcony above / porch below (garden door x4 z12)
z13  ....#####TTTTT######.....   main ground front z13; TOWER x10..14 z13..17 (shares walls with main + wing)
z14  ....jjjjjjT...T.....#....   j = jetty (upper wall z14, x4..9); WING x14..20 z14..20
z15  .....bbbbT...T.....#....    b = bay window under the jetty
z17  .........TTdTT.....#....    d = main entrance (tower south door)
z20  ..............###B###....   wing south gable; B = 5-wide bay under a pent-roof skirt
```
Heights: plinth y=1, ground walls y2..5 (clear 4), floor beam y6, upper walls y7..9 (clear 3), plate y10.
Main roof: span 9 (z6..14), 45 deg with a steepened top (block+stair at z9/z11) and a flared lip on the south
(west of the tower, overhang 2), ridge log top y17. Wing roof: eave y8 (2 below main), ridge log top y14
(3 below main) -- the two roofs are unioned as height fields, valleys resolve to inner-corner stairs.
Tower: stone shaft y2..12 with a string course (y6) and an andesite course (y10), stone cornice, oak-framed
lookout y13..17, 45-deg brim + 63-deg spire with dark-oak hips, finial top y24 (7 above the main ridge).

## Rooms (all have QA room markers; all sealed, reachable, spawn-proof)
* Ground (feet 2): tower vestibule (rug, lantern) | living room x5..9 (inglenook hearth with lit campfire,
  mantel, white wool sofa, rug, bookshelves/chiseled shelves, blanket chests, bay-window seat, garden door) |
  3-wide arch | kitchen-diner x11..19 (table for 6, sideboard, smoker + furnace under a brick hood at the chimney
  breast, sink under the window, crafting table, pantry: hay/pumpkin/honey/barrels, back door) | storage hall
  in the wing (6 double chests + 8 barrels, 3-wide aisle, shelf boards) + still room in the bay (brewing stand,
  water cauldron, ingredient barrel) | workshop lean-to (crafting, smithing, anvil, grindstone, stonecutter,
  loom, fletching table, blast furnace, chests, tool shelves).
* Upper (feet 7): master bedroom (double bed, nightstands, wardrobe, dresser, rug, reading seat, balcony door) |
  bathroom (water tub with quartz rim, basin cauldron with tap, lantern) | upper hall | enchanting room
  (15 valid shelves -- checked in the script with the game's exact offset/air-gap rule -- lectern, anvil,
  supply chest, oriel window seat, candles) | guest loft in the wing roof (2 beds, desk, chest, wall dormer).
* Attic (feet 11): kids' bunk nook (2 beds) under the gable dormer/eyebrow, chests + barrels, runner.
* Tower lookout (feet 14, ladder): glazed on all sides, map (cartography) table, stool, "telescope".

## Circulation
Front door -> vestibule (2 headroom under the first flight) -> door N into the kitchen-diner. Spiral of spruce
stairs + plank landings round a stripped-oak core: N(2) NE E SE S SW W NW N NE = upper landing (feet 7, doors
N to the hall, E to the loft), second loop to the attic landing (feet 11, door N), ladder to the lookout. Main
circulation 2-3 wide on the ground floor (arch 3 wide, aisle 3 wide), 1-wide spiral.

## Iteration log
1. Massing v1: main + wing + tower + lean-to, 45-deg roofs, 3x3 chimneys. Bug: interior masks blocked each roof's
   own surface -> fixed (masks only for hidden bodies). Read as "big box + pagoda hat": spire terraced, chimneys
   uniform pink pillars, both chimneys on the gable ends made the south elevation symmetric, walls dominated roof.
2. Massing v2: explicit roof profiles (steep top, south bell-cast lip), wing eave 2 lower, kitchen chimney moved
   to the north slope (breaks the long north roof, south elevation asymmetric), tower raised with a timber lookout,
   spire with dark-oak hips (reads as a crafted roof), chimney caps with hidden campfires.
3. Facade pass: frame posts + braces, quoins, 6 window types (brick 2x2/1x2 with shutters, timber with flower box,
   bays x2, oriel, wall dormer, gable dormer, shed dormer, slit windows, glazed lookout), jetty corbels, pent roof,
   hay door + hoist, balcony/porch. Fixed a misplaced shutter and a door hood colliding with a shutter.
4. Interior pass. QA found: attic leak at the shed-dormer corners (slab lower halves) -> logs at the cheeks; wing
   roof offered from z12 dropped hidden stairs into the upper hall (blocked a door) -> wing roof starts at z14;
   ladder over a void is not grabbable -> plank landing under the ladder. Then 0 errors, all rooms lit.
5. Landscaping: gradient paths with 3 bends, kidney beds, well, kitchen garden, orchard, props, fade ring.
   Fixed paths under props/the lean-to, the cart floating above its wheels, the woodshed vs a window.
6. Polish: trees rebuilt (branches climbing outward, ragged lighter undersides), west chimney given two
   shoulders (3x3 -> 2x3 -> 2x2), finials, door lanterns, vines (3-4 small patches), heavy white hoods replaced by
   stone-brick drip moulds, tower string courses (the stone shaft had an 11-course run), eyebrow window on the north
   slope, blast furnace, attic runner, footprint tightened (35x37 -> 32x33).

## Notes on rules / justified deviations
* Size 32 x 27 x 33 (building ~22 x 23) vs the brief's ~25 x 21: the full survival program (+3 bedrooms) needs the
  L-plan, and the user asked for 3-6 blocks of landscaping around it; the fade is organic (no platform).
* H07: the longest "flat run" QA reports is the 18-long ridge log and the north eave course -- roof edges, not
  walls. Brick walls are noise-mixed so no 5-run of one block occurs; the tower shaft now has 2 horizontal breaks.
* H12: the wing span is 7 (odd); the main span is 9 (odd, jettied upper storey).
* Chimney flues: the hearth campfire's flue is closed above the firebox (keeps the living room sealed); smoke comes
  from the campfires hidden one course below each crown, which are open to the sky.

## Round 2 (critique docs/critiques/02_round1.md, scored 5/10)
Before renders kept in `out/previews/02_large_player_house/before/`; side-by-side in `.../cu/before_after.png`.
* **B2 plaster:** `infill_at()` is now lime plaster (pale oak planks / white terracotta / calcite, value noise at
  scale 3.5, calcite toward the top, birch only in the course above a beam, boarded calcite apexes). It is used on
  the jetty, north upper wall, gables, lookout, porch gable and the lean-to, which is now an oak frame with
  plaster panels. Dark oak is trim only: the south eave courses are spruce, and only the lip stays dark.
  Light blocks went from ~140 tan birch + 1 white terracotta to 53 pale oak + 27 white terracotta + 20 calcite.
* **B4 noise:** roof repairs are now 2-4-cell strips inside one course, gated by a scale-4 field (~8 %), with none
  on verges, ridges, dormers or the spire. Chimneys are clean brick (stone breast at the foot, a sooty band only
  at the roof exit). The tower stone is clean, and the weathering moved to andesite quoins.
* **B5 entrance:** removed the slab hood, lamp arm, pot and white tabs. Added a gabled timber porch on the door
  axis: andesite/stone deck, flared 4-wide step, one oak post (the wing wall carries the other side), tie beam with
  3 clear, spruce gable with a dark verge and plaster gable, chain lantern, bench and 2 pots. The door is now
  crimson (the focal accent), and the path flares to 3 wide at the step.
* **B1 spire:** broach spire: a 45-deg flare course over the soffit, then a block+stair 2:1 needle to y24 + fence
  + rod (2 higher than before), continuous dark-oak hip lines, one field material.
  **Choice: waxed weathered cut copper.** I rendered both (`cu/eye_compare.png`, `cu/spire_copper.png` vs
  `spire_oak.png`). The dark-oak version disappears into the brown roofs and re-creates the "terraced" read. The
  copper is the single cool accent, makes the tower the hero, and matches the guide's P6 spire family, so it
  ties the village together. Waxed means it never oxidises. All finials became waxed weathered lightning rods to
  match. `B02_SPIRE=oak` re-renders the alternative.
* **B3 dormers:** north shed dormer replaced by a 5-wide gabled wall dormer (face in the wall plane, its own ridge
  2 below the main, valleys into the slope) with an attic window seat. The south gable dormer is deleted, which
  removes the mirrored gables. The wing east dormer now has a spruce roof with only a dark verge, oak posts,
  a 1x2 light, spruce shutters and a sill, and the eave is broken under it.
* **B6 trees:** new technique with branches climbing outward, rounded blobs per branch at offset heights, ~20 %
  drips and clumped oak/azalea/flowering mix. The big SW oak leans 1. The SE oak touching the wing is replaced by a
  small flowering tree at the east lawn, so the front is no longer bookended.
* **Improvements:**
  * bell-cast kick: dark slab lip on the north eave, and the south lip is the only dark course;
  * east back porch: plank deck, pent roof on oak posts wrapping to the wing skirt, lanterns, woodpile, hay;
  * tower: quoins, battered foot, string course, staggered windows following the spiral (tall middle one with
    a keystone), front light moved off the door axis;
  * 2-deep west loggia with its own slab roof;
  * west gable king post + brace;
  * chimneys made distinct: the west stack has decorated-pot chimney pots, the kitchen one is a slim plain
    2x2 with an L lip and a brick-wall pot;
  * stone sills on brick, spruce sills on timber (pale oak only as the wing's white shutters);
  * shrub masses at the corners, beds with grass edges and loose edging stones;
  * eyebrow sill and moss patches on the north slope;
  * interior: attic beds moved east (brown/light grey) away from the dormer glass, red/brown rugs, a candle
    centrepiece, a storage sorting table.
* Unchanged on the Keep list: massing, wing south gable, jetty + bay, plinth, smoke, the full interior with 15
  valid enchanting shelves (asserted in the script), and the farm story.
* QA: 0 errors / 0 warnings; validator PASS. The entrance marker moved to the path outside the porch step.

## Round 3 (critique docs/critiques/02_round2.md, scored 6/10; lead approved the slate roof over P3 spruce)
* Roof R3g: the prototype is ported as `slate_roof_pass()` (section 7 of the script). It runs in schematic
  coordinates (script + (4,2,6)) so the critic's region boxes apply verbatim.
  * Field: deepslate tile stairs/blocks, with no repair strips and no moss cubes.
  * Hem: deepslate-brick runs on the eave courses (~50 % on the first, ~20 % on the second).
  * Edges: the dark-oak eave coves stay as a thin line; the gable verges are solid 2-thick slate.
  * Ridges: polished-deepslate slab caps; deepslate-tile slab caps on the dormer ridges.
  * Moss: carpet only, on the low courses of the north- and east-facing slopes.
  * Eyebrow arch is now s s t s s. Spire unchanged.
* Walls W4:
  * New plaster gradient (white terracotta low, pale oak mid, calcite high); no birch remains anywhere.
  * Wing south gable is one plaster triangle: tie beam and roof planks in the face are plaster, the gable
    flower box is gone, the shutters are spruce, and the bay head has a plaster frieze.
  * The jetty light is re-centred with plaster cheeks and flanking crimson shutters.
  * The wing ground storey is timber-framed: oak posts, one brick nogging course, plaster panels.
* Fixes:
  * attic chests moved away from the eyebrow (a reading seat and a fern pot there instead);
  * west-stack soot cells are now brick;
  * the loggia roof is one longer shed;
  * the lean-to end boards are plaster;
  * the west gable brace is removed (calmer, and it had leaked once the chest moved);
  * the lookout y14 row is all plaster; the wing east dormer face is calcite;
  * the porch ridge is a slab cap on planks, with the lantern hung straight from the planks;
  * the main-ridge rods are replaced by polished-deepslate blocks with slate wall stubs; the wing finial
    now has a full block under it.
* QA 0/0, validator PASS, 15 enchanting shelves. Round 2 vs round 3:
  `out/previews/02_large_player_house/compare_r2_r3.png` (round-2 renders in `.../r2/`).
