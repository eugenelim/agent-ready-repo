# Resolve-vs-surface disposition record: engine-export-boundary

Opened at PLAN (2026-08-08). Closed at DECIDE. Records what the loop resolved on
its own authority versus what it surfaced to the human, per the work-loop
self-coverage gate.

## Assumption trio

**Files I will touch**

- `packages/agentbundle/agentbundle/build/tests/**` → `packages/agentbundle/tests/build_pipeline/**` (the move)
- Path anchors inside the moved suite: 35 `parents[5]`, one chained `.parent` walk, two `parents[2]` package reaches
- Two in-suite literals: `test_end_to_end_build.py:5` and
  `test_self_host_fixture_guard.py:74` (its `_FIXTURE_DIR` is **not** touched)
- Operative references (enumerated canonically in `plan.md` T1; three are
  removals, not rewrites): `build-check.yml`, `catalogue-tooling-ci-gates.yml`, `self_host_windows.py`, both `pyproject.toml`, `Makefile`, `release-agentbundle.yml`, `bandit.yaml`, `packs/AGENTS.local.md`, `test_install_snapshot.py`
- One composed-path reference: `tools/lint-build.py:123`
- `agentbundle/build/self_host.py` (the destructive-write guard) + its covering test
- `tools/build_zipapp.py` (remove `"tests"` from `ignore_patterns`)
- `agentbundle/catalogue_tooling/initialise_self_hosted.py` (vendored call-site exclusions)
- New: `tools/check-artifact-contents.py`, plus its test
- `docs/specs/catalogue-test-carve-out/{spec,plan}.md` — live sibling, four invalidated references
- New: `docs/specs/engine-export-boundary/notes/guard-sweep.md`
- Ride-along: `docs/adr/README.md` (missing ADR-0074 row) — **user-authorized, not carve-out-justified**: `docs/adr/` holds no file this change edits and the gap was not orphaned by this work, so it fails the bundled-fixes gates. It lands because the human explicitly asked for it, recorded as such rather than dressed up as a same-area ride-along.

**What tests demonstrate done**

The engine suite green from its new location with the same passing count; a built
wheel and zipapp opened and shown to contain zero engine test entries; a unit
test that fails against today's unfiltered `_collect_dir_bytes`; a guard test
that drives the real on-disk path and fails against the un-rewritten guard; an
editable install into a throwaway venv where `agentbundle.build.tests` no longer
resolves.

**What I am not changing**

No `MANIFEST.in`, no sdist graft — deferred to the carve-out spec by design. No
new top-level `tests/` directory. No `namespaces = false`. No pack content, no
`.apm/` trees, no ADR-0071 destinations. No test assertions, with one
pre-authorised exception: `test_self_host_fixture_guard.py:74`'s hardcoded path
literal. Its `_FIXTURE_DIR` is explicitly out of scope — it points at a tree this
change does not move, and repointing it would delete the coverage T2 needs. No version bump until the release task.

## Declined-pattern register

- **A `tools/` helper module shared between the new gate script and the vendored-payload test.** Declined: two callers, ~30 lines each, and the shared surface would be a single `is_test_path()` predicate. Inline it in both; extract when a third caller appears.
- **Making `check-artifact-contents.py` handle the sdist presence assertion now.** Declined: the spec explicitly defers it, and a gate asserting a property the tree does not yet have is a gate that ships red.
- **Rewriting the two `parents[2]` package reaches to use `importlib.resources`.** Declined: correct, but it changes how those tests resolve package data, which is a behaviour change smuggled into a relocation. Explicit path resolution keeps the diff honest.
- **Flipping `namespaces = false` while in `pyproject.toml`.** Declined and listed under the spec's *Ask first*: it would work, and it changes discovery semantics for the whole package — not a ride-along.
- **Fixing `install-marker.py`'s non-importable path while touching packaging.** Declined: recorded as a backlog slug, out of the spec's scope, and would muddy a release-blocking diff.
- **Adding a `tests/` glob to the `Makefile` so future suites are picked up automatically.** Declined: speculative generality. The `Makefile` enumerates by design, and the carve-out spec owns the new tree's runner.

## Domain-grounding check

Not required. The build rests on no ungrounded domain claim: the packaging
behaviour it depends on (PEP 420 namespace discovery, `shutil.ignore_patterns`
basename matching, setuptools wheel/sdist composition) was measured directly
against the real artifacts during RFC-0082 and is recorded in
`docs/rfc/0082-notes/enforcement-tool-trials.md`.

## Resolved by the loop

Three pre-EXECUTE adversarial rounds ran before any code. Resolved on the loop's
own authority, with evidence:

- **The guard's containment requirement was dropped as unimplementable** —
  `_refuse_fixture_packs_dir` takes no repo root, and adding one is an *Ask
  first* signature change. It was also unnecessary: component matching already
  preserves the `my-tests/fixtures-backup/` invariant the original comment names.
- **AC13 decided against RFC-0082's recommended default** —
  `self_host_windows.py` stays. Relocating it would re-touch every file T1 sweeps,
  and its ownership is the carve-out spec's question.
- **The sdist was removed from this spec's gate entirely** — asserting absence
  there would reject the carve-out's correct artifact once its graft lands.
- **`_FIXTURE_DIR` was reclassified from "repoint" to "do not touch"** after the
  reviewer showed it targets an unmoved tree.

## Surfaced to the human

**Round 3 plateaued: 8 blockers → 4 → 4.** Findings stopped shrinking, which is
the work-loop's termination condition #3 — spot-fixing without addressing the
root cause. Surfaced rather than grinding a fourth round.

**Root cause:** the plan specifies EXECUTE-time mechanics in prose — exact `grep`
invocations, exact exclusion tuples, exact `Makefile` line numbers — written
without running them. Each round the reviewer runs them and finds them wrong.
Two verified this round: T1's sweep command is permanently red as written
(it matches ~250 historical occurrences the parenthetical excludes but the
command does not), and the pinned `("tests/",)` engine exclusion misses
`packages/agentbundle/conftest.py`, which sits in the same vendored root.

Both are correct findings. Neither is a *contract* defect — the ACs are sound and
observable. They are implementation details being litigated at PLAN time, where
they cannot be tested.

**Recommended rung: steer.** Proceed to EXECUTE against the ACs, and let the
mechanics be settled by running them. The plan's command-level prose should be
demoted to intent, not kept as a specification nothing has executed.

