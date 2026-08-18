# Plan: rfc0088-round10-measurement

- **Status:** Drafting
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files this will touch**

- Evidence tree (`/private/tmp/rfc0088-round9-evidence.C5FnKi/`): sandbox
  parameterisation at existing driver launch sites; one new fixture
  (`s3/r10-restored-profile-realm.mjs`); one new composition fixture
  (`s2/r10-profile-with-node-permissions.mjs`); new `s1`/`s2`/`s3` result
  artifacts; `build-archive.py` MEMBERS; `verify-note-figures-r7.py` facts.
- Repo: `docs/rfc/0088-notes/spikes/` (round-10 note), the archive note,
  `docs/rfc/0088-web-pilot-foundation.md` (Amendments only — body stays frozen),
  and this spec pair.

**What demonstrates done**

Each task's fixture writes a results artifact containing at least one row that
could have failed, the figure verifier reports zero wrong and zero unclaimed
across all documents, every new fact fails under mutation of the field it
guards, and the repo gate suite passes with the RFC still `Experimental`.

**What is NOT changing**

RFC status; any blocker's open/closed state; any approver disposition (A–D); the
RFC body; production packs, runtime code, dependencies, contracts, catalogue
entries; the apparatus coverage figure; `origin/main`'s pre-existing
`catalogue-verify` failure.

## Declined-pattern register

| Temptation | Why declined |
| --- | --- |
| A shared `launchParameterised()` helper across all drivers | Each launch site differs in options and lifecycle, and a shared helper is a new module boundary inside a spike tree. Round 9's lesson was that a hand-maintained model of another program's behaviour goes stale; parameterise each site in place. |
| Reuse the realm driver to fake a "restored profile" | A restored profile is a different lifecycle — the realm must exist *before* the browser starts. Reusing the realm driver would measure the wrong thing and produce a green row for a question nobody asked (the stand-in defect, R9-8). |
| Re-run the mutation harness "while we're in there" | Explicitly refused by the round's stopping rule. Adding controls moves the coverage figure by construction, so a round that both adds facts and re-measures coverage reports its own activity as progress. |
| Add a `producer` field to artifacts to close R9-14 | Would require re-running every arm; hand-writing it into finished artifacts is fabrication. Stays a recorded bounded limit. |
| Fix `origin/main`'s `catalogue-verify` failure | Not this change's concern; widening a measurement PR into someone else's build fix hides the real diff. |
| Declare AC5 "not applicable" because the pull is expensive | Deferral with a slug keeps the gap visible. "Not applicable" would silently shrink the round's own scope. |

## Resolve-vs-surface disposition record

| Item | Disposition |
| --- | --- |
| Linux trust arm needs a ~3 GB pull on a space-constrained host running the owner's infra | **Surface** — disk spend on the owner's machine is theirs to authorise; recorded as AC5 + deferral slug so it cannot be lost. |
| work-loop FSM scripts absent from this repo | **Resolve** — run the loop discipline without the bookkeeping, named skip recorded in spec.md. |
| Reproduction identity (Playwright/Chromium versions) | **Resolved** before planning — verified on host, matches promoted evidence. |
| Task-1 target set | **Resolved** by grep, not recall — three files carry `chromiumSandbox`. |
| A driver behaving differently when sandboxed | **Resolve into the record** — it is a finding that falsifies a currently-unproven inference, and is reported, not smoothed. |

## Tasks

### T1 — Parameterise and re-run the S1 lifecycle corpus sandboxed

- **Verification:** visual / manual QA — real browser, mode read back.
- **Tests:** `s1/r10-*-results.json` records `sandboxRequested`, `sandboxObserved`
  and a row that fails when the two disagree; a deliberate mismatch injection
  makes the run fail. `no stub (manual QA)`.
- **Approach:** add `chromiumSandbox: true` at `s1/s1-lifecycle.mjs`'s launch
  site plus a read-back assertion; run both modes; record per-driver comparison.

### T2 — Re-run the S3 rail drivers sandboxed

- **Verification:** visual / manual QA.
- **Tests:** each rail driver's artifact carries its own sandboxed/off comparison
  and at least one control arm that must fail. `no stub (manual QA)`.
- **Approach:** same parameterisation at `s3/r5-mitm-trust.mjs` and
  `s3/r7-trust-and-method-composed.mjs` launch sites. Record per driver (AC2) —
  no aggregate summary.

### T3 — Compose the OS profile with the Node permission model

- **Verification:** visual / manual QA — real `sandbox-exec` + real Node flags.
- **Tests:** `s2/r10-profile-with-node-permissions-results.json` records, for
  each probed path, whether the profile admits it and whether the permission
  model denies it; the browser-profile read (correction 9) is a named row and its
  outcome is recorded either way. Control arm: the same read without the
  permission model must succeed, or the fixture proves nothing.
- **Approach:** new fixture; deny-default profile + `--permission` flags; probe
  the specific paths item 5 names (`file-read*` breadth, and the
  `sysctl kern.procargs2` argv read that exposes the SPKI pin).

### T4 — Restored-profile realm fixture

- **Verification:** visual / manual QA.
- **Tests:** `s3/r10-restored-profile-realm-results.json` records whether a realm
  present in a restored profile exists before the shim registers. Control arm: a
  fresh profile must show the shim registering first, or the fixture cannot tell
  the two cases apart.
- **Approach:** new fixture; create a synthetic profile containing a realm, close
  the browser, relaunch against that profile directory, observe ordering.

### T5 — Promote

- **Verification:** goal-based.
- **Tests:** `Done when:` archive builds, verifier reports zero wrong / zero
  unclaimed, `r9-gates.sh` passes, RFC status `Experimental`, every new fact has
  a recorded mutation test.

## Anchor-test sweep

Contract-anchor tests that pin file content and must be updated when it changes:
the archive's own manifest and digest (four claim sites — MEMBERS count, manifest
line count, archive-note figure, RFC figure) are re-synced by `r9-promote.sh`;
the defect-count reconciliation (`r9-defect-count.py`) pins the corrections-table
row count against three prose sites. Both are re-run in T5 rather than discovered
mid-execute.
