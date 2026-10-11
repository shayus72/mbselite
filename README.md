# mbselite

Lightweight model-based specs on sphinx-needs. Write a spec in Markdown with
typed blocks (requirement, scenario, action, decision, loop, state, ...);
the build generates clickable diagrams, tables and a JSON export from them.
One source, no hand-drawn pictures.

- Authoring guide and conventions: `mbselite/GUIDE.md`
- Metamodel (shared, never project-specific): `mbselite/__init__.py`
- Example spec: `specs/example-ota.md`

## Run

Needs Python 3.10+, Java, Graphviz and PlantUML (see `tools/README.md`).

    python build.py          # creates .venv on first run, builds, opens the site
    ./build.sh | build.cmd   # same, per platform

## Layout

    mbselite/   the tool: metamodel, build hook, viewer, authoring guide
    specs/      your spec files, conf.py, index.md
    tools/      optional portable Graphviz and plantuml.jar (git-ignored)

## Use in a project

Clone, or copy `mbselite/`, `specs/conf.py`, `specs/index.md`,
`requirements.txt` and `build.py` into the project. Set `project` and
`html_title` in `specs/conf.py`, delete `example-ota.md`, write specs, list
them in `specs/index.md`. Full guide: `mbselite/GUIDE.md`.
