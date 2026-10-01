// Render each <section class="card"> in cards.html to a 1080x1440 PNG in images/.
// Usage: node render.mjs
//   Optional env:
//     FONTSOURCE_DIR  path to an installed @fontsource/noto-sans-sc package (offline fonts)
//     CHROMIUM_PATH   Chromium executable (defaults to Playwright's bundled one)
import { chromium } from "playwright-core";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
let html = readFileSync(join(here, "cards.html"), "utf8");

if (process.env.FONTSOURCE_DIR) {
  const links = [400, 500, 700, 900]
    .map((w) => `<link rel="stylesheet" href="${pathToFileURL(join(process.env.FONTSOURCE_DIR, `${w}.css`))}">`)
    .join("\n");
  html = html.replace(/<!-- FONTS -->[\s\S]*?<!-- \/FONTS -->/, links);
}

const tmp = join(here, ".render.html");
writeFileSync(tmp, html);
mkdirSync(join(here, "images"), { recursive: true });

const browser = await chromium.launch(
  process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {}
);
const page = await browser.newPage({ viewport: { width: 1080, height: 1440 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(tmp).href, { waitUntil: "networkidle" });
await page.evaluate(() => document.fonts.ready);

// Flag any card whose content pushes the footer past the bottom edge.
const overflow = await page.$$eval("section.card", (cards) =>
  cards.map((c, i) => {
    const over = c.querySelector(".foot").getBoundingClientRect().bottom - c.getBoundingClientRect().bottom;
    return over > 1 ? `card ${i + 1}: overflows by ${Math.round(over)}px` : null;
  }).filter(Boolean)
);
overflow.forEach((m) => console.warn("WARN", m));

const cards = await page.$$("section.card");
for (const [i, card] of cards.entries()) {
  const out = join(here, "images", `${String(i + 1).padStart(2, "0")}.png`);
  await card.screenshot({ path: out });
  console.log("wrote", out);
}
await browser.close();
