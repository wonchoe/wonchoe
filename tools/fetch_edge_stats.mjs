// Public, zone-wide aggregates only. No request paths, IPs, or private metadata.
// Cloudflare schema: https://developers.cloudflare.com/analytics/graphql-api/migration-guides/zone-analytics/
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUTPUT = path.join(ROOT, "assets", "edge.json");
const DAY = 86_400_000;
const ISO_CODES = new Set((
  "AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ " +
  "CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR " +
  "GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP " +
  "KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ " +
  "NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ " +
  "TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS YE YT ZA ZM ZW XK"
).split(" "));
const NAMES = new Intl.DisplayNames(["en"], { type: "region" });

export function period(now = new Date()) {
  const midnight = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  return {
    start: new Date(midnight - 30 * DAY).toISOString().slice(0, 10),
    end: new Date(midnight - DAY).toISOString().slice(0, 10),
    days: 30,
  };
}

function number(value) {
  if (!Number.isSafeInteger(value) || value < 0) throw new Error("invalid aggregate");
  return value;
}

export function normalize(body, now = new Date()) {
  if (body.errors?.length) throw new Error("GraphQL rejected query");
  const groups = body.data?.viewer?.zones?.[0]?.audience;
  if (!Array.isArray(groups) || groups.length !== 1 || !groups[0]?.sum) {
    throw new Error("aggregate missing");
  }
  const sum = groups[0].sum;
  const totals = Object.fromEntries(["requests", "cachedRequests", "bytes", "cachedBytes"].map(key => [key, number(sum[key])]));
  if (totals.cachedRequests > totals.requests || totals.cachedBytes > totals.bytes || !Array.isArray(sum.countryMap)) {
    throw new Error("inconsistent aggregate");
  }
  const counts = new Map();
  let countryTotal = 0;
  for (const row of sum.countryMap) {
    const requests = number(row.requests);
    countryTotal += requests;
    const code = String(row.clientCountryName).toUpperCase();
    if (requests && ISO_CODES.has(code)) counts.set(code, (counts.get(code) || 0) + requests);
  }
  if (countryTotal > totals.requests) throw new Error("inconsistent country totals");
  const countries = [...counts].map(([code, requests]) => ({ code, name: NAMES.of(code), requests }))
    .sort((a, b) => b.requests - a.requests || a.code.localeCompare(b.code));
  return {
    schemaVersion: 1,
    source: "Cloudflare / cursor.style",
    updated: now.toISOString().slice(0, 10),
    period: period(now),
    totals,
    countries,
    unknownRequests: totals.requests - countries.reduce((total, country) => total + country.requests, 0),
  };
}

async function request(env, now, fetchImpl) {
  if (!env.CLOUDFLARE_API_TOKEN || !/^[a-f0-9]{32}$/i.test(env.CLOUDFLARE_ZONE_ID || "")) {
    throw new Error("Cloudflare configuration unavailable");
  }
  const range = period(now);
  // No dimensions: Cloudflare combines the entire interval into one group.
  // Inclusive boundaries select exactly 30 completed UTC calendar days.
  const query = `{ viewer { zones(filter: {zoneTag: "${env.CLOUDFLARE_ZONE_ID}"}) {
    audience: httpRequests1dGroups(limit: 1, filter: {date_geq: "${range.start}", date_leq: "${range.end}"}) {
      sum { requests cachedRequests bytes cachedBytes countryMap {clientCountryName requests} }
    }
  } } }`;
  const response = await fetchImpl("https://api.cloudflare.com/client/v4/graphql", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${env.CLOUDFLARE_API_TOKEN}` },
    body: JSON.stringify({ query }),
    signal: AbortSignal.timeout(30_000),
  });
  if (!response.ok) throw new Error("Cloudflare request failed");
  return normalize(await response.json(), now);
}

export async function refresh({ env = process.env, now = new Date(), fetchImpl = fetch, output = OUTPUT } = {}) {
  let snapshot;
  try {
    snapshot = await request(env, now, fetchImpl);
  } catch {
    // Never log raw API errors: upstream bodies can include request details.
    // Preserve the original bytes and date; a failed refresh is not new data.
    try {
      const previous = JSON.parse(fs.readFileSync(output, "utf8"));
      if (previous.schemaVersion !== 1 || !previous.updated || !previous.totals || !Array.isArray(previous.countries)) {
        throw new Error("no valid snapshot");
      }
      console.warn(`Audience sync unavailable; retaining snapshot from ${previous.updated}.`);
      return { refreshed: false, snapshot: previous };
    } catch {
      throw new Error("Audience sync unavailable and no previous snapshot exists; no statistics were written.");
    }
  }
  fs.mkdirSync(path.dirname(output), { recursive: true });
  const temporary = `${output}.tmp`;
  fs.writeFileSync(temporary, JSON.stringify(snapshot, null, 2) + "\n");
  fs.renameSync(temporary, output);
  console.log(`Audience synced: ${snapshot.countries.length} countries and territories; ${snapshot.period.start} to ${snapshot.period.end} UTC.`);
  return { refreshed: true, snapshot };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  refresh().catch(error => {
    console.error(error.message);
    process.exitCode = 1;
  });
}
