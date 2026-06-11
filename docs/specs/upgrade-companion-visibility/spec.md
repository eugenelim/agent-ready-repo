# Spec: upgrade companion-drop visibility

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0001 (Tier-2 file-safety contract + this spec's reconciling erratum); `agent-spec-cli` and `distribution-adapters` specs (Shipped) own the contract this consumes.
- **Contract:** none (no new API surface; consumes the existing Tier-2 / `.upstream.<ext>` contract verbatim)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

> **Mode: full** — risk trigger: *Compliance/governance surface* (amends a frozen
> Accepted RFC via an Approver-signed erratum) and a *public-interface change*
> (new CLI stderr output on `agentbundle upgrade`).

## Objective

When an adopter runs `agentbundle upgrade` and a projected file they have edited
since install is detected as Tier-2, the CLI preserves their edits and drops the
upstream version as a `.upstream.<ext>` companion — but today it does so
**silently**, so the adopter never learns the upgrade skipped their file or where
the companion landed. `install` surfaces this case (a stderr notice on its
seed-delivery rail; the install-state marker for its projection-walk companions);
`upgrade` surfaces nothing. This spec closes that gap: a Tier-2 companion-drop on
upgrade is announced to the operator (count + the companion path(s)), so they can
find and merge it. It also
records, via an RFC-0001 erratum, that the deterministic companion-drop — not the
RFC's original in-CLI three-option prompt — is the shipped Tier-2 contract, with
the keep/merge/overwrite interactivity owned by the `adapt-to-project` skill.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.

### Always do

- Preserve the Tier-2 file-safety contract verbatim: a Tier-2 path's adopter
  content is left byte-for-byte unchanged, and the upstream content is written to
  the `.upstream.<ext>` companion. This contract is owned by the
  `distribution-adapters` spec; this change consumes it.
- Emit the new companion-drop notice to **stderr**, so the stdout `upgraded:`
  recap stays parseable (same rationale as `install.py`'s seed-companion notice).
- Follow `install`'s companion-notice vocabulary ("kept as `*.upstream.<ext>`
  companions"), **extended** to also name the companion path(s) — `upgrade` has no
  install-state marker to record them in, so the path belongs in the notice.

### Ask first

- Any change to the Tier-2 file-safety contract itself (clobber semantics, a
  backup path, an interactive prompt). That is governance-gated and out of scope.

### Never do

- Reintroduce an in-CLI overwrite or `.pre-update.bak` path, or any keep /
  overwrite / adapt prompt. Interactivity lives in `adapt-to-project`, by design.
- Clobber a Tier-2 file, or block the CLI on stdin / make `upgrade` interactive.
- Break the `test_tier_invariants.py` conformance harness.

## Testing Strategy

- **Companion-drop visibility (AC1–AC4): TDD**, exercised by an **integration**
  test against the real `upgrade` command — install v1, edit a projected file to
  force Tier-2, upgrade, and assert on the on-disk effect (original preserved,
  companion written) and the stderr notice. The behavior only proves out across
  the install→edit→upgrade boundary, so it lives at the integration surface, not
  a unit test.
- **Regression (AC1, AC4): the existing `test_tier_invariants.py` harness stays
  green** — it already pins "never clobber + companion exists" across `upgrade`.
  AC4's TTY/non-TTY parity is satisfied **structurally**, not by a dedicated test:
  the Tier-2 branch reads no stdin and has no `isatty` check, so there is no
  TTY-dependent code path to diverge (asserting otherwise would only re-prove the
  compiler).
- **Erratum + backlog reconciliation (AC5): goal-based** — the RFC-0001 erratum
  exists and is Approver-signed; the backlog item is resolved; `lint-spec-status.py`
  passes.

## Acceptance Criteria

- [x] On `agentbundle upgrade`, a Tier-2 path's adopter content is preserved
  byte-for-byte and the upstream content is written to its `.upstream.<ext>`
  companion (existing safety invariant; regression-guarded by
  `test_tier_invariants.py` staying green).
- [x] When one or more Tier-2 companion-drops occur during an upgrade, the CLI
  emits a one-per-run summary to **stderr** naming the count and the companion
  path(s) written; the stdout `upgraded:` recap is unchanged and still parseable.
- [x] When no Tier-2 collision occurs, `upgrade` emits no companion notice (the
  summary is conditional).
- [x] The change adds no in-CLI overwrite/prompt path: no `.pre-update.bak`, no
  interactive prompt, no stdin read; TTY and non-TTY upgrades behave identically
  apart from the added stderr notice.
- [x] RFC-0001 § Errata records the reconciliation (Approver-signed,
  @eugenelim): the frozen body's Tier-2 in-CLI three-option prompt is superseded
  by the shipped companion-drop + surfacing + `adapt-to-project`-owned
  interactivity; the `docs/backlog.md` "Tier-2 upgrade prompt" item is resolved.

## Assumptions

- Technical: `upgrade.py`'s Tier-2 branch calls `safety.write_companion` with no
  operator notice and no recap tracking (source: `upgrade.py:365-374`, read 2026-06-11).
- Technical: `install.py` surfaces Tier-2 companions on its **seed-delivery** rail
  via a stderr count + "kept as *.upstream.<ext> companions" message
  (`install.py:891-904`); its **projection-walk** companions are recorded in the
  install-state marker (`new_companions`, `install.py:809-817, 2074, 2113`), not
  stderr. `upgrade` surfaces neither — this fix adds the stderr notice (read 2026-06-11).
- Technical: the deterministic Tier-2 companion-drop — not RFC-0001's in-CLI
  three-option prompt — is the shipped contract, pinned by two Shipped specs and
  the conformance harness (source: `agent-spec-cli/spec.md` Boundaries,
  `distribution-adapters/spec.md` §134-154, `test_tier_invariants.py` — read 2026-06-11).
- Process: the in-CLI three-option prompt is reconciled away via an RFC-0001
  erratum rather than implemented (source: user confirmation 2026-06-11).
- Product: a separate `--dry-run` / projection-plan feature (show what/where
  before writing) is deferred to its own spec, pending go/no-go (source: user
  confirmation 2026-06-11).
