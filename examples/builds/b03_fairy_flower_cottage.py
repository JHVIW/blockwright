"""b03 Fairy Flower Cottage -- "Blossom Bell" (round 2).

A round cottage (9-wide octagon-circle) under a bell-cast cherry roof, a small bay turret on the west flank with
its own bell, a leaning tuff chimney with a corbelled crown and real smoke on the north, a free-standing cherry tree
to the NE.  See docs/logs/03_fairy_flower_cottage.md and docs/critiques/03_round1.md.

Top view (x east, z south, main bell axis at 0,0; turret axis at -6,+2):

            z-8          . T T T .        T  cherry tree canopy (2 air clear of the roof everywhere)
            z-6        C C  .  T          C  chimney: 3x2 footing -> 2x2 stack -> leans north -> 3x3 crown
            z-4    # # # # #
              -3  #         #
                #             #
      b b b     #   round room  #  stair along the east wall, loft over the north half
    b       .   .   loft N      #
    b seat  .   .               #
      b b b   #             #
              +3  #  [door]  #
            z+4    # ( D ) #             recessed cherry door in a round-headed niche, azalea arch, step

Roof (both bells): octagonal offset rings k = max(|dx|, |dz|, |dx|+|dz|-c), every ring exactly one cell wide, so the
N/E/S/W facets are straight runs and the diagonals clean 45-degree staircases (8 hip lines).  Main profile: dark lip
slab @8, cherry top slab @8 (1 out), cherry slab @9 on the wall line (two-step 26 deg flare), 45 deg stairs @10,
63 deg @12 and @14, one cap block @15, dark post + copper lantern.

Run:  python -m blockwright build examples/builds/b03_fairy_flower_cottage.py [--quick] [--no-render] [--no-qa] [--views=a,b]
"""
import math
import sys

from blockwright import *

G = 0
b = Build("03_fairy_flower_cottage", "Fairy Flower Cottage", ground=G,
          description="Round fairy cottage under a bell-cast cherry roof, bay turret, loft, petal garden.")
cherry, doak, birch, spruce = wood("cherry"), wood("dark_oak"), wood("birch"), wood("spruce")

DIRS = {"north": (0, -1), "east": (1, 0), "south": (0, 1), "west": (-1, 0)}      # clockwise order
CW = list(DIRS)
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


def n4(x, z):
    return [(x + dx, z + dz) for dx, dz in DIRS.values()]


def octk(c, cut):
    """octagonal offset-ring metric around axis c: ring k is exactly one cell wide."""
    return lambda x, z: max(abs(x - c[0]), abs(z - c[1]), abs(x - c[0]) + abs(z - c[1]) - cut)


# ------------------------------------------------------------------------------------------------------------
# plan: main octagon (ring 4 = the 9-wide round plan) + turret octagon on the west flank
# ------------------------------------------------------------------------------------------------------------
MAIN_C, TUR_C = (0, 0), (-6, 2)
KM, KT = octk(MAIN_C, 2), octk(TUR_C, 1)
main = {(x, z) for x in range(-6, 7) for z in range(-6, 7) if KM(x, z) <= 4}
tur = {(x, z) for x in range(-10, -1) for z in range(-3, 7) if KT(x, z) <= 2}
plan = main | tur
wall = {c for c in plan if any(n not in plan for n in n4(*c))}
inside = plan - wall


# ------------------------------------------------------------------------------------------------------------
# bell roofs.  Each ring is a 4-connected loop except at the diagonal staircases, where a hidden "helper" stair
# sits in the inner cell of every diagonal joint at the ring's own level; blockwright.resolve then turns the joints into
# outer/inner/outer corner triplets (one smooth hip line).  Heights are in half blocks per ring.
# ------------------------------------------------------------------------------------------------------------
def cone_rings(c, kmax, kf):
    cells = {}
    for x in range(c[0] - kmax - 1, c[0] + kmax + 2):
        for z in range(c[1] - kmax - 1, c[1] + kmax + 2):
            k = kf(x, z)
            if k <= kmax:
                cells[(x, z)] = k
    helpers = {}
    for k in range(kmax, 1, -1):
        for (x, z) in sorted(p for p, v in cells.items() if v == k):
            for dx in (-1, 1):
                for dz in (-1, 1):
                    if cells.get((x + dx, z + dz)) != k:
                        continue
                    a, bb = (x + dx, z), (x, z + dz)
                    if cells.get(a) == k or cells.get(bb) == k:
                        continue
                    inner = min((a, bb), key=lambda p: (kf(*p), math.hypot(p[0] - c[0], p[1] - c[1])))
                    if cells.get(inner, 99) < k:
                        helpers.setdefault(k, set()).add(inner)
    return cells, helpers


def cone_facing(cells, x, z, k=None):
    """straight sides face inward; convex corners take the earlier, concave corners the later of their two
    directions (clockwise), so resolve pairs them into outer/inner corners."""
    k = cells[(x, z)] if k is None else k
    out = [d for d in CW if cells.get((x + DIRS[d][0], z + DIRS[d][1]), 99) > k]
    if len(out) == 1:
        return OPP[out[0]]
    if len(out) == 2:
        a, c2 = out
        if OPP[a] == c2:
            return None
        i, j = CW.index(a), CW.index(c2)
        return OPP[a if (j - i) % 4 == 1 else c2]
    if len(out) == 0:
        diag = []
        for i, d in enumerate(CW):
            e = CW[(i + 1) % 4]
            dx, dz = DIRS[d][0] + DIRS[e][0], DIRS[d][1] + DIRS[e][1]
            if cells.get((x + dx, z + dz), 99) > k:
                diag.append(e)
        if len(diag) == 1:
            return OPP[diag[0]]
    return None


def make_cone(c, kmax, kf, profile):
    cells, helpers = cone_rings(c, kmax, kf)
    out, hel = {}, {}
    for (x, z), k in cells.items():
        s, kind = profile[k]
        f = cone_facing(cells, x, z) if kind == "stair" else None
        if kind == "stair" and f is None:
            kind = "slab"
        out[(x, z)] = (s, kind, f, k)
    for k, ps in helpers.items():
        s, kind = profile[k]
        if kind != "stair":
            continue
        for (x, z) in ps:
            f = cone_facing(cells, x, z, k)
            if f is not None:
                hel[(x, z)] = ((s - 1) // 2, f, k)
    return out, hel


# Main (critique option A): R6 dark lip slab @8, R5 cherry top slab @8, R4 cherry slab @9 on the wall line,
# R3 stairs @10 on a top slab, R2 @12 and R1 @14 on planks (63 deg), R0 one cap block @15.
MAIN_PROFILE = {6: (17, "slab"), 5: (18, "slab"), 4: (19, "slab"), 3: (21, "stair"), 2: (25, "stair"),
                1: (29, "stair"), 0: (31, "spire")}
# Turret: overhang 1, eave at the main eave height, a steep (68 deg) crown so its needle reads in elev_w.  R2 is its wall line, so it is a full block (a top slab would
# leave a half-block gap over the wall top); it looks identical from outside.
TUR_PROFILE = {3: (17, "slab"), 2: (19, "stair"), 1: (23, "stair"), 0: (24, "spire")}   # round 3 (critique r2)
LIPK = {MAIN_C: 6, TUR_C: 3}

CONE_MAIN, HEL_MAIN = make_cone(MAIN_C, 6, KM, MAIN_PROFILE)
CONE_TUR, HEL_TUR = make_cone(TUR_C, 3, KT, TUR_PROFILE)
ROOF = {}
for p in set(CONE_MAIN) | set(CONE_TUR):
    a, t = CONE_MAIN.get(p), CONE_TUR.get(p)
    if t is None or (a is not None and a[0] >= t[0]):
        ROOF[p] = a + (MAIN_C,)
    else:
        ROOF[p] = t + (TUR_C,)


def roof_blocks():
    """-> {(x,y,z): (role, state)}; role: top | fill | helper | spire."""
    out = {}
    for (x, z), (s, kind, f, k, owner) in ROOF.items():
        w = doak if k == LIPK[owner] else cherry
        if kind == "spire":
            lvl = (s - 1) // 2
            out[(x, lvl, z)] = ("spire", cherry.planks)
        elif s % 2 == 1:
            lvl = (s - 1) // 2
            out[(x, lvl, z)] = ("top", w.stairs(f) if kind == "stair" else w.slab("bottom"))
        else:
            lvl = s // 2 - 1
            out[(x, lvl, z)] = ("top", w.slab("top") if kind == "slab" else w.planks)
        covers = []
        for d, n in zip(CW, n4(x, z)):
            if n not in ROOF:
                covers.append(s - 1)
                continue
            sn, nk, nf = ROOF[n][0], ROOF[n][1], ROOF[n][2]
            if sn >= s:
                continue
            covers.append(sn + 1 if (nk == "stair" and nf == OPP[d]) else sn)
        bp = min(covers) if covers else s - 1
        for yy in range(bp // 2, lvl):
            out[(x, yy, z)] = ("fill", cherry.slab("top") if (bp % 2 == 1 and yy == bp // 2) else cherry.planks)
    for hel, owner in ((HEL_MAIN, MAIN_C), (HEL_TUR, TUR_C)):
        for (x, z), (lvl, f, k) in hel.items():
            if ROOF.get((x, z), (0, 0, 0, 0, None))[4] == owner:
                out[(x, lvl, z)] = ("helper", cherry.stairs(f))
    # stair-on-stair risers (round 3, variant VB): a plank riser directly under a top stair whose outer side is
    # open becomes a stair with the same facing, so every 63-degree course shows a half-block shingle edge instead
    # of a 1.5-tall flat plank face.  Its empty upper quarters are backed by planks in the inner neighbours.
    tops = {(x, z): (y, st) for (x, y, z), (role, st) in out.items() if role == "top" and "_stairs" in st}
    for (x, y, z), (role, st) in list(out.items()):
        if role != "fill" or st != cherry.planks:
            continue
        t = tops.get((x, z))
        if not t or t[0] != y + 1:
            continue
        f = prop(t[1], "facing")
        outs = [(x - DIRS[f][0], z - DIRS[f][1])]
        for (dx, dz) in DIRS.values():
            q = (x + dx, z + dz)
            if q not in outs and q in ROOF and ROOF[q][0] < ROOF[(x, z)][0]:
                outs.append(q)
        if not [q for q in outs if (q[0], y, q[1]) not in out]:
            continue
        out[(x, y, z)] = ("riser", cherry.stairs(f))
        for (dx, dz) in DIRS.values():
            q = (x + dx, z + dz)
            if q in ROOF and ROOF[q][0] >= ROOF[(x, z)][0] and (q[0], y, q[1]) not in out:
                out[(q[0], y, q[1])] = ("fill", cherry.planks)
    return out


RB = roof_blocks()
for _c in (MAIN_C, TUR_C):                                     # apex column solid between the riser back-fill and cap
    _ys = sorted(y for (x, y, z) in RB if (x, z) == _c)
    for _y in range(_ys[0], _ys[-1]):
        RB.setdefault((_c[0], _y, _c[1]), ("fill", cherry.planks))
ROOF_BOTTOM = {}
for (_x, _y, _z) in RB:
    ROOF_BOTTOM[(_x, _z)] = min(_y, ROOF_BOTTOM.get((_x, _z), 99))


# ------------------------------------------------------------------------------------------------------------
# materials
# ------------------------------------------------------------------------------------------------------------
def plinth_stone(x, y, z):
    """tuff / mossy cobble / cobbled deepslate / mossy stone bricks, mossy at the bottom (patch noise)."""
    n = value3(x, y, z, 31, 2.5)
    if y <= 0:
        return "mossy_cobblestone" if n < 0.55 else ("moss_block" if n < 0.7 else "cobbled_deepslate")
    if n < 0.30:
        return "mossy_cobblestone"
    if n < 0.62:
        return "tuff"
    if n < 0.80:
        return "mossy_stone_bricks"
    return "cobbled_deepslate"


def plaster(x, y, z):
    """infill gradient (guide 2.2): mushroom stem low, stripped birch in the middle, pale oak planks high, with
    soft wobbling band edges (value noise), so it is never one material per course."""
    band = y + (value3(x * 0.9, y * 0.5, z * 0.9, 17, 2.6) - 0.5) * 1.8
    if band < 3.7:
        return "mushroom_stem"
    if band < 5.3:
        return birch.stripped_log("y")
    return "pale_oak_planks"


def chimney_stone(x, y, z):
    """gradient up the stack: mossy cobble at the foot, tuff / cobbled deepslate in the middle, tuff bricks with
    a few mossy stone bricks at the top."""
    n = value3(x, y, z, 53, 2.0)
    if y <= 1:
        return "mossy_cobblestone" if n < 0.6 else "cobbled_deepslate"
    if y <= 8:
        return "tuff" if n < 0.55 else ("cobbled_deepslate" if n < 0.85 else "mossy_cobblestone")
    return "mossy_stone_bricks" if hash01(x, y, z, 54) < 0.13 else "tuff_bricks"


def beam_axis(x, z, c=MAIN_C):
    return "x" if abs(z - c[1]) >= abs(x - c[0]) else "z"


# ------------------------------------------------------------------------------------------------------------
# 1. roof (placed first; later steps carve into it)
# ------------------------------------------------------------------------------------------------------------
for (x, y, z), (role, st) in RB.items():
    b.set(x, y, z, st)

# finials: one cap block per bell (placed by the profile), then a thin needle
cs = (CONE_MAIN[MAIN_C][0] - 1) // 2                          # cap y15
b.set(0, cs + 1, 0, doak.fence)
b.set(0, cs + 2, 0, lantern(kind="waxed_copper"))
ts = (CONE_TUR[TUR_C][0] - 1) // 2                            # cap y11
b.set(TUR_C[0], ts + 1, TUR_C[1], cherry.fence)
b.set(TUR_C[0], ts + 2, TUR_C[1], "end_rod")

# ------------------------------------------------------------------------------------------------------------
# 2. foundation, plinth, floor
# ------------------------------------------------------------------------------------------------------------
for (x, z) in plan:
    if (x, z) in wall:
        b.set(x, -1, z, "cobbled_deepslate")
        b.set(x, 0, z, plinth_stone(x, 0, z))
        b.set(x, 1, z, plinth_stone(x, 1, z))
    else:
        ring_cell = any(n in wall for n in n4(x, z))
        b.set(x, 0, z, "dirt")
        b.set(x, 1, z, doak.planks if ring_cell else cherry.planks)

# ------------------------------------------------------------------------------------------------------------
# 3. walls: sill beam y2, infill y3..y6, top plate y7, wall plate y8 under the eave; 7 dark posts on the
#    octagon corners of the main body (the 8th corner opens into the turret); the turret stone-based
# ------------------------------------------------------------------------------------------------------------
for (x, z) in wall:                                            # a top slab on a wall line would leave a half-
    y = ROOF_BOTTOM.get((x, z))                                # block gap over the wall top: make it a block
    if y is not None and "type=top" in b.get(x, y, z):
        b.set(x, y, z, doak.planks if "dark_oak" in b.get(x, y, z) else cherry.planks)
MAIN_POSTS = {(2, 4), (-2, 4), (2, -4), (-2, -4), (4, 2), (4, -2), (-4, -2)}
TUR_POSTS = {(-7, 0), (-7, 4)}
for (x, z) in wall:
    top = ROOF_BOTTOM.get((x, z), 9) - 1
    is_tur = (x, z) in tur and (x, z) not in main
    for y in range(2, top + 1):
        if (x, z) in MAIN_POSTS or (x, z) in TUR_POSTS:
            st = doak.log("y") if y <= 7 else doak.planks
            if is_tur and y == 2:
                st = plinth_stone(x, y, z)
        elif is_tur and y == 2:
            st = plinth_stone(x, y, z)
        elif y == 2 or y == 7:
            st = doak.stripped_log(beam_axis(x, z, TUR_C if is_tur else MAIN_C))
        elif y >= 8:
            st = doak.planks
        else:
            st = plaster(x, y, z)
        b.set(x, y, z, st)

# arched opening main room -> turret nook (x=-4, z 0..2): round head, lintel, partition above
for z in (0, 1, 2):
    b.set(-4, 5, z, doak.stripped_log("z"))
    b.set(-4, 6, z, plaster(-4, 6, z))
    b.set(-4, 7, z, doak.stripped_log("z"))
    b.set(-4, 8, z, doak.planks)
b.set(-4, 4, 0, doak.stairs("north", "top"))
b.set(-4, 4, 2, doak.stairs("south", "top"))

# ------------------------------------------------------------------------------------------------------------
# 4. entrance (south): round-headed 3-wide niche at L0, cherry door recessed at L-1
# ------------------------------------------------------------------------------------------------------------
for x in (-1, 0, 1):
    for y in (2, 3, 4, 5):
        b.remove(x, y, 4)
    b.set(x, 1, 4, doak.planks)                                # niche floor
    b.set(x, 6, 4, doak.stripped_log("x"))                     # lintel
b.set(-1, 5, 4, doak.stairs("west", "top"))                   # round head
b.set(1, 5, 4, doak.stairs("east", "top"))
for x in (-1, 1):                                              # niche cheeks (L-1)
    for y in (2, 3, 4):
        b.set(x, y, 3, plaster(x, y, 3))
    b.set(x, 5, 3, doak.planks)
b.set(0, 4, 3, pane())                                         # transom over the door
b.set(0, 5, 3, doak.planks)
b.door(0, 2, 3, "cherry", "north", hinge="right")
b.set(0, 1, 5, stairs("mossy_cobblestone", "north"))          # step
b.entrance(0, 1, 6)
b.set(0, 5, 4, lantern(hanging=True, kind="waxed_copper"))
b.set(-1, 2, 4, potted("allium"))                             # pots flanking the door inside the niche
b.set(1, 2, 4, potted("flowering_azalea_bush"))

# ------------------------------------------------------------------------------------------------------------
# 5. chimney (north): 3x2 footing with tuff shoulders -> 2x2 stack -> string course where it leaves the roof
#    -> leans one north on corbels -> corbelled 3x3 crown enclosing the campfire, slab rim, open sky above.
#    The hearth campfire sits in the wall below (glow and crackle; the smoke source is the crown fire).
# ------------------------------------------------------------------------------------------------------------
for (x, y, z) in list(b.blocks):                               # clear roof where the stack stands
    if z in (-5, -6) and x in (0, 1) and y >= 5:
        b.remove(x, y, z)
for y in range(-1, 5):                                         # footing 3x2
    for x in (-1, 0, 1):
        for z in (-5, -6):
            b.set(x, y, z, chimney_stone(x, y, z))
for z in (-5, -6):                                             # west shoulder steps in to the 2x2 stack
    b.set(-1, 5, z, stairs("tuff", "east"))
for y in range(5, 10):
    for x in (0, 1):
        for z in (-5, -6):
            b.set(x, y, z, "polished_tuff" if y == 9 else chimney_stone(x, y, z))
for x in (0, 1):                                               # string course on the N face
    b.set(x, 9, -7, stairs("tuff_bricks", "south", "top"))
for x in (0, 1):                                               # one lean course north + sloped S shoulder
    for z in (-6, -7):
        b.set(x, 10, z, "tuff_bricks" if (x + z) % 3 else "mossy_stone_bricks")
    b.set(x, 10, -5, stairs("tuff_bricks", "north"))
CROWN = [(x, z) for x in (-1, 0, 1) for z in (-8, -7, -6) if (x, z) != (0, -7)]   # ring round the flue (0,-7)
for (x, z) in CROWN:                                           # corbels under the overhanging crown cells
    if (x, 10, z) not in b:
        b.set(x, 10, z, stairs("tuff_bricks", "east" if x == -1 else "south", "top"))
for (x, z) in CROWN:                                           # enclosing ring, then the rim; two full corners
    b.set(x, 11, z, "mossy_stone_bricks" if (x, z) == (1, -6) else "tuff_bricks")
    b.set(x, 12, z, "tuff_bricks" if (x, z) in ((-1, -6), (1, -8)) else slab("tuff_brick", "bottom"))
b.set(0, 11, -7, campfire("south"))                            # enclosed, 1 below the rim, open sky above
b.set(-1, 13, -6, potted("allium"))                            # chimney pot and moss tuft stand flush
b.set(1, 13, -8, "moss_carpet")
for y in (5, 6, 7):                                            # ivy on the shady north face
    b.set(1, y, -7, vine())
for y in (2, 3, 4):
    b.set(-1, y, -7, vine())
b.set(0, 2, -4, campfire("south"))                             # hearth firebox in the north wall cell
b.remove(0, 3, -4)
b.set(0, 4, -4, stairs("tuff", "south", "top"))

# ------------------------------------------------------------------------------------------------------------
# 6. loft (floor y6 over the north half) + stair along the east wall (first step turns east)
# ------------------------------------------------------------------------------------------------------------
LOFT = {(x, z) for (x, z) in inside if z <= -1 and (x, z) in main}
STAIR = [(3, 2, 2, "east"), (3, 1, 3, "north"), (3, 0, 4, "north"), (3, -1, 5, "north")]
for (x, z) in LOFT:
    if (x, z) == (3, -1):
        continue
    b.set(x, 6, z, doak.stripped_log("x") if z == -1 else doak.planks)
for (x, z, y, f) in STAIR:
    b.set(x, y, z, cherry.stairs(f))

# ------------------------------------------------------------------------------------------------------------
# 7. facade details
# ------------------------------------------------------------------------------------------------------------
# knee brace + lip bracket pairs: inverted dark oak stairs from the wall plate out to the dark lip, at every
# second post (a shadow line and a visible structure under the 2-deep eave)
for (x, z, f) in ((5, 2, "west"), (6, 2, "west"), (2, -5, "south"), (2, -6, "south"), (-2, 5, "north"),
                  (-2, 6, "north"), (-5, -2, "east"), (-6, -2, "east")):
    b.set(x, 7, z, doak.stairs(f, "top"))

# south: round trellis arch of flowering azalea on cherry posts in front of the door niche
for x in (-2, 2):
    b.fill(x, 1, 5, x, 5, 5, cherry.fence)
    b.set(x, 6, 5, leaves("flowering_azalea"))                 # shoulders
for x in (-1, 0, 1):
    b.set(x, 7, 5, leaves("flowering_azalea") if x else leaves("azalea"))   # crown

# eyebrow windows in the flare (glass on the wall line, slab lid above, the fill behind opened):
#   south 3 wide over the door (double-height room), east 2 wide (stair top), north 2 wide (loft bed nook)
EYEBROWS = {"south": ([(-1, 4), (0, 4), (1, 4)], (0, -1)), "east": ([(4, -1), (4, 0)], (-1, 0)),
            "north": ([(-2, -4), (-1, -4)], (0, 1))}
KEEP_FILL = {(-2, -3)}                       # next to the NW diagonal wall: opening it would leak past that slab
for name, (cells, (ix, iz)) in EYEBROWS.items():
    for i, (x, z) in enumerate(cells):
        b.set(x, 9, z, pane())
        if (x + ix, z + iz) not in KEEP_FILL:
            b.remove(x + ix, 9, z + iz)
        centre = len(cells) == 3 and i == 1
        b.set(x, 10, z, cherry.stairs("north") if centre else cherry.slab("bottom"))

# east: shuttered stair window (cherry lattice shutters at L+1, hood and sill, a pot)
for y in (4, 5):
    b.set(4, y, 0, pane())
    b.set(5, y, -1, cherry.trapdoor("east", "bottom" if y == 4 else "top", open=True))
    b.set(5, y, 1, cherry.trapdoor("east", "bottom" if y == 4 else "top", open=True))
b.set(5, 6, 0, doak.stairs("west", "top"))
b.set(5, 3, 0, doak.trapdoor("east", "top"))
b.set(5, 4, 0, potted("allium"))

# SE facet: small porthole that balances the south front (one dark sill)
b.set(3, 4, 3, pane())
b.set(3, 3, 4, doak.trapdoor("south", "top"))                  # one dark sill, no floating hoods

# NE facet: kitchen window over the sink corner, sill plates and a pot of fern
b.set(3, 3, -3, pane())
b.set(3, 4, -3, pane())
b.set(3, 2, -4, doak.trapdoor("north", "top"))
b.set(4, 2, -3, doak.trapdoor("east", "top"))
b.set(3, 3, -4, potted("fern"))

# turret west: plus-shaped round window: dark round stair frame at L0, glass recessed at L-1, dark backers
for (z, y) in ((2, 4), (2, 5), (2, 6), (1, 5), (3, 5)):
    b.remove(-8, y, z)
    b.set(-7, y, z, pane())
b.set(-8, 4, 1, doak.stairs("north"))
b.set(-8, 4, 3, doak.stairs("south"))
b.set(-8, 6, 1, doak.stairs("north", "top"))
b.set(-8, 6, 3, doak.stairs("south", "top"))
for z in (1, 3):
    for y in (4, 6):
        b.set(-7, y, z, doak.planks)
for z in (1, 2, 3):                                            # flower box on brackets under the window
    b.set(-9, 3, z, "rooted_dirt" if z != 2 else "moss_block")
    b.set(-10, 3, z, cherry.trapdoor("west", open=True))
b.set(-9, 3, 0, cherry.trapdoor("north", open=True))
b.set(-9, 3, 4, cherry.trapdoor("south", open=True))
b.set(-9, 2, 1, doak.stairs("east", "top"))
b.set(-9, 2, 3, doak.stairs("east", "top"))
b.set(-9, 4, 1, "allium")
b.set(-9, 4, 2, state("pink_petals", flower_amount=4, facing="west"))
b.set(-9, 4, 3, "allium")

# turret south: small window with a single shutter, sill and a pot (the nook's second window)
b.set(-6, 4, 4, pane())
b.set(-6, 5, 4, pane())
b.set(-5, 4, 5, cherry.trapdoor("south", open=True))
b.set(-5, 5, 5, cherry.trapdoor("south", "top", open=True))
b.set(-6, 3, 5, doak.trapdoor("south", "top"))
b.set(-6, 4, 5, potted("pink_tulip"))

# turret bloom: a flowering azalea climber stepping up the SW post into the eave, spore blossom beside it
for (x, y, z) in ((-8, 1, 4), (-8, 2, 4), (-8, 3, 4), (-8, 4, 4), (-7, 5, 5), (-7, 6, 5), (-7, 7, 5)):
    b.set(x, y, z, leaves("flowering_azalea") if y % 3 else leaves("azalea"))
b.set(-6, 7, 5, "spore_blossom")

# glow berries: four strands of different lengths under the dark lip (cave vines need the lip's full underside)
for (x, z, n) in ((1, 6, 1), (5, 3, 4), (6, -1, 3), (-9, 3, 2)):
    assert b.get(x, 8, z).startswith("minecraft:dark_oak_slab"), (x, z)
    for i in range(n):
        b.set(x, 7 - i, z, state("cave_vines_plant", berries=True) if i < n - 1 else
              state("cave_vines", berries=True))

# NE living eave under the tree: moss swaps for flush top slabs on the 1-out ring (shape-safe: no stairs
# touch them), fallen petals and moss on top, flowering azalea spilling over the dark lip
for (x, z, top) in ((2, -5, "petals"), (3, -4, "moss_carpet"), (4, -3, "petals"), (5, -2, "petals"),
                    (-1, -5, "moss_carpet"), (-2, -5, "petals")):
    assert b.get(x, 8, z).startswith("minecraft:cherry_slab"), (x, z, b.get(x, 8, z))
    b.set(x, 8, z, "moss_block")
    b.set(x, 9, z, state("pink_petals", flower_amount=3, facing=CW[(x + z) % 4]) if top == "petals" else top)
for (x, y, z) in ((4, 8, -4), (3, 8, -5), (3, 7, -5), (5, 8, -3)):
    b.set(x, y, z, leaves("flowering_azalea"))

# ------------------------------------------------------------------------------------------------------------
# 8. the bell vault inside: a dark collar ring under the 5x5 ring and rafter feet on the hip lines
# ------------------------------------------------------------------------------------------------------------
for x in range(-2, 3):
    for z in range(-2, 3):
        if max(abs(x), abs(z)) == 2 and abs(x) + abs(z) < 4 and (x, 10, z) not in b:
            b.set(x, 10, z, doak.stripped_log("x" if abs(z) == 2 else "z"))
for (x, z, f) in ((2, 3, "south"), (-2, 3, "south"), (2, -3, "north"), (3, 2, "east"), (3, -2, "east"),
                  (-3, 2, "west"), (-3, -2, "west")):
    if b.get(x, 9, z).startswith("minecraft:cherry_slab"):
        b.set(x, 9, z, doak.stairs(f, "top"))

# ------------------------------------------------------------------------------------------------------------
# 9. interior, ground floor (stand y2)
# ------------------------------------------------------------------------------------------------------------
def chisel(facing, slots, seed):
    return state("chiseled_bookshelf", facing=facing,
                 **{f"slot_{i}_occupied": (hash3(i, seed, 0, 5) % 100) < slots for i in range(6)})


# hearth breast: tuff brick cheeks, dark oak mantel with candles and a potted azalea
for x in (-1, 1):
    b.set(x, 2, -3, "tuff_bricks")
    b.set(x, 3, -3, "chiseled_tuff_bricks" if x < 0 else "tuff_bricks")
    for y in (2, 3, 4, 5):
        b.set(x, y, -4, "tuff_bricks" if y < 5 else "polished_tuff")
for x in (-1, 0, 1):
    b.set(x, 4, -3, doak.stairs("north", "top"))
b.set(-1, 5, -3, candle("white", 3))
b.set(0, 5, -3, potted("flowering_azalea_bush"))
b.set(1, 5, -3, candle("pink", 2))
b.set(0, 5, -4, "polished_tuff")

# kitchen arc (NE): smoker, sink with tap under the new window, cherry shelves; storage under the stair
b.set(2, 2, -3, state("smoker", facing="south"))
b.set(3, 2, -2, state("water_cauldron", level=3))
b.set(3, 3, -2, state("tripwire_hook", facing="west"))
b.set(2, 4, -3, cherry.shelf("south"))
b.set(3, 4, -2, cherry.shelf("west"))
b.set(2, 3, -3, lantern())
b.set(3, 2, -1, barrel("west"))
b.set(3, 3, -1, barrel("up"))
b.set(3, 4, -1, potted("red_mushroom"))
b.set(3, 2, 0, barrel("west"))
b.set(3, 3, 0, cherry.trapdoor("west", "top"))
b.set(3, 2, 1, state("decorated_pot", facing="west"))

# reading corner (NW): bookshelf + chiseled shelf, pink armchair facing the fire
b.set(-2, 2, -3, "bookshelf")
b.set(-2, 3, -3, chisel("south", 60, 1))
b.set(-2, 4, -3, potted("fern"))
b.set(-3, 2, -2, chisel("east", 70, 2))
b.set(-3, 3, -2, "bookshelf")
b.set(-2, 2, -2, state("pink_wool_stairs", facing="west"))
b.set(-2, 2, -1, cherry.trapdoor("north", open=True))

# round table with a cloth, three stools
b.set(0, 2, 0, barrel("up"))
b.set(0, 3, 0, carpet("white"))
b.set(-1, 2, 0, cherry.stairs("west"))
b.set(1, 2, 0, cherry.stairs("east"))
b.set(0, 2, -1, cherry.stairs("north"))

# south corners: chest, pot stand
b.set(-3, 2, 2, chest("east"))
b.set(-2, 2, 3, barrel("up"))
b.set(-2, 3, 3, potted("allium"))
b.set(2, 2, 3, potted("azalea_bush"))

# round rug (5x5 minus corners): pink ring, white centre, never under furniture
for x in range(-2, 3):
    for z in range(-1, 4):
        dx, dz = abs(x), abs(z - 1)
        if dx == 2 and dz == 2:
            continue
        if (x, 2, z) not in b and (x, z) in inside and (x, 1, z) in b:
            b.set(x, 2, z, carpet("white" if dx + dz <= 1 else "pink"))

# chandelier from the bell's apex over the double-height room
for y in range(10, ROOF_BOTTOM[(0, 0)]):
    b.set(0, y, 0, chain())
b.set(0, 9, 0, lantern(hanging=True, kind="waxed_copper"))
for (dx, dz, f) in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
    b.set(dx, 9, dz, cherry.trapdoor(f, "top"))
    b.set(dx, 10, dz, candle("pink" if dx else "white", 1))

# turret nook: window seat with pink cushions under the plus window, side table, hanging lantern
for z in (1, 2, 3):
    b.set(-7, 2, z, state("pink_wool_slab", type="bottom"))
b.set(-5, 2, 1, potted("fern"))
b.set(-5, 2, 3, barrel("up"))
b.set(-5, 3, 3, candle("white", 2))
for y in range(7, ROOF_BOTTOM[TUR_C]):
    b.set(-6, y, 2, chain())
b.set(-6, 6, 2, lantern(hanging=True, kind="waxed_copper"))

# ------------------------------------------------------------------------------------------------------------
# 10. loft (stand y7): bed nook under the north skirt (lit by the north eyebrow), nightstand, chest, bookshelf,
#     a runner rug, lattice railing
# ------------------------------------------------------------------------------------------------------------
b.bed(-2, 7, -2, "pink", "north")
b.set(-1, 7, -3, chisel("south", 40, 3))
b.set(-1, 8, -3, lantern())
b.set(-3, 7, -2, chisel("east", 50, 4))
b.set(-3, 7, -1, barrel("east"))
b.set(-3, 8, -1, potted("allium"))
b.set(1, 7, -3, chest("south"))
b.set(2, 7, -3, barrel("south"))
b.set(2, 8, -3, candle("pink", 3))
b.set(0, 7, -3, cherry.shelf("south"))
for x in (-1, 0, 1):
    b.set(x, 7, -2, carpet("pink" if x else "white"))
for x in range(-3, 3):
    if (x, 7, -1) not in b:
        b.set(x, 7, -1, cherry.trapdoor("north", open=True))

# ------------------------------------------------------------------------------------------------------------
# 11. landscaping.  Everything at y0 is authored only where it is needed (soil under plants, paths, podzol,
#     pond); the rest stays natural terrain.  Rings: dense at the plinth, beds/props, then a scattered fade-out.
# ------------------------------------------------------------------------------------------------------------
FOOT = {(x, z) for (x, y, z) in b.blocks if y in (0, 1)}       # house + chimney cells at the ground
SITE_X, SITE_Z = (-12, 10), (-11, 11)                          # landscaping stays within ~23 x 23
ROOFTOP = {}
for (x, y, z) in b.blocks:                                     # highest house block per column (tree clearance)
    if y >= 2:
        ROOFTOP[(x, z)] = max(y, ROOFTOP.get((x, z), -99))


def free_ground(x, z):
    return (SITE_X[0] <= x <= SITE_X[1] and SITE_Z[0] <= z <= SITE_Z[1] and (x, z) not in FOOT
            and (x, 0, z) not in b and (x, 1, z) not in b)


def plant(x, z, st, soil="grass_block"):
    """a plant at y1 on authored soil at y0 (only on free ground)."""
    if not free_ground(x, z):
        return False
    b.set(x, 0, z, soil)
    b.set(x, 1, z, st)
    return True


def tall_plant(x, z, name, soil="grass_block"):
    if not free_ground(x, z) or (x, 2, z) in b:
        return False
    b.set(x, 0, z, soil)
    b.tall(x, 1, z, name)
    return True


def petals(x, z, n, seed=0):
    return state("pink_petals", flower_amount=max(1, min(4, n)), facing=CW[hash3(x, z, seed, 9) % 4])


# --- cherry tree (NE, free-standing), recipe T9 from critique round 2: a 2x2 flared base and 3 roots, a bark tube
#     trunk along an S-lean (a 2-wide band, so the lean reads as one diagonal), 4 limbs, a mushroom-cap umbrella
#     canopy with rim bulges and a weeping rim of drips; every leaf >= 2 air above the house
def walk(a, c):
    """6-connected integer path from cell a to cell c (largest remaining error first)."""
    out, (x, y, z) = [a], a
    while (x, y, z) != tuple(c):
        d = [c[0] - x, c[1] - y, c[2] - z]
        i = max(range(3), key=lambda k: (abs(d[k]), k == 1))
        step = 1 if d[i] > 0 else -1
        x, y, z = (x + step, y, z) if i == 0 else ((x, y + step, z) if i == 1 else (x, y, z + step))
        out.append((x, y, z))
    return out


def tube(pts, radii):
    """cells within the (tapering) radius of a float polyline + a guaranteed 6-connected core path."""
    cells = set()
    for (p, q), (ra, rb) in zip(zip(pts, pts[1:]), zip(radii, radii[1:])):
        lo = [math.floor(min(p[i], q[i]) - max(ra, rb)) - 1 for i in range(3)]
        hi = [math.ceil(max(p[i], q[i]) + max(ra, rb)) + 1 for i in range(3)]
        v = [q[i] - p[i] for i in range(3)]
        L2 = sum(c * c for c in v) or 1e-9
        for x in range(lo[0], hi[0] + 1):
            for y in range(lo[1], hi[1] + 1):
                for z in range(lo[2], hi[2] + 1):
                    w = [x - p[0], y - p[1], z - p[2]]
                    t = max(0.0, min(1.0, sum(w[k] * v[k] for k in range(3)) / L2))
                    c = [p[k] + v[k] * t for k in range(3)]
                    r = ra + (rb - ra) * t
                    if (x - c[0]) ** 2 + (y - c[1]) ** 2 + (z - c[2]) ** 2 <= r * r:
                        cells.add((x, y, z))
        cells.update(walk(tuple(round(c) for c in p), tuple(round(c) for c in q)))
    return cells


def lobe(c, rx, rz, ry_top, ry_bot, seed, rough):
    """domed ellipsoid (flatter underside) with a soft noisy edge."""
    cx, cy, cz = c
    out = set()
    for x in range(math.floor(cx - rx - 1), math.ceil(cx + rx + 2)):
        for z in range(math.floor(cz - rz - 1), math.ceil(cz + rz + 2)):
            for y in range(math.floor(cy - ry_bot - 1), math.ceil(cy + ry_top + 2)):
                dy = y - cy
                d = ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2 + (dy / (ry_top if dy >= 0 else ry_bot)) ** 2
                if d <= 1 + (value3(x * 1.3, y * 1.3, z * 1.3, seed, 1.6) - 0.5) * 2 * rough:
                    out.add((x, y, z))
    return out


def limb(points, tip=True):
    """a face-connected path of single-axis moves: sideways logs on runs, bark at elbows (used for the roots)."""
    for i, (x, y, z) in enumerate(points):
        if (x, y, z) in b:
            continue
        axes = set()
        for q in (points[i - 1] if i else None, points[i + 1] if i + 1 < len(points) else None):
            if q:
                d = [abs(q[0] - x), abs(q[1] - y), abs(q[2] - z)]
                axes.add("xyz"[d.index(1)])
        last = i == len(points) - 1
        b.set(x, y, z, cherry.wood("y") if (len(axes) != 1 or (tip and last)) else cherry.log(axes.pop()))


def tree_ok(x, y, z, leaf):
    if not (-12 <= x <= 10 and -11 <= z <= 11 and y <= 17) or (x, y, z) in b:
        return False
    if -2 <= x <= 2 and -9 <= z <= -5 and y >= 4:                # chimney crown and smoke column
        return False
    return not leaf or y >= ROOFTOP.get((x, z), -99) + 3


for (x, z) in ((7, -5), (8, -5), (7, -4), (8, -4)):            # 2x2 flared base
    for y in (1, 2):
        b.set(x, y, z, cherry.wood("y"))
limb([(8, 1, -4), (9, 1, -4), (9, 0, -4), (10, 0, -4)], tip=False)                # roots: 3, 2, 1 long
limb([(7, 1, -3), (7, 0, -3), (7, 0, -2)], tip=False)
b.set(8, 1, -6, cherry.wood("y"))
b.set(9, 1, -5, cherry.wood("y"))                              # east knuckle breaks the flat bark face
b.set(9, 2, -4, "moss_carpet")
for (x, z) in ((6, -5), (8, -3), (9, -6), (6, -4), (8, -6), (9, -3)):
    if free_ground(x, z):
        b.set(x, 0, z, "rooted_dirt" if (x + z) % 2 else "moss_block")

SPLIT = (6.9, 8.0, -6.9)
WOOD = tube([(7.5, 2.6, -4.5), (7.8, 4.4, -5.1), (7.5, 6.2, -6.0), SPLIT], [0.75, 0.66, 0.58, 0.52])
for pts in ([SPLIT, (5.6, 9.2, -6.6), (4.4, 10.2, -6.2)],      # W, under the cap rim toward the eave
            [SPLIT, (7.8, 9.4, -8.4), (8.6, 10.2, -9.4)],      # NE
            [SPLIT, (6.6, 9.6, -7.8), (6.3, 10.6, -8.2)],      # centre leader
            [(7.6, 5.4, -5.6), (8.6, 6.3, -5.0), (9.2, 6.8, -4.3)]):   # low E limb, ends below the eave line
    WOOD |= tube(pts, [0.5, 0.5, 0.5])
LEAF = lobe((6.6, 11.6, -7.6), 4.0, 3.5, 2.0, 0.6, 701, 0.22)  # main cap
LEAF |= lobe((3.9, 11.0, -6.4), 1.7, 1.6, 1.1, 0.6, 702, 0.2)   # W rim bulge, low over the eave
LEAF |= lobe((9.0, 12.0, -9.6), 1.5, 1.4, 1.0, 0.5, 703, 0.2)   # NE rim bulge
LEAF |= lobe((5.6, 13.4, -8.4), 1.6, 1.4, 0.8, 0.4, 704, 0.2)   # off-centre crown bump
for (x, y, z) in sorted(WOOD, key=lambda p: p[1]):
    if y >= 3 and tree_ok(x, y, z, False):
        b.set(x, y, z, cherry.wood("y"))
CANOPY = set()
for (x, y, z) in sorted(LEAF):
    if tree_ok(x, y, z, True):
        b.set(x, y, z, leaves("flowering_azalea") if hash01(x, y, z, 78) < 0.06 else leaves("cherry"))
        CANOPY.add((x, y, z))
for (x, y, z) in sorted(CANOPY):                               # weeping rim: drips only on the outer canopy
    if (x, y - 1, z) in b or hash01(x, y, z, 5) >= 0.38:
        continue
    if ((x - 6.6) / 4.0) ** 2 + ((z + 7.6) / 3.5) ** 2 < 0.45:
        continue
    n = 3 if hash01(x, y, z, 7) < 0.15 else (2 if hash01(x, y, z, 6) < 0.35 else 1)
    for i in range(1, n + 1):
        if not tree_ok(x, y - i, z, True):
            break
        b.set(x, y - i, z, leaves("cherry"))
if (9, 6, -4) not in b and (9, 7, -4) in b:
    b.set(9, 6, -4, lantern(hanging=True, kind="waxed_copper"))   # green-flame lantern under the east limb

# petal carpet under the canopy, fading out with distance from the trunk
for x in range(0, 12):
    for z in range(-12, 0):
        d = math.hypot(x - 6.8, (z + 6.2) * 1.1)
        if d > 5.3 or not free_ground(x, z):
            continue
        n = int(4.6 - d * 0.75 + value2(x, z, 81, 2.0) * 1.5)
        if n >= 1 and hash01(x, 0, z, 82) < 0.92:
            plant(x, z, petals(x, z, n, 1))
        elif hash01(x, 0, z, 83) < 0.3:
            plant(x, z, "short_grass")

# --- fairy ring (SE): 8 mushrooms on an imperfect circle, podzol only under each, grass and moss between
RING_C, RING_R = (6.5, 7.0), 2.5
for i in range(9):
    if i == 6:
        continue                                               # one gap
    a = i / 9 * 2 * math.pi + 0.25 * math.sin(i * 2.1)
    r = RING_R * (1 + 0.1 * math.sin(i * 1.7 + 0.5))
    x, z = round(RING_C[0] + r * math.cos(a)), round(RING_C[1] + r * math.sin(a))
    plant(x, z, "red_mushroom" if i % 3 else "brown_mushroom", "podzol")
for (x, z, st) in ((6, 7, "moss_carpet"), (7, 7, "short_grass"), (6, 6, "short_grass"), (5, 7, "fern"),
                   (7, 8, "moss_carpet")):
    plant(x, z, st, "moss_block" if st == "moss_carpet" else "grass_block")

# --- pond (SW): irregular, 1 deep at the edge and 2 in the middle, fully contained by authored blocks
POND_BLOBS = [((-7.0, 7.4), (2.3, 1.5)), ((-8.6, 8.7), (1.6, 1.3)), ((-5.6, 8.5), (1.3, 1.1))]


def in_pond(x, z, grow=0.0):
    return any(((x - cx) / (rx + grow)) ** 2 + ((z - cz) / (rz + grow)) ** 2 <= 1.0
               for (cx, cz), (rx, rz) in POND_BLOBS)


POND = {(x, z) for x in range(-12, -2) for z in range(5, 12) if in_pond(x, z) and (x, z) not in FOOT}
BANK = {(x, z) for x in range(-13, -1) for z in range(4, 13) if in_pond(x, z, 1.1) and (x, z) not in POND}
for (x, z) in POND:
    deep = in_pond(x, z, -0.9)
    b.set(x, 0, z, "water")
    if deep:
        b.set(x, -1, z, "water")
        b.set(x, -2, z, "clay")
    else:
        b.set(x, -1, z, "clay" if hash01(x, 0, z, 61) < 0.5 else "dirt")
    for (nx, nz) in n4(x, z):                                   # contain the deep part below
        if (nx, nz) not in POND or not in_pond(nx, nz, -0.9):
            if deep and (nx, -1, nz) not in b:
                b.set(nx, -1, nz, "dirt")
for (x, z) in BANK:
    if (x, z) in FOOT or (x, 0, z) in b:
        continue
    r = value2(x, z, 63, 1.7)
    b.set(x, 0, z, "mud" if r < 0.25 else ("moss_block" if r < 0.55 else "grass_block"))
    b.set(x, -1, z, "dirt")
for (x, z) in ((-9, 8), (-6, 8)):                               # lily pads
    if (x, z) in POND:
        b.set(x, 1, z, "lily_pad")
for (x, z) in ((-4, 10), (-10, 10)):                            # mossy boulders on the bank
    if (x, z) in BANK and (x, 1, z) not in b:
        b.set(x, 1, z, "mossy_cobblestone")
        b.set(x, 2, z, "moss_carpet")
for (x, z) in ((-9, 6), (-10, 7)):
    if (x, z) in BANK and any(n in POND for n in n4(x, z)) and (x, 1, z) not in b:
        b.set(x, 0, z, "grass_block")
        b.set(x, 1, z, "sugar_cane")
        b.set(x, 2, z, "sugar_cane")
for (x, z, plant_id) in ((-5, 7, "blue_orchid"), (-8, 10, "blue_orchid"), (-11, 9, "firefly_bush"),
                         (-4, 8, "firefly_bush"), (-7, 6, "short_grass"), (-6, 10, "fern")):
    if (x, z) in BANK and (x, 1, z) not in b:
        if b.get(x, 0, z).startswith("minecraft:mud"):
            b.set(x, 0, z, "grass_block")
        b.set(x, 1, z, plant_id)
for (x, z) in ((-5, 9), (-9, 9)):                               # small dripleaf standing in the shallows
    if (x, z) in POND and not in_pond(x, z, -0.9):
        b.set(x, -1, z, "clay")
        b.tall(x, 0, z, "small_dripleaf", facing="east", waterlogged=True)

# --- entrance path: worn dirt at the step, then stepping stones meandering +-1 to the gate, fading out
PATH = [(0, 6, "dirt_path"), (-1, 6, "coarse_dirt"), (1, 6, "rooted_dirt"), (0, 7, "polished_andesite"),
        (0, 8, "polished_andesite"), (1, 8, "polished_andesite"),            # one 2-cell stone
        (1, 9, "mossy_cobblestone"), (1, 10, "polished_andesite"), (0, 11, "coarse_dirt")]
for (x, z, st) in PATH:
    if free_ground(x, z):
        b.set(x, 0, z, st)
plant(1, 11, "moss_carpet", "moss_block")
b.set(2, 1, 9, stone("mossy_stone_brick").wall)                 # lamp post beside the path start
b.set(2, 2, 9, stone("mossy_stone_brick").wall)
b.set(2, 3, 9, lantern(kind="waxed_copper"))
b.set(2, 0, 9, "mossy_cobblestone")

# --- garden gate on the last stone: spruce picket runs, a mossy wall stub at the west end, a bush at the east
b.set(1, 1, 10, spruce.gate("south", open=True))
for x in (-1, 0, 2, 3, 4):
    b.set(x, 1, 10, spruce.fence)
    if (x, 0, 10) not in b:
        b.set(x, 0, 10, "grass_block")
b.set(-2, 1, 10, stone("mossy_cobblestone").wall)
b.set(-2, 2, 10, "moss_carpet")
if (-2, 0, 10) not in b:
    b.set(-2, 0, 10, "moss_block")
plant(3, 9, "short_grass")
plant(0, 9, "allium")


# --- beds along the plinth: drifts of 2 lead species + filler per side, 1-2 blocks deep around the walls
PATHCELLS = {(x, z) for x in (-1, 0, 1) for z in range(5, 12)}
for x in range(-11, 8):
    for z in range(-8, 9):
        dm, dt = math.hypot(x, z), math.hypot(x + 6, z - 2)
        near = (4.5 < dm <= 6.4 and dt > 2.4) or (2.4 < dt <= 4.0 and dm > 4.5)
        if not near or (x, z) in PATHCELLS or not free_ground(x, z) or in_pond(x, z, 1.3):
            continue
        a = math.degrees(math.atan2(z, x))                          # 90 = south, 0 = east, -90 = north
        drift = value2(x, z, 101, 2.2)
        if value2(x, z, 102, 1.6) < 0.3:
            continue                                               # breathing gaps
        if 35 < a < 150:                                           # south front: allium + petals
            st = "allium" if drift < 0.45 else petals(x, z, 2 + int(drift * 3), 5)
        elif -35 <= a <= 35:                                       # east: lilac drifts + allium
            if drift < 0.4 and tall_plant(x, z, "lilac"):
                continue
            st = "allium" if drift < 0.7 else "short_grass"
        elif -145 < a < -35:                                       # north, shady: ferns, moss, lilac
            if drift > 0.72 and tall_plant(x, z, "lilac"):
                continue
            st = "fern" if drift < 0.45 else ("moss_carpet" if drift < 0.6 else petals(x, z, 2, 6))
        else:                                                      # west / turret: petals + allium + azalea
            st = petals(x, z, 1 + int(drift * 4), 7) if drift < 0.55 else ("allium" if drift < 0.8 else "flowering_azalea")
        soil = "moss_block" if st in ("fern", "moss_carpet", "flowering_azalea") else "grass_block"
        plant(x, z, st, soil)


def bush(cx, cz, r, h, seed):
    """irregular azalea bush (guide 5.3): a lobed 1-high skirt, an off-centre 2-high core, a mossy base with
    carpet tufts and an azalea shrublet at the foot -- no two alike."""
    ox = 1 if hash01(cx, 0, cz, seed) < 0.5 else -1
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 2, cz + 3):
            d = math.hypot(x - cx, z - cz) + (value2(x, z, seed, 1.3) - 0.5) * 1.2
            if d > r or not free_ground(x, z):
                continue
            b.set(x, 0, z, "moss_block")
            b.set(x, 1, z, leaves("flowering_azalea") if hash01(x, 1, z, seed + 1) < 0.3 else leaves("azalea"))
            if h >= 2 and math.hypot(x - cx - ox * 0.6, z - cz) <= r - 0.9:
                b.set(x, 2, z, leaves("flowering_azalea") if hash01(x, 2, z, seed + 2) < 0.4 else leaves("azalea"))
    for (dx, dz) in ((2, 1), (-1, 2), (-2, -1), (1, -2)):
        x, z = cx + dx + ox, cz + dz
        if hash01(x, 0, z, seed + 3) < 0.55:
            plant(x, z, "moss_carpet", "moss_block")
    plant(cx - 2 * ox, cz + 1, "flowering_azalea", "moss_block")


bush(-6, -5, 1.9, 2, 11)
bush(-10, -1, 1.3, 1, 13)
bush(8, 2, 1.8, 2, 15)
bush(6, 10, 1.2, 1, 19)

# --- bench by the pond (sit and watch the lilies), dark oak with trapdoor arms
b.set(-3, 1, 8, doak.stairs("east"))
b.set(-3, 1, 9, doak.stairs("east"))
b.set(-3, 1, 7, doak.trapdoor("north", open=True))
b.set(-3, 1, 10, doak.trapdoor("south", open=True))
for z in (7, 8, 9, 10):
    if (-3, 0, z) not in b:
        b.set(-3, 0, z, "coarse_dirt" if z in (8, 9) else "grass_block")

# --- fade-out ring: scattered single flowers, grass tufts, coarse dirt specks
for x in range(-13, 11):
    for z in range(-12, 14):
        if not free_ground(x, z):
            continue
        d = min(math.hypot(x, z) - 4.5, math.hypot(x + 6, z - 2) - 2.4)
        if d < 1.5 or d > 5.0:
            continue
        r = hash01(x, 0, z, 91)
        fade = 1 - (d - 1.5) / 3.8
        if r < 0.10 * fade:
            plant(x, z, "allium" if hash01(x, 1, z, 92) < 0.4 else petals(x, z, 1 + hash3(x, 0, z, 3) % 2, 4))
        elif r < 0.22 * fade:
            plant(x, z, "short_grass")
        elif r < 0.26 * fade:
            b.set(x, 0, z, "coarse_dirt")

b.note("Concept: Direction A 'Blossom Bell' - round room under a bell-cast cherry roof, west bay turret with its own "
       "bell, leaning chimney with a corbelled smoking crown, free-standing cherry tree NE, loft bedroom in the bell.")
b.note("Round 2 (critique docs/critiques/03_round1.md): octagonal offset rings (uniform 1-cell rings and dark brim), "
       "two-step slab flare, plain plank risers, single cap + needle finials, turret moved to (-6,+2) with overhang 1 "
       "and the main eave height, eyebrows S/E/N, corbelled chimney crown, free-standing tree with 2 air clearance.")
b.note("Size: house incl. eaves ~16x14; landscaping ring 3-5 blocks around it (the user's 3-6 block rule) gives a "
       "~23x23 box against the brief guideline 15x17; all landscaping edges are organic.")
b.note("H12 odd spans: n/a (round plan, bells centred on single columns). Paste with Litematica replace = "
       "'with non-air' so paths, podzol and the pond replace the terrain.")

b.room("main", 0, 2, 1)
b.room("nook", -6, 2, 2)
b.room("kitchen", 2, 2, -2)
b.room("loft", -1, 7, -2)

if __name__ == "__main__":
    b.finish()
