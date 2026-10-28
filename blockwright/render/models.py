"""Block-state -> baked quads, following the 26.3 client model pipeline.

Ported from (decompiled 26.3 client):
  * BlockStateModelDispatcher / VariantSelector / multipart conditions  (blockstate JSON)
  * CuboidModelElement / CuboidFace / CuboidRotation                    (model JSON elements)
  * FaceBakery.bakeQuad / defaultFaceUV / uvlock via BlockMath.getFaceTransformation
  * Quadrant / OctahedralGroup                                          (variant x/y/z rotations)
  * render layer per quad from sprite transparency (BakedQuad.MaterialInfo / SpriteContents)

A baked quad is stored in block-local coordinates (block units, origin at the block's min corner).
"""
from __future__ import annotations

import math
import zlib
from dataclasses import dataclass, field

import numpy as np

from . import assets

# Direction order and vectors exactly as net.minecraft.core.Direction (3D data value order).
DIRS = ["down", "up", "north", "south", "west", "east"]
DIR_INDEX = {d: i for i, d in enumerate(DIRS)}
DIR_VEC = np.array([[0, -1, 0], [0, 1, 0], [0, 0, -1], [0, 0, 1], [-1, 0, 0], [1, 0, 0]], dtype=np.float64)
OPPOSITE = [1, 0, 3, 2, 5, 4]

LAYER_SOLID, LAYER_CUTOUT, LAYER_TRANSLUCENT = 0, 1, 2

# FaceInfo vertex extents: (x, y, z) each 0 = min, 1 = max
_FACE_INFO = {
    0: [(0, 0, 1), (0, 0, 0), (1, 0, 0), (1, 0, 1)],  # down
    1: [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)],  # up
    2: [(1, 1, 0), (1, 0, 0), (0, 0, 0), (0, 1, 0)],  # north
    3: [(0, 1, 1), (0, 0, 1), (1, 0, 1), (1, 1, 1)],  # south
    4: [(0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)],  # west
    5: [(1, 1, 1), (1, 0, 1), (1, 0, 0), (1, 1, 0)],  # east
}


# ----------------------------------------------------------------------------------------------
# rotations


def _rot_x(deg: float) -> np.ndarray:
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def _rot_y(deg: float) -> np.ndarray:
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def _rot_z(deg: float) -> np.ndarray:
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def _clean(m: np.ndarray) -> np.ndarray:
    m = np.where(np.abs(m) < 1e-9, 0.0, m)
    r = np.round(m)
    return np.where(np.abs(m - r) < 1e-9, r, m)


def variant_matrix(x: int, y: int, z: int) -> np.ndarray:
    """Quadrant.fromXYZAngles: BLOCK_ROT_* are rotations by -angle; composed Z * Y * X."""
    return _clean(_rot_z(-z) @ _rot_y(-y) @ _rot_x(-x))


_L2G = {
    3: np.eye(3),           # south
    5: _clean(_rot_y(90)),  # east
    4: _clean(_rot_y(-90)),  # west
    2: _clean(_rot_y(180)),  # north
    1: _clean(_rot_x(-90)),  # up
    0: _clean(_rot_x(90)),  # down
}
_G2L = {k: _clean(np.linalg.inv(v)) for k, v in _L2G.items()}


def nearest_dir(v) -> int:
    """Direction.getApproximateNearest."""
    best, bd = 1, -1e9
    for i in range(6):
        d = float(np.dot(DIR_VEC[i], v))
        if d > bd:
            best, bd = i, d
    return best


def _closest_dir_or_none(v) -> int | None:
    """FaceBakery.findClosestDirection (only directions with positive product)."""
    if not np.all(np.isfinite(v)):
        return None
    best, bp = None, 0.0
    for i in range(6):
        p = float(np.dot(DIR_VEC[i], v))
        if p >= 0.0 and p > bp:
            best, bp = i, p
    return best


def uvlock_matrix(m: np.ndarray, face: int) -> np.ndarray:
    """Inverse of BlockMath.getFaceTransformation(m, face) (3x3)."""
    action = m @ _L2G[face]
    n = action @ np.array([0.0, 0.0, 1.0])
    new_side = nearest_dir(n)
    ft = _G2L[new_side] @ action
    return _clean(np.linalg.inv(ft))


# ----------------------------------------------------------------------------------------------
# state strings


def parse_state(s: str) -> tuple[str, dict]:
    s = s.strip()
    if "[" in s:
        name, rest = s.split("[", 1)
        rest = rest.rstrip("]")
        props = {}
        for kv in rest.split(","):
            if kv:
                k, v = kv.split("=", 1)
                props[k.strip()] = v.strip()
    else:
        name, props = s, {}
    if ":" not in name:
        name = "minecraft:" + name
    return name, props


def full_props(block_id: str, props: dict) -> dict:
    reg = assets.registry()["blocks"].get(block_id)
    if reg is None:
        return dict(props)
    out = dict(reg.get("default", {}))
    out.update(props)
    return out


def canonical(s: str) -> str:
    bid, props = parse_state(s)
    props = full_props(bid, props)
    reg = assets.registry()["blocks"].get(bid)
    order = list(reg["properties"].keys()) if reg else sorted(props)
    if not props:
        return bid
    return bid + "[" + ",".join(f"{k}={props[k]}" for k in order if k in props) + "]"


# ----------------------------------------------------------------------------------------------
# blockstate dispatch


def pos_hash(x: int, y: int, z: int, salt: int = 0) -> int:
    """Deterministic positional hash (stands in for Mth.getSeed + RandomSource)."""
    h = (x * 3129871) ^ (z * 116129781) ^ (y * 7432873) ^ (salt * 2654435761)
    h = (h * h * 42317861 + h * 11) & 0xFFFFFFFFFFFF
    return h >> 16


def _cond_match(cond, props: dict) -> bool:
    if "OR" in cond:
        return any(_cond_match(c, props) for c in cond["OR"])
    if "AND" in cond:
        return all(_cond_match(c, props) for c in cond["AND"])
    for k, v in cond.items():
        v = str(v).lower() if isinstance(v, bool) else str(v)
        neg = v.startswith("!")
        if neg:
            v = v[1:]
        ok = props.get(k) in v.split("|")
        if ok == neg:
            return False
    return True


def _variant_key_match(key: str, props: dict) -> bool:
    if key == "":
        return True
    for kv in key.split(","):
        k, v = kv.split("=", 1)
        if props.get(k) != v:
            return False
    return True


def _pick_index(entry, h: int) -> int:
    if isinstance(entry, dict):
        return 0
    total = sum(int(e.get("weight", 1)) for e in entry)
    r = h % max(total, 1)
    for i, e in enumerate(entry):
        r -= int(e.get("weight", 1))
        if r < 0:
            return i
    return len(entry) - 1


def _matching_entries(block_id: str, props: dict) -> list:
    bs = assets.blockstate_json(block_id)
    if bs is None:
        return []
    out = []
    if "variants" in bs:
        for key, entry in bs["variants"].items():
            if _variant_key_match(key, props):
                out.append(entry)
                break
    else:
        for part in bs.get("multipart", []):
            if "when" not in part or _cond_match(part["when"], props):
                out.append(part["apply"])
    return out


_has_model_cache: dict = {}


def has_model(block_id: str, props: dict) -> bool:
    """False when the game would show the missing model for this state: no blockstate file, a `variants`
    definition with no entry matching the state, or a referenced model file that does not exist. A multipart
    state that matches no part (or a model without elements) is a valid, invisible model."""
    key = (block_id, tuple(sorted(props.items())))
    r = _has_model_cache.get(key)
    if r is None:
        bs = assets.blockstate_json(block_id)
        if bs is None:
            r = False
        else:
            entries = _matching_entries(block_id, props)
            r = bool(entries) or "variants" not in bs
            for e in entries:
                for v in (e if isinstance(e, list) else [e]):
                    if resolve_model(v.get("model", "")) is None:
                        r = False
        _has_model_cache[key] = r
    return r


def has_random_variants(block_id: str, props: dict) -> bool:
    return any(isinstance(e, list) and len(e) > 1 for e in _matching_entries(block_id, props))


def pick_signature(block_id: str, props: dict, h: int) -> tuple:
    """Indices of the weighted alternatives chosen for positional hash h (one per part)."""
    return tuple(_pick_index(e, h) for e in _matching_entries(block_id, props))


def select_parts(block_id: str, props: dict, signature: tuple | None = None) -> list[dict]:
    """Return the list of variant dicts {model, x, y, z, uvlock} for this state."""
    out = []
    for i, e in enumerate(_matching_entries(block_id, props)):
        if isinstance(e, dict):
            out.append(e)
        else:
            k = signature[i] if signature and i < len(signature) else 0
            out.append(e[min(k, len(e) - 1)])
    return out


# ----------------------------------------------------------------------------------------------
# model resolution


@dataclass
class ResolvedModel:
    elements: list
    textures: dict
    ambientocclusion: bool


_resolved_cache: dict[str, ResolvedModel | None] = {}


def resolve_model(model_id: str) -> ResolvedModel | None:
    if model_id in _resolved_cache:
        return _resolved_cache[model_id]
    chain = []
    mid = model_id
    seen = set()
    while mid and mid not in seen:
        seen.add(mid)
        if assets.strip_ns(mid).startswith("builtin/"):
            break
        j = assets.model_json(mid)
        if j is None:
            break
        chain.append(j)
        mid = j.get("parent")
    if not chain:
        _resolved_cache[model_id] = None
        return None
    textures: dict = {}
    for j in reversed(chain):
        textures.update(j.get("textures", {}))
    elements = None
    ao = None
    for j in chain:
        if elements is None and "elements" in j:
            elements = j["elements"]
        if ao is None and "ambientocclusion" in j:
            ao = bool(j["ambientocclusion"])
    rm = ResolvedModel(elements or [], textures, True if ao is None else ao)
    _resolved_cache[model_id] = rm
    return rm


def resolve_texture(textures: dict, ref: str) -> tuple[str | None, bool]:
    """Resolve a face's texture slot (TextureSlots: the face value always names a slot, with or without the
    leading '#'; slot values starting with '#' reference other slots, anything else is a sprite).
    Returns (sprite id without namespace, force_translucent)."""
    seen = set()
    if not isinstance(ref, str) or not ref:
        return None, False
    val = ref if ref.startswith("#") else "#" + ref
    while True:
        if isinstance(val, dict):
            return assets.strip_ns(val.get("sprite", "")), bool(val.get("force_translucent", False))
        if not isinstance(val, str):
            return None, False
        if val.startswith("#"):
            key = val[1:]
            if key in seen or key not in textures:
                return None, False
            seen.add(key)
            val = textures[key]
            continue
        return assets.strip_ns(val), False


# ----------------------------------------------------------------------------------------------
# sprite table + transparency


class SpriteTable:
    """Global sprite name <-> id table shared by all baked geometry."""

    def __init__(self):
        self.names: list[str] = []
        self.ids: dict[str, int] = {}
        self.missing = self.id("__missing__")

    def id(self, name: str) -> int:
        i = self.ids.get(name)
        if i is None:
            i = len(self.names)
            self.names.append(name)
            self.ids[name] = i
        return i

    def image(self, i: int) -> np.ndarray:
        name = self.names[i]
        img = None if name.startswith("__") else assets.load_texture(name)
        if img is None:
            img = np.zeros((16, 16, 4), np.uint8)
            img[..., 3] = 255
            img[:8, :8, 0] = img[8:, 8:, 0] = 248
            img[:8, :8, 2] = img[8:, 8:, 2] = 248
        return img


SPRITES = SpriteTable()

_transp_cache: dict = {}


def sprite_transparency(sprite: str, u0, v0, u1, v1) -> int:
    """SpriteContents.computeTransparency over the uv rect (uv in 0..1). Returns layer."""
    key = (sprite, round(u0, 4), round(v0, 4), round(u1, 4), round(v1, 4))
    if key in _transp_cache:
        return _transp_cache[key]
    img = assets.load_texture(sprite)
    if img is None:
        res = LAYER_SOLID
    else:
        h, w = img.shape[:2]
        x0, y0 = int(math.floor(min(u0, u1) * w)), int(math.floor(min(v0, v1) * h))
        x1, y1 = int(math.ceil(max(u0, u1) * w)), int(math.ceil(max(v0, v1) * h))
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(w, max(x1, x0 + 1)), min(h, max(y1, y0 + 1))
        a = img[y0:y1, x0:x1, 3]
        if a.size == 0:
            res = LAYER_SOLID
        elif np.any((a > 0) & (a < 255)):
            res = LAYER_TRANSLUCENT
        elif np.any(a == 0):
            res = LAYER_CUTOUT
        else:
            res = LAYER_SOLID
    _transp_cache[key] = res
    return res


# ----------------------------------------------------------------------------------------------
# baked geometry container


@dataclass
class Quads:
    """Structure-of-arrays quad list. Positions in block units (block-local or world)."""
    pos: np.ndarray = field(default_factory=lambda: np.zeros((0, 4, 3), np.float32))     # (n,4,3)
    uv: np.ndarray = field(default_factory=lambda: np.zeros((0, 4, 2), np.float32))      # (n,4,2) sprite-local 0..1
    sprite: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int32))
    tint: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int8))               # tintindex or -1
    cull: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int8))               # cull dir or -1
    shade: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int8))              # shading dir 0..5, -1=no shade
    face: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int8))               # actual quad direction 0..5
    layer: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int8))
    emit: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int8))
    rgb: np.ndarray | None = None                                                       # (n,3) explicit colour mult

    def __post_init__(self):
        if self.rgb is None:
            self.rgb = np.ones((len(self.sprite), 3), np.float32)

    def __len__(self):
        return len(self.sprite)

    @staticmethod
    def concat(items: list["Quads"]) -> "Quads":
        items = [q for q in items if q is not None and len(q)]
        if not items:
            return Quads()
        return Quads(*(np.concatenate([getattr(q, f) for q in items]) for f in
                       ("pos", "uv", "sprite", "tint", "cull", "shade", "face", "layer", "emit", "rgb")))

    def take(self, idx) -> "Quads":
        return Quads(*(getattr(self, f)[idx] for f in
                       ("pos", "uv", "sprite", "tint", "cull", "shade", "face", "layer", "emit", "rgb")))

    @staticmethod
    def from_lists(rows: list[tuple]) -> "Quads":
        """rows: (pos4x3, uv4x2, sprite, tint, cull, shade, face, layer, emit[, rgb])"""
        if not rows:
            return Quads()
        rows = [r if len(r) == 10 else tuple(r) + ((1.0, 1.0, 1.0),) for r in rows]
        pos, uv, spr, tint, cull, shade, face, layer, emit, rgb = zip(*rows)
        return Quads(np.asarray(pos, np.float32).reshape(-1, 4, 3), np.asarray(uv, np.float32).reshape(-1, 4, 2),
                     np.asarray(spr, np.int32), np.asarray(tint, np.int8), np.asarray(cull, np.int8),
                     np.asarray(shade, np.int8), np.asarray(face, np.int8), np.asarray(layer, np.int8),
                     np.asarray(emit, np.int8), np.asarray(rgb, np.float32).reshape(-1, 3))


def quad_face_dir(p: np.ndarray) -> int:
    n = np.cross(p[1] - p[0], p[2] - p[0])
    d = _closest_dir_or_none(n)
    return 1 if d is None else d


# ----------------------------------------------------------------------------------------------
# element baking


def _default_uv(frm, to, d):
    fx, fy, fz = frm
    tx, ty, tz = to
    if d == 0:
        return (fx, 16 - tz, tx, 16 - fz)
    if d == 1:
        return (fx, fz, tx, tz)
    if d == 2:
        return (16 - tx, 16 - ty, 16 - fx, 16 - fy)
    if d == 3:
        return (fx, 16 - ty, tx, 16 - fy)
    if d == 4:
        return (fz, 16 - ty, tz, 16 - fy)
    return (16 - tz, 16 - ty, 16 - fz, 16 - fy)


def _element_rotation(rot: dict):
    """Returns (origin (3,), 3x3 matrix incl. rescale) or None."""
    if not rot:
        return None
    origin = np.array(rot.get("origin", [8, 8, 8]), float) / 16.0
    if "axis" in rot or "angle" in rot:
        ang = float(rot.get("angle", 0))
        ax = rot.get("axis", "y")
        m = {"x": _rot_x, "y": _rot_y, "z": _rot_z}[ax](ang)
    else:
        x, y, z = float(rot.get("x", 0)), float(rot.get("y", 0)), float(rot.get("z", 0))
        m = _rot_z(z) @ _rot_y(y) @ _rot_x(x)          # Matrix4f.rotationZYX(z, y, x)
    if rot.get("rescale", False) and not np.allclose(m, np.eye(3)):
        scale = []
        for a in range(3):
            t = m[:, a]
            scale.append(1.0 / max(abs(t[0]), abs(t[1]), abs(t[2])))
        m = m @ np.diag(scale)
    return origin, m


_baked_cache: dict = {}


def bake_model(model_id: str, x: int = 0, y: int = 0, z: int = 0, uvlock: bool = False) -> tuple[Quads, bool]:
    """Bake one model with a variant rotation. Returns (quads in block-local coords, use_ao)."""
    key = (model_id, x % 360, y % 360, z % 360, bool(uvlock))
    if key in _baked_cache:
        return _baked_cache[key]
    rm = resolve_model(model_id)
    if rm is None:
        res = (Quads(), True)
        _baked_cache[key] = res
        return res
    M = variant_matrix(x, y, z)
    ident = np.allclose(M, np.eye(3))
    rows = []
    for el in rm.elements:
        frm = [float(v) for v in el["from"]]
        to = [float(v) for v in el["to"]]
        erot = _element_rotation(el.get("rotation"))
        shade_override = el.get("shade_direction_override")
        shade_override = DIR_INDEX.get(shade_override) if shade_override else None
        emit = int(el.get("light_emission", 0))
        lo = np.array(frm) / 16.0
        hi = np.array(to) / 16.0
        # UnbakedCuboidGeometry: faces lying on a zero-extent axis pair are not baked
        draw_axis = [True, True, True]          # x faces, y faces, z faces
        if frm[0] == to[0]:
            draw_axis[1] = draw_axis[2] = False
        if frm[1] == to[1]:
            draw_axis[0] = draw_axis[2] = False
        if frm[2] == to[2]:
            draw_axis[0] = draw_axis[1] = False
        for dname, face in el.get("faces", {}).items():
            d = DIR_INDEX.get(dname)
            if d is None or not draw_axis[(1, 1, 2, 2, 0, 0)[d]]:
                continue
            uvs = face.get("uv")
            if uvs is None:
                uvs = _default_uv(frm, to, d)
            uvs = [float(v) for v in uvs]
            sprite, force_tl = resolve_texture(rm.textures, face.get("texture", ""))
            if not sprite:
                sprite = "__missing__"          # unresolved slot: the game uses the missing sprite
            if force_tl:
                layer = LAYER_TRANSLUCENT
            else:
                layer = sprite_transparency(sprite, uvs[0] / 16, uvs[1] / 16, uvs[2] / 16, uvs[3] / 16)
            shift = (int(face.get("rotation", 0)) // 90) % 4
            uvT = uvlock_matrix(M, d) if (uvlock and not ident) else None
            pts, uvl = [], []
            for i in range(4):
                ex = _FACE_INFO[d][i]
                v = np.array([hi[0] if ex[0] else lo[0], hi[1] if ex[1] else lo[1], hi[2] if ex[2] else lo[2]])
                if erot is not None:
                    v = erot[1] @ (v - erot[0]) + erot[0]
                if not ident:
                    v = M @ (v - 0.5) + 0.5
                j = (i + shift) % 4
                ru = (uvs[0] if j in (0, 1) else uvs[2]) / 16.0
                rv = (uvs[1] if j in (0, 3) else uvs[3]) / 16.0
                if uvT is not None:
                    t = uvT @ np.array([ru - 0.5, rv - 0.5, 0.0])
                    ru, rv = t[0] + 0.5, t[1] + 0.5
                pts.append(v)
                uvl.append((ru, rv))
            pts = np.array(pts)
            fdir = quad_face_dir(pts)
            cull = face.get("cullface")
            cd = DIR_INDEX.get(cull, -1) if cull else -1
            if cd >= 0 and not ident:
                cd = nearest_dir(M @ DIR_VEC[cd])
            shade = shade_override if shade_override is not None else fdir
            tint = int(face.get("tintindex", -1))
            rows.append((pts, uvl, SPRITES.id(sprite), tint, cd, shade, fdir, layer, emit))
    res = (Quads.from_lists(rows), rm.ambientocclusion)
    _baked_cache[key] = res
    return res


def bake_state(block_id: str, props: dict, signature: tuple | None = None) -> tuple[Quads, bool]:
    """All quads for a block state (block-local), plus the AO flag of the first part."""
    parts = select_parts(block_id, props, signature)
    qs, ao = [], None
    for p in parts:
        q, a = bake_model(p.get("model", ""), int(p.get("x", 0)), int(p.get("y", 0)), int(p.get("z", 0)),
                          bool(p.get("uvlock", False)))
        if ao is None:
            ao = a
        qs.append(q)
    return Quads.concat(qs), (True if ao is None else ao)


def stable_hash(s: str) -> int:
    return zlib.crc32(s.encode("utf-8"))


_missing_cube = None


def missing_cube() -> Quads:
    """Magenta/black checker cube (the game's missing-model look) for states without geometry."""
    global _missing_cube
    if _missing_cube is None:
        rows = []
        for d in range(6):
            pts = np.array([[float(c) for c in ex] for ex in _FACE_INFO[d]])
            rows.append((pts, [(0, 0), (0, 1), (1, 1), (1, 0)], SPRITES.missing, -1, d, d, d, LAYER_SOLID, 0))
        _missing_cube = Quads.from_lists(rows)
    return _missing_cube
