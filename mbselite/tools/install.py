#!/usr/bin/env python3
"""Install (or update) the mbselite kit into a project.

    python3 <kit>/mbselite/tools/install.py [PROJECT] [--kicad] [--no-hooks] [--dry-run]

PROJECT defaults to the current directory. It copies, overwriting older copies:
  mbselite/ (metamodel, inliner, viewer, GUIDE.md, tools/), build.py, build.sh,
  build.cmd, requirements.txt
and only if missing:
  specs/conf.py (project name set to the folder name), specs/index.md
  (lists `generated-index` when the project has openspec/).
Then merges the Claude Code hooks from claude-hooks.json into
PROJECT/.claude/settings.json: the PostToolUse rebuild hook always, the
SessionStart KiCad hint only with --kicad. Other settings and hooks are kept;
an existing mbselite hook (same script name, any path) is updated in place, so
re-running is safe. Hooks added mid-session fire after `/hooks` or a restart.
"""
from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
KIT = TOOLS.parents[1]
KIT_FILES = ["build.py", "build.sh", "build.cmd", "requirements.txt"]
INDEX_TEMPLATE = """# Specs

Each spec is a Markdown file with typed blocks. Diagrams and tables on these
pages are generated from the blocks and link back to them. How to write one:
`mbselite/GUIDE.md`.
{openspec_note}
```{{toctree}}
:maxdepth: 3
{entries}
```
"""
OPENSPEC_NOTE = """
Pages under each change folder are generated from `openspec/` by
`mbselite/tools/openspec2mbselite.py` (run by a Claude Code hook on every spec
edit); never edit them. Hand-written model content goes in `<page>.model.md`.
"""


def script_name(cmd: str) -> str:
    return cmd.replace('"', "").rsplit("/", 1)[-1]


def merge_hooks(settings: dict, block: dict) -> list[str]:
    """Add each event's groups from `block` to settings["hooks"]; return what changed."""
    log: list[str] = []
    hooks = settings.setdefault("hooks", {})
    for event, groups in block.items():
        existing = hooks.setdefault(event, [])
        for group in groups:
            for new in group["hooks"]:
                name = script_name(new["command"])
                found = next(((g, h) for g in existing for h in g.get("hooks", [])
                              if h.get("type") == "command" and script_name(h.get("command", "")) == name), None)
                if found is None:
                    existing.append(copy.deepcopy(group))
                    log.append(f"added {event} hook {name}")
                    continue
                owner, old = found
                if owner.get("matcher") != group.get("matcher") and len(owner["hooks"]) > 1:
                    owner["hooks"].remove(old)       # shared group: never change other hooks' matcher
                    existing.append(copy.deepcopy(group))
                    log.append(f"moved {event} hook {name} to its own matcher group")
                elif old != new or owner.get("matcher") != group.get("matcher"):
                    old.clear()
                    old.update(new)
                    if "matcher" in group:
                        owner["matcher"] = group["matcher"]
                    log.append(f"updated {event} hook {name}")
    return log


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", nargs="?", type=Path, default=Path.cwd())
    ap.add_argument("--kicad", action="store_true", help="also install the SessionStart KiCad hint (hardware projects)")
    ap.add_argument("--no-hooks", action="store_true", help="copy the kit only, leave .claude/settings.json alone")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    proj = a.project.resolve()
    if proj == KIT:
        sys.exit("install.py: PROJECT is the kit itself; pass the project folder")
    if not proj.is_dir():
        sys.exit(f"install.py: no such folder {proj}")
    do = not a.dry_run
    say = (lambda m: print(("[dry-run] " if a.dry_run else "") + m))

    # 1. kit files (always refreshed: projects never edit them)
    say(f"copy mbselite/ -> {proj / 'mbselite'}")
    if do:
        shutil.copytree(KIT / "mbselite", proj / "mbselite", dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for s in TOOLS.glob("*.sh"):
            (proj / "mbselite" / "tools" / s.name).chmod(0o755)
    for f in KIT_FILES:
        say(f"copy {f}")
        if do:
            shutil.copy2(KIT / f, proj / f)

    # 2. project files (only when missing)
    specs = proj / "specs"
    has_os = (proj / "openspec").is_dir()
    conf = specs / "conf.py"
    if not conf.exists():
        say("create specs/conf.py")
        if do:
            specs.mkdir(exist_ok=True)
            conf.write_text((KIT / "specs" / "conf.py").read_text(encoding="utf-8")
                            .replace('"my-project"', json.dumps(proj.name))
                            .replace('"my-project specs"', json.dumps(f"{proj.name} specs")), encoding="utf-8")
    index = specs / "index.md"
    if not index.exists():
        say("create specs/index.md")
        if do:
            index.write_text(INDEX_TEMPLATE.format(openspec_note=OPENSPEC_NOTE if has_os else "",
                                                   entries="\ngenerated-index" if has_os else ""), encoding="utf-8")

    # 3. hooks
    if not a.no_hooks:
        block = json.loads((TOOLS / "claude-hooks.json").read_text(encoding="utf-8"))
        if not a.kicad:
            block.pop("SessionStart", None)
        path = proj / ".claude" / "settings.json"
        try:
            settings = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except json.JSONDecodeError as e:
            sys.exit(f"install.py: {path} is not valid JSON ({e}); fix it or use --no-hooks")
        log = merge_hooks(settings, block)
        for m in log:
            say(m + " in .claude/settings.json")
        if log and do:
            path.parent.mkdir(exist_ok=True)
            path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if log:
            print("note: a running Claude Code session picks up new hooks after /hooks or a restart")

    # Existing project files are never rewritten; say what they still need.
    if conf.exists() and "*.model.md" not in conf.read_text(encoding="utf-8"):
        print('todo: add "**/*.model.md" to exclude_patterns in specs/conf.py (model fragments are included, not built)')
    if has_os and index.exists() and "generated-index" not in index.read_text(encoding="utf-8"):
        print("todo: list generated-index in the toctree of specs/index.md (the OpenSpec pages hang off it)")

    print("next (from the project root, Python 3.11+): "
          + ("python3 mbselite/tools/openspec2mbselite.py && " if has_os else "")
          + "python3 build.py --no-open")
    return 0


if __name__ == "__main__":
    sys.exit(main())
