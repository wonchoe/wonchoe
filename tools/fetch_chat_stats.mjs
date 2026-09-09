// Pulls the chat figures from a read-only endpoint on cursor.style and writes
// assets/chat.json for tools/build_chat_card.py.
//
// Needs two repository secrets; without them this is a no-op, so the workflow
// keeps working before the endpoint exists:
//   CHAT_STATS_URL    e.g. https://cursor.style/api/profile-stats
//   CHAT_STATS_TOKEN  the bearer token the endpoint expects
import fs from "fs";
import fetch from "node-fetch";

const url = process.env.CHAT_STATS_URL;
const token = process.env.CHAT_STATS_TOKEN;
const OUT = "assets/chat.json";

if (!url || !token) {
  console.log("CHAT_STATS_URL / CHAT_STATS_TOKEN not set - leaving", OUT, "as it is");
  process.exit(0);
}

try {
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);

  const body = await res.json();
  if (!Array.isArray(body.metrics)) throw new Error("no metrics array in the response");

  // Only take what the card draws, and keep it to what fits.
  const clean = (rows, max) =>
    (Array.isArray(rows) ? rows : [])
      .filter((m) => m && m.label != null && m.value != null)
      .slice(0, max)
      .map((m) => ({ label: String(m.label), value: String(m.value) }));

  const metrics = clean(body.metrics, 6);
  // `today` is the old key: the endpoint moved to a complete day.
  const yesterday = clean(body.yesterday ?? body.today, 4);

  fs.writeFileSync(
    OUT,
    JSON.stringify(
      {
        updated: body.updated ?? new Date().toISOString().slice(0, 10),
        note: body.note ? String(body.note) : "",
        metrics,
        yesterday,
      },
      null,
      2
    ) + "\n"
  );
  console.log(`chat stats: ${metrics.length} totals, ${yesterday.length} for the last full day`);
} catch (err) {
  // A stale card is fine; a red workflow because someone's chat pod is
  // restarting is not.
  console.warn("chat stats unavailable, keeping the previous card:", err.message);
}
