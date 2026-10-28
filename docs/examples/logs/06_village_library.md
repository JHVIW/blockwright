# 06 Village Library ("Quillwood Library"): build log

## Plan

**Concept.** A tall, steep slate nave (9 span x 15 long, 63-degree stair-on-stair roof) on a heavy stone ground
storey, with a poplar timber frame and pale plaster above. The street gable carries a 5x5 rose window over a
porched, arched portal. An octagonal stair turret clings to the SE corner and rises well above the eave under a
patina-copper cone. A low plaster-and-timber enchanting wing pushes out of the east side, an oriel reading nook and
two clerestory dormers sit on the west, and a slim stone stack climbs the north gable from the reading fire.

**Top view** (authored coords, x east, z south, G = 0; stone outer face x-1..9 / z-1..15):
```
 z-3        CC                     C  chimney stack (north gable, real smoke)
 z-1   ###########                 #  stone ground storey, 2 thick (outer x-1/9, z-1/15)
 z 1   #  fire   # wwwwww          w  enchanting wing x10..15 z1..7 (gable east, ridge y9)
 z 3   #         #=  E   w            '=' arch through the nave wall, E enchanting table (12,2,4)
 z 5  B#  table  #       w         B  west buttress (z5)
 z 7   #         # wwwwww
 z 9  O#         #                 O  oriel (loft level, x-2, z8..12)
 z11  O#  gallery#
 z13   #  desk   # TT              T  octagonal stair turret, centre (10,14), r2 (5x5)
 z15   #####D#####TT
 z17     porch                     porch x1..7 z16..18, step z18
```
**Heights:** foundation y-1..0, floor block y1 (stand y2), stone storey y1..5, water table y6 on the outer layer,
timber band y6 / infill y7..9 / plate y10 (x0, x8, z0, z14). Loft deck y6 (stand y7): west x1..2, east x6..7,
south gallery z11..13. Main eave stair y10 (x-1/9), wall-line stair y11, stair-on-stair y12..17, ridge block y17 +
polished deepslate slab y18. Turret walls to y15, copper cone above, finial ~y24. Wing eave y5, ridge y9.

**Roof:** deepslate-tile field, deepslate-brick hem on the two eave courses (runs, never speckle), solid 2-thick
slate verges (plaster gables give the contrast), thin dark-oak eave coves, polished-deepslate slab ridge, moss
carpet only on the low east courses. Porch roof: deepslate with a dark-oak barge board. Turret cone: waxed weathered
cut copper with dark hips.

**Materials (P6 Golden Poplar):** poplar_log posts (L63), stripped_poplar_log beams (L154), infill pale_oak_planks
/ calcite (light, higher = lighter) with poplar_planks low, stone storey stone_bricks / polished_andesite quoins /
tuff_bricks / mossy at the foot. Accents: lanterns, poplar shutters/sills, chiseled bookshelves, cornflower +
azure_bluet + fern, yellow/orange poplar trees.

**Interior:** double-height reading hall (shelf aisles under the U-shaped gallery, long reading table with candles
in the centre, fireplace + armchairs at the north gable, librarian's desk + lectern by the entrance), U-gallery
reached by the turret spiral (slab spiral, 1 loop) and a library ladder, oriel reading nook, enchanting wing
(table + 15+ bookshelves at the vanilla ring distance).

**Landscape:** stone forecourt path from the porch dissolving into dirt path, two autumn poplars of different height
flanking the approach, cornflower/azure_bluet drifts, a west reading garden with a bench, lamp and a golden birch.

## Iteration notes
1. **Massing:** the first quick render had the roof lining leaking above the slates (it was placed on any cell next to a
   roof cell, so it fixed nothing). I limited it to cells under each column's lowest roof cell. The stone storey was
   5 courses and read as a box with a lid, so I lowered it to y1..4 with timber at y5..10. I raised the turret to
   y17 and gave it a stepped stair-on-stair copper cone with a needle.
2. **Leaks:** QA flagged the stair-on-stair quarter channels. At the dormer openings the empty top quarters of the
   stacked stairs connected along z, so I sealed the cheek-backing cells with deepslate tiles. The arch-head stair
   in the tall east window wall plane was a second leak; it now sits proud at L+1.
3. **First full facade pass (elevations):** the W/E slopes read as huge flat slate walls, the verge read as a heavy
   3-thick band, the turret read as a grey silo, the porch gable nested under the gable (two A-frames), and the
   rose window was cramped. Fixes:
   * the clerestory dormers moved to the east slope, with a gabled oriel on the west;
   * verge partners only under the single-stair columns;
   * the turret became a stone shaft to y10, a corbel ring, then a plaster lantern stage with shuttered lights;
   * the porch became a lean-to.
4. **Dormers and rose window:** the dormers read as dark chunks. They now have plaster cheeks, a 1x3 light and a
   dark-oak barge. The oriel gable at 63 degrees read as a box, so it is now 45 degrees, span 7, with its face flush
   with the oriel jetty. The rose window is now 3x3 lights in a proud 5x5 stone ring (chiseled keystone) and reads
   as round.
5. **Landscaping:** stone forecourt with a dissolving edge, stepping stones to a west reading garden (bench, lectern,
   lamp, kidney bed, golden birch), two poplars of different heights, a woodpile at the stack, vines, and a fade-out
   scatter. The trees first read as boxes, so I redid the profile as an egg-shaped radius table with a ragged edge.
   The birch moved NW. The porch was lowered by 1 for plaster share.
6. **Shares:** S 10 / N 10 / E 12 / W 6 % plaster. W is the roof-dominated side; this is noted in meta.

Final: QA 0 errors, validator PASS, 31x26x35, 3950 blocks, ground layer y=1 (schematic).
Remaining weak points:
* the cone reads a little "pagoda-tiered";
* the poplar canopies are still somewhat blocky;
* the west roof field is big and plain;
* the chimney shaft is a plain column.

## Round 2 (critique docs/critiques/06_round1.md, 5.5/10)
- A clay roof: brick_stairs field, mud_brick hem, dark-oak plank/slab ridges and verge fills, dark_oak_fence finial
  (final swap pass at the end of the script). Coves/barges stay dark oak.
- B flared witch-hat spire: kmax 4 slab flare on dark-oak brackets, k3 stair, k2/k1 stair-on-stair, ring 1.5 on the
  k1 diagonals, needle to T+7 + rod; hidden helper stairs kept. Second kick ring (k5) skipped: it would clip the
  nave's d3 roof course at x5..6.
- C flame poplars: 6 ellipsoid lobes incl. a fuller low skirt (dy 2.2, rx 1.9); 'turning' (W, h13) and 'yellow'
  with red SE skirt (E, h12). Noise-based jitter instead of random.
- West: small gabled dormer at z3 (calcite apron, 1x2 light, pale-oak flower box with pink petals), calcite/pale-oak
  oriel face and side walls, fewer west posts, no shutter -> W plaster 10% (S 10, N 10, E 12).
- Pink petals / allium / peony drifts in the forecourt beds; pale-oak window boxes on the north windows, west
  window and wing gable.
- Chimney: stone shaft with a corbel band at y13 and a tuff band y15..16, second decorated pot on a full block.
- Entrance: two lanterns under the porch soffit beside the door, poplar-slab step with moss-carpet edges, lamp post
  moved to (9,26). QA 0 errors, validator PASS. compare: out/previews/06_village_library/compare_r1_r2.png
