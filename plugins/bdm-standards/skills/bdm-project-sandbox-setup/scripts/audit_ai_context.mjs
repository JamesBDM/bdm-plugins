// audit_ai_context.mjs — the AI_Context part of the monthly sandbox audit (CLAUDE.md §13 keep-current triggers).
// Part of the bdm-project-sandbox-setup skill (R2). Read-only unless --refresh is given.
//
// Per project it reports:
//   stale    a converted copy whose source's modified time or size no longer matches the copy's header
//   removed  a converted copy whose source no longer exists
//   new      an in-scope document type added since the last build (not in AI_Context\_build_log.csv at all)
//   missing  a job folder with a sandbox but no AI_Context yet
// With --refresh, every project with any of the above is brought current: legacy pre-pass, build, OCR of new
// scans, index rebuild, and the summary §16 pointer. All of that is internal, reversible work (CLAUDE.md §10).
//
// usage: node audit_ai_context.mjs --all | --project "<folder>" ... | --projects-file <txt>
//                                  [--refresh] [--report "<file.md>"]
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { flag, opt, ROOT, TODAY, findSandbox, selectProjects } from './common.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const projects = selectProjects();
const DOC_EXT = new Set(['.pdf', '.docx', '.doc', '.xlsx', '.xlsm', '.xls', '.txt', '.md', '.pptx', '.csv']);
const brisbane = ms => new Date(ms + 10 * 3600e3).toISOString().slice(0, 16).replace('T', ' ') + ' (Brisbane)';

function walk(dir, rel = '', skipTop = null, out = []) {
  let ents; try { ents = fs.readdirSync(path.join(dir, rel), { withFileTypes: true }); } catch { return out; }
  for (const e of ents) {
    const r = rel ? path.join(rel, e.name) : e.name;
    if (e.isDirectory()) { if (!(rel === '' && skipTop && skipTop.test(e.name))) walk(dir, r, skipTop, out); }
    else if (e.isFile()) out.push(r);
  }
  return out;
}
function parseCsv(text) {
  const rows = []; for (const line of text.split(/\r?\n/).slice(1)) { if (!line) continue; const m = line.match(/^"((?:[^"]|"")*)"/); if (m) rows.push(m[1].replace(/""/g, '"')); }
  return rows;
}

function audit(proj) {
  const base = path.join(ROOT, proj);
  const sb = findSandbox(base);
  if (!sb) return { proj, state: 'no sandbox' };
  const ai = path.join(base, sb, 'AI_Context');
  if (!fs.existsSync(path.join(ai, 'INDEX.md'))) return { proj, state: 'missing', stale: [], removed: [], added: [] };
  const stale = [], removed = [], seen = new Set();
  for (const r of walk(ai)) {
    if (!r.endsWith('.md') || /(^|[\\/])(INDEX|_INDEX)\.md$/.test(r)) continue;
    const head = fs.readFileSync(path.join(ai, r), 'utf8').slice(0, 900);
    const src = (head.match(/^source: (.*)$/m) || [])[1]; if (!src) continue;
    seen.add(src.toLowerCase());
    const abs = path.join(base, ...src.split('/'));
    if (!fs.existsSync(abs)) { removed.push(src); continue; }
    const st = fs.statSync(abs);
    const mod = (head.match(/^source_modified: (.*)$/m) || [])[1]; const bytes = +((head.match(/^source_bytes: (\d+)/m) || [])[1]);
    if (mod !== brisbane(st.mtimeMs) || bytes !== st.size) stale.push(src);
  }
  // anything the last build considered (converted, excluded or failed) is listed in the build log
  const logged = new Set();
  try { for (const s of parseCsv(fs.readFileSync(path.join(ai, '_build_log.csv'), 'utf8'))) logged.add(s.split(path.sep).join('/').toLowerCase()); } catch {}
  const added = walk(base, '', /^00_ai_sandbox$/i)
    .filter(r => DOC_EXT.has(path.extname(r).toLowerCase()) && !path.basename(r).startsWith('~$'))
    .map(r => r.split(path.sep).join('/'))
    .filter(r => !logged.has(r.toLowerCase()) && !seen.has(r.toLowerCase()));
  const idx = fs.readFileSync(path.join(ai, 'INDEX.md'), 'utf8');
  const built = (idx.match(/^Generated (\d{4}-\d{2}-\d{2})/m) || [])[1] || '?';
  const unreadable = +((idx.match(/## Still unreadable \((\d+)\)/) || [])[1] || 0);
  return { proj, state: stale.length || removed.length || added.length ? 'needs refresh' : 'current', built, stale, removed, added, unreadable };
}

const node = (script, extra) => execFileSync(process.execPath, ['--max-old-space-size=6144', path.join(HERE, script), ...extra], { encoding: 'utf8', timeout: 3 * 3600e3, maxBuffer: 64 * 1024 * 1024 });
const before = projects.map(audit);
const toRefresh = before.filter(r => r.state === 'needs refresh' || r.state === 'missing').map(r => r.proj);
const refreshLog = [];
if (flag('--refresh') && toRefresh.length) {
  const pargs = toRefresh.flatMap(p => ['--project', p]);
  const step = (label, script, extra) => { try { node(script, extra); refreshLog.push(`${label}: done`); } catch (e) { refreshLog.push(`${label}: FAILED ${String(e.message).slice(0, 160)}`); } };
  step('legacy Word/Excel pre-pass', 'build_ai_context.mjs', [...pargs, '--legacy-only']);
  step('build', 'build_ai_context.mjs', pargs);
  if (process.platform === 'win32') step('OCR new scans', 'ocr_stubs.mjs', pargs);
  step('index rebuild', 'build_ai_context.mjs', pargs);
  step('summary §16 pointer', 'summary_pointer.mjs', pargs);
}
const after = flag('--refresh') && toRefresh.length ? projects.map(audit) : before;

const list = (title, items) => items.length ? [`**${title} (${items.length})**`, '', ...items.slice(0, 30).map(s => `- ${s}`), items.length > 30 ? `- ... and ${items.length - 30} more` : '', ''] : [];
const md = [`# AI_Context monthly audit — ${TODAY}`, '',
  'Checks every converted copy against its source (CLAUDE.md §8 stale rule) and looks for documents filed since the last build.' + (flag('--refresh') ? ' Projects that needed it were refreshed in the same pass.' : ' Report only: nothing was changed.'), '',
  '| Project | Last build | Stale | Source removed | New since build | Still unreadable | Status' + (flag('--refresh') ? ' after refresh' : '') + ' |',
  '|---|---|---|---|---|---|---|',
  ...before.map((b, i) => { const a = after[i]; return `| ${b.proj} | ${b.built ?? '-'} | ${b.stale?.length ?? '-'} | ${b.removed?.length ?? '-'} | ${b.added?.length ?? '-'} | ${a.unreadable ?? '-'} | ${a.state} |`; }), '',
  ...(refreshLog.length ? ['## Refresh steps', '', ...refreshLog.map(s => `- ${s}`), ''] : []),
  '## Detail (before refresh)', '',
  ...before.flatMap(b => (b.stale?.length || b.removed?.length || b.added?.length) ? [`### ${b.proj}`, '', ...list('Stale', b.stale), ...list('Source removed', b.removed), ...list('New since last build', b.added)] : []),
].join('\n');

const reportFile = opt('--report');
if (reportFile) { fs.mkdirSync(path.dirname(reportFile), { recursive: true }); fs.writeFileSync(reportFile, md + '\n'); console.log('report → ' + reportFile); }
else console.log(md);
console.log(JSON.stringify({ projects: projects.length, needed_refresh: toRefresh.length, refreshed: flag('--refresh') ? toRefresh.length : 0,
  still_needing: after.filter(a => a.state !== 'current').map(a => a.proj) }));
