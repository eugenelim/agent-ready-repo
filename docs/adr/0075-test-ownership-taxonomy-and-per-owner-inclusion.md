# ADR-0075: Every test has one owner — engine, catalogue, pack, or tools — and inclusion follows the owner, not the surface alone

- **Status:** Accepted
- **Date:** 2026-08-08
- **Decision-makers:** eugenelim
- **Consulted:** adversarial-reviewer
- **Supersedes:** none
- **Related:** [RFC-0082](../rfc/0082-test-ownership-boundaries-and-inclusion.md)
  (the proposal this records), [ADR-0071](0071-pack-runtime-export-boundary-and-test-placement.md)
  (pack-side companion — see *Relationship to ADR-0071*)

## Decision summary

- **Decision:** Every test carries exactly one owner — the engine, the
  catalogue, a single pack, or a `tools/` script — decided by what it *asserts*;
  each owner has one home; and each distribution surface carries suites by owner
  rather than by a single uniform rule.
- **Because:** placement without ownership is what produced four distribution
  surfaces behaving four different ways, and a rule keyed only on the surface
  cannot say whether a shipped suite can actually run where it lands.
- **Applies to:** every test in this repository, every engine distribution
  surface (wheel, sdist, zipapp, vendored engine copy), and both catalogue
  channels (`catalogue package`, `catalogue init`).
- **Tradeoff accepted:** ownership is decided per test *class*, not per module,
  so the migration is judgement-heavy and cannot be done by pattern.
- **Revisit if:** a fifth distribution channel appears, or an owner's tests must
  ship to a surface this table says they do not.

## Context

ADR-0071 (2026-08-06) made `.apm/` the runtime export boundary for packs and
moved pack tests to `packs/<pack>/tests/`. It scoped itself there, and disposed
of everything else in one sentence: *"This catalogue declines a root `tests/` — a
new top-level directory is RFC-gated here — and keeps catalogue-wide behaviour in
the engine's own suite."*

That left the engine ungoverned. Measured against `agentbundle` 0.29.8 by
building both artifacts from a clean source copy on 2026-08-07:

- the **wheel** shipped 45 test entries of 184, because
  `[tool.setuptools.packages.find]` defaults to `namespaces = true` and discovers
  the tree as a PEP 420 namespace package regardless of any `__init__.py`;
- the **sdist** shipped 8 top-level test files with no `conftest.py` and none of
  the in-package fixtures — present but unrunnable, for two independent reasons;
- `catalogue init --preset self-hosted --tooling vendored` swept the working tree
  with **no exclusions at all**, so its payload varied with whatever happened to
  be on disk, and it also copied a pack's tests through a path ADR-0071's
  projection-adapter reasoning does not cover;
- only the **zipapp** was correct, via an undocumented one-liner.

Underneath all four sat the deeper fault: 82 test modules inside
`packages/agentbundle/` resolve `REPO_ROOT / "packs"` and assert about the
catalogue. Relocating them *within* the engine package — the first draft of
RFC-0082 proposed exactly that — moves the problem and makes the sdist rule
incoherent, because the sdist contains no `packs/`.

Applying the taxonomy to real code then produced the finding that shaped this
decision: three modules that read as ordinary engine tests carry
catalogue-conformance *classes* inside them, each sweeping the live pack tree.
Ownership is therefore not a property of files.

## Decision

**We will assign every test exactly one owner, decided by what it asserts, and
derive both its location and its distribution from that owner.**

| Owner | Asserts | Home |
| --- | --- | --- |
| Engine | engine code behaves correctly — including when a live pack is used as *input* | `packages/<pkg>/tests/` |
| Catalogue, rule-shaped | *any* catalogue's content is well-formed | `tests/conformance/` |
| Catalogue, roster-shaped | *this* repository's specific content | `tests/roster/` |
| Pack | one pack's own content or behaviour | `packs/<pack>/tests/` (ADR-0071) |
| Tools | a `tools/` script's behaviour | `tools/`, co-located |

Three boundaries follow:

1. **`packages/<pkg>/<pkg>/` — the importable package directory — is the
   engine's runtime export boundary.** Nothing testable lives inside it. The
   package itself does not move; only test trees do.
2. **Inclusion is per surface and per owner.** The sdist carries the engine
   suite; the catalogue channels carry the catalogue and pack suites; the wheel,
   zipapp, and vendored engine copy carry none.
3. **A shipped catalogue test must be rule-shaped.** A roster-shaped test pins
   this repository's content and fails on day one in an adopter's catalogue, so
   roster-shaped tests stay home. The `conformance/` ÷ `roster/` directory split
   makes that a mechanical rule rather than a per-file judgement.

**Ownership is assigned per test class, not per module.** Where a module carries
both engine assertions and catalogue-conformance classes, the conformance classes
are extracted rather than the module relocated.

**Scope boundary.** `tools/test*.py` stays co-located: `tools/` crosses no
distribution surface, so the export boundary does not reach it. This is a named
exception *and* a destination — a test of a `tools/` script belongs at `tools/`
wherever it currently sits.

## Decision drivers

- **A shipped suite must be runnable where it lands.** This is the criterion
  that discriminates: it rejects a uniform "ship tests" rule (catalogue
  assertions cannot run from an sdist), a uniform "strip tests" rule (breaks
  redistributors who build from sdists), and roster-shaped conformance tests
  (cannot run in any other catalogue).
- **Structure over convention.** ADR-0071's own reasoning: a rule that "tests do
  not live here" cannot be checked when tests are already there.
- **Cost of being wrong is asymmetric.** Shipping tests that cannot run damages a
  consumer's trust in the artifact; omitting them costs a download.

## Consequences

**Positive:**

- Each of the four engine surfaces and both catalogue channels gets a stated,
  justified rule, replacing four accidental behaviours.
- An adopter's catalogue can verify itself from `catalogue init` onward, in every
  preset — which is what makes the vendored engine copy's wheel-class treatment
  coherent rather than a convenience.
- The rule extends to tests not yet written, because it keys on assertion rather
  than on location or convenience.
- Closes a genuine hole in ADR-0071: vendored mode ships pack tests through a raw
  tree copy that its projection-adapter reasoning never covered.

**Negative:**

- **The migration is judgement-heavy and cannot be automated.** Ownership is
  per class; the read-based signal that finds candidates cannot decide them. An
  early automated pass misfiled 24 modules into a pack named `contracts` that
  were reading the repository-root `contracts/` directory.
- **Four rules are harder to hold than one.** Anyone touching packaging must know
  which surface and which owner they are changing.
- **A new top-level directory.** `tests/` must be added to
  `tools/lint-build.py`'s `RFC_AUTHORISED_DIRS`, and it is refused until then.
- **Five positive allowlists must be widened**, none of them a filter to relax:
  `RFC_AUTHORISED_DIRS`, `_DEFAULT_INCLUDE_DIRS`, `_SOURCE_INCLUDE_DIRS`,
  `_SYNC_PAIRS`, and the `Makefile`'s `SAST_DIRS`.
- **The sdist half is speculative.** No one redistributes this package today; we
  pay configuration cost against a consumer that does not yet exist.
- **Two dangerous interactions ride along.** `build/self_host.py`'s
  destructive-write guard is a `"tests/fixtures/"` substring test that the new
  layout silently kills while its literal-argument test stays green; and
  `build_zipapp.py`'s bare `"tests"` ignore pattern would strip the scaffold's
  test template and abort `catalogue init` on manifest verification.

**Revisit if:** a fifth distribution channel appears, or an owner's tests must
ship to a surface this decision says they do not — most likely if adopters ask to
run engine unit tests against a vendored copy, which would reopen the wheel-class
classification.

## Relationship to ADR-0071

ADR-0071 stays in force: `.apm/` remains the pack-side export boundary, and
`packs/<pack>/tests/` remains where pack tests live. This ADR does **not**
supersede it.

It does reverse and supersede one sentence. ADR-0071 declined a root `tests/`
and parked catalogue-wide behaviour in the engine's suite; this decision reverses
the first clause and replaces the second. ADR-0071's second reason for declining
— that a root tree would give cross-pack and pack-owned tests the same home — is
answered by construction: because ownership is assigned before location, the root
tree holds neither pack tests nor engine tests.

ADRs are immutable in this repository and CI enforces it, so this correction
lives here, naming ADR-0071, and never as an edit to it.

## Confirmation

Two in-repo pure-stdlib instruments, both delivered by the implementing specs:

- an **artifact gate** in `tools/`, run in the release workflow after the build
  step, asserting no test content in the wheel, zipapp, or vendored engine copy
  (spec 1), and a complete, *runnable* engine tree in the sdist (spec 2);
- a **unit test over the vendored payload** in `packages/agentbundle/tests/`,
  because an adopter-side copy is not an artifact any CI job can open.

Portability is confirmed by construction rather than inspection: scaffold a
catalogue with `catalogue init` into a temporary directory and run the
materialised conformance suite against it. A suite that cannot pass there is not
rule-shaped, whatever the directory it sits in claims.

Third-party tooling was tested and rejected on evidence, not preference:
`check-wheel-contents` never fires on a nested test tree, and `pydistcheck`'s
`--expected-directories` form passes while the property is violated, because
setuptools wheels carry no directory entries. Transcripts are in
[`docs/rfc/0082-notes/`](../rfc/0082-notes/).

## References

- [RFC-0082](../rfc/0082-test-ownership-boundaries-and-inclusion.md) — the
  proposal, its options, and the measured evidence.
- [`docs/rfc/0082-notes/first-cut-ownership-mapping.md`](../rfc/0082-notes/first-cut-ownership-mapping.md)
  — provisional per-module classification and the four contested calls.
- [PyPA, Package Formats](https://packaging.python.org/en/latest/discussions/package-formats/)
  — wheels should never include tests and documentation, while sdists commonly do.
- [pytest, Good Integration Practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html)
  — tests outside application code, so they run against the installed package.
