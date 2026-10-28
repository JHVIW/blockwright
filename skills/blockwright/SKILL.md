---
name: blockwright
description: Design and generate handcrafted-quality Minecraft Java buildings as real .litematic schematics (Litematica), in any style (medieval, fantasy, japanese, modern, rustic, cottagecore or your own), with a builder -> critic agent loop, game-accurate block states, automated QA, real-texture renders and Litematica-native validation. Use when the user asks for a Minecraft build, house, base, village, castle, shop, schematic or .litematic file, e.g. "build me a medieval blacksmith as a litematic".
argument-hint: "[what to build, style, size, palette limits]"
---

# blockwright: builder -> critic pipeline for Minecraft builds

Each building gets its own bespoke Python script that runs on the `blockwright` toolkit. The toolkit makes the
result game-accurate: stair shapes, fence and pane connections, leaves and other derived states are resolved
exactly as the game would resolve them. QA checks floating blocks, support, leaks, walkability and spawn-proof
lighting. A renderer draws the real block models and textures. A fresh critic agent judges every first version and
prototypes fixes before they are applied.

Request: $ARGUMENTS

## Where things are

| What | Where |
|---|---|
| Builder API (Build, Frame, wood(), stairs, rooms, finish) | `${CLAUDE_PLUGIN_ROOT}/docs/API.md` |
| **Universal lessons (mandatory for every agent)** | `${CLAUDE_PLUGIN_ROOT}/docs/design/LESSONS.md` |
| Style packs (palettes, motifs, anti-patterns) | `${CLAUDE_PLUGIN_ROOT}/docs/styles/<style>.md` (`README.md` explains how to write a new one) |
| Technique catalogue (roofs, walls, windows, interiors, trees, landscaping, measured colours) | `${CLAUDE_PLUGIN_ROOT}/docs/design/techniques.md` |
| QA checks, renderer, conventions | `${CLAUDE_PLUGIN_ROOT}/docs/QA.md`, `RENDER.md`, `CONVENTIONS.md` |
| Example scripts (quality references) | `${CLAUDE_PLUGIN_ROOT}/examples/builds/` |
| Example critiques (format and fixes that worked) | `${CLAUDE_PLUGIN_ROOT}/docs/examples/critiques/` |
| Agent prompt templates | [builder](templates/builder_prompt.md), [critic](templates/critic_prompt.md), [brief](templates/brief.md) |

If `${CLAUDE_PLUGIN_ROOT}` did not expand, run `python -m blockwright where` to print these folders.

## 0. Environment (once per machine)
1. Run `python -m blockwright doctor`.
   - If Python cannot import `blockwright`, install it: `python -m pip install -e "${CLAUDE_PLUGIN_ROOT}"`.
   - If the renderer shows "textures missing", run `python -m blockwright setup`. It downloads the official
     Minecraft client jar from Mojang (about 30 MB) into the user cache and extracts the textures. Tell the user
     first.
   - The validator is optional and needs a JDK 25+. If `doctor` says it is missing, carry on and say so in the final
     report. Suggest `python -m blockwright setup --java <JDK home>` if the user wants it.
2. Pick the **workspace**:
   - the folder the user names;
   - else the current directory if it already has `builds/`;
   - else create `./minecraft-builds/`.

   Run every command from inside it. The layout is `builds/<slug>.py`, `out/{schematics,previews,reports,materials}`,
   `notes/{briefs,logs,critiques}`, `notes/LESSONS.md` and `scratch/`.

## 1. Brief
Turn the request into a brief at `notes/briefs/<slug>.md` (use [templates/brief.md](templates/brief.md)):
- **Style.** Use the closest pack in `docs/styles/`. If none fits (e.g. "steampunk"), write a short pack yourself in
  `notes/styles/<style>.md` from the template in `docs/styles/README.md`, with palette, motifs and anti-patterns,
  verified block ids only.
- **Program.** The rooms and functions, and one signature exterior element. For a blacksmith that is a forge with
  a chimney, an anvil corner, a quench trough, a storefront and a stable or yard.
- **Size.** A guideline W×D and storeys. Small is 9–15, medium 15–25, large 25–40.
- **Palette constraint.** If the user says "only blocks I have" or similar, get the list (pasted text or a file).
  Write it to `notes/palette.txt`, one item per line; `*_planks` globs and `#minecraft:logs` tags are allowed. Pass
  that path as the constraint. QA then fails on any item outside it. Otherwise use `none`.
- **Mood.** One or two sentences, plus how this build differs from the others in a set (silhouette, palette).

Ask the user only when something important is truly ambiguous: the style, or a hard palette limit. Otherwise
choose sensible defaults and state them.

## 2. Builder agent
Use one background `general-purpose` agent per building. Its prompt is
[templates/builder_prompt.md](templates/builder_prompt.md) with every `{{...}}` placeholder filled in:
- `{{DOCS}}` = `${CLAUDE_PLUGIN_ROOT}/docs`;
- `{{WORKSPACE}}` = the absolute workspace path.

The builder:
1. scaffolds with `python -m blockwright new <slug> --style <style> [--palette notes/palette.txt]`;
2. plans in `notes/logs/<slug>.md`;
3. works in this order: massing → roof → materials and contrast → details, interior and landscaping;
4. runs at least 5 render–look–fix cycles with `--quick`.

It finishes when QA reports 0 errors, `validate` passes (if it is set up) and a full render exists.

## 3. Look at the sheet yourself
`Read` `out/previews/<slug>/<slug>_sheet.png` and the hero iso view. Show it to the user: give the path and a short
description. Write down what you see. The usual faults are in LESSONS §1–6, and the biggest one is value contrast
between roof and walls. Don't call a building done at the builder's self-score.

## 4. Critic agent
Always use a *fresh* agent, with [templates/critic_prompt.md](templates/critic_prompt.md). Give it:
- your read of the sheet;
- the builder's self-reported weaknesses and score;
- the round number.

The critic writes `notes/critiques/<slug>_round<k>.md`. It prototypes fixes in `scratch/critic_<slug>_r<k>/`, in
a *copy* of the script and never the original. It keeps QA at 0 errors and renders before/after `compare_*.png`.

## 5. Apply
`SendMessage` the critic's report to the **original builder agent**, which still has its context. The builder
applies the fixes, re-renders, and re-checks QA and validate. Repeat steps 3–5 until the build is at least as good
as the example references in `docs/showcase/`. Two rounds is typical; one is enough for small builds.

## 6. Learn
When a new recurring mistake or a winning recipe shows up, add it to `notes/LESSONS.md` in the workspace. Every
future builder in that workspace reads it. If the lesson is universal, suggest the user contributes it upstream.

## 7. Ship
- Run `python -m blockwright validate out/schematics/<slug>.litematic` (skip it if the validator isn't set up).
- For a set, run `python -m blockwright package [slugs...] --name <collection>`. It writes `dist/<collection>.zip`
  with schematics, previews and material lists.
- To install, run `python -m blockwright install-to "<minecraft or instance folder>" --folder <collection>` **only
  with a folder the user gave you**. Never guess or search for a game install.
- Tell the user:
  - the ground layer (it is in the schematic description);
  - to paste with Litematica's Replace = "With non-air";
  - where the material list is.

Only ship finished buildings.

## Rules that matter
- **Concurrency.** Run at most 3 agents at once (builders plus critics). Builders iterate with `--quick` renders.
  If a rate or usage limit stops agents, resume them later with `SendMessage` to their agent id rather than
  restarting them. Their script and log are on disk.
- **Agent scope.** Agents edit only their own script, log, notes and outputs, never the Minecraft installation or
  another build's files. Scratch files get a slug prefix (e.g. `scratch/blacksmith_probe.py`), because the
  scratchpad is shared.
- **Shell.** If a shell heredoc breaks on quotes, write patch code to a file and run that instead.
- **The user's game.** It may be running. Copying schematics into a folder the user named is safe. Never touch mods,
  configs or saves.
- **Quality bar.** Handcrafted quality, never "AI boxes". Visual quality comes before speed.

## Quick mode
If the user wants something fast ("just a quick hut"), skip the critic. Build it yourself in one script, still with
at least 3 render–look–fix cycles and QA at 0 errors, and say that the full loop would raise the quality.
