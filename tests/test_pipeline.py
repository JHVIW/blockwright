"""End-to-end smoke tests: scaffold -> build -> litematic round trip -> QA -> palette -> render (if textures exist)."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from blockwright import Build, config, palette, qa, registry as R
from blockwright.litematic import read_litematic, write_litematic
from blockwright.resolve import resolve

ROOT = Path(__file__).resolve().parents[1]
ENV = {**os.environ, "PYTHONPATH": str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", "")}


def _cli(*args, cwd):
    return subprocess.run([sys.executable, "-m", "blockwright", *args], cwd=cwd, env=ENV, capture_output=True,
                          text=True)


def test_litematic_round_trip(tmp_path):
    blocks = {(0, 0, 0): R.parse_state("oak_planks"), (2, 1, 3): R.parse_state("oak_stairs[facing=east,half=top]"),
              (1, 2, 1): R.parse_state("lantern[hanging=true]")}
    p = tmp_path / "rt.litematic"
    write_litematic(p, blocks, (3, 3, 4), name="RT", author="t", ground=1)
    got, size, meta = read_litematic(p)
    assert got == blocks and tuple(size) == (3, 3, 4)


@pytest.mark.parametrize("layout, pos, prop, value", [
    # outer corner: a stair facing north with a stair facing east beside it at its back -> outer_right
    ({(0, 0, 0): "oak_stairs[facing=north]", (0, 0, -1): "oak_stairs[facing=east]"}, (0, 0, 0), "shape", "outer_right"),
    ({(0, 0, 0): "oak_fence", (1, 0, 0): "stone"}, (0, 0, 0), "east", "true"),
    ({(0, 0, 0): "glass_pane", (0, 0, 1): "glass_pane"}, (0, 0, 0), "south", "true"),
    ({(0, 0, 0): "oak_leaves", (1, 0, 0): "oak_log"}, (0, 0, 0), "distance", "1"),
])
def test_resolver_cases(layout, pos, prop, value):
    out, stats = resolve({p: R.parse_state(s) for p, s in layout.items()})
    assert not stats["errors"]
    assert R.prop(out[pos], prop) == value, out[pos]


def test_scaffold_builds_qa_clean(tmp_path):
    r = _cli("new", "smoke_hut", "--style", "medieval", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    script = tmp_path / "builds" / "smoke_hut.py"
    r = subprocess.run([sys.executable, str(script), "--no-render"], cwd=tmp_path, env=ENV, capture_output=True,
                       text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    rep = json.loads((tmp_path / "out" / "reports" / "smoke_hut_qa.json").read_text(encoding="utf-8"))
    assert rep["summary"]["errors"] == 0, [i for i in rep["issues"] if i["severity"] == "error"]
    assert (tmp_path / "out" / "schematics" / "smoke_hut.litematic").is_file()
    assert (tmp_path / "out" / "materials" / "smoke_hut.md").is_file()
    # the CLI qa command re-runs QA from the file + sidecar meta
    r = _cli("qa", "out/schematics/smoke_hut.litematic", cwd=tmp_path)
    assert r.returncode == 0, r.stdout[-2000:]


def test_qa_flags_floating_and_dark_room():
    b = Build("t_float", "t")
    b.fill(0, 0, 0, 4, 0, 4, "stone")
    b.set(2, 5, 2, "stone")                      # floating
    rep = qa.run_qa(*b.structure()[:3])
    assert any(i["check"] == "floating" and i["severity"] == "error" for i in rep["issues"])


def test_palette_parsing_and_check():
    entries = palette.parse_palette("// mine\noak_planks\n*_log\n# comment\n#minecraft:wool\ntag:flowers\n")
    assert "minecraft:oak_planks" in entries and "minecraft:*_log" in entries
    assert "#minecraft:wool" in entries and "#minecraft:flowers" in entries
    blocks = {(0, 0, 0): R.parse_state("oak_planks"), (1, 0, 0): R.parse_state("spruce_log"),
              (2, 0, 0): R.parse_state("red_wool"), (3, 0, 0): R.parse_state("cobblestone"),
              (4, 0, 0): R.parse_state("oak_door[half=lower]"), (4, 1, 0): R.parse_state("oak_door[half=upper]")}
    bad = {it for it, _n, _p in palette.check_blocks(blocks, entries)}
    assert bad == {"minecraft:cobblestone", "minecraft:oak_door"}


def test_palette_constraint_reported_by_qa():
    b = Build("t_pal", "t", allowed_blocks=["oak_planks"])
    b.fill(0, 0, 0, 2, 0, 2, "oak_planks")
    b.set(1, 1, 1, "cobblestone")
    blocks, size, meta, _ = b.structure()
    rep = qa.run_qa(blocks, size, meta)
    errs = [i for i in rep["issues"] if i["check"] == "palette"]
    assert len(errs) == 1 and "cobblestone" in errs[0]["message"]


def test_install_to_copies_only_into_given_folder(tmp_path):
    ws, game = tmp_path / "ws", tmp_path / "game"
    (ws / "out" / "schematics").mkdir(parents=True)
    (ws / "out" / "schematics" / "a.litematic").write_bytes(b"x")
    (game / "mods").mkdir(parents=True)
    r = _cli("install-to", str(game), "--folder", "mine", cwd=ws)
    assert r.returncode == 0, r.stderr
    assert (game / "schematics" / "mine" / "a.litematic").is_file()
    assert _cli("install-to", str(tmp_path / "nope"), cwd=ws).returncode == 2


@pytest.mark.assets
def test_render_smoke(tmp_path):
    if not (config.assets_root() / ".extracted.json").is_file():
        pytest.skip("Minecraft textures not set up (python -m blockwright setup)")
    from blockwright.render import render_views
    b = Build("t_render", "t")
    b.fill(0, 0, 0, 4, 0, 4, "grass_block")
    b.fill(1, 1, 1, 3, 3, 3, "oak_planks")
    blocks, size, meta, _ = b.structure()
    paths = render_views(blocks, size, tmp_path, meta=meta, views=["iso_se"], width=320, height=240)
    from PIL import Image
    img = Image.open([p for p in paths if str(p).endswith("iso_se.png")][0])
    assert img.size == (320, 240) and len(set(img.convert("RGB").getdata())) > 20
