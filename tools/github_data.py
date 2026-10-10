"""Fetch aggregate profile metrics without publishing private repository details.

The GitHub contribution graph counts qualifying commits, not every Git commit.
Classic ``read:user`` (or ``user``) enables private contribution data; ``repo``
also permits reading private repositories. We only describe commit coverage as
complete for the owner's token with both, and no unclassified restricted counts.
Unknown token permissions retain the conservative ``visible`` scope.
"""

import collections
import datetime as dt
import json
import urllib.error
import urllib.request


USER = "wonchoe"
TOP_LANGUAGES = 6
UTC = dt.timezone.utc


class _GitHub:
    def __init__(self, token):
        self.token = token
        self.scopes = None

    def request(self, path, payload=None):
        request = urllib.request.Request(
            "https://api.github.com/" + path,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "User-Agent": f"{USER}-profile-card",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                scopes = response.headers.get("X-OAuth-Scopes")
                if scopes is not None and scopes.strip():
                    self.scopes = {scope.strip() for scope in scopes.split(",") if scope.strip()}
                return json.load(response)
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"GitHub API request failed (HTTP {error.code})") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise RuntimeError("GitHub API request failed (network error)") from None
        except (ValueError, UnicodeError):
            raise RuntimeError("GitHub API returned an invalid response") from None

    def graphql(self, query, variables):
        body = self.request("graphql", {"query": query, "variables": variables})
        if not isinstance(body, dict) or body.get("errors") or not body.get("data"):
            # GraphQL errors may contain repository names or other private data.
            raise RuntimeError("GitHub GraphQL request failed; check token permissions")
        return body["data"]


def _iso(value):
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _count(value):
    if type(value) is not int or value < 0:
        raise RuntimeError("GitHub returned an invalid metric")
    return value


def _contribution_scope(scopes, is_owner, restricted):
    if scopes is None:
        return "visible"
    has_user = bool({"user", "read:user"} & scopes)
    if is_owner and has_user and "repo" in scopes and restricted == 0:
        return "all"
    if not has_user and restricted == 0:
        return "public"
    return "visible"


def _repository_metrics(api, user, is_owner):
    public = _count(user["publicRepositories"]["totalCount"])
    private = _count(user["privateRepositories"]["totalCount"])
    total = _count(user["repositories"]["totalCount"])
    if total != public + private:
        raise RuntimeError("GitHub repository counts are inconsistent")
    scopes = api.scopes
    if is_owner and scopes is not None and "repo" in scopes:
        return {"total": total, "public": public, "private": private, "scope": "all"}

    # read:user can supply the complete count without granting code access.
    if is_owner and scopes is not None and {"user", "read:user"} & scopes:
        try:
            profile = api.request("user")
        except RuntimeError:
            profile = {}
        owned_private = profile.get("owned_private_repos")
        public_count = profile.get("public_repos")
        if (profile.get("login", "").casefold() == USER.casefold()
                and type(owned_private) is int and owned_private >= 0
                and type(public_count) is int and public_count >= 0):
            return {"total": public_count + owned_private, "public": public_count,
                    "private": owned_private, "scope": "all"}

    # An app or fine-grained token may cover only selected private repositories.
    scope = "public" if scopes is not None and private == 0 else "visible"
    return {"total": total, "public": public,
            "private": private if private else None, "scope": scope}


LANGUAGE_FIELDS = """
    edges { size node { name color } }
    pageInfo { hasNextPage endCursor }
"""


def _language_metrics(api):
    sizes, colors = collections.Counter(), {}

    def add(connection):
        for edge in connection["edges"]:
            name = edge["node"]["name"]
            sizes[name] += _count(edge["size"])
            colors[name] = edge["node"]["color"] or "#8B98B5"

    def next_cursor(connection, previous):
        info = connection["pageInfo"]
        if not info["hasNextPage"]:
            return None
        cursor = info["endCursor"]
        if not cursor or cursor == previous:
            raise RuntimeError("GitHub returned invalid pagination")
        return cursor

    cursor = None
    while True:
        data = api.graphql("""
            query($login: String!, $after: String) {
              user(login: $login) {
                repositories(first: 100, after: $after, ownerAffiliations: [OWNER],
                             isFork: false, privacy: PUBLIC) {
                  pageInfo { hasNextPage endCursor }
                  nodes { id languages(first: 100) { """ + LANGUAGE_FIELDS + """ } }
                }
              }
            }
        """, {"login": USER, "after": cursor})
        repositories = data["user"]["repositories"]
        for repository in repositories["nodes"]:
            languages = repository["languages"]
            add(languages)
            language_cursor = next_cursor(languages, None)
            while language_cursor is not None:
                extra = api.graphql("""
                    query($id: ID!, $after: String!) {
                      node(id: $id) { ... on Repository {
                        languages(first: 100, after: $after) { """ + LANGUAGE_FIELDS + """ }
                      } }
                    }
                """, {"id": repository["id"], "after": language_cursor})
                languages = extra["node"]["languages"]
                add(languages)
                language_cursor = next_cursor(languages, language_cursor)
        cursor = next_cursor(repositories, cursor)
        if cursor is None:
            break

    total = sum(sizes.values())
    if not total:
        return []
    top = sorted(sizes.items(), key=lambda item: (-item[1], item[0]))[:TOP_LANGUAGES]
    result = [{"name": name, "share": size / total, "color": colors[name]}
              for name, size in top]
    remainder = total - sum(size for _, size in top)
    if remainder:
        result.append({"name": "Other", "share": remainder / total, "color": "#5B6785"})
    return result


def fetch(token, now=None):
    """Return schema v2 aggregates; ``now`` is an optional UTC-aware datetime."""
    if (not isinstance(token, str) or not token or not token.isascii()
            or any(char.isspace() for char in token)):
        raise ValueError("A GitHub token is required")
    now = now or dt.datetime.now(UTC)
    if not isinstance(now, dt.datetime):
        raise ValueError("now must be a datetime")
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    now = now.astimezone(UTC).replace(microsecond=0)
    api = _GitHub(token)
    metadata = api.graphql("""
        query($login: String!) {
          viewer { login }
          user(login: $login) {
            createdAt
            contributionsCollection { contributionYears }
            repositories(ownerAffiliations: [OWNER]) { totalCount }
            publicRepositories: repositories(ownerAffiliations: [OWNER], privacy: PUBLIC) { totalCount }
            privateRepositories: repositories(ownerAffiliations: [OWNER], privacy: PRIVATE) { totalCount }
          }
        }
    """, {"login": USER})
    user = metadata.get("user")
    if not user:
        raise RuntimeError("GitHub profile was not found")
    created = dt.datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00"))
    if now < created:
        raise ValueError("now cannot precede the GitHub account creation date")
    is_owner = metadata["viewer"]["login"].casefold() == USER.casefold()
    repositories = _repository_metrics(api, user, is_owner)

    # Imported Git history can predate the GitHub account itself. Use the API's
    # actual contribution years while retaining every intervening empty year.
    contribution_years = user["contributionsCollection"]["contributionYears"]
    if (not isinstance(contribution_years, list)
            or any(type(year) is not int or not 1 <= year <= 9999
                   for year in contribution_years)):
        raise RuntimeError("GitHub returned invalid contribution years")
    first_year = min([created.year, *contribution_years])

    # The API permits at most one year per collection. UTC calendar windows do
    # not overlap, including leap years, and preserve years with no activity.
    years, restricted_total, contributions_total = [], 0, 0
    for batch_start in range(first_year, now.year + 1, 10):
        declarations = ["$login: String!"]
        fields = []
        variables = {"login": USER}
        for year in range(batch_start, min(batch_start + 10, now.year + 1)):
            declarations.extend([f"$from{year}: DateTime!", f"$to{year}: DateTime!"])
            variables[f"from{year}"] = _iso(dt.datetime(year, 1, 1, tzinfo=UTC))
            variables[f"to{year}"] = _iso(min(now, dt.datetime(year, 12, 31, 23, 59, 59, tzinfo=UTC)))
            fields.append(f"y{year}: contributionsCollection(from: $from{year}, to: $to{year})"
                          " { totalCommitContributions restrictedContributionsCount"
                          " contributionCalendar { totalContributions } }")
        query = ("query(" + ", ".join(declarations) + ") { user(login: $login) { "
                 + " ".join(fields) + " } }")
        annual = api.graphql(query, variables)["user"]
        for year in range(batch_start, min(batch_start + 10, now.year + 1)):
            collection = annual[f"y{year}"]
            years.append({"year": year, "commits": _count(collection["totalCommitContributions"])})
            restricted_total += _count(collection["restrictedContributionsCount"])
            # Calendar totals already include any disclosed restricted activity.
            contributions_total += _count(collection["contributionCalendar"]["totalContributions"])

    commits_total = sum(year["commits"] for year in years)
    contribution_scope = _contribution_scope(api.scopes, is_owner, restricted_total)
    return {
        "schema_version": 2,
        "updated": now.date().isoformat(),
        "since": created.date().isoformat(),
        "repositories": repositories,
        "commits": {"total": commits_total, "scope": contribution_scope},
        "activity": {
            "total": contributions_total,
            "commits": commits_total,
            "restricted": restricted_total,
            "scope": contribution_scope,
            "period": "all_time",
            "from": dt.date(first_year, 1, 1).isoformat(),
            "to": now.date().isoformat(),
        },
        "years": years,
        "languages": _language_metrics(api),
        "language_scope": "public",
    }
