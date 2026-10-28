"""Block registry for Minecraft Java 26.3 (data version 5023).

Ground truth:
  * ``data/blocks_26.3.json`` -- dumped from the real game registry by ``blockwright/java/RegistryDump.java``
    (ids, properties with legal values in game order, defaults, item, per-state physics, collision shapes).
  * Block tags -- read from the 26.3 common jar (``data/minecraft/tags/block/*.json``), nested ``#tag``
    references resolved, cached to ``data/tags_26.3.json`` (key ``"tags"``).
  * Block class hierarchy (for ``instanceof`` checks the game makes, e.g. ``instanceof LeavesBlock``) --
    parsed from the decompiled 26.3 source (``net/minecraft/world/level/block``), cached in the same
    file under ``"class_ancestors"``.

Everything is loaded lazily once per process and all per-state work is cached, so calling these
functions in hot loops is fine.

A *state* is a string in vanilla command syntax.  The canonical form (returned by every function here)
always carries the namespace and **all** properties in registry order, e.g.
``minecraft:oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]``; a block without
properties is just ``minecraft:stone``.
"""
from __future__ import annotations

import difflib
import json
import os
import re
import zipfile
from pathlib import Path
from typing import NamedTuple

from . import config as _config

BLOCKS_JSON = _config.data_file("blocks")
TAGS_JSON = _config.data_file("tags")
COMMON_JAR = _config.client_jar()   # the vanilla client jar also carries data/minecraft/tags (downloaded by setup)
# Decompiled block sources (only needed to regenerate the class hierarchy cache for a new game version).
MCSRC_BLOCK = Path(os.environ.get("BLOCKWRIGHT_MCSRC_BLOCK", "")) if os.environ.get("BLOCKWRIGHT_MCSRC_BLOCK") else None

AIR = "minecraft:air"
DATA_VERSION: int | None = None   # set by _load() from the registry dump
GAME_VERSION: str | None = None
DIRS = ("down", "up", "north", "south", "west", "east")  # bit order of the sturdy mask in the dump
HORIZONTAL = ("north", "east", "south", "west")          # clockwise order seen from above

# Renamed / commonly mistyped ids -> hint shown in error messages (never applied silently).
_RENAME_HINTS = {
    "chain": "iron_chain", "grass": "short_grass", "grass_path": "dirt_path", "sign": "oak_sign",
    "wall_sign": "oak_wall_sign", "log": "oak_log", "planks": "oak_planks", "leaves": "oak_leaves",
    "stone_brick": "stone_bricks", "brick": "bricks", "wooden_door": "oak_door", "door": "oak_door",
    "lantern_hanging": "lantern[hanging=true]", "chains": "iron_chain", "shelf": "oak_shelf",
}


class Phys(NamedTuple):
    """Per-state physics from the registry dump (computed by the game with an empty world around)."""
    sturdy_faces: frozenset      # faces (names from DIRS) that are FULL-sturdy (isFaceSturdy)
    can_occlude: bool
    full_collision: bool         # isCollisionShapeFullBlock
    solid_render: bool
    light: int                   # light emission 0..15
    collision_boxes: tuple       # ((x1,y1,z1,x2,y2,z2), ...) in block units; fences reach y=1.5


class BlockInfo(NamedTuple):
    id: str
    cls: str                     # simple Java class name, e.g. "StairBlock"
    block_entity: bool
    item: str                    # item id of Block.asItem() ("minecraft:air" if none)
    properties: dict             # name -> tuple of legal values (registry order)
    default: dict                # name -> default value


_blocks: dict | None = None     # id -> BlockInfo
_raw: dict | None = None        # id -> raw json dict
_shapes: list | None = None
_shape_cache: dict = {}
_canon: dict = {}               # any accepted input string -> canonical
_parsed: dict = {}              # canonical -> (id, ((k, v), ...))
_phys_cache: dict = {}
_tags: dict | None = None       # tag id -> frozenset of block ids
_ancestors: dict | None = None  # class -> tuple(class, parent, grandparent, ...)
_short_ids: list | None = None
_prop_names: frozenset = frozenset()  # every property name used by any block


# ----------------------------------------------------------------------------------------------- loading
def _load():
    global _blocks, _raw, _shapes, _short_ids, _prop_names
    if _blocks is not None:
        return
    with open(BLOCKS_JSON, encoding="utf-8") as f:
        d = json.load(f)
    if not isinstance(d.get("data_version"), int) or "blocks" not in d:
        raise RuntimeError(f"{BLOCKS_JSON} is not a registry dump (run `python -m blockwright dump-registry`)")
    global DATA_VERSION, GAME_VERSION
    DATA_VERSION, GAME_VERSION = d["data_version"], d.get("version")
    blocks = {}
    for bid, b in d["blocks"].items():
        props = {k: tuple(v) for k, v in b["properties"].items()}
        blocks[bid] = BlockInfo(bid, b["class"], bool(b["block_entity"]), b["item"], props, dict(b["default"]))
    _raw = d["blocks"]
    _shapes = d["shapes"]
    _short_ids = sorted(k.split(":", 1)[1] for k in blocks)
    _prop_names = frozenset(k for b in blocks.values() for k in b.properties)
    _blocks = blocks


def all_blocks() -> list:
    """All block ids (``minecraft:...``) in registry order."""
    _load()
    return list(_blocks)


def info(block: str) -> BlockInfo:
    """Registry info for a block id or state (``BlockInfo`` named tuple)."""
    _load()
    bid = _norm_id(block)
    try:
        return _blocks[bid]
    except KeyError:
        raise ValueError(_unknown_block_msg(bid, block)) from None


def exists(block_id: str) -> bool:
    """True if ``block_id`` (namespace optional, no properties) is a registered block."""
    _load()
    return _norm_id(block_id) in _blocks


def _norm_id(s: str) -> str:
    s = s.split("[", 1)[0].strip()
    return s if ":" in s else "minecraft:" + s


def _unknown_block_msg(bid: str, original: str) -> str:
    short = bid.split(":", 1)[1]
    sugg = difflib.get_close_matches(short, _short_ids, n=6, cutoff=0.6)
    hint = _RENAME_HINTS.get(short)
    if hint and hint not in sugg:
        sugg.insert(0, hint)
    if not sugg:
        sugg = [i for i in _short_ids if short in i][:6]
    msg = f"Unknown block '{bid}' in state {original!r} (Minecraft 26.3 registry)."
    if sugg:
        msg += " Did you mean: " + ", ".join(sugg) + "?"
    return msg


# ------------------------------------------------------------------------------------------ state parsing
_STATE_RE = re.compile(r"^\s*([a-z0-9_.\-]+:)?([a-z0-9_./\-]+)\s*(?:\[(.*)\])?\s*$")


def parse_state(state: str) -> str:
    """Validate ``state`` and return its canonical full form.

    Accepts ``"oak_stairs[facing=north]"``, ``"minecraft:oak_stairs"``, spaces around ``,``/``=``.
    Missing properties get registry defaults; unknown blocks/properties/values raise ``ValueError``
    with close-match suggestions.
    """
    try:
        return _canon[state]
    except KeyError:
        pass
    except TypeError:
        raise TypeError(f"block state must be a str, got {type(state).__name__}: {state!r}") from None
    if not isinstance(state, str):
        raise TypeError(f"block state must be a str, got {type(state).__name__}: {state!r}")
    _load()
    m = _STATE_RE.match(state)
    if not m:
        raise ValueError(f"Malformed block state {state!r}; expected e.g. 'minecraft:oak_stairs[facing=north,half=top]'")
    ns, name, body = m.group(1) or "minecraft:", m.group(2), m.group(3)
    bid = ns + name
    if bid not in _blocks:
        raise ValueError(_unknown_block_msg(bid, state))
    given = {}
    if body is not None and body.strip():
        for part in body.split(","):
            if "=" not in part:
                raise ValueError(f"Malformed property {part.strip()!r} in {state!r}; expected key=value")
            k, v = (t.strip() for t in part.split("=", 1))
            if k in given:
                raise ValueError(f"Property {k!r} given twice in {state!r}")
            given[k] = v
    canon = _build(bid, given, state)
    _canon[state] = canon
    return canon


def _build(bid: str, given: dict, original) -> str:
    bi = _blocks[bid]
    for k, v in given.items():
        legal = bi.properties.get(k)
        if legal is None:
            names = list(bi.properties)
            sugg = difflib.get_close_matches(k, names, n=3, cutoff=0.5)
            msg = f"Block {bid} has no property {k!r} (in {original!r}). "
            msg += f"Valid properties: {', '.join(names) if names else '(none)'}."
            if sugg:
                msg += " Did you mean: " + ", ".join(sugg) + "?"
            raise ValueError(msg)
        if v not in legal:
            sugg = difflib.get_close_matches(str(v), legal, n=3, cutoff=0.4)
            msg = f"Invalid value {v!r} for {bid}.{k} (in {original!r}); legal values: {', '.join(legal)}."
            if sugg:
                msg += " Did you mean: " + ", ".join(sugg) + "?"
            raise ValueError(msg)
    if not bi.properties:
        canon = bid
        items = ()
    else:
        items = tuple((k, given.get(k, bi.default[k])) for k in bi.properties)
        canon = bid + "[" + ",".join(f"{k}={v}" for k, v in items) + "]"
    if canon not in _parsed:
        _parsed[canon] = (bid, items)
        _canon[canon] = canon
    return canon


def _split(state: str):
    """canonical (id, ((k, v), ...)) for any accepted state string."""
    c = _canon.get(state)
    if c is None:
        c = parse_state(state)
    return _parsed[c]


def _sv(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def make_state(block_id: str, props: dict | None = None, **kw) -> str:
    """Canonical state from a block id plus properties (dict and/or keywords; bool/int values allowed)."""
    _load()
    bid = _norm_id(block_id)
    if bid not in _blocks:
        raise ValueError(_unknown_block_msg(bid, block_id))
    given = {}
    if props:
        given.update({k: _sv(v) for k, v in props.items()})
    given.update({k: _sv(v) for k, v in kw.items()})
    return _build(bid, given, f"{bid}{given}")


def props(state: str) -> dict:
    """All properties of ``state`` as a new dict {name: value-string} (registry order)."""
    return dict(_split(state)[1])


def prop(state: str, name: str):
    """Single property value (string) or ``None`` if the block does not have that property.

    A name that NO block in 26.3 has (a typo such as ``"facng"``) raises ``ValueError`` instead of quietly
    returning ``None``."""
    items = _split(state)[1]
    for k, v in items:
        if k == name:
            return v
    if name not in _prop_names:
        sugg = difflib.get_close_matches(str(name), sorted(_prop_names), n=3, cutoff=0.6)
        raise ValueError(f"No block in 26.3 has a property {name!r}" + (f"; did you mean: {', '.join(sugg)}?" if sugg else ""))
    return None


def block_id(state: str) -> str:
    """Namespaced block id of a state (``minecraft:oak_stairs``)."""
    return _split(state)[0]


def with_props(state: str, **changes) -> str:
    """Copy of ``state`` with some properties changed (validated)."""
    bid, items = _split(state)
    given = dict(items)
    given.update({k: _sv(v) for k, v in changes.items()})
    return _build(bid, given, f"{state} + {changes}")


def with_block(state: str, new_block: str, **changes) -> str:
    """Swap the block of ``state`` keeping every property the new block also has with a legal value.

    Example: ``with_block("oak_stairs[facing=east]", "spruce_stairs")``.
    """
    _load()
    nid = _norm_id(new_block)
    if nid not in _blocks:
        raise ValueError(_unknown_block_msg(nid, new_block))
    legal = _blocks[nid].properties
    given = {k: v for k, v in _split(state)[1] if k in legal and v in legal[k]}
    given.update({k: _sv(v) for k, v in changes.items()})
    return _build(nid, given, f"{new_block} from {state}")


def default_state(block_id: str) -> str:
    return make_state(block_id)


def is_air(state: str) -> bool:
    """True for air, cave_air and void_air."""
    return bool(_phys_raw(state)[1] & 8)


# --------------------------------------------------------------------------------------------- physics
def _phys_raw(state: str):
    c = _canon.get(state) or parse_state(state)
    r = _phys_cache.get(c)
    if r is None:
        bid, items = _parsed[c]
        raw = _raw[bid]
        enc = raw.get("phys")
        if enc is None:
            enc = raw["phys_by_state"][",".join(f"{k}={v}" for k, v in items)]
        mask, flags, light, shape = (int(t) for t in enc.split(","))
        r = (mask, flags, light, shape)
        _phys_cache[c] = r
    return r


def _boxes(idx: int) -> tuple:
    b = _shape_cache.get(idx)
    if b is None:
        s = _shapes[idx]
        b = tuple(tuple(float(t) for t in part.split()) for part in s.split(";")) if s else ()
        _shape_cache[idx] = b
    return b


def phys(state: str) -> Phys:
    """``Phys(sturdy_faces, can_occlude, full_collision, solid_render, light, collision_boxes)``."""
    mask, flags, light, shape = _phys_raw(state)
    sturdy = frozenset(DIRS[i] for i in range(6) if mask & (1 << i))
    return Phys(sturdy, bool(flags & 1), bool(flags & 2), bool(flags & 4), light, _boxes(shape))


def sturdy(state: str, face: str) -> bool:
    """``state.isFaceSturdy(face)`` (FULL support type) with an empty world around."""
    return bool(_phys_raw(state)[0] & (1 << DIRS.index(face)))


def collision_boxes(state: str) -> tuple:
    return _boxes(_phys_raw(state)[3])


def full_collision(state: str) -> bool:
    return bool(_phys_raw(state)[1] & 2)


def light(state: str) -> int:
    return _phys_raw(state)[2]


def item(state: str) -> str:
    """Item id the game associates with the block (``Block.asItem()``); ``minecraft:air`` if none."""
    return info(block_id(state)).item


# ------------------------------------------------------------------------------------- tags & classes
def _read_tags_from_jar(jar: Path) -> dict:
    raw = {}
    prefix = "data/minecraft/tags/block/"
    with zipfile.ZipFile(jar) as z:
        for n in z.namelist():
            if n.startswith(prefix) and n.endswith(".json"):
                tag = "minecraft:" + n[len(prefix):-5]
                raw[tag] = json.loads(z.read(n).decode("utf-8")).get("values", [])
    resolved: dict = {}

    def resolve(tag, stack=()):
        if tag in resolved:
            return resolved[tag]
        if tag in stack:
            raise RuntimeError(f"cyclic block tag {tag}")
        out = set()
        for e in raw.get(tag, []):
            ref = e["id"] if isinstance(e, dict) else e
            if ref.startswith("#"):
                r = ref[1:] if ":" in ref else "minecraft:" + ref[1:]
                out |= resolve(r, stack + (tag,))
            else:
                out.add(ref if ":" in ref else "minecraft:" + ref)
        resolved[tag] = out
        return out

    for t in raw:
        resolve(t)
    return {t: sorted(v) for t, v in sorted(resolved.items())}


def _read_class_ancestors() -> dict:
    """{class: [parent, grandparent, ...]} for every block class in the dump, from the decompiled source."""
    pat = re.compile(r"^(?:public |protected |private )?(?:abstract |final |sealed |non-sealed |static )*"
                     r"class (\w+)(?:<[^>]*>)? extends (\w+)", re.M)
    parents = {}
    for dp, _dn, fn in os.walk(MCSRC_BLOCK):
        for f in fn:
            if f.endswith(".java"):
                with open(os.path.join(dp, f), encoding="utf-8", errors="replace") as fh:
                    for m in pat.finditer(fh.read()):
                        parents.setdefault(m.group(1), m.group(2))
    _load()
    out = {}
    for cls in sorted({b.cls for b in _blocks.values()}):
        chain, c = [], cls
        while c in parents and len(chain) < 20:
            c = parents[c]
            chain.append(c)
        out[cls] = chain
    return out


def _load_tags():
    global _tags, _ancestors
    if _tags is not None:
        return
    cache = None
    if TAGS_JSON.exists():
        with open(TAGS_JSON, encoding="utf-8") as f:
            cache = json.load(f)
        if "tags" not in cache or "class_ancestors" not in cache:
            cache = None
    if cache is None:
        if not COMMON_JAR.exists():
            raise RuntimeError(f"Block tags unavailable: neither {TAGS_JSON} nor {COMMON_JAR} exists")
        if MCSRC_BLOCK is None or not MCSRC_BLOCK.exists():
            raise RuntimeError(f"Class hierarchy unavailable: no cache {TAGS_JSON}; set BLOCKWRIGHT_MCSRC_BLOCK to the "
                               "decompiled net/minecraft/world/level/block folder to regenerate it")
        cache = {"version": _config.mc_version(), "source": COMMON_JAR.name, "tags": _read_tags_from_jar(COMMON_JAR),
                 "class_ancestors": _read_class_ancestors()}
        tmp = TAGS_JSON.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=0, sort_keys=True)
        os.replace(tmp, TAGS_JSON)
    _tags = {t: frozenset(v) for t, v in cache["tags"].items()}
    _ancestors = {c: (c,) + tuple(a) for c, a in cache["class_ancestors"].items()}


def _norm_tag(tag: str) -> str:
    tag = tag.lstrip("#")
    return tag if ":" in tag else "minecraft:" + tag


def tag_members(tag: str) -> frozenset:
    """All block ids in a block tag (nested tags resolved). Unknown tag -> ValueError."""
    _load_tags()
    t = _norm_tag(tag)
    try:
        return _tags[t]
    except KeyError:
        sugg = difflib.get_close_matches(t, list(_tags), n=5, cutoff=0.6)
        raise ValueError(f"Unknown block tag {tag!r}." + (f" Did you mean: {', '.join(sugg)}?" if sugg else "")) from None


def all_tags() -> list:
    _load_tags()
    return sorted(_tags)


def has_tag(state_or_id: str, tag: str) -> bool:
    """``state.is(BlockTags.X)``, e.g. ``has_tag("oak_fence[north=true]", "minecraft:fences")``."""
    return _block_of(state_or_id) in tag_members(tag)


def _block_of(state_or_id: str) -> str:
    if "[" in state_or_id:
        return block_id(state_or_id)
    c = _canon.get(state_or_id)
    if c is not None:
        return _parsed[c][0]
    _load()
    bid = _norm_id(state_or_id)
    if bid not in _blocks:      # has_tag("chain", ...) must not silently answer False for a non-existent block
        raise ValueError(_unknown_block_msg(bid, state_or_id))
    return bid


def block_class(state_or_id: str) -> str:
    """Simple Java class name of the block (``"StairBlock"``)."""
    return info(_block_of(state_or_id)).cls


def class_chain(state_or_id: str) -> tuple:
    """(class, parent, grandparent, ...) e.g. ('MangroveLeavesBlock', 'TintedParticleLeavesBlock', ..., 'LeavesBlock', ...)."""
    _load_tags()
    cls = block_class(state_or_id)
    return _ancestors.get(cls, (cls,))


def is_a(state_or_id: str, cls: str) -> bool:
    """Java ``block instanceof <cls>`` (by simple class name), using the decompiled class hierarchy."""
    return cls in class_chain(state_or_id)


def property_names() -> dict:
    """{property name: sorted list of distinct legal-value tuples} over the whole registry."""
    _load()
    out: dict = {}
    for b in _blocks.values():
        for k, v in b.properties.items():
            out.setdefault(k, set()).add(v)
    return {k: sorted(v) for k, v in sorted(out.items())}


def data_version() -> int:
    """Data version of the loaded registry dump (5023 for 26.3)."""
    _load()
    return DATA_VERSION
