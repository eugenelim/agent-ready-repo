# Spec: engine export boundary

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0075, RFC-0082, ADR-0071
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The `agentbundle` package directory holds no test code. Someone installing the
engine — from a wheel, a zipapp, or a vendored copy inside their own catalogue —
receives engine code and nothing else. The rule is enforced by construction: an
artifact that regains test content fails the release build, rather than being
caught by whoever happens to read the diff.

The source distribution is the surface whose consumers *do* run tests, and it is
deliberately left empty of them here. Its graft depends on the engine suite being
self-contained, which is not true until the catalogue carve-out lands — grafting
sooner would ship a packager catalogue assertions that cannot run from an archive
with no `packs/`. That gap is intentional, bounded by the sibling spec, and
named rather than papered over.

Success is measured on the built artifacts, not on the tree that produced them.
The wheel carries zero test entries where it currently carries 45 of 184. The
zipapp and the vendored engine payload carry none. `pip install -e
packages/agentbundle` continues to work unchanged, and every engine test that
passes today still passes from its new location.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Move test files with `git mv`, so history follows them.
- Re-run the reference sweep **unfiltered** before declaring the migration
  complete — including `*.yaml`, which a `*.yml`-only filter silently drops.
- Update every operative reference in the same commit as the move, so no
  intermediate commit leaves the suite uncollectable.
- Carry the `Engine-Change-RFC: RFC-0082` trailer on commits touching
  non-carved-out `packages/agentbundle/` paths. `/tests/` and `build/recipes/`
  are carved out (`tools/lint-catalogue-curation-guard.py:100-115`), so the
  relocation commits themselves do not need it — but the `self_host.py`,
  `build_zipapp.py`, and `_collect_dir_bytes` edits do.

### Ask first

- Any change to which tests *run* — this spec relocates tests and changes no
  assertions. A test that must be modified to survive the move is a signal to
  stop and surface, not to edit quietly.
- Adopting `namespaces = false` in `[tool.setuptools.packages.find]`. It would
  work, and it changes discovery semantics for the whole package.
- Deleting rather than rewriting the `bandit.yaml` entry that goes dead.

### Never do

- **No new top-level directory.** The repository-root `tests/` tree belongs to
  the catalogue carve-out spec, and creating it here would widen this spec past
  its release-blocking scope. Treat that as a rule, not as something the
  toolchain will catch: `RFC_AUTHORISED_DIRS` is the nominal guard, but its audit
  skips itself and returns success on a CI checkout, which the carve-out spec's
  AC14 fixes.
- **No new dependency.** The enforcement gate is pure-stdlib Python in `tools/`;
  `check-wheel-contents` and `pydistcheck` are both rejected on tested evidence.
- No `MANIFEST.in` graft. The sdist's presence half depends on the engine suite
  being self-contained, which is not true until the carve-out lands.
- No `include_package_data = True`. It would promote any grafted tree into the
  wheel and invert the whole rule.
- No changes to pack content, `.apm/` trees, or ADR-0071's `packs/<pack>/tests/`
  destination.

## Testing Strategy

- **The relocation itself: goal-based check, exercised at the integration
  surface.** The whole engine suite runs from its new location and is green.
  A unit test proves nothing here; the question is whether collection, path
  anchors, and CI wiring survive together.
- **Path-anchor rewrites: goal-based.** The suite passing *is* the check.
  Three idioms need rewriting and a `parents[N]`-only sweep misses one of them,
  so the failure mode is a missed edit, which a green suite excludes.
- **The `self_host.py` guard: TDD.** This is the one behavioral change, it is a
  safety control, and its current test passes a hardcoded literal — so it stays
  green while the guard dies. The replacement test drives the real on-disk path
  and must fail against the un-rewritten guard before it passes against the
  rewritten one.
- **The artifact gate: TDD.** A gate is worth only what its negative case is
  worth. It is written against a wheel known to contain tests and must reject
  it, before it is pointed at the real build.
- **The vendored-payload unit test: TDD.** Same reasoning — it must fail against
  today's unfiltered `_collect_dir_bytes` before it passes against the filtered
  one.
- **Editable install: goal-based.** `pip install -e` into a throwaway venv,
  then import the package and run the console script.

## Acceptance Criteria

- [ ] **AC1** — `packages/agentbundle/agentbundle/` contains no test files —
      no `tests/` directory, no `test_*.py`, no `conftest.py` — with one stated
      exemption: `_data/catalogue-scaffold/**` is inert template content that
      ships in the wheel by design and is never collected here.
- [ ] **AC2** — The relocated engine suite runs green from
      `packages/agentbundle/tests/`, with the same number of passing tests as
      before the move.
- [ ] **AC3** — A freshly built wheel contains zero entries matching a test
      path outside `_data/catalogue-scaffold/**`, verified by opening the
      artifact rather than by reading config.
- [ ] **AC4** — A freshly built zipapp contains zero engine test entries, and
      `"tests"` is removed from `build_zipapp.py`'s `ignore_patterns` entirely.
      The builder copies `packages/agentbundle/agentbundle` only, so after the
      move no engine test tree is inside that root and the pattern protects
      nothing — while still matching by basename at any depth, which would strip
      a scaffold test template. A zipapp built from a tree containing
      `_data/catalogue-scaffold/**/tests/` retains that content.
- [ ] **AC5** — `_collect_dir_bytes`'s two vendored call sites emit no test
      content; its packs call site still does. Asserted by a unit test, not by
      inspection.
- [ ] **AC6** — `pip install -e packages/agentbundle` succeeds; `import
      agentbundle` and `import agentbundle.build` resolve; the `agentbundle`
      console script reports the correct version; `import
      agentbundle.build.tests` raises `ModuleNotFoundError`.
- [ ] **AC7** — `build/self_host.py`'s destructive-write guard refuses a
      real-write self-host targeting the relocated fixture tree. It matches
      `tests` preceding `fixtures` as path components within the repository
      tree, preserving the existing anti-over-match invariant its comment names
      (`my-tests/fixtures-backup/` must still pass). Its covering test drives the
      real on-disk path, not a hardcoded string, and includes a negative case
      where the two components appear in the wrong order.
- [ ] **AC8** — The artifact gate is a pure-stdlib script in `tools/`, wired
      into `release-agentbundle.yml` after the build step. It fails on a **wheel
      or zipapp** containing test content, and passes a test-shaped path under
      `_data/catalogue-scaffold/**`; the exemption is written into the gate, not
      left to a reviewer. It asserts **nothing** about the sdist here — that
      surface's rule inverts from absence to presence when the carve-out lands
      its graft, and a gate asserting absence would then reject a correct
      artifact.
- [ ] **AC9** — The gate script's own path is in that workflow's
      `pull_request.paths` filter, so a change to the gate runs the gate.
- [ ] **AC10** — All ten operative references to the old path are updated, and
      an unfiltered re-sweep finds no operative reference remaining. Historical
      references under `docs/specs/**`, `docs/rfc/**`, `docs/product/changelog.md`,
      and the package `CHANGELOG.md` are deliberately untouched.
- [ ] **AC11** — `make ci` passes, and the Windows build-check leg passes with
      `self_host_windows.py`'s invocation paths updated.
- [ ] **AC12** — A sweep of `packages/agentbundle/agentbundle/**` for other
      substring-shaped path guards over `tests`, `fixtures`, or `build`, with its
      result recorded in a committed note at
      `docs/specs/engine-export-boundary/notes/guard-sweep.md` (found and fixed,
      or none). RFC-0082's pre-mortem asks for this rather than assuming
      `self_host.py` is the only one.
- [ ] **AC13** — A decision on whether `catalogue_tooling/self_host_windows.py`
      — a test runner that ships in every artifact — belongs inside the export
      boundary (RFC-0082 open question 2), recorded in the same committed note as
      AC12: either relocate it, or keep it with a stated reason.

## Assumptions

- **Technical:** runtime is Python ≥3.11 (`packages/agentbundle/pyproject.toml:9`).
- **Technical:** the wheel ships tests through PEP 420 namespace discovery, not
  `__init__.py` — deleting the marker leaves 44 of 45 entries (probe:
  `PEP420PackageFinder.find` vs `PackageFinder.find` against the real tree).
- **Technical:** editable install is unaffected by the move — `pip install -e`
  into a temp venv exits 0 and the console script resolves (probe, 2026-08-07).
- **Technical:** three path-anchor idioms exist in the suite —
  `parents[5]` (35 modules), one chained `.parent` walk, and two `parents[2]`
  reaches into the package; a `parents[N]`-only sweep misses the chained one.
- **Technical:** `build_zipapp.py`'s `ignore_patterns("tests")` matches by name
  at any depth (probe: `shutil.ignore_patterns`).
- **Technical:** ten files carry operative references, re-swept 2026-08-08 after
  rebasing onto `main`.
- **Process:** commits touching *non-carved-out* `packages/agentbundle/` paths
  require an `Engine-Change-RFC:` trailer; `classify_paths` carves out `/tests/`
  and `build/recipes/` (`tools/lint-catalogue-curation-guard.py:100-115`).
- **Process:** this spec is queued under `ini-002` Platform Core (user
  confirmation 2026-08-08). The `workspace.toml` queue entry is written by the
  same changeset that lands this spec, not assumed present.
- **Product:** `agentbundle/_data/install-marker.py`'s non-importable path is
  out of scope; a `[backlog].open` slug is added for it by the changeset that
  lands this spec (user confirmation 2026-08-08).
- **Process:** RFC-0082 open question 1 is answered here — the gate fails
  immediately rather than warning on introduction. The defect it guards exists
  today, so the gate is written against a known-good post-migration state and
  has nothing to grandfather.
- **Technical:** `packages/agentbundle/tests/build/` keeps an `__init__.py`,
  matching `tests/unit/` and `tests/integration/`, which both have one. The
  marker is not what puts the tree in the wheel, and dropping it would make the
  new sibling import as top-level names while its siblings do not.
