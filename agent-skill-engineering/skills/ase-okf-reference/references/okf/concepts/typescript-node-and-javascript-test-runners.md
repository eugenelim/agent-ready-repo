---
id: typescript-node-and-javascript-test-runners
title: TypeScript, Node, and JavaScript test runners
type: Reference
status: Active
license: Apache-2.0 OR MIT
---
# TypeScript, Node, and JavaScript test runners

## Scope and routing signals

Use for TypeScript or JavaScript skill scripts, evaluations, and browser tests
that depend on Node package resolution or runner concurrency. This guidance is
limited to the documented ecosystems and versions recorded below.

## Decisions and minimum evidence

Make package and module contracts explicit, and use a clean install that honors
the lockfile. Each runner provides runner-specific controls for limiting test
parallelism. Treat child-process exits, signals, streams, and working
directories as part of the contract.

## Construction method

Pin the package manager input, choose the module form deliberately, and pass
arguments without shell interpolation. Configure runner workers in the runner,
not through an assumed shared default. Browser workers consume real browser
and setup resources; select their count from the workload rather than CPU count
alone. Include dependency and tool versions in cache keys, and scan both
JavaScript and TypeScript dependency and source surfaces.

## Evidence and evaluation

Exercise a clean lockfile-respecting install, module resolution, child-process
success and failure, and the selected worker limit. Check cache invalidation
after a dependency input changes, and run the security scanner on the package
and source inputs it is meant to cover.

## Failure modes

An unlocked install makes an evaluation non-repeatable. A child process can
appear successful while its output or signal handling is lost. Excess browser
workers can add contention, and a cache key that omits dependency inputs can
reuse incompatible artifacts.

## Security and authority

Do not pass untrusted strings through a shell. Treat package lifecycle scripts,
downloaded browser binaries, and scan suppressions as explicit authority
boundaries. Review scan scope before accepting a clean result.

## Related topics

For process cost, consult `process-and-filesystem-cost`. For pack-level cache
and dependency ordering, consult `pack-and-ci-critical-paths`.

## Provenance and lifecycle

**TypeScript and Node runner contract:**
Each runner provides runner-specific controls for limiting test parallelism.
Last verified: 2026-08-30.
Revalidate when Node.js or Playwright changes test-parallelism controls.
Ecosystem: Node.js and Playwright.
Version range: Node.js >= 26.8.1, upper bound open; Playwright >= 1.62, upper bound open.
Node.js test runner documentation — https://nodejs.org/api/test.html
Retrieved at: 2026-08-30. Version: 26.8.1.
Playwright parallelism documentation — https://playwright.dev/docs/test-parallel
Retrieved at: 2026-08-30. Version: 1.62.
Node.js packages documentation — https://nodejs.org/api/packages.html
Retrieved at: 2026-08-30. Version: 26.8.1.
Node.js child process documentation — https://nodejs.org/api/child_process.html
Retrieved at: 2026-08-30. Version: 26.8.1.
npm ci documentation — https://docs.npmjs.com/cli/v11/commands/npm-ci/
Retrieved at: 2026-08-30. Version state: none exposed.
