// Pulls yesterday's and the last 30 days of Cloudflare traffic for cursor.style,
// writes the numbers into README.md and into assets/traffic.json, which
// tools/build_traffic.py turns into the card the README shows.
import fs from "fs";
import fetch from "node-fetch";

const zoneId = process.env.CLOUDFLARE_ZONE_ID;
const apiToken = process.env.CLOUDFLARE_API_TOKEN;
const TRAFFIC_JSON = "assets/traffic.json";

const day = (offset) =>
  new Date(Date.now() + offset * 86400000).toISOString().slice(0, 10);

const FIELDS = `sum { requests pageViews } uniq { uniques }`;
const flat = (g) => ({
  requests: g.sum.requests,
  pageViews: g.sum.pageViews,
  uniques: g.uniq.uniques,
});

async function graphql(query) {
  const res = await fetch("https://api.cloudflare.com/client/v4/graphql", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiToken}`,
    },
    body: JSON.stringify({ query }),
  });
  const body = await res.json();
  if (body.errors?.length) {
    throw new Error("Cloudflare GraphQL: " + JSON.stringify(body.errors));
  }
  return body.data.viewer.zones[0];
}

// The headline figures. Deliberately without `dimensions`, which makes
// Cloudflare collapse the range into a single group - that is what gives a real
// 30-day unique count instead of a sum of daily ones. This query is the whole
// point of the job: if it fails, the run should fail loudly.
async function getTotals() {
  const zone = await graphql(`
  { viewer { zones(filter: { zoneTag: "${zoneId}" }) {
      last24h: httpRequests1dGroups(limit: 1, filter: { date: "${day(-1)}" }) { ${FIELDS} }
      last30d: httpRequests1dGroups(
        limit: 1, filter: { date_geq: "${day(-30)}", date_leq: "${day(0)}" }
      ) { ${FIELDS} }
  } } }`);
  return { last24h: flat(zone.last24h[0]), last30d: flat(zone.last30d[0]) };
}

// The bars on the card. Adding `dimensions` splits the range into one row per
// day. Nice to have, not load-bearing: if it ever breaks, keep yesterday's
// series so the chart degrades to slightly stale rather than to blank.
async function getSeries() {
  try {
    const zone = await graphql(`
    { viewer { zones(filter: { zoneTag: "${zoneId}" }) {
        series: httpRequests1dGroups(
          limit: 40, filter: { date_geq: "${day(-30)}", date_leq: "${day(-1)}" }
        ) { dimensions { date } ${FIELDS} }
    } } }`);
    return zone.series
      .map((g) => ({ date: g.dimensions.date, ...flat(g) }))
      .sort((a, b) => a.date.localeCompare(b.date));
  } catch (err) {
    console.warn("daily series unavailable, keeping the previous one:", err.message);
    try {
      return JSON.parse(fs.readFileSync(TRAFFIC_JSON, "utf8")).days ?? [];
    } catch {
      return [];
    }
  }
}

function writeTrafficJson(stats) {
  fs.mkdirSync("assets", { recursive: true });
  fs.writeFileSync(
    TRAFFIC_JSON,
    JSON.stringify({ updated: day(0), ...stats }, null, 2) + "\n"
  );
}

function writeReadme(stats) {
  const n = (v) => v.toLocaleString("en-US");
  const summary =
    `**${n(stats.last30d.requests)}** requests &nbsp;·&nbsp; ` +
    `**${n(stats.last30d.pageViews)}** page views &nbsp;·&nbsp; ` +
    `**${n(stats.last30d.uniques)}** unique visitors &nbsp; over the last 30 days\n\n` +
    `<sub>Yesterday alone: ${n(stats.last24h.requests)} requests from ` +
    `${n(stats.last24h.uniques)} people. Refreshed ${day(0)} by the workflow above.</sub>`;

  const start = "<!-- CF-STATS:START -->";
  const end = "<!-- CF-STATS:END -->";
  const readme = fs.readFileSync("README.md", "utf8");

  // Missing markers is a real failure. Identical output is not: two runs on the
  // same day, or a quiet day at the edge, both legitimately change nothing.
  if (!readme.includes(start) || !readme.includes(end)) {
    throw new Error("CF-STATS markers missing from README.md");
  }

  fs.writeFileSync(
    "README.md",
    readme.replace(
      new RegExp(`${start}[\\s\\S]*?${end}`, "m"),
      `${start}\n\n${summary}\n\n${end}`
    )
  );
}

const totals = await getTotals();
const days = await getSeries();
writeTrafficJson({ days, ...totals });
writeReadme(totals);
console.log(
  `30d: ${totals.last30d.requests.toLocaleString()} requests, ` +
    `${days.length} days in the series`
);
