# Plan: engine export boundary

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is a `git mv` wearing a much larger coat. Moving
`packages/agentbundle/agentbundle/build/tests/` to
`packages/agentbundle/tests/build_pipeline/` is one command; making the repository still
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

- Build a wheel and a zipapp from a clean copy; open both with `zipfile` and
  confirm each carries zero engine test entries (the wheel was 45 of 184). The
  sdist is not inspected — this spec asserts nothing about it.
- `pip install -e packages/agentbundle` into a throwaway venv; confirm the
  console script runs and `agentbundle.build.tests` no longer resolves.

## Design (LLD)

`Shape: service`. Two sub-sections earn their place; the rest are pruned.

### Interfaces & contracts

Traces to AC3, AC4, AC5, AC8, AC8b. The enforcement surface is a single stdlib
script, `tools/check-artifact-contents.py`, whose contract is: given a built
`.whl` or `.pyz` path, exit non-zero if it contains any entry matching a test
path outside `_data/catalogue-scaffold/`. It takes the artifact path as
`argv[1]`; both formats are zip archives, so one `zipfile` reader covers them and
no `tarfile` arm is written. It prints offending entries to stderr.

It asserts **absence only**. The sdist is out of its scope entirely here: that
surface's rule inverts to presence when the carve-out lands its graft, so the
script grows a `tarfile` arm and a second mode then rather than being written
speculatively now — and, critically, must not assert absence on the sdist in the
meantime or it would reject the carve-out's correct artifact.

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

- **Implements:** AC1, AC2, AC6, AC10, AC14 (Testing Strategy: goal-based,
  integration surface)
- **Depends on:** none

**Tests:**

- Before: record the passing test count of `pytest tests/ agentbundle/build/tests/`.
- After: `python -m pytest tests/ -q` from `packages/agentbundle` passes with the
  same count. A drop means a module stopped being collected.
- No operative reference to the old path survives. The sweep must exclude the
  historical set (`docs/**`, `docs/product/changelog.md`, the package
  `CHANGELOG.md`) **inside the command**, not in a comment beside it — an earlier
  draft stated the exclusions in prose and the command was permanently red as a
  result. Write it, run it, and keep the invocation that actually passes; it is
  not specified here because nothing had executed it.
- A second sweep for composed fragments — `"tests" / "fixtures"` built from
  parts — returns nothing operative.
- Editable-install regression (AC6): `pip install -e packages/agentbundle` into a
  throwaway venv exits 0; `import agentbundle` and `import agentbundle.build`
  resolve; the console script reports the version from `pyproject.toml`; and
  `import agentbundle.build.tests` raises `ModuleNotFoundError`.

**Approach:**

`git mv packages/agentbundle/agentbundle/build/tests packages/agentbundle/tests/build`,
keeping its `__init__.py`.

**The moved suite inherits a fixture it does not have today.**
`packages/agentbundle/tests/conftest.py:26-30` defines an autouse
`_isolate_user_config_dir` that redirects `HOME`, `XDG_CONFIG_HOME`, `APPDATA`,
and `USERPROFILE` for everything under that tree. The build modules currently sit
outside its scope and gain it on move — including ones that spawn subprocesses
with `cwd=REPO_ROOT`. Compare passing counts **per module**, not just in
aggregate: an aggregate match can hide one module losing tests while another
gains them. `tests/unit/` and `tests/integration/` both have one,
and the marker is not what puts the tree in the wheel — PEP 420 discovery is.
Dropping it would make the new sibling import as top-level names while its
siblings import as `tests.unit.*`, reintroducing basename-collision exposure.

Path anchors, three idioms:

- `parents[5]` → `parents[4]` in 35 modules (repo-root anchor).
- One chained `.parent.parent.parent.parent` in
  `tests/build_pipeline/test_lint_packs.py:71` — same correction, and a `parents[N]`
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
`test_self_host_fixture_guard.py:74`.

Repoint `:74` to the **relative** `"tests/fixtures/packs"`. That value matches
the old substring guard *and* the new component guard, so T1 ends green on its
own without waiting for T2 — and it still exercises the `resolve()`-relative
input shape the surrounding comment says the pure-helper tests bypass.

Do **not** touch that module's `_FIXTURE_DIR`. It points at
`packages/agentbundle/tests/fixtures/`, a tree this change does not move; it is
not stale, it matches under both guards, and repointing it would delete the
coverage T2 depends on.

`packages/AGENTS.md` § Test conventions also changes, and the literal sweep will
never surface it: it says the test roots are `tests/unit/` and
`tests/integration/`, which this task falsifies by creating a third. Land only
that correction — RFC-0082's full four-owner rewrite belongs to the carve-out
spec.

One more file is live, not historical: `docs/specs/catalogue-test-carve-out/`
(spec and plan) is a Draft sibling carrying four `tests/build_pipeline/` (formerly `agentbundle/build/tests/`) references that
this change invalidates. It is carved out of AC10's untouched list and updated
here.

**Three of these are removals, not rewrites.** `bandit.yaml:23`'s
`*/build/tests/*` entry goes dead and its `*/tests/*` sibling at `:22` already
covers the new path. The root `pyproject.toml` mypy `exclude` falls outside
`files = [...]` once the tree moves, so it is deleted rather than repointed.
And `tools/lint-build.py:123`'s composed fixture path goes dead with them.

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
- `_FIXTURE_DIR = Path("/repo/packages/agentbundle/tests/fixtures/packs")` drives
  four of the six existing tests and is left exactly as it is. Its synthetic
  `/repo/…` prefix is correct: the guard matches path *components*, never
  repository containment, so a synthetic absolute path exercises it properly.
  This is why AC7 carries no repo-root requirement.
- Add the case this task exists for: the **relocated** shape
  `…/tests/build_pipeline/fixtures/packs`, which the old substring guard misses and the
  new component guard must catch. It fails before the rewrite — that is the red.
- Keep a case for `packages/agentbundle/tests/fixtures/`, which still matches
  today and must keep matching.

**Approach:**

`build/self_host.py:1611` reads `if "tests/fixtures/" in packs_dir.as_posix()`.
After the move the path is `…/tests/build_pipeline/fixtures/`, where `tests` and
`fixtures` are no longer adjacent, so the substring is absent and the guard fails
open — the command would overwrite the working tree with fixture data.

Rewrite it to test `packs_dir.parts` for a `tests` component followed by a
`fixtures` component. **The signature does not change** — no `repo_root`
parameter, no new argument, so the four direct call sites are untouched.

An earlier draft of this spec required the match to be "within the repository
tree", which the helper cannot express without a signature change. It was also
unnecessary: the invariant the current trailing slash protects is
`my-tests/fixtures-backup/`, and component matching already handles it —
`my-tests` is not the component `tests`, and `fixtures-backup` is not `fixtures`.
Over-matching a checkout under `~/tests/…/fixtures/…` is acceptable: that is a
directory literally shaped like the thing being guarded.

Include a negative case for the components in the wrong order.

While in this file, sweep `packages/agentbundle/agentbundle/**` for other
substring-shaped path guards over `tests`, `fixtures`, or `build`. Write the
result to `docs/specs/engine-export-boundary/notes/guard-sweep.md` (the `notes/`
directory does not exist yet), naming each file swept and each guard found.

Record the AC13 decision in the same note: `self_host_windows.py` **stays**, and
its invocation paths are updated in place by T1. Relocating it would re-touch
every file T1 has just swept, and its ownership is the carve-out spec's question,
not this one's.

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
- Assert it handles both `.whl` and `.pyz` without a third-party import — both
  are zip archives, so this is one reader, not two.
- Assert a test-shaped path under `_data/catalogue-scaffold/` does **not** fail
  the gate, and the same path anywhere else does. This is the exemption that
  keeps the carve-out's scaffold template from turning an already-released gate
  red.

**Approach:**

`tools/check-artifact-contents.py`, pure stdlib, ~30 lines. Absence assertion
only; the presence half arrives with the carve-out spec.

Its tests live in `tools/test_check_artifact_contents.py`, and T5 adds that file
to the `Makefile`'s enumerated `tools/` pytest line. The list is curated by hand —
`tools/test-all.py` says so in its own docstring — so an unlisted test file runs
nowhere and would let AC8 and AC11 pass without ever executing.

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
- Assert **both** non-vendored call sites still carry tests: the packs copy, and
  the guides copy under `--guides selected`. A routine-level or default-on
  exclusion breaks the guides path with nothing red — ADR-0071 wants catalogue
  archives to carry tests, and that is the regression a careless fix causes.
- Zipapp, AC4 first half: build one and assert zero engine test entries.
- Zipapp, AC4 second half: `monkeypatch.chdir` into a temporary directory laid
  out as `packages/agentbundle/agentbundle/_data/catalogue-scaffold/x/tests/test_t.py`,
  run the builder, and assert the file is *retained*. Chdir rather than a
  `--source` flag: `build_zipapp.py:29` hardcodes a cwd-relative source and
  `main()` takes only `<output_dir>`, and adding a flag for one caller is the
  thing `AGENTS.md` § Keeping changes minimal forbids. This is the case that
  fails while `"tests"` remains in `ignore_patterns`.

**Approach:**

The vendored-payload test is appended to
`packages/agentbundle/tests/unit/test_catalogue_tooling_self_hosted_init.py`,
which already covers this module.

`initialise_self_hosted.py`'s `_collect_dir_bytes` has four callers and takes no
exclusion parameter today. Give it one — `exclude: tuple[str, ...] = ()`,
defaulting to empty — and pass it **only** at the two vendored call sites
(`:830` engine, `:839` catalogue-curation). The empty default is what keeps this
a call-site change rather than a routine-level one.

The engine copy collects `cfg.source / "packages" / "agentbundle"`, so after T1
the relocated suite sits directly under the vendored root — and so does the root
`conftest.py`. Both are test content under AC1's definition, so both are excluded.
The curation copy (`:839`) excludes its own `tests/` tree.

Exclusion values are stated as intent, not as literals to paste: settle them by
running the T4 test against a synthetic source that carries a `tests/` tree, a
root `conftest.py`, and content that must survive.

The other two callers are the adopter's own catalogue — selected packs
(unconditional) and shared guides (conditional on `--guides selected`) — and
both must keep copying tests.

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

- **Implements:** AC5b, AC8b, AC9, AC11 (Testing Strategy: goal-based)
- **Depends on:** T2, T3, T4

**Tests:**

- `make ci` green.
- A PR touching only `tools/check-artifact-contents.py` runs the gate — asserted
  mechanically by parsing `.github/workflows/release-agentbundle.yml` and
  checking the path appears in `on.pull_request.paths`. It is static YAML; a
  human read is not the right instrument.

**Approach:**

Wire the gate into `release-agentbundle.yml` immediately after "Build wheel +
sdist". That job already runs on pull requests touching
`packages/agentbundle/**` and its build step carries no tag-only condition, so
the gate inherits PR-time coverage with no new trigger.

**The zipapp has to be built there too, with an argument, and not into `dist/`.**
`python -m build` produces a wheel and an sdist; the zipapp comes only from
`make zipapp`, which no workflow invokes. `tools/build_zipapp.py` requires
`<output_dir>` and exits 1 without it, so the bare invocation fails before the
gate runs. Use a scratch directory *outside* `packages/agentbundle/dist/` —
`twine check packages/agentbundle/dist/*` runs at `:88` and the publish job
uploads that directory to PyPI, so a stray `.pyz` there reddens the check and
contaminates the release. `release-agentbundle.yml` is `WORKFLOW_SCOPE`-exempt
in `tools/lint-ci-parity.py:106` ("Release workflow, not a gate"), so these step
additions need no `STEP_DISPOSITION` entry — unlike a `build-check.yml` change.

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

One version bump for the whole changeset, cut last. Bump both `pyproject.toml`
and `version.py`'s `CLI_VERSION`; the release workflow refuses a mismatch at tag
time.

Add a `packages/agentbundle/CHANGELOG.md` entry. `import agentbundle.build.tests`
stops resolving — a public import path removed — and no CI gate catches an
unrecorded interface change.

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

- **2026-08-08 (steer)** — Command-level mechanics demoted from specification to
  intent. Three pre-EXECUTE rounds each found the plan's literal invocations and
  exclusion tuples wrong, because they were written without running them; the
  ACs were sound throughout. The plan now states what each step must achieve and
  leaves the exact command to EXECUTE, where it can be tested. Human steer after
  the loop surfaced a plateau at 4 blockers.

- **2026-08-08** — Initial plan, from RFC-0082 as Accepted and ADR-0075. The
  sdist `MANIFEST.in` graft was moved out of this plan and into the carve-out
  spec: grafting before the engine suite is self-contained would ship a
  redistributor catalogue assertions that cannot run from an sdist, reproducing
  the defect the RFC exists to end.
