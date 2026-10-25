#!/usr/bin/env bash
# Claude Code PostToolUse hook (Edit|Write|MultiEdit|Bash), installed by
# mbselite/tools/install.py. When a Markdown file under openspec/ or specs/ is
# written, regenerate the mbselite pages from the OpenSpec specs and rebuild the
# site, so the rendered diagrams never lag the text.
#
# Project root: $MBSELITE_ROOT, else two levels above this script (the project
# that holds mbselite/tools/). The build is always run from that root.
# stdin: hook JSON {"tool_input": {"file_path": ...}, "tool_response": {"filePath": ...}}
# exit 0 = fine (one summary line); exit 2 = build warnings/errors, shown to the model.
set -u
TOOLS="$(cd "$(dirname "$0")" && pwd)"
ROOT="${MBSELITE_ROOT:-$(cd "$TOOLS/../.." && pwd)}"
cd "$ROOT" || exit 0
[ -f build.py ] && [ -d specs ] || exit 0                                          # not an mbselite project

# Interpreter: $MBSELITE_PYTHON, else the first python3.x >= 3.11 (sphinx 9 needs it).
PY="${MBSELITE_PYTHON:-}"
if [ -z "$PY" ]; then
  for c in python3.14 python3.13 python3.12 python3.11 python3; do
    command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null && { PY="$c"; break; }
  done
fi
[ -n "$PY" ] || { echo "mbselite hook: no Python 3.11+ found (set MBSELITE_PYTHON)" >&2; exit 0; }

FILE="$("$PY" -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print(""); sys.exit()
ti = d.get("tool_input") or {}
tr = d.get("tool_response") or {}
print(ti.get("file_path") or tr.get("filePath") or "")
' 2>/dev/null)"
# Bash (or any tool without a file_path): rebuild only if a spec Markdown file is
# newer than the last build. Scripts that patch openspec/ or specs/ via Bash
# otherwise leave the rendered twin stale.
if [ -z "$FILE" ]; then
  STAMP="$ROOT/specs/_build/html/needs.json"
  if [ -f "$STAMP" ]; then
    CHANGED="$(find "$ROOT/openspec" "$ROOT/specs" -name '*.md' -newer "$STAMP" -not -path '*/_build/*' 2>/dev/null | head -1)"
    [ -n "$CHANGED" ] || exit 0
    REL="${CHANGED#"$ROOT"/} (via Bash)"
  else
    REL="(no build yet)"
  fi
else
  REL="${FILE#"$ROOT"/}"
  [[ "$REL" == specs/_build/* ]] && exit 0                                          # build output
  [[ "$REL" =~ ^(openspec|specs)/.*\.md$ ]] || exit 0                               # only spec markdown
  head -c 200 "$FILE" 2>/dev/null | grep -q 'openspec2mbselite\.py from OpenSpec' && exit 0   # our own output
fi

LOG="$(mktemp)"
{
  { [ ! -d openspec ] || "$PY" "$TOOLS/openspec2mbselite.py" --root "$ROOT"; } && "$PY" build.py --no-open -q
} >"$LOG" 2>&1
RC=$?
if [ $RC -ne 0 ] || grep -qE 'WARNING|ERROR|Traceback' "$LOG"; then
  echo "mbselite rebuild after editing $REL reported problems:" >&2
  grep -E 'WARNING|ERROR|Traceback|Error|error:' "$LOG" | head -30 >&2
  rm -f "$LOG"; exit 2
fi
echo "mbselite site rebuilt (trigger: $REL) -> specs/_build/html/index.html"
rm -f "$LOG"; exit 0
