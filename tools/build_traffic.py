#!/usr/bin/env python3
"""Render assets/traffic.svg from assets/traffic.json.

update_readme.mjs writes the JSON straight from the Cloudflare GraphQL response;
this turns it into the card the README shows. Run daily by the stats workflow.
"""
import datetime as dt, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import typeset as T

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "assets" / "traffic.json"
OUT = ROOT / "assets" / "traffic.svg"

W, H = 1000, 320
PAD = 52
CHART = dict(top=104, base=196, left=PAD, right=W - PAD)  # top row is the peak-label lane
COLS = (566, 754, 928)          # right edge of each figure column


def fmt(n):
    return f"{int(n):,}"


def bars(days):
    if not days:
        return ('<path class="rule" stroke-dasharray="5 5" '
                f'd="M{CHART["left"]} {CHART["base"]}H{CHART["right"]}"/>'
                f'{T.run("mono", "the daily series fills in on the next sync", 12, W/2, CHART["base"] - 26, 0.2, anchor="middle", cls="hint")}')

    span = CHART["right"] - CHART["left"]
    gap = 5
    bw = (span - gap * (len(days) - 1)) / len(days)
    peak = max(range(len(days)), key=lambda i: days[i]["requests"])
    top = max(d["requests"] for d in days) or 1
    height = CHART["base"] - CHART["top"]

    out = []
    for i, d in enumerate(days):
        h = max(2.0, d["requests"] / top * height)
        x = CHART["left"] + i * (bw + gap)
        out.append(f'<rect class="bar" x="{x:.1f}" y="{CHART["base"]-h:.1f}" '
                   f'width="{bw:.1f}" height="{h:.1f}" rx="2" '
                   f'style="animation-delay:{i*22}ms"/>')

    # call out the busiest day rather than leaving the reader to eyeball it
    px = CHART["left"] + peak * (bw + gap) + bw / 2
    ph = CHART["base"] - max(2.0, days[peak]["requests"] / top * height)
    label = f'busiest day  {fmt(days[peak]["requests"])}'
    lx = min(max(px, CHART["left"] + T.width("mono", label, 11.5, 0.2) / 2),
             CHART["right"] - T.width("mono", label, 11.5, 0.2) / 2)
    out.append(f'<circle class="peak" cx="{px:.1f}" cy="{ph:.1f}" r="3.4"/>')
    out.append(f'<path class="peakline" d="M{px:.1f} {ph-8:.1f}V{CHART["top"]-14:.0f}"/>')
    out.append(f'{T.run("mono", label, 11.5, lx, CHART["top"]-20, 0.2, anchor="middle", cls="peaktxt")}')
    return "".join(out)


def axis(days):
    if not days or not days[0].get("date"):
        return ""
    left = dt.date.fromisoformat(days[0]["date"]).strftime("%b %-d")
    right = dt.date.fromisoformat(days[-1]["date"]).strftime("%b %-d")
    return (f'{T.run("mono", left, 11, CHART["left"], 218, 0.2)}'
            f'{T.run("mono", right, 11, CHART["right"], 218, 0.2, anchor="end")}')


def row(label, stat, y, cls):
    cells = [f'{T.run("mono", label, 13.5, PAD, y, 0.2)}']
    for x, key in zip(COLS, ("requests", "pageViews", "uniques")):
        cells.append(f'{T.run("mono", fmt(stat[key]), 13.5, x, y, 0.2, anchor="end")}')
    return f'<g class="{cls}">{"".join(cells)}</g>'


def build(data):
    T.reset()
    days = data.get("days") or []
    heads = "".join(
        f'{T.run("mono", h, 10.5, x, 250, 0.6, anchor="end")}'
        for x, h in zip(COLS, ("requests", "page views", "people")))

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
     viewBox="0 0 {W} {H}" role="img"
     aria-label="cursor.style edge traffic, {fmt(data["last30d"]["requests"])} requests over 30 days">
  <title>cursor.style traffic</title>
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0.3" y2="1">
      <stop offset="0" stop-color="#070C20"/><stop offset="1" stop-color="#0C1132"/>
    </linearGradient>
    <linearGradient id="spectrum" gradientUnits="userSpaceOnUse"
        x1="{CHART['left']}" y1="0" x2="{CHART['right']}" y2="0">
      <stop offset="0" stop-color="#38BDF8"/><stop offset="0.38" stop-color="#6366F1"/>
      <stop offset="0.66" stop-color="#A855F7"/><stop offset="1" stop-color="#EC4899"/>
    </linearGradient>
    <radialGradient id="glow"><stop offset="0" stop-color="#4F46E5" stop-opacity=".40"/>
      <stop offset="1" stop-color="#4F46E5" stop-opacity="0"/></radialGradient>
    <!--GLYPHDEFS-->
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="20"/></clipPath>
  </defs>

  <style>
    .head    {{ fill:#EDF2FF }}
    .sub     {{ fill:#8496C8 }}
    .rule    {{ stroke:#2B3768; stroke-width:1 }}
    .hint    {{ fill:#6B7CB0 }}
    .bar     {{ fill:url(#spectrum); transform-box:fill-box; transform-origin:bottom;
                animation:rise .7s cubic-bezier(.22,.9,.3,1) both }}
    .peak    {{ fill:#FFC23C }}
    .peakline{{ stroke:#FFC23C; stroke-width:1; stroke-opacity:.55 }}
    .peaktxt {{ fill:#FFC23C }}
    .colhead {{ fill:#67789F }}
    .r24     {{ fill:#9DB2E6 }}
    .r30     {{ fill:#EDF2FF }}
    .axis    {{ fill:#67789F }}
    @keyframes rise {{ from {{ transform:scaleY(0) }} to {{ transform:scaleY(1) }} }}
    @media (prefers-reduced-motion:reduce) {{ .bar {{ animation:none }} }}
  </style>

  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#sky)"/>
    <ellipse cx="500" cy="150" rx="520" ry="220" fill="url(#glow)"/>
    <rect x="0" y="{H-4}" width="{W}" height="4" fill="url(#spectrum)"/>
  </g>

  {T.run("display", "cursor.style at the edge", 25, PAD, 52, cls="head")}
  <path class="sub"  d="{T.path("mono", "Cloudflare, updated " + data["updated"], 11.5, W - PAD, 50, 0.2, anchor="end")}"/>

  {bars(days)}
  <path class="rule" d="M{CHART['left']} {CHART['base']}H{CHART['right']}"/>
  <g class="axis">{axis(days)}</g>

  <path class="rule" d="M{PAD} 230H{W-PAD}" opacity=".7"/>
  <g class="colhead">{heads}</g>
  {row("last 24 hours", data["last24h"], 276, "r24")}
  {row("last 30 days", data["last30d"], 300, "r30")}
</svg>
'''
    return svg.replace("<!--GLYPHDEFS-->", T.defs())


if __name__ == "__main__":
    data = json.loads(DATA.read_text(encoding="utf-8"))
    OUT.write_text(build(data), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)} - {OUT.stat().st_size / 1024:.0f} KB")
