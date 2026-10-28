# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [SemVer](https://semver.org/).

## [0.1.0] - 2026-10-28

First public release.

### Added
- `blockwright` Python toolkit:
  - `Build` / `Frame` API, with game-accurate state resolution (stairs, fences, walls, panes, leaves, vines,
    chests, ...) and rotate/mirror that matches the game;
  - Litematica 0.29.1 writer/reader and a vanilla structure `.nbt` writer;
  - survival material lists and an allowed-blocks palette constraint;
  - QA: floating, support, enclosure, walkability, spawn-proof lighting, palette, design metrics;
  - a numpy software renderer using the real block models and textures: iso, elevations, top, cutaways, eye level,
    close-ups and contact sheets.
- Cross-platform `setup`. It downloads the vanilla client jar from Mojang for the textures. Optionally it also
  downloads the game libraries, Litematica, MaLiLib and fabric-loader for the Litematica-native validator.
- CLI: `setup`, `doctor`, `where`, `new`, `build`, `qa`, `render`, `validate`, `materials`, `package`,
  `install-to`, `dump-registry`.
- Claude Code plugin with the `blockwright` skill: brief → builder agent → orchestrator's look → fresh critic
  agent → apply → lessons → ship. Ships builder, critic and brief templates.
- Design knowledge:
  - universal lessons and a technique catalogue;
  - style packs: cottagecore, medieval, fantasy, japanese, modern, rustic.
- Examples: the demo scene and three cottagecore showcase builds, plus example critiques and build logs.
- Tested on Minecraft Java 26.3 (data version 5023) and Litematica 0.29.1.
