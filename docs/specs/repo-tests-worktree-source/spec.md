# Spec: repo-tests-worktree-source

- **Status:** Shipped
- **Owner:** repository maintainers
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0036](../../adr/0036-install-source-resolves-through-trusted-precedence-chain-no-repo-source-no-cwd.md) <!-- its layer-3 editable-detection mechanism is why an install stays legitimate; AC11's ADR is an output of this spec, not a constraint on it -->
- **Shape:** mixed
- **Contract:** none <!-- the guard's exit code and stderr are a developer surface, not a published interface -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A contributor or supervised worker who runs the bare `pytest` console script
from the repository root, in a root-relative invocation governed by the root
configfile, tests this worktree's source — and can run it at all. Two things
break that today. `Makefile:7` puts both package directories on `PYTHONPATH`, so
`make` is correct, but a bare `pytest` has no such configuration and imports
whatever copy of `agentbundle` or `credbroker` is installed on the machine.
Worse, eight modules under `tools/` import repository code by package name
(`from tools.repo import ...`), which needs the repository root on `sys.path`;
`python3 -m pytest` supplies that by inserting the working directory, and the
bare console script does not — so those modules fail at collection, not at
assertion. A supervised worker that can only issue `pytest <path>` with no
environment prefix has therefore been getting a collection error on part of the
suite and a different version of the code on the rest. Success is that the bare
invocation both collects and resolves this worktree, that the instruction which
told each new session to write to a shared global environment no longer says
that, and that when the imported module and its distribution metadata disagree a
contributor gets a plain informational line explaining it instead of an
unexplainable failure.

**Scope: in-process imports under the root configfile.** pytest's `pythonpath`
option manipulates `sys.path` inside the pytest process; it never sets the
`PYTHONPATH` environment variable, so no child process of any kind is reached.
It also does not reach an invocation whose nearer configfile is a package's own
`pyproject.toml` (AC3).

## Acceptance Criteria

- [x] **AC1 — a bare `pytest` from the repository root collects and imports
  worktree source.** The root `pyproject.toml` declares
  `[tool.pytest.ini_options]` with
  `pythonpath = [".", "packages/agentbundle", "packages/credbroker"]`. The
  repository root entry is load-bearing, not decorative: without it the bare
  console script fails collection with `ModuleNotFoundError: No module named
  'tools'`. Two observables:

  1. `pytest --collect-only tools/test_managed_child.py`, as the bare console
     script with no environment prefix, collects its tests. Measured to
     discriminate: at `6452e255` it exits 2 with
     `ModuleNotFoundError: No module named 'tools'`.
  2. A test collected by that same bare invocation reports an
     `agentbundle.__file__` and a `credbroker.__file__` inside this worktree —
     read through pytest, so the declaration is what supplies them. An
     observable that prepends the entries by hand would pass before the change
     too and certify nothing.

  The mechanism is only the `sys.path` prepend. The repository root is *already*
  pytest's `configfile` and `rootdir` for a root-relative invocation — measured
  on pytest 9.0.3, which counts `pyproject.toml` for rootdir discovery whether or
  not it carries the `[tool.pytest.ini_options]` table — so adding the table
  changes no rootdir and introduces no configfile that was previously absent.
  Declared order is preserved on `sys.path`.

- [x] **AC2 — the resolution change is measured, never asserted.** Because the
  repository root is already the configfile for every root-relative invocation,
  the declared `pythonpath` reaches every `pytest` invocation in the
  `test-unleased` recipe *except* the two package-suite lines, whose nearer
  configfile AC3 covers. `test-unleased` is the recipe that holds them; `test` is
  a one-line delegation through `coordination_lease.py with-lease` and must not
  receive test lines. Baseline inventory at `6452e255`: 57 lines mentioning
  `pytest` inside the `test-unleased` recipe, of which 55 are suite invocations —
  two are `--collect-only` counters. Failure *sets* — never counts, never exit
  codes — are compared before and after across the `tools/ tests/` union and the
  37 `packs/**` and 2 `packages/**` suites, in the same no-`PYTHONPATH` frame in
  which the behaviour actually changes.

  Three outcomes, three responses. Fewer failures: keep the change and correct
  the `workspace.toml` entry that attributed them to the skew. An identical set:
  keep the change; it is a correctness fix for the bare console script whether or
  not it moves any test. New failures in
  `tools/test_marketplace_envelope_parity.py::test_resolved_layer_*` or the
  roster tests: stop and report; do not weaken them.

  A fourth disposition covers the measured case: a failure that disappears but
  was never in the register needs no `workspace.toml` edit at all, only a record
  in the PR's measurement. `test_resolved_layer_*` is expected to persist because
  `pythonpath` mutates `sys.path` only and never becomes an environment variable,
  so no child process of any kind is reached.

  The permitted `workspace.toml` correction is to re-describe an entry's cause
  against what is measured. Removing a test name from an entry is **not**
  permitted: two of the three tests named by
  `pre-existing-roster-catalogue-index-and-okf-release-metadata` are fixed by
  this change when run on their own — they compare a worktree literal against an
  imported `CLI_VERSION`, so worktree resolution is the fix — but their
  whole-suite result is order-dependent and passed even before it. They stay
  named as the record of that, and because a green `make test` can mask a
  resolution failure that a single-file run exposes.

- [x] **AC3 — the package suites are unaffected, observably.**
  `packages/agentbundle/tests/` and `packages/credbroker/` each resolve their own
  `[tool.pytest.ini_options]` as the nearer configfile, and neither declares a
  `pythonpath`, so the root declaration does not apply and those suites keep
  importing whatever is installed. The observable is that each suite's failure
  set is identical before and after the change. That residual is recorded in
  Assumption 6 and is out of scope here.

- [x] **AC4 — the local-development instruction no longer prescribes installing
  these packages, and drops no genuine requirement.** The `Makefile` comment
  above the static-analysis and test targets states that these targets need no
  install of `agentbundle` or `credbroker`, that `PYTHONPATH` and the pytest
  configuration provide both from source, and that a separately installed copy is
  legitimate and is not what these targets use. It names why an install remains
  legitimate — the `agentbundle` console script and ADR-0036's layer-3 editable
  catalogue detection — so the rewrite does not read as a discouragement. That
  legitimacy note names the *mechanism*, never the command, so it does not
  reintroduce the very instruction this criterion removes.

  It retains every requirement that is genuinely one: `ruff`, `mypy`, `pytest`,
  `tools/requirements.txt` (the linters' PyYAML and jsonschema), the
  `credbroker[crypto]` extras `cryptography` and `argon2-cffi` — which gate real
  assertions in `packages/credbroker/tests/unit/test_vault.py` and would silently
  become skips if dropped — and `tools/requirements-sast.txt` for the SAST leg.

  Equivalent guidance elsewhere is corrected in the same change or named, with
  its reason, as a different concern; `packages/agentbundle/conftest.py` is named
  explicitly, because it documents the same PYTHONPATH-versus-install question.

- [x] **AC5 — a guard refuses the state that makes worktrees clobber each other,
  and nothing else.** `tools/repo/editable_install_guard.py` exits non-zero for
  exactly one condition: an **editable** install of `agentbundle` or `credbroker`
  whose PEP 610 `direct_url.json` records a source directory that is not this
  worktree. That is the state in which this worktree's *subprocesses* import
  another checkout's code, and in which a `pip install -e` run here rewrites what
  a peer's in-flight gates resolve.

  It classifies from the recorded `direct_url.json` and never imports either
  package, because the point is to describe an install without loading code from
  it.

  **Discovery is by install location, not by `sys.path` order.** `Makefile:7`
  puts `packages/agentbundle` first on `PYTHONPATH` for every make target, so a
  first-match lookup answered with the in-worktree `*.egg-info` of Assumption 2 —
  which carries no `direct_url.json` and therefore made every verdict "regular".
  Measured: the guard was blind in exactly the invocation AC9 registers. Two
  independent mechanisms prevent it: every matching distribution is considered,
  not the first, and any whose metadata resolves inside this worktree is skipped
  as source-tree metadata rather than an install.

  Containment is component-wise against the resolved worktree root and
  **case-folded**. Component-wise because sibling worktrees share name prefixes,
  and a prefix test would call `<root>-peer` inside `<root>` and miss the only
  state the guard exists for. Case-folded because `Path.resolve()` does not
  normalise case on a case-insensitive volume and `os.path.normcase` is a no-op
  outside Windows, so a record naming `/users/...` for `/Users/...` describes
  this worktree and would otherwise be a permanent false alarm. Folding always,
  rather than probing case sensitivity, trades a missed detection on a
  case-sensitive volume for never false-alarming — the right direction given
  AC6.

- [x] **AC6 — the guard never fires on a legitimate setup.** A plain wheel
  install (no `direct_url.json`) is silent — that is the deliberate setup that
  puts the `agentbundle` console script on `PATH`, and failing on it would be a
  permanent false alarm. An absent install is silent. An editable install
  pointing at *this* worktree is silent, because it leaks nothing into a peer that
  this worktree does not already own. A direct-URL record without
  `dir_info.editable == true` is silent. An unreadable or unparseable record, a
  non-local `file://` host, and an undeterminable worktree root are each reported
  and **do not fail**: none of them is the harm state.

- [x] **AC7 — the guard names a repair, and both proofs are measured.** A failure
  states the recorded source, this worktree, why it matters, and two repairs: an
  uninstall (nothing here needs it — `python3 -m agentbundle` runs the CLI from
  source) and, if the console script is wanted, an editable install pointing at
  *this* worktree with the warning that it still rewrites global state.

  Construction tests cover every AC6 silent case and the AC5 failing case,
  including the sibling-prefix case, the case-variant path, and the
  source-tree-metadata-enumerated-first case that the shipped blocker came from.
  Each guard is mutated and its named case must fail; where two mechanisms are
  jointly sufficient, the mutation removes both, because mutating one while the
  other still covers it proves nothing.

  The guard is additionally proved end to end **in the frame that registers it**:
  a discoverable editable record pointing outside the worktree makes it exit
  non-zero with `Makefile:7`'s `PYTHONPATH` in place — the frame an earlier proof
  omitted, which is how the blindness passed unnoticed — and this worktree's real
  installs exit 0 both directly and through `make`.

- [x] **AC8 — the per-worktree virtual environment is declined on record.** An
  ADR created from the `new-adr` template, with `Status: Accepted` and a row in
  `docs/adr/README.md`, records the decision not to build one, its measured
  reasoning, and the latent trap that `worktree_hygiene`'s in-use test resolves
  distributions from the interpreter running the cleaner
  (`tools/repo/worktree_hygiene.py:862-870`, consumed at `:1161` and `:1736`), so
  it could never protect a per-worktree environment. `.venv`, `venv`, and `env`
  remain deletable `dependencies` candidates in that module's `NAMES` table
  (`:63-65`), unchanged.

- [x] **AC9 — the guard and its suite are registered where they run.**
  `make lint-editable-install` invokes the guard, and `test-unleased` depends on
  that target so the guard runs before the suites it protects.
  `tools/test_editable_install_guard.py` runs on its own line in `test-unleased`,
  matching the `test_worktree_*` family, which is deliberately covered locally and
  has no `build-check.yml` step. `docs/specs/README.md` carries a row for this
  spec.

## Boundaries

### Always do

- Treat the operator's installed `agentbundle` and `credbroker` as deliberate
  and correct.
- Measure resolution in a child process and report provenance beside every value.
- Compare failure sets across the change, never counts or exit codes.
- Classify an install from its recorded metadata, never by importing it.

### Ask first

- Changing the precedence the build gate chain gives an installed copy.
  `tools/repo/build_gate_chain.py:60-72` deliberately *appends* the credbroker
  source path "so a real installed copy still wins"; pytest's `pythonpath`
  *prepends*. The two frames differ — that helper governs the chain's own
  subprocess steps, not a bare `pytest` — but reversing it inside the pytest
  frame is a deliberate change to a documented choice.
- Editing any frozen artifact.
- Restructuring `packages/agentbundle/build/` or any other gitignored build
  output to reduce the shadowing surface of Assumption 7.

### Never do

- Uninstall, reinstall, or modify anything under the interpreter's
  `site-packages`, or run `pip install`, `pip install -e`, or `pip uninstall`.
- Create a virtual environment, or add tooling that creates one.
- Weaken `tools/test_marketplace_envelope_parity.py::test_resolved_layer_*` or
  any roster test to make a measurement come out green.
- Remove a test name from a `workspace.toml` known-issue entry (AC2).
- Edit the body of a shipped spec or an accepted ADR
  (`docs/CONVENTIONS.md` § Document lifecycle).
- Let the guard treat a plain installed copy, or an editable install pointing at
  this worktree, as a failure. Only an editable install pointing elsewhere fails.
- Import `agentbundle.catalogue_tooling.file_safety`, or any other module from
  the packages under measurement, into the guard's process.

## Testing Strategy

**Goal-based check** for AC1, AC4, AC11, and AC12: the declared configuration,
the rewritten comment, the ADR and its two index rows, and the registration
lines are verified by running AC1's two named observables and by scoped grep.

**Goal-based check** for AC2 and AC3, whose artifact is a measurement: the
`tools/ tests/` union and the 37 `packs/**` and 2 `packages/**` suites, before and
after, compared as failure sets.

**TDD** for AC5–AC7: `tools/test_editable_install_guard.py` drives the classifier
with recorded `direct_url.json` payloads — every AC6 silent case, the AC5 failing
case, and the sibling-prefix case that a string-prefix containment test would
miss. Two end-to-end checks close it: a discoverable editable record pointing
outside the worktree must exit 1, and this worktree's real installs must exit 0.

**Manual verification** for AC5 and AC9: run `make lint-editable-install` in this
worktree and record its exit code, and run the guard against a synthesised
peer-pointing editable record to see the refusal and its repair text.

## Assumptions

1. `pytest` is at least 7.0, where the `pythonpath` ini option exists; measured
   here as 9.0.3. An older pytest would ignore the key silently, which AC1's
   collection observable — not a version assertion — is what catches.
2. `packages/agentbundle/agentbundle.egg-info` is present in this worktree,
   untracked and gitignored (`.gitignore:64`), left by an earlier build. It is why
   `agentbundle`'s metadata currently resolves in-worktree at the source version.
   A fresh clone has no such directory, so `agentbundle` there resolves its
   metadata from `site-packages` at a different version and AC5's finding is what
   fires. No acceptance criterion depends on that directory existing.
3. The root `pyproject.toml` is a tracked repository file and is trusted at the
   level of the repository itself: an actor who can edit it already achieves
   execution through pytest. AC8's confinement is therefore defence in depth and
   a drift signal, not a trust boundary. The residual race between the parent
   confining an entry and the child importing from it is accepted unguarded for
   the same reason.
4. `agentbundle.catalogue_tooling.file_safety` is the repository's blessed
   confinement helper and is deliberately *not* used by the guard. Importing it
   would load code from the very distribution whose install shape the guard is
   describing. `tools/repo/worktree_hygiene.py` stays standard-library-only for
   the same reason, and the guard follows it.
5. The guard reads recorded metadata and spawns nothing, so the
   configuration-to-`sys.path` flow that would have needed taint coverage does
   not exist in it. `tools/` remains outside both custom Semgrep path rules
   (`tools/semgrep/argv-path-boundary.yml`, `tools/semgrep/env-path-taint.yml`);
   that is recorded rather than relied upon.
6. An installed `agentbundle` or `credbroker` may be present, absent, or a
   different version, and every one of those is legitimate; an editable install is
   legitimate only while it points at the worktree being worked in (AC5). The two
   package suites of AC3 continue to import the installed copy; giving them
   worktree source is a separate change and is not attempted here.
7. Prepending the two package directories also makes their top-level siblings
   importable — `tests`, `build`, `templates`, `conftest` — and measurement shows
   the collision is order-independent: `packages/agentbundle/tests/__init__.py`
   makes `tests` a regular package, which outranks the repository's
   `__init__.py`-less `tests/` namespace portion even though `"."` is declared
   first. Nothing under `tools/`, `tests/`, or `packs/` imports any of those names
   today, so no root-relative suite is affected, and AC2's before/after failure
   sets are what would catch it if one ever did.
