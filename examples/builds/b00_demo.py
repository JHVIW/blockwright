"""b00 demo -- a tiny cottage scene exercising the blockwright library end-to-end.

Exercises: hip stair roof over an L-shaped plan (inner + outer corners), fences + gate, cobblestone wall line
with a lantern on it, glass panes, a door, a bed, tall flowers, vines, a tiny tree, campfire on hay, mushroom
blocks, a Frame-placed window technique on two facades, a pasted (rotated + mirrored) prefab, rooms/entrance.

Run:  python -m blockwright build examples/builds/b00_demo.py [--quick] [--no-render] [--no-qa] [--views=a,b]
"""
import sys

from blockwright import *

b = Build("00_demo", "Demo Scene", ground=0, description="Core-library demo: tiny L-shaped cottage with garden.")
oak, spruce = wood("oak"), wood("spruce")
SEED = 7

# --- ground: organic grass patch (cells left unset keep the natural terrain) -------------------------------
b.disk(7, 0, 7, 7, "grass_block")

# --- footprint: main body x2..8 z3..7 + bedroom wing x2..5 z7..10 -------------------------------------------
main = {(x, z) for x in range(2, 9) for z in range(3, 8)}
wing = {(x, z) for x in range(2, 6) for z in range(7, 11)}
plan = main | wing


def is_edge(cells, x, z):
    return any((x + dx, z + dz) not in cells for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))


walls = {c for c in plan if is_edge(plan, *c)}
for (x, z) in plan:   # foundation: mossy at the bottom fading to plain cobblestone (smooth noise, not white)
    b.set(x, 0, z, gradient([(-1, "mossy_cobblestone"), (0.6, "cobblestone")], x, 0, z, seed=SEED, jitter=0.8)
          if (x, z) in walls else spruce.planks)
for (x, z) in walls:
    corner = sum((x + dx, z + dz) in walls for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))) == 2 and \
        not ((x - 1, z) in walls and (x + 1, z) in walls) and not ((x, z - 1) in walls and (x, z + 1) in walls)
    b.fill(x, 1, z, x, 3, z, oak.stripped_log("y") if corner else oak.planks)
b.fill(3, 1, 7, 4, 2, 7, AIR)                       # opening between main room and wing
for (x, z) in plan:                                 # wall plate + ceiling (seals the rooms from the attic)
    b.set(x, 4, z, oak.stripped_log("y") if (x, z) in walls else spruce.planks)

# --- hip roof: stair rings over the plan expanded by 1 (overhang); resolve() makes the corners -------------
# Rings use the 8-neighbourhood so the concave corner of the L gets a stair too (-> inner corner / valley).
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
SIDES = (("north", (0, -1)), ("south", (0, 1)), ("west", (-1, 0)), ("east", (1, 0)))


def is_edge8(cells, x, z):
    return any((x + dx, z + dz) not in cells for dx in (-1, 0, 1) for dz in (-1, 0, 1))


ring = {(x + dx, z + dz) for (x, z) in plan for dx in (-1, 0, 1) for dz in (-1, 0, 1)}
y = 4
while ring:
    edge = {c for c in ring if is_edge8(ring, *c)}
    for (x, z) in sorted(edge):
        out = [d for d, (dx, dz) in SIDES if (x + dx, z + dz) not in ring]
        if not out:                                 # concave corner: only a diagonal neighbour is outside
            dz = next(dz for dx in (-1, 1) for dz in (-1, 1) if (x + dx, z + dz) not in ring)
            out = ["south" if dz > 0 else "north"]
        ridge = ("north" in out and "south" in out) or ("east" in out and "west" in out)
        b.set(x, y, z, spruce.slab("bottom") if ridge else spruce.stairs(OPP[out[0]]))
    ring -= edge
    for (x, z) in ring:
        if is_edge8(ring, x, z):                    # hidden planks under the next ring keep the roof face-connected
            b.set(x, y, z, spruce.planks)
    y += 1


# --- technique: a shuttered window with a flower sill, authored once in canonical frame coords -------------
def window(f, u, v, flower):
    f.set(u, v, 0, pane())
    f.set(u, v + 1, 0, pane())
    for du in (-1, 1):                                      # open trapdoor shutters folded against the wall
        f.set(u + du, v, 1, spruce.trapdoor("out", "bottom", open=True))
        f.set(u + du, v + 1, 1, spruce.trapdoor("out", "top", open=True))
    f.set(u, v - 1, 1, spruce.stairs("in", "top"))          # upside-down stair as a sill
    f.set(u, v, 1, potted(flower))


window(b.frame((8, 1, 5), "east"), 0, 0, "red_tulip")      # east facade
window(b.frame((5, 1, 3), "north"), 0, 0, "cornflower")    # north facade
window(b.frame((5, 1, 10), "south"), -1, 0, "allium")      # wing, south facade

# --- front door on the south facade, entrance marker just outside ------------------------------------------
front = b.frame((7, 1, 7), "south")
front.door(0, 0, 0, "spruce", facing="in", hinge="left")
front.set(0, -1, 1, "dirt_path")
front.entrance(0, 0, 1)
b.line((7, 0, 9), (11, 0, 11), "dirt_path")             # path to the garden gate

# --- interior --------------------------------------------------------------------------------------------
b.bed(3, 1, 9, "red", "north")                              # foot at z=9, head at z=8
b.set(4, 1, 4, "crafting_table")
b.set(3, 1, 4, barrel("up"))
b.set(7, 1, 4, chest("south"))
b.set(5, 3, 5, lantern(hanging=True))
b.set(6, 1, 6, spruce.slab("top"))
b.set(6, 2, 6, candle("white", 3))
b.room("living", 5, 1, 5)
b.room("bedroom", 4, 1, 9)

# --- vines on the north wall (no faces given: resolve attaches them like the game would) -------------------
for vy in (1, 2, 3):
    b.set(7, vy, 2, vine())

# --- garden: fence ring with a gate, tall flowers, tiny tree, campfire on hay, a mushroom ------------------
b.walls(10, 1, 8, 14, 1, 12, oak.fence)
b.set(10, 1, 11, oak.gate("east"))                         # in the west fence, opens east-west
b.tall(12, 1, 10, "lilac")
b.tall(13, 1, 9, "rose_bush")
b.tall(11, 1, 9, "peony")
b.set(12, 1, 11, "cornflower")
b.set(13, 1, 11, "oxeye_daisy")

b.fill(12, 1, 3, 12, 3, 3, oak.log("y"))                   # tiny tree
b.ellipsoid(12, 4, 3, 2, 1, 2, oak.leaves, where="air")
b.set(12, 5, 3, oak.leaves)

b.set(11, 0, 6, "hay_block")                               # signal campfire
b.set(11, 1, 6, campfire("south"))

b.fill(1, 1, 13, 1, 2, 13, "mushroom_stem")                # small huge red mushroom
b.fill(0, 3, 12, 2, 3, 14, "red_mushroom_block")
b.set(1, 4, 13, "red_mushroom_block")

# --- cobblestone wall line along the south edge with a lantern on it --------------------------------------
b.line((3, 1, 13), (9, 1, 13), stone("cobblestone").wall)
b.set(6, 2, 13, lantern())

# --- prefab: a little bench, pasted rotated (west side) and mirrored (garden) ------------------------------
bench = Build("prefab_bench", "bench")
bench.set(0, 0, 0, spruce.stairs("north"))
bench.set(1, 0, 0, spruce.stairs("north"))
bench.set(-1, 0, 0, spruce.trapdoor("west", open=True))
bench.set(2, 0, 0, spruce.trapdoor("east", open=True))
b.paste(bench, (0, 1, 5), rot=1)                          # seat now faces east, along the west wall
b.frame((6, 1, 12), "north").paste(bench, (0, 0, 0), mirror="x")   # back against the garden wall

b.note("Demo scene for the blockwright library; not a production building.")
if __name__ == "__main__":
    b.finish()
