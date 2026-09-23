// Shared Chromium launcher: prefers CHROMIUM_PATH, then the preinstalled
// Playwright build in cloud sessions, then Playwright's own default.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

function findChromium() {
  if (process.env.CHROMIUM_PATH && fs.existsSync(process.env.CHROMIUM_PATH)) return process.env.CHROMIUM_PATH;
  const root = '/opt/pw-browsers';
  if (fs.existsSync(root)) {
    for (const d of fs.readdirSync(root).filter((n) => n.startsWith('chromium-')).sort().reverse()) {
      const p = path.join(root, d, 'chrome-linux', 'chrome');
      if (fs.existsSync(p)) return p;
    }
  }
  return undefined;
}

async function launch() {
  const executablePath = findChromium();
  return chromium.launch(executablePath ? { executablePath } : {});
}

// Page geometry for print measurements; keep in sync with @page in assets/style.css.
const PAGE = { widthMm: 210, heightMm: 297, top: 6.9, right: 8.7, bottom: 6, left: 9 };
const mmToPx = (mm) => (mm / 25.4) * 96;

module.exports = { launch, PAGE, mmToPx };
