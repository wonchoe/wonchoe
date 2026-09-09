#!/usr/bin/env python3
"""Render assets/chat.svg from assets/chat.json.

The numbers come from a read-only endpoint on cursor.style, called by the daily
workflow with a token held in GitHub secrets. Shape:

    { "updated": "2026-09-09",
      "note": "optional line under the figures",
      "metrics": [ {"label": "messages", "value": "1,204,551"}, ... ],
      "today":   [ {"label": "messages", "value": "8,410"}, ... ] }

Whatever the endpoint publishes is what gets drawn, so the decision about what
is fit to publish stays in one place - see ProfileStatsController.
"""
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import typeset as T

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "assets" / "chat.json"
OUT = ROOT / "assets" / "chat.svg"

W = 1000
PAD = 52


def group(items, y, per_row, value_size, label_size, gap):
    """Rows of centred figures. Returns (svg, the y the group ends at).

    The end is the bottom of the last label, not the last value baseline: the
    caller places the next thing against it, and returning the baseline once put
    the footnote straight through the labels.
    """
    out = []
    rows = [items[i:i + per_row] for i in range(0, len(items), per_row)]
    label_drop = label_size + 7
    for row in rows:
        span = (W - 2 * PAD) / len(row)
        for i, m in enumerate(row):
            mid = PAD + span * (i + 0.5)
            out.append(T.run("display", str(m["value"]), value_size, mid, y,
                             anchor="middle", cls="fig"))
            out.append(T.run("mono", str(m["label"]), label_size, mid, y + label_drop,
                             0.3, anchor="middle", cls="figlab"))
        y += gap
    return "".join(out), y - gap + label_drop


def build(d):
    T.reset()
    metrics = d.get("metrics") or []
    today = d.get("today") or []
    body, y = [], 0

    if not metrics and not today:
        body.append(T.run("mono", "figures arrive with the first sync from cursor.style",
                          12, W / 2, 128, 0.2, anchor="middle", cls="hint"))
        y = 170
    else:
        y = 96
        if metrics:
            body.append(T.run("mono", "all time", 11, PAD, y, 1.6, cls="sect"))
            chunk, y = group(metrics, y + 44, 3, 32, 11.5, 76)
            body.append(chunk)
            y += 28
        if today:
            body.append(f'<path class="rule" d="M{PAD} {y}H{W - PAD}"/>')
            y += 30
            body.append(T.run("mono", "today so far", 11, PAD, y, 1.6, cls="sect"))
            chunk, y = group(today, y + 40, 4, 24, 10.5, 62)
            body.append(chunk)
        y += 30

    if d.get("note"):
        body.append(T.run("mono", d["note"], 11, W / 2, y, 0.2, anchor="middle", cls="note"))
        y += 26

    H = int(y + 18)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
     viewBox="0 0 {W} {H}" role="img" aria-label="the cursor.style chat in numbers">
  <title>The cursor.style chat</title>
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0.3" y2="1">
      <stop offset="0" stop-color="#070C20"/><stop offset="1" stop-color="#0C1132"/>
    </linearGradient>
    <linearGradient id="spectrum" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#38BDF8"/><stop offset="0.38" stop-color="#6366F1"/>
      <stop offset="0.66" stop-color="#A855F7"/><stop offset="1" stop-color="#EC4899"/>
    </linearGradient>
    <radialGradient id="glow"><stop offset="0" stop-color="#7C3AED" stop-opacity=".35"/>
      <stop offset="1" stop-color="#7C3AED" stop-opacity="0"/></radialGradient>
    <!--GLYPHDEFS-->
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="20"/></clipPath>
  </defs>

  <style>
    .head   {{ fill:#EDF2FF }}
    .sub    {{ fill:#8496C8 }}
    .sect   {{ fill:#8AD5FB }}
    .fig    {{ fill:#EDF2FF }}
    .figlab {{ fill:#8496C8 }}
    .note   {{ fill:#7184B8 }}
    .hint   {{ fill:#6B7CB0 }}
    .rule   {{ stroke:#2B3768; stroke-width:1 }}
  </style>

  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#sky)"/>
    <ellipse cx="500" cy="{H // 2}" rx="540" ry="{int(H * 0.7)}" fill="url(#glow)"/>
    <rect x="0" y="{H - 4}" width="{W}" height="4" fill="url(#spectrum)"/>
  </g>

  {T.run("display", "the chat, in numbers", 25, PAD, 52, cls="head")}
  {T.run("mono", "updated " + d.get("updated", "-"), 11.5, W - PAD, 50, 0.2, anchor="end", cls="sub")}
  <path class="rule" d="M{PAD} 70H{W - PAD}"/>

  {"".join(body)}
</svg>
'''
    return svg.replace("<!--GLYPHDEFS-->", T.defs())


if __name__ == "__main__":
    data = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else {}
    OUT.write_text(build(data), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)} - {OUT.stat().st_size / 1024:.0f} KB")
