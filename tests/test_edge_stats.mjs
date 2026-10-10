import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { normalize, period, refresh } from "../tools/fetch_edge_stats.mjs";

const NOW = new Date("2026-10-10T01:00:00Z");
const ENV = { CLOUDFLARE_API_TOKEN: "synthetic-token", CLOUDFLARE_ZONE_ID: "0".repeat(32) };

function response() {
  return { data: { viewer: { zones: [{ audience: [{ sum: {
    requests: 1000, cachedRequests: 800, bytes: 10_000, cachedBytes: 7000,
    countryMap: [
      { clientCountryName: "US", requests: 400 },
      { clientCountryName: "UA", requests: 200 },
      { clientCountryName: "US", requests: 100 },
      { clientCountryName: "DE", requests: 50 },
      { clientCountryName: "FR", requests: 0 },
      { clientCountryName: "XX", requests: 100 },
      { clientCountryName: "T1", requests: 50 },
      { clientCountryName: "ZZ", requests: 100 },
    ],
  } }] }] } } };
}

function outputPath(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "profile-edge-test-"));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  return path.join(dir, "edge.json");
}

test("period includes exactly 30 completed UTC days, including leap day", () => {
  assert.deepEqual(period(NOW), { start: "2026-09-10", end: "2026-10-09", days: 30 });
  assert.deepEqual(period(new Date("2024-03-01T23:59:59Z")), {
    start: "2024-01-31", end: "2024-02-29", days: 30,
  });
  assert.deepEqual(period(new Date("2026-10-09T21:00:00-04:00")), period(NOW));
});

test("country counts combine duplicate codes and exclude unknown/bot-location codes", () => {
  const snapshot = normalize(response(), NOW);
  assert.deepEqual(snapshot.countries.map(({ code, requests }) => ({ code, requests })), [
    { code: "US", requests: 500 }, { code: "UA", requests: 200 }, { code: "DE", requests: 50 },
  ]);
  assert.equal(snapshot.unknownRequests, 250);
  assert.equal(snapshot.countries[0].requests / snapshot.totals.requests, 0.5);
  assert.equal(snapshot.totals.cachedRequests / snapshot.totals.requests, 0.8);
  assert.equal(snapshot.totals.cachedBytes / snapshot.totals.bytes, 0.7);
});

test("missing or invalid aggregates never become invented zeros", () => {
  assert.throws(() => normalize({ errors: [{ message: "upstream details" }] }, NOW), /GraphQL rejected/);
  assert.throws(() => normalize({ data: { viewer: { zones: [] } } }, NOW), /aggregate missing/);
  for (const value of [null, undefined, -1, 1.2, "10", NaN, Infinity]) {
    const body = response();
    body.data.viewer.zones[0].audience[0].sum.requests = value;
    assert.throws(() => normalize(body, NOW), /invalid aggregate/);
  }
  const body = response();
  body.data.viewer.zones[0].audience[0].sum.cachedRequests = 1001;
  assert.throws(() => normalize(body, NOW), /inconsistent aggregate/);
  body.data.viewer.zones[0].audience[0].sum.cachedRequests = 800;
  body.data.viewer.zones[0].audience[0].sum.countryMap[0].requests = 1001;
  assert.throws(() => normalize(body, NOW), /inconsistent country totals/);
});

test("a real zero aggregate remains valid", () => {
  const body = response();
  body.data.viewer.zones[0].audience[0].sum = {
    requests: 0, cachedRequests: 0, bytes: 0, cachedBytes: 0, countryMap: [],
  };
  const snapshot = normalize(body, NOW);
  assert.equal(snapshot.totals.requests, 0);
  assert.equal(snapshot.unknownRequests, 0);
  assert.deepEqual(snapshot.countries, []);
});

test("successful refresh requests only zone aggregates and writes only public summary fields", async t => {
  const output = outputPath(t);
  const result = await refresh({ env: ENV, now: NOW, output, fetchImpl: async (url, options) => {
    assert.equal(url, "https://api.cloudflare.com/client/v4/graphql");
    assert.equal(options.headers.Authorization, "Bearer synthetic-token");
    const { query } = JSON.parse(options.body);
    assert.match(query, /date_geq: "2026-09-10", date_leq: "2026-10-09"/);
    assert.match(query, /countryMap \{clientCountryName requests\}/);
    assert.ok(!query.includes("synthetic-token"));
    assert.doesNotMatch(query, /clientIP|clientRequestPath|dimensions/);
    return { ok: true, json: async () => response() };
  } });
  assert.equal(result.refreshed, true);
  const serialized = fs.readFileSync(output, "utf8");
  assert.doesNotMatch(serialized, /synthetic-token|Authorization|zoneTag|countryMap/);
  assert.deepEqual(Object.keys(JSON.parse(serialized)).sort(), [
    "countries", "period", "schemaVersion", "source", "totals", "unknownRequests", "updated",
  ]);
  assert.ok(!fs.existsSync(output + ".tmp"));
});

test("failed refresh preserves original snapshot bytes and date", async t => {
  const output = outputPath(t);
  const previous = JSON.stringify(normalize(response(), NOW), null, 2) + "\n";
  fs.writeFileSync(output, previous);
  const result = await refresh({ env: ENV, output, now: new Date("2026-10-11T01:00:00Z"),
    fetchImpl: async () => ({ ok: false, json: async () => { throw new Error("must not inspect error body"); } }),
  });
  assert.equal(result.refreshed, false);
  assert.equal(result.snapshot.updated, "2026-10-10");
  assert.equal(fs.readFileSync(output, "utf8"), previous);
});

test("first-run failure and missing configuration fail without publishing fake statistics", async t => {
  const output = outputPath(t);
  await assert.rejects(() => refresh({ env: {}, now: NOW, output,
    fetchImpl: async () => { throw new Error("fetch must not run without configuration"); },
  }), /no previous snapshot exists/);
  assert.ok(!fs.existsSync(output));
  await assert.rejects(() => refresh({ env: ENV, now: NOW, output,
    fetchImpl: async () => ({ ok: true, json: async () => ({ errors: [{ message: "private upstream details" }] }) }),
  }), /no previous snapshot exists/);
  assert.ok(!fs.existsSync(output));
});

test("malformed previous snapshot cannot silently count as a successful fallback", async t => {
  const output = outputPath(t);
  fs.writeFileSync(output, "{}");
  await assert.rejects(() => refresh({ env: {}, now: NOW, output }), /no previous snapshot exists/);
  assert.equal(fs.readFileSync(output, "utf8"), "{}");
});
