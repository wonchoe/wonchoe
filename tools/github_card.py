"""Render the profile's GitHub metrics without fetching or writing any data.

Both layouts use the same scope-aware data. Text is outlined through typeset,
so the cards remain self-contained when GitHub serves them as README images.
"""
import datetime as dt
import html
import re

import typeset as T


SCOPE = {
    "all": "public + private",
    "public": "public activity",
    "visible": "token-visible activity",
}


def _scope(metric):
    return SCOPE.get(metric.get("scope"), "token-visible activity")


def summary(d, details=True):
    """Accessible equivalent of the figures, preserving their actual scope."""
    repositories, commits, activity = (d[k] for k in ("repositories", "commits", "activity"))
    repo_scope = {
        "all": "owned repositories, public and private",
        "public": "public owned repositories",
        "visible": "token-visible owned repositories",
    }.get(repositories.get("scope"), "token-visible owned repositories")
    commit_summary = ("All-time GitHub commit contributions await the first sync"
                      if commits.get("total") is None else
                      f"{commits['total']:,} all-time GitHub commit contributions ({_scope(commits)})")
    activity_label = ("all-time contributions" if activity.get("period") == "all_time"
                      else "contributions in the last 12 months")
    parts = [f"{repositories['total']:,} {repo_scope}", commit_summary,
             f"{activity['total']:,} {activity_label} ({_scope(activity)})"]
    text = "; ".join(parts) + "."
    if not details:
        return text
    text += " Commits follow GitHub contribution rules."
    languages = d.get("languages") or []
    if languages:
        coverage = "Public and private" if d.get("language_scope") == "all" else "Public"
        text += f" {coverage} non-fork repository languages by code size: " + ", ".join(
            f"{lang['name']} {lang['share'] * 100:.1f}%" for lang in languages
        ) + "."
    return text + f" Updated {d['updated']}."


def _text(value, x, y, size=12, role="mono", cls="muted", anchor="start", tracking=0):
    return T.run(role, str(value), size, x, y, tracking, anchor=anchor, cls=cls)


def _fit(value, maximum, size=42):
    width = T.width("display", value, size)
    return min(size, size * maximum / width) if width else size


def _metrics(d, mobile, pad, width):
    repositories, commits, activity = (d[k] for k in ("repositories", "commits", "activity"))
    repo_label = {
        "all": "owned repositories",
        "public": "public repositories",
        "visible": "visible repositories",
    }.get(repositories.get("scope"), "visible repositories")
    private = repositories.get("private")
    if repositories.get("scope") == "public":
        repo_detail = "owned by wonchoe"
    elif private is None:
        repo_detail = f"{repositories['public']:,} public / private unknown"
    else:
        repo_detail = f"{repositories['public']:,} public + {private:,} private"
    if repositories.get("scope") == "visible":
        repo_note = "within token access"
    elif repositories.get("scope") == "all":
        repo_note = "public + private"
    else:
        repo_note = "private count unavailable"

    values = [
        (repositories["total"], repo_label, repo_detail, repo_note),
        (commits["total"], "commit contributions",
         "awaiting first sync" if commits["total"] is None else "all time",
         _scope(commits)),
        (activity["total"], "contributions",
         "all time" if activity.get("period") == "all_time" else "last 12 months",
         _scope(activity)),
    ]
    out = []
    if mobile:
        for i, (value, label, detail, note) in enumerate(values):
            top = 95 + i * 84
            formatted = "--" if value is None else f"{value:,}"
            out.append(_text(formatted, pad, top + 38, _fit(formatted, 156, 42),
                             role="display", cls="figure"))
            out.append(_text(label, 198, top + 14, 13.5, cls="white"))
            out.append(_text(detail, 198, top + 37, 11.4))
            out.append(_text(note, 198, top + 57, 10.7, cls="quiet"))
            if i != 2:
                out.append(f'<path class="rule" d="M{pad} {top + 72}H{width-pad}"/>')
    else:
        column = (width - 2 * pad) / 3
        for i, (value, label, detail, note) in enumerate(values):
            x = pad + i * column
            formatted = "--" if value is None else f"{value:,}"
            out.append(_text(formatted, x, 118, _fit(formatted, column - 24, 42),
                             role="display", cls="figure"))
            out.append(_text(label, x, 143, 13, cls="white"))
            # Preserve a separate period and scope for each activity measure.
            if i == 0:
                out.append(_text(detail, x, 164, 11.5))
                if repositories.get("scope") != "all":
                    out.append(_text(note, x, 182, 10.5, cls="quiet"))
            else:
                out.append(_text(f"{detail} / {note}", x, 164, 11.1))
            if i:
                out.append(f'<path class="rule" d="M{x-25:.1f} 89V175"/>')
    return "".join(out)


def _languages(d, mobile, pad, width, y):
    languages = d.get("languages") or []
    all_languages = d.get("language_scope") == "all"
    heading = "LANGUAGES / PUBLIC + PRIVATE" if all_languages else "PUBLIC REPOSITORY LANGUAGES"
    out = [_text(heading, pad, y, 11.5, cls="section", tracking=.6)]
    if mobile:
        out.append(_text("non-fork repositories / code by bytes", pad, y+20, 10.7))
        bar_y = y + 36
    else:
        out.append(_text("non-fork / code by bytes", width-pad, y, 10.7, anchor="end"))
        bar_y = y + 18
    if not languages:
        out.append(_text("Language data unavailable", pad, bar_y + 15, 12))
        return "".join(out), bar_y + 25

    x, span = pad, width-2*pad
    out.append(f'<clipPath id="languages-clip"><rect x="{pad}" y="{bar_y}" '
               f'width="{span}" height="12" rx="6"/></clipPath>')
    out.append('<g clip-path="url(#languages-clip)">')
    for lang in languages:
        color = lang.get("color") or "#5B6785"
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
            color = "#5B6785"
        length = max(0, min(1, lang["share"])) * span
        out.append(f'<rect x="{x:.2f}" y="{bar_y}" width="{length:.2f}" '
                   f'height="12" fill="{color}"/>')
        x += length
    out.append('</g>')

    x, legend_y = pad, bar_y + 39
    size = 11.5 if mobile else 11
    for lang in languages:
        label = f"{lang['name']} {lang['share'] * 100:.1f}%"
        length = T.width("mono", label, size) + 29
        if x > pad and x + length > width-pad:
            x, legend_y = pad, legend_y + 25
        color = lang.get("color") or "#5B6785"
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
            color = "#5B6785"
        out.append(f'<circle cx="{x+4}" cy="{legend_y-4}" r="3.5" fill="{color}"/>')
        out.append(_text(label, x+15, legend_y, size))
        x += length
    return "".join(out), legend_y


def build(d, mobile=False):
    """Build a desktop or narrow-screen SVG from schema-v2 cached metrics."""
    T.reset()
    width, pad = (480, 28) if mobile else (1000, 52)
    heading = "code, in numbers"
    out = [_text(heading, pad, 47 if mobile else 50, 27,
                 role="display", cls="white")]
    if mobile:
        out.append(_text("GitHub / updated " + d["updated"], pad, 72, 11))
    else:
        out.append(_text("GitHub / updated " + d["updated"], width-pad, 47,
                         11, anchor="end"))
    out.append(_metrics(d, mobile, pad, width))
    languages, y = _languages(d, mobile, pad, width, 365 if mobile else 211)
    out.append(languages)
    y += 29
    out.append(f'<path class="rule" d="M{pad} {y}H{width-pad}"/>')
    since = dt.date.fromisoformat(d["since"]).strftime("%b %Y")
    if mobile:
        out.append(_text("On GitHub since " + since, pad, y + 24, 10.7, cls="quiet"))
        out.append(_text("Commits follow GitHub contribution rules;", pad, y + 46,
                         10.5, cls="quiet"))
        out.append(_text("they do not include every git commit.", pad, y + 64,
                         10.5, cls="quiet"))
        height = y + 88
    else:
        out.append(_text("On GitHub since " + since, pad, y + 24, 10.5, cls="quiet"))
        out.append(_text("Commit counts follow GitHub contribution rules, not every git commit.",
                         width-pad, y + 24, 10, cls="quiet", anchor="end"))
        height = y + 48

    description = html.escape(summary(d), quote=True)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
  viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
  <title id="title">Oleksii Semeniuk on GitHub</title>
  <desc id="description">{description}</desc>
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2=".3" y2="1">
      <stop stop-color="#070C20"/><stop offset="1" stop-color="#0C1132"/>
    </linearGradient>
    <linearGradient id="spectrum" x1="0" y1="0" x2="1" y2="0">
      <stop stop-color="#38BDF8"/><stop offset=".38" stop-color="#6366F1"/>
      <stop offset=".66" stop-color="#A855F7"/><stop offset="1" stop-color="#EC4899"/>
    </linearGradient>
    <radialGradient id="glow">
      <stop stop-color="#4F46E5" stop-opacity=".3"/><stop offset="1" stop-color="#4F46E5" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="frame"><rect width="{width}" height="{height}" rx="20"/></clipPath>
    {T.defs()}
  </defs>
  <style>
    .white,.figure {{ fill:#EDF2FF }}
    .muted {{ fill:#9AAEDB }}
    .quiet {{ fill:#8496C8 }}
    .accent,.section {{ fill:#8AD5FB }}
    .rule {{ fill:none; stroke:#2B3768; stroke-width:1 }}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{width}" height="{height}" fill="url(#sky)"/>
    <ellipse cx="{width*.55:.1f}" cy="{height*.45:.1f}" rx="{width*.6:.1f}"
      ry="{height*.65:.1f}" fill="url(#glow)"/>
    <rect y="{height-4}" width="{width}" height="4" fill="url(#spectrum)"/>
  </g>
  {"".join(out)}
</svg>
'''
