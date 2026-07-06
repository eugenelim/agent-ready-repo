'use strict';

// test/security.test.js — run with: node test/security.test.js
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { validateInputPath, validateOutputPath, validateInputSize, parseArgs } = require('../scripts/render-proof.js');

const cwd = process.cwd();
// Isolated temp root for all test fixtures — avoids fixed-name collisions in shared os.tmpdir()
const testTmp = fs.mkdtempSync(path.join(os.tmpdir(), 'rp-sec-test-'));
try {

  // AC7a — use a guaranteed-nonexistent traversal path (timestamped) to force the ENOENT branch
  // deterministically on all platforms; '/etc/passwd' exists on macOS (symlinked via /private/etc)
  // and would fire the containment branch instead, whose realpath'd error string (/private/etc/passwd)
  // does not contain the lexical path.resolve(p) (/etc/passwd)
  const traversalTarget = '../../../nonexistent-render-proof-test-' + Date.now();
  const errA = validateInputPath(traversalTarget, cwd);
  assert(errA !== null, 'traversal not rejected');
  assert(errA.includes(path.resolve(traversalTarget)), 'ENOENT error must name the resolved path');

  // AC7b — existing path outside cwd exercises the containment check (not ENOENT)
  const outsideFile = path.join(testTmp, 'outside-probe.md');
  fs.writeFileSync(outsideFile, '');
  const errB = validateInputPath(outsideFile, cwd);
  assert(errB !== null, 'existing path outside cwd not rejected by containment');
  assert(
    errB.includes(fs.realpathSync(path.resolve(outsideFile))),
    'containment error must name the resolved path — AC7a path-naming requirement applies to both ENOENT and containment branches (on Linux CI, /etc/passwd exists so the containment branch fires, not ENOENT)'
  );

  // AC7 — valid relative path accepted; fixture.md exists (full GFM content written in T1)
  const ok = validateInputPath('evals/files/fixture.md', cwd);
  assert(ok === null, 'valid path rejected: ' + ok);

  // AC7c — symlink in cwd pointing outside is rejected
  const symlinkTarget = path.join(testTmp, 'secret.md');
  fs.writeFileSync(symlinkTarget, 'secret');
  const symlinkPath = path.join(cwd, 'test-symlink-input-escape.md');
  try {
    if (fs.existsSync(symlinkPath)) fs.unlinkSync(symlinkPath);
    fs.symlinkSync(symlinkTarget, symlinkPath);
    const errSym = validateInputPath('test-symlink-input-escape.md', cwd);
    assert(errSym !== null, 'input symlink escape not rejected');
  } finally {
    if (fs.existsSync(symlinkPath)) fs.unlinkSync(symlinkPath);
  }

  // AC8 — output outside cwd rejected (allow-root confinement)
  const errC = validateOutputPath('/etc/hosts', cwd);
  assert(errC !== null, '/etc/hosts not rejected');
  const errD = validateOutputPath('../sibling/out.html', cwd);
  assert(errD !== null, '../sibling output not rejected');

  // AC8d — root target unconditionally rejected
  const errRoot = validateOutputPath('/', cwd);
  assert(errRoot !== null, 'root / not rejected');

  // AC8 — valid output within cwd accepted
  const okOut = validateOutputPath('out/proof.html', cwd);
  assert(okOut === null, 'valid output rejected: ' + okOut);

  // AC8c — symlinked output directory inside cwd pointing outside is rejected
  const outDirTarget = path.join(testTmp, 'outside-outdir');
  fs.mkdirSync(outDirTarget);
  const symlinkDirPath = path.join(cwd, 'test-symlink-outdir');
  try {
    if (fs.existsSync(symlinkDirPath)) fs.unlinkSync(symlinkDirPath);
    fs.symlinkSync(outDirTarget, symlinkDirPath);
    const errSymOut = validateOutputPath('test-symlink-outdir/proof.html', cwd);
    assert(errSymOut !== null, 'output symlink-dir escape not rejected');
  } finally {
    if (fs.existsSync(symlinkDirPath)) fs.unlinkSync(symlinkDirPath);
  }

  // AC13 — size cap; exactly 10 MB is at the limit and must be rejected
  const sizeFile = path.join(testTmp, 'rp-size-test.md');
  fs.writeFileSync(sizeFile, Buffer.alloc(10 * 1024 * 1024));
  const errSize = validateInputSize(sizeFile);
  assert(errSize !== null, '10 MB file not rejected');

  // cwd-symlink divergence test (guards the fs.realpathSync(cwd) fix)
  // Must be INSIDE the try so testTmp still exists; uses an actual symlink as cwd
  // so reverting fs.realpathSync(cwd) to bare cwd would cause the test to fail on all platforms
  const realCwdDir = path.join(testTmp, 'real-cwd');
  fs.mkdirSync(realCwdDir);
  const symlinkCwd = path.join(testTmp, 'symlink-cwd');
  fs.symlinkSync(realCwdDir, symlinkCwd); // symlink-cwd → real-cwd
  const innerFile = path.join(realCwdDir, 'inner.md');
  fs.writeFileSync(innerFile, '');
  // validateInputPath must accept innerFile when cwd = symlinkCwd (symlink to realCwdDir)
  // Without fs.realpathSync(cwd), symlinkCwd ≠ realpath(innerFile)'s parent → false rejection
  const errCwdSym = validateInputPath(innerFile, symlinkCwd);
  assert(
    errCwdSym === null,
    'file inside symlinked cwd should be accepted when both sides are realpath-resolved: ' + errCwdSym
  );

} finally {
  fs.rmSync(testTmp, { recursive: true, force: true });
}

// parseArgs — defaults
const args = parseArgs(['fixture.md']);
assert(args.input === 'fixture.md', 'input wrong');
assert(args.output === 'fixture.html', 'output default wrong');

// parseArgs — explicit output
const args2 = parseArgs(['fixture.md', '--output', 'out/proof.html']);
assert(args2.output === 'out/proof.html', 'explicit output wrong');

console.log('All security tests pass');
