"""Cross-checks against the REAL code (optional; skipped when the JDK / jars are missing):

* Litematica 0.29.1 + malilib classes decode our .litematic files (DataFileUtils, SchematicMetadata,
  DataTypeUtils.readBlockStateFromTag, LitematicaBitArray) to exactly our blocks -- incl. 3/5/7-bit palettes
  whose entries span two longs.
* Minecraft 26.3 StructureTemplate.load reads our structure .nbt to exactly our blocks.
* blockwright.resolve output is a fixpoint of the game's own neighbour updates (Block.updateFromNeighbourShapes ->
  every BlockBehaviour.updateShape, plus LeavesBlock.updateDistance) in a fake level, on hand fixtures, the demo
  build and randomized fuzz fixtures.  Blocks the game would pop (canSurvive false -> air, e.g. a torch on
  nothing) are not resolve's concern and are only counted.

The Java harness sources are embedded below and compiled into <tempdir>/blockwright-tests/javatest on first use.
Run: ``python tests/test_core_gamecheck.py``.
"""
import hashlib
import os
import random
import re
import subprocess
import tempfile
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from blockwright import litematic as L, registry as R, structure_nbt as S  # noqa: E402
from blockwright.resolve import resolve  # noqa: E402

import pytest  # noqa: E402

from blockwright import validator  # noqa: E402

# JDK + jars come from `python -m blockwright setup --java <JDK>` (validator classpath); skipped when not set up.
_OK, _MSG, _INFO = validator.status()
_JH = validator._java_home(_INFO) if _OK else None
JDK = (_JH / "bin") if _JH else Path("missing-jdk")
WORK = Path(tempfile.gettempdir()) / "blockwright-tests" / "javatest"
SEP = os.pathsep
pytestmark = pytest.mark.jdk

JAVA_SOURCES = {
    "LitematicCheck.java": r'''
import fi.dy.masa.litematica.schematic.SchematicMetadata;
import fi.dy.masa.litematica.schematic.container.LitematicaBitArray;
import fi.dy.masa.malilib.util.data.tag.CompoundData;
import fi.dy.masa.malilib.util.data.tag.ListData;
import fi.dy.masa.malilib.util.data.tag.LongArrayData;
import fi.dy.masa.malilib.util.data.tag.util.DataFileUtils;
import fi.dy.masa.malilib.util.data.tag.util.DataTypeUtils;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.SharedConstants;
import net.minecraft.core.BlockPos;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.Bootstrap;
import net.minecraft.world.level.block.state.BlockState;

public class LitematicCheck {
	public static void main(String[] args) throws Exception {
		SharedConstants.tryDetectVersion();
		Bootstrap.bootStrap();
		RegistryAccess reg = RegistryAccess.fromRegistryOfRegistries(BuiltInRegistries.REGISTRY);
		for (String file : args) {
			System.out.println("FILE " + file);
			CompoundData nbt = DataFileUtils.readCompoundDataFromNbtFile(Path.of(file));
			System.out.println("ROOT version=" + nbt.getIntOrDefault("Version", -1) + " isInt=" + nbt.contains("Version", 3)
				+ " dv=" + nbt.getIntOrDefault("MinecraftDataVersion", -1) + " sub=" + nbt.getIntOrDefault("SubVersion", -1));
			SchematicMetadata meta = new SchematicMetadata();
			meta.readData(nbt.getCompound("Metadata"));
			int[] prev = meta.getPreviewImagePixelData();
			System.out.println("META regions=" + meta.getRegionCount() + " volume=" + meta.getTotalVolume() + " blocks="
				+ meta.getTotalBlocks() + " size=" + meta.getEnclosingSize().getX() + "," + meta.getEnclosingSize().getY() + ","
				+ meta.getEnclosingSize().getZ() + " created=" + meta.getTimeCreated() + " preview=" + (prev == null ? 0 : prev.length));
			CompoundData regions = nbt.getCompound("Regions");
			for (String name : regions.getKeys()) {
				CompoundData r = regions.getCompound(name);
				BlockPos size = DataTypeUtils.readBlockPos(r.getCompound("Size"));
				ListData palette = r.getList("BlockStatePalette");
				long[] longs = ((LongArrayData) r.getData("BlockStates").orElseThrow()).getLongArray();
				int bits = Math.max(2, 32 - Integer.numberOfLeadingZeros(palette.size() - 1));
				List<BlockState> states = new ArrayList<>();
				for (int i = 0; i < palette.size(); i++) states.add(DataTypeUtils.readBlockStateFromTag(palette.getCompoundAt(i), reg));
				System.out.println("REGION bits=" + bits + " palette0air=" + states.get(0).isAir());
				int sx = size.getX(), sy = size.getY(), sz = size.getZ();
				LitematicaBitArray arr = new LitematicaBitArray(bits, (long) sx * sy * sz, longs);
				for (int y = 0; y < sy; y++) for (int z = 0; z < sz; z++) for (int x = 0; x < sx; x++) {
					BlockState st = states.get(arr.getAt((long) y * sx * sz + (long) z * sx + x));
					if (!st.isAir()) System.out.println("B " + x + " " + y + " " + z + " " + st);
				}
			}
		}
	}
}
''',
    "StructureCheck.java": r'''
import java.lang.reflect.Field;
import java.nio.file.Path;
import java.util.List;
import net.minecraft.SharedConstants;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtAccounter;
import net.minecraft.nbt.NbtIo;
import net.minecraft.server.Bootstrap;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;

public class StructureCheck {
	public static void main(String[] args) throws Exception {
		SharedConstants.tryDetectVersion();
		Bootstrap.bootStrap();
		for (String file : args) {
			System.out.println("FILE " + file);
			CompoundTag tag = NbtIo.readCompressed(Path.of(file), NbtAccounter.unlimitedHeap());
			StructureTemplate t = new StructureTemplate();
			t.load(BuiltInRegistries.BLOCK, tag);
			System.out.println("SIZE " + t.getSize().getX() + "," + t.getSize().getY() + "," + t.getSize().getZ());
			Field f = StructureTemplate.class.getDeclaredField("palettes");
			f.setAccessible(true);
			Object pal = ((List<?>) f.get(t)).get(0);
			for (Object o : (List<?>) pal.getClass().getMethod("blocks").invoke(pal)) {
				StructureTemplate.StructureBlockInfo i = (StructureTemplate.StructureBlockInfo) o;
				System.out.println("B " + i.pos().getX() + " " + i.pos().getY() + " " + i.pos().getZ() + " " + i.state());
			}
		}
	}
}
''',
    "ResolveCheck.java": r'''
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeSet;
import net.minecraft.SharedConstants;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.Bootstrap;
import net.minecraft.tags.TagKey;
import net.minecraft.tags.TagLoader;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LeavesBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.Property;

/** args: tags.json then block files ("x y z state" lines). Prints DIFF lines (game update result != input). */
public class ResolveCheck {
	static Map<BlockPos, BlockState> W = new HashMap<>();
	static final TreeSet<String> unhandled = new TreeSet<>();
	static final RandomSource RNG = RandomSource.create(0);

	@SuppressWarnings({"unchecked", "rawtypes"})
	static BlockState parse(String s) {
		String id = s.contains("[") ? s.substring(0, s.indexOf('[')) : s;
		Block b = BuiltInRegistries.BLOCK.getValue(Identifier.parse(id));
		BlockState st = b.defaultBlockState();
		if (s.contains("[")) {
			for (String kv : s.substring(s.indexOf('[') + 1, s.length() - 1).split(",")) {
				String[] p = kv.split("=");
				Property prop = b.getStateDefinition().getProperty(p[0]);
				st = st.setValue(prop, (Comparable) prop.getValue(p[1]).orElseThrow());
			}
		}
		return st;
	}

	@SuppressWarnings({"unchecked", "rawtypes"})
	static String str(BlockState s) {
		StringBuilder sb = new StringBuilder(BuiltInRegistries.BLOCK.getKey(s.getBlock()).toString());
		if (!s.getProperties().isEmpty()) {
			sb.append('[');
			boolean first = true;
			for (Property p : s.getProperties()) {
				if (!first) sb.append(',');
				first = false;
				sb.append(p.getName()).append('=').append(p.getName((Comparable) s.getValue(p)));
			}
			sb.append(']');
		}
		return sb.toString();
	}

	public static void main(String[] args) throws Exception {
		SharedConstants.tryDetectVersion();
		Bootstrap.bootStrap();
		JsonObject tags = JsonParser.parseString(Files.readString(Path.of(args[0]))).getAsJsonObject().getAsJsonObject("tags");
		Map<TagKey<Block>, List<Holder<Block>>> map = new HashMap<>();
		for (String tag : tags.keySet()) {
			List<Holder<Block>> hs = new ArrayList<>();
			tags.getAsJsonArray(tag).forEach(e -> hs.add(BuiltInRegistries.BLOCK.get(Identifier.parse(e.getAsString())).orElseThrow()));
			map.put(TagKey.create(Registries.BLOCK, Identifier.parse(tag)), hs);
		}
		BuiltInRegistries.BLOCK.prepareTagReload(new TagLoader.LoadResult<>(Registries.BLOCK, map)).apply();
		InvocationHandler h = (proxy, m, a) -> {
			switch (m.getName()) {
				case "getBlockState": return W.getOrDefault((BlockPos) a[0], Blocks.AIR.defaultBlockState());
				case "getFluidState": return W.getOrDefault((BlockPos) a[0], Blocks.AIR.defaultBlockState()).getFluidState();
				case "getRandom": return RNG;
				case "scheduleTick": return null;
				case "isClientSide": return false;
				case "getMaxY": return 319;
				case "getMinY": return -64;
				case "getHeight": return 384;
				case "getRawBrightness": case "getMaxLocalRawBrightness": return 15;   // crops: full light, no light engine
				case "hashCode": return 1;
				case "equals": return proxy == a[0];
				case "toString": return "FakeLevel";
			}
			if (m.isDefault()) return InvocationHandler.invokeDefault(proxy, m, a);
			unhandled.add(m.getDeclaringClass().getSimpleName() + "." + m.getName());
			Class<?> r = m.getReturnType();
			if (r == boolean.class) return false;
			if (r == int.class) return 0;
			return null;
		};
		LevelAccessor level = (LevelAccessor) Proxy.newProxyInstance(ResolveCheck.class.getClassLoader(), new Class<?>[]{LevelAccessor.class}, h);
		Method updateDistance = LeavesBlock.class.getDeclaredMethod("updateDistance", BlockState.class, LevelAccessor.class, BlockPos.class);
		updateDistance.setAccessible(true);
		for (int f = 1; f < args.length; f++) {
			W = new HashMap<>();
			for (String line : Files.readAllLines(Path.of(args[f]))) {
				if (line.isBlank()) continue;
				String[] t = line.trim().split(" ", 4);
				W.put(new BlockPos(Integer.parseInt(t[0]), Integer.parseInt(t[1]), Integer.parseInt(t[2])), parse(t[3]));
			}
			System.out.println("FILE " + args[f]);
			for (Map.Entry<BlockPos, BlockState> e : W.entrySet()) {
				BlockPos pos = e.getKey();
				BlockState old = e.getValue();
				BlockState now = Block.updateFromNeighbourShapes(old, level, pos);
				if (now.getBlock() instanceof LeavesBlock) now = (BlockState) updateDistance.invoke(null, now, level, pos);
				if (now != old) System.out.println("DIFF " + pos.getX() + " " + pos.getY() + " " + pos.getZ() + " " + str(old) + " -> " + str(now));
			}
		}
		for (String u : unhandled) System.out.println("UNHANDLED " + u);
	}
}
''',
    "RotDump.java": r'''
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import net.minecraft.SharedConstants;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.Bootstrap;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.Property;

/** args: out.tsv. One line per block state: state, rotate(CW90, CW180, CCW90), mirror(FRONT_BACK, LEFT_RIGHT). */
public class RotDump {
	@SuppressWarnings({"unchecked", "rawtypes"})
	static String str(BlockState s) {
		StringBuilder sb = new StringBuilder(BuiltInRegistries.BLOCK.getKey(s.getBlock()).toString());
		if (!s.getProperties().isEmpty()) {
			sb.append('[');
			boolean first = true;
			for (Property p : s.getProperties()) {
				if (!first) sb.append(',');
				first = false;
				sb.append(p.getName()).append('=').append(p.getName((Comparable) s.getValue(p)));
			}
			sb.append(']');
		}
		return sb.toString();
	}

	public static void main(String[] args) throws Exception {
		SharedConstants.tryDetectVersion();
		Bootstrap.bootStrap();
		try (PrintWriter w = new PrintWriter(Files.newBufferedWriter(Path.of(args[0])))) {
			for (Block b : BuiltInRegistries.BLOCK) {
				for (BlockState s : b.getStateDefinition().getPossibleStates()) {
					w.println(str(s) + "\t" + str(s.rotate(Rotation.CLOCKWISE_90)) + "\t" + str(s.rotate(Rotation.CLOCKWISE_180)) + "\t"
						+ str(s.rotate(Rotation.COUNTERCLOCKWISE_90)) + "\t" + str(s.mirror(Mirror.FRONT_BACK)) + "\t"
						+ str(s.mirror(Mirror.LEFT_RIGHT)));
				}
			}
		}
	}
}
''',
    "ClassDump.java": r'''
import net.minecraft.SharedConstants;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.Bootstrap;
import net.minecraft.world.level.block.Block;

/** Prints "CLS <block id> <class> <superclass> ..." for every registered block. */
public class ClassDump {
	public static void main(String[] args) {
		SharedConstants.tryDetectVersion();
		Bootstrap.bootStrap();
		for (Block b : BuiltInRegistries.BLOCK) {
			StringBuilder sb = new StringBuilder(BuiltInRegistries.BLOCK.getKey(b).toString());
			for (Class<?> c = b.getClass(); c != null && c != Object.class; c = c.getSuperclass()) sb.append(' ').append(c.getSimpleName());
			System.out.println("CLS " + sb);
		}
	}
}
''',
}

_STATE_RE = re.compile(r"Block\{([^}]*)\}(?:\[(.*)\])?")


def available() -> bool:
    if not (_OK and _JH):
        pytest.skip(f"validator / JDK not set up: {_MSG}")
    return True


def _cp():
    return SEP.join(validator._cp(_INFO))


def compile_harness():
    WORK.mkdir(parents=True, exist_ok=True)
    stamp = WORK / ".compiled"
    digest = hashlib.sha1(repr(sorted(JAVA_SOURCES.items())).encode()).hexdigest()
    if stamp.exists() and all((WORK / n.replace(".java", ".class")).exists() for n in JAVA_SOURCES):
        if stamp.read_text() == digest:
            return
    for name, src in JAVA_SOURCES.items():
        (WORK / name).write_text(src, encoding="utf-8")
    r = subprocess.run([str(JDK / "javac"), "-nowarn", "-cp", _cp(), "-d", str(WORK)] + [str(WORK / n) for n in JAVA_SOURCES],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("javac failed:\n" + r.stderr[-3000:])
    stamp.write_text(digest)


def run_java(main, args):
    compile_harness()
    r = subprocess.run([str(JDK / "java"), "-cp", str(WORK) + SEP + _cp(), main] + [str(a) for a in args],
                       capture_output=True, text=True, cwd=WORK)
    lines = [re.sub(r"^\[[^\]]*\] \[[^\]]*\]: \[STDOUT\]: ", "", ln) for ln in r.stdout.splitlines()]
    if r.returncode != 0:
        raise RuntimeError(f"{main} failed ({r.returncode}):\n" + r.stderr[-3000:])
    return lines


def _state(txt):
    m = _STATE_RE.match(txt)
    props = dict(kv.split("=") for kv in m.group(2).split(",")) if m.group(2) else {}
    return R.make_state(m.group(1), props)


def _per_file(lines):
    out, cur = {}, None
    for ln in lines:
        if ln.startswith("FILE "):
            cur = ln[5:]
            out[cur] = []
        elif cur is not None:
            out[cur].append(ln)
    return out


def _random_blocks(seed, palette_size, n=(9, 6, 8), density=0.6):
    rnd = random.Random(seed)
    pool = [s for s in (R.make_state(b) for b in R.all_blocks()) if not R.is_air(s)]
    rnd.shuffle(pool)
    pool = pool[: palette_size - 1]
    blocks = {}
    for x in range(n[0]):
        for y in range(n[1]):
            for z in range(n[2]):
                if rnd.random() < density:
                    blocks[(x, y, z)] = rnd.choice(pool)
    for i, s in enumerate(pool):               # make sure every palette entry is used
        blocks[(i % n[0], 0, (i // n[0]) % n[2])] = s
    return blocks, n


# ---------------------------------------------------------------------------------------------------- tests
def test_litematica_decodes_our_files():
    if not available():
        print("skip: JDK / Litematica jars not found")
        return
    d = WORK / "files"
    d.mkdir(parents=True, exist_ok=True)
    cases = {}
    for seed, pal in ((1, 3), (2, 7), (3, 20), (4, 100), (5, 300)):      # 2, 3, 5, 7, 9 bits
        blocks, size = _random_blocks(seed, pal)
        p = d / f"lit_{pal}.litematic"
        argb = [(0xFF << 24) | (i * 997 & 0xFFFFFF) for i in range(120 * 120)] if seed == 4 else None
        L.write_litematic(p, blocks, size, name=f"P{pal}", author="t", ground=1, time_ms=777, preview_argb=argb)
        cases[str(p.resolve())] = (blocks, size, L.bits_for(len(set(blocks.values())) + 1), argb)
    out = _per_file(run_java("LitematicCheck", list(cases)))
    assert set(out) == set(cases), out.keys()
    for f, lines in out.items():
        blocks, size, bits, argb = cases[f]
        jb = {}
        for ln in lines:
            if ln.startswith("B "):
                _, x, y, z, st = ln.split(" ", 4)
                jb[(int(x), int(y), int(z))] = _state(st)
        assert jb == blocks, f
        root = next(ln for ln in lines if ln.startswith("ROOT"))
        meta = next(ln for ln in lines if ln.startswith("META"))
        reg = next(ln for ln in lines if ln.startswith("REGION"))
        assert root == "ROOT version=7 isInt=true dv=5023 sub=1", root
        assert f"blocks={len(blocks)}" in meta and f"size={size[0]},{size[1]},{size[2]}" in meta and "created=777" in meta
        assert f"preview={len(argb) if argb else 0}" in meta
        assert reg == f"REGION bits={bits} palette0air=true", (reg, bits)


def test_game_loads_structure_nbt():
    if not available():
        print("skip: JDK / jars not found")
        return
    d = WORK / "files"
    d.mkdir(parents=True, exist_ok=True)
    blocks, size = _random_blocks(11, 60)
    p = d / "s.nbt"
    S.write_structure(p, blocks, size)
    out = _per_file(run_java("StructureCheck", [p.resolve()]))
    lines = next(iter(out.values()))
    assert lines[0] == f"SIZE {size[0]},{size[1]},{size[2]}"
    jb = {}
    for ln in lines[1:]:
        _, x, y, z, st = ln.split(" ", 4)
        jb[(int(x), int(y), int(z))] = _state(st)
    assert jb == blocks


FUZZ_POOL = [
    "oak_stairs[facing={d},half={h}]", "cobblestone_stairs[facing={d},half={h}]", "oak_fence", "nether_brick_fence",
    "spruce_fence", "oak_fence_gate[facing={d},open={b}]", "cobblestone_wall", "mossy_stone_brick_wall", "glass_pane",
    "iron_bars", "light_blue_stained_glass_pane", "copper_bars", "stone", "oak_planks", "glass", "oak_leaves", "oak_log",
    "stone_slab[type={t}]", "red_mushroom_block", "mushroom_stem", "grass_block", "podzol", "snow", "hay_block",
    "campfire", "lantern", "torch", "vine", "vine[north={b},east={b},south={b},west={b},up={b}]", "pumpkin",
    "jungle_leaves", "spruce_trapdoor[facing={d},half={h},open={b}]", "oak_shelf", "chest", "white_carpet",
    "snow_block", "barrier", "andesite_wall", "oak_pressure_plate", "iron_chain", "hopper", "end_rod", "scaffolding",
    # review additions: chest pairing, growing plants, hanging moss, authored mushroom faces
    "chest[facing={d},type=left]", "chest[facing={d},type=right]", "chest[facing={d}]", "trapped_chest[facing={d},type=left]",
    "copper_chest[facing={d},type=right]", "exposed_copper_chest[facing={d}]", "cave_vines[berries={b}]",
    "cave_vines_plant[berries={b}]", "kelp", "kelp_plant", "weeping_vines", "weeping_vines_plant", "twisting_vines",
    "twisting_vines_plant", "pale_hanging_moss[tip={b}]",
    "brown_mushroom_block[north={b},east={b},south={b},west={b},up={b},down={b}]",
]


def _fuzz(seed, n=7, density=0.6):
    rnd = random.Random(seed)
    blocks = {}
    for x in range(n):
        for y in range(n):
            for z in range(n):
                if rnd.random() < density:
                    t = rnd.choice(FUZZ_POOL)
                    s = t.replace("{d}", rnd.choice(["north", "south", "east", "west"])).replace(
                        "{h}", rnd.choice(["top", "bottom"])).replace("{t}", rnd.choice(["top", "bottom", "double"]))
                    while "{b}" in s:
                        s = s.replace("{b}", rnd.choice(["true", "false"]), 1)
                    blocks[(x, y, z)] = R.parse_state(s)
    return blocks


def test_resolve_is_a_fixpoint_of_game_updates():
    if not available():
        print("skip: JDK / jars not found")
        return
    d = WORK / "files"
    d.mkdir(parents=True, exist_ok=True)
    fixtures = {}
    for seed in range(16):
        fixtures[f"fuzz{seed}"] = resolve(_fuzz(seed))[0]
    sys.path.insert(0, str(ROOT / "examples" / "builds"))
    import importlib
    demo = importlib.import_module("b00_demo")
    fixtures["demo"] = demo.b.structure()[0]
    ring = {}
    for x in range(3):
        ring[(x, 0, 0)] = R.parse_state("spruce_stairs[facing=south]")
        ring[(x, 0, 2)] = R.parse_state("spruce_stairs[facing=north]")
    ring[(0, 0, 1)] = R.parse_state("spruce_stairs[facing=east]")
    ring[(2, 0, 1)] = R.parse_state("spruce_stairs[facing=west]")
    fixtures["ring"] = resolve(ring)[0]
    # every resolved output of the hand-written rule fixtures in test_core_resolve.py
    for i, blocks in enumerate(_resolve_unit_outputs()):
        fixtures[f"unit{i:03d}"] = blocks
    paths = {}
    for name, blocks in fixtures.items():
        p = d / f"rc_{name}.txt"
        p.write_text("\n".join(f"{x} {y} {z} {s}" for (x, y, z), s in sorted(blocks.items())))
        paths[str(p.resolve())] = name
    lines = run_java("ResolveCheck", [R.TAGS_JSON] + list(paths))
    assert not [ln for ln in lines if ln.startswith("UNHANDLED")], lines
    out = _per_file(lines)
    total_pops = 0
    for f, ls in out.items():
        diffs = [ln for ln in ls if ln.startswith("DIFF")]
        real = [ln for ln in diffs if not ln.endswith("-> minecraft:air")]
        total_pops += len(diffs) - len(real)
        assert not real, (paths[f], real[:10])
        if paths[f] in ("demo", "ring"):
            assert not diffs, (paths[f], diffs[:5])
    print(f"      resolve == game updates on {len(out)} fixtures ({sum(len(b) for b in fixtures.values())} blocks); "
          f"{total_pops} unsupported decor blocks would pop (not a resolve concern)")


def _resolve_unit_outputs():
    """Run tests/test_core_resolve.py with resolve() wrapped, returning every resolved block dict it produced."""
    sys.path.insert(0, str(ROOT / "tests"))
    import importlib
    tr = importlib.import_module("test_core_resolve")
    captured, orig = [], tr.resolve

    def spy(blocks, *a, **kw):
        r = orig(blocks, *a, **kw)
        if r[0]:
            captured.append(dict(r[0]))
        return r

    tr.resolve = spy
    try:
        for name in sorted(k for k in vars(tr) if k.startswith("test_")):
            getattr(tr, name)()
    finally:
        tr.resolve = orig
    return captured


# The only places where blockwright.rotate deliberately differs from BlockState.rotate/mirror (all geometric fixes of vanilla
# shortcuts): class -> property names allowed to differ.  Fire/chorus side flags are not rotated by vanilla at all;
# vanilla's stair/chest/shelf mirrors keep the handedness in some orientations; anvils are not mirrored by vanilla.
_ROT_ALLOWED = {"FireBlock": {"north", "east", "south", "west"}, "ChorusPlantBlock": {"north", "east", "south", "west"}}
_MIRROR_ALLOWED = {**_ROT_ALLOWED, "StairBlock": {"shape"}, "ChestBlock": {"type"}, "ShelfBlock": {"side_chain"},
                   "AnvilBlock": {"facing"}}


def test_class_hierarchy_matches_game():
    """blockwright.registry.class_chain (parsed from the decompiled source) == the real runtime class chain of every block."""
    if not available():
        print("skip: JDK / jars not found")
        return
    lines = [ln[4:].split() for ln in run_java("ClassDump", []) if ln.startswith("CLS ")]
    assert len(lines) == len(R.all_blocks()), (len(lines), len(R.all_blocks()))
    bad = [(bid, R.class_chain(bid), tuple(chain)) for bid, *chain in lines if R.class_chain(bid) != tuple(chain)]
    assert not bad, bad[:5]


def test_rotate_mirror_match_game_for_every_state():
    if not available():
        print("skip: JDK / jars not found")
        return
    from blockwright.rotate import mirror_state, rotate_state
    out = WORK / "files" / "rotdump.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    run_java("RotDump", [out.resolve()])
    n, deviations = 0, {}
    for line in out.read_text(encoding="utf-8").splitlines():
        s, *game = line.split("\t")
        s = R.parse_state(s)
        ours = [rotate_state(s, 1), rotate_state(s, 2), rotate_state(s, 3), mirror_state(s, "x"), mirror_state(s, "z")]
        for i, (a, g) in enumerate(zip(ours, game)):
            g = R.parse_state(g)
            if a == g:
                continue
            assert R.block_id(a) == R.block_id(g), (s, a, g)
            changed = {k for k, v in R.props(a).items() if R.props(g)[k] != v}
            allowed = _ROT_ALLOWED if i < 3 else _MIRROR_ALLOWED
            ok = [c for c in R.class_chain(s) if c in allowed and changed <= allowed[c]]
            assert ok, f"{['cw90', 'cw180', 'ccw90', 'mirror_x', 'mirror_z'][i]} {s}: ours {a} != game {g}"
            deviations[ok[0]] = deviations.get(ok[0], 0) + 1
        n += 1
    assert n > 30000, n
    print(f"      rotate/mirror == game on {n} states; deliberate geometric deviations: {deviations}")


def run_all(ns):
    fails = 0
    for name in sorted(k for k in ns if k.startswith("test_") and callable(ns[k])):
        try:
            ns[name]()
            print(f"ok    {name}")
        except Exception:
            fails += 1
            print(f"FAIL  {name}")
            traceback.print_exc()
    print(f"{'FAILED' if fails else 'PASSED'}: {fails} failure(s)")
    return fails


if __name__ == "__main__":
    sys.exit(1 if run_all(dict(globals())) else 0)
