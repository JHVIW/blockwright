"""Allowed-block palettes: "build this only from blocks I have".

A palette file is plain text, one entry per line::

    // my survival storage, 2026-10
    oak_planks            an item id (namespace optional)
    *_planks              a glob over item ids
    stripped_*_log
    #minecraft:logs       a block tag (every block in it, mapped to its item)
    tag:flowers           the same, alternative spelling
    # a comment (a hash followed by a space or nothing), // also starts a comment

Matching happens on the *items* a build needs (``blockwright.materials``), because that is what a player owns: a
door's two halves are one ``oak_door``, a wall torch is a ``torch``, a waterlogged stair is just the stair.
"""
from __future__ import annotations

import fnmatch
from pathlib import Path

from . import registry as R


def _ns(s: str) -> str:
    return s if ":" in s else "minecraft:" + s


def parse_palette(text: str) -> list:
    """Normalised entries of a palette text: ``minecraft:id``, glob patterns, or ``#minecraft:tag``."""
    out = []
    for raw in text.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line or line == "#" or line.startswith("# "):
            continue
        line = line.split()[0]
        if line.startswith("tag:"):
            line = "#" + line[4:]
        if line.startswith("#"):
            out.append("#" + _ns(line[1:]))
        else:
            out.append(_ns(line))
    return out


def load_palette(path) -> list:
    return parse_palette(Path(path).read_text(encoding="utf-8"))


def allowed_items(entries) -> tuple:
    """(exact item ids, glob patterns) for a list of palette entries; tags are expanded to their blocks' items."""
    exact, globs = set(), []
    for e in entries:
        if e.startswith("#"):
            for bid in R.tag_members(e[1:]):
                exact.add(bid)
                it = R.item(bid)
                if it and it != R.AIR:
                    exact.add(it)
        elif any(c in e for c in "*?["):
            globs.append(e)
        else:
            exact.add(e)
    return exact, globs


def outside(items, entries) -> list:
    """Item ids from ``items`` (iterable or {item: count}) that the palette does not allow, sorted."""
    exact, globs = allowed_items(entries)
    bad = []
    for it in items:
        if it in exact or any(fnmatch.fnmatchcase(it, g) for g in globs):
            continue
        bad.append(it)
    return sorted(bad)


def check_blocks(blocks, entries) -> list:
    """[(item, count, example_pos), ...] for every needed item outside the palette (empty = all allowed)."""
    from .materials import material_list
    mats = material_list(blocks)
    bad = set(outside(mats["items"], entries))
    if not bad:
        return []
    where = {}
    for pos, st in blocks.items():
        it = R.item(st)
        if it in bad and it not in where:
            where[it] = pos
    return [(it, mats["items"][it], where.get(it)) for it in sorted(bad)]
