import { describe, it, expect } from 'vitest';
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import axe from 'axe-core';

const BUILD_ROOT = join(__dirname, '../../../build');

function loadBodyHtml(htmlPath: string): string {
  const html = readFileSync(htmlPath, 'utf8');
  const bodyMatch = html.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
  return bodyMatch?.[1] ?? html;
}

async function assertNoBlockingViolations(label: string) {
  const results = await axe.run(document.body);
  const blocking = results.violations.filter(
    (v) => v.impact === 'critical' || v.impact === 'serious'
  );
  if (blocking.length > 0) {
    blocking.forEach((v) =>
      console.error(`AXE ${v.impact} [${label}]: ${v.id} — ${v.description}`)
    );
  }
  expect(blocking, `No critical or serious axe violations on ${label}`).toHaveLength(0);
}

describe('fixture page axe (T19)', () => {
  const FIXTURE_HTML = join(BUILD_ROOT, 'primitives-fixture/index.html');

  it('built fixture page exists (run `npm run build` first if this fails)', () => {
    expect(existsSync(FIXTURE_HTML)).toBe(true);
  });

  it('no critical or serious axe violations on built fixture page', async () => {
    if (!existsSync(FIXTURE_HTML)) return;
    document.body.innerHTML = loadBodyHtml(FIXTURE_HTML);
    await assertNoBlockingViolations('primitives-fixture');
  });
});

describe('public web page axe (T20)', () => {
  const HOME_HTML = join(BUILD_ROOT, 'index.html');

  it('built web homepage exists (run `npm run build` first if this fails)', () => {
    expect(existsSync(HOME_HTML)).toBe(true);
  });

  it('no critical or serious axe violations on built web homepage', async () => {
    if (!existsSync(HOME_HTML)) return;
    document.body.innerHTML = loadBodyHtml(HOME_HTML);
    await assertNoBlockingViolations('web/index');
  });
});

describe('docs page axe (T21)', () => {
  const DOCS_HTML = join(BUILD_ROOT, 'docs/getting-started/index.html');

  it('built docs getting-started page exists (run docs-site build first if this fails)', () => {
    expect(existsSync(DOCS_HTML)).toBe(true);
  });

  it('no critical or serious axe violations on built docs getting-started page', async () => {
    if (!existsSync(DOCS_HTML)) return;
    document.body.innerHTML = loadBodyHtml(DOCS_HTML);
    await assertNoBlockingViolations('docs/getting-started');
    // Starlight HTML is large and axe walks all of it in jsdom. The 20s this
    // carried was set against a developer machine; the suite had never run in
    // CI until pages.yml started invoking it, and the first CI run took 23.1s
    // and timed out. 60s is ~2.5x the observed CI figure — headroom for a cold
    // or contended runner, still short enough to fail fast on a real hang.
  }, 60000);
});
