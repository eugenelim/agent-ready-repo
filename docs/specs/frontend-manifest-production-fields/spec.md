# Spec: frontend-manifest-production-fields

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Brief:** none
- **Contract:** none

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: light. Checked the security-boundary trigger explicitly: it does NOT
fire. Nothing here performs, gates, or relaxes a security or reliability review —
the change adds two *record-what-happened* fields and states, twice, that FE
must not render a verdict. -->

## Objective

The Digital Experience Contract asks a production surface for Security and
Privacy and for Reliability. The frontend-engineering evidence manifest required
neither, so the contract asked for evidence nothing collected.

## Acceptance Criteria

- [x] **AC1 — the manifest carries both fields at production tier.**
  `security/privacy review status` and `reliability/recovery status`, mirroring
  the contract's own `Required: production+` annotation.

- [x] **AC2 — they record status and handoff, never a verdict.** Stated twice in
  the skill body, because this is the failure the change could introduce: FE does
  not own security review or reliability engineering, and a field that reads like
  a sign-off would be worse than the gap it closes. A field whose honest value is
  "routed to `security-reviewer`, outstanding" is doing its job — it makes the
  gap visible while someone is deciding whether to ship.

- [x] **AC3 — blank is not an option below production tier.** On an explore- or
  pilot-tier surface they are recorded as not-applicable-at-this-tier, so a
  reader can distinguish "not needed yet" from "nobody looked".

- [x] **AC4 — verify mode emits them.** The mode that runs the gate suite and
  produces a manifest now names them, so a run cannot report four green gates
  while saying nothing about either.

- [x] **AC5 — the enumeration in `JOURNEY.md` matches.** It listed the eleven
  fields in prose; a stale enumeration is how the manifest and its adopter-facing
  description drift apart.

- [x] **AC6 — released and projected.** Pack 0.1.4 → 0.2.0 (minor: production
  surfaces gain two required fields), `.claude-plugin/plugin.json` kept in
  parity, and `make build-self FORCE=1` re-projected.

- [x] **AC7 — the originating AC records the follow-through.**
  `spec/frontend-engineering-doctrine-update` AC2 narrowed adopter-facing prose
  rather than claiming coverage. That was right at the time; the note records
  that both gaps it opened are now closed.

- [x] **AC8 — both backlog entries removed.**

## Boundaries

### Never do

- Never let these fields imply FE performed the review. AC2 is the rail.
- Never move security review into the frontend reviewer. `security-reviewer`
  keeps auth, secrets, and user-input boundaries.

## Testing Strategy

- **Goal-based**: `catalogue lint` clean for the pack (including CAT-L009
  pack.toml ↔ plugin.json parity), `make build-self` clean, `make ci`.
