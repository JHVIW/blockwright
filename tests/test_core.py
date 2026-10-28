"""Core library tests: registry, blocks, Build/Frame/paste, litematic + structure I/O, validate, materials, noise,
finish().  Run: ``python tests/test_core.py`` (or pytest if installed)."""
import gzip
import io
import os
import random
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import nbtlib  # noqa: E402
from nbtlib import Int, IntArray, List, Long, LongArray, String  # noqa: E402

from blockwright import *  # noqa: E402,F401,F403
from blockwright import litematic as L, materials as M, noise as N, registry as R, structure_nbt as S, validate as V  # noqa: E402
from blockwright.build import Build, BuildError, Frame  # noqa: E402

TMP_ROOT = Path(tempfile.gettempdir()) / "blockwright-tests"
TMP = TMP_ROOT / "core"
TMP.mkdir(parents=True, exist_ok=True)


def raises(exc, fn, *a, **kw):
    try:
        fn(*a, **kw)
    except exc as e:
        return e
    raise AssertionError(f"{fn.__name__}{a} did not raise {exc.__name__}")


# ============================================================================================== registry
def test_parse_state_canonical():
    assert R.parse_state("oak_stairs[facing=north]") == \
        "minecraft:oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]"
    assert R.parse_state("minecraft:stone") == "minecraft:stone"
    assert R.parse_state(" oak_stairs [ half = top , facing=east ] ") == \
        "minecraft:oak_stairs[facing=east,half=top,shape=straight,waterlogged=false]"
    # properties come out in registry order regardless of input order
    assert R.parse_state("cobblestone_wall[west=low,up=false]").startswith("minecraft:cobblestone_wall[east=none,north=none")


def test_parse_state_errors_with_suggestions():
    e = raises(ValueError, R.parse_state, "oak_stair[facing=north]")
    assert "oak_stairs" in str(e)
    e = raises(ValueError, R.parse_state, "oak_stairs[facin=north]")
    assert "facing" in str(e) and "Valid properties" in str(e)
    e = raises(ValueError, R.parse_state, "oak_stairs[facing=nort]")
    assert "legal values" in str(e) and "north" in str(e)
    assert "iron_chain" in str(raises(ValueError, R.parse_state, "chain"))
    raises(ValueError, R.parse_state, "oak_stairs[facing=north,facing=south]")
    raises(ValueError, R.parse_state, "oak_stairs[facing]")
    raises(TypeError, R.parse_state, None)


def test_props_block_id_item_with():
    s = R.parse_state("spruce_door[half=upper,facing=west]")
    assert R.block_id(s) == "minecraft:spruce_door"
    assert R.props(s)["facing"] == "west" and R.prop(s, "half") == "upper" and R.prop(s, "axis") is None
    assert R.item("wall_torch[facing=east]") == "minecraft:torch"
    assert R.item("potted_red_tulip") == "minecraft:air"
    assert R.with_props(s, open=True).count("open=true") == 1
    assert R.with_block("oak_stairs[facing=east,half=top]", "stone_brick_stairs") == \
        "minecraft:stone_brick_stairs[facing=east,half=top,shape=straight,waterlogged=false]"
    assert R.make_state("candle", candles=3, lit=True) == "minecraft:candle[candles=3,lit=true,waterlogged=false]"


def test_phys_and_shapes():
    p = R.phys("stone")
    assert p.sturdy_faces == frozenset(R.DIRS) and p.full_collision and p.can_occlude and p.solid_render and p.light == 0
    assert p.collision_boxes == ((0.0, 0.0, 0.0, 1.0, 1.0, 1.0),)
    f = R.phys("oak_fence")
    assert f.sturdy_faces == frozenset() and not f.full_collision and max(b[4] for b in f.collision_boxes) == 1.5
    st = R.phys("oak_stairs[facing=north,half=bottom]")
    assert st.sturdy_faces == frozenset({"down", "north"})
    assert R.phys("lantern").light == 15 and R.phys("torch").collision_boxes == ()
    assert R.is_air("cave_air") and not R.is_air("glass")
    # every state of every block has physics (phys or phys_by_state lookup works)
    for bid in ("minecraft:cobblestone_wall", "minecraft:oak_door", "minecraft:redstone_wire"):
        bi = R.info(bid)
        R.phys(R.make_state(bid))
        assert bi.properties


def test_tags_and_classes():
    assert R.has_tag("oak_fence", "minecraft:fences") and R.has_tag("oak_fence[north=true]", "#fences")
    assert R.has_tag("nether_brick_fence", "fences") and not R.has_tag("nether_brick_fence", "wooden_fences")
    assert R.has_tag("stripped_spruce_log", "minecraft:logs")       # nested #logs_that_burn -> #spruce_logs resolved
    assert "minecraft:poplar_fence" in R.tag_members("wooden_fences")
    raises(ValueError, R.tag_members, "minecraft:fencez")
    assert R.is_a("mangrove_leaves", "LeavesBlock") and R.is_a("cherry_leaves", "LeavesBlock")
    assert R.is_a("white_stained_glass_pane", "IronBarsBlock") and R.is_a("copper_bars", "IronBarsBlock")
    assert R.is_a("lilac", "DoublePlantBlock") and R.is_a("tall_grass", "DoublePlantBlock")
    assert R.is_a("straw_bed", "AbstractBedBlock") and not R.is_a("stone", "StairBlock")
    assert R.TAGS_JSON.exists()


def test_registry_speed_cached():
    import time
    t = time.time()
    for _ in range(20000):
        R.parse_state("oak_stairs[facing=north]")
        R.phys("minecraft:oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
    assert time.time() - t < 1.0


# ================================================================================================ blocks
def test_wood_families_derived():
    assert wood("spruce").log("x") == "minecraft:spruce_log[axis=x]"
    assert wood("crimson").ids["log"] == "minecraft:crimson_stem" and wood("warped").ids["wood"] == "minecraft:warped_hyphae"
    bam = wood("bamboo")
    assert bam.ids["log"] == "minecraft:bamboo_block" and bam.ids["wood"] is None and bam.mosaic == "minecraft:bamboo_mosaic"
    raises(ValueError, bam.wood)
    pop = wood("poplar")
    assert pop.leaves is None and pop.leaves_variants == ["minecraft:orange_poplar_leaves", "minecraft:red_poplar_leaves",
                                                          "minecraft:yellow_poplar_leaves"]
    assert wood("oak").leaves_variants == ["minecraft:oak_leaves"]
    assert wood("oak").leaves == "minecraft:oak_leaves[distance=7,persistent=true,waterlogged=false]"
    assert wood("pale_oak").door == "minecraft:pale_oak_door" and wood("cherry").shelf("south").startswith("minecraft:cherry_shelf[facing=south")
    assert wood("spruce_planks").name == "spruce"
    raises(ValueError, wood, "plastic")


def test_stone_families_derived():
    for name, block, stairs_id, wall_id in [
        ("cobblestone", "cobblestone", "cobblestone_stairs", "cobblestone_wall"),
        ("stone_brick", "stone_bricks", "stone_brick_stairs", "stone_brick_wall"),
        ("stone_bricks", "stone_bricks", "stone_brick_stairs", "stone_brick_wall"),
        ("brick", "bricks", "brick_stairs", "brick_wall"),
        ("deepslate_tile", "deepslate_tiles", "deepslate_tile_stairs", "deepslate_tile_wall"),
        ("mud_brick", "mud_bricks", "mud_brick_stairs", "mud_brick_wall"),
        ("tuff_brick", "tuff_bricks", "tuff_brick_stairs", "tuff_brick_wall"),
        ("polished_tuff", "polished_tuff", "polished_tuff_stairs", "polished_tuff_wall"),
        ("resin_brick", "resin_bricks", "resin_brick_stairs", "resin_brick_wall"),
        ("smooth_stone", "smooth_stone", None, None),
        ("polished_andesite", "polished_andesite", "polished_andesite_stairs", None),
        ("quartz", "quartz_block", "quartz_stairs", None),
    ]:
        f = stone(name)
        assert f.block_id == "minecraft:" + block, (name, f.block_id)
        assert f.stairs_id == (stairs_id and "minecraft:" + stairs_id), (name, f.stairs_id)
        assert f.wall_id == (wall_id and "minecraft:" + wall_id), (name, f.wall_id)
    raises(ValueError, stone("smooth_stone").stairs, "north")
    assert stone("smooth_stone").slab("top") == "minecraft:smooth_stone_slab[type=top,waterlogged=false]"


def test_generic_helpers():
    assert stairs("stone_bricks", "east", "top").startswith("minecraft:stone_brick_stairs[facing=east,half=top")
    assert slab("oak_planks") == "minecraft:oak_slab[type=bottom,waterlogged=false]"
    assert log("crimson", "z") == "minecraft:crimson_stem[axis=z]" and log("stripped_oak_log") == "minecraft:stripped_oak_log[axis=y]"
    assert fence("nether_brick").startswith("minecraft:nether_brick_fence[")
    assert gate("spruce", "west", open=True).startswith("minecraft:spruce_fence_gate[facing=west,in_wall=false,open=true")
    assert trapdoor("iron", "north").startswith("minecraft:iron_trapdoor[facing=north")
    assert lantern(True) == "minecraft:lantern[hanging=true,waterlogged=false]"
    assert lantern(kind="soul").startswith("minecraft:soul_lantern") and lantern(kind="copper").startswith("minecraft:copper_lantern")
    assert candle() == "minecraft:candle[candles=1,lit=true,waterlogged=false]" and "candles=4" in candle("red", 4)
    assert leaves("orange_poplar") == "minecraft:orange_poplar_leaves[distance=7,persistent=true,waterlogged=false]"
    assert vine("north", "up") == "minecraft:vine[east=false,north=true,south=false,up=true,west=false]"
    raises(ValueError, vine, "down")
    assert potted("red_tulip") == "minecraft:potted_red_tulip" and potted("azalea_bush") == "minecraft:potted_azalea_bush"
    raises(ValueError, potted, "oak_log")
    assert campfire() == "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"
    assert chain("x") == "minecraft:iron_chain[axis=x,waterlogged=false]"
    assert barrel("up") == "minecraft:barrel[facing=up,open=false]" and chest("south").startswith("minecraft:chest[facing=south,type=single")
    assert torch() == "minecraft:torch" and torch("east") == "minecraft:wall_torch[facing=east]"
    assert state("oak_trapdoor", facing="east", open=True, half="top").startswith("minecraft:oak_trapdoor[facing=east,half=top,open=true")
    assert pane("light_blue").startswith("minecraft:light_blue_stained_glass_pane[")
    # facing aliases are kept (validated) for Frames only
    s = stairs("oak", "out")
    assert "facing=out" in s and blocks.has_alias(s)
    raises(ValueError, stairs, "oak", "outward")


# ================================================================================================= Build
def test_build_set_get_remove():
    b = Build("t_basic", "T")
    b.set(0, 0, 0, "stone")
    b[1, 0, 0] = "oak_stairs[facing=east]"
    assert b.get(0, 0, 0) == "minecraft:stone" and b[1, 0, 0].startswith("minecraft:oak_stairs[facing=east")
    assert b.get(5, 5, 5) == AIR and (0, 0, 0) in b and (5, 5, 5) not in b and len(b) == 2
    b.set(0, 0, 0, "air")
    assert (0, 0, 0) not in b
    b.set(0, 0, 0, "stone")
    b.remove(0, 0, 0)
    del b[1, 0, 0]
    assert len(b) == 0
    raises(TypeError, b.set, 0.5, 0, 0, "stone")
    raises(TypeError, b.set, 0, 0, 0, None)
    raises(ValueError, b.set, 0, 0, 0, "stonee")
    e = raises(ValueError, b.set, 0, 0, 0, stairs("oak", "out"))
    assert "Frame" in str(e)
    raises(ValueError, Build, "bad slug", "x")
    raises(ValueError, Build, "Upper_COM", "x")


def test_fill_walls_line_shapes():
    b = Build("t_shapes", "T")
    assert b.fill(2, 0, 2, 0, 1, 0, "stone") == 18                       # any corner order, inclusive
    assert b.fill(0, 0, 0, 2, 0, 2, "dirt", where="air") == 0
    assert b.fill(0, 2, 0, 2, 2, 2, "dirt", where="air") == 9
    assert b.fill(0, 0, 0, 2, 2, 2, "glass", where=lambda x, y, z, cur: cur == "minecraft:dirt") == 9
    assert b.count("glass") == 9 and b.count("#minecraft:impermeable") == 9
    b2 = Build("t_walls", "T")
    assert b2.walls(0, 0, 0, 4, 1, 3, "oak_planks") == 2 * (5 * 2 + 2 * 2)
    assert (2, 0, 1) not in b2 and (0, 0, 1) in b2
    b3 = Build("t_line", "T")
    assert b3.line((0, 0, 0), (5, 2, -3), "stone") == 6
    assert (0, 0, 0) in b3 and (5, 2, -3) in b3
    assert b3.line((1, 1, 1), (1, 1, 1), "dirt") == 1
    b4 = Build("t_disk", "T")
    n = b4.disk(0, 0, 0, 3, "stone")
    assert n == len(b4) and (3, 0, 0) in b4 and (-3, 0, 0) in b4 and (0, 0, 3) in b4 and (3, 0, 3) not in b4
    assert all((-x, y, -z) in b4 for (x, y, z) in b4.blocks)              # symmetric
    b5 = Build("t_ring", "T")
    b5.ellipse(0, 0, 0, 4, 2, "stone", filled=False)
    assert (0, 0, 0) not in b5 and (4, 0, 0) in b5 and (0, 0, 2) in b5
    b6 = Build("t_ellipsoid", "T")
    b6.ellipsoid(0, 0, 0, 2, 3, 2, "stone")
    assert (0, 3, 0) in b6 and (0, 4, 0) not in b6 and (2, 0, 0) in b6
    # callable state for per-block variation
    b7 = Build("t_callable", "T")
    b7.fill(0, 0, 0, 3, 0, 0, lambda x, y, z: "stone" if x % 2 else "dirt")
    assert b7.get(0, 0, 0) == "minecraft:dirt" and b7.get(1, 0, 0) == "minecraft:stone"


def test_replace_bounds_palette():
    b = Build("t_replace", "T")
    b.fill(0, 0, 0, 3, 3, 3, "oak_planks")
    b.set(1, 1, 1, "oak_stairs[facing=east,half=top]")
    assert b.replace("oak_planks", "spruce_planks", region=(0, 0, 0, 3, 0, 3)) == 16
    assert b.count("spruce_planks") == 16 and b.count("oak_planks") == 64 - 16 - 1
    assert b.replace("oak_stairs", lambda x, y, z, s: R.with_block(s, "spruce_stairs")) == 1
    assert b.get(1, 1, 1) == "minecraft:spruce_stairs[facing=east,half=top,shape=straight,waterlogged=false]"
    assert b.replace("spruce_stairs[facing=east,half=top]", "air") == 1 and (1, 1, 1) not in b
    assert b.replace("#minecraft:planks", "stone", region=(0, 3, 0, 3, 3, 3)) == 16
    assert b.replace(lambda x, y, z, s: x == 0, "glass") == 16 and b.count("glass") == 16
    assert b.bounds() == ((0, 0, 0), (3, 3, 3)) and b.size() == (4, 4, 4)
    pal = b.palette()
    assert sum(pal.values()) == len(b)


def test_multiblock_helpers():
    b = Build("t_multi", "T")
    b.door(0, 1, 0, "spruce", "north", hinge="right")
    assert b.get(0, 1, 0) == "minecraft:spruce_door[facing=north,half=lower,hinge=right,open=false,powered=false]"
    assert b.get(0, 2, 0) == "minecraft:spruce_door[facing=north,half=upper,hinge=right,open=false,powered=false]"
    b.door(3, 1, 0, "iron", "east")
    assert b.get(3, 2, 0).startswith("minecraft:iron_door[facing=east,half=upper")
    raises(ValueError, b.door, 0, 1, 0, "plastic", "north")
    raises(ValueError, b.door, 0, 1, 0, "oak", "out")
    b.bed(0, 1, 5, "red", "east")                                  # foot at pos, head at pos + facing
    assert b.get(0, 1, 5) == "minecraft:red_bed[facing=east,occupied=false,part=foot]"
    assert b.get(1, 1, 5) == "minecraft:red_bed[facing=east,occupied=false,part=head]"
    b.bed(0, 1, 8, "straw", "north")
    assert b.get(0, 1, 7).startswith("minecraft:straw_bed[facing=north,occupied=false,part=head")
    for plant in ("lilac", "rose_bush", "peony", "sunflower", "tall_grass", "large_fern", "pitcher_plant"):
        b.tall(5, 1, 5, plant)
        assert b.get(5, 1, 5) == f"minecraft:{plant}[half=lower]" and b.get(5, 2, 5) == f"minecraft:{plant}[half=upper]"
    b.tall(6, 1, 6, "small_dripleaf", facing="east")
    assert b.get(6, 2, 6).startswith("minecraft:small_dripleaf[facing=east,half=upper")
    raises(ValueError, b.tall, 0, 0, 0, "poppy")


def test_frame_mapping_all_facings():
    b = Build("t_frame", "T")
    # u = viewer's right, w = outward (toward the viewer), for every facade direction
    expect = {"south": ((1, 0), (0, 1)), "north": ((-1, 0), (0, -1)), "east": ((0, -1), (1, 0)), "west": ((0, 1), (-1, 0))}
    for facing, (u_dir, w_dir) in expect.items():
        f = b.frame((10, 5, 20), facing)
        x, y, z = f.at(1, 0, 0)
        assert (x - 10, z - 20) == u_dir, (facing, "u")
        x, y, z = f.at(0, 0, 1)
        assert (x - 10, z - 20) == w_dir, (facing, "w")
        assert f.at(0, 3, 0) == (10, 8, 20)
        assert f.to_local(*f.at(2, 1, -3)) == (2, 1, -3)
        assert f.dir("out") == facing
        f.set(0, 0, 1, stairs("oak", "out"))
        assert R.prop(b.get(*f.at(0, 0, 1)), "facing") == facing
        assert R.prop(f.get(0, 0, 1), "facing") == "south"            # read back in canonical orientation
        f.set(0, 0, 2, "oak_log[axis=x]")
        assert R.prop(b.get(*f.at(0, 0, 2)), "axis") == ("x" if facing in ("south", "north") else "z")
        f.set(0, 0, 3, "oak_sign[rotation=0]")                         # rotation 0 = facing south
        r = int(R.prop(b.get(*f.at(0, 0, 3)), "rotation"))
        assert r == {"south": 0, "west": 4, "north": 8, "east": 12}[facing]
    raises(ValueError, b.frame, (0, 0, 0), "up")


def test_frame_door_bed_paste_markers():
    b = Build("t_frame2", "T")
    f = b.frame((0, 1, 0), "east")
    f.door(0, 0, 0, "oak")                      # default facing="in": placed from outside -> faces west here
    assert b.get(0, 1, 0).startswith("minecraft:oak_door[facing=west,half=lower")
    f.bed(-3, 0, 0, "blue", "left")             # u=-3 on an east facade = 3 blocks south; "left" = south too
    assert b.get(0, 1, 3).startswith("minecraft:blue_bed[facing=south") and "part=foot" in b.get(0, 1, 3)
    assert "part=head" in b.get(0, 1, 4)
    f.entrance(0, 0, 1)                         # one block outward = east
    f.room("hall", -2, 0, -1)                   # 2 to the viewer's left (south), 1 inward (west)
    assert b.entrances == [(1, 1, 0)] and b.rooms == {"hall": (-1, 1, 2)}
    prefab = Build("t_prefab", "P")
    prefab.set(0, 0, 0, "oak_stairs[facing=north]")
    prefab.set(1, 0, 0, "stone")
    g = b.frame((10, 0, 10), "west")
    g.paste(prefab, (0, 0, 0))
    # canonical +u lands on world +z for a west facade; stairs facing north (= in) end up facing east (= in)
    assert b.get(10, 0, 11) == "minecraft:stone"
    assert R.prop(b.get(10, 0, 10), "facing") == "east"
    nested = g.frame((5, 0, 0), "west")         # west relative to a west frame = north
    assert nested.facing == "north" and nested.origin == (10, 0, 15)


def test_paste_rotation_and_mirror_geometry():
    proto = Build("t_proto", "P")
    proto.set(0, 0, 0, "oak_stairs[facing=east]")   # stair whose back points at the block east of it
    proto.set(1, 0, 0, "stone")
    for rot in range(4):
        for mirror in (None, "x", "z"):
            b = Build("t_paste", "T")
            assert b.paste(proto, (5, 0, 5), rot=rot, mirror=mirror) == 2
            (sp,) = [p for p, s in b.blocks.items() if "stairs" in s]
            (stp,) = [p for p, s in b.blocks.items() if s == "minecraft:stone"]
            assert sp == (5, 0, 5)
            f = R.prop(b.blocks[sp], "facing")
            off = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[f]
            assert (sp[0] + off[0], sp[2] + off[1]) == (stp[0], stp[2]), (rot, mirror)  # still points at the stone
    b = Build("t_paste2", "T")
    b.paste(proto, (0, 0, 0), rot=1)
    assert b.get(0, 0, 1) == "minecraft:stone"                   # east rotated clockwise -> south
    raises(ValueError, b.paste, proto, (0, 0, 0), mirror="y")


def test_structure_normalization():
    b = Build("t_norm", "T", ground=-3)
    b.fill(-5, -4, 10, -3, -2, 12, "stone")
    b.room("r", -4, -1, 11)
    b.entrance(-4, -1, 13)
    blocks, size, meta, stats = b.structure()
    assert size == (3, 3, 3) and min(blocks) == (0, 0, 0)
    assert meta["ground"] == 1 and meta["rooms"]["r"] == (1, 3, 1) and meta["entrances"] == [(1, 3, 3)]
    assert meta["origin_offset"] == (-5, -4, 10)


# ============================================================================================ litematic
def test_bits_and_long_count():
    assert [L.bits_for(n) for n in (1, 2, 3, 4, 5, 8, 9, 16, 17, 64, 65, 82, 256, 257)] == \
        [2, 2, 2, 2, 3, 3, 4, 4, 5, 6, 7, 7, 8, 9]
    assert L.long_count(10, 2) == 1 and L.long_count(32, 2) == 1 and L.long_count(33, 2) == 2
    assert L.long_count(64, 7) == 7 and L.long_count(0, 2) == 1


def test_pack_unpack_spanning():
    assert L.pack([1, 2, 3], 2) == [0b111001]
    # worked example from docs/litematic-format.md (5 bits, cells 1..14, cell 12 straddles the two longs)
    five = L.pack(list(range(1, 15)), 5)
    assert [v & (2**64 - 1) for v in five] == [0xD62D4941CC520C41, 0x1C]
    # 7 bits: entry 9 occupies bits 63..69 -> spans long 0 (bit 63) and long 1 (bits 0..5)
    idx = [0] * 20
    idx[9] = 0x7F
    longs = L.pack(idx, 7)
    assert longs[0] == -(1 << 63) and longs[1] == 0b111111
    assert L.unpack(longs, 7, 20) == idx
    rnd = random.Random(5)
    for bits in range(2, 13):
        vals = [rnd.randrange(1 << bits) for _ in range(997)]
        packed = L.pack(vals, bits)
        assert len(packed) == L.long_count(997, bits)
        assert all(-(1 << 63) <= v < (1 << 63) for v in packed)
        assert L.unpack(packed, bits, 997) == vals


def _sample_blocks(seed=1, n=(6, 5, 7), density=0.5):
    rnd = random.Random(seed)
    ids = ["stone", "oak_planks", "glass", "oak_log[axis=x]", "spruce_stairs[facing=east,half=top]", "torch",
           "grass_block", "red_wool", "lantern[hanging=true]", "cobblestone_wall"]
    out = {}
    for x in range(n[0]):
        for y in range(n[1]):
            for z in range(n[2]):
                if rnd.random() < density:
                    out[(x, y, z)] = R.parse_state(rnd.choice(ids))
    out[(n[0] - 1, n[1] - 1, n[2] - 1)] = "minecraft:stone"
    return out, n


def test_litematic_roundtrip_and_tags():
    blocks, size = _sample_blocks()
    p = TMP / "rt.litematic"
    info = L.write_litematic(p, blocks, size, name="RT", author="tester", description="hello", ground=2, time_ms=123)
    raw = p.read_bytes()
    assert raw[:2] == b"\x1f\x8b" and raw[4:8] == b"\x00\x00\x00\x00"        # gzip, mtime 0
    root = nbtlib.File.parse(io.BytesIO(gzip.decompress(raw)))
    assert root.root_name == ""
    assert isinstance(root["MinecraftDataVersion"], Int) and int(root["MinecraftDataVersion"]) == 5023
    assert isinstance(root["Version"], Int) and int(root["Version"]) == 7 and int(root["SubVersion"]) == 1
    m = root["Metadata"]
    for k, cls in (("Name", String), ("Author", String), ("Description", String), ("RegionCount", Int),
                   ("TotalVolume", Int), ("TotalBlocks", Int), ("TimeCreated", Long), ("TimeModified", Long)):
        assert isinstance(m[k], cls), k
    assert int(m["TotalBlocks"]) == len(blocks) and int(m["TotalVolume"]) == 6 * 5 * 7 and int(m["TimeCreated"]) == 123
    assert str(m["Description"]) == "hello\nground layer: y=2 from the bottom"
    reg = root["Regions"]["RT"]
    pal = reg["BlockStatePalette"]
    assert dict(pal[0]) == {"Name": "minecraft:air"}
    for t in pal:
        bid = str(t["Name"])
        assert ("Properties" in t) == bool(R.info(bid).properties)
    assert isinstance(reg["BlockStates"], LongArray) and len(reg["BlockStates"]) == L.long_count(210, L.bits_for(len(pal)))
    for k in ("TileEntities", "Entities", "PendingBlockTicks", "PendingFluidTicks"):
        assert isinstance(reg[k], List) and len(reg[k]) == 0
    assert {k: int(v) for k, v in reg["Size"].items()} == {"x": 6, "y": 5, "z": 7}
    rb, rsize, meta = L.read_litematic(p)
    assert rb == blocks and rsize == size and meta["ground"] == 2 and meta["name"] == "RT"
    assert V.validate_file(p, expected=(blocks, size))["ok"]
    assert info["total_blocks"] == len(blocks)


def test_litematic_determinism_and_time_env():
    blocks, size = _sample_blocks(3)
    a, b = TMP / "det_a.litematic", TMP / "det_b.litematic"
    L.write_litematic(a, blocks, size, name="D", author="x", time_ms=99)
    L.write_litematic(b, dict(reversed(list(blocks.items()))), size, name="D", author="x", time_ms=99)
    assert a.read_bytes() == b.read_bytes()
    os.environ["CC_TIME_MS"] = "4242"
    try:
        L.write_litematic(a, blocks, size, name="D", author="x")
    finally:
        del os.environ["CC_TIME_MS"]
    assert L.read_litematic(a)[2]["time_created"] == 4242


def test_preview_image():
    from PIL import Image
    img = Image.new("RGBA", (300, 200), (10, 200, 30, 255))
    argb = L.preview_from_image(img)
    assert len(argb) == 120 * 120 and argb[0] == 0xFF0AC81E
    blocks, size = _sample_blocks(4)
    p = TMP / "prev.litematic"
    L.write_litematic(p, blocks, size, name="P", author="a", preview_argb=argb, time_ms=1)
    meta = L.read_litematic(p)[2]
    assert meta["preview_argb"] == argb
    root = L.load_nbt(p)
    assert isinstance(root["Metadata"]["PreviewImageData"], IntArray)
    raises(ValueError, L.write_litematic, p, blocks, size, name="P", author="a", preview_argb=[1, 2, 3])


def test_validate_file_detects_corruption():
    blocks, size = _sample_blocks(6)
    good = TMP / "good.litematic"
    L.write_litematic(good, blocks, size, name="G", author="a", time_ms=1)

    def mutate(fn, name):
        root = L.load_nbt(good)
        fn(root)
        q = TMP / name
        q.write_bytes(L.encode(root))
        return V.validate_file(q, expected=(blocks, size))

    def first_not_air(r):
        reg = next(iter(r["Regions"].values()))
        pal = reg["BlockStatePalette"]
        pal[0], pal[1] = pal[1], pal[0]

    assert not mutate(first_not_air, "c1.litematic")["ok"]
    assert not mutate(lambda r: next(iter(r["Regions"].values())).__setitem__(
        "BlockStates", LongArray(list(next(iter(r["Regions"].values()))["BlockStates"])[:-1])), "c2.litematic")["ok"]
    assert not mutate(lambda r: r["Metadata"].__setitem__("TotalBlocks", Int(1)), "c3.litematic")["ok"]
    assert not mutate(lambda r: r.__setitem__("Version", Long(7)), "c4.litematic")["ok"]

    def partial_props(r):
        reg = next(iter(r["Regions"].values()))
        for t in reg["BlockStatePalette"]:
            if "Properties" in t and len(t["Properties"]) > 1:
                del t["Properties"][next(iter(t["Properties"]))]
                return

    rep = mutate(partial_props, "c5.litematic")
    assert not rep["ok"] and any("properties" in e for e in rep["errors"])
    assert V.validate_file(good, expected=(blocks, size))["ok"]
    other = dict(blocks)
    other.pop(next(iter(other)))
    assert not V.validate_file(good, expected=(other, size))["ok"]


def test_structure_nbt_format():
    blocks, size = _sample_blocks(7)
    p = TMP / "s.nbt"
    S.write_structure(p, blocks, size)
    root = L.load_nbt(p)
    assert int(root["DataVersion"]) == 5023 and [int(v) for v in root["size"]] == list(size)
    for t in root["palette"]:
        assert "id" in t and "Name" not in t and "Properties" not in t
        assert ("properties" in t) == bool(R.info(str(t["id"])).properties)
    assert len(root["blocks"]) == len(blocks) and isinstance(root["entities"], List)
    e = root["blocks"][0]
    assert isinstance(e["pos"], List) and isinstance(e["state"], Int)
    rb, rs, dv = S.read_structure(p)
    assert rb == blocks and rs == size and dv == 5023


# ============================================================================================= validate
def test_validate_structure_markers():
    blocks = {(0, 0, 0): "minecraft:stone", (0, 1, 0): "minecraft:stone"}
    assert V.validate_structure(blocks, (1, 2, 1), {"rooms": {}, "entrances": [], "ground": 0}) == []
    probs = V.validate_structure(blocks, (1, 2, 1), {"rooms": {"r": (0, 0, 0)}, "entrances": [(0, 1, 0)], "ground": 0})
    assert len(probs) >= 3
    assert V.validate_structure({(0, 0, 0): "stone"}, (1, 1, 1))     # non-canonical
    assert V.validate_structure({(2, 0, 0): "minecraft:stone"}, (1, 1, 1))


# ============================================================================================ materials
def test_materials_rules():
    b = {(0, 0, 0): "oak_door[half=lower]", (0, 1, 0): "oak_door[half=upper]", (1, 0, 0): "red_bed[part=foot]",
         (1, 0, 1): "red_bed[part=head]", (2, 0, 0): "stone_slab[type=double]", (3, 0, 0): "pink_candle[candles=3]",
         (4, 0, 0): "potted_azalea_bush", (5, 0, 0): "wall_torch", (6, 0, 0): "water", (7, 0, 0): "oak_stairs[waterlogged=true]",
         (8, 0, 0): "cave_vines_plant", (9, 0, 0): "barrier", (10, 0, 0): "lilac[half=lower]", (10, 1, 0): "lilac[half=upper]",
         (11, 0, 0): "farmland", (12, 0, 0): "red_candle_cake", (13, 0, 0): "pink_petals[flower_amount=4]",
         (14, 0, 0): "leaf_litter[segment_amount=2]", (15, 0, 0): "sea_pickle[pickles=3]", (16, 0, 0): "potted_red_tulip",
         (17, 0, 0): "wheat", (18, 0, 0): "spruce_wall_sign", (19, 0, 0): "kelp_plant", (20, 0, 0): "wildflowers[flower_amount=2]"}
    r = M.material_list({k: R.parse_state(v) for k, v in b.items()})
    it = r["items"]
    assert it["minecraft:oak_door"] == 1 and it["minecraft:red_bed"] == 1 and it["minecraft:stone_slab"] == 2
    assert it["minecraft:pink_candle"] == 3 and it["minecraft:flower_pot"] == 2 and it["minecraft:azalea"] == 1
    assert it["minecraft:red_tulip"] == 1 and it["minecraft:torch"] == 1
    assert it["minecraft:water_bucket"] == 3            # water source + waterlogged stairs + sea_pickle (waterlogged by default)
    assert it["minecraft:glow_berries"] == 1 and it["minecraft:lilac"] == 1 and it["minecraft:dirt"] == 1
    assert it["minecraft:cake"] == 1 and it["minecraft:red_candle"] == 1 and it["minecraft:pink_petals"] == 4
    assert it["minecraft:leaf_litter"] == 2 and it["minecraft:sea_pickle"] == 3 and it["minecraft:wheat_seeds"] == 1
    assert it["minecraft:spruce_sign"] == 1 and it["minecraft:kelp"] == 1 and it["minecraft:wildflowers"] == 2
    assert "minecraft:barrier" not in it and any("barrier" in w for w in r["warnings"])
    assert M.stacks(130, "minecraft:stone") == "2 x 64 + 2" and M.stacks(20, "minecraft:oak_sign") == "1 x 16 + 4"
    assert M.stack_size("minecraft:red_bed") == 1 and M.stack_size("minecraft:straw_bed") == 16
    assert M.group_of("minecraft:oak_planks") == "wood" and M.group_of("minecraft:glass_pane") == "glass"
    assert M.group_of("minecraft:spruce_stairs") == "roofing" and M.group_of("minecraft:lantern") == "decor & lighting"
    assert M.group_of("minecraft:red_bed") == "furniture & utility" and M.group_of("minecraft:lilac") == "plants & landscaping"
    assert M.group_of("minecraft:cobblestone") == "structure / stone"
    md = M.to_markdown(r, "x")
    assert "| stone_slab | 2 | 2 |" in md and "## warnings" in md


# ================================================================================================ noise
def test_noise_deterministic_and_smooth():
    assert N.hash3(1, 2, 3, 4) == N.hash3(1, 2, 3, 4) and N.hash3(1, 2, 3, 4) != N.hash3(1, 2, 3, 5)
    vals = [N.hash01(x, 0, 0) for x in range(2000)]
    assert 0 <= min(vals) and max(vals) < 1 and 0.45 < sum(vals) / len(vals) < 0.55
    sm = [N.value3(x, 0, 0, seed=3, scale=4) for x in range(400)]
    assert all(0 <= v <= 1 for v in sm)
    jump_smooth = sum(abs(a - b) for a, b in zip(sm, sm[1:])) / 399
    jump_white = sum(abs(a - b) for a, b in zip(vals, vals[1:])) / 1999
    assert jump_smooth < jump_white / 2.5                               # value noise is not white noise
    assert all(0 <= N.fbm2(x, x * 3, 1) <= 1 for x in range(100))
    bands = [(0, "a"), (3, "b"), (6, "c")]
    assert [N.gradient(bands, 0, y, 0, jitter=0) for y in range(-1, 8)] == list("aaaabbbcc")
    g = [N.gradient(bands, x, 3, 0, seed=2, jitter=1.5) for x in range(60)]
    assert set(g) <= {"a", "b", "c"} and len(set(g)) >= 2
    assert N.pick(["x", "y"], 1, 2, 3) == N.pick(["x", "y"], 1, 2, 3)
    assert sum(N.chance(0.25, x, 0, 0, 9) for x in range(4000)) in range(850, 1150)


# =============================================================================================== finish
def test_finish_end_to_end_and_strict():
    out = TMP / "finish_out"
    if out.exists():
        shutil.rmtree(out)
    b = Build("t_finish", "Finish Test", ground=0)
    b.fill(0, 0, 0, 4, 0, 4, "cobblestone")
    b.walls(0, 1, 0, 4, 3, 4, "oak_planks")
    b.fill(0, 4, 0, 4, 4, 4, "spruce_planks")
    b.door(2, 1, 4, "oak", "north")
    b.room("inside", 2, 1, 2)
    b.entrance(2, 1, 5)
    res = b.finish(argv=["--no-render", "--no-qa"], out_dir=out)
    assert Path(res["litematic"]).exists() and Path(res["structure"]).exists() and Path(res["materials"]).exists()
    blocks, size, meta = L.read_litematic(res["litematic"])
    assert size == (5, 5, 5) and meta["ground"] == 0 and len(blocks) == res["blocks"]
    # strict validation: unpaired door half and a room marker inside a wall
    bad = Build("t_finish_bad", "Bad")
    bad.fill(0, 0, 0, 2, 0, 2, "stone")
    bad.set(1, 1, 1, "oak_door[half=lower]")
    bad.room("wall", 0, 0, 0)
    e = raises(BuildError, bad.finish, argv=["--no-render", "--no-qa"], out_dir=out)
    assert "no matching upper half" in str(e) and "room 'wall'" in str(e)
    res2 = bad.finish(argv=["--no-render", "--no-qa", "--lenient"], out_dir=out)
    assert res2["warnings"]


# ====================================================================================== review additions
def test_tall_matches_player_placement():
    b = Build("t_tall", "T")
    # SmallDripleafBlock.setPlacedBy: upper = default.setValue(HALF, UPPER).setValue(FACING, lower facing), waterlogged
    # copied from the WORLD at the upper position (copyWaterloggedFrom) -> dry unless asked
    b.tall(0, 1, 0, "small_dripleaf", facing="east", waterlogged=True)
    assert b.get(0, 1, 0) == "minecraft:small_dripleaf[facing=east,half=lower,waterlogged=true]"
    assert b.get(0, 2, 0) == "minecraft:small_dripleaf[facing=east,half=upper,waterlogged=false]"
    b.tall(1, 1, 0, "small_dripleaf", facing="west", waterlogged=True, upper_waterlogged=True)
    assert b.get(1, 2, 0) == "minecraft:small_dripleaf[facing=west,half=upper,waterlogged=true]"
    b.tall(2, 1, 0, "pitcher_crop", age=4)                         # PitcherCropBlock.isDouble(age >= 3)
    assert b.get(2, 2, 0) == "minecraft:pitcher_crop[age=4,half=upper]"
    raises(ValueError, b.tall, 3, 1, 0, "pitcher_crop", age=1)     # one block below age 3
    f = b.frame((10, 1, 10), "west")
    f.tall(0, 0, 0, "small_dripleaf", facing="out")
    assert R.prop(b.get(10, 2, 10), "facing") == "west"


def test_double_chest_helper_pairs_like_the_game():
    from blockwright.resolve import resolve
    for facing, side, other in (("north", "east", (1, 0, 0)), ("north", "west", (-1, 0, 0)),
                                ("east", "south", (0, 0, 1)), ("west", "south", (0, 0, 1))):
        b = Build("t_chest", "T")
        b.double_chest(0, 0, 0, facing, side)
        a, c = b.get(0, 0, 0), b.get(*other)
        assert R.prop(a, "type") != "single" and R.prop(c, "type") != "single" and R.prop(a, "type") != R.prop(c, "type")
        out, stats = resolve(b.blocks)
        assert out == b.blocks and not stats["warnings"], (facing, side, stats)   # already what the game keeps
    b = Build("t_chest2", "T")
    raises(ValueError, b.double_chest, 0, 0, 0, "north", "south")               # not perpendicular
    raises(ValueError, b.double_chest, 0, 0, 0, "north", "east", kind="ender_chest")
    raises(ValueError, b.double_chest, 0, 0, 0, "out", "left")                  # aliases only in a Frame
    f = b.frame((5, 0, 5), "east")
    f.double_chest(0, 0, 0, "out", "right", kind="trapped_chest")               # right = north on an east facade
    assert R.prop(b.get(5, 0, 5), "facing") == "east" and b.get(5, 0, 4).startswith("minecraft:trapped_chest")
    assert resolve(b.blocks)[0] == b.blocks


def test_paste_carries_tile_entities_and_frame_markers():
    proto = Build("t_te", "P")
    proto.set(1, 0, 0, "barrel[facing=up]")
    proto.tile_entity(1, 0, 0, nbtlib.Compound({"CustomName": String('"x"')}))
    proto.room("nook", 0, 0, 0)
    b = Build("t_te2", "T")
    b.paste(proto, (10, 0, 10), rot=1)
    assert list(b.tile_entities) == [(10, 0, 11)]
    b.paste(proto, (20, 0, 20), where=lambda x, y, z, cur: x != 21)            # filtered block -> no tile entity
    assert (21, 0, 20) not in b.tile_entities
    f = b.frame((0, 0, 0), "north")
    f.paste(proto, (0, 0, 0), markers=True)
    assert b.rooms == {"nook": (0, 0, 0)}
    n = len(b.blocks)
    raises(ValueError, f.paste, proto, (5, 0, 0), markers=True)                # duplicate room name
    assert len(b.blocks) == n                                                  # ... rejected before pasting


def test_review_registry_and_helper_traps():
    raises(ValueError, has_tag, "chain", "minecraft:fences")       # unknown id must not silently answer False
    assert has_tag("oak_fence", "minecraft:fences") and has_tag("minecraft:oak_fence", "#fences")
    assert glass("tinted") == "minecraft:tinted_glass"
    b = Build("t_count", "T")
    b.set(0, 0, 0, "oak_stairs[facing=east]")
    b.set(1, 0, 0, "oak_stairs[facing=west]")
    assert b.count("oak_stairs") == 2 and b.count("oak_stairs[facing=east]") == 1
    assert prop("oak_planks", "facing") is None                     # real property, block lacks it
    raises(ValueError, prop, "oak_stairs", "facng")                 # no block has it -> typo
    raises(ValueError, L.write_litematic, TMP / "t0.litematic", {(0, 0, 0): "stone"}, (1, 1, 1), name="x", author="y",
           time_ms=0)                                               # Litematica drops TimeCreated <= 0
    b2 = Build("t_empty", "T")
    b2.set(0, 0, 0, "vine[north=true]")                             # removed by resolve -> nothing to export
    raises(BuildError, b2.structure)


def test_read_litematic_prefers_lowercase_id_like_litematica():
    p = TMP / "lower_id.litematic"
    L.write_litematic(p, {(0, 0, 0): "minecraft:stone"}, (1, 1, 1), name="x", author="y", time_ms=1)
    root = L.load_nbt(p)
    pal = root["Regions"]["x"]["BlockStatePalette"]
    pal[1]["id"] = String("minecraft:dirt")                         # DataTypeUtils.readBlockStateFromTag: id wins
    p.write_bytes(L.encode(root))
    blocks, _size, _meta = L.read_litematic(p)
    assert blocks == {(0, 0, 0): "minecraft:dirt"}


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
