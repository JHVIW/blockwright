import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.TreeMap;
import net.minecraft.SharedConstants;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.Bootstrap;
import net.minecraft.world.level.block.Block;

/**
 * Dumps the superclass chain (simple names, up to java.lang.Object) of every
 * block class in the registry: {"StairBlock": ["Block", "BlockBehaviour"], "CandleBlock": ["AbstractCandleBlock", "Block", "BlockBehaviour"], ...}.
 * blockwright uses it for the game's instanceof checks. Usage: ClassAncestorsDump <out.json>
 */
public class ClassAncestorsDump {
	public static void main(String[] args) throws Exception {
		SharedConstants.tryDetectVersion();
		Bootstrap.bootStrap();
		TreeMap<String, JsonArray> out = new TreeMap<>();
		for (Block block : BuiltInRegistries.BLOCK) {
			Class<?> c = block.getClass();
			String name = c.getSimpleName();
			if (out.containsKey(name)) continue;
			JsonArray chain = new JsonArray();
			for (Class<?> p = c.getSuperclass(); p != null && p != Object.class; p = p.getSuperclass()) {
				chain.add(p.getSimpleName());
			}
			out.put(name, chain);
		}
		JsonObject root = new JsonObject();
		out.forEach(root::add);
		Files.writeString(Path.of(args[0]), new GsonBuilder().create().toJson(root));
	}
}
