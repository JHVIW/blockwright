# Lessons (read before building anything)

These are the mistakes that cost real rounds. In the example cottagecore set, each of the first three buildings
took three builder → critic rounds to climb from about 4–5/10 to about 7/10, and the same problems came up every
time. None of them are specific to cottagecore: they are about how Minecraft blocks read at a distance. Avoid them
from the first block and you start at round 3's level.

The rules below apply to **every style**. A style pack (`docs/styles/<style>.md`) may override a rule only where the
style genuinely demands it, and it says so in its "Deviations from LESSONS" section. Recipes and diagrams for
everything mentioned here are in [`techniques.md`](techniques.md).

## 1. Value contrast beats detail (the #1 problem every time)

**Roof ≠ walls.** The roof field must differ from the dominant visible wall material by **at least 40 luminance
(L, 0–255) or by a clear hue change**. Look up L values in the measured colour table, [`techniques.md` §2.1](techniques.md).
A wood roof over mostly-wood walls merges into one brown mass no matter how detailed it is.

| walls are mostly… | roof field that works | why |
|---|---|---|
| timber, brick or dark stone | slate (`deepslate_tiles`, L 55) or clay tile (`cinnabar_bricks`, L 75) when the walls are warm and mid-value; a light or coloured field (waxed cut copper, `cherry_planks`) when the walls are dark | hue or value break |
| ≥ 40% light plaster / pale stone | dark wood (`dark_oak_planks`, L 47; `spruce_planks`, L 89), slate, tuff brick | ≥ 40 L darker |
| light wood (birch, pale oak, bamboo) | slate, dark oak, tuff brick | value break |

Examples that worked in the example set: a `tuff_bricks` slate-like field with dark-oak trims over timber and plaster
(`examples/builds/b01_cozy_starter_cottage.py`); a `deepslate_tiles` field with a `deepslate_bricks` hem and
`polished_deepslate_slab` ridges over a brick-and-timber farmhouse (`docs/examples/critiques/02_round2.md`); a
`cherry_planks` bell roof over pale plaster and dark timber (`examples/builds/b03_fairy_flower_cottage.py`).

**Measure the light share per elevation.** Light material (plaster, pale stone, white panels, whatever your style's
light family is) has to be visible where the eye looks: on the gable you face from the front, on jetties and on bay
heads. Light material hidden behind porches or roofs does no good. **Aim for at least 10% light share on every
elevation.** Count first-hit blocks per elevation with a small counter in your script (see `shares()` in
`examples/builds/b01_cozy_starter_cottage.py`), not by eye. If the light share cannot reach 10%, change the value
balance with the roof (it is the only large surface that can) or raise the wall plate a course so more wall shows.

**Pale trim on dark walls.** Shutters, sills and planter fronts in a pale material stop windows reading as black
holes. Vary shutters 2/1/0 per window. Pale trim vanishes on white walls, so use a dark wood there.

## 2. Noise is the second "AI tell"

- **No per-block speckle anywhere**: not in roofs, walls, chimneys or towers. Single random cells read as static.
- Weathering goes only in **runs of 2–5 cells along a course**, using a same-value neighbour block, and on roofs
  only in the two eave courses (course 1 about 50%, course 2 about 20%). Choose runs with value noise stretched
  along the course, never `random`.
- Material gradients use smooth value noise at a scale of 3–5 blocks, plus a height bias (darker low, lighter high).
- Moss on a normal roof is `moss_carpet` only, on shady slopes and the lowest courses, at most 10% of the slope.
  Never `moss_block` cubes inside a stair field: they read as holes.
- **Check a render without shadows** before calling something noise. Sun shadows on a flat field make dark
  rectangles too; the cure for those is a calm field plus a hem, not more block variety.

## 3. Roof construction

- **45° (stairs only) is the default.** Steeper parts use **stair-on-stair** (a stair directly under a stair, same
  facing), never plank or block risers: flat faces under stairs read as "wedding cake" boxes.
- **Ridges are low slab caps** in the field family (or a `*_wall` row for a rounded tile ridge), with a full block
  only under a finial. Log ridges read as beams lying on the roof.
- **Trims form one continuous frame**: verge, eave lip and ridge read as a single line around the roof. Pick one
  verge treatment per building: a solid 2-thick verge in the field material (when the gable wall is light) *or* a
  contrasting barge board (when the field is dark and the gable is not). Never both dark.
- **Every visible edge is two layers thick** (stair + inverted stair or block under it) and overhangs ≥ 1.
- **Dormers are real gabled dormers** with their own slab ridge, set back from the eave. Never a flat-lidded box or a
  log stub lying on the slope.
- **Flared eaves**: a slab kick plus a top slab at the foot. Bell and catslide feet curve out.
- **Round or octagonal roofs** use the ring metric

  `k = max(|dx|, |dz|, |dx| + |dz| - 2)`

  around the centre, so every ring is exactly one cell wide and the hips are clean. Where two cells of a ring only
  touch diagonally, add a hidden helper stair in the inner cell so `resolve` shapes the corners. Working code:
  `octk` and `cone_rings` in `examples/builds/b03_fairy_flower_cottage.py`, and the cap in
  `examples/builds/b04_mushroom_cottage.py`.
- **Roof-to-wall balance**: if the roof hides the walls, lower the ridge (45° tops) or raise the wall plate one
  course.

## 4. Chimneys

- **Slim** above the roof (2×2 or 2×3), with a rim and 1–2 pots. Big 3×3 or 4×5 crowns read as boxes or hats.
- **Hidden campfire for smoke**: a lit `campfire` 1–2 blocks below the rim, walled in on all sides, with open air
  above. No flame visible from outside. Smoke particles collide with blocks and live about 6–9 blocks, so a campfire
  at the bottom of a long flue gives no smoke on the roof.
- Clean brick or stone, or a deliberate gradient (stone base → stepped course → brick). No random grey squares.
- Never stand a pot or carpet on a bottom slab: it floats half a block.

## 5. Trees

- Canopies are **domes or umbrellas** with an irregular edge and cut corners. Never flat stacked layers, spheres or
  cubes.
- Hang **1–3-long drips from the rim only**, never from the middle of the underside.
- Hide limb tips inside the leaves. **Logs touch face to face** (QA's floating check fails on edge-only contact); a
  2-wide trunk band reads as a smooth diagonal lean instead of a zig-zag.
- Keep **≥ 2 air between a canopy and any roof**, and keep canopies out of chimney smoke.
- Recipes that worked: the oak dome in `examples/builds/b01_cozy_starter_cottage.py` (`orchard_tree`) and the
  weeping cherry "T9" in `examples/builds/b03_fairy_flower_cottage.py` (numbers in
  `docs/examples/critiques/03_round2.md` §2).

## 6. Composition

- **One clear hierarchy per front**: hero element → secondary gable or volume → detail. Avoid mirrored gables and
  "bookend" trees either side of the door.
- **No flat plane longer than 6 blocks**: break it with a porch, a lean-to, a jetty, a buttress, a bay or a change of
  material.
- Silhouette first. If the four iso views do not each show a different, interesting outline, no amount of detail
  will save it.

## 7. Entrances

- The entrance must be the **obvious way in**: a porch or hood with its own small roof, a step up, a lantern
  **beside** the transom (not in front of it), and an accent-coloured door.
- Keep the door zone clear of clutter: free 1×2 cells in front and behind, nothing blocking the step.

## 8. Interiors

- **Complete for the function.** Every room in the program is there and furnished for its purpose: a bakery has
  ovens, counters and a flour store; a smithy has a forge, anvil and tool wall. One focal piece per room, furniture
  along 30–60% of the wall-adjacent floor, centre free.
- **Reachable.** Every floor and room is reachable through cells with ≥ 2 headroom; stairs have ≥ 2 air above every
  step and landing. QA's walkability check must pass.
- **Lit so nothing spawns.** Overworld hostiles spawn at block light 0 in 26.3, so every standable cell needs block
  light ≥ 1. Attics, cellars and stair halls count. Mix ambient (hanging lanterns), task (candles) and focal (hearth)
  light; hide strong sources (a froglight under a carpet lights a room invisibly).
- Walls, floor and ceiling in different materials.

## 9. Lighting outside

- A light at every door and every 6–9 blocks along paths. Lanterns on brackets, posts or chains, never torches
  sprayed over walls and never lanterns every 2 blocks.
- Light sources need legal support (a lantern needs a sturdy centre above or below); QA checks this.

## 10. Landscaping

- **Organic, 3–6 blocks around the building, fading out**: dense planting at the walls, beds and props next,
  scattered singles after that, then the natural terrain. Unset cells stay air so the world shows through.
- **No platform**: the landscaped outline is a union of irregular blobs, never the bounding box, and no edge runs
  straight for more than 7 blocks.
- One continuous worn path with speckle only on its edges.
- Ponds are organic, bean-shaped, with banks planted or mossy and no bare dirt.
- Flower colour in drifts of 3–7 of one species, 2 lead species + 1 filler per building; carry the pinks, blues and
  purples, not only white and yellow.
- Bushes in irregular shapes, never 2×2×2 cubes.

## 11. The process that worked

1. **Massing and roof first.** Render with `--quick` and look at all four iso views (open the PNG with the Read tool;
   do not trust your mental model).
2. **Then materials and contrast.** Check the roof-vs-wall value rule and measure each elevation's light share with
   your own counter.
3. **Then details, interior and landscaping.**
4. **Save a `compare_*.png` before/after** for every major change, so you judge by looking, not by memory.
5. **At least five render → look → fix cycles**, with close-ups (`--closeup X,Y,Z,r,az,el`) of the entrance, the
   roof edges and the chimney.
6. Keep the bounding box tidy. A box bigger than the guideline is fine when the landscaping needs it.
7. A critic round with fresh eyes (see `skills/blockwright/templates/critic_prompt.md`) reliably finds the one or
   two changes worth two points. Example critiques: `docs/examples/critiques/02_round2.md` (the reusable roof
   recipe, the slate field and the wall treatment), `docs/examples/critiques/01_round2.md` (the tuff roof) and
   `docs/examples/critiques/03_round2.md` (the bell roof profile and the T9 tree).

The smallest complete script to start from is `examples/builds/b00_demo.py`; the finished references are
`b01_cozy_starter_cottage.py`, `b03_fairy_flower_cottage.py` and `b04_mushroom_cottage.py`. Reuse their techniques
(roof functions, ring metric, tree recipes, gradients), not their designs.

## Add your own lessons

Every project learns things this file does not know yet. Keep them in your workspace at `notes/LESSONS.md`: one
bullet per lesson, phrased as a rule with a number where possible, and a pointer to the critique or script that proved
it. Builder and critic prompts read it alongside this file. When a lesson turns out to hold for every style, it is a
candidate for this file.
