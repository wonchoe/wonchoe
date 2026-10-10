#!/usr/bin/env python3
"""Draw self-contained desktop/mobile audience cards from Cloudflare aggregates.

Run fetch_edge_stats.mjs first in Actions, then this script. An absent snapshot
gets an explicit awaiting-sync design, never invented statistics. Map geometry
is bundled with its public-domain attribution in tools/maps/SOURCE.txt.
"""
import datetime as dt
import html
import json
import math
import pathlib
import unicodedata

import typeset as T

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "assets" / "edge.json"
MAP = json.loads((ROOT / "tools" / "maps" / "natural-earth-110m.json").read_text())


def text(string, size, x, y, role="mono", cls="muted", anchor="start"):
    return T.run(role, str(string), size, x, y, cls=cls, anchor=anchor)


def ascii_name(name):
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()


def fit_name(name, width):
    name = ascii_name(name)
    if T.width("text", name, 17) <= width:
        return name
    while T.width("text", name + "...", 17) > width:
        name = name[:-1]
    return name.rstrip() + "..."


def compact(value):
    for threshold, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if value >= threshold:
            return f"{value / threshold:.1f}".rstrip("0").rstrip(".") + suffix
    return f"{value:,.0f}"


def bandwidth(value):
    for threshold, suffix in ((1e15, "PB"), (1e12, "TB"), (1e9, "GB"), (1e6, "MB"), (1e3, "KB")):
        if value >= threshold:
            return f"{value / threshold:.1f} {suffix}"
    return f"{value} B"


def validate(data):
    if data is None:
        return
    if data.get("schemaVersion") != 1:
        raise ValueError("Unsupported audience schema")
    for key in ("requests", "cachedRequests", "bytes", "cachedBytes"):
        value = data["totals"][key]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError("Invalid audience metric")
    totals = data["totals"]
    if totals["cachedRequests"] > totals["requests"] or totals["cachedBytes"] > totals["bytes"]:
        raise ValueError("Inconsistent cache metrics")
    start, end = (dt.date.fromisoformat(data["period"][key]) for key in ("start", "end"))
    if (end - start).days != 29 or data["period"]["days"] != 30:
        raise ValueError("Expected 30 complete days")
    dt.date.fromisoformat(data["updated"])
    if not isinstance(data["countries"], list):
        raise ValueError("Missing country metrics")
    codes = set()
    for country in data["countries"]:
        if (len(country["code"]) != 2 or not country["code"].isalpha()
                or country["code"] in codes or not isinstance(country["requests"], int)
                or country["requests"] <= 0 or not isinstance(country["name"], str)):
            raise ValueError("Invalid country metrics")
        codes.add(country["code"])
    if sum(country["requests"] for country in data["countries"]) > totals["requests"]:
        raise ValueError("Country requests exceed total")


def world_map(countries, x, y, width):
    counts = {country["code"]: country["requests"] for country in countries}
    peak = max(counts.values(), default=1)
    shapes = []
    top_codes = {country["code"] for country in countries[:5]}
    pulses = []
    scale = width / 360
    for feature in MAP:
        requests = counts.get(feature["code"], 0)
        if requests:
            weight = math.log1p(requests) / math.log1p(peak)
            # Cyan highlights have more traffic; inactive regions remain indigo.
            rgb = tuple(round(low + (high - low) * weight) for low, high in zip((39, 58, 110), (111, 225, 230)))
            fill = "#" + "".join(f"{value:02x}" for value in rgb)
        else:
            fill = "#1b2850"
        shapes.append(f'<path d="{feature["path"]}" fill="{fill}"/>')
        if feature["code"] in top_codes:
            px, py = feature["center"]
            index = len(pulses)
            pulses.append(f'<g transform="translate({px},{py})"><circle r="2.1" fill="#f2fdff"/>'
                          f'<circle class="pulse" r="4.5" style="animation-delay:-{index * .65}s"/></g>')
    grid = "".join(f'<path d="M0 {lat}H360"/>' for lat in (25, 55, 85, 115))
    grid += "".join(f'<path d="M{lon} 0V145"/>' for lon in range(30, 360, 60))
    return (f'<g transform="translate({x},{y}) scale({scale:.5f})">'
            f'<g stroke="#27355d" stroke-width=".3" opacity=".65">{grid}</g>'
            f'<g stroke="#0b1531" stroke-width=".4" stroke-linejoin="round">{"".join(shapes)}</g>'
            f'{"".join(pulses)}</g>')


def ranking(countries, total, x, y, width, mobile=False, pending=False):
    row_height = 40 if mobile else 48
    out = [text("TOP LOCATIONS", 10, x, y, cls="cyan"),
           text("% OF REQUESTS", 9, x + width, y, anchor="end")]
    if not countries:
        message = "Awaiting first Cloudflare sync" if pending else "No country-attributed requests"
        out.append(text(message, 16, x, y + 50, role="text", cls="light"))
    for index, country in enumerate(countries[:5]):
        baseline = y + 35 + index * row_height
        share = country["requests"] / total * 100 if total else 0
        out.append(text(country["code"], 10, x, baseline, cls="cyan"))
        out.append(text(fit_name(country["name"], width - 122), 17, x + 35, baseline, role="text", cls="light"))
        out.append(text(f"{share:.1f}%", 12, x + width, baseline, cls="light", anchor="end"))
        out.append(f'<rect x="{x + 35}" y="{baseline + 8}" width="{width - 35}" height="3" rx="1.5" fill="#1c2a50"/>')
        out.append(f'<rect x="{x + 35}" y="{baseline + 8}" width="{(width - 35) * share / 100:.2f}" height="3" rx="1.5" fill="url(#spectrum)"/>')
    return "".join(out)


def build(data=None, mobile=False, static=False):
    validate(data)
    T.reset()
    w, h = (600, 832) if mobile else (1000, 556)
    pad = 32 if mobile else 44
    countries = sorted(data["countries"], key=lambda country: (-country["requests"], country["code"])) if data else []
    totals = data["totals"] if data else None
    updated = f'Updated {data["updated"]}' if data else "Awaiting first sync"
    heading = f'{len(countries)} countries & territories' if data else "An audience without borders"
    description = (f'cursor.style HTTP requests from {len(countries)} countries and territories, '
                   f'{data["period"]["start"]} to {data["period"]["end"]} UTC. '
                   f'{totals["cachedRequests"]:,} of {totals["requests"]:,} requests served from cache.'
                   if data else 'Global audience statistics awaiting the first Cloudflare sync.')
    content = [text("Across the world", 29, pad, 51, role="display", cls="light"),
               text("cursor.style / 30 complete UTC days", 11, pad, 76),
               text(heading, 26, pad, 121, role="display", cls="light")]
    if mobile:
        content += [world_map(countries, 32, 151, 536),
                    text("LOW", 9, 32, 391), text("HIGH REQUEST VOLUME", 9, 209, 391),
                    '<rect x="67" y="384" width="123" height="7" rx="3.5" fill="url(#heat)"/>',
                    ranking(countries, totals["requests"] if totals else 0, 32, 433, 536, True, not data)]
        rule_y, metric_y, label_y, foot_y = 676, 718, 744, 787
        positions = (32, 215, 415)
    else:
        content += [text(updated, 10.5, w - pad, 51, anchor="end"),
                    text("Geographic reach of HTTP requests", 10, pad, 144),
                    world_map(countries, 35, 166, 583),
                    text("LOW", 9, 44, 408), text("HIGH REQUEST VOLUME", 9, 220, 408),
                    '<rect x="78" y="401" width="123" height="7" rx="3.5" fill="url(#heat)"/>',
                    ranking(countries, totals["requests"] if totals else 0, 650, 123, 306, pending=not data)]
        rule_y, metric_y, label_y, foot_y = 432, 480, 503, 536
        positions = (44, 365, 710)
    cache_rate = f'{totals["cachedRequests"] / totals["requests"] * 100:.1f}%' if totals and totals["requests"] else "--"
    cached_bandwidth = bandwidth(totals["cachedBytes"]) if totals else "--"
    rate = compact(totals["requests"] / (30 * 86400)) + "/s" if totals else "--"
    content.append(f'<path d="M{pad} {rule_y}H{w-pad}" stroke="#29365e"/>')
    for index, (value, label) in enumerate(((cache_rate, "requests from cache"), (cached_bandwidth, "bandwidth from cache"), (rate, "average requests"))):
        content += [text(value, 29 if mobile else 34, positions[index], metric_y, role="display", cls="light"),
                    text(label, 9 if mobile else 10.5, positions[index], label_y)]
    if mobile:
        content += [text(updated + " / Cloudflare", 10, pad, foot_y),
                    text("Includes bots / map: Natural Earth / motion is illustrative", 8.4, pad, foot_y + 22)]
    else:
        content += [text("Includes bots / map: Natural Earth / motion is illustrative", 9, pad, foot_y),
                    text(f'{data["period"]["start"]} - {data["period"]["end"]} UTC' if data else "No data published yet", 9, w - pad, foot_y, anchor="end")]
    motion = (".pulse{fill:none;stroke:#d2fbff;stroke-width:.8;opacity:.3;animation:none}"
              if static else """
.pulse{fill:none;stroke:#d2fbff;stroke-width:.8;opacity:.55;animation:ping 3.8s ease-out infinite;transform-box:fill-box;transform-origin:center}
@keyframes ping{0%{transform:scale(.6);opacity:.7}80%,100%{transform:scale(2.6);opacity:0}}
@media(prefers-reduced-motion:reduce){.pulse{animation:none;opacity:.3}}
""")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{html.escape(description, quote=True)}">
<title>Global audience and edge performance</title><desc>{html.escape(description)}</desc>
<defs>
<linearGradient id="sky" x2=".7" y2="1"><stop stop-color="#070c20"/><stop offset="1" stop-color="#10183c"/></linearGradient>
<linearGradient id="spectrum"><stop stop-color="#38bdf8"/><stop offset=".5" stop-color="#818cf8"/><stop offset="1" stop-color="#e879f9"/></linearGradient>
<linearGradient id="heat"><stop stop-color="#273a6e"/><stop offset="1" stop-color="#6fe1e6"/></linearGradient>
<radialGradient id="glow"><stop stop-color="#435bd5" stop-opacity=".17"/><stop offset="1" stop-color="#435bd5" stop-opacity="0"/></radialGradient>
<clipPath id="frame"><rect width="{w}" height="{h}" rx="20"/></clipPath>
<!--GLYPHS-->
</defs>
<style>
.light{{fill:#edf2ff}}.muted{{fill:#8e9fc8}}.cyan{{fill:#7dd9ed}}
{motion}
</style>
<g clip-path="url(#frame)"><rect width="{w}" height="{h}" fill="url(#sky)"/>
<ellipse cx="{w*.32}" cy="{h*.45}" rx="{w*.5}" ry="{h*.55}" fill="url(#glow)"/>
<rect y="{h-4}" width="{w}" height="4" fill="url(#spectrum)"/></g>
{"".join(content)}
</svg>'''
    return svg.replace("<!--GLYPHS-->", T.defs())


if __name__ == "__main__":
    snapshot = json.loads(DATA.read_text()) if DATA.exists() else None
    for mobile in (False, True):
        for static in (False, True):
            name = "audience" + ("-mobile" if mobile else "") + ("-static" if static else "") + ".svg"
            output = ROOT / "assets" / name
            output.write_text(build(snapshot, mobile=mobile, static=static))
            print(f"{output.relative_to(ROOT)}: {output.stat().st_size // 1024} KB")
