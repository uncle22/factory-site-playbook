#!/usr/bin/env node
/**
 * allintitle: difficulty check.
 *
 * Counts pages that carry a phrase in their title, which is the cheapest
 * available proxy for how crowded that phrase is. Do this in Google — Bing and
 * several regional engines return a normal result count for the operator, which
 * looks like a difficulty number and is not one.
 *
 * Requires puppeteer-core and a local Chrome/Chromium.
 *   npm i puppeteer-core
 *   export CHROME_PATH="/path/to/chrome"
 *
 * Usage:
 *   node allintitle.js "phrase one" "phrase two"
 *   node allintitle.js --json "phrase one"
 *   node allintitle.js --lang en --gl us "phrase one"
 *
 * Exit codes: 0 ok, 6 blocked by a captcha or consent wall.
 */

const puppeteer = require('puppeteer-core');

const CHROME_CANDIDATES = [
  process.env.CHROME_PATH,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium',
  '/usr/bin/chromium-browser',
].filter(Boolean);

const UA =
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
  '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36';

function parseArgs(argv) {
  const options = { json: false, lang: 'en', gl: 'us', queries: [] };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--json') options.json = true;
    else if (arg === '--lang') options.lang = argv[++i];
    else if (arg === '--gl') options.gl = argv[++i];
    else options.queries.push(arg);
  }
  return options;
}

/** Google no longer reliably exposes #result-stats; read the visible text. */
function readCount() {
  const direct = document.querySelector('#result-stats');
  if (direct && direct.textContent.trim()) {
    const m = direct.textContent.replace(/\u00a0/g, ' ').match(/([\d,.]+)/);
    if (m) return m[1];
  }
  const text = document.body.innerText.replace(/\u00a0/g, ' ');
  const match = text.match(/([\d,.]+)\s*(?:results|result|条结果|results? found)/i);
  if (match) return match[1];
  if (/\bno results found\b|\bdid not match any documents\b/i.test(text)) return '0';
  return null;
}

function detectBlock() {
  const text = document.body.innerText.toLowerCase();
  if (text.includes('unusual traffic') || text.includes('recaptcha')) return 'captcha';
  if (document.querySelector('form[action*="consent"]') || text.includes('before you continue')) {
    return 'consent-wall';
  }
  return null;
}

(async () => {
  const options = parseArgs(process.argv.slice(2));
  if (!options.queries.length) {
    console.error('usage: node allintitle.js "phrase" ["phrase two" ...]');
    process.exit(2);
  }

  const executablePath = CHROME_CANDIDATES.find((p) => {
    try { return require('fs').existsSync(p); } catch { return false; }
  });
  if (!executablePath) {
    console.error('Chrome not found. Set CHROME_PATH to your browser binary.');
    process.exit(2);
  }

  const browser = await puppeteer.launch({
    executablePath,
    headless: 'new',
    args: ['--no-sandbox', '--disable-blink-features=AutomationControlled', `--lang=${options.lang}`],
  });

  const page = await browser.newPage();
  await page.setUserAgent(UA);
  await page.setExtraHTTPHeaders({ 'Accept-Language': `${options.lang}-${options.gl},${options.lang}` });
  await page.setViewport({ width: 1280, height: 900 });

  const results = [];
  let blocked = null;

  for (const query of options.queries) {
    const full = /^allintitle:/i.test(query) ? query : `allintitle:${query}`;
    const url =
      `https://www.google.com/search?hl=${options.lang}&gl=${options.gl}&num=10&q=` +
      encodeURIComponent(full);

    let count = null;
    let note = '';
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
      await new Promise((r) => setTimeout(r, 2500 + Math.random() * 1800));

      const block = await page.evaluate(detectBlock);
      if (block) {
        blocked = block;
        note = block;
      } else {
        count = await page.evaluate(readCount);
        if (count === null) note = 'count not found (layout change?)';
      }
    } catch (error) {
      note = String(error).slice(0, 60);
    }

    const numeric = count === null ? null : Number(String(count).replace(/[,.]/g, ''));
    results.push({ query: full, count: numeric, note });
    if (blocked) break;

    // be polite; a burst of identical requests is what triggers the wall
    await new Promise((r) => setTimeout(r, 1200 + Math.random() * 1200));
  }

  await browser.close();

  if (options.json) {
    console.log(JSON.stringify({ blocked, results }, null, 2));
  } else {
    for (const row of results) {
      let verdict = '';
      if (row.count === null) verdict = row.note;
      else if (row.count < 100) verdict = 'weak field';
      else if (row.count < 1000) verdict = 'competitive';
      else if (row.count < 5000) verdict = 'needs authority';
      else verdict = 'skip unless niche angle';
      console.log(
        `${String(row.count === null ? '-' : row.count).padStart(8)}  ${verdict.padEnd(20)}  ${row.query}`
      );
    }
    if (blocked) {
      console.log(`\nblocked: ${blocked}. wait a while, or check manually in a browser.`);
    }
  }

  process.exit(blocked ? 6 : 0);
})();
