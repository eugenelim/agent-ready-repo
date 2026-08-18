# Spec: rfc0088-round10-measurement

- **Status:** Implementing
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [RFC-0088](../../rfc/0088-web-pilot-foundation.md) — Experimental; this spec measures four of its named residuals and changes none of its decisions
- **Contract:** none — this spec produces evidence, not interfaces.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full (work-loop). Risk triggers that fired: security boundary (browser
launch, network I/O, filesystem, OS sandbox profiles) and multi-feature/dependent
tasks (four measurement tasks). NAMED SKIP: this repository does not ship
scripts/loop-engine.py, scripts/loop-cohort.py, scripts/lint-spec-status.py or
scripts/check-base-freshness.py, so full mode's FSM bookkeeping and its mechanical
doc-drift linter cannot run. The loop discipline (PLAN -> EXECUTE -> GATES ->
REVIEW -> DECIDE) runs without the state machine; base freshness was established
by fetching origin/main and branching from it. -->

## Objective

RFC-0088 has been Experimental for nine rounds. Its six pre-acceptance blockers
are dominated by approver dispositions no experiment can settle; the measurement
work that genuinely remains is a **finite, named list of four tasks**. This round
runs that list and stops.

The round exists to make Decision A decidable — not to raise confidence
generally. It is explicitly bounded: it measures the **architecture** and does
**not** re-measure the apparatus, because round 9 established that the coverage
figure moves when controls are added and is therefore not a progress metric.

## Boundaries

**In scope**

- Re-running the browser-launching drivers that have never been run with
  `chromiumSandbox: true`, so "the rails are sandbox-invariant" stops being
  generalised to figures no sandboxed arm produced.
- Composing the macOS OS-level boundary profile with the Node permission model —
  never done in any round.
- A restored-profile realm fixture — no fixture creates one at all today.
- A Linux trust arm (deferred; see Assumptions).

**Out of scope — and these are refusals, not omissions**

- **Any apparatus re-measurement.** No mutation-harness run, no coverage
  percentage, no claim-accounting figure is a deliverable of this round. The
  stopping rule below is what makes the round bounded.
- Changing the RFC's status, closing a blocker, or recording an approver
  disposition. A–D remain the approver's.
- Any implementation: no production packs, runtime code, dependencies,
  contracts, catalogue entries, SDK, adapters, scheduling, or account
  integrations.
- Fixing the pre-existing `CAT-V-014` `catalogue-verify` failure on `origin/main`.

**Security preconditions — binding on every subprocess and candidate**

Carried forward unchanged from the round-2 incident disposition. The three
session tokens exposed in the round-2 S4 run were rotated and the SSH agent held
no identities; that incident is closed for agent forwarding and those three
tokens. **The broader account-level exposure from that unmonitored run remains
ACCEPTED, not resolved, and must not be re-described as resolved.**

Every subprocess: never inherit the ambient environment; construct an explicit
allowlist; never pass `SSH_AUTH_SOCK`, session tokens, credentials, browser
profiles or protected config; scan the exact artifact and dependency tree before
execution; fresh synthetic profile and synthetic data only; never touch a
personal profile or live account; never print, log, compare or archive a
credential value. Executable adapters and candidate tools are trusted-code risks,
not sandboxes.

## Testing Strategy

Verification mode per task is **visual / manual QA against the real artifact** —
these are measurement fixtures, so the deliverable *is* the observed output of a
real browser or a real OS sandbox, and a passing unit gate would prove nothing.
Each task therefore:

1. Runs the real driver end-to-end and writes a results artifact with per-row
   `ok` / `result` fields.
2. Is admitted only if the artifact records a row that **could have failed** —
   a control arm, a denied operation, or a read-back that disagrees with the
   request. An arm with no failable row is not evidence.
3. Gets its published figures checked by `verify-note-figures-r7.py`, and every
   new fact is **mutation-tested individually**: mutate the artifact field, watch
   the fact fail, restore. A fact not shown to fail is not a control (R9-15).

Gates, in order: `build-archive.py` (privacy, provenance, duplicate-digest,
failing-row, import-closure gates) → `verify-note-figures-r7.py` → the repo gate
suite (`r9-gates.sh`).

## Acceptance Criteria

- [x] **AC1 — Sandboxed re-runs.** Every browser-launching driver in the promoted
      corpus that lacked `chromiumSandbox: true` runs sandboxed, with the mode
      **read back from the browser** and a run whose observed mode disagrees with
      its requested mode failing rather than silently reporting the other
      configuration.
- [x] **AC2 — Result stated per driver, not in aggregate.** Each re-run driver's
      sandboxed result is compared against its sandbox-off result and recorded as
      *identical* or *differing*, per driver. A single "no differences" summary
      does not satisfy this.
- [ ] **AC3 — Profile × Node permission model.** The macOS `deny default` profile
      runs composed with the Node permission model, and the artifact records which
      filesystem reads the permission model denies that the profile admits —
      including whether the correction-9 defeat (reading the live browser profile)
      is closed by the composition.
- [ ] **AC4 — Restored-profile realm.** A fixture creates a profile containing a
      realm, restarts the browser against it, and records whether the shim is
      registered before that realm exists. Whatever the outcome, it is recorded as
      *measured* — the standing claim today is "requirement, not measurement".
- [ ] **AC5 — Linux trust arm** *(deferred: rfc0088-round10-linux-trust-arm)* —
      requires a ~3 GB image pull and a new driver; see Assumptions.
- [x] **AC6 — No apparatus figure moves as a deliverable.** The round publishes no
      new coverage percentage or claim-accounting total. If a control defect is
      found it is fixed and recorded, and does **not** extend the round.
- [x] **AC7 — Every new fact is mutation-tested**, with the one-line result of each
      test recorded in the note rather than summarised as a pass.
- [x] **AC8 — Gates clean**: archive builds, figure verifier reports zero wrong and
      zero unclaimed, repo gate suite passes, RFC status still `Experimental`.

## Assumptions

- **A1 — The Linux trust arm is deferred, not dropped.** It needs both a ~3 GB
  `mcr.microsoft.com/playwright:v1.62.0-noble` pull and a **new** driver: the
  trust drivers (`s3/r5-mitm-trust.mjs`, `s3/r7-trust-and-method-composed.mjs`)
  are macOS-only, so there is nothing to merely re-run. The host has 15 GB free
  and is running the owner's own Docker infrastructure; the pull is the owner's
  call, not this round's. Recorded as AC5 with a deferral slug so the gap stays
  visible rather than quietly becoming "not applicable".
- **A2 — Reproduction identity holds.** Verified before planning: Playwright
  1.62.0 and bundled Chromium 151.0.7922.34 launch with `chromiumSandbox: true`
  on this host — the same versions as the promoted evidence.
- **A3 — The task-1 target set was derived, not recalled.** Exactly three fixture
  files carry `chromiumSandbox`; the S1 lifecycle corpus, both trust drivers and
  the S3 rail drivers do not. The RFC's "two drivers were parameterised" is
  consistent with this (two logical drivers plus one variant).
- **A4 — A differing sandboxed result is a finding, not a failure of the round.**
  If a driver behaves differently sandboxed, that falsifies the inference the RFC
  currently marks as unproven, and the round reports it as such.
