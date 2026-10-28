"""Rotate / mirror block states (every orientation-dependent property in the 26.3 registry).

Conventions (same as Minecraft's ``Rotation`` / ``Mirror``):
  * ``rotate_state(s, n)`` turns the state ``n`` quarter turns **clockwise seen from above**
    (north -> east -> south -> west).  Positions rotate as ``(x, z) -> (-z, x)`` per turn.
  * ``mirror_state(s, "x")`` mirrors across the x axis direction, i.e. ``x -> -x`` (east <-> west);
    this is vanilla ``Mirror.FRONT_BACK``.  ``mirror_state(s, "z")`` maps ``z -> -z`` (north <-> south),
    vanilla ``Mirror.LEFT_RIGHT``.

Property handling (verified against the 26.3 sources: ``Rotation.rotate``, ``Mirror.mirror``,
``StairBlock/DoorBlock/ChestBlock/WallBlock/CrossCollisionBlock/HugeMushroomBlock/RailBlock.rotate|mirror``):
  facing (4/5/6 dirs)        horizontal dirs rotate / mirror, up/down unchanged
  axis                       x <-> z on odd turns; unchanged by mirrors
  rotation (0..15)           rotate: (r + 4n) % 16; mirror x: (16 - r) % 16; mirror z: (8 - r) % 16
  north/east/south/west      values permuted between the four sides (booleans, wall sides, redstone sides)
  shape (stairs)             unchanged by rotation; mirror swaps *_left <-> *_right
  shape (rails)              direction pairs rotated / mirrored
  hinge (doors)              mirror swaps left/right
  type (chests single/left/right)   mirror swaps left/right
  side_chain (shelves)       mirror swaps left/right
  orientation (jigsaw/crafter, front_top)   both directions rotated / mirrored
Note: vanilla's stair FRONT_BACK mirror and chest mirror keep the handedness for some cases (game bugs);
we always apply the geometrically correct mirror.  ``blockwright.resolve`` recomputes stair shapes anyway.
tests/test_core_gamecheck.py compares every one of the 35,723 states with the game's own BlockState.rotate/mirror:
identical except stair shape / chest type / shelf side_chain handedness under mirrors, anvil facing under mirrors
(vanilla does not mirror anvils) and fire / chorus-plant sides (vanilla does not rotate them).  Not remapped (same as
vanilla): chiseled bookshelf slot_N_occupied and brewing stand has_bottle_N under mirrors.
"""
from __future__ import annotations

from . import registry as R

H = ("north", "east", "south", "west")
_SIDES = frozenset(H)

# Property names that never change under a rotation about Y or a horizontal mirror.
INVARIANT = frozenset("""
age attached attachment berries bites bloom bottom can_summon candles charges conditional copper_golem_pose cracked
crafting creaking_heart_state delay disarmed distance down drag dusted eggs enabled extended eye face flower_amount
half hanging has_book has_bottle_0 has_bottle_1 has_bottle_2 has_record hatch honey_level hydration in_wall
instrument inverted layers leaves level lit locked mode moisture natural note occupied ominous open part persistent
pickles potent_sulfur_state power powered sculk_sensor_phase segment_amount short shrieking signal_fire
slot_0_occupied slot_1_occupied slot_2_occupied slot_3_occupied slot_4_occupied slot_5_occupied snowy stage
thickness tilt tip trial_spawner_state triggered unstable up vault_state vertical_direction waterlogged
""".split())
# Property names this module transforms.
TRANSFORMED = frozenset("facing axis rotation north east south west shape hinge type side_chain orientation".split())

_STAIR_SHAPES = {"straight", "inner_left", "inner_right", "outer_left", "outer_right"}
_LR = {"left": "right", "right": "left"}
_CACHE: dict = {}


def rot_dir(d: str, n: int) -> str:
    """Rotate a direction name ``n`` quarter turns clockwise (up/down unchanged)."""
    if d in _SIDES:
        return H[(H.index(d) + n) % 4]
    return d


def mir_dir(d: str, axis: str) -> str:
    """Mirror a direction name: axis 'x' swaps east/west, 'z' swaps north/south."""
    if axis == "x":
        return {"east": "west", "west": "east"}.get(d, d)
    if axis == "z":
        return {"north": "south", "south": "north"}.get(d, d)
    raise ValueError(f"mirror axis must be 'x' or 'z', got {axis!r}")


def rotate_pos(x: int, z: int, n: int):
    """Rotate a horizontal offset ``n`` quarter turns clockwise seen from above: (x, z) -> (-z, x)."""
    n %= 4
    for _ in range(n):
        x, z = -z, x
    return x, z


def _rail(shape: str, f) -> str:
    if shape.startswith("ascending_"):
        return "ascending_" + f(shape[len("ascending_"):])
    a, b = shape.split("_")
    a, b = f(a), f(b)
    pair = {a, b}
    if pair == {"north", "south"}:
        return "north_south"
    if pair == {"east", "west"}:
        return "east_west"
    for name in ("south_east", "south_west", "north_west", "north_east"):
        if set(name.split("_")) == pair:
            return name
    raise AssertionError(shape)


def _transform(state: str, fdir, n_turns: int, mirror_axis):
    """Shared worker: ``fdir`` maps a direction name; n_turns for axis/rotation; mirror_axis or None."""
    bid, items = R._split(state)
    if not items:
        return R.parse_state(state)
    p = dict(items)
    legal = R.info(bid).properties
    out = dict(p)
    sides = [d for d in H if d in p]
    if sides:
        for d in sides:
            nd = fdir(d)
            out[nd] = p[d]
    for k, v in p.items():
        if k in _SIDES:
            continue
        if k == "facing":
            out[k] = fdir(v)
        elif k == "axis":
            if n_turns % 2 == 1 and v in ("x", "z"):
                out[k] = "z" if v == "x" else "x"
        elif k == "rotation":
            r = int(v)
            if mirror_axis is None:
                r = (r + 4 * n_turns) % 16
            elif mirror_axis == "x":
                r = (16 - r) % 16
            else:
                r = (8 - r) % 16
            out[k] = str(r)
        elif k == "shape":
            if v in _STAIR_SHAPES:
                if mirror_axis is not None and v != "straight":
                    a, b = v.split("_")
                    out[k] = f"{a}_{_LR[b]}"
            else:
                out[k] = _rail(v, fdir)
        elif k in ("hinge", "side_chain"):
            if mirror_axis is not None and v in _LR:
                out[k] = _LR[v]
        elif k == "type":
            if mirror_axis is not None and set(legal["type"]) == {"single", "left", "right"} and v in _LR:
                out[k] = _LR[v]
        elif k == "orientation":
            front, top = v.split("_")
            out[k] = f"{fdir(front)}_{fdir(top)}"
        elif k not in INVARIANT and k not in TRANSFORMED:
            raise NotImplementedError(f"rotate/mirror: unhandled property {k!r} on {bid}")
    return R.make_state(bid, out)


def rotate_state(state: str, quarter_turns_cw: int) -> str:
    """Rotate ``state`` by ``quarter_turns_cw`` clockwise quarter turns (seen from above)."""
    n = quarter_turns_cw % 4
    if n == 0:
        return R.parse_state(state)
    key = (state, n)
    r = _CACHE.get(key)
    if r is None:
        r = _transform(state, lambda d: rot_dir(d, n), n, None)
        _CACHE[key] = r
    return r


def mirror_state(state: str, axis: str) -> str:
    """Mirror ``state``: axis 'x' flips east/west (x -> -x), 'z' flips north/south (z -> -z)."""
    if axis not in ("x", "z"):
        raise ValueError(f"mirror axis must be 'x' or 'z', got {axis!r}")
    key = (state, "m" + axis)
    r = _CACHE.get(key)
    if r is None:
        r = _transform(state, lambda d: mir_dir(d, axis), 0, axis)
        _CACHE[key] = r
    return r
