# Plan: work-loop-concurrency-harness-reliability

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

## Approach

Keep the already-diagnosed harness repairs, then add a deterministic red test
for the production lock race exposed by the user's 50-run proof. Pause a leader
between exclusive creation and ownership-record write; prove that a follower
cannot reclaim or enter during that interval. Make the minimum production fix:
an empty record remains recognisable as crash residue, but is reclaimable only
after `stale_after`, like every other recognised lock. Regenerate projections
and publish the core patch release metadata.

## Assumption trio

- **Files:** this spec and plan; the cohort wrapper and concurrency harness;
  canonical `_statelock.py` and its direct test; core version manifests,
  generated projections, and changelog.
- **Done:** exact lock interleaving is red before and green after the fix; stale
  empty recovery remains green; diagnostics and static gates pass; 50
  consecutive concurrency runs and the deliberate unlocked run prove causal
  coverage on a writable runner.
- **Not changing:** timeout/stale budgets, lock path or record format,
  state/FSM behavior, case inventory, dependencies, or ADR-0074.

## Declined patterns

- Widening any timing budget: the failure is a false ownership inference, not
  a slow contender.
- Retrying or skipping failed cases: either converts evidence into probability.
- Reclaiming every empty record immediately: the empty file is an observable
  intermediate state of a live acquisition, not proof of a crashed creator.
- Removing empty-lock recovery: a creator killed before its record write still
  needs bounded automatic recovery after `stale_after`.
- Replacing the lock implementation or record format: the existing protocol
  needs a one-condition correction, not a new locking design.
- Keeping the live-tree fingerprint: it observes other processes, not only the
  harness under test.

## Resolve-vs-surface disposition record

| Item | Disposition |
| --- | --- |
| The original CI log does not name the failed case | Resolved by AC1; wrapper output is the first edit. |
| Tempfile-based execution cannot run in this session | Surface at handoff with exact commands; no false green claim. |
| Arrival spread can fail under unfair scheduling | Resolve with explicit contention evidence, not a larger threshold. |
| Live checkout can change independently of this suite | Resolve by asserting each child's resolved throwaway root. |
| Review Blocker: unlocked proof stopped at the probe | Applied: synchronize every unlocked caller at the real state-write boundary so the case-specific invariant runs and fails. |
| Review Blocker: some failures lacked canonical names/sync state | Applied: canonical `(case_name, test)` inventory plus last-sync suffix on every `fail()` path. |
| Initial light-mode blocker re-review | Clean — ready to commit. |
| Run 23: live empty lock reclaimed before token write | Escalated to full mode; add an exact interleaving regression and change immediate reclaim to stale-only reclaim. |
| Full-mode review Blocker: follower timeout alone did not prove leader ownership | Applied: AC5 and T2 also pin the leader inode, clean entry/exit, release, and absence of `StateLockLost`. |
| Full-mode review Blocker: TDD cases existed only in prose | Applied: materialized compiling `fresh-empty-lock-is-contended` and `stale-empty-lock-is-reclaimed` construction tests before production edits. |
| Security concern: sibling path confinement was a boundary but not an AC | Applied: AC9 and `lock-path-stays-lexical-sibling` pin lexical derivation and retain existing non-regular/symlink refusal tests. |
| Security re-review: fresh test omitted reclaim residue/link count | Applied: assert one link and no `.reclaim.*` companions before leader release or after cleanup. |
| Security re-review: dangling symlink did not cover an existing target | Applied: `lock-path-symlink-to-file-is-refused` pins refusal and target preservation. |
| Adversarial re-review: AC9 prohibited its own reclaim companion and did not exercise reclaim through a state symlink | Applied: allow only lexical `.lock.reclaim.*` companions and add `stale-reclaim-stays-lexical-sibling`. |
| Adversarial second re-review: target-directory reclaim residue was not checked | Applied: the stale-reclaim case globs both lexical and symlink-target directories for companions. |
| Full-mode adversarial final review | Clean — ready to commit. |
| Full-mode secure-design final review | Clean — ready to commit. |

## Diagnosis

| Candidate | Expected if true | Actual evidence | Verdict |
| --- | --- | --- | --- |
| Harness arrival spread exceeds 50 ms | A concurrent case fails its timing barrier without a production error. | Replaced with explicit real-lock contention; all followers reported contention in the eventual failure. | Real harness defect, fixed independently; not the run-23 cause. |
| Another process changes the live checkout | `harness-is-hermetic` reports mutable live paths changed. | Replaced with direct child repo-root evidence; run 23 passed this case. | Real harness isolation defect, fixed independently; not the run-23 cause. |
| A live empty lock is reclaimed before its owner writes the record | Two processes enter one critical section; one later loses ownership, a mutation is lost, and that process exits non-zero after printing its success line. | Run 23: all 8 children synchronized, all 7 followers contended, two children reported count 6, final count was 7, and one child printed success then exited 1. `_statelock.py` currently classifies every empty record as immediately reclaimable during the create-before-write window. | Confirmed root cause. |
| A contender merely exceeds the production lock timeout | One child exits with `StateLockTimeout` without duplicate intermediate counts or a post-success failure. | Failing child emitted a successful mutation first; final state lost one update. | Contradicted for run 23. |

The old comment that an empty lockfile “can never be a live holder's” is false:
`os.open(... O_CREAT|O_EXCL ...)` publishes the empty file before the next
`os.write`. Immediate reclaim removes a live lock, admits a second writer, and
causes the original holder's release token check to fail after its mutation.

## Tasks

### T1: Preserve and strengthen concurrency-suite evidence

**Depends on:** none

**Tests:**
- Goal-based (AC1): force a child failure and confirm its canonical `FAIL`
  diagnostic precedes the wrapper summary.
- TDD (AC2–AC4): followers record production-lock contention; all failures
  include canonical case and sync evidence; children report throwaway roots.

**Approach:** preserve child streams, replace scheduling inference with a
test-only real-lock proxy, and replace live-tree fingerprinting with direct
fixture-root evidence.

### T2: Add deterministic fresh-empty and stale-empty lock tests

**Depends on:** T1

**Mode:** TDD

**Stub:** true — `test_fresh_empty_lock_is_contended` and
`test_stale_empty_lock_is_reclaimed` in `test-statelock.py`; the complementary
`test_lock_path_stays_lexical_sibling`,
`test_stale_reclaim_stays_lexical_sibling`, and
`test_lock_path_symlink_to_file_is_refused` regressions pin AC9.

**Tests:**
- TDD red (AC5): pause a leader's `os.write` after exclusive file creation;
  require a follower to time out without entering, verify the lock path still
  has the leader's inode, then release the leader and require clean entry,
  release, exit 0, and no `StateLockLost`.
- Regression (AC6): age an empty lock beyond `stale_after` and require bounded
  reclaim and acquisition.
- Regression (AC9): acquire through a symlinked state path and prove the lock
  exists only at its lexical sibling; reclaim a stale lexical lock through the
  same path without touching the symlink target's directory; refuse a lock-path
  symlink to an existing file without modifying its target; retain existing
  dangling-symlink and non-regular-file refusal cases.

**Approach:** synchronize two standalone child processes with filesystem
markers so the pre-token interval remains open until the follower reports its
result. Do not infer ordering from sleeps.

### T3: Correct empty-lock reclaim semantics

**Depends on:** T2

**Tests:**
- AC5's exact interleaving turns green.
- AC6 and all existing `_statelock` security/recovery cases remain green.

**Approach:** retain empty records as recognised crash residue but gate their
reclaim on `age > stale_after`; update comments that asserted immediate reclaim
was safe. Do not change any timing constant.

### T4: Regenerate and release the core patch

**Depends on:** T3

**Tests:**
- AC8: `make build-self` succeeds and canonical/generated lock files match.
- Manifest and changelog checks identify the next core patch version.

**Approach:** bump both core manifests to the same patch version, regenerate
projected files from `.apm`, and add the dated changelog entry.

### T5: Prove reliability and causal coverage

**Depends on:** T4

**Tests:**
- AC7: state-lock suite, direct concurrency suite, and cohort wrapper pass.
- AC7: 50 consecutive direct concurrency-suite runs pass.
- AC7: deliberate lock bypass exits non-zero and names the affected case.
- Repository gates: Ruff, spec-status lint, build check, and diff checks.

**Approach:** run the exact handoff commands on a writable runner, capture the
old-code red result for AC5, then verify the fixed tree and causal proof.
