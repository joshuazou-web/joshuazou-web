// For every bullet: how many lines it wraps to and how full its last line is (%).
// A last line under ~85% reads as a ragged orphan; fix by trimming to fewer lines or
// adding true detail to fill the line. Usage: node lines.cjs <resume.html> [threshold=86]
const path = require('path');
const { launch, PAGE, mmToPx } = require('./browser.cjs');

(async () => {
  const [html, threshold = '86'] = process.argv.slice(2);
  const browser = await launch();
  const page = await browser.newPage();
  await page.setViewportSize({ width: Math.round(mmToPx(PAGE.widthMm - PAGE.left - PAGE.right)), height: 1200 });
  await page.goto('file://' + path.resolve(html));
  await page.emulateMedia({ media: 'print' });
  const rows = await page.evaluate(() => [...document.querySelectorAll('.sheet li, .lead')].map((el) => {
    const range = document.createRange(); range.selectNodeContents(el);
    const lines = {};
    for (const r of range.getClientRects()) { const k = Math.round(r.bottom); lines[k] = Math.max(lines[k] || 0, r.right); }
    const keys = Object.keys(lines).map(Number).sort((a, b) => a - b);
    const box = el.getBoundingClientRect();
    const last = (lines[keys[keys.length - 1]] - box.left) / box.width;
    return { n: keys.length, fill: Math.round(last * 100), text: el.textContent.trim().slice(0, 24) };
  }));
  for (const r of rows) {
    const flag = r.fill < +threshold ? '  <-- fix' : '';
    console.log(`${r.n} line(s) | last ${String(r.fill).padStart(3)}% | ${r.text}${flag}`);
  }
  await browser.close();
})();
