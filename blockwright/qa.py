"""blockwright.qa - automated quality checks for a finished structure (Minecraft Java 26.3).

Public API (see docs/QA.md for the exact rules of every check):

    run_qa(blocks, size, meta, registry=None) -> dict
    write_report(report, md_path, json_path) -> None

``blocks`` maps (x, y, z) -> canonical state string ("minecraft:oak_stairs[facing=east,...]"),
normalized so the bounding box min corner is (0, 0, 0); ``size`` is (sx, sy, sz); ``meta`` holds at least
``ground`` (y of the natural terrain surface layer), ``rooms`` {name: (x, y, z) feet position},
``entrances`` [(x, y, z) feet positions outside the main door], ``slug`` and ``title``.

This module is deliberately self-contained (stdlib + numpy).  Ground truth comes from
``data/blocks_26.3.json`` (dumped from the real 26.3 registry) and the vanilla block/fluid tags inside the
26.3 common jar.  Every game rule ported here cites the decompiled 26.3 class it comes from.

World model used by every check: cells outside the bounding box are air above ``ground``; wherever the build
left a cell empty at y <= ground there is natural terrain (grass_block at y == ground, dirt below), inside the
box and outside it.  That is how the build sits in the world after pasting.  Explicit air entries are treated as
empty cells (a .litematic cannot carve terrain with air).
"""
from __future__ import annotations

import json
import os
import re
import time
import zipfile
from collections import deque
from pathlib import Path

import numpy as np

from . import config as _config

BLOCKS_JSON = _config.data_file("blocks")
TAGS_JSON = _config.data_file("tags")

DIRS = ("down", "up", "north", "south", "west", "east")  # same order as the registry dump's sturdy mask
DVEC = {"down": (0, -1, 0), "up": (0, 1, 0), "north": (0, 0, -1), "south": (0, 0, 1), "west": (-1, 0, 0), "east": (1, 0, 0)}
OPP = {"down": "up", "up": "down", "north": "south", "south": "north", "west": "east", "east": "west"}
DBIT = {d: 1 << i for i, d in enumerate(DIRS)}
HORIZ = ("north", "south", "west", "east")
EPS = 1e-6

AIR_NAMES = frozenset({"minecraft:air", "minecraft:cave_air", "minecraft:void_air"})
TERRAIN_TOP = "minecraft:grass_block[snowy=false]"
TERRAIN_FILL = "minecraft:dirt"

# --------------------------------------------------------------------------------------------------------------
# Block class hierarchy (child -> parent) for every class in the 26.3 registry dump that does not extend Block
# directly.  Generated from the decompiled 26.3 sources (net/minecraft/world/level/block/**).
# --------------------------------------------------------------------------------------------------------------
_CLASS_PARENT_SRC = """
AmethystClusterBlock>AmethystBlock AnvilBlock>FallingBlock AttachedStemBlock>VegetationBlock AzaleaBlock>VegetationBlock
BannerBlock>AbstractBannerBlock AbstractBannerBlock>BaseEntityBlock BarrelBlock>BaseEntityBlock
BaseCoralFanBlock>BaseCoralPlantTypeBlock BaseCoralPlantBlock>BaseCoralPlantTypeBlock BaseCoralWallFanBlock>BaseCoralFanBlock
BeaconBlock>BaseEntityBlock BedBlock>AbstractBedBlock AbstractBedBlock>HorizontalDirectionalBlock BeehiveBlock>BaseEntityBlock
BeetrootBlock>CropBlock BellBlock>BaseEntityBlock BigDripleafBlock>HorizontalDirectionalBlock
BigDripleafStemBlock>HorizontalDirectionalBlock BlastFurnaceBlock>AbstractFurnaceBlock AbstractFurnaceBlock>BaseEntityBlock
BrewingStandBlock>BaseEntityBlock BrushableBlock>BaseEntityBlock BuddingAmethystBlock>AmethystBlock BushBlock>VegetationBlock
ButtonBlock>FaceAttachedHorizontalDirectionalBlock FaceAttachedHorizontalDirectionalBlock>HorizontalDirectionalBlock
CactusFlowerBlock>VegetationBlock CalibratedSculkSensorBlock>SculkSensorBlock CampfireBlock>BaseEntityBlock
CandleBlock>AbstractCandleBlock CandleCakeBlock>AbstractCandleBlock CarrotBlock>CropBlock
CarvedPumpkinBlock>HorizontalDirectionalBlock CauldronBlock>AbstractCauldronBlock CaveVinesBlock>GrowingPlantHeadBlock
GrowingPlantHeadBlock>GrowingPlantBlock CaveVinesPlantBlock>GrowingPlantBodyBlock GrowingPlantBodyBlock>GrowingPlantBlock
CeilingHangingSignBlock>SignBlock SignBlock>BaseEntityBlock ChainBlock>RotatedPillarBlock ChestBlock>AbstractChestBlock
AbstractChestBlock>BaseEntityBlock ChiseledBookShelfBlock>BaseEntityBlock ChorusPlantBlock>PipeBlock
CocoaBlock>HorizontalDirectionalBlock ColoredFallingBlock>FallingBlock CommandBlock>BaseEntityBlock ComparatorBlock>DiodeBlock
DiodeBlock>HorizontalDirectionalBlock ConcretePowderBlock>FallingBlock ConduitBlock>BaseEntityBlock CopperChestBlock>ChestBlock
CopperGolemStatueBlock>BaseEntityBlock CoralFanBlock>BaseCoralFanBlock CoralPlantBlock>BaseCoralPlantTypeBlock
CoralWallFanBlock>BaseCoralWallFanBlock CrafterBlock>BaseEntityBlock CreakingHeartBlock>BaseEntityBlock CropBlock>VegetationBlock
DaylightDetectorBlock>BaseEntityBlock DecoratedPotBlock>BaseEntityBlock DetectorRailBlock>BaseRailBlock
DispenserBlock>BaseEntityBlock DoublePlantBlock>VegetationBlock DragonEggBlock>FallingBlock
DriedGhastBlock>HorizontalDirectionalBlock DropperBlock>DispenserBlock DryVegetationBlock>VegetationBlock
EnchantingTableBlock>BaseEntityBlock EndGatewayBlock>BaseEntityBlock EndPortalBlock>BaseEntityBlock EndRodBlock>RodBlock
RodBlock>DirectionalBlock EnderChestBlock>AbstractChestBlock EyeblossomBlock>FlowerBlock FlowerBlock>VegetationBlock
FenceBlock>CrossCollisionBlock FenceGateBlock>HorizontalDirectionalBlock FireBlock>BaseFireBlock
FireflyBushBlock>VegetationBlock FlowerBedBlock>VegetationBlock FrostedIceBlock>IceBlock IceBlock>HalfTransparentBlock
FurnaceBlock>AbstractFurnaceBlock GlazedTerracottaBlock>HorizontalDirectionalBlock GlowLichenBlock>MultifaceSpreadeableBlock
MultifaceSpreadeableBlock>MultifaceBlock GrassBlock>SpreadingSnowyBlock SpreadingSnowyBlock>SnowyBlock
GrindstoneBlock>FaceAttachedHorizontalDirectionalBlock HayBlock>RotatedPillarBlock HoneyBlock>HalfTransparentBlock
HopperBlock>BaseEntityBlock InfestedRotatedPillarBlock>InfestedBlock IronBarsBlock>CrossCollisionBlock
JukeboxBlock>BaseEntityBlock KelpBlock>GrowingPlantHeadBlock KelpPlantBlock>GrowingPlantBodyBlock
LavaCauldronBlock>AbstractCauldronBlock LayeredCauldronBlock>AbstractCauldronBlock LeafLitterBlock>VegetationBlock
LecternBlock>BaseEntityBlock LeverBlock>FaceAttachedHorizontalDirectionalBlock LightningRodBlock>RodBlock
LilyPadBlock>VegetationBlock LoomBlock>HorizontalDirectionalBlock MangroveLeavesBlock>TintedParticleLeavesBlock
TintedParticleLeavesBlock>FallingParticlesLeavesBlock FallingParticlesLeavesBlock>LeavesBlock
MangrovePropaguleBlock>SaplingBlock SaplingBlock>VegetationBlock MovingPistonBlock>BaseEntityBlock MushroomBlock>VegetationBlock
MyceliumBlock>SpreadingSnowyBlock NetherFungusBlock>VegetationBlock NetherRootsBlock>VegetationBlock
NetherSproutsBlock>VegetationBlock NetherWartBlock>VegetationBlock ObserverBlock>DirectionalBlock
PiglinWallSkullBlock>WallSkullBlock WallSkullBlock>AbstractSkullBlock AbstractSkullBlock>BaseEntityBlock
PistonBaseBlock>DirectionalBlock PistonHeadBlock>DirectionalBlock PitcherCropBlock>DoublePlantBlock
PlayerHeadBlock>SkullBlock SkullBlock>AbstractSkullBlock PlayerWallHeadBlock>WallSkullBlock
PointedDripstoneBlock>SpeleothemBlock PotatoBlock>CropBlock PotentSulfurBlock>BaseEntityBlock PoweredRailBlock>BaseRailBlock
PressurePlateBlock>BasePressurePlateBlock RailBlock>BaseRailBlock RedstoneTorchBlock>BaseTorchBlock
RedstoneWallTorchBlock>RedstoneTorchBlock RepeaterBlock>DiodeBlock SandBlock>ColoredFallingBlock
SculkBlock>DropExperienceBlock SculkCatalystBlock>BaseEntityBlock SculkSensorBlock>BaseEntityBlock
SculkShriekerBlock>BaseEntityBlock SculkVeinBlock>MultifaceSpreadeableBlock SeaPickleBlock>VegetationBlock
SeagrassBlock>VegetationBlock ShelfBlock>BaseEntityBlock ShelfMushroomBlock>HorizontalDirectionalBlock
ShortDryGrassBlock>DryVegetationBlock ShulkerBoxBlock>BaseEntityBlock SlimeBlock>HalfTransparentBlock
SmallDripleafBlock>DoublePlantBlock SmithingTableBlock>CraftingTableBlock SmokerBlock>AbstractFurnaceBlock
SoulFireBlock>BaseFireBlock SpawnerBlock>BaseEntityBlock StainedGlassBlock>TransparentBlock
TransparentBlock>HalfTransparentBlock StainedGlassPaneBlock>IronBarsBlock StandingSignBlock>SignBlock StemBlock>VegetationBlock
StrawBedBlock>AbstractBedBlock StructureBlock>BaseEntityBlock SulfurSpikeBlock>SpeleothemBlock
SweetBerryBushBlock>VegetationBlock TallDryGrassBlock>DryVegetationBlock TallFlowerBlock>DoublePlantBlock
TallGrassBlock>VegetationBlock TallSeagrassBlock>DoublePlantBlock TestBlock>BaseEntityBlock TestInstanceBlock>BaseEntityBlock
TintedGlassBlock>TransparentBlock TorchBlock>BaseTorchBlock TorchflowerCropBlock>CropBlock
TrapDoorBlock>HorizontalDirectionalBlock TrappedChestBlock>ChestBlock TrialSpawnerBlock>BaseEntityBlock
TwistingVinesBlock>GrowingPlantHeadBlock TwistingVinesPlantBlock>GrowingPlantBodyBlock
UntintedParticleLeavesBlock>FallingParticlesLeavesBlock VaultBlock>BaseEntityBlock WallBannerBlock>AbstractBannerBlock
WallHangingSignBlock>SignBlock WallSignBlock>SignBlock WallTorchBlock>TorchBlock
WaterloggedTransparentBlock>TransparentBlock WeatheringCopperBarsBlock>IronBarsBlock WeatheringCopperBulbBlock>CopperBulbBlock
WeatheringCopperChainBlock>ChainBlock WeatheringCopperChestBlock>CopperChestBlock WeatheringCopperDoorBlock>DoorBlock
WeatheringCopperGolemStatueBlock>CopperGolemStatueBlock WeatheringCopperGrateBlock>WaterloggedTransparentBlock
WeatheringCopperSlabBlock>SlabBlock WeatheringCopperStairBlock>StairBlock WeatheringCopperTrapDoorBlock>TrapDoorBlock
WeatheringLanternBlock>LanternBlock WeatheringLightningRodBlock>LightningRodBlock WeepingVinesBlock>GrowingPlantHeadBlock
WeepingVinesPlantBlock>GrowingPlantBodyBlock WeightedPressurePlateBlock>BasePressurePlateBlock WitherRoseBlock>FlowerBlock
WitherSkullBlock>SkullBlock WitherWallSkullBlock>WallSkullBlock WoolCarpetBlock>CarpetBlock
"""
CLASS_PARENT = dict(pair.split(">") for pair in _CLASS_PARENT_SRC.split())


def class_chain(cls):
    """Return (cls, parent, grandparent, ...) up to (excluding) Block."""
    out = [cls]
    while out[-1] in CLASS_PARENT:
        out.append(CLASS_PARENT[out[-1]])
    return tuple(out)


# --------------------------------------------------------------------------------------------------------------
# Per-block exceptions to the generic rules.  Each set was derived from Blocks.java / the block classes of the
# decompiled 26.3 source and then verified state-by-state against the running game (tmp/qa/java/QaExtraDump).
# --------------------------------------------------------------------------------------------------------------
# BlockBehaviour.Properties#isValidSpawn overrides in Blocks.java (default: isFaceSturdy(UP) && lightEmission < 14),
# evaluated for a zombie: Blocks::never (glass family incl. copper grates = TransparentBlock, trapdoors, barrier,
# bedrock, scaffolding), polar-bear-only ice, fire-immune-only magma; Blocks::always for jack o'lantern / redstone lamp.
SPAWN_NEVER_CLASSES = frozenset({"TransparentBlock", "TrapDoorBlock", "IceBlock", "BarrierBlock", "ScaffoldingBlock",
                                 "MagmaBlock"})
SPAWN_NEVER = frozenset({"minecraft:bedrock"})
SPAWN_ALWAYS = frozenset({"minecraft:jack_o_lantern", "minecraft:redstone_lamp"})
# Properties#forceSolidOn / forceSolidOff in Blocks.java (legacy "solid" flag used by signs, banners, cakes, farmland...)
FORCE_SOLID_ON_CLASSES = frozenset({"SignBlock", "AbstractBannerBlock", "BasePressurePlateBlock", "FenceGateBlock", "WallBlock",
                                    "LanternBlock", "ChainBlock", "LightningRodBlock", "AmethystClusterBlock", "BaseCoralPlantTypeBlock"})
FORCE_SOLID_ON = frozenset("minecraft:" + n for n in (
    "cake cobweb conduit dried_ghast moving_piston pointed_dripstone sulfur_spike sculk_vein turtle_egg bell "
    "bamboo_sapling").split())
FORCE_SOLID_OFF = frozenset("minecraft:" + n for n in (
    "azalea flowering_azalea big_dripleaf chorus_flower chorus_plant end_rod ladder scaffolding snow").split())
# BlockBehaviour#isSignalSource overrides (classes whose isSignalSource returns true; RedstoneWireBlock's
# shouldSignal field is true outside of its own power calculation)
SIGNAL_CLASSES = frozenset({"BasePressurePlateBlock", "ButtonBlock", "DaylightDetectorBlock", "DetectorRailBlock", "DiodeBlock",
                            "JukeboxBlock", "LecternBlock", "LeverBlock", "LightningRodBlock", "ObserverBlock", "PoweredBlock",
                            "RedstoneTorchBlock", "RedstoneWireBlock", "SculkSensorBlock", "TargetBlock", "TrappedChestBlock",
                            "TripWireHookBlock"})
# FallingBlock.isFree(state) = isAir || #fire || liquid() || canBeReplaced(): the blocks a sand/gravel/concrete powder/
# anvil block falls through.  canBeReplaced() is Properties#replaceable (not in the registry dump); this list is the
# set of blocks for which the running 26.3 game returns isFree == true (every state of each), dumped headless.
FALL_THROUGH = frozenset("minecraft:" + n for n in (
    "air cave_air void_air water lava bubble_column fire soul_fire light structure_void short_grass tall_grass fern "
    "large_fern bush dead_bush short_dry_grass tall_dry_grass red_shrub seagrass tall_seagrass vine glow_lichen "
    "resin_clump hanging_roots leaf_litter snow nether_sprouts crimson_roots warped_roots").split())
# BlockBehaviour#getLightDampening: 15 for solid render (+ tinted glass), else 0 if propagatesSkylightDown else 1.
# propagatesSkylightDown defaults to "outline shape is not a full cube and no fluid"; the dump only has collision
# shapes, so blocks whose outline is a full cube but whose collision is not are listed here (verified against the
# game's getLightDampening for all 35,723 states, see docs/QA.md).
SKY_TRUE_CLASSES = frozenset({"BambooStalkBlock", "HangingMossBlock", "MossyCarpetBlock", "TransparentBlock", "VineBlock"})
SKY_FALSE_CLASSES = frozenset({"PipeBlock", "ShulkerBoxBlock", "TintedGlassBlock", "LiquidBlock"})
SKY_DRY_CLASSES = frozenset({"BarrierBlock", "CrossCollisionBlock", "GlowLichenBlock", "LightBlock", "VegetationBlock",
                             "WallBlock"})
OUTLINE_FULL = frozenset("minecraft:" + n for n in "cobweb end_gateway honey_block powder_snow sculk_shrieker".split())


# --------------------------------------------------------------------------------------------------------------
# Ground-truth loading
# --------------------------------------------------------------------------------------------------------------
_STATE_RE = re.compile(r"^\s*([a-z0-9_.\-]+:)?([a-z0-9_./\-]+)\s*(?:\[(.*)\])?\s*$")


def parse_state(s):
    """Parse "ns:name[k=v,...]" -> (full_name, {k: v}).  Raises ValueError on malformed syntax."""
    m = _STATE_RE.match(s)
    if not m:
        raise ValueError(f"malformed block state {s!r}")
    ns = m.group(1) or "minecraft:"
    props = {}
    if m.group(3):
        for kv in m.group(3).split(","):
            kv = kv.strip()
            if not kv:
                continue
            if "=" not in kv:
                raise ValueError(f"malformed property {kv!r} in {s!r}")
            k, v = kv.split("=", 1)
            props[k.strip()] = v.strip()
    return ns + m.group(2), props


def _parse_shape(text):
    if not text:
        return ()
    return tuple(tuple(float(v) for v in box.split()) for box in text.split(";"))


class GameData:
    """Registry dump + resolved vanilla tags.  Loaded once per process (see game_data())."""

    def __init__(self, dump, tags, fluid_tags):
        self.dump = dump
        self.blocks = dump["blocks"]
        self.shapes = [_parse_shape(s) for s in dump["shapes"]]
        self.tags = tags              # tag name (with namespace) -> frozenset of block names
        self.fluid_tags = fluid_tags
        self._states = {}

    def tag(self, name):
        """Resolved block tag.  Unknown tags raise KeyError (a silently empty tag would turn a rule off)."""
        if ":" not in name:
            name = "minecraft:" + name
        try:
            return self.tags[name]
        except KeyError:
            raise KeyError(f"block tag {name!r} not found in the 26.3 tag data") from None

    def info(self, s):
        """StateInfo for a state string (cached).  Never raises; invalid states get .valid False."""
        st = self._states.get(s)
        if st is None:
            st = StateInfo(self, s)
            self._states[s] = st
        return st


def _resolve_tags(raw):
    out = {}

    def res(name, stack):
        if name in out:
            return out[name]
        if name in stack:
            return set()
        stack.add(name)
        acc = set()
        for v in raw.get(name, ()):
            if isinstance(v, dict):
                v = v.get("id", "")
            if v.startswith("#"):
                acc |= res(v[1:] if ":" in v else "minecraft:" + v[1:], stack)
            else:
                acc.add(v if ":" in v else "minecraft:" + v)
        stack.discard(name)
        out[name] = frozenset(acc)
        return out[name]

    for n in list(raw):
        res(n, set())
    return out


def _load_tags(kind):
    """Resolved vanilla tags of one registry kind ("block" / "fluid"): {"minecraft:tag": frozenset(names)}.

    Source: the resolved tag cache shipped with the package (``blockwright/data/tags_<version>.json``; keys ``tags``
    for blocks and ``fluid_tags``).  A missing fluid section yields an empty dict (nothing critical needs it)."""
    with open(TAGS_JSON, encoding="utf-8") as f:
        cache = json.load(f)
    key = "tags" if kind == "block" else f"{kind}_tags"
    if key not in cache:
        if kind == "block":
            raise FileNotFoundError(f"vanilla block tags not found in {TAGS_JSON}")
        return {}
    return {k: frozenset(v) for k, v in cache[key].items()}


_GAME = None


def game_data(registry=None):
    """Return the process-wide GameData.  ``registry`` may be a blockwright.registry.Registry (its raw dump dict is reused
    when exposed as .dump/.data/.raw) - anything else is ignored and the dump is read from data/blocks_26.3.json."""
    global _GAME
    if _GAME is None:
        dump = None
        for attr in ("dump", "data", "raw"):
            cand = getattr(registry, attr, None) if registry is not None else None
            if isinstance(cand, dict) and "blocks" in cand and "shapes" in cand:
                dump = cand
                break
        if dump is None:
            with open(BLOCKS_JSON, encoding="utf-8") as f:
                dump = json.load(f)
        _GAME = GameData(dump, _load_tags("block"), _load_tags("fluid"))
    return _GAME


# --------------------------------------------------------------------------------------------------------------
# Shape helpers (face slices exactly like VoxelShape#getFaceShape: boxes crossing the plane 1e-7 inside the face)
# --------------------------------------------------------------------------------------------------------------
_RES = 32  # raster resolution for face coverage tests (shapes use 1/16 and 1/32 steps)
_AX = {"down": 1, "up": 1, "north": 2, "south": 2, "west": 0, "east": 0}
# face plane coordinates (u, v) per axis: Y -> (x, z); Z -> (x, y); X -> (z, y)
_UV = {1: (0, 2), 2: (0, 1), 0: (2, 1)}


def face_raster(boxes, d):
    """Boolean _RES x _RES raster of the face slice of a shape on side d (u, v as in _UV)."""
    a = _AX[d]
    c = 1 - 1e-7 if d in ("up", "south", "east") else 1e-7
    u, v = _UV[a]
    r = np.zeros((_RES, _RES), dtype=bool)
    for b in boxes:
        if b[a] < c < b[a + 3]:
            u1 = int(round(max(0.0, b[u]) * _RES)); u2 = int(round(min(1.0, b[u + 3]) * _RES))
            v1 = int(round(max(0.0, b[v]) * _RES)); v2 = int(round(min(1.0, b[v + 3]) * _RES))
            if u2 > u1 and v2 > v1:
                r[u1:u2, v1:v2] = True
    return r


def _region(u1, u2, v1, v2):
    m = np.zeros((_RES, _RES), dtype=bool)
    m[int(u1 * _RES / 16):int(u2 * _RES / 16), int(v1 * _RES / 16):int(v2 * _RES / 16)] = True
    return m


# SupportType.CENTER: Block.column(2, 0, 10) = box(7,0,7, 9,10,9); RIGID: block minus column(12, 0, 16).
# SupportType#isSupporting tests the 3D support shape against the face slice extruded through the block, so the
# requirement in face coordinates is the projection of that 3D shape along the face axis.
_CENTER_REQ = {1: _region(7, 9, 7, 9), 2: _region(7, 9, 0, 10), 0: _region(7, 9, 0, 10)}
_RIGID_REQ = {1: ~_region(2, 14, 2, 14), 2: np.ones((_RES, _RES), dtype=bool), 0: np.ones((_RES, _RES), dtype=bool)}
_FULL_REQ = np.ones((_RES, _RES), dtype=bool)


def _covers(raster, req):
    return bool(np.all(raster[req]))


class StateInfo:
    """Everything the checks need to know about one block state, derived from the dump + tags + ported rules."""

    def __init__(self, g, s):
        self.s = s
        self.problems = []          # validity problems (strings)
        self.notes = []             # non-fatal validity notes (non-canonical spelling, ...)
        try:
            self.name, self.props = parse_state(s)
        except ValueError as e:
            self.name, self.props = s, {}
            self.problems.append(str(e))
        b = g.blocks.get(self.name)
        if b is None:
            if not self.problems:
                self.problems.append(f"unknown block {self.name!r}")
            b = g.blocks["minecraft:air"]
            self.props = {}
        else:
            if not s.startswith(self.name):
                self.notes.append("namespace missing")
            full = {}
            for k, vals in b["properties"].items():
                if k in self.props:
                    if self.props[k] not in vals:
                        self.problems.append(f"illegal value {k}={self.props[k]} (legal: {','.join(vals)})")
                        full[k] = b["default"][k]
                    else:
                        full[k] = self.props[k]
                else:
                    full[k] = b["default"][k]
                    self.notes.append(f"property {k} missing (default {b['default'][k]} assumed)")
            for k in self.props:
                if k not in b["properties"]:
                    self.problems.append(f"unknown property {k!r}")
            self.props = full
        self.valid = not self.problems
        self.cls = b["class"]
        self.chain = class_chain(self.cls)
        if "phys" in b:
            phys = b["phys"]
        else:
            key = ",".join(f"{k}={self.props[k]}" for k in b["properties"])
            phys = b["phys_by_state"][key]
        sturdy, flags, light, shape = (int(v) for v in phys.split(","))
        self.sturdy = sturdy                       # Block#isFaceSturdy(.., SupportType.FULL) per DIRS bit
        self.can_occlude = bool(flags & 1)
        self.coll_full = bool(flags & 2)           # isCollisionShapeFullBlock
        self.solid_render = bool(flags & 4)
        self.is_air = bool(flags & 8)
        self.emission = light
        self.boxes = g.shapes[shape]               # collision boxes (block units, may exceed 0..1)
        self.top = max((bx[4] for bx in self.boxes), default=0.0)
        self._derive(g)

    def has(self, cls):
        return cls in self.chain

    def p(self, key, default=None):
        return self.props.get(key, default)

    # ---- derived facts -------------------------------------------------------------------------------------
    def _derive(self, g):
        n = self.name
        # fluid: FluidState of the block state
        if n in ("minecraft:water", "minecraft:bubble_column") or self.p("waterlogged") == "true" or \
                n in ("minecraft:kelp", "minecraft:kelp_plant", "minecraft:seagrass", "minecraft:tall_seagrass"):
            self.fluid = "water"
        elif n == "minecraft:lava":
            self.fluid = "lava"
        else:
            self.fluid = ""
        self.support_boxes = self._support_boxes()
        center = rigid = 0
        for i, d in enumerate(DIRS):
            r = face_raster(self.support_boxes, d)
            if _covers(r, _CENTER_REQ[_AX[d]]):
                center |= 1 << i
            if _covers(r, _RIGID_REQ[_AX[d]]):
                rigid |= 1 << i
        self.center = center    # isFaceSturdy(.., SupportType.CENTER)
        self.rigid = rigid      # isFaceSturdy(.., SupportType.RIGID)
        # legacy "solid" (BlockBehaviour.BlockStateBase#calculateSolid)
        live_coral = self.has("CoralPlantBlock") or self.has("CoralFanBlock") or self.has("CoralWallFanBlock")
        if n in FORCE_SOLID_ON or (any(c in FORCE_SOLID_ON_CLASSES for c in self.chain) and not live_coral):
            self.solid = True
        elif n in FORCE_SOLID_OFF or not self.boxes:
            self.solid = False
        else:
            xs = [b for bx in self.boxes for b in (bx[0], bx[3])]
            ys = [b for bx in self.boxes for b in (bx[1], bx[4])]
            zs = [b for bx in self.boxes for b in (bx[2], bx[5])]
            dx, dy, dz = max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)
            self.solid = (dx + dy + dz) / 3.0 >= 0.7291666666666666 or dy >= 1.0
        # Heightmap.Types.MOTION_BLOCKING: tag blocks_motion_in_heightmap or a non-empty fluid
        self.motion_blocking = n in g.tag("blocks_motion_in_heightmap") or bool(self.fluid)
        # isValidSpawn (for a zombie): default isFaceSturdy(UP) && lightEmission < 14 (BlockBehaviour.Properties)
        if n in SPAWN_NEVER or any(c in SPAWN_NEVER_CLASSES for c in self.chain):
            self.valid_spawn = False
        elif n in SPAWN_ALWAYS:
            self.valid_spawn = True
        else:
            self.valid_spawn = bool(self.sturdy & DBIT["up"]) and self.emission < 14
        self.signal = any(c in SIGNAL_CLASSES for c in self.chain)
        # EntityType#isBlockDangerous for a non fire-immune mob (zombie / player pathing)
        burning = n in g.tag("fire") or n in ("minecraft:lava", "minecraft:magma_block", "minecraft:lava_cauldron") or \
            (self.has("CampfireBlock") and self.p("lit") == "true")
        self.dangerous = burning or n in ("minecraft:wither_rose", "minecraft:sweet_berry_bush", "minecraft:cactus",
                                          "minecraft:powder_snow")
        # light: LightEngine#getOpacity = max(1, getLightDampening); dampening 15 for solid render
        if self.solid_render or n == "minecraft:tinted_glass":
            self.opacity = 15
        else:
            self.opacity = 1
        self.light_faces = None
        uses_shape = any(c in LIGHT_SHAPE_CLASSES for c in self.chain)
        if self.has("SlabBlock"):
            uses_shape = self.p("type") != "double"                  # SlabBlock#useShapeForLightOcclusion
        elif self.cls == "PistonBaseBlock":
            uses_shape = self.p("extended") == "true"                # PistonBaseBlock#useShapeForLightOcclusion
        if self.can_occlude and uses_shape:
            # occlusion shape == collision shape for these classes, except snow layers (SHAPES[layers] vs [layers-1])
            occ = self.support_boxes if self.cls == "SnowLayerBlock" else self.boxes
            self.light_faces = tuple(face_raster(occ, d) for d in DIRS)
        # raw light dampening (0 / 1 / 15), used by the sky light model
        if self.opacity == 15:
            self.damp = 15
        elif self.has("LeavesBlock"):
            self.damp = 1                                            # LeavesBlock#getLightDampening
        else:
            ch = set(self.chain)
            if ch & SKY_TRUE_CLASSES:
                sky = True
            elif ch & SKY_FALSE_CLASSES:
                sky = False
            elif ch & SKY_DRY_CLASSES:
                sky = not self.fluid
            elif n in OUTLINE_FULL or (self.has("MultifaceBlock") and not any(self.p(d) == "true" for d in DIRS)):
                sky = False                                          # outline shape is a full cube (a faceless
                                                                     # multiface block falls back to a full cube)
            else:
                sky = not self.coll_full and not self.fluid
            self.damp = 0 if sky else 1
        # collision face slices (enclosure / fluid flow): raster per side and "covers the whole face" flags
        self.coll_faces = tuple(face_raster(self.boxes, d) for d in DIRS)
        self.coll_full_face = tuple(bool(f.all()) for f in self.coll_faces)
        self.full_cube = all(self.coll_full_face)
        # enclosure kind: 2 = solid cell, 1 = partial cell (free space + some sealed faces), 0 = open (see docs/QA.md)
        if self.full_cube:
            self.enc_kind = 2
        elif any(self.coll_full_face):
            self.enc_kind = 1
        else:
            self.enc_kind = 2 if _enclosure_wall(self) else 0

    def _support_boxes(self):
        """getBlockSupportShape: the collision shape unless overridden (26.3 classes cited)."""
        if self.has("LeavesBlock"):
            return ()                                        # LeavesBlock#getBlockSupportShape -> empty
        if self.cls in ("MudBlock", "SoulSandBlock"):
            return ((0, 0, 0, 1, 1, 1),)                     # MudBlock / SoulSandBlock -> Shapes.block()
        if self.has("ShulkerBoxBlock"):
            return ((0, 0, 0, 1, 1, 1),)                     # closed shulker box -> Shapes.block()
        if self.cls == "SnowLayerBlock":                     # SHAPES[layers] = column(16, 0, layers*2)
            return ((0, 0, 0, 1, int(self.p("layers", "1")) * 2 / 16, 1),)
        if self.cls == "FenceGateBlock":                     # open -> empty; else column(16, 4, 5, 24) rotated
            if self.p("open") == "true":
                return ()
            if self.p("facing") in ("north", "south"):
                return ((0, 5 / 16, 6 / 16, 1, 1.5, 10 / 16),)
            return ((6 / 16, 5 / 16, 0, 10 / 16, 1.5, 1),)
        if self.cls == "ChorusFlowerBlock":
            return ((1 / 16, 0, 1 / 16, 15 / 16, 15 / 16, 15 / 16),)
        if self.cls == "CeilingHangingSignBlock":            # getShape: rotation 0/4/8/12 -> column(14,2,0,10)
            rot = int(self.p("rotation", "0"))
            if rot % 4 == 0:
                if rot in (0, 8):
                    return ((1 / 16, 0, 7 / 16, 15 / 16, 10 / 16, 9 / 16),)
                return ((7 / 16, 0, 1 / 16, 9 / 16, 10 / 16, 15 / 16),)
            return ((3 / 16, 0, 3 / 16, 13 / 16, 1, 13 / 16),)
        if self.cls == "WallHangingSignBlock":               # getShape: plank column(16,4,14,16) + column(14,2,0,10)
            if self.p("facing") in ("north", "south"):
                return ((0, 14 / 16, 6 / 16, 1, 1, 10 / 16), (1 / 16, 0, 7 / 16, 15 / 16, 10 / 16, 9 / 16))
            return ((6 / 16, 14 / 16, 0, 10 / 16, 1, 1), (7 / 16, 0, 1 / 16, 9 / 16, 10 / 16, 15 / 16))
        return self.boxes


# classes with useShapeForLightOcclusion() == true (directional light occlusion by shape)
LIGHT_SHAPE_CLASSES = frozenset({"DaylightDetectorBlock", "EnchantingTableBlock", "EndPortalFrameBlock", "FarmlandBlock",
                                 "LecternBlock", "PathBlock", "SculkSensorBlock", "SculkShriekerBlock", "ShelfBlock",
                                 "SlabBlock", "SnowLayerBlock", "StairBlock", "StonecutterBlock", "PistonBaseBlock",
                                 "PistonHeadBlock"})


# --------------------------------------------------------------------------------------------------------------
# World: dense padded grid of palette indices, with implied terrain
# --------------------------------------------------------------------------------------------------------------
class World:
    """The build as it sits in the world.  Grid index = coordinate + 1 (one cell of padding on every side).

    Cells outside the box are air above ``ground`` and terrain at/below it.  Unset cells at y <= ground inside the
    box are terrain too (grass_block at ground, dirt below).  Explicit air entries ("minecraft:air", cave_air,
    void_air) are treated exactly like unset cells: a .litematic stores air as palette entry 0 (blockwright.litematic omits
    it) and Litematica's paste (replace behaviour None / With non-air) leaves the world block in such cells, so air
    can never carve terrain.  They are listed in ``explicit_air`` (reported by the validity check).
    """

    def __init__(self, g, blocks, size, ground):
        self.g = g
        self.size = tuple(int(v) for v in size)
        self.ground = int(ground)
        sx, sy, sz = self.size
        self.shape = (sx + 2, sy + 2, sz + 2)
        # indices 0..2 are reserved for air / implied grass / implied dirt; authored states always get their own
        # palette entries (an authored grass block is not "implied terrain")
        self.palette = [g.info("minecraft:air"), g.info(TERRAIN_TOP), g.info(TERRAIN_FILL)]
        self._pindex = {}
        idx = np.zeros(self.shape, dtype=np.int32)
        ys = np.arange(self.shape[1]) - 1
        idx[:, ys < self.ground, :] = 2
        if -1 <= self.ground <= sy:
            idx[:, self.ground + 1, :] = 1
        self.out_of_box = []
        self.explicit_air = []
        for (x, y, z), s in blocks.items():
            if not (0 <= x < sx and 0 <= y < sy and 0 <= z < sz):
                self.out_of_box.append(((x, y, z), s))
                continue
            i = self._pindex.get(s)
            if i is None:
                st = g.info(s)
                if st.valid and st.is_air:
                    self.explicit_air.append((x, y, z))       # same as unset (see class docstring)
                    continue
                i = len(self.palette)
                self.palette.append(st)
                self._pindex[s] = i
            idx[x + 1, y + 1, z + 1] = i
        self.idx = idx
        self.implied = (idx == 1) | (idx == 2)       # implied natural terrain (never authored)
        self._arrays = {}
        self.cache = {}                               # lazily computed per-world arrays (light, ...)

    # ---- access ---------------------------------------------------------------------------------------------
    def inside(self, x, y, z):
        return -1 <= x <= self.size[0] and -1 <= y <= self.size[1] and -1 <= z <= self.size[2]

    def at(self, x, y, z):
        """StateInfo at world coords (anything beyond the padding is air/terrain by the same rule)."""
        if self.inside(x, y, z):
            return self.palette[self.idx[x + 1, y + 1, z + 1]]
        if y < self.ground:
            return self.palette[2]
        return self.palette[1] if y == self.ground else self.palette[0]

    def is_implied(self, x, y, z):
        if self.inside(x, y, z):
            return bool(self.implied[x + 1, y + 1, z + 1])
        return y <= self.ground

    def arr(self, attr):
        """Per-cell numpy array of a StateInfo attribute (cached)."""
        a = self._arrays.get(attr)
        if a is None:
            vals = [getattr(p, attr) for p in self.palette]
            a = np.asarray(vals)[self.idx]
            self._arrays[attr] = a
        return a

    def mask(self, pred, key=None):
        """Per-cell boolean array of pred(StateInfo) (cached when key given)."""
        if key is not None and key in self._arrays:
            return self._arrays[key]
        lut = np.array([bool(pred(p)) for p in self.palette], dtype=bool)
        m = lut[self.idx]
        if key is not None:
            self._arrays[key] = m
        return m

    def box_cells(self):
        """Iterate authored (non-implied, non-air) cells inside the box: yields (x, y, z, StateInfo)."""
        sel = (self.idx > 2)
        for gx, gy, gz in zip(*np.nonzero(sel)):
            yield int(gx) - 1, int(gy) - 1, int(gz) - 1, self.palette[self.idx[gx, gy, gz]]


def _rel(pos, d, k=1):
    v = DVEC[d]
    return (pos[0] + v[0] * k, pos[1] + v[1] * k, pos[2] + v[2] * k)


# --------------------------------------------------------------------------------------------------------------
# Check 3 helpers: ports of BlockState#canSurvive (26.3) for the blocks a cottage build uses
# --------------------------------------------------------------------------------------------------------------
def _sturdy(st, d):
    return bool(st.sturdy & DBIT[d])


def _center(st, d):
    return bool(st.center & DBIT[d])


def _can_support_center(w, pos, d):
    """Block.canSupportCenter(level, pos, direction): unstable_bottom_center (fence gates) never supports DOWN."""
    st = w.at(*pos)
    if d == "down" and st.name in w.g.tag("unstable_bottom_center"):
        return False
    return _center(st, d)


def _face_full(boxes, d):
    return _covers(face_raster(boxes, d), _FULL_REQ)


def _multiface_can_attach(w, pos, d, direction=None):
    """MultifaceBlock.canAttachTo(level, direction, pos + d, neighbour): the neighbour's support shape OR collision
    shape is full on side ``direction.getOpposite()``.  ``direction`` defaults to ``d`` (the face towards us)."""
    nb = w.at(*_rel(pos, d))
    o = OPP[direction or d]
    return _face_full(nb.support_boxes, o) or _face_full(nb.boxes, o)


def _water_at(w, pos):
    return w.at(*pos).fluid == "water"


def _veg_may_place_on(w, st, below_pos):
    """VegetationBlock#mayPlaceOn and its overrides.  Returns (ok, requirement text)."""
    g = w.g
    b = w.at(*below_pos)
    n = st.name
    tag = None
    if st.has("CropBlock") or st.cls == "PitcherCropBlock":
        tag = "supports_crops"
    elif st.cls in ("StemBlock", "AttachedStemBlock"):
        tag = "supports_melon_stem" if "melon" in n else "supports_pumpkin_stem"
    elif st.has("DryVegetationBlock"):
        tag = "supports_dry_vegetation"
    elif st.cls == "AzaleaBlock":
        tag = "supports_azalea"
    elif st.cls == "NetherSproutsBlock":
        tag = "supports_nether_sprouts"
    elif st.cls == "NetherWartBlock":
        tag = "supports_nether_wart"
    elif st.cls == "WitherRoseBlock":
        tag = "supports_wither_rose"
    elif st.cls in ("NetherFungusBlock", "NetherRootsBlock"):
        tag = "supports_" + n.split(":")[1]
    elif st.cls == "MangrovePropaguleBlock":
        tag = "supports_mangrove_propagule"
    elif st.cls == "LilyPadBlock":
        here = w.at(*_rel(below_pos, "up"))
        ok = (b.fluid == "water" or b.name in g.tag("supports_lily_pad")) and not here.fluid
        return ok, "water (or ice) below and no fluid in its own cell"
    elif st.cls in ("SeagrassBlock", "TallSeagrassBlock"):
        return _sturdy(b, "up") and b.name not in g.tag("cannot_support_seagrass"), "sturdy top face below"
    elif st.cls == "SeaPickleBlock":
        return bool(face_raster(b.boxes, "up").any()) or _sturdy(b, "up"), "a collision top face below"
    elif st.cls == "CactusFlowerBlock":
        return b.name in g.tag("support_override_cactus_flower") or _center(b, "up"), "center support below"
    elif st.cls == "SmallDripleafBlock":
        ok = b.name in g.tag("supports_small_dripleaf") or (
            w.at(*_rel(below_pos, "up")).fluid == "water" and b.name in g.tag("supports_vegetation"))
        return ok, "#supports_small_dripleaf, or #supports_vegetation under water"
    elif st.cls == "MushroomBlock":
        return (b.name in g.tag("overrides_mushroom_light_requirement") or b.solid_render), \
            "#overrides_mushroom_light_requirement or a full opaque block (and light < 13)"
    else:
        tag = "supports_vegetation"
    return b.name in g.tag(tag), "#minecraft:" + tag


def _vine_faces(w, pos, st):
    """VineBlock#getUpdatedState: which faces survive.  Returns dict face -> bool for faces set in the state."""
    out = {}
    above = w.at(*_rel(pos, "up"))
    if st.p("up") == "true":
        # VineBlock#getUpdatedState calls isAcceptableNeighbour(level, above, Direction.DOWN), i.e. canAttachTo tests
        # the block above on its UP face (vanilla quirk, confirmed in game): a vine hangs under a top slab or full
        # block, but not under a bottom slab / bottom stair
        out["up"] = _multiface_can_attach(w, pos, "up", "down")
    for d in HORIZ:
        if st.p(d) == "true":
            ok = _multiface_can_attach(w, pos, d)
            if not ok:
                ok = above.name == st.name and above.p(d) == "true"
            out[d] = ok
    return out


def survives(w, pos, st, light=None):
    """Port of BlockState#canSurvive for one block.

    Returns (ok, why) where ok is True/False, or None when this block type has no survival rule ported (or none
    exists).  ``why`` is a short human explanation of the rule that failed (or the rule checked).
    ``light`` is LevelReader#getRawBrightness(pos, 0) = max(sky light, block light) at ``pos`` (see raw_light());
    None skips the light part of the mushroom / crop rules.
    """
    g = w.g
    x, y, z = pos
    below, above = (x, y - 1, z), (x, y + 1, z)
    bst, ast_ = w.at(*below), w.at(*above)
    c = st.chain
    n = st.name
    facing = st.p("facing")

    if "LanternBlock" in c:                                            # LanternBlock#canSurvive
        if st.p("hanging") == "true":
            return _can_support_center(w, above, "down"), "hanging lantern needs center support above (Block.canSupportCenter)"
        return _can_support_center(w, below, "up"), "standing lantern needs center support below (Block.canSupportCenter)"
    if "RedstoneWallTorchBlock" in c or "WallTorchBlock" in c:          # WallTorchBlock.canSurvive(level,pos,facing)
        sp = _rel(pos, OPP[facing])
        return _sturdy(w.at(*sp), facing), f"wall torch needs a sturdy {facing} face on the block behind it at {sp}"
    if "BaseTorchBlock" in c:                                          # BaseTorchBlock#canSurvive
        return _can_support_center(w, below, "up"), "torch needs center support below (Block.canSupportCenter)"
    if st.cls == "CandleBlock":                                        # CandleBlock#canSurvive
        return _can_support_center(w, below, "up"), "candle needs center support below"
    if st.cls in ("CandleCakeBlock", "CakeBlock", "BannerBlock", "StandingSignBlock"):
        return bst.solid, "needs a solid block below (BlockState#isSolid)"       # cake/banner/sign canSurvive
    if st.cls in ("WallSignBlock", "WallBannerBlock"):
        sp = _rel(pos, OPP[facing])
        return w.at(*sp).solid, f"needs a solid block behind it at {sp}"
    if st.cls == "CeilingHangingSignBlock":                            # CeilingHangingSignBlock#canSurvive
        return _center(ast_, "down"), "hanging sign needs center support above"
    if st.cls == "WallHangingSignBlock":
        return True, ""                                                # no canSurvive override -> always survives
    if st.cls == "MossyCarpetBlock":                                   # MossyCarpetBlock#canSurvive
        if st.p("bottom") == "true":
            return not bst.is_air, "pale moss carpet needs a non-air block below"
        return bst.name == n and bst.p("bottom") == "true", "pale moss carpet side part needs its base below"
    if "CarpetBlock" in c:                                             # CarpetBlock#canSurvive: !isEmptyBlock(below)
        return not bst.is_air, "carpet needs a non-air block below"
    if "DoorBlock" in c:                                               # DoorBlock#canSurvive
        if st.p("half") == "lower":
            return _sturdy(bst, "up"), "door needs a sturdy top face below"
        return bst.name == n, "upper door half needs the lower half below"
    if st.cls == "LeafLitterBlock":                                    # LeafLitterBlock#canSurvive
        return _sturdy(bst, "up"), "leaf litter needs a sturdy top face below"
    if st.cls == "MangrovePropaguleBlock" and st.p("hanging") == "true":
        return ast_.name in g.tag("supports_hanging_mangrove_propagule"), "hanging propagule needs mangrove leaves above"
    if "DoublePlantBlock" in c and st.p("half") == "upper":            # DoublePlantBlock#canSurvive (upper)
        return bst.name == n and bst.p("half") == "lower", "upper half needs the lower half below"
    if st.cls == "MushroomBlock":                                      # MushroomBlock#canSurvive
        if bst.name in g.tag("overrides_mushroom_light_requirement"):
            return True, ""
        if light is not None and light >= 13:
            return False, ("mushroom needs light < 13 (sky or block light; open sky is 15) unless it stands on "
                           "mycelium/podzol/nylium (#overrides_mushroom_light_requirement)")
        ok, why = _veg_may_place_on(w, st, below)
        return ok, "mushroom needs " + why
    if (st.has("CropBlock") or (st.cls == "PitcherCropBlock" and st.p("half") == "lower")) \
            and light is not None and light < 8:                       # CropBlock#canSurvive: hasSufficientLight
        return False, "crop needs light >= 8 (sky or block light) - add a light source or open it to the sky"
    if st.cls == "SugarCaneBlock":                                     # SugarCaneBlock#canSurvive
        if bst.name == n:
            return True, ""
        if bst.name in g.tag("supports_sugar_cane"):
            for d in HORIZ:
                nb = w.at(*_rel(below, d))
                if nb.fluid == "water" or nb.name in g.tag("supports_sugar_cane_adjacently"):
                    return True, ""
        return False, "sugar cane needs sugar cane below, or #supports_sugar_cane soil with water beside that soil"
    if "VegetationBlock" in c:                                         # VegetationBlock#canSurvive -> mayPlaceOn(below)
        ok, why = _veg_may_place_on(w, st, below)
        return ok, f"{n.split(':')[1]} needs {why} below (found {bst.name.split(':')[1]})"
    if st.cls == "VineBlock":                                          # VineBlock#canSurvive
        faces = _vine_faces(w, pos, st)
        return any(faces.values()), ("vine needs a side face against a full block face (or the same face on a vine "
                                     "directly above), or up=true under a block whose TOP face is full (full block or "
                                     "top slab - a bottom slab/stair above does not hold it)")
    if "MultifaceBlock" in c:                                          # MultifaceBlock#canSurvive
        faces = [d for d in DIRS if st.p(d) == "true"]
        bad = [d for d in faces if not _multiface_can_attach(w, pos, d)]
        return bool(faces) and not bad, f"faces {bad or faces} need a full block face to attach to"
    if "GrowingPlantBlock" in c:                                       # GrowingPlantBlock#canSurvive
        grow = "up" if n.startswith(("minecraft:twisting_vines", "minecraft:kelp")) else "down"
        ap = _rel(pos, OPP[grow])
        at = w.at(*ap)
        if n.startswith("minecraft:kelp") and at.name in g.tag("cannot_support_kelp"):
            return False, "kelp cannot attach to this block"
        base = n[:-6] if n.endswith("_plant") else n
        ok = at.name in (base, base + "_plant") or _sturdy(at, grow)
        return ok, f"needs the same plant or a sturdy {grow} face at {ap}"
    if st.cls == "SporeBlossomBlock":                                  # SporeBlossomBlock#canSurvive
        return _can_support_center(w, above, "down") and not _water_at(w, pos), "spore blossom needs center support above, no water"
    if st.cls == "HangingRootsBlock":                                  # HangingRootsBlock#canSurvive
        return _sturdy(ast_, "down"), "hanging roots need a sturdy bottom face above"
    if st.cls == "HangingMossBlock":                                   # HangingMossBlock#canStayAtPosition
        return _multiface_can_attach(w, pos, "up") or ast_.name == n, "pale hanging moss needs a full face or moss above"
    if st.cls == "ShelfMushroomBlock":                                 # ShelfMushroomBlock#canSurvive
        sp = _rel(pos, OPP[facing])
        return _sturdy(w.at(*sp), facing), f"shelf mushroom needs a sturdy {facing} face at {sp}"
    if st.cls == "GrindstoneBlock":
        return True, ""                                                # GrindstoneBlock#canSurvive -> true
    if "FaceAttachedHorizontalDirectionalBlock" in c:                  # buttons, levers
        face = st.p("face")
        conn = "down" if face == "ceiling" else "up" if face == "floor" else facing
        d = OPP[conn]
        sp = _rel(pos, d)
        return _sturdy(w.at(*sp), OPP[d]), f"needs a sturdy {OPP[d]} face at {sp}"
    if "BasePressurePlateBlock" in c:                                  # BasePressurePlateBlock#canSurvive
        return bool(bst.rigid & DBIT["up"]) or _center(bst, "up"), "pressure plate needs rigid or center support below"
    if st.cls == "BellBlock":                                          # BellBlock#canSurvive
        att = st.p("attachment")
        conn = "up" if att == "floor" else "down" if att == "ceiling" else OPP[facing]
        d = OPP[conn]
        if d == "up":
            return _can_support_center(w, above, "down"), "ceiling bell needs center support above"
        sp = _rel(pos, d)
        return _sturdy(w.at(*sp), OPP[d]), f"bell needs a sturdy {OPP[d]} face at {sp}"
    if st.cls == "LadderBlock":                                        # LadderBlock#canSurvive
        sp = _rel(pos, OPP[facing])
        return _sturdy(w.at(*sp), facing), f"ladder needs a sturdy {facing} face on the block behind it at {sp}"
    if "BaseRailBlock" in c:                                           # BaseRailBlock#canSurvive
        return bool(bst.rigid & DBIT["up"]), "rail needs rigid support below"
    if st.cls == "RedstoneWireBlock":
        return _sturdy(bst, "up") or bst.name == "minecraft:hopper", "redstone needs a sturdy top face below"
    if "DiodeBlock" in c:
        return bool(bst.rigid & DBIT["up"]), "repeater/comparator needs rigid support below"
    if st.cls == "TripWireHookBlock":
        sp = _rel(pos, OPP[facing])
        return _sturdy(w.at(*sp), facing), f"tripwire hook needs a sturdy {facing} face at {sp}"
    if st.cls == "AmethystClusterBlock":
        sp = _rel(pos, OPP[facing])
        return _sturdy(w.at(*sp), facing), f"needs a sturdy {facing} face at {sp}"
    if st.cls == "CocoaBlock":                                         # CocoaBlock#canSurvive
        sp = _rel(pos, facing)
        return w.at(*sp).name in g.tag("supports_cocoa"), f"cocoa needs a jungle log at {sp}"
    if "BaseCoralWallFanBlock" in c:
        sp = _rel(pos, OPP[facing])
        return _sturdy(w.at(*sp), facing), f"wall coral needs a sturdy {facing} face at {sp}"
    if "BaseCoralPlantTypeBlock" in c:
        return _sturdy(bst, "up"), "coral needs a sturdy top face below"
    if st.cls == "ScaffoldingBlock":                                   # ScaffoldingBlock.getDistance < 7
        dist = 7
        if bst.name == n:
            dist = int(bst.p("distance"))
        elif _sturdy(bst, "up"):
            dist = 0
        if dist:
            for d in HORIZ:
                nb = w.at(*_rel(pos, d))
                if nb.name == n:
                    dist = min(dist, int(nb.p("distance")) + 1)
        return dist < 7, "scaffolding too far from support (distance 7)"
    if st.cls == "SnowLayerBlock":                                     # SnowLayerBlock#canSurvive
        if bst.name in g.tag("cannot_support_snow_layer"):
            return False, "snow cannot rest on this block"
        if bst.name in g.tag("support_override_snow_layer"):
            return True, ""
        return _face_full(bst.boxes, "up") or (bst.name == n and bst.p("layers") == "8"), "snow needs a full top face below"
    if st.cls == "FarmlandBlock":                                      # FarmlandBlock#canSurvive
        return (not ast_.solid) or ast_.name in g.tag("maintains_farmland"), "farmland turns to dirt under a solid block"
    if st.cls == "PathBlock":                                          # PathBlock#canSurvive
        return (not ast_.solid) or ast_.has("FenceGateBlock"), "dirt path turns to dirt under a solid block"
    if st.cls == "CactusBlock":                                        # CactusBlock#canSurvive
        for d in HORIZ:
            nb = w.at(*_rel(pos, d))
            if nb.solid or nb.fluid == "lava":
                return False, f"cactus breaks next to a solid block ({d})"
        ok = (bst.name == n or bst.name in g.tag("supports_cactus")) and ast_.cls != "LiquidBlock"
        return ok, "cactus needs cactus or sand below"
    if st.cls in ("BambooSaplingBlock", "BambooStalkBlock"):
        return bst.name in g.tag("supports_bamboo"), "bamboo needs #supports_bamboo below"
    if st.cls == "BigDripleafBlock":
        return bst.name in (n, "minecraft:big_dripleaf_stem") or bst.name in g.tag("supports_big_dripleaf"), "dripleaf support"
    if st.cls == "BigDripleafStemBlock":
        ok = (bst.name == n or bst.name in g.tag("supports_big_dripleaf")) and ast_.name in (n, "minecraft:big_dripleaf")
        return ok, "dripleaf stem needs support below and dripleaf above"
    if st.cls in ("FireBlock", "SoulFireBlock", "ChorusFlowerBlock", "ChorusPlantBlock", "FrogspawnBlock",
                  "BubbleColumnBlock", "PointedDripstoneBlock", "SulfurSpikeBlock"):
        return None, "survival rule not ported for this block"
    return None, ""


def falls(w, pos, st):
    """FallingBlock / BrushableBlock#tick: a gravity block (sand, red sand, gravel, concrete powder, anvils, dragon
    egg, suspicious sand/gravel) falls when the block below isFree (air, fire, liquid or a replaceable block such as
    short grass, ferns, vines, snow layers).  onPlace schedules that tick, so it happens right after pasting.
    Returns the block below (StateInfo) when the block will fall, else None."""
    if not (st.has("FallingBlock") or st.has("BrushableBlock")):
        return None
    b = w.at(pos[0], pos[1] - 1, pos[2])
    return b if b.name in FALL_THROUGH else None


_FLUID_SOURCE_NAMES = frozenset({"minecraft:kelp", "minecraft:kelp_plant", "minecraft:seagrass", "minecraft:tall_seagrass",
                                 "minecraft:bubble_column"})


def _fluid_source(st):
    """FluidState#isSource for the fluid in a block state."""
    if not st.fluid:
        return False
    if st.name in ("minecraft:water", "minecraft:lava"):
        return st.p("level") == "0"
    return True                                       # waterlogged blocks, kelp, seagrass, bubble columns


def fluid_escape(w, pos, st):
    """FlowingFluid#spread, reduced to "will the fluid in this cell move into a neighbour that has none?".

    A fluid spreads down, else sideways, into a neighbour that canHoldAnyFluid (#washed_away_by_fluids: air, plants,
    torches, carpets, ...; waterloggable blocks only take a *source*, never flowing water) when the shared face is
    not closed (FlowingFluid#canPassThroughWall: neither collision shape is a full cube and the two face slices do
    not cover the face together).  Returns (direction, neighbour pos, neighbour StateInfo) or None."""
    if not st.fluid:
        return None
    washed = w.g.tag("washed_away_by_fluids")
    for d in ("down", "north", "south", "west", "east"):
        q = _rel(pos, d)
        nb = w.at(*q)
        if nb.fluid or nb.name not in washed:
            continue
        if nb.full_cube or st.full_cube:
            continue
        k, ko = DIRS.index(d), DIRS.index(OPP[d])
        if (st.coll_faces[k] | nb.coll_faces[ko]).all():
            continue
        return d, q, nb
    return None


def pair_problem(w, pos, st):
    """Double-block consistency (DoorBlock / DoublePlantBlock / AbstractBedBlock #updateShape turn orphans to air)."""
    n = st.name
    if "DoorBlock" in st.chain or ("DoublePlantBlock" in st.chain and st.p("half") in ("lower", "upper")):
        other = _rel(pos, "up" if st.p("half") == "lower" else "down")
        o = w.at(*other)
        want = "upper" if st.p("half") == "lower" else "lower"
        if o.name != n or o.p("half") != want:
            return f"{st.p('half')} half without its {want} half at {other}"
        if "DoorBlock" in st.chain:
            for k in ("facing", "hinge", "open"):
                if o.p(k) != st.p(k):
                    return f"door halves disagree on {k} ({st.p(k)} vs {o.p(k)} at {other})"
        return None
    if "AbstractBedBlock" in st.chain:
        part, f = st.p("part"), st.p("facing")
        other = _rel(pos, f if part == "foot" else OPP[f])
        o = w.at(*other)
        if o.name != n or o.p("part") == part or o.p("facing") != f:
            return f"bed {part} without matching {'head' if part == 'foot' else 'foot'} at {other}"
    return None


# --------------------------------------------------------------------------------------------------------------
# Generic grid helpers
# --------------------------------------------------------------------------------------------------------------
def _dilate6(m):
    out = m.copy()
    out[1:, :, :] |= m[:-1, :, :]
    out[:-1, :, :] |= m[1:, :, :]
    out[:, 1:, :] |= m[:, :-1, :]
    out[:, :-1, :] |= m[:, 1:, :]
    out[:, :, 1:] |= m[:, :, :-1]
    out[:, :, :-1] |= m[:, :, 1:]
    return out


def _dilate26(m):
    out = m.copy()
    for ax in range(3):
        t = out.copy()
        sl1 = [slice(None)] * 3
        sl2 = [slice(None)] * 3
        sl1[ax], sl2[ax] = slice(1, None), slice(None, -1)
        t[tuple(sl1)] |= out[tuple(sl2)]
        t[tuple(sl2)] |= out[tuple(sl1)]
        out = t
    return out


def _flood(seed, passable):
    """6-connected flood fill of ``passable`` cells starting from ``seed`` (numpy, frontier based)."""
    reach = seed & passable
    front = reach
    while front.any():
        nxt = _dilate6(front) & passable & ~reach
        reach |= nxt
        front = nxt
    return reach


def _border(shape):
    b = np.zeros(shape, dtype=bool)
    b[0, :, :] = b[-1, :, :] = True
    b[:, 0, :] = b[:, -1, :] = True
    b[:, :, 0] = b[:, :, -1] = True
    return b


def _components(mask):
    """6-connected components of a (small) boolean mask -> list of lists of grid index tuples."""
    seen = np.zeros_like(mask)
    comps = []
    X, Y, Z = mask.shape
    for start in zip(*np.nonzero(mask)):
        start = tuple(int(v) for v in start)
        if seen[start]:
            continue
        seen[start] = True
        comp = [start]
        dq = deque([start])
        while dq:
            cx, cy, cz = dq.popleft()
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                n = (cx + dx, cy + dy, cz + dz)
                if 0 <= n[0] < X and 0 <= n[1] < Y and 0 <= n[2] < Z and mask[n] and not seen[n]:
                    seen[n] = True
                    comp.append(n)
                    dq.append(n)
        comps.append(comp)
    return comps


def _w(gpos):
    """Grid index -> world coordinates."""
    return (int(gpos[0]) - 1, int(gpos[1]) - 1, int(gpos[2]) - 1)


def _g(pos):
    return (int(pos[0]) + 1, int(pos[1]) + 1, int(pos[2]) + 1)


def _short(name):
    return name.split(":", 1)[1] if name.startswith("minecraft:") else name


class _Issues:
    def __init__(self):
        self.items = []

    def add(self, check, severity, message, pos=None, block=None, **extra):
        it = {"check": check, "severity": severity, "message": message}
        if pos is not None:
            it["pos"] = [int(v) for v in pos]
        if block is not None:
            it["block"] = block
        it.update(extra)
        self.items.append(it)


# --------------------------------------------------------------------------------------------------------------
# Check 1: validity
# --------------------------------------------------------------------------------------------------------------
def check_validity(w, blocks, iss):
    by_state = {}
    for pos, s in blocks.items():
        by_state.setdefault(s, []).append(pos)
    n_bad = 0
    for s, poss in sorted(by_state.items(), key=lambda kv: kv[0]):
        st = w.g.info(s)
        if st.problems:
            n_bad += len(poss)
            iss.add("validity", "error", f"illegal state {s!r}: {'; '.join(st.problems)} ({len(poss)} cells)",
                    pos=sorted(poss)[0], block=s, count=len(poss))
        elif st.notes:
            iss.add("validity", "warn", f"non-canonical state {s!r}: {'; '.join(st.notes)} ({len(poss)} cells)",
                    pos=sorted(poss)[0], block=s, count=len(poss))
    if w.explicit_air:
        low = sorted(p for p in w.explicit_air if p[1] <= w.ground)
        if low:
            iss.add("validity", "warn", f"{len(low)} explicit air cell(s) at or below ground (y <= {w.ground}), e.g. {low[0]}: "
                    f"air cannot carve terrain - the .litematic stores air as 'nothing' and Litematica's paste keeps "
                    f"the world block there, so these cells stay grass/dirt (QA models them that way)",
                    pos=low[0], count=len(low), positions=[list(p) for p in low[:50]])
        else:
            iss.add("validity", "info", f"{len(w.explicit_air)} explicit air cell(s) stored above ground (no effect: "
                    f"air is never written to the schematic)", pos=sorted(w.explicit_air)[0], count=len(w.explicit_air))
    for pos, s in w.out_of_box:
        iss.add("validity", "error", f"block outside the bounding box {w.size}", pos=pos, block=s)
    return {"distinct_states": len(by_state), "blocks": len(blocks), "illegal_cells": n_bad}


# --------------------------------------------------------------------------------------------------------------
# Check 2: floating blocks
# --------------------------------------------------------------------------------------------------------------
def check_floating(w, iss):
    nonair = ~w.mask(lambda p: p.is_air, "is_air")
    grounded = _flood(w.implied & nonair, nonair)
    floating = nonair & ~grounded & ~w.implied
    comps = _components(floating)
    comps.sort(key=lambda c: -len(c))
    for comp in comps[:50]:
        arr = np.array(comp)
        lo, hi = arr.min(axis=0), arr.max(axis=0)
        names = {}
        for c in comp:
            n = w.palette[w.idx[c]].name
            names[n] = names.get(n, 0) + 1
        sample = ", ".join(f"{_short(n)} x{k}" for n, k in sorted(names.items(), key=lambda kv: -kv[1])[:5])
        iss.add("floating", "error", f"{len(comp)} block(s) not connected to the ground (bbox {_w(lo)}..{_w(hi)}): {sample}",
                pos=_w(comp[0]), bbox=[list(_w(lo)), list(_w(hi))], count=len(comp))
    if len(comps) > 50:
        rest = comps[50:]
        iss.add("floating", "error", f"... and {len(rest)} more floating component(s) ({sum(len(c) for c in rest)} blocks) "
                f"not listed individually", pos=_w(rest[0][0]), count=len(rest))
    return {"floating_components": len(comps), "floating_blocks": int(sum(len(c) for c in comps))}


# --------------------------------------------------------------------------------------------------------------
# Check 3: support rules (+ double-block pairs)
# --------------------------------------------------------------------------------------------------------------
def _needs_light(st):
    return st.cls == "MushroomBlock" or st.has("CropBlock") or st.cls == "PitcherCropBlock"


def _leaf_distance(w):
    """LeavesBlock#updateDistance at steady state: 0 at #prevents_nearby_leaf_decay (logs/wood), +1 per leaves step,
    7 = unconnected."""
    leaf = w.mask(lambda p: p.has("LeavesBlock"), "leaves")
    tag = w.g.tag("prevents_nearby_leaf_decay")
    src = w.mask(lambda p: p.name in tag, "leaf_anchor")
    dist = np.full(w.shape, 7, dtype=np.int8)
    dist[src] = 0
    front = src
    for d in range(1, 7):
        front = _dilate6(front) & leaf & (dist == 7)
        dist[front] = d
    return dist


def _tick_changes(w, iss):
    """Blocks that random ticks will visibly change after pasting (see docs/QA.md, support):
    leaves decay, snow layers / ice melt next to light, bare dry farmland turns to dirt, saplings grow into trees."""
    pal = w.palette
    present = [p for p in pal[3:] if p.valid]
    out = {"decaying_leaves": 0, "melting": 0}
    if any(p.has("LeavesBlock") and p.p("persistent") == "false" for p in present):
        dist = _leaf_distance(w)
        stored7 = w.mask(lambda p: p.has("LeavesBlock") and p.p("persistent") == "false" and p.p("distance") == "7")
        loose = w.mask(lambda p: p.has("LeavesBlock") and p.p("persistent") == "false")
        bad = stored7 | (loose & (dist == 7))
        if bad.any():
            cells = sorted(_w(c) for c in zip(*np.nonzero(bad)))
            out["decaying_leaves"] = len(cells)
            iss.add("support", "error", f"{len(cells)} non-persistent leaves will decay (distance=7 stored, or no log/wood "
                    f"within 6 leaves), e.g. {cells[0]} - use persistent=true for decorative leaves (LeavesBlock#randomTick)",
                    pos=cells[0], count=len(cells), positions=[list(c) for c in cells[:50]])
    if any(p.cls == "SnowLayerBlock" or p.has("IceBlock") for p in present):
        L = block_light(w)
        limit = np.array([11 if p.cls == "SnowLayerBlock" else 11 - p.damp if p.has("IceBlock") else 99 for p in pal])[w.idx]
        melt = (L > limit) & ~w.implied
        if melt.any():
            cells = sorted(_w(c) for c in zip(*np.nonzero(melt)))
            out["melting"] = len(cells)
            iss.add("support", "error", f"{len(cells)} snow layer / ice block(s) melt from block light (snow: > 11, ice: "
                    f"> 11 - dampening), e.g. {cells[0]} - move the light source away", pos=cells[0], count=len(cells),
                    positions=[list(c) for c in cells[:50]])
    if any(p.cls == "FarmlandBlock" for p in present):
        farm = w.mask(lambda p: p.cls == "FarmlandBlock", "farmland")
        water = w.mask(lambda p: p.fluid == "water", "water")
        keep = np.roll(w.mask(lambda p: p.name in w.g.tag("maintains_farmland"), "keeps_farmland"), -1, axis=1)
        keep[:, -1, :] = False
        # FarmlandBlock#isNearWater: any water within x/z +-4, y +0..+1
        near = np.zeros_like(water)
        X, Y, Z = w.shape
        wp = np.pad(water, 4)
        for dx in range(-4, 5):
            for dz in range(-4, 5):
                for dy in (0, 1):
                    near |= wp[4 + dx:4 + dx + X, 4 + dy:4 + dy + Y, 4 + dz:4 + dz + Z]
        dry = farm & ~near & ~keep
        if dry.any():
            cells = sorted(_w(c) for c in zip(*np.nonzero(dry)))
            iss.add("support", "warn", f"{len(cells)} farmland block(s) without a crop on top and no water within 4 blocks "
                    f"dry out and turn to dirt, e.g. {cells[0]} - plant a crop or add water", pos=cells[0],
                    count=len(cells), positions=[list(c) for c in cells[:50]])
    if any(p.has("SaplingBlock") for p in present):
        sap = w.mask(lambda p: p.has("SaplingBlock"), "sapling")
        lit = np.roll(raw_light(w), -1, axis=1) >= 9
        grow = sap & lit
        if grow.any():
            cells = sorted(_w(c) for c in zip(*np.nonzero(grow)))
            iss.add("support", "warn", f"{len(cells)} sapling(s)/propagule(s) in light >= 9 grow into full trees, e.g. "
                    f"{cells[0]} - use a bush, a potted sapling or azalea for a small shrub", pos=cells[0],
                    count=len(cells), positions=[list(c) for c in cells[:50]])
    return out


def check_support(w, iss):
    checked = failed = 0
    unported = {}
    groups = {}
    fall_groups = {}
    escapes = []
    flowing = []
    light = raw_light(w) if any(_needs_light(p) for p in w.palette[3:]) else None
    for x, y, z, st in w.box_cells():
        if not st.valid or st.is_air:
            continue
        pos = (x, y, z)
        lv = int(light[x + 1, y + 1, z + 1]) if light is not None and _needs_light(st) else None
        ok, why = survives(w, pos, st, lv)
        if ok is None:
            if why:
                unported[st.name] = unported.get(st.name, 0) + 1
        else:
            checked += 1
            if not ok:
                failed += 1
                groups.setdefault((st.name, why.split(" at (")[0]), []).append((pos, why))
        if st.cls == "VineBlock":
            faces = _vine_faces(w, pos, st)
            lost = [d for d, okf in faces.items() if not okf]
            if lost and any(faces.values()):
                iss.add("support", "warn", f"vine faces {lost} have nothing to cling to and will be removed on the next "
                        f"block update", pos=pos, block=st.s)
        if st.cls == "WallHangingSignBlock":
            f = st.p("facing")
            okp = False
            for side in (_rotate_cw(f), _rotate_ccw(f)):
                nb = w.at(*_rel(pos, side))
                if nb.name in w.g.tag("wall_hanging_signs"):
                    okp = okp or _axis(nb.p("facing")) == _axis(f)
                else:
                    okp = okp or _sturdy(nb, OPP[side])
            if not okp:
                iss.add("support", "info", "wall hanging sign has no sturdy block beside it (it survives, but could not "
                        "be placed by hand)", pos=pos, block=st.s)
        pp = pair_problem(w, pos, st) if ok is not False else None
        if pp:
            iss.add("support", "error", f"{_short(st.name)}: {pp} - the game turns it into air on the next update",
                    pos=pos, block=st.s)
        fb = falls(w, pos, st)
        if fb is not None:
            fall_groups.setdefault((st.name, fb.name), []).append(pos)
        if st.fluid:
            if not _fluid_source(st):
                flowing.append(pos)
            esc = fluid_escape(w, pos, st)
            if esc is not None:
                escapes.append((pos, st, esc))
    for (name, why), lst in sorted(groups.items()):
        poss = [p for p, _ in lst]
        more = f" (+{len(lst) - 1} more)" if len(lst) > 1 else ""
        iss.add("support", "error", f"{_short(name)} at {poss[0]}{more} cannot survive: {lst[0][1]}",
                pos=poss[0], block=name, count=len(lst), positions=[list(p) for p in poss[:50]])
    for (name, below), poss in sorted(fall_groups.items()):
        poss.sort()
        more = f" (+{len(poss) - 1} more)" if len(poss) > 1 else ""
        iss.add("support", "error", f"{_short(name)} at {poss[0]}{more} falls: gravity block over {_short(below)} "
                f"(FallingBlock.isFree - air, liquids and replaceable plants/snow do not hold it)",
                pos=poss[0], block=name, count=len(poss), positions=[list(p) for p in poss[:50]])
    if escapes:
        by = {}
        for pos, st, (d, q, nb) in escapes:
            by.setdefault(st.fluid, []).append((pos, d, q, nb))
        for fl, lst in sorted(by.items()):
            pos, d, q, nb = lst[0]
            more = f" (+{len(lst) - 1} more cells)" if len(lst) > 1 else ""
            iss.add("support", "error", f"{fl} at {pos}{more} is not contained: it flows {d} into {q} "
                    f"({_short(nb.name)}) - a source starts flowing right after pasting (LiquidBlock#onPlace), a "
                    f"waterlogged block at its next block update; wall it in with full faces or drop waterlogged=true",
                    pos=pos, count=len(lst), positions=[list(p) for p, _, _, _ in lst[:50]])
    if flowing:
        iss.add("support", "warn", f"{len(flowing)} flowing (level != 0) fluid cell(s), e.g. {flowing[0]}: flowing water/lava "
                f"is recomputed on its first tick and drains away unless a source feeds it", pos=flowing[0],
                count=len(flowing))
    ticks = _tick_changes(w, iss)
    for name, k in sorted(unported.items()):
        iss.add("support", "info", f"survival rule for {_short(name)} not ported - {k} block(s) unchecked", block=name, count=k)
    return {"checked": checked, "failed": failed, "unchecked_types": len(unported),
            "falling": int(sum(len(v) for v in fall_groups.values())), "fluid_escapes": len(escapes), **ticks}


def _axis(d):
    return "x" if d in ("east", "west") else "z" if d in ("north", "south") else "y"


def _rotate_cw(d):
    return {"north": "east", "east": "south", "south": "west", "west": "north"}[d]


def _rotate_ccw(d):
    return {"north": "west", "west": "south", "south": "east", "east": "north"}[d]


# --------------------------------------------------------------------------------------------------------------
# Check 4: enclosure (leaks) + rain
# --------------------------------------------------------------------------------------------------------------
def _enclosure_wall(st):
    """True if the cell blocks air / rain / small mobs for the enclosure flood fill (see docs/QA.md)."""
    if not st.boxes:
        return False
    if st.has("DoorBlock") or st.has("TrapDoorBlock") or st.has("FenceGateBlock"):
        return st.p("open") != "true"
    if st.has("CrossCollisionBlock") or st.cls == "WallBlock":
        return True                                     # fences, panes, bars, walls
    if st.top <= 0.1875 + EPS:
        return False                                    # carpets, lily pads, ... (low and flat)
    xs = [b for bx in st.boxes for b in (bx[0], bx[3])]
    zs = [b for bx in st.boxes for b in (bx[2], bx[5])]
    if (max(xs) - min(xs)) * (max(zs) - min(zs)) < 0.5 - EPS:
        return False                                    # small decor: lanterns, pots, candles, chains, skulls, ladders
    return True


def _over_hearth(w, wall, hearth, c, depth=8):
    """Grid cell c sits in an open vertical shaft rising from a fire/campfire (a chimney flue)."""
    x, y, z = c
    for yy in range(y - 1, max(y - 1 - depth, -1), -1):
        if w.palette[w.idx[x, yy, z]].name in hearth:
            return True
        if wall[x, yy, z]:
            return False
    return False


def _pick_breach(path, wall, closed, shape, solid):
    """Name the hole on a leak path: among the path cells (marker and box border excluded) prefer those the 3x3x3
    closing fills (and that are not solid), then take the one with the most walls around it across the direction
    of travel; ties go to the cell nearest the outside."""
    inner = list(range(1, len(path) - 1))
    if not inner:
        return path[-1]
    cand = [k for k in inner if closed[path[k]] and not solid[path[k]]] or inner
    best_k, best = cand[-1], -1
    for k in cand:
        ax = int(np.nonzero(np.subtract(path[k + 1], path[k - 1]))[0][0]) if any(np.subtract(path[k + 1], path[k - 1])) else 1
        c = path[k]
        n_w = 0
        for oax in range(3):
            if oax == ax:
                continue
            for sgn in (-1, 1):
                q = list(c)
                q[oax] += sgn
                if 0 <= q[oax] < shape[oax] and wall[tuple(q)]:
                    n_w += 1
        if n_w >= best:
            best, best_k = n_w, k
    return path[best_k]


def _enclosure_axes(w):
    """Open faces between neighbouring cells for air / rain / small mobs (see docs/QA.md, enclosure)."""
    if "enc_axes" not in w.cache:
        solid = np.array([p.enc_kind == 2 for p in w.palette], dtype=bool)
        w.cache["enc_axes"] = _axis_open(w, lambda p: None if p.enc_kind == 2 else p.coll_faces, closed_lut=solid)
    return w.cache["enc_axes"]


def _flood_edges(seed, axes, allowed=None):
    """Flood fill from ``seed`` across the open faces ``axes`` (from _axis_open), optionally limited to ``allowed``."""
    reach = seed.copy() if allowed is None else seed & allowed
    front = reach.copy()
    while front.any():
        nxt = np.zeros_like(reach)
        for lo, hi, ok in axes:
            nxt[hi] |= front[lo] & ok
            nxt[lo] |= front[hi] & ok
        nxt &= ~reach
        if allowed is not None:
            nxt &= allowed
        reach |= nxt
        front = nxt
    return reach


def _plus_edges(axes, shape):
    """Flattened full-shape copies of the axis edge arrays: plus[ax][cell] = face between cell and cell+1 is open."""
    out = []
    for lo, hi, ok in axes:
        full = np.zeros(shape, dtype=bool)
        full[lo] = ok
        out.append(full.ravel())
    return out


def _bfs_path_edges(plus, shape, start, goal, blocked):
    """Shortest path (grid index tuples) from start to any goal cell across open faces, avoiding blocked cells."""
    X, Y, Z = shape
    dims = (X, Y, Z)
    strides = (Y * Z, Z, 1)
    blocked_f, goal_f = blocked.ravel(), goal.ravel()
    s = (start[0] * Y + start[1]) * Z + start[2]
    prev = {s: -1}
    dq = deque([s])
    found = None
    while dq:
        c = dq.popleft()
        if goal_f[c]:
            found = c
            break
        cx, rem = divmod(c, Y * Z)
        cy, cz = divmod(rem, Z)
        co = (cx, cy, cz)
        for ax in range(3):
            st_ = strides[ax]
            if co[ax] < dims[ax] - 1 and plus[ax][c]:
                n = c + st_
                if n not in prev and not blocked_f[n]:
                    prev[n] = c
                    dq.append(n)
            if co[ax] > 0:
                n = c - st_
                if plus[ax][n] and n not in prev and not blocked_f[n]:
                    prev[n] = c
                    dq.append(n)
    if found is None:
        return None
    path = []
    c = found
    while c != -1:
        cx, rem = divmod(c, Y * Z)
        cy, cz = divmod(rem, Z)
        path.append((cx, cy, cz))
        c = prev[c]
    path.reverse()
    return path


def check_enclosure(w, meta, iss):
    kind = np.array([p.enc_kind for p in w.palette], dtype=np.int8)[w.idx]
    solid = kind == 2
    # wall-like cells for the closing, breach naming and floors: solid cells and partial cells taller than a carpet
    wall = w.mask(lambda p: p.enc_kind == 2 or (p.enc_kind == 1 and p.top > 0.1875 + EPS), "enc_wallish")
    axes = _enclosure_axes(w)
    plus = None
    border = _border(w.shape)
    motion = w.mask(lambda p: p.motion_blocking, "motion")
    # covered[x,y,z] = some motion-blocking block strictly above (within the box)
    above = np.flip(np.logical_or.accumulate(np.flip(motion, axis=1), axis=1), axis=1)
    covered = np.zeros_like(motion)
    covered[:, :-1, :] = above[:, 1:, :]
    # closing of the walls: fills 1-2 cell holes -> used to name the breach and the "interior" for rain tests
    closed = ~_dilate26(~_dilate26(wall))
    closed_outside = _flood(border & ~closed, ~closed)
    interior_closed = ~closed & ~closed_outside
    hearth = w.g.tag("fire") | w.g.tag("campfires")
    on_hearth = np.roll(w.mask(lambda p: p.name in hearth, "hearth"), 1, axis=1)   # cell directly above a fire
    rooms = {}
    regions = {}
    for name, rpos in (meta.get("rooms") or {}).items():
        rpos = tuple(int(v) for v in rpos)
        gp = _g(rpos)
        info = {"marker": list(rpos)}
        rooms[name] = info
        if not w.inside(*rpos):
            iss.add("enclosure", "error", f"room '{name}' marker {rpos} is outside the box", pos=rpos)
            continue
        start = gp
        if solid[start]:
            up = (gp[0], gp[1] + 1, gp[2])
            if up[1] < w.shape[1] and not solid[up]:
                start = up
            else:
                iss.add("enclosure", "error", f"room '{name}' marker {rpos} is inside a solid block "
                        f"({_short(w.palette[w.idx[gp]].name)})", pos=rpos)
                continue
        seed = np.zeros_like(solid)
        seed[start] = True
        region = _flood_edges(seed, axes)
        leaks = []
        if (region & border).any():
            if plus is None:
                plus = _plus_edges(axes, w.shape)
            plug = np.zeros_like(solid)
            seen = set()
            for _ in range(8):
                path = _bfs_path_edges(plus, w.shape, start, border & ~plug, plug)
                if path is None:
                    break
                breach = _pick_breach(path, wall, closed, w.shape, solid)
                if breach in seen:                   # marker on the box boundary: the same escape every time
                    break
                seen.add(breach)
                k = path.index(breach)
                step = tuple(int(v) for v in np.subtract(path[min(k + 1, len(path) - 1)], path[max(k - 1, 0)]))
                kind_s = "roof/ceiling" if step[1] > 0 and step[0] == 0 and step[2] == 0 else \
                    "floor" if step[1] < 0 and step[0] == 0 and step[2] == 0 else "wall"
                sev = "error"
                bwx, bwy, bwz = _w(breach)
                if any(_over_hearth(w, wall, hearth, c) for c in path[k:]):
                    kind_s, sev = "chimney flue (escape rises straight up from a campfire/fire)", "warn"
                bst = w.palette[w.idx[breach]]
                what = f" (open {_short(bst.name)})" if bst.p("open") == "true" else \
                    f" ({_short(bst.name)} there leaves a gap)" if not bst.is_air else ""
                leaks.append({"breach": [bwx, bwy, bwz], "kind": kind_s, "path_len": len(path)})
                if sev == "warn":
                    msg = (f"room '{name}' is open to the sky through a chimney flue (hearth opening around "
                           f"{(bwx, bwy, bwz)}) - fine for smoke, check it is only 1 block wide")
                else:
                    msg = (f"room '{name}' leaks to the outside: hole in the {kind_s} around {(bwx, bwy, bwz)}{what} "
                           f"(escape path {len(path)} cells from the marker)")
                iss.add("enclosure", sev, msg, pos=(bwx, bwy, bwz), room=name, kind=kind_s)
                # plug a 3x3x3 neighbourhood around the breach and look for further holes
                bx, by, bz = breach
                plug[max(bx - 1, 0):bx + 2, max(by - 1, 0):by + 2, max(bz - 1, 0):bz + 2] = True
                plug[start] = False
            info["leaks"] = leaks
            # the room proper: inside the closed envelope, or (wide gaps / narrow rooms) the roofed cells around the marker
            if interior_closed[start]:
                region_in = _flood_edges(seed, axes, interior_closed)
            else:
                region_in = _flood_edges(seed, axes, covered)
        else:
            region_in = region
            info["leaks"] = []
        regions[name] = region_in
        info["volume"] = int(region_in.sum())
        floor = region_in & np.roll(wall, 1, axis=1) & ~wall     # room cells standing on a wall/floor block
        floor[:, 0, :] = False
        info["floor_cells"] = int(floor.sum())
        wet = floor & ~covered & ~on_hearth          # the cell over a hearth fire under an open flue is exempt
        if wet.any():
            cells = [_w(c) for c in zip(*np.nonzero(wet))]
            info["uncovered_floor"] = len(cells)
            iss.add("enclosure", "error", f"room '{name}': {len(cells)} floor cell(s) have no motion-blocking block "
                    f"above - rain falls in (e.g. {cells[0]})", pos=cells[0], room=name,
                    positions=[list(c) for c in cells[:50]])
    return {"rooms": rooms}, regions


# --------------------------------------------------------------------------------------------------------------
# Check 5: walkability (player movement BFS on real collision boxes)
# --------------------------------------------------------------------------------------------------------------
P_HALF = 0.3          # player half width (0.6 wide)
P_H = 1.8             # player height
STEP = 0.6            # Player step height (LivingEntity maxUpStep 0.6)
JUMP = 1.25           # jump apex (jump velocity 0.42)
CLIMB_EXIT = 1.6      # from a ladder cell the feet can rise to ~y+1, then step 0.6
SAFE_DROP = 3.0       # fall distance with no damage
_REGIONS = {"c": (0.5 - P_HALF, 0.5 - P_HALF, 0.5 + P_HALF, 0.5 + P_HALF),
            "east": (1 - P_HALF, 0.5 - P_HALF, 1.0, 0.5 + P_HALF), "west": (0.0, 0.5 - P_HALF, P_HALF, 0.5 + P_HALF),
            "south": (0.5 - P_HALF, 1 - P_HALF, 0.5 + P_HALF, 1.0), "north": (0.5 - P_HALF, 0.0, 0.5 + P_HALF, P_HALF)}


def _walk_boxes(st):
    if st.has("DoorBlock") or st.has("FenceGateBlock"):
        return ()                                   # openable: the player walks through
    if st.dangerous:
        return ((0.0, 0.0, 0.0, 1.0, 1.0, 1.0),)    # hazards: never walked through or stood on
    if st.cls == "ScaffoldingBlock":
        return ()                                   # climbable column
    return st.boxes


def _region_spans(boxes):
    out = {}
    for k, (x1, z1, x2, z2) in _REGIONS.items():
        out[k] = tuple((b[1], b[4]) for b in boxes if b[0] < x2 - EPS and b[3] > x1 + EPS and b[2] < z2 - EPS and b[5] > z1 + EPS)
    return out


def _merge(spans):
    """spans: list of (y1, y2, hazard) -> merged sorted list [y1, y2, hazard_top]."""
    spans = sorted(spans)
    out = []
    for y1, y2, hz in spans:
        if out and y1 <= out[-1][1] + EPS:
            if y2 > out[-1][1] + EPS:
                out[-1][1] = y2
                out[-1][2] = hz
            elif abs(y2 - out[-1][1]) <= EPS:
                out[-1][2] = out[-1][2] or hz
        else:
            out.append([y1, y2, hz])
    return out


def _free(I, h, top=None):
    """Player box fits with feet at h (up to h+1.8, or up to ``top`` if given) in a footprint with intervals I."""
    hi = (h + P_H) if top is None else top
    for y1, y2, _ in I:
        if y1 < hi - EPS and y2 > h + EPS:
            return False
    return True


def _support(I, h):
    best = None
    for iv in I:
        if iv[1] <= h + EPS and (best is None or iv[1] > best[1]):
            best = iv
    return best


class _Walker:
    def __init__(self, w):
        self.w = w
        X, Y, Z = w.shape
        hz = np.array([p.dangerous for p in w.palette])
        spans = [_region_spans(_walk_boxes(p)) for p in w.palette]
        climb_lut = np.array([(p.name in w.g.tag("climbable")) or p.fluid == "water" for p in w.palette])
        water_lut = np.array([p.fluid == "water" for p in w.palette])
        self.climb = climb_lut[w.idx]
        self.water = water_lut[w.idx]
        has = np.array([any(s.values()) for s in spans])[w.idx]
        # trapdoor hatches above/below a climbable cell are treated as open
        trap = w.mask(lambda p: p.has("TrapDoorBlock"), "trapdoor")
        hatch = trap & (np.roll(self.climb, 1, axis=1) | np.roll(self.climb, -1, axis=1))
        has &= ~hatch
        # LivingEntity#trapdoorUsableAsLadder: an (opened) trapdoor directly above a ladder with the same facing climbs
        fcode = {"north": 1, "south": 2, "west": 3, "east": 4}
        ladder_f = np.array([fcode.get(p.p("facing"), 0) if p.name == "minecraft:ladder" else 0 for p in w.palette])[w.idx]
        trap_f = np.array([fcode.get(p.p("facing"), 0) if p.has("TrapDoorBlock") else 0 for p in w.palette])[w.idx]
        below_f = np.roll(ladder_f, 1, axis=1)
        below_f[:, 0, :] = 0
        self.climb = self.climb | ((trap_f > 0) & (trap_f == below_f))
        self.col = {}
        for k in _REGIONS:
            self.col[k] = {}
        for gx, gy, gz in zip(*np.nonzero(has)):
            p = int(w.idx[gx, gy, gz])
            y0 = int(gy) - 1
            for k, sp in spans[p].items():
                if sp:
                    lst = self.col[k].setdefault((int(gx), int(gz)), [])
                    for a, b in sp:
                        lst.append((y0 + a, y0 + b, bool(hz[p])))
        self.merged = {}
        self.Y = Y

    def I(self, gx, gz, k="c"):
        key = (gx, gz, k)
        r = self.merged.get(key)
        if r is None:
            if k == "c":
                r = _merge(self.col["c"].get((gx, gz), []))
            elif k == "east":
                r = _merge(self.col["east"].get((gx, gz), []) + self.col["west"].get((gx + 1, gz), []))
            elif k == "south":
                r = _merge(self.col["south"].get((gx, gz), []) + self.col["north"].get((gx, gz + 1), []))
            self.merged[key] = r
        return r

    def edge(self, gx, gz, d):
        if d == "east":
            return self.I(gx, gz, "east")
        if d == "west":
            return self.I(gx - 1, gz, "east")
        if d == "south":
            return self.I(gx, gz, "south")
        return self.I(gx, gz - 1, "south")

    def climbable(self, gx, gz, h):
        gy = int(np.floor(h + EPS)) + 1
        X, Y, Z = self.w.shape
        if 0 <= gx < X and 0 <= gz < Z and 0 <= gy < Y:
            return bool(self.climb[gx, gy, gz])
        return False

    def soft_between(self, gx, gz, lo, hi):
        """Water or a climbable block in the fall path (no fall damage)."""
        X, Y, Z = self.w.shape
        if not (0 <= gx < X and 0 <= gz < Z):
            return False
        a, b = max(int(np.floor(lo + EPS)) + 1, 0), min(int(np.floor(hi + EPS)) + 2, Y)
        return bool(self.water[gx, a:b, gz].any() or self.climb[gx, a:b, gz].any()) if b > a else False

    def valid(self, gx, gz, h):
        I = self.I(gx, gz)
        if not _free(I, h):
            return False
        s = _support(I, h)
        if s is not None and abs(s[1] - h) <= EPS and not s[2]:
            return True
        return self.climbable(gx, gz, h)

    def nodes(self, gx, gz):
        I = self.I(gx, gz)
        out = set()
        for y1, y2, hz in I:
            if not hz and _free(I, y2):
                out.add(y2)
        X, Y, Z = self.w.shape
        if 0 <= gx < X and 0 <= gz < Z:
            for gy in np.nonzero(self.climb[gx, :, gz])[0]:
                h = float(gy - 1)
                if _free(I, h):
                    out.add(h)
        return sorted(out)

    def move(self, I_t, h, cap, I_start, cols, h0):
        """Move the player (feet h) into footprint I_t.  Returns the landing feet height or None."""
        if _free(I_t, h):
            s = _support(I_t, h)
            if s is None or s[2]:
                return None
            if h0 - s[1] > SAFE_DROP + EPS and not any(self.soft_between(cx, cz, s[1], h0) for cx, cz in cols):
                return None
            return s[1]
        for y1, y2, hz in I_t:
            if y2 <= h + EPS:
                continue
            if y2 - h > cap + EPS:
                break
            if hz or not _free(I_t, y2):
                continue
            if y2 - h > STEP + EPS and not _free(I_start, h, y2 + P_H):
                continue
            return y2
        return None

    def neighbours(self, gx, gz, h):
        out = []
        climbing = self.climbable(gx, gz, h)
        cap = CLIMB_EXIT if climbing else JUMP
        Ic = self.I(gx, gz)
        for d in HORIZ:
            dx, _, dz = DVEC[d]
            nx, nz = gx + dx, gz + dz
            X, Y, Z = self.w.shape
            if not (0 <= nx < X and 0 <= nz < Z):
                continue
            Ie = self.edge(gx, gz, d)
            s = self.move(Ie, h, cap, Ic, ((gx, gz), (nx, nz)), h)
            if s is None:
                continue
            In = self.I(nx, nz)
            cap2 = cap if abs(s - h) <= EPS else JUMP
            b = self.move(In, s, cap2, Ie, ((nx, nz),), h)
            if b is None or not self.valid(nx, nz, b):
                continue
            out.append((nx, nz, b))
        if climbing:
            up = float(np.floor(h + EPS)) + 1.0
            if _free(Ic, up) and self.valid(gx, gz, up):
                out.append((gx, gz, up))
        down = float(np.floor(h + EPS)) - 1.0
        if self.climbable(gx, gz, down) and _free(Ic, down):
            out.append((gx, gz, down))
        elif climbing:
            s = _support(Ic, h - EPS * 10)
            if s is not None and not s[2] and s[1] < h - EPS and _free(Ic, s[1]):
                out.append((gx, gz, s[1]))
        return out


def check_walkability(w, meta, iss):
    wk = _Walker(w)
    entrances = [tuple(int(v) for v in e) for e in (meta.get("entrances") or [])]
    rooms = {k: tuple(int(v) for v in p) for k, p in (meta.get("rooms") or {}).items()}
    result = {"entrances": [], "rooms": {}, "doors": []}
    if not entrances:
        iss.add("walkability", "warn", "meta has no entrances - walkability not evaluated")
        return result, set()
    visited = set()
    dq = deque()
    for e in entrances:
        gx, gz = e[0] + 1, e[2] + 1
        cands = [h for h in wk.nodes(gx, gz) if e[1] - 1.0 - EPS <= h <= e[1] + 1.0 + EPS]
        if not cands:
            iss.add("walkability", "error", f"entrance {e} is not a standable spot (no 1.8-high space with a floor)", pos=e)
            result["entrances"].append({"pos": list(e), "ok": False})
            continue
        h = min(cands, key=lambda v: abs(v - e[1]))
        result["entrances"].append({"pos": list(e), "ok": True, "feet": round(h, 4)})
        key = (gx, gz, int(round(h * 32)))
        if key not in visited:
            visited.add(key)
            dq.append((gx, gz, h))
    while dq:
        gx, gz, h = dq.popleft()
        for nx, nz, nh in wk.neighbours(gx, gz, h):
            key = (nx, nz, int(round(nh * 32)))
            if key not in visited:
                visited.add(key)
                dq.append((nx, nz, nh))
    reach_pts = [(gx - 1, k / 32.0, gz - 1) for gx, gz, k in visited]
    for name, rp in rooms.items():
        ok = any(x == rp[0] and z == rp[2] and rp[1] - 0.5 - EPS <= h < rp[1] + 1 - EPS for x, h, z in reach_pts)
        info = {"marker": list(rp), "reachable": ok}
        if not ok:
            best = None
            if reach_pts:
                best = min(reach_pts, key=lambda p: (p[0] - rp[0]) ** 2 + (p[1] - rp[1]) ** 2 + (p[2] - rp[2]) ** 2)
            standable = any(rp[1] - 0.5 - EPS <= h < rp[1] + 1 - EPS for h in wk.nodes(rp[0] + 1, rp[2] + 1))
            near = f"nearest reachable spot: feet at ({best[0]}, {best[1]:g}, {best[2]})" if best else "nothing reachable"
            extra = "" if standable else " (the marker itself is not a standable spot)"
            info["nearest"] = [best[0], round(best[1], 4), best[2]] if best else None
            iss.add("walkability", "error", f"room '{name}' at {rp} is not reachable from the entrances{extra}; {near}",
                    pos=rp, room=name)
        result["rooms"][name] = info
    # doors: 2-high standing space on both sides
    for x, y, z, st in w.box_cells():
        if not st.has("DoorBlock") or st.p("half") != "lower":
            continue
        f = st.p("facing")
        sides = []
        for d in (f, OPP[f]):
            p = _rel((x, y, z), d)
            hs = [h for h in wk.nodes(p[0] + 1, p[2] + 1) if y - 1.0 - EPS <= h <= y + STEP + EPS]
            sides.append(bool(hs))
            if not hs:
                blockers = [_short(w.at(p[0], yy, p[2]).name) for yy in (y, y + 1) if w.at(p[0], yy, p[2]).boxes]
                why = f"blocked by {', '.join(blockers)}" if blockers else "no floor within reach"
                iss.add("walkability", "error", f"door at {(x, y, z)}: no 2-high standing space on its {d} side at {p} ({why})",
                        pos=(x, y, z), block=st.s)
        result["doors"].append({"pos": [x, y, z], "both_sides_clear": all(sides)})
    result["reachable_nodes"] = len(visited)
    return result, visited


# --------------------------------------------------------------------------------------------------------------
# Check 6: lighting (block light propagation like the game's BlockLightEngine) + hostile spawn spots
# --------------------------------------------------------------------------------------------------------------
_POS_DIR = ("east", "up", "south")          # positive direction of axis 0 (x), 1 (y), 2 (z)


def _axis_open(w, faces_of, closed_lut=None):
    """Per axis (x, y, z): (lo, hi, ok) where ``ok`` (grid shape minus one along the axis) says whether the face
    between cell ``lo`` and its +axis neighbour ``hi`` is open: neither cell is closed (``closed_lut``, per palette
    entry) and the two face slices (``faces_of(state)`` -> 6 rasters or None) do not cover the face together
    (Shapes.faceShapeOccludes / mergedFaceOccludes).  The relation is symmetric, so one array serves both directions."""
    pal = w.palette
    full = np.zeros((len(pal), 6), dtype=bool)
    part = np.zeros((len(pal), 6), dtype=bool)
    for i, p in enumerate(pal):
        f6 = faces_of(p)
        if f6 is None:
            continue
        for k in range(6):
            full[i, k] = bool(f6[k].all())
            part[i, k] = bool(f6[k].any()) and not full[i, k]
    out = []
    for ax in range(3):
        d = _POS_DIR[ax]
        k, ko = DIRS.index(d), DIRS.index(OPP[d])
        lo, hi = [slice(None)] * 3, [slice(None)] * 3
        lo[ax], hi[ax] = slice(None, -1), slice(1, None)
        lo, hi = tuple(lo), tuple(hi)
        ia, ib = w.idx[lo], w.idx[hi]
        occ = full[ia, k] | full[ib, ko]
        if closed_lut is not None:
            occ |= closed_lut[ia] | closed_lut[ib]
        both = part[ia, k] & part[ib, ko] & ~occ
        if both.any():
            pairs = np.stack([ia[both], ib[both]], axis=1)
            uniq, inv = np.unique(pairs, axis=0, return_inverse=True)
            res = np.array([bool((faces_of(pal[a_i])[k] | faces_of(pal[b_i])[ko]).all()) for a_i, b_i in uniq.tolist()])
            occ[both] = res[np.asarray(inv).ravel()]
        out.append((lo, hi, ~occ))
    return out


def _light_axes(w):
    if "light_axes" not in w.cache:
        w.cache["light_axes"] = _axis_open(w, lambda p: p.light_faces)
    return w.cache["light_axes"]


def _propagate_light(L, axes, op):
    """LightEngine#propagateIncrease to a fixed point: a neighbour gets level - max(1, dampening) through open faces."""
    for _ in range(16):
        prev = L
        L = L.copy()
        for lo, hi, ok in axes:
            L[hi] = np.maximum(L[hi], np.where(ok, prev[lo] - op[hi], 0))
            L[lo] = np.maximum(L[lo], np.where(ok, prev[hi] - op[lo], 0))
        if np.array_equal(L, prev):
            break
    return np.clip(L, 0, 15)


def block_light(w):
    """Block light level per grid cell: emission, then -max(1, dampening) per step through non-occluding faces
    (BlockLightEngine).  Cached on the World."""
    if "block_light" not in w.cache:
        pal = w.palette
        em = np.array([p.emission for p in pal], dtype=np.int16)[w.idx]
        if not em.any():
            w.cache["block_light"] = em
        else:
            op = np.array([p.opacity for p in pal], dtype=np.int16)[w.idx]
            w.cache["block_light"] = _propagate_light(em, _light_axes(w), op)
    return w.cache["block_light"]


def sky_light(w):
    """Sky light level per grid cell (SkyLightEngine + ChunkSkyLightSources): every cell above the first edge going
    down a column that is occluded (lower cell has light dampening != 0, or the two occlusion faces cover the
    face) is a level-15 source - the open sky above the box included; light then spreads like block light.  The
    world around the box is flat terrain at ``ground`` with open sky.  Cached on the World."""
    if "sky_light" not in w.cache:
        pal = w.palette
        damp = np.array([p.damp for p in pal], dtype=np.int16)[w.idx]
        axes = _light_axes(w)
        lo, hi, ok_y = axes[1]
        down_open = ok_y & (damp[lo] == 0)          # [x, y, z]: light passes from y+1 straight down into y
        src = np.zeros(w.shape, dtype=bool)
        src[:, -1, :] = damp[:, -1, :] == 0        # the layer above the box is under open sky
        for y in range(w.shape[1] - 2, -1, -1):
            src[:, y, :] = src[:, y + 1, :] & down_open[:, y, :]
        L = np.where(src, 15, 0).astype(np.int16)
        w.cache["sky_light"] = _propagate_light(L, axes, np.maximum(damp, 1))
    return w.cache["sky_light"]


def raw_light(w):
    """LevelReader#getRawBrightness(pos, 0) per grid cell = max(sky light, block light) (time of day ignored)."""
    if "raw_light" not in w.cache:
        w.cache["raw_light"] = np.maximum(sky_light(w), block_light(w))
    return w.cache["raw_light"]


def check_lighting(w, regions, iss):
    L = block_light(w)
    pal = w.palette
    valid_spawn = np.array([p.valid_spawn for p in pal])[w.idx]
    g = w.g
    rails = g.tag("prevent_mob_spawning_inside")

    def empty_ok(p):           # NaturalSpawner.isValidEmptySpawnBlock
        return not (p.coll_full or p.signal or p.fluid or p.name in rails or p.dangerous)

    def clear(p, lim):         # zombie AABB (0.6 x 1.95) does not touch the cell's collision boxes below height lim
        x1, x2 = 0.5 - 0.3, 0.5 + 0.3
        return not any(b[0] < x2 and b[3] > x1 and b[2] < x2 and b[5] > x1 and b[1] < lim for b in p.boxes)

    feet_ok = np.array([empty_ok(p) and clear(p, 1.0) for p in pal])[w.idx]
    head_ok = np.array([empty_ok(p) and clear(p, 0.95) for p in pal])[w.idx]
    spawn = np.zeros_like(valid_spawn)
    spawn[:, 1:-1, :] = valid_spawn[:, :-2, :] & feet_ok[:, 1:-1, :] & head_ok[:, 2:, :] & (L[:, 1:-1, :] == 0)
    inbox = np.zeros_like(spawn)
    inbox[1:-1, 1:-1, 1:-1] = True
    spawn &= inbox
    in_room = np.zeros_like(spawn)
    reported = np.zeros_like(spawn)
    stats = {"rooms": {}}
    for name, reg in regions.items():
        sp = spawn & reg
        in_room |= reg
        lv = L[reg]
        stats["rooms"][name] = {"spawnable_spots": int(sp.sum()), "min_light": int(lv.min()) if lv.size else None,
                                "mean_light": round(float(lv.mean()), 2) if lv.size else None}
        new = sp & ~reported                     # rooms sharing one region are reported once
        reported |= sp
        if new.any():
            cells = [_w(c) for c in zip(*np.nonzero(new))]
            iss.add("lighting", "error", f"room '{name}': {len(cells)} spot(s) where hostile mobs can spawn (block light 0), "
                    f"e.g. {cells[0]} - add a light source", pos=cells[0], room=name, positions=[list(c) for c in cells[:50]])
    outside = spawn & ~in_room
    n_out = int(outside.sum())
    stats["landscape_spawnable_spots"] = n_out
    present = np.unique(w.idx)
    stats["light_source_types"] = sorted({_short(pal[i].name) for i in present if pal[i].emission > 0})
    if n_out:
        first = _w(next(zip(*np.nonzero(outside))))
        iss.add("lighting", "info", f"{n_out} dark spot(s) outside the rooms where hostile mobs could spawn at night "
                f"(block light 0), e.g. {first}", pos=first, count=n_out)
    return stats, L


# --------------------------------------------------------------------------------------------------------------
# Check 7: architecture metrics (info only)
# --------------------------------------------------------------------------------------------------------------
_NON_STRUCTURAL = ("VegetationBlock", "LeavesBlock", "CrossCollisionBlock", "WallBlock", "FenceGateBlock", "CarpetBlock",
                   "SnowLayerBlock", "LiquidBlock")


def _structural(p):
    """Building fabric (walls, floors, roofs, windows, doors) as opposed to fences, plants and small decor."""
    if p.has("DoorBlock"):
        return True
    if not _enclosure_wall(p):
        return False
    if p.has("CrossCollisionBlock"):
        return "pane" in p.name or "bars" in p.name
    return not any(c in _NON_STRUCTURAL for c in p.chain)


def _corners(mask2d):
    """Convex / concave corner counts of the outline of a 2D grid mask."""
    m = np.pad(mask2d.astype(np.int8), 1)
    q = m[:-1, :-1] + m[1:, :-1] + m[:-1, 1:] + m[1:, 1:]
    diag = ((m[:-1, :-1] == m[1:, 1:]) & (m[1:, :-1] == m[:-1, 1:]) & (m[:-1, :-1] != m[1:, :-1]))
    convex = int((q == 1).sum() + 2 * (diag & (q == 2)).sum())
    concave = int((q == 3).sum())
    return convex, concave


def check_metrics(w, meta, regions, iss):
    sx, sy, sz = w.size
    ground = w.ground
    core = (slice(1, -1), slice(1, -1), slice(1, -1))
    idx = w.idx[core]
    pal = w.palette
    authored = (idx > 2) & ~np.array([p.is_air for p in pal])[idx]
    structural = np.array([_structural(p) for p in pal])[idx] & authored
    out = {}
    # ---- footprint: structural cells in the first 3 layers above ground + enclosed holes, largest component
    y0 = max(ground + 1, 0)
    layer = structural[:, y0:min(y0 + 3, sy), :].any(axis=1) if y0 < sy else np.zeros((sx, sz), dtype=bool)
    for reg in regions.values():
        r = reg[core][:, y0:min(y0 + 3, sy), :].any(axis=1) if y0 < sy else np.zeros((sx, sz), dtype=bool)
        layer |= r
    if layer.any():
        filled = _fill2d(layer)
        comps = _components(filled[:, None, :])
        biggest = max(comps, key=len)
        fp = np.zeros_like(layer)
        for c in biggest:
            fp[c[0], c[2]] = True
        convex, concave = _corners(fp)
        out["footprint"] = {"area": int(fp.sum()), "convex_corners": convex, "concave_corners": concave,
                            "shape": "rectangle" if convex == 4 and concave == 0 else f"{convex}-corner outline",
                            "bbox_xz": [[int(np.nonzero(fp.any(1))[0].min()), int(np.nonzero(fp.any(0))[0].min())],
                                        [int(np.nonzero(fp.any(1))[0].max()), int(np.nonzero(fp.any(0))[0].max())]]}
    else:
        fp = np.zeros((sx, sz), dtype=bool)
        out["footprint"] = {"area": 0}
    # ---- roof: top structural block per footprint column, ridge lines = local maxima runs
    roof_h = np.full((sx, sz), -1, dtype=np.int32)
    ys = np.arange(sy)
    top_any = np.where(structural, ys[None, :, None], -1).max(axis=1)
    roof_h[fp] = top_any[fp]
    # ridge cells: local maxima of the roof height map that continue horizontally (a same-height local-max
    # neighbour) or are strict apexes; diagonal hip lines are local maxima too but are excluded that way
    D4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    lmax = np.zeros((sx, sz), dtype=bool)
    for x in range(sx):
        for z in range(sz):
            h = roof_h[x, z]
            if h >= 0 and all(h >= roof_h[x + dx, z + dz] for dx, dz in D4 if 0 <= x + dx < sx and 0 <= z + dz < sz):
                lmax[x, z] = True
    ridges = {}
    for x, z in zip(*np.nonzero(lmax)):
        h = roof_h[x, z]
        nbs = [(x + dx, z + dz) for dx, dz in D4 if 0 <= x + dx < sx and 0 <= z + dz < sz]
        cont = any(lmax[n] and roof_h[n] == h for n in nbs)
        apex = all(roof_h[n] < h for n in nbs)
        if cont or apex:
            ridges.setdefault(int(h), []).append((int(x), int(z)))
    ridge_lines = {}
    peaks = {}
    roofing = np.array([p.has("StairBlock") or p.has("SlabBlock") for p in pal])
    for h, cells in ridges.items():
        m = np.zeros((sx, 1, sz), dtype=bool)
        for x, z in cells:
            m[x, 0, z] = True
        for c in _components(m):
            a = np.array(c)
            if max(a[:, 0].max() - a[:, 0].min(), a[:, 2].max() - a[:, 2].min()) >= 2:
                ridge_lines.setdefault(h, []).append(len(c))
            elif all(roofing[idx[x, h, z]] for x, _, z in c):
                peaks[h] = peaks.get(h, 0) + 1          # hip-roof apex (short ridge of stairs/slabs)
    heights = sorted(set(ridge_lines) | set(peaks))
    out["roof"] = {"ridge_heights": heights, "distinct_ridge_heights": len(heights),
                   "ridge_lengths": {str(k): sorted(v) for k, v in sorted(ridge_lines.items())},
                   "apex_peaks": {str(k): v for k, v in sorted(peaks.items())},
                   "max_height_above_ground": int(roof_h.max() - ground) if fp.any() else 0}
    # ---- facades: exterior-facing structural cells, longest flat run, largest flat patch, windows
    wall = w.mask(_enclosure_wall, "enc_wall")
    outside = _flood(_border(w.shape) & ~wall, ~wall)[core]
    names = np.array([p.name for p in pal], dtype=object)[idx]
    glass = np.array([("glass" in p.name) for p in pal])[idx] & authored
    facades = {}
    best_run = (0, None)
    best_patch = (0, None)
    for d in HORIZ:
        dx, _, dz = DVEC[d]
        nbo = np.zeros_like(outside)
        src = [slice(None)] * 3
        dst = [slice(None)] * 3
        ax = 0 if dx else 2
        s = dx or dz
        if s > 0:
            dst[ax], src[ax] = slice(None, -1), slice(1, None)
        else:
            dst[ax], src[ax] = slice(1, None), slice(None, -1)
        nbo[tuple(dst)] = outside[tuple(src)]
        face = structural & nbo & (np.arange(sy)[None, :, None] > ground)
        win = glass & nbo
        planes = {}
        for x, y, z in zip(*np.nonzero(face)):
            key = int(x if ax == 0 else z)
            planes.setdefault(key, []).append((int(y), int(z if ax == 0 else x), names[x, y, z]))
        for key, cells in planes.items():
            cellset = {(y, u): n for y, u, n in cells}
            for (y, u), n in cellset.items():
                if cellset.get((y, u - 1)) == n:
                    continue
                k = 0
                while cellset.get((y, u + k)) == n:
                    k += 1
                if k > best_run[0]:
                    pos = (key, y, u) if ax == 0 else (u, y, key)
                    best_run = (k, {"length": k, "facade": d, "block": _short(n), "start": list(pos)})
            seen = set()
            for start, n in cellset.items():
                if start in seen:
                    continue
                comp = [start]
                seen.add(start)
                dq = deque([start])
                while dq:
                    cy, cu = dq.popleft()
                    for nyu in ((cy + 1, cu), (cy - 1, cu), (cy, cu + 1), (cy, cu - 1)):
                        if nyu not in seen and cellset.get(nyu) == n:
                            seen.add(nyu)
                            comp.append(nyu)
                            dq.append(nyu)
                if len(comp) > best_patch[0]:
                    pos = (key, start[0], start[1]) if ax == 0 else (start[1], start[0], key)
                    best_patch = (len(comp), {"blocks": len(comp), "facade": d, "block": _short(n), "at": list(pos)})
        wm = np.zeros((sx if ax == 2 else sz, sy, sz if ax == 0 else sx), dtype=bool)
        wins = 0
        if win.any():
            by_plane = {}
            for x, y, z in zip(*np.nonzero(win)):
                by_plane.setdefault(int(x if ax == 0 else z), []).append((int(z if ax == 0 else x), int(y)))
            for cells in by_plane.values():
                m = np.zeros((max(sx, sz), 1, sy), dtype=bool)
                for u, y in cells:
                    m[u, 0, y] = True
                wins += len(_components(m))
        facades[d] = {"windows": wins, "exterior_wall_blocks": int(face.sum())}
    out["facades"] = facades
    out["longest_flat_run"] = best_run[1]
    out["largest_flat_patch"] = best_patch[1]
    # ---- palette / composition
    used = [int(i) for i in np.unique(idx) if i > 2 and not pal[i].is_air]
    distinct_blocks = {pal[i].name for i in used}
    out["distinct_blocks"] = len(distinct_blocks)
    out["distinct_states"] = len({pal[i].s for i in used})
    n_auth = int(authored.sum())
    fp3 = np.broadcast_to(fp[:, None, :], idx.shape)
    building = authored & fp3                       # everything in the footprint columns (foundation .. roof)
    out["blocks"] = n_auth
    out["building_blocks"] = int(building.sum())
    out["landscaping_blocks"] = n_auth - int(building.sum())
    out["landscaping_fraction"] = round((n_auth - int(building.sum())) / n_auth, 3) if n_auth else 0.0
    out["footprint_fraction_of_box"] = round(float(fp.sum()) / (sx * sz), 3) if sx * sz else 0.0
    # ---- interior floor area per room / floor level
    rooms = {}
    floorish = np.array([_enclosure_wall(p) and (bool(p.sturdy & DBIT["up"]) or p.has("SlabBlock") or p.has("StairBlock"))
                         for p in pal])[w.idx]
    for name, reg in regions.items():
        floor = reg & np.roll(floorish, 1, axis=1) & ~floorish   # walkable floor below (slab/stair cells themselves
                                                                 # can be room cells now; count the cell above them)
        floor[:, 0, :] = False
        per = {}
        for gy in np.nonzero(floor.any(axis=(0, 2)))[0]:
            per[str(int(gy) - 1)] = int(floor[:, gy, :].sum())
        rooms[name] = {"floor_area": int(floor.sum()), "by_floor_y": per}
    out["rooms"] = rooms
    return out


def _fill2d(m):
    """Fill holes of a 2D mask (cells not reachable from the border through ~m)."""
    pad = np.pad(~m, 1, constant_values=True)
    seed = np.zeros_like(pad)
    seed[0, :] = seed[-1, :] = seed[:, 0] = seed[:, -1] = True
    reach = seed & pad
    while True:
        nxt = reach.copy()
        nxt[1:, :] |= reach[:-1, :]
        nxt[:-1, :] |= reach[1:, :]
        nxt[:, 1:] |= reach[:, :-1]
        nxt[:, :-1] |= reach[:, 1:]
        nxt &= pad
        if np.array_equal(nxt, reach):
            break
        reach = nxt
    return ~reach[1:-1, 1:-1]


# --------------------------------------------------------------------------------------------------------------
# Entry points
# --------------------------------------------------------------------------------------------------------------
CHECKS = ("validity", "floating", "support", "enclosure", "walkability", "lighting", "palette", "metrics")


def check_palette(blocks, meta, iss):
    """Allowed-blocks constraint (``meta["allowed_blocks"]``, entries as parsed by blockwright.palette).  Every
    needed item outside the list is an error: the player does not own it."""
    entries = meta.get("allowed_blocks") or []
    if not entries:
        return {"enabled": False}
    from .palette import check_blocks
    bad = check_blocks(blocks, entries)
    for item, count, pos in bad:
        iss.add("palette", "error", f"{item} x{count} is not in the allowed-blocks list", pos=pos)
    return {"enabled": True, "entries": len(entries), "outside": {it: n for it, n, _ in bad}}


def run_qa(blocks, size, meta, registry=None):
    """Run every check on a structure and return the report dict (JSON-serialisable).

    blocks: {(x, y, z): canonical state}, size: (sx, sy, sz), meta: {"ground", "rooms", "entrances", "slug", "title"}.
    """
    t0 = time.perf_counter()
    g = game_data(registry)
    meta = dict(meta or {})
    has_ground = meta.get("ground") is not None
    ground = int(meta["ground"]) if has_ground else 0
    blocks = {tuple(int(v) for v in k): v for k, v in blocks.items()}
    w = World(g, blocks, size, ground)
    iss = _Issues()
    timing = {}
    results = {}

    def timed(name, fn, *a):
        t = time.perf_counter()
        r = fn(*a)
        timing[name] = round(time.perf_counter() - t, 3)
        return r

    results["validity"] = timed("validity", check_validity, w, blocks, iss)
    if not has_ground:
        iss.add("validity", "warn", "meta has no 'ground' - assuming the terrain surface is y=0")
    results["floating"] = timed("floating", check_floating, w, iss)
    results["support"] = timed("support", check_support, w, iss)
    results["enclosure"], regions = timed("enclosure", check_enclosure, w, meta, iss)
    results["walkability"], _ = timed("walkability", check_walkability, w, meta, iss)
    results["lighting"], _ = timed("lighting", check_lighting, w, regions, iss)
    results["palette"] = timed("palette", check_palette, blocks, meta, iss)
    results["metrics"] = timed("metrics", check_metrics, w, meta, regions, iss)
    sev = {"error": 0, "warn": 0, "info": 0}
    for it in iss.items:
        sev[it["severity"]] += 1
    order = {"error": 0, "warn": 1, "info": 2}
    issues = sorted(iss.items, key=lambda it: (order[it["severity"]], CHECKS.index(it["check"])))
    timing["total"] = round(time.perf_counter() - t0, 3)
    return {
        "slug": meta.get("slug", ""), "title": meta.get("title", ""), "size": list(w.size), "ground": ground,
        "summary": {"errors": sev["error"], "warnings": sev["warn"], "infos": sev["info"], "passed": sev["error"] == 0},
        "checks": results, "issues": issues, "timing_s": timing,
        "qa_version": 1, "game_version": g.dump.get("version"),
    }


def _fmt_pos(p):
    return f"({p[0]}, {p[1]}, {p[2]})" if p is not None else ""


def report_markdown(report, max_per_check=40):
    """Human-readable markdown for a report dict."""
    s = report["summary"]
    L = []
    title = report.get("title") or report.get("slug") or "structure"
    L.append(f"# QA report - {title}")
    L.append("")
    verdict = "PASS" if s["passed"] else "FAIL"
    L.append(f"**{verdict}** - {s['errors']} error(s), {s['warnings']} warning(s), {s['infos']} info  ")
    L.append(f"size {tuple(report['size'])}, ground y={report['ground']}, checked in {report['timing_s']['total']}s")
    L.append("")
    by = {}
    for it in report["issues"]:
        by.setdefault(it["check"], []).append(it)
    c = report["checks"]
    sections = [
        ("validity", f"{c['validity']['blocks']} blocks, {c['validity']['distinct_states']} distinct states"),
        ("floating", f"{c['floating']['floating_components']} floating component(s)"),
        ("support", f"{c['support']['checked']} blocks with survival rules checked, {c['support']['failed']} failing; "
                    f"{c['support'].get('falling', 0)} falling block(s), {c['support'].get('fluid_escapes', 0)} "
                    f"uncontained fluid cell(s)"),
        ("enclosure", ", ".join(f"{k}: {'leaks' if v.get('leaks') else 'sealed'}" for k, v in c["enclosure"]["rooms"].items())
         or "no rooms in meta"),
        ("walkability", ", ".join(f"{k}: {'reachable' if v['reachable'] else 'UNREACHABLE'}"
                                  for k, v in c["walkability"].get("rooms", {}).items()) or "no rooms evaluated"),
        ("lighting", f"{c['lighting'].get('landscape_spawnable_spots', 0)} dark spawnable spots outside rooms; " +
         ", ".join(f"{k}: {v['spawnable_spots']} spawnable, min light {v['min_light']}" for k, v in c["lighting"]["rooms"].items())),
    ]
    pal = c.get("palette") or {}
    if pal.get("enabled"):
        sections.append(("palette", f"{pal['entries']} allowed entries; {len(pal['outside'])} item kind(s) outside the list"))
    for name, summary in sections:
        items = by.get(name, [])
        n_err = sum(1 for it in items if it["severity"] == "error")
        mark = "FAIL" if n_err else "ok"
        L.append(f"## {name} - {mark}")
        L.append(f"_{summary}_")
        L.append("")
        for it in items[:max_per_check]:
            pos = f" `{_fmt_pos(it['pos'])}`" if "pos" in it else ""
            L.append(f"- **{it['severity']}**{pos} {it['message']}")
        if len(items) > max_per_check:
            L.append(f"- ... {len(items) - max_per_check} more (see JSON)")
        L.append("")
    m = c["metrics"]
    L.append("## metrics")
    fp = m.get("footprint", {})
    L.append(f"- footprint: {fp.get('area', 0)} cells, {fp.get('convex_corners', 0)} convex / {fp.get('concave_corners', 0)} "
             f"concave corners ({fp.get('shape', '-')})")
    L.append(f"- roof ridge heights: {m['roof']['ridge_heights']} (lengths {m['roof']['ridge_lengths']}), "
             f"roof top {m['roof']['max_height_above_ground']} above ground")
    lr = m.get("longest_flat_run")
    if lr:
        L.append(f"- longest flat wall run: {lr['length']} x {lr['block']} on the {lr['facade']} facade from "
                 f"{_fmt_pos(lr['start'])}")
    lp = m.get("largest_flat_patch")
    if lp:
        L.append(f"- largest flat same-material patch: {lp['blocks']} x {lp['block']} on the {lp['facade']} facade")
    L.append("- windows per facade: " + ", ".join(f"{d} {v['windows']}" for d, v in m["facades"].items()))
    L.append(f"- distinct blocks: {m['distinct_blocks']} ({m['distinct_states']} states); landscaping fraction "
             f"{m['landscaping_fraction']}; footprint fraction of box {m['footprint_fraction_of_box']}")
    for name, r in m["rooms"].items():
        L.append(f"- room {name}: floor area {r['floor_area']} {r['by_floor_y']}")
    L.append("")
    return "\n".join(L)


def write_report(report, md_path, json_path):
    """Write the report as markdown (human) and JSON (machine).  Parent directories are created."""
    for p in (md_path, json_path):
        if p:
            Path(p).parent.mkdir(parents=True, exist_ok=True)
    if json_path:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=1)
    if md_path:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(report_markdown(report))


def main(argv=None):
    """CLI: python -m blockwright qa <file.litematic> [out_dir] [--meta meta.json] [--ground Y]

    The structure is read with blockwright.litematic.read_litematic (another module of this package).  ``meta`` (ground, rooms,
    entrances, slug, title) is taken from --meta (a JSON file), else from the litematic metadata dict (its "meta" key
    or the dict itself), and --ground overrides ground.  Exit code 0 when the report has no errors.
    """
    import argparse
    ap = argparse.ArgumentParser(description="QA checks for a .litematic structure")
    ap.add_argument("path")
    ap.add_argument("out_dir", nargs="?", default=None, help="default: <workspace>/out/reports")
    ap.add_argument("--meta", default=None, help="JSON with ground/rooms/entrances/slug/title (default: <path>.meta.json)")
    ap.add_argument("--ground", type=int, default=None)
    ap.add_argument("--allowed", default=None, help="allowed-blocks file: report every item outside it as an error")
    a = ap.parse_args(argv)
    from blockwright.litematic import read_litematic
    blocks, size, md = read_litematic(a.path)
    meta = {}
    if isinstance(md, dict):
        inner = md.get("meta")
        meta.update(inner if isinstance(inner, dict) else md)
    meta_path = a.meta
    if meta_path is None:                       # sidecar written by the build pipeline: <name>.meta.json
        side = Path(a.path).with_suffix(".meta.json")
        meta_path = str(side) if side.is_file() else None
    if meta_path:
        with open(meta_path, encoding="utf-8") as f:
            meta.update(json.load(f))
    if a.ground is not None:
        meta["ground"] = a.ground
    if meta.get("ground") is None:
        print("warning: no ground given (use --ground or --meta); assuming ground = 0")
    slug = meta.get("slug") or Path(a.path).stem
    meta.setdefault("slug", slug)
    if a.allowed:
        from .palette import load_palette
        meta["allowed_blocks"] = load_palette(a.allowed)
    rep = run_qa(blocks, size, meta)
    out_dir = a.out_dir or str(_config.workspace() / "out" / "reports")
    a.out_dir = out_dir
    write_report(rep, Path(a.out_dir) / f"{slug}_qa.md", Path(a.out_dir) / f"{slug}_qa.json")
    print(report_markdown(rep))
    return 0 if rep["summary"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
