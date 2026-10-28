# Modern

**Mood:** clean, calm, open, light-filled, precise.

Modern architecture is volumes and planes: crisp boxes stacked and slid past each other, thin roof slabs that
cantilever into space, walls that are either solid and smooth or entirely glass. It is horizontal, honest about
materials, and it never pretends to be old: no fake timber framing, no shutters, no thatch. Its warmth comes from
wood cladding, planting and light. Carried at a distance by **the composition of offset volumes** and **the contrast
between solid planes and dark glass**, with a thin, strong roof line.

## Palettes

### White Villa (white render, dark frames, warm wood)
| slot | blocks |
|---|---|
| roof field | flat: `smooth_stone` or `light_gray_concrete` behind the fascia (rarely visible); green roof of `moss_block` on one volume |
| roof trim | fascia `white_concrete_slab` (1 slab thick, overhang 1–3) or a `smooth_quartz_slab` edge; parapet cap `smooth_quartz_slab` |
| walls | `white_concrete` 55% · `smooth_quartz` 30% · `calcite` 15% (panels, not noise) |
| frame | mullions and reveals `black_concrete`, `polished_deepslate` |
| foundation | recessed shadow plinth of `polished_deepslate`, or `polished_andesite` |
| accent | `pale_oak_planks` or `stripped_spruce_log` (horizontal) cladding on one volume, `bamboo_planks` soffits |
| glass | `glass` and `glass_pane` floor to ceiling; `light_gray_stained_glass_pane` for privacy |
| lighting | `pearlescent_froglight` downlights, `end_rod` strips, `sea_lantern` in pools |

Value: very dark frames (`black_concrete`, `polished_deepslate` L 73) against white L 220+; wood cladding (L 93–220 depending on species) breaks the white.

### Concrete & Cedar (warm brutalist)
| slot | blocks |
|---|---|
| roof field | flat `gray_concrete` |
| roof trim | thick fascia of `light_gray_concrete` with a `light_gray_concrete_slab` drip edge |
| walls | `light_gray_concrete` 45% · `polished_andesite` 30% · `smooth_stone` 25% |
| frame | `polished_tuff` reveals, `polished_deepslate` window frames |
| foundation | `polished_tuff`, `tuff_bricks` retaining walls |
| accent | `stripped_spruce_log` and `spruce_planks` cladding (horizontal), `waxed_oxidized_copper` panels |
| glass | `glass_pane`, `gray_stained_glass_pane` |
| lighting | `ochre_froglight` warm downlights, `lantern` on the terrace |

Value: spruce cladding L 89–93 against light concrete: ΔL > 40. Keep concrete panels in joints so walls do not read
as one flat grey field.

### Dark Pavilion (black box, glass and timber soffits)
| slot | blocks |
|---|---|
| roof field | flat `polished_blackstone_slab` |
| roof trim | `black_concrete_slab` fascia; underside soffit `oak_planks` or `stripped_oak_log` (warm, lit) |
| walls | `polished_blackstone` 40% · `black_concrete` 30% · `polished_deepslate` 30% |
| frame | `black_concrete` |
| foundation | `smooth_stone` terrace, `smooth_stone_slab` steps |
| accent | `stripped_oak_log` and `oak_planks` (warm interior visible through glass), `waxed_copper_grate` screens |
| glass | `glass` (large), `glass_pane` |
| lighting | `ochre_froglight` behind glass, `end_rod` in the soffit |

Value: the light, lit wood soffit and terrace are the contrast against black walls.

## Signature motifs

- **Flat or shed roofs with thin edges**: a single slab line as the fascia, overhanging 1–3 as a cantilevered plane;
  shed roofs at 26.5° (slab steps) with a thin slab verge.
- **Offset volumes**: two or three boxes stacked and slid, an upper box cantilevering 2–4 over the lower, a
  double-height living room.
- **Large glazing**: floor-to-ceiling `glass` with mullions every 3–4 blocks, ribbon windows 1 high and long, corner
  windows with no post.
- **Horizontal rhythm**: long bands, ribbon windows, horizontal board cladding, low garden walls.
- **Materials as themselves**: concrete, quartz, smooth stone, wood, copper. No fake timber, no shutters.
- **Screens**: vertical slats of `spruce_fence` or `*_trapdoor` (open, edge on), `iron_bars`, `waxed_copper_grate`.
- **Roof terraces and pools**: `water` edged in `smooth_quartz_slab`, a `sea_lantern` underwater, glass balustrades
  (`glass_pane`).
- **Built-in planters**: concrete boxes with `azalea_leaves`, `fern`, `bamboo` or grasses.

## Roof recipes

- Flat roof: a parapet 1 high (or none, with a fascia slab), roof field 1 below the parapet top, thin overhang slab
  over glazing.
- Floating roof: the slab extends 2–3 past the walls on two sides, held by one slim column (`polished_deepslate` or a
  `*_wall` post) at the far corner.
- Shed roof: one slope at 26.5° using slab steps, the high side over the glazing.
- Green roof: `moss_block` with `moss_carpet`, `short_grass` and `bush`, edged by the fascia slab.

## Wall recipes

- Solid planes in panels: change block or step depth every 4–6 cells to make joints, so H07 still holds.
- Shadow gaps: recess one course at the base (dark plinth) or at a floor line to make the volume above appear to float.
- Cladding: horizontal logs or planks on one volume only, wrapping its corners.

## Interiors

- Open plan: kitchen island of `smooth_quartz_slab[type=top]` on `white_concrete`, stools of `*_wool_stairs`, a long
  dining table, a sofa group of `light_gray_wool_stairs` around a carpet.
- Stairs: slabs cantilevered from a wall (floating treads), glass-pane balustrade.
- Lighting: froglights flush in the ceiling as downlights in a sparse grid (not a solid glowing ceiling), or hidden
  under carpet; `end_rod` strips along shelves.
- Bathrooms with `smooth_quartz` and `glass_pane` shower screens; bedrooms with a feature wall of wood cladding.

## Landscaping

- Hardscape may be rectilinear: terrace slabs, stepping pads, a lap pool.
- Planting stays loose and natural: meadow grasses (`short_grass`, `tall_grass`, `bush`), `large_fern`, birch or
  cherry trees in odd groups, a moss garden.
- The outer edge still fades into the terrain over 3–6 blocks.

## Anti-patterns

- Fake timber framing, shutters, flower boxes, stair roofs: they belong to other styles.
- A single white box with square holes. Modern needs composition: offset volumes, overhangs, solid against glass.
- Untextured walls with no joints, reveals or depth (the "flat plane" problem is worse here, not better).
- Glowing ceilings of solid froglights.
- Rectangular lawn pads with no planting at the edges.

## Deviations from LESSONS

- **Roof form** (H04, LESSONS.md §3): flat and shed roofs replace 45° pitches. Keep the edge rule: a visible, thin,
  continuous fascia that overhangs ≥ 1, and at least 2 roof levels (H05).
- **Contrast** (LESSONS.md §1): the roof field is mostly invisible, so the rule moves to the facade: the fascia and
  frames differ from the dominant wall by ≥ 40 L, and solid against glass carries the value split. It still applies.
- **Plinth** (H06): a recessed dark shadow plinth or a floor slab on piers replaces the stone plinth; the step at the
  door stays.
- **Gradients** (H09): large surfaces may be one block if broken by joints, reveals or material changes every 4–6
  cells. Still no per-block speckle.
- **Glazing** (H10): up to 40–60% of a facade.
- **Landscaping edges** (H14): straight edges are allowed for hardscape only; planting edges and the outer fade
  stay organic.

## Reference builds

None in the repository yet.
