# Lightweight MBSE on sphinx-needs

Generic kit. `mbselite/__init__.py` is the metamodel and is shared by every
project. A project adds a `conf.py` of about ten lines and writes its specs
in Markdown. Diagrams and tables are generated from the spec; nothing is
drawn by hand. Every box links back to the block it came from.

Layout: `mbselite/` is the tool (never edited per project), `specs/` holds
the project's spec files, `conf.py` and `index.md`.

## Writing a spec

A spec is a Markdown file. Prose stays prose. Every thing the prose would
otherwise describe becomes one typed block:

````markdown
```{action} Download the image
:id: ACT-DOWNLOAD
:kind: step
:source: design.md §2
:summary: Fetches the image in 1 MiB chunks into the staging slot.
:flows_to: DEC-CHECKSUM

Full detail here. Any Markdown. Read by clicking the box.
```
````

- The text after `{type}` is the **title**: say what happens, as a short
  verb phrase or a question. "Load the netlist", "Input supported?". Not a
  label like "load".
- `summary` is one sentence shown on the box. Titles and summaries are what
  a reader sees without clicking. Everything else is one click away.
- Options are `:name: value` lines directly under the title. Leave a blank
  line before the body. A `#` preceded by a space inside a value starts a
  comment and eats the rest; wrap such a value in double quotes.

### Types

| Area | Type | Prefix | Use for |
|---|---|---|---|
| requirements | requirement | REQ- | a SHALL statement |
| | scenario | SC- | a WHEN/THEN case; put WHEN and THEN as two bullets in the body |
| | constraint | CON- | a limit the design must respect |
| structure | component | COMP- | a part of the system |
| | artifact | ART- | a file or record passed between parts |
| | interface | IF- | a boundary between components |
| behaviour | action | ACT- | a step that runs |
| | decision | DEC- | a check with a pass path and a fail path |
| | loop | LOOP- | a bounded repetition |
| | state | STATE- | a mode the system can be in |
| | transition | TR- | a guarded move between two states |
| rules | rule | RULE- | a design or coding rule, or cross-cutting behaviour |
| | record | ADR- | a decision record |

IDs: uppercase letters, digits and hyphens, starting with the type prefix.
`ACT-LOAD`, `REQ-RUN-1`. No underscores. An ID must be unique across the
whole site, so prefix with the spec name when several specs share a site.

### Fields

| Field | Holds |
|---|---|
| `summary` | one sentence, shown on the box |
| `kind` | the project's own word for this item; see the starter set under Modelling guidance |
| `source` | where in the prose it came from, free text: "docs/01 §4" |
| `condition` | a guard or predicate, as text |
| `limit` | a bound: "6 rounds", "3 attempts", "60 s" |
| `measure` | what progress or success is measured by |
| `result` | what happens on reaching this item: verdict, exit code |

Any field may appear on any type. Unknown field names fail the build.

### Links

Declare a link on the item the arrow leaves from. Targets are IDs,
comma-separated: `:flows_to: ACT-A, DEC-B`. Any type may use any link; the
middle column is typical use, not a rule.

| Link | Typical | Meaning |
|---|---|---|
| `flows_to` | action/decision → next; state → transition | then |
| `fails_to` | decision or loop → where control goes on "no" or exhaustion | the "no" branch of any decision, a failure only for a loop; absent means the run stops |
| `reenters` | loop → action | where the loop jumps back to |
| `to_state` | transition → state | target of a transition |
| `part_of` | anything → loop/component/state | nesting; everything inside a loop is `part_of` it |
| `reads`, `writes`, `uses` | anything → artifact/component | data and dependencies |
| `verifies` | scenario → requirement | this case tests that statement |
| `satisfies` | anything → requirement | this element meets it; a loop may satisfy a retry limit |
| `refines` | requirement → requirement | detail of a broader one |
| `applies_to` | rule/constraint → anything | where it acts |
| `derived_from` | anything → record/requirement | provenance |

Both ends of a link must be in a view for the arrow to be drawn.

## Conventions

1. One block per thing. Types are fixed; the project's word goes in `kind`.
2. Every block has `id`, `source` and `summary`.
3. Links point the way the arrow should read. `flows_to` means "then",
   never "re-enters" or "on fail"; those have their own links.
4. A guard goes in the `transition` title so it shows on the diagram:
   `improved: rank key smaller, rounds < 6`. The full text goes in
   `condition`.
5. A loop is a `loop` block with `limit`, `measure`, `reenters` and, if it
   can give up, `fails_to`. See "Modelling a loop" below for what goes
   inside it.
6. Views filter by `type`, `kind`, `part_of` and `docname`. A view never
   fixes a layout.
7. The build is the check: a dangling link, a missing id or a wrong field is
   a build error.

## Views

Views are `needflow` (diagram) and `needtable` (table) blocks. Filters are
Python expressions over the fields; `type` is the type name, `docname` is
the spec file name without `.md`, link fields are lists. Start a filter with
an identifier, never with a quote.

````markdown
```{needflow} Flow
:config: lr
:filter: type in ["action", "decision", "loop"] and docname == "ota"
:link_types: flows_to, fails_to, reenters
:show_link_names:
```

```{needflow} Retry loop
:config: default
:filter: type in ["state", "transition"] and "LOOP-RETRY" in part_of
:link_types: flows_to, to_state
```

```{needflow} Traceability
:config: default
:filter: type in ["requirement", "scenario"] and docname == "ota"
:link_types: verifies
:show_link_names:
```

```{needtable} Loops
:filter: type == "loop" and docname == "ota"
:columns: id, title, limit, measure, reenters, fails_to
:style: table
```
````

Every `needflow` names a config: `:config: default` for top to bottom,
`:config: lr` for left to right. Without one the diagram gets no styling
and its lines come out black, invisible in dark mode.
Reverse links are available in tables as `<link>_back`, for example
`flows_to_back as "From"`.

## Modelling guidance

Decisions the vocabulary alone does not make for you.

### Modelling a loop

A loop is a container. Inside it sit the actions that repeat and the
decision that decides whether to go round again. That is the default and
is enough for most loops.

- Entering: the element before the loop `flows_to` the first inner
  action, not the loop box. The loop box is only ever the target of the
  inner decision's `fails_to`.
- Inner actions and the inner decision are `part_of` the loop.
- The inner decision `flows_to` the next action on pass and `fails_to` the
  loop on "try again". The loop `reenters` the first inner action.
- The loop `fails_to` the one element that runs when it gives up: an
  action, or a decision when giving up itself branches. It lives in the
  main flow. Giving up is an edge, not a block: do not also create a
  "give up" state or action inside the loop.
- Add `state` and `transition` blocks only when the guards are worth a
  diagram of their own. They are a second view of the same loop, not a
  replacement for its actions. Keep to about six states. States and
  transitions are all `part_of` the loop, or the loop view will not find
  them. A state where the loop ends carries `kind: exit` if the run goes
  on, `kind: final` if the run ends, and a `result` that says in words
  what the loop's `fails_to` target does.
- Unbounded repetition, such as "ask the user to retry", is not a loop.
  Use a backwards `flows_to` from the decision to the earlier action. A
  `loop` block always has a `limit`.

Worked example, a download that retries three times:

````markdown
```{loop} Download retry
:id: LOOP-DL
:summary: Up to 3 attempts; progress is verified chunks; then give up.
:limit: 3 attempts
:measure: verified chunks
:reenters: ACT-DL-FETCH
:fails_to: ACT-DL-ABANDON
```

```{action} Fetch the image
:id: ACT-DL-FETCH
:kind: step
:part_of: LOOP-DL
:summary: Downloads the image into the staging slot.
:flows_to: DEC-DL-VALID
```

```{decision} Image valid?
:id: DEC-DL-VALID
:kind: check
:part_of: LOOP-DL
:summary: Checksum and signature match. Fail: try again.
:flows_to: ACT-DL-WRITE
:fails_to: LOOP-DL
```

```{action} Abandon the update
:id: ACT-DL-ABANDON
:kind: final
:summary: Marks the update failed and sleeps until the next check.
:result: update record = failed
```
````

### Starter set for `kind`

Reuse a word the site already uses before inventing one. These are the
conventional ones:

| Type | kinds |
|---|---|
| action | `step`, `final` (the run ends here) |
| decision | `check` (inside a loop), `gate` (any decision outside a loop) |
| state | `step`, `exit` (loop ends, run continues), `final` (run ends) |
| artifact | `file`, `record`, `log` |
| component | `system`, `external` |

`kind` is optional on requirement, scenario, transition, constraint, rule
and record.

### Titles by type

| Type | Title | Where the rest goes |
|---|---|---|
| action, loop | verb phrase: "Fetch the image" | `summary` |
| decision | question: "Image valid?" | `summary` says what fail means |
| state | noun phrase: "Waiting for rig" | `summary` |
| transition | `label: guard`, e.g. `busy: tries < 10` | `condition` only if the title had to shorten the guard |
| requirement | short name: "One result per push" | the SHALL sentence in the body, `summary` in plain words |
| scenario | short name | two bullets in the body, **WHEN** and **THEN** |
| artifact, component, interface | noun | `summary` |

### Multiple targets

Any link takes a list: `:flows_to: TR-A, TR-B, TR-C`. A state with three
exits lists its three transitions.

### Which link, when

- Design element meets a requirement: element `satisfies` requirement.
- Constraint comes from a requirement: constraint `derived_from`
  requirement. Constraint binds an element: constraint `applies_to`
  element.
- A rule for every step in a component: rule `applies_to` the component.
  List individual IDs only for exceptions.
- `reads` and `writes` are for data, whether the other end is an artifact
  or a component. `uses` is for a service or tool with no data of its own.

### Site and views

- `docname` is the path without `.md`, so a spec in `specs/ci.md` is
  `"specs/ci"`.
- `:show_link_names:` prints the link name on every arrow. Leave it off
  when one link type is drawn and the arrows need no label.
- Every link has a `<link>_back` reverse for tables. Column aliases need
  quotes: `flows_to_back as "From"`.
- A block body is optional. Leave a blank line before it when present.

## Project setup

Layout of the repo:

    mbselite/      the tool: metamodel, build hook, viewer, this guide. Never edited per project.
    specs/         the project's spec files, plus conf.py and index.md
    tools/         optional portable Graphviz and plantuml.jar (git-ignored)
    build.py       cross-platform build; build.sh / build.cmd wrap it

1. Clone the repo, or copy `mbselite/`, `specs/conf.py`, `specs/index.md`,
   `requirements.txt` and the build scripts into an existing project.
2. Set `project` and `html_title` in `specs/conf.py`. Delete
   `specs/example-ota.md` once you have your own specs.
3. Install the renderers: Java plus Graphviz and PlantUML on `PATH`, or
   drop portable copies into `tools/` (see Install).
4. Run `python build.py`. First run creates `.venv` and installs
   `requirements.txt`. A clean build prints no warnings.
5. List each spec file in the `toctree` of `specs/index.md`.
