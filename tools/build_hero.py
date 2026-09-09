#!/usr/bin/env python3
"""Render assets/hero.svg - the profile banner.

Concept: someone has just drag-selected the name, and the cursor that did it is
still sitting on the corner of the marquee. The mascot is the cursor.style logo
character, embedded as a data URI because SVGs on GitHub cannot fetch anything.
"""
import base64, io, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import typeset as T
from PIL import Image, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
PORTRAIT = ROOT / "assets" / "my_photo.png"

W, H = 1000, 290
FLOOR = 340          # the portrait rests here, clear of the spectrum strip
SCALE = 2            # embedded pixels per drawn pixel
NAME = "Oleksii Semeniuk"
# the LinkedIn headline, split where it reads naturally
HEADLINE = ["Senior DevOps Engineer  |  Cloud Platform Architect",
            "Kubernetes  |  Cybersecurity"]
# Two aligned columns under a label, so the list reads as certifications rather
# than as a job title - "Associate" is a exam level, not a seniority.
CREDS = [("AWS DevOps Engineer, Professional", "GitHub Actions Certified"),
         ("Kubernetes & Cloud Native (KCNA)", "Claude with Amazon Bedrock"),
         ("GitOps Certified, Enterprise", "Azure DevOps to GitHub migrations")]
CRED_COLS = (52, 400)
SEL = dict(x=52, y=34, w=620, h=144, r=10)
RIGHT = 948


def portrait(height_px):
    """The photo as a data URI, plus its aspect ratio.

    The source is a wide frame whose blue haze runs opaque to every edge, so a
    plain crop would leave a visible seam. Crop to the subject, fade the new
    edges back out, then quantise: this ends up embedded in the SVG, and the
    banner should not cost more than the page it sits on.
    """
    im = Image.open(PORTRAIT).convert("RGBA").crop((140, 0, 1310, 1086))
    w, h = im.size

    edge = Image.new("L", (w, h), 0)
    ImageDraw.Draw(edge).rectangle((70, 20, w - 70, h - 56), fill=255)
    edge = edge.filter(ImageFilter.GaussianBlur(46))
    alpha = im.split()[3]
    im.putalpha(Image.frombytes("L", (w, h), bytes(
        (a * m) // 255 for a, m in zip(alpha.tobytes(), edge.tobytes()))))
    im = im.crop(im.getbbox())

    ratio = im.width / im.height
    # Full-colour RGBA, no palette: a photograph forced through 256 entries
    # bands on skin, and this is the first thing anyone sees.
    im = im.resize((round(height_px * SCALE * ratio), round(height_px * SCALE)),
                   Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True, compress_level=9)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(), ratio


def build():
    T.reset()
    # Fills the column to the right of the marquee, centred on the banner.
    _, ratio = portrait(1)
    mh = H - 44
    mw = mh * ratio
    uri, _ = portrait(round(mh))
    mx, my = W - 22 - mw, (H - mh) / 2

    creds = T.run("mono", "certifications", 11, SEL["x"], 202, 1.6, cls="sect")
    creds += "".join(
        f'{T.run("mono", c, 12, CRED_COLS[col], 226 + row * 20, 0.2)}'
        for row, pair in enumerate(CREDS) for col, c in enumerate(pair))

    grid = "".join(f'<circle cx="{x}" cy="{y}" r="1.1"/>'
                   for x in range(18, W, 26) for y in range(16, H, 26))
    handles = "".join(
        f'<rect class="handle" x="{px-4}" y="{py-4}" width="8" height="8" rx="1.5"/>'
        for px, py in [(SEL["x"], SEL["y"]), (SEL["x"] + SEL["w"], SEL["y"]),
                       (SEL["x"], SEL["y"] + SEL["h"])])

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
     viewBox="0 0 {W} {H}" role="img"
     aria-label="Oleksii Semeniuk, senior DevOps engineer and cloud platform architect, Kubernetes and cybersecurity, Bradenton Florida">
  <title>Oleksii Semeniuk</title>
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0.35" y2="1">
      <stop offset="0" stop-color="#070C20"/><stop offset="1" stop-color="#0D1338"/>
    </linearGradient>
    <linearGradient id="spectrum" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#38BDF8"/><stop offset="0.38" stop-color="#6366F1"/>
      <stop offset="0.66" stop-color="#A855F7"/><stop offset="1" stop-color="#EC4899"/>
    </linearGradient>
    <radialGradient id="auroraA"><stop offset="0" stop-color="#3B82F6" stop-opacity=".60"/>
      <stop offset="1" stop-color="#3B82F6" stop-opacity="0"/></radialGradient>
    <radialGradient id="auroraB"><stop offset="0" stop-color="#D946EF" stop-opacity=".45"/>
      <stop offset="1" stop-color="#D946EF" stop-opacity="0"/></radialGradient>
    <radialGradient id="auroraC"><stop offset="0" stop-color="#22D3EE" stop-opacity=".32"/>
      <stop offset="1" stop-color="#22D3EE" stop-opacity="0"/></radialGradient>
    <!--GLYPHDEFS-->
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="20"/></clipPath>
  </defs>

  <style>
    .grid   {{ fill:#8AA0E4; opacity:.10 }}
    .name   {{ fill:#EDF2FF }}
    .tag    {{ fill:#9DB2E6 }}
    .creds  {{ fill:#93A6D6 }}
    .sect   {{ fill:#8AD5FB }}
    .rule   {{ stroke:#33427A; stroke-width:1 }}
    .marquee{{ fill:#38BDF8; fill-opacity:.07; stroke:#8AD5FB; stroke-opacity:.75;
               stroke-width:1.6; stroke-dasharray:8 6;
               animation:ants 2.2s linear infinite }}
    .handle {{ fill:#0A0F2A; stroke:#8AD5FB; stroke-opacity:.9; stroke-width:1.5 }}
    .drift  {{ animation:drift 11s ease-in-out infinite }}
    .drift2 {{ animation:drift 15s ease-in-out infinite reverse }}
    .cursor {{ animation:hover 4.6s ease-in-out infinite;
               transform-box:fill-box; transform-origin:center }}
    @keyframes ants  {{ to {{ stroke-dashoffset:-28 }} }}
    @keyframes drift {{ 0%,100% {{ opacity:.7 }} 50% {{ opacity:1 }} }}
    @keyframes hover {{ 0%,100% {{ transform:translateY(0) }}
                        50%     {{ transform:translateY(-5px) }} }}
    @media (prefers-reduced-motion:reduce) {{
      .marquee,.drift,.drift2,.cursor {{ animation:none }}
    }}
  </style>

  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#sky)"/>
    <ellipse class="drift"  cx="820" cy="30"  rx="400" ry="230" fill="url(#auroraA)"/>
    <ellipse class="drift2" cx="990" cy="280" rx="300" ry="190" fill="url(#auroraB)"/>
    <ellipse class="drift2" cx="70"  cy="300" rx="280" ry="170" fill="url(#auroraC)"/>
    <g class="grid">{grid}</g>
    <rect x="0" y="{H-4}" width="{W}" height="4" fill="url(#spectrum)"/>
  </g>

  <rect class="marquee" x="{SEL['x']}" y="{SEL['y']}" width="{SEL['w']}"
        height="{SEL['h']}" rx="{SEL['r']}"/>
  {handles}

  {T.run('display', NAME, 54, SEL['x'] + 32, 100, cls="name")}
  <g class="tag">
    {T.run('mono', HEADLINE[0], 13, SEL['x'] + 34, 140, 0.2)}
    {T.run('mono', HEADLINE[1], 13, SEL['x'] + 34, 164, 0.2)}
  </g>

  <g class="creds">{creds}</g>

  <g class="cursor"><image href="{uri}" x="{mx:.1f}" y="{my:.1f}"
       width="{mw:.1f}" height="{mh}"/></g>
</svg>
'''
    return svg.replace("<!--GLYPHDEFS-->", T.defs())


if __name__ == "__main__":
    out = ROOT / "assets" / "hero.svg"
    out.write_text(build(), encoding="utf-8")
    print(f"{out.relative_to(ROOT)} - {out.stat().st_size / 1024:.0f} KB")
