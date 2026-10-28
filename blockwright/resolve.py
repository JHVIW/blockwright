"""Game-accurate post-processing of a build: make every state exactly what Minecraft 26.3 computes, so
pasted builds look right and Litematica's schematic verifier agrees with a hand-built copy.

Every rule is a port of the decompiled 26.3 source (``.work/mcsrc/common/net/minecraft/world/level/block``);
the citation is next to each function.  Neighbours outside the build are unknown and treated as air.

``resolve(blocks) -> (new_blocks, stats)``; ``blocks`` maps (x, y, z) -> canonical state (no air).
The input dict is not modified.  Passes repeat until nothing changes (max 4).

stats = {"changes": {rule: n_changed, ...}, "errors": [...], "warnings": [...], "removed": [(pos, state, why)],
         "passes": n}
"errors" are structural problems (unpaired door/bed/double-plant halves) -- strict validation fails on them.
"warnings" include removed vines, chest halves reset to single and non-convergence.

Rules: stairs shape, fence / pane+bars / wall sides (+ wall post), gate in_wall, leaves distance (+ persistent),
snowy, campfire signal_fire, mushroom faces toward the same block, shelf side_chain, chest type pairing (+ copper chest
oxidation unification), growing plants head/body (cave/weeping/twisting vines, kelp), pale_hanging_moss tip, vines,
door upper half sync.  tests/test_core_gamecheck.py checks every rule output is a fixpoint of the game's updateShape.
"""
from __future__ import annotations

from collections import deque

from . import registry as R

AIR = R.AIR
OFF = {"north": (0, 0, -1), "south": (0, 0, 1), "west": (-1, 0, 0), "east": (1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}
OPP = {"north": "south", "south": "north", "west": "east", "east": "west", "up": "down", "down": "up"}
CW = {"north": "east", "east": "south", "south": "west", "west": "north"}
CCW = {v: k for k, v in CW.items()}
AXIS = {"north": "z", "south": "z", "east": "x", "west": "x", "up": "y", "down": "y"}
HORIZ = ("north", "east", "south", "west")
EPS_LO, EPS_HI = 1.0e-7, 0.9999999   # VoxelShape.calculateFace -> findIndex(axis, 1e-7 | 0.9999999)


def _add(p, d):
    o = OFF[d]
    return (p[0] + o[0], p[1] + o[1], p[2] + o[2])


# ------------------------------------------------------------------------------------ cached predicates
_kind_cache: dict = {}


def _kind(s: str) -> str:
    """Classify a state once: which rule family (if any) it belongs to."""
    k = _kind_cache.get(s)
    if k is None:
        chain = R.class_chain(s)
        if "StairBlock" in chain:
            k = "stairs"
        elif "FenceGateBlock" in chain:
            k = "gate"
        elif "FenceBlock" in chain:
            k = "fence"
        elif "IronBarsBlock" in chain:
            k = "bars"
        elif "WallBlock" in chain:
            k = "wall"
        elif "LeavesBlock" in chain:
            k = "leaves"
        elif "SnowyBlock" in chain:
            k = "snowy"
        elif "HugeMushroomBlock" in chain:
            k = "mushroom"
        elif "CampfireBlock" in chain:
            k = "campfire"
        elif "VineBlock" in chain:
            k = "vine"
        elif "ShelfBlock" in chain:
            k = "shelf"
        elif "DoorBlock" in chain:
            k = "door"
        elif "AbstractBedBlock" in chain:
            k = "bed"
        elif "DoublePlantBlock" in chain:
            k = "double_plant"
        elif "ChestBlock" in chain and "type" in R.info(R.block_id(s)).properties:
            k = "chest"
        elif R.block_id(s) in _GROWING_PLANTS:
            k = "growing_plant"
        elif "HangingMossBlock" in chain:
            k = "hanging_moss"
        else:
            k = ""
        _kind_cache[s] = k
    return k


# GrowingPlantHeadBlock / GrowingPlantBodyBlock pairs (KelpBlock, CaveVinesBlock, WeepingVinesBlock, TwistingVinesBlock
# and their *PlantBlock bodies: super(properties, Direction.UP|DOWN, ...)) -> (head, body, growth direction)
_GROWING = (("minecraft:kelp", "minecraft:kelp_plant", "up"),
            ("minecraft:cave_vines", "minecraft:cave_vines_plant", "down"),
            ("minecraft:weeping_vines", "minecraft:weeping_vines_plant", "down"),
            ("minecraft:twisting_vines", "minecraft:twisting_vines_plant", "up"))
_GROWING_PLANTS = {b: g for g in _GROWING for b in g[:2]}


def _bid(s):
    return R._split(s)[0]


def _p(s, name):
    for k, v in R._split(s)[1]:
        if k == name:
            return v
    return None


def _is_exception_for_connection(s) -> bool:
    """Block.isExceptionForConnection (Block.java)."""
    b = _bid(s)
    return (R.is_a(s, "LeavesBlock") or b in ("minecraft:barrier", "minecraft:carved_pumpkin", "minecraft:jack_o_lantern",
                                               "minecraft:melon", "minecraft:pumpkin")
            or R.has_tag(b, "minecraft:shulker_boxes"))


def _sturdy(s, face) -> bool:
    return s is not None and R.sturdy(s, face)


def _face_rects(boxes, face):
    """2D rectangles of VoxelShape.getFaceShape(face) (cells containing the boundary coordinate)."""
    out = []
    for (x1, y1, z1, x2, y2, z2) in boxes:
        if face == "down" and y1 <= EPS_LO < y2:
            out.append((x1, z1, x2, z2))
        elif face == "up" and y1 <= EPS_HI < y2:
            out.append((x1, z1, x2, z2))
        elif face == "north" and z1 <= EPS_LO < z2:
            out.append((x1, y1, x2, y2))
        elif face == "south" and z1 <= EPS_HI < z2:
            out.append((x1, y1, x2, y2))
        elif face == "west" and x1 <= EPS_LO < x2:
            out.append((z1, y1, z2, y2))
        elif face == "east" and x1 <= EPS_HI < x2:
            out.append((z1, y1, z2, y2))
    return out


def _covers(rects, target, eps=1e-9) -> bool:
    """True if ``target`` (a1,b1,a2,b2) minus the union of ``rects`` is empty (Shapes.joinIsNotEmpty ONLY_FIRST == false)."""
    ta1, tb1, ta2, tb2 = target
    xs = sorted({ta1, ta2} | {v for r in rects for v in (r[0], r[2]) if ta1 < v < ta2})
    zs = sorted({tb1, tb2} | {v for r in rects for v in (r[1], r[3]) if tb1 < v < tb2})
    for i in range(len(xs) - 1):
        cx = (xs[i] + xs[i + 1]) / 2
        for j in range(len(zs) - 1):
            cz = (zs[j] + zs[j + 1]) / 2
            if not any(r[0] - eps <= cx <= r[2] + eps and r[1] - eps <= cz <= r[3] + eps for r in rects):
                return False
    return True


_face_full_cache: dict = {}


def _collision_face_full(s, face) -> bool:
    """Block.isFaceFull(state.getCollisionShape(), face)."""
    if s is None:
        return False
    key = (s, face)
    r = _face_full_cache.get(key)
    if r is None:
        r = _covers(_face_rects(R.collision_boxes(s), face), (0.0, 0.0, 1.0, 1.0))
        _face_full_cache[key] = r
    return r


def _can_attach_to(nb, direction_towards_nb) -> bool:
    """MultifaceBlock.canAttachTo: isFaceFull(support shape) || isFaceFull(collision shape) on the facing side."""
    face = OPP[direction_towards_nb]
    return _sturdy(nb, face) or _collision_face_full(nb, face)


def _gate_connects_to_direction(gate, direction) -> bool:
    """FenceGateBlock.connectsToDirection: facing axis == direction.getClockWise() axis."""
    return AXIS[_p(gate, "facing")] == AXIS[CW[direction]]


# ------------------------------------------------------------------------------------------------ rules
def _stairs(W, p, s):
    """StairBlock.getStairsShape (StairBlock.java)."""
    facing, half = _p(s, "facing"), _p(s, "half")

    def is_stairs(t):
        return t is not None and _kind(t) == "stairs"

    def can_take_shape(neighbour_dir):
        n = W.get(_add(p, neighbour_dir))
        return not is_stairs(n) or _p(n, "facing") != facing or _p(n, "half") != half

    behind = W.get(_add(p, facing))
    if is_stairs(behind) and half == _p(behind, "half"):
        bf = _p(behind, "facing")
        if AXIS[bf] != AXIS[facing] and can_take_shape(OPP[bf]):
            return "outer_left" if bf == CCW[facing] else "outer_right"
    front = W.get(_add(p, OPP[facing]))
    if is_stairs(front) and half == _p(front, "half"):
        ff = _p(front, "facing")
        if AXIS[ff] != AXIS[facing] and can_take_shape(ff):
            return "inner_left" if ff == CCW[facing] else "inner_right"
    return "straight"


def _fence_connects(self_s, nb, d_from_nb) -> bool:
    """FenceBlock.connectsTo + isSameFence (FenceBlock.java)."""
    if nb is None:
        return False
    same = R.has_tag(nb, "minecraft:fences") and (
        R.has_tag(nb, "minecraft:wooden_fences") == R.has_tag(self_s, "minecraft:wooden_fences"))
    gate = _kind(nb) == "gate" and _gate_connects_to_direction(nb, d_from_nb)
    return (not _is_exception_for_connection(nb) and _sturdy(nb, d_from_nb)) or same or gate


def _bars_attaches(nb, d_from_nb) -> bool:
    """IronBarsBlock.attachsTo (panes, iron/copper bars)."""
    if nb is None:
        return False
    return ((not _is_exception_for_connection(nb) and _sturdy(nb, d_from_nb)) or _kind(nb) == "bars"
            or R.has_tag(nb, "minecraft:walls"))


def _wall_connects(nb, d_from_nb) -> bool:
    """WallBlock.connectsTo."""
    if nb is None:
        return False
    gate = _kind(nb) == "gate" and _gate_connects_to_direction(nb, d_from_nb)
    return (R.has_tag(nb, "minecraft:walls") or (not _is_exception_for_connection(nb) and _sturdy(nb, d_from_nb))
            or _kind(nb) == "bars" or gate)


# WallBlock TEST_SHAPE_POST = column(2,0,16); TEST_SHAPES_WALL = rotateHorizontal(boxZ(2,16,0,9)), as (x1,z1,x2,z2)
_TEST_POST = (7 / 16, 7 / 16, 9 / 16, 9 / 16)
_TEST_WALL = {"north": (7 / 16, 0.0, 9 / 16, 9 / 16), "east": (7 / 16, 7 / 16, 1.0, 9 / 16),
              "south": (7 / 16, 7 / 16, 9 / 16, 1.0), "west": (0.0, 7 / 16, 9 / 16, 9 / 16)}


def _wall_state(W, p, s):
    """WallBlock.getStateForPlacement -> updateShape(level, state, topPos, topState, n, e, s, w)."""
    conn = {d: _wall_connects(W.get(_add(p, d)), OPP[d]) for d in HORIZ}
    top = W.get(_add(p, "up"))
    above_face = _face_rects(R.collision_boxes(top), "down") if top is not None else []
    sides = {}
    for d in HORIZ:   # updateSides / makeWallState
        sides[d] = ("tall" if _covers(above_face, _TEST_WALL[d]) else "low") if conn[d] else "none"
    # shouldRaisePost
    if top is not None and _kind(top) == "wall" and _p(top, "up") == "true":
        up = True
    else:
        n, so, e, w = (sides[d] == "none" for d in ("north", "south", "east", "west"))
        has_corner = (n and so and w and e) or n != so or w != e
        if has_corner:
            up = True
        else:
            high = (sides["north"] == "tall" and sides["south"] == "tall") or (sides["east"] == "tall" and sides["west"] == "tall")
            up = False if high else ((top is not None and R.has_tag(top, "minecraft:wall_post_override"))
                                     or _covers(above_face, _TEST_POST))
    return R.with_props(s, up=up, **sides)


def _vine_support(W, p, d) -> bool:
    """VineBlock.canSupportAtFace."""
    if d == "down":
        return False
    if _can_attach_to(W.get(_add(p, d)), d):
        return True
    if d == "up":
        return False
    above = W.get(_add(p, "up"))
    return above is not None and _kind(above) == "vine" and _p(above, d) == "true"


def _vine_state(W, p, s):
    """VineBlock.getUpdatedState; vines authored with no faces get every supported face (placement-like)."""
    faces = {d: _p(s, d) == "true" for d in ("up",) + HORIZ}
    if not any(faces.values()):
        auto = {d: _vine_support(W, p, d) for d in HORIZ}
        if not any(auto.values()):
            auto["up"] = _vine_support(W, p, "up")
        faces.update(auto)
        return R.with_props(s, **faces), "auto"
    if faces["up"]:
        # literal port: getUpdatedState tests isAcceptableNeighbour(level, abovePos, Direction.DOWN)
        faces["up"] = _can_attach_to(W.get(_add(p, "up")), "down")
    for d in HORIZ:
        if faces[d]:
            faces[d] = _vine_support(W, p, d)
    return R.with_props(s, **faces), ""


def _chest_can_connect(s, nb) -> bool:
    """ChestBlock.chestCanConnectTo: same block; CopperChestBlock: any #copper_chests block with a TYPE."""
    if nb is None:
        return False
    if R.is_a(s, "CopperChestBlock"):
        return R.has_tag(nb, "minecraft:copper_chests") and R.prop(nb, "type") is not None
    return _bid(nb) == _bid(s)


def _chest_connected_dir(s) -> str:
    """ChestBlock.getConnectedDirection: LEFT -> facing.getClockWise(), otherwise facing.getCounterClockWise()."""
    f = _p(s, "facing")
    return CW[f] if _p(s, "type") == "left" else CCW[f]


_COPPER_STAGES = ("", "exposed_", "weathered_", "oxidized_")


def _least_oxidized_copper_chest(a: str, b: str) -> str:
    """CopperChestBlock.getLeastOxidizedChestOfConnectedBlocks: unwax both if only one is waxed, keep the less
    oxidized block (ties -> ``a``)."""
    def split(bid):
        n = bid.split(":")[1]
        waxed = n.startswith("waxed_")
        n = n[len("waxed_"):] if waxed else n
        return waxed, next(i for i, st in enumerate(_COPPER_STAGES) if n == st + "copper_chest")

    (wa, sa), (wb, sb) = split(a), split(b)
    waxed = wa and wb
    stage = sa if sa <= sb else sb
    return "minecraft:" + ("waxed_" if waxed else "") + _COPPER_STAGES[stage] + "copper_chest"


def _chest_state(W, p, s):
    """ChestBlock.updateShape applied in Block.UPDATE_SHAPE_ORDER (west, east, north, south)."""
    for d in ("west", "east", "north", "south"):
        nb = W.get(_add(p, d))
        if _chest_can_connect(s, nb):
            ntype = _p(nb, "type")
            if (_p(s, "type") == "single" and ntype != "single" and _p(s, "facing") == _p(nb, "facing")
                    and _chest_connected_dir(nb) == OPP[d]):
                s = R.with_props(s, type="left" if ntype == "right" else "right")
        elif _p(s, "type") != "single" and _chest_connected_dir(s) == d:
            s = R.with_props(s, type="single")
    return s


# ------------------------------------------------------------------------------------------ main entry
def resolve(blocks: dict, max_passes: int = 4):
    """Resolve all game-derived properties.  Returns ``(new_blocks, stats)``."""
    W = dict(blocks)
    stats = {"changes": {}, "errors": [], "warnings": [], "removed": [], "passes": 0}

    def bump(rule, n=1):
        stats["changes"][rule] = stats["changes"].get(rule, 0) + n

    def setp(p, new, rule):
        if W[p] != new:
            W[p] = new
            bump(rule)
            return True
        return False

    _check_multiblock(W, stats, bump)
    for _pass in range(max_passes):
        stats["passes"] += 1
        before = sum(stats["changes"].values())
        by_kind: dict = {}
        for p, s in W.items():
            k = _kind(s)
            if k:
                by_kind.setdefault(k, []).append(p)

        # LeavesBlock: persistent=true (builds must not decay) + distance like LeavesBlock.updateDistance
        leaves = by_kind.get("leaves", [])
        if leaves:
            for p in leaves:
                if _p(W[p], "persistent") != "true":
                    setp(p, R.with_props(W[p], persistent=True), "leaves_persistent")
            dist = {}
            q = deque()
            for p, s in W.items():
                if R.has_tag(s, "minecraft:prevents_nearby_leaf_decay"):
                    dist[p] = 0
                    q.append(p)
            while q:
                p = q.popleft()
                dd = dist[p] + 1
                if dd > 7:
                    continue
                for d in OFF:
                    n = _add(p, d)
                    t = W.get(n)
                    if t is not None and n not in dist and _kind(t) == "leaves":
                        dist[n] = dd
                        q.append(n)
            for p in leaves:
                setp(p, R.with_props(W[p], distance=dist.get(p, 7)), "leaves_distance")

        # SnowyBlock.getStateForPlacement / updateShape: snowy = above is #snow
        for p in by_kind.get("snowy", []):
            a = W.get(_add(p, "up"))
            setp(p, R.with_props(W[p], snowy=a is not None and R.has_tag(a, "minecraft:snow")), "snowy")

        # HugeMushroomBlock.updateShape: a face toward the same block becomes false; other faces keep their authored
        # value (the default state has every face true, so a plain "red_mushroom_block" ends up exactly like
        # getStateForPlacement; deliberately authored false faces -- the all-pores texture -- survive like in game)
        for p in by_kind.get("mushroom", []):
            s = W[p]
            b = _bid(s)
            off = {d: False for d in OFF if (t := W.get(_add(p, d))) is not None and _bid(t) == b}
            if off:
                setp(p, R.with_props(s, **off), "mushroom_faces")

        # ChestBlock.updateShape: orphaned left/right halves -> single; a single chest next to a half that points at
        # it (same facing) becomes the other half
        for p in by_kind.get("chest", []):
            s = W[p]
            new = _chest_state(W, p, s)
            if new != s and _p(new, "type") == "single":
                stats["warnings"].append(f"chest at {p} is type={_p(s, 'type')} but has no partner chest at "
                                         f"{_add(p, _chest_connected_dir(s))} -> single (like the game)")
            setp(p, new, "chest_type")
        # CopperChestBlock.updateShape: a connected half takes its partner's block (oxidation stage); a mutual pair
        # of different stages is unified to the least oxidized one, like placing the second half would
        for p in by_kind.get("chest", []):
            s = W[p]
            if _p(s, "type") == "single" or not R.is_a(s, "CopperChestBlock"):
                continue
            q = _add(p, _chest_connected_dir(s))
            t = W.get(q)
            if not _chest_can_connect(s, t) or _bid(t) == _bid(s):
                continue
            if _p(t, "type") != "single" and _add(q, _chest_connected_dir(t)) == p:
                blk = _least_oxidized_copper_chest(_bid(s), _bid(t))
                setp(q, R.with_block(t, blk), "copper_chest_stage")
            else:
                blk = _bid(t)
            setp(p, R.with_block(s, blk), "copper_chest_stage")

        # GrowingPlantHeadBlock/BodyBlock.updateShape: a head with its own plant in the growth direction becomes the
        # body (CaveVinesBlock keeps berries); a body without it becomes the head (game: random age; we use age=25 =
        # fully grown, like shears, so the tip does not keep growing in the world)
        for p in by_kind.get("growing_plant", []):
            s = W[p]
            head, body, gdir = _GROWING_PLANTS[_bid(s)]
            nb = W.get(_add(p, gdir))
            continues = nb is not None and _bid(nb) in (head, body)
            berries = {"berries": _p(s, "berries")} if _p(s, "berries") is not None else {}
            if _bid(s) == head and continues:
                setp(p, R.make_state(body, berries), "growing_plant")
            elif _bid(s) == body and not continues:
                setp(p, R.make_state(head, {"age": "25", **berries}), "growing_plant")

        # HangingMossBlock.updateShape: tip = the block below is not hanging moss
        for p in by_kind.get("hanging_moss", []):
            b = W.get(_add(p, "down"))
            setp(p, R.with_props(W[p], tip=not (b is not None and _bid(b) == _bid(W[p]))), "hanging_moss_tip")

        # CampfireBlock.isSmokeSource: signal_fire = below is hay_block
        for p in by_kind.get("campfire", []):
            b = W.get(_add(p, "down"))
            setp(p, R.with_props(W[p], signal_fire=b is not None and _bid(b) == "minecraft:hay_block"), "campfire_signal")

        # ShelfBlock/SideChainPartBlock: only powered shelves are connectable; unpowered -> unconnected
        for p in by_kind.get("shelf", []):
            s = W[p]
            if _p(s, "powered") == "true":
                msg = f"shelf at {p} is powered=true (needs a redstone signal); side_chain kept as authored"
                if msg not in stats["warnings"]:
                    stats["warnings"].append(msg)
            else:
                setp(p, R.with_props(s, side_chain="unconnected"), "shelf_side_chain")

        # StairBlock shapes
        for p in by_kind.get("stairs", []):
            setp(p, R.with_props(W[p], shape=_stairs(W, p, W[p])), "stairs_shape")

        # FenceBlock connections
        for p in by_kind.get("fence", []):
            s = W[p]
            setp(p, R.with_props(s, **{d: _fence_connects(s, W.get(_add(p, d)), OPP[d]) for d in HORIZ}), "fence")

        # IronBarsBlock family (glass panes, iron/copper bars)
        for p in by_kind.get("bars", []):
            s = W[p]
            setp(p, R.with_props(s, **{d: _bars_attaches(W.get(_add(p, d)), OPP[d]) for d in HORIZ}), "pane_bars")

        # FenceGateBlock in_wall: a wall on either side along the gate's span
        for p in by_kind.get("gate", []):
            s = W[p]
            f = _p(s, "facing")
            sides = ("west", "east") if AXIS[f] == "z" else ("north", "south")
            in_wall = any((t := W.get(_add(p, d))) is not None and R.has_tag(t, "minecraft:walls") for d in sides)
            setp(p, R.with_props(s, in_wall=in_wall), "gate_in_wall")

        # WallBlock: top-down so the wall above is final before its shape is used
        for p in sorted(by_kind.get("wall", []), key=lambda q: -q[1]):
            setp(p, _wall_state(W, p, W[p]), "wall")

        # VineBlock: top-down (a vine may be held by the vine above)
        for p in sorted(by_kind.get("vine", []), key=lambda q: -q[1]):
            new, how = _vine_state(W, p, W[p])
            if not any(_p(new, d) == "true" for d in ("up",) + HORIZ):
                stats["removed"].append((p, W[p], "vine has no supporting face"))
                stats["warnings"].append(f"vine at {p} has no supporting face -> removed (the game would pop it)")
                del W[p]
                bump("vine_removed")
                continue
            setp(p, new, "vine_auto_faces" if how else "vine_faces")

        if sum(stats["changes"].values()) == before:
            break
    else:
        stats["warnings"].append(f"resolve did not converge in {max_passes} passes (states may still change in game)")
    return W, stats


def _check_multiblock(W, stats, bump):
    """Door / bed / double-plant half consistency (DoorBlock, AbstractBedBlock, DoublePlantBlock.updateShape)."""
    errs = stats["errors"]
    for p, s in sorted(W.items()):
        k = _kind(s)
        if k == "door":
            if _p(s, "half") == "lower":
                up = _add(p, "up")
                u = W.get(up)
                if u is None or _bid(u) != _bid(s) or _p(u, "half") != "upper":
                    errs.append(f"door {_bid(s)} lower half at {p} has no matching upper half at {up}")
                else:
                    # DoorBlock.updateShape: the upper half becomes neighbourState.setValue(HALF, UPPER)
                    want = R.with_props(s, half="upper")
                    if u != want:
                        W[up] = want
                        bump("door_upper_synced")
            else:
                dn = _add(p, "down")
                lo = W.get(dn)
                if lo is None or _bid(lo) != _bid(s) or _p(lo, "half") != "lower":
                    errs.append(f"door {_bid(s)} upper half at {p} has no matching lower half at {dn}")
        elif k == "bed":
            part, f = _p(s, "part"), _p(s, "facing")
            other_dir = f if part == "foot" else OPP[f]          # AbstractBedBlock.getNeighbourDirection
            q = _add(p, other_dir)
            o = W.get(q)
            want_part = "head" if part == "foot" else "foot"
            if o is None or _bid(o) != _bid(s) or _p(o, "part") != want_part or _p(o, "facing") != f:
                errs.append(f"bed {_bid(s)} {part} at {p} (facing={f}) has no matching {want_part} at {q}")
        elif k == "double_plant":
            half = _p(s, "half")
            age = _p(s, "age")
            if age is not None and int(age) < 3 and R.is_a(s, "PitcherCropBlock"):
                # PitcherCropBlock.isDouble(age) = age >= 3: younger crops are a single lower block
                if half == "upper":
                    errs.append(f"{_bid(s)} upper half at {p} with age={age}: below age 3 the crop is one block "
                                "(half=lower only)")
                continue
            q = _add(p, "up" if half == "lower" else "down")
            o = W.get(q)
            want = "upper" if half == "lower" else "lower"
            if o is None or _bid(o) != _bid(s) or _p(o, "half") != want:
                errs.append(f"double plant {_bid(s)} {half} half at {p} has no matching {want} half at {q}")
