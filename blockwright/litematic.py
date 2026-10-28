"""Read / write Litematica ``.litematic`` schematics (Litematica 0.29.1 for Minecraft 26.3).

VERIFIED FORMAT FACTS -- each checked in the vineflower-decompiled ``litematica-fabric-26.3-0.29.1.jar``
and ``malilib-fabric-26.3-0.30.2.jar`` (class.method in brackets):

 1. File = gzip-compressed NBT, root TAG_Compound with the empty name ""
    [malilib DataFileUtils.writeCompoundDataToCompressedNbtFile(file, data) -> rootTagName "", GZIPOutputStream;
    readCompoundDataFromNbtFile tries gzip first, then uncompressed].
 2. Root tags: MinecraftDataVersion Int (game data version, 5023 for 26.3), Version Int 7, SubVersion Int 1,
    Metadata Compound, Regions Compound [LitematicaSchematic.writeToData].  The reader requires Version as an
    Int (type 3) in 1..7 [readFromData]; palettes are datafixed only when MinecraftDataVersion < current
    [convertBlockStatePalette_to_1_20_5].
 3. Metadata [SchematicMetadata.writeData / readData]: Name, Author, Description String (always written);
    RegionCount Int (written if > 0), TotalVolume Int (if > 0), TotalBlocks Int (if >= 0), TimeCreated Long
    (if > 0), TimeModified Long (if > 0), EnclosingSize Compound {x,y,z: Int} (DataTypeUtils.createVec3iTag ->
    putVec3i), PreviewImageData IntArray (only if present and non-empty).  The reader treats every tag as
    optional; TotalVolume/TotalBlocks only if Int, EnclosingSize only if Compound, PreviewImageData only if
    IntArray (type 11).
 4. PreviewImageData = int[] of ARGB pixels (NativeImage.makePixelArray -> getPixel = ARGB.fromABGR),
    row-major ``x + y*width``.  Litematica itself stores 120x120 (GuiSchematicManager.PreviewGenerator:
    previewDimensions = 120); the browser accepts any square (WidgetSchematicBrowser.createPreviewImage:
    size = sqrt(len), requires size*size == len).  We always write 120x120.
 5. Regions: one Compound per region name [writeSubRegionsToData]: BlockStatePalette List<Compound>,
    BlockStates LongArray, TileEntities List<Compound>, PendingBlockTicks List, PendingFluidTicks List,
    Entities List, Position Compound{x,y,z Int}, Size Compound{x,y,z Int} (DataTypeUtils.createBlockPosTag).
    The reader skips a region whose Position/Size lack Int x,y,z, or whose BlockStates is not LongArray (12)
    [readSubRegionsFromData].  Size may be negative in Litematica files (min/max corners are used); we write
    Position (0,0,0) and a positive Size.
 6. Palette entry = {Name: String "minecraft:id", Properties: Compound{name: String value}}; Properties is
    omitted for blocks without properties (isSingletonState) [DataTypeUtils.writeBlockStateToTag].  The reader
    accepts "Name"/"id" and "Properties"/"properties"; unknown block -> air, unknown property ignored
    [DataTypeUtils.readBlockStateFromTag].  (Vanilla 26.3 NbtUtils uses lowercase id/properties; Litematica
    writes Name/Properties, so we do too.)
 7. Palette index 0 MUST be minecraft:air: the container registers AIR first (LitematicaBlockStateContainer.
    setBits -> palette.idFor(AIR_BLOCK_STATE)) and Linear/HashMap palette.readFromData skip entry 0 only when it
    is air -- a non-air entry 0 shifts every id by one.  Entries must be unique (requestNewId does not dedupe).
 8. Bits per entry = max(2, 32 - Integer.numberOfLeadingZeros(paletteSize - 1)) = max(2, (paletteSize-1).
    bit_length()) [LitematicaBlockStateContainer.createFrom]; <= 4 bits -> linear palette, else hash map (no
    effect on the file).
 9. LitematicaBitArray: entry i occupies bits [i*bits, (i+1)*bits) of the little-endian concatenation of the
    longs; an entry MAY span two longs (setAt/getAt: low part in long startOffset>>6 at bit startOffset&63,
    high part in the next long).  Length = roundUp(volume*bits, 64) / 64 (= ceil(volume*bits/64)).
10. Index order = y * (sizeX*sizeZ) + z * sizeX + x [LitematicaBlockStateContainer.getIndex].
11. TotalBlocks = number of non-air states (createFromWorld counts !state.isAir()); TotalVolume = sum of region
    volumes; EnclosingSize = size of the box enclosing all regions [LitematicaSchematic.createFromWorld].
12. TileEntities entries: the block entity NBT plus region-relative x,y,z Int (DataTypeUtils.writeBlockPosToTag);
    entries without Int x,y,z or empty are skipped [readTileEntitiesFromData].  Block entities may be omitted:
    Litematica's paste does world.setBlock(), and the chunk creates a default block entity for such blocks.
13. Empty lists: malilib ListData.write uses element type 0 (TAG_End) for an empty list, like vanilla.

Determinism: the gzip header mtime is fixed to 0, palette order is "air, then first appearance in index
order", tile entities are sorted by position -> identical inputs give byte-identical files except the
TimeCreated/TimeModified longs (pass ``time_ms`` or set env ``CC_TIME_MS`` to pin them as well).
"""
from __future__ import annotations

import gzip
import io
import math
import os
import re
import time
from pathlib import Path

import nbtlib
from nbtlib import Compound, Int, IntArray, List, Long, LongArray, String

from . import registry as R

DATA_VERSION = R.data_version()
VERSION = 7
SUB_VERSION = 1
PREVIEW_SIZE = 120
_MASK64 = (1 << 64) - 1
_GROUND_RE = re.compile(r"ground layer: y=(-?\d+) from the bottom")


# --------------------------------------------------------------------------------------- bit array
def bits_for(palette_len: int) -> int:
    """max(2, ceil(log2(palette_len))) exactly as LitematicaBlockStateContainer.createFrom."""
    return max(2, (palette_len - 1).bit_length())


def long_count(volume: int, bits: int) -> int:
    """LitematicaBitArray: roundUp(volume*bits, 64) / 64 (roundUp(0, 64) == 64)."""
    total = volume * bits
    return 1 if total == 0 else (total + 63) // 64


def _signed64(v: int) -> int:
    return v - (1 << 64) if v >= (1 << 63) else v


def pack(indices, bits: int) -> list:
    """Pack palette indices into signed 64-bit longs (LitematicaBitArray.setAt semantics)."""
    arr = [0] * long_count(len(indices), bits)
    maxv = (1 << bits) - 1
    for i, v in enumerate(indices):
        if v < 0 or v > maxv:
            raise ValueError(f"palette index {v} does not fit in {bits} bits")
        start = i * bits
        li, off = start >> 6, start & 63
        arr[li] |= (v << off) & _MASK64
        if off + bits > 64:
            arr[li + 1] |= v >> (64 - off)
    return [_signed64(a) for a in arr]


def unpack(longs, bits: int, count: int) -> list:
    """Inverse of :func:`pack` (LitematicaBitArray.getAt)."""
    u = [int(x) & _MASK64 for x in longs]
    maxv = (1 << bits) - 1
    out = [0] * count
    for i in range(count):
        start = i * bits
        li, off = start >> 6, start & 63
        v = u[li] >> off
        if off + bits > 64:
            v |= u[li + 1] << (64 - off)
        out[i] = v & maxv
    return out


# ------------------------------------------------------------------------------------- helpers
def _state_tag(state: str) -> Compound:
    bid, items = R._split(state)
    tag = Compound({"Name": String(bid)})
    if items:
        tag["Properties"] = Compound({k: String(v) for k, v in items})
    return tag


def _xyz(x, y, z) -> Compound:
    return Compound({"x": Int(x), "y": Int(y), "z": Int(z)})


def _now_ms(time_ms):
    if time_ms is not None:
        return int(time_ms)
    env = os.environ.get("CC_TIME_MS")
    if env:
        return int(env)
    return int(time.time() * 1000)


def describe_with_ground(description: str, ground) -> str:
    """Description text with the machine-readable ground line appended (once)."""
    d = _GROUND_RE.sub("", description or "").rstrip()
    if ground is None:
        return d
    line = f"ground layer: y={int(ground)} from the bottom"
    return f"{d}\n{line}" if d else line


def preview_from_image(path_or_image, size: int = PREVIEW_SIZE) -> list:
    """Centre-crop to a square, resize to size x size, return ARGB ints (row-major) for PreviewImageData."""
    from PIL import Image
    img = path_or_image if hasattr(path_or_image, "convert") else Image.open(path_or_image)
    img = img.convert("RGBA")
    w, h = img.size
    side = min(w, h)
    x0, y0 = (w - side) // 2, (h - side) // 2
    img = img.crop((x0, y0, x0 + side, y0 + side)).resize((size, size), Image.LANCZOS)
    out = []
    for r, g, b, a in img.getdata():
        out.append((a << 24) | (r << 16) | (g << 8) | b)
    return out


# ---------------------------------------------------------------------------------------- writing
def build_nbt(blocks: dict, size, *, name: str, author: str, description: str, region_name: str | None = None,
              preview_argb=None, tile_entities=None, ground=None, time_ms=None) -> nbtlib.File:
    """Build the root NBT compound (see module docstring).  ``blocks`` must be normalized to 0..size-1."""
    sx, sy, sz = (int(v) for v in size)
    if sx <= 0 or sy <= 0 or sz <= 0:
        raise ValueError(f"size must be positive, got {size}")
    volume = sx * sy * sz
    palette = [R.AIR]
    index_of = {R.AIR: 0}
    indices = [0] * volume
    count = 0
    for (x, y, z), st in blocks.items():
        if not (0 <= x < sx and 0 <= y < sy and 0 <= z < sz):
            raise ValueError(f"block at {(x, y, z)} outside size {size}")
    # first appearance in index order -> deterministic palette (Litematica assigns ids in scan order too)
    for y in range(sy):
        for z in range(sz):
            base = (y * sz + z) * sx
            for x in range(sx):
                st = blocks.get((x, y, z))
                if st is None:
                    continue
                c = R.parse_state(st)
                if R.is_air(c):
                    continue
                i = index_of.get(c)
                if i is None:
                    i = index_of[c] = len(palette)
                    palette.append(c)
                indices[base + x] = i
                count += 1
    bits = bits_for(len(palette))
    longs = pack(indices, bits)
    t = _now_ms(time_ms)
    if t <= 0:      # SchematicMetadata writes/reads the times only when > 0 (Litematica would show none)
        raise ValueError(f"time_ms / CC_TIME_MS must be > 0 epoch milliseconds, got {t}")

    tes = List[Compound]() if tile_entities else List()
    for pos in sorted(tile_entities or {}):
        tag = Compound(dict(tile_entities[pos]))
        tag["x"], tag["y"], tag["z"] = Int(pos[0]), Int(pos[1]), Int(pos[2])
        tes.append(tag)

    meta = Compound()
    meta["Name"] = String(name)
    meta["Author"] = String(author)
    meta["Description"] = String(describe_with_ground(description, ground))
    meta["RegionCount"] = Int(1)
    meta["TotalVolume"] = Int(volume)
    meta["TotalBlocks"] = Int(count)
    meta["TimeCreated"] = Long(t)
    meta["TimeModified"] = Long(t)
    meta["EnclosingSize"] = _xyz(sx, sy, sz)
    if preview_argb is not None and len(preview_argb) > 0:
        n = len(preview_argb)
        if math.isqrt(n) ** 2 != n:
            raise ValueError(f"PreviewImageData must be square (got {n} pixels)")
        meta["PreviewImageData"] = IntArray([((int(v) & 0xFFFFFFFF) ^ 0x80000000) - 0x80000000 for v in preview_argb])

    region = Compound()
    region["BlockStatePalette"] = List[Compound]([_state_tag(s) for s in palette])
    region["BlockStates"] = LongArray(longs)
    region["TileEntities"] = tes
    region["PendingBlockTicks"] = List()
    region["PendingFluidTicks"] = List()
    region["Entities"] = List()
    region["Position"] = _xyz(0, 0, 0)
    region["Size"] = _xyz(sx, sy, sz)

    root = nbtlib.File(root_name="")
    root["MinecraftDataVersion"] = Int(DATA_VERSION)
    root["Version"] = Int(VERSION)
    root["SubVersion"] = Int(SUB_VERSION)
    root["Metadata"] = meta
    root["Regions"] = Compound({region_name or name: region})
    return root


def encode(root: nbtlib.File) -> bytes:
    """Serialize with a deterministic gzip header (mtime 0)."""
    raw = io.BytesIO()
    root.write(raw)
    return gzip.compress(raw.getvalue(), compresslevel=9, mtime=0)


def write_litematic(path, blocks: dict, size, *, name: str, author: str, description: str = "",
                    region_name: str | None = None, preview_argb=None, tile_entities=None, ground=None,
                    time_ms=None) -> dict:
    """Write a single-region .litematic.  ``blocks``: {(x,y,z): state} with 0 <= coord < size (air omitted).

    ``preview_argb``: optional list of square ARGB ints (use :func:`preview_from_image`).
    ``ground``: y of the terrain surface layer, appended to Description as "ground layer: y=N from the bottom".
    Returns {"path", "palette_size", "bits", "total_blocks", "volume", "bytes"}.
    """
    root = build_nbt(blocks, size, name=name, author=author, description=description, region_name=region_name,
                     preview_argb=preview_argb, tile_entities=tile_entities, ground=ground, time_ms=time_ms)
    data = encode(root)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)
    reg = next(iter(root["Regions"].values()))
    pal = len(reg["BlockStatePalette"])
    return {"path": str(path), "palette_size": pal, "bits": bits_for(pal),
            "total_blocks": int(root["Metadata"]["TotalBlocks"]), "volume": int(root["Metadata"]["TotalVolume"]),
            "bytes": len(data)}


# ---------------------------------------------------------------------------------------- reading
def load_nbt(path) -> nbtlib.File:
    data = Path(path).read_bytes()
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    return nbtlib.File.parse(io.BytesIO(data))


def _palette_state(tag) -> str:
    # DataTypeUtils.readBlockStateFromTag: a lowercase "id"/"properties" key wins over "Name"/"Properties"
    name = str(tag["id"] if "id" in tag else tag.get("Name", "minecraft:air"))
    props = tag["properties"] if "properties" in tag else tag.get("Properties", {})
    return R.make_state(name, {str(k): str(v) for k, v in props.items()})


def read_litematic(path):
    """Read a .litematic -> ``(blocks, size, metadata)``.

    blocks: {(x,y,z): canonical state} (air omitted), coordinates relative to the enclosing box min corner.
    size: (sx, sy, sz) enclosing size.  metadata: dict with name, author, description, ground (parsed from the
    description, or None), time_created, time_modified, region_count, total_volume, total_blocks,
    enclosing_size, preview_argb (list or None), data_version, version, sub_version, regions (list of names),
    tile_entities {(x,y,z): Compound}.
    """
    root = load_nbt(path)
    meta_t = root.get("Metadata", Compound())
    regions = root.get("Regions", Compound())
    raw_blocks = {}
    tiles = {}
    mins = []
    region_data = []
    for rname, reg in regions.items():
        pos = tuple(int(reg["Position"][k]) for k in "xyz")
        rsize = tuple(int(reg["Size"][k]) for k in "xyz")
        end = tuple(p + (s - 1 if s >= 0 else s + 1) for p, s in zip(pos, rsize))
        mn = tuple(min(a, b) for a, b in zip(pos, end))
        mx = tuple(max(a, b) for a, b in zip(pos, end))
        region_data.append((rname, reg, mn, mx))
        mins.append(mn)
    if not region_data:
        raise ValueError(f"{path}: no regions")
    gmin = tuple(min(m[i] for m in mins) for i in range(3))
    gmax = tuple(max(r[3][i] for r in region_data) for i in range(3))
    size = tuple(gmax[i] - gmin[i] + 1 for i in range(3))
    for rname, reg, mn, mx in region_data:
        sx, sy, sz = (mx[i] - mn[i] + 1 for i in range(3))
        pal = [_palette_state(t) for t in reg["BlockStatePalette"]]
        bits = bits_for(len(pal))
        idx = unpack(reg["BlockStates"], bits, sx * sy * sz)
        for i, v in enumerate(idx):
            if v >= len(pal):
                raise ValueError(f"{path}: region {rname} index {i} -> palette id {v} >= palette size {len(pal)}")
            st = pal[v]
            if R.is_air(st):
                continue
            x = i % sx
            z = (i // sx) % sz
            y = i // (sx * sz)
            raw_blocks[(x + mn[0] - gmin[0], y + mn[1] - gmin[1], z + mn[2] - gmin[2])] = st
        for te in reg.get("TileEntities", []):
            if all(k in te for k in "xyz"):
                tiles[(int(te["x"]) + mn[0] - gmin[0], int(te["y"]) + mn[1] - gmin[1], int(te["z"]) + mn[2] - gmin[2])] = te
    desc = str(meta_t.get("Description", ""))
    m = _GROUND_RE.search(desc)
    prev = meta_t.get("PreviewImageData")
    metadata = {
        "name": str(meta_t.get("Name", "?")), "author": str(meta_t.get("Author", "?")), "description": desc,
        "ground": int(m.group(1)) if m else None,
        "time_created": int(meta_t.get("TimeCreated", -1)), "time_modified": int(meta_t.get("TimeModified", -1)),
        "region_count": int(meta_t.get("RegionCount", 0)), "total_volume": int(meta_t.get("TotalVolume", -1)),
        "total_blocks": int(meta_t.get("TotalBlocks", -1)),
        "enclosing_size": tuple(int(meta_t["EnclosingSize"][k]) for k in "xyz") if "EnclosingSize" in meta_t else None,
        "preview_argb": [int(v) & 0xFFFFFFFF for v in prev] if prev is not None else None,
        "data_version": int(root.get("MinecraftDataVersion", -1)), "version": int(root.get("Version", -1)),
        "sub_version": int(root.get("SubVersion", -1)), "regions": list(regions.keys()), "tile_entities": tiles,
    }
    return raw_blocks, size, metadata
