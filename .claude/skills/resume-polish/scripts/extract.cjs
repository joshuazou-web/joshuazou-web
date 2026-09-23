// Walk content.html and dump its résumé structure (header, sections, company bars,
// project titles, bullets with bold/italic runs, logos, links) to JSON for build-docx.cjs.
// Usage: node extract.cjs <content.html> <out.json>
const fs = require('fs');
const path = require('path');
const { launch } = require('./browser.cjs');

(async () => {
  const [html, out] = process.argv.slice(2);
  const browser = await launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve(html));
  const data = await page.evaluate(() => {
    const runs = (el) => {
      const acc = [];
      const walk = (n, st) => {
        if (n.nodeType === 3) { const t = n.textContent.replace(/\s+/g, ' '); if (t.trim() || t === ' ') acc.push({ t, ...st }); return; }
        if (n.nodeType !== 1) return;
        if (n.tagName === 'IMG') { acc.push({ img: n.getAttribute('src') }); return; }
        const s = { ...st };
        if (['STRONG', 'B'].includes(n.tagName) || n.matches('.school,.date')) s.b = true;
        if (n.tagName === 'EM') s.i = true;
        n.childNodes.forEach((c) => walk(c, s));
      };
      walk(el, {});
      return acc;
    };
    const blocks = [];
    const sheet = document.querySelector('.sheet');
    const h1 = sheet.querySelector('h1');
    if (h1) blocks.push({ k: 'name', text: h1.textContent });
    sheet.querySelectorAll('.meta-row').forEach((m) => blocks.push({ k: 'meta', runs: runs(m) }));
    const lead = sheet.querySelector('.lead');
    if (lead) blocks.push({ k: 'lead', runs: runs(lead) });
    sheet.querySelectorAll('section').forEach((sec) => {
      sec.querySelectorAll(':scope > *').forEach((el) => {
        if (el.matches('.section-title')) blocks.push({ k: 'h2', text: el.textContent });
        else if (el.matches('.edu-row')) {
          const d = el.querySelector('.date');
          blocks.push({ k: 'edu', runs: runs(el.firstElementChild), date: d ? d.textContent : '' });
        } else if (el.matches('.company')) {
          const lg = el.querySelector('.company-logo');
          const ln = el.querySelector('.doc-link');
          blocks.push({ k: 'company', runs: runs(el.querySelector('.company-name')), date: el.querySelector('.company-meta').textContent,
            logo: lg ? lg.getAttribute('src') : null, link: ln ? { t: ln.textContent, href: ln.getAttribute('href') } : null });
        } else if (el.matches('.project')) {
          const t = el.querySelector('.project-title');
          if (t) blocks.push({ k: 'ptitle', text: t.textContent });
          el.querySelectorAll('li').forEach((li) => blocks.push({ k: 'li', lvl: li.classList.contains('nested') ? 1 : 0, runs: runs(li) }));
        } else if (el.matches('ul')) el.querySelectorAll('li').forEach((li) => blocks.push({ k: 'li', lvl: 0, runs: runs(li) }));
      });
    });
    return { title: document.title, blocks };
  });
  fs.writeFileSync(out, JSON.stringify(data, null, 1));
  console.log('blocks', data.blocks.length);
  await browser.close();
})();
