"""blockwright.render - Minecraft 26.3 voxel preview renderer (real block models + textures from the client jar).

Public API
    render_views(blocks, size, out_dir, meta=None, views="all"|"quick"|[...], terrain=True, ...) -> list[str]
    render_view(blocks, size, view, out_path, meta=None, terrain=True, ...) -> str
    read_litematic(path) -> (blocks, size, meta)        (standalone reader used by the CLI)
    ensure_assets()                                     (extract assets from the client jar once)
CLI
    python -m blockwright render <file.litematic> <out_dir> [--quick] [--views a,b] [--no-terrain] [--size WxH]
See docs/RENDER.md.
"""
from .assets import ensure_assets
from .litematic_io import read_litematic
from .views import VIEW_PRESETS, contact_sheet, detect_storeys, render_view, render_views

__all__ = ["render_views", "render_view", "read_litematic", "ensure_assets", "detect_storeys", "contact_sheet",
           "VIEW_PRESETS"]
