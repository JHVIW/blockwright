"""Shared pytest setup.

* The repo root goes on sys.path, so the suite runs from a plain clone without ``pip install``.
* Renderer tests need the Minecraft client textures, which are never shipped (``python -m blockwright setup``
  downloads them from Mojang).  Without them those tests are skipped, so CI runs everything else.
* Cross-checks against the real game classes (tests/test_core_gamecheck.py) need the validator set up with a JDK
  and skip themselves otherwise.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# renderer tests that only exercise pure code paths (no textures / models needed)
_NO_ASSETS_NEEDED = {"test_bits_decode_spanning", "test_reader_does_not_assume_air_at_palette_zero",
                     "test_physics_dump_is_used"}


def _assets_ready() -> bool:
    from blockwright import config
    return (config.assets_root() / ".extracted.json").is_file()


def pytest_collection_modifyitems(config, items):
    ready = _assets_ready()
    skip = pytest.mark.skip(reason="Minecraft textures not set up (run `python -m blockwright setup`)")
    for item in items:
        if Path(str(item.fspath)).name == "test_render.py" and item.name not in _NO_ASSETS_NEEDED:
            item.add_marker(pytest.mark.assets)
            if not ready:
                item.add_marker(skip)
