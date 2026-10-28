"""Geometry for blocks drawn by special / block-entity renderers in 26.3.

In 26.3 beds, signs and hanging signs are ordinary block models.  The blocks registered in
``BuiltInBlockModels`` (chests, bell body, banners, shulker boxes, skulls, decorated pot,
enchanting-table book, copper golem statue, conduit, end portal/gateway) plus the lectern book are
rebuilt here from the real entity-model cuboid definitions (ChestModel, BellModel, ShulkerModel,
BannerModel/BannerFlagModel, SkullModel, DecoratedPotRenderer, BookModel, CopperGolemModel) and the
real entity textures, with the renderers' model transforms.  Animated parts are frozen in a rest
pose.  Things that are not reproduced: sign text, banner patterns, items on campfires/shelves,
mob-specific head shapes (dragon/piglin use simplified boxes).
"""
from __future__ import annotations

import math

import numpy as np

from .models import LAYER_CUTOUT, LAYER_SOLID, SPRITES, Quads, quad_face_dir

DYE_COLORS = {
    "white": 0xF9FFFE, "orange": 0xF9801D, "magenta": 0xC74EBD, "light_blue": 0x3AB3DA,
    "yellow": 0xFED83D, "lime": 0x80C71F, "pink": 0xF38BAA, "gray": 0x474F52,
    "light_gray": 0x9D9D97, "cyan": 0x169C9C, "purple": 0x8932B8, "blue": 0x3C44AA,
    "brown": 0x835432, "green": 0x5E7C16, "red": 0xB02E26, "black": 0x1D1D21,
}
Y_ROT = {"south": 0, "west": 90, "north": 180, "east": 270}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east", "up": "down", "down": "up"}
STEP = {"north": (0, 0, -1), "south": (0, 0, 1), "west": (-1, 0, 0), "east": (1, 0, 0), "up": (0, 1, 0),
        "down": (0, -1, 0)}
CLOCKWISE = {"north": "east", "east": "south", "south": "west", "west": "north"}


def rgb_of(c: int) -> tuple[float, float, float]:
    return ((c >> 16) & 255) / 255.0, ((c >> 8) & 255) / 255.0, (c & 255) / 255.0


# ----------------------------------------------------------------------------------------------
# 4x4 matrix helpers (JOML conventions, right-handed, radians)


def T(x, y, z):
    m = np.eye(4)
    m[:3, 3] = (x, y, z)
    return m


def S(x, y=None, z=None):
    y = x if y is None else y
    z = x if z is None else z
    return np.diag([x, y, z, 1.0])


def RX(a):
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4)
    m[1, 1], m[1, 2], m[2, 1], m[2, 2] = c, -s, s, c
    return m


def RY(a):
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4)
    m[0, 0], m[0, 2], m[2, 0], m[2, 2] = c, s, -s, c
    return m


def RZ(a):
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4)
    m[0, 0], m[0, 1], m[1, 0], m[1, 1] = c, -s, s, c
    return m


def deg(a):
    return math.radians(a)


# ----------------------------------------------------------------------------------------------
# entity cuboids (ModelPart.Cube / Polygon port)


class Cube:
    def __init__(self, u, v, x, y, z, w, h, d, grow=0.0, faces=None, mirror=False):
        self.u, self.v = u, v
        self.box = (x, y, z, w, h, d)
        self.grow = grow
        self.faces = faces          # None = all, else set of names
        self.mirror = mirror

    def polygons(self, tw, th):
        x, y, z, w, h, d = self.box
        g = self.grow
        x0, y0, z0 = x - g, y - g, z - g
        x1, y1, z1 = x + w + g, y + h + g, z + d + g
        if self.mirror:
            x0, x1 = x1, x0
        t0, t1, t2, t3 = (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)
        l0, l1, l2, l3 = (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)
        u, v = self.u, self.v
        u0, u1, u2 = u, u + d, u + d + w
        u22, u3, u4 = u + d + w + w, u + d + w + d, u + d + w + d + w
        v0, v1, v2 = v, v + d, v + d + h
        spec = [
            ("down", (l1, l0, t0, t1), (u1, v0, u2, v1)),
            ("up", (t2, t3, l3, l2), (u2, v1, u22, v0)),
            ("west", (t0, l0, l3, t3), (u0, v1, u1, v2)),
            ("north", (t1, t0, t3, t2), (u1, v1, u2, v2)),
            ("east", (l1, t1, t2, l2), (u2, v1, u3, v2)),
            ("south", (l0, l1, l2, l3), (u3, v1, u4, v2)),
        ]
        out = []
        for name, verts, (pu0, pv0, pu1, pv1) in spec:
            if self.faces is not None and name not in self.faces:
                continue
            uvs = [(pu1 / tw, pv0 / th), (pu0 / tw, pv0 / th), (pu0 / tw, pv1 / th), (pu1 / tw, pv1 / th)]
            verts = list(verts)
            if self.mirror:
                verts.reverse()
                uvs.reverse()
            out.append((np.array(verts, float), uvs))
        return out


class Part:
    def __init__(self, cubes=(), offset=(0, 0, 0), rot=(0, 0, 0), children=()):
        self.cubes = list(cubes)
        self.offset = offset
        self.rot = rot
        self.children = list(children)


def emit(parts, root: np.ndarray, sprite: str, tw: int, th: int, rows: list, rgb=(1, 1, 1),
         layer=LAYER_CUTOUT):
    sid = SPRITES.id(sprite)

    def visit(part, m):
        m = m @ T(part.offset[0] / 16, part.offset[1] / 16, part.offset[2] / 16)
        if any(part.rot):
            m = m @ RZ(part.rot[2]) @ RY(part.rot[1]) @ RX(part.rot[0])
        for cube in part.cubes:
            for verts, uvs in cube.polygons(tw, th):
                p = np.c_[verts / 16.0, np.ones(4)] @ m.T
                p = p[:, :3]
                n = np.cross(p[1] - p[0], p[2] - p[0])
                if np.linalg.norm(n) < 1e-9:
                    continue
                f = quad_face_dir(p)
                rows.append((p, uvs, sid, -1, -1, f, f, layer, 0, rgb))
        for ch in part.children:
            visit(ch, m)

    for p in parts:
        visit(p, root)


# ----------------------------------------------------------------------------------------------
# individual special blocks


def _chest(rows, block, props):
    facing = props.get("facing", "north")
    ctype = props.get("type", "single")
    base = {"minecraft:chest": "normal", "minecraft:trapped_chest": "trapped", "minecraft:ender_chest": "ender"}.get(block)
    if base is None:  # copper chests
        n = block.split(":")[1].replace("waxed_", "")
        base = {"copper_chest": "copper", "exposed_copper_chest": "copper_exposed",
                "weathered_copper_chest": "copper_weathered", "oxidized_copper_chest": "copper_oxidized"}.get(n, "normal")
    if ctype == "single" or block == "minecraft:ender_chest":
        tex = f"entity/chest/{base}"
        parts = [Part([Cube(0, 19, 1, 0, 1, 14, 10, 14)]),
                 Part([Cube(0, 0, 1, 0, 0, 14, 5, 14)], (0, 9, 1)),
                 Part([Cube(0, 0, 7, -2, 14, 2, 4, 1)], (0, 9, 1))]
    elif ctype == "right":
        tex = f"entity/chest/{base}_right"
        vis = {"down", "up", "north", "south", "west"}
        parts = [Part([Cube(0, 19, 1, 0, 1, 15, 10, 14, faces=vis)]),
                 Part([Cube(0, 0, 1, 0, 0, 15, 5, 14, faces=vis)], (0, 9, 1)),
                 Part([Cube(0, 0, 15, -2, 14, 1, 4, 1, faces=vis)], (0, 9, 1))]
    else:
        tex = f"entity/chest/{base}_left"
        vis = {"down", "up", "north", "south", "east"}
        parts = [Part([Cube(0, 19, 0, 0, 1, 15, 10, 14, faces=vis)]),
                 Part([Cube(0, 0, 0, 0, 0, 15, 5, 14, faces=vis)], (0, 9, 1)),
                 Part([Cube(0, 0, 0, -2, 14, 1, 4, 1, faces=vis)], (0, 9, 1))]
    root = T(0.5, 0, 0.5) @ RY(deg(-Y_ROT.get(facing, 0))) @ T(-0.5, 0, -0.5)
    emit(parts, root, tex, 64, 64, rows)


def _bell(rows, block, props):
    body = Part([Cube(0, 0, -3, -6, -3, 6, 7, 6)], (8, 12, 8),
                children=[Part([Cube(0, 13, 4, 4, 4, 8, 2, 8)], (-8, -12, -8))])
    facing = props.get("facing", "north")
    root = T(0.5, 0, 0.5) @ RY(deg(-Y_ROT.get(facing, 0))) @ T(-0.5, 0, -0.5)
    emit([body], root, "entity/bell/bell_body", 32, 32, rows)


_SHULKER_ROT = {
    "down": RX(math.pi), "up": np.eye(4), "north": RX(math.pi / 2) @ RZ(math.pi),
    "south": RX(math.pi / 2), "west": RX(math.pi / 2) @ RZ(math.pi / 2), "east": RX(math.pi / 2) @ RZ(-math.pi / 2),
}


def _shulker(rows, block, props):
    name = block.split(":")[1]
    color = name[:-len("_shulker_box")] if name != "shulker_box" else None
    tex = f"entity/shulker/shulker_{color}" if color else "entity/shulker/shulker"
    parts = [Part([Cube(0, 0, -8, -16, -8, 16, 12, 16)], (0, 24, 0)),
             Part([Cube(0, 28, -8, -8, -8, 16, 8, 16)], (0, 24, 0))]
    d = props.get("facing", "up")
    root = T(0.5, 0.5, 0.5) @ S(0.9995) @ _SHULKER_ROT[d] @ S(1, -1, -1) @ T(0, -1, 0)
    emit(parts, root, tex, 64, 64, rows)


def _banner(rows, block, props):
    name = block.split(":")[1]
    wall = name.endswith("_wall_banner")
    color = name[:-len("_wall_banner")] if wall else name[:-len("_banner")]
    rgb = rgb_of(DYE_COLORS.get(color, 0xFFFFFF))
    if wall:
        angle = Y_ROT.get(props.get("facing", "north"), 0)
        wood = [Part([Cube(0, 42, -10, -20.5, 9.5, 20, 2, 2)])]
        flag = [Part([Cube(0, 0, -10, 0, -2, 20, 40, 1)], (0, -20.5, 10.5))]
    else:
        angle = int(props.get("rotation", "0")) * 22.5
        wood = [Part([Cube(44, 0, -1, -42, -1, 2, 42, 2)]), Part([Cube(0, 42, -10, -44, -1, 20, 2, 2)])]
        flag = [Part([Cube(0, 0, -10, 0, -2, 20, 40, 1)], (0, -44, 0))]
    root = T(0.5, 0, 0.5) @ RY(deg(-angle)) @ S(2 / 3, -2 / 3, -2 / 3)
    emit(wood, root, "entity/banner/banner_base", 64, 64, rows)
    emit(flag, root, "entity/banner/base", 64, 64, rows, rgb=rgb)


_SKULL_TEX = {
    "skeleton": ("entity/skeleton/skeleton", 64, 32), "wither_skeleton": ("entity/skeleton/wither_skeleton", 64, 32),
    "zombie": ("entity/zombie/zombie", 64, 64), "creeper": ("entity/creeper/creeper", 64, 32),
    "player": ("entity/player/wide/steve", 64, 64), "piglin": ("entity/piglin/piglin", 64, 64),
    "dragon": ("entity/enderdragon/dragon", 256, 256),
}


def _skull(rows, block, props):
    name = block.split(":")[1]
    wall = "_wall_" in name
    kind = name.replace("_wall_skull", "").replace("_wall_head", "").replace("_skull", "").replace("_head", "")
    tex, tw, th = _SKULL_TEX.get(kind, _SKULL_TEX["skeleton"])
    if kind == "piglin":
        cubes = [Cube(0, 0, -5, -8, -4, 10, 8, 8)]
    elif kind == "dragon":
        cubes = [Cube(112, 30, -8, -16, -8, 16, 16, 16)]
    else:
        cubes = [Cube(0, 0, -4, -8, -4, 8, 8, 8)]
        if th == 64 and kind in ("player", "zombie"):
            cubes.append(Cube(32, 0, -4, -8, -4, 8, 8, 8, grow=0.25))
    part = Part(cubes)
    if wall:
        f = props.get("facing", "north")
        sx, _, sz = STEP[f]
        root = T(0.5 - sx * 0.25, 0.25, 0.5 - sz * 0.25) @ RY(deg(-Y_ROT[OPP[f]])) @ S(-1, -1, 1)
    else:
        rot = int(props.get("rotation", "0")) * 22.5
        root = T(0.5, 0, 0.5) @ RY(deg(-rot)) @ S(-1, -1, 1)
    if kind == "dragon":
        root = root @ S(0.75)
    emit([part], root, tex, tw, th, rows)


def _decorated_pot(rows, block, props):
    f = props.get("facing", "north")
    root = T(0.5, 0.5, 0.5) @ RY(deg(180 - Y_ROT.get(f, 0))) @ T(-0.5, -0.5, -0.5)
    neck = Part([Cube(0, 0, 4, 17, 4, 8, 3, 8, grow=-0.1), Cube(0, 5, 5, 20, 5, 6, 1, 6, grow=0.2)],
                (0, 37, 16), (math.pi, 0, 0))
    plane = [Cube(-14, 13, 0, 0, 0, 14, 0, 14)]
    top = Part(plane, (1, 16, 1))
    bottom = Part(plane, (1, 0, 1))
    emit([neck, top, bottom], root, "entity/decorated_pot/decorated_pot_base", 32, 32, rows)
    side = [Cube(1, 0, 0, 0, 0, 14, 16, 0, faces={"north"})]
    sides = [Part(side, (15, 16, 1), (0, 0, math.pi)),
             Part(side, (1, 16, 1), (0, -math.pi / 2, math.pi)),
             Part(side, (15, 16, 15), (0, math.pi / 2, math.pi)),
             Part(side, (1, 16, 15), (math.pi, 0, 0))]
    emit(sides, root, "entity/decorated_pot/decorated_pot_side", 16, 16, rows)


def _book_parts(openness=1.5, pf1=0.1, pf2=0.9):
    o = openness
    so = math.sin(o)
    return [
        Part([Cube(0, 0, -6, -5, -0.005, 6, 10, 0.005)], (0, 0, -1), (0, math.pi + o, 0)),
        Part([Cube(16, 0, 0, -5, -0.005, 6, 10, 0.005)], (0, 0, 1), (0, -o, 0)),
        Part([Cube(12, 0, -1, -5, 0, 2, 10, 0.005)], (0, 0, 0), (0, math.pi / 2, 0)),
        Part([Cube(0, 10, 0, -4, -0.99, 5, 8, 1)], (so, 0, 0), (0, o, 0)),
        Part([Cube(12, 10, 0, -4, -0.01, 5, 8, 1)], (so, 0, 0), (0, -o, 0)),
        Part([Cube(24, 10, 0, -4, 0, 5, 8, 0.005)], (so, 0, 0), (0, o - 2 * o * pf1, 0)),
        Part([Cube(24, 10, 0, -4, 0, 5, 8, 0.005)], (so, 0, 0), (0, o - 2 * o * pf2, 0)),
    ]


def _lectern_book(rows, block, props):
    if props.get("has_book") != "true":
        return
    yrot = Y_ROT[CLOCKWISE.get(props.get("facing", "north"), "east")]
    root = T(0.5, 1.0625, 0.5) @ RY(deg(-yrot)) @ RZ(deg(67.5)) @ T(0, -0.125, 0)
    emit(_book_parts(1.5, 0.1, 0.9), root, "entity/enchantment/enchanting_table_book", 64, 32, rows)


def _enchanting_book(rows, block, props):
    root = T(0.5, 0.85, 0.5) @ RY(deg(-90)) @ RZ(deg(80))
    emit(_book_parts(1.1, 0.3, 0.7), root, "entity/enchantment/enchanting_table_book", 64, 32, rows)


def _copper_golem(rows, block, props):
    name = block.split(":")[1].replace("waxed_", "")
    stage = name.replace("copper_golem_statue", "").rstrip("_")
    tex = "entity/copper_golem/copper_golem" + (f"_{stage}" if stage else "")
    head = Part([Cube(0, 0, -4, -5, -5, 8, 5, 10, grow=0.015), Cube(56, 0, -1, -2, -6, 2, 3, 2),
                 Cube(37, 8, -1, -9, -1, 2, 4, 2, grow=-0.015), Cube(37, 0, -2, -13, -2, 4, 4, 4, grow=-0.015)],
                (0, -6, 0))
    body = Part([Cube(0, 15, -4, -6, -3, 8, 6, 6)], (0, -5, 0), children=[
        head,
        Part([Cube(36, 16, -3, -1, -2, 3, 10, 4)], (-4, -6, 0)),
        Part([Cube(50, 16, 0, -1, -2, 3, 10, 4)], (4, -6, 0)),
    ])
    legs = [Part([Cube(0, 27, -4, 0, -2, 4, 5, 4)], (0, -5, 0)), Part([Cube(16, 27, 0, 0, -2, 4, 5, 4)], (0, -5, 0))]
    f = props.get("facing", "north")
    root = T(0.5, 0, 0.5) @ RY(deg(-Y_ROT[OPP[f]])) @ S(-1, -1, 1)
    emit([body] + legs, root, tex, 64, 64, rows)


def _conduit(rows, block, props):
    emit([Part([Cube(0, 0, -3, -3, -3, 6, 6, 6)])], T(0.5, 0.5, 0.5), "entity/conduit/base", 32, 16, rows)


def _end_portal(rows, block, props):
    sid = SPRITES.id("block/black_concrete")
    y = 0.75 if block == "minecraft:end_portal" else 1.0
    p = np.array([[0, y, 0], [0, y, 1], [1, y, 1], [1, y, 0]], float)
    rows.append((p, [(0, 0), (0, 1), (1, 1), (1, 0)], sid, -1, 1, 1, 1, LAYER_SOLID, 15, (0.25, 0.3, 0.35)))


SPECIAL_BLOCK_CLASSES = {
    "ChestBlock": _chest, "TrappedChestBlock": _chest, "EnderChestBlock": _chest, "CopperChestBlock": _chest,
    "WeatheringCopperChestBlock": _chest, "BellBlock": _bell, "ShulkerBoxBlock": _shulker,
    "BannerBlock": _banner, "WallBannerBlock": _banner, "SkullBlock": _skull, "WallSkullBlock": _skull,
    "WitherSkullBlock": _skull, "WitherWallSkullBlock": _skull, "PlayerHeadBlock": _skull,
    "PlayerWallHeadBlock": _skull, "PiglinWallSkullBlock": _skull, "DecoratedPotBlock": _decorated_pot,
    "LecternBlock": _lectern_book, "EnchantingTableBlock": _enchanting_book,
    "CopperGolemStatueBlock": _copper_golem, "WeatheringCopperGolemStatueBlock": _copper_golem,
    "ConduitBlock": _conduit, "EndPortalBlock": _end_portal, "EndGatewayBlock": _end_portal,
}
SPECIAL_BLOCK_IDS = {
    "minecraft:bell": _bell, "minecraft:decorated_pot": _decorated_pot, "minecraft:lectern": _lectern_book,
    "minecraft:enchanting_table": _enchanting_book, "minecraft:conduit": _conduit,
    "minecraft:end_portal": _end_portal, "minecraft:end_gateway": _end_portal,
    "minecraft:piglin_head": _skull, "minecraft:dragon_head": _skull, "minecraft:dragon_wall_head": _skull,
}


def special_quads(block_id: str, cls: str, props: dict) -> Quads | None:
    """Extra (non-block-model) geometry for this state, block-local, or None."""
    fn = SPECIAL_BLOCK_IDS.get(block_id) or SPECIAL_BLOCK_CLASSES.get(cls)
    if fn is None:
        return None
    rows: list = []
    fn(rows, block_id, props)
    return Quads.from_lists(rows) if rows else None
