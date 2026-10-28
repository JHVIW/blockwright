import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import fi.dy.masa.litematica.schematic.LitematicaSchematic;
import fi.dy.masa.litematica.schematic.SchematicMetadata;
import fi.dy.masa.litematica.schematic.container.LitematicaBlockStateContainer;
import fi.dy.masa.litematica.util.FileType;
import fi.dy.masa.litematica.world.SchematicWorldHandler;
import fi.dy.masa.malilib.gui.Message;
import fi.dy.masa.malilib.gui.interfaces.IMessageConsumer;
import java.io.DataInputStream;
import java.io.InputStream;
import java.lang.reflect.Field;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.zip.GZIPInputStream;
import net.minecraft.SharedConstants;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.core.BlockPos;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.Vec3i;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.IntArrayTag;
import net.minecraft.nbt.IntTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.LongArrayTag;
import net.minecraft.nbt.LongTag;
import net.minecraft.nbt.NbtAccounter;
import net.minecraft.nbt.NbtIo;
import net.minecraft.nbt.StringTag;
import net.minecraft.nbt.Tag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.Bootstrap;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.Property;

/**
 * Validates .litematic files for Minecraft 26.3 + Litematica 0.29.1. See docs/litematic-format.md.
 *
 * Phase 1 (MC-native, independent of Litematica): reads the file with Minecraft's own NbtIo, checks every tag name/type
 * that Litematica reads, decodes the packed BlockStates with an independent bit-by-bit decoder, parses every palette
 * entry STRICTLY against the live 26.3 block registry (after Bootstrap.bootStrap()), counts blocks and compares the
 * Metadata counters.
 *
 * Phase 2 (Litematica's own reader, headless): loads the same file through LitematicaSchematic.createFromFile (the
 * method the in-game "Load Schematic" button calls), then compares every cell of every region container with the
 * phase-1 decode, plus metadata / tile entity / entity / tick counts. Litematica's GUI messages (errors/warnings it would
 * show the player) are captured and reported.
 *
 * Usage: LitematicValidate [--lenient] [--no-litematica] [-v] [--json out.json] file.litematic...
 * Exit code: 0 = all files valid, 1 = at least one error, 2 = usage / setup problem.
 */
public class LitematicValidate {
	static final String[] TAG_NAMES = {"End", "Byte", "Short", "Int", "Long", "Float", "Double", "ByteArray", "String", "List",
		"Compound", "IntArray", "LongArray"};
	static final int INT = 3, LONG = 4, DOUBLE = 6, STRING = 8, LIST = 9, COMPOUND = 10, INT_ARRAY = 11, LONG_ARRAY = 12;

	/** Captured before Bootstrap.bootStrap(), which redirects System.out/err into the logger. */
	static final java.io.PrintStream OUT = System.out;

	static boolean lenient = false;
	static boolean runLitematica = true;
	static boolean verbose = false;
	static int currentDataVersion;

	// ------------------------------------------------------------------------------------------------ report

	static final class Report {
		final Path file;
		final List<String> errors = new ArrayList<>();
		final List<String> warnings = new ArrayList<>();
		final List<String> infos = new ArrayList<>();
		final JsonObject json = new JsonObject();
		String litematicaSummary;
		int nErrors, nWarnings;
		/** Repetitive messages (same text modulo numbers) are printed 3 times, then only counted. */
		final Map<String, Integer> patternCount = new HashMap<>();
		final Map<String, Integer> suppressed = new LinkedHashMap<>();

		Report(Path file) {
			this.file = file;
		}

		private void add(List<String> list, String level, String s) {
			String pattern = level + " " + s.replaceAll("\\d+", "#");
			int n = this.patternCount.merge(pattern, 1, Integer::sum);
			if (n <= 3) list.add(s);
			else this.suppressed.merge(pattern, 1, Integer::sum);
		}

		void err(String s) {
			this.nErrors++;
			this.add(this.errors, "ERROR", s);
		}

		void warn(String s) {
			this.nWarnings++;
			this.add(this.warnings, "WARN ", s);
		}

		/** An error in strict mode, a warning with --lenient. */
		void strict(String s) {
			if (lenient) this.warn(s);
			else this.err(s);
		}

		void info(String s) {
			this.infos.add(s);
		}
	}

	static final class Region {
		String name;
		int[] pos = new int[3];
		int[] size = new int[3];
		int dx, dy, dz;
		long volume;
		int[] min = new int[3];
		int[] max = new int[3];
		int paletteSize;
		BlockState[] palette;       // null entry = palette entry that failed strict parsing
		int bits;
		long[] longs;
		int[] idx;                  // decoded palette index per cell (index = (y*dz + z)*dx + x), -1 = undecodable
		boolean decoded;
		int nonAir;
		int tileEntities, entities, blockTicks, fluidTicks;
		Map<String, Integer> counts = new TreeMap<>();
	}

	// ------------------------------------------------------------------------------------------------ main

	public static void main(String[] args) throws Exception {
		List<Path> files = new ArrayList<>();
		Path jsonOut = null;
		for (int i = 0; i < args.length; i++) {
			String a = args[i];
			switch (a) {
				case "--lenient" -> lenient = true;
				case "--no-litematica" -> runLitematica = false;
				case "-v", "--verbose" -> verbose = true;
				case "--json" -> jsonOut = Path.of(args[++i]);
				case "-h", "--help" -> {
					usage();
					System.exit(2);
				}
				default -> {
					if (a.startsWith("-")) {
						System.err.println("unknown option " + a);
						usage();
						System.exit(2);
					}
					files.add(Path.of(a));
				}
			}
		}
		if (files.isEmpty()) {
			usage();
			System.exit(2);
		}

		SharedConstants.tryDetectVersion();
		Bootstrap.bootStrap();
		currentDataVersion = SharedConstants.getCurrentVersion().dataVersion().version();

		String litInitError = null;
		if (runLitematica) {
			litInitError = initLitematicaHeadless();
			if (litInitError != null) {
				OUT.println("SETUP ERROR: could not initialise Litematica headless: " + litInitError);
			}
		}

		int failed = 0;
		JsonArray all = new JsonArray();
		for (Path f : files) {
			Report r = new Report(f);
			Map<String, Region> regions = null;
			try {
				regions = nativeCheck(f, r);
			} catch (Throwable t) {
				r.err("could not read file with Minecraft NbtIo: " + t);
			}
			if (runLitematica) {
				if (litInitError != null) {
					r.err("Litematica headless load not run: " + litInitError);
				} else {
					try {
						litematicaCheck(f, regions, r);
					} catch (Throwable t) {
						r.err("litematica: load threw " + t + at(t));
					}
				}
			}
			print(r, regions);
			if (r.nErrors > 0) failed++;
			r.json.addProperty("file", f.toString());
			r.json.addProperty("ok", r.nErrors == 0);
			r.json.addProperty("errorCount", r.nErrors);
			r.json.addProperty("warningCount", r.nWarnings);
			r.json.add("errors", arr(r.errors));
			r.json.add("warnings", arr(r.warnings));
			if (r.litematicaSummary != null) r.json.addProperty("litematicaSummary", r.litematicaSummary);
			all.add(r.json);
		}
		if (files.size() > 1) {
			OUT.println(String.format("%d file(s): %d passed, %d failed", files.size(), files.size() - failed, failed));
		}
		if (jsonOut != null) {
			Files.writeString(jsonOut, new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create().toJson(all));
		}
		System.exit(litInitError != null ? 2 : failed > 0 ? 1 : 0);
	}

	static void usage() {
		System.err.println("usage: LitematicValidate [--lenient] [--no-litematica] [-v] [--json out.json] file.litematic...");
		System.err.println("  --lenient        version/type deviations that Litematica tolerates become warnings instead of errors");
		System.err.println("  --no-litematica  skip the headless load through Litematica's own reader");
		System.err.println("  -v               print palette / block counts / infos");
	}

	static JsonArray arr(List<String> l) {
		JsonArray a = new JsonArray();
		l.forEach(a::add);
		return a;
	}

	static String at(Throwable t) {
		StackTraceElement[] st = t.getStackTrace();
		StringBuilder sb = new StringBuilder();
		for (int i = 0; i < Math.min(Integer.getInteger("litvalidate.frames", 4), st.length); i++) sb.append("\n      at ").append(st[i]);
		return sb.toString();
	}

	static void print(Report r, Map<String, Region> regions) {
		OUT.println("== " + r.file);
		if (regions != null) {
			for (Region g : regions.values()) {
				OUT.println(String.format("  region '%s': Position=(%d,%d,%d) Size=(%d,%d,%d) -> min=(%d,%d,%d) max=(%d,%d,%d) "
						+ "palette=%d bits=%d longs=%d nonAir=%d TE=%d entities=%d ticks=%d/%d",
					g.name, g.pos[0], g.pos[1], g.pos[2], g.size[0], g.size[1], g.size[2], g.min[0], g.min[1], g.min[2], g.max[0], g.max[1],
					g.max[2], g.paletteSize, g.bits, g.longs == null ? -1 : g.longs.length, g.nonAir, g.tileEntities, g.entities, g.blockTicks,
					g.fluidTicks));
				if (verbose) {
					for (int i = 0; i < g.paletteSize; i++) {
						OUT.println("      palette[" + i + "] = " + (g.palette[i] == null ? "<invalid>" : stateString(g.palette[i])));
					}
					for (Map.Entry<String, Integer> e : g.counts.entrySet()) {
						OUT.println(String.format("      %6d x %s", e.getValue(), e.getKey()));
					}
				}
			}
		}
		if (r.litematicaSummary != null) OUT.println("  " + r.litematicaSummary);
		if (verbose) r.infos.forEach(s -> OUT.println("  info  " + s));
		r.warnings.forEach(s -> OUT.println("  WARN  " + s));
		r.errors.forEach(s -> OUT.println("  ERROR " + s));
		r.suppressed.forEach((pattern, n) -> OUT.println("  ... " + n + " more like: " + pattern));
		OUT.println(String.format("  %s (%d error(s), %d warning(s))", r.nErrors == 0 ? "PASS" : "FAIL", r.nErrors, r.nWarnings));
	}

	// ------------------------------------------------------------------------------------------------ phase 1: MC-native

	static String typeName(Tag t) {
		return t == null ? "missing" : TAG_NAMES[t.getId()];
	}

	/** Returns the tag if it exists with exactly the given type, else reports and returns null. */
	static Tag need(CompoundTag c, String key, int type, String where, Report r, boolean required) {
		Tag t = c.get(key);
		if (t == null) {
			if (required) r.err(where + key + " is missing (expected " + TAG_NAMES[type] + ")");
			return null;
		}
		if (t.getId() != type) {
			r.err(where + key + " must be " + TAG_NAMES[type] + ", found " + typeName(t));
			return null;
		}
		return t;
	}

	static Integer needInt(CompoundTag c, String key, String where, Report r) {
		Tag t = need(c, key, INT, where, r, true);
		return t == null ? null : ((IntTag) t).value();
	}

	static int[] needXyz(CompoundTag c, String key, String where, Report r) {
		Tag t = need(c, key, COMPOUND, where, r, true);
		if (t == null) return null;
		CompoundTag v = (CompoundTag) t;
		Integer x = needInt(v, "x", where + key + ".", r), y = needInt(v, "y", where + key + ".", r), z = needInt(v, "z", where + key + ".", r);
		for (String k : v.keySet()) {
			if (!k.equals("x") && !k.equals("y") && !k.equals("z")) r.warn(where + key + " has unexpected key '" + k + "'");
		}
		return x == null || y == null || z == null ? null : new int[]{x, y, z};
	}

	static void unknownKeys(CompoundTag c, Set<String> known, String where, Report r) {
		for (String k : c.keySet()) {
			if (!known.contains(k)) r.warn(where + "unexpected key '" + k + "' (" + typeName(c.get(k)) + "), Litematica ignores it");
		}
	}

	static Map<String, Region> nativeCheck(Path f, Report r) throws Exception {
		// raw header: gzip magic, root tag type and root name
		byte[] magic = new byte[2];
		try (InputStream in = Files.newInputStream(f)) {
			if (in.read(magic) != 2) throw new java.io.EOFException("file shorter than 2 bytes");
		}
		boolean gz = (magic[0] & 0xff) == 0x1f && (magic[1] & 0xff) == 0x8b;
		if (!gz) r.strict("file is not gzip-compressed (Litematica writes gzip; it falls back to raw NBT on ZipException)");
		try (DataInputStream in = new DataInputStream(gz ? new GZIPInputStream(Files.newInputStream(f)) : Files.newInputStream(f))) {
			int type = in.readByte();
			if (type != COMPOUND) {
				r.err("root tag must be Compound, found type " + type);
				return null;
			}
			String rootName = in.readUTF();
			if (!rootName.isEmpty()) r.warn("root tag name is '" + rootName + "' (Litematica writes \"\"; it ignores the name)");
		}
		CompoundTag root;
		if (gz) {
			root = NbtIo.readCompressed(f, NbtAccounter.unlimitedHeap());
		} else {
			try (DataInputStream in = new DataInputStream(Files.newInputStream(f))) {
				root = NbtIo.read(in, NbtAccounter.unlimitedHeap());
			}
		}
		JsonObject jroot = new JsonObject();
		r.json.add("root", jroot);

		// ---- root
		unknownKeys(root, Set.of("MinecraftDataVersion", "Version", "SubVersion", "Metadata", "Regions"), "root: ", r);
		Tag dvTag = root.get("MinecraftDataVersion");
		if (dvTag == null) {
			r.err("MinecraftDataVersion is missing: Litematica then assumes datafixerDefaultSchema (1139 = MC 1.12), runs its 1.12->1.13 "
				+ "palette converter and the vanilla DataFixer 1139->current on every palette entry / TE / entity (states may be renamed or altered)");
		} else if (dvTag.getId() != INT) {
			r.strict("MinecraftDataVersion must be Int, found " + typeName(dvTag) + " (Litematica accepts any numeric here)");
		}
		int dv = dvTag != null && dvTag.asNumber().isPresent() ? dvTag.asNumber().get().intValue() : -1;
		jroot.addProperty("MinecraftDataVersion", dv);
		if (dvTag != null && dv != currentDataVersion) {
			String why = dv < currentDataVersion
				? "older than the running game (" + currentDataVersion + "): Litematica runs the vanilla DataFixer on palette/TEs/entities "
				+ "and its SchematicConverter post-process fixers (walls, redstone wire, beds, banners, flower pots, note blocks, signs, skulls)"
				: "newer than the running game (" + currentDataVersion + ")" + (dv - currentDataVersion > 100
				? ": Litematica shows 'newer_minecraft_version' warning" : ": no conversion, loaded as-is");
			if (dv < 1631 && dv > 0) {
				r.err("MinecraftDataVersion=" + dv + " < 1631: Litematica treats the palette as MC 1.12 and converts it");
			} else {
				r.strict("MinecraftDataVersion=" + dv + " is " + why);
			}
		}
		Tag vTag = root.get("Version");
		int version = -1;
		if (vTag == null || vTag.getId() != INT) {
			r.err("Version must be Int, found " + typeName(vTag) + " (Litematica: 'no_schematic_version_information', load fails)");
		} else {
			version = ((IntTag) vTag).value();
			if (version < 1 || version > 7) {
				r.err("Version=" + version + " not in 1..7: Litematica refuses to load ('unsupported_schematic_version')");
			} else if (version < 5) {
				r.err("Version=" + version + " < 5: Litematica converts the palette from MC 1.12 block ids");
			} else if (version != 7) {
				r.strict("Version=" + version + " (Litematica 0.29.1 writes 7; 5/6 still load)");
			}
		}
		jroot.addProperty("Version", version);
		Tag svTag = root.get("SubVersion");
		if (svTag == null || svTag.getId() != INT) {
			r.strict("SubVersion must be Int 1, found " + typeName(svTag) + " (Litematica writes it but never reads it)");
		} else if (((IntTag) svTag).value() != 1) {
			r.strict("SubVersion=" + ((IntTag) svTag).value() + " (Litematica 0.29.1 writes 1; it never reads it)");
		}

		// ---- regions (decoded before metadata so the counters can be compared)
		Map<String, Region> regions = new LinkedHashMap<>();
		Tag regsTag = need(root, "Regions", COMPOUND, "", r, true);
		if (regsTag != null) {
			CompoundTag regs = (CompoundTag) regsTag;
			if (regs.isEmpty()) r.err("Regions is empty");
			for (String name : regs.keySet()) {
				Tag t = regs.get(name);
				if (t.getId() != COMPOUND) {
					r.err("Regions." + name + " must be Compound, found " + typeName(t) + " (Litematica silently skips it)");
					continue;
				}
				Region g = regionCheck(name, (CompoundTag) t, version, r);
				if (g != null) regions.put(name, g);
			}
		}

		// ---- metadata
		Tag metaTag = need(root, "Metadata", COMPOUND, "", r, true);
		if (metaTag != null) {
			metadataCheck((CompoundTag) metaTag, regions, regsTag == null ? 0 : ((CompoundTag) regsTag).size(), r);
		}
		return regions;
	}

	static void metadataCheck(CompoundTag m, Map<String, Region> regions, int regionTagCount, Report r) {
		String w = "Metadata.";
		JsonObject jm = new JsonObject();
		r.json.add("metadata", jm);
		unknownKeys(m, Set.of("Name", "Author", "Description", "RegionCount", "TotalVolume", "TotalBlocks", "TimeCreated", "TimeModified",
			"EnclosingSize", "PreviewImageData"), w, r);
		for (String k : List.of("Name", "Author", "Description")) {
			Tag t = m.get(k);
			if (t == null || t.getId() != STRING) {
				r.strict(w + k + " must be String, found " + typeName(t) + " (Litematica then shows " + (k.equals("Description") ? "\"\"" : "\"?\"") + ")");
			} else {
				jm.addProperty(k, ((StringTag) t).value());
			}
		}
		Map<String, Integer> ints = new HashMap<>();
		for (String k : List.of("RegionCount", "TotalVolume", "TotalBlocks")) {
			Tag t = m.get(k);
			if (t == null || t.getId() != INT) {
				String effect = k.equals("RegionCount") ? "any numeric is accepted, missing = 0" : "only an Int is read; otherwise Litematica shows -1";
				r.strict(w + k + " must be Int, found " + typeName(t) + " (" + effect + ")");
			} else {
				ints.put(k, ((IntTag) t).value());
				jm.addProperty(k, ((IntTag) t).value());
			}
		}
		for (String k : List.of("TimeCreated", "TimeModified")) {
			Tag t = m.get(k);
			if (t == null || t.getId() != LONG) {
				r.strict(w + k + " must be Long (epoch millis), found " + typeName(t));
			} else if (((LongTag) t).value() <= 0) {
				r.warn(w + k + "=" + ((LongTag) t).value() + " (Litematica only writes it when > 0)");
			}
		}
		int[] encl = null;
		Tag es = m.get("EnclosingSize");
		if (es == null || es.getId() != COMPOUND) {
			r.strict(w + "EnclosingSize must be Compound{x,y,z Int}, found " + typeName(es) + " (Litematica then uses 0,0,0)");
		} else {
			encl = needXyz(m, "EnclosingSize", w, r);
		}
		Tag pv = m.get("PreviewImageData");
		if (pv != null) {
			if (pv.getId() != INT_ARRAY) {
				r.warn(w + "PreviewImageData must be IntArray, found " + typeName(pv) + " (ignored by Litematica)");
			} else {
				int n = ((IntArrayTag) pv).getAsIntArray().length;
				int side = (int) Math.sqrt(n);
				if (n == 0 || side * side != n) {
					r.warn(w + "PreviewImageData has " + n + " ints, not a non-empty perfect square: Litematica will not display it");
				} else {
					r.info(w + "PreviewImageData " + side + "x" + side + " ARGB (Litematica's own previews are 120x120)");
				}
			}
		}

		// ---- counters vs. the actual content
		if (ints.containsKey("RegionCount") && ints.get("RegionCount") != regionTagCount) {
			r.err(w + "RegionCount=" + ints.get("RegionCount") + " but Regions has " + regionTagCount + " entries");
		}
		long vol = 0, blocks = 0;
		boolean allDecoded = true;
		int[] lo = {Integer.MAX_VALUE, Integer.MAX_VALUE, Integer.MAX_VALUE}, hi = {Integer.MIN_VALUE, Integer.MIN_VALUE, Integer.MIN_VALUE};
		for (Region g : regions.values()) {
			vol += g.volume;
			blocks += g.nonAir;
			allDecoded &= g.decoded;
			for (int i = 0; i < 3; i++) {
				lo[i] = Math.min(lo[i], g.min[i]);
				hi[i] = Math.max(hi[i], g.max[i]);
			}
		}
		if (!regions.isEmpty()) {
			if (ints.containsKey("TotalVolume") && ints.get("TotalVolume") != vol) {
				r.err(w + "TotalVolume=" + ints.get("TotalVolume") + " but the regions' volume is " + vol);
			}
			if (allDecoded && ints.containsKey("TotalBlocks") && ints.get("TotalBlocks") != blocks) {
				r.err(w + "TotalBlocks=" + ints.get("TotalBlocks") + " but the regions contain " + blocks + " non-air blocks (BlockState.isAir() false)");
			}
			int[] want = {hi[0] - lo[0] + 1, hi[1] - lo[1] + 1, hi[2] - lo[2] + 1};
			if (encl != null && !Arrays.equals(encl, want)) {
				r.err(w + "EnclosingSize=" + Arrays.toString(encl) + " but the regions' enclosing box is " + Arrays.toString(want));
			}
			JsonObject jc = new JsonObject();
			jc.addProperty("volume", vol);
			jc.addProperty("nonAirBlocks", blocks);
			jc.addProperty("enclosingSize", Arrays.toString(want));
			r.json.add("computed", jc);
		}
	}

	static Region regionCheck(String name, CompoundTag t, int version, Report r) {
		String w = "region '" + name + "': ";
		Region g = new Region();
		g.name = name;
		unknownKeys(t, Set.of("Position", "Size", "BlockStatePalette", "BlockStates", "TileEntities", "Entities", "PendingBlockTicks",
			"PendingFluidTicks"), w, r);
		int[] pos = needXyz(t, "Position", w, r);
		int[] size = needXyz(t, "Size", w, r);
		if (pos == null || size == null) {
			r.err(w + "Position and Size must both be Compound{x,y,z Int}: otherwise Litematica silently drops the whole region");
			return null;
		}
		g.pos = pos;
		g.size = size;
		for (int i = 0; i < 3; i++) {
			if (size[i] == 0) {
				r.err(w + "Size has a 0 component (Litematica sizes are never 0: +n or -n)");
				return null;
			}
			int end = pos[i] + (size[i] > 0 ? size[i] - 1 : size[i] + 1);   // PositionUtils.getRelativeEndPositionFromAreaSize
			g.min[i] = Math.min(pos[i], end);
			g.max[i] = Math.max(pos[i], end);
		}
		if (size[0] < 0 || size[1] < 0 || size[2] < 0) {
			r.info(w + "negative Size: Position is the selection's corner 1, the block container starts at the min corner "
				+ Arrays.toString(g.min));
		}
		g.dx = Math.abs(size[0]);
		g.dy = Math.abs(size[1]);
		g.dz = Math.abs(size[2]);
		g.volume = (long) g.dx * g.dy * g.dz;

		// ---- palette
		Tag palTag = need(t, "BlockStatePalette", LIST, w, r, true);
		ListTag pal = palTag == null ? new ListTag() : (ListTag) palTag;
		g.paletteSize = pal.size();
		g.palette = new BlockState[g.paletteSize];
		if (g.paletteSize == 0) r.err(w + "BlockStatePalette is empty (index 0 must be minecraft:air)");
		Map<BlockState, Integer> seen = new HashMap<>();
		for (int i = 0; i < g.paletteSize; i++) {
			g.palette[i] = paletteEntry(pal.get(i), w + "palette[" + i + "] ", r);
			if (g.palette[i] != null) {
				Integer prev = seen.putIfAbsent(g.palette[i], i);
				if (prev != null) r.warn(w + "palette[" + i + "] duplicates palette[" + prev + "] (" + stateString(g.palette[i]) + ")");
			}
		}
		if (g.paletteSize > 0 && g.palette[0] != null && g.palette[0] != Blocks.AIR.defaultBlockState()) {
			r.err(w + "palette[0] must be minecraft:air, found " + stateString(g.palette[0]) + " (Litematica pre-seeds id 0 with air and "
				+ "appends a non-air palette[0] as a new id, shifting every index by one)");
		}

		// ---- block states
		g.bits = Math.max(2, 32 - Integer.numberOfLeadingZeros(Math.max(g.paletteSize, 1) - 1));
		Tag bsTag = t.get("BlockStates");
		if (bsTag == null || bsTag.getId() != LONG_ARRAY) {
			r.err(w + "BlockStates must be LongArray, found " + typeName(bsTag) + " (Litematica then creates NO block container for this region)");
		} else {
			g.longs = ((LongArrayTag) bsTag).getAsLongArray();
			long expected = (g.volume * g.bits + 63) / 64;
			if (g.longs.length < expected) {
				r.err(w + "BlockStates has " + g.longs.length + " longs, expected " + expected + " (= ceil(" + g.volume + " cells * " + g.bits
					+ " bits / 64)); Litematica loads it but throws ArrayIndexOutOfBounds when the missing cells are read");
			} else if (g.longs.length > expected) {
				r.warn(w + "BlockStates has " + g.longs.length + " longs, expected " + expected + " (extra longs are ignored)");
			}
			decode(g, w, r);
		}

		// ---- tile entities / entities / ticks
		if (version >= 2) {
			g.tileEntities = listCheck(t, "TileEntities", w, r, (c, where) -> tileEntityCheck(c, where, g, r));
			g.entities = listCheck(t, "Entities", w, r, (c, where) -> entityCheck(c, where, r));
		}
		if (version >= 3) g.blockTicks = listCheck(t, "PendingBlockTicks", w, r, (c, where) -> tickCheck(c, where, "Block", r));
		if (version >= 5) g.fluidTicks = listCheck(t, "PendingFluidTicks", w, r, (c, where) -> tickCheck(c, where, "Fluid", r));
		if (g.decoded) {
			int withBe = 0;
			for (int i = 0; i < g.idx.length; i++) {
				BlockState s = g.idx[i] >= 0 ? g.palette[g.idx[i]] : null;
				if (s != null && s.hasBlockEntity()) withBe++;
			}
			if (withBe > g.tileEntities) {
				r.info(w + (withBe - g.tileEntities) + " block(s) with a block entity have no TileEntities record; Litematica pastes them and "
					+ "the world creates a default (empty) block entity");
			}
		}
		return g;
	}

	interface ElementCheck {
		boolean check(CompoundTag c, String where);
	}

	static int listCheck(CompoundTag t, String key, String w, Report r, ElementCheck ec) {
		Tag lt = t.get(key);
		if (lt == null) {
			r.strict(w + key + " is missing (Litematica 0.29.1 always writes it, possibly empty; reading treats missing as empty)");
			return 0;
		}
		if (lt.getId() != LIST) {
			r.err(w + key + " must be List, found " + typeName(lt));
			return 0;
		}
		ListTag l = (ListTag) lt;
		int ok = 0;
		for (int i = 0; i < l.size(); i++) {
			Tag e = l.get(i);
			String where = w + key + "[" + i + "] ";
			if (e.getId() != COMPOUND) {
				r.err(where + "must be Compound, found " + typeName(e));
			} else if (ec.check((CompoundTag) e, where)) {
				ok++;
			}
		}
		return ok;
	}

	static boolean tileEntityCheck(CompoundTag c, String where, Region g, Report r) {
		Tag x = c.get("x"), y = c.get("y"), z = c.get("z");
		if (x == null || y == null || z == null || x.getId() != INT || y.getId() != INT || z.getId() != INT) {
			r.err(where + "needs Int x,y,z (container coordinates); Litematica drops entries without them");
			return false;
		}
		int px = ((IntTag) x).value(), py = ((IntTag) y).value(), pz = ((IntTag) z).value();
		if (px < 0 || py < 0 || pz < 0 || px >= g.dx || py >= g.dy || pz >= g.dz) {
			r.err(where + "position (" + px + "," + py + "," + pz + ") is outside the region container 0.." + (g.dx - 1) + ",0.." + (g.dy - 1)
				+ ",0.." + (g.dz - 1) + " (TileEntities x,y,z are relative to the region's min corner)");
			return false;
		}
		Tag id = c.get("id");
		BlockEntityType<?> type = null;
		if (id == null || id.getId() != STRING) {
			r.strict(where + "needs String id (block entity type; Litematica itself never reads it - the block creates the block entity "
				+ "and the NBT is loaded into it - but vanilla structure/other tools do)");
		} else {
			Identifier rl = Identifier.tryParse(((StringTag) id).value());
			type = rl == null ? null : BuiltInRegistries.BLOCK_ENTITY_TYPE.getValue(rl);
			if (type == null) r.strict(where + "unknown block entity type '" + ((StringTag) id).value() + "' in 26.3");
		}
		if (g.decoded) {
			int i = (py * g.dz + pz) * g.dx + px;
			BlockState s = g.idx[i] >= 0 ? g.palette[g.idx[i]] : null;
			if (s != null && !s.hasBlockEntity()) {
				r.warn(where + "is at (" + px + "," + py + "," + pz + ") = " + stateString(s) + ", which has no block entity (ignored on paste)");
			} else if (s != null && type != null && !type.isValid(s)) {
				r.warn(where + "type " + ((StringTag) id).value() + " is not valid for " + stateString(s));
			}
		}
		return true;
	}

	static boolean entityCheck(CompoundTag c, String where, Report r) {
		Tag id = c.get("id");
		if (id == null || id.getId() != STRING) {
			r.err(where + "needs String id");
		} else {
			Identifier rl = Identifier.tryParse(((StringTag) id).value());
			if (rl == null || !BuiltInRegistries.ENTITY_TYPE.containsKey(rl)) r.err(where + "unknown entity type '" + ((StringTag) id).value() + "'");
		}
		Tag pos = c.get("Pos");
		boolean ok = pos != null && pos.getId() == LIST && ((ListTag) pos).size() == 3;
		if (ok) {
			for (int i = 0; i < 3; i++) ok &= ((ListTag) pos).get(i).getId() == DOUBLE;
		}
		if (!ok) {
			r.err(where + "needs Pos: List of 3 Double (relative to the region Position); Litematica (Vec3.CODEC) falls back to 0,0,0");
			return true;
		}
		return true;
	}

	static boolean tickCheck(CompoundTag c, String where, String key, Report r) {
		Tag time = c.get("Time");
		if (time == null || time.getId() != INT) {
			r.err(where + "needs Int Time (delay in ticks); Litematica drops ticks without it");
			return false;
		}
		Tag id = c.get(key);
		Identifier rl = id != null && id.getId() == STRING ? Identifier.tryParse(((StringTag) id).value()) : null;
		boolean known = rl != null && (key.equals("Block") ? BuiltInRegistries.BLOCK.containsKey(rl) : BuiltInRegistries.FLUID.containsKey(rl));
		if (!known) {
			r.err(where + key + " must be the String id of a known " + key.toLowerCase() + ", found " + (id == null ? "nothing" : id.toString()));
			return false;
		}
		for (String k : List.of("x", "y", "z", "Priority")) {
			Tag v = c.get(k);
			if (v == null || v.getId() != INT) r.warn(where + k + " should be Int (Litematica defaults it to 0)");
		}
		Tag st = c.get("SubTick");
		if (st == null || st.getId() != LONG) r.warn(where + "SubTick should be Long (Litematica defaults it to 0)");
		return true;
	}

	/** Strict palette entry parse. Returns null (after reporting) if the entry is not exactly valid. */
	static BlockState paletteEntry(Tag e, String w, Report r) {
		if (e.getId() != COMPOUND) {
			r.err(w + "must be Compound, found " + typeName(e) + " (Litematica reads it as air)");
			return null;
		}
		CompoundTag c = (CompoundTag) e;
		for (String k : c.keySet()) {
			if (k.equals("id") || k.equals("properties")) {
				r.err(w + "has key '" + k + "': Litematica 0.29.1 prefers lowercase id/properties over Name/Properties when present; use Name/Properties only");
			} else if (!k.equals("Name") && !k.equals("Properties")) {
				r.warn(w + "unexpected key '" + k + "'");
			}
		}
		Tag nameTag = c.get("Name");
		if (nameTag == null || nameTag.getId() != STRING) {
			r.err(w + "Name must be String, found " + typeName(nameTag) + " (Litematica reads it as air)");
			return null;
		}
		String name = ((StringTag) nameTag).value();
		Identifier id = Identifier.tryParse(name);
		if (id == null) {
			r.err(w + "Name '" + name + "' is not a valid identifier (Litematica reads it as air)");
			return null;
		}
		if (!name.contains(":")) r.strict(w + "Name '" + name + "' has no namespace (write the canonical 'minecraft:" + name + "')");
		if (!BuiltInRegistries.BLOCK.containsKey(id)) {
			r.err(w + "unknown block '" + id + "' (not in the 26.3 registry; Litematica silently loads it as minecraft:air)");
			return null;
		}
		Block block = BuiltInRegistries.BLOCK.getValue(id);
		BlockState state = block.defaultBlockState();
		boolean ok = true;
		Tag propsTag = c.get("Properties");
		CompoundTag props = new CompoundTag();
		if (propsTag != null) {
			if (propsTag.getId() != COMPOUND) {
				r.err(w + "Properties must be Compound, found " + typeName(propsTag) + " (Litematica ignores it and uses defaults)");
				return null;
			}
			props = (CompoundTag) propsTag;
		}
		for (String key : props.keySet()) {
			Property<?> p = block.getStateDefinition().getProperty(key);
			if (p == null) {
				r.err(w + "unknown property '" + key + "' for " + id + " (valid: " + propNames(block) + "; Litematica silently ignores it)");
				ok = false;
				continue;
			}
			Tag v = props.get(key);
			if (v.getId() != STRING) {
				r.err(w + "property '" + key + "' of " + id + " must be a String, found " + typeName(v) + " (Litematica ignores it)");
				ok = false;
				continue;
			}
			String value = ((StringTag) v).value();
			if (p.getValue(value).isEmpty()) {
				r.err(w + "illegal value '" + value + "' for property '" + key + "' of " + id + " (legal: " + legalValues(p)
					+ "; Litematica silently uses the default '" + valueName(p, state.getValue(p)) + "')");
				ok = false;
				continue;
			}
			state = setValue(state, p, value);
		}
		List<String> missing = new ArrayList<>();
		for (Property<?> p : block.getStateDefinition().getProperties()) {
			if (!props.contains(p.getName())) missing.add(p.getName());
		}
		if (!missing.isEmpty()) {
			String msg = w + id + " has missing properties " + missing + " (canonical form lists all; Litematica fills defaults)";
			if (lenient) r.warn(msg);
			else {
				r.err(msg);
				ok = false;
			}
		}
		return ok ? state : null;
	}

	@SuppressWarnings({"unchecked", "rawtypes"})
	static BlockState setValue(BlockState s, Property p, String value) {
		return s.setValue(p, (Comparable) p.getValue(value).get());
	}

	@SuppressWarnings({"unchecked", "rawtypes"})
	static String valueName(Property p, Object v) {
		return p.getName((Comparable) v);
	}

	static String legalValues(Property<?> p) {
		List<String> l = new ArrayList<>();
		for (Object v : p.getPossibleValues()) l.add(valueName(p, v));
		return String.join("|", l);
	}

	static String propNames(Block b) {
		List<String> l = new ArrayList<>();
		for (Property<?> p : b.getStateDefinition().getProperties()) l.add(p.getName());
		return l.isEmpty() ? "none" : String.join(",", l);
	}

	static String stateString(BlockState s) {
		StringBuilder sb = new StringBuilder(BuiltInRegistries.BLOCK.getKey(s.getBlock()).toString());
		if (!s.getProperties().isEmpty()) {
			sb.append('[');
			boolean first = true;
			for (Property<?> p : s.getProperties()) {
				if (!first) sb.append(',');
				first = false;
				sb.append(p.getName()).append('=').append(valueName(p, s.getValue(p)));
			}
			sb.append(']');
		}
		return sb.toString();
	}

	/**
	 * Independent decoder: entry i occupies bits [i*bits, (i+1)*bits) of the bit stream formed by the longs, where bit k of
	 * the stream is bit (k mod 64) (LSB = 0) of long k/64. Done bit by bit on purpose (different code than Litematica's).
	 */
	static void decode(Region g, String w, Report r) {
		g.idx = new int[(int) g.volume];
		long totalBits = (long) g.longs.length * 64;
		int outOfRange = 0, truncated = 0;
		for (int i = 0; i < g.volume; i++) {
			long start = (long) i * g.bits;
			int v = 0;
			boolean cut = false;
			for (int b = 0; b < g.bits; b++) {
				long p = start + b;
				if (p >= totalBits) {
					cut = true;
					break;
				}
				v |= (int) ((g.longs[(int) (p >>> 6)] >>> (p & 63)) & 1L) << b;
			}
			if (cut) {
				g.idx[i] = -1;
				truncated++;
			} else if (v >= g.paletteSize) {
				if (outOfRange++ < 5) {
					int x = i % g.dx, z = (i / g.dx) % g.dz, y = i / (g.dx * g.dz);
					r.err(w + "cell (" + x + "," + y + "," + z + ") has palette index " + v + " >= palette size " + g.paletteSize
						+ " (Litematica reads it as air)");
				}
				g.idx[i] = -1;
			} else {
				g.idx[i] = v;
			}
		}
		if (outOfRange > 5) r.err(w + (outOfRange - 5) + " more cells with out-of-range palette indices");
		if (truncated > 0) r.err(w + truncated + " cells lie beyond the end of BlockStates");
		// unused high bits of the last long should be zero (Litematica's own writer leaves them zero)
		for (long p = g.volume * g.bits; p < totalBits; p++) {
			if (((g.longs[(int) (p >>> 6)] >>> (p & 63)) & 1L) != 0) {
				r.warn(w + "padding bits after the last entry are not zero (harmless, but Litematica writes zeros)");
				break;
			}
		}
		g.decoded = truncated == 0 && outOfRange == 0;
		int[] used = new int[g.paletteSize];
		for (int i = 0; i < g.volume; i++) {
			if (g.idx[i] < 0) continue;
			used[g.idx[i]]++;
			BlockState s = g.palette[g.idx[i]];
			if (s == null) {
				g.decoded = false;
				continue;
			}
			if (!s.isAir()) g.nonAir++;
			if (verbose) g.counts.merge(stateString(s), 1, Integer::sum);
		}
		for (int i = 1; i < g.paletteSize; i++) {
			if (used[i] == 0) r.info(w + "palette[" + i + "] is never used");
		}
	}

	// ------------------------------------------------------------------------------------------------ phase 2: Litematica

	static final List<String> CAPTURED = new ArrayList<>();

	/** Litematica/malilib report problems through InfoUtils.showGuiOrInGameMessage -> current Screen if it is an IMessageConsumer. */
	public static class CapturingScreen extends Screen implements IMessageConsumer {
		protected CapturingScreen() {
			super(Component.empty());   // never called: instances are made with Unsafe.allocateInstance (no GL / no Minecraft)
		}

		@Override
		public void addMessage(Message.MessageType type, String key, Object... args) {
			CAPTURED.add(type + " " + key + (args.length > 0 ? " " + Arrays.toString(args) : ""));
		}

		@Override
		public void addMessage(Message.MessageType type, int lifeTime, String key, Object... args) {
			this.addMessage(type, key, args);
		}
	}

	/**
	 * Litematica's reader needs: (1) Minecraft.getInstance().gameDirectory (Configs.Generic static init resolves the default
	 * schematic dir from it), (2) Minecraft.getInstance().gui.screen() for its message popups, (3) the registry access that
	 * SchematicWorldHandler normally receives on world join (palette entries are resolved through it; default is EMPTY).
	 * We provide exactly these on an Unsafe-allocated Minecraft (no constructor runs: no window, GL, sound or network).
	 */
	static String initLitematicaHeadless() {
		try {
			Field uf = Class.forName("sun.misc.Unsafe").getDeclaredField("theUnsafe");
			uf.setAccessible(true);
			Object unsafe = uf.get(null);
			java.lang.reflect.Method alloc = unsafe.getClass().getMethod("allocateInstance", Class.class);
			Path gameDir = Path.of(System.getProperty("litvalidate.gamedir", System.getProperty("java.io.tmpdir") + "/litvalidate-gamedir"));
			Files.createDirectories(gameDir);
			Minecraft mc = (Minecraft) alloc.invoke(unsafe, Minecraft.class);
			Gui gui = (Gui) alloc.invoke(unsafe, Gui.class);
			Screen screen = (Screen) alloc.invoke(unsafe, CapturingScreen.class);
			setField(Gui.class, "screen", gui, screen);
			setField(Minecraft.class, "gameDirectory", mc, gameDir.toFile());
			setField(Minecraft.class, "gui", mc, gui);
			setField(Minecraft.class, "instance", null, mc);
			SchematicWorldHandler.INSTANCE.setDynamicRegistryManager(RegistryAccess.fromRegistryOfRegistries(BuiltInRegistries.REGISTRY));
			return null;
		} catch (Throwable t) {
			return t.toString() + at(t);
		}
	}

	static void setField(Class<?> cls, String name, Object target, Object value) throws Exception {
		Field f = cls.getDeclaredField(name);
		f.setAccessible(true);
		f.set(target, value);
	}

	static void litematicaCheck(Path f, Map<String, Region> regions, Report r) {
		JsonObject jl = new JsonObject();
		r.json.add("litematica", jl);
		CAPTURED.clear();
		int errorsBefore = r.nErrors;
		Path abs = f.toAbsolutePath().normalize();
		Path dir = abs.getParent();
		String fileName = abs.getFileName().toString();

		FileType type = FileType.fromFile(abs);
		if (type != FileType.LITEMATICA_SCHEMATIC) {
			r.err("litematica: FileType.fromFile = " + type + " (the Load button only treats *.litematic as a Litematica schematic)");
		}
		if (!LitematicaSchematic.fileFromDirAndName(dir, fileName, FileType.LITEMATICA_SCHEMATIC).equals(abs)) {
			r.err("litematica: file name '" + fileName + "' is rewritten by FileNameUtils (illegal characters or 'COM'/'PRN'); Litematica cannot open it");
		}
		SchematicMetadata browserMeta = LitematicaSchematic.readMetadataFromFile(dir, fileName);
		if (browserMeta == null) r.err("litematica: readMetadataFromFile (schematic browser) returned null");

		LitematicaSchematic s = LitematicaSchematic.createFromFile(dir, fileName);
		for (String m : CAPTURED) {
			if (m.startsWith("ERROR")) r.err("litematica message: " + m);
			else r.warn("litematica message: " + m);
		}
		jl.addProperty("loaded", s != null);
		if (s == null) {
			r.err("litematica: createFromFile returned null (load failed)");
			// readFromFile swallows exceptions: repeat exactly what createFromFile does (private ctor + private readFromData) to see the cause
			try {
				java.lang.reflect.Constructor<LitematicaSchematic> ctor = LitematicaSchematic.class.getDeclaredConstructor(Path.class, FileType.class);
				ctor.setAccessible(true);
				LitematicaSchematic probe = ctor.newInstance(abs, FileType.LITEMATICA_SCHEMATIC);
				java.lang.reflect.Method read = LitematicaSchematic.class.getDeclaredMethod("readFromData",
					fi.dy.masa.malilib.util.data.tag.CompoundData.class);
				read.setAccessible(true);
				read.invoke(probe, LitematicaSchematic.readDataFromFile(abs));
			} catch (Throwable t) {
				while (t instanceof java.lang.reflect.InvocationTargetException && t.getCause() != null) t = t.getCause();
				String txt = t.toString();
				if (txt.contains("fi.dy.masa.litematica.mixin") || txt.contains("IMixin")) {
					r.err("litematica: cause: " + txt + " -- HARNESS LIMITATION, not necessarily a file defect: this code path needs a Mixin that "
						+ "only exists in-game (it is reached by the post-process fixers that run when MinecraftDataVersion < " + currentDataVersion + ")");
				} else {
					r.err("litematica: cause: " + txt + at(t));
				}
			}
			return;
		}
		SchematicMetadata m = s.getMetadata();
		if (m.getSchematicVersion() != 7 || m.getMinecraftDataVersion() != currentDataVersion) {
			r.info("litematica: schematic version " + m.getSchematicVersion() + ", data version " + m.getMinecraftDataVersion());
		}
		if (regions == null) return;

		// regions known to Litematica vs. the file
		Set<String> litRegions = new HashSet<>(s.getAreaSizes().keySet());
		for (String n : litRegions) {
			if (!regions.containsKey(n)) r.err("litematica: has region '" + n + "' that the native reader did not accept");
		}
		long cells = 0, identical = 0;
		for (Region g : regions.values()) {
			String w = "litematica: region '" + g.name + "': ";
			if (!litRegions.contains(g.name)) {
				r.err(w + "missing after load (Litematica dropped it)");
				continue;
			}
			BlockPos lpos = s.getSubRegionPosition(g.name);
			BlockPos lsize = s.getAreaSize(g.name);
			if (lpos.getX() != g.pos[0] || lpos.getY() != g.pos[1] || lpos.getZ() != g.pos[2]) r.err(w + "Position read as " + lpos);
			if (lsize.getX() != g.size[0] || lsize.getY() != g.size[1] || lsize.getZ() != g.size[2]) r.err(w + "Size read as " + lsize);
			LitematicaBlockStateContainer c = s.getSubRegionContainer(g.name);
			if (c == null) {
				r.err(w + "no block container (BlockStates not a LongArray?)");
				continue;
			}
			Vec3i cs = c.getSize();
			if (cs.getX() != g.dx || cs.getY() != g.dy || cs.getZ() != g.dz) {
				r.err(w + "container size " + cs + " != |Size| (" + g.dx + "," + g.dy + "," + g.dz + ")");
				continue;
			}
			if (c.getPalette().getPaletteSize() != g.paletteSize) {
				r.warn(w + "Litematica palette has " + c.getPalette().getPaletteSize() + " entries, file has " + g.paletteSize);
			}
			int mismatches = 0, unparsed = 0, crashes = 0;
			Map<String, String> unparsedAs = new LinkedHashMap<>();
			for (int y = 0; y < g.dy; y++) {
				for (int z = 0; z < g.dz; z++) {
					for (int x = 0; x < g.dx; x++) {
						int i = (y * g.dz + z) * g.dx + x;
						cells++;
						BlockState ls;
						try {
							ls = c.get(x, y, z);
						} catch (RuntimeException ex) {
							if (crashes++ == 0) r.err(w + "Litematica throws reading cell (" + x + "," + y + "," + z + "): " + ex);
							continue;
						}
						BlockState ns = g.idx != null && g.idx[i] >= 0 ? g.palette[g.idx[i]] : null;
						if (ns == null) {
							unparsed++;
							if (unparsedAs.size() < 5 && g.idx != null && g.idx[i] >= 0) {
								unparsedAs.putIfAbsent("palette[" + g.idx[i] + "]", stateString(ls));
							}
						} else if (ls != ns) {
							if (mismatches++ < 5) {
								r.err(w + "cell (" + x + "," + y + "," + z + "): Litematica has " + stateString(ls) + ", file decodes to " + stateString(ns));
							}
						} else {
							identical++;
						}
					}
				}
			}
			if (crashes > 1) r.err(w + crashes + " cells throw when read by Litematica");
			if (mismatches > 5) r.err(w + (mismatches - 5) + " more mismatching cells");
			if (unparsed > 0) {
				r.err(w + unparsed + " cell(s) use invalid palette entries; Litematica silently loads them as " + unparsedAs);
			}
			int lte = s.getBlockEntityMapForRegion(g.name) == null ? 0 : s.getBlockEntityMapForRegion(g.name).size();
			int lent = s.getEntityListForRegion(g.name) == null ? 0 : s.getEntityListForRegion(g.name).size();
			int lbt = s.getScheduledBlockTicksForRegion(g.name) == null ? 0 : s.getScheduledBlockTicksForRegion(g.name).size();
			int lft = s.getScheduledFluidTicksForRegion(g.name) == null ? 0 : s.getScheduledFluidTicksForRegion(g.name).size();
			if (lte != g.tileEntities) r.err(w + "Litematica kept " + lte + " tile entities, file has " + g.tileEntities + " valid ones");
			if (lent != g.entities) r.err(w + "Litematica kept " + lent + " entities, file has " + g.entities + " valid ones");
			if (lbt != g.blockTicks) r.warn(w + "Litematica kept " + lbt + " block ticks, file has " + g.blockTicks);
			if (lft != g.fluidTicks) r.warn(w + "Litematica kept " + lft + " fluid ticks, file has " + g.fluidTicks);
		}
		jl.addProperty("cells", cells);
		jl.addProperty("identical", identical);
		jl.addProperty("name", m.getName());
		jl.addProperty("totalBlocks", m.getTotalBlocks());
		jl.addProperty("totalVolume", m.getTotalVolume());
		jl.addProperty("enclosingSize", m.getEnclosingSize().toString());
		jl.addProperty("hasPreview", m.getPreviewImagePixelData() != null);
		String summary = "litematica: loaded, " + identical + "/" + cells + " cells identical to the strict MC-native decode"
			+ String.format("; shows name='%s' blocks=%d volume=%d size=%dx%dx%d regions=%d", m.getName(), m.getTotalBlocks(), m.getTotalVolume(),
			m.getEnclosingSize().getX(), m.getEnclosingSize().getY(), m.getEnclosingSize().getZ(), m.getRegionCount());
		if (identical == cells && r.nErrors == errorsBefore) {
			r.litematicaSummary = summary;
		} else {
			r.err(summary.replace("litematica: loaded,", "litematica: loaded, but only"));
		}
	}
}
