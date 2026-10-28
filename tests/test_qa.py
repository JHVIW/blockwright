"""Tests for blockwright/qa.py on hand-made fixtures.  Run:  python -m pytest tests/test_qa.py -q   (or python tests/test_qa.py)"""
import importlib.util
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from blockwright import qa  # noqa: E402

PLANKS = "minecraft:oak_planks"
COBBLE = "minecraft:cobblestone"
DOOR_L = "minecraft:oak_door[facing=south,half=lower,hinge=left,open=false,powered=false]"
DOOR_U = "minecraft:oak_door[facing=south,half=upper,hinge=left,open=false,powered=false]"
LANTERN_HANG = "minecraft:lantern[hanging=true,waterlogged=false]"
LANTERN_STAND = "minecraft:lantern[hanging=false,waterlogged=false]"
PANE_NS = "minecraft:glass_pane[east=true,north=false,south=false,waterlogged=false,west=true]"


def stair(facing):
    return f"minecraft:oak_stairs[facing={facing},half=bottom,shape=straight,waterlogged=false]"


def hut(storeys=1, lit=True, door=True):
    """7 x (4*storeys+1) x 7 hut on flat terrain: walls x/z in 1..7, interior 2..6, floor at y=0 (= ground),
    roof slab of planks.  Box 9 x (height+2) x 9, ground y=0, door in the north wall at x=4, entrance (4,1,0)."""
    top = 4 * storeys
    blocks = {}
    for x in range(1, 8):
        for z in range(1, 8):
            blocks[(x, 0, z)] = PLANKS                       # floor (replaces the grass layer)
            blocks[(x, top, z)] = PLANKS                     # roof
            for y in range(1, top):
                if x in (1, 7) or z in (1, 7):
                    blocks[(x, y, z)] = COBBLE if y == 1 else PLANKS
            for s in range(1, storeys):
                blocks[(x, 4 * s, z)] = PLANKS               # upper floors
    blocks[(1, 2, 4)] = "minecraft:glass_pane[east=false,north=true,south=true,waterlogged=false,west=false]"  # window
    if door:
        blocks[(4, 1, 1)] = DOOR_L
        blocks[(4, 2, 1)] = DOOR_U
    if lit:
        for s in range(storeys):
            blocks[(4, 4 * s + 3, 4)] = LANTERN_HANG          # hangs from the floor/roof above
    rooms = {"ground_floor": (4, 1, 4)}
    if storeys > 1:
        rooms["upstairs"] = (4, 5, 4)
    meta = {"slug": "test_hut", "title": "Test hut", "ground": 0, "rooms": rooms, "entrances": [(4, 1, 0)], "notes": ""}
    return blocks, (9, top + 2, 9), meta


def add_staircase(blocks):
    """Oak stairs climbing east along the south wall (z=6) from y=1 to the upper floor at y=4, with a stairwell."""
    blocks[(2, 1, 6)] = stair("east")
    blocks[(3, 2, 6)] = stair("east")
    blocks[(4, 3, 6)] = stair("east")
    for x in (2, 3, 4):
        blocks.pop((x, 4, 6), None)                          # stairwell opening in the upper floor
    return blocks


def errors(rep, check=None):
    return [i for i in rep["issues"] if i["severity"] == "error" and (check is None or i["check"] == check)]


class TestQA(unittest.TestCase):
    def test_sealed_hut_passes(self):
        b, size, meta = hut()
        rep = qa.run_qa(b, size, meta)
        self.assertEqual(errors(rep), [], json.dumps(errors(rep), indent=1))
        self.assertTrue(rep["summary"]["passed"])
        self.assertEqual(rep["checks"]["enclosure"]["rooms"]["ground_floor"]["leaks"], [])
        self.assertTrue(rep["checks"]["walkability"]["rooms"]["ground_floor"]["reachable"])
        self.assertEqual(rep["checks"]["lighting"]["rooms"]["ground_floor"]["spawnable_spots"], 0)
        m = rep["checks"]["metrics"]
        self.assertEqual(m["footprint"]["convex_corners"], 4)
        self.assertEqual(m["footprint"]["concave_corners"], 0)
        self.assertEqual(m["footprint"]["area"], 49)
        # 25 interior cells + the door niche: the closed south-facing door's panel sits on the cell's north side, so
        # the rest of the door cell belongs to the room
        self.assertEqual(m["rooms"]["ground_floor"]["floor_area"], 26)
        self.assertEqual(m["facades"]["west"]["windows"], 1)
        self.assertEqual(rep["checks"]["walkability"]["doors"][0]["both_sides_clear"], True)

    def test_missing_roof_block_leaks(self):
        b, size, meta = hut()
        del b[(3, 4, 3)]
        rep = qa.run_qa(b, size, meta)
        leaks = rep["checks"]["enclosure"]["rooms"]["ground_floor"]["leaks"]
        self.assertTrue(leaks)
        self.assertEqual(leaks[0]["breach"], [3, 4, 3])
        self.assertEqual(leaks[0]["kind"], "roof/ceiling")
        self.assertTrue(any("rain" in i["message"] for i in errors(rep, "enclosure")))

    def test_missing_wall_block_leaks(self):
        b, size, meta = hut()
        del b[(7, 2, 5)]
        rep = qa.run_qa(b, size, meta)
        leaks = rep["checks"]["enclosure"]["rooms"]["ground_floor"]["leaks"]
        self.assertEqual([lk["breach"] for lk in leaks], [[7, 2, 5]])
        self.assertEqual(leaks[0]["kind"], "wall")

    def test_wide_gap_leak_and_room_kept(self):
        b, size, meta = hut()
        for z in (3, 4, 5):
            for y in (1, 2):
                del b[(7, y, z)]                              # 3 x 2 hole in the east wall
        rep = qa.run_qa(b, size, meta)
        r = rep["checks"]["enclosure"]["rooms"]["ground_floor"]
        self.assertTrue(r["leaks"])
        bx, by, bz = r["leaks"][0]["breach"]
        self.assertEqual(bx, 7)
        self.assertIn(bz, (3, 4, 5))
        self.assertGreater(r["volume"], 50)                   # the roofed room is still analysed

    def test_narrow_corridor_room_leak(self):
        S = "minecraft:stone"
        b = {}
        for x in range(0, 9):                                 # 1-wide, 2-high corridor along x, closed except x=8 end
            b[(x, 0, 2)] = S
            b[(x, 3, 2)] = S
            for y in (1, 2):
                b[(x, y, 1)] = S
                b[(x, y, 3)] = S
        for y in (1, 2):
            b[(0, y, 2)] = S
        b[(8, 1, 2)] = S                                      # end wall with a hole at (8, 2, 2)
        meta = {"ground": 0, "rooms": {"corridor": (2, 1, 2)}, "entrances": []}
        rep = qa.run_qa(b, (9, 5, 5), meta)
        leaks = rep["checks"]["enclosure"]["rooms"]["corridor"]["leaks"]
        self.assertEqual(leaks[0]["breach"], [8, 2, 2])

    def test_chimney_flue_is_a_warning(self):
        b, size, meta = hut()
        size = (9, 8, 9)
        b[(6, 1, 4)] = "minecraft:campfire[facing=west,lit=true,signal_fire=false,waterlogged=false]"
        for y in range(2, 7):
            for (x, z) in ((5, 3), (5, 5), (6, 3), (6, 5), (7, 4)):
                b[(x, y, z)] = "minecraft:bricks"
            b.pop((6, y, 4), None)                            # open flue straight up through the roof
        for y in (3, 4, 5, 6):
            b[(5, y, 4)] = "minecraft:bricks"
        b.pop((5, 2, 4), None)                                # hearth opening (5,1..2,4) -- (5,1,4) is interior air
        rep = qa.run_qa(b, size, meta)
        enc = [i for i in rep["issues"] if i["check"] == "enclosure"]
        self.assertTrue(enc)
        self.assertTrue(all(i["severity"] == "warn" for i in enc), enc)

    def test_open_doorway_is_a_leak_but_closed_door_is_not(self):
        b, size, meta = hut(door=False)
        b.pop((4, 1, 1), None)
        b.pop((4, 2, 1), None)
        rep = qa.run_qa(b, size, meta)
        self.assertTrue(rep["checks"]["enclosure"]["rooms"]["ground_floor"]["leaks"])
        self.assertTrue(rep["checks"]["walkability"]["rooms"]["ground_floor"]["reachable"])

    def test_upstairs_unreachable_without_stairs(self):
        b, size, meta = hut(storeys=2)
        rep = qa.run_qa(b, size, meta)
        w = rep["checks"]["walkability"]["rooms"]
        self.assertTrue(w["ground_floor"]["reachable"])
        self.assertFalse(w["upstairs"]["reachable"])
        self.assertIsNotNone(w["upstairs"]["nearest"])
        self.assertTrue(any("upstairs" in i["message"] for i in errors(rep, "walkability")))

    def test_upstairs_reachable_with_staircase(self):
        b, size, meta = hut(storeys=2)
        add_staircase(b)
        rep = qa.run_qa(b, size, meta)
        w = rep["checks"]["walkability"]["rooms"]
        self.assertTrue(w["ground_floor"]["reachable"])
        self.assertTrue(w["upstairs"]["reachable"], json.dumps(errors(rep), indent=1))
        self.assertEqual(errors(rep), [], json.dumps(errors(rep), indent=1))

    def test_upstairs_reachable_with_ladder(self):
        b, size, meta = hut(storeys=2)
        b.pop((6, 4, 6))                                      # hatch hole in the upper floor
        for y in (1, 2, 3, 4):
            b[(6, y, 6)] = "minecraft:ladder[facing=north,waterlogged=false]"   # on the south wall (z=7)
        rep = qa.run_qa(b, size, meta)
        self.assertTrue(rep["checks"]["walkability"]["rooms"]["upstairs"]["reachable"], json.dumps(errors(rep), indent=1))

    def test_ladder_with_trapdoor_hatch(self):
        # ladder up to y=3, trapdoor in the floor hole: climbable once opened only if its facing matches the ladder's
        for facing, ok in (("north", True), ("south", False)):
            b, size, meta = hut(storeys=2)
            b.pop((6, 4, 6))
            for y in (1, 2, 3):
                b[(6, y, 6)] = "minecraft:ladder[facing=north,waterlogged=false]"
            b[(6, 4, 6)] = f"minecraft:oak_trapdoor[facing={facing},half=top,open=false,powered=false,waterlogged=false]"
            rep = qa.run_qa(b, size, meta)
            self.assertEqual(rep["checks"]["walkability"]["rooms"]["upstairs"]["reachable"], ok, facing)
            self.assertEqual(rep["checks"]["enclosure"]["rooms"]["ground_floor"]["leaks"], [])

    def test_ladder_too_short_does_not_reach(self):
        b, size, meta = hut(storeys=2)
        b.pop((6, 4, 6))
        for y in (1, 2):                                      # ends two blocks below the upper floor
            b[(6, y, 6)] = "minecraft:ladder[facing=north,waterlogged=false]"
        rep = qa.run_qa(b, size, meta)
        self.assertFalse(rep["checks"]["walkability"]["rooms"]["upstairs"]["reachable"])

    def test_floating_block(self):
        b, size, meta = hut()
        size = (9, 8, 9)
        b[(4, 6, 4)] = "minecraft:stone"
        rep = qa.run_qa(b, size, meta)
        fl = errors(rep, "floating")
        self.assertEqual(len(fl), 1)
        self.assertEqual(fl[0]["pos"], [4, 6, 4])
        self.assertEqual(rep["checks"]["floating"]["floating_blocks"], 1)

    def test_tree_leaves_connected_through_logs_are_fine(self):
        b, size, meta = hut()
        size = (12, 9, 9)
        for y in range(1, 5):
            b[(10, y, 4)] = "minecraft:oak_log[axis=y]"
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                b[(10 + dx, 5, 4 + dz)] = "minecraft:oak_leaves[distance=1,persistent=true,waterlogged=false]"
        rep = qa.run_qa(b, size, meta)
        self.assertEqual(errors(rep, "floating"), [])

    def test_unlit_room(self):
        b, size, meta = hut(lit=False)
        rep = qa.run_qa(b, size, meta)
        le = errors(rep, "lighting")
        self.assertEqual(len(le), 1)
        # 25 floor cells + the door niche (a zombie's 0.6-wide spawn box clears the 3/16 door panel)
        self.assertEqual(rep["checks"]["lighting"]["rooms"]["ground_floor"]["spawnable_spots"], 26)

    def test_carpet_floor_prevents_spawning(self):
        b, size, meta = hut(lit=False)
        for x in range(2, 7):
            for z in range(2, 7):
                b[(x, 1, z)] = "minecraft:white_carpet"
        rep = qa.run_qa(b, size, meta)
        self.assertEqual(rep["checks"]["lighting"]["rooms"]["ground_floor"]["spawnable_spots"], 1)
        self.assertEqual(errors(rep, "lighting")[0]["positions"], [[4, 1, 1]])     # only the un-carpeted door niche
        self.assertTrue(rep["checks"]["walkability"]["rooms"]["ground_floor"]["reachable"])

    def test_room_lit_by_distant_lantern(self):
        S = "minecraft:stone"
        b = {}
        n = 22                                               # 1-wide, 2-high hall along x, lantern at the west end
        for x in range(0, n + 2):
            for z in range(0, 3):
                b[(x, 0, z)] = S
                b[(x, 3, z)] = S
            for y in (1, 2):
                b[(x, y, 0)] = S
                b[(x, y, 2)] = S
        for y in (1, 2):
            b[(0, y, 1)] = S
            b[(n + 1, y, 1)] = S
        b[(1, 2, 1)] = LANTERN_HANG
        rep = qa.run_qa(b, (n + 2, 5, 3), {"ground": 0, "rooms": {"hall": (5, 1, 1)}, "entrances": []})
        L = qa.block_light(qa.World(qa.game_data(), b, (n + 2, 5, 3), 0))
        self.assertEqual([int(L[x + 1, 2, 2]) for x in range(1, 17)], list(range(14, -1, -1)) + [0])
        spots = errors(rep, "lighting")[0]["positions"]
        self.assertEqual(spots, [[x, 1, 1] for x in range(15, n + 1)])   # 15 steps from the lantern: light 0

    def test_partial_blocks_in_walls_leak(self):
        cases = {
            "stair in the wall": ((7, 2, 4), "minecraft:oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]"),
            "closed trapdoor in a window": ((1, 2, 4), "minecraft:oak_trapdoor[facing=east,half=bottom,open=false,powered=false,waterlogged=false]"),
            "bottom slab in the wall": ((4, 2, 7), "minecraft:oak_slab[type=bottom,waterlogged=false]"),
        }
        for label, (pos, s) in cases.items():
            b, size, meta = hut()
            b[pos] = s
            rep = qa.run_qa(b, size, meta)
            leaks = rep["checks"]["enclosure"]["rooms"]["ground_floor"]["leaks"]
            self.assertEqual([lk["breach"] for lk in leaks], [list(pos)], label)

    def test_open_trapdoor_shutter_seals(self):
        b, size, meta = hut()
        # open trapdoor flat against the outer face of the window cell (its panel covers the cell's east face)
        b[(1, 2, 4)] = "minecraft:oak_trapdoor[facing=west,half=bottom,open=true,powered=false,waterlogged=false]"
        rep = qa.run_qa(b, size, meta)
        self.assertEqual(rep["checks"]["enclosure"]["rooms"]["ground_floor"]["leaks"], [])

    def test_diagonal_leak_through_two_stairs(self):
        b, size, meta = hut()
        size = (10, 6, 9)
        # A: high half to the east (outer face sealed), open upper-west quarter faces the room
        b[(7, 2, 4)] = "minecraft:oak_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]"
        # B: high half to the north; its open upper-south half meets A's open quarter and runs out of its east face
        b[(7, 2, 3)] = "minecraft:oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]"
        rep = qa.run_qa(b, size, meta)
        leaks = rep["checks"]["enclosure"]["rooms"]["ground_floor"]["leaks"]
        self.assertTrue(leaks)
        self.assertIn(leaks[0]["breach"], ([7, 2, 4], [7, 2, 3]))
        b2, size2, meta2 = hut()
        b2[(7, 2, 4)] = b[(7, 2, 4)]                        # A alone (planks around it) does not leak
        rep2 = qa.run_qa(b2, size2, meta2)
        self.assertEqual(rep2["checks"]["enclosure"]["rooms"]["ground_floor"]["leaks"], [])

    def test_vine_up_face_quirk(self):
        # VineBlock tests the block above on its UP face (isAcceptableNeighbour(level, above, DOWN)), verified in game
        b, size, meta = hut()
        size = (12, 7, 9)
        b[(9, 3, 2)] = "minecraft:oak_slab[type=bottom,waterlogged=false]"
        b[(9, 2, 2)] = "minecraft:vine[east=false,north=false,south=false,up=true,west=false]"   # under bottom slab: breaks
        b[(9, 3, 6)] = "minecraft:oak_slab[type=top,waterlogged=false]"
        b[(9, 2, 6)] = "minecraft:vine[east=false,north=false,south=false,up=true,west=false]"   # under top slab: fine
        for y in (1, 2, 3):
            b[(10, y, 2)] = COBBLE                                      # pillars holding the slabs
            b[(10, y, 6)] = COBBLE
        rep = qa.run_qa(b, size, meta)
        self.assertEqual(sorted(tuple(i["pos"]) for i in errors(rep, "support")), [(9, 2, 2)])

    def test_falling_blocks(self):
        b, size, meta = hut()
        size = (12, 6, 9)
        b[(9, 1, 2)] = "minecraft:poppy"
        b[(9, 2, 2)] = "minecraft:sand"                                # on a poppy: holds (not replaceable)
        b[(10, 1, 2)] = "minecraft:short_grass"
        b[(10, 2, 2)] = "minecraft:gravel"                             # on short grass: falls
        b[(10, 1, 6)] = "minecraft:snow[layers=1]"
        b[(10, 2, 6)] = "minecraft:white_concrete_powder"              # on a snow layer: falls
        rep = qa.run_qa(b, size, meta)
        falls = [tuple(i["pos"]) for i in errors(rep, "support") if "falls" in i["message"]]
        self.assertEqual(sorted(falls), [(10, 2, 2), (10, 2, 6)])

    def test_mushroom_and_crop_light(self):
        b, size, meta = hut(lit=False)
        size = (12, 6, 9)
        b[(9, 1, 2)] = "minecraft:brown_mushroom"                      # outdoors on grass: sky light 15 -> breaks
        b[(9, 0, 4)] = "minecraft:podzol"
        b[(9, 1, 4)] = "minecraft:red_mushroom"                        # on podzol: light does not matter
        b[(3, 1, 3)] = "minecraft:brown_mushroom"                      # dark sealed room, on planks: fine
        b[(6, 0, 6)] = "minecraft:farmland[moisture=7]"
        b[(6, 1, 6)] = "minecraft:wheat[age=0]"                        # far from the window: sky light 6 -> breaks
        b[(10, 0, 6)] = "minecraft:farmland[moisture=7]"
        b[(10, 1, 6)] = "minecraft:wheat[age=0]"                       # outdoors: fine
        rep = qa.run_qa(b, size, meta)
        bad = sorted(tuple(i["pos"]) for i in errors(rep, "support"))
        self.assertEqual(bad, [(6, 1, 6), (9, 1, 2)])
        w = qa.World(qa.game_data(), b, size, 0)
        sky = qa.sky_light(w)
        self.assertEqual(int(sky[10, 2, 3]), 15)                       # (9, 1, 2) under open sky
        self.assertEqual(int(sky[3, 3, 5]), 13)                        # just inside the glass-pane window (1, 2, 4)
        # light passes a closed door (doors do not occlude light): outside 15, door cell 14, then -1 per step
        self.assertEqual(int(sky[5, 2, 3]), 13)                        # (4, 1, 2) right behind the door
        self.assertEqual(int(sky[7, 2, 7]), 7)                         # the wheat (6, 1, 6)
        box = {(x, y, z): "minecraft:stone" for x in range(5) for y in range(5) for z in range(5)
               if x in (0, 4) or y in (0, 4) or z in (0, 4)}
        self.assertEqual(int(qa.sky_light(qa.World(qa.game_data(), box, (5, 5, 5), 0))[3, 3, 3]), 0)   # sealed box

    def test_fluid_containment(self):
        b, size, meta = hut()
        size = (14, 6, 9)
        b[(9, 1, 2)] = "minecraft:water[level=0]"                      # water on the lawn: floods
        b[(11, 0, 5)] = "minecraft:water[level=0]"                     # pond cut into the terrain: contained
        b[(11, 1, 5)] = "minecraft:lily_pad"
        b[(12, 1, 7)] = COBBLE
        b[(12, 2, 7)] = "minecraft:cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]"
        b[(12, 3, 7)] = "minecraft:lantern[hanging=false,waterlogged=true]"   # waterlogged lantern on a post: spills
        rep = qa.run_qa(b, size, meta)
        fl = [i for i in errors(rep, "support") if "not contained" in i["message"]]
        self.assertEqual(len(fl), 1)
        self.assertEqual(sorted(map(tuple, fl[0]["positions"])), [(9, 1, 2), (12, 3, 7)])

    def test_random_tick_changes(self):
        b, size, meta = hut()
        size = (16, 9, 9)
        for y in range(1, 5):
            b[(11, y, 4)] = "minecraft:oak_log[axis=y]"
        b[(11, 5, 4)] = "minecraft:oak_leaves[distance=1,persistent=false,waterlogged=false]"   # next to the log: ok
        b[(12, 5, 4)] = "minecraft:oak_leaves[distance=7,persistent=false,waterlogged=false]"   # stored 7: decays
        b[(14, 1, 1)] = "minecraft:oak_leaves[distance=1,persistent=false,waterlogged=false]"   # no log: decays
        b[(14, 1, 7)] = "minecraft:oak_leaves[distance=7,persistent=true,waterlogged=false]"    # persistent: ok
        b[(9, 1, 7)] = "minecraft:snow[layers=1]"
        b[(9, 1, 6)] = LANTERN_STAND                                   # block light 14 next to the snow: melts
        b[(13, 1, 7)] = "minecraft:snow[layers=1]"                     # far from light: stays
        b[(9, 0, 1)] = "minecraft:farmland[moisture=7]"                # bare, dry: warn
        b[(10, 0, 1)] = "minecraft:farmland[moisture=7]"
        b[(10, 1, 1)] = "minecraft:carrots[age=0]"                     # crop keeps it
        b[(13, 1, 2)] = "minecraft:oak_sapling[stage=0]"               # outdoors: grows into a tree (warn)
        rep = qa.run_qa(b, size, meta)
        sup = [i for i in rep["issues"] if i["check"] == "support"]
        decay = [i for i in sup if "decay" in i["message"]]
        self.assertEqual(sorted(map(tuple, decay[0]["positions"])), [(12, 5, 4), (14, 1, 1)])
        melt = [i for i in sup if "melt" in i["message"]]
        self.assertEqual(melt[0]["positions"], [[9, 1, 7]])
        dry = [i for i in sup if "farmland" in i["message"]]
        self.assertEqual((dry[0]["severity"], dry[0]["positions"]), ("warn", [[9, 0, 1]]))
        grow = [i for i in sup if "sapling" in i["message"]]
        self.assertEqual((grow[0]["severity"], grow[0]["positions"]), ("warn", [[13, 1, 2]]))

    def test_explicit_air_cannot_carve_a_cellar(self):
        b, size, meta = hut()
        b[(4, 0, 4)] = "minecraft:air"           # meant as a hole in the floor: the schematic cannot express it
        rep = qa.run_qa(b, size, meta)
        warns = [i for i in rep["issues"] if i["check"] == "validity" and i["severity"] == "warn"]
        self.assertTrue(any("cannot carve terrain" in i["message"] for i in warns), warns)
        w = qa.World(qa.game_data(), b, size, 0)
        self.assertEqual(w.at(4, 0, 4).name, "minecraft:grass_block")   # implied terrain, not air

    def test_lantern_without_support(self):
        b, size, meta = hut()
        b[(3, 2, 3)] = LANTERN_STAND                          # standing lantern in mid air
        rep = qa.run_qa(b, size, meta)
        sup = errors(rep, "support")
        self.assertEqual(len(sup), 1)
        self.assertEqual(sup[0]["pos"], [3, 2, 3])
        self.assertIn("center support below", sup[0]["message"])

    def test_support_rules_misc(self):
        b, size, meta = hut()
        size = (12, 6, 9)
        b[(9, 1, 2)] = "minecraft:poppy"                                      # on grass: ok
        b[(9, 0, 4)] = "minecraft:stone"
        b[(9, 1, 4)] = "minecraft:poppy"                                      # on stone: fails
        b[(10, 1, 2)] = "minecraft:torch"                                     # on grass: ok
        b[(10, 0, 4)] = "minecraft:oak_slab[type=bottom,waterlogged=false]"
        b[(10, 1, 4)] = "minecraft:torch"                                     # on a bottom slab: fails (no center support)
        b[(5, 2, 2)] = "minecraft:wall_torch[facing=south]"                   # on the north wall, inside: ok
        b[(3, 2, 2)] = "minecraft:wall_torch[facing=north]"                   # facing away from the wall: fails
        b[(9, 1, 6)] = "minecraft:white_carpet"                               # on grass: ok
        rep = qa.run_qa(b, size, meta)
        bad = sorted(tuple(i["pos"]) for i in errors(rep, "support"))
        self.assertEqual(bad, [(3, 2, 2), (9, 1, 4), (10, 1, 4)])

    def test_orphan_door_half(self):
        b, size, meta = hut()
        del b[(4, 2, 1)]
        b[(4, 2, 1)] = PLANKS
        rep = qa.run_qa(b, size, meta)
        self.assertTrue(any("without its upper half" in i["message"] for i in errors(rep, "support")))

    def test_door_blocked_by_furniture(self):
        b, size, meta = hut()
        b[(4, 1, 2)] = "minecraft:barrel[facing=up,open=false]"
        rep = qa.run_qa(b, size, meta)
        self.assertTrue(any("door at (4, 1, 1)" in i["message"] for i in errors(rep, "walkability")))
        b[(4, 1, 2)] = stair("west")                          # a stair "chair" right behind the door
        rep = qa.run_qa(b, size, meta)
        self.assertTrue(any("door at (4, 1, 1)" in i["message"] for i in errors(rep, "walkability")))
        self.assertFalse(rep["checks"]["walkability"]["rooms"]["ground_floor"]["reachable"])

    def test_invalid_states(self):
        b, size, meta = hut()
        b[(8, 1, 8)] = "minecraft:not_a_block"
        b[(8, 1, 0)] = "minecraft:oak_stairs[facing=up]"
        rep = qa.run_qa(b, size, meta)
        msgs = [i["message"] for i in errors(rep, "validity")]
        self.assertEqual(len(msgs), 2)
        self.assertTrue(any("unknown block" in m for m in msgs))
        self.assertTrue(any("illegal value facing=up" in m for m in msgs))

    def test_gable_roof_hut(self):
        b, size, meta = hut()
        size = (9, 10, 9)
        for x in range(1, 8):
            for z in range(1, 8):
                b.pop((x, 4, z), None)                        # remove the flat roof
        for x in range(0, 9):
            for k in range(0, 4):
                b[(x, 4 + k, k)] = stair("south")             # north slope
                b[(x, 4 + k, 8 - k)] = stair("north")         # south slope
            b[(x, 8, 4)] = "minecraft:oak_slab[type=bottom,waterlogged=false]"  # ridge cap
        for x in (1, 7):                                       # gable end walls
            for k in range(0, 4):
                for z in range(k + 1, 8 - k):
                    b[(x, 4 + k, z)] = PLANKS
        b[(4, 3, 4)] = "minecraft:lantern[hanging=false,waterlogged=false]"
        b[(4, 2, 4)] = "minecraft:oak_fence[east=false,north=false,south=false,waterlogged=false,west=false]"
        b[(4, 1, 4)] = "minecraft:oak_fence[east=false,north=false,south=false,waterlogged=false,west=false]"
        meta["rooms"] = {"ground_floor": (3, 1, 3)}
        rep = qa.run_qa(b, size, meta)
        self.assertEqual(errors(rep), [], json.dumps(errors(rep), indent=1))
        roof = rep["checks"]["metrics"]["roof"]
        self.assertEqual(roof["ridge_heights"], [8])
        self.assertEqual(roof["distinct_ridge_heights"], 1)

    def test_walk_physics(self):
        S = "minecraft:stone"
        SLAB = "minecraft:oak_slab[type=bottom,waterlogged=false]"
        FENCE = "minecraft:oak_fence[east=false,north=true,south=true,waterlogged=false,west=false]"

        def corridor(b, ceiling_y=None, h=4):
            for x in range(0, 10):
                for y in range(1, h):
                    b[(x, y, 1)] = S
                    b[(x, y, 3)] = S
                if ceiling_y is not None:
                    for z in range(0, 5):
                        b.setdefault((x, ceiling_y, z), S)
            for y in range(1, h):
                b[(0, y, 2)] = S
                b[(9, y, 2)] = S
            return b

        def reach(b, target, entrance=(2, 1, 2)):
            meta = {"ground": 0, "rooms": {"t": target}, "entrances": [entrance]}
            return qa.run_qa(b, (10, 8, 5), meta)["checks"]["walkability"]["rooms"]["t"]["reachable"]

        self.assertTrue(reach({(5, 1, 2): S}, (5, 2, 2)))                              # jump 1 block in the open
        self.assertFalse(reach({(5, 1, 2): S, (5, 2, 2): S}, (5, 3, 2)))              # 2 blocks: no
        self.assertFalse(reach(corridor({(5, 1, 2): S}, 3, 3), (5, 2, 2)))            # 2-high tunnel: cannot jump up
        self.assertTrue(reach(corridor({(5, 1, 2): S}, 4, 4), (5, 2, 2)))             # 3-high: can
        self.assertTrue(reach(corridor({(5, 1, 2): SLAB, (6, 1, 2): S}, 4, 4), (6, 2, 2)))  # slab step
        self.assertFalse(reach(corridor({(5, 1, 2): FENCE}), (8, 1, 2)))              # fence post blocks
        self.assertTrue(reach(corridor({(x, 1, 2): "minecraft:white_carpet" for x in range(2, 9)}, h=3), (8, 1, 2)))
        plat = {(x, y, 2): S for x in range(0, 4) for y in range(1, 6)}               # 5-high platform
        self.assertFalse(reach(dict(plat), (8, 1, 2), entrance=(1, 6, 2)))            # 5 drop onto grass: unsafe
        plat.update({(x, 0, 2): "minecraft:water[level=0]" for x in range(4, 7)})
        self.assertTrue(reach(plat, (8, 1, 2), entrance=(1, 6, 2)))                   # into water: fine

    def test_support_facts_match_game(self):
        # spot checks of values verified against the running 26.3 game (a Java harness on the real game classes)
        g = qa.game_data()
        cases = {  # state: (center mask, rigid mask, solid, valid_spawn)
            "minecraft:oak_fence[east=false,north=false,south=false,waterlogged=false,west=false]": (3, 0, True, False),
            "minecraft:oak_leaves[distance=7,persistent=true,waterlogged=false]": (0, 0, True, False),
            "minecraft:glass": (63, 63, True, False),
            "minecraft:oak_slab[type=bottom,waterlogged=false]": (1, 1, True, False),
            "minecraft:iron_chain[axis=y,waterlogged=false]": (3, 0, True, False),
            "minecraft:oak_fence_gate[facing=north,in_wall=false,open=false,powered=false]": (2, 0, True, False),
            "minecraft:grass_block[snowy=false]": (63, 63, True, True),
            "minecraft:jack_o_lantern[facing=north]": (63, 63, True, True),
        }
        for s, (c, r, solid, spawn) in cases.items():
            st = g.info(s)
            self.assertEqual((st.center, st.rigid, st.solid, st.valid_spawn), (c, r, solid, spawn), s)

    def test_write_report(self):
        b, size, meta = hut()
        rep = qa.run_qa(b, size, meta)
        with tempfile.TemporaryDirectory() as d:
            qa.write_report(rep, Path(d) / "r" / "x_qa.md", Path(d) / "r" / "x_qa.json")
            md = (Path(d) / "r" / "x_qa.md").read_text(encoding="utf-8")
            js = json.loads((Path(d) / "r" / "x_qa.json").read_text(encoding="utf-8"))
        self.assertIn("PASS", md)
        self.assertEqual(js["summary"]["errors"], 0)

    def test_performance_45x45x40(self):
        # a dense village-sized box: 16 huts (2 storeys) on a 4x4 grid + noise landscaping
        blocks = {}
        for i in range(4):
            for j in range(4):
                b, _, _ = hut(storeys=2)
                add_staircase(b)
                for (x, y, z), s in b.items():
                    blocks[(x + i * 11, y, z + j * 11)] = s
        for x in range(45):
            for z in range(45):
                if (x * 7 + z * 13) % 5 == 0 and (x, 1, z) not in blocks and (x, 0, z) not in blocks:
                    blocks[(x, 1, z)] = "minecraft:short_grass"
        meta = {"ground": 0, "rooms": {f"r{i}{j}": (4 + i * 11, 5, 4 + j * 11) for i in range(4) for j in range(4)},
                "entrances": [(4, 1, 0)], "slug": "perf", "title": "perf"}
        t = time.perf_counter()
        rep = qa.run_qa(blocks, (45, 40, 45), meta)
        dt = time.perf_counter() - t
        print(f"\n45x45x40 QA: {dt:.2f}s  {rep['timing_s']}")
        self.assertLess(dt, 60.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
