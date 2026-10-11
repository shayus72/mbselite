# mbse-kit

Lightweight model-based specs on sphinx-needs. Write a spec in Markdown with
typed blocks (requirement, scenario, action, decision, loop, state, ...);
the build generates clickable diagrams, tables and a JSON export from them.
One source, no hand-drawn pictures.

- Authoring guide and conventions: `specsite/README.md`
- Metamodel (shared, never project-specific): `specsite/mbse_vocab.py`
- Example spec: `specsite/example-ota.md`

## Run

Needs Python 3.10+, Java, Graphviz and PlantUML (see `tools/README.md`).

    python build.py          # creates .venv on first run, builds, opens the site
    ./build.sh | build.cmd   # same, per platform

## Use in a project

Copy this folder into the project (or add it as a submodule), set `project`
and `html_title` in `specsite/conf.py`, delete `example-ota.md`, write
specs, list them in `specsite/index.md`.
