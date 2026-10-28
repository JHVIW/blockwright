"""Scene meshing: blocks dict -> world-space quad soup with culling, tints, AO, light and fluids.

Game rules ported from the 26.3 client/common source:
  * Block.shouldRenderFace (face-occlusion shapes + skipRendering overrides of HalfTransparentBlock,
    IronBarsBlock, LiquidBlock, LeavesBlock(cutout leaves: no skip), MangroveRootsBlock, PowderSnowBlock)
  * BlockModelLighter.prepareQuadAmbientOcclusion / prepareQuadFlat (smooth AO; corner tables, faceCubic rule,
    getShadeBrightness, lightPermeable = !solidRender, LightCoordsUtil.smoothBlend) and CardinalLighting.DEFAULT
  * LightEngine (sky sources, max(1, dampening) per step, shape light occlusion) and the lightmap.fsh colours
  * BlockColors / BlockTintSources at plains (temperature 0.8, downfall 0.4)
  * FluidRenderer (heights amount/9, corner averaging with legacy isSolid, face rules, flow direction, overlay)
Per-state physics (face occlusion shapes, isSolid, light dampening, shade brightness, emissive) come from
blockwright/data/render_physics_26.3.json, dumped from the game by blockwright/java/RenderPhysicsDump.java; without that
file they are approximated from the registry dump (collision shapes, flags).
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass

import numpy as np

from . import assets
from .models import (DIR_VEC, LAYER_SOLID, LAYER_TRANSLUCENT, OPPOSITE, SPRITES, Quads, bake_state, missing_cube,
                     canonical, has_model, has_random_variants, parse_state, pick_signature, pos_hash)
from .special import special_quads

CARDINAL = np.array([0.5, 1.0, 0.8, 0.8, 0.6, 0.6], np.float32)   # down up north south west east
DIRV = DIR_VEC.astype(np.int64)
# BlockModelLighter.AdjacencyInfo corners per direction (indices into DIRS)
AO_CORNERS = {
    0: (4, 5, 2, 3),  # DOWN:  W E N S
    1: (5, 4, 2, 3),  # UP:    E W N S
    2: (1, 0, 5, 4),  # NORTH: U D E W
    3: (4, 5, 0, 1),  # SOUTH: W E D U
    4: (1, 0, 2, 3),  # WEST:  U D N S
    5: (0, 1, 2, 3),  # EAST:  D U N S
}
INVISIBLE_CLASSES = {"BarrierBlock", "LightBlock", "StructureVoidBlock"}
BARS_TAG = {"minecraft:iron_bars"} | {f"minecraft:{w}{s}copper_bars" for w in ("", "waxed_")
                                      for s in ("", "exposed_", "weathered_", "oxidized_")}
ALWAYS_WATER = {"minecraft:seagrass", "minecraft:tall_seagrass", "minecraft:kelp", "minecraft:kelp_plant",
                "minecraft:bubble_column"}
DIR_PROP = ["down", "up", "north", "south", "west", "east"]

# BlockBehaviour.Properties.offsetType(...) in 26.3 Blocks.java (random render offset per position)
OFFSET_TYPES = {
    'mangrove_propagule': 'XZ', 'short_grass': 'XYZ', 'fern': 'XYZ', 'short_dry_grass': 'XYZ',
    'tall_dry_grass': 'XYZ', 'tall_seagrass': 'XZ', 'dandelion': 'XZ', 'golden_dandelion': 'XZ', 'torchflower': 'XZ',
    'poppy': 'XZ', 'blue_orchid': 'XZ', 'allium': 'XZ', 'azure_bluet': 'XZ', 'red_tulip': 'XZ', 'orange_tulip': 'XZ',
    'white_tulip': 'XZ', 'pink_tulip': 'XZ', 'oxeye_daisy': 'XZ', 'cornflower': 'XZ', 'wither_rose': 'XZ',
    'lily_of_the_valley': 'XZ', 'sunflower': 'XZ', 'lilac': 'XZ', 'rose_bush': 'XZ', 'peony': 'XZ',
    'tall_grass': 'XZ', 'large_fern': 'XZ', 'pitcher_plant': 'XZ', 'bamboo_sapling': 'XZ', 'bamboo': 'XZ',
    'warped_roots': 'XZ', 'nether_sprouts': 'XZ', 'crimson_roots': 'XZ', 'pointed_dripstone': 'XZ',
    'sulfur_spike': 'XZ', 'small_dripleaf': 'XYZ', 'hanging_roots': 'XZ', 'open_eyeblossom': 'XZ',
    'closed_eyeblossom': 'XZ',
}


def block_offsets(P: np.ndarray, kind: str) -> np.ndarray:
    """BlockBehaviour offset functions with Mth.getSeed(x, 0, z) (Java int/long overflow emulated)."""
    x = P[:, 0].astype(np.int64)
    z = P[:, 2].astype(np.int64)
    xi = (x * 3129871).astype(np.int32).astype(np.int64)        # int * int overflows in Java
    with np.errstate(over="ignore"):
        seed = xi ^ (z * np.int64(116129781)) ^ np.int64(0)
        seed = seed * seed * np.int64(42317861) + seed * np.int64(11)
    seed = seed >> 16
    ox = np.clip(((seed & 15) / 15.0 - 0.5) * 0.5, -0.25, 0.25)
    oz = np.clip((((seed >> 8) & 15) / 15.0 - 0.5) * 0.5, -0.25, 0.25)
    oy = ((((seed >> 4) & 15) / 15.0 - 1.0) * 0.2) if kind == "XYZ" else np.zeros(len(P))
    return np.stack([ox, oy, oz], axis=1).astype(np.float32)


PLAINS_T, PLAINS_D = 0.8, 0.4
WATER_COLOR = (0x3F / 255, 0x76 / 255, 0xE4 / 255)


def _argb(c: int):
    c &= 0xFFFFFFFF
    return ((c >> 16) & 255) / 255.0, ((c >> 8) & 255) / 255.0, (c & 255) / 255.0


_tint_cache: dict = {}


def tint_colors(block_id: str, props: dict) -> list:
    """Per-tintindex RGB colours for a block (BlockColors.createDefault, in-world at plains)."""
    b = block_id[10:]
    key = (b, props.get("age"), props.get("power"))
    if key in _tint_cache:
        return _tint_cache[key]
    grass = tuple(v / 255 for v in assets.colormap_pixel("grass", PLAINS_T, PLAINS_D))
    foliage = tuple(v / 255 for v in assets.colormap_pixel("foliage", PLAINS_T, PLAINS_D))
    dry = tuple(v / 255 for v in assets.colormap_pixel("dry_foliage", PLAINS_T, PLAINS_D))
    res: list = []
    if b in ("large_fern", "tall_grass", "fern", "short_grass", "potted_fern", "bush", "grass_block", "sugar_cane"):
        res = [grass]
    elif b in ("pink_petals", "wildflowers"):
        res = [(1.0, 1.0, 1.0), grass]
    elif b == "spruce_leaves":
        res = [_argb(-10380959)]
    elif b == "birch_leaves":
        res = [_argb(-8345771)]
    elif b in ("oak_leaves", "jungle_leaves", "acacia_leaves", "dark_oak_leaves", "vine", "mangrove_leaves"):
        res = [foliage]
    elif b == "leaf_litter":
        res = [dry]
    elif b in ("water_cauldron", "water", "bubble_column"):
        res = [WATER_COLOR]
    elif b == "redstone_wire":
        p = int(props.get("power", "0")) / 15.0
        r = p * 0.6 + (0.4 if p > 0 else 0.3)
        g = min(max(p * p * 0.7 - 0.5, 0.0), 1.0)
        bl = min(max(p * p * 0.6 - 0.7, 0.0), 1.0)
        res = [(r, g, bl)]
    elif b in ("attached_melon_stem", "attached_pumpkin_stem"):
        res = [_argb(-2046180)]
    elif b in ("melon_stem", "pumpkin_stem"):
        a = int(props.get("age", "0"))
        res = [(a * 32 / 255, (255 - a * 8) / 255, a * 4 / 255)]
    elif b == "lily_pad":
        res = [_argb(-14647248)]
    _tint_cache[key] = res
    return res


# ----------------------------------------------------------------------------------------------
# per-state info


def _phys(block_id: str, props: dict):
    reg = assets.registry()["blocks"].get(block_id)
    if reg is None:
        return 0, 0, 0, 0
    ph = reg.get("phys")
    if ph is None:
        key = ",".join(f"{k}={props.get(k)}" for k in reg["properties"])
        ph = reg.get("phys_by_state", {}).get(key)
        if ph is None:
            ph = next(iter(reg.get("phys_by_state", {"": "0,0,0,0"}).values()))
    sturdy, flags, light, shape = (int(v) for v in ph.split(","))
    return sturdy, flags, light, shape


_shape_mask_cache: dict = {}
FULL_MASK = (1 << 256) - 1


def _face_masks(shape_idx: int) -> tuple:
    """Per direction a 256-bit int (16x16 grid in the face plane) of the shape's face slice."""
    if shape_idx in _shape_mask_cache:
        return _shape_mask_cache[shape_idx]
    spec = assets.registry()["shapes"][shape_idx]
    boxes = []
    for part in spec.split(";"):
        if part.strip():
            boxes.append([float(v) for v in part.split()])
    masks = []
    eps = 1e-6
    for d in range(6):
        grid = np.zeros((16, 16), bool)
        for x1, y1, z1, x2, y2, z2 in boxes:
            if d == 0 and y1 <= eps:
                a, b = (x1, z1, x2, z2), None
            elif d == 1 and y2 >= 1 - eps:
                a, b = (x1, z1, x2, z2), None
            elif d == 2 and z1 <= eps:
                a, b = (x1, y1, x2, y2), None
            elif d == 3 and z2 >= 1 - eps:
                a, b = (x1, y1, x2, y2), None
            elif d == 4 and x1 <= eps:
                a, b = (z1, y1, z2, y2), None
            elif d == 5 and x2 >= 1 - eps:
                a, b = (z1, y1, z2, y2), None
            else:
                continue
            u0, v0, u1, v1 = (int(round(min(max(c, 0.0), 1.0) * 16)) for c in a)
            grid[u0:u1, v0:v1] = True
        bits = 0
        for i, v in enumerate(grid.ravel()):
            if v:
                bits |= 1 << i
        masks.append(bits)
    res = tuple(masks)
    _shape_mask_cache[shape_idx] = res
    return res


@dataclass
class StateInfo:
    state: str
    block: str
    props: dict
    cls: str
    can_occlude: bool
    full_collision: bool
    solid_render: bool
    light: int
    masks: tuple            # occlusion face masks (0 when !can_occlude)
    fluid: int              # 0 none, 1 water, 2 lava
    fluid_amount: int       # 1..8
    random: bool
    invisible: bool
    shade: float = 1.0      # Block.getShadeBrightness (AO occluder strength: 0.2 dark, 1.0 none)
    damp: float = 0.0       # BlockState.getLightDampening of a non-opaque block (0..15)
    problem: str | None = None   # why the state is not a valid 26.3 state (rendered as the missing-model cube)
    ancestors: tuple = ()
    solid: bool = False     # legacy BlockState.isSolid (fluid corner heights treat such neighbours as walls)
    sky_down: bool = False  # propagatesSkylightDown
    emissive: bool = False  # emissiveRendering (drawn full bright)
    light_faces: tuple = (0, 0, 0, 0, 0, 0)   # face masks used by the light engine (useShapeForLightOcclusion)


def _physics_entry(bid: str, props: dict, reg: dict):
    """Exact per-state physics from blockwright/data/render_physics_26.3.json, or None."""
    phys = assets.render_physics()
    if phys is None:
        return None
    e = phys["blocks"].get(bid)
    if isinstance(e, dict):
        e = e.get(",".join(f"{k}={props.get(k)}" for k in reg.get("properties", {})))
    if not isinstance(e, str):
        return None
    v = e.split(",")
    faces = phys["faces"]

    def mask(code: str) -> int:
        if code == "":
            return 0
        if code == "full":
            return FULL_MASK
        return int(code, 16)
    return dict(solid=v[0] == "1", sky_down=v[1] == "1", damp=float(v[2]), emissive=v[3] == "1",
                shade=int(v[4]) / 10.0, shape_light=v[5] == "1",
                masks=tuple(mask(faces[int(i)]) for i in v[6:12]))


_info_cache: dict = {}
_warned: set = set()


def _warn(msg: str) -> None:
    if msg not in _warned:
        _warned.add(msg)
        print(f"[blockwright.render] WARNING {msg}", file=sys.stderr)


def validate_state(bid: str, props: dict) -> str | None:
    """None when (block, given properties) is a valid 26.3 state, else a short reason. The game has no way to
    hold such a state; the renderer shows it as the magenta/black missing-model cube instead of guessing."""
    reg = assets.registry()["blocks"].get(bid)
    if reg is None:
        return f"unknown block {bid}"
    legal = reg.get("properties", {})
    for k, v in props.items():
        if k not in legal:
            return f"{bid} has no property {k!r}"
        if str(v) not in legal[k]:
            return f"invalid value {k}={v} for {bid} (legal: {'|'.join(legal[k])})"
    return None


def _shade_brightness(cls: str, anc: tuple, props: dict, full_collision: bool) -> float:
    """BlockBehaviour.getShadeBrightness and its 26.3 overrides."""
    if "TransparentBlock" in anc or cls in INVISIBLE_CLASSES:
        return 1.0
    if cls in ("MudBlock", "SoulSandBlock"):
        return 0.2
    if cls == "SnowLayerBlock":
        return 0.2 if props.get("layers") == "8" else 1.0
    return 0.2 if full_collision else 1.0


def state_info(state: str) -> StateInfo:
    if state in _info_cache:
        return _info_cache[state]
    bid, given = parse_state(state)
    problem = validate_state(bid, given) if bid not in ("minecraft:air", "minecraft:cave_air",
                                                         "minecraft:void_air") else None
    if problem:
        _warn(f"{problem} (state {state!r}) -> drawn as the missing-model cube")
    reg = assets.registry()["blocks"].get(bid, {})
    full = dict(reg.get("default", {}))
    full.update(given)
    props = full
    cls = reg.get("class", "Block")
    anc = assets.class_ancestors(cls)
    sturdy, flags, light, shape = _phys(bid, props)
    can_occ = bool(flags & 1)
    masks = _face_masks(shape) if can_occ else (0, 0, 0, 0, 0, 0)
    if flags & 4:
        masks = (FULL_MASK,) * 6
    fluid, amount = 0, 0
    if bid in ("minecraft:water", "minecraft:lava"):
        lv = int(props.get("level", "0")) if str(props.get("level", "0")).isdigit() else 0
        fluid = 1 if bid == "minecraft:water" else 2
        amount = 8 if lv == 0 or lv >= 8 else 8 - lv
    elif props.get("waterlogged") == "true" or bid in ALWAYS_WATER:
        fluid, amount = 1, 8
    full_coll, solid = bool(flags & 2), bool(flags & 4)
    ph = None if problem else _physics_entry(bid, props, reg)
    if ph is not None:              # exact values dumped from the game
        masks = ph["masks"]
        damp, shade, legacy_solid = ph["damp"], ph["shade"], ph["solid"]
        sky_down, emissive = ph["sky_down"], ph["emissive"]
        light_faces = masks if (ph["shape_light"] and can_occ) else (0,) * 6
    else:                           # approximations from the registry dump
        # light dampening: 1 unless propagatesSkylightDown (default: shape not a full cube and no fluid;
        # TransparentBlock/barrier/light override it to true)
        if solid:
            damp = 15.0
        elif fluid:
            damp = 1.0
        elif "TransparentBlock" in anc or cls in INVISIBLE_CLASSES:
            damp = 0.0
        else:
            damp = 1.0 if full_coll else 0.0
        shade = _shade_brightness(cls, anc, props, full_coll)
        legacy_solid = solid or full_coll or cls in ("SlabBlock", "StairBlock", "WallBlock", "FenceBlock",
                                                     "FenceGateBlock")
        sky_down, emissive = damp == 0.0, False
        light_faces = masks if cls in ("SlabBlock", "StairBlock", "SnowLayerBlock") else (0,) * 6
    info = StateInfo(state, bid, props, cls, can_occ, full_coll, solid, light, masks, fluid,
                     amount, False if problem else has_random_variants(bid, props),
                     bid in ("minecraft:air", "minecraft:cave_air", "minecraft:void_air", "minecraft:barrier",
                             "minecraft:light", "minecraft:structure_void", "minecraft:moving_piston"),
                     shade, damp, problem, anc, legacy_solid, sky_down, emissive, light_faces)
    _info_cache[state] = info
    return info


def skip_rendering(a: StateInfo, b: StateInfo, d: int) -> bool:
    """BlockBehaviour.skipRendering overrides relevant in 26.3."""
    if "HalfTransparentBlock" in a.ancestors or a.cls == "PowderSnowBlock":
        return b.block == a.block
    if "IronBarsBlock" in a.ancestors:
        if b.block == a.block or (a.block in BARS_TAG and b.block in BARS_TAG and DIR_PROP[OPPOSITE[d]] in b.props):
            if d < 2:
                return True
            return a.props.get(DIR_PROP[d]) == "true" and b.props.get(DIR_PROP[OPPOSITE[d]]) == "true"
        return False
    if a.cls == "LiquidBlock":
        return b.fluid == a.fluid
    if a.block == "minecraft:mangrove_roots":
        return b.block == a.block and d < 2
    return False


def should_render_face(a: StateInfo, b: StateInfo, d: int) -> bool:
    """Block.shouldRenderFace(a, neighbour b, direction d)."""
    occ = b.masks[OPPOSITE[d]]
    if occ == FULL_MASK:
        return False
    if skip_rendering(a, b, d):
        return False
    if occ == 0:
        return True
    own = a.masks[d]
    if own == 0:
        return True
    return (own & ~occ) != 0


# ----------------------------------------------------------------------------------------------
# scene


@dataclass
class Scene:
    pos: np.ndarray        # (N,4,3) float32 world
    uv: np.ndarray         # (N,4,2) float32 sprite-local
    sprite: np.ndarray     # (N,) int32
    rgb: np.ndarray        # (N,3) float32
    light: np.ndarray      # (N,4,3) float32: per-vertex AO x directional shade x lightmap colour
    layer: np.ndarray      # (N,) int8
    tri: np.ndarray        # (N,) bool  (P0,P1,P3 triangle)
    bias: np.ndarray       # (N,) float32 depth bias (later elements of a model win coplanar ties)
    frame_pts: np.ndarray  # (M,3) centres of the build's blocks (no terrain), used for auto-framing
    bmin: np.ndarray       # build bbox min (world)
    bmax: np.ndarray       # build bbox max (world, exclusive)
    ground: int

    def __len__(self):
        return len(self.sprite)


AIR = "minecraft:air"
GRASS = "minecraft:grass_block[snowy=false]"
DIRT = "minecraft:dirt"

_TERRAIN_LIKE = ("grass_block", "dirt", "coarse_dirt", "podzol", "rooted_dirt", "dirt_path", "moss_block",
                 "mud", "gravel", "farmland", "mycelium", "sand")


def guess_ground(blocks: dict, size) -> int:
    """Fallback when meta has no 'ground': the lowest layer that is mostly terrain-like blocks; else -1."""
    by_y: dict = {}
    for (x, y, z), s in blocks.items():
        b = s.split("[")[0].replace("minecraft:", "")
        c = by_y.setdefault(y, [0, 0])
        c[1] += 1
        if b in _TERRAIN_LIKE:
            c[0] += 1
    for y in sorted(by_y):
        t, n = by_y[y]
        if t >= 6 and t >= 0.3 * n:
            return y
    return min(by_y) - 1 if by_y else -1


def build_scene(blocks: dict, size, meta: dict | None = None, terrain: bool = True, cut: int | None = None,
                margin: int = 4, depth: int = 3, lighting: bool = True) -> Scene:
    """Mesh a structure. `cut`: only blocks with y <= cut are drawn (terrain unaffected).
    lighting: run the sky/block light engine (interiors darker, like the game in daylight)."""
    meta = meta or {}
    sx, sy, sz = (int(v) for v in size)
    ground = meta.get("ground")
    if ground is None:
        ground = guess_ground(blocks, size)
    ground = int(ground)

    items = {}
    for p, s in blocks.items():
        if s is None:
            continue
        if cut is not None and p[1] > cut:
            continue
        items[(int(p[0]), int(p[1]), int(p[2]))] = s
    if items:
        arr = np.array(list(items.keys()), np.int64)
        bmin = arr.min(0)
        bmax = arr.max(0) + 1
    else:
        bmin = np.array([0, 0, 0])
        bmax = np.array([max(sx, 1), max(sy, 1), max(sz, 1)])
    full_min = np.minimum(bmin, [0, 0, 0])
    full_max = np.maximum(bmax, [sx, sy, sz])

    # grid extents (with terrain margin and a 2-cell pad for AO lookups)
    m = margin if terrain else 0
    lo = np.array([full_min[0] - m, min(full_min[1], ground - depth) if terrain else full_min[1], full_min[2] - m])
    hi = np.array([full_max[0] + m, full_max[1], full_max[2] + m])
    pad = 2
    off = -lo + pad
    dims = tuple(int(v) for v in (hi - lo + 2 * pad))

    # palette
    palette: list[StateInfo] = [state_info(AIR)]
    pidx = {AIR: 0}
    grid = np.zeros(dims, np.int32)

    def pal(state):
        i = pidx.get(state)
        if i is None:
            info = state_info(state)
            canon = info.state
            i = len(palette)
            palette.append(info)
            pidx[state] = i
        return i

    coords = np.array(list(items.keys()), np.int64).reshape(-1, 3)
    ids = np.array([pal(s) for s in items.values()], np.int32)
    vis = np.array([not palette[i].invisible for i in ids], bool) if len(ids) else np.zeros(0, bool)
    frame_pts = (coords[vis] + 0.5).astype(np.float32) if vis.any() else ((bmin + bmax) / 2.0)[None].astype(np.float32)
    if cut is not None and vis.any():
        # frame cutaways on the part of the build that was covered by the removed upper blocks
        above = {(p[0], p[2]) for p in blocks if p[1] > cut}
        cov = np.array([(int(c[0]), int(c[2])) in above for c in coords[vis]], bool)
        if cov.sum() >= 4:
            frame_pts = frame_pts[cov]
    if len(coords):
        g = coords + off
        grid[g[:, 0], g[:, 1], g[:, 2]] = ids

    if terrain:
        gi, di = pal(GRASS), pal(DIRT)
        x0, x1 = full_min[0] - m, full_max[0] + m
        z0, z1 = full_min[2] - m, full_max[2] + m
        for y in range(ground - depth, ground + 1):
            gy = y + off[1]
            sub = grid[x0 + off[0]:x1 + off[0], gy, z0 + off[2]:z1 + off[2]]
            fill = sub == 0
            sub[fill] = gi if y == ground else di
        tmask = (grid == gi) | (grid == di)
        tc = np.argwhere(tmask)
        if len(tc):
            coords = np.concatenate([coords, tc - off])
            ids = np.concatenate([ids, grid[tmask].astype(np.int32)])

    # per-palette arrays
    npal = len(palette)
    full_coll = np.array([p.full_collision for p in palette])
    solid_r = np.array([p.solid_render for p in palette])
    S_grid = np.array([p.shade for p in palette], np.float32)[grid]
    perm_grid = ~solid_r[grid]
    emit_pal = np.array([p.light for p in palette], np.float32)

    # ---------------------------------------------------------------- instance block quads
    order = np.argsort(ids, kind="stable")
    ids_s = ids[order]
    coords_s = coords[order]
    bounds = np.searchsorted(ids_s, np.arange(npal + 1))
    parts = []          # (Quads world, cell (n,3), ao flag (n,), palette id)
    decision_cache: dict = {}
    for p in range(1, npal):
        a, b = bounds[p], bounds[p + 1]
        if a == b:
            continue
        info = palette[p]
        if info.invisible:
            continue
        P = coords_s[a:b]
        groups = []
        if info.random:
            sigs = {}
            for i, (x, y, z) in enumerate(P.tolist()):
                sig = pick_signature(info.block, info.props, pos_hash(x, y, z))
                sigs.setdefault(sig, []).append(i)
            for sig, idx in sigs.items():
                groups.append((sig, P[np.array(idx)]))
        else:
            groups.append((None, P))
        if info.problem:
            sq, tints = None, []
        else:
            sq = special_quads(info.block, info.cls, info.props)
            tints = tint_colors(info.block, info.props)
        for sig, PP in groups:
            if info.problem or not has_model(info.block, info.props):
                # invalid state / no blockstate entry / missing model file: the game's missing-model cube.
                # (A multipart state matching no part, or a model without elements, renders nothing - as in game.)
                q, use_ao = missing_cube(), False
            else:
                q, use_ao = bake_state(info.block, info.props, sig)
            use_ao = use_ao and info.light == 0
            for qq, ao_flag in ((q, use_ao), (sq, False)):
                if qq is None or not len(qq):
                    continue
                inst = _instance(qq, PP)
                off_kind = OFFSET_TYPES.get(info.block[10:]) if qq is q else None
                if off_kind:
                    inst.pos += np.repeat(block_offsets(PP, off_kind), len(qq), axis=0)[:, None, :]
                cell = np.repeat(PP, len(qq), axis=0)
                local = np.tile(np.arange(len(qq), dtype=np.float32), len(PP))
                # face culling
                keep = np.ones(len(inst), bool)
                cm = inst.cull >= 0
                if cm.any():
                    cd = inst.cull[cm].astype(np.int64)
                    nbp = cell[cm] + DIRV[cd] + off
                    nb = grid[nbp[:, 0], nbp[:, 1], nbp[:, 2]]
                    keys = nb.astype(np.int64) * 6 + cd
                    uk, inv = np.unique(keys, return_inverse=True)
                    dec = np.empty(len(uk), bool)
                    for j, k in enumerate(uk.tolist()):
                        ck = (p, k)
                        r = decision_cache.get(ck)
                        if r is None:
                            r = should_render_face(info, palette[k // 6], k % 6)
                            decision_cache[ck] = r
                        dec[j] = r
                    keep[np.flatnonzero(cm)] = dec[inv]
                if not keep.all():
                    inst = inst.take(keep)
                    cell = cell[keep]
                    local = local[keep]
                if not len(inst):
                    continue
                # tints
                if tints:
                    tm = (inst.tint >= 0) & (inst.tint < len(tints))
                    if tm.any():
                        tc_arr = np.array(tints, np.float32)
                        inst.rgb[tm] *= tc_arr[inst.tint[tm]]
                parts.append((inst, cell, np.full(len(inst), ao_flag), p, local))

    # ---------------------------------------------------------------- lighting (light engine + AO + cardinal)
    sky, blk = compute_light(palette, grid) if lighting else (None, None)
    quads = Quads.concat([x[0] for x in parts])
    if len(quads):
        cells = np.concatenate([x[1] for x in parts])
        aoflag = np.concatenate([x[2] for x in parts])
        pal_of = np.concatenate([np.full(len(x[0]), x[3], np.int32) for x in parts])
        light = np.repeat(CARDINAL[np.clip(quads.shade, 0, 5)][:, None], 4, axis=1).astype(np.float32)
        nos = quads.shade < 0
        light[nos] = 1.0
        bright = np.ones((len(quads), 4, 3), np.float32)       # lightmap colour per vertex
        if aoflag.any():
            idx = np.flatnonzero(aoflag)
            ao, lv = _ambient_occlusion(quads.pos[idx] - cells[idx][:, None, :], quads.face[idx].astype(np.int64),
                                        cells[idx] + off, full_coll[pal_of[idx]], S_grid, perm_grid, sky, blk)
            light[idx] *= ao
            if lv is not None:
                bright[idx] = lv
        if sky is not None:
            idx = np.flatnonzero(~aoflag)
            if len(idx):
                # ModelBlockRenderer.tesselateFlat: culled faces take the light of the neighbour in the cull
                # direction, unculled ones the neighbour when the face is cubic, else the block's own cell;
                # LightCoordsUtil.getLightCoords raises block light to the block's own emission.
                lp = quads.pos[idx] - cells[idx][:, None, :]
                d = quads.face[idx].astype(np.int64)
                cd = quads.cull[idx].astype(np.int64)
                culled = cd >= 0
                cubic = _face_cubic(lp, d, full_coll[pal_of[idx]])
                step = np.where(culled[:, None], DIRV[np.clip(cd, 0, 5)], cubic[:, None] * DIRV[d])
                gc = cells[idx] + off + step
                sl = sky[gc[:, 0], gc[:, 1], gc[:, 2]]
                bl = np.maximum(blk[gc[:, 0], gc[:, 1], gc[:, 2]], emit_pal[pal_of[idx]])
                bright[idx] = lightmap(sl, bl)[:, None, :]
        emis = (quads.emit > 0) | np.array([p.emissive for p in palette], bool)[pal_of]
        bright[emis] = 1.0                 # element light_emission / emissiveRendering: full bright
        light = light[:, :, None] * bright
        tri = np.zeros(len(quads), bool)
        bias = np.concatenate([x[4] for x in parts]) * np.float32(2e-4)
    else:
        light = np.zeros((0, 4, 3), np.float32)
        tri = np.zeros(0, bool)
        bias = np.zeros(0, np.float32)

    # ---------------------------------------------------------------- fluids
    fl = _fluids(palette, grid, coords, ids, off, sky, blk)
    if fl is not None:
        fq, flight, ftri = fl
        quads = Quads.concat([quads, fq])
        light = np.concatenate([light, flight])
        tri = np.concatenate([tri, ftri])
        bias = np.concatenate([bias, np.zeros(len(ftri), np.float32)])

    return Scene(quads.pos, quads.uv, quads.sprite, quads.rgb, light.astype(np.float32), quads.layer, tri,
                 bias.astype(np.float32), frame_pts, bmin.astype(np.float64), bmax.astype(np.float64), ground)


def _instance(q: Quads, P: np.ndarray) -> Quads:
    k, n = len(P), len(q)
    pos = (q.pos[None, :, :, :] + P[:, None, None, :].astype(np.float32)).reshape(k * n, 4, 3)
    rep = lambda a: np.tile(a, (k,) + (1,) * (a.ndim - 1))
    return Quads(pos, rep(q.uv), rep(q.sprite), rep(q.tint), rep(q.cull), rep(q.shade), rep(q.face), rep(q.layer),
                 rep(q.emit), rep(q.rgb).copy())


def _face_cubic(lp, face, fullcoll):
    axis_of = np.array([1, 1, 2, 2, 0, 0])
    positive = np.array([False, True, False, True, False, True])
    ax = axis_of[face]
    co = np.take_along_axis(lp, ax[:, None, None].repeat(4, 1), axis=2)[:, :, 0]
    cmin, cmax = co.min(1), co.max(1)
    flat = np.abs(cmax - cmin) < 1e-6
    bound = np.where(positive[face], cmax > 0.9999, cmin < 1e-4)
    return flat & (bound | fullcoll)


def _ambient_occlusion(lp, face, gcell, fullcoll, S, Pm, sky=None, blk=None):
    """Vectorised BlockModelLighter.prepareQuadAmbientOcclusion: smooth AO shade and smooth light
    (LightCoordsUtil.smoothBlend) per vertex. lp: (n,4,3) block-local vertex positions;
    face: (n,) quad direction; gcell: grid coords. Returns (ao (n,4), brightness (n,4) or None)."""
    n = len(face)
    out = np.ones((n, 4), np.float32)
    lout = np.ones((n, 4, 3), np.float32) if sky is not None else None
    mins = lp.min(1)
    maxs = lp.max(1)
    axis_of = np.array([1, 1, 2, 2, 0, 0])
    positive = np.array([False, True, False, True, False, True])

    def get(g, arr):
        return arr[g[:, 0], g[:, 1], g[:, 2]]

    for d in range(6):
        sel = np.flatnonzero(face == d)
        if not len(sel):
            continue
        ax = axis_of[d]
        cmin, cmax = mins[sel, ax], maxs[sel, ax]
        flat = np.abs(cmax - cmin) < 1e-6
        bound = (cmax > 0.9999) if positive[d] else (cmin < 1e-4)
        cubic = flat & (bound | fullcoll[sel])
        cell = gcell[sel]
        D = DIRV[d]
        base = cell + cubic[:, None] * D
        cs = AO_CORNERS[d]
        C = [DIRV[c] for c in cs]
        sh = [get(base + C[i], S) for i in range(4)]
        pm = [get(base + C[i] + D, Pm) for i in range(4)]

        def corner(i, j):
            v = get(base + C[i] + C[j], S)
            return np.where(pm[i] | pm[j], v, sh[0])

        center = np.where(cubic, get(base, S), get(cell, S))
        L = {
            (0, 3): (sh[3] + sh[0] + corner(0, 3) + center) * 0.25,
            (0, 2): (sh[2] + sh[0] + corner(0, 2) + center) * 0.25,
            (1, 2): (sh[2] + sh[1] + corner(1, 2) + center) * 0.25,
            (1, 3): (sh[3] + sh[1] + corner(1, 3) + center) * 0.25,
        }
        v = np.clip(lp[sel], 0.0, 1.0)            # (m,4,3)
        acc = np.zeros((len(sel), 4), np.float32)
        sacc = np.zeros((len(sel), 4), np.float32)
        bacc = np.zeros((len(sel), 4), np.float32)
        LL = None
        if sky is not None:
            # light coords per corner (sky, block), LightCoordsUtil.smoothBlend
            nxt_open = get(cell + D, Pm)
            ls = [(get(base + C[i], sky), get(base + C[i], blk)) for i in range(4)]
            # lightCenter: own cell, replaced by the neighbour's when the face is cubic or the neighbour not opaque
            ctr = tuple(np.where(cubic | nxt_open, get(cell + D, g), get(cell, g)) for g in (sky, blk))

            def lcorner(i, j):
                c = base + C[i] + C[j]
                open_ = pm[i] | pm[j]
                return (np.where(open_, get(c, sky), ls[0][0]), np.where(open_, get(c, blk), ls[0][1]))

            LL = {(0, 3): _smooth_blend(ls[3], ls[0], lcorner(0, 3), ctr),
                  (0, 2): _smooth_blend(ls[2], ls[0], lcorner(0, 2), ctr),
                  (1, 2): _smooth_blend(ls[2], ls[1], lcorner(1, 2), ctr),
                  (1, 3): _smooth_blend(ls[3], ls[1], lcorner(1, 3), ctr)}
        for (i, j), val in L.items():
            wi = _dir_weight(cs[i], v)
            wj = _dir_weight(cs[j], v)
            w = wi * wj
            acc += w * val[:, None]
            if LL is not None:
                sacc += w * LL[(i, j)][0][:, None]
                bacc += w * LL[(i, j)][1][:, None]
        out[sel] = np.clip(acc, 0.0, 1.0)
        if lout is not None:
            lout[sel] = lightmap(sacc, bacc)      # lightmap sampled per vertex (terrain.vsh)
    return out, lout


def _smooth_blend(n1, n2, n3, center):
    """LightCoordsUtil.smoothBlend on (sky, block) level pairs (float arrays, 0..15). When the centre is lit
    (sky > 2 or block > 2), a neighbour that is completely dark takes the centre's light and one with no sky
    light takes the centre's sky light; result = floor of the average in 1/16 level steps."""
    cs, cb = center
    use = (cs > 2) | (cb > 2)
    ssum, bsum = cs.astype(np.float32), cb.astype(np.float32)
    for s, b in (n1, n2, n3):
        dark = (s == 0) & (b == 0)
        s2 = np.where(use & (s == 0), cs, s)
        b2 = np.where(use & dark, cb, b)
        ssum = ssum + s2
        bsum = bsum + b2
    return np.floor(ssum * 4.0 + 1e-4) / 16.0, np.floor(bsum * 4.0 + 1e-4) / 16.0


# ----------------------------------------------------------------------------------------------
# light engine (sky light + block light, daylight)


# overworld at noon (DimensionTypes / EnvironmentAttributes / LightmapRenderStateExtractor, 26.3):
AMBIENT_LIGHT = 10 / 255.0                                            # AMBIENT_LIGHT_COLOR #0A0A0A
BLOCK_LIGHT_TINT = np.array([255, 216, 140], np.float32) / 255.0      # BLOCK_LIGHT_TINT -10100 = #FFD88C
BLOCK_FACTOR = 1.4                                                    # blockLightFlicker (~0) + 1.4
BRIGHTNESS_OPTION = 0.5                                               # options.gamma default (0.5)


def _lightmap_table(brightness=BRIGHTNESS_OPTION) -> np.ndarray:
    """The 16x16 lightmap texture (lightmap.fsh) as [sky, block] -> RGB."""
    lv = np.arange(16, dtype=np.float64) / 15.0
    gb = lv / (4.0 - 3.0 * lv)
    mixf = 0.9 * (2.0 * lv - 1.0) ** 2                                # parabolicMixFactor(block level)
    block_col = BLOCK_LIGHT_TINT[None, :] * (1.0 - mixf[:, None]) + mixf[:, None]
    color = (AMBIENT_LIGHT + gb[:, None, None] * 1.0                  # SkyLightColor white, SkyFactor 1
             + block_col[None, :, :] * (BLOCK_FACTOR * gb)[None, :, None])
    color = np.clip(color, 0.0, 1.0)
    mx = np.maximum(color.max(-1, keepdims=True), 1e-9)
    not_gamma = color * ((1.0 - (1.0 - mx) ** 4) / mx)
    return (color * (1.0 - brightness) + not_gamma * brightness).astype(np.float32)


LIGHTMAP = _lightmap_table()


def lightmap(sky, blk) -> np.ndarray:
    """RGB brightness (shape (..., 3)) for sky/block light levels (floats 0..15): the lightmap texture sampled
    with linear filtering at the (possibly fractional, smooth-blended) light coordinates, as terrain.vsh does."""
    s = np.clip(np.asarray(sky, np.float32), 0.0, 15.0)
    b = np.clip(np.asarray(blk, np.float32), 0.0, 15.0)
    s0 = np.floor(s).astype(np.int64)
    b0 = np.floor(b).astype(np.int64)
    s1 = np.minimum(s0 + 1, 15)
    b1 = np.minimum(b0 + 1, 15)
    fs = (s - s0)[..., None]
    fb = (b - b0)[..., None]
    T = LIGHTMAP
    out = (T[s0, b0] * (1 - fs) * (1 - fb) + T[s1, b0] * fs * (1 - fb) + T[s0, b1] * (1 - fs) * fb
           + T[s1, b1] * fs * fb)
    return out.astype(np.float32)


def compute_light(palette, grid):
    """Sky and block light levels (float32 grids 0..15) following the 26.3 LightEngine rules:
    * sky sources: every cell of a column down to the first cell that dampens light, is opaque or is cut off by
      a light-occluding face (ChunkSkyLightSources) gets 15;
    * propagation in all six directions loses max(1, dampening of the entered block) per step
      (LightEngine.getOpacity); opaque (solidRender) cells receive nothing;
    * blocks with useShapeForLightOcclusion (slabs, stairs, snow, ...) stop light where their face occlusion
      shapes and the neighbour's together cover the whole face (Shapes.faceShapeOccludes).
    Block light starts from each block's light emission."""
    npal = len(palette)
    op_p = np.array([p.solid_render for p in palette])
    damp_p = np.array([0.0 if p.solid_render else p.damp for p in palette], np.float32)
    emit_p = np.array([p.light for p in palette], np.float32)
    LF = [p.light_faces for p in palette]
    # B[d, a, b]: light moving in direction d from a cell with palette a into one with palette b is blocked
    B = np.zeros((6, npal, npal), bool)
    shaped = [i for i, f in enumerate(LF) if any(f)]
    for d in range(6):
        od = OPPOSITE[d]
        for a in shaped:
            for b in range(npal):
                if (LF[a][d] | LF[b][od]) == FULL_MASK:
                    B[d, a, b] = True
                if (LF[b][d] | LF[a][od]) == FULL_MASK:
                    B[d, b, a] = True
    op = op_p[grid]
    step = np.maximum(damp_p[grid], 1.0)               # max(1, dampening) of the entered cell
    X, Y, Z = grid.shape
    # sky sources (straight down while nothing dampens or occludes)
    sky = np.zeros(grid.shape, np.float32)
    open_col = np.ones((X, Z), bool)
    for y in range(Y - 1, -1, -1):
        g = grid[:, y, :]
        if y < Y - 1:
            open_col &= ~B[0, grid[:, y + 1, :], g]
        open_col &= ~op_p[g] & (damp_p[g] == 0.0)
        sky[:, y, :] = np.where(open_col, 15.0, 0.0)
    allowed = []
    for d in range(6):
        nb_ids = _shift(grid, DIRV[d], 0)               # palette of the neighbour n = c - v the light comes from
        allowed.append(~B[d, nb_ids, grid] & ~op)
    sky = _spread(sky, allowed, step)
    blk = _spread(emit_p[grid], allowed, step)
    return sky, blk


def _shift(a, v, fill):
    """out[c] = a[c - v] (out of range -> fill)."""
    out = np.full_like(a, fill)
    X, Y, Z = a.shape[:3]
    sx = slice(max(v[0], 0), X + min(v[0], 0))
    sy = slice(max(v[1], 0), Y + min(v[1], 0))
    sz = slice(max(v[2], 0), Z + min(v[2], 0))
    tx = slice(max(-v[0], 0), X + min(-v[0], 0))
    ty = slice(max(-v[1], 0), Y + min(-v[1], 0))
    tz = slice(max(-v[2], 0), Z + min(-v[2], 0))
    out[sx, sy, sz] = a[tx, ty, tz]
    return out


def _spread(L, allowed, step):
    L = L.astype(np.float32)
    for _ in range(15):
        new = L.copy()
        for d in range(6):
            src = _shift(L, DIRV[d], 0.0)
            cand = src - step
            np.maximum(new, np.where(allowed[d], cand, 0.0), out=new)
        if np.array_equal(new, L):
            break
        L = new
    return L


def _dir_weight(dirn: int, v):
    ax = (1, 1, 2, 2, 0, 0)[dirn]
    c = v[:, :, ax]
    return c if dirn in (1, 3, 5) else 1.0 - c


# ----------------------------------------------------------------------------------------------
# fluids


def _fluids(palette, grid, coords, ids, off, sky=None, blk=None):
    fl = np.array([p.fluid for p in palette], np.int8)
    amt = np.array([p.fluid_amount for p in palette], np.float32) / 9.0
    is_solid = np.array([p.solid for p in palette])           # legacy BlockState.isSolid
    if not (fl[ids] > 0).any():
        return None
    F = fl[grid]                       # fluid type per cell
    A = amt[grid]
    rows_pos, rows_uv, rows_spr, rows_rgb, rows_light, rows_layer, rows_tri = [], [], [], [], [], [], []
    still = {1: SPRITES.id("block/water_still"), 2: SPRITES.id("block/lava_still")}
    flow = {1: SPRITES.id("block/water_flow"), 2: SPRITES.id("block/lava_flow")}
    overlay_spr = SPRITES.id("block/water_overlay")

    sel = np.flatnonzero(fl[ids] > 0)
    for i in sel.tolist():
        x, y, z = coords[i]
        g = np.array([x, y, z]) + off
        t = int(F[g[0], g[1], g[2]])
        info = palette[ids[i]]

        def nb(dx, dy, dz):
            return g[0] + dx, g[1] + dy, g[2] + dz

        def height(c):
            if F[c] == t:
                up = (c[0], c[1] + 1, c[2])
                return 1.0 if F[up] == t else float(A[c])
            return -1.0 if is_solid[grid[c]] else 0.0

        h_self = height(tuple(g))
        if h_self >= 1.0:
            hNE = hNW = hSE = hSW = 1.0
        else:
            hN, hS = height(nb(0, 0, -1)), height(nb(0, 0, 1))
            hE, hW = height(nb(1, 0, 0)), height(nb(-1, 0, 0))

            def avg(h2, h1, corner):
                if h1 >= 1.0 or h2 >= 1.0:
                    return 1.0
                w = [0.0, 0.0]

                def add(h):
                    if h >= 0.8:
                        w[0] += h * 10
                        w[1] += 10
                    elif h >= 0.0:
                        w[0] += h
                        w[1] += 1
                if h1 > 0 or h2 > 0:
                    hc = height(corner)
                    if hc >= 1.0:
                        return 1.0
                    add(hc)
                add(h_self)
                add(h1)
                add(h2)
                return w[0] / w[1] if w[1] else h_self

            hNE = avg(hN, hE, nb(1, 0, -1))
            hNW = avg(hN, hW, nb(-1, 0, -1))
            hSE = avg(hS, hE, nb(1, 0, 1))
            hSW = avg(hS, hW, nb(-1, 0, 1))
        col = WATER_COLOR if t == 1 else (1.0, 1.0, 1.0)
        layer = LAYER_TRANSLUCENT if t == 1 else LAYER_SOLID
        # lava emits light 15: its lightmap value is ~1, but FluidRenderer still applies the directional shade
        if sky is not None and t == 1:
            up = nb(0, 1, 0)
            br = lightmap(max(sky[tuple(g)], sky[up]), max(blk[tuple(g)], blk[up]))
            col = tuple(float(c * b) for c, b in zip(col, br))
        up_state = palette[grid[nb(0, 1, 0)]]
        if F[nb(0, 1, 0)] != t:
            hmin = min(hNE, hNW, hSE, hSW)
            occ = up_state.masks[0]
            if not (occ == FULL_MASK and hmin >= 1.0):
                e = 0.001
                P = np.array([[x, y + hNW - e, z], [x, y + hSW - e, z + 1], [x + 1, y + hSE - e, z + 1],
                              [x + 1, y + hNE - e, z]], np.float32)
                fx, fz = _fluid_flow(tuple(int(v) for v in g), t, F, A, grid, palette)
                if fx == 0.0 and fz == 0.0:
                    uvq, top_spr = [(0, 0), (0, 1), (1, 1), (1, 0)], still[t]
                else:       # flowing sprite turned along FlowingFluid.getFlow (FluidRenderer top face)
                    ang = math.atan2(fz, fx) - math.pi / 2
                    s_, c_ = math.sin(ang) * 0.25, math.cos(ang) * 0.25
                    uvq = [(0.5 + (-c_ - s_), 0.5 + (-c_ + s_)), (0.5 + (-c_ + s_), 0.5 + (c_ + s_)),
                           (0.5 + (c_ + s_), 0.5 + (c_ - s_)), (0.5 + (c_ - s_), 0.5 + (-c_ - s_))]
                    top_spr = flow[t]
                L = 1.0
                _add_maybe_split(P, uvq, top_spr, col, L, layer, rows_pos, rows_uv, rows_spr, rows_rgb,
                                 rows_light, rows_layer, rows_tri)
        # sides
        sides = [
            (2, (0, 0, -1), hNW, hNE, [x, z + 0.001], [x + 1, z + 0.001]),
            (3, (0, 0, 1), hSE, hSW, [x + 1, z + 1 - 0.001], [x, z + 1 - 0.001]),
            (4, (-1, 0, 0), hSW, hNW, [x + 0.001, z + 1], [x + 0.001, z]),
            (5, (1, 0, 0), hNE, hSE, [x + 1 - 0.001, z], [x + 1 - 0.001, z + 1]),
        ]
        for d, dv, h0, h1, p0, p1 in sides:
            c = nb(*dv)
            if F[c] == t:
                continue
            # isFaceOccludedBySelf: own block face in direction d
            if info.masks[d] == FULL_MASK:
                continue
            nbs = palette[grid[c]]
            occ = nbs.masks[OPPOSITE[d]]
            if occ == FULL_MASK:
                continue
            if occ != 0 and _fluid_face_covered(occ, max(h0, h1)):
                continue
            # FluidRenderer: vertices (x0, y+hh0) (x1, y+hh1) (x1, y) (x0, y) face outwards; the reversed copy
            # (seen from inside the fluid) is added too unless the water_overlay sprite is used, which water
            # gets next to HalfTransparentBlock (glass, ice, ...) and leaves. Applies to water and lava alike.
            P = np.array([[p0[0], y + h0, p0[1]], [p1[0], y + h1, p1[1]], [p1[0], y, p1[1]], [p0[0], y, p0[1]]],
                         np.float32)
            uvq = [(0, (1 - h0) * 0.5), (0.5, (1 - h1) * 0.5), (0.5, 0.5), (0, 0.5)]
            L = CARDINAL[2] if d in (2, 3) else CARDINAL[4]
            overlay = t == 1 and ("HalfTransparentBlock" in nbs.ancestors or "LeavesBlock" in nbs.ancestors)
            spr = overlay_spr if overlay else flow[t]
            _add_maybe_split(P, uvq, spr, col, L, layer, rows_pos, rows_uv, rows_spr, rows_rgb, rows_light,
                             rows_layer, rows_tri)
            if not overlay:
                _add_maybe_split(P[[0, 3, 2, 1]], [uvq[0], uvq[3], uvq[2], uvq[1]], spr, col, L, layer, rows_pos,
                                 rows_uv, rows_spr, rows_rgb, rows_light, rows_layer, rows_tri)
        # bottom
        dn = nb(0, -1, 0)
        if F[dn] != t and palette[grid[dn]].masks[1] != FULL_MASK and info.masks[0] != FULL_MASK:
            P = np.array([[x, y + 0.001, z + 1], [x, y + 0.001, z], [x + 1, y + 0.001, z], [x + 1, y + 0.001, z + 1]],
                         np.float32)
            _add_maybe_split(P, [(0, 1), (0, 0), (1, 0), (1, 1)], still[t], col, CARDINAL[0],
                             layer, rows_pos, rows_uv, rows_spr, rows_rgb, rows_light, rows_layer, rows_tri)
    if not rows_pos:
        return None
    n = len(rows_pos)
    q = Quads(np.array(rows_pos, np.float32), np.array(rows_uv, np.float32), np.array(rows_spr, np.int32),
              np.full(n, -1, np.int8), np.full(n, -1, np.int8), np.full(n, 1, np.int8), np.full(n, 1, np.int8),
              np.array(rows_layer, np.int8), np.zeros(n, np.int8), np.array(rows_rgb, np.float32))
    light = np.repeat(np.array(rows_light, np.float32)[:, None, None], 4, axis=1)
    return q, np.repeat(light, 3, axis=2), np.array(rows_tri, bool)


_fluid_flow_blockers = None


def _blocks_fluid_flow() -> set:
    """Block tag minecraft:blocks_fluid_flow (data/tags_26.3.json)."""
    global _fluid_flow_blockers
    if _fluid_flow_blockers is None:
        try:
            import json
            tags = json.loads(assets.TAGS_JSON.read_text(encoding="utf-8")).get("tags", {})
            _fluid_flow_blockers = set(tags.get("minecraft:blocks_fluid_flow", []))
        except (OSError, ValueError):
            _fluid_flow_blockers = set()
    return _fluid_flow_blockers


def _fluid_flow(g, t, F, A, grid, palette):
    """Horizontal part of FlowingFluid.getFlow for the fluid cell g (grid coords) of type t."""
    own = float(A[g])
    fx = fz = 0.0
    for dx, dz in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        c = (g[0] + dx, g[1], g[2] + dz)
        ft = int(F[c])
        if ft != 0 and ft != t:          # affectsFlow: empty or the same fluid
            continue
        nh = float(A[c]) if ft == t else 0.0
        dist = 0.0
        if nh == 0.0:
            if palette[grid[c]].block not in _blocks_fluid_flow():
                b = (c[0], c[1] - 1, c[2])
                fb = int(F[b])
                if fb == 0 or fb == t:
                    bh = float(A[b]) if fb == t else 0.0
                    if bh > 0.0:
                        dist = own - (bh - 0.8888889)
        else:
            dist = own - nh
        fx += dx * dist
        fz += dz * dist
    return fx, fz


def _fluid_face_covered(occ_mask: int, h: float) -> bool:
    need = 0
    rows = int(np.ceil(min(max(h, 0.0), 1.0) * 16))
    for u in range(16):
        for v in range(rows):
            need |= 1 << (u * 16 + v)
    return (need & ~occ_mask) == 0


def _add_maybe_split(P, uvq, spr, col, L, layer, rp, ru, rs, rc, rl, rly, rt):
    """Add a quad; when non-planar (sloped water) add it as two triangles."""
    uvq = np.array(uvq, np.float32)
    par = P[0] + P[2] - P[1] - P[3]
    if np.abs(par).max() < 1e-5:
        rp.append(P)
        ru.append(uvq)
        rs.append(spr)
        rc.append(col)
        rl.append(L)
        rly.append(layer)
        rt.append(False)
        return
    for (a, b, c) in ((0, 1, 3), (2, 3, 1)):
        Pt = np.array([P[a], P[b], P[b] + P[c] - P[a], P[c]], np.float32)
        Ut = np.array([uvq[a], uvq[b], uvq[b] + uvq[c] - uvq[a], uvq[c]], np.float32)
        rp.append(Pt)
        ru.append(Ut)
        rs.append(spr)
        rc.append(col)
        rl.append(L)
        rly.append(layer)
        rt.append(True)
