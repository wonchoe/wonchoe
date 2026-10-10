// Public aggregates across all active zones this token can read; never domains or zone IDs.
// Discovery: https://developers.cloudflare.com/api/resources/zones/methods/list/
// Analytics: https://developers.cloudflare.com/analytics/graphql-api/migration-guides/zone-analytics/
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { normalize, period } from "./fetch_edge_stats.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUTPUT = path.join(ROOT, "assets", "portfolio.json");
const TOTAL_KEYS = ["requests", "cachedRequests", "bytes", "cachedBytes"];
const SOURCE = "Cloudflare / connected sites";
const SCOPE = "accessible_zones";
const sleep = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));
const CODES = new Set([
  "CONFIGURATION_MISSING", "ZONE_DISCOVERY_PERMISSION", "ZONE_DISCOVERY_FAILED",
  "ZONE_DISCOVERY_INCOMPLETE", "NO_ACCESSIBLE_ZONES", "ANALYTICS_PERMISSION",
  "ANALYTICS_FAILED", "ANALYTICS_INVALID", "COVERAGE_REDUCED", "TOTAL_OVERFLOW",
]);

export class PortfolioError extends Error {
  constructor(code, reason) {
    super(`Portfolio sync unavailable (${code}).`);
    this.code = code;
    if (safeReason(reason)) this.reason = reason;
  }
}

function safeReason(reason) {
  return typeof reason === "string" && /^(HTTP_[1-5]\d{2}|HTTP_ERROR|NETWORK|INVALID_JSON|INVALID_RESPONSE|UPSTREAM_ERROR|UPSTREAM_PERMISSION)$/.test(reason);
}
function fail(code, reason) { throw new PortfolioError(code, reason); }
function fingerprint(id) { return createHash("sha256").update(`cloudflare-zone:${id}`).digest("hex"); }
function safeSum(a, b) {
  const value = a + b;
  if (!Number.isSafeInteger(value) || value < 0) fail("TOTAL_OVERFLOW");
  return value;
}

function tokenFrom(env) {
  const token = env.CLOUDFLARE_PORTFOLIO_API_TOKEN || env.CLOUDFLARE_API_TOKEN;
  if (!token) fail("CONFIGURATION_MISSING");
  return token;
}

function retryAfter(response) {
  const value = response.headers?.get?.("retry-after");
  if (!value) return 0;
  const seconds = /^\d+(?:\.\d+)?$/.test(value.trim()) ? Number(value) : (Date.parse(value) - Date.now()) / 1000;
  return Number.isFinite(seconds) ? Math.max(0, Math.min(30_000, seconds * 1000)) : 0;
}

function requestFailure(stage, reason, retryable = false, response) {
  const error = new PortfolioError(`${stage}_FAILED`, reason);
  error.retryable = retryable;
  error.retryAfterMs = response ? retryAfter(response) : 0;
  throw error;
}

async function requestOnce(url, options, token, fetchImpl, stage) {
  let response;
  try {
    response = await fetchImpl(url, {
      ...options,
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      signal: AbortSignal.timeout(30_000),
    });
  } catch { requestFailure(stage, "NETWORK", true); }
  const httpReason = Number.isInteger(response.status) && response.status >= 100 && response.status <= 599
    ? `HTTP_${response.status}` : "HTTP_ERROR";
  if (response.status === 401 || response.status === 403) fail(`${stage}_PERMISSION`, httpReason);
  if (!response.ok) {
    const transient = [408, 429].includes(response.status) || (response.status >= 500 && response.status <= 599);
    requestFailure(stage, httpReason, transient, response);
  }
  let body;
  try { body = await response.json(); } catch { requestFailure(stage, "INVALID_JSON"); }
  if (!body || typeof body !== "object") requestFailure(stage, "INVALID_RESPONSE");
  if (body.success === false || body.errors?.length) {
    // Inspect only to choose a fixed diagnostic; never print upstream messages.
    const permission = Array.isArray(body.errors) && body.errors.some(error =>
      [10000, 9103, 9109].includes(error.code) ||
      /permission|unauthori[sz]ed|not authori[sz]ed|authentication|access denied|forbidden/i.test(String(error.message)));
    if (permission) fail(`${stage}_PERMISSION`, "UPSTREAM_PERMISSION");
    const transient = Array.isArray(body.errors) && body.errors.some(error =>
      /rate.?limit|too many requests|temporar|timed? ?out|timeout|internal(?: server)? error|upstream|unavailable|try again|deadline exceeded|resource exhausted/i.test(String(error.message)) ||
      /^(INTERNAL_SERVER_ERROR|INTERNAL_ERROR|TIMEOUT|RATE_LIMITED|SERVICE_UNAVAILABLE)$/.test(String(error.extensions?.code)));
    requestFailure(stage, "UPSTREAM_ERROR", transient, response);
  }
  return body;
}

async function api(url, options, token, fetchImpl, stage, sleepImpl) {
  for (let attempt = 1; attempt <= 3; attempt++) {
    try { return await requestOnce(url, options, token, fetchImpl, stage); }
    catch (error) {
      if (!error.retryable || attempt === 3) throw error;
      const delay = Math.max(attempt * 1000, error.retryAfterMs || 0);
      console.warn(`Portfolio ${stage.toLowerCase()} retry ${attempt}/2 (${error.reason}); waiting ${delay / 1000}s.`);
      await sleepImpl(delay);
    }
  }
}

export async function discoverZones({ env = process.env, fetchImpl = fetch, sleepImpl = sleep } = {}) {
  const token = tokenFrom(env);
  const zones = new Set();
  let totalCount;
  let totalPages;
  for (let page = 1; ; page++) {
    const url = new URL("https://api.cloudflare.com/client/v4/zones");
    url.search = new URLSearchParams({ status: "active", per_page: "50", page: String(page), order: "name", direction: "asc" });
    const body = await api(url.href, { method: "GET" }, token, fetchImpl, "ZONE_DISCOVERY", sleepImpl);
    const info = body.result_info;
    if (body.success !== true || !Array.isArray(body.result) || !info ||
        !Number.isSafeInteger(info.total_count) || info.total_count < 0 ||
        !Number.isSafeInteger(info.total_pages) || info.total_pages < 0 ||
        info.page !== page || info.count !== body.result.length) fail("ZONE_DISCOVERY_INCOMPLETE");
    if (page === 1) {
      totalCount = info.total_count;
      totalPages = info.total_pages;
    }
    if (totalCount !== info.total_count || totalPages !== info.total_pages ||
        (totalCount > 0 && totalPages < 1) || totalPages > 10_000) fail("ZONE_DISCOVERY_INCOMPLETE");
    for (const zone of body.result) {
      if (zone.status !== "active" || !/^[a-f0-9]{32}$/i.test(zone.id || "") || zones.has(zone.id.toLowerCase())) {
        fail("ZONE_DISCOVERY_INCOMPLETE");
      }
      zones.add(zone.id.toLowerCase());
    }
    if (page >= totalPages) break;
    if (!body.result.length) fail("ZONE_DISCOVERY_INCOMPLETE");
  }
  if (zones.size !== totalCount) fail("ZONE_DISCOVERY_INCOMPLETE");
  if (!zones.size) fail("NO_ACCESSIBLE_ZONES");
  return [...zones].sort();
}

async function zoneSnapshot(zone, { env, now, fetchImpl, sleepImpl }) {
  const range = period(now);
  const query = `{ viewer { zones(filter: {zoneTag: "${zone}"}) {
    zoneTag
    audience: httpRequests1dGroups(limit: 1, filter: {date_geq: "${range.start}", date_leq: "${range.end}"}) {
      sum { requests cachedRequests bytes cachedBytes countryMap {clientCountryName requests} }
    }
  } } }`;
  const body = await api("https://api.cloudflare.com/client/v4/graphql", {
    method: "POST", body: JSON.stringify({ query }),
  }, tokenFrom(env), fetchImpl, "ANALYTICS", sleepImpl);
  const zones = body.data?.viewer?.zones;
  if (!Array.isArray(zones) || zones.length !== 1 || zones[0].zoneTag !== zone) fail("ANALYTICS_INVALID");
  // A returned, matching zone with an empty result set has no HTTP events.
  // A missing zone, missing collection, null sum, or GraphQL error is a failure.
  if (Array.isArray(zones[0].audience) && zones[0].audience.length === 0) {
    zones[0].audience = [{ sum: { requests: 0, cachedRequests: 0, bytes: 0, cachedBytes: 0, countryMap: [] } }];
  }
  try { return normalize(body, now); } catch { fail("ANALYTICS_INVALID"); }
}

export function mergeSnapshots(snapshots, zoneIds, now = new Date()) {
  if (!zoneIds.length || snapshots.length !== zoneIds.length || new Set(zoneIds).size !== zoneIds.length) {
    fail("ZONE_DISCOVERY_INCOMPLETE");
  }
  const totals = Object.fromEntries(TOTAL_KEYS.map(key => [key, 0]));
  const counts = new Map();
  const range = period(now);
  let unknownRequests = 0;
  for (const snapshot of snapshots) {
    if (JSON.stringify(snapshot.period) !== JSON.stringify(range)) fail("ANALYTICS_INVALID");
    for (const key of TOTAL_KEYS) totals[key] = safeSum(totals[key], snapshot.totals[key]);
    unknownRequests = safeSum(unknownRequests, snapshot.unknownRequests);
    for (const country of snapshot.countries) {
      const previous = counts.get(country.code);
      counts.set(country.code, { ...country, requests: safeSum(previous?.requests || 0, country.requests) });
    }
  }
  return {
    schemaVersion: 1,
    source: SOURCE,
    scope: SCOPE,
    updated: now.toISOString().slice(0, 10),
    period: range,
    siteCount: zoneIds.length,
    // Zone IDs are random 128-bit identifiers; these irreversible hashes let us
    // reject lost coverage without exposing account IDs, domains, or zone IDs.
    coverageFingerprints: zoneIds.map(fingerprint).sort(),
    totals,
    countries: [...counts.values()].sort((a, b) => b.requests - a.requests || a.code.localeCompare(b.code)),
    unknownRequests,
  };
}

function readPrevious(output) {
  try {
    const snapshot = JSON.parse(fs.readFileSync(output, "utf8"));
    if (snapshot.schemaVersion !== 1 || snapshot.source !== SOURCE || snapshot.scope !== SCOPE ||
        !/^\d{4}-\d{2}-\d{2}$/.test(snapshot.updated) || !Number.isSafeInteger(snapshot.siteCount) || snapshot.siteCount < 1 ||
        !Array.isArray(snapshot.coverageFingerprints) || snapshot.coverageFingerprints.length !== snapshot.siteCount ||
        new Set(snapshot.coverageFingerprints).size !== snapshot.siteCount ||
        snapshot.coverageFingerprints.some(value => !/^[a-f0-9]{64}$/.test(value)) ||
        !Array.isArray(snapshot.countries) || !Number.isSafeInteger(snapshot.unknownRequests) || snapshot.unknownRequests < 0) return null;
    const now = new Date(`${snapshot.updated}T00:00:00Z`);
    if (JSON.stringify(snapshot.period) !== JSON.stringify(period(now))) return null;
    const normalized = normalize({ data: { viewer: { zones: [{ audience: [{ sum: {
      ...snapshot.totals,
      countryMap: snapshot.countries.map(country => ({ clientCountryName: country.code, requests: country.requests })),
    } }] }] } } }, now);
    if (normalized.unknownRequests !== snapshot.unknownRequests || normalized.countries.length !== snapshot.countries.length) return null;
    return snapshot;
  } catch { return null; }
}

export async function collect({ env = process.env, now = new Date(), fetchImpl = fetch, previous = null, sleepImpl = sleep } = {}) {
  const zones = await discoverZones({ env, fetchImpl, sleepImpl });
  const coverage = new Set(zones.map(fingerprint));
  if (previous && (previous.siteCount > zones.length || previous.coverageFingerprints.some(hash => !coverage.has(hash)))) {
    fail("COVERAGE_REDUCED");
  }
  const snapshots = [];
  // Conservative sequential requests avoid bursts against analytics rate limits.
  // Any single failure aborts the entire refresh; partial totals are not useful.
  for (const zone of zones) snapshots.push(await zoneSnapshot(zone, { env, now, fetchImpl, sleepImpl }));
  return mergeSnapshots(snapshots, zones, now);
}

export async function refresh({ env = process.env, now = new Date(), fetchImpl = fetch, output = OUTPUT, sleepImpl = sleep } = {}) {
  const previous = readPrevious(output);
  let snapshot;
  try {
    snapshot = await collect({ env, now, fetchImpl, previous, sleepImpl });
  } catch (error) {
    const code = CODES.has(error.code) ? error.code : "ANALYTICS_FAILED";
    const reason = safeReason(error.reason) ? error.reason : undefined;
    if (!previous) throw new PortfolioError(code, reason);
    console.warn(`Portfolio sync unavailable (${code}${reason ? `; ${reason}` : ""}); retaining snapshot from ${previous.updated}.`);
    return { refreshed: false, snapshot: previous, code, ...(reason ? { reason } : {}) };
  }
  fs.mkdirSync(path.dirname(output), { recursive: true });
  const temporary = `${output}.tmp`;
  fs.writeFileSync(temporary, JSON.stringify(snapshot, null, 2) + "\n");
  fs.renameSync(temporary, output);
  console.log(`Portfolio synced: ${snapshot.siteCount} connected sites, ${snapshot.countries.length} countries and territories; ${snapshot.period.start} to ${snapshot.period.end} UTC.`);
  return { refreshed: true, snapshot };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const task = process.argv.includes("--check")
    ? collect().then(snapshot => console.log(`Portfolio access verified: ${snapshot.siteCount} active connected sites; analytics available for every site. No files written.`))
    : refresh();
  task.catch(error => {
    const code = CODES.has(error.code) ? error.code : "ANALYTICS_FAILED";
    const reason = safeReason(error.reason) ? `; ${error.reason}` : "";
    console.error(`Portfolio sync unavailable (${code}${reason}); no statistics were written.`);
    process.exitCode = 1;
  });
}
