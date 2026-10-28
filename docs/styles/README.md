# Style packs

A **style pack** is one markdown file that tells builder and critic agents what a style looks like in Minecraft
blocks. It does not repeat general craft: the universal rules live in [`../design/LESSONS.md`](../design/LESSONS.md)
and the block-level recipes in [`../design/techniques.md`](../design/techniques.md). A pack only adds what is
specific to its style.

| pack | mood | maturity |
|---|---|---|
| [`cottagecore.md`](cottagecore.md) | warm, cosy, whimsical vernacular | full pack, six palettes, a worked 20-building set, reference builds |
| [`medieval.md`](medieval.md) | sturdy, crowded, lived-in towns and keeps | starter |
| [`fantasy.md`](fantasy.md) | exaggerated, magical, glowing | starter |
| [`japanese.md`](japanese.md) | calm, ordered, deep eaves, gardens | starter |
| [`modern.md`](modern.md) | clean lines, glass, horizontal rhythm | starter |
| [`rustic.md`](rustic.md) | survival-friendly, early-game materials | starter |

Choose a pack when you scaffold a build:

```bash
python -m blockwright new <slug> --title "..." --style <style> [--palette my_blocks.txt]
```

The builder prompt then reads `docs/styles/<style>.md` next to LESSONS.md.

## What a pack contains

1. **Mood and identity.** One paragraph a builder can hold in their head while placing blocks.
2. **Palettes.** 2–6 named palettes, each with the same slots, so builders can swap one for another:

   | slot | meaning |
   |---|---|
   | roof field | the large roof surface |
   | roof trim | verge, eave lip, ridge cap: the continuous frame around the roof |
   | walls | the dominant visible wall material (with gradient members and shares) |
   | frame | posts, beams, columns, mullions |
   | foundation | plinth and ground storey stone |
   | accent | doors, shutters, awnings, one or two colour notes |
   | glass | panes or blocks used for windows |
   | lighting | lantern or lamp family for doors, paths and interiors |

   Use only real 26.3 block ids (check them against `blockwright/data/blocks_26.3.json`). State the value
   relationship: either a measured one from the colour table in `techniques.md` §2.1, or the intent ("dark roof over
   light walls").
3. **Signature motifs.** The 5–10 elements that make the style recognisable at a glance, each with a block-level
   hint or a pointer to a technique.
4. **Roof and wall recipes.** Pitches, profiles, trims and wall assemblies that belong to the style.
5. **Interior notes** per typical program (house, shop, workshop, temple, ...).
6. **Landscaping.** Plants, paths, water, props and how the style meets the ground.
7. **Anti-patterns.** Style-specific ways to fail, on top of `techniques.md` §6.
8. **Deviations from LESSONS.** Where the style legitimately breaks a universal rule, and what replaces it. Keep
   this list short; everything not listed still applies.
9. **Reference builds** (optional). Example scripts, renders or critiques that show the pack done well.

## How a pack combines with the rest

Precedence, highest first:

1. **The allowed-blocks constraint** (`--palette`), if the user set one. It is a hard limit: the builder uses only
   those blocks and QA reports every block outside it as an error in the `palette` check. When the pack calls for a
   block that is not allowed, the builder substitutes the closest allowed block of similar value and shape (a slab
   for a slab, a stair for a stair) and notes it in the log.
2. **The building brief** (program, size, mood).
3. **The style pack**, including its deviations from LESSONS.
4. **`LESSONS.md`**, then **`techniques.md`**.

A pack never relaxes QA: lighting, support, walkability and validity rules are the same for every style.

### Allowed-blocks files

The constraint is a plain text file, one entry per line:

```text
// survival base: what we have in the chests
# the comment lines above and here are ignored (// or "# " with a space)
oak_planks
*_planks
*_log
cobblestone
#minecraft:wool
```

* item ids without namespace (`oak_planks`), globs (`*_planks`, `stripped_*_log`), or block tags (`#minecraft:logs`);
* a line starting with `//` or with `# ` (hash and a space) is a comment; `#minecraft:...` without a space is a tag.

Check a finished build against it with:

```bash
python -m blockwright materials out/schematics/<slug>.litematic --allowed my_blocks.txt
```

## Writing a new pack

Copy this template to `docs/styles/<name>.md`, fill every section, and run an id check over the file. Aim for
80–150 lines for a starter pack; grow it with lessons and reference builds as you go.

```markdown
# <Style name>

**Mood:** <three to six words>.

<One paragraph: what the style is, what it values, what a passer-by should feel. Name the one or two things that
carry the style at a distance (usually roof shape and wall colour).>

## Palettes

### <Palette name> (<one-line character>)
| slot | blocks |
|---|---|
| roof field | `<id>` stairs/slabs ... |
| roof trim | ... |
| walls | `<id>` 60% · `<id>` 30% · `<id>` 10% |
| frame | ... |
| foundation | ... |
| accent | ... |
| glass | ... |
| lighting | ... |

Value: <measured L numbers from techniques.md §2.1, or the intent>.

## Signature motifs
- **<motif>**: <block-level hint or technique reference>.

## Roof recipes
## Wall recipes
## Interiors
## Landscaping
## Anti-patterns
## Deviations from LESSONS
## Reference builds
```

Good packs are opinionated. "Use dark oak or spruce" is weaker than "dark-oak field, spruce barge board, slab ridge;
spruce only over walls that are at least 40% plaster".
