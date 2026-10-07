// build_ai_context.mjs — builds <Project>\00_ai_sandbox\AI_Context\ per CLAUDE.md §8 (R5, 7/10/26).
// Part of the bdm-project-sandbox-setup skill (R2). Shared plumbing and library install: common.mjs.
//
// Converts the project's static documents (except drawings) to markdown, one file per source,
// each with a source/revision header so staleness can be detected. Read-only on project documents.
// Idempotent: a source whose modified time and size match its copy's header is skipped.
//
// usage:
//   node build_ai_context.mjs --project "<job folder>" [--project ...] [--dry] [--limit N]
//   node build_ai_context.mjs --projects-file <txt> | --all
//   node build_ai_context.mjs --all --legacy-only     (Word/Excel pre-pass; run once before parallel builds)
//
// Excluded (logged to AI_Context\_build_log.csv with the reason):
//   - drawings (large-format PDF pages with title-block text or little text), any folder
//   - live registers (spreadsheets/CSVs named register / CAR / tracker / log / fee register / cashflow)
//   - superseded or archived copies (ss, superseded, _ARCHIVE, old, _DELETE folders)
//   - 00_ai_sandbox and 00_Email Communication, Office lock files, non-document types
//   - the duplicate of a same-name pair in one folder (PDF kept as the issued form, unless it has no text)
// .doc / .xls are converted to .docx / .xlsx through Word / Excel first (convert_legacy.ps1), cached outside the library.

import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { flag, opt, ROOT, CACHE, TODAY, sha, selectProjects, loadLibs } from './common.mjs';

const G = await loadLibs();
const JSZip = G.JSZip;
const pdfjs = G.pdfjs;

const HERE = path.dirname(fileURLToPath(import.meta.url));
const DRY = flag('--dry');
const LIMIT = opt('--limit') ? +opt('--limit') : Infinity;
const projects = selectProjects();

const RULES = 5;   // bump when classification or extraction rules change: older copies are rebuilt
const DOC_EXT = new Set(['.pdf', '.docx', '.doc', '.xlsx', '.xlsm', '.xls', '.txt', '.md', '.pptx']);
const SKIP_TOP = /^(00_ai_sandbox|00_AI_sandbox|00_Email Communication)$/i;
const SUPERSEDED_SEG = /^(_?ss|_?superseded.*|.*\bsuperseded\b.*|_?archive.*|_archive_.*|old|_old|zz_?old.*|_delete.*|_?backup.*)$/i;
const LIVE_REGISTER = /(register|\bcar\b|tracker|\blog\b|cash ?flow|fee register|correspondence)/i;
const DRAWING_PATH = /(drawing|\bdwg\b|architectur|structural|hydraulic|electrical|mechanical|civil|landscap|survey|shop ?dr|\bplans?\b|elevations?|\bsections?\b(?!\s*\d)|mark ?up|sketch|layout)/i;
// word-bounded on purpose: "inspection" contains "spec", "Approved" contains "ppr"
const SPEC_HINT = /\b(specs?|specifications?|management plan|execution plan|safety|traffic|finish(es)?|schedules?|reports?|brief|ppr|requirements|certificates?|letters?|memos?|minutes|notices?|approvals?|decisions?|conditions)\b/i;
const DRAWING_TEXT = /(scale\s*[:@]?\s*1\s*:\s*\d|drawing\s*(no|number|title)|dwg\.?\s*no|sheet\s*(no|number)|north\s*point|do not scale|issued for construction|revision\s+description|drawn\s*(by)?\s*:|checked\s*(by)?\s*:|surveyed by|job ref|datum\s*:)/i;
// "Read this first" list: tested on the FILE NAME (a folder called "13_Contract Admin" must not make everything core),
// plus anything filed in a contract-documents folder. Routine instruments and correspondence are never core.
const CORE_NAME = /(\bcontract\b|agreement|special conditions?|general conditions?|contract particulars|annexure|specification|\bspecs?\b|\bppr\b|principal'?s project requirements|decision notice|development approval|building approval|conditions of approval|scope of works?|preliminaries)/i;
const CORE_FOLDER = /(^|[\\/])\d*_?contract documents([\\/]|$)/i;
const NOT_CORE = /(invoice|claim|certificate|payment|recommendation|\bcsa\b|\beot\b|variation|minutes|quote|quotation|statutory declaration|insurance|currency|swms|transmittal|letter|email|notice of delay|\bnod\b|\bpc\s?\d)/i;
const isCore = rel => { const name = path.basename(rel); return !NOT_CORE.test(name) && (CORE_NAME.test(name) || CORE_FOLDER.test(path.dirname(rel))); };

const metaPath = out => path.join(CACHE, 'meta', sha(out.toLowerCase()) + '.json');
const esc = s => String(s ?? '').replace(/\|/g, '\\|').replace(/\r?\n/g, ' ').trim();

// ---------- discovery ----------
function walk(base, skipTop = null) {
  const out = [];
  const stack = [''];
  while (stack.length) {
    const rel = stack.pop();
    let ents; try { ents = fs.readdirSync(path.join(base, rel), { withFileTypes: true }); } catch { continue; }
    for (const e of ents) {
      const r = rel ? path.join(rel, e.name) : e.name;
      if (e.isDirectory()) { if (!(rel === '' && skipTop && skipTop.test(e.name))) stack.push(r); } else if (e.isFile()) out.push(r);
    }
  }
  return out;
}

function classify(base, rels) {
  const keep = [], skip = [];
  for (const rel of rels) {
    const segs = rel.split(path.sep); const name = segs[segs.length - 1]; const ext = path.extname(name).toLowerCase();
    const why = (reason) => skip.push({ rel, reason });
    if (!DOC_EXT.has(ext)) { if (['.csv'].includes(ext)) why('live register (csv)'); continue; }
    if (name.startsWith('~$')) { why('office lock file'); continue; }
    if (SKIP_TOP.test(segs[0])) { why('sandbox / email folder'); continue; }
    if (segs.slice(0, -1).some(s => SUPERSEDED_SEG.test(s))) { why('superseded or archived copy'); continue; }
    if (['.xlsx', '.xlsm', '.xls'].includes(ext) && LIVE_REGISTER.test(name)) { why('live register (read from source)'); continue; }
    keep.push(rel);
  }
  // same-stem pairs in one folder: prefer the PDF (issued form); fall back later if it has no text
  const byStem = new Map();
  for (const rel of keep) {
    const k = path.join(path.dirname(rel), path.basename(rel, path.extname(rel))).toLowerCase();
    (byStem.get(k) ?? byStem.set(k, []).get(k)).push(rel);
  }
  const primary = [], alternates = new Map();
  for (const group of byStem.values()) {
    if (group.length === 1) { primary.push(group[0]); continue; }
    const pdf = group.find(r => r.toLowerCase().endsWith('.pdf'));
    const lead = pdf ?? group[0];
    primary.push(lead);
    alternates.set(lead, group.filter(r => r !== lead));
  }
  return { primary, alternates, skip };
}

// ---------- output naming (flat per top folder, short, collision-safe) ----------
function outPathFor(aiDir, rel, used) {
  const segs = rel.split(path.sep);
  const top = segs.length > 1 ? segs[0].replace(/[<>:"|?*]/g, '_').slice(0, 40) : '_root';
  const ext = path.extname(rel).slice(1).toLowerCase();
  let stem = path.basename(rel, path.extname(rel)).replace(/[<>:"|?*\[\]#%{}]/g, '_').replace(/\s+/g, ' ').trim();
  const budget = 235 - path.join(aiDir, top).length - ext.length - 12;
  stem = stem.slice(0, Math.max(20, Math.min(70, budget)));
  let file = `${stem}__${ext}.md`;
  const key = path.join(top, file).toLowerCase();
  if (used.has(key) && used.get(key) !== rel) file = `${stem}__${ext}__${sha(rel).slice(0, 6)}.md`;
  used.set(path.join(top, file).toLowerCase(), rel);
  return path.join(aiDir, top, file);
}

// ---------- extractors ----------
async function extractPdf(abs, relForRules) {
  const data = new Uint8Array(fs.readFileSync(abs));
  const doc = await pdfjs.getDocument({ data, standardFontDataUrl: G.STANDARD_FONT_DATA_URL, cMapUrl: G.CMAP_URL, cMapPacked: true, verbosity: 0, isEvalSupported: false }).promise;
  const pages = []; let big = 0, chars = 0;
  for (let n = 1; n <= doc.numPages; n++) {
    const p = await doc.getPage(n);
    const vp = p.getViewport({ scale: 1 });
    if (Math.max(vp.width, vp.height) >= 1150) big++;
    const tc = await p.getTextContent();
    const rows = [];
    for (const it of tc.items) {
      if (!it.str) continue;
      const y = Math.round(it.transform[5]); const x = it.transform[4];
      let row = rows.find(r => Math.abs(r.y - y) <= 2);
      if (!row) rows.push(row = { y, items: [] });
      row.items.push({ x, s: it.str });
    }
    rows.sort((a, b) => b.y - a.y);
    const text = rows.map(r => r.items.sort((a, b) => a.x - b.x).map(i => i.s).join(' ').replace(/\s+/g, ' ').trim()).filter(Boolean).join('\n');
    chars += text.length; pages.push(text);
    p.cleanup();
  }
  await doc.destroy();
  const n = pages.length || 1;
  const largeFormat = big / n >= 0.5;
  const sample = pages.slice(0, 3).join('\n');
  const noText = chars / n < 40;
  const lines = pages.join('\n').split('\n').filter(Boolean);
  const prose = lines.filter(l => l.split(/\s+/).length >= 8).length / Math.max(1, lines.length);   // drawings are labels, documents are sentences
  const titleBlock = DRAWING_TEXT.test(sample);
  const pathHint = DRAWING_PATH.test(relForRules) && !SPEC_HINT.test(path.basename(relForRules));
  const isDrawing = (largeFormat && (titleBlock || chars / n < 1200 || pathHint)) || (titleBlock && prose < 0.12) || (titleBlock && pathHint && prose < 0.3) || (noText && pathHint);
  const body = pages.map((t, i) => `## Page ${i + 1}\n\n${t || '_[no text on this page]_'}`).join('\n\n');
  return { body, pages: pages.length, isDrawing, noText, words: body.split(/\s+/).length };
}

function decodeXml(s) { return s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&#(\d+);/g, (_, d) => String.fromCharCode(+d)).replace(/&amp;/g, '&'); }
function splitTop(xml, tag) {   // top-level <tag ...>...</tag> blocks, depth-aware
  const out = []; const open = new RegExp(`<${tag}[\\s>/]`, 'g'); const close = `</${tag}>`;
  let i = 0;
  while (true) {
    open.lastIndex = i; const m = open.exec(xml); if (!m) break;
    let depth = 0, j = m.index;
    while (j < xml.length) {
      open.lastIndex = j; const o = open.exec(xml); const c = xml.indexOf(close, j);
      if (c < 0) { j = xml.length; break; }
      if (o && o.index < c) { const selfClose = xml.slice(o.index, xml.indexOf('>', o.index) + 1).endsWith('/>'); if (!selfClose) depth++; j = xml.indexOf('>', o.index) + 1; if (selfClose && depth === 0) break; }
      else { depth--; j = c + close.length; if (depth === 0) break; }
    }
    out.push(xml.slice(m.index, j)); i = j;
  }
  return out;
}
function paraText(p) {
  return decodeXml(p.replace(/<w:tab\/>/g, '\t').replace(/<w:br[^>]*\/>/g, '\n').replace(/<w:delText[^>]*>[\s\S]*?<\/w:delText>/g, '')
    .replace(/<w:t(?:\s[^>]*)?>([\s\S]*?)<\/w:t>/g, '\u0001$1\u0002').replace(/<[^>]+>/g, '').replace(/[^\u0001\u0002]*\u0001([^\u0002]*)\u0002/g, '$1'));
}
function blockText(xml) { return splitTop(xml, 'w:p').map(paraText).join(' / ').replace(/\s+/g, ' ').trim(); }
async function extractDocx(abs) {
  const zip = await JSZip.loadAsync(fs.readFileSync(abs));
  const f = zip.file('word/document.xml'); if (!f) throw new Error('no word/document.xml');
  const xml = await f.async('string');
  const body = xml.slice(xml.indexOf('<w:body'), xml.lastIndexOf('</w:body>'));
  const out = []; let i = 0;
  const re = /<w:(p|tbl)[\s>]/g;
  while (true) {
    re.lastIndex = i; const m = re.exec(body); if (!m) break;
    const tag = 'w:' + m[1]; const blk = splitTop(body.slice(m.index), tag)[0]; i = m.index + blk.length;
    if (tag === 'w:p') {
      const t = paraText(blk).trim(); if (!t) continue;
      const st = (blk.match(/<w:pStyle w:val="([^"]+)"/) || [])[1] || '';
      const h = st.match(/^(?:Heading|heading)\s?(\d)/); out.push(h ? `${'#'.repeat(Math.min(+h[1] + 1, 6))} ${t}` : t);
    } else {
      const rows = splitTop(blk, 'w:tr').map(tr => splitTop(tr, 'w:tc').map(tc => esc(blockText(tc))));
      if (!rows.length) continue;
      const w = Math.max(...rows.map(r => r.length));
      const pad = r => [...r, ...Array(w - r.length).fill('')];
      out.push(['| ' + pad(rows[0]).join(' | ') + ' |', '|' + ' --- |'.repeat(w), ...rows.slice(1).map(r => '| ' + pad(r).join(' | ') + ' |')].join('\n'));
    }
  }
  const text = out.join('\n\n');
  return { body: text, pages: null, words: text.split(/\s+/).length, noText: text.trim().length < 20 };
}
async function extractXlsx(abs) {
  const wb = new G.ExcelJS.Workbook(); await wb.xlsx.readFile(abs);
  const parts = []; let words = 0;
  wb.eachSheet(ws => {
    if (ws.state && ws.state !== 'visible') { parts.push(`## Sheet: ${ws.name} _(hidden, not converted)_`); return; }
    const rows = []; let truncated = false;
    ws.eachRow({ includeEmpty: false }, (row, rn) => {
      if (rows.length >= 400) { truncated = true; return; }
      const vals = [];
      for (let c = 1; c <= Math.min(row.cellCount, 30); c++) {
        let v = row.getCell(c).value;
        if (v && typeof v === 'object') { if (v.result !== undefined) v = v.result; else if (v.richText) v = v.richText.map(t => t.text).join(''); else if (v.text) v = v.text; else if (v instanceof Date) v = isNaN(v) ? '' : v.toISOString().slice(0, 10); else if (v.error) v = v.error; else v = ''; }
        if (v instanceof Date) v = isNaN(v) ? '[invalid date]' : v.toISOString().slice(0, 10);
        if (typeof v === 'number') v = Math.round(v * 100) / 100;
        vals.push(esc(v));
      }
      while (vals.length && !vals[vals.length - 1]) vals.pop();
      if (vals.length) rows.push(`| ${rn} | ${vals.join(' | ')} |`);
    });
    words += rows.join(' ').split(/\s+/).length;
    parts.push(`## Sheet: ${ws.name}\n\n` + (rows.length ? rows.join('\n') : '_[empty]_') + (truncated ? '\n\n_[truncated at 400 rows: read the source for the rest]_' : ''));
  });
  return { body: parts.join('\n\n'), pages: wb.worksheets.length, words, noText: words < 5 };
}
async function extractPptx(abs) {
  const zip = await JSZip.loadAsync(fs.readFileSync(abs));
  const slides = Object.keys(zip.files).filter(n => /^ppt\/slides\/slide\d+\.xml$/.test(n)).sort((a, b) => +a.match(/\d+/)[0] - +b.match(/\d+/)[0]);
  const parts = [];
  for (const s of slides) { const x = await zip.file(s).async('string'); parts.push(`## Slide ${s.match(/\d+/)[0]}\n\n` + decodeXml((x.match(/<a:t>([\s\S]*?)<\/a:t>/g) || []).map(t => t.replace(/<\/?a:t>/g, '')).join(' '))); }
  const body = parts.join('\n\n'); return { body, pages: slides.length, words: body.split(/\s+/).length, noText: body.length < 20 };
}

// legacy .doc / .xls → cached .docx / .xlsx via Office COM (one batch per project)
function convertLegacy(list) {
  if (!list.length) return new Map();
  const jobs = list.map(abs => ({ src: abs, dst: path.join(CACHE, sha(abs + fs.statSync(abs).mtimeMs) + (abs.toLowerCase().endsWith('.doc') ? '.docx' : '.xlsx')) }));
  const todo = jobs.filter(j => !fs.existsSync(j.dst));
  if (todo.length) {
    const jf = path.join(CACHE, `jobs_${process.pid}.json`); fs.writeFileSync(jf, JSON.stringify(todo));
    try { execFileSync('powershell', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', path.join(HERE, 'convert_legacy.ps1'), '-Jobs', jf], { stdio: 'inherit', timeout: 30 * 60e3 }); }
    catch (e) { console.error('legacy conversion error:', e.message); }
    fs.rmSync(jf, { force: true });
  }
  return new Map(jobs.filter(j => fs.existsSync(j.dst)).map(j => [j.src, j.dst]));
}

function header(rel, st, meta) {
  return ['---',
    `source: ${rel.split(path.sep).join('/')}`,
    `source_modified: ${new Date(st.mtimeMs + 10 * 3600e3).toISOString().slice(0, 16).replace('T', ' ')} (Brisbane)`,
    `source_bytes: ${st.size}`,
    meta.pages != null ? `pages_or_sheets: ${meta.pages}` : null,
    `method: ${meta.method}`,
    `quality: ${meta.quality}`,
    `converted: ${TODAY}`,
    `rules: ${RULES}`,
    'stale_rule: if the source file\'s modified time or size no longer matches the two lines above, this copy is stale. Read the source and flag it for re-conversion.',
    '---', ''].filter(l => l !== null).join('\n');
}
function readHeader(file) {
  try { const h = fs.readFileSync(file, 'utf8').slice(0, 900); if (+((h.match(/^rules: (\d+)/m) || [])[1]) !== RULES) return null; return { mod: (h.match(/^source_modified: (.*)$/m) || [])[1], bytes: +((h.match(/^source_bytes: (\d+)/m) || [])[1]) }; } catch { return null; }
}

// ---------- per project ----------
async function runProject(proj) {
  const base = path.join(ROOT, proj);
  const sandbox = fs.readdirSync(base).find(d => /^00_ai_sandbox$/i.test(d));
  if (!sandbox) { console.log(`${proj}: NO SANDBOX — skipped (flag)`); return { proj, error: 'no sandbox' }; }
  const aiDir = path.join(base, sandbox, 'AI_Context');
  const { primary, alternates, skip } = classify(base, walk(base, /^00_ai_sandbox$/i));
  const todo = primary.slice(0, LIMIT);
  console.log(`${proj}: ${todo.length} to process, ${skip.length} excluded by rule`);
  if (DRY) return { proj, todo: todo.length, skip: skip.length };
  if (flag('--legacy-only')) { const m = convertLegacy(todo.filter(r => /\.(doc|xls)$/i.test(r)).map(r => path.join(base, r))); console.log(`${proj}: legacy cached ${m.size}`); return { proj, legacy: m.size }; }

  fs.mkdirSync(aiDir, { recursive: true });
  const legacy = convertLegacy(todo.filter(r => /\.(doc|xls)$/i.test(r)).map(r => path.join(base, r)));
  const used = new Map(); const done = []; const log = skip.map(s => ({ ...s, out: '' }));
  const t0 = Date.now(); let k = 0;
  const handle = async (rel, isAlt = false) => {
    const abs = path.join(base, rel); const st = fs.statSync(abs); const ext = path.extname(rel).toLowerCase();
    const out = outPathFor(aiDir, rel, used);
    const prev = readHeader(out);
    const mod = `${new Date(st.mtimeMs + 10 * 3600e3).toISOString().slice(0, 16).replace('T', ' ')} (Brisbane)`;
    if (prev && prev.mod === mod && prev.bytes === st.size) { let m = {}; try { m = JSON.parse(fs.readFileSync(metaPath(out), 'utf8')); } catch {} done.push({ rel, out, cached: true, ...m }); log.push({ rel, reason: 'unchanged since last build', out: path.relative(aiDir, out) }); return 'cached'; }
    let r, method;
    const timed = (p) => Promise.race([p, new Promise((_, rej) => setTimeout(() => rej(new Error('timed out after 240s')), 240e3))]);
    try {
      if (ext === '.pdf') { r = await timed(extractPdf(abs, rel)); method = 'pdf-text'; }
      else if (ext === '.docx') { r = await extractDocx(abs); method = 'docx-xml'; }
      else if (ext === '.doc') { const c = legacy.get(abs); if (!c) throw new Error('Word could not open or convert this .doc: read the source'); r = await extractDocx(c); method = 'doc-via-word'; }
      else if (ext === '.xlsx' || ext === '.xlsm') { r = await extractXlsx(abs); method = 'xlsx-cells'; }
      else if (ext === '.xls') { const c = legacy.get(abs); if (!c) throw new Error('Excel could not open this .xls (Office file block or damaged): read the source'); r = await extractXlsx(c); method = 'xls-via-excel'; }
      else if (ext === '.pptx') { r = await extractPptx(abs); method = 'pptx-text'; }
      else { const t = fs.readFileSync(abs, 'utf8'); r = { body: t, pages: null, words: t.split(/\s+/).length, noText: t.trim().length < 5 }; method = 'text'; }
    } catch (e) { log.push({ rel, reason: 'error: ' + e.message.slice(0, 120), out: '' }); return 'error'; }
    if (r.isDrawing) { log.push({ rel, reason: r.noText ? 'image-only pages (scanned drawings or photos)' : 'drawing (large-format, title block or little text)', out: '' }); return 'drawing'; }
    if (r.noText && ext === '.pdf' && !isAlt && alternates.has(rel)) {   // scanned PDF with an editable twin: use the twin
      for (const alt of alternates.get(rel)) { const res = await handle(alt, true); if (res === 'ok') { log.push({ rel, reason: 'no text layer; converted the same-name ' + path.extname(alt) + ' instead', out: '' }); return 'ok'; } }
    }
    const quality = r.noText ? (ext === '.pdf' ? 'no-text-layer (scanned: needs OCR, read the source)' : 'empty') : 'ok';
    const meta = { pages: r.pages, words: r.words, quality, method };
    fs.mkdirSync(path.dirname(out), { recursive: true });
    fs.writeFileSync(out, header(rel, st, { pages: r.pages, method, quality }) + `# ${path.basename(rel)}\n\n` + r.body + '\n');
    fs.mkdirSync(path.dirname(metaPath(out)), { recursive: true }); fs.writeFileSync(metaPath(out), JSON.stringify(meta));
    done.push({ rel, out, ...meta });
    log.push({ rel, reason: 'converted', out: path.relative(aiDir, out) });
    return 'ok';
  };
  for (const rel of todo) {
    await handle(rel);
    for (const alt of alternates.get(rel) ?? []) if (!done.some(d => d.rel === alt)) log.push({ rel: alt, reason: 'duplicate of ' + path.basename(rel), out: '' });
    if (++k % 50 === 0) console.log(`  ${proj}: ${k}/${todo.length} (${Math.round((Date.now() - t0) / 1000)}s)`);
  }

  // remove converted copies whose source is gone or now out of scope (only script-generated .md inside AI_Context)
  const keepOut = new Set(done.map(d => d.out.toLowerCase())); let removed = 0;
  for (const r2 of walk(aiDir)) {
    const f = path.join(aiDir, r2); const bn = path.basename(r2);
    if (!f.endsWith('.md') || bn === 'INDEX.md' || bn === '_INDEX.md') continue;
    if (!keepOut.has(f.toLowerCase())) { fs.rmSync(f, { force: true }); removed++; }
  }
  if (removed) log.push({ rel: '(AI_Context sweep)', reason: `removed ${removed} copies no longer in scope`, out: '' });
  // per-folder indexes + the routing INDEX.md
  const byTop = new Map();
  for (const d of done) { const top = path.relative(aiDir, d.out).split(path.sep)[0]; (byTop.get(top) ?? byTop.set(top, []).get(top)).push(d); }
  for (const [top, list] of byTop) {
    list.sort((a, b) => a.rel.localeCompare(b.rel));
    fs.writeFileSync(path.join(aiDir, top, '_INDEX.md'), `# ${top}: converted documents\n\nGenerated ${TODAY}. One row per source document. Read the converted file; check its header against the source before relying on it.\n\n| Converted file | Source | Pages | Words | Quality |\n|---|---|---|---|---|\n` +
      list.map(d => `| ${esc(path.basename(d.out))} | ${esc(d.rel.split(path.sep).join('/'))} | ${d.pages ?? ''} | ${d.words ?? ''} | ${esc(d.quality)} |`).join('\n') + '\n');
  }
  const core = done.filter(d => isCore(d.rel) && (d.quality === 'ok' || String(d.quality).startsWith('ocr'))).sort((a, b) => a.rel.localeCompare(b.rel));
  const scanned = done.filter(d => String(d.quality).startsWith('no-text'));
  const ocrd = done.filter(d => String(d.quality).startsWith('ocr'));
  const counts = log.reduce((m, l) => { const k2 = l.reason.startsWith('duplicate') ? 'duplicate' : l.reason.startsWith('error') ? 'error' : l.reason; m[k2] = (m[k2] || 0) + 1; return m; }, {});
  const idx = [`# AI_Context: ${proj}`, '',
    `Generated ${TODAY} by the bdm-project-sandbox-setup skill (scripts\\build_ai_context.mjs) under CLAUDE.md §8 (R5).`, '',
    'This folder holds the project\'s static documents, except drawings, converted to markdown. Each file opens with a header naming its source, the source\'s modified time and size, and the conversion date. **If the source has changed since, the copy is stale: read the source and flag it.** Live registers (CAR, correspondence register, fee registers, trackers) are never copied here: always read them from source.', '',
    '## How to use it', '',
    '1. Read the project summary first. It holds the current position.',
    '2. For what a document actually says, find it below or in the folder `_INDEX.md`, open the converted file, and check its header.',
    '3. Quote from the converted text, cite the source path, and verify any clause you will rely on against the source before issue.', '',
    `## Read this first: contract, specification and approvals (${core.length})`, '',
    '| Converted file | Source |', '|---|---|',
    ...core.map(d => `| ${esc(path.relative(aiDir, d.out).split(path.sep).join('/'))} | ${esc(d.rel.split(path.sep).join('/'))} |`), '',
    '## By folder', '', '| Folder | Documents | Index |', '|---|---|---|',
    ...[...byTop.keys()].sort().map(t => `| ${esc(t)} | ${byTop.get(t).length} | ${esc(t)}/_INDEX.md |`), '',
    `## Read by OCR (${ocrd.length})`, '', ocrd.length ? 'These were scanned PDFs, machine-read with Windows OCR. Each file says so in its header. OCR can misread figures, dates and names: check anything you will rely on against the source. Folder indexes mark them.' : 'None.', '',
    `## Still unreadable (${scanned.length})`, '', scanned.length ? 'Scanned PDFs where OCR found no usable text (photos, handwriting, or not yet OCR\'d). Their converted file is a stub. Read the source.' : 'None.', '',
    ...scanned.slice(0, 200).map(d => `- ${d.rel.split(path.sep).join('/')}`), scanned.length > 200 ? `- ... and ${scanned.length - 200} more (see folder indexes)` : '', '',
    '## Build summary', '', '| Outcome | Files |', '|---|---|', ...Object.entries(counts).sort((a, b) => b[1] - a[1]).map(([k3, v]) => `| ${esc(k3)} | ${v} |`), '',
    'Full per-file log: `_build_log.csv` in this folder.', ''].join('\n');
  fs.writeFileSync(path.join(aiDir, 'INDEX.md'), idx);
  fs.writeFileSync(path.join(aiDir, '_build_log.csv'), 'source,outcome,converted_file\n' + log.map(l => [l.rel, l.reason, l.out].map(v => '"' + String(v).replace(/"/g, '""') + '"').join(',')).join('\n') + '\n');
  const bytes = done.reduce((s, d) => { try { return s + fs.statSync(d.out).size; } catch { return s; } }, 0);
  const res = { proj, converted: done.length, core: core.length, scanned: scanned.length, counts, mb: Math.round(bytes / 1048576 * 10) / 10, secs: Math.round((Date.now() - t0) / 1000) };
  console.log(JSON.stringify(res));
  return res;
}

const results = [];
for (const p of projects) results.push(await runProject(p));
const summaryFile = path.join(CACHE, `run_${TODAY}_${process.pid}.json`);
fs.writeFileSync(summaryFile, JSON.stringify(results, null, 1));
console.log('summary →', summaryFile);
