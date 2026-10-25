# mbselite

Lightweight model-based specs. Write a specification in Markdown with typed
blocks. The build turns those blocks into clickable diagrams, tables and a
JSON export, and every box links back to the block it came from. One
source, no hand-drawn pictures, nothing to drift.

It is built on [sphinx-needs](https://sphinx-needs.readthedocs.io/),
[MyST](https://myst-parser.readthedocs.io/) and PlantUML. mbselite adds a
fixed, project-independent vocabulary (a small subset of SysML v2), the
conventions that make the diagrams read correctly, a box template that
shows what each thing does, a click-to-zoom viewer with dark mode, and an
authoring guide written so that both people and AI assistants can write
specs with it.

## Where it sits

mbselite is the last step of a spec-driven workflow, not a replacement for
it:

1. A person and an AI assistant brainstorm a change.
2. [OpenSpec](https://github.com/Fission-AI/OpenSpec) turns that into a
   proposal, a design and a spec with requirements and WHEN/THEN scenarios.
   The [Superpowers](https://github.com/obra/superpowers) skills for Claude
   Code drive the brainstorming, planning and test-first implementation
   around it.
3. mbselite renders the spec: the AI writes or converts the spec into typed
   blocks following `mbselite/GUIDE.md`, the build generates the diagrams
   and tables a person reads, and every box links back to the text.

Steps 1 and 2 are optional. Any Markdown spec with requirements and
behaviour can be written in mbselite form directly. But that is the
workflow this was built in, and the guide assumes specs that look like
OpenSpec output.

## Requirements

Build:

| What | Tested with | Notes |
|---|---|---|
| Python | 3.12, 3.13 | 3.11 or newer (sphinx ≥ 9.1 requires it); `build.py` stops with a one-line message on older |
| Java | 1.8 | any JRE 8+ |
| Graphviz | 12.2.1 | `dot` on PATH or in `tools/graphviz/bin/` |
| PlantUML | 1.2025.4 | `plantuml` on PATH, or `plantuml.jar` in `tools/` at the project root (next to `build.py`) |
| Python packages | see `requirements.txt` | sphinx 9.1, sphinx-needs 8.5, myst-parser 5.1, furo, sphinxcontrib-plantuml, pillow; installed by `build.py` |

Authoring, if an AI writes the specs: any assistant that can read
`mbselite/GUIDE.md` and write files. It was developed with Claude Code.
Give the assistant the guide, the metamodel `mbselite/__init__.py` and
the source document; nothing else is needed. Three blind trials, each
with a fresh assistant and only those files, produced specs that built
clean on the first try.

Verification, optional: have a second assistant that has not seen the
source read only the built site and describe the system back; compare
with the source. That is how the conventions in the guide were tuned.

## Why

Specifications written as prose are easy to write and hard to overview.
Diagrams are easy to overview and drift from the prose. mbselite makes the
prose the single source: the document is for whoever writes and reads the
detail, the generated views are for whoever needs the shape. A number
changed in the document changes in every diagram and table on the next
build, and nowhere else.

## Conventions it follows

- **sphinx-needs**, unchanged. A block is a MyST fenced directive with an
  `:id:`, options and a body. mbselite only supplies the configuration
  sphinx-needs needs anyway: thirteen block types (requirement, scenario,
  constraint, component, artifact, interface, action, decision, loop,
  state, transition, rule, record), the link kinds (`flows_to`, `fails_to`,
  `reenters`, `verifies`, `satisfies`, `part_of`, ...) and six fields.
- **OpenSpec** for requirement and scenario text: SHALL statements, WHEN /
  THEN scenarios, source citations. The text is kept verbatim; mbselite
  wraps it in a typed block so it gets an ID and links. Note that this
  wrapper is not what the `openspec` CLI validator expects, so a converted
  spec is an mbselite spec, not an OpenSpec one.
- **SysML v2** for the vocabulary: the block types are a small subset of its
  element kinds, and diagrams are views of the model, never the model.

The vocabulary, the conventions, modelling guidance (loops, state machines,
traceability) and view examples are in
[`mbselite/GUIDE.md`](mbselite/GUIDE.md). `specs/example-ota.md` is a
complete spec of a firmware updater written from that guide alone.

## What you get

- Flow diagrams of actions and decisions, with fail paths and loop
  re-entries drawn as their own arrow kinds.
- State machines with guards on the transitions.
- Traceability views and tables: requirement ↔ scenario, loop limits,
  gates, anything filterable by type, field or document.
- Every box shows type, a verb-phrase title, a one-line summary and the
  ID, and links to the full block. Click a diagram to open it in a
  pan-and-zoom viewer. Dark mode works.
- `needs.json`: every block with all fields and links, for scripts, tests
  or an AI to read.
- The build is the check: a dangling link, a missing ID or an unknown field
  fails the build.

## Install

Python 3.11 or newer, Java, Graphviz and PlantUML. Where `python3` is older
(Ubuntu 22.04 ships 3.10), run `python3.12 build.py` instead; the `.venv` is
created by whichever interpreter runs `build.py` first.

Linux (Debian/Ubuntu):

    sudo apt install python3-venv default-jre graphviz plantuml

macOS:

    brew install openjdk graphviz plantuml

Windows: install a JRE, then either put `dot` and `plantuml` on `PATH`, or
unzip a [Graphviz release](https://graphviz.org/download/) to
`tools/graphviz/` and drop
[`plantuml.jar`](https://github.com/plantuml/plantuml/releases) into
`tools/` next to `build.py`. The `tools/` folder is git-ignored.

Then:

    git clone https://github.com/shayus72/mbselite.git
    cd mbselite
    python build.py        # creates .venv, installs, builds, opens the site

`./build.sh` and `build.cmd` do the same on their platform. A clean build
prints no warnings. The build always runs from the project root (`build.py`
next to `specs/`); there is no `specs/build.py`.

Sphinx rebuilds only pages whose sources changed and never deletes output.
`build.py` adds `-a -E` by itself when a file in `mbselite/` is newer than the
last build. After deleting or renaming a spec, remove `specs/_build/` (or at
least the stale `.html`) so the old page does not linger.

## Layout

    mbselite/         the tool: metamodel (__init__.py), build hook, viewer, GUIDE.md
    mbselite/tools/   install.py, OpenSpec converter, Claude Code hooks, KiCad scaffolder
    specs/            your spec files, conf.py, index.md
    build.py          cross-platform build script

## As a Claude Code skill

    npx skills add shayus72/mbselite

installs the `mbselite` skill next to the
[spec-driven-tdd](https://github.com/strelov1/spec-driven-tdd) pack. Invoke
it after a spec is written or changed; it bootstraps the kit into the
project if needed, follows the guide, builds and checks. The skill is
`skills/mbselite/SKILL.md` and contains no code of its own.

## Use in your own project

1. From the project root:

       rm -rf /tmp/mbselite && git clone --depth 1 https://github.com/shayus72/mbselite.git /tmp/mbselite
       python3 /tmp/mbselite/mbselite/tools/install.py .     # --kicad for hardware projects

   This copies `mbselite/`, `build.py`, `build.sh`, `build.cmd` and
   `requirements.txt` (refreshing older copies), creates `specs/conf.py` and
   `specs/index.md` if they are missing, and merges the Claude Code hooks
   (below) into `.claude/settings.json`, keeping every other setting and
   hook. Re-running it updates the kit; `--no-hooks` skips the settings,
   `--dry-run` only lists what it would do. It never edits an existing
   `specs/conf.py` or `specs/index.md`; a `todo:` line says what they still
   need (`"**/*.model.md"` in `exclude_patterns`, `generated-index` in the
   toctree of an OpenSpec project). If the project's `.gitignore`
   ignores `tools/` (for `plantuml.jar`), write it as `/tools/`, or
   `mbselite/tools/` will not be committed.
2. Check `project` and `html_title` in `specs/conf.py`.
3. Write specs in `specs/` and list them in `specs/index.md`, or, in an
   OpenSpec project, let the converter generate them (next section).
4. Give `mbselite/GUIDE.md` to whoever writes specs, human or AI. It is
   self-contained.

## OpenSpec projects

`mbselite/tools/openspec2mbselite.py` (stdlib only) makes the rendered pages
a generated twin of the OpenSpec specs, so there is one source. Expected
layout, relative to the project root:

    openspec/changes/<change>/specs/<capability-path>/spec.md   active changes (archive/ skipped)
    openspec/changes/<change>/.openspec.yaml                     optional x-mbselite_id_prefix
    openspec/specs/<capability-path>/spec.md                     synced main specs (change "main")
    specs/index.md                                               lists `generated-index` once

It writes one page per capability at `specs/<change>/<capability-path>.md`,
an index per change and `specs/generated-index.md`. Each `### Requirement:`
becomes a `requirement` block and each `#### Scenario:` a `scenario` block
that `verifies` it, text verbatim; IDs are `REQ-<CAP>-<TITLE>` and
`SC-<CAP>-<TITLE>-<n>` from the headings. A `Source: …` / `**Source:** …` line
sets `:source:`, `ASSUMED` sets `:kind: assumed`, REMOVED / RENAMED
requirements are skipped. Every capability gets a default `component` that is
`part_of` its parent path, so a nested tree renders as a hierarchy.
Generated pages carry a marker line and are never edited; hand-written model
blocks go in `<page>.model.md` next to the page (or `index.model.md` for a
change), which the page includes instead of the default component.
`specs/conf.py` excludes `**/*.model.md` so fragments are not built twice.
`--check` exits 1 when a page is out of date (CI, pre-commit).

**Clashing capability names.** Two changes with a capability of the same
last path segment (`hardware/board` and `firmware/board`), or a change that
modifies a capability of another change or of the main specs, generate the
same IDs; the converter lists them and exits 1. Give one change a prefix in
its `.openspec.yaml` (OpenSpec ignores `x-` keys):

    x-mbselite_id_prefix: FN

and its IDs become `REQ-FN-BOARD-…`, `SC-FN-…`, `COMP-FN-…`.

**Claude Code hooks** (installed by `install.py`, commands relative to
`$CLAUDE_PROJECT_DIR`):

- PostToolUse `Edit|Write|MultiEdit|Bash` → `mbselite/tools/on-spec-change.sh`.
  After a `*.md` under `openspec/` or `specs/` is written (or, for Bash, when
  one is newer than the last build) it runs the converter and
  `build.py --no-open -q`; warnings come back to the session (exit 2). It
  uses `$MBSELITE_PYTHON` or the first `python3.x` ≥ 3.11 on PATH.
- SessionStart → `mbselite/tools/session-hint.sh` (`--kicad` only, below).

A settings file changed mid-session takes effect after `/hooks` or a
restart. The hooks are bash scripts (Linux, macOS, Git Bash on Windows).

## Hardware projects (KiCad)

    python3 mbselite/tools/kicad_sheets2spec.py ROOT.kicad_sch --change NAME \
        [--domain hardware] [--pcb-json pcb.json] [--slug-map specs/sheet-slugs.json] [--dry-run]

walks the sheet hierarchy and, for every sheet with components of its own,
writes (never overwriting) an OpenSpec delta spec
`openspec/changes/NAME/specs/<domain>/sheets/<slug>/…/spec.md` and a model
fragment with the sheet's component, nested like the schematic, plus
`<domain>/board` for the root sheet. Sheets holding only sub-sheets are
treated as containers. Slugs default to the kebab-case sheet-file stem; the
slug map (JSON `{"<file stem or sheet name>": "<slug>"}` or `a=b,c=d`) picks
better names. A `pcb.json` from kicad-happy adds footprint counts and
positions to the Purpose. The scaffolded requirement is a placeholder
marked ASSUMED; replace it. The change must exist
first (`/opsx:propose`). `install.py --kicad` adds the SessionStart hint that
reports sheets against capabilities. To make `/opsx:propose` follow the
one-capability-per-sheet convention, state it as a rule in
`openspec/config.yaml`, for example:

    rules:
      proposal:
        - One capability per functional KiCad sheet under <domain>/sheets/<slug>,
          nested like the schematic, plus <domain>/board for the root sheet.
      specs:
        - Scaffold with mbselite/tools/kicad_sheets2spec.py, then replace the
          placeholder requirement. Every requirement ends with a **Source:** line.

Never add project-specific types to `mbselite/`. A project's own words
(stage, gate, step, ...) go in the `kind` field of a block, and views
filter on it.

## Credits

sphinx-needs by useblocks (MIT), Sphinx (BSD), MyST-Parser (MIT), Furo
(MIT), sphinxcontrib-plantuml (BSD). PlantUML (GPL) and Graphviz (EPL) are
run as external programs and are not part of this repository.

## License

MIT, see `LICENSE`.
