import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.shapes.VoxelShape;
import net.minecraft.SharedConstants;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.Bootstrap;
import net.minecraft.world.level.EmptyBlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.Property;

/**
 * Dumps every block of the running Minecraft version (ids, properties, defaults, item, per-state physics)
 * to JSON, straight from the game's own registry. Usage: RegistryDump <out.json>
 */
public class RegistryDump {
	static final Direction[] DIRS = {Direction.DOWN, Direction.UP, Direction.NORTH, Direction.SOUTH, Direction.WEST, Direction.EAST};

	public static void main(String[] args) throws Exception {
		SharedConstants.tryDetectVersion();
		Bootstrap.bootStrap();
		JsonObject root = new JsonObject();
		root.addProperty("version", SharedConstants.getCurrentVersion().name());
		root.addProperty("data_version", SharedConstants.getCurrentVersion().dataVersion().version());
		root.addProperty("dirs", "down,up,north,south,west,east");
		JsonObject blocks = new JsonObject();
		for (Block block : BuiltInRegistries.BLOCK) {
			JsonObject b = new JsonObject();
			b.addProperty("class", block.getClass().getSimpleName());
			b.addProperty("block_entity", block instanceof EntityBlock);
			b.addProperty("item", BuiltInRegistries.ITEM.getKey(block.asItem()).toString());
			JsonObject props = new JsonObject();
			JsonObject defaults = new JsonObject();
			BlockState def = block.defaultBlockState();
			for (Property<?> p : block.getStateDefinition().getProperties()) {
				JsonArray vals = new JsonArray();
				for (Object v : p.getPossibleValues()) {
					vals.add(name(p, v));
				}
				props.add(p.getName(), vals);
				defaults.addProperty(p.getName(), name(p, def.getValue(p)));
			}
			b.add("properties", props);
			b.add("default", defaults);
			// Per-state physics, encoded as "<sturdy mask>,<flags>,<light>" where flags: 1=canOcclude 2=fullCollision 4=solidRender 8=air.
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
				b.addProperty("phys", first);
			} else {
				JsonObject per = new JsonObject();
				for (BlockState s : states) {
					per.addProperty(key(s), enc(s));
				}
				b.add("phys_by_state", per);
			}
			blocks.add(BuiltInRegistries.BLOCK.getKey(block).toString(), b);
		}
		root.add("blocks", blocks);
		JsonArray shapes = new JsonArray();
		for (String sh : SHAPES) shapes.add(sh);
		root.add("shapes", shapes);
		root.addProperty("phys_format", "sturdyMask(bit i = dirs[i]),flags(1 canOcclude,2 fullCollision,4 solidRender,8 air),lightEmission,collisionShapeIndex");
		Files.writeString(Path.of(args[0]), new GsonBuilder().create().toJson(root));
		System.out.println("blocks: " + blocks.size());
	}

	@SuppressWarnings({"unchecked", "rawtypes"})
	static String name(Property p, Object v) {
		return p.getName((Comparable) v);
	}

	static final List<String> SHAPES = new ArrayList<>();
	static final Map<String, Integer> SHAPE_IDS = new HashMap<>();

	/** Collision shape as "x1 y1 z1 x2 y2 z2;..." in block units (0..1, fences reach 1.5), interned into SHAPES. */
	static int shape(VoxelShape shape) {
		StringBuilder sb = new StringBuilder();
		for (AABB box : shape.toAabbs()) {
			if (sb.length() > 0) sb.append(';');
			sb.append(f(box.minX)).append(' ').append(f(box.minY)).append(' ').append(f(box.minZ)).append(' ')
				.append(f(box.maxX)).append(' ').append(f(box.maxY)).append(' ').append(f(box.maxZ));
		}
		return SHAPE_IDS.computeIfAbsent(sb.toString(), k -> {
			SHAPES.add(k);
			return SHAPES.size() - 1;
		});
	}

	static String f(double d) {
		String s = String.format(java.util.Locale.ROOT, "%.4f", d);
		s = s.replaceAll("0+$", "");
		return s.endsWith(".") ? s.substring(0, s.length() - 1) : s;
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
		int mask = 0;
		for (int i = 0; i < 6; i++) {
			if (s.isFaceSturdy(EmptyBlockGetter.INSTANCE, BlockPos.ZERO, DIRS[i])) mask |= 1 << i;
		}
		int flags = (s.canOcclude() ? 1 : 0) | (s.isCollisionShapeFullBlock(EmptyBlockGetter.INSTANCE, BlockPos.ZERO) ? 2 : 0)
			| (s.isSolidRender() ? 4 : 0) | (s.isAir() ? 8 : 0);
		return mask + "," + flags + "," + s.getLightEmission() + "," + shape(s.getCollisionShape(EmptyBlockGetter.INSTANCE, BlockPos.ZERO));
	}
}
