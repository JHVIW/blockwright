"""Write / read vanilla structure template ``.nbt`` files (``/place template``, structure blocks).

Verified against the decompiled 26.3 source:
  * StructureTemplate.save: tags ``blocks`` (List of {pos: List[Int x,y,z], state: Int, nbt?: Compound}),
    ``palette`` (List of block-state compounds), ``entities`` (List), ``size`` (List[Int x,y,z]) and
    ``DataVersion`` Int via NbtUtils.addCurrentDataVersion.
  * NbtUtils.writeBlockState in 26.3 writes ``{"id": String, "properties": Compound{String}}`` -- lowercase
    keys (older versions used Name/Properties); readBlockState reads ``id``/``properties``.  Because we write
    DataVersion 5023 the loader applies no datafixer, so the lowercase keys are required.
  * StructureTemplate.load -> loadPalette: blocks are re-sorted on load (addToLists/buildInfoList), so file
    order does not matter; we sort by (y, z, x) for determinism.
Air is omitted (unset cells keep the terrain when placed, like structure voids).
Install for /place: ``<world>/generated/minecraft/structures/<name>.nbt`` then
``/place template minecraft:<name> ~ ~ ~``.
"""
from __future__ import annotations

import os
from pathlib import Path

import nbtlib
from nbtlib import Compound, Int, List, String

from . import registry as R
from .litematic import encode, load_nbt

DATA_VERSION = R.data_version()


def build_structure(blocks: dict, size, tile_entities=None) -> nbtlib.File:
    sx, sy, sz = (int(v) for v in size)
    palette, index_of = [], {}
    entries = []
    for pos in sorted(blocks, key=lambda p: (p[1], p[2], p[0])):
        st = R.parse_state(blocks[pos])
        if R.is_air(st):
            continue
        x, y, z = pos
        if not (0 <= x < sx and 0 <= y < sy and 0 <= z < sz):
            raise ValueError(f"block at {pos} outside size {size}")
        i = index_of.get(st)
        if i is None:
            i = index_of[st] = len(palette)
            palette.append(st)
        e = Compound({"pos": List[Int]([Int(x), Int(y), Int(z)]), "state": Int(i)})
        if tile_entities and pos in tile_entities:
            e["nbt"] = Compound(dict(tile_entities[pos]))
        entries.append(e)
    pal = List[Compound]()
    for st in palette:
        bid, items = R._split(st)
        t = Compound({"id": String(bid)})
        if items:
            t["properties"] = Compound({k: String(v) for k, v in items})
        pal.append(t)
    root = nbtlib.File(root_name="")
    root["blocks"] = List[Compound](entries) if entries else List()
    root["palette"] = pal if palette else List()
    root["entities"] = List()
    root["size"] = List[Int]([Int(sx), Int(sy), Int(sz)])
    root["DataVersion"] = Int(DATA_VERSION)
    return root


def write_structure(path, blocks: dict, size, tile_entities=None) -> dict:
    """Write a gzipped vanilla structure .nbt; returns {"path", "blocks", "palette_size", "bytes"}."""
    root = build_structure(blocks, size, tile_entities)
    data = encode(root)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)
    return {"path": str(path), "blocks": len(root["blocks"]), "palette_size": len(root["palette"]), "bytes": len(data)}


def read_structure(path):
    """Read a structure .nbt -> (blocks, size, data_version). Accepts id/properties and legacy Name/Properties."""
    root = load_nbt(path)
    size = tuple(int(v) for v in root["size"])
    pal = []
    for t in root.get("palette", []):
        name = str(t.get("id", t.get("Name", "minecraft:air")))
        props = t.get("properties", t.get("Properties", {}))
        pal.append(R.make_state(name, {str(k): str(v) for k, v in props.items()}))
    blocks = {}
    for e in root.get("blocks", []):
        p = tuple(int(v) for v in e["pos"])
        st = pal[int(e["state"])]
        if not R.is_air(st):
            blocks[p] = st
    return blocks, size, int(root.get("DataVersion", -1))
