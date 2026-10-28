"""Build: a sparse voxel model of one building, plus oriented Frames, prefab pasting, multi-block helpers,
QA markers and the ``finish()`` export pipeline.

Coordinates: x = east, y = up, z = south (Minecraft).  Any integers (negative allowed); ``finish()``
normalizes the bounding box to start at (0, 0, 0).  States are validated the moment they are set.
"""
from __future__ import annotations

import json
import operator
import os
import re
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

from . import registry as R
from .blocks import FACING_ALIASES, bed_id, door_id, has_alias, resolve_alias
from .rotate import mirror_state, rotate_pos, rotate_state

AIR = R.AIR


def default_out_dir() -> Path:
    """Where ``finish()`` writes: ``$BLOCKWRIGHT_WORKSPACE/out``; else, for a script in ``<ws>/builds/``,
    ``<ws>/out``; else ``./out``."""
    from . import config
    if config.get("workspace"):
        return config.workspace() / "out"
    script = Path(sys.argv[0]).resolve() if sys.argv and sys.argv[0] not in ("", "-c") else None
    if script is not None and script.is_file() and script.parent.name == "builds":
        return script.parent.parent / "out"
    return Path.cwd() / "out"
_DIR_OFF = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
_FRAME_TURNS = {"south": 0, "west": 1, "north": 2, "east": 3}   # quarter turns cw from the canonical frame


class BuildError(Exception):
    """Strict validation failed (message lists every problem)."""


def _i(v, what="coordinate"):
    try:
        return operator.index(v)
    except TypeError:
        raise TypeError(f"{what} must be an int, got {type(v).__name__} {v!r}") from None


def _pos(x, y, z):
    return (_i(x), _i(y), _i(z))


def _rng(a, b):
    a, b = _i(a), _i(b)
    return range(min(a, b), max(a, b) + 1)


def _canon(state) -> str:
    if not isinstance(state, str):
        raise TypeError(f"block state must be a str, got {type(state).__name__}: {state!r}"
                        + (" (a family member that does not exist for this material?)" if state is None else ""))
    if has_alias(state):
        raise ValueError(f"{state!r}: facing=out/in/left/right is a Frame alias -- set it through a Frame "
                         "(b.frame(origin, facing).set(...)) or use a real direction")
    return R.parse_state(state)


def _bresenham3(p1, p2):
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    dx, dy, dz = abs(x2 - x1), abs(y2 - y1), abs(z2 - z1)
    sx = 1 if x2 > x1 else -1
    sy = 1 if y2 > y1 else -1
    sz = 1 if z2 > z1 else -1
    pts = [(x1, y1, z1)]
    if dx >= dy and dx >= dz:
        e1, e2 = 2 * dy - dx, 2 * dz - dx
        while x1 != x2:
            x1 += sx
            if e1 >= 0:
                y1 += sy
                e1 -= 2 * dx
            if e2 >= 0:
                z1 += sz
                e2 -= 2 * dx
            e1 += 2 * dy
            e2 += 2 * dz
            pts.append((x1, y1, z1))
    elif dy >= dx and dy >= dz:
        e1, e2 = 2 * dx - dy, 2 * dz - dy
        while y1 != y2:
            y1 += sy
            if e1 >= 0:
                x1 += sx
                e1 -= 2 * dy
            if e2 >= 0:
                z1 += sz
                e2 -= 2 * dy
            e1 += 2 * dx
            e2 += 2 * dz
            pts.append((x1, y1, z1))
    else:
        e1, e2 = 2 * dy - dz, 2 * dx - dz
        while z1 != z2:
            z1 += sz
            if e1 >= 0:
                y1 += sy
                e1 -= 2 * dz
            if e2 >= 0:
                x1 += sx
                e2 -= 2 * dz
            e1 += 2 * dy
            e2 += 2 * dx
            pts.append((x1, y1, z1))
    return pts


def _in_ellipse(dx, dz, rx, rz):
    return (dx / (rx + 0.5)) ** 2 + (dz / (rz + 0.5)) ** 2 <= 1.0


# ===================================================================================================== Build
class Build:
    """Sparse voxel build.  ``b = Build("01_cozy_cottage", "Cozy Cottage", ground=0)``.

    Core: ``set/get/remove``, ``b[x, y, z] = state``, ``(x, y, z) in b``, ``fill``, ``walls``, ``line``,
    ``disk``/``ellipse``, ``ellipsoid``, ``replace``, ``bounds``, ``size``, ``count``, ``palette``.
    Orientation: ``frame(origin, facing)``; prefabs: ``paste(other, at, rot, mirror)``.
    Multi-block: ``door``, ``bed``, ``tall``.  QA markers: ``room``, ``entrance``, ``note``.
    Export: ``finish()``.
    """

    def __init__(self, slug: str, title: str, *, ground: int = 0, author: str | None = None, description: str = "",
                 allowed_blocks=None):
        if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", slug):
            # Litematica's FileNameUtils rewrites names with special characters or the substrings COM/PRN,
            # after which the file is not found -> only lowercase file-safe slugs are allowed.
            raise ValueError(f"slug must be lowercase letters/digits/_/- (e.g. '01_cozy_cottage'), got {slug!r}")
        self.slug = slug
        self.title = title
        self.ground = _i(ground, "ground")
        if author is None:
            from . import config
            author = config.get("author")
        self.author = author
        self.description = description
        # allowed-blocks constraint: a palette file path, a list of entries, or $BLOCKWRIGHT_PALETTE / --palette=FILE
        self.allowed_blocks = None
        self.set_allowed_blocks(allowed_blocks or os.environ.get("BLOCKWRIGHT_PALETTE") or None)
        self.blocks: dict = {}
        self.rooms: dict = {}
        self.entrances: list = []
        self.notes: list = []
        self.tile_entities: dict = {}

    def set_allowed_blocks(self, palette) -> None:
        """Restrict the build to the items a player owns (see blockwright.palette).  ``palette``: path to a palette
        file, a list of entries, or None to lift the constraint.  QA reports every item outside it as an error."""
        from .palette import load_palette, parse_palette
        if palette is None:
            self.allowed_blocks = None
        elif isinstance(palette, (str, Path)) and Path(palette).is_file():
            self.allowed_blocks = load_palette(palette)
        elif isinstance(palette, str):
            self.allowed_blocks = parse_palette(palette.replace(",", "\n"))
        else:
            self.allowed_blocks = parse_palette("\n".join(palette))

    def __repr__(self):
        return f"Build({self.slug!r}, {len(self.blocks)} blocks)"

    # ------------------------------------------------------------------------------------ single blocks
    def set(self, x, y, z, state) -> None:
        """Place ``state`` (validated; air removes)."""
        p = _pos(x, y, z)
        s = _canon(state)
        if R.is_air(s):
            self.blocks.pop(p, None)
        else:
            self.blocks[p] = s

    def get(self, x, y, z, default=AIR) -> str:
        """Canonical state at (x, y, z), or ``default`` ("minecraft:air") if empty."""
        return self.blocks.get(_pos(x, y, z), default)

    def remove(self, x, y, z) -> None:
        self.blocks.pop(_pos(x, y, z), None)

    def __getitem__(self, pos):
        return self.get(*pos)

    def __setitem__(self, pos, state):
        self.set(*pos, state)

    def __delitem__(self, pos):
        self.remove(*pos)

    def __contains__(self, pos):
        return _pos(*pos) in self.blocks

    def __len__(self):
        return len(self.blocks)

    def _where_ok(self, where, x, y, z) -> bool:
        if where is None:
            return True
        if where == "air":
            return (x, y, z) not in self.blocks
        if where == "occupied":
            return (x, y, z) in self.blocks
        if callable(where):
            return bool(where(x, y, z, self.blocks.get((x, y, z), AIR)))
        raise ValueError(f"where must be None, 'air', 'occupied' or callable(x, y, z, current), got {where!r}")

    def _put(self, x, y, z, s, where) -> int:
        if self._where_ok(where, x, y, z):
            if R.is_air(s):
                self.blocks.pop((x, y, z), None)
            else:
                self.blocks[(x, y, z)] = s
            return 1
        return 0

    # ------------------------------------------------------------------------------------------ shapes
    def fill(self, x1, y1, z1, x2, y2, z2, state, where=None) -> int:
        """Fill the inclusive box (any corner order).  ``where``: None | "air" | "occupied" |
        callable(x, y, z, current_state) -> bool.  ``state`` may be a callable(x, y, z) -> state for
        per-block variation (e.g. blockwright.noise.gradient).  Returns the number of cells written."""
        n = 0
        fixed = None if callable(state) else _canon(state)
        for y in _rng(y1, y2):
            for z in _rng(z1, z2):
                for x in _rng(x1, x2):
                    s = fixed if fixed is not None else _canon(state(x, y, z))
                    n += self._put(x, y, z, s, where)
        return n

    def walls(self, x1, y1, z1, x2, y2, z2, state, where=None) -> int:
        """The four vertical walls of the inclusive box (hollow outline, no floor/ceiling)."""
        xa, xb = sorted((_i(x1), _i(x2)))
        za, zb = sorted((_i(z1), _i(z2)))
        n = 0
        fixed = None if callable(state) else _canon(state)
        for y in _rng(y1, y2):
            for z in range(za, zb + 1):
                for x in range(xa, xb + 1):
                    if x in (xa, xb) or z in (za, zb):
                        s = fixed if fixed is not None else _canon(state(x, y, z))
                        n += self._put(x, y, z, s, where)
        return n

    def line(self, p1, p2, state, where=None) -> int:
        """3D Bresenham line between two (x, y, z) points, inclusive."""
        fixed = None if callable(state) else _canon(state)
        n = 0
        for x, y, z in _bresenham3(_pos(*p1), _pos(*p2)):
            s = fixed if fixed is not None else _canon(state(x, y, z))
            n += self._put(x, y, z, s, where)
        return n

    def ellipse(self, cx, y, cz, rx, rz, state, filled=True, where=None) -> int:
        """Horizontal ellipse at height y (radii in blocks; test (dx/(rx+.5))^2 + (dz/(rz+.5))^2 <= 1).
        ``filled=False`` gives a 1-block outline (cells inside with a 4-neighbour outside)."""
        cx, y, cz, rx, rz = _i(cx), _i(y), _i(cz), _i(rx, "radius"), _i(rz, "radius")
        fixed = None if callable(state) else _canon(state)
        n = 0
        for dz in range(-rz, rz + 1):
            for dx in range(-rx, rx + 1):
                if not _in_ellipse(dx, dz, rx, rz):
                    continue
                if not filled and all(_in_ellipse(dx + a, dz + b, rx, rz) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    continue
                x, z = cx + dx, cz + dz
                s = fixed if fixed is not None else _canon(state(x, y, z))
                n += self._put(x, y, z, s, where)
        return n

    def disk(self, cx, y, cz, r, state, filled=True, where=None) -> int:
        """Horizontal disk (circle) of radius r at height y."""
        return self.ellipse(cx, y, cz, r, r, state, filled=filled, where=where)

    def ellipsoid(self, cx, cy, cz, rx, ry, rz, state, where=None, filled=True) -> int:
        """Ellipsoid (filled by default; ``filled=False`` -> 1-block shell)."""
        cx, cy, cz = _i(cx), _i(cy), _i(cz)
        rx, ry, rz = _i(rx, "radius"), _i(ry, "radius"), _i(rz, "radius")
        fixed = None if callable(state) else _canon(state)

        def inside(dx, dy, dz):
            return (dx / (rx + 0.5)) ** 2 + (dy / (ry + 0.5)) ** 2 + (dz / (rz + 0.5)) ** 2 <= 1.0

        n = 0
        for dy in range(-ry, ry + 1):
            for dz in range(-rz, rz + 1):
                for dx in range(-rx, rx + 1):
                    if not inside(dx, dy, dz):
                        continue
                    if not filled and all(inside(dx + a, dy + b, dz + c) for a, b, c in
                                          ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))):
                        continue
                    x, y, z = cx + dx, cy + dy, cz + dz
                    s = fixed if fixed is not None else _canon(state(x, y, z))
                    n += self._put(x, y, z, s, where)
        return n

    def replace(self, match, new, region=None) -> int:
        """Replace matching blocks.  ``match``: block id ("oak_planks", any state of it), full state
        ("oak_stairs[facing=east]" -> that exact canonical state), tag ("#minecraft:logs") or
        callable(x, y, z, state) -> bool.  ``new``: state, or callable(x, y, z, old_state) -> state
        (return "minecraft:air" to delete; ``blockwright.registry.with_block`` keeps properties).
        ``region``: optional (x1, y1, z1, x2, y2, z2) inclusive.  Returns the number replaced."""
        if callable(match):
            pred = match
        elif isinstance(match, str) and match.startswith("#"):
            members = R.tag_members(match)
            pred = lambda x, y, z, s: R.block_id(s) in members  # noqa: E731
        elif isinstance(match, str) and "[" in match:
            target = _canon(match)
            pred = lambda x, y, z, s: s == target  # noqa: E731
        elif isinstance(match, str):
            bid = R.info(match).id
            pred = lambda x, y, z, s: R.block_id(s) == bid  # noqa: E731
        else:
            raise TypeError(f"match must be a block id, state, '#tag' or callable, got {match!r}")
        fixed = None if callable(new) else _canon(new)
        if region is not None:
            x1, y1, z1, x2, y2, z2 = region
            xs, ys, zs = _rng(x1, x2), _rng(y1, y2), _rng(z1, z2)
        n = 0
        for (x, y, z), s in sorted(self.blocks.items()):
            if region is not None and not (x in xs and y in ys and z in zs):
                continue
            if pred(x, y, z, s):
                ns = fixed if fixed is not None else _canon(new(x, y, z, s))
                if R.is_air(ns):
                    del self.blocks[(x, y, z)]
                else:
                    self.blocks[(x, y, z)] = ns
                n += 1
        return n

    # ------------------------------------------------------------------------------------------- info
    def bounds(self):
        """((minx, miny, minz), (maxx, maxy, maxz)) of the blocks, or None if empty."""
        if not self.blocks:
            return None
        xs, ys, zs = zip(*self.blocks)
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

    def size(self):
        b = self.bounds()
        if b is None:
            return (0, 0, 0)
        return tuple(b[1][i] - b[0][i] + 1 for i in range(3))

    def count(self, match=None) -> int:
        """Number of blocks (optionally only those of a block id / '#tag')."""
        if match is None:
            return len(self.blocks)
        if match.startswith("#"):
            m = R.tag_members(match)
            return sum(1 for s in self.blocks.values() if R.block_id(s) in m)
        if "[" in match:                                   # exact state, like replace()
            target = _canon(match)
            return sum(1 for s in self.blocks.values() if s == target)
        bid = R.info(match).id
        return sum(1 for s in self.blocks.values() if R.block_id(s) == bid)

    def palette(self) -> Counter:
        """Counter {state: count}."""
        return Counter(self.blocks.values())

    def copy(self, slug=None, title=None) -> "Build":
        b = Build(slug or self.slug, title or self.title, ground=self.ground, author=self.author, description=self.description)
        b.blocks = dict(self.blocks)
        b.rooms = dict(self.rooms)
        b.entrances = list(self.entrances)
        b.notes = list(self.notes)
        b.tile_entities = dict(self.tile_entities)
        return b

    # ----------------------------------------------------------------------------------- orientation
    def frame(self, origin, facing) -> "Frame":
        """Oriented local coordinates; see :class:`Frame`.  ``facing`` = direction the facade faces."""
        return Frame(self, origin, facing)

    def paste(self, other: "Build", at, rot: int = 0, mirror=None, where=None, markers: bool = False) -> int:
        """Copy ``other``'s blocks so its (0, 0, 0) lands on ``at``: mirror first ("x": x -> -x, "z": z -> -z),
        then rotate ``rot`` clockwise quarter turns (seen from above), then translate.  States are
        rotated/mirrored too.  ``where`` filters like ``fill``.  ``markers=True`` also copies rooms/entrances.
        Tile entities of pasted blocks come along (their NBT is not rotated)."""
        ax, ay, az = _pos(*at)
        rot = _i(rot, "rot") % 4
        if mirror not in (None, "x", "z"):
            raise ValueError(f"mirror must be None, 'x' or 'z', got {mirror!r}")
        dup = sorted(set(other.rooms) & set(self.rooms)) if markers else []
        if dup:     # checked before anything is pasted
            raise ValueError(f"paste(markers=True): room(s) {dup} already marked; give rooms unique names "
                             "(or paste with markers=False and call room() yourself)")
        n = 0

        def tf(x, y, z):
            if mirror == "x":
                x = -x
            elif mirror == "z":
                z = -z
            dx, dz = rotate_pos(x, z, rot)
            return ax + dx, ay + y, az + dz

        placed = set()
        for (x, y, z), s in sorted(other.blocks.items()):
            if mirror:
                s = mirror_state(s, mirror)
            s = rotate_state(s, rot)
            if self._put(*tf(x, y, z), s, where):
                placed.add((x, y, z))
                n += 1
        for q, nbt in other.tile_entities.items():
            if q in placed:
                self.tile_entities[tf(*q)] = nbt
        if markers:
            for name, p in other.rooms.items():
                self.rooms[name] = tf(*p)
            self.entrances.extend(tf(*p) for p in other.entrances)
        return n

    # ------------------------------------------------------------------------------------ multi-block
    def door(self, x, y, z, wood, facing, hinge="left", open=False, powered=False) -> None:
        """Two-block door, lower half at (x, y, z).  ``wood``: "spruce" | "iron" | "copper" | door id | WoodFamily.
        ``facing`` is the block-state facing = the direction a player looks when placing it (a door facing
        north sits on the south edge of its cell).  ``hinge`` per Minecraft: left/right as seen by that player."""
        did = door_id(wood)
        if facing in FACING_ALIASES:
            raise ValueError("facing alias (out/in/left/right) only works through a Frame: frame.door(...)")
        lower = R.make_state(did, facing=facing, half="lower", hinge=hinge, open=open, powered=powered)
        x, y, z = _pos(x, y, z)
        self.blocks[(x, y, z)] = lower
        self.blocks[(x, y + 1, z)] = R.with_props(lower, half="upper")

    def bed(self, x, y, z, color, facing) -> None:
        """Bed with its FOOT at (x, y, z) and HEAD at (x, y, z) + facing (AbstractBedBlock.setPlacedBy).
        ``color``: "red" | ... | "straw" | bed id."""
        bid = bed_id(color)
        if facing not in _DIR_OFF:
            raise ValueError(f"bed facing must be north/south/east/west, got {facing!r}")
        x, y, z = _pos(x, y, z)
        dx, dz = _DIR_OFF[facing]
        self.blocks[(x, y, z)] = R.make_state(bid, facing=facing, part="foot")
        self.blocks[(x + dx, y, z + dz)] = R.make_state(bid, facing=facing, part="head")

    def tall(self, x, y, z, plant, upper_waterlogged=False, **props) -> None:
        """Two-block plant (lilac, rose_bush, peony, sunflower, tall_grass, large_fern, pitcher_plant,
        small_dripleaf, ...): lower half at y, upper at y + 1.  Any DoublePlantBlock is accepted.

        The upper half copies the lower's properties (small_dripleaf ``facing``) like ``setPlacedBy``, except
        ``waterlogged``: the game takes it from the water at each half's own position
        (``DoublePlantBlock.copyWaterloggedFrom``), so ``small_dripleaf`` with ``waterlogged=True`` gets a DRY upper
        half unless ``upper_waterlogged=True`` (fully submerged) -- a wet upper half would be a water source."""
        bid = R.info(plant).id
        if not R.is_a(bid, "DoublePlantBlock"):
            tall = sorted(i.split(":")[1] for i in R.all_blocks() if R.is_a(i, "DoublePlantBlock"))
            raise ValueError(f"{bid} is not a double-height plant; options: {', '.join(tall)}")
        x, y, z = _pos(x, y, z)
        lower = R.make_state(bid, props, half="lower")
        if R.is_a(bid, "PitcherCropBlock") and int(R.prop(lower, "age")) < 3:
            raise ValueError(f"{bid} below age 3 is a single block (PitcherCropBlock.isDouble): use "
                             f"b.set(x, y, z, 'pitcher_crop[age={R.prop(lower, 'age')}]')")
        upper = R.with_props(lower, half="upper")
        if R.prop(upper, "waterlogged") is not None:
            upper = R.with_props(upper, waterlogged=bool(upper_waterlogged))
        self.blocks[(x, y, z)] = lower
        self.blocks[(x, y + 1, z)] = upper

    def double_chest(self, x, y, z, facing, side, kind="chest", waterlogged=False) -> None:
        """Double chest: one half at (x, y, z), the other one block toward ``side`` (perpendicular to
        ``facing``); both fronts face ``facing``.  ``kind``: chest | trapped_chest | copper_chest | ...
        The types follow ChestBlock.getConnectedDirection (type=left has its partner at facing.getClockWise())."""
        if facing not in _DIR_OFF or side not in _DIR_OFF:
            raise ValueError(f"double_chest facing/side must be north/south/east/west, got {facing!r}/{side!r}"
                             + (" (aliases only work through a Frame)" if facing in FACING_ALIASES or side in FACING_ALIASES else ""))
        cw = {"north": "east", "east": "south", "south": "west", "west": "north"}
        if side not in (cw[facing], {v: k for k, v in cw.items()}[facing]):
            raise ValueError(f"double_chest side {side!r} must be perpendicular to facing {facing!r}")
        bid = R.info(kind).id
        if "type" not in R.info(bid).properties:
            raise ValueError(f"{bid} cannot form a double chest (no 'type' property)")
        t = "left" if side == cw[facing] else "right"
        x, y, z = _pos(x, y, z)
        dx, dz = _DIR_OFF[side]
        self.blocks[(x, y, z)] = R.make_state(bid, facing=facing, type=t, waterlogged=waterlogged)
        self.blocks[(x + dx, y, z + dz)] = R.make_state(bid, facing=facing, type="right" if t == "left" else "left",
                                                        waterlogged=waterlogged)

    # ------------------------------------------------------------------------------------- QA markers
    def room(self, name: str, x, y, z) -> None:
        """Mark a room: (x, y, z) = player FEET position inside it (that cell and the one above must be passable)."""
        if name in self.rooms:
            raise ValueError(f"room {name!r} already marked at {self.rooms[name]}")
        self.rooms[name] = _pos(x, y, z)

    def entrance(self, x, y, z) -> None:
        """Mark an entrance: player FEET position just outside the main door."""
        self.entrances.append(_pos(x, y, z))

    def note(self, text: str) -> None:
        self.notes.append(str(text))

    def tile_entity(self, x, y, z, nbt) -> None:
        """Optional block entity data (an nbtlib.Compound) stored in the schematic at (x, y, z)."""
        self.tile_entities[_pos(x, y, z)] = nbt

    # ---------------------------------------------------------------------------------------- export
    def structure(self, *, resolve_blocks: bool = True):
        """Resolved + normalized ``(blocks, size, meta, resolve_stats)`` without writing anything."""
        from .resolve import resolve
        if not self.blocks:
            raise BuildError(f"{self.slug}: build is empty")
        if resolve_blocks:
            blocks, rstats = resolve(self.blocks)
        else:
            blocks, rstats = dict(self.blocks), {"changes": {}, "errors": [], "warnings": [], "removed": [], "passes": 0}
        if not blocks:
            raise BuildError(f"{self.slug}: nothing left after resolve ({len(rstats['removed'])} block(s) removed)")
        xs, ys, zs = zip(*blocks)
        x0, y0, z0 = min(xs), min(ys), min(zs)
        size = (max(xs) - x0 + 1, max(ys) - y0 + 1, max(zs) - z0 + 1)

        def sh(p):
            return (p[0] - x0, p[1] - y0, p[2] - z0)

        # schematic index order (y, z, x): downstream output (palette order, previews) then does not depend on the
        # order the script set blocks in, and matches what read_litematic returns for the written file
        nb = {sh(p): blocks[p] for p in sorted(blocks, key=lambda p: (p[1], p[2], p[0]))}
        meta = {
            "slug": self.slug, "title": self.title, "ground": self.ground - y0,
            "rooms": {k: sh(v) for k, v in self.rooms.items()},
            "entrances": [sh(p) for p in self.entrances],
            "notes": "\n".join(self.notes), "author": self.author, "description": self.description,
            "origin_offset": (x0, y0, z0),
        }
        if self.allowed_blocks:
            meta["allowed_blocks"] = list(self.allowed_blocks)
        self._te_shifted = {}
        for p, v in sorted(self.tile_entities.items()):
            s = blocks.get(p)
            if s is None or not R.info(R.block_id(s)).block_entity:
                rstats["warnings"].append(f"tile entity at {p} dropped: {s or 'air'} has no block entity")
                continue
            self._te_shifted[sh(p)] = v
        return nb, size, meta, rstats

    def finish(self, views="all", qa=True, *, render=True, strict=True, out_dir=None, argv=None) -> dict:
        """Resolve -> normalize -> strict validation -> write .litematic (+ structure .nbt) -> read-back check
        -> materials -> QA (blockwright.qa, if present) -> render (blockwright.render, if present) + embedded thumbnail.

        CLI flags (read from sys.argv): ``--quick`` (fewer views), ``--no-render``, ``--no-qa``,
        ``--views=a,b`` (combines with ``--quick``), ``--lenient`` (validation problems become warnings).
        Returns a dict of paths and stats (``timings``: seconds per stage).  Raises BuildError on validation
        failure when strict."""
        from . import litematic, materials, structure_nbt, validate

        args = list(sys.argv[1:] if argv is None else argv)
        quick, extra_views = False, None
        it = iter(args)
        for a in it:
            if a == "--quick":
                quick = True
            elif a == "--no-render":
                render = False
            elif a == "--no-qa":
                qa = False
            elif a == "--lenient":
                strict = False
            elif a.startswith("--palette=") or a == "--palette":
                self.set_allowed_blocks(a.split("=", 1)[1] if "=" in a else next(it, None))
            elif a.startswith("--out=") or a == "--out":
                out_dir = a.split("=", 1)[1] if "=" in a else next(it, None)
            elif a.startswith("--views=") or a == "--views":
                spec = a.split("=", 1)[1] if "=" in a else next(it, "")
                extra_views = [v.strip() for v in spec.split(",") if v.strip()]
            elif a in ("-h", "--help"):
                print(_FINISH_HELP)
                raise SystemExit(0)
            elif a.startswith("-"):
                print(f"[blockwright] warning: unknown flag {a!r} ignored (known: --quick --no-render --no-qa --views=a,b "
                      "--lenient --palette=FILE --out=DIR)", file=sys.stderr)
        if extra_views is not None:     # like `python -m blockwright render`: --quick --views=eye -> quick set + eye
            views = (["quick"] if quick else []) + extra_views
        elif quick:
            views = "quick"
        out = Path(out_dir) if out_dir else default_out_dir()
        t0 = time.time()
        res = {"slug": self.slug, "warnings": []}
        timings = res["timings"] = {}
        lap = [time.time()]

        def tick(stage):
            now = time.time()
            timings[stage] = round(timings.get(stage, 0.0) + now - lap[0], 3)
            lap[0] = now

        blocks, size, meta, rstats = self.structure()
        res.update(size=size, blocks=len(blocks), resolve=rstats, ground=meta["ground"])
        tick("resolve")

        problems = list(rstats["errors"]) + validate.validate_structure(blocks, size, meta)
        if problems:
            msg = f"{self.slug}: {len(problems)} validation problem(s):\n  - " + "\n  - ".join(problems)
            if strict:
                raise BuildError(msg + "\n(run with --lenient to export anyway)")
            print("[blockwright] WARNING " + msg, file=sys.stderr)
            res["warnings"].extend(problems)
        tick("validate")

        lit_path = out / "schematics" / f"{self.slug}.litematic"
        nbt_path = out / "structures" / f"{self.slug}.nbt"
        lit_kw = dict(name=self.title, author=self.author, description=self.description, region_name=self.title,
                      ground=meta["ground"], tile_entities=self._te_shifted or None)
        time_ms = int(os.environ["CC_TIME_MS"]) if os.environ.get("CC_TIME_MS") else int(time.time() * 1000)
        lit = litematic.write_litematic(lit_path, blocks, size, time_ms=time_ms, **lit_kw)
        structure_nbt.write_structure(nbt_path, blocks, size, self._te_shifted or None)
        (out / "schematics").mkdir(parents=True, exist_ok=True)
        meta_path = out / "schematics" / f"{self.slug}.meta.json"
        meta_path.write_text(json.dumps({**meta, "size": size}, indent=2, default=list), encoding="utf-8")
        res.update(litematic=str(lit_path), structure=str(nbt_path), meta=str(meta_path), palette_size=lit["palette_size"])
        tick("write")

        report = validate.validate_file(lit_path, expected=(blocks, size))
        if report["errors"]:
            raise BuildError(f"{self.slug}: read-back of {lit_path} failed:\n  - " + "\n  - ".join(report["errors"]))
        sb, ssize, _dv = structure_nbt.read_structure(nbt_path)
        if sb != blocks or tuple(ssize) != tuple(size):
            raise BuildError(f"{self.slug}: structure .nbt read-back mismatch")
        tick("readback")

        mats = materials.material_list(blocks)
        mat_md = out / "materials" / f"{self.slug}.md"
        materials.write_materials(mats, mat_md, out / "materials" / f"{self.slug}.json", title=self.title)
        res.update(materials=str(mat_md), material_kinds=len(mats["items"]), material_total=mats["total_items"])
        tick("materials")

        qa_headline = "skipped"
        if qa:
            qa_headline = self._run_qa(blocks, size, meta, out, res)
        res["qa_headline"] = qa_headline
        tick("qa")

        render_msg = "skipped"
        if render:
            render_msg = self._run_render(blocks, size, meta, out, views, res, lit_path, lit_kw, time_ms, tick)
        res["render"] = render_msg
        res["seconds"] = round(time.time() - t0, 2)
        self._print_summary(res, rstats, mats)
        return res

    # ------------------------------------------------------------------------------------- pipeline parts
    def _run_qa(self, blocks, size, meta, out, res) -> str:
        try:
            from . import qa as qa_mod  # noqa: F401  (built by another agent; optional)
        except ImportError as e:
            res["warnings"].append(f"blockwright.qa not available ({e}); QA skipped")
            return "blockwright.qa not available"
        try:
            report = qa_mod.run_qa(blocks, size, meta)
            md, js = out / "reports" / f"{self.slug}_qa.md", out / "reports" / f"{self.slug}_qa.json"
            md.parent.mkdir(parents=True, exist_ok=True)
            qa_mod.write_report(report, md, js)
            res["qa_report"] = str(md)
            res["qa"] = report
            if isinstance(report, dict):
                for k in ("headline", "summary", "verdict", "score"):
                    if k in report:
                        v = report[k]
                        if isinstance(v, dict) and "passed" in v:
                            counts = ", ".join(f"{v[c]} {c}" for c in ("errors", "warnings", "infos") if c in v)
                            return ("PASS" if v["passed"] else "FAIL") + (f" ({counts})" if counts else "")
                        return str(v)
            return "done"
        except Exception as e:  # QA is optional and developed in parallel -- never block the export
            res["warnings"].append(f"blockwright.qa failed: {type(e).__name__}: {e}")
            traceback.print_exc()
            return f"QA failed ({type(e).__name__}: {e})"

    def _run_render(self, blocks, size, meta, out, views, res, lit_path, lit_kw, time_ms, tick=None) -> str:
        from . import litematic, validate
        try:
            from . import render as render_mod  # noqa: F401
            render_views = render_mod.render_views
        except (ImportError, AttributeError) as e:
            res["warnings"].append(f"blockwright.render not available ({e}); previews skipped")
            return "blockwright.render not available"
        pdir = out / "previews" / self.slug
        try:
            pdir.mkdir(parents=True, exist_ok=True)
            vlist = [views] if isinstance(views, (str, dict)) else list(views)
            if any(v in ("all", "quick") for v in vlist if isinstance(v, str)):
                # a full/quick set replaces the folder: stale views of an older version would mix old and new
                # pictures (an explicit --views=a,b re-render keeps the other files)
                for old in pdir.glob(f"{self.slug}_*.png"):
                    old.unlink()
            # square iso view for Litematica's 120x120 PreviewImageData (rendered in the same worker pool, kept
            # off the contact sheet); a centre crop of the 4:3 iso_se view would cut off the build's sides
            vlist.append(dict(getattr(render_mod, "VIEW_PRESETS", {}).get("iso_se", {"type": "ortho", "azimuth": 45,
                                                                                    "elevation": 32.0}),
                              name="thumb", width=THUMB_RENDER_PX, height=THUMB_RENDER_PX, sheet=False))
            paths = [str(p) for p in (render_views(blocks, size, pdir, meta=meta, views=vlist) or [])]
            res["previews"] = [p for p in paths if not Path(p).stem.endswith("_thumb")]
            res["contact_sheet"] = next((p for p in paths if Path(p).stem.endswith("_sheet")), None)
        except Exception as e:
            res["warnings"].append(f"blockwright.render failed: {type(e).__name__}: {e}")
            traceback.print_exc()
            return f"render failed ({type(e).__name__}: {e})"
        finally:
            if tick:
                tick("render")
        thumb = _pick_thumbnail(paths)
        if thumb:
            try:
                argb = litematic.preview_from_image(thumb)
                litematic.write_litematic(lit_path, blocks, size, preview_argb=argb, time_ms=time_ms, **lit_kw)
                rep = validate.validate_file(lit_path, expected=(blocks, size))
                if rep["errors"]:
                    raise BuildError("; ".join(rep["errors"]))
                res["thumbnail"] = thumb
            except Exception as e:
                res["warnings"].append(f"thumbnail embedding failed: {type(e).__name__}: {e}")
            if tick:
                tick("thumbnail")
        n = len(res["previews"])
        return f"{n} view(s)" + (" + contact sheet" if res.get("contact_sheet") else "") + f" -> {pdir}"

    def _print_summary(self, res, rstats, mats):
        sx, sy, sz = res["size"]
        ch = ", ".join(f"{k} {v}" for k, v in sorted(rstats["changes"].items())) or "no changes"
        lines = [
            f"[blockwright] {self.slug} \"{self.title}\": size {sx}x{sy}x{sz} (x*y*z), {res['blocks']} blocks, "
            f"palette {res['palette_size']}, ground y={res['ground']}",
            f"     resolve ({rstats['passes']} pass): {ch}; {len(rstats['errors'])} errors, {len(rstats['warnings'])} warnings",
            f"     litematic: {res['litematic']}",
            f"     structure: {res['structure']}",
            f"     materials: {res['materials']} ({mats['total_items']} items, {len(mats['items'])} kinds"
            + (f", {len(mats['warnings'])} warnings" if mats["warnings"] else "") + ")",
            f"     QA: {res['qa_headline']}" + (f" -> {res['qa_report']}" if res.get("qa_report") else ""),
            f"     render: {res['render']}" + (" (thumbnail embedded)" if res.get("thumbnail") else ""),
        ]
        for w in rstats["warnings"][:5]:
            lines.append(f"     ! {w}")
        for w in res["warnings"][:5]:
            lines.append(f"     ! {w}")
        tm = res.get("timings") or {}
        lines.append(f"     done in {res['seconds']}s" + (" (" + ", ".join(f"{k} {v:.1f}s" for k, v in tm.items()) + ")"
                                                         if tm else ""))
        print("\n".join(lines))


THUMB_RENDER_PX = 360   # rendered square (x2 supersampled), downsampled to Litematica's 120x120 preview

_FINISH_HELP = """usage: python builds/<slug>.py [--quick] [--views=a,b] [--no-render] [--no-qa] [--lenient]
                                [--palette=FILE] [--out=DIR]
  --quick        3 views (iso_se, iso_nw, cut_1) + contact sheet instead of all (~12)
  --views=a,b    only these views (iso_se iso_sw iso_ne iso_nw elev_s elev_e elev_n elev_w top cut_N eye);
                 with --quick: the quick set plus these
  --no-render    no previews (and no thumbnail in the .litematic)
  --no-qa        skip blockwright.qa
  --lenient      export despite validation problems (they become warnings)
  --palette=FILE allowed-blocks file: QA reports every item outside it as an error
  --out=DIR      output root (default: <workspace>/out, the folder next to builds/)
outputs: out/schematics/<slug>.litematic (+.meta.json), out/structures/<slug>.nbt, out/materials/<slug>.md|json,
         out/reports/<slug>_qa.md|json, out/previews/<slug>/<slug>_<view>.png + <slug>_sheet.png"""


def _pick_thumbnail(paths):
    if not paths:
        return None
    pngs = [p for p in paths if str(p).lower().endswith(".png")]
    for key in ("_thumb", "hero", "iso_se", "iso", "front"):
        for p in pngs:
            if key in Path(p).name.lower() and "sheet" not in Path(p).name.lower():
                return p
    singles = [p for p in pngs if "sheet" not in Path(p).name.lower()]
    return singles[0] if singles else (pngs[0] if pngs else None)


# ===================================================================================================== Frame
class Frame:
    """Oriented local coordinates on a Build.

    Author in the CANONICAL orientation "facade faces south": u = +x (east; the right hand of a viewer
    standing outside looking at the facade), v = up, w = +z (outward, toward that viewer).  The frame maps
    them onto its real ``facing`` (south | west | north | east) around ``origin`` (world position of local
    (0, 0, 0)), rotating positions AND block states (facing/axis/rotation/sides/...).

    Inside a frame every direction is canonical: "north" == "in", "south" == "out", "west" == "left",
    "east" == "right"; the aliases ``facing=out|in|left|right`` are accepted in states and helper arguments.
    """

    def __init__(self, build: Build, origin, facing: str):
        if facing not in _FRAME_TURNS:
            raise ValueError(f"frame facing must be south/west/north/east, got {facing!r}")
        self.build = build
        self.origin = _pos(*origin)
        self.facing = facing
        self.turns = _FRAME_TURNS[facing]

    def set_allowed_blocks(self, palette) -> None:
        """Restrict the build to the items a player owns (see blockwright.palette).  ``palette``: path to a palette
        file, a list of entries, or None to lift the constraint.  QA reports every item outside it as an error."""
        from .palette import load_palette, parse_palette
        if palette is None:
            self.allowed_blocks = None
        elif isinstance(palette, (str, Path)) and Path(palette).is_file():
            self.allowed_blocks = load_palette(palette)
        elif isinstance(palette, str):
            self.allowed_blocks = parse_palette(palette.replace(",", "\n"))
        else:
            self.allowed_blocks = parse_palette("\n".join(palette))

    def __repr__(self):
        return f"Frame(origin={self.origin}, facing={self.facing!r})"

    def at(self, u, v, w):
        """World (x, y, z) of local (u, v, w)."""
        dx, dz = rotate_pos(_i(u), _i(w), self.turns)
        ox, oy, oz = self.origin
        return (ox + dx, oy + _i(v), oz + dz)

    def to_local(self, x, y, z):
        """Local (u, v, w) of a world position."""
        ox, oy, oz = self.origin
        du, dw = rotate_pos(_i(x) - ox, _i(z) - oz, -self.turns)
        return (du, _i(y) - oy, dw)

    def state(self, state: str) -> str:
        """World state for a state authored in canonical frame orientation (aliases allowed)."""
        if not isinstance(state, str):
            return _canon(state)  # raises a helpful TypeError
        return rotate_state(R.parse_state(resolve_alias(state)), self.turns)

    def dir(self, d: str) -> str:
        """World direction of a canonical/alias direction ("out" -> the facade's facing)."""
        from .rotate import rot_dir
        return rot_dir(FACING_ALIASES.get(d, d), self.turns)

    def local_state(self, world_state: str) -> str:
        return rotate_state(world_state, -self.turns % 4)

    def set(self, u, v, w, state) -> None:
        self.build.set(*self.at(u, v, w), self.state(state))

    def get(self, u, v, w, default=AIR) -> str:
        """State at local (u, v, w), expressed in the canonical frame orientation."""
        s = self.build.get(*self.at(u, v, w), default=None)
        return default if s is None else self.local_state(s)

    def remove(self, u, v, w) -> None:
        self.build.remove(*self.at(u, v, w))

    def __getitem__(self, pos):
        return self.get(*pos)

    def __setitem__(self, pos, state):
        self.set(*pos, state)

    def _where(self, where):
        if where is None or isinstance(where, str):
            return where
        return lambda x, y, z, cur: where(*self.to_local(x, y, z), self.local_state(cur) if cur != AIR else AIR)

    def _st(self, state):
        if callable(state):
            return lambda x, y, z: self.state(state(*self.to_local(x, y, z)))
        return self.state(state)

    def fill(self, u1, v1, w1, u2, v2, w2, state, where=None) -> int:
        """Fill a local box.  ``where``/``state`` callables receive LOCAL (u, v, w) and local-orientation states."""
        st, wh = self._st(state), self._where(where)
        n = 0
        for v in _rng(v1, v2):
            for w in _rng(w1, w2):
                for u in _rng(u1, u2):
                    x, y, z = self.at(u, v, w)
                    s = st(x, y, z) if callable(st) else st
                    n += self.build._put(x, y, z, _canon(s) if callable(st) else s, wh)
        return n

    def walls(self, u1, v1, w1, u2, v2, w2, state, where=None) -> int:
        st, wh = self._st(state), self._where(where)
        ua, ub = sorted((_i(u1), _i(u2)))
        wa, wb = sorted((_i(w1), _i(w2)))
        n = 0
        for v in _rng(v1, v2):
            for w in range(wa, wb + 1):
                for u in range(ua, ub + 1):
                    if u in (ua, ub) or w in (wa, wb):
                        x, y, z = self.at(u, v, w)
                        s = st(x, y, z) if callable(st) else st
                        n += self.build._put(x, y, z, s, wh)
        return n

    def line(self, p1, p2, state, where=None) -> int:
        st, wh = self._st(state), self._where(where)
        n = 0
        for u, v, w in _bresenham3(_pos(*p1), _pos(*p2)):
            x, y, z = self.at(u, v, w)
            s = st(x, y, z) if callable(st) else st
            n += self.build._put(x, y, z, s, wh)
        return n

    def door(self, u, v, w, wood, facing="in", hinge="left", open=False, powered=False) -> None:
        """Door with its lower half at local (u, v, w); ``facing`` canonical/alias ("in" = placed from outside)."""
        self.build.door(*self.at(u, v, w), wood, self.dir(facing), hinge=hinge, open=open, powered=powered)

    def bed(self, u, v, w, color, facing) -> None:
        """Bed: FOOT at local (u, v, w), head one block toward ``facing`` (canonical/alias)."""
        self.build.bed(*self.at(u, v, w), color, self.dir(facing))

    def tall(self, u, v, w, plant, **props) -> None:
        if "facing" in props:
            props["facing"] = self.dir(props["facing"])
        self.build.tall(*self.at(u, v, w), plant, **props)

    def double_chest(self, u, v, w, facing, side, kind="chest", waterlogged=False) -> None:
        """Double chest at local (u, v, w) + one block toward ``side``; ``facing``/``side`` canonical or alias."""
        self.build.double_chest(*self.at(u, v, w), self.dir(facing), self.dir(side), kind=kind, waterlogged=waterlogged)

    def paste(self, other: Build, at, rot: int = 0, mirror=None, where=None, markers: bool = False) -> int:
        """Paste a prefab authored in canonical orientation with its (0,0,0) at local ``at``; ``rot`` and
        ``mirror`` ("x": u -> -u, "z": w -> -w) are applied in local space before the frame's rotation."""
        return self.build.paste(other, self.at(*at), rot=(_i(rot, "rot") + self.turns) % 4, mirror=mirror,
                                where=self._where(where), markers=markers)

    def room(self, name, u, v, w) -> None:
        self.build.room(name, *self.at(u, v, w))

    def entrance(self, u, v, w) -> None:
        self.build.entrance(*self.at(u, v, w))

    def frame(self, at, facing="south") -> "Frame":
        """Nested frame at local ``at`` whose canonical facing ``facing`` is relative to this frame."""
        return Frame(self.build, self.at(*at), self.dir(facing))
