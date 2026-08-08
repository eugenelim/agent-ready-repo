# Plan: engine export boundary

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is a `git mv` wearing a much larger coat. Moving
`packages/agentbundle/agentbundle/build/tests/` to
`packages/agentbundle/tests/build/` is one command; making the repository still
work afterwards is the spec.

Three edit sets follow the move, and they are different in kind. **Path anchors
inside the suite** are mechanical but come in three idioms, one of which a
`parents[N]` sweep misses. **Operative references outside the suite** are ten
files, most of the weight in one CI workflow. **One behavioural rewrite** — the
`self_host.py` destructive-write guard — is the only place where code semantics
change, and it is the riskiest task in the plan by a wide margin: the guard fails
open, silently, and its existing test passes a hardcoded string that keeps it
green either way.

Order of operations is chosen so nothing is ever half-moved. T1 moves everything
and fixes every reference in one commit, because an intermediate state where the
suite is uncollectable is worse than a large commit. T2 rewrites the guard under
TDD, since it is a control and deserves a failing test first. T3 and T4 add the
two enforcement instruments, each written against a known-bad input before being
pointed at the real build. T5 wires CI. T6 cuts the release.

The sdist graft is deliberately **not** here. It waits for the carve-out spec,
because grafting a suite that still contains catalogue assertions ships a
redistributor something that cannot run — the exact defect RFC-0082 exists to end.

## Constraints

- **ADR-0075** — the ownership taxonomy, the four homes, and per-owner
  inclusion. This spec implements the engine home and the absence half.
- **RFC-0082** — the proposal, its measured evidence, and the two-spec split.
- **ADR-0071** — unchanged and not reopened; `packs/<pack>/tests/` stays.
- **`Engine-Change-RFC:` trailer** — required on commits touching non-carved-out
  `packages/agentbundle/` paths; `classify_paths` carves out `/tests/` and
  `build/recipes/` (`tools/lint-catalogue-curation-guard.py:100-115`).
- **No new top-level directory** — `RFC_AUTHORISED_DIRS` refuses one, and the
  root `tests/` belongs to the carve-out spec.
- **New `tools/` scripts are pure-stdlib Python** (root `AGENTS.md`).

## Construction tests

**Integration tests:**

- Full engine suite from the new location: `python -m pytest tests/ -q` in
  `packages/agentbundle`, green, with the same passing count as before the move.
- `make ci` green on Linux/macOS.
- Windows build-check leg green — it is driven entirely by
  `self_host_windows.py`, whose invocation paths T1 rewrites.

**Manual verification:**

- Build a wheel and an sdist from a clean copy; open both with `zipfile` /
  `tarfile` and confirm the wheel's test-entry count is zero (was 45 of 184).
- `pip install -e packages/agentbundle` into a throwaway venv; confirm the
  console script runs and `agentbundle.build.tests` no longer resolves.

## Design (LLD)

`Shape: service`. Two sub-sections earn their place; the rest are pruned.

### Interfaces & contracts

Traces to AC3, AC4, AC5, AC8. The enforcement surface is a single stdlib script,
`tools/check-artifact-contents.py`, whose contract is: given a built wheel or
sdist path, exit non-zero if it contains any entry matching a test path. It takes
the artifact path as `argv[1]`; it reads `zipfile` for `.whl` and `tarfile` for
`.tar.gz`; it prints offending entries to stderr. It asserts **absence only** in
this spec — the presence half arrives with the carve-out's graft, and the script
grows a second mode then rather than being written speculatively now.

The vendored payload is not an artifact, so it is verified by unit test against
`_collect_dir_bytes` rather than by this script. That asymmetry is deliberate and
is why the spec names two instruments.

### Data & schema

Traces to AC1, AC2, AC6. No schema changes. The one structural fact worth
recording: `[tool.setuptools.packages.find]` keeps `namespaces = true` (the
default). The move makes discovery correct by layout, so the discovery mode is
left alone — flipping it would work but changes semantics for the whole package
and is listed under *Ask first*.

## Tasks

### T1 — Move the tree and update every reference

- **Implements:** AC1, AC2, AC6, AC10 (Testing Strategy: goal-based, integration
  surface)
- **Depends on:** none

**Tests:**

- Before: record the passing test count of `pytest tests/ agentbundle/build/tests/`.
- After: `python -m pytest tests/ -q` from `packages/agentbundle` passes with the
  same count. A drop means a module stopped being collected.
- `! grep -rq "build/tests" --include='*.py' --include='*.toml' --include='*.yml'
  --include='*.yaml' --include='*.md' .` over the operative set (excluding
  `docs/`, `docs/product/changelog.md`, and the package `CHANGELOG.md`). Written
  as a negated match: bare `grep` exits 1 on no-match, which a harness reads as
  failure.
- A second sweep for composed fragments — `"tests" / "fixtures"` built from
  parts — returns nothing operative.
- Editable-install regression (AC6): `pip install -e packages/agentbundle` into a
  throwaway venv exits 0; `import agentbundle` and `import agentbundle.build`
  resolve; the console script reports the version from `pyproject.toml`; and
  `import agentbundle.build.tests` raises `ModuleNotFoundError`.

**Approach:**

`git mv packages/agentbundle/agentbundle/build/tests packages/agentbundle/tests/build`,
keeping its `__init__.py`. `tests/unit/` and `tests/integration/` both have one,
and the marker is not what puts the tree in the wheel — PEP 420 discovery is.
Dropping it would make the new sibling import as top-level names while its
siblings import as `tests.unit.*`, reintroducing basename-collision exposure.

Path anchors, three idioms:

- `parents[5]` → `parents[4]` in 35 modules (repo-root anchor).
- One chained `.parent.parent.parent.parent` in
  `tests/build/test_lint_packs.py:71` — same correction, and a `parents[N]`
  sweep does not see it.
- Two `parents[2]` reaches *into* the package — `test_writers_emit_lf.py:29` and
  `test_adapter_root_bins_projection.py:202`. These are genuine rewrites: they
  resolve `agentbundle/_data/` by relative depth, which only worked because the
  test lived inside the package. Resolve the package explicitly.

Operative references, ten files: `.github/workflows/build-check.yml` (17
occurrences — the bulk), `.github/workflows/catalogue-tooling-ci-gates.yml` (5),
`agentbundle/catalogue_tooling/self_host_windows.py` (4 — shipped code invoking
the suite by path), root `pyproject.toml` (mypy `exclude`),
`packages/agentbundle/pyproject.toml` (`testpaths`), `Makefile`,
`.github/workflows/release-agentbundle.yml`, `bandit.yaml` (its
`*/build/tests/*` entry goes dead; `*/tests/*` still matches so scan coverage is
unchanged), `packs/AGENTS.local.md`, and
`tests/integration/test_install_snapshot.py`.

Two literals sit *inside* the suite and are easy to overlook because the sweep's
exclusion list is written for `docs/`: `test_end_to_end_build.py:5` and
`test_self_host_fixture_guard.py:74`. The second is the hardcoded argument that
keeps the destructive-write guard's test green either way — replace it here, in
the same commit as the move, so T1's own sweep can pass. T2 then rewrites the
guard it covers.

One reference is genuinely invisible to a literal sweep and needs a second pass
for composed fragments: `tools/lint-build.py:123` builds
`Path(build_dir) / "tests" / "fixtures"` from parts and goes dead after the move.
RFC-0082 § Evidence names this as the third reference class.

Sweep with `*.yaml` included — a `*.yml`-only filter silently drops
`bandit.yaml`, which happened twice while authoring RFC-0082.

### T2 — Rewrite the `self_host.py` destructive-write guard

- **Implements:** AC7, AC12, AC13 (Testing Strategy: TDD)
- **Depends on:** T1

**Tests:**

- A failing test first: drive `self_host` with `--packs-dir` pointing at the
  *relocated* fixture tree and assert it refuses. Against the un-rewritten guard
  this passes through and the test fails — that failure is the point.
- The existing `test_self_host_fixture_guard.py` currently asserts against the
  hardcoded literal `"agentbundle/build/tests/fixtures/packs"`. Replace that with
  the real on-disk path so the test cannot stay green while the guard is dead.
- Keep a case for `packages/agentbundle/tests/fixtures/`, which still matches
  today and must keep matching.

**Approach:**

`build/self_host.py:1611` reads `if "tests/fixtures/" in packs_dir.as_posix()`.
After the move the path is `…/tests/build/fixtures/`, where `tests` and
`fixtures` are no longer adjacent, so the substring is absent and the guard fails
open — the command would overwrite the working tree with fixture data.

Rewrite it to test for `tests` **preceding** `fixtures` as path components within
the repository tree. Order and locality both matter: the current trailing slash
is deliberate — its comment says it stops `my-tests/fixtures-backup/`
over-matching — and a bare "both components present anywhere" test would refuse
any `--packs-dir` under a checkout at `~/tests/…`. Include a negative case for
the wrong order.

While in this file, sweep `packages/agentbundle/agentbundle/**` for other
substring-shaped path guards over `tests`, `fixtures`, or `build`, and record the
result (AC12). Also record the AC13 decision on `self_host_windows.py` — a test
runner that ships in every artifact and points at a tree they do not contain.

Note the guard goes *half*-dead, not dead: `packages/agentbundle/tests/fixtures/`
keeps matching. That is precisely why nothing would surface it.

### T3 — The artifact gate

- **Implements:** AC3, AC8 (Testing Strategy: TDD)
- **Depends on:** T1

**Tests:**

- Construct a wheel known to contain a test entry (copy the real one, inject a
  file with `zipfile`), point the script at it, assert non-zero exit and the
  offending path on stderr.
- Point it at the post-T1 real wheel, assert zero exit.
- Assert it handles both `.whl` and `.tar.gz` without a third-party import.

**Approach:**

`tools/check-artifact-contents.py`, pure stdlib, ~30 lines. Absence assertion
only; the presence half arrives with the carve-out spec.

**The `_data/catalogue-scaffold/**` exemption is written into the gate here, not
later.** Scaffold content is inert template material that ships in the wheel by
design (`pyproject.toml:41`). Without the exemption, the carve-out spec's scaffold
test template turns this already-released gate red on a correct artifact. Pin it
with a TDD case: a test-shaped path under `_data/catalogue-scaffold/` does not
fail the gate; the same path anywhere else does.

Do not reach for `check-wheel-contents` or `pydistcheck`. Both were tested
against the real artifacts and rejected: the former's test-name check applies at
the library toplevel and never fires on a nested tree; the latter's
`--expected-directories` form silently passes on wheels, because setuptools
wheels carry no directory entries. Transcripts:
`docs/rfc/0082-notes/enforcement-tool-trials.md`.

### T4 — The vendored-payload unit test and the `_collect_dir_bytes` exclusions

- **Implements:** AC4, AC5 (Testing Strategy: TDD)
- **Depends on:** T1

**Tests:**

- A failing test first: assert the vendored engine payload contains no test
  content. Against today's unfiltered `_collect_dir_bytes` this fails.
- Assert the `packs/catalogue-curation/` vendored copy carries no pack tests.
- Assert the **packs** call site still carries tests — ADR-0071 wants catalogue
  archives to carry them, and this is the regression that a careless fix causes.
- Zipapp, AC4 first half: build one and assert zero engine test entries.
- Zipapp, AC4 second half: build from a synthetic tree containing
  `_data/catalogue-scaffold/x/tests/test_t.py` and assert the file is *retained*.
  This is the case that fails while `"tests"` remains in `ignore_patterns`, and
  it is why the pattern is removed rather than narrowed.

**Approach:**

`initialise_self_hosted.py`'s `_collect_dir_bytes` has four callers. Add the
exclusion **at the two vendored call sites** (`:830` engine, `:839`
catalogue-curation), not inside the routine. The other two — the adopter's
selected packs (unconditional) and shared guides (conditional on
`--guides selected`) — must keep copying tests.

Exclude by explicit relative path, not by a name-anywhere pattern, so the
exclusion cannot over-match an adopter's content.

Also **remove** `"tests"` from `tools/build_zipapp.py`'s `ignore_patterns`. The
builder copies `packages/agentbundle/agentbundle` only, so after the move no
engine test tree is inside that root and the pattern protects nothing. It cannot
be narrowed to the relocated tree — `shutil.ignore_patterns` matches basenames,
not paths, and the tree is outside the copy root. Leaving it in is actively
dangerous: it still matches `tests` at any depth, so the carve-out's scaffold
test template would be stripped and `catalogue init` would abort on manifest
verification.

### T5 — CI wiring

- **Implements:** AC9, AC11 (Testing Strategy: goal-based)
- **Depends on:** T2, T3, T4

**Tests:**

- `make ci` green.
- A PR touching only `tools/check-artifact-contents.py` runs the gate — verified
  by reading the resolved `pull_request.paths` filter, since it cannot be proven
  locally.

**Approach:**

Wire the gate into `release-agentbundle.yml` immediately after "Build wheel +
sdist". That job already runs on pull requests touching
`packages/agentbundle/**` and its build step carries no tag-only condition, so
the gate inherits PR-time coverage with no new trigger.

Add the gate script's own path to that workflow's `pull_request.paths`, which
today lists only `packages/agentbundle/**` and the workflow file — without it, a
PR changing only the gate never runs it.

### T6 — Release

- **Implements:** the release itself; every AC is closed by T1–T5 (Testing
  Strategy: goal-based)
- **Depends on:** T1, T2, T3, T4, T5

**Tests:**

- Tag-time gates pass, including the full suite from its new location.
- The published wheel contains no test entries — a re-check of AC3 against the
  artifact that actually ships, not a substitute for T3's gate.

**Approach:**

One version bump for the whole changeset, cut last. Bump both
`pyproject.toml` and `version.py`'s `CLI_VERSION`; the release workflow refuses a
mismatch at tag time.

## Risks

- **A missed path anchor leaves a module uncollected rather than failing.** A
  green suite with fewer tests looks like success. Mitigated by recording the
  passing count before T1 and comparing after.
- **The guard rewrite is the only semantic change and it fails open.** Mitigated
  by TDD ordering, and by replacing the hardcoded-literal assertion that lets it
  pass while broken.
- **`_collect_dir_bytes`'s shared routine invites a fix in the wrong place.** An
  exclusion inside the routine strips tests from the adopter's own catalogue and
  breaks ADR-0071. Mitigated by an explicit test on the packs call site.
- **`build-check.yml` carries most of the references.** A partial edit there
  reddens CI in a way that looks unrelated to the move.

## Changelog

- **2026-08-08** — Initial plan, from RFC-0082 as Accepted and ADR-0075. The
  sdist `MANIFEST.in` graft was moved out of this plan and into the carve-out
  spec: grafting before the engine suite is self-contained would ship a
  redistributor catalogue assertions that cannot run from an sdist, reproducing
  the defect the RFC exists to end.
