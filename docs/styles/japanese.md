# Japanese

**Mood:** calm, ordered, deep-shadowed, close to the garden.

Traditional Japanese architecture is a heavy, sweeping roof floating over a light timber frame. Walls are screens
rather than masses: posts on stone footings, white plaster or paper panels, sliding openings onto a veranda that
blurs inside and outside. Ornament is concentrated at the roof ridge, the brackets and the garden; everything else is
quiet and precise. Carried at a distance by **the roof's silhouette** (deep eaves, upturned corners, a hip-and-gable
form) and by **a dark roof over light walls**. Up close it lives in the garden: moss, raked gravel, stone lanterns,
water and one perfect tree.

## Palettes

### Kawara Machiya (tiled town house and temple hall)
| slot | blocks |
|---|---|
| roof field | `deepslate_tile_stairs`/`deepslate_tile_slab` (kawara tile) |
| roof trim | ridge `deepslate_tile_wall` on a `polished_deepslate` course, ends turned up with `polished_blackstone_brick_stairs`; eave lip `polished_deepslate_slab`; soffit `dark_oak_trapdoor[half=top]` rafters |
| walls | `calcite` 50% · `pale_oak_planks` 30% · `smooth_quartz` 20% plaster; lower band `dark_oak_planks` or `stripped_dark_oak_log` (horizontal) |
| frame | `stripped_dark_oak_log` posts and beams (or `stripped_spruce_log` for a warmer frame) |
| foundation | `polished_andesite` post footings, `andesite`/`stone` base, `cobblestone` drain edge |
| accent | `bamboo_trapdoor` lattices, `spruce_door`, one `red_wool` noren-like awning slab |
| glass | `white_stained_glass_pane` (shoji paper) |
| lighting | `lantern`; stone lanterns in the garden |

Value: tile L 55 over plaster L 220–224: strong dark-over-light. The dark lower band keeps the walls grounded.

### Shrine Vermilion (shrine, torii, pagoda)
| slot | blocks |
|---|---|
| roof field | `waxed_oxidized_cut_copper_stairs` (green copper) or `deepslate_tile_stairs` |
| roof trim | `dark_oak_stairs` eave lip and brackets, `gilded_blackstone` or `gold_block` ridge ends (one or two only) |
| walls | `calcite` 60% · `white_concrete` 40% panels |
| frame | `red_concrete` posts and beams, `red_concrete_stairs`/`red_concrete_slab` for curved members; `mangrove_planks` as a darker red |
| foundation | `polished_andesite`, `stone_bricks`, `smooth_stone` platform edge |
| accent | `black_concrete` torii cap (kasagi), `white_banner` on posts |
| glass | `white_stained_glass_pane` |
| lighting | `lantern` under the eaves, `candle` in the hall |

Value: green copper over white walls is a hue break; vermilion frame against white plaster is the signature.

### Sukiya Teahouse (rustic refinement: earth walls, bamboo, cedar)
| slot | blocks |
|---|---|
| roof field | `dark_oak_stairs` (cedar shingle) or `bamboo_mosaic_stairs` thatch with a `spruce_stairs` lip |
| roof trim | `spruce_stairs`, `bamboo_fence` ridge rail |
| walls | `packed_mud` 50% · `mud_bricks` 30% · `pale_oak_planks` 20% (earthen tsuchikabe) |
| frame | `stripped_spruce_log`, `bamboo_block` accents |
| foundation | `mossy_cobblestone` pads, `moss_block` ground |
| accent | `bamboo_trapdoor` windows, `bamboo_fence` screens, `potted_bamboo` |
| glass | `white_stained_glass_pane`, small and low |
| lighting | `lantern`, `candle` |

Value: dark-oak roof L 47 over earth walls L 109–112 (ΔL ≈ 63).

## Signature motifs

- **Irimoya (hip-and-gable) roof**: a hip roof on the lower part (rings, techniques.md §3.1.5) with a small gable
  triangle set back on top, its face in `dark_oak_planks` or a `bamboo_trapdoor` lattice. Ridge as above.
- **Upturned eaves**: the profile is concave, nearly flat at the edge (slab courses, 26.5°), 45° in the middle,
  stair-on-stair near the ridge. At each corner lift the last 1–2 cells with a slab kick and an extra stair so the
  hip line sweeps up.
- **Deep eaves**: overhang 2–3, carried by bracket clusters (stacked `dark_oak_stairs[half=top]` with
  `dark_oak_fence` stubs) and a rafter soffit of `dark_oak_trapdoor[half=top]`.
- **Engawa veranda**: a `dark_oak_slab[type=top]` or `spruce_slab` deck at floor level running along 1–3 sides, 1–2
  deep, under the eave, with a stone step (`polished_andesite` or `smooth_stone_slab`) at the entry.
- **Shoji screens**: panels of `white_stained_glass_pane` framed by posts every 2–3 blocks, with `birch_trapdoor` or
  `bamboo_trapdoor` (open, flush with the wall face) as the lattice on feature panels.
- **Tokonoma**: an alcove 1 deep, 2–3 wide, floor raised a slab, a `white_wall_banner` as the hanging scroll and one
  `potted_*` arrangement; a corner post of a different wood (`stripped_cherry_log`).
- **Torii**: two `red_concrete` posts (or `stripped_mangrove_log`), a tie beam 1 below the top, a `black_concrete`
  cap whose ends turn up with stairs.
- **Stone lanterns (toro)**: `stone_brick_wall` shaft, `stone_brick_slab[type=top]` platform, `lantern` on it, a
  `stone_brick_stairs` roof ring or slab cap above, `moss_carpet` on top.
- **Raked gravel and moss**: `gravel` beds with `andesite`/`tuff` boulders in odd groups, a moss (`moss_block`) shore.
- **Koi pond**: an organic pond with `lily_pad`, a few `sea_pickle` for glow, an arched bridge of stairs, stepping
  stones of `smooth_stone_slab`.
- **Cherry and azalea**: one cherry umbrella (techniques.md §5.4 T4/T9) or cloud-pruned azalea pads on a crooked
  trunk; `bamboo` groves on grass or dirt.

## Roof recipes

- Main halls: irimoya, overhang 2–3, upturned corners, ridge with turned-up ends.
- Gates and small shrines: kirizuma (plain gable) with a deep overhang and kicked verge ends.
- Pagodas: 3 or 5 tiers, each a smaller square of the same flared profile, a `lightning_rod` or `end_rod` +
  `iron_chain` finial spire on top.
- Machiya street fronts: a pent roof (hisashi) over the ground floor, a low upper storey with lattice windows.

## Wall recipes

- Posts proud of the plaster (L+1) every 2–3 blocks, a beam band (nageshi) at door-head height, plaster above and
  below. Lower band of dark wood boards on exposed sides.
- Sliding-door bays: full-height `white_stained_glass_pane` between posts; solid `dark_oak_planks` storm shutters
  (amado) on the weather side.

## Interiors

- Floors raised above the engawa, in `bamboo_mosaic` (tatami-like) or `birch_planks`, edged by a darker wood.
- Rooms divided by screens (`white_stained_glass_pane` or lattice trapdoors), not walls.
- Low furniture: tables of `dark_oak_slab[type=top]` on trapdoor legs, cushions of `*_carpet`, a sunken hearth (irori)
  with a `campfire` in a stone-edged pit and a hook on an `iron_chain`.
- Tokonoma in the main room, a kitchen with a stone floor at ground level (doma), `barrel` storage.
- Temples: an open hall with a raised altar platform, `candle`s, `lantern`s on chains, banners.

## Landscaping

- Composition over abundance: moss, gravel, stone, water and a few trees, arranged asymmetrically in odd groups.
- Stepping-stone paths that wander; a `gravel` raked bed bordered by stones; a koi pond with a bridge.
- Bamboo fences (`bamboo_fence`) and a stone or plaster garden wall with a small tiled cap.
- Plants: `cherry_leaves`, `azalea_leaves`, `spruce_leaves` pine pads, `fern`, `large_fern`, `bamboo`; few flowers.

## Anti-patterns

- A pagoda as a stack of identical boxes with flat stair roofs; corners that do not lift.
- Shallow eaves. The deep shadow under the roof is half the style.
- Red everywhere. Vermilion belongs to shrines and gates, not every house.
- Symmetrical, crowded gardens; flower beds in cottage drifts.
- Glass blocks for walls; plain grey wool for shoji.

## Deviations from LESSONS

- **Plinth** (H06): replace the continuous plinth with posts on stone footings, a raised floor and a stone step at
  every entry. The raised floor is still required.
- **Glazing** (H10): shoji walls may exceed 20% glazed area; count them as screens.
- **Ground contact** (H14): moss, gravel and stone count as soft ground contact; no flower requirement.
- **Symmetry** (H11): temple halls and gates may be symmetric on the entrance axis; gardens never are.
- **Value contrast still applies** (LESSONS.md §1): a tiled roof over dark timber walls merges; keep plaster on every
  elevation.

## Reference builds

None in the repository yet. The ring-metric roofs in `examples/builds/b03_fairy_flower_cottage.py` show the hip and
flare techniques an irimoya builds on.
