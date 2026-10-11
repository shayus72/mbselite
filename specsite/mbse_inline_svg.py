"""Sphinx hook: after the HTML build, inline every diagram SVG into its page.

Why: an inline SVG scales with CSS and keeps its links clickable, and the
page works from file:// as well as from a server (fetch() does not).
Register from conf.py with:  from mbse_inline_svg import setup
"""

import re
from pathlib import Path

_IMG = re.compile(r'<img src="([^"]+\.svg)"[^>]*?/?>', re.S)


def _inline(html_path: Path) -> None:
    text = html_path.read_text(encoding="utf-8")

    def repl(m: re.Match) -> str:
        svg_path = html_path.parent / m.group(1)
        if not svg_path.is_file():
            return m.group(0)
        svg = svg_path.read_text(encoding="utf-8")
        svg = re.sub(r"<\?xml[^>]*\?>", "", svg).strip()
        svg = re.sub(r'\sheight="[^"]*"', "", svg, count=1)
        svg = re.sub(r'\sstyle="[^"]*"', "", svg, count=1)
        svg = re.sub(r'\spreserveAspectRatio="[^"]*"', "", svg, count=1)
        return svg.replace("<svg ", '<svg class="mbse-diagram" preserveAspectRatio="xMidYMid meet" ', 1)

    new = _IMG.sub(repl, text)
    if new != text:
        html_path.write_text(new, encoding="utf-8")


def _on_build_finished(app, exception) -> None:
    if exception or app.builder.name != "html":
        return
    for page in Path(app.outdir).glob("*.html"):
        _inline(page)


def setup(app):
    app.connect("build-finished", _on_build_finished)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
