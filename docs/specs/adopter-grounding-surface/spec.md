# Spec: Adopter grounding surface — a persistent recording surface the adopter already owns

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0047 (Decisions 3, 4), ADR-0037 (D2), ADR-0010 (reference-architecture foundation)
- **Contract:** none <!-- seed + skill-prose change; no API surface -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An adopter has nowhere canonical to record their platform and verification coordinates — "we deploy to X via Terraform, the smoke check is `make smoke`, teardown is `make destroy`" — so the work-loop's infra preflight rediscovers them cold every loop, and the framework-grounding gate (`framework-contract-grounding` spec) starts from zero. Success: the adopter gets a **low-effort, optional recording surface in files they already own** — a short infra/verification command block in `AGENTS.md`'s "Commands you'll need", and sharpened prompts in the existing `reference.md` arc42 slots (Constraints; Key technology decisions; Observability / Testing standards) — and the work-loop infra preflight **reads those coordinates first, then falls back to cold oracle discovery**. Every read is **`if present`**: a repo that fills nothing runs exactly as it does today. The recorded surface *seeds* acquisition, never *replaces* it — the agent still derives the live contract, and a recorded value that contradicts the oracle is a surfaced drift signal.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Make **every** new preflight read presence-checked — read-if-present, degrade-honestly-if-absent (ADR-0037 D2; the load-bearing constraint).
- Keep the `AGENTS.md` command block **short** — it lives under the ~200-line cap; detail belongs in `reference.md` ("reference files, don't copy them").
- Edit the **seed/template sources** (`packs/core/seeds/AGENTS.md`, the `reference.md` asset) and project via `make build-self`; the repo's own root `AGENTS.md` block is a separate, hand-owned edit if wanted.
- Treat a recorded coordinate as a **seed for** oracle acquisition, never a replacement; surface a recorded-vs-oracle contradiction as a drift signal.

### Ask first

- Adding the recording surface to `adapt-to-project` / `init-project` **elicitation** flows (in scope per RFC-0047 follow-on, but confirm the elicitation wording stays optional and non-mandating).
- Any change that would make a filled `reference.md` or `AGENTS.md` block a *prerequisite* for any work-loop path.

### Never do

- **Introduce a new top-level config file** (no `grounding.toml`) — RFC-0047 non-goal; reuse files the adopter already owns.
- **Fail the loop, or add a CI gate, on absence** of any recorded coordinate.
- **Auto-populate** `reference.md` from the running stack — that is a separate detect-and-fill capability, out of scope.

## Testing Strategy

- **Seed/template prose exists (goal-based check).** `grep` the new `AGENTS.md` command block (deploy / smoke / teardown / seed) in `packs/core/seeds/AGENTS.md`, and the sharpened platform/framework/verification prompts in the `reference.md` asset.
- **Preflight reads coordinates first (goal-based check).** `grep` the new "read recorded coordinates if present, then fall back to cold oracle discovery" step in `references/infra-verification.md`, with explicit presence-check wording.
- **Presence-check degrades honestly (manual QA).** Exercise the work-loop infra preflight in two repos — one with a filled `AGENTS.md` block + `reference.md`, one with neither — and record that the first seeds acquisition from the recorded coordinates while the second degrades to today's cold discovery with no failure.
- **Projection clean (goal-based check).** `make build-self` projects the edited seed/template/skill sources and the tree is clean afterward.

## Acceptance Criteria

- [x] `packs/core/seeds/AGENTS.md`'s "Commands you'll need" carries a short, optional infra/verification command block (deploy / smoke-or-verify-status / teardown / seed-test-data), each line marked optional ("if any").
- [x] The `reference.md` asset's existing slots are sharpened to explicitly name (a) managed-runtime/platform targets under **Constraints**, (b) framework-library contracts under **Key technology decisions**, and (c) *where the verification tooling lives* under **Observability / Testing standards** — without adding a new section.
- [x] The work-loop infra preflight (`references/infra-verification.md`) gains a first step: **read the recorded coordinates** (the `AGENTS.md` block + the `reference.md` platform/verification sections) *if present*, then fall back to cold oracle discovery — phrased as "check recorded coordinates → acquire via oracles".
- [x] **Every** new read is presence-checked: absence lowers only the starting information, never fails the loop, and is **not** enforced by any CI gate (explicit negative criterion).
- [x] The recorded surface is documented as a **seed for** oracle acquisition, never a replacement; a recorded value contradicting the oracle is surfaced as a drift signal (matching AGENTS.md's "when this file is wrong").
- [x] **No new top-level config file** is introduced (`grep` finds no `grounding.toml` or equivalent).
- [x] `adapt-to-project` / `init-project` elicitation optionally prompts for these coordinates, phrased as optional and non-mandating (threaded into `adapt-to-project`'s reference-architecture-harvest Detect step and `init-project`'s Foundation phase, both read-if-present and non-mandating).
- [x] `make build-self` projects the edited sources and the tree is clean afterward; `lint-spec-status.py` clean.

## Assumptions

- Technical: `reference.md` already carries the right arc42 slots — Constraints (line ~29), Key technology decisions (~53), Crosscutting → Observability / Testing standards (~85). (source: verified `packs/core/.apm/skills/adapt-to-project/assets/reference.md` 2026-06-25)
- Technical: the infra preflight / multi-artifact discovery lives in `references/infra-verification.md` under the work-loop skill. (source: RFC-0047 § Proposal Layer B; work-loop SKILL.md references)
- Technical: the presence-check idiom is established — `agentbundle-layout.toml` optional resolution, `adapt-to-project` "(if present)" reads, `architect-design` "state which surface you detected (or 'none')". (source: RFC-0047 § Proposal; ADR-0037 D2)
- Process: seed edits must keep placeholder shape and pass `lint-seeds`/`lint-catalogue-seeds` (the four first-party packs stay enforced); a filled command block uses placeholders, not real commands. (source: `feedback_lint_seeds_forbids_rfc_numbers` memory; the `catalogue-seeds-lint` spec)
- Product: adopters will fill the optional surface often enough to be worth it — falsifiable, but bounded: an empty surface costs nothing because it is presence-checked. (source: RFC-0047 § Key assumptions)
