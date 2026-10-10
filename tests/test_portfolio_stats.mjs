import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { normalize } from "../tools/fetch_edge_stats.mjs";
import { collect, discoverZones, mergeSnapshots, refresh } from "../tools/fetch_portfolio_stats.mjs";

const NOW = new Date("2026-10-10T01:00:00Z");
const NEXT_DAY = new Date("2026-10-11T01:00:00Z");
const ENV = { CLOUDFLARE_API_TOKEN: "synthetic-token" };
const IDS = ["a", "b", "c", "d"].map(value => value.repeat(32));

function analytics(id, sum = {}) {
  return { data: { viewer: { zones: [{ zoneTag: id, audience: [{ sum: {
    requests: 100, cachedRequests: 80, bytes: 1000, cachedBytes: 700,
    countryMap: [{ clientCountryName: "US", requests: 60 }, { clientCountryName: "UA", requests: 30 }],
    ...sum,
  } }] }] } } };
}

function zonePage(ids, { page = 1, totalPages = 1, totalCount = ids.length } = {}) {
  return {
    success: true, errors: [],
    result: ids.map(id => ({ id, status: "active", name: `private-${id}.example`, account: { id: "private-account" } })),
    result_info: { count: ids.length, page, per_page: 50, total_pages: totalPages, total_count: totalCount },
  };
}

function ok(body) { return { ok: true, status: 200, json: async () => body }; }
function outputPath(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "profile-portfolio-test-"));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  return path.join(dir, "portfolio.json");
}

function fakeFetch(ids = IDS.slice(0, 2), overrides = {}) {
  return async (url, options) => {
    if (url.startsWith("https://api.cloudflare.com/client/v4/zones?")) return ok(zonePage(ids));
    assert.equal(url, "https://api.cloudflare.com/client/v4/graphql");
    const { query } = JSON.parse(options.body);
    const id = query.match(/zoneTag: "([a-f0-9]+)"/)[1];
    return ok(analytics(id, overrides[id] || {}));
  };
}

function priorSnapshot(ids = IDS.slice(0, 2)) {
  return mergeSnapshots(ids.map(id => normalize(analytics(id), NOW)), ids, NOW);
}

test("discovery follows every page of active accessible zones, without requiring a configured zone ID", async () => {
  const requested = [];
  const zones = await discoverZones({ env: ENV, fetchImpl: async (url, options) => {
    requested.push(url);
    assert.equal(options.headers.Authorization, "Bearer synthetic-token");
    const parsed = new URL(url);
    assert.equal(parsed.searchParams.get("status"), "active");
    assert.equal(parsed.searchParams.get("per_page"), "50");
    const page = Number(parsed.searchParams.get("page"));
    return ok(zonePage(page === 1 ? IDS.slice(0, 2) : IDS.slice(2), { page, totalPages: 2, totalCount: 4 }));
  } });
  assert.deepEqual(zones, IDS);
  assert.equal(requested.length, 2);
});

test("all sites share exact completed UTC dates; totals yield weighted cache percentages and country union", async () => {
  const fetchImpl = fakeFetch(IDS.slice(0, 2), {
    [IDS[1]]: {
      requests: 900, cachedRequests: 90, bytes: 9000, cachedBytes: 1800,
      countryMap: [{ clientCountryName: "US", requests: 100 }, { clientCountryName: "DE", requests: 750 }],
    },
  });
  let queried = 0;
  const snapshot = await collect({ env: ENV, now: NOW, fetchImpl: async (url, options) => {
    if (options.body) {
      const { query } = JSON.parse(options.body);
      assert.match(query, /date_geq: "2026-09-10", date_leq: "2026-10-09"/);
      assert.doesNotMatch(query, /uniq|clientIP|clientRequestPath|dimensions/i);
      queried++;
    }
    return fetchImpl(url, options);
  } });
  assert.equal(queried, 2);
  assert.deepEqual(snapshot.period, { start: "2026-09-10", end: "2026-10-09", days: 30 });
  assert.deepEqual(snapshot.totals, { requests: 1000, cachedRequests: 170, bytes: 10_000, cachedBytes: 2500 });
  assert.equal(snapshot.totals.cachedRequests / snapshot.totals.requests, 0.17);
  assert.notEqual(snapshot.totals.cachedRequests / snapshot.totals.requests, (0.8 + 0.1) / 2);
  assert.deepEqual(snapshot.countries.map(({ code, requests }) => ({ code, requests })), [
    { code: "DE", requests: 750 }, { code: "US", requests: 160 }, { code: "UA", requests: 30 },
  ]);
  assert.equal(snapshot.unknownRequests, 60);
  assert.equal(snapshot.siteCount, 2);
  assert.equal(snapshot.scope, "accessible_zones");
  assert.equal(snapshot.source, "Cloudflare / connected sites");
});

test("successful refresh publishes aggregates and opaque coverage only, with no credential or domain metadata", async t => {
  const output = outputPath(t);
  const result = await refresh({ env: ENV, now: NOW, fetchImpl: fakeFetch(), output });
  assert.equal(result.refreshed, true);
  const text = fs.readFileSync(output, "utf8");
  assert.doesNotMatch(text, /synthetic-token|private-|account|zoneTag|\.example|Authorization/);
  for (const id of IDS) assert.ok(!text.includes(id));
  assert.deepEqual(Object.keys(JSON.parse(text)).sort(), [
    "countries", "coverageFingerprints", "period", "schemaVersion", "scope", "siteCount", "source", "totals", "unknownRequests", "updated",
  ]);
  assert.equal(result.snapshot.coverageFingerprints.length, 2);
  assert.ok(result.snapshot.coverageFingerprints.every(hash => /^[a-f0-9]{64}$/.test(hash)));
  assert.ok(!fs.existsSync(output + ".tmp"));
});

test("matching zones with zero HTTP events remain valid, including an empty analytics result set", async () => {
  const snapshot = await collect({ env: ENV, now: NOW, fetchImpl: async (url) => {
    if (url.includes("/zones?")) return ok(zonePage([IDS[0]]));
    const body = analytics(IDS[0]);
    body.data.viewer.zones[0].audience = [];
    return ok(body);
  } });
  assert.equal(snapshot.siteCount, 1);
  assert.deepEqual(snapshot.totals, { requests: 0, cachedRequests: 0, bytes: 0, cachedBytes: 0 });
  assert.equal(snapshot.unknownRequests, 0);
  assert.deepEqual(snapshot.countries, []);
});

test("one site's analytics failure preserves the entire previous snapshot byte-for-byte and date", async t => {
  const output = outputPath(t);
  const previous = JSON.stringify(priorSnapshot(), null, 2) + "\n";
  fs.writeFileSync(output, previous);
  const mock = fakeFetch();
  let queried = 0;
  const delays = [];
  const result = await refresh({ env: ENV, now: NEXT_DAY, output, sleepImpl: async ms => delays.push(ms), fetchImpl: async (url, options) => {
    if (options.body && ++queried >= 2) return { ok: false, status: 503 };
    return mock(url, options);
  } });
  assert.equal(result.refreshed, false);
  assert.equal(result.code, "ANALYTICS_FAILED");
  assert.equal(result.reason, "HTTP_503");
  assert.equal(result.snapshot.updated, "2026-10-10");
  assert.equal(fs.readFileSync(output, "utf8"), previous);
  assert.equal(queried, 4);
  assert.deepEqual(delays, [1000, 2000]);
});

test("losing any previously covered site rejects smaller and substituted coverage before querying analytics", async t => {
  const output = outputPath(t);
  const previous = JSON.stringify(priorSnapshot(), null, 2) + "\n";
  fs.writeFileSync(output, previous);
  for (const ids of [[IDS[0]], [IDS[0], IDS[2]], [IDS[0], IDS[2], IDS[3]]]) {
    const result = await refresh({ env: ENV, now: NEXT_DAY, output, fetchImpl: async (url) => {
      assert.ok(url.includes("/zones?"), "coverage failure must happen before analytics");
      return ok(zonePage(ids));
    } });
    assert.equal(result.refreshed, false);
    assert.equal(result.code, "COVERAGE_REDUCED");
    assert.equal(fs.readFileSync(output, "utf8"), previous);
  }
});

test("adding accessible sites while keeping every prior site refreshes coverage", async t => {
  const output = outputPath(t);
  fs.writeFileSync(output, JSON.stringify(priorSnapshot()));
  const result = await refresh({ env: ENV, now: NEXT_DAY, output, fetchImpl: fakeFetch(IDS) });
  assert.equal(result.refreshed, true);
  assert.equal(result.snapshot.siteCount, 4);
  assert.equal(result.snapshot.updated, "2026-10-11");
  for (const hash of priorSnapshot().coverageFingerprints) assert.ok(result.snapshot.coverageFingerprints.includes(hash));
});

test("first-run failures provide fixed diagnostic codes and write no fake snapshot", async t => {
  const output = outputPath(t);
  const cases = [
    { env: {}, fetchImpl: async () => { assert.fail("must not fetch without a token"); }, code: "CONFIGURATION_MISSING" },
    { env: ENV, fetchImpl: async () => ({ ok: false, status: 403 }), code: "ZONE_DISCOVERY_PERMISSION" },
    { env: ENV, fetchImpl: async () => ok({ success: false, errors: [{ code: 10000, message: "secret upstream account details" }] }), code: "ZONE_DISCOVERY_PERMISSION" },
    { env: ENV, fetchImpl: async () => { throw new Error("private domain, token and URL"); }, code: "ZONE_DISCOVERY_FAILED" },
    { env: ENV, fetchImpl: async () => ok(zonePage([], { totalPages: 0 })), code: "NO_ACCESSIBLE_ZONES" },
  ];
  for (const scenario of cases) {
    await assert.rejects(() => refresh({ ...scenario, now: NOW, output, sleepImpl: async () => {} }), error => {
      assert.equal(error.code, scenario.code);
      assert.equal(error.message, `Portfolio sync unavailable (${scenario.code}).`);
      return true;
    });
    assert.ok(!fs.existsSync(output));
  }
});

test("partial or changing zone discovery never silently publishes a subset", async () => {
  const cases = [
    page => zonePage([IDS[0]], { page, totalPages: 2, totalCount: 2 }), // repeated zone
    page => zonePage([IDS[page - 1]], { page, totalPages: 2, totalCount: page === 1 ? 2 : 3 }),
    page => zonePage(page === 1 ? [IDS[0]] : [], { page, totalPages: 2, totalCount: 2 }),
    () => ({ success: true, result: [] }),
    () => zonePage([IDS[0]], { totalPages: 1, totalCount: 2 }),
    () => ({ ...zonePage([IDS[0]]), result: [{ id: IDS[0], status: "pending" }] }),
  ];
  for (const makePage of cases) {
    await assert.rejects(() => discoverZones({ env: ENV, fetchImpl: async url => {
      return ok(makePage(Number(new URL(url).searchParams.get("page"))));
    } }), { code: "ZONE_DISCOVERY_INCOMPLETE" });
  }
});

test("missing analytics, wrong zone, null data, and GraphQL errors are failures rather than zero traffic", async () => {
  const cases = [
    { body: { data: { viewer: { zones: [] } } }, code: "ANALYTICS_INVALID" },
    { body: analytics(IDS[1]), code: "ANALYTICS_INVALID" },
    { body: { data: { viewer: { zones: [{ zoneTag: IDS[0], audience: null }] } } }, code: "ANALYTICS_INVALID" },
    { body: { data: null, errors: [{ message: "private-domain.example: permission denied" }] }, code: "ANALYTICS_PERMISSION" },
    { body: analytics(IDS[0], { requests: -1 }), code: "ANALYTICS_INVALID" },
  ];
  for (const scenario of cases) {
    await assert.rejects(() => collect({ env: ENV, now: NOW, fetchImpl: async url => {
      return ok(url.includes("/zones?") ? zonePage([IDS[0]]) : scenario.body);
    } }), { code: scenario.code });
  }
});

test("integer overflow and mixed periods cannot turn into plausible aggregate metrics", () => {
  const first = normalize(analytics(IDS[0], { requests: Number.MAX_SAFE_INTEGER }), NOW);
  const second = normalize(analytics(IDS[1]), NOW);
  assert.throws(() => mergeSnapshots([first, second], IDS.slice(0, 2), NOW), { code: "TOTAL_OVERFLOW" });
  assert.throws(() => mergeSnapshots([second, normalize(analytics(IDS[1]), NEXT_DAY)], IDS.slice(0, 2), NOW), { code: "ANALYTICS_INVALID" });
});

test("malformed prior files do not qualify as retained verified data", async t => {
  const output = outputPath(t);
  for (const previous of [{}, { ...priorSnapshot(), unknownRequests: 99999 }, { ...priorSnapshot(), coverageFingerprints: [] }]) {
    const text = JSON.stringify(previous);
    fs.writeFileSync(output, text);
    await assert.rejects(() => refresh({ env: {}, now: NOW, output }), { code: "CONFIGURATION_MISSING" });
    assert.equal(fs.readFileSync(output, "utf8"), text);
  }
});

test("a dedicated portfolio token takes precedence without changing existing cursor credentials", async () => {
  const env = { ...ENV, CLOUDFLARE_PORTFOLIO_API_TOKEN: "synthetic-portfolio-token" };
  const mock = fakeFetch([IDS[0]]);
  await collect({ env, now: NOW, fetchImpl: async (url, options) => {
    assert.equal(options.headers.Authorization, "Bearer synthetic-portfolio-token");
    return mock(url, options);
  } });
  assert.equal(env.CLOUDFLARE_API_TOKEN, "synthetic-token");
});

test("transient HTTP, network, and GraphQL upstream failures retry only the failing query and recover", async t => {
  const warnings = [];
  t.mock.method(console, "warn", value => warnings.push(value));
  const scenarios = [
    ...[408, 429, 500, 502, 503, 504].map(status => () => ({ ok: false, status })),
    () => { throw new Error("private-domain.example synthetic-token connection reset"); },
    () => ok({ errors: [{ message: "private-domain.example synthetic-token: internal server error" }] }),
    () => ok({ errors: [{ message: "private-domain.example: rate limit exceeded" }] }),
    () => ok({ errors: [{ extensions: { code: "SERVICE_UNAVAILABLE" }, message: "private-account details" }] }),
  ];
  for (const failure of scenarios) {
    let discoveryCalls = 0;
    let analyticsCalls = 0;
    const requests = [];
    const delays = [];
    const snapshot = await collect({ env: ENV, now: NOW, sleepImpl: async ms => delays.push(ms),
      fetchImpl: async (url, options) => {
        if (url.includes("/zones?")) {
          discoveryCalls++;
          return ok(zonePage([IDS[0]]));
        }
        requests.push(options.body);
        if (++analyticsCalls < 3) return failure();
        return ok(analytics(IDS[0]));
      },
    });
    assert.equal(snapshot.totals.requests, 100);
    assert.equal(discoveryCalls, 1);
    assert.equal(analyticsCalls, 3);
    assert.equal(new Set(requests).size, 1);
    assert.deepEqual(delays, [1000, 2000]);
  }
  assert.doesNotMatch(warnings.join("\n"), /synthetic-token|private-domain|private-account/);
  assert.match(warnings.join("\n"), /HTTP_429/);
  assert.match(warnings.join("\n"), /HTTP_502/);
  assert.match(warnings.join("\n"), /NETWORK/);
  assert.match(warnings.join("\n"), /UPSTREAM_ERROR/);
});

test("discovery retries temporary failures without skipping or doubling zones", async () => {
  let calls = 0;
  const delays = [];
  const zones = await discoverZones({ env: ENV, sleepImpl: async ms => delays.push(ms), fetchImpl: async () => {
    if (++calls === 1) return { ok: false, status: 502 };
    return ok(zonePage(IDS));
  } });
  assert.deepEqual(zones, IDS);
  assert.equal(calls, 2);
  assert.deepEqual(delays, [1000]);
});

test("Retry-After seconds and HTTP dates are honored with a 30 second cap", async () => {
  const scenarios = [
    ["7", 7000],
    ["120", 30000],
    [new Date(Date.now() + 120_000).toUTCString(), 30000],
    ["not a date", 1000],
    ["0", 1000],
  ];
  for (const [header, expectedDelay] of scenarios) {
    let calls = 0;
    const delays = [];
    await discoverZones({ env: ENV, sleepImpl: async ms => delays.push(ms), fetchImpl: async () => {
      if (++calls === 1) return { ok: false, status: 429, headers: { get: name => name === "retry-after" ? header : null } };
      return ok(zonePage([IDS[0]]));
    } });
    assert.equal(calls, 2);
    assert.deepEqual(delays, [expectedDelay]);
  }
});

test("permission, permanent HTTP errors, and malformed analytics fail immediately without retry", async () => {
  const scenarios = [
    ...[400, 401, 403, 404, 422].map(status => () => ({ ok: false, status })),
    () => ok({ errors: [{ message: "permission denied for private-domain.example" }] }),
    () => ok({ errors: [{ message: "Cannot query field unknown on type Zone" }] }),
    () => ok({ data: { viewer: { zones: [{ zoneTag: IDS[0], audience: null }] } } }),
    () => ({ ok: true, status: 200, json: async () => { throw new Error("malformed JSON"); } }),
  ];
  for (const failure of scenarios) {
    let analyticsCalls = 0;
    await assert.rejects(() => collect({ env: ENV, now: NOW,
      sleepImpl: async () => assert.fail("permanent failures must not retry"),
      fetchImpl: async url => {
        if (url.includes("/zones?")) return ok(zonePage([IDS[0]]));
        analyticsCalls++;
        return failure();
      },
    }));
    assert.equal(analyticsCalls, 1);
  }
});

test("exhausted network retries expose only a safe diagnostic and keep the previous file and date", async t => {
  const output = outputPath(t);
  const previous = JSON.stringify(priorSnapshot(), null, 2) + "\n";
  fs.writeFileSync(output, previous);
  const warnings = [];
  t.mock.method(console, "warn", value => warnings.push(value));
  let calls = 0;
  const delays = [];
  const result = await refresh({ env: ENV, now: NEXT_DAY, output, sleepImpl: async ms => delays.push(ms),
    fetchImpl: async () => {
      calls++;
      throw new Error("private-domain.example synthetic-token upstream details");
    },
  });
  assert.equal(result.refreshed, false);
  assert.equal(result.code, "ZONE_DISCOVERY_FAILED");
  assert.equal(result.reason, "NETWORK");
  assert.equal(calls, 3);
  assert.deepEqual(delays, [1000, 2000]);
  assert.equal(result.snapshot.updated, "2026-10-10");
  assert.equal(fs.readFileSync(output, "utf8"), previous);
  assert.match(warnings.at(-1), /ZONE_DISCOVERY_FAILED; NETWORK/);
  assert.doesNotMatch(warnings.join("\n"), /private-domain|synthetic-token|upstream details/);
});
