# Contributing to blockwright

Thanks for helping. The most valuable contributions are, in rough order:

1. **Style packs** (`docs/styles/<style>.md`). Follow the template in `docs/styles/README.md`. Use real 26.3 block
   ids only, and include at least one build (script + renders) that shows the pack works.
2. **Lessons** (`docs/design/LESSONS.md`). A lesson is a recurring mistake or a recipe that won, phrased so it
   applies to any style. Before/after renders make the case.
3. **QA rules, resolver rules, renderer fixes.** Every game rule must cite the game class or method it ports, and
   should come with a test. If you can, cross-check it against the real game (see `tests/test_core_gamecheck.py`).
4. **New Minecraft versions.** Run `python -m blockwright setup --mc-version <v> --java <JDK>`, then
   `python -m blockwright dump-registry --out blockwright/data`. Run the full test suite including the JDK
   cross-checks, and describe what changed.

## Development

```bash
git clone https://github.com/JHVIW/blockwright && cd blockwright
python -m pip install -e ".[dev]"
python -m pytest                      # runs without any Minecraft files
python -m blockwright setup           # textures -> renderer tests run too
python -m blockwright setup --java /path/to/jdk-25   # validator + game cross-checks run too
```

Run the examples: `python -m blockwright build examples/builds/b00_demo.py --quick` (outputs go to
`examples/out/`, which git ignores).

Test locally as a Claude Code plugin: `claude --plugin-dir .`, then `claude plugin validate .`.

## Rules

- **No Mojang assets or game code in the repo.** Never commit textures, models or jars. Committing factual data
  dumped from the registry (ids, properties, shapes, tags) is fine.
- **No machine-specific paths.** Everything goes through `blockwright/config.py`.
- Keep the code plain and deterministic: no unseeded randomness (use `blockwright.noise`), and docstrings on the
  public API.
- Build scripts are bespoke. Shared helpers are *techniques* (a stair, a door, a Frame), never
  `make_house(w, d, material)`.

## Pull requests

- Keep PRs focused, with a test for every behaviour change.
- `pytest` must pass. CI runs it on Linux, macOS and Windows.
- For design changes, attach renders.
