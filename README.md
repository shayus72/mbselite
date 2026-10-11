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
| Python | 3.13 | 3.10 or newer |
| Java | 1.8 | any JRE 8+ |
| Graphviz | 12.2.1 | `dot` on PATH or in `tools/graphviz/bin/` |
| PlantUML | 1.2025.4 | `plantuml` on PATH or `tools/plantuml.jar` |
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

Python 3.10 or newer, Java, Graphviz and PlantUML.

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
prints no warnings.

## Layout

    mbselite/   the tool: metamodel (__init__.py), build hook, viewer, GUIDE.md
    specs/      your spec files, conf.py, index.md
    build.py    cross-platform build script

## Use in your own project

1. Clone, or copy `mbselite/`, `specs/conf.py`, `specs/index.md`,
   `requirements.txt` and `build.py` into the project.
2. Set `project` and `html_title` in `specs/conf.py`.
3. Write specs in `specs/`, list them in `specs/index.md`, delete the
   example.
4. Give `mbselite/GUIDE.md` to whoever writes specs, human or AI. It is
   self-contained.

Never add project-specific types to `mbselite/`. A project's own words
(stage, gate, step, ...) go in the `kind` field of a block, and views
filter on it.

## Credits

sphinx-needs by useblocks (MIT), Sphinx (BSD), MyST-Parser (MIT), Furo
(MIT), sphinxcontrib-plantuml (BSD). PlantUML (GPL) and Graphviz (EPL) are
run as external programs and are not part of this repository.

## License

MIT, see `LICENSE`.
