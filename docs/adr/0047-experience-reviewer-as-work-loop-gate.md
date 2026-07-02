# ADR-0047: `experience-reviewer` is a conditional specialist reviewer in `work-loop` for user-facing surface diffs — select-or-note, full-mode only

- **Status:** Accepted
- **Date:** 2026-07-02
- **Decision-makers:** eugenelim
- **Related:** [ADR-0042](0042-agent-additions-keyed-to-loop-and-work-type.md) (agent additions keyed to loop and work type); [ADR-0014](0014-rigor-scales-with-risk-work-loop-modes.md) (rigor scales with risk); [RFC-0050](../rfc/0050-experience-pack-pressure-test.md) (§ D7 — the `experience-reviewer` admitted); backlog items `experience-reviewer-as-work-loop-gate` and `experience-loop-trigger-for-site-changes`

## Decision summary

- **Decision:** `experience-reviewer` is added to `work-loop`'s specialist reviewer roster as a **conditional specialist** — triggered when a full-mode diff changes what a reader or adopter sees (a new page, a redesigned screen, a pack card, a docs page). It carries the standard select-or-note fallback: absence of the experience pack is a named skip, not a silent pass. Light-mode user-facing changes (copy edits, minor tweaks) receive only the pre-EXECUTE design-intent recommendation, not the review gate.
- **Because:** A frontend page can clear `adversarial-reviewer`, `security-reviewer`, and `quality-engineer` and still ship without design sense — those three lenses review code correctness, security, and testability but hold no design or experience lens. Autonomous design sessions (and solo work done without a design step) can produce pages that are technically sound but experientially broken.
- **Applies to:** The `core` pack's `work-loop` SKILL.md; any adopter who has the `experience` pack installed.
- **Tradeoff accepted:** The gate is degradable — when the experience pack is absent, the loop proceeds with a named skip rather than blocking. This is the same posture as `security-reviewer` on security-boundary diffs, and mirrors the broader select-or-note discipline (`work-loop` SKILL.md § 4 REVIEW). The result is a gate that fires when the right tools are available rather than a gate that blocks all adopters regardless of their pack configuration.
- **Revisit if:** The experience-reviewer scope expands beyond design artifacts to code diffs (it would then need a different trigger); or the pack cross-dependency model changes (if core declares a hard dependency on experience, the select-or-note fallback becomes unnecessary).

## Context

### The gap

`work-loop`'s specialist reviewer roster covers three lenses:
- `adversarial-reviewer` — always-on; spec/plan drift, missing edge cases, scope creep.
- `security-reviewer` — security-boundary diffs; auth, secrets, file/network I/O.
- `quality-engineer` — every full-mode loop; testability, observability, maintainability.

None of these holds a **design or experience lens**. When an agent builds a new docs page or redesigns a site section, the REVIEW phase has no reviewer that can flag "hero subtitle describes features not outcomes" or "five-second scan fails — reader cannot determine fit." The design quality gap was surfaced in sessions building the Ottawa site (session 2026-07-01): multiple iterations shipped pages with no design sense because no gate required a design-lens reviewer.

### Why not a new risk trigger?

The backlog items (`experience-reviewer-as-work-loop-gate`, `experience-loop-trigger-for-site-changes`) both proposed a "user-facing surface" risk trigger. There are two reasons to implement this as a REVIEW-roster entry rather than a risk trigger:

1. **The existing trigger already covers the high-stakes case.** A net-new page published to a public site IS "a public or published interface" under the existing "Structural or public-interface change" trigger — it routes to full mode already. Adding a new trigger would be redundant for the exact case where the gate matters most.

2. **Not all user-facing surface work warrants full-mode ceremony.** A minor copy edit on an existing page (fixing a typo, reordering a list) does not justify full-mode ceremony. A reviewer that fires only in full mode correctly scopes to the higher-risk changes (net-new pages, structural redesigns) where the architectural investment is already justified.

The result: full-mode user-facing surface diffs get the experience-reviewer gate; light-mode surface changes get the pre-EXECUTE design-intent recommendation only.

### ADR-0042 value test

ADR-0042 requires a new reviewer to clear:
1. **Different loop or work type than the core code-review gate.** ✓ — experience review is design/UX review, not code-diff review. It runs on rendered output (a described screen, a screenshot, a built page), not on the code diff itself.
2. **Unique agent value** — forked-context independence, parallelism, or distinct surface/cadence. ✓ — forked-context independence (the reviewer has not seen the authoring session; `design-critique`'s existing note confirms same-session review marks its own homework); distinct surface/cadence (a generated screen, not a code diff; invoked after EXECUTE, not inline).
3. **Charter's four principles.** ✓ — principle 3 in particular ("not a runtime engine") is satisfied; experience-reviewer is read-only and returns a findings block.
4. **Collision-hardened by construction.** ✓ — "experience-reviewer" has a unique discipline-word head distinct from "adversarial-reviewer," "security-reviewer," and "quality-engineer."

## Decision

> `experience-reviewer` is a **conditional specialist reviewer** in `work-loop`'s REVIEW section — not a fourth core-code-review lens, not always-on, and not behind a new risk trigger. It fires when the diff crosses a user-facing surface in full-mode work, carrying the standard select-or-note fallback. The pre-EXECUTE design-intent pass (running `aesthetic-direction` / `design-critique` before writing code for user-facing surface work) is advisory in both light and full mode.

Concretely:

- **Trigger:** "for diffs that change what a reader or adopter sees — a new page, a redesigned screen, a pack card, a docs page — in full-mode work."
- **Mandatory posture (select-or-note):** same enforcement surface as `security-reviewer`. The end-of-session checklist requires either a clean return or an explicit named skip. Absence of the experience pack is not a silent pass.
- **Artifact handoff:** the orchestrator passes the rendered output (described screen, screenshot, or path to built artifact) **plus the grounded aesthetic reference and constraints** (persona, outcome, platform surface) — not the code diff. Experience-reviewer's confirm-before-reviewing gate requires the grounded reference; an orchestrator that omits it produces a degraded review.
- **Light-mode advisory:** the pre-EXECUTE design-intent pass appears in the PLAN section with no full-mode gate. Light-mode changes receive the recommendation; only full-mode changes require the review gate.

## Consequences

**Positive:**
- Net-new user-facing pages authored in full mode (which they are — they fire "Structural or public-interface change") get an independent design lens before merge.
- The pattern is identical to `security-reviewer`'s conditional-specialist posture — easy to reason about, easy to extend.
- Light-mode copy changes are not burdened with full reviewer ceremony.
- Cross-pack dependency is soft (select-or-note fallback) — adopters without the experience pack are not blocked.

**Negative:**
- The gate degrades when the experience pack is absent — teams who skip experience pack installation will never see the gate fire even for net-new pages. Mitigated by the named-skip discipline (the final summary always names the skipped reviewer).
- The full-mode-only scoping means a light-mode copy edit that ships misleading marketing copy gets only the advisory, not the gate. Mitigated by the marketing clarity criterion added to `design-critique` (same PR).

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** the `adversarial-reviewer` pass and the implementing PR author confirm: the experience-reviewer entry in the SKILL.md carries the select-or-note fallback, names the artifact handoff contract, and the end-of-session checklist includes the reviewer in the coverage line.
- **Owner:** the PR author + the `adversarial-reviewer` pass.

## Alternatives considered

- **Add a "user-facing surface" risk trigger** to route all such changes to full mode. Declined: the existing "Structural or public-interface change" trigger already covers the high-stakes case (net-new pages); adding a new trigger would be redundant at the high end and too broad at the low end (minor copy edits do not warrant full-mode ceremony).
- **Make experience-reviewer always-on** alongside the three core lenses. Declined: ADR-0042 explicitly caps core always-on lenses at three (adversarial, security, quality); adding a fourth is a charter question. The conditional-specialist posture avoids that bar.
- **No gate — rely on author judgment.** Declined: the session record (Ottawa site, 2026-07-01) demonstrates this fails in practice. Multiple iterations shipped design-sense failures because no gate required a design-lens review.
