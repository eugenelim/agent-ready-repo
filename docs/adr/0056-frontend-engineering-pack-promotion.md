# ADR-0056: Promote `frontend-engineering` to first-class pack

- **Status:** Accepted (Amended by ADR-0057 — the "not modified or deleted" clause for the resident skill is superseded; the resident has been deleted)
- **Date:** 2026-07-25
- **Decision-makers:** eugenelim
- **Related:** [`guides/frontend-engineering/`](../../guides/frontend-engineering/), [`.claude/skills/frontend-engineering/SKILL.md`](../../.claude/skills/frontend-engineering/SKILL.md)

## Decision summary

- **Decision:** The `frontend-engineering` resident skill (`.claude/skills/frontend-engineering/`) is promoted to a first-class pack (`packs/frontend-engineering/`) with 9 skills, a `frontend-reviewer` agent, a guide tree, and a catalogue page. The resident skill file remains in place — it is not deleted. The pack ships an expanded 660-line version of the skill (the resident is 443 lines) that adds four explicit modes (create/retrofit/audit/verify), an 18-state matrix (vs. 6 in the resident), a 12-field page contract, an evidence manifest, Core Web Vitals targets, a brownfield checklist, and an updated WCAG baseline (2.2 AA vs. 2.1 AA). The pack skill supersedes the resident when both are installed. The resident remains unchanged as the baseline for users without the pack.
- **Because:** The skill has accumulated enough depth and distinct concerns — token system architecture, accessibility engineering, performance diagnostics, rendering strategy, component API design, responsive layout, CSS architecture — that a flat single-skill surface no longer serves the full range of tasks. A pack partitions those concerns into named atomic skills a practitioner loads by task, without forcing them to internalize the entire baseline skill every session.
- **Applies to:** `packs/frontend-engineering/` and the four work-loop insertion points that reference the pack's atomic skills and the `frontend-reviewer`.
- **Tradeoff accepted:** Nine skills and an agent to maintain rather than one. The tradeoff is accepted because the pack's skills are distinct and non-overlapping; the maintenance cost grows sub-linearly with the concern count.
- **Revisit if:** The pack grows beyond 12 skills, at which point a split by concern cluster (accessibility / performance / architecture) should be evaluated.

## Context

The resident `frontend-engineering` SKILL.md covers the full create/retrofit/audit/verify workflow, CSS token discipline, accessibility patterns, GATES commands, an evidence manifest, and performance targets. That breadth is intentional for a surface-level skill loaded at PLAN time — the practitioner needs the whole context to set up the pre-flight correctly.

The limitation appears when a task is narrowly scoped: a performance remediation, a token system design, a dedicated accessibility audit. Loading the full skill to address one of those concerns brings 600+ lines of incidental context. The pack partitions the skill into atomic disciplines a practitioner loads by task.

## Why ADR, not RFC

RFC-first is the right gate for a **new top-level directory** or a **cross-cutting change that affects multiple packs**. The `packs/` directory exists; `frontend-engineering` is an established, shipped skill. The promotion pattern — resident skill to pack — is the same pattern `experience-design` and `architect` followed, and it does not require a new structural decision. This is an execution decision, not a governance decision: ADR records it, pack ships it.

RFC would be appropriate if: the promotion required a new adapter-contract version, restructured `packs/` layout conventions, or proposed a new top-level directory. None of those apply here.

## Risk triggers (full-mode justification)

The following risk triggers fired, routing this work to full-mode work-loop:

- **Multi-feature or dependent tasks** — 9 skills, 1 agent, 4 work-loop insertion points, a guide tree, a sidebar addition, and a catalogue page are interdependent.
- **Structural or public-interface change** — the pack introduces a `frontend-reviewer` agent as a public interface; the work-loop REVIEW phase references it by name.
- **New dependency** — the pack's `frontend-engineering` skill formalizes a co-install dependency on the `experience-design` pack for genre routing (T2 gate already present in the resident skill; the pack makes it explicit).

## What changes

| Before | After |
|---|---|
| One 443-line skill in `.claude/skills/frontend-engineering/` | Same file unchanged; pack ships a 660-line expanded version as `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` |
| No atomic craft skills | 8 additional atomic skills partitioning the main skill's concerns |
| No diff-level reviewer | `frontend-reviewer` agent in `.apm/agents/` |
| No catalogue page | `web/src/content/packs/frontend-engineering.md` |
| No guide tree | `guides/frontend-engineering/` with tutorials, how-to, and reference |
| No work-loop integration | 4 insertion points in `work-loop` SKILL.md (footnote, EXECUTE FE, REVIEW, DECIDE) |

## What does not change

- The resident `.claude/skills/frontend-engineering/SKILL.md` is **not modified or deleted**. It remains the baseline surface for users without the pack installed.
- The pack skill's frontmatter `description` is intentionally expanded beyond the resident's: it adds the four modes (create/retrofit/audit/verify) that differentiate the pack version. The resident description is unchanged.
- **Precedence:** when the pack is installed alongside core, the pack's 660-line version supersedes the resident 443-line version — load the pack skill by name; it contains the full contract.
- The `experience-design` co-install requirement (genre routing) is unchanged — the pack formalizes what was already a T2 gate in the resident skill.

## Options considered

**Option A — RFC first, then ship:** Open an RFC, gather feedback, accept, then implement. Appropriate for new top-level directories and cross-cutting structural decisions. Rejected: `packs/` exists; the promotion pattern is established; the ADR captures the relevant decision context without requiring an additional RFC cycle.

**Option B — ADR + ship (selected):** Record the decision and its rationale in an ADR; implement immediately. The `packs/` precedent (`experience-design`, `architect`, `desk-research`) is the reference; no new structural decision is being made.
