# Spec: compare-bandit-suppressions

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** none — single task; verification mode is named in § Testing Strategy
- **Mode:** full (governance surface — it is the verification procedure for
  changes to `# nosec` suppressions, which govern what the SAST gate skips)
- **Constrained by:** [ADR-0084](../../adr/0084-nosec-reason-delimiter-and-stderr-as-a-gate.md),
  [ADR-0017](../../adr/0017-adopt-bandit-pip-audit-semgrep-sast-gate.md)
- **Contract:** none (a manual verification harness; no published interface)
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Named deviation from full mode

No `loop-engine` / `loop-cohort` state machine and no `plan.md` — a single task
whose verification is the tool's own reproduction of a historical result. The
two human approval gates were **granted up front by the requester**.

## Objective

Rewriting a `# nosec` comment is supposed to be behaviour-preserving, and the
only way to know is to compare what Bandit reports before and after. That
procedure exists — written out in `bandit-nosec-comment-hygiene`'s § Testing
Strategy — but it lives as **prose inside a Frozen spec**, so when the procedure
improves the record cannot be corrected. That is the defect this closes.

It earns being a tool for a second reason: the procedure has four traps, and
each one gave a *wrong answer* the first time it was run by hand. All four fail
silently — they produce a confident wrong number, not an error.

## The four traps, and where each is encoded

| Trap | What went wrong by hand | Where it lives now |
| --- | --- | --- |
| **Rows are not keys** | 362 raw result rows collapse to 239 distinct `(filename, test_id, issue_text)` keys; comparing row counts answers a different question | `scan()` reports both and diffs only the key set |
| **Two clean worktrees** | A worktree vs. the *dev tree* scanned gitignored build output on one side only, inflating both totals and inventing a 27-key delta | both sides are `git worktree add --detach`; the working tree is never scanned |
| **Relative scan roots** | Absolute paths stop `bandit.yaml`'s `exclude_dirs: '*/tests/*'` glob matching, so the two scans cover different file sets | roots stay relative, `cwd` is the worktree |
| **Both scans exit 1** | Findings are expected at the low/low floor, so a non-zero exit aborted the run | the exit code is ignored; a missing report is the only fatal case |

A fifth trap surfaced while building this and is encoded too: **`Path.resolve()`
anchors a relative path to the calling process's cwd** — the repo, not the
worktree — silently mixing the two trees. `_worktree_relative` is string-based
for that reason, and a case pins it.

## Two checks, because neither is sufficient

- **Reported findings.** Catches a suppression that weakened, or widened onto a
  test that fires somewhere in the repo.
- **Resolved-id inventory.** Every suppression comment at both revisions run
  through Bandit's own `_parse_nosec_comment`. Catches what the scan cannot see:
  a suppression widened onto a test that fires nowhere today, and any directive
  resolving to no id at all — a blanket suppression of the whole statement.

## A reported-finding difference has two possible causes

The finding diff cannot tell a moved *suppression* from moved *code*: a key on
one side only means either the suppression changed, or the file did. So the
rows name both, and the resolved-id inventory is the half that isolates
suppression changes — it compares only files present at both revisions.

Found by running the tool on this repo's own recent history: three findings
appeared at head solely because #971 added `tools/export_work_index.py`. An
earlier message asserted "suppression WEAKENED at head" for exactly those rows,
which was wrong.

## A difference is a signal, not a verdict

Exit 1 means "these two revisions do not suppress the same things — look". It
does not mean "you broke something". Proven on the tool's own validation run
against the change that motivated it (below), where the one reported difference
was the intended removal of a spurious directive.

Only a file present at **both** revisions can have had its suppressions changed.
A file added at head brings new suppressions by definition, and a deleted file
takes its own with it; both are printed as notes, neither fails the run. The
first version of this script conflated them and reported a false FAIL, because
the change it was validating against added two files.

## Acceptance Criteria

- [x] **AC1 — it reproduces the historical result exactly.** Run against the
      pinned base `1f6b2d2f` and the merged `7f186a0b`, it reports **362 rows →
      239 distinct keys on both sides, empty symmetric difference, and stderr
      54 → 0** — the numbers `bandit-nosec-comment-hygiene` records. This is the
      acceptance test: the tool is only worth having if it agrees with the
      hand-run procedure it replaces.

- [x] **AC2 — it detects the one real suppression change in that diff.** The
      same run reports `tools/capture-publish-control-evidence.py` as base
      `[{B310}, {B310}]` → head `[{B310}]`, which is exactly the spurious
      second directive that spec's AC2 removed (a prose block that *began* with
      `# nosec`). Detecting an intended change is the tool working.

- [x] **AC3 — added files are notes, not failures.** The same run reports
      `tools/run-bandit-gate.py` and `tools/test-sast-stderr-gate.py` as new
      files carrying two suppressions each, without failing on them.

- [x] **AC3b — a finding present on one side only is not attributed to a
      cause.** The rows name both possibilities (suppression moved, or code
      moved), because the finding diff cannot distinguish them; the resolved-id
      inventory is what isolates suppression changes. Verified on real history:
      `7f186a0b -> main` reports three head-only findings that exist purely
      because an unrelated PR added a file, alongside `resolved suppression ids:
      identical across 16 shared file(s)`.

- [x] **AC4 — blanket suppressions at head are called out by name**, separately
      from the equivalence result, since one is a defect regardless of what the
      base looked like.

- [x] **AC5 — the four traps are encoded, not documented.** Each has a
      counterpart in code per the table above, and the ones that are pure
      functions have self-test cases.

- [x] **AC6 — a ref compared against itself is identical.** `--e2e` runs it and
      must exit 0; a non-reproducible scan (wrong cwd, leaked absolute path,
      nondeterministic key) fails here.

- [x] **AC7 — the scan scope is derived, not copied.** Roots come from the
      Makefile's `SAST_DIRS`, and an appended second assignment fails loudly
      rather than silently narrowing the comparison.

- [x] **AC8 — it has a self-test with a home.**
      `tools/test-compare-bandit-suppressions.py`, added to `tools/test-all.py`'s
      curated manifest (whose entries `test-test-all.py` gates), running the
      fast cases only.

- [x] **AC9 — gates pass.** `python3 tools/lint-ruff.py`, `make lint-mypy`,
      `SKIP_SAST=1 make build-check`, `make sast`.

- [x] **AC10 — the register entry is removed, and the ordering it depended on
      is recorded.** `compare-bandit-suppressions-tool` is *added* by the
      sibling PR #977 and did not exist on the `origin/main` this branch was
      first cut from, so the two PRs agreed that whichever merged second would
      remove it. #977 merged first; this PR merges second and removes it here.
      Stated rather than silently checked — for most of this branch's life the
      AC could not be satisfied, and an AC that claims a deletion which never
      happened is worse than an open one.

## Boundaries

### Always do

- Always scan two clean worktrees. The working tree is never an input.
- Always keep the roots relative and derived from `SAST_DIRS`.

### Ask first

- Ask before wiring this into `make build-check`. It creates two worktrees and
  runs two full scans; it is a harness for a human touching a suppression, not
  a per-PR gate.

### Never do

- Never raise the severity floor. `low/low` is deliberate — a suppression that
  moved a low-severity finding is still a moved suppression, and the gate's own
  `medium/medium` floor would hide it.
- Never compare against a moving branch name in a recorded result. Pin the base
  to a SHA so the check stays reproducible after the branch advances.

## Testing Strategy

Goal-based, against a known-answer historical comparison:

- `python3 tools/compare-bandit-suppressions.py 1f6b2d2f 7f186a0b` reproduces
  the numbers in AC1–AC3. Run; output recorded in the PR description.
- `python3 tools/test-compare-bandit-suppressions.py` — fast trap cases.
- `python3 tools/test-compare-bandit-suppressions.py --e2e` — adds the same-ref
  comparison (two full scans). Run once here.
- `lint-ruff`, `make lint-mypy`, `SKIP_SAST=1 make build-check`, `make sast`.

## Assumptions

- Bandit's `_parse_nosec_comment` stays importable across the 1.9.x line pinned
  in `tools/requirements-sast.txt`. `tools/lint-nosec-form.py`'s parity case
  turns a change there into a red build, so this assumption is already gated
  elsewhere.

## Declined

- **Pure stdlib.** AGENTS.md requires it for new `tools/` scripts; this one is a
  Bandit *driver* — it shells out to `bandit` and imports its parser — so the
  rule cannot apply. Named here rather than worked around.
- **Wiring it into `make build-check`.** See Boundaries § Ask first.
- **Failing on any inventory difference.** Added and removed files are notes;
  only a file present at both revisions can have had its suppressions changed.
