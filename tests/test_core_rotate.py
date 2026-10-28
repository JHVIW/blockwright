"""rotate_state / mirror_state: every orientation-dependent property name in the 26.3 registry dump is tested.
Run: ``python tests/test_core_rotate.py``."""
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from blockwright import registry as R  # noqa: E402
from blockwright.rotate import INVARIANT, TRANSFORMED, mirror_state, rot_dir, rotate_state  # noqa: E402

H = ["north", "east", "south", "west"]


def P(s, k):
    return R.prop(s, k)


def test_every_property_name_is_classified():
    names = set(R.property_names())
    unknown = names - INVARIANT - TRANSFORMED
    assert not unknown, f"unclassified property names in the registry: {sorted(unknown)}"
    assert not (INVARIANT & TRANSFORMED)
    # the orientation-dependent names that exist in 26.3 (each has a dedicated test below)
    assert {"facing", "axis", "rotation", "north", "east", "south", "west", "shape", "hinge", "type", "side_chain",
            "orientation"} <= names


def _sample_states(bid):
    bi = R.info(bid)
    out = [R.make_state(bid)]
    for k, vals in bi.properties.items():
        for v in vals:
            out.append(R.make_state(bid, {k: v}))
    return out


def test_group_laws_on_every_block():
    """rot^4 = id, rot(1) then rot(3) = id, mirror twice = id, and rot2 = mirror x * mirror z for every block."""
    for bid in R.all_blocks():
        for s in _sample_states(bid):
            assert rotate_state(rotate_state(s, 1), 3) == s, s
            assert rotate_state(s, 4) == s and rotate_state(s, 0) == s
            r = s
            for _ in range(4):
                r = rotate_state(r, 1)
            assert r == s, s
            for ax in ("x", "z"):
                assert mirror_state(mirror_state(s, ax), ax) == s, (s, ax)
            assert rotate_state(s, 2) == mirror_state(mirror_state(s, "x"), "z"), s


def test_facing_4_5_6_dirs():
    s = R.parse_state("oak_stairs[facing=north]")
    assert [P(rotate_state(s, n), "facing") for n in range(4)] == H
    assert P(mirror_state(s, "z"), "facing") == "south" and P(mirror_state(s, "x"), "facing") == "north"
    e = R.parse_state("oak_stairs[facing=east]")
    assert P(mirror_state(e, "x"), "facing") == "west" and P(mirror_state(e, "z"), "facing") == "east"
    hop = R.parse_state("hopper[facing=down]")                    # 5-dir facing
    assert rotate_state(hop, 1) == hop and P(rotate_state(R.with_props(hop, facing="west"), 1), "facing") == "north"
    for v in ("up", "down"):                                      # 6-dir facing
        d = R.parse_state(f"dispenser[facing={v}]")
        assert rotate_state(d, 1) == d and mirror_state(d, "x") == d


def test_axis():
    for bid in ("oak_log", "iron_chain", "nether_portal", "hay_block"):
        legal = R.info(bid).properties["axis"]
        if "x" in legal:
            s = R.make_state(bid, axis="x")
            assert P(rotate_state(s, 1), "axis") == "z" and P(rotate_state(s, 2), "axis") == "x"
            assert P(mirror_state(s, "x"), "axis") == "x" and P(mirror_state(s, "z"), "axis") == "x"
        if "y" in legal:
            y = R.make_state(bid, axis="y")
            assert rotate_state(y, 1) == y


def test_rotation_16():
    """Vanilla Rotation.rotate(r, 16) and Mirror.mirror(r, 16) ported independently here."""
    def vanilla_mirror(r, mirror):
        steps, half = 16, 8
        c = r - steps if r > half else r
        return (half - c + steps) % steps if mirror == "LEFT_RIGHT" else (steps - c) % steps

    for bid in ("oak_sign", "white_banner", "skeleton_skull", "oak_hanging_sign"):
        for r in range(16):
            s = R.make_state(bid, rotation=r)
            for n in range(4):
                assert int(P(rotate_state(s, n), "rotation")) == (r + 4 * n) % 16
            assert int(P(mirror_state(s, "z"), "rotation")) == vanilla_mirror(r, "LEFT_RIGHT")
            assert int(P(mirror_state(s, "x"), "rotation")) == vanilla_mirror(r, "FRONT_BACK")
    # rotation 0 faces south: mirroring north<->south turns it to 8 (north), east-west mirror keeps it
    assert P(mirror_state(R.make_state("oak_sign", rotation=0), "z"), "rotation") == "8"


def test_side_properties_booleans_wallsides_redstone():
    f = R.parse_state("oak_fence[north=true]")
    assert R.props(rotate_state(f, 1))["east"] == "true" and R.props(rotate_state(f, 1))["north"] == "false"
    assert R.props(mirror_state(f, "z"))["south"] == "true"
    assert R.props(mirror_state(R.parse_state("oak_fence[east=true]"), "x"))["west"] == "true"
    w = R.parse_state("cobblestone_wall[north=tall,east=low,up=false]")
    r = R.props(rotate_state(w, 1))
    assert (r["east"], r["south"], r["north"], r["up"]) == ("tall", "low", "none", "false")
    rw = R.props(rotate_state(R.parse_state("redstone_wire[north=up,west=side]"), 3))
    assert rw["west"] == "up" and rw["south"] == "side"
    m = R.props(rotate_state(R.parse_state("red_mushroom_block[north=false,up=false]"), 2))
    assert m["south"] == "false" and m["up"] == "false" and m["north"] == "true"
    v = R.props(mirror_state(R.parse_state("vine[west=true,up=true]"), "x"))
    assert v["east"] == "true" and v["west"] == "false" and v["up"] == "true"
    # vanilla CrossCollisionBlock.rotate(CLOCKWISE_90): NORTH <- WEST, EAST <- NORTH, SOUTH <- EAST, WEST <- SOUTH
    s = R.parse_state("glass_pane[west=true,south=true]")
    r = R.props(rotate_state(s, 1))
    assert r["north"] == "true" and r["west"] == "true" and r["east"] == "false" and r["south"] == "false"
    g = R.props(rotate_state(R.parse_state("glow_lichen[down=true,north=true]"), 1))
    assert g["down"] == "true" and g["east"] == "true"


def test_stair_shape_and_hinge_and_chest_type_and_side_chain():
    s = R.parse_state("oak_stairs[facing=north,shape=outer_left]")
    assert P(rotate_state(s, 1), "shape") == "outer_left"
    assert P(mirror_state(s, "x"), "shape") == "outer_right" and P(mirror_state(s, "z"), "shape") == "outer_right"
    assert P(mirror_state(R.with_props(s, shape="inner_right"), "x"), "shape") == "inner_left"
    assert P(mirror_state(R.with_props(s, shape="straight"), "z"), "shape") == "straight"
    d = R.parse_state("oak_door[hinge=left,facing=east]")
    assert P(rotate_state(d, 1), "hinge") == "left" and P(mirror_state(d, "x"), "hinge") == "right"
    assert P(mirror_state(d, "x"), "facing") == "west" and P(mirror_state(d, "z"), "facing") == "east"
    c = R.parse_state("chest[type=left,facing=north]")
    assert P(rotate_state(c, 1), "type") == "left" and P(mirror_state(c, "z"), "type") == "right"
    assert P(mirror_state(R.parse_state("chest[type=single]"), "x"), "type") == "single"
    slab = R.parse_state("stone_slab[type=top]")
    assert mirror_state(slab, "x") == slab                          # slab 'type' is not handed
    ph = R.parse_state("piston_head[type=sticky]")
    assert P(mirror_state(ph, "x"), "type") == "sticky"
    sh = R.parse_state("oak_shelf[side_chain=left,powered=true]")
    assert P(rotate_state(sh, 2), "side_chain") == "left" and P(mirror_state(sh, "z"), "side_chain") == "right"
    assert P(mirror_state(R.with_props(sh, side_chain="center"), "z"), "side_chain") == "center"


def test_chest_double_pair_stays_consistent():
    """A double chest's halves must still point at each other after mirroring (ChestBlock.getConnectedDirection)."""
    def partner(state, pos):
        f, t = P(state, "facing"), P(state, "type")
        d = rot_dir(f, 1) if t == "left" else rot_dir(f, 3)          # LEFT -> facing.getClockWise()
        off = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[d]
        return (pos[0] + off[0], pos[1] + off[1])

    left = R.parse_state("chest[facing=north,type=left]")
    right = R.parse_state("chest[facing=north,type=right]")
    assert partner(left, (0, 0)) == (1, 0) and partner(right, (1, 0)) == (0, 0)
    for ax in ("x", "z"):
        ml, mr = mirror_state(left, ax), mirror_state(right, ax)
        pl = (0, 0) if ax == "z" else (0, 0)
        pr = (1, 0) if ax == "z" else (-1, 0)
        assert partner(ml, pl) == pr and partner(mr, pr) == pl, ax


def test_rail_shapes():
    r = R.parse_state("rail[shape=north_south]")
    assert P(rotate_state(r, 1), "shape") == "east_west"
    assert P(rotate_state(R.parse_state("rail[shape=ascending_north]"), 1), "shape") == "ascending_east"
    assert P(rotate_state(R.parse_state("rail[shape=south_east]"), 1), "shape") == "south_west"
    assert P(rotate_state(R.parse_state("rail[shape=north_west]"), 1), "shape") == "north_east"
    assert P(mirror_state(R.parse_state("rail[shape=south_east]"), "x"), "shape") == "south_west"
    assert P(mirror_state(R.parse_state("rail[shape=south_east]"), "z"), "shape") == "north_east"
    assert P(mirror_state(R.parse_state("powered_rail[shape=ascending_east]"), "x"), "shape") == "ascending_west"
    assert P(rotate_state(R.parse_state("detector_rail[shape=east_west]"), 1), "shape") == "north_south"


def test_orientation_front_top():
    j = R.parse_state("jigsaw[orientation=north_up]")
    assert P(rotate_state(j, 1), "orientation") == "east_up"
    assert P(rotate_state(R.parse_state("jigsaw[orientation=up_north]"), 1), "orientation") == "up_east"
    assert P(rotate_state(R.parse_state("crafter[orientation=down_west]"), 3), "orientation") == "down_south"
    assert P(mirror_state(R.parse_state("crafter[orientation=east_up]"), "x"), "orientation") == "west_up"
    assert P(mirror_state(R.parse_state("jigsaw[orientation=up_south]"), "z"), "orientation") == "up_north"


def test_invariant_properties_unchanged():
    for s in ("oak_trapdoor[half=top,open=true,facing=east]", "lever[face=ceiling,facing=north]",
              "bell[attachment=double_wall,facing=east]", "pointed_dripstone[vertical_direction=down]",
              "oak_door[half=upper]", "red_bed[part=head,facing=south]", "oak_leaves[distance=3,persistent=true]"):
        c = R.parse_state(s)
        props = R.props(c)
        for n in range(4):
            r = R.props(rotate_state(c, n))
            for k in ("half", "open", "face", "attachment", "vertical_direction", "part", "distance", "persistent"):
                if k in props:
                    assert r[k] == props[k], (s, k)


def test_geometric_consistency_of_facing_under_transforms():
    """Rotating a state together with the position it points to keeps them aligned (all 4-dir facings)."""
    off = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}

    def rot(p, n):
        x, z = p
        for _ in range(n % 4):
            x, z = -z, x
        return (x, z)

    for f in H:
        s = R.parse_state(f"furnace[facing={f}]")
        for n in range(4):
            assert off[P(rotate_state(s, n), "facing")] == rot(off[f], n)
        assert off[P(mirror_state(s, "x"), "facing")] == (-off[f][0], off[f][1])
        assert off[P(mirror_state(s, "z"), "facing")] == (off[f][0], -off[f][1])


def run_all(ns):
    fails = 0
    for name in sorted(k for k in ns if k.startswith("test_") and callable(ns[k])):
        try:
            ns[name]()
            print(f"ok    {name}")
        except Exception:
            fails += 1
            print(f"FAIL  {name}")
            traceback.print_exc()
    print(f"{'FAILED' if fails else 'PASSED'}: {fails} failure(s)")
    return fails


if __name__ == "__main__":
    sys.exit(1 if run_all(dict(globals())) else 0)
