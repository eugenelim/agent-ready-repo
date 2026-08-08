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
- **One test edit is pre-authorised, and only one.**
  `test_self_host_fixture_guard.py:74` passes the literal
  `"agentbundle/build/tests/fixtures/packs"`, which T1 repoints to
  `"tests/fixtures/packs"` — a path that matches both the old substring guard and
  the new component guard, so T1 stays green on its own. Its module-level
  `_FIXTURE_DIR` is **not** touched: it points at
  `packages/agentbundle/tests/fixtures/`, a tree this change does not move, and
  repointing it would destroy the coverage T2 needs. Everything else moves
  unmodified.
- Re-run the reference sweep **unfiltered** before declaring the migration
  complete — including `*.yaml`, which a `*.yml`-only filter silently drops.
- Update every operative reference in the same commit as the move, so no
  intermediate commit leaves the suite uncollectable.
- Carry the `Engine-Change-RFC: RFC-0082` trailer on every commit in this
  changeset **except** one touching only `packages/agentbundle/**/tests/**`.
  `/tests/` and `build/recipes/` are the guard's only carve-outs
  (`tools/lint-catalogue-curation-guard.py:100-115`), and T1 edits
  `self_host_windows.py` and `pyproject.toml` alongside the move, so the
  relocation commit needs it too. `tools/build_zipapp.py` is outside
  `packages/agentbundle/` and needs none.

### Ask first

- Any change to which tests *run*, or to what they assert, beyond the two
  pre-authorised edits named under *Always do*. A third test needing
  modification to survive the move is a signal to stop and surface.
- Adopting `namespaces = false` in `[tool.setuptools.packages.find]`. It would
  work, and it changes discovery semantics for the whole package.
- Adopting a different resolution for any of the three dead references than the
  removal AC10 names.

### Never do

- **No new top-level directory.** The repository-root `tests/` tree belongs to
  the catalogue carve-out spec, and creating it here would widen this spec past
  its release-blocking scope. Treat that as a rule, not as something the
  toolchain will catch: `RFC_AUTHORISED_DIRS` is the nominal guard, but its audit
  skips itself and returns success on a CI checkout, which the carve-out spec's
  AC14 fixes.
- **No new dependency.** The enforcement gate is pure-stdlib Python in `tools/`.
  `check-wheel-contents` and `pydistcheck` are both rejected under this rule;
  `check-wheel-contents` additionally does not detect the defect at all, and
  `pydistcheck` detects it only via `--expected-files`, not the natural-reading
  `--expected-directories` form.
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
- **Recorded decisions and sweeps (AC12, AC13): goal-based.** The committed note
  exists at the named path and names each file swept and each decision taken.
  Neither is TDD-shaped: one is a codebase sweep, the other a judgement.

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
- [ ] **AC4** — A freshly built zipapp contains zero engine test entries, and a
      zipapp built from a tree containing `_data/catalogue-scaffold/**/tests/`
      retains that content. (Mechanism and rationale: `plan.md` T4.)
- [ ] **AC5** — `_collect_dir_bytes`'s two vendored call sites emit no test
      content; its **packs** call site and its **guides** call site (under
      `--guides selected`) both still do. Asserted by a unit test appended to
      `packages/agentbundle/tests/unit/test_catalogue_tooling_self_hosted_init.py`,
      not by inspection.
- [ ] **AC5b** — Every test artifact this spec creates has a declared home and a
      runner. The gate and zipapp cases live in
      `tools/test_check_artifact_contents.py`, which is added to the `Makefile`'s
      enumerated `tools/` pytest line — that list is curated by hand, not
      globbed, so an unlisted file runs nowhere and would let AC8 and AC11 pass
      vacuously.
- [ ] **AC6** — `pip install -e packages/agentbundle` succeeds; `import
      agentbundle` and `import agentbundle.build` resolve; the `agentbundle`
      console script reports the correct version; `import
      agentbundle.build.tests` raises `ModuleNotFoundError`.
- [ ] **AC7** — `build/self_host.py`'s destructive-write guard refuses a
      real-write self-host targeting the relocated fixture tree
      (`…/tests/build/fixtures/…`) as well as the unmoved one
      (`…/tests/fixtures/…`). It matches `tests` preceding `fixtures` as **path
      components**, which preserves the anti-over-match invariant its comment
      names — `my-tests/fixtures-backup/` still passes, because neither is a
      component match. The helper signature is unchanged: no repo-root argument,
      no new parameter. Its covering test gains a case for the relocated shape
      and a negative case for the components in the wrong order.
- [ ] **AC8** — The artifact gate is a pure-stdlib script in `tools/` that
      accepts a `.whl` or a `.pyz`, fails on either containing test content, and
      passes a test-shaped path under `_data/catalogue-scaffold/**` — the
      exemption written into the gate, not left to a reviewer. It asserts
      **nothing** about the sdist: that surface's rule inverts from absence to
      presence when the carve-out lands its graft, and an absence assertion would
      then reject a correct artifact.
- [ ] **AC8b** — The gate runs on both artifacts it covers, in this order:
      the existing "Build wheel + sdist" step; then a new
      `python3 tools/build_zipapp.py <scratch-dir>` step, because no workflow
      builds a zipapp today and the builder requires an output directory
      argument; then the gate, pointed at the wheel in
      `packages/agentbundle/dist/` and at `<scratch-dir>/agentbundle.pyz`.
      `<scratch-dir>` is **outside** `packages/agentbundle/dist/`: that directory
      is what `twine check` validates and what the publish job uploads to PyPI,
      so a stray `.pyz` there would redden the check and poison the release.
- [ ] **AC9** — The gate script's own path is in that workflow's
      `pull_request.paths` filter, so a change to the gate runs the gate.
- [ ] **AC10** — Every operative reference enumerated in `plan.md` T1 is
      resolved — most rewritten, three **removed as dead**: `bandit.yaml`'s
      `*/build/tests/*` entry (its `*/tests/*` sibling already covers the new
      path), the root `pyproject.toml` mypy `exclude` (which falls outside
      `files = [...]` once the tree moves), and `tools/lint-build.py:123`'s
      composed fixture path. And
      an unfiltered re-sweep finds no operative reference remaining. Historical
      references under `docs/specs/**`, `docs/rfc/**`, `docs/product/changelog.md`,
      and the package `CHANGELOG.md` are deliberately untouched — **except**
      `docs/specs/catalogue-test-carve-out/**`, a live Draft spec pair whose
      `build/tests/` references this change invalidates.
- [ ] **AC11** — `make ci` passes, and the Windows build-check leg passes with
      `self_host_windows.py`'s invocation paths updated.
- [ ] **AC14** — `packages/AGENTS.md` § Test conventions names the third engine
      test root this change creates. It currently says the roots are `tests/unit/`
      and `tests/integration/`, which T1 falsifies. Only that correction lands
      here; the full four-owner rewrite RFC-0082 calls for belongs to the
      carve-out spec, and AC10's literal sweep would never surface this file.
- [ ] **AC12** — A sweep of `packages/agentbundle/agentbundle/**` for other
      substring-shaped path guards over `tests`, `fixtures`, or `build`, with its
      result recorded in a committed note at
      `docs/specs/engine-export-boundary/notes/guard-sweep.md` (found and fixed,
      or none). RFC-0082's pre-mortem asks for this rather than assuming
      `self_host.py` is the only one.
- [ ] **AC13** — `catalogue_tooling/self_host_windows.py` stays where it is, and
      the reason is recorded in the same committed note as AC12. This answers
      RFC-0082 open question 2 against its recommended default, deliberately:
      relocating it would re-touch every file T1 has just swept, and it is a
      tools-owned test runner — precisely the ownership question the carve-out
      spec exists to decide. Its invocation paths are updated in place here.

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
- **Technical:** the operative reference set is enumerated in `plan.md` T1 and
  re-swept 2026-08-08 after rebasing onto `main`. The enumeration in `plan.md` T1
  is the single canonical statement of the set; no count is restated here.
- **Technical:** moving the suite under `packages/agentbundle/tests/` brings it
  into scope of that tree's autouse `_isolate_user_config_dir` fixture
  (`tests/conftest.py:26-43`), which redirects `HOME`/`XDG_CONFIG_HOME`/`APPDATA`/
  `USERPROFILE`. Modules that spawn subprocesses with `cwd=REPO_ROOT` inherit it.
- **Technical:** the move removes the relocated modules from
  `tools/lint-build.py`'s stdlib-import audit, which walks
  `packages/agentbundle/agentbundle/build/**`. That is an accepted, recorded
  scope reduction — the audit exists to police shipped engine code, and these
  files stop being that.
- **Process:** commits touching *non-carved-out* `packages/agentbundle/` paths
  require an `Engine-Change-RFC:` trailer; `classify_paths` carves out `/tests/`
  and `build/recipes/` (`tools/lint-catalogue-curation-guard.py:100-115`).
- **Process:** this spec is queued under `ini-002` Platform Core
  (`workspace.toml:141`; user confirmation 2026-08-08).
- **Product:** `agentbundle/_data/install-marker.py`'s non-importable path is
  out of scope and carries the `agentbundle-install-marker-importable-path`
  slug in `[backlog].open` (user confirmation 2026-08-08).
- **Process:** RFC-0082 open question 1 is answered here — the gate fails
  immediately rather than warning on introduction. The defect it guards exists
  today, so the gate is written against a known-good post-migration state and
  has nothing to grandfather.
- **Technical:** `packages/agentbundle/tests/build/` keeps an `__init__.py`,
  matching `tests/unit/` and `tests/integration/`, which both have one. The
  marker is not what puts the tree in the wheel, and dropping it would make the
  new sibling import as top-level names while its siblings do not.
