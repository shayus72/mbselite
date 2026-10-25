#!/usr/bin/env python3
"""Build the spec site on Windows, Linux or macOS and open it.

    python build.py            build and open
    python build.py --no-open  build only
Other arguments go to sphinx-build (e.g. -q, -a -E). Run from anywhere; paths
are relative to this file, which sits at the project root next to specs/.
Creates .venv next to this file on first run. Needs Python 3.11+ (sphinx 9).
"""
import os, subprocess, sys, venv, webbrowser
from pathlib import Path

if sys.version_info < (3, 11):
    sys.exit("mbselite needs Python 3.11+ (sphinx 9); run with python3.11 or newer")

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

if not PY.exists():
    print("creating .venv ...")
    venv.create(VENV, with_pip=True)
    subprocess.check_call([str(PY), "-m", "pip", "install", "-q", "-r", str(ROOT / "requirements.txt")])

out = ROOT / "specs" / "_build" / "html"
args = [a for a in sys.argv[1:] if a != "--no-open"]
# Sphinx only rewrites pages whose sources changed, so a newer kit (inliner,
# metamodel, viewer) would not reach old pages: rebuild everything then.
stamp = out / "index.html"
kit = list((ROOT / "mbselite").glob("*.py")) + list((ROOT / "mbselite" / "static").glob("*"))
if stamp.is_file() and any(p.stat().st_mtime > stamp.stat().st_mtime for p in kit):
    args += [a for a in ("-a", "-E") if a not in args]
rc = subprocess.call([str(PY), "-m", "sphinx", "-b", "html", str(ROOT / "specs"), str(out)] + args)
if rc == 0 and "--no-open" not in sys.argv:
    webbrowser.open((out / "index.html").as_uri())
sys.exit(rc)
