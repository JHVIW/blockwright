"""b01 -- Cozy Starter Cottage with garden ("Catslide Cottage", palette P1 Thistledown).

A one-and-a-half storey timber-framed cottage: 11 x 7 main volume with a steep bell-cast dark-oak roof whose north
slope sweeps down (catslide) over a stone pantry lean-to, a fat exterior chimney on the west gable, a woodpile
lean-to on the east gable, an off-centre cross-gabled entrance porch, a bay window + gable dormer over a vaulted
living room, and a partial sleeping loft over the kitchen.

Top view (g = 0, x east, z south)            South elevation (schematic)
  x: -1 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14          R  ridge g+12/13, chimney rim g+14
  z0            [== catslide lip g+3 ==]        dormer ^ (ridge g+10)
  z1              = = = = = = =  lean-to        main eave lip g+6 ===========
  z3              =   a a     =  pantry          bay [GGG] + hood   porch ^ (ridge g+7)  [G]
  z4          # # # # # # # # # # #              plinth g+1, foundation g, g-1
  z5          #                   #  K
  z6  C C C C H                   #  K F         C chimney, H hearth, S stair, W woodpile
  z7  C C C C H     vault  | loft S #  W W
  z8  C C C C H                   S #  W W
  z9          w                   S #  W W
  z10         # . . . # . . D . . #  o
  z11         b b b b b . P P P
  z12                     p . p
  z13                       s

Run:  python -m blockwright build examples/builds/b01_cozy_starter_cottage.py [--quick] [--no-render] [--views=a,b]
"""
import sys

from blockwright import *

G = 0                                   # natural terrain surface
b = Build("01_cozy_starter_cottage", "Cozy Starter Cottage", ground=G,
          description="Catslide cottage with bay window, dormer, porch, exterior chimney and a vegetable garden.")

DO, SP, OAK, PO, BI = wood("dark_oak"), wood("spruce"), wood("oak"), wood("pale_oak"), wood("birch")
COB, SBR, MCOB, BRK = stone("cobblestone"), stone("stone_bricks"), stone("mossy_cobblestone"), stone("brick")

# ---- key dimensions -------------------------------------------------------------------------------------------
X0, X1 = 3, 13          # main walls (gable ends) x
Z0, Z1 = 4, 10          # main walls (eave sides) z ; span 7, ridge on z7
RZ = 7
PLATE = G + 7           # wall plate / top course (eaves raised one course in round 2)
LOFT = G + 5            # loft floor blocks (over x8..x12 only)
LOFT_X = (8, 12)
LEAN_X = (5, 11)        # pantry lean-to walls x, z1..z3
DOOR_X = 9


# ================================================================================================================
# materials (smooth noise, never white noise)
# ================================================================================================================
def field_family(along, course, p=0.0, moss=False, seed=11):
    """roof FIELD = tuff stone slate (never the frame wood). Weathering, not speckle: sun-bleached polished-tuff runs
    3-5 long ALONG one course (lattice 4 along, 1 across) with probability p (upper courses only); moss=True marks a
    deliberate mossy cluster cell on the shady north eaves."""
    if moss:
        return "mossy_stone_brick"
    if p > 0 and value2(along / 4.0, course * 7.31 + 0.5, seed, scale=1.0) > 1.0 - p * 1.15:
        return "polished_tuff"
    return "tuff_brick"


def field_stairs(fam, facing, half="bottom"):
    return state(fam + "_stairs", facing=facing, half=half)


def field_slab(kind="bottom"):
    return state("tuff_brick_slab", type=kind)


def stone_mix(x, y, z, seed=3):
    """plinth stone: cobble 45 / stone bricks 25 / mossy 20 / andesite 10, mossy toward the bottom."""
    moss = value3(x, y, z, seed=seed, scale=2.5) + (G + 1 - y) * 0.22
    if moss > 0.78:
        return "mossy_cobblestone"
    n = value3(x, y, z, seed=seed + 1, scale=2.0)
    if n > 0.70:
        return "stone_bricks"
    if n < 0.18:
        return "andesite"
    if chance(0.06, x, y, z, seed + 2):
        return "cracked_stone_bricks"
    return "cobblestone"


def rubble(x, y, z):
    """older stone of the pantry lean-to: smaller patches, more moss and andesite than the plinth."""
    n = value3(x, y, z, seed=45, scale=1.4)
    m = value3(x, y, z, seed=46, scale=1.8) + (G + 2 - y) * 0.15
    if m > 0.70:
        return "mossy_cobblestone"
    if n > 0.68:
        return "stone_bricks" if n < 0.82 else "mossy_stone_bricks"
    if n < 0.22:
        return "andesite" if n > 0.08 else "tuff"
    return "cobblestone"


def plaster(x, y, z):
    """ONE cream per framed panel: a mushroom-stem base course, a pale-oak field, calcite only high in the gables
    (lighter upward). Never mixed per block -- small panels of three different whites read as mistakes."""
    if y >= G + 9:
        return "calcite"
    if y == G + 2:
        return "mushroom_stem"
    return PO.planks


def chimney_mat(x, y, z):
    """deliberate gradient, no random squares: a rubble base (moss only low on the shady N/W corners), a
    two-course cobble/brick dither at g+5..g+6, clean brick above."""
    if y >= G + 6:
        return "bricks"
    if y == G + 5:                                              # toothing: stone corners run up one course
        return "cobblestone" if (x in (-1, 0, 2) and z in (6, 8)) else "bricks"
    if y <= G + 2 and (x <= -1 or z == 6) and value3(x, y, z, seed=34, scale=1.5) < 0.6:
        return "mossy_cobblestone"
    return "stone_bricks" if (y + x + z) % 5 == 0 and y >= G + 1 else "cobblestone"


# ================================================================================================================
# 1. foundation, plinth, floor
# ================================================================================================================
def main_plan():
    return {(x, z) for x in range(X0, X1 + 1) for z in range(Z0, Z1 + 1)}


def lean_plan():
    return {(x, z) for x in range(LEAN_X[0], LEAN_X[1] + 1) for z in range(1, Z0)}


def foundations():
    for (x, z) in main_plan() | lean_plan():
        edge = x in (X0, X1) or z in (Z0, Z1) or x in LEAN_X or z == 1
        if (x, z) in lean_plan() and not (x in LEAN_X or z == 1):
            edge = False
        if not edge:
            continue
        for y in (G - 1, G, G + 1):
            b.set(x, y, z, stone_mix(x, y, z))
    # interior floor
    for x in range(X0 + 1, X1):
        for z in range(Z0 + 1, Z1):
            b.set(x, G + 1, z, SP.planks)
    for x in range(LEAN_X[0] + 1, LEAN_X[1]):
        for z in range(2, Z0):
            b.set(x, G + 1, z, SP.planks)


# ================================================================================================================
# 2. walls (massing pass: plaster + corner posts + plate)
# ================================================================================================================
def gable_top(z, x=X0):
    """highest wall cell of the gable end at row z (just under the roof); the east end is half-hipped."""
    if x == X1 and z == RZ:
        return G + 10
    return {5: G + 8, 6: G + 9, 7: G + 10, 8: G + 9, 9: G + 8}.get(z, PLATE)


def walls():
    """timber frame: dark oak posts, stripped dark oak plates + a sole plate on the show sides, plaster infill."""
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            if not (x in (X0, X1) or z in (Z0, Z1)):
                continue
            top = gable_top(z, x) if x in (X0, X1) else PLATE
            for y in range(G + 2, top + 1):
                b.set(x, y, z, plaster(x, y, z))
    # posts: corners + wing corners on the south, a mid post on the east gable
    for (x, z) in ((X0, Z0), (X0, Z1), (X1, Z0), (X1, Z1), (7, Z1), (11, Z1), (X1, 7)):
        b.fill(x, G + 2, z, x, PLATE - 1, z, DO.log("y"))
    # plates (top course) and sole plates (bottom course) on the south and east faces
    b.fill(X0, PLATE, Z0, X1, PLATE, Z0, DO.stripped_log("x"))
    b.fill(X0, PLATE, Z1, X1, PLATE, Z1, DO.stripped_log("x"))
    b.fill(X0, PLATE, Z0 + 1, X0, PLATE, Z1 - 1, DO.stripped_log("z"))
    b.fill(X1, PLATE, Z0 + 1, X1, PLATE, Z1 - 1, DO.stripped_log("z"))
    # chimney breast: the west wall behind the stack is brick (it is the hearth wall inside)
    for z in (6, 7, 8):
        for y in range(G + 2, gable_top(z) + 1):
            b.set(X0, y, z, "bricks")


def lean_to_walls():
    """pantry lean-to under the catslide: stone plinth, three cream courses, a dark wall plate (z1 g+5) under the
    flared catslide foot; side walls follow the roof."""
    tops = {1: G + 5, 2: G + 5, 3: G + 6}
    for x in range(LEAN_X[0], LEAN_X[1] + 1):
        for z in (1, 2, 3):
            if not (x in LEAN_X or z == 1):
                continue
            for y in range(G + 2, tops[z] + 1):
                if z == 1 and y == G + 5:
                    b.set(x, y, z, DO.stripped_log("x"))
                elif (x, z) in ((LEAN_X[0], 1), (LEAN_X[1], 1)):
                    b.set(x, y, z, "stone_bricks" if y == G + 2 else rubble(x, y, z))
                else:
                    b.set(x, y, z, plaster(x, y, z) if y > G + 2 or z == 1 else rubble(x, y, z))


# ================================================================================================================
# 3. roofs (highest first)
# ================================================================================================================
SOUTH = {9: (9, "S"), 10: (8, "S"), 11: (7, "lip")}           # 45-degree south slope below the top course
NORTH = {5: (9, "S"), 4: (8, "S"), 3: (7, "S")}
TOP_Z = {8: "north", 6: "south"}                               # top course (g+10) beside the ridge
RIDGE = G + 11                                                 # ridge core (dark oak planks), cap slab at g+12
VERGE_X = (X0 - 1, X1 + 1)
CAT_X = (LEAN_X[0] - 1, LEAN_X[1] + 1)
# polished-tuff weathering only on the upper half of every slope; moss clusters only on the two lowest north
# field courses, near the chimney (west) and near the orchard tree (east)
P_UPPER = 0.30
MOSS = {(3, G + 7, 3), (4, G + 7, 3), (5, G + 6, 2), (6, G + 6, 2), (5, G + 7, 3),
        (11, G + 6, 2), (10, G + 6, 2), (12, G + 7, 3), (13, G + 7, 3), (11, G + 7, 3)}


def roof_cell(x, y, z, kind, up, role="field", p=0.0, along=None, course=None):
    """one roof cell. role: field (tuff slate) | trim (dark-oak frame of the main roof) | wing_trim (spruce barge
    boards of the front gable). up = compass direction toward the ridge (stairs face it)."""
    along = x if along is None else along
    course = z if course is None else course
    if role == "field":
        fam = field_family(along, course, p, moss=(x, y, z) in MOSS)
        st = field_stairs(fam, up) if kind == "S" else ("tuff_bricks" if kind == "B" else field_slab())
    else:
        w = DO if role == "trim" else SP
        st = w.stairs(up) if kind == "S" else (w.planks if kind == "B" else w.slab("bottom"))
    b.set(x, y, z, st)


def main_roof():
    """45-degree slate roof with a slab kick at the south eave and a flared catslide foot on the north, framed by
    one continuous dark-oak trim: verges, eave lips, ridge cap."""
    for x in range(VERGE_X[0], VERGE_X[1] + 1):
        verge = x in VERGE_X
        trim = "trim" if verge else "field"
        for z, (dy, kind) in SOUTH.items():
            role = "trim" if (verge or kind == "lip") else "field"
            roof_cell(x, G + dy, z, kind, "north", role, p=P_UPPER if z == 9 else 0.0)
        for z, (dy, kind) in NORTH.items():
            roof_cell(x, G + dy, z, kind, "south", trim, p=P_UPPER if z == 5 else 0.0)
        for z, up in TOP_Z.items():
            roof_cell(x, G + 10, z, "S", up, trim, p=P_UPPER)
        if CAT_X[0] <= x <= CAT_X[1]:
            catv = "trim" if x in CAT_X else "field"
            roof_cell(x, G + 6, 2, "S", "south", catv)                      # catslide course
            b.set(x, G + 6, 1, DO.slab("bottom") if x in CAT_X else field_slab("bottom"))   # flare: kick
            b.set(x, G + 5, 0, DO.slab("top") if x in CAT_X else field_slab("top"))
            b.set(x, G + 5, -1, DO.slab("bottom"))                          # lip: dark-oak trim, overhang 2
        # ridge: dark plank core, beam ends with log rings at the verges, one continuous dark-oak cap
        b.set(x, RIDGE, RZ, DO.stripped_log("x") if verge else DO.planks)
        b.set(x, RIDGE + 1, RZ, DO.slab("bottom"))
    # verge (barge board) under-layer: inverted partners + beam ends at the verge feet
    for x in VERGE_X:
        b.set(x, PLATE, Z1, DO.stripped_log("x"))
        b.set(x, PLATE, Z0, DO.stripped_log("x"))
        b.set(x, G + 8, 9, DO.stairs("south", "top"))
        b.set(x, G + 9, 8, DO.stairs("south", "top"))
        b.set(x, RIDGE - 1, RZ, DO.planks)
        b.set(x, G + 9, 6, DO.stairs("north", "top"))
        b.set(x, G + 8, 5, DO.stairs("north", "top"))
    # clip the east gable (half-hip): the ridge stops at x12; x13 carries the hip top, x14 the hip eave course
    for y in (RIDGE, RIDGE + 1):
        b.remove(X1, y, RZ)
        b.remove(X1 + 1, y, RZ)
    b.set(X1, RIDGE, RZ, DO.stairs("west"))
    for z in (6, 7, 8):
        b.set(X1 + 1, G + 10, z, DO.stairs("west"))
    b.set(X1 - 1, RIDGE + 1, RZ, state("waxed_lightning_rod", facing="up"))   # finial on the hip apex
    for x in CAT_X:                                                 # catslide verge partners / brackets
        b.set(x, G + 6, 3, DO.stairs("north", "top"))
        b.set(x, G + 5, 2, DO.stairs("north", "top"))
        b.set(x, G + 4, 1, DO.stairs("north", "top"))


WING_X = (7, 11)        # front cross-gable wing walls x (span 5); porch z11..z13 below, loft above
WING_Z = (11, 13)       # ground storey of the wing (recessed porch, front posts on z13)
JETTY_Z = 14            # the upper gable is jettied one block out over the porch front
WING_H = {6: 7, 7: 8, 8: 9, 9: 10, 10: 9, 11: 8, 12: 7}      # roof stair y per x (45 degrees), ridge x9 at g+10
MAIN_H = {11: 7, 10: 8, 9: 9, 8: 10}                           # roof cell y per z on the south slope


def wing_roof():
    """cross gable over the porch wing (slate field, spruce barge boards); its ridge (g+10) dies into the main
    south slope at z9."""
    zf = JETTY_Z + 1
    for z in range(9, zf + 1):
        front = z == zf
        for x, h in WING_H.items():
            mh = MAIN_H.get(z, -99)
            if h < mh or (h == mh and z != 11):
                continue                                    # main roof is higher or equal (valley): keep it
            if 8 <= x <= 10 and z in (10, 11):
                for y in range(G + 6, G + h):              # open the loft into the wing
                    b.remove(x, y, z)
            if z == 11:
                b.remove(x, PLATE, z)                       # main eave lip under the wing
            if x == 9:
                if front:
                    b.set(x, G + h, z, SP.slab("bottom"))   # half-height apex cap: no post on the gable tip
                else:
                    b.set(x, G + h, z, DO.stripped_log("z"))
                    b.set(x, G + h + 1, z, SP.slab("bottom"))
            else:
                role = "wing_trim" if (front or x in (6, 12)) else "field"
                roof_cell(x, G + h, z, "S", "east" if x < 9 else "west", role,
                          p=P_UPPER if x in (8, 10) else 0.0, along=z, course=x)
    b.set(9, G + 9, 9, DO.planks)                               # seal the valley under the dying wing ridge
    b.set(9, G + 9, zf, DO.stairs("south", "top"))              # corbel under the apex, hood over the gable window
    b.set(6, G + 6, zf, DO.stairs("east", "top"))               # eave brackets at the wing's front corners
    b.set(12, G + 6, zf, DO.stairs("west", "top"))


def wing_walls():
    x0, x1 = WING_X
    z0, z1 = WING_Z
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            side = x in WING_X
            if not side:
                b.set(x, G + 1, z, SP.planks)                   # porch floor
                for y in (G - 1, G):
                    b.set(x, y, z, stone_mix(x, y, z, seed=51))
                continue
            for y in (G - 1, G, G + 1):
                b.set(x, y, z, stone_mix(x, y, z, seed=52))
            for y in range(G + 2, PLATE + 1):
                b.set(x, y, z, plaster(x, y, z))
    # ground storey front: open between corner posts; bressumer beam at g+5 on z13
    for x in WING_X:
        b.fill(x, G + 2, z1, x, G + 4, z1, DO.log("y"))
    b.fill(x0, G + 5, z1, x1, G + 5, z1, DO.stripped_log("x"))
    # loft floor over the porch, jetty joists projecting to z14 (their ends show), corbels under the corners
    for x in range(x0 + 1, x1):
        for z in range(z0, z1 + 1):
            b.set(x, LOFT, z, SP.planks if z < z1 else DO.stripped_log("x"))
        b.set(x, LOFT, JETTY_Z, DO.stripped_log("z") if x != 9 else DO.stairs("north", "top"))
    for x in WING_X:
        b.set(x, LOFT, JETTY_Z, DO.stairs("north", "top"))
    # upper storey: side knee walls run out to the jetty, the jettied gable face on z14
    for x in WING_X:
        b.fill(x, G + 6, JETTY_Z, x, PLATE, JETTY_Z, DO.log("y"))
    for x in range(x0 + 1, x1):
        for y in (G + 6, G + 7, G + 8):
            b.set(x, y, JETTY_Z, plaster(x, y, JETTY_Z))
    b.set(9, G + 7, JETTY_Z, pane())
    b.set(9, G + 8, JETTY_Z, pane())
    b.set(9, G + 9, JETTY_Z, "calcite")                         # calcite apex under the ridge
    # the main wall's plate is cut where the loft runs into the wing
    for x in (8, 9, 10):
        b.remove(x, PLATE, Z1)


def roof_details():
    """eyebrow windows (south over the vault, and its north twin), a 3-wide gable dormer over the loft."""
    # south eyebrow: three panes in the lowest course, a round-headed arch (stairs toward the jambs + top slab)
    for x in (4, 5, 6):
        b.set(x, G + 8, Z1, pane())
    b.set(4, G + 9, Z1, DO.stairs("west", "top"))
    b.set(5, G + 9, Z1, DO.slab("top"))
    b.set(6, G + 9, Z1, DO.stairs("east", "top"))
    b.set(6, G + 8, Z1 - 1, candle("white", 2))                 # candle on the tie beam = the eyebrow's inner sill
    # north eyebrow over the vault (x4..6, two clear of the dormer), same recipe
    for x in (4, 5, 6):
        b.set(x, G + 8, Z0, pane())
    b.set(4, G + 9, Z0, DO.stairs("west", "top"))
    b.set(5, G + 9, Z0, DO.slab("top"))
    b.set(6, G + 9, Z0, DO.stairs("east", "top"))
    # gable dormer (north slope, x9..11): posts + 1x1 glass + calcite gable; its 45-degree roof (ridge log g+10,
    # two below the main cap) dies into the main slope at z6
    b.set(9, G + 8, Z0, DO.log("y"))
    b.set(11, G + 8, Z0, DO.log("y"))
    b.set(10, G + 8, Z0, pane())
    b.set(10, G + 9, Z0, "calcite")
    b.remove(10, G + 9, 5)                                      # dormer interior opens the loft upward
    for z in (3, 4, 5):
        role = "trim" if z == 3 else "field"
        roof_cell(9, G + 9, z, "S", "east", role, along=z, course=9)
        roof_cell(11, G + 9, z, "S", "west", role, along=z, course=11)
    for z in (3, 4, 5, 6):
        b.set(10, G + 10, z, DO.stripped_log("z"))
    b.set(10, G + 9, 3, DO.stairs("north", "top"))             # corbel under the dormer's front ridge end


def chimney():
    """exterior gable stack: 4-deep stone base to g+3 with a stair shoulder; 3x3 to g+9, brick shoulders, then a
    slim 2x3 shaft to the rim (g+13), no crown ring. The smoke campfire sits two below the rim, walled in on all four
    sides (the ridge core is its east neighbour), so no flame shows; open flue above it."""
    for x in range(-1, 3):
        for z in (6, 7, 8):
            for y in range(G - 1, G + 4):
                b.set(x, y, z, chimney_mat(x, y, z))
    for z in (6, 7, 8):
        b.set(-1, G + 4, z, COB.stairs("east"))
    for x in range(0, 3):
        for z in (6, 7, 8):
            for y in range(G + 4, G + 14):
                if x == 0 and y >= G + 10:
                    continue                                    # taper above the eave: the stack is 2 deep
                b.set(x, y, z, chimney_mat(x, y, z))
    for z in (6, 7, 8):
        b.set(0, G + 10, z, BRK.stairs("east"))                # shoulder
    b.set(1, G + 14, 6, "flower_pot")                          # two chimney pots on the rim
    b.set(1, G + 14, 8, state("decorated_pot", facing="west"))
    for (x, y, z, f) in ((0, G + 1, 9, "north"), (0, G + 2, 9, "north"), (-1, G + 1, 9, "north"),
                         (0, G + 3, 9, "north"), (-2, G + 1, 7, "east"), (-2, G + 2, 7, "east")):
        b.set(x, y, z, vine(f))
    b.set(2, G + 11, 7, campfire("north"))                      # flue on the 2-wide stack's inner edge
    b.remove(2, G + 12, 7)
    b.remove(2, G + 13, 7)
    b.set(3, G + 12, 7, "bricks")                                # close the rim on the ridge side (no notch)
    b.set(3, G + 13, 7, "bricks")


def woodpile_shed():
    """lean-to woodshed on the east gable: spruce roof on fence posts, a stack of mixed logs (ends AND bark)."""
    for z in range(8, 11):
        b.set(14, G + 4, z, SP.stairs("west"))
        b.set(15, G + 4, z, SP.slab("bottom"))
    for z in (8, 10):
        b.fill(15, G + 1, z, 15, G + 3, z, SP.fence)
    stack = {(8, 1): OAK.log("x"), (9, 1): SP.log("z"), (10, 1): OAK.log("x"),
             (8, 2): SP.log("x"), (9, 2): BI.log("x"), (10, 2): SP.log("z"),
             (8, 3): BI.log("x"), (9, 3): OAK.log("z")}
    for (z, dy), st in stack.items():
        b.set(14, G + dy, z, st)
    b.set(14, G + 3, 10, OAK.slab("bottom"))
    b.set(15, G + 1, 9, SP.log("z"))


# ================================================================================================================
# 4. facade details: windows (frame proud, glass back), pale shutters/sills, flower boxes, door, porch
# ================================================================================================================
FLOWERS = ("oxeye_daisy", "dandelion")


def flower_box(cells, front_dir, end_cells, seed):
    """soil at L+1, plants on it, front board at L+2 (trapdoor facing out), end boards."""
    dx, dz = {"south": (0, 1), "east": (1, 0), "north": (0, -1), "west": (-1, 0)}[front_dir]
    for i, (x, y, z) in enumerate(cells):
        b.set(x, y, z, pick(["rooted_dirt", "coarse_dirt", "moss_block"], x, y, z, seed, weights=[3, 2, 1]))
        b.set(x + dx, y, z + dz, PO.trapdoor(front_dir, open=True))
        plant = ("wildflowers", FLOWERS[0], "cornflower", FLOWERS[1], "allium")[(i + seed) % 5]
        if plant == "wildflowers":
            b.set(x, y + 1, z, state("wildflowers", flower_amount=3, facing=front_dir))
        else:
            b.set(x, y + 1, z, plant)
    for (x, y, z, f) in end_cells:
        b.set(x, y, z, PO.trapdoor(f, open=True))


def facade_south():
    # bay window on the living room: glazing pushed out to z11 between a new post (x3) and the wing wall (x7),
    # stripped-log sill and head beams on a cobble plinth, its own little spruce roof under the main roof
    for x in range(3, 7):
        for y in (G - 1, G, G + 1):
            b.set(x, y, 11, stone_mix(x, y, 11, seed=61))
    b.fill(3, G + 2, 11, 3, G + 6, 11, DO.log("y"))
    for x in (4, 5, 6):
        b.set(x, G + 2, 11, DO.stripped_log("x"))
        for y in (G + 3, G + 4, G + 5):
            b.set(x, y, 11, pane())
        b.set(x, G + 6, 11, plaster(x, G + 6, 11))              # cream frieze between glass and bay roof
        for y in (G + 2, G + 3, G + 4, G + 5):
            b.remove(x, y, Z1)                                  # the old wall opens into the bay
        b.set(x, G + 1, Z1, SP.planks)
        b.set(x, G + 2, Z1, SP.stairs("south"))                 # window seat in the bay
    for x in (3, 4, 5):
        b.set(x, PLATE, 11, DO.stairs("north"))                 # bay roof = the dark-oak south eave course
    b.set(X0 - 1, G + 6, 11, DO.stairs("north", "top"))         # bracket under the verge corner
    flower_box([(x, G + 2, 12) for x in (4, 5, 6)], "south", [(3, G + 2, 12, "west")], seed=1)
    b.set(4, G + 1, 12, DO.stairs("north", "top"))
    b.set(6, G + 1, 12, DO.stairs("north", "top"))
    # door: oak (windowed), transom light and a lintel; plaster either side
    for x in (8, 10):
        for y in range(G + 2, G + 5):
            b.set(x, y, Z1, plaster(x, y, Z1))
    b.fill(8, G + 5, Z1, 10, G + 5, Z1, DO.stripped_log("x"))
    b.set(DOOR_X, G + 4, Z1, pane())
    # stair window east of the porch: 1x2, no shutters, a pale sill
    b.set(12, G + 3, Z1, pane())
    b.set(12, G + 4, Z1, pane())
    b.set(12, G + 2, 11, PO.trapdoor("south", "top"))
    # porch: round-headed opening, bench, barrel + pot, lantern under the porch ceiling
    b.set(8, G + 4, WING_Z[1], PO.stairs("west", "top"))       # round-headed porch opening, cream arch
    b.set(10, G + 4, WING_Z[1], PO.stairs("east", "top"))
    b.set(8, G + 2, 11, SP.stairs("west"))
    b.set(8, G + 2, 12, SP.stairs("west"))
    b.set(8, G + 2, 13, PO.trapdoor("south", open=True))
    b.set(10, G + 2, 11, barrel("up"))
    b.set(10, G + 3, 11, potted("azalea_bush"))
    b.set(8, G + 4, 11, lantern(hanging=True))                 # lights the door recess, clear of the transom
    b.set(10, G + 4, JETTY_Z, lantern(hanging=True))            # and one under a jetty joist end, over the steps
    # side opening in the porch's east wall with a fence rail
    b.set(11, G + 2, 12, SP.fence)
    b.remove(11, G + 3, 12)
    b.remove(11, G + 4, 12)
    # jetty: a flowering-azalea box on a bracket right under the gable window (pink on the focal point)
    b.set(9, G + 5, JETTY_Z + 1, DO.stairs("north", "top"))
    b.set(9, G + 6, JETTY_Z + 1, leaves("flowering_azalea"))
    # steps up to the porch, peonies either side
    for x in (8, 9, 10):
        b.set(x, G + 1, 14, (SP if x == 9 else COB).stairs("north"))


def facade_east():
    # kitchen window 2x2 with a flower box and a PAIR of pale shutters (the woodpile moved south to make room)
    for z in (5, 6):
        b.set(X1, G + 3, z, pane())
        b.set(X1, G + 4, z, pane())
        b.set(X1 + 1, G + 5, z, DO.stairs("west", "top"))
    flower_box([(X1 + 1, G + 2, z) for z in (5, 6)], "east", [(X1 + 1, G + 2, 4, "north"),
                                                             (X1 + 1, G + 2, 7, "south")], seed=2)
    for z in (4, 7):
        b.set(X1 + 1, G + 3, z, PO.trapdoor("east", "bottom", open=True))
        b.set(X1 + 1, G + 4, z, PO.trapdoor("east", "top", open=True))
    # gable window 1x2 under the half-hip (the hip course is its hood), pale sill and shutters
    b.set(X1, G + 8, RZ, pane())
    b.set(X1, G + 9, RZ, pane())
    b.set(X1 + 1, PLATE, RZ, PO.trapdoor("east", "top"))
    for z in (6, 8):
        b.set(X1 + 1, G + 8, z, PO.trapdoor("east", "bottom", open=True))
        b.set(X1 + 1, G + 9, z, PO.trapdoor("east", "top", open=True))


def facade_west():
    b.set(X0, G + 3, 9, pane())
    b.set(X0, G + 4, 9, pane())
    b.set(X0 - 1, G + 3, 10, PO.trapdoor("west", "bottom", open=True))     # one shutter (the stack is the other side)
    b.set(X0 - 1, G + 4, 10, PO.trapdoor("west", "top", open=True))
    b.set(X0 - 1, G + 2, 9, PO.trapdoor("west", "top"))
    b.set(X0 - 1, G + 5, 9, DO.stairs("east", "top"))


def facade_north():
    b.set(12, G + 3, Z0, pane())                                   # little window over the kitchen counter
    b.set(12, G + 2, Z0 - 1, PO.trapdoor("north", "top"))
    b.set(LEAN_X[1], G + 3, 2, pane())                             # pantry window in the lean-to's east wall
    b.set(LEAN_X[1] + 1, G + 4, 2, DO.stairs("west", "top"))
    b.set(8, G + 3, 1, pane())                                     # pantry window on the north, plate as its head
    b.set(8, G + 2, 0, PO.trapdoor("north", "top"))
    for x in (LEAN_X[0], LEAN_X[1]):                               # quoins: stone bricks, alternating 1/2
        b.set(x, G + 1, 1, "mossy_cobblestone")
        b.set(x, G + 2, 1, "stone_bricks")
        b.set(x, G + 3, 1, "stone_bricks")
        b.set(x, G + 2, 2, "mossy_stone_bricks")
    for x in (7, 9, 11):                                           # rafter tails: tops meet the lip's underside
        b.set(x, G + 4, -1, SP.fence)
    b.set(X1, G + 6, Z1 + 1, SP.fence)                             # rafter tail under the south lip (east part)
    # arch from the main room into the pantry (round head: inverted stairs facing their jambs)
    for x in (8, 9):
        b.remove(x, G + 2, Z0)
        b.remove(x, G + 3, Z0)
    b.set(8, G + 4, Z0, PO.stairs("west", "top"))
    b.set(9, G + 4, Z0, PO.stairs("east", "top"))


# ================================================================================================================
# 5. interior
# ================================================================================================================
def floors():
    """spruce field with a dark oak border, stone kitchen corner, brick hearth, stone pantry."""
    for x in range(X0 + 1, X1):
        for z in range(Z0 + 1, Z1):
            if x >= 10:                                         # the whole kitchen strip in stone
                b.set(x, G + 1, z, "polished_andesite" if (x + z) % 2 else "stone_bricks")
            else:                                               # one spruce field for the living zone
                b.set(x, G + 1, z, SP.planks)
    for z in (6, 7, 8):
        b.set(X0, G + 1, z, "bricks")
    for x in range(LEAN_X[0] + 1, LEAN_X[1]):
        for z in (2, 3):
            b.set(x, G + 1, z, pick(["stone_bricks", "cobblestone", "mossy_stone_bricks"], x, 1, z, 81,
                                    weights=[4, 2, 1]))
    b.set(8, G + 1, Z0, "stone_bricks")                         # threshold under the pantry arch
    b.set(9, G + 1, Z0, "stone_bricks")


def hearth():
    """inglenook: 3-wide recess in the brick west wall, the fire set back into the chimney, mantel shelf."""
    for z in (6, 7, 8):
        b.remove(X0, G + 2, z)
        b.remove(X0, G + 3, z)
    b.set(X0 - 1, G + 2, 7, campfire("east"))
    for y in range(G + 3, G + 9):                               # short open flue: the indoor smoke goes up
        b.remove(X0 - 1, y, 7)
    b.set(X0, G + 2, 8, SP.log("z"))                            # firewood in the recess
    b.set(X0, G + 2, 6, "decorated_pot")
    b.set(X0, G + 4, 7, BRK.stairs("west", "top"))              # arched brick lintel
    for z in (6, 7, 8):
        b.set(X0 + 1, G + 4, z, DO.stairs("west", "top"))       # mantel shelf
    b.set(X0 + 1, G + 5, 6, candle("white", 2))
    b.set(X0 + 1, G + 5, 7, potted("dandelion"))
    b.set(X0 + 1, G + 5, 8, candle("white", 3))


def living_room():
    # armchairs facing the fire, rug between, window seat, bookcase wall, tie beam + ridge lantern in the vault
    for z in (6, 8):
        b.set(6, G + 2, z, state("brown_wool_stairs", facing="east"))
    for (x, z) in ((4, 6), (5, 6), (4, 8), (5, 8)):
        b.set(x, G + 2, z, carpet("red"))
    b.set(6, G + 2, 7, barrel("up"))                            # side table between the armchairs
    b.set(6, G + 3, 7, candle("white", 2))
    for (x, z) in ((4, 7), (5, 7)):
        b.set(x, G + 2, z, carpet("brown"))
    b.set(4, G + 2, 9, potted("fern"))
    for x in (4, 6):
        b.fill(x, G + 2, 5, x, G + 3, 5, "bookshelf")
    b.set(5, G + 2, 5, state("chiseled_bookshelf", facing="south", slot_0_occupied=True, slot_1_occupied=True,
                            slot_3_occupied=True, slot_4_occupied=True, slot_5_occupied=True))
    b.set(5, G + 3, 5, DO.shelf("south"))
    for x in (4, 5, 6):
        b.set(x, G + 4, 5, DO.stairs("north", "top"))           # cornice over the bookcase
    b.set(7, G + 2, 5, "lectern")
    # vault: tie beam across at x6, lantern on a chain from the ridge
    b.fill(6, PLATE, Z0 + 1, 6, PLATE, Z1 - 1, DO.stripped_log("z"))
    for y in (G + 9, G + 10):
        b.set(5, y, RZ, chain("y"))
    b.set(5, G + 8, RZ, lantern(hanging=True))


def loft():
    """sleeping loft at g+5 over x8..x12 and into the wing; ceiling beams below; railing over the vault."""
    for x in range(LOFT_X[0], LOFT_X[1] + 1):
        for z in range(Z0 + 1, Z1):
            b.set(x, LOFT, z, DO.stripped_log("z") if x in (8, 11) else SP.planks)
    for z in (7, 8, 9):                                         # stairwell
        b.remove(12, LOFT, z)
    for z in range(Z0 + 1, Z1):
        b.set(8, LOFT + 1, z, SP.fence)                         # railing over the living-room vault
    b.set(11, LOFT + 1, 8, SP.fence)                            # stairwell rail
    b.set(11, LOFT + 1, 9, SP.fence)
    b.set(8, LOFT - 1, Z1 - 1, SP.stairs("south", "top"))       # beam bracket at the loft edge
    # stair along the east wall: z9 g+2 -> z7 g+4 -> loft floor at z6
    for i, z in enumerate((9, 8, 7)):
        b.set(12, G + 2 + i, z, SP.stairs("north"))
    b.set(12, G + 2, 8, state("chiseled_bookshelf", facing="west", slot_0_occupied=True, slot_1_occupied=True,
                              slot_4_occupied=True))                 # under-stair storage
    b.set(12, G + 2, 7, barrel("west"))
    b.set(12, G + 3, 7, SP.planks)
    # loft furniture: bed nook in the wing gable, nightstand under the gable window, storage under the eaves
    b.bed(10, LOFT + 1, 12, "white", "south")
    b.set(9, LOFT + 1, 13, state("chiseled_bookshelf", facing="north", slot_1_occupied=True,
                                 slot_2_occupied=True, slot_4_occupied=True))
    b.set(9, LOFT + 2, 13, candle("white", 3))
    b.set(8, LOFT + 1, 13, chest("east"))
    b.set(8, LOFT + 1, 11, potted("oxeye_daisy"))
    b.set(10, LOFT + 1, 11, carpet("red"))
    b.set(9, LOFT + 1, 5, state("chiseled_bookshelf", facing="south", slot_0_occupied=True, slot_2_occupied=True,
                                slot_3_occupied=True))
    b.set(12, LOFT + 1, 5, barrel("west"))
    b.set(10, LOFT + 1, 5, chest("south"))
    b.set(11, LOFT + 1, 5, DO.slab("top"))                      # writing desk
    b.set(11, LOFT + 2, 5, candle("white", 2))
    b.set(12, LOFT + 2, 5, "flower_pot")
    for (x, z) in ((9, 6), (10, 6), (9, 7), (10, 7), (11, 7), (9, 8), (10, 8), (11, 8)):
        b.set(x, LOFT + 1, z, carpet("white" if (x, z) in ((10, 7), (9, 7)) else "brown"))
    b.set(11, LOFT + 1, 6, SP.stairs("south"))                  # desk chair under the north dormer
    b.set(10, G + 10, RZ, chain("y"))
    b.set(10, G + 9, RZ, lantern(hanging=True))


def kitchen_dining():
    b.set(10, G + 2, 5, barrel("up"))
    b.set(10, G + 3, 5, DO.shelf("south"))
    b.set(11, G + 2, 5, "water_cauldron[level=3]")             # sink under the little north window
    b.set(12, G + 2, 5, state("smoker", facing="south"))
    b.set(12, G + 3, 5, BRK.stairs("north", "top"))             # hood
    b.set(12, G + 4, 5, "bricks")
    b.set(12, G + 2, 6, "crafting_table")
    # table for two
    b.set(10, G + 2, 7, SP.fence)
    b.set(10, G + 3, 7, SP.pressure_plate)
    b.set(10, G + 2, 6, SP.stairs("north"))
    b.set(10, G + 2, 8, SP.stairs("south"))
    b.set(10, LOFT - 1, 7, lantern(hanging=True))


def pantry():
    b.set(6, G + 2, 2, barrel("up"))
    b.set(6, G + 3, 2, candle("white", 2))
    b.set(6, G + 2, 3, state("hay_block", axis="z"))
    b.set(7, G + 2, 2, DO.shelf("south"))
    b.set(8, G + 2, 2, chest("south"))
    b.set(9, G + 2, 2, "pumpkin")
    b.set(10, G + 2, 2, state("composter", level=5))
    b.set(10, G + 2, 3, "decorated_pot")
    b.set(7, G + 3, 2, DO.shelf("south"))


# ================================================================================================================
# 6. landscaping (ground layer g only where authored; everything else stays natural terrain)
# ================================================================================================================
import math

SITE_C = (8.0, 10.0)            # the landscaped area fades out inside an organic ellipse around the cottage
SITE_R = (12.5, 11.5)


def in_site(x, z, margin=0.0):
    nx, nz = (x - SITE_C[0]) / SITE_R[0], (z - SITE_C[1]) / SITE_R[1]
    return math.hypot(nx, nz) + (value2(x, z, 151, scale=4.0) - 0.5) * 0.35 <= 1.0 - margin


def free(x, z, y=G + 1):
    return (x, y, z) not in b and (x, G, z) not in b


def seg_dist(px, pz, a, c):
    (ax, az), (cx, cz) = a, c
    vx, vz = cx - ax, cz - az
    t = max(0.0, min(1.0, ((px - ax) * vx + (pz - az) * vz) / float(vx * vx + vz * vz)))
    return math.hypot(px - (ax + t * vx), pz - (az + t * vz))


def poly_dist(px, pz, pts):
    return min(seg_dist(px, pz, pts[i], pts[i + 1]) for i in range(len(pts) - 1))


# path: down the steps, a soft bend west, then out of the site to the SW (it keeps going in the world)
MAIN_PATH = [(9, 14.5), (9, 16.2), (7.5, 17.4), (5.0, 18.0), (2.2, 18.4), (-0.5, 19.4), (-3.5, 20.6)]
SPUR_GARDEN = [(10, 16.4), (13.4, 16.0)]                       # to the vegetable-garden gate
SPUR_SHED = [(10.5, 15.4), (12.6, 14.6), (15.2, 13.0), (16.2, 11.0)]   # round the corner to the woodpile


def paths():
    """a continuous worn dirt_path track (about 2 wide on the main path, 1 on the spurs); coarse/rooted speckle only
    on its outermost cells (<= 25%), a few grass bites into the edge -- no patchwork of tiles."""
    track = {}
    for x in range(-5, 21):
        for z in range(8, 24):
            if not free(x, z):
                continue
            wob = (value2(x, z, 91, scale=3.0) - 0.5) * 0.35
            d_main = poly_dist(x, z, MAIN_PATH) + wob
            d_spur = min(poly_dist(x, z, SPUR_GARDEN), poly_dist(x, z, SPUR_SHED)) + wob
            if (d_main <= 0.95 and (in_site(x, z, -0.08) or d_main < 0.5)) or d_spur <= 0.5:
                track[(x, z)] = d_main <= 0.95
    for (x, z), main in track.items():
        edge = any((x + dx, z + dz) not in track for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        n = value2(x, z, 92, scale=1.7)
        if edge and main and n > 0.83:
            continue                                            # grass bites into the edge
        top = "dirt_path"
        if edge and n < 0.25:
            top = "coarse_dirt" if hash01(x, 0, z, 93) < 0.6 else "rooted_dirt"
        b.set(x, G, z, top)


def bed(cells, species, seed, tall=None, filler="wildflowers", density=0.78):
    """grass soil with coarse/rooted dirt patches, drifts of 2 species + filler (smooth noise picks the drift)."""
    for (x, z) in cells:
        if not free(x, z):
            continue
        n = value2(x, z, seed, scale=2.2)
        b.set(x, G, z, "grass_block" if n > 0.22 else pick(["coarse_dirt", "rooted_dirt"], x, 0, z, seed + 1))
        if not chance(density, x, 1, z, seed + 2):
            if chance(0.6, x, 2, z, seed + 3):
                b.set(x, G + 1, z, "short_grass")
            continue
        k = int(n * len(species) * 1.0 + 0.0001) if len(species) > 2 else (0 if n < 0.36 else (-1 if n < 0.60 else 1))
        k = min(k, len(species) - 1)
        if len(species) == 2 and k == -1 or len(species) > 2 and value2(x, z, seed + 9, 1.6) > 0.72:
            b.set(x, G + 1, z, state(filler, flower_amount=2 + hash3(x, 0, z, seed) % 3,
                                     facing=("north", "east", "south", "west")[hash3(x, 1, z, seed) % 4]))
        else:
            b.set(x, G + 1, z, species[k])
    for (x, z, plant) in (tall or ()):
        if free(x, z, G + 1) and (x, G + 2, z) not in b:
            b.set(x, G, z, "grass_block")
            b.tall(x, G + 1, z, plant)


def bush(cx, cz, h, seed, r=1.3, flowering=0.15):
    """irregular leaf blob (persistent azalea/oak leaves), widest low, tapering up."""
    for x in range(int(cx - r - 1), int(cx + r + 2)):
        for z in range(int(cz - r - 1), int(cz + r + 2)):
            for y in range(G + 1, G + 1 + h):
                k = (y - G - 1) / max(1, h)
                rr = r * (1.0 - 0.45 * k) + (value3(x, y, z, seed, 1.5) - 0.5) * 0.9
                if math.hypot(x - cx, z - cz) > rr or (x, y, z) in b:
                    continue
                if y == G + 1 and (x, G, z) in b and not b.get(x, G, z).startswith("minecraft:grass"):
                    continue
                if y > G + 1 and (x, y - 1, z) not in b:
                    continue                                    # no overhanging leaf over air at the edges
                roll = hash01(x, y, z, seed)
                kind = "flowering_azalea" if roll < flowering else ("azalea" if roll < 0.7 else "oak")
                b.set(x, y, z, leaves(kind))
                if (x, G, z) not in b:
                    b.set(x, G, z, "grass_block")


def orchard_tree(bx, bz):
    """T1 orchard oak leaning toward the house: trunk kinks once, two branches at different heights,
    a flat-bottomed flowering canopy (widest at branch level, gaps underneath), soft root flare."""
    trunk = [(bx, G + 1, bz), (bx, G + 2, bz), (bx - 1, G + 3, bz), (bx - 1, G + 4, bz), (bx - 1, G + 5, bz)]
    for (x, y, z) in trunk:
        b.set(x, y, z, OAK.log("y"))
    b.set(bx, G + 3, bz, OAK.wood("x"))                         # thick knot where the trunk leans
    # branch 1 (low, north-east) and branch 2 (higher, long, toward the house / south-west)
    b.set(bx - 1, G + 4, bz - 1, OAK.log("z"))
    b.set(bx - 1, G + 4, bz - 2, OAK.log("z"))
    b.set(bx, G + 5, bz - 2, OAK.log("x"))
    b.set(bx - 2, G + 5, bz, OAK.log("x"))
    b.set(bx - 3, G + 5, bz, OAK.log("x"))
    b.set(bx - 3, G + 6, bz + 1, OAK.log("z"))
    b.set(bx - 4, G + 6, bz + 1, OAK.fence)
    b.set(bx - 1, G + 6, bz, OAK.log("y"))
    # root flare: slabs + rooted dirt + moss, not a ring of stairs
    for (x, z, s_) in ((bx, bz, "rooted_dirt"), (bx + 1, bz, "rooted_dirt"), (bx, bz + 1, "rooted_dirt"),
                       (bx - 1, bz, "moss_block"), (bx, bz - 1, "rooted_dirt"), (bx + 1, bz + 1, "moss_block"),
                       (bx + 2, bz, "coarse_dirt")):
        b.set(x, G, z, s_)
    b.set(bx - 1, G + 1, bz, "moss_carpet")
    b.set(bx + 1, G + 1, bz + 1, "fern")
    b.set(bx + 1, G + 1, bz, "moss_carpet")
    b.set(bx, G + 1, bz - 1, "fern")
    b.set(bx + 1, G + 1, bz, OAK.log("x"))                      # 1-long root stubs
    b.set(bx, G + 1, bz + 1, OAK.log("z"))
    # canopy: one dome (ellipsoid with per-cell jittered radius), widest at g+7, an irregular hanging fringe
    cx, cy, cz, rx, ry, rz = bx - 1.0, G + 7.4, bz, 3.6, 2.2, 3.4
    for x in range(bx - 6, bx + 4):
        for z in range(bz - 5, bz + 5):
            for y in range(G + 6, G + 11):
                if (x, y, z) in b or (x <= X1 + 1 and z >= 2):
                    continue                                    # frame the corner, never grow into the roof
                j = 1.0 + (hash01(x, y, z, 104) - 0.5) * 0.34
                q = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rz) ** 2
                if q > j * j:
                    continue
                if y == G + 6 and abs(x - cx) > 2.4 and abs(z - cz) > 2.2:
                    continue                                    # cut the corners of the lowest full layer
                roll = hash01(x, y, z, 102)
                b.set(x, y, z, leaves("flowering_azalea" if roll < 0.2 else ("azalea" if roll < 0.55 else "oak")))
    for (x, z) in ((bx - 4, bz + 1), (bx - 3, bz + 2), (bx + 1, bz - 2), (bx + 2, bz), (bx + 1, bz + 2),
                   (bx - 2, bz - 3), (bx - 1, bz - 1), (bx - 1, bz - 2), (bx - 2, bz - 2)):
        if (x, G + 5, z) not in b and (x, G + 6, z) in b and not (x <= X1 + 1 and z >= 2):
            b.set(x, G + 5, z, leaves("azalea"))                # fringe; also hides the branch tips


def boulder(x, z, seed):
    """a half-sunk mossy stone cluster: one 1-high stone, a slab chip, moss on top, dirt at its foot."""
    b.set(x, G, z, "coarse_dirt")
    b.set(x, G + 1, z, pick(["mossy_cobblestone", "cobblestone", "andesite"], x, 0, z, seed, weights=[3, 1, 1]))
    b.set(x, G + 2, z, "moss_carpet")
    dx, dz = ((1, 0), (0, 1), (-1, 0))[seed % 3]
    b.set(x + dx, G, z + dz, "moss_block")
    b.set(x + dx, G + 1, z + dz, stone("cobblestone").slab("bottom") if seed % 2 else "moss_carpet")


def pond():
    """a small bean-shaped pond SW of the house: water at g, deeper (g-1) in its belly, clay bed; banks mostly
    grass and moss, a little coarse dirt/mud only on the path side; boulders at both tips, reeds, lily pads.
    Every water cell is contained by blocks placed here."""
    water = {(1, 13), (2, 15), (1, 16), (0, 17), (-1, 13), (0, 13), (-3, 14), (-2, 14), (-1, 14), (0, 14), (1, 14), (-2, 15), (-1, 15), (0, 15),
             (1, 15), (-1, 16), (0, 16)}
    deep = {(-2, 14), (-1, 14), (0, 14), (-2, 15), (-1, 15), (0, 15)}
    for (x, z) in water:
        b.set(x, G, z, "water")
        if (x, z) in deep:
            b.set(x, G - 1, z, "water")
            b.set(x, G - 2, z, "clay")
        else:
            b.set(x, G - 1, z, "clay" if hash01(x, 0, z, 162) < 0.6 else "dirt")
    for (x, z) in water:
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx_, nz_ = x + dx, z + dz
            if (nx_, nz_) in water:
                continue
            path_side = nz_ >= 16 or nx_ >= 2
            if (nx_, G, nz_) not in b:
                bank = ("coarse_dirt" if hash01(nx_, 0, nz_, 163) < 0.5 else "mud") if path_side and \
                    hash01(nx_, 1, nz_, 164) < 0.45 else ("moss_block" if hash01(nx_, 2, nz_, 165) < 0.35 else
                                                          "grass_block")
                b.set(nx_, G, nz_, bank)
            if (nx_, G - 1, nz_) not in b:
                b.set(nx_, G - 1, nz_, "dirt")
        if (x, z) in deep:
            for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + dx, G - 1, z + dz) not in b:
                    b.set(x + dx, G - 1, z + dz, "dirt")
    for (x, z) in ((-1, 14), (0, 15), (-2, 15)):
        b.set(x, G + 1, z, "lily_pad")
    for (x, z) in ((-4, 14), (2, 14)):                            # boulders at the two tips
        b.set(x, G, z, "moss_block")
        b.set(x, G + 1, z, "mossy_cobblestone")
        b.set(x, G + 2, z, "moss_carpet")
    for (x, z) in ((-3, 13), (-3, 15), (-2, 13)):                 # reeds on the far bank, water beside the soil
        b.set(x, G, z, "grass_block")
        b.set(x, G + 1, z, "sugar_cane")
        b.set(x, G + 2, z, "sugar_cane")
    b.set(2, G + 1, 16, "fern") if b.get(2, G, 16) != "minecraft:water" else None
    b.set(-2, G + 1, 16, "blue_orchid")


def veg_garden():
    """small fenced kitchen garden: carrots, beetroot, potatoes, a pumpkin on its stem, a water hole."""
    x0, x1, z0, z1 = 14, 19, 14, 18
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1):
                b.set(x, G, z, "grass_block")
                if (x, z) == (x1, z1 - 1):                       # one missing fence segment (old fence)
                    b.set(x, G + 1, z, "short_grass")
                    continue
                b.set(x, G + 1, z, SP.fence)
            else:
                b.set(x, G, z, state("farmland", moisture=7))
    b.set(x0, G + 1, 16, SP.gate("east", open=True))
    b.set(x0, G, 16, "coarse_dirt")
    b.set(x0, G + 2, z0, lantern())
    b.set(x1, G + 2, z0, leaves("flowering_azalea"))              # climbing tuft on a corner post
    for x in range(x0 + 1, x1):
        b.set(x, G + 1, 15, state("carrots", age=7))
        b.set(x, G + 1, 17, state("potatoes", age=7))
    b.set(15, G + 1, 16, state("beetroots", age=3))
    b.set(16, G + 1, 16, state("beetroots", age=3))
    b.set(17, G, 16, "water")
    b.set(17, G + 1, 16, "lily_pad")
    b.set(18, G + 1, 16, state("attached_pumpkin_stem", facing="south"))
    b.set(18, G + 1, 17, "pumpkin")
    b.set(18, G, 17, "coarse_dirt")
    b.set(x1 + 1, G + 1, 15, state("composter", level=7))
    b.set(x1 + 1, G, 15, "coarse_dirt")
    # scarecrow keeping watch at the back corner
    b.set(x1 + 1, G, 18, "coarse_dirt")
    b.set(x1 + 1, G + 1, 18, SP.fence)
    b.set(x1 + 1, G + 2, 18, state("hay_block", axis="y"))
    b.set(x1 + 1, G + 3, 18, state("carved_pumpkin", facing="south"))
    b.set(x1 + 1, G + 2, 17, SP.trapdoor("south", open=True))
    b.set(x1 + 1, G + 2, 19, SP.trapdoor("north", open=True))


def handcart(x, z):
    """two-barrel handcart on grindstone wheels, loaded with hay and a pumpkin, handle resting to the west."""
    for (cx, cz) in ((x, z), (x + 1, z), (x, z - 1), (x, z + 1), (x - 1, z)):
        if free(cx, cz):
            b.set(cx, G, cz, "grass_block" if (cx, cz) != (x + 1, z) else "coarse_dirt")
    b.set(x, G + 1, z, barrel("west"))
    b.set(x + 1, G + 1, z, barrel("east"))
    b.set(x, G + 1, z - 1, state("grindstone", face="wall", facing="north"))
    b.set(x, G + 1, z + 1, state("grindstone", face="wall", facing="south"))
    b.set(x - 1, G + 1, z, SP.fence)
    b.set(x, G + 2, z, barrel("up"))
    b.set(x + 1, G + 2, z, state("composter", level=8))


def water_barrel():
    b.set(14, G + 1, 11, "water_cauldron[level=3]")
    b.set(14, G, 11, "mossy_cobblestone")
    for y in (G + 2, G + 3, G + 4):
        b.set(14, y, 11, chain("y"))


def lamp_post(x, z, arm):
    """lamp post A: cobble wall stub, three fence posts, an arm, lantern hanging under it."""
    b.set(x, G, z, "moss_block")
    b.set(x, G + 1, z, "mossy_cobblestone_wall")
    for y in (G + 2, G + 3, G + 4):
        b.set(x, y, z, SP.fence)
    ax, az = x + arm[0], z + arm[1]
    b.set(ax, G + 4, az, SP.fence)
    b.set(ax, G + 3, az, lantern(hanging=True))


def foundation_ring():
    """ring 0: soft planting hugging the plinth -- ferns, bushes, grass, moss -- in patches, not a hedge."""
    ring = set()
    for (x, y, z) in list(b.blocks):
        if y != G + 1:
            continue
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ring.add((x + dx, z + dz))
    for (x, z) in sorted(ring):
        if not free(x, z) or (x, G + 2, z) in b:
            continue
        n = value2(x, z, 171, scale=2.0)
        if n < 0.30:
            continue
        b.set(x, G, z, "grass_block" if n < 0.8 else "moss_block")
        if n > 0.8:
            b.set(x, G + 1, z, "moss_carpet" if chance(0.5, x, 0, z, 172) else "fern")
        else:
            b.set(x, G + 1, z, pick(["fern", "short_grass", "bush", "short_grass", FLOWERS[0]], x, 0, z, 173,
                                    weights=[3, 3, 2, 2, 1]))


def landscape():
    pond()
    paths()
    # colour: daisy + dandelion lead, cornflower / allium / pink tulip accents in drifts, wildflowers filler
    MIX = ("oxeye_daisy", "cornflower", "dandelion", "allium", "pink_tulip", "oxeye_daisy")
    # crescent bed in front of the bay box, west of the wing
    bed([(x, z) for x in range(1, 7) for z in (13, 14) if (x, z) not in ((4, 13), (5, 13), (6, 13), (1, 14))] +
        [(2, 11), (1, 11), (1, 12), (2, 12), (3, 13)], MIX, 111, tall=[(1, 12, "rose_bush")])
    b.set(2, G + 1, 11, "flowering_azalea")                        # pink shrub at the SW corner
    b.set(2, G, 11, "grass_block")
    # bed east of the wing around the water barrel
    bed([(12, 12), (13, 12), (12, 13), (13, 11), (15, 11), (15, 10), (13, 13), (14, 13)], MIX, 112)
    b.set(14, G + 1, 12, "flowering_azalea")
    b.set(14, G, 12, "grass_block")
    # peonies flanking the porch step
    for x in (7, 11):
        b.set(x, G, 14, "grass_block")
        b.tall(x, G + 1, 14, "peony")
    # kidney bed at the path mouth by the lamp
    bed([(x, z) for x in range(1, 7) for z in range(19, 23) if math.hypot(x - 3.6, (z - 20.3) * 1.5) < 2.2],
        MIX, 113)
    # east plinth drifts (by the bench and the chopping block)
    bed([(16, 3), (16, 4), (17, 3), (16, 6), (17, 7), (16, 10), (16, 11), (17, 11), (17, 10)], MIX, 114)
    lamp_post(4, 20, (0, -1))
    bush(3.4, 2.6, 2, 131, r=1.2)
    for (x, y, z) in ((4, G + 1, 0), (4, G + 2, 0), (3, G + 1, 0), (4, G + 1, -1)):   # tuck at the catslide corner
        if (x, y, z) not in b:
            b.set(x, y, z, leaves("flowering_azalea" if y == G + 2 else "azalea"))
    for (x, ys) in ((6, (G + 1, G + 2, G + 3, G + 4)), (10, (G + 2, G + 3, G + 4))):  # two ivy strands on the lean-to
        for y in ys:
            if (x, y, 0) not in b:
                b.set(x, y, 0, vine("south"))
    bush(13.2, 1.4, 2, 132, r=1.0)
    bush(-1.6, 2.0, 3, 133, r=1.8, flowering=0.3)                  # azalea clump NW
    bush(-2.4, 4.4, 2, 135, r=1.0, flowering=0.2)
    # the orchard tree NE with a bench under it, facing the garden
    orchard_tree(19, 2)
    for x in (17, 18):
        b.set(x, G + 1, 5, OAK.stairs("north"))
    b.set(16, G + 1, 5, OAK.trapdoor("west", open=True))
    b.set(19, G + 1, 5, OAK.trapdoor("east", open=True))
    for (x, z, n) in ((16, 2, 3), (17, 1, 2), (20, 4, 4), (18, 7, 1), (21, 1, 2), (15, 4, 2), (17, 6, 3),
                      (20, 6, 2), (16, 0, 1)):
        if free(x, z):
            b.set(x, G, z, "grass_block")
            b.set(x, G + 1, z, state("leaf_litter", segment_amount=n, facing=("north", "east", "south")[n % 3]))
    veg_garden()
    water_barrel()
    handcart(14, 20)
    for (x, z) in ((15, 19), (16, 19), (15, 21)):                 # a drift ties the cart to the garden fence
        if free(x, z):
            b.set(x, G, z, "grass_block")
            b.set(x, G + 1, z, state("wildflowers", flower_amount=3, facing="east") if x == 15 else "bush")
    for (x, z, top) in ((5, 18, "dirt_path"), (4, 17, "coarse_dirt"), (11, 17, "coarse_dirt"),
                        (-3, 19, "rooted_dirt")):                 # path corners: no long straight steps
        if (x, G + 1, z) not in b:
            b.set(x, G, z, top)
    for (x, z) in ((13, 15), (1, 18)):                            # grass bites into the path edge
        if (x, G + 1, z) not in b:
            b.set(x, G, z, "grass_block")
            b.set(x, G + 1, z, "short_grass")
    # chopping block by the woodpile
    b.set(16, G, 9, "coarse_dirt")
    b.set(16, G + 1, 9, OAK.stripped_log("y"))
    b.set(16, G + 2, 9, state("lever", face="floor", facing="east"))
    # old spruce fence along the west edge, running out into the meadow (a gap, a stone stub, a tuft)
    fence_line = [(-2, -1), (-3, -1), (-4, -1), (-4, 0)] + [(-4, z) for z in range(1, 10)] + [(-5, 10), (-5, 11)]
    for i, (x, z) in enumerate(fence_line):
        if (x, G + 1, z) in b or (x, G, z) in b and not b.get(x, G, z).startswith("minecraft:grass"):
            continue
        b.set(x, G, z, "grass_block")
        b.set(x, G + 1, z, "mossy_cobblestone_wall" if z == 6 else SP.fence)
    b.set(-4, G + 2, 0, leaves("azalea"))
    boulder(-2, 17, 1)
    boulder(20, 10, 2)
    foundation_ring()
    # ring 2 fade: scattered daisies, dandelions, grass tufts thinning out toward the site edge
    for x in range(-6, 23):
        for z in range(-3, 24):
            if not free(x, z) or not in_site(x, z):
                continue
            near = -2 <= x <= 19 and -3 <= z <= 19
            edge = 1.0 if near else 0.25
            if value2(x, z, 141, scale=3.0) > 0.55 and chance(0.30 * edge, x, 0, z, 142):
                b.set(x, G, z, "grass_block")
                b.set(x, G + 1, z, pick(["oxeye_daisy", "dandelion", "short_grass", "wildflowers"], x, 1, z, 143,
                                        weights=[3, 3, 3, 2]))


# ================================================================================================================
foundations()
walls()
lean_to_walls()
main_roof()
wing_roof()
wing_walls()
roof_details()
chimney()
woodpile_shed()
facade_south()
facade_east()
facade_west()
facade_north()
floors()
hearth()
living_room()
loft()
kitchen_dining()
pantry()
b.fill(DOOR_X, G + 2, Z1, DOOR_X, G + 3, Z1, AIR)
b.door(DOOR_X, G + 2, Z1, "oak", "north", hinge="right")
landscape()


def line_ceilings():
    """wood under the slate: a spruce trapdoor panel (top half) under every slate cell seen from the vault/loft."""
    cols = [(x, z) for x in range(X0 + 1, X1) for z in range(Z0 + 1, Z1)] +            [(x, z) for x in (8, 9, 10) for z in range(Z1, JETTY_Z)]
    for (x, z) in cols:
        for y in range(G + 13, G + 6, -1):
            above = b.get(x, y + 1, z)
            if (x, y, z) not in b and ("tuff" in above or "mossy_stone_brick" in above):
                if not any("glass_pane" in b.get(x + dx, y, z + dz) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    b.set(x, y, z, SP.trapdoor("north", "top"))
                break


line_ceilings()

b.entrance(DOOR_X, G + 1, 15)
b.room("living", 7, G + 2, 7)
b.room("kitchen", 11, G + 2, 7)
b.room("pantry", 8, G + 2, 3)
b.room("loft", 10, LOFT + 1, 7)
b.room("bed_nook", 9, LOFT + 1, 11)

def look(specs, out_dir="out/previews/01_cozy_starter_cottage/look"):
    """dev helper: close-ups in AUTHORED coordinates. spec 'x,y,z,radius,azimuth,elevation[,cut]'."""
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
    """dev helper: share of the first visible block per elevation cell (plants ignored), grouped like the critic."""
    groups = {
        "plaster": ("pale_oak_planks", "calcite", "mushroom_stem", "white_terracotta"),
        "roof": ("dark_oak_stairs", "dark_oak_slab", "dark_oak_planks", "spruce_stairs", "spruce_slab", "spruce_planks",
                 "stripped_dark_oak_log"),
        "timber": ("dark_oak_log", "stripped_dark_oak_log", "spruce_trapdoor", "dark_oak_trapdoor"),
        "pale_trim": ("pale_oak_trapdoor", "pale_oak_stairs", "pale_oak_slab"),
    }
    skip = ("grass", "fern", "flower", "daisy", "dandelion", "leaves", "vine", "bush", "tulip", "allium", "cornflower",
            "peony", "lilac", "petals", "carpet", "lantern", "chain", "fence", "wall", "azalea", "rose", "litter")
    house = {(x, y, z): s for (x, y, z), s in b.blocks.items() if -2 <= x <= 15 and -1 <= z <= 15 and y > G}
    for name, (axis, sign) in {"S": ("z", 1), "N": ("z", -1), "E": ("x", 1), "W": ("x", -1)}.items():
        first = {}
        for (x, y, z), s in house.items():
            bid = s.split("[")[0].replace("minecraft:", "")
            if any(k in bid for k in skip):
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
