"""Project conf: only what differs per project. The vocabulary is generic."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mbse_vocab import *  # noqa: F401,F403

project = "my-project"
html_title = "my-project specs"
extensions = ["myst_parser", "sphinx_needs", "sphinxcontrib.plantuml"]
source_suffix = {".md": "markdown"}
exclude_patterns = ["_build", "README.md"]
html_theme = "furo"

# Renderers. Portable copies may live in ../tools (Graphviz and plantuml.jar);
# otherwise `dot` and `plantuml` are taken from PATH. Java is needed for the
# jar. On Linux: apt install graphviz plantuml default-jre
_tools = Path(__file__).resolve().parent.parent / "tools"
_dot = next((p for p in (_tools / "graphviz" / "bin" / "dot.exe", _tools / "graphviz" / "bin" / "dot") if p.is_file()), None)
_jar = _tools / "plantuml.jar"
if _dot:
    os.environ["GRAPHVIZ_DOT"] = str(_dot)
plantuml = f'java -jar "{_jar}"' if _jar.is_file() else "plantuml"
plantuml_output_format = "svg_img"

html_static_path = ["_static"]
html_css_files = ["mbse.css"]
html_js_files = ["mbse.js"]
from mbse_inline_svg import setup  # noqa: E402,F401  inline diagrams into pages
