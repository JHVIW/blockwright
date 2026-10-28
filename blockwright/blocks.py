"""Readable block-state helpers.  Every function returns a canonical state string validated against the
26.3 registry (``blockwright.registry``), so typos fail loudly at the line that made them.

Techniques only -- no whole-building generators.

Facing aliases: any ``facing`` argument may be ``"out" | "in" | "left" | "right"``.  Such a state keeps the
alias (e.g. ``"minecraft:oak_stairs[facing=out,...]"``) and is **only accepted by a Frame**
(``b.frame(...).set(...)``), which maps it to a real direction (canonically out=south, in=north,
left=west, right=east, then rotated to the frame's facing).  ``Build.set`` rejects aliased states.
"""
from __future__ import annotations

import re

from . import registry as R

FACING_ALIASES = {"out": "south", "in": "north", "left": "west", "right": "east"}
_ALIAS_RE = re.compile(r"facing=(out|in|left|right)\b")
COLORS = ("white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray", "light_gray", "cyan",
          "purple", "blue", "brown", "green", "red", "black")


def _mk(block_id: str, **props) -> str:
    """make_state that tolerates a facing alias (validated with its canonical stand-in, alias kept)."""
    f = props.get("facing")
    if isinstance(f, str) and f in FACING_ALIASES:
        props["facing"] = FACING_ALIASES[f]
        s = R.make_state(block_id, props)
        return s.replace(f"facing={FACING_ALIASES[f]}", f"facing={f}", 1)
    return R.make_state(block_id, props)


def has_alias(state: str) -> bool:
    return bool(_ALIAS_RE.search(state))


def resolve_alias(state: str) -> str:
    """Replace a facing alias by its canonical-frame direction (out=south, in=north, left=west, right=east)."""
    return _ALIAS_RE.sub(lambda m: "facing=" + FACING_ALIASES[m.group(1)], state)


def state(name: str, **props) -> str:
    """Generic: ``state("oak_stairs", facing="east", half="top")``; bool/int values allowed."""
    return _mk(name, **props)


def _id(name: str) -> str:
    return name if ":" in name else "minecraft:" + name


def _exists(name: str):
    return _id(name) if R.exists(name) else None


def _first(*cands):
    for c in cands:
        if c and R.exists(c):
            return _id(c)
    return None


def _need(bid, what):
    if bid is None:
        raise ValueError(f"No {what} block exists in Minecraft 26.3")
    return bid


# ------------------------------------------------------------------------------------------ wood family
class WoodFamily:
    """All blocks of one wood type, derived from the registry (handles bamboo, crimson/warped, poplar, ...).

    Attributes (canonical states, or ``None`` when the family has no such block):
        planks, fence, pressure_plate, leaves (persistent=true), mosaic (bamboo only)
    Ids (strings or None): door (use with ``Build.door``), ids (dict role -> id), leaves_variants (list)
    Methods (raise ValueError if the family lacks the block):
        log(axis="y"), wood(axis="y"), stripped_log(axis="y"), stripped_wood(axis="y"),
        stairs(facing, half="bottom"), slab(type="bottom"), gate(facing, open=False),
        trapdoor(facing, half="bottom", open=False), button(facing="north", face="wall"),
        sign(rotation=0), wall_sign(facing), hanging_sign(rotation=0, attached=False),
        wall_hanging_sign(facing), shelf(facing), mosaic_stairs(facing, half), mosaic_slab(type)
    """

    def __init__(self, name: str):
        n = name.split(":")[-1]
        for suf in ("_planks", "_log", "_stem", "_wood", "_hyphae"):
            if n.endswith(suf) and R.exists(n[: -len(suf)] + "_planks"):
                n = n[: -len(suf)]
        if not R.exists(n + "_planks"):
            woods = sorted(i.split(":")[1][: -len("_planks")] for i in R.all_blocks() if i.endswith("_planks"))
            raise ValueError(f"Unknown wood type {name!r}; 26.3 wood types: {', '.join(woods)}")
        self.name = n
        log = _first(f"{n}_log", f"{n}_stem", f"{n}_block")
        wood = _first(f"{n}_wood", f"{n}_hyphae")
        ids = {
            "planks": _id(f"{n}_planks"),
            "log": log,
            "wood": wood,
            "stripped_log": _first("stripped_" + log.split(":")[1]) if log else None,
            "stripped_wood": _first("stripped_" + wood.split(":")[1]) if wood else None,
            "stairs": _exists(f"{n}_stairs"), "slab": _exists(f"{n}_slab"),
            "fence": _exists(f"{n}_fence"), "gate": _exists(f"{n}_fence_gate"),
            "door": _exists(f"{n}_door"), "trapdoor": _exists(f"{n}_trapdoor"),
            "button": _exists(f"{n}_button"), "pressure_plate": _exists(f"{n}_pressure_plate"),
            "sign": _exists(f"{n}_sign"), "wall_sign": _exists(f"{n}_wall_sign"),
            "hanging_sign": _exists(f"{n}_hanging_sign"), "wall_hanging_sign": _exists(f"{n}_wall_hanging_sign"),
            "shelf": _exists(f"{n}_shelf"), "leaves": _exists(f"{n}_leaves"),
            "mosaic": _exists(f"{n}_mosaic"), "mosaic_stairs": _exists(f"{n}_mosaic_stairs"),
            "mosaic_slab": _exists(f"{n}_mosaic_slab"), "sapling": _exists(f"{n}_sapling"),
        }
        self.ids = ids
        variants = []
        for i in R.all_blocks():
            m = re.fullmatch(rf"minecraft:(?:(\w+)_)?{re.escape(n)}_leaves", i)
            # dark_oak_leaves is not an oak leaves variant: "dark_oak" is a wood type of its own
            if m and not (m.group(1) and R.exists(f"{m.group(1)}_{n}_planks")):
                variants.append(i)
        self.leaves_variants = sorted(variants)
        self.planks = R.make_state(ids["planks"])
        self.fence = R.make_state(ids["fence"]) if ids["fence"] else None
        self.pressure_plate = R.make_state(ids["pressure_plate"]) if ids["pressure_plate"] else None
        self.leaves = R.make_state(ids["leaves"], persistent=True) if ids["leaves"] else None
        self.mosaic = R.make_state(ids["mosaic"]) if ids["mosaic"] else None
        self.door = ids["door"]

    def __repr__(self):
        return f"WoodFamily({self.name!r})"

    def _get(self, role):
        bid = self.ids.get(role)
        if bid is None:
            raise ValueError(f"wood type {self.name!r} has no {role.replace('_', ' ')} block in 26.3")
        return bid

    def log(self, axis="y"):
        return _mk(self._get("log"), axis=axis)

    def wood(self, axis="y"):
        return _mk(self._get("wood"), axis=axis)

    def stripped_log(self, axis="y"):
        return _mk(self._get("stripped_log"), axis=axis)

    def stripped_wood(self, axis="y"):
        return _mk(self._get("stripped_wood"), axis=axis)

    def stairs(self, facing, half="bottom"):
        return _mk(self._get("stairs"), facing=facing, half=half)

    def slab(self, type="bottom"):
        return _mk(self._get("slab"), type=type)

    def gate(self, facing, open=False):
        return _mk(self._get("gate"), facing=facing, open=open)

    def trapdoor(self, facing, half="bottom", open=False):
        return _mk(self._get("trapdoor"), facing=facing, half=half, open=open)

    def button(self, facing="north", face="wall"):
        return _mk(self._get("button"), facing=facing, face=face)

    def sign(self, rotation=0):
        return _mk(self._get("sign"), rotation=rotation)

    def wall_sign(self, facing):
        return _mk(self._get("wall_sign"), facing=facing)

    def hanging_sign(self, rotation=0, attached=False):
        return _mk(self._get("hanging_sign"), rotation=rotation, attached=attached)

    def wall_hanging_sign(self, facing):
        return _mk(self._get("wall_hanging_sign"), facing=facing)

    def shelf(self, facing):
        return _mk(self._get("shelf"), facing=facing)

    def mosaic_stairs(self, facing, half="bottom"):
        return _mk(self._get("mosaic_stairs"), facing=facing, half=half)

    def mosaic_slab(self, type="bottom"):
        return _mk(self._get("mosaic_slab"), type=type)


def wood(name: str) -> WoodFamily:
    """``wood("spruce")`` -> WoodFamily (oak, spruce, birch, jungle, acacia, dark_oak, pale_oak, mangrove,
    cherry, poplar, bamboo, crimson, warped)."""
    return WoodFamily(name)


# ----------------------------------------------------------------------------------------- stone family
class StoneFamily:
    """A stone-like material and its shapes, derived generically from the registry.

    ``block`` (state or None), ``block_id``, ``stairs_id``/``slab_id``/``wall_id`` (id or None),
    ``wall`` (default state or None), ``stairs(facing, half="bottom")``, ``slab(type="bottom")``.
    """

    def __init__(self, name: str):
        n = name.split(":")[-1]
        base = _material_base(n, ("_stairs", "_slab", "_wall"))
        block = _first(n, base + "s", base, base + "_block") if base else _first(n)
        if base is None:
            base = n
        self.name = n
        self.base = base
        self.block_id = block
        self.stairs_id = _exists(f"{base}_stairs")
        self.slab_id = _exists(f"{base}_slab")
        self.wall_id = _exists(f"{base}_wall")
        if not (self.block_id or self.stairs_id or self.slab_id or self.wall_id):
            raise ValueError(f"Unknown stone material {name!r} (no block/stairs/slab/wall found in 26.3)")
        self.block = R.make_state(block) if block else None
        self.wall = R.make_state(self.wall_id) if self.wall_id else None

    def __repr__(self):
        return f"StoneFamily({self.name!r})"

    def stairs(self, facing, half="bottom"):
        return _mk(_need(self.stairs_id, f"{self.name} stairs"), facing=facing, half=half)

    def slab(self, type="bottom"):
        return _mk(_need(self.slab_id, f"{self.name} slab"), type=type)


def _material_base(n: str, suffixes) -> str | None:
    """Find the prefix X such that X_<suffix> exists (oak_planks->oak, stone_bricks->stone_brick, ...)."""
    cands = [n]
    for strip in ("_planks", "_block", "s"):
        if n.endswith(strip):
            cands.append(n[: -len(strip)])
    for c in cands:
        for suf in suffixes:
            if R.exists(c + suf):
                return c
    return None


def stone(name: str) -> StoneFamily:
    """``stone("cobblestone")``, ``stone("stone_brick")``/``stone("stone_bricks")``, ``stone("brick")``,
    ``stone("deepslate_tile")``, ``stone("mud_brick")``, ``stone("smooth_stone")`` ..."""
    return StoneFamily(name)


# ------------------------------------------------------------------------------------ generic helpers
def _shape_id(material: str, suffix: str, what: str) -> str:
    m = material.split(":")[-1]
    if m.endswith(suffix) and R.exists(m):
        return _id(m)
    if R.exists(m + suffix):
        return _id(m + suffix)
    base = _material_base(m, (suffix,))
    if base is None:
        sugg = sorted(i.split(":")[1] for i in R.all_blocks() if i.endswith(suffix) and m.split("_")[0] in i)[:8]
        raise ValueError(f"No {what} for material {material!r} in 26.3." + (f" Similar: {', '.join(sugg)}" if sugg else ""))
    return _id(base + suffix)


def stairs(material: str, facing, half="bottom") -> str:
    """``stairs("spruce", "north")``, ``stairs("cobblestone", "east", "top")``, ``stairs("stone_bricks", ...)``."""
    return _mk(_shape_id(material, "_stairs", "stairs"), facing=facing, half=half)


def slab(material: str, type="bottom") -> str:
    return _mk(_shape_id(material, "_slab", "slab"), type=type)


def wall(material: str) -> str:
    """Wall block (connections are computed by blockwright.resolve)."""
    return _mk(_shape_id(material, "_wall", "wall"))


def log(material: str, axis="y") -> str:
    m = material.split(":")[-1]
    if R.exists(m) and "axis" in R.info(m).properties:
        return _mk(m, axis=axis)
    return WoodFamily(m).log(axis)


def trapdoor(material: str, facing, half="bottom", open=False) -> str:
    return _mk(_shape_id(material, "_trapdoor", "trapdoor"), facing=facing, half=half, open=open)


def fence(material: str) -> str:
    """Fence (connections are computed by blockwright.resolve).  ``fence("oak")``, ``fence("nether_brick")``."""
    return _mk(_shape_id(material, "_fence", "fence"))


def gate(material: str, facing, open=False) -> str:
    return _mk(_shape_id(material, "_fence_gate", "fence gate"), facing=facing, open=open)


def door_id(wood_or_id) -> str:
    """Door block id from a wood name / material ("spruce", "iron", "copper", "waxed_copper") or id."""
    if isinstance(wood_or_id, WoodFamily):
        return _need(wood_or_id.door, f"{wood_or_id.name} door")
    m = str(wood_or_id).split(":")[-1]
    if m.endswith("_door") and R.exists(m):
        return _id(m)
    if R.exists(m + "_door"):
        return _id(m + "_door")
    doors = sorted(i.split(":")[1] for i in R.all_blocks() if i.endswith("_door"))
    raise ValueError(f"No door for {wood_or_id!r}; doors in 26.3: {', '.join(doors)}")


def pane(color=None) -> str:
    """Glass pane (``pane()`` clear, ``pane("light_blue")`` stained)."""
    return _mk("glass_pane" if color is None else f"{color}_stained_glass_pane")


def glass(color=None) -> str:
    """``glass()`` clear, ``glass("light_blue")`` stained, ``glass("tinted")`` tinted glass."""
    if color == "tinted":
        return _mk("tinted_glass")
    return _mk("glass" if color is None else f"{color}_stained_glass")


def wool(color) -> str:
    return _mk(f"{color}_wool")


def carpet(color) -> str:
    return _mk("moss_carpet" if color == "moss" else f"{color}_carpet")


def lantern(hanging=False, kind="lantern") -> str:
    """``lantern()``, ``lantern(True)`` (hanging), kind: "lantern" | "soul" | "copper" | "exposed_copper" |
    "weathered_copper" | "oxidized_copper" | "waxed_copper" | ..."""
    bid = "lantern" if kind in ("lantern", "normal", "iron", None) else (kind if kind.endswith("lantern") else f"{kind}_lantern")
    return _mk(bid, hanging=hanging)


def torch(facing=None, kind="torch") -> str:
    """Standing torch (``facing=None``) or wall torch facing away from its wall. kind: torch|soul|copper|redstone."""
    pre = "" if kind in ("torch", None) else f"{kind}_"
    if facing is None:
        return _mk(f"{pre}torch")
    return _mk(f"{pre}wall_torch", facing=facing)


def candle(color=None, count=1, lit=True) -> str:
    return _mk("candle" if color is None else f"{color}_candle", candles=count, lit=lit)


def leaves(kind: str) -> str:
    """Leaves, always ``persistent=true`` (never decay): ``leaves("oak")``, ``leaves("orange_poplar")``,
    ``leaves("flowering_azalea")``.  Distance is computed by blockwright.resolve."""
    k = kind.split(":")[-1]
    bid = k if k.endswith("_leaves") else f"{k}_leaves"
    return _mk(bid, persistent=True)


def vine(*faces) -> str:
    """Vine on the given faces ("north", "east", "south", "west", "up").  ``vine()`` (no faces) lets
    blockwright.resolve attach it to every supporting neighbour like the game's placement would."""
    bad = [f for f in faces if f not in ("north", "east", "south", "west", "up")]
    if bad:
        raise ValueError(f"vine faces must be north/east/south/west/up, got {bad}")
    return _mk("vine", **{f: True for f in faces})


def potted(plant: str) -> str:
    """Flower pot with a plant: ``potted("red_tulip")``, ``potted("fern")``, ``potted("azalea_bush")``."""
    p = plant.split(":")[-1]
    if p.startswith("potted_"):
        p = p[len("potted_"):]
    if not R.exists(f"potted_{p}"):
        opts = sorted(i.split(":")[1][len("potted_"):] for i in R.all_blocks() if i.startswith("minecraft:potted_"))
        raise ValueError(f"No potted variant for {plant!r}; pottable in 26.3: {', '.join(opts)}")
    return _mk(f"potted_{p}")


def campfire(facing="north", lit=True, kind="campfire") -> str:
    """Campfire (``kind="soul"`` for soul campfire); signal_fire is computed by blockwright.resolve (hay below)."""
    return _mk("soul_campfire" if kind == "soul" else "campfire", facing=facing, lit=lit)


def chain(axis="y", kind="iron") -> str:
    """Chain; 26.3 id is ``iron_chain``.  kind: iron | copper | exposed_copper | waxed_copper | ..."""
    return _mk(f"{kind}_chain", axis=axis)


def barrel(facing, open=False) -> str:
    return _mk("barrel", facing=facing, open=open)


def chest(facing, type="single", kind="chest") -> str:
    """Chest (front faces ``facing``). kind: chest | trapped_chest | copper_chest | ..."""
    return _mk(kind, facing=facing, type=type)


def shelf(material: str, facing) -> str:
    """Wooden shelf whose front faces ``facing``."""
    return _mk(_shape_id(material, "_shelf", "shelf"), facing=facing)


def bed_id(color) -> str:
    c = str(color).split(":")[-1]
    if c.endswith("_bed") and R.exists(c):
        return _id(c)
    if R.exists(f"{c}_bed"):
        return _id(f"{c}_bed")
    raise ValueError(f"No bed for {color!r}; colors: {', '.join(COLORS)} or 'straw'")
