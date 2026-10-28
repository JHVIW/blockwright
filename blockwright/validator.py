"""Litematica-native validation: load a .litematic through Litematica's own reader, headless.

``python -m blockwright validate file.litematic...`` runs ``java/LitematicValidate.java`` (compiled by ``setup``)
on the vanilla client jar + game libraries + Litematica + MaLiLib + fabric-loader.  It checks every tag with
Minecraft's NbtIo, parses every palette entry strictly against the live game registry, then loads the file with
``LitematicaSchematic.createFromFile`` (what the in-game "Load Schematic" button calls) and compares it cell by cell
with an independent decode.  Exit code 0 = all valid, 1 = errors, 2 = not set up / usage problem.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from . import config

LOG4J = """<?xml version="1.0" encoding="UTF-8"?>
<Configuration status="WARN">
  <Appenders>
    <Console name="Err" target="SYSTEM_ERR"><PatternLayout pattern="  [log %level %logger{1}] %msg%n"/></Console>
  </Appenders>
  <Loggers>
    <Logger name="malilib" level="error"/>
    <Root level="warn"><AppenderRef ref="Err"/></Root>
  </Loggers>
</Configuration>
"""


def status() -> tuple:
    """(ready, message, classpath info dict or None)."""
    cpf = config.validator_dir() / "classpath.json"
    if not cpf.is_file():
        return False, (f"validator not set up (needs a JDK). Run `python -m {config.NAME} setup --java <JDK home>`; "
                       "everything else works without it."), None
    info = json.loads(cpf.read_text(encoding="utf-8"))
    missing = [p for p in _cp(info) if not Path(p).is_file()]
    if missing:
        return False, f"validator files missing ({missing[0]}); re-run `python -m {config.NAME} setup`", None
    return True, "ready", info


def _cp(info: dict) -> list:
    return info["libraries"] + [info["client"], info["litematica"], info["malilib"]] + info["fabric"]


def _java_home(info: dict) -> Path | None:
    jh = config.get("java_home") or info.get("java_home")
    if jh and (Path(jh) / "bin" / config._exe("java")).is_file():
        return Path(jh)
    return config.java_home()


def run(args: list) -> int:
    ok, msg, info = status()
    if not ok:
        print(f"validate: {msg}", file=sys.stderr)
        return 2
    jh = _java_home(info)
    if jh is None:
        print("validate: no JDK found (set java_home via setup --java)", file=sys.stderr)
        return 2
    vdir = config.validator_dir()
    classes = vdir / "classes"
    src = config.JAVA_SRC / "LitematicValidate.java"
    if not (classes / "LitematicValidate.class").is_file() or src.stat().st_mtime > (classes / "LitematicValidate.class").stat().st_mtime:
        from .setup_env import compile_java
        compile_java(jh, [src], _cp(info), classes)
    log4j = vdir / "log4j2-validate.xml"
    if not log4j.is_file() or log4j.read_text(encoding="utf-8") != LOG4J:
        log4j.write_text(LOG4J, encoding="utf-8")
    gamedir = vdir / "gamedir"
    gamedir.mkdir(parents=True, exist_ok=True)
    argv = []
    it = iter(args)
    for a in it:
        if a == "--json":
            argv += [a, str(Path(next(it)).resolve())]
        elif a.startswith("-"):
            argv.append(a)
        else:
            argv.append(str(Path(a).resolve()))
    extra = os.environ.get("BLOCKWRIGHT_JAVA_OPTS", "").split()
    cmd = ([str(jh / "bin" / config._exe("java"))] + extra +
           ["-Xss4m", "--enable-native-access=ALL-UNNAMED", "--sun-misc-unsafe-memory-access=allow",
            f"-Dlog4j2.configurationFile={log4j}", f"-Dlitvalidate.gamedir={gamedir}",
            "-cp", os.pathsep.join([str(classes)] + _cp(info)), "LitematicValidate"] + argv)
    return subprocess.run(cmd, cwd=str(gamedir)).returncode
