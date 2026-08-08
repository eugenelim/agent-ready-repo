# Spec: catalogue test carve-out

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0075, RFC-0082, ADR-0071
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Every test in this repository has a declared owner, and lives where that owner
lives. Tests that assert the catalogue's content is well-formed sit in a
repository-root `tests/` tree, separate from the engine that happens to validate
them. Tests that belong to one pack sit with that pack. Tests of a `tools/`
script sit beside the script.

The pay-off is for someone standing up their own catalogue. `agentbundle
catalogue init` hands them a conformance suite that runs against *their* packs
and tells them whether their catalogue is valid — in every preset, whether they
took the engine from PyPI or vendored it. That suite is portable by construction:
it asserts rules about whatever packs exist, never a roster of the packs this
repository happens to ship.

The engine's own source distribution finally carries a complete, runnable test
tree, which it cannot do while catalogue assertions are mixed into it.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Decide ownership from what a test **asserts**, never from what it reads or
  where it currently sits.
- Classify at the level of the test **class**, and split a module that carries
  both engine and catalogue assertions.
- Record a decided owner for every module touched, so the classification is
  reviewable in the diff rather than implied by the move.
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
  verification is that every relocated module carries a recorded owner and the
  full suite stays green from its new home.
- **Relocation: goal-based, integration surface.** Every suite runs green from
  its new location: the engine suite, the new conformance and roster trees, and
  each pack suite that gained modules.
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
- **The sdist graft: TDD.** Extract a built sdist and collect its suite. The
  test must fail while catalogue assertions remain in the engine tree, which is
  what makes it a real gate rather than a file count.

## Acceptance Criteria

- [ ] **AC1** — Every module in `packages/agentbundle/tests/` asserts engine
      behaviour. No module there resolves the live `packs/` tree to assert about
      its *content* — with one carve-out: engine tests that merely *borrow* a
      live pack as input may remain, and live under `tests/live-catalogue/`
      (AC9b), which is pruned from the sdist. Borrowing and asserting are the
      distinction ADR-0075 draws, and only the latter is disqualifying here.
- [ ] **AC2** — `tests/conformance/` and `tests/roster/` exist at the repository
      root, and `tests` is registered in `tools/lint-build.py`'s
      `RFC_AUTHORISED_DIRS` with an `# RFC-0082` comment.
- [ ] **AC3** — The three modules that test `tools/lint-agents-md.py` live at
      `tools/`.
- [ ] **AC4** — The three known mixed modules — `test_adapter_gemini.py`,
      `test_plugin_manifest_schema.py`, `test_shared_libs_projection.py` — have
      their catalogue-conformance classes extracted into `tests/conformance/`,
      with the engine assertions left behind.
- [ ] **AC5** — No test in `tests/conformance/` names a specific pack.
- [ ] **AC6** — Running `agentbundle catalogue init` into a temporary directory
      and executing the materialised conformance suite against the scaffolded
      catalogue passes. Verified for the default preset and for
      `--preset self-hosted` in both `--tooling` modes.
- [ ] **AC7** — A `catalogue package` archive contains `tests/conformance/`, in
      both the default and source flavours.
- [ ] **AC7b** — **No shipped channel carries `tests/roster/`.** Verified by
      absence in a `catalogue package` archive (both flavours), in a
      `catalogue init` scaffold, and in `--preset self-hosted` output. Both
      include-dir constants are walked wholesale, so a bare `tests` entry would
      ship the roster tree and silently violate D7.
- [ ] **AC8** — The bundled catalogue scaffold carries a `tests/conformance/`
      template, registered in `sync_authoring_scaffold.py`'s `_SYNC_PAIRS`, and
      `agentbundle catalogue init` materialises it. A scaffold file absent from
      `_SYNC_PAIRS` gets no manifest entry and is silently never materialised.
- [ ] **AC9** — A built sdist contains the complete engine test tree — modules
      **and** fixtures — and its suite both collects **and runs** from an
      extracted copy. Collection alone passes on a module that borrows the live
      catalogue and fails at run time, which is the defect this spec ends.
- [ ] **AC9b** — Engine tests that still borrow the live catalogue live under
      `packages/agentbundle/tests/live-catalogue/`, which `MANIFEST.in` prunes;
      verified by absence from the built sdist. The directory's contents at ship
      time are recorded as the remaining, countable debt — RFC-0082's stated
      mechanism and spec exit condition.
- [ ] **AC10** — The artifact gate asserts the sdist's presence half by
      extracting and collecting, not by counting files.
- [ ] **AC11** — **Every destination tree this spec creates or adds to** is
      reachable from the `Makefile` test target and from `build-check.yml` —
      the root `tests/` tree, `tools/` (which enumerates modules by name, with no
      glob), and each `packs/<pack>/tests/` that gained modules. A relocation
      into an unenumerated tree leaves the tests permanently uncollected.
- [ ] **AC11b** — Each new or renamed `build-check.yml` step carries a
      `STEP_DISPOSITION` entry in `tools/lint-ci-parity.py` naming the `make`
      target that covers it locally; that gate fails on an undispositioned step.
- [ ] **AC12** — A decision, recorded in `notes/ownership-record.md`, for which root-`tests/` subtrees enter
      SAST scope, and `SAST_DIRS` reflects it. `SAST_DIRS := tools packs
      packages` excludes the whole tree today; adding `tests` pulls in
      `tests/roster/` as well, and `bandit.yaml`'s `*/tests/*` glob does not
      match a root-anchored `tests/…` path, so scanned test code arrives with no
      test-tree exemption. State the handling for both subtrees.
- [ ] **AC13** — Every relocated module has its owner recorded in a **committed**
      note at `docs/specs/catalogue-test-carve-out/notes/ownership-record.md`,
      including the disposition of the contested calls. A PR description is not
      version-controlled and cannot be re-read during a later drift pass.
- [ ] **AC14** — `tools/lint-build.py`'s top-level-directory audit **runs** on a
      CI checkout where only `origin/main` exists, rather than skipping and
      returning success as it does today.

## Assumptions

- **Technical:** 82 modules match the quoted-directory sweep and 103 match the
  path-form sweep (RFC-0082 § Evidence). Both are candidate sets, not
  measurements, and the implementation re-derives rather than inheriting either —
  the first-cut mapping deliberately omits per-root counts because an earlier
  revision mislabelled the strict figures as loose.
- **Technical:** ownership is a property of test *classes*, not modules — three
  modules in `build/tests/` alone carry conformance classes inside engine
  modules (verified by reading `GeminiShippedAgentToolCoverageTests`,
  `SourcePluginJsonAuditTests`, `RealTreeInvariantTests`).
- **Technical:** five positive allowlists exclude a root `tests/` by
  construction — `RFC_AUTHORISED_DIRS`, `_DEFAULT_INCLUDE_DIRS`,
  `_SOURCE_INCLUDE_DIRS`, `_SYNC_PAIRS`, `SAST_DIRS` (each read directly,
  2026-08-07).
- **Technical:** `agentbundle catalogue init`'s default preset and its
  `--preset self-hosted` path share no code, so each needs its own wiring
  (`commands/catalogue_init.py:22-43`).
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
