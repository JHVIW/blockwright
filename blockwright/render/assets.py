"""Asset cache: extraction from the vanilla client jar and texture loading.

Mojang's assets are never shipped with blockwright.  ``python -m blockwright setup`` downloads the official client
jar into the user cache and extracts what the renderer needs into ``<cache>/minecraft/<version>/assets/minecraft/``
(same relative layout as in the jar): blockstates, models/block, textures/block (+ .mcmeta), textures/entity,
textures/colormap.
"""
from __future__ import annotations

import json
import os
import pathlib
import threading
import zipfile

import numpy as np
from PIL import Image

from .. import config as _config

ASSETS = _config.assets_root()
MC = ASSETS / "minecraft"
CLIENT_JAR = _config.client_jar()
REGISTRY_JSON = _config.data_file("blocks")

_PREFIXES = (
    "assets/minecraft/blockstates/",
    "assets/minecraft/models/block/",
    "assets/minecraft/textures/block/",
    "assets/minecraft/textures/entity/",
    "assets/minecraft/textures/colormap/",
)
_MARKER = ASSETS / ".extracted.json"
_lock = threading.Lock()


def ensure_assets(jar: str | os.PathLike | None = None, force: bool = False) -> pathlib.Path:
    """Extract the needed client assets into the cache once. Returns the assets root."""
    jar = pathlib.Path(jar) if jar else CLIENT_JAR
    with _lock:
        if _MARKER.exists() and not force:
            return ASSETS
        if not jar.exists():
            raise FileNotFoundError(f"Minecraft client jar not found ({jar}). Run `python -m blockwright setup` once "
                                    "to download it from Mojang and extract the textures.")
        n = 0
        with zipfile.ZipFile(jar) as z:
            for info in z.infolist():
                name = info.filename
                if name.endswith("/") or not name.startswith(_PREFIXES):
                    continue
                dest = ASSETS / name[len("assets/"):]
                dest.parent.mkdir(parents=True, exist_ok=True)
                with z.open(info) as src, open(dest, "wb") as out:
                    out.write(src.read())
                n += 1
        _MARKER.write_text(json.dumps({"jar": jar.name, "size": jar.stat().st_size, "files": n}))
    return ASSETS


def strip_ns(name: str) -> str:
    return name[10:] if name.startswith("minecraft:") else name


_json_cache: dict[str, object] = {}


def load_json(rel: str):
    """Load <assets>/minecraft/<rel> as JSON (cached). Returns None when missing."""
    if rel in _json_cache:
        return _json_cache[rel]
    p = MC / rel
    val = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    _json_cache[rel] = val
    return val


def blockstate_json(block_id: str):
    return load_json(f"blockstates/{strip_ns(block_id)}.json")


def model_json(model_id: str):
    """model_id like 'minecraft:block/oak_stairs' or 'block/oak_stairs'."""
    return load_json(f"models/{strip_ns(model_id)}.json")


_tex_cache: dict[str, np.ndarray | None] = {}


def load_texture(sprite: str) -> np.ndarray | None:
    """Return RGBA uint8 array (H, W, 4) for a sprite id like 'minecraft:block/stone' or
    'entity/chest/normal'. Animated textures return their first frame. None when missing."""
    key = strip_ns(sprite)
    if key in _tex_cache:
        return _tex_cache[key]
    p = MC / "textures" / (key + ".png")
    if not p.exists():
        _tex_cache[key] = None
        return None
    img = np.asarray(Image.open(p).convert("RGBA"))
    meta_p = p.with_name(p.name + ".mcmeta")
    if meta_p.exists():
        try:
            meta = json.loads(meta_p.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
        anim = meta.get("animation")
        if anim is not None:
            h, w = img.shape[:2]
            fw = int(anim.get("width", min(w, h)))
            fh = int(anim.get("height", fw if "width" in anim else min(w, h)))
            frames = anim.get("frames")
            idx = 0
            if frames:
                f0 = frames[0]
                idx = int(f0["index"] if isinstance(f0, dict) else f0)
            per_row = max(1, w // fw)
            fx, fy = (idx % per_row) * fw, (idx // per_row) * fh
            if fy + fh <= h and fx + fw <= w:
                img = img[fy:fy + fh, fx:fx + fw]
    img = np.ascontiguousarray(img)
    _tex_cache[key] = img
    return img


def colormap_pixel(name: str, temperature: float, downfall: float) -> tuple[int, int, int]:
    """Exact ColorMapColorUtil lookup on textures/colormap/<name>.png."""
    img = load_texture(f"colormap/{name}")
    t = min(max(temperature, 0.0), 1.0)
    r = min(max(downfall, 0.0), 1.0) * t
    x = int((1.0 - t) * 255.0)
    y = int((1.0 - r) * 255.0)
    px = img[y, x]
    return int(px[0]), int(px[1]), int(px[2])


_registry = None


def registry() -> dict:
    """The raw registry dump (data/blocks_26.3.json)."""
    global _registry
    if _registry is None:
        _registry = json.loads(REGISTRY_JSON.read_text(encoding="utf-8"))
    return _registry


PHYSICS_JSON = _config.data_file("render_physics")
_physics = None


def render_physics():
    """Per-state renderer physics dumped from the game by blockwright/java/RenderPhysicsDump.java (face
    occlusion shapes, legacy isSolid, light dampening, skylight, shade brightness, emissive). None when the
    file is missing; callers then fall back to approximations from the registry dump."""
    global _physics
    if _physics is None:
        try:
            _physics = json.loads(PHYSICS_JSON.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _physics = False
    return _physics or None


TAGS_JSON = _config.data_file("tags")
_ancestors = None


def class_ancestors(cls: str) -> tuple:
    """(cls, superclass, ...) of a 26.3 block class, from data/tags_26.3.json ('class_ancestors')."""
    global _ancestors
    if _ancestors is None:
        try:
            _ancestors = json.loads(TAGS_JSON.read_text(encoding="utf-8")).get("class_ancestors", {})
        except (OSError, ValueError):
            _ancestors = {}
    return (cls,) + tuple(_ancestors.get(cls, ()))
