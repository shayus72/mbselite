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

## Why

Specifications written as prose are easy to write and hard to overview.
Diagrams are easy to overview and drift from the prose. mbselite makes the
prose the single source: the document is for whoever writes and reads the
detail, the generated views are for whoever needs the shape. A number
changed in the document changes in every diagram and table on the next
build, and nowhere else.

## What a spec looks like

```markdown
## Download retry (design.md §2)

```{loop} Download retry
:id: LOOP-DL
:source: design.md §2
:summary: Up to 3 attempts; progress is verified chunks; then give up.
:limit: 3 attempts
:measure: verified chunks
:reenters: ACT-DL-FETCH
:fails_to: ACT-DL-ABANDON
```

```{decision} Image valid?
:id: DEC-DL-VALID
:kind: check
:part_of: LOOP-DL
:source: design.md §2
:summary: Checksum and signature match. Fail: try again.
:flows_to: ACT-DL-WRITE
:fails_to: LOOP-DL
```
```

Thirteen block types: requirement, scenario, constraint, component,
artifact, interface, action, decision, loop, state, transition, rule,
record. A handful of link kinds (`flows_to`, `fails_to`, `reenters`,
`verifies`, `satisfies`, `part_of`, ...) and six fields. Views are declared
in the same Markdown:

```markdown
```{needflow} Flow
:config: lr
:filter: type in ["action", "decision", "loop"] and docname == "updater"
:link_types: flows_to, fails_to, reenters
:show_link_names:
```
```

The full vocabulary, the conventions, modelling guidance (loops, state
machines, traceability) and view examples are in
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
