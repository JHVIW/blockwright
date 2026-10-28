# `.litematic` format — verified for Litematica 0.29.1 on Minecraft 26.3 (data version 5023)

Everything below was read from the decompiled `litematica-fabric-26.3-0.29.1.jar` / `malilib-fabric-26.3-0.30.2.jar`
(vineflower output) and then **checked by running
Litematica's own reader headlessly** (`python -m blockwright validate`, see the end). Citations are `Class#method`; paths are under
`fi/dy/masa/litematica/` unless they start with `malilib:` (= `fi/dy/masa/malilib/`).

Evidence summary
* A real file saved by Litematica on 26.3 (data version 5023, found in `~/Downloads/Cactus Farm V1-from-abfielder.litematic`)
  passes the strict validator: Litematica's reader and our independent decoder agree on 27 783/27 783 cells, its
  `TotalBlocks` (13 319) equals our `!isAir()` count, `EnclosingSize`/`TotalVolume` match.
* Our independent Python packer (`tests/fixtures/make_fixtures.py: pack`) re-encodes the `BlockStates` of 4 real
  Litematica files (6, 6, 7 and 8 bits per entry) **bit-identically**.
* Our fixtures (2-bit linear palette, 5-bit hash palette with straddling entries, two regions incl. negative `Size`) load
  through `LitematicaSchematic.createFromFile` with every cell identical; 8 broken fixtures are rejected for the right
  reason (`python tests/fixtures/make_fixtures.py --check` → 11/11).
* Tag layout of our fixture vs the 26.3 Litematica-saved file: same keys, same NBT types, same key order, same root name
  (`""`), same empty-list element type (End). The only differences are content (entities, preview image).

---------------------------------------------------------------------------------------------------------------------

## 1. Container

| What | Fact | Source |
|---|---|---|
| Compression | gzip. Reader falls back to raw NBT only on `ZipException`. Litematica always writes gzip. | malilib:`DataFileUtils#readCompoundDataFromNbtFile`, `#writeCompoundDataToCompressedNbtFile` |
| Root | Named-tag header: type byte, UTF name, payload. Litematica writes name `""`. The reader **ignores the type byte (unless 0) and the name** and parses the payload as a Compound (so it must be one). | malilib:`DataFileUtils#readFromNbtStream` |
| Size limit | 512 MiB uncompressed (`SizeTracker(536870912)`). | same |
| File name | Must end in `.litematic` (type detection is by extension only). `createFromFile` sanitises the name; a name containing `\ / : * ? " < > \|` `` ` ``, control/combining chars, or the case-sensitive substrings `COM` / `PRN` is rewritten and the file is then **not found**. Use lowercase slugs. | `util/FileType#fromFile`, `LitematicaSchematic#fileFromDirAndName`, malilib:`FileNameUtils` |

## 2. Root compound

| Tag | Type | Required | Reader behaviour (`LitematicaSchematic#readFromData`) |
|---|---|---|---|
| `MinecraftDataVersion` | Int | **yes** (write 5023) | Read with `getIntOrDefault` (any numeric accepted). **Missing → `datafixerDefaultSchema` = 1139 (MC 1.12)** → palette goes through the 1.12→1.13 converter *and* the vanilla DataFixer. See §3. |
| `Version` | Int | **yes** (write 7) | Must be exactly an Int (`contains("Version", 3)`), else "no_schematic_version_information" → load fails. Must be 1..7, else "unsupported_schematic_version" → load fails. |
| `SubVersion` | Int | write 1 | **Never read** anywhere in 0.29.1 (only written: `writeToData`). |
| `Metadata` | Compound | yes | `SchematicMetadata#readData`; missing → defaults (`Name "?"`, ...). |
| `Regions` | Compound | yes | One entry per sub-region, key = region name (any string, even `""`). Non-Compound entries are skipped silently. |

Litematica writes them in this order: `MinecraftDataVersion, Version, SubVersion, Metadata, Regions` (`#writeToData`).
Order is irrelevant for reading.

## 3. Version handling (what happens when numbers differ)

| Condition | Effect | Source |
|---|---|---|
| `Version < 5` (or `0 < MinecraftDataVersion < 1631`) | Every palette entry is converted from 1.12 ids (`SchematicConversionMaps#get_1_13_2_StateTagFor_1_12_Tag`). | `#convertBlockStatePalette_1_12_to_1_13_2` |
| `Version >= 2` | `TileEntities` and `Entities` read (v1 used a different wrapper format). | `#readSubRegionsFromData` |
| `Version >= 3` / `>= 5` | `PendingBlockTicks` / `PendingFluidTicks` read. | same |
| `MinecraftDataVersion < 5023` | (a) vanilla `DataFixers` `BLOCK_STATE` update of every palette entry, `BLOCK_ENTITY` of every TE, `ENTITY` of every entity (`SchematicConversionMaps#updateBlockStates/updateBlockEntity/updateEntity`, gated by config `datafixerMode`, default ALWAYS); (b) **post-process fixers recompute states** of walls, redstone wire, banners, beds, flower pots, note blocks, signs, skulls from their neighbours (`#postProcessContainerIfNeeded`, `SchematicConverter#addPostUpdateBlocksLitematica`, `WallStateFixer`). Verified on real files: wall `east/west=low/tall` values were rewritten. | `#convertBlockStatePalette_to_1_20_5` |
| `MinecraftDataVersion > 5023` | No conversion. If more than 100 above, a "newer_minecraft_version" warning is shown, load continues. | `#readFromData` |
| `MinecraftDataVersion == 5023` | Nothing is converted or post-processed — the file is used **exactly as stored**. → **always write 5023**. | |

## 4. `Metadata` compound

| Tag | Type | Reader (`SchematicMetadata#readData`) | Litematica's writer (`#writeData`) |
|---|---|---|---|
| `Name` | String | `getStringOrDefault` → `"?"` if missing / not String. Shown in the browser; becomes the placement name. | always |
| `Author` | String | default `"?"` | always |
| `Description` | String | default `""` | always |
| `RegionCount` | Int | any numeric, default 0. Display only. | only if > 0 |
| `TotalVolume` | Int | **only an exact Int** is read, else stays −1. Display only. | only if > 0 |
| `TotalBlocks` | Int | **only an exact Int** is read, else −1. Shown in the browser; adjusted when blocks are edited in schematic-edit mode (`SchematicUtils`). Definition: number of cells whose state `!isAir()` (air, cave_air, void_air are air) — verified on the 26.3 reference file. | if >= 0 |
| `TimeCreated` | Long | epoch **millis**, any numeric, default −1 | only if > 0 |
| `TimeModified` | Long | epoch millis | only if > 0 |
| `EnclosingSize` | Compound `{x,y,z: Int}` | Read only if Compound with three exact Ints, else (0,0,0). This is `LitematicaSchematic#getTotalSize()`. | always |
| `PreviewImageData` | IntArray | optional; read only if IntArray. Displayed only if `length = side²` (any side; Litematica makes 120×120). Pixel `i = x + y*side`, value = **ARGB** int (`0xAARRGGBB`, signed in NBT); fed to `NativeImage#setPixel` (ARGB→ABGR). Use alpha 0xFF. | if set |

`EnclosingSize` = size of the box enclosing all regions' corners (`PositionUtils#getEnclosingAreaSize`: max − min + 1
over every region's corner 1 and corner 2, see §5). `TotalVolume` = Σ |sx·sy·sz| over regions
(`PositionUtils#getTotalVolume`).

## 5. Region compound (`Regions.<name>`)

| Tag | Type | Notes |
|---|---|---|
| `Position` | Compound `{x,y,z: Int}` | **Required**: if `Position` or `Size` lacks an exact Int x/y/z (`DataTypeUtils#readBlockPos`), the whole region is **dropped silently**. |
| `Size` | Compound `{x,y,z: Int}` | Signed, never 0 (`Box#updateSize`: `pos2 − pos1 ± 1`). Container dimensions are `|Size|`. |
| `BlockStatePalette` | List of Compound | §6 |
| `BlockStates` | LongArray | §7. Must be exactly a LongArray (`getType() == 12`), otherwise **no block container is created** for the region. |
| `TileEntities` | List of Compound | §8 (missing = empty) |
| `Entities` | List of Compound | §8 (missing = empty) |
| `PendingBlockTicks` | List of Compound | §8 (missing = empty) |
| `PendingFluidTicks` | List of Compound | §8 (missing = empty) |

Litematica writes them in the order `BlockStatePalette, BlockStates, TileEntities, PendingBlockTicks, PendingFluidTicks,
Entities, Position, Size`; empty lists have element type End (0) (`#writeSubRegionsToData`). Neither matters to readers.

**Position / Size semantics** (`#setSubRegionPositions`, `#takeBlocksFromWorld`, `#readSubRegionsFromData`, `PositionUtils`):
* `Position` = the selection box's **corner 1** minus the area origin. The area origin is the schematic origin; a
  placement puts the schematic origin at the placement origin (on "Load", the player's block position —
  `SchematicPlacement#createFor`, `#resetAllSubRegionsToSchematicValues` use `Position` unchanged).
* `relEnd = Size − sign(Size)` per axis (`getRelativeEndPositionFromAreaSize`: s>0 → s−1, s<0 → s+1); corner 2 =
  `Position + relEnd`.
* Region **min corner** = `min(Position, Position + relEnd)` per axis; the block container's (0,0,0) is the min corner.
* Example (verified, `multi_region_negative` fixture): `Position (5,1,4) Size (-2,-2,-3)` → cells x 4..5, y 0..1,
  z 2..4; container (0,0,0) = (4,0,2); container (1,1,2) = (5,1,4) = Position. Real Litematica saves very often have
  negative sizes (selections dragged "backwards").
* For our generator: one region, `Position (0,0,0)`, positive `Size (sx,sy,sz)` → min corner = origin, everything simple.

## 6. `BlockStatePalette`

Each entry: `{Name: String "minecraft:oak_stairs", Properties: {facing: "east", half: "bottom", ...}}`.
Litematica writes `Properties` only when the block has properties (`DataTypeUtils#writeStatePropertiesToTag`:
`!state.isSingletonState()`), with **all** properties, values as strings (`Property#getName(value)`).

Parsing (`LitematicaBlockStatePalette{Linear,HashMap}#readFromData` → malilib:`DataTypeUtils#readBlockStateFromTag`,
resolved through `SchematicWorldHandler.INSTANCE.getRegistryManager()`):
* Key precedence: if the entry has a **lowercase `id`** key it is used instead of `Name`; likewise lowercase
  `properties` over `Properties` (26.3 vanilla `NbtUtils` switched to lowercase `id/properties`; Litematica accepts both
  and writes the legacy capitalised keys). Verified: an entry with `Name=oak_planks` + `id=dirt` loads as dirt.
  → write only `Name` / `Properties`.
* **Unknown block id → `minecraft:air`, silently.** (e.g. pre-26.x `minecraft:chain` — 26.3 has `minecraft:iron_chain`.)
* **Unknown property name → ignored, silently.**
* **Illegal value → ignored (property keeps its default), silently.**
* **Missing property → default, silently.**
* Non-String property value → read as `""` → ignored.
* So Litematica never rejects a bad palette; it silently changes your blocks. The validator treats all of these as errors.

**Index 0 must be `minecraft:air`** (exactly the default air state). The container pre-seeds id 0 with air
(`LitematicaBlockStateContainer#setBits` → `palette.idFor(AIR)`), then `readFromData` skips entry 0 *only if it is air*;
a non-air entry 0 is appended as a new id, **shifting every index by one** (verified: fixture `broken_air_not_first`
loads 0/27 cells correctly). Air at 0 is required even if the region contains no air.

Other rules: order of entries 1..n is free (Litematica's own order is first-encounter while saving); duplicates load fine
but are wasteful; unused entries are harmless but still count for the bit width.

## 7. `BlockStates` bit packing (`LitematicaBitArray`, `LitematicaBlockStateContainer#createFrom`)

* `bits = max(2, 32 − Integer.numberOfLeadingZeros(paletteLen − 1))` = `max(2, ceil(log2(paletteLen)))`, where
  `paletteLen` is the **number of entries in the list** (not the number used). 1–4 entries → 2 bits, 5–8 → 3, 9–16 → 4,
  17–32 → 5, 33–64 → 6, ..., 257–512 → 9. (Bits ≤ 4 use the linear palette, > 4 the hash palette — identical result.)
* Cell index: `i = (y * sizeZ + z) * sizeX + x` (`#getIndex`: `y*sizeLayer + z*sizeX + x`), x/y/z container coords
  (0..|Size|−1, from the min corner).
* Entry `i` occupies bits `[i*bits, i*bits+bits)` of the little-endian bit stream formed by the longs: stream bit `k`
  is bit `k mod 64` (LSB = 0) of long `k / 64`. **Entries straddle long boundaries** (no padding per long; this is
  *not* the vanilla 1.16+ chunk format).
* Length: exactly `ceil(volume * bits / 64)` longs (`roundUp(volume*bits, 64)/64`). The reader **does not check the
  length**: a short array loads, then throws `ArrayIndexOutOfBoundsException` when the missing cells are read (render /
  paste time) — verified with fixture `broken_short_blockstates`. Unused high bits of the last long: write 0.
* Indices `>= paletteLen` read as air (`getBlockState` returns null → `AIR_BLOCK_STATE` in `#get`).
* NBT longs are signed: store `u64 − 2^64` when `u64 >= 2^63`.

Worked example, 5 bits (palette of 21 entries), 14 cells with indices 1, 2, …, 14:
```
long[0] = 0xD62D4941CC520C41   cells 0..11 in bits 0..59; bits 60..63 = low 4 bits of cell 12 (value 13 = 0b01101 -> 0b1101 = 0xD)
long[1] = 0x000000000000001C   bit 0 = bit 4 of cell 12 (0); bits 1..5 = cell 13 (14 = 0b01110); rest 0
read cell 12: ((long0 >>> 60) | (long1 << 4)) & 0x1F = 13
length = ceil(14*5/64) = 2
```

## 8. Tile entities, entities, scheduled ticks

**TileEntities** — each element is the block entity NBT as saved by `BlockEntity#saveWithFullMetadata` (so it carries
`id` and `components`) plus Int `x,y,z` = **container coordinates** (relative to the region min corner)
(`#takeBlocksFromWorld`, `#readTileEntitiesFromData`). Entries without exact-Int x/y/z are dropped. On paste the block
is placed first and creates its own block entity; the NBT (x/y/z rewritten to world coords) is then loaded into it with
`loadWithComponents` (`SchematicPlacingUtils#placeToWorldWithinChunk`) — Litematica itself never reads `id`, but keep it
for other tools. NBT at a block without a block entity is ignored. Blocks with a block entity but no record get a
default (empty) block entity from the world. 26.3 note: **beds have no block entity** any more
(`blockwright/data/blocks_26.3.json`: `block_entity: false`); `minecraft:bed` TE records in old files are dropped by the DataFixer.

**Entities** — full entity NBT (`saveWithoutId` + `id`), with `Pos` = List of 3 Double **relative to the region
`Position` (corner 1, not the min corner)**; hanging entities also carry `TileX/Y/Z`, block-attached ones `block_pos`,
leashed `leash`, mobs `home_pos`, all relative to `Position` (`#takeEntitiesFromWorld`, `#placeEntitiesToWorld`).
`Pos` missing → (0,0,0) (`DataTypeUtils#getVec3dCodec`). Empty compounds are dropped. Not needed for our buildings.

**PendingBlockTicks / PendingFluidTicks** — `{Block|Fluid: String id, Priority: Int, SubTick: Long, Time: Int (delay in
ticks), x,y,z: Int (container coords)}` (`#writePendingTicksToData`, `#readPendingTicksFromData`). Entries without an
Int `Time` or with an unknown id are dropped. Write empty lists.

## 9. What Litematica does with the blocks (relevant for building design)

* Paste places states **verbatim** with `Level#setBlock(pos, state, 18)` = `UPDATE_CLIENTS | UPDATE_KNOWN_SHAPE` → no
  neighbour shape updates: stair shapes, fence/wall/pane/bars connections, door halves etc. appear exactly as stored, so
  they must be correct in the file (that is what `blockwright/resolve.py` is for).
* `minecraft:structure_void` cells are **never pasted** (`SchematicPlacingUtils`, `WorldPlacingUtils`,
  `LitematicaSchematic#placeBlocksToWorld`).
* Air cells: with the default `pasteReplaceBehavior = NONE` a cell is only pasted where the world has air, so schematic
  air never removes terrain; with `ALL` it does. The overlay option `schematicOverlayTypeExtra` (default on) highlights
  world blocks standing in schematic-air cells (e.g. natural grass/flowers inside the bounding box) as "extra" blocks
  (behaviour of the overlay taken from the option name/default, not traced through the renderer).

## 10. Writer checklist (what `blockwright/litematic.py` must do)

1. gzip; root = Compound with name `""`.
2. Root: `MinecraftDataVersion` Int **5023**, `Version` Int **7**, `SubVersion` Int **1**, `Metadata`, `Regions`.
3. Metadata: `Name`, `Author`, `Description` String; `RegionCount`, `TotalVolume`, `TotalBlocks` **Int** (not Long!);
   `TimeCreated`, `TimeModified` **Long** epoch millis (> 0); `EnclosingSize {x,y,z Int}`; optional
   `PreviewImageData` IntArray of side² ARGB ints (120×120 like Litematica).
4. `TotalBlocks` = count of non-air cells; `TotalVolume` = Σ volumes; `EnclosingSize` = enclosing box (= Size for one
   region at the origin); `RegionCount` = number of regions.
5. One region (name = slug is fine), `Position {0,0,0}`, `Size {sx,sy,sz}` all positive Ints.
6. Palette: entry 0 = `{Name:"minecraft:air"}` (no Properties); then each distinct state once,
   `{Name:"minecraft:<id>", Properties:{<every property>: "<value>"}}`, `Properties` omitted for property-less blocks;
   ids/properties/values exactly as in `blockwright/data/blocks_26.3.json`.
7. `bits = max(2, (len(palette)-1).bit_length())`; pack index `(y*sz+z)*sx+x` LSB-first, straddling longs;
   exactly `ceil(volume*bits/64)` signed longs.
8. `TileEntities`, `Entities`, `PendingBlockTicks`, `PendingFluidTicks`: write (empty) lists.
9. File name: lowercase `NN_slug.litematic` (no `COM`/`PRN`, no `\/:*?"<>|`).
10. Run `python -m blockwright validate out/schematics/*.litematic` — exit code 0 required.

## 11. Validator (`python -m blockwright validate`, `blockwright/java/LitematicValidate.java`)

```
python -m blockwright validate [--lenient] [--no-litematica] [-v] [--json report.json] file.litematic...
```
* Phase 1 (independent): Minecraft's `NbtIo.readCompressed`; checks every tag/type above; bit-by-bit decode; strict
  palette parse against the live 26.3 registry after `Bootstrap.bootStrap()` (unknown block / unknown property /
  illegal value / missing property / non-air index 0 / duplicates); block counts; metadata counters; TE/entity/tick
  records (TE positions, TE on a block without block entity, unknown ids).
* Phase 2 (Litematica's own code): `FileType.fromFile`, `fileFromDirAndName` (name rewriting),
  `readMetadataFromFile` (schematic browser path), `createFromFile` (the "Load Schematic" button path), then every cell
  of every region container (`LitematicaBlockStateContainer#get`) is compared by identity with phase 1, plus
  Position/Size/container size, palette size, TE/entity/tick counts and the metadata Litematica will display.
  Messages Litematica would show the player are captured (malilib `IMessageConsumer`) and reported.
* Strict by default (exactly what Litematica 0.29.1 writes on 26.3); `--lenient` turns tolerated deviations
  (other data/schematic versions, missing SubVersion, Long counters, missing lists, ...) into warnings.
* Exit 0 = all files valid, 1 = any error, 2 = usage/setup problem. ~5 s JVM + bootstrap, then fast.

Headless set-up (how Litematica runs without a game): classpath = the game's libraries (from Mojang's version JSON) + the vanilla 26.3 client jar + Litematica + MaLiLib (Modrinth) + fabric-loader and ASM (MaLiLib's static init asks `FabricLoader` for the mod list), all downloaded by `python -m blockwright setup`, run on a JDK 25.

Limitations (honest list)
* Verified: parsing/loading (the code that interprets the file). **Not** exercised headlessly: placement creation,
  rendering, paste, material list — they need a client world. They all read blocks through the same
  `LitematicaBlockStateContainer#get`, which is verified cell by cell.
* Mixins are not applied headlessly. Irrelevant for files with `MinecraftDataVersion == 5023`; for older files the
  redstone-wire post-process fixer needs a mixin accessor, so such files fail in the harness with a `ClassCastException`
  (reported as "HARNESS LIMITATION").
* For files with an older data version, phase-2 mismatches are *expected* (Litematica's DataFixer/post-processing
  rewrites states); the validator reports them truthfully.
* No in-game load is automated; load a schematic in Litematica once when you change the writer.
