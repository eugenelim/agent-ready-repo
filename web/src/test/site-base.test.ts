import { readFileSync } from 'node:fs';

import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest';

async function previewPort(value: string | undefined): Promise<number> {
  vi.resetModules();
  if (value === undefined) {
    vi.stubEnv('ARR_PREVIEW_PORT', undefined);
  } else {
    vi.stubEnv('ARR_PREVIEW_PORT', value);
  }
  return (await import('./e2e/site-base')).PREVIEW_PORT;
}

// Warm the module graph once, OUTSIDE any timed test body.
//
// The first `await import('./e2e/site-base')` pays the whole cold transform, and
// under machine contention that has exceeded vitest's 5000 ms default inside the
// first case -- a flake with nothing to do with what the case asserts. Measured
// here: first case 1536 ms and 2247 ms across two runs, later cases 7-52 ms; an
// instrumented probe put 1817.9 ms in the dynamic import and 0.1 ms in
// `vi.resetModules()`, so the cost is the transform, not the reset. With this
// hook the first case drops to 9 ms and every case runs 7-13 ms.
//
// The hook carries an explicit budget because vitest's default HOOK timeout is
// 10000 ms and a loaded full-suite run measured this import at ~114 s -- warming
// without a budget just relocates the same flake from the test to the hook. The
// asymmetry is deliberate: widen the budget for the transform, whose cost really
// does vary with load, and leave every assertion on the tight default, because
// widening an assertion's budget is what hides the defect.
//
// A known-valid port is stubbed before importing: `site-base.ts` throws at module
// load on an invalid `ARR_PREVIEW_PORT`, so an ambient value would turn eight
// readable per-case failures into one unreadable hook abort.
beforeAll(async () => {
  vi.stubEnv('ARR_PREVIEW_PORT', '4321');
  try {
    await import('./e2e/site-base');
  } finally {
    vi.unstubAllEnvs();
    vi.resetModules();
  }
}, 120_000);

afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
});

describe('warm-up contract', () => {
  // AC14 is checked MECHANICALLY, not by timing. A flake cannot be asserted
  // against a clock: delete the hook and every case below still passes, just
  // slowly enough to fail on a loaded runner. So the contract is structural --
  // the hook exists, it carries an explicit budget, and no case widens its own.
  const source = readFileSync(new URL(import.meta.url), 'utf8');

  it('warms the module in a hook with an explicit budget', () => {
    expect(source).toMatch(/beforeAll\(async \(\) => \{/);
    expect(source).toMatch(/await import\('\.\/e2e\/site-base'\)/);
    expect(source).toMatch(/\}, *[0-9][0-9_]*\);/);
  });

  it('leaves every case on the default per-test budget', () => {
    // Any INDENTED `}, <number>);` is a case widening its own budget. The hook's
    // own budget sits at column 0, so requiring leading whitespace distinguishes
    // the two. An earlier version of this pattern demanded four spaces and would
    // have missed a real widening, since the cases close at two.
    const widened = source.match(/^\s+\},\s*[0-9][0-9_]*\);\s*$/gm) ?? [];
    expect(widened).toEqual([]);
  });
});

describe('PREVIEW_PORT', () => {
  it('defaults to 4321 when ARR_PREVIEW_PORT is unset', async () => {
    expect(await previewPort(undefined)).toBe(4321);
  });

  it('defaults to 4321 when ARR_PREVIEW_PORT is empty', async () => {
    expect(await previewPort('')).toBe(4321);
  });

  it('honours a valid ARR_PREVIEW_PORT override', async () => {
    expect(await previewPort('49152')).toBe(49152);
  });

  it.each(['not-a-number', '1.5', '0', '-1', '65536'])(
    'rejects invalid ARR_PREVIEW_PORT %j',
    async (value) => {
      await expect(previewPort(value)).rejects.toThrow(
        `ARR_PREVIEW_PORT must be an integer from 1 to 65535; received ${JSON.stringify(value)}`,
      );
    },
  );
});
