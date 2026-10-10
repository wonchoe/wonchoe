"""Offline regressions for honest GitHub metrics and self-contained cards.

Run with: python3 -m unittest discover -s tests -v
"""
import copy
import datetime as dt
import io
import json
import pathlib
import sys
import unittest
from unittest import mock
import xml.etree.ElementTree as ET


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import github_card
import github_data
import build_github_card


UTC = dt.timezone.utc
NOW = dt.datetime(2024, 10, 10, 12, tzinfo=UTC)
SVG = "{http://www.w3.org/2000/svg}"


def connection(edges=None, nodes=None, next_cursor=None):
    result = {"pageInfo": {"hasNextPage": next_cursor is not None,
                           "endCursor": next_cursor}}
    if edges is not None:
        result["edges"] = edges
    if nodes is not None:
        result["nodes"] = nodes
    return result


def language(name, size, color="#123456"):
    return {"size": size, "node": {"name": name, "color": color}}


class GitHubFixture:
    """Serve realistic REST/GraphQL envelopes through the HTTP boundary."""

    def __init__(self, scopes="repo, read:user", owner=True, private=3):
        self.scopes = scopes
        self.owner = owner
        self.private = private
        self.created = "2022-06-01T09:00:00Z"
        self.annual = {2022: 3, 2023: 8, 2024: 17}
        self.annual_contributions = {2022: 11, 2023: 23, 2024: 41}
        self.contribution_years = None
        self.annual_restricted = 0
        self.rest_profile = {"login": "wonchoe", "public_repos": 4,
                             "owned_private_repos": 39}
        self.repo_pages = {
            None: connection(nodes=[{"id": "public-repo-1", "languages":
                                     connection(edges=[language("JavaScript", 30)])}])
        }
        self.language_pages = {}
        self.calls = []
        self.graphql_errors = None

    def __call__(self, request, timeout):
        path = request.full_url.removeprefix("https://api.github.com/")
        payload = json.loads(request.data) if request.data else None
        self.calls.append((path, payload))
        if path == "user":
            body = self.rest_profile
        elif path == "graphql":
            variables, query = payload["variables"], payload["query"]
            if self.graphql_errors:
                body = {"errors": self.graphql_errors}
            elif "createdAt" in query:
                body = {"data": {"viewer": {"login": "wonchoe" if self.owner else "other"},
                                 "user": {"createdAt": self.created,
                                          "contributionsCollection": {
                                              "contributionYears": self.contribution_years
                                              if self.contribution_years is not None
                                              else sorted(self.annual, reverse=True)},
                                          "repositories": {"totalCount": 4 + self.private},
                                          "publicRepositories": {"totalCount": 4},
                                          "privateRepositories": {"totalCount": self.private}}}}
            elif any(key.startswith("from") and key[4:].isdigit() for key in variables):
                years = [int(key[4:]) for key in variables
                         if key.startswith("from") and key[4:].isdigit()]
                body = {"data": {"user": {
                    f"y{year}": {"totalCommitContributions": self.annual[year],
                                "restrictedContributionsCount": self.annual_restricted,
                                "contributionCalendar": {"totalContributions":
                                    self.annual_contributions.get(year, self.annual[year] * 2)}}
                    for year in years if year in self.annual}}}
            elif "id" in variables:
                body = {"data": {"node": {"languages": self.language_pages[
                    (variables["id"], variables["after"])]}}}
            elif "after" in variables:
                body = {"data": {"user": {"repositories":
                                          self.repo_pages[variables["after"]]}}}
            else:
                raise AssertionError("Unexpected GraphQL operation")
        else:
            raise AssertionError(f"Unexpected API path: {path}")
        response = io.StringIO(json.dumps(body))
        response.headers = {} if self.scopes is None else {"X-OAuth-Scopes": self.scopes}
        return response

    def fetch(self, now=NOW):
        with mock.patch.object(github_data.urllib.request, "urlopen", side_effect=self):
            return github_data.fetch("test-token", now=now)


class GitHubDataTests(unittest.TestCase):
    def test_all_time_commits_and_contributions_are_distinct_sums_of_every_year(self):
        api = GitHubFixture()
        api.annual[2023] = 0
        data = api.fetch()
        self.assertEqual(data["commits"], {"total": 20, "scope": "all"})
        self.assertEqual(data["years"], [{"year": 2022, "commits": 3},
                                         {"year": 2023, "commits": 0},
                                         {"year": 2024, "commits": 17}])
        self.assertEqual(data["activity"]["total"], 75)
        self.assertEqual(data["activity"]["commits"], 20)
        self.assertEqual(data["activity"]["period"], "all_time")
        self.assertEqual(data["activity"]["from"], "2022-01-01")
        self.assertEqual(data["activity"]["to"], "2024-10-10")
        self.assertEqual(data["repositories"],
                         {"total": 7, "public": 4, "private": 3, "scope": "all"})
        metadata_query = api.calls[0][1]["query"]
        self.assertNotIn("isFork", metadata_query, "Owned repository total must include forks")

    def test_restricted_activity_is_not_added_to_commits_or_calendar_twice(self):
        api = GitHubFixture()
        api.annual_restricted = 11
        data = api.fetch()
        self.assertEqual(data["commits"]["total"], 28)
        self.assertEqual(data["activity"]["total"], 75)
        self.assertEqual(data["activity"]["restricted"], 33)
        self.assertEqual(data["commits"]["scope"], "visible")
        self.assertEqual(data["activity"]["scope"], "visible")

    def test_imported_commits_before_account_creation_are_included_in_all_time(self):
        api = GitHubFixture()
        api.created = "2020-06-01T09:00:00Z"
        api.annual = {2018: 5, 2019: 0, 2020: 3, 2021: 0, 2022: 3, 2023: 8, 2024: 17}
        api.contribution_years = [2024, 2023, 2022, 2020, 2018]
        data = api.fetch()
        self.assertEqual(data["since"], "2020-06-01")
        self.assertEqual(data["commits"]["total"], 36)
        self.assertEqual(data["years"], [
            {"year": year, "commits": commits} for year, commits in api.annual.items()
        ])
        self.assertEqual(data["activity"]["total"], 91)

    def test_selected_repo_and_unknown_tokens_cannot_claim_all_repositories(self):
        for scopes, private, owner, expected in [
            (None, 3, True, "visible"),
            (None, 0, True, "visible"),
            ("", 0, True, "visible"),
            ("public_repo", 0, True, "public"),
            ("repo, read:user", 3, False, "visible"),
        ]:
            with self.subTest(scopes=scopes, private=private, owner=owner):
                data = GitHubFixture(scopes=scopes, private=private, owner=owner).fetch()
                self.assertEqual(data["repositories"]["scope"], expected)
                self.assertNotEqual(data["commits"]["scope"], "all")

    def test_owner_read_user_can_supply_repo_total_without_private_code_access(self):
        data = GitHubFixture(scopes="read:user", private=0).fetch()
        self.assertEqual(data["repositories"],
                         {"total": 43, "public": 4, "private": 39, "scope": "all"})
        self.assertEqual(data["commits"]["scope"], "visible")

    def test_missing_private_count_is_unknown_instead_of_zero(self):
        api = GitHubFixture(scopes="read:user", private=0)
        api.rest_profile = {"login": "wonchoe", "public_repos": 4}
        data = api.fetch()
        self.assertIsNone(data["repositories"]["private"])
        self.assertEqual(data["repositories"]["scope"], "public")

    def test_language_bytes_include_both_repository_and_language_pages(self):
        api = GitHubFixture()
        api.repo_pages = {
            None: connection(nodes=[{"id": "public-repo-1", "languages": connection(
                edges=[language("JavaScript", 30)], next_cursor="more-languages")}],
                next_cursor="more-repos"),
            "more-repos": connection(nodes=[{"id": "public-repo-2", "languages":
                connection(edges=[language("JavaScript", 30), language("HTML", 30)])}]),
        }
        api.language_pages[("public-repo-1", "more-languages")] = connection(
            edges=[language("PHP", 10, None)])
        data = api.fetch()
        shares = {row["name"]: row["share"] for row in data["languages"]}
        self.assertEqual(shares, {"JavaScript": .6, "HTML": .3, "PHP": .1})
        self.assertAlmostEqual(sum(shares.values()), 1)
        self.assertEqual(data["language_scope"], "all")
        for path, payload in api.calls:
            if path == "graphql" and "after" in payload["variables"] and "id" not in payload["variables"]:
                self.assertIsNone(payload["variables"]["privacy"])
                self.assertIn("isFork: false", payload["query"])

    def test_private_languages_require_the_owner_token_with_repo_access(self):
        for scopes, owner in [("read:user", True), (None, True), ("repo", False)]:
            with self.subTest(scopes=scopes, owner=owner):
                api = GitHubFixture(scopes=scopes, owner=owner)
                data = api.fetch()
                self.assertEqual(data["language_scope"], "public")
                language_requests = [payload for path, payload in api.calls
                                     if path == "graphql" and "privacy" in payload["variables"]]
                self.assertTrue(language_requests)
                self.assertTrue(all(request["variables"]["privacy"] == "PUBLIC"
                                    for request in language_requests))

    def test_invalid_pagination_fails_instead_of_looping_or_omitting_data(self):
        api = GitHubFixture()
        api.repo_pages = {
            None: connection(nodes=[], next_cursor="same-cursor"),
            "same-cursor": connection(nodes=[], next_cursor="same-cursor"),
        }
        with self.assertRaisesRegex(RuntimeError, "pagination"):
            api.fetch()

    def test_missing_year_cannot_silently_create_a_partial_all_time_total(self):
        api = GitHubFixture()
        del api.annual[2023]
        with self.assertRaises((RuntimeError, KeyError)):
            api.fetch()

    def test_api_errors_do_not_publish_private_details(self):
        api = GitHubFixture()
        api.graphql_errors = [{"message": "Private secret-org/secret-repo denied"}]
        with self.assertRaises(RuntimeError) as result:
            api.fetch()
        self.assertNotIn("secret", str(result.exception))
        self.assertNotIn("test-token", str(result.exception))

    def test_calendar_year_requests_cover_each_year_without_overlap(self):
        api = GitHubFixture()
        api.created = "2013-09-12T00:00:00Z"
        api.annual = {year: year - 2013 for year in range(2013, 2025)}
        data = api.fetch()
        periods = []
        for path, payload in api.calls:
            if path != "graphql":
                continue
            variables = payload["variables"]
            for key, value in variables.items():
                if key.startswith("from") and key[4:].isdigit():
                    start = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
                    end = dt.datetime.fromisoformat(variables["to" + key[4:]].replace("Z", "+00:00"))
                    self.assertLess(end, start.replace(year=start.year + 1))
                    periods.append((start, end))
        periods.sort()
        self.assertEqual(len(periods), 12)
        for previous, following in zip(periods, periods[1:]):
            self.assertEqual(previous[1] + dt.timedelta(seconds=1), following[0])
        self.assertEqual(periods[-1][1], NOW)
        self.assertEqual(data["commits"]["total"], sum(api.annual.values()))

    def test_leap_day_refresh_closes_current_calendar_year_at_today(self):
        api = GitHubFixture()
        now = dt.datetime(2024, 2, 29, 12, tzinfo=UTC)
        data = api.fetch(now=now)
        annual = next(payload["variables"] for path, payload in api.calls
                      if path == "graphql" and "from2024" in payload["variables"])
        start = dt.datetime.fromisoformat(annual["from2024"].replace("Z", "+00:00"))
        end = dt.datetime.fromisoformat(annual["to2024"].replace("Z", "+00:00"))
        self.assertEqual(start, dt.datetime(2024, 1, 1, tzinfo=UTC))
        self.assertLessEqual(end - start, dt.timedelta(days=366))
        self.assertEqual(end, now)
        self.assertEqual(data["activity"]["to"], "2024-02-29")
        self.assertEqual(data["updated"], "2024-02-29")

    def test_invalid_tokens_fail_before_any_network_request(self):
        for token in ("", "   ", "bad\ntoken", "bad token", "токен"):
            with self.subTest(token=token):
                with mock.patch.object(github_data.urllib.request, "urlopen") as request:
                    with self.assertRaises(ValueError) as result:
                        github_data.fetch(token, now=NOW)
                    request.assert_not_called()
                    if token.strip():
                        self.assertNotIn(token, str(result.exception))


class GitHubCardTests(unittest.TestCase):
    def setUp(self):
        self.data = GitHubFixture().fetch()

    def parse_card(self, data, mobile=False):
        root = ET.fromstring(github_card.build(data, mobile=mobile))
        ids = {node.attrib["id"] for node in root.iter() if "id" in node.attrib}
        for node in root.iter():
            reference = node.attrib.get("href")
            if reference:
                self.assertTrue(reference.startswith("#"), "Cards must not fetch external assets")
                self.assertIn(reference[1:], ids, "Each outlined glyph must be defined in this SVG")
        self.assertEqual(root.attrib["role"], "img")
        for identity in root.attrib["aria-labelledby"].split():
            self.assertIn(identity, ids)
        description = root.find(SVG + "desc")
        self.assertIsNotNone(description)
        self.assertEqual(description.text, github_card.summary(data))
        return root

    def test_desktop_and_mobile_are_self_contained_and_have_same_accessible_metrics(self):
        for mobile, width in [(False, 1000), (True, 480)]:
            with self.subTest(mobile=mobile):
                root = self.parse_card(self.data, mobile=mobile)
                self.assertEqual(int(root.attrib["width"]), width)
        text = github_card.summary(self.data)
        self.assertIn("7 owned repositories, public and private", text)
        self.assertIn("28 all-time GitHub commit contributions", text)
        self.assertIn("75 all-time contributions", text)
        self.assertNotIn("last 12 months", text)

    def test_backend_year_breakdown_has_no_visual_or_accessible_chart(self):
        without_years = copy.deepcopy(self.data)
        without_years.pop("years")
        for mobile in (False, True):
            with self.subTest(mobile=mobile):
                self.assertEqual(github_card.build(self.data, mobile=mobile),
                                 github_card.build(without_years, mobile=mobile))

    def test_old_v2_activity_preserves_last_twelve_month_period_until_refreshed(self):
        data = copy.deepcopy(self.data)
        data["activity"].pop("period")
        self.assertIn("75 contributions in the last 12 months", github_card.summary(data))
        self.assertNotIn("75 all-time contributions", github_card.summary(data))
        self.parse_card(data)

    def test_unknown_history_stays_unknown_and_public_only_scope_stays_public(self):
        data = copy.deepcopy(self.data)
        data["repositories"] = {"total": 4, "public": 4, "private": None, "scope": "public"}
        data["commits"] = {"total": None, "scope": "public"}
        data["activity"]["scope"] = "public"
        data["years"] = []
        data["languages"] = []
        for mobile in (False, True):
            self.parse_card(data, mobile=mobile)
        text = github_card.summary(data)
        self.assertIn("4 public owned repositories", text)
        self.assertRegex(text.lower(), "await|unavailable|unknown|not yet")
        self.assertNotIn("0 all-time", text)
        self.assertNotIn("public and private", text)

    def test_language_names_are_escaped_and_colors_cannot_inject_svg_attributes(self):
        data = copy.deepcopy(self.data)
        data["languages"] = [{"name": 'A&B <language> "quoted"', "share": 1,
                              "color": '#fff\" onload=\"alert(1)'}]
        root = self.parse_card(data)
        self.assertIn('A&B <language> "quoted"', root.find(SVG + "desc").text)
        self.assertFalse(any("onload" in node.attrib for node in root.iter()))


class GitHubCacheTests(unittest.TestCase):
    def test_legacy_calendar_count_is_never_relabelled_as_all_time_commits(self):
        legacy = {"updated": "2024-10-09", "since": "2022-06-01", "repos": 4,
                  "contributions": 91, "languages": []}
        original = copy.deepcopy(legacy)
        normalized = build_github_card.normalize_cache(legacy)
        self.assertEqual(legacy, original)
        self.assertEqual(normalized["activity"]["total"], 91)
        self.assertIsNone(normalized["commits"]["total"])
        self.assertEqual(normalized["years"], [])
        self.assertIsNone(normalized["repositories"]["private"])
        self.assertEqual(normalized["repositories"]["scope"], "public")
        self.assertIn("91 contributions in the last 12 months", github_card.summary(normalized))
        for mobile in (False, True):
            ET.fromstring(github_card.build(normalized, mobile=mobile))

    def test_narrower_token_does_not_replace_previously_complete_counts(self):
        previous = GitHubFixture().fetch()
        languages_only = copy.deepcopy(previous)
        languages_only["language_scope"] = "public"
        self.assertTrue(build_github_card.keep_broader_cache(previous, languages_only))
        for key in ("repositories", "commits", "activity"):
            for narrower_scope in ("public", "visible"):
                with self.subTest(metric=key, scope=narrower_scope):
                    current = copy.deepcopy(previous)
                    current[key]["scope"] = narrower_scope
                    self.assertTrue(build_github_card.keep_broader_cache(previous, current))

    def test_authorized_count_changes_and_scope_upgrades_are_accepted(self):
        previous = GitHubFixture().fetch()
        current = copy.deepcopy(previous)
        current["repositories"]["total"] -= 1
        current["repositories"]["private"] -= 1
        current["activity"]["total"] -= 10
        self.assertFalse(build_github_card.keep_broader_cache(previous, current))
        for key in ("repositories", "commits", "activity"):
            previous[key]["scope"] = "public"
        self.assertFalse(build_github_card.keep_broader_cache(previous, current))


if __name__ == "__main__":
    unittest.main()
