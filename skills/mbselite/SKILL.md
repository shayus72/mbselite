---
name: mbselite
description: Render a spec as clickable diagrams and tables from one Markdown source. Use after a spec (OpenSpec or any requirements document) is written or changed, before review, or when someone asks to visualise, diagram or "see" a spec, pipeline, loop, state machine or traceability.
---

# mbselite

One source, generated views. The spec stays Markdown; typed blocks in it
produce flow diagrams, state machines, traceability views and tables, each
box linking back to its block. Nothing is drawn by hand.

## 1. Make sure the kit is in the project

If the project has no `mbselite/` folder:

```
git clone --depth 1 https://github.com/shayus72/mbselite.git /tmp/mbselite
cp -r /tmp/mbselite/mbselite /tmp/mbselite/build.py /tmp/mbselite/requirements.txt .
mkdir -p specs && cp -n /tmp/mbselite/specs/conf.py /tmp/mbselite/specs/index.md specs/
```

Set `project` and `html_title` in `specs/conf.py`. Build needs Python 3.10+,
Java, Graphviz and PlantUML (see the kit README's Install section).

## 2. Read the guide, then write

Read `mbselite/GUIDE.md` in full before writing any block. It holds the
vocabulary, the conventions, the modelling guidance for loops and state
machines, and view examples. Do not invent types, fields or links.

Converting an existing spec: keep every requirement SHALL sentence and every
scenario WHEN/THEN pair verbatim inside `requirement` and `scenario` blocks;
move the trailing citation into `:source:`. Model behaviour (actions,
decisions, loops, artifacts) only where the spec or the documents it cites
state it. Every block gets `:id:`, `:source:`, `:summary:`.

Writing a new spec: same rules; the OpenSpec shape (Purpose, Requirements
with Scenarios) is the expected skeleton.

## 3. Build and check

```
python build.py --no-open
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
