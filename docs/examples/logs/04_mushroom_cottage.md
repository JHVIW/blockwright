# 04 Woodland Mushroom Cottage: build log

## Plan

**Concept:** "Toadstool Hollow". A round mushroom-stem cottage (9-wide octagon) under a giant, slightly tilted red
mushroom cap: 15 across, a shallow dome with a curled-down rim, overhanging 3 all round, the pore underside as
pale gills with radial gill ribs. A smaller brown-cap pantry grows out of its east flank, its flat plate tucked
under the red rim (layered caps). A crooked tuff chimney pierces the cap on the north-west. A third tiny toadstool
(lamp) stands in the woodland garden. It should read as a cluster of mushrooms that happens to be a home.

**Top view (x east, z south, main stem centre 0,0; pantry centre 8,1):**
```
          z-7        C C               C  chimney (2x2 stack, corbelled crown with campfire)
          z-4    # # # # #
            -3  #         #
       w      #   loft N    #  . p p p     p  pantry stem (5-wide octagon), brown cap r~3.9
       bay  B #             # = p     p    =  1-long neck (passage) at z=1
              #  table      #   p     p
            +3  #         #     p p p
          z+4    # ( D ) #                 D  door S, round-headed frame, shelf-mushroom canopy, step
```

**Massing (g = 0):** footing y-1, stone plinth y0..y1 (floor y1, stand y2), stem walls y2..~y8 (they run up into
the cap), red cap underside (gills) y9, rim curls to y8, dome top y13; tilt -0.13*dz (south lower, north higher).
Pantry: walls y2..y4, brown plate y5, raised centre y6 -> at least 1 air under the red rim.
Loft floor y7 over the north half (stand y8, headroom to y11 under the cap shell), ladder on the east wall.

**Roof system:** a height field per column: top T(r) = 8 + 5.2*sqrt(1-(r/7.9)^2) - 0.13*dz, underside U = 9
(r 4.6..6.8) or 8 (rim r >= 6.8). Columns over the stem walls fill from wall top to T; inner columns are a 2-thick
shell whose bottom is the lowest neighbour's T-1 (closed shell). Mushroom faces: up and outward sides red, down and
inward faces false (pores = gills / pale dome ceiling inside).

**Palette (P5 Mossgrove, mushroom variant):** stem `mushroom_stem` (walls; value 197 vs the red cap ~ value 100:
strong hue + value contrast), frames `stripped_dark_oak_log` / `dark_oak_*`, plinth `tuff`/`mossy_cobblestone`/
`cobbled_deepslate`/`mossy_stone_bricks` (mossy low), cap `red_mushroom_block`, pantry `brown_mushroom_block`,
chimney tuff -> tuff bricks. Accents: `warped` (teal) shutters/door to try, lanterns, glow berries, shelf_mushroom.
Flowers: `lily_of_the_valley`, `blue_orchid` + `red_mushroom`/`brown_mushroom` on podzol, ferns.

**Rooms:** main round room (hearth N, bay window seat W, toadstool table centre, storage), pantry/kitchen (E),
loft bedroom in the cap dome (N half).

**Landscape:** podzol/coarse-dirt/moss woodland floor patches blending into grass, stepping-stone path S->SW, fallen
hollow log bench, stump with shelf mushrooms, a birch and an oak at the back, the toadstool lamp, mushroom drifts.

## Iterations
1. **Massing v1** (9-wide stem, cap at y8..13 with a -0.13*dz tilt and sin-wobbled outline): the cap swallowed the
   stem, the rim was a 3-tall red curtain, tilt + wobble rounding gave noisy terraces. -> dropped tilt/wobble, ring
   profile table per rounded radius, cap raised to gills y11 / top y16.
2. **Massing v2**: reads as a toadstool, but the stem was a plain straight tube. Brown cap plus-bump and curl looked
   like a cog -> clean disc + domed centre. Pore-texture warts read as sand patches, stem-block warts as sugar cubes.
3. **Rebuild with a tapering stem**: 11-wide ground storey (ring 5) -> polished-diorite stair "annulus" shoulder
   at y7 -> 9-wide loft storey (ring 4) carrying the cap. Bigger interior, real stem silhouette. Porch with its own
   little brown cap, bay window W, pantry neck E, chimney 2 above the cap with polished bands and a corbelled crown.
4. **Warts as white carpets** lying on the terraces (flat; no cubes) -> instant amanita. Tried an octagonal ring
   metric (lessons 3) for cleaner hips: it read as a square box cap, reverted to round rings.
5. **Landscape + details**: podzol/moss woodland floor weighted by shade and distance, birch pair, spruce, toadstool
   lamp, fallen log bench, stump with shelf mushrooms, woodpile, bushes, boulders, leaf litter (also on the cap's
   NW terraces under the birch), glow berries + spore blossoms under the gills, ivy on the chimney.
   Teal warped door + one teal shutter as the accent; thinner porch cap. Shares (first visible): stem 23-31%,
   red cap 22-33%, stone 10-21% on every side.

Final: 30x20x25 box, 2416 blocks, QA 0/0, validator PASS.

## Round 2 (critique docs/critiques/04_round1.md, 6.0/10)
Ported the critic's prototypes into the script as passes (section 15) plus rebuilds:
- B1/B2 red cap chamfered with red_wool stairs/slabs on every edge top cell, adjacent mushroom faces repainted
  true; warts on noses -> flush white_wool stairs, carpets only on flats; leaf litter only on flats too
  (litter-kept noses left red teeth in the slope).
- B3 brown pantry + porch caps rounded with brown_wool stairs + curled top-stair lip; porch crown forced north.
- B4 chimney: no 3x3 crown. 2x2 stack in courses (mossy base / stepped tuff water table y4 / tuff / tuff bricks),
  crooked head leaning north on two-step corbels at y12..14, campfire at y14 walled by the head on 3 sides and a
  corbelled block on the 4th (a lone tuff-brick wall post left the flame visible), polished-tuff slab rim y15,
  decorated pot + potted fern on the two full corners. Deviation: the head is 2x3 (shift north) so the fire can sit
  in a middle cell.
- B5 shoulder polished_diorite -> pale_oak stairs.
- Stem pilasters (mushroom_stem rib on a stone foot, pale-oak bracket) in 4 blank bays incl. the west.
- Ground cover rebuilt as 3 bean drifts + the cap's shade, fringe of leaf litter/ferns/sparse moss carpet.
- Path 2 wide at the step, stepping-stone slab edges; bush corners cut; lamp cap rounded (wool stair corners, slab
  top); loft reading nook (bookshelf, chair, rug by the bed); pantry herb rack (chains + hanging bundles).
QA 0/0, validator PASS, compare: out/previews/04_mushroom_cottage/compare_r1_r2.png.
