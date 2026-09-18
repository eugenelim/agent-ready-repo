/**
 * Generates web/public/social.png — the 1200×630 Open Graph social card.
 *
 *   npm run social --prefix web      (or: node web/scripts/generate-social.mjs)
 *
 * Colours are READ FROM ../src/styles/tokens.css at run time. Nothing here
 * hardcodes a hex. The card previously carried its own private copy of the
 * palette, which is how it kept the withdrawn amber accent for months after
 * the tokens dropped it.
 *
 * The card carries NO chroma. The single vermilion clearance mark
 * (--ds-clearance-dk) means a human cleared something; a social card is not a
 * receipt, so it does not get the mark
 * (docs/design/direction/tech-site-amendment-palette.md).
 */

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = dirname(fileURLToPath(import.meta.url));
const tokensPath = resolve(__dirname, '../src/styles/tokens.css');
const outputPath = resolve(__dirname, '../public/social.png');

/**
 * Parse every `--name: value;` declaration out of tokens.css, then resolve
 * `var(--other)` references transitively so a semantic token yields a literal.
 *
 * @param {string} css - contents of tokens.css
 * @returns {Map<string, string>} token name (with leading `--`) -> literal value
 */
function readTokens(css) {
  const raw = new Map();
  // Strip comments first: they contain hexes in prose and would poison the scan.
  const stripped = css.replace(/\/\*[\s\S]*?\*\//g, '');
  for (const [, name, value] of stripped.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) {
    if (!raw.has(name)) raw.set(name, value.trim());
  }
  const resolved = new Map();
  /** @param {string} name @param {number} depth @returns {string} */
  const resolve_ = (name, depth = 0) => {
    if (resolved.has(name)) return resolved.get(name);
    const value = raw.get(name);
    if (value === undefined) throw new Error(`tokens.css has no ${name}`);
    if (depth > 10) throw new Error(`token reference cycle at ${name}`);
    const out = value.replace(/var\((--[\w-]+)\)/g, (_, ref) => resolve_(ref, depth + 1));
    resolved.set(name, out);
    return out;
  };
  for (const name of raw.keys()) resolve_(name);
  return resolved;
}

const tokens = readTokens(readFileSync(tokensPath, 'utf8'));
/** @param {string} name @returns {string} */
const t = (name) => {
  const value = tokens.get(name);
  if (value === undefined) throw new Error(`tokens.css has no ${name}`);
  return value;
};

// The card's whole palette, every value from tokens.css. Dark zone only —
// the machine ground, the record tones on it, and no accent.
const palette = {
  ground: t('--ds-hero-bg'),          // machine ground, green-black
  heading: t('--ds-hero-fg'),         // primary text on dark
  body: t('--ds-hero-fg-2'),          // secondary text on dark
  eyebrow: t('--ds-hero-fg-muted'),   // muted label on dark
  rule: t('--prim-record-50'),        // the record tone — the rule is a record mark, not an accent
};
// 'Inter Variable' ships via Fontsource for the site; a headless browser has
// no access to it, so the rendered card falls through to the system stack
// that --ds-font-sans already declares.
const fontSans = t('--ds-font-sans');

const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    width: 1200px;
    height: 630px;
    background: ${palette.ground};
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 80px 96px;
    font-family: ${fontSans};
    overflow: hidden;
  }
  .eyebrow {
    font-size: 18px;
    font-weight: ${t('--ds-weight-semibold')};
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: ${palette.eyebrow};
    margin-bottom: 28px;
  }
  .name {
    font-size: 64px;
    font-weight: ${t('--ds-weight-heavy')};
    color: ${palette.heading};
    line-height: ${t('--ds-lead-display')};
    margin-bottom: 32px;
    letter-spacing: ${t('--ds-track-display')};
  }
  .tagline {
    font-size: 26px;
    font-weight: ${t('--ds-weight-regular')};
    color: ${palette.body};
    line-height: 1.5;
    max-width: 700px;
  }
  .rule {
    width: 56px;
    height: 4px;
    background: ${palette.rule};
    margin-bottom: 36px;
    border-radius: ${t('--ds-radius-sm')};
  }
</style>
</head>
<body>
  <div class="eyebrow">agent-ready-repo</div>
  <div class="rule"></div>
  <div class="name">The supervised AI<br>operating model.</div>
  <div class="tagline">Three peer loops across the full SDLC — with mechanical gates and human checkpoints the agent cannot bypass.</div>
</body>
</html>`;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
await page.setContent(html, { waitUntil: 'networkidle' });

mkdirSync(dirname(outputPath), { recursive: true });
writeFileSync(outputPath, await page.screenshot({ type: 'png' }));

await browser.close();
console.log(`social.png written to ${outputPath}`);
console.log(`palette from ${tokensPath}:`, palette);
