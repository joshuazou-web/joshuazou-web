/* One data source, two transports.
 *
 * With the API running the console reads live objects; without it, the static
 * snapshot. The shapes are identical because both come from the same
 * projection in Python, so nothing in the UI needs to know which one it got.
 */
import type { Snapshot } from "./types";

const API_SNAPSHOT = "/api/snapshot";
const STATIC_SNAPSHOT = "./snapshot.json";

export async function loadSnapshot(): Promise<{ snapshot: Snapshot; source: "api" | "static" }> {
  try {
    const live = await fetch(API_SNAPSHOT, { headers: { accept: "application/json" } });
    if (live.ok) return { snapshot: (await live.json()) as Snapshot, source: "api" };
  } catch {
    /* no API running — fall through to the published snapshot */
  }
  const stat = await fetch(STATIC_SNAPSHOT);
  if (!stat.ok) throw new Error(`could not load ${STATIC_SNAPSHOT} (${stat.status})`);
  return { snapshot: (await stat.json()) as Snapshot, source: "static" };
}
