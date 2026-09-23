// Build an editable Word version that mirrors the HTML layout (same page margins,
// fonts, blue hierarchy, grey company bars, logos, nested bullets, clickable links).
// Usage: node build-docx.cjs <resume.json> <out.docx> [line_twips=212] [logos_dir=.]
// line_twips is an exact line height; lower it until LibreOffice renders one page,
// then keep ~4 twips of slack because Word's CJK fonts wrap slightly differently.
const fs = require('fs');
const path = require('path');
const {
  ExternalHyperlink, ImageRun, Document, Packer, Paragraph, TextRun, TabStopType,
  BorderStyle, ShadingType, AlignmentType, LevelFormat, LineRuleType,
} = require('docx');

const [jsonPath, outPath, lineArg = '212', baseDir = path.dirname(path.resolve(process.argv[2]))] = process.argv.slice(2);
const { title, blocks } = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
const LINE = +lineArg;
const BLUE = '2458B8', TITLE_BLUE = '1F4E9C';
const MARGIN = { top: 391, bottom: 340, left: 510, right: 493 }; // = 6.9 / 6 / 9 / 8.7 mm
const W = 11906 - MARGIN.left - MARGIN.right;
const F = { ascii: 'Times New Roman', hAnsi: 'Times New Roman', eastAsia: 'SimSun', cs: 'Times New Roman' };
const H = { ascii: 'Microsoft YaHei', hAnsi: 'Microsoft YaHei', eastAsia: 'Microsoft YaHei' };
const SZ = 17; // half-points, ≈ 8.5pt body
const sp = { line: LINE, lineRule: LineRuleType.EXACT };

function image(src, heightPt) {
  const png = path.join(baseDir, src.replace(/\.svg$/, '.png')); // SVG logos need a PNG sibling
  if (!fs.existsSync(png)) return null;
  const buf = fs.readFileSync(png);
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);
  const hp = heightPt * 96 / 72;
  return new ImageRun({ type: 'png', data: buf, transformation: { width: Math.round(hp * w / h), height: Math.round(hp) } });
}

function run(r, o = {}) {
  if (r.img) { const im = image(r.img, o.imgh || 11); return im ? [im, new TextRun({ text: ' ', font: F, size: SZ })] : []; }
  const sep = r.t.trim() === '|';
  return [new TextRun({
    text: sep ? '  |  ' : r.t, bold: !!r.b || o.b, italics: !!r.i, font: F, size: o.size || SZ,
    color: sep ? '8A909B' : (o.color || (r.b ? '3A3A3A' : '222222')),
  })];
}

function runs(list, o = {}) {
  const out = [];
  list.forEach((r, i) => {
    if (r.t && !r.b && i > 0 && list[i - 1].b && !/^\s/.test(r.t) && r.t.trim() !== '|') out.push(...run({ t: '  ' }, o));
    out.push(...run(r, o));
  });
  return out;
}

const kids = [];
for (const x of blocks) {
  if (x.k === 'name') kids.push(new Paragraph({ spacing: { after: 20 }, children: [new TextRun({ text: x.text, bold: true, font: H, size: 42 })] }));
  else if (x.k === 'meta') kids.push(new Paragraph({ spacing: { ...sp, after: 0 }, children: runs(x.runs) }));
  else if (x.k === 'lead') kids.push(new Paragraph({ spacing: { ...sp, before: 20 }, alignment: AlignmentType.JUSTIFIED, children: runs(x.runs) }));
  else if (x.k === 'h2') kids.push(new Paragraph({
    spacing: { before: 120, after: 50 }, keepNext: true,
    border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: BLUE, space: 1 } },
    children: [new TextRun({ text: x.text, bold: true, font: H, size: 26, color: BLUE })],
  }));
  else if (x.k === 'edu') kids.push(new Paragraph({
    spacing: { ...sp }, tabStops: [{ type: TabStopType.RIGHT, position: W }],
    children: [...runs(x.runs, { imgh: 11 }), ...(x.date ? [new TextRun({ text: '\t' + x.date, bold: true, font: F, size: SZ })] : [])],
  }));
  else if (x.k === 'company') kids.push(new Paragraph({
    spacing: { before: 70, after: 20, line: LINE + 40, lineRule: LineRuleType.EXACT }, keepNext: true,
    shading: { type: ShadingType.CLEAR, color: 'auto', fill: 'F0F1F4' }, tabStops: [{ type: TabStopType.RIGHT, position: W - 60 }],
    children: [
      new TextRun({ text: ' ', font: F, size: 20 }),
      ...(x.logo ? run({ img: x.logo }, { imgh: 12 }) : []),
      ...runs(x.runs, { size: 19, color: '333333' }),
      new TextRun({ text: '\t', font: F, size: SZ }),
      ...(x.link ? [new ExternalHyperlink({ link: x.link.href, children: [new TextRun({ text: x.link.t, bold: true, font: F, size: 18, color: BLUE })] }),
        new TextRun({ text: '   ', font: F, size: SZ })] : []),
      new TextRun({ text: x.date, bold: true, font: F, size: SZ }),
    ],
  }));
  else if (x.k === 'ptitle') kids.push(new Paragraph({
    spacing: { ...sp, before: 10 }, keepNext: true,
    children: [new TextRun({ text: x.text.replace(/\s*\|\s*/g, '  |  '), bold: true, font: F, size: 18, color: TITLE_BLUE })],
  }));
  else if (x.k === 'li') kids.push(new Paragraph({ numbering: { reference: 'b', level: x.lvl || 0 }, alignment: AlignmentType.JUSTIFIED, spacing: { ...sp }, children: runs(x.runs) }));
}

const doc = new Document({
  title: title || 'Resume',
  styles: { default: { document: { run: { font: F, size: SZ } } } },
  numbering: { config: [{ reference: 'b', levels: [
    { level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 260, hanging: 180 } }, run: { size: 14 } } },
    { level: 1, format: LevelFormat.BULLET, text: '○', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 520, hanging: 180 } }, run: { size: 12 } } },
  ] }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { ...MARGIN, header: 0, footer: 0 } } }, children: kids }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(outPath, b); console.log('docx written, line', LINE); });
