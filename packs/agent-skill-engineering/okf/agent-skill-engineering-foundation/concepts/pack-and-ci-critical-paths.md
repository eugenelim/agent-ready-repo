---
id: pack-and-ci-critical-paths
title: Pack and CI critical paths
type: Reference
status: Active
license: Apache-2.0 OR MIT
---
# Pack and CI critical paths

## Scope and routing signals

Use for packs, evaluations, and their execution environments where job ordering,
caches, or repeated setup affects the critical path. It is not a general CI
configuration handbook.

## Decisions and minimum evidence

Job execution order is declared explicitly by naming prerequisite jobs. Cache
reuse is controlled by an explicit key, which may be derived from file contents.
Treat fixed setup and coordination as costs that repeat with each added unit.

## Construction method

Name only the dependencies that must precede a job. Put lockfiles and other
behavior-changing inputs into a cache key. Share setup only when it preserves
isolation and reduces repeated work; otherwise keep the boundary explicit.

## Evidence and evaluation

Measure the longest dependent chain, not only total job time. Exercise a cache
hit and invalidation after an input changes. Compare a split or shared setup
against the work it saves, including coordination time.

## Failure modes

Implicit ordering makes a run fragile. A broad cache key can restore stale
dependencies. Duplicated fixed setup and coordination overhead scales with the
units it is repeated across, so adding units trades against the work they save.

## Security and authority

Cache keys are not authority controls. Do not restore untrusted artifacts into
a privileged step, and keep credentials out of cache paths and job output.

## Related topics

For process-level batching, consult `process-and-filesystem-cost`. For
JavaScript dependency inputs, consult
`typescript-node-and-javascript-test-runners`.

## Provenance and lifecycle

**job dependencies:**
Job execution order is declared explicitly by naming prerequisite jobs.
Last verified: 2026-08-30.
Revalidate when either documented job dependency model changes.
GitHub Actions workflow syntax — https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
Retrieved at: 2026-08-30. Version state: none exposed.
GitLab CI needs documentation — https://docs.gitlab.com/ci/yaml/needs/
Retrieved at: 2026-08-30. Version state: none exposed.

**cache keys:**
Cache reuse is controlled by an explicit key, which may be derived from file contents.
Last verified: 2026-08-30.
Revalidate when either documented cache-key model changes.
GitHub Actions dependency caching — https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching
Retrieved at: 2026-08-30. Version state: none exposed.
GitLab CI caching documentation — https://docs.gitlab.com/ci/caching/
Retrieved at: 2026-08-30. Version state: none exposed.

**execution critical path:**
Duplicated fixed setup and coordination overhead scales with the units it is repeated across, so adding units trades against the work they save.
Last verified: 2026-08-30.
Revalidate when another independent critical-path failure is observed.
