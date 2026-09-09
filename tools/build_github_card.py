#!/usr/bin/env python3
"""Render assets/github.svg - what I actually write, from the GitHub API.

The popular readme-stats services were returning 503 and 402 when this profile
was built, so the card is generated here instead: one GraphQL call, cached to
assets/github.json, rendered with the same type and palette as the other cards.
Set GITHUB_TOKEN to refresh; without one it re-renders the cached JSON.
"""
import collections, datetime as dt, json, os, pathlib, sys, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import typeset as T

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "assets" / "github.json"
OUT = ROOT / "assets" / "github.svg"
USER = "wonchoe"

W, H = 1000, 230
PAD = 52
BAR = dict(y=164, h=14)
TOP_LANGUAGES = 6

QUERY = """
{ user(login: "%s") {
    createdAt
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      nodes {
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection { contributionCalendar { totalContributions } }
} }""" % USER


def fetch(token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY}).encode(),
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json",
                 "User-Agent": f"{USER}-profile-card"})
    body = json.loads(urllib.request.urlopen(req, timeout=45).read())
    if body.get("errors"):
        raise RuntimeError("GitHub GraphQL: " + json.dumps(body["errors"]))
    user = body["data"]["user"]

    sizes, colors = collections.Counter(), {}
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            sizes[edge["node"]["name"]] += edge["size"]
            colors[edge["node"]["name"]] = edge["node"]["color"] or "#8B98B5"

    total = sum(sizes.values()) or 1
    top = sizes.most_common(TOP_LANGUAGES)
    languages = [{"name": n, "share": s / total, "color": colors[n]} for n, s in top]
    rest = 1 - sum(l["share"] for l in languages)
    if rest > 0.001:
        languages.append({"name": "Other", "share": rest, "color": "#5B6785"})

    return {
        "updated": dt.date.today().isoformat(),
        "repos": user["repositories"]["totalCount"],
        "contributions": user["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "since": user["createdAt"][:10],
        "languages": languages,
    }


def figure(value, label, x):
    return (f'{T.run("display", value, 34, x, 112, cls="fig")}'
            f'{T.run("mono", label, 11.5, x, 134, 0.3, cls="figlab")}')


def build(d):
    T.reset()
    since = dt.date.fromisoformat(d["since"])
    figures = (figure(f"{d['repos']}", "public repositories", PAD)
               + figure(f"{d['contributions']:,}", "contributions, last 12 months", 300)
               + figure(since.strftime("%Y"), f"here since {since.strftime('%B')}", 620))

    segments, legend, x, lx = [], [], PAD, PAD
    span = W - 2 * PAD
    for lang in d["languages"]:
        w = lang["share"] * span
        segments.append(f'<rect x="{x:.1f}" y="{BAR["y"]}" width="{w:.2f}" '
                        f'height="{BAR["h"]}" fill="{lang["color"]}"/>')
        x += w
        label = f'{lang["name"]} {lang["share"] * 100:.1f}%'
        legend.append(f'<circle cx="{lx + 4:.0f}" cy="204" r="4" fill="{lang["color"]}"/>'
                      f'{T.run("mono", label, 11.5, lx + 15, 208, 0.2)}')
        lx += 15 + T.width("mono", label, 11.5, 0.2) + 20

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
     viewBox="0 0 {W} {H}" role="img"
     aria-label="{d["repos"]} public repositories, {d["contributions"]} contributions in the last year">
  <title>Oleksii Semeniuk on GitHub</title>
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0.3" y2="1">
      <stop offset="0" stop-color="#070C20"/><stop offset="1" stop-color="#0C1132"/>
    </linearGradient>
    <linearGradient id="spectrum" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#38BDF8"/><stop offset="0.38" stop-color="#6366F1"/>
      <stop offset="0.66" stop-color="#A855F7"/><stop offset="1" stop-color="#EC4899"/>
    </linearGradient>
    <radialGradient id="glow"><stop offset="0" stop-color="#4F46E5" stop-opacity=".35"/>
      <stop offset="1" stop-color="#4F46E5" stop-opacity="0"/></radialGradient>
    <!--GLYPHDEFS-->
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="20"/></clipPath>
    <clipPath id="barclip">
      <rect x="{PAD}" y="{BAR["y"]}" width="{W - 2 * PAD}" height="{BAR["h"]}" rx="7"/>
    </clipPath>
  </defs>

  <style>
    .head   {{ fill:#EDF2FF }}
    .sub    {{ fill:#8496C8 }}
    .fig    {{ fill:#EDF2FF }}
    .figlab {{ fill:#8496C8 }}
    .legend {{ fill:#9DB2E6 }}
    .bar    {{ transform-box:fill-box; transform-origin:left;
               animation:wipe .8s cubic-bezier(.22,.9,.3,1) both }}
    @keyframes wipe {{ from {{ transform:scaleX(0) }} to {{ transform:scaleX(1) }} }}
    @media (prefers-reduced-motion:reduce) {{ .bar {{ animation:none }} }}
  </style>

  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#sky)"/>
    <ellipse cx="500" cy="120" rx="520" ry="200" fill="url(#glow)"/>
    <rect x="0" y="{H - 4}" width="{W}" height="4" fill="url(#spectrum)"/>
  </g>

  {T.run("display", "what I actually write", 25, PAD, 52, cls="head")}
  <path class="sub"  d="{T.path("mono", "GitHub, updated " + d["updated"], 11.5, W - PAD, 50, 0.2, anchor="end")}"/>

  {figures}
  <g class="bar" clip-path="url(#barclip)">{"".join(segments)}</g>
  <g class="legend">{"".join(legend)}</g>
</svg>
'''
    return svg.replace("<!--GLYPHDEFS-->", T.defs())


if __name__ == "__main__":
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        # A stale card beats a failed run: the traffic numbers in the same job
        # matter more than this one, so never take the workflow down with us.
        try:
            DATA.write_text(json.dumps(fetch(token), indent=2) + "\n", encoding="utf-8")
        except Exception as err:
            print(f"GitHub refresh failed, re-rendering the cached numbers: {err}")
    data = json.loads(DATA.read_text(encoding="utf-8"))
    OUT.write_text(build(data), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)} - {OUT.stat().st_size / 1024:.0f} KB")
