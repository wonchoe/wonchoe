#!/usr/bin/env python3
"""Refresh the GitHub snapshot, both card sizes and the accessible README text.

PROFILE_STATS_TOKEN takes precedence over GITHUB_TOKEN / GH_TOKEN. With no
token (or --offline), rebuild the committed snapshot without network access.
Only aggregate counts and language percentages are written to disk.
"""
import argparse
import html
import json
import os
import pathlib
import re

from github_card import build, summary
from github_data import fetch

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "assets" / "github.json"
START = "<!-- GH-STATS:START -->"
END = "<!-- GH-STATS:END -->"


def normalize_cache(data):
    """Old snapshots contain no all-time commit count; never infer one."""
    if data.get("schema_version") == 2:
        return data
    return {
        "schema_version": 2,
        "updated": data["updated"],
        "since": data["since"],
        "repositories": {
            "total": data["repos"], "public": data["repos"],
            "private": None, "scope": "public", "includes_forks": False,
        },
        "commits": {"total": None, "scope": "public"},
        "activity": {
            "total": data["contributions"], "commits": None,
            "restricted": 0, "scope": "public",
        },
        "years": [],
        "languages": data["languages"],
        "language_scope": "public",
    }


def keep_broader_cache(previous, current):
    """A repo-scoped workflow token must not replace owner totals with a subset."""
    return (previous.get("language_scope") == "all" and current.get("language_scope") != "all") or any(
        previous[key]["scope"] == "all" and current[key]["scope"] != "all"
        for key in ("repositories", "commits", "activity")
    )


def readme_block(data):
    description = html.escape(summary(data), quote=True)
    readable = html.escape(summary(data, details=False), quote=True)
    language_coverage = "public and private" if data.get("language_scope") == "all" else "public"
    return f'''{START}

<div align="center">
  <picture>
    <source media="(max-width: 600px)" srcset="assets/github-mobile.svg">
    <img src="assets/github.svg" width="100%" alt="{description}">
  </picture>
</div>

{readable}

<sub>Commit counts follow <a href="https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference">GitHub contribution rules</a>; they are not a count of every commit on every branch. Languages reflect {language_coverage}, non-fork repositories. Snapshot: {data["updated"]} (UTC).</sub>

{END}'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Render the cached snapshot only")
    args = parser.parse_args()
    previous = normalize_cache(json.loads(DATA.read_text(encoding="utf-8"))) if DATA.exists() else None
    data = previous
    token = None if args.offline else (
        os.environ.get("PROFILE_STATS_TOKEN") or os.environ.get("GITHUB_TOKEN")
        or os.environ.get("GH_TOKEN")
    )
    if token:
        try:
            current = fetch(token)
            if previous and keep_broader_cache(previous, current):
                print("GitHub token has narrower access than the cached snapshot; keeping its counts and date. "
                      "Configure PROFILE_STATS_TOKEN with owner access (repo + read:user).")
            else:
                data = current
        except Exception as error:
            if previous is None:
                raise
            # Do not include API response bodies or credentials in workflow logs.
            print(f"GitHub refresh failed ({type(error).__name__}); keeping the previous snapshot and date.")
    if data is None:
        raise RuntimeError("No GitHub snapshot; configure PROFILE_STATS_TOKEN for the first refresh")

    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r"[\s\S]*?" + re.escape(END))
    if readme.count(START) != 1 or readme.count(END) != 1 or not pattern.search(readme):
        raise RuntimeError("Exactly one ordered GH-STATS marker pair is required in README.md")
    desktop, mobile = build(data), build(data, mobile=True)
    readme = pattern.sub(lambda _: readme_block(data), readme)

    DATA.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    for name, svg in (("github.svg", desktop), ("github-mobile.svg", mobile)):
        path = ROOT / "assets" / name
        path.write_text(svg, encoding="utf-8")
        print(f"{path.relative_to(ROOT)} - {path.stat().st_size / 1024:.0f} KB")
    readme_path.write_text(readme, encoding="utf-8")


if __name__ == "__main__":
    main()
