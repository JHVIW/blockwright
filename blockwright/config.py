"""Configuration and well-known paths.

Nothing in blockwright hard-codes a machine-specific path.  Every location comes from, in order of precedence:

1. environment variables (``BLOCKWRIGHT_CACHE``, ``BLOCKWRIGHT_JAVA_HOME``, ``BLOCKWRIGHT_MC_VERSION``,
   ``BLOCKWRIGHT_WORKSPACE``, ``BLOCKWRIGHT_AUTHOR``; ``BLOCKWRIGHT_CONFIG`` points at an alternative config file),
2. a ``blockwright.json`` in the current directory (per-workspace overrides),
3. the user config file written by ``python -m blockwright setup``
   (Windows ``%APPDATA%/blockwright/config.json``, macOS ``~/Library/Application Support/blockwright/config.json``,
   Linux ``$XDG_CONFIG_HOME/blockwright/config.json``),
4. the defaults below.

The cache (vanilla client jar, extracted textures, validator jars) lives outside the repository and is never
committed: Mojang's assets are downloaded from Mojang's own servers onto the user's machine by ``setup``.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

#: Project name.  Used for the CLI name, config/cache folder names and the default schematic author.
#: (Renaming the project = change this, the package folder and pyproject.toml.)
NAME = "blockwright"

PKG_DIR = Path(__file__).resolve().parent
PKG_DATA = PKG_DIR / "data"
JAVA_SRC = PKG_DIR / "java"
REPO_ROOT = PKG_DIR.parent          # only meaningful for a source checkout / plugin install
DOCS_DIR = REPO_ROOT / "docs"

TESTED = {"mc_version": "26.3", "litematica_version": "0.29.1", "malilib_version": "0.30.2"}

DEFAULTS = {
    "mc_version": TESTED["mc_version"],
    "litematica_version": TESTED["litematica_version"],
    "malilib_version": TESTED["malilib_version"],
    "fabric_loader_version": None,     # None = latest stable from meta.fabricmc.net at setup time
    "cache_dir": None,                 # None = platform cache dir (see default_cache_dir)
    "java_home": None,                 # JDK used by the optional validator; None = autodetect
    "author": NAME,
}

_ENV = {
    "mc_version": "BLOCKWRIGHT_MC_VERSION",
    "cache_dir": "BLOCKWRIGHT_CACHE",
    "java_home": "BLOCKWRIGHT_JAVA_HOME",
    "author": "BLOCKWRIGHT_AUTHOR",
    "workspace": "BLOCKWRIGHT_WORKSPACE",
}


def _home() -> Path:
    return Path(os.path.expanduser("~"))


def user_config_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or _home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = _home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or _home() / ".config")
    return base / NAME


def default_cache_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or _home() / "AppData" / "Local")
        return base / NAME / "cache"
    if sys.platform == "darwin":
        return _home() / "Library" / "Caches" / NAME
    return Path(os.environ.get("XDG_CACHE_HOME") or _home() / ".cache") / NAME


def config_file() -> Path:
    env = os.environ.get("BLOCKWRIGHT_CONFIG")
    return Path(env) if env else user_config_dir() / "config.json"


def _read_json(p: Path) -> dict:
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def load() -> dict:
    """The effective configuration (defaults < user config < ./blockwright.json < environment)."""
    cfg = dict(DEFAULTS)
    cfg.update({k: v for k, v in _read_json(config_file()).items() if v is not None})
    cfg.update({k: v for k, v in _read_json(Path.cwd() / "blockwright.json").items() if v is not None})
    for key, env in _ENV.items():
        if os.environ.get(env):
            cfg[key] = os.environ[env]
    return cfg


def save(updates: dict) -> Path:
    """Merge ``updates`` into the user config file and return its path."""
    p = config_file()
    cur = _read_json(p)
    cur.update(updates)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cur, indent=2) + "\n", encoding="utf-8")
    return p


def get(key: str, default=None):
    v = load().get(key)
    return default if v is None else v


# ------------------------------------------------------------------------------------------- derived paths
def mc_version() -> str:
    return str(get("mc_version"))


def cache_dir() -> Path:
    v = get("cache_dir")
    return Path(os.path.expanduser(str(v))) if v else default_cache_dir()


def version_dir(version: str | None = None) -> Path:
    return cache_dir() / "minecraft" / (version or mc_version())


def client_jar(version: str | None = None) -> Path:
    return version_dir(version) / "client.jar"


def version_json(version: str | None = None) -> Path:
    return version_dir(version) / "version.json"


def assets_root(version: str | None = None) -> Path:
    """Folder holding ``minecraft/{blockstates,models,textures}`` extracted from the client jar."""
    return version_dir(version) / "assets"


def libraries_dir() -> Path:
    return cache_dir() / "libraries"


def validator_dir(version: str | None = None) -> Path:
    return version_dir(version) / "validator"


def data_file(kind: str, version: str | None = None) -> Path:
    """Factual game data dumped from the registry: kind = blocks | tags | render_physics.

    Shipped data in the package wins; data generated by ``python -m blockwright dump-registry`` for another
    game version lives in the cache.  Returns the shipped path when neither exists (callers report it)."""
    v = version or mc_version()
    name = f"{kind}_{v}.json"
    for d in (PKG_DATA, version_dir(v) / "data"):
        if (d / name).is_file():
            return d / name
    return PKG_DATA / name


def workspace() -> Path:
    v = get("workspace")
    return Path(os.path.expanduser(str(v))).resolve() if v else Path.cwd().resolve()


def java_home() -> Path | None:
    """The configured JDK, else $JAVA_HOME, else a ``java`` on PATH.  None when nothing is found."""
    import shutil
    for cand in (get("java_home"), os.environ.get("JAVA_HOME")):
        if cand and (Path(cand) / "bin" / _exe("java")).is_file():
            return Path(cand)
    j = shutil.which("java")
    if j:
        p = Path(j).resolve()
        if (p.parent / _exe("javac")).is_file():
            return p.parent.parent
    return None


def _exe(name: str) -> str:
    return name + ".exe" if os.name == "nt" else name
