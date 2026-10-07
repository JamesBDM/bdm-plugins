// common.mjs — shared plumbing for the AI_Context scripts (bdm-project-sandbox-setup R2).
// No personal paths: everything resolves from the signed-in user's home at runtime (bdm-house-style §9).
//
// Libraries: pdfjs-dist 4.x, exceljs, jszip, loaded from a per-user folder OUTSIDE the synced library
// (default %USERPROFILE%\.george\lib, override with env AI_CONTEXT_LIB). 140 MB of node_modules must never
// sit in SharePoint. One-off install if missing:
//   mkdir "%USERPROFILE%\.george\lib" && cd /d "%USERPROFILE%\.george\lib" && npm init -y && npm install pdfjs-dist@4 exceljs jszip
//
// Project selection (all scripts):
//   --project "<folder>"   one project; repeat the flag for several
//   --projects-file <txt>  one folder name per line (e.g. the user's active list)
//   --all                  every 6-digit job folder at the root that already has a 00_ai_sandbox
//   --root "<path>"        projects root (default %USERPROFILE%\BDM\Projects - Documents)
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

export const args = process.argv.slice(2);
export const flag = n => args.includes(n);
export const opt = n => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : null; };
export const opts = n => args.flatMap((a, i) => (a === n && args[i + 1] ? [args[i + 1]] : []));

export const ROOT = opt('--root') || path.join(os.homedir(), 'BDM', 'Projects - Documents');
export const CACHE = path.join(os.homedir(), '.george', 'ai_context_cache');
fs.mkdirSync(CACHE, { recursive: true });
export const TODAY = new Date(Date.now() + 10 * 3600e3).toISOString().slice(0, 10);   // Brisbane date, no DST
export const sha = s => crypto.createHash('sha1').update(s).digest('hex');
export const findSandbox = base => { try { return fs.readdirSync(base).find(d => /^00_ai_sandbox$/i.test(d)) || null; } catch { return null; } };

export function selectProjects() {
  let list = opts('--project');
  const pf = opt('--projects-file');
  if (pf) list = list.concat(fs.readFileSync(pf, 'utf8').split(/\r?\n/).map(s => s.trim()).filter(s => s && !s.startsWith('#')));
  if (flag('--all')) list = list.concat(fs.readdirSync(ROOT, { withFileTypes: true })
    .filter(e => e.isDirectory() && /^\d{6}_/.test(e.name) && findSandbox(path.join(ROOT, e.name))).map(e => e.name));
  list = [...new Set(list)];
  if (!list.length) { console.error('Give --project "<folder>" (repeatable), --projects-file <txt>, or --all'); process.exit(1); }
  const missing = list.filter(p => !fs.existsSync(path.join(ROOT, p)));
  if (missing.length) { console.error('Not found under ' + ROOT + ': ' + missing.join('; ')); process.exit(1); }
  return list;
}

export async function loadLibs() {
  const LIB = process.env.AI_CONTEXT_LIB || path.join(os.homedir(), '.george', 'lib');
  const nm = path.join(LIB, 'node_modules');
  if (!fs.existsSync(path.join(nm, 'pdfjs-dist'))) {
    console.error(`Libraries not found in ${nm}. Install once (see the top of common.mjs), or set AI_CONTEXT_LIB.`);
    process.exit(2);
  }
  const req = createRequire(path.join(LIB, 'noop.js'));
  const pdfjsDir = path.join(nm, 'pdfjs-dist');
  return {
    pdfjs: await import(pathToFileURL(path.join(pdfjsDir, 'legacy', 'build', 'pdf.mjs')).href),
    STANDARD_FONT_DATA_URL: path.join(pdfjsDir, 'standard_fonts') + path.sep,
    CMAP_URL: path.join(pdfjsDir, 'cmaps') + path.sep,
    ExcelJS: req('exceljs'),
    JSZip: req('jszip'),
  };
}
