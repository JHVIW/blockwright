# 05 Rustic Bakery ("The Bell & Crust"): critique round 1

**Coordinates.** All coordinates are **schematic** coordinates unless marked *authored*.
Schematic = authored (the coordinates in `builds/b05_rustic_bakery.py`) + **(13, 1, 5)**. Ground is y=1, the main ridge is x=18, the oven centre is (27, ·, 15) and the birch trunk is (3, ·, 7).

**Prototypes.** The scratch work is in `tmp/critic05/`:
- `h.py`: the harness, working in schematic coords;
- `proto.py`: the three prototypes;
- `grid.py`: the labelled comparison maker.

None of them touches the build script. All three prototypes stacked (`python tmp/critic05/proto.py final C DH1 T --qa`) give **QA 0 errors, 0 warnings** (1 info, the same as before).

## 1. Scores

| category | score | note |
|---|---|---|
| Silhouette / massing | **7** | The bell-cast street gable, the lower bake wing and the terrace make a real hierarchy. The wing plus flue reads well from the SE. From E and W the main roof is one tall red rectangle. |
| Roof construction | **6** | The bell profile (flared kick → 45° → steep top), the curled verges and the slab-capped ridge are good work. But the east slope is about 14×9 cells of unbroken cinnabar (`elev_e`). The eyebrow at (22,14,14..15) reads as a hole, not a feature. The hem "weathering" is polished cinnabar at L78 against L75, so it is invisible. The west slope is just as flat. Where the west gablet meets the main slope it leaves a stepped L-notch (iso_sw, about x13..16, z9..15, y15..17). |
| Materials / contrast | **6** | Red tile over warm plaster and oak is right. The oven is the outlier: **46 `resin_bricks`/`resin_brick_stairs`** (hex ce5818, the most saturated block on the plot). The lead guessed orange terracotta; it is resin, but the effect is the same: a traffic cone. The same orange is repeated as a 3×3 string course on the flue. `oven_brick()` also dithers resin and brick per block, which breaks LESSONS §2. |
| Facade depth / detail | **7** | The proud-post shopfront, the wool awnings, the jetty with its cove, flower boxes, shutters 2/1/0, the porthole gable and the hanging sign all deserve to stay. The south plaster share is 9 %, just under the 10 % target. |
| Oven + chimney | **4** | Bright stepped 45° pyramid (rings at y4/y5 plus a slab at y6). Behind it is a 3×3 flue with a 3×3 rim crown, which LESSONS §4 calls a "box/hat". Smoke physics are correct (campfire on hay at (27,9,13), walled, open sky). |
| Interior | **7** | Every room is furnished: shop counter, cakes, bell, shelves; bake room with oven mouth, smokers, flour and kneading table; kitchen, parlour and attic bedroom. All rooms are sealed and reachable. Minor: the orange/brown carpet "tetris" rug in the shop (cut_1) and cut_2's yellow/orange bed block are loud. |
| Landscaping | **6** | It has a continuous path, terrace, pergola, parasol, planters and leaf litter. But the dirt path has stair-stepped, aliased edges (top view). Two bushes are near-cubes: x9..12 / y2..4 / z2..4 (25 of 36 cells) and x8..11 / y2..4 / z19..21. The flowers are nearly all yellow/orange. |
| Tree | **5** | The trunk lean and the limbs are fine. But the canopy is clipped flat on its east face at x7 (the eave clearance rule), and its bulk is two full 7×7 layers (y9, y10). That reads as stacked orange cubes. |
| Story / charm | **8** | Unmistakably a bakery: oven, smoke, awning, terrace tables, sign, woodpile lean-to. |
| **Overall** | **6.3** | With the three prototypes applied, about **7.2**. With improvements 4–6 as well, about **7.6**. |

**Lead's impressions, verified:**
- Street gable, awning and terrace are charming: **confirmed**.
- The oven is garish: **confirmed**. The material is resin brick, not orange terracotta.
- Flat side roofs: **confirmed**. East is worst; the west gablet only partly helps.
- The canopy is a blocky orange blob: **confirmed**. The cause is the flat clipped face plus full layers. It is only 4 orange leaves out of 122; `yellow_poplar` itself renders orange-gold.
- The flue is chunky: **confirmed**.

## 2. Blockers (block-level fixes)

### B1. Resin oven dome: garish stepped cone
The oven covers x25..29, z13..17 (octagon, corners cut):
- y3: `resin_bricks` ring;
- y4: `resin_brick_stairs` ring2 plus resin core;
- y5: ring1 stairs;
- y6: `resin_brick_slab` apex.

**Fix (prototyped, P1):**
- Make the dome `mud_brick`, using a round "bun" profile instead of the 45° pyramid.
- Keep the resin in one place only: a glowing mouth lip on the street face.

The exact cells are in §4 P1.

### B2. The 3×3 flue with a 3×3 crown and an orange string course
The flue covers x26..28, z12..14, y4..10, with a `flower_pot` at (28,11,13). The string course is at y7 (`resin_bricks`/`chiseled_resin_bricks`).

**Fix (prototyped, P1):**
- Turn the string course into a calm `mud_bricks` course.
- Above the roof, cut the four corners down to `brick_wall` posts. That makes a rounded, fluted stack about 2.2 wide on the diagonal.
- Keep the campfire walled on four sides by the full arms.
- Put one pot on a full rim arm.

### B3. The east main slope is an unbroken red field, and the eyebrow reads as a hole
The east slope covers x19..25, z4..17, y12..18. The eyebrow is at (22,14,14..15) with its arch at y15.

**Fix (prototyped, P2):**
- Replace the eyebrow with a real 3-wide gabled dormer (z12..16, face set back in plane x22, slab ridge dying into the slope at x20).
- Add a continuous `spruce_slab` eave board on the d7 lip of both long eaves (x11 and x25, y12). This is the "calm hem": one dark timber line that frames the field and ties into the timber frame, instead of invisible polished-cinnabar speckle.

### B4. The canopy is clipped flat and built from full layers
The canopy covers x0..7, y6..12, z4..11. The cut at x7 makes a vertical leaf wall facing the house, and y9/y10 are solid 7×7 slabs.

**Fix (prototyped, P3):**
- A wide umbrella of three lobes.
- Corner and spur cells removed on every layer.
- Rim-only drips.
- Gold with soft orange noise patches and a few red cells low on the sun side, so no horizontal stripes.
- Clearance stays at x≤8, so 2+ air remains to the west eave lip at x11.

## 3. Top 6 improvements (by impact)

1. **Oven to mud-brick bun, with the resin only at the mouth (B1).** This is the biggest single gain. The orange traffic cone was the first thing your eye hit in every SE view; now the eye goes to the shop gable as intended. The resin lip still says "hot oven".
2. **East-slope gabled dormer and spruce eave board (B3).** `elev_e` goes from one red wall to a slope with a hierarchy: shed dormer (kitchen), gabled dormer (bedroom), framed by a dark eave line. Of the hem variants, brick (H2) reads as a pink stripe and raw cinnabar (H3) as purple speckle. Both are rejected.
3. **Slim, rounded flue (B2).** `brick_wall` corner posts above y8; no orange band; one pot.
4. **West slope (not prototyped).**
   - Tidy the gablet junction: in iso_sw the gablet's ridge (x13..16, z12, y15..17) steps into the main slope as an L-shaped notch. Run the gablet's slab ridge on into the main slope one more cell (authored `GB_PROF`, cap at PLATE+5). Then fill the two valley cells on each side with `cinnabar_brick_stairs` facing the gablet ridge, so `blockwright.resolve` turns them into inner corners.
   - Use the same `spruce_slab` eave board on the west lip (x11, y12). It is already in P2's `hem()`.
   - The north half of the west slope (z4..8) still needs a small feature. Add a 1×1 `skylight` (glass pane with a `cinnabar_brick_slab[type=top]` hood) at (14,15,6). Do not add another dormer.
5. **Tree canopy (B4, prototyped).**
   - Optionally move the trunk 1 east (authored `golden_birch(-9, 2)`) so the west lobe isn't trimmed by the box edge at x0. A 1-wider box is fine (LESSONS §7.5).
6. **Landscaping and entrance polish.**
   - Path: smooth the stair-stepped dirt_path edges (`paths()`). Bite 1-cell `coarse_dirt`/`grass` notches only at the edge, and make the main run 2 wide from the door (18,1,18..20) to the street.
   - Bushes: break the two cube bushes (x9..12 / y2..4 / z2..4 and x8..11 / y2..4 / z19..21). Remove the four top corners, then drop one side column to y2 so each reads lobed.
   - Flowers: add one drift of `cornflower` + `allium` along the terrace edge (about x4..8, z16..18) so the palette isn't only yellow/orange.
   - Entrance: give the shop door at (18,2..3,18) a small hood, an `oak_slab[type=top]` pair on two `oak_stairs[half=top]` brackets at y5. LESSONS §6 asks for a porch roof; the awnings flank the door but leave it bare.
   - Interior: swap the shop's orange checker rug for a single `brown_carpet` field with a `white_carpet` border.

## 4. Prototype recipes and comparison images

Run any combination with `python tmp/critic05/proto.py <tag> <oven 0|A|B|C> <roof 0|D|DH1|DH2|DH3> <tree 0|T> [--flue W|X] [--qa] [--views ...]`.
The adopted set is `final C DH1 T` (flue W is the default).

### P1: oven and flue (`oven(P, "C")`, `FLUE = "W"`)

**Dome.** Centre (27,15). Ring r = max(|dx|,|dz|); the corner cells |dx|=|dz|=2 are skipped (they keep their `brick_slab` footing).
- **Ground and foot (unchanged):** y1 `mud_bricks`/`packed_mud`; y2 `bricks`.
- **y3, ring 2:** `mud_bricks`. The hollow and the mouth opening (27,3,13) toward the bake room stay.
- **y3, street lip:** (27,3,17) stays `chiseled_resin_bricks`. Add (26,3,17) `resin_brick_stairs[facing=east,half=top]` and (28,3,17) `resin_brick_stairs[facing=west,half=top]`. This is the only resin left.
- **y4:**
  - ring 2 becomes `mud_brick_stairs[half=bottom]` facing the centre (high side inward);
  - ring 1 and the centre become `mud_bricks`;
  - the flue foot cells (x26..28, z13..14) become `mud_bricks`.
- **y5, outside the flue:**
  - ring 1 becomes `mud_brick_stairs` facing the centre;
  - the centre (27,5,15) becomes `mud_bricks`;
  - the flue cells become `bricks`.
- **y6:** cleared (no apex slab). The profile is now 4.5/5 → 5.5/6 → 6.0, a round bun instead of a 6.5 cone.
- Variants A (same steps, new material) and B (`mud_brick_slab` crown) are shown for comparison. C is adopted.

**Flue.**
- **y7, all 3×3:** `mud_bricks` (replaces the resin and chiseled resin course).
- **Corners** (26,12), (28,12), (26,14), (28,14): y8 and y9 become `brick_wall`, y10 becomes air.
- **Arms** (27,12), (26,13), (28,13), (27,14) at y10: `bricks` (full rim).
- **Campfire** (27,9,13) on hay (27,8,13): unchanged, walled by the 4 arms, open above.
- **Pot:** remove the `flower_pot` at (28,11,13) and put a `flower_pot` at (27,11,12) on the north arm. Variant X puts a `decorated_pot` on a cross-section shaft (corners → `mud_brick_slab` at y8); it reads as "rabbit ears" and is rejected.

### P2: east gabled dormer and eave board (`roof(P, "DH1")`)

`R` = `cinnabar_brick`; the dormer centre is zc = 14.
- **Remove the eyebrow.** (22,14,14..15) panes become `R_stairs[facing=west]`. Remove the arch stairs at (22,15,14..15).
- **Dormer roof** for x = 21, 22, 23:
  - z12: `R_stairs[facing=south]` at y15;
  - z13: `R_stairs[facing=south]` at y16;
  - z15: `R_stairs[facing=north]` at y16;
  - z16: `R_stairs[facing=north]` at y15;
  - ridge: `R_slab[bottom]` at (x,17,14);
  - under the ridge at (x,16,14): x21 `oak_planks` (hidden), x22 `calcite` (gable apex), x23 `R_slab[type=top]`.
- **Ridge end.** `R_slab` at (20,17,14), where the ridge dies into the main slope.
- **Hidden fill.** (21,15,13) and (21,15,15) become `oak_planks`.
- **Face (x22).**
  - Cheeks: `stripped_oak_log[axis=y]` at z13 and z15, y14..15.
  - Glass: `glass_pane` at (22,14,14) and (22,15,14).
  - Niche: remove (21,15,14) so it opens into the attic.
  - Sill: `spruce_trapdoor[facing=east,half=top]` at (23,14,14).
  - Keep `R_stairs[facing=west]` at (23,13,14).
  - Remove any stray cinnabar at x23, y14..15, z13..15.
- **Hem (H1).** Every `cinnabar_brick_slab` at y12 with |x−18| = 7 and z 4..17 becomes `spruce_slab`, same type. That is the d7 eave lip on both long eaves: x11 (west) and x25 (east).
- **Rejected:** H2 (`brick_slab` on d6 and d7) and H3 (`cinnabar_stairs` course at y15, x15/x21).

### P3: golden birch umbrella (`tree(P, "T")`)

- Delete all `*_poplar_leaves`.
- **Lobes** (centre, rx, rz, ry_top, ry_bot): ((3.9, 9.9, 7.3), 4.0, 3.9, 2.1, 1.1), ((5.4, 9.4, 4.4), 2.4, 2.2, 1.5, 0.9) and ((1.8, 9.2, 9.8), 2.2, 2.1, 1.3, 0.8).
- **Surface jitter:** `value3(x*1.1, y*1.1, z*1.1, seed, 2.2)` at ±0.18, applied to the ellipsoid test.
- **Bounds:** keep cells with x 0..8 and y 7..13 that are not already occupied.
- **Rounding:** on each layer, remove cells with ≤1 same-layer 4-neighbour. Also remove half of the cells with exactly 2 neighbours (`hash01(...,904) < 0.5`).
- **Colour:**
  - `red_poplar` where y ≤ 9, z ≥ 8 and hash < 0.25;
  - `orange_poplar` where `value3(.8x, .8y, .8z, 905, 2.4)` > 0.62, or y ≤ 8 and n > 0.4;
  - `yellow_poplar` everywhere else.
- **Drips:** only from cells at y ≤ 9, more than 2.6 from the crown axis (3.6, 7.4), hash < 0.35. Each drip is 1 cell long (30 % are 2) of `yellow_poplar`, never below y7.
- Rejected T1: rounder, but the height-banded colour made yellow/red stripes and it shrank to a ball.

### Images

All are in `tmp/critic05/` of the example project:

| image | what it shows |
|---|---|
| `cmp_all.png` | **Overall before/after** (all three stacked): iso_se, iso_ne, elev_s, eye |
| `cmp_close.png` | Before/after close-ups: oven, flue, dormer, tree |
| `cmp_oven.png` | Before / A / B / C / C + W flue, at the oven and flue close-ups |
| `cmp_roof.png` | Before / D / D+H1 (adopted) / D+H2 / D+H3: elev_e, dormer close-up, iso_ne |
| `cmp_tree.png` | Before / T1 / T2 (adopted): tree close-up, iso_sw, elev_s, iso_nw |
| `cmp_sides.png` | Before/after: iso_sw, elev_w, elev_e |

The individual renders are in `tmp/critic05/img/`; the `final_*` files are the adopted set.

## 5. What to keep

- **The street gable.** The bell-cast cinnabar profile with flared kick and steep top, the curled 2-thick verges, the calcite gable with porthole, the finial and the jetty cove. This is the hero element and it works.
- **The shopfront.** Proud oak posts, stall risers, 3- and 2-wide panes, the red/white wool-stair awnings, the acacia door with transom, the lantern beside the transom (not in front), the hanging sign on the corner bracket, and the flower box on the jetty.
- **The terrace.** Stone terrace, vine pergola, striped parasol, three tables, sunflower planters. It is charming and the lead is right.
- **Oven placement and smoke physics.** The oven bulging toward the street, the mouth into the bake room through iron bars, the signal campfire on hay walled in a flue, and the woodpile lean-to.
- **Massing.** The lower bake wing tucked under the main eave, and the east shed dormer over the kitchen (now paired with the gabled one).
- **Materials.** The stone ground storey on the north (shady) side only, with vines there. The plaster bands: white terracotta low, sandstone, then calcite high.
- **The interior program.** Shop → bake room → kitchen/parlour → attic bedroom, all sealed, lit and reachable.
