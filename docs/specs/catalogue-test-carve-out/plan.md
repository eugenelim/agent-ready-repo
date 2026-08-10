# Plan: catalogue test carve-out

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The expensive part of this work is deciding, not moving. RFC-0082 records two
method-sensitive candidate counts; neither search is authoritative, and both
miss composed or marker-walking paths. The automated signal finds candidates
but cannot decide them, because reading `packs/` and testing `packs/` are
different things. The plan therefore front-loads classification as its own
deliverable: a recorded disposition for every test class in the two-search union
and the supplemental discovery inventory, plus every loose top-level
`packages/agentbundle/tests/test*.py` module whether or not a search selects it.
Engine-owned classes that do not move remain in the record.

The shape of the work is not what RFC-0082 first assumed, and the plan follows
the corrected picture. No module in `tests/build_pipeline/` (formerly
`agentbundle/build/tests/`) is a standalone rule-shaped conformance test. The
rule-shaped material exists, but embedded as classes inside three engine
modules. So the shipped conformance suite is assembled by **extraction**, not by
moving files, and that is T3a rather than a footnote.

Five positive allowlists gate the destination. None is a filter to relax. The
top-level audit is repaired and proven against an `origin/main`-only checkout
before `RFC_AUTHORISED_DIRS` admits the tree. The two archive allowlists ship
only `tests/conformance/`; `_SYNC_PAIRS` registers every scaffolded conformance
file; and `SAST_DIRS` admits the whole root tree, with no new test exemption.

Riskiest part: the portability claim. A conformance suite that passes here proves
nothing about an adopter's catalogue, because here the roster it might
accidentally depend on is satisfied. The only honest check is to scaffold a
catalogue and run the suite against it, so that is written as a task and not as a
review step.

## Constraints

- **ADR-0075** — the five test categories across four owning domains, their
  homes, class-level granularity, and per-owner inclusion.
- **RFC-0082** — the proposal and its measured evidence; D7 is the portability
  rule this plan implements.
- **ADR-0071** — `packs/<pack>/tests/` is where pack tests live; this plan adds
  to that tree and changes nothing about it.
- **`engine-export-boundary` spec must land first** — it makes the export
  boundary real, so relocations here cannot silently re-enter an artifact.
- **`Engine-Change-RFC:` trailer** on commits touching non-carved-out
  `packages/agentbundle/` paths; `/tests/` and `build/recipes/` are carved out
  (`tools/lint-catalogue-curation-guard.py:100-115`).
- **New `tools/` scripts are pure-stdlib Python.**
- **Release coupling** — every affected pack gets matching `pack.toml` and
  plugin-manifest version bumps plus marketplace/changelog regeneration; the
  scaffold and engine packaging changes get one coordinated `agentbundle`
  version bump and package changelog entry.
- **Shipped-content citation rule** — relocated pack tests contain no internal
  ADR, RFC, spec, or AC markers.

## Construction tests

**Integration tests:**

- The ownership-record completeness check accounts for every loose top-level
  `packages/agentbundle/tests/test*.py` module, every module in the union of both
  documented searches, the supplemental marker-walking and composed-path
  inventory across all four roots, and every test class within them.
- An `origin/main`-only scratch checkout proves the top-level-directory audit
  runs before the root tree is admitted.
- Every suite green from its new home: engine, `tests/conformance/`,
  `tests/roster/`, and each pack suite that gained modules.
- Each affected pack suite runs with its declared test dependencies preflighted;
  a planted absent dependency, including Linear's `httpx`, fails instead of
  turning the relocated assertion into a skip.
- The engine suite runs without any checkout-local catalogue tree, and
  `tests/live-catalogue/` is empty or absent at completion.
- `make ci` green, including the new root tree's runner.

**Manual verification:**

- `agentbundle catalogue init` into a temp directory, then run the materialised
  conformance suite against the scaffolded catalogue — for the default preset and
  for `--preset self-hosted` in both `--tooling` modes. This is the portability
  proof and cannot be replaced by inspection.
- Build a `catalogue package` archive in both flavours; confirm
  `tests/conformance/` is present and `tests/roster/` is absent.

## Design (LLD)

`Shape: mixed`. Four sub-sections earn their place.

### Component decomposition

Traces to AC2, AC4, AC5. The root tree splits by *shippability*, not by test
kind:

```
tests/
├── conformance/   rule-shaped; ships to every catalogue
└── roster/        pins this repository's content; never ships
```

That split is the mechanism behind D7. Shipping becomes a directory rule rather
than a per-file judgement someone has to remember, and it is reviewable in a diff.

### Interfaces & contracts

Traces to AC6, AC7, AC8. There is no new public interface contract. Three
existing shipping channels need distinct integration work:

- `catalogue package` — widen `_DEFAULT_INCLUDE_DIRS` and `_SOURCE_INCLUDE_DIRS`.
- `catalogue init --preset self-hosted` — copies from a source catalogue.
- `catalogue init` (default preset) — materialises the bundled scaffold, so the
  scaffold itself gains the portable `tests/conformance/` suite.

The scaffold template is inert content that lives *inside* the engine's export
boundary by design. The artifact gate must exempt
`_data/catalogue-scaffold/**`, and `build_zipapp.py`'s ignore pattern must
already have been narrowed by the engine spec — otherwise the zipapp strips the
template and `catalogue init` aborts on manifest verification.

### Data & schema

Traces to AC8 and AC13. The ownership record is the migration ledger: module,
class or module-level test group, owner, basis, destination, and shipping rule.
The scaffold manifest is hash-verified at init time, so each conformance file
must have its own `_SYNC_PAIRS` entry. An unregistered file is never
materialised and surfaces only as a non-blocking INFO.

### Behavior & rules

Traces to AC5, AC7b, AC9, and AC12. Inclusion is path-shaped and fail-closed:

| Surface | Included test owner | Mechanical boundary |
| --- | --- | --- |
| Engine sdist | self-contained engine | `graft tests` plus empty migration rail |
| Catalogue archives | catalogue + pack | root allowlist plus existing pack walk |
| Default catalogue init | rule-shaped catalogue | scaffold manifest entries |
| Self-hosted init | catalogue + selected packs | root copy plus existing pack copy |
| SAST | conformance + roster | root `tests` in `SAST_DIRS`; no new exemption |

## Tasks

### T1a — Classify `tests/build_pipeline/` at class granularity

- **Implements:** AC13
- **Verification mode:** goal-based, human-reviewed
- **Depends on:** none

**Tests:**

- Re-running both documented searches against
  `packages/agentbundle/tests/build_pipeline/` yields the recorded candidate
  slice.
- Every test class and module-level test in that slice has a proposed owner,
  basis, destination, and shipping rule.

**Approach:**

Start from `docs/rfc/0082-notes/first-cut-ownership-mapping.md`; re-read every
candidate module and do not inherit its verdicts. Create the build-pipeline
section of `notes/ownership-record.md`. Leave contested rows visibly pending for
T1d rather than choosing silently.

**Done when:** the build-pipeline section accounts for every class and
module-level test in its re-derived candidate slice.

### T1b — Classify `tests/unit/` at class granularity

- **Implements:** AC13
- **Verification mode:** goal-based, human-reviewed
- **Depends on:** T1a

**Tests:**

- Re-running both documented searches against `packages/agentbundle/tests/unit/`
  yields the recorded candidate slice.
- Every test class and module-level test in that slice has a proposed owner,
  basis, destination, and shipping rule.

**Approach:**

Read the unit candidate modules and append their class-level dispositions to the
canonical ownership record. Treat engine code invoked with a live pack as input
as engine-owned; treat assertions over catalogue content as catalogue-owned.

**Done when:** the unit section accounts for every class and module-level test in
its re-derived candidate slice.

### T1c — Classify `tests/integration/` at class granularity

- **Implements:** AC13
- **Verification mode:** goal-based, human-reviewed
- **Depends on:** T1b

**Tests:**

- Re-running both documented searches against
  `packages/agentbundle/tests/integration/` yields the recorded candidate slice.
- Every test class and module-level test in that slice has a proposed owner,
  basis, destination, and shipping rule.

**Approach:**

Read the integration candidate modules and append their class-level
dispositions. Keep invocation and assertion distinct: an integration test can
use a whole live catalogue and still be engine-owned if it asserts only engine
behavior.

**Done when:** the integration section accounts for every class and module-level
test in its re-derived candidate slice.

### T1d — Classify the loose root, complete the inventory, and ratify the record

- **Implements:** AC13
- **Verification mode:** goal-based, human-reviewed
- **Depends on:** T1c

**Tests:**

- Every loose `packages/agentbundle/tests/test*.py` module is enumerated, and
  every class or module-level test in it has a disposition even when neither
  RFC search selected the module.
- A third recorded inventory covers marker-walking and composed-path modules
  missed by both primary searches across the loose root and three nested roots.
- The completeness probe reports no loose top-level module or module from any
  nested-root discovery input missing and no class or module-level test without
  a disposition.
- Every contested call has an explicit human disposition.

**Approach:**

Classify the loose top-level test modules first, including modules such as
`test_linear_primitive.py` whose pack dependency is visible only by reading the
assertions. Then inspect all four roots for repository-marker walks and paths
composed from separate literals. Fold discoveries into the appropriate
ownership-record section. Resolve `contracts/adapter.toml` once for every
affected class, then resolve the module-specific contested calls. Granularity
itself is already closed by ADR-0075.

**Done when:** the canonical record covers the entire loose root and the full
three-input nested-root candidate set at class granularity, and all contested
dispositions have human sign-off.

### T2 — Make the top-level-directory audit run in CI

- **Implements:** AC14
- **Verification mode:** TDD
- **Depends on:** none

**Tests:**

- Add a failing `tools/test-lint-build.sh` case whose scratch repository has
  `origin/main` but no local `main`; prove an unauthorised directory still exits
  1 instead of printing the skip warning.
- Retain the existing local-`main`, authorised-directory, and normalised-exit
  cases.

**Stub handoff:** during `work-loop` PLAN, materialise the AC14 scratch-repo case
as a compilable red stub with `# STUB: AC14` and record `stub: true` before
EXECUTE. `new-spec` does not commit test stubs at spec-authoring time.

**Approach:**

In `tools/lint-build.py`, resolve the baseline from local `main` first and
`origin/main` second. Preserve the existing warning/skip behavior only when
neither ref can produce a merge base. Land this repair before adding `tests` to
`RFC_AUTHORISED_DIRS` or creating the root tree.

**Done when:** the new `origin/main`-only negative case fails before the code
change and passes after it without weakening the existing cases.

### T3a — Establish the catalogue-owned root trees

- **Implements:** AC2 and AC4
- **Verification mode:** goal-based, integration surface
- **Depends on:** T1d, T2

**Tests:**

- The three known mixed modules pass on both sides of extraction; every
  additional mixed catalogue/engine module in the record receives the same
  two-sided check.
- Rule-shaped tests pass under `tests/conformance/`; roster-shaped tests pass
  under `tests/roster/`.

**Approach:**

Add `"tests",  # RFC-0082` to the now-working `RFC_AUTHORISED_DIRS`, then create
both root subtrees with real test content. Extract catalogue classes from mixed
modules, move whole catalogue-owned modules with `git mv`, and carry only the
minimum shared setup each extracted class needs. Update path anchors per
destination. Do not perform a non-trivial roster-to-rule rewrite without the
spec's required sign-off.

**Done when:** every catalogue-owned row in the ownership record is in the
correct root subtree and its source/destination tests pass.

### T3b — Relocate tools- and pack-owned tests with pack release records

- **Implements:** AC3 and the pack half of AC16
- **Verification mode:** goal-based, integration surface
- **Depends on:** T1d, T3a

**Tests:**

- The three `test_lint_agents_md_{diataxis,legacy,risk}_block.py` modules pass
  from `tools/`.
- Every pack-owned module passes from its ADR-0071 home, and each affected
  pack's two version declarations increment together above the merge-base value.
- Each affected pack runner installs or preflights the dependencies declared by
  the relocated tests. Removing Linear's `httpx` makes the gate fail rather than
  report a successful skip.

**Approach:**

Move whole modules with `git mv`; extract a class when its source module is
mixed. Follow each pack's existing `tests/{skills,hooks,pack}/` layout. Strip
internal governance markers from moved pack content. Reuse each pack's declared
test-dependency installation path, add a preflight where a relocated assertion
would otherwise be guarded by `pytest.importorskip`, and reject a
missing-dependency skip. Bump each affected `pack.toml` and plugin manifest,
regenerate the marketplace/self-host projection, and add one product changelog
entry per bumped pack.

**Done when:** all tools/pack dispositions are in their owner homes and the pack
release records agree with the merge base and regenerated marketplace.

### T3c — Fixture-back engine tests in `tests/build_pipeline/`

- **Implements:** AC1 and AC9b
- **Verification mode:** goal-based, integration surface
- **Depends on:** T1d, T3a

**Tests:**

- Every engine-owned build-pipeline test passes using only engine source and
  fixtures inside the package source tree.
- Running the slice from a copy with no repository-root catalogue content stays
  green.

**Approach:**

Replace live catalogue inputs with the smallest representative fixtures needed
to test engine behavior. Do not copy roster assertions into fixtures; any such
assertion is a classification error and returns to T1d/T3a.

**Done when:** no engine-owned build-pipeline test requires the checkout's live
catalogue trees.

### T3d — Fixture-back engine tests in `tests/unit/`

- **Implements:** AC1 and AC9b
- **Verification mode:** goal-based
- **Depends on:** T1d, T3a

**Tests:**

- Every engine-owned unit test passes against local fixtures with no live
  catalogue root available.
- Tests remain unit-shaped: no subprocess or full-catalogue setup is introduced.

**Approach:**

Replace borrowed live inputs with focused fixtures while preserving the unit
boundary. A test that needs full-stack behavior moves to integration only after
sign-off; do not hide that change inside fixture work.

**Done when:** no engine-owned unit test requires the checkout's live catalogue
trees.

### T3e — Fixture-back engine tests in `tests/integration/` and close the rail

- **Implements:** AC1 and AC9b
- **Verification mode:** goal-based, integration surface
- **Depends on:** T1d, T3a, T3b, T3c, T3d

**Tests:**

- Every engine-owned integration test passes from a source copy containing no
  repository-root `packs/`, `profiles/`, `contracts/`, or `guides/` tree.
- `packages/agentbundle/tests/live-catalogue/` is empty or absent.

**Approach:**

Replace remaining borrowed live inputs with complete but minimal catalogue
fixtures. Use `tests/live-catalogue/` only as a visible intermediate rail; remove
its contents before this task completes.

**Done when:** the entire engine suite is fixture-backed and the migration rail
contains no accepted debt.

### T3f — Gate every destination locally, in CI, and in SAST

- **Implements:** AC5, AC11, AC11b, AC12, and AC15
- **Verification mode:** goal-based
- **Depends on:** T3a, T3b, T3c, T3d, T3e

**Tests:**

- `make test` and the relevant `build-check.yml` steps collect every new
  destination; `lint-ci-parity.py` accepts every new or renamed step.
- Every affected pack step preflights its relocated tests' declared dependencies
  and rejects an unexpected missing-dependency skip; a construction case removes
  Linear's `httpx` and must fail.
- A planted shipped-pack name makes the conformance-portability gate fail, while
  generic rule-shaped text passes. The gate derives the current pack names from
  the catalogue rather than maintaining a second roster.
- Bandit and Semgrep scan both root catalogue subtrees with no new exemption.
- A goal-based documentation check confirms `packages/AGENTS.md` names all five
  categories, their homes and surface rules, and the three retained engine test
  roots.

**Approach:**

Add `tests` to `Makefile:SAST_DIRS` without changing Bandit or Semgrep
exclusions. Add a pure-stdlib conformance-portability check under `tools/` plus
its negative construction test. Add explicit Makefile and CI runners for that
check, the root suite, the three tools modules, and every affected pack
destination; add matching `STEP_DISPOSITION` entries. Preserve the
one-pytest-process-per-pack-skill rule and check duplicate basenames before
consolidating modules. Update `packages/AGENTS.md` with the full ownership and
surface-inclusion table.

**Done when:** every final home is collected by local and CI gates, root tests
are scanned, and a hardcoded shipped-pack name cannot enter conformance.

### T4 — Include only conformance tests in catalogue archives

- **Implements:** AC7 and AC7b
- **Verification mode:** goal-based
- **Depends on:** T3a, T3f

**Tests:**

- Default and source-flavour archive tests assert every
  `tests/conformance/` file is present.
- Both flavours retain every affected `packs/<pack>/tests/` tree after the
  relocation; the root allowlist change does not narrow the existing pack walk.
- The same tests assert `tests/roster/` is absent, including a planted roster
  sentinel that would be caught by an accidentally broad `tests` allowlist.

**Approach:**

In `catalogue_tooling/package.py`, add `("tests", "conformance")` to
`_DEFAULT_INCLUDE_DIRS` and `"tests/conformance"` to
`_SOURCE_INCLUDE_DIRS`. Both collections walk their entries wholesale; never add
the root `tests` directory. Extend
`tests/unit/test_catalogue_tooling_{package,source_package}.py` at the archive
boundary rather than asserting constant shapes. Keep the existing `packs/`
allowlist entry unchanged; only the new root entry is scoped to conformance.

**Done when:** both archive flavours contain the complete conformance tree and
every affected pack suite, while the planted roster sentinel is absent.

### T5 — Carry conformance tests through both catalogue-init implementations

- **Implements:** AC6, AC8, and the scaffold half of AC16
- **Verification mode:** goal-based, end-to-end
- **Depends on:** T3a, T3b, T3f

**Tests:**

- Scaffold a default catalogue and self-hosted catalogues in both `external` and
  `vendored` tooling modes; assert conformance is present, roster is absent, and
  the materialised suite passes in each target.
- A scaffold projection test proves every root conformance file is registered,
  hash-manifested, and byte-identical in `_data/catalogue-scaffold/`.
- Existing assertions prove selected pack tests still survive self-hosted init.

**Approach:**

For self-hosted init, add an explicit collection of the source catalogue's
`tests/conformance/` to the in-memory file plan before the tooling-mode branch in
`catalogue_tooling/initialise_self_hosted.py`; never put this logic inside the
vendored engine copy.

For default init, add one `_SYNC_PAIRS` entry per conformance file in
`tools/catalogue/sync_authoring_scaffold.py`, run its write mode, and verify the
generated manifest. The `_data/catalogue-scaffold/**` export-boundary exemption
already exists and must stay narrow. Cover the behavior in
`tests/integration/test_catalogue_init.py`,
`tests/unit/test_catalogue_tooling_{init,self_hosted_init}.py`, and
`tests/integration/test_scaffold_projection.py`.

**Done when:** all three materialisation paths produce the complete conformance
suite, omit roster content, and execute green in their target catalogues.

### T6 — Restore the complete engine suite to the sdist

- **Implements:** AC9, AC9b, and AC10
- **Verification mode:** TDD
- **Depends on:** T3a, T3c, T3d, T3e

**Tests:**

- Start with a failing artifact test: build and extract an sdist, then collect
  and run its engine suite from the extracted copy.
- The green case proves modules and non-Python fixtures are present, the full
  suite runs without checkout-local catalogue content, and
  `tests/live-catalogue/` is absent.
- Negative fixtures prove file counts and collect-only checks cannot satisfy the
  gate when execution still depends on a missing live catalogue.
- Malicious archive fixtures cover absolute and traversing names, symlinks,
  hard links, and special-file members; every case is refused before writing
  outside the temporary extraction root.
- Cross-platform name fixtures cover POSIX absolute paths, Windows
  drive-absolute and drive-relative forms, UNC paths, and traversal with both
  slash directions. Checks behave identically on Linux and Windows runners.
- Boundary fixtures cover 10,001 members, a member over 32 MiB, total
  uncompressed content over 256 MiB, and aggregate expansion over 100:1. Each is
  refused before extraction, and temporary roots are absent after every success
  or failure path. Construct oversized cases from tar metadata/sparse streams so
  the tests do not allocate the prohibited payload sizes.
- The 10,001-member fixture is consumed through a streaming header iterator and
  fails as soon as the cap is crossed. A construction check rejects use of
  `TarFile.getmembers()` or any equivalent path that first retains all headers.
- A missing pytest executable, a collection error, a test failure, or a suite
  timeout exits non-zero; none degrades to an absence-only pass.
- The extracted run installs the same declared test dependencies as the normal
  package gate. A planted missing retained-engine dependency fails its preflight
  import before pytest, and a synthetic unrecognised skip reason containing
  `not installed`, `No module named`, or `importorskip` also fails the gate.
- A planted engine test that skips because `packs/`, `profiles/`, `contracts/`,
  `guides/`, or `dist/apm` is absent — including a "not present in this
  checkout" reason — fails the gate rather than certifying self-containment.
- Explicit expected platform or feature skips remain accepted, proving that the
  dependency-integrity check is fail-closed without turning every skip into an
  error.

**Stub handoff:** during `work-loop` PLAN, materialise the AC9/AC10 artifact
fixtures as compilable red stubs with `# STUB: AC9` / `# STUB: AC10` and record
`stub: true` before EXECUTE. `new-spec` does not commit test stubs at
spec-authoring time.

**Approach:**

Add `packages/agentbundle/MANIFEST.in` with an explicit `graft tests` and a
defensive `prune tests/live-catalogue`. Extend
`tools/check-artifact-contents.py`, its tests, and
`.github/workflows/release-agentbundle.yml` so the presence half opens the sdist,
validates every member, extracts into a fresh temporary root, then collects and
runs the suite with an argv-form subprocess. Any validation, extraction,
collection, or execution error exits non-zero; no fallback certifies presence.
Validate POSIX and Windows member-name forms independent of the host OS. Enforce
the member-count, per-member, total-size, and expansion-ratio constants while
streaming tar headers and before writing. Never call `TarFile.getmembers()` or
otherwise materialise the complete header set before the count cap fires. Use
`TemporaryDirectory` cleanup on all paths. Install pytest in the
build-and-smoke job before the gate; cap collection at 120 seconds and execution
at 900 seconds; raise the job timeout from 5 to at least 20 minutes. Measure the
cold extracted-suite run and tighten limits if evidence supports it; weakening
AC10's bounds requires a spec update.

Guard three packaging traps: `MANIFEST.in` command order, stale
`agentbundle.egg-info/SOURCES.txt`, and accidental `include_package_data = True`,
which would promote the graft into the wheel. Reuse one declared package-test
dependency installation path for the normal package gate and the extracted
sdist gate. Before pytest, import every optional dependency retained engine
tests would otherwise guard with `pytest.importorskip`; then inspect reported
skip reasons against the package suite's explicit expected-skip policy and fail
on any unrecognised dependency-absence reason. The same check rejects skip
reasons tied to absent checkout-local catalogue or projection content, including
`packs/`, `profiles/`, `contracts/`, `guides/`, `dist/apm`, and "not present in
this checkout"; those are evidence of an incomplete carve-out, never expected
archive behavior.

**Done when:** a freshly built sdist passes the dependency preflight,
safe-extraction, collection, skip-integrity, and execution gates from outside
the checkout, while every malicious archive fixture is rejected without an
out-of-root write.

### T7 — Verify the release-coupled change as one system

- **Implements:** AC6–AC12 and AC16
- **Verification mode:** goal-based
- **Depends on:** T4, T5, T6

**Tests:**

- Run the complete surface matrix: both catalogue archive flavours; default
  catalogue init; self-hosted init with external and vendored tooling; wheel,
  zipapp, vendored-engine, and sdist artifact gates.
- For both catalogue archive flavours, assert conformance and every affected
  pack-owned suite are present while roster is absent.
- Run the focused suites, `make lint-ruff`, `make lint-mypy`, and `make ci`.
- Verify the `agentbundle` package/version constants agree and every affected
  pack's manifest versions agree after regeneration. Compare each version to the
  merge base and fail unless it incremented; verify the matching package/product
  changelog entries exist.
- Run `tools/lint-catalogue-curation-guard.py --base <merge-base>` after the
  commits exist, so missing `Engine-Change-RFC: RFC-0082` trailers fail rather
  than surviving as a prose reminder.

**Approach:**

T4–T7 form one release-coupled PR and do not land independently. Apply one
coordinated `agentbundle` version increment above the merge-base version for the
archive, scaffold, init, and sdist behavior; update the package changelog with
both the restored sdist suite and shipped catalogue conformance suite. Confirm
the required `Engine-Change-RFC: RFC-0082` commit trailer with the repository
guard before closeout. Record any genuinely unrelated cleanup as follow-up
rather than widening this spec.

**Done when:** the full surface matrix and repository gates pass from the
coordinated versioned tree, with all version and changelog records in sync.

## Rollout

- **Delivery:** one coordinated repository change and one `agentbundle` release;
  no feature flag. Before publication, rollback is a normal revert. After the
  sdist and scaffold are published, correction requires a follow-up release.
- **Infrastructure:** none.
- **External systems:** the existing package and catalogue publication paths;
  no new service or credential.
- **Sequencing:** the shipped `engine-export-boundary` spec is the prerequisite.
  Within this plan, T2 lands before T3a creates root `tests/`; T1a–T1d and T2
  may progress independently until T3a; T4–T6 wait on only the relocation,
  runner, or self-containment slices they consume; T7 closes the release after
  all three shipping surfaces are green.

## Risks

- **The classification gets done with a grep because it is large.** This is the
  failure the whole spec exists to prevent. Mitigated by T1a–T1d producing a
  recorded owner per class, plus a mechanical candidate-completeness check, as
  their deliverable.
- **Extraction separates a class from shared setup and quietly weakens it.**
  Mitigated by requiring both halves green, and by treating a class that cannot
  be cleanly extracted as a contested call rather than forcing it.
- **The shipped suite is roster-shaped in practice and every adopter starts
  red.** Mitigated by T5's scaffold-and-run check, which cannot be satisfied by
  inspection.
- **Relocation re-enters an artifact** if this spec lands before the engine
  boundary. Mitigated by the ordering constraint.
- **SAST findings tempt a broad test exemption.** The root tree does not match
  the existing nested-test Bandit glob. AC12 makes that deliberate: fix or
  surface findings instead of hiding the whole new tree.
- **The restored sdist gate becomes green by collecting but not executing.** A
  borrowed live-catalogue dependency can collect successfully and fail only at
  runtime. T6 requires both phases from an extracted archive.

## Changelog

- **2026-08-08** — Initial plan, from RFC-0082 as Accepted and ADR-0075.
  Extraction (now T3a) is a first-class task rather than a footnote: applying the
  taxonomy to real code showed the rule-shaped material lives inside engine
  modules as classes, so the shipped suite is assembled by extraction rather
  than relocation. Roster rewriting is deliberately excluded and named as a
  follow-up.
- **2026-08-09** — Completed the plan from the workspace-ready scope. Expanded
  classification to every class in the re-derived candidate union; made the
  `origin/main` audit repair a prerequisite to the root tree; fixed all five
  allowlist dispositions; made an empty `live-catalogue/` the exit condition;
  split classification by source root and implementation by ownership/fixture
  slice; and separated archive, init, and sdist construction tests while keeping
  one coordinated release closeout.
- **2026-08-09** — Secure-design review required streaming tar-header
  validation so the 10,000-member cap bounds metadata allocation as well as
  extracted content; AC10 and T6 now prohibit all-members materialisation.
- **2026-08-09** — T3e's whole-suite self-containment audit found four
  non-candidate repository-governance/tool modules that the catalogue-path
  searches could not select. Applied the ratified taxonomy to move three to
  roster and one to tools before the sdist graft.
