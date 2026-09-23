// How much vertical space the content uses versus one A4 page's printable area.
// "over" > 0 means it spills to another page; aim for about -20..0 px on a one-page résumé.
// Usage: node measure.cjs <resume.html>
const path = require('path');
const { launch, PAGE, mmToPx } = require('./browser.cjs');

(async () => {
  const browser = await launch();
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1000, height: 1400 });
  await page.goto('file://' + path.resolve(process.argv[2]));
  await page.emulateMedia({ media: 'print' });
  const width = mmToPx(PAGE.widthMm - PAGE.left - PAGE.right);
  const used = await page.evaluate((w) => {
    const s = document.querySelector('.sheet');
    s.style.width = w + 'px'; s.style.padding = '0'; s.style.margin = '0';
    const top = s.getBoundingClientRect().top;
    const bottom = [...s.querySelectorAll('li,div,h2')].reduce((m, e) => Math.max(m, e.getBoundingClientRect().bottom), 0);
    return bottom - top;
  }, width);
  const avail = mmToPx(PAGE.heightMm - PAGE.top - PAGE.bottom);
  console.log(`content ${used.toFixed(0)}px  page ${avail.toFixed(0)}px  over ${(used - avail).toFixed(0)}px  (one line ≈ 14px)`);
  await browser.close();
})();
