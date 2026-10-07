#!/usr/bin/env node
// datum-bake.js — make a skill-written PDF show its markups in Adobe / Chrome.
//
// The embed step only writes Datum's editable project data into the PDF, so
// every other viewer shows the clean drawing. This script opens that PDF in
// the REAL Datum app (headless Chromium), runs Datum's own Save, and writes
// out exactly the file a person would get by opening it in Datum and pressing
// Ctrl+S: markups painted onto the pages for every viewer, plus the clean
// original and the live project tucked inside so it still reopens editable.
//
// Because it is Datum's own renderer, every markup type — clouds, symbols,
// BOQ tables, legends, measured quantity labels — comes out identical to the
// app, with nothing to keep in sync when Datum changes.
//
//   node datum-bake.js marked-up.pdf                 # bakes in place
//   node datum-bake.js marked-up.pdf -o baked.pdf
//   node datum-bake.js marked-up.pdf --app path/or/url/to/BDM-PDF-Markup-Tool.html
//
// Needs Node 18+ and Playwright (`npm install playwright`). Browser, first
// match wins: $CHROMIUM_PATH, Playwright's own Chromium
// (`npx playwright install chromium`), installed Chrome, installed Edge.
//
// The app comes from --app, else $DATUM_APP, else the live site. If pdf-lib
// 1.17.1 and pdfjs-dist 3.11.174 are installed next to Playwright they are
// served locally; otherwise the app loads them from its CDN as normal.
//
// Exit code 0 = baked and verified. Anything else = the input is untouched
// and the message says why.
'use strict';
const fs = require('fs');
const path = require('path');
const http = require('http');
const { createRequire } = require('module');

const LIVE_APP = 'https://jamesbdm.github.io/bdm-pdf-tool/BDM-PDF-Markup-Tool.html';
const CDN_PDFJS = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
const CDN_PDFLIB = 'https://unpkg.com/pdf-lib@1.17.1/dist/pdf-lib.min.js';

function fail(msg) { console.error('datum-bake: ' + msg); process.exit(1); }

function parseArgs(argv) {
  const a = { input: null, out: null, app: process.env.DATUM_APP || LIVE_APP, timeout: 600 };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    if (k === '-o' || k === '--out') a.out = argv[++i];
    else if (k === '--app') a.app = argv[++i];
    else if (k === '--timeout') a.timeout = Number(argv[++i]);
    else if (!a.input) a.input = k;
    else fail('unexpected argument ' + k);
  }
  if (!a.input) fail('usage: node datum-bake.js <pdf> [-o out.pdf] [--app path|url] [--timeout seconds]');
  a.out = a.out || a.input;
  return a;
}

// Resolve a package from wherever it is likely installed: next to this
// script, the working directory, or NODE_PATH.
function resolveFrom(name) {
  const bases = [__dirname, process.cwd(), ...(process.env.NODE_PATH || '').split(path.delimiter).filter(Boolean)];
  for (const b of bases) {
    try { return createRequire(path.join(b, 'x.js')).resolve(name); } catch (e) {}
  }
  return null;
}
function load(name) { const p = resolveFrom(name); return p ? require(p) : null; }

async function readApp(src) {
  if (/^https?:\/\//i.test(src)) {
    const res = await fetch(src);
    if (!res.ok) fail('could not fetch the Datum app from ' + src + ' (HTTP ' + res.status + ')');
    return await res.text();
  }
  if (!fs.existsSync(src)) fail('Datum app not found at ' + src);
  return fs.readFileSync(src, 'utf8');
}

// Serve the local pinned libraries when they are installed, so the bake works
// offline. Version-checked: a different build is worse than the CDN.
function vendorLibs() {
  const out = {};
  const want = [
    ['pdf-lib/package.json', '1.17.1', 'pdf-lib/dist/pdf-lib.min.js', 'pdf-lib.min.js'],
    ['pdfjs-dist/package.json', '3.11.174', 'pdfjs-dist/build/pdf.min.js', 'pdf.min.js'],
    ['pdfjs-dist/package.json', '3.11.174', 'pdfjs-dist/build/pdf.worker.min.js', 'pdf.worker.min.js'],
  ];
  for (const [pkg, ver, file, as] of want) {
    const pj = resolveFrom(pkg);
    if (!pj || JSON.parse(fs.readFileSync(pj, 'utf8')).version !== ver) return null;
    const f = resolveFrom(file);
    if (!f) return null;
    out[as] = f;
  }
  return out;
}

function serve(files) {
  const server = http.createServer((req, res) => {
    const rel = decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '');
    const f = files[rel];
    if (f === undefined) { res.writeHead(404).end(); return; }
    res.writeHead(200, { 'Content-Type': rel.endsWith('.html') ? 'text/html' : 'text/javascript' });
    if (Buffer.isBuffer(f)) res.end(f);           // the app page itself
    else fs.createReadStream(f).pipe(res);        // a vendored library file
  });
  return new Promise(r => server.listen(0, '127.0.0.1', () => r(server)));
}

async function launch(pw) {
  const tries = [];
  if (process.env.CHROMIUM_PATH) tries.push(['$CHROMIUM_PATH', { executablePath: process.env.CHROMIUM_PATH }]);
  tries.push(['Playwright Chromium', {}], ['Chrome', { channel: 'chrome' }], ['Edge', { channel: 'msedge' }]);
  const errs = [];
  for (const [label, opts] of tries) {
    try { return await pw.chromium.launch({ headless: true, ...opts }); }
    catch (e) { errs.push(label + ': ' + String(e.message).split('\n')[0]); }
  }
  fail('no usable browser.\n  ' + errs.join('\n  ') + '\n  Fix: npx playwright install chromium');
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const input = path.resolve(args.input);
  if (!fs.existsSync(input)) fail('no such file: ' + input);

  const pw = load('playwright') || load('playwright-core');
  if (!pw) fail('Playwright is not installed. Run: npm install playwright');

  let html = await readApp(args.app);
  const files = { 'datum.html': null };
  const vendor = vendorLibs();
  if (vendor) {
    const before = html;
    html = html.replace(CDN_PDFJS, 'pdf.min.js').replace(CDN_PDFLIB, 'pdf-lib.min.js');
    if (html !== before) {
      html = html.replace('<script src="pdf-lib.min.js"></scr' + 'ipt>',
        '<script src="pdf-lib.min.js"></scr' + 'ipt>\n<script>pdfjsLib.GlobalWorkerOptions.workerSrc = "pdf.worker.min.js";</scr' + 'ipt>');
      Object.assign(files, vendor);
    }
  }
  files['datum.html'] = Buffer.from(html, 'utf8');
  const server = await serve(files);
  const port = server.address().port;

  const browser = await launch(pw);
  const dialogs = [], errors = [];
  try {
    const ctx = await browser.newContext({ acceptDownloads: true });
    const page = await ctx.newPage();
    page.setDefaultTimeout(args.timeout * 1000);
    page.on('dialog', d => { dialogs.push(d.message()); d.accept(); });
    page.on('pageerror', e => errors.push(e.message));

    await page.goto('http://127.0.0.1:' + port + '/datum.html', { waitUntil: 'load' });
    await page.waitForFunction(() => typeof saveProject === 'function' && typeof writeSavedBytes === 'function');
    const appVersion = await page.evaluate(() => typeof APP_VERSION !== 'undefined' ? APP_VERSION : '?');

    // Record what the FILE carries, as Datum's own reader sees it during the
    // open. (After the open, currentPdfBytes is Datum's clean inner copy when
    // there is one, so it can't be asked afterwards.)
    await page.evaluate(() => {
      const orig = readBDMDataFromPdfBytes;
      window.__fileData = null;
      readBDMDataFromPdfBytes = async function (bytes) {
        const d = await orig(bytes);
        if (!window.__fileData) window.__fileData = d && d.project
          ? { n: (d.project.annotations || []).length, baked: !!d.bakedOverlay, clean: !!d.cleanBytes }
          : { n: -1 };
        return d;
      };
    });
    await page.setInputFiles('#pdf-input', input);
    // App state lives in top-level `let` bindings — bare identifiers, not window.*
    await page.waitForFunction(() => typeof pdfDoc !== 'undefined' && pdfDoc
      && typeof currentPdfBytes !== 'undefined' && currentPdfBytes && currentPdfBytes.length > 0
      && window.__fileData);

    const expected = await page.evaluate(() => window.__fileData);
    if (expected.n < 0) fail('this PDF carries no Datum markup data — nothing to bake');
    if (expected.baked && expected.clean) {
      console.log('datum-bake: already baked by Datum — nothing to do');
      if (path.resolve(args.out) !== input) fs.copyFileSync(input, path.resolve(args.out));
      return;
    }
    await page.waitForFunction(n => typeof annotations !== 'undefined' && annotations.length >= n, expected.n);
    await page.evaluate(async () => { if (document.fonts && document.fonts.ready) await document.fonts.ready; });

    // Run the real Save. Intercept only the final write: check the bytes with
    // Datum's reader, then hand them out as a download.
    await page.evaluate(() => {
      window.__bakeCheck = null;
      writeSavedBytes = async function (bytes) {
        const d = await readBDMDataFromPdfBytes(bytes.slice());
        window.__bakeCheck = {
          baked: !!(d && d.bakedOverlay), clean: !!(d && d.cleanBytes),
          n: d && d.project ? (d.project.annotations || []).length : -1, size: bytes.length,
        };
        downloadBlob(bytes, 'application/pdf', 'baked.pdf');
      };
    });
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.evaluate(() => saveProject()),
    ]);
    const check = await page.evaluate(() => window.__bakeCheck);

    if (!check) fail('Datum did not produce a file. ' + dialogs.concat(errors).join(' | '));
    if (!check.baked || !check.clean) {
      fail('Datum saved WITHOUT baking (the drawing was too big for the browser to hold a second copy). '
        + 'The input is unchanged; open it in Datum on a desktop and use Save, or Flatten for a share copy.'
        + (dialogs.length ? '\n  Datum said: ' + dialogs.join(' | ') : ''));
    }
    if (check.n !== expected.n) fail('markup count changed during the bake (' + expected.n + ' → ' + check.n + ') — input left unchanged');

    const out = path.resolve(args.out);
    const tmp = out + '.baking';
    await download.saveAs(tmp);
    fs.renameSync(tmp, out);
    console.log('datum-bake: baked ' + check.n + ' markups with Datum ' + appVersion + ' → ' + out
      + ' (' + (check.size / 1048576).toFixed(1) + ' MB)');
  } finally {
    await browser.close();
    server.close();
  }
}

main().catch(e => fail(e && e.stack || String(e)));
