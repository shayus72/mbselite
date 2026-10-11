#!/usr/bin/env python3
"""Build the spec site on Windows, Linux or macOS and open it.

    python build.py            build and open
    python build.py --no-open  build only
Creates .venv next to this file on first run.
"""
import os, subprocess, sys, venv, webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

if not PY.exists():
    print("creating .venv ...")
    venv.create(VENV, with_pip=True)
    subprocess.check_call([str(PY), "-m", "pip", "install", "-q", "-r", str(ROOT / "requirements.txt")])

out = ROOT / "specs" / "_build" / "html"
rc = subprocess.call([str(PY), "-m", "sphinx", "-b", "html", str(ROOT / "specs"), str(out)]
                     + [a for a in sys.argv[1:] if a != "--no-open"])
if rc == 0 and "--no-open" not in sys.argv:
    webbrowser.open((out / "index.html").as_uri())
sys.exit(rc)
