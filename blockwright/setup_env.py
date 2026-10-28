"""``python -m blockwright setup``: download everything blockwright needs onto this machine.

1. The vanilla client jar for the target version, from Mojang's official launcher manifest
   (piston-meta.mojang.com), SHA-1 verified, into the user cache.  The renderer's textures, block models and
   blockstates are extracted from it locally.  Nothing from the jar is ever part of the repository.
2. Optional, for the Litematica-native validator only: the game's Java libraries (Mojang's library server),
   Litematica + MaLiLib (Modrinth API) and fabric-loader + ASM (Fabric's maven), then the validator is compiled with
   a local JDK.  Skipped with a clear message when no JDK is found.

Everything is cross-platform Python (stdlib only, plus numpy/pillow for the renderer itself).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from . import __version__, config

MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
MODRINTH = "https://api.modrinth.com/v2"
FABRIC_META = "https://meta.fabricmc.net/v2"
FABRIC_MAVEN = "https://maven.fabricmc.net"
MAVEN_CENTRAL = "https://repo1.maven.org/maven2"
UA = f"{config.NAME}/{__version__} (+https://github.com/JHVIW/blockwright)"
ASM_FALLBACK = "9.8"


def log(msg=""):
    print(msg, flush=True)


# ------------------------------------------------------------------------------------------------ download
def _get(url: str, timeout=60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def get_json(url: str):
    return json.loads(_get(url).decode("utf-8"))


def _sha1(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path, sha1: str | None = None, label: str | None = None) -> Path:
    """Download ``url`` to ``dest`` unless an intact copy is already there (SHA-1 verified when given)."""
    if dest.is_file() and (sha1 is None or _sha1(dest) == sha1):
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    log(f"  downloading {label or dest.name} ...")
    tmp = dest.with_name(dest.name + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as out:
        shutil.copyfileobj(r, out, 1 << 20)
    if sha1 and _sha1(tmp) != sha1:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"checksum mismatch for {url}")
    os.replace(tmp, dest)
    return dest


# ------------------------------------------------------------------------------------------------ minecraft
def fetch_version_json(version: str) -> dict:
    vj = config.version_json(version)
    manifest = get_json(MANIFEST)
    entry = next((v for v in manifest["versions"] if v["id"] == version), None)
    if entry is None:
        if vj.is_file():
            return json.loads(vj.read_text(encoding="utf-8"))
        raise SystemExit(f"Minecraft version {version!r} is not in Mojang's version manifest")
    download(entry["url"], vj, entry.get("sha1"), label=f"version manifest {version}")
    return json.loads(vj.read_text(encoding="utf-8"))


def fetch_client(version: str, vjson: dict) -> Path:
    c = vjson["downloads"]["client"]
    return download(c["url"], config.client_jar(version), c.get("sha1"), label=f"Minecraft {version} client jar "
                    f"({c.get('size', 0) // (1 << 20)} MB, from Mojang)")


def extract_assets(version: str, jar: Path, force=False) -> Path:
    from .render import assets
    root = assets.ensure_assets(jar, force=force)
    marker = json.loads((root / ".extracted.json").read_text(encoding="utf-8"))
    log(f"  textures/models/blockstates: {marker['files']} files in {root}")
    return root


def library_jars(vjson: dict) -> list:
    """Download the game's (platform-independent) Java libraries; returns their paths."""
    out = []
    for lib in vjson.get("libraries", []):
        if lib.get("rules"):                       # OS-specific natives etc.: not needed headless
            continue
        art = (lib.get("downloads") or {}).get("artifact")
        if not art:
            continue
        dest = config.libraries_dir() / art["path"]
        download(art["url"], dest, art.get("sha1"), label=lib["name"])
        out.append(dest)
    return out


# ------------------------------------------------------------------------------------------------ mods
def modrinth_file(project: str, game_version: str, want: str | None) -> tuple:
    q = urllib.parse.urlencode({"game_versions": json.dumps([game_version]), "loaders": json.dumps(["fabric"])})
    versions = get_json(f"{MODRINTH}/project/{project}/version?{q}")
    if not versions:
        raise RuntimeError(f"Modrinth has no {project} build for Minecraft {game_version}")
    v = next((v for v in versions if v["version_number"] == want), None) if want else versions[0]
    if v is None:
        have = ", ".join(x["version_number"] for x in versions[:8])
        raise RuntimeError(f"{project} {want} not found for {game_version} on Modrinth (available: {have})")
    f = next((f for f in v["files"] if f.get("primary")), v["files"][0])
    return v["version_number"], f["url"], f["filename"], f["hashes"].get("sha1")


def fabric_jars(game_version: str, loader: str | None) -> tuple:
    """fabric-loader + ASM jars (malilib's static init asks FabricLoader for the mod list)."""
    if not loader:
        loaders = get_json(f"{FABRIC_META}/versions/loader")
        loader = next(l["version"] for l in loaders if l.get("stable", True))
    libs = []
    try:
        prof = get_json(f"{FABRIC_META}/versions/loader/{game_version}/{loader}/profile/json")
        libs = [(l["name"], l.get("url") or FABRIC_MAVEN + "/", l.get("sha1")) for l in prof.get("libraries", [])]
    except Exception:
        pass
    wanted = [l for l in libs if l[0].startswith(("net.fabricmc:fabric-loader:", "org.ow2.asm:"))]
    if not any(n.startswith("net.fabricmc:fabric-loader:") for n, _, _ in wanted):
        wanted.append((f"net.fabricmc:fabric-loader:{loader}", FABRIC_MAVEN + "/", None))
    if not any(n.startswith("org.ow2.asm:") for n, _, _ in wanted):
        wanted += [(f"org.ow2.asm:{a}:{ASM_FALLBACK}", MAVEN_CENTRAL + "/", None)
                   for a in ("asm", "asm-tree", "asm-commons", "asm-util", "asm-analysis")]
    out = []
    for name, base, sha1 in wanted:
        g, a, v = name.split(":")[:3]
        path = f"{g.replace('.', '/')}/{a}/{v}/{a}-{v}.jar"
        out.append(download(base.rstrip("/") + "/" + path, config.libraries_dir() / path, sha1, label=name))
    return loader, out


# ------------------------------------------------------------------------------------------------ java
def java_major(java_home: Path) -> int | None:
    try:
        r = subprocess.run([str(java_home / "bin" / config._exe("java")), "-version"], capture_output=True, text=True,
                           timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r'version "(\d+)(?:\.(\d+))?', r.stderr + r.stdout)
    if not m:
        return None
    major = int(m.group(1))
    return int(m.group(2)) if major == 1 and m.group(2) else major


def find_jdk(explicit: str | None, need: int) -> tuple:
    """(java_home, major, message).  java_home None when no suitable JDK (with javac) was found."""
    cands = []
    if explicit:
        cands.append(Path(os.path.expanduser(explicit)))
    auto = config.java_home()
    if auto:
        cands.append(auto)
    for jh in cands:
        if not (jh / "bin" / config._exe("javac")).is_file():
            continue
        major = java_major(jh)
        if major is not None and major >= need:
            return jh, major, f"JDK {major} at {jh}"
        if major is not None:
            return None, major, f"found JDK {major} at {jh}, but Minecraft {config.mc_version()} needs Java {need}+"
    return None, None, "no JDK (with javac) found"


def compile_java(java_home: Path, sources: list, classpath: list, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    cmd = [str(java_home / "bin" / config._exe("javac")), "-nowarn", "-encoding", "UTF-8", "-proc:none",
           "-cp", os.pathsep.join(str(p) for p in classpath), "-d", str(dest)] + [str(s) for s in sources]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        noise = re.compile(r"^(Note:|warning:|  class file for|  reason:|\d+ warnings?)")
        msg = "\n".join(l for l in r.stderr.splitlines() if not noise.match(l))
        raise RuntimeError(f"javac failed:\n{msg[-4000:]}")


def setup_validator(version: str, vjson: dict, jdk: Path, cfg: dict) -> dict:
    vdir = config.validator_dir(version)
    log("Validator dependencies (Litematica-native .litematic check):")
    libs = library_jars(vjson)
    jars = {"libraries": [str(p) for p in libs], "client": str(config.client_jar(version))}
    for project, key in (("litematica", "litematica_version"), ("malilib", "malilib_version")):
        ver, url, fname, sha1 = modrinth_file(project, version, cfg.get(key))
        jars[project] = str(download(url, vdir / "mods" / fname, sha1, label=f"{fname} (Modrinth)"))
        jars[project + "_version"] = ver
    loader, fjars = fabric_jars(version, cfg.get("fabric_loader_version"))
    jars["fabric"] = [str(p) for p in fjars]
    jars["fabric_loader_version"] = loader
    cp = classpath(jars)
    log("  compiling the validator ...")
    compile_java(jdk, [config.JAVA_SRC / "LitematicValidate.java"], cp, vdir / "classes")
    jars["java_home"] = str(jdk)
    (vdir / "classpath.json").write_text(json.dumps(jars, indent=1), encoding="utf-8")
    return jars


def classpath(jars: dict) -> list:
    return jars["libraries"] + [jars["client"], jars["litematica"], jars["malilib"]] + jars["fabric"]


# ------------------------------------------------------------------------------------------------ main
def run(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog=f"python -m {config.NAME} setup",
                                 description="Download the Minecraft client jar (textures for the renderer) and, "
                                             "optionally, the validator dependencies into the user cache.")
    ap.add_argument("--mc-version", default=None, help=f"Minecraft version (default {config.TESTED['mc_version']}, "
                                                       "the tested one)")
    ap.add_argument("--java", default=None, help="JDK home for the validator (default: config / $JAVA_HOME / PATH)")
    ap.add_argument("--cache", default=None, help=f"cache folder (default {config.default_cache_dir()})")
    ap.add_argument("--no-validator", action="store_true", help="skip the optional Litematica validator")
    ap.add_argument("--force", action="store_true", help="re-extract the assets")
    a = ap.parse_args(argv)

    updates = {}
    if a.cache:
        os.environ["BLOCKWRIGHT_CACHE"] = a.cache
        updates["cache_dir"] = str(Path(a.cache).expanduser().resolve())
    if a.mc_version:
        os.environ["BLOCKWRIGHT_MC_VERSION"] = a.mc_version
        updates["mc_version"] = a.mc_version
    cfg = config.load()
    version = config.mc_version()
    log(f"{config.NAME} setup -- Minecraft {version}, cache {config.cache_dir()}")
    if version != config.TESTED["mc_version"]:
        log(f"  note: {config.TESTED['mc_version']} is the tested version; for {version} also run "
            f"`python -m {config.NAME} dump-registry` (needs a JDK) to generate its block registry data.")

    log("Minecraft client (renderer textures):")
    vjson = fetch_version_json(version)
    jar = fetch_client(version, vjson)
    extract_assets(version, jar, force=a.force)

    need = int((vjson.get("javaVersion") or {}).get("majorVersion", 21))
    status = {"renderer": "ready", "validator": "skipped"}
    if a.no_validator:
        status["validator"] = "skipped (--no-validator)"
    else:
        jdk, major, msg = find_jdk(a.java, need)
        if jdk is None:
            status["validator"] = (f"not set up: {msg}. The validator is optional. Install a JDK {need}+ (e.g. Eclipse "
                                   f"Temurin) and re-run `python -m {config.NAME} setup --java <JDK home>`.")
        else:
            log(f"  using {msg}")
            if a.java:
                updates["java_home"] = str(jdk)
            try:
                j = setup_validator(version, vjson, jdk, cfg)
                status["validator"] = (f"ready (Litematica {j['litematica_version']}, MaLiLib {j['malilib_version']}, "
                                       f"fabric-loader {j['fabric_loader_version']}, JDK {major})")
            except Exception as e:  # never fail the whole setup on the optional part
                status["validator"] = f"FAILED: {type(e).__name__}: {e}"
    if updates:
        log(f"config saved: {config.save(updates)}")
    log("")
    for k, v in status.items():
        log(f"{k:>9}: {v}")
    log(f"\nNext: `python -m {config.NAME} new my_first_build` in an empty workspace folder.")
    return 0 if not status["validator"].startswith("FAILED") else 1
