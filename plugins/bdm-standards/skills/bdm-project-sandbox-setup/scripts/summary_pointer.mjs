// summary_pointer.mjs — writes/refreshes the AI_Context pointer block in each project's Project_Summary_*.md
// (CLAUDE.md §13 item 16). Idempotent: replaces the block between the markers if present.
// Inserted at the end of the "Reference / file pointers" section if one exists, else appended at the end.
// After writing, re-reads the file and checks the tail is intact (summaries have been silently truncated before).
//
// usage: node summary_pointer.mjs --project "<folder>" [--project ...] | --projects-file <txt> | --all
import fs from 'node:fs';
import path from 'node:path';
import { ROOT, TODAY, selectProjects } from './common.mjs';

const projects = selectProjects();
const START = '<!-- AI_Context:start -->', END = '<!-- AI_Context:end -->';

for (const proj of projects) {
  const base = path.join(ROOT, proj);
  const sb = fs.readdirSync(base).find(d => /^00_ai_sandbox$/i.test(d));
  const sums = sb ? fs.readdirSync(path.join(base, sb)).filter(f => /^Project_Summary_.*\.md$/i.test(f)) : [];
  if (sums.length !== 1) { console.log(`${proj}: FLAG — ${sums.length} Project_Summary files (expected exactly one); not edited`); continue; }
  const idxFile = path.join(base, sb, 'AI_Context', 'INDEX.md');
  if (!fs.existsSync(idxFile)) { console.log(`${proj}: no AI_Context\\INDEX.md yet; skipped`); continue; }
  const idx = fs.readFileSync(idxFile, 'utf8');
  const count = re => { const m = idx.match(re); return m ? +m[1] : 0; };
  const outcome = name => { const m = idx.match(new RegExp('^\\| ' + name.replace(/[()]/g, '\\$&') + '[^|]*\\| (\\d+) \\|', 'm')); return m ? +m[1] : 0; };
  const converted = outcome('converted') + outcome('unchanged since last build');
  const drawings = outcome('drawing (large-format, title block or little text)') + outcome('image-only pages (scanned drawings or photos)');
  const errors = outcome('error');
  const core = count(/## Read this first: contract, specification and approvals \((\d+)\)/);
  const ocrd = count(/## Read by OCR \((\d+)\)/);
  const ocr = count(/## Still unreadable \((\d+)\)/);
  const block = [START,
    '### AI_Context: static source documents (CLAUDE.md §8, §13 item 16)',
    '',
    `- **Folder:** \`${sb}\\AI_Context\\\`. The project's documents, except drawings, converted to markdown. Start at \`AI_Context\\INDEX.md\`, which lists the contract, specification and approvals first (${core}), then one index per folder.`,
    `- **Last re-index:** ${TODAY}. ${converted} documents converted; ${drawings} drawings excluded; ${ocrd} scanned PDFs read by OCR (check figures against source); ${ocr} still unreadable (stubs); ${errors} could not be converted (listed in \`AI_Context\\_build_log.csv\`).`,
    '- **Never in here:** live registers (CAR, correspondence register, fee registers, trackers). Read those from source.',
    '- **Stale rule:** every file\'s header carries the source\'s modified time and size. If they no longer match, the copy is stale: read the source, and refresh with the bdm-project-sandbox-setup skill (`scripts\\build_ai_context.mjs --project "' + proj + '"`). The monthly audit does this automatically.',
    '- **Quoting:** the summary holds the current position; AI_Context holds what the document says. Quote clauses from AI_Context, cite the source path, and check the source before issue.',
    END].join('\n');

  const file = path.join(base, sb, sums[0]);
  let s = fs.readFileSync(file, 'utf8');
  const before = s.length;
  const tailBefore = s.replace(new RegExp(START + '[\\s\\S]*?' + END), '').trimEnd().slice(-200);
  if (s.includes(START)) s = s.replace(new RegExp(START + '[\\s\\S]*?' + END), () => block);
  else {
    const lines = s.split('\n');
    const h = lines.findIndex(l => /^#{1,4}\s.*(reference|file pointers)/i.test(l));
    if (h >= 0) {
      const level = lines[h].match(/^#+/)[0].length;
      let end = lines.findIndex((l, i) => i > h && new RegExp(`^#{1,${level}}\\s`).test(l));
      if (end < 0) end = lines.length;
      lines.splice(end, 0, '', block, '');
      s = lines.join('\n');
    } else s = s.trimEnd() + '\n\n' + block + '\n';
  }
  fs.writeFileSync(file, s);
  // verify: re-read, block present once, original tail still present, size sane
  const back = fs.readFileSync(file, 'utf8');
  const ok = back.split(START).length === 2 && back.includes(tailBefore) && back.length >= before;
  console.log(`${proj}: ${sums[0]} ${ok ? 'updated, tail verified' : 'WRITE CHECK FAILED: inspect now'} (${before} -> ${back.length} chars)`);
}
