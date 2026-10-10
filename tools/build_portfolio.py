#!/usr/bin/env python3
"""Draw a separate overview of the Cloudflare domains available to the token.

The snapshot contains aggregate requests, never deduplicated visitors. Reuse
the audience card's map and typography, while keeping cursor.style's card and
source snapshot independent. Missing data does not produce a public card.
"""
import html
import json

import build_audience as audience

ROOT = audience.ROOT
DATA = ROOT / "assets" / "portfolio.json"
T = audience.T
text = audience.text


def validate(data):
    if data is None:
        raise ValueError("A real connected-sites snapshot is required")
    audience.validate(data)
    if data.get("scope") != "accessible_zones":
        raise ValueError("Expected accessible Cloudflare zones")
    sites = data.get("siteCount")
    if not isinstance(sites, int) or isinstance(sites, bool) or sites < 1:
        raise ValueError("Expected a positive connected-site count")


def build(data, mobile=False, static=False):
    validate(data)
    T.reset()
    w, h = (600, 900) if mobile else (1000, 580)
    pad = 32 if mobile else 44
    sites = data["siteCount"]
    countries = sorted(data["countries"], key=lambda country: (-country["requests"], country["code"]))
    totals = data["totals"]
    updated = f'Updated {data["updated"]}'
    subtitle = f'{sites} connected {"domain" if sites == 1 else "domains"} / 30 complete UTC days'
    heading = f'{len(countries)} countries & territories'
    description = (
        f'{totals["requests"]:,} HTTP requests and {totals["bytes"]:,} transferred bytes '
        f'across {sites} connected Cloudflare domains, '
        f'{data["period"]["start"]} to {data["period"]["end"]} UTC. '
        f'{totals["cachedRequests"]:,} requests served from cache. '
        f'Requests originated in {len(countries)} countries and territories. '
        'Scope: all Cloudflare zones accessible to the configured token. '
        'Requests include bots and are summed across domains; they are not unique visitors.'
    )
    content = [text("Across my projects", 29, pad, 51, role="display", cls="light"),
               text(subtitle, 11, pad, 76)]
    positions = (32, 215, 415) if mobile else (44, 365, 710)
    metric_y, label_y = (131, 156) if mobile else (141, 166)
    cache_rate = (f'{totals["cachedRequests"] / totals["requests"] * 100:.1f}%'
                  if totals["requests"] else "--")
    metrics = ((audience.compact(totals["requests"]), "total HTTP requests"),
               (audience.bandwidth(totals["bytes"]), "data transferred"),
               (cache_rate, "requests from cache"))
    for index, (value, label) in enumerate(metrics):
        content += [text(value, 31 if mobile else 38, positions[index], metric_y,
                         role="display", cls="light"),
                    text(label, 9 if mobile else 10.5, positions[index], label_y)]
    content.append(text(heading, 26, pad, 207, role="display", cls="light"))
    if mobile:
        content += [audience.world_map(countries, 32, 234, 536),
                    text("LOW", 9, 32, 474), text("HIGH REQUEST VOLUME", 9, 209, 474),
                    '<rect x="67" y="467" width="123" height="7" rx="3.5" fill="url(#heat)"/>',
                    audience.ranking(countries, totals["requests"], 32, 518, 536, mobile=True),
                    '<path d="M32 770H568" stroke="#29365e"/>',
                    text(updated + " / Cloudflare", 10, pad, 802),
                    text("Scope: accessible Cloudflare zones", 9, pad, 826),
                    text("Summed requests, including bots / not unique visitors", 9, pad, 850),
                    text("Map: Natural Earth / motion is illustrative", 8.5, pad, 874)]
    else:
        content += [text(updated, 10.5, w - pad, 51, anchor="end"),
                    audience.world_map(countries, 35, 225, 583),
                    text("LOW", 9, 44, 477), text("HIGH REQUEST VOLUME", 9, 220, 477),
                    '<rect x="78" y="470" width="123" height="7" rx="3.5" fill="url(#heat)"/>',
                    audience.ranking(countries, totals["requests"], 650, 209, 306),
                    '<path d="M44 510H956" stroke="#29365e"/>',
                    text("Scope: accessible Cloudflare zones", 9, pad, 536),
                    text("Summed requests, including bots / not unique visitors", 9, pad, 558),
                    text(f'{data["period"]["start"]} - {data["period"]["end"]} UTC',
                         9, w - pad, 536, anchor="end"),
                    text("Map: Natural Earth / motion is illustrative", 8.5,
                         w - pad, 558, anchor="end")]
    motion = (".pulse{fill:none;stroke:#d2fbff;stroke-width:.8;opacity:.3;animation:none}"
              if static else """
.pulse{fill:none;stroke:#d2fbff;stroke-width:.8;opacity:.55;animation:ping 3.8s ease-out infinite;transform-box:fill-box;transform-origin:center}
@keyframes ping{0%{transform:scale(.6);opacity:.7}80%,100%{transform:scale(2.6);opacity:0}}
@media(prefers-reduced-motion:reduce){.pulse{animation:none;opacity:.3}}
""")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{html.escape(description, quote=True)}">
<title>Connected domains: traffic and geographic reach</title><desc>{html.escape(description)}</desc>
<defs>
<linearGradient id="sky" x2=".7" y2="1"><stop stop-color="#0c1028"/><stop offset="1" stop-color="#171436"/></linearGradient>
<linearGradient id="spectrum"><stop stop-color="#a78bfa"/><stop offset=".5" stop-color="#e879f9"/><stop offset="1" stop-color="#38bdf8"/></linearGradient>
<linearGradient id="heat"><stop stop-color="#273a6e"/><stop offset="1" stop-color="#6fe1e6"/></linearGradient>
<radialGradient id="glow"><stop stop-color="#a855f7" stop-opacity=".14"/><stop offset="1" stop-color="#a855f7" stop-opacity="0"/></radialGradient>
<clipPath id="frame"><rect width="{w}" height="{h}" rx="20"/></clipPath>
<!--GLYPHS-->
</defs>
<style>
.light{{fill:#edf2ff}}.muted{{fill:#8e9fc8}}.cyan{{fill:#7dd9ed}}
{motion}
</style>
<g clip-path="url(#frame)"><rect width="{w}" height="{h}" fill="url(#sky)"/>
<ellipse cx="{w*.37}" cy="{h*.4}" rx="{w*.5}" ry="{h*.6}" fill="url(#glow)"/>
<rect y="{h-4}" width="{w}" height="4" fill="url(#spectrum)"/></g>
{"".join(content)}
</svg>'''
    return svg.replace("<!--GLYPHS-->", T.defs())


def main():
    if not DATA.exists():
        print("No connected-sites snapshot yet; portfolio cards were not generated.")
        return
    snapshot = json.loads(DATA.read_text())
    validate(snapshot)
    for mobile in (False, True):
        for static in (False, True):
            name = "portfolio" + ("-mobile" if mobile else "") + ("-static" if static else "") + ".svg"
            output = ROOT / "assets" / name
            output.write_text(build(snapshot, mobile=mobile, static=static))
            print(f"{output.relative_to(ROOT)}: {output.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
