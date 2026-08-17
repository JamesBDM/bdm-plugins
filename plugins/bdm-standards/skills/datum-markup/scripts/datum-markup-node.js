// datum-markup-node.js — Node.js embed step for the datum-markup skill.
// Use when Python/pypdf isn't available. Requires: npm install pdf-lib
//
//   const { embedDatumMarkup } = require('./datum-markup-node.js');
//   const out = await embedDatumMarkup(fs.readFileSync('source.pdf'), project);
//   fs.writeFileSync('marked-up.pdf', out);
//
// `project` is the payload object described in ../references/annotation-types.md
// (version 4: annotations, pageCalibrations, takeoffItems, ...).
// Coordinates: PDF points, origin TOP-LEFT, y down.
const { PDFDocument, PDFName, PDFHexString } = require('pdf-lib');

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

module.exports = { embedDatumMarkup };

// CLI: node datum-markup-node.js source.pdf project.json output.pdf
if (require.main === module) {
  const fs = require('fs');
  const [src, proj, out] = process.argv.slice(2);
  if (!out) { console.error('usage: node datum-markup-node.js <source.pdf> <project.json> <output.pdf>'); process.exit(1); }
  embedDatumMarkup(fs.readFileSync(src), JSON.parse(fs.readFileSync(proj, 'utf8')))
    .then(bytes => { fs.writeFileSync(out, bytes); console.log('wrote', out, bytes.length, 'bytes'); })
    .catch(e => { console.error(e); process.exit(1); });
}
