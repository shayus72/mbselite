---
name: mbselite
description: Render a spec as clickable diagrams and tables from one Markdown source. Use after a spec (OpenSpec or any requirements document) is written or changed, before review, or when someone asks to visualise, diagram or "see" a spec, pipeline, loop, state machine or traceability.
---

# mbselite

One source, generated views. The spec stays Markdown; typed blocks in it
produce flow diagrams, state machines, traceability views and tables, each
box linking back to its block. Nothing is drawn by hand.

## 1. Make sure the kit is in the project

If the project has no `mbselite/` folder (or to update an older copy), run
the kit's installer from the project root:

```
rm -rf /tmp/mbselite && git clone --depth 1 https://github.com/shayus72/mbselite.git /tmp/mbselite
python3 /tmp/mbselite/mbselite/tools/install.py .            # add --kicad for a KiCad hardware project
```

It copies `mbselite/` (with `mbselite/tools/`), `build.py`, `build.sh`,
`build.cmd` and `requirements.txt`; creates `specs/conf.py` and
`specs/index.md` only if missing (do what any `todo:` line it prints says
about existing ones); and merges the hooks into
`.claude/settings.json` without touching other settings or hooks:

- PostToolUse (Edit|Write|MultiEdit|Bash): `mbselite/tools/on-spec-change.sh`
  regenerates the pages from `openspec/` and rebuilds after every spec edit;
  build warnings come back to you as hook output (exit 2). Fix them.
- SessionStart, `--kicad` only: `mbselite/tools/session-hint.sh` reports the
  KiCad sheet hierarchy against the OpenSpec capabilities.

Hooks added mid-session fire only after `/hooks` or a restart; until then
run the converter and the build yourself (step 3). Check `project` and
`html_title` in `specs/conf.py`. The build needs Python 3.11+, Java,
Graphviz and PlantUML (see the kit README's Install section).

OpenSpec project: do not hand-convert. `mbselite/tools/openspec2mbselite.py`
turns `openspec/changes/<change>/specs/<cap>/spec.md` (and `openspec/specs/`)
into one generated page per capability under `specs/<change>/`, never to be
edited. Model content you add goes in a `<page>.model.md` fragment next to
the generated page. Two changes with the same capability name need
`x-mbselite_id_prefix: XX` in one change's `.openspec.yaml`.

KiCad project (`*.kicad_sch` with `(sheet` blocks): offer
`python3 mbselite/tools/kicad_sheets2spec.py ROOT.kicad_sch --change NAME --dry-run`
to scaffold one capability and fragment per sheet; it never overwrites.

## 2. Read the guide, then write

Read `mbselite/GUIDE.md` in full before writing any block. It holds the
vocabulary, the conventions, the modelling guidance for loops and state
machines, and view examples. Do not invent types, fields or links.

Converting a non-OpenSpec spec by hand: keep every requirement SHALL sentence and every
scenario WHEN/THEN pair verbatim inside `requirement` and `scenario` blocks;
move the trailing citation into `:source:`. Model behaviour (actions,
decisions, loops, artifacts) only where the spec or the documents it cites
state it. Every block gets `:id:`, `:source:`, `:summary:`.

Writing a new spec: same rules; the OpenSpec shape (Purpose, Requirements
with Scenarios) is the expected skeleton.

## 3. Build and check

```
python3 mbselite/tools/openspec2mbselite.py   # OpenSpec projects only
python3 build.py --no-open                    # from the project root, Python 3.11+
```

A clean build prints no warnings. Fix every warning: a dangling link, a
missing ID, an unknown field, a filter that starts with a quote, an option
value with a space-hash that needs quoting. List the spec in
`specs/index.md` if it is new.

## 4. Verify faithfulness (optional, recommended for conversions)

Have a fresh agent that has not seen the source read only the built site
(`specs/_build/html/`) and describe the system back; compare with the
source. Or hand it the source and `needs.json` and ask for every claim the
source does not support. Fix what it finds in the spec, never in the
generated output.
