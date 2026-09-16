/* Copy the platform's snapshot into the console's static assets.
 *
 * The console renders the same shapes whether it reads this file or the API, so
 * the published static demo cannot drift away from what the Python actually
 * produces: regenerate with `corridoros snapshot` and the page changes with it.
 */
import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const source = resolve(here, "../../../data/snapshot.json");
const target = resolve(here, "../public/snapshot.json");

if (!existsSync(source)) {
  console.error(
    `No snapshot at ${source}. Run \`python -m corridoros.cli snapshot data/snapshot.json\` first.`
  );
  process.exit(1);
}
mkdirSync(dirname(target), { recursive: true });
copyFileSync(source, target);
console.log(`snapshot -> ${target}`);
