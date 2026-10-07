// ocr_stubs.mjs — finds AI_Context stubs for scanned PDFs (quality: no-text-layer) and fills them with
// Windows OCR text (ocr_batch.ps1). Keeps the original header so the builder's stale check still works;
// only the method and quality lines change. OCR text is cached outside the library so re-runs are free.
//
// Windows only (uses the built-in Windows.Media.Ocr engine; nothing is downloaded).
//
// usage: node ocr_stubs.mjs --project "<folder>" [--project ...] | --projects-file <txt> | --all
//        then re-run build_ai_context.mjs for the same projects to refresh the indexes
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { ROOT, CACHE, sha, selectProjects } from './common.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const OCRDIR = path.join(CACHE, 'ocr'); fs.mkdirSync(OCRDIR, { recursive: true });
const projects = selectProjects();
const metaPath = out => path.join(CACHE, 'meta', sha(out.toLowerCase()) + '.json');
const QUALITY_OCR = 'ocr (machine-read from a scan: check figures, dates, names and clause numbers against the source before relying on them)';
const QUALITY_EMPTY = 'no-text-layer (OCR found no readable text: photos or handwriting, read the source)';

function walk(dir) { const out = []; for (const e of fs.readdirSync(dir, { withFileTypes: true })) { const p = path.join(dir, e.name); if (e.isDirectory()) out.push(...walk(p)); else if (e.name.endsWith('.md')) out.push(p); } return out; }

const jobs = [];
for (const proj of projects) {
  const base = path.join(ROOT, proj);
  const sb = fs.readdirSync(base).find(d => /^00_ai_sandbox$/i.test(d)); if (!sb) continue;
  const ai = path.join(base, sb, 'AI_Context'); if (!fs.existsSync(ai)) continue;
  for (const md of walk(ai)) {
    const head = fs.readFileSync(md, 'utf8').slice(0, 1200);
    if (!/^quality: no-text-layer \(scanned/m.test(head)) continue;
    const rel = (head.match(/^source: (.*)$/m) || [])[1]; if (!rel) continue;
    const src = path.join(base, ...rel.split('/'));
    if (!fs.existsSync(src)) continue;
    const st = fs.statSync(src);
    jobs.push({ proj, md, rel, src, txt: path.join(OCRDIR, sha(src + st.mtimeMs + st.size) + '.txt'), pages: +((head.match(/^pages_or_sheets: (\d+)/m) || [])[1] || 0) });
  }
}
const todo = jobs.filter(j => !fs.existsSync(j.txt));
console.log(`stubs: ${jobs.length} (${jobs.reduce((s, j) => s + j.pages, 0)} pages); to OCR now: ${todo.length}`);

// OCR in chunks so one bad file can't sink the batch and progress is visible
for (let i = 0; i < todo.length; i += 20) {
  const chunk = todo.slice(i, i + 20);
  const jf = path.join(OCRDIR, `jobs_${process.pid}.json`);
  // the WinRT file API cannot open paths over 260 characters: OCR a short-path temporary copy instead
  const temps = [];
  const items = chunk.map(j => {
    if (j.src.length < 250) return { src: j.src, txt: j.txt };
    const tmp = path.join(OCRDIR, 'tmp_' + sha(j.src).slice(0, 12) + '.pdf'); fs.copyFileSync(j.src, tmp); temps.push(tmp);
    return { src: tmp, txt: j.txt };
  });
  fs.writeFileSync(jf, JSON.stringify(items));
  try { execFileSync('powershell', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', path.join(HERE, 'ocr_batch.ps1'), '-JobFile', jf], { stdio: 'inherit', timeout: 60 * 60e3 }); }
  catch (e) { console.error('OCR chunk error:', e.message.slice(0, 200)); }
  fs.rmSync(jf, { force: true });
  for (const t of temps) fs.rmSync(t, { force: true });
}

// rewrite each stub with its OCR text, keeping the header (source, modified, bytes, rules) intact
let filled = 0, empty = 0, missing = 0;
for (const j of jobs) {
  if (!fs.existsSync(j.txt)) { missing++; continue; }
  const pages = fs.readFileSync(j.txt, 'utf8').split('\f');
  const words = pages.join(' ').split(/\s+/).filter(Boolean).length;
  const good = words >= 15;
  const old = fs.readFileSync(j.md, 'utf8');
  const end = old.indexOf('\n---\n', 4); const header = old.slice(0, end + 5);
  const newHeader = header.replace(/^method: .*$/m, 'method: pdf-ocr (Windows OCR, en-GB)').replace(/^quality: .*$/m, 'quality: ' + (good ? QUALITY_OCR : QUALITY_EMPTY));
  const body = `# ${path.basename(j.rel)}\n\n` + (good ? '> Machine-read from a scanned PDF. OCR can misread figures, dates and names: check anything you will rely on against the source.\n\n' : '') +
    pages.map((t, i) => `## Page ${i + 1}\n\n${t.trim() || '_[no text recognised on this page]_'}`).join('\n\n') + '\n';
  fs.writeFileSync(j.md, newHeader + body);
  let meta = {}; try { meta = JSON.parse(fs.readFileSync(metaPath(j.md), 'utf8')); } catch {}
  meta.quality = good ? QUALITY_OCR : QUALITY_EMPTY; meta.words = words; meta.method = 'pdf-ocr';
  fs.mkdirSync(path.dirname(metaPath(j.md)), { recursive: true }); fs.writeFileSync(metaPath(j.md), JSON.stringify(meta));
  good ? filled++ : empty++;
}
console.log(JSON.stringify({ stubs: jobs.length, ocr_filled: filled, ocr_found_nothing: empty, ocr_failed: missing }));
