"""Sphinx hook: after the HTML build, inline every diagram SVG into its page.

Why: an inline SVG scales with CSS and keeps its links clickable, and the
page works from file:// as well as from a server (fetch() does not).
Register from conf.py with:  from mbselite.inline_svg import setup
"""

import os
import re
from pathlib import Path

_IMG = re.compile(r'<img src="([^"]+\.svg)"[^>]*?/?>', re.S)
_HREF = re.compile(r'((?:xlink:)?href)="([^"]+)"')


def _rebase_links(svg: str, svg_dir: Path, page_dir: Path) -> str:
    """Relative links in the SVG were written for its own folder (_images/);
    once inlined they resolve against the page's folder, so re-base them."""

    def fix(m: re.Match) -> str:
        attr, target = m.group(1), m.group(2)
        if re.match(r"^(#|[a-zA-Z][a-zA-Z0-9+.-]*:|/)", target):  # fragment, URL scheme, root path
            return m.group(0)
        path, sep, frag = target.partition("#")
        rel = os.path.relpath(os.path.normpath(svg_dir / path), page_dir).replace(os.sep, "/")
        return f'{attr}="{rel}{sep}{frag}"'

    return _HREF.sub(fix, svg)


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
        svg = _rebase_links(svg, svg_path.parent, html_path.parent)
        return svg.replace("<svg ", '<svg class="mbselite-diagram" preserveAspectRatio="xMidYMid meet" ', 1)

    new = _IMG.sub(repl, text)
    if new != text:
        html_path.write_text(new, encoding="utf-8")


def _on_build_finished(app, exception) -> None:
    if exception or app.builder.name != "html":
        return
    for page in Path(app.outdir).rglob("*.html"):  # pages may live in sub-folders
        _inline(page)


def setup(app):
    app.connect("build-finished", _on_build_finished)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
