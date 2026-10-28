"""blockwright.resolve rules on small fixtures; expected values derived by hand from the 26.3 sources cited in
blockwright/resolve.py.  (tests/test_core_gamecheck.py additionally cross-checks against the real game code.)
Run: ``python tests/test_core_resolve.py``."""
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from blockwright import registry as R  # noqa: E402
from blockwright.resolve import resolve  # noqa: E402


def res(d):
    blocks = {p: R.parse_state(s) for p, s in d.items()}
    out, stats = resolve(blocks)
    again, stats2 = resolve(out)
    assert again == out and sum(stats2["changes"].values()) == 0, "resolve must be idempotent"
    return out, stats


def P(s, k):
    return R.prop(s, k)


# ------------------------------------------------------------------------------------------------ stairs
def test_stairs_outer_corner():
    # StairBlock.getStairsShape: behind (pos+facing) is a stair of the same half facing across -> OUTER
    out, _ = res({(0, 0, 0): "oak_stairs[facing=north]", (0, 0, -1): "oak_stairs[facing=west]"})
    assert P(out[(0, 0, 0)], "shape") == "outer_left"          # behind faces west == north.getCounterClockWise()
    out, _ = res({(0, 0, 0): "oak_stairs[facing=north]", (0, 0, -1): "oak_stairs[facing=east]"})
    assert P(out[(0, 0, 0)], "shape") == "outer_right"


def test_stairs_inner_corner_and_blocking():
    out, _ = res({(0, 0, 0): "oak_stairs[facing=north]", (0, 0, 1): "oak_stairs[facing=west]"})
    assert P(out[(0, 0, 0)], "shape") == "inner_left"          # front faces west == north.getCounterClockWise()
    out, _ = res({(0, 0, 0): "oak_stairs[facing=north]", (0, 0, 1): "oak_stairs[facing=east]"})
    assert P(out[(0, 0, 0)], "shape") == "inner_right"
    # canTakeShape: a same-facing/same-half stair on the side blocks the inner corner
    out, _ = res({(0, 0, 0): "oak_stairs[facing=north]", (0, 0, 1): "oak_stairs[facing=west]",
                  (-1, 0, 0): "oak_stairs[facing=north]"})
    assert P(out[(0, 0, 0)], "shape") == "straight"
    # different half -> no corner; different material still counts (isStairs is any StairBlock)
    out, _ = res({(0, 0, 0): "oak_stairs[facing=north]", (0, 0, -1): "oak_stairs[facing=west,half=top]"})
    assert P(out[(0, 0, 0)], "shape") == "straight"
    out, _ = res({(0, 0, 0): "oak_stairs[facing=north]", (0, 0, -1): "cut_copper_stairs[facing=west]"})
    assert P(out[(0, 0, 0)], "shape") == "outer_left"


def test_stairs_square_ring_roof():
    """A 3x3 ring of stairs facing inward (roof hip): 4 corners become outer corners, edges straight."""
    ring = {}
    for x in range(3):
        ring[(x, 0, 0)] = "spruce_stairs[facing=south]"
        ring[(x, 0, 2)] = "spruce_stairs[facing=north]"
    ring[(0, 0, 1)] = "spruce_stairs[facing=east]"
    ring[(2, 0, 1)] = "spruce_stairs[facing=west]"
    out, _ = res(ring)
    corners = {p: P(out[p], "shape") for p in ((0, 0, 0), (2, 0, 0), (0, 0, 2), (2, 0, 2))}
    assert all(v.startswith("outer") for v in corners.values()), corners
    assert P(out[(1, 0, 0)], "shape") == "straight" and P(out[(0, 0, 1)], "shape") == "straight"


# ---------------------------------------------------------------------------------------------- fences
def test_fence_connections():
    out, _ = res({(0, 0, 0): "oak_fence", (1, 0, 0): "spruce_fence", (-1, 0, 0): "stone", (0, 0, 1): "nether_brick_fence",
                  (0, 0, -1): "oak_leaves"})
    f = R.props(out[(0, 0, 0)])
    assert f["east"] == "true"      # same (wooden) fence family
    assert f["west"] == "true"      # sturdy full face
    assert f["south"] == "false"    # wooden vs nether brick fence: isSameFence false, not sturdy
    assert f["north"] == "false"    # leaves: isExceptionForConnection even though... (leaves are not sturdy anyway)
    out, _ = res({(0, 0, 0): "oak_fence", (1, 0, 0): "pumpkin", (-1, 0, 0): "glass"})
    assert P(out[(0, 0, 0)], "east") == "false" and P(out[(0, 0, 0)], "west") == "true"   # pumpkin is an exception
    out, _ = res({(0, 0, 0): "oak_fence", (-1, 0, 0): "oak_stairs[facing=east]", (1, 0, 0): "oak_stairs[facing=east]"})
    assert P(out[(0, 0, 0)], "west") == "true"      # stair's full east face (its back) is sturdy
    assert P(out[(0, 0, 0)], "east") == "false"     # the other stair shows its open front (west face not sturdy)


def test_fence_gate_connection_and_in_wall():
    out, _ = res({(0, 0, 0): "oak_fence", (1, 0, 0): "oak_fence_gate[facing=north]", (0, 0, 1): "oak_fence_gate[facing=north]"})
    assert P(out[(0, 0, 0)], "east") == "true"      # gate spans east-west -> connects sideways
    assert P(out[(0, 0, 0)], "south") == "false"    # gate's open face points at us
    out, _ = res({(0, 0, 0): "oak_fence_gate[facing=north]", (1, 0, 0): "cobblestone_wall", (0, 0, 1): "cobblestone_wall"})
    assert P(out[(0, 0, 0)], "in_wall") == "true"
    out, _ = res({(0, 0, 0): "oak_fence_gate[facing=east]", (1, 0, 0): "cobblestone_wall"})
    assert P(out[(0, 0, 0)], "in_wall") == "false"  # wall is not along the gate's span
    out, _ = res({(0, 0, 0): "oak_fence_gate[facing=east]", (0, 0, -1): "cobblestone_wall"})
    assert P(out[(0, 0, 0)], "in_wall") == "true"


# ---------------------------------------------------------------------------------------------- panes
def test_panes_and_bars():
    out, _ = res({(0, 0, 0): "glass_pane", (1, 0, 0): "stone", (-1, 0, 0): "iron_bars", (0, 0, 1): "cobblestone_wall",
                  (0, 0, -1): "oak_fence"})
    p = R.props(out[(0, 0, 0)])
    assert (p["east"], p["west"], p["south"], p["north"]) == ("true", "true", "true", "false")
    bars = R.props(out[(-1, 0, 0)])
    assert bars["east"] == "true" and bars["west"] == "false"
    out, _ = res({(0, 0, 0): "red_stained_glass_pane", (1, 0, 0): "copper_bars"})
    assert P(out[(0, 0, 0)], "east") == "true" and P(out[(1, 0, 0)], "west") == "true"


# ----------------------------------------------------------------------------------------------- walls
def test_wall_line_posts():
    out, _ = res({(x, 0, 0): "cobblestone_wall" for x in range(3)})
    mid, end = R.props(out[(1, 0, 0)]), R.props(out[(0, 0, 0)])
    assert (mid["east"], mid["west"], mid["up"]) == ("low", "low", "false")        # straight run: no post
    assert (end["east"], end["west"], end["up"]) == ("low", "none", "true")        # end: post
    alone, _ = res({(0, 0, 0): "cobblestone_wall"})
    assert P(alone[(0, 0, 0)], "up") == "true"
    corner, _ = res({(0, 0, 0): "cobblestone_wall", (1, 0, 0): "cobblestone_wall", (0, 0, 1): "cobblestone_wall"})
    assert P(corner[(0, 0, 0)], "up") == "true"                                    # northNone != southNone


def test_wall_tall_low_and_post_rules_above():
    base = {(x, 0, 0): "cobblestone_wall" for x in range(3)}
    full = {**base, (1, 1, 0): "stone"}
    m = R.props(res(full)[0][(1, 0, 0)])
    assert (m["east"], m["west"], m["up"]) == ("tall", "tall", "false")            # covered arms -> tall, no post
    bslab = {**base, (1, 1, 0): "stone_slab[type=bottom]"}
    assert P(res(bslab)[0][(1, 0, 0)], "east") == "tall"                            # bottom slab touches y=0
    tslab = {**base, (1, 1, 0): "stone_slab[type=top]"}
    m = R.props(res(tslab)[0][(1, 0, 0)])
    assert (m["east"], m["up"]) == ("low", "false")                                 # top slab does not touch the wall
    lan = {**base, (1, 1, 0): "lantern"}
    m = R.props(res(lan)[0][(1, 0, 0)])
    assert (m["east"], m["up"]) == ("low", "true")                                  # lantern base covers the post test
    tor = {**base, (1, 1, 0): "torch"}
    assert P(res(tor)[0][(1, 0, 0)], "up") == "true"                                # #wall_post_override
    car = {**base, (1, 1, 0): "white_carpet"}
    m = R.props(res(car)[0][(1, 0, 0)])
    assert (m["east"], m["up"]) == ("tall", "false")                                # carpet covers the whole top
    stacked = {(x, y, 0): "cobblestone_wall" for x in range(3) for y in range(2)}
    m = R.props(res(stacked)[0][(1, 0, 0)])
    assert m["east"] == "tall" and m["up"] == "false"     # the wall above (collision 1.5 high, arms 6 wide) covers the arms


def test_wall_connections():
    out, _ = res({(0, 0, 0): "cobblestone_wall", (1, 0, 0): "stone", (-1, 0, 0): "glass_pane",
                  (0, 0, 1): "oak_fence_gate[facing=north]", (0, 0, -1): "oak_fence"})
    w = R.props(out[(0, 0, 0)])
    assert (w["east"], w["west"], w["south"], w["north"]) == ("low", "low", "none", "none")
    out, _ = res({(0, 0, 0): "cobblestone_wall", (0, 0, 1): "oak_fence_gate[facing=east]"})
    assert P(out[(0, 0, 0)], "south") == "low"


# ---------------------------------------------------------------------------------------------- leaves
def test_leaves_distance_and_persistent():
    d = {(0, y, 0): "oak_log" for y in range(2)}
    for i in range(1, 10):
        d[(i, 1, 0)] = "oak_leaves[persistent=false]"
    out, stats = res(d)
    dist = [int(P(out[(i, 1, 0)], "distance")) for i in range(1, 10)]
    assert dist == [1, 2, 3, 4, 5, 6, 7, 7, 7]
    assert all(P(out[(i, 1, 0)], "persistent") == "true" for i in range(1, 10))
    assert stats["changes"]["leaves_persistent"] == 9
    out, _ = res({(0, 0, 0): "stripped_birch_wood", (0, 1, 0): "birch_leaves", (0, 2, 0): "azalea_leaves"})
    assert P(out[(0, 1, 0)], "distance") == "1" and P(out[(0, 2, 0)], "distance") == "2"
    out, _ = res({(0, 0, 0): "oak_leaves"})
    assert P(out[(0, 0, 0)], "distance") == "7"


# ------------------------------------------------------------------------------------------ misc rules
def test_snowy_campfire_mushroom_shelf():
    out, _ = res({(0, 0, 0): "grass_block[snowy=true]", (1, 0, 0): "grass_block", (1, 1, 0): "snow",
                  (2, 0, 0): "podzol", (2, 1, 0): "snow_block", (3, 0, 0): "mycelium", (3, 1, 0): "stone"})
    assert [P(out[(x, 0, 0)], "snowy") for x in range(4)] == ["false", "true", "true", "false"]
    out, _ = res({(0, 0, 0): "hay_block", (0, 1, 0): "campfire", (1, 0, 0): "dirt", (1, 1, 0): "soul_campfire[signal_fire=true]"})
    assert P(out[(0, 1, 0)], "signal_fire") == "true" and P(out[(1, 1, 0)], "signal_fire") == "false"
    out, _ = res({(0, 0, 0): "red_mushroom_block", (1, 0, 0): "red_mushroom_block", (0, 1, 0): "brown_mushroom_block",
                  (0, -1, 0): "mushroom_stem"})
    m = R.props(out[(0, 0, 0)])
    assert (m["east"], m["west"], m["up"], m["down"]) == ("false", "true", "true", "true")
    assert P(out[(1, 0, 0)], "west") == "false" and P(out[(0, -1, 0)], "up") == "true"
    out, stats = res({(0, 0, 0): "oak_shelf[side_chain=left]", (1, 0, 0): "oak_shelf[side_chain=center,powered=true]"})
    assert P(out[(0, 0, 0)], "side_chain") == "unconnected" and P(out[(1, 0, 0)], "side_chain") == "center"
    assert stats["warnings"]


def test_vines():
    out, _ = res({(0, 0, 0): "vine", (0, 0, -1): "stone"})
    v = R.props(out[(0, 0, 0)])
    assert (v["north"], v["south"], v["east"], v["west"], v["up"]) == ("true", "false", "false", "false", "false")
    out, _ = res({(0, 0, 0): "vine", (1, 0, 0): "oak_planks", (-1, 0, 0): "oak_planks"})
    assert P(out[(0, 0, 0)], "east") == "true" and P(out[(0, 0, 0)], "west") == "true"
    out, _ = res({(0, 0, 0): "vine", (0, 1, 0): "stone"})                         # only a ceiling -> up
    assert P(out[(0, 0, 0)], "up") == "true"
    # hanging vine below a supported vine keeps its face (canSupportAtFace: vine above with that face)
    out, _ = res({(0, 2, 0): "vine[north=true]", (0, 2, -1): "stone", (0, 1, 0): "vine[north=true]", (0, 0, 0): "vine[north=true]"})
    assert all(P(out[(0, y, 0)], "north") == "true" for y in range(3))
    # unsupported faces are dropped; a vine with nothing left is removed (+ warning)
    out, stats = res({(0, 0, 0): "vine[north=true,east=true]", (0, 0, -1): "stone"})
    assert P(out[(0, 0, 0)], "east") == "false" and P(out[(0, 0, 0)], "north") == "true"
    out, stats = res({(0, 0, 0): "vine[north=true]", (5, 5, 5): "stone"})
    assert (0, 0, 0) not in out and stats["removed"] and stats["warnings"]


def test_door_bed_double_plant_consistency():
    out, stats = res({(0, 0, 0): "oak_door[half=lower,facing=east,hinge=right,open=true]",
                      (0, 1, 0): "oak_door[half=upper,facing=north,hinge=left]", (0, -1, 0): "stone"})
    assert out[(0, 1, 0)] == R.parse_state("oak_door[half=upper,facing=east,hinge=right,open=true]")
    assert stats["changes"]["door_upper_synced"] == 1 and not stats["errors"]
    _, stats = res({(0, 0, 0): "oak_door[half=lower]"})
    assert any("no matching upper" in e for e in stats["errors"])
    _, stats = res({(0, 1, 0): "oak_door[half=upper]"})
    assert any("no matching lower" in e for e in stats["errors"])
    _, stats = res({(0, 0, 0): "red_bed[part=foot,facing=east]", (1, 0, 0): "red_bed[part=head,facing=east]"})
    assert not stats["errors"]
    _, stats = res({(0, 0, 0): "red_bed[part=foot,facing=east]", (0, 0, 1): "red_bed[part=head,facing=east]"})
    assert len(stats["errors"]) == 2
    _, stats = res({(0, 0, 0): "red_bed[part=foot,facing=east]", (1, 0, 0): "blue_bed[part=head,facing=east]"})
    assert len(stats["errors"]) == 2
    _, stats = res({(0, 0, 0): "lilac[half=lower]", (0, 1, 0): "lilac[half=upper]"})
    assert not stats["errors"]
    _, stats = res({(0, 0, 0): "lilac[half=lower]", (0, 1, 0): "peony[half=upper]"})
    assert len(stats["errors"]) == 2


# ------------------------------------------------------------- review fixtures (catch a wrong port of each rule)
def test_stairs_outer_blocked_precedence_top_half():
    # outer: canTakeShape(behindFacing.getOpposite()) -- here behind faces west, so the stair at pos+east blocks it
    out, _ = res({(0, 0, 0): "oak_stairs[facing=north]", (0, 0, -1): "oak_stairs[facing=west]",
                  (1, 0, 0): "oak_stairs[facing=north]"})
    assert P(out[(0, 0, 0)], "shape") == "straight"
    # ... but a stair at pos+west (the wrong side) does not block it
    out, _ = res({(0, 0, 0): "oak_stairs[facing=north]", (0, 0, -1): "oak_stairs[facing=west]",
                  (-1, 0, 0): "oak_stairs[facing=north]"})
    assert P(out[(0, 0, 0)], "shape") == "outer_left"
    # inner: canTakeShape(frontFacing) -- front faces west, so the stair at pos+west blocks it, pos+east does not
    out, _ = res({(0, 0, 0): "oak_stairs[facing=north]", (0, 0, 1): "oak_stairs[facing=west]",
                  (1, 0, 0): "oak_stairs[facing=north]"})
    assert P(out[(0, 0, 0)], "shape") == "inner_left"
    # a blocking stair of the other half does not block
    out, _ = res({(0, 0, 0): "oak_stairs[facing=north]", (0, 0, 1): "oak_stairs[facing=west]",
                  (-1, 0, 0): "oak_stairs[facing=north,half=top]"})
    assert P(out[(0, 0, 0)], "shape") == "inner_left"
    # behind (outer) is tested before front (inner)
    out, _ = res({(0, 0, 0): "oak_stairs[facing=north]", (0, 0, -1): "oak_stairs[facing=west]",
                  (0, 0, 1): "oak_stairs[facing=east]"})
    assert P(out[(0, 0, 0)], "shape") == "outer_left"
    # top half works the same way; a behind stair on the same axis (facing south) never makes a corner
    out, _ = res({(0, 0, 0): "oak_stairs[facing=east,half=top]", (1, 0, 0): "oak_stairs[facing=south,half=top]"})
    assert P(out[(0, 0, 0)], "shape") == "outer_right"           # south == east.getClockWise()
    out, _ = res({(0, 0, 0): "oak_stairs[facing=north]", (0, 0, -1): "oak_stairs[facing=south]"})
    assert P(out[(0, 0, 0)], "shape") == "straight"


def test_fence_more_neighbours():
    out, _ = res({(0, 0, 0): "oak_fence", (1, 0, 0): "stone_slab[type=top]", (-1, 0, 0): "stone_slab[type=double]",
                  (0, 0, 1): "cobblestone_wall", (0, 0, -1): "iron_bars"})
    f = R.props(out[(0, 0, 0)])
    assert (f["east"], f["west"], f["south"], f["north"]) == ("false", "true", "false", "false")
    # gate in the fence line connects only when its span is along the line (connectsToDirection uses getClockWise)
    out, _ = res({(0, 0, 0): "oak_fence", (1, 0, 0): "spruce_fence_gate[facing=east]",
                  (-1, 0, 0): "spruce_fence_gate[facing=south]"})
    f = R.props(out[(0, 0, 0)])
    assert (f["east"], f["west"]) == ("false", "true")
    # melon / carved pumpkin / jack o'lantern are exceptions although sturdy
    for b in ("melon", "carved_pumpkin[facing=west]", "jack_o_lantern", "barrier"):
        out, _ = res({(0, 0, 0): "oak_fence", (1, 0, 0): b})
        assert P(out[(0, 0, 0)], "east") == "false", b


def test_wall_post_kept_by_wall_post_above():
    # upper wall at a T junction keeps its post (northNone != southNone) and its arms cover the lower wall's arms,
    # so the lower straight run would drop its post -- shouldRaisePost: topNeighbour is a WallBlock with UP -> true
    d = {(x, 0, 0): "cobblestone_wall" for x in range(3)}
    d.update({(x, 1, 0): "cobblestone_wall" for x in range(3)})
    d[(1, 1, 1)] = "cobblestone_wall"
    out, _ = res(d)
    up = R.props(out[(1, 1, 0)])
    assert (up["east"], up["west"], up["south"], up["north"], up["up"]) == ("low", "low", "low", "none", "true")
    lo = R.props(out[(1, 0, 0)])
    assert (lo["east"], lo["west"], lo["up"]) == ("tall", "tall", "true")


def test_leaves_only_propagate_through_leaves_6_neighbours():
    out, _ = res({(0, 0, 0): "oak_log", (1, 1, 0): "oak_leaves", (1, 0, 0): "stone", (2, 0, 0): "oak_leaves",
                  (0, 0, 1): "oak_leaves", (0, 0, 2): "birch_leaves", (5, 5, 5): "dark_oak_leaves"})
    assert P(out[(1, 1, 0)], "distance") == "7"          # diagonal to the log
    assert P(out[(2, 0, 0)], "distance") == "7"          # stone does not carry the distance
    assert P(out[(0, 0, 1)], "distance") == "1" and P(out[(0, 0, 2)], "distance") == "2"   # mixed leaf types do
    assert P(out[(5, 5, 5)], "persistent") == "true"


def test_mushroom_faces_only_turn_off_toward_same_block():
    # HugeMushroomBlock.updateShape only sets faces toward the same block to false; authored pores stay
    pores = "brown_mushroom_block[north=false,east=false,south=false,west=false,up=false,down=false]"
    out, stats = res({(0, 0, 0): pores, (5, 0, 0): "mushroom_stem[up=false]"})
    assert out[(0, 0, 0)] == R.parse_state(pores) and "mushroom_faces" not in stats["changes"]
    assert P(out[(5, 0, 0)], "up") == "false"                                    # authored, nothing above
    out, _ = res({(0, 0, 0): "red_mushroom_block", (0, 1, 0): "red_mushroom_block", (1, 0, 0): "brown_mushroom_block"})
    m = R.props(out[(0, 0, 0)])
    assert (m["up"], m["east"], m["west"], m["down"]) == ("false", "true", "true", "true")
    assert P(out[(0, 1, 0)], "down") == "false"


def test_vine_up_quirk_literal_port():
    # VineBlock.getUpdatedState tests isAcceptableNeighbour(above, Direction.DOWN) = the TOP face of the block above
    out, _ = res({(0, 0, 0): "vine[up=true]", (0, 1, 0): "stone_slab[type=top]"})
    assert P(out[(0, 0, 0)], "up") == "true"
    out, stats = res({(0, 0, 0): "vine[up=true]", (0, 1, 0): "stone_slab[type=bottom]"})
    assert (0, 0, 0) not in out and stats["removed"]
    # a vine also holds on a full-faced collision shape that is not sturdy-supporting? (glass is sturdy: full block)
    out, _ = res({(0, 0, 0): "vine", (1, 0, 0): "glass"})
    assert P(out[(0, 0, 0)], "east") == "true"


def test_chest_pairing_like_updateShape():
    # orphaned half -> single (+ warning)
    out, stats = res({(0, 0, 0): "chest[facing=north,type=left]"})
    assert P(out[(0, 0, 0)], "type") == "single" and any("no partner" in w for w in stats["warnings"])
    # type=left pairs to facing.getClockWise() (north -> east): the single chest there becomes the right half
    out, _ = res({(0, 0, 0): "chest[facing=north,type=left]", (1, 0, 0): "chest[facing=north]"})
    assert (P(out[(0, 0, 0)], "type"), P(out[(1, 0, 0)], "type")) == ("left", "right")
    out, _ = res({(0, 0, 0): "chest[facing=north,type=right]", (-1, 0, 0): "chest[facing=north]"})
    assert P(out[(-1, 0, 0)], "type") == "left"
    # a chest on the wrong side (left half's partner must be east) does not pair; the half is orphaned
    out, _ = res({(0, 0, 0): "chest[facing=north,type=left]", (-1, 0, 0): "chest[facing=north]"})
    assert (P(out[(0, 0, 0)], "type"), P(out[(-1, 0, 0)], "type")) == ("single", "single")
    # different facing: the game keeps the half (neighbour is a chest) and does not pair the single one
    out, _ = res({(0, 0, 0): "chest[facing=north,type=left]", (1, 0, 0): "chest[facing=south]"})
    assert (P(out[(0, 0, 0)], "type"), P(out[(1, 0, 0)], "type")) == ("left", "single")
    # trapped chest is a different block -> no pairing; copper chests of any oxidation pair (#copper_chests)
    out, _ = res({(0, 0, 0): "chest[facing=north,type=left]", (1, 0, 0): "trapped_chest[facing=north,type=right]"})
    assert (P(out[(0, 0, 0)], "type"), P(out[(1, 0, 0)], "type")) == ("single", "single")
    out, _ = res({(0, 0, 0): "weathered_copper_chest[facing=east,type=left]", (0, 0, 1): "exposed_copper_chest[facing=east]"})
    assert (P(out[(0, 0, 0)], "type"), P(out[(0, 0, 1)], "type")) == ("left", "right")
    # CopperChestBlock.updateShape: a connected pair ends up as ONE block -- the least oxidized (unwaxed if mixed)
    assert R.block_id(out[(0, 0, 0)]) == R.block_id(out[(0, 0, 1)]) == "minecraft:exposed_copper_chest"
    out, _ = res({(0, 0, 0): "waxed_oxidized_copper_chest[facing=east,type=left]",
                  (0, 0, 1): "weathered_copper_chest[facing=east,type=right]"})
    assert R.block_id(out[(0, 0, 0)]) == R.block_id(out[(0, 0, 1)]) == "minecraft:weathered_copper_chest"


def test_growing_plants_head_body_and_hanging_moss():
    d = {(0, 4, 0): "stone", (0, 3, 0): "cave_vines", (0, 2, 0): "cave_vines[berries=true]", (0, 1, 0): "cave_vines"}
    out, _ = res(d)
    assert out[(0, 3, 0)] == R.parse_state("cave_vines_plant[berries=false]")
    assert out[(0, 2, 0)] == R.parse_state("cave_vines_plant[berries=true]")      # CaveVinesBlock keeps berries
    assert out[(0, 1, 0)] == R.parse_state("cave_vines[age=0,berries=false]")     # authored tip kept
    out, _ = res({(0, 1, 0): "stone", (0, 0, 0): "cave_vines_plant[berries=true]"})
    assert out[(0, 0, 0)] == R.parse_state("cave_vines[age=25,berries=true]")     # body without a tip -> head
    out, _ = res({(0, y, 0): "kelp" for y in range(3)})                           # kelp grows UP
    assert [R.block_id(out[(0, y, 0)]) for y in range(3)] == ["minecraft:kelp_plant"] * 2 + ["minecraft:kelp"]
    out, _ = res({(0, y, 0): "twisting_vines_plant" for y in range(2)})
    assert [R.block_id(out[(0, y, 0)]) for y in range(2)] == ["minecraft:twisting_vines_plant", "minecraft:twisting_vines"]
    out, _ = res({(0, y, 0): "weeping_vines" for y in range(2)})                 # weeping vines hang DOWN
    assert [R.block_id(out[(0, y, 0)]) for y in range(2)] == ["minecraft:weeping_vines", "minecraft:weeping_vines_plant"]
    out, _ = res({(0, y, 0): "pale_hanging_moss[tip=true]" for y in range(3)})
    assert [P(out[(0, y, 0)], "tip") for y in range(3)] == ["true", "false", "false"]


def test_pitcher_crop_single_below_age_3():
    _, stats = res({(0, 0, 0): "pitcher_crop[age=1,half=lower]"})
    assert not stats["errors"]
    _, stats = res({(0, 0, 0): "pitcher_crop[age=1,half=lower]", (0, 1, 0): "pitcher_crop[age=1,half=upper]"})
    assert len(stats["errors"]) == 1
    _, stats = res({(0, 0, 0): "pitcher_crop[age=4,half=lower]"})
    assert len(stats["errors"]) == 1


def test_outside_neighbours_are_air():
    out, _ = res({(0, 0, 0): "oak_fence"})
    assert R.props(out[(0, 0, 0)]) == {"east": "false", "north": "false", "south": "false", "waterlogged": "false", "west": "false"}


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
