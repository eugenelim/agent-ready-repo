# Plan: sca-gate-hardening

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `tools/audit-requirements.py` — all six behaviour fixes.
- `tools/test-audit-requirements.py` — cases 10-12 (predicate, env scrub, floor).
- `workspace.toml` — remove the six closed `[backlog].open` entries.
- `docs/specs/sca-gate-hardening/{spec.md,plan.md}` — this contract.

**What demonstrates done**
- `python3 tools/test-audit-requirements.py` exits 0 with the new cases passing.
- The REAL leg runs green: `python3 tools/audit-requirements.py tools/requirements.txt
  $(find packs -name requirements.txt | sort)` at exit 0 over all nine manifests.
- Each of the five mutations in spec AC6 produces its named failure, then reverts.
- A warm-cache before/after timing pair for AC1's "measured free" claim.
- `make lint-ruff`, `python3 tools/lint-build.py`, `make ci` green.

**What I am NOT changing**
- Not the Makefile's `--ignore-vuln` suppressions or its manifest list.
- Not the three unaudited `tools/` manifests' coverage (AC7 pins, does not widen).
- Not `partition()`'s first-party skipping, which is the file's original subject.
- Not batching anything — the archived spec explains why.

## Declined patterns

- **Tempted:** add the three unaudited `tools/` manifests to the invocation while the
  file is open; it is one argument each and closes a sibling entry.
  **Declined:** `sast-requirements-not-audited` records an explicit
  audit-vs-Dependabot decision ("Decide which, then do one — doing both duplicates the
  noise"). Taking the audit half unilaterally pre-empts it. AC7 pins the roster so a
  new manifest is deliberate, which is the part that needs no decision.
- **Tempted:** make `sca-requirements-include-lines-unaudited` exit 2 on an
  include-only manifest, the entry's stated alternative. **Declined:** the entry offers
  "count them as content that must be audited, **or** exit 2". Counting them audits
  the manifest, which is what the gate is for; exiting 2 refuses a shape self-test
  case 4 already blesses.
- **Tempted:** assert AC2 by calling `audit()` and checking the printed output — it
  exercises the real path. **Declined, after doing it:** it spawned pip-audit against a
  nonexistent include, adding network I/O and a usage error to a self-test. Asserted on
  the predicate instead (AC8). The first version also *passed*, which is why this was
  caught by timing the suite rather than by it failing.
- **Tempted:** pin the manifest roster by content hash rather than count, so a *changed*
  manifest also fails. **Declined:** that is the noisy-re-sign trade recorded under
  `ci-parity-hidden-gate-in-dispositioned-step`; a manifest's contents changing is
  normal and the audit already reads them.
- **Tempted:** raise `--strict` to the `--build-system` and `--optional-group`
  invocations too. **Declined:** the entry explicitly scopes that as a separate
  decision ("Decide separately whether the requirements-sast.txt and /dev/stdin
  invocations get it too"). They flow through the same `audit_lines`, so they DO
  inherit it — noted here because that is a consequence worth being explicit about
  rather than silent, and it is the desirable direction.

## Tasks

### T1 — Read the six entries against the code; confirm each is live
- **Mode:** goal-based. `Done when:` each defect is located in `audit_requirements.py`
  or the Makefile and confirmed present.
- **Tests:** no stub (goal-based).
- **Status:** done. All six live; AC2's is latent-but-sanctioned.

### T2 — Implement AC1-AC5
- **Mode:** goal-based. `Done when:` `lint-ruff` clean and the real leg exits 0.
- **Tests:** no stub for the behaviour; T4 adds the assertions.
- **Touches:** `tools/audit-requirements.py`.

### T3 — Verify the flags by invocation, not by reading
- **Mode:** goal-based. `Done when:` the real leg runs green over all nine manifests.
- **Tests:** no stub (goal-based).
- **Status:** done, and it earned its place — `--service` was wrong (`-s` /
  `--vulnerability-service` is the real flag) and the failure did not name the flag.
  Reading the diff would not have caught it.

### T4 — AC7 + AC8: the floor and the predicate cases
- **Mode:** goal-based. `Done when:` self-test exits 0 with cases 10-12 present.
- **Tests:** the file under change is the test.
- **Touches:** `tools/test-audit-requirements.py`.

### T5 — AC6: mutate every new control
- **Mode:** goal-based. `Done when:` all five mutations produce their named failure
  and `git diff --stat Makefile` is empty afterwards.
- **Tests:** no stub (goal-based).

### T6 — AC1's timing claim
- **Mode:** goal-based. `Done when:` a warm-cache before/after pair exists, taken
  back to back after a discarded warm-up, with the frame recorded beside the numbers.
- **Tests:** no stub (goal-based).

### T7 — Close the six backlog entries
- **Mode:** goal-based. `Done when:` the slug-set delta against `HEAD~1` is exactly
  those six and `lint-spec-status` is clean.
- **Tests:** no stub (goal-based).
- **Touches:** `workspace.toml`.
