"""Material list: count the obtainable ITEMS needed to build the final block set.

Rules (block -> items):
  * item from the registry dump (``Block.asItem()``): wall torches -> torch, wall signs -> sign, crops -> seeds/produce
    (wheat -> wheat_seeds, carrots -> carrot, ...), cave_vines -> glow_berries, big_dripleaf_stem -> big_dripleaf ...
  * two-block things counted once: doors (lower half), beds (foot), double plants (lower half)
  * slab type=double -> 2; amounts: candles, sea_pickle pickles, pink_petals/wildflowers flower_amount,
    leaf_litter segment_amount, turtle_egg eggs, snow layers
  * potted_X -> flower_pot + X;  candle cakes -> cake + candle;  *_plant parts -> their item
    (kelp_plant -> kelp, cave_vines_plant -> glow_berries, weeping/twisting_vines_plant -> vines, bamboo_sapling -> bamboo,
    attached stems -> seeds, tall_seagrass -> seagrass)
  * water/lava source -> bucket; waterlogged=true -> +1 water_bucket (placement uses); farmland / dirt_path -> dirt (+note)
  * creative-only / unobtainable blocks are listed as warnings.
Stack sizes come from the real game (``Item.getDefaultMaxStackSize`` dumped from 26.3; only non-64 listed below).
"""
from __future__ import annotations

import json
from pathlib import Path

from . import registry as R

# Dumped from Minecraft 26.3 (BuiltInRegistries.ITEM, components bound), filtered to block items + buckets.
_STACKS_RAW = """
shulker_box=1 white_shulker_box=1 orange_shulker_box=1 magenta_shulker_box=1 light_blue_shulker_box=1 yellow_shulker_box=1
lime_shulker_box=1 pink_shulker_box=1 gray_shulker_box=1 light_gray_shulker_box=1 cyan_shulker_box=1 purple_shulker_box=1
blue_shulker_box=1 brown_shulker_box=1 green_shulker_box=1 red_shulker_box=1 black_shulker_box=1 flint_and_steel=1
oak_sign=16 spruce_sign=16 birch_sign=16 jungle_sign=16 acacia_sign=16 cherry_sign=16 dark_oak_sign=16 pale_oak_sign=16
mangrove_sign=16 poplar_sign=16 bamboo_sign=16 crimson_sign=16 warped_sign=16 oak_hanging_sign=16 spruce_hanging_sign=16
birch_hanging_sign=16 jungle_hanging_sign=16 acacia_hanging_sign=16 cherry_hanging_sign=16 dark_oak_hanging_sign=16
pale_oak_hanging_sign=16 mangrove_hanging_sign=16 poplar_hanging_sign=16 bamboo_hanging_sign=16 crimson_hanging_sign=16
warped_hanging_sign=16 bucket=16 water_bucket=1 lava_bucket=1 powder_snow_bucket=1 snowball=16 egg=16 cake=1
white_bed=1 orange_bed=1 magenta_bed=1 light_blue_bed=1 yellow_bed=1 lime_bed=1 pink_bed=1 gray_bed=1 light_gray_bed=1
cyan_bed=1 purple_bed=1 blue_bed=1 brown_bed=1 green_bed=1 red_bed=1 black_bed=1 straw_bed=16 armor_stand=16
white_banner=16 orange_banner=16 magenta_banner=16 light_blue_banner=16 yellow_banner=16 lime_banner=16 pink_banner=16
gray_banner=16 light_gray_banner=16 cyan_banner=16 purple_banner=16 blue_banner=16 brown_banner=16 green_banner=16
red_banner=16 black_banner=16
"""
STACK_SIZE = {"minecraft:" + k: int(v) for k, v in (t.split("=") for t in _STACKS_RAW.split())}

CREATIVE_ONLY = {f"minecraft:{n}" for n in """
barrier light structure_void structure_block jigsaw command_block chain_command_block repeating_command_block
test_block test_instance_block bedrock spawner trial_spawner vault budding_amethyst reinforced_deepslate
petrified_oak_slab end_portal_frame end_portal end_gateway nether_portal frosted_ice moving_piston piston_head
infested_stone infested_cobblestone infested_stone_bricks infested_mossy_stone_bricks infested_cracked_stone_bricks
infested_chiseled_stone_bricks infested_deepslate chorus_plant frogspawn suspicious_sand suspicious_gravel
bubble_column knowledge_book
""".split()}

_PLANT_PART_ITEM = {
    "minecraft:kelp_plant": "minecraft:kelp", "minecraft:cave_vines_plant": "minecraft:glow_berries",
    "minecraft:weeping_vines_plant": "minecraft:weeping_vines", "minecraft:twisting_vines_plant": "minecraft:twisting_vines",
    "minecraft:bamboo_sapling": "minecraft:bamboo", "minecraft:attached_pumpkin_stem": "minecraft:pumpkin_seeds",
    "minecraft:attached_melon_stem": "minecraft:melon_seeds", "minecraft:tall_seagrass": "minecraft:seagrass",
    "minecraft:water": "minecraft:water_bucket", "minecraft:lava": "minecraft:lava_bucket",
    "minecraft:farmland": "minecraft:dirt", "minecraft:dirt_path": "minecraft:dirt",
}
_AMOUNT_PROPS = ("candles", "pickles", "flower_amount", "segment_amount", "eggs", "layers")

GROUPS = ("structure / stone", "wood", "roofing", "glass", "decor & lighting", "furniture & utility",
          "plants & landscaping", "other")


def stack_size(item: str) -> int:
    return STACK_SIZE.get(item, 64)


def stacks(count: int, item: str) -> str:
    """'3 x 64 + 12' style text (or '12' when under one stack)."""
    s = stack_size(item)
    n, r = divmod(count, s)
    if n == 0:
        return str(r)
    return f"{n} x {s}" + (f" + {r}" if r else "")


def _items_for(state: str, add, warn, note):
    bid, items = R._split(state)
    p = dict(items)
    chain = R.class_chain(state)
    if R.is_air(state):
        return
    if bid in CREATIVE_ONLY:
        warn(f"{bid} is creative-only / not obtainable as an item in survival")
        return
    if bid in ("minecraft:fire", "minecraft:soul_fire"):
        note("fire: light it with a flint_and_steel (soul fire needs soul sand/soil below)")
        add("minecraft:flint_and_steel", 0)
        return
    if "DoorBlock" in chain and p.get("half") == "upper":
        return
    if "AbstractBedBlock" in chain and p.get("part") == "head":
        return
    if "DoublePlantBlock" in chain and p.get("half") == "upper":
        return
    if p.get("waterlogged") == "true":
        add("minecraft:water_bucket", 1)
        note("waterlogged blocks: one water_bucket placement each (an infinite water source refills buckets)")
    if bid in ("minecraft:water", "minecraft:lava"):
        if p.get("level") != "0":
            note(f"flowing {bid.split(':')[1]} ignored (only sources need a bucket)")
            return
    if bid in ("minecraft:farmland", "minecraft:dirt_path"):
        note("farmland / dirt_path: place dirt (or grass) and use a hoe / shovel")
    if bid in _PLANT_PART_ITEM:
        add(_PLANT_PART_ITEM[bid], 1)
        return
    if bid.startswith("minecraft:potted_"):
        add("minecraft:flower_pot", 1)
        plant = bid[len("minecraft:potted_"):]
        if plant in ("azalea_bush", "flowering_azalea_bush"):
            plant = plant[: -len("_bush")]
        pid = "minecraft:" + plant
        if R.exists(pid) and R.info(pid).item != R.AIR:
            add(R.info(pid).item, 1)
        else:
            warn(f"cannot determine the plant item for {bid}")
        return
    if bid.endswith("candle_cake"):
        add("minecraft:cake", 1)
        add(bid[: -len("_cake")] if bid != "minecraft:candle_cake" else "minecraft:candle", 1)
        return
    it = R.info(bid).item
    if it == R.AIR:
        warn(f"{bid} has no item in 26.3 (not counted)")
        return
    n = 1
    if "SlabBlock" in chain and p.get("type") == "double":
        n = 2
    for k in _AMOUNT_PROPS:
        if k in p and p[k].isdigit():
            n = int(p[k])
            break
    add(it, n)


def material_list(blocks) -> dict:
    """``blocks``: dict pos->state or any iterable of states.  Returns
    {"items": {item: count} (sorted by count desc), "groups": {group: {item: count}}, "total_items": int,
     "warnings": [...], "notes": [...]}."""
    states = blocks.values() if isinstance(blocks, dict) else blocks
    counts: dict = {}
    warnings: list = []
    notes: list = []

    def add(item, n):
        counts[item] = counts.get(item, 0) + n

    def warn(msg):
        if msg not in warnings:
            warnings.append(msg)

    def note(msg):
        if msg not in notes:
            notes.append(msg)

    for s in states:
        _items_for(s, add, warn, note)
    if "minecraft:flint_and_steel" in counts:
        counts["minecraft:flint_and_steel"] = max(1, counts["minecraft:flint_and_steel"])
    items = dict(sorted(((k, v) for k, v in counts.items() if v > 0), key=lambda kv: (-kv[1], kv[0])))
    groups: dict = {g: {} for g in GROUPS}
    for it, n in items.items():
        groups[group_of(it)][it] = n
    return {"items": items, "groups": {g: v for g, v in groups.items() if v}, "total_items": sum(items.values()),
            "warnings": warnings, "notes": notes}


_DECOR_IDS = {f"minecraft:{n}" for n in """
torch soul_torch copper_torch redstone_torch end_rod sea_lantern glowstone shroomlight ochre_froglight verdant_froglight
pearlescent_froglight flower_pot bell decorated_pot redstone_lamp copper_bulb exposed_copper_bulb weathered_copper_bulb
oxidized_copper_bulb waxed_copper_bulb waxed_exposed_copper_bulb waxed_weathered_copper_bulb waxed_oxidized_copper_bulb
lightning_rod jack_o_lantern carved_pumpkin skeleton_skull wither_skeleton_skull zombie_head player_head creeper_head
dragon_head piglin_head painting item_frame glow_item_frame armor_stand moss_carpet pale_moss_carpet candle_cake
""".split()}
_FURNITURE_IDS = {f"minecraft:{n}" for n in """
chest trapped_chest barrel ender_chest crafting_table furnace smoker blast_furnace lectern cartography_table
fletching_table smithing_table stonecutter grindstone loom composter cauldron bookshelf chiseled_bookshelf
beehive bee_nest jukebox note_block brewing_stand enchanting_table hopper crafter respawn_anchor lodestone ladder
scaffolding cake dropper dispenser copper_chest exposed_copper_chest weathered_copper_chest oxidized_copper_chest
waxed_copper_chest waxed_exposed_copper_chest waxed_weathered_copper_chest waxed_oxidized_copper_chest
""".split()}
_LANDSCAPE_IDS = {f"minecraft:{n}" for n in """
grass_block dirt coarse_dirt rooted_dirt podzol mycelium moss_block pale_moss_block mud gravel sand red_sand clay
vine glow_lichen lily_pad sugar_cane bamboo cactus wheat_seeds carrot potato beetroot_seeds melon_seeds pumpkin_seeds
torchflower_seeds pitcher_pod sweet_berries glow_berries brown_mushroom red_mushroom brown_mushroom_block
red_mushroom_block mushroom_stem short_grass tall_grass fern large_fern bush firefly_bush dead_bush leaf_litter
pink_petals wildflowers hay_block pumpkin melon water_bucket seagrass kelp small_dripleaf big_dripleaf spore_blossom
hanging_roots mangrove_roots muddy_mangrove_roots cocoa_beans nether_wart short_dry_grass tall_dry_grass sunflower
lilac rose_bush peony pitcher_plant pale_hanging_moss shelf_mushroom snow snow_block farmland dirt_path
""".split()}


def group_of(item: str) -> str:
    """Group name for the markdown list (heuristic, documented in GROUPS order)."""
    name = item.split(":")[1]
    tagged = R.exists(item)

    def tag(t):
        return tagged and R.has_tag(item, t)

    if "glass" in name:
        return "glass"
    if name.endswith("_stairs") or name.endswith("_slab"):
        return "roofing"
    if item in _FURNITURE_IDS or tag("beds") or tag("anvil") or tag("wooden_shelves") or tag("cauldrons") or tag("shulker_boxes"):
        return "furniture & utility"
    if (item in _DECOR_IDS or tag("lanterns") or tag("candles") or tag("campfires") or tag("chains") or tag("banners")
            or tag("wool_carpets") or tag("all_signs") or name.endswith("_banner") or name.endswith("_sign")):
        return "decor & lighting"
    if (item in _LANDSCAPE_IDS or tag("leaves") or tag("saplings") or tag("flowers") or tag("small_flowers")
            or tag("crops") or tag("dirt") or tag("moss_blocks")):
        return "plants & landscaping"
    if (tag("planks") or tag("logs") or tag("wooden_fences") or tag("fence_gates") or tag("wooden_doors")
            or tag("wooden_trapdoors") or tag("wooden_buttons") or tag("wooden_pressure_plates")
            or name.startswith("stripped_") or name in ("bamboo_mosaic", "bamboo_block")):
        return "wood"
    if tagged:
        return "structure / stone"
    return "other"


def to_markdown(report: dict, title: str = "") -> str:
    lines = [f"# Materials{': ' + title if title else ''}", "",
             f"Total items: **{report['total_items']}** ({len(report['items'])} kinds)", ""]
    for g, items in report["groups"].items():
        lines += [f"## {g}", "", "| item | count | stacks + remainder |", "|---|---:|---|"]
        for it, n in items.items():
            lines.append(f"| {it.split(':')[1]} | {n} | {stacks(n, it)} |")
        lines.append("")
    if report["warnings"]:
        lines += ["## warnings", ""] + [f"- {w}" for w in report["warnings"]] + [""]
    if report["notes"]:
        lines += ["## notes", ""] + [f"- {w}" for w in report["notes"]] + [""]
    return "\n".join(lines)


def write_materials(report: dict, md_path, json_path, title: str = "") -> None:
    md_path, json_path = Path(md_path), Path(json_path)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(to_markdown(report, title), encoding="utf-8")
    data = dict(report)
    data["stacks"] = {it: stacks(n, it) for it, n in report["items"].items()}
    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
