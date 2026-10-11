"""Generic, project-independent vocabulary for lightweight MBSE on top of
sphinx-needs. Import it from any project's conf.py:

    from mbse_vocab import *

A project never adds types here. Its own words (stage, gate, loop, ...) go in
the `kind` field of an item, so views can filter on them without a new type.

Vocabulary (type -> ID prefix), mirroring SysML v2 element kinds:

  requirements  requirement REQ-   scenario SC-     constraint CON-
  structure     component  COMP-  artifact ART-    interface IF-
  behaviour     action     ACT-   state    STATE-  transition TR-   decision DEC-   loop LOOP-
  rules         rule       RULE-  record   ADR-

Links (declared on the source item; the arrow is drawn source -> target, so a
link name must read as flow from the item that declares it):

  satisfies, verifies, refines        requirement traceability
  part_of, reads, writes, uses        structure
  flows_to, to_state                  behaviour (state -flows_to-> transition -to_state-> state)
  fails_to                            decision/loop -> where control goes on fail or exhaustion (none = stop)
  reenters                            loop -> the action it jumps back to
  applies_to, derived_from            rules and provenance
"""

needs_id_required = True
needs_id_regex = r"^[A-Z]+-[A-Z0-9-]+$"
needs_flow_engine = "plantuml"
needs_build_json = True
needs_show_link_type = True
needs_show_link_title = False
needs_default_layout = "clean"

# PlantUML node styles: node card component folder hexagon usecase storage
# file rectangle artifact database frame package
needs_types = [
    # requirements
    {"directive": "requirement", "title": "Requirement", "prefix": "REQ-", "color": "#DBEAFE", "style": "rectangle"},
    {"directive": "scenario", "title": "Scenario", "prefix": "SC-", "color": "#FEF3C7", "style": "rectangle"},
    {"directive": "constraint", "title": "Constraint", "prefix": "CON-", "color": "#FEE2E2", "style": "file"},
    # structure
    {"directive": "component", "title": "Component", "prefix": "COMP-", "color": "#E0E7FF", "style": "component"},
    {"directive": "artifact", "title": "Artifact", "prefix": "ART-", "color": "#F1F5F9", "style": "artifact"},
    {"directive": "interface", "title": "Interface", "prefix": "IF-", "color": "#F1F5F9", "style": "frame"},
    # behaviour
    {"directive": "action", "title": "Action", "prefix": "ACT-", "color": "#E0E7FF", "style": "card"},
    {"directive": "state", "title": "State", "prefix": "STATE-", "color": "#FEF9C3", "style": "usecase"},
    {"directive": "transition", "title": "Transition", "prefix": "TR-", "color": "#FFFFFF", "style": "rectangle"},
    {"directive": "decision", "title": "Decision", "prefix": "DEC-", "color": "#FEE2E2", "style": "hexagon"},
    {"directive": "loop", "title": "Loop", "prefix": "LOOP-", "color": "#FFEDD5", "style": "folder"},
    # rules and provenance
    {"directive": "rule", "title": "Rule", "prefix": "RULE-", "color": "#DCFCE7", "style": "file"},
    {"directive": "record", "title": "Decision record", "prefix": "ADR-", "color": "#F3E8FF", "style": "folder"},
]

needs_links = {
    # requirements
    "satisfies": {"incoming": "satisfied by", "outgoing": "satisfies", "color": "#64748B"},
    "verifies": {"incoming": "verified by", "outgoing": "verifies", "color": "#64748B", "style": "dashed"},
    "refines": {"incoming": "refined by", "outgoing": "refines", "color": "#64748B", "style": "dotted"},
    # structure
    "part_of": {"incoming": "contains", "outgoing": "part of", "color": "#94A3B8", "style": "dotted"},
    "reads": {"incoming": "read by", "outgoing": "reads", "color": "#0EA5E9", "style": "dashed"},
    "writes": {"incoming": "written by", "outgoing": "writes", "color": "#0EA5E9"},
    "uses": {"incoming": "used by", "outgoing": "uses", "color": "#94A3B8", "style": "dashed"},
    # behaviour
    "flows_to": {"incoming": "flows from", "outgoing": "flows to", "color": "#1D4ED8"},
    "to_state": {"incoming": "entered via", "outgoing": "to", "color": "#D97706"},
    "fails_to": {"incoming": "on fail from", "outgoing": "on fail", "color": "#DC2626", "style": "dashed"},
    "reenters": {"incoming": "re-entered by", "outgoing": "re-enters", "color": "#EA580C", "style": "bold"},
    # rules and provenance
    "applies_to": {"incoming": "governed by", "outgoing": "applies to", "color": "#16A34A", "style": "dashed"},
    "derived_from": {"incoming": "source of", "outgoing": "derived from", "color": "#7C3AED", "style": "dotted"},
}

_str = {"schema": {"type": "string"}}
needs_fields = {
    "kind": _str,       # the project's own word for this item; "final" is reserved
    "summary": _str,    # one sentence shown on the diagram box
    "source": _str,     # citation into the prose: "docs/01 §4"
    "condition": _str,  # guard or predicate, as text
    "limit": _str,      # a bound: "6 rounds", "3 attempts", "250 ms"
    "measure": _str,    # what progress or success is measured by
    "result": _str,     # what happens on reaching this item: verdict, exit code
}

# What a box shows: type, title, one-line summary, id. Everything else is one
# click away.
needs_diagram_template = (
    r"<size:10>{{type_name}}</size>\n"
    r"**{{title|wordwrap(26, wrapstring='**\\n**')}}**"
    r"{% if summary %}\n{{summary|wordwrap(34, wrapstring='\\n')}}{% endif %}"
    r"\n<size:9>{{id}}</size>"
)

# Diagram look. "default" applies everywhere; "lr" lays out left to right.
_skin = """
skinparam defaultFontName {font}
skinparam defaultFontSize 11
skinparam shadowing false
skinparam roundCorner 8
skinparam backgroundColor transparent
skinparam ArrowColor #64748B
skinparam ArrowFontColor #475569
skinparam ArrowFontSize 9
skinparam nodesep 30
skinparam ranksep 40
skinparam defaultTextAlignment left
skinparam LineThickness 0.8
"""
import sys as _sys
_skin = _skin.replace("{font}", "Segoe UI" if _sys.platform == "win32" else "DejaVu Sans")
needs_flow_configs = {
    "default": _skin,
    "lr": _skin + "left to right direction" + chr(10),
}
needs_flow_show_links = True
