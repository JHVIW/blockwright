# 05 Rustic Bakery with outdoor seating: builder log

## Plan (round 1)

**Concept: "The Bell & Crust".** A tall, narrow two-and-a-half-storey bakery shows its bell-cast "Dutch" gable to
the street (south). A red cinnabar-tile roof flares out at the foot, rises at 45° through the middle and steepens to
63° under the ridge. The verge is a 2-thick cinnabar band whose foot curls outward. The upper storey is a pale
timber-framed flat jettied over a glazed oak shopfront with a red-and-white wool awning. A lower bake-room wing runs
east behind it, and in front of that wing a round brick-and-resin bread oven bulges toward the street. The oven's
octagonal flue throws a heavy (signal) plume of smoke. To the west, a stone terrace under a vine pergola and a
striped parasol is shaded by a golden birch.

Palette P4 "Honey & Clay":
- frame: oak log and stripped oak;
- infill: white terracotta (low), smooth sandstone, calcite (high, gables);
- stone ground storey: cobble, mud brick, packed mud, mossy cobble;
- roof: cinnabar brick with a polished-cinnabar eave hem;
- accents: resin brick (oven), red/white wool awning, acacia shutters, `orange_tulip`, `sunflower`, `wildflowers`.

Contrast check: roof L≈75 (red) against stone L≈120 (grey/brown), plaster L≈185–224 and timber L≈88/147.

```
top view (g = 0; x east, z south / street)
 x: -9 ........ -1 0          10 11        17 18
 z-1             [ main roof, verge ]
 z0              # # # # # # # # # # #
 z1   pergola    #  stair ->      #  # # # # # # # #   bake-room wing x10..17, z1..7 (ridge z4, along x)
 z4   P . . P    #     shop       arch  bake room  #   east gable x17, service door
 z7   P table P  D side door      #  # # # # # # # #
 z8   . parasol  #                #   ( oven 5x5  )    oven x12..16, z8..12, 3x3 flue x13..15 z7..9
 z10  terrace    # [GGG] P D P [GG] #  (  dome   )
 z11  tree SW      [upper floor jetty z11]  ( oven )
 z13            ~~ path to the street ~~  bench + lamp post
```

South elevation: the main gable (ridge y17.5) is on the left, the wing eave (y5) is set back, the dome
(y5.5) and its flue rim (y11) are on the right, and the golden birch frames the left.

Storeys:
- ground floor y1, shop with 4 clear blocks (y2–y5);
- upper floor y6, flat with 3 clear blocks (y7–y9);
- attic floor y10, bedroom under the bell roof;
- bake-room wing floor y1, plate y5, open to the rafters.

Rooms:
- **shop** (counter, cake displays, shelves);
- **bake room** (oven mouth, smokers, flour sacks, kneading table);
- **kitchen** and **parlour** (upper floor);
- **bedroom** (attic, dormer and porthole).

Steps:
1. Massing and roof, then look at all four iso views.
2. Materials and plaster share per elevation.
3. Facades, interior and landscaping.
4. At least 5 render–look–fix cycles.

## Rounds (render, look, fix)
1. **Massing and roof.**
   - Bell-cast main gable (span 11, ridge x5) and a wing (span 7, ridge z4) tucked under the main eave.
   - The flare lip curls out at the verge feet.
   - Removed the speckled mud-brick patches from the stone. The chimney became a 3×3 flue with softened rim corners.
2. **Facades.**
   - Proud-post shopfront (3-wide and 2-wide panes) with a two-row red/white wool awning and an acacia door with a transom.
   - Lantern on a fence bracket beside the transom.
   - Jetty, flower box, shutters (2/1/0 per window) and a porthole in the gable.
   - Fixed the dormer sill, which had replaced a roof stair.
3. **Terrace, landscaping and interior.**
   - Terrace and pergola, three tables (one under a wool parasol), sunflower planters and paths.
   - Interior: shop, bake room, kitchen, parlour and attic bedroom.
   - QA fixes:
     - attic straddle headroom;
     - floating stair treads (storage under them);
     - porthole glass leak (backed corners);
     - brick-stair oven face leak.
4. **Plaster share was low (S 7 / E 8 / W 2 %).**
   - Raised the main plate one course (LESSONS §3), which made the upper storey 4 clear.
   - Replaced the dormer with a steep west wall gablet that uses the same bell profile.
5. **Oven, tree and bushes.**
   - Octagonal oven: brick course, resin course, resin dome, chiseled keystone (deliberate bands, no noise).
   - Golden birch moved behind the terrace (NW) and domed, with no limb tips below the canopy.
   - Lobed bushes with azalea and fern feet.
6. **East slope and story details.**
   - East shed dormer (the slope was 52 % plain roof) and an eyebrow.
   - Hanging shop sign on a corner bracket, a shop bell on the counter, fewer repeated cakes.
7. **West side and final pass.**
   - The west ground storey (terrace side) became timber and plaster on the plinth.
   - Final plaster shares: S 9 / N 15 / E 10 / W 12 %.
   - Vines only on the shady north stone. Canopy kept at least 2 air from the eave.

**Result:**
- QA: 0 errors, 0 warnings.
- `validate.sh`: PASS.
- Box 36×21×24, 2975 blocks, ground y=1.

## Round 2 (critique `docs/critiques/05_round1.md`, 6.3/10)
- **Prototypes ported** (adopted set `C DH1 T` from `tmp/critic05/proto.py`). A `SchemView` adapter maps the critic's
  schematic coordinates onto the build (authored = schematic − (13,1,5)), so the recipes run unchanged:
  - **P1 oven:** mud-brick bun dome; resin only at the street mouth lip.
  - **P1 flue:** mud-brick band, `brick_wall` corner posts above the roof, one pot. The signal campfire is still
    walled on four sides with open sky above.
  - **P2 east roof:** a 3-wide gabled dormer replaces the eyebrow, and a `spruce_slab` eave board runs along both
    long eaves.
  - **P3 tree:** three-lobe umbrella with rounded layers, rim-only drips and noise-patch gold/orange.
- **Improvements 4–6, by hand:**
  - west gablet: valley stairs turned toward the gablet ridge, and the ridge dies into the slope as a full block (a
    slab leaked);
  - 1×1 skylight with a slab hood on the north half of the west slope;
  - main path 2 wide from the door, with fewer, smaller edge bites;
  - the two cube bushes are broken up;
  - cornflower/allium drift on the terrace's south edge;
  - top-slab hood over the shop door;
  - shop rug is now a brown field with a white border.
- **Not done:** the optional trunk shift one block east, which would move the critic's coordinates.
- **Result:**
  - QA 0 errors, 0 warnings; `validate.sh` PASS.
  - 36×21×24, 3002 blocks.
  - Comparison sheet: `out/previews/05_rustic_bakery/compare_r1_r2.png`.
