# Spec: catalogue test carve-out

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0075, RFC-0082, ADR-0071
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Every test class in this repository has one owner under ADR-0075's taxonomy and
lives with that owner: engine, catalogue rule-shaped, catalogue roster-shaped,
one pack, or `tools/`. Every candidate module that reaches into the live
catalogue has a committed class-level ownership decision, including modules
whose tests stay with the engine.

Tests that assert that any catalogue is well-formed sit in a repository-root
`tests/conformance/` tree, separate from the engine that validates them. Tests
that pin this repository's catalogue sit in non-shipping `tests/roster/`. Tests
that belong to one pack sit with that pack. Tests of a `tools/` script sit beside
the script.

The pay-off is for someone standing up their own catalogue. `agentbundle
catalogue init` hands them a conformance suite that runs against *their* packs
and tells them whether their catalogue is valid — in every preset, whether they
took the engine from PyPI or vendored it. That suite is portable by construction:
it asserts rules about whatever packs exist, never a roster of the packs this
repository happens to ship.

The engine's source distribution carries its complete, self-contained test tree
and fixtures. Extracting the archive and running that suite needs no repository
root, live `packs/`, `profiles/`, `contracts/`, or `guides/` tree.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Decide ownership from what a test **asserts**, never from what it reads or
  where it currently sits.
- Classify at the level of the test **class**, and split a module that carries
  both engine and catalogue assertions.
- Inventory every loose `packages/agentbundle/tests/test*.py` module, re-derive
  the candidate set in the three nested engine-test roots with both RFC-0082
  search methods, then inspect all four roots for marker-walking and
  composed-path cases that either method misses.
- Record every candidate module and every test class it contains, including
  engine-owned classes that stay put. Module-level tests may share one recorded
  disposition only when they all assert the same ownership boundary.
- Verify portability by running the materialised suite against a scaffolded
  catalogue, not by reading it.

### Ask first

- Reclassifying anything the first-cut mapping marks as a **contested call**.
  Three are genuinely open; the fourth — granularity — is already decided by
  ADR-0075 (*ownership is assigned per test class, not per module*), so only its
  per-module application needs recording, not the principle.
- Rewriting a roster-shaped test into a rule-shaped one beyond the trivial
  cases. The default is relocate-and-mark; a wholesale rewrite is a separate
  decision.
- Whether `contracts/adapter.toml` counts as catalogue content or engine input.
  It is unsettled, it affects several modules, and it should be decided once.

### Never do

- **No new dependency.** Enforcement stays pure-stdlib Python in `tools/`.
- No new top-level directory other than the RFC-0082-authorised `tests/` tree.
- **No test may move without an owner recorded.** A bulk relocation driven by a
  grep is the failure mode this spec exists to prevent; an early automated pass
  misfiled 24 modules into a pack named `contracts` that were reading the
  repository-root `contracts/` directory.
- No changes to ADR-0071's `packs/<pack>/tests/` layout, only additions to it.
- No shipped conformance test that names a specific pack.
- **No `tests/roster/` content in any shipped channel.** Both packaging
  include-lists are wholesale directory walks, so scoping must be to
  `tests/conformance/` rather than to `tests`.

## Testing Strategy

- **Classification: goal-based, human-reviewed.** There is no automated check
  for "is this the right owner" — that is the finding the RFC rests on. The
  verification is that every candidate class carries a recorded owner and the
  full suite stays green from its final home.
- **Relocation: goal-based, integration surface.** Every suite runs green from
  its new location: the engine suite, the new conformance and roster trees, and
  each pack suite that gained modules. A moved pack test executes with its
  pack-declared test dependencies present; a missing-dependency skip is a gate
  failure, not a green relocation.
- **Portability of the shipped suite: goal-based, end-to-end.** Scaffold a
  catalogue into a temporary directory with `agentbundle catalogue init` and run
  the materialised conformance suite against it. This is the only check that
  distinguishes a rule-shaped suite from one that merely looks rule-shaped, and
  it is why the criterion is written as a command rather than a review.
- **Pack-name absence in the shipped suite (AC5): goal-based.** A grep-shaped
  check over `tests/conformance/` for any shipped pack name, run in CI. This is
  what makes D7 mechanical rather than a review judgement — the same reason the
  `conformance/` ÷ `roster/` split exists.
- **The allowlist widenings: goal-based.** Each is verified by its effect —
  the directory is admitted, the archive contains the tree, the scaffold
  materialises it — never by reading the config.
- **The sdist graft: TDD.** Extract a built sdist, collect its suite, and run it
  from the extracted copy. The negative case proves that a suite which depends
  on a checkout-local catalogue is rejected; counting files is not a gate. The
  extracted run uses the same declared test dependencies as the normal package
  gate, preflights optional imports retained by engine tests, and rejects an
  unexpected missing-dependency skip rather than treating it as success.

## Acceptance Criteria

- [x] **AC1** — Every module in `packages/agentbundle/tests/` asserts engine
      behaviour. No engine test requires the checkout's live `packs/`,
      `profiles/`, `contracts/`, or `guides/` tree: borrowed catalogue inputs are
      fixture-backed, and catalogue assertions live with the catalogue owner.
- [x] **AC2** — `tests/conformance/` and `tests/roster/` exist at the repository
      root, and `tests` is registered in `tools/lint-build.py`'s
      `RFC_AUTHORISED_DIRS` with an `# RFC-0082` comment.
- [x] **AC3** — The three modules that test `tools/lint-agents-md.py` live at
      `tools/`.
- [x] **AC4** — The three known mixed modules — `test_adapter_gemini.py`,
      `test_plugin_manifest_schema.py`, `test_shared_libs_projection.py` — have
      their catalogue-conformance classes extracted into `tests/conformance/`,
      with the engine assertions left behind. Every additional mixed module
      found during the complete classification receives the same class-level
      treatment.
- [x] **AC5** — No test in `tests/conformance/` names a specific pack.
- [x] **AC6** — Running `agentbundle catalogue init` into a temporary directory
      and executing the materialised conformance suite against the scaffolded
      catalogue passes. Verified for the default preset and for
      `--preset self-hosted` in both `--tooling` modes.
- [x] **AC7** — A `catalogue package` archive contains `tests/conformance/`, in
      both the default and source flavours.
- [x] **AC7b** — **No shipped channel carries `tests/roster/`.** Verified by
      absence in a `catalogue package` archive (both flavours), in a
      `catalogue init` scaffold, and in `--preset self-hosted` output. Both
      include-dir constants are walked wholesale, so a bare `tests` entry would
      ship the roster tree and silently violate D7.
- [x] **AC8** — The bundled catalogue scaffold carries the portable
      `tests/conformance/` suite. Every file is registered in
      `sync_authoring_scaffold.py`'s `_SYNC_PAIRS`, and `agentbundle catalogue
      init` materialises it. A scaffold file absent from `_SYNC_PAIRS` gets no
      manifest entry and is silently never materialised.
- [x] **AC9** — A built sdist contains the complete engine test tree — modules
      **and** fixtures — and its suite both collects **and runs** from an
      extracted copy. Collection alone passes on a module that borrows the live
      catalogue and fails at run time, which is the defect this spec ends. The
      archive run installs the same declared test dependencies as the normal
      `agentbundle` package gate. Before pytest, it imports every optional module
      that a retained engine test would otherwise pass through
      `pytest.importorskip`; a failed import fails the gate. Pytest's reported
      skip reasons are checked, and an unrecognised dependency-absence skip —
      including `not installed`, `No module named`, or an `importorskip` reason —
      fails instead of certifying the archive. So does a skip caused by absent
      checkout-local `packs/`, `profiles/`, `contracts/`, `guides/`, `dist/apm`,
      or content described as "not present in this checkout". Intentional
      platform or feature skips remain permitted only through the package
      suite's explicit expected skip policy.
- [x] **AC9b** — Engine tests that still borrow the live catalogue live under
      `packages/agentbundle/tests/live-catalogue/`, which `MANIFEST.in` prunes;
      verified by absence from the built sdist. The directory is empty or absent
      when this spec ships: it is a visible migration rail, not accepted
      remaining debt.
- [x] **AC10** — The artifact gate asserts the sdist's presence half by safely
      extracting, collecting, and executing the suite, not by counting files.
      Extraction uses a fresh temporary root; canonical destinations stay under
      that root; absolute, traversing, symlink, hard-link, and special-file
      members are rejected. Member-name checks are host-independent and reject
      POSIX absolute paths, Windows drive-absolute and drive-relative paths, UNC
      paths, and traversal using `/` or `\` before any write. The gate caps an
      archive at 10,000 members, 32 MiB per member, 256 MiB total uncompressed,
      and a 100:1 aggregate expansion ratio. Member validation streams tar
      headers and applies the count limit before retaining the full member set;
      `TarFile.getmembers()` or an equivalent unbounded metadata materialisation
      is not permitted. Temporary content is removed on every exit path. Pytest
      is invoked as an argument vector without a shell,
      with 120 seconds for collection and 900 seconds for execution; timeout or
      any extraction, collection, or execution error fails closed. The workflow
      job timeout is at least 20 minutes so it exceeds the subprocess bounds.
- [x] **AC11** — **Every destination tree this spec creates or adds to** is
      reachable from the `Makefile` test target and from `build-check.yml` —
      the root `tests/` tree, `tools/` (which enumerates modules by name, with no
      glob), and each `packs/<pack>/tests/` that gained modules. A relocation
      into an unenumerated tree leaves the tests permanently uncollected. Each
      affected pack runner installs or preflights the dependencies declared for
      its relocated tests and rejects a missing-dependency skip; in particular,
      the relocated Linear primitive test must execute with `httpx` available.
- [x] **AC11b** — Each new or renamed `build-check.yml` step carries a
      `STEP_DISPOSITION` entry in `tools/lint-ci-parity.py` naming the `make`
      target that covers it locally; that gate fails on an undispositioned step.
- [x] **AC12** — `SAST_DIRS` includes `tests`, so both `tests/conformance/` and
      `tests/roster/` enter Bandit and Semgrep scope. No new root-test exemption
      is added to `bandit.yaml` or the Semgrep arguments; a finding is fixed or
      surfaced rather than hidden by widening an exclusion.
- [x] **AC13** — The complete classification set — every loose top-level
      `packages/agentbundle/tests/test*.py` module, plus the union of both RFC
      search methods and the supplemental marker-walking and composed-path
      inventory across all four engine-test roots — has a **committed**,
      class-level ownership record at
      `docs/specs/catalogue-test-carve-out/notes/ownership-record.md`. It records
      the inventory/search method and candidate counts per existing engine test
      root; one disposition per test class (plus any module-level tests); owner,
      basis, destination, and shipping rule; every engine-owned stay; every
      mixed-module extraction; and the disposition of all contested calls. A
      completeness check proves that every loose top-level module and every
      candidate module from the three nested-root discovery inputs appears in
      the record.
- [x] **AC14** — `tools/lint-build.py`'s top-level-directory audit **runs** on a
      CI checkout where only `origin/main` exists, rather than skipping and
      returning success as it does today.
- [x] **AC15** — `packages/AGENTS.md` states the five ownership categories,
      their homes, and their per-surface inclusion rules, while retaining the
      three engine test roots established by the engine-export-boundary spec.
- [x] **AC16** — Every affected pack carries the required matching version bump
      in `pack.toml` and `.claude-plugin/plugin.json`, the marketplace and product
      changelog are regenerated, and the scaffold change carries one
      `agentbundle` version bump plus its package changelog entry. Package-code
      commits outside the tests/recipes carve-outs carry the required
      `Engine-Change-RFC: RFC-0082` trailer.

## Assumptions

- **Technical:** 82 modules match the quoted-directory sweep and 103 match the
  path-form sweep (RFC-0082 § Evidence). Both are candidate sets, not
  measurements, and the implementation re-derives rather than inheriting either —
  the first-cut mapping deliberately omits per-root counts because an earlier
  revision mislabelled the strict figures as loose.
- **Technical:** ownership is a property of test *classes*, not modules — three
  modules in `tests/build_pipeline/` (formerly `agentbundle/build/tests/`) alone
  carry conformance classes inside engine modules (verified by reading
  `GeminiShippedAgentToolCoverageTests`,
  `SourcePluginJsonAuditTests`, `RealTreeInvariantTests`).
- **Technical:** five positive allowlists exclude a root `tests/` by
  construction — `RFC_AUTHORISED_DIRS`, `_DEFAULT_INCLUDE_DIRS`,
  `_SOURCE_INCLUDE_DIRS`, `_SYNC_PAIRS`, `SAST_DIRS` (each read directly,
  2026-08-07).
- **Technical:** the fifth allowlist includes both catalogue subtrees in SAST
  scope; no new test-tree exemption is introduced (user confirmation
  2026-08-09).
- **Technical:** `agentbundle catalogue init`'s default preset and its
  `--preset self-hosted` path use distinct materialisation implementations, so
  each needs its own wiring (`commands/catalogue_init.py:22-43`).
- **Technical:** each selected pack's `tests/` already ships through
  `catalogue init --preset self-hosted` today, unfiltered — that column needs no
  new work, only to survive the engine spec's exclusion edit
  (`initialise_self_hosted.py:807`).
- **Process:** this spec is queued under `ini-002` Platform Core
  (user confirmation 2026-08-08).
- **Product:** roster-shaped tests are relocated and marked non-shipping;
  rewriting them into rule-shaped tests is a named follow-up, not this spec
  (user confirmation 2026-08-08).
- **Product:** the sweep cannot see modules that locate the repository root by
  walking for a marker rather than by index — `test_shared_libs_projection.py`
  is one, found only by hand.
- **Product:** the complete candidate mapping is committed at class granularity,
  including engine-owned tests that do not move (user confirmation 2026-08-09).
- **Process:** `RFC_AUTHORISED_DIRS`' CI-checkout fallback is repaired and tested
  before the repository-root `tests/` tree is introduced (user confirmation
  2026-08-09).
- **Technical:** the current `packages/agentbundle/` tree is 545 files and about
  6 MiB (`find … -type f | wc -l`; `du -sk`, 2026-08-09), so AC10's archive
  limits leave more than an order of magnitude of growth while bounding a
  malformed artifact.
