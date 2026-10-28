"""Independent .litematic fixture writer + fixture self-test for tools/validate.sh.

This deliberately does NOT import `blockwright` (the core library): it is a second, tiny implementation of the
format documented in docs/litematic-format.md, used to prove the Java validator works and to give the core
writer something to diff against.

Usage:
    python tests/fixtures/make_fixtures.py            # (re)write all fixtures into tests/fixtures/
    python tests/fixtures/make_fixtures.py --check    # write them, then run tools/validate.sh on each and
                                                      # assert the expected verdict / error text

Ground truth for block ids, property names, legal values and defaults: data/blocks_26.3.json.
"""
import gzip
import io
import json
import pathlib
import shutil
import subprocess
import sys

import nbtlib
from nbtlib.tag import Compound, Int, IntArray, List, Long, LongArray, String

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REGISTRY = json.loads((ROOT / "data" / "blocks_26.3.json").read_text(encoding="utf-8"))
BLOCKS = REGISTRY["blocks"]
DATA_VERSION = REGISTRY["data_version"]          # 5023 for 26.3
FIXED_TIME = 1761393600000                       # 2025-10-25T12:00:00Z, fixed so output is reproducible

AIR = "minecraft:air"


# --------------------------------------------------------------------------------------------- states

def state(name, **props):
    """Canonical palette entry: (block id, full property dict) with registry defaults filled in.

    Validates against the registry dump so the *valid* fixtures are valid by construction.
    """
    if ":" not in name:
        name = "minecraft:" + name
    info = BLOCKS[name]                                   # KeyError = unknown block, on purpose
    full = dict(info["default"])
    for k, v in props.items():
        v = str(v).lower() if isinstance(v, bool) else str(v)
        if k not in info["properties"] or v not in info["properties"][k]:
            raise ValueError(f"{name}: illegal {k}={v}")
        full[k] = v
    return (name, tuple(sorted(full.items())))


def raw_state(name, props):
    """Palette entry written exactly as given (no defaults, no validation) - for broken fixtures."""
    return (name, tuple(props.items()))


def palette_tag(entry):
    name, props = entry
    tag = Compound({"Name": String(name)})
    if props:                                            # Litematica omits Properties for single-state blocks
        tag["Properties"] = Compound({k: String(v) for k, v in props})
    return tag


# --------------------------------------------------------------------------------------------- bit packing

def bits_for(palette_size):
    """Litematica: max(2, 32 - Integer.numberOfLeadingZeros(paletteSize - 1)) == max(2, ceil(log2(n)))."""
    return max(2, (palette_size - 1).bit_length())


def pack(indices, bits):
    """LitematicaBitArray packing: entry i occupies bits [i*bits, (i+1)*bits) of the little-endian bit
    stream formed by the longs (bit 0 = LSB of long 0); entries MAY straddle two longs."""
    n_longs = (len(indices) * bits + 63) // 64
    words = [0] * n_longs
    mask = (1 << bits) - 1
    for i, v in enumerate(indices):
        assert 0 <= v <= mask
        start = i * bits
        w, off = start >> 6, start & 63
        words[w] |= (v << off) & 0xFFFFFFFFFFFFFFFF
        if off + bits > 64:                              # spills into the next long
            words[w + 1] |= v >> (64 - off)
    return [x - (1 << 64) if x >= (1 << 63) else x for x in words]   # NBT longs are signed


# --------------------------------------------------------------------------------------------- writer

class Region:
    def __init__(self, name, position, size):
        self.name = name
        self.position = position                         # Position tag (corner "pos1", relative to schematic origin)
        self.size = size                                 # signed Size tag; |size| = container dimensions
        self.blocks = {}                                 # (x,y,z) container coords (0..|size|-1) -> entry
        self.tile_entities = []                          # list of Compound (with x,y,z container coords)
        self.palette_override = None                     # broken fixtures: explicit palette list
        self.blockstates_override = None                 # broken fixtures: explicit long list

    @property
    def dims(self):
        return tuple(abs(s) for s in self.size)

    def min_corner(self):
        """Region min corner relative to schematic origin (PositionUtils.getRelativeEndPositionFromAreaSize)."""
        end = [p + (s - 1 if s > 0 else s + 1) for p, s in zip(self.position, self.size)]
        return tuple(min(a, b) for a, b in zip(self.position, end)), tuple(max(a, b) for a, b in zip(self.position, end))

    def to_tag(self):
        sx, sy, sz = self.dims
        palette = [(AIR, ())]                            # index 0 MUST be air
        index_of = {palette[0]: 0}
        for e in sorted(set(self.blocks.values()) - {palette[0]}):
            index_of[e] = len(palette)
            palette.append(e)
        if self.palette_override is not None:
            palette = self.palette_override
            index_of = {e: i for i, e in enumerate(palette)}
        indices = []
        for y in range(sy):                              # index = (y*sz + z)*sx + x
            for z in range(sz):
                for x in range(sx):
                    indices.append(index_of[self.blocks.get((x, y, z), (AIR, ()))])
        longs = pack(indices, bits_for(len(palette)))
        if self.blockstates_override is not None:
            longs = self.blockstates_override(longs)
        return Compound({
            "BlockStatePalette": compound_list([palette_tag(e) for e in palette]),
            "BlockStates": LongArray(longs),
            "TileEntities": compound_list(self.tile_entities),
            "PendingBlockTicks": compound_list([]),
            "PendingFluidTicks": compound_list([]),
            "Entities": compound_list([]),
            "Position": xyz(self.position),
            "Size": xyz(self.size),
        })

    def non_air_count(self):
        return sum(1 for e in self.blocks.values() if e[0] not in ("minecraft:air", "minecraft:cave_air", "minecraft:void_air"))


def compound_list(items):
    """List of Compound; an empty list is written with element type End (0), exactly like Litematica/vanilla do."""
    return List[Compound](items) if items else List([])


def xyz(v):
    return Compound({"x": Int(v[0]), "y": Int(v[1]), "z": Int(v[2])})


def write_litematic(path, name, regions, description="", preview=None, meta_override=None):
    mins = [r.min_corner()[0] for r in regions]
    maxs = [r.min_corner()[1] for r in regions]
    lo = [min(m[i] for m in mins) for i in range(3)]
    hi = [max(m[i] for m in maxs) for i in range(3)]
    meta = Compound({
        "Name": String(name),
        "Author": String("make_fixtures.py"),
        "Description": String(description),
        "RegionCount": Int(len(regions)),
        "TotalVolume": Int(sum(r.dims[0] * r.dims[1] * r.dims[2] for r in regions)),
        "TotalBlocks": Int(sum(r.non_air_count() for r in regions)),
        "TimeCreated": Long(FIXED_TIME),
        "TimeModified": Long(FIXED_TIME),
        "EnclosingSize": xyz([hi[i] - lo[i] + 1 for i in range(3)]),
    })
    if preview is not None:
        meta["PreviewImageData"] = IntArray(preview)
    if meta_override:
        meta_override(meta)
    root = nbtlib.File({
        "MinecraftDataVersion": Int(DATA_VERSION),
        "Version": Int(7),
        "SubVersion": Int(1),
        "Metadata": meta,
        "Regions": Compound({r.name: r.to_tag() for r in regions}),
    }, gzipped=True, root_name="")
    buf = io.BytesIO()
    root.write(buf)                                      # type byte 10, root name "", payload
    pathlib.Path(path).write_bytes(gzip.compress(buf.getvalue(), mtime=0))   # mtime=0: byte-identical reruns
    return path


# --------------------------------------------------------------------------------------------- fixtures

def tiny_region(name="tiny"):
    """3x3x3, palette = air, stone, oak_planks (3 states, 2 bits)."""
    r = Region(name, (0, 0, 0), (3, 3, 3))
    for x in range(3):
        for z in range(3):
            r.blocks[(x, 0, z)] = state("stone")
    r.blocks[(1, 1, 1)] = state("oak_planks")
    r.blocks[(0, 1, 0)] = state("oak_planks")
    r.blocks[(2, 2, 2)] = state("oak_planks")
    return r


def stairs_region():
    """5x4x6 = 120 cells, 21 palette entries -> 5 bits/entry (entries straddle long boundaries)."""
    r = Region("stairs", (0, 0, 0), (5, 4, 6))
    sx, sy, sz = r.dims
    for x in range(sx):
        for z in range(sz):
            r.blocks[(x, 0, z)] = state("cobblestone") if (x + z) % 3 else state("mossy_cobblestone")
    stair_variants = [
        state("oak_stairs", facing="north", half="bottom", shape="straight", waterlogged=False),
        state("oak_stairs", facing="south", half="top", shape="inner_left", waterlogged=False),
        state("oak_stairs", facing="east", half="bottom", shape="outer_right", waterlogged=True),
        state("spruce_stairs", facing="west", half="top", shape="outer_left", waterlogged=False),
        state("spruce_stairs", facing="north", half="bottom", shape="inner_right", waterlogged=True),
    ]
    others = [
        state("spruce_slab", type="top"),
        state("spruce_slab", type="bottom", waterlogged=True),
        state("oak_log", axis="x"),
        state("oak_log", axis="z"),
        state("lantern", hanging=True),
        state("oak_fence", north=True, south=True),
        state("cobblestone_wall", up=True, east="low", west="tall"),
        state("oak_door", facing="east", half="lower", hinge="right"),
        state("oak_door", facing="east", half="upper", hinge="right"),
        state("spruce_trapdoor", facing="south", half="top", open=True),
        state("iron_chain", axis="x"),
        state("potted_poppy"),
        state("chest", facing="west"),
    ]
    cells = [(x, y, z) for y in range(1, sy) for z in range(sz) for x in range(sx)]
    for i, e in enumerate(stair_variants + others):
        r.blocks[cells[i * 3]] = e
    # a block entity with its TileEntities record (coords are container coords, relative to the region min corner)
    chest_pos = [p for p, e in r.blocks.items() if e[0] == "minecraft:chest"][0]
    r.tile_entities.append(Compound({
        "id": String("minecraft:chest"),
        "x": Int(chest_pos[0]), "y": Int(chest_pos[1]), "z": Int(chest_pos[2]),
        "Items": List[Compound]([]),
    }))
    return r


def preview_pixels(n=120):
    """n*n ARGB ints (row-major, index = x + y*n), as Litematica's NativeImage.makePixelArray produces."""
    px = []
    for y in range(n):
        for x in range(n):
            argb = (0xFF << 24) | ((x * 2) << 16) | ((y * 2) << 8) | 0x60
            px.append(argb - (1 << 32) if argb >= (1 << 31) else argb)
    return px


def multi_region():
    """Two regions, the second with a negative Size (Litematica keeps the selection's corner-1 as Position)."""
    a = Region("a_positive", (0, 0, 0), (3, 2, 2))
    for x in range(3):
        for z in range(2):
            a.blocks[(x, 0, z)] = state("dirt_path")
    b = Region("b_negative", (5, 1, 4), (-2, -2, -3))     # covers x 4..5, y 0..1, z 2..4
    b.blocks[(0, 0, 0)] = state("oak_log", axis="y")       # container (0,0,0) = region MIN corner (4,0,2)
    b.blocks[(1, 1, 2)] = state("lantern")                 # max corner (5,1,4) == Position
    return [a, b]


def build_all():
    out = {}
    out["tiny_3x3x3"] = write_litematic(HERE / "tiny_3x3x3.litematic", "tiny_3x3x3", [tiny_region()])
    out["stairs_5x4x6_5bit"] = write_litematic(HERE / "stairs_5x4x6_5bit.litematic", "stairs_5x4x6_5bit",
                                              [stairs_region()], description="5-bit palette, straddling entries",
                                              preview=preview_pixels())
    out["multi_region_negative"] = write_litematic(HERE / "multi_region_negative.litematic", "multi_region_negative",
                                                  multi_region())

    # ---- broken ones (each must FAIL with the given error text) ----
    r = tiny_region()
    r.blocks[(1, 2, 1)] = raw_state("minecraft:oak_stairs",
                                    {"facing": "up", "half": "bottom", "shape": "straight", "waterlogged": "false"})
    out["broken_bad_value"] = write_litematic(HERE / "broken_bad_value.litematic", "broken_bad_value", [r])

    r = tiny_region()
    r.blocks[(1, 2, 1)] = raw_state("minecraft:cottage_door", {})
    out["broken_unknown_block"] = write_litematic(HERE / "broken_unknown_block.litematic", "broken_unknown_block", [r])

    r = tiny_region()
    r.blocks[(1, 2, 1)] = raw_state("minecraft:lantern", {"hanging": "false", "waterlogged": "false", "lit": "true"})
    out["broken_unknown_property"] = write_litematic(HERE / "broken_unknown_property.litematic", "broken_unknown_property", [r])

    r = tiny_region()
    r.blocks[(1, 2, 1)] = raw_state("minecraft:oak_stairs", {"facing": "east", "half": "top"})
    out["broken_missing_property"] = write_litematic(HERE / "broken_missing_property.litematic", "broken_missing_property", [r])

    r = tiny_region()
    r.palette_override = [state("stone"), (AIR, ()), state("oak_planks")]
    out["broken_air_not_first"] = write_litematic(HERE / "broken_air_not_first.litematic", "broken_air_not_first", [r])

    r = stairs_region()
    r.blockstates_override = lambda longs: longs[:-1]
    out["broken_short_blockstates"] = write_litematic(HERE / "broken_short_blockstates.litematic", "broken_short_blockstates", [r])

    def bad_counts(meta):
        meta["TotalBlocks"] = Int(int(meta["TotalBlocks"]) + 1)
        meta["EnclosingSize"] = xyz((3, 4, 3))
    out["broken_metadata_counts"] = write_litematic(HERE / "broken_metadata_counts.litematic", "broken_metadata_counts",
                                                   [tiny_region()], meta_override=bad_counts)

    def bad_types(meta):
        meta["TotalVolume"] = Long(27)                   # Litematica ignores TotalVolume unless it is an Int
    out["broken_metadata_types"] = write_litematic(HERE / "broken_metadata_types.litematic", "broken_metadata_types",
                                                  [tiny_region()], meta_override=bad_types)
    return out


# expected verdicts for --check: (should_pass, substring that must appear in the validator output)
EXPECT = {
    "tiny_3x3x3": (True, "litematica: loaded, 27/27 cells identical"),
    "stairs_5x4x6_5bit": (True, "litematica: loaded, 120/120 cells identical"),
    "multi_region_negative": (True, "litematica: loaded, 24/24 cells identical"),
    "broken_bad_value": (False, "illegal value 'up' for property 'facing'"),
    "broken_unknown_block": (False, "unknown block 'minecraft:cottage_door'"),
    "broken_unknown_property": (False, "unknown property 'lit'"),
    "broken_missing_property": (False, "missing properties [shape, waterlogged]"),
    "broken_air_not_first": (False, "palette[0] must be minecraft:air"),
    "broken_short_blockstates": (False, "BlockStates has 9 longs, expected 10"),
    "broken_metadata_counts": (False, "Metadata.TotalBlocks=13 but"),
    "broken_metadata_types": (False, "Metadata.TotalVolume must be Int"),
}


def run_validator(paths):
    """One JVM for all files (bootstrap takes seconds). Returns (exit code, {file stem: output section})."""
    validate = (ROOT / "tools" / "validate.sh").as_posix()
    # shutil.which finds Git Bash; a bare "bash" in CreateProcess would pick System32ash.exe (WSL) first on Windows
    bash = shutil.which("bash") or "bash"
    proc = subprocess.run([bash, validate] + [p.as_posix() for p in paths], capture_output=True, text=True)
    sections, current = {}, None
    for line in proc.stdout.splitlines():
        if line.startswith("== "):
            current = pathlib.PureWindowsPath(line[3:]).stem
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return proc.returncode, {k: "\n".join(v) for k, v in sections.items()}, proc.stdout + proc.stderr


def check(paths):
    code, sections, raw = run_validator(list(paths.values()))
    failures = 0
    for key, path in paths.items():
        should_pass, needle = EXPECT[key]
        out = sections.get(key, "")
        passed = "\n  PASS (" in out
        ok = bool(out) and passed == should_pass and needle in out
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {key:28s} verdict={'PASS' if passed else 'FAIL'} expect={'PASS' if should_pass else 'FAIL'}"
              f"{'' if needle in out else '  (missing text: ' + needle + ')'}")
        if not ok:
            print("     " + (out or raw).strip().replace("\n", "\n     "))
    expected_code = 0 if all(EXPECT[k][0] for k in paths) else 1
    if code != expected_code:
        failures += 1
        print(f"FAIL validator exit code {code}, expected {expected_code}")
    print(f"{len(paths) - failures}/{len(paths)} fixture checks as expected (validator exit code {code})")
    return failures


if __name__ == "__main__":
    written = build_all()
    for k, p in written.items():
        print("wrote", p)
    if "--check" in sys.argv:
        sys.exit(1 if check(written) else 0)
