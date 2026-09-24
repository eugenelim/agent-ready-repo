# Plan: catalogue sync — package sync for both `--package` destinations

- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Spec:** [`spec.md`](spec.md)
- **Owner:** eugenelim

## Approach

Phase 3 left four seam points and a frozen contract around them. The work is
not "add package sync" — it is inverting an exclusion that four call sites
already agree on, then adding the one control that makes the inversion safe.

The order follows the risk. The containment predicate lands first and alone,
because three later tasks depend on which spelling of a path counts as a
package path, and today two call sites disagree about that. The refusals land
before the write extent is wired, so at no commit does the tree hold a write
path to the running engine without the control that refuses it.

## Constraints

- Phase 2's § Boundaries, phase 3's § Agent Rules, and this spec's § Agent
  Rules all bind. Where this spec supersedes a criterion, its identifier names
  what it replaces; nothing edits the frozen phase-3 spec.
- Commits touching `packages/agentbundle/` carry an `Engine-Change-RFC:`
  trailer, and so does the squash body.
- `.agentbundle/tooling/` is empty in this repository, which self-hosts in
  external tooling mode. Every check over the `agentbundle` extent runs against
  a constructed vendored fixture. No test writes to the running interpreter's
  install root.

## Construction tests

Every criterion's oracle is named in the spec's Testing Strategy. What follows
is where each check lives and which production seam it drives, which the
criteria do not say.

- The extent predicate and the scope machinery are unit-tested against the
  planned-path set of a real replay, not a hand-written list —
  `tests/unit/test_catalogue_sync.py`, reusing the
  `_replay_scope_predicate_source` fixture phase 3 built at `:1830`.
- The refusals are driven through the real parser at the command boundary, with
  `resolve_catalogue` and `fetch_catalogue_archive_with_provenance` monkeypatched
  to raise, so "no fetch ran" is an assertion rather than an inference. This is
  the shape phase 3's `:5544` test already uses.
- The self-replacement integration check pip-installs editable into a temporary
  venv and drives the real detector in a subprocess —
  `tests/integration/test_editable_source_detection.py`'s existing shape. It
  asserts an exit code and nothing else, because the refusing run writes nothing
  to observe.
- Six contract-anchor tests pin the current seam behaviour and must move in the
  same commits as the code they pin. They are enumerated in T0.

## Durable-output map

| Durable output | Task |
| --- | --- |
| `docs/architecture/catalogue/upstream-sync.md` | T8 |
| `guides/_shared/how-to/create-a-self-hosted-catalogue.md` and its projection | T8 |
| `packages/agentbundle/README-pypi.md` | T8 |
| `packages/agentbundle/CHANGELOG.md`, `docs/product/changelog.md` | T8 |

## Design (LLD)

### Design decisions

**One containment predicate, identity-based.** Today `select_write_set` uses
`path.startswith(_DEFERRED_PACKAGE_PREFIXES)` (`catalogue_sync.py:186`) while
`_in_coverage` uses `_resolves_within(target, path, _DEFERRED_PACKAGE_PREFIXES)`
(`:776`, defined at `:718`), which compares device and inode through `os.path.samestat`. The
disagreement is inert while nothing under those prefixes is written or removed.
This phase makes both real, so it collapses to the identity-based one. The
string test is the weaker of the two in exactly the direction that matters: a
traversal or, on a case-insensitive mount, a case-variant spelling passes the
prefix test as "not a package path" and would be written under the wrong group
and, worse, admitted to removal outside its coverage.

**Self-replacement is a property of the target, not the source.** No operand
of either AC-0083 input comes from the source, which is what lets the refusal
sit above source resolution and perform no fetch. It also means the refusal is
decidable during `--dry-run`, which is where an adopter should meet it.

**The refusal takes two inputs because the detector fails open.**
`_detect_editable_source` is bounded by an enclosing git repository: at
`source_defaults.py:396-401` it prints a diagnostic and returns `None` when
`_enclosing_git_root` finds none, before it reads the `catalogue.toml` and
`packs/` markers at all. § Grounding's probe confirms a derived catalogue with
both markers and no `.git` takes that branch. A derived catalogue need not be a
git repository, so the adopter who installed the vendored engine editable in a
plain directory is the one the detector cannot see — and is the one whose run
replaces executing code. The second input reads the running package's own
resolved location, which needs neither a PEP 610 record nor a git root. It is
not a second editable-install detector: it answers a narrower question the
first cannot reach, and the two are combined in one control.

**`tree_modified` is observed, not inferred.** The three conditions sharing
exit 1 differ in whether writes landed, and the write sequence already tracks
that: `WriteSequenceResult.acted` is every destination landed and `removed` is
every path unlinked. The field reads those, rather than re-deriving intent from
the exit row, because the row is what the caller already has and cannot use.

### Interfaces & contracts

`--package` moves from a reserved selector to a scoping flag. `cli.py:1236-1242`
keeps its `choices` tuple, which is the only validation the parser owns, and
loses its "not available yet" help text. `_scope_subtrees` (`:121`) gains the
package axis so one function still answers "what is in scope".

### Component / module decomposition

No new module. The extent predicate, the scope axis, the write group and the
refusals all live in `catalogue_sync.py`, which is the one command module the
CLI's lazy-dispatch convention allocates. `safety.py` is unchanged: phase 3's
`Publish` enum, `write_jailed` and the two typed errors are the write
primitives, and this phase adds a caller, not a primitive.

### Failure, edge cases & resilience

- A package write failing mid-run is the case AC-0090 covers, and the reason
  AC-0080 puts packages last: every other write is durable before one is
  attempted, so a rollback executing from replaced code has less to undo.
- `--package agentbundle` under external tooling is AC-0082's malformed row,
  not a silent success.
- A vendored adopter who is *not* running the target's engine — a PyPI install
  beside a vendored copy — is not refused. `_detect_editable_source` returns
  `None` for a non-editable install, which is the correct answer.

### Dependencies & integration

No new dependency. `_detect_editable_source` is imported from
`agentbundle/source_defaults.py`, which `catalogue_sync` does not import today; the import is
the integration. AC-0083's second input needs no import beyond the running
package itself.

## Tasks

### T0: the anchor tests are inventoried and pinned to their criteria

**Depends on:** none

**Tests:** none — this task writes no assertion. It records, in this plan, which
existing assertion each later task must move, so a false GATES failure mid-
EXECUTE is impossible.

**Approach:** the six are `test_catalogue_sync.py:1866` (`admitted == planned`
and `deferred == 0`), `:1907` (duplicates the prefix tuple literally, pins the
extent across four scopes and asserts `deferred_count == len(deferred_paths)`),
`:5601` (`summary["deferred_package"] == 2`), `:4958` (`run(...) == 3` across
six mode-name combinations plus the no-fetch guard), `:4981` (argparse exit 2,
the sole guard on `cli.py`'s `choices`), and `:5739` (`run(...) == 2`, pinning
the `--format json` row above the `--package` row). Three unpinned literals also
move: the refusal message, the `deferred-package=` counts token, and the
`cli.py` help string.

**Done when:** each of the six names the task that rewrites it, below.

### T1: one identity-based predicate decides package membership

**Depends on:** none

**Tests:**
- A path under `.agentbundle/tooling/agentbundle/`, one under
  `.agentbundle/tooling/packs/catalogue-curation/`, and one under
  `packages/credbroker/` each resolve to their AC-0078 destination; a sibling
  such as `packages/credbroker-extras/x` resolves to neither. Verifies AC-0078.
- A traversal spelling reaching the same file receives the decision the
  canonical spelling receives. On a case-insensitive mount, so does a
  case-variant spelling; the check names its skip reason where the platform
  affords no such mount. Verifies AC-0087.
- The admission path and the coverage path return the same answer for every
  input above. The oracle is agreement between the two call sites, which is the
  property that fails today, not either one's correctness alone.

**Approach:** `_resolves_within` (`:718`) already implements the identity
comparison for coverage. The decision is whether to widen it or to hoist it;
T1 hoists, because three callers need it and a helper reached from one is how
the current disagreement arose.

**Done when:** `catalogue_sync.py` holds no `startswith` test against a package
prefix, and the new tests pass.

**Touches:** packages/agentbundle/agentbundle/commands/catalogue_sync.py, packages/agentbundle/tests/unit/test_catalogue_sync.py

### T2: the refusals land before the write extent exists

**Depends on:** T1

**Tests:**
- `--package agentbundle` without `--tooling vendored` exits 2 and names both
  flags, with the resolver monkeypatched to raise. Verifies AC-0082.
- A run whose write set would reach the `agentbundle` destination exits 3 and
  leaves the pre-run walk tuple of the whole target tree unchanged, once per
  AC-0083 input: with `_detect_editable_source` returning the target root, and
  with the running package resolved inside the target's vendored tooling root
  over a target carrying no `.git`. A third case, neither input holding, exits
  past the refusal. Verifies AC-0083.
- The same run performs no fetch, asserted by the raising resolver. Verifies
  AC-0084.
- `--package agentbundle --format json` without `--yes` still exits 2, not 3:
  the malformed group stays above both new rows. Rewrites the anchor at
  `:5739`.
- The refusal fires on `--dry-run` as well as apply, and on a bare
  `--tooling vendored` apply that named no `--package`.

**Approach:** both rows go into `run()` above the `_resolve_source` call at
`:3168`, replacing the block at `:3155-3167`. Ordering is the load-bearing
part: absent-extent above self-replacement, because a run with no destination
has no write set to test.

**Done when:** the new tests pass, `:4958`'s six-combination anchor is rewritten
to the new contract, and no test asserts the retired refusal message.

**Touches:** packages/agentbundle/agentbundle/commands/catalogue_sync.py, packages/agentbundle/agentbundle/cli.py, packages/agentbundle/tests/unit/test_catalogue_sync.py

### T3: the write set admits the package extent under a package scope

**Depends on:** T1, T2

**Tests:**
- An apply run over a vendored fixture admits every replayed path under both
  AC-0078 destinations; the write set differs from the same run with those
  paths removed by exactly that extent. Verifies AC-0079.
- `--package credbroker` admits `packages/credbroker/**` and nothing else;
  `--package agentbundle --tooling vendored` admits the whole vendored tooling
  root and nothing else; `--pack core --package credbroker` admits the union.
  Verifies AC-0081.
- With no scoping flag, a `--tooling vendored` run admits the package extent
  and an external-mode run has none to admit.
- `catalogue.toml` and `tests/conformance/**` stay excluded under a package
  scope, as under every other. Rewrites the anchors at `:1866` and `:1907`.

**Approach:** `_scope_subtrees` gains the package axis and `select_write_set`
loses its deferral branch and its second return value.

**Done when:** the new tests pass and `select_write_set` returns a set alone.

**Touches:** packages/agentbundle/agentbundle/commands/catalogue_sync.py, packages/agentbundle/tests/unit/test_catalogue_sync.py

### T4: packages write last

**Depends on:** T3

**Tests:**
- Over a write set spanning all five groups, every package path's index in the
  observed sequence exceeds every non-package path's index, and the ownership
  state is written after all of them. Verifies AC-0080.
- The relative order of the first four groups is unchanged from phase 3.

**Approach:** `_write_group` (`:581`) gains a fifth branch returning 4, and the
derivation-wide fallthrough keeps 3. The ordering is a property of the returned
sequence, so the test reads `write_order`'s output rather than instrumenting
the write loop.

**Done when:** the new tests pass and phase 3's ordering tests still do.

**Touches:** packages/agentbundle/agentbundle/commands/catalogue_sync.py, packages/agentbundle/tests/unit/test_catalogue_sync.py

### T5: coverage reaches the package extent

**Depends on:** T1, T3

**Tests:**
- A recorded path under either destination that the source has stopped
  shipping is a removal candidate when coverage reaches it, and the sha guard
  still governs whether it is removed. Verifies AC-0086.
- An external-mode run does not remove a recorded `.agentbundle/tooling/`
  path: the tooling mode narrows that destination's coverage, the way
  `--guides-mode none` narrows `guides/`. This is the mode-asymmetry class
  AC-0069 exists for, and the package extent is now inside it rather than
  excluded from it.
- A scoped run still leaves everything outside its scope out of coverage.

**Approach:** `_in_coverage`'s early return at `:776` inverts into the positive
condition AC-0086 states. The ordering matters: `_in_coverage` ends
`return True` at `:786`, so the branch must be added before the exclusion is
removed, never after.

**Done when:** the new tests pass and the `out_of_coverage` count over a
vendored fixture is zero for package paths a vendored run could have planned.

**Touches:** packages/agentbundle/agentbundle/commands/catalogue_sync.py, packages/agentbundle/tests/unit/test_catalogue_sync.py

### T6: the summary retires one field and gains another

**Depends on:** T3

**Tests:**
- The `--format json` summary's key set and the printed counts line's tokens
  each equal a fixed expected set carrying no `deferred_package` and no
  `deferred-package`. Verifies AC-0088. Rewrites the anchor at `:5601`.
- `tree_modified` is false on a declined-consent run and on a no-terminal run,
  and true on a completed apply with non-zero `companion_occupied` — the three
  conditions sharing exit 1. Each is cross-checked against a pre-run and
  post-run walk rather than against the code path that set it. Verifies
  AC-0089.
- `tree_modified` matches AC-0089's end-state rule on both code-4 restore
  rows, driven through the real write sequence rather than a constructed
  result object.

**Approach:** the field is read from `WriteSequenceResult.acted` and `.removed`,
which the sequence already populates. The pre/post walk in the test is the
independent oracle; the implementation must not use it.

**Done when:** the new tests pass and no surface names `deferred_package`.

**Touches:** packages/agentbundle/agentbundle/commands/catalogue_sync.py, packages/agentbundle/tests/unit/test_catalogue_sync.py

### T7: rollback covers a failed package write

**Depends on:** T4, T6

**Tests:**
- With a forced failure on a package write, the post-run walk tuple of the
  whole target tree equals the pre-run walk, and the code is AC-0085's restored
  row. Verifies AC-0090.
- With the restore itself forced to fail, the code is the unrestored row and
  the run names what it left behind.
- The snapshot spans the package extent, so a vendored fixture's snapshot
  bound accounting includes those bytes.

**Approach:** the snapshot and restore are already write-set-wide
(`snapshot_write_set` at `:459`, `restore_from_snapshot` at `:520`), so this
task verifies reach rather than adding a mechanism. If a test shows it does not
reach, that is a defect in this phase's admission wiring, not a missing
feature.

**Done when:** the new tests pass.

**Touches:** packages/agentbundle/tests/unit/test_catalogue_sync.py

### T8: the durable outputs are current

**Depends on:** T2, T3, T4, T5, T6

**Tests:** goal-based.
- `grep` establishes that § Granularity names `.agentbundle/tooling/`, that no
  § Rollout phase is unmarked, and that § Known risks states which extent the
  refusal covers. Verifies AC-0091.
- The guide and its rendered projection both carry the `--package` section;
  the projection is regenerated and re-measured inside this task, per phase 2's
  § Always do. Verifies AC-0092.
- The three release surfaces each name the shipped version and the `--package`
  change. Verifies AC-0093.

**Done when:** all three greps pass and the site build is clean.

**Touches:** docs/architecture/catalogue/upstream-sync.md, guides/_shared/how-to/create-a-self-hosted-catalogue.md, packages/agentbundle/README-pypi.md, packages/agentbundle/CHANGELOG.md, docs/product/changelog.md

### T9: a vendored adopter's run is exercised end to end

**Depends on:** T1 through T8

**Tests:** visual / manual QA. Build a vendored fixture catalogue, run
`agentbundle catalogue sync --source <fixture> --tooling vendored --package
agentbundle <target>` for real, and record the printed plan, the consent
prompt, the exit code and the post-run tree. Then run it against a target that
*is* the editable install root and record the refusal.

**Done when:** both transcripts are in the verification ledger and AC-0099 and
AC-0100 hold against them.

**Touches:** docs/specs/catalogue-package-sync/notes/verification-ledger.md

## Grounding

The seam points, the write sequence, the anchor tests and the detector were
read at `d00f39e34`. Line numbers in this plan are from that commit.

**The release-surface derivation.** `notes/grounding/derive-release-surfaces.py`
enumerates the surfaces a version bump must move, from the version-bump rule
plus the package's declared readme rather than from a hand-written list, and
reports for each whether it carries adopter-facing prose or a version literal
alone. At `d00f39e34` it reports five surfaces, all at `0.49.0`:
`packages/agentbundle/agentbundle/version.py` and
`packages/agentbundle/pyproject.toml` (literal only), and
`packages/agentbundle/CHANGELOG.md`, `docs/product/changelog.md` and
`packages/agentbundle/README-pypi.md` (prose). AC-0097 quantifies over all
five; AC-0098 over the three prose surfaces. The script is the closed set, not
this paragraph — re-run it rather than trusting the count here.

One probe ran before review, against that commit. It constructed a directory
carrying `catalogue.toml` and `packs/` and no `.git`, and called
`_enclosing_git_root` on a vendored engine path beneath it. The result was
`None`, which is the branch at `source_defaults.py:396-401` that returns before
the marker walk. That measurement is why AC-0083 takes two inputs rather than
one, and it is recorded here rather than restated at the criterion.

## Rollout

Additive within the verb. Reverting this phase restores phase 3's behaviour
exactly: the package subtrees return to being reported and not written.

## Risks

- **The refusal's reach is narrower than the risk's.** AC-0083's two inputs
  cover an editable `agentbundle` rooted at the target and a vendored engine
  installed editable, git repository or not. Neither covers an editable
  `credbroker`, which the spec records as a follow-on. Accepted knowingly.
- **The vendored fixture is the only place the `agentbundle` extent is
  exercised.** A fixture that diverges from what `init` actually writes would
  let every check pass over a shape no adopter has. T1's first test compares
  against `init`'s own output for this reason.

## Changelog

- 2026-09-24 — drafted.
