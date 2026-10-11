"""Project conf: only what differs per project. The tool lives in ../mbselite."""

import os
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root))
from mbselite import *  # noqa: F401,F403  metamodel, templates, styles
from mbselite.inline_svg import setup  # noqa: F401  inline diagrams into pages

project = "my-project"
html_title = "my-project specs"
extensions = ["myst_parser", "sphinx_needs", "sphinxcontrib.plantuml"]
source_suffix = {".md": "markdown"}
exclude_patterns = ["_build"]
html_theme = "furo"
html_static_path = [str(_root / "mbselite" / "static")]
html_css_files = ["mbselite.css"]
html_js_files = ["mbselite.js"]

# Renderers. Portable copies may live in ../tools (Graphviz and plantuml.jar);
# otherwise `dot` and `plantuml` are taken from PATH. Java is needed for the
# jar. On Linux: apt install graphviz plantuml default-jre
_tools = _root / "tools"
_dot = next((p for p in (_tools / "graphviz" / "bin" / "dot.exe", _tools / "graphviz" / "bin" / "dot") if p.is_file()), None)
_jar = _tools / "plantuml.jar"
if _dot:
    os.environ["GRAPHVIZ_DOT"] = str(_dot)
plantuml = f'java -jar "{_jar}"' if _jar.is_file() else "plantuml"
plantuml_output_format = "svg_img"
