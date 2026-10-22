#!/usr/bin/env python3
"""Render desktop and mobile infrastructure illustrations for the README.

The animated dashes describe the direction of requests, configuration and
observability. Their speed is illustrative; this image is not live telemetry.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import typeset as T

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "architecture.svg"
MOBILE_OUT = ROOT / "assets" / "architecture-mobile.svg"
STATIC_OUT = ROOT / "assets" / "architecture-static.svg"
MOBILE_STATIC_OUT = ROOT / "assets" / "architecture-mobile-static.svg"

CLOUD_CHIPS = [
    ("WAF and CDN", "cache, rate limiting"),
    ("Redirect rules", "locale and host routing"),
    ("Zero Trust", "admin and ops access"),
    ("Realtime", "TURN relays, SFU rooms"),
]
CLUSTER_CHIPS = [
    ("Traefik", "ingress, TLS, ACME"),
    ("Laravel", "site, admin, API"),
    ("Node", "chat, presence, calls"),
    ("Workers", "queues, cron, moderation"),
]
CONFIG_CHIPS = [("AWS SSM", "Parameter Store"), ("External Secrets", "SSM into the cluster")]
STATE_CHIPS = [
    ("MySQL", "accounts"), ("MongoDB", "messages"), ("Redis", "queues"),
    ("Meilisearch", "search"), ("R2", "media"),
]


def chip(x, y, width, height, name, subtitle, kind, mobile=False):
    name_size = min(13 if mobile else 12.5,
                    (width - 14) / T.width("mono", name, 1, 0))
    sub_size = min(10.2 if mobile else 10,
                   (width - 12) / T.width("mono", subtitle, 1, 0))
    return (f'<rect class="chip {kind}" x="{x:.1f}" y="{y:.1f}" '
            f'width="{width:.1f}" height="{height:.1f}" rx="9"/>'
            + T.run("mono", name, name_size, x + width / 2,
                    y + height / 2 - 2, anchor="middle", cls="primary")
            + T.run("mono", subtitle, sub_size, x + width / 2,
                    y + height / 2 + 14, anchor="middle", cls="secondary"))


def box(x, y, width, height, label, kind, chips, cols=2, mobile=False):
    """Group a real set of components, with consistent text sizes."""
    out = [f'<rect class="group {kind}" x="{x}" y="{y}" width="{width}" '
           f'height="{height}" rx="14"/>',
           T.run("mono", label, 12 if mobile else 11.5, x + 16, y + 23,
                 0.4, cls="group-label")]
    pad, gap = 14, 10
    rows = [chips[i:i + cols] for i in range(0, len(chips), cols)]
    cell_width = (width - 2 * pad - gap * (cols - 1)) / cols
    cell_height = (height - 36 - pad - gap * (len(rows) - 1)) / len(rows)
    for row_index, row in enumerate(rows):
        for col_index, (name, subtitle) in enumerate(row):
            cx = x + pad + col_index * (cell_width + gap)
            cy = y + 36 + row_index * (cell_height + gap)
            out.append(chip(cx, cy, cell_width, cell_height, name, subtitle, kind, mobile))
    return "".join(out)


def flow(path, x, y, direction="down", kind="request", delay=0):
    """Animate along the path's source-to-destination order, with a fixed head."""
    dx, dy = {"down": (0, 1), "up": (0, -1), "right": (1, 0), "left": (-1, 0)}[direction]
    bx, by = x - dx * 7, y - dy * 7
    head = f"M{bx + dy * 4} {by - dx * 4}L{x} {y}L{bx - dy * 4} {by + dx * 4}Z"
    return (f'<g class="connection {kind}"><path class="track" d="{path}"/>'
            f'<path class="packet" d="{path}" style="animation-delay:{delay}s"/>'
            f'<path class="arrowhead" d="{head}"/></g>')


def delivery(x, y, width, mobile=False):
    """Actions dispatches to three runner options, then GitOps delivers."""
    center = x + width / 2
    dispatch, collect = x + 8, x + width - 8
    runner_x, runner_width = x + 28, width - 56
    parts = [
        f'<rect class="group delivery" x="{x}" y="{y}" width="{width}" height="350" rx="14"/>',
        T.run("mono", "HOW IT SHIPS", 12 if mobile else 11.5,
              x + 16, y + 23, 0.4, cls="group-label"),
        chip(x + 14, y + 36, width - 28, 48, "GitHub Actions", "build, scan, push", "delivery", mobile),
        chip(x + 14, y + 286, width - 28, 50, "Argo CD", "GitOps sync", "delivery", mobile),
        T.run("mono", "images + Git", 10, center, y + 273,
              anchor="middle", cls="secondary"),
    ]
    runners = [("GitHub", "hosted runner"), ("CodeBuild", "self-hosted"), ("EC2 Spot", "self-hosted")]
    for index, (name, subtitle) in enumerate(runners):
        runner_y = y + 110 + index * 52
        runner_center = runner_y + 21
        parts.append(chip(runner_x, runner_y, runner_width, 42, name, subtitle, "delivery", mobile))
        parts.append(flow(f"M{center} {y + 84}V{y + 98}H{dispatch}V{runner_center}H{runner_x - 6}",
                          runner_x, runner_center, "right", "release", -0.3 - index * 0.2))
        parts.append(flow(f"M{runner_x + runner_width} {runner_center}H{collect - 6}",
                          collect, runner_center, "right", "release", -0.7))
    parts.append(flow(f"M{collect} {y + 131}V{y + 280}H{center}", center, y + 286,
                      kind="release", delay=-1))
    return "".join(parts)


def user_box(x, y, width):
    return (f'<rect class="chip edge" x="{x}" y="{y}" width="{width}" height="54" rx="12"/>'
            + T.run("mono", "browsers, extensions, mobile web", 12.5,
                    x + width / 2, y + 23, anchor="middle", cls="primary")
            + T.run("mono", "five public brands", 10.5,
                    x + width / 2, y + 41, anchor="middle", cls="secondary"))


def aws_project(x, y, width, mobile=False):
    """The upload API signs URLs; browsers upload directly to S3."""
    center = x + width / 2
    return "".join([
        f'<rect class="group aws" x="{x}" y="{y}" width="{width}" height="214" rx="14"/>',
        T.run("mono", "AWS / IMAGE UPLOADS", 11.5, x + 16, y + 23,
              cls="group-label"),
        chip(x + 14, y + 36, width - 28, 42, "API Gateway", "upload URL endpoint", "aws", mobile),
        flow(f"M{center} {y + 78}V{y + 90}", center, y + 96,
             kind="request", delay=-0.4),
        chip(x + 14, y + 96, width - 28, 42, "Lambda", "presigned URLs", "aws", mobile),
        flow(f"M{center} {y + 138}V{y + 150}", center, y + 156,
             kind="request", delay=-0.8),
        chip(x + 14, y + 156, width - 28, 44, "S3", "direct browser upload", "aws", mobile),
    ])


def watcher(x, y, width):
    return (f'<rect class="chip observe" x="{x}" y="{y}" width="{width}" height="60" rx="10"/>'
            + T.run("mono", "Grafana", 13, x + width / 2, y + 25, anchor="middle", cls="primary")
            + T.run("mono", "dashboards, alerts", 10.5,
                    x + width / 2, y + 43, anchor="middle", cls="secondary"))


def desktop_layout():
    parts = [
        user_box(340, 110, 320),
        flow("M500 164V196", 500, 202),
        box(270, 202, 460, 156, "01 / CLOUDFLARE", "edge", CLOUD_CHIPS),
        flow("M500 358V390", 500, 396, delay=-0.6),
        box(270, 396, 460, 156, "02 / K3S CLUSTER", "cluster", CLUSTER_CHIPS),
        delivery(28, 202, 210),
        flow("M238 513H264", 270, 513, "right", "release", -0.5),
        aws_project(762, 164, 210),
        flow("M500 382H746V221H770", 776, 221, "right", delay=-0.9),
        '<circle class="cyan" cx="500" cy="382" r="3"/>',
        box(762, 396, 210, 156, "CONFIGURATION", "delivery", CONFIG_CHIPS, cols=1),
        flow("M762 474H736", 730, 474, "left", "release", -0.8),
        flow("M500 552V592", 500, 598, kind="storage", delay=-1),
        box(100, 598, 630, 100, "03 / STATE", "data", STATE_CHIPS, cols=5),
        watcher(762, 626, 210),
        flow("M730 528H746V656H756", 762, 656, "right", "telemetry", -1.3),
        T.run("mono", "REQUESTS", 10, 518, 186, 0.6, cls="cyan"),
        T.run("mono", "ORIGIN", 10, 518, 373, 0.6, cls="cyan"),
        T.run("mono", "PERSIST", 10, 518, 582, 0.6, cls="pink"),
    ]
    return "".join(parts)


def mobile_layout():
    parts = [
        user_box(44, 122, 392),
        flow("M240 176V210", 240, 216),
        box(24, 216, 432, 174, "01 / CLOUDFLARE", "edge", CLOUD_CHIPS, mobile=True),
        flow("M240 390V428", 240, 434, delay=-0.6),
        box(24, 434, 432, 174, "02 / K3S CLUSTER", "cluster", CLUSTER_CHIPS, mobile=True),
        delivery(24, 654, 202, mobile=True),
        flow("M226 965H232V628H124V614", 124, 608, "up", "release", -0.5),
        box(254, 654, 202, 162, "CONFIGURATION", "delivery", CONFIG_CHIPS, cols=1, mobile=True),
        flow("M356 654V614", 356, 608, "up", "release", -0.8),
        aws_project(254, 838, 202, mobile=True),
        flow("M240 422H462V895H448", 442, 895, "left", delay=-0.9),
        '<circle class="cyan" cx="240" cy="422" r="3"/>',
        flow("M240 608V1108", 240, 1114, kind="storage", delay=-1),
        box(24, 1114, 432, 170, "03 / STATE", "data", STATE_CHIPS, cols=3, mobile=True),
        watcher(126, 1332, 228),
        # Bridge over the origin-to-AWS route without implying a junction.
        flow("M456 580H458C458 572 466 572 466 580H469V1362H360",
             354, 1362, "left", "telemetry", -1.3),
        T.run("mono", "requests", 10.5, 256, 201, cls="cyan"),
        T.run("mono", "origin", 10.5, 256, 416, cls="cyan"),
    ]
    return "".join(parts)


def build(mobile=False, static=False):
    """Return an SVG, optionally vertical and/or without animated paths.

    Static variants are selected by README picture sources for reduced motion.
    Older Chromium versions do not propagate that media preference into an
    embedded SVG's own stylesheet, so the internal media query is insufficient.
    """
    T.reset()
    width, height = (480, 1460) if mobile else (1000, 764)
    pad = 24 if mobile else 40
    heading = T.run("display", "One operator. One cluster.", 28 if mobile else 31,
                    pad, 48, cls="primary")
    subtitle = T.run("text", "From a browser click to a byte of state.",
                     16, pad, 77, cls="secondary")
    body = mobile_layout() if mobile else desktop_layout()
    path_label = "Paths" if static else "Animated paths"
    if mobile:
        footer = (T.run("mono", path_label + " illustrate the architecture.", 10.5,
                        pad, height - 38, cls="secondary")
                  + T.run("mono", "Request / release / state / observability", 10.5,
                          pad, height - 19, cls="secondary"))
    else:
        footer = T.run("mono", path_label + " illustrate request, release, state and observability flows.",
                       11, pad, height - 26, cls="secondary")
    packet_animation = "none" if static else "flow 1.4s linear infinite"
    motion_rules = "" if static else """
    @keyframes flow { to { stroke-dashoffset:-48 } }
    @media (prefers-reduced-motion:reduce) { .packet { animation:none } }
    """
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
  viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">One operator. One cluster.</title>
  <desc id="desc">Browsers reach Cloudflare, then a k3s cluster running Traefik, Laravel, Node and workers.
  GitHub Actions dispatches builds to GitHub-hosted runners or self-hosted runners in AWS CodeBuild or on EC2 Spot instances.
  Builds publish images and update Git manifests; Argo CD syncs releases into the cluster.
  AWS SSM and External Secrets supply configuration.
  The origin route also branches to the AWS image-upload project's API Gateway.
  API Gateway invokes Lambda, which signs S3 upload URLs; browsers upload files directly to S3.
  MySQL, MongoDB, Redis, Meilisearch and R2 hold state. Grafana receives observability data.
  {path_label} illustrate direction, not live traffic.</desc>
  <defs>
    <linearGradient id="sky" x2=".3" y2="1"><stop stop-color="#070C20"/><stop offset="1" stop-color="#0C1132"/></linearGradient>
    <linearGradient id="spectrum"><stop stop-color="#38BDF8"/><stop offset=".5" stop-color="#8B5CF6"/><stop offset="1" stop-color="#EC4899"/></linearGradient>
    <radialGradient id="glow"><stop stop-color="#4F46E5" stop-opacity=".21"/><stop offset="1" stop-color="#4F46E5" stop-opacity="0"/></radialGradient>
    <clipPath id="frame"><rect width="{width}" height="{height}" rx="20"/></clipPath>
    {T.defs()}
  </defs>
  <style>
    .primary {{ fill:#EDF2FF }} .secondary, .group-label {{ fill:#93A4CE }}
    .cyan {{ fill:#65D4FF }} .pink {{ fill:#F18BCB }}
    .group {{ fill:#0B1029; fill-opacity:.8; stroke-width:1 }}
    .chip {{ fill:#0D1531; stroke-width:1 }}
    .edge.group {{ stroke:#224665 }} .edge.chip {{ stroke:#3489A9 }}
    .cluster.group {{ stroke:#533783; fill:#171039 }} .cluster.chip {{ stroke:#8057BB }}
    .delivery.group {{ stroke:#594923 }} .delivery.chip {{ stroke:#A17D32 }}
    .aws.group {{ stroke:#664326 }} .aws.chip {{ stroke:#C78B4A }}
    .data.group {{ stroke:#582C4D }} .data.chip {{ stroke:#A54E8B }}
    .observe.chip {{ stroke:#479C89 }}
    .connection {{ color:#65D4FF }} .release {{ color:#FFD477 }}
    .storage {{ color:#F18BCB }} .telemetry {{ color:#77DFBE }}
    .track {{ fill:none; stroke:currentColor; stroke-opacity:.2; stroke-width:2 }}
    .packet {{ fill:none; stroke:currentColor; stroke-width:2.5; stroke-linecap:round;
      stroke-dasharray:3 21; animation:{packet_animation} }}
    .arrowhead {{ fill:currentColor; opacity:.9 }}
    {motion_rules}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{width}" height="{height}" fill="url(#sky)"/>
    <ellipse cx="{width / 2}" cy="{height * .55}" rx="{width * .55}" ry="{height * .4}" fill="url(#glow)"/>
    <rect y="{height - 4}" width="{width}" height="4" fill="url(#spectrum)"/>
  </g>
  {heading}{subtitle}{body}{footer}
</svg>
'''


if __name__ == "__main__":
    for output, mobile, static in ((OUT, False, False), (MOBILE_OUT, True, False),
                                   (STATIC_OUT, False, True), (MOBILE_STATIC_OUT, True, True)):
        svg = build(mobile=mobile, static=static)
        output.write_text("\n".join(line.rstrip() for line in svg.splitlines()) + "\n", encoding="utf-8")
        print(f"{output.relative_to(ROOT)} - {output.stat().st_size / 1024:.0f} KB")
