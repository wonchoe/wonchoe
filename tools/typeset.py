"""Turn strings into SVG <path> outlines.

GitHub serves README images with `default-src 'none'` - an SVG can never pull a
web font down, and every machine has a different set of installed fonts. Baking
the display type into outlines is the only way the banner looks the same for
everyone. Fonts here are ASCII-only subsets; see tools/fonts/OFL-*.txt.
"""
import pathlib

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONT_DIR = pathlib.Path(__file__).resolve().parent / "fonts"
FILES = {
    "display": "Baloo2-ExtraBold.ttf",   # the name, headline figures
    "text": "Baloo2-Medium.ttf",         # prose
    "mono": "JetBrainsMono-Bold.ttf",    # anything a machine produced
}
_cache = {}
_glyphs = {}          # (role, glyph name) -> id
_outlines = []        # [(id, path data)] in first-seen order


def _font(role):
    if role not in _cache:
        f = TTFont(FONT_DIR / FILES[role])
        _cache[role] = (f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm)
    return _cache[role]


def width(role, string, size, tracking=0.0):
    gs, cmap, upm = _font(role)
    adv = sum(gs[cmap[ord(c)]].width if ord(c) in cmap else upm * 0.5 for c in string)
    return adv * size / upm + tracking * max(0, len(string) - 1)


def _num(v):
    """Shortest form that still lands on the right pixel at these sizes."""
    r = round(v, 1)
    return str(int(r)) if r == int(r) else f"{r:.1f}"


def path(role, string, size, x, y, tracking=0.0, anchor="start"):
    """A single path for `string`, baseline at (x, y). anchor: start|middle|end."""
    gs, cmap, upm = _font(role)
    scale = size / upm
    if anchor != "start":
        w = width(role, string, size, tracking)
        x -= w if anchor == "end" else w / 2
    pen = SVGPathPen(gs, ntos=_num)
    cursor = 0.0
    for ch in string:
        name = cmap.get(ord(ch))
        if name is None:
            cursor += upm * 0.5
            continue
        gs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x + cursor * scale, y)))
        cursor += gs[name].width + tracking / scale
    return pen.getCommands()


# --- glyph reuse -----------------------------------------------------------
# A page carrying six of these cards was 664 KB of repeated outline data. Each
# distinct glyph is now described once and referenced afterwards, which is what
# a font would do if GitHub let one load.

def reset():
    """Start a new document. Call before building, so defs() holds only its own."""
    _glyphs.clear()
    _outlines.clear()


def defs():
    """The <path> definitions every run() so far points at."""
    return "".join(f'<path id="{i}" d="{d}"/>' for i, d in _outlines)


def _glyph(role, name):
    key = (role, name)
    if key not in _glyphs:
        gs, _, _ = _font(role)
        pen = SVGPathPen(gs, ntos=_num)
        gs[name].draw(pen)
        data = pen.getCommands()
        gid = f"{role[0]}{len(_glyphs)}" if data else ""   # blanks need no node
        _glyphs[key] = gid
        if gid:
            _outlines.append((gid, data))
    return _glyphs[key]


def run(role, string, size, x, y, tracking=0.0, anchor="start", cls=None):
    """A <g> of <use> references, baseline at (x, y)."""
    gs, cmap, upm = _font(role)
    scale = size / upm
    if anchor != "start":
        w = width(role, string, size, tracking)
        x -= w if anchor == "end" else w / 2

    uses, cursor = [], 0.0
    for ch in string:
        name = cmap.get(ord(ch))
        if name is None:
            cursor += upm * 0.5
            continue
        gid = _glyph(role, name)
        if gid:
            uses.append(f'<use href="#{gid}" x="{_num(cursor)}"/>')
        cursor += gs[name].width + tracking / scale

    attr = f' class="{cls}"' if cls else ""
    return (f'<g{attr} transform="translate({_num(x)},{_num(y)}) '
            f'scale({scale:.5f},{-scale:.5f})">{"".join(uses)}</g>')
