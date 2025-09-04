// update_readme.mjs
import fs from "fs";
import fetch from "node-fetch";

const zoneId = process.env.CLOUDFLARE_ZONE_ID;
const apiToken = process.env.CLOUDFLARE_API_TOKEN;

async function getStats() {
  console.log("ZONE_ID:", zoneId);
  const query = `
  {
    viewer {
      zones(filter: { zoneTag: "${zoneId}" }) {
        last24h: httpRequests1dGroups(
          limit: 1,
          filter: { date: "${new Date(Date.now() - 24*60*60*1000).toISOString().slice(0, 10)}" }
        ) {
          sum {
            requests
            pageViews
          }
          uniq {
            uniques
          }
        }
        last30d: httpRequests1dGroups(
          limit: 30,
          filter: {
            date_geq: "${new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)}",
            date_leq: "${new Date().toISOString().slice(0, 10)}"
          }
        ) {
          sum {
            requests
            pageViews
          }
          uniq {
            uniques
          }
        }
      }
    }
  }`;

  const res = await fetch("https://api.cloudflare.com/client/v4/graphql", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiToken}`,
    },
    body: JSON.stringify({ query }),
  });

  const data = await res.json();
  console.log(JSON.stringify(data, null, 2));

  const last24h = data.data.viewer.zones[0].last24h[0];
  const last30d = data.data.viewer.zones[0].last30d;

  // Сумуємо дані за 30 днів
  const last30dStats = last30d.reduce((acc, day) => {
    acc.sum.requests += day.sum.requests;
    acc.sum.pageViews += day.sum.pageViews;
    acc.uniq.uniques = Math.max(acc.uniq.uniques, day.uniq.uniques);
    return acc;
  }, { 
    sum: { requests: 0, pageViews: 0 }, 
    uniq: { uniques: 0 } 
  });

  return {
    last24h,
    last30d: last30dStats
  };
}

async function updateReadme() {
  const stats = await getStats();
  
  // Форматуємо дані за останні 24 години
  const last24h = {
    visits: stats.last24h.uniq.uniques.toLocaleString(),
    views: stats.last24h.sum.pageViews.toLocaleString(),
    requests: stats.last24h.sum.requests.toLocaleString(),
  };

  // Форматуємо дані за останні 30 днів
  const last30d = {
    visits: stats.last30d.uniq.uniques.toLocaleString(),
    views: stats.last30d.sum.pageViews.toLocaleString(),
    requests: stats.last30d.sum.requests.toLocaleString(),
  };

  let readme = fs.readFileSync("README.md", "utf8");

  const markerStart = "<!-- CF-STATS:START -->";
  const markerEnd = "<!-- CF-STATS:END -->";

const newStats = `
<table>
  <tr>
    <th>Period</th>
    <th>Requests</th>
    <th>Page Views</th>
    <th>Unique Visitors</th>
  </tr>
  <tr>
    <td><b>Last 24 hours</b></td>
    <td><img src="https://img.shields.io/badge/🌐 ${last24h.requests}-1DA1F2?style=for-the-badge"/></td>
    <td><img src="https://img.shields.io/badge/👀 ${last24h.views}-2ecc71?style=for-the-badge"/></td>
    <td><img src="https://img.shields.io/badge/👥 ${last24h.visits}-f1c40f?style=for-the-badge"/></td>
  </tr>
  <tr>
    <td><b>Last 30 days</b></td>
    <td><img src="https://img.shields.io/badge/🌐 ${last30d.requests}-1DA1F2?style=for-the-badge"/></td>
    <td><img src="https://img.shields.io/badge/👀 ${last30d.views}-2ecc71?style=for-the-badge"/></td>
    <td><img src="https://img.shields.io/badge/👥 ${last30d.visits}-f1c40f?style=for-the-badge"/></td>
  </tr>
</table>
`;

  const regex = new RegExp(`${markerStart}[\\s\\S]*?${markerEnd}`, "m");

readme = readme.replace(
  regex,
  `${markerStart}\n${newStats}\n${markerEnd}`
);

  fs.writeFileSync("README.md", readme);
}

updateReadme();