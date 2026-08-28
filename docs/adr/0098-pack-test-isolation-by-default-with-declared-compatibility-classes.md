# ADR-0098: Pack tests are isolated by default, grouped only by a declared compatibility class

- **Status:** Proposed <!-- Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-08-28
- **Decision-makers:** eugenelim
- **Consulted:** adversarial-reviewer, quality-engineer
- **Supersedes:** none
- **Related:** ADR-0071 (the pack is the ownership and test-execution boundary —
  unchanged by this ADR), RFC-0082 (test ownership boundaries),
  `docs/specs/lint-performance-p0/` (whose golden-baseline pin this ADR amends),
  `docs/specs/pack-test-compatibility-classes/`

## Decision summary

- **Decision:** A pack test suite runs in its own pytest process by default. A
  single process may cover several suites **only** when they form an explicitly
  declared, single-pack compatibility class whose test-module identity,
  subject-module identity, and import-set cleanliness are re-derived from source
  by a fail-closed gate on every run.
- **Because:** the previous rule — one process per skill test directory,
  unconditionally — was correct but blunt. It could not distinguish a suite that
  genuinely needs a clean interpreter from one that reads markdown with
  `pathlib`, so it charged an interpreter start to both. The replacement keeps
  the safe default and makes the exception carry its evidence.
- **Applies to:** every pack in this catalogue and every runner that invokes a
  pack test suite.

## Context

`guides/_shared/reference/catalogue-authoring-standards.md` § 4 and the
`Makefile` both stated one process per skill directory as a correctness
requirement, and `tools/lint-pack-test-boundary.py` enforced it by rejecting any
invocation spanning two skill test directories, regardless of whether those
suites could actually collide.

The rationale was real. Two collisions are possible and they fail differently:

- **Test-module basenames.** Two `test_render.py` files in one run make pytest
  refuse the second with `import file mismatch`. Measured on pytest 9.0.3 this
  is loud — collection is interrupted with exit code 2.
- **Subject modules.** Two skills each shipping `scripts/render.py`, imported by
  putting each `scripts/` directory on `sys.path`, resolve `import render` to
  whichever landed first, and `sys.modules` caches that object for every later
  importer. This one is **silent**: the second suite binds the first module and
  can still pass green.

The blunt rule protected against both by never letting them meet. The cost was
45 pack-scoped pytest launches in `make test`, many of them for suites that
import nothing but the standard library.

Two facts, both measured rather than assumed, made a finer rule possible. First,
`agent-skill-engineering`'s skill test directories already carry `__init__.py`
with underscored names, so their duplicate `test_contract.py` files resolve to
distinct dotted module names under pytest's default prepend mode — no flag
needed. Second, most pack suites that touch a skill-local subject already follow
the authoring standard's own recipe: `spec_from_file_location` under a
pack-and-skill-qualified name.

## Decision

Isolation is the default and needs no declaration. Grouping is the exception and
must be declared in `tools/pack_test_compatibility.py` as typed data carrying
its own evidence: owning pack, exact member paths, required import mode, how
duplicate basenames are resolved, and the subject-import disposition.

The gate re-derives safety from source rather than trusting the declaration. A
class fails when a member's import set — its test modules, **every `conftest.py`
from the repository root down to the member's own directory**, and locally
imported helpers — mutates `sys.path`, when a duplicate basename is not covered
by the declared resolution, or when a subject-module name cannot be statically
resolved.

The subject invariant is **one name maps to one path**, not name-uniqueness. Two
members loading the same file under the same name is idempotent and safe; the
hazard is one name resolving to two different files.

Three boundaries are deliberately retained:

- A class never spans packs. ADR-0071's execution boundary stands.
- A floor-bearing suite is never grouped. `tools/pytest_collection_floor.py`
  counts `len(items)` **session-wide** and `--collection-floor-suite` is only a
  display label, so a per-suite floor is enforced by that suite being the sole
  target of its invocation — grouping would silently turn two exact floors into
  one aggregate.
- A grouped command lists its members explicitly. An ancestor-shaped invocation
  is rejected even when the destinations it covers today match a class exactly,
  because a suite added underneath would otherwise join the class silently.

## Decision drivers

- The silent failure mode must stay mechanically detectable as the tree evolves;
  a rule that is safe only for today's filenames is not a rule.
- `--import-mode=importlib` addresses test-module identity and nothing else. It
  must never be presented as a fix for subject collisions, and it stays
  class-scoped rather than becoming a repository default.
- Runtime payloads under `.apm/` are not repackaged for tests. Hyphenated skill
  directories and standalone scripts remain valid; tests adapt to that shape.
- Process reduction is secondary to semantic equivalence. Retained isolation is
  valid engineering, not a failure to optimise.

## Consequences

`make test` drops from 45 to 32 pack-scoped pytest launches across five classes,
with the collected node-ID set unchanged at 1958 and raw count equal to unique
count on both sides — nothing lost, nothing run twice.

The benefit is bounded and now measured. It accrues where interpreter startup
and repeated collection dominate: `desk-research`'s six content suites go from
18.45 s to 2.91 s. It does not accrue where suites are dominated by real work. A
nine-member `core` class was characterised in full and **rejected**: correctness
was clean (523 node IDs identical, forward and reverse green, 522 passed and 1
skipped either way) but peak resident memory rose 222 MiB → 239 MiB against an
8 MiB tolerance, for a wall-time change inside the measurement noise. At roughly
0.5 s per test those suites are dominated by subprocess and filesystem work, so
removing eight interpreter launches buys little. That boundary is the honest
scope of this decision.

`catalogue-curation` and `atlassian` keep isolation because their import sets
mutate `sys.path` — in `atlassian`'s case from `jira/conftest.py`, which pytest
loads even for a single-file invocation. Grouping them is possible only behind a
bounded migration that this decision does not require.

**Amendment to `docs/specs/lint-performance-p0/`.** Replacing
`runners-keep-suites-isolated` changes the boundary lint's observable output in
all 22 captured golden cases, because that check's `ok` line appears in every
passing one. That spec routes such a difference to *Ask first*; approval was
given, so `PINNED_COMMIT` and `PINNED_BLOB_SHA256` are repointed at the commit
carrying the new lint and the baseline is regenerated from that pinned subject.
This is a recorded amendment with its reason, not a rebaseline to make a failing
comparison pass — the distinction that spec's rail draws. The baseline resumes
its anti-regression role from the new pin.
