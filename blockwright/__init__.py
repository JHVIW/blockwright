"""blockwright -- code-first Minecraft building toolkit (Minecraft Java 26.3 + Litematica 0.29.1 tested).

Builder scripts start with::

    from blockwright import *

    b = Build("my_house", "My House", ground=2)
    ...
    b.finish()

See docs/API.md for the full reference and ``python -m blockwright --help`` for the CLI.
"""
__version__ = "0.1.0"

from . import blocks, noise, registry
from .blocks import (COLORS, StoneFamily, WoodFamily, barrel, bed_id, campfire, candle, carpet, chain, chest, door_id,
                     fence, gate, glass, lantern, leaves, log, pane, potted, shelf, slab, stairs, state, stone, torch,
                     trapdoor, vine, wall, wood, wool)
from .build import Build, BuildError, Frame
from .palette import load_palette, parse_palette
from .noise import chance, fbm2, fbm3, gradient, hash01, hash3, pick, value2, value3
from .registry import (AIR, block_class, block_id, has_tag, is_a, item, make_state, parse_state, phys, prop, props,
                       tag_members, with_block, with_props)
from .rotate import mirror_state, rotate_state

R = registry

__all__ = [
    "Build", "BuildError", "Frame", "AIR", "load_palette", "parse_palette", "R", "registry", "blocks", "noise",
    # registry
    "parse_state", "make_state", "props", "prop", "block_id", "with_props", "with_block", "has_tag", "tag_members", "is_a",
    "block_class", "item", "phys",
    # rotation
    "rotate_state", "mirror_state",
    # block helpers
    "state", "wood", "stone", "WoodFamily", "StoneFamily", "stairs", "slab", "wall", "log", "trapdoor", "fence", "gate",
    "door_id", "bed_id", "pane", "glass", "wool", "carpet", "lantern", "torch", "candle", "leaves", "vine", "potted",
    "campfire", "chain", "barrel", "chest", "shelf", "COLORS",
    # noise
    "hash3", "hash01", "chance", "pick", "value2", "value3", "fbm2", "fbm3", "gradient",
]
