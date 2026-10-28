"""Minimal standalone .litematic reader for the renderer CLI (does not depend on blockwright.litematic)."""
from __future__ import annotations

import json
import math
import pathlib
import re

import nbtlib
import numpy as np


def _state_string(entry) -> str:
    name = str(entry["Name"])
    if ":" not in name:
        name = "minecraft:" + name
    props = entry.get("Properties")
    if props:
        inner = ",".join(f"{k}={str(v)}" for k, v in props.items())
        return f"{name}[{inner}]"
    return name


def decode_bits(longs, n_entries: int, bits: int) -> np.ndarray:
    """LitematicaBitArray: entries packed back-to-back LSB-first, may span two longs."""
    arr = np.asarray(longs, dtype=np.int64).view(np.uint64)
    idx = np.arange(n_entries, dtype=np.uint64)
    start_bit = idx * np.uint64(bits)
    start_long = (start_bit >> np.uint64(6)).astype(np.int64)
    off = start_bit & np.uint64(63)
    end_long = ((start_bit + np.uint64(bits) - np.uint64(1)) >> np.uint64(6)).astype(np.int64)
    mask = np.uint64((1 << bits) - 1)
    lo = arr[start_long] >> off
    val = lo & mask
    span = start_long != end_long
    if span.any():
        hi_shift = np.uint64(64) - off[span]
        hi = arr[end_long[span]] << hi_shift
        val[span] = (lo[span] | hi) & mask
    return val.astype(np.int64)


def read_litematic(path):
    """Returns (blocks {(x,y,z): state}, size (sx,sy,sz), meta dict). Multiple regions are merged
    in schematic-global coordinates and normalised so the min corner is (0,0,0)."""
    f = nbtlib.load(str(path))
    root = f.root if hasattr(f, "root") else f
    md = root.get("Metadata", {})
    meta = {}
    for k in ("Name", "Author", "Description"):
        if k in md:
            meta[k.lower()] = str(md[k])
    blocks = {}
    for rname, reg in root["Regions"].items():
        pos = reg["Position"]
        siz = reg["Size"]
        px, py, pz = int(pos["x"]), int(pos["y"]), int(pos["z"])
        sx, sy, sz = int(siz["x"]), int(siz["y"]), int(siz["z"])
        # negative sizes: region extends towards negative axis from Position
        ox = px + sx + 1 if sx < 0 else px
        oy = py + sy + 1 if sy < 0 else py
        oz = pz + sz + 1 if sz < 0 else pz
        ax, ay, az = abs(sx), abs(sy), abs(sz)
        palette = [_state_string(e) for e in reg["BlockStatePalette"]]
        bits = max(2, math.ceil(math.log2(max(len(palette), 1))))
        vol = ax * ay * az
        longs = reg["BlockStates"]
        need = math.ceil(vol * bits / 64)
        if len(longs) < need:
            raise ValueError(f"{path}: region {rname!r}: BlockStates has {len(longs)} longs, "
                             f"{need} needed for {ax}x{ay}x{az} at {bits} bits")
        vals = decode_bits(longs, vol, bits)
        if len(palette) and int(vals.max(initial=0)) >= len(palette):
            raise ValueError(f"{path}: region {rname!r}: palette index {int(vals.max())} out of range "
                             f"({len(palette)} entries)")
        # palette entry 0 is normally air, but do not assume it (Litematica just indexes the palette)
        air_ids = [k for k, s in enumerate(palette) if s.split("[")[0] in
                   ("minecraft:air", "minecraft:cave_air", "minecraft:void_air")]
        keep = ~np.isin(vals, np.array(air_ids, np.int64)) if air_ids else np.ones(len(vals), bool)
        nz = np.flatnonzero(keep)
        for i in nz.tolist():
            st = palette[vals[i]]
            x = i % ax
            z = (i // ax) % az
            y = i // (ax * az)
            blocks[(ox + x, oy + y, oz + z)] = st
    if blocks:
        arr = np.array(list(blocks.keys()))
        mn = arr.min(0)
    else:
        mn = np.zeros(3, int)
    es = md.get("EnclosingSize")
    if es is not None:
        size = (int(es["x"]), int(es["y"]), int(es["z"]))
    else:
        mx = np.array(list(blocks.keys())).max(0) if blocks else np.zeros(3, int)
        size = tuple(int(v) for v in (mx - mn + 1))
    # region positions are relative to the schematic origin; normalise to min corner of the regions
    allmin = []
    for rname, reg in root["Regions"].items():
        pos, siz = reg["Position"], reg["Size"]
        allmin.append([min(int(pos[a]), int(pos[a]) + int(siz[a]) + 1) if int(siz[a]) < 0 else int(pos[a])
                       for a in "xyz"])
    o = np.array(allmin).min(0) if allmin else np.zeros(3, int)
    blocks = {(x - int(o[0]), y - int(o[1]), z - int(o[2])): s for (x, y, z), s in blocks.items()}
    # ground line written by blockwright.litematic ("ground layer: y=N from the bottom")
    desc = meta.get("description", "")
    m = re.search(r"ground layer: y=(-?\d+) from the bottom", desc)
    if m:
        meta["ground"] = int(m.group(1))
    # sidecar <stem>.meta.json (slug, title, ground, rooms, entrances, ...) written by the build pipeline
    side = pathlib.Path(path).with_suffix("").with_suffix(".meta.json")
    if side.exists():
        try:
            j = json.loads(side.read_text(encoding="utf-8"))
            if isinstance(j, dict):
                for k, v in j.items():
                    if v is not None:
                        meta[k] = v
        except Exception:
            pass
    meta.setdefault("slug", pathlib.Path(path).stem)
    meta.setdefault("title", meta.get("name", meta["slug"]))
    return blocks, size, meta
