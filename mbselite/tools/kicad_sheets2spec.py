#!/usr/bin/env python3
"""Scaffold OpenSpec capabilities and mbselite model fragments from a KiCad
hierarchical schematic — one capability per sheet, nested like the schematic.

For every sheet reachable from the root schematic this writes, unless the
file already exists (existing files are never touched):

  openspec/changes/<change>/specs/<domain>/sheets/<slug>[/<child-slug>...]/spec.md
      OpenSpec delta spec: Purpose pre-filled from the sheet (name, file, key
      parts, footprint count and bounding box when a kicad-happy pcb.json is
      given) and one placeholder requirement (ASSUMED) to replace.
  specs/<change>/<domain>/sheets/<slug>[...].model.md
      mbselite fragment with the sheet's component block: source = sheet
      file, part_of = parent sheet's component (root: COMP-BOARD), summary
      from the key parts, satisfies = the scaffolded requirement's id.

plus, for the root sheet, `<domain>/board/spec.md` + `board.model.md`
(COMP-BOARD) and an `index.model.md` with the hierarchy diagram.

Sheets that hold no components of their own (only sub-sheet instances and
fiducials) are treated as containers: no capability, but their children are
scaffolded one level up (the KiCad "page 2" pattern).

Slugs default to the kebab-case sheet *file* stem (Power_Supply_sch →
power-supply-sch). Pass --slug-map name=slug,... (or a JSON file) to choose
better names; the map is keyed by sheet file stem or sheet name.

Usage:
  kicad_sheets2spec.py ROOT.kicad_sch --change NAME [--domain hardware]
      [--pcb-json pcb.json] [--out specs] [--slug-map MAP] [--dry-run]
Requires an existing OpenSpec change (run `openspec new change` / /opsx:propose first).
If the change's .openspec.yaml sets `x-mbselite_id_prefix: XX`, the ids written into
fragments carry it the way the converter does (COMP-XX-BOARD, COMP-XX-SHEET-..., REQ-XX-...).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from openspec2mbselite import change_id_prefix, slug as id_slug  # noqa: E402  same id scheme as the converter

RE_SHEET = re.compile(r'\(sheet\s.*?\(property "Sheetname" "([^"]+)".*?\(property "Sheetfile" "([^"]+)"', re.S)
RE_REF = re.compile(r'\(property "Reference" "([^"#]+)"')
# Key parts for a sheet summary, in display priority; passives, diodes, test points, fiducials, holes are left out.
KEY_PREFIXES = ("U", "Q", "K", "J", "T", "Y", "X", "SW", "TH", "F")
SKIP_PREFIXES = ("FB", "FID", "TP")


@dataclass
class Sheet:
    name: str
    file: Path
    refs: list[str] = field(default_factory=list)
    children: list["Sheet"] = field(default_factory=list)

    @property
    def is_container(self) -> bool:
        own = [r for r in self.refs if not r.startswith("FID")]
        return not own and bool(self.children)


def kebab(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return re.sub(r"-{2,}", "-", s)


def parse_sheet(file: Path, name: str, seen: set[Path]) -> Sheet:
    text = file.read_text(encoding="utf-8")
    refs = sorted({r for r in RE_REF.findall(text) if re.search(r"\d", r)})
    sheet = Sheet(name=name, file=file, refs=refs)
    for child_name, child_file in RE_SHEET.findall(text):
        child = file.parent / child_file
        key = child.resolve()
        if key in seen or not child.is_file():
            continue
        seen.add(key)
        sheet.children.append(parse_sheet(child, child_name, seen))
    return sheet


def load_pcb(path: Path | None) -> dict[str, dict]:
    if not path:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {f["reference"]: f for f in data.get("footprints", [])}


def describe(sheet: Sheet, fps: dict[str, dict]) -> tuple[str, str]:
    """Return (key-part summary, footprint facts) for a sheet."""
    def prefix_rank(ref: str) -> int:
        return next((i for i, p in enumerate(KEY_PREFIXES) if ref.startswith(p)), len(KEY_PREFIXES))

    key = sorted((r for r in sheet.refs if r.startswith(KEY_PREFIXES) and not r.startswith(SKIP_PREFIXES)),
                 key=lambda r: (prefix_rank(r), int(re.sub(r"\D", "", r) or 0)))
    parts = []
    for r in key[:10]:
        val = fps.get(r, {}).get("value")
        parts.append(f"{r} {val}" if val and str(val) not in ("~", "") else r)
    summary = ", ".join(parts) + (" …" if len(key) > 10 else "")
    placed = [fps[r] for r in sheet.refs if r in fps]
    facts = f"{len(sheet.refs)} components"
    if placed:
        xs = [f["x"] for f in placed]; ys = [f["y"] for f in placed]
        bottom = sum(1 for f in placed if f.get("layer") == "B.Cu")
        facts += (f", {len(placed)} placed ({len(placed) - bottom} top / {bottom} bottom), "
                  f"bbox x {min(xs):.0f}–{max(xs):.0f} mm, y {min(ys):.0f}–{max(ys):.0f} mm")
    return summary or "(passives only)", facts


def spec_skeleton(sheet: Sheet, summary: str, facts: str) -> str:
    return f"""# Spec Delta

## Purpose

Sheet `{sheet.file.name}` ("{sheet.name}"): {summary}.
{facts}. Scaffolded from the KiCad hierarchy — edit the Purpose and replace
the placeholder requirement below; every requirement needs a **Source:** line.

## ADDED Requirements

### Requirement: Sheet is specified
The `{sheet.file.name}` sheet SHALL meet the requirements written here in place
of this placeholder (ASSUMED: scaffolded, not yet specified).
**Source:** {sheet.file.name}

#### Scenario: Placeholder replaced
- **GIVEN** the scaffolded spec of `{sheet.file.name}`
- **WHEN** the change is reviewed
- **THEN** this requirement has been replaced by the sheet's real requirements
"""


def fragment(sheet: Sheet, comp_id: str, parent_id: str, summary: str, facts: str, req_ids: list[str]) -> str:
    sat = f":satisfies: {', '.join(req_ids)}\n" if req_ids else ""
    return f"""# {sheet.name}

## Model

```{{component}} {sheet.name}
:id: {comp_id}
:kind: sheet
:source: {sheet.file.name}
:part_of: {parent_id}
:summary: {summary}. {facts}.
{sat}
Scaffolded from the KiCad hierarchy; describe the block's role, interfaces
and constraints here.
```
"""


def board_fragment(root: Sheet, facts: str, req_ids: list[str], board_id: str = "COMP-BOARD") -> str:
    sat = f":satisfies: {', '.join(req_ids)}\n" if req_ids else ""
    return f"""# Board (root sheet)

## Model

```{{component}} {root.name or root.file.stem}
:id: {board_id}
:kind: system
:source: {root.file.name} (root)
:summary: Root sheet of the board. {facts}.
{sat}
Scaffolded from the KiCad hierarchy; describe the board, its connectors and
voltage domains here.
```
"""


def board_spec(root: Sheet) -> str:
    return f"""# Spec Delta

## Purpose

Board-level requirements from the root sheet `{root.file.name}`: what spans
sheets (connectors, power and voltage domains, mechanical fit). Scaffolded —
replace the placeholder requirement below.

## ADDED Requirements

### Requirement: Board is specified
The board SHALL meet the requirements written here in place of this
placeholder (ASSUMED: scaffolded, not yet specified).
**Source:** {root.file.name}

#### Scenario: Placeholder replaced
- **GIVEN** the scaffolded board spec
- **WHEN** the change is reviewed
- **THEN** this requirement has been replaced by the board's real requirements
"""


def index_fragment(change: str, title: str) -> str:
    return f"""# {title}

Specification mirrored on the KiCad sheet hierarchy: one page for the board
(root sheet) and one per functional sub-sheet, nested like the schematic.
Click a sheet in the hierarchy to open its page.

```{{needflow}} Sheet hierarchy — click a sheet to open its page
:config: default
:filter: type == "component" and "{change}/" in docname
:link_types: part_of
```

```{{needtable}} Sheets and their requirements
:filter: type == "component" and "{change}/" in docname
:columns: id, title, source, satisfies
:style: table
```

## Pages
"""


def req_ids_for(spec_text: str, cap_tail: str, prefix: str = "") -> list[str]:
    """The ids the converter will give these requirements (same slug lengths, same prefix)."""
    cap_slug = (f"{prefix}-" if prefix else "") + id_slug(cap_tail, 24)
    return [f"REQ-{cap_slug}-{id_slug(t, 60)}" for t in re.findall(r"^### Requirement:\s*(.+?)\s*$", spec_text, re.M)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root_sch", type=Path)
    ap.add_argument("--change", required=True)
    ap.add_argument("--domain", default="hardware")
    ap.add_argument("--pcb-json", type=Path)
    ap.add_argument("--out", type=Path, default=None, help="mbselite specs dir (default <project>/specs)")
    ap.add_argument("--slug-map", default="", help="name=slug,... or a JSON file {name_or_stem: slug}")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    root_sch = a.root_sch.absolute()   # not resolve(): a symlinked schematic still belongs to the project it sits in
    project = root_sch.parent
    change_dir = project / "openspec" / "changes" / a.change
    if not change_dir.is_dir():
        sys.exit(f"no OpenSpec change at {change_dir} — create it first (openspec new change / /opsx:propose)")
    out_dir = (a.out or project / "specs").resolve()
    # x-mbselite_id_prefix in the change's .openspec.yaml: the converter puts it after
    # the type prefix of every id (REQ-XX-..., COMP-XX-...); the fragments must match.
    prefix = change_id_prefix(project, a.change)
    px = f"{prefix}-" if prefix else ""
    board_id = f"COMP-{px}BOARD"

    slug_map: dict[str, str] = {}
    if a.slug_map:
        p = Path(a.slug_map)
        slug_map = json.loads(p.read_text()) if p.is_file() else dict(kv.split("=", 1) for kv in a.slug_map.split(",") if "=" in kv)

    def slug_of(sheet: Sheet) -> str:
        return slug_map.get(sheet.file.stem) or slug_map.get(sheet.name) or kebab(sheet.file.stem)

    fps = load_pcb(a.pcb_json.resolve() if a.pcb_json else None)
    root = parse_sheet(root_sch, root_sch.stem, {root_sch.resolve()})
    planned: dict[Path, str] = {}

    _, root_facts = describe(root, fps)
    board_spec_path = change_dir / "specs" / a.domain / "board" / "spec.md"
    planned[board_spec_path] = board_spec(root)
    planned[out_dir / a.change / a.domain / "board.model.md"] = board_fragment(
        root, root_facts, req_ids_for(planned[board_spec_path], "board", prefix), board_id)
    planned[out_dir / a.change / "index.model.md"] = index_fragment(a.change, f"{root.name} — {a.domain} specification")

    def walk(sheet: Sheet, cap_prefix: str, parent_id: str, depth: int) -> None:
        for child in sheet.children:
            if child.is_container:
                print(f"{'  ' * depth}[container] {child.name} ({child.file.name}) — descending")
                walk(child, cap_prefix, parent_id, depth + 1)
                continue
            s = slug_of(child)
            cap_path = f"{cap_prefix}/{s}"
            comp_id = f"COMP-{px}SHEET-" + id_slug(s, 30)
            summary, facts = describe(child, fps)
            spec_path = change_dir / "specs" / cap_path / "spec.md"
            planned[spec_path] = spec_skeleton(child, summary, facts)
            planned[out_dir / a.change / (cap_path + ".model.md")] = fragment(
                child, comp_id, parent_id, summary, facts, req_ids_for(planned[spec_path], s, prefix))
            print(f"{'  ' * depth}{child.name} ({child.file.name}) -> {cap_path}  [{len(child.refs)} refs]")
            walk(child, cap_path, comp_id, depth + 1)

    print(f"{root.name} ({root.file.name}) -> {a.domain}/board")
    walk(root, f"{a.domain}/sheets", board_id, 1)

    created = skipped = 0
    for path, text in planned.items():
        if path.exists():
            skipped += 1
            continue
        created += 1
        if not a.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    verb = "would create" if a.dry_run else "created"
    print(f"\nkicad_sheets2spec: {verb} {created} file(s), {skipped} already present (never overwritten)")
    if created and not a.dry_run:
        print("next: write real requirements in the scaffolded spec.md files, then run mbselite/tools/openspec2mbselite.py (the hook does it on save)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
