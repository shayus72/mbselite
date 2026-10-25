#!/usr/bin/env bash
# Claude Code SessionStart hook (KiCad hardware projects; installed by
# mbselite/tools/install.py --kicad): tell the session what kind of project
# this is and whether the KiCad sheet hierarchy is covered by OpenSpec specs.
# Output goes into the session context. Silent when nothing applies.
# Project root: $MBSELITE_ROOT, else two levels above this script.
set -u
TOOLS="$(cd "$(dirname "$0")" && pwd)"
ROOT="${MBSELITE_ROOT:-$(cd "$TOOLS/../.." && pwd)}"
cd "$ROOT" || exit 0
REL_TOOLS="${TOOLS#"$ROOT"/}"

# A root schematic instantiates sub-sheets but is itself not named as a Sheetfile anywhere.
roots=()
for f in *.kicad_sch; do
  [ -f "$f" ] || continue
  grep -q '(sheet' "$f" && ! grep -q "\"$(basename "$f")\"" ./*.kicad_sch 2>/dev/null && roots+=("$f")
done
[ ${#roots[@]} -gt 0 ] || exit 0

sheets=$(grep -l -E '\(property "Reference" "[A-Z]' ./*.kicad_sch 2>/dev/null | wc -l)
subsheets=$(grep -ho '(property "Sheetfile" "[^"]*"' ./*.kicad_sch 2>/dev/null | sort -u | wc -l)
changes=$(ls -d openspec/changes/*/ 2>/dev/null | grep -v archive | wc -l)
caps=$(find openspec/changes -path '*/archive' -prune -o -name spec.md -print 2>/dev/null | wc -l)

echo "KiCad hardware project: root schematic ${roots[*]}, $subsheets hierarchical sub-sheet(s) across $sheets sheet files."
echo "OpenSpec: $changes change(s), $caps capability spec(s). Specs mirror the sheet hierarchy (one capability per sheet)."
if [ "$caps" -lt "$subsheets" ]; then
  echo "Some sheets have no capability yet — run: python3 $REL_TOOLS/kicad_sheets2spec.py ${roots[0]} --change <name> [--pcb-json <pcb.json>] [--slug-map specs/sheet-slugs.json] --dry-run"
fi
echo "mbselite site: python3 build.py --no-open from the repo root (Python 3.11+; auto-rebuilt by hook on spec edits) -> specs/_build/html/index.html"
exit 0
