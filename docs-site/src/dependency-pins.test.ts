import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

// `overrides` is the sole remediation for two advisories in a tree that ships to
// readers, and deleting it is a diff no gate reads: the lockfile keeps its
// resolution, so `npm audit` and the SAST leg both stay green, and the manifest
// is in neither SAST_DIRS nor SAST_CONFIG. The vulnerable copies only come back
// at the next install — by which point the removal is someone else's surprise.
// These assertions put the removal and the regression in the same diff.
const read = (name: string) =>
  JSON.parse(readFileSync(fileURLToPath(new URL(`../${name}`, import.meta.url)), 'utf8'));

/** Compare dotted numeric versions; no semver dependency is added for this. */
function compare(a: string, b: string): number {
  const pa = a.split('.').map(Number);
  const pb = b.split('.').map(Number);
  for (let i = 0; i < Math.max(pa.length, pb.length); i += 1) {
    const d = (pa[i] ?? 0) - (pb[i] ?? 0);
    if (d !== 0) return d;
  }
  return 0;
}

// GHSA-r5fr-rjxr-66jc (high) and GHSA-f23m-r3pf-42rh (moderate) are both
// vulnerable at `<=4.17.23`, so anything at or below it is what must not ship.
const LAST_VULNERABLE_LODASH_ES = '4.17.23';

test('no lodash-es at or below the advisory ceiling is resolved', () => {
  const lock = read('package-lock.json');
  const offenders = Object.entries(lock.packages as Record<string, { version?: string }>)
    .filter(([path]) => path.endsWith('node_modules/lodash-es'))
    .filter(([, meta]) => compare(meta.version ?? '0', LAST_VULNERABLE_LODASH_ES) <= 0)
    .map(([path, meta]) => `${path}@${meta.version}`);
  assert.deepEqual(
    offenders,
    [],
    `lodash-es <=${LAST_VULNERABLE_LODASH_ES} is resolved and would ship to ` +
      `readers: ${offenders.join(', ')}. GHSA-r5fr-rjxr-66jc (high) and ` +
      'GHSA-f23m-r3pf-42rh (moderate) cover that range. mermaid 12 reaches it ' +
      "through chevrotain, which pins it exactly, so npm's own fix is a mermaid " +
      'downgrade — the manifest override is what holds this.'
  );
});

test('the manifest still declares the override that holds that ceiling', () => {
  const declared = read('package.json').overrides?.['lodash-es'];
  assert.ok(
    typeof declared === 'string' && compare(declared, LAST_VULNERABLE_LODASH_ES) > 0,
    'docs-site/package.json must override lodash-es above ' +
      `${LAST_VULNERABLE_LODASH_ES}; found ${JSON.stringify(declared)}. Without it ` +
      "the next install re-nests chevrotain's vulnerable copies, and nothing " +
      'fails in the diff that removed the override. Retire this by repinning ' +
      'chevrotain once it admits a fixed lodash-es, not by deleting the assertion.'
  );
});
