#!/usr/bin/env python3
"""Render assets/architecture.svg - what sits between a click and a byte.

Hand-placed rather than left to a layout engine. The cluster is the middle of
the picture because that is what the picture is about: traffic comes down into
it, delivery and configuration push in from the sides, state hangs underneath,
and Grafana watches. Stacked bands said the same thing but read as a table.
"""
import pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import typeset as T

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "architecture.svg"

W, H = 1000, 620
INK = "#3C4A82"

# --- geometry ---------------------------------------------------------------
USERS = dict(x=340, y=30, w=320, h=48)
CLOUD = dict(x=270, y=104, w=460, h=150)
K3S = dict(x=270, y=286, w=460, h=150)
DELIV = dict(x=34, y=286, w=206, h=150)
CONF = dict(x=760, y=286, w=206, h=150)
STATE = dict(x=120, y=470, w=600, h=104)
WATCH = dict(x=760, y=496, w=206, h=52)


def box(g, label, cls, chips, cols=2):
    """A titled group with chips laid out inside it."""
    out = [f'<rect class="grp {cls}" x="{g["x"]}" y="{g["y"]}" width="{g["w"]}" '
           f'height="{g["h"]}" rx="12"/>',
           T.run("mono", label, 11, g["x"] + 15, g["y"] + 19, 0.7, cls="grplabel")]
    pad, gap = 15, 9
    rows = [chips[i:i + cols] for i in range(0, len(chips), cols)]
    cw = (g["w"] - 2 * pad - gap * (cols - 1)) / cols
    ch = (g["h"] - 26 - pad - gap * (len(rows) - 1)) / len(rows)
    for r, row in enumerate(rows):
        for c, (name, sub) in enumerate(row):
            x = g["x"] + pad + c * (cw + gap)
            y = g["y"] + 26 + r * (ch + gap)
            mid = x + cw / 2
            out.append(f'<rect class="chip {cls}" x="{x:.1f}" y="{y:.1f}" '
                       f'width="{cw:.1f}" height="{ch:.1f}" rx="8"/>')
            out.append(T.run("mono", name, 12.5, mid, y + ch / 2 - 2, 0.2,
                             anchor="middle", cls="cname"))
            out.append(T.run("mono", sub, 10, mid, y + ch / 2 + 13, 0.2,
                             anchor="middle", cls="csub"))
    return "".join(out)


def arrow(x1, y1, x2, y2):
    """Straight connector with a head at the far end."""
    if x1 == x2:
        d = 1 if y2 > y1 else -1
        head = f'M{x2 - 5} {y2 - 8 * d}L{x2} {y2}L{x2 + 5} {y2 - 8 * d}Z'
    else:
        d = 1 if x2 > x1 else -1
        head = f'M{x2 - 8 * d} {y2 - 5}L{x2} {y2}L{x2 - 8 * d} {y2 + 5}Z'
    return (f'<path class="flow" d="M{x1} {y1}L{x2 - (0 if x1 == x2 else 6 * d)} '
            f'{y2 - (6 * d if x1 == x2 else 0)}"/><path class="head" d="{head}"/>')


def elbow(x1, y1, x2, y2, at):
    """Right-angled connector: across to `at`, down, then in."""
    return (f'<path class="flow" d="M{x1} {y1}H{at}V{y2}H{x2 - 6}"/>'
            f'<path class="head" d="M{x2 - 8} {y2 - 5}L{x2} {y2}L{x2 - 8} {y2 + 5}Z"/>')


def build():
    T.reset()
    parts = [
        f'<rect class="chip edge" x="{USERS["x"]}" y="{USERS["y"]}" '
        f'width="{USERS["w"]}" height="{USERS["h"]}" rx="10"/>',
        T.run("mono", "browsers, extensions, mobile web", 12.5,
              USERS["x"] + USERS["w"] / 2, USERS["y"] + 21, 0.2, anchor="middle", cls="cname"),
        T.run("mono", "five public brands", 10,
              USERS["x"] + USERS["w"] / 2, USERS["y"] + 36, 0.2, anchor="middle", cls="csub"),

        arrow(500, USERS["y"] + USERS["h"], 500, CLOUD["y"]),
        box(CLOUD, "Cloudflare", "edge", [
            ("WAF and CDN", "cache, rate limiting"),
            ("Redirect rules", "locale and host routing"),
            ("Zero Trust", "admin and ops access"),
            ("Realtime", "TURN relays, SFU rooms"),
        ]),

        arrow(500, CLOUD["y"] + CLOUD["h"], 500, K3S["y"]),
        box(K3S, "k3s cluster", "k8s", [
            ("Traefik", "ingress, TLS, ACME"),
            ("Laravel", "site, admin, API"),
            ("Node", "chat, presence, calls"),
            ("Workers", "queues, cron, moderation"),
        ]),

        box(DELIV, "how it ships", "ci", [
            ("GitHub Actions", "build, scan, push"),
            ("Argo CD", "GitOps sync"),
        ], cols=1),
        arrow(DELIV["x"] + DELIV["w"], 361, K3S["x"], 361),

        box(CONF, "how it is configured", "ci", [
            ("AWS SSM", "Parameter Store"),
            ("External Secrets", "SSM into the cluster"),
        ], cols=1),
        arrow(CONF["x"], 361, K3S["x"] + K3S["w"], 361),

        arrow(500, K3S["y"] + K3S["h"], 500, STATE["y"]),
        box(STATE, "state", "data", [
            ("MySQL", "accounts"),
            ("MongoDB", "messages"),
            ("Redis", "queues"),
            ("Meilisearch", "search"),
            ("R2", "media"),
        ], cols=5),

        f'<rect class="chip ci" x="{WATCH["x"]}" y="{WATCH["y"]}" '
        f'width="{WATCH["w"]}" height="{WATCH["h"]}" rx="8"/>',
        T.run("mono", "Grafana", 12.5, WATCH["x"] + WATCH["w"] / 2, WATCH["y"] + 22,
              0.2, anchor="middle", cls="cname"),
        T.run("mono", "dashboards, alerts", 10, WATCH["x"] + WATCH["w"] / 2,
              WATCH["y"] + 37, 0.2, anchor="middle", cls="csub"),
        elbow(K3S["x"] + K3S["w"], 410, WATCH["x"], WATCH["y"] + 26, 742),
    ]

    head = T.run("display", "one operator, one cluster", 25, 40, 50, cls="head")
    sub = ""

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
     viewBox="0 0 {W} {H}" role="img"
     aria-label="Browsers reach Cloudflare, which fronts a k3s cluster running Traefik, Laravel, Node and workers. GitHub Actions and Argo CD push releases into the cluster, AWS SSM and External Secrets supply its configuration, MySQL, MongoDB, Redis, Meilisearch and R2 hold its state, and Grafana watches it.">
  <title>How it holds together</title>
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0.3" y2="1">
      <stop offset="0" stop-color="#070C20"/><stop offset="1" stop-color="#0C1132"/>
    </linearGradient>
    <linearGradient id="spectrum" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#38BDF8"/><stop offset="0.38" stop-color="#6366F1"/>
      <stop offset="0.66" stop-color="#A855F7"/><stop offset="1" stop-color="#EC4899"/>
    </linearGradient>
    <radialGradient id="glow"><stop offset="0" stop-color="#4F46E5" stop-opacity=".34"/>
      <stop offset="1" stop-color="#4F46E5" stop-opacity="0"/></radialGradient>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="20"/></clipPath>
    {T.defs()}
  </defs>

  <style>
    .head      {{ fill:#EDF2FF }}
    .sub       {{ fill:#8496C8 }}
    .grp       {{ fill:#0A0F28; fill-opacity:.5; stroke-width:1 }}
    .grplabel  {{ fill:#8496C8 }}
    .chip      {{ fill:#0B1130; stroke-width:1.2 }}
    .cname     {{ fill:#EDF2FF }}
    .csub      {{ fill:#8496C8 }}
    .flow      {{ stroke:{INK}; stroke-width:1.6; fill:none }}
    .head[d]   {{ fill:{INK} }}
    .edge.grp  {{ stroke:#1D3A63 }}  .edge.chip {{ stroke:#38BDF8; stroke-opacity:.75 }}
    .k8s.grp   {{ stroke:#3A2C74; fill-opacity:.75 }}
    .k8s.chip  {{ stroke:#8B5CF6; stroke-opacity:.8 }}
    .data.grp  {{ stroke:#5A2049 }}  .data.chip {{ stroke:#EC4899; stroke-opacity:.7 }}
    .ci.grp    {{ stroke:#5A4718 }}  .ci.chip   {{ stroke:#FFC23C; stroke-opacity:.7 }}
  </style>

  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#sky)"/>
    <ellipse cx="500" cy="360" rx="430" ry="230" fill="url(#glow)"/>
    <rect x="0" y="{H - 4}" width="{W}" height="4" fill="url(#spectrum)"/>
  </g>

  {head}{sub}
  {"".join(parts)}
</svg>
'''


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)} - {OUT.stat().st_size / 1024:.0f} KB")
