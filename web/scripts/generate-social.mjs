/**
 * Generates web/public/social.png — the 1200×630 Open Graph social card.
 * Run once from repo root: node web/scripts/generate-social.mjs
 */

import { createRequire } from 'module';
import { writeFileSync, mkdirSync } from 'fs';
import { dirname, resolve } from 'path';
import { fileURLToPath } from 'url';

const require = createRequire(import.meta.url);
const puppeteer = require('/opt/homebrew/lib/node_modules/puppeteer/lib/puppeteer/puppeteer.js');

const __dirname = dirname(fileURLToPath(import.meta.url));
const outputPath = resolve(__dirname, '../public/social.png');

const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    width: 1200px;
    height: 630px;
    background: #0b0e12;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 80px 96px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    overflow: hidden;
  }
  .eyebrow {
    font-size: 18px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #e8952b;
    margin-bottom: 28px;
  }
  .name {
    font-size: 64px;
    font-weight: 800;
    color: #f8fafc;
    line-height: 1.05;
    margin-bottom: 32px;
    letter-spacing: -0.02em;
  }
  .tagline {
    font-size: 26px;
    font-weight: 400;
    color: rgba(248, 250, 252, 0.65);
    line-height: 1.5;
    max-width: 700px;
  }
  .rule {
    width: 56px;
    height: 4px;
    background: #e8952b;
    margin-bottom: 36px;
    border-radius: 2px;
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

const browser = await puppeteer.launch({ headless: true });
const page = await browser.newPage();
await page.setViewport({ width: 1200, height: 630, deviceScaleFactor: 1 });
await page.setContent(html, { waitUntil: 'networkidle0' });

mkdirSync(dirname(outputPath), { recursive: true });
const screenshot = await page.screenshot({ type: 'png' });
writeFileSync(outputPath, screenshot);

await browser.close();
console.log(`social.png written to ${outputPath}`);
