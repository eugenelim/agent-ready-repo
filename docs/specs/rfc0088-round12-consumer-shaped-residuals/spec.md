# Spec: rfc0088-round12-consumer-shaped-residuals

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [RFC-0088](../../rfc/0088-web-pilot-foundation.md) — Experimental; this spec measures open questions 4, 5 and 6 and two residuals, and changes no disposition
- **Contract:** none — this spec produces evidence, not interfaces.
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full (work-loop). Risk triggers: security boundary (browser launch,
credential handling, OS isolation, filesystem) and multi-feature/dependent tasks.
Full-mode scripts live at .claude/skills/work-loop/scripts/ — skill-relative. -->

## Objective

Round 11 measured the binding requirements the 2026-08-18 dispositions attach, and
two of them were amended as a result. Reading those amendments against a **real
consumer pack** — an adopter's productivity pack in a separate catalogue, which
this repository does not modify — surfaced three design questions the RFC could not
answer from its own fixtures, now recorded as open questions 4, 5 and 6.

This round measures them. Its user is the approver, who needs each open question to
rest on an observation rather than on a structural argument before an acceptance
carries it. Success is that every arm produces an artifact containing a row that
**could have failed**, and that any arm contradicting a recommended candidate is
reported as a finding.

The round measures the **architecture** and does **not** re-measure the apparatus.
No coverage percentage, claim-accounting total, or mutation-corpus figure is a
deliverable.

Five arms, each deciding something:

1. **Destination-scoped worker policy** (open question 4). A global suppression
   switch forces a choice between losing a surface and losing the control, because
   real destinations have opposite needs.
2. **Page-resident token boundary** (open question 5). Whether a consumer that
   must replay a scoped API token can do so without the broker ever holding it.
3. **Browser signing-identity anchor** (open question 6). Whether a stable vendor
   team identifier plus notarization and library-validation is a usable provenance
   anchor for an auto-updating system browser.
4. **Separate-uid attachment isolation.** Whether running the browser under a
   different OS user closes the same-uid endpoint-attachment exposure that
   disposition B accepted — the cheap alternative to containerising.
5. **What the worker purge actually touches.** Enumerating which profile stores the
   item-6 purge removes, which bounds whether a device-bound refresh credential
   survives it.

## Boundaries

### Always do

- Run every subprocess under an explicit environment allowlist, never the ambient
  environment, and prove it by having the child print its own environment.
- Give every arm a control that fails when the control under test is removed, and
  admit the arm only if that control actually failed in the same run.
- Read a mode, platform, identity or state back from the artifact rather than
  asserting what was requested.
- Mutation-test each new fact individually and record the one-line result.
- Compare every touched member against `manifest-r7.sha256` before promoting.

### Ask first

- **Adding any dependency, toolchain, or compile step** — this is the recorded
  unblock condition for the native-addon residual, which is deliberately NOT in
  this round.
- Any arm that would require a credential, an account, or a live authenticated
  session.
- Extending the round beyond these five arms.
- Any change to an RFC decision, disposition, blocker item, or status field.

### Never do

- **No implementation.** No production packs, runtime code, dependencies,
  contracts, catalogue entries, adapters, or new top-level directories.
- **No modification of any other catalogue or pack.** A real consumer pack informed
  these questions; it is read-only context and this round writes nothing to it.
- **No vendor, product, employer, tenant or account identifier** in any artifact,
  note, fixture, or commit — and **no URI**. Address destinations by role. Supply
  endpoints and binary paths through the environment, never hard-coded.
- **No credential, real profile, or live account.** Synthetic data and fresh
  synthetic profiles only; never print, log, compare, or archive a credential
  value, even a synthetic one.
- **Never convert a characterisation fixture, inspection-only result, hard-coded
  literal, or failed security precondition into a Pass.**
- **Never move RFC-0088 to Accepted, close a blocker item, or revise a recorded
  disposition.**

## Testing Strategy

Verification mode for every task is **visual / manual QA against the real
artifact**: these are measurement fixtures, and the deliverable is the observed
behaviour of a real browser, a real OS boundary, or a real signed binary. A passing
unit gate would prove nothing, because what is under test is whether the platform
behaves as an open question assumes.

Each task runs the real driver end-to-end, writes a results artifact with per-row
`ok` fields and a `provenance` block, and is admitted only if it records a row that
**could have failed**. Figures are derived by `verify-note-figures-r7.py` and each
new fact is mutation-tested by the `r11-fact-negative-tests.py` mechanism.

Gate order: `build-archive.py` → `verify-note-figures-r7.py` → `r9-gates.sh`.

## Acceptance Criteria

- [ ] **AC1 — Worker policy can be applied per destination.** One session suppresses
      service workers for one destination while permitting them for another, with a
      control arm showing a global block breaking the permitted destination's flow.
      If per-destination scoping proves impossible, that is recorded as a finding
      against open question 4's recommended candidate.
- [ ] **AC2 — A scoped API token can be replayed without the broker holding it.**
      A page-resident capture-and-use shim performs authenticated calls against a
      synthetic API while the driver process never receives the token, asserted from
      the driver side. A control arm without the shim fails the same calls.
- [ ] **AC3 — The token never reaches a durable surface.** The artifact records that
      no token value appears in the job file, the driver environment, process argv,
      stdout, or the results artifact — each checked explicitly, not asserted.
- [ ] **AC4 — Signing identity is a usable provenance anchor.** The artifact records
      a system browser's team identifier, notarization status, and hardened-runtime
      and library-validation flags, read from the binary, with a control showing a
      binary lacking that identity is distinguishable.
- [ ] **AC5 — Separate-uid isolation measured.** Whether a process running as a
      different OS user can reach the browser's bind endpoint, with a same-uid
      control arm that **can** reach it — otherwise the isolation row proves nothing.
- [ ] **AC6 — The worker purge's blast radius is enumerated.** The artifact lists
      which profile stores the item-6 purge removes and which it leaves, so whether
      a profile-resident credential survives is bounded by observation.
- [ ] **AC7 — Every new fact is mutation-tested individually**, with the one-line
      result recorded per fact.
- [ ] **AC8 — No apparatus figure is a deliverable**, and no vendor, product,
      tenant, account identifier, or URI appears in any artifact or note — verified
      by an explicit scan.
- [ ] **AC9 — Gates clean**: archive builds, figure verifier reports zero wrong and
      zero claimed-nowhere, `r9-gates.sh` passes, RFC status still `Experimental`.

## Assumptions

- Technical: the evidence tree and its helpers are reconstructible from the archive
  note; round 11 left the promote cycle converging and the manifest matching its
  tree at rest (source: round-11 note, R11-2 and R11-6)
- Technical: `serviceWorkers: 'allow' | 'block'` is a per-**context** option, so
  per-destination scoping plausibly means one context per destination — to be
  measured, not assumed (source: round-11 arm 2)
- Technical: an MDM-provisioned system browser carries a stable vendor team
  identifier, notarization, and hardened-runtime plus library-validation flags
  (source: local signature read, 2026-08-18)
- Product: the token-replay pattern comes from a real adopter pack read as
  read-only context; this round writes nothing to it (source: user direction
  2026-08-18)
- Process: the native-addon confinement bypass stays OUT of this round because it
  needs a toolchain, which is an *Ask first* boundary (source: backlog entry
  `rfc0088-native-addon-confinement-bypass`)
- Process: the post-authentication silent-SSO worker dependency is not measurable
  under the security preconditions and is not scheduled (source: front-door probe
  note, Limits)
