# Fantasy

**Mood:** exaggerated, magical, glowing, storybook-strange.

Fantasy takes a believable building and pushes one or two things too far: a roof that curls, a tower that leans, a
house grown out of a mushroom or a tree, crystals breaking through the foundation, light that comes from things
rather than lamps. The skill is restraint everywhere else. Structure still reads as wood and stone with honest
weight; the magic is the accent. Carried at a distance by **an unmistakable silhouette** (spires, curves, a giant
cap or trunk) and, at dusk, by **glowing accents** in a few deliberate places.

## Palettes

### Starlit Spire (wizard tower: pale stone, dark slate, amethyst)
| slot | blocks |
|---|---|
| roof field | `deepslate_tile_stairs` witch-hat cones (63° + flare); or `waxed_oxidized_cut_copper_stairs` for a teal spire |
| roof trim | `polished_blackstone_brick_stairs` lip and hips; finial `end_rod` on a `polished_blackstone_brick_wall` |
| walls | `calcite` 45% · `polished_diorite` 25% · `smooth_quartz` 15% · `tuff_bricks` 15% low |
| frame | `polished_deepslate` bands and window surrounds, `dark_oak_log` balcony posts |
| foundation | `cobbled_deepslate` 40% · `deepslate_bricks` 30% · `tuff` 20% · `mossy_cobblestone` 10% |
| accent | `amethyst_block` and `amethyst_cluster` breaking through the plinth, `purple_stained_glass_pane` in one rose window |
| glass | `glass_pane`, one coloured feature window |
| lighting | `waxed_copper_lantern` (green flame), `end_rod`, `pearlescent_froglight` hidden under carpet |

Value: slate L 55 over calcite L 224: the strongest dark-over-light split in the game.

### Toadstool Hollow (mushroom house)
| slot | blocks |
|---|---|
| roof field | `red_mushroom_block` cap on a smooth height field (or `brown_mushroom_block` for a flat cap) |
| roof trim | a `mushroom_stem` gill ring under the cap rim, `brown_mushroom_block` underside |
| walls | `mushroom_stem` 60% · `pale_oak_planks` 25% · `calcite` 15% |
| frame | `stripped_dark_oak_log` door and window frames, curved with stairs |
| foundation | `mossy_cobblestone`, `moss_block`, `rooted_dirt`, `podzol` |
| accent | `shroomlight` spots, `glow_lichen` in nooks, `red_mushroom`/`brown_mushroom` on `podzol`, `spore_blossom` |
| glass | round `glass_pane` portholes (techniques.md §3.3.4) |
| lighting | `shroomlight`, `lantern` |

Value: red cap over pale stem is a hue and value break. Working example: `examples/builds/b04_mushroom_cottage.py`.

### Elderroot (tree house)
| slot | blocks |
|---|---|
| roof field | `spruce_stairs` or a living moss roof, small and many (a cluster of pods), each with a flared lip |
| roof trim | `dark_oak_stairs`, continuous on every pod |
| walls | `stripped_oak_log` 50% · `oak_planks` 30% · `pale_oak_planks` 20% (light pods against the dark trunk) |
| frame | the tree: `dark_oak_wood` trunk, `mangrove_roots` and `rooted_dirt` flare, `oak_wood` limbs |
| foundation | roots and `mossy_cobblestone` boulders; walkways of `spruce_slab` on `iron_chain` or brackets |
| accent | `cave_vines` with berries, `azalea_leaves`/`flowering_azalea_leaves` canopy, rope bridges of `*_fence` and slabs |
| glass | `glass_pane` |
| lighting | `lantern` on chains, `verdant_froglight` glow in the canopy |

### Ember Court (nether-tinged, for dark-lord or forge-temple builds)
| slot | blocks |
|---|---|
| roof field | `polished_blackstone_brick_stairs` |
| roof trim | `gilded_blackstone` corners, `crimson_stairs` lip |
| walls | `crimson_planks` 50% · `nether_bricks` 30% · `crimson_hyphae` 20% |
| frame | `warped_stem` posts (teal against crimson) |
| foundation | `blackstone`, `basalt`, `smooth_basalt` |
| accent | `shroomlight`, `warped_wart_block`, `soul_lantern` |
| glass | `black_stained_glass_pane` |
| lighting | `shroomlight`, `soul_lantern` (10), `lantern` |

Value: keep the walls (crimson, mid-dark) and roof (blackstone, dark) apart with gold corners and teal posts; this
palette fails the 40 L rule on value alone, so hue must do the work.

## Signature motifs

- **Exaggerated silhouettes**: lean a tower 1 block per 4–6 of height, taper or bulge walls, bend the tip of a
  witch-hat cone (offset the top 3–4 rings), stack roofs in tiers.
- **Spires and needles**: 63° cones with a 2-course flare, an `end_rod` or `lightning_rod` finial, small turrets on
  corbels (inverted-stair rings).
- **Curved and organic roofs**: height-field caps and bells; ring metric `k = max(|dx|,|dz|,|dx|+|dz|-2)` for round
  plans; horned verge tips and curled eaves.
- **Mushroom and tree houses**: the host organism is the structure; rooms are pods or hollows.
- **Crystals**: `amethyst_block` outcrops with `amethyst_cluster` and `large_amethyst_bud` on their faces, in 2–3
  clusters, never everywhere.
- **Glowing accents**: froglights, shroomlights, glow-berry strands, copper lanterns, candles; a few strong points
  and a soft scatter.
- **Round and arched windows**, rose windows, doors with round heads.
- **Visible support for everything that "floats"**: chains, roots, vines, brackets. QA's floating check applies to
  magic too.

## Roof recipes

- Witch hat: 63° stair-on-stair cone, 2-course flare at the base, bent tip, dark lip.
- Mushroom cap: height field `T(r)` over a round plan, underside one block in, stem ring under the rim.
- Bell: concave profile (techniques.md §3.1.4) on octagonal rings, as in `examples/builds/b03_fairy_flower_cottage.py`.
- Tiered pagoda-like stacks: each tier smaller and flared, joined by short wall drums.

## Interiors

- Wizard tower: spiral stair around a log core, a library ring, an alchemy room (`brewing_stand`, `cauldron`,
  `*_shelf` with `decorated_pot`s), an observatory under the cone.
- Mushroom/tree house: round rooms, curved walls with inverted stairs, furniture built into the walls, glow sources
  hidden in nooks.
- Light every room to block light ≥ 1 regardless of mood; gloom comes from soft, low sources, not darkness.

## Landscaping

- Fairy rings of mushrooms on `podzol`, mossy boulders, giant mushrooms as trees, glowing ponds (`sea_pickle` in
  water), `firefly_bush` clumps, crystals in the rocks.
- Paths that wind; stepping stones; arched bridges over a stream.
- Trees with character: weeping, gnarled pale oak with `pale_hanging_moss`, cherry umbrellas (techniques.md §5.4).

## Anti-patterns

- Random colour as "magic": purple wool walls, rainbow glass, every block a different hue.
- Glow everywhere: froglights on every surface flatten the scene. Two or three focal glows, the rest soft.
- Floating islands or rocks with no visible support (QA fails them, and they read as glitches).
- Exaggerating everything at once: if the tower leans, the walls bulge, the roof curls and crystals sprout, nothing
  reads. Pick one hero exaggeration per building.

## Deviations from LESSONS

- **Pitch** (H04): roofs may go well beyond 63° and below 45° where a curve demands it.
- **Symmetry** (H11): stronger asymmetry is expected, not just tolerated.
- **Accents** (H09): up to 3 accent materials if one of them is a light source.
- Roof-vs-wall value contrast (LESSONS.md §1) still applies, as does the no-speckle rule.

## Reference builds

- `examples/builds/b03_fairy_flower_cottage.py`: octagonal bell roofs, weeping cherry, fairy ring.
- `examples/builds/b04_mushroom_cottage.py`: mushroom cap on a height field.
