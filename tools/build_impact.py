#!/usr/bin/env python3
"""Build dated impact cards from the existing Cloudflare and chat snapshots.

No network or credentials are required. Missing values stay unavailable rather
than becoming a zero, and the 30-day unique count comes from the range
aggregate, never from a sum of daily unique counts.
"""
import datetime as dt
import html
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import typeset as T

ROOT = pathlib.Path(__file__).resolve().parent.parent
TRAFFIC = ROOT / "assets" / "traffic.json"
CHAT = ROOT / "assets" / "chat.json"
OUT = ROOT / "assets" / "impact.svg"
MOBILE_OUT = ROOT / "assets" / "impact-mobile.svg"


def number(value):
    """Accept JSON numbers or the chat endpoint's comma-separated integers."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        value = float(str(value).replace(",", ""))
        return int(value) if math.isfinite(value) and value >= 0 else None
    except (ValueError, TypeError):
        return None


def compact(value):
    if value is None:
        return "--"
    for divisor, unit in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if value >= divisor:
            precision = 1 if value / divisor >= 10 else 2
            return f"{value / divisor:.{precision}f}".rstrip("0").rstrip(".") + unit
    return str(value)


def snapshot_date(data):
    try:
        return dt.date.fromisoformat(str(data.get("updated", ""))[:10])
    except ValueError:
        return None


def metrics(traffic, chat):
    """Expose source values and dates for callers, alt text and validation."""
    totals = traffic.get("last30d") or {}
    yesterday = {item.get("label"): number(item.get("value"))
                 for item in (chat.get("yesterday") or [])}
    traffic_date, chat_date = snapshot_date(traffic), snapshot_date(chat)
    return {
        "requests": number(totals.get("requests")),
        "visitors": number(totals.get("uniques")),
        "messages": yesterday.get("messages"),
        "calls": yesterday.get("calls"),
        "traffic_start": traffic_date - dt.timedelta(days=30) if traffic_date else None,
        "traffic_end": traffic_date - dt.timedelta(days=1) if traffic_date else None,
        # The endpoint dates its rollups in America/New_York, but `updated` is
        # a UTC date without a time. Around midnight those can differ, so do
        # not manufacture the report date by subtracting one from `updated`.
        "chat_updated": chat_date,
    }


def build(traffic, chat, mobile=False):
    """Return a four-metric SVG with explicit source periods."""
    T.reset()
    data = metrics(traffic, chat)
    width, height = (480, 520) if mobile else (1000, 312)
    pad, gap = (24, 16) if mobile else (32, 16)
    columns = 2 if mobile else 4
    cell_width = (width - 2 * pad - (columns - 1) * gap) / columns
    cell_height = 144 if mobile else 136
    cards = []
    items = [
        ("requests", "EDGE REQUESTS", "30 DAYS", "cyan"),
        ("visitors", "UNIQUE VISITORS", "30 DAYS", "violet"),
        ("messages", "CHAT MESSAGES", "ONE DAY", "pink"),
        ("calls", "CALLS CONNECTED", "ONE DAY", "green"),
    ]
    for index, (key, label, period, color) in enumerate(items):
        x = pad + (index % columns) * (cell_width + gap)
        y = (98 if mobile else 104) + (index // columns) * (cell_height + gap)
        value = data[key]
        exact = f"{value:,}" if value is not None else "not reported"
        detail = f"~{value / (30 * 86400):.1f} req/s average" if key == "requests" and value is not None else exact
        cards.extend([
            f'<g><title>{html.escape(label.title())}: {exact}; {period.lower()}</title>',
            f'<rect class="cell" x="{x}" y="{y}" width="{cell_width}" height="{cell_height}" rx="14"/>',
            f'<path class="accent {color}" d="M{x + 18} {y + 19}h18"/>',
            T.run("mono", period, 10, x + cell_width - 17, y + 23, .3, anchor="end", cls="muted"),
            T.run("display", compact(value), 45 if mobile else 47, x + 17, y + 79, cls=color),
            T.run("mono", label, 11, x + 18, y + 101, .2, cls="primary"),
            T.run("mono", detail, 10.2, x + 18, y + 122, cls="muted"),
            '</g>',
        ])

    traffic_period = (f'{data["traffic_start"].isoformat()} to {data["traffic_end"].isoformat()} UTC'
                      if data["traffic_start"] else "source date unavailable")
    chat_update = f'updated {data["chat_updated"].isoformat()}' if data["chat_updated"] else "update date unavailable"
    chat_period = "last full day, New York / " + chat_update
    if mobile:
        footer = (T.run("mono", "CLOUDFLARE / CURSOR.STYLE", 10.5, pad, 438, .3, cls="secondary")
                  + T.run("mono", traffic_period, 10.5, pad, 457, cls="muted")
                  + T.run("mono", "CHAT / LAST FULL DAY, NEW YORK", 10.5, pad, 482, cls="secondary")
                  + T.run("mono", chat_update, 10.5, pad, 501, cls="muted"))
    else:
        footer = (T.run("mono", "Cloudflare / cursor.style / " + traffic_period, 11, pad, 270, cls="secondary")
                  + T.run("mono", "chat.cursor.style / " + chat_period, 11, pad, 291, cls="secondary"))
    heading = T.run("display", "Built here. Used out there.", 28 if mobile else 31, pad, 47, cls="primary")
    subtitle = T.run("text", "Real products. Real usage. A daily snapshot.", 15 if mobile else 16, pad, 75, cls="secondary")
    description = (
        f'Cloudflare traffic for cursor.style, {traffic_period}: '
        f'{data["requests"] if data["requests"] is not None else "unavailable"} requests and '
        f'{data["visitors"] if data["visitors"] is not None else "unavailable"} unique visitors. '
        f'Chat for {chat_period}: '
        f'{data["messages"] if data["messages"] is not None else "unavailable"} messages and '
        f'{data["calls"] if data["calls"] is not None else "unavailable"} connected calls. '
        'A dated snapshot, not live telemetry.'
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
  viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">Built here. Used out there.</title><desc id="desc">{html.escape(description)}</desc>
  <defs>
    <linearGradient id="sky" x2=".5" y2="1"><stop stop-color="#070C20"/><stop offset="1" stop-color="#101135"/></linearGradient>
    <linearGradient id="spectrum"><stop stop-color="#38BDF8"/><stop offset=".5" stop-color="#8B5CF6"/><stop offset="1" stop-color="#EC4899"/></linearGradient>
    <clipPath id="frame"><rect width="{width}" height="{height}" rx="20"/></clipPath>
    {T.defs()}
  </defs>
  <style>
    .primary {{ fill:#EDF2FF }} .secondary {{ fill:#A5B3D6 }} .muted {{ fill:#8296C1 }}
    .cyan {{ fill:#65D4FF; stroke:#65D4FF }} .violet {{ fill:#B59AFF; stroke:#B59AFF }}
    .pink {{ fill:#F392CD; stroke:#F392CD }} .green {{ fill:#7AE3C0; stroke:#7AE3C0 }}
    g.cyan, g.violet, g.pink, g.green {{ stroke:none }}
    .cell {{ fill:#101932; stroke:#263150; stroke-width:1 }}
    .accent {{ stroke-width:3; stroke-linecap:round }}
  </style>
  <g clip-path="url(#frame)"><rect width="{width}" height="{height}" fill="url(#sky)"/>
    <rect y="{height - 4}" width="{width}" height="4" fill="url(#spectrum)"/></g>
  {heading}{subtitle}{"".join(cards)}{footer}
</svg>
'''


def read_snapshot(path):
    # An unavailable source can be represented truthfully while a first sync is
    # being configured. Malformed existing JSON still fails the build loudly.
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


if __name__ == "__main__":
    traffic, chat = read_snapshot(TRAFFIC), read_snapshot(CHAT)
    for output, mobile in ((OUT, False), (MOBILE_OUT, True)):
        output.write_text(build(traffic, chat, mobile=mobile), encoding="utf-8")
        print(f"{output.relative_to(ROOT)} - {output.stat().st_size / 1024:.0f} KB")
