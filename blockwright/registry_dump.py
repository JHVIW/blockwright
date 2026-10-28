"""``python -m blockwright dump-registry``: regenerate the factual game data from the game itself.

blockwright ships ``data/blocks_26.3.json``, ``tags_26.3.json`` and ``render_physics_26.3.json``.  They are facts
about the game (block ids, properties, legal values, defaults, collision shapes, sturdy faces, light, tag
membership), produced by running small Java programs against the vanilla client jar headless:

* ``java/RegistryDump.java``      -> ``blocks_<version>.json``
* ``java/RenderPhysicsDump.java`` -> ``render_physics_<version>.json``
* ``java/ClassAncestorsDump.java`` + the jar's ``data/minecraft/tags`` -> ``tags_<version>.json``

Needs ``setup`` with a JDK first (the game libraries come from the validator setup).  Output goes to the cache
(``<cache>/minecraft/<version>/data``), where blockwright finds it for that version; pass ``--out`` to write
elsewhere (e.g. ``blockwright/data`` when contributing a new version).
"""
from __future__ import annotations

import json
import os
import subprocess
import zipfile
from pathlib import Path

from . import config


def _resolve_tags(raw: dict) -> dict:
    resolved: dict = {}

    def res(tag, stack=()):
        if tag in resolved:
            return resolved[tag]
        if tag in stack:
            raise RuntimeError(f"cyclic tag {tag}")
        out = set()
        for e in raw.get(tag, []):
            ref = e["id"] if isinstance(e, dict) else e
            if ref.startswith("#"):
                r = ref[1:] if ":" in ref else "minecraft:" + ref[1:]
                out |= res(r, stack + (tag,))
            else:
                out.add(ref if ":" in ref else "minecraft:" + ref)
        resolved[tag] = out
        return out

    for t in raw:
        res(t)
    return {t: sorted(v) for t, v in sorted(resolved.items())}


def read_tags(jar: Path, kind: str) -> dict:
    raw = {}
    prefix = f"data/minecraft/tags/{kind}/"
    with zipfile.ZipFile(jar) as z:
        for n in z.namelist():
            if n.startswith(prefix) and n.endswith(".json"):
                raw["minecraft:" + n[len(prefix):-5]] = json.loads(z.read(n).decode("utf-8")).get("values", [])
    return _resolve_tags(raw)


def run(a) -> int:
    from . import validator
    from .setup_env import compile_java
    ok, msg, info = validator.status()
    if not ok:
        print(f"dump-registry needs the game libraries and a JDK: {msg}")
        return 2
    jh = validator._java_home(info)
    version = config.mc_version()
    out = Path(a.out) if a.out else config.version_dir(version) / "data"
    out.mkdir(parents=True, exist_ok=True)
    cp = info["libraries"] + [info["client"]]
    classes = config.version_dir(version) / "dump-classes"
    srcs = [config.JAVA_SRC / n for n in ("RegistryDump.java", "RenderPhysicsDump.java", "ClassAncestorsDump.java")]
    compile_java(jh, srcs, cp, classes)
    java = str(jh / "bin" / config._exe("java"))
    full_cp = os.pathsep.join([str(classes)] + cp)
    work = config.version_dir(version) / "dump-work"
    work.mkdir(parents=True, exist_ok=True)
    anc = work / "class_ancestors.json"
    for main, dest in (("RegistryDump", out / f"blocks_{version}.json"),
                       ("RenderPhysicsDump", out / f"render_physics_{version}.json"),
                       ("ClassAncestorsDump", anc)):
        print(f"  {main} -> {dest}")
        r = subprocess.run([java, "--enable-native-access=ALL-UNNAMED", "-cp", full_cp, main, str(dest)], cwd=str(work))
        if r.returncode != 0:
            print(f"{main} failed (exit {r.returncode})")
            return 1
    jar = Path(info["client"])
    tags = {"version": version, "source": f"minecraft {version} client jar (data/minecraft/tags)",
            "tags": read_tags(jar, "block"), "fluid_tags": read_tags(jar, "fluid"),
            "class_ancestors": json.loads(anc.read_text(encoding="utf-8"))}
    (out / f"tags_{version}.json").write_text(json.dumps(tags, indent=0, sort_keys=True), encoding="utf-8")
    print(f"  tags -> {out / f'tags_{version}.json'}\ndone.")
    return 0
