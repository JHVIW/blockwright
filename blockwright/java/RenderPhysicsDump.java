import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.SharedConstants;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.Bootstrap;
import net.minecraft.world.level.EmptyBlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.Property;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Renderer physics for every 26.3 block state, straight from the game (blockwright.render uses it when present):
 * per state "legacySolid,propagatesSkylightDown,lightDampening,emissiveRendering,shadeBrightness*10,
 * useShapeForLightOcclusion,face0..face5" where face i = index into "faces" of getFaceOcclusionShape(dirs[i])
 * ("" = empty, "full" = Shapes.block(), else 16x16 face mask as 64 hex digits, bit u*16+v).
 * Usage (see docs/RENDER.md): java -cp <classes>;<classpath> RenderPhysicsDump blockwright/data/render_physics_26.3.json
 */
public class RenderPhysicsDump {
	static final Direction[] DIRS = {Direction.DOWN, Direction.UP, Direction.NORTH, Direction.SOUTH, Direction.WEST, Direction.EAST};
	static final List<String> FACES = new ArrayList<>();
	static final Map<String, Integer> FACE_IDS = new HashMap<>();

	public static void main(String[] args) throws Exception {
		SharedConstants.tryDetectVersion();
		Bootstrap.bootStrap();
		JsonObject root = new JsonObject();
		root.addProperty("version", SharedConstants.getCurrentVersion().name());
		root.addProperty("format", "solid,skyDown,lightDampening,emissive,shade*10,shapeLightOcclusion,face0..5 (dirs down,up,north,south,west,east)");
		JsonObject blocks = new JsonObject();
		for (Block block : BuiltInRegistries.BLOCK) {
			List<BlockState> states = block.getStateDefinition().getPossibleStates();
			String first = enc(states.get(0));
			boolean uniform = true;
			for (BlockState s : states) {
				if (!enc(s).equals(first)) {
					uniform = false;
					break;
				}
			}
			if (uniform) {
				blocks.addProperty(BuiltInRegistries.BLOCK.getKey(block).toString(), first);
			} else {
				JsonObject per = new JsonObject();
				for (BlockState s : states) {
					per.addProperty(key(s), enc(s));
				}
				blocks.add(BuiltInRegistries.BLOCK.getKey(block).toString(), per);
			}
		}
		root.add("blocks", blocks);
		JsonArray faces = new JsonArray();
		for (String f : FACES) faces.add(f);
		root.add("faces", faces);
		Files.writeString(Path.of(args[0]), new GsonBuilder().create().toJson(root));
		System.out.println("blocks: " + blocks.size() + ", face shapes: " + FACES.size());
	}

	static int face(VoxelShape shape, Direction dir) {
		String code;
		if (shape.isEmpty()) {
			code = "";
		} else if (shape == Shapes.block()) {
			code = "full";
		} else {
			long[] bits = new long[4];
			int axisU, axisV;
			switch (dir.getAxis()) {
				case X -> { axisU = 2; axisV = 1; }   // (z, y)
				case Y -> { axisU = 0; axisV = 2; }   // (x, z)
				default -> { axisU = 0; axisV = 1; }  // (x, y)
			}
			for (AABB box : shape.toAabbs()) {
				double[] lo = {box.minX, box.minY, box.minZ};
				double[] hi = {box.maxX, box.maxY, box.maxZ};
				int u0 = clamp((int) Math.round(lo[axisU] * 16)), u1 = clamp((int) Math.round(hi[axisU] * 16));
				int v0 = clamp((int) Math.round(lo[axisV] * 16)), v1 = clamp((int) Math.round(hi[axisV] * 16));
				for (int u = u0; u < u1; u++) {
					for (int v = v0; v < v1; v++) {
						int bit = u * 16 + v;
						bits[bit >> 6] |= 1L << (bit & 63);
					}
				}
			}
			StringBuilder sb = new StringBuilder();
			for (int i = 3; i >= 0; i--) sb.append(String.format("%016x", bits[i]));
			code = sb.toString();
		}
		return FACE_IDS.computeIfAbsent(code, k -> {
			FACES.add(k);
			return FACES.size() - 1;
		});
	}

	static int clamp(int v) {
		return Math.max(0, Math.min(16, v));
	}

	@SuppressWarnings({"unchecked", "rawtypes"})
	static String name(Property p, Object v) {
		return p.getName((Comparable) v);
	}

	static String key(BlockState s) {
		StringBuilder sb = new StringBuilder();
		for (Property<?> p : s.getProperties()) {
			if (sb.length() > 0) sb.append(',');
			sb.append(p.getName()).append('=').append(name(p, s.getValue(p)));
		}
		return sb.toString();
	}

	static String enc(BlockState s) {
		StringBuilder sb = new StringBuilder();
		sb.append(s.isSolid() ? 1 : 0).append(',')
			.append(s.propagatesSkylightDown() ? 1 : 0).append(',')
			.append(s.getLightDampening()).append(',')
			.append(s.emissiveRendering() ? 1 : 0).append(',')
			.append(Math.round(s.getShadeBrightness(EmptyBlockGetter.INSTANCE, BlockPos.ZERO) * 10)).append(',')
			.append(s.useShapeForLightOcclusion() ? 1 : 0);
		for (Direction d : DIRS) {
			sb.append(',').append(face(s.getFaceOcclusionShape(d), d));
		}
		return sb.toString();
	}
}
