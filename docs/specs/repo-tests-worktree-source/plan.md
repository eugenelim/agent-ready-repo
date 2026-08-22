# Plan: repo-tests-worktree-source

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`. When it changes substantially (a different approach, not just
> a re-ordering), note why in the changelog at the bottom. Once it is `Done`
> and the spec is `Shipped`, the directory freezes as a unit
> (`docs/CONVENTIONS.md` § Document lifecycle).

## Approach

Four of the five deliverables are single-artifact edits; the fourth is a new
module with its own suite, and the fifth is a governance record. The ordering is
forced by one fact: the change to pytest's resolution has to be *measured*, and a
measurement needs a baseline taken before anything else moves. So the baseline
runs first, the configuration change second, the after-run third, and only then
does the interpretation — including any correction to `workspace.toml` — get
written.

The riskiest part is not the configuration line; it is its reach. The repository
root is already pytest's configfile for every root-relative invocation, so the
declared `pythonpath` lands in every invocation of the `test-unleased` recipe
rather than the two suites the brief named. That is why the baseline covers
`packs/**` and `packages/**` as well as `tools/ tests/`, and why the top-level
name collision is measured and recorded in the spec's Assumption 7.

The guard is deliberately not a report. T2 removes the *need* to install and T3
removes the *instruction* to, but neither prevents the act — and the harm the
brief set out to stop is an act, not a state of skew. So the last task refuses
the one install shape that actually makes worktrees clobber each other, and does
it by reading recorded metadata rather than importing the packages whose install
shape it is describing.

## Constraints

Each of these is stated once, in `spec.md`, and referenced here by criterion
rather than restated, so the two documents cannot drift apart:

- The declared `pythonpath` value and why `"."` is load-bearing — AC1.
- The invocation inventory and the recipe that holds it — AC2.
- The `workspace.toml` correction that is permitted, and the removal that is not
  — AC2 and Boundaries § Never do.
- The single condition the guard refuses, and everything it must stay silent on
  — AC5, AC6.
- The frozen-artifact rule sending the venv decision to an ADR — Boundaries
  § Never do, and AC8.
- The `build_gate_chain.py` append-versus-prepend tension — Boundaries
  § Ask first.
- The blessed-helper non-use and its circularity reason — Assumption 4.
- The top-level name collision, measured — Assumption 7.
- No `pip` command runs at any point — Boundaries § Never do.

## Construction tests

**Integration tests:** the guard is exercised end to end twice — against a
synthesised, discoverable editable record pointing outside this worktree (must
exit 1) and against this worktree's real installs (must exit 0). Neither is a
fake: the first is discovered through `importlib.metadata` on a real path.

**Manual verification:** run `make lint-editable-install` and record its exit
code. Run `python3 -m pytest tools/test_editable_install_guard.py -q` on its own
line, for the reason AC9 gives: the module-level `sys.path.insert` that reaches
`tools/repo`, which is why the `test_worktree_*` family gets its own lines too.

## Tasks

### T1: baseline the suites

**Depends on:** none

Run the `tools/ tests/` union and each of the 37 `packs/**` and 2 `packages/**`
suites as its own invocation, in the no-`PYTHONPATH` frame. Record the failure
set verbatim.

**Measured** at `6452e255`, clean tree, 2026-08-21. `tools/ tests/`:
`1 failed, 1575 passed, 8 skipped, 101 subtests passed in 920.93s`. The 39
package and pack suites: 39 ran, 1 failed. The combined baseline failure set is
exactly:

```
tools/test_marketplace_envelope_parity.py::test_resolved_layer_fails_loudly_when_the_package_is_unimportable
packs/atlassian/tests/skills/jira/test_intake_policy.py::test_guarded_write_policy_sends_once_without_retry
```

The second is not in `workspace.toml`'s register and is **frame-dependent**: it
fails with no `PYTHONPATH` and passes with `make`'s. Simulating AC1's declared
entries makes it pass, so T2 is expected to resolve it and the set should
shrink to one. Because it is in no register entry, AC2's fourth disposition
applies: record the shrink in the PR's measurement, edit no `workspace.toml`
entry. The remaining failure persists for the reason AC2 records.

Coverage note: the Makefile runs the `tools/` and root `tests/` files across 16
separate lines, and this baseline runs their union in one process. The per-line
split exists for basename collisions; the union is used here only because before
and after are then compared under identical framing. `make test` at the finish
gate exercises the per-line framing.

**That framing turned out to matter, and is worth recording.** Two tests named by
the `pre-existing-roster-catalogue-index-and-okf-release-metadata` register entry
— `test_okf_catalogue_discovery.py::test_release_metadata_moves_together_for_okf_catalogue_discovery`
and `test_catalogue_wave4_live_contracts.py::test_live_catalogue_indexes_every_manifest_pack`
— **fail in isolation at the base commit** but **passed in the whole-suite
baseline at that same commit**. So the whole-suite result is order-dependent:
something earlier in `pytest tools/ tests/` leaves the worktree on `sys.path`.
The source was not identified — it is a pre-existing property of the suite, not
of this change, and running the obvious candidates (`test_marketplace_envelope_parity`,
`test_okf_pre_pr`, `test_workspace_status_projection`) before them did not
reproduce it.

Recorded rather than diagnosed, because the consequence stands on its own: a
green `make test` can mask a resolution failure that `pytest <file>` exposes.
Both tests do now pass in isolation after this change, and independently of the
untracked `*.egg-info` — verified by removing it.

The runner puts no pipe around the gate, because a piped `$?` reports the
filter's status rather than pytest's; the runner was proven against a known-fail
command before the 39 runs were trusted.

**Tests:** no stub (measurement). Done when: the combined failure set is
recorded.

### T2: declare the pytest pythonpath

**Depends on:** T1

Add `[tool.pytest.ini_options]` with AC1's three-entry `pythonpath` to the root
`pyproject.toml`. Re-run both baseline legs and diff the failure sets, then act
on AC2's three branches. Run the two package suites to confirm AC3's observable.

**Measured** 2026-08-22, same no-`PYTHONPATH` frame as T1.

| leg | before | after |
| --- | --- | --- |
| `tools/ tests/` union | 1 failed, 1575 passed, 8 skipped | 1 failed, **1597** passed, 8 skipped |
| 37 `packs/**` + 2 `packages/**` | 1 failed | **0 failed** |

Failure **set** shrank from two to one:

```
before: {test_resolved_layer_fails_loudly_when_the_package_is_unimportable,
         test_guarded_write_policy_sends_once_without_retry}
after:  {test_resolved_layer_fails_loudly_when_the_package_is_unimportable}
```

AC2's "fewer failures" branch, and no new failures. The `+22` passed accounts
exactly for this change's own new test file, so no other test changed state —
which is the check that a bare count would have hidden.

`test_guarded_write_policy_sends_once_without_retry` is in no register entry, so
AC2's fourth disposition applies: recorded here and in the PR, no
`workspace.toml` edit. The register entry that *does* exist was re-described
per AC2 without removing any test name; the slug sets of all three
`workspace.toml` arrays are byte-identical to the base, so the edit is
comment-only.

Both AC1 observables pass: `pytest --collect-only tools/test_managed_child.py`
under the bare console script went from `ModuleNotFoundError: No module named
'tools'` to 16 tests collected, and a test collected by that same invocation
reports both packages' `__file__` inside this worktree.

**Tests:** goal-based. Done when: both AC1 observables pass, and the before and
after failure sets are recorded for the `tools/ tests/` union, the 37 `packs/**`
suites, and the 2 `packages/**` suites.

### T3: correct the install instruction

**Depends on:** T2

Rewrite the `Makefile` comment above the static-analysis and test targets to
AC4's content, retaining every requirement AC4 enumerates — dropping the
`credbroker[crypto]` extras would silently convert real assertions into skips —
and naming why an install stays legitimate. Sweep the repository for the same
guidance and either correct it or record why an occurrence is a different
concern: the CI workflows install deliberately into a fresh runner, and the
adopter-facing "Route 4: Local clone" documentation installs to obtain the
console script and ADR-0036's editable catalogue detection. Neither is this
instruction. Name `packages/agentbundle/conftest.py` in the sweep result.

The rewrite spans **two** comments, not one: `Makefile:322-324` carries the
install instruction, and `Makefile:334` carries "Dev-time Python deps beyond
agentbundle: jsonschema>=4.0, PyYAML" — whose "beyond agentbundle" presumes the
same install and so belongs to the same correction.

**Tests:** goal-based. Done when

```
! sed -n '321,336p' Makefile | grep -qE 'pip install -e .*(agentbundle|credbroker)'
```

succeeds, every requirement AC4 lists is still named within that span, and the
sweep result is recorded. The check is scoped to the span because the same
pattern legitimately matches the CI workflows and the adopter-facing install
route, which T3 deliberately leaves alone. Bounds are re-derived before the
check runs, since editing the block moves them.

**Sweep result** (2026-08-22). 44 files mention `pip install -e` against
`agentbundle` or `credbroker`. Every one outside the corrected span is a
different concern, by class:

| class | why it stays |
| --- | --- |
| `.github/workflows/**` | installs deliberately into a fresh CI runner, where nothing is on `PYTHONPATH` |
| adopter guides, `docs-site/`, package `README`s | teach an adopter to obtain the console script and ADR-0036 editable detection |
| shipped `docs/specs/**`, `docs/rfc/**` | frozen bodies (`docs/CONVENTIONS.md` § Document lifecycle) |
| tests, fixtures, `tools/lint-ci-parity.py` | assert on install strings; they are not guidance |
| `packages/agentbundle/conftest.py` | sets the `PYTHONPATH` *environment variable* so subprocess children resolve the package — the one thing AC1's in-process change deliberately does not do, so it is still required and is not redundant |

The decisive check: a grep for install guidance framed as a precondition for
running the tests or gates (`to run` / `before running` / `in order to run` near
`test`/`gate`/`make`) returns zero hits outside the corrected span. The
`Makefile` comment was the only contributor-facing instance.

### T4: the editable-install guard

**Depends on:** T2

Add `tools/repo/editable_install_guard.py`, standard-library-only. It reads each
package's PEP 610 `direct_url.json` — never importing either package — and exits
non-zero for exactly one condition: an editable install whose recorded source is
not this worktree. Everything else is silent or reported-without-failing, per
AC6. A failure names the repair. Wire it as `make lint-editable-install` and make
`test-unleased` depend on it, and register
`tools/test_editable_install_guard.py` on its own `test-unleased` line, per AC9.

**Why a guard rather than a report.** The original brief's goal was to stop
editable installs clobbering each other and the shared interpreter. T2 removes
the *need* to install and T3 removes the *instruction* to, but neither prevents
the act, and a report that merely describes version skew prevents nothing — it
diagnoses a symptom of a state that may never occur. The guard refuses the one
state that actually causes the harm, and it can do so without a false alarm on
the operator's deliberate wheel install, because "editable, pointing elsewhere"
is never a legitimate setup.

**Tests:** TDD, `stub: true`. `tools/test_editable_install_guard.py` covers every
AC6 silent case (plain wheel, absent, editable-pointing-here,
editable-pointing-into-here, non-editable direct URL), the AC5 failing case, the
sibling-prefix case a string-prefix containment test would miss, the
report-but-do-not-fail cases (unparseable record, non-local URL host,
undeterminable root), and the real-repository happy path. Plus two end-to-end
proofs: a synthesised discoverable editable record pointing outside the worktree
exits 1, and this worktree's real installs exit 0.

### T5: record the declined venv

**Depends on:** T3

Write the ADR from `.claude/skills/new-adr/assets/adr.md` with
`Status: Accepted`, allocating the ordinal late via
`python3 .claude/skills/new-adr/scripts/next-ordinal.py docs/adr` because a peer
session may take the next number, and add its `docs/adr/README.md` row. It
depends on T3 because its central claim — that T2 and T3 remove the need
for the install the venv was meant to isolate — is not established until that
instruction is actually corrected.

Content: the venv was proposed to stop a `pip install -e` corrupting an
environment shared by nine worktrees, and T2–T3 remove the need for that
install, so the venv would isolate a write that no longer happens. `python3 -m
venv` fails in `ensurepip` under the supervised worker's sandbox everywhere
tried, while `--without-pip` succeeds, so directory creation is not the problem.
The root cause is pip's `install` building a network session even under
`--no-index`, materialising certifi's CA bundle as a temporary file carrying the
macOS `com.apple.provenance` extended attribute, which that sandbox denies read
and unlink on with `EPERM` — a policy denial, not a file mode, so no allowlist,
path, or permission change helps. The residue is roughly 265KB of undeletable
litter per attempt the worker cannot clean up itself. And the latent trap of
AC11: the in-use test resolves distributions from the interpreter running the
cleaner, so it could never protect a per-worktree environment.

State the frame on those measurements, because it is what localises the cause:
they were taken under the supervised worker's sandbox, and `python3 -m venv`
succeeds under this session's sandbox on the same machine and interpreter.

**Tests:** goal-based. Done when: the ADR exists with a sequential ordinal and
`Status: Accepted`, `docs/adr/README.md` carries its row, `docs/specs/README.md`
carries this spec's row (AC12), and both
`python3 .claude/skills/work-loop/scripts/lint-spec-status.py --root .` and
`python3 .claude/skills/work-loop/scripts/lint-traceability.py --root .` pass.

## Changelog

- Initial plan.
- Revised after the round-1 adversarial and secure-design reviews. Three changes
  were substantive. The declared `pythonpath` gained `"."`, without which the bare
  console script does not collect at all — the change did not work as first
  specified. The claim that adding the `[tool.pytest.ini_options]` table creates
  the rootdir and configfile was struck as false: pytest 9.0.3 already treats the
  root `pyproject.toml` as both, so the measured blast radius is every
  `test-unleased` invocation and the baseline widened accordingly. And the
  diagnostic's discriminator moved from metadata *location* to version
  *disagreement*, because keying on location made it fire permanently on a
  correct local setup.
- Revised again after round 2, which attributed most of its findings to the
  round-1 fixes rather than to the original artifact — the signal that the
  artifact had outgrown the task. Scope was narrowed on the owner's decision:
  module drift is now left to the shipped `worktree_hygiene.py scan`, which
  already reports it, so the diagnostic carries only the version comparison. That
  dissolved the top-level-name allowlist criterion, whose stated allowlist could
  not fail on the collision it existed to catch, and the duplicate-probe overlap.
  Also corrected: entries resolve against rootdir rather than the working
  directory, because that is what pytest does and the alternative inverts the
  judgement from a subdirectory; a per-run nonce was added because a sentinel
  alone is forgeable by the untrusted `site-packages` copy; the confined value is
  now required to be the value passed to the child; redaction became mechanical
  rather than a transcription-time obligation; and the `RuntimeError` justification
  was corrected to `OSError` `ELOOP`, measured on 3.13.13.
- Revised after round 3, which **withdrew the round-2 narrowing above**. The
  claim that the shipped scan already reports module drift was true for only half
  the surface — `worktree_hygiene.py` does not mention `credbroker` at all, and
  its criterion is titled "scan measures *agentbundle* import resolution". Worse,
  the version-only discriminator would not have caught the failures it was
  justified by: `tests/roster/test_okf_catalogue_discovery.py:40,53` compares a
  worktree literal against a `CLI_VERSION` imported from the resolved module, and
  in the registered failure that module came from `site-packages` and agreed with
  its own metadata. So module-location drift was restored as finding A, the
  version disagreement kept as finding B, and the delegation claim replaced with
  the accurate distinction: the two probes measure different frames, because the
  shipped one strips `PYTHONPATH` and seeds nothing while this one seeds the
  declared entries. A shadowed metadata copy was settled as context inside a
  finding, never a trigger. AC7 gained the run-scoped-versus-per-package split,
  AC8 gained the upward root-discovery walk that its own invariance clause
  requires, and the stub was rewritten twice — the first version could not have
  been made green by any conformant implementation, and four of its five cases
  passed against a do-nothing module.
- Revised after the implementation review (adversarial + secure-design +
  quality, on the diff). Six defects were real and none were visible from the
  prose:
  - **The nonce was handed to the party it distrusted.** The probe passed it as
    `sys.argv[1]` and left it there through `__import__`, so a package could read
    it, print a nonce-bearing record, and `os._exit(0)` — producing total silence
    at exit 0. Demonstrated with a fixture. Fixed by `del sys.argv[1:]` before any
    import, with the startup-code residual now stated in AC8.
  - **Two inputs made an always-exit-0 command traceback**: a `pyproject.toml`
    whose `tool.pytest` is not a table, and a non-list `metadata_copies`.
  - **A closed stdout exited 120.** `make worktree-doctor | head` broke the
    contract. The print block is now inside the guard.
  - **`Report.exit_code` was a never-assigned constant**, so 15 `assertEqual(...,
    0)` assertions were tautologies, and no test called `main()` — which is
    exactly why the BrokenPipe defect shipped. The field is gone and `main` is
    now tested, including a real subprocess for the pipe case.
  - **An incomplete probe record read as clean**: a payload omitting a package
    reported nothing about it. `_parse` now requires every package.
  - **The effective metadata version was inferred from enumeration order** in the
    parent. The child now reports what `md.version()` actually returns.
  Also corrected a false claim this plan and `workspace.toml` both carried — see
  T1's coverage note. Redaction moved from an allowlist to a denylist so it fails
  closed, and the mutation set grew to 12, all killed.
- Scope narrowed on the owner's call after the implementation review. The drift
  diagnostic was **dropped**, and a guard added in its place. The reasoning is
  worth keeping, because it was a proportionality error and not a technical one:
  the diagnostic was correct, tested, and mutation-proven, and it still prevented
  nothing. It reported a version skew — a *symptom* — while the goal was to stop
  editable installs clobbering a shared interpreter, which is an *act*. It also
  consumed most of this loop's effort and produced nearly every review finding,
  which is the signal that should have prompted the question earlier. What
  replaced it is smaller and refuses the actual harm state, and — the owner's
  other point — T3 now states what to *do* rather than only deleting what not to
  do, since removing a wrong instruction otherwise leaves a vacuum.
- Revised after a focused review of the guard, which found it **blind in the one
  invocation that registers it**: `md.distribution(name)` returns the first match
  on `sys.path`, and `Makefile:7` puts `packages/agentbundle` first, so the
  in-worktree `*.egg-info` answered instead of the real install and every verdict
  came back "regular". Measured: exit 1 unmasked, exit 0 under `make`. My own
  fire-proof had certified the unmasked frame, which is exactly how this passed.
  Discovery now considers every matching distribution and skips any whose
  metadata resolves inside the worktree. Also fixed: containment was
  case-sensitive (`os.path.normcase` is a no-op outside Windows) and would have
  false-alarmed on a case-variant path naming this same worktree; the repair text
  offered `credbroker` a console script it does not have; and the unreadable-record
  branch was partly dead because `read_text` suppresses `OSError` internally. The
  end-to-end proofs are now run with `Makefile:7`'s `PYTHONPATH` in place.
