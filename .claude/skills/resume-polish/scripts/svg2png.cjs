// Rasterize SVG logos to transparent PNG siblings (Word cannot embed SVG reliably).
// Usage: node svg2png.cjs <logos_dir>
const fs = require('fs');
const path = require('path');
const { launch } = require('./browser.cjs');

(async () => {
  const dir = path.resolve(process.argv[2] || 'logos');
  const browser = await launch();
  const page = await browser.newPage();
  for (const f of fs.readdirSync(dir).filter((n) => n.endsWith('.svg'))) {
    const tmp = path.join(dir, '_tmp.html');
    fs.writeFileSync(tmp, `<body style="margin:0;background:transparent"><img id=i src="${f}" style="height:256px"></body>`);
    await page.goto('file://' + tmp);
    await page.waitForTimeout(150);
    await (await page.$('#i')).screenshot({ path: path.join(dir, f.replace(/\.svg$/, '.png')), omitBackground: true });
    fs.unlinkSync(tmp);
    console.log('png', f);
  }
  await browser.close();
})();
