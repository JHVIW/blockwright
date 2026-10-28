"""Command line: ``python -m blockwright <command> ...`` (also installed as the ``blockwright`` command).

    setup                         download the Minecraft client jar (+ optional validator deps) into the cache
    doctor                        show configuration and what is ready
    where                         print the docs / examples / skill folders (for agents)
    new <slug>                    scaffold builds/<slug>.py in the workspace
    build <slug|script> [flags]   run a build script (flags: --quick --no-render --no-qa --views=a,b --palette=F)
    qa <file.litematic>           QA checks -> out/reports
    render <file.litematic> [dir] previews (iso, elevations, cutaways, eye level, close-ups, contact sheet)
    validate <file.litematic>...  load through Litematica's own reader (optional, needs a JDK)
    materials <file.litematic>    material list (+ --allowed my_blocks.txt palette check)
    package [slug...]             zip schematics + previews + materials into dist/
    install-to <minecraft dir>    copy schematics into an instance's schematics/ folder
    dump-registry                 regenerate the block registry data from the game (needs a JDK)

The workspace is the current folder (or ``--workspace`` / ``$BLOCKWRIGHT_WORKSPACE``): ``builds/`` holds one script
per build, ``out/`` the results, ``notes/`` briefs, logs, critiques and lessons, ``scratch/`` critic prototypes.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from . import config

NAME = config.NAME
SUBDIRS = ("builds", "out/schematics", "out/previews", "out/reports", "out/materials", "notes/briefs", "notes/logs",
           "notes/critiques", "scratch")


def _ws() -> Path:
    return config.workspace()


def _env_with_pkg() -> dict:
    env = dict(os.environ)
    root = str(config.PKG_DIR.parent)
    env["PYTHONPATH"] = root + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return env


# ------------------------------------------------------------------------------------------------ commands
def cmd_doctor(_args) -> int:
    cfg = config.load()
    print(f"{NAME} {__import__('blockwright').__version__}  (Python {sys.version.split()[0]})")
    print(f"  config file   : {config.config_file()}{'' if config.config_file().is_file() else ' (not created yet)'}")
    print(f"  workspace     : {_ws()}")
    print(f"  mc version    : {config.mc_version()} (tested: {config.TESTED['mc_version']}, "
          f"Litematica {config.TESTED['litematica_version']})")
    print(f"  cache         : {config.cache_dir()}")
    reg = config.data_file("blocks")
    print(f"  registry data : {'ok' if reg.is_file() else 'MISSING (run dump-registry)'} {reg.name}")
    marker = config.assets_root() / ".extracted.json"
    print(f"  renderer      : {'ready' if marker.is_file() else 'textures missing -> run `python -m blockwright setup`'}")
    from . import validator
    ok, msg, info = validator.status()
    print(f"  validator     : {msg}" + (f" (Litematica {info.get('litematica_version')})" if ok else ""))
    jh = config.java_home() or cfg.get("java_home")
    print(f"  JDK           : {jh or 'not found (only needed for validate / dump-registry)'}")
    return 0


def cmd_where(_args) -> int:
    root = config.PKG_DIR.parent

    def p(path):
        return str(path) if path.exists() else f"(not in this install: {path.name} ships with the git checkout / plugin)"

    print(json.dumps({"package": str(config.PKG_DIR), "docs": p(config.DOCS_DIR),
                      "examples": p(root / "examples" / "builds"), "skill": p(root / "skills" / NAME),
                      "workspace": str(_ws())}, indent=1))
    return 0


def cmd_new(a) -> int:
    ws = _ws()
    slug = a.slug
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", slug):
        print("slug must be lowercase letters, digits, _ or - (e.g. medieval_blacksmith)", file=sys.stderr)
        return 2
    for d in SUBDIRS:
        (ws / d).mkdir(parents=True, exist_ok=True)
    script = ws / "builds" / f"{slug}.py"
    if script.exists() and not a.force:
        print(f"{script} already exists (use --force to overwrite)", file=sys.stderr)
        return 1
    title = a.title or " ".join(w.capitalize() for w in re.split(r"[_-]+", slug) if not w.isdigit())
    palette_line = ""
    if a.palette:
        pal = Path(a.palette).resolve()
        if not pal.is_file():
            print(f"palette file not found: {pal}", file=sys.stderr)
            return 2
        rel = os.path.relpath(pal, ws).replace("\\", "/")
        palette_line = (f'b.set_allowed_blocks(__import__("pathlib").Path(__file__).resolve().parents[1] / "{rel}")'
                        "   # QA errors on any item outside it")
    tmpl = (config.PKG_DIR / "templates" / "build_script.py.tmpl").read_text(encoding="utf-8")
    script.write_text(tmpl.format(slug=slug, title=title.replace('"', "'"), style=a.style, palette_line=palette_line),
                      encoding="utf-8")
    log = ws / "notes" / "logs" / f"{slug}.md"
    if not log.exists():
        log.write_text(f"# {title} -- build log\n\nStyle: {a.style}\nPalette constraint: {a.palette or 'none'}\n\n"
                       "## Plan\n\n## Iterations\n", encoding="utf-8")
    print(f"created {script}\n        {log}\nnext: python builds/{slug}.py --quick")
    return 0


def _find_script(target: str) -> Path | None:
    p = Path(target)
    if p.suffix == ".py" and p.is_file():
        return p.resolve()
    ws = _ws()
    for cand in (ws / "builds" / f"{target}.py", ws / "builds" / f"b{target}.py"):
        if cand.is_file():
            return cand
    hits = sorted((ws / "builds").glob(f"*{target}*.py")) if (ws / "builds").is_dir() else []
    return hits[0] if len(hits) == 1 else None


def cmd_build(a, rest) -> int:
    script = _find_script(a.target)
    if script is None:
        print(f"no build script for {a.target!r} in {_ws() / 'builds'}", file=sys.stderr)
        return 2
    return subprocess.run([sys.executable, str(script)] + rest, env=_env_with_pkg()).returncode


def cmd_qa(rest) -> int:
    from . import qa
    return qa.main(rest)


def cmd_render(rest) -> int:
    from .render.__main__ import main
    if rest and not rest[0].startswith("-") and (len(rest) == 1 or rest[1].startswith("-")):
        stem = Path(rest[0]).stem
        rest = [rest[0], str(_ws() / "out" / "previews" / stem)] + rest[1:]
    main(rest)
    return 0


def cmd_validate(rest) -> int:
    from . import validator
    if not [r for r in rest if not r.startswith("-")]:
        print("usage: python -m blockwright validate [--lenient] [-v] [--json out.json] file.litematic...",
              file=sys.stderr)
        return 2
    return validator.run(rest)


def cmd_materials(a) -> int:
    from . import materials
    from .litematic import read_litematic
    blocks, _size, md = read_litematic(a.file)
    slug = Path(a.file).stem
    rep = materials.material_list(blocks)
    out = _ws() / "out" / "materials"
    title = (md or {}).get("name") if isinstance(md, dict) else None
    materials.write_materials(rep, out / f"{slug}.md", out / f"{slug}.json", title=title or slug)
    print(materials.to_markdown(rep, title=title or slug))
    if a.allowed:
        from .palette import check_blocks, load_palette
        bad = check_blocks(blocks, load_palette(a.allowed))
        if bad:
            print(f"\n{len(bad)} item kind(s) are NOT in {a.allowed}:")
            for it, n, pos in bad:
                print(f"  - {it} x{n}" + (f"  (e.g. at {tuple(pos)})" if pos is not None else ""))
            return 1
        print(f"\nall {len(rep['items'])} item kinds are in {a.allowed}")
    return 0


def _finished(slugs) -> list:
    sch = _ws() / "out" / "schematics"
    found = sorted(sch.glob("*.litematic")) if sch.is_dir() else []
    if slugs:
        found = [p for p in found if p.stem in slugs]
    return found


def cmd_package(a) -> int:
    from .materials import GROUPS, group_of, stacks
    found = _finished(a.slugs)
    if not found:
        print("no schematics in out/schematics", file=sys.stderr)
        return 1
    if a.validate:
        from . import validator
        ok, msg, _ = validator.status()
        if ok:
            rc = validator.run([str(p) for p in found])
            if rc != 0:
                print("validation failed -- not packaging", file=sys.stderr)
                return rc
        else:
            print(f"(skipping Litematica validation: {msg})")
    ws = _ws()
    name = a.name or ws.name
    dist = ws / "dist" / name
    if dist.exists():
        shutil.rmtree(dist)
    for sub in ("schematics", "previews", "materials"):
        (dist / sub).mkdir(parents=True)
    total = {}
    rows = []
    for lit in found:
        slug = lit.stem
        shutil.copy2(lit, dist / "schematics" / lit.name)
        for view in ("sheet", "iso_se", "iso_sw", "iso_nw", "eye"):
            src = ws / "out" / "previews" / slug / f"{slug}_{view}.png"
            if src.exists():
                shutil.copy2(src, dist / "previews" / src.name)
        mj = ws / "out" / "materials" / f"{slug}.json"
        if mj.exists():
            items = json.loads(mj.read_text(encoding="utf-8"))["items"]
            for it, n in items.items():
                total[it] = total.get(it, 0) + n
            rows.append((slug, sum(items.values())))
            md = mj.with_suffix(".md")
            if md.exists():
                shutil.copy2(md, dist / "materials" / md.name)
    lines = [f"# Master material list -- {name}", "", "| build | items |", "|---|---:|"]
    lines += [f"| {s} | {n} |" for s, n in rows]
    for group in GROUPS:
        g = sorted(((i, n) for i, n in total.items() if group_of(i) == group), key=lambda r: -r[1])
        if g:
            lines += ["", f"## {group}", "", "| item | count | stacks |", "|---|---:|---|"]
            lines += [f"| {i.split(':', 1)[1]} | {n} | {stacks(n, i)} |" for i, n in g]
    (dist / "materials" / "MASTER_MATERIALS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (dist / "README.md").write_text(
        f"# {name}\n\nLitematica schematics made with {NAME} for Minecraft {config.mc_version()}.\n\n"
        "Copy `schematics/*.litematic` into your instance's `schematics/` folder, open Litematica (M) -> Load "
        "Schematics. Each schematic's description names its ground layer; paste with Replace = \"With non-air\".\n",
        encoding="utf-8")
    zpath = ws / "dist" / f"{name}.zip"
    if zpath.exists():
        zpath.unlink()
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(dist.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(dist.parent))
    print(f"packaged {len(found)} build(s) -> {zpath} ({zpath.stat().st_size // 1024} KB)")
    return 0


def cmd_install_to(a) -> int:
    target = Path(os.path.expanduser(a.minecraft_dir)).resolve()
    if not target.is_dir():
        print(f"not a folder: {target}", file=sys.stderr)
        return 2
    sch = target if target.name == "schematics" else target / "schematics"
    if target.name != "schematics" and not any((target / d).exists() for d in ("schematics", "mods", "saves", "options.txt")):
        print(f"{target} does not look like a Minecraft game folder (no schematics/, mods/ or saves/). Pass the "
              "instance folder or its schematics folder.", file=sys.stderr)
        return 2
    dest = sch / a.folder if a.folder else sch
    found = _finished(a.slugs)
    if not found:
        print("no schematics in out/schematics", file=sys.stderr)
        return 1
    dest.mkdir(parents=True, exist_ok=True)
    for p in found:
        shutil.copy2(p, dest / p.name)
    print(f"copied {len(found)} schematic(s) -> {dest}")
    return 0


def cmd_dump_registry(a) -> int:
    from . import registry_dump
    return registry_dump.run(a)


# ------------------------------------------------------------------------------------------------ main
def main(argv=None) -> int:
    import argparse
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--workspace"] and len(argv) > 1:
        os.environ["BLOCKWRIGHT_WORKSPACE"] = argv[1]
        argv = argv[2:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if argv[0] in ("-V", "--version"):
        print(__import__("blockwright").__version__)
        return 0
    cmd, rest = argv[0], argv[1:]
    passthrough = {"qa": cmd_qa, "render": cmd_render, "validate": cmd_validate}
    if cmd in passthrough:
        return passthrough[cmd](rest) or 0
    if cmd == "setup":
        from . import setup_env
        return setup_env.run(rest)
    ap = argparse.ArgumentParser(prog=f"python -m {NAME} {cmd}")
    if cmd == "doctor":
        return cmd_doctor(ap.parse_args(rest))
    if cmd == "where":
        return cmd_where(ap.parse_args(rest))
    if cmd == "new":
        ap.add_argument("slug")
        ap.add_argument("--title", default=None)
        ap.add_argument("--style", default="cottagecore", help="style pack name (docs/styles/<style>.md)")
        ap.add_argument("--palette", default=None, help="allowed-blocks file to enforce")
        ap.add_argument("--force", action="store_true")
        return cmd_new(ap.parse_args(rest))
    if cmd == "build":
        if not rest or rest[0].startswith("-"):
            print(f"usage: python -m {NAME} build <slug|path/to/script.py> [--quick] [--no-render] ...", file=sys.stderr)
            return 2
        return cmd_build(argparse.Namespace(target=rest[0]), rest[1:])
    if cmd == "materials":
        ap.add_argument("file")
        ap.add_argument("--allowed", default=None, help="allowed-blocks file; exit 1 if anything is outside it")
        return cmd_materials(ap.parse_args(rest))
    if cmd == "package":
        ap.add_argument("slugs", nargs="*")
        ap.add_argument("--name", default=None, help="collection name (default: workspace folder name)")
        ap.add_argument("--no-validate", dest="validate", action="store_false")
        return cmd_package(ap.parse_args(rest))
    if cmd == "install-to":
        ap.add_argument("minecraft_dir", help="the game/instance folder (or its schematics folder)")
        ap.add_argument("slugs", nargs="*")
        ap.add_argument("--folder", default=None, help="sub-folder inside schematics/ (e.g. my_village)")
        return cmd_install_to(ap.parse_args(rest))
    if cmd == "dump-registry":
        ap.add_argument("--out", default=None, help="output folder (default: the cache's data folder)")
        return cmd_dump_registry(ap.parse_args(rest))
    print(f"unknown command {cmd!r}\n{__doc__}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
