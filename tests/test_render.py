"""Tests for blockwright.render. Run: python -m pytest tests/test_render.py -q   (or: python tests/test_render.py)

`make_test_scene()` builds the renderer acceptance scene (stairs in every orientation/half/shape, slabs, logs,
fences/walls/panes/bars, doors, trapdoors, lanterns, plants, leaves, vines, water, glass, furniture...).
`python tests/test_render.py --render` renders it to <tempdir>/blockwright-tests/render/test_scene/.
"""
from __future__ import annotations

import math
import pathlib
import sys
import time

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
import tempfile  # noqa: E402
TMP_ROOT = pathlib.Path(tempfile.gettempdir()) / "blockwright-tests"
sys.path.insert(0, str(ROOT))

from blockwright.render import models, render_view, render_views  # noqa: E402
from blockwright.render.litematic_io import decode_bits  # noqa: E402
from blockwright.render.mesh import build_scene, state_info, tint_colors  # noqa: E402
from blockwright.render.views import detect_storeys  # noqa: E402


# ----------------------------------------------------------------------------------------------
# test scene


def make_test_scene():
    B: dict = {}

    def put(x, y, z, s):
        B[(x, y, z)] = s if s.startswith("minecraft:") else "minecraft:" + s

    W, D = 44, 40
    # ground: cobblestone floor pad + dirt path strip (terrain grass is synthesised around it)
    for x in range(W):
        for z in range(D):
            put(x, 0, z, "stone_bricks" if (x + z) % 7 else "mossy_stone_bricks")
    for x in range(W):
        put(x, 0, 18, "dirt_path")

    # --- stairs: rows per facing, columns shape x half
    shapes = ["straight", "inner_left", "inner_right", "outer_left", "outer_right"]
    for fi, facing in enumerate(["north", "east", "south", "west"]):
        for si, shape in enumerate(shapes):
            for hi, half in enumerate(["bottom", "top"]):
                x = 1 + (si * 2 + hi) * 2
                z = 1 + fi * 2
                mat = "oak_stairs" if half == "bottom" else "spruce_stairs"
                put(x, 1 + hi, z, f"{mat}[facing={facing},half={half},shape={shape},waterlogged=false]")
    # --- slabs / logs
    put(22, 1, 1, "oak_slab[type=bottom]")
    put(24, 1, 1, "oak_slab[type=top]")
    put(26, 1, 1, "oak_slab[type=double]")
    put(22, 1, 3, "oak_log[axis=y]")
    put(24, 1, 3, "oak_log[axis=x]")
    put(26, 1, 3, "oak_log[axis=z]")
    put(28, 1, 3, "birch_log[axis=x]")
    put(30, 1, 3, "stripped_spruce_log[axis=z]")
    # --- fences / walls / panes / bars (lines with connections)
    for x in range(22, 27):
        e = "true" if x < 26 else "false"
        w = "true" if x > 22 else "false"
        put(x, 1, 6, f"oak_fence[east={e},west={w},north=false,south=false]")
        ew = "low" if x < 26 else "none"
        ww = "low" if x > 22 else "none"
        up = "true" if x in (22, 24, 26) else "false"
        put(x, 1, 8, f"cobblestone_wall[east={ew},west={ww},north=none,south=none,up={up}]")
        put(x, 1, 10, f"glass_pane[east={e},west={w},north=false,south=false]")
        put(x, 1, 12, f"iron_bars[east={e},west={w},north=false,south=false]")
    put(28, 1, 6, "oak_fence[north=false,south=true,east=false,west=false]")
    put(28, 1, 7, "oak_fence[north=true,south=false,east=true,west=false]")
    put(29, 1, 7, "oak_fence[north=false,south=false,east=false,west=true]")
    put(28, 1, 10, "glass_pane[north=false,south=true,east=true,west=false]")
    put(29, 1, 10, "glass_pane[north=false,south=false,east=false,west=true]")
    put(28, 1, 11, "glass_pane[north=true,south=false,east=false,west=false]")
    put(31, 1, 6, "oak_fence_gate[facing=south,open=false,in_wall=false]")
    put(33, 1, 6, "oak_fence_gate[facing=south,open=true,in_wall=false]")
    # --- doors (facing south) hinge left/right, open/closed
    for i, (hinge, opn) in enumerate([("left", "false"), ("right", "false"), ("left", "true"), ("right", "true")]):
        x = 1 + i * 3
        put(x, 1, 21, f"oak_door[facing=south,half=lower,hinge={hinge},open={opn}]")
        put(x, 2, 21, f"oak_door[facing=south,half=upper,hinge={hinge},open={opn}]")
        put(x + 13, 1, 21, f"spruce_door[facing=east,half=lower,hinge={hinge},open={opn}]")
        put(x + 13, 2, 21, f"spruce_door[facing=east,half=upper,hinge={hinge},open={opn}]")
    # --- trapdoors
    for i, (half, opn, facing) in enumerate([("bottom", "false", "north"), ("top", "false", "north"),
                                             ("bottom", "true", "north"), ("bottom", "true", "south"),
                                             ("top", "true", "east"), ("bottom", "true", "west")]):
        put(28 + i * 2, 1, 21, f"spruce_trapdoor[facing={facing},half={half},open={opn}]")
    # --- lanterns: standing + hanging from a beam
    put(1, 1, 25, "lantern[hanging=false]")
    put(3, 1, 25, "soul_lantern[hanging=false]")
    for x in range(5, 10):
        put(x, 4, 25, "oak_planks")
    put(6, 3, 25, "lantern[hanging=true]")
    put(8, 3, 25, "iron_chain[axis=y]")
    put(8, 2, 25, "copper_lantern[hanging=true]")
    # --- plants
    flowers = ["poppy", "dandelion", "cornflower", "oxeye_daisy", "allium", "lily_of_the_valley", "short_grass",
               "fern", "bush", "firefly_bush", "sweet_berry_bush[age=3]"]
    for i, f in enumerate(flowers):
        put(12 + i, 0, 25, "grass_block[snowy=false]")
        put(12 + i, 1, 25, f)
    for i, f in enumerate(["rose_bush", "sunflower", "lilac", "peony", "tall_grass", "large_fern"]):
        put(12 + i, 0, 27, "grass_block[snowy=false]")
        put(12 + i, 1, 27, f"{f}[half=lower]")
        put(12 + i, 2, 27, f"{f}[half=upper]")
    put(24, 1, 25, "pink_petals[facing=north,flower_amount=4]")
    put(25, 1, 25, "wildflowers[facing=east,flower_amount=3]")
    put(26, 1, 25, "leaf_litter[facing=south,segment_amount=4]")
    # --- leaves
    for i, lv in enumerate(["oak_leaves", "birch_leaves", "spruce_leaves", "cherry_leaves", "azalea_leaves",
                            "flowering_azalea_leaves", "yellow_poplar_leaves", "orange_poplar_leaves",
                            "red_poplar_leaves"]):
        x = 1 + i * 2
        put(x, 1, 29, f"{lv}[persistent=true]")
        put(x, 2, 29, f"{lv}[persistent=true]")
        put(x + 1, 1, 29, f"{lv}[persistent=true]")
    # --- vines on a wall
    for y in range(1, 5):
        for x in range(20, 24):
            put(x, y, 29, "bricks")
        put(21, y, 30, "vine[north=true,east=false,south=false,west=false,up=false]")
        put(22, y, 30, "vine[north=true,east=false,south=false,west=false,up=false]")
    # --- water pool with glass + stained glass
    for x in range(26, 34):
        for z in range(26, 32):
            edge = x in (26, 33) or z in (26, 31)
            put(x, 0, z, "stone_bricks" if edge else "sand")
            if not edge:
                put(x, 1, z, "water[level=0]")
            else:
                put(x, 1, z, "stone_brick_slab[type=bottom]")
    put(28, 0, 28, "sand")
    put(28, 1, 28, "seagrass")
    put(30, 1, 29, "oak_stairs[facing=west,half=bottom,shape=straight,waterlogged=true]")
    put(31, 1, 27, "lily_pad") if False else None
    put(31, 2, 28, "lily_pad")
    for y in range(1, 4):
        put(35, y, 26, "glass")
        put(35, y, 27, "glass")
        put(37, y, 26, "red_stained_glass")
        put(37, y, 27, "light_blue_stained_glass")
        put(39, y, 26, "tinted_glass")
    put(39, 1, 28, "glass_pane[north=true,south=true,east=false,west=false]")
    put(41, 1, 26, "white_stained_glass_pane[north=false,south=false,east=true,west=true]")
    # --- furniture & block entities
    put(1, 1, 33, "red_bed[facing=south,part=head]")
    put(1, 1, 34, "red_bed[facing=south,part=foot]")
    put(3, 1, 33, "light_blue_bed[facing=east,part=foot]")
    put(4, 1, 33, "light_blue_bed[facing=east,part=head]")
    put(6, 1, 33, "chest[facing=south,type=single]")
    put(8, 1, 33, "chest[facing=east,type=single]")
    put(11, 1, 33, "chest[facing=south,type=left]")
    put(10, 1, 33, "chest[facing=south,type=right]")
    put(13, 1, 33, "barrel[facing=up,open=false]")
    put(14, 1, 33, "barrel[facing=north,open=false]")
    put(16, 1, 33, "campfire[facing=south,lit=true]")
    put(18, 1, 33, "brown_mushroom_block[up=true,down=false,north=true,south=true,east=true,west=true]")
    put(19, 1, 33, "red_mushroom_block[up=true,down=false,north=true,south=true,east=true,west=true]")
    put(20, 1, 33, "mushroom_stem[up=false,down=false,north=true,south=true,east=true,west=true]")
    put(22, 1, 33, "candle[candles=1,lit=true]")
    put(23, 1, 33, "white_candle[candles=3,lit=false]")
    put(24, 1, 33, "red_candle[candles=4,lit=true]")
    put(26, 1, 33, "potted_poppy")
    put(27, 1, 33, "potted_fern")
    put(28, 1, 33, "flower_pot")
    put(30, 1, 33, "bell[attachment=floor,facing=south]")
    for x in (32, 33, 34):
        put(x, 1, 33, "white_carpet" if x != 33 else "red_carpet")
    put(36, 1, 33, "oak_sign[rotation=0]")
    put(37, 1, 33, "oak_sign[rotation=2]")
    put(38, 2, 32, "oak_planks")
    put(38, 2, 33, "oak_wall_sign[facing=south]")
    put(38, 1, 35, "oak_planks")
    put(39, 3, 35, "oak_planks")
    put(39, 2, 35, "oak_hanging_sign[attached=false,rotation=0]")
    put(1, 1, 37, "lectern[facing=south,has_book=true]")
    put(3, 1, 37, "decorated_pot[facing=south]")
    put(5, 1, 37, "white_banner[rotation=0]")
    put(7, 2, 36, "stone_bricks")
    put(7, 2, 37, "blue_wall_banner[facing=south]")
    put(9, 1, 37, "skeleton_skull[rotation=0]")
    put(11, 1, 37, "enchanting_table")
    put(13, 1, 37, "oak_shelf[facing=south,side_chain=unconnected]")
    put(15, 1, 37, "crafting_table")
    put(17, 1, 37, "furnace[facing=south,lit=false]")
    put(19, 1, 37, "composter[level=0]")
    put(21, 1, 37, "hay_block[axis=y]")
    put(23, 1, 37, "bookshelf")
    put(25, 1, 37, "torch")
    put(27, 2, 36, "stone_bricks")
    put(27, 2, 37, "wall_torch[facing=south]")
    put(29, 1, 37, "shulker_box[facing=up]")
    put(31, 1, 37, "grindstone[face=floor,facing=south]")
    put(33, 1, 37, "smoker[facing=south]")
    put(35, 1, 37, "red_banner[rotation=4]")
    return B, (W, 6, D), {"slug": "render_test", "title": "renderer test scene", "ground": 0,
                          "rooms": {}, "entrances": [(4, 1, 21)]}


# ----------------------------------------------------------------------------------------------
# unit tests


def _bake(state):
    bid, props = models.parse_state(state)
    props = models.full_props(bid, props)
    return models.bake_state(bid, props)[0]


def test_stairs_tall_back_matches_facing():
    for facing, axis, sign in [("north", 2, -1), ("south", 2, 1), ("west", 0, -1), ("east", 0, 1)]:
        q = _bake(f"minecraft:oak_stairs[facing={facing},half=bottom,shape=straight]")
        upper = q.pos[(q.pos[:, :, 1].min(1) >= 0.5 - 1e-6)]
        c = upper[:, :, axis].mean()
        assert (c - 0.5) * sign > 0, (facing, c)


def test_top_stairs_upside_down():
    q = _bake("minecraft:oak_stairs[facing=north,half=top,shape=straight]")
    # full slab part must be the upper half
    tops = q.pos[(q.face == 1)]
    assert np.isclose(tops[:, :, 1].max(), 1.0)
    bottoms = q.pos[(q.face == 0)]
    assert np.isclose(bottoms[:, :, 1].min(), 0.0) and np.isclose(bottoms[:, :, 1].max(), 0.5)


def test_log_axis_texture():
    q = _bake("minecraft:oak_log[axis=x]")
    names = [models.SPRITES.names[s] for s in q.sprite]
    east = [n for n, f in zip(names, q.face) if f in (4, 5)]
    assert all(n.endswith("oak_log_top") for n in east), east
    up = [n for n, f in zip(names, q.face) if f == 1]
    assert all(n.endswith("oak_log") for n in up), up


def test_door_hinge_side():
    # facing=south closed door: slab on the north edge (z in 0..3/16); hinge left/right flips texture u
    ql = _bake("minecraft:oak_door[facing=south,half=lower,hinge=left,open=false]")
    zr = ql.pos[:, :, 2]
    assert zr.max() <= 3 / 16 + 1e-6 or zr.min() >= 13 / 16 - 1e-6
    qo = _bake("minecraft:oak_door[facing=south,half=lower,hinge=left,open=true]")
    xs = qo.pos[:, :, 0]
    assert xs.max() - xs.min() <= 3 / 16 + 1e-6  # open door is a thin slab along z


def test_model_bounds_match_collision_shapes():
    """Orientation check against the game's own shapes: for every state of these blocks the baked model's
    bounding box equals the registry collision shape's bounding box (stairs incl. inner/outer, doors incl.
    hinge/open, trapdoors, beds, slabs, wall signs, carpets, buttons, grindstones)."""
    import itertools
    from blockwright.render import assets
    from blockwright.render.mesh import _phys
    reg = assets.registry()
    shapes = reg["shapes"]
    checked = 0
    for bid in ["minecraft:oak_stairs", "minecraft:oak_door", "minecraft:spruce_trapdoor", "minecraft:red_bed",
                "minecraft:oak_slab", "minecraft:oak_wall_sign", "minecraft:white_carpet",
                "minecraft:stone_button", "minecraft:grindstone"]:
        b = reg["blocks"][bid]
        keys = list(b["properties"])
        for combo in itertools.product(*[b["properties"][k] for k in keys]):
            p = dict(zip(keys, combo))
            if p.get("waterlogged") == "true" or p.get("powered") == "true":
                continue
            q, _ = models.bake_state(bid, p)
            _, _, _, si = _phys(bid, p)
            boxes = np.array([[float(v) for v in s.split()] for s in shapes[si].split(";") if s.strip()])
            if not len(boxes) or not len(q):
                continue
            pts = q.pos.reshape(-1, 3)
            assert np.allclose(pts.min(0), boxes[:, :3].min(0), atol=0.07), (bid, p)
            assert np.allclose(pts.max(0), boxes[:, 3:].max(0), atol=0.07), (bid, p)
            checked += 1
    assert checked > 100, checked


def test_face_culling_between_full_blocks():
    blocks = {(0, 0, 0): "minecraft:stone", (1, 0, 0): "minecraft:stone"}
    sc = build_scene(blocks, (2, 1, 1), {"ground": -5}, terrain=False)
    assert len(sc) == 10


def test_glass_culls_glass_but_leaves_do_not():
    g = build_scene({(0, 0, 0): "minecraft:glass", (1, 0, 0): "minecraft:glass"}, (2, 1, 1), {"ground": -5},
                    terrain=False)
    assert len(g) == 10
    lv = "minecraft:oak_leaves[distance=1,persistent=true,waterlogged=false]"
    l2 = build_scene({(0, 0, 0): lv, (1, 0, 0): lv}, (2, 1, 1), {"ground": -5}, terrain=False)
    assert len(l2) == 12


def test_tints():
    grass = tint_colors("minecraft:grass_block", {})[0]
    assert tuple(round(c * 255) for c in grass) == (0x91, 0xBD, 0x59)
    fol = tint_colors("minecraft:oak_leaves", {})[0]
    assert tuple(round(c * 255) for c in fol) == (0x77, 0xAB, 0x2F)
    assert tint_colors("minecraft:cherry_leaves", {}) == []


def test_bits_decode_spanning():
    rng = np.random.default_rng(1)
    bits = 5
    vals = rng.integers(0, 2 ** bits, 1000)
    total = math.ceil(1000 * bits / 64)
    acc = 0
    for i, v in enumerate(vals.tolist()):
        acc |= v << (i * bits)
    longs = [(acc >> (64 * k)) & (2 ** 64 - 1) for k in range(total)]
    longs = np.array([l - 2 ** 64 if l >= 2 ** 63 else l for l in longs], np.int64)
    assert (decode_bits(longs, 1000, bits) == vals).all()


def test_water_and_special_geometry():
    blocks = {(0, 0, 0): "minecraft:water[level=0]", (2, 0, 0): "minecraft:chest[facing=north,type=single]",
              (4, 0, 0): "minecraft:bell[attachment=floor,facing=north]"}
    sc = build_scene(blocks, (5, 1, 1), {"ground": -5}, terrain=False)
    assert (sc.layer == 2).any()             # translucent water
    assert len(sc) > 30


def test_storeys_from_floors():
    B = {}
    for x in range(8):
        for z in range(8):
            B[(x, 0, z)] = "minecraft:oak_planks"
            B[(x, 4, z)] = "minecraft:oak_planks"
    for y in range(1, 8):
        for x in range(8):
            B[(x, y, 0)] = "minecraft:stone_bricks"
            B[(x, y, 7)] = "minecraft:stone_bricks"
    cuts = detect_storeys(B, (8, 8, 8), {"ground": 0})
    assert cuts[:2] == [2, 6], cuts


def test_invalid_states_draw_missing_cube():
    """States the game cannot hold (unknown block / property / value) must not be silently half-drawn."""
    for st in ["minecraft:oak_fence[east=yes]", "minecraft:oak_planks[axis=y]", "minecraft:cottage_door",
               "oak_stairs[facing=up]"]:
        sc = build_scene({(0, 0, 0): st}, (1, 1, 1), {"ground": -5}, terrain=False)
        names = {models.SPRITES.names[s] for s in sc.sprite}
        assert names == {"__missing__"} and len(sc) == 6, (st, names, len(sc))
    assert state_info("minecraft:oak_fence[east=yes]").problem
    assert state_info("minecraft:oak_fence[east=true]").problem is None


def test_empty_models_render_nothing():
    """A multipart state matching no part / a model without elements is invisible in game (not 'missing')."""
    for st in ["minecraft:pitcher_crop[age=0,half=upper]",
               "minecraft:cobblestone_wall[east=none,north=none,south=none,west=none,up=false,waterlogged=false]"]:
        assert len(build_scene({(0, 0, 0): st}, (1, 1, 1), {"ground": -5}, terrain=False)) == 0, st


def test_bare_slot_texture_reference():
    """Face textures name a slot with or without '#' (TextureSlots.getMaterial); heavy_core uses 'all'."""
    q = _bake("minecraft:heavy_core")
    assert {models.SPRITES.names[s] for s in q.sprite} == {"block/heavy_core"}


def test_shade_brightness_and_light_damping():
    """Block.getShadeBrightness overrides: glass casts no AO, mud/soul sand do; leaves/ice dampen light."""
    assert state_info("minecraft:glass").shade == 1.0
    assert state_info("minecraft:white_stained_glass").shade == 1.0
    assert state_info("minecraft:stone").shade == 0.2
    assert state_info("minecraft:mud").shade == 0.2
    assert state_info("minecraft:oak_leaves[distance=1,persistent=true,waterlogged=false]").shade == 0.2
    assert state_info("minecraft:glass").damp == 0.0 and state_info("minecraft:ice").damp == 1.0
    assert state_info("minecraft:oak_leaves[distance=1,persistent=true,waterlogged=false]").damp == 1.0
    # blue_ice is a HalfTransparentBlock: same-block faces are skipped
    from blockwright.render.mesh import skip_rendering
    bi = state_info("minecraft:blue_ice")
    assert skip_rendering(bi, bi, 5)


def test_lightmap_matches_shader():
    """lightmap.fsh at overworld noon: ambient #0A0A0A, block factor 1.4, warm block-light tint, gamma 0.5."""
    from blockwright.render.mesh import lightmap
    assert np.allclose(lightmap(15, 0), 1.0) and np.allclose(lightmap(0, 15), 1.0)
    dark = lightmap(0, 0)
    assert np.allclose(dark, dark[0]) and 0.08 < dark[0] < 0.11        # not pitch black
    warm = lightmap(0, 9)
    assert warm[0] > warm[1] > warm[2]                                  # mid block light is orange
    sc = build_scene({(0, 0, 0): "minecraft:stone"}, (1, 1, 1), {"ground": -5}, terrain=False)
    assert sc.light.shape == (len(sc), 4, 3)


def test_uvlock_keeps_textures_world_aligned():
    """uvlock (BlockMath.getFaceTransformation): every face of every stair state maps texture u/v to world
    axes exactly like an unrotated full block (defaultFaceUV), so roof planks line up."""
    import itertools
    canon = {0: lambda p: (p[0], 1 - p[2]), 1: lambda p: (p[0], p[2]), 2: lambda p: (1 - p[0], 1 - p[1]),
             3: lambda p: (p[0], 1 - p[1]), 4: lambda p: (p[2], 1 - p[1]), 5: lambda p: (1 - p[2], 1 - p[1])}
    reg = models.assets.registry()["blocks"]["minecraft:oak_stairs"]["properties"]
    n = 0
    for f, h, s in itertools.product(reg["facing"], reg["half"], reg["shape"]):
        q = _bake(f"minecraft:oak_stairs[facing={f},half={h},shape={s}]")
        for i in range(len(q)):
            for k in range(4):
                assert np.allclose(canon[int(q.face[i])](q.pos[i, k]), q.uv[i, k], atol=1e-4), (f, h, s, i)
            n += 1
    assert n > 300


def test_fluid_faces_face_outwards_and_slab_rims_keep_water_flat():
    """FluidRenderer: side faces wind outwards (plus a reversed copy, for lava too); neighbours with legacy
    isSolid (slabs round a pond) do not pull the water surface corners down."""
    sc = build_scene({(0, 0, 0): "minecraft:lava[level=0]"}, (1, 1, 1), {"ground": -5}, terrain=False)
    names = [models.SPRITES.names[s] for s in sc.sprite]
    sides = [i for i, n in enumerate(names) if n == "block/lava_flow"]
    assert len(sides) == 8, names
    out = 0
    for i in sides:
        P = sc.pos[i].astype(np.float64)
        n = np.cross(P[1] - P[0], P[3] - P[0])
        out += (n @ (P.mean(0) - np.array([0.5, 0.5, 0.5]))) > 0
    assert out == 4, out                      # one outward + one inward copy per side
    B = {(1, 0, 1): "minecraft:water[level=0]"}
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if dx or dz:
                B[(1 + dx, 0, 1 + dz)] = "minecraft:oak_slab[type=bottom,waterlogged=false]"
    sc = build_scene(B, (3, 1, 3), {"ground": -5}, terrain=False)
    tops = [i for i, s in enumerate(sc.sprite) if models.SPRITES.names[s] == "block/water_still"
            and sc.pos[i][:, 1].min() > 0.5]
    assert tops and np.allclose(sc.pos[tops[0]][:, 1], 8 / 9 - 0.001, atol=1e-4), sc.pos[tops[0]]


def test_physics_dump_is_used():
    from blockwright.render import assets
    if assets.render_physics() is None:
        print("     (no render_physics data - fallback approximations in use)")
        return
    assert state_info("minecraft:magma_block").emissive
    assert state_info("minecraft:oak_slab[type=bottom,waterlogged=false]").solid
    assert not state_info("minecraft:short_grass").solid
    # fence occlusion arms are the thin 2x9 px rails, not the 4x16 px (24 px tall) collision arm
    fence = state_info("minecraft:oak_fence[east=false,north=true,south=false,waterlogged=false,west=false]")
    assert bin(fence.masks[2]).count("1") < 40, bin(fence.masks[2]).count("1")


def test_reader_does_not_assume_air_at_palette_zero():
    from blockwright.render import read_litematic
    fx = ROOT / "tests" / "fixtures"
    blocks, size, _ = read_litematic(fx / "broken_air_not_first.litematic")
    assert len(blocks) == 12, len(blocks)
    try:
        read_litematic(fx / "broken_short_blockstates.litematic")
    except ValueError as e:
        assert "BlockStates" in str(e)
    else:
        raise AssertionError("short BlockStates array not reported")


def test_view_names_unique_and_missing_cut_skipped():
    from blockwright.render.views import view_list
    B = {(0, 0, 0): "minecraft:stone"}
    names = [v["name"] for v in view_list(B, (1, 1, 1), {"ground": 0},
                                          ["quick", "iso_se", {"target": (0, 0, 0)}, {"target": (0, 0, 0), "zoom": 2},
                                           "cut_3"])]
    assert names == ["iso_se", "iso_nw", "cut_1", "custom", "custom_2"], names


def test_render_quick_image():
    B, size, meta = make_test_scene()
    sub = {p: s for p, s in B.items() if p[0] < 12 and p[2] < 10}
    out = TMP_ROOT / "render" / "pytest"
    p = render_view(sub, size, {"name": "iso_se", "azimuth": 45, "elevation": 32}, out / "quick.png", meta=meta,
                    width=400, height=300)
    from PIL import Image
    im = np.asarray(Image.open(p))
    assert im.shape == (300, 400, 3)
    assert im.std() > 20


def test_closeup_camera_and_quick_views():
    B, size, meta = make_test_scene()
    out = TMP_ROOT / "render" / "pytest"
    p = render_view(B, size, {"name": "door", "azimuth": 20, "elevation": 25, "target": (4, 1, 21), "radius": 3},
                    out / "closeup.png", meta=meta, width=320, height=240)
    assert pathlib.Path(p).exists()
    paths = render_views({k: v for k, v in B.items() if k[2] > 30}, size, out, meta=dict(meta, slug="q"),
                         views="quick", width=320, height=240, workers=1)
    names = [pathlib.Path(x).name for x in paths]
    assert names[:2] == ["q_iso_se.png", "q_iso_nw.png"] and names[-1] == "q_sheet.png", names


if __name__ == "__main__":
    if "--render" in sys.argv:
        B, size, meta = make_test_scene()
        t = time.time()
        views = sys.argv[sys.argv.index("--render") + 1].split(",") if len(sys.argv) > sys.argv.index("--render") + 1 else "all"
        paths = render_views(B, size, TMP_ROOT / "render" / "test_scene", meta=meta, views=views, verbose=True)
        print("\n".join(paths))
        print(f"{time.time() - t:.1f}s")
    else:
        fails = 0
        for name, fn in list(globals().items()):
            if name.startswith("test_") and callable(fn):
                try:
                    fn()
                    print("ok  ", name)
                except Exception as e:  # noqa: BLE001
                    fails += 1
                    print("FAIL", name, repr(e))
        sys.exit(1 if fails else 0)
