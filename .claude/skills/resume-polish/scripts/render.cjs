// Render the built résumé HTML to PDF (print CSS, A4) and a 300 dpi PNG of each page.
// Usage: node render.cjs <resume.html> <out.pdf>
const path = require('path');
const { execFileSync } = require('child_process');
const { launch } = require('./browser.cjs');

(async () => {
  const [html, pdf] = process.argv.slice(2);
  const browser = await launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve(html));
  // The ASu editor autosaves to localStorage; clear it so stale edits never leak into the PDF.
  await page.evaluate(() => { try { localStorage.clear(); } catch (e) {} });
  await page.reload();
  await page.emulateMedia({ media: 'print' });
  await page.pdf({ path: pdf, preferCSSPageSize: true, printBackground: true });
  await browser.close();
  // PNG for annotation: rasterize the PDF itself so it matches what gets submitted.
  execFileSync('python3', ['-c', `
import pypdfium2 as p, sys
d = p.PdfDocument(sys.argv[1]); print('pages', len(d))
stem = sys.argv[1][:-4]
for i in range(len(d)):
    d[i].render(scale=300/72).to_pil().save(stem + ('' if len(d) == 1 else f'_p{i+1}') + '.png')
`, pdf], { stdio: 'inherit' });
})();
