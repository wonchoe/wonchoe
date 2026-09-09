#!/usr/bin/env python3
"""Render the credential badges that have no official artwork to show.

Drawn as one consistent set in this page's own language rather than as
look-alikes of an issuer's badge: the credentials are real, but a badge the
issuer never published would misrepresent them. Sized and shaped to sit in the
same grid as the official ones.
"""
import pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import typeset as T

ROOT = pathlib.Path(__file__).resolve().parent.parent
S = 400
HEX = "200,14 370,112 370,288 200,386 30,288 30,112"
HEX_IN = "200,34 353,122 353,278 200,366 47,278 47,122"

BADGES = [
    ("badge-claude-bedrock", "Anthropic", "CLAUDE", "BEDROCK", "2026", "#FFC23C"),
    ("badge-copilot", "GitHub", "COPILOT", "CORE SKILLS", "2026", "#A855F7"),
    ("badge-gh-migrations", "GitHub", "MIGRATIONS", "TO GITHUB", "2025", "#38BDF8"),
]


def fit(role, text, ideal, limit, tracking=0.0):
    """Largest size at or below `ideal` that keeps `text` inside `limit`."""
    size = ideal
    while size > 8 and T.width(role, text, size, tracking) > limit:
        size -= 0.5
    return size


def build(issuer, line1, line2, year, accent):
    T.reset()
    body = (
        T.run("mono", issuer.upper(), 21, S / 2, 118, 3.2, anchor="middle", cls="issuer")
        + T.run("display", line1, fit("display", line1, 46, 236), S / 2, 186,
                anchor="middle", cls="main")
        + T.run("display", line2, fit("display", line2, 27, 236), S / 2, 224,
                anchor="middle", cls="second")
        + T.run("mono", year, 22, S / 2, 300, 2.0, anchor="middle", cls="year")
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{S}" height="{S}"
     viewBox="0 0 {S} {S}" role="img"
     aria-label="{issuer} credential: {line1} {line2}, {year}">
  <title>{issuer} - {line1} {line2}</title>
  <defs>
    <linearGradient id="face" x1="0" y1="0" x2="0.4" y2="1">
      <stop offset="0" stop-color="#111A44"/><stop offset="1" stop-color="#070C20"/>
    </linearGradient>
    {T.defs()}
  </defs>
  <style>
    .plate  {{ fill:url(#face); stroke:{accent}; stroke-width:6 }}
    .inner  {{ fill:none; stroke:{accent}; stroke-opacity:.45; stroke-width:2 }}
    .issuer {{ fill:{accent} }}
    .main   {{ fill:#EDF2FF }}
    .second {{ fill:#9DB2E6 }}
    .year   {{ fill:{accent}; fill-opacity:.9 }}
    .rule   {{ stroke:{accent}; stroke-opacity:.5; stroke-width:2 }}
  </style>
  <polygon class="plate" points="{HEX}"/>
  <polygon class="inner" points="{HEX_IN}"/>
  <path class="rule" d="M132 138H268"/>
  <path class="rule" d="M148 262H252"/>
  {body}
</svg>
'''


if __name__ == "__main__":
    for name, issuer, l1, l2, year, accent in BADGES:
        out = ROOT / "assets" / f"{name}.svg"
        out.write_text(build(issuer, l1, l2, year, accent), encoding="utf-8")
        print(f"{out.relative_to(ROOT)} - {out.stat().st_size / 1024:.0f} KB")
