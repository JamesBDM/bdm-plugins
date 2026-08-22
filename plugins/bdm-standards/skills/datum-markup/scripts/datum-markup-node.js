// datum-markup-node.js — Node.js embed step for the datum-markup skill.
// Use when Python/pypdf isn't available. Requires: npm install pdf-lib
//
//   const { embedDatumMarkup, pageSizes, verify } = require('./datum-markup-node.js');
//   const src = fs.readFileSync('source.pdf');
//   const sizes = await pageSizes(src);
//   verify(project, sizes);                       // throws on the invisible mistakes
//   fs.writeFileSync('marked-up.pdf', await embedDatumMarkup(src, project));
//
// `project` is the payload object described in ../references/annotation-types.md
// (version 4: annotations, pageCalibrations, takeoffItems, ...).
// Coordinates: PDF points, origin TOP-LEFT, y down.
//
// Targets Datum v3.22.
const { PDFDocument, PDFName, PDFHexString } = require('pdf-lib');

// Every type Datum's renderer knows. Anything else draws a dashed placeholder.
const VALID_TYPES = new Set([
  'measure','polyline','area','rectangle','ellipse','line','polygon','cloud',
  'arrow','text','callout','stamp','tick','signature','image','symbol','pen',
  'highlight','count','dimension','cutcontent','legend','table',
  // v3.22 presentation markups
  'chip','badge','divider','banner','quote','kpi','chevron','timeline',
  'bracket','progress','chart'
]);
const BOX2_TYPES = new Set([
  'rectangle','ellipse','highlight','cutcontent','image','symbol',
  'chip','kpi','banner','quote','divider','chevron','timeline','bracket',
  'chart','progress'
]);

// { pageIndex: [widthPt, heightPt] } as Datum sees them, /Rotate applied.
async function pageSizes(sourceBytes) {
  const doc = await PDFDocument.load(sourceBytes, { updateMetadata: false, throwOnInvalidObject: false });
  const out = {};
  doc.getPages().forEach((pg, i) => {
    const { width, height } = pg.getSize();
    const rot = ((pg.getRotation().angle % 360) + 360) % 360;
    out[i] = (rot === 90 || rot === 270) ? [height, width] : [width, height];
  });
  return out;
}

// Catch the mistakes that render as "nothing" rather than as something wrong.
// Returns the problem list; throws unless { strict: false }.
function verify(project, sizes, opts) {
  const problems = [];
  const seen = new Set();
  const items = new Map((project.takeoffItems || []).map(i => [i.id, i]));
  const compatible = {
    measure: ['length','vertical'], polyline: ['length','vertical'],
    dimension: ['length','vertical'], area: ['area','volume'], count: ['count']
  };
  const measuredPages = new Set();

  (project.annotations || []).forEach(a => {
    if (!a.id) problems.push('annotation with no id');
    else if (seen.has(a.id)) problems.push(`duplicate id ${a.id}`);
    seen.add(a.id);

    if (!VALID_TYPES.has(a.type))
      problems.push(`${a.id}: unknown type "${a.type}" — Datum draws a placeholder box`);

    if (!Number.isInteger(a.page) || a.page < 0)
      problems.push(`${a.id}: page must be a 0-based int, got ${a.page}`);
    else if (sizes && sizes[a.page]) {
      const [w, h] = sizes[a.page];
      const pts = (a.points || []).concat([a.anchor, a.textPos]).filter(Boolean);
      const bad = pts.find(p => p.x < -1 || p.x > w + 1 || p.y < -1 || p.y > h + 1);
      if (bad) problems.push(
        `${a.id}: point (${Math.round(bad.x)},${Math.round(bad.y)}) is off a ${Math.round(w)}x${Math.round(h)} page`);
    }

    if (BOX2_TYPES.has(a.type) && (a.points || []).length !== 2)
      problems.push(`${a.id}: ${a.type} needs exactly 2 points`);

    if (a.takeoffItemId) {
      const it = items.get(a.takeoffItemId);
      if (!it) problems.push(`${a.id}: takeoffItemId ${a.takeoffItemId} has no matching item`);
      else {
        const ok = compatible[a.type];
        if (ok && !ok.includes(it.resultType))
          problems.push(`${a.id}: ${a.type} cannot feed a "${it.resultType}" item`);
      }
      if (Number.isInteger(a.page)) measuredPages.add(a.page);
    }

    // A boolean here is the classic silent failure: canvas rejects it as a
    // fillStyle and keeps the previous colour, so the text vanishes.
    if (a.boxFill === true || a.labelBackground === true)
      problems.push(`${a.id}: boxFill/labelBackground must be a colour STRING or false, never true`);
  });

  [...measuredPages].sort((x, y) => x - y).forEach(pg => {
    if (!(project.pageCalibrations || {})[String(pg)])
      problems.push(`page ${pg} has measured shapes but no calibration (quantities read "Not calibrated")`);
  });

  if (problems.length && (!opts || opts.strict !== false))
    throw new Error('Datum payload problems:\n  - ' + problems.join('\n  - '));
  return problems;
}

async function embedDatumMarkup(sourceBytes, project) {
  const doc = await PDFDocument.load(sourceBytes, {
    updateMetadata: false, throwOnInvalidObject: false
  });
  const b64 = Buffer.from(JSON.stringify(project), 'utf8').toString('base64');
  const info = doc.getInfoDict();
  info.set(PDFName.of('BDMMarkupData'), PDFHexString.fromText(b64));
  info.set(PDFName.of('BDMVersion'), PDFHexString.fromText('4'));
  info.set(PDFName.of('BDMBakedOverlay'), PDFHexString.fromText('0'));
  return await doc.save();
}

module.exports = { embedDatumMarkup, pageSizes, verify, VALID_TYPES, BOX2_TYPES };

// CLI: node datum-markup-node.js source.pdf project.json output.pdf
if (require.main === module) {
  const fs = require('fs');
  const [src, proj, out] = process.argv.slice(2);
  if (!out) { console.error('usage: node datum-markup-node.js <source.pdf> <project.json> <output.pdf>'); process.exit(1); }
  const bytes = fs.readFileSync(src);
  const project = JSON.parse(fs.readFileSync(proj, 'utf8'));
  pageSizes(bytes)
    .then(sizes => { verify(project, sizes); return embedDatumMarkup(bytes, project); })
    .then(b => { fs.writeFileSync(out, b); console.log('wrote', out, b.length, 'bytes'); })
    .catch(e => { console.error(e.message); process.exit(1); });
}
