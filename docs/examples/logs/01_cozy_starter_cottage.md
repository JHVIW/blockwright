# 01 Cozy Starter Cottage — builder log

## Concept
"Catslide Cottage" (brief direction A), with grafts: a 1-deep **bay window** with its own pent hood on the living
room, a small **gable dormer** above it lighting a vaulted living room, a **cross-gabled entrance porch** pushed off
centre (door at x10, not on the facade centre), a fat **exterior stone/brick chimney** on the west gable and a
**woodpile lean-to** on the east gable. Behind: the north slope sweeps down over a stone pantry lean-to (catslide)
to g+3. Garden: crescent daisy bed, wandering path, fenced vegetable patch (SE), flowering orchard tree + bench (NE),
azalea clump (NW), broken fence (W), lamp post at the path mouth.

## Footprint sketch (g = 0, x east, z south)
```
x:      -1 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
z 0                [==== catslide lip g+3 ====]
z 1                  = = = = = = =                    lean-to (stone) x5..11, z1..3; pantry inside
z 2                  =         =
z 3                  =  a a    =                      arch x8..9 in the main north wall
z 4              # # # # # # # # # # #
z 5              #                   #  K  F          F = flower box under the east kitchen window
z 6       C C C  H                   #  K
z 7       C C C  H        vault | loft (g+5) S #  W W    woodpile lean-to x14..15, z7..10
z 8       C C C  H                   S #  W W
z 9              w                   S #  W W
z10              # B B B #   D   #   #  o             B = bay (z11), D door x10, o water barrel
z11              b b b b b   P P P                    porch x9..11 z11..12, step z13
z12                          p . p
```
## Massing heights
* plinth g+1 (foundation g, g-1), walls g+2..g+6 (plate g+6), loft floor g+5 over x8..x12 only.
* Main roof: span 7 (z4..z10), ridge z7: log g+12 + slab cap g+13; south: lip slab z11 g+6, steep block+stair
  courses (63°) to the ridge (bell-cast kick); north: 63° top, 45° from z4 down over the lean-to to a lip at z0 g+3.
* Porch cross gable ridge g+7 (5 roof cells x8..x12), dormer ridge g+10, chimney rim g+14, woodpile roof g+4.

## Palette (P1 Thistledown)
frame `dark_oak_log` posts, `stripped_dark_oak_log` plates/beams; infill `pale_oak_planks` / `calcite` /
`mushroom_stem` / `white_terracotta` (darker low); plinth `cobblestone` / `stone_bricks` / `mossy_cobblestone` /
`andesite`; roof `dark_oak_stairs`/`dark_oak_planks` with ~15% `spruce` speckle, verge trim `spruce_stairs` +
inverted partner; chimney stone base -> `bricks` (+cobble); shutters `spruce_trapdoor`; doors `oak_door` (front, windowed)
and `spruce`; glass panes. Flowers: `oxeye_daisy`, `dandelion` + `wildflowers`.

## Room program
* Living (vault, x4..7): inglenook hearth west (campfire set into the chimney), mantel, 2 armchairs, rug, bookshelves,
  bay window seat.
* Dining/kitchen (under loft, x8..12): table + 2 chairs, kitchen counters on the north wall (barrels, smoker,
  cauldron sink, crafting table, shelves), straight stair along the east wall up to the loft.
* Pantry (lean-to): barrels, hay, pumpkin, composter, chest, candle.
* Loft (g+5 floor, x8..12): bed nook, nightstand, chest, porthole light, fence railing over the vault.

## Iteration log
1. **Massing v1** (steep 63° block+stair roof, tiny 3-wide porch gable, bay + dormer): the south slope read as a
   flat wall of plank risers; porch/dormer/bay jumbled; spruce speckle too loud. -> switched to a bell-cast profile
   (lip slab kick, 45° middle, block+stair top, ridge g+11), speckle reduced.
2. **Massing v2**: box + big lid, the south side needed a real secondary volume. -> replaced the porch with a
   5-span front cross-gable wing (x7..11) holding a recessed porch below and a loft extension above (re-entrant
   corners, third ridge height); chimney top-hat brim removed.
3. **Walls/details**: timber frame (posts, plates, sole plates), feature window + flower box, stair window with one
   shutter, east kitchen window + box, porthole, door with transom/lintel. Close-ups showed the wing gable drowned
   in a 2-thick spruce verge, dark door jambs, a porthole that read as a cluster of log ends -> wing partners
   dropped, jambs plastered, porthole re-made of planks + stairs, chimney crown in brick + two chimney pots.
4. **Interior**: inglenook hearth (fire set back into the stack, short indoor flue, mantel with candles), armchairs,
   rug, bookcase + lectern, window seat, vault with tie beam and ridge lantern; kitchen (barrel counter + shelf,
   cauldron sink under a window, smoker with brick hood, crafting table), table for two, under-stair barrels, stair
   to a g+5 loft, pantry. QA: valley leak (open stair quarters where the wing ridge dies into the main slope) ->
   full block under the wing ridge; loft unreachable (beam bracket over the stair foot) -> bracket moved.
5. **Landscaping v1**: path, beds, veg patch, tree, bench, lamp. Judge's view: zig-zag staircase path with
   isolated speckle squares, lollipop tree with a staircase-like root flare, debris-like fence, lone stone cube,
   bounding box 27x27. -> path re-routed (gentler bend, continuous shoulders, grass creeping in, fades at the site
   edge), organic site ellipse for the fade ring, pond with reeds/lily pads, boulders, scarecrow.
6. **Jetty**: upper wing gable jettied 1 over the porch (joist ends, corbels, lantern under the jetty) — the
   strongest depth/shadow line on the main facade.
7. **Roof life**: eyebrow window (3 panes + slab arch) lighting the vault; shed dormer on the north slope over the
   loft (2x2 glass, slab roof); finial (post + waxed lightning rod) on the east ridge end. Moss blocks on the
   catslide tried and removed (they read as green cubes and showed from inside as a mossy ceiling).
8. **Polish**: rug re-laid with chairs on its corners, cream loft rug + desk under the dormer, ivy on the chimney
   base, tree moved NE so it frames the corner without hiding the porthole, tree roots as moss/ferns instead of
   crate-like logs, coherent old fence line, less grass hiding the front, ridge/cap/chimney/lean-to stone given
   more variation (QA flat-run metrics), more spruce repair patches on the roof (~10%), handcart by the garden.

## QA notes / justified warnings
* QA: 0 errors, 0 warnings. The only info is "dark spawnable spots outside the rooms" = open lawn at night,
  normal for a garden; paths are lit at the door (jetty lantern), mid-path (lamp post) and the garden gate.
* Longest flat run (metric) is a roof stair course on the north slope, not a wall.
* The site is larger than the 17x15 guideline (about 26x23 incl. the fade ring): the pond (W), vegetable patch
  (SE) and orchard tree (NE) were judged worth it; the bounding box is mostly sparse fade planting.

## Round 2 (critique docs/critiques/01_round1.md, scored 4/10)
Visible-share check (first visible block per elevation cell, plants ignored, `--shares` dev flag):
| facade | plaster before -> after | pale trim after |
|---|---|---|
| S | 5% -> 7% | 6% |
| N | 1% -> 5% | 3% |
| E | 4% -> 11% | 9% |
| W | 6% -> 9% | 3% |
* **B1:** `plaster()` is now one cream per panel: a mushroom_stem base course, pale_oak_planks, and calcite only
  at g+9 and up. No white_terracotta. Sole plates are removed. Shutters, sills and flower-box fronts are
  pale_oak. Shutters vary: 2 on the east kitchen and gable windows, 1 on the west, 0 on the bay, stair window
  and dormer. The lean-to has cream panels with a dark plate under the lip, replacing the grey stripe.
  - **Eaves raised one course** (plate g+7). This gives every wall one more visible course. Roof, ridge,
    chimney, wing and dormer moved up with it; floors and rooms stayed put. The loft now has 3 headroom.
  - **S stays under the 10% target.** The south face is mostly bay glass, porch and roof, and the light share
    there is 13% (7% plaster + 6% pale trim). Cream now dominates the focal jetty gable, porch and door recess
    in the eye view.
* **B2:** per-block speckle is replaced by course-aligned weathering (lattice 4 along, 1 across). p is 0.30 on
  the eave and verge courses, 0.10 mid-slope on the catslide, and 0 near the ridge. Eave lips, the north eave
  course and the ridge cap are now one spruce trim, and the ridge core is dark planks.
* **B3:** the shed dormer is replaced by a 3-wide gable dormer (calcite gable, ridge 2 below the main ridge). A
  north pantry window has been added. Also new on the lean-to: quoins, 2 ivy strands, an azalea tuck at the NW
  corner, and rafter tails.
* **B4:** the porthole ring is removed. The east gable has a 1x2 window with pale shutters and sill under a
  **half-hip** (jerkinhead): the ridge stops at x12 and the lightning rod sits on the hip apex. The woodpile is
  now mixed oak/spruce/birch logs, laid with ends and bark sides showing.
* **B5:** the chimney is a deliberate gradient: a rubble base with moss only low on the N/W, a single toothing
  course, then clean brick. It tapers to 2x3 above the eave with stair shoulders. The corbelled crown ring
  wraps all four sides, one below the rim. The flue moved to the stack's inner edge with the campfire one
  below the open rim.
* **B6:** the path is a continuous worn track with edge-only coarse/rooted speckle and grass bites. The pond is
  a bean shape with green/moss banks, boulders at both tips and reeds on the far bank. Colour drifts are now
  daisy/dandelion plus cornflower, allium and pink tulip, with peonies at the step and flowering-azalea shrubs
  at the SW/SE corners. About 54 flower cells.
* **Top-10 items done:**
  - a real bay (projects 1, cream frieze, spruce roof course, window seat inside);
  - the porch as a round-headed cream arch;
  - an azalea box under the jetty window, end/corbel/end joist rhythm, a lantern in the door recess plus one
    under a jetty joist;
  - the wing ridge raised to g+11 with a block+stair course;
  - the eyebrow arch;
  - rafter tails;
  - interior: side table between the armchairs, 3 barrels swapped for a chiseled bookshelf and a shelf, one
    floor field per zone (spruce living, stone kitchen strip);
  - the scarecrow faces south, the cart carries a composter instead of a pumpkin, and the fade ring is thinned
    beyond about 5 blocks.
* QA: 0 errors, 0 warnings. Validator: PASS. The round-1 renders are kept in
  out/previews/01_cozy_starter_cottage/round1/ for before/after comparison.

## Round 3 (critique docs/critiques/01_round2.md, 5.5/10)
* B1 + #1: roof field is tuff slate (tuff_brick stairs/slab/bricks), with polished-tuff runs on the upper courses
  and mossy stone-brick clusters on the two lowest north courses. Main-roof frame is dark oak (verges, lips, ridge
  cap). The wing keeps spruce barge boards. Every top is now 45°, all ridges dropped one course, and the dormer is one
  lower (1x1 glass, ridge 2 below the main cap).
* B2: lean-to wall one course taller (plate g+5). Catslide foot flared (slab kick, top slab, dark-oak lip, overhang
  2). Rafter tails and ivy moved up.
* B3: crown ring removed, so the shaft is a slim 2x3 with a rim and two pots (one a decorated pot). The campfire sits
  2 below the rim, walled in by the ridge core, with an open flue above.
* B4: tree canopy rebuilt as a dome with a jittered radius, cut corners, an irregular fringe hiding the branch tips,
  and root stubs.
* Also: wing apex is a half slab (no horn). Transom lantern moved aside. North eyebrow added. Candle added on the
  south eyebrow's sill. Pond enlarged with no bare dirt (reeds stand on grass). Path corners filled. Cart now carries
  a barrel, with a flower drift to the fence.
* Not done: wood lining under the slate inside the vault/loft. The tuff underside is visible from the loft.
