"""Validation of in-memory structures and written ``.litematic`` files against the verified Litematica 0.29.1
format (facts listed in ``blockwright/litematic.py``) and the 26.3 registry.

* ``validate_structure(blocks, size, meta=None) -> [problem, ...]`` -- used by ``Build.finish`` (strict).
* ``validate_file(path, expected=None) -> {"ok", "errors", "warnings", "stats"}`` -- parses the file back
  with nbtlib and checks every tag name/type, palette legality (complete property sets, legal values,
  air at index 0, no duplicates), bit-array length and indices, metadata totals, and (if ``expected=(blocks,
  size)`` is given) exact round-trip equality.
* ``assert_valid_file(path, expected=None)`` raises ``ValueError`` listing the errors.
"""
from __future__ import annotations

import math
from pathlib import Path

import nbtlib
from nbtlib import Compound, Int, IntArray, List, Long, LongArray, String

from . import registry as R
from .litematic import DATA_VERSION, PREVIEW_SIZE, SUB_VERSION, VERSION, bits_for, load_nbt, long_count, unpack


def validate_structure(blocks: dict, size, meta: dict | None = None) -> list:
    """Problems with a normalized structure (empty list = fine)."""
    probs = []
    try:
        sx, sy, sz = (int(v) for v in size)
    except Exception:
        return [f"size must be 3 ints, got {size!r}"]
    if min(sx, sy, sz) <= 0:
        probs.append(f"size must be positive, got {size}")
    for p, s in blocks.items():
        if len(p) != 3 or not all(isinstance(c, int) for c in p):
            probs.append(f"bad position {p!r}")
            continue
        if not (0 <= p[0] < sx and 0 <= p[1] < sy and 0 <= p[2] < sz):
            probs.append(f"block {s} at {p} outside size {size}")
        try:
            c = R.parse_state(s)
        except (ValueError, TypeError) as e:
            probs.append(f"illegal state at {p}: {e}")
            continue
        if c != s:
            probs.append(f"non-canonical state at {p}: {s!r} (canonical {c!r})")
        if R.is_air(c):
            probs.append(f"air stored explicitly at {p} (absence means air)")
        if len(probs) > 50:
            probs.append("... (truncated)")
            return probs
    if meta:
        def passable(q):
            s = blocks.get(q)
            return s is None or not R.full_collision(s)

        for name, q in (meta.get("rooms") or {}).items():
            if not (0 <= q[0] < sx and 0 <= q[1] < sy and 0 <= q[2] < sz):
                probs.append(f"room {name!r} marker {q} is outside the build box {size}")
            for qq, what in ((q, "feet"), ((q[0], q[1] + 1, q[2]), "head")):
                if not passable(qq):
                    probs.append(f"room {name!r} marker {q}: {what} cell {qq} is solid ({blocks[qq]})")
        for q in meta.get("entrances") or []:
            for qq, what in ((tuple(q), "feet"), ((q[0], q[1] + 1, q[2]), "head")):
                if not passable(qq):
                    probs.append(f"entrance marker {tuple(q)}: {what} cell {qq} is solid ({blocks[qq]})")
        g = meta.get("ground")
        if g is not None and not (-3 <= g <= sy):
            probs.append(f"ground y={g} is far outside the build height 0..{sy - 1}")
    return probs


def _is(tag, cls) -> bool:
    return isinstance(tag, cls)


def _check_xyz(tag, where, errs):
    if not _is(tag, Compound):
        errs.append(f"{where} must be a Compound, got {type(tag).__name__}")
        return None
    for k in "xyz":
        if k not in tag or not _is(tag[k], Int):
            errs.append(f"{where}.{k} must be an Int")
            return None
    return tuple(int(tag[k]) for k in "xyz")


def validate_file(path, expected=None) -> dict:
    """Validate a written .litematic.  ``expected``: optional ``(blocks, size)`` for exact round-trip equality."""
    errs, warns, stats = [], [], {}
    path = Path(path)
    raw = path.read_bytes()
    if raw[:2] != b"\x1f\x8b":
        errs.append("file is not gzip-compressed (Litematica writes GZIPOutputStream)")
    try:
        root = load_nbt(path)
    except Exception as e:
        return {"ok": False, "errors": [f"cannot parse NBT: {e}"], "warnings": warns, "stats": stats}
    if getattr(root, "root_name", "") != "":
        errs.append(f"root tag name must be empty, got {root.root_name!r}")

    def need(tag, key, cls, where):
        if key not in tag:
            errs.append(f"missing {where}{key}")
            return None
        if not _is(tag[key], cls):
            errs.append(f"{where}{key} must be {cls.__name__}, got {type(tag[key]).__name__}")
            return None
        return tag[key]

    dv = need(root, "MinecraftDataVersion", Int, "")
    if dv is not None and int(dv) != DATA_VERSION:
        errs.append(f"MinecraftDataVersion {int(dv)} != {DATA_VERSION}")
    v = need(root, "Version", Int, "")
    if v is not None and int(v) != VERSION:
        errs.append(f"Version {int(v)} != {VERSION}")
    sv = need(root, "SubVersion", Int, "")
    if sv is not None and int(sv) != SUB_VERSION:
        errs.append(f"SubVersion {int(sv)} != {SUB_VERSION}")
    meta = need(root, "Metadata", Compound, "")
    regions = need(root, "Regions", Compound, "")
    extra = set(root) - {"MinecraftDataVersion", "Version", "SubVersion", "Metadata", "Regions"}
    if extra:
        warns.append(f"unexpected root tags: {sorted(extra)}")
    if meta is None or regions is None:
        return {"ok": False, "errors": errs, "warnings": warns, "stats": stats}

    total_volume = 0
    total_blocks = 0
    mins, maxs = [], []
    decoded = {}
    for rname, reg in regions.items():
        w = f"Regions.{rname}."
        if not _is(reg, Compound):
            errs.append(f"{w[:-1]} must be a Compound")
            continue
        pos = _check_xyz(reg.get("Position"), w + "Position", errs) if "Position" in reg else errs.append(f"missing {w}Position")
        size = _check_xyz(reg.get("Size"), w + "Size", errs) if "Size" in reg else errs.append(f"missing {w}Size")
        pal = need(reg, "BlockStatePalette", List, w)
        bs = need(reg, "BlockStates", LongArray, w)
        for k in ("TileEntities", "Entities", "PendingBlockTicks", "PendingFluidTicks"):
            lst = need(reg, k, List, w)
            if lst is not None and len(lst) and lst.subtype is not Compound:
                errs.append(f"{w}{k} elements must be Compounds")
        if pos is None or size is None or pal is None or bs is None:
            continue
        if 0 in size:
            errs.append(f"{w}Size has a zero dimension {size}")
            continue
        if any(s < 0 for s in size):
            warns.append(f"{w}Size is negative {size} (allowed by Litematica, never written by blockwright)")
        asz = tuple(abs(s) for s in size)
        end = tuple(p + (s - 1 if s > 0 else s + 1) for p, s in zip(pos, size))
        mins.append(tuple(min(a, b) for a, b in zip(pos, end)))
        maxs.append(tuple(max(a, b) for a, b in zip(pos, end)))
        volume = asz[0] * asz[1] * asz[2]
        total_volume += volume
        # palette
        states = []
        seen = set()
        for i, t in enumerate(pal):
            pw = f"{w}BlockStatePalette[{i}]"
            if not _is(t, Compound):
                errs.append(f"{pw} must be a Compound")
                states.append(R.AIR)
                continue
            name = t.get("Name")
            if not _is(name, String):
                errs.append(f"{pw}.Name must be a String")
                states.append(R.AIR)
                continue
            bid = str(name)
            if not R.exists(bid) or ":" not in bid:
                errs.append(f"{pw}: unknown or un-namespaced block {bid!r}")
                states.append(R.AIR)
                continue
            legal = R.info(bid).properties
            props = t.get("Properties")
            if legal:
                if not _is(props, Compound):
                    errs.append(f"{pw} ({bid}) must have a Properties Compound")
                    states.append(R.AIR)
                    continue
                if set(props) != set(legal):
                    errs.append(f"{pw} ({bid}) properties {sorted(props)} != registry {sorted(legal)}")
                for k, val in props.items():
                    if not _is(val, String):
                        errs.append(f"{pw}.Properties.{k} must be a String")
                    elif k in legal and str(val) not in legal[k]:
                        errs.append(f"{pw}.Properties.{k}={val} not legal for {bid} ({', '.join(legal[k])})")
            elif props is not None:
                errs.append(f"{pw} ({bid}) has no properties but carries a Properties tag")
            extra_keys = set(t) - {"Name", "Properties"}
            if extra_keys:
                warns.append(f"{pw} has extra keys {sorted(extra_keys)}")
            try:
                st = R.make_state(bid, {str(k): str(val) for k, val in (props or {}).items()})
            except ValueError as e:
                errs.append(f"{pw}: {e}")
                st = R.AIR
            if st in seen:
                errs.append(f"{pw}: duplicate palette entry {st} (Litematica palettes do not dedupe)")
            seen.add(st)
            states.append(st)
        if not states or states[0] != R.AIR or (len(pal) and "Properties" in pal[0]):
            errs.append(f"{w}BlockStatePalette[0] must be minecraft:air without Properties")
        bits = bits_for(len(states))
        want = long_count(volume, bits)
        if len(bs) != want:
            errs.append(f"{w}BlockStates has {len(bs)} longs, expected {want} (volume {volume}, {bits} bits)")
            continue
        idx = unpack(bs, bits, volume)
        bad = [i for i, x in enumerate(idx) if x >= len(states)]
        if bad:
            errs.append(f"{w}BlockStates: {len(bad)} indices >= palette size {len(states)} (first at {bad[0]})")
            continue
        pad_bits = len(bs) * 64 - volume * bits
        if pad_bits:
            last = int(bs[-1]) & ((1 << 64) - 1)
            if last >> (64 - pad_bits):
                warns.append(f"{w}BlockStates has non-zero padding bits")
        used = set(idx)
        unused = [states[i] for i in range(1, len(states)) if i not in used]
        if unused:
            warns.append(f"{w}{len(unused)} unused palette entries")
        sx, sy, sz = asz
        mn = mins[-1]
        for i, x in enumerate(idx):
            st = states[x]
            if st == R.AIR or R.is_air(st):
                continue
            total_blocks += 1
            decoded[(i % sx + mn[0], i // (sx * sz) + mn[1], (i // sx) % sz + mn[2])] = st
        for j, te in enumerate(reg.get("TileEntities", [])):
            p = _check_xyz(te, f"{w}TileEntities[{j}]", errs)
            if p is not None and not all(0 <= p[k] < asz[k] for k in range(3)):
                errs.append(f"{w}TileEntities[{j}] position {p} outside the region")
        stats.setdefault("regions", {})[rname] = {"size": size, "palette": len(states), "bits": bits, "longs": len(bs)}

    # metadata
    for k, cls in (("Name", String), ("Author", String), ("Description", String), ("RegionCount", Int),
                   ("TotalVolume", Int), ("TotalBlocks", Int), ("TimeCreated", Long), ("TimeModified", Long),
                   ("EnclosingSize", Compound)):
        need(meta, k, cls, "Metadata.")
    if _is(meta.get("RegionCount"), Int) and int(meta["RegionCount"]) != len(regions):
        errs.append(f"Metadata.RegionCount {int(meta['RegionCount'])} != {len(regions)} regions")
    if _is(meta.get("TotalVolume"), Int) and int(meta["TotalVolume"]) != total_volume:
        errs.append(f"Metadata.TotalVolume {int(meta['TotalVolume'])} != {total_volume}")
    if _is(meta.get("TotalBlocks"), Int) and int(meta["TotalBlocks"]) != total_blocks:
        errs.append(f"Metadata.TotalBlocks {int(meta['TotalBlocks'])} != {total_blocks} non-air blocks")
    for k in ("TimeCreated", "TimeModified"):
        if _is(meta.get(k), Long) and int(meta[k]) <= 0:
            warns.append(f"Metadata.{k} <= 0 (Litematica then omits it)")
    enc = None
    if mins:
        gmin = tuple(min(m[i] for m in mins) for i in range(3))
        gmax = tuple(max(m[i] for m in maxs) for i in range(3))
        enc = tuple(gmax[i] - gmin[i] + 1 for i in range(3))
        es = _check_xyz(meta.get("EnclosingSize"), "Metadata.EnclosingSize", errs) if "EnclosingSize" in meta else None
        if es is not None and es != enc:
            errs.append(f"Metadata.EnclosingSize {es} != enclosing box {enc}")
    if "PreviewImageData" in meta:
        pv = meta["PreviewImageData"]
        if not _is(pv, IntArray):
            errs.append("Metadata.PreviewImageData must be an IntArray")
        else:
            n = len(pv)
            if n == 0 or math.isqrt(n) ** 2 != n:
                errs.append(f"Metadata.PreviewImageData length {n} is not a non-empty square")
            elif n != PREVIEW_SIZE * PREVIEW_SIZE:
                warns.append(f"PreviewImageData is {math.isqrt(n)}x{math.isqrt(n)} (Litematica makes {PREVIEW_SIZE}x{PREVIEW_SIZE})")
    stats.update(total_blocks=total_blocks, total_volume=total_volume, enclosing=enc)

    if expected is not None:
        eb, esz = expected
        if enc is not None and tuple(esz) != enc:
            errs.append(f"round-trip size {enc} != expected {tuple(esz)}")
        eb = {p: R.parse_state(s) for p, s in eb.items() if not R.is_air(R.parse_state(s))}
        if decoded != eb:
            missing = [p for p in eb if p not in decoded][:5]
            extra_p = [p for p in decoded if p not in eb][:5]
            diff = [p for p in eb if p in decoded and decoded[p] != eb[p]][:5]
            errs.append(f"round-trip block mismatch: missing {missing}, extra {extra_p}, "
                        f"different {[(p, eb[p], decoded[p]) for p in diff]}")
    return {"ok": not errs, "errors": errs, "warnings": warns, "stats": stats}


def assert_valid_file(path, expected=None) -> dict:
    rep = validate_file(path, expected)
    if rep["errors"]:
        raise ValueError(f"{path}: invalid litematic:\n  - " + "\n  - ".join(rep["errors"]))
    return rep
