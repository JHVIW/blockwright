"""b04 Woodland Mushroom Cottage -- "Toadstool Hollow".

A round mushroom-stem cottage under a giant red mushroom cap (15 across, a domed umbrella with white warts, pale
gill underside with radial ribs).  The stem tapers: an 11-wide ground storey steps in at a pale "annulus" shoulder
to a 9-wide loft storey that carries the cap.  A brown-capped pantry grows out of the east flank, a little brown
canopy shelters the door, a tuff chimney pierces the cap at the back, and a woodland garden (podzol, ferns,
mushrooms, a fallen log, a toadstool lamp, birch and spruce) surrounds it.  See docs/logs/04_mushroom_cottage.md.

Top view (x east, z south; main stem centre 0,0, pantry centre 9,1):

          z-7         C C                C  chimney 2x2 -> corbelled crown
          z-5      # # # # #             ground storey: octagon ring 5 (11 wide), loft storey ring 4 (9 wide)
                 #           #
        b      #   hearth N    #  .  p p p       p  pantry (5-wide octagon) under a brown plate cap
        b bay  #   loft above  # = p       p     =  neck at z=1
        b      #     table     #   p       p
                 #           #       p p p
          z+5      # ( D ) #
                    [porch]              brown canopy on two fence posts, step

Run:  python -m blockwright build examples/builds/b04_mushroom_cottage.py [--quick] [--no-render] [--no-qa] [--views=a,b]
      python -m blockwright build examples/builds/b04_mushroom_cottage.py --look X,Y,Z,r,az,el ...   (close-ups, authored coordinates)
      python -m blockwright build examples/builds/b04_mushroom_cottage.py --shares                    (first-visible material share per side)
"""
import math
import sys

from blockwright import *

G = 0
b = Build("04_mushroom_cottage", "Woodland Mushroom Cottage", ground=G,
          description="Round mushroom-stem cottage under a giant red cap, brown-cap pantry, loft, woodland garden.")
doak, spruce, birch, oak = wood("dark_oak"), wood("spruce"), wood("birch"), wood("oak")

DIRS = {"north": (0, -1), "east": (1, 0), "south": (0, 1), "west": (-1, 0)}
CW = list(DIRS)
FACES6 = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0), "up": (0, 1, 0),
          "down": (0, -1, 0)}


def n4(x, z):
    return [(x + dx, z + dz) for dx, dz in DIRS.values()]


def octk(c, cut):
    return lambda x, z: max(abs(x - c[0]), abs(z - c[1]), abs(x - c[0]) + abs(z - c[1]) - cut)


def facing_in(x, z, c=(0, 0)):
    """compass direction from (x,z) toward the centre c (dominant axis)."""
    dx, dz = c[0] - x, c[1] - z
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


# ------------------------------------------------------------------------------------------------------------
# plan
# ------------------------------------------------------------------------------------------------------------
MAIN_C, PAN_C = (0, 0), (9, 1)
KM, KP = octk(MAIN_C, 2), octk(PAN_C, 1)
low = {(x, z) for x in range(-6, 7) for z in range(-6, 7) if KM(x, z) <= 5}        # ground storey
low_wall = {c for c in low if KM(*c) == 5}
low_in = low - low_wall
up_wall = {c for c in low if KM(*c) == 4}                                           # loft storey wall ring
up_in = {c for c in low if KM(*c) <= 3}
pan = {(x, z) for x in range(6, 13) for z in range(-3, 6) if KP(x, z) <= 2}
pan_wall = {c for c in pan if KP(*c) == 2}
pan_in = pan - pan_wall
NECK_WALL = {(6, 0), (6, 2)}
FOOT = low | pan | {(6, 0), (6, 1), (6, 2)}
SKIRT_Y = 7                       # the annulus shoulder course (ring 5)


# ------------------------------------------------------------------------------------------------------------
# materials
# ------------------------------------------------------------------------------------------------------------
def plinth_stone(x, y, z):
    n = value3(x, y, z, 41, 2.4)
    if y <= 0:
        return "mossy_cobblestone" if n < 0.5 else ("cobbled_deepslate" if n < 0.8 else "tuff")
    if n < 0.32:
        return "mossy_cobblestone"
    if n < 0.62:
        return "tuff"
    if n < 0.82:
        return "mossy_stone_bricks"
    return "cobbled_deepslate"


STAIR_OF = {"mossy_cobblestone": "mossy_cobblestone", "tuff": "tuff", "mossy_stone_bricks": "mossy_stone_brick",
            "cobbled_deepslate": "cobbled_deepslate"}


def stone_top(x, z):
    """plinth top course: y1, and y2 where the mossy stone climbs into the stem (smooth noise runs)."""
    return 2 if value2(x, z, 43, 2.2) > 0.5 else 1


def chimney_stone(x, y, z):
    n = value3(x, y, z, 53, 2.0)
    if y <= 2:
        return "mossy_cobblestone" if n < 0.55 else "cobbled_deepslate"
    if y <= 9:
        return "tuff" if n < 0.6 else ("cobbled_deepslate" if n < 0.85 else "mossy_cobblestone")
    return "tuff_bricks"


def mush(block, faces):
    return state(block, **{d: (d in faces) for d in FACES6})


def cap_state(x, y, z, cells, top_of, block):
    """up faces red, down faces pores; a side face is red when it looks at open air above the neighbouring
    column's cap (or beyond the cap), pores when it looks into the space under the cap (gills, dome inside)."""
    faces = set()
    for d, (dx, dy, dz) in FACES6.items():
        n = (x + dx, y + dy, z + dz)
        if n in cells or d == "down":
            continue
        t = top_of(n[0], n[2])
        if d == "up" or t is None or n[1] > t:
            faces.add(d)
    return mush(block, faces)


# ------------------------------------------------------------------------------------------------------------
# the red cap: a height field per column (ring = rounded distance from the stem axis)
# ------------------------------------------------------------------------------------------------------------
CAP_R = 7.45
TOP = {0: 16, 1: 16, 2: 16, 3: 15, 4: 15, 5: 14, 6: 13, 7: 12}     # dome profile per ring
UNDER_GILL, UNDER_RIM = 11, 10


def cap_r(x, z):
    return math.hypot(x, z)


import os
CAP_CUT = int(os.environ.get("CAP_CUT", "-1"))     # -1 = round rings (chosen; octagons read boxy)


def cap_k(x, z):
    """octagonal ring index (every terrace exactly one cell wide, clean hips) -- lessons 3"""
    if CAP_CUT < 0:
        return round(cap_r(x, z))
    return max(abs(x), abs(z), abs(x) + abs(z) - CAP_CUT)


def cap_top(x, z):
    return TOP[min(7, cap_k(x, z))]


def cap_under(x, z):
    """the rim curls down one block only over the south front (the door side); elsewhere a 2-thick edge."""
    if cap_k(x, z) >= 7 and abs(math.degrees(math.atan2(z, x)) - 95) < 48:
        return UNDER_RIM
    return UNDER_GILL


STACK_COLS = {(-2, -6), (-1, -6), (-2, -7), (-1, -7), (-2, -8), (-1, -8)}
CAP_COLS = {(x, z) for x in range(-9, 10) for z in range(-9, 10) if cap_k(x, z) <= 7}
CAP = set()
WALL_TOP = {}                               # loft wall columns: highest wall y
for (x, z) in CAP_COLS:
    t = cap_top(x, z)
    if (x, z) in up_in:
        lo = min([t] + [cap_top(*n) for n in n4(x, z)]) - 1      # closed 2-thick shell over the loft
    else:
        lo = cap_under(x, z)
        if (x, z) in up_wall:
            WALL_TOP[(x, z)] = lo - 1
    for y in range(lo, t + 1):
        CAP.add((x, y, z))


def red_top(x, z):
    return cap_top(x, z) if (x, z) in CAP_COLS else None


# ------------------------------------------------------------------------------------------------------------
# 1. foundations, plinth, floors
# ------------------------------------------------------------------------------------------------------------
for (x, z) in FOOT:
    if (x, z) in low_wall or (x, z) in pan_wall or (x, z) in NECK_WALL:
        b.set(x, -1, z, "cobbled_deepslate")
        for y in range(0, stone_top(x, z) + 1):
            b.set(x, y, z, plinth_stone(x, y, z))
    else:
        b.set(x, 0, z, "dirt")
        edge = any(n not in FOOT or n in low_wall for n in n4(x, z)) and (x, z) in low_in
        b.set(x, 1, z, doak.planks if edge else spruce.planks)

# ------------------------------------------------------------------------------------------------------------
# 2. stem walls: ground storey ring 5 (to y6), annulus shoulder y7, loft storey ring 4 (y7 up into the cap);
#    pantry and neck walls to y5
# ------------------------------------------------------------------------------------------------------------
for (x, z) in low_wall:
    for y in range(stone_top(x, z) + 1, SKIRT_Y):
        b.set(x, y, z, "mushroom_stem")
    b.set(x, SKIRT_Y, z, stairs("pale_oak", facing_in(x, z)))
for (x, z) in up_wall:
    for y in range(SKIRT_Y, WALL_TOP[(x, z)] + 1):
        b.set(x, y, z, "mushroom_stem")
for (x, z) in pan_wall | NECK_WALL:
    for y in range(stone_top(x, z) + 1, 6):
        b.set(x, y, z, "mushroom_stem")
for y in (2, 3):                                               # passage main -> neck -> pantry
    for x in (5, 6, 7):
        b.remove(x, y, 1)
for y in (4, 5):
    b.set(6, y, 1, "mushroom_stem")

# ------------------------------------------------------------------------------------------------------------
# 3. red cap, warts, gill ribs
# ------------------------------------------------------------------------------------------------------------
for (x, y, z) in CAP:
    b.set(x, y, z, cap_state(x, y, z, CAP, red_top, "red_mushroom_block"))
# amanita warts: white carpet patches lying on the terraces (flat, so no pale cubes stick out of the dome)
SPOTS = [(-1, -1, 2), (3, 1, 1), (-3, 3, 2), (3, -4, 1), (-5, -1, 2), (0, -4, 1), (4, 3, 2), (1, 5, 1),
         (-4, 4, 1), (5, -1, 1), (-2, -5, 1), (6, 2, 1), (-6, 2, 2), (2, -6, 1), (-1, 6, 2), (5, -4, 1),
         (-4, -4, 2), (1, 2, 1)]
WARTS = []
for (x, z, n) in SPOTS:
    for (cx, cz) in [(x, z), (x + 1, z), (x, z + 1)][:n]:
        if (cx, cz) in CAP_COLS and (cx, cz) not in STACK_COLS:
            b.set(cx, cap_top(cx, cz) + 1, cz, carpet("white"))
            WARTS.append((cx, cz))
# fallen birch leaves gathered on the shady north-west terraces of the cap (two small drifts, under the birch)
for (x, z) in ((-4, -5), (-5, -4), (-4, -4), (-3, -6), (-6, -3), (-5, -5), (-2, -6), (-6, -2)):
    if (x, z) in CAP_COLS and (x, z) not in WARTS and (x, z) not in STACK_COLS:
        y = cap_top(x, z) + 1
        if (x, y, z) not in b:
            b.set(x, y, z, state("leaf_litter", segment_amount=2 + hash3(x, 0, z, 81) % 3,
                                 facing=CW[hash3(x, 1, z, 82) % 4]))
RIBS = set()
for i in range(18):
    a = (i + 0.5) / 18 * 2 * math.pi
    for rr in (5.6, 6.2):
        x, z = round(rr * math.cos(a)), round(rr * math.sin(a))
        if (x, z) in CAP_COLS and (x, z) not in low and cap_under(x, z) == UNDER_GILL and cap_k(x, z) < 7:
            RIBS.add((x, UNDER_GILL - 1, z))
for p in RIBS:
    b.set(*p, "mushroom_stem")

# ------------------------------------------------------------------------------------------------------------
# 4. brown cap over the pantry: a flat plate (y6) with a raised centre (y7)
# ------------------------------------------------------------------------------------------------------------
BCAP, BTOP = set(), {}
for x in range(5, 15):
    for z in range(-4, 7):
        ra = math.hypot(x - PAN_C[0] - 0.2, z - PAN_C[1])
        if ra > 3.95 or (x, z) in low:
            continue
        BCAP.add((x, 6, z))
        BTOP[(x, z)] = 6
        if ra <= 2.75:
            BCAP.add((x, 7, z))
            BTOP[(x, z)] = 7
for (x, y, z) in BCAP:
    b.set(x, y, z, cap_state(x, y, z, BCAP, lambda a, c: BTOP.get((a, c)), "brown_mushroom_block"))

# ------------------------------------------------------------------------------------------------------------
# 5. chimney (NNW), round 2: a slim 2x2 stack graded in courses (mossy base -> stepped tuff water table -> tuff ->
#    tuff bricks above the cap), crooked: at y14..15 the head leans north on corbels (2 wide x 3 deep, so the fire
#    in its middle cell is walled by stack on 3 sides and a tuff-brick wall on the 4th), a polished-tuff slab rim,
#    pots on the two full corners, open sky over the campfire.  No 3x3 crown.
# ------------------------------------------------------------------------------------------------------------
STACK = [(-2, -6), (-1, -6), (-2, -7), (-1, -7)]
HEAD = [(x, z) for x in (-2, -1) for z in (-9, -8, -7)]


def chimney_course(y):
    if y <= 3:
        return ("mossy_cobblestone", "cobbled_deepslate", "mossy_cobblestone", "cobbled_deepslate", "mossy_cobblestone")[y + 1]
    if y <= 9:
        return "tuff"
    return "tuff_bricks"


for (x, z) in STACK:
    for y in range(-1, 14):
        b.set(x, y, z, chimney_course(y))
for z in (-6, -7):                                              # 3x2 footing with a stepped west shoulder
    for y in range(-1, 5):
        b.set(-3, y, z, chimney_course(y))
    b.set(-3, 5, z, stairs("tuff", "east"))
for x in (-2, -1):                                              # battered foot + stepped water table (north)
    b.set(x, 0, -8, "mossy_cobblestone")
    b.set(x, 1, -8, stairs("mossy_cobblestone", "south"))
    b.set(x, 4, -8, stairs("tuff", "south"))
b.set(-3, 4, -8, stairs("tuff", "south"))
for x in (-2, -1):                                              # the lean: corbels, steps, shifted head
    b.set(x, 12, -8, stairs("tuff_bricks", "south", "top"))
    b.set(x, 13, -8, "tuff_bricks")
    b.set(x, 13, -9, stairs("tuff_bricks", "south", "top"))
    b.set(x, 14, -6, stairs("tuff_bricks", "north"))
FLUE = (-1, -8)
for (x, z) in HEAD:
    b.set(x, 14, z, "tuff_bricks")
b.set(FLUE[0], 14, FLUE[1], campfire("south"))                  # walled by the head on 3 sides ...
b.set(0, 14, -8, "tuff_bricks")                                 # ... and a corbelled block on the 4th
b.set(0, 13, -8, stairs("tuff_bricks", "west", "top"))
b.set(0, 15, -8, slab("polished_tuff"))
for (x, z) in HEAD:                                             # rim course one above the fire, open sky over it
    if (x, z) == FLUE:
        continue
    b.set(x, 15, z, "polished_tuff" if (x, z) in ((-2, -9), (-1, -7)) else slab("polished_tuff", "top"))
b.set(-2, 16, -9, "decorated_pot")
b.set(-1, 16, -7, potted("fern"))
for y in (10, 11):                                              # ivy on one column of the north face
    b.set(-1, y, -8, vine())

for x in (-2, 0):                                               # hearth: tuff cheeks in the wall, fire between
    for y in (2, 3, 4):
        b.set(x, y, -5, "tuff_bricks")
b.set(-1, 2, -5, campfire("south"))
b.set(-1, 3, -5, "tuff_bricks")
b.set(-1, 4, -5, "chiseled_tuff_bricks")
for x in (-2, -1, 0):
    b.set(x, 5, -5, "polished_tuff")
for x in (-2, -1, 0):                                           # mantel
    b.set(x, 4, -4, doak.stairs("north", "top"))
b.set(-2, 5, -4, candle("white", 3))
b.set(-1, 5, -4, potted("fern"))
b.set(0, 5, -4, potted("red_mushroom"))

# ------------------------------------------------------------------------------------------------------------
# 6. stem base flare (the volva): stone stairs on the ring outside the ground storey, in runs with gaps
# ------------------------------------------------------------------------------------------------------------
FLARE = set()
for x in range(-7, 8):
    for z in range(-7, 8):
        if KM(x, z) != 6 or (x, z) in FOOT or (x, z) in STACK or (x <= -6 and abs(z) <= 2) or (x >= 6 and -1 <= z <= 3):
            continue
        if abs(x) <= 2 and z == 6:
            continue                                            # porch
        if value2(x, z, 47, 1.6) < 0.45:
            continue
        mat = plinth_stone(x, 1, z)
        b.set(x, 0, z, plinth_stone(x, 0, z))
        b.set(x, 1, z, stairs(STAIR_OF[mat], facing_in(x, z)))
        FLARE.add((x, z))

# ------------------------------------------------------------------------------------------------------------
# 7. loft floor over the north half (stand y8), a stem pillar with a ladder, railing
# ------------------------------------------------------------------------------------------------------------
LOFT = {(x, z) for (x, z) in up_in if z <= -1}
for (x, z) in LOFT:
    if (x, z) != (3, -2):
        b.set(x, 7, z, doak.stripped_log("x") if z == -1 else spruce.planks)
for y in range(2, 7):
    b.set(4, y, -2, doak.log("y"))
for y in range(2, 8):
    b.set(3, y, -2, state("ladder", facing="west"))
for x in range(-3, 4):
    if (x, -1) in LOFT:
        b.set(x, 8, -1, spruce.trapdoor("north", open=True))
for (x, z) in ((-4, -1), (4, -1)):                              # corbels under the loft beam ends
    b.set(x, 6, z, doak.stairs("east" if x > 0 else "west", "top"))

# ------------------------------------------------------------------------------------------------------------
# 8. entrance (south): door in a stripped-dark-oak frame with round shoulders and a transom; a porch on two dark
#    fence posts under its own little brown cap; mossy step; lantern beside the frame
# ------------------------------------------------------------------------------------------------------------
for y in (2, 3, 4):
    b.set(-1, y, 5, doak.stripped_log("y"))
    b.set(1, y, 5, doak.stripped_log("y"))
b.set(-1, 5, 5, doak.stairs("west", "top"))
b.set(1, 5, 5, doak.stairs("east", "top"))
b.set(0, 5, 5, doak.stripped_log("x"))
b.door(0, 2, 5, "warped", "north", hinge="left")     # teal accent door (P5)
b.set(0, 4, 5, pane())
for x in (-1, 0, 1):
    b.set(x, 0, 6, "cobbled_deepslate")
    b.set(x, 1, 6, doak.planks if x == 0 else "mossy_stone_bricks")
for x in (-1, 1):
    b.set(x, 0, 7, "cobbled_deepslate")
    b.set(x, 1, 7, "mossy_cobblestone")
    for y in (2, 3, 4):
        b.set(x, y, 7, doak.fence)
b.set(0, 1, 7, stairs("mossy_cobblestone", "north"))
b.set(0, 0, 7, "dirt")
PORCH = {(x, z) for x in range(-2, 3) for z in (6, 7)} | {(-1, 8), (0, 8), (1, 8)}
PCAP, PTOP = set(), {}
for (x, z) in PORCH:
    PCAP.add((x, 5, z))
    PTOP[(x, z)] = 5
for (x, z) in ((-1, 6), (0, 6), (1, 6)):                          # a low crown against the wall only
    PCAP.add((x, 6, z))
    PTOP[(x, z)] = 6
for (x, y, z) in PCAP:
    b.set(x, y, z, cap_state(x, y, z, PCAP, lambda a, c: PTOP.get((a, c)), "brown_mushroom_block"))
b.set(-2, 4, 6, lantern(hanging=True))
b.entrance(0, 1, 9)

# ------------------------------------------------------------------------------------------------------------
# 9. windows
# ------------------------------------------------------------------------------------------------------------
def tdoor(kind, f, half="bottom", open_=True):
    return wood(kind).trapdoor(f, half, open=open_)


# loft south: round (plus) window over the porch, dark stair shoulders in the wall plane, dark backers inside
for (x, y) in ((0, 8), (0, 9), (0, 10), (-1, 9), (1, 9)):
    b.set(x, y, 4, pane())
b.set(-1, 8, 4, doak.stairs("west"))
b.set(1, 8, 4, doak.stairs("east"))
b.set(-1, 10, 4, doak.stairs("west", "top"))
b.set(1, 10, 4, doak.stairs("east", "top"))
for (x, y) in ((-1, 8), (1, 8), (-1, 10), (1, 10)):
    b.set(x, y, 3, doak.planks)

# ground SW diagonal: 1x2 window, sill and a pot
b.set(-3, 3, 4, pane())
b.set(-3, 4, 4, pane())
b.set(-3, 2, 5, doak.trapdoor("south", "top"))
b.set(-3, 3, 5, potted("blue_orchid"))
b.set(-2, 3, 5, tdoor("warped", "south"))          # one teal shutter (the other side is the porch)
b.set(-2, 4, 5, tdoor("warped", "south", "top"))

# ground SE diagonal: a single porthole with a sill
b.set(3, 4, 4, pane())
b.set(3, 3, 5, doak.trapdoor("south", "top"))

# west bay window (3 wide, 1 deep) on dark posts, pent roof, flower box on brackets
for z in (-1, 0, 1):
    for y in (2, 3, 4, 5):
        b.remove(-5, y, z)
    b.set(-5, 1, z, spruce.planks)
    b.set(-6, 0, z, plinth_stone(-6, 0, z))
    b.set(-6, 1, z, plinth_stone(-6, 1, z))
    b.set(-6, 2, z, doak.stripped_log("z"))
    b.set(-6, 3, z, pane())
    b.set(-6, 4, z, pane())
    b.set(-6, 5, z, doak.stripped_log("z"))
for z in (-2, 2):
    b.set(-6, 0, z, plinth_stone(-6, 0, z))
    b.set(-6, 1, z, plinth_stone(-6, 1, z))
    for y in (2, 3, 4, 5):
        b.set(-6, y, z, doak.log("y"))
for z in (-2, -1, 0, 1, 2):
    b.set(-6, 6, z, doak.stairs("east"))
    b.set(-7, 6, z, doak.slab("bottom"))
for z in (-1, 0, 1):
    b.set(-7, 2, z, "rooted_dirt" if z else "moss_block")
    b.set(-8, 2, z, tdoor("spruce", "west"))
    b.set(-7, 3, z, "lily_of_the_valley" if z else "blue_orchid")
b.set(-7, 2, -2, tdoor("spruce", "north"))
b.set(-7, 2, 2, tdoor("spruce", "south"))
b.set(-7, 1, -1, doak.stairs("east", "top"))
b.set(-7, 1, 1, doak.stairs("east", "top"))

# ground north: shuttered 1x2 east of the hearth (one shutter, west side is the chimney)
b.set(2, 3, -5, pane())
b.set(2, 4, -5, pane())
b.set(2, 2, -6, doak.trapdoor("north", "top"))
b.set(1, 3, -6, tdoor("spruce", "north"))
b.set(1, 4, -6, tdoor("spruce", "north", "top"))
# ground east: 1x2 north of the passage with a sill pot
b.set(5, 3, -1, pane())
b.set(5, 4, -1, pane())
b.set(6, 2, -1, doak.trapdoor("east", "top"))
b.set(6, 3, -1, potted("lily_of_the_valley"))
# ground west-north-west small window
b.set(-4, 4, -3, pane())

# loft windows on the ring-4 storey: low wide north eyebrow, east and west singles
b.set(0, 9, -4, pane())
b.set(1, 9, -4, pane())
b.set(4, 9, 0, pane())
b.set(-4, 9, -1, pane())
b.set(-4, 8, 2, pane())

# pantry: east 1x2 with shutters and a flower box, south porthole
for y in (3, 4):
    b.set(11, y, 1, pane())
    b.set(12, y, 0, tdoor("spruce", "east", "bottom" if y == 3 else "top"))
    b.set(12, y, 2, tdoor("spruce", "east", "bottom" if y == 3 else "top"))
b.set(12, 2, 1, "rooted_dirt")
b.set(12, 3, 1, "lily_of_the_valley")
b.set(13, 2, 1, tdoor("spruce", "east"))
b.set(12, 2, 0, tdoor("spruce", "north"))
b.set(12, 2, 2, tdoor("spruce", "south"))
b.set(12, 1, 1, doak.stairs("west", "top"))
b.set(9, 3, 3, pane())
b.set(9, 2, 4, doak.trapdoor("south", "top"))

# ------------------------------------------------------------------------------------------------------------
# 10. stem details: bracket fungi, glow berries and spore blossoms under the cap, a little north-side ivy
# ------------------------------------------------------------------------------------------------------------
for (x, y, z, f) in ((4, 5, 4, "south"), (4, 6, 4, "south"), (3, 6, 5, "south"), (6, 5, -2, "east"),
                     (6, 4, -2, "east"), (3, 9, 4, "south"), (-4, 5, 4, "south")):
    if (x, y, z) not in b:
        b.set(x, y, z, state("shelf_mushroom", facing=f))
HUNG = []
for (x, z, n) in ((-7, 2, 2), (6, -3, 3), (-4, -6, 1), (5, -5, 2), (-6, -4, 1), (7, 2, 2)):
    yb = cap_under(x, z)
    if (x, z) not in CAP_COLS or (x, yb, z) not in b or (x, yb - 1, z) in b:
        print("skip vine", x, z)
        continue
    for i in range(n):
        b.set(x, yb - 1 - i, z, state("cave_vines_plant" if i < n - 1 else "cave_vines", berries=True))
    HUNG.append((x, z))
for (x, z) in ((5, 3), (-4, 6), (2, -6)):
    yb = cap_under(x, z)
    if (x, yb, z) in b and (x, yb - 1, z) not in b:
        b.set(x, yb - 1, z, "spore_blossom")
for (x, z, ys) in ((3, -5, (4, 5, 6)), (-3, -5, (3, 4))):     # ivy on the shady north face
    for y in ys:
        if (x, y, z) not in b:
            b.set(x, y, z, vine())

# ------------------------------------------------------------------------------------------------------------
# 11. interior, ground storey (stand y2)
# ------------------------------------------------------------------------------------------------------------
b.set(-2, 2, -3, state("green_wool_stairs", facing="south"))    # armchair facing the fire
b.set(-3, 2, -3, spruce.trapdoor("west", open=True))
b.set(-3, 2, -2, barrel("up"))
b.set(-3, 3, -2, candle("white", 2))
b.set(1, 2, -4, "bookshelf")
b.set(2, 2, -4, state("chiseled_bookshelf", facing="south", slot_0_occupied=True, slot_1_occupied=True,
                       slot_4_occupied=True))
b.set(2, 3, -4, potted("brown_mushroom"))
b.set(1, 3, -4, lantern())
b.set(3, 2, -3, chest("west"))
b.set(-4, 2, -2, chest("east"))

# toadstool table in the middle: stem block with a red cloth, two stools, a lantern
b.set(0, 2, 1, "mushroom_stem")
b.set(0, 3, 1, carpet("red"))
b.set(-1, 2, 1, spruce.stairs("west"))
b.set(1, 2, 1, spruce.stairs("east"))
for x in range(-2, 3):                                          # oval rug: white heart, green border
    for z in range(-1, 4):
        q = (x / 2.6) ** 2 + ((z - 1) / 2.3) ** 2
        if q <= 1.0 and (x, 2, z) not in b:
            b.set(x, 2, z, carpet("white" if q < 0.35 else "green"))
b.set(0, 2, -3, state("green_wool_stairs", facing="south"))     # second armchair
b.set(-1, 6, -2, "spore_blossom")                               # under the loft floor, over the fireside
b.set(4, 4, 0, spruce.shelf("west"))
b.set(4, 4, -1, spruce.shelf("west"))
b.set(4, 5, 0, potted("brown_mushroom"))
b.set(-4, 4, 2, spruce.shelf("east"))
b.set(-4, 5, 2, potted("blue_orchid"))
b.set(3, 3, 3, state("brewing_stand"))

# south arc: crafting corner, barrels, plants; east storage by the passage
b.set(-3, 2, 3, barrel("up"))
b.set(-3, 3, 3, potted("lily_of_the_valley"))
b.set(-4, 2, 2, "crafting_table")
b.set(3, 2, 3, barrel("north"))
b.set(4, 2, 2, state("composter"))
b.set(2, 2, 4, potted("fern"))
b.set(-2, 2, 4, potted("blue_orchid"))
b.set(4, 2, -1, barrel("west"))
b.set(4, 3, -1, lantern())

# bay window seat (green cushions) and a lantern on the sill corner
for z in (-1, 0, 1):
    b.set(-5, 2, z, state("green_wool_slab", type="bottom"))
b.set(-4, 2, -1, spruce.trapdoor("north", open=True))

# chandelier from the dome over the tall south half
_y = 3
while (0, _y + 1, 2) not in b:
    _y += 1
for y in range(9, _y + 1):
    b.set(0, y, 2, chain())
b.set(0, 8, 2, lantern(hanging=True))
b.set(-4, 6, 1, lantern(hanging=True)) if (-4, 7, 1) in b else None

# ------------------------------------------------------------------------------------------------------------
# 12. loft (stand y8): bed under the dome, nightstand, chest, bookshelf, rug
# ------------------------------------------------------------------------------------------------------------
b.bed(-2, 8, -2, "red", "north")
b.set(-1, 8, -3, barrel("south"))
b.set(-1, 9, -3, lantern())
b.set(-3, 8, -1, state("chiseled_bookshelf", facing="east", slot_0_occupied=True, slot_2_occupied=True,
                       slot_3_occupied=True))
b.set(1, 8, -3, chest("south"))
b.set(2, 8, -3, "bookshelf")                                    # reading nook: shelf, chair, lantern
b.set(2, 9, -3, potted("lily_of_the_valley"))
b.set(0, 8, -3, state("green_wool_stairs", facing="north"))
b.set(-3, 8, -2, potted("fern"))
for x in (0, 1):
    b.set(x, 8, -2, carpet("red" if x else "white"))
b.set(-1, 8, -2, carpet("white"))                               # rug beside the bed

# ------------------------------------------------------------------------------------------------------------
# 13. pantry (stand y2)
# ------------------------------------------------------------------------------------------------------------
b.set(8, 2, 0, barrel("south"))
b.set(9, 2, 0, state("smoker", facing="south"))
b.set(10, 2, 0, state("water_cauldron", level=3))
b.set(10, 2, 1, "crafting_table")
b.set(10, 2, 2, barrel("west"))
b.set(9, 2, 2, chest("north"))
b.set(10, 4, 0, spruce.shelf("south"))
b.set(8, 4, 0, spruce.shelf("south"))
b.set(9, 3, 2, potted("brown_mushroom"))
b.set(9, 5, 1, lantern(hanging=True))
b.set(8, 3, 0, candle("orange", 2))


# ------------------------------------------------------------------------------------------------------------
# 14. landscaping: a woodland floor that is densest in the shade under the cap and fades into the meadow
# ------------------------------------------------------------------------------------------------------------
SITE_X, SITE_Z = (-12, 15), (-11, 13)
OCC0 = {(x, z) for (x, y, z) in b.blocks if y in (0, 1)}


def free(x, z):
    return (SITE_X[0] <= x <= SITE_X[1] and SITE_Z[0] <= z <= SITE_Z[1] and (x, z) not in OCC0
            and (x, 0, z) not in b and (x, 1, z) not in b)


def plant(x, z, st, soil="grass_block"):
    if not free(x, z):
        return False
    b.set(x, 0, z, soil)
    if st:
        b.set(x, 1, z, st)
    return True


def tall_plant(x, z, name, soil="grass_block"):
    if not free(x, z) or (x, 2, z) in b:
        return False
    b.set(x, 0, z, soil)
    b.tall(x, 1, z, name)
    return True


# distance (4-neighbour steps) from the house footprint
DIST = {}
frontier = [c for c in OCC0]
for c in frontier:
    DIST[c] = 0
i = 0
while i < len(frontier):
    c = frontier[i]
    i += 1
    for n in n4(*c):
        if n not in DIST and SITE_X[0] - 2 <= n[0] <= SITE_X[1] + 2 and SITE_Z[0] - 2 <= n[1] <= SITE_Z[1] + 2:
            DIST[n] = DIST[c] + 1
            frontier.append(n)

# --- path: worn dirt from the step, curving south-west, stepping stones near the lamp, fading out
PATH_PTS = [(0.5, 8.0), (0.4, 10.4), (-0.5, 12.0), (-1.8, 13.6)]
PATH = {}
for i in range(len(PATH_PTS) - 1):
    (ax, az), (cx, cz) = PATH_PTS[i], PATH_PTS[i + 1]
    for k in range(13):
        t = k / 12
        px, pz = ax + (cx - ax) * t, az + (cz - az) * t
        for dx in (-2, -1, 0, 1, 2):
            for dz in (-1, 0, 1):
                q = (round(px) + dx, round(pz) + dz)
                dd = math.hypot(q[0] - px, q[1] - pz)
                PATH[q] = min(PATH.get(q, 9), dd)
PATH_CORE = set()
for (x, z), dd in sorted(PATH.items()):
    if not free(x, z) or z < 8:
        continue
    wide = 1.0 if z <= 10 else 0.62                             # 2 wide at the porch step, then 1
    if dd <= wide:
        b.set(x, 0, z, "dirt_path" if hash01(x, 0, z, 4) < 0.85 else "coarse_dirt")
        PATH_CORE.add((x, z))
    elif dd <= wide + 0.75 and z >= 9:                          # stepping-stone edge: low slabs on the grass
        r = hash01(x, 0, z, 5)
        if r < 0.42:
            b.set(x, 1, z, slab("mossy_cobblestone" if hash01(x, 1, z, 6) < 0.55 else "tuff"))
        elif r < 0.62:
            b.set(x, 0, z, "coarse_dirt")

# --- trees: a birch pair at the back-west, a spruce behind the pantry (all >= 2 air clear of the caps)
def birch_tree(bx, bz, h, seed, R=2.6):
    for y in range(1, h + 1):
        b.set(bx, y, bz, birch.log("y"))
    b.set(bx + 1, h - 3, bz, birch.log("x"))                    # a short side branch
    for (x, z, s_) in ((bx, bz, "rooted_dirt"), (bx + 1, bz, "moss_block"), (bx, bz + 1, "coarse_dirt")):
        b.set(x, 0, z, s_)
    cy = h - 1
    for x in range(bx - 3, bx + 4):
        for z in range(bz - 3, bz + 4):
            for y in range(cy - 2, h + 3):
                if (x, y, z) in b:
                    continue
                dy = y - cy
                rr = R if dy <= 0 else R - dy * 0.75
                j = 1 + (value3(x * 1.4, y * 1.4, z * 1.4, seed, 1.7) - 0.5) * 0.5
                if math.hypot(x - bx, z - bz) <= rr * j and dy >= -2 - (1 if hash01(x, y, z, seed) < 0.25 else 0):
                    if dy == -2 and math.hypot(x - bx, z - bz) > R - 0.8:
                        continue
                    b.set(x, y, z, leaves("birch") if hash01(x, y, z, seed + 1) < 0.8 else leaves("oak"))
    b.set(bx, h + 1, bz, leaves("birch"))


def spruce_tree(bx, bz, h, seed):
    for y in range(1, h + 1):
        b.set(bx, y, bz, spruce.log("y"))
    b.set(bx, 0, bz, "podzol")
    for y in range(3, h + 2):
        k = h + 1 - y                                          # distance below the tip
        r = [0.6, 1.1, 1.6, 1.2, 2.1, 1.7, 2.6, 2.2, 3.0][min(8, k)]
        for x in range(bx - 3, bx + 4):
            for z in range(bz - 3, bz + 4):
                if (x, y, z) in b:
                    continue
                d = math.hypot(x - bx, z - bz) * (1 + (hash01(x, y, z, seed) - 0.5) * 0.25)
                if d <= r:
                    b.set(x, y, z, leaves("spruce"))
    b.set(bx, h + 2, bz, leaves("spruce"))


birch_tree(-10, -8, 11, 301)
birch_tree(-10, 4, 7, 302, R=1.8)
spruce_tree(13, -7, 10, 303)

# --- toadstool lamp (the third, tiny cap) beside the path: a 3-block stem, a domed red cap, a lantern under it
TL = (-6, 9)
for y in (1, 2, 3):
    b.set(TL[0], y, TL[1], "mushroom_stem")
b.set(TL[0], 0, TL[1], "podzol")
LCAP = {(TL[0] + dx, 4, TL[1] + dz) for dx in (-1, 0, 1) for dz in (-1, 0, 1)} | {(TL[0], 5, TL[1])}
LTOP = {(TL[0] + dx, TL[1] + dz): 4 for dx in (-1, 0, 1) for dz in (-1, 0, 1)}
LTOP[TL] = 5
for (x, y, z) in LCAP:
    b.set(x, y, z, cap_state(x, y, z, LCAP, lambda a, c: LTOP.get((a, c)), "red_mushroom_block"))
b.set(TL[0] + 1, 3, TL[1], lantern(hanging=True))
# a second, much smaller toadstool a little way off (stem 1, cap 1), vanilla mushrooms around both
for (x, z, m) in ((-7, 11, "red_mushroom"), (-5, 11, "brown_mushroom"), (-4, 9, "brown_mushroom"),
                  (-9, 9, "red_mushroom"), (-8, 6, "brown_mushroom"), (-10, 8, "red_mushroom")):
    if free(x, z):
        b.set(x, 0, z, "podzol")
        b.set(x, 1, z, m)

# --- fallen hollow log bench (SE of the porch, facing the path), mossy top, bracket fungi, ferns
for x in range(3, 8):
    b.set(x, 1, 10, oak.log("x"))
    b.set(x, 0, 10, "podzol" if x % 2 else "coarse_dirt")
for x in (4, 5, 7):
    b.set(x, 2, 10, "moss_carpet")
b.set(8, 1, 10, oak.trapdoor("east", open=True))                # the hollow end
b.set(5, 1, 11, state("shelf_mushroom", facing="south"))
b.set(6, 1, 9, state("shelf_mushroom", facing="north"))

# --- stump with shelf mushrooms (NE, by the spruce)
for y in (1, 2):
    b.set(10, y, -6, oak.log("y"))
b.set(10, 3, -6, "moss_carpet")
b.set(10, 0, -6, "rooted_dirt")
b.set(11, 1, -6, state("shelf_mushroom", facing="east"))
b.set(10, 2, -5, state("shelf_mushroom", facing="south"))
b.set(9, 1, -6, state("shelf_mushroom", facing="west"))

# --- woodpile under the cap's NW edge (fuel for the hearth)
for (x, y, z) in ((-5, 1, -6), (-4, 1, -6), (-5, 2, -6), (-6, 1, -5)):
    if (x, y, z) not in b and (x, 0, z) not in b:
        b.set(x, y, z, spruce.log("z" if z == -6 else "x"))

# --- bushes (irregular azalea / oak-leaf blobs with a mossy skirt), mossy boulders, leaf litter under the birches
def bush(cx, cz, r, h, seed):
    ox = 1 if hash01(cx, 0, cz, seed) < 0.5 else -1
    for x in range(cx - 3, cx + 4):
        for z in range(cz - 3, cz + 4):
            d = math.hypot(x - cx, z - cz) + (value2(x, z, seed, 1.3) - 0.5) * 1.2
            if d > r or not free(x, z):
                continue
            ex, ez = abs(x - cx), abs(z - cz)
            if ex >= 1 and ez >= 1 and math.hypot(ex, ez) > r - 0.35:
                continue                                        # cut the corners: never a box
            b.set(x, 0, z, "moss_block")
            roll = hash01(x, 1, z, seed + 1)
            b.set(x, 1, z, leaves("flowering_azalea" if roll < 0.18 else ("azalea" if roll < 0.6 else "oak")))
            if h >= 2 and math.hypot(x - cx - ox * 0.6, z - cz) <= r - 0.9:
                b.set(x, 2, z, leaves("azalea" if hash01(x, 2, z, seed + 2) < 0.6 else "oak"))
    for (dx, dz) in ((2, 1), (-1, 2), (-2, -1), (1, -2)):
        x, z = cx + dx + ox, cz + dz
        if hash01(x, 0, z, seed + 3) < 0.6:
            plant(x, z, "fern", "podzol")


def boulder(x, z, n, seed):
    cells = [(x, z), (x + 1, z), (x, z + 1)][:n]
    for i, (cx, cz) in enumerate(cells):
        if free(cx, cz):
            b.set(cx, 0, cz, "cobblestone")
            b.set(cx, 1, cz, "mossy_cobblestone" if i != 1 else stairs("mossy_cobblestone", "west"))
            if i == 0:
                b.set(cx, 2, cz, "moss_carpet")


bush(-9, -4, 1.7, 2, 501)
bush(10, 7, 1.5, 1, 502)
bush(14, 3, 1.4, 2, 503)
bush(0, -10, 1.9, 2, 504)
bush(-11, 10, 1.4, 1, 505)
bush(4, 13, 1.3, 1, 506)
bush(-8, 12, 1.2, 1, 507)
boulder(-12, -1, 2, 1)
boulder(12, 10, 3, 2)
boulder(5, -9, 1, 3)
boulder(2, 12, 1, 4)
for (tx, tz, rad) in ((-10, -8, 3.4), (-10, 4, 2.4), (13, -7, 2.6)):
    for x in range(tx - 4, tx + 5):
        for z in range(tz - 4, tz + 5):
            dd = math.hypot(x - tx, z - tz)
            if 0.9 < dd <= rad and hash01(x, 3, z, 77) < 0.45 and free(x, z):
                b.set(x, 1, z, state("leaf_litter", segment_amount=1 + hash3(x, 0, z, 79) % 4,
                                     facing=CW[hash3(x, 1, z, 80) % 4]))

# --- ground cover (round 2): the woodland floor lives in a few merged bean-shaped drifts -- the cap's shade and
#     the ground under the birch pair and the spruce -- with soft fringes of moss carpet, leaf litter and ferns;
#     outside them a meadow of lily of the valley / blue orchid drifts fading out.  No lone podzol squares.
BEANS = [((-8.3, -6.8), 4.4, 2.7, 35), ((-10.0, 2.8), 2.3, 3.1, 10), ((12.8, -5.6), 3.2, 2.3, -20)]


def wood_q(x, z):
    q = cap_r(x, z) / 7.8
    for (cx, cz), rx, rz, ang in BEANS:
        a = math.radians(ang)
        u = (x - cx) * math.cos(a) + (z - cz) * math.sin(a)
        v = -(x - cx) * math.sin(a) + (z - cz) * math.cos(a)
        q = min(q, math.hypot(u / rx, v / rz))
    return q + (value2(x, z, 405, 2.6) - 0.5) * 0.3


for x in range(SITE_X[0], SITE_X[1] + 1):
    for z in range(SITE_Z[0], SITE_Z[1] + 1):
        if not free(x, z) or (x, z) in PATH:
            continue
        d = DIST.get((x, z), 9)
        q = wood_q(x, z)
        r = hash01(x, 0, z, 402)
        drift = value2(x, z, 403, 2.3)
        if q <= 1.0:
            v = value2(x, z, 404, 2.4)
            soil = "podzol" if v < 0.6 else ("moss_block" if v < 0.85 else "coarse_dirt")
            if r < 0.15:
                st, soil = ("red_mushroom" if drift < 0.5 else "brown_mushroom"), "podzol"
            elif r < 0.45:
                st = "fern"
            elif r < 0.58 and soil == "moss_block":
                st = "moss_carpet"
            elif r < 0.64 and (x, z) not in CAP_COLS:
                st = "lily_of_the_valley"
            else:
                st = None
            if st is None and r > 0.93 and tall_plant(x, z, "large_fern", "podzol"):
                continue
            plant(x, z, st, soil)
        elif q <= 1.4:                                          # fringe on the grass
            if r < 0.07:
                plant(x, z, "moss_carpet")
            elif r < 0.36:
                plant(x, z, state("leaf_litter", segment_amount=1 + hash3(x, 0, z, 79) % 3,
                                  facing=CW[hash3(x, 1, z, 80) % 4]))
            elif r < 0.55:
                plant(x, z, "fern")
        elif d <= 6:
            fade = 1.0 - d / 7.5
            if r < 0.75 * fade:
                if drift < 0.42:
                    st = "lily_of_the_valley"
                elif drift > 0.66:
                    st = "blue_orchid"
                else:
                    st = "short_grass" if r < 0.35 else "fern"
                plant(x, z, st)
            elif r < 0.82 * fade:
                plant(x, z, "bush")
        elif r < 0.06:
            plant(x, z, "short_grass")

# firefly bushes by the log and the stump (glow at night)
plant(8, 11, "firefly_bush")
plant(12, -4, "firefly_bush")


# ------------------------------------------------------------------------------------------------------------
# 15. round-2 passes (critique docs/critiques/04_round1.md)
# ------------------------------------------------------------------------------------------------------------
SIDES5 = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0), "up": (0, 1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


def bid(st):
    return st.split("[")[0].replace("minecraft:", "")


def repaint(changed, block):
    """full mushroom blocks next to a new wool stair/slab show their skin on that side, not the pale pores."""
    for (x, y, z) in list(b.blocks):
        st = b.blocks[(x, y, z)]
        if bid(st) != block:
            continue
        on = [d for d, (dx, dy, dz) in SIDES5.items() if (x + dx, y + dy, z + dz) in changed]
        if on:
            b.set(x, y, z, with_props(st, **{d: True for d in on}))


def column_tops(block, ylo, yhi, keep=lambda x, z: True):
    T, Bt = {}, {}
    for (x, y, z), st in b.blocks.items():
        if bid(st) == block and ylo <= y <= yhi and keep(x, z):
            T[(x, z)] = max(y, T.get((x, z), -99))
            Bt[(x, z)] = min(y, Bt.get((x, z), 99))
    return T, Bt


def pick_facing(x, z, T, t, c):
    lower = {d: T.get((x + dx, z + dz), -99) for d, (dx, dz) in DIRS.items()}
    low = [d for d, v in lower.items() if v < t]
    high = [d for d, v in lower.items() if v >= t]
    cand = [d for d in high if OPP[d] in low] or high
    cand.sort(key=lambda d: -(DIRS[d][0] * (c[0] - x) + DIRS[d][1] * (c[1] - z)))
    return low, high, (cand[0] if cand else None), lower


# B1 + B2: chamfer every edge top cell of the red cap with red wool stairs (45-degree dome instead of a
# ziggurat), isolated peaks become slabs; a wart on a nose becomes a flush white wool stair; carpets stay on flats
T, _ = column_tops("red_mushroom_block", 9, 30, lambda x, z: abs(x) <= 8 and abs(z) <= 8)
CHANGED = set()
for (x, z), t in sorted(T.items()):
    above = b.get(x, t + 1, z)
    wart = bid(above) == "white_carpet"
    litter = bid(above) == "leaf_litter"
    if above != AIR and not wart and not litter:
        continue                                                # chimney: keep the full block
    low, high, f, _l = pick_facing(x, z, T, t, MAIN_C)
    if not low:
        continue
    if litter:
        b.remove(x, t + 1, z)                                   # leaf litter stays on the flats only
    if not high:
        b.set(x, t, z, slab("red_wool"))
    elif wart:
        b.remove(x, t + 1, z)
        b.set(x, t, z, stairs("white_wool", f))
    else:
        b.set(x, t, z, stairs("red_wool", f))
    CHANGED.add((x, t, z))
repaint(CHANGED, "red_mushroom_block")

# B3: round the brown pantry and porch caps with brown wool stairs and a curled top-stair lip under the rim;
# the porch crown leans on the wall (facing north) so it is one clean row, not a battlement
BT, BB = column_tops("brown_mushroom_block", 3, 8)
PORCH_TOP = max(v for (x, z), v in BT.items() if x < 4)
BCH, LIPS = set(), []
for (x, z), t in sorted(BT.items()):
    if (x, t + 1, z) in b:
        continue
    c = PAN_C if x >= 4 else (0, 5)
    low, high, f, lower = pick_facing(x, z, BT, t, c)
    if not low:
        continue
    if x < 4 and t == PORCH_TOP:
        f = "north"
    elif not high:
        continue
    b.set(x, t, z, stairs("brown_wool", f))
    BCH.add((x, t, z))
    outer = [d for d in low if lower[d] == -99]
    if outer:
        y = BB[(x, z)] - 1
        dx, dz = DIRS[OPP[outer[0]]]
        if (x, y, z) not in b and (x, y - 1, z) not in b and (x + dx, y, z + dz) not in b:
            LIPS.append(((x, y, z), f))
for (p, f) in LIPS:
    b.set(*p, stairs("brown_wool", f, "top"))
    BCH.add(p)
repaint(BCH, "brown_mushroom_block")

# lamp toadstool: corners become red wool stairs toward the stem, the top cube a slab -> a little dome
LCH = set()
for dx in (-1, 1):
    for dz in (-1, 1):
        p = (TL[0] + dx, 4, TL[1] + dz)
        b.set(*p, stairs("red_wool", "east" if dx < 0 else "west"))
        LCH.add(p)
b.set(TL[0], 5, TL[1], slab("red_wool"))
LCH.add((TL[0], 5, TL[1]))
repaint(LCH, "red_mushroom_block")

# stem pilasters ("fibre ribs") on the ground storey: a 1-wide mushroom-stem rib at L+1 in every 3rd-4th blank bay,
# on a stone foot, capped by a pale-oak bracket under the shoulder
RING6 = sorted({(x, z) for x in range(-7, 8) for z in range(-7, 8) if KM(x, z) == 6},
               key=lambda c: math.atan2(c[1], c[0]))
PILASTERS, last = [], -9
for i, (x, z) in enumerate(RING6 + RING6[:4]):
    f = facing_in(x, z)
    w = (x + DIRS[f][0], z + DIRS[f][1])
    if w not in low_wall or abs(x) <= 2 and z >= 5 or (x, z) in STACK or x >= 6:
        continue
    blank = all(bid(b.get(w[0], y, w[1])) == "mushroom_stem" for y in range(3, 7))
    free_col = all((x, y, z) not in b for y in range(2, 8))
    neighbours_ok = all(not bid(b.get(x + ddx, y, z + ddz)).endswith("trapdoor") for (ddx, ddz) in DIRS.values()
                        for y in range(2, 6))
    if blank and free_col and neighbours_ok and i - last >= 3 and (x, z) not in [p for p in PILASTERS]:
        if bid(b.get(x, 1, z)).endswith("stairs") or (x, 1, z) not in b:
            b.set(x, 0, z, plinth_stone(x, 0, z))
            b.set(x, 1, z, plinth_stone(x, 1, z))
        for y in range(2, 7):
            b.set(x, y, z, "mushroom_stem")
        b.set(x, 7, z, stairs("pale_oak", f, "top"))
        PILASTERS.append((x, z))
        last = i
print("pilasters:", PILASTERS)

# pantry herb rack: drying bundles on chains from the cap ceiling
for (x, z, item) in ((8, 2, potted("fern")), (10, 2, "hay_block"), (8, 1, potted("azalea_bush"))):
    if (x, 5, z) not in b and (x, 4, z) not in b:
        b.set(x, 5, z, chain())
        b.set(x, 4, z, item)


b.note("Concept 'Toadstool Hollow': round mushroom-stem cottage under a giant red cap (15 across), tapering stem "
       "with an annulus shoulder, brown-cap pantry and porch canopy, tuff chimney through the cap, woodland garden.")
b.note("H12 odd spans: n/a (round plan). Paste with Litematica replace = 'with non-air' so paths and podzol "
       "replace the terrain.")

b.room("main", 0, 2, 0)
b.room("pantry", 9, 2, 1)
b.room("loft", 0, 8, -2)


# ------------------------------------------------------------------------------------------------------------
# dev helpers
# ------------------------------------------------------------------------------------------------------------
def look(specs, out_dir="out/previews/04_mushroom_cottage/look"):
    """close-ups in AUTHORED coordinates. spec 'x,y,z,radius,azimuth,elevation[,cut]'."""
    from blockwright.render import render_views
    blocks, size, meta, _ = b.structure()
    ox, oy, oz = meta["origin_offset"]
    views = []
    for i, sp in enumerate(specs):
        v = [float(t) for t in sp.split(",")]
        d = {"name": f"look{i}", "target": (int(v[0]) - ox, int(v[1]) - oy, int(v[2]) - oz), "radius": v[3],
             "azimuth": v[4], "elevation": v[5]}
        if len(v) > 6:
            d["cut"] = int(v[6]) - oy
        views.append(d)
    print("origin offset (authored = schematic + offset):", (ox, oy, oz))
    for p in render_views(blocks, size, out_dir, meta=meta, views=views):
        print(p)


def shares():
    """share of the first visible block per elevation cell (plants ignored)."""
    groups = {"stem": ("mushroom_stem", "pale_oak_stairs"),
              "red cap": ("red_mushroom_block",), "brown cap": ("brown_mushroom_block",),
              "stone": ("tuff", "mossy_cobblestone", "cobbled_deepslate", "mossy_stone_bricks", "tuff_bricks",
                        "polished_tuff"),
              "dark wood": ("dark_oak_log", "stripped_dark_oak_log", "dark_oak_stairs", "dark_oak_slab",
                            "dark_oak_planks", "dark_oak_trapdoor", "dark_oak_fence")}
    skip = ("grass", "fern", "flower", "leaves", "vine", "bush", "orchid", "lily", "carpet", "lantern", "chain",
            "mushroom[", "podzol", "dirt", "log[axis=x", "red_mushroom", "brown_mushroom", "path", "moss_block")
    house = {(x, y, z): s for (x, y, z), s in b.blocks.items() if -8 <= x <= 14 and -8 <= z <= 8 and y > G}
    for name, (axis, sign) in {"S": ("z", 1), "N": ("z", -1), "E": ("x", 1), "W": ("x", -1)}.items():
        first = {}
        for (x, y, z), s in house.items():
            bid = s.split("[")[0].replace("minecraft:", "")
            if bid in ("red_mushroom", "brown_mushroom") or any(k in bid for k in skip[:12]):
                continue
            key, depth = ((x, y), z) if axis == "z" else ((z, y), x)
            if key not in first or depth * sign > first[key][0] * sign:
                first[key] = (depth, bid)
        tot = len(first)
        cnt = {g: sum(1 for d, bid in first.values() if bid in ids) for g, ids in groups.items()}
        print(name, tot, {g: f"{100 * c / tot:.0f}%" for g, c in cnt.items()})


if __name__ == "__main__":
    if "--look" in sys.argv:
        look(sys.argv[sys.argv.index("--look") + 1:])
    elif "--shares" in sys.argv:
        shares()
    else:
        b.finish()
